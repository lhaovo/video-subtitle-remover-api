import os
import re
import signal
import subprocess
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator


BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = Path(os.environ.get("VSR_WEB_DIR", str(BASE_DIR / "web_debug"))).expanduser()
DATA_DIR = Path(os.environ.get("VSR_DATA_DIR", str(BASE_DIR / "api_data"))).expanduser()
UPLOAD_DIR = DATA_DIR / "uploads"
OUTPUT_DIR = DATA_DIR / "outputs"
ALLOWED_MODES = {"sttn-auto", "sttn-det", "lama", "propainter", "opencv"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class JobRequest(BaseModel):
    input: str = Field(min_length=1)
    output: str = Field(min_length=1)
    mode: Literal["sttn-auto", "sttn-det", "lama", "propainter", "opencv"] = "sttn-auto"
    areas: list[tuple[int, int, int, int]] = Field(default_factory=list)

    @field_validator("input", "output")
    @classmethod
    def normalize_path(cls, value: str) -> str:
        return str(Path(value).expanduser())


class Job(BaseModel):
    id: str
    input: str
    output: str
    mode: str
    areas: list[tuple[int, int, int, int]]
    status: Literal["queued", "running", "succeeded", "failed", "cancelled"]
    progress: int = 0
    error: str | None = None
    log: list[str] = Field(default_factory=list)
    created_at: float
    started_at: float | None = None
    finished_at: float | None = None
    command: list[str] = Field(default_factory=list)


class UploadResponse(BaseModel):
    filename: str
    input: str
    output: str
    preview_url: str


app = FastAPI(title="Video Subtitle Remover API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

app.mount("/media", StaticFiles(directory=DATA_DIR), name="media")

jobs: dict[str, Job] = {}
processes: dict[str, subprocess.Popen[str]] = {}
lock = threading.RLock()
executor = ThreadPoolExecutor(max_workers=int(os.environ.get("VSR_API_WORKERS", "1")))
progress_pattern = re.compile(r"(\d{1,3})%")


def safe_filename(filename: str) -> str:
    original = Path(filename).name
    stem = Path(original).stem or "video"
    suffix = Path(original).suffix.lower()
    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._") or "video"
    return f"{safe_stem}{suffix}"


def build_command(job: Job) -> list[str]:
    python_bin = os.environ.get("VSR_PYTHON", sys.executable)
    command = [
        python_bin,
        "-u",
        str(BASE_DIR / "backend" / "main.py"),
        "-i",
        job.input,
        "-o",
        job.output,
        "--inpaint-mode",
        job.mode,
    ]
    for ymin, ymax, xmin, xmax in job.areas:
        command.extend(["-c", str(ymin), str(ymax), str(xmin), str(xmax)])
    return command


def default_output_path(input_path: Path) -> Path:
    return OUTPUT_DIR / f"{input_path.stem}_no_sub{input_path.suffix or '.mp4'}"


def append_log(job_id: str, line: str) -> None:
    clean_line = line.strip()
    if not clean_line:
        return
    with lock:
        job = jobs.get(job_id)
        if not job:
            return
        job.log.append(clean_line)
        job.log = job.log[-200:]
        match = progress_pattern.search(clean_line)
        if match:
            job.progress = max(job.progress, min(99, int(match.group(1))))


def heartbeat(job_id: str, process: subprocess.Popen[str]) -> None:
    last_progress = -1
    while process.poll() is None:
        time.sleep(10)
        with lock:
            job = jobs.get(job_id)
            if not job or job.status != "running":
                return
            progress = job.progress
        if progress == last_progress:
            append_log(job_id, f"heartbeat: still running, progress {progress}%")
        else:
            append_log(job_id, f"heartbeat: running, progress {progress}%")
            last_progress = progress


def update_job(job_id: str, **updates: object) -> None:
    with lock:
        job = jobs[job_id]
        for key, value in updates.items():
            setattr(job, key, value)


def run_job(job_id: str) -> None:
    with lock:
        job = jobs[job_id]
        job.status = "running"
        job.started_at = time.time()
        job.command = build_command(job)
        command = list(job.command)

    output_parent = Path(job.output).parent
    output_parent.mkdir(parents=True, exist_ok=True)

    try:
        env = os.environ.copy()
        env.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
        env.setdefault("PYTHONUNBUFFERED", "1")
        append_log(job_id, "starting subtitle remover process")

        process = subprocess.Popen(
            command,
            cwd=str(BASE_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            start_new_session=True,
            env=env,
        )
        with lock:
            processes[job_id] = process

        threading.Thread(target=heartbeat, args=(job_id, process), daemon=True).start()

        assert process.stdout is not None
        for line in process.stdout:
            append_log(job_id, line)

        return_code = process.wait()
        with lock:
            current = jobs[job_id]
            processes.pop(job_id, None)
            current.finished_at = time.time()
            if current.status == "cancelled":
                current.progress = min(current.progress, 99)
                return
            if return_code == 0 and Path(current.output).exists():
                current.status = "succeeded"
                current.progress = 100
            else:
                current.status = "failed"
                current.error = f"subtitle remover exited with code {return_code}"
    except Exception as exc:
        with lock:
            processes.pop(job_id, None)
            job = jobs[job_id]
            job.status = "failed"
            job.error = str(exc)
            job.finished_at = time.time()


@app.get("/", response_class=HTMLResponse)
def index() -> FileResponse:
    index_path = WEB_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="web_debug/index.html not found")
    return FileResponse(index_path)


@app.get("/api/health")
def health() -> dict[str, object]:
    accelerator: dict[str, object]
    try:
        import torch

        accelerator = {
            "torch": torch.__version__,
            "torchCuda": torch.version.cuda,
            "cudaAvailable": torch.cuda.is_available(),
            "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        }
    except Exception as exc:
        accelerator = {"error": str(exc)}

    return {
        "ok": True,
        "baseDir": str(BASE_DIR),
        "python": os.environ.get("VSR_PYTHON", sys.executable),
        "workers": executor._max_workers,
        "accelerator": accelerator,
    }


@app.post("/api/uploads", response_model=UploadResponse)
async def upload_video(file: UploadFile = File(...)) -> UploadResponse:
    safe_name = safe_filename(file.filename or "video.mp4")
    suffix = Path(safe_name).suffix.lower()
    if suffix not in VIDEO_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"unsupported video extension: {suffix}")

    target = UPLOAD_DIR / f"{int(time.time())}_{uuid.uuid4().hex[:8]}_{safe_name}"
    with target.open("wb") as output:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            output.write(chunk)

    return UploadResponse(
        filename=safe_name,
        input=str(target),
        output=str(default_output_path(target)),
        preview_url=f"/media/uploads/{target.name}",
    )


@app.post("/api/jobs", response_model=Job)
def create_job(request: JobRequest) -> Job:
    input_path = Path(request.input)
    if not input_path.exists():
        raise HTTPException(status_code=400, detail=f"input file not found: {request.input}")
    if request.mode not in ALLOWED_MODES:
        raise HTTPException(status_code=400, detail=f"unsupported mode: {request.mode}")

    job_id = uuid.uuid4().hex
    job = Job(
        id=job_id,
        input=str(input_path),
        output=str(Path(request.output)),
        mode=request.mode,
        areas=request.areas,
        status="queued",
        created_at=time.time(),
    )
    with lock:
        jobs[job_id] = job
    executor.submit(run_job, job_id)
    return job


@app.get("/api/jobs", response_model=list[Job])
def list_jobs() -> list[Job]:
    with lock:
        return sorted(jobs.values(), key=lambda item: item.created_at, reverse=True)


@app.get("/api/jobs/{job_id}", response_model=Job)
def get_job(job_id: str) -> Job:
    with lock:
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="job not found")
        return job


@app.post("/api/jobs/{job_id}/cancel", response_model=Job)
def cancel_job(job_id: str) -> Job:
    with lock:
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="job not found")
        if job.status not in {"queued", "running"}:
            return job
        job.status = "cancelled"
        job.finished_at = time.time()
        process = processes.get(job_id)

    if process and process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

    with lock:
        return jobs[job_id]


@app.get("/api/jobs/{job_id}/output")
def download_output(job_id: str) -> FileResponse:
    with lock:
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="job not found")
        output = Path(job.output)
    if not output.exists():
        raise HTTPException(status_code=404, detail="output file not found")
    return FileResponse(output)

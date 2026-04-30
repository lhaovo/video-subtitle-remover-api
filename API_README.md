# VSR API 调试服务

这个服务给 `video-subtitle-remover` 增加一个轻量 HTTP API 和浏览器调试页，不改变原来的 GUI/CLI。当前服务端口统一使用 `8332`，可作为 `video-manager` 的外部字幕擦除服务。

## Docker 启动

模型权重不放入 Git。首次部署前先恢复 `backend/models`：

```bash
scripts/install-models.sh /path/to/video-subtitle-remover-models.tgz
```

也可以通过环境变量从 HTTP 或 NAS 挂载路径安装：

```bash
VSR_MODEL_ARCHIVE_URL=file:///mnt/video-manager/model-packages/video-subtitle-remover-models.tgz scripts/install-models.sh
```

已有可用模型的机器可以导出模型包：

```bash
scripts/export-models.sh /mnt/video-manager/model-packages/video-subtitle-remover-models.tgz
```

模型文件说明见 `docs/models.md`。上游完整发布包来源：<https://github.com/YaoFANGUK/video-subtitle-remover/releases>。

```bash
docker compose up -d --build
```

访问：

```text
http://127.0.0.1:8332
```

健康检查：

```bash
curl http://127.0.0.1:8332/api/health
```

停止：

```bash
docker compose down
```

## 本地启动

已安装依赖时也可以直接启动：

```bash
uvicorn api_server:app --host 0.0.0.0 --port 8332
```

调试页支持上传视频、浏览器预览、拖动时间轴、在当前画面框选字幕区域、提交任务和下载输出。

## API 用法

上传视频：

```bash
curl -X POST http://127.0.0.1:8332/api/uploads \
  -F 'file=@/path/to/input.mp4'
```

返回的 `input`、`output` 可以直接用于提交任务。

提交任务：

```bash
curl -X POST http://127.0.0.1:8332/api/jobs \
  -H 'Content-Type: application/json' \
  -d '{
    "input": "/data/uploads/input.mp4",
    "output": "/data/outputs/input_no_sub.mp4",
    "mode": "sttn-auto",
    "areas": []
  }'
```

`areas` 格式是 `YMIN YMAX XMIN XMAX`：

```json
{
  "areas": [[900, 1080, 100, 1820]]
}
```

查询任务：

```bash
curl http://127.0.0.1:8332/api/jobs
curl http://127.0.0.1:8332/api/jobs/{job_id}
```

取消任务：

```bash
curl -X POST http://127.0.0.1:8332/api/jobs/{job_id}/cancel
```

下载输出：

```bash
curl -L -o output.mp4 http://127.0.0.1:8332/api/jobs/{job_id}/output
```

## 环境变量

- `VSR_PYTHON`：执行 `backend/main.py` 的 Python 路径，默认使用启动 API 的 Python。
- `VSR_API_WORKERS`：并发处理任务数，默认 `1`。
- `VSR_DATA_DIR`：上传和输出文件目录，Docker 默认 `/data`。
- `VSR_WEB_DIR`：调试页目录，默认 `web_debug`。
- `VSR_FFMPEG_PATH`：ffmpeg 路径，Docker 默认 `/usr/bin/ffmpeg`。
- `PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK`：Docker 默认 `True`。

## Docker 运行环境

当前 Dockerfile 面向 API/headless 运行：

```text
Python 3.12
PaddlePaddle 3.0.0
Torch 2.6.0+cu124
Torchvision 0.21.0+cu124
API 端口 8332
```

`docker-compose.yml` 默认启用：

```yaml
gpus: all
ports:
  - "8332:8332"
volumes:
  - ./api_data:/data
```

如果机器没有 NVIDIA GPU，需要把 `docker-compose.yml` 里的 `gpus: all` 和 `deploy.resources.reservations.devices` 去掉，并将 Docker build 参数 `HARDWARE_ACCELERATOR` 改为 `cpu`。

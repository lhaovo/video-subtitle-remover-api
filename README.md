# video-subtitle-remover-api

这是一个给 `video-manager` 使用的字幕擦除 API 服务，基于 `video-subtitle-remover` 的核心处理代码整理而来。

当前仓库只保留 API、Docker、Web 调试页和运行所需代码，不再维护原 GUI 项目的说明、截图和多语言 README。

## 功能

- 提供 HTTP API 去除视频硬字幕。
- 提供浏览器调试页，可以上传视频、预览、拖动时间轴、框选字幕区域并提交任务。
- 支持 Docker Compose 启动。
- 默认使用 CUDA 12.4 镜像配置，端口为 `8332`。
- 可作为 `video-manager` 的外部字幕擦除服务。

## 模型文件

模型权重不提交到 Git，需要从模型包恢复到 `backend/models`。

当前内部 NAS 模型包：

```text
/mnt/video-manager/model-packages/video-subtitle-remover-models.tgz
sha256: 67d2ddd89ea63089702d8b97bea3438382dabefe37afc36efb5463fd8be4bd8f
```

恢复模型：

```bash
scripts/install-models.sh /mnt/video-manager/model-packages/video-subtitle-remover-models.tgz
```

已有可用模型时，可以重新导出模型包：

```bash
scripts/export-models.sh /mnt/video-manager/model-packages/video-subtitle-remover-models.tgz
```

上游完整发布包来源：

```text
https://github.com/YaoFANGUK/video-subtitle-remover/releases
```

## Docker 启动

```bash
docker compose up -d --build
```

访问调试页：

```text
http://127.0.0.1:8332
```

健康检查：

```bash
curl http://127.0.0.1:8332/api/health
```

停止服务：

```bash
docker compose down
```

## 主要配置

`docker-compose.yml` 默认配置：

```text
端口: 8332
数据目录: ./api_data -> /data
video-manager 处理中目录: ../video_manager/data/processing -> /data/processing
未处理视频目录: /mnt/video-manager/unprocessed -> /videos/unprocessed
已处理视频目录: /mnt/video-manager/processed -> /videos/processed
GPU: gpus: all
```

主要环境变量：

```text
VSR_API_WORKERS=1
VSR_DATA_DIR=/data
VSR_WEB_DIR=web_debug
VSR_FFMPEG_PATH=/usr/bin/ffmpeg
PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True
```

`video-manager` 会把剪辑后的中间文件写到本机 `data/processing`，再把 `/data/processing/...` 路径传给 VSR。VSR 容器必须把同一个宿主机目录挂到同一个容器路径 `/data/processing`，否则“先剪辑再去字幕”的任务会报 `input file not found`。

如果机器没有 NVIDIA GPU，需要移除 `docker-compose.yml` 中的 `gpus: all` 和 `deploy.resources.reservations.devices`，并把 Docker build 参数 `HARDWARE_ACCELERATOR` 改成 `cpu`。

## API

上传视频：

```bash
curl -X POST http://127.0.0.1:8332/api/uploads \
  -F 'file=@/path/to/input.mp4'
```

提交任务：

```bash
curl -X POST http://127.0.0.1:8332/api/jobs \
  -H 'Content-Type: application/json' \
  -d '{
    "input": "/data/uploads/input.mp4",
    "output": "/data/outputs/input_no_sub.mp4",
    "mode": "sttn-auto",
    "areas": [[900, 1080, 100, 1820]]
  }'
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

下载结果：

```bash
curl -L -o output.mp4 http://127.0.0.1:8332/api/jobs/{job_id}/output
```

## 本地启动

已安装依赖时可以直接启动：

```bash
uvicorn api_server:app --host 0.0.0.0 --port 8332
```

通常建议优先使用 Docker Compose，避免 Python、Paddle、Torch、CUDA 版本不一致。

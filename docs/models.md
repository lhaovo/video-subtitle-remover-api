# Model Files

The API repository does not commit model weights. The weight files are large binary artifacts and should be delivered as a versioned archive through NAS, an internal HTTP server, GitHub Release assets, or another artifact store.

The original upstream project publishes full application packages on GitHub Releases:

https://github.com/YaoFANGUK/video-subtitle-remover/releases

Those packages are the upstream source for the model files. For our API deployment, the preferred internal workflow is to create a compact model archive once from a working machine and reuse it for fresh clones and Docker hosts.

## Required Files

The current API expects these files under `backend/models`:

```text
backend/models/sttn-auto/infer_model.pth
backend/models/sttn-det/sttn.pth
backend/models/big-lama/big-lama.pt
backend/models/propainter/ProPainter.pth
backend/models/propainter/raft-things.pth
backend/models/propainter/recurrent_flow_completion.pth
backend/models/V5/ch_det/inference.pdiparams
backend/models/V5/ch_det_fast/inference.pdiparams
```

The `big-lama_*`, `ProPainter_*`, and `fs_manifest.csv` split files are optional when the merged `big-lama.pt` and `ProPainter.pth` files already exist. They are useful only for restoring merged files from split parts.

## Export From A Working Machine

Run this on a machine where VSR already works:

```bash
scripts/export-models.sh
```

To place the archive somewhere specific:

```bash
scripts/export-models.sh /mnt/video-manager/model-packages/video-subtitle-remover-models.tgz
```

Keep the resulting archive outside Git. Good locations are:

```text
NAS shared directory
GitHub Release asset
Hugging Face private/public model repository
internal HTTP file server
```

Current internal NAS archive:

```text
/mnt/video-manager/model-packages/video-subtitle-remover-models.tgz
sha256: 67d2ddd89ea63089702d8b97bea3438382dabefe37afc36efb5463fd8be4bd8f
```

## Install On A Fresh Clone

From a local archive:

```bash
scripts/install-models.sh /mnt/video-manager/model-packages/video-subtitle-remover-models.tgz
```

From HTTP:

```bash
VSR_MODEL_ARCHIVE_URL=https://example.com/video-subtitle-remover-models.tgz scripts/install-models.sh
```

From a mounted NAS path:

```bash
VSR_MODEL_ARCHIVE_URL=file:///mnt/video-manager/model-packages/video-subtitle-remover-models.tgz scripts/install-models.sh
```

After installation, build or restart the Docker service:

```bash
docker compose up -d --build
```

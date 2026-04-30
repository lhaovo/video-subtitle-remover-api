#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

OUT="${1:-dist/video-subtitle-remover-models-$(date +%Y%m%d).tgz}"

required_files=(
  "backend/models/sttn-auto/infer_model.pth"
  "backend/models/sttn-det/sttn.pth"
  "backend/models/big-lama/big-lama.pt"
  "backend/models/propainter/ProPainter.pth"
  "backend/models/propainter/raft-things.pth"
  "backend/models/propainter/recurrent_flow_completion.pth"
  "backend/models/V5/ch_det/inference.pdiparams"
  "backend/models/V5/ch_det_fast/inference.pdiparams"
)

missing=()
for file in "${required_files[@]}"; do
  if [ ! -f "$file" ]; then
    missing+=("$file")
  fi
done

if [ "${#missing[@]}" -gt 0 ]; then
  printf 'Missing model files:\n' >&2
  printf '  %s\n' "${missing[@]}" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUT")"
tar -czf "$OUT" backend/models

printf 'Model archive written: %s\n' "$OUT"
if command -v sha256sum >/dev/null 2>&1; then
  sha256sum "$OUT"
fi

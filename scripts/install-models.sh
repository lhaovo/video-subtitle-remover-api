#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

SOURCE="${1:-${VSR_MODEL_ARCHIVE_URL:-}}"
MODEL_DIR="${MODEL_DIR:-backend/models}"

usage() {
  cat >&2 <<'EOF'
Usage:
  scripts/install-models.sh /path/to/video-subtitle-remover-models.tgz
  VSR_MODEL_ARCHIVE_URL=https://example.com/video-subtitle-remover-models.tgz scripts/install-models.sh
  VSR_MODEL_ARCHIVE_URL=file:///mnt/nas/video-subtitle-remover-models.tgz scripts/install-models.sh

The archive may contain backend/models, models, or the model folders directly.
EOF
}

if [ -z "$SOURCE" ]; then
  usage
  exit 2
fi

tmp_dir="$(mktemp -d)"
cleanup() {
  rm -rf "$tmp_dir"
}
trap cleanup EXIT

archive="$tmp_dir/models-archive"

case "$SOURCE" in
  http://*|https://*)
    if command -v curl >/dev/null 2>&1; then
      curl -fL "$SOURCE" -o "$archive"
    elif command -v wget >/dev/null 2>&1; then
      wget -O "$archive" "$SOURCE"
    else
      echo "curl or wget is required to download models" >&2
      exit 1
    fi
    ;;
  file://*)
    cp "${SOURCE#file://}" "$archive"
    ;;
  *)
    cp "$SOURCE" "$archive"
    ;;
esac

extract_dir="$tmp_dir/extracted"
mkdir -p "$extract_dir"

if tar -tzf "$archive" >/dev/null 2>&1; then
  tar -xzf "$archive" -C "$extract_dir"
elif tar -tf "$archive" >/dev/null 2>&1; then
  tar -xf "$archive" -C "$extract_dir"
elif command -v unzip >/dev/null 2>&1 && unzip -t "$archive" >/dev/null 2>&1; then
  unzip -q "$archive" -d "$extract_dir"
else
  echo "Unsupported model archive format. Use .tgz, .tar.gz, .tar, or .zip." >&2
  exit 1
fi

mkdir -p "$MODEL_DIR"

if [ -d "$extract_dir/backend/models" ]; then
  cp -a "$extract_dir/backend/models/." "$MODEL_DIR/"
elif [ -d "$extract_dir/models" ]; then
  cp -a "$extract_dir/models/." "$MODEL_DIR/"
else
  copied=0
  for dir in V5 big-lama propainter sttn-auto sttn-det; do
    if [ -e "$extract_dir/$dir" ]; then
      cp -a "$extract_dir/$dir" "$MODEL_DIR/"
      copied=1
    fi
  done
  if [ "$copied" -eq 0 ]; then
    echo "Archive does not contain backend/models, models, or known model folders." >&2
    exit 1
  fi
fi

required_files=(
  "$MODEL_DIR/sttn-auto/infer_model.pth"
  "$MODEL_DIR/sttn-det/sttn.pth"
  "$MODEL_DIR/big-lama/big-lama.pt"
  "$MODEL_DIR/propainter/ProPainter.pth"
  "$MODEL_DIR/propainter/raft-things.pth"
  "$MODEL_DIR/propainter/recurrent_flow_completion.pth"
  "$MODEL_DIR/V5/ch_det/inference.pdiparams"
  "$MODEL_DIR/V5/ch_det_fast/inference.pdiparams"
)

missing=()
for file in "${required_files[@]}"; do
  if [ ! -f "$file" ]; then
    missing+=("$file")
  fi
done

if [ "${#missing[@]}" -gt 0 ]; then
  printf 'Model install finished, but required files are still missing:\n' >&2
  printf '  %s\n' "${missing[@]}" >&2
  exit 1
fi

echo "Models installed into $MODEL_DIR"

#!/usr/bin/env bash
# Runs the OOS Gold pipeline inside a local Docker container that stands in
# for a Microsoft Fabric Lakehouse notebook (PySpark).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="oos-fabric-demo:latest"

echo "Building image (skips layers that are already cached)..."
docker build -t "$IMAGE_NAME" -f "$REPO_DIR/Dockerfile" "$REPO_DIR"

echo "Running pipeline..."
docker run --rm \
  -v "$REPO_DIR:/home/gunjan/work" \
  -w /home/gunjan/work \
  "$IMAGE_NAME" \
  python src/pipeline.py

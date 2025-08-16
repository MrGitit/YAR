#!/bin/bash
set -e
cd "$(dirname "$0")"
source .venv/bin/activate
python -m src.main --script_path samples/script.txt --scenes 5 --out output/exports/yar_stills.mp4

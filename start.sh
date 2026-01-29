#!/bin/bash
# Quick start script for Hand Viewer
# Usage: ./start.sh [--verbose]

cd "$(dirname "$0")"
source venv/bin/activate
python hand_viewer/app.py "$@"


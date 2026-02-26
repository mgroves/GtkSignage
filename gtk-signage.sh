#!/usr/bin/env bash
set -e

export PYTHONPATH="/app/lib/python3.12/site-packages:/app/lib/gtk-signage"

exec python3 /app/lib/gtk-signage/main.py
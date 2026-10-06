#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn==21.2.0

echo "=== pip list ==="
pip list | grep -i gunicorn || echo "GUNICORN NOT INSTALLED"

python manage.py collectstatic --no-input
python manage.py migrate
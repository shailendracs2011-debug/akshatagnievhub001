#!/usr/bin/env bash
set -e
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
[ -f .env ] || cp .env.example .env
python manage.py migrate
python manage.py bootstrap_admin
python manage.py seed_data
python manage.py runserver

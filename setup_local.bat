@echo off
setlocal
py -3.13 -m venv .venv
call .venv\Scripts\activate
python -m pip install -r requirements.txt
if not exist .env copy .env.example .env
python manage.py migrate
python manage.py bootstrap_admin
python manage.py seed_data
python manage.py runserver

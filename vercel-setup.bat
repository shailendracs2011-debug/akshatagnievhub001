@echo off
REM Vercel Postgres Setup Script for Windows
REM Run this after installing Vercel CLI: npm i -g vercel

echo === Vercel PostgreSQL Setup ===
echo.
echo Step 1: Create Vercel Postgres database
call vercel postgres create aaev-hub-db
echo.
echo Step 2: Link database to project
call vercel link
call vercel postgres link aaev-hub-db
echo.
echo Step 3: Get DATABASE_URL
call vercel env pull .env.production
echo.
echo Step 4: Run migrations locally
python manage.py migrate
echo.
echo Step 5: Create superuser
python manage.py createsuperuser
echo.
echo Step 6: Seed initial data
python manage.py bootstrap_admin
python manage.py seed_data
echo.
echo === Setup Complete ===
echo Now push your code and deploy on Vercel
pause

#!/bin/bash
# Vercel Postgres Setup Script
# Run this after installing Vercel CLI: npm i -g vercel

echo "=== Vercel PostgreSQL Setup ==="
echo ""
echo "Step 1: Create Vercel Postgres database"
vercel postgres create aaev-hub-db
echo ""
echo "Step 2: Link database to project"
vercel link
vercel postgres link aaev-hub-db
echo ""
echo "Step 3: Get DATABASE_URL"
vercel env pull .env.production
echo ""
echo "Step 4: Run migrations locally"
python manage.py migrate
echo ""
echo "Step 5: Create superuser"
python manage.py createsuperuser
echo ""
echo "Step 6: Seed initial data"
python manage.py bootstrap_admin
python manage.py seed_data
echo ""
echo "=== Setup Complete ==="
echo "Now push your code and deploy on Vercel"

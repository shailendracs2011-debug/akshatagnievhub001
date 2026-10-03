# Akshat Agni EV Hub - Deployment Guide

## Prerequisites
- GitHub repository with this code pushed
- Vercel account (sign up at vercel.com)
- GoDaddy domain: `akshatagnievhub.in`
- PostgreSQL database (Supabase, Neon, Railway, or Vercel Postgres)

## Step 1: Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit for Vercel deployment"
git remote add origin https://github.com/YOUR_USERNAME/aaev-hub.git
git push -u origin main
```

## Step 2: Create PostgreSQL Database
Get your `DATABASE_URL` from:
- **Supabase**: Project Settings > Database > Connection string
- **Neon**: Dashboard > Connection Details
- **Railway**: Variables tab > DATABASE_URL

Format: `postgres://user:password@host:5432/dbname`

## Step 3: Deploy on Vercel
1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your GitHub repository
3. Vercel auto-detects Django configuration

## Step 4: Set Environment Variables
In Vercel Dashboard > Settings > Environment Variables, add:

| Variable | Value |
|----------|-------|
| `SECRET_KEY` | Generate at https://djecrety.ir/ |
| `DATABASE_URL` | Your PostgreSQL connection string |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `akshatagnievhub.in,www.akshatagnievhub.in,.vercel.app` |
| `CSRF_TRUSTED_ORIGINS` | `https://akshatagnievhub.in,https://www.akshatagnievhub.in` |

## Step 5: Deploy
Click **Deploy** button in Vercel. Wait for build to complete (~2-3 minutes).

## Step 6: Connect Domain
1. In Vercel: Settings > Domains > Add `akshatagnievhub.in` and `www.akshatagnievhub.in`
2. In GoDaddy: Update nameservers to Vercel's nameservers OR update A records:
   - `@` → `76.76.21.21`
   - `www` → `76.76.21.21`

## Step 7: Create Admin User
After deployment, run:
```bash
vercel env pull .env.production
python manage.py createsuperuser
python manage.py bootstrap_admin
```

## Post-Deployment Checklist
- [ ] Visit https://akshatagnievhub.in - website loads
- [ ] Visit https://akshatagnievhub.in/admin - admin panel works
- [ ] Visit https://akshatagnievhub.in/erp/ - ERP dashboard loads
- [ ] Test Excel export from all ERP pages
- [ ] Configure company settings at /erp/settings/
- [ ] Upload logo, signature, and company details
- [ ] Test PDF invoice generation
- [ ] Verify SSL certificate is active (HTTPS)

## Important Notes
- **Never commit `.env` or `.env.production`** - they contain secrets
- **Database migrations** run automatically on Vercel deploy
- **Static files** are collected automatically via WhiteNoise
- **Media files** (logo, signature) are stored as base64 in database - no S3 needed
- **Logs** available in Vercel Dashboard > Deployments > Logs

## Troubleshooting
- **Build fails**: Check Vercel build logs for missing dependencies
- **Database errors**: Verify DATABASE_URL format and PostgreSQL version
- **Static files not loading**: Ensure `collectstatic` ran during build
- **CSRF errors**: Verify `CSRF_TRUSTED_ORIGINS` includes your domain with `https://`
- **Image upload errors**: Check `DATA_UPLOAD_MAX_MEMORY_SIZE` in settings

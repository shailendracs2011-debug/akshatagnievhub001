@echo off
setlocal enabledelayedexpansion

echo ==============================================
echo   AAeV Hub - Vercel Deployment Helper
echo ==============================================
echo.

set "REPO_DIR=C:\Users\Shailendra Patel\Documents\AAeVHub_live\aaev_dev"

echo [1/6] Checking Git installation...
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo Git not found. Installing Git via winget...
    call winget install --id Git.Git --accept-package-agreements --accept-source-agreements
    echo Please restart PowerShell and run this script again.
    pause
    exit /b 1
) else (
    echo Git is installed.
)

echo.
echo [2/6] Configuring Git repository...
cd /d "%REPO_DIR%"

git config user.email "deploy@aaevhub.local" >nul 2>nul
git config user.name "Deploy Script" >nul 2>nul

if not exist ".git" (
    git init
    echo Initialized new git repository.
) else (
    echo Git repository already exists.
)

echo.
echo [3/6] Staging files...
git add .
git status --short | findstr "^M" >nul
if %errorlevel% equ 0 (
    echo Note: You have modified tracked files. Review changes before committing.
    pause
)

echo.
echo [4/6] Creating commit...
git commit -m "Deploy: prepare for Vercel production deployment" || (
    echo Nothing to commit or commit failed. Continuing...
)

echo.
echo [5/6] Setting remote and pushing...
set /p GITHUB_REPO="Enter your GitHub repo URL (e.g. https://github.com/username/aaev-hub.git): "
if "!GITHUB_REPO!"=="" (
    echo Skipped: No repo URL provided.
) else (
    git remote remove origin >nul 2>nul
    git remote add origin "!GITHUB_REPO!"
    git branch -M main
    git push -u origin main || (
        echo Push failed. Check your GitHub credentials and repo URL.
        pause
    )
)

echo.
echo [6/6] Generating environment summary...
echo.
echo ==============================================
echo   NEXT STEPS
echo ==============================================
echo.
echo 1. Go to https://vercel.com/new
echo 2. Import your GitHub repository
echo 3. Set these Environment Variables in Vercel:
echo.
echo    SECRET_KEY=^<generate-at-djecrety.ir^>
echo    DATABASE_URL=^<your-postgres-connection-string^>
echo    DEBUG=False
echo    ALLOWED_HOSTS=akshatagnievhub.in,www.akshatagnievhub.in,.vercel.app
echo    CSRF_TRUSTED_ORIGINS=https://akshatagnievhub.in,https://www.akshatagnievhub.in
echo.
echo 4. Click Deploy in Vercel
echo 5. After deploy, add domain in Vercel:
echo    - akshatagnievhub.in
echo    - www.akshatagnievhub.in
echo 6. In GoDaddy, update nameservers to Vercel nameservers
echo    OR update A records:
echo      @ ^> 76.76.21.21
echo      www ^> 76.76.21.21
echo.
echo ==============================================
echo.
pause

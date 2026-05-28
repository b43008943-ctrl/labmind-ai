@echo off
title LabMind AI — Starting...
color 0A

echo.
echo  ==========================================
echo   LabMind AI — Smart Analyst System
echo  ==========================================
echo.

echo  [1/5] Starting Redis + PostgreSQL...
docker-compose up -d
timeout /t 3 /nobreak > nul
echo  Done!
echo.

echo  [2/5] Getting current IP address...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4" ^| findstr "192.168"') do (
  set IP=%%a
)
set IP=%IP: =%
echo  IP: %IP%
echo.

echo  [3/5] Starting Backend...
start "LabMind Backend" cmd /k "cd /d d:\New folder\ai-backend && .venv\Scripts\activate && uvicorn app.main:app --host 0.0.0.0 --port 8000"
timeout /t 5 /nobreak > nul
echo  Backend starting...
echo.

echo  [4/5] Starting Celery Worker...
start "LabMind Celery" cmd /k "cd /d d:\New folder\ai-backend && .venv\Scripts\activate && celery -A app.workers.celery_app worker --loglevel=info"
timeout /t 3 /nobreak > nul
echo  Celery starting...
echo.

echo  [5/5] Building and serving Frontend...
cd /d "d:\New folder"
taskkill /F /IM node.exe > nul 2>&1
timeout /t 2 /nobreak > nul
call npm run build
start "LabMind Frontend" cmd /k "cd /d d:\New folder && serve -s dist -l 5173"
timeout /t 5 /nobreak > nul
echo.

echo  ==========================================
echo   App ready! Open on your phone:
echo   http://%IP%:5173
echo  ==========================================
echo.
start http://%IP%:5173
pause

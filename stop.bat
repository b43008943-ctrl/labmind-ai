@echo off
echo Stopping LabMind AI...
docker-compose down
taskkill /fi "windowtitle eq LabMind*" /f > nul 2>&1
taskkill /F /IM cloudflared.exe > nul 2>&1
echo Done!
pause

@echo off
setlocal
cd /d "%~dp0"
if not exist ".env" (
    powershell.exe -NoProfile -File configure.ps1
    if errorlevel 1 goto failed
)
docker compose up -d --wait metadata redis analytics
if errorlevel 1 goto failed
if not exist ".redash-initialized" (
    docker compose run --rm server create_db
    if errorlevel 1 goto failed
    type nul > ".redash-initialized"
)
docker compose up -d
if errorlevel 1 goto failed
docker compose exec -T server python /bootstrap/provision.py
if errorlevel 1 goto failed
start "" "http://localhost:5000/dashboards"
pause
exit /b 0
:failed
echo.
echo Setup stopped. Send the error shown above to ChatGPT.
echo If the admin account is not configured, open http://localhost:5000/setup and run this file again.
pause
exit /b 1

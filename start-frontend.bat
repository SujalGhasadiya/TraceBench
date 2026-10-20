@echo off
cd /d "%~dp0frontend"
title TraceBench Frontend (Port 5173)

echo ========================================================
echo Starting TraceBench Frontend UI (Vite + React)...
echo ========================================================

npm run dev

pause

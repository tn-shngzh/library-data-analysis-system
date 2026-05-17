@echo off
chcp 65001 >nul 2>&1

echo ========================================
echo    Library Data Analysis System
echo ========================================
echo.

echo Cleaning up old processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr "LISTENING" ^| findstr ":8000 "') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr "LISTENING" ^| findstr ":5174 "') do taskkill /F /PID %%a >nul 2>&1

set ROOT=%~dp0
set BACKEND=%ROOT%library_data_analysis_fastapi
set FRONTEND=%ROOT%library_data_analysis_vue

echo [1/2] Starting Backend (FastAPI)...
start "FastAPI Backend" cmd /k "cd /d %BACKEND% && python main.py"

echo [2/2] Starting Frontend (Vue)...
start "Vue Frontend" cmd /k "cd /d %FRONTEND% && npm run dev"

echo.
echo Starting...
echo Backend: http://127.0.0.1:8000
echo Frontend: http://localhost:5174
echo.
echo Done!
pause

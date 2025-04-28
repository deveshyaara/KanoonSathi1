@echo off
echo ===================================
echo KanoonSathi Deployment Startup Script
echo ===================================

REM Check if .env file exists
if not exist .env (
  echo Error: .env file not found.
  echo Please create an .env file with your environment variables.
  echo You can use .env.example as a template.
  exit /b 1
)

REM Start the backend server
echo Starting KanoonSathi backend server...
start cmd /k "cd backend && python server.py"

REM Wait for backend to initialize
echo Waiting for backend to initialize...
timeout /t 5 /nobreak > nul

REM Start the Next.js frontend
echo Starting KanoonSathi frontend...
start cmd /k "npm run dev"

echo ===================================
echo KanoonSathi application started successfully!
echo Backend: %NEXT_PUBLIC_BACKEND_URL% ^(from .env^)
echo Frontend: %NEXT_PUBLIC_APP_URL% ^(from .env^)
echo ===================================
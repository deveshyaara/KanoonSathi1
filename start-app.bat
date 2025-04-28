@echo off
echo ===================================
echo KanoonSathi Production Startup Script
echo ===================================

REM Set environment to production
set NODE_ENV=production

REM Verify setup using deployment helper
echo Running deployment verification...
node deployment-setup.js
if %ERRORLEVEL% NEQ 0 (
  echo Deployment verification failed. Please fix the issues and try again.
  exit /b 1
)

REM Build Next.js application if not already built
if not exist .next (
  echo Building Next.js application...
  call npm run build
  if %ERRORLEVEL% NEQ 0 (
    echo Next.js build failed. Please fix any issues and try again.
    exit /b 1
  )
)

REM Start the backend server
echo Starting KanoonSathi backend server...
start cmd /k "cd backend && python server.py"

REM Wait for backend to initialize
echo Waiting for backend to initialize...
timeout /t 5 /nobreak > nul

REM Start the Next.js production server
echo Starting KanoonSathi frontend in production mode...
start cmd /k "npm start"

echo ===================================
echo KanoonSathi production application started successfully!
echo Backend: %NEXT_PUBLIC_BACKEND_URL%
echo Frontend: %NEXT_PUBLIC_APP_URL%
echo ===================================
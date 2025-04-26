@echo off
echo ===============================================
echo KanoonSathi App Launcher
echo ===============================================

echo Starting Python Backend on port 8001...
start cmd /k "cd backend && python server.py"

echo Starting Vite Frontend on port 5173...
start cmd /k "cd legal-reader-ui && npm run dev"

echo.
echo Services started! Access the application at:
echo - Frontend: http://localhost:5173
echo - Backend API: http://localhost:8001
echo.
echo Press any key to close this window (services will continue running)
pause > nul
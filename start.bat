@echo off
echo =======================================================
echo Starting CargoScope Platform
echo =======================================================
echo.
echo Starting FastAPI Backend API...
start "CargoScope Backend" cmd /k "cd backend && venv\Scripts\activate && uvicorn main:app --reload --port 8000"

echo Starting Vite React Frontend (Web)...
start "CargoScope Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Services are launching in separate windows!
echo - Backend will be available at: http://localhost:8000/docs
echo - Frontend will be available at: http://localhost:5173
echo.
pause

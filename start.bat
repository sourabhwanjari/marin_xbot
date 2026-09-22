@echo off
TITLE MARINEX AI System Launcher
COLOR 0B
echo ======================================================================
echo                  MARINEX AI: MARINE INTELLIGENCE
echo         AI-Powered Marine Intelligence & Decision Support
echo       ORCA: Marine EcOsystem Reasoning with Collaborative Agents
echo ======================================================================
echo.
echo Starting Backend (FastAPI on http://localhost:8000)...
start "MARINEX AI Backend Server" cmd /k "cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo.
echo Starting Frontend (Next.js on http://localhost:3000)...
start "MARINEX AI Frontend Client" cmd /k "cd frontend && npm run dev"

echo.
echo ======================================================================
echo  Both services launched in separate windows!
echo  - Backend API:   http://localhost:8000 (Docs: http://localhost:8000/docs)
echo  - Frontend App:  http://localhost:3000
echo ======================================================================
echo.
pause

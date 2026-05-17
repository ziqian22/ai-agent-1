@echo off
echo Starting Banner Designer...

REM Check .env file
if not exist ".env" (
    echo Error: .env file not found
    echo Please create .env file with:
    echo   CLAUDE_API_KEY=your_key
    echo   CLAUDE_BASE_URL=your_url
    echo   RUNNINGHUB_API_KEY=your_key
    pause
    exit /b 1
)

REM Start backend
echo Starting backend on port 8000...
start "Backend" cmd /k "cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000"

REM Wait for backend
timeout /t 3 /nobreak >nul

REM Start frontend
echo Starting frontend on port 3000...
start "Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Services started successfully!
echo Frontend: http://localhost:3000
echo Backend: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Close Backend and Frontend windows to stop services
pause

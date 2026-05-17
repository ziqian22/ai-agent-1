@echo off
chcp 65001 >nul
echo ========================================
echo Running Hub Workflow Test Tool
echo ========================================
echo.
echo Starting application...
echo.

cd /d "%~dp0"
streamlit run app.py

pause

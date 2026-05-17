@echo off
chcp 65001 >nul
echo ========================================
echo 易拉宝AI Agent 启动脚本
echo ========================================
echo.

echo 正在启动易拉宝AI设计助手...
echo.
echo 浏览器将自动打开 http://localhost:8501
echo.
echo 按 Ctrl+C 可以停止服务
echo ========================================
echo.

streamlit run agent_app.py

pause

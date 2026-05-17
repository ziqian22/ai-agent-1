@echo off
chcp 65001 >nul
echo 🔍 检查部署准备情况...
echo.

echo 📁 检查配置文件...
set "all_exist=true"

if exist "railway.json" (echo ✅ railway.json) else (echo ❌ railway.json 不存在 & set "all_exist=false")
if exist "nixpacks.toml" (echo ✅ nixpacks.toml) else (echo ❌ nixpacks.toml 不存在 & set "all_exist=false")
if exist "backend\requirements.txt" (echo ✅ backend\requirements.txt) else (echo ❌ backend\requirements.txt 不存在 & set "all_exist=false")
if exist "frontend\.env.production" (echo ✅ frontend\.env.production) else (echo ❌ frontend\.env.production 不存在 & set "all_exist=false")
if exist ".gitignore" (echo ✅ .gitignore) else (echo ❌ .gitignore 不存在 & set "all_exist=false")

echo.
echo 🔑 检查环境变量配置...
if exist ".env.example" (
    echo ✅ .env.example 存在
    echo    请确保在 Railway 中配置以下变量：
    echo    - CLAUDE_API_KEY
    echo    - RUNNINGHUB_API_KEY
    echo    - CLAUDE_BASE_URL
) else (
    echo ❌ .env.example 不存在
    set "all_exist=false"
)

echo.
echo 📦 检查 Git 状态...
if exist ".git" (
    echo ✅ Git 已初始化
    git remote -v 2>nul | findstr "origin" >nul
    if %errorlevel% equ 0 (
        echo ✅ 已配置远程仓库
    ) else (
        echo ⚠️  未配置远程仓库
        echo    运行: git remote add origin ^<你的GitHub仓库地址^>
    )
) else (
    echo ❌ Git 未初始化
    echo    运行: git init
    set "all_exist=false"
)

echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if "%all_exist%"=="true" (
    echo ✅ 所有检查通过！可以开始部署了
    echo.
    echo 📝 下一步：
    echo 1. 推送代码到 GitHub: git push origin main
    echo 2. 访问 https://railway.app
    echo 3. 选择 'Deploy from GitHub repo'
    echo 4. 配置环境变量
    echo.
    echo 详细步骤请查看: QUICK_DEPLOY.md
) else (
    echo ❌ 有些检查未通过，请先解决上述问题
)

echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
pause

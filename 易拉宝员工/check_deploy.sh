#!/bin/bash

echo "🔍 检查部署准备情况..."
echo ""

# 检查必要文件
echo "📁 检查配置文件..."
files=(
    "railway.json"
    "nixpacks.toml"
    "backend/requirements.txt"
    "frontend/.env.production"
    ".gitignore"
)

all_exist=true
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file 不存在"
        all_exist=false
    fi
done

echo ""

# 检查环境变量示例
echo "🔑 检查环境变量配置..."
if [ -f ".env.example" ]; then
    echo "✅ .env.example 存在"
    echo "   请确保在 Railway 中配置以下变量："
    grep -v "^#" .env.example | grep "=" | cut -d= -f1 | sed 's/^/   - /'
else
    echo "❌ .env.example 不存在"
    all_exist=false
fi

echo ""

# 检查 Git 状态
echo "📦 检查 Git 状态..."
if [ -d ".git" ]; then
    echo "✅ Git 已初始化"

    # 检查是否有远程仓库
    if git remote -v | grep -q "origin"; then
        echo "✅ 已配置远程仓库"
        git remote -v | head -2
    else
        echo "⚠️  未配置远程仓库"
        echo "   运行: git remote add origin <你的GitHub仓库地址>"
    fi

    # 检查未提交的更改
    if [ -n "$(git status --porcelain)" ]; then
        echo "⚠️  有未提交的更改"
        echo "   运行: git add . && git commit -m 'Ready for deployment'"
    else
        echo "✅ 没有未提交的更改"
    fi
else
    echo "❌ Git 未初始化"
    echo "   运行: git init"
    all_exist=false
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$all_exist" = true ]; then
    echo "✅ 所有检查通过！可以开始部署了"
    echo ""
    echo "📝 下一步："
    echo "1. 推送代码到 GitHub: git push origin main"
    echo "2. 访问 https://railway.app"
    echo "3. 选择 'Deploy from GitHub repo'"
    echo "4. 配置环境变量"
    echo ""
    echo "详细步骤请查看: QUICK_DEPLOY.md"
else
    echo "❌ 有些检查未通过，请先解决上述问题"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

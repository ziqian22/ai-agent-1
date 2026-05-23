#!/bin/bash

# 易拉宝设计助手 - 一键部署脚本

set -e

echo "🚀 开始部署易拉宝设计助手..."

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "⚠️  未找到 .env 文件，从 .env.example 复制..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ 已创建 .env 文件，请编辑并填入你的 API Keys"
        echo "📝 编辑命令: nano .env"
        exit 0
    else
        echo "❌ 未找到 .env.example 文件"
        exit 1
    fi
fi

# 检查必需的环境变量
source .env
if [ -z "$CLAUDE_API_KEY" ] || [ -z "$RUNNINGHUB_API_KEY" ]; then
    echo "❌ 请在 .env 文件中设置 CLAUDE_API_KEY 和 RUNNINGHUB_API_KEY"
    exit 1
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p results temp_uploads knowledge_base/files

# 构建前端
echo "🔨 构建前端..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi
npm run build
cd ..

# 构建并启动 Docker 容器
echo "🐳 构建 Docker 镜像..."
docker-compose build

echo "🚀 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
if docker-compose ps | grep -q "Up"; then
    echo "✅ 部署成功！"
    echo ""
    echo "📍 访问地址:"
    echo "   - 前端: http://localhost"
    echo "   - 后端 API: http://localhost:8000"
    echo "   - API 文档: http://localhost:8000/docs"
    echo ""
    echo "📊 查看日志: docker-compose logs -f"
    echo "🛑 停止服务: docker-compose down"
else
    echo "❌ 服务启动失败，请查看日志:"
    docker-compose logs
    exit 1
fi

#!/bin/bash

# 易拉宝设计助手 - 启动脚本

echo "🚀 启动易拉宝AI设计助手..."

# 检查环境变量
if [ ! -f ".env" ]; then
    echo "❌ 错误: 未找到 .env 文件"
    echo "请创建 .env 文件并配置以下环境变量:"
    echo "  CLAUDE_API_KEY=your_claude_api_key"
    echo "  CLAUDE_BASE_URL=your_claude_base_url (可选)"
    echo "  RUNNINGHUB_API_KEY=your_runninghub_api_key"
    exit 1
fi

# 启动后端
echo "📦 启动后端服务 (端口 8000)..."
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# 等待后端启动
sleep 3

# 启动前端
echo "🎨 启动前端服务 (端口 3000)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ 服务启动成功!"
echo "📱 前端地址: http://localhost:3000"
echo "🔧 后端地址: http://localhost:8000"
echo "📖 API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 捕获退出信号
trap "echo ''; echo '🛑 停止服务...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM

# 等待
wait

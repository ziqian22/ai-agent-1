# 易拉宝AI设计助手

基于 Claude Opus 4.7 和 Running Hub API 的智能易拉宝设计助手。

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/new)

## ✨ 功能特点

- 📤 **多格式支持**: 支持图片（PNG/JPG）和文档（PDF/Word/PPT）上传
- 🤖 **智能对话**: Claude 驱动的自然对话式交互
- 🎨 **自动设计**: 基于产品信息自动生成专业易拉宝
- 🖼️ **智能抠图**: 自动去除产品图片背景
- 💬 **流畅体验**: 无需繁琐确认,自然沟通即可完成设计
- 🎯 **多风格支持**: 科技感、简约商务、自然清新等多种风格

## 🚀 快速部署（推荐）

### Railway 一键部署

1. 点击上方 "Deploy on Railway" 按钮
2. 连接 GitHub 账号
3. 配置环境变量（见下方）
4. 等待部署完成

详细步骤：[QUICK_DEPLOY.md](./QUICK_DEPLOY.md)

### 环境变量配置

```env
CLAUDE_API_KEY=你的Claude API密钥
RUNNINGHUB_API_KEY=你的RunningHub API密钥
CLAUDE_BASE_URL=你的Claude API地址（可选）
```

## 技术栈

### 后端
- FastAPI
- Claude Opus 4.7 Vision API
- Running Hub API
- Python 3.8+

### 前端
- Vue 3
- Element Plus
- Vite

## 快速开始

### 1. 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install
cd ..
```

### 2. 配置环境变量

创建 `.env` 文件:

```env
CLAUDE_API_KEY=your_claude_api_key
CLAUDE_BASE_URL=your_claude_base_url  # 可选
RUNNINGHUB_API_KEY=your_runninghub_api_key
```

### 3. 启动服务

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

**或手动启动:**

```bash
# 启动后端 (端口 8000)
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 启动前端 (端口 3000)
cd frontend
npm run dev
```

### 4. 访问应用

- 前端: http://localhost:3000
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

## 使用流程

1. **上传文件**: 拖拽或点击上传产品图片或文档
2. **确认信息**: AI 自动分析产品信息,与您确认
3. **选择风格**: 选择设计风格偏好
4. **生成易拉宝**: AI 自动生成专业易拉宝设计
5. **下载结果**: 查看并下载生成的易拉宝图片

## API 接口

### POST /api/upload
上传文件并分析产品信息

**请求:**
- `file`: 文件 (multipart/form-data)

**响应:**
```json
{
  "session_id": "uuid",
  "analysis": "分析结果文本",
  "product_info": {
    "product_name": "产品名称",
    "brand": "品牌",
    "slogan": "核心卖点",
    "features": ["特点1", "特点2"],
    "scenes": ["场景1", "场景2"]
  }
}
```

### POST /api/chat
发送对话消息

**请求:**
```json
{
  "session_id": "uuid",
  "message": "用户消息"
}
```

**响应:**
```json
{
  "type": "message|generating|result",
  "content": "回复内容",
  "images": ["图片URL1", "图片URL2"],
  "progress": 50
}
```

## 项目结构

```
.
├── backend/
│   └── main.py              # FastAPI 后端
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── chat.js      # API 调用
│   │   ├── components/
│   │   │   └── ChatArea.vue # 对话组件
│   │   ├── App.vue          # 主应用
│   │   └── main.js          # 入口文件
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── vision_analyzer.py       # 图片/文档分析
├── banner_generator.py      # 易拉宝生成
├── banner_prompt_template.py # Prompt 模板
├── requirements.txt
├── .env.example
├── start.sh                 # Linux/Mac 启动脚本
└── start.bat                # Windows 启动脚本
```

## 注意事项

- 确保已配置正确的 API Key
- Running Hub API 生成的图片 URL 有效期为 24 小时
- 大型文档分析可能需要较长时间
- 建议使用 Chrome/Edge 浏览器以获得最佳体验

## License

MIT

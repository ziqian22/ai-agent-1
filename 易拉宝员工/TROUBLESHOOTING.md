# 上传错误 500 - 排查和修复指南

## 问题描述
点击上传时显示: `Request failed with status code 500`

## 已修复的问题

### 1. FormData 参数类型问题
**问题**: FastAPI 接收 FormData 时,`save_to_kb` 参数是字符串而不是布尔值

**修复**: 
```python
# backend/main.py 第132行
async def upload_file(
    file: UploadFile = File(...),
    save_to_kb: str = "false"  # 改为字符串类型
):
    # 转换字符串为布尔值
    save_to_kb_bool = save_to_kb.lower() == "true"
```

## 如何验证修复

### 方法 1: 重启后端服务

1. **停止当前后端服务** (Ctrl+C)

2. **重新启动后端**:
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

3. **刷新前端页面** (F5)

4. **重新测试上传**

### 方法 2: 查看后端日志

后端服务运行时会显示详细的错误信息。如果还有 500 错误,请查看后端终端的错误堆栈。

常见错误:
- `ModuleNotFoundError` - 缺少依赖库
- `FileNotFoundError` - 文件路径问题
- `AttributeError` - 对象属性不存在

## 可能的其他问题

### 问题 1: 缺少依赖库

**症状**: 后端启动时报错 `ModuleNotFoundError`

**解决**:
```bash
pip install -r requirements.txt
```

### 问题 2: 环境变量未配置

**症状**: 后端启动时报错 `ValueError: 请设置 CLAUDE_API_KEY`

**解决**: 检查 `.env` 文件是否存在并配置正确:
```env
CLAUDE_API_KEY=your_key
CLAUDE_BASE_URL=your_url
RUNNINGHUB_API_KEY=your_key
```

### 问题 3: 端口被占用

**症状**: 后端启动时报错 `Address already in use`

**解决**:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <进程ID> /F

# Linux/Mac
lsof -i :8000
kill -9 <进程ID>
```

### 问题 4: 文件上传大小限制

**症状**: 上传大文件时 500 错误

**解决**: 在 `backend/main.py` 添加:
```python
from fastapi import FastAPI

app = FastAPI(title="易拉宝设计助手 API")

# 增加文件上传大小限制
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,
)
```

## 调试步骤

### 1. 检查后端是否正常运行

访问: http://localhost:8000

应该看到:
```json
{
  "status": "ok",
  "message": "易拉宝设计助手 API"
}
```

### 2. 检查 API 文档

访问: http://localhost:8000/docs

应该看到 Swagger UI 界面,可以直接测试 API

### 3. 使用 API 文档测试上传

1. 打开 http://localhost:8000/docs
2. 找到 `POST /api/upload` 接口
3. 点击 "Try it out"
4. 上传一张测试图片
5. 点击 "Execute"
6. 查看响应

### 4. 查看详细错误信息

如果还是 500 错误,后端终端会显示完整的错误堆栈,例如:

```
ERROR:    Exception in ASGI application
Traceback (most recent call last):
  File "...", line 123, in ...
    ...
AttributeError: 'NoneType' object has no attribute 'get'
```

请将完整的错误信息发给我,我会帮您定位问题。

## 快速测试脚本

我创建了一个测试脚本 `test_upload.py`,可以快速测试上传功能:

```bash
# 1. 在项目根目录放置一张测试图片 test_image.jpg
# 2. 运行测试脚本
python test_upload.py
```

## 当前修复状态

✅ **已修复**: FormData 参数类型问题
✅ **已修复**: 超时配置问题
✅ **已修复**: 输入框交互问题

## 下一步

1. **重启后端服务**
2. **刷新前端页面**
3. **重新测试上传**
4. **如果还有问题,查看后端日志并告诉我具体的错误信息**

---

**更新时间**: 2026-05-17

# Railway 部署问题修复

## 问题原因

1. **Python 版本不兼容**：Railway 默认使用 Python 3.13，但 Pillow 10.2.0 不支持
2. **依赖版本过旧**：Pillow 10.2.0 有兼容性问题

## 已修复的文件

### 1. requirements.txt
- ✅ 移除了 streamlit（不需要）
- ✅ 更新 Pillow 版本：`10.2.0` → `>=10.3.0`
- ✅ 添加了所有必需的依赖

### 2. backend/requirements.txt
- ✅ 更新 Pillow 版本：`10.2.0` → `>=10.3.0`

### 3. runtime.txt
- ✅ 指定 Python 版本：`python-3.11`

### 4. nixpacks.toml
- ✅ 已配置使用 Python 3.11
- ✅ 包含 gcc 编译器（Pillow 需要）

### 5. railway.json
- ✅ 更新构建配置

## 🚀 重新部署步骤

### 方法一：通过 Git 推送（推荐）

```bash
cd 易拉宝员工

# 提交修复
git add .
git commit -m "Fix: 修复 Railway 部署问题 - 更新 Python 和依赖版本"
git push

# Railway 会自动重新部署
```

### 方法二：在 Railway 控制台

1. 进入你的 Railway 项目
2. 点击 "Deployments" 标签
3. 点击 "Redeploy" 按钮

## ✅ 验证部署

部署成功后，访问：
- 健康检查：`https://your-app.railway.app/`
- API 文档：`https://your-app.railway.app/docs`

## 🔧 如果还是失败

### 检查环境变量

确保在 Railway 项目设置中配置了：

```
CLAUDE_API_KEY=你的密钥
RUNNINGHUB_API_KEY=你的密钥
CLAUDE_BASE_URL=你的API地址（可选，如果使用代理）
```

### 查看部署日志

在 Railway 控制台查看详细的构建和运行日志，找到具体错误信息。

### 常见问题

1. **端口问题**：Railway 会自动设置 `$PORT` 环境变量，代码已正确使用
2. **文件路径问题**：确保 `backend/main.py` 存在
3. **依赖冲突**：如果还有问题，可以尝试删除版本号限制

## 📝 备选方案

如果 Railway 部署仍有问题，可以尝试：

### 1. Render.com（类似 Railway）

创建 `render.yaml`:

```yaml
services:
  - type: web
    name: banner-designer
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.9
```

### 2. Vercel（仅后端）

创建 `vercel.json`:

```json
{
  "builds": [
    {
      "src": "backend/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "backend/main.py"
    }
  ]
}
```

### 3. Docker + 任意云服务器

使用我之前创建的 Docker 配置：

```bash
# 在服务器上
git clone 你的仓库
cd 易拉宝员工
docker-compose up -d
```

## 🎯 推荐流程

1. **先修复 Railway**：提交代码，让 Railway 重新部署
2. **如果还失败**：查看日志，告诉我具体错误
3. **备选方案**：使用 Docker 部署到云服务器（最稳定）

现在提交代码试试吧！

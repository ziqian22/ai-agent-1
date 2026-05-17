# 易拉宝AI设计助手 - 部署指南

## 🚀 Railway 部署步骤

### 1. 准备工作

确保你有：
- GitHub 账号
- Railway 账号（用 GitHub 登录即可）
- 项目的 API Keys：
  - `CLAUDE_API_KEY`
  - `RUNNINGHUB_API_KEY`

### 2. 推送代码到 GitHub

```bash
# 初始化 Git（如果还没有）
git init
git add .
git commit -m "Initial commit"

# 创建 GitHub 仓库后推送
git remote add origin https://github.com/你的用户名/你的仓库名.git
git branch -M main
git push -u origin main
```

### 3. 在 Railway 部署

1. 访问 https://railway.app
2. 点击 "Start a New Project"
3. 选择 "Deploy from GitHub repo"
4. 选择你的仓库
5. Railway 会自动检测并部署

### 4. 配置环境变量

在 Railway 项目设置中添加：

```
CLAUDE_API_KEY=你的Claude API密钥
RUNNINGHUB_API_KEY=你的RunningHub API密钥
CLAUDE_BASE_URL=你的Claude API地址（可选）
```

### 5. 配置前端 API 地址

部署完成后，Railway 会给你一个域名，例如：
`https://your-app.railway.app`

在前端代码中更新 API 地址：
- 编辑 `frontend/src/api/chat.js`
- 将 API_BASE_URL 改为你的 Railway 域名

重新提交代码：
```bash
git add .
git commit -m "Update API URL"
git push
```

Railway 会自动重新部署。

### 6. 访问应用

部署完成后，访问 Railway 提供的域名即可使用。

## 📊 预计成本

Railway 免费额度：
- $5/月免费额度
- 对于试用阶段完全够用
- 超出后按使用量计费（约 $0.000231/分钟）

## 🔧 故障排查

### 部署失败
- 检查 `requirements.txt` 是否完整
- 查看 Railway 部署日志

### API 调用失败
- 确认环境变量已正确设置
- 检查 CORS 配置

### 图片无法显示
- 确认静态文件目录已创建
- 检查文件路径是否正确

## 📝 注意事项

1. **API Keys 安全**：不要将 `.env` 文件提交到 Git
2. **文件存储**：Railway 重启后临时文件会丢失，建议使用对象存储（如 AWS S3）
3. **数据库**：如需持久化数据，建议添加 PostgreSQL 服务

## 🎯 生产环境优化建议

1. **使用对象存储**：将生成的图片存储到 S3/OSS
2. **添加数据库**：使用 PostgreSQL 存储对话历史
3. **配置域名**：绑定自定义域名
4. **启用 CDN**：加速静态资源访问
5. **监控告警**：配置 Railway 的监控功能

## 🆘 需要帮助？

- Railway 文档：https://docs.railway.app
- 项目 Issues：提交到 GitHub Issues

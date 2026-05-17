# 易拉宝AI设计助手

快速部署到 Railway 的完整指南。

## 📋 部署前检查清单

- [x] 已创建 Railway 配置文件
- [x] 已创建后端 requirements.txt
- [x] 已配置前端环境变量支持
- [x] 已更新 .gitignore
- [ ] 需要推送代码到 GitHub
- [ ] 需要在 Railway 配置环境变量

## 🚀 快速部署（3 步完成）

### 第 1 步：推送到 GitHub

```bash
# 如果还没有初始化 Git
git init
git add .
git commit -m "准备部署到 Railway"

# 在 GitHub 创建新仓库后
git remote add origin https://github.com/你的用户名/仓库名.git
git branch -M main
git push -u origin main
```

### 第 2 步：在 Railway 部署

1. 访问 https://railway.app （用 GitHub 登录）
2. 点击 **"New Project"** → **"Deploy from GitHub repo"**
3. 选择你刚推送的仓库
4. Railway 会自动开始部署

### 第 3 步：配置环境变量

在 Railway 项目页面：
1. 点击项目 → **"Variables"** 标签
2. 添加以下环境变量：

```
CLAUDE_API_KEY=你的Claude密钥
RUNNINGHUB_API_KEY=你的RunningHub密钥
CLAUDE_BASE_URL=你的Claude地址（可选）
```

3. 保存后 Railway 会自动重新部署

### 第 4 步：更新前端 API 地址

部署完成后，Railway 会给你一个域名，例如：
```
https://your-app-production.up.railway.app
```

编辑 `frontend/.env.production`：
```env
VITE_API_URL=https://your-app-production.up.railway.app
```

重新提交：
```bash
git add frontend/.env.production
git commit -m "更新生产环境 API 地址"
git push
```

✅ **完成！** 等待 Railway 重新部署后即可访问。

## 💰 费用说明

- **免费额度**：$5/月
- **试用阶段**：完全够用
- **预估使用**：轻度使用约 $2-3/月

## 🔍 查看部署状态

在 Railway 项目页面可以看到：
- **Deployments**：部署历史和日志
- **Metrics**：CPU、内存使用情况
- **Logs**：实时运行日志

## ⚠️ 重要提示

1. **不要提交 .env 文件**（已在 .gitignore 中）
2. **临时文件会丢失**：Railway 重启后 `results/` 目录会清空
3. **首次访问可能较慢**：冷启动需要 10-20 秒

## 🎯 给客户试用的建议

1. **准备演示数据**：提前上传一些产品图片
2. **设置使用说明**：在首页添加简单的使用指引
3. **监控使用情况**：定期查看 Railway 的 Metrics
4. **收集反馈**：在界面添加反馈入口

## 🆘 常见问题

### Q: 部署失败怎么办？
A: 查看 Railway 的 Logs 标签，通常是依赖安装失败或环境变量未配置。

### Q: 图片无法显示？
A: 检查后端的静态文件路径配置，确保 `/results` 路径可访问。

### Q: API 调用超时？
A: Railway 免费版有 CPU 限制，生成时间可能较长，已设置 15 分钟超时。

### Q: 如何绑定自定义域名？
A: 在 Railway 项目设置中的 "Settings" → "Domains" 添加。

## 📞 需要帮助？

详细文档：[DEPLOYMENT.md](./DEPLOYMENT.md)

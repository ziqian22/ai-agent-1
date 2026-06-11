# Cloudflare Pages 部署指南

## 前端部署到 Cloudflare Pages

### 配置信息：

- **Root directory**: `易拉宝员工/frontend`
- **Build command**: `npm run build`
- **Build output directory**: `dist`
- **Deploy command**: 留空

### 环境变量：

在 Cloudflare Pages 项目设置中添加：

```
VITE_API_URL=https://ai-agent-1-production-4014.up.railway.app
```

### 部署步骤：

1. 访问 https://dash.cloudflare.com/
2. Workers & Pages → Create application → Pages → Connect to Git
3. 选择仓库：`ziqian22/ai-agent-1`
4. 配置构建设置（见上方）
5. 添加环境变量
6. Save and Deploy

部署完成后，会得到域名：`https://你的项目名.pages.dev`

## 后端继续使用 Railway

后端地址：https://ai-agent-1-production-4014.up.railway.app

无需修改后端代码，保持现状即可。

## 架构说明

```
用户
  ↓
Cloudflare Pages（前端，国内可访问）
  ↓
Railway（后端 API，国内可访问）
  ↓
Supabase（数据库）
```

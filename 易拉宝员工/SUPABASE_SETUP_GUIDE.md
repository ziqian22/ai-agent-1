# 🚀 Supabase Storage 配置指南

## 📋 快速开始（20分钟）

Supabase 是完全免费的对象存储服务，无需绑定信用卡。

---

## ✨ 为什么选择 Supabase？

- ✅ **完全免费** - 1GB 存储永久免费
- ✅ **无需绑卡** - 直接注册就能用
- ✅ **有管理界面** - 可以看到上传的图片
- ✅ **稳定可靠** - 专业的对象存储服务
- ✅ **简单易用** - API 简单，集成快速

---

## 🚀 配置步骤

### 第 1 步：注册 Supabase（3分钟）

1. 访问：https://supabase.com
2. 点击 **Start your project**
3. 用 **GitHub 账号**登录（最快）
4. 完成注册

### 第 2 步：创建项目（2分钟）

1. 点击 **New Project**
2. 填写：
   - **Name**: `banner-ai-designer`
   - **Database Password**: 保持自动生成的（或自己设置）
   - **Region**: 选择 **Northeast Asia (Tokyo)** 或 **Southeast Asia (Singapore)**
3. 点击 **Create new project**
4. 等待 1-2 分钟初始化

### 第 3 步：创建 Storage Bucket（1分钟）

1. 左侧菜单点击 **Storage**
2. 点击 **Create a new bucket**
3. 填写：
   - **Name**: `banner-images`
   - **Public bucket**: ✅ **必须勾选**（重要！）
4. 点击 **Create bucket**

### 第 4 步：获取 API 密钥（1分钟）

1. 左侧菜单点击 **Settings** → **API**
2. 复制以下两个值：
   - ✅ **Project URL**: `https://xxx.supabase.co`
   - ✅ **anon public** key: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

---

## 🔧 本地配置

### 编辑 `.env` 文件

添加以下配置：

```env
# Supabase Storage 配置（图片持久化）
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=你的anon_public_key
SUPABASE_BUCKET=banner-images
```

### 测试配置

```bash
# 运行测试脚本
python test_r2.py
```

如果看到 `✅ Supabase Storage 配置测试完成！`，说明配置成功。

---

## ☁️ Railway 部署配置

### 添加环境变量

1. 登录 Railway：https://railway.app
2. 进入你的项目
3. 点击你的服务
4. 切换到 **Variables** 标签
5. 点击 **New Variable**，逐个添加：
   - `SUPABASE_URL` = `https://your-project.supabase.co`
   - `SUPABASE_KEY` = `你的anon_public_key`
   - `SUPABASE_BUCKET` = `banner-images`
6. 点击 **Deploy**

### 推送代码

```bash
# 提交代码
git add .
git commit -m "集成 Supabase Storage 实现图片持久化"
git push

# Railway 会自动重新部署
```

---

## 🧪 验证

### 本地测试

1. 启动应用：`start.bat`
2. 访问：http://localhost:3000
3. 上传图片并生成易拉宝
4. 查看控制台，应该看到：
   ```
   ✅ 上传成功: results/banner_xxx.png -> https://xxx.supabase.co/storage/v1/object/public/banner-images/results/banner_xxx.png
   ```

### Railway 测试

1. 访问你的 Railway 域名
2. 生成一张易拉宝
3. 复制图片 URL
4. 在 Supabase Dashboard 中查看：
   - **Storage** → **banner-images** → **results/**
   - 应该能看到上传的图片

---

## 📊 工作原理

```
用户上传产品图片
    ↓
AI 生成易拉宝
    ↓
保存到本地 results/ 目录
    ↓
自动上传到 Supabase Storage
    ↓
返回 Supabase 的公开 URL（永久有效）
    ↓
✅ Railway 重启后依然可访问
```

---

## 🔍 故障排查

### 问题 1：上传失败

**错误提示**：
```
❌ 上传失败: 403 Forbidden
```

**解决方案**：
1. 检查 Storage Bucket 是否设置为 **Public**
2. 在 Supabase Dashboard 中：
   - **Storage** → **banner-images** → **Settings**
   - 确认 **Public bucket** 已启用

### 问题 2：无法访问图片

**错误提示**：
```
Access Denied
```

**解决方案**：
1. 检查图片 URL 格式是否正确：
   ```
   https://xxx.supabase.co/storage/v1/object/public/banner-images/results/banner_xxx.png
   ```
2. 确认 Bucket 设置为 Public

### 问题 3：配置了但仍使用本地 URL

**原因**：环境变量未生效

**解决方案**：
1. 检查 `.env` 文件是否正确
2. 重启应用
3. 查看控制台输出：
   ```
   ⚠️ Supabase 未配置，跳过上传
   ```
   说明环境变量未加载

---

## 💰 成本说明

### 免费额度（永久免费）

| 项目 | 免费额度 | 预估使用 | 是否超出 |
|------|----------|----------|----------|
| 存储空间 | 1 GB | ~500 MB | ❌ 不会 |
| 带宽 | 2 GB/月 | ~500 MB/月 | ❌ 不会 |
| API 请求 | 无限 | 任意 | ✅ 完全免费 |

**结论**：对于易拉宝设计助手的使用量，**完全在免费额度内**。

---

## 📞 需要帮助？

- **Supabase 文档**：https://supabase.com/docs/guides/storage
- **Storage API 参考**：https://supabase.com/docs/reference/javascript/storage

---

## ✅ 完成清单

- [ ] 注册 Supabase 账号
- [ ] 创建项目
- [ ] 创建 Storage Bucket（设置为 Public）
- [ ] 获取 API URL 和 Key
- [ ] 配置本地 `.env` 文件
- [ ] 运行测试脚本
- [ ] 配置 Railway 环境变量
- [ ] 推送代码并部署
- [ ] 测试图片上传和访问

---

**祝配置顺利！** 🎉

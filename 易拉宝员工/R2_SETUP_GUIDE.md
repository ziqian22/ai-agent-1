# 🗂️ Cloudflare R2 图片持久化存储配置指南

## 📋 问题说明

Railway 等云平台重启后，临时文件会丢失，导致生成的易拉宝图片无法访问。

**解决方案**：使用 Cloudflare R2 对象存储，永久保存生成的图片。

---

## ✨ 为什么选择 Cloudflare R2？

| 优势 | 说明 |
|------|------|
| 💰 **免费额度大** | 10GB 存储 + 每月 100 万次读取 |
| 🚀 **无流量费用** | 不像 AWS S3 按流量收费 |
| 🔌 **兼容 S3 API** | 代码改动小，易于集成 |
| 🌍 **全球 CDN** | 访问速度快 |

---

## 🚀 配置步骤

### 第 1 步：注册 Cloudflare 账号

1. 访问 https://dash.cloudflare.com/sign-up
2. 填写邮箱、密码，完成注册
3. 验证邮箱

### 第 2 步：创建 R2 存储桶

1. 登录 Cloudflare Dashboard
2. 左侧菜单选择 **R2**
3. 点击 **Create bucket**
4. 输入存储桶名称：`banner-images`
5. 选择区域：**自动（推荐）**
6. 点击 **Create bucket**

### 第 3 步：生成 API Token

1. 在 R2 页面，点击 **Manage R2 API Tokens**
2. 点击 **Create API Token**
3. 配置权限：
   - **Token name**: `banner-api-token`
   - **Permissions**: 选择 **Edit（读写权限）**
   - **TTL**: `Forever（永久有效）`
4. 点击 **Create API Token**
5. **重要**：复制以下三个值（只显示一次）：
   - ✅ **Access Key ID**
   - ✅ **Secret Access Key**
   - ✅ **Endpoint URL**（形如 `https://xxx.r2.cloudflarestorage.com`）

### 第 4 步：配置环境变量

#### 本地开发

编辑 `.env` 文件，添加以下配置：

```env
# Cloudflare R2 对象存储配置（图片持久化）
R2_ENDPOINT=https://your-account-id.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=你的Access_Key_ID
R2_SECRET_ACCESS_KEY=你的Secret_Access_Key
R2_BUCKET_NAME=banner-images
R2_PUBLIC_URL=  # 可选：自定义域名
```

#### Railway 部署

1. 登录 Railway 项目
2. 点击你的服务
3. 切换到 **Variables** 标签
4. 点击 **New Variable**，逐个添加：
   - `R2_ENDPOINT` = `https://your-account-id.r2.cloudflarestorage.com`
   - `R2_ACCESS_KEY_ID` = `你的Access_Key_ID`
   - `R2_SECRET_ACCESS_KEY` = `你的Secret_Access_Key`
   - `R2_BUCKET_NAME` = `banner-images`
5. 点击 **Save**
6. Railway 会自动重新部署

---

## 🧪 测试验证

### 方法 1：本地测试

```bash
# 安装依赖
pip install boto3

# 启动应用
start.bat

# 访问前端
http://localhost:3000

# 上传图片并生成易拉宝
# 查看控制台输出，应该看到：
# [INFO] ✅ 图片已上传到 R2: https://xxx.r2.cloudflarestorage.com/...
```

### 方法 2：检查 R2 存储桶

1. 登录 Cloudflare Dashboard
2. 进入 **R2** → **banner-images**
3. 查看 **Objects** 标签
4. 应该看到 `results/banner_xxx.png` 文件

---

## 📊 工作原理

```
用户上传产品图片
    ↓
AI 生成易拉宝
    ↓
保存到本地 results/ 目录
    ↓
自动上传到 R2 存储（如果已配置）
    ↓
返回 R2 的公开 URL（永久有效）
    ↓
用户可以随时访问
```

**关键点**：
- ✅ R2 配置正确 → 使用 R2 URL（永久有效）
- ⚠️ R2 未配置 → 使用本地 URL（重启后失效）

---

## 🔍 故障排查

### 问题 1：图片上传失败

**错误提示**：
```
❌ 上传失败: botocore.exceptions.NoCredentialsError
```

**解决方案**：
1. 检查 `.env` 文件中的 R2 配置是否正确
2. 确认 API Token 是否有 **Edit** 权限
3. 重启应用

### 问题 2：图片无法访问

**错误提示**：
```
Access Denied
```

**解决方案**：
1. 检查存储桶权限设置
2. 在 Cloudflare R2 中，进入 `banner-images` 存储桶
3. 点击 **Settings** → **Public Access**
4. 启用 **Allow public access**（可选，推荐）

### 问题 3：R2 配置了但仍使用本地 URL

**原因**：配置不完整

**解决方案**：
1. 检查控制台输出：
   ```
   ⚠️ R2 未配置，跳过上传
   ```
2. 确认以下三个环境变量都已设置：
   - `R2_ENDPOINT`
   - `R2_ACCESS_KEY_ID`
   - `R2_SECRET_ACCESS_KEY`

---

## 💰 成本估算

### 免费额度（完全够用）

| 项目 | 免费额度 | 预估使用 | 是否超出 |
|------|----------|----------|----------|
| 存储空间 | 10 GB | ~1-2 GB | ❌ 不会 |
| 读取请求 | 100 万次/月 | ~1-5 万次/月 | ❌ 不会 |
| 写入请求 | 100 万次/月 | ~100-500 次/月 | ❌ 不会 |
| 流量 | **免费无限** | 任意 | ✅ 完全免费 |

**结论**：对于易拉宝设计助手的使用量，**完全在免费额度内**。

### 超出后付费（极少发生）

- 存储：$0.015/GB/月
- 写入：$4.50/百万次
- 读取：$0.36/百万次

---

## 🎯 自定义域名（可选）

如果你想使用自己的域名访问图片（如 `https://cdn.pudow.com/results/banner.png`）：

### 配置步骤

1. 在 Cloudflare 添加域名
2. 创建 CNAME 记录指向 R2 存储桶
3. 在 `.env` 中设置：
   ```env
   R2_PUBLIC_URL=https://cdn.pudow.com
   ```

---

## 📞 需要帮助？

- **Cloudflare R2 文档**：https://developers.cloudflare.com/r2/
- **boto3 文档**：https://boto3.amazonaws.com/v1/documentation/api/latest/index.html

---

## ✅ 完成清单

- [ ] 注册 Cloudflare 账号
- [ ] 创建 R2 存储桶 `banner-images`
- [ ] 生成 API Token（记录 3 个值）
- [ ] 配置本地 `.env` 文件
- [ ] 配置 Railway 环境变量
- [ ] 本地测试上传功能
- [ ] Railway 部署并测试

---

**祝配置顺利！** 🎉

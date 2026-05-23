# 🔧 GitHub 文件更新指南

## 问题确认

Railway 日志显示它还在读取：
```
streamlit==1.31.0 (line 1)
pillow==10.3.0 (line 4)
```

这说明 GitHub 上的 `requirements.txt` **没有更新成功**。

---

## ✅ 立即操作：在 GitHub 网页更新文件

### 步骤 1：更新根目录 requirements.txt

1. 访问：https://github.com/ziqian22/ai-agent-1/blob/main/易拉宝员工/requirements.txt

2. 点击右上角 **铅笔图标**（Edit this file）

3. **删除所有内容**，粘贴以下内容（不要有任何修改）：

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
httpx==0.26.0
python-dotenv==1.0.0
pillow>=10.3.0
anthropic>=0.18.0
PyPDF2>=3.0.0
python-docx>=1.1.0
python-pptx>=0.6.23
python-multipart==0.0.6
aiofiles==23.2.1
```

4. 点击 **Commit changes**

5. 提交信息填写：`Fix: 移除 streamlit，更新 pillow 版本`

6. **确保选择 "Commit directly to the main branch"**

7. 点击 **Commit changes** 确认

---

### 步骤 2：更新 backend/requirements.txt

1. 访问：https://github.com/ziqian22/ai-agent-1/blob/main/易拉宝员工/backend/requirements.txt

2. 点击右上角 **铅笔图标**

3. 找到第 5 行 `pillow==10.2.0`，改为 `pillow>=10.3.0`

4. 点击 **Commit changes**

5. 提交信息：`Fix: 更新 pillow 版本`

6. 点击 **Commit changes** 确认

---

### 步骤 3：确保 runtime.txt 存在

1. 访问：https://github.com/ziqian22/ai-agent-1/blob/main/易拉宝员工/runtime.txt

2. 如果文件不存在，点击 **Add file** → **Create new file**

3. 文件名：`runtime.txt`

4. 内容：
```
python-3.11.9
```

5. 提交

---

### 步骤 4：在 Railway 强制重新部署

1. 进入 Railway 项目

2. 点击 **Settings** 标签

3. 找到 **Environment Variables**，添加：
   ```
   NIXPACKS_PYTHON_VERSION=3.11
   ```

4. 点击右上角的 **三个点** → **Redeploy**

5. 选择 **"Clear build cache and redeploy"**

---

## 🎯 验证步骤

更新后，在 GitHub 上刷新页面，确认：

✅ `requirements.txt` 第 1 行是 `fastapi==0.109.0`（不是 streamlit）
✅ `requirements.txt` 包含 `pillow>=10.3.0`
✅ `runtime.txt` 内容是 `python-3.11.9`

然后等待 Railway 重新部署（约 2-3 分钟）。

---

## 📸 如果还是不行

请截图给我：
1. GitHub 上 requirements.txt 的内容（前 10 行）
2. Railway 的 Settings → General 页面（显示连接的仓库和分支）
3. Railway 的最新构建日志

---

**现在立即去 GitHub 更新这两个文件！记得要点击 "Commit changes" 确认提交。**

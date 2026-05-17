# 知识库添加和编辑功能说明

## ✅ 功能已完成

### 1. 添加产品功能 ✅

**入口**: 知识库管理页面 → 点击"添加产品"按钮

**功能**:
- ✅ 手动填写产品信息
- ✅ 上传产品图片
- ✅ 上传 Logo 图片(可选)
- ✅ 自动保存到知识库

**表单字段**:
- **产品名称** (必填) - 如: 勇士K6直饮机
- **品牌** (必填) - 如: 朴道健康水专家
- **产品类型** (可选) - 如: 饮水机
- **产品特点** (可选) - 多个特点用逗号分隔
  - 示例: `高效节能, 智能控制, 静音运行`
- **适用场景** (可选) - 多个场景用逗号分隔
  - 示例: `办公室, 家庭, 学校`
- **产品图片** (必填) - 支持 PNG/JPG
- **Logo图片** (可选) - 支持 PNG/JPG

### 2. 编辑产品功能 ✅

**入口**: 知识库管理页面 → 产品卡片右上角菜单 → 点击"编辑"

**功能**:
- ✅ 修改产品名称
- ✅ 修改品牌
- ✅ 修改产品类型
- ✅ 修改产品特点
- ✅ 修改适用场景
- ⚠️ 暂不支持修改图片(需要重新添加)

### 3. 其他功能 ✅

**使用产品**:
- 点击产品卡片右上角菜单 → "使用"
- 自动加载产品信息到对话页面
- 可以直接开始生成易拉宝

**删除产品**:
- 点击产品卡片右上角菜单 → "删除"
- 确认后删除产品及其文件

**搜索产品**:
- 在搜索框输入关键词
- 支持搜索产品名称、品牌、产品类型

---

## 使用流程

### 添加产品流程

1. **打开添加对话框**
   - 点击"知识库管理"菜单
   - 点击"添加产品"按钮

2. **填写产品信息**
   ```
   产品名称: 勇士K6直饮机
   品牌: 朴道健康水专家
   产品类型: 饮水机
   产品特点: 高效节能, 智能控制, 静音运行, 4重净化
   适用场景: 办公室, 家庭, 学校, 医院
   ```

3. **上传图片**
   - 点击"选择图片"按钮
   - 选择产品图片
   - (可选) 点击"选择Logo"上传品牌Logo

4. **提交**
   - 点击"添加"按钮
   - 等待上传完成
   - 看到"产品添加成功"提示

5. **验证**
   - 在产品列表中看到新添加的产品
   - 产品卡片显示产品图片和信息

### 编辑产品流程

1. **打开编辑对话框**
   - 找到要编辑的产品
   - 点击产品卡片右上角的"⋮"图标
   - 选择"编辑"

2. **修改信息**
   - 表单会自动填充当前产品信息
   - 修改需要更改的字段
   - 注意: 图片暂时不能修改

3. **保存**
   - 点击"保存"按钮
   - 看到"产品更新成功"提示

4. **验证**
   - 产品卡片显示更新后的信息

---

## 技术实现

### 前端实现

**文件**: `frontend/src/views/KnowledgeBase.vue`

**关键功能**:

1. **表单管理**
```javascript
const productForm = ref({
  product_name: '',
  brand: '',
  product_type: '',
  features: '',
  scenes: '',
  imageFile: null,
  logoFile: null
})
```

2. **添加产品**
```javascript
const addProduct = async () => {
  const formData = new FormData()
  formData.append('product_name', productForm.value.product_name)
  formData.append('brand', productForm.value.brand)
  formData.append('product_type', productForm.value.product_type || '')
  formData.append('features', productForm.value.features || '')
  formData.append('scenes', productForm.value.scenes || '')
  formData.append('image', productForm.value.imageFile.raw)
  
  if (productForm.value.logoFile) {
    formData.append('logo', productForm.value.logoFile.raw)
  }

  await axios.post('/api/knowledge-base/products', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}
```

3. **编辑产品**
```javascript
const updateProduct = async () => {
  const product_info = {
    product_name: productForm.value.product_name,
    brand: productForm.value.brand,
    product_type: productForm.value.product_type || '',
    features: productForm.value.features.split(',').map(f => f.trim()).filter(f => f),
    scenes: productForm.value.scenes.split(',').map(s => s.trim()).filter(s => s)
  }

  await axios.put(
    `/api/knowledge-base/products/${currentProduct.value.id}`,
    { product_info }
  )
}
```

### 后端实现

**文件**: `backend/main.py`

**关键接口**:

1. **添加产品 API**
```python
@app.post("/api/knowledge-base/products")
async def add_product(
    product_name: str = Form(...),
    brand: str = Form(...),
    product_type: str = Form(""),
    features: str = Form(""),
    scenes: str = Form(""),
    image: UploadFile = File(...),
    logo: UploadFile = File(None)
):
    # 保存图片
    image_path = upload_dir / f"{uuid.uuid4()}_{image.filename}"
    with open(image_path, "wb") as f:
        f.write(await image.read())
    
    # 构建产品信息
    product_info = {
        "product_name": product_name,
        "brand": brand,
        "product_type": product_type,
        "features": [f.strip() for f in features.split(',') if f.strip()],
        "scenes": [s.strip() for s in scenes.split(',') if s.strip()]
    }
    
    # 添加到知识库
    product_id = knowledge_base.add_product(
        product_info=product_info,
        image_path=str(image_path),
        logo_path=str(logo_path) if logo_path else None
    )
    
    return {"product_id": product_id}
```

2. **更新产品 API**
```python
@app.put("/api/knowledge-base/products/{product_id}")
async def update_product(product_id: str, product_info: Dict[str, Any]):
    success = knowledge_base.update_product(product_id, product_info)
    if not success:
        raise HTTPException(status_code=404, detail="产品不存在")
    return {"success": True}
```

---

## 注意事项

### 1. 图片格式
- 支持: PNG, JPG, JPEG
- 建议大小: < 10MB
- 建议尺寸: 800x800 或更大

### 2. 特点和场景格式
- 使用**中文逗号**或**英文逗号**分隔
- 自动去除首尾空格
- 空值会被过滤

**示例**:
```
正确: 高效节能, 智能控制, 静音运行
正确: 高效节能，智能控制，静音运行
错误: 高效节能;智能控制;静音运行 (不支持分号)
```

### 3. 编辑限制
- 当前版本不支持修改产品图片和Logo
- 如需更换图片,请删除后重新添加
- 或者在下个版本中实现图片更新功能

### 4. 数据持久化
- 产品数据保存在 `knowledge_base/products.json`
- 产品图片保存在 `knowledge_base/files/{product_id}/`
- 重启后端服务后数据不会丢失

---

## 常见问题

### Q1: 添加产品时提示"添加失败"?
**A**: 检查以下几点:
1. 产品名称和品牌是否填写
2. 是否选择了产品图片
3. 图片格式是否正确 (PNG/JPG)
4. 后端服务是否正常运行

### Q2: 编辑产品后看不到更新?
**A**: 
1. 刷新页面 (F5)
2. 检查后端日志是否有错误
3. 确认修改的字段是否正确保存

### Q3: 如何修改产品图片?
**A**: 
- 当前版本不支持直接修改图片
- 临时方案: 删除产品后重新添加
- 或等待下个版本的图片更新功能

### Q4: 特点和场景没有正确分隔?
**A**: 
- 确保使用逗号分隔 (中文或英文逗号都可以)
- 不要使用分号、空格或其他符号
- 示例: `特点1, 特点2, 特点3`

---

## 下一步优化

### 优先级: 高
1. **支持编辑时修改图片**
   - 添加图片上传字段
   - 保留原图片作为预览
   - 上传新图片后替换

2. **批量导入产品**
   - 支持 Excel/CSV 导入
   - 批量上传图片
   - 自动匹配产品和图片

### 优先级: 中
3. **产品分类管理**
   - 添加产品分类
   - 按分类筛选
   - 分类统计

4. **产品标签系统**
   - 添加自定义标签
   - 按标签筛选
   - 标签云展示

---

## 测试验证

### 测试步骤

1. **测试添加功能**
   ```
   1. 点击"添加产品"
   2. 填写所有字段
   3. 上传图片
   4. 点击"添加"
   5. 验证: 产品列表中出现新产品
   ```

2. **测试编辑功能**
   ```
   1. 点击产品菜单 → "编辑"
   2. 修改产品名称
   3. 点击"保存"
   4. 验证: 产品名称已更新
   ```

3. **测试删除功能**
   ```
   1. 点击产品菜单 → "删除"
   2. 确认删除
   3. 验证: 产品从列表中消失
   ```

4. **测试搜索功能**
   ```
   1. 在搜索框输入产品名称
   2. 验证: 只显示匹配的产品
   3. 清空搜索框
   4. 验证: 显示所有产品
   ```

---

**更新时间**: 2026-05-17
**状态**: ✅ 功能已完成并可用

<template>
  <div class="knowledge-base">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>知识库管理</span>
          <el-button type="primary" :icon="Plus" @click="openAddDialog">
            添加产品
          </el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <el-input
        v-model="searchKeyword"
        placeholder="搜索产品名称、品牌或类型..."
        :prefix-icon="Search"
        clearable
        style="margin-bottom: 20px"
      />

      <!-- 产品列表 -->
      <div v-if="loading" class="loading-container">
        <el-icon class="is-loading" :size="40"><Loading /></el-icon>
        <p>加载中...</p>
      </div>

      <el-empty v-else-if="filteredProducts.length === 0" description="暂无产品">
        <el-button type="primary" @click="openAddDialog">添加第一个产品</el-button>
      </el-empty>

      <div v-else class="products-grid">
        <el-card
          v-for="product in filteredProducts"
          :key="product.id"
          class="product-card"
          shadow="hover"
        >
          <template #header>
            <div class="product-header">
              <span class="product-name">{{ product.product_info.product_name }}</span>
              <el-dropdown @command="handleCommand($event, product)">
                <el-icon><MoreFilled /></el-icon>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="use">使用</el-dropdown-item>
                    <el-dropdown-item command="edit">编辑</el-dropdown-item>
                    <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>

          <div class="product-content">
            <el-image
              :src="product.image_url || product.image_path"
              fit="cover"
              class="product-image"
            >
              <template #error>
                <div class="image-error">图片加载失败</div>
              </template>
            </el-image>
            <div class="product-info">
              <p><strong>品牌:</strong> {{ product.product_info.brand }}</p>
              <p><strong>类型:</strong> {{ product.product_info.product_type || '未分类' }}</p>
              <p><strong>创建时间:</strong> {{ formatDate(product.created_at) }}</p>
            </div>
          </div>
        </el-card>
      </div>
    </el-card>

    <!-- 添加/编辑产品对话框 -->
    <el-dialog
      v-model="showFormDialog"
      :title="isEditing ? '编辑产品' : '添加产品'"
      width="600px"
      @close="resetForm"
    >
      <el-form :model="productForm" label-width="100px" ref="formRef">
        <el-form-item label="产品名称" required>
          <el-input v-model="productForm.product_name" placeholder="请输入产品名称" />
        </el-form-item>

        <el-form-item label="品牌" required>
          <el-input v-model="productForm.brand" placeholder="请输入品牌名称" />
        </el-form-item>

        <el-form-item label="产品类型">
          <el-input v-model="productForm.product_type" placeholder="如: 饮水机、空调等" />
        </el-form-item>

        <el-form-item label="产品特点">
          <el-input
            v-model="productForm.features"
            type="textarea"
            :rows="3"
            placeholder="多个特点用逗号分隔,如: 高效节能,智能控制,静音运行"
          />
        </el-form-item>

        <el-form-item label="适用场景">
          <el-input
            v-model="productForm.scenes"
            type="textarea"
            :rows="2"
            placeholder="多个场景用逗号分隔,如: 办公室,家庭,学校"
          />
        </el-form-item>

        <el-form-item label="产品图片" required v-if="!isEditing">
          <el-upload
            ref="imageUploadRef"
            :auto-upload="false"
            :on-change="handleImageChange"
            :show-file-list="false"
            accept=".png,.jpg,.jpeg"
          >
            <el-button :icon="Picture">选择图片</el-button>
          </el-upload>
          <div v-if="productForm.imageFile" style="margin-top: 10px">
            <el-tag closable @close="productForm.imageFile = null">
              {{ productForm.imageFile.name }}
            </el-tag>
          </div>
        </el-form-item>

        <el-form-item label="Logo图片" v-if="!isEditing">
          <el-upload
            ref="logoUploadRef"
            :auto-upload="false"
            :on-change="handleLogoChange"
            :show-file-list="false"
            accept=".png,.jpg,.jpeg"
          >
            <el-button :icon="Picture">选择Logo</el-button>
          </el-upload>
          <div v-if="productForm.logoFile" style="margin-top: 10px">
            <el-tag closable @close="productForm.logoFile = null">
              {{ productForm.logoFile.name }}
            </el-tag>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showFormDialog = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          {{ isEditing ? '保存' : '添加' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Plus, Search, Loading, MoreFilled, Picture } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

// 添加 emit 用于通知父组件切换页面
const emit = defineEmits(['switch-to-chat'])

const searchKeyword = ref('')
const loading = ref(false)
const products = ref([])
const showFormDialog = ref(false)
const isEditing = ref(false)
const submitting = ref(false)
const currentProduct = ref(null)

// 表单数据
const productForm = ref({
  product_name: '',
  brand: '',
  product_type: '',
  features: '',
  scenes: '',
  imageFile: null,
  logoFile: null
})

// 过滤产品
const filteredProducts = computed(() => {
  if (!searchKeyword.value) return products.value

  const keyword = searchKeyword.value.toLowerCase()
  return products.value.filter(p => {
    const info = p.product_info
    return (
      info.product_name?.toLowerCase().includes(keyword) ||
      info.brand?.toLowerCase().includes(keyword) ||
      info.product_type?.toLowerCase().includes(keyword)
    )
  })
})

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

// 打开添加对话框
const openAddDialog = () => {
  isEditing.value = false
  resetForm()
  showFormDialog.value = true
}

// 打开编辑对话框
const openEditDialog = (product) => {
  isEditing.value = true
  currentProduct.value = product

  // 填充表单数据
  const info = product.product_info
  productForm.value = {
    product_name: info.product_name || '',
    brand: info.brand || '',
    product_type: info.product_type || '',
    features: info.features?.join(', ') || '',
    scenes: info.scenes?.join(', ') || '',
    imageFile: null,
    logoFile: null
  }

  showFormDialog.value = true
}

// 重置表单
const resetForm = () => {
  productForm.value = {
    product_name: '',
    brand: '',
    product_type: '',
    features: '',
    scenes: '',
    imageFile: null,
    logoFile: null
  }
  currentProduct.value = null
}

// 处理图片选择
const handleImageChange = (file) => {
  productForm.value.imageFile = file
}

// 处理Logo选择
const handleLogoChange = (file) => {
  productForm.value.logoFile = file
}

// 提交表单
const submitForm = async () => {
  // 验证必填项
  if (!productForm.value.product_name) {
    ElMessage.error('请输入产品名称')
    return
  }
  if (!productForm.value.brand) {
    ElMessage.error('请输入品牌名称')
    return
  }
  if (!isEditing.value && !productForm.value.imageFile) {
    ElMessage.error('请选择产品图片')
    return
  }

  submitting.value = true

  try {
    if (isEditing.value) {
      // 编辑产品
      await updateProduct()
    } else {
      // 添加产品
      await addProduct()
    }
  } catch (error) {
    console.error(error)
  } finally {
    submitting.value = false
  }
}

// 添加产品
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

  try {
    await axios.post('/api/knowledge-base/products', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    ElMessage.success('产品添加成功')
    showFormDialog.value = false
    loadProducts()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '添加失败')
  }
}

// 更新产品
const updateProduct = async () => {
  const product_info = {
    product_name: productForm.value.product_name,
    brand: productForm.value.brand,
    product_type: productForm.value.product_type || '',
    features: productForm.value.features.split(',').map(f => f.trim()).filter(f => f),
    scenes: productForm.value.scenes.split(',').map(s => s.trim()).filter(s => s)
  }

  try {
    await axios.put(
      `/api/knowledge-base/products/${currentProduct.value.id}`,
      { product_info }
    )

    ElMessage.success('产品更新成功')
    showFormDialog.value = false
    loadProducts()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '更新失败')
  }
}

// 处理操作命令
const handleCommand = async (command, product) => {
  switch (command) {
    case 'use':
      try {
        ElMessage.info('正在加载产品信息...')

        const response = await axios.post(`/api/knowledge-base/products/${product.id}/use`)
        const sessionId = response.data.session_id

        // 保存 session_id 到 sessionStorage
        sessionStorage.setItem('chat_session_id', sessionId)

        // 使用后端返回的消息初始化对话历史
        const initialMessage = {
          role: 'assistant',
          content: response.data.message
        }
        sessionStorage.setItem('chat_messages', JSON.stringify([initialMessage]))

        ElMessage.success('已加载产品信息，正在跳转到对话页面...')

        // 通知父组件切换到对话页面
        emit('switch-to-chat', sessionId)
      } catch (error) {
        console.error('加载产品失败:', error)
        ElMessage.error(error.response?.data?.detail || '加载产品失败')
      }
      break
    case 'edit':
      openEditDialog(product)
      break
    case 'delete':
      ElMessageBox.confirm('确定要删除这个产品吗?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(async () => {
        try {
          await axios.delete(`/api/knowledge-base/products/${product.id}`)
          ElMessage.success('删除成功')
          loadProducts()
        } catch (error) {
          ElMessage.error('删除失败')
        }
      }).catch(() => {})
      break
  }
}

// 加载产品列表
const loadProducts = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/knowledge-base/products')
    products.value = response.data.products || []
    console.log('[DEBUG] 加载知识库产品:', products.value.length, '个')
  } catch (error) {
    ElMessage.error('加载产品列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadProducts()
})
</script>

<style scoped>
.knowledge-base {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  color: #909399;
}

.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.product-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.product-card:hover {
  transform: translateY(-4px);
}

.product-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.product-name {
  font-weight: 600;
  font-size: 16px;
}

.product-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.product-image {
  width: 100%;
  height: 200px;
  border-radius: 4px;
}

.product-info p {
  margin: 4px 0;
  font-size: 14px;
  color: #606266;
}
</style>

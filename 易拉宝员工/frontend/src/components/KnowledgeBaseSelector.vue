<template>
  <el-dialog
    v-model="visible"
    title="从知识库选择产品"
    width="800px"
    :close-on-click-modal="false"
  >
    <!-- 搜索框 -->
    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索产品名称、品牌..."
        :prefix-icon="Search"
        clearable
        @input="handleSearch"
      />
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading" :size="40"><Loading /></el-icon>
      <p>加载中...</p>
    </div>

    <!-- 空状态 -->
    <el-empty v-else-if="filteredProducts.length === 0" description="暂无产品">
      <p style="color: #909399">请先在知识库中添加产品</p>
    </el-empty>

    <!-- 产品列表 -->
    <div v-else class="products-grid">
      <div
        v-for="product in filteredProducts"
        :key="product.id"
        :class="['product-card', { selected: selectedProduct?.id === product.id }]"
        @click="selectProduct(product)"
      >
        <!-- 产品图片 -->
        <div class="product-image">
          <el-image
            v-if="product.image_path"
            :src="getImageUrl(product.image_path)"
            fit="cover"
          >
            <template #error>
              <div class="image-error">
                <el-icon><Picture /></el-icon>
              </div>
            </template>
          </el-image>
          <div v-else class="image-placeholder">
            <el-icon :size="40"><Picture /></el-icon>
          </div>
        </div>

        <!-- 产品信息 -->
        <div class="product-info">
          <h4>{{ product.product_info.product_name }}</h4>
          <p class="brand">{{ product.product_info.brand }}</p>
          <el-tag size="small" type="info">{{ product.product_info.product_type }}</el-tag>
        </div>

        <!-- 选中标记 -->
        <div v-if="selectedProduct?.id === product.id" class="selected-mark">
          <el-icon :size="24" color="#67c23a"><CircleCheck /></el-icon>
        </div>
      </div>
    </div>

    <!-- 底部按钮 -->
    <template #footer>
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="primary" :disabled="!selectedProduct" @click="handleConfirm">
        确定使用
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Search, Loading, Picture, CircleCheck } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const props = defineProps({
  modelValue: Boolean
})

const emit = defineEmits(['update:modelValue', 'product-selected'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const loading = ref(false)
const products = ref([])
const searchQuery = ref('')
const selectedProduct = ref(null)

// 过滤后的产品列表
const filteredProducts = computed(() => {
  if (!searchQuery.value) {
    return products.value
  }

  const query = searchQuery.value.toLowerCase()
  return products.value.filter(product => {
    const info = product.product_info
    return (
      info.product_name?.toLowerCase().includes(query) ||
      info.brand?.toLowerCase().includes(query) ||
      info.product_type?.toLowerCase().includes(query)
    )
  })
})

// 监听对话框打开，加载产品列表
watch(visible, (newVal) => {
  if (newVal) {
    loadProducts()
  } else {
    // 关闭时重置
    selectedProduct.value = null
    searchQuery.value = ''
  }
})

// 加载产品列表
const loadProducts = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/knowledge-base/products')
    products.value = response.data.products || []
  } catch (error) {
    console.error('加载产品列表失败:', error)
    ElMessage.error('加载产品列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索处理
const handleSearch = () => {
  // 搜索逻辑已在 computed 中处理
}

// 选择产品
const selectProduct = (product) => {
  selectedProduct.value = product
}

// 获取图片URL
const getImageUrl = (imagePath) => {
  // 如果是完整URL，直接返回
  if (imagePath.startsWith('http')) {
    return imagePath
  }
  // 否则构建本地路径
  return `/api/files/${encodeURIComponent(imagePath)}`
}

// 取消
const handleCancel = () => {
  visible.value = false
}

// 确认选择
const handleConfirm = () => {
  if (!selectedProduct.value) {
    ElMessage.warning('请选择一个产品')
    return
  }

  emit('product-selected', selectedProduct.value)
  visible.value = false
}
</script>

<style scoped>
.search-bar {
  margin-bottom: 20px;
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
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  max-height: 500px;
  overflow-y: auto;
  padding: 4px;
}

.product-card {
  position: relative;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.3s;
  background: white;
}

.product-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.2);
  transform: translateY(-2px);
}

.product-card.selected {
  border-color: #67c23a;
  background: #f0f9ff;
}

.product-image {
  width: 100%;
  height: 150px;
  border-radius: 4px;
  overflow: hidden;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
}

.product-image .el-image {
  width: 100%;
  height: 100%;
}

.image-placeholder,
.image-error {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: #c0c4cc;
}

.product-info h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-info .brand {
  margin: 0 0 8px 0;
  font-size: 12px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selected-mark {
  position: absolute;
  top: 8px;
  right: 8px;
  background: white;
  border-radius: 50%;
  padding: 2px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}
</style>

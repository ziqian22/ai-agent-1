<template>
  <div class="generation-history">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>生成记录</span>
          <el-button :icon="Refresh" @click="loadHistory">刷新</el-button>
        </div>
      </template>

      <!-- 加载中 -->
      <div v-if="loading" class="loading-container">
        <el-icon class="is-loading" :size="40"><Loading /></el-icon>
        <p>加载中...</p>
      </div>

      <!-- 空状态 -->
      <el-empty v-else-if="historyList.length === 0" description="暂无生成记录">
        <p style="color: #909399">生成易拉宝后,记录会显示在这里</p>
      </el-empty>

      <!-- 记录列表 -->
      <div v-else class="history-grid">
        <el-card
          v-for="(item, index) in historyList"
          :key="index"
          class="history-card"
          shadow="hover"
        >
          <template #header>
            <div class="history-header">
              <span class="history-title">{{ item.product_name }}</span>
              <el-tag :type="getStyleType(item.style)">{{ item.style }}</el-tag>
            </div>
          </template>

          <div class="history-content">
            <!-- 显示所有生成的图片 -->
            <div class="images-grid">
              <div
                v-for="(imageUrl, imgIndex) in item.image_urls"
                :key="imgIndex"
                class="image-item"
              >
                <el-image
                  :src="imageUrl"
                  fit="cover"
                  class="history-image"
                  :preview-src-list="item.image_urls"
                  :initial-index="imgIndex"
                  :preview-teleported="true"
                  :hide-on-click-modal="true"
                />
                <div class="image-actions">
                  <el-tooltip content="下载图片" placement="top">
                    <el-button
                      type="success"
                      :icon="Download"
                      size="default"
                      circle
                      @click.stop="downloadSingleImage(imageUrl, item.product_name, imgIndex)"
                    />
                  </el-tooltip>
                </div>
                <div class="image-hint">
                  <el-icon><ZoomIn /></el-icon>
                  <span>点击查看大图</span>
                </div>
              </div>
            </div>

            <div class="history-info">
              <p><strong>品牌:</strong> {{ item.brand }}</p>
              <p><strong>风格:</strong> {{ item.style }}</p>
              <p><strong>生成数量:</strong> {{ item.image_urls?.length || 0 }} 张</p>
              <p><strong>生成时间:</strong> {{ formatDate(item.created_at) }}</p>
            </div>

            <div class="history-actions">
              <el-button type="primary" :icon="Download" @click="downloadAllImages(item)">
                下载全部
              </el-button>
              <el-button :icon="Delete" @click="deleteRecord(item)">
                删除
              </el-button>
            </div>
          </div>
        </el-card>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Refresh, Loading, Download, Delete, ZoomIn } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

const loading = ref(false)
const historyList = ref([])

// 获取风格类型
const getStyleType = (style) => {
  const typeMap = {
    '科技感': 'primary',
    '简约商务': '',
    '自然清新': 'success',
    '时尚活力': 'warning',
    '高端奢华': 'danger'
  }
  return typeMap[style] || ''
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 下载单张图片
const downloadSingleImage = async (imageUrl, productName, index) => {
  try {
    // 直接从图片 URL 下载
    const response = await axios.get(imageUrl, {
      responseType: 'blob'
    })

    // 创建下载链接
    const url = window.URL.createObjectURL(response.data)
    const link = document.createElement('a')
    link.href = url
    link.download = `${productName}_${index + 1}.png`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    // 释放 URL 对象
    setTimeout(() => {
      window.URL.revokeObjectURL(url)
    }, 100)

    ElMessage.success('下载成功')
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error(`下载失败: ${error.message}`)
  }
}

// 下载所有图片
const downloadAllImages = async (item) => {
  if (!item.image_urls || item.image_urls.length === 0) {
    ElMessage.error('没有可下载的图片')
    return
  }

  ElMessage.info(`开始下载 ${item.image_urls.length} 张图片...`)

  for (let i = 0; i < item.image_urls.length; i++) {
    try {
      await downloadSingleImage(item.image_urls[i], item.product_name, i)
      // 添加延迟,避免浏览器阻止多个下载
      if (i < item.image_urls.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 500))
      }
    } catch (error) {
      console.error(`下载第 ${i + 1} 张图片失败:`, error)
    }
  }

  ElMessage.success('全部下载完成')
}

// 删除记录
const deleteRecord = (item) => {
  ElMessageBox.confirm('确定要删除这条记录吗?', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await axios.delete(`/api/generation-history/${item.id}`)
      ElMessage.success('删除成功')
      loadHistory()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

// 加载历史记录
const loadHistory = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/generation-history')
    historyList.value = response.data.history || []
    console.log('[DEBUG] 加载生成记录:', historyList.value.length, '条')
  } catch (error) {
    ElMessage.error('加载历史记录失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.generation-history {
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

.history-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.history-card {
  transition: transform 0.2s;
}

.history-card:hover {
  transform: translateY(-4px);
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.history-title {
  font-weight: 600;
  font-size: 16px;
}

.history-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
}

.image-item {
  position: relative;
  aspect-ratio: 1 / 2;
  overflow: hidden;
  border-radius: 4px;
  cursor: pointer;
}

.image-item:hover .image-actions {
  opacity: 1;
}

.image-item:hover .image-hint {
  opacity: 1;
}

.history-image {
  width: 100%;
  height: 100%;
}

.image-actions {
  position: absolute;
  top: 8px;
  right: 8px;
  opacity: 0;
  transition: opacity 0.3s;
  z-index: 10;
}

.image-actions .el-button {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.image-actions .el-button:hover {
  transform: scale(1.15);
  transition: transform 0.2s;
}

.image-hint {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 14px;
  opacity: 0;
  transition: opacity 0.3s;
}

.image-hint .el-icon {
  font-size: 18px;
}

.history-info p {
  margin: 4px 0;
  font-size: 14px;
  color: #606266;
}

.history-actions {
  display: flex;
  gap: 8px;
}

.history-actions .el-button {
  flex: 1;
}
</style>

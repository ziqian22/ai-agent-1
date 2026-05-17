<template>
  <div class="banner-preview-container">
    <div class="preview-header">
      <h3>选择您喜欢的易拉宝</h3>
      <p class="hint">鼠标悬停可预览 Logo 效果，点击选择按钮确认</p>
    </div>

    <div class="banner-grid">
      <div
        v-for="(banner, index) in banners"
        :key="index"
        class="banner-item"
        @mouseenter="hoveredIndex = index"
        @mouseleave="hoveredIndex = null"
      >
        <!-- 易拉宝图片 -->
        <div class="banner-image-wrapper">
          <el-image
            :src="banner.url"
            fit="contain"
            class="banner-image"
            :preview-src-list="banners.map(b => b.url)"
            :initial-index="index"
          />

          <!-- Logo 预览层（悬停时显示） -->
          <div v-if="hoveredIndex === index && banner.recommendedLogo" class="logo-preview-layer">
            <!-- 推荐的 Logo（半透明叠加） -->
            <img
              :src="getLogoPreviewUrl(banner)"
              :style="getLogoStyle(banner)"
              class="logo-overlay"
              alt="Logo 预览"
            />
          </div>
        </div>

        <!-- Logo 信息卡片（悬停时显示） -->
        <transition name="fade">
          <div v-if="hoveredIndex === index && banner.recommendedLogo" class="logo-info-card">
            <div class="logo-header">
              <el-icon><Picture /></el-icon>
              <span class="logo-name">{{ banner.recommendedLogo.name }}</span>
            </div>

            <div class="logo-reason">
              <el-icon><InfoFilled /></el-icon>
              <span>{{ banner.recommendedLogo.reason }}</span>
            </div>

            <!-- Logo 选择器 -->
            <el-select
              v-model="banner.selectedLogoId"
              placeholder="选择 Logo"
              size="small"
              @change="updateLogoPreview(index)"
              class="logo-selector"
            >
              <el-option
                v-for="logo in logoLibrary"
                :key="logo.id"
                :label="logo.displayName"
                :value="logo.id"
              >
                <span>{{ logo.displayName }}</span>
                <el-tag size="small" style="margin-left: 8px">{{ logo.variant }}</el-tag>
              </el-option>
            </el-select>

            <!-- 位置调整 -->
            <el-radio-group
              v-model="banner.logoPosition"
              size="small"
              @change="updateLogoPreview(index)"
              class="position-selector"
            >
              <el-radio-button label="左上角">左上角</el-radio-button>
              <el-radio-button label="右上角">右上角</el-radio-button>
            </el-radio-group>
          </div>
        </transition>

        <!-- 选择按钮 -->
        <el-button
          type="primary"
          :icon="Check"
          @click="selectBanner(index)"
          :loading="composing && selectedIndex === index"
          class="select-button"
        >
          {{ composing && selectedIndex === index ? '合成中...' : '选择这张' }}
        </el-button>
      </div>
    </div>

    <!-- 加载中提示 -->
    <div v-if="analyzing" class="analyzing-overlay">
      <el-icon class="is-loading" :size="40"><Loading /></el-icon>
      <p>正在分析易拉宝并推荐 Logo...</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { Picture, InfoFilled, Check, Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const props = defineProps({
  bannerUrls: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['banner-selected'])

// 状态
const banners = ref([])
const logoLibrary = ref([])
const hoveredIndex = ref(null)
const analyzing = ref(false)
const composing = ref(false)
const selectedIndex = ref(null)

// 加载 Logo 库
const loadLogoLibrary = async () => {
  console.log('[BannerPreview] loadLogoLibrary 开始')
  try {
    console.log('[BannerPreview] 发送请求到 /api/logo-library')
    const response = await axios.get('/api/logo-library')
    console.log('[BannerPreview] 收到响应:', response)
    console.log('[BannerPreview] response.data:', response.data)

    logoLibrary.value = response.data.logos
    console.log('[BannerPreview] ✅ logoLibrary 设置完成:', logoLibrary.value)
  } catch (error) {
    console.error('[BannerPreview] ❌ 加载 Logo 库失败:', error)
    console.error('[BannerPreview] 错误详情:', error.message)
    console.error('[BannerPreview] 错误响应:', error.response)
    ElMessage.error('加载 Logo 库失败')
  }
}

// 分析易拉宝并推荐 Logo
const analyzeBanners = async () => {
  console.log('[BannerPreview] analyzeBanners 开始')
  analyzing.value = true

  try {
    console.log('[BannerPreview] 发送分析请求，banner_urls:', props.bannerUrls)
    const response = await axios.post('/api/analyze-banners-for-logo', {
      banner_urls: props.bannerUrls
    })

    console.log('[BannerPreview] 收到分析响应:', response)
    console.log('[BannerPreview] response.data:', response.data)

    const recommendations = response.data.recommendations
    console.log('[BannerPreview] recommendations:', recommendations)

    // 构建易拉宝数据
    banners.value = props.bannerUrls.map((url, index) => {
      const recommendation = recommendations[index]
      console.log(`[BannerPreview] 处理 banner ${index}:`, recommendation)

      if (recommendation.error) {
        console.warn(`[BannerPreview] banner ${index} 有错误:`, recommendation.error)
        return {
          url: url,
          error: recommendation.error,
          recommendedLogo: null,
          selectedLogoId: null,
          logoPosition: '右上角'
        }
      }

      const recommendedLogo = logoLibrary.value.find(
        l => l.id === recommendation.recommended_logo.id
      )
      console.log(`[BannerPreview] banner ${index} 推荐的 Logo:`, recommendedLogo)

      return {
        url: url,
        analysis: recommendation.analysis,
        recommendedLogo: {
          id: recommendation.recommended_logo.id,
          name: recommendedLogo?.displayName || '未知',
          position: recommendation.recommended_logo.position,
          sizeRatio: recommendation.recommended_logo.size_ratio,
          reason: recommendation.reason
        },
        selectedLogoId: recommendation.recommended_logo.id,
        logoPosition: recommendation.recommended_logo.position
      }
    })

    console.log('[BannerPreview] ✅ banners 构建完成:', banners.value)
    ElMessage.success('分析完成！鼠标悬停可预览 Logo 效果')
  } catch (error) {
    console.error('[BannerPreview] ❌ 分析失败:', error)
    console.error('[BannerPreview] 错误详情:', error.message)
    console.error('[BannerPreview] 错误响应:', error.response)
    ElMessage.error('分析失败，请重试')
  } finally {
    analyzing.value = false
    console.log('[BannerPreview] analyzeBanners 结束，analyzing:', analyzing.value)
  }
}

// 获取 Logo 预览 URL
const getLogoPreviewUrl = (banner) => {
  const logo = logoLibrary.value.find(l => l.id === banner.selectedLogoId)
  if (logo) {
    return `/logo_library/${logo.filename}`
  }
  return ''
}

// 获取 Logo 样式（位置和尺寸）
const getLogoStyle = (banner) => {
  const position = banner.logoPosition
  const sizeRatio = banner.recommendedLogo.sizeRatio || 0.25

  // 计算位置
  const margin = 20
  let positionStyle = {}

  if (position === '左上角') {
    positionStyle = {
      top: `${margin}px`,
      left: `${margin}px`
    }
  } else {
    positionStyle = {
      top: `${margin}px`,
      right: `${margin}px`
    }
  }

  return {
    ...positionStyle,
    width: `${sizeRatio * 100}%`,
    opacity: 0.9
  }
}

// 更新 Logo 预览
const updateLogoPreview = (index) => {
  const banner = banners.value[index]
  const selectedLogo = logoLibrary.value.find(l => l.id === banner.selectedLogoId)

  if (selectedLogo) {
    banner.recommendedLogo = {
      ...banner.recommendedLogo,
      id: selectedLogo.id,
      name: selectedLogo.displayName,
      position: banner.logoPosition
    }
  }
}

// 选择易拉宝并合成 Logo
const selectBanner = async (index) => {
  const banner = banners.value[index]

  if (!banner.selectedLogoId) {
    ElMessage.warning('请先选择一个 Logo')
    return
  }

  selectedIndex.value = index
  composing.value = true

  try {
    const response = await axios.post('/api/compose-logo', {
      banner_url: banner.url,
      logo_id: banner.selectedLogoId,
      position: banner.logoPosition
    })

    ElMessage.success('Logo 合成完成！')

    // 通知父组件
    emit('banner-selected', {
      originalUrl: banner.url,
      finalUrl: response.data.final_url,
      logoInfo: response.data.logo_info
    })
  } catch (error) {
    console.error('合成失败:', error)
    ElMessage.error('合成失败，请重试')
  } finally {
    composing.value = false
    selectedIndex.value = null
  }
}

// 组件挂载时初始化
onMounted(async () => {
  console.log('[BannerPreview] ========== 组件挂载开始 ==========')
  console.log('[BannerPreview] props.bannerUrls:', props.bannerUrls)
  console.log('[BannerPreview] bannerUrls 数量:', props.bannerUrls?.length)
  console.log('[BannerPreview] bannerUrls 类型:', typeof props.bannerUrls)

  try {
    console.log('[BannerPreview] 开始加载 Logo 库...')
    await loadLogoLibrary()
    console.log('[BannerPreview] ✅ Logo 库加载完成，数量:', logoLibrary.value.length)
    console.log('[BannerPreview] Logo 库内容:', logoLibrary.value)

    console.log('[BannerPreview] 开始分析易拉宝...')
    await analyzeBanners()
    console.log('[BannerPreview] ✅ 分析完成，banners 数量:', banners.value.length)
    console.log('[BannerPreview] banners 内容:', banners.value)

    console.log('[BannerPreview] ========== 组件挂载完成 ==========')
  } catch (error) {
    console.error('[BannerPreview] ❌ 初始化失败:', error)
    console.error('[BannerPreview] 错误详情:', error.message)
    console.error('[BannerPreview] 错误堆栈:', error.stack)
  }
})
</script>

<style scoped>
.banner-preview-container {
  padding: 20px;
  position: relative;
}

.preview-header {
  text-align: center;
  margin-bottom: 24px;
}

.preview-header h3 {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 8px;
}

.hint {
  color: #909399;
  font-size: 14px;
}

.banner-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

.banner-item {
  position: relative;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  padding: 12px;
  transition: all 0.3s;
  background: white;
}

.banner-item:hover {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.2);
}

.banner-image-wrapper {
  position: relative;
  width: 100%;
  aspect-ratio: 1 / 2;
  overflow: hidden;
  border-radius: 4px;
  background: #f5f7fa;
}

.banner-image {
  width: 100%;
  height: 100%;
}

.logo-preview-layer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.logo-overlay {
  position: absolute;
  object-fit: contain;
  transition: all 0.3s;
}

.logo-info-card {
  margin-top: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

.logo-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-weight: 600;
  color: #303133;
}

.logo-reason {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
}

.logo-selector {
  width: 100%;
  margin-bottom: 8px;
}

.position-selector {
  width: 100%;
}

.position-selector :deep(.el-radio-button__inner) {
  width: 100%;
}

.select-button {
  width: 100%;
  margin-top: 12px;
}

.analyzing-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.95);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.analyzing-overlay p {
  margin-top: 16px;
  font-size: 16px;
  color: #606266;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

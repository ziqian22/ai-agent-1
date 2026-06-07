<template>
  <div class="app-container">
    <el-container>
      <!-- 左侧导航栏 -->
      <el-aside width="200px" class="sidebar">
        <div class="logo">
          <h2>🎨 易拉宝助手</h2>
        </div>
        <el-menu
          :default-active="activeMenu"
          @select="handleMenuSelect"
          class="sidebar-menu"
        >
          <el-menu-item index="chat">
            <el-icon><ChatDotRound /></el-icon>
            <span>Agent 对话</span>
          </el-menu-item>
          <el-menu-item index="knowledge">
            <el-icon><FolderOpened /></el-icon>
            <span>知识库管理</span>
          </el-menu-item>
          <el-menu-item index="history">
            <el-icon><PictureFilled /></el-icon>
            <span>生成记录</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容区 -->
      <el-container>
        <el-header class="app-header">
          <div class="header-content">
            <h3>{{ getPageTitle() }}</h3>
            <div class="header-actions">
              <el-button
                v-if="activeMenu === 'chat'"
                @click="resetSession"
                :icon="Refresh"
              >
                重新开始
              </el-button>
            </div>
          </div>
        </el-header>

        <el-main class="app-main">
          <!-- 根据 activeMenu 显示不同内容 -->
          <ChatArea
            v-if="activeMenu === 'chat'"
            :session-id="sessionId"
            @session-created="handleSessionCreated"
          />
          <KnowledgeBase
            v-else-if="activeMenu === 'knowledge'"
            :key="knowledgeBaseKey"
            @switch-to-chat="handleSwitchToChat"
          />
          <GenerationHistory
            v-else-if="activeMenu === 'history'"
            :key="generationHistoryKey"
          />
        </el-main>
      </el-container>
    </el-container>

    <!-- 页面使用精灵助手 -->
    <HelpAssistant />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Refresh, ChatDotRound, FolderOpened, PictureFilled } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import ChatArea from './components/ChatArea.vue'
import KnowledgeBase from './views/KnowledgeBase.vue'
import GenerationHistory from './views/GenerationHistory.vue'
import HelpAssistant from './components/HelpAssistant.vue'

const sessionId = ref(null)
const activeMenu = ref('chat')

// 用于强制刷新组件的 key
const knowledgeBaseKey = ref(0)
const generationHistoryKey = ref(0)

const handleSessionCreated = (id) => {
  sessionId.value = id
}

const handleSwitchToChat = (newSessionId) => {
  // 更新 sessionId
  sessionId.value = newSessionId
  // 切换到对话页面
  activeMenu.value = 'chat'
}

const handleMenuSelect = (index) => {
  activeMenu.value = index

  // 切换到知识库或生成记录时,强制刷新组件
  if (index === 'knowledge') {
    knowledgeBaseKey.value++
  } else if (index === 'history') {
    generationHistoryKey.value++
  }
}

const getPageTitle = () => {
  const titles = {
    chat: 'Agent 对话',
    knowledge: '知识库管理',
    history: '生成记录'
  }
  return titles[activeMenu.value] || ''
}

const resetSession = async () => {
  if (!sessionId.value) {
    location.reload()
    return
  }

  try {
    await ElMessageBox.confirm(
      '确定要重新开始吗？当前对话将被清除。',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    location.reload()
  } catch {
    // 用户取消
  }
}
</script>

<style scoped>
.app-container {
  height: 100vh;
  background: #f5f7fa;
}

.sidebar {
  background: white;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}

.logo {
  padding: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.logo h2 {
  margin: 0;
  font-size: 18px;
  color: #303133;
  text-align: center;
}

.sidebar-menu {
  flex: 1;
  border-right: none;
}

.app-header {
  background: white;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}

.header-content h3 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.app-main {
  padding: 24px;
  height: calc(100vh - 60px);
  overflow: auto;
}
</style>

<template>
  <div class="chat-container">
    <!-- 左侧对话列表 -->
    <div class="conversation-sidebar">
      <div class="sidebar-header">
        <el-button type="primary" :icon="Plus" @click="createNewConversation" style="width: 100%">
          新建对话
        </el-button>
      </div>

      <div class="conversation-list">
        <div
          v-for="conv in conversations"
          :key="conv.id"
          class="conversation-item"
          :class="{ active: conv.id === sessionId }"
          @click="switchConversation(conv.id)"
        >
          <div class="conv-header">
            <div class="conv-title">{{ conv.title }}</div>
            <el-icon class="delete-icon" @click.stop="deleteConversation(conv.id)">
              <Delete />
            </el-icon>
          </div>
          <div class="conv-meta">
            <span>{{ conv.messageCount }} 条消息</span>
            <span>{{ formatTime(conv.updatedAt) }}</span>
          </div>
        </div>

        <el-empty v-if="conversations.length === 0" description="暂无对话" :image-size="60" />
      </div>
    </div>

    <!-- 右侧对话区域 -->
    <div class="chat-area">
      <!-- 对话内容保持原样 -->
      <slot></slot>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { Plus, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// Props
const props = defineProps({
  sessionId: String,
  messages: Array
})

// Emits
const emit = defineEmits(['new-conversation', 'switch-conversation'])

// 对话列表
const conversations = ref(JSON.parse(localStorage.getItem('conversations') || '[]'))

// 新建对话
const createNewConversation = () => {
  // 保存当前对话
  if (props.sessionId && props.messages.length > 0) {
    saveCurrentConversation()
  }

  emit('new-conversation')
  ElMessage.success('已创建新对话')
}

// 保存当前对话
const saveCurrentConversation = () => {
  if (!props.sessionId || props.messages.length === 0) return

  const conversation = {
    id: props.sessionId,
    title: extractTitle(props.messages),
    messages: props.messages,
    createdAt: conversations.value.find(c => c.id === props.sessionId)?.createdAt || new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    messageCount: props.messages.length
  }

  // 更新或添加对话
  const index = conversations.value.findIndex(c => c.id === props.sessionId)
  if (index >= 0) {
    conversations.value[index] = conversation
  } else {
    conversations.value.unshift(conversation)
  }

  // 保存到 localStorage
  localStorage.setItem('conversations', JSON.stringify(conversations.value))
}

// 切换对话
const switchConversation = (conversationId) => {
  if (conversationId === props.sessionId) return

  // 保存当前对话
  if (props.sessionId && props.messages.length > 0) {
    saveCurrentConversation()
  }

  // 加载目标对话
  const conversation = conversations.value.find(c => c.id === conversationId)
  if (conversation) {
    emit('switch-conversation', conversation)
  }
}

// 删除对话
const deleteConversation = async (conversationId) => {
  try {
    await ElMessageBox.confirm('确定要删除这个对话吗?', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    conversations.value = conversations.value.filter(c => c.id !== conversationId)
    localStorage.setItem('conversations', JSON.stringify(conversations.value))

    // 如果删除的是当前对话,创建新对话
    if (conversationId === props.sessionId) {
      emit('new-conversation')
    }

    ElMessage.success('对话已删除')
  } catch {
    // 用户取消
  }
}

// 提取对话标题
const extractTitle = (messages) => {
  // 从第一条助手消息中提取产品名称
  const firstAssistant = messages.find(m => m.role === 'assistant')
  if (firstAssistant) {
    const match = firstAssistant.content.match(/产品名称[：:]\s*[*]*(.+?)[\n*]/)
    if (match) {
      return match[1].trim().replace(/\*/g, '')
    }
  }
  return '新对话 ' + new Date().toLocaleTimeString()
}

// 格式化时间
const formatTime = (timeStr) => {
  const time = new Date(timeStr)
  const now = new Date()
  const diff = now - time

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  return time.toLocaleDateString()
}

// 监听消息变化,自动保存
watch(() => props.messages, () => {
  if (props.sessionId && props.messages.length > 0) {
    saveCurrentConversation()
  }
}, { deep: true })

// 组件挂载时加载对话列表
onMounted(() => {
  conversations.value = JSON.parse(localStorage.getItem('conversations') || '[]')
})
</script>

<style scoped>
.chat-container {
  display: flex;
  height: 100%;
  gap: 0;
}

.conversation-sidebar {
  width: 260px;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  background: #fafafa;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
  background: white;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.conversation-item {
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
  border: 1px solid #e4e7ed;
}

.conversation-item:hover {
  background: #f5f7fa;
  border-color: #409eff;
}

.conversation-item.active {
  background: #e6f7ff;
  border-color: #409eff;
  box-shadow: 0 2px 4px rgba(64, 158, 255, 0.2);
}

.conv-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.conv-title {
  font-weight: 500;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.delete-icon {
  color: #909399;
  cursor: pointer;
  transition: color 0.2s;
}

.delete-icon:hover {
  color: #f56c6c;
}

.conv-meta {
  font-size: 12px;
  color: #909399;
  display: flex;
  justify-content: space-between;
}

.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
</style>

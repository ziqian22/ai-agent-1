<template>
  <conversation-manager
    :session-id="sessionId"
    :messages="messages"
    @new-conversation="handleNewConversation"
    @switch-conversation="handleSwitchConversation"
  >
    <div class="chat-area">
      <el-card class="chat-card">
      <!-- 对话历史 -->
      <div class="chat-history" ref="chatHistoryRef">
        <!-- 欢迎消息 -->
        <div v-if="messages.length === 0" class="welcome-message">
          <el-empty description="开始对话">
            <template #image>
              <el-icon :size="100" color="#409eff"><ChatDotRound /></el-icon>
            </template>
            <p>上传产品图片或文档,我会帮您设计专业的易拉宝</p>
          </el-empty>
        </div>

        <!-- 消息列表 -->
        <div
          v-for="(msg, index) in messages"
          :key="index"
          :class="['message', msg.role]"
        >
          <div class="message-content">
            <div class="message-text" v-html="formatMessage(msg.content)"></div>

            <!-- 快捷按钮（使用后端返回的 quick_actions） -->
            <div v-if="msg.role === 'assistant' && msg.quick_actions && msg.quick_actions.length > 0" class="quick-actions-inline">
              <el-button
                v-for="(action, idx) in msg.quick_actions"
                :key="idx"
                :type="action.label.includes('✅') || action.label.includes('确认') ? 'primary' : 'default'"
                size="default"
                @click="sendQuickMessage(action.value)"
                :disabled="loading"
              >
                {{ action.label }}
              </el-button>
            </div>

            <!-- 显示生成的图片 -->
            <div v-if="msg.images && msg.images.length > 0" class="message-images">
              <el-image
                v-for="(img, idx) in msg.images"
                :key="idx"
                :src="img"
                :preview-src-list="msg.images"
                fit="cover"
                class="result-image"
              />
            </div>
          </div>
        </div>

        <!-- 加载中提示 -->
        <div v-if="loading" class="message assistant">
          <div class="message-content">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>思考中...</span>
          </div>
        </div>
      </div>

      <!-- 已选择的文件预览 -->
      <div v-if="selectedFile" class="file-preview">
        <el-tag closable @close="clearSelectedFile" type="info" size="large">
          <el-icon><Document /></el-icon>
          {{ selectedFile.name }}
        </el-tag>
        <el-checkbox v-model="saveToKnowledgeBase" style="margin-left: 12px">
          同步到知识库
        </el-checkbox>
      </div>

      <!-- 输入框 -->
      <div class="chat-input">
        <div class="input-wrapper">
          <!-- 左侧按钮组 -->
          <div class="input-actions-left">
            <!-- 文件上传按钮 -->
            <el-upload
              ref="fileUploadRef"
              :auto-upload="false"
              :on-change="handleFileSelect"
              :show-file-list="false"
              accept=".png,.jpg,.jpeg,.pdf,.docx,.pptx"
            >
              <el-button :icon="Document" circle title="上传文件(PDF/Word/PPT)"></el-button>
            </el-upload>

            <!-- 图片上传按钮 -->
            <el-upload
              ref="imageUploadRef"
              :auto-upload="false"
              :on-change="handleImageSelect"
              :show-file-list="false"
              accept=".png,.jpg,.jpeg"
            >
              <el-button :icon="Picture" circle title="上传图片"></el-button>
            </el-upload>

            <!-- 知识库按钮 -->
            <el-button :icon="FolderOpened" circle title="从知识库选择" @click="openKnowledgeSelector"></el-button>
          </div>

          <!-- 输入框 -->
          <el-input
            v-model="userInput"
            :disabled="loading"
            placeholder="输入您的需求或问题..."
            @keyup.enter="sendMessage"
            class="message-input"
            :rows="1"
            type="textarea"
            resize="none"
          />

          <!-- 发送按钮 -->
          <el-button
            :icon="Promotion"
            :loading="loading"
            @click="sendMessage"
            type="primary"
            circle
            size="large"
            class="send-button"
          >
          </el-button>
        </div>
      </div>
    </el-card>
    </div>

    <!-- 知识库选择器 -->
    <knowledge-base-selector
      v-model="showKnowledgeSelector"
      @product-selected="handleProductSelected"
    />
  </conversation-manager>
</template>

<script setup>
import { ref, nextTick, onMounted, watch } from 'vue'
import { Document, Picture, FolderOpened, Promotion, Loading, ChatDotRound } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { uploadFile, sendChatMessage } from '../api/chat'
import ConversationManager from './ConversationManager.vue'
import KnowledgeBaseSelector from './KnowledgeBaseSelector.vue'
import axios from 'axios'

const emit = defineEmits(['session-created'])
const props = defineProps({
  sessionId: String
})

// 使用 sessionStorage 持久化对话数据
const sessionId = ref(props.sessionId || sessionStorage.getItem('chat_session_id') || null)
const messages = ref(JSON.parse(sessionStorage.getItem('chat_messages') || '[]'))
const userInput = ref('')
const loading = ref(false)
const chatHistoryRef = ref(null)
const selectedFile = ref(null)
const saveToKnowledgeBase = ref(false)

// 知识库选择器
const showKnowledgeSelector = ref(false)

// 新建对话
const handleNewConversation = () => {
  // 清空当前对话
  sessionId.value = null
  messages.value = []
  userInput.value = ''
  selectedFile.value = null
  saveToKnowledgeBase.value = false

  // 清空 sessionStorage
  sessionStorage.removeItem('chat_session_id')
  sessionStorage.removeItem('chat_messages')
}

// 切换对话
const handleSwitchConversation = (conversation) => {
  sessionId.value = conversation.id
  messages.value = conversation.messages

  // 更新 sessionStorage
  sessionStorage.setItem('chat_session_id', conversation.id)
  sessionStorage.setItem('chat_messages', JSON.stringify(conversation.messages))

  nextTick(() => {
    scrollToBottom()
  })
}

// 监听 sessionId 变化
watch(sessionId, (newVal) => {
  if (newVal) {
    sessionStorage.setItem('chat_session_id', newVal)
  }
})

// 监听 props.sessionId 变化（从知识库加载时）
watch(() => props.sessionId, (newVal) => {
  if (newVal && newVal !== sessionId.value) {
    sessionId.value = newVal
    // 从 sessionStorage 加载消息
    const savedMessages = sessionStorage.getItem('chat_messages')
    if (savedMessages) {
      messages.value = JSON.parse(savedMessages)
      nextTick(() => {
        scrollToBottom()
      })
    }
  }
})

// 监听 messages 变化
watch(messages, (newVal) => {
  sessionStorage.setItem('chat_messages', JSON.stringify(newVal))
}, { deep: true })

// 组件挂载时恢复数据
onMounted(() => {
  if (messages.value.length > 0) {
    scrollToBottom()
  }
})

// 文件选择(不立即上传)
const handleFileSelect = (file) => {
  selectedFile.value = file
  ElMessage.info(`已选择文件: ${file.name}，点击发送按钮开始分析`)
}

// 图片选择(不立即上传)
const handleImageSelect = (file) => {
  selectedFile.value = file
  ElMessage.info(`已选择图片: ${file.name}，点击发送按钮开始分析`)
}

// 清除选择
const clearSelectedFile = () => {
  selectedFile.value = null
  saveToKnowledgeBase.value = false
}

// 打开知识库选择器
const openKnowledgeSelector = () => {
  showKnowledgeSelector.value = true
}

// 处理知识库产品选择
const handleProductSelected = async (product) => {
  try {
    loading.value = true
    ElMessage.info('正在加载产品信息...')

    // 调用后端API使用该产品
    const response = await axios.post(`/api/knowledge-base/products/${product.id}/use`)

    // 如果当前没有会话，创建新会话
    if (!sessionId.value) {
      sessionId.value = response.data.session_id
      emit('session-created', response.data.session_id)
    } else {
      // 如果已有会话，需要更新会话信息
      // 这里我们清空当前对话，使用新的产品信息
      sessionId.value = response.data.session_id
      messages.value = []
    }

    // 添加助手消息
    messages.value.push({
      role: 'assistant',
      content: response.data.message
    })

    scrollToBottom()
    ElMessage.success('已加载产品信息')
  } catch (error) {
    console.error('加载产品失败:', error)
    ElMessage.error(error.response?.data?.detail || '加载产品失败')
  } finally {
    loading.value = false
  }
}

// 显示知识库选择器（旧方法，保持兼容）
const showKnowledgeSelectorOld = () => {
  openKnowledgeSelector()
}

// 发送消息(包含文件)
const sendMessage = async () => {
  // 如果有选中的文件,先上传
  if (selectedFile.value) {
    await uploadFileAndAnalyze()
    return
  }

  // 否则发送文本消息
  if (!userInput.value.trim() || loading.value) return

  const message = userInput.value.trim()
  userInput.value = ''

  // ✅ 修复问题2: 如果没有 session_id，先生成一个
  if (!sessionId.value) {
    sessionId.value = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
    emit('session-created', sessionId.value)
  }

  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: message
  })

  scrollToBottom()
  loading.value = true

  try {
    const response = await sendChatMessage(sessionId.value, message)

    // 添加助手回复
    messages.value.push({
      role: 'assistant',
      content: response.content,
      images: response.images,
      quick_actions: response.quick_actions || []  // 保存后端返回的快捷按钮
    })

    scrollToBottom()
  } catch (error) {
    ElMessage.error(error.message || '发送失败')
  } finally {
    loading.value = false
  }
}

// 发送快捷消息（点击按钮时）
const sendQuickMessage = async (message) => {
  if (loading.value) return

  // ✅ 修复问题2: 如果没有 session_id，先生成一个
  if (!sessionId.value) {
    sessionId.value = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
    emit('session-created', sessionId.value)
  }

  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: message
  })

  scrollToBottom()
  loading.value = true

  try {
    const response = await sendChatMessage(sessionId.value, message)

    // 添加助手回复
    messages.value.push({
      role: 'assistant',
      content: response.content,
      images: response.images,
      quick_actions: response.quick_actions || []  // 保存后端返回的快捷按钮
    })

    scrollToBottom()
  } catch (error) {
    ElMessage.error(error.message || '发送失败')
  } finally {
    loading.value = false
  }
}

// 上传文件并分析
const uploadFileAndAnalyze = async () => {
  loading.value = true

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value.raw)
    formData.append('save_to_kb', saveToKnowledgeBase.value)

    // 如果已有 session_id,传递给后端
    if (sessionId.value) {
      formData.append('session_id', sessionId.value)
    }

    const response = await uploadFile(formData)

    // ✅ 修复问题2: 始终使用后端返回的 session_id（后端可能创建了新的）
    if (response.session_id && response.session_id !== sessionId.value) {
      sessionId.value = response.session_id
      emit('session-created', response.session_id)
    }

    // 添加用户消息(显示上传的文件)
    messages.value.push({
      role: 'user',
      content: `上传了文件: ${selectedFile.value.name}`
    })

    // 添加助手的分析结果到对话
    messages.value.push({
      role: 'assistant',
      content: response.analysis,
      quick_actions: response.quick_actions || []  // 保存后端返回的快捷按钮
    })

    // 清除选择
    clearSelectedFile()
    scrollToBottom()
    ElMessage.success('文件上传成功')
  } catch (error) {
    ElMessage.error(error.message || '文件上传失败')
  } finally {
    loading.value = false
  }
}

// 格式化消息（支持 Markdown 基本格式）
const formatMessage = (text) => {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (chatHistoryRef.value) {
      chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight
    }
  })
}
</script>

<style scoped>
.chat-area {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  min-height: 400px;
  max-height: calc(100vh - 300px);
}

.welcome-message {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
}

.welcome-message p {
  margin-top: 16px;
  font-size: 14px;
}

.message {
  margin-bottom: 16px;
  display: flex;
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.message-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 8px;
  word-wrap: break-word;
}

.message.user .message-content {
  background: #409eff;
  color: white;
}

.message.assistant .message-content {
  background: #f4f4f5;
  color: #303133;
}

.message-text {
  line-height: 1.6;
}

.quick-actions-inline {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #e4e7ed;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.message.assistant .quick-actions-inline {
  border-top-color: #dcdfe6;
}

.message-images {
  margin-top: 12px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.result-image {
  width: 200px;
  height: 400px;
  border-radius: 4px;
  cursor: pointer;
}

.file-preview {
  padding: 12px 20px;
  border-top: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
}

.chat-input {
  padding: 16px 20px;
  border-top: 1px solid #e4e7ed;
}

.input-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.input-actions-left {
  display: flex;
  gap: 8px;
}

.message-input {
  flex: 1;
}

.message-input :deep(.el-textarea__inner) {
  padding: 10px 12px;
  line-height: 1.5;
  min-height: 40px !important;
  max-height: 120px;
  resize: none;
}

.send-button {
  flex-shrink: 0;
}

.is-loading {
  margin-right: 8px;
}
</style>

<template>
  <div class="help-assistant">
    <!-- 悬浮球按钮 -->
    <el-badge
      :value="unreadCount"
      :hidden="!unreadCount || isOpen"
      class="floating-badge"
    >
      <el-button
        :icon="isOpen ? Close : QuestionFilled"
        circle
        size="large"
        type="primary"
        class="floating-button"
        @click="togglePanel"
        :class="{ 'is-open': isOpen }"
      >
      </el-button>
    </el-badge>

    <!-- 对话面板 -->
    <transition name="slide-fade">
      <div v-if="isOpen" class="help-panel">
        <!-- 头部 -->
        <div class="help-header">
          <div class="header-info">
            <el-icon class="header-icon"><MagicStick /></el-icon>
            <span class="header-title">使用精灵</span>
          </div>
          <el-button
            :icon="Close"
            text
            @click="closePanel"
            class="close-btn"
          />
        </div>

        <!-- 对话区域 -->
        <div class="help-messages" ref="messagesContainer">
          <div
            v-for="(msg, index) in messages"
            :key="index"
            :class="['message-item', msg.role]"
          >
            <div class="message-avatar">
              <el-icon v-if="msg.role === 'assistant'">
                <MagicStick />
              </el-icon>
              <el-icon v-else>
                <User />
              </el-icon>
            </div>
            <div class="message-content">
              <div class="message-text" v-html="formatMessage(msg.content)"></div>
              <div class="message-time">{{ msg.time }}</div>
            </div>
          </div>

          <!-- 加载状态 -->
          <div v-if="loading" class="message-item assistant">
            <div class="message-avatar">
              <el-icon><MagicStick /></el-icon>
            </div>
            <div class="message-content">
              <div class="message-text typing">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="help-input">
          <el-input
            v-model="userInput"
            type="textarea"
            :rows="2"
            placeholder="有什么可以帮助您的吗？"
            @keydown.enter.exact.prevent="sendMessage"
            :disabled="loading"
          />
          <el-button
            type="primary"
            :icon="Promotion"
            @click="sendMessage"
            :loading="loading"
            :disabled="!userInput.trim()"
          >
            发送
          </el-button>
        </div>

        <!-- 快捷问题 -->
        <div class="quick-questions" v-if="messages.length === 1">
          <div class="quick-title">常见问题：</div>
          <el-tag
            v-for="(q, index) in quickQuestions"
            :key="index"
            class="quick-tag"
            @click="askQuestion(q)"
          >
            {{ q }}
          </el-tag>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { QuestionFilled, Close, MagicStick, User, Promotion } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const isOpen = ref(false)
const loading = ref(false)
const userInput = ref('')
const messages = ref([])
const messagesContainer = ref(null)
const unreadCount = ref(0)

// 快捷问题
const quickQuestions = [
  '如何上传产品图片？',
  '支持哪些设计风格？',
  '如何使用知识库？',
  '生成需要多长时间？'
]

// 初始化欢迎消息
onMounted(() => {
  messages.value = [{
    role: 'assistant',
    content: '你好！我是页面使用精灵 🧚‍♀️\n\n我可以帮助你了解系统的所有功能和使用方法。有什么问题尽管问我吧！',
    time: formatTime()
  }]
})

// 切换面板
const togglePanel = () => {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    unreadCount.value = 0
    nextTick(() => {
      scrollToBottom()
    })
  }
}

const closePanel = () => {
  isOpen.value = false
}

// 发送消息
const sendMessage = async () => {
  const message = userInput.value.trim()
  if (!message || loading.value) return

  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: message,
    time: formatTime()
  })

  userInput.value = ''
  loading.value = true

  nextTick(() => {
    scrollToBottom()
  })

  try {
    const response = await axios.post('/api/help/chat', {
      message: message,
      history: messages.value.slice(0, -1).map(m => ({
        role: m.role,
        content: m.content
      }))
    })

    // 添加助手回复
    messages.value.push({
      role: 'assistant',
      content: response.data.reply,
      time: formatTime()
    })

    // 如果面板关闭，显示未读消息提示
    if (!isOpen.value) {
      unreadCount.value++
    }
  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error('发送失败，请重试')
    // 移除用户消息
    messages.value.pop()
  } finally {
    loading.value = false
    nextTick(() => {
      scrollToBottom()
    })
  }
}

// 快速提问
const askQuestion = (question) => {
  userInput.value = question
  sendMessage()
}

// 格式化消息（支持简单的 markdown）
const formatMessage = (text) => {
  return text
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
}

// 格式化时间
const formatTime = () => {
  const now = new Date()
  return `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
}

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}
</script>

<style scoped>
.help-assistant {
  position: fixed;
  bottom: 30px;
  right: 30px;
  z-index: 9999;
}

.floating-badge {
  display: block;
}

.floating-button {
  width: 60px;
  height: 60px;
  font-size: 28px;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
  transition: all 0.3s ease;
}

.floating-button:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 16px rgba(64, 158, 255, 0.4);
}

.floating-button.is-open {
  background-color: #909399;
}

.help-panel {
  position: fixed;
  bottom: 110px;
  right: 30px;
  width: 400px;
  height: 600px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.help-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon {
  font-size: 20px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
}

.close-btn {
  color: white;
  font-size: 18px;
}

.help-messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background: #f5f7fa;
}

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 18px;
}

.message-item.assistant .message-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.message-item.user .message-avatar {
  background: #409eff;
  color: white;
}

.message-content {
  max-width: 75%;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message-item.user .message-content {
  align-items: flex-end;
}

.message-text {
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  word-break: break-word;
}

.message-item.assistant .message-text {
  background: white;
  color: #303133;
  border-radius: 0 12px 12px 12px;
}

.message-item.user .message-text {
  background: #409eff;
  color: white;
  border-radius: 12px 0 12px 12px;
}

.message-time {
  font-size: 12px;
  color: #909399;
  padding: 0 4px;
}

/* 打字效果 */
.typing {
  display: flex;
  gap: 4px;
  padding: 16px !important;
}

.typing span {
  width: 8px;
  height: 8px;
  background: #909399;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-10px);
  }
}

.help-input {
  padding: 16px;
  background: white;
  border-top: 1px solid #e4e7ed;
  display: flex;
  gap: 12px;
}

.help-input :deep(.el-textarea__inner) {
  resize: none;
  border-radius: 8px;
}

.help-input .el-button {
  align-self: flex-end;
}

.quick-questions {
  padding: 12px 16px 16px;
  background: white;
  border-top: 1px solid #e4e7ed;
}

.quick-title {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.quick-tag {
  margin-right: 8px;
  margin-bottom: 8px;
  cursor: pointer;
}

/* 过渡动画 */
.slide-fade-enter-active {
  transition: all 0.3s ease;
}

.slide-fade-leave-active {
  transition: all 0.3s ease;
}

.slide-fade-enter-from {
  transform: translateY(20px);
  opacity: 0;
}

.slide-fade-leave-to {
  transform: translateY(20px);
  opacity: 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .help-panel {
    width: calc(100vw - 40px);
    height: 500px;
    right: 20px;
    bottom: 100px;
  }

  .help-assistant {
    right: 20px;
    bottom: 20px;
  }
}
</style>

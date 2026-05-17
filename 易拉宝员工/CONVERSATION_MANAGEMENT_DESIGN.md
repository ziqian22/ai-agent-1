# 新建对话和历史对话功能设计

## 功能需求

### 1. 新建对话
- 点击"新建对话"按钮
- 创建新的 session
- 清空当前对话界面
- 可以上传新的产品图片

### 2. 历史对话列表
- 显示所有历史对话
- 每个对话显示:
  - 产品名称
  - 创建时间
  - 对话消息数
- 点击可以切换到该对话

### 3. 对话切换
- 切换对话时,加载该对话的历史消息
- 保持 session_id
- 可以继续对话

---

## UI 设计

### 方案 1: 左侧边栏 (推荐)

```
┌─────────────────────────────────────────────────┐
│  🎨 易拉宝助手                                   │
├──────────┬──────────────────────────────────────┤
│          │  Agent 对话                          │
│ 对话列表 │  ┌────────────────────────────────┐ │
│          │  │ 新建对话 [+]                   │ │
│ [+] 新对话│  └────────────────────────────────┘ │
│          │                                      │
│ 📝 产品A │  对话内容区域                        │
│   5条消息│  ┌────────────────────────────────┐ │
│   刚刚   │  │ 用户: 上传了产品图             │ │
│          │  │ AI: 我已经分析了...            │ │
│ 📝 产品B │  │ ...                            │ │
│   3条消息│  └────────────────────────────────┘ │
│   10分钟前│                                     │
│          │  输入框                              │
│ 📝 产品C │  ┌────────────────────────────────┐ │
│   8条消息│  │ [文件] [图片] [知识库] [发送] │ │
│   1小时前│  └────────────────────────────────┘ │
└──────────┴──────────────────────────────────────┘
```

### 方案 2: 顶部标签页

```
┌─────────────────────────────────────────────────┐
│  🎨 易拉宝助手                                   │
├─────────────────────────────────────────────────┤
│  Agent 对话                                      │
│  ┌─────┬─────┬─────┬─────┬─────┐               │
│  │产品A│产品B│产品C│ ... │ [+] │               │
│  └─────┴─────┴─────┴─────┴─────┘               │
│                                                  │
│  对话内容区域                                    │
│  ┌────────────────────────────────────────────┐ │
│  │ 用户: 上传了产品图                         │ │
│  │ AI: 我已经分析了...                        │ │
│  │ ...                                        │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  输入框                                          │
│  ┌────────────────────────────────────────────┐ │
│  │ [文件] [图片] [知识库] [发送]             │ │
│  └────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

**推荐方案 1**: 左侧边栏,更清晰,更符合聊天应用习惯

---

## 数据结构

### 对话列表存储

```javascript
// localStorage 存储所有对话
const conversations = [
  {
    id: "session_xxx",
    title: "名士K6直饮机",  // 产品名称
    messages: [...],
    createdAt: "2026-05-17T18:00:00",
    updatedAt: "2026-05-17T18:30:00",
    messageCount: 5
  },
  {
    id: "session_yyy",
    title: "名士N5智能直饮机",
    messages: [...],
    createdAt: "2026-05-17T17:00:00",
    updatedAt: "2026-05-17T17:20:00",
    messageCount: 3
  }
]
```

### 当前对话

```javascript
const currentConversationId = ref(null)
const currentMessages = ref([])
```

---

## 实现步骤

### 步骤 1: 修改 ChatArea.vue

**添加对话管理功能**:
```javascript
// 对话列表
const conversations = ref(JSON.parse(localStorage.getItem('conversations') || '[]'))
const currentConversationId = ref(localStorage.getItem('current_conversation_id') || null)

// 新建对话
const createNewConversation = () => {
  // 保存当前对话
  if (currentConversationId.value) {
    saveCurrentConversation()
  }
  
  // 创建新对话
  currentConversationId.value = null
  sessionId.value = null
  messages.value = []
  
  // 清空 sessionStorage
  sessionStorage.removeItem('chat_session_id')
  sessionStorage.removeItem('chat_messages')
  
  ElMessage.success('已创建新对话')
}

// 保存当前对话
const saveCurrentConversation = () => {
  if (!sessionId.value || messages.value.length === 0) return
  
  const conversation = {
    id: sessionId.value,
    title: extractTitle(messages.value),  // 从消息中提取标题
    messages: messages.value,
    createdAt: conversations.value.find(c => c.id === sessionId.value)?.createdAt || new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    messageCount: messages.value.length
  }
  
  // 更新或添加对话
  const index = conversations.value.findIndex(c => c.id === sessionId.value)
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
  // 保存当前对话
  if (currentConversationId.value) {
    saveCurrentConversation()
  }
  
  // 加载目标对话
  const conversation = conversations.value.find(c => c.id === conversationId)
  if (conversation) {
    currentConversationId.value = conversationId
    sessionId.value = conversationId
    messages.value = conversation.messages
    
    // 更新 sessionStorage
    sessionStorage.setItem('chat_session_id', conversationId)
    sessionStorage.setItem('chat_messages', JSON.stringify(conversation.messages))
    
    scrollToBottom()
  }
}

// 提取对话标题
const extractTitle = (messages) => {
  // 从第一条助手消息中提取产品名称
  const firstAssistant = messages.find(m => m.role === 'assistant')
  if (firstAssistant) {
    const match = firstAssistant.content.match(/产品名称[：:]\s*(.+?)[\n*]/)
    if (match) {
      return match[1].trim()
    }
  }
  return '新对话'
}

// 监听消息变化,自动保存
watch(messages, () => {
  if (sessionId.value) {
    saveCurrentConversation()
  }
}, { deep: true })
```

### 步骤 2: 添加 UI 组件

**对话列表侧边栏**:
```vue
<template>
  <div class="chat-container">
    <!-- 左侧对话列表 -->
    <div class="conversation-sidebar">
      <div class="sidebar-header">
        <h3>对话列表</h3>
        <el-button type="primary" :icon="Plus" @click="createNewConversation">
          新建对话
        </el-button>
      </div>
      
      <div class="conversation-list">
        <div
          v-for="conv in conversations"
          :key="conv.id"
          class="conversation-item"
          :class="{ active: conv.id === currentConversationId }"
          @click="switchConversation(conv.id)"
        >
          <div class="conv-title">{{ conv.title }}</div>
          <div class="conv-meta">
            <span>{{ conv.messageCount }} 条消息</span>
            <span>{{ formatTime(conv.updatedAt) }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 右侧对话区域 -->
    <div class="chat-area">
      <!-- 原有的对话界面 -->
    </div>
  </div>
</template>
```

### 步骤 3: 样式

```css
.chat-container {
  display: flex;
  height: 100%;
}

.conversation-sidebar {
  width: 250px;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
}

.conversation-item {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background 0.2s;
}

.conversation-item:hover {
  background: #f5f7fa;
}

.conversation-item.active {
  background: #e6f7ff;
  border-left: 3px solid #409eff;
}

.conv-title {
  font-weight: 500;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
}
```

---

## 优势

### 1. 多产品管理 ✨
- 可以同时处理多个产品
- 每个产品独立的对话
- 不会混淆

### 2. 历史记录 📝
- 保留所有对话历史
- 可以随时查看之前的对话
- 可以继续之前的对话

### 3. 用户体验 🎯
- 类似微信/钉钉的聊天界面
- 符合用户习惯
- 操作简单直观

---

## 注意事项

### 1. 数据持久化

- 使用 `localStorage` 存储对话列表
- 每次消息变化自动保存
- 刷新页面后数据不丢失

### 2. 性能优化

- 对话列表只显示最近 20 条
- 旧对话可以归档
- 消息过多时分页加载

### 3. 删除对话

- 添加删除按钮
- 确认后删除对话
- 删除后无法恢复

---

**设计时间**: 2026-05-17
**状态**: 设计完成,准备实现

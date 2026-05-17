import axios from 'axios'

// 根据环境变量决定 API 地址
const API_BASE_URL = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: API_BASE_URL ? `${API_BASE_URL}/api` : '/api',
  timeout: 900000, // 15分钟超时（易拉宝生成平均需要6分钟，最长可达18分钟）
})

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)

/**
 * 上传文件
 * @param {FormData} formData - 包含文件的 FormData
 * @returns {Promise<{session_id: string, analysis: string, product_info: object}>}
 */
export const uploadFile = (formData) => {
  return api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 发送聊天消息
 * @param {string} sessionId - 会话 ID
 * @param {string} message - 用户消息
 * @returns {Promise<{type: string, content: string, images: string[]}>}
 */
export const sendChatMessage = (sessionId, message) => {
  return api.post('/chat', {
    session_id: sessionId,
    message
  })
}

/**
 * 获取会话信息
 * @param {string} sessionId - 会话 ID
 * @returns {Promise<object>}
 */
export const getSession = (sessionId) => {
  return api.get(`/session/${sessionId}`)
}

/**
 * 删除会话
 * @param {string} sessionId - 会话 ID
 * @returns {Promise<object>}
 */
export const deleteSession = (sessionId) => {
  return api.delete(`/session/${sessionId}`)
}

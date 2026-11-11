import axios from 'axios'
import { getToken } from './auth'
import { ElMessage } from 'element-plus'
import { logout } from './user'
import router from '@/router'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 60000
})

// 请求拦截器
service.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器
service.interceptors.response.use(
  (res) => {
    const data = res.data
    // 后端统一返回 HTTP 200，业务错误放在 body 的 code 字段里
    if (data && typeof data === 'object' && 'code' in data && data.code !== 200) {
      if (data.code === 401) {
        logout()
        router.push('/login')
      }
      ElMessage.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message || '请求失败'))
    }
    return data
  },
  (err) => {
    if (err.response) {
      const httpStatus = err.response.status

      if (httpStatus === 401) {
        ElMessage.error('登录状态已失效，请重新登录')
        logout()
        router.push('/login')
      } else {
        ElMessage.error(err.response.data?.message || '请求失败')
      }
    } else {
      ElMessage.error('网络异常，请检查后端服务')
    }

    return Promise.reject(err)
  }
)

export default service

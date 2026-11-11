// 仅供页面 setup 函数使用
import { ref } from 'vue'
import { getUserInfo, setToken, setUserInfo, removeToken, removeUserInfo } from './auth'

const userInfo = ref(getUserInfo()) // 响应式对象，可以随时更新最新的值

// 退出登录：清空token、用户信息
// 单独导出，方便请求拦截器等非组件环境直接调用（useUser 内部也复用这个函数）
export function logout() {
  removeToken()
  removeUserInfo()
  userInfo.value = null
}

export function useUser() {
  // 登录成功后调用：保存token、用户信息，更新全局响应式userInfo
  function saveLoginData(data) {
    setToken(data.token)
    setUserInfo(data.user)
    userInfo.value = data.user
  }

  // 修改个人资料后调用：更新用户信息
  function updateUser(user) {
    setUserInfo(user)
    userInfo.value = user
  }

  // 重新从localStorage加载用户信息
  function reloadUser() {
    userInfo.value = getUserInfo()
  }

  return {
    userInfo,
    saveLoginData,
    updateUser,
    reloadUser,
    logout
  }
}

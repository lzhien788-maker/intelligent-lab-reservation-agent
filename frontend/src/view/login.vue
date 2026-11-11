<template>
  <div class="login-page">
    <div class="login-shell">
      <!-- 左侧：品牌介绍 -->
      <section class="brand">
        <div class="brand-glow brand-glow-1" />
        <div class="brand-glow brand-glow-2" />

        <div class="brand-top">
          <div class="brand-logo">
            <img src="@/assets/imgs/logo.png" alt="logo" />
          </div>
          <div class="brand-meta">
            <div class="brand-name">智能实验室预约系统</div>
            <div class="brand-tech">FastAPI · Vue3 · LangGraph Agent</div>
          </div>
        </div>

        <h1 class="brand-title">让实验室预约<br />像聊天一样简单</h1>
        <p class="brand-desc">
          一站式管理实验室、设备与预约审核，内置 AI 助手，用一句话完成查询、预约与审核跟踪。
        </p>

        <ul class="brand-features">
          <li>
            <span class="icon"><el-icon><Calendar /></el-icon></span>
            <span class="text">实验室与设备预约，时段冲突自动校验</span>
          </li>
          <li>
            <span class="icon"><el-icon><MagicStick /></el-icon></span>
            <span class="text">AI 智能助手，流式对话 + 工具调用</span>
          </li>
          <li>
            <span class="icon"><el-icon><CircleCheck /></el-icon></span>
            <span class="text">预约在线审核，待审核 / 通过 / 拒绝全程留痕</span>
          </li>
        </ul>

        <div class="brand-foot">智能实验室预约系统 · 教学实战项目</div>
      </section>

      <!-- 右侧：登录表单 -->
      <section class="panel">
        <div class="panel-head">
          <h2>欢迎回来</h2>
          <p>登录后即可管理实验室与预约</p>
        </div>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-width="0"
          class="login-form"
          @keyup.enter="handleLogin"
        >
          <el-form-item prop="username">
            <el-input
              v-model="form.username"
              size="large"
              placeholder="请输入账号"
              :prefix-icon="User"
              clearable
            />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              size="large"
              placeholder="请输入密码"
              :prefix-icon="Lock"
              show-password
            />
          </el-form-item>

          <el-button
            class="login-btn"
            size="large"
            type="primary"
            :loading="loading"
            @click="handleLogin"
          >
            登 录
          </el-button>
        </el-form>

        <div class="panel-foot">
          还没有账号？
          <router-link class="link" to="/register">立即注册</router-link>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { User, Lock, Calendar, MagicStick, CircleCheck } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { useUser } from '@/utils/user'
import { loginApi } from '@/api/auth'

const { saveLoginData } = useUser()

const formRef = ref()
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [
    { required: true, message: '请输入账号', trigger: 'blur' },
    { min: 3, max: 20, message: '账号长度需在 3 到 20 个字符之间', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '账号只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度需在 6 到 20 个字符之间', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!formRef.value) return

  // 表单校验不通过直接返回，错误提示由 el-form 自己显示
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  loading.value = true
  try {
    const res = await loginApi({
      username: form.username,
      password: form.password
    })
    saveLoginData(res.data)
    ElMessage.success('登录成功')
    await router.push('/manager/home')
  } catch (err) {
    // 业务错误（账号或密码错误等）已在请求拦截器里统一弹出，这里不用重复提示
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 24px;
  background:
    radial-gradient(1000px 600px at 8% 10%, #e8f1fb 0%, rgba(232, 241, 251, 0) 60%),
    radial-gradient(900px 500px at 92% 90%, #e6f4f2 0%, rgba(230, 244, 242, 0) 60%),
    #f2f5f9;
}

.login-shell {
  width: 100%;
  max-width: 1000px;
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  background-color: #fff;
  border-radius: 20px;
  overflow: hidden;
  box-shadow:
    0 30px 70px rgba(15, 45, 70, 0.14),
    0 2px 6px rgba(15, 45, 70, 0.06);
}

/* ---------- 左侧品牌 ---------- */
.brand {
  position: relative;
  overflow: hidden;
  padding: 48px 44px;
  color: #fff;
  background:
    linear-gradient(160deg, #0a2c47 0%, #10527a 48%, #117d95 100%);
  display: flex;
  flex-direction: column;
}

/* 装饰光斑 */
.brand-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(10px);
  pointer-events: none;
}

.brand-glow-1 {
  width: 320px;
  height: 320px;
  right: -110px;
  top: -90px;
  background: radial-gradient(circle, rgba(90, 210, 214, 0.35), rgba(90, 210, 214, 0));
}

.brand-glow-2 {
  width: 260px;
  height: 260px;
  left: -90px;
  bottom: -80px;
  background: radial-gradient(circle, rgba(90, 150, 255, 0.32), rgba(90, 150, 255, 0));
}

.brand-top {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-logo {
  width: 46px;
  height: 46px;
  flex-shrink: 0;
  border-radius: 12px;
  background-color: rgba(255, 255, 255, 0.92);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.16);
}

.brand-logo img {
  width: 26px;
  height: 26px;
  object-fit: contain;
}

.brand-name {
  font-size: 17px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.brand-tech {
  margin-top: 4px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.62);
  letter-spacing: 0.4px;
}

.brand-title {
  position: relative;
  margin-top: 44px;
  font-size: 32px;
  line-height: 1.35;
  font-weight: 700;
  letter-spacing: 1px;
}

.brand-desc {
  position: relative;
  margin-top: 16px;
  font-size: 13px;
  line-height: 1.9;
  color: rgba(255, 255, 255, 0.72);
  max-width: 380px;
}

.brand-features {
  position: relative;
  margin-top: 34px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.brand-features li {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.86);
}

.brand-features .icon {
  width: 26px;
  height: 26px;
  flex-shrink: 0;
  border-radius: 8px;
  background-color: rgba(255, 255, 255, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: #8fe3e0;
}

.brand-foot {
  position: relative;
  margin-top: auto;
  padding-top: 36px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  letter-spacing: 0.5px;
}

/* ---------- 右侧登录 ---------- */
.panel {
  padding: 54px 52px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.panel-head h2 {
  font-size: 24px;
  font-weight: 600;
  color: #1f2d3d;
}

.panel-head p {
  margin-top: 8px;
  font-size: 13px;
  color: #9aa4b2;
}

.login-form {
  margin-top: 30px;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 22px;
}

.login-form :deep(.el-input__wrapper) {
  height: 46px;
  border-radius: 10px;
  background-color: #f7f9fc;
  box-shadow: 0 0 0 1px #e6ebf2 inset;
  transition: all 0.2s ease;
}

.login-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #c8d6e6 inset;
}

.login-form :deep(.el-input__wrapper.is-focus) {
  background-color: #fff;
  box-shadow: 0 0 0 1px #2f8ee0 inset, 0 0 0 4px rgba(47, 142, 224, 0.12);
}

.login-form :deep(.el-input__inner) {
  font-size: 14px;
}

.login-btn {
  width: 100%;
  height: 46px;
  margin-top: 6px;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  letter-spacing: 4px;
  font-weight: 500;
  background-image: linear-gradient(96deg, #1677d9 0%, #2296ef 100%);
  box-shadow: 0 10px 22px rgba(34, 150, 239, 0.28);
  transition: transform 0.18s ease, box-shadow 0.18s ease, opacity 0.18s ease;
}

.login-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 26px rgba(34, 150, 239, 0.34);
  opacity: 0.96;
}

.login-btn:active {
  transform: translateY(0);
}

.panel-foot {
  margin-top: 24px;
  text-align: center;
  font-size: 13px;
  color: #9aa4b2;
}

.panel-foot .link {
  margin-left: 4px;
  color: #1677d9;
  font-weight: 500;
}

.panel-foot .link:hover {
  text-decoration: underline;
}

/* 窄屏：只留登录卡 */
@media (max-width: 900px) {
  .login-shell {
    grid-template-columns: 1fr;
    max-width: 420px;
  }

  .brand {
    display: none;
  }

  .panel {
    padding: 40px 28px;
  }
}
</style>

<template>
  <div class="home">
    <!-- 1. 欢迎卡片 -->
    <el-card shadow="never" class="welcome-card">
      <div class="welcome-row">
        <div class="welcome-text">
          <div class="welcome-title">欢迎您：{{ displayName }}</div>
          <div class="welcome-sub">
            欢迎使用实验室预约系统，当前身份：{{ roleText }}
          </div>
        </div>
        <el-button type="primary" @click="go('/manager/ai-chat')">
          <el-icon style="margin-right: 4px"><MagicStick /></el-icon>
          打开AI助手
        </el-button>
      </div>
    </el-card>

    <!-- 2. 数据概览 -->
    <el-card shadow="never" class="stat-card">
      <div class="stat-row" v-loading="loading">
        <div class="stat-item">
          <div class="stat-label">开放的实验室</div>
          <div class="stat-value">{{ openLabCount }}</div>
        </div>
        <div class="stat-divider" />
        <div class="stat-item">
          <div class="stat-label">与我相关的预约</div>
          <div class="stat-value">{{ myReservationCount }}</div>
        </div>
      </div>
    </el-card>

    <!-- 3. 快捷入口 -->
    <el-card shadow="never" class="quick-card">
      <div class="card-title">快捷入口</div>
      <div class="quick-links">
        <el-button
          v-for="item in quickLinks"
          :key="item.path"
          link
          type="primary"
          @click="go(item.path)"
        >
          {{ item.label }}
        </el-button>
      </div>
    </el-card>

    <!-- 4. 系统可以做什么 -->
    <div class="section-title">系统可以做什么</div>
    <el-row :gutter="16">
      <el-col v-for="item in features" :key="item.title" :xs="24" :sm="8">
        <el-card shadow="never" class="feature-card">
          <div class="feature-title">{{ item.title }}</div>
          <div class="feature-desc">{{ item.desc }}</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import router from '@/router'
import { MagicStick } from '@element-plus/icons-vue'
import { useUser } from '@/utils/user'
import { getLabListApi } from '@/api/lab'
import { getReservationListApi } from '@/api/reservation'

const { userInfo } = useUser()

const displayName = computed(
  () => userInfo.value?.name || userInfo.value?.username || '同学'
)
const isAdmin = computed(() => userInfo.value?.role === 'admin')
const roleText = computed(() => (isAdmin.value ? '管理员' : '学生'))

const openLabCount = ref(0)
const myReservationCount = ref(0)
const loading = ref(false)

// 快捷入口：管理员看到管理类，学生看到查询/预约类
const quickLinks = computed(() =>
  isAdmin.value
    ? [
        { label: '预约审核', path: '/manager/reservation' },
        { label: '实验室管理', path: '/manager/lab' },
        { label: '设备列表管理', path: '/manager/equ' },
        { label: '用户管理', path: '/manager/user' }
      ]
    : [
        { label: '实验室列表', path: '/manager/labs' },
        { label: '实验室预约', path: '/manager/booking' },
        { label: '我的预约', path: '/manager/my-reservation' },
        { label: 'AI智能助手', path: '/manager/ai-chat' }
      ]
)

const features = [
  {
    title: '业务预约',
    desc: '实验室与设备浏览、提交预约、我的预约与管理员审核，全流程闭环'
  },
  {
    title: '知识库问答',
    desc: 'RAG 检索规程和开放时间等文档，回答有依据，不凭空编造'
  },
  {
    title: '智能 Agent',
    desc: '根据用户的自然语言主动进行 Tool Call 和节点编排循环，可查库、流式对话、确认后提交表单'
  }
]

const go = (path) => router.push(path)

// 只取总数，所以 page_size 传 1，省流量
const loadStats = async () => {
  loading.value = true
  try {
    const [labRes, reserveRes] = await Promise.all([
      getLabListApi({ page: 1, page_size: 1, status: 1 }),
      // 学生默认只看自己的；管理员显式 only_mine=true 也只看自己的
      getReservationListApi({ page: 1, page_size: 1, only_mine: true })
    ])
    openLabCount.value = labRes?.data?.total ?? 0
    myReservationCount.value = reserveRes?.data?.total ?? 0
  } catch {
    // 拦截器已经弹过提示，这里保持默认 0
  } finally {
    loading.value = false
  }
}

onMounted(loadStats)
</script>

<style scoped>
.home {
  padding-bottom: 20px;
}

.welcome-card {
  margin-bottom: 16px;
}

.welcome-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.welcome-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.welcome-sub {
  margin-top: 6px;
  font-size: 13px;
  color: #909399;
}

.stat-card {
  margin-bottom: 16px;
}

.stat-row {
  display: flex;
  align-items: center;
  min-height: 64px;
}

.stat-item {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: #409eff;
  line-height: 1;
}

.stat-divider {
  width: 1px;
  height: 40px;
  background-color: #ebeef5;
  margin: 0 24px;
  flex-shrink: 0;
}

.quick-card {
  margin-bottom: 20px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.quick-links {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 18px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 12px 2px;
}

.feature-card {
  height: 100%;
  min-height: 96px;
}

.feature-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.feature-desc {
  font-size: 13px;
  color: #909399;
  line-height: 1.7;
}
</style>

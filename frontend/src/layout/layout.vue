<template>
  <div class="common-layout">
    <el-container style="min-height: 100vh">
      <el-header
        style="
          display: flex;
          align-items: center;
          border-bottom: 1px solid #ddd;
          background-color: #fff;
        "
      >
        <div
          style="flex: 1; display: flex; align-items: center; font-size: 24px; font-weight: bold"
        >
          <img style="width: 40px" src="@/assets/imgs/logo.png" alt="" />
          <div style="margin-left: 5px">智能实验室预约系统</div>
        </div>
        <div>
          <el-dropdown @command="handleCommand">
            <div style="display: flex; align-items: center; cursor: pointer">
              <img
                :src="avatarSrc"
                style="width: 30px; height: 30px; border-radius: 50%; object-fit: cover"
                alt=""
              />
              <div style="margin-left: 6px">{{ displayName }}</div>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人信息</el-dropdown-item>
                <el-dropdown-item command="password">修改密码</el-dropdown-item>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-container>
        <el-aside width="220px">
          <el-menu style="height: 100%" router :default-active="$route.path">
            <el-menu-item index="/manager/home">
              <el-icon><House /></el-icon>
              <span>系统首页</span>
            </el-menu-item>

            <el-menu-item index="/manager/ai-chat">
              <el-icon><MagicStick /></el-icon>
              <span>AI智能助手</span>
            </el-menu-item>

            <!-- 学生端只读页面：所有登录用户可见 -->
            <el-menu-item index="/manager/labs">
              <el-icon><Reading /></el-icon>
              <span>实验室列表</span>
            </el-menu-item>

            <el-menu-item index="/manager/booking">
              <el-icon><Calendar /></el-icon>
              <span>实验室预约</span>
            </el-menu-item>

            <el-menu-item index="/manager/my-reservation">
              <el-icon><Clock /></el-icon>
              <span>我的预约</span>
            </el-menu-item>

            <!-- 管理员功能 -->
            <el-menu-item v-if="isAdmin" index="/manager/lab">
              <el-icon><Document /></el-icon>
              <span>实验室管理</span>
            </el-menu-item>

            <el-menu-item v-if="isAdmin" index="/manager/equ">
              <el-icon><Notification /></el-icon>
              <span>设备列表管理</span>
            </el-menu-item>

            <el-menu-item v-if="isAdmin" index="/manager/user">
              <el-icon><User /></el-icon>
              <span>用户管理</span>
            </el-menu-item>

            <el-menu-item v-if="isAdmin" index="/manager/reservation">
              <el-icon><Tickets /></el-icon>
              <span>预约审核</span>
            </el-menu-item>
          </el-menu>
        </el-aside>

        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import router from '@/router'
import { useUser } from '@/utils/user'
import { getFileUrl } from '@/utils/file'
import { House, Document, Notification, User, Reading, Calendar, Tickets, Clock, MagicStick } from '@element-plus/icons-vue'
import defaultAvatar from '@/assets/imgs/logo.png'

const { userInfo, logout } = useUser()

// 顶部显示的用户名：优先姓名，其次账号
const displayName = computed(() => userInfo.value?.name || userInfo.value?.username || '未登录')

// 只有管理员才显示用户管理入口
const isAdmin = computed(() => userInfo.value?.role === 'admin')

// 头像：有头像用上传的，没有就回退到默认 logo
const avatarSrc = computed(() =>
  userInfo.value?.avatar ? getFileUrl(userInfo.value.avatar) : defaultAvatar
)

const handleCommand = (command) => {
  if (command === 'profile') {
    router.push('/manager/profile')
  } else if (command === 'password') {
    router.push('/manager/password')
  } else if (command === 'logout') {
    logout()
    router.push('/login')
  }
}
</script>

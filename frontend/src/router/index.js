import { createRouter, createWebHistory } from 'vue-router'
import { getToken, getUserInfo } from '@/utils/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),

  routes: [
    { path: '/', redirect: '/manager/home' },
    {
      path: '/manager',
      name: 'Layout',
      component: () => import('@/layout/layout.vue'),
      children: [
        { path: 'home', name: 'Home', component: () => import('@/view/Home.vue') },
        // AI 智能助手：所有登录用户都能用
        { path: 'ai-chat', name: 'AiChat', component: () => import('@/view/AiChat.vue') },
        // 学生端只读：实验室列表、某个实验室的设备列表
        { path: 'labs', name: 'Labs', component: () => import('@/view/Labs.vue') },
        {
          path: 'lab-equipment',
          name: 'LabEquipment',
          component: () => import('@/view/LabEquipment.vue')
        },
        // 预约实验室（所有登录用户可用，学生提交预约）
        {
          path: 'booking',
          name: 'Booking',
          component: () => import('@/view/Booking.vue')
        },
        // 我的预约：只看自己的预约，可取消
        {
          path: 'my-reservation',
          name: 'MyReservation',
          component: () => import('@/view/MyReservation.vue')
        },
        // 预约审核（管理员）：看全部预约并通过/拒绝
        {
          path: 'reservation',
          name: 'Reservation',
          component: () => import('@/view/Reservation.vue'),
          meta: { requiresAdmin: true }
        },
        // 以下为管理员功能
        {
          path: 'lab',
          name: 'Lab',
          component: () => import('@/view/lab.vue'),
          meta: { requiresAdmin: true }
        },
        {
          path: 'equ',
          name: 'Equipment',
          component: () => import('@/view/equipment.vue'),
          meta: { requiresAdmin: true }
        },
        { path: 'profile', name: 'Profile', component: () => import('@/view/profile.vue') },
        { path: 'password', name: 'password', component: () => import('@/view/password.vue') },
        {
          path: 'user',
          name: 'User',
          component: () => import('@/view/User.vue'),
          meta: { requiresAdmin: true }
        }
      ]
    },
    { path: '/login', name: 'Login', component: () => import('@/view/login.vue') },
    { path: '/register', name: 'register', component: () => import('@/view/register.vue') }
  ]
})

// 路由守卫：验证 token，并拦截非管理员访问管理员页面
router.beforeEach((to) => {
  const token = getToken()
  if (to.path === '/login' || to.path === '/register') {
    return true
  }
  if (!token) {
    return '/login'
  }
  // 学生直接输入管理员页面也进不去，统一回到首页
  if (to.meta.requiresAdmin && getUserInfo()?.role !== 'admin') {
    return '/manager/home'
  }
  return true
})

export default router

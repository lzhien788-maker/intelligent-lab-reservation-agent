<template>
  <el-card>
    <template #header>
      <span>个人信息</span>
    </template>

    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="90px"
      style="max-width: 560px"
    >
      <el-form-item label="头像">
        <div>
          <el-upload
            class="avatar-uploader"
            action="#"
            :show-file-list="false"
            accept="image/*"
            :before-upload="beforeAvatarUpload"
            :http-request="handleAvatarUpload"
          >
            <img v-if="form.avatar" :src="getFileUrl(form.avatar)" class="avatar" alt="" />
            <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
          </el-upload>
          <div class="upload-tip">点击更换头像，支持 jpg / png / gif / webp</div>
        </div>
      </el-form-item>

      <el-form-item label="账号">
        <el-input v-model="form.username" disabled />
      </el-form-item>

      <el-form-item label="姓名" prop="name">
        <el-input v-model="form.name" placeholder="请输入姓名" clearable />
      </el-form-item>

      <el-form-item label="邮箱" prop="email">
        <el-input v-model="form.email" placeholder="请输入邮箱" clearable />
      </el-form-item>

      <el-form-item label="手机号" prop="phone">
        <el-input v-model="form.phone" placeholder="请输入手机号" clearable maxlength="11" />
      </el-form-item>

      <el-form-item label="角色">
        <el-tag :type="form.role === 'admin' ? 'danger' : 'success'">
          {{ form.role === 'admin' ? '管理员' : '学生' }}
        </el-tag>
      </el-form-item>

      <el-form-item>
        <el-button type="primary" :loading="saving" :disabled="uploading" @click="handleSave">
          保存修改
        </el-button>
        <el-button @click="loadInfo">重置</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getUserInfoApi, updateUserInfoApi } from '@/api/user'
import { uploadFileApi } from '@/api/files'
import { getFileUrl } from '@/utils/file'
import { useUser } from '@/utils/user'

const { updateUser } = useUser()

const formRef = ref()
const saving = ref(false)
const uploading = ref(false)

const form = reactive({
  username: '',
  name: '',
  email: '',
  phone: '',
  avatar: '',
  role: ''
})

const rules = {
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { max: 50, message: '姓名不能超过 50 个字符', trigger: 'blur' }
  ],
  email: [{ type: 'email', message: '邮箱格式不正确', trigger: 'blur' }],
  phone: [{ pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }]
}

// 查询当前登录用户信息，填充表单
const loadInfo = async () => {
  try {
    const res = await getUserInfoApi()
    const data = res.data || {}
    form.username = data.username || ''
    form.name = data.name || ''
    form.email = data.email || ''
    form.phone = data.phone || ''
    form.avatar = data.avatar || ''
    form.role = data.role || ''
  } catch (err) {
    // 业务错误已在请求拦截器统一提示
  }
}

// 上传前校验：只允许图片，大小不超过 100MB
const beforeAvatarUpload = (file) => {
  const isImage = /^image\/(png|jpe?g|gif|webp)$/i.test(file.type)
  if (!isImage) {
    ElMessage.error('只能上传 jpg / png / gif / webp 格式的图片')
    return false
  }
  if (file.size > 100 * 1024 * 1024) {
    ElMessage.error('图片不能超过 100MB')
    return false
  }
  return true
}

// 自定义上传：走项目统一的 axios 实例，自动带上 token
const handleAvatarUpload = async (options) => {
  uploading.value = true
  try {
    const res = await uploadFileApi(options.file)
    form.avatar = res.data.url
    ElMessage.success('头像已上传，记得点保存')
  } catch (err) {
    // 业务错误已在请求拦截器统一提示
  } finally {
    uploading.value = false
  }
}

const handleSave = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  saving.value = true
  try {
    const res = await updateUserInfoApi({
      name: form.name,
      // 清空时传 null，让后端把字段置空
      email: form.email || null,
      phone: form.phone || null,
      avatar: form.avatar || null
    })
    // 同步刷新 localStorage 和全局响应式用户信息，顶部昵称/头像会立即变化
    updateUser(res.data)
    ElMessage.success('修改成功')
  } catch (err) {
    // 业务错误已在请求拦截器统一提示
  } finally {
    saving.value = false
  }
}

onMounted(loadInfo)
</script>

<style scoped>
.avatar-uploader {
  width: 100px;
  height: 100px;
  border: 1px dashed var(--el-border-color);
  border-radius: 50%;
  cursor: pointer;
  overflow: hidden;
  transition: border-color 0.2s;
}
.avatar-uploader:hover {
  border-color: var(--el-color-primary);
}
.avatar {
  width: 100px;
  height: 100px;
  object-fit: cover;
  display: block;
}
.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 100px;
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.upload-tip {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
}
</style>

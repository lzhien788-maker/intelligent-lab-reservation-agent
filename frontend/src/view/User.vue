<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>用户管理</span>
        <el-button type="primary" @click="openCreate">
          <el-icon><Plus /></el-icon>
          新增用户
        </el-button>
      </div>
    </template>

    <!-- 搜索栏 -->
    <div class="toolbar">
      <el-input
        v-model="searchForm.username"
        placeholder="请输入账号或名称查询"
        style="width: 240px"
        clearable
        @keyup.enter="handleSearch"
        @clear="handleSearch"
      />
      <el-button type="primary" @click="handleSearch">查询</el-button>
      <el-button @click="handleReset">重置</el-button>
    </div>

    <!-- 用户表格 -->
    <el-table :data="tableData" v-loading="loading" stripe>
      <el-table-column prop="username" label="账号" min-width="120" />
      <el-table-column prop="name" label="名称" min-width="120" />
      <el-table-column prop="avatar" label="头像" width="90">
        <template #default="{ row }">
          <el-avatar v-if="row.avatar" :src="getFileUrl(row.avatar)" :size="40" />
          <el-avatar v-else :size="40" :icon="UserFilled" />
        </template>
      </el-table-column>
      <el-table-column prop="email" label="邮箱" min-width="180" />
      <el-table-column prop="phone" label="手机号" min-width="130" />
      <el-table-column prop="role" label="角色" width="100">
        <template #default="{ row }">
          <el-tag :type="row.role === 'admin' ? 'danger' : 'success'" size="small">
            {{ row.role === 'admin' ? '管理员' : '学生' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="isEnabled(row.status) ? 'success' : 'danger'" size="small">
            {{ isEnabled(row.status) ? '正常' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-tooltip
            :disabled="!isSelf(row)"
            content="不能删除当前登录账号"
            placement="top"
          >
            <span>
              <el-button
                link
                type="danger"
                :disabled="isSelf(row)"
                @click="handleDelete(row)"
              >
                删除
              </el-button>
            </span>
          </el-tooltip>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination">
      <span>共 {{ total }} 条</span>
      <el-pagination
        v-model:current-page="query.page"
        :page-size="query.page_size"
        :total="total"
        layout="prev, pager, next"
        @current-change="loadData"
      />
    </div>

    <!-- 新增 / 编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑用户' : '新增用户'"
      width="520px"
      destroy-on-close
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="账号" prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入账号"
            maxlength="20"
            :disabled="isEdit"
            clearable
          />
        </el-form-item>

        <el-form-item label="头像" prop="avatar">
          <el-upload
            class="avatar-uploader"
            :show-file-list="false"
            :http-request="handleAvatarUpload"
            accept="image/*"
          >
            <img v-if="form.avatar" :src="getFileUrl(form.avatar)" class="avatar-preview" />
            <div v-else class="avatar-placeholder">
              <el-icon><Plus /></el-icon>
            </div>
          </el-upload>
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            maxlength="20"
            :placeholder="isEdit ? '留空则不修改密码' : '请输入 6-20 位密码'"
            clearable
          />
        </el-form-item>

        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="请输入姓名" maxlength="50" clearable />
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" maxlength="50" clearable />
        </el-form-item>

        <el-form-item label="手机号" prop="phone">
          <el-input
            v-model="form.phone"
            placeholder="请输入手机号"
            maxlength="11"
            clearable
          />
        </el-form-item>

        <el-form-item label="角色" prop="role">
          <el-select
            v-model="form.role"
            placeholder="请选择角色"
            style="width: 100%"
            :disabled="editingSelf"
          >
            <el-option label="学生" value="student" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>

        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="form.status" :disabled="editingSelf">
            <el-radio :value="1">正常</el-radio>
            <el-radio :value="0">禁用</el-radio>
          </el-radio-group>
          <div v-if="editingSelf" class="form-tip">不能禁用或降级当前登录账号</div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit">
          {{ isEdit ? '保存' : '新增' }}
        </el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, UserFilled } from '@element-plus/icons-vue'
import {
  createUserApi,
  deleteUserApi,
  getUserListApi,
  updateUserApi
} from '@/api/user'
import { uploadFileApi } from '@/api/files'
import { getFileUrl } from '@/utils/file'
import { useUser } from '@/utils/user'

const { userInfo, updateUser } = useUser()

const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const tableData = ref([])
const total = ref(0)
const formRef = ref()

const searchForm = reactive({
  username: ''
})

const query = reactive({
  page: 1,
  page_size: 10
})

const createDefaultForm = () => ({
  id: null,
  username: '',
  password: '',
  name: '',
  avatar: '',
  email: '',
  phone: '',
  role: 'student',
  status: 1
})

const form = reactive(createDefaultForm())

const validatePassword = (_rule, value, callback) => {
  if (!isEdit.value && !value) {
    callback(new Error('请输入密码'))
    return
  }
  if (value && (value.length < 6 || value.length > 20)) {
    callback(new Error('密码长度需为 6-20 位'))
    return
  }
  callback()
}

const validateEmail = (_rule, value, callback) => {
  if (!value) {
    callback()
    return
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
    callback(new Error('邮箱格式不正确'))
    return
  }
  callback()
}

const validatePhone = (_rule, value, callback) => {
  if (!value) {
    callback()
    return
  }
  if (!/^1[3-9]\d{9}$/.test(value)) {
    callback(new Error('请输入正确的手机号'))
    return
  }
  callback()
}

const rules = {
  username: [
    { required: true, message: '请输入账号', trigger: 'blur' },
    { min: 3, max: 20, message: '账号长度需为 3-20 位', trigger: 'blur' }
  ],
  password: [{ validator: validatePassword, trigger: 'blur' }],
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { max: 50, message: '姓名不能超过 50 个字符', trigger: 'blur' }
  ],
  email: [{ validator: validateEmail, trigger: 'blur' }],
  phone: [{ validator: validatePhone, trigger: 'blur' }]
}

const isEnabled = (status) => String(status) === '1'

const isSelf = (row) => Number(userInfo.value?.id) === Number(row.id)

// 编辑自己时不允许在页面上把自己禁用或降级，后端也有同样的保护
const editingSelf = computed(
  () => isEdit.value && Number(form.id) === Number(userInfo.value?.id)
)

const loadData = async () => {
  loading.value = true
  try {
    const res = await getUserListApi({
      page: query.page,
      page_size: query.page_size,
      keywords: searchForm.username || undefined
    })
    tableData.value = res.data?.list || []
    total.value = res.data?.total || 0
  } catch (err) {
    // 错误已在拦截器统一提示
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  query.page = 1
  loadData()
}

const handleReset = () => {
  searchForm.username = ''
  query.page = 1
  loadData()
}

const openCreate = () => {
  isEdit.value = false
  Object.assign(form, createDefaultForm())
  dialogVisible.value = true
  nextTick(() => formRef.value?.clearValidate())
}

const openEdit = (row) => {
  isEdit.value = true
  Object.assign(form, {
    id: row.id,
    username: row.username || '',
    password: '',
    name: row.name || '',
    avatar: row.avatar || '',
    email: row.email || '',
    phone: row.phone || '',
    role: row.role || 'student',
    status: isEnabled(row.status) ? 1 : 0
  })
  dialogVisible.value = true
  nextTick(() => formRef.value?.clearValidate())
}

const resetForm = () => {
  Object.assign(form, createDefaultForm())
  formRef.value?.clearValidate()
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  const editing = isEdit.value
  saving.value = true
  try {
    const payload = {
      name: form.name.trim(),
      avatar: form.avatar || null,
      email: form.email.trim() || null,
      phone: form.phone.trim() || null,
      role: form.role,
      status: Number(form.status)
    }

    if (editing) {
      if (form.password) {
        payload.password = form.password
      }
      const res = await updateUserApi(form.id, payload)
      // 编辑的是当前登录账号时，同步顶部昵称/头像
      if (Number(form.id) === Number(userInfo.value?.id)) {
        updateUser(res.data)
      }
      ElMessage.success('修改成功')
    } else {
      payload.username = form.username.trim()
      payload.password = form.password
      await createUserApi(payload)
      ElMessage.success('新增成功')
      query.page = 1
    }

    dialogVisible.value = false
    await loadData()
  } catch (err) {
    // 错误已在拦截器统一提示
  } finally {
    saving.value = false
  }
}

// 头像上传
const handleAvatarUpload = async (options) => {
  try {
    const res = await uploadFileApi(options.file)
    form.avatar = res.data?.url || ''
    ElMessage.success('头像上传成功')
  } catch (err) {
    // 错误已在拦截器统一提示
  }
}

const handleDelete = async (row) => {
  if (isSelf(row)) return

  try {
    await ElMessageBox.confirm(
      `确定删除用户“${row.username}”吗？删除后不可恢复。`,
      '删除确认',
      {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        confirmButtonClass: 'el-button--danger'
      }
    )
  } catch {
    return
  }

  try {
    await deleteUserApi(row.id)
    ElMessage.success('删除成功')
    if (tableData.value.length === 1 && query.page > 1) {
      query.page -= 1
    }
    await loadData()
  } catch (err) {
    // 错误已在拦截器统一提示
  }
}

onMounted(loadData)
</script>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 20px;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 16px;
}

.form-tip {
  width: 100%;
  margin-top: 4px;
  font-size: 12px;
  line-height: 1.5;
  color: #909399;
}

.avatar-uploader :deep(.el-upload) {
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  overflow: hidden;
  transition: border-color 0.2s;
}

.avatar-uploader :deep(.el-upload:hover) {
  border-color: #409eff;
}

.avatar-preview {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
  display: block;
}

.avatar-placeholder {
  width: 80px;
  height: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #8c939d;
  font-size: 14px;
}
</style>

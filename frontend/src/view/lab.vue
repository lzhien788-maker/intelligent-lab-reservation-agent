<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>实验室管理</span>
        <el-button type="primary" @click="openCreate">
          <el-icon><Plus /></el-icon>
          新增实验室
        </el-button>
      </div>
    </template>

    <!-- 搜索栏 -->
    <div class="toolbar">
      <el-input
        v-model="searchForm.keyword"
        placeholder="请输入实验室名称查询"
        style="width: 240px"
        clearable
        @keyup.enter="handleSearch"
        @clear="handleSearch"
      />
      <el-button type="primary" @click="handleSearch">查询</el-button>
      <el-button @click="handleReset">重置</el-button>
    </div>

    <!-- 实验室表格 -->
    <el-table :data="tableData" v-loading="loading" stripe>
      <el-table-column prop="name" label="实验室名称" min-width="140" />
      <el-table-column prop="img" label="封面" width="90">
        <template #default="{ row }">
          <el-image
            v-if="row.img"
            :src="getFileUrl(row.img)"
            :preview-src-list="[getFileUrl(row.img)]"
            fit="cover"
            style="width: 50px; height: 50px; border-radius: 4px"
          />
          <el-image
            v-else
            :src="defaultLabImg"
            fit="cover"
            style="width: 50px; height: 50px; border-radius: 4px; background: #f5f5f5"
          />
        </template>
      </el-table-column>
      <el-table-column prop="location" label="位置" min-width="120" />
      <el-table-column prop="capacity" label="容量" width="80" />
      <el-table-column prop="open_time" label="开放时间" width="100" />
      <el-table-column prop="close_time" label="关闭时间" width="100" />
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="isOpen(row.status) ? 'success' : 'danger'" size="small">
            {{ isOpen(row.status) ? '开放' : '关闭' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
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
      :title="isEdit ? '编辑实验室' : '新增实验室'"
      width="560px"
      destroy-on-close
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="实验室名称" prop="name">
          <el-input
            v-model="form.name"
            placeholder="请输入实验室名称"
            maxlength="50"
            clearable
          />
        </el-form-item>

        <el-form-item label="简介" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入实验室简介"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="封面图片" prop="img">
          <el-upload
            class="avatar-uploader"
            :show-file-list="false"
            :http-request="handleUpload"
            accept="image/*"
          >
            <img v-if="form.img" :src="getFileUrl(form.img)" class="avatar-preview" />
            <div v-else class="avatar-placeholder">
              <el-icon><Plus /></el-icon>
            </div>
          </el-upload>
        </el-form-item>

        <el-form-item label="位置" prop="location">
          <el-input
            v-model="form.location"
            placeholder="请输入实验室位置，如：实训楼301"
            maxlength="100"
            clearable
          />
        </el-form-item>

        <el-form-item label="容量" prop="capacity">
          <el-input-number
            v-model="form.capacity"
            :min="1"
            :max="999"
            placeholder="容纳人数"
          />
        </el-form-item>

        <el-form-item label="开放时间" prop="open_time">
          <el-time-picker
            v-model="form.open_time"
            format="HH:mm"
            value-format="HH:mm"
            placeholder="选择开放时间"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="关闭时间" prop="close_time">
          <el-time-picker
            v-model="form.close_time"
            format="HH:mm"
            value-format="HH:mm"
            placeholder="选择关闭时间"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">开放</el-radio>
            <el-radio :value="0">关闭</el-radio>
          </el-radio-group>
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
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getLabListApi,
  createLabApi,
  updateLabApi,
  deleteLabApi
} from '@/api/lab'
import { uploadFileApi } from '@/api/files'
import { getFileUrl } from '@/utils/file'

// 默认实验室占位图（计算机实验室内部）
const defaultLabImg = 'https://aka.doubaocdn.com/l/ylxQpRYj0w'

const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const tableData = ref([])
const total = ref(0)
const formRef = ref()

const searchForm = reactive({
  keyword: ''
})

const query = reactive({
  page: 1,
  page_size: 10
})

const createDefaultForm = () => ({
  id: null,
  name: '',
  description: '',
  img: '',
  location: '',
  capacity: 30,
  open_time: '',
  close_time: '',
  status: 1
})

const form = reactive(createDefaultForm())

const rules = {
  name: [
    { required: true, message: '请输入实验室名称', trigger: 'blur' },
    { max: 50, message: '名称不能超过 50 个字符', trigger: 'blur' }
  ],
  capacity: [
    { required: true, message: '请输入容量', trigger: 'blur' }
  ]
}

const isOpen = (status) => Number(status) === 1

const loadData = async () => {
  loading.value = true
  try {
    const res = await getLabListApi({
      page: query.page,
      page_size: query.page_size,
      keywords: searchForm.keyword || undefined
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
  searchForm.keyword = ''
  query.page = 1
  loadData()
}

const openCreate = () => {
  isEdit.value = false
  Object.assign(form, createDefaultForm())
  dialogVisible.value = true
}

const openEdit = (row) => {
  isEdit.value = true
  Object.assign(form, {
    id: row.id,
    name: row.name || '',
    description: row.description || '',
    img: row.img || '',
    location: row.location || '',
    capacity: row.capacity || 30,
    open_time: row.open_time || '',
    close_time: row.close_time || '',
    status: isOpen(row.status) ? 1 : 0
  })
  dialogVisible.value = true
}

const resetForm = () => {
  Object.assign(form, createDefaultForm())
  formRef.value?.clearValidate()
}

// 图片上传
const handleUpload = async (options) => {
  try {
    const res = await uploadFileApi(options.file)
    form.img = res.data?.url || ''
    ElMessage.success('图片上传成功')
  } catch (err) {
    // 错误已在拦截器统一提示
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  const payload = {
    name: form.name.trim(),
    description: form.description?.trim() || null,
    img: form.img || null,
    location: form.location?.trim() || null,
    capacity: Number(form.capacity),
    open_time: form.open_time || null,
    close_time: form.close_time || null,
    status: Number(form.status)
  }

  saving.value = true
  try {
    if (isEdit.value) {
      await updateLabApi(form.id, payload)
      ElMessage.success('修改成功')
    } else {
      await createLabApi(payload)
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

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定删除实验室“${row.name}”吗？删除后不可恢复。`,
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
    await deleteLabApi(row.id)
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
  width: 120px;
  height: 80px;
  object-fit: cover;
  display: block;
}

.avatar-placeholder {
  width: 120px;
  height: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #8c939d;
  font-size: 14px;
}
</style>

<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>实验室列表</span>
        <el-tag v-if="isStudent" type="success" size="small">仅展示开放的实验室</el-tag>
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

    <!-- 实验室表格（只读） -->
    <el-table :data="tableData" v-loading="loading" stripe>
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
      <el-table-column prop="name" label="实验室名称" min-width="150" />
      <el-table-column prop="location" label="位置" min-width="120">
        <template #default="{ row }">{{ row.location || '-' }}</template>
      </el-table-column>
      <el-table-column prop="capacity" label="容量" width="80">
        <template #default="{ row }">{{ row.capacity }} 人</template>
      </el-table-column>
      <el-table-column label="开放时间" width="140">
        <template #default="{ row }">
          <span v-if="row.open_time || row.close_time">
            {{ row.open_time || '--' }} ~ {{ row.close_time || '--' }}
          </span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="isOpen(row.status) ? 'success' : 'danger'" size="small">
            {{ isOpen(row.status) ? '开放' : '关闭' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="110" fixed="right">
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            :disabled="!isOpen(row.status)"
            @click="goEquipments(row)"
          >
            查看设备
          </el-button>
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
  </el-card>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getLabListApi } from '@/api/lab'
import { getFileUrl } from '@/utils/file'
import { useUser } from '@/utils/user'

// 默认实验室占位图
const defaultLabImg = 'https://aka.doubaocdn.com/l/ylxQpRYj0w'

const router = useRouter()
const { userInfo } = useUser()

const loading = ref(false)
const tableData = ref([])
const total = ref(0)

const isStudent = computed(() => userInfo.value?.role !== 'admin')

const searchForm = reactive({
  keyword: ''
})

const query = reactive({
  page: 1,
  page_size: 10
})

const isOpen = (status) => Number(status) === 1

const loadData = async () => {
  loading.value = true
  try {
    const res = await getLabListApi({
      page: query.page,
      page_size: query.page_size,
      keywords: searchForm.keyword || undefined,
      // 学生只看开放的实验室
      status: isStudent.value ? 1 : undefined
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

// 进入该实验室的设备列表
const goEquipments = (row) => {
  router.push({ path: '/manager/lab-equipment', query: { lab_id: row.id } })
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

:deep(.el-table .cell) {
  line-height: 22px;
}
</style>

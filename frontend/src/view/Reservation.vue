<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>预约审核</span>
        <el-tag type="info" size="small">管理员审核学生提交的预约</el-tag>
      </div>
    </template>

    <div class="toolbar">
      <el-select
        v-model="query.status"
        placeholder="全部状态"
        clearable
        style="width: 150px"
        @change="handleSearch"
      >
        <el-option label="待审核" :value="0" />
        <el-option label="已通过" :value="1" />
        <el-option label="已拒绝" :value="2" />
        <el-option label="已取消" :value="3" />
      </el-select>
      <el-button type="primary" @click="handleSearch">查询</el-button>
      <el-button @click="handleReset">重置</el-button>
    </div>

    <el-table :data="tableData" v-loading="loading" stripe>
      <el-table-column prop="user_name" label="预约人" width="110" />
      <el-table-column prop="lab_name" label="实验室" min-width="130" />
      <el-table-column label="设备" min-width="130">
        <template #default="{ row }">
          {{ row.equipment_name || '仅实验室' }}
        </template>
      </el-table-column>
      <el-table-column prop="reserve_date" label="预约日期" width="120" />
      <el-table-column label="时间段" width="130">
        <template #default="{ row }">{{ row.start_time }} ~ {{ row.end_time }}</template>
      </el-table-column>
      <el-table-column prop="remark" label="备注" min-width="140">
        <template #default="{ row }">{{ row.remark || '-' }}</template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)" size="small">
            {{ statusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status === 0">
            <el-button link type="success" @click="handleAudit(row, 1)">通过</el-button>
            <el-button link type="danger" @click="handleAudit(row, 2)">拒绝</el-button>
          </template>
          <span v-else class="done-tip">已处理</span>
        </template>
      </el-table-column>
    </el-table>

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
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getReservationListApi, auditReservationApi } from '@/api/reservation'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)

const query = reactive({
  page: 1,
  page_size: 10,
  status: null
})

const statusText = (status) => {
  const map = { 0: '待审核', 1: '已通过', 2: '已拒绝', 3: '已取消' }
  return map[status] || '未知'
}

const statusTagType = (status) => {
  const map = { 0: 'warning', 1: 'success', 2: 'danger', 3: 'info' }
  return map[status] || 'info'
}

const loadData = async () => {
  loading.value = true
  try {
    // 不传 only_mine，管理员拿到的是全部预约
    const res = await getReservationListApi({
      page: query.page,
      page_size: query.page_size,
      status: query.status === null || query.status === '' ? undefined : query.status
    })
    tableData.value = res.data?.list || []
    total.value = res.data?.total || 0
  } catch (err) {
    // 拦截器已提示
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  query.page = 1
  loadData()
}

const handleReset = () => {
  query.status = null
  query.page = 1
  loadData()
}

const handleAudit = async (row, status) => {
  const actionText = status === 1 ? '通过' : '拒绝'
  try {
    await ElMessageBox.confirm(
      `确定${actionText}「${row.user_name} 预约 ${row.lab_name} ${row.reserve_date} ${row.start_time}~${row.end_time}」吗？`,
      `${actionText}预约`,
      { type: 'warning', confirmButtonText: `确定${actionText}`, cancelButtonText: '取消' }
    )
  } catch (e) {
    return
  }
  try {
    const res = await auditReservationApi(row.id, status)
    ElMessage.success(res.message || '审核完成')
    loadData()
  } catch (err) {
    // 拦截器已提示
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

.done-tip {
  color: #909399;
  font-size: 13px;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 16px;
}
</style>

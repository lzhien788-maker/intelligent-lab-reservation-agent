<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>我的预约</span>
        <el-button type="primary" @click="router.push('/manager/booking')">
          去预约实验室
        </el-button>
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
      <el-table-column prop="lab_name" label="实验室" min-width="130" />
      <el-table-column label="设备" min-width="130">
        <template #default="{ row }">
          {{ row.equipment_name || '仅实验室' }}
        </template>
      </el-table-column>
      <el-table-column prop="type" label="类型" width="110">
        <template #default="{ row }">
          <el-tag :type="row.type === '设备预约' ? 'primary' : 'info'" size="small">
            {{ row.type }}
          </el-tag>
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
      <el-table-column label="操作" width="110" fixed="right">
        <template #default="{ row }">
          <el-button
            link
            type="danger"
            :disabled="row.status === 2 || row.status === 3"
            @click="handleCancel(row)"
          >
            取消预约
          </el-button>
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
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getReservationListApi, cancelReservationApi } from '@/api/reservation'

const router = useRouter()

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
    const res = await getReservationListApi({
      page: query.page,
      page_size: query.page_size,
      status: query.status === null || query.status === '' ? undefined : query.status,
      // 我的预约：管理员也只查自己的
      only_mine: true
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

const handleCancel = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要取消「${row.lab_name} ${row.reserve_date} ${row.start_time}~${row.end_time}」这条预约吗？`,
      '取消预约',
      { type: 'warning', confirmButtonText: '确定取消', cancelButtonText: '再想想' }
    )
  } catch (e) {
    return
  }
  try {
    const res = await cancelReservationApi(row.id)
    ElMessage.success(res.message || '已取消')
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

.pagination {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 16px;
}
</style>

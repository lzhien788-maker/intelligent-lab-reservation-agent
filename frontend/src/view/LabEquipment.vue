<template>
  <el-card v-loading="labLoading">
    <template #header>
      <div class="card-header">
        <div class="title">
          <el-button link type="primary" @click="goBack">
            <el-icon><ArrowLeft /></el-icon>
            返回
          </el-button>
          <span class="title-text">
            设备列表
            <el-tag v-if="labInfo" type="info" size="small">{{ labInfo.name }}</el-tag>
          </span>
        </div>
        <el-tag v-if="labInfo" :type="isOpen(labInfo.status) ? 'success' : 'danger'" size="small">
          {{ isOpen(labInfo.status) ? '开放' : '关闭' }}
        </el-tag>
      </div>
    </template>

    <!-- 实验室基本信息 -->
    <el-descriptions v-if="labInfo" :column="4" border size="small" class="lab-desc">
      <el-descriptions-item label="位置">
        {{ labInfo.location || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="容量">{{ labInfo.capacity }} 人</el-descriptions-item>
      <el-descriptions-item label="开放时间">
        {{ labInfo.open_time || '--' }} ~ {{ labInfo.close_time || '--' }}
      </el-descriptions-item>
      <el-descriptions-item label="简介">
        {{ labInfo.description || '-' }}
      </el-descriptions-item>
    </el-descriptions>

    <!-- 搜索栏 -->
    <div class="toolbar">
      <el-input
        v-model="searchForm.keyword"
        placeholder="请输入设备名称查询"
        style="width: 240px"
        clearable
        @keyup.enter="handleSearch"
        @clear="handleSearch"
      />
      <el-button type="primary" @click="handleSearch">查询</el-button>
      <el-button @click="handleReset">重置</el-button>
    </div>

    <!-- 设备表格（只读） -->
    <el-table :data="tableData" v-loading="loading" stripe>
      <el-table-column prop="img" label="图片" width="90">
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
            :src="defaultEquipImg"
            fit="cover"
            style="width: 50px; height: 50px; border-radius: 4px; background: #f5f5f5"
          />
        </template>
      </el-table-column>
      <el-table-column prop="name" label="设备名称" min-width="140" />
      <el-table-column prop="spec" label="型号规格" min-width="120">
        <template #default="{ row }">{{ row.spec || '-' }}</template>
      </el-table-column>
      <el-table-column prop="quantity" label="数量" width="80" />
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="isNormal(row.status) ? 'success' : 'warning'" size="small">
            {{ isNormal(row.status) ? '正常' : '维修中' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="设备说明" min-width="180">
        <template #default="{ row }">{{ row.description || '-' }}</template>
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
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { getLabDetailApi } from '@/api/lab'
import { getEquipmentListApi } from '@/api/equipment'
import { getFileUrl } from '@/utils/file'

// 默认设备占位图
const defaultEquipImg = 'https://aka.doubaocdn.com/l/u2ZcD4taUb'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const labLoading = ref(false)
const tableData = ref([])
const total = ref(0)
const labInfo = ref(null)

const labId = Number(route.query.lab_id)

const searchForm = reactive({
  keyword: ''
})

const query = reactive({
  page: 1,
  page_size: 10
})

const isOpen = (status) => Number(status) === 1
const isNormal = (status) => Number(status) === 1

const goBack = () => {
  router.push('/manager/labs')
}

// 查询当前实验室信息，用于页面顶部显示实验室名称
const loadLabInfo = async () => {
  labLoading.value = true
  try {
    const res = await getLabDetailApi(labId)
    labInfo.value = res.data || null
  } catch (err) {
    // 实验室不存在等情况已在拦截器统一提示
  } finally {
    labLoading.value = false
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await getEquipmentListApi({
      page: query.page,
      page_size: query.page_size,
      keywords: searchForm.keyword || undefined,
      lab_id: labId
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

onMounted(() => {
  if (!labId) {
    ElMessage.warning('请先从实验室列表进入')
    router.replace('/manager/labs')
    return
  }
  loadLabInfo()
  loadData()
})
</script>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-text {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
}

.lab-desc {
  margin-bottom: 18px;
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

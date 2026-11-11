<template>
  <el-card class="box-card">
    <template #header>
      <div class="card-header">
        <span>实验室预约</span>
        <el-tag type="info" size="small">提交后需管理员审核</el-tag>
      </div>
    </template>

    <el-form :model="form" label-width="90px">
      <el-row :gutter="16">
        <el-col :xs="24" :sm="12" :md="8">
          <el-form-item label="实验室" required>
            <el-select
              v-model="form.lab_id"
              placeholder="请选择实验室"
              style="width: 100%"
              @change="handleLabChange"
            >
              <el-option
                v-for="lab in labList"
                :key="lab.id"
                :label="lab.name"
                :value="lab.id"
              >
                <span>{{ lab.name }}</span>
                <span class="option-tip">{{ lab.location || '' }}</span>
              </el-option>
            </el-select>
          </el-form-item>
        </el-col>

        <el-col :xs="24" :sm="12" :md="8">
          <el-form-item label="设备">
            <el-select
              v-model="form.equipment_id"
              placeholder="不选 = 只预约实验室"
              style="width: 100%"
              clearable
              :disabled="!form.lab_id"
            >
              <el-option
                v-for="eq in equipmentList"
                :key="eq.id"
                :label="eq.name"
                :value="eq.id"
              >
                <span>{{ eq.name }}</span>
                <span class="option-tip">{{ eq.spec || '' }}</span>
              </el-option>
            </el-select>
          </el-form-item>
        </el-col>

        <el-col :xs="24" :sm="12" :md="8">
          <el-form-item label="预约日期" required>
            <el-date-picker
              v-model="form.reserve_date"
              type="date"
              placeholder="选择日期"
              value-format="YYYY-MM-DD"
              :disabled-date="disabledDate"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>

        <el-col :xs="24" :sm="12" :md="8">
          <el-form-item label="开始时间" required>
            <el-time-select
              v-model="form.start_time"
              :start="timeRange.start"
              step="00:30"
              :end="timeRange.end"
              placeholder="开始时间"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>

        <el-col :xs="24" :sm="12" :md="8">
          <el-form-item label="结束时间" required>
            <el-time-select
              v-model="form.end_time"
              :start="timeRange.start"
              step="00:30"
              :end="timeRange.end"
              placeholder="结束时间"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>

        <el-col :xs="24" :sm="12" :md="8">
          <el-form-item label="备注">
            <el-input v-model="form.remark" placeholder="选填，例如：做实验课项目" />
          </el-form-item>
        </el-col>
      </el-row>

      <div class="form-footer">
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          提交预约
        </el-button>
        <el-button @click="handleReset">重置</el-button>
        <el-button link type="primary" @click="router.push('/manager/my-reservation')">
          去「我的预约」查看提交记录
        </el-button>
      </div>
    </el-form>
  </el-card>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getLabListApi } from '@/api/lab'
import { getEquipmentListApi } from '@/api/equipment'
import { createReservationApi } from '@/api/reservation'

const router = useRouter()

const submitting = ref(false)
const labList = ref([])
const equipmentList = ref([])

const form = reactive({
  lab_id: null,
  equipment_id: null,
  reserve_date: '',
  start_time: '',
  end_time: '',
  remark: ''
})

// 时间选择器的范围跟着实验室开放时间走
const timeRange = computed(() => {
  const lab = labList.value.find((item) => item.id === form.lab_id)
  return {
    start: (lab && lab.open_time) || '08:00',
    end: (lab && lab.close_time) || '21:00'
  }
})

// 只能选今天及以后
const disabledDate = (time) => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return time.getTime() < today.getTime()
}

// 加载开放的实验室
const loadLabs = async () => {
  try {
    const res = await getLabListApi({ page: 1, page_size: 100, status: 1 })
    labList.value = res.data?.list || []
  } catch (err) {
    // 拦截器已提示
  }
}

// 切换实验室：重新加载设备，清掉之前选的设备和时间
const handleLabChange = async () => {
  form.equipment_id = null
  form.start_time = ''
  form.end_time = ''
  equipmentList.value = []
  if (!form.lab_id) return
  try {
    const res = await getEquipmentListApi({ page: 1, page_size: 100, lab_id: form.lab_id })
    equipmentList.value = (res.data?.list || []).filter((item) => item.status === 1)
  } catch (err) {
    equipmentList.value = []
  }
}

const handleReset = () => {
  form.lab_id = null
  form.equipment_id = null
  form.reserve_date = ''
  form.start_time = ''
  form.end_time = ''
  form.remark = ''
  equipmentList.value = []
}

const handleSubmit = async () => {
  if (!form.lab_id) {
    ElMessage.warning('请选择实验室')
    return
  }
  if (!form.reserve_date) {
    ElMessage.warning('请选择预约日期')
    return
  }
  if (!form.start_time || !form.end_time) {
    ElMessage.warning('请选择开始和结束时间')
    return
  }
  if (form.end_time <= form.start_time) {
    ElMessage.warning('结束时间必须晚于开始时间')
    return
  }

  submitting.value = true
  try {
    const res = await createReservationApi({
      lab_id: form.lab_id,
      equipment_id: form.equipment_id || null,
      reserve_date: form.reserve_date,
      start_time: form.start_time,
      end_time: form.end_time,
      remark: form.remark || null
    })
    ElMessage.success(res.message || '预约提交成功')
    handleReset()
    try {
      await ElMessageBox.confirm('预约已提交，要去「我的预约」查看吗？', '提示', {
        confirmButtonText: '去看看',
        cancelButtonText: '继续预约',
        type: 'success'
      })
      router.push('/manager/my-reservation')
    } catch (e) {
      // 用户选择继续预约
    }
  } catch (err) {
    // 后端的业务错误拦截器已经弹窗了
  } finally {
    submitting.value = false
  }
}

onMounted(loadLabs)
</script>

<style scoped>
.box-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.option-tip {
  float: right;
  color: #909399;
  font-size: 12px;
}

.form-footer {
  margin-left: 90px;
}
</style>

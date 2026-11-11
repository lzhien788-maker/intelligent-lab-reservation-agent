import request from '@/utils/request'

// 分页查询设备列表
export function getEquipmentListApi(params) {
  return request({
    url: '/api/equipment/list',
    method: 'get',
    params
  })
}

// 新增设备
export function createEquipmentApi(data) {
  return request({
    url: '/api/equipment',
    method: 'post',
    data
  })
}

// 编辑设备
export function updateEquipmentApi(id, data) {
  return request({
    url: `/api/equipment/${id}`,
    method: 'put',
    data
  })
}

// 删除设备
export function deleteEquipmentApi(id) {
  return request({
    url: `/api/equipment/${id}`,
    method: 'delete'
  })
}

// 获取所有实验室列表（下拉选择用）
export function getLabAllApi() {
  return request({
    url: '/api/lab/list',
    method: 'get',
    params: { page: 1, page_size: 999 }
  })
}

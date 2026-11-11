import request from '@/utils/request'

// 分页查询实验室列表
export function getLabListApi(params) {
  return request({
    url: '/api/lab/list',
    method: 'get',
    params
  })
}

// 查询单个实验室详情
export function getLabDetailApi(id) {
  return request({
    url: `/api/lab/${id}`,
    method: 'get'
  })
}

// 新增实验室
export function createLabApi(data) {
  return request({
    url: '/api/lab',
    method: 'post',
    data
  })
}

// 编辑实验室
export function updateLabApi(id, data) {
  return request({
    url: `/api/lab/${id}`,
    method: 'put',
    data
  })
}

// 删除实验室
export function deleteLabApi(id) {
  return request({
    url: `/api/lab/${id}`,
    method: 'delete'
  })
}

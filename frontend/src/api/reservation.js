import request from '@/utils/request'

// 提交预约
export function createReservationApi(data) {
  return request({
    url: '/api/reservation',
    method: 'post',
    data
  })
}

// 预约分页列表：学生自动只看自己的；管理员看全部，传 only_mine=true 只看自己
export function getReservationListApi(params) {
  return request({
    url: '/api/reservation/list',
    method: 'get',
    params
  })
}

// 管理员审核预约：status 1 通过 / 2 拒绝
export function auditReservationApi(id, status) {
  return request({
    url: `/api/reservation/${id}/audit`,
    method: 'put',
    data: { status }
  })
}

// 取消预约
export function cancelReservationApi(id) {
  return request({
    url: `/api/reservation/${id}/cancel`,
    method: 'put'
  })
}

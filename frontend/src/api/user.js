import request from '@/utils/request'

// 获取当前登录用户信息
export function getUserInfoApi() {
  return request({
    url: '/api/user/me',
    method: 'get'
  })
}

// 修改当前登录用户信息（只传要改的字段）
export function updateUserInfoApi(data) {
  return request({
    url: '/api/user/me',
    method: 'put',
    data
  })
}

/**
 * 修改密码
 */
export function updatePassword(data) {
  return request({
    url: '/api/user/password',
    method: 'put',
    data
  })
}

// 分页查询用户列表（管理员用）
export function getUserListApi(params) {
  return request({
    url: '/api/user/list',
    method: 'get',
    params
  })
}

// 管理员新增用户
export function createUserApi(data) {
  return request({
    url: '/api/user',
    method: 'post',
    data
  })
}

// 管理员编辑用户
export function updateUserApi(id, data) {
  return request({
    url: `/api/user/${id}`,
    method: 'put',
    data
  })
}

// 管理员删除用户
export function deleteUserApi(id) {
  return request({
    url: `/api/user/${id}`,
    method: 'delete'
  })
}

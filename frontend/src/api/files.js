import request from '@/utils/request'

// 上传文件，返回 { original_name, disk_name, size, url }
export function uploadFileApi(file) {
  const formData = new FormData()
  // 注意：后端参数名是 file（不是 files），字段名必须与函数签名一致
  formData.append('file', file)
  return request({
    url: '/api/files/upload',
    method: 'post',
    data: formData
  })
}

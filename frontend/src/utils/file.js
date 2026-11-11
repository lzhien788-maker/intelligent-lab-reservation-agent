const FILE_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

/**
 * 把后端返回的相对路径（如 /uploads/xxx.png）拼成可访问的完整地址
 * 已经是 http(s) 开头的地址则原样返回
 */
export function getFileUrl(url) {
  if (!url) return ''
  if (/^(https?:)?\/\//.test(url)) return url
  return FILE_BASE_URL + url
}

import request from '@/utils/request'
import { getToken } from '@/utils/auth'

const baseURL = import.meta.env.VITE_API_BASE_URL || ''

// 与 AI 助手对话（非流式）：传全部历史消息，一次性返回一条 assistant 消息
// 大模型响应比较慢，单独把超时放宽到 60 秒
export function chatApi(data) {
  return request({
    url: '/api/ai/chat',
    method: 'post',
    data,
    timeout: 60000
  })
}

/**
 * 流式对话（SSE）：后端一边跑 Agent 一边推事件，这里边读边回调
 *
 * 为什么不能用 axios：axios 必须等整个响应体收完才回调，做不到"边收边处理"，
 * 所以这里用原生 fetch + response.body.getReader() 手动读数据流。
 *
 * @param {Object} data     { messages: [{ role, content }] }
 * @param {Function} onEvent 每解析出一条事件就调用一次，参数是后端 yield 出来的对象：
 *                           { type: 'status' | 'tool_start' | 'tool_end' | 'token' | 'done' | 'error', ... }
 */
export async function chatStreamApi(data, onEvent) {
  const token = getToken()

  const res = await fetch(`${baseURL}/api/ai/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify(data)
  })

  if (res.status === 401) {
    throw new Error('登录已失效，请重新登录')
  }
  if (!res.ok || !res.body) {
    throw new Error('流式接口请求失败')
  }

  const contentType = res.headers.get('content-type') || ''
  if (!contentType.includes('text/event-stream')) {
    throw new Error('流式接口返回异常（不是 text/event-stream）')
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  // 后端一条消息的格式是：data: {...}\n\n
  // 一个网络分片可能包含半条消息，所以先攒到 buffer，再按空行切开
  const handleBlock = (block) => {
    const dataLines = []
    for (const line of block.split('\n')) {
      if (line.startsWith('data:')) {
        dataLines.push(line.slice(5).trim())
      }
    }
    if (!dataLines.length) return
    let payload
    try {
      payload = JSON.parse(dataLines.join('\n'))
    } catch {
      return // 半截 JSON 或者空行，忽略
    }
    onEvent(payload)
  }

  while (true) {
    const { done, value } = await reader.read() // done: true 表示流结束
    if (done) break

    // stream: true 表示后面可能还有字节，别把半个字符当成完整字符解码
    buffer += decoder.decode(value, { stream: true })

    const blocks = buffer.split('\n\n')
    // 最后一段可能是半截消息，留着和下一批数据拼
    buffer = blocks.pop()
    for (const block of blocks) {
      if (block.trim()) handleBlock(block)
    }
  }

  // 收尾：把残留的完整消息也处理掉
  if (buffer.trim()) handleBlock(buffer)
}

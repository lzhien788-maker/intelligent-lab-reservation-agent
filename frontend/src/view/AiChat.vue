<template>
  <el-card class="ai-card">
    <template #header>
      <div class="card-header">
        <div class="card-title">
          <el-icon><MagicStick /></el-icon>
          <span>AI智能助手</span>
        </div>
        <el-button link type="primary" :disabled="loading" @click="handleClear">
          清空对话
        </el-button>
      </div>
    </template>

    <div class="chat-wrap">
      <!-- 消息列表：助手在左（白气泡），用户在右（蓝气泡） -->
      <div ref="listRef" class="message-list">
        <div
          v-for="(item, index) in messages"
          :key="index"
          class="message-row"
          :class="item.role"
        >
          <!-- 用户消息 -->
          <div v-if="item.role === 'user'" class="bubble">{{ item.content }}</div>

          <!-- 助手消息：上方是执行过程，下面是回答气泡 -->
          <div v-else class="assistant-wrap">
            <div v-if="item.steps && item.steps.length" class="steps">
              <div
                v-for="(step, si) in item.steps"
                :key="si"
                class="step"
                :class="step.state"
              >
                <span class="step-icon">
                  <el-icon v-if="step.state === 'done'"><Select /></el-icon>
                  <el-icon v-else><Loading /></el-icon>
                </span>
                <span class="step-text">{{ step.text }}</span>
                <span v-if="step.preview" class="step-preview">{{ step.preview }}</span>
              </div>
            </div>

            <div class="bubble" :class="{ typing: item.streaming && !item.content }">
              <template v-if="item.content">{{ item.content }}</template>
              <template v-else-if="item.error">{{ item.error }}</template>
              <template v-else-if="item.streaming">
                正在思考
                <span class="dot" />
                <span class="dot" />
                <span class="dot" />
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部输入区：keydown 挂在外层，事件从 textarea 冒泡上来，一定生效 -->
      <div class="input-area" @keydown.enter="handleEnter">
        <el-input
          v-model="input"
          type="textarea"
          :rows="3"
          resize="none"
          maxlength="1000"
          show-word-limit
          :disabled="loading"
          placeholder="请输入你的问题，Enter 发送，Shift + Enter 换行"
        />
        <el-button
          type="primary"
          class="send-btn"
          :loading="loading"
          :disabled="!input.trim()"
          @click="handleSend"
        >
          发送
        </el-button>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { nextTick, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { MagicStick, Loading, Select } from '@element-plus/icons-vue'
import { chatStreamApi } from '@/api/ai'

const WELCOME = {
  role: 'assistant',
  content:
    '你好，我是AI智能助手，可以帮你查询实验室和设备，也可以帮你提交预约。有什么想问的直接输入就好。',
  welcome: true
}

const messages = ref([{ ...WELCOME }])
const input = ref('')
const loading = ref(false)
const listRef = ref(null)

// 滚动到最底部，保证新消息可见
const scrollToBottom = async () => {
  await nextTick()
  const el = listRef.value
  if (el) el.scrollTop = el.scrollHeight
}

const handleEnter = (e) => {
  if (e.shiftKey) return // Shift + Enter 换行
  e.preventDefault()
  handleSend()
}

const handleSend = async () => {
  const text = input.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  input.value = ''
  loading.value = true

  // 先塞一条空的助手消息，后面边收 token 边往里追加，实现打字机效果
  messages.value.push({
    role: 'assistant',
    content: '',
    steps: [],
    error: '',
    streaming: true
  })
  const idx = messages.value.length - 1
  const current = () => messages.value[idx]
  scrollToBottom()

  // 历史消息：去掉欢迎语和还没内容的空消息
  const history = messages.value
    .filter((m) => !m.welcome && m.content && m.content.trim())
    .map((m) => ({ role: m.role, content: m.content }))

  try {
    await chatStreamApi({ messages: history }, (evt) => {
      const msg = current()
      if (!msg) return

      switch (evt.type) {
        case 'status':
          msg.steps.push({ text: evt.message || '正在思考…', state: 'running', name: '' })
          break

        case 'tool_start':
          msg.steps.push({
            text: `正在${evt.label || evt.name}…`,
            state: 'running',
            name: evt.name || ''
          })
          break

        case 'tool_end': {
          // 找到这个工具对应那条"进行中"的记录，就地改成已完成
          const step = [...msg.steps]
            .reverse()
            .find((s) => s.state === 'running' && s.name === (evt.name || ''))
          if (step) {
            step.state = 'done'
            step.text = `已完成：${evt.label || evt.name}`
            if (evt.preview) step.preview = evt.preview
          } else {
            msg.steps.push({
              text: `已完成：${evt.label || evt.name}`,
              state: 'done',
              name: evt.name || '',
              preview: evt.preview
            })
          }
          break
        }

        case 'token':
          msg.content += evt.content || ''
          break

        case 'error':
          msg.error = evt.message || '出错了，请重试'
          break

        default:
          break
      }

      scrollToBottom()
    })
  } catch (err) {
    ElMessage.error(err?.message || '流式请求失败，请检查后端')
    const msg = current()
    if (msg) msg.error = err?.message || '请求失败'
  } finally {
    const msg = current()
    if (msg) {
      msg.streaming = false
      msg.steps.forEach((s) => {
        if (s.state === 'running') s.state = 'done'
      })
      if (!msg.content && !msg.error) {
        // 一个字都没吐出来，别留个空气泡
        messages.value.splice(idx, 1)
        ElMessage.error('AI 没有返回内容，请重试')
      }
    }
    loading.value = false
    scrollToBottom()
  }
}

const handleClear = () => {
  messages.value = [{ ...WELCOME }]
  input.value = ''
  scrollToBottom()
}
</script>

<style scoped>
.ai-card {
  height: calc(100vh - 140px);
  display: flex;
  flex-direction: column;
}

.ai-card :deep(.el-card__body) {
  flex: 1;
  padding: 0;
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: bold;
}

.chat-wrap {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: #f6f7f9;
}

.message-row {
  display: flex;
  margin-bottom: 16px;
}

.message-row.assistant {
  justify-content: flex-start;
}

.message-row.user {
  justify-content: flex-end;
}

.assistant-wrap {
  max-width: 70%;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.steps {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 6px 10px;
  border-radius: 6px;
  background-color: #f2f3f5;
  border: 1px dashed #dcdfe6;
}

.step {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #909399;
  line-height: 1.6;
}

.step.done {
  color: #67c23a;
}

.step-icon {
  display: inline-flex;
  align-items: center;
  font-size: 12px;
}

.step-text {
  flex-shrink: 0;
}

.step-preview {
  color: #a8abb2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.bubble {
  padding: 10px 14px;
  border-radius: 8px;
  line-height: 1.7;
  font-size: 14px;
  white-space: pre-wrap;
  word-break: break-word;
}

.message-row.assistant .bubble {
  background-color: #fff;
  border: 1px solid #e5e6eb;
  color: #333;
}

.message-row.user .bubble {
  background-color: #409eff;
  color: #fff;
}

.typing .dot {
  display: inline-block;
  width: 4px;
  height: 4px;
  margin-left: 3px;
  border-radius: 50%;
  background-color: #909399;
  animation: blink 1.2s infinite;
}

.typing .dot:nth-of-type(2) {
  animation-delay: 0.2s;
}

.typing .dot:nth-of-type(3) {
  animation-delay: 0.4s;
}

@keyframes blink {
  0%,
  100% {
    opacity: 0.2;
  }
  50% {
    opacity: 1;
  }
}

.input-area {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 12px 16px;
  border-top: 1px solid #e5e6eb;
  background-color: #fff;
}

.send-btn {
  height: 40px;
  flex-shrink: 0;
}
</style>

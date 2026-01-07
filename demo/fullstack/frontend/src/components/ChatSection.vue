<script setup>
import { ref, nextTick, onMounted, onUnmounted } from 'vue'

const messages = ref([
  {
    content: '您好！我是赛博玄数智能助手。请问今天您想咨询什么事项？我可以为您提供八字、紫微斗数、奇门遁甲等多种术数分析。',
    isUser: false,
    time: '10:30'
  },
  {
    content: '我想问一下2025年的事业运势如何',
    isUser: true,
    time: '10:31'
  },
  {
    content: '好的，为了给您更准确的分析，我需要了解一些基本信息。请问您的出生年月日和时辰是？另外，如果方便的话，可以给我3个随机数字（1-9），用于辅助分析。',
    isUser: false,
    time: '10:31'
  }
])

const inputText = ref('')
const isTyping = ref(false)
const chatContainer = ref(null)
let ws = null

const scrollToBottom = () => {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

const formatTime = () => {
  const now = new Date()
  return `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padLeft(2, '0')}`
}

const sendMessage = () => {
  const text = inputText.value.trim()
  if (!text) return

  // 添加用户消息
  messages.value.push({
    content: text,
    isUser: true,
    time: formatTime()
  })
  inputText.value = ''
  scrollToBottom()

  // 模拟AI回复
  isTyping.value = true
  setTimeout(() => {
    isTyping.value = false
    const responses = [
      '根据您提供的信息，我正在为您进行多维度分析...',
      '从八字来看，您的命局呈现出较好的发展态势。日主属土，喜用神为金水。',
      '2025年乙巳年，天干乙木生火，地支巳火当令，整体运势稳中有升。'
    ]
    messages.value.push({
      content: responses[Math.floor(Math.random() * responses.length)],
      isUser: false,
      time: formatTime()
    })
    scrollToBottom()
  }, 1500)
}

const handleKeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

onMounted(() => {
  scrollToBottom()
})
</script>

<template>
  <div class="glass-card overflow-hidden flex flex-col h-[500px]">
    <!-- 头部 -->
    <div class="flex items-center justify-between px-6 py-4 border-b border-white/[0.06]">
      <div class="flex items-center gap-2">
        <span class="text-lg">💬</span>
        <h3 class="text-sm font-medium text-gray-100">智能问答</h3>
      </div>
      <button class="btn-secondary !py-2 !px-4 text-sm">
        <span>🔄</span>
        <span>新对话</span>
      </button>
    </div>

    <!-- 消息列表 -->
    <div ref="chatContainer" class="flex-1 overflow-y-auto p-4 space-y-4">
      <div
        v-for="(message, index) in messages"
        :key="index"
        :class="['flex gap-3', message.isUser ? 'justify-end' : 'justify-start']"
      >
        <!-- AI头像 -->
        <div
          v-if="!message.isUser"
          class="w-9 h-9 rounded-full bg-gradient-to-br from-primary to-primary-light flex items-center justify-center text-white text-sm flex-shrink-0"
        >
          ☯
        </div>

        <!-- 消息内容 -->
        <div :class="['max-w-[80%]', message.isUser ? 'order-first' : '']">
          <div :class="message.isUser ? 'chat-bubble-user' : 'chat-bubble-ai'">
            <p class="text-sm leading-relaxed">{{ message.content }}</p>
          </div>
          <p :class="['text-[10px] text-gray-500 mt-1', message.isUser ? 'text-right' : 'text-left']">
            {{ message.time }}
          </p>
        </div>

        <!-- 用户头像 -->
        <div
          v-if="message.isUser"
          class="w-9 h-9 rounded-full bg-gradient-to-br from-accent to-accent-light flex items-center justify-center text-white text-sm font-medium flex-shrink-0"
        >
          李
        </div>
      </div>

      <!-- 打字指示器 -->
      <div v-if="isTyping" class="flex gap-3">
        <div class="w-9 h-9 rounded-full bg-gradient-to-br from-primary to-primary-light flex items-center justify-center text-white text-sm flex-shrink-0">
          ☯
        </div>
        <div class="chat-bubble-ai flex items-center gap-1 px-4">
          <span class="w-2 h-2 bg-gray-400 rounded-full typing-dot"></span>
          <span class="w-2 h-2 bg-gray-400 rounded-full typing-dot"></span>
          <span class="w-2 h-2 bg-gray-400 rounded-full typing-dot"></span>
        </div>
      </div>
    </div>

    <!-- 输入区 -->
    <div class="p-4 border-t border-white/[0.06]">
      <div class="flex gap-3">
        <input
          v-model="inputText"
          @keydown="handleKeydown"
          type="text"
          placeholder="输入您的问题..."
          class="input-field flex-1"
        />
        <button
          @click="sendMessage"
          :class="[
            'w-12 h-12 rounded-xl flex items-center justify-center transition-all',
            inputText.trim()
              ? 'bg-gradient-to-r from-primary to-primary-dark text-white shadow-lg shadow-primary/30'
              : 'bg-dark-tertiary text-gray-500'
          ]"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

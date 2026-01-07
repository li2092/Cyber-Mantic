<script setup>
import { ref } from 'vue'

defineProps({
  title: {
    type: String,
    default: '问道'
  }
})

const searchQuery = ref('')
</script>

<template>
  <header class="h-16 bg-white/[0.02] backdrop-blur-xl border-b border-white/[0.08] flex items-center justify-between px-8 sticky top-0 z-40">
    <!-- 页面标题 -->
    <div class="flex items-center gap-3">
      <span class="text-2xl">💬</span>
      <h2 class="text-lg font-medium text-gray-100">{{ title }} · 智能对话</h2>
    </div>

    <!-- 右侧操作 -->
    <div class="flex items-center gap-4">
      <!-- 搜索框 -->
      <div class="relative">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索历史记录..."
          class="w-60 h-10 pl-10 pr-4 bg-dark-tertiary border border-white/[0.08] rounded-xl text-sm text-gray-100 placeholder:text-gray-500 outline-none focus:border-primary transition-colors"
        />
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>

      <!-- 通知按钮 -->
      <button class="relative w-10 h-10 bg-white/[0.03] border border-white/[0.08] rounded-xl flex items-center justify-center text-gray-400 hover:bg-dark-tertiary hover:text-gray-100 transition-colors">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        <span class="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full text-[10px] text-white flex items-center justify-center font-medium">3</span>
      </button>

      <!-- 主题切换 -->
      <button class="w-10 h-10 bg-white/[0.03] border border-white/[0.08] rounded-xl flex items-center justify-center text-gray-400 hover:bg-dark-tertiary hover:text-gray-100 transition-colors">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
        </svg>
      </button>
    </div>
  </header>
</template>

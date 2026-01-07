<script setup>
const historyItems = [
  {
    title: '2025年事业运势分析',
    meta: '八字 · 2小时前',
    dotColor: 'bg-green-500'
  },
  {
    title: '感情姻缘咨询',
    meta: '紫微斗数 · 昨天',
    dotColor: 'bg-primary'
  },
  {
    title: '投资决策分析',
    meta: '奇门遁甲 · 3天前',
    dotColor: 'bg-amber-500'
  }
]
</script>

<template>
  <div class="glass-card">
    <!-- 头部 -->
    <div class="px-6 py-4 border-b border-white/[0.06]">
      <div class="flex items-center gap-2">
        <span class="text-lg">📜</span>
        <h3 class="text-sm font-medium text-gray-100">最近分析</h3>
      </div>
    </div>

    <!-- 内容 -->
    <div class="p-3">
      <button
        v-for="item in historyItems"
        :key="item.title"
        class="w-full flex items-center gap-3 p-3 rounded-xl transition-colors hover:bg-dark-tertiary group"
      >
        <span :class="['w-2 h-2 rounded-full flex-shrink-0', item.dotColor]"></span>
        <div class="flex-1 text-left">
          <p class="text-sm text-gray-100 group-hover:text-white transition-colors truncate">
            {{ item.title }}
          </p>
          <p class="text-xs text-gray-500">{{ item.meta }}</p>
        </div>
      </button>
    </div>
  </div>
</template>

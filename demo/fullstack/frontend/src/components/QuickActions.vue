<script setup>
const actions = [
  { icon: '🎲', label: '小六壬' },
  { icon: '✍️', label: '测字' },
  { icon: '🌸', label: '梅花易数' },
  { icon: '⚔️', label: '六爻' }
]
</script>

<template>
  <div class="glass-card">
    <!-- 头部 -->
    <div class="px-6 py-4 border-b border-white/[0.06]">
      <div class="flex items-center gap-2">
        <span class="text-lg">⚡</span>
        <h3 class="text-sm font-medium text-gray-100">快捷操作</h3>
      </div>
    </div>

    <!-- 内容 -->
    <div class="p-4">
      <div class="grid grid-cols-2 gap-3">
        <button
          v-for="action in actions"
          :key="action.label"
          class="p-5 bg-dark-tertiary rounded-xl text-center border border-transparent transition-all hover:bg-primary/10 hover:border-primary hover:-translate-y-0.5 group"
        >
          <span class="text-3xl block mb-2">{{ action.icon }}</span>
          <span class="text-sm text-gray-400 group-hover:text-gray-100 transition-colors">{{ action.label }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

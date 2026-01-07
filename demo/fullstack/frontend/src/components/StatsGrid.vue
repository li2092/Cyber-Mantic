<script setup>
const stats = [
  {
    icon: '📊',
    value: '128',
    label: '本月分析次数',
    trend: '↑ 12%',
    trendUp: true,
    iconBg: 'bg-primary/15',
    iconColor: 'text-primary-light'
  },
  {
    icon: '⏱️',
    value: '24.5h',
    label: '学习总时长',
    trend: '↑ 8%',
    trendUp: true,
    iconBg: 'bg-accent/15',
    iconColor: 'text-accent'
  },
  {
    icon: '📝',
    value: '56',
    label: '笔记数量',
    trend: '↑ 5%',
    trendUp: true,
    iconBg: 'bg-green-500/15',
    iconColor: 'text-green-500'
  },
  {
    icon: '🎯',
    value: '87%',
    label: '分析准确率',
    trend: '↓ 3%',
    trendUp: false,
    iconBg: 'bg-red-500/15',
    iconColor: 'text-red-500'
  }
]
</script>

<template>
  <div class="grid grid-cols-4 gap-6">
    <div
      v-for="stat in stats"
      :key="stat.label"
      class="stat-card group"
    >
      <!-- 头部 -->
      <div class="flex justify-between items-start mb-4">
        <div :class="['w-12 h-12 rounded-xl flex items-center justify-center text-2xl', stat.iconBg]">
          {{ stat.icon }}
        </div>
        <span
          :class="[
            'text-xs px-2.5 py-1 rounded-lg font-medium',
            stat.trendUp ? 'bg-green-500/15 text-green-500' : 'bg-red-500/15 text-red-500'
          ]"
        >
          {{ stat.trend }}
        </span>
      </div>

      <!-- 数值 -->
      <p class="text-3xl font-bold text-gray-100 mb-1">{{ stat.value }}</p>
      <p class="text-sm text-gray-500">{{ stat.label }}</p>
    </div>
  </div>
</template>

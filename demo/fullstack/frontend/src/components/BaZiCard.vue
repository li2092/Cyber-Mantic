<script setup>
const pillars = [
  { label: '年柱', gan: '甲', zhi: '子' },
  { label: '月柱', gan: '丙', zhi: '寅' },
  { label: '日柱', gan: '戊', zhi: '辰' },
  { label: '时柱', gan: '庚', zhi: '午' }
]

const wuxing = [
  { name: '木', count: 2, color: 'bg-wuxing-wood/20 text-wuxing-wood' },
  { name: '火', count: 3, color: 'bg-wuxing-fire/20 text-wuxing-fire' },
  { name: '土', count: 2, color: 'bg-wuxing-earth/20 text-wuxing-earth' },
  { name: '金', count: 1, color: 'bg-wuxing-metal/20 text-wuxing-metal' },
  { name: '水', count: 0, color: 'bg-wuxing-water/20 text-wuxing-water' }
]
</script>

<template>
  <div class="glass-card">
    <!-- 头部 -->
    <div class="px-6 py-4 border-b border-white/[0.06]">
      <div class="flex items-center gap-2">
        <span class="text-lg">🎴</span>
        <h3 class="text-sm font-medium text-gray-100">八字命盘</h3>
      </div>
    </div>

    <!-- 内容 -->
    <div class="p-6">
      <!-- 四柱 -->
      <div class="grid grid-cols-4 gap-3 mb-6">
        <div
          v-for="pillar in pillars"
          :key="pillar.label"
          class="bazi-pillar"
        >
          <p class="text-[10px] text-gray-500 mb-2">{{ pillar.label }}</p>
          <p class="font-serif text-2xl text-primary-light mb-1">{{ pillar.gan }}</p>
          <p class="font-serif text-2xl text-accent">{{ pillar.zhi }}</p>
        </div>
      </div>

      <!-- 五行分布 -->
      <div class="flex justify-around">
        <div
          v-for="wx in wuxing"
          :key="wx.name"
          class="text-center"
        >
          <div class="relative inline-block">
            <div :class="['wuxing-circle', wx.color]">
              {{ wx.name }}
            </div>
            <span
              :class="[
                'absolute -bottom-1 -right-1 w-5 h-5 rounded-full text-[10px] font-semibold flex items-center justify-center',
                'bg-dark-primary border-2',
                wx.color.includes('wood') ? 'border-wuxing-wood text-wuxing-wood' :
                wx.color.includes('fire') ? 'border-wuxing-fire text-wuxing-fire' :
                wx.color.includes('earth') ? 'border-wuxing-earth text-wuxing-earth' :
                wx.color.includes('metal') ? 'border-wuxing-metal text-wuxing-metal' :
                'border-wuxing-water text-wuxing-water'
              ]"
            >
              {{ wx.count }}
            </span>
          </div>
          <p class="text-xs text-gray-400 mt-2">{{ wx.name }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

const props = defineProps({
  active: {
    type: String,
    default: '问道'
  }
})

const emit = defineEmits(['update:active'])

const navSections = [
  {
    title: '核心功能',
    items: [
      { icon: '💬', label: '问道', badge: null },
      { icon: '🔮', label: '推演', badge: 'New' },
      { icon: '📚', label: '典籍', badge: null },
    ]
  },
  {
    title: '个人中心',
    items: [
      { icon: '💡', label: '洞察', badge: null },
      { icon: '📜', label: '历史记录', badge: null },
    ]
  },
  {
    title: '系统',
    items: [
      { icon: '⚙️', label: '设置', badge: null },
      { icon: '❓', label: '帮助', badge: null },
    ]
  }
]

const handleNavClick = (label) => {
  emit('update:active', label)
}
</script>

<template>
  <aside class="fixed left-0 top-0 bottom-0 w-[260px] bg-white/[0.02] backdrop-blur-xl border-r border-white/[0.08] flex flex-col z-50">
    <!-- Logo -->
    <div class="p-6 border-b border-white/[0.08]">
      <div class="flex items-center gap-3">
        <div class="w-12 h-12 bg-gradient-to-br from-primary to-primary-light rounded-xl flex items-center justify-center shadow-lg shadow-primary/30">
          <span class="text-2xl">☯</span>
        </div>
        <div>
          <h1 class="font-serif text-xl font-semibold bg-gradient-to-r from-gray-100 to-primary-light bg-clip-text text-transparent">
            赛博玄数
          </h1>
          <p class="text-[10px] text-gray-500 tracking-[2px]">CYBER MANTIC</p>
        </div>
      </div>
    </div>

    <!-- 导航菜单 -->
    <nav class="flex-1 overflow-y-auto px-3 py-4">
      <div v-for="section in navSections" :key="section.title" class="mb-6">
        <h2 class="text-[10px] text-gray-500 uppercase tracking-[1.5px] px-4 mb-2">
          {{ section.title }}
        </h2>
        <button
          v-for="item in section.items"
          :key="item.label"
          @click="handleNavClick(item.label)"
          :class="[
            'nav-btn',
            props.active === item.label ? 'active' : ''
          ]"
        >
          <span class="text-xl">{{ item.icon }}</span>
          <span class="flex-1 text-left">{{ item.label }}</span>
          <span
            v-if="item.badge"
            class="px-2 py-0.5 text-[10px] bg-primary rounded-full text-white"
          >
            {{ item.badge }}
          </span>
        </button>
      </div>
    </nav>

    <!-- 用户卡片 -->
    <div class="p-3">
      <div class="flex items-center gap-3 p-3 bg-white/[0.03] border border-white/[0.08] rounded-xl">
        <div class="w-10 h-10 bg-gradient-to-br from-accent to-accent-light rounded-full flex items-center justify-center text-white font-semibold">
          李
        </div>
        <div class="flex-1">
          <p class="text-sm font-medium text-gray-100">李明</p>
          <p class="text-xs text-green-500 flex items-center gap-1">
            <span class="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
            API 已连接
          </p>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
</script>

<template>
  <div class="relative overflow-hidden rounded-3xl p-8 border border-white/[0.08]" style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(245, 158, 11, 0.1) 50%, rgba(16, 185, 129, 0.1) 100%);">
    <!-- 装饰 -->
    <span class="absolute right-8 top-1/2 -translate-y-1/2 text-[100px] text-white/10 select-none">☯</span>

    <!-- 内容 -->
    <div class="relative">
      <h1 class="font-serif text-2xl font-semibold text-gray-100 mb-2">
        欢迎回来，李明
      </h1>
      <p class="text-gray-400 mb-6">
        今日宜：问事、出行、签约 | 紫气东来，万事可期
      </p>
      <div class="flex gap-3">
        <button class="btn-primary">
          <span>✨</span>
          <span>开始新对话</span>
        </button>
        <button class="btn-secondary">
          <span>📊</span>
          <span>查看今日运势</span>
        </button>
      </div>
    </div>
  </div>
</template>

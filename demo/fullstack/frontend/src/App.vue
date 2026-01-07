<script setup>
import { ref } from 'vue'
import Sidebar from './components/Sidebar.vue'
import TopBar from './components/TopBar.vue'
import WelcomeBanner from './components/WelcomeBanner.vue'
import StatsGrid from './components/StatsGrid.vue'
import ChatSection from './components/ChatSection.vue'
import BaZiCard from './components/BaZiCard.vue'
import QuickActions from './components/QuickActions.vue'
import HistoryList from './components/HistoryList.vue'

const activeNav = ref('问道')
</script>

<template>
  <div class="min-h-screen bg-dark-primary relative overflow-hidden">
    <!-- 背景装饰 -->
    <div class="fixed inset-0 pointer-events-none">
      <!-- 渐变光晕 -->
      <div class="absolute -top-1/4 -left-1/4 w-1/2 h-1/2 bg-primary/10 rounded-full blur-3xl"></div>
      <div class="absolute -bottom-1/4 -right-1/4 w-1/2 h-1/2 bg-accent/5 rounded-full blur-3xl"></div>

      <!-- 八卦装饰 -->
      <span class="absolute top-20 right-20 text-[120px] text-white/[0.03] select-none animate-float">☯</span>
      <span class="absolute bottom-32 left-10 text-[100px] text-white/[0.02] select-none animate-float" style="animation-delay: -3s;">☰</span>
    </div>

    <!-- 主布局 -->
    <div class="relative flex min-h-screen">
      <!-- 侧边栏 -->
      <Sidebar v-model:active="activeNav" />

      <!-- 主内容区 -->
      <main class="flex-1 ml-[260px] flex flex-col">
        <!-- 顶部栏 -->
        <TopBar :title="activeNav" />

        <!-- 内容区 -->
        <div class="flex-1 overflow-y-auto p-8">
          <!-- 欢迎横幅 -->
          <WelcomeBanner class="mb-8" />

          <!-- 统计卡片 -->
          <StatsGrid class="mb-8" />

          <!-- 主内容网格 -->
          <div class="grid grid-cols-3 gap-6">
            <!-- 对话区 (2列) -->
            <div class="col-span-2">
              <ChatSection />
            </div>

            <!-- 右侧面板 (1列) -->
            <div class="space-y-6">
              <BaZiCard />
              <QuickActions />
              <HistoryList />
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

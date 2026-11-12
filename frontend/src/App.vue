<script setup lang="ts">
import { useAuthStore } from './stores/auth'
const auth = useAuthStore()
</script>

<template>
  <header class="site-topbar">
    <router-link class="site-brand" to="/">文町<span>社区</span></router-link>
    <div class="topbar-caption">让每一种兴趣，都有回响</div>
    <div class="topbar-right"><span class="online-dot" />文字连接你我<span class="user-badge">{{ auth.user?.username || '欢迎来到文町' }}</span></div>
  </header>
  <router-view />
  <footer class="site-footer">文町 · 记录生活，分享热爱<span>友善表达，让交流更美好</span></footer>
</template>

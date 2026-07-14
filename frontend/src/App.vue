<template>
  <!-- 登录页：全屏渲染 -->
  <div v-if="route.meta.hideNav" style="height:100vh">
    <router-view />
  </div>

  <!-- 主应用：侧边栏 + Header + 内容 -->
  <div v-else class="app-layout">
    <!-- 侧边栏 -->
    <aside class="app-sidebar">
      <div class="logo">
        <el-icon :size="24"><FirstAidKit /></el-icon>
        <span>Lab2FHIR</span>
      </div>
      <el-menu
        :default-active="activeRoute"
        class="el-menu-vertical"
        router
      >
        <el-menu-item index="/">
          <el-icon><DataBoard /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-menu-item v-if="authStore.isPathologyStaff" index="/import">
          <el-icon><Upload /></el-icon>
          <span>导入报告</span>
        </el-menu-item>
        <el-menu-item index="/reports">
          <el-icon><Document /></el-icon>
          <span>报告列表</span>
        </el-menu-item>
      </el-menu>

      <div style="margin-top:auto;padding:16px;border-top:1px solid rgba(255,255,255,0.08)">
        <div style="font-size:12px;color:rgba(255,255,255,0.4);line-height:1.8">
          Lab2FHIR v1.0<br/>
          化验单 → FHIR R4
        </div>
      </div>
    </aside>

    <!-- 主区域 -->
    <div class="app-main">
      <header class="app-header">
        <h2>{{ currentTitle }}</h2>
        <div style="display:flex;align-items:center;gap:12px">
          <el-tag
            :type="authStore.isPathologyStaff ? 'warning' : 'info'"
            size="small"
          >
            {{ authStore.isPathologyStaff ? '病理科' : '医生' }}
          </el-tag>
          <span style="font-size:13px;color:#606266">{{ authStore.displayName }}</span>
          <el-button text size="small" @click="handleLogout">退出</el-button>
        </div>
      </header>
      <main class="app-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth.js'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeRoute = computed(() => route.path)
const currentTitle = computed(() => route.meta?.title || 'Lab2FHIR')

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

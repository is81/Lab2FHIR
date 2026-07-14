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
        <el-menu-item index="/import">
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
          <template v-if="authStore.isAuthenticated">
            <el-tag size="small" type="warning">已登录</el-tag>
            <el-button text size="small" @click="showPwdDialog = true">修改密码</el-button>
            <el-popconfirm title="确定清空所有数据和文件？此操作不可恢复" @confirm="handleClearAll">
              <template #reference>
                <el-button text size="small" type="danger">清空数据</el-button>
              </template>
            </el-popconfirm>
            <el-button text size="small" @click="authStore.logout()">退出</el-button>
          </template>
        </div>
      </header>
      <main class="app-content">
        <router-view />
      </main>
    </div>

    <!-- 修改密码弹窗 -->
    <el-dialog v-model="showPwdDialog" title="修改密码" width="360px" center>
      <el-form :model="pwdForm" @submit.prevent="handleChangePwd" size="large">
        <el-form-item>
          <el-input v-model="pwdForm.old" type="password" placeholder="原密码" show-password />
        </el-form-item>
        <el-form-item>
          <el-input v-model="pwdForm.new1" type="password" placeholder="新密码" show-password />
        </el-form-item>
        <el-form-item>
          <el-input v-model="pwdForm.new2" type="password" placeholder="确认新密码" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="pwdLoading" @click="handleChangePwd" style="width:100%">
            {{ pwdLoading ? '修改中...' : '确认修改' }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref, reactive } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from './stores/auth.js'
import api from './api/index.js'

const route = useRoute()
const authStore = useAuthStore()

const activeRoute = computed(() => route.path)
const currentTitle = computed(() => route.meta?.title || 'Lab2FHIR')

// 修改密码
const showPwdDialog = ref(false)
const pwdLoading = ref(false)
const pwdForm = reactive({ old: '', new1: '', new2: '' })

async function handleClearAll() {
  try {
    await api.delete('/admin/clear')
    ElMessage.success('数据已清空')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  }
}

async function handleChangePwd() {
  if (!pwdForm.old) { ElMessage.warning('请输入原密码'); return }
  if (!pwdForm.new1) { ElMessage.warning('请输入新密码'); return }
  if (pwdForm.new1 !== pwdForm.new2) { ElMessage.warning('两次新密码不一致'); return }
  pwdLoading.value = true
  try {
    await api.put('/auth/password', { old_password: pwdForm.old, new_password: pwdForm.new1 })
    ElMessage.success('密码已修改')
    showPwdDialog.value = false
    pwdForm.old = ''; pwdForm.new1 = ''; pwdForm.new2 = ''
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '修改失败')
  } finally {
    pwdLoading.value = false
  }
}
</script>

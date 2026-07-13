import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { title: '首页', icon: 'DataBoard' }
  },
  {
    path: '/import',
    name: 'Import',
    component: () => import('../views/ImportView.vue'),
    meta: { title: '导入报告', icon: 'Upload' }
  },
  {
    path: '/reports',
    name: 'ReportList',
    component: () => import('../views/ReportList.vue'),
    meta: { title: '报告列表', icon: 'Document' }
  },
  {
    path: '/reports/:id',
    name: 'ReportDetail',
    component: () => import('../views/ReportDetail.vue'),
    meta: { title: '报告详情', icon: 'View' }
  },
  {
    path: '/patients/:name',
    name: 'PatientView',
    component: () => import('../views/PatientView.vue'),
    meta: { title: '患者视图', icon: 'User' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 2.7 修复：路由守卫，验证参数有效性
router.beforeEach((to, from, next) => {
  if (to.name === 'ReportDetail') {
    const id = parseInt(to.params.id)
    if (isNaN(id) || id < 1) {
      next('/reports')
      return
    }
  }
  if (to.name === 'PatientView' && !to.params.name) {
    next('/reports')
    return
  }
  next()
})

export default router

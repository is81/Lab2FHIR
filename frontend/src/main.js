import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import './styles/global.css'

const pinia = createPinia()
const app = createApp(App)
app.use(pinia)
app.use(ElementPlus, { locale: zhCn })
app.use(router)

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 启动时验证持久化 token 的有效性
import { useAuthStore } from './stores/auth.js'
const authStore = useAuthStore()
if (authStore.isAuthenticated) {
  authStore.fetchMe()  // 异步验证，失败会自动 logout
}

app.mount('#app')

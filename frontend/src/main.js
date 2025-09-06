import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue' 
import Notifications from '@kyvg/vue3-notification'
import { setupI18n } from './i18n'
import { useAuthStore } from './stores/auth'
import { useThemeStore } from './stores/theme'
import { useMarketStore } from './stores/market'
import '@/assets/styles/main.scss' 
 
// 导入路由配置 
import routes from './routes'
 
// 初始化i18n 
const i18n = setupI18n()
 
// 创建路由实例
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL), 
  routes,
  scrollBehavior(to, from, savedPosition) {
    // 返回顶部或保持滚动位置 
    if (savedPosition) {
      return savedPosition 
    } else {
      return { top: 0 }
    }
  }
})
 
// 全局路由守卫 
router.beforeEach(async  (to, from, next) => {
  const authStore = useAuthStore()
  const themeStore = useThemeStore()
  
  // 初始化主题 
  await themeStore.initializeTheme() 
  
  // 检查需要认证的路由
  if (to.meta.requiresAuth  && !authStore.isAuthenticated)  {
    next('/login')
    return 
  }
  
  // 检查已认证用户访问登录页
  if (to.name  === 'Login' && authStore.isAuthenticated)  {
    next('/dashboard')
    return
  }
  
  // 设置页面标题
  document.title  = to.meta.title  
    ? `${to.meta.title}  | CryptoTrader` 
    : 'CryptoTrader' 
  
  next()
})
 
// 创建Vue应用 
const app = createApp(App)
 
// 使用插件 
app.use(createPinia()) 
app.use(router) 
app.use(i18n) 
app.use(Notifications) 
 
// 全局错误处理 
app.config.errorHandler  = (err, vm, info) => {
  console.error('Global  error:', err)
  const marketStore = useMarketStore()
  marketStore.setError(err.message  || 'An unknown error occurred')
}
 
// 全局属性 
app.config.globalProperties.$filters  = {
  formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value)
  },
  formatPercentage(value) {
    return `${(value * 100).toFixed(2)}%`
  }
}
 
// 挂载应用 
app.mount('#app') 
 
// 开发环境下暴露全局变量 
if (import.meta.env.DEV)  {
  window.__APP__ = app 
  window.__ROUTER__ = router 
}
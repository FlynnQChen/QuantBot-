<template>
  <div id="app" :class="themeClass">
    <!-- 系统通知组件 -->
    <notifications position="bottom right" />
    
    <!-- 全局加载指示器 -->
    <div v-if="isLoading" class="global-loader">
      <div class="loader-content">
        <spinner size="large" />
        <p>加载中...</p>
      </div>
    </div>
    
    <!-- 主应用布局 -->
    <div class="app-layout">
      <!-- 顶部导航栏 -->
      <header class="app-header">
        <div class="header-left">
          <router-link to="/" class="logo-link">
            <img src="@/assets/logo.svg"  alt="Trading Platform" class="logo">
            <span class="app-name">CryptoTrader</span>
          </router-link>
          
          <nav class="main-nav">
            <router-link 
              v-for="route in mainRoutes" 
              :key="route.path" 
              :to="route.path" 
              active-class="active"
              class="nav-item"
            >
              {{ route.meta?.title  || route.name  }}
            </router-link>
          </nav>
        </div>
        
        <div class="header-right">
          <div class="market-status">
            <span class="status-indicator" :class="marketTrend"></span>
            <span class="status-text">{{ marketStatusText }}</span>
            <span class="btc-price">
              BTC: ${{ btcPrice.toLocaleString()  }}
              <span :class="btcChange >= 0 ? 'up' : 'down'">
                ({{ btcChange >= 0 ? '+' : '' }}{{ btcChange.toFixed(2)  }}%)
              </span>
            </span>
          </div>
          
          <div class="user-controls">
            <button class="notifications-btn" @click="toggleNotifications">
              <i class="icon-bell"></i>
              <span v-if="unreadNotifications > 0" class="badge">
                {{ unreadNotifications }}
              </span>
            </button>
            
            <dropdown class="user-dropdown" :offset="[0, 10]">
              <template #trigger>
                <div class="user-avatar">
                  <img :src="user.avatar"  :alt="user.name"> 
                </div>
              </template>
              <template #content>
                <div class="dropdown-menu">
                  <div class="user-info">
                    <div class="avatar">
                      <img :src="user.avatar"  :alt="user.name"> 
                    </div>
                    <div class="details">
                      <h4>{{ user.name  }}</h4>
                      <p>{{ user.email  }}</p>
                    </div>
                  </div>
                  <div class="dropdown-divider"></div>
                  <router-link to="/settings" class="dropdown-item">
                    <i class="icon-settings"></i> 账户设置 
                  </router-link>
                  <a href="#" class="dropdown-item" @click.prevent="logout"> 
                    <i class="icon-logout"></i> 退出登录
                  </a>
                </div>
              </template>
            </dropdown>
          </div>
        </div>
      </header>
      
      <!-- 通知面板 -->
      <transition name="slide-fade">
        <notifications-panel 
          v-if="showNotifications"
          @close="showNotifications = false"
        />
      </transition>
      
      <!-- 主内容区域 -->
      <main class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
      
      <!-- 底部状态栏 -->
      <footer class="app-footer">
        <div class="footer-left">
          <span class="connection-status" :class="connectionStatus">
            <span class="status-dot"></span>
            {{ connectionStatusText }}
          </span>
          <span class="last-sync">
            最后同步: {{ formatTime(lastSync) }}
          </span>
        </div>
        
        <div class="footer-right">
          <span class="app-version">v{{ appVersion }}</span>
          <a href="#" class="help-link">帮助中心</a>
          <a href="#" class="feedback-link">意见反馈</a>
        </div>
      </footer>
    </div>
  </div>
</template>
 
<script>
import { mapState, mapGetters } from 'vuex'
import { format } from 'date-fns'
import Dropdown from '@/components/ui/Dropdown.vue' 
import Spinner from '@/components/ui/Spinner.vue' 
import NotificationsPanel from '@/components/NotificationsPanel.vue' 
 
export default {
  components: {
    Dropdown,
    Spinner,
    NotificationsPanel
  },
  data() {
    return {
      showNotifications: false,
      lastSync: Date.now(), 
      marketTrend: 'up',
      btcPrice: 42356.78,
      btcChange: 2.34,
      connectionStatus: 'connected',
      unreadNotifications: 3,
      mainRoutes: [
        { path: '/dashboard', name: 'Dashboard', meta: { title: '仪表盘' } },
        { path: '/trade', name: 'Trade', meta: { title: '交易' } },
        { path: '/portfolio', name: 'Portfolio', meta: { title: '资产' } },
        { path: '/history', name: 'History', meta: { title: '历史' } },
        { path: '/analytics', name: 'Analytics', meta: { title: '分析' } }
      ],
      priceUpdateInterval: null,
      syncInterval: null 
    }
  },
  computed: {
    ...mapState(['isLoading', 'user', 'theme']),
    ...mapGetters(['appVersion']),
    themeClass() {
      return `theme-${this.theme}` 
    },
    marketStatusText() {
      return this.marketTrend  === 'up' ? '牛市' : '熊市'
    },
    connectionStatusText() {
      return {
        connected: '已连接',
        disconnected: '连接断开',
        reconnecting: '重新连接中...'
      }[this.connectionStatus]
    }
  },
  created() {
    this.setupRealTimeUpdates() 
    this.loadInitialData() 
  },
  mounted() {
    // 检查用户认证状态 
    if (!this.user)  {
      this.$router.push('/login') 
    }
  },
  beforeUnmount() {
    this.cleanupIntervals() 
  },
  methods: {
    formatTime(timestamp, formatStr = 'MM/dd HH:mm:ss') {
      return format(new Date(timestamp), formatStr)
    },
    setupRealTimeUpdates() {
      // 模拟实时价格更新 
      this.priceUpdateInterval  = setInterval(() => {
        this.btcPrice  = 42356.78 + (Math.random()  - 0.5) * 500 
        this.btcChange  = 2.34 + (Math.random()  - 0.5) * 2
        this.marketTrend  = this.btcChange  >= 0 ? 'up' : 'down'
      }, 5000)
      
      // 模拟同步状态更新 
      this.syncInterval  = setInterval(() => {
        this.lastSync  = Date.now() 
      }, 30000)
    },
    loadInitialData() {
      // 加载初始数据
      this.$store.dispatch('loadInitialData') 
    },
    cleanupIntervals() {
      clearInterval(this.priceUpdateInterval) 
      clearInterval(this.syncInterval) 
    },
    toggleNotifications() {
      this.showNotifications  = !this.showNotifications  
      if (this.showNotifications)  {
        this.unreadNotifications  = 0
      }
    },
    logout() {
      this.$store.dispatch('logout') 
      this.$router.push('/login') 
    }
  }
}
</script>
 
<style lang="scss">
#app {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-color);
  color: var(--text-color);
  transition: background 0.3s ease;
  
  &.theme-light {
    --bg-color: #f5f6fa;
    --text-color: #2a2a3c;
    --primary-color: #6e45e2;
    --secondary-color: #a5a6c1;
    --card-bg: #ffffff;
    --border-color: #e0e0e5;
  }
  
  &.theme-dark {
    --bg-color: #1e1e2d;
    --text-color: #e0e0e0;
    --primary-color: #8a63f2;
    --secondary-color: #6a6a7c;
    --card-bg: #2a2a3c;
    --border-color: #3a3a4c;
  }
}
 
.global-loader {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  
  .loader-content {
    text-align: center;
    color: white;
    
    p {
      margin-top: 16px;
    }
  }
}
 
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100%;
}
 
.app-header {
  height: 60px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--card-bg);
  border-bottom: 1px solid var(--border-color);
  z-index: 100;
}
 
.header-left {
  display: flex;
  align-items: center;
}
 
.logo-link {
  display: flex;
  align-items: center;
  text-decoration: none;
  margin-right: 32px;
  
  .logo {
    height: 32px;
    margin-right: 12px;
  }
  
  .app-name {
    font-size: 18px;
    font-weight: bold;
    color: var(--text-color);
  }
}
 
.main-nav {
  display: flex;
  
  .nav-item {
    padding: 8px 16px;
    margin-right: 8px;
    text-decoration: none;
    color: var(--secondary-color);
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s;
    
    &:hover {
      color: var(--primary-color);
      background: rgba(110, 69, 226, 0.1);
    }
    
    &.active {
      color: var(--primary-color);
      background: rgba(110, 69, 226, 0.1);
    }
  }
}
 
.header-right {
  display: flex;
  align-items: center;
}
 
.market-status {
  display: flex;
  align-items: center;
  margin-right: 24px;
  font-size: 14px;
  
  .status-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 8px;
    
    &.up {
      background: #00e676;
    }
    
    &.down {
      background: #ff4757;
    }
  }
  
  .status-text {
    margin-right: 16px;
    font-weight: 500;
  }
  
  .btc-price {
    font-weight: 500;
    
    .up {
      color: #00e676;
    }
    
    .down {
      color: #ff4757;
    }
  }
}
 
.user-controls {
  display: flex;
  align-items: center;
  
  .notifications-btn {
    background: none;
    border: none;
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    margin-right: 12px;
    cursor: pointer;
    position: relative;
    color: var(--secondary-color);
    
    &:hover {
      background: rgba(110, 69, 226, 0.1);
      color: var(--primary-color);
    }
    
    .badge {
      position: absolute;
      top: -2px;
      right: -2px;
      background: #ff4757;
      color: white;
      border-radius: 50%;
      width: 16px;
      height: 16px;
      font-size: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
  }
}
 
.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  overflow: hidden;
  cursor: pointer;
  
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}
 
.dropdown-menu {
  width: 240px;
  padding: 16px;
  background: var(--card-bg);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
 
.user-info {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  
  .avatar {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    overflow: hidden;
    margin-right: 12px;
    
    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
  }
  
  h4 {
    margin: 0 0 4px;
    font-size: 15px;
  }
  
  p {
    margin: 0;
    font-size: 13px;
    color: var(--secondary-color);
  }
}
 
.dropdown-divider {
  height: 1px;
  background: var(--border-color);
  margin: 12px -16px;
}
 
.dropdown-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
  text-decoration: none;
  color: var(--text-color);
  font-size: 14px;
  
  i {
    margin-right: 8px;
    width: 20px;
    text-align: center;
  }
  
  &:hover {
    color: var(--primary-color);
  }
}
 
.app-main {
  flex: 1;
  overflow: auto;
  padding: 24px;
  background: var(--bg-color);
}
 
.app-footer {
  height: 40px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--card-bg);
  border-top: 1px solid var(--border-color);
  font-size: 12px;
  color: var(--secondary-color);
}
 
.footer-left, .footer-right {
  display: flex;
  align-items: center;
}
 
.connection-status {
  display: flex;
  align-items: center;
  margin-right: 16px;
  
  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 6px;
  }
  
  &.connected .status-dot {
    background: #00e676;
  }
  
  &.disconnected .status-dot {
    background: #ff4757;
  }
  
  &.reconnecting .status-dot {
    background: #ffa502;
  }
}
 
.last-sync {
  margin-right: 16px;
}
 
.app-version {
  margin-right: 16px;
}
 
.help-link, .feedback-link {
  color: var(--secondary-color);
  text-decoration: none;
  margin-right: 16px;
  
  &:hover {
    color: var(--primary-color);
  }
}
 
/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
 
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
 
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}
 
.slide-fade-leave-active {
  transition: all 0.3s ease-in;
}
 
.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateY(20px);
  opacity: 0;
}
 
/* 响应式设计 */
@media (max-width: 1024px) {
  .app-header {
    padding: 0 16px;
  }
  
  .logo-link .app-name {
    display: none;
  }
  
  .market-status {
    display: none;
  }
}
 
@media (max-width: 768px) {
  .main-nav {
    display: none;
  }
  
  .app-main {
    padding: 16px;
  }
  
  .app-footer {
    flex-direction: column;
    height: auto;
    padding: 8px 16px;
    text-align: center;
    
    .footer-left, .footer-right {
      margin: 4px 0;
    }
  }
}
</style>
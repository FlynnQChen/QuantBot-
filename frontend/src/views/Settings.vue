<template>
  <div class="settings-container">
    <!-- 设置导航栏 -->
    <div class="settings-nav">
      <div class="profile-header">
        <div class="avatar">
          <img :src="user.avatar"  alt="User Avatar">
        </div>
        <div class="profile-info">
          <h3>{{ user.name  }}</h3>
          <p>{{ user.email  }}</p>
        </div>
      </div>
      <nav>
        <button 
          v-for="tab in tabs" 
          :key="tab.id" 
          :class="{ active: activeTab === tab.id  }"
          @click="activeTab = tab.id" 
        >
          <i :class="tab.icon"></i> 
          {{ tab.label  }}
        </button>
      </nav>
    </div>
 
    <!-- 设置内容区域 -->
    <div class="settings-content">
      <!-- 账户设置 -->
      <div v-show="activeTab === 'account'" class="settings-section">
        <h2>账户设置</h2>
        <form @submit.prevent="updateAccount"> 
          <div class="form-group">
            <label>用户名</label>
            <input 
              type="text" 
              v-model="accountForm.name" 
              placeholder="输入用户名"
            >
          </div>
          <div class="form-group">
            <label>电子邮箱</label>
            <input 
              type="email" 
              v-model="accountForm.email" 
              placeholder="输入电子邮箱"
            >
          </div>
          <div class="form-group">
            <label>头像</label>
            <div class="avatar-upload">
              <img :src="accountForm.avatarPreview  || accountForm.avatar"  alt="Avatar Preview">
              <div class="upload-controls">
                <input 
                  type="file" 
                  ref="avatarInput"
                  accept="image/*"
                  @change="handleAvatarUpload"
                  hidden 
                >
                <button 
                  type="button"
                  class="btn-upload"
                  @click="$refs.avatarInput.click()" 
                >
                  选择图片
                </button>
                <button 
                  type="button"
                  class="btn-remove"
                  @click="removeAvatar"
                  v-if="accountForm.avatarPreview  || accountForm.avatar" 
                >
                  移除
                </button>
              </div>
            </div>
          </div>
          <div class="form-actions">
            <button type="submit" class="btn-save">保存更改</button>
          </div>
        </form>
      </div>
 
      <!-- 安全设置 -->
      <div v-show="activeTab === 'security'" class="settings-section">
        <h2>安全设置</h2>
        
        <div class="security-item">
          <div class="security-info">
            <h4>密码</h4>
            <p>定期更改密码以保护账户安全</p>
          </div>
          <button 
            class="btn-change"
            @click="showPasswordModal = true"
          >
            更改密码
          </button>
        </div>
 
        <div class="security-item">
          <div class="security-info">
            <h4>双重验证</h4>
            <p>为账户添加额外的安全层</p>
          </div>
          <toggle-switch 
            v-model="securityForm.twoFactorEnabled" 
            @change="updateTwoFactor"
          />
        </div>
 
        <div v-if="securityForm.twoFactorEnabled"  class="two-factor-setup">
          <div class="qr-code">
            <img :src="twoFactorQRCode" alt="2FA QR Code">
          </div>
          <div class="backup-codes">
            <h4>备用代码</h4>
            <p>请妥善保存这些一次性代码</p>
            <div class="codes-grid">
              <div 
                v-for="(code, index) in backupCodes"
                :key="index"
                class="code-item"
              >
                {{ code }}
              </div>
            </div>
            <button 
              class="btn-regenerate"
              @click="generateBackupCodes"
            >
              重新生成代码
            </button>
          </div>
        </div>
 
        <div class="security-item">
          <div class="security-info">
            <h4>活跃会话</h4>
            <p>当前登录的设备</p>
          </div>
        </div>
        <div class="sessions-list">
          <div 
            v-for="session in activeSessions" 
            :key="session.id" 
            class="session-item"
          >
            <div class="session-icon">
              <i :class="session.deviceType  === 'desktop' ? 'icon-desktop' : 'icon-mobile'"></i>
            </div>
            <div class="session-details">
              <div class="session-device">
                <strong>{{ session.deviceName  }}</strong>
                <span v-if="session.current"  class="current-label">当前设备</span>
              </div>
              <div class="session-info">
                <span>{{ session.browser  }}</span>
                <span>{{ session.ip  }}</span>
                <span>最后活跃: {{ formatTime(session.lastActive)  }}</span>
              </div>
            </div>
            <button 
              class="btn-revoke"
              @click="revokeSession(session.id)" 
              v-if="!session.current" 
            >
              撤销 
            </button>
          </div>
        </div>
      </div>
 
      <!-- API密钥管理 -->
      <div v-show="activeTab === 'api'" class="settings-section">
        <h2>API 密钥管理</h2>
        <div class="api-description">
          <p>使用API密钥可以编程访问您的账户。请妥善保管您的密钥，不要泄露给他人。</p>
          <button 
            class="btn-create"
            @click="showApiKeyModal = true"
          >
            <i class="icon-plus"></i> 创建新密钥 
          </button>
        </div>
 
        <div class="api-keys-list">
          <div 
            v-for="key in apiKeys"
            :key="key.id" 
            class="api-key-item"
          >
            <div class="key-info">
              <h4>{{ key.name  }}</h4>
              <p>创建于 {{ formatTime(key.createdAt)  }}</p>
              <div class="key-permissions">
                <span 
                  v-for="perm in key.permissions" 
                  :key="perm"
                  class="permission-tag"
                >
                  {{ perm }}
                </span>
              </div>
            </div>
            <div class="key-actions">
              <button 
                class="btn-show"
                @click="showApiKey(key)"
                v-if="!key.revealed" 
              >
                显示密钥 
              </button>
              <div class="key-value" v-else>
                <code>{{ key.secret  }}</code>
                <button 
                  class="btn-copy"
                  @click="copyToClipboard(key.secret)" 
                >
                  复制
                </button>
              </div>
              <button 
                class="btn-delete"
                @click="deleteApiKey(key.id)" 
              >
                删除
              </button>
            </div>
          </div>
          <div v-if="apiKeys.length  === 0" class="no-keys">
            <p>您还没有创建任何API密钥</p>
          </div>
        </div>
      </div>
 
      <!-- 通知设置 -->
      <div v-show="activeTab === 'notifications'" class="settings-section">
        <h2>通知设置</h2>
        
        <div class="notification-group">
          <h3>电子邮件通知</h3>
          <div class="notification-item">
            <div class="notification-info">
              <h4>账户活动</h4>
              <p>登录、密码更改等重要活动</p>
            </div>
            <toggle-switch v-model="notificationForm.email.account"  />
          </div>
          <div class="notification-item">
            <div class="notification-info">
              <h4>交易执行</h4>
              <p>订单成交、取消等交易活动</p>
            </div>
            <toggle-switch v-model="notificationForm.email.trading"  />
          </div>
          <div class="notification-item">
            <div class="notification-info">
              <h4>市场警报</h4>
              <p>价格警报、波动通知</p>
            </div>
            <toggle-switch v-model="notificationForm.email.alerts"  />
          </div>
        </div>
 
        <div class="notification-group">
          <h3>应用内通知</h3>
          <div class="notification-item">
            <div class="notification-info">
              <h4>声音提醒</h4>
              <p>交易执行时的声音提示</p>
            </div>
            <toggle-switch v-model="notificationForm.app.sound"  />
          </div>
          <div class="notification-item">
            <div class="notification-info">
              <h4>桌面通知</h4>
              <p>即使应用最小化也显示通知</p>
            </div>
            <toggle-switch v-model="notificationForm.app.desktop"  />
          </div>
        </div>
 
        <div class="notification-group">
          <h3>短信通知</h3>
          <div class="notification-item">
            <div class="notification-info">
              <h4>启用短信通知</h4>
              <p>重要通知通过短信发送</p>
            </div>
            <toggle-switch v-model="notificationForm.sms.enabled"  />
          </div>
          <div v-if="notificationForm.sms.enabled"  class="sms-phone">
            <label>手机号码</label>
            <input 
              type="tel" 
              v-model="notificationForm.sms.phone" 
              placeholder="+国家代码 手机号码"
            >
          </div>
        </div>
 
        <div class="form-actions">
          <button class="btn-save" @click="saveNotificationSettings">保存设置</button>
        </div>
      </div>
 
      <!-- 偏好设置 -->
      <div v-show="activeTab === 'preferences'" class="settings-section">
        <h2>偏好设置</h2>
        
        <div class="preference-group">
          <h3>界面设置</h3>
          <div class="preference-item">
            <div class="preference-info">
              <h4>主题</h4>
              <p>选择应用的颜色主题</p>
            </div>
            <div class="theme-selector">
              <button 
                v-for="theme in themes"
                :key="theme.value" 
                :class="{ active: preferenceForm.theme  === theme.value  }"
                @click="preferenceForm.theme  = theme.value" 
              >
                <div class="theme-preview" :class="theme.value"></div> 
                <span>{{ theme.label  }}</span>
              </button>
            </div>
          </div>
          <div class="preference-item">
            <div class="preference-info">
              <h4>语言</h4>
              <p>选择界面显示语言</p>
            </div>
            <select v-model="preferenceForm.language"> 
              <option 
                v-for="lang in languages"
                :key="lang.code" 
                :value="lang.code" 
              >
                {{ lang.name  }}
              </option>
            </select>
          </div>
          <div class="preference-item">
            <div class="preference-info">
              <h4>默认时间范围</h4>
              <p>图表默认显示的时间范围</p>
            </div>
            <select v-model="preferenceForm.defaultTimeRange"> 
              <option 
                v-for="range in timeRanges"
                :key="range.value" 
                :value="range.value" 
              >
                {{ range.label  }}
              </option>
            </select>
          </div>
        </div>
 
        <div class="preference-group">
          <h3>交易设置</h3>
          <div class="preference-item">
            <div class="preference-info">
              <h4>默认订单类型</h4>
              <p>交易面板默认选择的订单类型</p>
            </div>
            <select v-model="preferenceForm.defaultOrderType"> 
              <option value="limit">限价单</option>
              <option value="market">市价单</option>
            </select>
          </div>
          <div class="preference-item">
            <div class="preference-info">
              <h4>确认对话框</h4>
              <p>执行交易前显示确认对话框</p>
            </div>
            <toggle-switch v-model="preferenceForm.showConfirmDialogs"  />
          </div>
          <div class="preference-item">
            <div class="preference-info">
              <h4>默认杠杆</h4>
              <p>合约交易的默认杠杆倍数</p>
            </div>
            <select v-model="preferenceForm.defaultLeverage"> 
              <option 
                v-for="lev in leverageOptions"
                :key="lev"
                :value="lev"
              >
                {{ lev }}x
              </option>
            </select>
          </div>
        </div>
 
        <div class="form-actions">
          <button class="btn-save" @click="savePreferences">保存偏好</button>
        </div>
      </div>
    </div>
 
    <!-- 更改密码模态框 -->
    <modal 
      v-if="showPasswordModal"
      title="更改密码"
      @close="showPasswordModal = false"
    >
      <form @submit.prevent="changePassword"> 
        <div class="form-group">
          <label>当前密码</label>
          <input 
            type="password" 
            v-model="passwordForm.current" 
            placeholder="输入当前密码"
            required 
          >
        </div>
        <div class="form-group">
          <label>新密码</label>
          <input 
            type="password" 
            v-model="passwordForm.new" 
            placeholder="输入新密码"
            required 
          >
          <password-strength :password="passwordForm.new"  />
        </div>
        <div class="form-group">
          <label>确认新密码</label>
          <input 
            type="password" 
            v-model="passwordForm.confirm" 
            placeholder="再次输入新密码"
            required 
          >
        </div>
        <div class="form-actions">
          <button type="button" class="btn-cancel" @click="showPasswordModal = false">取消</button>
          <button type="submit" class="btn-save">更改密码</button>
        </div>
      </form>
    </modal>
 
    <!-- 创建API密钥模态框 -->
    <modal 
      v-if="showApiKeyModal"
      title="创建API密钥"
      @close="showApiKeyModal = false"
    >
      <form @submit.prevent="createApiKey"> 
        <div class="form-group">
          <label>密钥名称</label>
          <input 
            type="text" 
            v-model="apiKeyForm.name" 
            placeholder="输入密钥名称"
            required
          >
        </div>
        <div class="form-group">
          <label>权限</label>
          <div class="permissions-grid">
            <label 
              v-for="perm in availablePermissions"
              :key="perm.value" 
              class="permission-item"
            >
              <input 
                type="checkbox" 
                v-model="apiKeyForm.permissions" 
                :value="perm.value" 
              >
              <span>{{ perm.label  }}</span>
            </label>
          </div>
        </div>
        <div class="form-group">
          <label>IP限制 (可选)</label>
          <input 
            type="text" 
            v-model="apiKeyForm.ipRestriction" 
            placeholder="例如: 192.168.1.1"
          >
          <p class="hint">留空表示允许任何IP访问</p>
        </div>
        <div class="form-actions">
          <button type="button" class="btn-cancel" @click="showApiKeyModal = false">取消</button>
          <button type="submit" class="btn-save">创建密钥</button>
        </div>
      </form>
    </modal>
  </div>
</template>
 
<script>
import { format } from 'date-fns'
import Modal from '@/components/ui/Modal.vue' 
import ToggleSwitch from '@/components/ui/ToggleSwitch.vue' 
import PasswordStrength from '@/components/ui/PasswordStrength.vue' 
 
export default {
  components: {
    Modal,
    ToggleSwitch,
    PasswordStrength 
  },
  data() {
    return {
      activeTab: 'account',
      tabs: [
        { id: 'account', label: '账户', icon: 'icon-user' },
        { id: 'security', label: '安全', icon: 'icon-lock' },
        { id: 'api', label: 'API', icon: 'icon-key' },
        { id: 'notifications', label: '通知', icon: 'icon-bell' },
        { id: 'preferences', label: '偏好', icon: 'icon-settings' }
      ],
      user: {
        name: '张三',
        email: 'user@example.com', 
        avatar: 'https://i.pravatar.cc/150?img=3' 
      },
      accountForm: {
        name: '张三',
        email: 'user@example.com', 
        avatar: 'https://i.pravatar.cc/150?img=3', 
        avatarPreview: null 
      },
      securityForm: {
        twoFactorEnabled: false 
      },
      twoFactorQRCode: 'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=otpauth://totp/MyApp:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=MyApp', 
      backupCodes: ['ABCD12', 'EFGH34', 'IJKL56', 'MNOP78', 'QRST90'],
      activeSessions: [
        {
          id: 'session1',
          deviceType: 'desktop',
          deviceName: 'MacBook Pro',
          browser: 'Chrome on macOS',
          ip: '192.168.1.100',
          lastActive: Date.now()  - 3600000,
          current: true
        },
        {
          id: 'session2',
          deviceType: 'mobile',
          deviceName: 'iPhone 12',
          browser: 'Safari on iOS',
          ip: '203.0.113.42',
          lastActive: Date.now()  - 86400000,
          current: false 
        }
      ],
      showPasswordModal: false,
      passwordForm: {
        current: '',
        new: '',
        confirm: ''
      },
      apiKeys: [
        {
          id: 'key1',
          name: '交易机器人',
          secret: 'API-KEY-1234567890',
          permissions: ['read', 'trade'],
          createdAt: Date.now()  - 86400000,
          revealed: false
        },
        {
          id: 'key2',
          name: '数据分析',
          secret: 'API-KEY-0987654321',
          permissions: ['read'],
          createdAt: Date.now()  - 259200000,
          revealed: false
        }
      ],
      showApiKeyModal: false,
      apiKeyForm: {
        name: '',
        permissions: ['read'],
        ipRestriction: ''
      },
      availablePermissions: [
        { value: 'read', label: '读取' },
        { value: 'trade', label: '交易' },
        { value: 'withdraw', label: '提现' }
      ],
      notificationForm: {
        email: {
          account: true,
          trading: true,
          alerts: false
        },
        app: {
          sound: true,
          desktop: false 
        },
        sms: {
          enabled: false,
          phone: ''
        }
      },
      preferenceForm: {
        theme: 'dark',
        language: 'zh-CN',
        defaultTimeRange: '1d',
        defaultOrderType: 'limit',
        showConfirmDialogs: true,
        defaultLeverage: 10 
      },
      themes: [
        { value: 'light', label: '浅色' },
        { value: 'dark', label: '深色' },
        { value: 'system', label: '系统' }
      ],
      languages: [
        { code: 'zh-CN', name: '简体中文' },
        { code: 'en-US', name: 'English' },
        { code: 'ja-JP', name: '日本語' }
      ],
      timeRanges: [
        { value: '1h', label: '1小时' },
        { value: '4h', label: '4小时' },
        { value: '1d', label: '1天' },
        { value: '1w', label: '1周' }
      ],
      leverageOptions: [1, 5, 10, 20, 50, 100]
    }
  },
  methods: {
    formatTime(timestamp, formatStr = 'yyyy-MM-dd HH:mm') {
      return format(new Date(timestamp), formatStr)
    },
    handleAvatarUpload(event) {
      const file = event.target.files[0] 
      if (file) {
        const reader = new FileReader()
        reader.onload  = (e) => {
          this.accountForm.avatarPreview  = e.target.result  
        }
        reader.readAsDataURL(file) 
      }
    },
    removeAvatar() {
      this.accountForm.avatarPreview  = null
      this.accountForm.avatar  = ''
    },
    updateAccount() {
      // 实际项目中这里应该是API调用
      this.user.name  = this.accountForm.name 
      this.user.email  = this.accountForm.email 
      if (this.accountForm.avatarPreview)  {
        this.user.avatar  = this.accountForm.avatarPreview 
      }
      
      this.$notify({
        title: '更新成功',
        message: '账户信息已更新',
        type: 'success'
      })
    },
    changePassword() {
      if (this.passwordForm.new  !== this.passwordForm.confirm)  {
        this.$notify.error({ 
          title: '错误',
          message: '新密码不匹配'
        })
        return 
      }
      
      // 实际项目中这里应该是API调用
      console.log('Changing  password...')
      
      this.showPasswordModal  = false
      this.passwordForm  = {
        current: '',
        new: '',
        confirm: ''
      }
      
      this.$notify({
        title: '密码已更改',
        message: '您的密码已成功更新',
        type: 'success'
      })
    },
    updateTwoFactor(enabled) {
      // 实际项目中这里应该是API调用 
      console.log(`Two-factor  auth ${enabled ? 'enabled' : 'disabled'}`)
      
      if (enabled) {
        this.$notify({
          title: '双重验证已启用',
          message: '请扫描二维码设置验证器应用',
          type: 'success'
        })
      }
    },
    generateBackupCodes() {
      // 生成新的备用代码
      this.backupCodes  = Array.from({  length: 5 }, () => {
        return Math.random().toString(36).substring(2,  8).toUpperCase()
      })
      
      this.$notify({
        title: '备用代码已更新',
        message: '请保存您的新备用代码',
        type: 'warning'
      })
    },
    revokeSession(sessionId) {
      // 实际项目中这里应该是API调用 
      this.activeSessions  = this.activeSessions.filter(s  => s.id  !== sessionId)
      
      this.$notify({
        title: '会话已撤销',
        message: '设备访问权限已被撤销',
        type: 'success'
      })
    },
    createApiKey() {
      // 实际项目中这里应该是API调用 
      const newKey = {
        id: `key-${Date.now()}`, 
        name: this.apiKeyForm.name, 
        secret: `API-KEY-${Math.random().toString(36).substring(2,  12).toUpperCase()}`,
        permissions: [...this.apiKeyForm.permissions], 
        createdAt: Date.now(), 
        revealed: true
      }
      
      this.apiKeys.unshift(newKey) 
      this.showApiKeyModal  = false 
      this.apiKeyForm  = {
        name: '',
        permissions: ['read'],
        ipRestriction: ''
      }
      
      this.$notify({
        title: 'API密钥已创建',
        message: '请妥善保存您的密钥',
        type: 'success'
      })
    },
    showApiKey(key) {
      key.revealed  = true 
    },
    copyToClipboard(text) {
      navigator.clipboard.writeText(text) 
      this.$notify({
        title: '已复制',
        message: 'API密钥已复制到剪贴板',
        type: 'success'
      })
    },
    deleteApiKey(keyId) {
      this.$confirm('确定要删除此API密钥吗?', '警告', {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        // 实际项目中这里应该是API调用 
        this.apiKeys  = this.apiKeys.filter(k  => k.id  !== keyId)
        
        this.$notify({
          title: '已删除',
          message: 'API密钥已成功删除',
          type: 'success'
        })
      })
    },
    saveNotificationSettings() {
      // 实际项目中这里应该是API调用
      this.$notify({
        title: '保存成功',
        message: '通知设置已更新',
        type: 'success'
      })
    },
    savePreferences() {
      // 实际项目中这里应该是API调用 
      this.$store.dispatch('updatePreferences',  this.preferenceForm) 
      
      this.$notify({
        title: '保存成功',
        message: '偏好设置已更新',
        type: 'success'
      })
    }
  }
}
</script>
 
<style scoped>
.settings-container {
  display: flex;
  height: 100%;
  background: #1e1e2d;
  color: #e0e0e0;
}
 
.settings-nav {
  width: 240px;
  padding: 20px;
  border-right: 1px solid #3a3a4c;
  display: flex;
  flex-direction: column;
}
 
.profile-header {
  display: flex;
  align-items: center;
  margin-bottom: 30px;
}
 
.avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  overflow: hidden;
  margin-right: 15px;
}
 
.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
 
.profile-info h3 {
  margin: 0 0 5px;
  font-size: 16px;
}
 
.profile-info p {
  margin: 0;
  font-size: 14px;
  color: #b8b8d1;
}
 
.settings-nav nav {
  display: flex;
  flex-direction: column;
}
 
.settings-nav button {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  margin-bottom: 8px;
  background: none;
  border: none;
  color: #b8b8d1;
  text-align: left;
  border-radius: 6px;
  cursor: pointer;
}
 
.settings-nav button i {
  margin-right: 12px;
  width: 20px;
  height: 20px;
  display: inline-block;
}
 
.settings-nav button.active  {
  background: #6e45e2;
  color: white;
}
 
.settings-nav button:hover:not(.active) {
  background: #3a3a4c;
}
 
.settings-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}
 
.settings-section {
  max-width: 800px;
  margin: 0 auto;
}
 
.settings-section h2 {
  margin: 0 0 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #3a3a4c;
}
 
.form-group {
  margin-bottom: 20px;
}
 
.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: #b8b8d1;
}
 
.form-group input {
  width: 100%;
  background: #3a3a4c;
  border: 1px solid #4a4a5c;
  color: white;
  padding: 10px 12px;
  border-radius: 6px;
}
 
.form-group input[type="email"],
.form-group input[type="password"],
.form-group input[type="tel"] {
  /* 确保所有输入框样式一致 */
}
 
.avatar-upload {
  display: flex;
  align-items: center;
}
 
.avatar-upload img {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
  margin-right: 20px;
}
 
.upload-controls {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
 
.btn-upload, .btn-remove {
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
}
 
.btn-upload {
  background: #6e45e2;
  color: white;
  border: none;
}
 
.btn-remove {
  background: none;
  border: 1px solid #ff4757;
  color: #ff4757;
}
 
.form-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 30px;
}
 
.btn-save {
  background: #6e45e2;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
}
 
.btn-save:hover {
  background: #8a63f2;
}
 
.btn-cancel {
  background: #3a3a4c;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  margin-right: 10px;
}
 
.btn-cancel:hover {
  background: #4a4a5c;
}
 
.security-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid #3a3a4c;
}
 
.security-info h4 {
  margin: 0 0 4px;
  font-size: 15px;
}
 
.security-info p {
  margin: 0;
  font-size: 13px;
  color: #b8b8d1;
}
 
.btn-change {
  background: none;
  border: 1px solid #6e45e2;
  color: #6e45e2;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
}
 
.btn-change:hover {
  background: rgba(110, 69, 226, 0.1);
}
 
.two-factor-setup {
  background: #2a2a3c;
  border-radius: 8px;
  padding: 20px;
  margin: 20px 0;
  display: flex;
  gap: 30px;
}
 
.qr-code {
  width: 200px;
  height: 200px;
  background: white;
  padding: 10px;
  border-radius: 8px;
}
 
.qr-code img {
  width: 100%;
  height: 100%;
}
 
.backup-codes {
  flex: 1;
}
 
.backup-codes h4 {
  margin: 0 0 8px;
}
 
.backup-codes p {
  margin: 0 0 16px;
  color: #b8b8d1;
  font-size: 14px;
}
 
.codes-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 20px;
}
 
.code-item {
  background: #3a3a4c;
  padding: 10px;
  text-align: center;
  font-family: monospace;
  font-size: 18px;
  border-radius: 4px;
}
 
.btn-regenerate {
  background: none;
  border: 1px solid #ffa502;
  color: #ffa502;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
}
 
.btn-regenerate:hover {
  background: rgba(255, 165, 2, 0.1);
}
 
.sessions-list {
  margin-top: 20px;
}
 
.session-item {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #3a3a4c;
}
 
.session-icon {
  width: 40px;
  height: 40px;
  background: #3a3a4c;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
}
 
.session-icon i {
  font-size: 20px;
}
 
.session-details {
  flex: 1;
}
 
.session-device {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}
 
.session-device strong {
  margin-right: 8px;
}
 
.current-label {
  background: rgba(0, 230, 118, 0.2);
  color: #00e676;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}
 
.session-info {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #b8b8d1;
}
 
.btn-revoke {
  background: none;
  border: 1px solid #ff4757;
  color: #ff4757;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
 
.btn-revoke:hover {
  background: rgba(255, 71, 87, 0.1);
}
 
.api-description {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
 
.btn-create {
  background: #6e45e2;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
}
 
.btn-create i {
  margin-right: 6px;
}
 
.api-keys-list {
  background: #2a2a3c;
  border-radius: 8px;
  overflow: hidden;
}
 
.api-key-item {
  display: flex;
  justify-content:
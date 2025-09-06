<template>
  <div class="risk-control">
    <!-- 风险控制头部 -->
    <div class="risk-header">
      <h2><i class="icon-shield"></i> 风险控制中心</h2>
      <div class="risk-status" :class="overallStatus">
        {{ riskStatusText }}
        <span class="last-updated">
          最后更新: {{ lastUpdated }}
        </span>
      </div>
    </div>
 
    <!-- 风险控制仪表盘 -->
    <div class="risk-dashboard">
      <!-- 风险概况卡片 -->
      <div class="dashboard-card overview">
        <h3>风险概况</h3>
        <div class="risk-meters">
          <div class="meter-group">
            <div class="meter-label">账户风险度</div>
            <div class="meter-container">
              <radial-meter 
                :value="riskMetrics.accountRisk  * 100" 
                :max="100"
                :thresholds="[30, 70]"
                unit="%"
              />
            </div>
          </div>
          <div class="meter-group">
            <div class="meter-label">组合波动率</div>
            <div class="meter-container">
              <radial-meter 
                :value="riskMetrics.portfolioVolatility  * 100"
                :max="50"
                :thresholds="[15, 30]"
                unit="%"
              />
            </div>
          </div>
          <div class="meter-group">
            <div class="meter-label">最大回撤</div>
            <div class="meter-container">
              <radial-meter 
                :value="riskMetrics.maxDrawdown  * 100"
                :max="100"
                :thresholds="[20, 50]"
                unit="%"
              />
            </div>
          </div>
        </div>
      </div>
 
      <!-- 实时风险警报 -->
      <div class="dashboard-card alerts">
        <h3>实时风险警报</h3>
        <div class="alert-list">
          <div 
            v-for="(alert, index) in activeAlerts" 
            :key="index"
            class="alert-item"
            :class="alert.level" 
          >
            <div class="alert-icon">
              <i :class="alertIcon(alert.level)"></i> 
            </div>
            <div class="alert-content">
              <div class="alert-title">{{ alert.title  }}</div>
              <div class="alert-message">{{ alert.message  }}</div>
              <div class="alert-time">{{ formatTime(alert.timestamp)  }}</div>
            </div>
            <button 
              class="alert-dismiss"
              @click="dismissAlert(index)"
            >
              &times;
            </button>
          </div>
          <div v-if="activeAlerts.length  === 0" class="no-alerts">
            <i class="icon-check"></i> 当前无风险警报 
          </div>
        </div>
      </div>
 
      <!-- 风险控制规则配置 -->
      <div class="dashboard-card rules-config">
        <h3>风险控制规则</h3>
        <div class="tabs">
          <button 
            v-for="tab in tabs" 
            :key="tab.id" 
            :class="{ active: activeTab === tab.id  }"
            @click="activeTab = tab.id" 
          >
            {{ tab.label  }}
          </button>
        </div>
 
        <!-- 账户级风险规则 -->
        <div v-show="activeTab === 'account'" class="rule-group">
          <div class="rule-item">
            <div class="rule-info">
              <h4>最大账户风险度</h4>
              <p>当账户风险度超过阈值时暂停交易</p>
            </div>
            <div class="rule-controls">
              <toggle-switch 
                v-model="accountRules.maxRiskEnabled" 
              />
              <input 
                type="number" 
                v-model.number="accountRules.maxRiskThreshold" 
                min="0"
                max="100"
                step="1"
                :disabled="!accountRules.maxRiskEnabled" 
              >
              <span>%</span>
            </div>
          </div>
 
          <div class="rule-item">
            <div class="rule-info">
              <h4>单日最大亏损</h4>
              <p>当日累计亏损达到阈值时停止交易</p>
            </div>
            <div class="rule-controls">
              <toggle-switch 
                v-model="accountRules.dailyLossEnabled" 
              />
              <input 
                type="number" 
                v-model.number="accountRules.dailyLossThreshold" 
                min="0"
                step="0.5"
                :disabled="!accountRules.dailyLossEnabled" 
              >
              <span>{{ quoteCurrency }}</span>
            </div>
          </div>
        </div>
 
        <!-- 策略级风险规则 -->
        <div v-show="activeTab === 'strategy'" class="rule-group">
          <div class="rule-item">
            <div class="rule-info">
              <h4>单策略最大回撤</h4>
              <p>策略回撤超过阈值时自动停止</p>
            </div>
            <div class="rule-controls">
              <toggle-switch 
                v-model="strategyRules.maxDrawdownEnabled" 
              />
              <input 
                type="number" 
                v-model.number="strategyRules.maxDrawdownThreshold" 
                min="0"
                max="100"
                step="1"
                :disabled="!strategyRules.maxDrawdownEnabled" 
              >
              <span>%</span>
            </div>
          </div>
 
          <div class="rule-item">
            <div class="rule-info">
              <h4>连续亏损次数</h4>
              <p>策略连续亏损达到阈值时暂停</p>
            </div>
            <div class="rule-controls">
              <toggle-switch 
                v-model="strategyRules.consecutiveLossesEnabled" 
              />
              <input 
                type="number" 
                v-model.number="strategyRules.consecutiveLossesThreshold" 
                min="1"
                step="1"
                :disabled="!strategyRules.consecutiveLossesEnabled" 
              >
              <span>次</span>
            </div>
          </div>
        </div>
 
        <!-- 交易级风险规则 -->
        <div v-show="activeTab === 'trade'" class="rule-group">
          <div class="rule-item">
            <div class="rule-info">
              <h4>单笔最大风险</h4>
              <p>限制单笔交易占用保证金比例</p>
            </div>
            <div class="rule-controls">
              <toggle-switch 
                v-model="tradeRules.perTradeRiskEnabled" 
              />
              <input 
                type="number" 
                v-model.number="tradeRules.perTradeRiskThreshold" 
                min="0"
                max="100"
                step="1"
                :disabled="!tradeRules.perTradeRiskEnabled" 
              >
              <span>%</span>
            </div>
          </div>
 
          <div class="rule-item">
            <div class="rule-info">
              <h4>最大杠杆倍数</h4>
              <p>限制策略可使用的最大杠杆</p>
            </div>
            <div class="rule-controls">
              <toggle-switch 
                v-model="tradeRules.maxLeverageEnabled" 
              />
              <input 
                type="number" 
                v-model.number="tradeRules.maxLeverageThreshold" 
                min="1"
                max="100"
                step="1"
                :disabled="!tradeRules.maxLeverageEnabled" 
              >
              <span>倍</span>
            </div>
          </div>
        </div>
 
        <div class="rule-actions">
          <button 
            class="btn-reset"
            @click="resetRules"
          >
            恢复默认 
          </button>
          <button 
            class="btn-save"
            @click="saveRules"
          >
            保存设置 
          </button>
        </div>
      </div>
 
      <!-- 风险事件历史 -->
      <div class="dashboard-card history">
        <h3>风险事件历史</h3>
        <div class="history-controls">
          <select v-model="historyFilter">
            <option value="all">全部事件</option>
            <option value="triggered">已触发规则</option>
            <option value="warning">警告事件</option>
          </select>
          <span class="show-count">
            显示 {{ filteredHistory.length  }} 条记录 
          </span>
        </div>
        <div class="history-list">
          <div 
            v-for="(event, index) in paginatedHistory" 
            :key="index"
            class="history-item"
            :class="event.level" 
          >
            <div class="event-time">{{ formatTime(event.timestamp)  }}</div>
            <div class="event-type">{{ event.type  }}</div>
            <div class="event-message">{{ event.message  }}</div>
            <div class="event-action">{{ event.action  }}</div>
          </div>
          <div v-if="filteredHistory.length  === 0" class="no-history">
            暂无历史记录 
          </div>
        </div>
        <div class="history-pagination">
          <button 
            v-for="page in pageNumbers" 
            :key="page"
            :class="{ active: currentPage === page }"
            @click="currentPage = page"
          >
            {{ page }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
 
<script>
import RadialMeter from '@/components/charts/RadialMeter.vue' 
import ToggleSwitch from '@/components/ui/ToggleSwitch.vue' 
import { format } from 'date-fns'
 
export default {
  components: {
    RadialMeter,
    ToggleSwitch 
  },
  data() {
    return {
      activeTab: 'account',
      tabs: [
        { id: 'account', label: '账户级' },
        { id: 'strategy', label: '策略级' },
        { id: 'trade', label: '交易级' }
      ],
      accountRules: {
        maxRiskEnabled: true,
        maxRiskThreshold: 30,
        dailyLossEnabled: true,
        dailyLossThreshold: 1000
      },
      strategyRules: {
        maxDrawdownEnabled: true,
        maxDrawdownThreshold: 20,
        consecutiveLossesEnabled: true,
        consecutiveLossesThreshold: 5 
      },
      tradeRules: {
        perTradeRiskEnabled: true,
        perTradeRiskThreshold: 5,
        maxLeverageEnabled: true,
        maxLeverageThreshold: 10
      },
      riskMetrics: {
        accountRisk: 0.15,
        portfolioVolatility: 0.12,
        maxDrawdown: 0.08
      },
      activeAlerts: [
        {
          level: 'warning',
          title: 'ETH/USDT 策略回撤超过15%',
          message: '当前回撤15.8%，接近最大阈值20%',
          timestamp: Date.now()  - 3600000
        },
        {
          level: 'critical',
          title: '账户风险度达到25%',
          message: '当前账户风险度25.3%，建议降低仓位',
          timestamp: Date.now()  - 1800000
        }
      ],
      riskHistory: [
        {
          level: 'triggered',
          type: '账户风控',
          message: '触发单日最大亏损限制 (1000 USDT)',
          action: '已暂停所有交易',
          timestamp: Date.now()  - 86400000
        },
        // 更多历史记录...
      ],
      historyFilter: 'all',
      currentPage: 1,
      itemsPerPage: 5,
      lastUpdated: format(new Date(), 'HH:mm:ss')
    }
  },
  computed: {
    quoteCurrency() {
      return this.$store.getters.account?.quoteCurrency  || 'USDT'
    },
    overallStatus() {
      if (this.activeAlerts.some(a  => a.level  === 'critical')) return 'critical'
      if (this.activeAlerts.some(a  => a.level  === 'warning')) return 'warning'
      return 'safe'
    },
    riskStatusText() {
      switch (this.overallStatus)  {
        case 'critical': return '高风险状态'
        case 'warning': return '风险警告'
        default: return '风险可控'
      }
    },
    filteredHistory() {
      if (this.historyFilter  === 'all') return this.riskHistory  
      return this.riskHistory.filter(e  => e.level  === this.historyFilter) 
    },
    paginatedHistory() {
      const start = (this.currentPage  - 1) * this.itemsPerPage 
      return this.filteredHistory.slice(start,  start + this.itemsPerPage) 
    },
    pageNumbers() {
      const pages = Math.ceil(this.filteredHistory.length  / this.itemsPerPage) 
      return Array.from({  length: pages }, (_, i) => i + 1)
    }
  },
  methods: {
    formatTime(timestamp) {
      return format(new Date(timestamp), 'MM/dd HH:mm:ss')
    },
    alertIcon(level) {
      return {
        warning: 'icon-warning',
        critical: 'icon-error'
      }[level] || 'icon-info'
    },
    dismissAlert(index) {
      this.activeAlerts.splice(index,  1)
    },
    saveRules() {
      const rules = {
        account: this.accountRules, 
        strategy: this.strategyRules, 
        trade: this.tradeRules  
      }
      
      this.$store.dispatch('saveRiskRules',  rules).then(() => {
        this.$notify({
          title: '保存成功',
          message: '风险控制规则已更新',
          type: 'success'
        })
      }).catch(err => {
        this.$notify.error({ 
          title: '保存失败',
          message: err.message  
        })
      })
    },
    resetRules() {
      this.$confirm('确定恢复默认风险控制规则吗?', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.loadDefaultRules() 
        this.$notify({
          title: '已重置',
          message: '风险规则已恢复默认值',
          type: 'success'
        })
      })
    },
    loadDefaultRules() {
      const defaultRules = this.$store.getters.defaultRiskRules 
      this.accountRules  = { ...defaultRules.account  }
      this.strategyRules  = { ...defaultRules.strategy  }
      this.tradeRules  = { ...defaultRules.trade  }
    },
    updateRiskMetrics() {
      this.$socket.subscribeRiskMetrics(data  => {
        this.riskMetrics  = data
        this.lastUpdated  = format(new Date(), 'HH:mm:ss')
        
        // 检查风险警报 
        this.checkRiskAlerts(data) 
      })
    }
  },
  created() {
    this.updateRiskMetrics() 
  }
}
</script>
 
<style scoped>
.risk-control {
  padding: 20px;
  background: #1e1e2d;
  color: #e0e0e0;
  height: 100%;
  display: flex;
  flex-direction: column;
}
 
.risk-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #3a3a4c;
}
 
.risk-header h2 {
  margin: 0;
  font-size: 24px;
  display: flex;
  align-items: center;
  gap: 10px;
}
 
.icon-shield {
  display: inline-block;
  width: 24px;
  height: 24px;
  background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg"  viewBox="0 0 24 24" fill="%236e45e2"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11V11.99z"/></svg>');
}
 
.risk-status {
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: bold;
  display: flex;
  align-items: center;
  gap: 10px;
}
 
.risk-status.safe  {
  background: rgba(0, 230, 118, 0.2);
  color: #00e676;
}
 
.risk-status.warning  {
  background: rgba(255, 165, 2, 0.2);
  color: #ffa502;
}
 
.risk-status.critical  {
  background: rgba(255, 71, 87, 0.2);
  color: #ff4757;
}
 
.last-updated {
  font-size: 12px;
  opacity: 0.8;
  font-weight: normal;
}
 
.risk-dashboard {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto auto;
  gap: 16px;
}
 
.dashboard-card {
  background: #2a2a3c;
  border-radius: 8px;
  padding: 16px;
}
 
.dashboard-card h3 {
  margin: 0 0 16px;
  color: white;
}
 
.overview {
  grid-column: 1;
  grid-row: 1;
}
 
.alerts {
  grid-column: 2;
  grid-row: 1;
}
 
.rules-config {
  grid-column: 1;
  grid-row: 2;
}
 
.history {
  grid-column: 2;
  grid-row: 2;
}
 
.risk-meters {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}
 
.meter-group {
  display: flex;
  flex-direction: column;
  align-items: center;
}
 
.meter-label {
  font-size: 14px;
  color: #b8b8d1;
  margin-bottom: 8px;
}
 
.meter-container {
  width: 100%;
  height: 120px;
}
 
.alert-list {
  max-height: 300px;
  overflow-y: auto;
}
 
.alert-item {
  display: flex;
  align-items: center;
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 6px;
}
 
.alert-item.warning  {
  background: rgba(255, 165, 2, 0.1);
  border-left: 3px solid #ffa502;
}
 
.alert-item.critical  {
  background: rgba(255, 71, 87, 0.1);
  border-left: 3px solid #ff4757;
}
 
.alert-icon {
  width: 24px;
  height: 24px;
  margin-right: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}
 
.icon-warning {
  display: inline-block;
  width: 20px;
  height: 20px;
  background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg"  viewBox="0 0 24 24" fill="%23ffa502"><path d="M12 2L1 21h22L12 2zm0 3.5L19.5 19h-15L12 5.5zM11 10v4h2v-4h-2zm0 6v2h2v-2h-2z"/></svg>');
}
 
.icon-error {
  display: inline-block;
  width: 20px;
  height: 20px;
  background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg"  viewBox="0 0 24 24" fill="%23ff4757"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm1-13h-2v6h2V7zm0 8h-2v2h2v-2z"/></svg>');
}
 
.alert-content {
  flex: 1;
}
 
.alert-title {
  font-weight: bold;
  margin-bottom: 4px;
}
 
.alert-message {
  font-size: 13px;
  color: #b8b8d1;
}
 
.alert-time {
  font-size: 12px;
  color: #6a6a7c;
  margin-top: 4px;
}
 
.alert-dismiss {
  background: none;
  border: none;
  color: #6a6a7c;
  font-size: 20px;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
}
 
.alert-dismiss:hover {
  color: #ff4757;
}
 
.no-alerts {
  padding: 20px;
  text-align: center;
  color: #6a6a7c;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
 
.icon-check {
  display: inline-block;
  width: 24px;
  height: 24px;
  background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg"  viewBox="0 0 24 24" fill="%2300e676"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/></svg>');
}
 
.tabs {
  display: flex;
  border-bottom: 1px solid #3a3a4c;
  margin-bottom: 16px;
}
 
.tabs button {
  background: none;
  border: none;
  padding: 8px 16px;
  cursor: pointer;
  color: #b8b8d1;
  position: relative;
}
 
.tabs button.active  {
  color: white;
  font-weight: bold;
}
 
.tabs button.active::after  {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 2px;
  background: #6e45e2;
}
 
.rule-group {
  margin-bottom: 20px;
}
 
.rule-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #3a3a4c;
}
 
.rule-info h4 {
  margin: 0 0 4px;
  font-size: 14px;
}
 
.rule-info p {
  margin: 0;
  font-size: 12px;
  color: #b8b8d1;
}
 
.rule-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}
 
.rule-controls input {
  width: 80px;
  background: #3a3a4c;
  border: 1px solid #4a4a5c;
  color: white;
  padding: 6px 8px;
  border-radius: 4px;
  text-align: right;
}
 
.rule-controls span {
  font-size: 14px;
  color: #b8b8d1;
}
 
.rule-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}
 
.btn-reset {
  background: #3a3a4c;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}
 
.btn-reset:hover {
  background: #4a4a5c;
}
 
.btn-save {
  background: #6e45e2;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
}
 
.btn-save:hover {
  background: #8a63f2;
}
 
.history-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
 
.history-controls select {
  background: #3a3a4c;
  border: 1px solid #4a4a5c;
  color: white;
  padding: 6px 12px;
  border-radius: 4px;
}
 
.show-count {
  font-size: 12px;
  color: #6a6a7c;
}
 
.history-list {
  max-height: 300px;
  overflow-y: auto;
}
 
.history-item {
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 4px;
  font-size: 13px;
  display: grid;
  grid-template-columns: 120px 100px 1fr 80px;
  gap: 10px;
  align-items: center;
}
 
.history-item.triggered  {
  background: rgba(255, 71, 87, 0.1);
}
 
.history-item.warning  {
  background: rgba(255, 165, 2, 0.1);
}
 
.event-time {
  color: #b8b8d1;
}
 
.event-type {
  font-weight: bold;
}
 
.event-action {
  text-align: right;
  color: #6e45e2;
}
 
.no-history {
  padding: 20px;
  text-align: center;
  color: #6a6a7c;
}
 
.history-pagination {
  display: flex;
  justify-content: center;
  gap: 4px;
  margin-top: 12px;
}
 
.history-pagination button {
  background: #3a3a4c;
  border: none;
  color: white;
  width: 30px;
  height: 30px;
  border-radius: 4px;
  cursor: pointer;
}
 
.history-pagination button.active  {
  background: #6e45e2;
  font-weight: bold;
}
 
/* 暗黑模式适配 */
@media (prefers-color-scheme: dark) {
  .risk-control {
    background: #1e1e2d;
  }
 
  .dashboard-card {
    background: #252537;
  }
 
  .rule-controls input {
    background: #323248;
    border-color: #424258;
  }
 
  .tabs {
    border-color: #424258;
  }
 
  .rule-item {
    border-color: #424258;
  }
}
 
/* 响应式布局 */
@media (max-width: 1200px) {
  .risk-dashboard {
    grid-template-columns: 1fr;
  }
 
  .overview {
    grid-column: 1;
    grid-row: 1;
  }
 
  .alerts {
    grid-column: 1;
    grid-row: 2;
  }
 
  .rules-config {
    grid-column: 1;
    grid-row: 3;
  }
 
  .history {
    grid-column: 1;
    grid-row: 4;
  }
}
 
@media (max-width: 768px) {
  .risk-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
 
  .risk-meters {
    grid-template-columns: 1fr;
  }
 
  .history-item {
    grid-template-columns: 1fr;
    gap: 4px;
  }
 
  .event-action {
    text-align: left;
  }
}
</style>
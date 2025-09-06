<template>
  <div class="dashboard-container">
    <!-- 顶部状态栏 -->
    <div class="status-bar">
      <div class="connection-status" :class="connectionStatus">
        <i class="status-icon"></i>
        {{ connectionText }}
      </div>
      <div class="last-update">
        最后更新: {{ formatTime(lastUpdate) }}
      </div>
      <div class="market-status">
        <span class="market-indicator" :class="marketTrend">
          {{ marketStatusText }}
        </span>
        <span class="btc-price">
          BTC: ${{ btcPrice.toLocaleString()  }}
          <span :class="btcChange >= 0 ? 'up' : 'down'">
            ({{ btcChange >= 0 ? '+' : '' }}{{ btcChange.toFixed(2)  }}%)
          </span>
        </span>
      </div>
    </div>
 
    <!-- 主仪表盘 -->
    <div class="dashboard-grid">
      <!-- 资产概览 -->
      <div class="card asset-overview">
        <div class="card-header">
          <h3>资产概览</h3>
          <div class="time-range">
            <button 
              v-for="range in timeRanges" 
              :key="range"
              :class="{ active: activeRange === range }"
              @click="changeTimeRange(range)"
            >
              {{ range }}
            </button>
          </div>
        </div>
        <div class="card-body">
          <div class="balance-summary">
            <div class="total-value">
              <span class="label">总资产价值</span>
              <span class="value">{{ totalValue.toLocaleString()  }} USD</span>
            </div>
            <div class="balance-change">
              <span class="label">24小时变化</span>
              <span :class="['value', balanceChange >= 0 ? 'up' : 'down']">
                {{ balanceChange >= 0 ? '+' : '' }}{{ balanceChange.toFixed(2)  }}%
              </span>
            </div>
          </div>
          <div class="asset-distribution">
            <pie-chart 
              :data="assetDistribution"
              :options="chartOptions"
            />
          </div>
          <div class="asset-list">
            <div 
              v-for="asset in filteredAssets" 
              :key="asset.symbol" 
              class="asset-item"
            >
              <div class="asset-info">
                <span class="symbol">{{ asset.symbol  }}</span>
                <span class="name">{{ asset.name  }}</span>
              </div>
              <div class="asset-values">
                <span class="amount">{{ asset.amount.toFixed(4)  }}</span>
                <span class="value">{{ asset.value.toLocaleString()  }} USD</span>
              </div>
              <div 
                class="asset-change"
                :class="asset.change24h  >= 0 ? 'up' : 'down'"
              >
                {{ asset.change24h  >= 0 ? '+' : '' }}{{ asset.change24h.toFixed(2)  }}%
              </div>
            </div>
          </div>
        </div>
      </div>
 
      <!-- 策略绩效 -->
      <div class="card strategy-performance">
        <div class="card-header">
          <h3>策略绩效</h3>
          <select v-model="selectedStrategy">
            <option 
              v-for="strategy in strategies" 
              :key="strategy.id" 
              :value="strategy.id" 
            >
              {{ strategy.name  }}
            </option>
          </select>
        </div>
        <div class="card-body">
          <div class="performance-metrics">
            <div class="metric">
              <span class="label">总收益率</span>
              <span 
                class="value"
                :class="currentStrategy.return  >= 0 ? 'up' : 'down'"
              >
                {{ (currentStrategy.return  * 100).toFixed(2) }}%
              </span>
            </div>
            <div class="metric">
              <span class="label">夏普比率</span>
              <span class="value">
                {{ currentStrategy.sharpe.toFixed(2)  }}
              </span>
            </div>
            <div class="metric">
              <span class="label">最大回撤</span>
              <span class="value down">
                {{ (currentStrategy.drawdown  * 100).toFixed(2) }}%
              </span>
            </div>
            <div class="metric">
              <span class="label">胜率</span>
              <span class="value">
                {{ (currentStrategy.winRate  * 100).toFixed(2) }}%
              </span>
            </div>
          </div>
          <div class="equity-chart">
            <line-chart 
              :data="equityData"
              :options="equityChartOptions"
            />
          </div>
        </div>
      </div>
 
      <!-- 市场动态 -->
      <div class="card market-movers">
        <div class="card-header">
          <h3>市场动态</h3>
          <div class="market-tabs">
            <button 
              v-for="tab in marketTabs" 
              :key="tab"
              :class="{ active: activeMarketTab === tab }"
              @click="activeMarketTab = tab"
            >
              {{ tab }}
            </button>
          </div>
        </div>
        <div class="card-body">
          <div class="market-table">
            <div class="table-header">
              <div class="col-symbol">交易对</div>
              <div class="col-price">价格</div>
              <div class="col-change">24h涨跌</div>
              <div class="col-volume">成交量</div>
              <div class="col-action">操作</div>
            </div>
            <div 
              v-for="item in marketData" 
              :key="item.symbol" 
              class="table-row"
            >
              <div class="col-symbol">
                <span class="base">{{ item.base  }}</span>
                <span class="quote">/{{ item.quote  }}</span>
              </div>
              <div class="col-price">
                {{ item.price.toLocaleString()  }}
              </div>
              <div 
                class="col-change"
                :class="item.change  >= 0 ? 'up' : 'down'"
              >
                {{ item.change  >= 0 ? '+' : '' }}{{ item.change.toFixed(2)  }}%
              </div>
              <div class="col-volume">
                {{ formatVolume(item.volume)  }}
              </div>
              <div class="col-action">
                <button 
                  class="trade-btn"
                  @click="openTradePanel(item.symbol)" 
                >
                  交易
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
 
      <!-- 实时交易 -->
      <div class="card live-trades">
        <div class="card-header">
          <h3>实时交易</h3>
          <div class="view-actions">
            <button @click="showAllTrades">查看全部</button>
          </div>
        </div>
        <div class="card-body">
          <div class="trades-list">
            <div 
              v-for="trade in recentTrades" 
              :key="trade.id" 
              class="trade-item"
              :class="trade.side" 
            >
              <div class="trade-time">
                {{ formatTime(trade.timestamp,  'HH:mm:ss') }}
              </div>
              <div class="trade-pair">
                {{ trade.symbol  }}
              </div>
              <div class="trade-side">
                <span :class="trade.side"> 
                  {{ trade.side  === 'buy' ? '买入' : '卖出' }}
                </span>
              </div>
              <div class="trade-price">
                {{ trade.price.toFixed(4)  }}
              </div>
              <div class="trade-amount">
                {{ trade.amount.toFixed(4)  }}
              </div>
              <div class="trade-value">
                {{ (trade.price  * trade.amount).toFixed(2)  }} USD 
              </div>
            </div>
          </div>
        </div>
      </div>
 
      <!-- 风险监控 -->
      <div class="card risk-monitor">
        <div class="card-header">
          <h3>风险监控</h3>
          <div class="risk-level" :class="riskLevel">
            {{ riskLevelText }}
          </div>
        </div>
        <div class="card-body">
          <div class="risk-indicators">
            <div class="indicator">
              <div class="gauge-container">
                <radial-gauge 
                  :value="riskMetrics.accountRisk  * 100"
                  :max="100"
                  :thresholds="[30, 70]"
                  label="账户风险度"
                />
              </div>
            </div>
            <div class="indicator">
              <div class="gauge-container">
                <radial-gauge 
                  :value="riskMetrics.portfolioVolatility  * 100"
                  :max="50"
                  :thresholds="[15, 30]"
                  label="组合波动率"
                />
              </div>
            </div>
          </div>
          <div class="risk-alerts">
            <div 
              v-for="(alert, index) in activeAlerts" 
              :key="index"
              class="alert-item"
              :class="alert.level" 
            >
              <i class="alert-icon"></i>
              <div class="alert-message">{{ alert.message  }}</div>
              <button 
                class="alert-dismiss"
                @click="dismissAlert(index)"
              >
                &times;
              </button>
            </div>
            <div v-if="activeAlerts.length  === 0" class="no-alerts">
              当前无风险警报 
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
 
<script>
import { format } from 'date-fns'
import PieChart from '@/components/charts/PieChart.vue' 
import LineChart from '@/components/charts/LineChart.vue' 
import RadialGauge from '@/components/charts/RadialGauge.vue' 
 
export default {
  components: {
    PieChart,
    LineChart,
    RadialGauge
  },
  data() {
    return {
      connectionStatus: 'connected',
      lastUpdate: Date.now(), 
      marketTrend: 'up',
      btcPrice: 42356.78,
      btcChange: 2.34,
      activeRange: '24H',
      timeRanges: ['24H', '1W', '1M', '1Y'],
      totalValue: 12543.21,
      balanceChange: 1.23,
      assets: [
        { symbol: 'BTC', name: 'Bitcoin', amount: 0.25, value: 10589.20, change24h: 2.34 },
        { symbol: 'ETH', name: 'Ethereum', amount: 5.2, value: 1254.32, change24h: -1.56 },
        { symbol: 'USDT', name: 'Tether', amount: 500, value: 500, change24h: 0 },
        { symbol: 'SOL', name: 'Solana', amount: 15, value: 1200, change24h: 5.67 }
      ],
      selectedStrategy: 'strategy1',
      strategies: [
        { id: 'strategy1', name: '趋势跟踪策略', return: 0.125, sharpe: 1.8, drawdown: 0.15, winRate: 0.65 },
        { id: 'strategy2', name: '均值回归策略', return: 0.082, sharpe: 1.2, drawdown: 0.08, winRate: 0.72 }
      ],
      activeMarketTab: '涨幅榜',
      marketTabs: ['涨幅榜', '跌幅榜', '成交量'],
      marketData: [
        { base: 'BTC', quote: 'USDT', price: 42356.78, change: 2.34, volume: 1254321 },
        { base: 'ETH', quote: 'USDT', price: 2412.56, change: -1.23, volume: 987654 },
        { base: 'SOL', quote: 'USDT', price: 80.45, change: 5.67, volume: 765432 },
        { base: 'ADA', quote: 'USDT', price: 0.56, change: 3.45, volume: 654321 }
      ],
      recentTrades: [
        { id: 1, symbol: 'BTC/USDT', side: 'buy', price: 42312.34, amount: 0.02, timestamp: Date.now()  - 120000 },
        { id: 2, symbol: 'ETH/USDT', side: 'sell', price: 2415.67, amount: 1.5, timestamp: Date.now()  - 180000 }
      ],
      riskLevel: 'low',
      riskMetrics: {
        accountRisk: 0.25,
        portfolioVolatility: 0.18 
      },
      activeAlerts: [
        { level: 'warning', message: 'ETH仓位超过组合20%限制' },
        { level: 'info', message: 'BTC/USDT策略达到日交易次数上限' }
      ],
      chartOptions: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right'
          }
        }
      },
      equityChartOptions: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: false
          }
        }
      }
    }
  },
  computed: {
    connectionText() {
      return {
        connected: '已连接',
        disconnected: '连接断开',
        reconnecting: '重新连接中...'
      }[this.connectionStatus]
    },
    marketStatusText() {
      return this.marketTrend  === 'up' ? '牛市' : '熊市'
    },
    assetDistribution() {
      return {
        labels: this.assets.map(a  => a.symbol), 
        datasets: [{
          data: this.assets.map(a  => a.value), 
          backgroundColor: [
            '#6e45e2', '#00e676', '#ff4757', '#ffa502'
          ]
        }]
      }
    },
    filteredAssets() {
      return this.assets.filter(a  => a.value  > 10)
    },
    currentStrategy() {
      return this.strategies.find(s  => s.id  === this.selectedStrategy)  || {}
    },
    equityData() {
      // 模拟策略净值曲线数据 
      return {
        labels: Array.from({  length: 30 }, (_, i) => `${i + 1}天`),
        datasets: [{
          label: '策略净值',
          data: Array.from({  length: 30 }, (_, i) => 
            1 + (this.currentStrategy.return  * (i / 29)) + (Math.random()  - 0.5) * 0.1
          ),
          borderColor: '#6e45e2',
          tension: 0.1
        }]
      }
    },
    riskLevelText() {
      return {
        low: '低风险',
        medium: '中风险',
        high: '高风险'
      }[this.riskLevel]
    }
  },
  created() {
    this.initWebSocket() 
    this.loadDashboardData() 
  },
  methods: {
    formatTime(timestamp, formatStr = 'MM/dd HH:mm') {
      return format(new Date(timestamp), formatStr)
    },
    formatVolume(vol) {
      if (vol > 1000000) return `${(vol / 1000000).toFixed(2)}M`
      if (vol > 1000) return `${(vol / 1000).toFixed(2)}K`
      return vol.toFixed(2) 
    },
    changeTimeRange(range) {
      this.activeRange  = range 
      this.loadDashboardData() 
    },
    openTradePanel(symbol) {
      this.$router.push({  name: 'trade', query: { symbol } })
    },
    showAllTrades() {
      this.$router.push({  name: 'trades' })
    },
    dismissAlert(index) {
      this.activeAlerts.splice(index,  1)
    },
    initWebSocket() {
      // 模拟WebSocket连接 
      this.connectionStatus  = 'connected'
      
      // 模拟实时数据更新
      this.interval  = setInterval(() => {
        this.lastUpdate  = Date.now() 
        this.btcPrice  = 42356.78 + (Math.random()  - 0.5) * 500 
        this.btcChange  = 2.34 + (Math.random()  - 0.5) * 2 
        
        // 随机更新市场数据
        this.marketData  = this.marketData.map(item  => ({
          ...item,
          price: item.price  * (1 + (Math.random()  - 0.5) * 0.02),
          change: item.change  + (Math.random()  - 0.5) * 1 
        }))
      }, 5000)
    },
    loadDashboardData() {
      // 这里实际项目中应该是API调用
      console.log(`Loading  data for ${this.activeRange}  range`)
    }
  },
  beforeDestroy() {
    clearInterval(this.interval) 
  }
}
</script>
 
<style scoped>
.dashboard-container {
  padding: 20px;
  background: #1e1e2d;
  color: #e0e0e0;
  height: 100%;
  display: flex;
  flex-direction: column;
}
 
.status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #3a3a4c;
  font-size: 14px;
}
 
.connection-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 4px;
}
 
.connection-status.connected  {
  background: rgba(0, 230, 118, 0.2);
  color: #00e676;
}
 
.connection-status.disconnected  {
  background: rgba(255, 71, 87, 0.2);
  color: #ff4757;
}
 
.connection-status.reconnecting  {
  background: rgba(255, 165, 2, 0.2);
  color: #ffa502;
}
 
.status-icon {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
 
.connection-status.connected  .status-icon {
  background: #00e676;
}
 
.connection-status.disconnected  .status-icon {
  background: #ff4757;
}
 
.connection-status.reconnecting  .status-icon {
  background: #ffa502;
}
 
.last-update {
  color: #b8b8d1;
}
 
.market-status {
  display: flex;
  align-items: center;
  gap: 15px;
}
 
.market-indicator {
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: bold;
}
 
.market-indicator.up  {
  background: rgba(0, 230, 118, 0.2);
  color: #00e676;
}
 
.market-indicator.down  {
  background: rgba(255, 71, 87, 0.2);
  color: #ff4757;
}
 
.btc-price {
  font-weight: bold;
}
 
.up {
  color: #00e676;
}
 
.down {
  color: #ff4757;
}
 
.dashboard-grid {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto auto;
  gap: 16px;
}
 
.card {
  background: #2a2a3c;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
 
.card-header {
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #3a3a4c;
}
 
.card-header h3 {
  margin: 0;
  font-size: 16px;
  color: white;
}
 
.card-body {
  flex: 1;
  padding: 16px;
  overflow: auto;
}
 
.time-range button {
  background: none;
  border: none;
  color: #b8b8d1;
  padding: 4px 8px;
  margin-left: 8px;
  cursor: pointer;
}
 
.time-range button.active  {
  color: white;
  background: #6e45e2;
  border-radius: 4px;
}
 
.balance-summary {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}
 
.total-value .label,
.balance-change .label {
  display: block;
  font-size: 12px;
  color: #b8b8d1;
  margin-bottom: 4px;
}
 
.total-value .value {
  font-size: 24px;
  font-weight: bold;
}
 
.balance-change .value {
  font-size: 18px;
  font-weight: bold;
}
 
.asset-distribution {
  height: 200px;
  margin-bottom: 20px;
}
 
.asset-list {
  max-height: 200px;
  overflow-y: auto;
}
 
.asset-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #3a3a4c;
}
 
.asset-info {
  flex: 1;
}
 
.asset-info .symbol {
  font-weight: bold;
  margin-right: 8px;
}
 
.asset-info .name {
  font-size: 12px;
  color: #b8b8d1;
}
 
.asset-values {
  flex: 1;
  text-align: right;
  padding-right: 16px;
}
 
.asset-values .amount {
  display: block;
  font-weight: bold;
}
 
.asset-values .value {
  font-size: 12px;
  color: #b8b8d1;
}
 
.asset-change {
  width: 80px;
  text-align: right;
  font-weight: bold;
}
 
.performance-metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
 
.metric {
  background: #3a3a4c;
  border-radius: 6px;
  padding: 12px;
  text-align: center;
}
 
.metric .label {
  display: block;
  font-size: 12px;
  color: #b8b8d1;
  margin-bottom: 6px;
}
 
.metric .value {
  font-size: 18px;
  font-weight: bold;
}
 
.equity-chart {
  height: 200px;
}
 
.market-tabs button {
  background: none;
  border: none;
  color: #b8b8d1;
  padding: 6px 12px;
  margin-left: 8px;
  cursor: pointer;
}
 
.market-tabs button.active  {
  color: white;
  background: #6e45e2;
  border-radius: 4px;
}
 
.market-table {
  font-size: 14px;
}
 
.table-header {
  display: flex;
  padding: 8px 0;
  border-bottom: 1px solid #3a3a4c;
  font-weight: bold;
  color: #b8b8d1;
}
 
.table-row {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #3a3a4c;
}
 
.table-row:hover {
  background: #3a3a4c;
}
 
.col-symbol {
  flex: 1;
}
 
.col-symbol .base {
  font-weight: bold;
}
 
.col-symbol .quote {
  color: #b8b8d1;
}
 
.col-price {
  width: 120px;
  text-align: right;
}
 
.col-change {
  width: 100px;
  text-align: right;
  font-weight: bold;
}
 
.col-volume {
  width: 120px;
  text-align: right;
}
 
.col-action {
  width: 80px;
  text-align: right;
}
 
.trade-btn {
  background: #6e45e2;
  color: white;
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
 
.trade-btn:hover {
  background: #8a63f2;
}
 
.trades-list {
  max-height: 300px;
  overflow-y: auto;
}
 
.trade-item {
  display: flex;
  padding: 8px 0;
  border-bottom: 1px solid #3a3a4c;
  font-size: 13px;
}
 
.trade-item.buy  {
  background: rgba(0, 230, 118, 0.05);
}
 
.trade-item.sell  {
  background: rgba(255, 71, 87, 0.05);
}
 
.trade-time {
  width: 80px;
  color: #b8b8d1;
}
 
.trade-pair {
  width: 100px;
  font-weight: bold;
}
 
.trade-side {
  width: 80px;
}
 
.trade-side .buy {
  color: #00e676;
}
 
.trade-side .sell {
  color: #ff4757;
}
 
.trade-price {
  width: 100px;
  text-align: right;
}
 
.trade-amount {
  width: 100px;
  text-align: right;
}
 
.trade-value {
  width: 120px;
  text-align: right;
  color: #b8b8d1;
}
 
.risk-level {
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: bold;
}
 
.risk-level.low  {
  background: rgba(0, 230, 118, 0.2);
  color: #00e676;
}
 
.risk-level.medium  {
  background: rgba(255, 165, 2, 0.2);
  color: #ffa502;
}
 
.risk-level.high  {
  background: rgba(255, 71, 87, 0.2);
  color: #ff4757;
}
 
.risk-indicators {
  display: flex;
  justify-content: space-around;
  margin-bottom: 20px;
}
 
.indicator {
  width: 200px;
}
 
.gauge-container {
  height: 120px;
}
 
.risk-alerts {
  max-height: 120px;
  overflow-y: auto;
}
 
.alert-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  margin-bottom: 8px;
  border-radius: 4px;
}
 
.alert-item.info  {
  background: rgba(110, 69, 226, 0.1);
  border-left: 3px solid #6e45e2;
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
  width: 16px;
  height: 16px;
  margin-right: 8px;
}
 
.alert-item.info  .alert-icon {
  background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg"  viewBox="0 0 24 24" fill="%236e45e2"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>');
}
 
.alert-item.warning  .alert-icon {
  background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg"  viewBox="0 0 24 24" fill="%23ffa502"><path d="M12 2L1 21h22L12 2zm0 3.5L19.5 19h-15L12 5.5zM11 10v4h2v-4h-2zm0 6v2h2v-2h-2z"/></svg>');
}
 
.alert-item.critical  .alert-icon {
  background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg"  viewBox="0 0 24 24" fill="%23ff4757"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm1-13h-2v6h2V7zm0 8h-2v2h2v-2z"/></svg>');
}
 
.alert-message {
  flex: 1;
  font-size: 13px;
}
 
.alert-dismiss {
  background: none;
  border: none;
  color: #6a6a7c;
  font-size: 16px;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
}
 
.alert-dismiss:hover {
  color: #ff4757;
}
 
.no-alerts {
  text-align: center;
  padding: 20px;
  color: #6a6a7c;
}
 
/* 响应式布局 */
@media (max-width: 1200px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}
 
@media (max-width: 768px) {
  .status-bar {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
 
  .performance-metrics {
    grid-template-columns: 1fr 1fr;
  }
 
  .table-header,
  .table-row {
    flex-wrap: wrap;
  }
 
  .col-symbol,
  .col-price,
  .col-change,
  .col-volume,
  .col-action {
    width: 50%;
    text-align: left !important;
    margin-bottom: 4px;
  }
 
  .trade-item {
    flex-wrap: wrap;
  }
 
  .trade-time,
  .trade-pair,
  .trade-side,
  .trade-price,
  .trade-amount,
  .trade-value {
    width: 50%;
    text-align: left !important;
    margin-bottom: 4px;
  }
}
</style>
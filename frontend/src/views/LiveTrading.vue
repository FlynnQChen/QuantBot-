<template>
  <div class="live-trading-container">
    <!-- 顶部控制栏 -->
    <div class="control-bar">
      <div class="market-selector">
        <select v-model="selectedSymbol" @change="changeSymbol">
          <option 
            v-for="symbol in availableSymbols" 
            :key="symbol" 
            :value="symbol"
          >
            {{ symbol }}
          </option>
        </select>
        <div class="price-display">
          <span class="current-price" :class="priceDirection">
            {{ currentPrice.toFixed(pricePrecision)  }}
          </span>
          <span class="price-change" :class="priceChange >= 0 ? 'up' : 'down'">
            {{ priceChange >= 0 ? '+' : '' }}{{ priceChange.toFixed(2)  }}%
          </span>
        </div>
      </div>
      <div class="trading-actions">
        <button 
          class="btn-flat"
          :class="{ active: activeTab === 'trade' }"
          @click="activeTab = 'trade'"
        >
          交易 
        </button>
        <button 
          class="btn-flat"
          :class="{ active: activeTab === 'orders' }"
          @click="activeTab = 'orders'"
        >
          订单 
        </button>
        <button 
          class="btn-flat"
          :class="{ active: activeTab === 'positions' }"
          @click="activeTab = 'positions'"
        >
          仓位
        </button>
      </div>
    </div>
 
    <!-- 主交易区域 -->
    <div class="trading-grid">
      <!-- 左侧：市场数据和图表 -->
      <div class="market-data">
        <div class="chart-container">
          <trading-chart 
            :symbol="selectedSymbol" 
            :interval="chartInterval"
            @price-update="handlePriceUpdate"
          />
        </div>
        <div class="market-depth">
          <div class="depth-header">
            <h4>市场深度</h4>
            <select v-model="depthPrecision" class="precision-select">
              <option value="0.1">0.1</option>
              <option value="0.01">0.01</option>
              <option value="0.001">0.001</option>
            </select>
          </div>
          <div class="depth-container">
            <div class="bids">
              <div 
                v-for="(bid, index) in depthData.bids"  
                :key="'bid'+index"
                class="depth-level"
                :style="{ width: `${bid.percent}%`  }"
              >
                <span class="depth-price">{{ bid.price.toFixed(pricePrecision)  }}</span>
                <span class="depth-amount">{{ bid.amount.toFixed(amountPrecision)  }}</span>
                <span class="depth-total">{{ bid.total.toFixed(amountPrecision)  }}</span>
              </div>
            </div>
            <div class="market-price">
              {{ currentPrice.toFixed(pricePrecision)  }}
            </div>
            <div class="asks">
              <div 
                v-for="(ask, index) in depthData.asks"  
                :key="'ask'+index"
                class="depth-level"
                :style="{ width: `${ask.percent}%`  }"
              >
                <span class="depth-price">{{ ask.price.toFixed(pricePrecision)  }}</span>
                <span class="depth-amount">{{ ask.amount.toFixed(amountPrecision)  }}</span>
                <span class="depth-total">{{ ask.total.toFixed(amountPrecision)  }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
 
      <!-- 中间：交易面板 -->
      <div class="trading-panel">
        <div v-show="activeTab === 'trade'" class="trade-form">
          <div class="form-group">
            <div class="trade-type">
              <button 
                v-for="type in tradeTypes" 
                :key="type.value" 
                :class="{ active: tradeType === type.value  }"
                @click="tradeType = type.value" 
              >
                {{ type.label  }}
              </button>
            </div>
          </div>
          
          <div class="form-group">
            <label>价格 ({{ quoteCurrency }})</label>
            <input 
              type="number" 
              v-model.number="orderPrice" 
              :placeholder="currentPrice.toFixed(pricePrecision)" 
              step="0.0001"
            >
          </div>
          
          <div class="form-group">
            <label>数量 ({{ baseCurrency }})</label>
            <input 
              type="number" 
              v-model.number="orderAmount" 
              placeholder="0.00"
              step="0.01"
            >
            <div class="amount-actions">
              <span 
                v-for="percent in [25, 50, 75, 100]"
                :key="percent"
                @click="setAmountPercent(percent)"
              >
                {{ percent }}%
              </span>
            </div>
          </div>
          
          <div class="form-group">
            <label>总价 ({{ quoteCurrency }})</label>
            <input 
              type="number" 
              v-model.number="orderTotal" 
              placeholder="0.00"
              readonly
            >
          </div>
          
          <div class="form-group">
            <button 
              class="btn-buy"
              :disabled="!canPlaceOrder"
              @click="placeOrder('buy')"
            >
              买入 {{ baseCurrency }}
            </button>
            <button 
              class="btn-sell"
              :disabled="!canPlaceOrder"
              @click="placeOrder('sell')"
            >
              卖出 {{ baseCurrency }}
            </button>
          </div>
        </div>
 
        <!-- 订单管理 -->
        <div v-show="activeTab === 'orders'" class="orders-list">
          <div class="table-header">
            <div class="col-time">时间</div>
            <div class="col-pair">交易对</div>
            <div class="col-type">类型</div>
            <div class="col-price">价格</div>
            <div class="col-amount">数量</div>
            <div class="col-filled">已成交</div>
            <div class="col-status">状态</div>
            <div class="col-action">操作</div>
          </div>
          <div 
            v-for="order in activeOrders" 
            :key="order.id" 
            class="order-item"
          >
            <div class="col-time">{{ formatTime(order.timestamp)  }}</div>
            <div class="col-pair">{{ order.symbol  }}</div>
            <div class="col-type" :class="order.side"> 
              {{ order.side  === 'buy' ? '买入' : '卖出' }}
              <span v-if="order.type  !== 'limit'">({{ order.type  }})</span>
            </div>
            <div class="col-price">{{ order.price.toFixed(pricePrecision)  }}</div>
            <div class="col-amount">{{ order.amount.toFixed(amountPrecision)  }}</div>
            <div class="col-filled">{{ order.filled.toFixed(amountPrecision)  }}</div>
            <div class="col-status">
              <span :class="order.status">{{  formatStatus(order.status)  }}</span>
            </div>
            <div class="col-action">
              <button 
                v-if="order.status  === 'open'"
                class="btn-cancel"
                @click="cancelOrder(order.id)" 
              >
                撤单 
              </button>
            </div>
          </div>
          <div v-if="activeOrders.length  === 0" class="no-orders">
            当前没有活跃订单
          </div>
        </div>
 
        <!-- 仓位管理 -->
        <div v-show="activeTab === 'positions'" class="positions-list">
          <div class="table-header">
            <div class="col-pair">交易对</div>
            <div class="col-size">仓位大小</div>
            <div class="col-entry">开仓均价</div>
            <div class="col-mark">标记价格</div>
            <div class="col-pnl">未实现盈亏</div>
            <div class="col-action">操作</div>
          </div>
          <div 
            v-for="position in positions" 
            :key="position.symbol" 
            class="position-item"
          >
            <div class="col-pair">{{ position.symbol  }}</div>
            <div class="col-size" :class="position.side"> 
              {{ position.size.toFixed(amountPrecision)  }}
            </div>
            <div class="col-entry">{{ position.entryPrice.toFixed(pricePrecision)  }}</div>
            <div class="col-mark">{{ position.markPrice.toFixed(pricePrecision)  }}</div>
            <div class="col-pnl" :class="position.pnl  >= 0 ? 'up' : 'down'">
              {{ position.pnl.toFixed(2)  }} ({{ position.pnlPercent.toFixed(2)  }}%)
            </div>
            <div class="col-action">
              <button 
                class="btn-close"
                @click="showClosePosition(position.symbol)" 
              >
                平仓 
              </button>
            </div>
          </div>
          <div v-if="positions.length  === 0" class="no-positions">
            当前没有持仓
          </div>
        </div>
      </div>
 
      <!-- 右侧：交易历史和账户信息 -->
      <div class="trading-sidebar">
        <div class="account-summary">
          <h4>账户概览</h4>
          <div class="balance-item">
            <span class="label">总资产</span>
            <span class="value">{{ accountBalance.total.toFixed(2)  }} {{ quoteCurrency }}</span>
          </div>
          <div class="balance-item">
            <span class="label">可用余额</span>
            <span class="value">{{ accountBalance.free.toFixed(2)  }} {{ quoteCurrency }}</span>
          </div>
          <div class="balance-item">
            <span class="label">持仓价值</span>
            <span class="value">{{ accountBalance.positions.toFixed(2)  }} {{ quoteCurrency }}</span>
          </div>
        </div>
 
        <div class="trade-history">
          <h4>最新成交</h4>
          <div 
            v-for="trade in recentTrades" 
            :key="trade.id" 
            class="trade-item"
            :class="trade.side" 
          >
            <div class="trade-time">{{ formatTime(trade.timestamp,  'HH:mm:ss') }}</div>
            <div class="trade-side">
              {{ trade.side  === 'buy' ? '买入' : '卖出' }}
            </div>
            <div class="trade-price">{{ trade.price.toFixed(pricePrecision)  }}</div>
            <div class="trade-amount">{{ trade.amount.toFixed(amountPrecision)  }}</div>
            <div class="trade-total">{{ (trade.price  * trade.amount).toFixed(2)  }}</div>
          </div>
        </div>
      </div>
    </div>
 
    <!-- 平仓模态框 -->
    <modal 
      v-if="showCloseModal"
      @close="showCloseModal = false"
      title="确认平仓"
    >
      <div class="close-position-form">
        <div class="form-group">
          <label>交易对</label>
          <input type="text" :value="closeSymbol" readonly>
        </div>
        <div class="form-group">
          <label>平仓数量</label>
          <input 
            type="number" 
            v-model.number="closeAmount" 
            :max="positionToClose.size" 
            step="0.01"
          >
          <span class="max-amount" @click="closeAmount = positionToClose.size"> 
            全部 
          </span>
        </div>
        <div class="form-group">
          <label>平仓价格</label>
          <input 
            type="number" 
            v-model.number="closePrice" 
            :placeholder="positionToClose.markPrice.toFixed(pricePrecision)" 
            step="0.0001"
          >
        </div>
        <div class="form-actions">
          <button class="btn-cancel" @click="showCloseModal = false">
            取消
          </button>
          <button 
            class="btn-confirm"
            :class="positionToClose.side  === 'long' ? 'btn-sell' : 'btn-buy'"
            @click="closePosition"
          >
            确认{{ positionToClose.side  === 'long' ? '卖出' : '买入' }}平仓 
          </button>
        </div>
      </div>
    </modal>
  </div>
</template>
 
<script>
import { format } from 'date-fns'
import TradingChart from '@/components/charts/TradingChart.vue' 
import Modal from '@/components/ui/Modal.vue' 
 
export default {
  components: {
    TradingChart,
    Modal
  },
  data() {
    return {
      selectedSymbol: 'BTC/USDT',
      availableSymbols: ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'ADA/USDT'],
      activeTab: 'trade',
      chartInterval: '15m',
      currentPrice: 42356.78,
      priceChange: 2.34,
      priceDirection: 'up',
      depthPrecision: '0.01',
      depthData: {
        bids: [
          { price: 42350.12, amount: 0.25, total: 0.25, percent: 80 },
          { price: 42345.67, amount: 0.18, total: 0.43, percent: 65 },
          // 更多买单数据...
        ],
        asks: [
          { price: 42360.45, amount: 0.32, total: 0.32, percent: 85 },
          { price: 42365.89, amount: 0.21, total: 0.53, percent: 70 },
          // 更多卖单数据...
        ]
      },
      tradeTypes: [
        { value: 'limit', label: '限价单' },
        { value: 'market', label: '市价单' }
      ],
      tradeType: 'limit',
      orderPrice: null,
      orderAmount: null,
      activeOrders: [
        {
          id: 'order1',
          symbol: 'BTC/USDT',
          side: 'buy',
          type: 'limit',
          price: 42000.00,
          amount: 0.02,
          filled: 0.01,
          status: 'open',
          timestamp: Date.now()  - 3600000 
        }
      ],
      positions: [
        {
          symbol: 'BTC/USDT',
          side: 'long',
          size: 0.05,
          entryPrice: 41500.00,
          markPrice: 42356.78,
          pnl: 42.84,
          pnlPercent: 2.06 
        }
      ],
      accountBalance: {
        total: 12543.21,
        free: 5432.10,
        positions: 7111.11 
      },
      recentTrades: [
        {
          id: 'trade1',
          symbol: 'BTC/USDT',
          side: 'buy',
          price: 42312.34,
          amount: 0.02,
          timestamp: Date.now()  - 120000
        }
      ],
      showCloseModal: false,
      closeSymbol: '',
      closeAmount: null,
      closePrice: null 
    }
  },
  computed: {
    baseCurrency() {
      return this.selectedSymbol.split('/')[0] 
    },
    quoteCurrency() {
      return this.selectedSymbol.split('/')[1] 
    },
    pricePrecision() {
      return this.selectedSymbol.includes('BTC')  ? 2 : 4
    },
    amountPrecision() {
      return this.selectedSymbol.includes('BTC')  ? 4 : 2 
    },
    orderTotal() {
      if (!this.orderPrice  || !this.orderAmount)  return 0 
      return this.orderPrice  * this.orderAmount  
    },
    canPlaceOrder() {
      if (this.tradeType  === 'market') return !!this.orderAmount 
      return !!this.orderPrice  && !!this.orderAmount  
    },
    positionToClose() {
      return this.positions.find(p  => p.symbol  === this.closeSymbol)  || {}
    }
  },
  watch: {
    orderPrice(newVal) {
      if (newVal <= 0) this.orderPrice  = null 
    },
    orderAmount(newVal) {
      if (newVal <= 0) this.orderAmount  = null 
    }
  },
  methods: {
    changeSymbol() {
      // 切换交易对时重新加载数据 
      this.loadMarketData() 
    },
    handlePriceUpdate(priceData) {
      this.currentPrice  = priceData.price 
      this.priceChange  = priceData.change  
      this.priceDirection  = priceData.direction 
    },
    setAmountPercent(percent) {
      if (!this.accountBalance.free)  return
      
      const maxAmount = this.accountBalance.free  / this.currentPrice  
      this.orderAmount  = (maxAmount * percent / 100).toFixed(this.amountPrecision) 
    },
    placeOrder(side) {
      const order = {
        symbol: this.selectedSymbol, 
        side,
        type: this.tradeType, 
        price: this.tradeType  === 'limit' ? this.orderPrice  : null,
        amount: this.orderAmount, 
        timestamp: Date.now() 
      }
      
      // 模拟订单提交
      this.activeOrders.unshift({ 
        ...order,
        id: `order-${Date.now()}`, 
        status: 'open',
        filled: 0 
      })
      
      // 重置表单 
      this.orderPrice  = null
      this.orderAmount  = null 
      
      this.$notify({
        title: '订单已提交',
        message: `${side === 'buy' ? '买入' : '卖出'} ${this.orderAmount}  ${this.baseCurrency}`, 
        type: 'success'
      })
    },
    cancelOrder(orderId) {
      const orderIndex = this.activeOrders.findIndex(o  => o.id  === orderId)
      if (orderIndex >= 0) {
        this.activeOrders[orderIndex].status  = 'canceled'
        this.$notify({
          title: '订单已取消',
          type: 'warning'
        })
      }
    },
    showClosePosition(symbol) {
      this.closeSymbol  = symbol
      this.closeAmount  = this.positionToClose.size  
      this.closePrice  = this.positionToClose.markPrice 
      this.showCloseModal  = true
    },
    closePosition() {
      // 模拟平仓操作 
      const positionIndex = this.positions.findIndex(p  => p.symbol  === this.closeSymbol) 
      if (positionIndex >= 0) {
        this.positions.splice(positionIndex,  1)
        
        this.recentTrades.unshift({ 
          id: `trade-${Date.now()}`, 
          symbol: this.closeSymbol, 
          side: this.positionToClose.side  === 'long' ? 'sell' : 'buy',
          price: this.closePrice  || this.positionToClose.markPrice, 
          amount: this.closeAmount, 
          timestamp: Date.now() 
        })
        
        this.$notify({
          title: '平仓成功',
          message: `已平仓 ${this.closeAmount}  ${this.baseCurrency}`, 
          type: 'success'
        })
        
        this.showCloseModal  = false 
      }
    },
    formatTime(timestamp, formatStr = 'MM/dd HH:mm') {
      return format(new Date(timestamp), formatStr)
    },
    formatStatus(status) {
      const statusMap = {
        open: '未成交',
        filled: '已成交',
        canceled: '已取消',
        rejected: '已拒绝'
      }
      return statusMap[status] || status 
    },
    loadMarketData() {
      // 实际项目中这里应该是API调用
      console.log(`Loading  market data for ${this.selectedSymbol}`) 
    }
  },
  mounted() {
    this.loadMarketData() 
    
    // 模拟实时数据更新
    this.interval  = setInterval(() => {
      // 更新市场深度
      this.depthData.bids.forEach(bid  => {
        bid.amount  = Math.max(0,  bid.amount  + (Math.random()  - 0.5) * 0.02)
      })
      this.depthData.asks.forEach(ask  => {
        ask.amount  = Math.max(0,  ask.amount  + (Math.random()  - 0.5) * 0.02)
      })
      
      // 更新订单状态
      this.activeOrders.forEach(order  => {
        if (order.status  === 'open' && Math.random()  > 0.9) {
          order.filled  = order.amount  
          order.status  = 'filled'
        }
      })
      
      // 更新持仓盈亏 
      this.positions.forEach(pos  => {
        pos.markPrice  = this.currentPrice  * (1 + (Math.random()  - 0.5) * 0.001)
        pos.pnl  = (pos.markPrice  - pos.entryPrice)  * pos.size 
        pos.pnlPercent  = (pos.pnl  / (pos.entryPrice  * pos.size))  * 100 
      })
    }, 3000)
  },
  beforeDestroy() {
    clearInterval(this.interval) 
  }
}
</script>
 
<style scoped>
.live-trading-container {
  padding: 16px;
  background: #1e1e2d;
  color: #e0e0e0;
  height: 100%;
  display: flex;
  flex-direction: column;
}
 
.control-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #3a3a4c;
}
 
.market-selector {
  display: flex;
  align-items: center;
  gap: 16px;
}
 
.market-selector select {
  background: #3a3a4c;
  border: 1px solid #4a4a5c;
  color: white;
  padding: 8px 16px;
  border-radius: 4px;
  font-weight: bold;
}
 
.price-display {
  display: flex;
  align-items: center;
  gap: 8px;
}
 
.current-price {
  font-size: 18px;
  font-weight: bold;
}
 
.current-price.up  {
  color: #00e676;
}
 
.current-price.down  {
  color: #ff4757;
}
 
.price-change {
  font-size: 14px;
}
 
.price-change.up  {
  color: #00e676;
}
 
.price-change.down  {
  color: #ff4757;
}
 
.trading-actions {
  display: flex;
  gap: 8px;
}
 
.btn-flat {
  background: none;
  border: none;
  color: #b8b8d1;
  padding: 8px 16px;
  cursor: pointer;
  position: relative;
}
 
.btn-flat.active  {
  color: white;
  font-weight: bold;
}
 
.btn-flat.active::after  {
  content: '';
  position: absolute;
  bottom: -17px;
  left: 0;
  right: 0;
  height: 2px;
  background: #6e45e2;
}
 
.trading-grid {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 350px 300px;
  gap: 16px;
  height: calc(100vh - 120px);
}
 
.market-data {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
 
.chart-container {
  height: 400px;
  background: #2a2a3c;
  border-radius: 8px;
  overflow: hidden;
}
 
.market-depth {
  background: #2a2a3c;
  border-radius: 8px;
  padding: 16px;
  flex: 1;
}
 
.depth-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
 
.depth-header h4 {
  margin: 0;
}
 
.precision-select {
  background: #3a3a4c;
  border: 1px solid #4a4a5c;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
}
 
.depth-container {
  display: flex;
  flex-direction: column;
  height: calc(100% - 40px);
}
 
.bids, .asks {
  display: flex;
  flex-direction: column;
}
 
.bids .depth-level {
  background: rgba(0, 230, 118, 0.1);
  border-left: 3px solid #00e676;
}
 
.asks .depth-level {
  background: rgba(255, 71, 87, 0.1);
  border-left: 3px solid #ff4757;
}
 
.depth-level {
  display: flex;
  justify-content: space-between;
  padding: 4px 8px;
  margin-bottom: 2px;
  font-size: 12px;
}
 
.depth-price {
  width: 80px;
  text-align: left;
}
 
.depth-amount {
  width: 80px;
  text-align: right;
}
 
.depth-total {
  width: 80px;
  text-align: right;
}
 
.market-price {
  text-align: center;
  padding: 8px;
  font-weight: bold;
  border-top: 1px solid #3a3a4c;
  border-bottom: 1px solid #3a3a4c;
}
 
.trading-panel {
  background: #2a2a3c;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
}
 
.trade-form, .orders-list, .positions-list {
  padding: 16px;
  flex: 1;
  overflow-y: auto;
}
 
.form-group {
  margin-bottom: 16px;
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
  padding: 8px 12px;
  border-radius: 4px;
}
 
.trade-type {
  display: flex;
  margin-bottom: 16px;
}
 
.trade-type button {
  flex: 1;
  background: #3a3a4c;
  border: none;
  color: #b8b8d1;
  padding: 8px;
  cursor: pointer;
}
 
.trade-type button:first-child {
  border-radius: 4px 0 0 4px;
}
 
.trade-type button:last-child {
  border-radius: 0 4px 4px 0;
}
 
.trade-type button.active  {
  background: #6e45e2;
  color: white;
}
 
.amount-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
}
 
.amount-actions span {
  font-size: 12px;
  color: #6e45e2;
  cursor: pointer;
}
 
.btn-buy, .btn-sell {
  width: 100%;
  padding: 12px;
  border: none;
  border-radius: 4px;
  font-weight: bold;
  cursor: pointer;
  margin-top: 8px;
}
 
.btn-buy {
  background: #00e676;
  color: #00391c;
}
 
.btn-buy:hover {
  background: #00c96b;
}
 
.btn-sell {
  background: #ff4757;
  color: #800a15;
}
 
.btn-sell:hover {
  background: #e63e4d;
}
 
.table-header {
  display: flex;
  padding: 8px 0;
  border-bottom: 1px solid #3a3a4c;
  font-size: 12px;
  color: #b8b8d1;
}
 
.order-item, .position-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #3a3a4c;
  font-size: 13px;
}
 
.col-time {
  width: 80px;
}
 
.col-pair {
  width: 80px;
  font-weight: bold;
}
 
.col-type {
  width: 60px;
}
 
.col-type.buy  {
  color: #00e676;
}
 
.col-type.sell  {
  color: #ff4757;
}
 
.col-price {
  width: 80px;
  text-align: right;
}
 
.col-amount {
  width: 80px;
  text-align: right;
}
 
.col-filled {
  width: 80px;
  text-align: right;
}
 
.col-status {
  width: 80px;
  text-align: center;
}
 
.col-status .open {
  color: #ffa502;
}
 
.col-status .filled {
  color: #00e676;
}
 
.col-status .canceled {
  color: #b8b8d1;
}
 
.col-action {
  width: 60px;
  text-align: right;
}
 
.btn-cancel {
  background: none;
  border: 1px solid #ff4757;
  color: #ff4757;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}
 
.btn-cancel:hover {
  background: rgba(255, 71, 87, 0.1);
}
 
.col-size {
  width: 100px;
  text-align: right;
}
 
.col-size.long  {
  color: #00e676;
}
 
.col-size.short  {
  color: #ff4757;
}
 
.col-entry, .col-mark {
  width: 100px;
  text-align: right;
}
 
.col-pnl {
  width: 120px;
  text-align: right;
}
 
.col-pnl.up  {
  color: #00e676;
}
 
.col-pnl.down  {
  color: #ff4757;
}
 
.btn-close {
  background: none;
  border: 1px solid #6e45e2;
  color: #6e45e2;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}
 
.btn-close:hover {
  background: rgba(110, 69, 226, 0.1);
}
 
.no-orders, .no-positions {
  text-align: center;
  padding: 40px;
  color: #6a6a7c;
}
 
.trading-sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
 
.account-summary, .trade-history {
  background: #2a2a3c;
  border-radius: 8px;
  padding: 16px;
}
 
.account-summary h4, .trade-history h4 {
  margin: 0 0 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #3a3a4c;
}
 
.balance-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  font-size: 14px;
}
 
.balance-item .label {
  color: #b8b8d1;
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
  width: 60px;
  color: #b8b8d1;
}
 
.trade-side {
  width: 40px;
}
 
.trade-side.buy  {
  color: #00e676;
}
 
.trade-side.sell  {
  color: #ff4757;
}
 
.trade-price {
  width: 80px;
  text-align: right;
}
 
.trade-amount {
  width: 80px;
  text-align: right;
}
 
.trade-total {
  width: 80px;
  text-align: right;
  color: #b8b8d1;
}
 
.close-position-form {
  padding: 16px;
}
 
.close-position-form .form-group {
  margin-bottom: 16px;
}
 
.close-position-form input {
  width: 100%;
  background: #3a3a4c;
  border: 1px solid #4a4a5c;
  color: white;
  padding: 8px 12px;
  border-radius: 4px;
}
 
.max-amount {
  font-size: 12px;
  color: #6e45e2;
  cursor: pointer;
  margin-left: 8px;
}
 
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 24px;
}
 
.btn
<template>
  <div class="trade-panel">
    <!-- 市场数据头部 -->
    <div class="market-header">
      <div class="symbol-selector">
        <select v-model="selectedSymbol" @change="onSymbolChange">
          <option 
            v-for="symbol in availableSymbols" 
            :value="symbol"
            :key="symbol"
          >
            {{ symbol }}
          </option>
        </select>
        <span class="price-display" :class="priceChangeClass">
          {{ currentPrice || '--' }}
          <span class="price-change">
            ({{ priceChangePercent }}%)
          </span>
        </span>
      </div>
      
      <div class="market-stats">
        <div class="stat-item">
          <span class="stat-label">24H量</span>
          <span class="stat-value">{{ volume24h || '--' }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">买一价</span>
          <span class="stat-value">{{ bidPrice || '--' }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">卖一价</span>
          <span class="stat-value">{{ askPrice || '--' }}</span>
        </div>
      </div>
    </div>
 
    <!-- 交易操作区 -->
    <div class="trade-actions">
      <div class="action-group buy-group">
        <h3>买入</h3>
        <div class="form-row">
          <label>价格</label>
          <input 
            type="number" 
            v-model.number="buyPrice"  
            :placeholder="askPrice || '市价'" 
            step="0.0001"
          >
        </div>
        <div class="form-row">
          <label>数量</label>
          <input 
            type="number" 
            v-model.number="buyAmount"  
            placeholder="0.00"
            step="0.01"
          >
          <span class="asset-unit">{{ baseAsset }}</span>
        </div>
        <div class="form-row">
          <label>总价</label>
          <span class="calculated-value">
            {{ (buyPrice * buyAmount).toFixed(4) || '--' }}
            <span class="asset-unit">{{ quoteAsset }}</span>
          </span>
        </div>
        <button 
          class="action-btn buy-btn"
          :disabled="!canBuy"
          @click="placeOrder('buy')"
        >
          买入 {{ baseAsset }}
        </button>
      </div>
 
      <div class="action-group sell-group">
        <h3>卖出</h3>
        <div class="form-row">
          <label>价格</label>
          <input 
            type="number" 
            v-model.number="sellPrice"  
            :placeholder="bidPrice || '市价'"
            step="0.0001"
          >
        </div>
        <div class="form-row">
          <label>数量</label>
          <input 
            type="number" 
            v-model.number="sellAmount"  
            placeholder="0.00"
            step="0.01"
          >
          <span class="asset-unit">{{ baseAsset }}</span>
        </div>
        <div class="form-row">
          <label>总价</label>
          <span class="calculated-value">
            {{ (sellPrice * sellAmount).toFixed(4) || '--' }}
            <span class="asset-unit">{{ quoteAsset }}</span>
          </span>
        </div>
        <button 
          class="action-btn sell-btn"
          :disabled="!canSell"
          @click="placeOrder('sell')"
        >
          卖出 {{ baseAsset }}
        </button>
      </div>
    </div>
 
    <!-- 持仓信息 -->
    <div class="position-info">
      <h3>当前持仓</h3>
      <div v-if="currentPosition" class="position-details">
        <div class="position-row">
          <span class="label">方向</span>
          <span 
            class="value"
            :class="currentPosition.side  === 'long' ? 'long' : 'short'"
          >
            {{ currentPosition.side  === 'long' ? '多头' : '空头' }}
          </span>
        </div>
        <div class="position-row">
          <span class="label">数量</span>
          <span class="value">
            {{ currentPosition.amount  }} {{ baseAsset }}
          </span>
        </div>
        <div class="position-row">
          <span class="label">开仓均价</span>
          <span class="value">
            {{ currentPosition.entryPrice  }} {{ quoteAsset }}
          </span>
        </div>
        <div class="position-row">
          <span class="label">当前价值</span>
          <span class="value">
            {{ (currentPosition.amount  * currentPrice).toFixed(4) }} {{ quoteAsset }}
          </span>
        </div>
        <div class="position-row">
          <span class="label">盈亏</span>
          <span 
            class="value"
            :class="currentPosition.unrealizedPnl  >= 0 ? 'profit' : 'loss'"
          >
            {{ currentPosition.unrealizedPnl.toFixed(4)  }} {{ quoteAsset }}
            ({{ currentPosition.unrealizedPnlPercent.toFixed(2)  }}%)
          </span>
        </div>
        <button 
          class="close-btn"
          @click="closePosition"
        >
          平仓 
        </button>
      </div>
      <div v-else class="no-position">
        没有持仓
      </div>
    </div>
 
    <!-- 杠杆设置 -->
    <div class="leverage-settings">
      <h3>杠杆设置</h3>
      <div class="leverage-control">
        <input 
          type="range" 
          v-model.number="leverage"  
          min="1" 
          max="100" 
          step="1"
          @change="updateLeverage"
        >
        <span class="leverage-value">×{{ leverage }}</span>
      </div>
      <div class="margin-info">
        <div class="margin-row">
          <span class="label">预估保证金</span>
          <span class="value">
            {{ estimatedMargin.toFixed(4)  }} {{ quoteAsset }}
          </span>
        </div>
      </div>
    </div>
 
    <!-- 订单确认弹窗 -->
    <transition name="modal">
      <div v-if="showConfirmModal" class="modal-mask">
        <div class="modal-container">
          <h3>确认订单</h3>
          <div class="modal-content">
            <p> 
              {{ confirmSide === 'buy' ? '买入' : '卖出' }} 
              {{ confirmAmount }} {{ baseAsset }} @ 
              {{ confirmPrice || '市价' }} {{ quoteAsset }}
            </p>
            <p>预估成本: {{ (confirmAmount * confirmPrice).toFixed(4) }} {{ quoteAsset }}</p>
          </div>
          <div class="modal-actions">
            <button class="cancel-btn" @click="showConfirmModal = false">取消</button>
            <button 
              class="confirm-btn"
              :class="confirmSide"
              @click="confirmOrder"
            >
              确认{{ confirmSide === 'buy' ? '买入' : '卖出' }}
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>
 
<script>
import { mapState, mapGetters } from 'vuex'
 
export default {
  name: 'TradePanel',
  data() {
    return {
      selectedSymbol: 'BTC/USDT',
      buyPrice: null,
      buyAmount: null,
      sellPrice: null,
      sellAmount: null,
      leverage: 10,
      showConfirmModal: false,
      confirmSide: '',
      confirmPrice: null,
      confirmAmount: null,
      currentMarketData: null
    }
  },
  computed: {
    ...mapState(['account']),
    ...mapGetters(['availableSymbols', 'positions']),
    
    baseAsset() {
      return this.selectedSymbol.split('/')[0] 
    },
    quoteAsset() {
      return this.selectedSymbol.split('/')[1] 
    },
    currentPrice() {
      return this.currentMarketData?.lastPrice  
    },
    priceChangePercent() {
      const change = this.currentMarketData?.priceChangePercent  
      return change ? change.toFixed(2)  : '--'
    },
    priceChangeClass() {
      if (!this.currentMarketData)  return ''
      return this.currentMarketData.priceChangePercent  >= 0 ? 'up' : 'down'
    },
    bidPrice() {
      return this.currentMarketData?.bidPrice  
    },
    askPrice() {
      return this.currentMarketData?.askPrice 
    },
    volume24h() {
      return this.currentMarketData?.volume  
        ? `${this.currentMarketData.volume}  ${this.baseAsset}` 
        : '--'
    },
    canBuy() {
      return this.buyAmount  > 0 && 
        (this.account?.balance[this.quoteAsset]  || 0) >= this.buyAmount  * (this.buyPrice  || this.askPrice) 
    },
    canSell() {
      return this.sellAmount  > 0
    },
    currentPosition() {
      return this.positions.find(p  => p.symbol  === this.selectedSymbol) 
    },
    estimatedMargin() {
      if (!this.buyAmount  || !this.currentPrice)  return 0
      return (this.buyAmount  * (this.buyPrice  || this.currentPrice))  / this.leverage  
    }
  },
  watch: {
    selectedSymbol(newVal) {
      this.subscribeMarketData(newVal) 
    },
    askPrice(newVal) {
      if (!this.buyPrice)  this.buyPrice  = newVal
    },
    bidPrice(newVal) {
      if (!this.sellPrice)  this.sellPrice  = newVal 
    }
  },
  mounted() {
    this.subscribeMarketData(this.selectedSymbol) 
  },
  methods: {
    subscribeMarketData(symbol) {
      // 取消之前的订阅
      if (this.marketDataSubscription)  {
        this.marketDataSubscription.unsubscribe() 
      }
      
      // 订阅新的市场数据 
      this.marketDataSubscription  = this.$socket.subscribeMarketData( 
        symbol,
        data => {
          this.currentMarketData  = data 
        }
      )
    },
    onSymbolChange() {
      this.resetForm() 
    },
    resetForm() {
      this.buyPrice  = this.askPrice 
      this.buyAmount  = null
      this.sellPrice  = this.bidPrice  
      this.sellAmount  = null 
    },
    placeOrder(side) {
      this.confirmSide  = side
      this.confirmPrice  = side === 'buy' ? this.buyPrice  : this.sellPrice 
      this.confirmAmount  = side === 'buy' ? this.buyAmount  : this.sellAmount 
      this.showConfirmModal  = true
    },
    confirmOrder() {
      const orderData = {
        symbol: this.selectedSymbol, 
        side: this.confirmSide, 
        type: this.confirmPrice  ? 'limit' : 'market',
        amount: this.confirmAmount, 
        price: this.confirmPrice, 
        leverage: this.leverage 
      }
      
      this.$store.dispatch('placeOrder',  orderData).then(() => {
        this.$notify({
          title: '订单已提交',
          message: `${this.confirmSide  === 'buy' ? '买入' : '卖出'} ${this.confirmAmount}  ${this.baseAsset}`, 
          type: 'success'
        })
        this.resetForm() 
      }).catch(err => {
        this.$notify.error({ 
          title: '下单失败',
          message: err.message  
        })
      })
      
      this.showConfirmModal  = false
    },
    closePosition() {
      this.$confirm(`确认平仓 ${this.currentPosition.amount}  ${this.baseAsset}?`,  '提示', {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        return this.$store.dispatch('closePosition',  this.selectedSymbol) 
      }).then(() => {
        this.$notify({
          title: '平仓成功',
          type: 'success'
        })
      }).catch(err => {
        if (err !== 'cancel') {
          this.$notify.error({ 
            title: '平仓失败',
            message: err.message 
          })
        }
      })
    },
    updateLeverage() {
      this.$store.dispatch('updateLeverage',  {
        symbol: this.selectedSymbol, 
        leverage: this.leverage 
      }).catch(err => {
        this.$notify.error({ 
          title: '杠杆调整失败',
          message: err.message 
        })
      })
    }
  },
  beforeDestroy() {
    if (this.marketDataSubscription)  {
      this.marketDataSubscription.unsubscribe() 
    }
  }
}
</script>
 
<style scoped>
.trade-panel {
  display: grid;
  grid-template-rows: auto 1fr;
  gap: 16px;
  height: 100%;
  color: #e0e0e0;
}
 
.market-header {
  background: #2a2a3c;
  border-radius: 8px;
  padding: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
 
.symbol-selector {
  display: flex;
  align-items: center;
  gap: 12px;
}
 
.symbol-selector select {
  background: #3a3a4c;
  border: none;
  color: white;
  padding: 6px 12px;
  border-radius: 4px;
  font-weight: bold;
}
 
.price-display {
  font-size: 18px;
  font-weight: bold;
  font-family: 'Courier New', monospace;
}
 
.price-display.up  {
  color: #00e676;
}
 
.price-display.down  {
  color: #ff4757;
}
 
.price-change {
  font-size: 14px;
}
 
.market-stats {
  display: flex;
  gap: 20px;
}
 
.stat-item {
  display: flex;
  flex-direction: column;
}
 
.stat-label {
  font-size: 12px;
  color: #b8b8d1;
}
 
.stat-value {
  font-size: 14px;
  font-weight: bold;
}
 
.trade-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
 
.action-group {
  background: #2a2a3c;
  border-radius: 8px;
  padding: 16px;
}
 
.action-group h3 {
  margin-top: 0;
  margin-bottom: 16px;
  font-size: 16px;
}
 
.buy-group h3 {
  color: #00e676;
}
 
.sell-group h3 {
  color: #ff4757;
}
 
.form-row {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
}
 
.form-row label {
  width: 60px;
  font-size: 14px;
}
 
.form-row input {
  flex: 1;
  background: #3a3a4c;
  border: 1px solid #4a4a5c;
  color: white;
  padding: 8px 12px;
  border-radius: 4px;
}
 
.form-row .asset-unit {
  margin-left: 8px;
  font-size: 14px;
  color: #b8b8d1;
}
 
.calculated-value {
  flex: 1;
  padding: 8px 0;
}
 
.action-btn {
  width: 100%;
  padding: 10px;
  border: none;
  border-radius: 4px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 8px;
}
 
.buy-btn {
  background: linear-gradient(90deg, #00e676, #00ff88);
  color: #1e1e2d;
}
 
.buy-btn:hover {
  opacity: 0.9;
}
 
.buy-btn:disabled {
  background: #3a3a4c;
  color: #6a6a7c;
  cursor: not-allowed;
}
 
.sell-btn {
  background: linear-gradient(90deg, #ff4757, #ff6b81);
  color: white;
}
 
.sell-btn:hover {
  opacity: 0.9;
}
 
.sell-btn:disabled {
  background: #3a3a4c;
  color: #6a6a7c;
  cursor: not-allowed;
}
 
.position-info,
.leverage-settings {
  background: #2a2a3c;
  border-radius: 8px;
  padding: 16px;
}
 
.position-info h3,
.leverage-settings h3 {
  margin-top: 0;
  margin-bottom: 16px;
  font-size: 16px;
}
 
.position-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
 
.position-row {
  display: flex;
  justify-content: space-between;
}
 
.position-row .label {
  color: #b8b8d1;
}
 
.position-row .value {
  font-weight: bold;
}
 
.value.long  {
  color: #00e676;
}
 
.value.short  {
  color: #ff4757;
}
 
.value.profit  {
  color: #00e676;
}
 
.value.loss  {
  color: #ff4757;
}
 
.no-position {
  text-align: center;
  padding: 20px;
  color: #6a6a7c;
}
 
.close-btn {
  margin-top: 12px;
  width: 100%;
  padding: 8px;
  background: #ff4757;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
 
.close-btn:hover {
  background: #ff6b81;
}
 
.leverage-control {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
 
.leverage-control input[type="range"] {
  flex: 1;
  height: 4px;
  -webkit-appearance: none;
  background: #3a3a4c;
  border-radius: 2px;
  outline: none;
}
 
.leverage-control input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  background: #6e45e2;
  border-radius: 50%;
  cursor: pointer;
}
 
.leverage-value {
  font-weight: bold;
  min-width: 40px;
  text-align: center;
}
 
.margin-row {
  display: flex;
  justify-content: space-between;
}
 
.margin-row .label {
  color: #b8b8d1;
}
 
/* 模态框样式 */
.modal-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}
 
.modal-container {
  background: #2a2a3c;
  border-radius: 8px;
  padding: 20px;
  width: 400px;
  max-width: 90%;
}
 
.modal-container h3 {
  margin-top: 0;
  color: white;
}
 
.modal-content {
  margin: 20px 0;
  line-height: 1.6;
}
 
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
 
.modal-actions button {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
 
.cancel-btn {
  background: #3a3a4c;
  color: white;
}
 
.cancel-btn:hover {
  background: #4a4a5c;
}
 
.confirm-btn {
  font-weight: bold;
}
 
.confirm-btn.buy  {
  background: #00e676;
  color: #1e1e2d;
}
 
.confirm-btn.sell  {
  background: #ff4757;
  color: white;
}
 
/* 暗黑模式适配 */
@media (prefers-color-scheme: dark) {
  .market-header,
  .action-group,
  .position-info,
  .leverage-settings {
    background: #252537;
  }
  
  .form-row input {
    background: #323248;
    border-color: #424258;
  }
  
  .modal-container {
    background: #252537;
  }
}
</style>
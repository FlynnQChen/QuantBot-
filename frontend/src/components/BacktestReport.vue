<template>
  <div class="backtest-report">
    <!-- 报告头部概览 -->
    <div class="report-header">
      <h2>{{ strategyName }} 回测报告</h2>
      <div class="summary-stats">
        <div class="stat-card total-return">
          <span class="stat-label">总收益率</span>
          <span 
            class="stat-value"
            :class="summaryStats.totalReturn  >= 0 ? 'profit' : 'loss'"
          >
            {{ (summaryStats.totalReturn  * 100).toFixed(2) }}%
          </span>
        </div>
        <div class="stat-card sharpe">
          <span class="stat-label">夏普比率</span>
          <span class="stat-value">
            {{ summaryStats.sharpeRatio.toFixed(2)  }}
          </span>
        </div>
        <div class="stat-card max-drawdown">
          <span class="stat-label">最大回撤</span>
          <span class="stat-value loss">
            {{ (summaryStats.maxDrawdown  * 100).toFixed(2) }}%
          </span>
        </div>
        <div class="stat-card win-rate">
          <span class="stat-label">胜率</span>
          <span class="stat-value">
            {{ (summaryStats.winRate  * 100).toFixed(2) }}%
          </span>
        </div>
      </div>
    </div>
 
    <!-- 主要分析区域 -->
    <div class="analysis-grid">
      <!-- 净值曲线 -->
      <div class="chart-card">
        <h3>净值曲线</h3>
        <line-chart 
          :data="equityCurve"
          :options="equityCurveOptions"
          class="chart-container"
        />
      </div>
 
      <!-- 回撤分析 -->
      <div class="chart-card">
        <h3>回撤分析</h3>
        <bar-chart 
          :data="drawdownData"
          :options="drawdownOptions"
          class="chart-container"
        />
      </div>
 
      <!-- 月度收益热力图 -->
      <div class="chart-card wide-card">
        <h3>月度收益分布</h3>
        <heatmap-chart 
          :data="monthlyReturns"
          :options="heatmapOptions"
          class="chart-container"
        />
      </div>
 
      <!-- 交易信号可视化 -->
      <div class="chart-card wide-card">
        <h3>交易信号</h3>
        <candlestick-chart 
          :ohlc="priceData" 
          :signals="tradeSignals"
          class="chart-container"
        />
      </div>
 
      <!-- 详细统计表格 -->
      <div class="table-card">
        <h3>详细统计数据</h3>
        <div class="table-scroll">
          <table class="stats-table">
            <thead>
              <tr>
                <th>指标</th>
                <th>值</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(value, key) in detailedStats" :key="key">
                <td>{{ getStatLabel(key) }}</td>
                <td :class="getValueClass(key, value)">
                  {{ formatStatValue(key, value) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
 
      <!-- 交易日志 -->
      <div class="table-card">
        <h3>交易记录 (共 {{ trades.length  }} 笔)</h3>
        <div class="table-scroll">
          <table class="trades-table">
            <thead>
              <tr>
                <th>时间</th>
                <th>方向</th>
                <th>价格</th>
                <th>数量</th>
                <th>盈亏</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="(trade, index) in paginatedTrades" 
                :key="index"
                :class="trade.side" 
              >
                <td>{{ formatTime(trade.time)  }}</td>
                <td>{{ trade.side  === 'buy' ? '买入' : '卖出' }}</td>
                <td>{{ trade.price.toFixed(4)  }}</td>
                <td>{{ trade.amount.toFixed(4)  }}</td>
                <td :class="trade.pnl  >= 0 ? 'profit' : 'loss'">
                  {{ trade.pnl.toFixed(4)  }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="pagination-controls">
          <button 
            @click="currentPage--"
            :disabled="currentPage === 1"
          >
            上一页 
          </button>
          <span>第 {{ currentPage }} 页 / 共 {{ totalPages }} 页</span>
          <button 
            @click="currentPage++"
            :disabled="currentPage >= totalPages"
          >
            下一页
          </button>
        </div>
      </div>
    </div>
 
    <!-- 报告导出 -->
    <div class="report-actions">
      <button class="export-btn" @click="exportPDF">
        <i class="export-icon"></i> 导出PDF报告
      </button>
      <button class="export-btn" @click="exportCSV">
        <i class="export-icon"></i> 导出交易记录CSV
      </button>
    </div>
  </div>
</template>
 
<script>
import { format } from 'date-fns'
import { LineChart, BarChart } from 'vue-chartjs'
import HeatmapChart from '@/components/charts/HeatmapChart.vue' 
import CandlestickChart from '@/components/charts/CandlestickChart.vue' 
 
export default {
  components: {
    LineChart,
    BarChart,
    HeatmapChart,
    CandlestickChart 
  },
  props: {
    backtestData: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      currentPage: 1,
      perPage: 10,
      equityCurveOptions: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            type: 'logarithmic',
            title: {
              display: true,
              text: '净值(对数)'
            }
          }
        }
      },
      drawdownOptions: {
        responsive: true,
        scales: {
          y: {
            beginAtZero: true,
            max: 0,
            ticks: {
              callback: value => `${Math.abs(value)}%` 
            }
          }
        }
      },
      heatmapOptions: {
        responsive: true,
        plugins: {
          legend: {
            display: false 
          }
        }
      }
    }
  },
  computed: {
    strategyName() {
      return this.backtestData.strategy  || '自定义策略'
    },
    summaryStats() {
      return this.backtestData.summary  || {}
    },
    detailedStats() {
      return this.backtestData.detailedStats  || {}
    },
    equityCurve() {
      return this.formatChartData( 
        this.backtestData.equityCurve, 
        'rgba(110, 69, 226, 0.8)',
        '净值曲线'
      )
    },
    drawdownData() {
      return this.formatChartData( 
        this.backtestData.drawdowns, 
        'rgba(255, 71, 87, 0.8)',
        '回撤',
        true 
      )
    },
    monthlyReturns() {
      return this.backtestData.monthlyReturns  || {}
    },
    priceData() {
      return this.backtestData.priceData  || []
    },
    tradeSignals() {
      return this.backtestData.signals  || []
    },
    trades() {
      return this.backtestData.trades  || []
    },
    paginatedTrades() {
      const start = (this.currentPage  - 1) * this.perPage 
      return this.trades.slice(start,  start + this.perPage) 
    },
    totalPages() {
      return Math.ceil(this.trades.length  / this.perPage) 
    }
  },
  methods: {
    formatChartData(rawData, borderColor, label, isDrawdown = false) {
      const labels = rawData.map(item  => format(new Date(item[0]), 'MM/dd'))
      const data = rawData.map(item  => isDrawdown ? item[1] * -100 : item[1])
      
      return {
        labels,
        datasets: [{
          label,
          data,
          borderColor,
          backgroundColor: borderColor.replace('0.8',  '0.2'),
          tension: 0.1,
          fill: true 
        }]
      }
    },
    getStatLabel(key) {
      const labels = {
        totalReturn: '总收益率',
        annualizedReturn: '年化收益率',
        sharpeRatio: '夏普比率',
        sortinoRatio: '索提诺比率',
        maxDrawdown: '最大回撤',
        winRate: '胜率',
        profitFactor: '盈亏比',
        avgTrade: '平均每笔收益',
        totalTrades: '总交易次数',
        winningTrades: '盈利交易数',
        losingTrades: '亏损交易数',
        avgWin: '平均盈利',
        avgLoss: '平均亏损'
      }
      return labels[key] || key
    },
    formatStatValue(key, value) {
      if (typeof value === 'number') {
        if (['Rate', 'Ratio', 'Return'].some(k => key.includes(k)))  {
          return (value * 100).toFixed(2) + '%'
        }
        if (value > 1000) {
          return value.toFixed(0) 
        }
        return value.toFixed(4) 
      }
      return value
    },
    getValueClass(key, value) {
      if (typeof value !== 'number') return ''
      
      if (key.includes('Return')  || key.includes('Win'))  {
        return value >= 0 ? 'profit' : 'loss'
      }
      if (key.includes('Drawdown')  || key.includes('Loss'))  {
        return 'loss'
      }
      return ''
    },
    formatTime(timestamp) {
      return format(new Date(timestamp), 'yyyy-MM-dd HH:mm') 
    },
    exportPDF() {
      // 使用html2canvas和jsPDF生成PDF报告 
      this.$emit('export', 'pdf')
    },
    exportCSV() {
      // 生成CSV交易记录 
      this.$emit('export', 'csv')
    }
  }
}
</script>
 
<style scoped>
.backtest-report {
  padding: 20px;
  background: #1e1e2d;
  color: #e0e0e0;
  height: 100%;
  display: flex;
  flex-direction: column;
}
 
.report-header {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #3a3a4c;
}
 
.report-header h2 {
  margin: 0 0 16px;
  color: white;
}
 
.summary-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}
 
.stat-card {
  background: #2a2a3c;
  border-radius: 8px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
 
.stat-card.total-return  {
  border-top: 4px solid #6e45e2;
}
 
.stat-card.sharpe  {
  border-top: 4px solid #00e676;
}
 
.stat-card.max-drawdown  {
  border-top: 4px solid #ff4757;
}
 
.stat-card.win-rate  {
  border-top: 4px solid #ffa502;
}
 
.stat-label {
  font-size: 14px;
  color: #b8b8d1;
  margin-bottom: 8px;
}
 
.stat-value {
  font-size: 24px;
  font-weight: bold;
  font-family: 'Courier New', monospace;
}
 
.stat-value.profit  {
  color: #00e676;
}
 
.stat-value.loss  {
  color: #ff4757;
}
 
.analysis-grid {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto auto auto;
  gap: 16px;
  margin-bottom: 20px;
}
 
.chart-card {
  background: #2a2a3c;
  border-radius: 8px;
  padding: 16px;
}
 
.chart-card h3 {
  margin: 0 0 16px;
  color: white;
}
 
.chart-container {
  height: 300px;
}
 
.wide-card {
  grid-column: span 2;
}
 
.table-card {
  background: #2a2a3c;
  border-radius: 8px;
  padding: 16px;
  grid-column: span 2;
}
 
.table-card h3 {
  margin: 0 0 16px;
  color: white;
}
 
.table-scroll {
  max-height: 300px;
  overflow-y: auto;
}
 
.stats-table, .trades-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
 
.stats-table th, 
.trades-table th {
  background: #3a3a4c;
  color: white;
  padding: 10px;
  text-align: left;
  position: sticky;
  top: 0;
}
 
.stats-table td, 
.trades-table td {
  padding: 10px;
  border-bottom: 1px solid #3a3a4c;
}
 
.stats-table tr:nth-child(even),
.trades-table tr:nth-child(even) {
  background: #2a2a3c;
}
 
.stats-table tr:hover,
.trades-table tr:hover {
  background: #3a3a4c;
}
 
.trades-table .buy {
  background: rgba(0, 230, 118, 0.1);
}
 
.trades-table .sell {
  background: rgba(255, 71, 87, 0.1);
}
 
.profit {
  color: #00e676;
}
 
.loss {
  color: #ff4757;
}
 
.pagination-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 16px;
}
 
.pagination-controls button {
  background: #3a3a4c;
  border: none;
  color: white;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}
 
.pagination-controls button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
 
.report-actions {
  display: flex;
  justify-content: flex-end;
  gap: 16px;
  padding-top: 16px;
  border-top: 1px solid #3a3a4c;
}
 
.export-btn {
  background: #6e45e2;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}
 
.export-btn:hover {
  background: #8a63f2;
}
 
.export-icon {
  display: inline-block;
  width: 16px;
  height: 16px;
  background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg"  viewBox="0 0 24 24" fill="white"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>');
}
 
/* 暗黑模式适配 */
@media (prefers-color-scheme: dark) {
  .backtest-report {
    background: #1e1e2d;
  }
 
  .chart-card,
  .table-card,
  .stat-card {
    background: #252537;
  }
 
  .stats-table tr:nth-child(even),
  .trades-table tr:nth-child(even) {
    background: #252537;
  }
 
  .stats-table tr:hover,
  .trades-table tr:hover {
    background: #323248;
  }
}
 
/* 响应式布局 */
@media (max-width: 768px) {
  .analysis-grid {
    grid-template-columns: 1fr;
  }
 
  .wide-card {
    grid-column: span 1;
  }
 
  .summary-stats {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
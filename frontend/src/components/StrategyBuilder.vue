<template>
  <div class="strategy-builder">
    <!-- 策略构建画布 -->
    <div class="builder-canvas" @dragover.prevent  @drop="handleDrop">
      <!-- 指标节点容器 -->
      <div 
        v-for="(node, index) in nodes" 
        :key="node.id" 
        class="strategy-node"
        :style="nodeStyle(node)"
        @mousedown="startDrag(node.id,  $event)"
      >
        <div class="node-header" :class="`node-type-${node.type}`"> 
          <span class="node-title">{{ nodeLabels[node.type] }}</span>
          <button class="node-remove" @click="removeNode(index)">×</button>
        </div>
        <div class="node-body">
          <!-- 条件节点参数 -->
          <template v-if="node.type  === 'condition'">
            <div class="param-group">
              <label>指标：</label>
              <select v-model="node.params.indicator"> 
                <option v-for="ind in indicators" :value="ind.value">{{  ind.label  }}</option>
              </select>
            </div>
            <div class="param-group">
              <label>比较：</label>
              <select v-model="node.params.operator"> 
                <option v-for="op in operators" :value="op">{{ op }}</option>
              </select>
            </div>
            <div class="param-group">
              <label>阈值：</label>
              <input type="number" v-model.number="node.params.threshold"  step="0.01">
            </div>
          </template>
 
          <!-- 动作节点参数 -->
          <template v-else-if="node.type  === 'action'">
            <div class="param-group">
              <label>操作：</label>
              <select v-model="node.params.action"> 
                <option value="buy">买入</option>
                <option value="sell">卖出</option>
                <option value="close">平仓</option>
              </select>
            </div>
            <div class="param-group">
              <label>数量：</label>
              <input 
                type="number" 
                v-model.number="node.params.amount" 
                :placeholder="amountPlaceholder(node)"
              >
            </div>
          </template>
 
          <!-- 连接点 -->
          <div class="node-connector" @mousedown.stop="startConnection(node.id)"></div> 
        </div>
      </div>
 
      <!-- 连接线 -->
      <svg class="connection-layer">
        <path 
          v-for="(conn, idx) in connections" 
          :key="idx"
          :d="connectionPath(conn)" 
          class="connection-line"
        />
      </svg>
    </div>
 
    <!-- 指标工具箱 -->
    <div class="indicator-toolbox">
      <div 
        v-for="ind in availableIndicators"
        :key="ind.value" 
        class="indicator-item"
        draggable="true"
        @dragstart="dragIndicator = ind"
      >
        {{ ind.label  }}
      </div>
    </div>
 
    <!-- 策略预览 -->
    <div class="strategy-preview">
      <h3>策略逻辑预览</h3>
      <pre class="code-preview">{{ generatedCode }}</pre>
      <div class="preview-actions">
        <button 
          class="btn-save"
          :disabled="!isStrategyValid"
          @click="saveStrategy"
        >
          保存策略 
        </button>
        <button class="btn-test" @click="backtestStrategy">回测</button>
      </div>
    </div>
 
    <!-- 参数校验错误提示 -->
    <transition name="fade">
      <div v-if="validationError" class="validation-error">
        {{ validationError }}
      </div>
    </transition>
  </div>
</template>
 
<script>
import { generateStrategyCode } from '@/utils/strategy-generator'
 
export default {
  name: 'StrategyBuilder',
  data() {
    return {
      dragIndicator: null,
      draggingNode: null,
      startPos: { x: 0, y: 0 },
      connectingFrom: null,
      nodes: [
        {
          id: 'node-1',
          type: 'condition',
          position: { x: 100, y: 50 },
          params: {
            indicator: 'rsi',
            operator: '>',
            threshold: 30
          }
        },
        {
          id: 'node-2',
          type: 'action',
          position: { x: 400, y: 50 },
          params: {
            action: 'buy',
            amount: 100 
          }
        }
      ],
      connections: [
        { from: 'node-1', to: 'node-2' }
      ],
      indicators: [
        { value: 'rsi', label: 'RSI' },
        { value: 'macd', label: 'MACD' },
        { value: 'ma', label: '移动平均线' },
        { value: 'bollinger', label: '布林带' }
      ],
      operators: ['>', '<', '>=', '<=', '==', '!='],
      nodeLabels: {
        condition: '条件',
        action: '动作'
      },
      validationError: null 
    }
  },
  computed: {
    availableIndicators() {
      return this.indicators.filter(ind  => 
        !this.nodes.some(n  => 
          n.type  === 'condition' && n.params.indicator  === ind.value 
        )
      )
    },
    generatedCode() {
      try {
        return generateStrategyCode(this.nodes,  this.connections) 
      } catch (e) {
        return `// 策略不完整\n${e.message}` 
      }
    },
    isStrategyValid() {
      this.validationError  = null 
      
      // 检查节点连接
      if (this.nodes.length  >= 2 && this.connections.length  === 0) {
        this.validationError  = '请连接策略节点'
        return false
      }
 
      // 检查条件节点参数
      const invalidCondition = this.nodes.find(n  => 
        n.type  === 'condition' && (
          isNaN(n.params.threshold)  ||
          n.params.threshold  === ''
        )
      )
      if (invalidCondition) {
        this.validationError  = '请设置有效的指标阈值'
        return false
      }
 
      // 检查动作节点参数
      const invalidAction = this.nodes.find(n  => 
        n.type  === 'action' && (
          isNaN(n.params.amount)  ||
          n.params.amount  <= 0
        )
      )
      if (invalidAction) {
        this.validationError  = '交易数量必须大于零'
        return false 
      }
 
      return true 
    }
  },
  methods: {
    nodeStyle(node) {
      return {
        left: `${node.position.x}px`, 
        top: `${node.position.y}px`, 
        zIndex: this.draggingNode  === node.id  ? 100 : 10 
      }
    },
    handleDrop(e) {
      if (!this.dragIndicator)  return 
      
      const newNode = {
        id: `node-${Date.now()}`, 
        type: 'condition',
        position: { 
          x: e.offsetX  - 100, 
          y: e.offsetY  - 20 
        },
        params: {
          indicator: this.dragIndicator.value, 
          operator: '>',
          threshold: 50 
        }
      }
      
      this.nodes.push(newNode) 
      this.dragIndicator  = null 
    },
    startDrag(nodeId, e) {
      this.draggingNode  = nodeId
      this.startPos  = {
        x: e.clientX, 
        y: e.clientY 
      }
      document.addEventListener('mousemove',  this.handleDrag) 
      document.addEventListener('mouseup',  this.stopDrag) 
    },
    handleDrag(e) {
      if (!this.draggingNode)  return 
      
      const node = this.nodes.find(n  => n.id  === this.draggingNode) 
      if (!node) return
      
      const dx = e.clientX  - this.startPos.x 
      const dy = e.clientY  - this.startPos.y  
      
      node.position.x  += dx 
      node.position.y  += dy
      
      this.startPos  = {
        x: e.clientX, 
        y: e.clientY  
      }
    },
    stopDrag() {
      this.draggingNode  = null 
      document.removeEventListener('mousemove',  this.handleDrag) 
      document.removeEventListener('mouseup',  this.stopDrag) 
    },
    startConnection(nodeId) {
      this.connectingFrom  = nodeId
      document.addEventListener('mousemove',  this.drawTempConnection) 
      document.addEventListener('mouseup',  this.finishConnection) 
    },
    drawTempConnection(e) {
      // 实时绘制临时连接线（需要SVG实现）
    },
    finishConnection(e) {
      if (!this.connectingFrom)  return 
      
      const targetElement = document.elementFromPoint(e.clientX,  e.clientY) 
      if (targetElement?.closest('.node-connector')) {
        const toNode = targetElement.closest('.strategy-node')?.id  
        if (toNode && toNode !== this.connectingFrom)  {
          this.connections.push({ 
            from: this.connectingFrom, 
            to: toNode
          })
        }
      }
      
      this.connectingFrom  = null 
      document.removeEventListener('mousemove',  this.drawTempConnection) 
      document.removeEventListener('mouseup',  this.finishConnection) 
    },
    connectionPath(conn) {
      const fromNode = this.nodes.find(n  => n.id  === conn.from) 
      const toNode = this.nodes.find(n  => n.id  === conn.to) 
      
      if (!fromNode || !toNode) return ''
      
      const startX = fromNode.position.x  + 180
      const startY = fromNode.position.y  + 40 
      const endX = toNode.position.x  
      const endY = toNode.position.y  + 40
      
      const cpx1 = startX + (endX - startX) / 2
      const cpy1 = startY 
      const cpx2 = cpx1 
      const cpy2 = endY
      
      return `M${startX},${startY} C${cpx1},${cpy1} ${cpx2},${cpy2} ${endX},${endY}`
    },
    removeNode(index) {
      const nodeId = this.nodes[index].id 
      this.nodes.splice(index,  1)
      this.connections  = this.connections.filter( 
        conn => conn.from  !== nodeId && conn.to  !== nodeId 
      )
    },
    amountPlaceholder(node) {
      return node.params.action  === 'close' ? '全部平仓' : '输入数量...'
    },
    saveStrategy() {
      if (!this.isStrategyValid)  return
      
      const strategy = {
        name: `自定义策略-${new Date().toLocaleString()}`,
        nodes: this.nodes, 
        connections: this.connections, 
        code: this.generatedCode, 
        createdAt: Date.now() 
      }
      
      this.$emit('save', strategy)
      this.$notify({
        title: '保存成功',
        message: '策略已保存到本地',
        type: 'success'
      })
    },
    backtestStrategy() {
      if (!this.isStrategyValid)  return
      
      this.$emit('backtest', {
        nodes: this.nodes, 
        connections: this.connections  
      })
    }
  }
}
</script>
 
<style scoped>
.strategy-builder {
  display: grid;
  grid-template-columns: 1fr 250px;
  grid-template-rows: auto 200px;
  height: 100%;
  gap: 16px;
  position: relative;
}
 
.builder-canvas {
  grid-column: 1;
  grid-row: 1 / span 2;
  background-color: #2a2a3c;
  border-radius: 8px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}
 
.strategy-node {
  position: absolute;
  width: 200px;
  background: #3a3a4c;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  cursor: move;
  user-select: none;
}
 
.node-header {
  padding: 8px 12px;
  border-radius: 6px 6px 0 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  color: white;
}
 
.node-type-condition {
  background: linear-gradient(90deg, #6e45e2, #8a63f2);
}
 
.node-type-action {
  background: linear-gradient(90deg, #00e676, #00ff88);
}
 
.node-title {
  font-size: 14px;
}
 
.node-remove {
  background: none;
  border: none;
  color: white;
  font-size: 18px;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
}
 
.node-remove:hover {
  color: #ff4757;
}
 
.node-body {
  padding: 12px;
}
 
.param-group {
  margin-bottom: 10px;
}
 
.param-group label {
  display: block;
  font-size: 12px;
  color: #b8b8d1;
  margin-bottom: 4px;
}
 
.param-group select,
.param-group input {
  width: 100%;
  padding: 6px 8px;
  border-radius: 4px;
  border: 1px solid #4a4a5c;
  background: #2a2a3c;
  color: white;
}
 
.node-connector {
  width: 16px;
  height: 16px;
  background: #6e45e2;
  border-radius: 50%;
  position: absolute;
  right: -8px;
  top: 50%;
  transform: translateY(-50%);
  cursor: crosshair;
  border: 2px solid #3a3a4c;
}
 
.node-connector:hover {
  transform: translateY(-50%) scale(1.2);
}
 
.connection-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  overflow: visible;
}
 
.connection-line {
  stroke: #6e45e2;
  stroke-width: 2;
  fill: none;
  marker-end: url(#arrowhead);
}
 
.indicator-toolbox {
  grid-column: 2;
  grid-row: 1;
  background: #2a2a3c;
  border-radius: 8px;
  padding: 12px;
}
 
.indicator-item {
  background: #3a3a4c;
  color: white;
  padding: 8px 12px;
  margin-bottom: 8px;
  border-radius: 4px;
  cursor: grab;
  font-size: 13px;
  transition: all 0.2s;
}
 
.indicator-item:hover {
  background: #4a4a5c;
  transform: translateX(4px);
}
 
.strategy-preview {
  grid-column: 2;
  grid-row: 2;
  background: #2a2a3c;
  border-radius: 8px;
  padding: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
 
.strategy-preview h3 {
  margin: 0 0 12px;
  font-size: 14px;
  color: #b8b8d1;
}
 
.code-preview {
  flex: 1;
  background: #1e1e2d;
  border-radius: 4px;
  padding: 8px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #a9dc76;
  overflow: auto;
  margin: 0;
  white-space: pre-wrap;
}
 
.preview-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}
 
.preview-actions button {
  flex: 1;
  padding: 8px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.2s;
}
 
.btn-save {
  background: linear-gradient(90deg, #6e45e2, #8a63f2);
  color: white;
}
 
.btn-save:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
 
.btn-test {
  background: linear-gradient(90deg, #00e676, #00ff88);
  color: #1e1e2d;
}
 
.validation-error {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: #ff4757;
  color: white;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 14px;
  box-shadow: 0 2px 10px rgba(255, 71, 87, 0.3);
  z-index: 100;
}
 
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}
 
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
 
/* 暗黑模式适配 */
@media (prefers-color-scheme: dark) {
  .builder-canvas,
  .indicator-toolbox,
  .strategy-preview {
    background: #252537;
  }
  
  .strategy-node {
    background: #323248;
  }
  
  .param-group select,
  .param-group input {
    background: #252537;
  }
  
  .code-preview {
    background: #1e1e2d;
  }
}
</style>
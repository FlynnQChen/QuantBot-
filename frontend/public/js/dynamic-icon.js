// 动态交易状态图标
class StatusIcon {
  constructor() {
    this.canvas  = document.createElement('canvas'); 
    this.canvas.width  = this.canvas.height  = 64;
    this.ctx  = this.canvas.getContext('2d'); 
    this.currentProfit  = null;
    
    // 初始化监听 
    if (window.__APP_CONFIG__?.wsUrl) {
      this.initWebSocket(); 
    }
  }
 
  initWebSocket() {
    const ws = new WebSocket(window.__APP_CONFIG__.wsUrl);
    
    ws.onmessage  = (event) => {
      const data = JSON.parse(event.data); 
      this.update(data.profitStatus); 
    };
  }
 
  update(isProfit) {
    if (this.currentProfit  === isProfit) return;
    this.currentProfit  = isProfit;
    
    // 绘制图标
    this.ctx.clearRect(0,  0, 64, 64);
    
    // 背景圆 
    this.ctx.beginPath(); 
    this.ctx.arc(32,  32, 28, 0, Math.PI*2);
    this.ctx.fillStyle  = isProfit ? '#00e67620' : '#ff475720';
    this.ctx.fill(); 
    
    // 边框 
    this.ctx.strokeStyle  = isProfit ? '#00e676' : '#ff4757';
    this.ctx.lineWidth  = 3;
    this.ctx.stroke(); 
    
    // 文字
    this.ctx.font  = 'bold 24px sans-serif';
    this.ctx.textAlign  = 'center';
    this.ctx.textBaseline  = 'middle';
    this.ctx.fillStyle  = '#ffffff';
    this.ctx.fillText('QB',  32, 34);
    
    this.updateFavicon(); 
  }
 
  updateFavicon() {
    const link = document.querySelector("link[rel*='icon']")  || 
                 document.createElement('link'); 
    link.type  = 'image/png';
    link.rel  = 'icon';
    link.href  = this.canvas.toDataURL('image/png'); 
    document.head.appendChild(link); 
  }
}
 
// 启动监听 
new StatusIcon();
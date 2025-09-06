// 实时生成带状态指示的favicon
const canvas = document.createElement('canvas'); 
canvas.width  = 64; 
canvas.height  = 64;
 
function updateFavicon(profit) {
  const ctx = canvas.getContext('2d'); 
  
  // 绘制量子轨道 
  ctx.beginPath(); 
  ctx.arc(32,  32, 28, 0, Math.PI*2);
  ctx.strokeStyle  = profit ? '#00e676' : '#ff4757';
  ctx.lineWidth  = 4;
  ctx.stroke(); 
 
  // 绘制QB字母
  ctx.font  = 'bold 24px sans-serif';
  ctx.fillStyle  = '#1e1e2d';
  ctx.fillText('QB',  16, 38);
 
  // 更新图标 
  const link = document.querySelector("link[rel*='icon']")  || 
               document.createElement('link'); 
  link.type  = 'image/png';
  link.rel  = 'icon';
  link.href  = canvas.toDataURL('image/png'); 
  document.head.appendChild(link); 
}
 
// 示例：根据盈利状态切换 
setInterval(() => {
  const isProfit = new Date().getSeconds() % 2 === 0;
  updateFavicon(isProfit);
}, 1000);
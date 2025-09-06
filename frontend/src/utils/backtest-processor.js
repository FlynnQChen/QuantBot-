export function processBacktestData(rawData) {
  // 计算额外指标
  const processed = {
    ...rawData,
    detailedStats: {
      ...rawData.stats, 
      profitFactor: rawData.stats.grossProfit  / Math.abs(rawData.stats.grossLoss), 
      avgTrade: rawData.stats.netProfit  / rawData.stats.totalTrades, 
      avgWin: rawData.stats.grossProfit  / rawData.stats.winningTrades, 
      avgLoss: rawData.stats.grossLoss  / rawData.stats.losingTrades  
    }
  }
 
  // 生成月度热力图数据 
  if (rawData.dailyReturns)  {
    processed.monthlyReturns  = groupByMonth(rawData.dailyReturns) 
  }
 
  return processed 
}
 
function groupByMonth(dailyData) {
  // 按月份分组计算收益
  // ...
}
import numpy as np 
import pandas as pd
from typing import Dict, List, Optional, Tuple 
from collections import defaultdict
from ..utils.portfolio  import PortfolioAllocator  # 新增资产组合管理工具
 
class MultiBacktestEngine(BacktestEngine):
    """
    多币种回测引擎（继承自BacktestEngine）
    新增功能：
    - 支持多交易对并行回测 
    - 资产组合权重动态调整
    - 跨币种风险暴露控制 
    """
 
    def __init__(self, initial_balance: float = 10000):
        super().__init__(initial_balance)
        self.symbol_data  = {}  # 存储各交易对历史数据 {symbol: klines}
        self.allocator  = PortfolioAllocator(method="risk_parity")  # 资产分配器
 
    def load_data(
        self,
        symbols: List[str],
        klines_map: Dict[str, List[Dict]],
        timeframe: str = '1h',
        start: str = None,
        end: str = None
    ):
        """
        加载多币种历史数据
        :param klines_map: {symbol: klines} 格式的数据字典 
        """
        for symbol, klines in klines_map.items(): 
            df = pd.DataFrame(klines)
            df['timestamp'] = pd.to_datetime(df['time'],  unit='ms')
            df.set_index('timestamp',  inplace=True)
            
            if start:
                df = df[df.index >= pd.to_datetime(start)] 
            if end:
                df = df[df.index <= pd.to_datetime(end)] 
            
            self.symbol_data[symbol]  = resample_klines(df, timeframe)
        logger.info(f" 加载 {len(symbols)} 个交易对数据 | 时间范围: {start} 至 {end}")
 
    def run(
        self,
        commission: float = 0.0005,
        slippage: float = 0.0001,
        rebalance_freq: str = 'W'  # 资产再平衡频率（周/月/季度）
    ) -> Dict[str, Dict]:
        """
        执行多币种回测 
        :return: {
            'portfolio': {总资金曲线和绩效},
            'symbols': {各币种详细交易记录}
        }
        """
        # 初始化资产组合 
        portfolio = defaultdict(float)
        portfolio['USDT'] = self.initial_balance  
        results = {sym: {'trades': []} for sym in self.symbol_data.keys()} 
        
        # 获取统一时间轴
        timestamps = self._get_aligned_timestamps()
        
        for i, ts in enumerate(timestamps):
            # 每日/每周再平衡
            if self._need_rebalance(ts, rebalance_freq):
                weights = self.allocator.calculate_weights( 
                    symbols=list(self.symbol_data.keys()), 
                    volatilities={sym: self._get_recent_volatility(sym, ts) for sym in self.symbol_data} 
                )
                self._rebalance_portfolio(portfolio, weights, ts)
            
            # 遍历所有交易对 
            for symbol in self.symbol_data.keys(): 
                kline = self._get_kline_at(symbol, ts)
                if kline is None:
                    continue
                
                # 执行策略逻辑（继承自父类）
                signal = self._generate_signal(symbol, kline)
                if signal:
                    self._execute_multi_trade(
                        symbol=symbol,
                        signal=signal,
                        portfolio=portfolio,
                        commission=commission,
                        slippage=slippage,
                        timestamp=ts 
                    )
        
        return self._generate_multi_report(results, portfolio)
 
    def _execute_multi_trade(
        self,
        symbol: str,
        signal: Dict,
        portfolio: Dict[str, float],
        commission: float,
        slippage: float,
        timestamp: str 
    ):
        """多币种交易执行（考虑资产组合）"""
        base, quote = symbol.split('/')   # 如BTC/USDT → base=BTC, quote=USDT 
        price = signal['price'] * (1 + np.random.normal(0,  slippage))
        
        # 计算可分配资金 
        allocated = portfolio[quote] * self.allocator.weights.get(symbol,  0)
        amount = allocated / price 
        
        # 记录交易 
        trade = {
            'time': timestamp,
            'symbol': symbol,
            'action': signal['action'],
            'price': price,
            'amount': amount,
            'commission': amount * price * commission 
        }
        
        # 更新资产组合 
        if signal['action'] == 'buy':
            portfolio[quote] -= amount * price 
            portfolio[base] += amount 
        else:
            portfolio[base] -= amount 
            portfolio[quote] += amount * price 
        
        self.history[symbol].append(trade) 
 
    def _generate_multi_report(self, results: Dict, portfolio: Dict) -> Dict:
        """生成多币种报告"""
        # 计算总资金曲线（按最终价格折算为USDT）
        total_value = portfolio['USDT']
        for sym, klines in self.symbol_data.items(): 
            base = sym.split('/')[0] 
            if base in portfolio:
                total_value += portfolio[base] * klines[-1]['close']
        
        # 各币种绩效分析 
        symbol_metrics = {}
        for sym, trades in self.history.items(): 
            df = pd.DataFrame(trades)
            if len(df) == 0:
                continue
                
            df['pnl'] = df['price'].diff() * df['amount']  # 简化计算 
            symbol_metrics[sym] = {
                'total_return': df['pnl'].sum() / self.initial_balance, 
                'win_rate': len(df[df['pnl'] > 0]) / len(df)
            }
        
        return {
            'portfolio': {
                'final_value': total_value,
                'return': total_value / self.initial_balance  - 1,
                'symbol_weights': self.allocator.weights 
            },
            'symbols': symbol_metrics
        }
 
    # ----------- 工具方法 -----------
    def _get_aligned_timestamps(self) -> List[str]:
        """获取所有交易对齐的时间轴（按最低频率）"""
        timestamps = set()
        for sym, data in self.symbol_data.items(): 
            timestamps.update(data['time'].astype(str)) 
        return sorted(timestamps)
 
    def _get_kline_at(self, symbol: str, timestamp: str) -> Optional[Dict]:
        """获取指定时间点的K线"""
        df = self.symbol_data[symbol] 
        return df[df['time'] == timestamp].iloc[0].to_dict() if not df.empty  else None
 
    def _get_recent_volatility(self, symbol: str, timestamp: str) -> float:
        """计算最近波动率（用于资产分配）"""
        window = self.symbol_data[symbol][ 
            (self.symbol_data[symbol]['time']  <= timestamp) & 
            (self.symbol_data[symbol]['time']  >= pd.to_datetime(timestamp)  - pd.Timedelta(days=30))
        ]
        return window['close'].pct_change().std()
 
    def _need_rebalance(self, timestamp: str, freq: str) -> bool:
        """检查是否需要再平衡"""
        dt = pd.to_datetime(timestamp) 
        if freq == 'W':
            return dt.weekday  == 0  # 每周一
        elif freq == 'M':
            return dt.day  == 1  # 每月第一天 
        return False 
 
    def _rebalance_portfolio(self, portfolio: Dict, weights: Dict, timestamp: str):
        """执行资产再平衡"""
        # 实现逻辑需根据交易所API调整 
        logger.info(f"{timestamp}  资产再平衡 | 新权重: {weights}")
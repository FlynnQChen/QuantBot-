import numpy as np
from typing import Dict, Optional 
from .base_strategy import BaseStrategy
from ..utils.logger  import logger
 
class RSIMACDStrategy(BaseStrategy):
    """
    RSI+MACD 组合策略 
    功能：
    - 基于RSI超买超卖和MACD金叉死叉生成信号 
    - 支持动态调整指标参数
    - 适配多交易所（Binance/OKX）
    """
 
    def __init__(self, connector):
        super().__init__(strategy_name="rsi_macd", connector=connector)
        self.exchanges  = ["binance", "okx"]  # 声明支持的交易所
 
    def calculate_rsi(self, closes: list, period: int = None) -> float:
        """计算RSI值"""
        period = period or self.indicators['RSI']['period'] 
        deltas = np.diff(closes) 
        seed = deltas[:period + 1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down 
        return 100 - (100 / (1 + rs))
 
    def calculate_macd(self, closes: list) -> float:
        """计算MACD柱状图值（快速EMA-慢速EMA）"""
        fast_period = self.indicators['MACD']['fast_period'] 
        slow_period = self.indicators['MACD']['slow_period'] 
        ema_fast = np.mean(closes[-fast_period:]) 
        ema_slow = np.mean(closes[-slow_period:]) 
        return ema_fast - ema_slow
 
    def calculate_signals(self, symbol: str, klines: Dict) -> Optional[Dict]:
        """
        生成交易信号（覆盖基类方法）
        :param klines: 包含 'open', 'high', 'low', 'close', 'volume' 的字典 
        :return: {'action': 'buy/sell', 'symbol': str, 'leverage': int} 或 None
        """
        try:
            closes = klines['close']
            if len(closes) < max(self.indicators['MACD']['slow_period'],  self.indicators['RSI']['period']): 
                logger.warning(" 数据不足，跳过信号计算")
                return None 
 
            # 计算指标 
            rsi = self.calculate_rsi(closes) 
            macd = self.calculate_macd(closes) 
            overbought = self.indicators['RSI']['overbought'] 
            oversold = self.indicators['RSI']['oversold'] 
 
            # 信号逻辑
            if rsi < oversold and macd > 0:
                return {
                    'action': 'buy',
                    'symbol': symbol,
                    'leverage': self.indicators.get('leverage',  3)
                }
            elif rsi > overbought and macd < 0:
                return {
                    'action': 'sell',
                    'symbol': symbol,
                    'reduce_only': False  # 允许开空单
                }
            return None
 
        except Exception as e:
            logger.error(f" 信号计算失败: {e}")
            raise 
 
    def execute_trade(self, signal: Dict, exchange: str = 'binance'):
        """
        扩展执行逻辑（支持双线持仓）
        """
        if signal['action'] == 'sell' and self.indicators.get('hedge_mode',  False):
            signal['reduce_only'] = False  # 对冲模式下允许同时持有多空
        super().execute_trade(signal, exchange)
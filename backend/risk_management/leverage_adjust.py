import numpy as np
from typing import Dict, Optional 
from ..api.api_connector  import APIConnector
from ..utils.logger  import logger
from ..utils.data_processor  import calculate_atr  # 假设已有ATR计算工具
 
class LeverageManager:
    """
    智能杠杆调节器
    功能：
    - 基于市场波动率动态调整杠杆
    - 防止保证金不足导致的强平
    - 支持多交易所差异化配置 
    """
 
    def __init__(self, connector: APIConnector):
        self.connector  = connector 
        self.volatility_cache  = {}  # 存储各交易对波动率数据 {symbol: {'atr': float, 'last_updated': timestamp}}
 
    def calculate_volatility(self, symbol: str, klines: Dict) -> float:
        """
        计算交易对的实时波动率（默认使用ATR）
        :param klines: 包含 'high', 'low', 'close', 'time' 的K线数据
        :return: 标准化波动率（0~1）
        """
        atr = calculate_atr(
            highs=np.array(klines['high']), 
            lows=np.array(klines['low']), 
            closes=np.array(klines['close']), 
            period=14 
        )
        self.volatility_cache[symbol]  = {
            'atr': atr,
            'last_updated': klines['time'][-1]
        }
        return atr / klines['close'][-1]  # 转换为价格百分比
 
    def get_safe_leverage(self, symbol: str, exchange: str, volatility: float = None) -> int:
        """
        计算安全杠杆倍数
        :param volatility: 可选手动传入波动率（否则自动计算）
        :return: 推荐杠杆倍数（1~25x）
        """
        # 从交易所获取合约信息 
        contract = self.connector.get_exchange(exchange).fetch_market(symbol) 
        max_leverage = contract.get('limits',  {}).get('leverage', {}).get('max', 25)
 
        # 动态计算杠杆（波动率越高，杠杆越低）
        volatility = volatility or self.volatility_cache.get(symbol,  {}).get('atr', 0.05)
        recommended = min(
            max_leverage,
            int(0.1 / (volatility + 0.01))  # 基础公式：杠杆≈10%风险/波动率 
        )
        return max(1, recommended)  # 至少1倍杠杆
 
    def auto_adjust(self, symbol: str, exchange: str, klines: Dict):
        """
        自动调整杠杆（主入口方法）
        """
        current_leverage = self._get_current_leverage(exchange, symbol)
        volatility = self.calculate_volatility(symbol,  klines)
        safe_leverage = self.get_safe_leverage(symbol,  exchange, volatility)
 
        if current_leverage != safe_leverage:
            self._apply_leverage(exchange, symbol, safe_leverage)
            logger.info(f"{symbol}  杠杆从 {current_leverage}x 调整为 {safe_leverage}x (波动率: {volatility:.2%})")
 
    def _get_current_leverage(self, exchange: str, symbol: str) -> int:
        """获取当前杠杆倍数"""
        try:
            positions = self.connector.get_exchange(exchange).get_positions(symbol) 
            return positions.get('long',  {}).get('leverage', 1) or 1
        except Exception as e:
            logger.warning(f" 获取当前杠杆失败: {e}, 使用默认值1x")
            return 1
 
    def _apply_leverage(self, exchange: str, symbol: str, leverage: int):
        """向交易所提交杠杆调整"""
        try:
            api = self.connector.get_exchange(exchange) 
            api.set_leverage(leverage,  symbol)
        except Exception as e:
            logger.error(f" 杠杆调整失败: {e}")
            raise 
 
    def reset_to_conservative(self, exchange: str, symbol: str):
        """重置为保守杠杆（风控紧急调用）"""
        self._apply_leverage(exchange, symbol, 3) 
        logger.warning(f" 紧急重置 {symbol} 杠杆为3x")
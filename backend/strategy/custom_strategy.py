import numpy as np 
from typing import Dict, Optional
from .base_strategy import BaseStrategy 
from ..utils.logger  import logger 
 
class CustomStrategy(BaseStrategy):
    """
    支持动态指标组合的自定义策略 
    功能：
    - 解析YAML配置的指标和规则 
    - 支持RSI/MACD/MA多指标组合 
    - 集成动态止损参数 
    """
 
    def __init__(self, connector, strategy_config: str = "custom_strategy"):
        super().__init__(strategy_name=strategy_config, connector=connector)
        self.ma_type  = self.indicators['MA'].get('type',  'SMA')  # 默认SMA
 
    def calculate_indicators(self, klines: Dict) -> Dict:
        """计算所有配置文件中定义的指标"""
        closes = klines['close']
        ma_period = self.indicators['MA']['period'] 
        
        return {
            'RSI': self.calculate_rsi(closes), 
            'MACD': self.calculate_macd(closes), 
            'MA': self._calculate_ma(closes, ma_period),
            'close': closes[-1]  # 当前价格用于条件判断 
        }
 
    def _calculate_ma(self, closes: list, period: int) -> float:
        """根据配置类型计算移动平均"""
        if self.ma_type  == "SMA":
            return np.mean(closes[-period:]) 
        elif self.ma_type  == "EMA":
            return np.convolve( 
                closes[-period:], 
                np.exp(np.linspace(-1,  0, period)), 
                mode='valid'
            )[0]
        else:
            raise ValueError(f"不支持的MA类型: {self.ma_type}") 
 
    def calculate_signals(self, symbol: str, klines: Dict) -> Optional[Dict]:
        """
        执行用户自定义规则 
        示例规则条件: 
        - "RSI < 30 and MACD > 0 and close > MA"
        - "RSI > 70 and MACD < 0"
        """
        try:
            indicator_values = self.calculate_indicators(klines) 
            
            # 动态执行所有规则
            for rule in self.rule_engine: 
                if rule['func'](**indicator_values):
                    return {
                        'action': rule['action'],
                        'symbol': symbol,
                        'leverage': self.indicators.get('leverage',  3),
                        'stop_loss': self._get_stop_price(  # 动态计算初始止损价
                            entry_price=indicator_values['close'],
                            side=rule['action'].split('_')[-1]  # 从open_long提取long
                        )
                    }
            return None
 
        except Exception as e:
            logger.error(f" 信号生成失败: {e}")
            raise 
 
    def _get_stop_price(self, entry_price: float, side: str) -> float:
        """根据风险参数计算初始止损价"""
        risk_config = self.indicators.get('risk_params',  {}).get('trailing_stop', {})
        risk_pct = risk_config.get('initial_risk',  0.02)
        
        return ( 
            entry_price * (1 - risk_pct) if side == 'long' 
            else entry_price * (1 + risk_pct)
        )
 
    # ----------- 复用父类指标计算 -----------
    def calculate_rsi(self, closes: list, period: int = None) -> float:
        """同RSIMACDStrategy"""
        period = period or self.indicators['RSI']['period'] 
        deltas = np.diff(closes) 
        up = deltas[deltas >= 0].mean()
        down = -deltas[deltas < 0].mean()
        return 100 - (100 / (1 + (up / down)))
 
    def calculate_macd(self, closes: list) -> float:
        """同RSIMACDStrategy"""
        fast = np.mean(closes[-self.indicators['MACD']['fast_period']:]) 
        slow = np.mean(closes[-self.indicators['MACD']['slow_period']:]) 
        return fast - slow
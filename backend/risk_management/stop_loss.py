from typing import Dict, Optional 
from ..api.api_connector  import APIConnector
from ..utils.logger  import logger
import numpy as np 
 
class StopLossManager:
    """
    多级止损与止盈控制器
    功能：
    - 动态追踪止损（Trailing Stop）
    - 分仓位独立止损控制 
    - 盈利回撤保护（Drawdown Protection）
    """
 
    def __init__(self, connector: APIConnector):
        self.connector  = connector 
        self.active_stops  = {}  # 存储活跃止损单 {symbol: {'price': float, 'side': str}}
 
    def calculate_trailing_stop(self, current_price: float, entry_price: float, side: str, 
                              atr: float = None) -> float:
        """
        计算动态追踪止损价
        :param atr: 平均真实波幅（可选，用于波动性调整）
        :return: 止损价
        """
        # 从配置加载参数（示例值，实际从策略配置读取）
        stop_config = {
            'initial_risk': 0.02,    # 初始风险2%
            'trailing_ratio': 0.5,   # 盈利50%后启动追踪 
            'min_trail': 0.01        # 最小追踪距离1%
        }
        
        if side == 'long':
            # 多头止损逻辑 
            initial_stop = entry_price * (1 - stop_config['initial_risk'])
            if current_price <= initial_stop:
                return initial_stop 
            
            profit_ratio = (current_price - entry_price) / entry_price 
            if profit_ratio >= stop_config['trailing_ratio']:
                trail_distance = max( 
                    stop_config['min_trail'],
                    atr * 0.5 if atr else stop_config['initial_risk'] / 2 
                )
                return current_price * (1 - trail_distance)
            return initial_stop
        
        else:  # 空头止损逻辑（对称）
            initial_stop = entry_price * (1 + stop_config['initial_risk'])
            if current_price >= initial_stop:
                return initial_stop 
            
            profit_ratio = (entry_price - current_price) / entry_price 
            if profit_ratio >= stop_config['trailing_ratio']:
                trail_distance = max(
                    stop_config['min_trail'],
                    atr * 0.5 if atr else stop_config['initial_risk'] / 2
                )
                return current_price * (1 + trail_distance)
            return initial_stop 
 
    def check_position_stop(self, exchange: str, symbol: str, price_data: Dict) -> Optional[str]:
        """
        检查持仓是否触发止损
        :param price_data: 包含最新价格和指标的数据 {'close': float, 'atr': float}
        :return: 'stop_loss' 或 'take_profit' 或 None
        """
        positions = self.connector.get_exchange(exchange).get_positions(symbol) 
        current_price = price_data['close']
        
        for side, pos in positions.items(): 
            if not pos.get('size',  0):
                continue 
                
            entry_price = pos['entry_price']
            stop_price = self.calculate_trailing_stop( 
                current_price=current_price,
                entry_price=entry_price,
                side=side,
                atr=price_data.get('atr') 
            )
            
            # 多头止损检查 
            if side == 'long' and current_price <= stop_price:
                return 'stop_loss'
            # 空头止损检查 
            elif side == 'short' and current_price >= stop_price:
                return 'stop_loss'
        
        return None
 
    def execute_stop(self, exchange: str, symbol: str, stop_type: str):
        """执行止损/止盈操作"""
        try:
            api = self.connector.get_exchange(exchange) 
            positions = api.get_positions(symbol) 
            
            for side, pos in positions.items(): 
                if not pos.get('size',  0):
                    continue 
                    
                api.create_order( 
                    symbol=symbol,
                    side='sell' if side == 'long' else 'buy',
                    amount=pos['size'],
                    reduce_only=True,
                    params={'stopLoss': True}  # 标记为止损单（部分交易所支持）
                )
            logger.warning(f"{stop_type}  触发: {symbol}")
            
        except Exception as e:
            logger.error(f" 止损执行失败: {e}")
            raise 
 
    def update_active_stops(self, exchange: str, symbol: str, price_data: Dict):
        """更新动态止损单（适用于交易所不支持本地止损的场景）"""
        current_price = price_data['close']
        if symbol not in self.active_stops: 
            return
            
        stop_info = self.active_stops[symbol] 
        if ((stop_info['side'] == 'long' and current_price <= stop_info['price']) or
            (stop_info['side'] == 'short' and current_price >= stop_info['price'])):
            self.execute_stop(exchange,  symbol, 'trailing_stop')
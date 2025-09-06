from typing import Dict, List, Optional
from ..api.api_connector  import APIConnector 
from ..utils.logger  import logger 
import numpy as np
 
class PositionControl:
    """
    持仓与风控管理器
    功能：
    - 监控多空仓位平衡 
    - 动态调整杠杆和保证金
    - 强制平仓和止损控制 
    """
 
    def __init__(self, connector: APIConnector):
        self.connector  = connector
        self.max_risk_per_trade  = 0.02  # 单笔交易最大风险（占本金比例）
        self.global_stop_loss  = -0.15   # 全局止损线（-15%）
 
    def get_hedge_positions(self, exchange: str, symbol: str) -> Dict[str, Dict]:
        """
        获取对冲仓位信息（多空分离）
        :return: {'long': {size, entry_price, ...}, 'short': {...}}
        """
        try:
            positions = self.connector.get_exchange(exchange).get_positions(symbol) 
            return {
                'long': positions.get('long',  {}),
                'short': positions.get('short',  {})
            }
        except Exception as e:
            logger.error(f" 获取对冲仓位失败: {e}")
            raise 
 
    def calculate_position_size(self, balance: float, price: float, risk_pct: float = None) -> float:
        """
        根据风险计算开仓量 
        :param balance: 可用保证金
        :param price: 当前价格 
        :param risk_pct: 可选覆盖默认风险比例 
        """
        risk = risk_pct or self.max_risk_per_trade 
        return (balance * risk) / price 
 
    def check_stop_conditions(self, exchange: str, symbol: str) -> Optional[str]:
        """
        检查是否触发止损 
        :return: 'global_stop'（全局止损）或 'position_stop'（单仓位止损）
        """
        positions = self.get_hedge_positions(exchange,  symbol)
        balance = self.connector.get_exchange(exchange).get_balance()['total'] 
 
        # 全局止损检查 
        if balance <= self.global_stop_loss: 
            return 'global_stop'
 
        # 单仓位止损检查（示例：亏损超过5%）
        for side, pos in positions.items(): 
            if pos.get('unrealized_pnl',  0) / pos.get('initial_margin',  1) < -0.05:
                return 'position_stop'
        return None
 
    def adjust_leverage(self, exchange: str, symbol: str, leverage: int):
        """动态调整杠杆（根据波动率模型）"""
        try:
            api = self.connector.get_exchange(exchange) 
            api.set_leverage(leverage,  symbol)
            logger.info(f"{symbol}  杠杆调整为 {leverage}x")
        except Exception as e:
            logger.error(f" 杠杆调整失败: {e}")
 
    def close_all_positions(self, exchange: str, symbol: str, reason: str):
        """强制平仓（多空同时平仓）"""
        try:
            api = self.connector.get_exchange(exchange) 
            positions = self.get_hedge_positions(exchange,  symbol)
 
            for side in ['long', 'short']:
                if positions[side].get('size', 0) > 0:
                    api.create_order( 
                        symbol=symbol,
                        side='sell' if side == 'long' else 'buy',
                        amount=positions[side]['size'],
                        reduce_only=True
                    )
            logger.warning(f" 强制平仓 {symbol}（原因: {reason}）")
        except Exception as e:
            logger.error(f" 平仓失败: {e}")
            raise
 
    def hedge_rebalance(self, exchange: str, symbol: str):
        """
        对冲再平衡（确保多空仓位价值相等）
        说明：需在config中启用 'hedge_mode'
        """
        positions = self.get_hedge_positions(exchange,  symbol)
        long_val = positions['long'].get('notional', 0)
        short_val = positions['short'].get('notional', 0)
 
        if abs(long_val - short_val) > max(long_val, short_val) * 0.1:  # 价值差超过10%
            logger.info(f" 对冲再平衡: long={long_val}, short={short_val}")
            # 实现自动平衡逻辑（需根据交易所API调整）
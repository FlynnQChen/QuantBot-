from datetime import datetime
from typing import Dict, List, Optional, Union 
from enum import Enum, auto
from pydantic import BaseModel, validator, root_validator
from ..utils.logger  import logger
import numpy as np 
 
class PositionSide(Enum):
    """持仓方向枚举"""
    LONG = auto()      # 多头持仓
    SHORT = auto()     # 空头持仓 
    NET = auto()       # 净持仓（单向模式）
 
class PositionStatus(Enum):
    """持仓状态枚举"""
    OPEN = auto()      # 持仓中 
    CLOSING = auto()   # 平仓中 
    CLOSED = auto()    # 已平仓
    LIQUIDATED = auto() # 已被强平 
 
class Position(BaseModel):
    """
    统一持仓模型 
    字段说明：
    - symbol: 交易对 BTC/USDT
    - side: 持仓方向
    - status: 持仓状态 
    - entry_price: 开仓均价 
    - current_price: 当前标记价格
    - amount: 持仓数量（正向）
    - leverage: 杠杆倍数 
    - liquidation_price: 强平价格 
    - unrealized_pnl: 未实现盈亏（当前价值）
    - realized_pnl: 已实现盈亏（平仓部分）
    - fees: 累计手续费 
    - opened_at: 开仓时间戳（毫秒）
    - updated_at: 最后更新时间戳 
    - meta: 交易所原始数据（备用）
    """
    # 核心字段
    symbol: str 
    side: PositionSide 
    status: PositionStatus = PositionStatus.OPEN
    entry_price: float
    current_price: float 
    amount: float
    leverage: int = 1
 
    # 动态计算字段
    liquidation_price: Optional[float] = None 
    unrealized_pnl: Optional[float] = None
    realized_pnl: float = 0.0
    fees: Dict[str, float] = {}  # {'open': 0.001, 'close': 0.002}
 
    # 时间字段 
    opened_at: int = int(datetime.now().timestamp()  * 1000)
    updated_at: Optional[int] = None
 
    # 元数据
    meta: Dict = {}
 
    class Config:
        json_encoders = {
            datetime: lambda dt: int(dt.timestamp()  * 1000),
            Enum: lambda e: e.name  
        }
        use_enum_values = True 
 
    @validator('symbol')
    def validate_symbol(cls, v):
        """验证交易对格式"""
        if '/' not in v:
            raise ValueError('symbol must contain "/" (e.g. BTC/USDT)')
        return v.upper() 
 
    @root_validator(pre=True)
    def calculate_dynamic_fields(cls, values):
        """计算动态字段（强平价、未实现盈亏等）"""
        side = values.get('side') 
        entry = values.get('entry_price') 
        current = values.get('current_price',  entry)
        amount = values.get('amount',  0)
        leverage = values.get('leverage',  1)
 
        if None in (side, entry, amount):
            return values 
 
        # 计算未实现盈亏 
        if side == PositionSide.LONG:
            values['unrealized_pnl'] = (current - entry) * amount 
        else:
            values['unrealized_pnl'] = (entry - current) * amount 
 
        # 计算强平价格（简化版，实际需考虑保证金率）
        if leverage > 1:
            if side == PositionSide.LONG:
                values['liquidation_price'] = entry * (1 - 1/leverage)
            else:
                values['liquidation_price'] = entry * (1 + 1/leverage)
 
        return values
 
    def update_from_exchange(self, exchange_data: Dict):
        """
        根据交易所数据更新持仓
        :param exchange_data: CCXT格式的持仓数据 
        """
        try:
            self.current_price  = float(exchange_data['markPrice'])
            self.amount  = float(exchange_data['positionAmt'])
            self.entry_price  = float(exchange_data['entryPrice'])
            self.leverage  = int(exchange_data['leverage'])
            self.unrealized_pnl  = float(exchange_data['unrealizedPnl'])
            self.liquidation_price  = float(exchange_data.get('liquidationPrice',  0))
            self.updated_at  = exchange_data.get('timestamp')  or int(datetime.now().timestamp()  * 1000)
            self.meta  = exchange_data 
        except Exception as e:
            logger.error(f" 持仓更新失败: {e}")
            raise
 
    def close(self, close_price: float, fee: float = 0.0):
        """平仓操作（更新状态和已实现盈亏）"""
        if self.status  != PositionStatus.OPEN:
            raise ValueError("只能平仓OPEN状态的持仓")
 
        self.status  = PositionStatus.CLOSED 
        self.current_price  = close_price 
        self.realized_pnl  = self.unrealized_pnl 
        self.unrealized_pnl  = 0 
        self.fees['close']  = fee
        self.updated_at  = int(datetime.now().timestamp()  * 1000)
 
    def pnl_percentage(self) -> float:
        """计算收益率（基于保证金）"""
        margin = (self.entry_price  * self.amount)  / self.leverage 
        return (self.unrealized_pnl  or 0) / margin if margin != 0 else 0
 
    def risk_ratio(self) -> float:
        """计算风险率（距强平价距离）"""
        if not self.liquidation_price: 
            return 0.0
            
        if self.side  == PositionSide.LONG:
            return (self.current_price  - self.liquidation_price)  / self.current_price  
        else:
            return (self.liquidation_price  - self.current_price)  / self.current_price 
 
class PositionBook:
    """持仓集合管理器（多空分开维护）"""
    def __init__(self):
        self.positions:  Dict[str, Dict[PositionSide, Position]] = {}  # {symbol: {side: Position}}
 
    def update_or_add(self, position: Position):
        """更新或添加持仓"""
        if position.symbol  not in self.positions: 
            self.positions[position.symbol]  = {}
        
        self.positions[position.symbol][position.side]  = position
 
    def get_position(self, symbol: str, side: PositionSide) -> Optional[Position]:
        """获取指定方向的持仓"""
        return self.positions.get(symbol,  {}).get(side)
 
    def get_net_position(self, symbol: str) -> Optional[Position]:
        """获取净持仓（多头-空头）"""
        long = self.get_position(symbol,  PositionSide.LONG)
        short = self.get_position(symbol,  PositionSide.SHORT)
        
        if not long and not short:
            return None 
            
        return Position(
            symbol=symbol,
            side=PositionSide.NET,
            entry_price=(
                (long.entry_price  * long.amount  - short.entry_price  * short.amount)  / 
                (long.amount  - short.amount)  if long and short else 
                long.entry_price  if long else short.entry_price 
            ),
            amount=abs((long.amount  if long else 0) - (short.amount  if short else 0)),
            current_price=long.current_price  if long else short.current_price, 
            leverage=max(
                long.leverage  if long else 1, 
                short.leverage  if short else 1
            )
        )
 
    def clean_closed_positions(self):
        """清理已关闭的持仓"""
        for symbol in list(self.positions.keys()): 
            for side in list(self.positions[symbol].keys()): 
                if self.positions[symbol][side].status  in (
                    PositionStatus.CLOSED, 
                    PositionStatus.LIQUIDATED
                ):
                    del self.positions[symbol][side] 
            
            if not self.positions[symbol]: 
                del self.positions[symbol] 
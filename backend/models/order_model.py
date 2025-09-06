from datetime import datetime 
from typing import Dict, List, Optional, Union 
from enum import Enum, auto
from pydantic import BaseModel, validator
from ..utils.logger  import logger
 
class OrderStatus(Enum):
    """订单状态枚举"""
    NEW = auto()          # 已创建未提交 
    PENDING = auto()      # 已提交未成交 
    PARTIALLY_FILLED = auto()  # 部分成交 
    FILLED = auto()       # 完全成交
    CANCELED = auto()     # 已取消 
    REJECTED = auto()     # 被拒绝
    EXPIRED = auto()      # 已过期
 
class OrderType(Enum):
    """订单类型枚举"""
    MARKET = auto()       # 市价单
    LIMIT = auto()        # 限价单 
    STOP = auto()         # 止损单
    TAKE_PROFIT = auto()  # 止盈单
    FOK = auto()          # 全部成交或取消 
    IOC = auto()          # 立即成交或取消
 
class OrderSide(Enum):
    """订单方向枚举"""
    BUY = auto()          # 买入 
    SELL = auto()         # 卖出
 
class Order(BaseModel):
    """
    统一订单模型（兼容多交易所）
    字段说明：
    - exchange_order_id: 交易所订单ID（成交后生成）
    - client_order_id: 客户端自定义ID（策略生成）
    - symbol: 交易对 BTC/USDT
    - side: 买卖方向
    - type: 订单类型
    - status: 订单状态
    - price: 下单价格（市价单可为None）
    - amount: 下单数量（市价单可能为quote数量）
    - filled: 已成交数量
    - remaining: 剩余数量
    - cost: 已成交总金额（数量×均价）
    - fee: 手续费（成交后更新）
    - created_at: 创建时间戳（毫秒）
    - updated_at: 最后更新时间戳 
    - params: 交易所特定参数（如post_only）
    """
    # 必填字段 
    symbol: str
    side: OrderSide 
    type: OrderType 
    status: OrderStatus = OrderStatus.NEW
    
    # 可选字段
    exchange_order_id: Optional[str] = None 
    client_order_id: Optional[str] = None
    price: Optional[float] = None
    amount: Optional[float] = None
    filled: float = 0.0 
    remaining: Optional[float] = None 
    cost: float = 0.0 
    fee: Optional[Dict[str, float]] = None  # {'currency': 'USDT', 'cost': 0.05}
    created_at: int = int(datetime.now().timestamp()  * 1000)
    updated_at: Optional[int] = None 
    params: Dict = {}
 
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
 
    @validator('price', 'amount', 'filled', 'cost', pre=True)
    def validate_non_negative(cls, v):
        """验证数值非负"""
        if v is not None and float(v) < 0:
            raise ValueError('value cannot be negative')
        return v 
 
    def update_from_exchange(self, exchange_data: Dict):
        """
        根据交易所数据更新订单 
        :param exchange_data: CCXT格式的订单数据 
        """
        try:
            self.status  = OrderStatus[exchange_data['status'].upper()]
            self.filled  = float(exchange_data['filled'])
            self.remaining  = float(exchange_data['remaining']) if 'remaining' in exchange_data else None
            self.cost  = float(exchange_data['cost']) if 'cost' in exchange_data else 0.0 
            self.fee  = exchange_data.get('fee') 
            self.updated_at  = exchange_data.get('timestamp')  or int(datetime.now().timestamp()  * 1000)
            
            if 'id' in exchange_data:
                self.exchange_order_id  = str(exchange_data['id'])
        except Exception as e:
            logger.error(f" 订单更新失败: {e}")
            raise 
 
    def to_exchange_format(self, exchange: str) -> Dict:
        """
        转换为交易所特定格式
        :param exchange: binance/okx等 
        :return: 交易所API所需的订单参数 
        """
        common = {
            'symbol': self.symbol, 
            'side': self.side.name.lower(), 
            'type': self.type.name.lower(), 
            'amount': self.amount, 
            'clientOrderId': self.client_order_id, 
            **self.params  
        }
 
        if self.price  is not None:
            common['price'] = self.price 
 
        # 交易所特定适配
        if exchange == 'binance':
            return {**common, 'newClientOrderId': self.client_order_id} 
        elif exchange == 'okx':
            return {**common, 'clOrdId': self.client_order_id} 
        else:
            return common 
 
    def is_active(self) -> bool:
        """检查订单是否仍活跃（可成交）"""
        return self.status  in [ 
            OrderStatus.NEW,
            OrderStatus.PENDING,
            OrderStatus.PARTIALLY_FILLED
        ]
 
    def is_closed(self) -> bool:
        """检查订单是否已结束"""
        return self.status  in [
            OrderStatus.FILLED,
            OrderStatus.CANCELED,
            OrderStatus.REJECTED,
            OrderStatus.EXPIRED
        ]
 
class OrderBook:
    """订单集合管理器（用于策略内部跟踪）"""
    def __init__(self):
        self.orders:  Dict[str, Order] = {}  # {client_order_id: Order}
 
    def add(self, order: Order):
        """添加新订单"""
        if order.client_order_id  in self.orders: 
            raise ValueError(f"订单已存在: {order.client_order_id}") 
        self.orders[order.client_order_id]  = order
 
    def update(self, client_order_id: str, updates: Dict) -> Optional[Order]:
        """更新订单状态"""
        if client_order_id not in self.orders: 
            logger.warning(f" 订单不存在: {client_order_id}")
            return None 
        
        order = self.orders[client_order_id] 
        for k, v in updates.items(): 
            if hasattr(order, k):
                setattr(order, k, v)
        order.updated_at  = int(datetime.now().timestamp()  * 1000)
        return order 
 
    def get_active_orders(self, symbol: str = None) -> List[Order]:
        """获取活跃订单列表"""
        return [
            o for o in self.orders.values()  
            if o.is_active()  and (symbol is None or o.symbol  == symbol)
        ]
 
    def clean_closed_orders(self, max_age_sec: int = 86400):
        """清理已关闭的旧订单"""
        now = datetime.now().timestamp() 
        to_delete = [
            id_ for id_, o in self.orders.items() 
            if o.is_closed()  and (now - o.updated_at/1000)  > max_age_sec
        ]
        for id_ in to_delete:
            del self.orders[id_] 
import os 
import ccxt 
from typing import Dict, Optional, Union
from ..utils.logger  import logger 
from ..utils.data_parser  import parse_kline_data 
import yaml 
 
class BinanceAPI:
    """Binance 合约交易API封装（支持实盘/测试网切换）"""
    
    def __init__(self, api_key: str = "", api_secret: str = "", testnet: bool = False):
        """
        初始化Binance连接 
        :param api_key: 用户输入的API Key 
        :param api_secret: 用户输入的API Secret
        :param testnet: 是否使用测试网 
        """
        self.api_key  = api_key 
        self.api_secret  = api_secret 
        self.testnet  = testnet 
        self.exchange  = self._init_exchange()
        self.load_config() 
        
    def _init_exchange(self) -> ccxt.binance: 
        """初始化CCXT Binance实例"""
        config = {
            'apiKey': self.api_key, 
            'secret': self.api_secret, 
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future'
            }
        }
        
        if self.testnet: 
            config['urls'] = {'api': 'https://testnet.binancefuture.com'} 
            
        return ccxt.binance(config) 
    
    def load_config(self):
        """从configs/exchanges.yaml 加载端点配置"""
        config_path = os.path.join(os.path.dirname(__file__),  '../../configs/exchanges.yaml') 
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) 
            if self.testnet: 
                self.base_url  = config['binance']['testnet']['api_base']
            else:
                self.base_url  = config['binance']['real']['api_base']
    
    # --------------- 账户相关 ---------------
    def get_balance(self) -> Dict[str, float]:
        """获取合约账户USDT余额"""
        try:
            balance = self.exchange.fetch_balance() 
            return {
                'total': balance['total']['USDT'],
                'free': balance['free']['USDT'],
                'used': balance['used']['USDT']
            }
        except Exception as e:
            logger.error(f" 获取余额失败: {e}")
            raise 
    
    # --------------- 交易相关 ---------------
    def create_order(
        self,
        symbol: str,
        side: str,  # 'buy' or 'sell'
        order_type: str = 'market',
        amount: float = 0.0,
        price: Optional[float] = None,
        leverage: int = 1,
        reduce_only: bool = False
    ) -> Dict:
        """
        创建合约订单
        :param symbol: 交易对如 'BTC/USDT'
        :param side: 方向 (buy/sell)
        :param order_type: 订单类型 (market/limit)
        :param amount: 数量（以币为单位）
        :param price: 限价单价格
        :param leverage: 杠杆倍数
        :param reduce_only: 是否仅减仓 
        """
        try:
            # 先设置杠杆 
            self.exchange.set_leverage(leverage,  symbol)
            
            # 下单 
            order = self.exchange.create_order( 
                symbol=symbol,
                type=order_type,
                side=side,
                amount=amount,
                price=price,
                params={'reduceOnly': reduce_only}
            )
            logger.info(f" 订单创建成功: {order}")
            return order
        except Exception as e:
            logger.error(f" 下单失败: {e}")
            raise
    
    # --------------- 数据获取 ---------------
    def fetch_klines(
        self,
        symbol: str,
        timeframe: str = '1h',
        limit: int = 1000
    ) -> Dict:
        """获取K线数据（用于回测和实时分析）"""
        try:
            klines = self.exchange.fetch_ohlcv(symbol,  timeframe, limit=limit)
            return parse_kline_data(klines)  # 使用utils中的数据处理 
        except Exception as e:
            logger.error(f" 获取K线失败: {e}")
            raise 
 
    # --------------- 测试网切换 ---------------
    def switch_testnet(self, enabled: bool):
        """动态切换测试网模式"""
        self.testnet  = enabled
        self.exchange  = self._init_exchange()
        self.load_config() 
        logger.info(f" 已切换至{'测试网' if enabled else '实盘'}模式")
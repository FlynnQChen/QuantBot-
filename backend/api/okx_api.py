import os 
import ccxt 
from typing import Dict, Optional, Union
from ..utils.logger  import logger
from ..utils.data_parser  import parse_kline_data
import yaml
 
class OKXAPI:
    """OKX 合约交易API封装（支持实盘/测试网切换和双线持仓）"""
 
    def __init__(self, api_key: str = "", api_secret: str = "", passphrase: str = "", testnet: bool = False):
        """
        初始化OKX连接
        :param api_key: 用户输入的API Key 
        :param api_secret: 用户输入的API Secret
        :param passphrase: OKX专属API密码
        :param testnet: 是否使用测试网
        """
        self.api_key  = api_key
        self.api_secret  = api_secret
        self.passphrase  = passphrase 
        self.testnet  = testnet 
        self.exchange  = self._init_exchange()
        self.load_config() 
 
    def _init_exchange(self) -> ccxt.okx: 
        """初始化CCXT OKX实例"""
        config = {
            'apiKey': self.api_key, 
            'secret': self.api_secret, 
            'password': self.passphrase, 
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap'  # 统一账户合约
            }
        }
        
        if self.testnet: 
            config['urls'] = {'api': 'https://www.okx.com'}   # OKX测试网与实盘域名相同，需通过API Key区分
            
        return ccxt.okx(config) 
 
    def load_config(self):
        """从configs/exchanges.yaml 加载端点配置"""
        config_path = os.path.join(os.path.dirname(__file__),  '../../configs/exchanges.yaml') 
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) 
            if self.testnet: 
                self.base_url  = config['okx']['testnet']['api_base']
            else:
                self.base_url  = config['okx']['real']['api_base']
 
    # --------------- 账户相关 ---------------
    def get_balance(self) -> Dict[str, float]:
        """获取合约账户USDT余额"""
        try:
            balance = self.exchange.fetch_balance({'type':  'swap'})
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
        reduce_only: bool = False,
        hedge_mode: bool = True  # 支持双线持仓
    ) -> Dict:
        """
        创建合约订单（支持双线持仓模式）
        :param hedge_mode: 是否启用对冲模式（同时持有多空仓位）
        """
        try:
            # 设置杠杆和对冲模式 
            self.exchange.set_leverage(leverage,  symbol)
            self.exchange.set_position_mode(hedge_mode,  symbol)
            
            # 下单
            order = self.exchange.create_order( 
                symbol=symbol,
                type=order_type,
                side=side,
                amount=amount,
                price=price,
                params={
                    'reduceOnly': reduce_only,
                    'tdMode': 'cross'  # 全仓模式 
                }
            )
            logger.info(f" 订单创建成功: {order}")
            return order 
        except Exception as e:
            logger.error(f" 下单失败: {e}")
            raise 
 
    # --------------- 持仓管理 ---------------
    def get_positions(self, symbol: Optional[str] = None) -> Dict:
        """
        获取持仓信息（支持双线持仓查询）
        :param symbol: 若为None则返回所有持仓
        """
        try:
            positions = self.exchange.fetch_positions(['swap'],  symbol)
            # 格式化持仓数据：{symbol: {long: {...}, short: {...}}}
            formatted = {}
            for pos in positions:
                if pos['symbol'] not in formatted:
                    formatted[pos['symbol']] = {}
                formatted[pos['symbol']][pos['side']] = pos 
            return formatted 
        except Exception as e:
            logger.error(f" 获取持仓失败: {e}")
            raise
 
    # --------------- 数据获取 ---------------
    def fetch_klines(
        self,
        symbol: str,
        timeframe: str = '1h',
        limit: int = 1000
    ) -> Dict:
        """获取K线数据（与Binance格式统一）"""
        try:
            klines = self.exchange.fetch_ohlcv(symbol,  timeframe, limit=limit)
            return parse_kline_data(klines)  # 复用Binance的数据解析器 
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
from typing import Dict, Union 
from .binance_api import BinanceAPI
from .okx_api import OKXAPI
from ..utils.logger  import logger
import yaml
import os 
 
class APIConnector:
    """
    统一交易所连接器 
    功能：
    - 集中管理 Binance 和 OKX 的 API 实例 
    - 动态切换实盘/测试网模式 
    - 提供统一的接口调用
    """
 
    def __init__(self):
        self.exchanges  = {
            "binance": None,
            "okx": None
        }
        self.testnet_mode  = False
        self.load_config() 
 
    def load_config(self): 
        """加载交易所配置文件"""
        config_path = os.path.join(os.path.dirname(__file__),  '../../configs/exchanges.yaml') 
        with open(config_path, 'r') as f:
            self.exchange_configs  = yaml.safe_load(f) 
 
    def initialize_exchange(
        self,
        exchange: str,
        api_key: str = "",
        api_secret: str = "",
        passphrase: str = ""  # OKX 专用 
    ) -> Union[BinanceAPI, OKXAPI]:
        """
        初始化交易所连接 
        :param exchange: 'binance' 或 'okx'
        :param api_key: 用户输入的API Key 
        :param api_secret: 用户输入的API Secret
        :param passphrase: OKX 专用API密码
        :return: 交易所API实例
        """
        try:
            if exchange == "binance":
                self.exchanges["binance"]  = BinanceAPI(
                    api_key=api_key,
                    api_secret=api_secret,
                    testnet=self.testnet_mode 
                )
                logger.info(f"Binance  API 初始化成功（{'测试网' if self.testnet_mode  else '实盘'}模式）")
                return self.exchanges["binance"] 
 
            elif exchange == "okx":
                self.exchanges["okx"]  = OKXAPI(
                    api_key=api_key,
                    api_secret=api_secret,
                    passphrase=passphrase,
                    testnet=self.testnet_mode  
                )
                logger.info(f"OKX  API 初始化成功（{'测试网' if self.testnet_mode  else '实盘'}模式）")
                return self.exchanges["okx"] 
 
            else:
                raise ValueError(f"不支持的交易所: {exchange}")
 
        except Exception as e:
            logger.error(f" 交易所初始化失败: {e}")
            raise 
 
    def switch_testnet_mode(self, enabled: bool):
        """
        动态切换所有交易所的测试网模式
        :param enabled: 是否启用测试网 
        """
        self.testnet_mode  = enabled 
        for exchange in self.exchanges.values(): 
            if exchange is not None:
                exchange.switch_testnet(enabled) 
        logger.info(f" 全局切换到 {'测试网' if enabled else '实盘'} 模式")
 
    def get_exchange(self, exchange: str) -> Union[BinanceAPI, OKXAPI]:
        """
        获取已初始化的交易所实例 
        :param exchange: 'binance' 或 'okx'
        :raises RuntimeError: 如果交易所未初始化
        """
        if self.exchanges.get(exchange)  is None:
            raise RuntimeError(f"{exchange} 未初始化，请先调用 initialize_exchange()")
        return self.exchanges[exchange] 
 
    def get_all_balances(self) -> Dict[str, Dict]:
        """获取所有已初始化交易所的余额"""
        balances = {}
        for name, exchange in self.exchanges.items(): 
            if exchange is not None:
                try:
                    balances[name] = exchange.get_balance() 
                except Exception as e:
                    logger.error(f" 获取 {name} 余额失败: {e}")
        return balances 
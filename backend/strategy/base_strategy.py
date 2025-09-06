from abc import ABC, abstractmethod 
from typing import Dict, List, Optional
from ..api.api_connector  import APIConnector
from ..utils.logger  import logger
import yaml
import os 
 
class BaseStrategy(ABC):
    """
    策略抽象基类 
    功能：
    - 定义策略开发标准接口
    - 管理指标参数和交易所连接 
    - 提供通用的回测和实盘执行逻辑 
    """
 
    def __init__(self, strategy_name: str, connector: APIConnector):
        """
        :param strategy_name: 策略名称（对应configs/strategy_presets/下的配置文件）
        :param connector: APIConnector实例（用于访问交易所API）
        """
        self.strategy_name  = strategy_name
        self.connector  = connector
        self.indicators  = {}  # 存储指标参数（如 {'RSI': {'period': 14}}）
        self.exchanges  = []   # 策略适用的交易所（如 ['binance', 'okx']）
        self.load_config() 
 
    def load_config(self):
        """从预设文件加载策略配置"""
        config_path = os.path.join( 
            os.path.dirname(__file__), 
            f'../../configs/strategy_presets/{self.strategy_name}.yaml' 
        )
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) 
                self.indicators  = config.get('indicators',  {})
                self.exchanges  = config.get('exchanges',  [])
                logger.info(f" 策略配置加载成功: {self.strategy_name}") 
        except FileNotFoundError:
            logger.warning(f" 未找到策略配置文件: {config_path}, 使用默认参数")
        except Exception as e:
            logger.error(f" 加载策略配置失败: {e}")
            raise 
 
    def update_indicator_params(self, indicator: str, params: Dict):
        """动态更新指标参数（供前端调用）"""
        if indicator in self.indicators: 
            self.indicators[indicator].update(params) 
            logger.info(f" 指标 {indicator} 参数更新为: {params}")
        else:
            logger.warning(f" 尝试更新不存在的指标: {indicator}")
 
    @abstractmethod 
    def calculate_signals(self, symbol: str, klines: Dict) -> Optional[Dict]:
        """
        抽象方法：计算交易信号（需子类实现）
        :param symbol: 交易对（如 'BTC/USDT'）
        :param klines: K线数据（包含开盘价、最高价等）
        :return: 信号字典（如 {'action': 'buy', 'price': 50000}）或 None（无信号）
        """
        pass
 
    def execute_trade(self, signal: Dict, exchange: str = 'binance'):
        """
        通用交易执行逻辑（子类可覆盖）
        :param signal: calculate_signals() 生成的信号
        :param exchange: 交易所名称（binance/okx）
        """
        try:
            api = self.connector.get_exchange(exchange) 
            if signal['action'] == 'buy':
                api.create_order( 
                    symbol=signal['symbol'],
                    side='buy',
                    amount=signal.get('amount',  0.01),
                    leverage=signal.get('leverage',  1)
                )
            elif signal['action'] == 'sell':
                api.create_order( 
                    symbol=signal['symbol'],
                    side='sell',
                    amount=signal.get('amount',  0.01),
                    reduce_only=signal.get('reduce_only',  False)
                )
            logger.info(f" 执行交易: {signal}")
        except Exception as e:
            logger.error(f" 交易执行失败: {e}")
            raise 
 
    def run_backtest(self, symbol: str, klines: List[Dict]):
        """
        通用回测逻辑（子类可扩展）
        :param symbol: 交易对
        :param klines: 历史K线数据
        """
        for kline in klines:
            signal = self.calculate_signals(symbol,  kline)
            if signal:
                logger.debug(f" 回测信号: {signal}") 
                # 这里可添加回测统计逻辑（如累计收益计算）
 
    def get_indicator_params(self) -> Dict:
        """获取当前指标参数（供前端显示）"""
        return self.indicators 
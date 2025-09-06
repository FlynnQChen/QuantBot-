#!/usr/bin/env python3
"""
CryptoTrader 主程序入口
====================== 
 
功能:
1. 初始化交易系统 
2. 启动交易引擎
3. 管理策略生命周期
4. 处理系统信号 
5. 监控系统健康状态
"""
 
import asyncio
import signal 
import logging
from typing import Dict, Optional 
from decimal import Decimal 
import argparse 
import platform
 
# 配置日志格式 
logging.basicConfig( 
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('CryptoTrader') 
 
class CryptoTrader:
    """主交易系统类"""
    
    def __init__(self, config: Dict):
        """
        初始化交易系统
        
        参数:
            config: 系统配置字典 
        """
        self.config  = config 
        self.running  = False
        self.components  = {
            'risk_engine': None,
            'market_data': None,
            'order_executor': None,
            'strategy_runner': None
        }
        
        # 系统状态监控 
        self.system_stats  = {
            'uptime': 0.0,
            'performance': {
                'order_rate': 0.0,
                'latency': 0.0
            },
            'resources': {
                'memory': 0.0,
                'cpu': 0.0 
            }
        }
 
    async def initialize(self):
        """异步初始化系统组件"""
        logger.info("Initializing  CryptoTrader system...")
        
        # 初始化顺序很重要
        from risk_engine import RiskEngine
        from market_data import MarketDataFeed 
        from execution import OrderExecutor
        from strategies import StrategyRunner 
        
        try:
            # 1. 初始化风控引擎 
            self.components['risk_engine']  = RiskEngine(
                max_leverage=self.config['risk']['max_leverage'], 
                position_limits=self.config['risk']['position_limits'] 
            )
            
            # 2. 启动市场数据feed 
            self.components['market_data']  = MarketDataFeed(
                symbols=self.config['trading']['symbols'], 
                data_provider=self.config['data']['provider'] 
            )
            await self.components['market_data'].connect() 
            
            # 3. 初始化订单执行器
            self.components['order_executor']  = OrderExecutor(
                api_key=self.config['exchange']['api_key'], 
                api_secret=self.config['exchange']['api_secret'], 
                sandbox=self.config['exchange']['sandbox'] 
            )
            
            # 4. 加载交易策略
            self.components['strategy_runner']  = StrategyRunner(
                strategies=self.config['strategies'], 
                market_data=self.components['market_data'], 
                executor=self.components['order_executor'], 
                risk_engine=self.components['risk_engine'] 
            )
            
            logger.info("All  system components initialized successfully")
            return True 
            
        except Exception as e:
            logger.error(f"System  initialization failed: {str(e)}")
            return False 
 
    async def run(self):
        """运行主交易循环"""
        if not await self.initialize(): 
            logger.error("Aborting  due to initialization failure")
            return 
        
        self.running  = True 
        logger.info("Starting  CryptoTrader main loop")
        
        # 注册信号处理器 
        loop = asyncio.get_running_loop() 
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig,  self.graceful_shutdown) 
        
        # 启动组件 
        tasks = [
            asyncio.create_task(self.components['market_data'].run()), 
            asyncio.create_task(self.components['strategy_runner'].run()), 
            asyncio.create_task(self.monitor_system())  
        ]
        
        try:
            await asyncio.gather(*tasks) 
        except asyncio.CancelledError:
            logger.info("Main  loop tasks cancelled")
        finally:
            await self.shutdown() 
 
    async def monitor_system(self):
        """监控系统健康状态"""
        logger.info("Starting  system monitor")
        while self.running: 
            await asyncio.sleep(5)   # 每5秒检查一次 
            
            # 更新系统统计信息
            self.system_stats['uptime']  += 5
            self.update_performance_metrics() 
            self.check_system_health() 
            
            # 简单日志输出
            if self.system_stats['uptime']  % 60 == 0:  # 每分钟记录一次 
                logger.info(f"System  uptime: {self.system_stats['uptime']}s") 
    
    def update_performance_metrics(self):
        """更新性能指标"""
        # 这里应该有实际的性能监控实现 
        # 现在使用模拟数据 
        self.system_stats['performance']['order_rate']  = 10.5  # orders/sec 
        self.system_stats['performance']['latency']  = 0.15     # seconds 
    
    def check_system_health(self):
        """检查系统健康状况"""
        # 检查组件状态 
        for name, component in self.components.items(): 
            if not component or not component.is_healthy(): 
                logger.warning(f"Component  {name} is not healthy")
                
        # 检查资源使用情况 
        self.system_stats['resources']['memory']  = 45.2  # %
        self.system_stats['resources']['cpu']  = 32.7     # %
        
        if self.system_stats['resources']['memory']  > 90:
            logger.error("Memory  usage critically high!")
 
    def graceful_shutdown(self):
        """优雅关闭系统"""
        logger.info("Initiating  graceful shutdown...")
        self.running  = False 
        
        # 取消所有运行中的任务
        for task in asyncio.all_tasks(): 
            if task is not asyncio.current_task(): 
                task.cancel() 
 
    async def shutdown(self):
        """清理系统资源"""
        logger.info("Shutting  down system components...")
        
        # 按逆序关闭组件
        shutdown_order = [
            'strategy_runner',
            'order_executor',
            'market_data',
            'risk_engine'
        ]
        
        for component in shutdown_order:
            if self.components[component]: 
                try:
                    await self.components[component].close() 
                    logger.info(f"{component}  shutdown complete")
                except Exception as e:
                    logger.error(f"Error  shutting down {component}: {str(e)}")
        
        logger.info("CryptoTrader  shutdown complete")
 
def load_config(config_path: Optional[str] = None) -> Dict:
    """
    加载系统配置
    
    参数:
        config_path: 可选的自定义配置文件路径
    
    返回:
        配置字典 
    """
    import json 
    import os 
    
    # 默认配置 
    default_config = {
        "risk": {
            "max_leverage": 10,
            "position_limits": {
                "BTC": Decimal('50'),
                "ETH": Decimal('100'),
                "*": Decimal('1000000')
            }
        },
        "trading": {
            "symbols": ["BTC/USDT", "ETH/USDT"],
            "base_currency": "USDT"
        },
        "data": {
            "provider": "binance",
            "update_interval": 1.0
        },
        "exchange": {
            "api_key": os.getenv("EXCHANGE_API_KEY",  ""),
            "api_secret": os.getenv("EXCHANGE_API_SECRET",  ""),
            "sandbox": True 
        },
        "strategies": [
            {
                "name": "mean_reversion",
                "params": {
                    "lookback_period": 14,
                    "threshold": 1.5
                },
                "enabled": True 
            }
        ]
    }
    
    # 从文件加载自定义配置 
    if config_path and os.path.exists(config_path): 
        try:
            with open(config_path) as f:
                user_config = json.load(f) 
                
                # 合并配置 (浅合并)
                for key in user_config:
                    if key in default_config and isinstance(default_config[key], dict):
                        default_config[key].update(user_config[key])
                    else:
                        default_config[key] = user_config[key]
                        
                logger.info(f"Loaded  configuration from {config_path}")
        except Exception as e:
            logger.warning(f"Failed  to load config file: {str(e)}")
    
    return default_config
 
def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='CryptoTrader Trading System')
    
    parser.add_argument( 
        '--config',
        type=str,
        default=None,
        help='Path to custom configuration file'
    )
    
    parser.add_argument( 
        '--sandbox',
        action='store_true',
        help='Run in sandbox/test mode'
    )
    
    parser.add_argument( 
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set the logging level'
    )
    
    return parser.parse_args() 
 
async def main():
    """主程序入口"""
    args = parse_args()
    
    # 设置日志级别
    logging.getLogger().setLevel(args.log_level) 
    
    # 加载配置 
    config = load_config(args.config) 
    
    # 应用命令行参数覆盖 
    if args.sandbox: 
        config['exchange']['sandbox'] = True 
    
    # 打印系统信息
    logger.info(f"Starting  CryptoTrader on {platform.system()}  {platform.release()}") 
    logger.info(f"Python  version: {platform.python_version()}") 
    logger.info(f"Initializing  with {len(config['trading']['symbols'])} symbols")
    
    # 创建并运行交易系统
    trader = CryptoTrader(config)
    try:
        await trader.run() 
    except Exception as e:
        logger.critical(f"Fatal  error in main loop: {str(e)}")
        await trader.shutdown() 
        raise 
 
if __name__ == "__main__":
    try:
        asyncio.run(main()) 
    except KeyboardInterrupt:
        logger.info("Shutdown  requested by user")
    except Exception as e:
        logger.error(f"Unexpected  error: {str(e)}")
        raise 
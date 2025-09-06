import json
import os 
from typing import Dict, List, Optional, Union
from pathlib import Path
from pydantic import BaseModel, validator, root_validator
from enum import Enum 
from ..utils.logger  import logger 
import yaml 
 
class ExchangeConfig(BaseModel):
    """交易所账户配置模型"""
    name: str  # binance/okx
    api_key: str
    api_secret: str 
    password: Optional[str] = None  # 某些交易所需要 
    sandbox: bool = False  # 是否使用测试网 
    proxies: Optional[Dict] = None  # {'http': 'http://proxy:port', 'https': 'https://proxy:port'}
 
class RiskConfig(BaseModel):
    """风险控制配置模型"""
    max_risk_per_trade: float = 0.02  # 单笔交易最大风险（账户比例）
    daily_stop_loss: float = -0.1  # 日止损线 
    leverage_strategy: str = "conservative"  # aggressive/moderate/conservative
    blacklist: List[str] = []  # 交易对黑名单
 
class StrategyConfig(BaseModel):
    """策略配置模型"""
    name: str 
    enabled: bool = True
    params: Dict[str, Union[float, int, str]]  # 策略特定参数
    symbols: List[str]  # 适用的交易对 
 
class NotificationConfig(BaseModel):
    """通知配置模型"""
    email: Optional[str] = None 
    slack_webhook: Optional[str] = None 
    telegram_chat_id: Optional[str] = None
    alert_levels: List[str] = ["critical"]  # critical/warning/info
 
class UserConfig(BaseModel):
    """
    用户主配置模型 
    包含所有个性化设置
    """
    exchanges: List[ExchangeConfig]
    risk: RiskConfig 
    strategies: List[StrategyConfig]
    notifications: NotificationConfig 
    version: str = "1.0"
 
    class Config:
        json_encoders = {
            Path: lambda p: str(p),
        }
 
    @validator('strategies')
    def validate_strategy_symbols(cls, v, values):
        """验证策略交易对在黑名单中是否被禁用"""
        risk_config = values.get('risk',  RiskConfig())
        blacklist = set(risk_config.blacklist) 
        
        for strategy in v:
            invalid_symbols = [s for s in strategy.symbols  if s in blacklist]
            if invalid_symbols:
                raise ValueError(f"策略 {strategy.name}  包含黑名单交易对: {invalid_symbols}")
        return v 
 
class ConfigManager:
    """
    配置管理器 
    负责配置的加载、保存和验证 
    """
    DEFAULT_PATH = "configs/user_config.json" 
 
    def __init__(self, config_path: str = None):
        self.config_path  = config_path or self.DEFAULT_PATH
        self.config:  Optional[UserConfig] = None 
 
    def load(self) -> UserConfig:
        """从文件加载配置（支持JSON/YAML）"""
        path = Path(self.config_path) 
        if not path.exists(): 
            raise FileNotFoundError(f"配置文件不存在: {path}")
 
        try:
            raw = path.read_text(encoding='utf-8') 
            if path.suffix.lower()  in ('.yaml', '.yml'):
                data = yaml.safe_load(raw) 
            else:
                data = json.loads(raw) 
            
            self.config  = UserConfig(**data)
            logger.info(f" 配置加载成功: {path}")
            return self.config 
        except Exception as e:
            logger.error(f" 配置加载失败: {e}")
            raise
 
    def save(self, config: UserConfig = None, path: str = None):
        """保存配置到文件"""
        config = config or self.config 
        if config is None:
            raise ValueError("没有可保存的配置")
 
        save_path = Path(path or self.config_path) 
        save_path.parent.mkdir(exist_ok=True) 
 
        try:
            data = config.json(indent=2,  ensure_ascii=False)
            save_path.write_text(data,  encoding='utf-8')
            logger.info(f" 配置保存成功: {save_path}")
        except Exception as e:
            logger.error(f" 配置保存失败: {e}")
            raise
 
    def update_strategy_param(
        self, 
        strategy_name: str, 
        param_name: str, 
        value: Union[float, int, str],
        save: bool = False
    ) -> bool:
        """动态更新策略参数"""
        if self.config  is None:
            raise ValueError("配置未加载")
 
        target = None 
        for strategy in self.config.strategies: 
            if strategy.name  == strategy_name:
                target = strategy
                break
 
        if target is None:
            logger.error(f" 策略不存在: {strategy_name}")
            return False 
 
        if param_name not in target.params: 
            logger.error(f" 参数不存在: {strategy_name}.{param_name}")
            return False 
 
        # 类型检查 
        old_value = target.params[param_name] 
        if type(old_value) != type(value):
            logger.error(f" 参数类型不匹配: {type(old_value)} != {type(value)}")
            return False 
 
        target.params[param_name]  = value 
        logger.info(f" 参数更新: {strategy_name}.{param_name} = {value}")
 
        if save:
            self.save() 
        return True 
 
    def get_exchange_config(self, exchange_name: str) -> Optional[ExchangeConfig]:
        """获取指定交易所配置"""
        if self.config  is None:
            return None 
 
        for exchange in self.config.exchanges: 
            if exchange.name.lower()  == exchange_name.lower(): 
                return exchange 
        return None 
 
# ------------------- 示例配置生成 -------------------
def generate_example_config(output_path: str = "configs/example_user_config.yaml"): 
    """生成示例配置文件"""
    example = UserConfig(
        exchanges=[
            ExchangeConfig(
                name="binance",
                api_key="your_api_key_here",
                api_secret="your_api_secret_here"
            )
        ],
        risk=RiskConfig(
            max_risk_per_trade=0.02,
            daily_stop_loss=-0.1,
            blacklist=["SHIB/USDT", "DOGE/USDT"]
        ),
        strategies=[
            StrategyConfig(
                name="RSI_MACD",
                params={"rsi_period": 14, "macd_fast": 12},
                symbols=["BTC/USDT", "ETH/USDT"]
            )
        ],
        notifications=NotificationConfig(
            email="your_email@example.com", 
            alert_levels=["critical", "warning"]
        )
    )
 
    manager = ConfigManager(output_path)
    manager.save(example) 
    print(f"示例配置已生成: {output_path}")
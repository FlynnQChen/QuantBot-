"""
backend/app.py  
QuantBot 交易系统核心API服务 
 
功能模块：
1. 系统状态管理 
2. 策略生命周期控制
3. 实时数据推送
4. 风险控制接口 
5. 账户操作接口
"""
 
import asyncio
from concurrent.futures  import ThreadPoolExecutor 
from fastapi import FastAPI, WebSocket, HTTPException, Depends, status
from fastapi.middleware.cors  import CORSMiddleware
from fastapi.security  import APIKeyHeader 
from fastapi.staticfiles  import StaticFiles 
from pydantic import BaseModel, Field 
from typing import List, Optional, Dict
import uvicorn 
import logging 
from datetime import datetime
 
# 项目内部模块 
from utils.logger  import logger
from utils.time_utils  import time_utils
from models.user_config  import ConfigManager
from api.api_connector  import APIManager
from strategy.base_strategy  import StrategyManager 
from risk_management.position_control  import RiskManager
from notifier.alert_manager  import AlertManager
 
# --- 初始化FastAPI应用 ---
app = FastAPI(
    title="QuantBot Trading System API",
    description="量化交易系统RESTful接口文档",
    version="2.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)
 
# 跨域设置
app.add_middleware( 
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# --- 安全认证 --- 
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)
 
async def authenticate(api_key: str = Depends(api_key_header)):
    """API密钥验证"""
    if not api_key or api_key != ConfigManager().get_api_key():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return api_key
 
# --- 数据模型 --- 
class SystemStatus(BaseModel):
    status: str = Field(..., example="running")
    exchanges: List[str] = Field(..., example=["binance", "okx"])
    running_strategies: int = Field(..., example=3)
    last_heartbeat: datetime
 
class StrategyConfig(BaseModel):
    name: str = Field(..., example="RSI_MACD")
    params: Dict = Field(..., example={"rsi_period": 14, "macd_fast": 12})
    symbols: List[str] = Field(..., example=["BTC/USDT", "ETH/USDT"])
 
class OrderRequest(BaseModel):
    symbol: str
    side: str  # buy/sell 
    type: str  # market/limit
    amount: float 
    price: Optional[float] = None 
 
# --- 全局服务实例 ---
config = ConfigManager()
api = APIManager()
strategies = StrategyManager()
risk = RiskManager()
alerts = AlertManager()
 
# 线程池执行同步操作 
executor = ThreadPoolExecutor(max_workers=16)
 
# --- 生命周期管理 ---
@app.on_event("startup") 
async def initialize_system():
    """系统启动初始化"""
    try:
        await api.connect_all(config.get_exchanges()) 
        strategies.load_presets(config.get_strategy_presets()) 
        risk.start() 
        logger.success(" 系统启动完成")
    except Exception as e:
        logger.critical(f" 启动失败: {e}")
        raise RuntimeError("系统初始化失败")
 
@app.on_event("shutdown")  
async def shutdown_cleanup():
    """系统关闭清理"""
    await api.disconnect_all() 
    strategies.stop_all() 
    risk.stop() 
    logger.info(" 系统已安全关闭")
 
# --- 核心API接口 ---
@app.get("/api/status",  response_model=SystemStatus)
async def get_status():
    """获取系统运行状态"""
    return {
        "status": "running",
        "exchanges": api.connected_exchanges, 
        "running_strategies": strategies.count_active(), 
        "last_heartbeat": time_utils.now() 
    }
 
@app.post("/api/strategy/start",  status_code=201)
async def start_strategy(
    config: StrategyConfig, 
    _: str = Depends(authenticate)
):
    """
    启动新策略实例 
    - 策略名称需在presets中预定义
    - 自动绑定到指定交易对
    """
    def _start():
        if not strategies.validate(config.name): 
            raise HTTPException(400, "无效策略名称")
        strategies.start( 
            config.name, 
            config.params, 
            config.symbols  
        )
    
    try:
        await asyncio.get_event_loop().run_in_executor(executor,  _start)
        return {"message": f"策略 {config.name}  已启动"}
    except Exception as e:
        logger.error(f" 策略启动失败: {e}")
        raise HTTPException(500, str(e))
 
@app.delete("/api/strategy/{strategy_id}") 
async def stop_strategy(
    strategy_id: str, 
    _: str = Depends(authenticate)
):
    """停止运行中的策略"""
    if not strategies.stop(strategy_id): 
        raise HTTPException(404, "策略不存在")
    return {"message": "策略已停止"}
 
@app.post("/api/order",  status_code=201)
async def create_order(
    order: OrderRequest, 
    _: str = Depends(authenticate)
):
    """手动下单接口"""
    try:
        result = await api.place_order( 
            order.symbol, 
            order.side, 
            order.type, 
            order.amount, 
            order.price  
        )
        alerts.notify_order(result) 
        return result 
    except Exception as e:
        logger.error(f" 下单失败: {e}")
        raise HTTPException(400, str(e))
 
# --- WebSocket实时数据 ---
active_connections = set()
 
@app.websocket("/ws/market") 
async def market_data_feed(websocket: WebSocket):
    """实时市场数据推送"""
    await websocket.accept() 
    active_connections.add(websocket) 
    try:
        while True:
            data = await api.get_realtime_updates() 
            await websocket.send_json(data) 
            await asyncio.sleep(0.5)   # 500ms更新间隔 
    except Exception as e:
        logger.warning(f"WebSocket 断开: {e}")
    finally:
        active_connections.remove(websocket) 
 
# --- 静态文件服务 ---
app.mount("/",  StaticFiles(directory="../frontend/dist", html=True), name="ui")
 
# --- 主入口 ---
if __name__ == "__main__":
    uvicorn.run( 
        app="app:app",
        host="0.0.0.0", 
        port=8000,
        reload=False,
        log_config=None,  # 使用自定义logger 
        access_log=False,
        timeout_keep_alive=60 
    )
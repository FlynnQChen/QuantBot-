"""
backend/utils/logger.py 
统一日志管理模块 
 
功能：
1. 多级别日志记录（DEBUG/INFO/WARNING/ERROR/CRITICAL）
2. 控制台和文件双输出 
3. 支持结构化JSON日志
4. 自动日志轮转（按天）
5. 异步日志记录（可选）
6. 调用栈信息自动捕获
7. 支持多种日志格式（控制台/JSON/GELF）
"""
 
import logging
import sys 
import os
from logging.handlers  import TimedRotatingFileHandler, QueueHandler, QueueListener 
from pathlib import Path 
from typing import Optional, Dict, Any, Union
import json 
from datetime import datetime
import inspect 
import queue
import threading 
import socket
from enum import Enum 
 
class LogFormat(Enum):
    """日志格式枚举"""
    CONSOLE = 'console'  # 控制台友好格式
    JSON = 'json'        # 结构化JSON格式
    GELF = 'gelf'        # Graylog日志格式
 
class LogLevel(Enum):
    """日志级别枚举（兼容logging模块）"""
    DEBUG = logging.DEBUG     # 调试信息
    INFO = logging.INFO       # 常规运行信息
    WARNING = logging.WARNING # 警告信息
    ERROR = logging.ERROR     # 错误信息
    CRITICAL = logging.CRITICAL # 严重错误 
 
class EnhancedJSONEncoder(json.JSONEncoder):
    """增强型JSON编码器（处理特殊类型）"""
    def default(self, obj):
        # 处理datetime、Path等特殊类型的序列化
        if isinstance(obj, datetime):
            return obj.isoformat()  + "Z"
        elif isinstance(obj, Path):
            return str(obj)
        elif isinstance(obj, Enum):
            return obj.value  
        return super().default(obj)
 
class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器基类"""
    def __init__(self, fmt_dict: Dict[LogLevel, str]):
        """
        参数:
            fmt_dict: 不同日志级别对应的格式模板
        """
        self.fmt_dict  = fmt_dict 
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录"""
        log_fmt = self.fmt_dict.get(LogLevel(record.levelno)) 
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record) 
 
class JSONFormatter(StructuredFormatter):
    """JSON格式日志格式化器"""
    def __init__(self):
        super().__init__({
            level: json.dumps({ 
                "timestamp": datetime.utcnow().isoformat(), 
                "level": level.name, 
                "message": record.getMessage(), 
                "module": record.module, 
                "function": record.funcName, 
                "line": record.lineno, 
                "thread": record.threadName, 
                **getattr(record, 'extra', {})
            }, cls=EnhancedJSONEncoder)
            for level in LogLevel
        })
 
class ConsoleFormatter(StructuredFormatter):
    """控制台日志格式化器"""
    def __init__(self):
        super().__init__({
            LogLevel.DEBUG: "[%(asctime)s] DEBUG %(module)s:%(lineno)d - %(message)s",
            LogLevel.INFO: "[%(asctime)s] INFO - %(message)s",
            LogLevel.WARNING: "[%(asctime)s] WARNING - %(message)s",
            LogLevel.ERROR: "[%(asctime)s] ERROR %(module)s:%(lineno)d - %(message)s",
            LogLevel.CRITICAL: "[%(asctime)s] CRITICAL %(module)s:%(lineno)d - %(message)s"
        })
 
def get_caller_info(skip_frames: int = 2) -> Dict[str, Any]:
    """
    获取调用者信息（用于增强日志上下文）
    
    参数:
        skip_frames: 跳过多少层调用栈 
        
    返回:
        包含调用者信息的字典
    """
    frame = inspect.currentframe() 
    for _ in range(skip_frames):
        if frame.f_back:
            frame = frame.f_back
    return {
        "caller_file": Path(frame.f_code.co_filename).name, 
        "caller_line": frame.f_lineno,
    }
 
class AsyncLogHandler:
    """异步日志处理器（使用队列避免阻塞主线程）"""
    def __init__(self, base_handler: logging.Handler):
        """
        参数:
            base_handler: 实际执行日志记录的处理器 
        """
        self.log_queue  = queue.Queue(-1)  # 无限大小队列
        self.listener  = QueueListener(
            self.log_queue,  
            base_handler,
            respect_handler_level=True 
        )
        self.handler  = QueueHandler(self.log_queue) 
        
    def start(self):
        """启动异步日志线程"""
        self.listener.start() 
        
    def stop(self):
        """停止异步日志线程"""
        self.listener.stop() 
 
class Logger:
    """
    主日志记录器类 
    
    特性:
    - 单例模式确保全局唯一 
    - 支持同步/异步日志记录 
    - 多处理器支持（控制台+文件）
    - 自动日志轮转
    """
    
    _instances = {}  # 单例缓存
 
    def __new__(cls, name: str = "app", log_file: Optional[str] = None, 
                async_log: bool = False, log_level: LogLevel = LogLevel.INFO):
        """单例模式实现"""
        if name not in cls._instances:
            cls._instances[name] = super().__new__(cls)
        return cls._instances[name]
 
    def __init__(self, name: str = "app", log_file: Optional[str] = None,
                 async_log: bool = False, log_level: LogLevel = LogLevel.INFO):
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self.async_log  = async_log
        self.logger  = logging.getLogger(name) 
        self.logger.setLevel(log_level.value) 
        
        # 初始化处理器
        self._setup_handlers(log_file, log_level)
        
        # 如果是异步模式，启动监听线程
        if async_log:
            for handler in self.logger.handlers: 
                if isinstance(handler, AsyncLogHandler):
                    handler.start() 
 
    def _setup_handlers(self, log_file: Optional[str], log_level: LogLevel):
        """配置日志处理器"""
        
        # 控制台处理器（始终启用）
        console_handler = logging.StreamHandler(sys.stdout) 
        console_handler.setLevel(log_level.value) 
        console_handler.setFormatter(ConsoleFormatter()) 
        
        if self.async_log: 
            console_handler = AsyncLogHandler(console_handler)
        
        self.logger.addHandler(console_handler) 
        
        # 文件处理器（如果指定了日志文件）
        if log_file:
            Path(log_file).parent.mkdir(parents=True,  exist_ok=True)
            file_handler = TimedRotatingFileHandler(
                log_file,
                when='midnight',  # 按天轮转
                backupCount=7,    # 保留7天 
                encoding='utf-8'
            ) 
            file_handler.setLevel(logging.DEBUG)   # 文件记录所有级别
            file_handler.setFormatter(JSONFormatter()) 
            
            if self.async_log: 
                file_handler = AsyncLogHandler(file_handler)
            
            self.logger.addHandler(file_handler) 
 
    def log(self, level: LogLevel, message: str, **kwargs):
        """
        基础日志方法 
        
        参数:
            level: 日志级别 
            message: 日志消息
            kwargs: 额外上下文信息 
        """
        extra = get_caller_info()
        extra.update(kwargs) 
        self.logger.log(level.value,  message, extra=extra)
 
    # 快捷方法
    def debug(self, message: str, **kwargs):
        """记录DEBUG级别日志"""
        self.log(LogLevel.DEBUG,  message, **kwargs)
 
    def info(self, message: str, **kwargs):
        """记录INFO级别日志"""
        self.log(LogLevel.INFO,  message, **kwargs)
 
    def warning(self, message: str, **kwargs):
        """记录WARNING级别日志"""
        self.log(LogLevel.WARNING,  message, **kwargs)
 
    def error(self, message: str, **kwargs):
        """记录ERROR级别日志"""
        self.log(LogLevel.ERROR,  message, **kwargs)
 
    def critical(self, message: str, **kwargs):
        """记录CRITICAL级别日志"""
        self.log(LogLevel.CRITICAL,  message, **kwargs)
 
    def exception(self, message: str, **kwargs):
        """记录异常日志（自动包含堆栈）"""
        extra = get_caller_info()
        extra.update(kwargs) 
        self.logger.exception(message,  extra=extra)
 
# 全局默认日志记录器 
logger = Logger(
    name="trading_system",
    log_file="logs/trading.log", 
    async_log=True,
    log_level=LogLevel.INFO 
)
 
# 兼容传统用法的快捷方法
debug = logger.debug  
info = logger.info 
warning = logger.warning 
error = logger.error  
critical = logger.critical  
exception = logger.exception 
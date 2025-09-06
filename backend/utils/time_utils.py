"""
backend/utils/time_utils.py  
高频交易时间处理工具集
 
功能：
1. 多时区自动转换
2. 时间戳精度处理（纳秒级）
3. 交易时段检测 
4. 性能优化的时间间隔计算
"""
 
import time 
from datetime import datetime, timedelta 
import pytz
from typing import Union, Optional, Tuple 
import pandas as pd
import numpy as np 
from functools import lru_cache 
 
# 金融市场的常用时区 
MARKET_TIMEZONES = {
    'NY': 'America/New_York',
    'LONDON': 'Europe/London',
    'TOKYO': 'Asia/Tokyo',
    'HK': 'Asia/Hong_Kong',
    'SH': 'Asia/Shanghai',
    'UTC': 'UTC'
}
 
class TimeUtils:
    """核心时间处理工具类"""
    
    def __init__(self, default_timezone: str = 'Asia/Shanghai'):
        """
        参数:
            default_timezone: 默认时区（pytz格式或MARKET_TIMEZONES中的key）
        """
        self.default_tz  = self._parse_timezone(default_timezone)
    
    @staticmethod 
    @lru_cache(maxsize=32)
    def _parse_timezone(tz: str) -> pytz.BaseTzInfo:
        """缓存时区对象解析结果"""
        return pytz.timezone(MARKET_TIMEZONES.get(tz,  tz))
 
    def now(self, tz: Optional[str] = None) -> datetime:
        """
        获取当前时间（带时区）
        
        参数:
            tz: 时区标识（如'NY'或'America/New_York'）
        
        返回:
            datetime: 带时区的当前时间
        """
        tz_obj = self._parse_timezone(tz) if tz else self.default_tz 
        return datetime.now(tz_obj) 
    
    def to_timestamp(
        self, 
        dt: Union[datetime, str, int, float], 
        unit: str = 'ms'
    ) -> int:
        """
        统一时间转换为时间戳
        
        参数:
            dt: 可接受类型:
                - datetime对象（带或不带时区）
                - 时间字符串（如'2023-01-01 00:00:00'）
                - 时间戳（支持s/ms/ns）
            unit: 输出单位 ('s'/'ms'/'ns')
        
        返回:
            int: 指定单位的时间戳 
        """
        if isinstance(dt, str):
            dt = pd.to_datetime(dt).to_pydatetime() 
        elif isinstance(dt, (int, float)):
            return self._convert_timestamp_unit(dt, 's', unit)
        
        if dt.tzinfo  is None:
            dt = self.default_tz.localize(dt) 
        
        ts = dt.timestamp() 
        return self._convert_timestamp_unit(ts, 's', unit)
    
    @staticmethod 
    def _convert_timestamp_unit(
        ts: Union[int, float], 
        from_unit: str, 
        to_unit: str 
    ) -> int:
        """时间戳单位转换"""
        units = {'s': 1, 'ms': 1e3, 'ns': 1e9}
        return int(ts * units[to_unit] / units[from_unit])
    
    def from_timestamp(
        self, 
        timestamp: Union[int, float], 
        unit: str = 'ms',
        tz: Optional[str] = None
    ) -> datetime:
        """
        时间戳转datetime对象
        
        参数:
            timestamp: 时间戳数值 
            unit: 输入单位 ('s'/'ms'/'ns')
            tz: 目标时区 
            
        返回:
            datetime: 带时区的datetime对象
        """
        ts_seconds = self._convert_timestamp_unit(timestamp, unit, 's')
        dt = datetime.fromtimestamp(ts_seconds) 
        
        tz_obj = self._parse_timezone(tz) if tz else self.default_tz  
        return tz_obj.localize(dt) 
    
    def is_market_open(
        self, 
        symbol: str, 
        dt: Optional[datetime] = None 
    ) -> bool:
        """
        检测指定时间是否在交易时段内
        
        参数:
            symbol: 交易对符号（如'BTC/USDT'）
            dt: 检测时间，默认当前时间
            
        返回:
            bool: 是否在交易时段
        """
        dt = dt or self.now() 
        # TODO: 实现各交易所交易时间规则 
        return True
    
    def sleep_until(
        self, 
        target_time: Union[datetime, str], 
        check_interval: float = 0.001 
    ):
        """
        高精度休眠直到目标时间
        
        参数:
            target_time: 目标时间（datetime或可解析字符串）
            check_interval: 检查间隔（秒）
        """
        if isinstance(target_time, str):
            target_time = pd.to_datetime(target_time).to_pydatetime() 
        
        while True:
            remaining = (target_time - self.now()).total_seconds() 
            if remaining <= 0:
                break
            time.sleep(min(check_interval,  remaining))
    
    def generate_time_range(
        self,
        start: Union[datetime, str],
        end: Union[datetime, str],
        interval: Union[int, timedelta, str],
        unit: str = 'ms'
    ) -> np.ndarray: 
        """
        生成时间序列（优化版）
        
        参数:
            start: 开始时间
            end: 结束时间 
            interval: 间隔（支持int/timedelta/字符串如'1h'）
            unit: 输出时间戳单位
            
        返回:
            np.ndarray:  时间戳数组 
        """
        if isinstance(interval, str):
            interval = pd.to_timedelta(interval) 
        elif isinstance(interval, int):
            interval = timedelta(milliseconds=interval)
        
        start_dt = pd.to_datetime(start).to_pydatetime() 
        end_dt = pd.to_datetime(end).to_pydatetime() 
        
        timestamps = []
        current = start_dt
        while current <= end_dt:
            timestamps.append(self.to_timestamp(current,  unit))
            current += interval 
        
        return np.array(timestamps,  dtype=np.int64) 
 
# 全局默认实例（使用上海时区）
time_utils = TimeUtils('Asia/Shanghai')
 
# 快捷函数 
def get_timestamp(unit='ms') -> int:
    """获取当前时间戳（默认毫秒）"""
    return time_utils.to_timestamp(time_utils.now(),  unit)
 
def format_time(
    dt: Union[datetime, int, float], 
    fmt: str = '%Y-%m-%d %H:%M:%S',
    tz: Optional[str] = None
) -> str:
    """
    时间格式化输出 
    
    参数:
        dt: 输入时间 
        fmt: 格式字符串 
        tz: 目标时区
        
    返回:
        str: 格式化后的时间字符串
    """
    if isinstance(dt, (int, float)):
        dt = time_utils.from_timestamp(dt,  'ms', tz)
    return dt.strftime(fmt) 
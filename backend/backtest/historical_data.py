import os 
import pandas as pd
import numpy as np 
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from ..api.api_connector  import APIConnector 
from ..utils.logger  import logger 
from ..utils.data_processor  import resample_klines, fill_missing_data 
 
class HistoricalDataManager:
    """
    历史数据管理器 
    功能：
    - 多交易所历史数据统一采集与缓存 
    - 自动处理数据缺失和异常值 
    - 支持TICK/分钟/小时/日线数据
    """
 
    def __init__(self, connector: APIConnector, data_dir: str = "data/historical"):
        self.connector  = connector
        self.data_dir  = data_dir
        os.makedirs(data_dir,  exist_ok=True)
        self.cache  = {}  # 内存缓存 {exchange_symbol_tf: pd.DataFrame}
 
    def fetch_historical_data(
        self,
        symbol: str,
        exchange: str = "binance",
        timeframe: str = "1h",
        start_date: str = "2020-01-01",
        end_date: str = None,
        force_refresh: bool = False
    ) -> pd.DataFrame:
        """
        获取历史数据（优先使用本地缓存）
        :param timeframe: 时间框架（1m/5m/1h/1d）
        :param start_date: 起始日期（YYYY-MM-DD）
        :param end_date: 结束日期（默认当前时间）
        :param force_refresh: 是否强制重新下载 
        :return: DataFrame with columns [timestamp, open, high, low, close, volume]
        """
        # 生成唯一缓存键 
        cache_key = f"{exchange}_{symbol}_{timeframe}"
        end_date = end_date or datetime.now().strftime("%Y-%m-%d") 
 
        # 检查内存缓存
        if not force_refresh and cache_key in self.cache: 
            df = self.cache[cache_key] 
            mask = (df.index  >= pd.to_datetime(start_date))  & (df.index  <= pd.to_datetime(end_date)) 
            return df[mask].copy()
 
        # 检查本地文件缓存 
        file_path = os.path.join(self.data_dir,  f"{cache_key}.parquet")
        if not force_refresh and os.path.exists(file_path): 
            df = pd.read_parquet(file_path) 
            self.cache[cache_key]  = df
            mask = (df.index  >= pd.to_datetime(start_date))  & (df.index  <= pd.to_datetime(end_date)) 
            return df[mask].copy()
 
        # 从交易所API获取数据
        logger.info(f" 开始下载数据: {exchange} {symbol} {timeframe} [{start_date} to {end_date}]")
        df = self._fetch_from_exchange(symbol, exchange, timeframe, start_date, end_date)
        
        # 数据预处理 
        df = self._preprocess_data(df, timeframe)
        
        # 更新缓存 
        df.to_parquet(file_path) 
        self.cache[cache_key]  = df
        return df 
 
    def _fetch_from_exchange(
        self,
        symbol: str,
        exchange: str,
        timeframe: str,
        start_date: str,
        end_date: str 
    ) -> pd.DataFrame:
        """从交易所API获取原始数据（自动处理分页）"""
        api = self.connector.get_exchange(exchange) 
        delta = self._get_timedelta(timeframe)
        current = pd.to_datetime(start_date) 
        end = pd.to_datetime(end_date) 
        all_klines = []
 
        while current < end:
            try:
                klines = api.fetch_ohlcv( 
                    symbol=symbol,
                    timeframe=timeframe,
                    since=int(current.timestamp()  * 1000),
                    limit=1000  # 交易所单次请求最大值 
                )
                if not klines:
                    break
                
                df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'],  unit='ms')
                all_klines.append(df) 
                
                # 更新查询时间点 
                current = df['timestamp'].iloc[-1] + delta
                
            except Exception as e:
                logger.error(f" 获取数据失败: {current} | {e}")
                break
 
        if not all_klines:
            raise ValueError(f"未获取到数据: {symbol} {timeframe}")
        return pd.concat(all_klines).set_index('timestamp') 
 
    def _preprocess_data(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """数据清洗和重采样"""
        # 处理缺失值 
        df = fill_missing_data(df, timeframe)
        
        # 去除异常值（价格变动超过3倍标准差）
        returns = df['close'].pct_change()
        threshold = 3 * returns.std() 
        df = df[(returns.abs()  < threshold) | returns.isna()] 
        
        # 统一时区
        df.index  = df.index.tz_localize(None) 
        return df 
 
    def _get_timedelta(self, timeframe: str) -> timedelta:
        """转换时间框架为timedelta"""
        if timeframe.endswith('m'): 
            return timedelta(minutes=int(timeframe[:-1]))
        elif timeframe.endswith('h'): 
            return timedelta(hours=int(timeframe[:-1]))
        elif timeframe.endswith('d'): 
            return timedelta(days=int(timeframe[:-1]))
        else:
            raise ValueError(f"不支持的时间框架: {timeframe}")
 
    def get_multiple_symbols(
        self,
        symbols: List[str],
        exchange: str = "binance",
        timeframe: str = "1h",
        start_date: str = "2020-01-01",
        end_date: str = None 
    ) -> Dict[str, pd.DataFrame]:
        """批量获取多币种数据"""
        return {
            sym: self.fetch_historical_data( 
                symbol=sym,
                exchange=exchange,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )
            for sym in symbols 
        }
 
    def clean_cache(self, max_days: int = 30):
        """清理过期缓存（保留最近N天的数据）"""
        cutoff = datetime.now()  - timedelta(days=max_days)
        for file in os.listdir(self.data_dir): 
            file_path = os.path.join(self.data_dir,  file)
            if os.path.getmtime(file_path)  < cutoff.timestamp(): 
                os.remove(file_path) 
                logger.info(f" 清理过期缓存: {file}")
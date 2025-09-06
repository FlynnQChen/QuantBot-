import numpy as np
import pandas as pd 
from typing import Dict, List, Optional, Union
from logging import getLogger
 
logger = getLogger(__name__)
 
def resample_klines(df: pd.DataFrame, target_tf: str) -> pd.DataFrame:
    """
    K线数据重采样（支持任意时间框架转换）
    :param df: 输入DataFrame需包含 [open, high, low, close, volume] 列 
    :param target_tf: 目标时间框架（1m/5m/1h/4h/1d等）
    :return: 重采样后的DataFrame
    """
    ohlc_dict = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }
    try:
        if target_tf.endswith('m'): 
            freq = f"{int(target_tf[:-1])}T"
        elif target_tf.endswith('h'): 
            freq = f"{int(target_tf[:-1])}H"
        elif target_tf.endswith('d'): 
            freq = f"{int(target_tf[:-1])}D"
        else:
            raise ValueError(f"Unsupported timeframe: {target_tf}")
        
        resampled = df.resample(freq).agg(ohlc_dict).dropna() 
        logger.debug(f"Resampled  {len(df)} → {len(resampled)} bars ({target_tf})")
        return resampled 
        
    except Exception as e:
        logger.error(f"Resampling  failed: {e}")
        raise
 
def fill_missing_data(df: pd.DataFrame, timeframe: str, method: str = 'linear') -> pd.DataFrame:
    """
    填充缺失的K线数据 
    :param method: 填充方式（linear/ffill/bfill）
    """
    if timeframe.endswith('m'): 
        freq = f"{int(timeframe[:-1])}T"
    elif timeframe.endswith('h'): 
        freq = f"{int(timeframe[:-1])}H"
    else:
        freq = "1D"
    
    full_range = pd.date_range(start=df.index.min(),  end=df.index.max(),  freq=freq)
    return df.reindex(full_range).interpolate(method=method) 
 
def calculate_atr(highs: np.ndarray,  lows: np.ndarray,  closes: np.ndarray,  period: int = 14) -> float:
    """
    计算平均真实波幅 (ATR)
    :param highs: 最高价数组 
    :param lows: 最低价数组 
    :param closes: 收盘价数组（前一日）
    """
    if len(highs) < period or len(lows) < period or len(closes) < period:
        raise ValueError(f"数据长度不足 {period}")
    
    tr = np.maximum( 
        highs - lows,
        np.maximum(np.abs(highs  - closes), np.abs(lows  - closes))
    )
    return np.mean(tr[-period:]) 
 
def calculate_technical_indicators(df: pd.DataFrame, indicators: Dict) -> pd.DataFrame:
    """
    批量计算技术指标
    :param indicators: 配置字典 {'RSI': {'period': 14}, 'MACD': {'fast': 12, ...}}
    :return: 添加指标列的DataFrame 
    """
    df = df.copy() 
    closes = df['close'].values
    
    for name, params in indicators.items(): 
        try:
            if name == 'RSI':
                df['RSI'] = _calculate_rsi(closes, params.get('period',  14))
            elif name == 'MACD':
                fast = params.get('fast_period',  12)
                slow = params.get('slow_period',  26)
                df['MACD'], df['MACD_Signal'] = _calculate_macd(closes, fast, slow)
            elif name == 'MA':
                df['MA'] = _calculate_ma(closes, params.get('period',  20), params.get('type',  'SMA'))
            # 可扩展其他指标...
        except Exception as e:
            logger.error(f" 指标计算失败 {name}: {e}")
    
    return df
 
def validate_data_quality(df: pd.DataFrame) -> Dict[str, Union[bool, dict]]:
    """
    数据质量校验 
    :return: {
        'is_valid': bool,
        'issues': {
            'missing_rows': int,
            'abnormal_volume': int,
            'price_spikes': int
        }
    }
    """
    report = {'is_valid': True, 'issues': {}}
    
    # 检查缺失数据 
    missing = df.isnull().sum().sum() 
    if missing > 0:
        report['issues']['missing_rows'] = missing 
        report['is_valid'] = False
    
    # 检查异常成交量（超过3倍标准差）
    vol_mean, vol_std = df['volume'].mean(), df['volume'].std()
    abnormal_vol = len(df[df['volume'] > vol_mean + 3 * vol_std])
    if abnormal_vol > 0:
        report['issues']['abnormal_volume'] = abnormal_vol 
    
    # 检查价格异常波动（单根K线涨跌幅超10%）
    returns = df['close'].pct_change().abs()
    spikes = len(returns[returns > 0.1])
    if spikes > 0:
        report['issues']['price_spikes'] = spikes
    
    return report
 
# ------------------- 私有计算函数 -------------------
def _calculate_rsi(prices: np.ndarray,  period: int = 14) -> np.ndarray: 
    """计算RSI指标"""
    deltas = np.diff(prices) 
    seed = deltas[:period + 1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down 
    rsi = np.zeros_like(prices) 
    rsi[:period] = 100. - 100. / (1. + rs)
    
    for i in range(period, len(prices)):
        delta = deltas[i - 1]
        if delta > 0:
            upval = delta 
            downval = 0.
        else:
            upval = 0.
            downval = -delta 
        
        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period 
        rs = up / down
        rsi[i] = 100. - 100. / (1. + rs)
        
    return rsi 
 
def _calculate_macd(prices: np.ndarray,  fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
    """计算MACD指标（快线、信号线）"""
    ema_fast = pd.Series(prices).ewm(span=fast, adjust=False).mean()
    ema_slow = pd.Series(prices).ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow 
    signal_line = macd_line.ewm(span=signal,  adjust=False).mean()
    return macd_line.values,  signal_line.values 
 
def _calculate_ma(prices: np.ndarray,  period: int, ma_type: str = 'SMA') -> np.ndarray: 
    """计算移动平均线（支持SMA/EMA）"""
    s = pd.Series(prices)
    if ma_type == 'SMA':
        return s.rolling(period).mean().values 
    elif ma_type == 'EMA':
        return s.ewm(span=period,  adjust=False).mean().values
    else:
        raise ValueError(f"不支持的MA类型: {ma_type}")
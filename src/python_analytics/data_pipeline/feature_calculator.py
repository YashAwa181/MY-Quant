import numpy as np
import pandas as pd

def compute_atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    """Calculates Average True Range (ATR)."""
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()
    
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=window).mean()

def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates directional, volatility, and momentum features."""
    data = df.copy()
    
    # 1. Volatility Metrics
    data['atr'] = compute_atr(data, window=14)
    data['returns'] = data['close'].pct_change()
    data['volatility_std'] = data['returns'].rolling(window=20).std()
    
    # 2. Trend & Directional Metrics (EMA Slopes)
    data['ema_20'] = data['close'].ewm(span=20, adjust=False).mean()
    data['ema_50'] = data['close'].ewm(span=50, adjust=False).mean()
    data['ema_slope_20'] = (data['ema_20'] - data['ema_20'].shift(3)) / 3
    
    # 3. Momentum Velocity & Acceleration
    data['momentum_velocity'] = data['close'] - data['close'].shift(5)
    data['momentum_acceleration'] = data['momentum_velocity'] - data['momentum_velocity'].shift(3)
    
    # 4. Market Structure Basics (Swing Highs / Lows)
    data['swing_high'] = data['high'].rolling(window=5, center=True).apply(lambda x: x[2] == max(x), raw=True)
    data['swing_low'] = data['low'].rolling(window=5, center=True).apply(lambda x: x[2] == min(x), raw=True)
    
    return data.dropna()
import pandas as pd
import numpy as np

class VolatilityAnalyzer:
    def __init__(self, df: pd.DataFrame):
        """
        Initializes the Volatility Analyzer to measure compression, 
        expansion, and shock events across the time series.
        """
        self.df = df.copy()

    def _compute_atr(self, window: int = 14) -> pd.Series:
        """Calculates standard Average True Range."""
        high_low = self.df['high'] - self.df['low']
        high_close = (self.df['high'] - self.df['close'].shift()).abs()
        low_close = (self.df['low'] - self.df['close'].shift()).abs()
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(window=window).mean()

    def _analyze_volatility(self):
        """Processes multi-dimensional volatility metrics."""
        # 1. Base ATR and Long-Term Baseline
        self.df['atr'] = self._compute_atr(window=14)
        self.df['atr_baseline'] = self.df['atr'].rolling(window=50).mean()
        
        # 2. Compression vs Expansion Identification
        # Volatility is considered compressed if current ATR is 20% below its baseline
        self.df['compression'] = self.df['atr'] < (self.df['atr_baseline'] * 0.8)
        # Volatility is considered expanding if current ATR is 20% above its baseline
        self.df['expansion'] = self.df['atr'] > (self.df['atr_baseline'] * 1.2)
        # If neither threshold is met, volatility is stable
        self.df['stable'] = ~(self.df['compression'] | self.df['expansion'])
        
        # 3. Candle Dispersion & Intraday Volatility
        self.df['intraday_range_pct'] = (self.df['high'] - self.df['low']) / self.df['open'] * 100
        self.df['candle_dispersion'] = self.df['intraday_range_pct'].rolling(window=20).std()
        
        # 4. Gap Frequency
        # Detects price gaps between sessions or candles greater than 0.2%
        self.df['gap_size'] = (self.df['open'] - self.df['close'].shift(1)).abs() / self.df['close'].shift(1) * 100
        self.df['is_gap'] = self.df['gap_size'] > 0.2
        self.df['gap_freq'] = self.df['is_gap'].rolling(window=20).sum()
        
        # 5. Shock Events
        # Detects moves that exceed 3 standard deviations of recent normal returns
        self.df['returns'] = self.df['close'].pct_change()
        self.df['rolling_std'] = self.df['returns'].rolling(window=20).std()
        self.df['shock_event'] = self.df['returns'].abs() > (self.df['rolling_std'] * 3)
        
        # 6. Normalized Volatility Score (0-100)
        # Normalizes current ATR against the maximum ATR seen in the last 252 periods
        max_atr_historical = self.df['atr'].rolling(window=252, min_periods=20).max()
        self.df['vol_score'] = (self.df['atr'] / max_atr_historical) * 100

    def evaluate_latest(self) -> dict:
        """Returns the final volatility scoring for the current market state."""
        self._analyze_volatility()
        latest = self.df.iloc[-1]
        
        # Handle NaN values during initial warmup periods
        vol_score = int(latest['vol_score']) if pd.notna(latest['vol_score']) else 0
        
        return {
            "Current Volatility": vol_score,
            "Stable": "YES" if latest['stable'] else "NO",
            "Expanding": "YES" if latest['expansion'] else "NO",
            "Compression": "YES" if latest['compression'] else "NO"
        }

if __name__ == "__main__":
    # Example integration using data_loader.py from the sandbox
    from src.python_analytics.data_pipeline.data_loader import fetch_sandbox_data
    
    raw_data = fetch_sandbox_data(symbol="SPY", period="60d", interval="15m")
    analyzer = VolatilityAnalyzer(raw_data)
    
    print("\n--- Volatility Analyzer Output ---")
    results = analyzer.evaluate_latest()
    for key, value in results.items():
        print(f"{key}: {value}")
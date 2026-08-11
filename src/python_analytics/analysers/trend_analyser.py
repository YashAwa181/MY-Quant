import pandas as pd
import numpy as np

class TrendAnalyzer:
    def __init__(self, df: pd.DataFrame):
        """
        Initializes the analyzer to evaluate trend across multiple dimensions.
        """
        self.df = df.copy()
        
    def _compute_quality(self, window: int = 20) -> pd.Series:
        """
        Calculates Trend Quality using Kaufman's Efficiency Ratio (ER).
        ER = absolute net change / sum of absolute individual changes.
        An ER closer to 1.0 indicates a very clean, straight-line trend.
        """
        net_change = self.df['close'].diff(window).abs()
        abs_change = self.df['close'].diff().abs().rolling(window=window).sum()
        return net_change / abs_change

    def _analyze_trend(self):
        """Processes the multiple dimensions of the trend."""
        # 1. Base Moving Averages for foundational direction
        self.df['ema_20'] = self.df['close'].ewm(span=20, adjust=False).mean()
        self.df['ema_50'] = self.df['close'].ewm(span=50, adjust=False).mean()
        
        # 2. Direction
        self.df['bullish'] = self.df['ema_20'] > self.df['ema_50']
        self.df['Direction'] = np.where(self.df['bullish'], 'Bullish', 'Bearish')
        
        # 3. Persistence (Consecutive bars in the same direction)
        direction_changes = self.df['bullish'].ne(self.df['bullish'].shift()).cumsum()
        self.df['Persistence'] = self.df.groupby(direction_changes).cumcount() + 1
        
        # 4. Strength (Normalized EMA Slope to 0-100 scale)
        self.df['ema_slope'] = (self.df['ema_20'] - self.df['ema_20'].shift(3)) / 3
        self.df['Strength'] = (self.df['ema_slope'].abs() / self.df['close'] * 10000).clip(0, 100)
        
        # 5. Acceleration (Derivative of Strength)
        self.df['strength_change'] = self.df['Strength'].diff(3)
        self.df['Acceleration'] = np.where(self.df['strength_change'] > 0, 'Increasing', 'Decreasing')
        
        # 6. Quality (Categorization of smoothness)
        self.df['er'] = self._compute_quality(window=20)
        
        conditions = [
            (self.df['er'] > 0.6),
            (self.df['er'] > 0.4),
            (self.df['er'] > 0.2)
        ]
        choices = ['Excellent', 'Good', 'Fair']
        self.df['Quality'] = np.select(conditions, choices, default='Poor')

    def evaluate_latest(self) -> dict:
        """Returns the final scoring for the current trend state."""
        self._analyze_trend()
        latest = self.df.iloc[-1]
        
        return {
            "Direction": latest['Direction'],
            "Strength": round(latest['Strength'], 2),
            "Acceleration": latest['Acceleration'],
            "Persistence": f"{int(latest['Persistence'])} bars",
            "Quality": latest['Quality']
        }

if __name__ == "__main__":
    # Example integration assuming data_loader.py exists in your sandbox
    from src.python_analytics.data_pipeline.data_loader import fetch_sandbox_data
    
    raw_data = fetch_sandbox_data(symbol="SPY", period="30d", interval="15m")
    analyzer = TrendAnalyzer(raw_data)
    
    print("\n--- Trend Analyzer Output ---")
    results = analyzer.evaluate_latest()
    for key, value in results.items():
        print(f"{key}: {value}")
import pandas as pd
import numpy as np

class MarketStructureAnalyzer:
    def __init__(self, df: pd.DataFrame, swing_window: int = 5):
        """
        Initializes the analyzer with market data and a lookback window 
        for identifying geometric swing points.
        """
        self.df = df.copy()
        self.window = swing_window
        
    def _identify_swings(self):
        """Locates geometric swing highs and swing lows."""
        # A swing high is the highest high in the rolling window
        self.df['swing_high'] = self.df['high'] == self.df['high'].rolling(window=self.window, center=True).max()
        # A swing low is the lowest low in the rolling window
        self.df['swing_low'] = self.df['low'] == self.df['low'].rolling(window=self.window, center=True).min()
        
        # Forward fill the last known swing price levels for comparison
        self.df['last_swing_high'] = self.df['high'].where(self.df['swing_high']).ffill()
        self.df['last_swing_low'] = self.df['low'].where(self.df['swing_low']).ffill()

    def _detect_breaks(self):
        """Detects Break of Structure (BOS) and Change of Character (CHOCH)."""
        self.df['BOS'] = False
        self.df['CHOCH'] = False
        self.df['trend'] = 0 # 1 for Bullish, -1 for Bearish
        
        current_trend = 1
        
        for i in range(1, len(self.df)):
            close_price = self.df['close'].iloc[i]
            last_high = self.df['last_swing_high'].iloc[i-1]
            last_low = self.df['last_swing_low'].iloc[i-1]
            
            # Bullish Structure Logic
            if current_trend == 1:
                if close_price > last_high:
                    self.df.iat[i, self.df.columns.get_loc('BOS')] = True # Trend continues
                elif close_price < last_low:
                    self.df.iat[i, self.df.columns.get_loc('CHOCH')] = True # Trend reverses[cite: 2]
                    current_trend = -1
                    
            # Bearish Structure Logic
            elif current_trend == -1:
                if close_price < last_low:
                    self.df.iat[i, self.df.columns.get_loc('BOS')] = True # Trend continues[cite: 2]
                elif close_price > last_high:
                    self.df.iat[i, self.df.columns.get_loc('CHOCH')] = True # Trend reverses[cite: 2]
                    current_trend = 1
                    
            self.df.iat[i, self.df.columns.get_loc('trend')] = current_trend

    def _evaluate_compression_expansion(self):
        """Determines if the market structure is compressing or expanding[cite: 2]."""
        # Calculate localized price range
        self.df['price_range'] = self.df['high'] - self.df['low']
        self.df['avg_range'] = self.df['price_range'].rolling(window=20).mean()
        
        # Expansion: Current ranges are significantly wider than average[cite: 2]
        self.df['Expansion'] = self.df['price_range'] > (self.df['avg_range'] * 1.5)
        # Compression: Current ranges are significantly tighter than average[cite: 2]
        self.df['Compression'] = self.df['price_range'] < (self.df['avg_range'] * 0.5)

    def analyze(self) -> dict:
        """Returns the final scoring for the current market state[cite: 2]."""
        self._identify_swings()
        self._detect_breaks()
        self._evaluate_compression_expansion()
        
        latest = self.df.iloc[-1]
        recent_trend = self.df['trend'].tail(20)
        
        # Calculate structure control percentages based on recent history
        bull_score = (recent_trend == 1).mean() * 100
        bear_score = (recent_trend == -1).mean() * 100
        
        return {
            "Bull Structure": round(bull_score, 2),
            "Bear Structure": round(bear_score, 2),
            "Compression": bool(latest['Compression']),
            "Expansion": bool(latest['Expansion']),
            "BOS": bool(latest['BOS']),
            "CHOCH": bool(latest['CHOCH'])
        }

if __name__ == "__main__":
    # Assuming fetch_sandbox_data is imported from data_loader.py
    from src.python_analytics.data_pipeline.data_loader import fetch_sandbox_data
    
    raw_data = fetch_sandbox_data(symbol="SPY", period="10d", interval="15m")
    analyzer = MarketStructureAnalyzer(raw_data, swing_window=5)
    
    print("\n--- Market Structure Output ---")
    results = analyzer.analyze()
    for key, value in results.items():
        print(f"{key}: {value}")
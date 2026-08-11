import pandas as pd
import numpy as np
from src.python_analytics.data_pipeline.feature_calculator import compute_features
from src.python_analytics.data_pipeline.data_loader import fetch_sandbox_data

class MarketIntelligenceEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def evaluate_latest(self) -> dict:
        row = self.df.iloc[-1]
        
        # Trend Analyzer Score (0 to 100)
        trend_direction = "Bullish" if row['ema_20'] > row['ema_50'] else "Bearish"
        trend_strength = min(100, abs(row['ema_slope_20']) / row['close'] * 10000)
        
        # Volatility Analyzer Score
        recent_vol = row['volatility_std']
        avg_vol = self.df['volatility_std'].mean()
        vol_score = min(100, (recent_vol / (avg_vol + 1e-8)) * 50)
        
        # Momentum Analyzer Score
        mom_score = min(100, max(0, 50 + (row['momentum_velocity'] / row['close'] * 1000)))
        
        # Aggregated Confidence Calculation
        confidence_index = np.mean([trend_strength, mom_score, 100 - vol_score])
        
        return {
            "Timestamp": row.name,
            "Trend Direction": trend_direction,
            "Trend Strength Score": round(trend_strength, 2),
            "Volatility Score": round(vol_score, 2),
            "Momentum Score": round(mom_score, 2),
            "Aggregated Confidence Index": round(confidence_index, 2)
        }

if __name__ == "__main__":
    raw_data = fetch_sandbox_data(symbol="SPY", period="60d", interval="15m")
    processed_data = compute_features(raw_data)
    
    mie = MarketIntelligenceEngine(processed_data)
    print("\n--- Market Intelligence Snapshot ---")
    for key, value in mie.evaluate_latest().items():
        print(f"{key}: {value}")
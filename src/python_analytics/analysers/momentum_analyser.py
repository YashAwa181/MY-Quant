import pandas as pd
import numpy as np

class MomentumAnalyzer:
    def __init__(self, df: pd.DataFrame, velocity_period: int = 5, accel_period: int = 3):
        """
        Initializes the Momentum Analyzer to evaluate price speed, acceleration, 
        impulse force, exhaustion, and divergences.
        """
        self.df = df.copy()
        self.v_period = velocity_period
        self.a_period = accel_period

    def _compute_rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        """Calculates Relative Strength Index (RSI) for divergence and exhaustion logic."""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / (loss + 1e-8)
        return 100 - (100 / (1 + rs))

    def _detect_divergence(self, lookback: int = 20) -> str:
        """
        Detects regular Bullish or Bearish divergence between price and momentum.
        """
        recent = self.df.tail(lookback)
        if len(recent) < lookback:
            return "None"

        # Check for Bearish Divergence: Higher High in Price, Lower High in Momentum
        price_hh = recent['high'].iloc[-1] > recent['high'].iloc[:-5].max()
        mom_lh = recent['velocity'].iloc[-1] < recent['velocity'].iloc[:-5].max()
        
        # Check for Bullish Divergence: Lower Low in Price, Higher Low in Momentum
        price_ll = recent['low'].iloc[-1] < recent['low'].iloc[:-5].min()
        mom_hl = recent['velocity'].iloc[-1] > recent['velocity'].iloc[:-5].min()

        if price_hh and mom_lh:
            return "Bearish Divergence"
        elif price_ll and mom_hl:
            return "Bullish Divergence"
        return "None"

    def _analyze_momentum(self):
        """Calculates velocity, acceleration, impulse, and exhaustion metrics."""
        # 1. Velocity (Price speed over N bars)
        self.df['velocity'] = self.df['close'] - self.df['close'].shift(self.v_period)
        
        # Normalized Momentum Score (0-100 scale centered at 50)
        volatility = (self.df['high'] - self.df['low']).rolling(window=14).mean()
        normalized_v = (self.df['velocity'] / (volatility + 1e-8)) * 10
        self.df['momentum_score'] = (50 + normalized_v).clip(0, 100)

        # 2. Acceleration (Change in velocity over M bars)
        self.df['acceleration'] = self.df['velocity'] - self.df['velocity'].shift(self.a_period)

        # 3. Impulse (Force evaluation: Are speed and acceleration aligned?)
        v_sign = np.sign(self.df['velocity'])
        a_sign = np.sign(self.df['acceleration'])
        
        conditions = [
            (v_sign == a_sign) & (self.df['acceleration'].abs() > self.df['acceleration'].rolling(10).mean().abs()),
            (v_sign != a_sign)
        ]
        choices = ['Strong', 'Weakening']
        self.df['impulse'] = np.select(conditions, choices, default='Stable')

        # 4. Exhaustion (Velocity decaying while price/RSI at extremes)
        self.df['rsi'] = self._compute_rsi(self.df['close'])
        rsi_extreme = (self.df['rsi'] > 70) | (self.df['rsi'] < 30)
        accel_slowing = self.df['acceleration'] * np.sign(self.df['velocity']) < 0
        
        self.df['exhaustion'] = np.where(
            rsi_extreme & accel_slowing, "Near", "Far"
        )

    def evaluate_latest(self) -> dict:
        """Returns the final momentum evaluation snapshot[cite: 2]."""
        self._analyze_momentum()
        latest = self.df.iloc[-1]
        divergence = self._detect_divergence()

        return {
            "Momentum Score": round(latest['momentum_score'], 2),
            "Velocity": round(latest['velocity'], 2),
            "Acceleration": round(latest['acceleration'], 2),
            "Impulse": latest['impulse'],
            "Exhaustion": latest['exhaustion'],
            "Divergence": divergence
        }

if __name__ == "__main__":
    from src.python_analytics.data_pipeline.data_loader import fetch_sandbox_data

    raw_data = fetch_sandbox_data(symbol="SPY", period="60d", interval="15m")
    analyzer = MomentumAnalyzer(raw_data)

    print("\n--- Momentum Analyzer Output ---")
    results = analyzer.evaluate_latest()
    for key, value in results.items():
        print(f"{key}: {value}")
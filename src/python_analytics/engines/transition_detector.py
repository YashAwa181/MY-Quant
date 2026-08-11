import pandas as pd
from src.python_analytics.analysers.trend_analyser import TrendAnalyzer
from src.python_analytics.analysers.volatility_analyser import VolatilityAnalyzer

class TransitionDetector:
    def __init__(self, df: pd.DataFrame):
        """
        Initializes the Transition Detector to model the exact lifecycle phase
        of the current market.
        """
        self.df = df.copy()
        
        # Initialize dependencies
        self.trend_engine = TrendAnalyzer(self.df)
        self.vol_engine = VolatilityAnalyzer(self.df)

    def _determine_state(self) -> str:
        """Evaluates the combined metrics to classify the transition state."""
        trend_data = self.trend_engine.evaluate_latest()
        vol_data = self.vol_engine.evaluate_latest()
        
        strength = trend_data["Strength"]
        acceleration = trend_data["Acceleration"]
        quality = trend_data["Quality"]
        
        compression = vol_data["Compression"] == "YES"
        expansion = vol_data["Expanding"] == "YES"        
        # State 1: Strong Trend
        if strength > 60 and acceleration == "Increasing" and not compression:
            return "Trend"
            
        # State 2: Weakening Trend[cite: 2]
        # Momentum is stalling or quality is degrading
        if (strength > 40 and acceleration == "Decreasing") or (strength > 60 and quality == "Poor"):
            return "Weak Trend"
            
        # State 4: Compression[cite: 2]
        # Volatility has explicitly dried up (regardless of slight directional drift)
        if compression:
            return "Compression"
            
        # State 5: Expansion[cite: 2]
        # Volatility is violently increasing, usually breaking out of compression
        if expansion and strength < 40:
            return "Expansion"
            
        # State 6: Range (Mean Reverting)[cite: 2]
        # Low directional strength, stable volatility, no compression
        if strength < 30 and not compression and not expansion:
            return "Range"
            
        # State 3: Uncertain[cite: 2]
        # Conflicting signals (e.g., high strength but massive volatility expansion 
        # indicating a potential chaotic news event rather than a clean trend).
        return "Uncertain"

    def evaluate_latest(self) -> dict:
        """Returns the current structural market state[cite: 2]."""
        current_state = self._determine_state()
        
        return {
            "Current Phase": current_state,
            "Lifecycle Sequence": "Trend -> Weak Trend -> Uncertain -> Compression -> Expansion -> Range"
        }

if __name__ == "__main__":
    from src.python_analytics.data_pipeline.data_loader import fetch_sandbox_data

    # Use your sandbox data to test the transition state
    raw_data = fetch_sandbox_data(symbol="SPY", period="60d", interval="15m")
    detector = TransitionDetector(raw_data)

    print("\n--- Transition Detector Output ---")
    results = detector.evaluate_latest()
    for key, value in results.items():
        print(f"{key}: {value}")
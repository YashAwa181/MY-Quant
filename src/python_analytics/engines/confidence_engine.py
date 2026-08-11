import pandas as pd
import numpy as np

# Import the previously built analyzers
from src.python_analytics.analysers.trend_analyser import TrendAnalyzer
from src.python_analytics.analysers.momentum_analyser import MomentumAnalyzer
from src.python_analytics.analysers.volatility_analyser import VolatilityAnalyzer
from src.python_analytics.analysers.liquidity_analyser import LiquidityAnalyzer
from src.python_analytics.analysers.structure_analyser import MarketStructureAnalyzer
from src.python_analytics.engines.transition_detector import TransitionDetector

class ConfidenceEngine:
    def __init__(self, df: pd.DataFrame):
        """
        Initializes the Confidence Engine to aggregate multi-dimensional 
        market metrics into a single tradeable index.
        """
        self.df = df.copy()
        
        # Initialize sub-modules
        self.trend_engine = TrendAnalyzer(self.df)
        self.momentum_engine = MomentumAnalyzer(self.df)
        self.volatility_engine = VolatilityAnalyzer(self.df)
        self.liquidity_engine = LiquidityAnalyzer(self.df)
        self.structure_engine = MarketStructureAnalyzer(self.df, swing_window=5)

    def _calculate_confidence(self) -> dict:
        """
        Calculates the aggregate confidence score by weighting module outputs.
        """
        # 1. Fetch latest data from all modules
        trend = self.trend_engine.evaluate_latest()
        momentum = self.momentum_engine.evaluate_latest()
        volatility = self.volatility_engine.evaluate_latest()
        liquidity = self.liquidity_engine.evaluate_latest()
        structure = self.structure_engine.analyze()

        # 2. Extract Base Scores
        trend_score = trend.get("Strength", 0)
        mom_score = momentum.get("Momentum Score", 0)
        vol_score = volatility.get("Current Volatility", 0)
        
        # 3. Calculate Structure Alignment (0-100)
        # If trend is Bullish, how much of the structure agrees?
        if trend.get("Direction") == "Bullish":
            structure_score = structure.get("Bull Structure", 0)
        else:
            structure_score = structure.get("Bear Structure", 0)

        # 4. Liquidity Adjustment
        # Parse percentage string (e.g., "76.0%") back to float
        sweep_prob_str = liquidity.get("Sweep Probability", "50%").replace("%", "")
        sweep_prob = float(sweep_prob_str)
        # High sweep probability increases overall execution confidence
        liquidity_score = sweep_prob 

        # 5. Apply Weighting Algorithm
        # Weights can be adjusted based on strategy (e.g., trend-following vs mean-reversion)
        weights = {
            "trend": 0.30,
            "structure": 0.25,
            "momentum": 0.20,
            "volatility": 0.15,
            "liquidity": 0.10
        }

        # Inverse volatility score for standard trend-following (high vol = lower confidence)
        normalized_vol = 100 - vol_score if volatility.get("Stable") == "YES" else vol_score

        # Calculate weighted sum
        aggregate_confidence = (
            (trend_score * weights["trend"]) +
            (structure_score * weights["structure"]) +
            (mom_score * weights["momentum"]) +
            (normalized_vol * weights["volatility"]) +
            (liquidity_score * weights["liquidity"])
        )

        # 6. Apply Penalties for Conflicting Data (Divergence or Exhaustion)
        if momentum.get("Exhaustion") == "Near":
            aggregate_confidence *= 0.70  # 30% penalty
        if momentum.get("Divergence") != "None":
            aggregate_confidence *= 0.80  # 20% penalty
            
        final_confidence = min(100.0, max(0.0, aggregate_confidence))

        return {
            "Trend Score": round(trend_score, 1),
            "Structure Score": round(structure_score, 1),
            "Momentum Score": round(mom_score, 1),
            "Volatility Score": round(normalized_vol, 1),
            "Liquidity Score": round(liquidity_score, 1),
            "Final Confidence": round(final_confidence, 1)
        }

    def evaluate_latest(self) -> dict:
        """Outputs the consensus evaluation."""
        return self._calculate_confidence()

if __name__ == "__main__":
    from src.python_analytics.data_pipeline.data_loader import fetch_sandbox_data

    # Load sandbox data
    raw_data = fetch_sandbox_data(symbol="SPY", period="60d", interval="15m")
    
    # Run the consensus engine
    engine = ConfidenceEngine(raw_data)
    
    print("\n--- Confidence Engine Consensus ---")
    results = engine.evaluate_latest()
    for key, value in results.items():
        if key == "Final Confidence":
            print("-" * 35)
            print(f"{key}: {value} / 100")
        else:
            print(f"{key}: {value}")
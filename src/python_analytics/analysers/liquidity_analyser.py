import pandas as pd
import numpy as np

class LiquidityAnalyzer:
    def __init__(self, df: pd.DataFrame, tolerance_pct: float = 0.08, lookback: int = 50):
        """
        Initializes the Liquidity Analyzer to identify Equal Highs/Lows, 
        liquidity pools, and sweep probabilities.
        
        :param tolerance_pct: Percentage threshold within which two price levels are considered "equal".
        :param lookback: Number of historical bars to search for liquidity clusters.
        """
        self.df = df.copy()
        self.tolerance = tolerance_pct / 100.0
        self.lookback = lookback

    def _find_equal_levels(self):
        """Detects Equal Highs (EQH) and Equal Lows (EQL) within the lookback window."""
        recent = self.df.tail(self.lookback)
        highs = recent['high'].values
        lows = recent['low'].values
        
        eqh_count = 0
        eql_count = 0
        
        # Check pairwise distances between recent swing peaks/valleys
        for i in range(len(highs)):
            for j in range(i + 5, len(highs)): # Require at least 5 bars separation
                if abs(highs[i] - highs[j]) / highs[i] <= self.tolerance:
                    eqh_count += 1
                if abs(lows[i] - lows[j]) / lows[i] <= self.tolerance:
                    eql_count += 1

        self.eqh_clusters = eqh_count
        self.eql_clusters = eql_count

    def _evaluate_liquidity_depth(self) -> tuple[str, str]:
        """Categorizes Buy-Side and Sell-Side liquidity depth (High, Medium, Low)."""
        # High count of Equal Highs indicates a large pool of stop losses above (Buy-Side Liquidity)
        if self.eqh_clusters >= 3:
            bsl = "High"
        elif self.eqh_clusters >= 1:
            bsl = "Medium"
        else:
            bsl = "Low"

        # High count of Equal Lows indicates a large pool of stop losses below (Sell-Side Liquidity)
        if self.eql_clusters >= 3:
            ssl = "High"
        elif self.eql_clusters >= 1:
            ssl = "Medium"
        else:
            ssl = "Low"

        return bsl, ssl

    def _calculate_sweep_probability(self, bsl: str, ssl: str) -> float:
        """
        Estimates the probability (0-100%) that price will sweep nearby liquidity pools.
        Probability rises when liquidity is high and price is moving toward the pool.
        """
        latest = self.df.iloc[-1]
        recent_high_max = self.df['high'].tail(self.lookback).max()
        recent_low_min = self.df['low'].tail(self.lookback).min()
        
        dist_to_high = (recent_high_max - latest['close']) / latest['close']
        dist_to_low = (latest['close'] - recent_low_min) / latest['close']

        base_prob = 40.0 # Baseline probability
        
        # Add weight based on pool liquidity density
        if bsl == "High" or ssl == "High":
            base_prob += 25.0
        elif bsl == "Medium" or ssl == "Medium":
            base_prob += 15.0

        # Add weight if price is approaching the nearest liquidity boundary
        min_dist = min(dist_to_high, dist_to_low)
        if min_dist < 0.005: # Within 0.5% of liquidity pool
            base_prob += 20.0
        elif min_dist < 0.01: # Within 1.0% of liquidity pool
            base_prob += 10.0

        return min(95.0, max(10.0, base_prob))

    def evaluate_latest(self) -> dict:
        """Returns the final liquidity assessment output."""
        self._find_equal_levels()
        bsl, ssl = self._evaluate_liquidity_depth()
        sweep_prob = self._calculate_sweep_probability(bsl, ssl)

        return {
            "Buy Side Liquidity": bsl,
            "Sell Side Liquidity": ssl,
            "Sweep Probability": f"{round(sweep_prob, 1)}%",
            "Equal High Clusters": self.eqh_clusters,
            "Equal Low Clusters": self.eql_clusters
        }

if __name__ == "__main__":
    from src.python_analytics.data_pipeline.data_loader import fetch_sandbox_data

    raw_data = fetch_sandbox_data(symbol="SPY", period="60d", interval="15m")
    analyzer = LiquidityAnalyzer(raw_data)

    print("\n--- Liquidity Analyzer Output ---")
    results = analyzer.evaluate_latest()
    for key, value in results.items():
        print(f"{key}: {value}")
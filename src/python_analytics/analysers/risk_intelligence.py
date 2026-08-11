import pandas as pd
import numpy as np

class RiskIntelligence:
    def __init__(self, df: pd.DataFrame):
        """
        Initializes the Risk Intelligence module to evaluate real-time 
        environmental dangers distinct from standard position sizing.
        """
        self.df = df.copy()

    def _evaluate_spread_risk(self) -> float:
        """
        Evaluates the danger of current execution spreads.
        Note: True spread analysis requires bid/ask tick data. For OHLCV data, 
        we proxy this by analyzing the High/Low gap relative to the Open.
        """
        # Calculate localized intraday range as a proxy for liquidity tightness
        self.df['range_pct'] = (self.df['high'] - self.df['low']) / self.df['open'] * 100
        avg_range = self.df['range_pct'].rolling(window=50).mean()
        current_range = self.df['range_pct'].iloc[-1]
        
        # If the current range is massively wider than average, spread/slippage risk is high
        if current_range > (avg_range.iloc[-1] * 2.5):
            return 85.0
        elif current_range > (avg_range.iloc[-1] * 1.5):
            return 50.0
        return 10.0

    def _evaluate_volatility_explosion(self) -> float:
        """
        Detects sudden, violent spikes in market energy that destroy stop losses.
        """
        # Calculate standard Average True Range
        tr = pd.concat([
            self.df['high'] - self.df['low'],
            (self.df['high'] - self.df['close'].shift()).abs(),
            (self.df['low'] - self.df['close'].shift()).abs()
        ], axis=1).max(axis=1)
        
        atr = tr.rolling(window=14).mean()
        
        # Calculate the rate of change of the ATR itself
        atr_roc = atr.pct_change(periods=3) * 100
        current_roc = atr_roc.iloc[-1]
        
        if pd.isna(current_roc):
            return 0.0
            
        # If ATR expands by more than 40% in just 3 bars, volatility is exploding
        if current_roc > 40:
            return 95.0
        elif current_roc > 20:
            return 60.0
        return 15.0

    def _detect_anomalies(self) -> float:
        """
        Detects 3-sigma standard deviation price shocks (Flash Crashes / News events).
        """
        returns = self.df['close'].pct_change()
        rolling_std = returns.rolling(window=20).std()
        
        current_return = returns.iloc[-1]
        current_std = rolling_std.iloc[-1]
        
        if pd.isna(current_return) or pd.isna(current_std) or current_std == 0:
            return 0.0
            
        z_score = abs(current_return / current_std)
        
        if z_score >= 3.0: # 3-Sigma Event
            return 100.0
        elif z_score >= 2.0: # 2-Sigma Event
            return 60.0
        return 0.0

    def evaluate_latest(self) -> dict:
        """Outputs the final environmental risk assessment."""
        spread_risk = self._evaluate_spread_risk()
        vol_risk = self._evaluate_volatility_explosion()
        shock_risk = self._detect_anomalies()
        
        # Aggregate Risk Score (0-100)
        # Weighing immediate price shocks the heaviest
        total_risk = min(100.0, (spread_risk * 0.20) + (vol_risk * 0.35) + (shock_risk * 0.45))
        
        # Generate Actionable Recommendation
        if total_risk >= 80:
            recommendation = "Halt Trading (High Danger)"
        elif total_risk >= 50:
            recommendation = "Trade Small (Reduce Size)"
        else:
            recommendation = "Normal Operations"
            
        return {
            "Spread/Slippage Threat": round(spread_risk, 1),
            "Volatility Explosion Threat": round(vol_risk, 1),
            "Market Shock Threat": round(shock_risk, 1),
            "Total Environmental Risk": round(total_risk, 1),
            "Recommendation": recommendation
        }

if __name__ == "__main__":
    from src.python_analytics.data_pipeline.data_loader import fetch_sandbox_data

    # Load sandbox data
    raw_data = fetch_sandbox_data(symbol="SPY", period="60d", interval="15m")
    
    # Run the Risk Intelligence engine
    risk_engine = RiskIntelligence(raw_data)
    
    print("\n--- Risk Intelligence Assessment ---")
    results = risk_engine.evaluate_latest()
    for key, value in results.items():
        if key == "Total Environmental Risk":
            print("-" * 35)
            print(f"{key}: {value} / 100")
        else:
            print(f"{key}: {value}")
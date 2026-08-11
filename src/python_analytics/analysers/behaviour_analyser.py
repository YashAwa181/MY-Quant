import pandas as pd
import numpy as np

class MarketBehaviourAnalyzer:
    def __init__(self, df: pd.DataFrame, asset_type: str = "forex"):
        """
        Initializes the Behaviour Analyzer to study the empirical personality 
        and statistical habits of the market.
        
        :param asset_type: 'forex' (24-hour) or 'equity' (US Market Hours)
        """
        self.df = df.copy()
        self.asset_type = asset_type.lower()
        
        # Ensure timestamp index is a datetime object
        if not isinstance(self.df.index, pd.DatetimeIndex):
            self.df.index = pd.to_datetime(self.df.index)
            
        # Standardize timezone handling for accurate session tagging
        if self.df.index.tz is None:
            self.df.index = self.df.index.tz_localize('UTC')

    def _assign_sessions(self):
        """Tags each bar with its corresponding trading session dynamically."""
        if self.asset_type == "equity":
            # Convert to US Eastern Time for Equities
            df_tz = self.df.index.tz_convert('America/New_York')
            hours = df_tz.hour
            minutes = df_tz.minute
            
            conditions = [
                ((hours == 9) & (minutes >= 30)) | ((hours >= 10) & (hours < 12)),
                (hours >= 12) & (hours <= 16)
            ]
            choices = ['Morning', 'Afternoon']
        else:
            # Default to UTC Global Sessions for Forex/Crypto
            hours = self.df.index.hour
            conditions = [
                (hours >= 0) & (hours < 8),
                (hours >= 8) & (hours < 13),
                (hours >= 13) & (hours < 22)
            ]
            choices = ['Asian', 'London', 'New York']
            
        self.df['session'] = np.select(conditions, choices, default='Closed')

    def _analyze_session_reversals(self) -> str:
        """Determines the statistical probability of session reversals."""
        session_data = self.df.groupby([self.df.index.date, 'session'])['close'].apply(
            lambda x: x.iloc[-1] - x.iloc[0] if len(x) > 0 else 0
        ).unstack()
        
        # Define the two sessions to compare based on asset type
        sess1, sess2 = ('Morning', 'Afternoon') if self.asset_type == 'equity' else ('London', 'New York')
        
        if sess1 not in session_data.columns or sess2 not in session_data.columns:
            return "Insufficient Session Data"
            
        valid_days = session_data[[sess1, sess2]].dropna()
        
        if len(valid_days) < 5:
            return "Gathering Data"
            
        # Reversal = negative product (sessions moved in opposite directions)
        reversals = (valid_days[sess1] * valid_days[sess2]) < 0
        reversal_rate = reversals.mean() * 100
        
        if reversal_rate > 60:
            return f"High ({reversal_rate:.1f}%)"
        elif reversal_rate < 40:
            return f"Low ({reversal_rate:.1f}% - Trend Continuation)"
        return f"Neutral ({reversal_rate:.1f}%)"

    def _calculate_pullback_size(self) -> float:
        """Calculates the average structural pullback size."""
        recent_ranges = (self.df['high'] - self.df['low']).rolling(window=14).max()
        return recent_ranges.mean()

    def _determine_mean_reversion(self) -> str:
        """Evaluates if the market personality is currently mean-reverting or impulsive."""
        ma = self.df['close'].rolling(window=20).mean()
        crosses = np.sign(self.df['close'] - ma).diff().abs() > 0
        cross_rate = crosses.sum() / len(self.df)
        
        if cross_rate > 0.15:
            return "Highly Mean Reverting"
        elif cross_rate < 0.05:
            return "Highly Impulsive"
        return "Balanced"

    def evaluate_latest(self) -> dict:
        """Returns the behavioural statistics of the market."""
        self._assign_sessions()
        reversal_stat = self._analyze_session_reversals()
        avg_pullback = self._calculate_pullback_size()
        personality = self._determine_mean_reversion()
        
        label = "Afternoon Reverses Morning" if self.asset_type == "equity" else "NY Reverses London"
        
        return {
            "Personality": personality,
            label: reversal_stat,
            "Average Pullback Size": round(avg_pullback, 4)
        }

if __name__ == "__main__":
    from src.python_analytics.data_pipeline.data_loader import fetch_sandbox_data

    print("\n--- Testing US Equity (SPY) ---")
    spy_data = fetch_sandbox_data(symbol="SPY", period="60d", interval="15m")
    equity_analyzer = MarketBehaviourAnalyzer(spy_data, asset_type="equity")
    for key, value in equity_analyzer.evaluate_latest().items():
        print(f"{key}: {value}")

    print("\n--- Testing Forex (EURUSD=X) ---")
    fx_data = fetch_sandbox_data(symbol="EURUSD=X", period="60d", interval="15m")
    fx_analyzer = MarketBehaviourAnalyzer(fx_data, asset_type="forex")
    for key, value in fx_analyzer.evaluate_latest().items():
        print(f"{key}: {value}")
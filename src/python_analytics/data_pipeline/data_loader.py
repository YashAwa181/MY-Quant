import yfinance as yf
import pandas as pd

def fetch_sandbox_data(symbol: str = "SPY", period: str = "60d", interval: str = "15m") -> pd.DataFrame:
    """
    Downloads historical OHLCV data from Yahoo Finance.
    """
    df = yf.download(tickers=symbol, period=period, interval=interval, progress=False)
    
    # Flatten MultiIndex columns if returned by yfinance
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    df.rename(columns={
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume"
    }, inplace=True)
    
    return df.dropna()

if __name__ == "__main__":
    df = fetch_sandbox_data()
    print("Data Ingested Successfully:")
    print(df.tail())
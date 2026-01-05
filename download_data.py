import yfinance as yf
import pandas as pd
import time
import os

ticker = "SPY"
start_date = "2020-01-01"
end_date = "2026-01-01"

print(f"Downloading {ticker} data from {start_date} to {end_date}...")

try:
    time.sleep(2)
    df = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True, progress=False)
    
    if df.empty:
        raise ValueError("Downloaded data is empty")
    
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    
    if 'Close' in df.columns:
        df = df[['Close']].rename(columns={'Close': 'Adj Close'})
    elif 'Adj Close' in df.columns:
        df = df[['Adj Close']]
    else:
        raise ValueError("No valid price column found")
    
    df.index.name = 'Date'
    df = df.reset_index()
    
    if not os.path.exists('data'):
        os.makedirs('data')
    
    file_path = 'data/sp500_historical.csv'
    df.to_csv(file_path, index=False)
    print(f"Successfully downloaded {len(df)} trading days")
    print(f"Data saved to: {file_path}")
    
except Exception as e:
    print(f"Download failed: {e}")
    print("Please check network connection and try again later")


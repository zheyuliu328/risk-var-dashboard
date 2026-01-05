import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm, chi2
import time
from datetime import datetime, timedelta

def get_data(tickers, start, end, max_retries=3):
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                wait_time = 5 * attempt
                print(f"Retrying in {wait_time} seconds (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
            
            data = yf.download(tickers, start=start, end=end, progress=False)['Adj Close']
            
            if data.empty or len(data) == 0:
                raise ValueError("No data downloaded")
            
            returns = data.pct_change().dropna()
            if returns.empty or len(returns) == 0:
                raise ValueError("No returns calculated")
            
            portfolio_return = returns.mean(axis=1)
            print(f"Successfully retrieved {len(portfolio_return)} trading days")
            return portfolio_return
            
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Data retrieval failed after {max_retries} attempts: {e}")
                print("Attempting fallback date range...")
                try:
                    time.sleep(3)
                    data = yf.download(tickers, start='2020-01-01', end='2024-12-31', progress=False)['Adj Close']
                    if not data.empty:
                        returns = data.pct_change().dropna()
                        portfolio_return = returns.mean(axis=1)
                        print(f"Fallback data retrieved: {len(portfolio_return)} trading days")
                        return portfolio_return
                except:
                    pass
                raise ValueError("Unable to retrieve data. Please check network connection or try again later.")
            continue

def generate_sample_data(start_date='2022-01-01', end_date='2026-01-01'):
    print("Using synthetic data mode (fallback when API is rate-limited)...")
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    
    dates = pd.bdate_range(start=start, end=end)
    
    mu = 0.10 / 252
    sigma = 0.20 / np.sqrt(252)
    
    np.random.seed(42)
    returns = np.random.normal(mu, sigma, len(dates))
    
    extreme_days = np.random.choice(len(dates), size=int(len(dates) * 0.02), replace=False)
    returns[extreme_days] += np.random.normal(0, 3*sigma, len(extreme_days))
    
    portfolio_return = pd.Series(returns, index=dates)
    print(f"Generated {len(portfolio_return)} trading days of synthetic data")
    return portfolio_return

def calculate_var(returns, confidence_level=0.99, window=252):
    alpha = 1 - confidence_level
    
    rolling_mean = returns.rolling(window=window).mean()
    rolling_std = returns.rolling(window=window).std()
    z_score = norm.ppf(alpha)
    parametric_var = rolling_mean + z_score * rolling_std
    
    historical_var = returns.rolling(window=window).quantile(alpha)
    
    return parametric_var.dropna(), historical_var.dropna()

def kupiec_pof_test(actual_returns, var_forecasts, confidence_level=0.99):
    exceptions = actual_returns < var_forecasts
    N = len(actual_returns)
    x = exceptions.sum()
    p = 1 - confidence_level
    
    if x == 0:
        LR_pof = -2 * (N * np.log(1 - p) - N * np.log(1))
    else:
        term1 = x * np.log(p) + (N - x) * np.log(1 - p)
        term2 = x * np.log(x/N) + (N - x) * np.log(1 - x/N)
        LR_pof = -2 * (term1 - term2)
    
    critical_value = chi2.ppf(0.95, df=1)
    result = "PASS" if LR_pof < critical_value else "FAIL"
    
    print(f"\n--- Kupiec Test Results ---")
    print(f"Total Observations: {N}")
    print(f"Number of Exceptions: {x}")
    if N > 0:
        print(f"Failure Rate: {x/N:.4f} (Expected: {p:.4f})")
    else:
        print(f"Failure Rate: N/A (Expected: {p:.4f})")
    print(f"LR Statistic: {LR_pof:.4f} (Critical: {critical_value:.4f})")
    print(f"Conclusion: Model {result}")
    
    return exceptions

def plot_results(returns, param_var, hist_var, exceptions, save_path='images/var_dashboard.png'):
    plt.figure(figsize=(12, 6))
    plt.plot(returns.index, returns, label='Daily Returns', color='grey', alpha=0.5, linewidth=0.8)
    plt.plot(param_var.index, param_var, label='Parametric VaR (99%)', color='red', linestyle='--')
    plt.plot(hist_var.index, hist_var, label='Historical VaR (99%)', color='blue', linewidth=1.5)
    
    if exceptions.sum() > 0:
        ex_dates = returns[exceptions].index
        ex_values = returns[exceptions]
        plt.scatter(ex_dates, ex_values, color='black', marker='x', s=50, label='Exceptions', zorder=5)
    
    plt.title('Risk Dashboard: Portfolio VaR Backtesting (S&P 500 Proxy)')
    plt.xlabel('Date')
    plt.ylabel('Daily Returns')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\nChart saved to: {save_path}")
    plt.close()

if __name__ == "__main__":
    try:
        data_returns = get_data(['SPY'], start='2022-01-01', end='2026-01-01')
    except ValueError as e:
        print(f"\nNote: {e}")
        print("Switching to synthetic data mode for demonstration...\n")
        data_returns = generate_sample_data(start_date='2022-01-01', end_date='2026-01-01')
    
    param_var, hist_var = calculate_var(data_returns)
    aligned_returns = data_returns.loc[param_var.index]
    exceptions = kupiec_pof_test(aligned_returns, hist_var, confidence_level=0.99)
    
    if len(aligned_returns) > 0:
        plot_results(aligned_returns, param_var, hist_var, exceptions)
    else:
        print("Warning: Insufficient data for visualization")

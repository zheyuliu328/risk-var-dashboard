import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm, chi2

def get_data(filepath='data/sp500_historical.csv'):
    try:
        print(f"Loading local market data from {filepath}...")
        data = pd.read_csv(filepath, index_col='Date', parse_dates=True)
        returns = data['Adj Close'].pct_change().dropna()
        print(f"Successfully loaded {len(returns)} trading days")
        return returns
    except FileNotFoundError:
        print(f"Error: File {filepath} not found")
        print("Please run download_data.py first to download market data")
        raise
    except Exception as e:
        print(f"Error loading data: {e}")
        raise

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
    failure_rate = x/N if N > 0 else 0.0
    
    print(f"\n--- Kupiec Test Results ---")
    print(f"Total Observations: {N}")
    print(f"Number of Exceptions: {x}")
    print(f"Failure Rate: {failure_rate:.4f} (Expected: {p:.4f})")
    print(f"LR Statistic: {LR_pof:.4f} (Critical: {critical_value:.4f})")
    print(f"Conclusion: Model {result}")
    
    return exceptions, {'N': N, 'x': x, 'failure_rate': failure_rate, 'LR_stat': LR_pof, 'critical_value': critical_value, 'result': result}

def plot_results(returns, param_var, hist_var, exceptions, test_stats, save_path='images/var_dashboard.png'):
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(16, 8))
    fig.patch.set_facecolor('#0d1117')
    ax.set_facecolor('#161b22')
    
    ax.plot(returns.index, returns, label='Daily Returns', color='#8b949e', alpha=0.6, linewidth=0.7, zorder=1)
    ax.plot(param_var.index, param_var, label='Parametric VaR (99%)', color='#f85149', linestyle='-', linewidth=1.8, alpha=0.9, zorder=2)
    ax.plot(hist_var.index, hist_var, label='Historical VaR (99%)', color='#58a6ff', linewidth=2.0, alpha=0.9, zorder=3)
    
    if exceptions.sum() > 0:
        ex_dates = returns[exceptions].index
        ex_values = returns[exceptions]
        ax.scatter(ex_dates, ex_values, color='#ffd700', marker='x', s=100, linewidths=3.0, label='VaR Breaches', zorder=10)
    
    ax.set_title('Risk Dashboard: Portfolio VaR Backtesting | S&P 500 Proxy', 
                 fontsize=16, fontweight='bold', color='#c9d1d9', pad=20)
    ax.set_xlabel('Date', fontsize=12, color='#8b949e')
    ax.set_ylabel('Daily Returns', fontsize=12, color='#8b949e')
    
    ax.tick_params(colors='#8b949e', labelsize=10)
    ax.grid(True, alpha=0.2, color='#30363d', linestyle='--', linewidth=0.8)
    
    legend = ax.legend(loc='upper left', frameon=True, fancybox=True, shadow=True, 
                      facecolor='#161b22', edgecolor='#30363d', fontsize=10)
    for text in legend.get_texts():
        text.set_color('#c9d1d9')
    
    stats_text = f"Kupiec Test: {test_stats['result']} | "
    stats_text += f"LR Stat: {test_stats['LR_stat']:.2f} (Critical: {test_stats['critical_value']:.2f}) | "
    stats_text += f"Failure Rate: {test_stats['failure_rate']:.2%} (Expected: {(1-0.99):.2%})"
    
    if test_stats['result'] == 'FAIL':
        stats_text += "\nFat Tails Detected: Market exhibits extreme risk beyond Normal Distribution"
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
           verticalalignment='top', bbox=dict(boxstyle='round', facecolor='#21262d', 
           edgecolor='#30363d', alpha=0.9), color='#c9d1d9', family='monospace')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='#0d1117')
    print(f"\nChart saved to: {save_path}")
    plt.close()

if __name__ == "__main__":
    data_returns = get_data()
    
    param_var, hist_var = calculate_var(data_returns)
    aligned_returns = data_returns.loc[param_var.index]
    exceptions, test_stats = kupiec_pof_test(aligned_returns, hist_var, confidence_level=0.99)
    
    if len(aligned_returns) > 0:
        plot_results(aligned_returns, param_var, hist_var, exceptions, test_stats)
    else:
        print("Warning: Insufficient data for visualization")

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm, chi2
import time
from datetime import datetime, timedelta

# ==========================================
# 1. 战术准备：数据获取 (Data Ingestion)
# ==========================================
def get_data(tickers, start, end, max_retries=3):
    print(f"正在从前线获取数据: {tickers}...")
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                wait_time = 5 * attempt  # 递增等待时间
                print(f"等待 {wait_time} 秒后重试 (尝试 {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
            
            data = yf.download(tickers, start=start, end=end, progress=False)['Adj Close']
            
            if data.empty or len(data) == 0:
                raise ValueError("No data downloaded")
            
            # 计算投资组合的日收益率（假设等权重）
            returns = data.pct_change().dropna()
            if returns.empty or len(returns) == 0:
                raise ValueError("No returns calculated")
            
            portfolio_return = returns.mean(axis=1) # 简化模型：等权重
            print(f"成功获取 {len(portfolio_return)} 个交易日的数据")
            return portfolio_return
            
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"数据获取失败 (已尝试 {max_retries} 次): {e}")
                print("使用备用日期范围...")
                # 最后一次尝试使用更早的日期范围
                try:
                    time.sleep(3)
                    data = yf.download(tickers, start='2020-01-01', end='2024-12-31', progress=False)['Adj Close']
                    if not data.empty:
                        returns = data.pct_change().dropna()
                        portfolio_return = returns.mean(axis=1)
                        print(f"备用数据获取成功: {len(portfolio_return)} 个交易日")
                        return portfolio_return
                except:
                    pass
                raise ValueError(f"无法获取数据，请稍后重试或检查网络连接")
            continue

def generate_sample_data(start_date='2022-01-01', end_date='2026-01-01'):
    """
    生成合成股票数据用于演示（当API限流时使用）
    使用几何布朗运动模型模拟股票价格
    """
    print("使用合成数据模式（API限流时的备用方案）...")
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    
    # 生成交易日序列（排除周末）
    dates = pd.bdate_range(start=start, end=end)
    
    # 参数：年化收益率 ~10%, 年化波动率 ~20%
    mu = 0.10 / 252  # 日收益率
    sigma = 0.20 / np.sqrt(252)  # 日波动率
    
    # 生成随机收益率
    np.random.seed(42)  # 可复现
    dt = 1
    returns = np.random.normal(mu, sigma, len(dates))
    
    # 添加一些极端事件（模拟市场波动）
    extreme_days = np.random.choice(len(dates), size=int(len(dates) * 0.02), replace=False)
    returns[extreme_days] += np.random.normal(0, 3*sigma, len(extreme_days))
    
    portfolio_return = pd.Series(returns, index=dates)
    print(f"生成了 {len(portfolio_return)} 个交易日的合成数据")
    return portfolio_return

# ==========================================
# 2. 核心武器：VaR 计算引擎 (VaR Engine)
# ==========================================
def calculate_var(returns, confidence_level=0.99, window=252):
    """
    计算历史模拟法 (Historical) 和 参数法 (Parametric) VaR
    """
    alpha = 1 - confidence_level
    
    # 滚动窗口计算
    # 1. 参数法 (Normal Distribution assumption)
    rolling_mean = returns.rolling(window=window).mean()
    rolling_std = returns.rolling(window=window).std()
    # VaR = mean - Z * std (注意VaR通常表示为正数损失，但在时间序列对比中我们通常画负值线)
    z_score = norm.ppf(alpha)
    parametric_var = rolling_mean + z_score * rolling_std
    
    # 2. 历史模拟法 (Historical Simulation)
    historical_var = returns.rolling(window=window).quantile(alpha)
    
    return parametric_var.dropna(), historical_var.dropna()

# ==========================================
# 3. 战果检验：Kupiec POF 回测 (Backtesting)
# ==========================================
def kupiec_pof_test(actual_returns, var_forecasts, confidence_level=0.99):
    """
    Kupiec Proportion of Failures Test
    H0: 模型准确 (例外率 = 1 - confidence_level)
    """
    exceptions = actual_returns < var_forecasts
    N = len(actual_returns)
    x = exceptions.sum() # 例外天数
    p = 1 - confidence_level # 期望失败率 (e.g., 0.01)
    
    # 避免 log(0)
    if x == 0:
        LR_pof = -2 * (N * np.log(1 - p) - N * np.log(1)) # 简化处理
    else:
        # Kupiec LR 统计量公式
        term1 = x * np.log(p) + (N - x) * np.log(1 - p)
        term2 = x * np.log(x/N) + (N - x) * np.log(1 - x/N)
        LR_pof = -2 * (term1 - term2)
    
    # 卡方分布临界值 (1 degree of freedom)
    critical_value = chi2.ppf(0.95, df=1)
    
    result = "PASS (绿灯)" if LR_pof < critical_value else "FAIL (红灯)"
    
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

# ==========================================
# 4. 战场可视化 (Visual Reporting)
# ==========================================
def plot_results(returns, param_var, hist_var, exceptions, save_path='images/var_dashboard.png'):
    plt.figure(figsize=(12, 6))
    plt.plot(returns.index, returns, label='Daily Returns', color='grey', alpha=0.5, linewidth=0.8)
    plt.plot(param_var.index, param_var, label='Parametric VaR (99%)', color='red', linestyle='--')
    plt.plot(hist_var.index, hist_var, label='Historical VaR (99%)', color='blue', linewidth=1.5)
    
    # 标记突破点 (Exceptions)
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
    print(f"\n图表已保存至: {save_path}")
    plt.close()

# ==========================================
# 指挥官入口
# ==========================================
if __name__ == "__main__":
    # 模拟一个简单的投资组合：SPY (美股大盘)
    # 哲宇，把这里的日期改成最新的，体现你在 continually monitoring
    try:
        data_returns = get_data(['SPY'], start='2022-01-01', end='2026-01-01')
    except ValueError as e:
        print(f"\n注意: {e}")
        print("切换到合成数据模式以演示功能...\n")
        data_returns = generate_sample_data(start_date='2022-01-01', end_date='2026-01-01')
    
    # 留出前252天作为预热窗口，不参与回测
    param_var, hist_var = calculate_var(data_returns)
    
    # 对齐数据（切掉前252天）
    aligned_returns = data_returns.loc[param_var.index]
    
    # 执行回测
    exceptions = kupiec_pof_test(aligned_returns, hist_var, confidence_level=0.99)
    
    # 绘图
    if len(aligned_returns) > 0:
        plot_results(aligned_returns, param_var, hist_var, exceptions)
    else:
        print("警告: 没有足够的数据进行可视化")


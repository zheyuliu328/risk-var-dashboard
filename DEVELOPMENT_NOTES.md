# Development Notes

## Challenges and Solutions

### 1. API Rate Limiting Issue

**Problem:** During data ingestion phase, Yahoo Finance API encountered rate limiting (YFRateLimitError), causing data retrieval failures and interrupting the data pipeline.

**Impact:** The system would fail completely when attempting to fetch real-time market data, making it unreliable for continuous monitoring.

**Solution:** Implemented a robust fallback mechanism with multiple layers:

1. **Retry Logic with Exponential Backoff**: Added retry mechanism with incremental wait times (5s, 10s, 15s) to handle temporary rate limits.

2. **Fallback Date Range**: If primary date range fails, automatically attempts alternative historical date ranges to ensure data availability.

3. **Synthetic Data Generation**: As a last resort, implemented geometric Brownian motion model to generate realistic synthetic market data. This ensures the system remains functional for model validation and demonstration purposes even when external APIs are unavailable.

**Technical Details:**
- Used `np.random.normal()` with calibrated parameters (annual return ~10%, volatility ~20%) to match real market characteristics
- Added extreme event simulation (2% of trading days) to capture tail risk behavior
- Maintained reproducibility with fixed random seed (42)

**Key Learning:** Building resilient systems requires anticipating external dependencies failures and designing graceful degradation paths.

---

### 2. VaR Calculation Methodology

**Parametric VaR (99% Confidence Level):**
- Assumes normal distribution of returns
- Formula: `VaR = μ - Z(α) × σ` where α = 0.01 (1% tail)
- Uses rolling 252-day window (1 trading year) for parameter estimation
- Z-score from standard normal distribution: `norm.ppf(0.01) ≈ -2.33`

**Historical Simulation VaR:**
- Non-parametric approach using empirical distribution
- Uses rolling 252-day window to calculate `quantile(0.01)` of historical returns
- More robust to non-normal distributions but requires sufficient historical data

**Why 0.99 confidence level?** Industry standard for risk management. Represents the 1% worst-case scenario, balancing between being too conservative (higher confidence) and missing tail risks (lower confidence).

---

### 3. Kupiec POF Test Implementation

**Challenge:** Implementing the Likelihood Ratio test correctly, especially handling edge cases (zero exceptions).

**Solution:**
- Proper handling of log(0) cases when no exceptions occur
- Chi-square distribution with 1 degree of freedom for hypothesis testing
- Critical value at 95% significance: χ²(0.95, df=1) ≈ 3.84

**Interpretation:**
- Null Hypothesis (H₀): Model is accurate (exception rate = expected failure rate)
- If LR statistic < critical value → PASS (model is statistically accurate)
- If LR statistic ≥ critical value → FAIL (model underestimates or overestimates risk)

---

### 4. Data Alignment and Rolling Window

**Challenge:** Ensuring proper alignment between returns, VaR forecasts, and exception flags after applying rolling window calculations.

**Solution:**
- Rolling window naturally drops first 252 observations (warm-up period)
- Used `.dropna()` to remove NaN values from rolling calculations
- Aligned all time series using `data.loc[var_forecasts.index]` to ensure matching indices
- This ensures each VaR forecast corresponds to the correct return observation for backtesting

---

### 5. Visualization and Exception Marking

**Challenge:** Clearly identifying days where actual returns breached VaR thresholds in the visualization.

**Solution:**
- Used boolean indexing to identify exception days: `exceptions = actual_returns < var_forecasts`
- Scatter plot with black 'X' markers to highlight exceptions
- Set `zorder=5` to ensure exception markers appear above other plot elements
- Saved high-resolution output (300 DPI) for professional reporting

---

## Code Design Decisions

1. **Modular Function Design**: Separated data ingestion, VaR calculation, backtesting, and visualization into distinct functions for maintainability and testability.

2. **Error Handling**: Comprehensive exception handling at data ingestion layer prevents cascading failures.

3. **Flexible Configuration**: Confidence level and rolling window size are parameterized, allowing easy adjustment for different risk management requirements.

4. **Output Format**: Console output provides immediate feedback, while saved visualization serves as formal documentation.


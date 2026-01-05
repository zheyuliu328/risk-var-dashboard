# Development Notes

## Challenges and Solutions

### 1. API Rate Limiting and Data Retrieval Robustness

During the initial data ingestion phase, the Yahoo Finance API encountered rate limiting issues that caused intermittent data retrieval failures. This presented a critical challenge because the entire risk dashboard depends on reliable access to historical market data. When the API rate limit was triggered, the system would fail completely, making it unsuitable for production use where continuous monitoring is essential.

To address this problem, I implemented a multi-layered fallback mechanism designed to maximize the probability of successfully retrieving real market data. The first layer involves an exponential backoff retry strategy with increasing wait times between attempts. This handles temporary rate limits that may resolve themselves after a brief pause. The retry mechanism attempts up to five times with wait intervals of 10, 20, 30, 40, and 50 seconds respectively, giving the API sufficient time to reset its rate limit counter.

When the primary date range fails after all retry attempts, the system automatically attempts multiple alternative historical date ranges. I configured four different fallback periods spanning from 2017 to 2024, each with sufficient historical depth to support the 252-day rolling window required for VaR calculations. This approach recognizes that while the most recent data may be rate-limited, older historical data might still be accessible. Each alternative range is tested sequentially with appropriate delays to avoid triggering additional rate limits.

The key insight here is that production risk management systems cannot rely on synthetic data. Real market data contains actual correlations, volatility clustering, and tail events that synthetic models cannot fully capture. Therefore, the system is designed to exhaust all possible avenues for obtaining real market data before failing, ensuring that any analysis performed is based on actual market behavior rather than simulated patterns.

### 2. VaR Calculation Methodology and Confidence Level Selection

The Value-at-Risk calculation employs two complementary methodologies to provide a comprehensive view of portfolio risk. The parametric approach assumes that returns follow a normal distribution, which allows for analytical calculation using the mean and standard deviation of historical returns. This method calculates VaR as the mean return minus the product of the Z-score corresponding to the confidence level and the standard deviation. For a 99% confidence level, this translates to alpha equals 0.01, meaning we're identifying the 1% worst-case scenario. The Z-score for this tail probability is approximately negative 2.33 from the standard normal distribution.

The historical simulation method takes a non-parametric approach by directly using the empirical distribution of historical returns. Instead of assuming normality, this method sorts the historical returns and identifies the quantile corresponding to the confidence level. For 99% confidence, this means finding the 1st percentile of the historical return distribution. This approach is more robust to deviations from normality, such as fat tails or skewness, which are common in financial markets.

Both methods use a rolling 252-day window, which represents one full trading year. This window size balances the need for sufficient data points to estimate parameters reliably while remaining responsive to changing market conditions. The rolling window approach ensures that the VaR estimates adapt to recent market volatility rather than being anchored to distant historical periods that may no longer be relevant.

The choice of 99% confidence level represents an industry standard in risk management. This level balances the competing objectives of being conservative enough to capture tail risks while not being so conservative that the VaR estimates become meaningless for practical decision-making. A higher confidence level like 99.9% would capture even more extreme events but would result in VaR estimates so large that they might not be actionable. Conversely, a lower confidence level like 95% would be more likely to be breached, reducing the model's credibility.

### 3. Kupiec POF Test Implementation and Statistical Validation

The Kupiec Proportion of Failures test serves as the primary mechanism for validating the accuracy of the VaR model. This test evaluates whether the observed frequency of exceptions, defined as days when actual returns breach the VaR threshold, matches the expected frequency implied by the confidence level. For a 99% VaR model, we expect exceptions to occur approximately 1% of the time.

Implementing this test correctly required careful attention to the statistical theory underlying the likelihood ratio test. The test statistic follows a chi-square distribution with one degree of freedom, and the critical value at 95% significance level is approximately 3.84. When the calculated likelihood ratio statistic falls below this critical value, we fail to reject the null hypothesis that the model is accurate, resulting in a PASS verdict. If the statistic exceeds the critical value, we reject the null hypothesis and conclude that the model is either underestimating or overestimating risk, resulting in a FAIL verdict.

One particular challenge was handling the edge case where no exceptions occur during the backtesting period. In this scenario, the standard likelihood ratio formula involves taking the logarithm of zero, which is undefined. I addressed this by implementing a special case that calculates the likelihood ratio using the limit as the number of exceptions approaches zero, ensuring the test remains mathematically sound even when the observed exception rate is exactly zero.

The test provides a traffic-light system that gives immediate feedback on model performance. A PASS result indicates that the model is statistically consistent with the expected exception rate, providing confidence that the VaR estimates are reliable for risk management purposes. A FAIL result triggers the need for model review and potential recalibration, ensuring that risk management decisions are based on accurate risk estimates.

### 4. Data Alignment and Rolling Window Implementation

Ensuring proper temporal alignment between returns, VaR forecasts, and exception flags presented a subtle but critical challenge. The rolling window calculation naturally introduces a warm-up period where the first 252 observations cannot produce VaR estimates because there isn't sufficient historical data. This means that the VaR time series begins 252 days after the returns time series starts.

To handle this alignment issue, I implemented a systematic approach where the rolling window calculations automatically drop the initial observations that don't have sufficient history. The VaR calculation functions return time series that begin only after the rolling window is fully populated. Then, when aligning the actual returns with the VaR forecasts for backtesting, I use pandas index-based alignment to ensure that each VaR forecast corresponds to the correct return observation on the same date.

This alignment is crucial because the Kupiec test requires comparing each VaR forecast with the actual return that occurred on that same day. Any misalignment would invalidate the statistical test results, potentially leading to incorrect conclusions about model accuracy. The solution uses pandas' robust indexing capabilities to guarantee that the time series are properly synchronized before performing any comparisons or calculations.

### 5. Visualization Design and Exception Highlighting

Creating an effective visualization that clearly communicates risk information required careful consideration of visual design principles. The dashboard displays three key elements: the daily returns as a grey line showing actual portfolio performance, the parametric VaR as a red dashed line indicating the analytical risk estimate, and the historical VaR as a solid blue line showing the empirical risk estimate. These visual distinctions help users quickly understand the relationship between actual performance and risk thresholds.

The most critical visual element is the marking of exception days, which are the days when actual returns breached the VaR threshold. These exceptions are marked with black X markers that stand out clearly against the other plot elements. I used boolean indexing to identify these exception days efficiently, comparing the actual returns series with the VaR forecasts series to create a boolean mask. This mask is then used to extract the dates and values corresponding to exceptions, which are plotted as scatter points.

To ensure the exception markers are always visible, I set the zorder parameter to 5, which places them above all other plot elements in the visual stacking order. This guarantees that even when multiple elements overlap, the exception markers remain clearly visible. The visualization is saved at 300 DPI resolution, which provides sufficient quality for professional reporting and presentation purposes while maintaining reasonable file sizes.

## Code Design Philosophy

The codebase is structured around modular function design, with each major component separated into distinct functions. This separation serves multiple purposes. First, it enhances maintainability by allowing each function to be understood, tested, and modified independently. Second, it improves testability by enabling unit testing of individual components without requiring the entire system to be executed. Third, it facilitates future enhancements, as new features can be added by extending existing functions or adding new ones without disrupting the overall architecture.

Error handling is implemented comprehensively at the data ingestion layer, which is the most likely point of failure due to external dependencies. By catching and handling exceptions at this early stage, the system prevents cascading failures that could corrupt calculations or produce misleading results. The error messages are designed to be informative, helping users understand what went wrong and what actions they might take to resolve the issue.

The system is designed with flexibility in mind, with key parameters like confidence level and rolling window size exposed as function parameters rather than hard-coded constants. This allows the same codebase to be used for different risk management requirements without modification. For example, a more conservative risk manager might prefer a 99.5% confidence level, while a more aggressive one might use 95%, and both can be accommodated by simply changing the parameter value.

Finally, the output format balances immediate feedback with formal documentation. Console output provides real-time information about data retrieval, calculation progress, and test results, allowing users to monitor the system's operation. Simultaneously, the saved visualization serves as a permanent record that can be included in reports, presentations, or regulatory submissions, ensuring that the analysis is properly documented for compliance and audit purposes.

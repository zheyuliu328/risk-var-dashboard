# VaR Risk Dashboard

> A production-grade Market Risk Engine for calculating and validating 99% Value-at-Risk with statistical backtesting

![Risk Dashboard](images/var_dashboard.png)

---

## Overview

This engine calculates and validates 99% Value-at-Risk (VaR) using real-world S&P 500 market data spanning from 2020 to 2026. The analysis reveals critical insights about fat-tail risks during market stress periods, demonstrating why standard normal distribution assumptions fall short in extreme conditions. The model identified a 1.67% failure rate, which exceeds the expected 1% threshold, with the Kupiec test correctly rejecting the null hypothesis through a likelihood ratio statistic of 4.77. This provides empirical evidence for the necessity of Expected Shortfall and stress testing in modern risk management frameworks.

---

## Features

The engine implements a dual-calculation approach, employing both Parametric VaR based on the variance-covariance method and Historical Simulation VaR using empirical distributions. This dual methodology enables comparison between theoretical and observed risk patterns, revealing when market behavior deviates from standard assumptions.

Statistical validation is integrated through the Kupiec Proportion of Failures test, which rigorously evaluates whether the observed exception rate matches the expected rate implied by the confidence level. The test provides a traffic-light system where PASS indicates model accuracy and FAIL triggers the need for model review and recalibration.

Visualization follows institutional reporting standards with a Bloomberg Terminal-inspired dark theme that clearly highlights risk breaches and volatility clusters. The dashboard automatically annotates key statistics including Kupiec test results, likelihood ratio statistics, and failure rates, providing immediate context for risk assessment decisions. All outputs are generated at high resolution suitable for presentations and regulatory reporting.

The architecture is designed for production use, featuring static data persistence for reproducibility, extensible design with clear component separation, and robust error handling throughout the data pipeline. This ensures that risk calculations remain reliable and repeatable regardless of network conditions or external API availability.

---

## Quick Start

Install the required dependencies using `pip install -r requirements.txt`. This will install all necessary packages including pandas, numpy, matplotlib, scipy, and yfinance. Next, run the `download_data.py` script to fetch and store historical market data from Yahoo Finance. This step only needs to be performed once, as the data will be saved locally for future use. Finally, execute `main.py` to run the complete analysis, which will automatically load the processed dataset, calculate rolling VaR metrics using both parametric and historical methods, perform Kupiec backtesting to validate model accuracy, and generate the dashboard visualization.

---

## Methodology

The engine operates on a rolling 252-day window, representing approximately one full trading year. This window size balances the need for sufficient historical data to estimate parameters reliably while remaining responsive to changing market conditions. The rolling approach ensures that VaR estimates adapt to recent volatility patterns rather than being anchored to distant historical periods.

The Parametric VaR calculation uses the variance-covariance method, which assumes that returns follow a normal distribution. The formula calculates VaR as the mean return minus the product of the Z-score corresponding to the confidence level and the standard deviation. For a 99% confidence level, this translates to identifying the 1% worst-case scenario using a Z-score of approximately 2.33 from the standard normal distribution.

The Historical Simulation method takes a non-parametric approach by directly using the empirical distribution of historical returns. Instead of assuming normality, this method sorts the historical returns and identifies the quantile corresponding to the confidence level. For 99% confidence, this means finding the 1st percentile of the historical return distribution. This approach is more robust to deviations from normality such as fat tails or skewness, which are common in financial markets.

The Kupiec test evaluates the null hypothesis that the observed failure rate matches the expected failure rate implied by the confidence level. The test uses a likelihood ratio statistic that follows a chi-square distribution with one degree of freedom. The critical value at 95% significance level is approximately 3.84. When the calculated likelihood ratio statistic falls below this critical value, we fail to reject the null hypothesis, resulting in a PASS verdict indicating the model is statistically accurate. If the statistic exceeds the critical value, we reject the null hypothesis and conclude that the model is either underestimating or overestimating risk, resulting in a FAIL verdict.

---

## Technology Stack

The implementation uses Python 3.9 or higher as the core programming language, leveraging NumPy and Pandas for efficient vectorized operations on time series data. These libraries enable the rolling window calculations and statistical operations to be performed efficiently even on large datasets spanning multiple years of daily market data. Statistical computations rely on SciPy for chi-square testing and normal distribution quantile calculations, while visualization is handled by Matplotlib with extensive customization to meet institutional reporting standards. Market data integration is facilitated through yfinance, which provides seamless access to historical price data from Yahoo Finance.

---

## Project Structure

The project is organized into clear functional components. The `main.py` file contains the primary VaR calculation engine, Kupiec testing logic, and visualization code. The `download_data.py` script handles the data pipeline for fetching and cleaning real market data from Yahoo Finance. The `data` directory stores the processed market data in CSV format, specifically S&P 500 historical prices from 2020 to 2026. The `images` directory contains generated reports and charts, with the primary output being the VaR backtesting dashboard visualization saved at high resolution.

---

## Results

The analysis demonstrates that during the 2022 Federal Reserve rate hike cycle, the normal distribution assumption underlying Parametric VaR was inadequate. The observed exception rate of 1.67% significantly differs from the expected 1%, highlighting the importance of non-parametric methods such as Historical Simulation, complementary risk measures including Expected Shortfall, and comprehensive stress testing frameworks. The likelihood ratio statistic of 4.77 exceeded the critical value of 3.84, leading to rejection of the null hypothesis and providing statistical evidence that the normal distribution assumption is insufficient for capturing the true risk profile during periods of market stress.

---

## License

MIT License

---

*For detailed development notes and technical decisions, see [DEVELOPMENT_NOTES.md](DEVELOPMENT_NOTES.md)*

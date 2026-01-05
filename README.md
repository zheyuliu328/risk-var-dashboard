# Quantitative Risk Engine: VaR Modeling & Backtesting Dashboard

![Risk Dashboard](images/var_dashboard.png)

## Executive Summary

This project implements a production-grade Market Risk Engine designed to calculate and validate 99% Value-at-Risk (VaR) for equity portfolios. Unlike theoretical exercises, this engine is tested against real-world market data from the S&P 500 spanning 2020 to 2026, demonstrating the limitations of normal distribution assumptions during extreme market stress periods such as the 2022 Federal Reserve rate hike cycle.

The key finding from this analysis is that the model identified a 1.67% failure rate, which exceeds the expected 1% threshold. This result successfully captures what risk professionals call "Fat Tail" risks, where extreme events occur more frequently than standard normal distribution models predict. The Kupiec statistical test correctly rejected the null hypothesis with a likelihood ratio statistic of 4.77, providing empirical evidence for why Expected Shortfall (ES) and stress testing are necessary supplements to VaR in modern risk management frameworks.

## Technical Features

The engine implements a dual-calculation approach using both Parametric VaR based on normal distribution assumptions and Historical Simulation VaR using empirical distributions. This dual methodology allows for comparison between theoretical and observed risk patterns, revealing when market behavior deviates from standard assumptions.

Statistical validation is integrated through the Kupiec Proportion of Failures (POF) test, which rigorously evaluates whether the observed exception rate matches the expected rate implied by the confidence level. This test provides a traffic-light system where PASS indicates model accuracy and FAIL triggers the need for model review and recalibration.

The data engineering layer includes a static data persistence mechanism that stores verified market data locally, ensuring reproducibility and eliminating dependency on external API rate limits. This design choice reflects production considerations where risk calculations must be reliable and repeatable regardless of network conditions. The architecture is designed to be extensible, with clear separation between data ingestion, calculation, validation, and visualization components, making it straightforward to integrate future enhancements such as Monte Carlo simulation.

Visualization follows institutional reporting standards with a Bloomberg Terminal-inspired dark theme that clearly highlights risk breaches and volatility clusters. The dashboard automatically annotates key statistics including the Kupiec test results, likelihood ratio statistics, and failure rates, providing immediate context for risk assessment decisions.

## Methodology and Mathematical Foundation

The engine operates on a rolling 252-day window, which represents approximately one full trading year. This window size balances the need for sufficient historical data to estimate parameters reliably while remaining responsive to changing market conditions. The rolling approach ensures that VaR estimates adapt to recent volatility patterns rather than being anchored to distant historical periods that may no longer be relevant.

The Parametric VaR calculation uses the variance-covariance method, which assumes that returns follow a normal distribution. The formula calculates VaR as the mean return minus the product of the Z-score corresponding to the confidence level and the standard deviation. For a 99% confidence level, this translates to alpha equals 0.01, meaning we're identifying the 1% worst-case scenario. The Z-score for this tail probability is approximately 2.33 from the standard normal distribution. However, as this project's backtesting demonstrates, this assumption is often violated in real markets, particularly during periods of extreme stress.

The Historical Simulation method takes a non-parametric approach by directly using the empirical distribution of historical returns. Instead of assuming normality, this method sorts the historical returns and identifies the quantile corresponding to the confidence level. For 99% confidence, this means finding the 1st percentile of the historical return distribution. This approach is more robust to deviations from normality such as fat tails or skewness, which are common in financial markets.

The Kupiec test evaluates the null hypothesis that the observed failure rate matches the expected failure rate implied by the confidence level. The test uses a likelihood ratio statistic that follows a chi-square distribution with one degree of freedom. The critical value at 95% significance level is approximately 3.84. When the calculated likelihood ratio statistic falls below this critical value, we fail to reject the null hypothesis, resulting in a PASS verdict indicating the model is statistically accurate. If the statistic exceeds the critical value, we reject the null hypothesis and conclude that the model is either underestimating or overestimating risk, resulting in a FAIL verdict.

In this analysis, the likelihood ratio statistic of 4.77 exceeded the critical value of 3.84, leading to rejection of the null hypothesis. This provides statistical evidence that the observed exception rate of 1.67% is significantly different from the expected 1%, indicating that the normal distribution assumption underlying Parametric VaR is inadequate for capturing the true risk profile during the analysis period.

## Technology Stack

The implementation uses Python 3.9 or higher as the core programming language, leveraging NumPy and Pandas for efficient vectorized operations on time series data. These libraries enable the rolling window calculations and statistical operations to be performed efficiently even on large datasets spanning multiple years of daily market data.

Statistical computations rely on SciPy for chi-square testing and normal distribution quantile calculations. The scipy.stats module provides the norm.ppf function for calculating Z-scores and the chi2.ppf function for determining critical values in hypothesis testing.

Visualization is handled by Matplotlib with extensive customization to meet institutional reporting standards. The plotting code implements a dark theme inspired by Bloomberg Terminal aesthetics, with carefully chosen color schemes that ensure clarity while maintaining a professional appearance suitable for risk management presentations and regulatory reporting.

## Project Structure

The project is organized into clear functional components. The main.py file contains the primary VaR calculation engine, Kupiec testing logic, and visualization code. This file can be executed directly to reproduce the complete analysis from data loading through statistical testing to chart generation.

The download_data.py script handles the data pipeline for fetching and cleaning real market data from Yahoo Finance. This script is designed to be run once to establish a local data repository, after which the main analysis can run independently without network connectivity. The script includes error handling and data validation to ensure data quality.

The data directory stores the processed market data in CSV format, specifically the S&P 500 historical prices from 2020 to 2026. This static storage approach ensures that the analysis is reproducible and not subject to external API availability or rate limiting issues.

The images directory contains generated reports and charts, with the primary output being the VaR backtesting dashboard visualization. This chart is saved at high resolution suitable for inclusion in presentations, reports, or regulatory submissions.

## Usage Instructions

To reproduce this analysis, begin by installing the required dependencies using pip install with the requirements.txt file. This will install all necessary packages including pandas, numpy, matplotlib, scipy, and yfinance.

Next, run the download_data.py script to fetch and store the historical market data. This step only needs to be performed once, as the data will be saved locally for future use. The script downloads SPY data from 2020-01-01 to 2026-01-01 and saves it to the data directory in CSV format.

Finally, execute the main.py script to run the complete analysis. The system will automatically load the processed dataset, calculate rolling VaR metrics using both parametric and historical methods, perform Kupiec backtesting to validate model accuracy, and generate the dashboard visualization. The chart will be saved to the images directory, and the statistical test results will be displayed in the console output.

## Development Notes

For detailed information about challenges encountered during development and their solutions, see DEVELOPMENT_NOTES.md. This document provides comprehensive coverage of the technical decisions made during implementation, including data engineering considerations, statistical testing methodology, and visualization design choices.

## Impact and Applications

This implementation demonstrates real-world financial data integration with robust error handling, statistical risk modeling using both parametric and non-parametric approaches, and model validation using industry-standard backtesting frameworks. The system is designed for production use where reliability and accuracy are paramount, providing a foundation that can be extended with additional features such as Monte Carlo simulation, Conditional VaR calculation, multi-asset portfolio support with correlation modeling, and real-time data streaming capabilities.

The analysis results provide valuable insights into the limitations of standard VaR models during periods of market stress, reinforcing the importance of complementary risk measures and stress testing in comprehensive risk management frameworks.

## License

MIT License

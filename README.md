# VaR Risk Dashboard

> A production-grade Market Risk Engine for calculating and validating 99% Value-at-Risk with statistical backtesting

![Risk Dashboard](images/var_dashboard.png)

---

## Overview

This engine calculates and validates 99% Value-at-Risk (VaR) using real-world S&P 500 market data (2020-2026). The analysis reveals critical insights about fat-tail risks during market stress periods, demonstrating why standard normal distribution assumptions fall short in extreme conditions.

The model identified a **1.67% failure rate** (exceeding the expected 1% threshold), with the Kupiec test correctly rejecting the null hypothesis (LR statistic: 4.77). This provides empirical evidence for the necessity of Expected Shortfall and stress testing in modern risk management frameworks.

---

## Quick Start

```bash
pip install -r requirements.txt
python download_data.py
python main.py
```

---

## Methodology

The engine implements dual-calculation approaches: **Parametric VaR** using variance-covariance method and **Historical Simulation VaR** using empirical distributions. Statistical validation is performed through the Kupiec Proportion of Failures test, operating on a rolling 252-day window to ensure VaR estimates adapt to recent volatility patterns.

---

## Technology Stack

Python 3.9+, NumPy, Pandas, SciPy, Matplotlib, yfinance

---

## License

MIT License

# VaR Risk Dashboard

> A production-grade Market Risk Engine for calculating and validating 99% Value-at-Risk with statistical backtesting

![Risk Dashboard](images/var_dashboard.png)

---

## Overview

This engine calculates and validates **99% Value-at-Risk (VaR)** using real-world S&P 500 market data (2020-2026). The analysis reveals critical insights about fat-tail risks during market stress periods, demonstrating why standard normal distribution assumptions fall short in extreme conditions.

**Key Finding:** The model identified a **1.67% failure rate** (exceeding the expected 1% threshold), with the Kupiec test correctly rejecting the null hypothesis (LR statistic: 4.77). This provides empirical evidence for the necessity of Expected Shortfall and stress testing in modern risk frameworks.

---

## Features

✨ **Dual Methodology**
- Parametric VaR (variance-covariance method)
- Historical Simulation VaR (non-parametric)

📊 **Statistical Validation**
- Kupiec Proportion of Failures (POF) test
- Traffic-light system (PASS/FAIL) for model accuracy

🎨 **Institutional-Grade Visualization**
- Bloomberg Terminal-inspired dark theme
- Automated annotation of key statistics
- High-resolution output for presentations

🔧 **Production-Ready Architecture**
- Static data persistence for reproducibility
- Extensible design with clear component separation
- Robust error handling and data validation

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Download market data (one-time setup)
python download_data.py

# Run analysis and generate dashboard
python main.py
```

---

## Methodology

**Rolling Window:** 252 trading days (≈ 1 year)

**Parametric VaR:** Assumes normal distribution, uses Z-score (2.33 for 99% confidence)

**Historical Simulation:** Uses empirical distribution, identifies 1st percentile directly

**Kupiec Test:** Evaluates model accuracy using likelihood ratio statistic (critical value: 3.84)

---

## Technology Stack

- **Python 3.9+**
- **NumPy & Pandas** — Vectorized time series operations
- **SciPy** — Statistical testing and distributions
- **Matplotlib** — Professional visualization
- **yfinance** — Market data integration

---

## Project Structure

```
Risk_VaR_Dashboard/
├── main.py              # VaR engine, backtesting, visualization
├── download_data.py     # Data pipeline (Yahoo Finance)
├── data/                # Historical market data (CSV)
├── images/              # Generated dashboards
└── requirements.txt     # Dependencies
```

---

## Results

The analysis demonstrates that during the 2022 Federal Reserve rate hike cycle, the normal distribution assumption underlying Parametric VaR was inadequate. The observed exception rate of **1.67%** significantly differs from the expected **1%**, highlighting the importance of:

- Non-parametric methods (Historical Simulation)
- Complementary risk measures (Expected Shortfall)
- Stress testing frameworks

---

## License

MIT License

---

*For detailed development notes and technical decisions, see [DEVELOPMENT_NOTES.md](DEVELOPMENT_NOTES.md)*

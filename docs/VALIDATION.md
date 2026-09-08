# Local validation record — 2026-09-07

This record concerns the corrected local code and fully synthetic inputs. It is not a market-data backtest, approval record or production-readiness claim.

## Environment and commands

- Python 3.14.5
- NumPy 2.4.2; pandas 3.0.1; SciPy 1.17.1; Matplotlib 3.10.8
- pytest 9.0.2

```bash
MPLBACKEND=Agg python3 -m pytest -v
MPLBACKEND=Agg python3 main.py --source synthetic --seed 20260907 --observations 1500 --window 252 --output-dir output/validation-20260907 --plot
```

Result: **49 tests passed**. The suite includes forecast-timing perturbations, missing/index validation, binomial boundary limits, an independent chi-square survival check using `erfc`, offline CLI reproducibility and output-preservation checks. CI is configured for Python 3.9 and 3.12; those environments were not run locally.

The synthetic series has 1,500 observations and 1,248 usable forecasts after 252 warm-up observations. Dates are artificial labels starting from 2000-01-03. Confidence is 99%; hypothesis-test significance is 5%.

| Model | Exceptions / usable observations | Exception rate | LR statistic | Asymptotic p-value | Coverage decision |
|---|---:|---:|---:|---:|---|
| Normal parametric | 23 / 1,248 | 1.842948718% | 7.172704500 | 0.007402110 | REJECT |
| Historical | 16 / 1,248 | 1.282051282% | 0.920801525 | 0.337264606 | DO_NOT_REJECT |

These are outcomes of one stated simulation and environment. Non-rejection is not model validation, and rejection alone does not identify a cause. No seed was selected to obtain a desired test decision.

The optional chart marks exceptions of the historical threshold. Full generated JSON, forecasts and chart are local ignored artifacts under `output/validation-20260907/`; they are not the checked-in legacy image.

## Preserved legacy assets

No download was executed. SHA-256 values of the existing assets were unchanged across the work:

- `data/sp500_historical.csv`: `c4f8ccecd9c57a97803409e8e9da3261da4ded613d49de380b54047f9a56189a`.
- `images/var_dashboard.png`: `bed1d0025eab4422b17825934f6e7db68b6d22c085335aa8ff40f7bc03522804`.

The tests and this simulation do not verify the source vintage or numerical conclusions of those legacy assets.

## Second review — 2026-09-08

A fresh clone and non-editable wheel installation were checked in a virtual environment with
no inherited system packages. Python 3.14.5, NumPy 2.5.3, pandas 3.0.5, SciPy 1.18.1,
Matplotlib 3.11.1 and pytest 9.1.1 were used. The installed module ran from outside the
checkout and reproduced the same exception counts and coverage conclusions above.

The review found that duplicate `Adj Close` headers were silently renamed by pandas, causing
the first asset's prices to be selected. A multi-ticker download could create that ambiguous
CSV itself. The reader now rejects duplicate headers before parsing. The downloader accepts
one ticker, checks returned ticker identity when a ticker level is present, rejects ambiguous
price columns, and validates price/index inputs before saving.

**59 tests passed** after the correction. New tests use invented CSVs and mocked download
responses; no provider was called. They cover duplicate core headers, multiple requested symbols,
wrong/multiple returned identities, repeated price fields and a valid single-symbol round trip.
The new `risk-var` entry point runs from the installed wheel. CI installs the package and executes
that command outside the checkout instead of testing only a source-file invocation.

Independent review also recomputed 351 Kupiec likelihood/p-value cases and 106 rolling quantile
windows. Those checks support the stated estimator and test implementation; they do not establish
real-market suitability. With discrete returns or many ties, strict exceptions can occur less
often than `1-confidence`; rejection of exact coverage is not automatically a quantile coding error.

The two legacy asset hashes above remain unchanged.

# VaR Forecasting and Backtesting Lab

An educational Python project for one-observation-ahead Value-at-Risk forecasts and unconditional-coverage diagnostics. The default example uses reproducible synthetic returns and works offline.

The project demonstrates how forecast timing, missing observations and statistical interpretation can change a risk conclusion. It is not a production risk engine, a regulatory capital implementation, or evidence of validated investment performance.

## Run offline

```bash
python -m pip install '.[test]'
python -m pytest -v
risk-var --source synthetic --seed 20260907 --observations 1500
```

The last command prints JSON for both models and writes no files. The synthetic series uses a Student-t distribution with 5 degrees of freedom, a fixed seed, a 0.0002 location and 0.01 standard-deviation scale. Its business-day dates are artificial labels, not a historical trading calendar. A fixed seed makes the demonstration reproducible within the recorded environment; it does not guarantee a statistical test will reject or fail to reject.

The installed `risk-var` command works outside the checkout; `python main.py` remains supported.

To save a new report, forecast table and chart:

```bash
MPLBACKEND=Agg python main.py --source synthetic --seed 20260907 --output-dir output/demo --plot
```

Generated results belong in the ignored `output/` directory. Existing output files are not overwritten; choose a new directory for a subsequent saved run. `--confidence`, `--significance` and `--window` set forecast confidence, hypothesis-test significance and estimation-window length independently.

## Optional local CSV

```bash
python main.py --source csv --csv-path data/sp500_historical.csv
```

This reads an existing CSV with unique headers, unique increasing `Date` values and positive `Adj Close` prices. Duplicate price columns are rejected before parsing can silently rename them. Returns are decimal simple returns. Missing prices are not filled, and internal missing-return rows remain in the time sequence.

The bundled CSV and `images/var_dashboard.png` are retained legacy assets. Their source vintage and the old chart's numerical claims have not been revalidated here. The old chart is not evidence for the corrected algorithm. The offline demo and tests do not download data or change either asset.

`download_data.py` is a separate, optional network tool. Importing it is safe; explicitly running it requires `yfinance`, saves to `output/downloaded_prices.csv` by default, and refuses to overwrite an existing file. It accepts exactly one ticker and checks any returned ticker column level before choosing prices. Neither the demo nor CI makes a download request; tests use synthetic mocked responses.

## Forecast definition and timing correction

The API returns a **lower-tail return threshold**, often negative, rather than a positive currency loss amount. For confidence `c`, the exception probability is `p = 1 - c`; an exception occurs only when `actual_return < threshold`. Equality is not counted as an exception.

For forecast observation `t`, both models use exactly the previous `w` indexed observations, `r[t-w]` through `r[t-1]`:

- Normal parametric threshold: `mean(history) + normal_ppf(1-c) * sample_std(history)`, using `ddof=1`.
- Historical threshold: the `1-c` sample quantile with linear interpolation.

The original implementation rolled over the unshifted return series. A threshold labelled `t` therefore used `r[t]`, the very outcome being evaluated. That leaks same-observation information into a purported forecast and can alter the exception count. The corrected implementation shifts returns by one observation **before** rolling. With 252 complete prior observations, the first forecast is for observation 253.

Indexes must be one-dimensional, unique, non-missing and increasing; callers must supply labels in chronological order. The code does not silently sort or deduplicate them. A missing value inside an estimation window suppresses that window's forecast. It does not fill the gap or compress time by dropping the missing return first.

This forward-looking comparison is consistent with the historical backtesting rationale of comparing risk estimates to subsequent outcomes. [BCBS, 1996 backtesting framework](https://www.bis.org/publ/bcbs22.pdf) is cited for that methodological background; it is a superseded document, not a claim of current regulatory compliance.

## Kupiec unconditional-coverage test

The test aligns forecasts and actual returns **by label** and uses only pairs where both values are present. It reports unmatched labels, dropped missing pairs and the effective sample size. Infinities and ambiguous indexes are rejected. An empty effective sample raises an error instead of returning a reassuring result.

For `N` usable pairs, `x` exceptions and `p = 1-c`, define `q = x/N`:

```text
log L0 = x log(p) + (N-x) log(1-p)
log L1 = x log(q) + (N-x) log(1-q)
LR     = 2 (log L1 - log L0)
p-value = P(chi-square with 1 degree of freedom >= LR)
```

The implementation uses the limit `0 log(0) = 0` to handle both zero exceptions and exceptions on every observation. This is numerical boundary handling, not evidence that the chi-square approximation is exact in those cases. [SciPy's `xlogy` documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.special.xlogy.html) describes the stable primitive used.

Results are `REJECT` or `DO_NOT_REJECT` at the selected significance level. **Non-rejection does not establish that a model is valid.** The p-value is not the probability that the model is correct. Kupiec POF assesses the aggregate exception frequency; it does not test exception clustering, loss severity, calibration stability or the adequacy of the underlying economic assumptions. Rejection also does not identify fat tails as the cause. Rare exceptions and small samples limit power and the accuracy of asymptotic inference. [Kupiec's original 1995 paper, Federal Reserve archive](https://fedinprint.org/item/fedgfe/34596/original) discusses the limitations of verifying tail-risk estimates.

## What the tests establish

- Same-day shocks and appended future observations cannot change an existing forecast.
- The first forecast and an independently calculated short-window threshold have the intended time alignment.
- Missing-history windows, mismatched labels and empty backtests are handled explicitly.
- Zero/all-exception likelihood limits and chi-square p-values match an independent closed-form check.
- Invalid probabilities, windows, indexes and nonnumeric/infinite values are rejected.
- Rearranging exceptions into clusters leaves POF unchanged, demonstrating its coverage-only scope.
- The synthetic CLI is deterministic, writes only when requested, and preserves existing output files.
- Importing the optional downloader never invokes the network path.

Passing these tests supports implementation correctness for the tested cases. It does not establish market-model adequacy. See [development notes](DEVELOPMENT_NOTES.md) for scope and residual limitations, and [validation record](docs/VALIDATION.md) for the recorded local run.

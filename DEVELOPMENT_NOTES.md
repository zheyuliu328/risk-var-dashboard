# Development notes

## Scope of the correction

The earlier implementation calculated same-observation rolling thresholds, while its documentation described forecasts. The corrected estimator uses `returns.shift(1)` before forming either rolling window. A missing return remains a missing observation and is never filled or removed to make the estimation history appear complete.

The coverage test now aligns on observation labels, excludes only incomplete pairs and reports those exclusions. It rejects ambiguous indexes and invalid numerical inputs. The binomial log-likelihood uses `xlogy`, so both zero-exception and all-exception boundaries are finite for valid probabilities. A p-value and a hypothesis-test decision replace the old model-level PASS/FAIL label.

The plotting labels now use the requested confidence and actual input source. A rejected coverage test no longer generates an unsupported fat-tail diagnosis. The default CLI is offline and synthetic; the downloader is explicitly optional and has no import-time side effects. Existing CSVs and charts are not overwritten.

## Statistical interpretation

The null hypothesis concerns unconditional exception probability. Its large-sample reference distribution is chi-square with one degree of freedom. The reference distribution is approximate, particularly for small samples or very rare exceptions. A high p-value can reflect insufficient evidence or low test power; it is not proof of model validity. A low p-value requires investigation but does not, by itself, identify a distributional cause.

The returned `actual_only_labels`, `forecast_only_labels` and `missing_pairs_dropped` make sample selection visible. Warm-up observations naturally lack forecasts. Other gaps may be informative; excluding missing pairs does not establish that the remaining sample is representative.

See [Kupiec (1995)](https://fedinprint.org/item/fedgfe/34596/original) for the original coverage-test discussion and [BCBS (1996)](https://www.bis.org/publ/bcbs22.pdf) for historical backtesting context. The latter is superseded and is not used here as a current compliance specification.

## Limitations and possible later work

- A fixed rolling window and a normal model are simple educational specifications. Historical quantiles also have sampling error and depend on the chosen interpolation rule.
- The lab forecasts a scalar return series, not a multi-asset portfolio with positions, currencies, nonlinear pricing and changing exposures.
- POF ignores the order and size of exceptions. Independence or conditional-coverage tests, expected-shortfall validation, scenario analysis and sensitivity to window choices would require additional implementation and review.
- Synthetic Student-t returns demonstrate a controlled data-generating process. They do not reproduce actual volatility clustering, stress histories or transaction costs.
- Calendar conventions, stale-market-data controls and external data-source provenance have not been validated.
- Previous prose claiming implemented retry/fallback logic, production readiness or confirmed fixed performance figures is superseded by this description of the actual code.

The checked-in legacy CSV and image are unchanged. New local experiment results belong under ignored `output/`; concise evidence can be recorded under `docs/` with the exact command, seed and environment.

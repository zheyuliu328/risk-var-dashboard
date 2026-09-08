"""One-observation-ahead VaR forecasts and unconditional-coverage diagnostics."""

import argparse
import csv
import json
from numbers import Integral, Real
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import xlogy
from scipy.stats import chi2, norm


def _probability(value, name):
    if (
        isinstance(value, (bool, np.bool_))
        or not isinstance(value, Real)
        or not np.isfinite(value)
        or not 0 < value < 1
        or not 0 < 1.0 - value < 1
    ):
        raise ValueError(f"{name} must be a finite probability strictly between 0 and 1")
    return float(value)


def _series(values, name):
    """Keep missing observations as gaps; reject ambiguous ordering and infinity."""
    if not isinstance(values, pd.Series):
        raise TypeError(f"{name} must be a pandas Series with ordered observation labels")
    index = values.index
    if isinstance(index, pd.MultiIndex):
        raise ValueError(f"{name} must have a one-dimensional index")
    if index.hasnans or not index.is_unique or not index.is_monotonic_increasing:
        raise ValueError(f"{name} index must be unique, non-missing and increasing")
    if (
        not pd.api.types.is_numeric_dtype(values.dtype)
        or pd.api.types.is_bool_dtype(values.dtype)
        or pd.api.types.is_complex_dtype(values.dtype)
    ):
        raise TypeError(f"{name} must contain real numeric returns, not strings or booleans")
    numeric = values.astype(float)
    if np.isinf(numeric.to_numpy()).any():
        raise ValueError(f"{name} must not contain infinite values")
    return numeric


def get_data(filepath="data/sp500_historical.csv"):
    """Read a local CSV only. Missing prices are not forward-filled."""
    with open(filepath, encoding="utf-8-sig", newline="") as source:
        header = next(csv.reader(source), [])
        if len(header) != len(set(header)):
            raise ValueError("CSV headers must be unique; duplicated price columns are ambiguous")
        if "Date" not in header or "Adj Close" not in header:
            raise ValueError("CSV must contain exactly one 'Date' and one 'Adj Close' column")
        source.seek(0)
        data = pd.read_csv(source, index_col="Date", parse_dates=True)
    if not isinstance(data.index, pd.DatetimeIndex):
        raise ValueError("CSV Date values must parse as dates")
    if "Adj Close" not in data:
        raise ValueError("CSV must contain an 'Adj Close' column")
    prices = _series(data["Adj Close"], "prices")
    if (prices.dropna() <= 0).any():
        raise ValueError("Non-missing prices must be positive")
    # Remove only the structural first return; preserve gaps inside the series.
    return prices.pct_change(fill_method=None).iloc[1:].rename("returns")


def calculate_var(returns, confidence_level=0.99, window=252):
    """Return lower-tail return thresholds, with forecast t using t-window..t-1.

    A complete window of non-missing prior observations is required. The sample
    standard deviation uses ddof=1; historical quantiles use linear interpolation.
    Returned labels are forecast/realization labels, not estimation-end labels.
    """
    confidence_level = _probability(confidence_level, "confidence_level")
    if isinstance(window, (bool, np.bool_)) or not isinstance(window, Integral) or window < 2:
        raise ValueError("window must be an integer of at least 2")
    returns = _series(returns, "returns")
    alpha = 1.0 - confidence_level
    history = returns.shift(1).rolling(window=int(window), min_periods=int(window))
    parametric = history.mean() + norm.ppf(alpha) * history.std(ddof=1)
    historical = history.quantile(alpha, interpolation="linear")
    return parametric.dropna().rename("parametric_var"), historical.dropna().rename("historical_var")


def kupiec_pof_test(actual_returns, var_forecasts, confidence_level=0.99, significance_level=0.05):
    """Test unconditional coverage on finite, label-aligned observations.

    An exception is strictly actual_return < lower-tail return threshold. Missing
    pairs and unmatched labels are excluded and counted in the returned report.
    The chi-square p-value is asymptotic, including at zero/all exceptions.
    """
    confidence_level = _probability(confidence_level, "confidence_level")
    significance_level = _probability(significance_level, "significance_level")
    actual = _series(actual_returns, "actual_returns")
    forecast = _series(var_forecasts, "var_forecasts")
    common = actual.index.intersection(forecast.index, sort=False)
    pairs = pd.DataFrame({"actual": actual.reindex(common), "forecast": forecast.reindex(common)})
    complete = pairs.dropna()
    if complete.empty:
        raise ValueError("Kupiec test requires at least one finite, label-aligned observation")
    exceptions = (complete["actual"] < complete["forecast"]).rename("exception")
    n = int(len(exceptions))
    x = int(exceptions.sum())
    probability = 1.0 - confidence_level
    observed = x / n
    null_log_likelihood = xlogy(x, probability) + xlogy(n - x, confidence_level)
    fitted_log_likelihood = xlogy(x, observed) + xlogy(n - x, 1.0 - observed)
    # xlogy(0, 0) = 0 gives the correct binomial boundary limits.
    lr = max(0.0, float(2.0 * (fitted_log_likelihood - null_log_likelihood)))
    p_value = float(chi2.sf(lr, df=1))
    reject = p_value < significance_level
    stats = {
        "N": n,
        "x": x,
        "failure_rate": observed,
        "expected_failure_rate": probability,
        "expected_exceptions": n * probability,
        "LR_stat": lr,
        "p_value": p_value,
        "critical_value": float(chi2.isf(significance_level, df=1)),
        "confidence_level": confidence_level,
        "significance_level": significance_level,
        "reject_null": reject,
        "result": "REJECT" if reject else "DO_NOT_REJECT",
        "actual_observations": len(actual),
        "forecast_observations": len(forecast),
        "common_labels": len(common),
        "missing_pairs_dropped": len(pairs) - n,
        "actual_only_labels": len(actual) - len(common),
        "forecast_only_labels": len(forecast) - len(common),
        "sample_start": str(complete.index[0]),
        "sample_end": str(complete.index[-1]),
        "interpretation": (
            "Reject unconditional coverage at the selected significance level. "
            if reject else
            "Do not reject unconditional coverage at the selected significance level. "
        ) + (
            "This is not model approval or evidence of independence, tail-loss accuracy, "
            "or a particular cause such as fat tails. The p-value is asymptotic; "
            "rare exceptions and small samples limit inference."
        ),
    }
    return exceptions, stats


def synthetic_returns(observations=1500, seed=20260907):
    """Generate reproducible Student-t scenarios, not historical market data."""
    if isinstance(observations, bool) or not isinstance(observations, Integral) or observations < 1:
        raise ValueError("observations must be a positive integer")
    rng = np.random.default_rng(seed)
    returns = 0.0002 + 0.01 * np.sqrt(3.0 / 5.0) * rng.standard_t(5, size=int(observations))
    dates = pd.bdate_range("2000-01-03", periods=int(observations), name="Date")
    return pd.Series(returns, index=dates, name="returns")


def plot_results(returns, param_var, hist_var, exceptions, test_stats,
                 save_path="output/var_dashboard.png", source_label="Synthetic returns"):
    """Save a new chart; exception markers refer to the historical forecast."""
    import matplotlib.pyplot as plt

    path = Path(save_path)
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing chart: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    confidence = test_stats["confidence_level"]
    with plt.style.context("dark_background"):
        fig, ax = plt.subplots(figsize=(14, 7))
        ax.plot(returns.index, returns, label="Observed returns", color="#8b949e", alpha=0.65, linewidth=0.7)
        ax.plot(param_var.index, param_var, label=f"Normal VaR threshold ({confidence:.1%})", color="#f85149")
        ax.plot(hist_var.index, hist_var, label=f"Historical VaR threshold ({confidence:.1%})", color="#58a6ff")
        breach_dates = exceptions.index[exceptions.to_numpy()]
        ax.scatter(breach_dates, returns.reindex(breach_dates), color="#ffd700", marker="x",
                   label="Historical VaR exceptions", zorder=5)
        ax.set(title=f"One-observation-ahead VaR | {source_label}", xlabel="Observation date", ylabel="Decimal return")
        ax.grid(alpha=0.2)
        ax.legend(loc="lower left")
        summary = (
            f"Historical coverage: {test_stats['result']} | p={test_stats['p_value']:.4g} | "
            f"exceptions={test_stats['x']}/{test_stats['N']} "
            f"(expected rate {test_stats['expected_failure_rate']:.2%})\n"
            "Unconditional coverage only; non-rejection is not model validation."
        )
        ax.text(0.01, 0.99, summary, transform=ax.transAxes, va="top", fontsize=9)
        fig.tight_layout()
        try:
            fig.savefig(path, dpi=150, bbox_inches="tight")
        finally:
            plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("synthetic", "csv"), default="synthetic")
    parser.add_argument("--csv-path", type=Path, default=Path("data/sp500_historical.csv"))
    parser.add_argument("--observations", type=int, default=1500)
    parser.add_argument("--seed", type=int, default=20260907)
    parser.add_argument("--window", type=int, default=252)
    parser.add_argument("--confidence", type=float, default=0.99)
    parser.add_argument("--significance", type=float, default=0.05)
    parser.add_argument("--output-dir", type=Path, help="Optional new results directory, e.g. output/demo")
    parser.add_argument("--plot", action="store_true", help="Also save a chart; requires --output-dir")
    args = parser.parse_args(argv)
    if args.plot and args.output_dir is None:
        parser.error("--plot requires --output-dir")
    try:
        returns = synthetic_returns(args.observations, args.seed) if args.source == "synthetic" else get_data(args.csv_path)
        parametric, historical = calculate_var(returns, args.confidence, args.window)
        _, param_stats = kupiec_pof_test(returns, parametric, args.confidence, args.significance)
        exceptions, hist_stats = kupiec_pof_test(returns, historical, args.confidence, args.significance)
        report = {
            "source": "synthetic Student-t(df=5) decimal returns" if args.source == "synthetic" else "local CSV",
            "seed": args.seed if args.source == "synthetic" else None,
            "input_path": str(args.csv_path) if args.source == "csv" else None,
            "window": args.window,
            "forecast_timing": "forecast t uses only the previous window observations through t-1",
            "parametric": param_stats,
            "historical": hist_stats,
        }
        if args.output_dir is not None:
            names = ["summary.json", "forecasts.csv"] + (["var_dashboard.png"] if args.plot else [])
            for name in names:
                if (args.output_dir / name).exists():
                    raise FileExistsError(f"Refusing to overwrite {args.output_dir / name}; use a new output directory")
            args.output_dir.mkdir(parents=True, exist_ok=True)
            with (args.output_dir / "summary.json").open("x") as handle:
                json.dump(report, handle, indent=2, allow_nan=False)
                handle.write("\n")
            with (args.output_dir / "forecasts.csv").open("x") as handle:
                pd.concat([returns, parametric, historical], axis=1).to_csv(handle)
            if args.plot:
                label = "Synthetic Student-t scenarios" if args.source == "synthetic" else "Local CSV (user-supplied provenance)"
                plot_results(returns, parametric, historical, exceptions, hist_stats,
                             args.output_dir / "var_dashboard.png", label)
        print(json.dumps(report, indent=2, allow_nan=False))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

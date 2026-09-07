"""Regression tests for forecast timing, coverage inference and offline execution."""

import builtins
import json
import math
from pathlib import Path
import runpy
import warnings

import numpy as np
import pandas as pd
import pytest
from scipy.stats import norm

import main


def series(values):
    return pd.Series(values, index=pd.date_range("2001-01-01", periods=len(values)), dtype=float)


def test_first_forecast_uses_only_three_previous_returns():
    values = series([0.01, -0.02, 0.03, -0.80, 0.07])
    parametric, historical = main.calculate_var(values, confidence_level=0.95, window=3)
    assert parametric.index[0] == values.index[3]
    assert historical.index[0] == values.index[3]
    prior = np.array([0.01, -0.02, 0.03])
    expected_normal = prior.mean() + norm.ppf(0.05) * prior.std(ddof=1)
    assert parametric.iloc[0] == pytest.approx(expected_normal)
    assert historical.iloc[0] == pytest.approx(-0.017)


def test_today_and_future_cannot_change_todays_forecast():
    values = series([0.01, -0.02, 0.03, 0.04, -0.05, 0.06, 0.02, 0.01])
    changed = values.copy()
    changed.iloc[4:] = [-0.80, 0.50, -0.60, 0.40]
    original_forecasts = main.calculate_var(values, window=3)
    changed_forecasts = main.calculate_var(changed, window=3)
    for original, altered in zip(original_forecasts, changed_forecasts):
        pd.testing.assert_series_equal(original.loc[:values.index[4]], altered.loc[:values.index[4]])
        assert original.loc[values.index[5]] != altered.loc[values.index[5]]


def test_appending_future_observations_preserves_existing_forecasts():
    values = main.synthetic_returns(50, seed=17)
    for shorter, longer in zip(main.calculate_var(values.iloc[:30], window=5),
                               main.calculate_var(values, window=5)):
        pd.testing.assert_series_equal(shorter, longer.loc[shorter.index])


def test_missing_history_suppresses_forecasts_without_compressing_time():
    values = series([0.01, 0.02, np.nan, 0.03, 0.04, 0.05])
    parametric, historical = main.calculate_var(values, window=2)
    expected_index = values.index[[2, 5]]
    pd.testing.assert_index_equal(parametric.index, expected_index)
    pd.testing.assert_index_equal(historical.index, expected_index)


def test_insufficient_history_and_constant_history():
    values = series([0.02] * 5)
    assert all(item.empty for item in main.calculate_var(values, window=5))
    for forecasts in main.calculate_var(values, window=2):
        np.testing.assert_allclose(forecasts, 0.02)


@pytest.mark.parametrize("confidence", [0, 1, -0.1, 1.1, np.nan, np.inf, True, "0.99", 1e-30])
def test_invalid_confidence_rejected_by_forecasting_and_backtest(confidence):
    values = series([0.01, 0.02, -0.03])
    with pytest.raises(ValueError, match="confidence_level"):
        main.calculate_var(values, confidence_level=confidence, window=2)
    with pytest.raises(ValueError, match="confidence_level"):
        main.kupiec_pof_test(values, values, confidence_level=confidence)


@pytest.mark.parametrize("window", [0, 1, -1, 2.5, True, "2"])
def test_invalid_window_rejected(window):
    with pytest.raises(ValueError, match="window"):
        main.calculate_var(series([0.01] * 5), window=window)


@pytest.mark.parametrize("index", [
    pd.Index([0, 0, 1]),
    pd.Index([2, 1, 0]),
    pd.DatetimeIndex(["2001-01-01", None, "2001-01-03"]),
    pd.MultiIndex.from_tuples([(0, 1), (0, 2), (1, 1)]),
])
def test_ambiguous_indexes_rejected(index):
    invalid = pd.Series([0.01, 0.02, -0.03], index=index)
    valid = series([0.01, 0.02, -0.03])
    with pytest.raises(ValueError, match="index"):
        main.calculate_var(invalid, window=2)
    with pytest.raises(ValueError, match="index"):
        main.kupiec_pof_test(invalid, valid)
    with pytest.raises(ValueError, match="index"):
        main.kupiec_pof_test(valid, invalid)


@pytest.mark.parametrize("invalid", [
    [0.01, 0.02],
    pd.Series(["0.01", "0.02"]),
    pd.Series([True, False]),
    pd.Series([1 + 1j, 2 + 0j]),
    pd.Series([np.inf, 0.02]),
])
def test_invalid_numeric_input_is_not_silently_coerced(invalid):
    with pytest.raises((TypeError, ValueError)):
        main.calculate_var(invalid, window=2)
    with pytest.raises((TypeError, ValueError)):
        main.kupiec_pof_test(series([0.01, 0.02]), invalid)


def test_backtest_aligns_labels_and_reports_exclusions():
    dates = pd.date_range("2001-01-01", periods=6)
    actual = pd.Series([0.0, -0.02, np.nan, 0.01, -0.10], index=dates[:5])
    forecast = pd.Series([-0.01, -0.01, np.nan, -0.01], index=dates[[1, 2, 3, 5]])
    exceptions, stats = main.kupiec_pof_test(actual, forecast)
    assert exceptions.index.tolist() == [dates[1]]
    assert exceptions.tolist() == [True]
    assert stats["N"] == 1
    assert stats["x"] == 1
    assert stats["common_labels"] == 3
    assert stats["missing_pairs_dropped"] == 2
    assert stats["actual_only_labels"] == 2
    assert stats["forecast_only_labels"] == 1


@pytest.mark.parametrize("actual, forecast", [
    (pd.Series(dtype=float), pd.Series(dtype=float)),
    (pd.Series([0.0], index=[0]), pd.Series([-0.1], index=[1])),
    (series([np.nan, 0.0]), series([-0.1, np.nan])),
])
def test_empty_effective_sample_raises_instead_of_passing(actual, forecast):
    with pytest.raises(ValueError, match="at least one finite, label-aligned"):
        main.kupiec_pof_test(actual, forecast)


@pytest.mark.parametrize("all_exceptions", [False, True])
def test_zero_and_all_exception_limits_and_p_values(all_exceptions):
    n = 20
    actual = series([-0.20 if all_exceptions else 0.02] * n)
    forecast = series([-0.05] * n)
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        _, stats = main.kupiec_pof_test(actual, forecast, confidence_level=0.95)
    expected_lr = -2 * n * math.log(0.05 if all_exceptions else 0.95)
    assert stats["LR_stat"] == pytest.approx(expected_lr)
    # df=1 chi-square survival has an independent closed form.
    assert stats["p_value"] == pytest.approx(math.erfc(math.sqrt(expected_lr / 2)), rel=1e-12)
    assert math.isfinite(stats["LR_stat"])
    assert 0 <= stats["p_value"] <= 1


def test_equality_is_not_an_exception_and_non_rejection_is_not_pass():
    forecast = series([-0.02] * 100)
    actual = forecast.copy()
    actual.iloc[3] = -0.03
    exceptions, stats = main.kupiec_pof_test(actual, forecast)
    assert exceptions.sum() == 1
    assert stats["LR_stat"] == pytest.approx(0, abs=1e-12)
    assert stats["p_value"] == pytest.approx(1, abs=1e-6)
    assert stats["result"] == "DO_NOT_REJECT"
    assert stats["reject_null"] is False


def test_significance_level_controls_the_decision():
    actual, forecast = series([0.02] * 20), series([-0.05] * 20)
    _, strict = main.kupiec_pof_test(actual, forecast, 0.95, significance_level=0.05)
    _, lenient = main.kupiec_pof_test(actual, forecast, 0.95, significance_level=0.20)
    assert strict["result"] == "DO_NOT_REJECT"
    assert lenient["result"] == "REJECT"
    assert strict["p_value"] == lenient["p_value"]


@pytest.mark.parametrize("significance", [0, 1, np.nan, np.inf, True])
def test_invalid_significance_rejected(significance):
    with pytest.raises(ValueError, match="significance_level"):
        main.kupiec_pof_test(series([0.0]), series([-0.1]), significance_level=significance)


def test_pof_does_not_detect_exception_clustering():
    clustered = series([0.01] * 100)
    dispersed = clustered.copy()
    clustered.iloc[:10] = -0.10
    dispersed.iloc[::10] = -0.10
    forecast = series([-0.05] * 100)
    _, first = main.kupiec_pof_test(clustered, forecast, 0.90)
    _, second = main.kupiec_pof_test(dispersed, forecast, 0.90)
    assert first["x"] == second["x"] == 10
    assert first["p_value"] == second["p_value"]


def test_csv_reader_does_not_fill_or_remove_internal_missing_returns(tmp_path):
    path = tmp_path / "prices.csv"
    path.write_text("Date,Adj Close\n2001-01-01,100\n2001-01-02,110\n2001-01-03,\n2001-01-04,121\n2001-01-05,133.1\n")
    returns = main.get_data(path)
    assert len(returns) == 4
    np.testing.assert_allclose(returns.to_numpy(), [0.1, np.nan, np.nan, 0.1], equal_nan=True)


def test_downloader_import_does_not_import_network_client(monkeypatch):
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "yfinance":
            raise AssertionError("Importing the module must not start the download path")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    namespace = runpy.run_path(str(Path(main.__file__).with_name("download_data.py")))
    assert callable(namespace["main"])


def test_downloader_refuses_existing_file_before_network_access(tmp_path):
    from download_data import main as download_main

    path = tmp_path / "existing.csv"
    path.write_text("preserve this data\n")
    with pytest.raises(SystemExit) as exc:
        download_main(["--output", str(path)])
    assert exc.value.code == 2
    assert path.read_text() == "preserve this data\n"


def test_offline_cli_is_reproducible_and_does_not_read_local_data(monkeypatch, capsys, tmp_path):
    def forbidden_read(*args, **kwargs):
        raise AssertionError("Synthetic mode must not read market data")

    monkeypatch.setattr(main, "get_data", forbidden_read)
    monkeypatch.chdir(tmp_path)
    args = ["--observations", "80", "--window", "20", "--seed", "42"]
    assert main.main(args) == 0
    first = json.loads(capsys.readouterr().out)
    assert main.main(args) == 0
    second = json.loads(capsys.readouterr().out)
    assert first == second
    assert first["historical"]["N"] == 60
    assert first["parametric"]["N"] == 60
    assert first["seed"] == 42
    assert "synthetic" in first["source"]
    assert list(tmp_path.iterdir()) == []


def test_cli_writes_new_outputs_and_refuses_overwriting_them(tmp_path, capsys):
    output = tmp_path / "run"
    args = ["--observations", "40", "--window", "10", "--output-dir", str(output)]
    main.main(args)
    capsys.readouterr()
    before = {path.name: path.read_bytes() for path in output.iterdir()}
    assert set(before) == {"summary.json", "forecasts.csv"}
    with pytest.raises(SystemExit) as exc:
        main.main(args)
    assert exc.value.code == 2
    assert before == {path.name: path.read_bytes() for path in output.iterdir()}


def test_chart_uses_aligned_exception_dates_and_preserves_existing_chart(tmp_path):
    values = series([0.01, -0.02, np.nan, 0.03, 0.04, -0.20, 0.01, 0.02])
    parametric, historical = main.calculate_var(values, window=2, confidence_level=0.90)
    exceptions, stats = main.kupiec_pof_test(values, historical, confidence_level=0.90)
    path = tmp_path / "chart.png"
    main.plot_results(values, parametric, historical, exceptions, stats, path)
    before = path.read_bytes()
    assert before.startswith(b"\x89PNG\r\n\x1a\n")
    with pytest.raises(FileExistsError):
        main.plot_results(values, parametric, historical, exceptions, stats, path)
    assert path.read_bytes() == before

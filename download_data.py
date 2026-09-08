"""Optional Yahoo Finance downloader. Importing this module never downloads data."""

import argparse
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ticker", default="SPY")
    parser.add_argument("--start", default="2020-01-01")
    parser.add_argument("--end", default="2026-01-01")
    parser.add_argument("--output", type=Path, default=Path("output/downloaded_prices.csv"))
    args = parser.parse_args(argv)
    args.ticker = args.ticker.strip()
    if not args.ticker or any(c.isspace() or c == "," for c in args.ticker):
        parser.error("--ticker requires exactly one symbol")
    if args.output.exists():
        parser.error(f"Refusing to overwrite existing data: {args.output}")

    # Network access is an explicit opt-in by running this script, not importing it.
    import pandas as pd
    import yfinance as yf

    data = yf.download(args.ticker, start=args.start, end=args.end, auto_adjust=True, progress=False)
    if data.empty:
        raise ValueError("Downloaded data is empty")
    if isinstance(data.columns, pd.MultiIndex):
        if data.columns.nlevels != 2:
            raise ValueError("Expected a two-level Price/Ticker column index")
        tickers = data.columns.get_level_values(1).unique()
        if len(tickers) != 1 or str(tickers[0]).upper() != args.ticker.upper():
            raise ValueError("Downloaded ticker identity does not match the single requested symbol")
        data = data.xs(tickers[0], axis=1, level=1)
    if not data.columns.is_unique:
        raise ValueError("Downloaded price columns are ambiguous")
    if "Close" in data:
        data = data[["Close"]].rename(columns={"Close": "Adj Close"})
    elif "Adj Close" in data:
        data = data[["Adj Close"]]
    else:
        raise ValueError("No valid price column found")
    from main import _series

    if not isinstance(data.index, pd.DatetimeIndex):
        raise ValueError("Downloaded observations require a Date index")
    prices = _series(data["Adj Close"], "downloaded prices")
    if prices.dropna().empty or (prices.dropna() <= 0).any():
        raise ValueError("Downloaded non-missing prices must be positive and nonempty")
    data.index.name = "Date"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as handle:
        data.to_csv(handle)
    print(f"Saved {len(data)} adjusted observations for {args.ticker} to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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
    if args.output.exists():
        parser.error(f"Refusing to overwrite existing data: {args.output}")

    # Network access is an explicit opt-in by running this script, not importing it.
    import pandas as pd
    import yfinance as yf

    data = yf.download(args.ticker, start=args.start, end=args.end, auto_adjust=True, progress=False)
    if data.empty:
        raise ValueError("Downloaded data is empty")
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(1)
    if "Close" in data:
        data = data[["Close"]].rename(columns={"Close": "Adj Close"})
    elif "Adj Close" in data:
        data = data[["Adj Close"]]
    else:
        raise ValueError("No valid price column found")
    data.index.name = "Date"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as handle:
        data.to_csv(handle)
    print(f"Saved {len(data)} adjusted observations for {args.ticker} to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

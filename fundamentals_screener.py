def _yoy_growth_from_financials(ticker: yf.Ticker):
    """Returns (revenue_growth_pct, profit_growth_pct, latest_revenue, latest_profit)
    using the latest two annual financials. Absolute figures are in raw rupees."""
    try:
        fin = ticker.financials  # annual, most recent columns first
        if fin is None or fin.empty or fin.shape[1] < 2:
            return None, None, None, None
        revenue_row = fin.loc["Total Revenue"] if "Total Revenue" in fin.index else None
        profit_row = fin.loc["Net Income"] if "Net Income" in fin.index else None
        rev_growth = _pct_growth(revenue_row.iloc[0], revenue_row.iloc[1]) if revenue_row is not None else None
        profit_growth = _pct_growth(profit_row.iloc[0], profit_row.iloc[1]) if profit_row is not None else None
        latest_revenue = float(revenue_row.iloc[0]) if revenue_row is not None else None
        latest_profit = float(profit_row.iloc[0]) if profit_row is not None else None
        return rev_growth, profit_growth, latest_revenue, latest_profit
    except Exception:
        return None, None, None, None

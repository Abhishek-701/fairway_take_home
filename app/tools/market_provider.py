"""Market data provider abstraction.

The first provider is yfinance, but tools depend on this module so a licensed
provider can be swapped in without changing agent planning.
"""

from __future__ import annotations

from typing import Any


class MarketProvider:
    name = "abstract"

    def quote(self, ticker: str) -> dict[str, Any]:
        raise NotImplementedError

    def history(self, ticker: str, period: str) -> dict[str, Any]:
        raise NotImplementedError


class YFinanceProvider(MarketProvider):
    name = "yfinance"

    def quote(self, ticker: str) -> dict[str, Any]:
        import yfinance as yf

        return dict(yf.Ticker(ticker).fast_info)

    def history(self, ticker: str, period: str):
        import yfinance as yf

        return yf.Ticker(ticker).history(period=period)


def get_provider() -> MarketProvider:
    return YFinanceProvider()

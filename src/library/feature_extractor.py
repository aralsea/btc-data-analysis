from typing import Any

import numpy as np
import pandas as pd


# テクニカル指標を計算する
class MyTAStratSet:
    """
    Utils for pandas_ta.Strategy.
    See https://github.com/twopirllc/pandas-ta/blob/main/examples/PandasTA_Strategy_Examples.ipynb
    """

    def __init__(self) -> None:
        # エンバーゴ用
        self.max_length = 0
        # 不要な列を削除するためのリスト
        self.unnecessary_cols: list[str] = []

    def roc(self, length_list: list[int]) -> list[dict[str, Any]]:
        strats = []
        for length in length_list:
            s = [
                {"kind": "roc", "length": length, "close": "close", "prefix": "close"},
                # {"kind": "roc", "length": length, "close": "open", "prefix": "open"},
                # {"kind": "roc", "length": length, "close": "high", "prefix": "high"},
                # {"kind": "roc", "length": length, "close": "low", "prefix": "low"},
            ]
            self.max_length = max(self.max_length, length)
            strats += s
        return strats

    def sma_roc(self, length_list: list[int]) -> list[dict[str, Any]]:
        strats = []
        for length in length_list:
            s = [
                {"kind": "sma", "length": length, "close": "close", "prefix": "close"},
                {
                    "kind": "roc",
                    "length": length,
                    "close": f"close_SMA_{length}",
                    "prefix": f"close_SMA_{length}",
                },
            ]
            self.unnecessary_cols.append(f"close_SMA_{length}")
            self.max_length = max(self.max_length, length)
            strats += s
        return strats

    def return_sma(self, length_list: list[int]) -> list[dict[str, Any]]:
        strats = []
        for length in length_list:
            s = [
                {"kind": "roc", "length": 1, "close": "close", "prefix": "close"},
                {
                    "kind": "sma",
                    "length": length,
                    "close": f"close_ROC_{1}",
                    "prefix": f"close_ROC_{1}",
                },
            ]
            self.unnecessary_cols.append(f"close_ROC_{1}")
            self.max_length = max(self.max_length, length)
            strats += s
        return strats

    def basicstats(self, length_list: list[int]) -> list[dict[str, Any]]:
        strats = []
        for length in length_list:
            s = [
                {"kind": "zscore", "length": length},
                {"kind": "skew", "length": length},
                {"kind": "entropy", "length": length},
            ]
            self.max_length = max(self.max_length, length)
            strats += s
        return strats

    def vola(self, length_list: list[int]) -> list[dict[str, Any]]:
        strats = []
        for length in length_list:
            s = [
                {"kind": "stdev", "length": length},
                {"kind": "atr", "length": length},
                {"kind": "rvi", "length": length},
                {"kind": "massi", "fast": int(length / 2), "slow": length},
            ]
            self.max_length = max(self.max_length, length)
            strats += s
        return strats

    def momentum(self, length_list: list[int]) -> list[dict[str, Any]]:
        strats = []
        for length in length_list:
            s = [
                {"kind": "rsi", "length": length},
                {"kind": "macd", "fast": int(length / 2), "slow": length},
                {"kind": "psl", "length": length, "close": "close", "open_": "open"},
            ]
            self.max_length = max(self.max_length, length)
            strats += s
        return strats


THRESHOLD = 0.005


def add_sma(df: pd.DataFrame, length: int) -> pd.DataFrame:
    df[f"sma_{length}"] = df["close"].rolling(length).mean()
    return df


def add_hv(df: pd.DataFrame, length: int) -> pd.DataFrame:
    df[f"hv_{length}"] = (
        np.log(df["return"].astype(float) + 1.0)
        .rolling(window=length, min_periods=1)
        .std()
    )
    return df


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = add_sma(df, 10)  # FIXME pandas taを使う
    df = add_sma(df, 20)
    df = add_sma(df, 50)
    df["return"] = df["close"].pct_change().shift(-1)
    df = add_hv(df, 10)
    df["mask"] = df["hv_10"].apply(lambda x: 1 if abs(x) > THRESHOLD else 0)
    return df

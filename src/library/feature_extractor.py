import pandas as pd


def add_sma(df: pd.DataFrame, length: int) -> pd.DataFrame:
    df[f"sma_{length}"] = df["close"].rolling(length).mean()
    return df

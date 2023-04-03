import datetime as dt
import os
from typing import List

import pandas as pd
import requests


def get_data(periods: int, before: dt.datetime, after: dt.datetime) -> List[list]:
    """cryptowatchからデータを取得する.

    Args:
        periods (int): 足を指定. Ex. 15分足: 900, 日足: 86400
        before (dt.datetime): before以前のデータを取得.
        after (dt.datetime): after以降のデータを取得.

    Returns:
        List[list]: サイズ(7, min(length, 6000))のリスト.
            data[i] = [unixtime, o, h, l, c, volume, quotevolume]
            API docs: https://docs.cryptowat.ch/rest-api/markets/ohlc
    """
    # 端っこの処理について:
    # # 例えばperiods=900(15分足), beforeがちょうど17:00:00だった場合, 16:45~17:00のデータが入る.
    # # afterについて, afterがちょうど16:30:00だった場合, 16:15~16:30のデータが入る.
    # UNIXに直す必要があり, timestamp()メソッドを使っている.
    response = requests.get(
        "https://api.cryptowat.ch/markets/bitflyer/btcjpy/ohlc?"
        + f"periods={periods}"
        + f"&before={int(before.timestamp())}"
        + "&after={int(after.timestamp())}"
    )
    response_ = response.json()

    # response = {"result": {"900": [[...], [...], ]}}
    data = response_["result"][f"{periods}"]
    return data


def round_down_dt_by_15min(t: dt.datetime) -> dt.datetime:
    """datetimeを15分で丸める.
    Ex: 17:13 -> 17:00, 16:53 -> 16:45
    Args:
        t (dt.datetime): 丸めたいdatetime.
    Returns:
        dt.datetime: 丸められた結果.
    """
    return t.replace(minute=t.minute - t.minute % 15, second=0, microsecond=0)


COLUMNS = [
    "CloseTime",
    "OpenPrice",
    "HighPrice",
    "LowPrice",
    "ClosePrice",
    "Volume",
    "QuoteVolume",
]


def get_new_data(periods: int, length: int) -> None:
    """現在から遡ってlength件分のデータを保存する.

    Args:
        periods (int): 足を指定. Ex. 15分足: 900, 日足: 86400
        length (int): データの取得件数, <=6000 (一度に6000件までしか取得できない,
        6000より大きい件数を返すよう指定してもAPIからは6000件しか返ってこない)

    """
    save_path = f"btf_periods{periods}.csv"
    # save_pathが既に存在している場合, 何もしない
    if os.path.exists(save_path):
        print("File already exists.")
        return None

    # データ取得期間を指定
    before = dt.datetime.now()
    after = before - dt.timedelta(seconds=periods * length)

    # データ取得
    data = get_data(periods, before, after)
    print(
        f"Data from {dt.datetime.fromtimestamp(data[0][0])} to "
        + "{dt.datetime.fromtimestamp(data[-1][0])} are saved"
    )

    # dataframeにして保存
    df = pd.DataFrame(data, columns=COLUMNS)
    df.to_csv(save_path, index=False)


def add_data(periods: int) -> None:
    """csvファイルに最新のデータを追加する.

    Args:
        periods (int): Ex. 15分足: 900, 日足: 86400

    """
    save_path = f"btf_periods{periods}.csv"
    old_df = pd.read_csv(save_path)
    # csvファイル上の最新の時刻(+periods)から現時点までのデータを取得
    before = dt.datetime.now()
    after = dt.datetime.fromtimestamp(old_df["CloseTime"].values[-1]) + dt.timedelta(
        seconds=periods
    )
    print(before)
    print(after)

    # データ取得
    data = get_data(periods, before, after)

    print(
        f"Data from {dt.datetime.fromtimestamp(data[0][0])} to"
        + "{dt.datetime.fromtimestamp(data[-1][0])} are saved"
    )

    # 既存のdataと結合して保存
    tmp_df = pd.DataFrame(data, columns=COLUMNS)
    new_df = pd.concat([old_df, tmp_df])
    new_df.to_csv(save_path, index=False)


if __name__ == "__main__":
    periods = 900
    length = 6000
    # get_new_data(periods=900, length=6000)
    add_data(periods=900)

import datetime
from typing import Any, NamedTuple, Optional, Union

import pandas as pd

INITIAL_CASH = 1000000  # 100万円


class Tick(NamedTuple):
    Index: pd.Timestamp
    open: float
    high: float
    low: float
    close: float
    volume: float


class BaseOrder:
    _id = 0

    def __init__(
        self,
        timestamp: pd.Timestamp,
        side: str,
        size: float,
    ) -> None:
        self.id = BaseOrder._id
        BaseOrder._id += 1
        self.timestamp = timestamp
        self.side = side
        self.size = size
        self.completion_time: Optional[pd.Timestamp] = None
        self.completion_status = "unexecuted"


class LimitOrder(BaseOrder):
    def __init__(
        self, timestamp: pd.Timestamp, side: str, size: float, price: int
    ) -> None:
        super().__init__(timestamp=timestamp, side=side, size=size)
        self.price = price


class MarketOrder(BaseOrder):
    def __init__(self, timestamp: pd.Timestamp, side: str, size: float) -> None:
        super().__init__(timestamp=timestamp, side=side, size=size)


Order = Union[LimitOrder, MarketOrder]


class PositionSnapShot(NamedTuple):
    timestamp: pd.Timestamp
    cash: float
    position: float
    valuation: float  # position * (close value) + cash


class BackTester:
    def __init__(self, ohlcv_df: pd.DataFrame, config: dict[str, Any]) -> None:
        self.ohlcv_df = ohlcv_df
        self.ohlcv_it = ohlcv_df.itertuples(name="Tick")

        self.tick: Tick = Tick(
            Index=pd.Timestamp.min,
            open=0,
            high=0,
            low=0,
            close=0,
            volume=0,
        )  # ダミーデータで初期化
        self.now_time: pd.Timestamp = self.tick.Index

        self._snapshots: list[PositionSnapShot] = []

        self.active_orders: list[Order] = []
        self.archived_orders: list[Order] = []
        self.slippage: float = config["slippage"]  # 成行注文の時のスリッページ想定値
        self.minutes_to_expire: int = config["minutes_to_expire"]
        self.cash: float = INITIAL_CASH  # amount of JPY
        self.position: float = 0  # amount of BTC

    def __iter__(self) -> "BackTester":
        return self

    def __next__(self) -> pd.Timestamp:
        self.tick = next(self.ohlcv_it)
        self.now_time = self.tick.Index
        self.handle_orders()
        self.take_snapshot()
        return self.now_time

    def handle_orders(self) -> None:
        remained_orders: list[Order] = []
        for order in self.active_orders:
            # 有効期限が過ぎたものを削除
            time_diff = self.now_time - order.timestamp
            if time_diff.total_seconds() >= self.minutes_to_expire * 60:
                order.completion_time = self.now_time
                order.completion_status = "expired"
                self.archived_orders.append(order)
                continue

            # 注文実行
            if isinstance(order, MarketOrder) or (
                isinstance(order, LimitOrder)
                and (order.price > self.tick.low)
                or (order.price < self.tick.high)
            ):
                self.execute_order(order)
                self.archived_orders.append(order)
                continue

            # 実行されなかった場合は残す
            remained_orders.append(order)

        self.active_orders = remained_orders

    def execute_order(self, order: Order) -> None:
        price = self.tick.close
        if isinstance(order, MarketOrder):
            if order.side == "BUY":
                price = round(price * (1 + self.slippage))
            else:
                price = round(price * (1 - self.slippage))
        else:
            price = order.price

        if order.side == "BUY":
            self.position += order.size
            self.cash -= price * order.size
        else:
            self.position -= order.size
            self.cash += price * order.size

        order.completion_time = self.now_time
        order.completion_status = "executed"

    @property
    def snapshot(self) -> pd.DataFrame:
        return pd.DataFrame(self._snapshots).set_index("timestamp")

    def take_snapshot(self) -> None:
        self._snapshots.append(
            PositionSnapShot(
                timestamp=self.now_time,
                cash=self.cash,
                position=self.position,
                valuation=self.position * self.tick.close + self.cash,
            )
        )

    def run_backtest(self) -> None:
        for now_time in self:
            pass


if __name__ == "__main__":
    # CSVデータを読み込む
    df = pd.read_csv(
        "../input_data/btf_periods900.csv",
    )
    # UNIXtimeをpandas.Timestampに変換する
    df["CloseTime"] = pd.to_datetime(df["CloseTime"], unit="s")

    rename_dict = {
        "CloseTime": "timestamp",
        "OpenPrice": "open",
        "HighPrice": "high",
        "LowPrice": "low",
        "ClosePrice": "close",
        "Volume": "volume",
    }
    df = df[list(rename_dict.keys())].rename(columns=rename_dict).set_index("timestamp")

    config = {"slippage": 0, "minutes_to_expire": 60}
    tester = BackTester(df, config)
    tester.run_backtest()
    snapshot = tester.snapshot
    print(snapshot)

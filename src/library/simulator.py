import random
from typing import Any, Literal, NamedTuple

import pandas as pd

INITIAL_CASH = 1000000  # 100万円

Side = Literal["BUY", "SELL"]


class Tick(NamedTuple):
    Index: pd.Timestamp
    open: float
    high: float
    low: float
    close: float
    volume: float


class OrderResult(NamedTuple):
    completion_time: pd.Timestamp | None = None
    completion_status: str = "unexecuted"
    cash_diff: float | None = None
    position_diff: float | None = None


class BaseOrder:
    _id = 0

    def __init__(
        self,
        timestamp: pd.Timestamp,
        side: Side,
        size: float,
    ) -> None:
        if size <= 0:
            raise ValueError("size must be a positive number.")
        self.id = BaseOrder._id
        BaseOrder._id += 1
        self.timestamp = timestamp
        self.side: Side = side
        self.size = size
        self.result = OrderResult()

    def __eq__(self, other: object | None) -> bool:
        if isinstance(other, BaseOrder):
            return self.id == other.id
        return False

    @property
    def is_executed(self) -> bool:
        return self.result.completion_status == "executed"

    @property
    def is_unexecuted(self) -> bool:
        return self.result.completion_status == "unexecuted"


class LimitOrder(BaseOrder):
    def __init__(
        self, timestamp: pd.Timestamp, side: Side, size: float, price: int
    ) -> None:
        if price < 0:
            raise ValueError("price must be a non-negative number.")
        super().__init__(timestamp=timestamp, side=side, size=size)
        self.price = price


class MarketOrder(BaseOrder):
    def __init__(self, timestamp: pd.Timestamp, side: Side, size: float) -> None:
        super().__init__(timestamp=timestamp, side=side, size=size)


Order = LimitOrder | MarketOrder


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
                order.result = OrderResult(self.now_time, "expired", None, None)
                self.archived_orders.append(order)
                continue

            if not self.validate_order(order):
                order.result = OrderResult(self.now_time, "invalid", None, None)
                self.archived_orders.append(order)
                continue

            # 注文実行
            if isinstance(order, MarketOrder) or (
                isinstance(order, LimitOrder)
                and ((order.price > self.tick.low) or (order.price < self.tick.high))
            ):
                self.execute_order(order)
                assert order.is_executed
                self.archived_orders.append(order)
                continue

            # 実行されなかったものは残す
            assert order.is_unexecuted
            remained_orders.append(order)

        self.active_orders = remained_orders

    def validate_order(self, order: Order) -> bool:
        # check minimum lot
        # TODO

        # check max lot
        # TODO

        # check collateral
        # TODO

        # check max_position
        price = self.tick.close
        if isinstance(order, MarketOrder):
            if order.side == "BUY":
                price = round(price * (1 + self.slippage))
            else:
                price = round(price * (1 - self.slippage))
        else:
            price = order.price

        if order.side == "BUY":
            return self.cash - price * order.size >= 0
        else:
            return self.position - order.size >= 0

    def execute_order(self, order: Order) -> None:
        price = self.tick.close
        if isinstance(order, MarketOrder):
            if order.side == "BUY":
                price = round(price * (1 + self.slippage))
            else:
                price = round(price * (1 - self.slippage))
        else:
            price = order.price

        cash_diff: float = 0
        position_diff: float = 0
        if order.side == "BUY":
            cash_diff = price * order.size * (-1)
            position_diff = order.size
        else:
            cash_diff = price * order.size
            position_diff = order.size * (-1)

        self.cash += cash_diff
        self.position += position_diff

        order.result = OrderResult(self.now_time, "executed", cash_diff, position_diff)

    @property
    def snapshots(self) -> pd.DataFrame:
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

    def get_current_state(self):
        return PositionSnapShot(
            timestamp=self.now_time,
            cash=self.cash,
            position=self.position,
            valuation=self.position * self.tick.close + self.cash,
        )

    def market_buy(self, size: float) -> None:
        """
        保有cashを超える分の注文は買える最大値に変換される
        """
        order = MarketOrder(self.now_time, side="BUY", size=size)
        self.active_orders.append(order)

    def market_sell(self, size: float) -> None:
        """
        保有cashを超える分の注文は売れる最大値に変換される
        """
        order = MarketOrder(self.now_time, side="SELL", size=size)
        self.active_orders.append(order)

    def limit_buy(
        self,
        size: float,
        price: int,
    ) -> None:
        order = LimitOrder(self.now_time, side="BUY", size=size, price=price)
        self.active_orders.append(order)

    def limit_sell(
        self,
        size: float,
        price: int,
    ) -> None:
        order = LimitOrder(self.now_time, side="SELL", size=size, price=price)
        self.active_orders.append(order)

    def add_order(self, order: Order) -> None:
        self.active_orders.append(order)


class myRunner:
    def __init__(self, tester: BackTester) -> None:
        self.tester = tester

    def run(self) -> None:
        # ランダムに売買する
        for i, now_time in enumerate(self.tester):
            now_price = self.tester.tick.close
            now_cash = self.tester.cash
            now_position = self.tester.position
            if i % 2 == 0:
                expected_max_size = now_cash / now_price
                portion = random.random()
                self.tester.market_buy(expected_max_size * portion)
            else:
                portion = random.random()
                self.tester.market_sell(now_position * portion)


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

    config = {"slippage": 0.001, "minutes_to_expire": 60}
    tester = BackTester(df, config)
    runner = myRunner(tester=tester)
    runner.run()
    snapshots = tester.snapshots
    print(snapshots)

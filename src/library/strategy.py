from abc import ABCMeta, abstractmethod
from typing import NamedTuple

import pandas as pd

from library.simulator import PositionSnapShot, Side

# import pandas_ta as ta


class CloseCondition:
    def is_satisfied(self) -> bool:
        return True


class Signal(NamedTuple):
    side: Side
    size: float


class AbstractStrategy(metaclass=ABCMeta):
    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df

    @abstractmethod
    def get_signal(self, position_snap_shot: PositionSnapShot) -> Signal | None:
        pass


# class GoldenCrossStrategy(AbstractStrategy):
#     def __init__(
#         self, length_short: int = 10, length_long: int = 20, length_expire: int = 10
#     ):
#         super().__init__()
#         self.length_short = length_short
#         self.length_long = length_long
#         self.length_expire = length_expire
#         # 現在時刻からself.requiring_periods前までのデータを使って注文を出す
#         self.requiring_periods = length_long + 1

#     # dfを, now_timeからself.requiring_periods前まで切り取る
#     # dfのindexは"timestamp", columnsは"open", "high", "low", "close", "volume"
#     def slice_df(self, now_time: pd.Timestamp, df: pd.DataFrame) -> pd.DataFrame:
#         tmp_df = df[df.index <= now_time]
#         return tmp_df.iloc[-self.requiring_periods :]

#     # main body
#     # self.queue_of_ordersに注文を追加する
#     def open_orders(
#         self,
#         df: pd.DataFrame,
#         position_snap_shot: PositionSnapShot,
#     ) -> list[Order]:
#         now_time = position_snap_shot.timestamp
#         now_cash = position_snap_shot.cash
#         now_price = df.loc[now_time, "close"]
#         open_orders: list[Order] = []
#         # ta.smaに渡すデータをなるべく小さくするため, 予めdfを切り取っておく
#         tmp_df = self.slice_df(now_time=now_time, df=df)
#         # ポジションサイズを指定
#         expected_max_size = now_cash / now_price
#         size = expected_max_size * 0.01

#         # ゴールデンクロス
#         # length_short期SMAがlength_long期SMAを上回った瞬間に買い, length_expire期後にポジション解消
#         if len(tmp_df) >= self.length_long + 1:
#             sma_short = ta.sma(close=tmp_df["close"], length=self.length_short).values
#             sma_long = ta.sma(close=tmp_df["close"], length=self.length_long).values
#             if sma_short[-1] > sma_long[-1] and sma_short[-2] < sma_long[-2]:
#                 # 買い注文
#                 o1 = MarketOrder(timestamp=now_time, side="BUY", size=size)
#                 self.queue_of_orders.append(o1)
#                 # ポジション解消
#                 # FIXME: 実際にはslippageの影響でsizeが少し小さくなる
#                 o2 = MarketOrder(
#                     timestamp=now_time + pd.Timedelta(seconds=900 * self.length_expire),
#                     side="SELL",
#                     size=size,
#                 )
#                 self.queue_of_orders.append(o2)
#         return open_orders

#     def close_orders(
#         self,
#         df: pd.DataFrame,
#         position_snap_shot: PositionSnapShot,
#     ) -> list[Order]:
#         now_time = position_snap_shot.timestamp
#         close_orders: list[Order] = []
#         for _, position in self.order2position.items():
#             if position.close_condition.is_satisfied():
#                 close_order = MarketOrder(
#                     timestamp=now_time, side="SELL", size=position.amount
#                 )
#                 close_orders.append(close_order)

#         return close_orders

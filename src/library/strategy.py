from abc import ABCMeta, abstractmethod
from typing import NamedTuple

import pandas as pd
import pandas_ta as ta

from library.simulator import PositionSnapShot, Side


class Signal(NamedTuple):
    side: Side
    size: float
    exit_time: pd.Timestamp | None = None
    # この時刻を過ぎたら手仕舞いを始める


class AbstractStrategy(metaclass=ABCMeta):
    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df

    @abstractmethod
    def get_signal(self, position_snap_shot: PositionSnapShot) -> Signal | None:
        pass


class GoldenCrossStrategy(AbstractStrategy):
    def __init__(
        self,
        df: pd.DataFrame,
        length_short: int = 10,
        length_long: int = 20,
        length_expire: int = 10,
    ):
        super().__init__(df=df)
        self.length_short = length_short
        self.length_long = length_long
        self.length_expire = length_expire
        # 現在時刻からself.requiring_periods前までのデータを使って注文を出す
        self.requiring_periods = length_long + 1

    # dfを, now_timeからself.requiring_periods前まで切り取る
    # dfのindexは"timestamp", columnsは"open", "high", "low", "close", "volume"
    def slice_df(self, now_time: pd.Timestamp) -> pd.DataFrame:
        tmp_df = self.df[self.df.index <= now_time]
        return tmp_df.iloc[-self.requiring_periods :]

    # main body
    def get_signal(self, position_snap_shot: PositionSnapShot) -> Signal | None:
        now_time = position_snap_shot.timestamp
        now_cash = position_snap_shot.cash
        now_price = self.df.loc[now_time, "close"]

        # ta.smaに渡すデータをなるべく小さくするため, 予めdfを切り取っておく
        tmp_df = self.slice_df(now_time=now_time)

        if len(tmp_df) >= self.length_long + 1:
            sma_short = ta.sma(close=tmp_df["close"], length=self.length_short).values
            sma_long = ta.sma(close=tmp_df["close"], length=self.length_long).values
            if sma_short[-1] > sma_long[-1] and sma_short[-2] < sma_long[-2]:
                # 買い注文
                return Signal(
                    side="BUY",
                    size=now_cash * 0.5 / now_price,
                    exit_time=now_time + pd.Timedelta(seconds=900 * self.length_expire),
                )
        return None


class FridayBuyStrategy(AbstractStrategy):
    def __init__(
        self,
        df: pd.DataFrame,
    ):
        super().__init__(df=df)

    def get_signal(self, position_snap_shot: PositionSnapShot) -> Signal | None:
        """
        金曜夜00:00に買って土曜00:00に売る
        """
        now_time = position_snap_shot.timestamp
        now_cash = position_snap_shot.cash
        now_price = self.df.loc[now_time, "close"]

        if now_time.dayofweek == 4 and now_time.hour == 0:
            return Signal(
                side="BUY",
                size=now_cash * 0.5 / now_price,
                exit_time=now_time + pd.Timedelta(days=1),
            )
        return None

import pandas as pd
import pandas_ta as ta

from library.simulator import BackTester, MarketOrder, Order


class RunnerwithStrategy:
    def __init__(self, tester: BackTester, strategy) -> None:
        self.tester = tester
        self.strategy = strategy

    def run(self) -> None:
        for i, now_time in enumerate(self.tester):
            # 現在時刻までの情報を取得
            now_price = self.tester.tick.close
            now_cash = self.tester.cash
            now_position = self.tester.position
            active_orders = self.tester.active_orders
            # 注文を作成
            self.strategy.make_order(
                df=self.tester.ohlcv_df,
                now_time=now_time,
                now_price=now_price,
                now_cash=now_cash,
                now_position=now_position,
                active_orders=active_orders,
            )
            # testerに注文を渡す
            self.strategy.add_order(now_time=now_time, tester=self.tester)


class AbstractStrategy:
    def __init__(self):
        self.orders_to_be_added: list[Order] = []

    # now_timeまでに発注すべき注文をtesterに渡す
    def add_order(self, now_time: pd.Timestamp, tester: BackTester) -> None:
        remained_orders_to_be_added = []
        for o in self.orders_to_be_added:
            if o.timestamp <= now_time:
                tester.add_order(o)
            else:
                remained_orders_to_be_added.append(o)
        self.orders_to_be_added = remained_orders_to_be_added


class GcStrategy(AbstractStrategy):
    def __init__(
        self, length_short: int = 10, length_long: int = 20, length_expire: int = 10
    ):
        super().__init__()
        self.length_short = length_short
        self.length_long = length_long
        self.length_expire = length_expire
        # 現在時刻からself.requiring_periods前までのデータを使って注文を出す
        self.requiring_periods = length_long + 1

    # dfを, now_timeからself.requiring_periods前まで切り取る
    # dfのindexは"timestamp", columnsは"open", "high", "low", "close", "volume"
    def slice_df(self, now_time: pd.Timestamp, df: pd.DataFrame) -> pd.DataFrame:
        tmp_df = df[df.index <= now_time]
        return tmp_df.iloc[-self.requiring_periods :]

    # main body
    # self.orders_to_be_addedに注文を追加する
    def make_order(
        self,
        df: pd.DataFrame,
        now_time: pd.Timestamp,
        now_price: float,
        now_cash: float,
        now_position: float,
        active_orders: list[Order],
    ) -> None:
        # ta.smaに渡すデータをなるべく小さくするため, 予めdfを切り取っておく
        tmp_df = self.slice_df(now_time=now_time, df=df)
        # ポジションサイズを指定
        expected_max_size = now_cash / now_price
        size = expected_max_size * 0.01

        # ゴールデンクロス
        # length_short期SMAがlength_long期SMAを上回った瞬間に買い, length_expire期後にポジション解消
        if len(tmp_df) >= self.length_long + 1:
            sma_short = ta.sma(close=tmp_df["close"], length=self.length_short).values
            sma_long = ta.sma(close=tmp_df["close"], length=self.length_long).values
            if sma_short[-1] > sma_long[-1] and sma_short[-2] < sma_long[-2]:
                # 買い注文
                o1 = MarketOrder(timestamp=now_time, side="BUY", size=size)
                self.orders_to_be_added.append(o1)
                # ポジション解消
                # FIXME: 実際にはslippageの影響でsizeが少し小さくなる
                o2 = MarketOrder(
                    timestamp=now_time + pd.Timedelta(seconds=900 * self.length_expire),
                    side="SELL",
                    size=size,
                )
                self.orders_to_be_added.append(o2)

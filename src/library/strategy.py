import pandas as pd
import pandas_ta as ta

from library.simulator import BackTester, MarketOrder, Order


class TestStrategy:
    def __init__(self, df: pd.DataFrame):
        # dfのindexは"timestamp", columnsは"open", "high", "low", "close", "volume"
        self.df = df
        self.orders_to_be_added: list[Order] = []

    # 現在時刻までの情報を受け取り、注文をself.orders_to_be_addedに追加
    def make_order(
        self,
        now_time: pd.Timestamp,
        now_price: float,
        now_cash: float,
        now_position: float,
        active_orders: list[Order],
    ) -> None:
        # 現在時刻までのデータを使って注文を出す
        tmp_df = self.df[self.df.index <= now_time]
        now_price = tmp_df["close"].iloc[-1]
        expected_max_size = now_cash / now_price
        size = expected_max_size * 0.01

        # ゴールデンクロス
        # 10期SMAが20期SMAを上回った瞬間に買い
        if len(tmp_df) >= 20:
            sma_10 = ta.sma(close=tmp_df["close"], length=10).values
            sma_20 = ta.sma(close=tmp_df["close"], length=20).values
            if sma_10[-1] > sma_20[-1] and sma_10[-2] < sma_20[-2]:
                # 買い注文
                o1 = MarketOrder(timestamp=now_time, side="BUY", size=size)
                self.orders_to_be_added.append(o1)
                # 5期後にポジション解消
                # FIXME: 実際にはslippageの影響でsizeが少し小さくなる
                o2 = MarketOrder(
                    timestamp=now_time + pd.Timedelta(seconds=900 * 5),
                    side="SELL",
                    size=size,
                )
                self.orders_to_be_added.append(o2)

    def add_order(self, now_time: pd.Timestamp, tester: BackTester) -> None:
        # now_timeまでに発注すべき注文をtesterに渡す
        remained_orders_to_be_added = []
        for o in self.orders_to_be_added:
            if o.timestamp <= now_time:
                tester.add_order(o)
            else:
                remained_orders_to_be_added.append(o)
        self.orders_to_be_added = remained_orders_to_be_added


class RunnerwithStrategy:
    def __init__(self, tester: BackTester, strategy) -> None:
        self.tester = tester
        self.strategy = strategy

    def run(self) -> None:
        # ランダムに売買する
        for i, now_time in enumerate(self.tester):
            # 現在時刻までの情報を取得
            now_price = self.tester.tick.close
            now_cash = self.tester.cash
            now_position = self.tester.position
            active_orders = self.tester.active_orders
            # 注文を作成
            self.strategy.make_order(
                now_time=now_time,
                now_price=now_price,
                now_cash=now_cash,
                now_position=now_position,
                active_orders=active_orders,
            )
            # testerに注文を渡す
            self.strategy.add_order(now_time=now_time, tester=self.tester)


class AbstractStrategy:
    def __init__(self, df):
        return None

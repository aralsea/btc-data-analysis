import pandas as pd
import pandas_ta as ta

from library.simulator import MarketOrder, Order


class AbstractStrategy:
    def __init__(self, df):
        # dfのindexは"timestamp", columnsは"open", "high", "low", "close", "volume"
        self.df = df

    # 現在時刻までの情報を受け取り、注文を出力する関数
    def make_order(
        self,
        now_time: pd.Timestamp,
        now_cash: float,
        now_position: float,
        active_orders: list[Order],
    ) -> list[Order]:
        # 現在時刻までのデータを使って注文を出す
        tmp_df = self.df.loc[:now_time]
        now_price = tmp_df["close"].iloc[-1]
        expected_max_size = now_cash / now_price
        size = expected_max_size * 0.1

        # ゴールデンクロス
        # 10期SMAが20期SMAを上回った瞬間に買い
        if len(tmp_df) >= 20:
            sma_10 = ta.sma(close=tmp_df["close"], length=10).values
            sma_20 = ta.sma(close=tmp_df["close"], length=20).values
            if sma_10[-1] > sma_20[-1] and sma_10[-2] < sma_20[-2]:
                # 買い注文
                order1 = MarketOrder(timestamp=now_time, side="BUY", size=size)
                # 逆の売り注文を1期後に出し、ポジション解消したい
                # TODO
                # order2 = MarketOrder(
                #   timestamp=now_time + pd.Timedelta(min=15), side="SELL", size=size
                # )
                # のようにしたい
        return [
            order1,
        ]

import pandas as pd

from library.simulator import BackTester, MarketOrder, Order
from library.strategy import AbstractStrategy

THRESHOLD: float = 10000
# 10000円以下のポジションは無視する


class Runner:
    def __init__(self, tester: BackTester, strategy: AbstractStrategy) -> None:
        self.tester = tester
        self.strategy = strategy
        self.unexecuted_order: Order | None = None  # 発注済みだが未約定の注文
        self.current_position: float = 0
        # abs(current_position) *（現在価格）< THRESHOLDの場合にはポジションが存在しないとみなす
        self.exit_time: pd.Timestamp | None = None

    @property
    def has_position(
        self,
    ) -> bool:
        return abs(self.current_position) * self.tester.tick.close >= THRESHOLD

    def run(self) -> None:
        for now_time in self.tester:
            self.update_status()
            if self.unexecuted_order:
                continue
            if not self.has_position:
                # ポジション作成
                self.exit_time = None
                signal = self.strategy.get_signal(self.tester.get_current_state())
                if signal:
                    order = MarketOrder(now_time, signal.side, signal.size)
                    self.exit_time = signal.exit_time
                    self.tester.add_order(order)
                    self.unexecuted_order = order
            else:
                # 手仕舞い
                if self.exit_time and self.exit_time > now_time:
                    continue
                order = MarketOrder(
                    now_time,
                    "SELL" if self.current_position > 0 else "BUY",
                    abs(self.current_position),
                )
                self.tester.add_order(order)
                self.unexecuted_order = order

    def update_status(self) -> None:
        if self.unexecuted_order is None:
            return

        if self.unexecuted_order.is_unexecuted:
            assert self.unexecuted_order in self.tester.active_orders
            return

        # 以下 executed or expired or invalid
        assert self.unexecuted_order in self.tester.archived_orders
        if self.unexecuted_order.is_executed:
            # 約定していた場合
            self.current_position += self.unexecuted_order.result.position_diff
        else:
            # expired or invalid
            pass
        self.unexecuted_order = None

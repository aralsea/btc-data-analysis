
from library.simulator import Order


class AbstractStrategy:
    def __init__(self, df, cash, position, active_orders):
        self.df = df

    def get_order(self) -> list[Order]:
        return []

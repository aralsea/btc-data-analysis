import datetime
import random
import time
from typing import Union

import numpy as np


def test_strategy() -> dict[str, Union[str, float]]:
    signals = ["buy", "sell"]
    amounts = np.arange(0.1, 1.0, 0.1)
    flag: dict[str, Union[str, float]] = {
        "signal": random.choice(signals),
        "amount": random.choice(amounts),
    }
    return flag


if __name__ == "__main__":
    try:
        while True:
            flag = test_strategy()
            print(
                f"{datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')}"
                f" : {flag.get('signal')}"
                f" {flag.get('amount'):.2f} BTC"
            )
            time.sleep(5)
    except KeyboardInterrupt:
        exit()

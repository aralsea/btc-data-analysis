import datetime as dt

import requests

# cf. https://ryota-trade.com/?p=952

periods = 900  # 15分足: 900, 日足: 86400
length = 1000  # データの取得件数, <=6000 (一度に6000件までしか取得できない)

before = dt.datetime.now()
after = before - dt.timedelta(seconds=periods * length)

# UNIXに直す
response = requests.get(
    f"https://api.cryptowat.ch/markets/bitflyer/btcjpy/ohlc?periods={periods}&before={int(before.timestamp())}&after={int(after.timestamp())}"
)
response = response.json()

# response = {"result": {"900": [[...], [...], ]}}
data = response["result"][f"{periods}"]

# len(data) = length
print(len(data))
# data[i] = [unixtime, o, h, l, c, volume, quotevolume]
print(dt.datetime.fromtimestamp(data[0][0]))
print(dt.datetime.fromtimestamp(data[-1][0]))

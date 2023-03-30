from datetime import datetime

import requests

# cf. https://ryota-trade.com/?p=952

# CryptowatchのAPIで１分足を取得
response = requests.get("https://api.cryptowat.ch/markets/bitflyer/btcfxjpy/ohlc?periods=60")
response = response.json()

# 最後から２番目のローソク足を取り出す
data = response["result"]["60"][-2]
print(data)

# ローソク足から日時・始値・終値を取り出す
close_time = datetime.fromtimestamp(data[0]).strftime('%Y/%m/%d %H:%M')
open_price = data[1]
close_price = data[4]

print( "時間： " + close_time
	+ " 始値： " + str(open_price)
	+ " 終値： " + str(close_price) )

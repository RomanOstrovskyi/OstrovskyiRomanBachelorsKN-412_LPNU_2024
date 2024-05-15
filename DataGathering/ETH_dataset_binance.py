from binance.client import Client
import csv
from datetime import datetime, timedelta
import requests
import pandas as pd
import pandas_ta as ta


csv_headers = [
        'Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_time',
        'Quote_asset_volume', 'Number_of_trades', 'Taker_buy_base_asset_volume',
        'Taker_buy_quote_asset_volume', 'Cryptoname', 'FAGI'
]

api_key = ''
api_secret = ''

client = Client(api_key, api_secret)


print("Please enter the name of crypto, which dataset you want to collect: ")
print("Available crypto: ETHUSDT")
# symbol = input().upper()

symbol = "ETHUSDT"

allowed_names = ["ETHUSDT"]

if symbol not in allowed_names:
    raise Exception("This crypto is not available")

counter = 15

global_csv_data = []

end_time = datetime.now() - timedelta(days=250)
start_time = end_time - timedelta(days=300)

response = requests.get('https://api.alternative.me/fng/?limit=10000')
fng_data = response.json()['data']

fng_dict = {int(item['timestamp']): item['value'] for item in fng_data}

while counter:

    klines = client.futures_klines(
        symbol=symbol,
        interval=Client.KLINE_INTERVAL_1DAY,
        startTime=int(start_time.timestamp() * 1000),
        endTime=int(end_time.timestamp() * 1000)
    )

    csv_data = []
    global_csv_data.append(csv_data)

    for item in klines:
        print(item)
        timestamp = item[0] / 1000
        date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        close_timestamp = item[6] / 1000
        close_date = datetime.fromtimestamp(close_timestamp).strftime('%Y-%m-%d')
        open_price = item[1]
        high_price = item[2]
        low_price = item[3]
        close_price = item[4]
        volume = item[5]
        close_time = close_date
        quote_asset_volume = item[7]
        number_of_trades = item[8]
        taker_buy_base_asset_volume = item[9]
        taker_buy_quote_asset_volume = item[10]

        fear_and_greed_index = fng_dict.get(int(timestamp), None)

        csv_data.append([
            date, open_price, high_price, low_price, close_price, volume, close_time,
            quote_asset_volume, number_of_trades, taker_buy_base_asset_volume,
            taker_buy_quote_asset_volume, symbol, fear_and_greed_index
        ])

    counter -= 1

    end_time = start_time
    start_time = end_time - timedelta(days=50)


def calculate_rsi(data, time_window=14):
    diff = data.diff(1).dropna()
    up_chg = 0 * diff
    down_chg = 0 * diff
    up_chg[diff > 0] = diff[diff>0]
    down_chg[diff < 0] = diff[diff < 0]
    up_chg_avg = up_chg.ewm(com=time_window-1, min_periods=time_window).mean()
    down_chg_avg = down_chg.ewm(com=time_window-1, min_periods=time_window).mean()
    rs = abs(up_chg_avg/down_chg_avg)
    rsi = 100 - 100/(1+rs)
    return rsi


final_csv_data = [row for chunk in reversed(global_csv_data) for row in chunk]

df = pd.DataFrame(final_csv_data, columns=csv_headers)
df['Close'] = df['Close'].astype(float)
df['RSI'] = ta.rsi(df['Close'], length=14)
df['MA_50'] = ta.sma(df['Close'], length=50)
df['ROC_26'] = ta.roc(df['Close'], length=26)

# Add 'RSI' to your CSV headers
csv_headers.extend(['RSI', 'MA_50', 'ROC_26'])

# Convert the DataFrame back to a list of lists and include the new 'RSI' column
final_csv_data = df.values.tolist()

with open(f'{symbol}_rsi_fagi_1.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(csv_headers)
    writer.writerows(final_csv_data)


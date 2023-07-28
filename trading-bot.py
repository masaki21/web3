# Import libraries
import requests
from binance.client import Client
import pandas as pd
import numpy as np
from dotenv import load_dotenv
load_dotenv()

import os

# Binance Future API
API_KEY = os.environ.get('API_KEY') or ""
API_SECRET = os.environ.get('API_SECRET') or  ""

print('API_KEY', API_KEY, 'API_SECRET', API_SECRET)
client = Client(API_KEY, API_SECRET, testnet=True)

# Constants
SYMBOL = "BTCUSDT"
TIME_PERIOD = "1m"  # Taking 1 minutes time period
LIMIT = "200"  # Taking 200 candles as limit
QNTY = 0.03
stock_price = []
pos_held = False

# Get our account information
account = client.futures_account_balance()
print(account)
asset = pd.DataFrame(account)
print(asset)
last_price = client.get_symbol_ticker(symbol="BTCUSDT")
print(last_price)


# Get data from Binance
def get_data():
    url = "https://api.binance.com/api/v3/klines?symbol={}&interval={}&limit={}".format(SYMBOL, TIME_PERIOD, LIMIT)
    res = requests.get(url)
    return_data = []
    for each in res.json():
        return_data.append(float(each[4]))
    return np.array(return_data)


# Calculate EMA
def calculate_ema(prices, days, smoothing=2):
    ema = [sum(prices[:days]) / days]
    for price in prices[days:]:
        ema.append((price * (smoothing / (1 + days))) + ema[-1] * (1 - (smoothing / (1 + days))))
    return ema


# EMA Algorithm
while True:
    print("")
    print("Checking Price")
    ema = calculate_ema(get_data(), len(get_data()))[-1]
    last_price = get_data()[-1]  # Most recent closing price
    print("Exponential Moving Average: " + str(ema))
    print("Last Price: " + str(last_price))

    # Buy
    if last_price > ema and not pos_held:  # If price is crossing EMA, and we haven't already bought -> so we buy it
        print("Buy")
        client.futures_create_order(symbol=SYMBOL, side="BUY", type="MARKET", quantity=QNTY)
        # client.futures_create_order(symbol='BTCUSDT', side='BUY', type='LIMIT', timeInForce='GTC', quantity=0.01, price=38780.0)
        pos_held = True
        stock_price.append(last_price)
    print(stock_price)

    # Sell
    if len(stock_price) != 0:
        if last_price >= (stock_price[-1] + stock_price[-1] * 0.0013) and pos_held:
            print("Sell take profit")
            client.futures_create_order(symbol=SYMBOL, side="SELL", type="MARKET", quantity=QNTY)
            # client.futures_create_order(symbol='BTCUSDT', side='SELL', type='LIMIT', timeInForce='GTC', quantity=0.01, price=40000.0)
            pos_held = False
            stock_price.clear()
        elif last_price <= (stock_price[-1] - stock_price[-1] * 0.05) and pos_held:
            print("Sell stop loss")
            client.futures_create_order(symbol=SYMBOL, side="SELL", type="MARKET", quantity=QNTY)
            # client.futures_create_order(symbol='BTCUSDT', side='SELL', type='LIMIT', timeInForce='GTC', quantity=0.01, price=40000.0)
            pos_held = False
            stock_price.clear()
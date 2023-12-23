import binance
import websocket
import json
import backtrader as bt

# import Libraries
from binance.spot import Spot as Client
import pandas as pd
import plotly.graph_objects as go
from IPython.display import display

# url to access binance api
base_url = "https://api.binance.com"

# use for testing
base_url_test = "https://testnet.binance.vision" 

# create Client to access API
spot_client = Client(base_url=base_url)


# requesting exchange info
exchange_info = spot_client.exchange_info()
exchange_info


# symbols as DataFrame
symbols = pd.DataFrame(exchange_info['symbols'])
symbols

# Access current Prices for your desired symbol
btcusd_price = spot_client.ticker_price("BTCUSDT")
btcusd_price

# Access historical prices
btcusd_history = spot_client.klines("BTCUSDT", "1h", limit=100)
display(btcusd_history[:2])

# show as DataFrame
columns=['time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 
         'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore']
btcusd_history_df = pd.DataFrame(btcusd_history, columns=columns)
btcusd_history_df['time'] = pd.to_datetime(btcusd_history_df['time'], unit='ms')

display(btcusd_history_df)

# plot results
fig = go.Figure(data=[go.Candlestick(x=btcusd_history_df['time'],
                open=btcusd_history_df['open'],
                high=btcusd_history_df['high'],
                low=btcusd_history_df['low'],
                close=btcusd_history_df['close'])])
 
fig.show()

depth = spot_client.depth("BTCUSDT", limit=10)
depth_df = pd.DataFrame(depth)

depth_df


trades = spot_client.trades("BTCUSDT", limit=10)
trades_df = pd.DataFrame(trades)
trades_df['time'] = pd.to_datetime(trades_df['time'], unit='ms')

trades_df

# note: isBuyerMaker = True -> sell transaction, isBuyerMaker = False -> buy transaction




# Set your API keys
API_KEY = 'TXiQy4J38Ml2PFJTkVTPWtHPTch6CEGh50yjweG3rD0BkgcX6zukgNH1Okkf32p8'
SECRET_KEY = 'AoqBwu2ttbMDo5dC2hbj4dDpiVl5aYa1l0WO'


# Set the cryptocurrencies and WebSocket data subscriptions
symbols = ['btcusdt', 'ethusdt', 'dogeusdt', 'rvnusdt', 'roseusdt']
channels = [f'{symbol}@kline_1m' for symbol in symbols]
websocket_url = 'wss://stream.binance.com:9443/ws'

# Set the take-profit and stop-loss percentages
take_profit_pct = 0.4  # 40% take-profit
stop_loss_pct = 0.3  # 30% stop-loss

# Create a WebSocket connection
ws = websocket.WebSocketApp(websocket_url)

class VWAPandSMA(bt.Strategy):
    def __init__(self):
        self.vwap = bt.indicators.WeightedMovingAverage(
            self.data.typical, period=30, plotname='VWAP'
        )
        self.sma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=200, plotname='SMA'
        )
        self.buy_signal = bt.indicators.CrossOver(self.data.close, self.vwap)
        self.sell_signal = bt.indicators.CrossDown(self.data.close, self.vwap)

    def next(self):
        if self.buy_signal[0]:
            self.buy()
        elif self.sell_signal[0]:
            self.sell()

def on_open(ws):
    # Set the subscription messages for each symbol
    subscribe_msgs = [
        {
            'method': 'SUBSCRIBE',
            'params': [channel],
            'id': idx + 1
        }
        for idx, channel in enumerate(channels)
    ]
    # Send the subscription messages
    for msg in subscribe_msgs:
        ws.send(json.dumps(msg))

def on_message(ws, message):
    # Parse the received message
    msg = json.loads(message)
    if 'k' in msg:
        # Update the candlestick data
        kline_data = msg['k']
        symbol = kline_data['s']
        # Get the latest price
        latest_price = float(kline_data['c'])
        print(f'Latest Price ({symbol}): {latest_price}')

        # Check if the take-profit or stop-loss should be triggered
        # Replace this logic with your own trading strategy
        if latest_price >= take_profit_pct:
            print(f'Take-profit triggered ({symbol})')
            # Perform the take-profit action

        elif latest_price <= stop_loss_pct:
            print(f'Stop-loss triggered ({symbol})')
            # Perform the stop-loss action

        # Run the trading strategy
        cerebro = bt.Cerebro()
        cerebro.addstrategy(VWAPandSMA)
        data = bt.feeds.YourDataFeed()  # Replace with your data feed
        cerebro.adddata(data)
        cerebro.run()

def on_close(ws):
    print('WebSocket Connection Closed')

# Set the WebSocket event handlers
ws.on_open = on_open
ws.on_message = on_message
ws.on_close = on_close

# Connect to the WebSocket and keep it running
ws.run_forever()

# Run the trading strategy
cerebro = bt.Cerebro()
cerebro.addstrategy(VWAPandSMA)
data = bt.feeds.YourDataFeed()  # Replace with your data feed
cerebro.adddata(data)
cerebro.run()

# Plot the trading strategy
cerebro.plot(style='candle', iplot=True)

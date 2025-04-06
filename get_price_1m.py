import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

# Set the stock symbol
stock_symbol = 'AAPL'

# Get the ticker object
ticker = yf.Ticker(stock_symbol)

# Get the historical data for the last day at 1-minute intervals
hist = ticker.history(period='1d', interval='1m')

# Plotting the OHLC data
fig, ax = plt.subplots(figsize=(10, 6))

# Plot Open, High, Low, Close as candlesticks
ax.plot(hist.index, hist['Open'], label='Open', color='blue', alpha=0.6)
ax.plot(hist.index, hist['High'], label='High', color='green', alpha=0.6)
ax.plot(hist.index, hist['Low'], label='Low', color='red', alpha=0.6)
ax.plot(hist.index, hist['Close'], label='Close', color='black', alpha=0.6)

# Format the x-axis (time)
ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

# Rotate the date labels for better readability
plt.xticks(rotation=45)

# Add labels and title
plt.title(f'{stock_symbol} 1-Day OHLC Data', fontsize=14)
plt.xlabel('Time', fontsize=12)
plt.ylabel('Price ($)', fontsize=12)

# Add a legend
plt.legend()

# Show the plot
plt.tight_layout()
plt.show()

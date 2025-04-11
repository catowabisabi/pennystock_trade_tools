import yfinance as yf
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# 取得股票數據
stock_symbol = 'AAPL'
ticker = yf.Ticker(stock_symbol)
hist = ticker.history(period="1d", interval="1m")

# 提取收盤價和成交量
prices = hist['Close'].values
volumes = hist['Volume'].values

# 將收盤價和成交量作為特徵向量組合
data = np.column_stack((prices, volumes))

# 設置 K-means 聚類的數量（假設聚成 3 個類別）
kmeans = KMeans(n_clusters=3)
hist['Cluster'] = kmeans.fit_predict(data)

# 繪製圖表
plt.figure(figsize=(12,6))
plt.plot(hist.index, hist['Close'], label='Close Price', color='blue')

# 標出每個聚類的中心點，這些通常可以視為支撐或阻力位
centroids = kmeans.cluster_centers_
for centroid in centroids:
    plt.axhline(y=centroid[0], color='red', linestyle='--', label='Cluster Centroid')

plt.title(f'{stock_symbol} Support and Resistance Levels using K-means with Volume')
plt.xlabel('Date')
plt.ylabel('Price')
plt.legend()
plt.show()

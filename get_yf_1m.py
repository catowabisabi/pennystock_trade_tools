import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import pytz

# 設定股票代碼
stock_symbol = 'bjdx'

# 取得歷史數據（包含成交量）
ticker = yf.Ticker(stock_symbol)
hist = ticker.history(period='1d', interval='1m')

# 轉換時區（美東時間 ET）
et_tz = pytz.timezone('America/New_York')
hist.index = hist.index.tz_convert(et_tz)

# 建立時間欄位
hist["Datetime"] = hist.index
hist["Time"] = hist.index.strftime("%H:%M")

# 計算成交量顏色（上漲綠、下跌紅）
hist['Color'] = ['green' if c >= o else 'red' for c, o in zip(hist['Close'], hist['Open'])]

# 創建子圖（上方 K 線圖，下方成交量）
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                    vertical_spacing=0.05, row_heights=[0.7, 0.3])

# 添加 K 線圖
fig.add_trace(go.Candlestick(
    x=hist["Datetime"],
    open=hist['Open'],
    high=hist['High'],
    low=hist['Low'],
    close=hist['Close'],
    increasing_line_color='lime',  
    decreasing_line_color='red'    
), row=1, col=1)

# 添加成交量圖（顏色對應紅綠）
fig.add_trace(go.Bar(
    x=hist["Datetime"],
    y=hist['Volume'],
    marker=dict(color=hist['Color']),
    opacity=0.3,
    name="Volume"
), row=2, col=1)

# **加上時間間隔線**
for i, time in enumerate(hist["Time"]):
    if ":30" in time:  # **30 分鐘間隔 → 25% 透明線**
        line_width = 0.5
    #if ":15" in time or ":45" in time:  # **15 分鐘間隔 → 10% 透明線**
        #line_width = 0.5
    #elif ":05" in time or ":10" in time or ":20" in time or ":25" in time or ":35" in time or ":40" in time or ":50" in time or ":55" in time:  # **5 分鐘間隔 → 3% 透明線**
    #    line_width = 1
    else:
        continue  # 跳過不需要的時間
    
    fig.add_shape(type="line",
                  x0=hist["Datetime"].iloc[i], y0=0,
                  x1=hist["Datetime"].iloc[i], y1=1,
                  xref='x', yref='paper',
                  line=dict(color="white", width=line_width, dash="dot"))

# **在成交量區加上橫線**
volume_max = hist['Volume'].max()
#for level in [0.1, 0.1, 0.3]:  # 25%、50%、75% 水準線
#    fig.add_shape(type="line",
#                  x0=hist["Datetime"].iloc[0], y0=volume_max * level,
 #                 x1=hist["Datetime"].iloc[-1], y1=volume_max * level,
  #                xref='x', yref='y2',
 #                 line=dict(color="white", width=1, dash="dash"))

# 設定 TradingView 風格
fig.update_layout(
    title=f'{stock_symbol} 1-Day Candlestick Chart (ET Time)',
    xaxis_title='Time (ET)',
    yaxis_title='Price ($)',
    xaxis_rangeslider_visible=False,
    paper_bgcolor="black",  # 圖表外部背景（黑色）
    plot_bgcolor="#0F1B2A",  # 圖表內部背景（深藍色）
    font=dict(color="white"),  # 文字顏色（白色）
    xaxis=dict(
        gridcolor="rgba(255, 255, 255, 0.3)",  # X 軸白線透明度 50%
        tickformat="%H:%M",  # 顯示時間（時:分）
        showticklabels=True  # 顯示時間標籤
    ),
    yaxis=dict(gridcolor="rgba(255, 255, 255, 0.3)"),  # Y 軸白線透明度 50%
    yaxis2=dict(gridcolor="rgba(255, 255, 255, 0.3)")  # **成交量區的白線透明度 50%**
)

# 顯示圖表
fig.show()

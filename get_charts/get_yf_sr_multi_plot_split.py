import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from scipy import stats
from scipy.signal import argrelextrema, find_peaks
import pytz
from datetime import datetime
from collections import defaultdict
from functools import partial

class SupportResistanceAnalyzer:
    def __init__(self, df):
        self.df = df
        self.results = {}
    
    def fibonacci_levels(self, atr_multiplier=1.5):
        try:
            # 改進：使用ATR過濾有效波段
            highs = self.df['high'].rolling(5).max()
            lows = self.df['low'].rolling(5).min()
            atr = (self.df['high'] - self.df['low']).mean()
            
            valid_highs = highs[highs.diff() > atr * atr_multiplier]
            valid_lows = lows[lows.diff() < -atr * atr_multiplier]
            
            high = valid_highs.max() if not valid_highs.empty else self.df['high'].max()
            low = valid_lows.min() if not valid_lows.empty else self.df['low'].min()
            diff = high - low
            
            levels = {
                '0%': high,
                '23.6%': high - diff * 0.236,
                '38.2%': high - diff * 0.382,
                '50%': high - diff * 0.5,
                '61.8%': high - diff * 0.618,
                '100%': low
            }
            self.results['Fibonacci'] = levels
        except Exception as e:
            print(f"Error in fibonacci_levels: {str(e)}")
            self.results['Fibonacci'] = "N/A"
    
    def pivot_points(self, volatility_window=5):
        try:
            # 改進：動態窗口
            volatility = self.df['close'].pct_change().rolling(volatility_window).std().fillna(0)
            window = np.where(volatility > 0.05, 5, 10)
            
            # 使用scipy找極值點
            peaks, _ = find_peaks(self.df['high'], prominence=0.1)
            valleys, _ = find_peaks(-self.df['low'], prominence=0.1)
            
            resistance = self.df['high'].iloc[peaks].dropna()
            support = self.df['low'].iloc[valleys].dropna()
            
            # 合併相近水平（改用固定$0.02閾值）
            resistance = self._cluster_levels(resistance, threshold=0.02)
            support = self._cluster_levels(support, threshold=0.02)
            
            self.results['Pivot Points'] = {
                'Support': support,
                'Resistance': resistance
            }
        except Exception as e:
            print(f"Error in pivot_points: {str(e)}")
            self.results['Pivot Points'] = "N/A"
    
    def _cluster_levels(self, levels, threshold=0.02):
        if len(levels) == 0:
            return []
            
        clustered = []
        for level in sorted(levels):
            if not clustered:
                clustered.append([level])
            else:
                last_group = clustered[-1]
                if abs(level - np.mean(last_group)) <= threshold:
                    last_group.append(level)
                else:
                    clustered.append([level])
        return [round(np.mean(group), 2) for group in clustered]

    def bollinger_bands(self, window=20, std_dev=2):
        try:
            if len(self.df) < window:
                raise ValueError("Insufficient data for Bollinger Bands")
                
            close = self.df['close']
            middle = close.rolling(window=window).mean()
            std = close.rolling(window=window).std()
            
            upper = middle + (std * std_dev)
            lower = middle - (std * std_dev)
            
            self.results['Bollinger Bands'] = {
                'Upper': upper.iloc[-1],
                'Middle': middle.iloc[-1],
                'Lower': lower.iloc[-1]
            }
        except Exception as e:
            print(f"Error in bollinger_bands: {str(e)}")
            self.results['Bollinger Bands'] = "N/A"
    
    def kmeans_clusters(self, n_clusters=5):
        try:
            if len(self.df) < n_clusters:
                raise ValueError("Insufficient data for KMeans")
                
            # 改進：加入高低收盤價
            prices = self.df[['high', 'low', 'close']].values
            kmeans = KMeans(n_clusters=n_clusters).fit(prices)
            levels = sorted([x[2] for x in kmeans.cluster_centers_])  # 取收盤價中心
            self.results['KMeans Clusters'] = levels
        except Exception as e:
            print(f"Error in kmeans_clusters: {str(e)}")
            self.results['KMeans Clusters'] = "N/A"
    
    def volume_profile(self, bins=20):
        try:
            if len(self.df) < 20:
                raise ValueError("Insufficient data for Volume Profile")
                
            # 改進：動態價格分箱
            price_range = self.df['high'].max() - self.df['low'].min()
            step = max(0.01, price_range / bins)  # Penny Stock最小步長$0.01
            price_bins = np.arange(
                np.floor(self.df['low'].min()),
                np.ceil(self.df['high'].max()) + step,
                step
            )
            
            volume_at_price = []
            for i in range(1, len(price_bins)):
                mask = (self.df['high'] >= price_bins[i-1]) & (self.df['low'] <= price_bins[i])
                volume_at_price.append({
                    'price': (price_bins[i-1] + price_bins[i]) / 2,
                    'volume': self.df[mask]['volume'].sum()
                })
            
            # 改進：取成交量前20%的水平
            volumes = [x['volume'] for x in volume_at_price]
            if not volumes:
                self.results['Volume Profile'] = []
                return
                
            threshold = np.percentile(volumes, 80)
            significant_levels = [
                x['price'] for x in volume_at_price
                if x['volume'] >= threshold
            ]
            
            self.results['Volume Profile'] = significant_levels
        except Exception as e:
            print(f"Error in volume_profile: {str(e)}")
            self.results['Volume Profile'] = "N/A"
    
    def run_all_analysis(self):
        methods = [
            ('Fibonacci', self.fibonacci_levels),
            ('Pivot Points', self.pivot_points),
            ('Bollinger Bands', self.bollinger_bands),
            ('KMeans Clusters', partial(self.kmeans_clusters, n_clusters=5)),
            ('Volume Profile', self.volume_profile)
        ]
        
        for name, method in methods:
            try:
                method()
            except Exception as e:
                print(f"Method {name} failed: {str(e)}")
                self.results[name] = "N/A"
        
        return self.results

def get_stock_data(ticker, period='5d', interval='15m'):
    ticker = ticker.upper()
    try:
        data = yf.download(ticker, period=period, interval=interval, prepost=True)
        if data.empty:
            raise ValueError(f"No data found for {ticker}")
            
        if isinstance(data.columns, pd.MultiIndex):
            data = data.loc[:, data.columns.get_level_values(1).isin([ticker])]
            data.columns = data.columns.droplevel(1)
        
        data.columns = data.columns.str.lower()
        data = data[['open', 'high', 'low', 'close', 'volume']]
        
        if data.index.tzinfo is None:
            et_tz = pytz.timezone('America/New_York')
            data.index = data.index.tz_localize('UTC').tz_convert(et_tz)
        
        return data.sort_index()
    except Exception as e:
        raise ValueError(f"Error downloading {ticker}: {str(e)}")

def create_base_chart(df, title):
    """創建基礎K線圖（含成交量）"""
    hist = df.copy().reset_index()
    hist['color'] = np.where(hist['close'] >= hist['open'], 'lime', 'red')
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                       vertical_spacing=0.05, row_heights=[0.7, 0.3])
    
    # K線
    fig.add_trace(go.Candlestick(
        x=hist["Datetime"],
        open=hist['open'],
        high=hist['high'],
        low=hist['low'],
        close=hist['close'],
        increasing_line_color='lime',
        decreasing_line_color='red',
        name="OHLC"
    ), row=1, col=1)
    
    # 成交量
    fig.add_trace(go.Bar(
        x=hist["Datetime"],
        y=hist['volume'],
        marker_color=hist['color'],
        opacity=0.3,
        name="Volume"
    ), row=2, col=1)
    
    # 盤前盤後標記（改進：處理多日數據）
    unique_dates = pd.to_datetime(hist["Datetime"].dt.date.unique())
    for date in unique_dates:
        pre_market_start = pd.to_datetime(f"{date} 04:00:00").tz_localize("America/New_York")
        pre_market_end = pd.to_datetime(f"{date} 09:30:00").tz_localize("America/New_York")
        post_market_start = pd.to_datetime(f"{date} 16:00:00").tz_localize("America/New_York")
        post_market_end = pd.to_datetime(f"{date} 20:00:00").tz_localize("America/New_York")
        
        fig.add_vrect(
            x0=pre_market_start, x1=pre_market_end,
            fillcolor="yellow", opacity=0.1, layer="below", line_width=0,
            row="all", col="all"
        )
        fig.add_vrect(
            x0=post_market_start, x1=post_market_end,
            fillcolor="navy", opacity=0.1, layer="below", line_width=0,
            row="all", col="all"
        )
    
    # 統一風格
    fig.update_layout(
        title=title,
        paper_bgcolor="black",
        plot_bgcolor="#0F1B2A",
        font=dict(color="white"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.2)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.2)"),
        yaxis2=dict(gridcolor="rgba(255,255,255,0.2)"),
        margin=dict(l=50, r=50, t=80, b=50),
        height=800,
        showlegend=False
    )
    
    return fig

def create_fibonacci_chart(df, results):
    fig = create_base_chart(df, f"{df.index[-1].strftime('%Y-%m-%d')} Fibonacci Levels")
    
    if 'Fibonacci' not in results or results['Fibonacci'] == "N/A":
        return fig
    
    levels = results['Fibonacci']
    colors = ['#FFD700', '#FFA500', '#FF8C00', '#FF6347', '#FF4500', '#FF0000']
    
    for i, (name, level) in enumerate(levels.items()):
        fig.add_shape(
            type="line", 
            x0=df.index[0], y0=level,
            x1=df.index[-1], y1=level,
            line=dict(color=colors[i], width=2, dash="dash"),
            row=1, col=1
        )
        fig.add_annotation(
            x=df.index[-1], y=level,
            text=f"Fib {name} ({level:.2f})",
            xanchor="left",
            font=dict(color=colors[i], size=12),
            showarrow=False,
            row=1, col=1
        )
    
    return fig

def create_pivot_chart(df, results):
    fig = create_base_chart(df, f"{df.index[-1].strftime('%Y-%m-%d')} Pivot Points")
    
    if 'Pivot Points' not in results or results['Pivot Points'] == "N/A":
        return fig
    
    # 支撐位（藍色）
    supports = results['Pivot Points'].get('Support', [])
    for i, level in enumerate(supports[:5]):  # 最多顯示5個
        fig.add_shape(
            type="line",
            x0=df.index[0], y0=level,
            x1=df.index[-1], y1=level,
            line=dict(color='#1E90FF', width=1.5),
            row=1, col=1
        )
        fig.add_annotation(
            x=df.index[-1], y=level,
            text=f"S ({level:.2f})",
            xanchor="left",
            font=dict(color='#1E90FF', size=10),
            showarrow=False,
            row=1, col=1
        )
    
    # 阻力位（紅色）
    resistances = results['Pivot Points'].get('Resistance', [])
    for i, level in enumerate(resistances[:5]):
        fig.add_shape(
            type="line",
            x0=df.index[0], y0=level,
            x1=df.index[-1], y1=level,
            line=dict(color='#FF6347', width=1.5),
            row=1, col=1
        )
        fig.add_annotation(
            x=df.index[-1], y=level,
            text=f"R ({level:.2f})",
            xanchor="left",
            font=dict(color='#FF6347', size=10),
            showarrow=False,
            row=1, col=1
        )
    
    return fig

def create_bollinger_chart(df, results):
    fig = create_base_chart(df, f"{df.index[-1].strftime('%Y-%m-%d')} Bollinger Bands")
    
    if 'Bollinger Bands' not in results or results['Bollinger Bands'] == "N/A":
        return fig
    
    bb = results['Bollinger Bands']
    colors = ['#00FA9A', '#FFFFFF', '#FF69B4']
    
    # 計算20期布林帶（用於繪製完整帶狀）
    window = 20
    close = df['close']
    middle = close.rolling(window).mean()
    std = close.rolling(window).std()
    upper = middle + (std * 2)
    lower = middle - (std * 2)
    
    # 添加帶狀區域
    fig.add_trace(go.Scatter(
        x=df.index,
        y=upper,
        line=dict(color=colors[0], width=1),
        name="Upper Band",
        hoverinfo='skip'
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=lower,
        line=dict(color=colors[2], width=1),
        fill='tonexty',
        fillcolor='rgba(173, 216, 230, 0.1)',
        name="Lower Band",
        hoverinfo='skip'
    ), row=1, col=1)
    
    # 標記當前水平
    for name, level, color in zip(['Upper', 'Middle', 'Lower'], 
                                 [bb['Upper'], bb['Middle'], bb['Lower']], 
                                 colors):
        fig.add_shape(
            type="line",
            x0=df.index[-20], y0=level,
            x1=df.index[-1], y1=level,
            line=dict(color=color, width=2, dash="dot"),
            row=1, col=1
        )
        fig.add_annotation(
            x=df.index[-1], y=level,
            text=f"{name} ({level:.2f})",
            xanchor="left",
            font=dict(color=color, size=10),
            showarrow=False,
            row=1, col=1
        )
    
    return fig

def create_kmeans_chart(df, results):
    fig = create_base_chart(df, f"{df.index[-1].strftime('%Y-%m-%d')} KMeans Clusters")
    
    if 'KMeans Clusters' not in results or results['KMeans Clusters'] == "N/A":
        return fig
    
    levels = results['KMeans Clusters']
    colors = ['#FF00FF', '#BA55D3', '#9370DB', '#7B68EE', '#6A5ACD']
    
    for i, level in enumerate(levels):
        fig.add_shape(
            type="line",
            x0=df.index[0], y0=level,
            x1=df.index[-1], y1=level,
            line=dict(color=colors[i % len(colors)], width=1.5, dash="dashdot"),
            row=1, col=1
        )
        fig.add_annotation(
            x=df.index[-1], y=level,
            text=f"Cluster {i+1} ({level:.2f})",
            xanchor="left",
            font=dict(color=colors[i % len(colors)], size=10),
            showarrow=False,
            row=1, col=1
        )
    
    return fig

def create_volume_profile_chart(df, results):
    fig = create_base_chart(df, f"{df.index[-1].strftime('%Y-%m-%d')} Volume Profile")
    
    if 'Volume Profile' not in results or not results['Volume Profile']:
        return fig
    
    levels = results['Volume Profile']
    max_vol = df['volume'].max()
    
    for level in levels:
        # 添加水平線
        fig.add_shape(
            type="line",
            x0=df.index[0], y0=level,
            x1=df.index[-1], y1=level,
            line=dict(color='#20B2AA', width=1, dash="dot"),
            row=1, col=1
        )
        
        # 在成交量圖上標記
        fig.add_shape(
            type="line",
            x0=df.index[0], y0=0,
            x1=df.index[-1], y1=max_vol * 0.8,
            xref="x", yref="y2",
            line=dict(color='#20B2AA', width=0.5),
            opacity=0.3,
            row=2, col=1
        )
        
        fig.add_annotation(
            x=df.index[-1], y=level,
            text=f"VP ({level:.2f})",
            xanchor="left",
            font=dict(color='#20B2AA', size=10),
            showarrow=False,
            row=1, col=1
        )
    
    return fig

def analyze_stock(ticker, period='3d', interval='5m'):
    try:
        df = get_stock_data(ticker, period, interval)
        analyzer = SupportResistanceAnalyzer(df)
        results = analyzer.run_all_analysis()
        
        charts = {
            'Fibonacci': create_fibonacci_chart(df, results),
            'Pivot Points': create_pivot_chart(df, results),
            'Bollinger Bands': create_bollinger_chart(df, results),
            'KMeans Clusters': create_kmeans_chart(df, results),
            'Volume Profile': create_volume_profile_chart(df, results)
        }
        
        return charts, results
        
    except Exception as e:
        print(f"Error analyzing {ticker}: {str(e)}")
        return None, None

# 使用示例
if __name__ == "__main__":
    ticker = "icct" 
    period = "3d"
    interval = "5m"
    
    charts, results = analyze_stock(ticker, period, interval)
    
    if charts:
        # 選擇性顯示（每次只取消註釋一個）
        #charts['Fibonacci'].show()
        charts['Pivot Points'].show()
        # charts['Bollinger Bands'].show()
        # charts['KMeans Clusters'].show()
        # charts['Volume Profile'].show()
        
        # 打印結果（不會觸發圖表顯示）
        print("\n📊 Analysis Results:")
        for method, values in results.items():
            print(f"\n🔍 {method}:")
            if isinstance(values, dict):
                for k, v in values.items():
                    print(f"  • {k}: {v}")
            elif isinstance(values, (list, np.ndarray)):
                print(f"  • Levels: {np.unique(np.array(values).round(2))}")
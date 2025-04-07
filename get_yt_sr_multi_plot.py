import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from scipy import stats
import pytz
from datetime import datetime, timedelta
from collections import defaultdict
from functools import partial

class SupportResistanceAnalyzer:
    def __init__(self, df):
        self.df = df
        self.results = {}
    
    def fibonacci_levels(self):
        try:
            high = self.df['high'].max()
            low = self.df['low'].min()
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
    
    def pivot_points(self, window=10, significance=3):
        try:
            if len(self.df) < window:
                raise ValueError("Insufficient data for pivot points")
                
            # 使用更平滑的极值检测
            self.df['local_max'] = self.df['high'].rolling(window=window, center=True).apply(
                lambda x: x.max() if (x.argmax() in [window//2-1, window//2]) else np.nan)
            self.df['local_min'] = self.df['low'].rolling(window=window, center=True).apply(
                lambda x: x.min() if (x.argmin() in [window//2-1, window//2]) else np.nan)
            
            # 筛选显著水平
            resistance = self.df['local_max'].dropna()
            support = self.df['local_min'].dropna()
            
            # 合并邻近水平（0.5%以内视为同一水平）
            resistance = self._cluster_levels(resistance, threshold=0.005)
            support = self._cluster_levels(support, threshold=0.005)
            
            self.results['Pivot Points'] = {
                'Support': support,
                'Resistance': resistance
            }
        except Exception as e:
            print(f"Error in pivot_points: {str(e)}")
            self.results['Pivot Points'] = "N/A"
    
    def _cluster_levels(self, levels, threshold=0.005):
        if len(levels) == 0:
            return []
            
        clustered = []
        mean_price = np.mean(levels)
        dynamic_threshold = mean_price * threshold
        
        for level in sorted(levels):
            if not clustered:
                clustered.append([level])
            else:
                last_group = clustered[-1]
                if abs(level - np.mean(last_group)) <= dynamic_threshold:
                    last_group.append(level)
                else:
                    clustered.append([level])
        return [round(np.mean(group), 2) for group in clustered]

    def bollinger_bands(self):
        try:
            window = 20
            if len(self.df) < window:
                raise ValueError("Insufficient data for Bollinger Bands")
                
            close = self.df['close']
            middle = close.rolling(window=window).mean()
            std = close.rolling(window=window).std()
            
            upper = middle + (std * 2)
            lower = middle - (std * 2)
            
            self.results['Bollinger Bands'] = {
                'Support': lower.iloc[-1],
                'Resistance': upper.iloc[-1]
            }
        except Exception as e:
            print(f"Error in bollinger_bands: {str(e)}")
            self.results['Bollinger Bands'] = "N/A"
    
    def kmeans_clusters(self, n_clusters=5):
        try:
            if len(self.df) < n_clusters:
                raise ValueError("Insufficient data for KMeans")
                
            prices = self.df[['close']].values
            kmeans = KMeans(n_clusters=n_clusters).fit(prices)
            levels = sorted([x[0] for x in kmeans.cluster_centers_])
            self.results['KMeans Clusters'] = levels
        except Exception as e:
            print(f"Error in kmeans_clusters: {str(e)}")
            self.results['KMeans Clusters'] = "N/A"
    
    def volume_profile(self, price_step=0.5):
        try:
            if len(self.df) < 20:
                raise ValueError("Insufficient data for Volume Profile")
                
            # 根据价格波动动态设定区间
            price_range = np.arange(
                np.floor(self.df['low'].min()),
                np.ceil(self.df['high'].max()) + price_step,
                price_step
            )
            
            volume_at_price = []
            for i in range(1, len(price_range)):
                mask = (self.df['high'] >= price_range[i-1]) & (self.df['low'] <= price_range[i])
                volume_at_price.append({
                    'price': (price_range[i-1] + price_range[i]) / 2,
                    'volume': self.df[mask]['volume'].sum()
                })
            
            # 寻找成交量显著高于平均的区间
            volumes = [x['volume'] for x in volume_at_price if x['volume'] > 0]
            if not volumes:
                self.results['Volume Profile'] = []
                return
                
            mean_vol = np.mean(volumes)
            std_vol = np.std(volumes)
            significant_levels = [
                x['price'] for x in volume_at_price
                if x['volume'] > mean_vol + std_vol
            ]
            
            self.results['Volume Profile'] = significant_levels
        except Exception as e:
            print(f"Error in volume_profile: {str(e)}")
            self.results['Volume Profile'] = "N/A"
            
    def trendlines(self, window=20, angle_threshold=5):
        try:
            if len(self.df) < window:
                raise ValueError("Insufficient data for Trendlines")
                
            valid_support = []
            valid_resistance = []
            
            # 使用随机采样提高性能
            sample_indices = np.random.choice(
                range(window, len(self.df)),
                size=min(50, len(self.df)-window),
                replace=False
            )
            
            for i in sample_indices:
                # 支撑趋势线
                recent_lows = self.df['low'].iloc[i-window:i]
                slope, intercept = self._robust_regression(recent_lows)
                angle = np.degrees(np.arctan(slope))
                
                if slope < 0 and abs(angle) > angle_threshold:
                    valid_support.append(intercept + slope*(window-1))
                
                # 阻力趋势线
                recent_highs = self.df['high'].iloc[i-window:i]
                slope, intercept = self._robust_regression(recent_highs)
                angle = np.degrees(np.arctan(slope))
                
                if slope > 0 and abs(angle) > angle_threshold:
                    valid_resistance.append(intercept + slope*(window-1))
            
            current_support = np.mean(valid_support[-3:]) if valid_support else None
            current_resistance = np.mean(valid_resistance[-3:]) if valid_resistance else None
                
            self.results['Trendlines'] = {
                'Current Support': current_support,
                'Current Resistance': current_resistance
            }
        except Exception as e:
            print(f"Error in trendlines: {str(e)}")
            self.results['Trendlines'] = "N/A"

    def _robust_regression(self, series):
        """使用改进的Theil-Sen算法"""
        x = np.arange(len(series))
        indices = np.random.choice(len(series), size=min(50, len(series)), replace=False)
        slopes = []
        for i in indices:
            for j in indices:
                if j > i:
                    slopes.append((series.iloc[j] - series.iloc[i]) / (j - i))
        slope = np.median(slopes)
        intercept = np.median(series - slope*x)
        return slope, intercept
        
    def run_all_analysis(self):
        methods = [
            ('Fibonacci', self.fibonacci_levels),
            ('Pivot Points', partial(self.pivot_points, window=10)),
            ('Bollinger Bands', self.bollinger_bands),
            ('KMeans Clusters', partial(self.kmeans_clusters, n_clusters=5)),
            ('Volume Profile', self.volume_profile),
            ('Trendlines', self.trendlines)
        ]
        
        for name, method in methods:
            try:
                method()
            except Exception as e:
                print(f"Method {name} failed: {str(e)}")
                self.results[name] = "N/A"
        
        return self.results

    def get_all_levels(self):
        """Return all support and resistance levels in a structured way"""
        support_levels = []
        resistance_levels = []
        
        # Extract levels from results
        for method, values in self.results.items():
            if values == "N/A":
                continue
                
            if isinstance(values, dict):
                # For methods that return a dict with 'Support' and 'Resistance' keys
                if 'Support' in values:
                    if isinstance(values['Support'], (float, int, np.floating)):
                        support_levels.append((method, values['Support']))
                    elif isinstance(values['Support'], (list, np.ndarray)):
                        for level in values['Support']:
                            support_levels.append((method, level))
                if 'Resistance' in values:
                    if isinstance(values['Resistance'], (float, int, np.floating)):
                        resistance_levels.append((method, values['Resistance']))
                    elif isinstance(values['Resistance'], (list, np.ndarray)):
                        for level in values['Resistance']:
                            resistance_levels.append((method, level))
                            
                # Special case for Fibonacci levels
                if method == 'Fibonacci':
                    for key, value in values.items():
                        if key in ['0%', '23.6%', '38.2%']:
                            resistance_levels.append((f"Fib {key}", value))
                        elif key in ['61.8%', '100%']:
                            support_levels.append((f"Fib {key}", value))
                        elif key == '50%':
                            resistance_levels.append((f"Fib {key}", value))
                            support_levels.append((f"Fib {key}", value))
            
            # For methods that return a list of levels (like KMeans)
            elif isinstance(values, list):
                if values:
                    support_levels.append((method, min(values)))
                    resistance_levels.append((method, max(values)))
                    
            # For methods that return a single value (like Volume Profile)
            elif isinstance(values, (float, int, np.floating)):
                support_levels.append((method, values))
                resistance_levels.append((method, values))
                
        # Calculate importance scores
        level_scores = defaultdict(float)
        current_price = self.df['close'].iloc[-1]
        
        method_weights = {
            'Volume Profile': 2.0,
            'Pivot Points': 1.5,
            'Trendlines': 1.2,
            'Fibonacci': 1.0,
            'Bollinger Bands': 0.8,
            'KMeans Clusters': 0.5
        }
        
        for level_type in ['Support', 'Resistance']:
            levels = support_levels if level_type == 'Support' else resistance_levels
            for method, value in levels:
                weight = method_weights.get(method, 1.0)
                proximity = 1.5 if abs(value - current_price)/current_price < 0.02 else 1.0
                level_scores[(level_type, value)] += weight * proximity
        
        # Merge nearby levels (within 0.5%)
        merged_levels = {'Support': [], 'Resistance': []}
        tolerance = current_price * 0.005
        
        for level_type in ['Support', 'Resistance']:
            levels = support_levels if level_type == 'Support' else resistance_levels
            sorted_levels = sorted(levels, key=lambda x: x[1])
            current_group = []
            
            for method, value in sorted_levels:
                if not current_group:
                    current_group.append((method, value))
                else:
                    last_value = current_group[-1][1]
                    if abs(value - last_value) <= tolerance:
                        current_group.append((method, value))
                    else:
                        # Merge group and keep the most significant
                        best_method = max(
                            [(m, level_scores[(level_type, v)]) for m, v in current_group],
                            key=lambda x: x[1]
                        )[0]
                        merged_value = np.mean([v for _, v in current_group])
                        merged_levels[level_type].append((best_method, round(merged_value, 2)))
                        current_group = [(method, value)]
            
            if current_group:
                best_method = max(
                    [(m, level_scores[(level_type, v)]) for m, v in current_group],
                    key=lambda x: x[1]
                )[0]
                merged_value = np.mean([v for _, v in current_group])
                merged_levels[level_type].append((best_method, round(merged_value, 2)))
        
        return merged_levels

def get_stock_data(ticker, period='5d', interval='15m'):
    ticker = ticker.upper()
    
    try:
        # 獲取資料
        data = yf.download(ticker, period=period, interval=interval,  prepost=True)
        
        if data.empty:
            raise ValueError(f"No data found for ticker {ticker}")
        
        # 修正 MultiIndex (如果需要)
        if isinstance(data.columns, pd.MultiIndex):
            new_data = pd.DataFrame()
            new_data['open'] = data[('Open', ticker)] if ('Open', ticker) in data.columns else data['Open']
            new_data['high'] = data[('High', ticker)] if ('High', ticker) in data.columns else data['High']
            new_data['low'] = data[('Low', ticker)] if ('Low', ticker) in data.columns else data['Low'] 
            new_data['close'] = data[('Close', ticker)] if ('Close', ticker) in data.columns else data['Close']
            new_data['volume'] = data[('Volume', ticker)] if ('Volume', ticker) in data.columns else data['Volume']
            new_data.index = data.index
            data = new_data
        else:
            data.columns = data.columns.str.lower()
            data = data[['open', 'high', 'low', 'close', 'volume']]
        
        # 設置時區(如果時區資訊缺失)
        if data.index.tzinfo is None:
            et_tz = pytz.timezone('America/New_York')
            data.index = data.index.tz_localize('UTC').tz_convert(et_tz)
        else:
            et_tz = pytz.timezone('America/New_York')
            data.index = data.index.tz_convert(et_tz)
            
        # 確保時間排序正確
        data = data.sort_index(ascending=True)
        
        return data
        
    except Exception as e:
        raise ValueError(f"Error downloading data for {ticker}: {str(e)}")

def create_stock_chart_with_sr(ticker_symbol, period='5d', interval='15m'):
    try:
        # 獲取數據
        df = get_stock_data(ticker_symbol, period=period, interval=interval)
        
        # 運行支撐阻力分析
        analyzer = SupportResistanceAnalyzer(df)
        results = analyzer.run_all_analysis()
        
        # 獲取所有支撐阻力水平
        sr_levels = analyzer.get_all_levels()
        
        # 準備資料用於繪圖
        hist = df.copy()
        hist.index.name = 'Datetime'
        hist.reset_index(inplace=True)
        
        # 計算蠟燭圖顏色
        hist['Color'] = ['green' if c >= o else 'red' for c, o in zip(hist['close'], hist['open'])]
        
        # 創建子圖 (上方 K 線圖，下方成交量)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.05, row_heights=[0.7, 0.3])
        
        # 添加 K 線圖
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
        
        # 添加成交量圖
        fig.add_trace(go.Bar(
            x=hist["Datetime"],
            y=hist['volume'],
            marker=dict(color=hist['Color']),
            opacity=0.3,
            name="Volume"
        ), row=2, col=1)
        
        # 添加時間間隔線
        for i, time in enumerate(hist["Datetime"]):
            if i == 0 or i == len(hist)-1:
                continue
                
            minute = time.minute
            if minute == 0:  # 每小時標記
                fig.add_shape(type="line",
                          x0=time, y0=0,
                          x1=time, y1=1,
                          xref='x', yref='paper',
                          line=dict(color="white", width=0.5, dash="dot"))
        




        # 获取所有唯一的日期（处理多日数据）
        unique_dates = pd.to_datetime(hist["Datetime"].dt.date.unique())

        for date in unique_dates:
            # 盘前时段（4:00 - 9:30 ET）
            pre_market_start = pd.to_datetime(f"{date.strftime('%Y-%m-%d')} 04:00:00").tz_localize("America/New_York")
            pre_market_end = pd.to_datetime(f"{date.strftime('%Y-%m-%d')} 09:30:00").tz_localize("America/New_York")
            
            # 盘后时段（16:00 - 20:00 ET）
            post_market_start = pd.to_datetime(f"{date.strftime('%Y-%m-%d')} 16:00:00").tz_localize("America/New_York")
            post_market_end = pd.to_datetime(f"{date.strftime('%Y-%m-%d')} 20:00:00").tz_localize("America/New_York")
            
            # 添加背景色
            fig.add_vrect(
                x0=pre_market_start, x1=pre_market_end,
                fillcolor="yellow", opacity=0.2,
                layer="below", line_width=0,
                row="all", col="all"
            )
            fig.add_vrect(
                x0=post_market_start, x1=post_market_end,
                fillcolor="navy", opacity=0.2,
                layer="below", line_width=0,
                row="all", col="all"
            )





        # 添加支撐位水平線
        support_colors = ['#00FFFF', '#00BFFF', '#1E90FF', '#0000FF', '#00008B']
        for i, (method, level) in enumerate(sr_levels['Support'][:5]):  # 限制顯示前5個支撐位
            if level is None or np.isnan(level):
                continue
                
            color_idx = min(i, len(support_colors)-1)
            fig.add_shape(type="line",
                          x0=hist["Datetime"].iloc[0], y0=level,
                          x1=hist["Datetime"].iloc[-1], y1=level,
                          line=dict(color=support_colors[color_idx], width=1.5, dash="solid"),
                          opacity=0.7,
                          row=1, col=1)
            fig.add_annotation(
                x=hist["Datetime"].iloc[-1], y=level,
                text=f"S: {method} ({level:.2f})",
                showarrow=False,
                xanchor="right",
                font=dict(color=support_colors[color_idx], size=10),
                row=1, col=1
            )
        
        # 添加阻力位水平線
        resistance_colors = ['#FFC0CB', '#F08080', '#FA8072', '#FF6347', '#FF0000']
        for i, (method, level) in enumerate(sr_levels['Resistance'][:5]):  # 限制顯示前5個阻力位
            if level is None or np.isnan(level):
                continue
                
            color_idx = min(i, len(resistance_colors)-1)
            fig.add_shape(type="line",
                          x0=hist["Datetime"].iloc[0], y0=level,
                          x1=hist["Datetime"].iloc[-1], y1=level,
                          line=dict(color=resistance_colors[color_idx], width=1.5, dash="solid"),
                          opacity=0.7,
                          row=1, col=1)
            fig.add_annotation(
                x=hist["Datetime"].iloc[-1], y=level,
                text=f"R: {method} ({level:.2f})",
                showarrow=False,
                xanchor="right",
                font=dict(color=resistance_colors[color_idx], size=10),
                row=1, col=1
            )

        # 标记盘前时段（美东时间 4:00 - 9:30）
        pre_market_start = hist["Datetime"].iloc[0].replace(hour=4, minute=0, second=0)
        pre_market_end = hist["Datetime"].iloc[0].replace(hour=9, minute=30, second=0)
        fig.add_vrect(
            x0=pre_market_start, x1=pre_market_end,
            fillcolor="yellow", opacity=0.2,
            layer="below", line_width=0,
            row="all", col="all"
        )

        # 标记盘后时段（美东时间 16:00 - 20:00）
        post_market_start = hist["Datetime"].iloc[0].replace(hour=16, minute=0, second=0)
        post_market_end = hist["Datetime"].iloc[0].replace(hour=20, minute=0, second=0)
        fig.add_vrect(
            x0=post_market_start, x1=post_market_end,
            fillcolor="navy", opacity=0.2,
            layer="below", line_width=0,
            row="all", col="all"
        )
        
        # 設定 TradingView 風格
        fig.update_layout(
            title=f'{ticker_symbol.upper()} {period} {interval} Chart with Support/Resistance (ET)',
            xaxis_title='Time (ET)',
            yaxis_title='Price ($)',
            xaxis_rangeslider_visible=False,
            paper_bgcolor="black",
            plot_bgcolor="#0F1B2A",
            font=dict(color="white"),
            xaxis=dict(
                gridcolor="rgba(255, 255, 255, 0.2)",
                showticklabels=True
            ),
            yaxis=dict(gridcolor="rgba(255, 255, 255, 0.2)"),
            yaxis2=dict(gridcolor="rgba(255, 255, 255, 0.2)"),
            margin=dict(l=50, r=50, t=80, b=50),
            height=800
        )
        
        # 返回圖表和分析結果
        return fig, results
        
    except Exception as e:
        print(f"Error creating chart: {str(e)}")
        return None, None

if __name__ == "__main__":
    # 設定股票代碼和參數
    stock_symbol = 'icct'  # 可以更改為其他股票代碼
    time_period = '3d'     # 推薦使用更長的時間範圍
    time_interval = '5m'  # 推薦使用15分鐘線
    
    try:
        # 創建圖表和獲取分析結果
        fig, results = create_stock_chart_with_sr(stock_symbol, period=time_period, interval=time_interval)
        
        if fig is None:
            raise ValueError("Failed to create chart")
        
        # 顯示圖表
        fig.show()
        
        # 輸出支撐阻力分析報告
        print(f"\n📈 Support & Resistance Analysis Report for {stock_symbol}")
        print("="*60)
        for method, values in results.items():
            if values == "N/A":
                print(f"\n🔍 {method}: Not available")
                continue
                
            print(f"\n🔍 {method}:")
            if isinstance(values, dict):
                for k, v in values.items():
                    if isinstance(v, (float, np.floating)):
                        print(f"  • {k}: {v:.2f}")
                    elif isinstance(v, (list, np.ndarray)):
                        print(f"  • {k}: {np.unique(np.array(v).round(2))}")
                    else:
                        print(f"  • {k}: {v}")
            elif isinstance(values, list):
                print(f"  • Levels: {np.unique(np.array(values).round(2))}")
            elif isinstance(values, (float, int, np.floating)):
                print(f"  • Value: {values:.2f}")
                
    except Exception as e:
        print(f"Error in main execution: {str(e)}")
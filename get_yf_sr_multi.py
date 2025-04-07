import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from scipy import stats
from datetime import datetime, timedelta

# 1. 改進的數據獲取函數 - 增加回溯天數和錯誤處理
def get_1min_data(ticker, days_back=7):  # 預設回溯7天獲取更多數據
    ticker = ticker.upper()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    print(f"正在獲取 {ticker} 從 {start_date.date()} 到 {end_date.date()} 的1分鐘K線...")
    
    data = yf.download(
        tickers=ticker,
        start=start_date,
        end=end_date,
        interval='1m'
    )
    
    if len(data) == 0:
        print(f"警告: 無法獲取 {ticker} 的1分鐘數據，嘗試獲取日線數據...")
        # 嘗試獲取日線數據作為備用
        data = yf.download(
            tickers=ticker,
            start=start_date - timedelta(days=30),  # 獲取更長時間的日線數據
            end=end_date,
            interval='1d'
        )
    
    data = data.dropna()
    print(f"成功獲取 {len(data)} 根K線")
    
    # 修復 yfinance 的 MultiIndex 列
    if isinstance(data.columns, pd.MultiIndex):
        # 創建新的 DataFrame 並正確命名列
        new_data = pd.DataFrame()
        new_data['open'] = data[('Open', ticker)]
        new_data['high'] = data[('High', ticker)]
        new_data['low'] = data[('Low', ticker)]
        new_data['close'] = data[('Close', ticker)]
        new_data['volume'] = data[('Volume', ticker)]
        return new_data
    else:
        # 如果已經是標準 Index
        data.columns = data.columns.str.lower()
        return data[['open', 'high', 'low', 'close', 'volume']]

# 2. 支撐阻力分析類 - 添加數據檢查和動態調整
class SupportResistanceAnalyzer:
    def __init__(self, df):
        self.df = df
        self.results = {}
        self.min_data_required = 20  # 大多數方法需要的最小資料量
    
    def _check_data_sufficiency(self, min_samples=5):
        """檢查是否有足夠的數據進行分析"""
        return len(self.df) >= min_samples
    
    def fibonacci_levels(self):
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
    
    def pivot_points(self):
        # 動態調整窗口大小，確保不大於可用數據量的1/3
        window = min(5, max(2, len(self.df) // 3))
        
        if not self._check_data_sufficiency(window * 2):
            print(f"數據不足，無法計算樞軸點")
            return
            
        self.df['local_max'] = self.df['high'].rolling(window=window, center=True).max()
        self.df['local_min'] = self.df['low'].rolling(window=window, center=True).min()
        
        resistance = self.df[self.df['high'] == self.df['local_max']]['high'].dropna().unique()
        support = self.df[self.df['low'] == self.df['local_min']]['low'].dropna().unique()
        
        if len(resistance) > 0 and len(support) > 0:
            self.results['Pivot Points'] = {'Support': support, 'Resistance': resistance}
        else:
            print("無法識別有效的樞軸點")

    def bollinger_bands(self):
        # 動態調整窗口大小
        window = min(20, max(5, len(self.df) // 2))
        
        if not self._check_data_sufficiency(window):
            print(f"數據不足，無法計算布林帶")
            return
            
        close = self.df['close']
        
        # 計算中間帶 (SMA)
        middle = close.rolling(window=window).mean()
        
        # 計算標準差
        std = close.rolling(window=window).std()
        
        # 計算上下帶 (2個標準差)
        upper = middle + (std * 2)
        lower = middle - (std * 2)
        
        # 存儲最新值
        if not pd.isna(upper.iloc[-1]) and not pd.isna(lower.iloc[-1]):
            self.results['Bollinger Bands'] = {
                'Support': lower.iloc[-1],
                'Resistance': upper.iloc[-1]
            }
    
    def kmeans_clusters(self):
        # 動態調整聚類數量
        n_clusters = min(5, max(2, len(self.df) // 10))
        
        if not self._check_data_sufficiency(n_clusters * 2):
            print(f"數據不足，無法進行K-means聚類")
            return
            
        prices = self.df[['close']].values
        kmeans = KMeans(n_clusters=n_clusters).fit(prices)
        levels = sorted([float(x[0]) for x in kmeans.cluster_centers_])
        self.results['KMeans Clusters'] = levels
    
    def volume_profile(self):
        # 動態調整分箱數量
        bins = min(20, max(3, len(self.df) // 5))
        
        if not self._check_data_sufficiency(bins * 2):
            print(f"數據不足，無法計算成交量分布")
            return
            
        low = self.df['low'].min()
        high = self.df['high'].max()
        price_range = np.linspace(low, high, bins)
        
        volume_dist = []
        for i in range(1, len(price_range)):
            mask = (self.df['low'] >= price_range[i-1]) & (self.df['high'] <= price_range[i])
            volume_dist.append(self.df[mask]['volume'].sum())
        
        if sum(volume_dist) > 0:  # 確保有成交量數據
            max_vol_level = price_range[np.argmax(volume_dist)]
            self.results['Volume Profile'] = float(max_vol_level)
    
    def trendlines(self):
        # 動態調整窗口大小
        window = min(20, max(5, len(self.df) // 3))
        
        if not self._check_data_sufficiency(window * 2):
            print(f"數據不足，無法計算趨勢線")
            return
            
        x = np.arange(window)
        support = []
        resistance = []
        
        for i in range(window, len(self.df)):
            recent_lows = self.df['low'].iloc[i-window:i].values
            recent_highs = self.df['high'].iloc[i-window:i].values
            
            # 僅在數據無缺失值時進行計算
            if not np.isnan(recent_lows).any() and not np.isnan(recent_highs).any():
                slope_low, intercept_low = stats.linregress(x, recent_lows)[:2]
                support.append(intercept_low + slope_low*(window-1))
                
                slope_high, intercept_high = stats.linregress(x, recent_highs)[:2]
                resistance.append(intercept_high + slope_high*(window-1))
        
        if support and resistance:  # 確保列表非空
            self.results['Trendlines'] = {
                'Current Support': float(support[-1]),
                'Current Resistance': float(resistance[-1])
            }
    
    def smart_money_levels(self):
        if not self._check_data_sufficiency(5):
            print(f"數據不足，無法計算聰明錢水平")
            return
            
        self.df['vwap'] = self.df['volume'] * (self.df['high'] + self.df['low'] + self.df['close'])/3
        self.df['vwap'] = self.df['vwap'].cumsum() / self.df['volume'].cumsum()
        
        # 尋找成交量堆積區
        window = min(20, max(3, len(self.df) // 3))
        
        support = self.df['low'].rolling(window).min().dropna()
        resistance = self.df['high'].rolling(window).max().dropna()
        
        if len(support) > 0 and len(resistance) > 0:
            self.results['Smart Money'] = {
                'Support': float(support.iloc[-1]),
                'Resistance': float(resistance.iloc[-1])
            }
    
    def run_all_analysis(self):
        if len(self.df) < 3:
            print("警告: 數據量過少，無法進行有效分析。請嘗試獲取更多數據。")
            self.results['Error'] = "數據不足"
            return self.results
            
        methods = [
            self.fibonacci_levels,
            self.pivot_points,
            self.bollinger_bands,
            self.kmeans_clusters,
            self.volume_profile,
            self.trendlines,
            self.smart_money_levels
        ]
        
        for method in methods:
            try:
                method()
            except Exception as e:
                print(f"錯誤在 {method.__name__}: {str(e)}")
        
        return self.results

# 3. 改進的結果格式化輸出 - 添加NaN值處理
def format_results(results):
    if 'Error' in results:
        return f"\n⚠️ 分析失敗: {results['Error']}\n"
        
    output = "\n📈 支撐阻力分析報告\n"
    output += "="*50 + "\n"
    
    # 收集所有有效水平線
    all_levels = []
    
    for method, values in results.items():
        output += f"\n🔍 {method}:\n"
        
        if isinstance(values, dict):
            for k, v in values.items():
                if isinstance(v, (float, np.floating)):
                    output += f"  • {k}: {v:.4f}\n"
                    # 只收集有效的數值
                    if not pd.isna(v):
                        all_levels.append(float(v))
                elif isinstance(v, np.ndarray):
                    valid_values = v[~np.isnan(v)]  # 過濾NaN值
                    if len(valid_values) > 0:
                        output += f"  • {k}: {np.unique(valid_values.round(4))}\n"
                        all_levels.extend([float(x) for x in valid_values])
                else:
                    output += f"  • {k}: {v}\n"
        else:
            if isinstance(values, list):
                valid_values = [x for x in values if not pd.isna(x)]
                if valid_values:
                    output += f"  • Levels: {np.unique(np.array(valid_values).round(4))}\n"
                    all_levels.extend([float(x) for x in valid_values])
            elif not pd.isna(values):
                output += f"  • Value: {values:.4f}\n"
                all_levels.append(float(values))
    
    # 生成綜合建議
    if len(all_levels) >= 3:
        try:
            # 過濾所有NaN值並確保列表非空
            all_levels = [x for x in all_levels if not pd.isna(x)]
            
            if len(all_levels) >= 3:
                n_clusters = min(3, len(all_levels) // 2)
                cluster = KMeans(n_clusters=n_clusters).fit(np.array(all_levels).reshape(-1,1))
                key_levels = sorted([float(x[0]) for x in cluster.cluster_centers_])
                
                output += "\n🎯 關鍵共識水平:\n"
                output += f"  • 強支撐: {min(key_levels):.4f}\n"
                output += f"  • 樞軸區: {np.median(key_levels):.4f}\n"
                output += f"  • 強阻力: {max(key_levels):.4f}\n"
            else:
                output += "\n⚠️ 數據點不足，無法生成共識水平\n"
        except Exception as e:
            output += f"\n⚠️ 生成共識水平時出錯: {str(e)}\n"
    else:
        output += "\n⚠️ 數據點不足，無法生成共識水平\n"
    
    return output

# 主程序
if __name__ == "__main__":
    # 參數設置
    TICKER = 'aapl'  # 更改為你要分析的股票代碼
    DAYS_BACK = 14   # 回溯14天以獲取更多數據
    
    # 獲取數據
    df = get_1min_data(TICKER, days_back=DAYS_BACK)
    print(f"獲取到 {len(df)} 根K線用於分析")
    
    if len(df) < 20:
        print(f"警告: 數據量可能不足以進行全面分析 (僅有 {len(df)} 根K線)")
    
    # 運行分析
    analyzer = SupportResistanceAnalyzer(df)
    results = analyzer.run_all_analysis()
    
    # 生成報告
    report = format_results(results)
    print(report)
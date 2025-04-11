


import os
import requests
import pandas as pd
from dotenv import load_dotenv
import time
from datetime import datetime, timedelta

# 加载.env文件中的环境变量
load_dotenv()
API_KEY = os.getenv("FMP_KEY")  # 请在.env文件中添加FINNHUB_API_KEY

BASE_URL = "https://finnhub.io/api/v1"

class FinnhubAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.request_count = 0
        self.last_request_time = time.time()
    
    def _rate_limit(self):
        """确保不超过API调用限制 (免费账户60次/分钟)"""
        current_time = time.time()
        if current_time - self.last_request_time < 60 and self.request_count >= 60:
            wait_time = 60 - (current_time - self.last_request_time)
            print(f"达到API限制，等待 {wait_time:.2f} 秒...")
            time.sleep(wait_time)
            self.request_count = 0
            self.last_request_time = time.time()
        elif current_time - self.last_request_time >= 60:
            self.request_count = 0
            self.last_request_time = current_time
    
    def get_data(self, endpoint, **params):
        """发送请求到Finnhub API"""
        self._rate_limit()
        
        headers = {
            "X-Finnhub-Token": self.api_key
        }
        
        url = f"{BASE_URL}/{endpoint}"
        response = requests.get(url, headers=headers, params=params)
        self.request_count += 1
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"错误: {response.status_code}")
            print(response.text)
            return None
    
    def get_stock_candles(self, symbol, resolution="D", from_date=None, to_date=None):
        """获取股票K线数据
        resolution参数: 1, 5, 15, 30, 60, D, W, M (分钟和日/周/月)
        """
        if from_date is None:
            # 默认获取过去30天数据
            from_date = int((datetime.now() - timedelta(days=30)).timestamp())
        
        if to_date is None:
            to_date = int(datetime.now().timestamp())
            
        data = self.get_data(
            "stock/candle", 
            symbol=symbol,
            resolution=resolution,
            from_=from_date,
            to=to_date
        )
        
        if data and data.get("s") == "ok":
            df = pd.DataFrame({
                "timestamp": data["t"],
                "open": data["o"],
                "high": data["h"],
                "low": data["l"],
                "close": data["c"],
                "volume": data["v"]
            })
            # 转换时间戳为日期
            df["date"] = pd.to_datetime(df["timestamp"], unit="s")
            df["symbol"] = symbol
            return df
        return None
    
    def get_quote(self, symbol):
        """获取股票实时报价"""
        data = self.get_data("quote", symbol=symbol)
        
        if data:
            return data
        return None
    
    def get_symbol_lookup(self, query):
        """搜索股票代码"""
        data = self.get_data("search", q=query)
        
        if data and "result" in data:
            return pd.DataFrame(data["result"])
        return None
    
    def get_market_news(self, category="general", min_id=0):
        """获取市场新闻
        category: general, forex, crypto, merger
        """
        data = self.get_data("news", category=category, minId=min_id)
        
        if data:
            return pd.DataFrame(data)
        return None
    
    def get_company_news(self, symbol, from_date=None, to_date=None):
        """获取公司新闻"""
        if from_date is None:
            from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        if to_date is None:
            to_date = datetime.now().strftime("%Y-%m-%d")
            
        data = self.get_data(
            "company-news",
            symbol=symbol,
            from_=from_date,
            to=to_date
        )
        
        if data:
            return pd.DataFrame(data)
        return None
    
    def get_peers(self, symbol):
        """获取同行业公司"""
        data = self.get_data("stock/peers", symbol=symbol)
        
        if data:
            return data
        return None
    
    def get_gainers_losers(self):
        """通过获取大量股票并排序来模拟获取涨跌幅最大的股票
        (Finnhub免费API没有直接的top gainers/losers端点)
        """
        # 常见股票列表 (可以根据需要扩展)
        symbols = ["AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "NVDA", "JPM", "BAC", "WMT", 
                  "PFE", "DIS", "NFLX", "INTC", "AMD", "BA", "XOM", "CVX", "PG", "KO"]
        
        quotes = []
        for symbol in symbols:
            quote = self.get_quote(symbol)
            if quote:
                quote["symbol"] = symbol
                quotes.append(quote)
            time.sleep(0.1)  # 避免过快请求
            
        if quotes:
            df = pd.DataFrame(quotes)
            gainers = df.sort_values("dp", ascending=False)  # dp是百分比变化
            losers = df.sort_values("dp", ascending=True)
            return {
                "gainers": gainers,
                "losers": losers,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        return None

# 使用示例
if __name__ == "__main__":
    if not API_KEY:
        print("错误: 没有在.env文件中找到FINNHUB_API_KEY")
        exit(1)
    
    finnhub = FinnhubAPI(API_KEY)
    
    # 示例1: 获取股票行情
    symbol = "AAPL"
    print(f"获取{symbol}的实时报价...")
    quote = finnhub.get_quote(symbol)
    if quote:
        print(f"当前价格: {quote.get('c', 'N/A')}")
        print(f"今日变动: {quote.get('d', 'N/A')} ({quote.get('dp', 'N/A')}%)")
        print(f"今日开盘: {quote.get('o', 'N/A')}")
        print(f"今日最高: {quote.get('h', 'N/A')}")
        print(f"今日最低: {quote.get('l', 'N/A')}")
        print(f"上一收盘: {quote.get('pc', 'N/A')}")
    
    # 示例2: 获取K线数据
    print(f"\n获取{symbol}的每日K线数据(最近30天)...")
    candles = finnhub.get_stock_candles(symbol)
    if candles is not None:
        print(candles.tail())
    
    # 示例3: 搜索股票代码
    search_term = "TESLA"
    print(f"\n搜索股票: {search_term}")
    results = finnhub.get_symbol_lookup(search_term)
    if results is not None and not results.empty:
        print(results[["symbol", "description", "type"]])
    
    # 示例4: 获取市场新闻
    print("\n获取最新市场新闻...")
    news = finnhub.get_market_news(category="general")
    if news is not None and not news.empty:
        print(news[["headline", "datetime", "source"]].head())
    
    # 示例5: 获取同行业公司
    print(f"\n获取{symbol}的同行业公司...")
    peers = finnhub.get_peers(symbol)
    if peers:
        print(peers)
    
    # 示例6: 模拟获取涨跌幅最大的股票
    print("\n获取涨跌幅最大的股票...")
    gainer_loser = finnhub.get_gainers_losers()
    if gainer_loser:
        print("\n涨幅最大的5只股票:")
        print(gainer_loser["gainers"].head()[["symbol", "c", "d", "dp"]])
        
        print("\n跌幅最大的5只股票:")
        print(gainer_loser["losers"].head()[["symbol", "c", "d", "dp"]])
        
        print(f"\n数据更新时间: {gainer_loser['last_updated']}")
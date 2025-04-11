import os
import requests
import pandas as pd
from dotenv import load_dotenv
import time
from datetime import datetime

# 載入.env檔案中的環境變數
load_dotenv()
API_KEY = os.getenv("ALPHA_VANTAGE_KEY")

BASE_URL = "https://www.alphavantage.co/query"

class AlphaVantageAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.request_count = 0
        self.last_request_time = time.time()
    
    def _rate_limit(self):
        """確保不超過API調用限制 (5次/分鐘)"""
        current_time = time.time()
        if current_time - self.last_request_time < 60 and self.request_count >= 5:
            wait_time = 60 - (current_time - self.last_request_time)
            print(f"達到API限制，等待 {wait_time:.2f} 秒...")
            time.sleep(wait_time)
            self.request_count = 0
            self.last_request_time = time.time()
        elif current_time - self.last_request_time >= 60:
            self.request_count = 0
            self.last_request_time = current_time
    
    def get_data(self, function, **params):
        """發送請求到Alpha Vantage API"""
        self._rate_limit()
        
        query_params = {
            "function": function,
            "apikey": self.api_key,
            **params
        }
        
        response = requests.get(BASE_URL, params=query_params)
        self.request_count += 1
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"錯誤: {response.status_code}")
            print(response.text)
            return None
    
    def get_daily(self, symbol, outputsize="compact"):
        """獲取每日股票數據"""
        data = self.get_data(
            "TIME_SERIES_DAILY", 
            symbol=symbol,
            outputsize=outputsize
        )
        
        if data and "Time Series (Daily)" in data:
            df = pd.DataFrame(data["Time Series (Daily)"]).T
            # 轉換列名
            df.columns = [col.split(". ")[1] for col in df.columns]
            # 轉換數據類型
            for col in df.columns:
                df[col] = pd.to_numeric(df[col])
            # 添加日期和代碼列
            df.index = pd.to_datetime(df.index)
            df["symbol"] = symbol
            return df
        return None
    
    def get_top_gainers_losers(self):
        """獲取漲跌幅最大的股票"""
        data = self.get_data("TOP_GAINERS_LOSERS")
        
        if data and "top_gainers" in data:
            gainers_df = pd.DataFrame(data["top_gainers"])
            losers_df = pd.DataFrame(data["most_actively_traded"])
            return {
                "gainers": gainers_df,
                "most_active": losers_df,
                "last_updated": data.get("last_updated", "")
            }
        return None
    
    def get_quote(self, symbol):
        """獲取股票實时报價"""
        data = self.get_data("GLOBAL_QUOTE", symbol=symbol)
        
        if data and "Global Quote" in data:
            return data["Global Quote"]
        return None
    
    def search_symbol(self, keywords):
        """搜尋股票代碼"""
        data = self.get_data("SYMBOL_SEARCH", keywords=keywords)
        
        if data and "bestMatches" in data:
            return pd.DataFrame(data["bestMatches"])
        return None

# 使用示例
if __name__ == "__main__":
    if not API_KEY:
        print("錯誤: 沒有在.env文件中找到ALPHA_VANTAGE_KEY")
        exit(1)
    
    alpha = AlphaVantageAPI(API_KEY)
    
    # 示例1: 獲取漲幅最大的股票
    print("獲取漲幅最大的股票...")
    top_stocks = alpha.get_top_gainers_losers()
    if top_stocks:
        print("\n前5個漲幅最大的股票:")
        print(top_stocks["gainers"].head()[["ticker", "price", "change_percentage"]])
        
        print("\n前5個交易最活躍的股票:")
        print(top_stocks["most_active"].head()[["ticker", "price", "change_percentage"]])
        
        print(f"\n數據更新時間: {top_stocks['last_updated']}")
    
    # 示例2: 獲取特定股票的每日數據
    symbol = "AAPL"
    print(f"\n獲取{symbol}的每日數據...")
    daily_data = alpha.get_daily(symbol)
    if daily_data is not None:
        print(daily_data.head())
    
    # 示例3: 獲取實时报價
    print(f"\n獲取{symbol}的實时报價...")
    quote = alpha.get_quote(symbol)
    if quote:
        print(f"當前價格: {quote.get('05. price', 'N/A')}")
        print(f"變動: {quote.get('09. change', 'N/A')} ({quote.get('10. change percent', 'N/A')})")
    
    # 示例4: 搜尋股票代碼
    search_term = "TESLA"
    print(f"\n搜尋股票: {search_term}")
    results = alpha.search_symbol(search_term)
    if results is not None and not results.empty:
        print(results[["1. symbol", "2. name", "4. region"]])
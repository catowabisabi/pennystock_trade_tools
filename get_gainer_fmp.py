import os
import json
import certifi
from urllib.request import urlopen
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

class StockGainers:
    def __init__(self, 
                 min_price=0.9, max_price=10, 
                 min_pct=30, max_pct=1000):
        self.api_key = os.getenv("FMP_KEY")
        self.url = f"https://financialmodelingprep.com/api/v3/stock_market/gainers?apikey={self.api_key}"
        self.min_price = min_price
        self.max_price = max_price
        self.min_pct = min_pct
        self.max_pct = max_pct
        self.df = None

    def fetch_data(self):
        response = urlopen(self.url)
        data = json.loads(response.read().decode("utf-8"))
        self.df = pd.DataFrame(data)
        return self

    def clean_and_filter(self):
        if self.df is None:
            raise ValueError("Data not loaded. Please run fetch_data() first.")

        # 過濾欄位
        self.df = self.df[['symbol', 'change', 'price', 'changesPercentage']]

        # 篩選價格與漲幅
        self.df = self.df[
            (self.df['price'] >= self.min_price) &
            (self.df['price'] <= self.max_price) &
            (self.df['changesPercentage'] >= self.min_pct) &
            (self.df['changesPercentage'] <= self.max_pct)
        ]

        # 重新命名欄位
        self.df = self.df.rename(columns={
            'symbol': 'SYMBOL',
            'change': '$CHG',
            'price': 'PRICE',
            'changesPercentage': '%CHG'
        })

        # 百分比欄位格式化
        self.df['%CHG'] = self.df['%CHG'].map(lambda x: f"{x:.2f}%")
        return self

    def show(self):
        if self.df is not None:
            print(self.df)
        else:
            print("No data to display.")

sg = StockGainers(min_price=0.5, max_price=20, min_pct=30, max_pct=500)
sg.fetch_data().clean_and_filter().show()

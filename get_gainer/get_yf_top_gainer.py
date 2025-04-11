import requests
import pandas as pd
from io import StringIO

def get_top_gainers(count=10):
    url = "https://finance.yahoo.com/gainers"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    
    # 修复：使用StringIO包装响应内容
    tables = pd.read_html(StringIO(response.text))
    
    # 尝试不同的列名组合（Yahoo Finance可能更改列名）
    possible_columns = {
        '% Change': ['% Change', 'Change %', 'Change'],
        'Price (Intraday)': ['Price (Intraday)', 'Price', 'Last Price']
    }
    
    for table in tables:
        # 检查是否包含关键列
        change_col = next((col for col in possible_columns['% Change'] if col in table.columns), None)
        price_col = next((col for col in possible_columns['Price (Intraday)'] if col in table.columns), None)
        
        if change_col and price_col:
            # 标准化列名
            table = table.rename(columns={
                change_col: '% Change',
                price_col: 'Price'
            })
            return table[['Symbol', 'Name', 'Price', '% Change']].head(count)
    
    raise ValueError("无法从页面中解析涨幅数据")

# 示例调用
try:
    top_10 = get_top_gainers(10)
    print(top_10.to_string(index=False))
except Exception as e:
    print(f"错误: {e}")
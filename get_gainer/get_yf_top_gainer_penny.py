import requests
import pandas as pd
from io import StringIO
import re

def get_penny_stocks(price_max=5.0, count=20):
    """
    從Yahoo Finance獲取低價股（Penny Stocks）列表
    :param price_max: 最高股價（默認≤5美元）
    :param count: 返回結果數量
    """
    # 使用penny_stocks篩選器，但也可以嘗試其他URL
    #url = "https://finance.yahoo.com/screener/predefined/penny_stocks"
    url = "https://finance.yahoo.com/research-hub/screener/most_active_penny_stocks/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    
    # 使用StringIO包裝響應內容
    tables = pd.read_html(StringIO(response.text))
    
    # 嘗試不同的列名組合（Yahoo Finance可能更改列名）
    possible_columns = {
        'Symbol': ['Symbol', 'Ticker', 'symbol'],
        'Name': ['Name', 'Company', 'Company Name'],
        'Price': ['Price (Intraday)', 'Price', 'Last Price'],
        '% Change': ['% Change', 'Change %', 'Change']
    }
    
    for table in tables:
        # 檢查是否包含必要列
        symbol_col = next((col for col in possible_columns['Symbol'] if col in table.columns), None)
        name_col = next((col for col in possible_columns['Name'] if col in table.columns), None)
        price_col = next((col for col in possible_columns['Price'] if col in table.columns), None)
        
        if symbol_col and price_col:
            # 標準化列名
            rename_map = {
                symbol_col: 'Symbol',
                price_col: 'Price'
            }
            
            if name_col:
                rename_map[name_col] = 'Name'
                
            change_col = next((col for col in possible_columns['% Change'] if col in table.columns), None)
            if change_col:
                rename_map[change_col] = '% Change'
                
            table = table.rename(columns=rename_map)
            
            # 確保Price列是數值型
            if isinstance(table['Price'].iloc[0], str):
                # 使用正則表達式提取數字
                table['Price'] = table['Price'].apply(
                    lambda x: float(re.search(r'(\d+\.\d+)', str(x)).group(1)) if re.search(r'(\d+\.\d+)', str(x)) else None
                )
            
            # 篩選價格 <= price_max 的股票
            penny_stocks = table[table['Price'] <= price_max].copy()
            
            # 選擇需要的列
            required_cols = ['Symbol', 'Price']
            if 'Name' in penny_stocks.columns:
                required_cols.insert(1, 'Name')
            if '% Change' in penny_stocks.columns:
                required_cols.append('% Change')
                
            return penny_stocks[required_cols].head(count)
    
    raise ValueError("無法從頁面中解析Penny Stocks數據")

def get_realtime_penny_gainers(price_max=1.0, count=10):
    """
    獲取實時上漲的低價股（Penny Stocks）
    :param price_max: 最高股價（默認≤1美元）
    :param count: 返回結果數量
    """
    # 先從Penny Stocks篩選器獲取基礎數據
    try:
        penny_stocks = get_penny_stocks(price_max=price_max, count=100)  # 獲取更多股票以便後續篩選
        
        # 確保存在% Change列
        if '% Change' not in penny_stocks.columns:
            print("警告: 無法獲取漲跌幅數據，只返回價格低於閾值的股票")
            return penny_stocks.head(count)
            
        # 提取%變化的純數字值（去除百分比符號）
        if isinstance(penny_stocks['% Change'].iloc[0], str):
            penny_stocks['% Change'] = penny_stocks['% Change'].apply(
                lambda x: float(re.search(r'([+-]?\d+\.\d+)', str(x)).group(1)) if re.search(r'([+-]?\d+\.\d+)', str(x)) else 0
            )
        
        # 篩選出上漲的股票並按漲幅排序
        gainers = penny_stocks[penny_stocks['% Change'] > 0].sort_values('% Change', ascending=False)
        
        # 格式化結果
        if 'Name' in gainers.columns:
            gainers['Name'] = gainers['Name'].apply(lambda x: str(x)[:30] if len(str(x)) > 30 else str(x))
            
        gainers['Price'] = gainers['Price'].round(2)
        
        if not gainers.empty:
            return gainers.head(count)
        else:
            print("未找到符合條件的上漲低價股")
            return penny_stocks.head(count)
            
    except Exception as e:
        print(f"獲取實時低價股數據時出錯: {e}")
        # 如果失敗，嘗試只獲取常規的penny stocks
        return get_penny_stocks(price_max=price_max, count=count)

# 測試運行
if __name__ == "__main__":
    try:
        # 獲取價格低於5美元的penny stocks
        print("\n== 所有價格低於5美元的Penny Stocks ==")
        penny_stocks = get_penny_stocks(price_max=5.0, count=10)
        print(penny_stocks.to_string(index=False))
        
        print("\n== 價格低於1美元且正在上漲的Penny Stocks ==")
        penny_gainers = get_realtime_penny_gainers(price_max=1.0, count=10)
        print(penny_gainers.to_string(index=False))
        
    except Exception as e:
        print(f"錯誤: {e}")
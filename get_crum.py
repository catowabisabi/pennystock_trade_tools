from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import requests
import pandas as pd

# 取得 crumb 和 cookies
def get_crumb_and_cookies(stock: str):
    options = Options()
    options.add_argument('--headless')  # 無頭模式
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)
    driver.get(f"https://finance.yahoo.com/quote/{stock}/history")
    
    try:
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return typeof window.YAHOO !== 'undefined' && window.YAHOO.context && window.YAHOO.context.user.crumb")
        )
        
        crumb = driver.execute_script("return window.YAHOO.context.user.crumb")
        cookies = driver.get_cookies()

        print(f"Crumb: {crumb}")
        return crumb, cookies
    except Exception as e:
        print(f"Error getting crumb: {e}")
        return None, None
    finally:
        driver.quit()


# 使用取得的 crumb 和 cookies 發送請求來篩選股票
def fetch_stocks(crumb, cookies):
    url = "https://query2.finance.yahoo.com/v1/finance/screener"
    params = {
        "crumb": crumb,  # 使用從瀏覽器中獲得的 crumb
        "lang": "en-US",
        "region": "US",
        "count": 50,
        "start": 0,
    }

    # 筛选条件（对应 Equity Filters）
    payload = {
        "size": 50,
        "offset": 0,
        "sortField": "volume",
        "sortType": "DESC",
        "quoteType": "EQUITY",
        "query": {
            "operator": "AND",
            "operands": [
                {"operator": "gte", "operands": ["price", 0.1]},
                {"operator": "lte", "operands": ["price", 5]},
                {"operator": "gte", "operands": ["volume", 1000000]},
            ]
        }
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
    }

    # 將 cookies 轉換為字典格式
    cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}

    response = requests.post(url, params=params, json=payload, headers=headers, cookies=cookies_dict)
    data = response.json()

    # 檢查返回的數據
    print(data)

    if "finance" in data and "result" in data["finance"]:
        stocks = data["finance"]["result"][0]["quotes"]
        df = pd.DataFrame(stocks)
        print(df[["symbol", "shortName", "regularMarketPrice", "regularMarketVolume"]])
    else:
        print("獲取股票資料失敗或返回格式不正確")


# 主程式，整合這兩個功能
def main(stock: str):
    print("獲取 Crumb 和 Cookies...")
    crumb, cookies = get_crumb_and_cookies(stock)
    
    if crumb and cookies:
        print("開始獲取股票資料...")
        fetch_stocks(crumb, cookies)
    else:
        print("無法獲取 Crumb 或 Cookies，請檢查錯誤。")

if __name__ == "__main__":
    stock = "AAPL"  # 你可以修改這裡的股票代碼
    main(stock)

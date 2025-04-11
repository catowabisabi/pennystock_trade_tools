import requests
import pandas as pd
import json

# === 設定 User-Agent（你必須提供）===
HEADERS = {
    "User-Agent": "MySECDataBot/1.0 (enomars@gmail.com)"
}

# === Ticker to CIK 轉換（會從 SEC 下載 mapping 檔）===
def get_cik(ticker: str) -> str:
    url = "https://www.sec.gov/include/ticker.txt"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    
    lines = response.text.strip().split('\n')
    mapping = dict(line.split('\t') for line in lines)
    
    cik = mapping.get(ticker.lower())
    if not cik:
        raise ValueError(f"找不到 ticker: {ticker}")
    
    return cik.zfill(10)  # 補足成10位數

# === 根據 CIK 取出最近的 Filing ===
def get_recent_filings(ticker: str, count: int = 10):
    cik = get_cik(ticker)
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    
    filings = data['filings']['recent']
    df = pd.DataFrame({
        'form': filings['form'],
        'filed_date': filings['filingDate'],
        'accession': filings['accessionNumber'],
        'primary_doc': filings['primaryDocument'],
    })

    print(f"\n📄 {ticker.upper()} 的最近 {count} 筆 SEC Filing:")
    print(df.head(count).to_string(index=False))

# === 範例：查詢 NVDA 最近 Filing ===
if __name__ == "__main__":
    get_recent_filings("NVDA", count=5)

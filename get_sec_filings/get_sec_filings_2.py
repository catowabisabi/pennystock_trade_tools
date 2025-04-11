import requests
import pandas as pd
import time
from retrying import retry

# 安装依赖：pip install retrying

# --- 全局配置 ---
SYMBOL_LIST = ['AREB', 'TNON', 'BPTS', 'IBO', 'AEHL', "aapl"]
CIK_URL = "https://www.sec.gov/files/company_tickers.json"
HEADERS = {
    'User-Agent': 'MyTradingBot/1.0 (example@gmail.com)',
    'Accept-Encoding': 'gzip, deflate'
}

# --- 增强型CIK获取 ---
@retry(stop_max_attempt_number=3, wait_fixed=2000)
def load_cik_mapping():
    response = requests.get(CIK_URL, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    print(f"Loaded {len(data)} CIK mappings from SEC website.")
    
    # 创建 ticker 到 CIK 的映射字典
    cik_map = {}
    for key, entry in data.items():
        ticker = entry.get('ticker')
        cik = str(entry.get('cik_str')).zfill(10)
        if ticker and cik:
            cik_map[ticker] = cik
    
    #print(f"Successfully processed {len(cik_map)} ticker-CIK pairs")
    return cik_map

# --- 智能财务数据提取 ---
def get_metric(facts, metric_names, unit='USD'):
    print ("Getting Financial Metrics...")
    for metric in metric_names:
        if metric in facts:
            entries = facts[metric].get('units', {}).get(unit, [])
            print(f"Getting {metric} in {unit}...")
            print("Entries:", entries[0])
            if entries:
                # 取最新非空值（按end日期排序）
                sorted_entries = sorted(
                    [e for e in entries if 'end' in e and 'val' in e],
                    key=lambda x: x['end'], 
                    reverse=True
                )
                print("Sorted Entries:", sorted_entries[0])
                return sorted_entries[0]['val'] if sorted_entries else None
    return None

# --- 增强版SEC数据获取 ---
@retry(stop_max_attempt_number=3, wait_fixed=2000)
def get_sec_data(symbol, cik_map):
    cik = cik_map.get(symbol.upper())
    if not cik:
        return {"symbol": symbol, "error": "CIK not found"}

    # 获取申报文件
    sub_url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    response = requests.get(sub_url, headers=HEADERS)
    response.raise_for_status()
    filings_data = response.json()

    # 分析申报文件
    recent = filings_data.get('filings', {}).get('recent', {})
    forms = recent.get('form', [])
    dates = recent.get('filingDate', [])
    accession = recent.get('accessionNumber', [])

    # ATM发行分析
    shelf_forms = {'S-3', 'S-3/A', 'S-3ASR', 'F-3', 'F-3ASR'}
    shelf_dates = []
    for form, date in zip(forms, dates):
        if form in shelf_forms:
            shelf_dates.append(date)
    
    # 检查三年内有效的S-3
    has_valid_shelf = any(pd.to_datetime(date) > pd.Timestamp.now() - pd.DateOffset(years=3) 
                          for date in shelf_dates)

    # 获取财务数据
    facts_url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    response = requests.get(facts_url, headers=HEADERS)
    facts = response.json().get("facts", {}).get("us-gaap", {}) if response.ok else {}

    # 关键指标（兼容不同名称）
    cash = get_metric(facts, [
        'CashAndCashEquivalentsAtCarryingValue',
        'CashCashEquivalentsAndShortTermInvestments'
    ])
    
    debt = get_metric(facts, [
        'LongTermDebt',
        'LongTermDebtAndCapitalLeaseObligation',
        'DebtCurrentAndNoncurrent'
    ])

    return {
        "symbol": symbol,
        "cik": cik,
        "cash": f"${cash/1e6:.2f}M" if cash else "N/A",
        "debt": f"${debt/1e6:.2f}M" if debt else "N/A",
        "shelf_status": "Active" if has_valid_shelf else "None",
        "last_shelf_date": max(shelf_dates) if shelf_dates else None,
        "atm_risk": "High" if has_valid_shelf and (cash is None or cash < 1e7) else "Medium"
    }

# --- 执行主程序 ---
if __name__ == "__main__":
    try:
        # 加载CIK映射表
        cik_mapping = load_cik_mapping()
        
        # 获取数据（带指数退避）
        results = []
        for idx, symbol in enumerate(SYMBOL_LIST):
            try:
                print(f"Processing {symbol} ({idx+1}/{len(SYMBOL_LIST)})...")
                data = get_sec_data(symbol, cik_mapping)
                results.append(data)
                print(f"Completed {symbol}")
                
                # 动态延迟（SEC建议至少0.5秒）
                time.sleep(max(0.5, idx*0.1))
                
            except Exception as e:
                print(f"Error processing {symbol}: {str(e)}")
                results.append({"symbol": symbol, "error": str(e)})
        
        # 显示结果
        result_df = pd.DataFrame(results)
        print("\nResults:")
        print(result_df.to_string(index=False))
        
    except Exception as e:
        print(f"Fatal error: {str(e)}")
import requests
import pandas as pd
import time
from retrying import retry
from requests_cache import CachedSession, SQLiteCache
from datetime import datetime
from tabulate import tabulate

class SECFinancialAnalyzer:
    def __init__(self):
        self.SYMBOL_LIST = ['AREB', 'TNON', 'BPTS', 'IBO', 'AEHL', "AAPL"]
        self.CIK_URL = "https://www.sec.gov/files/company_tickers.json"
        self.HEADERS = {
            'User-Agent': 'MyCompany/1.0 (contact@mycompany.com)',
            'Accept-Encoding': 'gzip, deflate'
        }
        self.session = self._create_cached_session()
        
    def _create_cached_session(self):
        """创建带缓存的请求会话"""
        return CachedSession(
            cache_name='sec_cache',
            backend=SQLiteCache(),
            allowable_methods=('GET',),
            expire_after=3600,
            stale_if_error=True
        )
    
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def load_cik_mapping(self):
        """加载CIK映射表"""
        try:
            response = self.session.get(self.CIK_URL, headers=self.HEADERS)
            response.raise_for_status()
            data = response.json()
            return {
                entry['ticker'].upper(): str(entry['cik_str']).zfill(10)
                for entry in data.values()
                if entry.get('ticker') and entry.get('cik_str')
            }
        except Exception as e:
            print(f"Error loading CIK mapping: {str(e)}")
            return {}

    def get_metric(self, facts, metric_names, unit='USD'):
        """获取财务指标"""
        for metric in metric_names:
            if metric in facts:
                entries = [e for e in facts[metric].get('units', {}).get(unit, []) 
                         if 'end' in e and 'val' in e]
                if entries:
                    return sorted(entries, key=lambda x: x['end'], reverse=True)[0]['val']
        return None

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def get_company_data(self, symbol, cik_map):
        """获取公司数据"""
        try:
            cik = cik_map.get(symbol.upper())
            if not cik:
                return {"symbol": symbol, "error": "CIK not found"}

            # 获取申报文件
            filings = self.session.get(
                f"https://data.sec.gov/submissions/CIK{cik}.json",
                headers=self.HEADERS
            ).json().get('filings', {}).get('recent', {})

            # 分析Shelf文件
            shelf_dates = [
                date for form, date in zip(filings.get('form', []), filings.get('filingDate', []))
                if form in {'S-3', 'S-3/A', 'S-3ASR', 'F-3', 'F-3ASR'}
            ]
            has_shelf = any(pd.to_datetime(date) > pd.Timestamp.now() - pd.DateOffset(years=3)
                          for date in shelf_dates)

            # 获取财务数据
            facts = self.session.get(
                f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
                headers=self.HEADERS
            ).json().get("facts", {}).get("us-gaap", {})

            cash = self.get_metric(facts, [
                'CashAndCashEquivalentsAtCarryingValue',
                'CashCashEquivalentsAndShortTermInvestments'
            ])
            
            debt = self.get_metric(facts, [
                'LongTermDebt',
                'LongTermDebtAndCapitalLeaseObligation'
            ])

            return {
                "Symbol": symbol.upper(),
                "CIK": cik,
                "Cash": f"${cash/1e6:.2f}M" if cash else "N/A",
                "Debt": f"${debt/1e6:.2f}M" if debt else "N/A",
                "Shelf Status": "Active" if has_shelf else "None",
                "Last Shelf Date": max(shelf_dates) if shelf_dates else "None",
                "ATM Risk": "High" if has_shelf and (not cash or cash < 1e7) else "Medium"
            }
            
        except Exception as e:
            return {
                "Symbol": symbol.upper(),
                "Error": str(e)
            }

    def print_results_table(self, results):
        """打印漂亮的表格结果"""
        # 转换结果为DataFrame
        df = pd.DataFrame(results)
        
        # 处理NaN值
        df.fillna("", inplace=True)
        
        # 打印表格
        print("\n" + "="*80)
        print("SEC FINANCIAL ANALYSIS RESULTS".center(80))
        print("="*80)
        print(tabulate(df, headers='keys', tablefmt='grid', showindex=False))
        print("="*80 + "\n")

    def generate_html_report(self, results):
        """生成HTML报告"""
        try:
            df = pd.DataFrame(results)
            df.fillna("", inplace=True)
            
            # 基本HTML模板（简化样式避免字体问题）
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>SEC Financial Report</title>
                <meta charset="UTF-8">
                <style>
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                    tr:hover {{ background-color: #f5f5f5; }}
                    .high {{ color: red; font-weight: bold; }}
                </style>
            </head>
            <body>
                <h2>SEC Financial Analysis Report</h2>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                {df.to_html(classes='dataframe', index=False, escape=False)}
            </body>
            </html>
            """
            
            # 高亮风险项
            html = html.replace('>High<', ' class="high">High<')
            
            with open("sec_report.html", "w", encoding='utf-8') as f:
                f.write(html)
            print("\nHTML report saved as 'sec_report.html'")
            
        except Exception as e:
            print(f"\nError generating HTML report: {str(e)}")

    def run_analysis(self):
        """执行分析流程"""
        print("Starting SEC financial analysis...")
        cik_map = self.load_cik_mapping()
        
        results = []
        for idx, symbol in enumerate(self.SYMBOL_LIST):
            print(f"\nProcessing {symbol} ({idx+1}/{len(self.SYMBOL_LIST)})...")
            results.append(self.get_company_data(symbol, cik_map))
            time.sleep(max(0.5, idx*0.1))
        
        # 打印结果表格
        self.print_results_table(results)
        
        # 生成HTML报告
        self.generate_html_report(results)
        
        return results

if __name__ == "__main__":
    analyzer = SECFinancialAnalyzer()
    analyzer.SYMBOL_LIST = ['mspr']
    analyzer.run_analysis()
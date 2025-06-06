# Pennystock Trade Tools 股票交易工具

[English](#english) | [繁體中文](#traditional-chinese)

<a name="traditional-chinese"></a>
## 繁體中文

### 簡介
這是一個強大的股票交易工具集，專門用於分析和監控便士股（Penny Stocks）。該工具集整合了多個數據源，包括 Yahoo Finance、Finnhub、Financial Modeling Prep (FMP) 和 Alpha Vantage，提供全面的市場數據分析功能。

### 主要功能
- **漲幅股票追蹤**
  - 多數據源支持（Yahoo Finance、Finnhub、FMP、Alpha Vantage）
  - 自動篩選和排序功能
  - 實時價格監控
  
- **新聞監控**
  - 整合 Financial Modeling Prep 新聞源
  - 即時市場新聞更新
  
- **SEC 文件監控**
  - 自動獲取 SEC 申報文件
  - 支持多種文件類型分析
  - HTML 報告生成

- **圖表分析**
  - 技術分析圖表生成
  - 多時間週期支持
  - 自定義指標支持

### 項目結構
```
├── get_gainer/          # 漲幅股票追蹤模組
├── get_news/            # 新聞監控模組
├── get_sec_filings/     # SEC文件監控模組
├── get_charts/          # 圖表生成模組
├── get_price/           # 價格監控模組
└── utilities/           # 通用工具函數
```

### 安裝方式
```bash
# 克隆專案
git clone https://github.com/yourusername/pennystock_trade_tools.git

# 進入專案目錄
cd pennystock_trade_tools

# 安裝依賴
pip install -r requirements.txt

# 設置環境變量
cp .env.example .env
# 編輯 .env 文件，添加您的 API 密鑰
```

### 使用說明
1. 設置 API 密鑰：
   - Finnhub API 密鑰
   - Alpha Vantage API 密鑰
   - Financial Modeling Prep API 密鑰

2. 運行漲幅股票追蹤：
   ```bash
   python get_gainer/get_yf_top_gainer_penny.py
   ```

3. 獲取新聞更新：
   ```bash
   python get_news/get_news_fmp.py
   ```

4. 監控 SEC 文件：
   ```bash
   python get_sec_filings/get_sec_filings_3.py
   ```

### 注意事項
- 請確保已安裝 Chrome 瀏覽器（用於 Selenium 操作）
- 所有 API 密鑰都應該保存在 .env 文件中
- 建議使用虛擬環境運行項目

---

<a name="english"></a>
## English

### Introduction
This is a powerful stock trading toolkit specifically designed for analyzing and monitoring penny stocks. The toolkit integrates multiple data sources including Yahoo Finance, Finnhub, Financial Modeling Prep (FMP), and Alpha Vantage to provide comprehensive market data analysis capabilities.

### Key Features
- **Top Gainers Tracking**
  - Multiple data source support (Yahoo Finance, Finnhub, FMP, Alpha Vantage)
  - Automatic filtering and sorting
  - Real-time price monitoring
  
- **News Monitoring**
  - Financial Modeling Prep news integration
  - Real-time market news updates
  
- **SEC Filings Monitor**
  - Automatic SEC filing retrieval
  - Support for multiple document types
  - HTML report generation

- **Chart Analysis**
  - Technical analysis chart generation
  - Multiple timeframe support
  - Custom indicator support

### Project Structure
```
├── get_gainer/          # Top gainers tracking module
├── get_news/            # News monitoring module
├── get_sec_filings/     # SEC filings monitoring module
├── get_charts/          # Chart generation module
├── get_price/           # Price monitoring module
└── utilities/           # Common utility functions
```

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/pennystock_trade_tools.git

# Navigate to project directory
cd pennystock_trade_tools

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env file and add your API keys
```

### Usage
1. Setup API Keys:
   - Finnhub API key
   - Alpha Vantage API key
   - Financial Modeling Prep API key

2. Run Top Gainers Tracking:
   ```bash
   python get_gainer/get_yf_top_gainer_penny.py
   ```

3. Get News Updates:
   ```bash
   python get_news/get_news_fmp.py
   ```

4. Monitor SEC Filings:
   ```bash
   python get_sec_filings/get_sec_filings_3.py
   ```

### Important Notes
- Ensure Chrome browser is installed (required for Selenium operations)
- All API keys should be stored in the .env file
- Recommended to run the project in a virtual environment

---

## License
MIT License

## Contact
If you have any questions or suggestions, please feel free to open an issue or contact us directly.

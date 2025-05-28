# 安裝 tradebot 環境及量化交易相關庫 這篇教程將指導你如何在 conda 上創建一個名為 tradebot 的虛擬環境，並安裝一些量化交易所需的庫，包括 uv, yfinance, pandas, matplotlib, numpy 等。 ## 步驟 1: 安裝 Conda 首先，請確保你已經安裝了 Anaconda 或 Miniconda。如果你還沒有安裝，可以前往官方網站下載： - Anaconda 安裝頁面 - Miniconda 安裝頁面 安裝後，請打開命令行（Terminal 或 CMD），並檢查 conda 是否正確安裝： 
bash bash CopyEdit conda --version
 ## 步驟 2: 創建虛擬環境 tradebot 打開終端機或命令提示符，並執行以下命令來創建一個新的虛擬環境： 
bash bash CopyEdit conda create --name tradebot python=3.9
 這會創建一個名為 tradebot 的虛擬環境，並安裝 Python 3.9。如果你需要其他版本的 Python，可以將 python=3.9 改為你需要的版本。 ## 步驟 3: 啟動虛擬環境 創建環境後，激活它： 
bash bash CopyEdit conda activate tradebot
 ## 步驟 4: 安裝所需的庫 ### 4.1 安裝 uv 和 uv pip 库 安裝 uv 及 uv pip： 
bash bash CopyEdit pip install uv pip install uv pip
 ### 4.2 安裝量化交易所需的庫 以下是安裝所需庫的命令。你可以直接使用 pip 安裝： 
bash bash CopyEdit pip install yfinance pandas numpy matplotlib
 這些庫涵蓋了數據獲取（yfinance）、數據處理（pandas）、數學計算（numpy）和可視化（matplotlib）等基本需求。 ### 4.3 安裝量化交易相關庫 如果你有特定的需求，還可以安裝更多量化交易相關的庫。以下是一些常用的庫： 
bash bash CopyEdit pip install ta-lib pip install backtrader pip install zipline pip install pytorch
 ### 4.4 使用 requirements.txt 安裝 如果你有一個 requirements.txt 文件，包含所有需要的庫，則可以使用以下命令一鍵安裝： 
bash bash CopyEdit pip install -r requirements.txt
 requirements.txt 文件範例如下： 
vbnet CopyEdit yfinance pandas numpy matplotlib ta-lib backtrader zipline
 ## 步驟 5: 確認安裝 完成庫的安裝後，確保所有庫都已正確安裝。可以通過以下命令檢查庫是否安裝成功： 
bash bash CopyEdit pip list
 這會顯示你當前虛擬環境中安裝的所有庫。 ## 步驟 6: 開始使用 你現在可以開始編寫你的量化交易策略或其他相關工作了。將所有代碼保存在你的專案資料夾中，並在虛擬環境中運行。# pennystock_trade_tools 6:00 - 9:30 am EST get top gainers fmp Get News Get SEC Filings

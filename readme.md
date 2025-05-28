# 安裝 `tradebot` 環境及量化交易相關庫

這篇教程將指導你如何在 `conda` 上創建一個名為 `tradebot` 的虛擬環境，並安裝一些量化交易所需的庫，包括 `uv`, `yfinance`, `pandas`, `matplotlib`, `numpy` 等。

## 步驟 1: 安裝 Conda

首先，請確保你已經安裝了 Anaconda 或 Miniconda。如果你還沒有安裝，可以前往官方網站下載：

- Anaconda 安裝頁面
- Miniconda 安裝頁面

安裝後，請打開命令行（Terminal 或 CMD），並檢查 `conda` 是否正確安裝：
# tradebot 環境安裝教學

本指南將協助你在 `conda` 中建立一個名為 `tradebot` 的虛擬環境，並安裝量化交易所需的常用庫，包括：

- `uv`
- `yfinance`
- `pandas`
- `numpy`
- `matplotlib`
- 其他量化分析工具庫（如 `ta-lib`, `backtrader`, `zipline`, `pytorch`）

---

## 步驟 1：安裝 Conda

請先安裝 Anaconda 或 Miniconda：

- [Anaconda 官方下載頁面](https://www.anaconda.com/products/distribution)
- [Miniconda 官方下載頁面](https://docs.conda.io/en/latest/miniconda.html)

安裝後，開啟終端機或命令提示字元，並確認 `conda` 是否安裝成功：

```bash
conda --version


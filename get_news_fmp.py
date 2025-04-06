import os
import json
import certifi
from urllib.request import urlopen
import pandas as pd
from dotenv import load_dotenv

# 加載環境變量
load_dotenv()
api_key = os.getenv("FMP_KEY")

#!/usr/bin/env python
import certifi
import json
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

# Function to get JSON parsed data
def get_jsonparsed_data(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        }
        req = Request(url, headers=headers)  # Add headers to avoid blocking
        response = urlopen(req)
        data = response.read().decode("utf-8")
        return json.loads(data)
    except HTTPError as e:
        print(f"HTTP Error: {e.code}")
    except URLError as e:
        print(f"URL Error: {e.reason}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Replace YOUR_API_KEY with your actual FMP API key
api_key = api_key
url = f"https://financialmodelingprep.com/stable/news/stock-latest?apikey={api_key}"

# Fetch and print the data
data = get_jsonparsed_data(url)
if data:
    print(json.dumps(data, indent=4))  # Pretty print the JSON response

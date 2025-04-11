import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import socket

class SeleniumChromeController:
    def __init__(self, chrome_path=None, user_data_dir=None, port=9222):
        self.chrome_path = chrome_path or r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        self.user_data_dir = user_data_dir or r"C:\selenium-chrome"
        self.port = port
        self.driver = None

    def is_port_in_use(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", self.port))
                return False
            except socket.error:
                return True

    def launch_chrome_with_debugging(self):
        if not self.is_port_in_use():
            print("啟動 Chrome 並開啟遠程調試...")
            subprocess.Popen([
                self.chrome_path,
                f"--remote-debugging-port={self.port}",
                f"--user-data-dir={self.user_data_dir}",
                "--start-maximized"
            ])
            time.sleep(5)
        else:
            print(f"Chrome 遠程調試端口 {self.port} 已經在使用中")

    def start_driver(self, use_debugging_port=False, headless=False):
        chrome_options = Options()

        if use_debugging_port:
            chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.port}")
        else:
            chrome_options.add_argument(f"--user-data-dir={self.user_data_dir}")

        if headless:
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--window-size=1920,1080")

        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def get_html(self, url, use_debugging=False, headless=False):
        if use_debugging:
            self.launch_chrome_with_debugging()

        self.start_driver(use_debugging_port=use_debugging, headless=headless)

        try:
            self.driver.get(url)
            time.sleep(6)
            print("頁面標題:", self.driver.title)
            return self.driver.page_source
        finally:
            if not use_debugging and self.driver:
                self.driver.quit()

# 測試
if __name__ == "__main__":
    controller = SeleniumChromeController()
    html = controller.get_html("https://www.google.com", use_debugging=False, headless=False)
    # print(html)  # 若需要輸出頁面 HTML 可取消註解

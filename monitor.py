import datetime
import logging
import time
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from config import EMAIL_SENDER, EMAIL_RECEIVER, EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT, EMAIL_PASSWORD
#爬到的數字很奇怪、還未確認加股價名子的功能

#pythonw monitor.py背景執行(cmd:存放monitor.py的資料夾)
#taskkill /F /IM python.exe 結束 all (cmd:python.exe的資料夾)
#taskkill /F /IM pythonw.exe
#tasklist | findstr python 檢查

# 設定日誌記錄
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

LAST = 'last_price.txt'  # 用來儲存最後一次查詢的股價檔案路徑

def get_stock_price(url):
    headers = {"User-Agent": "Mozilla/5.0"}  # 防止被 Yahoo Finance 阻擋

    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        price_tag = soup.find("fin-streamer", {"data-field": "regularMarketPrice"})
        
        if price_tag:
            stock_price = float(price_tag.text.replace(",", ""))  # 將股價轉為浮點數
            logging.info(f"當前股價: {stock_price}")
            return stock_price
        else:
            logging.warning("無法找到股價資訊")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"請求錯誤: {e}")
        return None

def load_last_price(stockName):
    try:
        with open(LAST, 'r') as f:
            last_prices = {}
            for line in f:
                stock_name, stock_price = line.strip().split(":")
                if(last_prices[stockName]):
                    return float(stock_price)
                
            logging.info(f"讀取股價資料: {last_prices}")
            return last_prices
    except FileNotFoundError:
        logging.warning("找不到檔案，可能是第一次執行")
        return None
    except ValueError:
        logging.error("發生錯誤")
        return None

import logging

LAST = "stock_prices.txt"  # 存儲股價的檔案名稱

def save_current_price(name, current_price):
    try:
        # 嘗試讀取現有的資料
        stock_data = {}
        try:
            with open(LAST, 'r') as f:
                
                for line in f:
                   
                    stock_name, stock_price = line.strip().split(":")
                    stock_data[stock_name] = float(stock_price)
        except FileNotFoundError:
            pass  

        
        stock_data[name] = current_price

       
        with open(LAST, 'w') as f:
            for stock_name, stock_price in stock_data.items():
                f.write(f"{stock_name}:{stock_price}\n")

        logging.info(f"已儲存")

    except Exception as e:
        logging.error(f"儲存股價時發生錯誤: {e}")


def send_email(message):
    
    sender = EMAIL_SENDER
    receiver = EMAIL_RECEIVER
    smtp_server = EMAIL_SMTP_SERVER
    smtp_port = EMAIL_SMTP_PORT
    password = EMAIL_PASSWORD

    msg = MIMEText(message, 'plain', 'utf-8')
    msg['Subject'] = "股價變更通知"
    msg['From'] = sender
    msg['To'] = receiver

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
        logging.info("Email sent successfully!")
    except Exception as e:
        logging.info(f"Error sending email: {e}")
    

def check(name,url,percent):
    logging.info("name")
    current_price = get_stock_price(url)
    
    if current_price is None:
        logging.warning("無法獲取股價")
        return

    last_price = load_last_price(name)

    logging.info(f"上次股價: {last_price}, 當前股價: {current_price}")

    price_change_percentage = ((current_price - last_price) / last_price) * 100
    logging.info(f"股價變動百分比: {price_change_percentage:.2f}%")

    # 當股價變動超過 3% 時發送郵件
    # #3
    if abs(price_change_percentage) >= percent:
        price_change = current_price - last_price
        message = f"股價變動通知!\n\n前次價格: {last_price}\n當前價格: {current_price}\n變化量: {price_change}\n變動百分比: {price_change_percentage:.2f}%"
        send_email(message)

    save_current_price(name, current_price)
    logging.info("-----------------------------")


if __name__ == "__main__":
    
    stocks = [
        {"name": "台積電", "url": "https://finance.yahoo.com/quote/2330.TW", "percent": 5},
        {"name": "聯發科", "url": "https://finance.yahoo.com/quote/2454.TW", "value": 3},
    ]
    current_time = datetime.now()
    current_hour = current_time.hour
  

    while 9 <= current_hour < 13:
        for stock in stocks:
            check(stock['name'], stock['url'], stock['percent'])
        
        time.sleep(60)  

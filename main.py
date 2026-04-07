import requests
import time
import pandas as pd
import os

TOKEN = os.getenv("8375925127:AAFiwnwEw58AwYMpH4lEzbmesiNaQwGs_yc")
CHAT_ID = os.getenv("8375925127")

last_signal = None

def send(msg):
    url = f"https://api.telegram.org/bot{8375925127:AAFiwnwEw58AwYMpH4lEzbmesiNaQwGs_yc}/sendMessage"
    requests.post(url, data={"chat_id": 8375925127, "text": msg})

def get_data():
    url = "https://api.twelvedata.com/time_series?symbol=XAU/USD&interval=15min&outputsize=100&apikey=demo"
    data = requests.get(url).json()
    
    closes = [float(x["close"]) for x in data["values"]]
    closes.reverse()
    
    df = pd.DataFrame(closes, columns=["close"])
    return df

def calculate(df):
    df["EMA200"] = df["close"].ewm(span=200).mean()
    
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    
    return df

def check(df):
    global last_signal
    
    price = df["close"].iloc[-1]
    ema = df["EMA200"].iloc[-1]
    rsi = df["RSI"].iloc[-1]

    signal = None

    if price > ema and rsi < 40:
        signal = "BUY"
    elif price < ema and rsi > 60:
        signal = "SELL"

    if signal and signal != last_signal:
        msg = f"""📊 XAUUSD {signal}

💰 Price: {price:.2f}
📈 EMA200: {ema:.2f}
📉 RSI: {rsi:.2f}

⏰ TF: M15"""
        send(msg)
        last_signal = signal

while True:
    try:
        df = get_data()
        df = calculate(df)
        check(df)
    except Exception as e:
        print(e)

    time.sleep(900)

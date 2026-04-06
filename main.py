import telebot
import yfinance as yf
import pandas as pd
import time
from flask import Flask
from threading import Thread
import datetime

# --- [ ตั้งค่าข้อมูลส่วนตัว ] ---
TOKEN = '8628685069:AAHL6ERD6ims3kA8S29WggyEWAzrqhu8ybY'
CHAT_ID = '8414725904'
# ----------------------------

bot = telebot.TeleBot(TOKEN)
app = Flask('')

@app.route('/')
def home():
    return "AI Trader Master System is Live!"

def run_web_server():
    app.run(host='0.0.0.0', port=8080)

def get_market_data():
    # ดึงข้อมูลทองคำ 15 นาที และ 1 ชั่วโมง เพื่อดูเทรนด์
    gold = yf.Ticker("GC=F")
    df = gold.history(period="3d", interval="15m")
    return df

def analyze_logic(df):
    last_close = df['Close'].iloc[-1]
    high_recent = df['High'].iloc[-10:-1].max()
    low_recent = df['Low'].iloc[-10:-1].min()
    
    # คำนวณหาจุด TP/SL แบบอัตราส่วน R:R 1:2
    risk = 5.0 # ระยะ SL 5 จุด
    reward = 10.0 # ระยะ TP 10 จุด

    # กลยุทธ์ Break of Structure (BOS) และ Liquidity
    if last_close > high_recent:
        return {
            'action': 'BUY 🚀',
            'entry': round(last_close, 2),
            'tp': round(last_close + reward, 2),
            'sl': round(last_close - risk, 2),
            'reason': 'Price broke recent High (BOS) - Strong Momentum'
        }
    elif last_close < low_recent:
        return {
            'action': 'SELL 🔻',
            'entry': round(last_close, 2),
            'tp': round(last_close - reward, 2),
            'sl': round(last_close + risk, 2),
            'reason': 'Price broke recent Low (Liquidity Sweep) - Bearish Shift'
        }
    return None

def start_trading():
    print("AI Master Bot Started...")
    while True:
        try:
            df = get_market_data()
            signal = analyze_logic(df)
            
            if signal:
                message = (
                    f"🏆 **AI TRADER PREMIUM SIGNAL**\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🔸 **Asset:** XAUUSD (Gold)\n"
                    f"🔸 **Action:** {signal['action']}\n"
                    f"📍 **Entry:** {signal['entry']}\n"
                    f"✅ **Take Profit:** {signal['tp']}\n"
                    f"❌ **Stop Loss:** {signal['sl']}\n"
                    f"📊 **Risk:** 2% per trade\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"💡 **Reason:** {signal['reason']}\n"
                    f"⏰ **Time:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                bot.send_message(CHAT_ID, message, parse_mode='Markdown')
                # พักการส่งสัญญาณ 1 ชั่วโมงเพื่อป้องกันสัญญาณซ้ำซ้อน
                time.sleep(3600)
            else:
                # สแกนตลาดทุก 2 นาที
                time.sleep(120)
                
        except Exception as e:
            print(f"Error encountered: {e}")
            time.sleep(60)

if __name__ == "__main__":
    # เริ่มต้นระบบป้องกันการหลับ
    t = Thread(target=run_web_server)
    t.daemon = True
    t.start()
    
    # เริ่มต้นระบบเทรด
    start_trading()

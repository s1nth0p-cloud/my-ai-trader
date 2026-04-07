import telebot
import yfinance as yf
import pandas as pd
import time
from flask import Flask
from threading import Thread
import datetime
import requests

# --- [ ตั้งค่าข้อมูลส่วนตัว ] ---
TOKEN = '8628685069:AAHL6ERD6ims3kA8S29WggyEWAzrqhu8ybY'
CHAT_ID = '8414725904'
SYMBOLS = {"GC=F": "XAUUSD (Gold)", "EURUSD=X": "EURUSD"}
# ----------------------------

bot = telebot.TeleBot(TOKEN)
app = Flask('')

@app.route('/')
def home():
    return "Institutional Sniper System v2 (News Aware) is Live!"

def run_web_server():
    app.run(host='0.0.0.0', port=8080)

# --- [ ฟังก์ชันเช็คข่าวแรง ] ---
def is_high_impact_news():
    try:
        # ดึงข้อมูลจาก Economic Calendar API (ตัวอย่างการจำลองการดึงข้อมูลจาก API ข่าว)
        # ในระดับใช้งานจริง แนะนำให้เชื่อมกับ API ของ ForexFactory หรือ Investing
        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        response = requests.get(url)
        data = response.json()
        
        now = datetime.datetime.utcnow()
        for event in data:
            if event['impact'] == 'High': # กรองเฉพาะข่าวกล่องแดง
                event_time = datetime.datetime.strptime(event['date'], "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None)
                time_diff = (event_time - now).total_seconds() / 60
                
                # ถ้าข่าวจะออกใน 30 นาที หรือเพิ่งออกไปไม่เกิน 30 นาที
                if -30 < time_diff < 30:
                    return True, event['title']
    except:
        return False, ""
    return False, ""

def get_data(symbol, tf):
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="1d", interval=tf)
    return df

def calculate_rsi(df, period=9):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (100 + rs))

def analyze_institutional(symbol_key):
    df_m1 = get_data(symbol_key, "1m")
    df_m5 = get_data(symbol_key, "5m")
    
    if df_m1.empty or df_m5.empty: return None

    curr_price = df_m1['Close'].iloc[-1]
    ema200_m5 = df_m5['Close'].rolling(window=200).mean().iloc[-1]
    rsi_m1 = calculate_rsi(df_m1).iloc[-1]
    
    fvg_down = df_m5['Low'].iloc[-3] > df_m5['High'].iloc[-1]
    fvg_up = df_m5['High'].iloc[-3] < df_m5['Low'].iloc[-1]

    # BUY Logic
    if curr_price > ema200_m5 and rsi_m1 < 30 and fvg_up:
        return {'action': 'BUY 🚀', 'tp': 10.0 if "GC=F" in symbol_key else 0.0010, 'sl': 3.0 if "GC=F" in symbol_key else 0.0003, 'reason': 'Institutional FVG + M1 Oversold'}
    
    # SELL Logic
    elif curr_price < ema200_m5 and rsi_m1 > 70 and fvg_down:
        return {'action': 'SELL 🔻', 'tp': 10.0 if "GC=F" in symbol_key else 0.0010, 'sl': 3.0 if "GC=F" in symbol_key else 0.0003, 'reason': 'Institutional FVG + M1 Overbought'}
    return None

def start_trading():
    print("Institutional Sniper v2 Started...")
    last_signal_time = {s: 0 for s in SYMBOLS}
    news_announced = False # ป้องกันบอทส่งข้อความแจ้งเตือนข่าวซ้ำๆ
    
    while True:
        try:
            # 1. เช็คข่าวแรงก่อนเป็นอันดับแรก
            is_news, news_title = is_high_impact_news()
            
            if is_news:
                if not news_announced:
                    bot.send_message(CHAT_ID, f"⚠️ **HIGH IMPACT NEWS ALERT!**\n━━━━━━━━━━━━━━━━━━━━\n📰 ข่าว: {news_title}\n🛑 **ระบบหยุดส่งสัญญาณชั่วคราว** 60 นาที เพื่อความปลอดภัยของพอร์ตครับ", parse_mode='Markdown')
                    news_announced = True
                print(f"Skipping due to news: {news_title}")
                time.sleep(300) # พัก 5 นาทีแล้วค่อยเช็คใหม่
                continue
            
            news_announced = False # รีเซ็ตสถานะแจ้งข่าวเมื่อตลาดปลอดภัย
            
            # 2. ถ้าไม่มีข่าว สแกนตลาดปกติ
            for sym, name in SYMBOLS.items():
                signal = analyze_institutional(sym)
                current_time = time.time()
                
                if signal and (current_time - last_signal_time[sym] > 300):
                    price = get_data(sym, "1m")['Close'].iloc[-1]
                    tp_price = price + signal['tp'] if 'BUY' in signal['action'] else price - signal['tp']
                    sl_price = price - signal['sl'] if 'BUY' in signal['action'] else price + signal['sl']
                    
                    message = (
                        f"🏆 **INSTITUTIONAL SIGNAL (PRO)**\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🔸 **Asset:** {name}\n"
                        f"⚡ **Action:** {signal['action']}\n"
                        f"📍 **Entry:** {round(price, 5)}\n"
                        f"✅ **TP (1000 pts):** {round(tp_price, 5)}\n"
                        f"❌ **SL (Sniper):** {round(sl_price, 5)}\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"💡 **Logic:** {signal['reason']}\n"
                        f"📊 **Trend:** Confirmed by EMA200 M5\n"
                        f"📡 **Status:** Market Safe (No High Impact News)"
                    )
                    bot.send_message(CHAT_ID, message, parse_mode='Markdown')
                    last_signal_time[sym] = current_time
            
            time.sleep(30) # สแกนทุก 30 วินาที
                
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    t = Thread(target=run_web_server)
    t.daemon = True
    t.start()
    start_trading()

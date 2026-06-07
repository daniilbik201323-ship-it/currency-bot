import requests
import json
import time
from datetime import datetime
import telebot
import threading
import schedule

BOT_TOKEN = "8401998613:AAHRN7f6SlYr5xzbz24BXpEHdaQr71WbA6E"
CHAT_ID = "7255548810"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=5)
    except:
        pass

# --- ТЕЛЕГРАМ-БОТ ---
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🤖 *Привет! Я бот для отслеживания курсов валют и криптовалют.*\n\n"
        "/help — инструкция\n"
        "/convert USD 100 — конвертировать валюту\n\n"
        "💡 *По вопросам:* @dooxsi"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "📋 *Инструкция:*\n\n"
        "📈 *Сигналы:* бот сам пришлёт уведомление при изменении курса\n"
        "💱 *Конвертер:* /convert USD 100\n\n"
        "📩 *По вопросам:* @dooxsi"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['convert'])
def convert_currency(message):
    parts = message.text.split()
    if len(parts) != 3:
        bot.reply_to(message, "❌ Используй: /convert USD 100")
        return
    currency = parts[1].upper()
    try:
        amount = float(parts[2])
    except:
        bot.reply_to(message, "❌ Неверное число")
        return
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        data = requests.get(url).json()
        usd_to_rub = data['rates']['RUB']
        rates = {
            "USD": usd_to_rub,
            "EUR": data['rates']['EUR'] * usd_to_rub,
            "CNY": usd_to_rub / data['rates']['CNY'],
            "GBP": usd_to_rub / data['rates']['GBP'],
            "JPY": usd_to_rub / data['rates']['JPY'],
            "UAH": usd_to_rub / data['rates']['UAH'],
            "KZT": usd_to_rub / data['rates']['KZT'],
            "CHF": usd_to_rub / data['rates']['CHF'],
            "CAD": usd_to_rub / data['rates']['CAD'],
            "PLN": usd_to_rub / data['rates']['PLN'],
            "SEK": usd_to_rub / data['rates']['SEK'],
            "INR": usd_to_rub / data['rates']['INR']
        }
        crypto_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,binancecoin,solana,ripple,dogecoin&vs_currencies=usd"
        crypto_data = requests.get(crypto_url).json()
        rates["BTC"] = crypto_data.get('bitcoin', {}).get('usd', 0) * usd_to_rub
        rates["ETH"] = crypto_data.get('ethereum', {}).get('usd', 0) * usd_to_rub
        rates["BNB"] = crypto_data.get('binancecoin', {}).get('usd', 0) * usd_to_rub
        rates["SOL"] = crypto_data.get('solana', {}).get('usd', 0) * usd_to_rub
        rates["XRP"] = crypto_data.get('ripple', {}).get('usd', 0) * usd_to_rub
        rates["DOGE"] = crypto_data.get('dogecoin', {}).get('usd', 0) * usd_to_rub
        
        if currency not in rates:
            bot.reply_to(message, f"❌ Валюта {currency} не поддерживается")
            return
        result = amount * rates[currency]
        bot.reply_to(message, f"✅ {amount} {currency} = {result:.2f} ₽")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

def run_telebot():
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Ошибка соединения: {e}. Переподключение через 10 сек...")
            time.sleep(10)

threading.Thread(target=run_telebot, daemon=True).start()

# --- РАССЫЛКА ---
def get_currency_rates():
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        data = requests.get(url).json()
        usd_to_rub = data['rates']['RUB']
        crypto_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        crypto_data = requests.get(crypto_url).json()
        btc = crypto_data.get('bitcoin', {}).get('usd', 0) * usd_to_rub
        return f"📊 *Курсы на {datetime.now().strftime('%d.%m.%Y %H:%M')}*\n💵 Доллар: {usd_to_rub:.2f} ₽\n🪙 Биткоин: {btc:,.0f} ₽"
    except:
        return "❌ Ошибка получения курсов"

def send_daily_rate():
    msg = get_currency_rates()
    send_telegram(msg)
    print(f"[{datetime.now()}] Рассылка отправлена")

def run_scheduler():
    schedule.every().day.at("01:00").do(send_daily_rate)
    schedule.every().day.at("09:00").do(send_daily_rate)
    schedule.every().day.at("05:00").do(send_daily_rate)
    schedule.every().day.at("07:00").do(send_daily_rate)
    while True:
        schedule.run_pending()
        time.sleep(60)

threading.Thread(target=run_scheduler, daemon=True).start()

# --- СИГНАЛЫ ---
SIGNAL_FILE = "last_rates.json"
try:
    with open(SIGNAL_FILE, "r") as f:
        last = json.load(f)
except:
    last = {}

print("🚀 Бот запущен. Мониторинг курсов 18 валют...")
send_telegram("✅ Бот запущен.")

while True:
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        data = requests.get(url).json()
        usd_to_rub = data['rates']['RUB']
        eur_to_rub = data['rates']['EUR'] * usd_to_rub

        crypto_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        crypto_data = requests.get(crypto_url).json()
        btc_to_rub = crypto_data.get('bitcoin', {}).get('usd', 0) * usd_to_rub

        # --- СИГНАЛЫ С НАПРАВЛЕНИЕМ (СТРЕЛКИ) ---
        if "usd" in last and last["usd"] != 0:
            change = abs(usd_to_rub - last["usd"]) / last["usd"] * 100
            if 0.01 < change < 50:
                if usd_to_rub > last["usd"]:
                    direction = "📈 вырос"
                    arrow = "⬆️"
                else:
                    direction = "📉 упал"
                    arrow = "⬇️"
                send_telegram(f"🔴 Доллар {direction} на {change:.2f}% {arrow} (был {last['usd']:.2f}, стал {usd_to_rub:.2f})")
        
        if "eur" in last and last["eur"] != 0:
            change = abs(eur_to_rub - last["eur"]) / last["eur"] * 100
            if 0.01 < change < 50:
                if eur_to_rub > last["eur"]:
                    direction = "📈 вырос"
                    arrow = "⬆️"
                else:
                    direction = "📉 упал"
                    arrow = "⬇️"
                send_telegram(f"🔴 Евро {direction} на {change:.2f}% {arrow}")
        
        if "btc" in last and last["btc"] != 0:
            change = abs(btc_to_rub - last["btc"]) / last["btc"] * 100
            if 0.01 < change < 50:
                if btc_to_rub > last["btc"]:
                    direction = "📈 вырос"
                    arrow = "⬆️"
                else:
                    direction = "📉 упал"
                    arrow = "⬇️"
                send_telegram(f"🔴 Биткоин {direction} на {change:.2f}% {arrow}")

        # Сохраняем курсы
        last = {"usd": usd_to_rub, "eur": eur_to_rub, "btc": btc_to_rub}
        with open(SIGNAL_FILE, "w") as f:
            json.dump(last, f)

        # --- КУРСЫ ДЛЯ МЕНЮ ---
        def safe_div(a, b):
            return a / b if b and b != 0 else a

        gbp_to_rub = safe_div(usd_to_rub, data['rates']['GBP'])
        chf_to_rub = safe_div(usd_to_rub, data['rates']['CHF'])
        cad_to_rub = safe_div(usd_to_rub, data['rates']['CAD'])
        cny_to_rub = safe_div(usd_to_rub, data['rates']['CNY'])
        jpy_to_rub = safe_div(usd_to_rub, data['rates']['JPY'])
        uah_to_rub = safe_div(usd_to_rub, data['rates']['UAH'])
        pln_to_rub = safe_div(usd_to_rub, data['rates']['PLN'])
        sek_to_rub = safe_div(usd_to_rub, data['rates']['SEK'])
        inr_to_rub = safe_div(usd_to_rub, data['rates']['INR'])
        kzt_to_rub = safe_div(usd_to_rub, data['rates']['KZT'])

        # --- МЕНЮ ---
        print("\n1. USD\n2. EUR\n3. CNY\n4. GBP\n5. JPY\n6. CHF\n7. CAD\n8. UAH\n9. PLN\n10. SEK\n11. INR\n12. KZT\n13. BTC\n14. ETH\n15. BNB\n16. SOL\n17. XRP\n18. DOGE\n0. Выход")
        choice = input("Выбери валюту: ").strip()

        if choice == "0":
            print("Пока!")
            break

        # --- ВЫБОР ВАЛЮТЫ ---
        if choice == "1":
            currency = "USD"
            rate = usd_to_rub
        elif choice == "2":
            currency = "EUR"
            rate = eur_to_rub
        elif choice == "3":
            currency = "CNY"
            rate = cny_to_rub
        elif choice == "4":
            currency = "GBP"
            rate = gbp_to_rub
        elif choice == "5":
            currency = "JPY"
            rate = jpy_to_rub
        elif choice == "6":
            currency = "CHF"
            rate = chf_to_rub
        elif choice == "7":
            currency = "CAD"
            rate = cad_to_rub
        elif choice == "8":
            currency = "UAH"
            rate = uah_to_rub
        elif choice == "9":
            currency = "PLN"
            rate = pln_to_rub
        elif choice == "10":
            currency = "SEK"
            rate = sek_to_rub
        elif choice == "11":
            currency = "INR"
            rate = inr_to_rub
        elif choice == "12":
            currency = "KZT"
            rate = kzt_to_rub
        elif choice == "13":
            currency = "BTC"
            rate = btc_to_rub
        elif choice == "14":
            currency = "ETH"
            rate = crypto_data.get('ethereum', {}).get('usd', 0) * usd_to_rub
        elif choice == "15":
            currency = "BNB"
            rate = crypto_data.get('binancecoin', {}).get('usd', 0) * usd_to_rub
        elif choice == "16":
            currency = "SOL"
            rate = crypto_data.get('solana', {}).get('usd', 0) * usd_to_rub
        elif choice == "17":
            currency = "XRP"
            rate = crypto_data.get('ripple', {}).get('usd', 0) * usd_to_rub
        elif choice == "18":
            currency = "DOGE"
            rate = crypto_data.get('dogecoin', {}).get('usd', 0) * usd_to_rub
        else:
            print("Неверный выбор (1-18 или 0)")
            continue

        try:
            amount = float(input(f"Сколько {currency}? "))
        except ValueError:
            print("Ошибка! Введи число.")
            continue

        if amount < 0:
            print("Сумма не может быть отрицательной")
            continue

        result = amount * rate
        print(f"{amount} {currency} = {result:.2f} RUB")

        with open("conversions.txt", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now()}, {amount} {currency}, {result:.2f} RUB\n")

        time.sleep(1)

    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
        time.sleep(5)

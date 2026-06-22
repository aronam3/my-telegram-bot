import os
import telebot
import requests
import io
import urllib3
import threading
from flask import Flask

# إعداد خادم ويب بسيط لإرضاء Render
app = Flask(__name__)
@app.route('/')
def home():
    return "البوت يعمل بنجاح"

def run_web():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# تشغيل خادم الويب في خلفية
threading.Thread(target=run_web).start()

# بقية كود البوت
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
BOT_TOKEN = os.environ.get('BOT_TOKEN')
MY_CHAT_ID = int(os.environ.get('MY_CHAT_ID', 0))

if not BOT_TOKEN:
    exit()

bot = telebot.TeleBot(BOT_TOKEN, threaded=False, skip_pending=True)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.id == MY_CHAT_ID:
        bot.reply_to(message, "البوت متصل ويعمل!")

@bot.message_handler(func=lambda message: True)
def chat_ai(message):
    if message.chat.id != MY_CHAT_ID: return
    try:
        encoded_text = requests.utils.quote(message.text.encode('utf-8'))
        response = requests.get(f"https://pollinations.ai/{encoded_text}", timeout=60, verify=False)
        if response.status_code == 200:
            bot.reply_to(message, response.text)
    except:
        pass

bot.infinity_polling(none_stop=True)


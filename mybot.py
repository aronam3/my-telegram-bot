import os
import telebot
import requests
import io
import urllib3
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

# إعداد سيرفر بسيط لإرضاء Render (يمنع إغلاق البوت)
def run_server():
    port = int(os.environ.get('PORT', 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# إعداد البوت
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
BOT_TOKEN = os.environ.get('BOT_TOKEN')
MY_CHAT_ID = int(os.environ.get('MY_CHAT_ID', 0))

if not BOT_TOKEN:
    print("خطأ: يرجى إضافة BOT_TOKEN في إعدادات البيئة")
    exit()

bot = telebot.TeleBot(BOT_TOKEN, threaded=False, skip_pending=True)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.chat.id == MY_CHAT_ID:
        bot.reply_to(message, "البوت يعمل الآن ومستعد لخدمتك!")

@bot.message_handler(commands=['image'])
def generate_image(message):
    if message.chat.id != MY_CHAT_ID: return
    prompt = message.text.replace('/image', '').strip()
    if not prompt:
        bot.reply_to(message, "يرجى كتابة وصف للصورة.")
        return
    bot.reply_to(message, "جاري توليد الصورة، يرجى الانتظار...")
    try:
        encoded_prompt = requests.utils.quote(prompt.encode('utf-8'))
        image_url = f"https://pollinations.ai/{encoded_prompt}?width=1024&height=1024&nologo=true"
        response = requests.get(image_url, timeout=60, verify=False)
        if response.status_code == 200:
            bot.send_photo(message.chat.id, photo=io.BytesIO(response.content), caption="تم توليد الصورة.")
        else:
            bot.reply_to(message, "فشل الاتصال بسيرفر الصور.")
    except:
        bot.reply_to(message, "خطأ في الشبكة.")

@bot.message_handler(func=lambda message: True)
def chat_ai(message):
    if message.chat.id != MY_CHAT_ID: return
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        encoded_text = requests.utils.quote(message.text.encode('utf-8'))
        response = requests.get(f"https://pollinations.ai/{encoded_text}", timeout=60, verify=False)
        if response.status_code == 200:
            bot.reply_to(message, response.text)
    except:
        bot.reply_to(message, "حدث خطأ أثناء المحادثة.")

print("البوت بدأ العمل بنجاح...")
bot.infinity_polling(none_stop=True)

import telebot
import requests
import io
import os

# جلب التوكن من إعدادات Render التي أضفناها
BOT_TOKEN = os.environ.get('BOT_TOKEN')
REPLICATE_API_TOKEN = os.environ.get('REPLICATE_API_TOKEN')
MY_CHAT_ID = os.environ.get('MY_CHAT_ID')

bot = telebot.TeleBot(BOT_TOKEN)

# تنظيف أي Webhook قديم عالق قبل البدء
bot.delete_webhook()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "البوت يعمل الآن بنجاح ومستعد لخدمتك!")

@bot.message_handler(commands=['image'])
def generate_image(message):
    prompt = message.text.replace('/image', '').strip()
    if not prompt:
        bot.reply_to(message, "يرجى كتابة وصف للصورة.")
        return
    
    bot.reply_to(message, "جاري توليد الصورة، يرجى الانتظار...")
    try:
        encoded_prompt = requests.utils.quote(prompt.encode('utf-8'))
        image_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&model=flux"
        response = requests.get(image_url, timeout=60, verify=False)
        
        if response.status_code == 200:
            bot.send_photo(message.chat.id, photo=io.BytesIO(response.content), caption="توليد الصورة")
        else:
            bot.reply_to(message, "فشل الاتصال بسيرفر الصور.")
    except Exception as e:
        bot.reply_to(message, f"خطأ في الشبكة: {e}")

@bot.message_handler(func=lambda message: True)
def chat_ai(message):
    if message.chat.id != int(MY_CHAT_ID):
        return
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        encoded_text = requests.utils.quote(message.text.encode('utf-8'))
        response = requests.get(f"https://pollinations.ai/{encoded_text}", timeout=60)
        if response.status_code == 200:
            bot.reply_to(message, response.text)
        else:
            bot.reply_to(message, "حدث خطأ أثناء المحادثة.")
    except Exception:
        bot.reply_to(message, "حدث خطأ أثناء المحادثة.")

# التشغيل النهائي
print("البوت بدأ العمل بنجاح...")
bot.infinity_polling(none_stop=True)

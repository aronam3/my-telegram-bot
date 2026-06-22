import telebot
import requests
import io
import urllib3

# إخفاء تحذيرات الأمان
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# سحب التوكن من إعدادات Render تلقائياً
BOT_TOKEN = os.environ.get('BOT_TOKEN')
MY_CHAT_ID = int(os.environ.get('MY_CHAT_ID', 0))

# التحقق من وجود التوكن
if not BOT_TOKEN:
    print("خطأ: لم يتم العثور على BOT_TOKEN في إعدادات البيئة")
    exit()

bot = telebot.TeleBot(BOT_TOKEN, threaded=False, skip_pending=True)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if message.chat.id == MY_CHAT_ID:
        bot.reply_to(message, "أهلاً بك، البوت جاهز الآن")

@bot.message_handler(commands=['image'])
def generate_image(message):
    if message.chat.id != MY_CHAT_ID:
        return
    prompt = message.text.replace('/image', '').strip()
    if not prompt:
        bot.reply_to(message, "يرجى كتابة وصف للصورة بعد الأمر")
        return
    bot.reply_to(message, "جاري توليد صورتك... يرجى الانتظار")
    try:
        encoded_prompt = requests.utils.quote(prompt.encode('utf-8'))
        image_url = f"https://pollinations.ai/{encoded_prompt}?width=1024&height=1024&nologo=true"
        response = requests.get(image_url, timeout=60, verify=False)
        if response.status_code == 200:
            bot.send_photo(message.chat.id, photo=io.BytesIO(response.content), caption="جاهزة")
        else:
            bot.reply_to(message, "حدث خطأ في سيرفر الصور")
    except Exception:
        bot.reply_to(message, "خطأ مؤقت في الشبكة، أعد المحاولة فوراً")

@bot.message_handler(func=lambda message: True)
def chat_ai(message):
    if message.chat.id != MY_CHAT_ID:
        return
    bot.send_chat_action(message.chat.id, 'typing')
    user_text = message.text
    try:
        encoded_text = requests.utils.quote(user_text.encode('utf-8'))
        ai_url = f"https://pollinations.ai/{encoded_text}"
        response = requests.get(ai_url, timeout=60, verify=False)
        if response.status_code == 200:
            bot.reply_to(message, response.text)
        else:
            bot.reply_to(message, "السيرفر مشغول، أعد المحاولة فوراً")
    except Exception:
        bot.reply_to(message, "خطأ مؤقت في الشبكة، أعد المحاولة فوراً")

print("البوت بدأ العمل...")
bot.infinity_polling(none_stop=True)

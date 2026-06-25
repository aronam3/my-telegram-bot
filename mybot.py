import os
import io
import logging
import requests
from PIL import Image, ImageEnhance, ImageFilter
import telebot
import replicate

# ==================== الإعدادات ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# قراءة التوكنات من متغيرات البيئة
BOT_TOKEN = os.environ.get("BOT_TOKEN")
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN")
AUTHORIZED_USER_ID = int(os.environ.get("AUTHORIZED_USER_ID", "6683119855"))

if not BOT_TOKEN or not REPLICATE_API_TOKEN:
    raise ValueError("❌ BOT_TOKEN و REPLICATE_API_TOKEN مطلوبان!")

os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

# ==================== التحسينات ====================
BEST_MODEL = "black-forest-labs/flux-2-max"

NEGATIVE_PROMPT = (
    "watercolor, blurry, low quality, distorted, deformed, "
    "ugly, bad anatomy, watermark, text, signature, oversaturated, "
    "oversaturated colors, painting, illustration, cartoon, anime, "
    "sketch, drawing, oil painting, acrylic, pastel, foggy, "
    "noise, grainy, pixelated, low resolution, amateur, "
    "bad hands, extra fingers, mutated hands, poorly drawn hands"
)

def enhance_prompt(prompt: str) -> str:
    enhancers = (
        "photorealistic, 8k resolution, ultra detailed, sharp focus, "
        "professional photography, DSLR camera, natural lighting, "
        "high quality, crisp details, realistic textures, "
        "masterpiece, best quality"
    )
    return f"{prompt}, {enhancers}"

def post_process_image(image_bytes: bytes) -> io.BytesIO:
    img = Image.open(io.BytesIO(image_bytes))
    
    if img.mode in ('RGBA', 'LA', 'P'):
        img = img.convert('RGB')
    
    # تحسين الوضوح
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
    
    # تحسين التباين
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.1)
    
    # تحسين الحدة
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.2)
    
    # تصحيح الألوان
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(0.95)
    
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=95, optimize=True)
    output.seek(0)
    return output

# ==================== إنشاء البوت ====================
bot = telebot.TeleBot(BOT_TOKEN)

# حذف Webhook أولاً
bot.remove_webhook()

# ==================== الأوامر ====================

@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id != AUTHORIZED_USER_ID:
        return
    
    welcome = (
        "🎨 *بوت توليد الصور - جودة محسّنة*\n\n"
        "✨ التحسينات:\n"
        "• نموذج FLUX.2 Max\n"
        "• معالجة وضوح + ألوان\n"
        "• Negative Prompt\n\n"
        "📝 `/generate وصف الصورة`"
    )
    bot.send_message(message.chat.id, welcome, parse_mode='Markdown')

@bot.message_handler(commands=['generate'])
def generate(message):
    if message.from_user.id != AUTHORIZED_USER_ID:
        return
    
    # استخراج الوصف من الرسالة
    prompt = message.text.replace('/generate', '').strip()
    
    if not prompt:
        bot.send_message(message.chat.id, "❌ الاستخدام: `/generate وصف الصورة`")
        return

    enhanced = enhance_prompt(prompt)
    
    wait_msg = bot.send_message(message.chat.id, "⏳ جاري التوليد...")
    
    try:
        output = replicate.run(
            BEST_MODEL,
            input={
                "prompt": enhanced,
                "negative_prompt": NEGATIVE_PROMPT,
                "aspect_ratio": "1:1",
                "output_format": "png",
                "output_quality": 100,
                "num_inference_steps": 50,
                "guidance_scale": 7.5,
            }
        )
        
        img_url = output[0]
        response = requests.get(img_url, timeout=60)
        response.raise_for_status()
        
        processed = post_process_image(response.content)
        
        # حذف رسالة الانتظار
        bot.delete_message(message.chat.id, wait_msg.message_id)
        
        # إرسال الصورة
        caption = f"🎨 {prompt}\n🤖 FLUX.2 Max | ✨ معالجة"
        bot.send_photo(message.chat.id, photo=processed, caption=caption)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        bot.delete_message(message.chat.id, wait_msg.message_id)
        bot.send_message(message.chat.id, f"❌ خطأ: {str(e)[:300]}")

# ==================== تشغيل البوت ====================
if __name__ == "__main__":
    logger.info("🤖 البوت يعمل...")
    bot.polling(none_stop=True, interval=0)

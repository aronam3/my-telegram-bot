"""
🤖 بوت تيليجرام + Replicate API
"""

import os
import replicate
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ═══════════════════════════════════════════
# قراءة التوكنات من Environment Variables
# ═══════════════════════════════════════════

BOT_TOKEN = os.environ.get("BOT_TOKEN")
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN")
AUTHORIZED_USER_ID = int(os.environ.get("AUTHORIZED_USER_ID", "123456789"))

if not BOT_TOKEN or not REPLICATE_API_TOKEN:
    raise ValueError("❌ BOT_TOKEN و REPLICATE_API_TOKEN مطلوبان!")

# ═══════════════════════════════════════════


# ─── التحقق من الصلاحية ───
async def is_authorized(update: Update) -> bool:
    return update.effective_user.id == AUTHORIZED_USER_ID


# ─── أمر /start ───
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update):
        return
    
    await update.message.reply_text(
        "🎨 <b>مرحباً!</b>\n\n"
        "🖼 <b>الأوامر:</b>\n"
        "• /generate <b>وصف</b> - توليد صورة\n\n"
        "✨ مثال: <code>/generate قطة فضائية</code>",
        parse_mode="HTML"
    )


# ─── أمر /generate مع Replicate ───
async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update):
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 <b>الاستخدام:</b>\n<code>/generate وصف الصورة</code>",
            parse_mode="HTML"
        )
        return
    
    prompt = " ".join(context.args)
    processing_msg = await update.message.reply_text(
        f"⏳ جاري إنشاء: <i>{prompt}</i>...\nقد تستغرق 10-30 ثانية",
        parse_mode="HTML"
    )
    
    try:
        # تشغيل نموذج Replicate
        output = replicate.run(
            "stability-ai/stable-diffusion-xl-base-1.0",
            input={"prompt": prompt, "width": 1024, "height": 1024}
        )
        
        # output عبارة عن رابط (URL)
        image_url = output[0] if isinstance(output, list) else output
        
        # تحميل الصورة وإرسالها
        await update.message.reply_photo(
            photo=image_url,
            caption=f"🎨 <b>{prompt}</b>",
            parse_mode="HTML"
        )
        
        # حذف رسالة "جاري الإنشاء"
        await processing_msg.delete()
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ خطأ: <code>{str(e)}</code>", parse_mode="HTML")


# ─── التشغيل الرئيسي ───
def main():
    print("🚀 تشغيل البوت...")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("generate", generate))
    
    print("✅ البوت يعمل!")
    app.run_polling()


if __name__ == "__main__":
    main()

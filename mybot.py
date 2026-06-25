"""
🤖 بوت تيليجرام + Replicate API (Polling Mode)
"""

import os
import replicate
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ───────────────────────────────
# قراءة التوكنات من Environment Variables
# ───────────────────────────────

BOT_TOKEN = os.environ.get("BOT_TOKEN")
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN")
AUTHORIZED_USER_ID = int(os.environ.get("AUTHORIZED_USER_ID", "123456789"))

if not BOT_TOKEN or not REPLICATE_API_TOKEN:
    raise ValueError("❌ مطلوب BOT_TOKEN و REPLICATE_API_TOKEN!")

# ───────────────────────────────
# التحقق من الصلاحية
# ───────────────────────────────

async def is_authorized(update: Update) -> bool:
    return update.effective_user.id == AUTHORIZED_USER_ID

# ───────────────────────────────
# أمر /start
# ───────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update):
        return

    await update.message.reply_text(
        "👋 <b>أهلاً بيك!</b>\n\n"
        "📋 <b>الأوامر المتاحة:</b>\n"
        "• /generate <b>وصف</b> — توليد صورة بالذكاء الاصطناعي\n\n"
        "✨ <b>مثال:</b>\n"
        "<code>/generate a beautiful sunset over the ocean</code>",
        parse_mode="HTML"
    )

# ───────────────────────────────
# أمر /generate مع Replicate
# ───────────────────────────────

async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update):
        return

    if not context.args:
        await update.message.reply_text(
            "📋 <b>الاستخدام:</b>\n"
            "<code>/generate وصف الصورة</code>\n\n"
            "مثال: <code>/generate a cat wearing sunglasses</code>",
            parse_mode="HTML"
        )
        return

    prompt = " ".join(context.args)

    processing_msg = await update.message.reply_text(
        f"⏳ <b>جاري الإنشاء...</b>\n"
        f"📝 <i>{prompt}</i>\n"
        f"قد تستغرق 10-30 ثانية",
        parse_mode="HTML"
    )

    try:
        # تشغيل نموذج Replicate
        # الموديل: Stable Diffusion XL
        output = replicate.run(
            "stability-ai/stable-diffusion-xl-base-1.0",
            input={
                "prompt": prompt,
                "width": 1024,
                "height": 1024,
                "num_inference_steps": 50,
                "guidance_scale": 7.5,
                "scheduler": "K_EULER",
            }
        )

        # استخراج رابط الصورة
        image_url = output[0] if isinstance(output, list) else output

        # إرسال الصورة
        await update.message.reply_photo(
            photo=image_url,
            caption=f"🎨 <b>{prompt}</b>",
            parse_mode="HTML"
        )

        # حذف رسالة "جاري الإنشاء"
        await processing_msg.delete()

    except Exception as e:
        error_text = str(e)

        # رسائل خطأ مفيدة
        if "401" in error_text or "Unauthenticated" in error_text:
            error_msg = "توكن Replicate غير صالح. تحقق من REPLICATE_API_TOKEN."
        elif "404" in error_text or "Not found" in error_text:
            error_msg = "الموديل غير متاح حالياً. جرب لاحقاً أو استخدم موديل بديل."
        elif "payment" in error_text.lower() or "credit" in error_text.lower():
            error_msg = "رصيد Replicate نفد. تحتاج شحن الرصيد."
        else:
            error_msg = error_text[:300]

        await processing_msg.edit_text(
            f"❌ <b>خطأ:</b> <code>{error_msg}</code>\n\n"
            f"💡 <b>نصائح:</b>\n"
            f"• تأكد من صلاحية REPLICATE_API_TOKEN\n"
            f"• جرب وصفاً بالإنجليزية\n"
            f"• قد يكون الموديل غير متاح مؤقتاً",
            parse_mode="HTML"
        )

# ───────────────────────────────
# التشغيل الرئيسي (Polling)
# ───────────────────────────────

def main():
    print("🚀 تشغيل البوت...")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("generate", generate))

    print("✅ البوت يعمل بالـ Polling!")
    print("⏳ جاري الاستماع للرسائل...")

    # Polling mode (الأفضل مع Background Worker)
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

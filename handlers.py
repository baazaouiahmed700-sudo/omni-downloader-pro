"""
handlers.py — Telegram message & callback handlers
"""

import os
import re
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

from downloader import Downloader
from gemini_ai import GeminiAI

logger = logging.getLogger(__name__)

# ─── Singletons ─────────────────────────────────────────────────────────────
downloader = Downloader()
gemini     = GeminiAI()

# ─── URL Pattern (1 000+ platforms via yt-dlp) ──────────────────────────────
URL_RE = re.compile(
    r"https?://[^\s]+",
    re.IGNORECASE,
)

# ─── Platform Helpers ────────────────────────────────────────────────────────
PLATFORMS = {
    "youtube.com": ("YouTube",   "🎬"),
    "youtu.be":    ("YouTube",   "🎬"),
    "tiktok.com":  ("TikTok",    "🎵"),
    "instagram.com":("Instagram","📸"),
    "twitter.com": ("Twitter/X", "🐦"),
    "x.com":       ("Twitter/X", "🐦"),
    "facebook.com":("Facebook",  "📘"),
    "fb.watch":    ("Facebook",  "📘"),
    "twitch.tv":   ("Twitch",    "🎮"),
    "reddit.com":  ("Reddit",    "🟠"),
    "vimeo.com":   ("Vimeo",     "🎥"),
    "dailymotion": ("Dailymotion","📺"),
}

def detect_platform(url: str):
    url_lower = url.lower()
    for key, (name, emoji) in PLATFORMS.items():
        if key in url_lower:
            return name, emoji
    return "Web", "🌐"


# ─── /start ──────────────────────────────────────────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 *Omni-Downloader Pro*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "أرسل لي أي رابط فيديو من:\n"
        "🎬 YouTube · 🎵 TikTok · 📸 Instagram\n"
        "🐦 Twitter/X · 📘 Facebook · 🎮 Twitch\n"
        "🟠 Reddit · 🎥 Vimeo · وأكثر من 1000 موقع!\n\n"
        "⚡ *الميزات:*\n"
        "• تحميل بدون علامة مائية\n"
        "• جودة تصل لـ 4K\n"
        "• استخراج صوت MP3 بجودة 320kbps\n"
        "• 🤖 تحليل المحتوى بـ Gemini AI\n\n"
        "الأوامر: /help · /about",
        parse_mode="Markdown",
    )


# ─── /help ───────────────────────────────────────────────────────────────────
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *دليل الاستخدام*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "1️⃣ الصق رابط الفيديو في المحادثة\n"
        "2️⃣ اختر صيغة التحميل من الأزرار\n"
        "3️⃣ انتظر لحظة وستحصل على ملفك!\n\n"
        "🔧 *الأوامر:*\n"
        "/start — الصفحة الرئيسية\n"
        "/help  — هذه الرسالة\n"
        "/about — معلومات البوت\n\n"
        "⚠️ *ملاحظة:* حجم الملف لا يتجاوز 50MB",
        parse_mode="Markdown",
    )


# ─── /about ──────────────────────────────────────────────────────────────────
async def cmd_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Omni-Downloader Pro v1.0*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔧 *المكتبات المستخدمة:*\n"
        "• `yt-dlp` — محرك التحميل\n"
        "• `Gemini AI` — تحليل المحتوى\n"
        "• `python-telegram-bot` — واجهة تيليغرام\n"
        "• `FastAPI` — خادم الـ Webhook\n\n"
        "☁️ *يعمل على:* Render Cloud\n"
        "🐍 *Python:* 3.11+",
        parse_mode="Markdown",
    )


# ─── URL Message Handler ──────────────────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    urls = URL_RE.findall(text)

    if not urls:
        await update.message.reply_text(
            "⚠️ لم أجد رابطاً صالحاً.\n"
            "أرسل رابط فيديو مباشرةً وسأقوم بمعالجته!",
        )
        return

    url = urls[0]
    context.user_data["url"] = url

    platform, emoji = detect_platform(url)
    short_url = url[:55] + ("…" if len(url) > 55 else "")

    keyboard = [
        [
            InlineKeyboardButton("🎬 فيديو — أعلى جودة",   callback_data="v_best"),
            InlineKeyboardButton("📱 فيديو — 720p",         callback_data="v_720"),
        ],
        [
            InlineKeyboardButton("💿 فيديو — 480p",         callback_data="v_480"),
            InlineKeyboardButton("📼 فيديو — 360p",         callback_data="v_360"),
        ],
        [
            InlineKeyboardButton("🎵 صوت MP3 — 320kbps",   callback_data="a_320"),
            InlineKeyboardButton("🎶 صوت MP3 — 128kbps",   callback_data="a_128"),
        ],
        [
            InlineKeyboardButton("🤖 تحليل AI (Gemini)",   callback_data="ai_analyze"),
        ],
        [
            InlineKeyboardButton("❌ إلغاء",                callback_data="cancel"),
        ],
    ]

    await update.message.reply_text(
        f"{emoji} *تم اكتشاف رابط {platform}*\n\n"
        f"`{short_url}`\n\n"
        "اختر صيغة التحميل 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


# ─── Callback Query Handler ───────────────────────────────────────────────────
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    url  = context.user_data.get("url")

    # ── Cancel ──────────────────────────────────────────────────────────────
    if data == "cancel":
        await query.edit_message_text("❌ تم الإلغاء.")
        return

    if not url:
        await query.edit_message_text(
            "⚠️ انتهت صلاحية الجلسة.\nأرسل الرابط من جديد."
        )
        return

    # ── AI Analyze ──────────────────────────────────────────────────────────
    if data == "ai_analyze":
        await _handle_ai(query, url)
        return

    # ── Download ─────────────────────────────────────────────────────────────
    media_type = "video" if data.startswith("v_") else "audio"
    quality    = data.split("_")[1]   # best | 720 | 480 | 360 | 320 | 128

    await _handle_download(query, context, url, media_type, quality)


# ─── Download Logic ───────────────────────────────────────────────────────────
async def _handle_download(query, context, url, media_type, quality):
    chat_id = query.message.chat_id
    label = "فيديو" if media_type == "video" else "صوت"
    q_label = quality if quality != "best" else "أعلى جودة"

    await query.edit_message_text(
        f"⬇️ *جاري التحميل…*\n\n"
        f"📂 النوع: {label}\n"
        f"🎚 الجودة: {q_label}\n\n"
        f"⏳ يرجى الانتظار…",
        parse_mode="Markdown",
    )

    file_path, info = await downloader.download(url, media_type, quality)

    if not file_path:
        await query.edit_message_text(
            "❌ *فشل التحميل*\n\n"
            "الأسباب المحتملة:\n"
            "• الرابط خاص أو محذوف\n"
            "• المنصة تطلب تسجيل دخول\n"
            "• الفيديو محظور جغرافياً\n\n"
            "جرب رابطاً آخر أو جودة مختلفة.",
            parse_mode="Markdown",
        )
        return

    file_size = os.path.getsize(file_path)
    title     = (info.get("title") or "فيديو")[:60]
    duration  = int(info.get("duration") or 0)
    dur_str   = f"{duration // 60}:{duration % 60:02d}"

    if file_size > 50 * 1024 * 1024:
        os.remove(file_path)
        await query.edit_message_text(
            f"⚠️ *الملف كبير جداً*\n\n"
            f"الحجم: `{file_size / (1024*1024):.1f} MB`\n"
            f"الحد الأقصى لتيليغرام: 50 MB\n\n"
            f"💡 جرب جودة أقل (480p أو 360p).",
            parse_mode="Markdown",
        )
        return

    await query.edit_message_text(
        f"📤 *جاري الإرسال…*\n\n"
        f"📝 {title}\n"
        f"⏱ {dur_str} | 💾 {file_size / (1024*1024):.1f} MB",
        parse_mode="Markdown",
    )

    caption = (
        f"{'🎬' if media_type == 'video' else '🎵'} *{title}*\n\n"
        f"_تم التحميل بواسطة Omni-Downloader Pro_"
    )

    try:
        with open(file_path, "rb") as f:
            if media_type == "audio":
                await context.bot.send_audio(
                    chat_id=chat_id,
                    audio=f,
                    title=title,
                    duration=duration,
                    caption=caption,
                    parse_mode="Markdown",
                )
            else:
                await context.bot.send_video(
                    chat_id=chat_id,
                    video=f,
                    caption=caption,
                    parse_mode="Markdown",
                    supports_streaming=True,
                    duration=duration,
                )

        await query.delete_message()

    except Exception as e:
        logger.error(f"Send error: {e}")
        await query.edit_message_text(f"❌ فشل الإرسال: {str(e)[:120]}")

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


# ─── AI Analysis ──────────────────────────────────────────────────────────────
async def _handle_ai(query, url):
    if not os.getenv("GEMINI_API_KEY"):
        await query.edit_message_text(
            "⚠️ *Gemini AI غير مفعّل*\n\n"
            "أضف `GEMINI_API_KEY` في متغيرات البيئة على Render.",
            parse_mode="Markdown",
        )
        return

    await query.edit_message_text("🤖 جاري تحليل المحتوى بـ Gemini AI…")

    info = await downloader.get_info(url)
    if not info:
        await query.edit_message_text("❌ لم أتمكن من قراءة معلومات الفيديو.")
        return

    analysis = await gemini.analyze_video_metadata(info)

    title    = (info.get("title") or "غير معروف")[:60]
    duration = int(info.get("duration") or 0)
    views    = info.get("view_count")
    likes    = info.get("like_count")

    header = (
        f"🤖 *تحليل Gemini AI*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 *{title}*\n"
        f"⏱ المدة: {duration // 60}:{duration % 60:02d}\n"
    )
    if views:
        header += f"👁 المشاهدات: {views:,}\n"
    if likes:
        header += f"❤️ الإعجابات: {likes:,}\n"

    header += f"\n🧠 *التحليل:*\n{analysis}"

    # Telegram max message length = 4096
    if len(header) > 4000:
        header = header[:3990] + "…"

    await query.edit_message_text(header, parse_mode="Markdown")


# ─── Register All Handlers ────────────────────────────────────────────────────
def setup_handlers(application: Application):
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help",  cmd_help))
    application.add_handler(CommandHandler("about", cmd_about))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    application.add_handler(CallbackQueryHandler(handle_callback))

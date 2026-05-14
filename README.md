# 🚀 Omni-Downloader Pro

بوت تيليغرام احترافي لتحميل الفيديوهات من أكثر من **1000 منصة** مع تحليل ذكي بـ **Gemini AI**.

---

## ✨ الميزات

| الميزة | التفاصيل |
|---|---|
| 🎬 تحميل فيديو | جودات: Best · 720p · 480p · 360p |
| 🎵 تحميل صوت | MP3 بجودة 320kbps أو 128kbps |
| 🚫 بدون علامة مائية | TikTok · Instagram · وغيرها |
| 🤖 Gemini AI | تحليل المحتوى + هاشتاجات + تصنيف |
| 🌍 تجاوز الحظر الجغرافي | خاصية geo_bypass مفعّلة |
| 🧹 تنظيف Metadata | إزالة بيانات التتبع تلقائياً |

---

## 🗂 هيكل المشروع

```
omni-downloader-pro/
├── main.py          ← FastAPI + Telegram Webhook
├── handlers.py      ← منطق الأوامر والأزرار
├── downloader.py    ← محرك yt-dlp
├── gemini_ai.py     ← تكامل Gemini AI
├── requirements.txt ← المكتبات
├── render.yaml      ← إعدادات Render
├── .env.example     ← قالب متغيرات البيئة
└── .gitignore
```

---

## 🚢 النشر على Render (خطوة بخطوة)

### الخطوة 1 — أنشئ بوت تيليغرام
1. افتح [@BotFather](https://t.me/BotFather) على تيليغرام
2. أرسل `/newbot` واتبع التعليمات
3. احتفظ بـ **Bot Token**

### الخطوة 2 — ارفع الكود على GitHub
```bash
git init
git add .
git commit -m "Initial commit — Omni-Downloader Pro"
git remote add origin https://github.com/username/omni-downloader-pro.git
git push -u origin main
```

### الخطوة 3 — أنشئ Web Service على Render
1. اذهب لـ [render.com](https://render.com) → **New → Web Service**
2. اربط مستودع GitHub
3. اضبط الإعدادات:
   - **Environment:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

### الخطوة 4 — أضف متغيرات البيئة
في لوحة Render → **Environment** أضف:

| المفتاح | القيمة |
|---|---|
| `TELEGRAM_BOT_TOKEN` | `123456:ABC-your-token` |
| `WEBHOOK_URL` | *(اتركه فارغاً الآن)* |
| `GEMINI_API_KEY` | *(اختياري)* |

### الخطوة 5 — انشر واحصل على الـ URL
1. اضغط **Deploy**
2. انتظر اكتمال البناء (~2 دقيقة)
3. انسخ عنوان الـ URL الذي يعطيك إياه Render:
   ```
   https://omni-downloader-pro.onrender.com
   ```

### الخطوة 6 — أضف WEBHOOK_URL وأعد النشر
1. ارجع لـ **Environment** وأضف:
   - `WEBHOOK_URL` = `https://omni-downloader-pro.onrender.com`
2. اضغط **Manual Deploy** أو انتظر إعادة النشر التلقائية

### ✅ جرب البوت!
افتح البوت على تيليغرام وأرسل `/start`

---

## 🔧 التشغيل المحلي (للتطوير)

```bash
# 1. ثبّت المتطلبات
pip install -r requirements.txt

# 2. انسخ ملف البيئة
cp .env.example .env
# عدّل .env وأضف مفاتيحك

# 3. شغّل الخادم
uvicorn main:app --reload --port 8000

# 4. للاختبار المحلي مع Webhook، استخدم ngrok:
ngrok http 8000
# ثم عدّل WEBHOOK_URL في .env بعنوان ngrok
```

---

## 📦 المكتبات الرئيسية

- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** — محرك التحميل (يُحدَّث تلقائياً)
- **[python-telegram-bot v20](https://python-telegram-bot.org/)** — واجهة تيليغرام
- **[FastAPI](https://fastapi.tiangolo.com/)** — خادم الـ Webhook
- **[google-generativeai](https://pypi.org/project/google-generativeai/)** — Gemini AI

---

## ⚠️ ملاحظات مهمة

- **حجم الملف:** تيليغرام يقبل حتى **50MB** فقط
- **الخطة المجانية على Render:** الخادم يُوقف بعد 15 دقيقة من عدم النشاط (يعود تلقائياً عند أول طلب)
- **yt-dlp:** يحتاج تحديثاً دورياً لمتابعة تغييرات المنصات
- **Gemini API:** مجاني حتى حدود معينة من [Google AI Studio](https://aistudio.google.com)

---

## 📄 الترخيص

MIT License — للاستخدام الشخصي والتعليمي.

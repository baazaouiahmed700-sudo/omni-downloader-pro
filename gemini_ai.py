"""
gemini_ai.py — Google Gemini AI Integration
Provides content analysis, caption generation, and smart tagging.
"""

import os
import asyncio
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class GeminiAI:
    """Async-safe Gemini 1.5 Flash wrapper."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self._model  = None

        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._model = genai.GenerativeModel("gemini-1.5-flash")
                logger.info("✅ Gemini AI initialized (gemini-1.5-flash)")
            except ImportError:
                logger.warning("google-generativeai not installed — AI features disabled.")
            except Exception as exc:
                logger.error(f"Gemini init error: {exc}")
        else:
            logger.info("GEMINI_API_KEY not set — AI features disabled.")

    # ── Internal: async wrapper around synchronous Gemini call ───────────────
    async def _generate(self, prompt: str) -> str:
        if not self._model:
            return "⚠️ Gemini AI غير متاح (مفتاح API مفقود أو مكتبة غير مثبتة)."

        loop = asyncio.get_event_loop()

        def _call():
            response = self._model.generate_content(prompt)
            return response.text

        try:
            return await loop.run_in_executor(None, _call)
        except Exception as exc:
            logger.error(f"Gemini generation error: {exc}")
            return f"❌ خطأ في Gemini: {str(exc)[:150]}"

    # ── 1. Full Metadata Analysis ─────────────────────────────────────────────
    async def analyze_video_metadata(self, info: Dict) -> str:
        """
        Deep analysis: summary, hashtags, suggested title, category, tone.
        Accepts a yt-dlp info dict.
        """
        title       = info.get("title", "غير معروف")[:200]
        description = (info.get("description") or "")[:600]
        tags        = ", ".join((info.get("tags") or [])[:15])
        uploader    = info.get("uploader", "غير معروف")
        views       = info.get("view_count", 0) or 0
        likes       = info.get("like_count", 0) or 0
        duration    = int(info.get("duration") or 0)

        prompt = f"""
أنت محلل محتوى رقمي متخصص. قم بتحليل الفيديو التالي بناءً على بياناته الوصفية:

**العنوان:** {title}
**الوصف:** {description or "غير متاح"}
**الوسوم:** {tags or "غير متاحة"}
**المنشئ:** {uploader}
**المشاهدات:** {views:,}
**الإعجابات:** {likes:,}
**المدة:** {duration // 60} دقيقة و{duration % 60} ثانية

قدِّم التحليل بالتنسيق التالي:

📌 **الملخص** (3 جمل مختصرة تشرح محتوى الفيديو):
[ملخصك هنا]

🏷 **الهاشتاجات المقترحة** (8 هاشتاجات مناسبة):
[هاشتاجاتك هنا]

✏️ **عنوان مقترح أكثر جذباً:**
[عنوانك هنا]

📂 **تصنيف المحتوى:**
[التصنيف + سبب مختصر]

📊 **تقييم الأداء المتوقع:**
[تحليل سريع لأداء هذا المحتوى بناءً على البيانات]

أجب باللغة العربية حصراً، بأسلوب احترافي ومباشر.
""".strip()

        return await self._generate(prompt)

    # ── 2. Social Caption Generator ──────────────────────────────────────────
    async def generate_caption(self, info: Dict, platform: str = "general") -> str:
        """Generate an engaging caption for re-posting the video."""
        title       = info.get("title", "")[:150]
        description = (info.get("description") or "")[:400]

        platform_hints = {
            "instagram": "مناسب للإنستغرام، احترافي وجذاب مع إيموجي",
            "tiktok":    "مناسب لتيك توك، قصير وعصري مع ترندات",
            "twitter":   "مناسب لتويتر/إكس، لا يتجاوز 280 حرفاً",
            "youtube":   "وصف يوتيوب مفصّل مع كلمات مفتاحية للـ SEO",
            "general":   "عام ومناسب لجميع المنصات",
        }
        hint = platform_hints.get(platform, platform_hints["general"])

        prompt = f"""
اكتب كابشن احترافي لإعادة نشر هذا الفيديو على منصات التواصل الاجتماعي.

**العنوان الأصلي:** {title}
**الوصف:** {description or "غير متاح"}
**المنصة المستهدفة:** {hint}

المتطلبات:
- جذاب ويحفز على التفاعل
- يتضمن دعوة للفعل (CTA) واضحة
- هاشتاجات في النهاية
- باللغة العربية

اكتب الكابشن مباشرةً دون مقدمات.
""".strip()

        return await self._generate(prompt)

    # ── 3. Smart Category Classifier ────────────────────────────────────────
    async def classify_content(self, info: Dict) -> str:
        """Return a single category label for batch-download sorting."""
        title = info.get("title", "")[:200]
        desc  = (info.get("description") or "")[:300]

        prompt = f"""
صنّف هذا الفيديو في فئة واحدة فقط من القائمة:
تعليم | برمجة | ميكانيكا | علوم | ترفيه | رياضة | طبخ | سفر | أخبار | موسيقى | أخرى

العنوان: {title}
الوصف: {desc}

أجب بالفئة فقط — كلمة واحدة.
""".strip()

        result = await self._generate(prompt)
        # Strip any accidental extra text
        return result.split("\n")[0].strip()[:30]

    # ── 4. Sensitive Content Detector ────────────────────────────────────────
    async def check_sensitivity(self, info: Dict) -> Dict:
        """
        Returns {"safe": bool, "reason": str}
        Quick pre-upload safety check.
        """
        title = info.get("title", "")[:150]
        tags  = ", ".join((info.get("tags") or [])[:10])

        prompt = f"""
هل يبدو هذا الفيديو آمناً للنشر على منصات التواصل الاجتماعي؟

العنوان: {title}
الوسوم: {tags}

أجب بـ JSON فقط بهذا الشكل:
{{"safe": true/false, "reason": "سبب مختصر"}}
""".strip()

        raw = await self._generate(prompt)

        import json, re
        try:
            match = re.search(r"\{.*?\}", raw, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:
            pass

        return {"safe": True, "reason": "لم يمكن التحليل"}

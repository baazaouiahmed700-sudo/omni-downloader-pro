"""
downloader.py — yt-dlp Download Engine
Handles 1000+ platforms with quality selection, watermark removal, and metadata cleaning.
"""

import os
import asyncio
import logging
import glob
from typing import Optional, Tuple, Dict, Any

import yt_dlp

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "/tmp/omni_dl"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# ─── Format Strings ──────────────────────────────────────────────────────────
VIDEO_FORMATS = {
    "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best",
    "720":  "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]",
    "480":  "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best[height<=480]",
    "360":  "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/best[height<=360]",
}

AUDIO_FORMATS = {
    "320": "bestaudio/best",
    "192": "bestaudio/best",
    "128": "bestaudio/best",
}


class Downloader:
    """Async-safe wrapper around yt-dlp."""

    # ── Base yt-dlp options ──────────────────────────────────────────────────
    def _base_opts(self) -> Dict:
        return {
            "outtmpl":           f"{DOWNLOAD_DIR}/%(id)s.%(ext)s",
            "quiet":             True,
            "no_warnings":       True,
            "nocheckcertificate":True,
            "geo_bypass":        True,
            "socket_timeout":    30,
            "retries":           5,
            "fragment_retries":  5,
            "ignoreerrors":      False,
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            },
            # Remove tracking metadata from the output file
            "postprocessors": [{
                "key": "FFmpegMetadata",
                "add_metadata": False,
            }],
        }

    # ── Platform-specific tweaks ─────────────────────────────────────────────
    def _platform_opts(self, url: str) -> Dict:
        url_l = url.lower()

        if "tiktok.com" in url_l:
            # Prefer the watermark-free stream yt-dlp exposes
            return {
                "format": (
                    "download_addr-1/download_addr/"
                    "play_addr_h264/play_addr/bestvideo+bestaudio/best"
                ),
                "http_headers": {
                    "User-Agent": (
                        "TikTok 26.2.0 rv:262018 "
                        "(iPhone; iOS 14.4.2; en_US) Cronet"
                    )
                },
            }

        if "instagram.com" in url_l:
            return {
                "format": "best[ext=mp4]/best",
            }

        return {}

    # ── Public: get info only (no download) ─────────────────────────────────
    async def get_info(self, url: str) -> Optional[Dict[str, Any]]:
        opts = {**self._base_opts(), "skip_download": True}

        def _run():
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=False)

        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, _run)
        except Exception as exc:
            logger.error(f"get_info failed: {exc}")
            return None

    # ── Public: download ─────────────────────────────────────────────────────
    async def download(
        self,
        url: str,
        media_type: str,   # "video" | "audio"
        quality: str,      # "best" | "720" | "480" | "360" | "320" | "128"
    ) -> Tuple[Optional[str], Dict]:
        """
        Returns (file_path, info_dict).
        file_path is None on failure.
        """
        opts = {**self._base_opts()}
        platform_opts = self._platform_opts(url)

        # Apply platform overrides (but let quality/format below win for video)
        if "format" in platform_opts and media_type == "video":
            opts["format"] = platform_opts.pop("format")
        opts.update({k: v for k, v in platform_opts.items() if k != "format"})

        if media_type == "audio":
            opts["format"] = AUDIO_FORMATS.get(quality, "bestaudio/best")
            # Replace the metadata-only postprocessor with audio extraction
            opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": quality if quality in ("320", "192", "128") else "320",
                },
                {"key": "FFmpegMetadata", "add_metadata": False},
            ]
        else:
            if "format" not in opts:           # not overridden by platform opts
                opts["format"] = VIDEO_FORMATS.get(quality, VIDEO_FORMATS["best"])
            opts["merge_output_format"] = "mp4"

        info: Dict = {}
        loop = asyncio.get_event_loop()

        def _run():
            with yt_dlp.YoutubeDL(opts) as ydl:
                extracted = ydl.extract_info(url, download=True)
                if extracted:
                    info.update(extracted)
                    return ydl.prepare_filename(extracted)
                return None

        try:
            raw_path = await loop.run_in_executor(None, _run)
        except yt_dlp.utils.DownloadError as exc:
            logger.error(f"yt-dlp DownloadError: {exc}")
            return None, info
        except Exception as exc:
            logger.error(f"download unexpected error: {exc}")
            return None, info

        # ── Resolve actual path ──────────────────────────────────────────────
        file_path = self._resolve_path(raw_path, info, media_type)
        return file_path, info

    # ── Path resolution helper ───────────────────────────────────────────────
    def _resolve_path(
        self,
        raw_path: Optional[str],
        info: Dict,
        media_type: str,
    ) -> Optional[str]:
        """yt-dlp sometimes changes the extension; find the real file."""

        candidates = []

        # 1. Audio → look for .mp3 sibling
        if media_type == "audio" and raw_path:
            mp3 = os.path.splitext(raw_path)[0] + ".mp3"
            candidates.append(mp3)

        # 2. The path yt-dlp reported
        if raw_path:
            candidates.append(raw_path)

        # 3. Search by video ID in the download folder
        vid_id = info.get("id", "")
        if vid_id:
            candidates.extend(glob.glob(f"{DOWNLOAD_DIR}/{vid_id}.*"))

        for p in candidates:
            if p and os.path.isfile(p) and os.path.getsize(p) > 0:
                return p

        logger.warning(f"Could not find downloaded file. raw_path={raw_path}")
        return None

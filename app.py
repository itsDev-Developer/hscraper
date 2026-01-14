from flask import Flask, request, jsonify, send_from_directory
import yt_dlp
import os
import uuid
import time
import threading
from datetime import datetime, timedelta

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ===== RATE LIMIT CONTROL =====
LAST_DOWNLOAD_TIME = 0
MIN_INTERVAL = 90  # seconds between downloads (IMPORTANT)
LOCK = threading.Lock()

# ===== AUTO DELETE =====
DELETE_AFTER = 3600  # 1 hour

def delete_later(path, delay=DELETE_AFTER):
    def task():
        time.sleep(delay)
        if os.path.exists(path):
            os.remove(path)
    threading.Thread(target=task, daemon=True).start()

@app.route("/")
def home():
    return {"status": "API running"}

@app.route("/download", methods=["POST"])
def download_video():
    global LAST_DOWNLOAD_TIME

    with LOCK:
        now = time.time()
        wait = MIN_INTERVAL - (now - LAST_DOWNLOAD_TIME)
        if wait > 0:
            return jsonify({
                "error": "Rate limit active",
                "retry_after_seconds": int(wait)
            }), 429

        LAST_DOWNLOAD_TIME = now

    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "Video URL required"}), 400

    video_url = data["url"]
    filename = f"{uuid.uuid4()}.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    ydl_opts = {
        "outtmpl": filepath,
        "format": "mp4",
        "noplaylist": True,
        "cookiefile": "cookies.txt",
        "quiet": True,

        # 🔥 ANTI-RATE-LIMIT SETTINGS
        "sleep_interval": 3,
        "max_sleep_interval": 7,
        "retries": 3,
        "fragment_retries": 3,
        "concurrent_fragment_downloads": 1,
        "http_chunk_size": 1048576,

        # 🔥 STRONG FINGERPRINT
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "headers": {
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.instagram.com/"
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        delete_later(filepath)

        return jsonify({
            "status": "success",
            "download_url": f"/file/{filename}",
            "expires_in": "1 hour"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/file/<filename>")
def serve_file(filename):
    return send_from_directory(
        DOWNLOAD_DIR,
        filename,
        as_attachment=True
    )

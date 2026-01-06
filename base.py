import os, subprocess, hashlib, time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HLS_DIR = os.path.join(BASE_DIR, "static", "streams")
os.makedirs(HLS_DIR, exist_ok=True)

@app.route("/convert", methods=["POST", "OPTIONS"])
def convert():
    if request.method == "OPTIONS": return jsonify({"status": "ok"}), 200

    data = request.get_json(silent=True)
    video_url = data.get("url")
    stream_id = hashlib.md5(video_url.encode()).hexdigest()
    out_dir = os.path.join(HLS_DIR, stream_id)
    playlist = os.path.join(out_dir, "index.m3u8")

    os.makedirs(out_dir, exist_ok=True)

    # Start FFmpeg ONLY if the playlist doesn't exist
    if not os.path.exists(playlist):
        headers = "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36\r\n"
        
        cmd = [
            "ffmpeg", "-y", "-headers", headers,
            "-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_delay_max", "5",
            "-i", video_url,
            "-map", "0:v:0", "-map", "0:a", 
            "-c:v", "copy", "-c:a", "aac", "-ac", "2",
            "-sn", "-dn", 
            "-f", "hls", "-hls_time", "10", "-hls_list_size", "0",
            "-hls_playlist_type", "vod",
            "-hls_segment_filename", os.path.join(out_dir, "seg_%05d.ts"),
            playlist
        ]
        # Start and move on immediately
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # RETURN IMMEDIATELY - Don't wait for the file
    proto = request.headers.get("X-Forwarded-Proto", "https")
    hls_url = f"{proto}://{request.host}/static/streams/{stream_id}/index.m3u8"
    
    return jsonify({"status": "success", "hls_link": hls_url})

@app.route("/static/streams/<path:filename>")
def serve_hls(filename):
    return send_from_directory(HLS_DIR, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

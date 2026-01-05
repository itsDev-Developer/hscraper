import os
import subprocess
import hashlib
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HLS_OUTPUT_DIR = os.path.join(BASE_DIR, "static", "streams")
os.makedirs(HLS_OUTPUT_DIR, exist_ok=True)

@app.route('/convert', methods=['POST', 'OPTIONS'])
def convert():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"}), 200

    data = request.get_json()
    video_url = data.get('url')
    if not video_url:
        return jsonify({"status": "error", "message": "Missing URL"}), 400

    stream_id = hashlib.md5(video_url.encode()).hexdigest()
    output_path = os.path.join(HLS_OUTPUT_DIR, stream_id)
    playlist_file = os.path.join(output_path, 'index.m3u8')

    os.makedirs(output_path, exist_ok=True)
    base_server_url = request.host_url.rstrip('/').replace('http://', 'https://')

    # ✅ If playlist already exists, reuse it
    if os.path.exists(playlist_file):
        return jsonify({
            "status": "success",
            "hls_link": f"{base_server_url}/static/streams/{stream_id}/index.m3u8"
        }), 200

    # ✅ FIXED FFMPEG COMMAND
    cmd = [
        'ffmpeg', '-y',
        '-hide_banner', '-loglevel', 'error',

        # Network stability
        '-reconnect', '1',
        '-reconnect_streamed', '1',
        '-reconnect_delay_max', '5',

        '-i', video_url,

        # Map everything safely
        '-map', '0:v',
        '-map', '0:a?',
        '-map', '0:s?',

        # Video untouched
        '-c:v', 'copy',

        # Audio compatible with HLS
        '-c:a', 'aac',
        '-ac', '2',

        # Subtitles → WebVTT (Video.js compatible)
        '-c:s', 'webvtt',

        # HLS FLAGS (VERY IMPORTANT)
        '-f', 'hls',
        '-hls_time', '6',
        '-hls_list_size', '0',
        '-hls_flags', 'independent_segments',
        '-hls_playlist_type', 'event',

        '-hls_segment_filename',
        os.path.join(output_path, 'seg_%05d.ts'),

        playlist_file
    ]

    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # ✅ Proper wait: ensure BOTH playlist + first segment exist
    timeout = 10
    while timeout > 0:
        if os.path.exists(playlist_file):
            segs = [f for f in os.listdir(output_path) if f.endswith('.ts')]
            if len(segs) >= 1:
                break
        time.sleep(1)
        timeout -= 1

    if os.path.exists(playlist_file):
        return jsonify({
            "status": "success",
            "hls_link": f"{base_server_url}/static/streams/{stream_id}/index.m3u8"
        }), 200

    return jsonify({"status": "error", "message": "FFmpeg failed"}), 500


@app.route('/static/streams/<path:filename>')
def custom_static(filename):
    response = send_from_directory(HLS_OUTPUT_DIR, filename)
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

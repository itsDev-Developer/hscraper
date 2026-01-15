from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright

app = Flask(__name__)


def extract_m3u8(video_url, timeout=60000):
    m3u8_links = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )

        page = context.new_page()

        def capture(response):
            url = response.url
            if ".m3u8" in url:
                m3u8_links.add(url)

        page.on("response", capture)

        page.goto(video_url, wait_until="networkidle", timeout=timeout)
        page.wait_for_timeout(5000)

        browser.close()

    return list(m3u8_links)


@app.route("/convert", methods=["POST"])
def convert():
    data = request.get_json(silent=True)

    if not data or "url" not in data:
        return jsonify({
            "status": "error",
            "message": "Missing 'url' field"
        }), 400

    url = data["url"]

    try:
        links = extract_m3u8(url)

        return jsonify({
            "status": "success",
            "count": len(links),
            "m3u8": links
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

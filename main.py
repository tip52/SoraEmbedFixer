from flask import Flask, request, redirect
from playwright.sync_api import sync_playwright
import os, time

app = Flask(__name__)

# Directory for a persistent Chrome profile
PROFILE_DIR = os.path.join(os.getcwd(), "chrome_profile")
os.makedirs(PROFILE_DIR, exist_ok=True)


def extract_video_url(sora_url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            PROFILE_DIR,
            headless=False,   # must be False or Sora blocks it
            channel="chrome", # use installed Chrome
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
        )
        page = browser.new_page()

        print(f"Navigating to {sora_url} ...")
        page.goto(sora_url, timeout=90000)

        # wait for <video> to appear
        page.wait_for_selector("video", timeout=60000)
        video_url = page.get_attribute("video", "src")

        print(f"Extracted video: {video_url}")
        browser.close()
        return video_url


@app.route("/embed")
def embed():
    target_url = request.args.get("url")
    if not target_url:
        return "No ?url= provided", 400

    video_url = extract_video_url(target_url)
    if not video_url:
        return "Could not extract video", 500

    # Redirect so Discord or browser sees the raw MP4
    return redirect(video_url, code=302)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

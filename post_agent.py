import os
import random
from datetime import datetime, timezone, timedelta
import requests

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
BINANCE_SQUARE_API_KEY = os.environ.get("BINANCE_SQUARE_API_KEY", "").strip()

if not GEMINI_API_KEY or not BINANCE_SQUARE_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY or BINANCE_SQUARE_API_KEY in GitHub Secrets.")

BD_TZ = timezone(timedelta(hours=6))
now_bd = datetime.now(BD_TZ)
hour_bd = now_bd.hour

if 5 <= hour_bd < 12:
    slot_name = "Morning"
    vibe = "Sharp morning market pulse, key psychology check, and high-energy hook to start the trading day."
elif 12 <= hour_bd < 17:
    slot_name = "Afternoon"
    vibe = "Mid-day momentum check, common trader traps to avoid, and crisp actionable insight."
else:
    slot_name = "Evening"
    vibe = "Evening wrap-up, risk management reflection, and engaging question for global traders."

angles = [
    "contrarian market belief",
    "trader psychology & FOMO trap",
    "risk management rule that saves accounts",
    "liquidity & breakout patience",
    "simple comparison between disciplined vs emotional trading"
]
chosen_angle = random.choice(angles)

history_file = "last_post.txt"
previous_note = ""
if os.path.exists(history_file):
    with open(history_file, "r", encoding="utf-8") as f:
        previous_note = f.read().strip()

prompt = f"""
You are a top-performing crypto creator on Binance Square writing in English.
Create ONE viral, high-engagement Binance Square post for the {slot_name} slot.

Style & Vibe: {vibe}
Angle: {chosen_angle}
Avoid repeating this previous post summary: {previous_note}

Strict formatting rules:
1. Start with a punchy 1-2 line scroll-stopping hook (no cheesy clickbait or guaranteed profit promises).
2. Keep paragraphs short (1-2 sentences max) and easy to skim on mobile.
3. Include 2-3 clear bullet points with concrete trading/market takeaways.
4. Include 2-3 relevant cashtags like $BTC, $BNB, $ETH, or $SOL only where natural.
5. End with a short, natural question to spark comments.
6. Total length: roughly 110 to 180 words. Output ONLY the final post text, no quotes or extra labels.
"""

gemini_url = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
)
gem_resp = requests.post(gemini_url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
gem_resp.raise_for_status()
post_text = gem_resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

square_endpoints = [
    "https://www.binance.com/bapi/composite/v1/public/pgc/open/content/add",
    "https://www.binance.com/bapi/composite/v1/friendly/pgc/open/content/add",
]

headers = {
    "Content-Type": "application/json",
    "X-Square-OpenAPI-Key": BINANCE_SQUARE_API_KEY,
    "clienttype": "web",
}

payload_variants = [
    {"bodyTextOnly": post_text},
    {"content": post_text},
    {"text": post_text},
]

published = False
last_error = ""

for url in square_endpoints:
    for body in payload_variants:
        try:
            r = requests.post(url, headers=headers, json=body, timeout=25)
            if r.status_code in (200, 201):
                resp_json = r.json() if r.text else {}
                code = str(resp_json.get("code", "000000"))
                if code in ("000000", "0", "200", ""):
                    published = True
                    break
                last_error = f"API response ({url}): {resp_json}"
            else:
                last_error = f"HTTP {r.status_code} ({url}): {r.text[:200]}"
        except Exception as exc:
            last_error = f"Error ({url}): {exc}"
    if published:
        break

if not published:
    raise RuntimeError(f"Failed to publish to Binance Square. Last error: {last_error}")

with open(history_file, "w", encoding="utf-8") as f:
    f.write(f"[{now_bd.isoformat()} - {slot_name} - {chosen_angle}] {post_text[:180]}")

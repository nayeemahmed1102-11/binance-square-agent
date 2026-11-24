import os
import random
from datetime import datetime, timezone, timedelta
import requests

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
BINANCE_SQUARE_API_KEY = os.environ.get("BINANCE_SQUARE_API_KEY", "").strip()

if not GEMINI_API_KEY or not BINANCE_SQUARE_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY or BINANCE_SQUARE_API_KEY in environment.")

TOPICS = [
    "Bitcoin price action, key support/resistance levels, and market sentiment today",
    "Ethereum and Layer-2 ecosystem updates, network activity, and trader takeaways",
    "Altcoin momentum, liquidity rotation, and risk management tips for crypto traders",
    "Crypto market psychology, avoiding FOMO/panic selling, and disciplined trading habits",
    "Stablecoin flows, macro news impact on crypto, and what traders are watching next",
]

BD_TIME = datetime.now(timezone.utc) + timedelta(hours=6)
slot_label = BD_TIME.strftime("%I:%M %p BDT")
topic = random.choice(TOPICS)

prompt = f"""
You are a sharp, engaging crypto market creator posting on Binance Square in English.
Write a high-retention, viral-style short post about: {topic}.
Context time: {slot_label}.

Rules:
- Keep it concise, punchy, and easy to scan (around 110-180 words).
- Start with a strong hook line.
- Use clean bullet points or short paragraphs where helpful.
- End with an engaging question to spark comments.
- Add 3-5 relevant hashtags at the end (e.g., #Crypto #Bitcoin #BinanceSquare).
- Do NOT give guaranteed financial advice; keep tone objective, sharp, and community-friendly.
- Output ONLY the final post text.
"""

MODELS_TO_TRY = [
    ("v1beta", "gemini-2.5-flash"),
    ("v1beta", "gemini-2.0-flash"),
    ("v1beta", "gemini-1.5-flash"),
    ("v1", "gemini-1.5-flash"),
]

generated_text = None
last_error = None

for api_version, model_name in MODELS_TO_TRY:
    url = f"https://generativelanguage.googleapis.com/{api_version}/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }
    try:
        resp = requests.post(url, json=payload, timeout=30)
        if resp.status_code == 404:
            last_error = f"404 for {api_version}/{model_name}: {resp.text}"
            continue
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts).strip()
            if text:
                generated_text = text
                print(f"Generated post using {api_version}/{model_name}")
                break
    except Exception as exc:
        last_error = str(exc)

if not generated_text:
    raise RuntimeError(f"Failed to generate content from Gemini API. Last error: {last_error}")

print("----- GENERATED POST -----")
print(generated_text)
print("--------------------------")

SQUARE_ENDPOINTS = [
    "https://www.binance.com/bapi/composite/v1/public/pgc/open/content/add",
    "https://www.binance.com/bapi/composite/v1/friendly/pgc/open/content/add",
]

headers = {
    "Content-Type": "application/json",
    "X-Square-OpenAPI-Key": BINANCE_SQUARE_API_KEY,
    "Authorization": f"Bearer {BINANCE_SQUARE_API_KEY}",
    "User-Agent": "Mozilla/5.0",
}

post_payloads = [
    {"bodyTextOnly": generated_text},
    {"content": generated_text},
    {"text": generated_text},
]

published = False
square_errors = []

for endpoint in SQUARE_ENDPOINTS:
    for body in post_payloads:
        try:
            r = requests.post(endpoint, json=body, headers=headers, timeout=30)
            if r.status_code in (200, 201):
                print("Published to Binance Square:", r.text[:300])
                published = True
                break
            square_errors.append(f"{endpoint} [{r.status_code}]: {r.text[:200]}")
        except Exception as exc:
            square_errors.append(f"{endpoint} [EXC]: {str(exc)}")
    if published:
        break

if not published:
    raise RuntimeError("Failed to publish to Binance Square. Details: " + " | ".join(square_errors))

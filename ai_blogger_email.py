# File: ai_blogger_hf_email.py

import os
import time
import random
import smtplib
import logging
import requests
import feedparser
import html
from email.message import EmailMessage
from datetime import datetime
from urllib.parse import quote_plus

# ---------------- Config -----------------
TOPIC_SEED = "AI Evolution"

HTTP_TIMEOUT = 15
MAX_RETRIES = 5
RETRY_BACKOFF = 2.0

# Secrets from GitHub
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
BLOGGER_POST_EMAIL = os.getenv("BLOGGER_POST_EMAIL")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

if not all([GMAIL_USER, GMAIL_APP_PASSWORD, BLOGGER_POST_EMAIL, UNSPLASH_ACCESS_KEY, HF_TOKEN]):
    raise ValueError("❌ Missing required environment variables! Please set them in GitHub Secrets.")

logger = logging.getLogger("ai_blogger")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
logger.addHandler(handler)

# ---------------- Utils -----------------
def requests_retry(url, headers=None):
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(url, headers=headers, timeout=HTTP_TIMEOUT)
            if r.status_code == 200:
                return r
            else:
                logger.warning(f"HTTP {r.status_code} for {url}")
        except Exception as e:
            logger.warning(f"Retry {attempt+1} for {url}: {e}")
        time.sleep(RETRY_BACKOFF * (attempt+1))
    return None

# ---------------- Research -----------------
def fetch_wikipedia_summary(term):
    slug = term.replace(" ", "_")
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote_plus(slug)}"
    r = requests_retry(url)
    if r:
        return r.json().get("extract", "")
    return ""

def fetch_google_news(query, max_items=3):
    snippets = []
    rss = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
    try:
        feed = feedparser.parse(rss)
        for entry in feed.entries[:max_items]:
            t = entry.get('title', '')
            s = entry.get('summary', '')
            snippets.append(f"{t}. {s}")
    except Exception as e:
        logger.error(f"Google News error: {e}")
    return snippets

def fetch_arxiv_titles(query, max_items=3):
    out = []
    url = f"http://export.arxiv.org/api/query?search_query=all:{quote_plus(query)}&start=0&max_results={max_items}"
    r = requests_retry(url)
    if r:
        try:
            feed = feedparser.parse(r.text)
            for entry in feed.entries[:max_items]:
                out.append(entry.get("title", ""))
        except Exception as e:
            logger.error(f"Arxiv parse error: {e}")
    return out

def gather_context(topic):
    ctx = []
    wiki = fetch_wikipedia_summary(topic)
    if wiki:
        ctx.append("Wikipedia: " + wiki)
    ctx.extend(fetch_google_news(topic))
    ctx.extend(fetch_arxiv_titles(topic))
    random.shuffle(ctx)
    return ctx[:6]

# ---------------- HuggingFace (AI Content) -----------------
def hf_generate_blog(topic, context):
    # gpt2 ফ্রি/ওপেন—কনটেন্ট ছোট হতে পারে; তবু কাজ চলবে
    url = "https://api-inference.huggingface.co/models/gpt2"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    prompt = (
        f"Write a ~600 word SEO optimized blog post about {topic}. "
        f"Use headings and short paragraphs. Context: {context}"
    )

    for attempt in range(MAX_RETRIES):
        try:
            r = requests.post(
                url,
                headers=headers,
                json={"inputs": prompt, "max_length": 700},
                timeout=60,
            )
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and data and "generated_text" in data[0]:
                    text = data[0]["generated_text"]
                    # পরিষ্কার/সীমাবদ্ধতা
                    text = text.replace("\r", "").strip()
                    if len(text) > 6000:
                        text = text[:6000] + "..."
                    return text
                else:
                    logger.error(f"Unexpected HF response: {data}")
            else:
                logger.warning(f"HuggingFace error {r.status_code}: {r.text[:200]}")
        except Exception as e:
            logger.warning(f"HF retry {attempt+1}: {e}")
        time.sleep(RETRY_BACKOFF * (attempt+1))

    return f"{topic} - AI Evolution Blog Post (Fallback)"

# ---------------- Unsplash Image -----------------
def fetch_unsplash_image(query):
    url = f"https://api.unsplash.com/photos/random?query={quote_plus(query)}&client_id={UNSPLASH_ACCESS_KEY}&orientation=landscape"
    r = requests_retry(url)
    if r:
        try:
            return r.json().get("urls", {}).get("regular", "")
        except Exception:
            return ""
    return ""

# ---------------- HTML Builder -----------------
def build_html(topic, text, image_url):
    safe_topic = html.escape(topic)
    # টেক্সটকে সেফ করা + অনুচ্ছেদে ভাঙা
    safe_text = html.escape(text).strip()
    if not safe_text:
        safe_text = "Short update about AI evolution."
    paras = [p.strip() for p in safe_text.split("\n\n") if p.strip()]
    body = "".join(f"<p>{p.replace('\n', '<br>')}</p>" for p in paras) or f"<p>{safe_text}</p>"

    html_body = f"<h2>{safe_topic}</h2>{body}"
    if image_url:
        html_body += (
            f'<p><img src="{image_url}" alt="{safe_topic}" '
            f'style="max-width:100%;height:auto;border-radius:12px;"></p>'
        )
    return html_body

# ---------------- Email (Blogger Post via Email) -----------------
def send_email(subject, plain_text, html_body):
    safe_subject = subject[:180]
    msg = EmailMessage()
    msg["Subject"] = safe_subject
    msg["From"] = GMAIL_USER
    msg["To"] = BLOGGER_POST_EMAIL

    # ❗ Blogger কখনো plain-text নেয়—তাই এখানে আসল কনটেন্টই রাখলাম
    msg.set_content(f"{plain_text}")

    # HTML ভার্সন
    msg.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        logger.info("✅ Email sent successfully!")
    except Exception as e:
        logger.error(f"❌ Failed to send email: {e}")
        raise

# ---------------- Main -----------------
def main():
    topic = TOPIC_SEED
    logger.info(f"Selected topic: {topic}")

    context = gather_context(topic)
    text = hf_generate_blog(topic, context)
    logger.info(f"Generated Blog Content (preview): {text[:200]!r}")

    image_url = fetch_unsplash_image(topic)
    html_body = build_html(topic, text, image_url)
    plain_body = f"{topic}\n\n{text}"

    subject = f"{topic} - Auto Post {datetime.now().strftime('%Y-%m-%d')}"
    send_email(subject, plain_body, html_body)

if __name__ == "__main__":
    main()

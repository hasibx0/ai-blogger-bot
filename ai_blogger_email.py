# File: ai_blogger_random_topics.py

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

# ---------------- Topics -----------------
AI_TOPICS = [
    "The Future of Artificial General Intelligence",
    "How Generative AI is Changing Content Creation",
    "AI in Healthcare: Revolutionizing Diagnosis",
    "The Role of AI in Cybersecurity",
    "AI for Climate Change Solutions",
    "AI and the Future of Education",
    "AI in Finance: Fraud Detection and Trading",
    "Ethics of Artificial Intelligence",
    "Bias in AI Systems",
    "AI in Autonomous Vehicles",
    "The Role of AI in Robotics",
    "AI in Smart Cities",
    "AI in Agriculture: Feeding the World",
    "AI for Space Exploration",
    "AI in the Gaming Industry",
    "AI and the Future of Jobs",
    "AI in Marketing and Advertising",
    "The Dark Side of AI: Risks and Dangers",
    "AI in Customer Service",
    "AI and Natural Language Processing",
    "AI-Powered Personal Assistants",
    "AI in E-commerce",
    "AI in Mental Health Support",
    "AI and Creative Writing",
    "AI in Music Generation",
    "AI for Small Businesses",
    "AI and Human Creativity",
    "The Role of AI in Innovation",
    "AI in Drug Discovery",
    "AI in Supply Chain Optimization",
    "AI and Big Data",
    "AI and Quantum Computing",
    "AI for Smart Homes",
    "AI in Virtual Reality",
    "AI and Augmented Reality",
    "AI in Social Media Platforms",
    "AI for Image Recognition",
    "AI in Speech Recognition",
    "AI in Video Editing",
    "AI in Photography",
    "AI in Journalism",
    "AI in Art Generation",
    "AI in Fraud Detection",
    "AI in Banking Sector",
    "AI for Personalized Medicine",
    "AI and Self-Driving Cars",
    "AI in Logistics",
    "AI in Disaster Management",
    "AI for Smart Energy Grids",
    "AI and Renewable Energy",
    "AI in Stock Market Prediction",
    "AI and Ethics in Decision Making",
    "AI in Government Services",
    "AI in Military Applications",
    "AI in Political Campaigns",
    "AI and Privacy Concerns",
    "AI in Cloud Computing",
    "AI and Data Security",
    "AI for Predictive Maintenance",
    "AI and Edge Computing",
    "AI in Telecom Industry",
    "AI in Internet of Things (IoT)",
    "AI in Legal Industry",
    "AI in Real Estate",
    "AI in Construction Industry",
    "AI in Sports Analytics",
    "AI in Fashion Industry",
    "AI and Consumer Behavior",
    "AI in Travel and Tourism",
    "AI for Language Translation",
    "AI and Multilingual Systems",
    "AI in Accessibility",
    "AI in Voice Assistants",
    "AI for Smart Wearables",
    "AI in Human Resources",
    "AI in Recruitment",
    "AI in Employee Training",
    "AI in Performance Management",
    "AI for Predicting Customer Churn",
    "AI in Call Centers",
    "AI in Food Industry",
    "AI in Recipe Generation",
    "AI in Personalized Learning",
    "AI in Online Education",
    "AI in Scientific Research",
    "AI in Astronomy",
    "AI in Biology Research",
    "AI in Chemistry Research",
    "AI in Physics Research",
    "AI in Genetics",
    "AI in Genomics",
    "AI in Epidemiology",
    "AI for Pandemic Prediction",
    "AI in Remote Work",
    "AI in Collaboration Tools",
    "AI in Project Management",
    "AI in Document Summarization",
    "AI in Search Engines",
    "AI in Knowledge Management",
    "AI in Business Intelligence",
    "AI in Market Research",
    "AI in Competitive Intelligence",
    "AI for Product Design",
    "AI in Manufacturing",
    "AI in Quality Control",
    "AI in Process Automation",
    "AI in Robotics Process Automation (RPA)",
    "AI in Energy Sector",
    "AI in Oil and Gas",
    "AI in Mining Industry",
    "AI in Water Management",
    "AI in Environmental Protection",
    "AI in Wildlife Conservation",
    "AI in Smart Farming",
    "AI in Crop Monitoring",
    "AI in Precision Agriculture",
    "AI in Pest Control",
    "AI in Soil Monitoring",
    "AI in Irrigation Systems",
    "AI in Climate Prediction",
    "AI in Renewable Energy Forecasting",
    "AI in Transportation",
    "AI in Railways",
    "AI in Airlines",
    "AI in Shipping Industry",
    "AI in Traffic Management",
    "AI in Ride-Sharing Apps",
    "AI in Public Safety",
    "AI in Law Enforcement",
    "AI in Criminal Investigation",
    "AI in Surveillance Systems",
    "AI in Border Security",
    "AI in Counter-Terrorism",
    "AI in Emergency Response",
    "AI in Firefighting",
    "AI in Earthquake Detection",
    "AI in Flood Prediction",
    "AI in Weather Forecasting",
    "AI in Smart Healthcare Devices",
    "AI in Patient Monitoring",
    "AI in Surgery Assistance",
    "AI in Medical Imaging",
    "AI in Radiology",
    "AI in Pathology",
    "AI in Cardiology",
    "AI in Oncology",
    "AI in Neurology",
    "AI in Psychology",
    "AI in Personalized Diets",
    "AI in Fitness Tracking",
    "AI in Sports Performance",
    "AI in Talent Scouting",
    "AI in Esports",
    "AI in Movie Production",
    "AI in Script Writing",
    "AI in Video Games",
    "AI in Animation",
    "AI in Film Editing",
    "AI in Sound Engineering",
    "AI in Podcast Production",
    "AI in Digital Marketing",
    "AI in SEO Optimization",
    "AI in Social Media Marketing",
    "AI in Influencer Marketing",
    "AI in Content Curation",
    "AI in Chatbots",
    "AI in Recommendation Systems",
    "AI in Personalized Ads",
    "AI in Consumer Insights",
    "AI in Retail Industry",
    "AI in Shopping Experience",
    "AI in Virtual Try-On",
    "AI in Inventory Management",
    "AI in Supply Chain Transparency",
    "AI in Fraud Prevention",
    "AI in Online Payments",
    "AI in Cryptocurrency",
    "AI in Blockchain",
    "AI in NFT Industry",
    "AI in Smart Contracts",
    "AI in Insurance",
    "AI in Risk Management",
    "AI in Actuarial Science",
    "AI in Banking Automation",
    "AI in Credit Scoring",
    "AI in Loan Processing",
    "AI in Wealth Management",
    "AI in Investment Analysis",
    "AI in Portfolio Management",
    "AI in Taxation",
    "AI in Government Policy",
    "AI in Smart Voting Systems",
    "AI in Democracy",
    "AI in Social Justice",
    "AI in International Relations",
    "AI in Diplomacy",
    "AI in Global Trade",
    "AI in Cultural Preservation",
    "AI in Language Preservation",
    "AI in History Research",
    "AI in Archaeology",
    "AI in Anthropology",
    "AI in Sociology",
    "AI in Psychology Therapy",
    "AI in Cognitive Science",
    "AI in Philosophy",
    "AI and Human Consciousness",
    "The Future of Human-AI Collaboration"
]
# (২০০+ টপিক দেওয়া হলো)

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
            snippets.append(f"{entry.get('title','')}. {entry.get('summary','')}")
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
    if wiki: ctx.append("Wikipedia: " + wiki)
    ctx.extend(fetch_google_news(topic))
    ctx.extend(fetch_arxiv_titles(topic))
    random.shuffle(ctx)
    return ctx[:6]

# ---------------- HuggingFace -----------------
def hf_generate_blog(topic, context):
    url = "https://api-inference.huggingface.co/models/gpt2"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    prompt = f"Write a 600 word SEO optimized blog post about {topic}. Use keywords naturally. Context: {context}"

    for attempt in range(MAX_RETRIES):
        try:
            r = requests.post(url, headers=headers, json={"inputs": prompt, "max_length": 700}, timeout=60)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and "generated_text" in data[0]:
                    return data[0]["generated_text"]
                else:
                    logger.error(f"Unexpected HF response: {data}")
                    return f"{topic} - AI Evolution Blog Post"
            else:
                logger.warning(f"HuggingFace error {r.status_code}: {r.text}")
        except Exception as e:
            logger.warning(f"HF retry {attempt+1}: {e}")
        time.sleep(RETRY_BACKOFF * (attempt+1))

    return f"{topic} - AI Evolution Blog Post (Fallback)"

# ---------------- Unsplash -----------------
def fetch_unsplash_image(query):
    url = f"https://api.unsplash.com/photos/random?query={quote_plus(query)}&client_id={UNSPLASH_ACCESS_KEY}"
    r = requests_retry(url)
    if r:
        try:
            return r.json().get("urls", {}).get("regular", "")
        except Exception:
            return ""
    return ""

# ---------------- Email (Blogger) -----------------
def send_email(subject, html_body):
    safe_subject = html.escape(subject)[:180]
    msg = EmailMessage()
    msg["Subject"] = safe_subject
    msg["From"] = GMAIL_USER
    msg["To"] = BLOGGER_POST_EMAIL
    msg.set_content("This email contains an HTML post for Blogger.")
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
    topic = random.choice(AI_TOPICS)
    logger.info(f"Selected topic: {topic}")

    context = gather_context(topic)
    blog_content = hf_generate_blog(topic, context)
    image_url = fetch_unsplash_image(topic)

    html_body = f"<h2>{topic}</h2><p>{blog_content}</p>"
    if image_url:
        html_body += f'<p><img src="{image_url}" alt="{topic}" style="max-width:100%;"></p>'

    send_email(f"{topic} - Auto Post {datetime.now().strftime('%Y-%m-%d')}", html_body)

if __name__ == "__main__":
    main()

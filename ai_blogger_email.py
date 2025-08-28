import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import requests

# --------------------------
# HuggingFace Generate Blog
# --------------------------
def hf_generate_blog(topic, context=""):
    API_URL = "https://api-inference.huggingface.co/models/gpt2"
    headers = {"Authorization": f"Bearer {os.getenv('HF_TOKEN')}"}

    prompt = (
        f"Write a ~600 word SEO optimized blog post about {topic}. "
        f"Make it sound like a human wrote it — conversational, natural flow, "
        f"use rhetorical questions, storytelling, and short paragraphs. "
        f"Include headings with ## and ### like a real blogger. "
        f"Context: {context}"
    )

    payload = {"inputs": prompt, "max_new_tokens": 600, "temperature": 0.9}

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list) and "generated_text" in data[0]:
            return data[0]["generated_text"]
        else:
            return f"## {topic}\n\n(Fallback text) Could not generate content."
    except Exception as e:
        return f"## {topic}\n\n(Fallback Error: {str(e)})"


# --------------------------
# Send Email to Blogger
# --------------------------
def send_email(subject, body, to_email):
    gmail_user = os.getenv("GMAIL_USER")
    gmail_pass = os.getenv("GMAIL_APP_PASSWORD")

    if not gmail_user or not gmail_pass:
        raise ValueError("❌ Gmail credentials missing from environment variables")

    message = MIMEMultipart()
    message["From"] = gmail_user
    message["To"] = to_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(gmail_user, gmail_pass)
        server.sendmail(gmail_user, to_email, message.as_string())

    print("✅ Email sent to Blogger successfully!")


# --------------------------
# MAIN
# --------------------------
if __name__ == "__main__":
    BLOGGER_POST_EMAIL = os.getenv("BLOGGER_POST_EMAIL")

    topic = "AI Evolution"
    today = datetime.now().strftime("%Y-%m-%d")
    title = f"{topic} - Auto Post {today}"

    blog_text = hf_generate_blog(topic, context="Latest AI news, research and trends.")

    email_body = f"""
    <h2>{topic}</h2>
    <p>{blog_text}</p>
    """

    send_email(title, email_body, BLOGGER_POST_EMAIL)

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
    HF_TOKEN = os.getenv("HF_TOKEN")
    MODEL = "google/gemma-2b-it"  # 🔹 চাইলে Mistral/Falcon ব্যবহার করতে পারো

    API_URL = f"https://api-inference.huggingface.co/models/{MODEL}"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}

    prompt = (
        f"Write a 600-word SEO optimized blog post about {topic}. "
        f"Make it conversational and natural, as if a human blogger wrote it. "
        f"Use storytelling, rhetorical questions, and short paragraphs. "
        f"Use headings with ## and ### like a real blog post. "
        f"Context: {context}"
    )

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 700,
            "temperature": 0.8,
            "top_p": 0.9,
            "do_sample": True,
        },
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()

        if isinstance(result, list) and "generated_text" in result[0]:
            return result[0]["generated_text"]
        elif isinstance(result, dict) and "generated_text" in result:
            return result["generated_text"]
        else:
            return f"## {topic}\n\n(Fallback) Could not parse response: {result}"
    except Exception as e:
        return f"## {topic}\n\n(Fallback Error: {str(e)})"


# --------------------------
# Send Email to Blogger
# --------------------------
def send_email(subject, body, to_email):
    gmail_user = os.getenv("GMAIL_USER")
    gmail_pass = os.getenv("GMAIL_APP_PASSWORD")

    if not gmail_user or not gmail_pass:
        raise ValueError("❌ Gmail credentials missing in environment variables")

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
    <div style="font-family:Arial, sans-serif; line-height:1.6;">
    {blog_text}
    </div>
    """

    send_email(title, email_body, BLOGGER_POST_EMAIL)

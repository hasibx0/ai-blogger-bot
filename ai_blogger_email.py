import os
import requests
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Hugging Face API
HF_API_URL = "https://api-inference.huggingface.co/models/google/gemma-7b-it"
HF_HEADERS = {"Authorization": f"Bearer {os.getenv('HF_TOKEN')}"}

def hf_generate_blog(topic, context=""):
    prompt = (
        f"Write a 600 word SEO optimized blog post about {topic}. "
        f"Make it sound conversational, engaging, and human-like. "
        f"Use storytelling, rhetorical questions, and short paragraphs. "
        f"Include headings with ## and ### like a blogger. "
        f"Context: {context}"
    )
    
    response = requests.post(
        HF_API_URL,
        headers=HF_HEADERS,
        json={"inputs": prompt, "parameters": {"max_new_tokens": 800}}
    )
    
    if response.status_code != 200:
        return f"Error from HuggingFace API: {response.text}"
    
    data = response.json()
    if isinstance(data, list) and "generated_text" in data[0]:
        return data[0]["generated_text"]
    return str(data)

# Blogger API Setup
BLOG_ID = os.getenv("BLOG_ID")  # তোমার Blogger Blog ID .env এ রাখবে

def post_to_blogger(title, content):
    creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/blogger"])
    service = build("blogger", "v3", credentials=creds)

    body = {
        "kind": "blogger#post",
        "blog": {"id": BLOG_ID},
        "title": title,
        "content": content,
    }

    post = service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
    print(f"✅ Blog posted: {post['url']}")
    return post['url']


if __name__ == "__main__":
    today = datetime.now().strftime("%Y-%m-%d")
    topic = "AI Evolution"
    context = "Latest AI news, research and future trends"
    
    print("⚡ Generating blog content...")
    blog_content = hf_generate_blog(topic, context)
    
    print("⚡ Posting to Blogger...")
    post_to_blogger(f"{topic} - Auto Post {today}", blog_content)

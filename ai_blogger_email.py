import os
import requests
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

# ---------- Hugging Face Blog Generator ----------
def hf_generate_blog(topic, context=""):
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    headers = {"Authorization": f"Bearer {os.getenv('HF_TOKEN')}"}

    prompt = (
        f"Write a ~600 word SEO optimized blog post about {topic}. "
        f"Make it sound like a human wrote it — conversational, natural flow, "
        f"use rhetorical questions, storytelling, and short paragraphs. "
        f"Include headings with ## and ### like a real blogger. "
        f"Context: {context}"
    )

    response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
    if response.status_code != 200:
        return f"⚠️ HuggingFace Error: {response.text}"

    data = response.json()
    if isinstance(data, list) and "generated_text" in data[0]:
        return data[0]["generated_text"]
    return str(data)

# ---------- Blogger Auth ----------
SCOPES = ["https://www.googleapis.com/auth/blogger"]

def get_blogger_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    else:
        if not os.path.exists("credentials.json"):
            raise FileNotFoundError("❌ credentials.json missing! Please download from Google Cloud Console.")
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token_file:
            token_file.write(creds.to_json())
        print("✅ token.json created successfully")

    service = build("blogger", "v3", credentials=creds)
    return service

# ---------- Post to Blogger ----------
def post_to_blogger(title, content):
    service = get_blogger_service()
    blog_id = os.getenv("BLOG_ID")  # 👉 তোমার Blog ID .env বা secrets এ রাখো

    post = {
        "kind": "blogger#post",
        "title": title,
        "content": content
    }

    result = service.posts().insert(blogId=blog_id, body=post, isDraft=False).execute()
    print(f"✅ Post published: {result['url']}")
    return result['url']

# ---------- Main ----------
if __name__ == "__main__":
    topic = "AI Evolution"
    today = datetime.now().strftime("%Y-%m-%d")

    print("⚡ Generating blog content...")
    blog_content = hf_generate_blog(topic)

    print("⚡ Posting to Blogger...")
    post_to_blogger(f"{topic} - Auto Post {today}", blog_content)

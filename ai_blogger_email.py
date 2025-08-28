import os
import requests
import html
import markdown
from datetime import datetime

# -------------------------
# HuggingFace API: Generate Blog Content
# -------------------------
def hf_generate_blog(topic, context=""):
    API_URL = "https://api-inference.huggingface.co/models/gpt2"
    headers = {"Authorization": f"Bearer {os.getenv('HF_API_KEY')}"}

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

# -------------------------
# Build HTML for Blogger (Markdown → HTML)
# -------------------------
def build_html(topic, text, image_url=None):
    safe_topic = html.escape(topic)

    # Convert markdown to clean HTML
    html_text = markdown.markdown(text, extensions=["extra"])

    html_body = f"<h2>{safe_topic}</h2>{html_text}"

    if image_url:
        html_body += (
            f'<p><img src="{image_url}" alt="{safe_topic}" '
            f'style="max-width:100%;height:auto;border-radius:12px;"></p>'
        )
    return html_body

# -------------------------
# Blogger API Post
# -------------------------
def post_to_blogger(blog_id, access_token, title, content):
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts/"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    data = {"kind": "blogger#post", "blog": {"id": blog_id}, "title": title, "content": content}

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        print("✅ Post published successfully!")
    else:
        print("❌ Error:", response.text)

# -------------------------
# MAIN SCRIPT
# -------------------------
if __name__ == "__main__":
    BLOG_ID = os.getenv("BLOGGER_BLOG_ID")
    ACCESS_TOKEN = os.getenv("BLOGGER_ACCESS_TOKEN")

    topic = "AI Evolution"
    today = datetime.now().strftime("%Y-%m-%d")
    title = f"{topic} - Auto Post {today}"

    blog_text = hf_generate_blog(topic, context="Latest AI news, research and trends.")
    image_url = "https://example.com/sample-image.jpg"  # Optional image

    content = build_html(topic, blog_text, image_url)

    post_to_blogger(BLOG_ID, ACCESS_TOKEN, title, content)

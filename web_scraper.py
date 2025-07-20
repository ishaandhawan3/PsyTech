import requests
from bs4 import BeautifulSoup
import psycopg2
import streamlit as st
from datetime import datetime
from google.generativeai import GenerativeModel

# Set up Gemini (replace with your key management strategy)
import google.generativeai as genai
genai.configure(api_key=st.secrets['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-pro')

# Define sources
SOURCES = [
    "https://parenting.firstcry.com/articles/category/growth-development/",
    "https://parenting.firstcry.com/articles/category/just-for-kids/",
    "https://parenting.firstcry.com/articles/category/behavior-discipline/",
    "https://www.parentcircle.com/",
    "https://www.understood.org/en/articles"
]

# Connect to DB using st.secrets
DB_CONFIG = {
    "host": st.secrets["DB_HOST"],
    "dbname": st.secrets["DB_NAME"],
    "user": st.secrets["DB_USER"],
    "password": st.secrets["DB_PASSWORD"],
    "port": 5432 
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def summarize_and_tag_with_llm(title, content):
    prompt = f"""
    You are a helpful assistant. Given the following article:

    Title: {title}
    Content: {content}

    1. Generate a short summary (max 3 sentences).
    2. Suggest 1–3 categories for the article (e.g., parenting, autism, ADHD, behavior).

    Format:
    Summary: <summary>
    Categories: <comma-separated-categories>
    """
    response = model.generate_content(prompt)
    summary, categories = "", ""
    try:
        parts = response.text.split("Categories:")
        summary = parts[0].replace("Summary:", "").strip()
        categories = parts[1].strip()
    except:
        summary = content[:200]
        categories = "General"
    return summary, categories

def store_article(title, url, summary, categories):
    conn = get_db_connection()
    cur = conn.cursor()
    # Deduplicate based on URL
    cur.execute("SELECT 1 FROM articles WHERE url = %s", (url,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return

    cur.execute("""
        INSERT INTO articles (title, url, summary, categories, scraped_at)
        VALUES (%s, %s, %s, %s, %s)
    """, (title, url, summary, categories, datetime.utcnow()))
    conn.commit()
    cur.close()
    conn.close()

def scrape_firstcry_category(url):
    try:
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        articles = soup.select('li.clearfix > a')
        for a in articles:
            title = a.get('title')
            link = a.get('href')
            if link and title:
                content_resp = requests.get(link)
                content_soup = BeautifulSoup(content_resp.text, 'html.parser')
                content_div = content_soup.find("div", class_="article_content")
                content = content_div.text.strip() if content_div else ""
                summary, categories = summarize_and_tag_with_llm(title, content)
                store_article(title, link, summary, categories)
    except Exception as e:
        print(f"Error scraping FirstCry: {e}")

def scrape_parentcircle():
    try:
        r = requests.get("https://www.parentcircle.com/")
        soup = BeautifulSoup(r.text, 'html.parser')
        articles = soup.select('a.readmore')
        for a in articles:
            link = a.get('href')
            if link:
                full_url = f"https://www.parentcircle.com{link}" if link.startswith("/") else link
                res = requests.get(full_url)
                inner = BeautifulSoup(res.text, 'html.parser')
                title_tag = inner.find("h1")
                content_div = inner.find("div", class_="content-description")
                if title_tag and content_div:
                    title = title_tag.text.strip()
                    content = content_div.text.strip()
                    summary, categories = summarize_and_tag_with_llm(title, content)
                    store_article(title, full_url, summary, categories)
    except Exception as e:
        print(f"Error scraping ParentCircle: {e}")

def scrape_understood():
    try:
        r = requests.get("https://www.understood.org/en/articles")
        soup = BeautifulSoup(r.text, 'html.parser')
        articles = soup.select("a.card")
        for a in articles:
            title = a.get("aria-label")
            link = a.get("href")
            if link and title:
                full_url = f"https://www.understood.org{link}" if link.startswith("/") else link
                res = requests.get(full_url)
                inner = BeautifulSoup(res.text, 'html.parser')
                paragraphs = inner.select("div[data-testid='ArticleContainer'] p")
                content = "\n".join(p.text.strip() for p in paragraphs)
                summary, categories = summarize_and_tag_with_llm(title, content)
                store_article(title, full_url, summary, categories)
    except Exception as e:
        print(f"Error scraping Understood.org: {e}")

def scrape_all():
    for url in SOURCES[:3]:
        scrape_firstcry_category(url)
    scrape_parentcircle()
    scrape_understood()

# To run independently:
if __name__ == "__main__":
    scrape_all()
    print("✅ Scraping completed.")

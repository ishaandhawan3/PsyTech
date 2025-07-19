import streamlit as st
import psycopg2
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import google.generativeai as genai
import re

# Load secrets from Streamlit secrets file
DB_CONFIG = {
    'host': st.secrets["db_host"],
    'dbname': st.secrets["db_name"],
    'user': st.secrets["db_user"],
    'password': st.secrets["db_password"],
    'port': st.secrets["db_port"]
}

GEMINI_API_KEY = st.secrets["gemini_api_key"]

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def setup_database():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT,
            interests TEXT
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id SERIAL PRIMARY KEY,
            title TEXT,
            url TEXT UNIQUE,
            summary TEXT,
            categories JSONB,
            user_id INTEGER REFERENCES users(id),
            scraped_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

# Scraper functions (unchanged logic)
def scrape_understood():
    url = "https://www.understood.org/en/articles"
    articles = []
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        for a in soup.select("a.ArticleCard_titleLink__3J1Hy"):
            title = a.text.strip()
            link = "https://www.understood.org" + a.get("href")
            articles.append({"title": title, "url": link})
    except:
        pass
    return articles

def scrape_raisingchildren():
    url = "https://raisingchildren.net.au/guides/a-z-health-reference"
    articles = []
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        for li in soup.select(".listItem-title > a"):
            title = li.text.strip()
            link = "https://raisingchildren.net.au" + li.get("href")
            articles.append({"title": title, "url": link})
    except:
        pass
    return articles

def scrape_autismspeaks():
    url = "https://www.autismspeaks.org/expert-opinion"
    articles = []
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        for card in soup.select(".view-content .card-title a"):
            title = card.text.strip()
            link = "https://www.autismspeaks.org" + card.get("href")
            articles.append({"title": title, "url": link})
    except:
        pass
    return articles

def scrape_verywellfamily():
    url = "https://www.verywellfamily.com/special-needs-parents-4164367"
    articles = []
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        for a in soup.select("a.comp.card--regular"):
            title = a.get("aria-label") or a.text.strip()
            link = a.get("href")
            if link and not link.startswith("http"):
                link = "https://www.verywellfamily.com" + link
            if title and link:
                articles.append({"title": title.strip(), "url": link})
    except:
        pass
    return articles

def scrape_sensationalbrain():
    url = "https://sensationalbrain.com/blog/"
    articles = []
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        for h2 in soup.select(".post-title a"):
            title = h2.text.strip()
            link = h2.get("href")
            articles.append({"title": title, "url": link})
    except:
        pass
    return articles

ALL_SCRAPERS = [
    scrape_understood,
    scrape_raisingchildren,
    scrape_autismspeaks,
    scrape_verywellfamily,
    scrape_sensationalbrain
]

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-pro")

def categorize_and_summarize(article):
    try:
        prompt = f"Categorize this article: {article['title']} ({article['url']})"
        response = model.generate_content(prompt)
        categories = re.findall(r"\\w+", response.text.lower())

        summary_prompt = f"Summarize this article: {article['title']} ({article['url']})"
        summary = model.generate_content(summary_prompt).text.strip()

        return summary, categories
    except:
        return "", []

def insert_articles(articles, user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    for article in articles:
        cur.execute("SELECT 1 FROM articles WHERE url = %s", (article["url"],))
        if cur.fetchone():
            continue
        summary, categories = categorize_and_summarize(article)
        cur.execute("""
            INSERT INTO articles (title, url, summary, categories, user_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            article["title"],
            article["url"],
            summary,
            json.dumps(categories),
            user_id
        ))
    conn.commit()
    cur.close()
    conn.close()

# Streamlit App
setup_database()
st.title("🧠 Personalized Parenting & Child Dev Feed")

if "user_id" not in st.session_state:
    name = st.text_input("👤 Enter your name")
    interests = st.multiselect("🧩 Choose your interests", [
        "Parenting", "Autism", "ADHD", "Special Needs", "Child Development"
    ])
    if st.button("🚀 Generate Feed"):
        if name and interests:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO users (name, interests) VALUES (%s, %s) RETURNING id", (name, ','.join(interests)))
            user_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            st.session_state.user_id = user_id
            st.session_state.name = name
            st.session_state.interests = interests
            with st.spinner("✅ Interests saved! Scraping articles for you..."):
                all_articles = []
                for scraper in ALL_SCRAPERS:
                    all_articles.extend(scraper())
                insert_articles(all_articles, user_id)
            st.success("🎉 Articles scraped and stored!")
        else:
            st.warning("Please enter your name and select interests.")

if "user_id" in st.session_state:
    st.header(f"📰 Welcome, {st.session_state.name}!")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT title, url, summary, categories FROM articles
        WHERE user_id = %s ORDER BY scraped_at DESC LIMIT 15
    """, (st.session_state.user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    if rows:
        for title, url, summary, categories in rows:
            st.markdown(f"### [{title}]({url})")
            if summary:
                st.write(summary)
            st.caption(", ".join(json.loads(categories)))
    else:
        st.info("No articles found. Please regenerate feed.")

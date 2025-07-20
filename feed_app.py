import streamlit as st
import psycopg2
import json
import time
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import google.generativeai as genai
from selenium.webdriver.chrome.service import Service
import re

# Setup DB
DB_CONFIG = {
    'host': st.secrets["DB_HOST"],
    'dbname': st.secrets["DB_NAME"],
    'user': st.secrets["DB_USER"],
    'password': st.secrets["DB_PASSWORD"],
    'port': 5432
}

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-pro")

# Set up Selenium driver with headless Chrome
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver

driver = init_driver()

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# Setup DB tables
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
    
# Selenium-based scraping functions
def scrape_understood():
    url = "https://www.understood.org/en/articles"
    articles = []
    try:
        driver.get(url)
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        for a in soup.select("a.BaseContentCard_cardAnchor__V1lxw"):
            title = a.get_text(strip=True)
            link = "https://www.understood.org" + a.get("href")
            if title and link:
                articles.append({"title": title, "url": link})
        st.success(f"✅ Understood: {len(articles)} articles scraped.")
    except Exception as e:
        st.warning(f"❌ Understood scrape failed: {e}")
    return articles

def scrape_raisingchildren():
    url = "https://raisingchildren.net.au/guides/a-z-health-reference"
    articles = []
    try:
        driver.get(url)
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        for a in soup.select(".listItem a"):
            title = a.get_text(strip=True)
            link = "https://raisingchildren.net.au" + a['href']
            if title and link:
                articles.append({"title": title, "url": link})
        st.success(f"✅ RaisingChildren: {len(articles)} articles scraped.")
    except Exception as e:
        st.warning(f"❌ RaisingChildren scrape failed: {e}")
    return articles

def scrape_autismspeaks():
    url = "https://www.autismspeaks.org/expert-opinion"
    articles = []
    try:
        driver.get(url)
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        for card in soup.select("h3.card-title a"):
            title = card.get_text(strip=True)
            link = card.get("href")
            if not link.startswith("http"):
                link = "https://www.autismspeaks.org" + link
            articles.append({"title": title, "url": link})
        st.success(f"✅ AutismSpeaks: {len(articles)} articles scraped.")
    except Exception as e:
        st.warning(f"❌ AutismSpeaks scrape failed: {e}")
    return articles

def scrape_verywellfamily():
    url = "https://www.verywellfamily.com/special-needs-parents-4164367"
    articles = []
    try:
        driver.get(url)
        time.sleep(4)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        for a in soup.select("a.card--regular"):
            title = a.get("aria-label") or a.get_text(strip=True)
            link = a.get("href")
            if link and not link.startswith("http"):
                link = "https://www.verywellfamily.com" + link
            if title and link:
                articles.append({"title": title.strip(), "url": link})
        st.success(f"✅ VeryWellFamily: {len(articles)} articles scraped.")
    except Exception as e:
        st.warning(f"❌ VeryWellFamily scrape failed: {e}")
    return articles

def scrape_sensationalbrain():
    url = "https://sensationalbrain.com/blog/"
    articles = []
    try:
        driver.get(url)
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        for a in soup.select("h2.entry-title a"):
            title = a.get_text(strip=True)
            link = a['href']
            articles.append({"title": title, "url": link})
        st.success(f"✅ SensationalBrain: {len(articles)} articles scraped.")
    except Exception as e:
        st.warning(f"❌ SensationalBrain scrape failed: {e}")
    return articles

ALL_SCRAPERS = [
    scrape_understood,
    scrape_raisingchildren,
    scrape_autismspeaks,
    scrape_verywellfamily,
    scrape_sensationalbrain
]

# Categorize + summarize using Gemini
def categorize_and_summarize(article):
    try:
        prompt = f"Categorize this article based on parenting and special needs topics: {article['title']} ({article['url']})"
        response = model.generate_content(prompt)
        categories = re.findall(r"\w+", response.text.lower())

        summary_prompt = f"Summarize this article: {article['title']} ({article['url']})"
        summary = model.generate_content(summary_prompt).text.strip()

        return summary, categories
    except Exception:
        return "", []

# Insert new articles into the DB
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

# === Streamlit App ===
setup_database()
st.title("🧠 Personalized Parenting & Child Development Feed")

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
            with st.spinner("🔍 Scraping articles for you..."):
                all_articles = []
                for scraper in ALL_SCRAPERS:
                    all_articles.extend(scraper())
                insert_articles(all_articles, user_id)
            st.success("🎉 Articles scraped and stored!")
        else:
            st.warning("Please enter your name and select interests.")

if "user_id" in st.session_state:
    st.subheader(f"📰 Welcome, {st.session_state.name}!")
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

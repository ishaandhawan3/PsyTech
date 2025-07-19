import streamlit as st
import psycopg2
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from datetime import datetime
import time
import re

# Load credentials from Streamlit secrets
DB_CONFIG = {
    'host': st.secrets["db_host"],
    'dbname': st.secrets["db_name"],
    'user': st.secrets["db_user"],
    'password': st.secrets["db_password"],
    'port': st.secrets["db_port"]
}

GEMINI_API_KEY = st.secrets["gemini_api_key"]

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-pro")

# Database connection
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def setup_database():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name TEXT,
        interests TEXT[]
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS articles (
        id SERIAL PRIMARY KEY,
        title TEXT,
        url TEXT UNIQUE,
        summary TEXT,
        categories TEXT[],
        user_id INTEGER REFERENCES users(id),
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    cur.close()
    conn.close()

# Web scraper templates
def scrape_understood():
    url = "https://www.understood.org/en/articles"
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        articles = []
        for a in soup.select("a.ArticleCard_titleLink__3J1Hy"):
            title = a.text.strip()
            link = "https://www.understood.org" + a.get("href")
            articles.append((title, link))
        return articles
    except:
        return []

def scrape_raisingchildren():
    url = "https://raisingchildren.net.au/guides/a-z-health-reference"
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        articles = []
        for li in soup.select(".listItem-title > a"):
            title = li.text.strip()
            link = "https://raisingchildren.net.au" + li.get("href")
            articles.append((title, link))
        return articles
    except:
        return []

def scrape_autismspeaks():
    url = "https://www.autismspeaks.org/expert-opinion"
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        articles = []
        for card in soup.select(".view-content .card-title a"):
            title = card.text.strip()
            link = "https://www.autismspeaks.org" + card.get("href")
            articles.append((title, link))
        return articles
    except:
        return []

def scrape_verywellfamily():
    url = "https://www.verywellfamily.com/special-needs-parents-4164367"
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        articles = []
        for a in soup.select("a.comp.card--regular"):
            title = a.get("aria-label") or a.text.strip()
            link = a.get("href")
            if link and not link.startswith("http"):
                link = "https://www.verywellfamily.com" + link
            if title and link:
                articles.append((title.strip(), link))
        return articles
    except:
        return []

def scrape_sensationalbrain():
    url = "https://sensationalbrain.com/blog/"
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        articles = []
        for h2 in soup.select(".post-title a"):
            title = h2.text.strip()
            link = h2.get("href")
            articles.append((title, link))
        return articles
    except:
        return []

ALL_SCRAPERS = [
    scrape_understood,
    scrape_raisingchildren,
    scrape_autismspeaks,
    scrape_verywellfamily,
    scrape_sensationalbrain
]

def fetch_and_store_articles(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    st.session_state.scraped = []

    with st.spinner("Scraping articles for you..."):
        for scraper in ALL_SCRAPERS:
            articles = scraper()
            for title, url in articles:
                try:
                    # Generate metadata using Gemini
                    prompt = f"""
                    Categorize this article based on parenting interests: {title} ({url})
                    Return a list of relevant categories like [parenting, autism, communication, etc.].
                    """
                    response = model.generate_content(prompt)
                    categories = re.findall(r"\w+", response.text.lower())
                    summary_prompt = f"Summarize this article: {title} ({url})"
                    summary = model.generate_content(summary_prompt).text.strip()

                    cur.execute("""
                        INSERT INTO articles (title, url, summary, categories, user_id)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (url) DO NOTHING;
                    """, (title, url, summary, categories, user_id))

                    st.session_state.scraped.append(title)
                except:
                    continue

    conn.commit()
    cur.close()
    conn.close()

# Streamlit App
st.title("🧠 Personalized Parenting Feed")

setup_database()

if "user_id" not in st.session_state:
    with st.form("user_form"):
        name = st.text_input("Enter your name:")
        interests = st.multiselect("Choose your parenting interests:", [
            "autism", "adhd", "communication", "education", "behavior", "mental health",
            "emotional development", "learning disabilities", "relationships", "therapy"
        ])
        submitted = st.form_submit_button("Submit")
        if submitted and name and interests:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO users (name, interests) VALUES (%s, %s) RETURNING id", (name, interests))
            user_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()

            st.session_state.user_id = user_id
            st.session_state.interests = interests
            st.success("✅ Interests saved! Scraping articles for you...")
            fetch_and_store_articles(user_id)

else:
    st.subheader(f"👋 Welcome back!")
    st.info("Showing your personalized parenting feed:")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT title, url, summary, categories FROM articles WHERE user_id = %s ORDER BY scraped_at DESC LIMIT 15", (st.session_state.user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if rows:
        for title, url, summary, categories in rows:
            st.markdown(f"### [{title}]({url})")
            st.write(summary)
            st.caption(f"Categories: {', '.join(categories)}")
            st.markdown("---")
    else:
        st.warning("No articles yet. Click below to scrape.")
        if st.button("🔄 Fetch Articles"):
            fetch_and_store_articles(st.session_state.user_id)
            st.experimental_rerun()

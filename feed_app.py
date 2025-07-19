import streamlit as st
import google.generativeai as genai
import psycopg2
import requests
from bs4 import BeautifulSoup

# Gemini Configuration
genai.configure(api_key="your-gemini-api-key")

# Neon DB Config
DB_CONFIG = {
    "dbname": st.secrets["DB_NAME"],
    "user": st.secrets["DB_USER"],
    "password": st.secrets["DB_PASSWORD"],
    "host": st.secrets["DB_HOST"],
    "port": 5432
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def setup_database():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS users CASCADE;")
    cur.execute("DROP TABLE IF EXISTS articles CASCADE;")
    conn.commit()
    
    cur.execute('''
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            name TEXT,
            interests TEXT
        );
    ''')
    cur.execute('''
        CREATE TABLE articles (
            id SERIAL PRIMARY KEY,
            title TEXT,
            url TEXT UNIQUE,
            summary TEXT,
            categories TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

def categorize_article_with_llm(title, summary, interests):
    prompt = f"""
    Classify the following article into parenting-related categories such as "special needs", "child behavior", "parent-child bonding", "emotional intelligence", etc.
    Title: {title}
    Summary: {summary}
    User Interests: {interests}
    Return a list of relevant tags only, separated by commas.
    """
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)
    tags = response.text.strip().split(",")
    return [tag.strip() for tag in tags]

def insert_article(title, url, summary, categories):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO articles (title, url, summary, categories) 
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (url) DO NOTHING;
        """, (title, url, summary, ", ".join(categories)))
        conn.commit()
    except Exception as e:
        print("DB Insert Error:", e)
    finally:
        cur.close()
        conn.close()

def scrape_kidshealth(interests):
    url = "https://kidshealth.org/en/parents/"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, "html.parser")
    for a in soup.select(".content-list a"):
        href = a.get("href")
        full_url = f"https://kidshealth.org{href}" if href.startswith("/") else href
        title = a.get_text(strip=True)
        summary = title
        categories = categorize_article_with_llm(title, summary, interests)
        insert_article(title, full_url, summary, categories)

def scrape_rcn(interests):
    url = "https://raisingchildren.net.au/guides/a-z-health-reference"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, "html.parser")
    for item in soup.select(".list-item a"):
        title = item.get_text(strip=True)
        full_url = f"https://raisingchildren.net.au{item.get('href')}"
        summary = title
        categories = categorize_article_with_llm(title, summary, interests)
        insert_article(title, full_url, summary, categories)

def scrape_understood(interests):
    url = "https://www.understood.org/en/articles"
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, "html.parser")
    for item in soup.select("a[data-testid='card-link']"):
        full_url = "https://www.understood.org" + item.get("href")
        title = item.get_text(strip=True)
        summary = title
        categories = categorize_article_with_llm(title, summary, interests)
        insert_article(title, full_url, summary, categories)

# Streamlit App
st.set_page_config(page_title="Personalized Parenting Feed", layout="wide")
st.title("🧠 Parenting Support Feed")

setup_database()

with st.form("interest_form"):
    name = st.text_input("Enter your name")
    selected_interests = st.multiselect(
        "Select your parenting interests",
        ["Special Needs", "Child Behavior", "Emotional Intelligence", "Parenting Tips", "Mental Health", "Parent-Child Bonding"]
    )
    submitted = st.form_submit_button("Submit")

if submitted:
    interests_str = ", ".join(selected_interests)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (name, interests) VALUES (%s, %s)", (name, interests_str))
    conn.commit()
    cur.close()
    conn.close()
    st.success("✅ Interests saved! Scraping articles for you...")

    with st.spinner("🔄 Scraping resources and articles..."):
        scrape_kidshealth(interests_str)
        scrape_rcn(interests_str)
        scrape_understood(interests_str)
    st.success("🎉 Articles scraped and stored!")

# Show personalized feed
st.subheader("📰 Your Personalized Feed")
conn = get_db_connection()
cur = conn.cursor()
cur.execute("SELECT title, url, summary, categories FROM articles ORDER BY scraped_at DESC LIMIT 15")
rows = cur.fetchall()
cur.close()
conn.close()

for title, url, summary, categories in rows:
    st.markdown(f"### [{title}]({url})")
    st.markdown(f"**Categories:** {categories}")
    st.markdown("---")

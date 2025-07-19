import streamlit as st
import psycopg2
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# --- CONFIG ---
DB_CONFIG = {
    'host': st.secrets["DB_HOST"],
    'dbname': st.secrets["DB_NAME"],
    'user': st.secrets["DB_USER"],
    'password': st.secrets["DB_PASSWORD"],
    'sslmode': 'require'
}

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)

# --- DATABASE SETUP ---
def connect_db():
    return psycopg2.connect(**DB_CONFIG)

def create_tables():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT,
            interests TEXT[]
        );
        CREATE TABLE IF NOT EXISTS articles (
            id SERIAL PRIMARY KEY,
            title TEXT,
            link TEXT,
            summary TEXT,
            categories TEXT[],
            user_id INT REFERENCES users(id)
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

# --- LLM CATEGORY TAGGING ---
def categorize_article_with_llm(title, summary, interests):
    prompt = f"""
    Classify this article into parenting-related categories like "special needs", "child behavior", "emotional intelligence", etc.
    Title: {title}
    Summary: {summary}
    User Interests: {interests}
    Return a list of tags only, separated by commas.
    """
    model = genai.GenerativeModel("gemini-pro")
    try:
        response = model.generate_content(prompt)
        tags = response.text.strip().split(",")
        return [tag.strip() for tag in tags if tag.strip()]
    except Exception as e:
        return ["Uncategorized"]

# --- SCRAPERS ---
def scrape_kidshealth():
    url = "https://kidshealth.org/en/parents/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    articles = []
    for item in soup.select(".content-list a"):
        title = item.get_text(strip=True)
        link = f"https://kidshealth.org{item.get('href')}"
        articles.append((title, "", link))
    return articles

def scrape_cdcgov():
    url = "https://www.cdc.gov/parents/index.html"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    articles = []
    for item in soup.select("ul.medium li a"):
        title = item.get_text(strip=True)
        link = "https://www.cdc.gov" + item.get("href")
        articles.append((title, "", link))
    return articles

def scrape_nichd():
    url = "https://www.nichd.nih.gov/newsroom/news"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    articles = []
    for item in soup.select("div.teaser__content a"):
        title = item.get_text(strip=True)
        link = "https://www.nichd.nih.gov" + item.get("href")
        articles.append((title, "", link))
    return articles

def scrape_understood():
    url = "https://www.understood.org/articles"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    articles = []
    for item in soup.select("a.card-content-link"):
        title = item.get_text(strip=True)
        link = "https://www.understood.org" + item.get("href")
        articles.append((title, "", link))
    return articles

def scrape_childwelfare():
    url = "https://www.childwelfare.gov/topics/parenting/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    articles = []
    for link in soup.select("a.resource-link"):
        title = link.get_text(strip=True)
        href = link.get("href")
        articles.append((title, "", f"https://www.childwelfare.gov{href}"))
    return articles

def scrape_all_sources():
    return (
        scrape_kidshealth() +
        scrape_cdcgov() +
        scrape_nichd() +
        scrape_understood() +
        scrape_childwelfare()
    )

# --- STORE ARTICLES ---
def store_articles(user_id, interests):
    conn = connect_db()
    cur = conn.cursor()
    articles = scrape_all_sources()
    for title, summary, link in articles:
        categories = categorize_article_with_llm(title, summary, interests)
        cur.execute('''
            INSERT INTO articles (title, link, summary, categories, user_id)
            VALUES (%s, %s, %s, %s, %s)
        ''', (title, link, summary, categories, user_id))
    conn.commit()
    cur.close()
    conn.close()

# --- STREAMLIT APP ---
def main():
    st.title("🧒 Personalized Parenting Feed")
    create_tables()

    name = st.text_input("Enter your name:")
    interests = st.multiselect("Choose your parenting interests:", [
        "Special Needs", "ADHD", "Autism", "Child Bonding", "Positive Parenting",
        "Teen Development", "Emotional Intelligence", "Child Behavior", "Parenting Tips", "Child Psychology", "Parenting Challenges", "Child Safety", "Healthy Parenting", "Parenting Resources", "Parenting Support", "Child Development", "Parenting Education", "Parenting Strategies", "Parenting Styles", "Parenting Advice", "Parenting Skills", "Parenting Techniques"
    ])

    if st.button("Submit") and name and interests:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (name, interests) VALUES (%s, %s) RETURNING id", (name, interests))
        user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        st.success("✅ Interests saved! Scraping articles now...")
        store_articles(user_id, interests)

    st.header("📚 Your Personalized Feed")
    if name:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE name=%s", (name,))
        row = cur.fetchone()
        if row:
            user_id = row[0]
            cur.execute("SELECT title, link, categories FROM articles WHERE user_id=%s", (user_id,))
            articles = cur.fetchall()
            if articles:
                for title, link, categories in articles:
                    st.markdown(f"### [{title}]({link})")
                    st.write(f"**Tags**: {', '.join(categories)}")
            else:
                st.info("No articles yet. Click submit to generate your feed.")
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()

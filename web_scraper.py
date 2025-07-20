import requests
from bs4 import BeautifulSoup
import psycopg2

DB_CONFIG = {
    "dbname": "neondb",
    "user": "neondb_owner",
    "password": "npg_NRo1IkM7bQrj",
    "host": "ep-morning-wildflower-a1wn2f3t-pooler.ap-southeast-1.aws.neon.tech",
    "port": 5432,
    "sslmode": "require"
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def setup_database():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS resources (
        id SERIAL PRIMARY KEY,
        title TEXT,
        url TEXT UNIQUE,
        summary TEXT,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

def scrape_parentcircle():
    url = "https://www.parentcircle.com/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    articles = []

    for item in soup.select("a[href*='/article/']")[:10]:
        link = item.get("href")
        title = item.get_text(strip=True)
        full_url = link if link.startswith("http") else f"https://www.parentcircle.com{link}"
        if title and link:
            articles.append({
                "title": title,
                "url": full_url,
                "summary": ""
            })
    print("Scraped Articles:", articles)
    return articles

def store_resources(resources):
    conn = get_db_connection()
    cur = conn.cursor()
    for resource in resources:
        try:
            print("Inserting:", resource["title"])
            cur.execute("""
                INSERT INTO resources (title, url, summary)
                VALUES (%s, %s, %s)
                ON CONFLICT (url) DO NOTHING
            """, (resource["title"], resource["url"], resource["summary"]))
        except Exception as e:
            print("Insert error:", e)
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    setup_database()
    resources = scrape_parentcircle()
    store_resources(resources)
    print("✅ Resources scraped and stored!")

from flask import Flask, request, jsonify
from flask_cors import CORS
import feedparser
import time
import threading
import os
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app) # Enable CORS for requests from your Streamlit frontend

# --- Database Configuration from .env ---
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# --- Function to get a database connection ---
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            sslmode='require' # Neon requires SSL
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

# --- Configuration for RSS Feeds ---
# Using a subset of the previously identified RSS feeds for demonstration.
# You can add more verified RSS feed URLs here.
RSS_FEED_CONFIG = [
    {
        "name": "ADDitude Magazine",
        "url": "https://additudemag.libsyn.com/rss", # Podcast feed, but demonstrates parsing structure
        "categories": ["ADHD", "Educational Support", "School Support", "Special Needs"]
    },
    {
        "name": "Janet Lansbury - Elevating Child Care",
        "url": "https://www.janetlansbury.com/feed",
        "categories": ["parenting", "Educational Support", "Family Activities"]
    },
    {
        "name": "Scary Mommy",
        "url": "https://scarymommy.com/rss",
        "categories": ["parenting", "Sleep", "Therapy Resources"]
    },
    {
        "name": "Wrightslaw Way",
        "url": "https://feeds.feedburner.com/TheWrig",
        "categories": ["Special Needs", "Educational Support", "School Support", "Therapy Resources"]
    },
    {
        "name": "The Autism Cafe",
        "url": "https://theautismcafe.com/feed",
        "categories": ["Autism", "sensory_issues", "Special Needs", "Therapy Resources"]
    },
    {
        "name": "Special Needs Jungle",
        "url": "https://www.specialneedsjungle.com/feed/",
        "categories": ["Special Needs", "Educational Support", "School Support", "Therapy Resources"]
    }
]

# --- Function to fetch and parse RSS feeds and store in DB ---
def fetch_and_parse_rss():
    print("Starting RSS fetch and parse and storing in Neon DB...")
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            print("Failed to connect to database. Skipping RSS fetch.")
            return

        cur = conn.cursor()
        articles_added_count = 0

        for config in RSS_FEED_CONFIG:
            feed_url = config["url"]
            source_name = config["name"]
            source_categories = config["categories"]
            print(f"  Fetching from: {source_name} ({feed_url})")
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries:
                    title = entry.title if hasattr(entry, 'title') else "No Title"
                    summary = entry.summary_detail.value if hasattr(entry, 'summary_detail') and hasattr(entry.summary_detail, 'value') else \
                              entry.description if hasattr(entry, 'description') else "No summary available."
                    article_url = entry.link if hasattr(entry, 'link') else None

                    image_url = None
                    if hasattr(entry, 'media_content') and entry.media_content:
                        for media in entry.media_content:
                            if 'type' in media and media['type'].startswith('image/'):
                                image_url = media['url']
                                break
                    elif hasattr(entry, 'enclosures') and entry.enclosures:
                        for enc in entry.enclosures:
                            if 'type' in enc and enc['type'].startswith('image/'):
                                image_url = enc['url']
                                break
                    if not image_url:
                        image_url = "https://placehold.co/300x200/CCCCCC/000000?text=No+Image"

                    # Parse published date
                    published_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        # Convert time.struct_time to datetime object
                        published_date = datetime(*entry.published_parsed[:6])

                    if article_url:
                        try:
                            # Check if article already exists using UNIQUE constraint on article_url
                            cur.execute(
                                "INSERT INTO articles (title, summary, image_url, article_url, source_name, published_date) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (article_url) DO NOTHING RETURNING id;",
                                (title, summary, image_url, article_url, source_name, published_date)
                            )
                            article_id_result = cur.fetchone()

                            if article_id_result: # If a new article was inserted
                                article_id = article_id_result[0]
                                articles_added_count += 1
                                print(f"        -> Added new article: {title}") # Added this print
                                # Insert categories for the new article
                                for category in source_categories:
                                    cur.execute(
                                        "INSERT INTO article_categories (article_id, category) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
                                        (article_id, category)
                                    )
                            else:
                                print(f"        -> Article already exists: {title}") # Added this print
                            conn.commit() # Commit after each article or batch
                        except Exception as insert_e:
                            conn.rollback()
                            print(f"      Error inserting article {article_url}: {insert_e}")
                    else:
                        print(f"      Skipping entry due to missing article_url: {title}")

            except Exception as e:
                print(f"  Error processing feed {source_name} ({feed_url}): {e}")
        print(f"  Finished processing feed from {source_name}.") # Added this print

        print(f"Finished RSS fetch. Added {articles_added_count} new articles to Neon DB.")

    except Exception as e:
        print(f"Overall database or fetching error: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

# --- Initial fetch on startup and scheduled fetching ---
def start_fetching_schedule():
    # Initial fetch
    fetch_and_parse_rss()

    # Schedule subsequent fetches (e.g., every 4 hours = 14400 seconds)
    interval_seconds = 14400 # 4 hours
    def schedule_loop():
        while True:
            time.sleep(interval_seconds)
            fetch_and_parse_rss()
    
    # Run in a separate thread to not block the Flask app
    scheduler_thread = threading.Thread(target=schedule_loop, daemon=True)
    scheduler_thread.start()

# Start the fetching process when the Flask app starts
# This will run in a separate thread
threading.Thread(target=start_fetching_schedule, daemon=True).start()

# --- Root Endpoint (to avoid 404) ---
@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to the Parenting Resource Backend! Use /api/articles to fetch data."}), 200

# --- API Endpoint ---
@app.route('/api/articles', methods=['GET'])
def get_articles():
    interests_param = request.args.get('interests', '')
    selected_interests = [i.strip() for i in interests_param.split(',') if i.strip()]

    conn = None
    articles = []
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cur = conn.cursor()

        if selected_interests:
            # Query to select articles based on selected categories
            # Using a subquery to find article_ids that match any of the selected interests
            # and then joining back to articles to get full details.
            # DISTINCT is used in the outer query to avoid duplicate articles if they belong
            # to multiple selected categories.
            query = """
                SELECT DISTINCT a.id, a.title, a.summary, a.image_url, a.article_url, a.source_name, a.published_date
                FROM articles a
                JOIN article_categories ac ON a.id = ac.article_id
                WHERE ac.category = ANY(%s)
                ORDER BY a.published_date DESC;
            """
            cur.execute(query, (selected_interests,))
        else:
            # If no interests are selected, return all articles
            query = """
                SELECT id, title, summary, image_url, article_url, source_name, published_date
                FROM articles
                ORDER BY published_date DESC;
            """
            cur.execute(query)
        
        # Fetch all rows and convert to list of dictionaries
        column_names = [desc[0] for desc in cur.description]
        articles = [dict(zip(column_names, row)) for row in cur.fetchall()]

        # Convert datetime objects to string for JSON serialization
        for article in articles:
            if isinstance(article.get('published_date'), datetime):
                article['published_date'] = article['published_date'].isoformat()

    except Exception as e:
        print(f"Database error during API query: {e}")
        return jsonify({"error": "Failed to retrieve articles"}), 500
    finally:
        if conn:
            cur.close()
            conn.close()

    return jsonify(articles)

# --- Main entry point for Flask app ---
if __name__ == '__main__':
    # Flask will run on http://127.0.0.1:5000 by default
    # use_reloader=False is important when using threading to prevent duplicate threads
    app.run(debug=True, use_reloader=False)

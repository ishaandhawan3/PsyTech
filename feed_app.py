# app.py
import streamlit as st
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import json
import google.generativeai as genai

# --- Gemini API setup ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('models/gemini-1.5-flash')

# --- Scraping Functions ---
def scrape_parenting_science():
    url = "https://www.parentingscience.com/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    articles = []
    for a in soup.select("a[href*='.html']"):
        text = a.get_text(strip=True)
        link = a.get("href")
        if link.startswith("http") and len(text) > 10:
            articles.append({"title": text, "url": link, "source": "Parenting Science"})
        elif len(text) > 10:
            articles.append({"title": text, "url": url + link, "source": "Parenting Science"})
    return articles[:15]  # Limit to top 15

# --- Summarize and Filter with Gemini ---
def personalize_articles(articles, interests):
    prompt = f"""
    A parent is interested in the following topics: {', '.join(interests)}.
    Given the following articles:
    {json.dumps(articles, indent=2)}
    
    Select the most relevant ones and provide a summary in this format:
    [
      {{"title": "...", "url": "...", "summary": "...", "source": "..."}},
      ...
    ]
    """
    response = model.generate_content(prompt)
    try:
        return json.loads(response.text)
    except:
        return []

# --- Streamlit UI ---
st.set_page_config(page_title="Personalized Parenting Feed")
st.title("👪 Personalized Parenting Feed")

interests = st.multiselect("Choose your topics:", [
    "Autism", "ADHD", "Positive Parenting", "Toddler Tantrums",
    "Sleep Training", "Nutrition", "Discipline", "Early Education"
])

if interests:
    with st.spinner("Fetching resources and personalizing..."):
        articles = scrape_parenting_science()
        personalized_feed = personalize_articles(articles, interests)

    if personalized_feed:
        st.subheader("Your Personalized Feed")
        for art in personalized_feed:
            st.markdown(f"### [{art['title']}]({art['url']})")
            st.markdown(f"*Source: {art['source']}*")
            st.markdown(art['summary'])
            st.markdown("---")
    else:
        st.warning("Couldn't generate a personalized feed. Try different topics or check your API key.")
else:
    st.info("Please select one or more topics to begin.")

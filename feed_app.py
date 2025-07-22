import streamlit as st
import requests # Import the requests library to make HTTP calls
import re # Import regex for HTML stripping

# --- Configuration for Backend API ---
# Ensure your Flask backend is running on this URL
BACKEND_API_URL = "http://127.0.0.1:5000/api/articles"

# --- All possible categories (must match categories used in your backend's RSS_FEED_CONFIG) ---
# In a more advanced setup, you might fetch these categories from a backend endpoint.
all_categories = sorted([
    "ADHD",
    "Autism",
    "Educational Support",
    "Family Activities",
    "Nutrition",
    "Sleep",
    "Screen Time",
    "Sibling Relationships",
    "School Support",
    "Therapy Resources",
    "Special Needs",
    "Developmental Milestones",
    "parenting", # General parenting category often used
    "sensory_issues" # Specific category from Autism Cafe
])

# --- Helper function to strip HTML tags ---
def strip_html_tags(text):
    """Removes HTML tags from a string."""
    if text is None:
        return ""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

# --- Function to fetch articles from the backend API ---
@st.cache_data(ttl=3600) # Cache data for 1 hour to reduce API calls
def get_articles_from_backend(interests):
    """
    Fetches articles from the Flask backend API based on selected interests.
    """
    params = {"interests": ",".join(interests)} if interests else {}
    try:
        response = requests.get(BACKEND_API_URL, params=params)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        articles = response.json()

        # Enhance relevance: Sort articles to prioritize those with keywords in title/summary
        if interests:
            def calculate_relevance(article):
                score = 0
                title = article.get('title', '').lower()
                summary = article.get('summary', '').lower()
                
                for interest in interests:
                    keyword = interest.lower()
                    if keyword in title:
                        score += 2 # Higher score for title match
                    if keyword in summary:
                        score += 1 # Lower score for summary match
                return score

            articles.sort(key=calculate_relevance, reverse=True)
            
        return articles
    except requests.exceptions.ConnectionError:
        st.error("Backend server is not reachable. Please ensure your Flask backend is running.")
        return []
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching articles from backend: {e}")
        return []

# --- Streamlit Application Layout ---
st.set_page_config(layout="wide", page_title="Parenting Resource Feed") # Changed to wide layout for 3 columns

st.title("👨‍👩‍👧‍👦 Parenting Resource Feed")

# Initialize session state for page navigation
if 'page' not in st.session_state:
    st.session_state.page = 'interest_selection'
if 'selected_interests' not in st.session_state:
    st.session_state.selected_interests = []

# --- Page 1: Interest Selection ---
if st.session_state.page == 'interest_selection':
    st.markdown("Please select your areas of interest to customize your feed:")

    current_selection = st.multiselect(
        "Choose your interests:",
        options=all_categories,
        default=[] # No default selections
    )
    # Update session state only when the multiselect value changes
    # This prevents unnecessary reruns if the user just clicks outside the multiselect
    if current_selection != st.session_state.selected_interests:
        st.session_state.selected_interests = current_selection

    if st.button("Show My Feed"):
        st.session_state.page = 'feed_display'
        # Clear cache for get_articles_from_backend when moving to feed display
        # This ensures fresh data is fetched based on new interests
        st.cache_data.clear()
        # Force a rerun to switch to the next page
        st.rerun() # Corrected: Added parentheses to st.rerun()

# --- Page 2: Feed Display ---
elif st.session_state.page == 'feed_display':
    st.subheader("Your Personalized Feed")

    # Fetch articles from the backend based on selected interests
    fetched_articles = get_articles_from_backend(st.session_state.selected_interests)

    # Limit to a maximum of 20 articles
    filtered_articles = fetched_articles[:20]

    if not filtered_articles:
        if st.session_state.selected_interests:
            st.warning("No articles found for your selected interests. Try going back and selecting different ones, or ensure the backend has fetched data for these categories!")
        else:
            st.info("No specific interests selected. Showing all available articles. Go back to select interests for a personalized feed.")
            # If no interests selected, fetch all articles (by passing empty list)
            # and then apply the limit.
            all_fetched_articles = get_articles_from_backend([])
            filtered_articles = all_fetched_articles[:20] # Apply limit here too

    if filtered_articles:
        # Create 3 columns for the cards
        cols = st.columns(3)
        for i, article in enumerate(filtered_articles):
            with cols[i % 3]: # Distribute articles across the 3 columns
                with st.container(border=True):
                    # Ensure all fields are accessed safely with .get()
                    image_url = article.get("image_url", "https://placehold.co/300x200/CCCCCC/000000?text=No+Image")
                    title = article.get('title', 'No Title')
                    summary = article.get('summary', 'No summary available.')
                    source_name = article.get('source_name', 'Unknown Source')
                    article_url = article.get('article_url', '#')
                    article_id_or_url = article.get('id', article_url) # Use ID if available, else URL for key

                    st.image(image_url, caption=source_name, use_column_width=True)
                    st.markdown(f"**{strip_html_tags(title)}**") # Strip HTML from title
                    
                    # Display first sentence or a truncated summary, stripping HTML
                    display_summary = strip_html_tags(summary)
                    display_summary = display_summary.split('.')[0] + '.' if '.' in display_summary else display_summary
                    st.write(display_summary)
                    st.markdown(f"Source: *{source_name}*")

                    # Use a unique key for each button to avoid Streamlit warnings
                    # Ensure key is a string and unique across all buttons
                    button_key = f"read_more_{article_id_or_url}_feed"
                    if st.button(f"Read More about '{strip_html_tags(title)}'", key=button_key):
                        # Toggle the state for this specific article's details
                        st.session_state[f"show_details_{article_id_or_url}"] = not st.session_state.get(f"show_details_{article_id_or_url}", False)

                    # Display full details if the state for this article is True
                    if st.session_state.get(f"show_details_{article_id_or_url}", False):
                        st.markdown("---")
                        st.markdown(f"**Full Summary:** {strip_html_tags(summary)}") # Strip HTML from full summary
                        # Use target='_blank' to open the link in a new tab
                        st.markdown(f"**Read the full article:** [Click here to go to {source_name}]({article_url})", unsafe_allow_html=True)
                        st.markdown("---")

    st.markdown("---")
    if st.button("Go Back to Select Interests"):
        st.session_state.page = 'interest_selection'
        # Clear cache for get_articles_from_backend when going back to selection,
        # so it refetches if interests change or on next "Show My Feed"
        st.cache_data.clear()
        st.rerun() # Corrected: Added parentheses to st.rerun()

st.caption("Note: This is a prototype. In a real mobile app, clicking 'Read More' would typically open the article in an in-app browser (WebView/Custom Tabs) for a seamless experience. Ensure your Flask backend is running for this app to function.")

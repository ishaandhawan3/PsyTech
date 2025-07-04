import streamlit as st
import pandas as pd
import os

# If using Gemini, import and set up the API
try:
    from google import genai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
except ImportError:
    genai = None

# Load activity data
@st.cache_data
def load_activities():
    try:
        return pd.read_csv("activities.csv", encoding="utf-8")
    except UnicodeDecodeError:
        # Try with a more permissive encoding
        return pd.read_csv("activities.csv", encoding="latin1")


# Generate AI-powered questions (Gemini or fallback)
def generate_questions(child_profile):
    if genai:
        prompt = (
            f"Generate 3 concise, parent-friendly questions to assess a child's needs for activity recommendations. "
            f"Child profile: {child_profile}. Questions should cover strengths, challenges, social, emotional, and physical aspects."
        )
        response = genai.Client().models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return [q.strip("- ").strip() for q in response.text.split("\n") if q.strip()]
    else:
        # Fallback static questions
        return [
            "What are your child's main strengths?",
            "What challenges does your child face most often?",
            "Are there any specific skills you want your child to improve?",
            "Does your child have any sensory sensitivities or physical limitations?",
            "What motivates or excites your child during play or learning?"
        ]

# Recommend activities based on answers and tags
def recommend_activities(answers, activities_df):
    # Simple keyword matching for demo; replace with Gemini for production
    keywords = " ".join(answers).lower()
    mask = (
        activities_df["Tags"].str.lower().str.contains(keywords) |
        activities_df["Helpful For Conditions"].str.lower().str.contains(keywords) |
        activities_df["Keywords"].str.lower().str.contains(keywords)
    )
    filtered = activities_df[mask]
    if filtered.empty:
        return activities_df.sample(3)  # fallback: random 3 activities
    return filtered

# Display full activity details
def show_activity_details(row):
    st.subheader(row["Activity Name"])
    st.markdown(f"**Metadata:** {row.get('Tags', '')}")
    st.markdown(f"**Helpful For Conditions:** {row.get('Helpful For Conditions', '')}")
    st.markdown(f"**Prerequisite:** {row.get('Prerequisite', 'See activity instructions or materials needed.')}")
    st.markdown(f"**Safety Instructions:** {row.get('Safety Instructions', 'Adult supervision recommended. Ensure safe environment.')}")
    st.markdown(f"**How to Perform Activity:** {row.get('How to Instructions - Manual', 'See instructions in activity database.')}")
    st.markdown(f"**Post Activity Feedback:** {row.get('Post Activity Feedback', 'How did your child respond? What went well? What was challenging?')}")
    st.markdown("---")

# Main Streamlit app
def main():
    st.title("AI Activity Recommendation for Children with Special Needs")
    st.write("Answer a few questions to get personalized activity recommendations for your child.")

    # Step 1: Collect child profile
    child_profile = st.text_area("Describe your child's age, strengths, challenges, and any diagnoses (e.g., ADHD, Autism, etc.):")

    if child_profile:
        st.markdown("### Step 2: Parent Questionnaire")
        questions = generate_questions(child_profile)
        answers = []
        for i, q in enumerate(questions):
            ans = st.text_input(q, key=f"q_{i}")
            answers.append(ans)
        if st.button("Get Recommendations"):
            activities_df = load_activities()
            recs = recommend_activities(answers, activities_df)
            st.markdown("## Recommended Activities")
            for _, row in recs.iterrows():
                show_activity_details(row)
                # Collect feedback
                feedback = st.text_area(f"Feedback for {row['Activity Name']}:", key=f"fb_{row['Activity Name']}")
                if st.button(f"Submit Feedback for {row['Activity Name']}", key=f"submit_{row['Activity Name']}"):
                    st.success("Thank you for your feedback!")
            st.markdown("## Analytics Report")
            st.info("Analytics and progress tracking will appear here as you use more activities and provide feedback.")

if __name__ == "__main__":
    main()

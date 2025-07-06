import streamlit as st
import pandas as pd
import os

# Optional: Gemini integration
try:
    from google import genai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
except ImportError:
    genai = None

@st.cache_data
def load_activities():
    try:
        df = pd.read_csv("activities.csv", encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv("activities.csv", encoding="latin1")
    df = df[df['Activity Name'].notna()]
    df = df[df['Activity Name'].astype(str).str.strip() != '']
    return df

def generate_questions(child_profile):
    if genai:
        prompt = (
            f"Generate 5 concise, parent-friendly questions to assess a child's needs for activity recommendations. "
            f"Child profile: {child_profile}. Questions should cover strengths, challenges, social, emotional, and physical aspects."
        )
        response = genai.Client().models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return [q.strip("- ").strip() for q in response.text.split("\n") if q.strip()]
    else:
        return [
            "What are your child's main strengths?",
            "What challenges does your child face most often?",
            "Are there any specific skills you want your child to improve?",
            "Does your child have any sensory sensitivities or physical limitations?",
            "What motivates or excites your child during play or learning?"
        ]

def recommend_activities(answers, activities_df):
    keywords = " ".join(answers).lower()
    mask = (
        activities_df["Focus Area(s)"].astype(str).str.lower().str.contains(keywords) |
        activities_df["Analyze Progress"].astype(str).str.lower().str.contains(keywords) |
        activities_df["Illness Attached"].astype(str).str.lower().str.contains(keywords) |
        activities_df["Other Keywords"].astype(str).str.lower().str.contains(keywords)
    )
    filtered = activities_df[mask]
    if filtered.empty:
        return activities_df.sample(3)
    return filtered

def generate_activity_details(activity_row):
    activity_name = activity_row["Activity Name"]
    # Collect all metadata fields, only if they exist and are not empty
    metadata = []
    if pd.notna(activity_row.get("Focus Area(s)", "")) and activity_row.get("Focus Area(s)", "").strip():
        metadata.append(f"**Focus Area(s):** {activity_row['Focus Area(s)']}")
    if pd.notna(activity_row.get("Analyze Progress", "")) and activity_row.get("Analyze Progress", "").strip():
        metadata.append(f"**Key Skills/Goals:** {activity_row['Analyze Progress']}")
    if pd.notna(activity_row.get("Illness Attached", "")) and activity_row.get("Illness Attached", "").strip():
        metadata.append(f"**Helpful For:** {activity_row['Illness Attached']}")
    if pd.notna(activity_row.get("Other Keywords", "")) and activity_row.get("Other Keywords", "").strip():
        metadata.append(f"**Keywords:** {activity_row['Other Keywords']}")
    if pd.notna(activity_row.get("Parent Description", "")) and activity_row.get("Parent Description", "").strip():
        metadata.append(f"**Parent Descriptions:** {activity_row['Parent Description']}")

    # Join metadata as normal text (not heading, not bold block)
    meta_str = "\n".join(metadata)
    return f"""
**Activity Name:** {activity_name}

{meta_str}
"""


def main():
    st.title("Child Wellness Companion")
    st.write("Answer a few questions to get personalized activity recommendations for your child's well being.")

    activities_df = load_activities()

    if 'profile' not in st.session_state:
        st.session_state['profile'] = None
    if 'recs' not in st.session_state:
        st.session_state['recs'] = None

    # PART 1: Show the form only if profile is not yet submitted
    if st.session_state['profile'] is None:
        with st.form("child_profile_form"):
            child_name = st.text_input("Child's Name")
            child_age = st.text_input("Child's Age")
            child_strengths = st.text_input("Child's Strengths (e.g., creative, social, focused)")
            child_challenges = st.text_input("Child's Challenges (e.g., attention, sensory, social)")
            child_diagnoses = st.text_input("Previous Diagnoses (e.g., ADHD, Autism, None)")
            any_other_information = st.text_input("Any Other Information(optional)")
            submitted = st.form_submit_button("Submit Profile")

        if submitted:
            if not (child_name and child_age and child_strengths and child_challenges and child_diagnoses):
                st.error("Please fill out all fields before submitting.")
            else:
                st.session_state['profile'] = {
                    "name": child_name,
                    "age": child_age,
                    "strengths": child_strengths,
                    "challenges": child_challenges,
                    "diagnoses": child_diagnoses,
                    "other_info": any_other_information
                }
                st.success("Profile submitted!")

    # PART 2: Show the profile summary if profile is submitted
    if st.session_state['profile'] is None:
        with st.form("child_profile_form"):
            child_name = st.text_input("Child's Name")
            child_age = st.text_input("Child's Age")
            child_strengths = st.text_input("Child's Strengths (e.g., creative, social, focused)")
            child_challenges = st.text_input("Child's Challenges (e.g., attention, sensory, social)")
            child_diagnoses = st.text_input("Previous Diagnoses (e.g., ADHD, Autism, None)")
            any_other_information = st.text_input("Any Other Information (optional)")
            submitted = st.form_submit_button("Submit Profile")

        if submitted:
            # Only check the mandatory fields (exclude 'any_other_information')
            if not (child_name and child_age and child_strengths and child_challenges and child_diagnoses):
                st.error("Please fill out all mandatory fields before submitting.")
            else:
                st.session_state['profile'] = {
                    "name": child_name,
                    "age": child_age,
                    "strengths": child_strengths,
                    "challenges": child_challenges,
                    "diagnoses": child_diagnoses,
                    "other_info": any_other_information  # This can be empty
                }
                st.success("Profile submitted!")


        # Step 2: Questionnaire
        if st.session_state['recs'] is None:
            st.markdown("Questionnaire")
            questions = generate_questions(profile)
            answers = []
            for i, q in enumerate(questions):
                ans = st.text_input(q, key=f"questionnaire_q_{i}")
                answers.append(ans)
            if st.button("Get Recommendations", key="get_recommendations"):
                recs = recommend_activities(answers, activities_df)
                st.session_state['recs'] = recs.reset_index(drop=True)

    # Step 3: Display recommendations (activity name and metadata only)
    if st.session_state['recs'] is not None:
        st.markdown("## Recommended Activities")
        recs = st.session_state['recs']
        for idx, row in recs.iterrows():
            details = generate_activity_details(row)
            st.markdown(details)

        if st.button("Start Over", key="start_over"):
            st.session_state['profile'] = None
            st.session_state['recs'] = None

if __name__ == "__main__":
    main()

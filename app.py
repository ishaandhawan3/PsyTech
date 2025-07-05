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

# Load activity data with encoding fallback and filter out empty activity names
@st.cache_data
def load_activities():
    try:
        df = pd.read_csv("activities.csv", encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv("activities.csv", encoding="latin1")
    # Remove rows with missing or blank activity names
    df = df[df['Activity Name'].notna()]
    df = df[df['Activity Name'].astype(str).str.strip() != '']
    return df

# Generate AI-powered questions (Gemini or fallback)
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

# Recommend activities based on answers and tags/keywords
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

# Generate detailed activity info using Gemini
def generate_activity_details(activity_row):
    activity_name = activity_row["Activity Name"]
    metadata = []
    if pd.notna(activity_row.get("Focus Area(s)", "")):
        metadata.append(f"Focus Area(s): {activity_row['Focus Area(s)']}")
    if pd.notna(activity_row.get("Analyze Progress", "")):
        metadata.append(f"Key Skills/Goals: {activity_row['Analyze Progress']}")
    if pd.notna(activity_row.get("Illness Attached", "")):
        metadata.append(f"Helpful For: {activity_row['Illness Attached']}")
    if pd.notna(activity_row.get("Other Keywords", "")):
        metadata.append(f"Keywords: {activity_row['Other Keywords']}")
    if pd.notna(activity_row.get("Parent Description", "")):
        metadata.append(f"Parent Descriptions: {activity_row['Parent Description']}")

    meta_str = "\n".join(metadata)
    if genai:
        prompt = f"""
You are an expert in child development and therapy. For the following activity, generate a detailed, structured report for parents of children with special needs (including but not limited to autism, ADHD, learning disabilities, and physical challenges).

Activity Name: {activity_name}

Activity Metadata:
{meta_str}

For this activity, provide:
1. Activity Name
2. Activity Metadata (summarize focus area, suitable age group, and key developmental skills or goals)
3. Prerequisite (list materials, skills, or setup needed)
4. Safety Instructions (clear, concise, and age-appropriate)
5. How to Perform Activity (step-by-step instructions)
6. Post Activity Feedback (questions for parent/child to reflect on the experience)
7. Analytics Report (what to track, how to measure progress or engagement)

Format the output for this activity as:

---
**Activity Name:** [Name]

**Activity Metadata:**  
[Metadata]

**Prerequisite:**  
[List]

**Safety Instructions:**  
[List]

**How to Perform Activity:**  
[Step-by-step instructions]

**Post Activity Feedback:**  
[List of questions]

**Analytics Report:**  
[What to track, how to measure progress]

---
"""
        response = genai.Client().models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text
    else:
        # Fallback: simple template using available data
        return f"""
---
**Activity Name:** {activity_name}

**Activity Metadata:**  
{meta_str}

**Prerequisite:**  
See activity instructions or materials needed.

**Safety Instructions:**  
Adult supervision recommended. Ensure safe environment.

**How to Perform Activity:**  
See instructions in activity database.

**Post Activity Feedback:**  
How did your child respond? What went well? What was challenging?

**Analytics Report:**  
Track engagement, skill improvement, and parent/child feedback over time.
---
"""

def main():
    st.title("Child Wellness Companion")
    st.write("Answer a few questions to get personalized activity recommendations for your child's well being.")

    activities_df = load_activities()

    # Use session state to persist profile, recommendations, and feedback
    if 'profile' not in st.session_state:
        st.session_state['profile'] = None
    if 'recs' not in st.session_state:
        st.session_state['recs'] = None
    if 'feedback' not in st.session_state:
        st.session_state['feedback'] = {}

    # Initialize session state for profile if not present
    if 'profile' not in st.session_state:
        st.session_state['profile'] = None

    # PART 1: Show the form only if profile is not yet submitted
    if st.session_state['profile'] is None:
        with st.form("child_profile_form"):
            child_name = st.text_input("Child's Name")
            child_age = st.text_input("Child's Age")
            child_strengths = st.text_input("Child's Strengths (e.g., creative, social, focused)")
            child_challenges = st.text_input("Child's Challenges (e.g., attention, sensory, social)")
            child_diagnoses = st.text_input("Diagnoses (e.g., ADHD, Autism, None)")
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
                    "diagnoses": child_diagnoses
                }
                st.success("Profile submitted!")

    # PART 2: Show the profile summary if profile is submitted
    if st.session_state['profile'] is not None:
        profile = st.session_state['profile']
        st.markdown("#### Profile Summary")
        st.write(
            f"Name: {profile.get('name', '')}\n\n"
            f"Age: {profile.get('age', '')}\n\n"
            f"Strengths: {profile.get('strengths', '')}\n\n"
            f"Challenges: {profile.get('challenges', '')}\n\n"
            f"Diagnoses: {profile.get('diagnoses', '')}"
        )


        # Step 2: Questionnaire
        if st.session_state['recs'] is None:
            st.markdown("### Step 2: Parent Questionnaire")
            questions = generate_questions(profile)
            answers = []
            for i, q in enumerate(questions):
                ans = st.text_input(q, key=f"questionnaire_q_{i}")
                answers.append(ans)
            if st.button("Get Recommendations", key="get_recommendations"):
                recs = recommend_activities(answers, activities_df)
                st.session_state['recs'] = recs.reset_index(drop=True)

    # Step 3: Display recommendations and feedback
    if st.session_state['recs'] is not None:
        st.markdown("## Recommended Activities")
        recs = st.session_state['recs']
        for idx, row in recs.iterrows():
            details = generate_activity_details(row)
            st.markdown(details)
            feedback_key = f"fb_{row['Activity Name']}_{idx}"
            feedback = st.text_area(f"Feedback for {row['Activity Name']}:", key=feedback_key)
            submit_key = f"submit_{row['Activity Name']}_{idx}"
            if st.button(f"Submit Feedback for {row['Activity Name']}", key=submit_key):
                st.session_state['feedback'][row['Activity Name']] = feedback
                st.success("Thank you for your feedback!")
            if row['Activity Name'] in st.session_state['feedback']:
                st.markdown(f"**Your Feedback:** {st.session_state['feedback'][row['Activity Name']]}")

        if st.button("Start Over", key="start_over"):
            st.session_state['profile'] = None
            st.session_state['recs'] = None
            st.session_state['feedback'] = {}

if __name__ == "__main__":
    main()



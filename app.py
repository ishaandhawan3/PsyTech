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

def recommend_activities(form_data, activities_df):
    # Combine all form answers into a single string for keyword matching
    keywords = " ".join([str(v) for v in form_data.values() if v]).lower()
    mask = (
        activities_df["Focus Area(s)"].astype(str).str.lower().str.contains(keywords) |
        activities_df["Analyze Progress"].astype(str).str.lower().str.contains(keywords) |
        activities_df["Illness Attached"].astype(str).str.lower().str.contains(keywords) |
        activities_df["Other Keywords"].astype(str).str.lower().str.contains(keywords) |
        activities_df["Parent Description"].astype(str).str.lower().str.contains(keywords)
    )
    filtered = activities_df[mask]
    # If less than 5, generate more using AI
    if filtered.shape[0] < 5:
        num_to_generate = 5 - filtered.shape[0]
        ai_activities = []
        if genai:
            # Use the first 3 activities as style reference
            sample_acts = filtered.head(3).to_dict(orient="records")
            prompt = (
                f"Based on this child profile: {form_data}, "
                f"and these example activities: {sample_acts}, "
                f"generate {num_to_generate} new, unique activity recommendations. "
                "Each activity should include: Activity Name, Focus Area(s), Key Skills/Goals, Helpful For, Keywords, Parent Descriptions. "
                "Format as a JSON list of dicts with these keys: 'Activity Name', 'Focus Area(s)', 'Analyze Progress', 'Illness Attached', 'Other Keywords', 'Parent Description'."
            )
            response = genai.Client().models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            import json
            try:
                ai_activities = json.loads(response.text)
            except Exception:
                ai_activities = []
        # Convert AI activities to DataFrame and append
        if ai_activities:
            ai_df = pd.DataFrame(ai_activities)
            filtered = pd.concat([filtered, ai_df], ignore_index=True)
        else:
            # Fallback: fill with random activities not already selected
            extra = activities_df[~activities_df.index.isin(filtered.index)].sample(num_to_generate)
            filtered = pd.concat([filtered, extra])
    else:
        filtered = filtered.head(5)
    return filtered

def generate_activity_details(activity_row):
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
    meta_str = "\n".join(metadata)
    return meta_str

def main():
    st.title("Child Wellness Companion")
    st.write("Fill out the form below to get personalized activity recommendations for your child.")

    activities_df = load_activities()

    if 'profile' not in st.session_state:
        st.session_state['profile'] = None
    if 'recs' not in st.session_state:
        st.session_state['recs'] = None

    # Single form for all questions
    if st.session_state['profile'] is None:
        with st.form("child_profile"):
            child_name = st.text_input("Child's Name")
            child_age = st.text_input("Child's Age")
            child_strengths = st.text_input("Child's Strengths (e.g., creative, social, focused)")
            child_challenges = st.text_input("Child's Challenges (e.g., attention, sensory, social)")
            child_diagnoses = st.text_input("Previous Diagnoses (e.g., ADHD, Autism, None)")
            skills_to_improve = st.text_input("Are there any specific skills you want your child to improve?")
            sensory_physical = st.text_input("Does your child have any sensory sensitivities or physical limitations?")
            motivation = st.text_input("What motivates or excites your child during play or learning?")
            any_other_information = st.text_input("Any Other Information (optional)")
            submitted = st.form_submit_button("Submit Profile")

        if submitted:
            if not (child_name and child_age and child_strengths and child_challenges and child_diagnoses and skills_to_improve and sensory_physical and motivation):
                st.error("Please fill out all mandatory fields before submitting.")
            else:
                st.session_state['profile'] = {
                    "name": child_name,
                    "age": child_age,
                    "strengths": child_strengths,
                    "challenges": child_challenges,
                    "diagnoses": child_diagnoses,
                    "skills_to_improve": skills_to_improve,
                    "sensory_physical": sensory_physical,
                    "motivation": motivation,
                    "other_info": any_other_information
                }
                st.success("Profile submitted!")

    # Show the profile summary and recommendations if profile is submitted
    if st.session_state['profile'] is not None:
        profile = st.session_state['profile']
        st.markdown("#### Profile Summary")
        st.write(
            f"Name: {profile.get('name', '')}\n\n"
            f"Age: {profile.get('age', '')}\n\n"
            f"Strengths: {profile.get('strengths', '')}\n\n"
            f"Challenges: {profile.get('challenges', '')}\n\n"
            f"Diagnoses: {profile.get('diagnoses', '')}\n\n"
            f"Skills to Improve: {profile.get('skills_to_improve', '')}\n\n"
            f"Sensory/Physical Limitations: {profile.get('sensory_physical', '')}\n\n"
            f"Motivation: {profile.get('motivation', '')}\n\n"
            f"Other Info: {profile.get('other_info', '')}"
        )

        if st.session_state['recs'] is None:
            # Recommend activities based on all form input
            recs = recommend_activities(profile, activities_df)
            st.session_state['recs'] = recs.reset_index(drop=True)

    # Display recommendations (activity name as dropdown, metadata inside)
    if st.session_state['recs'] is not None:
        st.markdown("## Recommended Activities")
        recs = st.session_state['recs']
        for idx, row in recs.iterrows():
            with st.expander(row["Activity Name"]):
                details = generate_activity_details(row)
                st.markdown(details)

        if st.button("Start Over", key="start_over"):
            st.session_state['profile'] = None
            st.session_state['recs'] = None

if __name__ == "__main__":
    main()

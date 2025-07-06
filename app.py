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

def ai_generate_tags(form_data, sample_acts):
    prompt = (
        f"You are an expert in child development and therapy. "
        f"Given this child profile: {form_data}, "
        f"and these example activities: {sample_acts}, "
        "generate a new, unique activity recommendation. "
        "For this activity, generate the following fields in the exact format below:\n"
        "- Activity Name: (short, descriptive, unique, and relevant to the profile)\n"
        "- Focus Area: (comma-separated, e.g. Fine Motor, Cognitive; must be specific and relevant)\n"
        "- Conditions: (comma-separated, e.g. ADHD, Autism, etc.; must be relevant to the profile and activity)\n"
        "- Keywords: (comma-separated, e.g. puzzles, matching, visual, etc.; must be specific to the activity)\n"
        "Do not use dashes or placeholders. All fields must be filled with realistic, relevant values. "
        "Format your response as a JSON dict with these exact keys: 'Activity Name', 'Focus Area', 'Conditions', 'Keywords'."
    )
    response = genai.Client().models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    import json
    try:
        tags = json.loads(response.text)
        # Fallback: If any field is empty, fill with a generic but relevant value
        for field in ["Activity Name", "Focus Area", "Conditions", "Keywords"]:
            if field not in tags or not str(tags[field]).strip():
                tags[field] = "General" if field == "Focus Area" else "See activity description"
        return tags
    except Exception:
        return {
            "Activity Name": "Engagement Activity",
            "Focus Area": "Cognitive, Fine Motor",
            "Conditions": "ADHD, Autism",
            "Keywords": "puzzles, matching, visual, focus"
        }

def extract_tags(activity_row):
    # Focus Area
    focus_area = activity_row.get("Focus Area(s)", "—")
    # Conditions
    conditions = activity_row.get("Illness Attached", "—")
    # Keywords
    keywords = activity_row.get("Other Keywords", "—")
    # Activity Name
    activity_name = activity_row.get("Activity Name", "—")
    return {
        "Activity Name": activity_name if str(activity_name).strip() else "—",
        "Focus Area": focus_area if str(focus_area).strip() else "—",
        "Conditions": conditions if str(conditions).strip() else "—",
        "Keywords": keywords if str(keywords).strip() else "—"
    }

def recommend_activities(form_data, activities_df):
    keywords = " ".join([str(v) for v in form_data.values() if v]).lower()
    mask = (
        activities_df["Focus Area(s)"].astype(str).str.lower().str.contains(keywords) |
        activities_df["Analyze Progress"].astype(str).str.lower().str.contains(keywords) |
        activities_df["Illness Attached"].astype(str).str.lower().str.contains(keywords) |
        activities_df["Other Keywords"].astype(str).str.lower().str.contains(keywords) |
        activities_df["Parent Description"].astype(str).str.lower().str.contains(keywords)
    )
    filtered = activities_df[mask]
    tag_rows = []
    for idx, row in filtered.iterrows():
        tags = extract_tags(row)
        tag_rows.append(tags)
    # If less than 5, generate more using AI (with real activity names)
    if len(tag_rows) < 5 and genai:
        num_to_generate = 5 - len(tag_rows)
        sample_acts = tag_rows[:3]
        for _ in range(num_to_generate):
            ai_tags = ai_generate_tags(form_data, sample_acts)
            tag_rows.append(ai_tags)
    elif len(tag_rows) < 5:
        # Fallback: fill with dashes and generic names
        for i in range(5 - len(tag_rows)):
            tag_rows.append({
                "Activity Name": f"Activity {i+1+len(tag_rows)}",
                "Focus Area": "—",
                "Conditions": "—",
                "Keywords": "—"
            })
    return tag_rows[:5]

def display_activity(activity):
    st.markdown(
        f"<div style='font-size:1.3em; font-weight:bold; margin-bottom:0.2em'>{activity['Activity Name']}</div>",
        unsafe_allow_html=True
    )
    st.markdown("**Tags**")
    st.markdown(f"Focus Area: {activity['Focus Area']}")
    st.markdown(f"Conditions: {activity['Conditions']}")
    st.markdown(f"Keywords: {activity['Keywords']}")

def main():
    st.title("Child Wellness Companion")
    st.write("Fill out the form below to get personalized activity recommendations for your child.")

    activities_df = load_activities()

    if 'profile' not in st.session_state:
        st.session_state['profile'] = None
    if 'recs' not in st.session_state:
        st.session_state['recs'] = None

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

    if st.session_state['profile'] is not None:
        profile = st.session_state['profile']
        st.markdown("#### Profile Summary")
        st.write(
            f"Name: {profile.get('name', '')}\n"
            f"Age: {profile.get('age', '')}\n"
            f"Strengths: {profile.get('strengths', '')}\n"
            f"Challenges: {profile.get('challenges', '')}\n"
            f"Diagnoses: {profile.get('diagnoses', '')}\n"
            f"Skills to Improve: {profile.get('skills_to_improve', '')}\n"
            f"Sensory/Physical Limitations: {profile.get('sensory_physical', '')}\n"
            f"Motivation: {profile.get('motivation', '')}\n"
            f"Other Info: {profile.get('other_info', '')}"
        )

        if st.session_state['recs'] is None:
            tag_rows = recommend_activities(profile, activities_df)
            st.session_state['recs'] = tag_rows

    if st.session_state['recs'] is not None:
        st.markdown("## Recommended Activities")
        for activity in st.session_state['recs']:
            name = activity.get("Activity Name", "")
            if not isinstance(name, str) or not name.strip():
                name = "Unnamed Activity"
            with st.expander(name):
                display_activity(activity)

        if st.button("Start Over", key="start_over"):
            st.session_state['profile'] = None
            st.session_state['recs'] = None

if __name__ == "__main__":
    main()

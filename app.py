import streamlit as st
import pandas as pd
import os
import re
import google.generativeai as genai

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)


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
    import json

    prompt = f"""
    You are a child therapist.

    CHILD PROFILE:
    {form_data}

    SAMPLE ACTIVITIES:
    {sample_acts}

    Generate ONE highly personalized activity. Respond ONLY with JSON (no code formatting), like this:

    {{
    "Activity Name": "Emotion Safari",
    "Focus Area": "Emotional Regulation, Visual Processing",
    "Conditions": "Autism, ADHD",
    "Keywords": "animals, matching cards, emotion expressions"
    }}
    """

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        raw = response.text.strip()

        # st.write("🔍 Gemini Response:", raw)  # Debug output


        # Remove code block formatting if present
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.IGNORECASE)

        # Try to parse
        tags = json.loads(raw)


        # Validate all required fields
        for key in ["Activity Name", "Focus Area", "Conditions", "Keywords"]:
            if key not in tags or not str(tags[key]).strip():
                raise ValueError(f"Missing field: {key}")

        return tags

    except Exception as e:
        st.warning(f"⚠️ Gemini failed: {e}")
        return {
            "Activity Name": "Engagement Activity",
            "Focus Area": "Cognitive, Fine Motor",
            "Conditions": "ADHD, Autism",
            "Keywords": "puzzles, matching, visual, focus"
        }

    


def extract_tags(activity_row):
    import pandas as pd
    def clean(val):
        if pd.isna(val) or val is None or str(val).strip().lower() in ["", "nan", "none", "—"]:
            return "—"
        return str(val).strip()
    return {
        "Activity Name": clean(activity_row.get("Activity Name", "—")),
        "Focus Area": clean(activity_row.get("Focus Area(s)", "—")),
        "Conditions": clean(activity_row.get("Illness Attached", "—")),
        "Keywords": clean(activity_row.get("Other Keywords", "—"))
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
        # pass at most 3 sample rows for style
        sample_acts = tag_rows[:3]
        for _ in range(num_to_generate):
            tag_rows.append(ai_generate_tags(form_data, sample_acts))

    elif len(tag_rows) < 5:
        # Fallback: fill with generic values
        for i in range(5 - len(tag_rows)):
            tag_rows.append({
                "Activity Name": f"Engagement Activity {i+1+len(tag_rows)}",
                "Focus Area": "Cognitive, Fine Motor",
                "Conditions": "ADHD, Autism",
                "Keywords": "puzzles, matching, visual, focus"
            })
    return tag_rows[:5]

def display_activity(activity):
    """Pretty print one activity — works in light & dark mode."""
    st.markdown(
        f"<div style='font-size:1.35rem; font-weight:700; margin-bottom:0.4rem;'>"
        f"{activity['Activity Name']}</div>",
        unsafe_allow_html=True
    )
    # each field on its own line, inheriting Streamlit theme colours
    st.markdown(f"**Focus Area:** {activity['Focus Area']}")
    st.markdown(f"**Conditions:** {activity['Conditions']}")
    st.markdown(f"**Keywords:** {activity['Keywords']}")


def main():
    st.title("Child Wellness Companion")
    st.write("Fill out the form below to get personalized activity recommendations for your child.")

    activities_df = load_activities()

    if 'profile' not in st.session_state:
        st.session_state['profile'] = None
    if 'recs' not in st.session_state:
        st.session_state['recs'] = None

    # FORM
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

    # PROFILE SUMMARY + RECOMMENDATIONS
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
            tag_rows = recommend_activities(profile, activities_df)
            st.session_state['recs'] = tag_rows

    # DISPLAY RECOMMENDED ACTIVITIES
    if st.session_state['recs'] is not None:
        st.markdown("## Recommended Activities")
        for activity in st.session_state['recs']:
            if not isinstance(activity, dict):
                continue  # skip invalid data
            
            name = activity.get("Activity Name", "").strip() or "Unnamed Activity"
            with st.expander(name):
                display_activity(activity)

        if st.button("Start Over", key="start_over"):
            st.session_state['profile'] = None
            st.session_state['recs'] = None

if __name__ == "__main__":
    main()


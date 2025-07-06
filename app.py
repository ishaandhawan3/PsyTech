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

def ai_generate_tags(activity_name, form_data, sample_acts):
    prompt = (
        f"You are an expert in child development and therapy. "
        f"Given this child profile: {form_data}, "
        f"and these example activities: {sample_acts}, "
        f"generate a new activity with the name '{activity_name}'. "
        "For this activity, generate the following tags in the exact format below:\n"
        "- Focus Area: (comma-separated, e.g. Fine Motor, Cognitive)\n"
        "- Age Group: (e.g. 4–6, 6–8, 8–10, 10+, or a range like 4–10+)\n"
        "- Conditions: (comma-separated, e.g. ADHD, Autism, etc.)\n"
        "- Keywords: (comma-separated, e.g. puzzles, matching, visual, etc.)\n"
        "If a tag is not applicable, use a dash (—). Format your response as a JSON dict with these exact keys: 'Focus Area', 'Age Group', 'Conditions', 'Keywords'."
    )
    response = genai.Client().models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    import json
    try:
        tags = json.loads(response.text)
        for field in ["Focus Area", "Age Group", "Conditions", "Keywords"]:
            if field not in tags or not str(tags[field]).strip():
                tags[field] = "—"
        return tags
    except Exception:
        return {field: "—" for field in ["Focus Area", "Age Group", "Conditions", "Keywords"]}

def extract_tags(activity_row):
    # Focus Area
    focus_area = activity_row.get("Focus Area(s)", "—")
    # Age Group: collect all age columns with a checkmark
    age_cols = [
        ("4–6: Early Childhood Education", "4–6"),
        ("6–8: Social, Emotional, Behavioral", "6–8"),
        ("8–10: Focus, Engagement", "8–10"),
        ("10+", "10+")
    ]
    age_group = []
    for col, label in age_cols:
        val = str(activity_row.get(col, "")).strip()
        if val in ["✔️", "(✔️)"]:
            age_group.append(label)
    age_group_str = ", ".join(age_group) if age_group else "—"
    # Conditions
    conditions = activity_row.get("Illness Attached", "—")
    # Keywords
    keywords = activity_row.get("Other Keywords", "—")
    return {
        "Focus Area": focus_area if str(focus_area).strip() else "—",
        "Age Group": age_group_str,
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
    # If less than 5, generate more using AI (full tags)
    if filtered.shape[0] < 5 and genai:
        num_to_generate = 5 - filtered.shape[0]
        sample_acts = filtered.head(3).to_dict(orient="records")
        ai_activity_names = [f"AI Activity {i+1}" for i in range(num_to_generate)]
        ai_activities = []
        for name in ai_activity_names:
            tags = ai_generate_tags(name, form_data, sample_acts)
            ai_activities.append({
                "Activity Name": name,
                **tags
            })
        ai_df = pd.DataFrame(ai_activities)
        filtered = pd.concat([filtered, ai_df], ignore_index=True)
    else:
        filtered = filtered.head(5)
    # For all activities, ensure tags are present and filled (use AI for missing if possible)
    tag_rows = []
    for idx, row in filtered.iterrows():
        if "Focus Area" in row and "Age Group" in row and "Conditions" in row and "Keywords" in row:
            tags = {
                "Focus Area": row["Focus Area"],
                "Age Group": row["Age Group"],
                "Conditions": row["Conditions"],
                "Keywords": row["Keywords"]
            }
        else:
            # Extract from CSV or use AI if missing
            tags = extract_tags(row)
            # If any tag is missing, try to fill with AI
            if genai and any(v == "—" for v in tags.values()):
                ai_tags = ai_generate_tags(row.get("Activity Name", f"Activity {idx+1}"), form_data, sample_acts)
                for k in tags:
                    if tags[k] == "—" and ai_tags[k] != "—":
                        tags[k] = ai_tags[k]
        tag_rows.append({
            "Activity Name": row.get("Activity Name", f"Activity {idx+1}"),
            **tags
        })
    return tag_rows

def display_activity(activity):
    st.markdown(
        f"<div style='font-size:1.3em; font-weight:bold; margin-bottom:0.2em'>{activity['Activity Name']}</div>",
        unsafe_allow_html=True
    )
    st.markdown("**Tags**")
    st.markdown(f"- **Focus Area:** {activity['Focus Area']}")
    st.markdown(f"- **Age Group:** {activity['Age Group']}")
    st.markdown(f"- **Conditions:** {activity['Conditions']}")
    st.markdown(f"- **Keywords:** {activity['Keywords']}")

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
            with st.expander(activity["Activity Name"]):
                display_activity(activity)

        if st.button("Start Over", key="start_over"):
            st.session_state['profile'] = None
            st.session_state['recs'] = None

if __name__ == "__main__":
    main()

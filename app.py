###############################################################################
#  Child Wellness Companion – final working version
###############################################################################
import streamlit as st
import pandas as pd
import os, re, json
import google.generativeai as genai

# ─────────────────────────────────────────────────────────────────────────────
# Gemini setup
# ─────────────────────────────────────────────────────────────────────────────
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# ─────────────────────────────────────────────────────────────────────────────
# 1. Load and clean activities.csv
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_activities():
    try:
        df = pd.read_csv("activities.csv", encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv("activities.csv", encoding="latin1")

    # drop totally empty “Unnamed” cols created by Excel
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    # keep only rows with a non‑blank name
    df = df[df["Activity Name"].astype(str).str.strip() != ""]
    df = df.reset_index(drop=True)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 2. Utility: extract four meta‑fields from one CSV row
# ─────────────────────────────────────────────────────────────────────────────
def extract_tags(row):
    def clean(x):
        if pd.isna(x) or str(x).strip().lower() in {"", "nan", "none", "—"}:
            return "—"
        return str(x).strip()

    return {
        "Activity Name": clean(row.get("Activity Name")),
        "Focus Area":    clean(row.get("Focus Area(s)")),
        "Conditions":    clean(row.get("Conditions") or row.get("Illness Attached")),
        "Keywords":      clean(row.get("Other Keywords")),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. Generate ONE new activity via Gemini (if needed)
# ─────────────────────────────────────────────────────────────────────────────
def ai_generate_tags(profile, sample_acts):
    prompt = f"""
You are an expert child therapist.

CHILD PROFILE:
{profile}

EXAMPLE ACTIVITIES (style reference):
{sample_acts}

Create ONE new activity for this child.
Return your answer strictly as JSON (no code fences):

{{
  "Activity Name": "...",
  "Focus Area": "...",
  "Conditions": "...",
  "Keywords": "..."
}}
"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        txt   = model.generate_content(prompt).text.strip()
        txt   = re.sub(r"^```(?:json)?\s*|\s*```$", "", txt, flags=re.I).strip()
        tags  = json.loads(txt)

        for key in ["Activity Name", "Focus Area", "Conditions", "Keywords"]:
            if key not in tags or not str(tags[key]).strip():
                raise ValueError("missing field")

        return tags

    except Exception as e:
        st.warning(f"⚠️ Gemini failed, using fallback ({e})")
        return {
            "Activity Name": "Engagement Activity",
            "Focus Area": "Cognitive, Fine Motor",
            "Conditions": "ADHD, Autism",
            "Keywords": "puzzles, matching, visual, focus"
        }


# ─────────────────────────────────────────────────────────────────────────────
# 4. Main recommender – CSV first, Gemini top‑up
# ─────────────────────────────────────────────────────────────────────────────
def recommend_activities(profile, df):
    query = " ".join(str(v) for v in profile.values() if v).lower()

    mask = (
        df["Focus Area(s)"].astype(str).str.lower().str.contains(query, na=False) |
        df["Analyze Progress"].astype(str).str.lower().str.contains(query, na=False) |
        df["Conditions"].astype(str).str.lower().str.contains(query, na=False) |
        df["Illness Attached"].astype(str).str.lower().str.contains(query, na=False) |
        df["Other Keywords"].astype(str).str.lower().str.contains(query, na=False) |
        df["Parent Description"].astype(str).str.lower().str.contains(query, na=False)
    )

    # Extract and deduplicate by activity name
    seen_names = set()
    unique_csv_hits = []
    for _, row in df[mask].iterrows():
        tags = extract_tags(row)
        name = tags["Activity Name"].strip().lower()
        if name and name not in seen_names:
            unique_csv_hits.append(tags)
            seen_names.add(name)

    # If less than 5, top up with unique Gemini activities
    while len(unique_csv_hits) < 5:
        ai_tags = ai_generate_tags(profile, unique_csv_hits[:3])
        ai_name = ai_tags["Activity Name"].strip().lower()
        if ai_name and ai_name not in seen_names:
            unique_csv_hits.append(ai_tags)
            seen_names.add(ai_name)

    return unique_csv_hits[:5]



# ─────────────────────────────────────────────────────────────────────────────
# 5. Display helper
# ─────────────────────────────────────────────────────────────────────────────
def display_activity(act):
    st.markdown(
        f"<div style='font-size:1.35rem; font-weight:700; margin-bottom:0.4rem;'>"
        f"{act['Activity Name']}</div>",
        unsafe_allow_html=True
    )
    st.markdown(f"**Focus Area:** {act['Focus Area']}")
    st.markdown(f"**Conditions:** {act['Conditions']}")
    st.markdown(f"**Keywords:** {act['Keywords']}")


# ─────────────────────────────────────────────────────────────────────────────
# 6. Streamlit UI
# ─────────────────────────────────────────────────────────────────────────────-
def main():
    st.title("Child Wellness Companion")
    st.write("Fill out the form below to get personalized activity recommendations for your child.")

    df = load_activities()

    # Session state
    if 'profile' not in st.session_state: st.session_state['profile'] = None
    if 'recs'    not in st.session_state: st.session_state['recs']    = None

    # ── FORM ─────────────────────────────────────────────
    if st.session_state['profile'] is None:
        with st.form("child_profile"):
            child_name        = st.text_input("Child's Name")
            child_age         = st.text_input("Child's Age")
            child_strengths   = st.text_input("Child's Strengths (e.g., creative, social, focused)")
            child_challenges  = st.text_input("Child's Challenges (e.g., attention, sensory, social)")
            child_diagnoses   = st.text_input("Previous Diagnoses (e.g., ADHD, Autism, None)")
            skills_to_improve = st.text_input("Specific skills you want your child to improve")
            sensory_physical  = st.text_input("Sensory sensitivities or physical limitations")
            motivation        = st.text_input("What motivates or excites your child?")
            other_info        = st.text_input("Any Other Information (optional)")
            submitted         = st.form_submit_button("Submit Profile")

        if submitted:
            required = [child_name, child_age, child_strengths, child_challenges,
                        child_diagnoses, skills_to_improve, sensory_physical, motivation]
            if not all(required):
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
                    "other_info": other_info
                }
                st.success("Profile submitted!")
    df = df.drop_duplicates(subset=["Activity Name"])


    # ── PROFILE SUMMARY + RECOMMENDATIONS ───────────────
    if st.session_state['profile'] is not None:
        p = st.session_state['profile']
        st.markdown("#### Profile Summary")
        st.write(
            f"**Name:** {p['name']}\n\n"
            f"**Age:** {p['age']}\n\n"
            f"**Strengths:** {p['strengths']}\n\n"
            f"**Challenges:** {p['challenges']}\n\n"
            f"**Diagnoses:** {p['diagnoses']}\n\n"
            f"**Skills to Improve:** {p['skills_to_improve']}\n\n"
            f"**Sensory/Physical Limitations:** {p['sensory_physical']}\n\n"
            f"**Motivation:** {p['motivation']}\n\n"
            f"**Other Info:** {p['other_info']}"
        )

        if st.session_state['recs'] is None:
            st.session_state['recs'] = recommend_activities(p, df)

    # ── SHOW ACTIVITIES ─────────────────────────────────
    if st.session_state['recs'] is not None:
        st.markdown("## Recommended Activities")
        for act in st.session_state['recs']:
            with st.expander(act.get("Activity Name", "Unnamed Activity")):
                display_activity(act)

        if st.button("Start Over"):
            st.session_state['profile'] = None
            st.session_state['recs']    = None


if __name__ == "__main__":
    main()

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
    """
    Load activities from activities.csv.

    Expected optional extra columns:
      • 'Age Min'  – smallest age in years (int/float)
      • 'Age Max'  – largest age in years (int/float)
      • 'Age Group' – alternative textual age band (e.g. "5‑7")

    If no age columns exist, age filtering will be skipped gracefully.
    """
    try:
        df = pd.read_csv("activities.csv", encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv("activities.csv", encoding="latin1")

    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    df = df[df["Activity Name"].astype(str).str.strip() != ""]
    df = df.drop_duplicates(subset=["Activity Name"]).reset_index(drop=True)

    # Ensure numeric age columns where possible
    for col in ["Age Min", "Age Max"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

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
    """
    Return exactly 5 unique activities.
    • Scores CSV rows by age, conditions, focus areas, keywords, strengths, and challenges.
    • If fewer than 5 CSV matches, Gemini fills the gap.
    """
    seen, chosen = set(), []

    def age_matches(row, child_age):
        if "Age Min" in row and "Age Max" in row and not pd.isna(row["Age Min"]):
            return row["Age Min"] <= child_age <= row["Age Max"]
        if "Age Group" in row and isinstance(row["Age Group"], str):
            m = re.match(r"(\d+)\s*[-–]\s*(\d+)", row["Age Group"])
            if m:
                lo, hi = map(int, m.groups())
                return lo <= child_age <= hi
        return True

    def overlap(a, b):
        return bool(set(a).intersection(b))

    # Extract structured profile info
    child_age = None
    try:
        child_age = float(profile.get("age", "").split()[0])
    except (ValueError, AttributeError):
        pass

    strengths = re.findall(r"\w+", profile.get("strengths", "").lower())
    challenges = re.findall(r"\w+", profile.get("challenges", "").lower())
    tokens = re.findall(r"\w+", " ".join(str(v) for v in profile.values()).lower())

    for _, row in df.iterrows():
        name = str(row["Activity Name"]).strip()
        if not name:
            continue

        score = 0
        if child_age is not None and age_matches(row, child_age):
            score += 2

        # Match on diagnoses
        cond_text = " ".join([str(row.get("Conditions", "")),
                              str(row.get("Illness Attached", ""))]).lower()
        if overlap(tokens, cond_text.split()):
            score += 2

        # Match on focus areas / keywords
        focus_kw = " ".join([str(row.get("Focus Area(s)", "")),
                             str(row.get("Other Keywords", ""))]).lower()
        if overlap(tokens, focus_kw.split()):
            score += 1

        # Bonus for strengths and challenges match
        if overlap(strengths, focus_kw.split()):
            score += 1
        if overlap(challenges, focus_kw.split()):
            score += 1

        if score:
            chosen.append((score, extract_tags(row)))

    # Sort by score and remove duplicates
    chosen.sort(key=lambda x: -x[0])
    unique_csv = []
    seen_names = set()
    for score, tags in chosen:
        n = tags["Activity Name"].strip().lower()
        if n and n not in seen_names:
            unique_csv.append(tags)
            seen_names.add(n)
        if len(unique_csv) == 5:
            break

    # Top up with Gemini if needed
    remaining = 5 - len(unique_csv)
    samples = unique_csv[:3]
    attempts = 0
    while remaining > 0 and attempts < 10:
        ai_tags = ai_generate_tags(profile, samples)
        ai_name = ai_tags["Activity Name"].strip().lower()
        if ai_name and ai_name not in seen_names:
            unique_csv.append(ai_tags)
            seen_names.add(ai_name)
            remaining -= 1
        attempts += 1

    return unique_csv

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

import streamlit as st
import openai
from openai import OpenAI

county_hotlines = {
        "": "",
        "Los Angeles (CA)": "Didi Hirsch Suicide Prevention Center: 1-877-727-4747",
        "Alameda (CA)": "Alameda Crisis Support Services: 1-800-309-2131",
        "San Francisco (CA)": "San Francisco Suicide Prevention: 1-415-781-0500",
        "Santa Clara (CA)": "Santa Clara County Suicide & Crisis Hotline: 1-855-278-4204",
        "Cook (IL)": "NAMI Chicago Helpline: 1-833-626-4244",
        "King (WA)": "Crisis Connections: 1-866-427-4747",
        "Fulton (GA)": "Georgia Crisis & Access Line: 1-800-715-4225",
        "Baltimore (MA)": "Here2Help Line: 410-433-5175"

        # add more directories here ...
    }


# ---- PAGE SETUP ----
st.set_page_config(page_title="TEMPOS Evaluator", layout="wide")
client = OpenAI(api_key=st.secrets["openai_api_key"])

# ---- CSS STYLING ----
st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .sidebar .sidebar-content {
            background-color: #f0f4f8;
        }
    </style>
""", unsafe_allow_html=True)

# ---- SIDEBAR: TEMPOS INFO ----

st.logo("sm_howl_looks_logo_02.png", size="large")
with st.sidebar:
    st.title("TEMPOS Framework")
    st.write("Assessment criteria:")

    st.info('How does the report frame the suicide?')
    st.info('Does the report include factual and non-speculative information about suicide?')
    st.info('Does the report use appropriate/non-stigmatizing language?')
    st.info('How does the report describe the suicide method and scene?')
    st.info('How does the report describe the suicide note?')
    st.info('What visual content does the report include?')
    st.info('How does the report describe risk factors and reasons for suicide?')
    st.info('Does the report use sensational language?')
    st.info('Does the report glamorize suicide?')
    st.info('Does the report include suicide prevention and mental health resources? ')

    st.title("TEMPOS Scoring")

    st.success("2: Helpful messaging, full adherence")
    st.warning("1: Mixed messaging, partial adherence")
    st.error("0: Harmful messaging, non-adherence to guidelines")
    
    st.markdown("---")
    st.subheader("☎️ Helpful Resources")
    st.write("- Suicide and Crisis Lifeline: 988")
    st.write("- Stanford Counseling and Psychological Services (CAPS): 650.723.3785")
 
    st.markdown("---")
    st.write("For more information on TEMPOS, visit the [Stanford Medicine website](https://med.stanford.edu/psychiatry/special-initiatives/mediamh/resources/tempos.html).")

# ---- MAIN PANEL ----
st.title("📄 TEMPOS Writing Evaluator")
st.write("Paste or write your response below. The system will provide a breakdown using the **TEMPOS framework**:")

# ---- USER INPUT ----
user_input = st.text_area("✍️ Your Text", height=250, placeholder="Write your paragraph here...")

# ---- EVALUATE BUTTON ----
if st.button("Evaluate"):
    if user_input.strip() == "":
        st.warning("Please enter some text to evaluate.")
    else:
        prompt = f"""

        You are a sympathetic and professional expert.
        Evaluate this user-input text using the TEMPOS framework.

        The Tempos criteria:
        1. How does the report frame the suicide?
        2. Does the report include factual and non-speculative information about suicide?
        3. Does the report use appropriate/non-stigmatizing language?
        4. How does the report describe the suicide method and scene?
        5. How does the report describe the suicide note?
        6. What visual content does the report include?
        7. How does the report describe risk factors and reasons for suicide?
        8. Does the report use sensational language?
        9. Does the report glamorize suicide?
        10. Does the report include suicide prevention and mental health resources?

        The TEMPOS framework ranks are as follows:
        - 0 for harmful messaging and non-adherence to the guideline
        - 1 for mixed messaging and partial adherence to the guideline
        - 2 for helpful messaging and full adherence to the guideline.

        Your output should be as follows:

        - Provide a numerical score followed by a one sentence evaluation for each of the 10 TEMPOS criteria
        - Conclude with only the average score (no calculation shown).

        - On the next line, say "What went well: " then highlight specific examples or phrases from the text to justify what went well, if it appplies.
        - Lastly, say "Suggestions for improvement: " then suggest ways to improve on relevant criteria.

        Paragraph:
        \"\"\"{user_input}\"\"\"
        """

        with st.spinner("Analyzing..."):
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            st.session_state["analysis"] = response.choices[0].message.content

# ---- DISPLAY RESULTS AND USER FEEDBACK ----
        if "analysis" in st.session_state:
            st.markdown("### Feedback")
            st.markdown(st.session_state["analysis"])

st.markdown("---")

if "show_popup" not in st.session_state:
    st.session_state.show_popup = False

def toggle_popup():
    st.session_state.show_popup = not st.session_state.show_popup

# Button to trigger "popup"
st.button("💬 Click here for mental health help", on_click=toggle_popup)

# Conditional rendering
if st.session_state.show_popup:
    st.markdown("### 🧠 Mental Health Support")
    st.write("Please note that your location will not be collected or shared.")
    county = st.selectbox("Select your county", list(county_hotlines.keys()))

    if county:
        hotline = county_hotlines.get(county.strip(), "National Suicide Prevention Lifeline: 988")
        st.success(f"📞 {hotline}")
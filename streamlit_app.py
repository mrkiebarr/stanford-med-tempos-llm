import streamlit as st
import openai
from openai import OpenAI


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

    st.write("TEMPOS, or Tool for Evaluating Media Portrayals of Suicide, serves as a guideline for journalists to monitor the adherence of specific articles, scripts, and social media posts to the [Recommendations for Reporting on Suicide](https://reportingonsuicide.org/) developed by leading experts in the fields of mental health, suicide prevention, and journalism.") 
    st.write("This dashboard leverages the power of TEMPOS-trained AI model to analyze user text input and provide real-time scoring and feedback on suicide-related reports.")
    st.write("Assessment criteria:")

    st.info('1. How does the report frame the suicide?')
    st.info('2. Does the report include factual and non-speculative information about suicide?')
    st.info('3. Does the report use appropriate/non-stigmatizing language?')
    st.info('4. How does the report describe the suicide method and scene?')
    st.info('5. How does the report describe the suicide note?')
    st.info('6. What visual content does the report include? [Disclaimer: the AI model is not trained to analyze visual content; therefore, this criterion automatically receives a score of 0 which is not factored in the overall average score.]')
    st.info('7. How does the report describe risk factors and reasons for suicide?')
    st.info('8. Does the report use sensational language?')
    st.info('9. Does the report glamorize suicide?')
    st.info('10. Does the report include suicide prevention and mental health resources? ')

    st.write("For a detailed breakdown of the TEMPOS Framework, visit [here](https://tempos.su.domains/).")
    st.markdown("---")
    st.title("TEMPOS Scoring")

    st.success("2: Helpful messaging, full adherence")
    st.warning("1: Mixed messaging, partial adherence")
    st.error("0: Harmful messaging, non-adherence to guidelines")
    
    st.markdown("---")
    st.subheader("☎️ Helpful Resources")
    st.write("- Suicide and Crisis Lifeline: 988")
    st.write("- Stanford Counseling and Psychological Services (CAPS): 650.723.3785")

# ---- MAIN PANEL ----
st.title("📄 TEMPOS Insight")
st.write("Paste or write your text below. We will carefully analyze and provide feedback based on the **TEMPOS framework**:")

# ---- USER INPUT ----
user_input = st.text_area("✍️ Your Text", height=250, placeholder="Write your paragraph here...")

# ---- EVALUATE BUTTON ----
if st.button("Evaluate"):
    if user_input.strip() == "":
        st.warning("Please enter some text to evaluate.")
    else:
        prompt = f"""

        You are a sympathetic and professional expert on mental health journalism.
        Evaluate this user-input text using the TEMPOS Framework derived from https://tempos.su.domains/, identifying the rationale behind every single score for each criterion for accurate rating.

        The Tempos criteria:
        1. How does the report frame the suicide?
            - 2: Frames suicide as a preventable mental health outcome; reports that coping skills, support and treatment work for most people (recovery is possible).
            - 1: Doesn't portray suicide as an escape or inevitable response to hardship, but fails to include that suicide is preventable and that resources are available to those who are struggling; may include a mix of these two portrayals.
            - 0: Explicitly presents or strongly implies that suicide is a common, acceptable, or inevitable response to hardship; frames suicide as a way out or a way of taking control of one's circumstances.
        2. Does the report include factual and non-speculative information about suicide?
            - 2: Includes information that is clearly factual in nature, not speculative. May include quotes or objective information from informed sources (e.g. people or organizations with mental health or suicide prevention expertise, and/or people with lived experience).
            - 1: Does not include speculation/non-factual information, but also fails to provide factual information about suicide/mental health; may include a mix of these two portrayals.
            - 0: Includes information that is clearly speculative (e.g., non-factual) about the causes of / reasons for suicide. Sources of information (e.g. friends / family / professionals) are not factually informed or are inaccurate / inappropriate.
        3. Does the report use appropriate/non-stigmatizing language?
            - 2: Uses appropriate/non-stigmatizing language that is more neutral and treats suicide similarly to other causes of death (e.g. died by suicide)
            - 1: Uses a mix of inappropriate and appropriate language.
            - 0: Uses inappropriate / stigmatizing language that implies criminality (e.g. committed), judgment, or positive connotations (e.g. successful attempt).

        4. How does the report describe the suicide method and scene?
            - 2: Reports the death as a suicide but keeps information general and does not mention method.
            - 1: Briefly mentions suicide method (e.g. asphyxiation, overdose) but does not include explicit details about the method used or the scene of the death.
            - 0: Describes or depicts, in a detailed manner, the method and/or location of the suicide; ‘sets the scene’ by including information about what was found at the scene of the death, how the person was found, or the type of object used.
        5. How does the report describe the suicide note? 
            - 2: Does not mention a note or its contents; states that no note was found.
            - 1: Reports that a note was found but does not include any content from the note.
            - 0: Shares specific content drawn directly from a suicide note.
        6. What visual content does the report include? [This criterion should automatically receive a zero because visual content is not included in the text input. Do not include this in the denominator for overall calculation]
            - 2: Uses visual content of the person who died from school/work/ family or photo unrelated to suicide.
            - 1: Includes visual content of grieving/sad individuals, memorials, or funerals.
            - 0: Includes any visual content (e.g. photos / videos) of the location or method of death.
        7. How does the report describe risk factors and reasons for suicide?
            - 2: Acknowledges (in the body of the article or in a sidebar) the complexity of suicide and describes risk factors (e.g. mental illness, economic hardship, family issues) that give suicide context.
            - 1: Does not speculate about reasons for death but does not include information about risk factors.
            - 0: Oversimplifies or speculates on the reason for suicide; simplifies the issue of suicide by directly or indirectly attributing the death to a single reason or saying that it happened ‘without warning’.
        8. Does the report use sensational language?
            - 2: Reports on the death using non-sensational facts and language that focuses on the person’s life rather than death (similar to reporting on non-suicide deaths); when referring to suicide rates, references best available data and uses words like ‘increase’ or ‘rise.’
            - 1: Includes some sensitive language that focuses on the person’s life rather than death, but also includes a few instances of sensational language/details about the death.
            - 0: Includes shocking or provocative language / details about suicide designed to elicit an emotional response; uses sensational language (e.g. ‘epidemic’, ‘skyrocketing’, ‘spike’) when describing suicide rates.
        9. Does the report glamorize suicide?
            - 2: Does not portray suicide in a positive or glamorous manner; focuses on the life they lived rather than their death, acknowledges positive aspects of their life, as well as their struggles.
            - 1: Includes some content that glamorizes/portrays suicide in a positive light; portrays their life in an idealized or glamorized way without acknowledging struggles.
            - 0: Majority of article content glamorizes suicide; includes several tributes or portrays suicide in a positive manner (e.g. ties suicide to heroism, romance, honor).
        10. Does the report include suicide prevention and mental health resources?
            - 2: Includes a suicide hotline/crisis number as well as additional resources for mental health care and suicide prevention, for example local mental health resources, suicide prevention organizations, websites.
            - 1: Includes a suicide hotline/crisis number as well as additional resources for mental health care and suicide prevention, for example local mental health resources, suicide prevention organizations, websites.
            - 0: Does not include any resources

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

        with st.spinner("Please wait while I analyze your report..."):
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

st.markdown("### 🧠 Mental Health Support")
st.write("Please reach out to your local mental health service provider or refer to the Department of Health Care Services [Mental Health Services Division](https://www.dhcs.ca.gov/services/Pages/MentalHealthPrograms-Svcs.aspx) for a list of helpful resources.")
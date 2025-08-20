import streamlit as st
from openai import OpenAI
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

# =========================
# PAGE & GLOBAL CLIENTS
# =========================
st.set_page_config(page_title="TEMPOS Evaluator", layout="wide")

# OpenAI client for GPT calls
client = OpenAI(api_key=st.secrets["openai_api_key"])

@st.cache_resource
def init_retrieval_clients():
    """
    Initialize Pinecone (v3 SDK) and the SAME embedder you used in Colab:
    sentence-transformers/all-mpnet-base-v2 (768-dim).
    """
    # Pinecone serverless: connect via host URL from console
    pc = Pinecone(api_key=st.secrets["pinecone_api_key"])
    index = pc.Index(host=st.secrets["pinecone_index_host"])

    # Use the SAME model as ingestion (Colab)
    embedder = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

    # Namespace used during ingestion
    namespace = st.secrets.get("pinecone_namespace", "tempos")

    return index, embedder, namespace

index, embedder, NAMESPACE = init_retrieval_clients()

def retrieve_context(query: str, k: int = 4, max_chars: int = 2500):
    """
    Embed the user query (768-dim), hit Pinecone, and return a compact context block
    plus the raw matches for display.
    """
    # 1) Embed query
    qvec = embedder.encode([query])[0].tolist()

    # 2) Query Pinecone (top_k with metadata)
    res = index.query(
        namespace=NAMESPACE,
        vector=qvec,
        top_k=k,
        include_metadata=True
    )

    # 3) Build a trimmed context to avoid token bloat
    snippets, matches = [], res.get("matches", [])
    total = 0
    for m in matches:
        piece = (m.get("metadata", {}).get("preview") or "").strip()
        if not piece:
            continue
        if total + len(piece) > max_chars:
            piece = piece[: max(0, max_chars - total)]
        snippets.append(piece)
        total += len(piece)
        if total >= max_chars:
            break

    return "\n\n---\n\n".join(snippets), matches


# =========================
# HEADER / BRANDING
# =========================
col1, col2 = st.columns([1, 1])
with col1:
    st.image("sm_howl_looks_logo_02.png", use_container_width=True)
with col2:
    st.image("county of santa clara.png", use_container_width=True)

# =========================
# SIDEBAR (INFO)
# =========================
with st.sidebar:
    st.title("TEMPOS Framework")

    st.write(
        "TEMPOS, or Tool for Evaluating Media Portrayals of Suicide, serves as a guideline for journalists "
        "to monitor adherence to the "
        "[Recommendations for Reporting on Suicide](https://reportingonsuicide.org/). "
        "This dashboard leverages a TEMPOS-aligned AI model to analyze user text and provide real-time scoring "
        "and feedback."
    )
    st.write("Assessment criteria:")
    st.info('1. How does the report frame the suicide?')
    st.info('2. Does the report include factual and non-speculative information about suicide?')
    st.info('3. Does the report use appropriate/non-stigmatizing language?')
    st.info('4. How does the report describe the suicide method and scene?')
    st.info('5. How does the report describe the suicide note?')
    st.info('6. What visual content does the report include? (N/A in this text-only tool)')
    st.info('7. How does the report describe risk factors and reasons for suicide?')
    st.info('8. Does the report use sensational language?')
    st.info('9. Does the report glamorize suicide?')
    st.info('10. Does the report include suicide prevention and mental health resources?')

    st.markdown("---")
    st.title("TEMPOS Scoring")
    st.success("2: Helpful messaging, full adherence")
    st.warning("1: Mixed messaging, partial adherence")
    st.error("0: Harmful messaging, non-adherence to guidelines")

    st.markdown("---")
    st.title("Why Retrieval Level Matters")
    st.info("Level 1 (k=1): The system only looks at the single most relevant part of one article. Very focused, but it might miss important context from other parts of that article or from other articles.")
    st.info("Level 3–5 (k=3–5): The system looks at a few different parts, which might all come from the same article or from several different articles. This usually gives the best balance—enough context without too much extra.")
    st.info("Level 10+ (k=10+): The system pulls in many parts from across multiple articles. This can help with complex topics, but it also risks bringing in sections that aren’t really relevant.")

    st.markdown("---")
    st.subheader("☎️ Suicide and Crisis Lifeline")
    st.write("- Call/ Text: **988**")
    st.write("- Chat or more: [988lifeline.org](https://988lifeline.org/)")
    st.subheader("☎️ Additional Resources")
    st.write("- [American Foundation for Suicide Prevention](https://afsp.org/)")
    st.write("- [National Institute of Mental Health](https://nimh.nih.gov/)")
    st.write("- [Suicide Prevention Resource Center](https://sprc.org/)")
    st.write("- [American Association of Suicidology](https://suicidology.org/)")

# =========================
# MAIN
# =========================
st.title("📄 TEMPOS (Tool for Evaluating Media Portrayals of Suicide)")
st.caption("Select a retrieval level below. Then paste or write your text in the text area. The evaluation will be grounded in existing reports carefully assessed by human experts. (For more information on why retrieval level matters, please refer to the sidebar.")

# Controls
k = st.slider("Retrieval Level", 1, 10, 4)
user_input = st.text_area("✍️ Your Text", height=250, placeholder="Write your paragraph here...")

if st.button("Evaluate"):
    if not user_input.strip():
        st.warning("Please enter some text to evaluate.")
    else:
        # 1) Retrieve supporting context from Pinecone
        with st.spinner("Retrieving relevant context from your CSV index..."):
            context, matches = retrieve_context(user_input, k=k, max_chars=2500)

        # 2) Build augmented prompt: your rubric + retrieved context + user text
        prompt = f"""
You are a sympathetic and professional expert on mental health journalism.
Evaluate the user-input text using the TEMPOS criteria. Use the CSV context to ground your evaluation.
If the CSV context does not contain information for a criterion, say so explicitly. Do not fabricate.

[CSV CONTEXT]
{context}

[USER PARAGRAPH]
\"\"\"{user_input}\"\"\"

[SCORING RUBRIC]
1. How does the report frame the suicide?
    - 2: Frames suicide as a preventable mental health outcome; reports that coping skills, support and treatment work for most people (recovery is possible).
    - 1: Doesn't portray suicide as an escape or inevitable response to hardship, but fails to include that suicide is preventable and that resources are available to those who are struggling; may include a mix of these two portrayals.
    - 0: Explicitly presents or strongly implies that suicide is a common, acceptable, or inevitable response to hardship; frames suicide as a way out or a way of taking control of one's circumstances.
2. Does the report include factual and non-speculative information about suicide?
    - 2: Includes information that is clearly factual in nature, not speculative. May include quotes or objective information from informed sources (e.g. people or organizations with mental health or suicide prevention expertise, and/or people with lived experience).
    - 1: Does not include speculation/non-factual information, but also fails to provide factual information about suicide/mental health; may include a mix of these two portrayals.
    - 0: Includes information that is clearly speculative (e.g., non-factual) about the causes of / reasons for suicide. Sources of information are not informed or are inappropriate.
3. Does the report use appropriate/non-stigmatizing language?
    - 2: Uses appropriate/non-stigmatizing language that is neutral and treats suicide similarly to other causes of death (e.g., “died by suicide”).
    - 1: Uses a mix of inappropriate and appropriate language.
    - 0: Uses inappropriate / stigmatizing language that implies criminality (e.g., “committed”), judgment, or positive connotations (e.g., “successful attempt”).
4. How does the report describe the suicide method and scene?
    - 2: Reports the death as a suicide but keeps information general and does not mention method.
    - 1: Briefly mentions suicide method (e.g., asphyxiation, overdose) but does not include explicit details about the method used or the scene of the death.
    - 0: Describes or depicts, in a detailed manner, the method and/or location of the suicide; ‘sets the scene’ with details about how the person was found or the object used.
    - N/A: Article is not about a specific person's suicide.
5. How does the report describe the suicide note?
    - 2: Does not mention a note or its contents; or states that no note was found.
    - 1: Reports that a note was found but does not include any content from the note.
    - 0: Shares specific content drawn directly from a suicide note.
    - N/A: Article is not about a specific person's suicide.
6. What visual content does the report include?
    - N/A; our model does not assess visual content. Do not include this in the denominator.
7. How does the report describe risk factors and reasons for suicide?
    - 2: Acknowledges complexity and describes risk factors (e.g., mental illness, economic hardship, family issues).
    - 1: Does not speculate about reasons for death but does not include information about risk factors.
    - 0: Oversimplifies or speculates on reasons; attributes the death to a single cause or says it happened ‘without warning’.
8. Does the report use sensational language?
    - 2: Uses non-sensational language; focuses on the person’s life rather than death; references best available data when mentioning rates.
    - 1: Mix of neutral and sensational elements.
    - 0: Uses shocking or provocative language designed to elicit emotion (e.g., ‘epidemic’, ‘skyrocketing’, ‘spike’).
9. Does the report glamorize suicide?
    - 2: Does not portray suicide positively; focuses on the life lived while acknowledging struggles.
    - 1: Some idealized or glamorized elements without acknowledging struggles.
    - 0: Strong glamorization or repeated tributes tying suicide to heroism, romance, or honor.
10. Does the report include suicide prevention and mental health resources?
    - 2: Includes a crisis number (e.g., 988) AND additional resources (local services, organizations, websites).
    - 1: Includes some resources but missing key details.
    - 0: No resources included.

[OUTPUT FORMAT]
- Provide a numerical score followed by a one‑sentence evaluation for each criterion (1–10).
- Then, on a new line: "What went well:" with specific examples/phrases from the text that justify positives (if applicable).
- Then, "Suggestions for improvement:" with concrete, actionable guidance tied to the criteria.
"""

        # 3) Call GPT with the augmented prompt
        with st.spinner("Analyzing your report..."):
            response = client.chat.completions.create(
                model="gpt-5",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            st.session_state["analysis"] = response.choices[0].message.content

        # 4) Show results and sources
        if "analysis" in st.session_state:
            st.markdown("### Feedback")
            st.markdown(st.session_state["analysis"])

            with st.expander("See retrieved CSV context"):
                if not matches:
                    st.write("No context retrieved.")
                else:
                    for i, m in enumerate(matches, 1):
                        meta = m.get("metadata", {})
                        st.markdown(
                            f"**Snippet {i}**  •  score: {m.get('score', 0):.4f}  •  row_index: {meta.get('row_index','?')}  •  chunk: {meta.get('chunk_id','?')}"
                        )
                        st.code(meta.get("preview", "")[:800])

# Footer
st.markdown("---")
st.markdown(
    """
### 🧠 Mental Health Support
Please reach out to your local mental health service provider or refer to the
[Substance Abuse and Mental Health Services Adminsitration (SAMHSA)](https://www.samhsa.gov/find-help)
for a list of helpful resources.

---
<small>Developers: Mark David Barranda & Carol Li, Data Science Society @ UC Berkeley</small>
""",
    unsafe_allow_html=True,
)
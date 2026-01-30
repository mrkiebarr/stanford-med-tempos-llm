import os
from pathlib import Path
import streamlit as st
from openai import OpenAI
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

# =========================
# PAGE & OPENAI CLIENT
# =========================
st.set_page_config(page_title="TEMPOS Evaluator", layout="wide")

if "openai_api_key" not in st.secrets:
    st.error('Missing "openai_api_key" in secrets. Add it to .streamlit/secrets.toml or deployment settings.')
    st.stop()

client = OpenAI(api_key=st.secrets["openai_api_key"])

# =========================
# SAFE / LAZY INIT
# =========================
@st.cache_resource(show_spinner=False)
def init_retrieval_clients():
    """Create Pinecone index client + local embedder (lazy, cached)."""
    # Secrets checks
    missing = [k for k in ("pinecone_api_key", "pinecone_index_host") if k not in st.secrets]
    if missing:
        raise RuntimeError(f"Missing secrets: {missing}. Add them to secrets.")

    pc = Pinecone(api_key=st.secrets["pinecone_api_key"])
    index = pc.Index(host=st.secrets["pinecone_index_host"])

    # Use the SAME model as ingestion
    embedder = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

    namespace = st.secrets.get("pinecone_namespace", "tempos")
    return index, embedder, namespace

def get_clients():
    """Initialize once, on demand, with user-visible status and errors."""
    if "pc_index" not in st.session_state:
        try:
            index, embedder, namespace = init_retrieval_clients()
            st.session_state["pc_index"] = index
            st.session_state["embedder"] = embedder
            st.session_state["namespace"] = namespace
            
        except Exception as e:
            st.error(f"Setup error: {e}")
            st.stop()
    return st.session_state["pc_index"], st.session_state["embedder"], st.session_state["namespace"]

# =========================
# EXEMPLAR HELPERS
# =========================
CRITERION_LABEL = {
    "1": "Framing of Suicide",
    "2": "Factual & Non‑Speculative Information",
    "3": "Appropriate / Non‑stigmatizing Language",
    "4": "Method / Scene",
    "5": "Suicide Note",
    "6": "Visual Content",
    "7": "Reasons & Risk Factors",
    "8": "Sensationalism",
    "9": "Glamorizing Suicide",
    "10": "Prevention & MH Resources",
}

def get_scores_from_meta(md: dict) -> dict:
    """Read flattened scores score_1..score_10 from metadata."""
    out = {}
    for i in range(1, 11):
        key = f"score_{i}"
        if key in md:
            out[str(i)] = md[key]  # 0/1/2 or "N/A"
    return out

def build_exemplar_block(matches, max_examples: int = 3, snippet_chars: int = 600) -> str:
    """Turn matches into few-shot exemplars using flattened scores."""
    exemplars = []
    for m in matches[:max_examples]:
        md = (m.get("metadata") or {})
        scores = get_scores_from_meta(md)
        preview = (md.get("preview") or "").strip()[:snippet_chars]
        title = (md.get("title") or "").strip()
        if not scores or not preview:
            continue
        exemplars.append(
            f"[EXEMPLAR]\n"
            f"Title: {title or 'Untitled'}\n"
            f"Human TEMPOS scores: {scores}\n"
            f"Excerpt:\n{preview}"
        )
    return "\n\n".join(exemplars)

# =========================
# RETRIEVAL
# =========================
def retrieve_context(index, embedder, namespace, query: str, k: int = 5, max_chars: int = 2500):
    """Embed query, hit Pinecone, and return compact context + raw matches."""
    qvec = embedder.encode([query])[0].tolist()
    res = index.query(namespace=namespace, vector=qvec, top_k=k, include_metadata=True)

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

# with st.sidebar:
#     st.title("TEMPOS Framework")
#     st.write(
#         "TEMPOS, or Tool for Evaluating Media Portrayals of Suicide, helps assess adherence to "
#         "[Recommendations for Reporting on Suicide](https://reportingonsuicide.org/). "
#         "This tool analyzes user text and provides real-time scoring and feedback grounded on human expert-based assessement."
#     )

#     st.info(
#         "[Assessment criteria](https://med.stanford.edu/content/dam/sm/psychiatry/documents/initiatives/mediamh/TEMPOS%20Apr23.pdf):\n"
#         "1. How does the report frame the suicide?\n"
#         "2. Does the report include factual and non-speculative information about suicide?\n"
#         "3. Does the report use appropriate/non-stigmatizing language?\n"
#         "4. How does the report describe the suicide method and scene?\n"
#         "5. How does the report describe the suicide note?\n"
#         "6. What visual content does the report include? (N/A in this text-only tool)\n"
#         "7. How does the report describe risk factors and reasons for suicide?\n"
#         "8. Does the report use sensational language?\n"
#         "9. Does the report glamorize suicide?\n"
#         "10. Does the report include suicide prevention and mental health resources?"
#     )

#     st.markdown("---")
#     st.title("TEMPOS Scoring")
#     st.success("2: Helpful messaging, full adherence")
#     st.warning("1: Mixed messaging, partial adherence")
#     st.error("0: Harmful messaging, non-adherence to guidelines")

    
#     #st.markdown("---")
#     #st.title("Why Retrieval Level Matters")
#     #st.info("k=1: very focused; may miss context.\n")
#     #st.info("k=3–5: best balance (recommended).")
#     #st.info("k=6+: broader; may add noise and tokens.")

#     st.markdown("---")
#     st.subheader("☎️ Suicide and Crisis Lifeline")
#     st.write("- Call/ Text: **988**")
#     st.write("- Chat or more: [988lifeline.org](https://988lifeline.org/)")
#     st.subheader("☎️ Additional Resources")
#     st.write("- [AFSP](https://afsp.org/)")
#     st.write("- [NIMH](https://nimh.nih.gov/)")
#     st.write("- [SPRC](https://sprc.org/)")
#     st.write("- [AAS](https://suicidology.org/)")
# # SIDEBAR (INFO)
# =========================


# =========================
# MAIN
# =========================
st.title("📄 TEMPOS (Tool for Evaluating Media Portrayals of Suicide)")

# k = st.slider("Retrieval Level (top‑k)", 1, 8, 4)

user_input = st.text_area("✍️ Paste or type your text", height=250, placeholder="Write your paragraph here...")

if st.button("Evaluate"):
    if not user_input.strip():
        st.warning("Please enter some text to evaluate.")
        st.stop()

    # Init retrieval engines lazily (so the page is not blank on first load)
    index, embedder, NAMESPACE = get_clients()

    # Retrieve supporting context from Pinecone
    with st.spinner("Retrieving relevant context from your CSV index..."):
        try:
            context, matches = retrieve_context(index, embedder, NAMESPACE, user_input, k=5, max_chars=2500)
            exemplar_block = build_exemplar_block(matches, max_examples=3)
        except Exception as e:
            st.error(f"Pinecone retrieval error: {e}")
            st.stop()

    # Build prompt
    prompt = f"""
You are a sympathetic and professional expert on mental health journalism.
Score the user-input text using the TEMPOS criteria. When exemplars are provided,
adhere to their decision boundaries (human-coded labels) and prefer the stricter
(lower) score when uncertain. Cite phrases from the USER text when justifying.

[EXEMPLARS]
{exemplar_block or "None available"}

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
    - 2: Includes information that is clearly factual in nature, not speculative. May include quotes or objective information from informed sources.
    - 1: No speculation, but lacks factual info about suicide/mental health.
    - 0: Includes speculation or non-factual causes/reasons for suicide; sources are not informed/appropriate.
3. Does the report use appropriate/non-stigmatizing language?
    - 2: Neutral, appropriate language (e.g., “died by suicide”).
    - 1: Mix of appropriate and inappropriate language.
    - 0: Stigmatizing language (e.g., “committed”), judgment, or positive connotations.
4. How does the report describe the suicide method and scene?
    - 2: General, does not mention method.
    - 1: Briefly mentions method without explicit details or scene.
    - 0: Detailed description of method and/or scene.
    - N/A: Not about a specific person's suicide.
5. How does the report describe the suicide note?
    - 2: No note or no contents shared.
    - 1: Note mentioned, contents not shared.
    - 0: Specific note contents shared.
    - N/A: Not about a specific person's suicide.
6. What visual content does the report include?
    - N/A; visual content not assessed. (Include but say 'N/A; visual content not assessed')
7. How does the report describe risk factors and reasons for suicide?
    - 2: Acknowledges complexity; describes risk factors.
    - 1: Avoids speculation but lacks risk factors.
    - 0: Oversimplifies/speculates; attributes to a single cause.
8. Does the report use sensational language?
    - 2: Non-sensational; focuses on life; uses careful data language.
    - 1: Mixed neutral/sensational elements.
    - 0: Shocking/provocative language (e.g., ‘epidemic’, ‘spike’).
9. Does the report glamorize suicide?
    - 2: Does not portray suicide positively; acknowledges struggles.
    - 1: Some idealization without acknowledging struggles.
    - 0: Strong glamorization or repeated tributes.
10. Does the report include suicide prevention and mental health resources?
    - 2: Includes 988 and additional resources (local services, organizations, websites).
    - 1: Some resources but missing key details.
    - 0: No resources included.

[OUTPUT FORMAT]
- Provide a numerical score + one sentence for each criterion (1–10).
- "What went well:" with quotes from the USER text.
- "Suggestions for improvement:" with actionable guidance.
- If evidence is missing for a criterion, output "N/A" and explain briefly.
"""

    # OpenAI call (with robust error handling)
    try:
        with st.spinner("Analyzing your report..."):
            resp = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1200,  # cap output
            )
        st.session_state["analysis"] = resp.choices[0].message.content
    except Exception as e:
        st.error(f"OpenAI error: {e}")
        st.stop()


    # Results & sources
    if "analysis" in st.session_state:
        st.markdown("### Feedback")
        st.markdown(st.session_state["analysis"])
#
 #       with st.expander("See retrieved CSV context"):
  #          if not matches:
   #             st.write("No context retrieved.")
    #        else:
     #           for i, m in enumerate(matches, 1):
    #                meta = m.get("metadata", {}) or {}
     #               st.markdown(
     #                   f"**Snippet {i}** • score: {m.get('score', 0):.4f} • "
     #                   f"row_index: {meta.get('row_index','?')} • chunk: {meta.get('chunk_id','?')}"
     #               )
     #               if meta.get("title"):
     #                   st.write(f"**Title:** {meta['title']}")
     #               if meta.get("link"):
     #                   st.markdown(f"[Open Source Link]({meta['link']})")
     #               scores = get_scores_from_meta(meta)
     #               if scores:
     #                   st.write("**Human TEMPOS scores:**", scores)
     #               st.code((meta.get("preview") or "")[:800])

# Footer
st.markdown("---")
st.markdown(
    """
### 🧠 Mental Health Support
Please reach out to your local mental health service provider or refer to the
[Substance Abuse and Mental Health Services Administration (SAMHSA)](https://www.samhsa.gov/find-help)
for a list of helpful resources.

---
<small>Developers: Mark David Barranda & Carol Li, Data Science Society @ UC Berkeley</small>
""",
    unsafe_allow_html=True,
)
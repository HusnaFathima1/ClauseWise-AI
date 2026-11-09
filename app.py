
import io
import json
import streamlit as st
import fitz
from docx import Document

from clause_analyzer import analyze_policy


# -------------------- PAGE SETTINGS --------------------

st.set_page_config(
    page_title="ClauseWise AI",
    page_icon="⚖️",
    layout="wide",
)


# -------------------- DESIGN --------------------

st.markdown("""
<style>
.stApp {
    background: #f5f7fb;
}
.block-container {
    max-width: 1200px;
    padding-top: 2rem;
}
.hero {
    background: linear-gradient(120deg, #101d3a, #234c80);
    color: white;
    padding: 30px;
    border-radius: 18px;
    margin-bottom: 24px;
}
.hero h1 {
    color: white;
    font-size: 38px;
}
.hero p {
    color: #e1e9f7;
    font-size: 17px;
}
div[data-testid="stMetric"] {
    background: white;
    padding: 16px;
    border-radius: 12px;
    border: 1px solid #e5eaf2;
}
</style>
""", unsafe_allow_html=True)


# -------------------- SESSION STATE --------------------

if "policy_text" not in st.session_state:
    st.session_state.policy_text = ""

if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = []

if "loaded_filename" not in st.session_state:
    st.session_state.loaded_filename = None


# -------------------- SIDEBAR --------------------

st.sidebar.title("⚖️ ClauseWise AI")
st.sidebar.caption("Understand every clause before you agree.")
st.sidebar.divider()

st.sidebar.subheader("Features")
st.sidebar.write("📄 PDF, DOCX and TXT upload")
st.sidebar.write("🔍 NLP-based clause classification")
st.sidebar.write("🧠 Plain-English rule-based explanations")
st.sidebar.write("🧩 Structured meaning representation")
st.sidebar.write("⏰ Condition and deadline extraction")
st.sidebar.write("🚩 Risk-pattern screening")
st.sidebar.write("📥 Downloadable analysis report")

st.sidebar.info(
    "Works directly online. No Ollama installation or API key required."
)

st.sidebar.warning(
    "This application provides preliminary text analysis, "
    "not legal advice."
)


# -------------------- HEADER --------------------

st.markdown("""
<div class="hero">
    <h1>ClauseWise AI ⚖️</h1>
    <p>Understand every clause before you agree.</p>
    <p>
        An NLP-based policy analyzer that extracts clauses,
        identifies common patterns, explains detected meanings
        and highlights conditions and potential risk signals.
    </p>
</div>
""", unsafe_allow_html=True)


# -------------------- DOCUMENT UPLOAD --------------------

st.subheader("📄 Analyze a Policy or Agreement")

uploaded_file = st.file_uploader(
    "Upload a policy document",
    type=["pdf", "docx", "txt"],
)

if uploaded_file is not None:
    try:
        if st.session_state.loaded_filename != uploaded_file.name:

            file_bytes = uploaded_file.getvalue()
            filename = uploaded_file.name.lower()

            if filename.endswith(".pdf"):
                with fitz.open(
                    stream=file_bytes,
                    filetype="pdf",
                ) as pdf:
                    extracted_text = "\n".join(
                        page.get_text() for page in pdf
                    )

            elif filename.endswith(".docx"):
                document = Document(io.BytesIO(file_bytes))
                extracted_text = "\n".join(
                    paragraph.text
                    for paragraph in document.paragraphs
                )

            else:
                extracted_text = file_bytes.decode("utf-8-sig")

            if extracted_text.strip():
                st.session_state.policy_text = extracted_text
                st.session_state.analysis_results = []
                st.session_state.loaded_filename = uploaded_file.name

                st.success("Document text extracted successfully!")

            else:
                st.warning(
                    "No selectable text was found. Scanned PDFs "
                    "need OCR, which is not included in this version."
                )

    except Exception as error:
        st.error(f"Could not read the file: {error}")


# -------------------- TEXT INPUT --------------------

policy_text = st.text_area(
    "Paste or edit policy text",
    key="policy_text",
    height=240,
    placeholder="Paste an agreement, terms of service or privacy policy here...",
)


# -------------------- ANALYSIS --------------------

if st.button(
    "🔍 Analyze Policy",
    type="primary",
    use_container_width=True,
):

    if not policy_text.strip():
        st.warning("Please paste text or upload a document.")

    else:
        try:
            with st.spinner("Analyzing clauses and identifying patterns..."):

                st.session_state.analysis_results = analyze_policy(
                    policy_text
                )

            if st.session_state.analysis_results:
                st.success("Policy analysis completed successfully!")
            else:
                st.warning(
                    "No clauses were identified. Try providing more text."
                )

        except Exception as error:
            st.session_state.analysis_results = []
            st.error(f"Analysis failed: {error}")


# -------------------- RESULTS DASHBOARD --------------------

results = st.session_state.analysis_results

if results:

    st.divider()
    st.header("📊 Analysis Dashboard")

    category_counts = {}
    risk_counts = {}

    for result in results:

        category = result.get("category", "Unclassified")
        risk = result.get("risk_level", "Not assessed")

        category_counts[category] = (
            category_counts.get(category, 0) + 1
        )

        risk_counts[risk] = risk_counts.get(risk, 0) + 1

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Clauses", len(results))

    col2.metric(
        "Categories Found",
        len(category_counts)
    )

    col3.metric(
        "High-Attention Flags",
        risk_counts.get("High attention", 0)
    )

    col4.metric(
        "Medium-Attention Flags",
        risk_counts.get("Medium attention", 0)
    )

    left, right = st.columns(2)

    with left:
        st.subheader("Clause Categories")
        st.bar_chart(category_counts)

    with right:
        st.subheader("Attention Patterns")
        st.bar_chart(risk_counts)


    # -------------------- CLAUSE DETAILS --------------------

    st.divider()
    st.subheader("🔎 Clause-by-Clause Analysis")

    for result in results:

        confidence = max(
            0.0,
            min(
                1.0,
                float(result.get("confidence", 0.50))
            )
        )

        risk = result.get("risk_level", "Not assessed")

        meaning = result.get(
            "meaning_representation", {}
        )

        if not isinstance(meaning, dict):
            meaning = {}

        clause_number = result.get("clause_number", "?")
        category = result.get("category", "Unclassified")

        original_text = result.get(
            "original_text", "Original clause unavailable."
        )

        simple_explanation = result.get(
            "simple_explanation",
            "No common explanation pattern was identified."
        )

        with st.expander(
            f"Clause {clause_number} — {category} — {risk}",
            expanded=False
        ):

            st.markdown("### 1. Original Agreement Clause")
            st.write(original_text)

            st.markdown("### 2. Simple Meaning")
            st.info(simple_explanation)

            st.caption(
                "This explanation is generated using configured "
                "NLP and text-pattern analysis, not generative AI."
            )

            st.markdown("### 3. Structured Meaning Representation")

            meaning_col1, meaning_col2 = st.columns(2)

            with meaning_col1:

                st.markdown("**Actor**")
                st.write(meaning.get("actor", "Not identified"))

                st.markdown("**Action**")
                st.write(meaning.get("action", "Not identified"))

                st.markdown("**Object**")
                st.write(meaning.get("object", "Not identified"))

            with meaning_col2:

                st.markdown("**Modality**")
                st.write(meaning.get("modality", "Not identified"))

                st.markdown("**Conditions**")

                meaning_conditions = meaning.get(
                    "conditions", []
                )

                if meaning_conditions:
                    for condition in meaning_conditions:
                        st.write(f"• {condition}")
                else:
                    st.write("No common condition pattern detected.")

            with st.expander("View machine-readable meaning"):
                st.json(meaning)


            # -------------------- CLASSIFICATION --------------------

            st.markdown("### 4. Clause Classification")

            st.write(f"**Category:** {category}")

            st.progress(confidence)

            st.write(
                f"Rule-match score: {confidence:.0%}"
            )

            st.caption(
                "This score represents the configured rule match, "
                "not a calibrated probability of correctness."
            )


            # -------------------- RISK SCREENING --------------------

            st.markdown("### 5. Risk-Pattern Screening")

            if risk == "High attention":
                st.error(f"🚩 {risk}")

            elif risk == "Medium attention":
                st.warning(f"⚠️ {risk}")

            else:
                st.info(f"ℹ️ {risk}")

            risk_reasons = result.get("risk_reasons", [])

            if risk_reasons:
                for reason in risk_reasons:
                    st.write(f"• {reason}")
            else:
                st.write("No configured risk patterns were identified.")

            st.caption(
                "Risk labels are preliminary screening signals, "
                "not legal conclusions."
            )


            # -------------------- CONDITIONS --------------------

            st.markdown("### 6. Conditions and Deadlines")

            conditions = result.get("conditions", [])

            if conditions:
                for condition in conditions:
                    st.write(f"• {condition}")
            else:
                st.write(
                    "No common condition or deadline pattern detected."
                )


    # -------------------- DOWNLOAD REPORT --------------------

    report_lines = [
        "CLAUSEWISE — POLICY ANALYSIS REPORT",
        "=" * 55,
        "",
        "Analysis type: Rule-based NLP and text-pattern analysis",
        "Disclaimer: Preliminary automated text analysis only.",
        "This report is not legal advice or a definitive risk assessment.",
        "",
        f"Total clauses analyzed: {len(results)}",
        "",
    ]

    for result in results:

        meaning = result.get(
            "meaning_representation", {}
        )

        if not isinstance(meaning, dict):
            meaning = {}

        confidence = float(
            result.get("confidence", 0.50)
        )

        report_lines.extend([
            f"CLAUSE {result.get('clause_number', '?')}",
            "-" * 40,

            f"Category: {result.get('category', 'Unclassified')}",

            f"Rule-match score: {confidence:.0%}",

            f"Attention level: {result.get('risk_level', 'Not assessed')}",

            "Attention reasons: " + "; ".join(
                map(str, result.get("risk_reasons", []))
            ),

            "",
            "Original clause:",
            str(result.get("original_text", "")),

            "",
            "Simple meaning:",
            str(result.get("simple_explanation", "")),

            "",
            "Structured meaning:",

            f"Actor: {meaning.get('actor', 'Not identified')}",

            f"Action: {meaning.get('action', 'Not identified')}",

            f"Object: {meaning.get('object', 'Not identified')}",

            f"Modality: {meaning.get('modality', 'Not identified')}",

            "Semantic conditions: " + "; ".join(
                map(str, meaning.get("conditions", []))
            ),

            "Detected conditions/deadlines: " + "; ".join(
                map(str, result.get("conditions", []))
            ),

            "",
        ])

    st.download_button(
        "⬇️ Download Analysis Report",
        data="\n".join(report_lines),
        file_name="clausewise_analysis.txt",
        mime="text/plain",
        use_container_width=True,
    )


# -------------------- FOOTER --------------------

st.divider()

st.caption(
    "ClauseWise | NLP-Based Policy Analysis and Meaning Representation"
)

st.caption(
    "This application uses configured NLP and rule-based patterns. "
    "It may miss context, exceptions or complex legal meanings. "
    "Review the original document and consult a qualified legal "
    "professional before making important decisions."
)

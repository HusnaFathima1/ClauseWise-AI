
import io
import re
import streamlit as st
import fitz
from docx import Document

# ==================================================
# CLAUSEWISE AI - PUBLIC RULE-BASED NLP VERSION
# No Ollama, API key or local AI required
# ==================================================

st.set_page_config(
    page_title="ClauseWise | Legal Document Analyzer",
    page_icon="⚖️",
    layout="wide"
)

# ---------------- DESIGN ----------------

st.markdown("""
<style>
.stApp {background:#f5f7fb;}
.block-container {max-width:1150px;padding-top:2rem;}
.hero {
 background:linear-gradient(120deg,#132744,#254a91,#4268e9);
 padding:32px;border-radius:20px;color:white;margin-bottom:25px;
}
.hero h1 {color:white;font-size:36px;}
.hero p {color:#e5edff;font-size:16px;}
.card {
 background:white;padding:20px;border-radius:14px;
 border:1px solid #e5eaf2;margin:12px 0;
}
.small {color:#66758b;font-size:13px;}
</style>
""", unsafe_allow_html=True)

# ---------------- TEXT EXTRACTION ----------------

def extract_text(file):
    data = file.getvalue()
    name = file.name.lower()

    if name.endswith(".pdf"):
        with fitz.open(stream=data, filetype="pdf") as pdf:
            return "\n".join(page.get_text() for page in pdf)

    if name.endswith(".docx"):
        doc = Document(io.BytesIO(data))
        parts = [p.text for p in doc.paragraphs]
        for table in doc.tables:
            for row in table.rows:
                parts.append(" | ".join(c.text for c in row.cells))
        return "\n".join(parts)

    if name.endswith(".txt"):
        return data.decode("utf-8", errors="replace")

    return ""

# ---------------- CLAUSE CLASSIFICATION ----------------

CATEGORIES = {
    "Payment": ["payment", "pay", "fee", "invoice", "salary",
                "amount", "charges", "interest"],
    "Termination": ["terminate", "termination", "cancel",
                    "cancellation", "end this agreement"],
    "Confidentiality": ["confidential", "disclose", "secret",
                        "non-disclosure", "proprietary"],
    "Liability": ["liability", "liable", "damages",
                  "indemnify", "indemnification"],
    "Privacy": ["personal data", "privacy", "data collection",
                "process personal", "information"],
    "Renewal": ["renew", "renewal", "automatically extend",
                "auto-renew"],
    "Restrictions": ["prohibited", "shall not", "must not",
                     "restricted", "forbidden"],
    "Dispute Resolution": ["arbitration", "dispute",
                           "jurisdiction", "court"],
    "Obligations": ["shall", "must", "agrees to", "is required to"],
}

RISK_PATTERNS = {
    "High attention": [
        "unlimited liability",
        "without notice",
        "sole discretion",
        "waive all claims",
        "irrevocably",
        "without any refund",
        "perpetual",
        "indemnify against all claims",
    ],
    "Medium attention": [
        "penalty",
        "automatic renewal",
        "non-refundable",
        "at any time",
        "additional charges",
        "may modify",
        "without prior consent",
    ],
}

def classify_clause(text):
    lower = text.lower()

    scores = {
        category: sum(1 for word in words if word in lower)
        for category, words in CATEGORIES.items()
    }

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        best = "General Provision"

    return best

def identify_risk(text):
    lower = text.lower()

    for level in ["High attention", "Medium attention"]:
        matches = [
            phrase for phrase in RISK_PATTERNS[level]
            if phrase in lower
        ]
        if matches:
            return level, matches

    return "No configured risk pattern detected", []

def explain_clause(text, category):
    lower = text.lower()

    if category == "Payment":
        return ("This clause concerns money, fees or payment obligations. "
                "Check the amount, due date, additional charges and refund terms.")

    if category == "Termination":
        return ("This clause concerns ending the agreement. "
                "Check who can terminate it, the notice period and any consequences.")

    if category == "Confidentiality":
        return ("This clause concerns protecting confidential information. "
                "Check what information is protected, permitted disclosures and how long the duty lasts.")

    if category == "Liability":
        return ("This clause concerns responsibility for losses or damages. "
                "Check the extent of responsibility, exclusions and any financial limits.")

    if category == "Privacy":
        return ("This clause concerns personal information or data handling. "
                "Check what data is collected, why it is used and who can access it.")

    if category == "Renewal":
        return ("This clause concerns extending the agreement. "
                "Check whether renewal happens automatically and how to prevent it.")

    if category == "Restrictions":
        return ("This clause places limits on permitted actions. "
                "Identify exactly what is restricted and whether exceptions are provided.")

    if category == "Dispute Resolution":
        return ("This clause explains how disagreements may be resolved. "
                "Check the specified process, location and applicable rules.")

    if "shall" in lower or "must" in lower:
        return ("This clause appears to create a duty or requirement. "
                "Identify who must act, what they must do and any stated deadline.")

    return ("This clause contains a general agreement provision. "
            "Review the exact wording to identify its effect, conditions and exceptions.")

def split_clauses(text):
    chunks = re.split(r'\n\s*(?=(?:\d+(?:\.\d+)*[.)]?\s+|[A-Z][.)]\s+))', text)
    clauses = []

    for chunk in chunks:
        chunk = re.sub(r'\s+', ' ', chunk).strip()
        if len(chunk) >= 25:
            clauses.append(chunk)

    if not clauses:
        clauses = [
            part.strip()
            for part in re.split(r'(?<=[.;])\s+', text)
            if len(part.strip()) >= 25
        ]

    return clauses[:60]

def analyze(text):
    results = []

    for index, clause in enumerate(split_clauses(text), 1):
        category = classify_clause(clause)
        risk, reasons = identify_risk(clause)

        results.append({
            "number": index,
            "text": clause,
            "category": category,
            "meaning": explain_clause(clause, category),
            "risk": risk,
            "reasons": reasons,
        })

    return results

# ---------------- HEADER ----------------

st.markdown("""
<div class="hero">
 <h1>⚖️ ClauseWise</h1>
 <p>Understand the words. Notice the risks.</p>
 <p>Explore agreement clauses, identify obligations and examine
 potential risk patterns in plain English.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("⚖️ ClauseWise")
    st.caption("Legal Document Awareness")
    st.divider()
    st.write("📄 Document upload")
    st.write("🔍 Clause classification")
    st.write("📖 Plain-English explanations")
    st.write("🚩 Risk-pattern detection")
    st.write("📥 Downloadable report")
    st.divider()
    st.info("This public version uses rule-based NLP. No local AI or API key is required.")

# ---------------- INPUT ----------------

st.header("1. Upload your agreement")

uploaded = st.file_uploader(
    "Choose a document",
    type=["pdf", "docx", "txt"]
)

pasted = st.text_area(
    "Or paste agreement text",
    height=180,
    placeholder="Paste your agreement or legal clause here..."
)

text = ""

if uploaded:
    try:
        text = extract_text(uploaded)
        if not text.strip():
            st.warning("No selectable text found. Scanned PDFs require OCR.")
    except Exception as e:
        st.error(f"Document reading error: {e}")

elif pasted.strip():
    text = pasted.strip()

# ---------------- ANALYSIS ----------------

if text.strip():
    st.success("Document text is ready for analysis.")

    if st.button("🔍 Analyze Agreement", type="primary",
                 use_container_width=True):
        st.session_state.results = analyze(text)
        st.session_state.source_text = text

if st.session_state.get("results"):
    results = st.session_state.results

    st.divider()
    st.header("2. Analysis Dashboard")

    high = sum(r["risk"] == "High attention" for r in results)
    medium = sum(r["risk"] == "Medium attention" for r in results)
    categories = len(set(r["category"] for r in results))

    a, b, c, d = st.columns(4)
    a.metric("Total Clauses", len(results))
    b.metric("Categories", categories)
    c.metric("High Attention", high)
    d.metric("Medium Attention", medium)

    st.subheader("Category Distribution")
    counts = {}
    for r in results:
        counts[r["category"]] = counts.get(r["category"], 0) + 1
    st.bar_chart(counts)

    st.divider()
    st.header("3. Clause-by-Clause Explanation")

    for r in results:
        with st.expander(
            f"Clause {r['number']} | {r['category']} | {r['risk']}"
        ):
            st.markdown("**Original Agreement Clause**")
            st.write(r["text"])

            st.markdown("**Simple Meaning**")
            st.info(r["meaning"])

            st.markdown("**Classification**")
            st.write(r["category"])

            st.markdown("**Risk Screening**")
            if r["risk"] == "High attention":
                st.error(r["risk"])
            elif r["risk"] == "Medium attention":
                st.warning(r["risk"])
            else:
                st.success(r["risk"])

            if r["reasons"]:
                st.write("Matched patterns:", ", ".join(r["reasons"]))

    # ---------------- CONCLUSION ----------------

    st.divider()
    st.header("4. Overall Conclusion")

    if high:
        st.warning(
            f"{high} clause(s) contain configured high-attention patterns. "
            "Review their exact wording carefully before accepting the agreement."
        )
    elif medium:
        st.info(
            f"{medium} clause(s) contain configured medium-attention patterns. "
            "Review the conditions, charges and obligations."
        )
    else:
        st.success(
            "No configured high- or medium-attention patterns were detected. "
            "This does not guarantee that the agreement is safe or risk-free."
        )

    st.write(
        f"The document contains {len(results)} detected clauses across "
        f"{categories} categories. Read the original wording and verify "
        "important obligations before signing."
    )

    # ---------------- REPORT ----------------

    st.divider()
    st.header("5. Download Report")

    report = [
        "CLAUSEWISE - POLICY ANALYSIS REPORT",
        "=" * 45,
        f"Total clauses: {len(results)}",
        f"High attention: {high}",
        f"Medium attention: {medium}",
        "",
    ]

    for r in results:
        report.extend([
            f"CLAUSE {r['number']}",
            f"Category: {r['category']}",
            f"Attention: {r['risk']}",
            f"Original text: {r['text']}",
            f"Simple meaning: {r['meaning']}",
            f"Matched patterns: {', '.join(r['reasons'])}",
            "",
        ])

    report.extend([
        "CONCLUSION",
        f"{high} high-attention and {medium} medium-attention clauses detected.",
        "",
        "DISCLAIMER: Preliminary rule-based text analysis only. Not legal advice.",
    ])

    st.download_button(
        "⬇️ Download ClauseWise Report",
        "\n".join(report),
        file_name="ClauseWise_Report.txt",
        mime="text/plain",
        use_container_width=True,
    )

# ---------------- FOOTER ----------------

st.divider()
st.caption(
    "ClauseWise | Rule-Based NLP Legal Document Awareness "
    "| Automated results are preliminary and are not legal advice."
)

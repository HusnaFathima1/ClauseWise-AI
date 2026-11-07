
import re
import spacy


# ============================================================
# CLAUSEWISE AI - NLP MEANING REPRESENTATION
# ============================================================

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = spacy.blank("en")
    nlp.add_pipe("sentencizer")


# -------------------- UTILITIES --------------------

def contains_phrase(text, phrase):
    return bool(
        re.search(
            r"(?<!\w)" + re.escape(phrase) + r"(?!\w)",
            text,
            re.IGNORECASE,
        )
    )


def contains_any(text, phrases):
    return any(contains_phrase(text, phrase) for phrase in phrases)


def split_into_clauses(text):
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []

    doc = nlp(text)
    return [
        sentence.text.strip()
        for sentence in doc.sents
        if sentence.text.strip()
    ]


# -------------------- CLASSIFICATION --------------------

CLAUSE_TYPES = {
    "Prohibition": [
        "must not", "shall not", "may not", "cannot",
        "prohibited", "forbidden", "not permitted", "not allowed"
    ],
    "Condition": [
        "unless", "provided that", "subject to",
        "in the event that", "on condition that"
    ],
    "Termination": [
        "terminate", "termination", "suspend", "revoke",
        "cancel", "close your account"
    ],
    "Data and Privacy": [
        "personal information", "personal data", "privacy",
        "share your data", "third party", "tracking",
        "cookies", "collect your information"
    ],
    "Payment or Fees": [
        "fee", "payment", "charge", "penalty",
        "refund", "subscription", "billing", "pay"
    ],
    "Obligation": [
        "must", "shall", "required to",
        "is responsible for", "obligated to", "have to"
    ],
    "Permission": [
        "may", "permitted to", "allowed to", "can"
    ],
}


def classify_clause(clause):
    lower = clause.lower()

    # Check prohibitions before general modal words.
    priority = [
        "Prohibition", "Condition", "Termination",
        "Data and Privacy", "Payment or Fees",
        "Obligation", "Permission"
    ]

    scores = {
        "Prohibition": 0.95,
        "Condition": 0.90,
        "Termination": 0.85,
        "Data and Privacy": 0.85,
        "Payment or Fees": 0.85,
        "Obligation": 0.80,
        "Permission": 0.80,
    }

    for category in priority:
        if contains_any(lower, CLAUSE_TYPES[category]):
            return category, scores[category]

    return "General Policy", 0.50


# -------------------- CONDITIONS --------------------

def extract_conditions(clause):
    patterns = [
        r"\bunless\b[^,.;]*",
        r"\bif\b[^,.;]*",
        r"\bprovided that\b[^,.;]*",
        r"\bsubject to\b[^,.;]*",
        r"\bexcept(?: as| when| where)?\b[^,.;]*",
        r"\bwithin\s+\d+\s+(?:hours?|days?|weeks?|months?|years?)\b",
        r"\bno later than\b[^,.;]*",
        r"\bat least\s+\d+\s+(?:hours?|days?|weeks?|months?|years?)\b",
    ]

    found = []

    for pattern in patterns:
        for match in re.finditer(pattern, clause, re.IGNORECASE):
            value = match.group(0).strip()
            if value not in found:
                found.append(value)

    return found


# -------------------- SEMANTIC FRAME --------------------

def extract_meaning(clause):
    text = clause.strip()

    actor = "Not confidently identified"
    action = "Not confidently identified"
    object_ = "Not confidently identified"
    modality = "Not identified"

    # Match prohibitions first, then obligations, then permission.
    if re.search(
        r"\b(must not|shall not|may not|cannot)\b",
        text, re.IGNORECASE
    ):
        modality = "Prohibition"
    elif re.search(
        r"\b(must|shall|required to|have to|obligated to)\b",
        text, re.IGNORECASE
    ):
        modality = "Obligation"
    elif re.search(
        r"\b(may|can|permitted to|allowed to)\b",
        text, re.IGNORECASE
    ):
        modality = "Permission or possibility"

    # Pattern A: "You must pay the subscription fee..."
    # Pattern B: "You must not share your password..."
    # Pattern C: "The company may terminate your account..."
    pattern = re.compile(
        r"\b(?P<actor>the company|the provider|the organization|"
        r"the service provider|the user|the customer|the subscriber|"
        r"you|the parties|users|customers|we|they)\b"
        r"\s+"
        r"(?P<modal>must not|shall not|may not|must|shall|may|can)"
        r"\s+"
        r"(?P<action>[a-z]+)"
        r"(?:\s+(?P<object>[^,.;]+))?",
        re.IGNORECASE,
    )

    match = pattern.search(text)

    if match:
        actor = match.group("actor")
        action = match.group("action")
        remainder = (match.group("object") or "").strip()

        # Keep the object phrase and remove trailing conditions.
        remainder = re.split(
            r"\b(?:if|unless|provided that|within|before|after)\b",
            remainder,
            flags=re.IGNORECASE,
        )[0].strip()

        # Remove a leading linking phrase if present.
        remainder = re.sub(
            r"^(?:to|that)\s+", "", remainder, flags=re.IGNORECASE
        )

        if remainder:
            object_ = remainder

    return {
        "actor": actor,
        "action": action,
        "object": object_,
        "modality": modality,
        "conditions": extract_conditions(text),
    }


# -------------------- SIMPLE MEANING --------------------

def simplify_clause(clause):
    text = clause.strip()
    lower = text.lower()

    # Payment deadline
    if (
        contains_any(lower, ["pay", "payment"])
        and contains_any(lower, ["must", "shall", "required to", "have to"])
    ):
        deadline = re.search(
            r"\bwithin\s+\d+\s+(?:hours?|days?|weeks?|months?|years?)\b",
            text, re.IGNORECASE
        )

        explanation = (
            "You are required to make the payment. Check the original "
            "agreement for the amount and any other payment rules."
        )

        if deadline:
            explanation = (
                f"You must make the payment {deadline.group(0)}. "
                "Check the agreement for the amount and payment method."
            )

        return explanation

    # Password or credential restrictions
    if (
        contains_any(lower, ["must not", "shall not", "may not", "cannot"])
        and contains_any(lower, [
            "password", "login credentials", "login details",
            "account credentials"
        ])
    ):
        return (
            "You are not allowed to share your password or login "
            "credentials with other people."
        )

    # Other prohibitions
    if re.search(
        r"\b(must not|shall not|may not|cannot)\b",
        lower
    ) or contains_any(lower, [
        "prohibited", "forbidden", "not permitted", "not allowed"
    ]):
        return (
            "This clause forbids or restricts an action. Check the "
            "original wording to identify the exact restriction "
            "and any exceptions."
        )

    # Conditional termination
    if (
        contains_any(lower, [
            "terminate", "termination", "suspend", "revoke",
            "close your account"
        ])
        and contains_any(lower, [
            "if you", "if the user", "if the customer",
            "violate", "breach", "break"
        ])
    ):
        return (
            "The company may close or suspend the account if the "
            "user breaks the rules of the agreement."
        )

    # Other termination
    if contains_any(lower, [
        "terminate", "termination", "suspend", "revoke"
    ]):
        return (
            "This clause concerns ending or suspending an agreement, "
            "service, or account. Check who can take this action and when."
        )

    # Automatic renewal
    if contains_any(lower, [
        "automatically renew", "automatic renewal",
        "renews automatically", "auto-renew"
    ]):
        return (
            "The subscription or agreement may renew automatically. "
            "Check the original text for renewal dates and cancellation rules."
        )

    # Data and privacy
    if contains_any(lower, [
        "personal information", "personal data",
        "share your data", "third party", "tracking", "cookies"
    ]):
        return (
            "This clause concerns personal information or data handling. "
            "Check what information is collected or shared, with whom, "
            "and for what purpose."
        )

    # Conditions
    if contains_any(lower, [
        "unless", "provided that", "subject to",
        "in the event that", "on condition that"
    ]):
        conditions = extract_conditions(text)
        if conditions:
            return (
                "This clause applies under a stated condition: "
                + "; ".join(conditions)
                + ". Read the original wording for the complete rule."
            )

    # General obligation
    if contains_any(lower, [
        "must", "shall", "required to", "obligated to", "have to"
    ]):
        return (
            "This clause describes a requirement or responsibility. "
            "Check who must act, what is required, and any deadlines."
        )

    # Permission
    if contains_any(lower, ["may", "permitted to", "allowed to", "can"]):
        return (
            "This clause describes an action that may be permitted. "
            "Check who may act and what conditions apply."
        )

    # Limited wording simplification
    simplified = text
    for old, new in [
        (r"\bprior to\b", "before"),
        (r"\bsubsequent to\b", "after"),
        (r"\bin the event that\b", "if"),
        (r"\bnotwithstanding\b", "despite"),
        (r"\bcommence\b", "begin"),
        (r"\bremit\b", "pay"),
    ]:
        simplified = re.sub(old, new, simplified, flags=re.IGNORECASE)

    if simplified != text:
        return "In simpler wording: " + simplified

    return (
        "A separate explanation could not be generated confidently "
        "using the current rules. Review the original clause in context."
    )


# -------------------- ATTENTION-PATTERN SCREENING --------------------

def assess_risk(clause):
    lower = clause.lower()
    reasons = []

    high_patterns = {
        "Penalty or late-fee language": [
            "penalty", "late fee", "liquidated damages",
            "forfeit", "forfeiture"
        ],
        "Automatic renewal language": [
            "automatically renew", "automatic renewal",
            "renews automatically", "auto-renew"
        ],
        "Termination or suspension language": [
            "terminate", "termination", "suspend",
            "revoke", "close your account"
        ],
        "Liability or indemnity language": [
            "indemnify", "indemnification", "liable",
            "limitation of liability", "hold harmless"
        ],
        "Waiver or dispute language": [
            "waive", "waiver", "binding arbitration",
            "class action", "dispute resolution"
        ],
    }

    medium_patterns = {
        "Payment or financial commitment": [
            "fee", "payment", "charge", "billing",
            "subscription", "pay", "non-refundable"
        ],
        "Personal-data handling": [
            "personal information", "personal data",
            "share your data", "third party", "tracking", "cookies"
        ],
        "Deadline or time limit": [
            "within ", "no later than", "before expiry",
            "days", "hours", "months"
        ],
        "Restriction or prohibition": [
            "must not", "shall not", "may not",
            "prohibited", "forbidden", "not allowed"
        ],
    }

    for reason, phrases in high_patterns.items():
        if contains_any(lower, phrases):
            reasons.append(reason)

    if reasons:
        return "High attention", reasons

    for reason, phrases in medium_patterns.items():
        if contains_any(lower, phrases):
            reasons.append(reason)

    if reasons:
        return "Medium attention", reasons

    return "General review", [
        "No configured attention pattern matched; review the clause in context."
    ]


# -------------------- MAIN ANALYZER --------------------

def analyze_policy(text):
    results = []

    for index, clause in enumerate(split_into_clauses(text), start=1):
        category, confidence = classify_clause(clause)
        conditions = extract_conditions(clause)
        meaning = extract_meaning(clause)
        explanation = simplify_clause(clause)
        risk_level, risk_reasons = assess_risk(clause)

        results.append({
            "clause_number": index,
            "original_text": clause,
            "category": category,
            "confidence": confidence,
            "conditions": conditions,
            "simple_explanation": explanation,
            "meaning_representation": meaning,
            "risk_level": risk_level,
            "risk_reasons": risk_reasons,
        })

    return results

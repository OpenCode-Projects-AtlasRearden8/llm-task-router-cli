import re
from dataclasses import dataclass


QUICK = "quick_job"
DEEP = "deep_think"

QUICK_KEYWORDS = {
    "typo": 3,
    "quick": 3,
    "short": 2,
    "summarize": 2,
    "summary": 2,
    "translate": 2,
    "rephrase": 2,
    "rewrite this sentence": 3,
    "spell": 2,
    "proofread": 2,
    "headline": 2,
    "bullet": 2,
    "list idea": 2,
    "name ideas": 2,
    "one-liner": 3,
    "caption": 2,
    "tweet": 2,
    "subject line": 3,
    "extract": 2,
    "date": 1,
    "url": 1,
    "format": 1,
    "grammar": 3,
    "question": 1,
    "answer": 1,
}

DEEP_KEYWORDS = {
    "analyze": 3,
    "analysis": 3,
    "compare and contrast": 3,
    "compare": 2,
    "evaluate": 2,
    "strategy": 3,
    "strategic": 3,
    "architect": 3,
    "architecture": 3,
    "design": 2,
    "plan": 2,
    "roadmap": 3,
    "refactor": 2,
    "migrate": 2,
    "migration": 2,
    "debug": 2,
    "investigate": 2,
    "research": 2,
    "review my code": 3,
    "code review": 3,
    "long-form": 3,
    "essay": 2,
    "chapter": 2,
    "outline a": 2,
    "pros and cons": 3,
    "trade-off": 2,
    "tradeoff": 2,
    "build a system": 3,
    "think through": 3,
    "reason": 2,
    "argument": 2,
    "proofread my whole": 2,
}

QUICK_MAX_WORDS = 5


@dataclass
class Classification:
    task: str
    category: str
    score: int
    confidence: float
    reasons: list


def _word_count(text):
    words = re.findall(r"\S+", text)
    return len(words)


def classify(task):
    text = task.strip()
    lowered = text.lower()
    quick_score = 0
    deep_score = 0
    reasons = []

    for phrase, weight in DEEP_KEYWORDS.items():
        if phrase in lowered:
            deep_score += weight

    for phrase, weight in QUICK_KEYWORDS.items():
        if phrase in lowered:
            quick_score += weight

    scope_words = (r"\b(whole|entire|all|every|everything|full|complete|"
                   r"comprehensive|detailed|thorough|in depth|in-depth)\b")
    expansion = re.search(scope_words, lowered)
    if expansion:
        deep_score += 2
        reasons.append("scope-expanding phrase: '%s'" % expansion.group(1))

    if len(text) > 240:
        deep_score += 2
        reasons.append("task text is long (%d chars)" % len(text))

    no_keyword_signals = quick_score == 0 and deep_score == 0

    words = _word_count(text)
    if words <= QUICK_MAX_WORDS:
        quick_score += 2

    score = quick_score - deep_score
    if score > 0:
        category = QUICK
    elif score < 0:
        category = DEEP
    else:
        category = QUICK
        reasons.append("tie score; ties default to quick_job (cheap to retry)")

    magnitude = max(1, max(quick_score, deep_score))
    if no_keyword_signals:
        reasons.append("no keyword signals; defaulted on length")

    if quick_score:
        reasons.append("quick signals score %d" % quick_score)
    if deep_score:
        reasons.append("deep signals score %d" % deep_score)
    reasons.append("word count %d" % words)

    confidence = round(min(1.0, 0.5 + 0.1 * magnitude), 2)
    return Classification(
        task=text,
        category=category,
        score=score,
        confidence=confidence,
        reasons=reasons,
    )

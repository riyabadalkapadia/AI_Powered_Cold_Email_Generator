import re
from typing import Optional, List, Dict
from dateutil import parser
def clean_text(text: str) -> str:
    # Remove HTML tags
    text = re.sub(r'<[^>]*?>', ' ', text)
    # Remove URLs
    text = re.sub(r'https?://[\w\-.&+(),!*%]+', '', text)
    # Keep some punctuation but remove others
    text = re.sub(r'[^\w\s.,!?-]', ' ', text)
    # Replace multiple spaces with a single space
    text = re.sub(r'\s{2,}', ' ', text)
    # Trim leading and trailing whitespace
    text = text.strip()
    return text


def _try_parse_date(date_str: str) -> Optional[object]:
    """Attempt to parse a date string into a datetime object.

    Returns the datetime object or None if parsing fails.
    """
    # Remove ordinal suffixes (1st, 2nd, 3rd, 4th)
    cleaned = re.sub(r'(?<=\d)(st|nd|rd|th)', '', date_str, flags=re.IGNORECASE)
    # Strip extra words like 'until' or ':'
    cleaned = re.sub(r'^(until|till)\b[:\-\s]*', '', cleaned, flags=re.IGNORECASE)
    try:
        dt = parser.parse(cleaned, fuzzy=True, dayfirst=False)
        return dt
    except Exception:
        return None


def extract_deadline(text: str) -> Optional[str]:
    """Try to find an application deadline in the provided text.

    Strategy:
    - Find all date-like substrings using several regex patterns.
    - Score each candidate by proximity to strong/medium/weak anchor phrases.
    - Prefer candidates with stronger anchors; break ties by preferring parsed dates and more recent dates.
    - Return a human-readable date string (e.g., 'November 04, 2025') or None.
    """
    if not text:
        return None

    # anchor groups
    strong_anchors = [
        'must complete', 'must complete your application', 'complete your application before',
        'you must complete', 'complete before', 'complete your application', 'must apply by',
        'you must apply', 'complete by', 'end of day on', 'end of day', 'you must complete your application before'
    ]
    medium_anchors = [
        'apply by', 'apply before', 'application deadline', 'deadline', 'closing date',
        'last date to apply', 'last date', 'apply until', 'apply through'
    ]
    weak_anchors = [
        'will accept applications', 'accept applications', 'applications will be accepted',
        'open until', 'accepting applications until', 'applications open', 'will begin accepting'
    ]

    # date regex patterns (handles ordinals, abbreviated months, numeric and ISO style)
    month_names = r'(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?'
    date_patterns = [
        rf"\b{month_names}\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+\d{{4}}\b",
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        rf"\b\d{{1,2}}(?:st|nd|rd|th)?\s+{month_names}\s+\d{{4}}\b",
        r"\b\d{4}-\d{2}-\d{2}\b",
    ]
    combined_date_regex = re.compile('|'.join(date_patterns), flags=re.IGNORECASE)

    # special-case: phrases like 'will accept applications ... until <date>'
    special_until = re.search(r'will accept applications[\s\S]{0,300}?until\s+([^\n\r]{0,120})', text, flags=re.IGNORECASE)
    if special_until:
        candidate = special_until.group(1)
        msp = combined_date_regex.search(candidate)
        if msp:
            parsed = _try_parse_date(msp.group(0).strip())
            if parsed:
                return parsed.strftime('%B %d, %Y')
            return msp.group(0).strip()

    # collect all date candidates and score them
    candidates: List[Dict] = []
    for m in combined_date_regex.finditer(text):
        ds = m.group(0).strip()
        parsed = _try_parse_date(ds)
        s, e = m.start(), m.end()
        window_start = max(0, s - 200)
        window_end = min(len(text), e + 200)
        context = text[window_start:window_end]
        ctx_lower = context.lower()
        score = 0
        for a in strong_anchors:
            if a in ctx_lower:
                score = max(score, 300)
        for a in medium_anchors:
            if a in ctx_lower and score < 200:
                score = max(score, 200)
        for a in weak_anchors:
            if a in ctx_lower and score < 100:
                score = max(score, 100)
        # small bonus if the word 'before' appears close to the date
        if re.search(r'\b(before|by|until|through|throughout)\b', ctx_lower):
            score += 5
        candidates.append({'text': ds, 'parsed': parsed, 'score': score, 'context': context, 'span': (s, e)})

    if not candidates:
        return None

    # sort candidates by score desc, then by parsed datetime (later dates preferred), then by earliest occurrence
    def sort_key(c):
        parsed_ts = c['parsed'].timestamp() if c['parsed'] is not None else 0
        return (c['score'], parsed_ts, -c['span'][0])

    candidates.sort(key=sort_key, reverse=True)
    best = candidates[0]
    if best['parsed']:
        return best['parsed'].strftime('%B %d, %Y')
    return best['text']


def debug_deadline_search(text: str, context_chars: int = 200) -> List[Dict]:
    """Return a list of context snippets where deadline-like anchors appear and any date matches found nearby.

    Each item is a dict: { 'anchor': anchor, 'context': snippet, 'date_match': matched_date_or_None }
    """
    results: List[Dict] = []
    if not text:
        return results

    anchors = [
        'will accept applications', 'accept applications', 'applications will be accepted',
        'open until', 'accepting applications until', 'apply by', 'apply before', 'application deadline',
        'deadline', 'closing date', 'last date to apply', 'last date', 'complete your application', 'end of day'
    ]

    month_names = r'(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?'
    date_patterns = [
        rf"\b{month_names}\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+\d{{4}}\b",
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        rf"\b\d{{1,2}}(?:st|nd|rd|th)?\s+{month_names}\s+\d{{4}}\b",
        r"\b\d{4}-\d{2}-\d{2}\b",
    ]
    combined_date_regex = re.compile('|'.join(date_patterns), flags=re.IGNORECASE)

    text_lower = text.lower()
    for anchor in anchors:
        start_idx = 0
        while True:
            idx = text_lower.find(anchor, start_idx)
            if idx == -1:
                break
            start = max(0, idx - context_chars)
            end = min(len(text), idx + len(anchor) + context_chars)
            snippet = text[start:end]
            m = combined_date_regex.search(snippet)
            results.append({'anchor': anchor, 'context': snippet, 'date_match': m.group(0).strip() if m else None})
            start_idx = idx + len(anchor)

    # If no anchors found, also return a few standalone date matches from the whole text
    if not results:
        for m in combined_date_regex.finditer(text):
            start = max(0, m.start() - context_chars)
            end = min(len(text), m.end() + context_chars)
            snippet = text[start:end]
            results.append({'anchor': None, 'context': snippet, 'date_match': m.group(0).strip()})

    return results
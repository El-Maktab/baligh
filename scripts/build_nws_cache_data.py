#!/usr/bin/env python3
"""Build NWS static cache YAML files from external sources.

*****************************************************************************
*   NOTE: THIS FILE IS COMPLETELY AI GENERATED TO FETCH DATA                *
*   FROM MULTIPLE SOURCES FOR CACHE IN NWS. FEEL FREE TO REMOVE             *
*   IT IF NEEDED.                                                           *
*****************************************************************************

Sources:
    - Arabic Wikiquote
    - Jawaher multidialectal Arabic proverbs dataset (HuggingFace)
    - Famous phrases and religious collocations

Outputs:
    - src/services/nws/data/idioms.yaml
    - src/services/nws/data/phrases.yaml

Key generation strategy:
    For every proverb / phrase of N words, generate N-1 (key, suggestion) pairs
    starting from keys of length 2, to MAX_KEY_WORDS:
        "ضرب عصفورين بحجر واحد":
            key="ضرب"              suggestion="عصفورين"
            key="ضرب عصفورين"     suggestion="بحجر"
            key="ضرب عصفورين بحجر" suggestion="واحد"

    All keys are normalized with the same loose_arabic_lookup_key function
    used at runtime by CacheManager.build_key.

Usage:
    uv run python scripts/build_nws_cache_data.py
    uv run python scripts/build_nws_cache_data.py --dry-run
    uv run python scripts/build_nws_cache_data.py --limit 200

Authors:
    - Akram Hany
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
import unicodedata
from pathlib import Path
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

import yaml

###############################################################################
# Paths
###############################################################################

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "src" / "services" / "nws" / "data"
IDIOMS_OUT = DATA_DIR / "idioms.yaml"
PHRASES_OUT = DATA_DIR / "phrases.yaml"

###############################################################################
# Constants
###############################################################################

# should match the context_window_size in config.yaml
MAX_KEY_WORDS = 5

# min words of proverbs (key + suggested word, which means key min length is 2).
MIN_WORDS = 3

# max allowed proverbs sizes.
MAX_WORDS = 15

# required by wikimedia
USER_AGENT = "BalighNWSBuilder/1.0 (GP project; contact: akramhany65@gmail.com)"

# Wikiquote pages that contain Arabic proverbs
WIKIQUOTE_PAGES = [
    "أمثال_عربية",
]

# Jawaher hugging face api
HF_ROWS_URL = (
    "https://datasets-server.huggingface.co/rows"
    "?dataset=UBC-NLP%2FJawaher-benchmark"
    "&config=default"
    "&split=train"
    "&offset={offset}"
    "&length={length}"
)
HF_BATCH = 100  # rows per request

MSA_VARIETIES = {"msa", "MSA", "Modern Standard Arabic", "modern standard arabic"}

###############################################################################
# Normalization (using loose_arabic_lookup_key())
###############################################################################
# TODO: replace the normalization section with a call to loose_arabic_lookup_key
_DIACRITICS_RE = re.compile(r"[\u064b-\u065f\u0670]")
_CONTROL_MARKS_RE = re.compile(r"[\u200e\u200f\u202a-\u202e\u2066-\u2069]")
_WHITESPACE_RE = re.compile(r"\s+")
_TATWEEL = "\u0640"
_LOOSE_ARABIC_TRANSLATION = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ى": "ي",
        "ة": "ه",
    }
)
# Match a single Arabic "word" (letters only, no digits, no punctuation)
_ARABIC_WORD_RE = re.compile(r"^[\u0621-\u064a\u066e-\u06d3]+$")


def _normalize(text: str) -> str:
    """Normalize Arabic text, matching CacheManager.build_key output."""
    text = unicodedata.normalize("NFKC", text)
    text = _CONTROL_MARKS_RE.sub("", text)
    text = text.replace(_TATWEEL, "")
    text = _DIACRITICS_RE.sub("", text)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text.translate(_LOOSE_ARABIC_TRANSLATION)


def _normalize_word(word: str) -> str:
    return _normalize(word)


def _is_arabic_word(word: str) -> bool:
    clean = _normalize(word)
    return bool(clean) and bool(_ARABIC_WORD_RE.fullmatch(clean))


###############################################################################
# Wikitext cleaning
###############################################################################

# [[link|display]] → display   /   [[link]] → link
_WIKILINK_RE = re.compile(r"\[\[(?:[^\]|]*\|)?([^\]]+)\]\]")
# {{template}} and {{تصنيف:...}}
_TEMPLATE_RE = re.compile(r"\{\{[^}]*\}\}")
# HTML tags
_HTML_TAG_RE = re.compile(r"<[^>]+>")
# Attribution at end of line:  (author)  or  – author
_ATTRIBUTION_RE = re.compile(r"[\(\（]([^)）]+)[\)）]\s*$")
_DASH_ATTRIBUTION_RE = re.compile(r"\s*[-–—]\s*\S.*$")
# Reference style [1]
_REF_RE = re.compile(r"\[\d+\]")
# Any remaining [ or ] chars (unclosed wikilinks)
_BRACKET_RE = re.compile(r"[\[\]]")


def _clean_wikitext(raw: str) -> str:
    """Strip wikitext markup and return plain Arabic text."""
    text = _WIKILINK_RE.sub(r"\1", raw)
    text = _TEMPLATE_RE.sub("", text)
    text = _HTML_TAG_RE.sub("", text)
    text = _REF_RE.sub("", text)
    text = _ATTRIBUTION_RE.sub("", text)
    text = _DASH_ATTRIBUTION_RE.sub("", text)
    text = _BRACKET_RE.sub("", text)
    # Remove Arabic punctuation and any remaining Latin/digit chars
    text = re.sub(r"[.!?,;:؟،؛\"\'«»…*|/\\{}]", "", text)
    text = re.sub(r"[a-zA-Z0-9]", "", text)
    return _WHITESPACE_RE.sub(" ", text).strip()


def _is_valid_proverb(words: list[str]) -> bool:
    """Return True if the word list forms a usable proverb entry."""
    if not (MIN_WORDS <= len(words) <= MAX_WORDS):
        return False
    return all(_is_arabic_word(w) for w in words)


# ─────────────────────────────────────────────────────────────────────────────
# Key generation
# ─────────────────────────────────────────────────────────────────────────────


def _generate_key_pairs(
    words: list[str],
) -> list[tuple[str, str]]:
    """Generate (normalized_key, normalized_suggestion) pairs for a phrase.

    Keys start at 2 words (minimum) to reduce false positives from single-word
    keys, which are too ambiguous across unrelated proverbs.

    For a phrase of N words, produces up to min(N-2, MAX_KEY_WORDS-1) pairs:
        words[0:2]          → words[2]   (smallest key: 2 words)
        words[0:3]          → words[3]
        ...
        words[0:MAX_KEY_WORDS] → words[MAX_KEY_WORDS]

    Args:
        words: Clean Arabic word tokens of the proverb.

    Returns:
        List of (key_string, suggestion_word) pairs, or empty list if the
        phrase has fewer than 3 words (not enough for a 2-word key +
        suggestion).
    """
    pairs: list[tuple[str, str]] = []
    norm_words = [_normalize_word(w) for w in words]
    for i in range(1, min(len(norm_words) - 1, MAX_KEY_WORDS)):
        key = " ".join(norm_words[: i + 1])
        suggestion = norm_words[i + 1]
        if key and suggestion:
            pairs.append((key, suggestion))
    return pairs


# ─────────────────────────────────────────────────────────────────────────────
# HTTP helpers
# ─────────────────────────────────────────────────────────────────────────────


def _fetch_json(url: str, *, retries: int = 3, pause: float = 1.5) -> dict | None:
    """Fetch a URL and return parsed JSON, with simple retry logic."""
    for attempt in range(1, retries + 1):
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=20) as resp:
                raw = resp.read().decode("utf-8")
            return json.loads(raw)  # type: ignore[return-value]
        except (URLError, json.JSONDecodeError) as exc:
            logging.warning(
                "Attempt %d/%d failed for %s: %s", attempt, retries, url, exc
            )
            if attempt < retries:
                time.sleep(pause * attempt)
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Source: Arabic Wikiquote
# ─────────────────────────────────────────────────────────────────────────────

_WIKIQUOTE_API = "https://ar.wikiquote.org/w/api.php"


def _fetch_wikiquote_wikitext(page_title: str) -> str:
    """Return wikitext for a single Wikiquote page."""
    encoded_title = quote(page_title, safe="")
    url = (
        f"{_WIKIQUOTE_API}?action=parse&page={encoded_title}&prop=wikitext&format=json"
    )
    data = _fetch_json(url)
    if not data:
        return ""
    try:
        return data["parse"]["wikitext"]["*"]
    except (KeyError, TypeError):
        return ""


def _parse_wikiquote_page(wikitext: str) -> list[list[str]]:
    """Extract proverbs from Wikiquote wikitext as token lists."""
    proverbs: list[list[str]] = []
    for raw_line in wikitext.splitlines():
        line = raw_line.strip()
        # Only process list items (lines starting with *)
        if not line.startswith("*"):
            continue
        # Skip lines that are just navigation links to other pages
        if line.startswith("* [[") and line.endswith("]]"):
            continue
        line = line.lstrip("* ").strip()
        cleaned = _clean_wikitext(line)
        if not cleaned:
            continue
        words = cleaned.split()
        if _is_valid_proverb(words):
            proverbs.append(words)
    return proverbs


def fetch_wikiquote_proverbs(pages: list[str]) -> list[list[str]]:
    """Fetch and parse proverbs from a list of Arabic Wikiquote pages."""
    all_proverbs: list[list[str]] = []
    for page in pages:
        logging.info("Fetching Wikiquote page: %s", page)
        wikitext = _fetch_wikiquote_wikitext(page)
        if not wikitext:
            logging.warning("No wikitext returned for page: %s", page)
            continue
        page_proverbs = _parse_wikiquote_page(wikitext)
        logging.info("  → found %d proverbs", len(page_proverbs))
        all_proverbs.extend(page_proverbs)
        time.sleep(0.5)  # Wikimedia rate-limit courtesy
    return all_proverbs


# ─────────────────────────────────────────────────────────────────────────────
# Source: Jawaher dataset (HuggingFace datasets-server API)
# ─────────────────────────────────────────────────────────────────────────────


def _fetch_jawaher_batch(offset: int) -> list[dict]:
    """Fetch one page of Jawaher rows from the HuggingFace datasets-server API."""
    url = HF_ROWS_URL.format(offset=offset, length=HF_BATCH)
    data = _fetch_json(url)
    if not data:
        return []
    try:
        return [item["row"] for item in data.get("rows", [])]
    except (KeyError, TypeError):
        return []


def fetch_jawaher_proverbs(total: int = 1000) -> list[list[str]]:
    """Fetch MSA proverbs from the Jawaher dataset via HuggingFace API."""
    all_proverbs: list[list[str]] = []
    offset = 0
    logging.info("Fetching Jawaher dataset from HuggingFace...")
    while offset < total:
        logging.info("  → offset %d", offset)
        rows = _fetch_jawaher_batch(offset)
        if not rows:
            break
        for row in rows:
            variety = str(row.get("Variety", "")).strip()
            if variety not in MSA_VARIETIES:
                continue
            proverb_text = str(row.get("Proverbs", "")).strip()
            if not proverb_text:
                continue
            cleaned = _clean_wikitext(proverb_text)
            words = cleaned.split()
            if _is_valid_proverb(words):
                all_proverbs.append(words)
        offset += HF_BATCH
        time.sleep(0.3)
    logging.info("Jawaher: collected %d MSA proverbs", len(all_proverbs))
    return all_proverbs


# ─────────────────────────────────────────────────────────────────────────────
# Source: Hand-curated famous phrases (Tier 2)
# ─────────────────────────────────────────────────────────────────────────────

# Each entry is a list of words forming a complete famous phrase.
# These are well-known formulaic phrases, religious openings, and
# high-frequency Arabic collocations.
HAND_CURATED_PHRASES: list[list[str]] = [
    # ── بسملة والقرآنية ──────────────────────────────────────────────────────
    "بسم الله الرحمن الرحيم".split(),
    "الحمد لله رب العالمين".split(),
    "الرحمن الرحيم مالك يوم الدين".split(),
    "إياك نعبد وإياك نستعين".split(),
    "اهدنا الصراط المستقيم".split(),
    "صراط الذين أنعمت عليهم".split(),
    "وما توفيقي إلا بالله".split(),
    "ربنا آتنا في الدنيا حسنة".split(),
    "وفي الآخرة حسنة وقنا عذاب النار".split(),
    "ربنا لا تؤاخذنا إن نسينا".split(),
    "سبحان الله وبحمده سبحان الله العظيم".split(),
    "لا إله إلا الله محمد رسول الله".split(),
    "الله أكبر ولله الحمد".split(),
    "لا حول ولا قوة إلا بالله".split(),
    "استغفر الله العظيم وأتوب إليه".split(),
    "صلى الله عليه وسلم".split(),
    "رضي الله عنه وأرضاه".split(),
    "إن شاء الله تعالى".split(),
    "ما شاء الله لا قوة إلا بالله".split(),
    "بارك الله فيك وفي عمرك".split(),
    "جزاك الله خيرا وأحسن إليك".split(),
    "السلام عليكم ورحمة الله وبركاته".split(),
    "وعليكم السلام ورحمة الله وبركاته".split(),
    "أهلا وسهلا ومرحبا بكم".split(),
    "حياكم الله وبياكم".split(),
    "تفضلوا بالدخول والجلوس".split(),
    "اللهم صل على سيدنا محمد".split(),
    "اللهم اغفر لنا ذنوبنا".split(),
    "إنا لله وإنا إليه راجعون".split(),
    "رحمة الله عليه رحمة واسعة".split(),
    # ── تعبيرات يومية رسمية ──────────────────────────────────────────────────
    "في ما يخص موضوع".split(),
    "وفقا لما تقدم".split(),
    "بناء على ما سبق".split(),
    "في ضوء ما سبق ذكره".split(),
    "يتضح مما سبق أن".split(),
    "من المعلوم أن".split(),
    "من الجدير بالذكر أن".split(),
    "تجدر الإشارة إلى أن".split(),
    "لا بد من الإشارة إلى".split(),
    "ولا يفوتنا أن نذكر".split(),
    "خلاصة القول أن".split(),
    "وفي الختام نقول".split(),
    "وبناء على ذلك".split(),
    "وعلى صعيد آخر".split(),
    "وفي السياق ذاته".split(),
    "وتأسيسا على ما سبق".split(),
    "ولا شك في أن".split(),
    "من الضروري التأكيد على".split(),
    "يعتبر هذا الموضوع من أهم".split(),
    "ويمكن القول إن".split(),
    # ── تعبيرات أكاديمية ─────────────────────────────────────────────────────
    "تهدف هذه الدراسة إلى".split(),
    "يتناول هذا البحث".split(),
    "أجرت الدراسة مقارنة بين".split(),
    "توصلت الدراسة إلى نتائج".split(),
    "أثبتت الدراسة أن".split(),
    "وقد خلصت الدراسة إلى".split(),
    "وفي إطار هذا البحث".split(),
    "وقد استنتج الباحث أن".split(),
    "وتشير الدراسات إلى أن".split(),
    "ويرى الباحثون أن".split(),
    "وقد اتفق العلماء على".split(),
    "وذهب بعض العلماء إلى".split(),
    "ويختلف العلماء في هذه المسألة".split(),
    "ومن أبرز نتائج الدراسة".split(),
    "وفي حدود علم الباحث".split(),
    # ── صياغات خطابية ──────────────────────────────────────────────────────
    "أيها السادة والسيدات الكرام".split(),
    "أيها الحضور الكريم".split(),
    "يشرفني أن أتحدث إليكم".split(),
    "يسعدني أن أقدم لكم".split(),
    "أود أن أستهل حديثي بـ".split(),
    "ولا يسعني في هذا المقام".split(),
    "وفي هذه المناسبة الكريمة".split(),
    "وأتوجه بالشكر الجزيل إلى".split(),
    "وأخيرا وليس آخرا".split(),
    "ونتطلع في المستقبل إلى".split(),
    "ونأمل أن يكون لهذا اللقاء".split(),
    "وأدعو الله أن يوفقنا جميعا".split(),
    # ── تعبيرات شائعة ───────────────────────────────────────────────────────
    "في واقع الأمر".split(),
    "من هذا المنطلق".split(),
    "على صعيد آخر".split(),
    "في المقابل".split(),
    "بصرف النظر عن".split(),
    "على الرغم من ذلك".split(),
    "ومن جهة أخرى".split(),
    "وعلى الجانب الآخر".split(),
    "وفيما يتعلق بـ".split(),
    "ومن ثم فإن".split(),
    "وتجدر الإشارة إلى".split(),
    "كما يتضح من".split(),
    "وبما أن".split(),
    "ومن المعروف أن".split(),
    "الأمر الذي يؤدي إلى".split(),
    "مما سبق يتضح أن".split(),
    "وخلاصة القول".split(),
    "وفي نهاية المطاف".split(),
    "وبشكل عام يمكن القول".split(),
]


# ─────────────────────────────────────────────────────────────────────────────
# YAML entry building
# ─────────────────────────────────────────────────────────────────────────────


def _build_cache_entries(
    all_proverbs: list[list[str]],
    *,
    score: float = 1.0,
    limit: int | None = None,
) -> list[dict]:
    """Convert proverb word-lists into YAML-ready cache entries.

    Generates multi-key entries with prefix expansion. Conflicts (same
    normalized key appearing in multiple proverbs) keep the first entry and
    log a warning.

    Args:
        all_proverbs: List of tokenized proverbs.
        score: Confidence score assigned to all entries.
        limit: If set, stop after this many unique keys.

    Returns:
        List of ``{"key": str, "suggestions": [{"word": str, "score": float}]}``
        dicts, sorted alphabetically by key.
    """
    seen_keys: dict[str, str] = {}  # key → suggestion (first wins)
    conflict_count = 0

    for words in all_proverbs:
        for key, suggestion in _generate_key_pairs(words):
            if key in seen_keys:
                if seen_keys[key] != suggestion:
                    conflict_count += 1
                    logging.debug(
                        "Key conflict: '%s' already maps to '%s', ignoring '%s'",
                        key,
                        seen_keys[key],
                        suggestion,
                    )
            else:
                seen_keys[key] = suggestion
                if limit and len(seen_keys) >= limit:
                    break
        if limit and len(seen_keys) >= limit:
            break

    logging.info(
        "Total unique keys: %d | Conflicts skipped: %d",
        len(seen_keys),
        conflict_count,
    )

    entries = [
        {"key": key, "suggestions": [{"word": suggestion, "score": score}]}
        for key, suggestion in sorted(seen_keys.items())
    ]
    return entries


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build NWS static cache YAML files from external sources."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and parse but do NOT write output files.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of unique keys per file (default: unlimited).",
    )
    parser.add_argument(
        "--skip-wikiquote",
        action="store_true",
        help="Skip the Arabic Wikiquote fetch step.",
    )
    parser.add_argument(
        "--skip-jawaher",
        action="store_true",
        help="Skip the Jawaher HuggingFace fetch step.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable DEBUG logging.",
    )
    return parser.parse_args()


def _write_yaml(path: Path, entries: list[dict], *, dry_run: bool) -> None:
    """Write a list of cache entries to a YAML file."""
    if dry_run:
        logging.info("[DRY RUN] Would write %d entries to %s", len(entries), path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.dump(
            entries,
            fh,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
            width=120,
        )
    logging.info("Wrote %d entries to %s", len(entries), path)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────


def main() -> int:
    """Main function of build script."""
    args = _parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    # ── Tier 1: idioms ────────────────────────────────────────────────────────
    idiom_proverbs: list[list[str]] = []

    if not args.skip_wikiquote:
        wq_proverbs = fetch_wikiquote_proverbs(WIKIQUOTE_PAGES)
        logging.info("Wikiquote total: %d proverbs", len(wq_proverbs))
        idiom_proverbs.extend(wq_proverbs)
    else:
        logging.info("Skipping Wikiquote.")

    if not args.skip_jawaher:
        jw_proverbs = fetch_jawaher_proverbs(total=1000)
        logging.info("Jawaher total: %d MSA proverbs", len(jw_proverbs))
        idiom_proverbs.extend(jw_proverbs)
    else:
        logging.info("Skipping Jawaher.")

    # Deduplicate at proverb level (same normalized text from multiple sources)
    seen_texts: set[str] = set()
    deduped_idioms: list[list[str]] = []
    for words in idiom_proverbs:
        fingerprint = " ".join(_normalize_word(w) for w in words)
        if fingerprint not in seen_texts:
            seen_texts.add(fingerprint)
            deduped_idioms.append(words)
    logging.info(
        "Idiom proverbs after deduplication: %d (removed %d duplicates)",
        len(deduped_idioms),
        len(idiom_proverbs) - len(deduped_idioms),
    )

    idiom_entries = _build_cache_entries(deduped_idioms, score=1.0, limit=args.limit)
    _write_yaml(IDIOMS_OUT, idiom_entries, dry_run=args.dry_run)

    # ── Tier 2: phrases ───────────────────────────────────────────────────────
    phrase_entries = _build_cache_entries(
        HAND_CURATED_PHRASES, score=1.0, limit=args.limit
    )
    _write_yaml(PHRASES_OUT, phrase_entries, dry_run=args.dry_run)

    logging.info("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

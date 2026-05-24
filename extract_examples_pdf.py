"""
Search maly_princ_lat.pdf for example sentences matching each vocabulary entry.
Matches the ISV word or inflected forms using stem-prefix heuristics.
Outputs examples_maly_princ.json — empty string where no match found.

Usage:
    py extract_examples_pdf.py
"""

import fitz   # pymupdf
import json
import os
import re
import sys

PDF_PATH   = r"C:\Users\carbon\Documents\Interslavic\maly_princ_lat.pdf"
VOCAB_JS   = os.path.join(os.path.dirname(__file__), "vocab.js")
OUTPUT     = os.path.join(os.path.dirname(__file__), "examples_maly_princ.json")

# ── load PDF text ──────────────────────────────────────────────────────────────

def load_pdf_text(path):
    doc = fitz.open(path)
    pages = []
    for page in doc:
        pages.append(page.get_text())
    return "\n".join(pages)

# ── sentence splitting ─────────────────────────────────────────────────────────

def split_sentences(text):
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Split on sentence-ending punctuation followed by space + capital or end
    parts = re.split(r'(?<=[.!?…])\s+(?=[A-ZÁČÉĚÍÓŠŮÚŽŹ–"«»„""]|$)', text)
    sentences = []
    for s in parts:
        s = s.strip()
        if len(s) > 8:
            sentences.append(s)
    return sentences

# ── vocab loading ──────────────────────────────────────────────────────────────

def load_vocab(path):
    with open(path, encoding="utf-8") as f:
        src = f.read()
    src = re.sub(r"^const VOCAB\s*=\s*", "", src.strip())
    src = re.sub(r";\s*$", "", src)
    return json.loads(src)

# ── stem / search helpers ──────────────────────────────────────────────────────

def normalize(s):
    """Lowercase, strip diacritics-preserving, strip punctuation."""
    return re.sub(r"[^\w]", "", s.lower())

def get_stems(isv_raw):
    """
    Given an ISV field (may contain commas, parens, <sup>, HTML), return a list
    of (stem, min_stem_len) pairs to search for.
    """
    # strip HTML tags including <sup>...</sup>
    clean = re.sub(r"<[^>]+>", "", isv_raw)
    # strip explanatory trailing parens like (kogo? čego?)
    clean = re.sub(r"\s*\([^)]*\?\s*[^)]*\)", "", clean)
    # split on comma and optional-bracket alternatives
    parts = re.split(r"[,/]", clean)
    stems = []
    for part in parts:
        part = part.strip()
        # expand optional parens: (po)zvoniti → pozvoniti, zvoniti
        expanded = expand_optional(part)
        for w in expanded:
            w = re.sub(r"\W", "", w).lower()  # keep letters only, lowercase
            if not w:
                continue
            # stem length: use first N characters
            # short words (≤4): match whole word
            # medium (5-7): first len-1
            # longer: first max(4, len-3)
            L = len(w)
            if L <= 3:
                stem_len = L         # exact
            elif L <= 5:
                stem_len = L - 1
            elif L <= 8:
                stem_len = L - 2
            else:
                stem_len = L - 3
            stems.append((w[:stem_len], stem_len))
    # deduplicate
    seen = set()
    result = []
    for s in stems:
        if s[0] not in seen:
            seen.add(s[0])
            result.append(s)
    return result

def expand_optional(word):
    """Expand (optional) prefixes/suffixes: (po)zvoniti → [pozvoniti, zvoniti]"""
    m = re.match(r"^\(([^)]+)\)(.+)$", word)
    if m:
        return [m.group(1) + m.group(2), m.group(2)]
    m = re.match(r"^(.+)\(([^)]+)\)$", word)
    if m:
        return [m.group(1) + m.group(2), m.group(1)]
    return [word]

# Build a regex pattern for a stem that matches it as a word-start
def stem_pattern(stem):
    escaped = re.escape(stem)
    # match stem at word boundary start (preceded by non-letter or start)
    return re.compile(r"(?<![a-záčéěíóšůúžźćđ])" + escaped, re.IGNORECASE)

# ── main ───────────────────────────────────────────────────────────────────────

def main():
    print("Loading PDF…")
    raw_text = load_pdf_text(PDF_PATH)

    print("Splitting into sentences…")
    sentences = split_sentences(raw_text)
    print(f"  {len(sentences)} sentences found")

    print("Loading vocab…")
    vocab = load_vocab(VOCAB_JS)
    print(f"  {len(vocab)} entries")

    results = {}
    matched = 0
    for entry in vocab:
        num = str(entry["num"])
        isv = entry.get("isv", "").strip()
        if not isv:
            results[num] = ""
            continue

        stems = get_stems(isv)
        if not stems:
            results[num] = ""
            continue

        best = ""
        best_score = -1

        for sentence in sentences:
            score = 0
            for (stem, slen) in stems:
                pat = stem_pattern(stem)
                if pat.search(sentence):
                    # prefer longer stems (more specific match) and shorter sentences
                    score = max(score, slen * 100 - len(sentence))
            if score > best_score:
                best_score = score
                best = sentence

        if best_score > 0:
            results[num] = best.strip()
            matched += 1
        else:
            results[num] = ""

    # sort by numeric key
    results_sorted = {str(k): results[str(k)] for k in sorted(int(k) for k in results)}

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(results_sorted, f, ensure_ascii=False, indent=2)

    print(f"\nDone. {matched}/{len(vocab)} entries matched.")
    print(f"Output: {OUTPUT}")

if __name__ == "__main__":
    main()

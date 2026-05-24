"""
Generate example Interslavic sentences for all vocabulary entries in vocab.js.
Results are saved incrementally to examples.json so the script can be resumed.

Usage:
    py generate_examples.py

Requires ANTHROPIC_API_KEY in the environment (or a .env file).
"""

import json
import os
import re
import sys
import time

import anthropic

# ── paths ──────────────────────────────────────────────────────────────────────
VOCAB_JS   = os.path.join(os.path.dirname(__file__), 'vocab.js')
OUTPUT_JSON = os.path.join(os.path.dirname(__file__), 'examples.json')

# ── tuning ─────────────────────────────────────────────────────────────────────
BATCH_SIZE   = 40    # words per API call
MODEL        = 'claude-haiku-4-5-20251001'
MAX_TOKENS   = 4096

SYSTEM_PROMPT = """\
You are helping build a learning resource for Interslavic (Medžuslovjansky), \
an auxiliary Slavic language designed to be understood by speakers of all Slavic languages.

Your task: for each vocabulary item, write ONE short example sentence in Interslavic \
that clearly illustrates the meaning of the word.

Rules:
- Use only simple, common vocabulary. A beginner should understand the sentence \
  without knowing any word except the target word.
- Sentences should be short (5–10 words ideally).
- The target word (or a grammatically inflected form of it) MUST appear in the sentence.
- Do not add translations or explanations — just the Interslavic sentence.
- Use standard Interslavic orthography (č, š, ž, ě, etc.).
- Output ONLY valid JSON: an object mapping each num (as a string key) to the sentence string.
  Example: {"1": "Da, ja razuměm tebe.", "2": "Ne, to ne jest pravda."}
- No markdown, no code fences, no commentary — raw JSON only.
"""

# ── helpers ────────────────────────────────────────────────────────────────────

def load_vocab():
    with open(VOCAB_JS, encoding='utf-8') as f:
        src = f.read()
    # strip the JS wrapper and parse as JSON
    src = re.sub(r'^const VOCAB\s*=\s*', '', src.strip())
    src = re.sub(r';\s*$', '', src)
    return json.loads(src)


def load_existing():
    if os.path.exists(OUTPUT_JSON):
        with open(OUTPUT_JSON, encoding='utf-8') as f:
            return json.load(f)
    return {}


def save(data):
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def make_user_prompt(batch):
    lines = []
    for w in batch:
        lines.append(f'num={w["num"]}  isv="{w["isv"]}"  en="{w["en"]}"  cat="{w["cat"]}"')
    return "Generate one example sentence for each entry below:\n\n" + "\n".join(lines)


def call_api(client, batch):
    prompt = make_user_prompt(batch)
    resp = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.content[0].text.strip()
    # strip accidental code fences
    text = re.sub(r'^```[a-z]*\n?', '', text)
    text = re.sub(r'\n?```$', '', text)
    return json.loads(text)


# ── main ───────────────────────────────────────────────────────────────────────

def main():
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        sys.exit("Error: ANTHROPIC_API_KEY environment variable not set.")

    client = anthropic.Anthropic(api_key=api_key)
    vocab   = load_vocab()
    results = load_existing()

    already_done = set(str(k) for k in results)
    remaining    = [w for w in vocab if str(w['num']) not in already_done]

    if not remaining:
        print("All entries already generated.")
        return

    total   = len(remaining)
    batches = [remaining[i:i+BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]
    print(f"{total} entries to generate across {len(batches)} batches (model: {MODEL})")

    done = 0
    for i, batch in enumerate(batches):
        nums = [w['num'] for w in batch]
        print(f"  Batch {i+1}/{len(batches)} — nums {nums[0]}..{nums[-1]} ", end='', flush=True)
        try:
            new_entries = call_api(client, batch)
            # normalise keys to strings
            for k, v in new_entries.items():
                results[str(k)] = v
            save(results)
            done += len(new_entries)
            print(f"ok ({len(new_entries)} sentences, {done}/{total} total)")
        except Exception as e:
            print(f"FAILED: {e}")
            print("  Progress saved. Re-run to continue.")
            sys.exit(1)

        if i < len(batches) - 1:
            time.sleep(0.5)   # be gentle with rate limits

    print(f"\nDone. {len(results)} sentences written to {OUTPUT_JSON}")


if __name__ == '__main__':
    main()

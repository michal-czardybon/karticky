# Kartičky — Project Notes for Claude

## What this is

A single-page flashcard PWA for learning Interslavic (Medžuslovjansky).
Files: `karticky.html` (app), `vocab.js` (word data), `categories.js` (category translations).

---

## Vocabulary update workflow

### Source document

`C:\Users\carbon\Documents\Prywatne\ISV\1000 slov — multi.docx`

The document contains tables with vocabulary in multiple languages. Each table has a header row where the first cell is empty and subsequent cells name the language in Interslavic (e.g. `angielsky`, `medžuslovjansky`). Rows start with a sequential number in column 0.

Word categories come from **Heading 2** paragraphs (`w:pStyle w:val="Nagwek2"`) that appear in the document body between tables. The extractor tracks the most recent heading and assigns it as the `cat` field on every entry from the following table.

### Running the extractor

```
py extract_vocab.py
```

Writes to `vocab.js`. Run from any directory — paths are hardcoded in the script.

### Output fields (in order)

`num`, `cat`, `pl`, `cz`, `sk`, `uk`, `ru`, `cr`, `isv`, `en`, `de`, `sv`, `es`, `it`, `ia`

A row is only included if it has a valid ISV column **and** a non-empty English translation.

---

## Known quirks in the source document

### Language header typos in HEADER_MAP

The document contains misspelled column headers that must be mapped:

| Typo in docx | Correct mapping |
|---|---|
| `medžuslvjansky` | `isv` |
| `rosyjsky` | `ru` |
| `italijanksy` | `it` |

Note: `interlingua` maps to `ia` (the column header in the document is the full language name, not an adjective form).

These are already handled in `extract_vocab.py`. If a future update adds a new language column and entries go missing, check whether the header is a new typo variant.

### Column order shifts

When new language columns are added to the document (e.g. Swedish was added between DE and ES), column indices shift. The extractor reads the header row dynamically, so this is handled automatically — **do not hardcode column indices**.

### Warning triangle (⚠ U+26A0)

Some cells contain `⚠` (U+26A0) followed by an optional variation selector (U+FE0F). The extractor strips both:
```python
text = re.sub(r' *\u26a0\ufe0f? *', '', text)
```

### Superscript in ISV column

ISV words sometimes use superscript characters (e.g. `mysliti²`). The extractor wraps superscript runs in `<sup>` tags for the ISV field only. Other language fields receive plain text.

### Deduplication

If the same `num` appears in multiple tables (e.g. repeated entry across sections), only the first occurrence is kept.

---

## Answer matching rules (Vpisyvanje mode)

These rules apply when checking a typed answer against `item.isv`:

1. Strip `<sup>…</sup>` and all HTML tags.
2. Strip **explanatory** parentheticals — space-separated `(…)` at the end, e.g. `vslěd (kogo? čego?)` → `vslěd`. Do this **before** splitting on `,` and `? `.
3. Split on `,` and `? ` to get individual variants.
4. For each variant, expand **optional attached parens** recursively:
   - `(po)zvoniti` → `[pozvoniti, zvoniti]`
   - `izvini(te)` → `[izvinite, izvini]`
5. Normalize each expanded form: remove all punctuation/spaces, lowercase, then apply character substitutions: `ĉ→č`, `ê→ě`, `ŝ→š`.
6. The answer is correct if any normalized expanded form matches the normalized user input.

---

## categories.js

`const CATS` — maps 47 ISV category names (as they appear in `cat` fields of `vocab.js`) to translations in 12 languages: `pl`, `cz`, `sk`, `uk`, `ru`, `cr`, `en`, `de`, `sv`, `es`, `it`, `ia`.

When updating vocabulary that changes category names, update `CATS` accordingly. The `catLabel(cat)` function in `karticky.html` falls back to the raw ISV name if no translation is found.

### Category name to watch

`'Put i srědstva transporta'` → translated as **travel** (not roads): pl: `Podróże i środki transportu`, en: `Travel and transport`, etc.

---

## Persistence

The app saves `karticky_lang` and `karticky_mode` to `localStorage` on every change and restores them on page load.

import zipfile, json, re, sys, io
import xml.etree.ElementTree as ET

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DOCX = r'C:\Users\carbon\Documents\Prywatne\ISV\1000 slov — multi.docx'
OUT  = r'C:\Users\carbon\Documents\Prywatne\ISV\Kartičky\vocab.js'

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

HEADER_MAP = {
    'poljsky':          'pl',
    'češsky':           'cz',
    'slovačsky':        'sk',
    'ukrajinsky':       'uk',
    'rosijsky':         'ru',
    'rosyjsky':         'ru',
    'hrvatsky':         'cr',
    'medžuslovjansky':  'isv',
    'medžuslvjansky':   'isv',
    'angielsky':        'en',
    'němečsky':         'de',
    'špansky':          'es',
    'italijansky':      'it',
    'italijanksy':      'it',
}

def para_style(p):
    pPr = p.find('.//{%s}pPr' % W)
    if pPr is None: return None
    ps = pPr.find('{%s}pStyle' % W)
    return ps.get('{%s}val' % W) if ps is not None else None

def para_text(p):
    return ''.join(t.text or '' for t in p.iter('{%s}t' % W)).strip().replace('\xa0', ' ')

def cell_text(tc, sup_tags=False):
    result = []
    for para in tc.iter('{%s}p' % W):
        for run in para.iter('{%s}r' % W):
            rpr = run.find('{%s}rPr' % W)
            is_sup = False
            if rpr is not None:
                va = rpr.find('{%s}vertAlign' % W)
                if va is not None and va.get('{%s}val' % W) == 'superscript':
                    is_sup = True
            for t in run.iter('{%s}t' % W):
                txt = t.text or ''
                if txt:
                    result.append(('<sup>%s</sup>' % txt) if (sup_tags and is_sup) else txt)
    text = ''.join(result).strip()
    text = re.sub(r' *\u26a0\ufe0f? *', '', text)
    return text

def process_table(tbl, category):
    direct_rows = [ch for ch in tbl if ch.tag == '{%s}tr' % W]
    if not direct_rows:
        return []
    header_cells = [cell_text(tc) for tc in direct_rows[0].findall('{%s}tc' % W)]
    if not header_cells or header_cells[0] != '':
        return []
    col_map = {}
    for i, h in enumerate(header_cells):
        if h in HEADER_MAP:
            col_map[i] = HEADER_MAP[h]
    if 'isv' not in col_map.values():
        return []
    en_col = next((i for i, f in col_map.items() if f == 'en'), None)
    if en_col is None:
        return []

    entries = []
    for tr in direct_rows[1:]:
        cells_plain = [cell_text(tc, False) for tc in tr.findall('{%s}tc' % W)]
        cells_sup   = [cell_text(tc, True)  for tc in tr.findall('{%s}tc' % W)]
        if not cells_plain: continue
        num = cells_plain[0]
        if not re.match(r'^\d+$', num): continue
        en_val = cells_plain[en_col] if en_col < len(cells_plain) else ''
        if not en_val or en_val.strip() in ('-', '–', ''): continue
        entry = {'num': int(num), 'cat': category}
        for col_i, field in col_map.items():
            if col_i < len(cells_sup):
                entry[field] = cells_sup[col_i] if field == 'isv' else cells_plain[col_i]
        entries.append(entry)
    return entries

with zipfile.ZipFile(DOCX) as z:
    xml_bytes = z.read('word/document.xml')

root = ET.fromstring(xml_bytes)
body = root.find('{%s}body' % W)

rows_out = []
current_category = ''

for child in body:
    tag = child.tag
    if tag == '{%s}p' % W:
        style = para_style(child)
        if style == 'Nagwek2':
            current_category = para_text(child)
    elif tag == '{%s}tbl' % W:
        rows_out.extend(process_table(child, current_category))

rows_out.sort(key=lambda r: r['num'])
seen = set()
deduped = []
for r in rows_out:
    if r['num'] not in seen:
        seen.add(r['num'])
        deduped.append(r)
rows_out = deduped

print(f'Extracted {len(rows_out)} entries', file=sys.stderr)

FIELDS = ['num','cat','pl','cz','sk','uk','ru','cr','isv','en','de','es','it']

lines = ['const VOCAB = [']
for i, entry in enumerate(rows_out):
    ordered = {f: entry.get(f, '') for f in FIELDS}
    comma = ',' if i < len(rows_out) - 1 else ''
    lines.append('  ' + json.dumps(ordered, ensure_ascii=False) + comma)
lines.append('];')

with open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')

print(f'Written to {OUT}', file=sys.stderr)

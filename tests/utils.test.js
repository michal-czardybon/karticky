const { normalize, splitTopLevel, expandOptionalParens } = require('../utils.js');

// ─── normalize ───────────────────────────────────────────────────────────────

describe('normalize', () => {
  test('lowercases input', () => {
    expect(normalize('Ahoj')).toBe('ahoj');
  });

  test('strips spaces and punctuation', () => {
    expect(normalize('ne znam, ne znaju')).toBe('neznamneznaju');
  });

  test('strips HTML tags', () => {
    expect(normalize('<b>mysliti</b>')).toBe('mysliti');
  });

  test('strips superscript tags and their content', () => {
    expect(normalize('mysliti<sup>2</sup>')).toBe('mysliti');
  });

  test('allows cz as substitute for č', () => {
    expect(normalize('czlovek')).toBe('človek');
  });

  test('allows sz as substitute for š', () => {
    expect(normalize('szum')).toBe('šum');
  });

  test('allows ć as substitute for č', () => {
    expect(normalize('ćlovek')).toBe('človek');
  });

  test('allows ê/è/é as substitute for ě', () => {
    expect(normalize('věriti')).toBe('věriti');
    expect(normalize('vêriti')).toBe('věriti');
    expect(normalize('vèriti')).toBe('věriti');
    expect(normalize('vériti')).toBe('věriti');
  });

  test('allows ś as substitute for š', () => {
    expect(normalize('śum')).toBe('šum');
  });

  test('strips bracket characters but not their content', () => {
    // Note: space-separated explanatory parens like " (komu?)" are stripped
    // *before* normalize() is called, in the answer-checking pipeline.
    // normalize() itself only strips the bracket/punctuation characters.
    expect(normalize('zvoniti (komu?)')).toBe('zvonitikomu');
  });
});

// ─── splitTopLevel ───────────────────────────────────────────────────────────

describe('splitTopLevel', () => {
  test('splits on comma', () => {
    expect(splitTopLevel('ne znam, ne znaju')).toEqual(['ne znam', ' ne znaju']);
  });

  test('splits on "? " separator', () => {
    expect(splitTopLevel('kto? čto?')).toEqual(['kto?', 'čto?']);
  });

  test('does not split on comma inside parentheses', () => {
    expect(splitTopLevel('zvoniti (komu?, čemu?)')).toEqual(['zvoniti (komu?, čemu?)']);
  });

  test('handles single entry with no separators', () => {
    expect(splitTopLevel('da')).toEqual(['da']);
  });

  test('handles multiple comma-separated variants', () => {
    expect(splitTopLevel('a, b, c')).toEqual(['a', ' b', ' c']);
  });
});

// ─── expandOptionalParens ────────────────────────────────────────────────────

describe('expandOptionalParens', () => {
  test('expands prefix parens: (po)zvoniti → [pozvoniti, zvoniti]', () => {
    expect(expandOptionalParens('(po)zvoniti')).toEqual(['pozvoniti', 'zvoniti']);
  });

  test('expands suffix parens: izvini(te) → [izvinite, izvini]', () => {
    expect(expandOptionalParens('izvini(te)')).toEqual(['izvinite', 'izvini']);
  });

  test('does not expand space-separated parens (explanatory)', () => {
    expect(expandOptionalParens('zvoniti (komu?)')).toEqual(['zvoniti (komu?)']);
  });

  test('handles word with no parens', () => {
    expect(expandOptionalParens('da')).toEqual(['da']);
  });

  test('expands multiple optional parens recursively', () => {
    const result = expandOptionalParens('(s)pisati(sja)');
    expect(result).toContain('spisatisja');
    expect(result).toContain('spisati');
    expect(result).toContain('pisatisja');
    expect(result).toContain('pisati');
    expect(result.length).toBe(4);
  });

  test('deduplicates identical expansions', () => {
    const result = expandOptionalParens('(a)bc');
    expect(result).toEqual(['abc', 'bc']);
    expect(new Set(result).size).toBe(result.length);
  });
});

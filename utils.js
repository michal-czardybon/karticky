function normalize(s) {
  return s.replace(/<sup>[^<]*<\/sup>/gi, '')  // remove superscripts (incl. content)
           .replace(/<[^>]*>/g, '')              // strip remaining HTML tags
           .replace(/[\s,.!?;:()\[\]{}]/g, '')  // strip punctuation/spaces/brackets
           .toLowerCase()
           .replace(/cz/g, 'č')                 // allow cz as substitute for č
           .replace(/sz/g, 'š')                 // allow sz as substitute for š
           .replace(/ĉ/g, 'č')                  // allow ĉ as substitute for č
           .replace(/ć/g, 'č')                  // allow ć as substitute for č
           .replace(/[êèé]/g, 'ě')              // allow ê/è/é as substitute for ě
           .replace(/ŝ/g, 'š')                  // allow ŝ as substitute for š
           .replace(/ś/g, 'š');                 // allow ś as substitute for š
}

// Split on ',' and '? ' only at top level (not inside parentheses)
function splitTopLevel(s) {
  var parts = [], depth = 0, start = 0;
  for (var i = 0; i < s.length; i++) {
    if (s[i] === '(') depth++;
    else if (s[i] === ')') depth--;
    else if (depth === 0) {
      if (s[i] === ',') { parts.push(s.substring(start, i)); start = i + 1; }
      else if (s[i] === '?' && i + 1 < s.length && s[i + 1] === ' ') {
        parts.push(s.substring(start, i + 1)); start = i + 2; i++;
      }
    }
  }
  parts.push(s.substring(start));
  return parts;
}

// Expand attached parens into two variants: "(po)zvoniti" → ["pozvoniti","zvoniti"]
function expandOptionalParens(s) {
  for (var i = 0; i < s.length; i++) {
    if (s[i] === '(' && (i === 0 || s[i - 1] !== ' ')) {
      var close = s.indexOf(')', i);
      if (close < 0) break;
      var before = s.substring(0, i);
      var inside = s.substring(i + 1, close);
      var after  = s.substring(close + 1);
      var result = [];
      expandOptionalParens(before + inside + after).forEach(function(v) { result.push(v); });
      expandOptionalParens(before + after).forEach(function(v) { if (result.indexOf(v) < 0) result.push(v); });
      return result;
    }
  }
  return [s];
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { normalize, splitTopLevel, expandOptionalParens };
}

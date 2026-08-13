// Lightweight parser/validator for matrix/vector cell inputs.
// Accepts:
//  - plain numbers: 123, -12.34
//  - pi or π (exact token, case-insensitive)
//  - sqrt(x) or √x where x is a supported part
//  - fractions a/b where a and b are supported parts
//  - power x^y where x and y are supported parts
// Disallows full expressions combining operators like 2pi (implicit multiplication), 1+2, 2*3 etc.

export type ParseResult = {
  valid: boolean;
  value?: number; // computed numeric value when valid
  normalized?: string; // optional normalized string representation
  error?: string;
};

function isNumericToken(s: string) {
  return /^-?\d+(?:\.\d+)?$/.test(s);
}

function stripSpaces(s: string) {
  return s.replace(/\s+/g, '');
}

// Parse a part that cannot be an expression with + or * etc.
function parsePart(s: string): ParseResult {
  const raw = s.trim();
  if (raw === '') return { valid: false, error: 'Empty' };

  // allow leading unary -
  let neg = false;
  let token = raw;
  if (token.startsWith('-')) {
    neg = true;
    token = token.slice(1);
  }

  token = stripSpaces(token);

  // plain number
  if (/^\d+(?:\.\d+)?$/.test(token)) {
    const num = parseFloat(token);
    return { valid: true, value: neg ? -num : num, normalized: (neg ? '-' : '') + String(num) };
  }

  // exact pi token
  if (/^(pi|π)$/i.test(token)) {
    const num = Math.PI;
    return { valid: true, value: neg ? -num : num, normalized: (neg ? '-' : '') + 'pi' };
  }

  // sqrt(...) or √...
  const sqrtMatch = token.match(/^sqrt\((.+)\)$/i) || token.match(/^√(.+)$/);
  if (sqrtMatch) {
    const inner = sqrtMatch[1];
    const innerParsed = parsePart(inner);
    if (!innerParsed.valid) return { valid: false, error: 'Invalid sqrt argument' };
    if (innerParsed.value! < 0) return { valid: false, error: 'Sqrt of negative' };
    const num = Math.sqrt(innerParsed.value!);
    return { valid: true, value: neg ? -num : num, normalized: (neg ? '-' : '') + `sqrt(${innerParsed.normalized})` };
  }

  // fraction a/b
  const fracMatch = token.match(/^(.+)\/(.+)$/);
  if (fracMatch) {
    const a = fracMatch[1];
    const b = fracMatch[2];
    // disallow nested full expressions; parse parts
    const pa = parsePart(a);
    const pb = parsePart(b);
    if (!pa.valid || !pb.valid) return { valid: false, error: 'Invalid fraction parts' };
    if (pb.value === 0) return { valid: false, error: 'Division by zero' };
    const num = pa.value! / pb.value!;
    return { valid: true, value: neg ? -num : num, normalized: (neg ? '-' : '') + `${pa.normalized}/${pb.normalized}` };
  }

  // power x^y
  const powMatch = token.match(/^(.+)\^(?:\(?(.+)\)?)$/);
  if (powMatch) {
    const base = powMatch[1];
    const exp = powMatch[2];
    const pb = parsePart(base);
    const pe = parsePart(exp);
    if (!pb.valid || !pe.valid) return { valid: false, error: 'Invalid power parts' };
    const num = Math.pow(pb.value!, pe.value!);
    return { valid: true, value: neg ? -num : num, normalized: (neg ? '-' : '') + `${pb.normalized}^${pe.normalized}` };
  }

  return { valid: false, error: 'Unsupported token or contains operators' };
}

export function parseCellInput(rawInput: string): ParseResult {
  if (rawInput == null) return { valid: false, error: 'No input' };
  const s = String(rawInput).trim();
  if (s === '') return { valid: true, value: 0, normalized: '0' };

  // Quick rejection: disallow letters except pi/sqrt
  const allowedWords = ['pi', 'π', 'sqrt', '√'];
  // if letters present, ensure they appear only as allowed tokens
  const letters = s.match(/[A-Za-zπ√]/g);
  if (letters) {
    const joined = letters.join('').toLowerCase();
    // crude check: if there's any alphabetic character not in an allowed token sequence, be more strict by attempting parsePart
    // we'll proceed to parsePart which will handle acceptable tokens and reject others
  }

  // disallow implicit multiplication like 2pi or pi2 or )(
  if (/\d+(pi|π)|(?:pi|π)\d+/.test(s.replace(/\s+/g, ''))) {
    return { valid: false, error: 'Implicit multiplication like "2pi" is not allowed; use a single token like "pi" or a numeric value' };
  }

  // only allow a single top-level part: no plus/minus/operators in the middle (except fraction and power which are handled)
  if (/[+*]/.test(s)) {
    return { valid: false, error: 'Operators like + or * are not allowed inside a cell' };
  }

  // use parsePart to accept the allowed patterns
  const result = parsePart(s);
  if (!result.valid) return result;
  // normalization: use numeric string for numbers, use 'pi' for pi, and keep sqrt/fraction/power normalized form
  return { valid: true, value: result.value, normalized: result.normalized };
}

export default parseCellInput;

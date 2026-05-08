"""
add_a11y.py
===========
Adds accessibilityRole="button" + accessibilityLabel to every <TouchableOpacity
that is missing them, by extracting the label from the closest <Text> child.

Also adds accessibilityLabel to <TextInput / <InputField from placeholder.
"""

import re
import os
import glob

SRC = os.path.join(os.path.dirname(__file__), '..', 'facesyma_mobile', 'src')
files = sorted(
    glob.glob(os.path.join(SRC, 'screens', '*.tsx')) +
    glob.glob(os.path.join(SRC, 'components', '*.tsx'))
)

EMOJI_RE = re.compile(
    r'^[\U0001F300-\U0001FFFF\U00002600-\U000027FF\U0000FE00-\U0000FEFF'
    r'\U00002000-\U0000206F\s→←↑↓•·]+$'
)

def is_emoji_only(text: str) -> bool:
    return bool(EMOJI_RE.match(text.strip()))


def humanize(name: str) -> str:
    name = re.sub(r'^(handle|on|press|do|goto|navigate|go|open|close|toggle|show|hide)', '', name, flags=re.IGNORECASE)
    name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name).strip()
    return name.title() if name else ''


T_KEY_RE  = re.compile(r"\{t\('([^']+)',\s*\w+\)\}")
T_KEY2_RE = re.compile(r'\{t\("([^"]+)",\s*\w+\)\}')


def extract_label_from_text_lines(lines_after, max_look=20):
    found_text_open = False
    for line in lines_after[:max_look]:
        stripped = line.strip()
        if re.search(r'<Text[\s>/]', stripped) or stripped == '<Text>':
            found_text_open = True
            inline = re.search(r'<Text[^>]*>(.+?)</Text>', stripped)
            if inline:
                raw = inline.group(1).strip()
                if is_emoji_only(raw):
                    found_text_open = False
                    continue
                m = T_KEY_RE.search(raw)
                if m:
                    return "t('" + m.group(1) + "', lang)"
                m = T_KEY2_RE.search(raw)
                if m:
                    return 't("' + m.group(1) + '", lang)'
                if raw.startswith('{') and raw.endswith('}'):
                    inner = raw[1:-1].strip()
                    if re.match(r'^[a-zA-Z_][a-zA-Z0-9_.]*$', inner):
                        return inner
                clean = re.sub(r'[{}]', '', raw).strip()
                if clean and not is_emoji_only(clean) and len(clean) < 60:
                    return repr(clean)
                found_text_open = False
        elif found_text_open:
            raw = stripped
            if not raw or raw.startswith('<') or raw.startswith('//'):
                found_text_open = False
                continue
            if is_emoji_only(raw):
                found_text_open = False
                continue
            m = T_KEY_RE.search(raw)
            if m:
                return "t('" + m.group(1) + "', lang)"
            m = T_KEY2_RE.search(raw)
            if m:
                return 't("' + m.group(1) + '", lang)'
            clean = re.sub(r'[{}\'"\\]', '', raw).strip()
            if clean and not is_emoji_only(clean) and len(clean) < 60 and not clean.startswith('style'):
                return repr(clean)
            found_text_open = False
    return None


def extract_label_from_onpress(text):
    m = re.search(r'onPress=\{([a-zA-Z_][a-zA-Z0-9_.]*)\}', text)
    if m:
        name = m.group(1).split('.')[-1]
        h = humanize(name)
        if h and h.lower() not in ('', 'button', 's'):
            return repr(h)
    return None


def extract_label_from_style(text):
    m = re.search(r'style=\{\[?styles\.([a-zA-Z_][a-zA-Z0-9_]*)', text)
    if m:
        name = re.sub(r'(Btn|Button|Card|Wrap|Row|Box|Container|Banner|Item|Touch)$', '', m.group(1), flags=re.IGNORECASE)
        h = humanize(name)
        if h and h.lower() not in ('', 'button'):
            return repr(h)
    return None


def build_label_attr(label_expr, indent):
    if not label_expr:
        label_expr = "'button'"
    # Wrap in {} if it's a function call or variable; otherwise it's already repr'd
    if label_expr.startswith("t(") or (not label_expr.startswith("'") and not label_expr.startswith('"')):
        return indent + '  accessibilityLabel={' + label_expr + '}'
    else:
        return indent + '  accessibilityLabel=' + label_expr


stats = {'files': 0, 'buttons': 0, 'inputs': 0}

for fpath in files:
    with open(fpath, encoding='utf-8') as f:
        content = f.read()

    original = content
    lines = content.split('\n')
    out = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # ── TouchableOpacity ─────────────────────────────────────────────────
        if '<TouchableOpacity' in stripped:
            has_role  = 'accessibilityRole'  in line
            has_label = 'accessibilityLabel' in line

            if has_role and has_label:
                out.append(line)
                i += 1
                continue

            # Collect the full opening element
            elem_lines = [line]
            j = i + 1
            # If line doesn't end the element opening, keep collecting
            first_no_comment = stripped.split('//')[0]
            opens = first_no_comment.count('<') - first_no_comment.count('</')
            closes_self = '/>' in first_no_comment
            angle_open = '>' in first_no_comment and not '/>' in first_no_comment

            if not angle_open and not closes_self:
                while j < len(lines):
                    nxt = lines[j].strip()
                    nxt_nc = nxt.split('//')[0]
                    elem_lines.append(lines[j])
                    j += 1
                    if '>' in nxt_nc:
                        break

            full = '\n'.join(elem_lines)

            if 'accessibilityRole' in full and 'accessibilityLabel' in full:
                out.extend(elem_lines)
                i = j if j > i + 1 else i + 1
                continue

            # Determine label
            lines_after = lines[j:] if j > i + 1 else lines[i + 1:]
            label = (
                extract_label_from_text_lines(lines_after) or
                extract_label_from_onpress(full) or
                extract_label_from_style(full)
            )

            indent = ' ' * (len(lines[i]) - len(lines[i].lstrip()))
            new_props = []
            if 'accessibilityRole' not in full:
                new_props.append(indent + '  accessibilityRole="button"')
            if 'accessibilityLabel' not in full:
                new_props.append(build_label_attr(label, indent))

            # Insert new props: append after the first element line
            result_lines = elem_lines[:]
            if len(result_lines) == 1:
                first = result_lines[0]
                # Insert props before the closing > or />
                close = '/>' if first.rstrip().endswith('/>') else '>'
                base = first.rstrip()
                if base.endswith(close):
                    base = base[:-len(close)].rstrip()
                props_str = '\n'.join(new_props)
                result_lines[0] = base + '\n' + props_str + '\n' + indent + close
            else:
                # Multi-line: insert after the first line
                result_lines[1:1] = ['\n'.join(new_props)]

            out.extend(result_lines)
            i = j if j > i + 1 else i + 1
            stats['buttons'] += 1
            continue

        # ── TextInput / InputField: label from placeholder ────────────────
        if re.search(r'<(InputField|TextInput)\b', stripped) and 'accessibilityLabel' not in stripped:
            ph = re.search(r"placeholder=\{t\(['\"]([^'\"]+)['\"],", stripped)
            if not ph:
                ph = re.search(r"placeholder=['\"]([^'\"]+)['\"]", stripped)
            if ph:
                indent = ' ' * (len(line) - len(line.lstrip()))
                val = ph.group(1)
                if '.' in val and not ' ' in val:
                    label_expr = "t('" + val + "', lang)"
                    label_attr = indent + '  accessibilityLabel={' + label_expr + '}'
                else:
                    label_attr = indent + '  accessibilityLabel=' + repr(val)

                close = '/>' if line.rstrip().endswith('/>') else '>'
                base = line.rstrip()
                if base.endswith(close):
                    base = base[:-len(close)].rstrip()
                new_line = base + '\n' + label_attr + '\n' + indent + close
                out.append(new_line)
                i += 1
                stats['inputs'] += 1
                continue

        out.append(line)
        i += 1

    new_content = '\n'.join(out)
    if new_content != original:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        stats['files'] += 1

print(f"Files modified : {stats['files']}")
print(f"Buttons fixed  : {stats['buttons']}")
print(f"Inputs fixed   : {stats['inputs']}")

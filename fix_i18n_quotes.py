"""Fix unescaped apostrophes in single-quoted i18n.ts values."""
import re

I18N_PATH = r'facesyma_mobile\src\utils\i18n.ts'

with open(I18N_PATH, 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixes = 0
new_lines = []
for i, line in enumerate(lines, 1):
    # Only process key: value lines
    m = re.match(r"^(\s*'[^']+'\s*:\s*')(.*)',(\s*)$", line)
    if m:
        prefix = m.group(1)    # everything up to and including opening quote
        value = m.group(2)     # the raw value content
        suffix = m.group(3)    # trailing whitespace

        # Find unescaped single quotes in value
        result = []
        j = 0
        had_problem = False
        while j < len(value):
            ch = value[j]
            if ch == '\\' and j + 1 < len(value):
                # escaped char — keep as-is
                result.append(ch)
                result.append(value[j+1])
                j += 2
                continue
            if ch == "'":
                # unescaped apostrophe — escape it
                result.append("\\'")
                had_problem = True
                j += 1
                continue
            result.append(ch)
            j += 1

        if had_problem:
            new_value = ''.join(result)
            new_line = f"{prefix}{new_value}',{suffix}"
            # Verify the fix makes sense
            if new_line != line:
                fixes += 1
                print(f"  L{i}: fixed unescaped apostrophe")
            new_lines.append(new_line)
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

with open(I18N_PATH, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f'\nDone: {fixes} lines fixed')

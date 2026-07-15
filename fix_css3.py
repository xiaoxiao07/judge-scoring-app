# -*- coding: utf-8 -*-
"""Reliable CSS fix - use anchored string operations"""
import sys

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# ===== Fix 1: Insert additional popover CSS after the existing popover section =====
# Find "}\n    /* === radio" which is the boundary between popover and radio sections
# In the file, \n is literal backslash-n (2 chars)
boundary = '}\\n    /* === radio \\u9009\\u94ae === */'
pos = text.find(boundary)
if pos < 0:
    print("FAIL: Could not find popover/radio boundary!")
    # Debug
    radio = '\\u9009\\u94ae === */'
    p2 = text.find(radio)
    if p2 >= 0:
        print(f"Found radio comment at {p2}, context: {repr(text[p2-40:p2+20])}")
    sys.exit(1)

print(f"Found boundary at {pos}")

insert_text = ('}\\n    /* \\u4e0b\\u62c9\\u83dc\\u5355\\u9009\\u9879 - '
    '\\u5185\\u5c42\\u5bb9\\u5668\\u5f3a\\u5316 */\\n'
    '    div[data-baseweb=\\"popover\\"] {\\n'
    '        background-color: #FFFFFF !important;\\n'
    '        border: 1px solid #c0c0c0 !important;\\n'
    '    }\\n'
    '    div[data-baseweb=\\"popover\\"] ul,\\n'
    '    div[data-baseweb=\\"popover\\"] li,\\n'
    '    div[data-baseweb=\\"popover\\"] div[role=\\"option\\"],\\n'
    '    div[data-baseweb=\\"popover\\"] span {\\n'
    '        background: #FFFFFF !important;\\n'
    '        color: #1a1a1a !important;\\n'
    '    }\\n'
    '    div[data-baseweb=\\"popover\\"] li[role=\\"option\\"]:hover,\\n'
    '    div[data-baseweb=\\"popover\\"] div[role=\\"option\\"]:hover {\\n'
    '        background: #e3ecfa !important;\\n'
    '        color: #1a1a1a !important;\\n'
    '    }\\n    /* === radio \\u9009\\u94ae === */')

text = text.replace(boundary, insert_text)
print("OK: Inserted popover inner container selectors")

# ===== Fix 2: Help icon =====
# Find "/* help \\u56fe\\u6807 */"
help_comment = '/* help \\u56fe\\u6807 */'
pos = text.find(help_comment)
if pos < 0:
    print("FAIL: Could not find help comment!")
    sys.exit(1)

print(f"Found help comment at {pos}")

# The rule starts with 4 spaces before /* help...
rule_start = pos - 4  # "    /* help..."
# Verify
assert text[rule_start:rule_start+4] == '    ', f"Expected 4 spaces before help comment, got {repr(text[rule_start:rule_start+20])}"

# Find the closing } of this rule (3rd } after position pos)
c1 = text.find('}', pos)
c2 = text.find('}', c1 + 1)
c3 = text.find('}', c2 + 1)
print(f"Closing braces at {c1}, {c2}, {c3}")

# Verify this is actually the help icon rule by checking what follows
rule_end = c3 + 1
print(f"Rule end char: {repr(text[rule_end-5:rule_end+5])}")

old_section = text[rule_start:rule_end]
print(f"Old section ({len(old_section)} chars): {repr(old_section[:60])}...")

if 'stTooltipIcon' not in old_section:
    print("WARNING: Old section doesn't contain stTooltipIcon!")

new_section = ('    /* help \\u56fe\\u6807 - \\u84dd\\u8272\\u9ad8\\u4eae */\\n'
    '    .stTooltipIcon, .stTooltipIcon svg,\\n'
    '    [data-testid=\\"stTooltipIcon\\"],\\n'
    '    [data-testid=\\"stTooltipIcon\\"] svg {\\n'
    '        fill: #4472C4 !important;\\n'
    '        color: #4472C4 !important;\\n'
    '        opacity: 1 !important;\\n'
    '        background: transparent !important;\\n'
    '    }')

text = text[:rule_start] + new_section + text[rule_end:]
print(f"OK: Updated help icon section ({len(new_section)} chars)")

# Write back
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("\nDONE: File saved!")

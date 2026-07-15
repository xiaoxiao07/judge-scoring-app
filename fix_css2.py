# -*- coding: utf-8 -*-
"""Fix CSS - read file and do precise replacements based on anchored positions"""
import sys

with open('app.py', 'rb') as f:
    raw = f.read()

# ===== Fix 1: Insert after popover section =====
# Find the radio section which comes right after the popover section
# Search for: \n    /* === radio
radio = b'\\n    /* === radio \\u9009\\u94ae === */'
radio_pos = raw.find(radio)
if radio_pos < 0:
    print("FAIL: Could not find radio section!")
    sys.exit(1)

print(f"Radio section found at {radio_pos}")

# The content to insert BEFORE the radio section
# Build it with \n as literal backslash-n sequences
insert = b'\\n    /* \\u4e0b\\u62c9\\u83dc\\u5355\\u9009\\u9879 - \\u5185\\u5c42\\u5bb9\\u5668\\u5f3a\\u5316 */\\n    div[data-baseweb=\\"popover\\"] {\\n        background-color: #FFFFFF !important;\\n        border: 1px solid #c0c0c0 !important;\\n    }\\n    div[data-baseweb=\\"popover\\"] ul,\\n    div[data-baseweb=\\"popover\\"] li,\\n    div[data-baseweb=\\"popover\\"] div[role=\\"option\\"],\\n    div[data-baseweb=\\"popover\\"] span {\\n        background: #FFFFFF !important;\\n        color: #1a1a1a !important;\\n    }\\n    div[data-baseweb=\\"popover\\"] li[role=\\"option\\"]:hover,\\n    div[data-baseweb=\\"popover\\"] div[role=\\"option\\"]:hover {\\n        background: #e3ecfa !important;\\n        color: #1a1a1a !important;\\n    }'

# Insert at radio_pos (before the radio section)
raw = raw[:radio_pos] + insert + raw[radio_pos:]
print(f"OK: Inserted popover inner container selectors (inserted at {radio_pos})")

# ===== Fix 2: Help icon =====
# Find: /* help 图标 */
help_comment = b'/* help \\u56fe\\u6807 */'
help_pos = raw.find(help_comment)
if help_pos < 0:
    print("FAIL: Could not find help comment!")
    sys.exit(1)

print(f"Help comment found at {help_pos}")

# Find the closing brace of this rule (the 3rd } after the comment)
c1 = raw.find(b'}', help_pos)
c2 = raw.find(b'}', c1 + 1)
c3 = raw.find(b'}', c2 + 1)
print(f"Closing braces at {c1}, {c2}, {c3}")

# Go back to find start of line (before the 4-space indent)
# The rule starts with "    /* help..."
line_start = help_pos
while line_start > 0 and raw[line_start-1:line_start] != b'\\n':
    line_start -= 1
# Now line_start is at the position right after the \n, so the indent starts here

print(f"Rule starts at {line_start}: {repr(raw[line_start:line_start+20])}")
print(f"Rule ends at {c3+1}: {repr(raw[c3-10:c3+3])}")

old_section = raw[line_start:c3+1]
print(f"Old section ({len(old_section)} bytes)")

# Build replacement with EXACT same format (correctly escaped)
new_section = b'    /* help \\u56fe\\u6807 - \\u84dd\\u8272\\u9ad8\\u4eae */\\n    .stTooltipIcon, .stTooltipIcon svg,\\n    [data-testid=\\"stTooltipIcon\\"],\\n    [data-testid=\\"stTooltipIcon\\"] svg {\\n        fill: #4472C4 !important;\\n        color: #4472C4 !important;\\n        opacity: 1 !important;\\n        background: transparent !important;\\n    }'

raw = raw[:line_start] + new_section + raw[c3+1:]
print(f"OK: Help icon section updated ({len(new_section)} bytes)")

# Write back
with open('app.py', 'wb') as f:
    f.write(raw)
print("\nDONE: File saved!")

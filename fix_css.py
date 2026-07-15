# -*- coding: utf-8 -*-
"""Fix selectbox dropdown and tooltip icon CSS"""
import sys

with open('C:/Users/lx/Desktop/judge-scoring-app/app.py', 'rb') as f:
    raw = f.read()

# ===== Fix 1: Selectbox popover =====
# Find the comment position
idx = raw.find(b'\\u4e0b\\u62c9\\u83dc\\u5355\\u5f39\\u51fa */')
assert idx >= 0, "Popover comment not found!"

# Go back to find the start of this CSS block (4 spaces + /*)
start = idx
while start > 0 and raw[start-1:start] != b'\n':
    start -= 1
# Now start is at the newline before the comment line

old_end = raw.find(b'\\n    /* === radio ', idx)
if old_end < 0:
    old_end = raw.find(b'\\n    /* === radio', idx)
assert old_end >= 0, "Could not find end of popover section"

# Extract the old section (after newline to before the next section)
old_section = raw[start+1:old_end]
print(f"Old popover section ({len(old_section)} bytes):")
print(repr(old_section[:100]))
print("...")
print(repr(old_section[-100:]))

# Build new section
new_section = b'    /* \\u4e0b\\u62c9\\u83dc\\u5355\\u5f39\\u51fa */\\n    ul[role=\\"listbox\\"], li[role=\\"option\\"],\\n    div[data-baseweb=\\"popover\\"], div[data-baseweb=\\"popover\\"] *,\\n    div[data-testid=\\"stSelectbox\\"] div[role=\\"listbox\\"],\\n    div[data-testid=\\"stSelectbox\\"] li[role=\\"option\\"] {\\n        background: #FFFFFF !important;\\n        color: #1a1a1a !important;\\n    }\\n    /* \\u4e0b\\u62c9\\u83dc\\u5355\\u9009\\u9879 - \\u5185\\u5c42\\u5bb9\\u5668\\u5f3a\\u5316 */\\n    div[data-baseweb=\\"popover\\"] {\\n        background-color: #FFFFFF !important;\\n        border: 1px solid #c0c0c0 !important;\\n    }\\n    div[data-baseweb=\\"popover\\"] ul,\\n    div[data-baseweb=\\"popover\\"] li,\\n    div[data-baseweb=\\"popover\\"] div[role=\\"option\\"],\\n    div[data-baseweb=\\"popover\\"] span {\\n        background: #FFFFFF !important;\\n        color: #1a1a1a !important;\\n    }\\n    div[data-baseweb=\\"popover\\"] li[role=\\"option\\"]:hover,\\n    div[data-baseweb=\\"popover\\"] div[role=\\"option\\"]:hover {\\n        background: #e3ecfa !important;\\n        color: #1a1a1a !important;\\n    }\\n    li[role=\\"option\\"]:hover, div[role=\\"option\\"]:hover,\\n    li[role=\\"option\\"][aria-selected=\\"true\\"] {\\n        background: #e3ecfa !important;\\n        color: #1a1a1a !important;\\n    }\\n'

print(f"\\nNew popover section ({len(new_section)} bytes)")
assert old_section != new_section, "Old and new are the same!"

raw = raw[:start+1] + new_section + raw[old_end:]

print("Popover section replaced successfully!")

# ===== Fix 2: Help icon =====
idx2 = raw.find(b'/* help \\u56fe')
assert idx2 >= 0, "Help icon comment not found!"

# Find the full rule - from start of line to closing }
start2 = raw.rfind(b'\\n', 0, idx2) + 1  # start of this line
end2 = raw.find(b'}', idx2)  # first closing brace of the rule
# The rule has 3 properties (fill, color, opacity) + closing }
# Find the 3rd closing brace by counting
for _ in range(3):
    end2 = raw.find(b'}', end2 + 1)

# Show help icon section
old_help = raw[start2:end2+1]
print(f"\\nOld help section ({len(old_help)} bytes):")
print(repr(old_help))

new_help = b'    /* help \\u56fe\\u6807 - \\u84dd\\u8272\\u9ad8\\u4eae */\\n    .stTooltipIcon, .stTooltipIcon svg,\\n    [data-testid=\\"stTooltipIcon\\"],\\n    [data-testid=\\"stTooltipIcon\\"] svg {\\n        fill: #4472C4 !important;\\n        color: #4472C4 !important;\\n        opacity: 1 !important;\\n        background: transparent !important;\\n    }\\n'

print(f"\\nNew help section ({len(new_help)} bytes):")
print(repr(new_help))

raw = raw[:start2] + new_help + raw[end2+1:]

print("\\nHelp icon section replaced successfully!")

# Write back
with open('C:/Users/lx/Desktop/judge-scoring-app/app.py', 'wb') as f:
    f.write(raw)

print("\\nDONE: File saved!")

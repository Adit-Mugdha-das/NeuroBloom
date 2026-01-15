#!/usr/bin/env python3
"""Fix the Chart.js configuration errors in the reports page"""

file_path = r"d:\NeuroBloom\frontend-svelte\src\routes\doctor\patient\[id]\reports\+page.svelte"

# Read the file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace using regex to handle any whitespace
import re

# Pattern to find the ticks block with beginAtZero and max
pattern = r"(ticks:\s*\{\s*color:\s*'#fff',\s*backdropColor:\s*'transparent',)\s*beginAtZero:\s*true,\s*max:\s*100\s*(\})"

replacement = r"\1\n\t\t\t\t\t},\n\t\t\t\t\tsuggestedMin: 0,\n\t\t\t\t\tsuggestedMax: 100"

content = re.sub(pattern, replacement, content)

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed Chart.js configuration in reports page!")
print("Removed 'beginAtZero' and 'max' from ticks and moved them to scale level as 'suggestedMin/suggestedMax'")

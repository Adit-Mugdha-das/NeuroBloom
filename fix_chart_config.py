#!/usr/bin/env python3
"""Fix Chart.js configuration in reports page"""

file_path = r"d:\NeuroBloom\frontend-svelte\src\routes\doctor\patient\[id]\reports\+page.svelte"

# Read the file
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and fix the problematic lines
modified = False
for i in range(len(lines)):
    # Look for the line with beginAtZero
    if 'beginAtZero: true,' in lines[i]:
        # Get the indentation
        indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
        
        # Remove beginAtZero line
        del lines[i]
        
        # Remove max line (which should now be at position i)
        if i < len(lines) and 'max: 100' in lines[i]:
            del lines[i]
        
        # Find the closing brace of ticks and add suggestedMin/Max before the closing brace of the r scale
        # Look for the line with just closing brace and tabs
        for j in range(i, min(i + 5, len(lines))):
            if lines[j].strip() == '}':
                # This is the closing brace of ticks
                # Add suggestedMin and suggestedMax after it
                lines.insert(j + 1, indent[:-1] + 'suggestedMin: 0,\n')
                lines.insert(j + 2, indent[:-1] + 'suggestedMax: 100\n')
                # Add closing brace and comma for ticks
                lines[j] = lines[j].rstrip() + ',\n'
                modified = True
                break
        break

if modified:
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("✅ Fixed! Removed 'beginAtZero' and 'max' from ticks, added 'suggestedMin' and 'suggestedMax' to scale.")
else:
    print("❌ Could not find the problematic lines. The file may have already been fixed.")

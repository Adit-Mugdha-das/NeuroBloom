#!/usr/bin/env python3
"""Script to update all task endpoints to include task_id parameter"""

import re

# Read the file
with open('backend/app/api/training.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Define all the replacements with specific context
replacements = [
    # digit-span track_session_completion
    (
        r'(def submit_digit_span_session\(.*?# Track session completion\s+)track_session_completion\(plan, "working_memory", session, user_id\)',
        r'\1track_session_completion(plan, "working_memory", session, user_id, task_id)',
        'digit-span'
    ),
    # spatial-span extraction
    (
        r'(@router\.post\("/tasks/spatial-span/submit.*?if not plan or plan\.id is None:\s+raise HTTPException.*?)\n(\s+# Score each trial)',
        r'\1\n    # Extract task_id for session tracking\n    task_id = session_data.get("task_id")\n\2',
        'spatial-span extraction'
    ),
    # spatial-span track_session_completion
    (
        r'(def submit_spatial_span_session\(.*?# Track session completion\s+)track_session_completion\(plan, "working_memory", session, user_id\)',
        r'\1track_session_completion(plan, "working_memory", session, user_id, task_id)',
        'spatial-span'
    ),
    # letter-number-sequencing extraction
    (
        r'(@router\.post\("/tasks/letter-number-sequencing/submit.*?if not plan or plan\.id is None:\s+raise HTTPException.*?)\n(\s+# Score each trial)',
        r'\1\n    # Extract task_id for session tracking\n    task_id = session_data.get("task_id")\n\2',
        'letter-number-sequencing extraction'
    ),
    # letter-number-sequencing track_session_completion
    (
        r'(def submit_letter_number_sequencing_session\(.*?# Track session completion\s+)track_session_completion\(plan, "working_memory", session, user_id\)',
        r'\1track_session_completion(plan, "working_memory", session, user_id, task_id)',
        'letter-number-sequencing'
    ),
    # operation-span extraction
    (
        r'(def submit_operation_span_session\(.*?if not plan or plan\.id is None:\s+raise HTTPException.*?)\n(\s+# Score each trial)',
        r'\1\n    # Extract task_id for session tracking\n    task_id = session_data.get("task_id")\n\2',
        'operation-span extraction'
    ),
    # operation-span track_session_completion
    (
        r'(def submit_operation_span_session\(.*?# Track session completion\s+)track_session_completion\(plan, "working_memory", session, user_id\)',
        r'\1track_session_completion(plan, "working_memory", session, user_id, task_id)',
        'operation-span'
    ),
]

# Apply replacements
for pattern, replacement, name in replacements:
    matches = list(re.finditer(pattern, content, re.DOTALL))
    if matches:
        print(f"✓ Found {len(matches)} match(es) for {name}")
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    else:
        print(f"✗ No match found for {name}")

# Write back
with open('backend/app/api/training.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\nDone! File updated.")

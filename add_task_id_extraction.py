import re

# Read file
with open('backend/app/api/training.py', 'r', encoding='utf-8') as f:
    content = f.read()

# List of endpoints that need task_id extraction added
# Format: (endpoint pattern, insertion pattern, task_id extraction line)
extractions = [
    # For endpoints with session_data dict parameter
    ('letter-number-sequencing', 'def submit_letter_number_sequencing_session', 'session_data'),
    ('operation-span', 'def submit_operation_span_session', 'session_data'),
    ('pattern-comparison', 'def submit_pattern_comparison_session', 'request_data'),
    ('stroop', 'def submit_stroop_session', 'request_data'),
    ('pasat', 'def submit_pasat_session', 'request_data'),
    ('trail-making-b', 'def submit_trail_making_b_session', 'submission.session_data'),
    ('wcst', 'def submit_wcst_session', 'submission.session_data'),
    ('soc', 'def submit_soc_session', 'request_data'),
    ('verbal-fluency', 'def submit_verbal_fluency_session', 'request_data'),
    ('dccs', 'def submit_dccs_session', 'request_data'),
    ('plus-minus', 'def submit_plus_minus_session', 'request_data'),
    ('category-fluency', 'def submit_category_fluency_trial', 'request_data'),
    ('twenty-questions', 'def submit_twenty_questions_game', 'request_data'),
    ('cancellation-test', 'def submit_cancellation_test', 'request_data'),
    ('multiple-object-tracking', 'def submit_mot_response', 'request_data'),
    ('useful-field-of-view', 'def submit_ufov_response', 'trial_data'),
]

# For go-nogo and flanker which use request parameter object
special_extractions = [
    ('gonogo', 'def submit_gonogo_session', 'request'),
    ('flanker', 'def submit_flanker_session', 'request'),
]

added_count = 0

# Add extractions for session_data/request_data based endpoints
for endpoint, func_name, data_source in extractions:
    if data_source == 'submission.session_data':
        # For trail-making-b and wcst that use submission parameter
        pattern = rf'({re.escape(func_name)}.*?if not plan\.id:.*?raise HTTPException.*?\n)'
        replacement = r'\1    # Extract task_id for session tracking\n    task_id = submission.session_data.get("task_id")\n    \n'
    elif 'trial_data' in data_source:
        # For useful-field-of-view
        pattern = rf'({re.escape(func_name)}.*?from app\.services\.useful_field_of_view_task.*?\n)'
        replacement = r'\1    \n    # Extract task_id for session tracking\n    task_id = trial_data.get("task_id")\n    \n'
    else:
        # For most endpoints using request_data or session_data
        # Find pattern after getting session_data or request_data
        if 'session_data' in data_source:
            pattern = rf'({re.escape(func_name)}.*?session_data = {data_source}\.get\("session_data"\).*?\n)'
        else:
            # Try multiple patterns
            pattern = rf'({re.escape(func_name)}.*?{data_source} = request_data\.get.*?\n\s*if not )'
            if not re.search(pattern, content, re.DOTALL):
                # Alternative: look for validation after request_data extraction
                pattern = rf'({re.escape(func_name)}.*?{data_source}\.get\("(session_data|difficulty)".*?\n\s+if )'
        replacement = r'\1    task_id = ' + data_source + r'.get("task_id")  # Extract task_id for session tracking\n    \n    if '
    
    if re.search(pattern, content, re.DOTALL):
        count_before = len(re.findall(r'task_id', content))
        content = re.sub(pattern, replacement, content, count=1, flags=re.DOTALL)
        count_after = len(re.findall(r'task_id', content))
        if count_after > count_before:
            added_count += 1
            print(f'✓ Added task_id extraction for {endpoint}')
        else:
            print(f'✗ No change for {endpoint} (might already exist)')
    else:
        print(f'✗ Pattern not found for {endpoint}')

# Handle go-nogo and flanker special cases
for endpoint, func_name, param in special_extractions:
    pattern = rf'({re.escape(func_name)}.*?difficulty = {param}\.difficulty.*?responses = {param}\.responses\n)'
    replacement = r'\1    task_id = getattr(' + param + r', "task_id", None)  # Extract task_id for session tracking\n    \n'
    
    if re.search(pattern, content, re.DOTALL):
        count_before = len(re.findall(r'task_id', content))
        content = re.sub(pattern, replacement, content, count=1, flags=re.DOTALL)
        count_after = len(re.findall(r'task_id', content))
        if count_after > count_before:
            added_count += 1
            print(f'✓ Added task_id extraction for {endpoint}')
        else:
            print(f'✗ No change for {endpoint} (might already exist)')
    else:
        print(f'✗ Pattern not found for {endpoint}')

# Write back
with open('backend/app/api/training.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f'\nTotal extractions added: {added_count}')

import re

# Read file
with open('backend/app/api/training.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Line-based updates - find and update track_session_completion calls that don't have task_id

updated_count = 0
endpoints_updated = []

for i in range(len(lines)):
    # Look for track_session_completion calls without task_id
    if 'track_session_completion(' in lines[i] and ', task_id)' not in lines[i]:
        # Check if it's not the function definition
        if 'def track_session_completion' not in lines[i]:
            # Replace the call
            old_line = lines[i]
            lines[i] = lines[i].replace(
                'track_session_completion(plan, "working_memory", session, user_id)',
                'track_session_completion(plan, "working_memory", session, user_id, task_id)'
            )
            lines[i] = lines[i].replace(
                'track_session_completion(plan, "processing_speed", session, user_id)',
                'track_session_completion(plan, "processing_speed", session, user_id, task_id)'
            )
            lines[i] = lines[i].replace(
                'track_session_completion(plan, "attention", session, user_id)',
                'track_session_completion(plan, "attention", session, user_id, task_id)'
            )
            lines[i] = lines[i].replace(
                'track_session_completion(plan, "flexibility", session, user_id)',
                'track_session_completion(plan, "flexibility", session, user_id, task_id)'
            )
            lines[i] = lines[i].replace(
                'track_session_completion(plan, "planning", session, user_id)',
                'track_session_completion(plan, "planning", session, user_id, task_id)'
            )
            lines[i] = lines[i].replace(
                'track_session_completion(training_plan, "visual_scanning", session, user_id)',
                'track_session_completion(training_plan, "visual_scanning", session, user_id, task_id)'
            )
            
            if lines[i] != old_line:
                updated_count += 1
                # Look backwards to find endpoint name
                for j in range(i-1, max(0, i-100), -1):
                    if '@router.post("/tasks/' in lines[j]:
                        match = re.search(r'/tasks/([\w-]+)/', lines[j])
                        if match:
                            endpoints_updated.append(match.group(1))
                        break

# Write back
with open('backend/app/api/training.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f'Updated {updated_count} track_session_completion calls')
print(f'Endpoints updated: {sorted(set(endpoints_updated))}')

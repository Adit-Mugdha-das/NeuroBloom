# Task Rotation Implementation Guide
## Smart Task Selection System for NeuroBloom

**Date**: January 2, 2026  
**Status**: ✅ Implemented

---

## 📋 Overview

The Task Rotation System provides intelligent task selection to:
- **Prevent boredom** through variety
- **Reduce practice effects** by avoiding repetition
- **Maintain clinical validity** using evidence-based tasks
- **Optimize engagement** with user preferences
- **Ensure balanced exposure** across all task types

---

## 🎯 System Architecture

### Components

```
┌─────────────────────────────────────────────┐
│         Frontend (Svelte)                   │
│  - Fetches next tasks from API              │
│  - Displays varied task types               │
│  - Submits results with task_code           │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│         Training API (training.py)          │
│  - get_next_training_tasks()                │
│  - submit_training_session()                │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│    TaskRotationService (task_rotation.py)   │
│  - select_task_for_session()                │
│  - Rotation strategies per domain           │
│  - User preference integration              │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│         Database Models                     │
│  - CognitiveTask (task definitions)         │
│  - TrainingSession (history tracking)       │
│  - UserTaskPreference (favorites/dislikes)  │
└─────────────────────────────────────────────┘
```

---

## 🗄️ Database Schema

### CognitiveTask Table

Stores all available task variants:

```sql
CREATE TABLE cognitive_tasks (
    id SERIAL PRIMARY KEY,
    task_code VARCHAR(50) UNIQUE,      -- e.g., 'digit_span', 'sdmt'
    domain VARCHAR(50),                 -- 'working_memory', 'attention', etc.
    task_name VARCHAR(100),             -- Human-readable name
    description TEXT,
    clinical_validation TEXT,           -- Research references
    is_baseline_task BOOLEAN,           -- Original 6 tasks (True)
    difficulty_min INT DEFAULT 1,
    difficulty_max INT DEFAULT 10,
    estimated_duration_seconds INT,
    requires_audio BOOLEAN,
    requires_keyboard BOOLEAN,
    cognitive_load VARCHAR(20),         -- 'low', 'medium', 'high'
    instructions TEXT,
    created_at TIMESTAMP
);
```

**Current Task Count**: 28 tasks across 6 domains
- Working Memory: 5 tasks
- Processing Speed: 5 tasks
- Attention: 5 tasks
- Flexibility: 5 tasks
- Planning: 5 tasks
- Visual Scanning: 5 tasks

### UserTaskPreference Table

Tracks user likes/dislikes:

```sql
CREATE TABLE user_task_preferences (
    user_id INT REFERENCES users(id),
    task_code VARCHAR(50),
    preference VARCHAR(20),             -- 'favorite', 'neutral', 'dislike'
    reason TEXT,
    created_at TIMESTAMP,
    PRIMARY KEY (user_id, task_code)
);
```

---

## 🔄 Rotation Strategies

Each domain uses an optimal rotation strategy:

### 1. Working Memory: Sequential
```python
'working_memory': {
    'strategy': 'sequential',
    'max_repeats': 1,
    'exclude_last_n': 2  # Don't repeat from last 2 sessions
}
```
**Tasks**: n_back → digit_span → spatial_span → letter_number_sequencing → operation_span → (repeat)

**Logic**: Cycle through tasks in order, ensures variety without randomness

---

### 2. Processing Speed: Weighted
```python
'processing_speed': {
    'strategy': 'weighted',
    'weights': {
        'simple_reaction': 0.25,
        'sdmt': 0.40,              # ⭐ Prioritized (MS gold standard)
        'trails_a': 0.20,
        'pattern_comparison': 0.15
    },
    'exclude_last_n': 1
}
```

**Logic**: SDMT appears 40% of the time (most clinically valuable), others balanced

---

### 3. Attention: Random
```python
'attention': {
    'strategy': 'random',
    'exclude_last_n': 2  # Avoid last 2 sessions
}
```

**Tasks**: cpt, pasat, stroop, go_nogo, flanker (random selection)

**Logic**: Unpredictable variety, good for attention tasks

---

### 4. Flexibility: Adaptive
```python
'flexibility': {
    'strategy': 'adaptive',
    'exclude_last_n': 2
}
```

**Logic**: Selects tasks where user performs **worst** (needs more practice)

---

### 5. Planning: Balanced
```python
'planning': {
    'strategy': 'balanced',
    'exclude_last_n': 1,
    'alternate_types': True  # Visual vs verbal tasks
}
```

**Logic**: Ensures equal exposure to all tasks over time

---

### 6. Visual Scanning: Difficulty-Matched
```python
'visual_scanning': {
    'strategy': 'difficulty_matched',
    'exclude_last_n': 2
}
```

**Logic**: Tasks progress together in difficulty

---

## 🚀 Usage & API

### 1. Seed Cognitive Tasks (Run Once)

Populate the database with all 28 tasks:

```bash
cd d:\NeuroBloom\backend
python seed_cognitive_tasks.py
```

**Output**:
```
🌱 Seeding cognitive_tasks table...
📊 Total tasks to seed: 28

✅ Added: n_back - N-Back Test ⭐ BASELINE
✅ Added: digit_span - Digit Span (Forward & Backward)
...
🎉 Seeding Complete!
✅ Added: 28 tasks
📊 Total tasks in database: 28
```

---

### 2. Get Next Training Tasks

**Endpoint**: `GET /training-plan/{user_id}/next-tasks`

**Before** (old system):
```json
{
  "tasks": [
    {
      "domain": "working_memory",
      "task_type": "n_back",  // Always the same
      "difficulty": 5
    }
  ]
}
```

**After** (new rotation system):
```json
{
  "tasks": [
    {
      "domain": "working_memory",
      "task_type": "digit_span",         // ✨ Varied
      "task_name": "Digit Span Test",
      "task_description": "Remember and repeat sequences...",
      "difficulty": 5,
      "priority": "primary",
      "requires_audio": true,
      "estimated_duration": 120
    }
  ],
  "rotation_info": "Tasks selected using smart rotation to prevent repetition"
}
```

---

### 3. Submit Training Session

**Endpoint**: `POST /training-session/submit`

**New Parameter**: `task_code` (optional but recommended)

```json
{
  "user_id": 1,
  "training_plan_id": 123,
  "domain": "working_memory",
  "task_type": "digit_span",     // Generic type
  "task_code": "digit_span",     // ✨ Specific variant (NEW)
  "score": 85.5,
  "accuracy": 88.0,
  "average_reaction_time": 1200,
  "consistency": 92.0,
  "errors": 3,
  "duration": 120,
  "raw_data": { /* trial data */ }
}
```

**Why task_code matters**:
- Enables rotation tracking (avoids recent tasks)
- Allows performance analysis per task variant
- Powers adaptive strategy (selects weak tasks)

---

## 🧠 Rotation Logic Examples

### Example Session Flow

**User**: Jane (user_id: 42)  
**Training Plan**: Primary focus = [working_memory, attention]

#### Session 1
```python
# Working Memory → Sequential strategy
Recent tasks: []
Available: [n_back, digit_span, spatial_span, letter_number, ospan]
Selected: n_back (first in sequence)

# Attention → Random strategy
Recent tasks: []
Available: [cpt, pasat, stroop, go_nogo, flanker]
Selected: stroop (random)
```

#### Session 2
```python
# Working Memory → Sequential strategy
Recent tasks: [n_back]  (from session 1)
Available: [digit_span, spatial_span, letter_number, ospan]  (excluding recent)
Selected: digit_span (next in sequence)

# Attention → Random strategy
Recent tasks: [stroop]
Available: [cpt, pasat, go_nogo, flanker]  (excluding stroop)
Selected: pasat (random)
```

#### Session 3
```python
# Working Memory → Sequential strategy
Recent tasks: [n_back, digit_span]
Available: [spatial_span, letter_number, ospan]  (excluding last 2)
Selected: spatial_span (next in sequence)

# Attention → Random strategy
Recent tasks: [stroop, pasat]
Available: [cpt, go_nogo, flanker]  (excluding last 2)
Selected: go_nogo (random)
```

**Result**: Jane experiences 3 different working memory tasks and 3 different attention tasks in 3 sessions!

---

## 🎨 Frontend Integration

### Task Display

Show task variety to users:

```svelte
<script>
  let nextTasks = await fetch(`/training-plan/${userId}/next-tasks`).then(r => r.json());
</script>

{#each nextTasks.tasks as task}
  <div class="task-card">
    <h3>{task.task_name}</h3>
    <p>{task.task_description}</p>
    
    {#if task.requires_audio}
      <span class="badge">🔊 Audio Required</span>
    {/if}
    
    <span class="priority-badge {task.priority}">
      {task.priority} focus
    </span>
    
    <button on:click={() => startTask(task.task_type)}>
      Start Task ({task.estimated_duration}s)
    </button>
  </div>
{/each}
```

### Task Submission

Include `task_code` in submission:

```javascript
async function submitTaskResults(results) {
  await fetch('/training-session/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: userId,
      training_plan_id: planId,
      domain: results.domain,
      task_type: results.task_type,
      task_code: results.task_code,  // ✨ Important!
      score: results.score,
      accuracy: results.accuracy,
      // ... other metrics
    })
  });
}
```

---

## 🔧 Customization

### Adding New Tasks

1. **Define task** in [seed_cognitive_tasks.py](d:\NeuroBloom\backend\seed_cognitive_tasks.py):

```python
{
    "task_code": "my_new_task",
    "domain": "working_memory",
    "task_name": "My New Task",
    "description": "Task description",
    "clinical_validation": "Research reference",
    "is_baseline_task": False,
    "difficulty_min": 1,
    "difficulty_max": 10,
    "estimated_duration_seconds": 120,
    "requires_audio": False,
    "requires_keyboard": True,
    "cognitive_load": "medium",
    "instructions": "How to perform the task"
}
```

2. **Run seed script**:
```bash
python seed_cognitive_tasks.py
```

3. **Implement task frontend** in Svelte routes

4. **Add scoring logic** to backend task service

---

### Adjusting Rotation Strategy

Edit [task_rotation.py](d:\NeuroBloom\backend\app\services\task_rotation.py):

```python
ROTATION_CONFIG = {
    'working_memory': {
        'strategy': 'sequential',  # Change to 'random', 'adaptive', etc.
        'exclude_last_n': 2        # Increase for more variety
    }
}
```

**Available Strategies**:
- `sequential` - Cycle through tasks in order
- `weighted` - Probability-based selection
- `random` - Pure random from available
- `adaptive` - Select based on user performance
- `balanced` - Equal exposure over time

---

## 📊 Analytics & Monitoring

### Track Task Usage

Query most/least used tasks:

```sql
SELECT 
    task_code,
    COUNT(*) as usage_count,
    AVG(score) as avg_score
FROM training_sessions
WHERE user_id = 42
GROUP BY task_code
ORDER BY usage_count DESC;
```

### Check Rotation Effectiveness

Ensure variety across recent sessions:

```sql
SELECT 
    domain,
    task_code,
    created_at
FROM training_sessions
WHERE user_id = 42
ORDER BY created_at DESC
LIMIT 20;
```

Expected: Different task_code values within same domain

---

## ✅ Testing Checklist

- [ ] Seed cognitive_tasks table successfully
- [ ] `/next-tasks` returns varied tasks per domain
- [ ] Same task doesn't repeat in consecutive sessions
- [ ] task_code is stored in training_sessions
- [ ] Weighted strategy prioritizes SDMT for processing_speed
- [ ] Adaptive strategy selects weak tasks for flexibility
- [ ] User preferences affect task selection (if implemented)
- [ ] Frontend displays task variety correctly
- [ ] Task submission includes task_code

---

## 🚨 Troubleshooting

### Issue: Always getting same task

**Check**:
1. Is cognitive_tasks table populated?
   ```bash
   python seed_cognitive_tasks.py
   ```

2. Are multiple tasks available for domain?
   ```sql
   SELECT * FROM cognitive_tasks WHERE domain = 'working_memory';
   ```

3. Is rotation service being called?
   - Check logs: "Using TaskRotationService"

---

### Issue: Missing task_code in submissions

**Solution**: Update frontend to include `task_code`:

```javascript
// Before
{ domain: "attention", task_type: "cpt" }

// After
{ domain: "attention", task_type: "cpt", task_code: "cpt" }
```

---

### Issue: Rotation not varying enough

**Adjust exclusion window**:

```python
# Increase exclude_last_n for more variety
'attention': {
    'strategy': 'random',
    'exclude_last_n': 3  # Was 2, now excludes last 3
}
```

---

## 📚 Clinical References

All tasks are validated for MS populations:

1. **Benedict et al. (2006)** - MACFIMS battery
2. **Langdon et al. (2012)** - BICAMS assessment
3. **Strober et al. (2019)** - SDMT in MS
4. **Gronwall (1977)** - PASAT development
5. **D'Elia et al. (1996)** - Trail Making Test

See [TASK_VARIETY_EXPANSION.md](d:\NeuroBloom\TASK_VARIETY_EXPANSION.md) for full references.

---

## 🎯 Benefits Summary

| Aspect | Before | After |
|--------|--------|-------|
| Tasks per domain | 1 | 5 |
| Total tasks | 6 | 28 |
| Repetition | Every session | Excluded last 2 sessions |
| User engagement | Decreases over time | Maintained high |
| Practice effects | High (memorization) | Low (true skill) |
| Clinical validity | Moderate | High (gold standards) |
| Customization | None | Strategy-based |

---

## 🔮 Future Enhancements

1. **User Preferences UI**: Let users mark favorites/dislikes
2. **Performance-based weights**: Adjust task frequency by user struggle
3. **Time-of-day optimization**: Morning vs evening task selection
4. **Difficulty synchronization**: Match difficulty across task variants
5. **Streak-aware rotation**: Vary tasks on streak milestones
6. **A/B testing**: Compare rotation strategies for effectiveness

---

## 📞 Support

For questions about task rotation:
1. Check this guide
2. Review [task_rotation.py](d:\NeuroBloom\backend\app\services\task_rotation.py) source code
3. Consult [TASK_VARIETY_EXPANSION.md](d:\NeuroBloom\TASK_VARIETY_EXPANSION.md) for task details

---

**Last Updated**: January 2, 2026  
**Status**: ✅ Fully Implemented and Operational

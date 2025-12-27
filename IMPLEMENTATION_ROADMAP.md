# 🧠 NeuroBloom - Complete Implementation Roadmap
## Clinical-Grade Cognitive Assessment Platform

---

## 📋 OVERVIEW

Transform NeuroBloom from basic brain games into a clinical-grade cognitive assessment and training platform with:
- Validated neuropsychological tests
- MS-specific adaptations
- Adaptive AI difficulty
- Comprehensive progress tracking
- Weekly re-planning algorithm

**Tech Stack:**
- Backend: FastAPI + PostgreSQL
- Frontend: SvelteKit
- Charts: Chart.js / D3.js
- Real-time: WebSockets (for live sessions)
i ch
---

## 🗂️ COMPLETE DATABASE SCHEMA

### 1. Users Table (Enhanced)
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    date_of_birth DATE,
    diagnosis VARCHAR(100),  -- 'MS', 'healthy_control', 'other'
    created_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP
);
```

### 2. Baseline Assessment Table
```sql
CREATE TABLE baseline_assessments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    assessment_date TIMESTAMP DEFAULT NOW(),
    
    -- Domain Scores (0-100)
    working_memory_score FLOAT,
    attention_score FLOAT,
    flexibility_score FLOAT,
    planning_score FLOAT,
    processing_speed_score FLOAT,
    visual_scanning_score FLOAT,
    
    -- Raw Metrics (JSON)
    raw_metrics JSONB,  -- All detailed metrics per domain
    
    -- Flags
    is_baseline BOOLEAN DEFAULT true,
    assessment_duration_minutes INTEGER,
    
    UNIQUE(user_id, is_baseline)  -- Only one baseline per user
);
```

### 3. Cognitive Domains Table
```sql
CREATE TABLE cognitive_domains (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE,  -- 'working_memory', 'attention', etc.
    display_name VARCHAR(100),
    description TEXT,
    icon VARCHAR(50)
);
```

### 4. Tasks Library Table
```sql
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    task_name VARCHAR(100) UNIQUE,
    task_type VARCHAR(50),  -- 'nback', 'cpt', 'task_switching', etc.
    
    -- Domain mapping
    primary_domain_id INTEGER REFERENCES cognitive_domains(id),
    secondary_domains JSONB,  -- Array of domain IDs
    
    -- Difficulty parameters
    difficulty_knobs JSONB,  -- {min, max, step} for each parameter
    
    -- Task configuration
    instructions TEXT,
    estimated_duration_minutes INTEGER,
    
    -- Validation info
    is_validated BOOLEAN DEFAULT false,
    validation_source VARCHAR(255)
);
```

### 5. Test Sessions Table (Enhanced)
```sql
CREATE TABLE test_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_date TIMESTAMP DEFAULT NOW(),
    session_type VARCHAR(50),  -- 'baseline', 'training', 'reassessment'
    
    -- Session details
    total_duration_minutes INTEGER,
    tasks_completed INTEGER,
    session_number INTEGER,  -- Day 1, 2, 3...
    
    -- Fatigue detection
    fatigue_detected BOOLEAN DEFAULT false,
    performance_drift FLOAT,  -- Drop percentage
    breaks_taken INTEGER,
    
    -- Status
    completed BOOLEAN DEFAULT false,
    completion_percentage FLOAT
);
```

### 6. Task Results Table (Detailed Metrics)
```sql
CREATE TABLE task_results (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES test_sessions(id),
    user_id INTEGER REFERENCES users(id),
    task_id INTEGER REFERENCES tasks(id),
    
    -- Performance metrics
    accuracy FLOAT,  -- Percentage
    reaction_time_mean FLOAT,  -- Milliseconds
    reaction_time_std FLOAT,  -- Variability
    
    -- Error analysis
    errors_total INTEGER,
    errors_miss INTEGER,  -- Missed targets
    errors_false_alarm INTEGER,  -- False positives
    errors_perseveration INTEGER,  -- Stuck on old rule
    
    -- Difficulty tracking
    difficulty_level INTEGER,
    difficulty_adjustments JSONB,  -- History of changes
    
    -- Round-by-round data
    round_data JSONB,  -- [{round: 1, acc: 0.8, rt: 450, ...}, ...]
    
    -- Fatigue
    fatigue_index FLOAT,  -- Performance drop over time
    
    -- Timestamps
    task_start_time TIMESTAMP,
    task_end_time TIMESTAMP,
    actual_duration_seconds INTEGER
);
```

### 7. Training Plans Table
```sql
CREATE TABLE training_plans (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    plan_start_date DATE,
    plan_end_date DATE,
    
    -- Target domains (what to train)
    target_domains JSONB,  -- [{domain_id, priority_percentage, target_improvement}, ...]
    
    -- Task allocation
    daily_task_sequence JSONB,  -- Which tasks, how long, what difficulty
    
    -- Plan basis
    based_on_assessment_id INTEGER REFERENCES baseline_assessments(id),
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    last_updated TIMESTAMP DEFAULT NOW()
);
```

### 8. Progress Snapshots Table
```sql
CREATE TABLE progress_snapshots (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    snapshot_date DATE,
    days_since_baseline INTEGER,
    
    -- Current scores per domain
    working_memory_current FLOAT,
    attention_current FLOAT,
    flexibility_current FLOAT,
    planning_current FLOAT,
    processing_speed_current FLOAT,
    visual_scanning_current FLOAT,
    
    -- Improvements vs baseline
    working_memory_delta FLOAT,
    attention_delta FLOAT,
    flexibility_delta FLOAT,
    planning_delta FLOAT,
    processing_speed_delta FLOAT,
    visual_scanning_delta FLOAT,
    
    -- Trends
    improvement_rate VARCHAR(50),  -- 'improving', 'stagnant', 'declining'
    consistency_score FLOAT,
    
    UNIQUE(user_id, snapshot_date)
);
```

---

## 🏗️ BACKEND STRUCTURE (FastAPI)

### Phase 1: Core Models & Database
```
backend/
├── app/
│   ├── models/
│   │   ├── user.py
│   │   ├── baseline_assessment.py
│   │   ├── cognitive_domain.py
│   │   ├── task.py
│   │   ├── test_session.py
│   │   ├── task_result.py
│   │   ├── training_plan.py
│   │   └── progress_snapshot.py
│   │
│   ├── schemas/
│   │   ├── baseline_assessment.py
│   │   ├── task_result.py
│   │   ├── training_plan.py
│   │   └── progress.py
│   │
│   ├── api/
│   │   ├── auth.py
│   │   ├── baseline.py          # NEW
│   │   ├── tasks.py
│   │   ├── sessions.py           # NEW
│   │   ├── training_plans.py     # NEW
│   │   ├── progress.py           # NEW
│   │   └── adaptive.py           # NEW - Difficulty adjustment
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── scoring.py            # NEW - Domain scoring logic
│   │   └── algorithms/
│   │       ├── adaptive_difficulty.py
│   │       ├── fatigue_detection.py
│   │       └── plan_generator.py
│   │
│   └── main.py
```

---

## 🎨 FRONTEND STRUCTURE (SvelteKit)

### Phase 1: Project Setup
```
frontend/
├── src/
│   ├── lib/
│   │   ├── api.js                # API client
│   │   ├── stores.js             # Svelte stores
│   │   ├── utils.js
│   │   └── components/
│   │       ├── Header.svelte
│   │       ├── Sidebar.svelte
│   │       ├── LoadingSpinner.svelte
│   │       └── ProgressChart.svelte
│   │
│   ├── routes/
│   │   ├── +layout.svelte
│   │   ├── +page.svelte          # Landing/Login
│   │   │
│   │   ├── auth/
│   │   │   ├── login/+page.svelte
│   │   │   └── register/+page.svelte
│   │   │
│   │   ├── dashboard/
│   │   │   └── +page.svelte
│   │   │
│   │   ├── baseline/              # NEW - Baseline assessment
│   │   │   ├── +page.svelte       # Overview & start
│   │   │   ├── intro/+page.svelte
│   │   │   ├── tasks/
│   │   │   │   ├── working-memory/+page.svelte
│   │   │   │   ├── attention/+page.svelte
│   │   │   │   ├── flexibility/+page.svelte
│   │   │   │   ├── planning/+page.svelte
│   │   │   │   ├── processing-speed/+page.svelte
│   │   │   │   └── visual-scanning/+page.svelte
│   │   │   └── results/+page.svelte
│   │   │
│   │   ├── training/              # NEW - Daily training
│   │   │   ├── +page.svelte       # Today's session
│   │   │   ├── session/[id]/+page.svelte
│   │   │   └── task/[taskId]/+page.svelte
│   │   │
│   │   ├── progress/              # NEW - Progress tracking
│   │   │   ├── +page.svelte
│   │   │   └── detailed/+page.svelte
│   │   │
│   │   └── admin/                 # Optional: clinician view
│   │       └── +page.svelte
│   │
│   └── app.css
│
├── static/
└── svelte.config.js
```

---

## 📝 STEP-BY-STEP IMPLEMENTATION PLAN

---

## **PHASE 1: Project Setup & Migration (Week 1)**

### Step 1.1: Setup SvelteKit Frontend
```bash
# Remove old React frontend
cd D:\NeuroBloom
rm -rf frontend/src frontend/package.json frontend/vite.config.js frontend/index.html

# Create new SvelteKit project
npm create svelte@latest frontend
# Choose: Skeleton project, TypeScript: No, ESLint/Prettier: Yes

cd frontend
npm install
npm install axios chart.js
```

### Step 1.2: Update Backend Models
Create all 8 database models in `backend/app/models/`

### Step 1.3: Database Migration
```bash
# Create migration script
alembic init alembic
alembic revision --autogenerate -m "Add clinical tables"
alembic upgrade head
```

---

## **PHASE 2: Baseline Assessment System (Week 2-3)**

### Step 2.1: Implement 6 Validated Tasks

#### A. Working Memory - N-Back Test
**File:** `frontend/src/routes/baseline/tasks/working-memory/+page.svelte`

**Task Logic:**
- Show sequence of letters: A, B, C, A, D...
- User clicks "Match" if current letter = letter N steps back
- Start with 1-back, progress to 2-back if accuracy > 80%

**Metrics to collect:**
```javascript
{
  total_trials: 20,
  correct_hits: 15,
  false_alarms: 2,
  misses: 3,
  reaction_times: [450, 523, 389, ...],
  accuracy: 0.75,
  mean_rt: 452.3,
  rt_std: 67.8
}
```

**Backend endpoint:**
```python
@router.post("/baseline/working-memory")
def submit_working_memory(data: WorkingMemoryResult, user_id: int):
    # Calculate normalized score
    score = calculate_working_memory_score(data)
    # Save to baseline_assessments
    return {"score": score, "raw_metrics": data}
```

#### B. Attention - Continuous Performance Test (CPT)
**File:** `frontend/src/routes/baseline/tasks/attention/+page.svelte`

**Task Logic:**
- Show rapid sequence of letters (1 per second)
- Click ONLY when you see "X after A" (AX sequence)
- Run for 5 minutes, 300 trials

**Metrics:**
```javascript
{
  targets_shown: 30,      // AX sequences
  targets_hit: 25,
  misses: 5,
  false_alarms: 8,        // Clicked when not AX
  sustained_attention_drift: 0.15,  // Performance drop %
  vigilance_decrement: true
}
```

#### C. Cognitive Flexibility - Task Switching
**File:** `frontend/src/routes/baseline/tasks/flexibility/+page.svelte`

**Task Logic:**
- Show number + background color
- If blue background: judge odd/even
- If red background: judge >5 or <5
- Switch rules randomly

**Metrics:**
```javascript
{
  total_switches: 40,
  switch_errors: 6,
  no_switch_errors: 2,
  switch_cost_rt: 234,    // RT increase on switch trials
  perseveration_errors: 3  // Used old rule
}
```

#### D. Planning - Tower of Hanoi (3-disk)
**File:** `frontend/src/routes/baseline/tasks/planning/+page.svelte`

**Task Logic:**
- Move 3 disks from peg A to peg C
- Optimal solution: 7 moves
- Track planning time before first move

**Metrics:**
```javascript
{
  moves_taken: 12,
  optimal_moves: 7,
  excess_moves: 5,
  planning_time_ms: 8500,
  first_move_latency: 8500,
  total_time_seconds: 45
}
```

#### E. Processing Speed - Simple & Choice RT
**File:** `frontend/src/routes/baseline/tasks/processing-speed/+page.svelte`

**Task Logic:**
Part 1: Simple RT - press space when green square appears
Part 2: Choice RT - press left for circle, right for square

**Metrics:**
```javascript
{
  simple_rt_mean: 285,
  simple_rt_std: 45,
  choice_rt_mean: 456,
  choice_rt_std: 78,
  choice_accuracy: 0.95,
  speed_accuracy_tradeoff: "balanced"
}
```

#### F. Visual Scanning - Visual Search
**File:** `frontend/src/routes/baseline/tasks/visual-scanning/+page.svelte`

**Task Logic:**
- Grid of 50 letters (Ts, Ls, Xs)
- Find all "T"s (5 targets)
- Track search time per target

**Metrics:**
```javascript
{
  targets_total: 5,
  targets_found: 4,
  search_time_ms: 12500,
  time_per_target: 2500,
  scan_efficiency: 0.68,
  missed_targets: 1
}
```

### Step 2.2: Scoring Algorithm
**File:** `backend/app/core/scoring.py`

```python
def calculate_domain_score(metrics: dict, domain: str) -> float:
    """
    Normalize to 0-100 scale using weighted formula:
    - Accuracy: 60%
    - Reaction Time: 30%
    - Consistency: 10%
    
    Compare to age-matched norms (future: use local DB)
    """
    
    if domain == "working_memory":
        accuracy_score = (metrics['correct_hits'] / metrics['total_trials']) * 60
        
        # RT scoring (faster = better, with ceiling/floor)
        rt_normalized = normalize_rt(metrics['mean_rt'], 
                                     min_rt=300, max_rt=1000)
        rt_score = (1 - rt_normalized) * 30
        
        # Consistency (lower std = better)
        consistency_score = (1 - min(metrics['rt_std'] / 200, 1)) * 10
        
        return accuracy_score + rt_score + consistency_score
    
    # Similar for other domains...
```

### Step 2.3: Baseline Results Page
**File:** `frontend/src/routes/baseline/results/+page.svelte`

Show:
- Radar chart with 6 domain scores
- Strengths vs weaknesses
- Detailed metrics per domain
- "Your cognitive profile" summary
- Button: "Start Training Program"

---

## **PHASE 3: Adaptive Training Engine (Week 4-5)**

### Step 3.1: Training Plan Generator
**File:** `backend/app/core/algorithms/plan_generator.py`

```python
class TrainingPlanGenerator:
    def generate(self, baseline: BaselineAssessment) -> TrainingPlan:
        """
        Generate personalized training plan based on baseline
        """
        
        # 1. Identify weak domains (score < 60)
        weak_domains = [d for d in domains if d.score < 60]
        
        # 2. Calculate time allocation
        total_session_minutes = 25
        allocations = {}
        
        # 60% on weak domains
        weak_time = 0.6 * total_session_minutes
        for domain in weak_domains:
            allocations[domain.id] = weak_time / len(weak_domains)
        
        # 40% on maintenance domains
        maintenance_time = 0.4 * total_session_minutes
        # ...
        
        # 3. Select tasks per domain
        task_sequence = []
        for domain_id, minutes in allocations.items():
            tasks = get_tasks_for_domain(domain_id)
            task_sequence.append({
                'task_id': tasks[0].id,
                'duration_minutes': minutes,
                'starting_difficulty': baseline.get_domain_score(domain_id) / 20
            })
        
        # 4. Add MS-specific rules
        if user.diagnosis == 'MS':
            # Shorter blocks
            task_sequence = split_into_shorter_blocks(task_sequence, max_block=6)
            # Add micro-breaks
            task_sequence = insert_breaks(task_sequence, every_n_minutes=6)
        
        return TrainingPlan(
            user_id=baseline.user_id,
            target_domains=allocations,
            daily_task_sequence=task_sequence
        )
```

### Step 3.2: Adaptive Difficulty Controller
**File:** `backend/app/core/algorithms/adaptive_difficulty.py`

```python
class AdaptiveDifficultyController:
    TARGET_ACCURACY = 0.75  # Sweet spot: 70-85%
    
    def adjust(self, round_results: list, current_difficulty: int) -> int:
        """
        Adjust difficulty based on last 3 rounds
        """
        recent_accuracy = mean([r['accuracy'] for r in round_results[-3:]])
        recent_rt = mean([r['rt'] for r in round_results[-3:]])
        
        # Check if too easy
        if recent_accuracy > 0.85 and is_rt_stable(recent_rt):
            return min(current_difficulty + 1, MAX_DIFFICULTY)
        
        # Check if too hard
        elif recent_accuracy < 0.65:
            return max(current_difficulty - 1, 1)
        
        # Check for fatigue
        elif self.detect_fatigue(round_results):
            return current_difficulty  # Keep same but trigger break
        
        else:
            return current_difficulty  # In sweet spot
```

### Step 3.3: Fatigue Detection (MS-Specific)
**File:** `backend/app/core/algorithms/fatigue_detection.py`

```python
def detect_fatigue(round_results: list) -> bool:
    """
    Detect cognitive fatigue by analyzing performance drift
    """
    if len(round_results) < 6:
        return False
    
    # Compare first 3 rounds vs last 3 rounds
    early_performance = mean([r['accuracy'] for r in round_results[:3]])
    late_performance = mean([r['accuracy'] for r in round_results[-3:]])
    
    performance_drop = (early_performance - late_performance) / early_performance
    
    # Also check RT increase
    early_rt = mean([r['rt'] for r in round_results[:3]])
    late_rt = mean([r['rt'] for r in round_results[-3:]])
    rt_increase = (late_rt - early_rt) / early_rt
    
    # Fatigue if accuracy drops >15% OR RT increases >20%
    return performance_drop > 0.15 or rt_increase > 0.20
```

---

## **PHASE 4: Progress Tracking & Re-Planning (Week 6)**

### Step 4.1: Weekly Snapshot Generator
**File:** `backend/app/core/algorithms/snapshot_generator.py`

```python
def generate_weekly_snapshot(user_id: int, week_number: int):
    """
    Every 7 days, calculate current domain scores
    """
    # Get all sessions from past 7 days
    sessions = get_last_7_days_sessions(user_id)
    
    # Calculate average performance per domain
    domain_scores = {}
    for domain in DOMAINS:
        tasks = get_tasks_for_domain(domain.id, sessions)
        avg_accuracy = mean([t.accuracy for t in tasks])
        avg_rt = mean([t.reaction_time_mean for t in tasks])
        
        # Calculate current score
        domain_scores[domain.name] = calculate_current_score(avg_accuracy, avg_rt)
    
    # Compare to baseline
    baseline = get_baseline(user_id)
    deltas = {}
    for domain in DOMAINS:
        current = domain_scores[domain.name]
        baseline_score = getattr(baseline, f"{domain.name}_score")
        deltas[domain.name] = current - baseline_score
    
    # Save snapshot
    snapshot = ProgressSnapshot(
        user_id=user_id,
        snapshot_date=date.today(),
        days_since_baseline=week_number * 7,
        **{f"{d}_current": domain_scores[d] for d in domain_scores},
        **{f"{d}_delta": deltas[d] for d in deltas}
    )
    
    return snapshot
```

### Step 4.2: Training Plan Re-Generator (Day 8 Logic)
**File:** `backend/app/core/algorithms/plan_regenerator.py`

```python
def regenerate_plan(user_id: int, week_snapshot: ProgressSnapshot):
    """
    After 7 days, adjust training plan based on progress
    """
    baseline = get_baseline(user_id)
    current_plan = get_active_plan(user_id)
    
    # Analyze each domain's progress
    domain_progress = {}
    for domain in DOMAINS:
        delta = getattr(week_snapshot, f"{domain.name}_delta")
        
        if delta >= 5:
            status = "improving"
        elif delta >= 2:
            status = "slow_progress"
        else:
            status = "stagnant"
        
        domain_progress[domain.name] = {
            "status": status,
            "delta": delta,
            "current_allocation": current_plan.get_allocation(domain.id)
        }
    
    # Re-allocate training time
    new_allocations = {}
    
    # STAGNANT domains get MORE time
    stagnant = [d for d, info in domain_progress.items() if info['status'] == 'stagnant']
    for domain in stagnant:
        new_allocations[domain] = min(info['current_allocation'] * 1.5, 40)  # Max 40%
    
    # IMPROVING domains get LESS time (they're working)
    improving = [d for d, info in domain_progress.items() if info['status'] == 'improving']
    for domain in improving:
        new_allocations[domain] = max(info['current_allocation'] * 0.7, 10)  # Min 10%
    
    # For STAGNANT domains, also check if difficulty is too high
    for domain in stagnant:
        tasks = get_domain_tasks(domain)
        avg_difficulty = mean([t.difficulty_level for t in tasks])
        if avg_difficulty > 3:
            # Reduce difficulty by 1-2 levels
            new_allocations[f"{domain}_difficulty"] = avg_difficulty - 1
    
    # Generate new task sequence
    new_sequence = build_task_sequence(new_allocations)
    
    # Deactivate old plan, create new one
    current_plan.is_active = False
    new_plan = TrainingPlan(
        user_id=user_id,
        target_domains=new_allocations,
        daily_task_sequence=new_sequence,
        based_on_assessment_id=baseline.id
    )
    
    return new_plan
```

### Step 4.3: Progress Visualization
**File:** `frontend/src/routes/progress/+page.svelte`

Show:
- Line chart: 6 domains over time (weekly snapshots)
- Improvement deltas with color coding
- Current training focus breakdown (pie chart)
- Next re-planning date countdown
- Session completion streak

---

## **PHASE 5: MS-Specific Features (Week 7)**

### Step 5.1: Fatigue-Aware Sessions
```svelte
<!-- frontend/src/routes/training/session/[id]/+page.svelte -->

<script>
  let fatigueDetected = false;
  
  async function checkFatigue(roundResults) {
    const response = await api.post('/sessions/check-fatigue', {
      round_results: roundResults
    });
    
    if (response.data.fatigue_detected) {
      fatigueDetected = true;
      // Show break prompt
      showBreakModal();
    }
  }
  
  function showBreakModal() {
    // Pause task
    // Show: "Take a 60-second break"
    // Countdown timer
    // Resume after break
  }
</script>
```

### Step 5.2: Micro-Breaks System
- Automatic break every 6 minutes
- Optional "I need a break" button always visible
- Break duration: 30-60 seconds
- Breathing exercise animation during break

### Step 5.3: MS Dashboard Insights
- Weekly fatigue patterns chart
- Best time of day for training (based on performance)
- Session completion rate vs fatigue correlation

---

## **PHASE 6: Admin/Clinician View (Week 8)**

### Features:
- Patient list
- Individual patient cognitive profiles
- Raw metrics export (CSV)
- Progress comparison charts
- Flags for declining performance

---

## **PHASE 7: Local Norms & Research Mode (Week 9-10)**

### Step 7.1: Healthy Controls Database
```sql
CREATE TABLE healthy_controls (
    id SERIAL PRIMARY KEY,
    age_group VARCHAR(20),  -- '18-25', '26-35', etc.
    education_level VARCHAR(50),
    baseline_data JSONB,
    
    -- Anonymous demographic
    gender VARCHAR(20),
    location VARCHAR(100)
);
```

### Step 7.2: Norm Comparison
```python
def compare_to_norms(user_score: float, domain: str, user_age: int) -> dict:
    """
    Compare user to age-matched healthy controls
    """
    age_group = get_age_group(user_age)
    norms = get_norms(domain, age_group)
    
    percentile = calculate_percentile(user_score, norms['distribution'])
    
    return {
        "percentile": percentile,
        "interpretation": get_interpretation(percentile),
        "sample_size": norms['n']
    }
```

---

## 🎯 **IMPLEMENTATION TIMELINE**

### Week 1: Setup
- [ ] Create SvelteKit project
- [ ] Update database schema
- [ ] Create all models

### Week 2: Baseline Tasks (Part 1)
- [ ] Working Memory (N-back)
- [ ] Attention (CPT)
- [ ] Scoring algorithms

### Week 3: Baseline Tasks (Part 2)
- [ ] Flexibility (Task Switching)
- [ ] Planning (Tower of Hanoi)
- [ ] Processing Speed (RT tests)
- [ ] Visual Scanning
- [ ] Baseline results page

### Week 4: Adaptive Engine
- [ ] Difficulty controller
- [ ] Fatigue detection
- [ ] Training plan generator

### Week 5: Training Sessions
- [ ] Training task components (reuse baseline with adaptive difficulty)
- [ ] Session flow management
- [ ] Real-time difficulty adjustment

### Week 6: Progress Tracking
- [ ] Weekly snapshots
- [ ] Re-planning algorithm
- [ ] Progress charts

### Week 7: MS Features
- [ ] Micro-breaks
- [ ] Fatigue-aware scheduling
- [ ] MS-specific insights

### Week 8: Admin View
- [ ] Patient management
- [ ] Data export

### Week 9-10: Research Features
- [ ] Norms database
- [ ] Comparison tools

---

## 📚 **NEXT IMMEDIATE STEPS**

1. **Start with SvelteKit setup** (30 min)
2. **Create database tables** (1 hour)
3. **Build first baseline task: N-Back** (4 hours)
4. **Test scoring algorithm** (2 hours)

**Ready to start?** 

Shall I begin with:
- **A)** SvelteKit project setup + file structure
- **B)** Database migration files
- **C)** First task implementation (N-Back)

Let me know and I'll start coding!

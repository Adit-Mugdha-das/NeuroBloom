# NeuroBloom - Cognitive Training Platform

## 📋 Table of Contents
- [Overview](#overview)
- [System Architecture](#system-architecture)
- [User Journey](#user-journey)
- [Cognitive Domains](#cognitive-domains)
- [Training System](#training-system)
- [Adaptive Difficulty Algorithm](#adaptive-difficulty-algorithm)
- [Session Structure](#session-structure)
- [Scoring & Metrics](#scoring--metrics)
- [Visualizations & Graphs](#visualizations--graphs)
- [Gamification Features](#gamification-features)
- [Performance Tracking](#performance-tracking)
- [Technical Implementation](#technical-implementation)

---

## Overview

**NeuroBloom** is a comprehensive cognitive training platform designed to assess and improve cognitive abilities across six key domains. The system uses adaptive algorithms to personalize training difficulty and provides detailed performance analytics.

### Core Features
- ✅ User authentication (Register/Login)
- ✅ Baseline cognitive assessment (6 domains)
- ✅ Personalized training plan generation
- ✅ Adaptive difficulty adjustment
- ✅ Performance tracking & visualization
- ✅ Badge achievement system
- ✅ Daily streak tracking with freeze mechanism
- ✅ Real-time progress monitoring
- ✅ Baseline vs Current performance comparison

---

## System Architecture

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL
- **ORM**: SQLModel
- **Authentication**: Token-based

### Frontend
- **Framework**: SvelteKit (Svelte 5)
- **Language**: TypeScript
- **Styling**: Custom CSS with gradients
- **API Communication**: Axios

### Key Models
1. **User** - Authentication and profile data
2. **BaselineAssessment** - Initial cognitive profile
3. **TrainingPlan** - Personalized training configuration
4. **TrainingSession** - Individual task completion records
5. **CognitiveTask** - Task definitions and metadata
6. **Badge** - Achievement tracking

---

## User Journey

### 1. Registration & Login
```
Register → Login → Dashboard
```
- **Registration**: Email + Password
- **Login**: Token-based authentication
- **Session Management**: Persistent login state

### 2. Baseline Assessment
```
Dashboard → Complete 6 Tasks → Calculate Baseline → Training Plan
```

**Six Baseline Tasks:**
1. **Working Memory** - N-back task
2. **Processing Speed** - Simple Reaction Time
3. **Attention** - Flanker task
4. **Cognitive Flexibility** - Task Switching
5. **Planning** - Tower of London
6. **Visual Scanning** - Visual Search

**Assessment Flow:**
1. User completes all 6 tasks (one per domain)
2. System calculates domain scores (0-100)
3. Overall cognitive score computed (average of 6 domains)
4. Baseline results page displays comprehensive analysis
5. Training plan generated based on baseline scores

### 3. Training Phase
```
Training Plan → Complete Sessions → Track Progress → View Analytics
```

**Session Structure:**
- Each session = **4 tasks**
- Tasks selected from different domains
- Task order randomized for variety
- Progress tracked: "1/4", "2/4", "3/4", "4/4"

### 4. Progress Monitoring
```
Dashboard → Training Page → Progress Page → Baseline Results
```

---

## Cognitive Domains

### 1. Working Memory 🧠
**What it is:** Ability to hold and manipulate information in mind temporarily.

**Tasks:**
- N-Back
- Digit Span
- Spatial Span
- Letter-Number Sequencing
- Operation Span

**Real-world applications:** Remembering phone numbers, following multi-step instructions, mental arithmetic

---

### 2. Attention 👁️
**What it is:** Ability to focus on relevant information while ignoring distractions.

**Tasks:**
- Flanker Task
- Go/No-Go
- Stroop Test

**Real-world applications:** Driving in traffic, studying in noisy environments, selective listening

---

### 3. Cognitive Flexibility 🔄
**What it is:** Ability to switch between different tasks or mental sets.

**Tasks:**
- Task Switching
- DCCS (Dimensional Change Card Sort)
- Plus-Minus Task

**Real-world applications:** Multitasking, adapting to new situations, problem-solving from different angles

---

### 4. Planning 🎯
**What it is:** Ability to organize steps to achieve a goal.

**Tasks:**
- Tower of London
- Twenty Questions
- Category Fluency

**Real-world applications:** Project management, trip planning, organizing daily schedules

---

### 5. Processing Speed ⚡
**What it is:** How quickly you can process and respond to information.

**Tasks:**
- Simple Reaction Time
- SDMT (Symbol Digit Modalities Test)
- Trail Making Test (Part A)
- Inspection Time
- Pattern Comparison

**Real-world applications:** Quick decision-making, sports performance, typing speed

---

### 6. Visual Scanning 🔍
**What it is:** Ability to quickly locate specific information in a visual field.

**Tasks:**
- Visual Search
- Cancellation Test
- Multiple Object Tracking

**Real-world applications:** Reading maps, finding items in a cluttered space, visual proofreading

---

## Training System

### Focus Area Classification

Based on baseline scores, domains are categorized into:

1. **Primary Focus** (2 domains)
   - Weakest areas
   - Highest training priority
   - More frequent task selection

2. **Secondary Focus** (2 domains)
   - Middle-tier performance
   - Moderate training frequency
   - Balanced improvement

3. **Maintenance** (2 domains)
   - Strongest areas
   - Periodic practice
   - Prevent skill degradation

### Task Selection Algorithm

Each training session selects 4 tasks:
```
1. Random domain selection (varied each session)
2. Task rotation within domain (cycling through available tasks)
3. Difficulty level based on current performance
4. No duplicate domains in single session
```

---

## Adaptive Difficulty Algorithm

### How It Works

**After Each Session (4 tasks complete):**
1. Evaluate performance per domain
2. Adjust difficulty based on accuracy
3. Update difficulty levels in training plan

### Difficulty Levels
- **Range**: 1 (easiest) to 10 (hardest)
- **Starting point**: Based on baseline score
  - Score < 50: Difficulty 3
  - Score 50-70: Difficulty 5
  - Score > 70: Difficulty 7

### Adjustment Rules

```python
if accuracy >= 85%:
    difficulty = min(current + 1, 10)  # Increase (max 10)
elif accuracy < 65%:
    difficulty = max(current - 1, 1)   # Decrease (min 1)
else:
    difficulty = current               # Maintain
```

**Logic:**
- ✅ **High accuracy (≥85%)** → Task too easy → Increase difficulty
- ⚠️ **Low accuracy (<65%)** → Task too hard → Decrease difficulty
- ✓ **Medium accuracy (65-85%)** → Optimal challenge → Maintain

### Difficulty Updates
- Updates happen **only after full session** (4 tasks complete)
- Each domain adjusted independently
- Changes persist across sessions
- Real-time display on Training page

---

## Session Structure

### Session Lifecycle

1. **Session Start**
   - 4 tasks assigned (random domains)
   - Difficulty set per domain
   - Progress: 0/4

2. **Task Completion**
   - User completes task
   - Score calculated
   - Progress updated (1/4, 2/4, 3/4)
   - Redirects to Training page

3. **Session Complete** (4/4 tasks done)
   - Difficulty adjustment calculated
   - Streak updated
   - Badges checked
   - Session counter incremented
   - New session initialized

### Key Metrics Per Task
- **Score**: Overall performance (0-100)
- **Accuracy**: Percentage correct responses
- **Reaction Time**: Average response speed (ms)
- **Consistency**: Standard deviation of reaction times
- **Errors**: Number of mistakes

---

## Scoring & Metrics

### Score Calculation

**Baseline Scores:**
- Calculated from 6 baseline tasks
- Domain scores: 0-100 scale
- Overall score: Average of 6 domains

**Training Scores:**
- Each task scored 0-100
- Domain average: Mean of all tasks in that domain
- Overall average: Mean across all domains

### Score Labels
```
≥ 80: Excellent (Green)
70-79: Good (Light Green)
60-69: Average (Orange)
50-59: Below Average (Light Red)
< 50: Needs Improvement (Red)
```

### Dashboard Metrics

1. **Total Sessions**
   - Count of completed 4-task sessions
   - NOT individual task count

2. **Total Tasks**
   - Count of individual tasks completed
   - 4 tasks = 1 session

3. **Active Domains**
   - Number of domains with training history
   - Maximum: 6 domains

4. **Last Training**
   - Date of most recent session

---

## Visualizations & Graphs

### 1. Radar Chart (Cognitive Profile)

**What it shows:**
- Hexagonal chart with 6 axes (one per domain)
- Each axis represents one cognitive domain
- Distance from center = performance score

**Two overlays:**
- **Baseline (Blue dashed line)**: Initial assessment scores
- **Current (Green solid line)**: Current training performance

**How to read:**
- Larger area = Better overall performance
- Symmetrical shape = Balanced cognitive profile
- Asymmetrical = Strength/weakness pattern
- Gap between lines = Improvement/decline

**Purpose:**
- Quick visual comparison
- Identify strongest/weakest domains
- Track progress over time

---

### 2. Domain Score Cards

**Display format:**
```
┌─────────────────────────┐
│  Working Memory         │
│                         │
│  [72.5]     [78.3]     │
│  Baseline   Current     │
└─────────────────────────┘
```

**Features:**
- Side-by-side comparison
- Color-coded by performance level
- Shows both baseline and current scores

---

### 3. Progress Bars

**Used for:**
- Baseline task completion (6/6 tasks)
- Session progress (1/4, 2/4, 3/4, 4/4)
- Domain difficulty levels (visual bars)

**Visual feedback:**
- Filled portion = Progress percentage
- Color = Performance level
- Animation on updates

---

### 4. Difficulty Visualization

**Training Page - Current Difficulty:**
```
Working Memory    [████████░░] Level 8/10
Attention         [██████░░░░] Level 6/10
Flexibility       [██░░░░░░░░] Level 2/10
Planning          [███████░░░] Level 7/10
Processing Speed  [█████████░] Level 9/10
Visual Scanning   [████░░░░░░] Level 4/10
```

**Features:**
- Real-time difficulty display
- Visual bar representation
- Numeric level (1-10)

---

### 5. Overall Score Comparison

**Two-card layout:**

**Baseline Score Card:**
- Initial assessment date
- Overall score (average)
- Performance label

**Current Score Card:**
- Latest performance
- Current overall score
- Improvement indicator (↑ 5.2 points)

---

## Gamification Features

### 1. Badge System

**Badge Categories:**

**A. Streak Badges**
```
🔥 Getting Started    - 3 day streak
🔥 On Fire           - 7 day streak
🔥 Unstoppable       - 14 day streak
🔥 Legendary         - 30 day streak
```

**B. Session Completion Badges**
```
🎯 First Steps       - 1 session
🎯 Getting Going     - 5 sessions
🎯 Committed         - 10 sessions
🎯 Dedicated         - 25 sessions
🎯 Expert            - 50 sessions
🎯 Master            - 100 sessions
```

**C. Domain Mastery Badges**
```
🧠 Working Memory Master
👁️ Attention Master
🔄 Flexibility Master
🎯 Planning Master
⚡ Speed Master
🔍 Visual Scanning Master
```

**Earning Criteria:**
- Average score ≥ 80 in domain
- Minimum 10 tasks completed in domain

**Display:**
- Notification on earning
- Badge gallery view
- Progress tracking

---

### 2. Streak Tracking

**Streak System:**
- Tracks consecutive days trained
- Encourages daily practice
- Includes freeze mechanism

**How it works:**

```
Day 1: First session → Streak = 1
Day 2: Train → Streak = 2
Day 3: Train → Streak = 3
Day 4: SKIP → Freeze used (if available) → Streak = 3
Day 6: Train → Streak = 4
Day 8: SKIP (no freeze) → Streak = 1 (reset)
```

**Streak Freeze:**
- **One-time protection** per streak
- Protects against 1 missed day
- Replenishes when streak breaks
- Visual indicator on dashboard

**Streak Metrics:**
- **Current Streak**: Consecutive days
- **Longest Streak**: Personal best
- **Total Training Days**: Lifetime count

---

## Performance Tracking

### 1. Performance Comparison API

**Endpoint:** `/api/training/training-session/performance-comparison/{user_id}`

**Returns:**
```json
{
  "comparison": {
    "working_memory": {
      "baseline": 65.5,
      "current": 72.3,
      "change": 6.8,
      "tasks_completed": 12
    },
    "attention": { ... },
    // ... other domains
  }
}
```

**Features:**
- Baseline vs current comparison
- Absolute change calculation
- Task count per domain
- Only includes domains with training data

---

### 2. Metrics Dashboard

**Endpoint:** `/api/training/training-session/metrics/{user_id}`

**Returns:**
```json
{
  "total_sessions": 5,
  "total_tasks": 20,
  "metrics_by_domain": {
    "working_memory": {
      "total_sessions": 5,
      "average_score": 72.3,
      "average_accuracy": 78.5,
      "current_difficulty": 6,
      "improvement": 8.2,
      "trend": "improving"
    }
  },
  "last_training_date": "2026-01-09T10:30:00"
}
```

**Trend Classification:**
- **Improving**: Change > +5 points
- **Stable**: Change between -5 and +5
- **Declining**: Change < -5 points

---

### 3. Session History

**Tracking:**
- Every task completion saved
- Timestamp recorded
- Performance metrics stored
- Difficulty levels logged

**Data retention:**
- Unlimited history
- Accessible via API
- Used for trend analysis

---

## Technical Implementation

### Cache Busting

**Problem:** Browser caching stale training data

**Solution:** Timestamp query parameters
```javascript
getPlan: async (userId) => {
  const response = await api.get(
    `/api/training/training-plan/${userId}?_t=${Date.now()}`
  );
  return response.data;
}
```

**Applied to:**
- Training plan retrieval
- Metrics fetching
- Performance comparison
- Next tasks recommendation

---

### Session Completion Tracking

**Implementation:**
```python
completed_tasks = plan.get_current_session_tasks_completed()
task_identifier = task_id if task_id else domain
if task_identifier not in completed_tasks:
    completed_tasks.append(task_identifier)
    plan.current_session_tasks_completed = json.dumps(completed_tasks)

session_complete = len(completed_tasks) >= 4

if session_complete:
    # Adjust difficulties
    # Update streak
    # Check badges
    # Reset session
    plan.total_sessions_completed += 1
    plan.current_session_tasks_completed = "[]"
```

---

### Difficulty Persistence

**Storage:**
```python
# JSON format in database
current_difficulty = {
    "working_memory": 6,
    "attention": 5,
    "flexibility": 3,
    "planning": 7,
    "processing_speed": 8,
    "visual_scanning": 4
}
```

**Updates:**
- Only after full session (4 tasks)
- Per-domain independent adjustment
- Persisted to database
- Retrieved for next session

---

### Baseline Recalculation

**Feature:** Allow users to retake baseline assessment

**Implementation:**
1. User clicks "Recalculate Baseline"
2. System fetches latest 6 baseline tasks
3. Recalculates domain scores
4. Updates `assessment_date` timestamp
5. Refreshes training plan if needed

**Use cases:**
- User improved and wants new baseline
- Initial assessment on bad day
- Progress milestone check

---

## Data Flow Diagrams

### Task Completion Flow
```
User completes task
    ↓
Submit results to backend
    ↓
Calculate score, accuracy, metrics
    ↓
Create TrainingSession record
    ↓
Add task_id to completed tasks array
    ↓
Check if session complete (4/4)
    ↓
YES → Adjust difficulties, update streak, check badges
    ↓
Redirect to Training page
    ↓
Page reloads fresh data (cache-busted)
    ↓
Display updated progress & difficulty
```

### Streak Update Flow
```
Session completes
    ↓
Get last_session_date from plan
    ↓
Calculate days_since_last
    ↓
If 0 days → Update timestamp, no streak change
If 1 day → Increment streak
If 2 days + freeze available → Use freeze, maintain streak
If 2+ days OR no freeze → Reset streak to 1
    ↓
Update longest_streak if current > longest
    ↓
Set last_session_date to now
```

---

## Key Features Summary

### ✅ Authentication System
- Secure registration and login
- Token-based sessions
- Persistent user state

### ✅ Baseline Assessment
- 6 domain evaluation
- Comprehensive scoring
- Visual results presentation
- Recalculation capability

### ✅ Adaptive Training
- Personalized task selection
- Dynamic difficulty adjustment
- Session-based structure
- Progress tracking

### ✅ Performance Analytics
- Baseline vs current comparison
- Radar chart visualization
- Domain-specific metrics
- Trend analysis

### ✅ Gamification
- Badge achievement system
- Streak tracking with freeze
- Progress milestones
- Motivational feedback

### ✅ User Experience
- Real-time progress updates
- Visual feedback
- Intuitive navigation
- Responsive design

---

## Future Enhancements (Potential)

### 📊 Advanced Analytics
- Weekly/Monthly progress reports
- Performance prediction
- Personalized insights
- Export data functionality

### 🎮 Enhanced Gamification
- Leaderboards
- Social features
- Custom challenges
- Reward tiers

### 🧪 New Task Types
- Additional cognitive domains
- Task variations
- Custom difficulty curves
- Specialized training modules

### 📱 Mobile Experience
- Native mobile app
- Offline mode
- Push notifications
- Mobile-optimized tasks

### 🤖 AI Integration
- Personalized recommendations
- Adaptive pacing
- Predictive difficulty
- Smart scheduling

---

## System Status

**Current Version:** 1.0  
**Status:** Production Ready ✅

**Core Features Implemented:**
- ✅ User authentication
- ✅ Baseline assessment (6 domains)
- ✅ Training plan generation
- ✅ Adaptive difficulty system
- ✅ Session tracking (4-task sessions)
- ✅ Streak tracking with freeze
- ✅ Badge system
- ✅ Performance comparison
- ✅ Visual analytics
- ✅ Cache-busting for fresh data
- ✅ Real-time progress updates
- ✅ Difficulty visualization

**Bug Fixes Applied:**
- ✅ Task completion tracking (commit order)
- ✅ Session counting (4 tasks = 1 session)
- ✅ Baseline recalculation date update
- ✅ Dashboard metric accuracy
- ✅ Streak freeze logic
- ✅ Cache invalidation

---

## Conclusion

NeuroBloom provides a comprehensive, scientifically-informed cognitive training platform with:
- **Personalized training** based on individual baselines
- **Adaptive difficulty** that grows with user performance
- **Rich analytics** to track improvement
- **Gamification** to maintain engagement
- **Robust tracking** of sessions and streaks

The system successfully combines cognitive science principles with modern web development to create an engaging, effective training experience.

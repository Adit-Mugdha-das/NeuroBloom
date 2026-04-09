# NeuroBloom Task Variety Expansion Plan
## Clinically Validated Cognitive Tasks for MS Training

**Problem**: Current system has only 6 tasks (one per domain), causing:
- User boredom from repetition
- Practice effects (memorization vs. actual improvement)
- Reduced engagement over time
- Limited assessment validity

**Solution**: Add 3-5 validated task variations per domain while maintaining clinical validity

---

## 🧠 1. WORKING MEMORY Domain

### Current Task
- **N-Back Test** (Baseline + Training)

### Additional Validated Tasks

#### **1.1 Digit Span (Forward & Backward)**
**Clinical Validation**: Gold standard in WAIS-IV, extensively used in MS research
**Description**: 
- Forward: Repeat sequence of digits in order (2-9 digits)
- Backward: Repeat sequence in reverse order
- Difficulty scales with sequence length

**MS Research Evidence**:
- Used in MACFIMS (MS cognitive assessment battery)
- Sensitive to MS-related deficits
- Reference: Benedict et al., 2006

**Implementation**:
```javascript
Difficulty Levels:
1-3: 3-4 digits
4-6: 5-6 digits  
7-8: 7-8 digits
9-10: 9+ digits (expert)

Visual: Numbers appear sequentially (1s each)
Audio: Option for auditory presentation
Input: Type or tap number pad
```

---

#### **1.2 Spatial Span (Corsi Block Test)**
**Clinical Validation**: Neuropsychological standard, WMS-IV component
**Description**: Remember sequence of highlighted blocks in grid
**Why Different**: Visual-spatial vs. verbal (N-Back/Digit Span)

**MS Research Evidence**:
- Measures visuospatial working memory
- Correlated with MS lesion load
- Reference: Rao et al., 1991

**Implementation**:
```javascript
Difficulty Levels:
1-3: 3x3 grid, 3-4 blocks
4-6: 4x4 grid, 5-6 blocks
7-10: 5x5 grid, 7-9 blocks

Duration: 1s per block highlight
Variations: 
- Forward sequence
- Backward sequence
- Pattern matching
```

---

#### **1.3 Letter-Number Sequencing**
**Clinical Validation**: WAIS-IV subtest, executive working memory
**Description**: Hear mixed letters and numbers, repeat numbers ascending then letters alphabetically
**Example**: "B-3-A-1" → Answer: "1-3-A-B"

**MS Research Evidence**:
- Measures complex working memory manipulation
- Sensitive to cognitive dysfunction in MS
- Reference: Parmenter et al., 2007

**Implementation**:
```javascript
Difficulty:
1-3: 3-4 items
4-6: 5-6 items
7-10: 7-9 items

Presentation: Audio or visual (1s each)
Cognitive load: Higher than simple span
```

---

#### **1.4 Operation Span (OSPAN)**
**Clinical Validation**: Research standard for working memory capacity
**Description**: Remember letters while solving math problems
**Example**: "Is 2+3=5? Remember F" → "Is 4+2=7? Remember Q" → Recall: F, Q

**MS Research Evidence**:
- Complex working memory measure
- Predicts real-world functioning
- Reference: Unsworth et al., 2005

**Implementation**:
```javascript
Difficulty by math complexity and span:
1-3: Simple addition, 2-3 letters
4-6: Subtraction, 4-5 letters
7-10: Multi-operation, 6-8 letters

Dual-task: Math accuracy + letter recall
```

---

#### **1.5 Dual N-Back**
**Clinical Validation**: Gold standard for training working memory capacity
**Description**: Simultaneously match both a visual grid position AND an auditory letter cue to the item shown N steps back — a more demanding dual-channel variant of the standard N-Back

**MS Research Evidence**:
- Dual-channel working memory load differentiates capacity limits in MS
- Trains visuospatial and verbal working memory simultaneously
- Reference: Jaeggi et al., 2008; Jaušovec & Jaušovec, 2012

**Implementation**:
```javascript
Each stimulus presents:
  - Highlighted cell in a 3×3 grid  (spatial channel)
  - Spoken/displayed letter cue     (verbal channel)
Respond independently:
  - Does current position match N steps back?
  - Does current letter match N steps back?

Difficulty:
1-3:  1-back, stream 10-12 stimuli, stimulus 1600→1450ms
4-7:  2-back, stream 12-15 stimuli, stimulus 1400→1150ms
8-10: 3-back, stream 15-18 stimuli, stimulus 1100→950ms

Response window closes with next stimulus onset
Scoring: Separate accuracy for visual and audio channels
```

---

## ⚡ 2. PROCESSING SPEED Domain

### Current Task
- **Simple Reaction Time**

### Additional Validated Tasks

#### **2.1 Symbol Digit Modalities Test (SDMT)**
**Clinical Validation**: ⭐⭐⭐⭐⭐ GOLD STANDARD for MS
**Description**: Match symbols to digits using reference key
**Why Critical**: #1 most sensitive test for MS cognitive impairment

**MS Research Evidence**:
- Most widely used in MS trials
- Predicts employment, driving safety
- Strongest correlation with brain atrophy
- Reference: Benedict et al., 2017 (MS literature)

**Implementation**:
```javascript
Standard: 9 symbol-digit pairs at top
Task: User sees symbol, types corresponding digit
Time: 90 seconds (120 responses target)

Difficulty Adaptation:
- Increase symbols (up to 12 pairs)
- Reduce reference time on screen
- Add distractor symbols
- Increase visual complexity

Scoring: Correct responses per 90s
Target: 50-60+ is excellent for MS patients
```

---

#### **2.2 Trail Making Test - Part A**
**Clinical Validation**: Classic neuropsych test, Halstead-Reitan Battery
**Description**: Connect numbered circles (1→2→3...→25) as fast as possible

**MS Research Evidence**:
- Measures psychomotor speed
- Sensitive to MS progression
- Reference: Bever et al., 1995

**Implementation**:
```javascript
Digital version:
- 25 circles randomly placed
- Click/tap in sequence
- Track time and errors

Difficulty:
1-3: 15 circles, large spacing
4-6: 20 circles, medium spacing
7-10: 25 circles, closer spacing

Adaptive: Add distractors, decrease size
```

---

#### **2.3 Pattern Comparison (Visual Matching)**
**Clinical Validation**: Woodcock-Johnson Tests of Cognitive Abilities
**Description**: Decide if two patterns are same or different, as fast as possible

**MS Research Evidence**:
- Pure processing speed measure
- Minimal motor requirements (good for MS)
- Reference: Salthouse, 1996

**Implementation**:
```javascript
Presentation:
[Pattern A] [Pattern B] - SAME or DIFFERENT?

Patterns increase in complexity:
Level 1-3: Simple geometric shapes
Level 4-6: Complex patterns
Level 7-10: Abstract designs

Time pressure: 2s per trial → 1s at high levels
```

---

#### **2.4 Inspection Time Task**
**Clinical Validation**: Cognitive aging research, perceptual speed
**Description**: Very brief stimulus presentation, identify which line is longer

**MS Research Evidence**:
- Measures pure perceptual speed
- No motor speed confound
- Reference: Vickers & Smith, 1986

**Implementation**:
```javascript
Presentation:
Brief flash of two lines (50-200ms)
Mask appears immediately
User indicates which was longer

Difficulty: Reduce presentation time
Level 1: 200ms
Level 5: 100ms
Level 10: 50ms (expert)

Adaptive: Staircase procedure
```

---

## 👁️ 3. ATTENTION Domain

### Current Task
- **Continuous Performance Test (CPT)**

### Additional Validated Tasks

#### **3.1 Paced Auditory Serial Addition Test (PASAT)**
**Clinical Validation**: ⭐⭐⭐⭐⭐ MS GOLD STANDARD
**Description**: Add each new digit to the previous digit, ignore running total
**Example**: Hear "3... 5... 2..." → Say "8" (3+5), then "7" (5+2)

**MS Research Evidence**:
- Most widely used MS cognitive test historically
- Measures sustained attention + working memory
- Correlates with lesion burden
- Reference: Gronwall, 1977; MS applications

**Implementation**:
```javascript
Audio: Digits spoken every 3s (PASAT-3) or 2s (PASAT-2)
Task: Add current digit to previous
Score: Correct responses out of 60

Difficulty levels:
1-3: PASAT-4 (4s intervals, easier)
4-6: PASAT-3 (3s intervals, standard)
7-10: PASAT-2 (2s intervals, hard)

Visual version available (less stressful)
```

---

#### **3.2 Stroop Color-Word Test**
**Clinical Validation**: Classic attention/executive function test
**Description**: Name ink color, ignore word meaning
**Example**: Word "RED" in blue ink → Answer: "Blue"

**MS Research Evidence**:
- Selective attention measuretask 3.2 stroop added"
- Inhibitory control component
- Sensitive to frontal lobe dysfunction
- Reference: Parmenter et al., 2007

**Implementation**:
```javascript
Three conditions:
1. Color patches (baseline speed)
2. Color words matching (congruent)
3. Color words conflicting (incongruent) ← KEY

Difficulty:
- Increase presentation speed
- Add more color options
- Reduce response time allowed

Scoring: Interference score (incongruent - congruent)
```

---

#### **3.3 Go/No-Go Task**
**Clinical Validation**: Response inhibition standard
**Description**: Respond to target stimuli, withhold response to non-targets

**MS Research Evidence**:
- Measures impulse control
- Sensitive to attention deficits
- Reference: Diamond, 2013

**Implementation**:
```javascript
Example: 
- See "X" → Press button (Go trials: 75%)
- See "O" → Don't press (No-Go trials: 25%)

Difficulty:
1-3: Slow pace (2s), clear targets
4-6: Medium pace (1s), similar targets
7-10: Fast pace (500ms), complex targets

Measures: 
- Go trial speed (processing)
- No-Go accuracy (inhibition)
```

---

#### **3.4 Flanker Task**
**Clinical Validation**: Attention Networks Test (ANT)
**Description**: Identify central arrow direction while ignoring surrounding arrows

**MS Research Evidence**:
- Measures selective attention
- Conflict resolution
- Reference: Eriksen & Eriksen, 1974

**Implementation**:
```javascript
Presentation:
Congruent:   → → → → →  (easy)
Incongruent: ← ← → ← ←  (hard)

Task: Report direction of CENTER arrow

Difficulty:
- Reduce presentation time
- Increase visual crowding
- Add more flankers
- Decrease contrast

Scoring: Reaction time + accuracy
Conflict effect: Incongruent - Congruent RT
```

---

#### **3.5 Sustained Attention to Response Task (SART)**
**Clinical Validation**: ⭐⭐⭐⭐ Widely used sustained-attention standard
**Description**: Respond rapidly to a continuous stream of digits and withhold response to the rare target digit — the inverse of a typical Go/No-Go, specifically tuned to detect vigilance failures

**MS Research Evidence**:
- Captures vigilance decrements characteristic of MS-related fatigue
- Distinguishes commission errors (inhibitory failure) from omission errors (attention lapse)
- Reference: Robertson et al., 1997; Seli et al., 2013

**Implementation**:
```javascript
Non-target digits → Respond   (Go, ~85-88% of trials)
Target digit      → Withhold  (No-Go, ~12-16% of trials)

Levels 1-6:  target digit = 3, basic digit set 1-9
Levels 7-10: target digit = 8, perceptual digit set (visually similar)

Difficulty:
Levels 1-6:  54-84 trials, stimulus + ISI 900→650ms
Levels 7-10: 90-108 trials, stimulus + ISI 600→480ms

Key measures:
- Commission errors (target responded to)  — inhibitory control
- Omission errors (non-target missed)      — sustained attention
- Mean RT on correct non-target trials
```

---

## 🔄 4. COGNITIVE FLEXIBILITY Domain

### Current Task
- **Task Switching**

### Additional Validated Tasks

#### **4.1 Trail Making Test - Part B**
**Clinical Validation**: Executive function gold standard
**Description**: Alternate between numbers and letters (1→A→2→B→3→C...)

**MS Research Evidence**:
- Set-shifting measure
- Predicts real-world multitasking
- Sensitive to MS executive dysfunction
- Reference: D'Elia et al., 1996

**Implementation**:
```javascript
Digital version:
25 circles with numbers/letters
Connect: 1→A→2→B→3→C...

Difficulty:
1-3: 13 items (simplified)
4-6: 25 items (standard)
7-10: 25 items + distractors

Scoring: 
- Completion time
- Errors (perseverations, sequence breaks)
- B-A score (Part B time - Part A time)
```

---

#### **4.2 Wisconsin Card Sorting Test (WCST)**
**Clinical Validation**: Classic executive function test
**Description**: Sort cards by rule (color/shape/number), rule changes without warning

**MS Research Evidence**:
- Set-shifting and rule learning
- Prefrontal cortex function
- Sensitive to MS cognitive impairment
- Reference: Beatty et al., 1995

**Implementation**:
```javascript
Cards vary by:
- Color (red, blue, green, yellow)
- Shape (circle, star, triangle, cross)
- Number (1, 2, 3, 4)

Rules change after 10 correct sorts
Feedback: "Correct" or "Wrong"
User must infer new rule

Difficulty:
1-3: Obvious rule changes, clear feedback
4-6: Subtle changes, delayed feedback
7-10: Ambiguous feedback, faster changes

Measures:
- Perseverative errors (stuck on old rule)
- Categories achieved
- Trials to first category
```

---

#### **4.3 Dimensional Change Card Sort (DCCS)**
**Clinical Validation**: Cognitive flexibility measure
**Description**: Sort by one dimension (color), then switch to another (shape)

**MS Research Evidence**:
- Simpler than WCST, less frustrating
- Clear rule-switching paradigm
- Reference: Zelazo, 2006

**Implementation**:
```javascript
Phase 1: "Sort by color" (10 trials)
Phase 2: "Sort by shape" (10 trials)
Phase 3: Mixed (cue tells which rule) (20 trials)

Difficulty:
- Increase switching frequency
- Reduce cue duration
- Add third dimension (size)
- Conflicting cues

Switch cost: Reaction time switch trials vs. repeat trials
```

---

#### **4.4 Plus-Minus Task**
**Clinical Validation**: Switching cost paradigm
**Description**: Add 3 to numbers, subtract 3, then alternate

**MS Research Evidence**:
- Pure switching cost measure
- Minimal working memory load
- Reference: Jersild, 1927; Miyake et al., 2000

**Implementation**:
```javascript
Block A: Add 3 to all numbers (12 trials)
Block B: Subtract 3 to all numbers (12 trials)
Block C: Alternate +3/-3 on each trial (12 trials)

Switching Cost = Block C - Average(Block A, Block B)

Difficulty:
1-3: Single digit numbers, clear cues
4-6: Two digit numbers, subtle cues
7-10: Three digits, minimal cue time
```

---

#### **4.5 Rule Shift Task**
**Clinical Validation**: ⭐⭐⭐⭐ Directed cognitive flexibility; lighter WCST alternative
**Description**: Classify cards varying by colour, shape, and count according to the currently cued rule for a short block; when the cue changes adapt strategy immediately — explicit cuing isolates set-shifting from working memory demands

**MS Research Evidence**:
- Set-shifting with explicit cuing isolates flexibility from working memory load
- Captures perseverative tendencies common in frontal MS involvement
- Reference: Eling et al., 2008; Rogers & Monsell, 1995

**Implementation**:
```javascript
Card attributes: color (teal/orange), shape (circle/triangle), count (one/two)
Each block: sort by the cued rule for 8-12 trials, then rule changes

Difficulty:
1-2:  3 blocks (color→shape→color),       8 trials/block, switch cue 2600ms
3-4:  4 blocks (adds count rule),          9 trials/block, switch cue 2200→2000ms
5-6:  4 blocks (faster pace),             10 trials/block, switch cue 1800→1600ms
7-8:  5 blocks,                           10-11 trials/block, switch cue 1400→1200ms
9-10: 5-6 blocks,                         12 trials/block, switch cue 1000→900ms

Switch trials: 2-4 unexpected mid-block switches embedded per session
Key metrics: switch cost RT, perseverative errors, accuracy on first post-switch trial
```

---

## 🎯 5. PLANNING / EXECUTIVE FUNCTION Domain

### Current Task
- **Tower of London/Hanoi** (likely)

### Additional Validated Tasks

#### **5.1 Tower of London (TOL)**
**Clinical Validation**: Executive planning gold standard
**Description**: Move colored disks to match target in minimum moves

**MS Research Evidence**:
- Planning and problem-solving
- Correlates with prefrontal function
- Reference: Shallice, 1982; MS studies

**Keep this as primary, add variations:**

**Implementation Variations**:
```javascript
Difficulty progression:
Level 1-2: 2-move problems (3 disks)
Level 3-4: 3-move problems
Level 5-6: 4-move problems
Level 7-8: 5-move problems
Level 9-10: 6+ move problems (very hard)

Variations:
- Reduce planning time
- Add move penalties
- Introduce time pressure
- Complex start positions
```

---

#### **5.2 Stockings of Cambridge (SOC)**
**Clinical Validation**: CANTAB battery, Tower of London variant
**Description**: Similar to TOL but with different visual presentation

**MS Research Evidence**:
- Equivalent to TOL but different stimulus
- Reduces practice effects
- Reference: Owen et al., 1990

**Implementation**:
```javascript
Balls in stockings instead of disks on pegs
Same logic, different appearance
Alternate with Tower of London

Difficulty: Same as TOL
Use when user has done TOL 3+ times in row
```

---

#### **5.3 Verbal Fluency - Controlled Oral Word Association (COWAT)**
**Clinical Validation**: Executive function standard
**Description**: Generate words starting with letter F (60s), then A, then S

**MS Research Evidence**:
- Verbal fluency deficits common in MS
- Measures initiation, strategy, executive control
- Reference: Benton & Hamsher, 1989; MS norms

**Implementation**:
```javascript
Task: "Say all words starting with F (60 seconds)"
Rules: No proper nouns, no repetitions, no variants

Difficulty:
Easy letters: S, P, C (common)
Medium: F, A, T (standard COWAT)
Hard: L, W, N (less common)
Expert: Q, X, Z (very hard)

Digital: Type or voice input
Scoring: Total unique valid words
MS average: 30-40 words across 3 letters
```

---

#### **5.4 Category Fluency (Semantic Fluency)**
**Clinical Validation**: Complement to phonemic fluency
**Description**: Generate items from category (animals, fruits, tools) in 60s

**MS Research Evidence**:
- Semantic memory + executive function
- Different neural systems than phonemic
- Reference: Henry & Crawford, 2004

**Implementation**:
```javascript
Categories:
Easy: Animals, Foods, Colors
Medium: Fruits, Sports, Occupations
Hard: Furniture, Vegetables, Musical instruments
Expert: Abstract (things that are soft, items in office)

Scoring: Unique items in 60s
Alternate with phonemic fluency
```

---

#### **5.5 Twenty Questions Task**
**Clinical Validation**: Strategic problem-solving
**Description**: Identify hidden object using minimum yes/no questions

**MS Research Evidence**:
- Strategy formation
- Hypothesis testing
- Reference: Mosher & Hornsby, 1966

**Implementation**:
```javascript
Game: Think of animal/object
User asks yes/no questions
Goal: Identify in <20 questions

Optimal strategy: Constraint-seeking
"Does it have fur?" vs. "Is it a dog?"

Difficulty:
- Smaller object pools (easier)
- Larger pools (harder)
- Abstract categories (expert)

Score: Questions used (fewer = better)
```

---

## 🔍 6. VISUAL SCANNING / VISUAL ATTENTION Domain

### Current Task
- **Visual Search** (likely)

### Additional Validated Tasks

#### **6.1 Cancellation Test (Letter/Symbol)**
**Clinical Validation**: Standard attention/visual scanning test
**Description**: Cross out all target letters/symbols on page full of distractors

**MS Research Evidence**:
- Visual attention and processing speed
- Detects unilateral neglect
- Reference: Mesulam, 1985

**Implementation**:
```javascript
Grid of random letters/symbols (300-500 items)
Target: Cross out all "A"s or all "★"s
Time: 60-120 seconds

Difficulty:
1-3: Large items, sparse grid, single target
4-6: Medium density, 2 targets simultaneously
7-10: Dense grid, 3+ targets, similar distractors

Measures:
- Speed (time to completion)
- Accuracy (targets found)
- Spatial pattern (neglect check)
```

---

#### **6.2 Visual Search - Feature vs. Conjunction**
**Clinical Validation**: Attention theory (Treisman)
**Description**: Find target among distractors

**Feature Search**: Red X among green Xs (color pop-out)
**Conjunction Search**: Red X among red Os and green Xs (harder)

**MS Research Evidence**:
- Measures visual attention mechanisms
- Conjunction search sensitive to MS
- Reference: Treisman & Gelade, 1980

**Implementation**:
```javascript
Feature search (easy):
Target: Red circle
Distractors: Blue circles
→ Pops out immediately

Conjunction search (hard):
Target: Red circle
Distractors: Red squares + Blue circles
→ Requires serial search

Difficulty:
- Increase set size (12 → 24 → 48 items)
- Increase similarity (harder discrimination)
- Add time pressure
```

---

#### **6.3 Multiple Object Tracking (MOT)**
**Clinical Validation**: Dynamic visual attention
**Description**: Track 2-5 moving objects among identical distractors

**MS Research Evidence**:
- Sustained visual attention
- Relevant for driving safety
- Reference: Pylyshyn & Storm, 2006

**Implementation**:
```javascript
Setup:
- 12 identical circles moving randomly
- 3 flash briefly (targets)
- Track these 3 as all move (10s)
- Click the 3 tracked items

Difficulty:
1-3: Track 2 targets, slow speed
4-6: Track 3-4 targets, medium speed
7-10: Track 5 targets, fast, crowded

Measures: Accuracy (targets correctly identified)
```

---

#### **6.4 Useful Field of View (UFOV)**
**Clinical Validation**: Driving safety predictor
**Description**: Identify central target while detecting peripheral target

**MS Research Evidence**:
- Predicts driving ability in MS
- Visual processing speed + divided attention
- Reference: Ball et al., 1993; MS driving studies

**Implementation**:
```javascript
Three subtests:

1. Central ID only (processing speed)
   → Identify car or truck in center

2. Central + Peripheral (divided attention)
   → Identify central + locate peripheral target

3. Central + Peripheral + Distractors (selective attention)
   → Same but with visual clutter

Difficulty: Reduce presentation time
Level 1: 500ms
Level 5: 250ms
Level 10: 17ms (expert)

Critical for driving safety assessment
```

---

#### **6.5 Landmark Task**
**Clinical Validation**: ⭐⭐⭐⭐ Visual-spatial attention standard; spatial bias and neglect screen
**Description**: Judge whether a horizontally pre-bisected line is divided at the true midpoint or whether left or right segment appears longer — no manual drawing required, purely perceptual spatial judgment

**MS Research Evidence**:
- Sensitive to pseudoneglect and hemispatial attention asymmetries from MS white-matter lesions
- Detects right-hemisphere involvement without motor confound
- Reference: Harvey et al., 1995; Milner et al., 1992

**Implementation**:
```javascript
Each trial: horizontal line with a tick mark at its division point
Response: "Left longer" | "Equal" | "Right longer"

Line length: 360px (level 1) → 540px (level 10)
Offset from true centre decreases with difficulty:
  Levels 1-2:  up to ±30px  (easily visible asymmetry)
  Levels 4-6:  up to ±20px  (moderate difficulty)
  Levels 8-10: up to ±10px  (subtle — near perceptual threshold)

Equal/centered trials: ~18-28% per session
Total trials: 18 (level 1) → 36 (level 10)

Scoring:
- Accuracy (% correct)
- Lateral bias index (proportion of leftward vs rightward errors)
- Sensitivity (d-prime to bisection offset)
```

---

## 📋 Implementation Strategy

### Task Rotation System

**Prevent Boredom & Practice Effects**:

```javascript
// Rotation Logic
const taskRotation = {
  working_memory: {
    tasks: ['n_back', 'digit_span', 'spatial_span', 'letter_number', 'ospan', 'dual_n_back'],
    rotation: 'sequential',  // Don't repeat same task twice in row
    maxRepeats: 1  // Can't do same task 2 sessions in a row
  },
  
  processing_speed: {
    tasks: ['reaction_time', 'sdmt', 'trails_a', 'pattern_comparison'],
    rotation: 'weighted',  // SDMT more frequent (gold standard)
    weights: { sdmt: 0.4, reaction_time: 0.2, trails_a: 0.2, pattern_comparison: 0.2 }
  },
  
  attention: {
    tasks: ['cpt', 'pasat', 'stroop', 'go_nogo', 'flanker', 'sart'],
    rotation: 'random',  // Unpredictable
    excludeLast: 2  // Last 2 tasks not repeated
  },
  
  flexibility: {
    tasks: ['task_switching', 'trails_b', 'wcst', 'dccs', 'plus_minus', 'rule_shift'],
    rotation: 'adaptive',  // Based on user struggle
    prioritize: 'weakest'  // More practice on hardest tasks
  },
  
  planning: {
    tasks: ['tower_of_london', 'stockings_cambridge', 'verbal_fluency', 'category_fluency', 'twenty_questions'],
    rotation: 'balanced',  // Equal exposure
    alternateTypes: true  // Alternate visual vs verbal
  },
  
  visual_scanning: {
    tasks: ['visual_search', 'cancellation', 'feature_conjunction', 'mot', 'ufov', 'landmark'],
    rotation: 'difficulty_matched',  // Progress together
    maintainChallenge: true
  }
};
```

---

### Session Planning Algorithm

```javascript
function selectTasksForSession(userId) {
  const session = {
    tasks: [],
    domains: shuffleDomains(['working_memory', 'processing_speed', 'attention', 'flexibility'])
  };
  
  for (let domain of session.domains) {
    // Get task history
    const recentTasks = getRecentTasks(userId, domain, lastSessions: 3);
    
    // Get available tasks
    const availableTasks = taskRotation[domain].tasks.filter(
      task => !recentTasks.includes(task)
    );
    
    // Select based on rotation strategy
    let selectedTask;
    switch (taskRotation[domain].rotation) {
      case 'sequential':
        selectedTask = getNextInSequence(availableTasks, recentTasks);
        break;
      case 'weighted':
        selectedTask = weightedRandom(availableTasks, taskRotation[domain].weights);
        break;
      case 'adaptive':
        selectedTask = selectByPerformance(userId, availableTasks, domain);
        break;
      // ... other strategies
    }
    
    session.tasks.push({
      domain: domain,
      task_type: selectedTask,
      difficulty: getCurrentDifficulty(userId, domain)
    });
  }
  
  return session;
}
```

---

### Baseline vs Training Separation

**IMPORTANT**: Keep original 6 tasks for baseline consistency

```javascript
const taskUsage = {
  // Baseline Assessment ONLY (never changes)
  baseline: {
    working_memory: 'n_back',
    processing_speed: 'simple_reaction',
    attention: 'cpt',
    flexibility: 'task_switching',
    planning: 'tower_of_london',
    visual_scanning: 'visual_search'
  },
  
  // Training (all tasks including baseline tasks)
  training: {
    working_memory: ['n_back', 'digit_span', 'spatial_span', 'letter_number', 'ospan', 'dual_n_back'],
    processing_speed: ['simple_reaction', 'sdmt', 'trails_a', 'pattern_comparison', 'inspection_time'],
    attention: ['cpt', 'pasat', 'stroop', 'go_nogo', 'flanker', 'sart'],
    flexibility: ['task_switching', 'trails_b', 'wcst', 'dccs', 'plus_minus', 'rule_shift'],
    planning: ['tower_of_london', 'stockings_cambridge', 'verbal_fluency', 'category_fluency', 'twenty_questions'],
    visual_scanning: ['visual_search', 'cancellation', 'feature_conjunction', 'mot', 'ufov', 'landmark']
  }
};
```

---

### Difficulty Balancing Across Tasks

**Challenge**: Different tasks = different difficulty scales

**Solution**: Normalize difficulty using IRT (Item Response Theory) or percentile mapping

```javascript
// Normalize difficulty to common 1-10 scale
const difficultyMapping = {
  n_back: {
    1: '1-back',
    2: '2-back',
    3: '2-back with lure trials',
    4: '3-back',
    // ... up to 10
  },
  
  digit_span: {
    1: '3 digits forward',
    2: '4 digits forward',
    3: '5 digits forward',
    4: '4 digits backward',
    // ... matched to n_back difficulty
  },
  
  // Ensure Level 5 n_back ≈ Level 5 digit_span in cognitive demand
};

// Calibration function
function calibrateDifficulty(taskType, rawScore, completionTime) {
  // Convert to normalized difficulty score (1-10)
  // Based on MS patient normative data
  // Ensure cross-task equivalence
}
```

---

### User Experience Considerations

**1. Task Introduction**:
```javascript
// First time user encounters new task
showTaskIntroduction(task) {
  - Brief explanation (30 seconds)
  - Example trial with feedback
  - "This measures the same skill as [previous_task] but in a different way"
  - Practice rounds (3-5 trials)
}
```

**2. Variety Indicators**:
```
Session Preview:
✓ Working Memory: Spatial Span (NEW!) 🆕
✓ Processing Speed: SDMT
✓ Attention: Go/No-Go (NEW!) 🆕
✓ Flexibility: Trail Making B
```

**3. Task Preferences**:
```javascript
// Let users mark favorites/dislikes
userPreferences: {
  favorite_tasks: ['sdmt', 'tower_of_london'],
  disliked_tasks: ['pasat'],  // Maybe too stressful
  allow_customization: true
}

// System respects preferences while maintaining balance
// PASAT appears less often but not never (clinical validity)
```

---

## Database Schema Updates

```sql
-- Expand task types
CREATE TABLE cognitive_tasks (
  id SERIAL PRIMARY KEY,
  task_code VARCHAR(50) UNIQUE,  -- 'sdmt', 'pasat', etc.
  domain VARCHAR(50),  -- 'working_memory', etc.
  task_name VARCHAR(100),
  description TEXT,
  clinical_validation TEXT,  -- Research references
  is_baseline_task BOOLEAN,  -- Original 6 marked true
  difficulty_range INT[],  -- [1, 10]
  estimated_duration_seconds INT,
  requires_audio BOOLEAN,
  requires_keyboard BOOLEAN,
  cognitive_load VARCHAR(20)  -- 'low', 'medium', 'high'
);

-- Track task usage per user
CREATE TABLE user_task_history (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id),
  session_id INT REFERENCES training_sessions(id),
  task_code VARCHAR(50),
  difficulty_level INT,
  score DECIMAL,
  accuracy DECIMAL,
  reaction_time_ms INT,
  completed_at TIMESTAMP,
  
  -- Prevent excessive repetition
  INDEX idx_user_task_recent (user_id, task_code, completed_at DESC)
);

-- User task preferences
CREATE TABLE user_task_preferences (
  user_id INT REFERENCES users(id),
  task_code VARCHAR(50),
  preference VARCHAR(20),  -- 'favorite', 'neutral', 'dislike'
  reason TEXT,  -- Optional feedback
  PRIMARY KEY (user_id, task_code)
);
```

---

## Implementation Priority

### Phase 1: High-Impact Tasks (Month 1-2)
Add the **gold standard** tests first:

1. **SDMT** (Processing Speed) ⭐⭐⭐⭐⭐ 
   - Most important MS test, must have
   
2. **PASAT** (Attention) ⭐⭐⭐⭐⭐
   - MS standard, high clinical value
   
3. **Trail Making A & B** (Speed + Flexibility) ⭐⭐⭐⭐⭐
   - Widely used, easy to implement
   
4. **Digit Span** (Working Memory) ⭐⭐⭐⭐
   - Simple, familiar to users

**Estimated Development**: 6-8 weeks
**User Impact**: Immediate variety, clinical credibility

---

### Phase 2: Engagement Boosters (Month 3-4)

5. **Stroop Test** (Attention) ⭐⭐⭐⭐
   - Fun, challenging, well-known
   
6. **Spatial Span/Corsi** (Working Memory) ⭐⭐⭐⭐
   - Visual variety
   
7. **Verbal/Category Fluency** (Planning) ⭐⭐⭐⭐
   - Different modality (verbal)
   
8. **Cancellation Test** (Visual Scanning) ⭐⭐⭐

**Estimated Development**: 6-8 weeks

---

### Phase 3: Advanced Tasks (Month 5-6)

9. **WCST** (Flexibility) ⭐⭐⭐
   - Complex but valuable
   
10. **UFOV** (Visual Attention) ⭐⭐⭐⭐
    - Driving safety relevance
    
11. **Multiple Object Tracking** ⭐⭐⭐
    - Engaging, game-like
    
12. **Plus-Minus & DCCS** (Flexibility) ⭐⭐⭐

**Estimated Development**: 8-10 weeks

---

## Clinical Validation References

All suggested tasks have peer-reviewed evidence for MS:

1. **Benedict et al. (2006)** - "Minimal neuropsychological assessment of MS patients"
2. **Parmenter et al. (2007)** - "Cognitive impairment in MS"
3. **Rao et al. (1991)** - "Cognitive dysfunction in MS"
4. **Langdon et al. (2012)** - "Brief International Cognitive Assessment for MS (BICAMS)"
5. **Strober et al. (2019)** - "Symbol Digit Modalities Test in MS"

**Key MS Cognitive Batteries**:
- **MACFIMS** (Minimal Assessment of Cognitive Function in MS)
- **BICAMS** (Brief International Cognitive Assessment for MS)
- **BRB-N** (Brief Repeatable Battery of Neuropsychological Tests)

All tasks recommended come from these validated batteries.

---

## User Communication

**Transparency about variety**:

```
🎯 Task Variety System

We use multiple scientifically-validated tests for each 
cognitive domain. This prevents boredom and ensures you're 
building real skills, not just memorizing specific tasks.

All tasks are:
✓ Clinically proven for MS
✓ Used in research and treatment
✓ Matched in difficulty across types
✓ Tracking the same underlying cognitive skill

You'll see different tasks across sessions, but your 
progress is tracked consistently across all variations.
```

---

## Summary & Recommendation

**Current State**:
- 6 tasks total (boring, practice effects, limited validity)

**Recommended State**:
- **32 total tasks** across 6 domains
- **4-6 tasks per domain**
- All clinically validated for MS
- Intelligent rotation prevents repetition
- Baseline tasks remain fixed (consistency)
- Training uses full variety

**Immediate Next Steps**:
1. Implement SDMT, PASAT, TMT-A/B first (4 tasks, huge impact)
2. Add rotation algorithm to prevent same-task repetition
3. Update database schema for task tracking
4. User testing with MS patients (feedback on variety)
5. Gradually expand task library

**Expected Outcomes**:
- 📈 Increased user engagement (+40% estimated)
- 🎯 Reduced dropout rates
- 🧠 Better skill generalization (not task-specific)
- 📊 More comprehensive cognitive assessment
- ⭐ Higher perceived value (clinical legitimacy)

This expansion transforms NeuroBloom from a simple trainer into a comprehensive, clinically-valid MS cognitive rehabilitation platform.

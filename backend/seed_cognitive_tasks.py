"""
Seed cognitive_tasks table with all task variants for task rotation system.
Based on TASK_VARIETY_EXPANSION.md specifications.

Run this script to populate the database with all available cognitive tasks.
"""

from sqlmodel import Session, select
from app.core.config import engine
from app.models.cognitive_task import CognitiveTask

def seed_cognitive_tasks():
    """Populate cognitive_tasks table with all task variants"""
    
    tasks = [
        # ============================================
        # WORKING MEMORY DOMAIN
        # ============================================
        {
            "task_code": "n_back",
            "domain": "working_memory",
            "task_name": "N-Back Test",
            "description": "Remember items from N positions back in sequence",
            "clinical_validation": "Gold standard working memory test. Used extensively in MS research.",
            "is_baseline_task": True,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 180,
            "requires_audio": False,
            "requires_keyboard": True,
            "cognitive_load": "high",
            "instructions": "Press SPACE when the current item matches the one N positions back."
        },
        {
            "task_code": "digit_span",
            "domain": "working_memory",
            "task_name": "Digit Span (Forward & Backward)",
            "description": "Remember and repeat sequences of digits in order or reverse",
            "clinical_validation": "WAIS-IV gold standard. Used in MACFIMS MS battery. Reference: Benedict et al., 2006",
            "is_baseline_task": False,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 120,
            "requires_audio": True,
            "requires_keyboard": True,
            "cognitive_load": "medium",
            "instructions": "Remember the sequence of digits and type them back in order (forward) or reverse (backward)."
        },
        {
            "task_code": "spatial_span",
            "domain": "working_memory",
            "task_name": "Spatial Span (Corsi Block Test)",
            "description": "Remember sequence of highlighted blocks in grid",
            "clinical_validation": "WMS-IV component. Visuospatial working memory. Reference: Rao et al., 1991",
            "is_baseline_task": False,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 120,
            "requires_audio": False,
            "requires_keyboard": False,
            "cognitive_load": "medium",
            "instructions": "Watch the blocks light up, then click them in the same order."
        },
        {
            "task_code": "letter_number_sequencing",
            "domain": "working_memory",
            "task_name": "Letter-Number Sequencing",
            "description": "Hear mixed letters and numbers, repeat numbers ascending then letters alphabetically",
            "clinical_validation": "WAIS-IV subtest. Complex working memory manipulation. Reference: Parmenter et al., 2007",
            "is_baseline_task": False,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 150,
            "requires_audio": True,
            "requires_keyboard": True,
            "cognitive_load": "high",
            "instructions": "Example: B-3-A-1 → Answer: 1-3-A-B (numbers first ascending, then letters alphabetically)."
        },
        {
            "task_code": "operation_span",
            "domain": "working_memory",
            "task_name": "Operation Span (OSPAN)",
            "description": "Remember letters while solving math problems",
            "clinical_validation": "Research standard for working memory capacity. Reference: Unsworth et al., 2005",
            "is_baseline_task": False,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 180,
            "requires_audio": False,
            "requires_keyboard": True,
            "cognitive_load": "high",
            "instructions": "Solve math problems while remembering letters. Example: 2+3=5? Remember F → 4+2=7? Remember Q → Recall: F, Q"
        },
        
        # ============================================
        # PROCESSING SPEED DOMAIN
        # ============================================
        {
            "task_code": "simple_reaction",
            "domain": "processing_speed",
            "task_name": "Simple Reaction Time",
            "description": "Press button as quickly as possible when stimulus appears",
            "clinical_validation": "Basic processing speed measure",
            "is_baseline_task": True,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 90,
            "requires_audio": False,
            "requires_keyboard": True,
            "cognitive_load": "low",
            "instructions": "Press SPACE as quickly as possible when you see the target."
        },
        {
            "task_code": "sdmt",
            "domain": "processing_speed",
            "task_name": "Symbol Digit Modalities Test (SDMT)",
            "description": "Match symbols to digits using reference key",
            "clinical_validation": "⭐⭐⭐⭐⭐ MS GOLD STANDARD. Most sensitive test for MS cognitive impairment. Reference: Benedict et al., 2017",
            "is_baseline_task": False,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 90,
            "requires_audio": False,
            "requires_keyboard": True,
            "cognitive_load": "medium",
            "instructions": "Use the reference key to match symbols to their corresponding digits. Work as quickly and accurately as possible."
        },
        {
            "task_code": "trails_a",
            "domain": "processing_speed",
            "task_name": "Trail Making Test - Part A",
            "description": "Connect numbered circles (1→2→3...→25) as fast as possible",
            "clinical_validation": "Halstead-Reitan Battery. Psychomotor speed. Reference: Bever et al., 1995",
            "is_baseline_task": False,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 120,
            "requires_audio": False,
            "requires_keyboard": False,
            "cognitive_load": "low",
            "instructions": "Click the circles in numerical order as quickly as possible: 1→2→3→4..."
        },
        {
            "task_code": "pattern_comparison",
            "domain": "processing_speed",
            "task_name": "Pattern Comparison",
            "description": "Decide if two patterns are same or different, as fast as possible",
            "clinical_validation": "Woodcock-Johnson Tests. Pure processing speed. Reference: Salthouse, 1996",
            "is_baseline_task": False,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 120,
            "requires_audio": False,
            "requires_keyboard": True,
            "cognitive_load": "low",
            "instructions": "Quickly determine if two patterns are SAME or DIFFERENT."
        },
        {
            "task_code": "inspection_time",
            "domain": "processing_speed",
            "task_name": "Inspection Time Task",
            "description": "Very brief stimulus presentation, identify which line is longer",
            "clinical_validation": "Perceptual speed measure. No motor speed confound. Reference: Vickers & Smith, 1986",
            "is_baseline_task": False,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 90,
            "requires_audio": False,
            "requires_keyboard": True,
            "cognitive_load": "low",
            "instructions": "Two lines flash briefly. Indicate which line was longer (left or right)."
        },
        
        # ============================================
        # ATTENTION DOMAIN
        # ============================================
        {
            "task_code": "cpt",
            "domain": "attention",
            "task_name": "Continuous Performance Test",
            "description": "Maintain focus and respond to infrequent target stimuli",
            "clinical_validation": "Sustained attention gold standard",
            "is_baseline_task": True,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 180,
            "requires_audio": False,
            "requires_keyboard": True,
            "cognitive_load": "medium",
            "instructions": "Press SPACE only when you see the target letter X. Ignore all other letters."
        },
        {
            "task_code": "pasat",
            "domain": "attention",
            "task_name": "Paced Auditory Serial Addition Test (PASAT)",
            "description": "Add each new digit to the previous digit, ignore running total",
            "clinical_validation": "⭐⭐⭐⭐⭐ MS GOLD STANDARD. Sustained attention + working memory. Reference: Gronwall, 1977",
            "is_baseline_task": False,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 180,
            "requires_audio": True,
            "requires_keyboard": True,
            "cognitive_load": "high",
            "instructions": "Add each new digit to the PREVIOUS digit (not the running total). Example: hear 3...5...2 → say 8 (3+5), then 7 (5+2)."
        },
        {
            "task_code": "stroop",
            "domain": "attention",
            "task_name": "Stroop Color-Word Test",
            "description": "Name ink color, ignore word meaning",
            "clinical_validation": "Classic selective attention test. Reference: Parmenter et al., 2007",
            "is_baseline_task": False,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 120,
            "requires_audio": False,
            "requires_keyboard": True,
            "cognitive_load": "medium",
            "instructions": "Name the INK COLOR, not the word. Example: RED in blue ink → Answer: Blue"
        },
        {
            "task_code": "go_nogo",
            "domain": "attention",
            "task_name": "Go/No-Go Task",
            "description": "Respond to target stimuli, withhold response to non-targets",
            "clinical_validation": "Response inhibition standard. Reference: Diamond, 2013",
            "is_baseline_task": False,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 120,
            "requires_audio": False,
            "requires_keyboard": True,
            "cognitive_load": "medium",
            "instructions": "Press button when you see X (Go trials), but don't press for O (No-Go trials)."
        },
        {
            "task_code": "flanker",
            "domain": "attention",
            "task_name": "Flanker Task",
            "description": "Identify central arrow direction while ignoring surrounding arrows",
            "clinical_validation": "Attention Networks Test (ANT). Reference: Eriksen & Eriksen, 1974",
            "is_baseline_task": False,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 120,
            "requires_audio": False,
            "requires_keyboard": True,
            "cognitive_load": "medium",
            "instructions": "Report the direction of the CENTER arrow only. Ignore the surrounding arrows."
        },
        
        # ============================================
        # FLEXIBILITY DOMAIN
        # ============================================
        {
            "task_code": "task_switching",
            "domain": "flexibility",
            "task_name": "Task Switching",
            "description": "Alternate between different task rules on cue",
            "clinical_validation": "Set-shifting paradigm",
            "is_baseline_task": True,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 150,
            "requires_audio": False,
            "requires_keyboard": True,
            "cognitive_load": "high",
            "instructions": "Follow the current rule (shown at top). Rules change between trials."
        },
        {
            "task_code": "trails_b",
            "domain": "flexibility",
            "task_name": "Trail Making Test - Part B",
            "description": "Alternate between numbers and letters (1→A→2→B→3→C...)",
            "clinical_validation": "⭐⭐⭐⭐⭐ Executive function gold standard. Reference: D'Elia et al., 1996",
            "is_baseline_task": False,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 180,
            "requires_audio": False,
            "requires_keyboard": False,
            "cognitive_load": "high",
            "instructions": "Alternate between numbers and letters: 1→A→2→B→3→C..."
        },
        {
            "task_code": "wcst",
            "domain": "flexibility",
            "task_name": "Wisconsin Card Sorting Test (WCST)",
            "description": "Sort cards by rule (color/shape/number), rule changes without warning",
            "clinical_validation": "Classic executive function test. Reference: Beatty et al., 1995",
            "is_baseline_task": False,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 300,
            "requires_audio": False,
            "requires_keyboard": False,
            "cognitive_load": "high",
            "instructions": "Sort cards by the hidden rule. Use feedback to discover the rule. The rule changes periodically."
        },
        {
            "task_code": "dccs",
            "domain": "flexibility",
            "task_name": "Dimensional Change Card Sort (DCCS)",
            "description": "Sort by one dimension (color), then switch to another (shape)",
            "clinical_validation": "Cognitive flexibility measure. Reference: Zelazo, 2006",
            "is_baseline_task": False,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 150,
            "requires_audio": False,
            "requires_keyboard": False,
            "cognitive_load": "medium",
            "instructions": "Sort cards by the dimension shown (COLOR or SHAPE)."
        },
        {
            "task_code": "plus_minus",
            "domain": "flexibility",
            "task_name": "Plus-Minus Task",
            "description": "Add 3 to numbers, subtract 3, then alternate",
            "clinical_validation": "Pure switching cost measure. Reference: Jersild, 1927; Miyake et al., 2000",
            "is_baseline_task": False,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 120,
            "requires_audio": False,
            "requires_keyboard": True,
            "cognitive_load": "medium",
            "instructions": "Follow the operation shown: +3 or -3. In mixed blocks, alternate between operations."
        },
        
        # ============================================
        # PLANNING DOMAIN
        # ============================================
        {
            "task_code": "tower_of_london",
            "domain": "planning",
            "task_name": "Tower of London",
            "description": "Move colored disks to match target in minimum moves",
            "clinical_validation": "Executive planning gold standard. Reference: Shallice, 1982",
            "is_baseline_task": True,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 180,
            "requires_audio": False,
            "requires_keyboard": False,
            "cognitive_load": "high",
            "instructions": "Rearrange the disks to match the target configuration in the minimum number of moves."
        },
        {
            "task_code": "stockings_cambridge",
            "domain": "planning",
            "task_name": "Stockings of Cambridge (SOC)",
            "description": "Tower of London variant with balls in stockings",
            "clinical_validation": "CANTAB battery. Reference: Owen et al., 1990",
            "is_baseline_task": False,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 180,
            "requires_audio": False,
            "requires_keyboard": False,
            "cognitive_load": "high",
            "instructions": "Move the balls to match the target pattern in the minimum number of moves."
        },
        {
            "task_code": "verbal_fluency",
            "domain": "planning",
            "task_name": "Verbal Fluency (COWAT)",
            "description": "Generate words starting with given letter in 60 seconds",
            "clinical_validation": "Executive function standard. Reference: Benton & Hamsher, 1989",
            "is_baseline_task": False,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 60,
            "requires_audio": False,
            "requires_keyboard": True,
            "cognitive_load": "medium",
            "instructions": "Type all words you can think of that start with the given letter. No proper nouns or repetitions."
        },
        {
            "task_code": "category_fluency",
            "domain": "planning",
            "task_name": "Category Fluency",
            "description": "Generate items from category (animals, fruits, etc.) in 60 seconds",
            "clinical_validation": "Semantic fluency measure. Reference: Henry & Crawford, 2004",
            "is_baseline_task": False,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 60,
            "requires_audio": False,
            "requires_keyboard": True,
            "cognitive_load": "medium",
            "instructions": "Type all items from the category you can think of (e.g., animals, fruits). Be specific."
        },
        {
            "task_code": "twenty_questions",
            "domain": "planning",
            "task_name": "Twenty Questions Task",
            "description": "Identify hidden object using minimum yes/no questions",
            "clinical_validation": "Strategic problem-solving. Reference: Mosher & Hornsby, 1966",
            "is_baseline_task": False,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 240,
            "requires_audio": False,
            "requires_keyboard": True,
            "cognitive_load": "high",
            "instructions": "Guess the hidden object by asking yes/no questions. Use strategy to minimize questions."
        },
        
        # ============================================
        # VISUAL SCANNING DOMAIN
        # ============================================
        {
            "task_code": "visual_search",
            "domain": "visual_scanning",
            "task_name": "Visual Search",
            "description": "Find target among distractors",
            "clinical_validation": "Visual attention standard",
            "is_baseline_task": True,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 120,
            "requires_audio": False,
            "requires_keyboard": False,
            "cognitive_load": "low",
            "instructions": "Click on the target item as quickly as possible."
        },
        {
            "task_code": "cancellation_test",
            "domain": "visual_scanning",
            "task_name": "Cancellation Test",
            "description": "Cross out all target letters/symbols on page",
            "clinical_validation": "Visual attention and processing speed. Reference: Mesulam, 1985",
            "is_baseline_task": False,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 120,
            "requires_audio": False,
            "requires_keyboard": False,
            "cognitive_load": "low",
            "instructions": "Click on all target symbols/letters as quickly as possible."
        },
        {
            "task_code": "feature_conjunction",
            "domain": "visual_scanning",
            "task_name": "Feature vs Conjunction Search",
            "description": "Find target in feature search (easy) or conjunction search (hard)",
            "clinical_validation": "Attention theory. Reference: Treisman & Gelade, 1980",
            "is_baseline_task": False,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 120,
            "requires_audio": False,
            "requires_keyboard": False,
            "cognitive_load": "medium",
            "instructions": "Find the target item. Feature search: target pops out. Conjunction search: requires careful scanning."
        },
        {
            "task_code": "multiple_object_tracking",
            "domain": "visual_scanning",
            "task_name": "Multiple Object Tracking (MOT)",
            "description": "Track 2-5 moving objects among identical distractors",
            "clinical_validation": "Dynamic visual attention. Driving safety relevance. Reference: Pylyshyn & Storm, 2006",
            "is_baseline_task": False,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 150,
            "requires_audio": False,
            "requires_keyboard": False,
            "cognitive_load": "high",
            "instructions": "Watch the target objects flash, then track them as they move. Click the tracked objects when movement stops."
        },
        {
            "task_code": "useful_field_of_view",
            "domain": "visual_scanning",
            "task_name": "Useful Field of View (UFOV)",
            "description": "Identify central target while detecting peripheral target",
            "clinical_validation": "⭐⭐⭐⭐⭐ Driving safety predictor. Reference: Ball et al., 1993",
            "is_baseline_task": False,
            "difficulty_min": 1,
            "difficulty_max": 10,
            "estimated_duration_seconds": 120,
            "requires_audio": False,
            "requires_keyboard": True,
            "cognitive_load": "medium",
            "instructions": "Identify the central target AND locate the peripheral target. Stimuli appear very briefly."
        }
    ]
    
    with Session(engine) as session:
        print("🌱 Seeding cognitive_tasks table...")
        print(f"📊 Total tasks to seed: {len(tasks)}\n")
        
        added_count = 0
        skipped_count = 0
        
        for task_data in tasks:
            # Check if task already exists
            existing = session.exec(
                select(CognitiveTask).where(CognitiveTask.task_code == task_data["task_code"])
            ).first()
            
            if existing:
                print(f"⏭️  Skipping {task_data['task_code']} (already exists)")
                skipped_count += 1
                continue
            
            # Create new task
            task = CognitiveTask(**task_data)
            session.add(task)
            
            baseline_marker = "⭐ BASELINE" if task_data["is_baseline_task"] else ""
            print(f"✅ Added: {task_data['task_code']} - {task_data['task_name']} {baseline_marker}")
            added_count += 1
        
        session.commit()
        
        print(f"\n{'='*60}")
        print(f"🎉 Seeding Complete!")
        print(f"{'='*60}")
        print(f"✅ Added: {added_count} tasks")
        print(f"⏭️  Skipped: {skipped_count} tasks (already existed)")
        print(f"📊 Total tasks in database: {added_count + skipped_count}")
        print(f"\n📋 Task Distribution:")
        
        # Count by domain
        with Session(engine) as count_session:
            domains = ["working_memory", "processing_speed", "attention", "flexibility", "planning", "visual_scanning"]
            for domain in domains:
                count = len(count_session.exec(
                    select(CognitiveTask).where(CognitiveTask.domain == domain)
                ).all())
                print(f"   {domain}: {count} tasks")

if __name__ == "__main__":
    seed_cognitive_tasks()

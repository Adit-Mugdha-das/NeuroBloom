"""
Trail Making Test - Part B Service

Clinical Validation: ⭐⭐⭐⭐⭐ Executive Function Gold Standard
Measures: Cognitive flexibility, set-shifting, divided attention, task switching
MS Relevance: Highly sensitive to MS executive dysfunction and multitasking deficits

Reference: D'Elia et al., 1996; Reitan & Wolfson, 1985
TMT-B is part of Halstead-Reitan Neuropsychological Battery
"""

from typing import Dict, List, Any, Optional, Tuple
import random
from datetime import datetime
import math

class TrailMakingBTask:
    """
    Trail Making Test - Part B (TMT-B)
    
    Task Structure:
    - Alternate between numbers and letters: 1→A→2→B→3→C...→13
    - User must connect circles in correct alternating sequence
    - Visual-motor tracking + cognitive flexibility
    
    Difficulty Progression:
    - Levels 1-3: 13 items (simplified for MS patients)
    - Levels 4-6: 25 items (standard clinical version)
    - Levels 7-10: 25 items + distractor circles
    
    Key Measures:
    - Completion time (primary metric)
    - Sequence errors (wrong connections)
    - Perseverative errors (same mistake repeated)
    - TMT B-A score (Part B time - Part A baseline)
    """
    
    # Target sequences for each difficulty level
    DIFFICULTY_CONFIG = {
        1: {
            "total_items": 8,  # 1-A-2-B-3-C-4-D
            "numbers": [1, 2, 3, 4],
            "letters": ['A', 'B', 'C', 'D'],
            "distractors": 0,
            "circle_size": "large",
            "spacing": "generous",
            "time_limit_seconds": 180,  # 3 minutes
            "description": "Beginner - 8 items, easy spacing"
        },
        2: {
            "total_items": 10,  # 1-A-2-B-3-C-4-D-5-E
            "numbers": [1, 2, 3, 4, 5],
            "letters": ['A', 'B', 'C', 'D', 'E'],
            "distractors": 0,
            "circle_size": "large",
            "spacing": "comfortable",
            "time_limit_seconds": 180,
            "description": "Easy - 10 items"
        },
        3: {
            "total_items": 13,  # Full simplified: 1-A-2-B-3-C-4-D-5-E-6-F-7
            "numbers": [1, 2, 3, 4, 5, 6, 7],
            "letters": ['A', 'B', 'C', 'D', 'E', 'F'],
            "distractors": 0,
            "circle_size": "medium",
            "spacing": "comfortable",
            "time_limit_seconds": 240,  # 4 minutes
            "description": "Moderate - 13 items simplified"
        },
        4: {
            "total_items": 25,  # Standard clinical: 1-A-2-B...12-L-13
            "numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
            "letters": ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'],
            "distractors": 0,
            "circle_size": "medium",
            "spacing": "standard",
            "time_limit_seconds": 300,  # 5 minutes (clinical standard)
            "description": "Intermediate - Standard 25-item version"
        },
        5: {
            "total_items": 25,
            "numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
            "letters": ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'],
            "distractors": 0,
            "circle_size": "medium",
            "spacing": "compact",
            "time_limit_seconds": 300,
            "description": "Challenging - Closer spacing"
        },
        6: {
            "total_items": 25,
            "numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
            "letters": ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'],
            "distractors": 3,  # Add distractor circles
            "circle_size": "small",
            "spacing": "compact",
            "time_limit_seconds": 300,
            "description": "Advanced - With distractors"
        },
        7: {
            "total_items": 25,
            "numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
            "letters": ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'],
            "distractors": 5,
            "circle_size": "small",
            "spacing": "tight",
            "time_limit_seconds": 300,
            "description": "Expert - More distractors, tight spacing"
        },
        8: {
            "total_items": 25,
            "numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
            "letters": ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'],
            "distractors": 7,
            "circle_size": "small",
            "spacing": "tight",
            "time_limit_seconds": 300,
            "description": "Master - Many distractors"
        },
        9: {
            "total_items": 25,
            "numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
            "letters": ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'],
            "distractors": 10,
            "circle_size": "extra-small",
            "spacing": "very-tight",
            "time_limit_seconds": 300,
            "description": "Elite - Maximum distractors"
        },
        10: {
            "total_items": 25,
            "numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
            "letters": ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'],
            "distractors": 15,  # Many distractors
            "circle_size": "extra-small",
            "spacing": "very-tight",
            "time_limit_seconds": 300,
            "description": "Ultimate - Extreme challenge"
        }
    }
    
    # Canvas dimensions for circle placement
    CANVAS_WIDTH = 800
    CANVAS_HEIGHT = 600
    MARGIN = 60  # Keep circles away from edges
    
    def __init__(self):
        self.session_data = {}
    
    def generate_session(self, difficulty: int = 1, user_baseline_time: Optional[float] = None) -> Dict[str, Any]:
        """
        Generate a Trail Making Test - Part B session.
        
        Args:
            difficulty: Level 1-10
            user_baseline_time: User's TMT-A baseline time (for B-A calculation)
        
        Returns:
            Session data with circle positions and correct sequence
        """
        if difficulty not in self.DIFFICULTY_CONFIG:
            difficulty = 1
        
        config = self.DIFFICULTY_CONFIG[difficulty]
        
        # Build the correct sequence (alternating numbers and letters)
        correct_sequence = self._build_sequence(config)
        
        # Generate circle positions (non-overlapping)
        circles = self._generate_circle_positions(config, correct_sequence)
        
        session_data = {
            "difficulty": difficulty,
            "total_items": config["total_items"],
            "time_limit_seconds": config["time_limit_seconds"],
            "circles": circles,
            "correct_sequence": correct_sequence,
            "circle_size": config["circle_size"],
            "spacing": config["spacing"],
            "description": config["description"],
            "user_baseline_time": user_baseline_time,  # For B-A calculation
            "instructions": "Connect circles in order: 1→A→2→B→3→C... Click each circle in sequence."
        }
        
        self.session_data = session_data
        return session_data
    
    def _build_sequence(self, config: Dict) -> List[str]:
        """Build the correct alternating sequence."""
        sequence = []
        numbers = config["numbers"]
        letters = config["letters"]
        
        # Alternate: number, letter, number, letter...
        for i in range(len(numbers)):
            sequence.append(str(numbers[i]))
            if i < len(letters):
                sequence.append(letters[i])
        
        # Add final letter if needed to match total_items
        if len(sequence) < config["total_items"] and len(letters) > len(numbers):
            sequence.append(letters[len(numbers)])
        
        return sequence[:config["total_items"]]
    
    def _generate_circle_positions(self, config: Dict, correct_sequence: List[str]) -> List[Dict]:
        """
        Generate non-overlapping positions for all circles (targets + distractors).
        
        Returns list of circles with {id, label, x, y, is_distractor}
        """
        circles = []
        positions = []
        
        # Determine minimum distance based on spacing
        spacing_map = {
            "generous": 120,
            "comfortable": 100,
            "standard": 90,
            "compact": 80,
            "tight": 70,
            "very-tight": 60
        }
        min_distance = spacing_map.get(config["spacing"], 90)
        
        # Place target circles first
        for idx, label in enumerate(correct_sequence):
            pos = self._find_valid_position(positions, min_distance)
            circles.append({
                "id": f"target-{idx}",
                "label": label,
                "x": pos[0],
                "y": pos[1],
                "is_distractor": False,
                "sequence_index": idx
            })
            positions.append(pos)
        
        # Add distractor circles (numbers/letters not in sequence)
        distractor_pool = self._get_distractor_pool(config, correct_sequence)
        for i in range(config["distractors"]):
            if i < len(distractor_pool):
                pos = self._find_valid_position(positions, min_distance)
                circles.append({
                    "id": f"distractor-{i}",
                    "label": distractor_pool[i],
                    "x": pos[0],
                    "y": pos[1],
                    "is_distractor": True,
                    "sequence_index": -1
                })
                positions.append(pos)
        
        # Shuffle circles so targets aren't in order visually
        random.shuffle(circles)
        
        return circles
    
    def _find_valid_position(self, existing_positions: List[Tuple[int, int]], min_distance: int) -> Tuple[int, int]:
        """Find a position that doesn't overlap with existing circles."""
        max_attempts = 100
        
        for _ in range(max_attempts):
            x = random.randint(self.MARGIN, self.CANVAS_WIDTH - self.MARGIN)
            y = random.randint(self.MARGIN, self.CANVAS_HEIGHT - self.MARGIN)
            
            # Check distance from all existing positions
            valid = True
            for ex_x, ex_y in existing_positions:
                distance = math.sqrt((x - ex_x)**2 + (y - ex_y)**2)
                if distance < min_distance:
                    valid = False
                    break
            
            if valid:
                return (x, y)
        
        # Fallback: return random position even if overlap
        return (
            random.randint(self.MARGIN, self.CANVAS_WIDTH - self.MARGIN),
            random.randint(self.MARGIN, self.CANVAS_HEIGHT - self.MARGIN)
        )
    
    def _get_distractor_pool(self, config: Dict, sequence: List[str]) -> List[str]:
        """Get pool of distractor numbers/letters not in the sequence."""
        distractors = []
        
        # Numbers not in sequence
        max_number = max(config["numbers"]) if config["numbers"] else 13
        for num in range(14, min(20, 14 + config["distractors"] + 5)):
            if str(num) not in sequence:
                distractors.append(str(num))
        
        # Letters not in sequence
        all_letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        for letter in all_letters:
            if letter not in sequence and len(distractors) < config["distractors"] * 2:
                distractors.append(letter)
        
        random.shuffle(distractors)
        return distractors
    
    def score_session(self, session_data: Dict[str, Any], user_sequence: List[str], 
                     completion_time_seconds: float, errors: List[Dict]) -> Dict[str, Any]:
        """
        Score a completed Trail Making Test - Part B session.
        
        Args:
            session_data: Original session configuration
            user_sequence: List of circle IDs clicked in order
            completion_time_seconds: Total time taken
            errors: List of error events {sequence_index, clicked_label, expected_label, type}
        
        Returns:
            Scoring metrics and performance assessment
        """
        correct_sequence = session_data["correct_sequence"]
        total_items = len(correct_sequence)
        time_limit = session_data["time_limit_seconds"]
        
        # Count error types
        sequence_errors = sum(1 for e in errors if e.get("type") == "sequence_error")
        perseverative_errors = sum(1 for e in errors if e.get("type") == "perseverative_error")
        total_errors = len(errors)
        
        # Completion status
        completed = len(user_sequence) >= total_items and completion_time_seconds < time_limit
        
        # Calculate accuracy
        correct_connections = total_items - sequence_errors
        accuracy = (correct_connections / total_items * 100) if total_items > 0 else 0
        
        # Time penalty for errors (clinical scoring: +5 seconds per error)
        adjusted_time = completion_time_seconds + (total_errors * 5)
        
        # Calculate B-A score if baseline available
        b_a_score = None
        baseline_time = session_data.get("user_baseline_time")
        if baseline_time:
            b_a_score = completion_time_seconds - baseline_time
        
        # Performance categorization (based on clinical norms)
        performance_level = self._categorize_performance(
            completion_time_seconds, 
            total_errors, 
            session_data["difficulty"]
        )
        
        # Calculate percentile (age-adjusted norms would be ideal)
        percentile = self._calculate_percentile(completion_time_seconds, session_data["difficulty"])
        
        metrics = {
            "completion_time_seconds": round(completion_time_seconds, 2),
            "adjusted_time_seconds": round(adjusted_time, 2),
            "total_errors": total_errors,
            "sequence_errors": sequence_errors,
            "perseverative_errors": perseverative_errors,
            "accuracy": round(accuracy, 1),
            "completed": completed,
            "b_a_score": round(b_a_score, 2) if b_a_score else None,
            "performance_level": performance_level,
            "percentile": percentile,
            "items_completed": len(user_sequence),
            "total_items": total_items,
            "difficulty": session_data["difficulty"]
        }
        
        return {
            "metrics": metrics,
            "interpretation": self._generate_interpretation(metrics),
            "clinical_note": self._generate_clinical_note(metrics)
        }
    
    def _categorize_performance(self, time_seconds: float, errors: int, difficulty: int) -> str:
        """Categorize performance based on time and errors."""
        # Adjust thresholds by difficulty
        if difficulty <= 3:
            excellent_time = 60
            good_time = 90
            fair_time = 120
        elif difficulty <= 6:
            excellent_time = 90
            good_time = 120
            fair_time = 180
        else:
            excellent_time = 120
            good_time = 150
            fair_time = 210
        
        if errors == 0 and time_seconds < excellent_time:
            return "Excellent"
        elif errors <= 1 and time_seconds < good_time:
            return "Good"
        elif errors <= 3 and time_seconds < fair_time:
            return "Fair"
        elif errors <= 5:
            return "Needs Improvement"
        else:
            return "Struggling"
    
    def _calculate_percentile(self, time_seconds: float, difficulty: int) -> int:
        """Rough percentile estimation (would need proper normative data)."""
        # Simplified percentile based on time and difficulty
        if difficulty <= 3:
            if time_seconds < 45: return 95
            elif time_seconds < 60: return 85
            elif time_seconds < 90: return 70
            elif time_seconds < 120: return 50
            else: return 30
        elif difficulty <= 6:
            if time_seconds < 75: return 95
            elif time_seconds < 100: return 85
            elif time_seconds < 135: return 70
            elif time_seconds < 180: return 50
            else: return 30
        else:
            if time_seconds < 100: return 95
            elif time_seconds < 130: return 85
            elif time_seconds < 165: return 70
            elif time_seconds < 210: return 50
            else: return 30
    
    def _generate_interpretation(self, metrics: Dict) -> str:
        """Generate human-readable interpretation."""
        perf = metrics["performance_level"]
        time = metrics["completion_time_seconds"]
        errors = metrics["total_errors"]
        
        if perf == "Excellent":
            return f"Outstanding cognitive flexibility! Completed in {time:.1f}s with {errors} error(s). Your set-shifting ability is exceptional."
        elif perf == "Good":
            return f"Strong performance. Completed in {time:.1f}s with {errors} error(s). Good task-switching and divided attention."
        elif perf == "Fair":
            return f"Adequate performance. Time: {time:.1f}s, Errors: {errors}. Continue practicing to improve switching speed."
        elif perf == "Needs Improvement":
            return f"Performance below target. Time: {time:.1f}s, Errors: {errors}. Focus on accuracy before speed."
        else:
            return f"Challenging session. Time: {time:.1f}s, Errors: {errors}. Practice will help build cognitive flexibility."
    
    def _generate_clinical_note(self, metrics: Dict) -> str:
        """Generate clinical observation note."""
        notes = []
        
        if metrics["completion_time_seconds"] < 90:
            notes.append("Fast completion time suggests good processing speed.")
        elif metrics["completion_time_seconds"] > 180:
            notes.append("Slower completion may indicate executive function challenges.")
        
        if metrics["sequence_errors"] > 5:
            notes.append("Frequent sequence errors suggest set-shifting difficulty.")
        
        if metrics["perseverative_errors"] > 2:
            notes.append("Perseverative errors indicate possible cognitive inflexibility.")
        
        if metrics.get("b_a_score") and metrics["b_a_score"] > 120:
            notes.append("Large B-A score suggests significant executive dysfunction.")
        
        if metrics["accuracy"] > 95:
            notes.append("High accuracy demonstrates strong attention to task rules.")
        
        return " ".join(notes) if notes else "Performance within normal parameters."

"""
Cancellation Test Task Service

Clinical Validation: Standard visual attention/scanning test
Reference: Mesulam, 1985
MS Evidence: Visual attention and processing speed assessment, detects unilateral neglect

Implementation: Grid of random letters/symbols, user identifies all target items
"""

import random
from typing import Dict, Any, List, Tuple
from datetime import datetime


class CancellationTestTask:
    """
    Cancellation Test - Visual scanning and attention task.
    
    Task: Find and mark all instances of target letter(s) or symbol(s) in a grid
    Measures: Visual scanning speed, attention, spatial processing
    """
    
    # Letter pools for different difficulty levels
    LETTER_POOL = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    COMMON_LETTERS = "AEIOURSTLNMDHCP"  # More frequent
    RARE_LETTERS = "JQXZKVWYFGB"  # Less frequent
    
    # Symbol pools
    SYMBOLS = ["★", "●", "■", "▲", "◆", "♦", "♣", "♠", "♥", "✦", "✧", "○", "□", "△"]
    
    # Grid configurations by difficulty
    # Optimized for MS patients with visual accessibility as PRIMARY concern
    # Reference: Mesulam (1985), Weintraub & Mesulam (1988)
    # Uses scrollable container with LARGE cells (50-60px) for patients with visual impairments
    # Challenge increases through: grid size, target count, target types, letter complexity
    # Clinical validity: 150-540 cells matches standard cancellation tests
    GRID_CONFIGS = {
        1: {"rows": 10, "cols": 15, "total": 150, "targets": 1, "target_count": 18, "suggested_time": 120},
        2: {"rows": 12, "cols": 17, "total": 204, "targets": 1, "target_count": 24, "suggested_time": 150},
        3: {"rows": 13, "cols": 19, "total": 247, "targets": 2, "target_count": 28, "suggested_time": 180},
        4: {"rows": 14, "cols": 21, "total": 294, "targets": 2, "target_count": 32, "suggested_time": 210},
        5: {"rows": 15, "cols": 22, "total": 330, "targets": 2, "target_count": 36, "suggested_time": 240},
        6: {"rows": 16, "cols": 23, "total": 368, "targets": 2, "target_count": 40, "suggested_time": 270},
        7: {"rows": 17, "cols": 24, "total": 408, "targets": 3, "target_count": 44, "suggested_time": 300},
        8: {"rows": 18, "cols": 25, "total": 450, "targets": 3, "target_count": 48, "suggested_time": 330},
        9: {"rows": 19, "cols": 26, "total": 494, "targets": 3, "target_count": 52, "suggested_time": 360},
        10: {"rows": 20, "cols": 27, "total": 540, "targets": 3, "target_count": 56, "suggested_time": 390}
    }
    
    # Performance benchmarks (percentage of targets found)
    PERFORMANCE_BENCHMARKS = {
        "excellent": 95,      # 95%+ targets found
        "good": 85,           # 85-94% targets found
        "average": 70,        # 70-84% targets found
        "below_average": 50   # 50-69% targets found
    }
    
    @staticmethod
    def generate_trial(difficulty: int, use_symbols: bool = False) -> Dict[str, Any]:
        """
        Generate a cancellation test trial.
        
        Args:
            difficulty: Difficulty level (1-10)
            use_symbols: If True, use symbols instead of letters
            
        Returns:
            Trial configuration with grid and targets
        """
        difficulty = max(1, min(10, difficulty))
        config = CancellationTestTask.GRID_CONFIGS[difficulty]
        
        # Select target items
        if use_symbols:
            available_items = CancellationTestTask.SYMBOLS
            target_items = random.sample(available_items, config["targets"])
            distractor_items = [s for s in available_items if s not in target_items]
        else:
            # Use letters - mix of common and rare
            if difficulty <= 3:
                available_items = CancellationTestTask.COMMON_LETTERS
            else:
                available_items = CancellationTestTask.LETTER_POOL
            
            target_items = random.sample(available_items, config["targets"])
            distractor_items = [l for l in available_items if l not in target_items]
        
        # Generate grid with targets and distractors
        grid = []
        target_positions = []
        
        # Calculate targets per target item
        targets_per_item = config["target_count"] // config["targets"]
        remaining_targets = config["target_count"] % config["targets"]
        
        # Create list of all items to place
        items_to_place = []
        for i, target in enumerate(target_items):
            count = targets_per_item + (1 if i < remaining_targets else 0)
            items_to_place.extend([target] * count)
        
        # Fill remaining with distractors
        remaining_slots = config["total"] - len(items_to_place)
        items_to_place.extend(random.choices(distractor_items, k=remaining_slots))
        
        # Shuffle
        random.shuffle(items_to_place)
        
        # Build grid and track target positions
        idx = 0
        for row in range(config["rows"]):
            grid_row = []
            for col in range(config["cols"]):
                item = items_to_place[idx]
                grid_row.append(item)
                
                if item in target_items:
                    target_positions.append({"row": row, "col": col, "item": item})
                
                idx += 1
            grid.append(grid_row)
        
        return {
            "difficulty": difficulty,
            "grid": grid,
            "rows": config["rows"],
            "cols": config["cols"],
            "target_items": target_items,
            "target_count": config["target_count"],
            "target_positions": target_positions,
            "suggested_time": config["suggested_time"],
            "use_symbols": use_symbols,
            "instructions": f"Find and click all instances of: {', '.join(target_items)}",
            "total_items": config["total"]
        }

    @staticmethod
    def score_response(
        marked_positions: List[Dict[str, int]],
        target_positions: List[Dict[str, Any]],
        completion_time: float,
        suggested_time: int,
        difficulty: int
    ) -> Dict[str, Any]:
        """
        Score the cancellation test response.
        No time limits - focuses on accuracy. Completion time is tracked for performance analysis.

        Args:
            marked_positions: List of positions marked by user [{"row": 0, "col": 1}, ...]
            target_positions: List of actual target positions
            completion_time: Time taken in seconds
            suggested_time: Suggested time (not enforced)
            difficulty: Difficulty level
            
        Returns:
            Scoring results with accuracy, speed, and spatial analysis
        """
        # Convert to sets for comparison
        marked_set = {(pos["row"], pos["col"]) for pos in marked_positions}
        target_set = {(pos["row"], pos["col"]) for pos in target_positions}
        
        # Calculate metrics
        true_positives = len(marked_set & target_set)  # Correctly marked targets
        false_positives = len(marked_set - target_set)  # Incorrectly marked non-targets
        false_negatives = len(target_set - marked_set)  # Missed targets
        
        total_targets = len(target_positions)
        accuracy = (true_positives / total_targets * 100) if total_targets > 0 else 0
        
        # Check for spatial patterns (neglect detection)
        spatial_analysis = CancellationTestTask._analyze_spatial_pattern(
            target_positions, marked_positions
        )
        
        # Determine performance rating based ONLY on accuracy
        if accuracy >= CancellationTestTask.PERFORMANCE_BENCHMARKS["excellent"]:
            performance_rating = "excellent"
            raw_score = 100
        elif accuracy >= CancellationTestTask.PERFORMANCE_BENCHMARKS["good"]:
            performance_rating = "good"
            raw_score = 85
        elif accuracy >= CancellationTestTask.PERFORMANCE_BENCHMARKS["average"]:
            performance_rating = "average"
            raw_score = 70
        elif accuracy >= CancellationTestTask.PERFORMANCE_BENCHMARKS["below_average"]:
            performance_rating = "below_average"
            raw_score = 55
        else:
            performance_rating = "poor"
            raw_score = 30
        
        # Speed metric (for tracking only, not penalized)
        # Items per minute = (total_targets / completion_time) * 60
        scanning_speed = (total_targets / completion_time * 60) if completion_time > 0 else 0

        final_score = raw_score

        # Difficulty adjustment based on accuracy only
        difficulty_adjustment = CancellationTestTask.calculate_difficulty_adjustment(
            accuracy, completion_time, suggested_time, difficulty
        )
        
        return {
            "score": round(final_score, 1),
            "raw_score": raw_score,
            "accuracy": round(accuracy, 1),
            "targets_found": true_positives,
            "targets_missed": false_negatives,
            "false_alarms": false_positives,
            "total_targets": total_targets,
            "completion_time": round(completion_time, 1),
            "suggested_time": suggested_time,
            "scanning_speed": round(scanning_speed, 1),
            "performance_rating": performance_rating,
            "spatial_analysis": spatial_analysis,
            "difficulty_adjustment": difficulty_adjustment,
            "feedback": CancellationTestTask._generate_feedback(
                performance_rating, accuracy, spatial_analysis
            )
        }
    
    @staticmethod
    def _analyze_spatial_pattern(
        target_positions: List[Dict[str, Any]],
        marked_positions: List[Dict[str, int]]
    ) -> Dict[str, Any]:
        """
        Analyze spatial pattern of responses to detect potential neglect.
        
        Args:
            target_positions: List of actual target positions
            marked_positions: List of user-marked positions
            
        Returns:
            Spatial analysis results
        """
        if not target_positions:
            return {"neglect_detected": False}
        
        # Get grid dimensions
        max_row = max(pos["row"] for pos in target_positions)
        max_col = max(pos["col"] for pos in target_positions)
        
        mid_col = max_col // 2
        
        # Separate targets into left and right halves
        left_targets = [p for p in target_positions if p["col"] < mid_col]
        right_targets = [p for p in target_positions if p["col"] >= mid_col]
        
        marked_set = {(pos["row"], pos["col"]) for pos in marked_positions}
        
        # Count hits in each half
        left_hits = sum(1 for p in left_targets if (p["row"], p["col"]) in marked_set)
        right_hits = sum(1 for p in right_targets if (p["row"], p["col"]) in marked_set)
        
        left_accuracy = (left_hits / len(left_targets) * 100) if left_targets else 0
        right_accuracy = (right_hits / len(right_targets) * 100) if right_targets else 0
        
        # Detect significant asymmetry (>20% difference suggests possible neglect)
        asymmetry = abs(left_accuracy - right_accuracy)
        neglect_detected = asymmetry > 20
        
        neglect_side = None
        if neglect_detected:
            neglect_side = "left" if left_accuracy < right_accuracy else "right"
        
        return {
            "neglect_detected": neglect_detected,
            "neglect_side": neglect_side,
            "left_accuracy": round(left_accuracy, 1),
            "right_accuracy": round(right_accuracy, 1),
            "asymmetry": round(asymmetry, 1)
        }
    
    @staticmethod
    def _generate_feedback(
        performance_rating: str,
        accuracy: float,
        spatial_analysis: Dict[str, Any]
    ) -> str:
        """Generate personalized feedback based on performance."""
        feedback_parts = []
        
        # Performance feedback
        if performance_rating == "excellent":
            feedback_parts.append(f"Excellent work! You found {accuracy:.0f}% of the targets.")
        elif performance_rating == "good":
            feedback_parts.append(f"Good job! You found {accuracy:.0f}% of the targets.")
        elif performance_rating == "average":
            feedback_parts.append(f"You found {accuracy:.0f}% of the targets. Try to scan more systematically.")
        else:
            feedback_parts.append(f"You found {accuracy:.0f}% of the targets. Practice scanning the entire grid carefully.")
        
        # Spatial pattern feedback
        if spatial_analysis.get("neglect_detected"):
            side = spatial_analysis.get("neglect_side")
            feedback_parts.append(f"Note: You missed more targets on the {side} side. Try to scan both sides equally.")
        
        return " ".join(feedback_parts)
    
    @staticmethod
    def calculate_difficulty_adjustment(
        accuracy: float,
        completion_time: float,
        suggested_time: int,
        current_difficulty: int
    ) -> int:
        """
        Calculate difficulty adjustment for next trial.
        Based primarily on accuracy, time is tracked but not penalized.

        Args:
            accuracy: Percentage of targets found
            completion_time: Time taken
            suggested_time: Suggested time (not enforced)
            current_difficulty: Current difficulty level
            
        Returns:
            Difficulty adjustment (-2 to +2)
        """
        # Excellent performance: increase difficulty
        if accuracy >= 95:
            return 2
        elif accuracy >= 90:
            return 1
        
        # Poor performance: decrease difficulty
        elif accuracy < 60:
            return -2
        elif accuracy < 75:
            return -1
        
        # Average performance: maintain difficulty
        return 0

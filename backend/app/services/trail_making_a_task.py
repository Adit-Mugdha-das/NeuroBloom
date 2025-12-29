"""
Trail Making Test - Part A (TMT-A) Task Service

Classic neuropsychological test from the Halstead-Reitan Battery.
User connects numbered circles in sequence (1→2→3...→25) as fast as possible.

Clinical Validation: Gold standard for measuring psychomotor speed and visual scanning
MS Research: Highly sensitive to MS-related processing speed deficits
Reference: Bever et al., 1995
"""

import random
from typing import List, Dict, Tuple
from datetime import datetime


class TrailMakingATask:
    """
    Service for generating and scoring Trail Making Test Part A (TMT-A) trials
    """
    
    # Difficulty configuration
    # TMT-A norms: <29s = excellent, 29-78s = average, >78s = impaired for MS patients
    DIFFICULTY_CONFIG = {
        1: {
            "num_circles": 15,
            "circle_radius": 35,       # Larger circles (pixels)
            "min_spacing": 100,        # Minimum distance between circles
            "distractors": 0,          # No distractor symbols
            "time_limit": 120,         # 2 minutes
        },
        2: {
            "num_circles": 15,
            "circle_radius": 32,
            "min_spacing": 90,
            "distractors": 0,
            "time_limit": 120,
        },
        3: {
            "num_circles": 18,
            "circle_radius": 30,
            "min_spacing": 85,
            "distractors": 0,
            "time_limit": 120,
        },
        4: {
            "num_circles": 20,         # Standard TMT-A
            "circle_radius": 28,
            "min_spacing": 75,
            "distractors": 3,          # Add some distractors
            "time_limit": 120,
        },
        5: {
            "num_circles": 20,
            "circle_radius": 26,
            "min_spacing": 70,
            "distractors": 5,
            "time_limit": 120,
        },
        6: {
            "num_circles": 22,
            "circle_radius": 25,
            "min_spacing": 65,
            "distractors": 5,
            "time_limit": 120,
        },
        7: {
            "num_circles": 25,         # Full standard TMT-A
            "circle_radius": 24,
            "min_spacing": 60,
            "distractors": 7,
            "time_limit": 120,
        },
        8: {
            "num_circles": 25,
            "circle_radius": 22,
            "min_spacing": 55,
            "distractors": 10,
            "time_limit": 120,
        },
        9: {
            "num_circles": 25,
            "circle_radius": 20,
            "min_spacing": 50,
            "distractors": 12,
            "time_limit": 120,
        },
        10: {
            "num_circles": 25,
            "circle_radius": 18,       # Smaller circles
            "min_spacing": 45,         # Closer spacing
            "distractors": 15,         # More distractors
            "time_limit": 120,
        },
    }
    
    # Canvas size for circle placement
    CANVAS_WIDTH = 800
    CANVAS_HEIGHT = 600
    
    @staticmethod
    def generate_trial(difficulty: int) -> Dict:
        """
        Generate TMT-A trial with circle positions
        
        Args:
            difficulty: Level 1-10
            
        Returns:
            Dict with:
            - circles: List of {number, x, y, radius}
            - distractors: List of {symbol, x, y, radius}
            - time_limit: Time limit in seconds
            - difficulty: Difficulty level
        """
        config = TrailMakingATask.DIFFICULTY_CONFIG.get(
            difficulty, 
            TrailMakingATask.DIFFICULTY_CONFIG[5]
        )
        
        num_circles = config["num_circles"]
        circle_radius = config["circle_radius"]
        min_spacing = config["min_spacing"]
        num_distractors = config["distractors"]
        
        # Generate circle positions (avoiding overlaps)
        circles = []
        positions = []
        
        # Generate numbered circles (1 to num_circles)
        for number in range(1, num_circles + 1):
            position = TrailMakingATask._generate_non_overlapping_position(
                positions, circle_radius, min_spacing
            )
            
            circles.append({
                "number": number,
                "x": position[0],
                "y": position[1],
                "radius": circle_radius
            })
            positions.append(position)
        
        # Generate distractor symbols
        distractors = []
        distractor_symbols = ['□', '△', '○', '◇', '☆', '♦', '♣', '♠', '♥', '●', '■', '▲', '◆', '★', '×']
        
        for i in range(num_distractors):
            position = TrailMakingATask._generate_non_overlapping_position(
                positions, circle_radius, min_spacing
            )
            
            distractors.append({
                "symbol": random.choice(distractor_symbols),
                "x": position[0],
                "y": position[1],
                "radius": circle_radius
            })
            positions.append(position)
        
        return {
            "circles": circles,
            "distractors": distractors,
            "time_limit": config["time_limit"],
            "difficulty": difficulty,
            "canvas_width": TrailMakingATask.CANVAS_WIDTH,
            "canvas_height": TrailMakingATask.CANVAS_HEIGHT
        }
    
    @staticmethod
    def _generate_non_overlapping_position(
        existing_positions: List[Tuple[int, int]], 
        radius: int, 
        min_spacing: int
    ) -> Tuple[int, int]:
        """
        Generate a random position that doesn't overlap with existing positions
        
        Args:
            existing_positions: List of (x, y) tuples already placed
            radius: Circle radius
            min_spacing: Minimum distance between circle centers
            
        Returns:
            Tuple of (x, y) coordinates
        """
        margin = radius + 10
        max_attempts = 100
        
        for _ in range(max_attempts):
            x = random.randint(margin, TrailMakingATask.CANVAS_WIDTH - margin)
            y = random.randint(margin, TrailMakingATask.CANVAS_HEIGHT - margin)
            
            # Check if this position is far enough from all existing positions
            valid = True
            for ex_x, ex_y in existing_positions:
                distance = ((x - ex_x) ** 2 + (y - ex_y) ** 2) ** 0.5
                if distance < min_spacing:
                    valid = False
                    break
            
            if valid:
                return (x, y)
        
        # If we can't find a non-overlapping position, just return a random one
        # (this shouldn't happen with reasonable parameters)
        return (
            random.randint(margin, TrailMakingATask.CANVAS_WIDTH - margin),
            random.randint(margin, TrailMakingATask.CANVAS_HEIGHT - margin)
        )
    
    @staticmethod
    def score_response(
        trial: Dict,
        completion_time: float,
        errors: List[Dict],
        clicks: List[Dict]
    ) -> Dict:
        """
        Score TMT-A trial
        
        Args:
            trial: Original trial data
            completion_time: Total time taken in milliseconds
            errors: List of error events {timestamp, clicked_number, expected_number}
            clicks: List of all clicks {timestamp, number, x, y}
            
        Returns:
            Dict with scoring metrics
        """
        num_circles = len(trial["circles"])
        num_errors = len(errors)
        
        # Convert completion time to seconds
        completion_time_sec = completion_time / 1000
        
        # Calculate score based on TMT-A norms for MS patients
        # Excellent: <29s, Good: 29-39s, Average: 40-78s, Impaired: >78s
        # Adjust for number of circles (standard is 25)
        normalized_time = completion_time_sec * (25 / num_circles)
        
        if normalized_time < 29:
            performance_level = "Excellent"
            base_score = 100
        elif normalized_time < 40:
            performance_level = "Good"
            base_score = 85
        elif normalized_time < 78:
            performance_level = "Average"
            base_score = 70
        else:
            performance_level = "Needs Practice"
            base_score = 50
        
        # Penalize for errors (each error reduces score by 5 points)
        error_penalty = min(num_errors * 5, 30)
        score = max(base_score - error_penalty, 0)
        
        # Calculate processing speed (circles per second)
        processing_speed = num_circles / completion_time_sec if completion_time_sec > 0 else 0
        
        # Calculate accuracy (percentage of correct clicks)
        total_clicks = len(clicks)
        accuracy = ((total_clicks - num_errors) / total_clicks * 100) if total_clicks > 0 else 0
        
        # Calculate path efficiency (straight-line distance vs actual path)
        path_efficiency = TrailMakingATask._calculate_path_efficiency(trial["circles"], clicks)
        
        return {
            "score": round(score, 1),
            "completion_time": round(completion_time_sec, 2),
            "normalized_time": round(normalized_time, 2),
            "performance_level": performance_level,
            "errors": num_errors,
            "total_clicks": total_clicks,
            "accuracy": round(accuracy, 1),
            "processing_speed": round(processing_speed, 2),
            "path_efficiency": round(path_efficiency, 1),
        }
    
    @staticmethod
    def _calculate_path_efficiency(circles: List[Dict], clicks: List[Dict]) -> float:
        """
        Calculate how efficiently the user traced the path
        100% = perfect straight lines between circles
        """
        if len(clicks) < 2:
            return 100.0
        
        # Calculate ideal distance (straight lines between consecutive circles)
        ideal_distance = 0
        for i in range(len(circles) - 1):
            x1, y1 = circles[i]["x"], circles[i]["y"]
            x2, y2 = circles[i + 1]["x"], circles[i + 1]["y"]
            ideal_distance += ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        
        # Calculate actual distance (path through all clicks)
        actual_distance = 0
        for i in range(len(clicks) - 1):
            x1, y1 = clicks[i]["x"], clicks[i]["y"]
            x2, y2 = clicks[i + 1]["x"], clicks[i + 1]["y"]
            actual_distance += ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        
        if actual_distance == 0:
            return 100.0
        
        # Efficiency is ideal/actual (capped at 100%)
        efficiency = (ideal_distance / actual_distance) * 100
        return min(efficiency, 100.0)
    
    @staticmethod
    def determine_difficulty_adjustment(
        normalized_time: float, 
        errors: int, 
        difficulty: int
    ) -> Tuple[int, str]:
        """
        Determine if difficulty should change based on performance
        
        Args:
            normalized_time: Completion time normalized to 25 circles
            errors: Number of errors made
            difficulty: Current difficulty level
            
        Returns:
            Tuple of (new_difficulty, reason)
        """
        # Excellent performance with few errors - increase difficulty
        if normalized_time < 35 and errors <= 1 and difficulty < 10:
            return difficulty + 1, f"Excellent time ({normalized_time:.1f}s) - increased difficulty"
        
        # Poor performance or many errors - decrease difficulty
        elif (normalized_time > 80 or errors > 3) and difficulty > 1:
            return difficulty - 1, f"Slower time ({normalized_time:.1f}s) or errors ({errors}) - decreased difficulty"
        
        # Maintain current difficulty
        else:
            return difficulty, f"Good performance ({normalized_time:.1f}s, {errors} errors) - maintained difficulty"

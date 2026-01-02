"""
Multiple Object Tracking (MOT) Task
Clinical Validation: Pylyshyn & Storm (2006) - Dynamic visual attention
Measures: Sustained visual attention, divided attention, relevant for driving safety

Track multiple moving objects among identical distractors.
MS patients show deficits in dynamic attention and tracking abilities.
"""

from typing import Dict, Any, List
import random
import math
from datetime import datetime


class MultipleObjectTrackingTask:
    """
    Multiple Object Tracking task - track moving targets among distractors.
    
    Clinically validated measure of sustained visual attention and
    dynamic object tracking relevant for MS patients and driving safety.
    """
    
    # Task configurations by difficulty
    # Based on Pylyshyn & Storm (2006) and MS visual attention research
    # Very gradual progression for MS patients
    TRACKING_CONFIGS = {
        1: {"total_objects": 6, "targets": 1, "speed": 0.7, "tracking_duration": 8, "arena_size": 600},
        2: {"total_objects": 8, "targets": 1, "speed": 0.8, "tracking_duration": 8, "arena_size": 600},
        3: {"total_objects": 8, "targets": 1, "speed": 0.9, "tracking_duration": 10, "arena_size": 600},
        4: {"total_objects": 10, "targets": 1, "speed": 1.0, "tracking_duration": 10, "arena_size": 600},
        5: {"total_objects": 10, "targets": 1, "speed": 1.1, "tracking_duration": 10, "arena_size": 650},
        6: {"total_objects": 12, "targets": 1, "speed": 1.2, "tracking_duration": 10, "arena_size": 650},
        7: {"total_objects": 12, "targets": 2, "speed": 0.9, "tracking_duration": 10, "arena_size": 650},
        8: {"total_objects": 14, "targets": 2, "speed": 1.0, "tracking_duration": 12, "arena_size": 700},
        9: {"total_objects": 14, "targets": 2, "speed": 1.1, "tracking_duration": 12, "arena_size": 700},
        10: {"total_objects": 16, "targets": 3, "speed": 1.0, "tracking_duration": 12, "arena_size": 700}
    }
    
    OBJECT_RADIUS = 20  # Radius of each circle in pixels
    MIN_DISTANCE = 50   # Minimum distance between objects to prevent overlap
    
    @staticmethod
    def generate_trial(difficulty: int) -> Dict[str, Any]:
        """
        Generate a Multiple Object Tracking trial.
        
        Args:
            difficulty: 1-10 difficulty level
            
        Returns:
            Trial configuration with object positions and target indices
        """
        config = MultipleObjectTrackingTask.TRACKING_CONFIGS[difficulty]
        total_objects = config["total_objects"]
        num_targets = config["targets"]
        arena_size = config["arena_size"]
        
        # Generate initial positions for all objects (ensure no overlap)
        objects = []
        attempts = 0
        max_attempts = 1000
        
        while len(objects) < total_objects and attempts < max_attempts:
            attempts += 1
            
            # Random position within arena
            x = random.uniform(
                MultipleObjectTrackingTask.OBJECT_RADIUS + 10,
                arena_size - MultipleObjectTrackingTask.OBJECT_RADIUS - 10
            )
            y = random.uniform(
                MultipleObjectTrackingTask.OBJECT_RADIUS + 10,
                arena_size - MultipleObjectTrackingTask.OBJECT_RADIUS - 10
            )
            
            # Random velocity
            angle = random.uniform(0, 2 * math.pi)
            speed = config["speed"]
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            # Check if position is valid (not too close to existing objects)
            valid = True
            for obj in objects:
                dist = math.sqrt((x - obj["x"])**2 + (y - obj["y"])**2)
                if dist < MultipleObjectTrackingTask.MIN_DISTANCE:
                    valid = False
                    break
            
            if valid:
                objects.append({
                    "id": len(objects),
                    "x": x,
                    "y": y,
                    "vx": vx,
                    "vy": vy,
                    "is_target": False
                })
        
        # If we couldn't place all objects, reduce minimum distance requirement
        if len(objects) < total_objects:
            # Fallback: use grid-based positioning
            objects = MultipleObjectTrackingTask._generate_grid_positions(
                total_objects, arena_size, config["speed"]
            )
        
        # Randomly select target objects
        target_indices = random.sample(range(total_objects), num_targets)
        for idx in target_indices:
            objects[idx]["is_target"] = True
        
        return {
            "difficulty": difficulty,
            "total_objects": total_objects,
            "num_targets": num_targets,
            "tracking_duration": config["tracking_duration"],
            "arena_size": arena_size,
            "speed_multiplier": config["speed"],
            "objects": objects,
            "target_indices": target_indices,
            "trial_start_time": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def _generate_grid_positions(count: int, arena_size: int, speed: float) -> List[Dict[str, Any]]:
        """Fallback grid-based positioning when random placement fails."""
        objects = []
        grid_size = math.ceil(math.sqrt(count))
        spacing = arena_size / (grid_size + 1)
        
        for i in range(count):
            row = i // grid_size
            col = i % grid_size
            
            x = spacing * (col + 1) + random.uniform(-spacing/4, spacing/4)
            y = spacing * (row + 1) + random.uniform(-spacing/4, spacing/4)
            
            # Ensure within bounds
            x = max(MultipleObjectTrackingTask.OBJECT_RADIUS + 10, 
                   min(x, arena_size - MultipleObjectTrackingTask.OBJECT_RADIUS - 10))
            y = max(MultipleObjectTrackingTask.OBJECT_RADIUS + 10,
                   min(y, arena_size - MultipleObjectTrackingTask.OBJECT_RADIUS - 10))
            
            angle = random.uniform(0, 2 * math.pi)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            objects.append({
                "id": i,
                "x": x,
                "y": y,
                "vx": vx,
                "vy": vy,
                "is_target": False
            })
        
        return objects
    
    @staticmethod
    def score_response(
        trial_data: Dict[str, Any],
        user_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Score user's response to MOT trial.
        
        Args:
            trial_data: Original trial configuration
            user_response: User's selected object IDs and timing
            
        Returns:
            Scoring results with accuracy, precision, recall
        """
        target_indices = set(trial_data["target_indices"])
        selected_indices = set(user_response.get("selected_objects", []))
        total_targets = trial_data["num_targets"]
        response_time = user_response.get("response_time", 0)
        
        # Calculate confusion matrix values
        true_positives = len(target_indices & selected_indices)  # Correct targets selected
        false_positives = len(selected_indices - target_indices)  # Non-targets selected
        false_negatives = len(target_indices - selected_indices)  # Targets missed
        
        # Calculate metrics
        accuracy = true_positives / total_targets if total_targets > 0 else 0
        precision = true_positives / len(selected_indices) if len(selected_indices) > 0 else 0
        recall = accuracy  # Same as accuracy in this case
        
        # F1 score (harmonic mean of precision and recall)
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # Overall score (weighted combination)
        # Emphasize accuracy (getting all targets) over precision (avoiding false alarms)
        score = 0.7 * accuracy + 0.3 * precision
        
        # Performance classification
        if accuracy == 1.0 and false_positives == 0:
            performance = "perfect"
        elif accuracy >= 0.8 and precision >= 0.8:
            performance = "excellent"
        elif accuracy >= 0.6 and precision >= 0.6:
            performance = "good"
        elif accuracy >= 0.4:
            performance = "average"
        else:
            performance = "needs_improvement"
        
        # Tracking efficiency (how well user maintained attention)
        tracking_efficiency = 1.0 - (false_positives + false_negatives) / (total_targets * 2)
        tracking_efficiency = max(0, tracking_efficiency)
        
        return {
            "score": score,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "targets_found": true_positives,
            "targets_missed": false_negatives,
            "total_targets": total_targets,
            "performance": performance,
            "tracking_efficiency": tracking_efficiency,
            "response_time": response_time,
            "num_objects": trial_data["total_objects"],
            "tracking_duration": trial_data["tracking_duration"]
        }
    
    @staticmethod
    def calculate_difficulty_adjustment(
        recent_scores: List[float],
        current_difficulty: int,
        accuracy: float,
        precision: float
    ) -> int:
        """
        Calculate adaptive difficulty adjustment for MOT.
        
        Args:
            recent_scores: Last 5 trial scores
            current_difficulty: Current difficulty level (1-10)
            accuracy: Current trial accuracy (recall)
            precision: Current trial precision
            
        Returns:
            New difficulty level
        """
        if len(recent_scores) < 3:
            return current_difficulty
        
        avg_score = sum(recent_scores) / len(recent_scores)
        
        # Increase difficulty if consistently performing well
        if avg_score >= 0.85 and accuracy >= 0.8 and precision >= 0.8:
            return min(10, current_difficulty + 1)
        
        # Decrease if struggling
        elif avg_score < 0.5 or accuracy < 0.4:
            return max(1, current_difficulty - 1)
        
        # Stay at current level
        return current_difficulty
    
    @staticmethod
    def get_feedback_message(results: Dict[str, Any]) -> str:
        """Generate helpful feedback message based on performance."""
        accuracy = results["accuracy"]
        precision = results["precision"]
        false_positives = results["false_positives"]
        false_negatives = results["false_negatives"]
        
        if results["performance"] == "perfect":
            return "Perfect tracking! You identified all targets with no errors. Excellent sustained attention!"
        
        elif accuracy == 1.0 and false_positives > 0:
            return f"You found all {results['total_targets']} targets, but selected {false_positives} extra object(s). Try to be more selective."
        
        elif false_negatives > 0 and false_positives == 0:
            return f"Good precision, but you missed {false_negatives} target(s). Keep your eyes moving to track all objects."
        
        elif accuracy >= 0.6:
            return "Good tracking ability! With practice, you'll improve your sustained attention even more."
        
        else:
            return "Tracking multiple objects is challenging. Focus on one target at a time, then expand your attention."

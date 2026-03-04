"""
Inspection Time Task Service

Clinical Validation: Cognitive aging research, perceptual speed assessment
Measures: Pure perceptual processing speed without motor confound
MS Relevance: Excellent for MS - measures basic processing speed independent of motor function

Reference: Vickers, D., & Smith, P. (1986). The rationale for the inspection time index.
"""

from typing import Dict, List, Any, Optional
import random
from datetime import datetime

class InspectionTimeTask:
    """
    Inspection Time task - measures pure perceptual processing speed.
    
    Brief presentation of two lines, user identifies which is longer.
    Critical feature: Very short presentation time followed by mask.
    """
    
    # Difficulty levels: 10 levels with decreasing presentation times
    DIFFICULTY_CONFIG = {
        1: {
            "presentation_time_ms": 200,  # Very easy - plenty of time
            "trials_per_session": 15,
            "line_difference_min": 25,  # Minimum pixel difference
            "line_difference_max": 50,  # Maximum pixel difference
            "description": "Beginner - Clear differences, longer viewing time"
        },
        2: {
            "presentation_time_ms": 170,
            "trials_per_session": 15,
            "line_difference_min": 22,
            "line_difference_max": 45,
            "description": "Easy - Noticeable differences"
        },
        3: {
            "presentation_time_ms": 140,
            "trials_per_session": 18,
            "line_difference_min": 20,
            "line_difference_max": 40,
            "description": "Moderate - Shorter viewing time"
        },
        4: {
            "presentation_time_ms": 120,
            "trials_per_session": 18,
            "line_difference_min": 18,
            "line_difference_max": 35,
            "description": "Intermediate - Quick perception needed"
        },
        5: {
            "presentation_time_ms": 110,
            "trials_per_session": 20,
            "line_difference_min": 15,
            "line_difference_max": 30,
            "description": "Standard - Average perceptual speed"
        },
        6: {
            "presentation_time_ms": 100,
            "trials_per_session": 20,
            "line_difference_min": 15,
            "line_difference_max": 28,
            "description": "Challenging - Rapid perception required"
        },
        7: {
            "presentation_time_ms": 90,
            "trials_per_session": 22,
            "line_difference_min": 12,
            "line_difference_max": 25,
            "description": "Advanced - Very brief exposure"
        },
        8: {
            "presentation_time_ms": 80,
            "trials_per_session": 22,
            "line_difference_min": 12,
            "line_difference_max": 22,
            "description": "Expert - Subtle differences"
        },
        9: {
            "presentation_time_ms": 75,
            "trials_per_session": 25,
            "line_difference_min": 10,
            "line_difference_max": 20,
            "description": "Master - Minimal viewing time"
        },
        10: {
            "presentation_time_ms": 70,
            "trials_per_session": 25,
            "line_difference_min": 10,
            "line_difference_max": 18,
            "description": "Elite - Extreme challenge"
        }
    }
    
    # Base line height and mask pattern
    BASE_LINE_HEIGHT = 150  # pixels
    LINE_WIDTH = 8  # pixels
    MASK_DURATION_MS = 500  # How long to show mask
    
    def __init__(self):
        self.session_data = {}
    
    def generate_trial(self, difficulty: int = 5) -> Dict[str, Any]:
        """
        Generate a single inspection time trial.
        
        Returns:
            trial_data containing line configurations, presentation time, etc.
        """
        config = self.DIFFICULTY_CONFIG.get(difficulty, self.DIFFICULTY_CONFIG[5])
        
        # Determine which line is longer (left or right)
        longer_side = random.choice(["left", "right"])
        
        # Generate line heights with appropriate difference
        difference = random.randint(
            config["line_difference_min"],
            config["line_difference_max"]
        )
        
        if longer_side == "left":
            left_height = self.BASE_LINE_HEIGHT + difference
            right_height = self.BASE_LINE_HEIGHT
        else:
            left_height = self.BASE_LINE_HEIGHT
            right_height = self.BASE_LINE_HEIGHT + difference
        
        trial_data = {
            "left_height": left_height,
            "right_height": right_height,
            "longer_side": longer_side,
            "difference_pixels": difference,
            "presentation_time_ms": config["presentation_time_ms"],
            "mask_duration_ms": self.MASK_DURATION_MS,
            "line_width": self.LINE_WIDTH,
            "difficulty": difficulty
        }
        
        return trial_data
    
    def generate_session(self, difficulty: int = 5) -> Dict[str, Any]:
        """
        Generate a complete inspection time session with multiple trials.
        """
        config = self.DIFFICULTY_CONFIG.get(difficulty, self.DIFFICULTY_CONFIG[5])
        num_trials = config["trials_per_session"]
        
        trials = []
        for i in range(num_trials):
            trial = self.generate_trial(difficulty)
            trial["trial_number"] = i + 1
            trials.append(trial)
        
        session_id = f"inspection_time_{datetime.utcnow().timestamp()}"
        
        session_data = {
            "session_id": session_id,
            "difficulty": difficulty,
            "trials": trials,
            "total_trials": num_trials,
            "config": config,
            "presentation_time_ms": config["presentation_time_ms"]
        }
        
        # Store session data
        self.session_data[session_id] = {
            "trials": trials,
            "started_at": datetime.utcnow(),
            "difficulty": difficulty
        }
        
        return session_data
    
    def score_response(
        self,
        session_id: str,
        trial_index: int,
        user_answer: str,
        reaction_time: float,
        difficulty: int
    ) -> Dict[str, Any]:
        """
        Score a single trial response.
        
        Args:
            session_id: Session identifier
            trial_index: Index of the trial in the session
            user_answer: "left" or "right"
            reaction_time: Time from mask appearance to response (ms)
            difficulty: Current difficulty level
        
        Returns:
            Scoring metrics
        """
        session = self.session_data.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        trial = session["trials"][trial_index]
        correct_answer = trial["longer_side"]
        
        is_correct = user_answer.lower() == correct_answer
        
        # Score based on correctness
        trial_score = 100 if is_correct else 0
        
        return {
            "is_correct": is_correct,
            "trial_score": trial_score,
            "reaction_time": reaction_time,
            "correct_answer": correct_answer,
            "difference_pixels": trial["difference_pixels"]
        }
    
    def score_session(
        self,
        session_id: str,
        responses: List[Dict[str, Any]],
        difficulty: int
    ) -> Dict[str, Any]:
        """
        Score entire session and determine performance metrics.
        
        Args:
            session_id: Session identifier
            responses: List of {trial_index, user_answer, reaction_time}
            difficulty: Difficulty level
        
        Returns:
            Complete scoring with adaptation recommendations
        """
        session = self.session_data.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        total_trials = len(session["trials"])
        correct_count = 0
        total_reaction_time = 0
        trial_scores = []
        
        # Score each response
        for response in responses:
            result = self.score_response(
                session_id,
                response["trial_index"],
                response["user_answer"],
                response["reaction_time"],
                difficulty
            )
            
            if result.get("is_correct"):
                correct_count += 1
            
            total_reaction_time += response["reaction_time"]
            trial_scores.append(result["trial_score"])
        
        # Calculate metrics
        accuracy = (correct_count / total_trials * 100) if total_trials > 0 else 0
        average_reaction_time = total_reaction_time / total_trials if total_trials > 0 else 0
        
        # Overall score: primarily based on accuracy
        overall_score = sum(trial_scores) / len(trial_scores) if trial_scores else 0
        
        # Performance classification based on accuracy and presentation time
        config = self.DIFFICULTY_CONFIG.get(difficulty, self.DIFFICULTY_CONFIG[5])
        presentation_time = config["presentation_time_ms"]
        
        # Classification considers both accuracy and difficulty level
        if accuracy >= 90:
            if presentation_time <= 70:
                performance_level = "Excellent"
            elif presentation_time <= 120:
                performance_level = "Very Good"
            else:
                performance_level = "Good"
        elif accuracy >= 75:
            performance_level = "Good"
        elif accuracy >= 60:
            performance_level = "Average"
        else:
            performance_level = "Needs Practice"
        
        # Consistency (standard deviation of reaction times)
        if len(responses) > 1:
            rt_values = [r["reaction_time"] for r in responses]
            mean_rt = sum(rt_values) / len(rt_values)
            variance = sum((rt - mean_rt) ** 2 for rt in rt_values) / len(rt_values)
            std_dev = variance ** 0.5
            # Lower std_dev = higher consistency
            consistency = max(0, 100 - (std_dev / mean_rt * 100) if mean_rt > 0 else 50)
        else:
            consistency = 50
        
        # Perceptual speed index (based on accuracy at given presentation time)
        # Higher accuracy at shorter presentation = better perceptual speed
        perceptual_speed_index = (accuracy / 100) * (200 / max(50, presentation_time)) * 100
        
        metrics = {
            "score": round(overall_score, 1),
            "accuracy": round(accuracy, 1),
            "correct_count": correct_count,
            "total_trials": total_trials,
            "average_reaction_time": round(average_reaction_time, 1),
            "consistency": round(consistency, 1),
            "performance_level": performance_level,
            "presentation_time_ms": presentation_time,
            "perceptual_speed_index": round(perceptual_speed_index, 1)
        }
        
        # Determine difficulty adjustment
        adjustment = self.determine_difficulty_adjustment(
            accuracy,
            presentation_time,
            difficulty
        )
        
        return {
            "metrics": metrics,
            "difficulty_adjustment": adjustment["new_difficulty"],
            "adaptation_reason": adjustment["reason"]
        }
    
    def determine_difficulty_adjustment(
        self,
        accuracy: float,
        presentation_time: int,
        current_difficulty: int
    ) -> Dict[str, Any]:
        """
        Determine if difficulty should be adjusted based on performance.
        """
        new_difficulty = current_difficulty
        reason = "Maintaining current difficulty"
        
        # Excellent performance at this speed - increase difficulty
        if accuracy >= 90:
            if current_difficulty < 10:
                new_difficulty = min(10, current_difficulty + 1)
                reason = f"Excellent accuracy at {presentation_time}ms - reducing presentation time"
        
        # Very good performance - small increase
        elif accuracy >= 80:
            if current_difficulty < 10 and random.random() < 0.5:
                new_difficulty = min(10, current_difficulty + 1)
                reason = "Strong perceptual speed - ready for briefer exposure"
        
        # Poor performance - decrease difficulty
        elif accuracy < 60:
            if current_difficulty > 1:
                new_difficulty = max(1, current_difficulty - 1)
                reason = f"Increasing presentation time to build perceptual skills"
        
        # Below average - small decrease
        elif accuracy < 70:
            if current_difficulty > 1 and random.random() < 0.3:
                new_difficulty = max(1, current_difficulty - 1)
                reason = "Adjusting presentation time for optimal learning"
        
        return {
            "new_difficulty": new_difficulty,
            "reason": reason
        }

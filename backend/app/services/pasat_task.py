"""
Paced Auditory Serial Addition Test (PASAT) Service

Clinical Validation: ⭐⭐⭐⭐⭐ MS GOLD STANDARD
Measures: Sustained attention + working memory + processing speed under pressure
MS Relevance: Most widely used MS cognitive test historically

Reference: Gronwall, D. M. A. (1977). Paced Auditory Serial-Addition Task
"""

from typing import Dict, List, Any, Optional
import random
from datetime import datetime

class PASATTask:
    """
    PASAT - Add each new digit to the previous digit, ignore running total.
    
    Example: Hear "3... 5... 2..." → Answer "8" (3+5), then "7" (5+2)
    
    Classic MS assessment tool measuring sustained attention and working memory.
    """
    
    # Difficulty levels: 10 levels with decreasing inter-stimulus intervals
    DIFFICULTY_CONFIG = {
        1: {
            "interval_seconds": 4.0,  # PASAT-4 (easiest)
            "total_trials": 15,
            "digit_range": (1, 9),
            "description": "Beginner - 4 second intervals, plenty of time"
        },
        2: {
            "interval_seconds": 3.8,
            "total_trials": 20,
            "digit_range": (1, 9),
            "description": "Easy - Comfortable pace"
        },
        3: {
            "interval_seconds": 3.5,
            "total_trials": 25,
            "digit_range": (1, 9),
            "description": "Moderate - Approaching standard PASAT-3"
        },
        4: {
            "interval_seconds": 3.0,  # PASAT-3 (standard)
            "total_trials": 30,
            "digit_range": (1, 9),
            "description": "Standard - PASAT-3, clinical norm"
        },
        5: {
            "interval_seconds": 2.8,
            "total_trials": 35,
            "digit_range": (1, 9),
            "description": "Intermediate - Faster than standard"
        },
        6: {
            "interval_seconds": 2.5,
            "total_trials": 40,
            "digit_range": (1, 9),
            "description": "Challenging - Quick sustained attention"
        },
        7: {
            "interval_seconds": 2.2,
            "total_trials": 45,
            "digit_range": (1, 9),
            "description": "Advanced - Approaching PASAT-2"
        },
        8: {
            "interval_seconds": 2.0,  # PASAT-2 (hard)
            "total_trials": 50,
            "digit_range": (1, 9),
            "description": "Expert - PASAT-2, high demand"
        },
        9: {
            "interval_seconds": 1.8,
            "total_trials": 55,
            "digit_range": (1, 9),
            "description": "Master - Very rapid pace"
        },
        10: {
            "interval_seconds": 1.6,
            "total_trials": 60,
            "digit_range": (1, 9),
            "description": "Elite - Extreme sustained attention challenge"
        }
    }
    
    def __init__(self):
        self.session_data = {}
    
    def generate_digit_sequence(self, num_trials: int, digit_range: tuple) -> List[int]:
        """
        Generate sequence of random digits for PASAT.
        
        Args:
            num_trials: Number of digits to generate
            digit_range: Tuple of (min, max) for digit range
        
        Returns:
            List of random digits
        """
        digits = []
        for _ in range(num_trials):
            digit = random.randint(digit_range[0], digit_range[1])
            digits.append(digit)
        
        return digits
    
    def calculate_correct_answers(self, digits: List[int]) -> List[int]:
        """
        Calculate the correct answer for each trial.
        
        Args:
            digits: List of digits presented
        
        Returns:
            List of correct sums (digit[i-1] + digit[i])
        """
        correct_answers = []
        
        for i in range(1, len(digits)):
            correct_sum = digits[i-1] + digits[i]
            correct_answers.append(correct_sum)
        
        return correct_answers
    
    def generate_session(self, difficulty: int = 4, visual_mode: bool = True) -> Dict[str, Any]:
        """
        Generate a complete PASAT session.
        
        Args:
            difficulty: Difficulty level 1-10
            visual_mode: If True, show digits visually (less stressful than audio-only)
        
        Returns:
            Session data with digit sequence, correct answers, timing
        """
        config = self.DIFFICULTY_CONFIG.get(difficulty, self.DIFFICULTY_CONFIG[4])
        
        # Generate digit sequence
        digits = self.generate_digit_sequence(
            config["total_trials"],
            config["digit_range"]
        )
        
        # Calculate correct answers
        correct_answers = self.calculate_correct_answers(digits)
        
        # Build trials
        trials = []
        for i in range(len(digits)):
            trial = {
                "trial_number": i + 1,
                "digit": digits[i],
                "is_first": i == 0,  # First digit has no answer
                "correct_answer": correct_answers[i-1] if i > 0 else None,
                "previous_digit": digits[i-1] if i > 0 else None
            }
            trials.append(trial)
        
        session_id = f"pasat_{datetime.utcnow().timestamp()}"
        
        session_data = {
            "session_id": session_id,
            "difficulty": difficulty,
            "interval_seconds": config["interval_seconds"],
            "total_trials": config["total_trials"],
            "visual_mode": visual_mode,
            "digits": digits,
            "correct_answers": correct_answers,
            "trials": trials,
            "config": config
        }
        
        # Store session data
        self.session_data[session_id] = {
            "digits": digits,
            "correct_answers": correct_answers,
            "started_at": datetime.utcnow(),
            "difficulty": difficulty,
            "interval_seconds": config["interval_seconds"]
        }
        
        return session_data
    
    def score_response(
        self,
        session_id: str,
        trial_index: int,
        user_answer: Optional[int],
        reaction_time: float
    ) -> Dict[str, Any]:
        """
        Score a single trial response.
        
        Args:
            session_id: Session identifier
            trial_index: Index of the trial (0-based, but trial 0 has no answer)
            user_answer: User's answer (sum of previous two digits)
            reaction_time: Time taken to respond (ms)
        
        Returns:
            Scoring metrics for this trial
        """
        session = self.session_data.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        # First trial has no answer
        if trial_index == 0:
            return {
                "is_correct": None,
                "trial_score": 0,
                "correct_answer": None,
                "skipped": True
            }
        
        correct_answer = session["correct_answers"][trial_index - 1]
        
        # No response counts as incorrect
        if user_answer is None:
            is_correct = False
        else:
            is_correct = (user_answer == correct_answer)
        
        trial_score = 100 if is_correct else 0
        
        return {
            "is_correct": is_correct,
            "trial_score": trial_score,
            "correct_answer": correct_answer,
            "user_answer": user_answer,
            "reaction_time": reaction_time
        }
    
    def score_session(
        self,
        session_id: str,
        responses: List[Dict[str, Any]],
        difficulty: int
    ) -> Dict[str, Any]:
        """
        Score entire PASAT session.
        
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
        
        # Filter out first trial (no answer required)
        scoreable_responses = [r for r in responses if r.get("trial_index", 0) > 0]
        total_trials = len(scoreable_responses)
        
        correct_count = 0
        total_reaction_time = 0
        reaction_times = []
        
        # Score each response
        for response in scoreable_responses:
            result = self.score_response(
                session_id,
                response["trial_index"],
                response.get("user_answer"),
                response["reaction_time"]
            )
            
            if result.get("is_correct"):
                correct_count += 1
            
            total_reaction_time += response["reaction_time"]
            reaction_times.append(response["reaction_time"])
        
        # Calculate metrics
        accuracy = (correct_count / total_trials * 100) if total_trials > 0 else 0
        average_reaction_time = total_reaction_time / total_trials if total_trials > 0 else 0
        
        # Overall score (accuracy is primary metric for PASAT)
        overall_score = accuracy
        
        # Performance classification based on MS norms
        interval = session["interval_seconds"]
        
        if accuracy >= 90:
            if interval <= 2.0:
                performance_level = "Excellent"
            elif interval <= 3.0:
                performance_level = "Very Good"
            else:
                performance_level = "Good"
        elif accuracy >= 75:
            performance_level = "Good"
        elif accuracy >= 60:
            performance_level = "Average"
        elif accuracy >= 40:
            performance_level = "Fair"
        else:
            performance_level = "Needs Practice"
        
        # Consistency (coefficient of variation of reaction times)
        if len(reaction_times) > 1:
            mean_rt = sum(reaction_times) / len(reaction_times)
            variance = sum((rt - mean_rt) ** 2 for rt in reaction_times) / len(reaction_times)
            std_dev = variance ** 0.5
            cv = (std_dev / mean_rt * 100) if mean_rt > 0 else 100
            consistency = max(0, 100 - cv)
        else:
            consistency = 50
        
        # Calculate sustained attention metric
        # Compare first third vs last third performance (fatigue indicator)
        third = len(scoreable_responses) // 3
        if third > 0:
            first_third = scoreable_responses[:third]
            last_third = scoreable_responses[-third:]
            
            first_third_correct = sum(1 for r in first_third if self.score_response(
                session_id, r["trial_index"], r.get("user_answer"), r["reaction_time"]
            ).get("is_correct"))
            
            last_third_correct = sum(1 for r in last_third if self.score_response(
                session_id, r["trial_index"], r.get("user_answer"), r["reaction_time"]
            ).get("is_correct"))
            
            sustained_attention = (last_third_correct / len(last_third) * 100) if len(last_third) > 0 else 0
            fatigue_effect = (first_third_correct / len(first_third) * 100) - sustained_attention if len(first_third) > 0 else 0
        else:
            sustained_attention = accuracy
            fatigue_effect = 0
        
        metrics = {
            "score": round(overall_score, 1),
            "accuracy": round(accuracy, 1),
            "correct_count": correct_count,
            "total_trials": total_trials,
            "average_reaction_time": round(average_reaction_time, 1),
            "consistency": round(consistency, 1),
            "sustained_attention": round(sustained_attention, 1),
            "fatigue_effect": round(fatigue_effect, 1),
            "performance_level": performance_level,
            "interval_seconds": interval
        }
        
        # Determine difficulty adjustment
        adjustment = self.determine_difficulty_adjustment(
            accuracy,
            interval,
            difficulty,
            fatigue_effect
        )
        
        return {
            "metrics": metrics,
            "difficulty_adjustment": adjustment["new_difficulty"],
            "adaptation_reason": adjustment["reason"]
        }
    
    def determine_difficulty_adjustment(
        self,
        accuracy: float,
        interval_seconds: float,
        current_difficulty: int,
        fatigue_effect: float
    ) -> Dict[str, Any]:
        """
        Determine if difficulty should be adjusted based on performance.
        """
        new_difficulty = current_difficulty
        reason = "Maintaining current difficulty"
        
        # Excellent performance with low fatigue - increase difficulty
        if accuracy >= 85 and fatigue_effect < 10:
            if current_difficulty < 10:
                new_difficulty = min(10, current_difficulty + 1)
                reason = f"Excellent performance at {interval_seconds}s intervals - reducing interval"
        
        # Very good performance - small increase
        elif accuracy >= 75 and fatigue_effect < 15:
            if current_difficulty < 10 and random.random() < 0.5:
                new_difficulty = min(10, current_difficulty + 1)
                reason = "Strong sustained attention - ready for faster pace"
        
        # Poor performance or high fatigue - decrease difficulty
        elif accuracy < 50 or fatigue_effect > 25:
            if current_difficulty > 1:
                new_difficulty = max(1, current_difficulty - 1)
                reason = f"Slowing pace to reduce cognitive load"
        
        # Below average - small decrease
        elif accuracy < 65:
            if current_difficulty > 1 and random.random() < 0.3:
                new_difficulty = max(1, current_difficulty - 1)
                reason = "Adjusting interval for optimal challenge level"
        
        return {
            "new_difficulty": new_difficulty,
            "reason": reason
        }

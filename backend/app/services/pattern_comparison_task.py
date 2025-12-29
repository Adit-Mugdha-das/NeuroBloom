"""
Pattern Comparison (Visual Matching) Task Service

Clinical Validation: Woodcock-Johnson Tests of Cognitive Abilities
Measures: Pure processing speed with minimal motor requirements
MS Relevance: Excellent for MS patients - minimal motor demands, pure speed assessment

Reference: Salthouse, T. A. (1996). The processing-speed theory of adult age differences in cognition.
"""

from typing import Dict, List, Any, Optional
import random
from datetime import datetime

class PatternComparisonTask:
    """
    Pattern Comparison (Visual Matching) task from Woodcock-Johnson Tests.
    Presents two patterns and user must decide if they are SAME or DIFFERENT.
    
    Pure processing speed measure with minimal motor requirements.
    """
    
    # Difficulty levels: 10 levels with varying complexity and time pressure
    DIFFICULTY_CONFIG = {
        1: {
            "pattern_type": "simple_geometric",
            "pattern_size": 3,  # 3x3 grid
            "trials_per_session": 10,
            "time_per_trial": 2.5,  # seconds
            "similarity_level": 0.3  # How similar different patterns can be (0-1)
        },
        2: {
            "pattern_type": "simple_geometric",
            "pattern_size": 3,
            "trials_per_session": 12,
            "time_per_trial": 2.2,
            "similarity_level": 0.4
        },
        3: {
            "pattern_type": "simple_geometric",
            "pattern_size": 4,  # 4x4 grid
            "trials_per_session": 12,
            "time_per_trial": 2.0,
            "similarity_level": 0.5
        },
        4: {
            "pattern_type": "complex",
            "pattern_size": 4,
            "trials_per_session": 15,
            "time_per_trial": 1.8,
            "similarity_level": 0.6
        },
        5: {
            "pattern_type": "complex",
            "pattern_size": 4,
            "trials_per_session": 15,
            "time_per_trial": 1.6,
            "similarity_level": 0.65
        },
        6: {
            "pattern_type": "complex",
            "pattern_size": 5,  # 5x5 grid
            "trials_per_session": 15,
            "time_per_trial": 1.5,
            "similarity_level": 0.7
        },
        7: {
            "pattern_type": "abstract",
            "pattern_size": 5,
            "trials_per_session": 18,
            "time_per_trial": 1.3,
            "similarity_level": 0.75
        },
        8: {
            "pattern_type": "abstract",
            "pattern_size": 5,
            "trials_per_session": 18,
            "time_per_trial": 1.2,
            "similarity_level": 0.8
        },
        9: {
            "pattern_type": "abstract",
            "pattern_size": 6,  # 6x6 grid
            "trials_per_session": 20,
            "time_per_trial": 1.1,
            "similarity_level": 0.85
        },
        10: {
            "pattern_type": "abstract",
            "pattern_size": 6,
            "trials_per_session": 20,
            "time_per_trial": 1.0,
            "similarity_level": 0.9
        }
    }
    
    # Pattern elements for different types
    SIMPLE_GEOMETRIC_SHAPES = ["■", "●", "▲", "◆", "★"]
    COMPLEX_SHAPES = ["◎", "◉", "◐", "◑", "◒", "◓", "◔", "◕", "◖", "◗"]
    ABSTRACT_SYMBOLS = ["◈", "◇", "◊", "○", "◌", "◍", "◎", "●", "◐", "◑", "◒", "◓", "◔", "◕", "◖", "◗", "☆", "★", "✦", "✧"]
    
    def __init__(self):
        self.session_data = {}
    
    def generate_trial(self, difficulty: int = 5) -> Dict[str, Any]:
        """
        Generate a pattern comparison trial.
        
        Returns:
            trial_data containing pattern_a, pattern_b, correct_answer, time_limit
        """
        config = self.DIFFICULTY_CONFIG.get(difficulty, self.DIFFICULTY_CONFIG[5])
        
        # Get shape set based on pattern type
        if config["pattern_type"] == "simple_geometric":
            shapes = self.SIMPLE_GEOMETRIC_SHAPES
        elif config["pattern_type"] == "complex":
            shapes = self.COMPLEX_SHAPES
        else:  # abstract
            shapes = self.ABSTRACT_SYMBOLS
        
        size = config["pattern_size"]
        
        # Generate pattern A
        pattern_a = self._generate_pattern(size, shapes)
        
        # Decide if patterns should be same or different (50/50 chance)
        is_same = random.choice([True, False])
        
        if is_same:
            # Make pattern B identical to A
            pattern_b = [row[:] for row in pattern_a]  # Deep copy
            correct_answer = "SAME"
        else:
            # Make pattern B similar but different
            pattern_b = self._generate_similar_pattern(
                pattern_a, 
                shapes, 
                config["similarity_level"]
            )
            correct_answer = "DIFFERENT"
        
        trial_data = {
            "pattern_a": pattern_a,
            "pattern_b": pattern_b,
            "correct_answer": correct_answer,
            "time_limit": config["time_per_trial"],
            "pattern_size": size,
            "pattern_type": config["pattern_type"],
            "difficulty": difficulty,
            "trials_per_session": config["trials_per_session"]
        }
        
        return trial_data
    
    def _generate_pattern(self, size: int, shapes: List[str]) -> List[List[str]]:
        """Generate a random pattern grid"""
        pattern = []
        for _ in range(size):
            row = [random.choice(shapes) for _ in range(size)]
            pattern.append(row)
        return pattern
    
    def _generate_similar_pattern(
        self, 
        original: List[List[str]], 
        shapes: List[str], 
        similarity: float
    ) -> List[List[str]]:
        """
        Generate a pattern similar to the original but with some differences.
        similarity: 0.0 (very different) to 1.0 (almost identical)
        """
        size = len(original)
        new_pattern = [row[:] for row in original]  # Start with copy
        
        # Calculate number of cells to change (lower similarity = more changes)
        total_cells = size * size
        # At similarity 0.9, change ~2 cells; at 0.3, change ~14 cells (for 5x5)
        num_changes = max(1, int(total_cells * (1 - similarity)))
        
        # Randomly change some cells
        changed_positions = set()
        attempts = 0
        while len(changed_positions) < num_changes and attempts < num_changes * 3:
            row = random.randint(0, size - 1)
            col = random.randint(0, size - 1)
            if (row, col) not in changed_positions:
                # Change to a different shape
                current_shape = new_pattern[row][col]
                available_shapes = [s for s in shapes if s != current_shape]
                if available_shapes:
                    new_pattern[row][col] = random.choice(available_shapes)
                    changed_positions.add((row, col))
            attempts += 1
        
        return new_pattern
    
    def generate_session(self, difficulty: int = 5) -> Dict[str, Any]:
        """
        Generate a complete session with multiple trials.
        Trials vary in complexity throughout the session.
        """
        config = self.DIFFICULTY_CONFIG.get(difficulty, self.DIFFICULTY_CONFIG[5])
        num_trials = config["trials_per_session"]
        
        trials = []
        
        # Create variation within session based on difficulty level
        # Mix of current difficulty and adjacent levels for variety
        difficulty_variations = self._get_difficulty_variations(difficulty, num_trials)
        
        for i, trial_difficulty in enumerate(difficulty_variations):
            trial = self.generate_trial(trial_difficulty)
            # Add trial number for tracking
            trial["trial_number"] = i + 1
            trials.append(trial)
        
        session_id = f"pattern_comparison_{datetime.utcnow().timestamp()}"
        
        session_data = {
            "session_id": session_id,
            "difficulty": difficulty,
            "trials": trials,
            "total_trials": num_trials,
            "config": config
        }
        
        # Store session data
        self.session_data[session_id] = {
            "trials": trials,
            "started_at": datetime.utcnow(),
            "difficulty": difficulty
        }
        
        return session_data
    
    def _get_difficulty_variations(self, base_difficulty: int, num_trials: int) -> List[int]:
        """
        Generate difficulty variations for trials within a session.
        Creates a mix of current, slightly easier, and slightly harder trials.
        """
        variations = []
        
        # Calculate difficulty range (±1 from base, clamped to 1-10)
        min_diff = max(1, base_difficulty - 1)
        max_diff = min(10, base_difficulty + 1)
        
        # Create a progression pattern
        for i in range(num_trials):
            progress = i / max(1, num_trials - 1)  # 0.0 to 1.0
            
            # Early trials: easier (70% base, 30% easier)
            # Middle trials: mixed (50% base, 25% easier, 25% harder)
            # Late trials: harder (60% base, 40% harder)
            
            if progress < 0.3:  # First 30% of trials
                # More easier trials to warm up
                if random.random() < 0.3:
                    trial_diff = min_diff
                else:
                    trial_diff = base_difficulty
            elif progress < 0.7:  # Middle 40% of trials
                # Balanced mix
                rand = random.random()
                if rand < 0.25 and min_diff < base_difficulty:
                    trial_diff = min_diff
                elif rand < 0.75:
                    trial_diff = base_difficulty
                else:
                    trial_diff = max_diff
            else:  # Last 30% of trials
                # More challenging trials
                if random.random() < 0.4 and max_diff > base_difficulty:
                    trial_diff = max_diff
                else:
                    trial_diff = base_difficulty
            
            variations.append(trial_diff)
        
        return variations
    
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
            user_answer: "SAME" or "DIFFERENT"
            reaction_time: Time taken in seconds
            difficulty: Current difficulty level
        
        Returns:
            Scoring metrics
        """
        session = self.session_data.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        trial = session["trials"][trial_index]
        correct_answer = trial["correct_answer"]
        time_limit = trial["time_limit"]
        
        is_correct = user_answer.upper() == correct_answer
        is_timeout = reaction_time > time_limit
        
        # Calculate accuracy score
        if is_correct and not is_timeout:
            trial_score = 100
        elif is_correct and is_timeout:
            # Partial credit for correct but slow
            trial_score = 60
        else:
            trial_score = 0
        
        return {
            "is_correct": is_correct,
            "is_timeout": is_timeout,
            "trial_score": trial_score,
            "reaction_time": reaction_time,
            "time_limit": time_limit,
            "correct_answer": correct_answer
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
        total_time = 0
        timeout_count = 0
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
            if result.get("is_timeout"):
                timeout_count += 1
            
            total_time += response["reaction_time"]
            trial_scores.append(result["trial_score"])
        
        # Calculate metrics
        accuracy = (correct_count / total_trials * 100) if total_trials > 0 else 0
        average_reaction_time = total_time / total_trials if total_trials > 0 else 0
        
        # Calculate processing speed (correct responses per minute)
        total_time_minutes = total_time / 60
        processing_speed = correct_count / total_time_minutes if total_time_minutes > 0 else 0
        
        # Overall score: weighted combination
        overall_score = sum(trial_scores) / len(trial_scores) if trial_scores else 0
        
        # Apply timeout penalty
        timeout_penalty = timeout_count * 5
        overall_score = max(0, overall_score - timeout_penalty)
        
        # Performance classification based on MS norms
        # Salthouse (1996) norms for pattern comparison
        if processing_speed >= 35:
            performance_level = "Excellent"
        elif processing_speed >= 25:
            performance_level = "Good"
        elif processing_speed >= 15:
            performance_level = "Average"
        else:
            performance_level = "Needs Practice"
        
        # Consistency (standard deviation of reaction times)
        if len(responses) > 1:
            rt_values = [r["reaction_time"] for r in responses]
            mean_rt = sum(rt_values) / len(rt_values)
            variance = sum((rt - mean_rt) ** 2 for rt in rt_values) / len(rt_values)
            std_dev = variance ** 0.5
            consistency = max(0, 100 - (std_dev * 50))  # Lower std_dev = higher consistency
        else:
            consistency = 50
        
        metrics = {
            "score": round(overall_score, 1),
            "accuracy": round(accuracy, 1),
            "correct_count": correct_count,
            "total_trials": total_trials,
            "average_reaction_time": round(average_reaction_time, 3),
            "processing_speed": round(processing_speed, 1),
            "timeout_count": timeout_count,
            "consistency": round(consistency, 1),
            "performance_level": performance_level,
            "total_time": round(total_time, 2)
        }
        
        # Determine difficulty adjustment
        adjustment = self.determine_difficulty_adjustment(
            accuracy, 
            processing_speed,
            timeout_count,
            total_trials,
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
        processing_speed: float,
        timeout_count: int,
        total_trials: int,
        current_difficulty: int
    ) -> Dict[str, Any]:
        """
        Determine if difficulty should be adjusted based on performance.
        """
        new_difficulty = current_difficulty
        reason = "Maintaining current difficulty"
        
        # Excellent performance - increase difficulty
        if accuracy >= 90 and processing_speed >= 30 and timeout_count <= 2:
            if current_difficulty < 10:
                new_difficulty = min(10, current_difficulty + 1)
                reason = "Excellent accuracy and speed - increasing challenge"
        
        # Very good performance - small increase
        elif accuracy >= 85 and processing_speed >= 25 and timeout_count <= 3:
            if current_difficulty < 10 and random.random() < 0.5:
                new_difficulty = min(10, current_difficulty + 1)
                reason = "Strong performance - ready for more complexity"
        
        # Poor performance - decrease difficulty
        elif accuracy < 60 or timeout_count > total_trials * 0.4:
            if current_difficulty > 1:
                new_difficulty = max(1, current_difficulty - 1)
                reason = "Reducing complexity to build confidence and speed"
        
        # Below average - small decrease
        elif accuracy < 70 or processing_speed < 15:
            if current_difficulty > 1 and random.random() < 0.3:
                new_difficulty = max(1, current_difficulty - 1)
                reason = "Adjusting difficulty to optimize learning"
        
        return {
            "new_difficulty": new_difficulty,
            "reason": reason
        }

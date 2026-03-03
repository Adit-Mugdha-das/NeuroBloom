"""
Wisconsin Card Sorting Test (WCST) Task Service

Clinical validation: Classic executive function test measuring set-shifting,
rule learning, and cognitive flexibility.

Reference: Beatty et al., 1995 - MS cognitive impairment sensitivity
"""

import random
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime


class WCSTTask:
    """
    Wisconsin Card Sorting Test implementation
    
    Cards vary by three dimensions:
    - Color: red, blue, green, yellow
    - Shape: circle, star, triangle, cross
    - Number: 1, 2, 3, 4
    
    User must sort cards by matching rule (color/shape/number).
    Rule changes after 10 correct sorts without warning.
    User must infer the new rule from feedback.
    """
    
    # Card attributes
    COLORS = ["red", "blue", "green", "yellow"]
    SHAPES = ["circle", "star", "triangle", "cross"]
    NUMBERS = [1, 2, 3, 4]
    RULES = ["color", "shape", "number"]
    
    # Difficulty configuration
    DIFFICULTY_CONFIG = {
        1: {
            "trials": 40,
            "feedback_clarity": "obvious",  # Very clear "Correct!"/"Wrong!"
            "rule_change_warning": True,  # Subtle hint when rule changes
            "feedback_delay_ms": 0,
            "correct_needed": 10,  # Correct sorts needed before rule change
        },
        2: {
            "trials": 48,
            "feedback_clarity": "obvious",
            "rule_change_warning": True,
            "feedback_delay_ms": 0,
            "correct_needed": 10,
        },
        3: {
            "trials": 56,
            "feedback_clarity": "clear",  # Clear feedback
            "rule_change_warning": False,  # No warning
            "feedback_delay_ms": 200,
            "correct_needed": 9,  # Smoother progression
        },
        4: {
            "trials": 64,
            "feedback_clarity": "clear",
            "rule_change_warning": False,
            "feedback_delay_ms": 300,
            "correct_needed": 9,  # Smoother progression
        },
        5: {
            "trials": 64,
            "feedback_clarity": "subtle",  # Less obvious feedback
            "rule_change_warning": False,
            "feedback_delay_ms": 400,
            "correct_needed": 8,  # Moderate challenge
        },
        6: {
            "trials": 64,
            "feedback_clarity": "subtle",
            "rule_change_warning": False,
            "feedback_delay_ms": 500,
            "correct_needed": 8,  # Moderate challenge
        },
        7: {
            "trials": 80,
            "feedback_clarity": "ambiguous",  # Minimal feedback
            "rule_change_warning": False,
            "feedback_delay_ms": 600,
            "correct_needed": 7,  # High challenge
        },
        8: {
            "trials": 80,
            "feedback_clarity": "ambiguous",
            "rule_change_warning": False,
            "feedback_delay_ms": 700,
            "correct_needed": 7,  # High challenge
        },
        9: {
            "trials": 96,
            "feedback_clarity": "minimal",  # Very subtle feedback
            "rule_change_warning": False,
            "feedback_delay_ms": 800,
            "correct_needed": 6,  # Very fast rule changes
        },
        10: {
            "trials": 96,
            "feedback_clarity": "minimal",
            "rule_change_warning": False,
            "feedback_delay_ms": 1000,
            "correct_needed": 5,  # Maximum challenge - very rapid switching
        },
    }
    
    def __init__(self):
        """Initialize WCST task service"""
        pass
    
    def generate_session(self, difficulty: int = 1) -> Dict[str, Any]:
        """
        Generate a WCST session with trials and target cards
        
        Args:
            difficulty: 1-10, affects number of trials, feedback clarity, rule change speed
            
        Returns:
            Dict with session configuration
        """
        if difficulty not in range(1, 11):
            difficulty = 1
        
        config = self.DIFFICULTY_CONFIG[difficulty]
        
        # Generate 4 target cards (one of each color/shape/number)
        target_cards = self._generate_target_cards()
        
        # Generate trial cards (random combinations)
        trial_cards = self._generate_trial_cards(config["trials"])
        
        # Initial rule (random)
        initial_rule = random.choice(self.RULES)
        
        session_data = {
            "difficulty": difficulty,
            "config": config,
            "target_cards": target_cards,
            "trial_cards": trial_cards,
            "initial_rule": initial_rule,  # For backend tracking only, not shown to user
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        return session_data
    
    def _generate_target_cards(self) -> List[Dict[str, Any]]:
        """
        Generate 4 target cards representing each sorting pile
        
        Returns:
            List of 4 cards with distinct color, shape, and number
        """
        # Classic WCST uses these 4 specific target cards
        target_cards = [
            {"color": "red", "shape": "triangle", "number": 1},
            {"color": "green", "shape": "star", "number": 2},
            {"color": "yellow", "shape": "cross", "number": 3},
            {"color": "blue", "shape": "circle", "number": 4},
        ]
        
        return target_cards
    
    def _generate_trial_cards(self, num_trials: int) -> List[Dict[str, Any]]:
        """
        Generate random trial cards for user to sort
        
        Args:
            num_trials: Number of cards to generate
            
        Returns:
            List of random cards
        """
        trial_cards = []
        
        for _ in range(num_trials):
            card = {
                "color": random.choice(self.COLORS),
                "shape": random.choice(self.SHAPES),
                "number": random.choice(self.NUMBERS),
            }
            trial_cards.append(card)
        
        return trial_cards
    
    def score_session(
        self,
        session_data: Dict[str, Any],
        responses: List[Dict[str, Any]],
        baseline_flexibility: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Score WCST session based on user responses
        
        Args:
            session_data: Original session configuration
            responses: List of user responses with trial_index, selected_pile, response_time
            baseline_flexibility: User's baseline flexibility score (optional)
            
        Returns:
            Dict with scores and performance metrics
        """
        difficulty = session_data["difficulty"]
        config = session_data["config"]
        target_cards = session_data["target_cards"]
        trial_cards = session_data["trial_cards"]
        initial_rule = session_data["initial_rule"]
        
        # Initialize tracking variables
        current_rule = initial_rule
        correct_in_row = 0
        categories_achieved = 0
        trials_to_first_category = None
        perseverative_errors = 0
        non_perseverative_errors = 0
        total_errors = 0
        rule_changes = []
        previous_rule = None
        correct_responses = 0
        
        # Process each response
        for i, response in enumerate(responses):
            trial_index = response["trial_index"]
            selected_pile = response["selected_pile"]  # 0-3
            response_time = response.get("response_time", 0)
            
            if trial_index >= len(trial_cards):
                continue
            
            trial_card = trial_cards[trial_index]
            target_card = target_cards[selected_pile]
            
            # Check if response is correct according to current rule
            is_correct = self._check_match(trial_card, target_card, current_rule)
            
            if is_correct:
                correct_responses += 1
                correct_in_row += 1
                
                # Check if we've achieved a category (10 correct in a row)
                if correct_in_row >= config["correct_needed"]:
                    categories_achieved += 1
                    
                    # Record trials to first category
                    if trials_to_first_category is None:
                        trials_to_first_category = trial_index + 1
                    
                    # Change rule after category achieved
                    previous_rule = current_rule
                    current_rule = self._get_next_rule(current_rule)
                    rule_changes.append({
                        "trial": trial_index + 1,
                        "from_rule": previous_rule,
                        "to_rule": current_rule,
                    })
                    correct_in_row = 0
            else:
                # Error occurred
                total_errors += 1
                correct_in_row = 0
                
                # Check if it's a perseverative error (matching old rule)
                if previous_rule and self._check_match(trial_card, target_card, previous_rule):
                    perseverative_errors += 1
                else:
                    non_perseverative_errors += 1
        
        # Calculate metrics
        total_trials = len(responses)
        accuracy = (correct_responses / total_trials * 100) if total_trials > 0 else 0
        
        # Perseverative error rate (key WCST metric)
        perseverative_error_rate = (perseverative_errors / total_trials * 100) if total_trials > 0 else 0
        
        # Average response time
        total_time = sum(r.get("response_time", 0) for r in responses)
        avg_response_time = total_time / total_trials if total_trials > 0 else 0
        
        # Calculate percentile score (higher categories = better)
        # MS patients typically achieve 2-4 categories, healthy controls 4-6
        percentile = self._calculate_percentile(
            categories_achieved,
            perseverative_errors,
            total_trials,
            difficulty,
        )
        
        # Categorize performance
        performance_category = self._categorize_performance(
            categories_achieved,
            perseverative_error_rate,
            accuracy,
            difficulty,
        )
        
        # Generate detailed feedback
        feedback = self._generate_feedback(
            categories_achieved,
            perseverative_errors,
            non_perseverative_errors,
            trials_to_first_category,
            performance_category,
        )
        
        return {
            "score": percentile,
            "accuracy": round(accuracy, 1),
            "total_trials": total_trials,
            "correct_responses": correct_responses,
            "total_errors": total_errors,
            "categories_achieved": categories_achieved,
            "trials_to_first_category": trials_to_first_category,
            "perseverative_errors": perseverative_errors,
            "non_perseverative_errors": non_perseverative_errors,
            "perseverative_error_rate": round(perseverative_error_rate, 1),
            "rule_changes": len(rule_changes),
            "average_response_time": round(avg_response_time),
            "performance_category": performance_category,
            "feedback": feedback,
            "rule_change_details": rule_changes,
        }
    
    def _check_match(self, trial_card: Dict, target_card: Dict, rule: str) -> bool:
        """Check if trial card matches target card according to rule"""
        return trial_card[rule] == target_card[rule]
    
    def _get_next_rule(self, current_rule: str) -> str:
        """Get next rule (cycle through color -> shape -> number -> color...)"""
        rule_index = self.RULES.index(current_rule)
        next_index = (rule_index + 1) % len(self.RULES)
        return self.RULES[next_index]
    
    def _calculate_percentile(
        self,
        categories: int,
        perseverative_errors: int,
        total_trials: int,
        difficulty: int,
    ) -> float:
        """
        Calculate percentile score based on WCST performance
        
        MS norms (approximate):
        - 0-1 categories: <20th percentile
        - 2 categories: 20-40th percentile
        - 3 categories: 40-60th percentile
        - 4 categories: 60-75th percentile
        - 5+ categories: 75-95th percentile
        """
        # Base score on categories achieved
        if categories == 0:
            base_score = 10
        elif categories == 1:
            base_score = 25
        elif categories == 2:
            base_score = 40
        elif categories == 3:
            base_score = 55
        elif categories == 4:
            base_score = 70
        elif categories == 5:
            base_score = 82
        else:  # 6+
            base_score = 92
        
        # Adjust for perseverative errors
        if total_trials > 0:
            persev_rate = perseverative_errors / total_trials
            if persev_rate > 0.3:  # High perseveration
                base_score -= 15
            elif persev_rate > 0.2:
                base_score -= 10
            elif persev_rate > 0.1:
                base_score -= 5
        
        # Adjust for difficulty
        difficulty_bonus = (difficulty - 1) * 2  # Up to +18 at level 10
        
        final_score = base_score + difficulty_bonus
        return max(1, min(99, final_score))  # Clamp to 1-99
    
    def _categorize_performance(
        self,
        categories: int,
        persev_rate: float,
        accuracy: float,
        difficulty: int,
    ) -> str:
        """Categorize overall performance"""
        # Excellent: 4+ categories, low perseveration
        if categories >= 4 and persev_rate < 15 and accuracy >= 70:
            return "Excellent"
        
        # Good: 3 categories or good accuracy with some categories
        if categories >= 3 or (categories >= 2 and accuracy >= 65 and persev_rate < 25):
            return "Good"
        
        # Fair: 2 categories or reasonable performance
        if categories >= 2 or (categories >= 1 and accuracy >= 55):
            return "Fair"
        
        # Needs Improvement: 1 category or struggling
        if categories >= 1 or accuracy >= 40:
            return "Needs Improvement"
        
        return "Struggling"
    
    def _generate_feedback(
        self,
        categories: int,
        persev_errors: int,
        non_persev_errors: int,
        trials_to_first: Optional[int],
        performance: str,
    ) -> str:
        """Generate clinical feedback based on performance"""
        feedback_parts = []
        
        # Categories achieved
        if categories >= 5:
            feedback_parts.append("Excellent set-shifting ability! You successfully adapted to multiple rule changes.")
        elif categories >= 3:
            feedback_parts.append("Good cognitive flexibility. You identified and adapted to several rule changes.")
        elif categories >= 2:
            feedback_parts.append("Moderate flexibility. You discovered some rule changes but may benefit from more practice.")
        elif categories == 1:
            feedback_parts.append("You achieved one category. Focus on recognizing when the rule has changed.")
        else:
            feedback_parts.append("Try to identify patterns in the feedback to discover the sorting rule.")
        
        # Perseverative errors
        if persev_errors > non_persev_errors and persev_errors > 5:
            feedback_parts.append(
                "You had several perseverative errors (continuing with an old rule after it changed). "
                "Practice letting go of previous strategies when feedback suggests a change."
            )
        elif persev_errors <= 3:
            feedback_parts.append("You showed good ability to shift away from old rules.")
        
        # Trials to first category
        if trials_to_first and trials_to_first <= 15:
            feedback_parts.append("You quickly identified the initial rule.")
        elif trials_to_first and trials_to_first > 25:
            feedback_parts.append("Take time to analyze the pattern in the feedback to identify the rule faster.")
        
        return " ".join(feedback_parts)

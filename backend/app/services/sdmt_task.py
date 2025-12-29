"""
Symbol Digit Modalities Test (SDMT) Task Service

⭐⭐⭐⭐⭐ GOLD STANDARD for MS cognitive impairment detection

The most widely used and sensitive test for MS cognitive dysfunction.
User matches symbols to digits using a reference key as quickly as possible.

Clinical Validation: Most sensitive measure of MS-related cognitive changes
Reference: Benedict et al., 2017
"""

import random
from typing import List, Dict
from datetime import datetime


class SDMTTask:
    """
    Service for generating and scoring Symbol Digit Modalities Test (SDMT) trials
    """
    
    # Symbol sets (using Unicode characters for visual variety)
    SYMBOL_SETS = {
        'basic': ['★', '●', '■', '▲', '◆', '♦', '♠', '♣', '♥'],
        'geometric': ['◐', '◑', '◒', '◓', '◔', '◕', '◖', '◗', '◘', '◙', '◚', '◛'],
        'shapes': ['◢', '◣', '◤', '◥', '◰', '◱', '◲', '◳', '◴', '◵', '◶', '◷'],
        'arrows': ['←', '→', '↑', '↓', '↖', '↗', '↘', '↙', '⇐', '⇒', '⇑', '⇓'],
    }
    
    # Difficulty configuration
    # Standard SDMT: 9 symbol-digit pairs, 90 seconds
    # MS norms: 40-50 correct = mild impairment, 50-60 = average, 60+ = good
    DIFFICULTY_CONFIG = {
        1: {
            "num_pairs": 6,           # Easier: fewer symbols to remember
            "duration_seconds": 90,
            "symbol_set": "basic",
            "target_responses": 30,   # Lower target
        },
        2: {
            "num_pairs": 7,
            "duration_seconds": 90,
            "symbol_set": "basic",
            "target_responses": 35,
        },
        3: {
            "num_pairs": 8,
            "duration_seconds": 90,
            "symbol_set": "basic",
            "target_responses": 40,
        },
        4: {
            "num_pairs": 9,           # Standard SDMT
            "duration_seconds": 90,
            "symbol_set": "basic",
            "target_responses": 45,
        },
        5: {
            "num_pairs": 9,
            "duration_seconds": 90,
            "symbol_set": "geometric",
            "target_responses": 50,
        },
        6: {
            "num_pairs": 10,          # Increased complexity
            "duration_seconds": 90,
            "symbol_set": "geometric",
            "target_responses": 55,
        },
        7: {
            "num_pairs": 10,
            "duration_seconds": 90,
            "symbol_set": "shapes",
            "target_responses": 60,
        },
        8: {
            "num_pairs": 11,
            "duration_seconds": 90,
            "symbol_set": "shapes",
            "target_responses": 65,
        },
        9: {
            "num_pairs": 12,          # Expert level
            "duration_seconds": 90,
            "symbol_set": "arrows",
            "target_responses": 70,
        },
        10: {
            "num_pairs": 12,
            "duration_seconds": 90,
            "symbol_set": "arrows",
            "target_responses": 75,
        },
    }
    
    @staticmethod
    def generate_trial(difficulty: int) -> Dict:
        """
        Generate SDMT trial with symbol-digit mappings and test sequence
        
        Args:
            difficulty: Level 1-10
            
        Returns:
            Dict with:
            - symbol_digit_mapping: Dict[symbol -> digit]
            - test_sequence: List of symbols to match
            - duration_seconds: Time limit
            - target_responses: Expected correct count
        """
        config = SDMTTask.DIFFICULTY_CONFIG.get(difficulty, SDMTTask.DIFFICULTY_CONFIG[5])
        
        # Select symbol set
        symbol_set_name = config["symbol_set"]
        available_symbols = SDMTTask.SYMBOL_SETS[symbol_set_name]
        
        # Create symbol-digit mapping
        num_pairs = config["num_pairs"]
        selected_symbols = random.sample(available_symbols, num_pairs)
        digits = list(range(1, num_pairs + 1))
        random.shuffle(digits)
        
        symbol_digit_mapping = {
            symbol: digit 
            for symbol, digit in zip(selected_symbols, digits)
        }
        
        # Generate test sequence (random symbols, weighted for balance)
        # Standard SDMT has ~120 items, but we'll generate more for high performers
        test_sequence_length = max(120, config["target_responses"] + 50)
        test_sequence = [
            random.choice(selected_symbols) 
            for _ in range(test_sequence_length)
        ]
        
        return {
            "symbol_digit_mapping": symbol_digit_mapping,
            "test_sequence": test_sequence,
            "duration_seconds": config["duration_seconds"],
            "target_responses": config["target_responses"],
            "difficulty": difficulty
        }
    
    @staticmethod
    def score_response(
        trial: Dict,
        user_responses: List[int],
        response_times: List[float],
        completed_count: int
    ) -> Dict:
        """
        Score SDMT trial
        
        Args:
            trial: Original trial data
            user_responses: List of digits entered by user
            response_times: Reaction time for each response (ms)
            completed_count: Number of items attempted
            
        Returns:
            Dict with scoring metrics
        """
        symbol_digit_mapping = trial["symbol_digit_mapping"]
        test_sequence = trial["test_sequence"]
        
        # Calculate correct responses
        correct_count = 0
        incorrect_count = 0
        
        for i, user_digit in enumerate(user_responses):
            if i >= len(test_sequence):
                break
                
            correct_digit = symbol_digit_mapping[test_sequence[i]]
            if user_digit == correct_digit:
                correct_count += 1
            else:
                incorrect_count += 1
        
        # Calculate metrics
        total_attempted = completed_count
        accuracy = (correct_count / total_attempted * 100) if total_attempted > 0 else 0
        
        # Average response time for correct answers
        correct_times = [
            response_times[i] 
            for i in range(min(len(user_responses), len(response_times)))
            if i < len(test_sequence) and user_responses[i] == symbol_digit_mapping[test_sequence[i]]
        ]
        avg_response_time = sum(correct_times) / len(correct_times) if correct_times else 0
        
        # Processing speed: correct responses per minute
        processing_speed = correct_count * (60 / trial["duration_seconds"])
        
        # Score (SDMT standard: number of correct responses)
        score = correct_count
        
        # Consistency: std dev of response times
        if len(correct_times) > 1:
            mean_time = sum(correct_times) / len(correct_times)
            variance = sum((t - mean_time) ** 2 for t in correct_times) / len(correct_times)
            consistency_sd = variance ** 0.5
            consistency = max(0, 100 - (consistency_sd / mean_time * 100)) if mean_time > 0 else 0
        else:
            consistency = 100
        
        return {
            "score": score,
            "correct_count": correct_count,
            "incorrect_count": incorrect_count,
            "total_attempted": total_attempted,
            "accuracy": round(accuracy, 1),
            "processing_speed": round(processing_speed, 1),
            "avg_response_time": round(avg_response_time, 0),
            "consistency": round(consistency, 1),
        }
    
    @staticmethod
    def determine_difficulty_adjustment(score: int, difficulty: int, target: int) -> tuple[int, str]:
        """
        Determine if difficulty should change based on performance
        
        Args:
            score: Number of correct responses
            difficulty: Current difficulty level
            target: Target number for this level
            
        Returns:
            Tuple of (new_difficulty, reason)
        """
        # SDMT: Increase if exceeding target by 10+, decrease if below target by 10+
        if score >= target + 10 and difficulty < 10:
            return difficulty + 1, f"Excellent! {score} correct responses (target: {target})"
        elif score < target - 10 and difficulty > 1:
            return difficulty - 1, f"Let's adjust. {score} correct responses (target: {target})"
        else:
            return difficulty, f"Good progress! {score} correct responses (target: {target})"

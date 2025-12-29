"""
Digit Span Task Implementation
Backend logic for generating trials and scoring
"""

import random
from typing import List, Dict, Tuple

class DigitSpanTask:
    """
    Digit Span Test - Working Memory Assessment
    
    Based on WAIS-IV Digit Span subtest
    Forward: Repeat digits in same order
    Backward: Repeat digits in reverse order
    """
    
    # Difficulty to sequence length mapping
    DIFFICULTY_CONFIG = {
        1: {'length': 3, 'type': 'forward'},
        2: {'length': 4, 'type': 'forward'},
        3: {'length': 5, 'type': 'forward'},
        4: {'length': 4, 'type': 'backward'},
        5: {'length': 5, 'type': 'backward'},
        6: {'length': 6, 'type': 'backward'},
        7: {'length': 7, 'type': 'backward'},
        8: {'length': 8, 'type': 'mixed'},  # Mix of forward/backward
        9: {'length': 9, 'type': 'mixed'},
        10: {'length': 10, 'type': 'mixed'}
    }
    
    @staticmethod
    def generate_sequence(length: int) -> List[int]:
        """Generate random digit sequence (1-9, no repeats in row)"""
        sequence = []
        last_digit = None
        
        for _ in range(length):
            # Choose digit 1-9, avoid immediate repetition
            choices = [d for d in range(1, 10) if d != last_digit]
            digit = random.choice(choices)
            sequence.append(digit)
            last_digit = digit
        
        return sequence
    
    @staticmethod
    def generate_trial(difficulty: int) -> Dict:
        """
        Generate a single Digit Span trial
        
        Returns:
            dict with:
                - sequence: list of digits
                - span_type: 'forward' or 'backward'
                - length: number of digits
                - difficulty: difficulty level
        """
        config = DigitSpanTask.DIFFICULTY_CONFIG.get(
            difficulty, 
            {'length': 5, 'type': 'forward'}
        )
        
        length = config['length']
        span_type = config['type']
        
        # For mixed mode, randomly choose forward or backward
        if span_type == 'mixed':
            span_type = random.choice(['forward', 'backward'])
        
        sequence = DigitSpanTask.generate_sequence(length)
        
        return {
            'sequence': sequence,
            'span_type': span_type,
            'length': length,
            'difficulty': difficulty
        }
    
    @staticmethod
    def generate_session(difficulty: int, num_trials: int = 8) -> List[Dict]:
        """
        Generate full session of Digit Span trials
        
        Args:
            difficulty: Starting difficulty (1-10)
            num_trials: Number of trials to generate
            
        Returns:
            List of trial configurations
        """
        trials = []
        
        # Generate trials with slight difficulty variation
        for i in range(num_trials):
            # Vary difficulty slightly across trials
            trial_diff = difficulty
            if i > 0 and i % 3 == 0:  # Every 3rd trial, increase difficulty slightly
                trial_diff = min(difficulty + 1, 10)
            
            trial = DigitSpanTask.generate_trial(trial_diff)
            trial['trial_number'] = i + 1
            trials.append(trial)
        
        return trials
    
    @staticmethod
    def score_response(
        sequence: List[int], 
        user_response: List[int], 
        span_type: str
    ) -> Dict:
        """
        Score user's response
        
        Args:
            sequence: Original digit sequence
            user_response: User's entered sequence
            span_type: 'forward' or 'backward'
            
        Returns:
            dict with correct, accuracy, expected_response
        """
        # Expected response based on span type
        if span_type == 'backward':
            expected = list(reversed(sequence))
        else:
            expected = sequence
        
        # Check if correct
        correct = user_response == expected
        
        # Calculate partial accuracy (how many digits in correct positions)
        accuracy = 0.0
        if user_response and expected:
            min_len = min(len(user_response), len(expected))
            matches = sum(1 for i in range(min_len) if user_response[i] == expected[i])
            accuracy = (matches / len(expected)) * 100
        
        return {
            'correct': correct,
            'accuracy': accuracy,
            'expected_response': expected,
            'user_response': user_response
        }
    
    @staticmethod
    def calculate_session_metrics(trials: List[Dict]) -> Dict:
        """
        Calculate overall session performance metrics
        
        Args:
            trials: List of completed trials with scoring
            
        Returns:
            dict with performance metrics
        """
        if not trials:
            return {
                'score': 0,
                'accuracy': 0,
                'correct_count': 0,
                'total_trials': 0,
                'longest_span': 0,
                'forward_accuracy': 0,
                'backward_accuracy': 0
            }
        
        correct_count = sum(1 for t in trials if t.get('correct', False))
        total_trials = len(trials)
        
        # Overall accuracy
        avg_accuracy = sum(t.get('accuracy', 0) for t in trials) / total_trials
        
        # Score: combination of correct trials and accuracy
        score = (correct_count / total_trials * 70) + (avg_accuracy * 0.3)
        
        # Longest span achieved correctly
        correct_trials = [t for t in trials if t.get('correct', False)]
        longest_span = max([t['length'] for t in correct_trials], default=0)
        
        # Separate forward/backward performance
        forward_trials = [t for t in trials if t.get('span_type') == 'forward']
        backward_trials = [t for t in trials if t.get('span_type') == 'backward']
        
        forward_acc = (
            sum(t.get('accuracy', 0) for t in forward_trials) / len(forward_trials)
            if forward_trials else 0
        )
        backward_acc = (
            sum(t.get('accuracy', 0) for t in backward_trials) / len(backward_trials)
            if backward_trials else 0
        )
        
        return {
            'score': round(score, 1),
            'accuracy': round(avg_accuracy, 1),
            'correct_count': correct_count,
            'total_trials': total_trials,
            'longest_span': longest_span,
            'forward_accuracy': round(forward_acc, 1),
            'backward_accuracy': round(backward_acc, 1),
            'consistency': round((correct_count / total_trials) * 100, 1)
        }
    
    @staticmethod
    def calculate_average_reaction_time(trials: List[Dict]) -> float:
        """Calculate average reaction time from trial data"""
        reaction_times = [
            t.get('reaction_time', 0) 
            for t in trials 
            if t.get('reaction_time', 0) > 0
        ]
        
        if not reaction_times:
            return 0.0
        
        return sum(reaction_times) / len(reaction_times)

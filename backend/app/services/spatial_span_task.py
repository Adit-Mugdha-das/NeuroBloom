"""
Spatial Span Task (Corsi Block Test)
Visual-spatial working memory assessment
"""

import random
from typing import List, Dict

class SpatialSpanTask:
    """
    Corsi Block Test - Spatial Working Memory
    
    Based on WMS-IV Spatial Span subtest
    Shows sequence of blocks lighting up in grid
    User must repeat in same order (forward) or reverse (backward)
    """
    
    # Difficulty configuration
    DIFFICULTY_CONFIG = {
        1: {'grid_size': 3, 'length': 3, 'type': 'forward'},
        2: {'grid_size': 3, 'length': 4, 'type': 'forward'},
        3: {'grid_size': 3, 'length': 4, 'type': 'forward'},
        4: {'grid_size': 4, 'length': 4, 'type': 'backward'},
        5: {'grid_size': 4, 'length': 5, 'type': 'backward'},
        6: {'grid_size': 4, 'length': 6, 'type': 'backward'},
        7: {'grid_size': 5, 'length': 6, 'type': 'backward'},
        8: {'grid_size': 5, 'length': 7, 'type': 'mixed'},
        9: {'grid_size': 5, 'length': 8, 'type': 'mixed'},
        10: {'grid_size': 5, 'length': 9, 'type': 'mixed'}
    }
    
    @staticmethod
    def generate_sequence(grid_size: int, length: int) -> List[int]:
        """
        Generate random sequence of block positions (0 to grid_size²-1)
        No immediate repeats
        """
        total_blocks = grid_size * grid_size
        sequence = []
        last_position = None
        
        for _ in range(length):
            # Choose position, avoid immediate repetition
            choices = [p for p in range(total_blocks) if p != last_position]
            position = random.choice(choices)
            sequence.append(position)
            last_position = position
        
        return sequence
    
    @staticmethod
    def generate_trial(difficulty: int) -> Dict:
        """Generate a single Spatial Span trial"""
        
        config = SpatialSpanTask.DIFFICULTY_CONFIG.get(difficulty, 
                                                        SpatialSpanTask.DIFFICULTY_CONFIG[5])
        
        grid_size = config['grid_size']
        length = config['length']
        span_type = config['type']
        
        # For mixed type, randomly choose forward or backward
        if span_type == 'mixed':
            span_type = random.choice(['forward', 'backward'])
        
        sequence = SpatialSpanTask.generate_sequence(grid_size, length)
        
        return {
            'sequence': sequence,
            'grid_size': grid_size,
            'length': length,
            'span_type': span_type
        }
    
    @staticmethod
    def generate_session(difficulty: int = 5, num_trials: int = 8) -> List[Dict]:
        """Generate complete session with multiple trials"""
        trials = []
        for _ in range(num_trials):
            trial = SpatialSpanTask.generate_trial(difficulty)
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
        
        Returns:
            correct: bool
            accuracy: float (0-100)
            error_type: str
        """
        expected = sequence if span_type == 'forward' else list(reversed(sequence))
        
        if len(user_response) != len(expected):
            return {
                'correct': False,
                'accuracy': 0.0,
                'error_type': 'length_mismatch',
                'expected': expected
            }
        
        # Count correct positions
        correct_count = sum(1 for u, e in zip(user_response, expected) if u == e)
        accuracy = (correct_count / len(expected)) * 100
        
        is_correct = correct_count == len(expected)
        
        # Determine error type
        error_type = None
        if not is_correct:
            if correct_count == 0:
                error_type = 'complete_reversal'
            elif correct_count < len(expected) / 2:
                error_type = 'order_error'
            else:
                error_type = 'partial_recall'
        
        return {
            'correct': is_correct,
            'accuracy': accuracy,
            'error_type': error_type,
            'expected': expected,
            'correct_positions': correct_count
        }
    
    @staticmethod
    def calculate_session_metrics(trials: List[Dict]) -> Dict:
        """Calculate overall session performance metrics"""
        
        total_trials = len(trials)
        correct_count = sum(1 for t in trials if t.get('correct', False))
        accuracy = (correct_count / total_trials * 100) if total_trials > 0 else 0
        
        # Calculate longest successful span
        longest_span = 0
        for trial in trials:
            if trial.get('correct', False):
                longest_span = max(longest_span, trial.get('length', 0))
        
        # Separate forward vs backward performance
        forward_trials = [t for t in trials if t.get('span_type') == 'forward']
        backward_trials = [t for t in trials if t.get('span_type') == 'backward']
        
        forward_accuracy = 0
        if forward_trials:
            forward_correct = sum(1 for t in forward_trials if t.get('correct', False))
            forward_accuracy = (forward_correct / len(forward_trials) * 100)
        
        backward_accuracy = 0
        if backward_trials:
            backward_correct = sum(1 for t in backward_trials if t.get('correct', False))
            backward_accuracy = (backward_correct / len(backward_trials) * 100)
        
        # Consistency: standard deviation of accuracy across trials
        accuracies = [t.get('accuracy', 0) for t in trials]
        avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0
        variance = sum((a - avg_accuracy) ** 2 for a in accuracies) / len(accuracies) if accuracies else 0
        std_dev = variance ** 0.5
        consistency = max(0, 100 - std_dev)  # Higher is more consistent
        
        # Score calculation (0-100)
        score = (accuracy * 0.6) + (longest_span * 5) + (consistency * 0.4)
        score = min(100, score)
        
        return {
            'score': round(score, 1),
            'accuracy': round(accuracy, 1),
            'correct_count': correct_count,
            'total_trials': total_trials,
            'longest_span': longest_span,
            'forward_accuracy': round(forward_accuracy, 1),
            'backward_accuracy': round(backward_accuracy, 1),
            'consistency': round(consistency, 1)
        }
    
    @staticmethod
    def calculate_average_reaction_time(trials: List[Dict]) -> float:
        """Calculate average reaction time across trials"""
        reaction_times = [t.get('reaction_time', 0) for t in trials if t.get('reaction_time')]
        return sum(reaction_times) / len(reaction_times) if reaction_times else 0

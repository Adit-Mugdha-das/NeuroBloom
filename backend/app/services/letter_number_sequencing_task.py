"""
Letter-Number Sequencing Task Service

WAIS-IV subtest measuring executive working memory and mental manipulation.
User hears/sees mixed letters and numbers, must recall numbers in ascending order
followed by letters in alphabetical order.

Example: "B-3-A-1" → "1-3-A-B"

Clinical Validation: WAIS-IV component, sensitive to MS cognitive dysfunction
Reference: Parmenter et al., 2007
"""

import random
from typing import List, Dict, Tuple


class LetterNumberSequencingTask:
    """
    Service for generating and scoring Letter-Number Sequencing trials
    """
    
    # Difficulty configuration based on sequence length
    DIFFICULTY_CONFIG = {
        1: {"length": 3, "numbers": 2, "letters": 1},
        2: {"length": 3, "numbers": 2, "letters": 1},
        3: {"length": 4, "numbers": 2, "letters": 2},
        4: {"length": 5, "numbers": 3, "letters": 2},
        5: {"length": 5, "numbers": 3, "letters": 2},
        6: {"length": 6, "numbers": 3, "letters": 3},
        7: {"length": 7, "numbers": 4, "letters": 3},
        8: {"length": 8, "numbers": 4, "letters": 4},
        9: {"length": 8, "numbers": 5, "letters": 3},
        10: {"length": 9, "numbers": 5, "letters": 4}
    }
    
    # Available single digits and letters
    NUMBERS = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
    LETTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'R', 'S', 'T']
    # Excluded I, O, Q to avoid confusion with 1, 0
    
    @staticmethod
    def generate_sequence(difficulty: int) -> Tuple[List[str], List[str], List[str]]:
        """
        Generate a mixed letter-number sequence
        
        Args:
            difficulty: Level 1-10
            
        Returns:
            Tuple of (scrambled_sequence, correct_numbers, correct_letters)
        """
        config = LetterNumberSequencingTask.DIFFICULTY_CONFIG.get(difficulty, {"length": 4, "numbers": 2, "letters": 2})
        
        num_numbers = config["numbers"]
        num_letters = config["letters"]
        
        # Select random numbers and letters without replacement
        selected_numbers = random.sample(LetterNumberSequencingTask.NUMBERS, num_numbers)
        selected_letters = random.sample(LetterNumberSequencingTask.LETTERS, num_letters)
        
        # Combine and shuffle
        sequence = selected_numbers + selected_letters
        random.shuffle(sequence)
        
        # Correct answers: numbers ascending, letters alphabetical
        correct_numbers = sorted(selected_numbers, key=lambda x: int(x))
        correct_letters = sorted(selected_letters)
        
        return sequence, correct_numbers, correct_letters
    
    @staticmethod
    def generate_trial(difficulty: int) -> Dict:
        """
        Generate a single trial
        
        Returns:
            {
                "sequence": ["B", "3", "A", "1"],
                "correct_numbers": ["1", "3"],
                "correct_letters": ["A", "B"],
                "difficulty": 5,
                "length": 4
            }
        """
        sequence, correct_numbers, correct_letters = LetterNumberSequencingTask.generate_sequence(difficulty)
        
        return {
            "sequence": sequence,
            "correct_numbers": correct_numbers,
            "correct_letters": correct_letters,
            "difficulty": difficulty,
            "length": len(sequence)
        }
    
    @staticmethod
    def generate_session(difficulty: int, num_trials: int = 8) -> List[Dict]:
        """
        Generate a complete session with multiple trials
        """
        trials = []
        for _ in range(num_trials):
            trial = LetterNumberSequencingTask.generate_trial(difficulty)
            trials.append(trial)
        
        return trials
    
    @staticmethod
    def score_response(
        correct_numbers: List[str],
        correct_letters: List[str],
        user_numbers: List[str],
        user_letters: List[str]
    ) -> Dict:
        """
        Score a user's response
        
        Returns:
            {
                "correct": bool,
                "numbers_correct": bool,
                "letters_correct": bool,
                "numbers_accuracy": float,
                "letters_accuracy": float,
                "error_type": str
            }
        """
        # Check exact matches
        numbers_correct = user_numbers == correct_numbers
        letters_correct = user_letters == correct_letters
        
        # Calculate partial accuracy
        numbers_accuracy = 0.0
        if len(correct_numbers) > 0:
            correct_count = sum(1 for i, num in enumerate(user_numbers) 
                              if i < len(correct_numbers) and num == correct_numbers[i])
            numbers_accuracy = (correct_count / len(correct_numbers)) * 100
        
        letters_accuracy = 0.0
        if len(correct_letters) > 0:
            correct_count = sum(1 for i, letter in enumerate(user_letters) 
                              if i < len(correct_letters) and letter == correct_letters[i])
            letters_accuracy = (correct_count / len(correct_letters)) * 100
        
        # Determine error type
        error_type = None
        if not (numbers_correct and letters_correct):
            if not numbers_correct and not letters_correct:
                error_type = "both_incorrect"
            elif not numbers_correct:
                error_type = "numbers_incorrect"
            else:
                error_type = "letters_incorrect"
        
        return {
            "correct": numbers_correct and letters_correct,
            "numbers_correct": numbers_correct,
            "letters_correct": letters_correct,
            "numbers_accuracy": numbers_accuracy,
            "letters_accuracy": letters_accuracy,
            "error_type": error_type
        }
    
    @staticmethod
    def calculate_session_metrics(scored_trials: List[Dict]) -> Dict:
        """
        Calculate overall session performance metrics
        
        Args:
            scored_trials: List of trials with scoring results
            
        Returns:
            {
                "score": int (0-100),
                "accuracy": float,
                "correct_count": int,
                "total_trials": int,
                "numbers_accuracy": float,
                "letters_accuracy": float,
                "longest_sequence": int,
                "consistency": float
            }
        """
        total_trials = len(scored_trials)
        if total_trials == 0:
            return {
                "score": 0,
                "accuracy": 0.0,
                "correct_count": 0,
                "total_trials": 0,
                "numbers_accuracy": 0.0,
                "letters_accuracy": 0.0,
                "longest_sequence": 0,
                "consistency": 0.0
            }
        
        # Count correct trials
        correct_count = sum(1 for trial in scored_trials if trial.get('correct', False))
        
        # Calculate accuracy
        accuracy = (correct_count / total_trials) * 100
        
        # Average numbers and letters accuracy
        avg_numbers_accuracy = sum(trial.get('numbers_accuracy', 0) for trial in scored_trials) / total_trials
        avg_letters_accuracy = sum(trial.get('letters_accuracy', 0) for trial in scored_trials) / total_trials
        
        # Find longest correctly recalled sequence
        longest_sequence = 0
        for trial in scored_trials:
            if trial.get('correct', False):
                sequence_length = trial.get('length', 0)
                if sequence_length > longest_sequence:
                    longest_sequence = sequence_length
        
        # Calculate consistency (variance in performance)
        if total_trials > 1:
            accuracies = [100 if trial.get('correct', False) else 0 for trial in scored_trials]
            mean_acc = sum(accuracies) / len(accuracies)
            variance = sum((acc - mean_acc) ** 2 for acc in accuracies) / len(accuracies)
            std_dev = variance ** 0.5
            consistency = max(0, 100 - std_dev)  # Higher is more consistent
        else:
            consistency = 100.0
        
        # Calculate score (0-100)
        score = int(accuracy)
        
        return {
            "score": score,
            "accuracy": accuracy,
            "correct_count": correct_count,
            "total_trials": total_trials,
            "numbers_accuracy": avg_numbers_accuracy,
            "letters_accuracy": avg_letters_accuracy,
            "longest_sequence": longest_sequence,
            "consistency": consistency
        }
    
    @staticmethod
    def calculate_average_reaction_time(scored_trials: List[Dict]) -> int:
        """
        Calculate average reaction time across trials
        
        Returns:
            Average reaction time in milliseconds
        """
        reaction_times = [trial.get('reaction_time', 0) for trial in scored_trials if trial.get('reaction_time')]
        
        if not reaction_times:
            return 0
        
        return int(sum(reaction_times) / len(reaction_times))

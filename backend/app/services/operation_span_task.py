"""
Operation Span (OSPAN) Task Service

Research standard for measuring complex working memory capacity.
User must solve math problems while remembering letters for later recall.

Example: "Is 2+3=5? Remember F" → "Is 4+2=7? Remember Q" → Recall: F, Q

Clinical Validation: Research standard, predicts real-world functioning
Reference: Unsworth et al., 2005
"""

import random
from typing import List, Dict, Tuple


class OperationSpanTask:
    """
    Service for generating and scoring Operation Span (OSPAN) trials
    """
    
    # Difficulty configuration — one axis changes per level:
    # Levels 1-3:  simple addition, set size grows 2→3→4, generous time
    # Levels 4-6:  subtraction introduced, set size 4→5→5, time tightens
    # Levels 7-9:  multi-operation, set size 5→6→7, time tightens further
    # Level 10:    multi-operation, set size 8, tightest time — expert ceiling
    #
    # Time limits are set per math type so each type starts with breathing room
    # then gradually tightens: addition 6→5s, subtraction 7→5.5s, multi 8→6s
    DIFFICULTY_CONFIG = {
        1:  {"set_size": 2, "operation_type": "simple_addition",  "time_limit": 6000},  # 2 letters, easy addition, 6s
        2:  {"set_size": 3, "operation_type": "simple_addition",  "time_limit": 5500},  # +1 letter, time tightens
        3:  {"set_size": 4, "operation_type": "simple_addition",  "time_limit": 5000},  # +1 letter, time tightens
        4:  {"set_size": 4, "operation_type": "subtraction",      "time_limit": 7000},  # math type switch only, time resets
        5:  {"set_size": 5, "operation_type": "subtraction",      "time_limit": 6500},  # +1 letter, time tightens
        6:  {"set_size": 5, "operation_type": "subtraction",      "time_limit": 5500},  # same letters, time tightens
        7:  {"set_size": 5, "operation_type": "multi_operation",  "time_limit": 8000},  # math type switch only, time resets
        8:  {"set_size": 6, "operation_type": "multi_operation",  "time_limit": 7000},  # +1 letter, time tightens
        9:  {"set_size": 7, "operation_type": "multi_operation",  "time_limit": 6500},  # +1 letter, time tightens
        10: {"set_size": 8, "operation_type": "multi_operation",  "time_limit": 6000},  # +1 letter, tightest — expert ceiling
    }
    
    # Available letters (excluding vowels to reduce acronym formation)
    LETTERS = ['B', 'C', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'R', 'S', 'T']
    
    @staticmethod
    def generate_math_problem(operation_type: str) -> Tuple[str, int, bool]:
        """
        Generate a math problem based on operation type
        
        Returns:
            Tuple of (equation_text, correct_answer, is_correct)
        """
        if operation_type == "simple_addition":
            # Simple addition: (1-9) + (1-9)
            a = random.randint(1, 9)
            b = random.randint(1, 9)
            correct_answer = a + b
            
            # 50% chance of wrong answer (off by 1-3)
            is_correct = random.choice([True, False])
            shown_answer = correct_answer if is_correct else correct_answer + random.choice([-2, -1, 1, 2])
            
            equation = f"{a} + {b} = {shown_answer}"
            
        elif operation_type == "subtraction":
            # Subtraction: (10-20) - (1-9), ensuring positive result
            a = random.randint(10, 20)
            b = random.randint(1, min(9, a - 1))
            correct_answer = a - b
            
            is_correct = random.choice([True, False])
            shown_answer = correct_answer if is_correct else correct_answer + random.choice([-2, -1, 1, 2])
            
            equation = f"{a} - {b} = {shown_answer}"
            
        else:  # multi_operation
            # Mix of operations: (a op1 b) op2 c
            # Larger numbers than addition/subtraction to genuinely increase cognitive load
            a = random.randint(4, 12)
            b = random.randint(2, 8)
            c = random.randint(2, 6)

            op1 = random.choice(['+', '-'])
            op2 = random.choice(['+', '-'])
            
            # Calculate correct answer
            if op1 == '+':
                temp = a + b
            else:
                temp = a - b
            
            if op2 == '+':
                correct_answer = temp + c
            else:
                correct_answer = temp - c
            
            is_correct = random.choice([True, False])
            shown_answer = correct_answer if is_correct else correct_answer + random.choice([-2, -1, 1, 2])
            
            equation = f"({a} {op1} {b}) {op2} {c} = {shown_answer}"
        
        return equation, shown_answer, is_correct
    
    @staticmethod
    def generate_trial(difficulty: int) -> Dict:
        """
        Generate a single OSPAN trial (set of math-letter pairs)
        
        Returns:
            {
                "set_size": 3,
                "operation_type": "simple_addition",
                "time_limit": 4000,
                "items": [
                    {
                        "equation": "3 + 5 = 8",
                        "shown_answer": 8,
                        "correct_answer": 8,
                        "is_correct": True,
                        "letter": "F"
                    },
                    ...
                ],
                "correct_letters": ["F", "K", "M"]
            }
        """
        config = OperationSpanTask.DIFFICULTY_CONFIG.get(difficulty, {"set_size": 3, "operation_type": "simple_addition", "time_limit": 4000})
        
        set_size = config["set_size"]
        operation_type = config["operation_type"]
        time_limit = config["time_limit"]
        
        # Generate set_size math-letter pairs
        items = []
        correct_letters = []
        
        # Select unique letters
        selected_letters = random.sample(OperationSpanTask.LETTERS, set_size)
        
        for letter in selected_letters:
            equation, shown_answer, is_correct = OperationSpanTask.generate_math_problem(operation_type)
            
            # The correct answer is what the equation should equal
            if is_correct:
                correct_answer = shown_answer
            else:
                # Calculate actual correct answer
                if operation_type == "simple_addition":
                    parts = equation.split('=')[0].strip().split('+')
                    correct_answer = int(parts[0]) + int(parts[1])
                elif operation_type == "subtraction":
                    parts = equation.split('=')[0].strip().split('-')
                    correct_answer = int(parts[0]) - int(parts[1])
                else:  # multi_operation - recalculate
                    # Parse the equation
                    eq_part = equation.split('=')[0].strip()
                    # This is complex, just use the generated correct_answer from generation
                    # For simplicity, we'll store it during generation
                    correct_answer = shown_answer  # Will be fixed in generation
            
            items.append({
                "equation": equation,
                "shown_answer": shown_answer,
                "is_correct": is_correct,
                "letter": letter
            })
            
            correct_letters.append(letter)
        
        return {
            "set_size": set_size,
            "operation_type": operation_type,
            "time_limit": time_limit,
            "items": items,
            "correct_letters": correct_letters,
            "difficulty": difficulty
        }
    
    @staticmethod
    def generate_session(difficulty: int, num_trials: int = 6) -> List[Dict]:
        """
        Generate a complete OSPAN session
        Note: Fewer trials than other tasks because each trial is more demanding
        """
        trials = []
        for _ in range(num_trials):
            trial = OperationSpanTask.generate_trial(difficulty)
            trials.append(trial)
        
        return trials
    
    @staticmethod
    def score_response(
        correct_letters: List[str],
        user_letters: List[str],
        math_responses: List[bool],
        math_correct: List[bool]
    ) -> Dict:
        """
        Score both letter recall and math accuracy
        
        Returns:
            {
                "letters_correct": bool,
                "letter_accuracy": float,
                "math_accuracy": float,
                "dual_task_score": float,  # Combined score
                "partial_credit": float
            }
        """
        # Score letter recall
        letters_correct = user_letters == correct_letters
        
        # Calculate letter partial accuracy (position-based)
        letter_accuracy = 0.0
        if len(correct_letters) > 0:
            correct_count = sum(1 for i, letter in enumerate(user_letters) 
                              if i < len(correct_letters) and letter == correct_letters[i])
            letter_accuracy = (correct_count / len(correct_letters)) * 100
        
        # Calculate math accuracy
        math_accuracy = 0.0
        if len(math_correct) > 0:
            correct_count = sum(1 for i, response in enumerate(math_responses)
                              if i < len(math_correct) and response == math_correct[i])
            math_accuracy = (correct_count / len(math_correct)) * 100
        
        # Dual-task score: average of both (must maintain both tasks)
        dual_task_score = (letter_accuracy + math_accuracy) / 2
        
        # Partial credit: more lenient scoring
        partial_credit = (letter_accuracy * 0.6 + math_accuracy * 0.4)
        
        return {
            "letters_correct": letters_correct,
            "letter_accuracy": letter_accuracy,
            "math_accuracy": math_accuracy,
            "dual_task_score": dual_task_score,
            "partial_credit": partial_credit
        }
    
    @staticmethod
    def calculate_session_metrics(scored_trials: List[Dict]) -> Dict:
        """
        Calculate overall session performance metrics
        
        Returns:
            {
                "score": int (0-100),
                "accuracy": float,
                "letter_recall_accuracy": float,
                "math_accuracy": float,
                "dual_task_performance": float,
                "correct_count": int,
                "total_trials": int,
                "consistency": float
            }
        """
        total_trials = len(scored_trials)
        if total_trials == 0:
            return {
                "score": 0,
                "accuracy": 0.0,
                "letter_recall_accuracy": 0.0,
                "math_accuracy": 0.0,
                "dual_task_performance": 0.0,
                "correct_count": 0,
                "total_trials": 0,
                "consistency": 0.0
            }
        
        # Count perfect trials (both letters and math correct)
        correct_count = sum(1 for trial in scored_trials if trial.get('letters_correct', False) and trial.get('math_accuracy', 0) == 100)
        
        # Average accuracies
        avg_letter_accuracy = sum(trial.get('letter_accuracy', 0) for trial in scored_trials) / total_trials
        avg_math_accuracy = sum(trial.get('math_accuracy', 0) for trial in scored_trials) / total_trials
        avg_dual_task = sum(trial.get('dual_task_score', 0) for trial in scored_trials) / total_trials
        
        # Overall accuracy (based on dual-task performance)
        accuracy = avg_dual_task
        
        # Calculate consistency
        if total_trials > 1:
            dual_task_scores = [trial.get('dual_task_score', 0) for trial in scored_trials]
            mean_score = sum(dual_task_scores) / len(dual_task_scores)
            variance = sum((score - mean_score) ** 2 for score in dual_task_scores) / len(dual_task_scores)
            std_dev = variance ** 0.5
            consistency = max(0, 100 - std_dev)
        else:
            consistency = 100.0
        
        # Score (0-100)
        score = int(accuracy)
        
        return {
            "score": score,
            "accuracy": accuracy,
            "letter_recall_accuracy": avg_letter_accuracy,
            "math_accuracy": avg_math_accuracy,
            "dual_task_performance": avg_dual_task,
            "correct_count": correct_count,
            "total_trials": total_trials,
            "consistency": consistency
        }
    
    @staticmethod
    def calculate_average_reaction_time(scored_trials: List[Dict]) -> int:
        """
        Calculate average reaction time across trials
        """
        reaction_times = [trial.get('reaction_time', 0) for trial in scored_trials if trial.get('reaction_time')]
        
        if not reaction_times:
            return 0
        
        return int(sum(reaction_times) / len(reaction_times))

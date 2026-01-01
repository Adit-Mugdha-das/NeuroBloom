"""
Plus-Minus Task Service

Clinical validation: Switching cost paradigm measuring cognitive flexibility
Description: Add 3 to numbers, subtract 3, then alternate between operations

MS Research Evidence:
- Pure switching cost measure
- Minimal working memory load
- Reference: Jersild, 1927; Miyake et al., 2000

Three blocks:
A. Add 3 to all numbers (12 trials)
B. Subtract 3 to all numbers (12 trials)
C. Alternate +3/-3 on each trial (12 trials)

Switching Cost = Block C RT - Average(Block A RT, Block B RT)
"""

import random
from typing import Dict, Any, List, Tuple
from datetime import datetime


class PlusMinusTask:
    """
    Plus-Minus Task implementation
    
    Three blocks:
    - Block A: Add 3 (single operation, baseline speed)
    - Block B: Subtract 3 (single operation, baseline speed)
    - Block C: Alternate +3/-3 (switching cost measured)
    
    Difficulty affects:
    - Number range (single digit → three digits)
    - Cue clarity and duration
    - Time pressure
    """
    
    # Difficulty configuration
    DIFFICULTY_CONFIG = {
        1: {
            "block_a_trials": 12,
            "block_b_trials": 12,
            "block_c_trials": 12,
            "number_range": (1, 9),  # Single digit
            "cue_duration_ms": 2000,  # Clear cues shown for 2 seconds
            "cue_clarity": "clear",  # "+3" or "-3" shown prominently
            "allow_negative": False,  # Numbers chosen to avoid negative results
        },
        2: {
            "block_a_trials": 12,
            "block_b_trials": 12,
            "block_c_trials": 12,
            "number_range": (2, 9),
            "cue_duration_ms": 1800,
            "cue_clarity": "clear",
            "allow_negative": False,
        },
        3: {
            "block_a_trials": 12,
            "block_b_trials": 12,
            "block_c_trials": 12,
            "number_range": (3, 9),
            "cue_duration_ms": 1500,
            "cue_clarity": "clear",
            "allow_negative": False,
        },
        4: {
            "block_a_trials": 15,
            "block_b_trials": 15,
            "block_c_trials": 15,
            "number_range": (10, 99),  # Two digit numbers
            "cue_duration_ms": 1200,
            "cue_clarity": "subtle",  # Smaller cue
            "allow_negative": False,
        },
        5: {
            "block_a_trials": 15,
            "block_b_trials": 15,
            "block_c_trials": 15,
            "number_range": (10, 99),
            "cue_duration_ms": 1000,
            "cue_clarity": "subtle",
            "allow_negative": True,  # Can result in negative numbers
        },
        6: {
            "block_a_trials": 15,
            "block_b_trials": 15,
            "block_c_trials": 15,
            "number_range": (20, 99),
            "cue_duration_ms": 800,
            "cue_clarity": "subtle",
            "allow_negative": True,
        },
        7: {
            "block_a_trials": 18,
            "block_b_trials": 18,
            "block_c_trials": 18,
            "number_range": (100, 999),  # Three digit numbers
            "cue_duration_ms": 600,
            "cue_clarity": "minimal",  # Very small cue
            "allow_negative": True,
        },
        8: {
            "block_a_trials": 18,
            "block_b_trials": 18,
            "block_c_trials": 18,
            "number_range": (100, 999),
            "cue_duration_ms": 500,
            "cue_clarity": "minimal",
            "allow_negative": True,
        },
        9: {
            "block_a_trials": 20,
            "block_b_trials": 20,
            "block_c_trials": 20,
            "number_range": (100, 999),
            "cue_duration_ms": 400,
            "cue_clarity": "minimal",
            "allow_negative": True,
        },
        10: {
            "block_a_trials": 20,
            "block_b_trials": 20,
            "block_c_trials": 20,
            "number_range": (100, 999),
            "cue_duration_ms": 300,
            "cue_clarity": "minimal",
            "allow_negative": True,
        },
    }
    
    @classmethod
    def generate_session(cls, difficulty: int = 1) -> Dict[str, Any]:
        """
        Generate a complete Plus-Minus session with three blocks
        
        Args:
            difficulty: Level 1-10
            
        Returns:
            Session configuration with all three blocks
        """
        if difficulty not in cls.DIFFICULTY_CONFIG:
            difficulty = 1
            
        config = cls.DIFFICULTY_CONFIG[difficulty]
        
        # Generate trials for each block
        block_a_trials = cls._generate_block_trials(
            config["block_a_trials"],
            operation="add",
            number_range=config["number_range"],
            allow_negative=config["allow_negative"]
        )
        
        block_b_trials = cls._generate_block_trials(
            config["block_b_trials"],
            operation="subtract",
            number_range=config["number_range"],
            allow_negative=config["allow_negative"]
        )
        
        block_c_trials = cls._generate_alternating_trials(
            config["block_c_trials"],
            number_range=config["number_range"],
            allow_negative=config["allow_negative"]
        )
        
        session_id = f"plus_minus_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
        
        return {
            "session_id": session_id,
            "task_type": "plus_minus",
            "difficulty": difficulty,
            "config": {
                "cue_duration_ms": config["cue_duration_ms"],
                "cue_clarity": config["cue_clarity"],
                "number_range": config["number_range"],
            },
            "blocks": {
                "block_a": {
                    "name": "add_only",
                    "operation": "add",
                    "instruction": "Add 3 to each number",
                    "trials": block_a_trials,
                    "total_trials": len(block_a_trials)
                },
                "block_b": {
                    "name": "subtract_only",
                    "operation": "subtract",
                    "instruction": "Subtract 3 from each number",
                    "trials": block_b_trials,
                    "total_trials": len(block_b_trials)
                },
                "block_c": {
                    "name": "alternating",
                    "operation": "alternating",
                    "instruction": "Follow the cue: +3 or -3",
                    "trials": block_c_trials,
                    "total_trials": len(block_c_trials)
                }
            },
            "total_trials": len(block_a_trials) + len(block_b_trials) + len(block_c_trials),
            "generated_at": datetime.now().isoformat()
        }
    
    @classmethod
    def _generate_block_trials(cls, num_trials: int, operation: str,
                               number_range: Tuple[int, int],
                               allow_negative: bool) -> List[Dict[str, Any]]:
        """Generate trials for Block A or Block B (single operation)"""
        trials = []
        min_num, max_num = number_range
        
        for i in range(num_trials):
            if operation == "add":
                # Any number in range is fine for addition
                number = random.randint(min_num, max_num)
                correct_answer = number + 3
            else:  # subtract
                if not allow_negative:
                    # Ensure result is non-negative
                    number = random.randint(max(min_num, 3), max_num)
                else:
                    number = random.randint(min_num, max_num)
                correct_answer = number - 3
            
            trials.append({
                "trial_number": i + 1,
                "number": number,
                "operation": operation,
                "correct_answer": correct_answer,
                "is_switch": False  # No switching in single-operation blocks
            })
        
        return trials
    
    @classmethod
    def _generate_alternating_trials(cls, num_trials: int,
                                     number_range: Tuple[int, int],
                                     allow_negative: bool) -> List[Dict[str, Any]]:
        """Generate trials for Block C (alternating operations)"""
        trials = []
        min_num, max_num = number_range
        
        # Start with random operation
        current_operation = random.choice(["add", "subtract"])
        
        for i in range(num_trials):
            # Generate appropriate number based on operation
            if current_operation == "add":
                number = random.randint(min_num, max_num)
                correct_answer = number + 3
            else:  # subtract
                if not allow_negative:
                    number = random.randint(max(min_num, 3), max_num)
                else:
                    number = random.randint(min_num, max_num)
                correct_answer = number - 3
            
            trials.append({
                "trial_number": i + 1,
                "number": number,
                "operation": current_operation,
                "correct_answer": correct_answer,
                "is_switch": i > 0  # Every trial after first is a switch
            })
            
            # Alternate operation for next trial
            current_operation = "subtract" if current_operation == "add" else "add"
        
        return trials
    
    @classmethod
    def score_session(cls, session_data: Dict[str, Any],
                     user_responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Score a completed Plus-Minus session
        
        Args:
            session_data: Original session configuration
            user_responses: List of user responses with timing
            
        Returns:
            Detailed scoring including switching cost
        """
        difficulty = session_data.get("difficulty", 1)
        blocks = session_data.get("blocks", {})
        
        # Initialize scoring
        results = {
            "difficulty": difficulty,
            "total_trials": 0,
            "correct_trials": 0,
            "accuracy": 0.0,
            "mean_rt": 0.0,
            "blocks": {},
            "switching_cost": 0.0,
            "switching_cost_accuracy": 0.0,
            "score": 0
        }
        
        # Score each block separately
        response_idx = 0
        
        for block_name in ["block_a", "block_b", "block_c"]:
            if block_name not in blocks:
                continue
            
            block = blocks[block_name]
            block_trials = block["trials"]
            block_results = {
                "total": len(block_trials),
                "correct": 0,
                "accuracy": 0.0,
                "mean_rt": 0.0,
                "rts": []
            }
            
            for trial in block_trials:
                if response_idx >= len(user_responses):
                    break
                
                response = user_responses[response_idx]
                response_idx += 1
                
                is_correct = response.get("user_answer") == trial["correct_answer"]
                rt = response.get("reaction_time_ms", 0)
                
                if is_correct:
                    block_results["correct"] += 1
                    results["correct_trials"] += 1
                
                if rt > 0:
                    block_results["rts"].append(rt)
                
                results["total_trials"] += 1
            
            # Calculate block metrics
            if block_results["total"] > 0:
                block_results["accuracy"] = block_results["correct"] / block_results["total"]
            
            if block_results["rts"]:
                block_results["mean_rt"] = sum(block_results["rts"]) / len(block_results["rts"])
            
            results["blocks"][block_name] = block_results
        
        # Calculate switching cost (RT-based)
        if "block_a" in results["blocks"] and "block_b" in results["blocks"] and "block_c" in results["blocks"]:
            block_a_rt = results["blocks"]["block_a"]["mean_rt"]
            block_b_rt = results["blocks"]["block_b"]["mean_rt"]
            block_c_rt = results["blocks"]["block_c"]["mean_rt"]
            
            if block_a_rt > 0 and block_b_rt > 0 and block_c_rt > 0:
                baseline_rt = (block_a_rt + block_b_rt) / 2
                results["switching_cost"] = block_c_rt - baseline_rt
            
            # Calculate switching cost in accuracy
            block_a_acc = results["blocks"]["block_a"]["accuracy"]
            block_b_acc = results["blocks"]["block_b"]["accuracy"]
            block_c_acc = results["blocks"]["block_c"]["accuracy"]
            
            baseline_acc = (block_a_acc + block_b_acc) / 2
            results["switching_cost_accuracy"] = baseline_acc - block_c_acc  # Positive = worse in switching
        
        # Overall accuracy
        if results["total_trials"] > 0:
            results["accuracy"] = results["correct_trials"] / results["total_trials"]
        
        # Calculate overall mean RT
        all_rts = []
        for block_name, block_result in results["blocks"].items():
            all_rts.extend(block_result.get("rts", []))
        if all_rts:
            results["mean_rt"] = sum(all_rts) / len(all_rts)
        
        # Calculate final score (0-100)
        # Weight: 50% accuracy + 30% speed + 20% switching performance
        accuracy_score = results["accuracy"] * 50
        
        # Speed score (faster is better)
        expected_rt = 2000  # Expected mean RT in ms
        if results["mean_rt"] > 0:
            speed_score = max(0, min(30, 30 * (expected_rt / results["mean_rt"])))
        else:
            speed_score = 0
        
        # Switching performance (lower cost is better)
        # Normalize: 0ms cost = 20 points, 500ms cost = 0 points
        if results["switching_cost"] >= 0:
            switching_score = max(0, 20 - (results["switching_cost"] / 25))
        else:
            switching_score = 20  # Bonus if somehow faster in switching
        
        results["score"] = int(accuracy_score + speed_score + switching_score)
        
        return results


# Singleton instance
plus_minus_task_service = PlusMinusTask()

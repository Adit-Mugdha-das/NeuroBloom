"""
Stockings of Cambridge (SOC) Task Service

Clinical validation: CANTAB battery, Tower of London variant
Description: Move colored balls between stockings to match target configuration

MS Research Evidence:
- Equivalent to TOL but different stimulus presentation
- Reduces practice effects from TOL repetition
- Reference: Owen et al., 1990; CANTAB battery

Three stockings with capacity constraints:
- Stocking 1: Holds 3 balls
- Stocking 2: Holds 2 balls
- Stocking 3: Holds 1 ball

Same logic as Tower of London, different visual presentation
"""

import random
from typing import Dict, Any, List, Tuple
from datetime import datetime


class StockingsOfCambridgeTask:
    """
    Stockings of Cambridge implementation
    
    Planning task with 3 colored balls in 3 stockings
    User must rearrange balls to match goal state in minimum moves
    
    Identical logic to Tower of London, different visual metaphor
    Use alternately with TOL to prevent practice effects
    
    Difficulty affects:
    - Minimum moves required (2-6+)
    - Planning time allowed
    - Move penalties for exceeding minimum
    - Starting configuration complexity
    """
    
    # Ball colors
    COLORS = ["red", "blue", "green"]
    
    # Stocking capacities (same as TOL peg capacities)
    STOCKING_CAPACITIES = [3, 2, 1]  # Stocking 0 holds 3, 1 holds 2, 2 holds 1
    
    # Difficulty configuration - realistic progression for MS patients
    DIFFICULTY_CONFIG = {
        1: {
            "min_moves": 2,
            "max_moves": 2,
            "problems_count": 3,  # Start with fewer problems
            "planning_time_seconds": 90,  # More time for beginners
            "move_penalty": False,
            "show_minimum_moves": True,
        },
        2: {
            "min_moves": 2,
            "max_moves": 2,
            "problems_count": 4,
            "planning_time_seconds": 75,
            "move_penalty": False,
            "show_minimum_moves": True,
        },
        3: {
            "min_moves": 2,
            "max_moves": 3,  # Mix easier and harder
            "problems_count": 4,
            "planning_time_seconds": 60,
            "move_penalty": False,
            "show_minimum_moves": True,
        },
        4: {
            "min_moves": 3,
            "max_moves": 3,
            "problems_count": 5,
            "planning_time_seconds": 50,
            "move_penalty": False,
            "show_minimum_moves": True,
        },
        5: {
            "min_moves": 3,
            "max_moves": 4,
            "problems_count": 5,
            "planning_time_seconds": 45,
            "move_penalty": True,
            "show_minimum_moves": True,
        },
        6: {
            "min_moves": 4,
            "max_moves": 4,
            "problems_count": 6,
            "planning_time_seconds": 40,
            "move_penalty": True,
            "show_minimum_moves": True,
        },
        7: {
            "min_moves": 4,
            "max_moves": 5,
            "problems_count": 6,
            "planning_time_seconds": 35,
            "move_penalty": True,
            "show_minimum_moves": False,
        },
        8: {
            "min_moves": 5,
            "max_moves": 5,
            "problems_count": 7,
            "planning_time_seconds": 30,
            "move_penalty": True,
            "show_minimum_moves": False,
        },
        9: {
            "min_moves": 5,
            "max_moves": 6,
            "problems_count": 7,
            "planning_time_seconds": 25,
            "move_penalty": True,
            "show_minimum_moves": False,
        },
        10: {
            "min_moves": 6,
            "max_moves": 7,
            "problems_count": 8,
            "planning_time_seconds": 20,
            "move_penalty": True,
            "show_minimum_moves": False,
        },
    }
    
    # Problem library (same as TOL - planning logic is identical)
    PROBLEM_LIBRARY = {
        2: [
            # 2-move problems
            ([[0, 1, 2], [], []], [[1, 2], [0], []]),
            ([[0, 1, 2], [], []], [[2], [0, 1], []]),
            ([[0, 1], [2], []], [[1], [0], [2]]),
            ([[0, 1], [2], []], [[0, 2], [1], []]),
            ([[0], [1, 2], []], [[1, 0], [2], []]),
            ([[0], [1], [2]], [[0, 1], [], [2]]),
        ],
        3: [
            # 3-move problems
            ([[0, 1, 2], [], []], [[0], [2], [1]]),
            ([[0, 1, 2], [], []], [[2, 0], [], [1]]),
            ([[0, 1], [2], []], [[0], [], [1, 2]]),
            ([[0], [1, 2], []], [[2], [1], [0]]),
            ([[0, 1], [2], []], [[2, 1], [], [0]]),
            ([[0, 2], [1], []], [[1], [0], [2]]),
        ],
        4: [
            # 4-move problems
            ([[0, 1, 2], [], []], [[1], [], [2, 0]]),
            ([[0, 1, 2], [], []], [[], [1], [0, 2]]),
            ([[0], [1, 2], []], [[1], [], [0, 2]]),
            ([[0, 1], [2], []], [[], [2, 0], [1]]),
            ([[0, 2], [1], []], [[2], [], [0, 1]]),
            ([[0, 1, 2], [], []], [[0, 2], [], [1]]),
        ],
        5: [
            # 5-move problems
            ([[0, 1, 2], [], []], [[], [], [0, 1, 2]]),
            ([[0, 1, 2], [], []], [[], [2, 1], [0]]),
            ([[0], [1, 2], []], [[], [], [1, 0, 2]]),
            ([[0, 2], [1], []], [[], [0], [2, 1]]),
            ([[0, 1], [2], []], [[], [], [2, 0, 1]]),
        ],
        6: [
            # 6-move problems
            ([[0, 1, 2], [], []], [[], [0], [1, 2]]),
            ([[0, 2], [1], []], [[], [], [1, 2, 0]]),
            ([[0, 1], [2], []], [[2], [], [1, 0]]),
        ],
        7: [
            # 7-move problems (very hard)
            ([[0, 1, 2], [], []], [[2], [1], [0]]),
        ]
    }
    
    @classmethod
    def generate_session(cls, difficulty: int = 1) -> Dict[str, Any]:
        """
        Generate a complete SOC session with multiple problems
        
        Args:
            difficulty: Level 1-10
            
        Returns:
            Session configuration with problems
        """
        if difficulty not in cls.DIFFICULTY_CONFIG:
            difficulty = 1
            
        config = cls.DIFFICULTY_CONFIG[difficulty]
        
        # Generate problems within the difficulty range
        problems = []
        min_moves = config["min_moves"]
        max_moves = config["max_moves"]
        
        # Select random problems from library
        for i in range(config["problems_count"]):
            # Pick a random target move count
            target_moves = random.randint(min_moves, max_moves)
            
            # Get problems for this move count
            if target_moves in cls.PROBLEM_LIBRARY:
                problem_set = cls.PROBLEM_LIBRARY[target_moves]
                start, goal = random.choice(problem_set)
                
                # Deep copy to avoid mutations
                start_copy = [stocking[:] for stocking in start]
                goal_copy = [stocking[:] for stocking in goal]
                
                problems.append({
                    "problem_number": i + 1,
                    "start_state": start_copy,
                    "goal_state": goal_copy,
                    "minimum_moves": target_moves,
                    "show_minimum": config["show_minimum_moves"]
                })
        
        session_id = f"soc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
        
        return {
            "session_id": session_id,
            "task_type": "stockings_of_cambridge",
            "difficulty": difficulty,
            "config": {
                "planning_time_seconds": config["planning_time_seconds"],
                "move_penalty": config["move_penalty"],
                "show_minimum_moves": config["show_minimum_moves"],
                "stocking_capacities": cls.STOCKING_CAPACITIES,
                "colors": cls.COLORS
            },
            "problems": problems,
            "total_problems": len(problems),
            "generated_at": datetime.now().isoformat()
        }
    
    @classmethod
    def score_session(cls, session_data: Dict[str, Any],
                     user_solutions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Score a completed SOC session
        
        Args:
            session_data: Original session configuration
            user_solutions: List of user solutions with moves
            
        Returns:
            Detailed scoring including planning efficiency
        """
        difficulty = session_data.get("difficulty", 1)
        problems = session_data.get("problems", [])
        config = session_data.get("config", {})
        
        # Initialize scoring
        results = {
            "difficulty": difficulty,
            "total_problems": len(problems),
            "problems_solved": 0,
            "perfect_solutions": 0,  # Solved in minimum moves
            "total_moves": 0,
            "total_minimum_moves": 0,
            "planning_efficiency": 0.0,
            "average_time_per_problem": 0.0,
            "problems": [],
            "score": 0
        }
        
        total_time = 0
        
        for i, problem in enumerate(problems):
            if i >= len(user_solutions):
                break
                
            solution = user_solutions[i]
            min_moves = problem["minimum_moves"]
            user_moves = solution.get("moves_used", 0)
            time_taken = solution.get("time_seconds", 0)
            solved = solution.get("solved", False)
            
            results["total_minimum_moves"] += min_moves
            results["total_moves"] += user_moves
            total_time += time_taken
            
            problem_result = {
                "problem_number": problem["problem_number"],
                "minimum_moves": min_moves,
                "moves_used": user_moves,
                "time_seconds": time_taken,
                "solved": solved,
                "perfect": solved and user_moves == min_moves,
                "efficiency": min_moves / user_moves if user_moves > 0 else 0
            }
            
            if solved:
                results["problems_solved"] += 1
                if user_moves == min_moves:
                    results["perfect_solutions"] += 1
            
            results["problems"].append(problem_result)
        
        # Calculate overall metrics
        if results["total_problems"] > 0:
            results["average_time_per_problem"] = total_time / results["total_problems"]
        
        if results["total_moves"] > 0:
            results["planning_efficiency"] = results["total_minimum_moves"] / results["total_moves"]
        
        # Calculate final score (0-100)
        # Weight: 40% completion + 40% efficiency + 20% speed
        completion_score = (results["problems_solved"] / results["total_problems"]) * 40 if results["total_problems"] > 0 else 0
        efficiency_score = results["planning_efficiency"] * 40
        
        # Speed score (faster is better, normalize against expected time)
        expected_time_per_problem = config.get("planning_time_seconds", 30) * 0.5
        if results["average_time_per_problem"] > 0:
            speed_score = min(20, 20 * (expected_time_per_problem / results["average_time_per_problem"]))
        else:
            speed_score = 0
        
        # Bonus for perfect solutions
        perfect_bonus = (results["perfect_solutions"] / results["total_problems"]) * 10 if results["total_problems"] > 0 else 0
        
        results["score"] = int(completion_score + efficiency_score + speed_score + perfect_bonus)
        
        return results


# Singleton instance
soc_task_service = StockingsOfCambridgeTask()

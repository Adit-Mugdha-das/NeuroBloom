"""
Dimensional Change Card Sort (DCCS) Task Service

Clinical validation: Cognitive flexibility measure, simpler than WCST
Description: Sort by one dimension (color), then switch to another (shape)

MS Research Evidence:
- Simpler than WCST, less frustrating for MS patients
- Clear rule-switching paradigm
- Reference: Zelazo, 2006

Phases:
1. Sort by color (10 trials)
2. Sort by shape (10 trials)
3. Mixed - cue tells which rule (20 trials)
"""

import random
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime


class DCCSTask:
    """
    Dimensional Change Card Sort implementation
    
    Cards vary by two or three dimensions:
    - Color: red, blue
    - Shape: circle, star
    - Size: small, large (added in higher difficulties)
    
    Three phases:
    1. Pre-switch: Sort by one dimension (e.g., color)
    2. Post-switch: Sort by different dimension (e.g., shape)
    3. Mixed: Cue indicates which rule to use on each trial
    """
    
    # Card attributes
    COLORS = ["red", "blue"]
    SHAPES = ["circle", "star"]
    SIZES = ["small", "large"]
    
    # Difficulty configuration
    DIFFICULTY_CONFIG = {
        1: {
            "phase1_trials": 10,  # Pre-switch phase
            "phase2_trials": 10,  # Post-switch phase
            "phase3_trials": 20,  # Mixed phase
            "cue_duration_ms": 2000,  # How long cue is shown
            "use_size_dimension": False,  # Only color + shape
            "switch_frequency": 0.3,  # 30% switch trials in phase 3
            "conflicting_cues": False,  # Cards match both rules
        },
        2: {
            "phase1_trials": 10,
            "phase2_trials": 10,
            "phase3_trials": 20,
            "cue_duration_ms": 1800,
            "use_size_dimension": False,
            "switch_frequency": 0.4,
            "conflicting_cues": False,
        },
        3: {
            "phase1_trials": 12,
            "phase2_trials": 12,
            "phase3_trials": 24,
            "cue_duration_ms": 1500,
            "use_size_dimension": False,
            "switch_frequency": 0.5,
            "conflicting_cues": True,  # Some trials have conflicting features
        },
        4: {
            "phase1_trials": 12,
            "phase2_trials": 12,
            "phase3_trials": 24,
            "cue_duration_ms": 1200,
            "use_size_dimension": False,
            "switch_frequency": 0.5,
            "conflicting_cues": True,
        },
        5: {
            "phase1_trials": 15,
            "phase2_trials": 15,
            "phase3_trials": 30,
            "cue_duration_ms": 1000,
            "use_size_dimension": True,  # Add size dimension
            "switch_frequency": 0.6,
            "conflicting_cues": True,
        },
        6: {
            "phase1_trials": 15,
            "phase2_trials": 15,
            "phase3_trials": 30,
            "cue_duration_ms": 800,
            "use_size_dimension": True,
            "switch_frequency": 0.6,
            "conflicting_cues": True,
        },
        7: {
            "phase1_trials": 15,
            "phase2_trials": 15,
            "phase3_trials": 30,
            "cue_duration_ms": 600,
            "use_size_dimension": True,
            "switch_frequency": 0.7,
            "conflicting_cues": True,
        },
        8: {
            "phase1_trials": 18,
            "phase2_trials": 18,
            "phase3_trials": 36,
            "cue_duration_ms": 500,
            "use_size_dimension": True,
            "switch_frequency": 0.7,
            "conflicting_cues": True,
        },
        9: {
            "phase1_trials": 18,
            "phase2_trials": 18,
            "phase3_trials": 36,
            "cue_duration_ms": 400,
            "use_size_dimension": True,
            "switch_frequency": 0.8,
            "conflicting_cues": True,
        },
        10: {
            "phase1_trials": 20,
            "phase2_trials": 20,
            "phase3_trials": 40,
            "cue_duration_ms": 300,
            "use_size_dimension": True,
            "switch_frequency": 0.8,
            "conflicting_cues": True,
        },
    }
    
    @classmethod
    def generate_session(cls, difficulty: int = 1) -> Dict[str, Any]:
        """
        Generate a complete DCCS session with all three phases
        
        Args:
            difficulty: Level 1-10
            
        Returns:
            Session configuration with trials for all phases
        """
        if difficulty not in cls.DIFFICULTY_CONFIG:
            difficulty = 1
            
        config = cls.DIFFICULTY_CONFIG[difficulty]
        
        # Randomly select which dimension for each phase
        dimensions = ["color", "shape"]
        if config["use_size_dimension"]:
            dimensions.append("size")
            
        # Shuffle to randomize which comes first
        random.shuffle(dimensions)
        phase1_dimension = dimensions[0]
        phase2_dimension = dimensions[1] if len(dimensions) >= 2 else dimensions[0]
        
        # Generate target cards for sorting
        target_cards = cls._generate_target_cards(config["use_size_dimension"])
        
        # Generate trials for each phase
        phase1_trials = cls._generate_phase_trials(
            config["phase1_trials"],
            phase1_dimension,
            config["use_size_dimension"],
            is_mixed=False
        )
        
        phase2_trials = cls._generate_phase_trials(
            config["phase2_trials"],
            phase2_dimension,
            config["use_size_dimension"],
            is_mixed=False
        )
        
        phase3_trials = cls._generate_mixed_trials(
            config["phase3_trials"],
            [phase1_dimension, phase2_dimension],
            config["use_size_dimension"],
            config["switch_frequency"],
            config["conflicting_cues"]
        )
        
        session_id = f"dccs_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
        
        return {
            "session_id": session_id,
            "task_type": "dccs",
            "difficulty": difficulty,
            "config": {
                "cue_duration_ms": config["cue_duration_ms"],
                "use_size_dimension": config["use_size_dimension"],
                "switch_frequency": config["switch_frequency"],
                "phase1_dimension": phase1_dimension,
                "phase2_dimension": phase2_dimension,
            },
            "target_cards": target_cards,
            "phases": {
                "phase1": {
                    "name": "pre_switch",
                    "rule": phase1_dimension,
                    "instruction": f"Sort by {phase1_dimension.upper()}",
                    "trials": phase1_trials,
                    "total_trials": len(phase1_trials)
                },
                "phase2": {
                    "name": "post_switch",
                    "rule": phase2_dimension,
                    "instruction": f"Sort by {phase2_dimension.upper()}",
                    "trials": phase2_trials,
                    "total_trials": len(phase2_trials)
                },
                "phase3": {
                    "name": "mixed",
                    "rule": "varies",
                    "instruction": "Follow the cue on each trial",
                    "trials": phase3_trials,
                    "total_trials": len(phase3_trials)
                }
            },
            "total_trials": len(phase1_trials) + len(phase2_trials) + len(phase3_trials),
            "generated_at": datetime.now().isoformat()
        }
    
    @classmethod
    def _generate_target_cards(cls, use_size: bool) -> List[Dict[str, Any]]:
        """Generate the target sorting bins"""
        targets = []
        
        # Always have color and shape targets
        # Target 1: Red Circle
        target1 = {
            "id": 1,
            "color": "red",
            "shape": "circle"
        }
        if use_size:
            target1["size"] = "large"
        targets.append(target1)
        
        # Target 2: Blue Star
        target2 = {
            "id": 2,
            "color": "blue",
            "shape": "star"
        }
        if use_size:
            target2["size"] = "small"
        targets.append(target2)
        
        return targets
    
    @classmethod
    def _generate_card(cls, use_size: bool, conflicting: bool = False, 
                       target_match: Optional[str] = None) -> Dict[str, Any]:
        """Generate a single test card"""
        if conflicting:
            # Card that could match multiple targets on different dimensions
            # e.g., Red Star (matches target 1 on color, target 2 on shape)
            card = {
                "color": random.choice(cls.COLORS),
                "shape": random.choice(cls.SHAPES),
            }
        else:
            # Card that clearly matches one target
            card = {
                "color": random.choice(cls.COLORS),
                "shape": random.choice(cls.SHAPES),
            }
        
        if use_size:
            card["size"] = random.choice(cls.SIZES)
            
        return card
    
    @classmethod
    def _generate_phase_trials(cls, num_trials: int, dimension: str, 
                               use_size: bool, is_mixed: bool) -> List[Dict[str, Any]]:
        """Generate trials for Phase 1 or Phase 2 (single rule)"""
        trials = []
        
        for i in range(num_trials):
            card = cls._generate_card(use_size, conflicting=False)
            
            # Determine correct answer based on dimension
            if dimension == "color":
                correct_target = 1 if card["color"] == "red" else 2
            elif dimension == "shape":
                correct_target = 1 if card["shape"] == "circle" else 2
            elif dimension == "size":
                correct_target = 1 if card["size"] == "large" else 2
            else:
                correct_target = 1
                
            trials.append({
                "trial_number": i + 1,
                "card": card,
                "rule": dimension,
                "cue_shown": False,  # No cue in phase 1 and 2
                "correct_target": correct_target,
                "is_switch_trial": False  # Only relevant in phase 3
            })
            
        return trials
    
    @classmethod
    def _generate_mixed_trials(cls, num_trials: int, dimensions: List[str],
                               use_size: bool, switch_frequency: float,
                               conflicting_cues: bool) -> List[Dict[str, Any]]:
        """Generate trials for Phase 3 (mixed rules with cues)"""
        trials = []
        previous_rule = None
        
        for i in range(num_trials):
            # Decide if this is a switch trial
            if previous_rule is None:
                # First trial - pick random rule
                current_rule = random.choice(dimensions)
                is_switch = False
            else:
                # Determine if we should switch based on frequency
                if random.random() < switch_frequency:
                    # Switch trial
                    other_rules = [d for d in dimensions if d != previous_rule]
                    current_rule = random.choice(other_rules) if other_rules else previous_rule
                    is_switch = True
                else:
                    # Repeat trial
                    current_rule = previous_rule
                    is_switch = False
            
            # Generate card (potentially conflicting)
            card = cls._generate_card(use_size, conflicting=conflicting_cues)
            
            # Determine correct answer based on current rule
            if current_rule == "color":
                correct_target = 1 if card["color"] == "red" else 2
            elif current_rule == "shape":
                correct_target = 1 if card["shape"] == "circle" else 2
            elif current_rule == "size":
                correct_target = 1 if card["size"] == "large" else 2
            else:
                correct_target = 1
                
            trials.append({
                "trial_number": i + 1,
                "card": card,
                "rule": current_rule,
                "cue_shown": True,  # Cue is shown in mixed phase
                "correct_target": correct_target,
                "is_switch_trial": is_switch,
                "previous_rule": previous_rule
            })
            
            previous_rule = current_rule
            
        return trials
    
    @classmethod
    def score_session(cls, session_data: Dict[str, Any], 
                     user_responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Score a completed DCCS session
        
        Args:
            session_data: Original session configuration
            user_responses: List of user responses with timing
            
        Returns:
            Detailed scoring results including switch costs
        """
        difficulty = session_data.get("difficulty", 1)
        phases = session_data.get("phases", {})
        
        # Initialize scoring
        results = {
            "difficulty": difficulty,
            "total_trials": 0,
            "correct_trials": 0,
            "accuracy": 0.0,
            "mean_rt": 0.0,
            "phases": {},
            "switch_cost": 0.0,
            "perseverative_errors": 0,
            "score": 0
        }
        
        # Score each phase separately
        response_idx = 0
        
        for phase_name in ["phase1", "phase2", "phase3"]:
            if phase_name not in phases:
                continue
                
            phase = phases[phase_name]
            phase_trials = phase["trials"]
            phase_results = {
                "total": len(phase_trials),
                "correct": 0,
                "accuracy": 0.0,
                "mean_rt": 0.0,
                "rts": []
            }
            
            for trial in phase_trials:
                if response_idx >= len(user_responses):
                    break
                    
                response = user_responses[response_idx]
                response_idx += 1
                
                is_correct = response.get("selected_target") == trial["correct_target"]
                rt = response.get("reaction_time_ms", 0)
                
                if is_correct:
                    phase_results["correct"] += 1
                    results["correct_trials"] += 1
                    
                if rt > 0:
                    phase_results["rts"].append(rt)
                    
                results["total_trials"] += 1
            
            # Calculate phase metrics
            if phase_results["total"] > 0:
                phase_results["accuracy"] = phase_results["correct"] / phase_results["total"]
                
            if phase_results["rts"]:
                phase_results["mean_rt"] = sum(phase_results["rts"]) / len(phase_results["rts"])
                
            results["phases"][phase_name] = phase_results
        
        # Calculate switch cost (Phase 3 specific)
        if "phase3" in results["phases"]:
            switch_cost = cls._calculate_switch_cost(
                phases["phase3"]["trials"],
                user_responses[results["phases"]["phase1"]["total"] + results["phases"]["phase2"]["total"]:]
            )
            results["switch_cost"] = switch_cost
        
        # Calculate perseverative errors (using wrong rule from previous phase)
        if "phase2" in results["phases"]:
            perseverative = cls._count_perseverative_errors(
                phases["phase1"]["rule"],
                phases["phase2"]["trials"],
                user_responses[results["phases"]["phase1"]["total"]:
                             results["phases"]["phase1"]["total"] + results["phases"]["phase2"]["total"]]
            )
            results["perseverative_errors"] = perseverative
        
        # Overall accuracy
        if results["total_trials"] > 0:
            results["accuracy"] = results["correct_trials"] / results["total_trials"]
            
        # Calculate overall mean RT
        all_rts = []
        for phase_name, phase_result in results["phases"].items():
            all_rts.extend(phase_result.get("rts", []))
        if all_rts:
            results["mean_rt"] = sum(all_rts) / len(all_rts)
        
        # Calculate final score (0-100)
        # Weight: 60% accuracy + 20% speed + 20% switch performance
        accuracy_score = results["accuracy"] * 60
        
        # Speed score (faster is better, normalize against expected RT)
        expected_rt = 1500  # Expected mean RT in ms
        if results["mean_rt"] > 0:
            speed_score = max(0, min(20, 20 * (expected_rt / results["mean_rt"])))
        else:
            speed_score = 0
            
        # Switch performance (lower switch cost is better)
        if results["switch_cost"] >= 0:
            switch_score = max(0, 20 - (results["switch_cost"] / 50))  # Normalize
        else:
            switch_score = 10
            
        results["score"] = int(accuracy_score + speed_score + switch_score)
        
        return results
    
    @classmethod
    def _calculate_switch_cost(cls, trials: List[Dict[str, Any]], 
                               responses: List[Dict[str, Any]]) -> float:
        """
        Calculate switch cost: mean RT for switch trials - mean RT for repeat trials
        """
        switch_rts = []
        repeat_rts = []
        
        for i, trial in enumerate(trials):
            if i >= len(responses):
                break
                
            response = responses[i]
            rt = response.get("reaction_time_ms", 0)
            
            if rt <= 0:
                continue
                
            # Only count correct trials for switch cost
            if response.get("selected_target") != trial["correct_target"]:
                continue
                
            if trial.get("is_switch_trial", False):
                switch_rts.append(rt)
            else:
                repeat_rts.append(rt)
        
        if not switch_rts or not repeat_rts:
            return 0.0
            
        switch_mean = sum(switch_rts) / len(switch_rts)
        repeat_mean = sum(repeat_rts) / len(repeat_rts)
        
        return switch_mean - repeat_mean
    
    @classmethod
    def _count_perseverative_errors(cls, previous_rule: str, 
                                    trials: List[Dict[str, Any]],
                                    responses: List[Dict[str, Any]]) -> int:
        """
        Count how many times user used the previous phase's rule in current phase
        """
        perseverative_count = 0
        
        for i, trial in enumerate(trials):
            if i >= len(responses):
                break
                
            response = responses[i]
            selected = response.get("selected_target")
            correct = trial["correct_target"]
            
            # Skip correct responses
            if selected == correct:
                continue
                
            # Check if they used previous rule
            card = trial["card"]
            if previous_rule == "color":
                previous_rule_target = 1 if card["color"] == "red" else 2
            elif previous_rule == "shape":
                previous_rule_target = 1 if card["shape"] == "circle" else 2
            elif previous_rule == "size":
                previous_rule_target = 1 if card["size"] == "large" else 2
            else:
                continue
                
            if selected == previous_rule_target:
                perseverative_count += 1
                
        return perseverative_count


# Singleton instance
dccs_task_service = DCCSTask()

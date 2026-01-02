"""
Useful Field of View (UFOV) Task Service

Clinical Validation: Ball et al., 1993 - Driving safety predictor
Purpose: Assess visual processing speed and divided attention

Three Subtests:
1. Central ID only (processing speed)
2. Central + Peripheral (divided attention)
3. Central + Peripheral + Distractors (selective attention)

MS Research: Predicts driving ability in MS patients
"""

import random
from typing import Dict, List, Tuple, Optional

# UFOV difficulty configurations - MS-friendly progression
UFOV_CONFIGS = [
    # Level 1-3: Central only (build confidence)
    {
        "level": 1,
        "subtest": "central_only",
        "presentation_time_ms": 800,
        "central_targets": ["car", "truck"],
        "peripheral_targets": [],
        "num_distractors": 0,
        "description": "Identify central vehicle (car or truck)"
    },
    {
        "level": 2,
        "subtest": "central_only",
        "presentation_time_ms": 700,
        "central_targets": ["car", "truck"],
        "peripheral_targets": [],
        "num_distractors": 0,
        "description": "Identify central vehicle - faster"
    },
    {
        "level": 3,
        "subtest": "central_only",
        "presentation_time_ms": 600,
        "central_targets": ["car", "truck"],
        "peripheral_targets": [],
        "num_distractors": 0,
        "description": "Identify central vehicle - rapid"
    },
    # Level 4-6: Central + Peripheral (divided attention)
    {
        "level": 4,
        "subtest": "central_peripheral",
        "presentation_time_ms": 500,
        "central_targets": ["car", "truck"],
        "peripheral_targets": ["circle", "triangle", "square"],
        "num_distractors": 0,
        "description": "Identify central vehicle AND locate peripheral shape"
    },
    {
        "level": 5,
        "subtest": "central_peripheral",
        "presentation_time_ms": 400,
        "central_targets": ["car", "truck"],
        "peripheral_targets": ["circle", "triangle", "square"],
        "num_distractors": 0,
        "description": "Divided attention - faster"
    },
    {
        "level": 6,
        "subtest": "central_peripheral",
        "presentation_time_ms": 350,
        "central_targets": ["car", "truck"],
        "peripheral_targets": ["circle", "triangle", "square"],
        "num_distractors": 0,
        "description": "Divided attention - rapid"
    },
    # Level 7-10: Central + Peripheral + Distractors (selective attention)
    {
        "level": 7,
        "subtest": "central_peripheral_distractors",
        "presentation_time_ms": 300,
        "central_targets": ["car", "truck"],
        "peripheral_targets": ["circle", "triangle", "square"],
        "num_distractors": 24,
        "description": "Selective attention with distractors"
    },
    {
        "level": 8,
        "subtest": "central_peripheral_distractors",
        "presentation_time_ms": 250,
        "central_targets": ["car", "truck"],
        "peripheral_targets": ["circle", "triangle", "square"],
        "num_distractors": 36,
        "description": "Complex selective attention"
    },
    {
        "level": 9,
        "subtest": "central_peripheral_distractors",
        "presentation_time_ms": 200,
        "central_targets": ["car", "truck"],
        "peripheral_targets": ["circle", "triangle", "square"],
        "num_distractors": 47,
        "description": "Advanced selective attention"
    },
    {
        "level": 10,
        "subtest": "central_peripheral_distractors",
        "presentation_time_ms": 150,
        "central_targets": ["car", "truck"],
        "peripheral_targets": ["circle", "triangle", "square"],
        "num_distractors": 47,
        "description": "Expert driving safety assessment"
    }
]

# Peripheral locations (clock positions)
PERIPHERAL_POSITIONS = [
    {"angle": 0, "label": "3 o'clock", "x": 1, "y": 0},
    {"angle": 45, "label": "1:30", "x": 0.707, "y": -0.707},
    {"angle": 90, "label": "12 o'clock", "x": 0, "y": -1},
    {"angle": 135, "label": "10:30", "x": -0.707, "y": -0.707},
    {"angle": 180, "label": "9 o'clock", "x": -1, "y": 0},
    {"angle": 225, "label": "7:30", "x": -0.707, "y": 0.707},
    {"angle": 270, "label": "6 o'clock", "x": 0, "y": 1},
    {"angle": 315, "label": "4:30", "x": 0.707, "y": 0.707}
]


def generate_trial(difficulty_level: int = 1) -> Dict:
    """
    Generate a UFOV trial based on difficulty level
    
    Args:
        difficulty_level: 1-10, determines presentation time and complexity
        
    Returns:
        Trial configuration with central target, peripheral target, and distractors
    """
    if difficulty_level < 1 or difficulty_level > 10:
        difficulty_level = 1
    
    config = UFOV_CONFIGS[difficulty_level - 1]
    
    # Select central target
    central_target = random.choice(config["central_targets"])
    
    # Select peripheral target and position (if applicable)
    peripheral_target = None
    peripheral_position = None
    peripheral_angle = None
    
    if config["subtest"] in ["central_peripheral", "central_peripheral_distractors"]:
        peripheral_target = random.choice(config["peripheral_targets"])
        position = random.choice(PERIPHERAL_POSITIONS)
        peripheral_position = position["label"]
        peripheral_angle = position["angle"]
    
    # Generate distractors (if applicable)
    distractors = []
    if config["num_distractors"] > 0 and peripheral_target is not None and peripheral_angle is not None:
        distractors = _generate_distractors(
            config["num_distractors"],
            peripheral_target,
            peripheral_angle
        )
    
    return {
        "difficulty_level": difficulty_level,
        "subtest": config["subtest"],
        "presentation_time_ms": config["presentation_time_ms"],
        "description": config["description"],
        "central_target": central_target,
        "peripheral_target": peripheral_target,
        "peripheral_position": peripheral_position,
        "peripheral_angle": peripheral_angle,
        "distractors": distractors,
        "instructions": _get_instructions(config["subtest"])
    }


def _generate_distractors(count: int, target_shape: str, target_angle: int) -> List[Dict]:
    """
    Generate distractor shapes for peripheral vision
    Ensures no overlap with target position
    """
    distractors = []
    shapes = ["circle", "triangle", "square"]
    
    # Create a grid of possible positions
    # Avoid target angle ±20 degrees
    available_angles = []
    for angle in range(0, 360, 8):  # Every 8 degrees
        if abs(angle - target_angle) > 20 and abs(angle - target_angle) < 340:
            available_angles.append(angle)
    
    # Randomize and select positions
    random.shuffle(available_angles)
    selected_angles = available_angles[:count]
    
    for angle in selected_angles:
        # Random radius (distance from center)
        radius = random.uniform(0.5, 0.95)  # Normalized radius
        
        # Random shape (can be same as target - that's the challenge)
        shape = random.choice(shapes)
        
        distractors.append({
            "shape": shape,
            "angle": angle,
            "radius": radius
        })
    
    return distractors


def _get_instructions(subtest: str) -> str:
    """Get instructions based on subtest type"""
    instructions = {
        "central_only": "Identify the central vehicle: Car or Truck?",
        "central_peripheral": "Identify the central vehicle AND locate the peripheral shape",
        "central_peripheral_distractors": "Identify the central vehicle AND locate the peripheral target among distractors"
    }
    return instructions.get(subtest, "")


def score_response(
    trial_data: Dict,
    central_response: str,
    peripheral_response: Optional[str] = None
) -> Dict:
    """
    Score a UFOV response
    
    Args:
        trial_data: The original trial configuration
        central_response: User's answer for central target ("car" or "truck")
        peripheral_response: User's answer for peripheral position (e.g., "3 o'clock")
        
    Returns:
        Scoring results with accuracy, processing speed metrics
    """
    subtest = trial_data["subtest"]
    
    # Score central target
    central_correct = (central_response.lower() == trial_data["central_target"].lower())
    
    # Score peripheral target (if applicable)
    peripheral_correct = None
    if subtest in ["central_peripheral", "central_peripheral_distractors"]:
        if peripheral_response:
            peripheral_correct = (peripheral_response == trial_data["peripheral_position"])
        else:
            peripheral_correct = False
    
    # Calculate overall accuracy
    if subtest == "central_only":
        accuracy = 1.0 if central_correct else 0.0
        score = 100 if central_correct else 0
    else:
        # Both must be correct for full credit
        if central_correct and peripheral_correct:
            accuracy = 1.0
            score = 100
        elif central_correct or peripheral_correct:
            accuracy = 0.5
            score = 50
        else:
            accuracy = 0.0
            score = 0
    
    # Performance classification
    if accuracy >= 1.0:
        performance = "perfect"
    elif accuracy >= 0.5:
        performance = "partial"
    else:
        performance = "incorrect"
    
    return {
        "score": score,
        "accuracy": accuracy,
        "central_correct": central_correct,
        "peripheral_correct": peripheral_correct,
        "performance": performance,
        "subtest": subtest,
        "presentation_time_ms": trial_data["presentation_time_ms"],
        "processing_speed_score": _calculate_processing_speed_score(
            trial_data["presentation_time_ms"],
            central_correct
        )
    }


def _calculate_processing_speed_score(presentation_time_ms: int, correct: bool) -> float:
    """
    Calculate processing speed score
    Faster presentation times with correct responses = higher scores
    """
    if not correct:
        return 0.0
    
    # Normalize based on presentation time (800ms = baseline, 150ms = expert)
    # Linear scale: 800ms = 1.0, 150ms = 5.33
    max_time = 800
    min_time = 150
    
    normalized = (max_time - presentation_time_ms) / (max_time - min_time)
    processing_speed = 1.0 + (normalized * 4.33)
    
    return min(5.33, max(1.0, processing_speed))


def calculate_difficulty_adjustment(
    recent_scores: List[Dict],
    current_difficulty: int
) -> Tuple[int, str]:
    """
    Calculate difficulty adjustment based on recent performance
    
    Args:
        recent_scores: List of recent score dictionaries
        current_difficulty: Current difficulty level (1-10)
        
    Returns:
        Tuple of (new_difficulty_level, reason)
    """
    if not recent_scores or len(recent_scores) < 3:
        return current_difficulty, "insufficient_data"
    
    # Calculate average accuracy from recent trials
    avg_accuracy = sum(s["accuracy"] for s in recent_scores) / len(recent_scores)
    
    # Calculate central accuracy (core skill)
    central_correct_count = sum(1 for s in recent_scores if s.get("central_correct", False))
    central_accuracy = central_correct_count / len(recent_scores)
    
    # Increase difficulty if performing well
    if avg_accuracy >= 0.85 and central_accuracy >= 0.9 and current_difficulty < 10:
        return current_difficulty + 1, "high_performance"
    
    # Decrease difficulty if struggling
    elif avg_accuracy < 0.4 and current_difficulty > 1:
        return current_difficulty - 1, "low_performance"
    
    # Stay at current level
    else:
        return current_difficulty, "appropriate_challenge"


def get_feedback_message(score_result: Dict) -> str:
    """
    Generate feedback message based on performance
    """
    performance = score_result["performance"]
    subtest = score_result["subtest"]
    time_ms = score_result["presentation_time_ms"]
    
    if performance == "perfect":
        if time_ms <= 200:
            return f"Excellent! You correctly identified both targets in just {time_ms}ms. Your visual processing speed is exceptional!"
        elif time_ms <= 400:
            return f"Great work! Both targets identified correctly in {time_ms}ms. Your divided attention is strong."
        else:
            return f"Good job! You identified the target(s) correctly. Keep building speed!"
    
    elif performance == "partial":
        if score_result.get("central_correct"):
            return f"You got the central target! The peripheral target was at {score_result.get('peripheral_position', 'unknown')}. Try expanding your visual field awareness."
        else:
            return "You located the peripheral target but missed the central one. Remember to identify the center vehicle first, then expand awareness."
    
    else:
        if subtest == "central_only":
            return f"The central target appeared for {time_ms}ms. Focus on the center and respond quickly. Practice will improve your processing speed."
        else:
            return "Divided attention is challenging! Try to maintain central focus while using peripheral awareness. This skill improves with practice."


def get_performance_summary(session_scores: List[Dict]) -> Dict:
    """
    Generate performance summary for a session
    """
    if not session_scores:
        return {}
    
    total_trials = len(session_scores)
    central_correct = sum(1 for s in session_scores if s.get("central_correct", False))
    peripheral_correct = sum(1 for s in session_scores if s.get("peripheral_correct") is True)
    perfect_trials = sum(1 for s in session_scores if s["performance"] == "perfect")
    
    avg_accuracy = sum(s["accuracy"] for s in session_scores) / total_trials
    avg_processing_speed = sum(s["processing_speed_score"] for s in session_scores) / total_trials
    
    # Determine subtests used
    subtests_used = set(s["subtest"] for s in session_scores)
    
    return {
        "total_trials": total_trials,
        "perfect_trials": perfect_trials,
        "central_accuracy": central_correct / total_trials,
        "peripheral_accuracy": peripheral_correct / total_trials if peripheral_correct > 0 else None,
        "overall_accuracy": avg_accuracy,
        "avg_processing_speed_score": avg_processing_speed,
        "subtests_completed": list(subtests_used),
        "driving_safety_indicator": _get_driving_safety_indicator(avg_accuracy, avg_processing_speed)
    }


def _get_driving_safety_indicator(accuracy: float, processing_speed: float) -> str:
    """
    Provide driving safety indicator based on UFOV performance
    Research shows UFOV predicts crash risk
    """
    if accuracy >= 0.8 and processing_speed >= 3.0:
        return "excellent_visual_processing"
    elif accuracy >= 0.6 and processing_speed >= 2.0:
        return "good_visual_processing"
    elif accuracy >= 0.4:
        return "moderate_visual_processing"
    else:
        return "needs_improvement"

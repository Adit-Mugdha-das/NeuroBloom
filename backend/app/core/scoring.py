"""
Scoring algorithms for cognitive domain assessment
Converts raw test metrics to 0-100 scores
"""
import json
from typing import Dict, Any

def calculate_working_memory_score(metrics: Dict[str, Any]) -> float:
    """
    N-Back scoring: accuracy (60%) + RT (30%) + consistency (10%)
    """
    accuracy = metrics.get('accuracy', 0) / 100  # Convert to 0-1
    mean_rt = metrics.get('mean_rt', 1000)
    rt_std = metrics.get('rt_std', 200)
    
    # Accuracy component (60 points max)
    accuracy_score = accuracy * 60
    
    # RT component (30 points max) - faster is better
    # Normalize RT: 300ms=100%, 1000ms=0%
    rt_normalized = max(0, min(1, (1000 - mean_rt) / 700))
    rt_score = rt_normalized * 30
    
    # Consistency component (10 points max) - lower std is better
    # Normalize std: 0-50ms=100%, >200ms=0%
    consistency_normalized = max(0, min(1, (200 - rt_std) / 200))
    consistency_score = consistency_normalized * 10
    
    return min(100, accuracy_score + rt_score + consistency_score)


def calculate_attention_score(metrics: Dict[str, Any]) -> float:
    """
    CPT scoring: hit rate (60%) + false alarm penalty (30%) + vigilance (10%)
    """
    targets_shown = metrics.get('targets_shown', 1)
    targets_hit = metrics.get('targets_hit', 0)
    false_alarms = metrics.get('false_alarms', 0)
    mean_rt = metrics.get('mean_rt', 1000)
    vigilance_decrement = metrics.get('vigilance_decrement', 0)
    
    # Hit rate (60 points)
    hit_rate = targets_hit / targets_shown if targets_shown > 0 else 0
    hit_score = hit_rate * 60
    
    # False alarm penalty (30 points - subtract for errors)
    # More than 5 false alarms = 0 points
    fa_penalty = max(0, 30 - (false_alarms * 6))
    
    # Vigilance (10 points) - penalize if performance drops
    vigilance_score = max(0, 10 - (vigilance_decrement * 50))
    
    return min(100, hit_score + fa_penalty + vigilance_score)


def calculate_flexibility_score(metrics: Dict[str, Any]) -> float:
    """
    Task switching: accuracy (60%) + switch cost (30%) + perseveration (10%)
    """
    accuracy = metrics.get('accuracy', 0) / 100
    switch_cost_rt = metrics.get('switch_cost_rt', 500)
    perseveration_errors = metrics.get('perseveration_errors', 0)
    
    # Accuracy (60 points)
    accuracy_score = accuracy * 60
    
    # Switch cost (30 points) - lower is better
    # 0-100ms = 30 points, >400ms = 0 points
    switch_normalized = max(0, min(1, (400 - switch_cost_rt) / 400))
    switch_score = switch_normalized * 30
    
    # Perseveration penalty (10 points)
    # 0 errors = 10 points, 5+ errors = 0 points
    persev_score = max(0, 10 - (perseveration_errors * 2))
    
    return min(100, accuracy_score + switch_score + persev_score)


def calculate_planning_score(metrics: Dict[str, Any]) -> float:
    """
    Tower of Hanoi: efficiency (60%) + planning time (30%) + completion (10%)
    """
    moves_taken = metrics.get('moves_taken', 100)
    optimal_moves = metrics.get('optimal_moves', 7)
    planning_time_ms = metrics.get('planning_time_ms', 30000)
    completed = metrics.get('completed', False)
    
    # Efficiency (60 points) - closer to optimal is better
    excess_moves = max(0, moves_taken - optimal_moves)
    # 0 excess = 60 points, 10+ excess = 0 points
    efficiency_score = max(0, 60 - (excess_moves * 6))
    
    # Planning time (30 points) - moderate is best
    # 5-15 seconds = optimal, <5 or >30 = poor
    planning_sec = planning_time_ms / 1000
    if 5 <= planning_sec <= 15:
        planning_score = 30
    elif planning_sec < 5:
        planning_score = max(0, planning_sec * 6)
    else:
        planning_score = max(0, 30 - ((planning_sec - 15) * 2))
    
    # Completion bonus (10 points)
    completion_score = 10 if completed else 0
    
    return min(100, efficiency_score + planning_score + completion_score)


def calculate_processing_speed_score(metrics: Dict[str, Any]) -> float:
    """
    Reaction time: simple RT (40%) + choice RT (40%) + consistency (20%)
    """
    simple_rt_mean = metrics.get('simple_rt_mean', 500)
    choice_rt_mean = metrics.get('choice_rt_mean', 700)
    simple_rt_std = metrics.get('simple_rt_std', 100)
    choice_accuracy = metrics.get('choice_accuracy', 0.5)
    
    # Simple RT (40 points) - 200ms=100%, 500ms=0%
    simple_normalized = max(0, min(1, (500 - simple_rt_mean) / 300))
    simple_score = simple_normalized * 40
    
    # Choice RT with accuracy (40 points)
    # 400ms + high accuracy = 40 points
    choice_normalized = max(0, min(1, (800 - choice_rt_mean) / 400))
    choice_score = choice_normalized * 30 + (choice_accuracy * 10)
    
    # Consistency (20 points) - lower std is better
    consistency_normalized = max(0, min(1, (150 - simple_rt_std) / 150))
    consistency_score = consistency_normalized * 20
    
    return min(100, simple_score + choice_score + consistency_score)


def calculate_visual_scanning_score(metrics: Dict[str, Any]) -> float:
    """
    Visual search: accuracy (60%) + speed (30%) + efficiency (10%)
    """
    targets_total = metrics.get('targets_total', 5)
    targets_found = metrics.get('targets_found', 0)
    search_time_ms = metrics.get('search_time_ms', 30000)
    
    # Accuracy (60 points)
    accuracy = targets_found / targets_total if targets_total > 0 else 0
    accuracy_score = accuracy * 60
    
    # Speed (30 points) - time per target found
    # 2 seconds per target = 30 points, 5+ seconds = 0 points
    time_per_target = search_time_ms / max(1, targets_found)
    speed_normalized = max(0, min(1, (5000 - time_per_target) / 3000))
    speed_score = speed_normalized * 30
    
    # Efficiency (10 points) - found all targets quickly
    efficiency_score = 10 if targets_found == targets_total else (targets_found / targets_total) * 10
    
    return min(100, accuracy_score + speed_score + efficiency_score)


def calculate_overall_score(domain_scores: Dict[str, float]) -> float:
    """
    Calculate overall cognitive score (average of all domains)
    """
    scores = [
        domain_scores.get('working_memory', 0),
        domain_scores.get('attention', 0),
        domain_scores.get('flexibility', 0),
        domain_scores.get('planning', 0),
        domain_scores.get('processing_speed', 0),
        domain_scores.get('visual_scanning', 0)
    ]
    
    # Only average completed domains (non-zero scores)
    completed_scores = [s for s in scores if s > 0]
    
    if not completed_scores:
        return 0.0
    
    return sum(completed_scores) / len(completed_scores)

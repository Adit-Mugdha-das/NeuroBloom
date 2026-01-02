"""
Test suite for Multiple Object Tracking (MOT) task
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.multiple_object_tracking_task import MultipleObjectTrackingTask


def test_trial_generation():
    """Test MOT trial generation across difficulty levels."""
    print("\n=== Testing MOT Trial Generation ===\n")
    
    for difficulty in [1, 3, 5, 7, 10]:
        trial = MultipleObjectTrackingTask.generate_trial(difficulty)
        
        print(f"Difficulty {difficulty}:")
        print(f"  Total objects: {trial['total_objects']}")
        print(f"  Num targets: {trial['num_targets']}")
        print(f"  Tracking duration: {trial['tracking_duration']}s")
        print(f"  Arena size: {trial['arena_size']}px")
        print(f"  Speed multiplier: {trial['speed_multiplier']}")
        print(f"  Target indices: {trial['target_indices']}")
        
        # Verify objects
        assert len(trial['objects']) == trial['total_objects']
        target_count = sum(1 for obj in trial['objects'] if obj['is_target'])
        assert target_count == trial['num_targets']
        
        # Verify positions are within arena
        for obj in trial['objects']:
            assert 0 <= obj['x'] <= trial['arena_size']
            assert 0 <= obj['y'] <= trial['arena_size']
            assert 'vx' in obj and 'vy' in obj
        
        print("  ✓ Trial structure valid\n")


def test_perfect_response():
    """Test scoring when user identifies all targets correctly."""
    print("\n=== Testing Perfect Response ===\n")
    
    trial = MultipleObjectTrackingTask.generate_trial(difficulty=5)
    
    # Perfect response: select exactly the target indices
    user_response = {
        "selected_objects": trial['target_indices'].copy(),
        "response_time": 1.5
    }
    
    results = MultipleObjectTrackingTask.score_response(trial, user_response)
    
    print(f"Score: {results['score']:.3f}")
    print(f"Accuracy: {results['accuracy']:.3f}")
    print(f"Precision: {results['precision']:.3f}")
    print(f"F1 Score: {results['f1_score']:.3f}")
    print(f"Targets found: {results['targets_found']}/{results['total_targets']}")
    print(f"False positives: {results['false_positives']}")
    print(f"Performance: {results['performance']}")
    
    assert results['accuracy'] == 1.0
    assert results['precision'] == 1.0
    assert results['false_positives'] == 0
    assert results['false_negatives'] == 0
    assert results['performance'] == 'perfect'
    print("✓ Perfect response scored correctly\n")


def test_partial_response():
    """Test scoring when user misses some targets."""
    print("\n=== Testing Partial Response ===\n")
    
    trial = MultipleObjectTrackingTask.generate_trial(difficulty=5)
    
    # Select only first 2 targets out of 4
    user_response = {
        "selected_objects": trial['target_indices'][:2],
        "response_time": 2.0
    }
    
    results = MultipleObjectTrackingTask.score_response(trial, user_response)
    
    print(f"Score: {results['score']:.3f}")
    print(f"Accuracy: {results['accuracy']:.3f}")
    print(f"Precision: {results['precision']:.3f}")
    print(f"Targets found: {results['targets_found']}/{results['total_targets']}")
    print(f"Targets missed: {results['targets_missed']}")
    print(f"False positives: {results['false_positives']}")
    print(f"Performance: {results['performance']}")
    
    assert results['accuracy'] == 0.5  # 2 out of 4
    assert results['precision'] == 1.0  # No false positives
    assert results['targets_missed'] == 2
    print("✓ Partial response scored correctly\n")


def test_false_alarms():
    """Test scoring when user selects non-target objects."""
    print("\n=== Testing False Alarms ===\n")
    
    trial = MultipleObjectTrackingTask.generate_trial(difficulty=5)
    
    # Get non-target indices
    all_indices = set(range(trial['total_objects']))
    target_indices = set(trial['target_indices'])
    non_target_indices = list(all_indices - target_indices)
    
    # Select all targets + 2 non-targets
    user_response = {
        "selected_objects": trial['target_indices'] + non_target_indices[:2],
        "response_time": 1.8
    }
    
    results = MultipleObjectTrackingTask.score_response(trial, user_response)
    
    print(f"Score: {results['score']:.3f}")
    print(f"Accuracy: {results['accuracy']:.3f}")
    print(f"Precision: {results['precision']:.3f}")
    print(f"Targets found: {results['targets_found']}/{results['total_targets']}")
    print(f"False positives: {results['false_positives']}")
    print(f"Performance: {results['performance']}")
    
    assert results['accuracy'] == 1.0  # All targets found
    assert results['false_positives'] == 2
    assert results['precision'] < 1.0  # Precision penalized
    print("✓ False alarms scored correctly\n")


def test_poor_response():
    """Test scoring when user performs poorly."""
    print("\n=== Testing Poor Response ===\n")
    
    trial = MultipleObjectTrackingTask.generate_trial(difficulty=5)
    
    # Get non-target indices
    all_indices = set(range(trial['total_objects']))
    target_indices = set(trial['target_indices'])
    non_target_indices = list(all_indices - target_indices)
    
    # Select only 1 target + 3 non-targets
    user_response = {
        "selected_objects": [trial['target_indices'][0]] + non_target_indices[:3],
        "response_time": 2.5
    }
    
    results = MultipleObjectTrackingTask.score_response(trial, user_response)
    
    print(f"Score: {results['score']:.3f}")
    print(f"Accuracy: {results['accuracy']:.3f}")
    print(f"Precision: {results['precision']:.3f}")
    print(f"Targets found: {results['targets_found']}/{results['total_targets']}")
    print(f"Targets missed: {results['targets_missed']}")
    print(f"False positives: {results['false_positives']}")
    print(f"Performance: {results['performance']}")
    
    assert results['accuracy'] == 0.25  # 1 out of 4
    assert results['false_positives'] == 3
    assert results['precision'] == 0.25  # 1 correct out of 4 selected
    print("✓ Poor response scored correctly\n")


def test_difficulty_adaptation():
    """Test adaptive difficulty adjustment."""
    print("\n=== Testing Difficulty Adaptation ===\n")
    
    # Test increase difficulty (excellent performance)
    recent_scores = [0.9, 0.92, 0.88, 0.91, 0.90]
    new_diff = MultipleObjectTrackingTask.calculate_difficulty_adjustment(
        recent_scores, 5, accuracy=0.9, precision=0.85
    )
    print(f"Excellent performance (avg 0.90): {5} → {new_diff}")
    assert new_diff == 6
    
    # Test decrease difficulty (poor performance)
    recent_scores = [0.3, 0.35, 0.4, 0.38, 0.32]
    new_diff = MultipleObjectTrackingTask.calculate_difficulty_adjustment(
        recent_scores, 5, accuracy=0.35, precision=0.4
    )
    print(f"Poor performance (avg 0.35): {5} → {new_diff}")
    assert new_diff == 4
    
    # Test maintain difficulty (moderate performance)
    recent_scores = [0.6, 0.65, 0.62, 0.58, 0.63]
    new_diff = MultipleObjectTrackingTask.calculate_difficulty_adjustment(
        recent_scores, 5, accuracy=0.62, precision=0.65
    )
    print(f"Moderate performance (avg 0.62): {5} → {new_diff}")
    assert new_diff == 5
    
    print("✓ Difficulty adaptation working correctly\n")


def test_tracking_metrics():
    """Test tracking efficiency and F1 score calculations."""
    print("\n=== Testing Tracking Metrics ===\n")
    
    trial = MultipleObjectTrackingTask.generate_trial(difficulty=5)
    
    # Mixed performance: 3 correct, 1 miss, 1 false alarm
    user_response = {
        "selected_objects": trial['target_indices'][:3] + [max(trial['target_indices']) + 1],
        "response_time": 1.7
    }
    
    results = MultipleObjectTrackingTask.score_response(trial, user_response)
    
    print(f"Accuracy (Recall): {results['accuracy']:.3f}")
    print(f"Precision: {results['precision']:.3f}")
    print(f"F1 Score: {results['f1_score']:.3f}")
    print(f"Tracking Efficiency: {results['tracking_efficiency']:.3f}")
    
    # Verify F1 calculation
    expected_f1 = 2 * (results['precision'] * results['recall']) / (results['precision'] + results['recall'])
    assert abs(results['f1_score'] - expected_f1) < 0.001
    
    print("✓ Tracking metrics calculated correctly\n")


def test_feedback_messages():
    """Test feedback message generation."""
    print("\n=== Testing Feedback Messages ===\n")
    
    trial = MultipleObjectTrackingTask.generate_trial(difficulty=5)
    
    # Perfect performance
    results = MultipleObjectTrackingTask.score_response(
        trial,
        {"selected_objects": trial['target_indices'], "response_time": 1.5}
    )
    message = MultipleObjectTrackingTask.get_feedback_message(results)
    print(f"Perfect: {message}")
    assert "Perfect tracking" in message
    
    # All targets but with false alarms
    all_indices = set(range(trial['total_objects']))
    non_targets = list(all_indices - set(trial['target_indices']))
    results = MultipleObjectTrackingTask.score_response(
        trial,
        {"selected_objects": trial['target_indices'] + non_targets[:1], "response_time": 1.5}
    )
    message = MultipleObjectTrackingTask.get_feedback_message(results)
    print(f"All targets + FP: {message}")
    assert "found all" in message.lower()
    
    print("✓ Feedback messages generated correctly\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("MULTIPLE OBJECT TRACKING TASK - TEST SUITE")
    print("="*60)
    
    try:
        test_trial_generation()
        test_perfect_response()
        test_partial_response()
        test_false_alarms()
        test_poor_response()
        test_difficulty_adaptation()
        test_tracking_metrics()
        test_feedback_messages()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED")
        print("="*60 + "\n")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}\n")
        raise
    except Exception as e:
        print(f"\n✗ ERROR: {e}\n")
        raise

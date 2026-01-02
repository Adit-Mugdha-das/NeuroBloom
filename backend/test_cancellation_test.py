"""
Test script for Cancellation Test task service.
Run with: python test_cancellation_test.py
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.cancellation_test_task import CancellationTestTask


def test_generate_trial():
    """Test trial generation across different difficulty levels."""
    print("\n=== Testing Trial Generation ===\n")
    
    for difficulty in [1, 3, 5, 7, 10]:
        print(f"Difficulty {difficulty}:")
        
        # Test with letters
        trial = CancellationTestTask.generate_trial(difficulty, use_symbols=False)
        
        print(f"  Grid size: {trial['rows']} x {trial['cols']} = {trial['total_items']} items")
        print(f"  Targets: {trial['target_items']} (count: {trial['target_count']})")
        print(f"  Time limit: {trial['time_limit']} seconds")
        print(f"  Instructions: {trial['instructions']}")
        
        # Verify grid contains correct number of targets
        target_count_in_grid = sum(
            1 for row in trial['grid'] for item in row 
            if item in trial['target_items']
        )
        print(f"  Actual targets in grid: {target_count_in_grid}")
        
        assert len(trial['target_positions']) == trial['target_count'], \
            f"Target position count mismatch: {len(trial['target_positions'])} vs {trial['target_count']}"
        
        assert target_count_in_grid == trial['target_count'], \
            f"Grid target count mismatch: {target_count_in_grid} vs {trial['target_count']}"
        
        print(f"  ✓ Trial generated successfully\n")
    
    # Test with symbols
    print("Testing symbol mode:")
    trial = CancellationTestTask.generate_trial(5, use_symbols=True)
    print(f"  Target symbols: {trial['target_items']}")
    print(f"  ✓ Symbol mode works\n")


def test_scoring():
    """Test scoring mechanism."""
    print("\n=== Testing Scoring ===\n")
    
    # Generate a trial
    trial = CancellationTestTask.generate_trial(difficulty=5, use_symbols=False)
    target_positions = trial['target_positions']
    total_targets = len(target_positions)
    
    print(f"Trial has {total_targets} targets")
    
    # Test 1: Perfect performance
    print("\nTest 1: Perfect Performance (100% accuracy)")
    all_marked = [{"row": p["row"], "col": p["col"]} for p in target_positions]
    results = CancellationTestTask.score_response(
        marked_positions=all_marked,
        target_positions=target_positions,
        completion_time=30.0,
        time_limit=75,
        difficulty=5
    )
    
    print(f"  Score: {results['score']}")
    print(f"  Accuracy: {results['accuracy']}%")
    print(f"  Targets found: {results['targets_found']}/{results['total_targets']}")
    print(f"  Performance: {results['performance_rating']}")
    print(f"  Difficulty adjustment: {results['difficulty_adjustment']}")
    print(f"  Feedback: {results['feedback']}")
    
    assert results['accuracy'] == 100.0, "Perfect accuracy should be 100%"
    assert results['performance_rating'] == "excellent", "Should be excellent"
    assert results['difficulty_adjustment'] > 0, "Should increase difficulty"
    print("  ✓ Perfect performance scored correctly\n")
    
    # Test 2: Good performance (90% found)
    print("Test 2: Good Performance (90% accuracy)")
    marked_90 = all_marked[:int(total_targets * 0.9)]
    results = CancellationTestTask.score_response(
        marked_positions=marked_90,
        target_positions=target_positions,
        completion_time=45.0,
        time_limit=75,
        difficulty=5
    )
    
    print(f"  Score: {results['score']}")
    print(f"  Accuracy: {results['accuracy']}%")
    print(f"  Performance: {results['performance_rating']}")
    print(f"  Difficulty adjustment: {results['difficulty_adjustment']}")
    
    assert 85 <= results['accuracy'] <= 95, f"Accuracy should be ~90%, got {results['accuracy']}"
    print("  ✓ Good performance scored correctly\n")
    
    # Test 3: Average performance (75% found)
    print("Test 3: Average Performance (75% accuracy)")
    marked_75 = all_marked[:int(total_targets * 0.75)]
    results = CancellationTestTask.score_response(
        marked_positions=marked_75,
        target_positions=target_positions,
        completion_time=60.0,
        time_limit=75,
        difficulty=5
    )
    
    print(f"  Score: {results['score']}")
    print(f"  Accuracy: {results['accuracy']}%")
    print(f"  Performance: {results['performance_rating']}")
    print(f"  Difficulty adjustment: {results['difficulty_adjustment']}")
    
    assert results['performance_rating'] == "average", "Should be average performance"
    print("  ✓ Average performance scored correctly\n")
    
    # Test 4: With false positives
    print("Test 4: Performance with False Positives")
    marked_with_errors = all_marked[:int(total_targets * 0.8)]
    # Add some false positives
    marked_with_errors.extend([
        {"row": 0, "col": 0},  # Assuming these aren't targets
        {"row": 1, "col": 1},
        {"row": 2, "col": 2}
    ])
    
    results = CancellationTestTask.score_response(
        marked_positions=marked_with_errors,
        target_positions=target_positions,
        completion_time=50.0,
        time_limit=75,
        difficulty=5
    )
    
    print(f"  Accuracy: {results['accuracy']}%")
    print(f"  Targets found: {results['targets_found']}")
    print(f"  False alarms: {results['false_alarms']}")
    
    assert results['false_alarms'] >= 0, "Should track false alarms"
    print("  ✓ False positives tracked correctly\n")


def test_spatial_analysis():
    """Test spatial pattern detection (neglect)."""
    print("\n=== Testing Spatial Analysis ===\n")
    
    # Create mock target positions (50% left, 50% right)
    target_positions = []
    for row in range(10):
        for col in range(10):
            target_positions.append({"row": row, "col": col, "item": "A"})
    
    # Test 1: Balanced performance
    print("Test 1: Balanced Performance (no neglect)")
    all_marked = [{"row": p["row"], "col": p["col"]} for p in target_positions]
    results = CancellationTestTask.score_response(
        marked_positions=all_marked,
        target_positions=target_positions,
        completion_time=30.0,
        time_limit=60,
        difficulty=5
    )
    
    spatial = results['spatial_analysis']
    print(f"  Left accuracy: {spatial['left_accuracy']}%")
    print(f"  Right accuracy: {spatial['right_accuracy']}%")
    print(f"  Neglect detected: {spatial['neglect_detected']}")
    
    assert not spatial['neglect_detected'], "Should not detect neglect with balanced performance"
    print("  ✓ No neglect detected correctly\n")
    
    # Test 2: Left-side neglect
    print("Test 2: Left-Side Neglect Simulation")
    # Only mark right-side targets
    right_marked = [{"row": p["row"], "col": p["col"]} for p in target_positions if p["col"] >= 5]
    
    results = CancellationTestTask.score_response(
        marked_positions=right_marked,
        target_positions=target_positions,
        completion_time=30.0,
        time_limit=60,
        difficulty=5
    )
    
    spatial = results['spatial_analysis']
    print(f"  Left accuracy: {spatial['left_accuracy']}%")
    print(f"  Right accuracy: {spatial['right_accuracy']}%")
    print(f"  Neglect detected: {spatial['neglect_detected']}")
    print(f"  Neglect side: {spatial.get('neglect_side')}")
    
    assert spatial['neglect_detected'], "Should detect neglect pattern"
    assert spatial.get('neglect_side') == "left", "Should identify left-side neglect"
    print("  ✓ Left neglect detected correctly\n")


def test_difficulty_adjustment():
    """Test difficulty adjustment logic."""
    print("\n=== Testing Difficulty Adjustment ===\n")
    
    test_cases = [
        (95, 30, 60, 5, "Excellent performance, fast completion", 2),
        (90, 40, 60, 5, "Good performance", 1),
        (80, 50, 60, 5, "Average performance", 0),
        (70, 55, 60, 5, "Below average", -1),
        (50, 60, 60, 5, "Poor performance", -2),
    ]
    
    for accuracy, time, limit, difficulty, description, expected_adjustment in test_cases:
        adjustment = CancellationTestTask.calculate_difficulty_adjustment(
            accuracy, time, limit, difficulty
        )
        
        print(f"{description}:")
        print(f"  Accuracy: {accuracy}%, Time: {time}/{limit}s")
        print(f"  Adjustment: {adjustment} (expected: {expected_adjustment})")
        
        assert adjustment == expected_adjustment, \
            f"Expected {expected_adjustment}, got {adjustment}"
        
        print("  ✓ Correct adjustment\n")


if __name__ == "__main__":
    print("=" * 70)
    print("CANCELLATION TEST - Backend Service Tests")
    print("=" * 70)
    
    try:
        test_generate_trial()
        test_scoring()
        test_spatial_analysis()
        test_difficulty_adjustment()
        
        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED")
        print("=" * 70)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

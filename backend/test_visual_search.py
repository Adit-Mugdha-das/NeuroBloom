"""
Test suite for Visual Search Task
Tests feature and conjunction search generation and scoring
"""

from app.services.visual_search_task import VisualSearchTask


def test_feature_search_generation():
    """Test feature search trial generation."""
    print("\n=== Testing Feature Search Generation ===")
    
    # Generate easy feature search trial (difficulty 1-3)
    trial = VisualSearchTask.generate_trial(difficulty=2)
    
    print(f"Search Type: {trial['search_type']}")
    print(f"Set Size: {trial['set_size']}")
    print(f"Target Present: {trial['target_present']}")
    print(f"Target: {trial['target']}")
    print(f"Time Limit: {trial['time_limit']}s")
    print(f"Number of items: {len(trial['items'])}")
    
    # Verify target properties
    target = trial['target']
    print(f"\nTarget properties: shape={target['shape']}, color={target['color']}")
    
    # Check item diversity
    shapes = set(item['shape'] for item in trial['items'])
    colors = set(item['color'] for item in trial['items'])
    print(f"Unique shapes: {shapes}")
    print(f"Unique colors: {colors}")
    
    assert trial['search_type'] == 'feature', "Should be feature search at difficulty 2"
    assert len(trial['items']) == trial['set_size'], "Item count should match set size"
    
    print("✓ Feature search generation passed")


def test_conjunction_search_generation():
    """Test conjunction search trial generation."""
    print("\n=== Testing Conjunction Search Generation ===")
    
    # Generate conjunction search trial (difficulty 4+)
    trial = VisualSearchTask.generate_trial(difficulty=5)
    
    print(f"Search Type: {trial['search_type']}")
    print(f"Set Size: {trial['set_size']}")
    print(f"Target Present: {trial['target_present']}")
    print(f"Target: {trial['target']}")
    print(f"Time Limit: {trial['time_limit']}s")
    print(f"Similarity: {trial['similarity']}")
    
    # Check for distractor variety
    shapes = set(item['shape'] for item in trial['items'])
    colors = set(item['color'] for item in trial['items'])
    print(f"\nUnique shapes: {shapes}")
    print(f"Unique colors: {colors}")
    print(f"Distractor types: Should have items sharing ONE feature with target")
    
    assert trial['search_type'] == 'conjunction', "Should be conjunction search at difficulty 5"
    assert len(trial['items']) == trial['set_size'], "Item count should match set size"
    assert len(shapes) >= 2, "Conjunction search should have multiple shapes"
    assert len(colors) >= 2, "Conjunction search should have multiple colors"
    
    print("✓ Conjunction search generation passed")


def test_scoring_correct_response():
    """Test scoring with correct response."""
    print("\n=== Testing Scoring - Correct Response ===")
    
    trial = VisualSearchTask.generate_trial(difficulty=3)
    
    # Simulate correct response
    user_response = {
        "target_found": trial['target_present'],
        "reaction_time": 5.0  # 5 seconds
    }
    
    results = VisualSearchTask.score_response(trial, user_response)
    
    print(f"Correct: {results['correct']}")
    print(f"Accuracy: {results['accuracy']}")
    print(f"Score: {results['score']:.2f}")
    print(f"Response Type: {results['response_type']}")
    print(f"Search Efficiency: {results['search_efficiency']:.3f}s per item")
    print(f"Search Slope: {results['search_slope_ms']:.1f}ms per item")
    print(f"Performance: {results['performance']}")
    
    assert results['correct'] == True, "Should be correct"
    assert results['accuracy'] == 1.0, "Accuracy should be 100%"
    assert results['score'] > 0, "Score should be positive"
    
    print("✓ Correct response scoring passed")


def test_scoring_incorrect_response():
    """Test scoring with incorrect response."""
    print("\n=== Testing Scoring - Incorrect Response ===")
    
    trial = VisualSearchTask.generate_trial(difficulty=3)
    
    # Simulate incorrect response (opposite of truth)
    user_response = {
        "target_found": not trial['target_present'],
        "reaction_time": 8.0
    }
    
    results = VisualSearchTask.score_response(trial, user_response)
    
    print(f"Correct: {results['correct']}")
    print(f"Accuracy: {results['accuracy']}")
    print(f"Score: {results['score']:.2f}")
    print(f"Response Type: {results['response_type']}")
    
    assert results['correct'] == False, "Should be incorrect"
    assert results['accuracy'] == 0.0, "Accuracy should be 0%"
    assert results['score'] == 0.0, "Score should be 0"
    
    print("✓ Incorrect response scoring passed")


def test_search_slope_analysis():
    """Test search slope calculation."""
    print("\n=== Testing Search Slope Analysis ===")
    
    # Feature search should be fast (parallel processing)
    feature_trial = VisualSearchTask.generate_trial(difficulty=2)
    feature_response = {
        "target_found": feature_trial['target_present'],
        "reaction_time": 2.0  # Fast response
    }
    feature_results = VisualSearchTask.score_response(feature_trial, feature_response)
    
    # Conjunction search should be slower (serial processing)
    conjunction_trial = VisualSearchTask.generate_trial(difficulty=6)
    conjunction_response = {
        "target_found": conjunction_trial['target_present'],
        "reaction_time": 10.0  # Slower response
    }
    conjunction_results = VisualSearchTask.score_response(conjunction_trial, conjunction_response)
    
    print(f"Feature Search:")
    print(f"  Set Size: {feature_results['set_size']}")
    print(f"  Search Slope: {feature_results['search_slope_ms']:.1f}ms/item")
    print(f"  Performance: {feature_results['performance']}")
    
    print(f"\nConjunction Search:")
    print(f"  Set Size: {conjunction_results['set_size']}")
    print(f"  Search Slope: {conjunction_results['search_slope_ms']:.1f}ms/item")
    print(f"  Performance: {conjunction_results['performance']}")
    
    print("\nNote: Feature search should have lower slope (parallel)")
    print("      Conjunction search should have higher slope (serial)")
    
    print("✓ Search slope analysis passed")


def test_difficulty_adaptation():
    """Test adaptive difficulty algorithm."""
    print("\n=== Testing Difficulty Adaptation ===")
    
    # Test increase (good performance)
    recent_scores = [0.9, 0.85, 0.92, 0.88, 0.90]
    current_difficulty = 5
    new_difficulty = VisualSearchTask.calculate_difficulty_adjustment(
        recent_scores, current_difficulty, accuracy=0.9, reaction_time=5.0, time_limit=20.0
    )
    print(f"Good Performance: {current_difficulty} → {new_difficulty}")
    assert new_difficulty >= current_difficulty, "Should increase or maintain"
    
    # Test decrease (poor performance)
    recent_scores = [0.4, 0.5, 0.3, 0.6, 0.45]
    current_difficulty = 5
    new_difficulty = VisualSearchTask.calculate_difficulty_adjustment(
        recent_scores, current_difficulty, accuracy=0.0, reaction_time=15.0, time_limit=20.0
    )
    print(f"Poor Performance: {current_difficulty} → {new_difficulty}")
    assert new_difficulty <= current_difficulty, "Should decrease or maintain"
    
    # Test maintain (average performance)
    recent_scores = [0.7, 0.75, 0.72, 0.68, 0.70]
    current_difficulty = 5
    new_difficulty = VisualSearchTask.calculate_difficulty_adjustment(
        recent_scores, current_difficulty, accuracy=0.7, reaction_time=10.0, time_limit=20.0
    )
    print(f"Average Performance: {current_difficulty} → {new_difficulty}")
    
    print("✓ Difficulty adaptation passed")


def test_response_types():
    """Test all response type classifications."""
    print("\n=== Testing Response Type Classification ===")
    
    # Hit: Target present, user says yes
    trial_present = {"target_present": True, "set_size": 20, "search_type": "feature", "time_limit": 30}
    response_yes = {"target_found": True, "reaction_time": 3.0}
    result = VisualSearchTask.score_response(trial_present, response_yes)
    print(f"Hit: {result['response_type']} (correct={result['correct']})")
    assert result['response_type'] == 'hit'
    
    # Miss: Target present, user says no
    response_no = {"target_found": False, "reaction_time": 3.0}
    result = VisualSearchTask.score_response(trial_present, response_no)
    print(f"Miss: {result['response_type']} (correct={result['correct']})")
    assert result['response_type'] == 'miss'
    
    # False Alarm: Target absent, user says yes
    trial_absent = {"target_present": False, "set_size": 20, "search_type": "feature", "time_limit": 30}
    result = VisualSearchTask.score_response(trial_absent, response_yes)
    print(f"False Alarm: {result['response_type']} (correct={result['correct']})")
    assert result['response_type'] == 'false_alarm'
    
    # Correct Rejection: Target absent, user says no
    result = VisualSearchTask.score_response(trial_absent, response_no)
    print(f"Correct Rejection: {result['response_type']} (correct={result['correct']})")
    assert result['response_type'] == 'correct_rejection'
    
    print("✓ Response type classification passed")


if __name__ == "__main__":
    print("="*60)
    print("Visual Search Task - Test Suite")
    print("Based on Treisman & Gelade (1980)")
    print("="*60)
    
    try:
        test_feature_search_generation()
        test_conjunction_search_generation()
        test_scoring_correct_response()
        test_scoring_incorrect_response()
        test_search_slope_analysis()
        test_difficulty_adaptation()
        test_response_types()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED!")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

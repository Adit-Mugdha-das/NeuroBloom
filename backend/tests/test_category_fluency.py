"""
Test script for Category Fluency task implementation
"""

from app.services.category_fluency_task import CategoryFluencyTask

def test_generate_trial():
    """Test trial generation at different difficulty levels"""
    print("=" * 60)
    print("Testing Trial Generation")
    print("=" * 60)
    
    for difficulty in [1, 3, 5, 7, 10]:
        trial = CategoryFluencyTask.generate_trial(difficulty)
        print(f"\nDifficulty {difficulty}:")
        print(f"  Category: {trial['category_name']}")
        print(f"  Description: {trial['description']}")
        print(f"  Examples: {', '.join(trial['examples'])}")
        print(f"  Time Limit: {trial['time_limit_seconds']}s")

def test_scoring():
    """Test scoring with different response scenarios"""
    print("\n" + "=" * 60)
    print("Testing Scoring")
    print("=" * 60)
    
    # Test Case 1: Good performance
    print("\n--- Test Case 1: Good Performance (18 unique words) ---")
    words_good = ["dog", "cat", "bird", "fish", "elephant", "lion", "tiger", "bear",
                  "horse", "cow", "pig", "sheep", "rabbit", "deer", "wolf", "fox",
                  "zebra", "giraffe"]
    result = CategoryFluencyTask.score_response(words_good, 55.0, 1)
    print(f"Unique Count: {result['unique_count']}")
    print(f"Score: {result['normalized_score']}")
    print(f"Performance: {result['performance_rating']}")
    print(f"Feedback: {result['feedback']}")
    
    # Test Case 2: With duplicates
    print("\n--- Test Case 2: With Duplicates ---")
    words_duplicates = ["apple", "banana", "orange", "apple", "grape", "BANANA", "cherry"]
    result = CategoryFluencyTask.score_response(words_duplicates, 30.0, 1)
    print(f"Total Submitted: {result['total_submitted']}")
    print(f"Unique Count: {result['unique_count']}")
    print(f"Duplicate Count: {result['duplicate_count']}")
    print(f"Feedback: {result['feedback']}")
    
    # Test Case 3: Below average
    print("\n--- Test Case 3: Below Average (4 words) ---")
    words_few = ["chair", "table", "sofa", "desk"]
    result = CategoryFluencyTask.score_response(words_few, 45.0, 7)
    print(f"Unique Count: {result['unique_count']}")
    print(f"Performance: {result['performance_rating']}")
    print(f"Feedback: {result['feedback']}")
    
    # Test Case 4: Excellent performance
    print("\n--- Test Case 4: Excellent Performance (25 words) ---")
    words_excellent = [f"word{i}" for i in range(25)]
    result = CategoryFluencyTask.score_response(words_excellent, 58.0, 5)
    print(f"Unique Count: {result['unique_count']}")
    print(f"Score: {result['normalized_score']}")
    print(f"Performance: {result['performance_rating']}")
    print(f"Should Advance: {result['should_advance']}")

def test_difficulty_adjustment():
    """Test difficulty adjustment algorithm"""
    print("\n" + "=" * 60)
    print("Testing Difficulty Adjustment")
    print("=" * 60)
    
    # Excellent performance - should advance by 2
    result_excellent = CategoryFluencyTask.score_response(
        ["word" + str(i) for i in range(22)], 60.0, 5
    )
    new_diff = CategoryFluencyTask.calculate_difficulty_adjustment(5, result_excellent)
    print(f"\nCurrent: 5, Unique Words: 22, New Difficulty: {new_diff} (Expected: 7)")
    
    # Good performance - should advance by 1
    result_good = CategoryFluencyTask.score_response(
        ["word" + str(i) for i in range(16)], 60.0, 3
    )
    new_diff = CategoryFluencyTask.calculate_difficulty_adjustment(3, result_good)
    print(f"Current: 3, Unique Words: 16, New Difficulty: {new_diff} (Expected: 4)")
    
    # Poor performance - should decrease by 1
    result_poor = CategoryFluencyTask.score_response(
        ["word" + str(i) for i in range(6)], 60.0, 5
    )
    new_diff = CategoryFluencyTask.calculate_difficulty_adjustment(5, result_poor)
    print(f"Current: 5, Unique Words: 6, New Difficulty: {new_diff} (Expected: 4)")
    
    # Average performance - should stay same
    result_avg = CategoryFluencyTask.score_response(
        ["word" + str(i) for i in range(12)], 60.0, 5
    )
    new_diff = CategoryFluencyTask.calculate_difficulty_adjustment(5, result_avg)
    print(f"Current: 5, Unique Words: 12, New Difficulty: {new_diff} (Expected: 5)")

def test_word_validation():
    """Test word normalization and validation"""
    print("\n" + "=" * 60)
    print("Testing Word Validation")
    print("=" * 60)
    
    test_words = [
        "Apple",
        "BANANA",
        "  orange  ",
        "grape-fruit",
        "",
        "   ",
        "123",
        "apple2"
    ]
    
    print("\nWord Validation Results:")
    for word in test_words:
        is_valid = CategoryFluencyTask.is_valid_word(word)
        normalized = CategoryFluencyTask.normalize_word(word) if is_valid else "N/A"
        print(f"  '{word}' -> Valid: {is_valid}, Normalized: '{normalized}'")

if __name__ == "__main__":
    test_generate_trial()
    test_scoring()
    test_difficulty_adjustment()
    test_word_validation()
    
    print("\n" + "=" * 60)
    print("✓ All tests completed successfully!")
    print("=" * 60)

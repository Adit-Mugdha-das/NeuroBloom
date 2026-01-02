"""
Test script for Twenty Questions task implementation
"""

from app.services.twenty_questions_task import TwentyQuestionsTask

def test_generate_game():
    """Test game generation at different difficulty levels"""
    print("=" * 60)
    print("Testing Game Generation")
    print("=" * 60)
    
    for difficulty in [1, 2, 3, 4, 5]:
        game = TwentyQuestionsTask.generate_game(difficulty)
        print(f"\nDifficulty {difficulty}:")
        print(f"  Category: {game['category']}")
        print(f"  Target: {game['target_object_name']}")
        print(f"  Pool Size: {game['pool_size']}")
        print(f"  Max Questions: {game['max_questions']}")
        print(f"  Attributes: {list(game['target_attributes'].keys())[:5]}...")

def test_answer_question():
    """Test question answering logic"""
    print("\n" + "=" * 60)
    print("Testing Question Answering")
    print("=" * 60)
    
    # Generate a game with a dog
    game = TwentyQuestionsTask.generate_game(1)
    target_attributes = game['target_attributes']
    target_name = game['target_object_name']
    
    print(f"\nTarget Object: {target_name}")
    print(f"Attributes: {target_attributes}")
    
    # Test various questions
    test_questions = [
        "Is it an animal?",
        "Does it have fur?",
        "Can it fly?",
        "Does it live in water?",
        "Is it a pet?",
        "Does it have four legs?",
        "Is it a mammal?"
    ]
    
    print("\nAsking questions:")
    for question in test_questions:
        answer = TwentyQuestionsTask.answer_question(question, target_attributes)
        print(f"  Q: {question}")
        print(f"  A: {answer['answer']} (confidence: {answer['confidence']})")

def test_scoring():
    """Test scoring with different performance scenarios"""
    print("\n" + "=" * 60)
    print("Testing Scoring")
    print("=" * 60)
    
    # Test Case 1: Excellent performance (7 questions, correct)
    print("\n--- Test Case 1: Excellent Performance (7 questions, correct) ---")
    questions_history = [
        {"question": "Is it an animal?", "answer": "yes"},
        {"question": "Does it have fur?", "answer": "yes"},
        {"question": "Is it a pet?", "answer": "yes"},
        {"question": "Does it have four legs?", "answer": "yes"},
        {"question": "Does it bark?", "answer": "yes"},
        {"question": "Is it a dog?", "answer": "yes"},
        {"question": "Confirmed: Dog", "answer": "correct"}
    ]
    result = TwentyQuestionsTask.score_game(7, True, 1, questions_history)
    print(f"Score: {result['normalized_score']}")
    print(f"Performance: {result['performance_rating']}")
    print(f"Strategy Score: {result['strategy_score']}")
    print(f"Feedback: {result['feedback']}")
    print(f"Tips: {result['tips']}")
    
    # Test Case 2: Good performance (12 questions, correct)
    print("\n--- Test Case 2: Good Performance (12 questions, correct) ---")
    questions_history_2 = [{"question": f"Question {i}", "answer": "yes"} for i in range(12)]
    result = TwentyQuestionsTask.score_game(12, True, 1, questions_history_2)
    print(f"Score: {result['normalized_score']}")
    print(f"Performance: {result['performance_rating']}")
    
    # Test Case 3: Poor performance (19 questions, correct)
    print("\n--- Test Case 3: Below Average (19 questions, correct) ---")
    questions_history_3 = [{"question": f"Is it a {animal}?", "answer": "no"} for animal in ["cat", "bird", "fish", "horse", "rabbit", "chicken", "cow", "duck", "frog", "elephant", "lion", "tiger", "bear", "monkey", "snake", "turtle", "penguin", "dolphin", "dog"]]
    result = TwentyQuestionsTask.score_game(19, True, 1, questions_history_3)
    print(f"Score: {result['normalized_score']}")
    print(f"Performance: {result['performance_rating']}")
    print(f"Strategy Score: {result['strategy_score']}")
    print(f"Specific Guesses: {result['specific_guesses']}")
    
    # Test Case 4: Failed to identify
    print("\n--- Test Case 4: Failed to Identify (20 questions, wrong) ---")
    result = TwentyQuestionsTask.score_game(20, False, 1, questions_history_3)
    print(f"Score: {result['normalized_score']}")
    print(f"Performance: {result['performance_rating']}")
    print(f"Feedback: {result['feedback']}")

def test_difficulty_adjustment():
    """Test difficulty adjustment algorithm"""
    print("\n" + "=" * 60)
    print("Testing Difficulty Adjustment")
    print("=" * 60)
    
    # Excellent performance - should advance by 2
    result_excellent = TwentyQuestionsTask.score_game(6, True, 5, [])
    new_diff = TwentyQuestionsTask.calculate_difficulty_adjustment(5, result_excellent)
    print(f"\nCurrent: 5, Questions: 6, Correct: Yes, New Difficulty: {new_diff} (Expected: 7)")
    
    # Good performance - should advance by 1
    result_good = TwentyQuestionsTask.score_game(11, True, 3, [])
    new_diff = TwentyQuestionsTask.calculate_difficulty_adjustment(3, result_good)
    print(f"Current: 3, Questions: 11, Correct: Yes, New Difficulty: {new_diff} (Expected: 4)")
    
    # Poor performance - should decrease by 1
    result_poor = TwentyQuestionsTask.score_game(18, True, 5, [])
    new_diff = TwentyQuestionsTask.calculate_difficulty_adjustment(5, result_poor)
    print(f"Current: 5, Questions: 18, Correct: Yes, New Difficulty: {new_diff} (Expected: 4)")
    
    # Failed - should decrease by 1
    result_failed = TwentyQuestionsTask.score_game(15, False, 5, [])
    new_diff = TwentyQuestionsTask.calculate_difficulty_adjustment(5, result_failed)
    print(f"Current: 5, Questions: 15, Correct: No, New Difficulty: {new_diff} (Expected: 4)")
    
    # Average performance - should stay same
    result_avg = TwentyQuestionsTask.score_game(14, True, 5, [])
    new_diff = TwentyQuestionsTask.calculate_difficulty_adjustment(5, result_avg)
    print(f"Current: 5, Questions: 14, Correct: Yes, New Difficulty: {new_diff} (Expected: 5)")

if __name__ == "__main__":
    test_generate_game()
    test_answer_question()
    test_scoring()
    test_difficulty_adjustment()
    
    print("\n" + "=" * 60)
    print("✓ All tests completed successfully!")
    print("=" * 60)

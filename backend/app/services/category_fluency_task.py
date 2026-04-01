"""
Category Fluency (Semantic Fluency) Task Service

Clinical Validation: Complement to phonemic fluency
Description: Generate items from category (animals, fruits, tools) in 60s

MS Research Evidence:
- Semantic memory + executive function
- Different neural systems than phonemic
- Reference: Henry & Crawford, 2004
"""

from typing import Dict, Any, List
from datetime import datetime
import re


class CategoryFluencyTask:
    """
    Category Fluency task implementation for semantic memory and executive function assessment.
    Users generate words from a given category in 60 seconds.
    """
    
    # Category pools by difficulty level
    CATEGORIES = {
        1: {  # Easy
            "animals": {
                "name": "Animals",
                "examples": ["dog", "cat", "bird", "fish"],
                "description": "Name as many animals as you can"
            },
            "foods": {
                "name": "Foods",
                "examples": ["apple", "bread", "rice", "chicken"],
                "description": "Name as many foods as you can"
            },
            "colors": {
                "name": "Colors",
                "examples": ["red", "blue", "green", "yellow"],
                "description": "Name as many colors as you can"
            }
        },
        2: {  # Easy-Medium
            "animals": {
                "name": "Animals",
                "examples": ["dog", "cat", "bird", "fish"],
                "description": "Name as many animals as you can"
            },
            "foods": {
                "name": "Foods",
                "examples": ["apple", "bread", "rice", "chicken"],
                "description": "Name as many foods as you can"
            }
        },
        3: {  # Medium-Easy
            "fruits": {
                "name": "Fruits",
                "examples": ["apple", "banana", "orange", "grape"],
                "description": "Name as many fruits as you can"
            },
            "colors": {
                "name": "Colors",
                "examples": ["red", "blue", "green", "yellow"],
                "description": "Name as many colors as you can"
            }
        },
        4: {  # Medium
            "fruits": {
                "name": "Fruits",
                "examples": ["apple", "banana", "orange", "grape"],
                "description": "Name as many fruits as you can"
            },
            "sports": {
                "name": "Sports",
                "examples": ["soccer", "basketball", "tennis", "swimming"],
                "description": "Name as many sports as you can"
            }
        },
        5: {  # Medium
            "sports": {
                "name": "Sports",
                "examples": ["soccer", "basketball", "tennis", "swimming"],
                "description": "Name as many sports as you can"
            },
            "occupations": {
                "name": "Occupations",
                "examples": ["doctor", "teacher", "engineer", "chef"],
                "description": "Name as many occupations as you can"
            }
        },
        6: {  # Medium-Hard
            "occupations": {
                "name": "Occupations",
                "examples": ["doctor", "teacher", "engineer", "chef"],
                "description": "Name as many occupations as you can"
            },
            "furniture": {
                "name": "Furniture",
                "examples": ["chair", "table", "sofa", "desk"],
                "description": "Name as many pieces of furniture as you can"
            }
        },
        7: {  # Hard
            "furniture": {
                "name": "Furniture",
                "examples": ["chair", "table", "sofa", "desk"],
                "description": "Name as many pieces of furniture as you can"
            },
            "vegetables": {
                "name": "Vegetables",
                "examples": ["carrot", "broccoli", "tomato", "lettuce"],
                "description": "Name as many vegetables as you can"
            }
        },
        8: {  # Hard
            "vegetables": {
                "name": "Vegetables",
                "examples": ["carrot", "broccoli", "tomato", "lettuce"],
                "description": "Name as many vegetables as you can"
            },
            "instruments": {
                "name": "Musical Instruments",
                "examples": ["piano", "guitar", "violin", "drums"],
                "description": "Name as many musical instruments as you can"
            }
        },
        9: {  # Expert
            "instruments": {
                "name": "Musical Instruments",
                "examples": ["piano", "guitar", "violin", "drums"],
                "description": "Name as many musical instruments as you can"
            },
            "soft_things": {
                "name": "Things That Are Soft",
                "examples": ["pillow", "cotton", "feather", "blanket"],
                "description": "Name as many things that are soft as you can"
            }
        },
        10: {  # Expert
            "soft_things": {
                "name": "Things That Are Soft",
                "examples": ["pillow", "cotton", "feather", "blanket"],
                "description": "Name as many things that are soft as you can"
            },
            "office_items": {
                "name": "Items in an Office",
                "examples": ["desk", "computer", "stapler", "phone"],
                "description": "Name as many items you would find in an office as you can"
            }
        }
    }
    
    # Performance benchmarks (number of unique words)
    PERFORMANCE_BENCHMARKS = {
        "excellent": 20,      # 20+ words = excellent
        "good": 15,           # 15-19 words = good
        "average": 10,        # 10-14 words = average
        "below_average": 5    # 5-9 words = below average
    }
    
    @staticmethod
    def generate_trial(difficulty: int) -> Dict[str, Any]:
        """
        Generate a category fluency trial based on difficulty level.
        
        Args:
            difficulty: Difficulty level (1-10)
            
        Returns:
            Trial configuration with category and instructions
        """
        difficulty = max(1, min(10, difficulty))
        
        # Get available categories for this difficulty
        categories = CategoryFluencyTask.CATEGORIES.get(difficulty, CategoryFluencyTask.CATEGORIES[5])
        
        # Select a category (can be randomized or rotated)
        import random
        category_key = random.choice(list(categories.keys()))
        category_data = categories[category_key]
        
        return {
            "difficulty": difficulty,
            "category_key": category_key,
            "category_name": category_data["name"],
            "description": category_data["description"],
            "examples": category_data["examples"][:2],  # Show 2 examples
            "time_limit_seconds": 60,
            "instructions": f"You have 60 seconds to name as many {category_data['name'].lower()} as you can. Type each word and press Enter to submit it."
        }
    
    @staticmethod
    def normalize_word(word: str) -> str:
        """
        Normalize a word for comparison (lowercase, strip whitespace).
        
        Args:
            word: The word to normalize
            
        Returns:
            Normalized word
        """
        return word.strip().lower()
    
    @staticmethod
    def is_valid_word(word: str) -> bool:
        """
        Check if a word is valid (not empty, contains letters).
        
        Args:
            word: The word to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not word or len(word.strip()) == 0:
            return False

        # Accept alphabetic input across scripts so Bangla responses work too.
        return any(char.isalpha() for char in word.strip())
    
    @staticmethod
    def score_response(submitted_words: List[str], time_taken_seconds: float, difficulty: int) -> Dict[str, Any]:
        """
        Score the user's response for category fluency task.
        
        Args:
            submitted_words: List of words submitted by the user
            time_taken_seconds: Time taken to complete (up to 60s)
            difficulty: Difficulty level (1-10)
            
        Returns:
            Scoring results including unique count, duplicates, and performance metrics
        """
        # Normalize and validate words
        normalized_words = []
        invalid_words = []
        
        for word in submitted_words:
            if CategoryFluencyTask.is_valid_word(word):
                normalized_words.append(CategoryFluencyTask.normalize_word(word))
            else:
                invalid_words.append(word)
        
        # Count unique words
        unique_words = list(set(normalized_words))
        unique_count = len(unique_words)
        
        # Count duplicates
        duplicate_count = len(normalized_words) - unique_count
        
        # Calculate raw score (unique words only)
        raw_score = unique_count
        
        # Performance rating
        performance_rating = "below_average"
        if unique_count >= CategoryFluencyTask.PERFORMANCE_BENCHMARKS["excellent"]:
            performance_rating = "excellent"
        elif unique_count >= CategoryFluencyTask.PERFORMANCE_BENCHMARKS["good"]:
            performance_rating = "good"
        elif unique_count >= CategoryFluencyTask.PERFORMANCE_BENCHMARKS["average"]:
            performance_rating = "average"
        
        # Calculate normalized score (0-100 scale)
        # Scale based on difficulty and performance
        max_expected = CategoryFluencyTask.PERFORMANCE_BENCHMARKS["excellent"] + (difficulty * 2)
        normalized_score = min(100, (unique_count / max_expected) * 100)
        
        # Calculate words per second rate
        words_per_second = unique_count / max(1, time_taken_seconds)
        
        # Determine if user should advance
        advance_threshold = 15  # Need 15+ unique words to advance
        should_advance = unique_count >= advance_threshold and difficulty < 10
        
        return {
            "raw_score": raw_score,
            "normalized_score": round(normalized_score, 2),
            "unique_count": unique_count,
            "total_submitted": len(submitted_words),
            "duplicate_count": duplicate_count,
            "invalid_count": len(invalid_words),
            "performance_rating": performance_rating,
            "words_per_second": round(words_per_second, 2),
            "time_taken_seconds": round(time_taken_seconds, 2),
            "should_advance": should_advance,
            "feedback": CategoryFluencyTask._generate_feedback(
                unique_count, duplicate_count, performance_rating, difficulty
            ),
            "submitted_words": submitted_words,
            "unique_words": unique_words,
            "invalid_words": invalid_words
        }
    
    @staticmethod
    def _generate_feedback(unique_count: int, duplicate_count: int, 
                          performance_rating: str, difficulty: int) -> str:
        """
        Generate performance feedback for the user.
        
        Args:
            unique_count: Number of unique words
            duplicate_count: Number of duplicate words
            performance_rating: Performance rating
            difficulty: Difficulty level
            
        Returns:
            Feedback message
        """
        feedback_parts = []
        
        # Performance feedback
        if performance_rating == "excellent":
            feedback_parts.append(f"Excellent! You generated {unique_count} unique words.")
        elif performance_rating == "good":
            feedback_parts.append(f"Good work! You generated {unique_count} unique words.")
        elif performance_rating == "average":
            feedback_parts.append(f"You generated {unique_count} unique words.")
        else:
            feedback_parts.append(f"You generated {unique_count} unique words. Try to think of more items next time.")
        
        # Duplicate feedback
        if duplicate_count > 0:
            feedback_parts.append(f"Note: {duplicate_count} duplicate word(s) were not counted.")
        
        # Strategy tips based on performance
        if unique_count < 10:
            feedback_parts.append("Tip: Try thinking of subcategories (e.g., farm animals, pets, wild animals).")
        
        return " ".join(feedback_parts)
    
    @staticmethod
    def calculate_difficulty_adjustment(current_difficulty: int, performance: Dict[str, Any]) -> int:
        """
        Calculate the next difficulty level based on performance.
        
        Args:
            current_difficulty: Current difficulty level (1-10)
            performance: Performance metrics from score_response
            
        Returns:
            Next difficulty level (1-10)
        """
        unique_count = performance["unique_count"]
        
        # Advancement criteria
        if unique_count >= 20 and current_difficulty < 10:
            # Excellent performance - increase by 2
            return min(10, current_difficulty + 2)
        elif unique_count >= 15 and current_difficulty < 10:
            # Good performance - increase by 1
            return min(10, current_difficulty + 1)
        elif unique_count < 8 and current_difficulty > 1:
            # Below average - decrease by 1
            return max(1, current_difficulty - 1)
        else:
            # Maintain current difficulty
            return current_difficulty

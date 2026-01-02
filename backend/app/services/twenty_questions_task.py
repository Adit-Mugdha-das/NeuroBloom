"""
Twenty Questions Task Service

Clinical Validation: Strategic problem-solving
Description: Identify hidden object using minimum yes/no questions

MS Research Evidence:
- Strategy formation
- Hypothesis testing
- Reference: Mosher & Hornsby, 1966
"""

from typing import Dict, Any, List, Optional
import random


class TwentyQuestionsTask:
    """
    Twenty Questions task implementation for strategic problem-solving assessment.
    User asks yes/no questions to identify a hidden object.
    """
    
    # Object pools organized by difficulty level with attributes
    OBJECT_POOLS = {
        1: {  # Easy - Small pool (10 common animals)
            "category": "Common Animals",
            "objects": [
                {
                    "name": "Dog",
                    "attributes": {
                        "is_animal": True,
                        "has_fur": True,
                        "has_four_legs": True,
                        "is_pet": True,
                        "can_fly": False,
                        "lives_in_water": False,
                        "is_mammal": True,
                        "is_domesticated": True,
                        "barks": True
                    }
                },
                {
                    "name": "Cat",
                    "attributes": {
                        "is_animal": True,
                        "has_fur": True,
                        "has_four_legs": True,
                        "is_pet": True,
                        "can_fly": False,
                        "lives_in_water": False,
                        "is_mammal": True,
                        "is_domesticated": True,
                        "meows": True
                    }
                },
                {
                    "name": "Bird",
                    "attributes": {
                        "is_animal": True,
                        "has_fur": False,
                        "has_feathers": True,
                        "has_four_legs": False,
                        "can_fly": True,
                        "lives_in_water": False,
                        "is_mammal": False,
                        "lays_eggs": True
                    }
                },
                {
                    "name": "Fish",
                    "attributes": {
                        "is_animal": True,
                        "has_fur": False,
                        "has_scales": True,
                        "has_four_legs": False,
                        "can_fly": False,
                        "lives_in_water": True,
                        "is_mammal": False,
                        "has_gills": True
                    }
                },
                {
                    "name": "Horse",
                    "attributes": {
                        "is_animal": True,
                        "has_fur": True,
                        "has_four_legs": True,
                        "is_pet": False,
                        "can_fly": False,
                        "lives_in_water": False,
                        "is_mammal": True,
                        "is_large": True,
                        "can_be_ridden": True
                    }
                },
                {
                    "name": "Rabbit",
                    "attributes": {
                        "is_animal": True,
                        "has_fur": True,
                        "has_four_legs": True,
                        "is_pet": True,
                        "can_fly": False,
                        "lives_in_water": False,
                        "is_mammal": True,
                        "hops": True,
                        "has_long_ears": True
                    }
                },
                {
                    "name": "Chicken",
                    "attributes": {
                        "is_animal": True,
                        "has_fur": False,
                        "has_feathers": True,
                        "has_four_legs": False,
                        "can_fly": False,
                        "lives_in_water": False,
                        "is_mammal": False,
                        "lays_eggs": True,
                        "is_farm_animal": True
                    }
                },
                {
                    "name": "Cow",
                    "attributes": {
                        "is_animal": True,
                        "has_fur": True,
                        "has_four_legs": True,
                        "is_pet": False,
                        "can_fly": False,
                        "lives_in_water": False,
                        "is_mammal": True,
                        "is_large": True,
                        "is_farm_animal": True,
                        "produces_milk": True
                    }
                },
                {
                    "name": "Duck",
                    "attributes": {
                        "is_animal": True,
                        "has_fur": False,
                        "has_feathers": True,
                        "has_four_legs": False,
                        "can_fly": True,
                        "lives_in_water": True,
                        "is_mammal": False,
                        "lays_eggs": True,
                        "quacks": True
                    }
                },
                {
                    "name": "Frog",
                    "attributes": {
                        "is_animal": True,
                        "has_fur": False,
                        "has_four_legs": True,
                        "can_fly": False,
                        "lives_in_water": True,
                        "is_mammal": False,
                        "is_amphibian": True,
                        "can_jump": True,
                        "croaks": True
                    }
                }
            ]
        },
        2: {  # Easy-Medium (15 animals)
            "category": "Animals",
            "objects": [
                # Include all from level 1 plus more
                {"name": "Dog", "attributes": {"is_animal": True, "has_fur": True, "has_four_legs": True, "is_pet": True, "can_fly": False, "lives_in_water": False, "is_mammal": True}},
                {"name": "Cat", "attributes": {"is_animal": True, "has_fur": True, "has_four_legs": True, "is_pet": True, "can_fly": False, "lives_in_water": False, "is_mammal": True}},
                {"name": "Bird", "attributes": {"is_animal": True, "has_feathers": True, "can_fly": True, "is_mammal": False, "lays_eggs": True}},
                {"name": "Fish", "attributes": {"is_animal": True, "has_scales": True, "lives_in_water": True, "is_mammal": False, "has_gills": True}},
                {"name": "Horse", "attributes": {"is_animal": True, "has_fur": True, "has_four_legs": True, "is_mammal": True, "is_large": True}},
                {"name": "Elephant", "attributes": {"is_animal": True, "has_fur": False, "has_four_legs": True, "is_mammal": True, "is_large": True, "has_trunk": True}},
                {"name": "Lion", "attributes": {"is_animal": True, "has_fur": True, "has_four_legs": True, "is_mammal": True, "is_wild": True, "is_carnivore": True}},
                {"name": "Tiger", "attributes": {"is_animal": True, "has_fur": True, "has_four_legs": True, "is_mammal": True, "is_wild": True, "has_stripes": True}},
                {"name": "Bear", "attributes": {"is_animal": True, "has_fur": True, "has_four_legs": True, "is_mammal": True, "is_large": True, "is_wild": True}},
                {"name": "Monkey", "attributes": {"is_animal": True, "has_fur": True, "is_mammal": True, "can_climb": True, "has_tail": True, "is_intelligent": True}},
                {"name": "Snake", "attributes": {"is_animal": True, "has_scales": True, "has_no_legs": True, "is_reptile": True, "is_long": True}},
                {"name": "Turtle", "attributes": {"is_animal": True, "has_shell": True, "has_four_legs": True, "is_reptile": True, "is_slow": True}},
                {"name": "Penguin", "attributes": {"is_animal": True, "has_feathers": True, "can_fly": False, "lives_in_cold": True, "can_swim": True}},
                {"name": "Dolphin", "attributes": {"is_animal": True, "lives_in_water": True, "is_mammal": True, "is_intelligent": True, "can_swim": True}},
                {"name": "Shark", "attributes": {"is_animal": True, "lives_in_water": True, "is_fish": True, "is_carnivore": True, "has_teeth": True}}
            ]
        },
        3: {  # Medium (20 objects - mixed animals and common items)
            "category": "Animals and Objects",
            "objects": [
                {"name": "Dog", "attributes": {"is_animal": True, "is_living": True, "has_fur": True, "is_pet": True}},
                {"name": "Cat", "attributes": {"is_animal": True, "is_living": True, "has_fur": True, "is_pet": True}},
                {"name": "Chair", "attributes": {"is_furniture": True, "is_living": False, "is_used_for_sitting": True}},
                {"name": "Table", "attributes": {"is_furniture": True, "is_living": False, "has_flat_surface": True}},
                {"name": "Car", "attributes": {"is_vehicle": True, "is_living": False, "has_wheels": True, "is_transportation": True}},
                {"name": "Tree", "attributes": {"is_plant": True, "is_living": True, "is_large": True, "has_leaves": True}},
                {"name": "Book", "attributes": {"is_object": True, "is_living": False, "is_for_reading": True, "has_pages": True}},
                {"name": "Phone", "attributes": {"is_electronic": True, "is_living": False, "is_communication_device": True}},
                {"name": "Apple", "attributes": {"is_food": True, "is_living": True, "is_fruit": True, "is_edible": True}},
                {"name": "Bird", "attributes": {"is_animal": True, "is_living": True, "can_fly": True, "has_feathers": True}},
                {"name": "Fish", "attributes": {"is_animal": True, "is_living": True, "lives_in_water": True, "has_scales": True}},
                {"name": "Bicycle", "attributes": {"is_vehicle": True, "is_living": False, "has_wheels": True, "requires_pedaling": True}},
                {"name": "Computer", "attributes": {"is_electronic": True, "is_living": False, "is_machine": True, "has_screen": True}},
                {"name": "Flower", "attributes": {"is_plant": True, "is_living": True, "is_beautiful": True, "has_petals": True}},
                {"name": "Ball", "attributes": {"is_toy": True, "is_living": False, "is_round": True, "is_used_in_sports": True}},
                {"name": "Shoe", "attributes": {"is_clothing": True, "is_living": False, "is_worn_on_feet": True}},
                {"name": "Pen", "attributes": {"is_tool": True, "is_living": False, "is_for_writing": True}},
                {"name": "Cup", "attributes": {"is_container": True, "is_living": False, "holds_liquid": True}},
                {"name": "Clock", "attributes": {"is_object": True, "is_living": False, "tells_time": True, "has_numbers": True}},
                {"name": "Guitar", "attributes": {"is_instrument": True, "is_living": False, "makes_music": True, "has_strings": True}}
            ]
        },
        4: {  # Medium (25 diverse objects)
            "category": "Various Objects",
            "objects": [
                {"name": "Airplane", "attributes": {"is_vehicle": True, "can_fly": True, "is_large": True}},
                {"name": "Boat", "attributes": {"is_vehicle": True, "floats_on_water": True, "is_transportation": True}},
                {"name": "Mountain", "attributes": {"is_natural": True, "is_large": True, "is_tall": True}},
                {"name": "Ocean", "attributes": {"is_natural": True, "is_large": True, "contains_water": True}},
                {"name": "Sun", "attributes": {"is_celestial": True, "is_hot": True, "gives_light": True}},
                # ... add 20 more diverse objects
                {"name": "Piano", "attributes": {"is_instrument": True, "makes_music": True, "has_keys": True}},
                {"name": "Camera", "attributes": {"is_electronic": True, "takes_pictures": True}},
                {"name": "Television", "attributes": {"is_electronic": True, "has_screen": True, "shows_images": True}},
                {"name": "Refrigerator", "attributes": {"is_appliance": True, "keeps_food_cold": True, "is_large": True}},
                {"name": "Lamp", "attributes": {"is_object": True, "gives_light": True, "is_electric": True}}
            ]
        },
        5: {  # Medium-Hard (30 objects - abstract concepts starting to appear)
            "category": "Objects and Concepts",
            "objects": [
                {"name": "Love", "attributes": {"is_emotion": True, "is_abstract": True, "is_positive": True}},
                {"name": "Freedom", "attributes": {"is_concept": True, "is_abstract": True, "is_valuable": True}},
                {"name": "Time", "attributes": {"is_concept": True, "is_abstract": True, "is_measurable": True}},
                # Mix of concrete and abstract
                {"name": "Diamond", "attributes": {"is_object": True, "is_valuable": True, "is_hard": True, "is_shiny": True}},
                {"name": "Thunder", "attributes": {"is_natural": True, "makes_sound": True, "happens_in_storms": True}}
                # ... add 25 more objects
            ]
        }
    }
    
    # Performance benchmarks (number of questions used)
    PERFORMANCE_BENCHMARKS = {
        "excellent": 7,       # 7 or fewer questions = excellent
        "good": 12,           # 8-12 questions = good
        "average": 17,        # 13-17 questions = average
        "below_average": 20   # 18-20 questions = below average
    }
    
    @staticmethod
    def generate_game(difficulty: int) -> Dict[str, Any]:
        """
        Generate a Twenty Questions game based on difficulty level.
        
        Args:
            difficulty: Difficulty level (1-10)
            
        Returns:
            Game configuration with target object and category
        """
        difficulty = max(1, min(10, difficulty))
        
        # Map difficulty to object pool (1-5, then repeat with harder pools)
        pool_difficulty = ((difficulty - 1) % 5) + 1
        object_pool = TwentyQuestionsTask.OBJECT_POOLS.get(pool_difficulty, TwentyQuestionsTask.OBJECT_POOLS[3])
        
        # Select a random target object
        target_object = random.choice(object_pool["objects"])
        
        return {
            "difficulty": difficulty,
            "category": object_pool["category"],
            "target_object_name": target_object["name"],
            "target_attributes": target_object["attributes"],
            "pool_size": len(object_pool["objects"]),
            "max_questions": 20,
            "instructions": "I'm thinking of something. Ask yes/no questions to figure out what it is! You have up to 20 questions.",
            "hint": f"It's in the category: {object_pool['category']}"
        }
    
    @staticmethod
    def answer_question(question: str, target_attributes: Dict[str, bool], target_object_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Answer a yes/no question about the target object using AI-like logic.
        
        Args:
            question: The question asked by the user
            target_attributes: Dictionary of attributes for the target object
            target_object_name: The actual name of the target object (optional)
            
        Returns:
            Answer (yes/no/maybe) and confidence
        """
        question_lower = question.lower().strip()
        
        # Check if asking about specific object (discourage this strategy)
        if target_object_name:
            object_name_lower = target_object_name.lower()
            # Direct object guess (not ideal strategy but answer honestly)
            if object_name_lower in question_lower or question_lower.endswith(object_name_lower):
                return {"answer": "yes", "confidence": "high"}
            # Check for similar named objects that aren't the target
            common_animals = ["dog", "cat", "bird", "fish", "elephant", "lion", "tiger", "bear", 
                            "horse", "cow", "pig", "chicken", "duck", "rabbit", "mouse", "snake"]
            for animal in common_animals:
                if animal in question_lower and animal != object_name_lower:
                    return {"answer": "no", "confidence": "high"}
        
        # Attribute-based questions (good strategy)
        if "animal" in question_lower or "living" in question_lower:
            return {"answer": "yes" if target_attributes.get("is_animal", False) else "no", "confidence": "high"}
        
        if "fur" in question_lower or "hairy" in question_lower:
            return {"answer": "yes" if target_attributes.get("has_fur", False) else "no", "confidence": "high"}
        
        if "fly" in question_lower:
            return {"answer": "yes" if target_attributes.get("can_fly", False) else "no", "confidence": "high"}
        
        if "water" in question_lower or "swim" in question_lower:
            return {"answer": "yes" if target_attributes.get("lives_in_water", False) else "no", "confidence": "high"}
        
        if "pet" in question_lower or "domestic" in question_lower:
            return {"answer": "yes" if target_attributes.get("is_pet", False) else "no", "confidence": "high"}
        
        if "leg" in question_lower or "four leg" in question_lower:
            return {"answer": "yes" if target_attributes.get("has_four_legs", False) else "no", "confidence": "high"}
        
        if "mammal" in question_lower:
            return {"answer": "yes" if target_attributes.get("is_mammal", False) else "no", "confidence": "high"}
        
        if "large" in question_lower or "big" in question_lower:
            return {"answer": "yes" if target_attributes.get("is_large", False) else "no", "confidence": "high"}
        
        if "wild" in question_lower:
            return {"answer": "yes" if target_attributes.get("is_wild", False) else "no", "confidence": "high"}
        
        if "feather" in question_lower:
            return {"answer": "yes" if target_attributes.get("has_feathers", False) else "no", "confidence": "high"}
        
        if "scale" in question_lower:
            return {"answer": "yes" if target_attributes.get("has_scales", False) else "no", "confidence": "high"}
        
        # If we can't determine, provide helpful hint
        return {"answer": "I'm not sure about that question. Try asking about attributes like 'Does it have fur?' or 'Is it large?'", "confidence": "low"}
    
    @staticmethod
    def score_game(
        questions_asked: int,
        correctly_identified: bool,
        difficulty: int,
        questions_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Score the Twenty Questions game based on performance.
        
        Args:
            questions_asked: Number of questions asked
            correctly_identified: Whether user identified the object correctly
            difficulty: Difficulty level (1-10)
            questions_history: List of questions and answers
            
        Returns:
            Scoring results including efficiency rating and performance metrics
        """
        # Base score calculation
        if not correctly_identified:
            raw_score = 0
            performance_rating = "incorrect"
            feedback = "You didn't identify the object correctly. Try asking more constraint-seeking questions!"
        else:
            # Score based on efficiency (fewer questions = better)
            if questions_asked <= TwentyQuestionsTask.PERFORMANCE_BENCHMARKS["excellent"]:
                performance_rating = "excellent"
                raw_score = 100
                feedback = f"Excellent! You identified it in just {questions_asked} questions. Very efficient!"
            elif questions_asked <= TwentyQuestionsTask.PERFORMANCE_BENCHMARKS["good"]:
                performance_rating = "good"
                raw_score = 85
                feedback = f"Good work! You identified it in {questions_asked} questions. Try to use fewer next time."
            elif questions_asked <= TwentyQuestionsTask.PERFORMANCE_BENCHMARKS["average"]:
                performance_rating = "average"
                raw_score = 70
                feedback = f"You identified it in {questions_asked} questions. Focus on asking broader questions first."
            else:
                performance_rating = "below_average"
                raw_score = 55
                feedback = f"You used {questions_asked} questions. Try constraint-seeking questions like 'Is it living?' instead of specific guesses."
        
        # Adjust score based on difficulty
        difficulty_multiplier = 1 + (difficulty - 1) * 0.05
        normalized_score = min(100, raw_score * difficulty_multiplier)
        
        # Calculate question efficiency
        question_efficiency = (20 - questions_asked) / 20 * 100 if correctly_identified else 0
        
        # Analyze question quality (simple heuristic)
        constraint_seeking_count = sum(
            1 for q in questions_history 
            if any(keyword in q.get("question", "").lower() for keyword in ["is it", "does it", "can it", "has it"])
        )
        specific_guess_count = len(questions_history) - constraint_seeking_count
        strategy_score = (constraint_seeking_count / max(1, len(questions_history))) * 100
        
        # Determine if user should advance
        should_advance = correctly_identified and questions_asked <= 12 and difficulty < 10
        
        return {
            "raw_score": raw_score,
            "normalized_score": round(normalized_score, 2),
            "performance_rating": performance_rating,
            "questions_asked": questions_asked,
            "correctly_identified": correctly_identified,
            "question_efficiency": round(question_efficiency, 2),
            "strategy_score": round(strategy_score, 2),
            "constraint_seeking_questions": constraint_seeking_count,
            "specific_guesses": specific_guess_count,
            "should_advance": should_advance,
            "feedback": feedback,
            "tips": TwentyQuestionsTask._generate_tips(performance_rating, questions_asked, strategy_score)
        }
    
    @staticmethod
    def _generate_tips(performance_rating: str, questions_asked: int, strategy_score: float) -> str:
        """
        Generate strategic tips for the user.
        
        Args:
            performance_rating: Performance rating
            questions_asked: Number of questions asked
            strategy_score: Strategy quality score (0-100)
            
        Returns:
            Tips for improvement
        """
        tips = []
        
        if strategy_score < 60:
            tips.append("💡 Ask broader questions first (e.g., 'Is it living?' 'Is it an animal?') before guessing specific items.")
        
        if questions_asked > 15:
            tips.append("🎯 Use binary search strategy: divide the possibilities in half with each question.")
        
        if performance_rating in ["average", "below_average"]:
            tips.append("🔍 Constraint-seeking questions are more efficient than specific guesses.")
        
        if not tips:
            tips.append("⭐ Great strategy! Keep using broad questions to narrow down possibilities.")
        
        return " ".join(tips)
    
    @staticmethod
    def calculate_difficulty_adjustment(current_difficulty: int, performance: Dict[str, Any]) -> int:
        """
        Calculate the next difficulty level based on performance.
        
        Args:
            current_difficulty: Current difficulty level (1-10)
            performance: Performance metrics from score_game
            
        Returns:
            Next difficulty level (1-10)
        """
        if not performance["correctly_identified"]:
            # Failed to identify - decrease difficulty
            return max(1, current_difficulty - 1)
        
        questions_asked = performance["questions_asked"]
        
        # Advancement criteria
        if questions_asked <= 7 and current_difficulty < 10:
            # Excellent efficiency - increase by 2
            return min(10, current_difficulty + 2)
        elif questions_asked <= 12 and current_difficulty < 10:
            # Good efficiency - increase by 1
            return min(10, current_difficulty + 1)
        elif questions_asked > 17 and current_difficulty > 1:
            # Poor efficiency - decrease by 1
            return max(1, current_difficulty - 1)
        else:
            # Maintain current difficulty
            return current_difficulty

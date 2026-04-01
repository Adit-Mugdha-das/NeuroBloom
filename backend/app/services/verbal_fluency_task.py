"""
Verbal Fluency - Controlled Oral Word Association (COWAT) Task Service

Clinical validation: Executive function standard (Benton & Hamsher, 1989)
Description: Generate words starting with specific letters in 60 seconds

MS Research Evidence:
- Verbal fluency deficits common in MS
- Measures initiation, strategy, executive control
- Standard letters: F, A, S (COWAT)
- MS average: 30-40 words across 3 letters (10-13 per letter)

Rules:
- No proper nouns (names, places, brands)
- No repetitions
- No variants (e.g., "run", "running", "runs" count as one)
- Words must start with the target letter
"""

import random
from typing import Dict, Any, List, Set
from datetime import datetime
import re


class VerbalFluencyTask:
    """
    Verbal Fluency (COWAT) implementation
    
    User generates words starting with specific letters
    Each letter round is 60 seconds
    
    Difficulty affects:
    - Letter selection (common vs rare)
    - Number of letters (1-3)
    - Time per letter (may reduce for higher levels)
    - Strictness of validation
    
    Scoring based on unique valid words
    """
    
    # Letter sets by difficulty
    LETTER_SETS = {
        "easy": ["S", "P", "C", "B", "M"],  # Very common starting letters
        "medium": ["F", "A", "T", "R", "D"],  # Standard COWAT (F, A, S/T)
        "hard": ["L", "W", "N", "H", "G"],  # Less common
        "expert": ["Q", "X", "Z", "V", "J"],  # Rare starting letters
    }

    BANGLA_LETTER_SETS = {
        "easy": ["ক", "ম", "ব", "স", "প"],
        "medium": ["অ", "ত", "ন", "ল", "চ"],
        "hard": ["দ", "র", "গ", "হ", "শ"],
        "expert": ["ভ", "ফ", "ঘ", "ছ", "ঝ"],
    }

    ENGLISH_SUFFIXES = ["ing", "ed", "s", "es", "er", "est", "ly", "tion", "ness", "ment"]
    BANGLA_SUFFIXES = ["গুলো", "গুলি", "দের", "ের", "টা", "টি", "রা", "তে", "র"]
    
    # Common proper nouns to reject (not exhaustive, but helps)
    COMMON_PROPER_NOUNS = {
        # Names
        "john", "mary", "james", "michael", "david", "robert", "sarah", "jennifer",
        "william", "richard", "thomas", "charles", "daniel", "matthew", "joseph",
        # Places
        "america", "europe", "asia", "africa", "france", "spain", "italy", "germany",
        "london", "paris", "rome", "beijing", "tokyo", "moscow", "berlin",
        "california", "texas", "florida", "york",
        # Brands/Companies
        "google", "facebook", "apple", "microsoft", "amazon", "walmart", "target",
        "ford", "toyota", "honda", "nike", "adidas", "pepsi", "coke",
        # Days/Months
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
        "january", "february", "march", "april", "june", "july", "august",
        "september", "october", "november", "december",
    }
    
    # Difficulty configuration
    DIFFICULTY_CONFIG = {
        1: {
            "letter_category": "easy",
            "num_letters": 1,
            "time_per_letter_seconds": 60,
            "min_words_target": 5,  # Low target for beginners
            "strict_validation": False,
        },
        2: {
            "letter_category": "easy",
            "num_letters": 2,
            "time_per_letter_seconds": 60,
            "min_words_target": 8,
            "strict_validation": False,
        },
        3: {
            "letter_category": "medium",
            "num_letters": 2,
            "time_per_letter_seconds": 60,
            "min_words_target": 10,
            "strict_validation": False,
        },
        4: {
            "letter_category": "medium",
            "num_letters": 3,
            "time_per_letter_seconds": 60,
            "min_words_target": 12,
            "strict_validation": True,
        },
        5: {
            "letter_category": "medium",
            "num_letters": 3,
            "time_per_letter_seconds": 60,
            "min_words_target": 15,
            "strict_validation": True,
        },
        6: {
            "letter_category": "hard",
            "num_letters": 2,
            "time_per_letter_seconds": 60,
            "min_words_target": 12,
            "strict_validation": True,
        },
        7: {
            "letter_category": "hard",
            "num_letters": 3,
            "time_per_letter_seconds": 60,
            "min_words_target": 15,
            "strict_validation": True,
        },
        8: {
            "letter_category": "hard",
            "num_letters": 3,
            "time_per_letter_seconds": 55,
            "min_words_target": 18,
            "strict_validation": True,
        },
        9: {
            "letter_category": "expert",
            "num_letters": 2,
            "time_per_letter_seconds": 60,
            "min_words_target": 10,
            "strict_validation": True,
        },
        10: {
            "letter_category": "expert",
            "num_letters": 3,
            "time_per_letter_seconds": 60,
            "min_words_target": 12,
            "strict_validation": True,
        },
    }

    @staticmethod
    def normalize_locale(locale: str | None) -> str:
        return "bn" if locale == "bn" else "en"

    @staticmethod
    def letter_sets_for_locale(locale: str) -> Dict[str, List[str]]:
        return (
            VerbalFluencyTask.BANGLA_LETTER_SETS
            if VerbalFluencyTask.normalize_locale(locale) == "bn"
            else VerbalFluencyTask.LETTER_SETS
        )

    @staticmethod
    def variant_suffixes_for_locale(locale: str) -> List[str]:
        return (
            VerbalFluencyTask.BANGLA_SUFFIXES
            if VerbalFluencyTask.normalize_locale(locale) == "bn"
            else VerbalFluencyTask.ENGLISH_SUFFIXES
        )

    @staticmethod
    def localized_instruction_copy(locale: str, seconds: int) -> Dict[str, Any]:
        if VerbalFluencyTask.normalize_locale(locale) == "bn":
            return {
                "title": "শব্দপ্রবাহ অনুশীলন",
                "description": f"প্রতিটি অক্ষর দেখে {seconds} সেকেন্ডের মধ্যে সেই অক্ষর দিয়ে যত বেশি সম্ভব শব্দ লিখুন।",
                "rules": [
                    "দেওয়া অক্ষর দিয়ে শুরু হয় এমন শব্দ লিখুন",
                    "ব্যক্তিনাম, জায়গার নাম বা ব্র্যান্ডের নাম লিখবেন না",
                    "একই শব্দ বারবার লেখা যাবে না",
                    "একই শব্দের কাছাকাছি রূপ একবারই গণনা হবে",
                    "প্রতিটি শব্দ লিখে Enter বা Space চাপুন"
                ],
                "details_title": "সেশনের বিবরণ",
                "comparison": "এমএস রোগীদের গড়: প্রতি অক্ষরে ১০-১৩টি শব্দ"
            }

        return {
            "title": "Verbal Fluency Test",
            "description": f"Generate as many words as possible starting with each letter in {seconds} seconds.",
            "rules": [
                "Type words that start with the given letter",
                "No proper nouns (names, places, brands)",
                "No repetitions",
                "No variants (run, running, runs = 1 word)",
                "Press Enter or Space to submit each word"
            ],
            "details_title": "Session Details",
            "comparison": "MS patient average: 10-13 words per letter"
        }

    @staticmethod
    def localized_reason(reason_key: str, locale: str, **kwargs: Any) -> str:
        locale = VerbalFluencyTask.normalize_locale(locale)

        if locale == "bn":
            reasons = {
                "empty_word": "ফাঁকা শব্দ গ্রহণযোগ্য নয়",
                "too_short": "খুব ছোট (কমপক্ষে ২টি অক্ষর)",
                "wrong_letter": f"'{kwargs.get('target_letter', '')}' দিয়ে শুরু হতে হবে",
                "proper_noun": "ব্যক্তিনাম বা বিশেষ নাম গ্রহণযোগ্য নয়",
                "proper_noun_common": "নাম, জায়গা বা ব্র্যান্ড গ্রহণযোগ্য নয়",
                "variant_used": "একই শব্দপরিবার আগেই ব্যবহার হয়েছে"
            }
            return reasons.get(reason_key, reason_key)

        reasons = {
            "empty_word": "Empty word",
            "too_short": "Too short (min 2 letters)",
            "wrong_letter": f"Must start with '{kwargs.get('target_letter', '')}'",
            "proper_noun": "No proper nouns",
            "proper_noun_common": "No proper nouns (names/places/brands)",
            "variant_used": "Variant already used"
        }
        return reasons.get(reason_key, reason_key)
    
    @staticmethod
    def generate_session(
        difficulty: int,
        baseline_score: int | None = None,
        locale: str = "en"
    ) -> Dict[str, Any]:
        """
        Generate a verbal fluency session
        
        Args:
            difficulty: 1-10
            baseline_score: Not used (task doesn't adapt based on baseline)
            
        Returns:
            Session data with letters and configuration
        """
        if difficulty not in VerbalFluencyTask.DIFFICULTY_CONFIG:
            difficulty = 5
            
        locale = VerbalFluencyTask.normalize_locale(locale)
        config = VerbalFluencyTask.DIFFICULTY_CONFIG[difficulty]
        letter_category = config["letter_category"]
        num_letters = config["num_letters"]
        instruction_copy = VerbalFluencyTask.localized_instruction_copy(
            locale,
            config["time_per_letter_seconds"]
        )

        # Select random letters from the category
        available_letters = VerbalFluencyTask.letter_sets_for_locale(locale)[letter_category].copy()
        random.shuffle(available_letters)
        selected_letters = available_letters[:num_letters]
        
        session_data = {
            "difficulty": difficulty,
            "letters": selected_letters,
            "letter_category": letter_category,
            "time_per_letter_seconds": config["time_per_letter_seconds"],
            "min_words_target": config["min_words_target"],
            "strict_validation": config["strict_validation"],
            "total_letters": num_letters,
            "locale": locale,
            "script": "bangla" if locale == "bn" else "latin",
            "instructions": {
                "title": instruction_copy["title"],
                "description": instruction_copy["description"],
                "rules": instruction_copy["rules"]
            }
        }
        
        return session_data
    
    @staticmethod
    def _get_word_root(word: str) -> str:
        """
        Get root form of word to detect variants
        Simple heuristic: remove common suffixes
        """
        word = word.lower()
        
        # Remove common suffixes
        suffixes = VerbalFluencyTask.ENGLISH_SUFFIXES
        
        for suffix in sorted(suffixes, key=len, reverse=True):
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                return word[:-len(suffix)]
        
        return word
    
    @staticmethod
    def validate_word(
        word: str,
        target_letter: str,
        seen_roots: Set[str],
        strict: bool = True,
        locale: str = "en"
    ) -> Dict[str, Any]:
        """
        Validate a word submission
        
        Returns:
            {
                "valid": bool,
                "reason": str (if invalid),
                "root": str (word root for variant detection)
            }
        """
        locale = VerbalFluencyTask.normalize_locale(locale)
        word_clean = word.strip().lower()
        target_letter_lower = target_letter.strip().lower()
        
        # Basic validation
        if not word_clean:
            return {
                "valid": False,
                "reason": VerbalFluencyTask.localized_reason("empty_word", locale)
            }

        if len(word_clean) < 2:
            return {
                "valid": False,
                "reason": VerbalFluencyTask.localized_reason("too_short", locale)
            }

        # Check if word starts with target letter
        if not word_clean.startswith(target_letter_lower):
            return {
                "valid": False,
                "reason": VerbalFluencyTask.localized_reason(
                    "wrong_letter",
                    locale,
                    target_letter=target_letter
                )
            }

        # Check if it's a proper noun (basic check - starts with capital in original)
        if (
            locale == "en"
            and strict
            and word[0].isupper()
            and word not in ["I", "I'm", "I've", "I'd", "I'll"]
        ):
            return {
                "valid": False,
                "reason": VerbalFluencyTask.localized_reason("proper_noun", locale)
            }

        # Check against common proper nouns list
        if locale == "en" and word_clean in VerbalFluencyTask.COMMON_PROPER_NOUNS:
            return {
                "valid": False,
                "reason": VerbalFluencyTask.localized_reason("proper_noun_common", locale)
            }

        # Check for variants (root already seen)
        root = VerbalFluencyTask._get_word_root(word_clean)
        if locale == "bn":
            for suffix in sorted(VerbalFluencyTask.BANGLA_SUFFIXES, key=len, reverse=True):
                if root.endswith(suffix) and len(root) > len(suffix) + 1:
                    root = root[: -len(suffix)]
                    break

        if root in seen_roots:
            return {
                "valid": False,
                "reason": VerbalFluencyTask.localized_reason("variant_used", locale)
            }
        
        return {
            "valid": True,
            "root": root
        }
    
    @staticmethod
    def score_session(session_data: Dict[str, Any], user_responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Score verbal fluency session
        
        Args:
            session_data: Original session data from generate_session
            user_responses: List of letter results
                [
                    {
                        "letter": "F",
                        "words": ["fish", "food", "fun", ...],
                        "time_taken_seconds": 58.3
                    },
                    ...
                ]
                
        Returns:
            Scoring results with performance metrics
        """
        difficulty = session_data["difficulty"]
        locale = VerbalFluencyTask.normalize_locale(session_data.get("locale"))
        config = VerbalFluencyTask.DIFFICULTY_CONFIG[difficulty]
        strict = config["strict_validation"]
        
        total_valid_words = 0
        total_invalid_words = 0
        letter_results = []
        
        for response in user_responses:
            letter = response["letter"]
            words = response.get("words", [])
            time_taken = response.get("time_taken_seconds", 60)
            
            seen_roots = set()
            valid_words = []
            invalid_words = []
            
            for word in words:
                validation = VerbalFluencyTask.validate_word(
                    word,
                    letter,
                    seen_roots,
                    strict,
                    locale=locale
                )
                
                if validation["valid"]:
                    valid_words.append(word.lower())
                    seen_roots.add(validation["root"])
                else:
                    invalid_words.append({
                        "word": word,
                        "reason": validation["reason"]
                    })
            
            letter_result = {
                "letter": letter,
                "valid_word_count": len(valid_words),
                "invalid_word_count": len(invalid_words),
                "valid_words": valid_words,
                "invalid_words": invalid_words,
                "time_taken_seconds": time_taken,
            }
            
            letter_results.append(letter_result)
            total_valid_words += len(valid_words)
            total_invalid_words += len(invalid_words)
        
        # Calculate score
        # MS average: 30-40 words across 3 letters (10-13 per letter)
        # Scale: 0-100
        avg_words_per_letter = total_valid_words / len(user_responses) if user_responses else 0
        
        # Scoring rubric
        # 15+ words per letter = 100 (excellent)
        # 10-15 = 70-100 (good, MS average range)
        # 5-10 = 40-70 (below average)
        # <5 = 0-40 (low)
        
        if avg_words_per_letter >= 15:
            score = 100
        elif avg_words_per_letter >= 10:
            score = 70 + ((avg_words_per_letter - 10) / 5) * 30
        elif avg_words_per_letter >= 5:
            score = 40 + ((avg_words_per_letter - 5) / 5) * 30
        else:
            score = (avg_words_per_letter / 5) * 40
        
        score = round(min(100, max(0, score)))
        
        # Performance classification
        if avg_words_per_letter >= 13:
            performance = "excellent"
        elif avg_words_per_letter >= 10:
            performance = "good"
        elif avg_words_per_letter >= 7:
            performance = "average"
        else:
            performance = "below_average"
        
        results = {
            "score": score,
            "total_valid_words": total_valid_words,
            "total_invalid_words": total_invalid_words,
            "avg_words_per_letter": round(avg_words_per_letter, 1),
            "letter_results": letter_results,
            "performance": performance,
            "difficulty": difficulty,
            "completed": True,
            "ms_comparison": {
                "description": VerbalFluencyTask.localized_instruction_copy(
                    locale,
                    session_data.get("time_per_letter_seconds", 60)
                )["comparison"],
                "user_avg": round(avg_words_per_letter, 1),
                "status": "above_average" if avg_words_per_letter >= 10 else "below_average"
            }
        }
        
        return results


# Singleton instance
verbal_fluency_task_service = VerbalFluencyTask()

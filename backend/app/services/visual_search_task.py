"""
Visual Search Task (Feature vs. Conjunction)
Clinical Validation: Treisman & Gelade (1980) - Attention theory
Measures: Visual attention mechanisms, selective attention

Feature Search: Target differs by single feature (color OR shape)
Conjunction Search: Target defined by multiple features (color AND shape)
MS patients show deficits in conjunction search due to attentional demands
"""

from typing import Dict, Any, List
import random
from datetime import datetime


class VisualSearchTask:
    """
    Visual Search task implementing feature and conjunction search paradigms.
    
    Feature search: Red circle among blue circles (pops out)
    Conjunction search: Red circle among red squares + blue circles (serial search)
    """
    
    # Search configurations by difficulty
    # Based on Treisman & Gelade (1980) and MS visual attention research
    SEARCH_CONFIGS = {
        1: {"set_size": 12, "search_type": "feature", "time_limit": 30, "similarity": "low"},
        2: {"set_size": 16, "search_type": "feature", "time_limit": 25, "similarity": "low"},
        3: {"set_size": 20, "search_type": "feature", "time_limit": 20, "similarity": "medium"},
        4: {"set_size": 24, "search_type": "conjunction", "time_limit": 45, "similarity": "low"},
        5: {"set_size": 28, "search_type": "conjunction", "time_limit": 40, "similarity": "low"},
        6: {"set_size": 32, "search_type": "conjunction", "time_limit": 35, "similarity": "medium"},
        7: {"set_size": 36, "search_type": "conjunction", "time_limit": 30, "similarity": "medium"},
        8: {"set_size": 40, "search_type": "conjunction", "time_limit": 25, "similarity": "high"},
        9: {"set_size": 44, "search_type": "conjunction", "time_limit": 20, "similarity": "high"},
        10: {"set_size": 48, "search_type": "conjunction", "time_limit": 15, "similarity": "high"}
    }
    
    # Visual stimuli definitions
    SHAPES = ["circle", "square", "triangle", "diamond"]
    COLORS = ["red", "blue", "green", "yellow", "purple", "orange"]
    
    # Similarity levels affect distractor selection
    SIMILARITY_CONFIGS = {
        "low": {"color_distance": 3, "shape_variants": 1},     # Very different
        "medium": {"color_distance": 2, "shape_variants": 2},   # Somewhat similar
        "high": {"color_distance": 1, "shape_variants": 3}      # Very similar
    }
    
    @staticmethod
    def generate_trial(difficulty: int) -> Dict[str, Any]:
        """
        Generate a visual search trial based on difficulty.
        
        Args:
            difficulty: 1-10 difficulty level
            
        Returns:
            Trial configuration with items array and target info
        """
        config = VisualSearchTask.SEARCH_CONFIGS[difficulty]
        set_size = config["set_size"]
        search_type = config["search_type"]
        similarity = config["similarity"]
        
        # Determine if target is present (75% present, 25% absent)
        target_present = random.random() < 0.75
        
        # Select target properties
        if search_type == "feature":
            # Feature search: Target differs by ONE feature
            target = VisualSearchTask._generate_feature_search_trial(
                set_size, target_present, similarity
            )
        else:
            # Conjunction search: Target differs by COMBINATION of features
            target = VisualSearchTask._generate_conjunction_search_trial(
                set_size, target_present, similarity
            )
        
        return {
            "difficulty": difficulty,
            "search_type": search_type,
            "set_size": set_size,
            "time_limit": config["time_limit"],
            "target_present": target_present,
            "target": target["target"],
            "items": target["items"],
            "similarity": similarity,
            "trial_start_time": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def _generate_feature_search_trial(set_size: int, target_present: bool, similarity: str) -> Dict[str, Any]:
        """Generate feature search trial (single feature difference)."""
        
        # Choose target - single distinctive feature
        # Example: Red circle among blue circles (color differs)
        # Or: Red circle among red squares (shape differs)
        
        search_dimension = random.choice(["color", "shape"])
        
        if search_dimension == "color":
            # All same shape, different colors
            shape = random.choice(VisualSearchTask.SHAPES)
            target_color = random.choice(VisualSearchTask.COLORS)
            
            # Select distractor color (different from target)
            available_colors = [c for c in VisualSearchTask.COLORS if c != target_color]
            distractor_color = random.choice(available_colors)
            
            target_item = {"shape": shape, "color": target_color}
            distractor_template = {"shape": shape, "color": distractor_color}
            
        else:
            # All same color, different shapes
            color = random.choice(VisualSearchTask.COLORS)
            target_shape = random.choice(VisualSearchTask.SHAPES)
            
            # Select distractor shape (different from target)
            available_shapes = [s for s in VisualSearchTask.SHAPES if s != target_shape]
            distractor_shape = random.choice(available_shapes)
            
            target_item = {"shape": target_shape, "color": color}
            distractor_template = {"shape": distractor_shape, "color": color}
        
        # Build items array
        items = []
        
        if target_present:
            # Add target at random position
            target_index = random.randint(0, set_size - 1)
            for i in range(set_size):
                if i == target_index:
                    items.append({
                        **target_item,
                        "position": VisualSearchTask._random_position(i, set_size),
                        "is_target": True
                    })
                else:
                    items.append({
                        **distractor_template,
                        "position": VisualSearchTask._random_position(i, set_size),
                        "is_target": False
                    })
        else:
            # All distractors
            for i in range(set_size):
                items.append({
                    **distractor_template,
                    "position": VisualSearchTask._random_position(i, set_size),
                    "is_target": False
                })
        
        return {
            "target": target_item,
            "items": items
        }
    
    @staticmethod
    def _generate_conjunction_search_trial(set_size: int, target_present: bool, similarity: str) -> Dict[str, Any]:
        """Generate conjunction search trial (multiple feature combination)."""
        
        # Conjunction search: Target defined by BOTH color AND shape
        # Example: Red circle among red squares + blue circles
        # Requires serial search through items
        
        target_shape = random.choice(VisualSearchTask.SHAPES)
        target_color = random.choice(VisualSearchTask.COLORS)
        target_item = {"shape": target_shape, "color": target_color}
        
        # Create two distractor types that share ONE feature with target
        available_shapes = [s for s in VisualSearchTask.SHAPES if s != target_shape]
        available_colors = [c for c in VisualSearchTask.COLORS if c != target_color]
        
        # Distractor Type 1: Same color, different shape (red square)
        distractor_shape_1 = random.choice(available_shapes)
        distractor_type_1 = {"shape": distractor_shape_1, "color": target_color}
        
        # Distractor Type 2: Different color, same shape (blue circle)
        distractor_color_2 = random.choice(available_colors)
        distractor_type_2 = {"shape": target_shape, "color": distractor_color_2}
        
        # For higher similarity, add more distractor variants
        distractor_types = [distractor_type_1, distractor_type_2]
        
        if similarity in ["medium", "high"]:
            # Add third distractor type (different color + shape)
            distractor_shape_3 = random.choice(available_shapes)
            distractor_color_3 = random.choice(available_colors)
            distractor_type_3 = {"shape": distractor_shape_3, "color": distractor_color_3}
            distractor_types.append(distractor_type_3)
        
        # Build items array
        items = []
        
        if target_present:
            # Add target at random position
            target_index = random.randint(0, set_size - 1)
            for i in range(set_size):
                if i == target_index:
                    items.append({
                        **target_item,
                        "position": VisualSearchTask._random_position(i, set_size),
                        "is_target": True
                    })
                else:
                    # Randomly select distractor type
                    distractor = random.choice(distractor_types)
                    items.append({
                        **distractor,
                        "position": VisualSearchTask._random_position(i, set_size),
                        "is_target": False
                    })
        else:
            # All distractors
            for i in range(set_size):
                distractor = random.choice(distractor_types)
                items.append({
                    **distractor,
                    "position": VisualSearchTask._random_position(i, set_size),
                    "is_target": False
                })
        
        return {
            "target": target_item,
            "items": items
        }
    
    @staticmethod
    def _random_position(index: int, total: int) -> Dict[str, float]:
        """
        Generate random position for item in visual field.

        Research-valid display with scaled viewport:
        - Viewport size scales with item count (more items = larger area)
        - This ensures RT scales linearly with items (research-valid)
        - Maximum 70% of screen height (leave 30% for header + buttons)
        - Random distribution for natural appearance

        Viewport scaling:
        - 12 items: ~40% of screen (compact, sparse)
        - 24 items: ~52% of screen (medium density)
        - 48 items: ~70% of screen (larger area, dense)
        """
        # Calculate grid for positioning
        grid_size = int(total ** 0.5) + 1
        row = index // grid_size
        col = index % grid_size
        
        # Scale viewport based on item count (research-valid)
        # Formula: grows from 40% (12 items) to 70% (48 items)
        viewport_scale = 0.40 + ((total - 12) / 120.0)  # Gradual scaling
        viewport_scale = min(0.70, max(0.40, viewport_scale))  # Clamp between 40-70%

        # Center the viewport on screen
        margin = (1.0 - viewport_scale) / 2.0

        # Position within grid
        x_in_grid = col / grid_size
        y_in_grid = row / grid_size

        # Map to scaled viewport (centered)
        x = margin + (x_in_grid * viewport_scale)
        y = margin + (y_in_grid * viewport_scale)

        # Add random jitter for natural appearance
        cell_size = viewport_scale / grid_size
        jitter_x = random.uniform(-0.10, 0.10) * cell_size
        jitter_y = random.uniform(-0.10, 0.10) * cell_size

        return {
            "x": x + jitter_x,
            "y": y + jitter_y
        }
    
    @staticmethod
    def score_response(trial_data: Dict[str, Any], user_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score user's response to visual search trial.
        
        Args:
            trial_data: Original trial configuration
            user_response: User's response with answer and timing
            
        Returns:
            Scoring results with accuracy, RT, efficiency, search slope
        """
        target_present = trial_data["target_present"]
        user_answer = user_response.get("target_found", False)
        reaction_time = user_response.get("reaction_time", 0)
        set_size = trial_data["set_size"]
        search_type = trial_data["search_type"]
        
        # Determine correctness
        correct = (user_answer == target_present)
        
        # Calculate accuracy score
        if correct:
            accuracy = 1.0
            # Bonus for fast correct responses
            time_limit = trial_data["time_limit"]
            speed_bonus = max(0, (time_limit - reaction_time) / time_limit) * 0.2
            score = min(1.0, accuracy + speed_bonus)
        else:
            accuracy = 0.0
            score = 0.0
        
        # Calculate search efficiency (RT per item)
        search_efficiency = reaction_time / set_size if set_size > 0 else 0
        search_slope = search_efficiency * 1000  # Convert to ms/item

        # Performance classification - Research-valid with scaled viewport
        # Now that viewport scales with item count, ms/item is valid measure
        # Thresholds based on Treisman & Gelade (1980) + similarity effects
        # ADJUSTED: More forgiving ratings for lower difficulties to encourage patients

        similarity = trial_data.get("similarity", "low")
        difficulty = trial_data.get("difficulty", 5)

        # Apply difficulty-based flexibility multiplier
        # Lower difficulties get more lenient thresholds
        if difficulty <= 3:
            flexibility = 1.5  # 50% more lenient for beginners
        elif difficulty <= 6:
            flexibility = 1.2  # 20% more lenient for intermediate
        else:
            flexibility = 1.0  # Standard thresholds for advanced

        if search_type == "feature":
            # Feature search - parallel processing with pop-out
            if similarity == "low":
                # Clear pop-out: nearly flat slope
                if search_slope < (15 * flexibility) and correct:
                    performance = "excellent"  # Truly parallel
                elif search_slope < (35 * flexibility) and correct:
                    performance = "good"  # Efficient parallel
                elif search_slope < (65 * flexibility) and correct:
                    performance = "average"  # Adequate
                else:
                    performance = "needs_improvement"
            elif similarity == "medium":
                # Reduced pop-out: some serial component
                if search_slope < (30 * flexibility) and correct:
                    performance = "excellent"
                elif search_slope < (60 * flexibility) and correct:
                    performance = "good"
                elif search_slope < (100 * flexibility) and correct:
                    performance = "average"
                else:
                    performance = "needs_improvement"
            else:  # high similarity
                # Crowding effects: approaching serial
                if search_slope < (50 * flexibility) and correct:
                    performance = "excellent"
                elif search_slope < (85 * flexibility) and correct:
                    performance = "good"
                elif search_slope < (130 * flexibility) and correct:
                    performance = "average"
                else:
                    performance = "needs_improvement"
        else:
            # Conjunction search - serial attention required
            if similarity == "low":
                # Efficient serial search
                if search_slope < (40 * flexibility) and correct:
                    performance = "excellent"
                elif search_slope < (75 * flexibility) and correct:
                    performance = "good"
                elif search_slope < (120 * flexibility) and correct:
                    performance = "average"
                else:
                    performance = "needs_improvement"
            elif similarity == "medium":
                # Moderate serial search
                if search_slope < (65 * flexibility) and correct:
                    performance = "excellent"
                elif search_slope < (110 * flexibility) and correct:
                    performance = "good"
                elif search_slope < (165 * flexibility) and correct:
                    performance = "average"
                else:
                    performance = "needs_improvement"
            else:  # high similarity
                # Difficult serial search
                if search_slope < (90 * flexibility) and correct:
                    performance = "excellent"
                elif search_slope < (145 * flexibility) and correct:
                    performance = "good"
                elif search_slope < (215 * flexibility) and correct:
                    performance = "average"
                else:
                    performance = "needs_improvement"

        # Detect response type
        if correct and target_present:
            response_type = "hit"
        elif not correct and target_present:
            response_type = "miss"
        elif not correct and not target_present:
            response_type = "false_alarm"
        else:
            response_type = "correct_rejection"
        
        return {
            "score": score,
            "accuracy": accuracy,
            "correct": correct,
            "reaction_time": reaction_time,
            "search_efficiency": search_efficiency,
            "search_slope_ms": search_slope,
            "performance": performance,
            "response_type": response_type,
            "search_type": search_type,
            "set_size": set_size,
            "target_present": target_present,
            "user_answer": user_answer
        }
    
    @staticmethod
    def calculate_difficulty_adjustment(
        recent_scores: List[float],
        current_difficulty: int,
        accuracy: float,
        reaction_time: float,
        time_limit: float
    ) -> int:
        """
        Calculate adaptive difficulty adjustment.
        
        Args:
            recent_scores: Last 5 trial scores
            current_difficulty: Current difficulty level (1-10)
            accuracy: Current trial accuracy
            reaction_time: Current trial RT
            time_limit: Time limit for trial
            
        Returns:
            New difficulty level
        """
        if len(recent_scores) < 3:
            return current_difficulty
        
        avg_score = sum(recent_scores) / len(recent_scores)
        avg_rt_ratio = reaction_time / time_limit if time_limit > 0 else 1.0
        
        # Increase difficulty if performing well
        if avg_score >= 0.85 and accuracy >= 0.9 and avg_rt_ratio < 0.6:
            return min(10, current_difficulty + 1)
        
        # Decrease if struggling
        elif avg_score < 0.6 or accuracy == 0:
            return max(1, current_difficulty - 1)
        
        # Stay at current level
        return current_difficulty

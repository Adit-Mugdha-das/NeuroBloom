"""
Flanker Task Service (Eriksen Flanker Test)

Clinical Validation: ⭐⭐⭐⭐ Attention Networks Test (ANT) Component
Measures: Selective attention, conflict resolution, executive control
MS Relevance: Sensitive to attention deficits and executive dysfunction

Reference: Eriksen & Eriksen, 1974; Fan et al., 2002 (ANT)
"""

from typing import Dict, List, Any, Optional
import random
from datetime import datetime

class FlankerTask:
    """
    Flanker Task - Test selective attention and conflict resolution.
    
    Task Structure:
    - Congruent trials: All arrows point same direction (→ → → → →)
    - Incongruent trials: Flankers conflict with target (← ← → ← ←)
    - User must identify direction of CENTER arrow only
    
    Key Measures:
    - Overall accuracy and reaction time
    - Congruent vs Incongruent performance
    - Flanker/Conflict Effect: RT_incongruent - RT_congruent
    - Error rate on incongruent trials (interference)
    """
    
    # Arrow stimuli for different difficulty levels
    ARROW_SETS = {
        'basic': {
            'left': '←',
            'right': '→',
            'description': 'Basic arrows'
        },
        'thick': {
            'left': '⬅',
            'right': '➡',
            'description': 'Thick arrows'
        },
        'double': {
            'left': '⇐',
            'right': '⇒',
            'description': 'Double arrows'
        },
        'triangles': {
            'left': '◀',
            'right': '▶',
            'description': 'Triangle pointers'
        }
    }
    
    # Difficulty levels: 10 levels optimized for MS patients
    # Key variables: presentation time, flanker count, congruent ratio, spacing
    DIFFICULTY_CONFIG = {
        1: {
            "arrow_set": "basic",
            "presentation_time_ms": 1200,  # Generous time for MS patients starting out
            "inter_stimulus_interval_ms": 600,
            "total_trials": 40,
            "flanker_count": 2,
            "congruent_ratio": 0.60,
            "stimulus_size": "large",
            "spacing": "wide",
            "description": "Beginner - Comfortable pace"
        },
        2: {
            "arrow_set": "basic",
            "presentation_time_ms": 1000,  # Still comfortable
            "inter_stimulus_interval_ms": 550,
            "total_trials": 50,
            "flanker_count": 2,
            "congruent_ratio": 0.58,
            "stimulus_size": "large",
            "spacing": "wide",
            "description": "Easy - Relaxed"
        },
        3: {
            "arrow_set": "basic",
            "presentation_time_ms": 850,  # Gradual decrease
            "inter_stimulus_interval_ms": 500,
            "total_trials": 60,
            "flanker_count": 2,
            "congruent_ratio": 0.55,
            "stimulus_size": "large",
            "spacing": "medium",
            "description": "Moderate - Building speed"
        },
        4: {
            "arrow_set": "basic",
            "presentation_time_ms": 700,  # Standard clinical timing starts here
            "inter_stimulus_interval_ms": 500,
            "total_trials": 70,
            "flanker_count": 2,
            "congruent_ratio": 0.52,
            "stimulus_size": "medium",
            "spacing": "medium",
            "description": "Intermediate - Standard pace"
        },
        5: {
            "arrow_set": "thick",
            "presentation_time_ms": 600,  # Research standard (500-800ms typical)
            "inter_stimulus_interval_ms": 500,
            "total_trials": 80,
            "flanker_count": 3,
            "congruent_ratio": 0.50,
            "stimulus_size": "medium",
            "spacing": "medium",
            "description": "Challenging - Research standard"
        },
        6: {
            "arrow_set": "thick",
            "presentation_time_ms": 500,  # Clinical ANT standard
            "inter_stimulus_interval_ms": 450,
            "total_trials": 90,
            "flanker_count": 3,
            "congruent_ratio": 0.48,
            "stimulus_size": "medium",
            "spacing": "narrow",
            "description": "Advanced - ANT standard"
        },
        7: {
            "arrow_set": "double",
            "presentation_time_ms": 400,  # Getting challenging
            "inter_stimulus_interval_ms": 450,
            "total_trials": 100,
            "flanker_count": 3,
            "congruent_ratio": 0.45,
            "stimulus_size": "small",
            "spacing": "narrow",
            "description": "Expert - Fast pace"
        },
        8: {
            "arrow_set": "double",
            "presentation_time_ms": 350,  # Very fast
            "inter_stimulus_interval_ms": 400,
            "total_trials": 110,
            "flanker_count": 3,
            "congruent_ratio": 0.43,
            "stimulus_size": "small",
            "spacing": "narrow",
            "description": "Master - Demanding"
        },
        9: {
            "arrow_set": "triangles",
            "presentation_time_ms": 300,  # Elite performance
            "inter_stimulus_interval_ms": 400,
            "total_trials": 120,
            "flanker_count": 3,
            "congruent_ratio": 0.42,
            "stimulus_size": "small",
            "spacing": "tight",
            "description": "Elite - Peak performance"
        },
        10: {
            "arrow_set": "triangles",
            "presentation_time_ms": 250,  # Maximum challenge (research lower bound ~150-250ms)
            "inter_stimulus_interval_ms": 400,
            "total_trials": 120,
            "flanker_count": 3,
            "congruent_ratio": 0.40,  # 60% incongruent
            "stimulus_size": "small",
            "spacing": "tight",
            "description": "Ultimate - Extreme speed, maximum conflict"
        }
    }
    
    def __init__(self):
        self.session_data = {}
    
    def generate_session(self, difficulty: int = 1) -> Dict[str, Any]:
        """
        Generate a Flanker task session with specified difficulty.
        
        Returns:
            Session data including trials, configuration, and metadata
        """
        if difficulty not in self.DIFFICULTY_CONFIG:
            difficulty = 1
        
        config = self.DIFFICULTY_CONFIG[difficulty]
        arrow_set = self.ARROW_SETS[config['arrow_set']]
        
        # Generate trial sequence
        trials = self._generate_trials(
            total_trials=config['total_trials'],
            congruent_ratio=config['congruent_ratio'],
            flanker_count=config['flanker_count'],
            arrow_set=arrow_set
        )
        
        # Count trial types
        congruent_count = sum(1 for t in trials if t['trial_type'] == 'congruent')
        incongruent_count = len(trials) - congruent_count
        
        session_data = {
            'difficulty': difficulty,
            'trials': trials,
            'total_trials': len(trials),
            'congruent_trials': congruent_count,
            'incongruent_trials': incongruent_count,
            
            # Timing configuration
            'presentation_time_ms': config['presentation_time_ms'],
            'inter_stimulus_interval_ms': config['inter_stimulus_interval_ms'],
            
            # Display configuration
            'flanker_count': config['flanker_count'],
            'stimulus_size': config['stimulus_size'],
            'spacing': config['spacing'],
            'arrow_set': config['arrow_set'],
            
            # Arrow symbols
            'left_arrow': arrow_set['left'],
            'right_arrow': arrow_set['right'],
            
            # Metadata
            'created_at': datetime.utcnow().isoformat(),
            'description': config['description']
        }
        
        return session_data
    
    def _generate_trials(
        self,
        total_trials: int,
        congruent_ratio: float,
        flanker_count: int,
        arrow_set: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Generate sequence of congruent and incongruent trials.
        
        Ensures:
        - Proper ratio of congruent to incongruent
        - No more than 4 consecutive same trial type
        - Balanced left/right target directions
        - Random but controlled sequence
        """
        trials = []
        congruent_count = int(total_trials * congruent_ratio)
        incongruent_count = total_trials - congruent_count
        
        # Create trial pool
        trial_pool = (
            [{'type': 'congruent', 'direction': 'left'}] * (congruent_count // 2) +
            [{'type': 'congruent', 'direction': 'right'}] * (congruent_count - congruent_count // 2) +
            [{'type': 'incongruent', 'direction': 'left'}] * (incongruent_count // 2) +
            [{'type': 'incongruent', 'direction': 'right'}] * (incongruent_count - incongruent_count // 2)
        )
        
        # Shuffle with constraint: no more than 4 consecutive same type
        random.shuffle(trial_pool)
        trial_pool = self._constrain_sequence(trial_pool, max_consecutive=4)
        
        # Build trial objects
        for i, trial_spec in enumerate(trial_pool):
            target_direction = trial_spec['direction']
            trial_type = trial_spec['type']
            
            # Build arrow display
            if trial_type == 'congruent':
                # All arrows point same direction
                if target_direction == 'left':
                    display = arrow_set['left'] * (2 * flanker_count + 1)
                else:
                    display = arrow_set['right'] * (2 * flanker_count + 1)
            else:
                # Incongruent: flankers point opposite direction
                if target_direction == 'left':
                    flanker = arrow_set['right']
                    target = arrow_set['left']
                else:
                    flanker = arrow_set['left']
                    target = arrow_set['right']
                
                display = flanker * flanker_count + target + flanker * flanker_count
            
            trials.append({
                'trial_number': i + 1,
                'trial_type': trial_type,
                'target_direction': target_direction,
                'display': display,
                'flanker_count': flanker_count
            })
        
        return trials
    
    def _constrain_sequence(
        self,
        trial_pool: List[Dict],
        max_consecutive: int = 4
    ) -> List[Dict]:
        """
        Rearrange trials to prevent too many consecutive same trial types.
        """
        result = []
        consecutive_count = 0
        last_type = None
        
        # Sort into buckets
        congruent = [t for t in trial_pool if t['type'] == 'congruent']
        incongruent = [t for t in trial_pool if t['type'] == 'incongruent']
        
        random.shuffle(congruent)
        random.shuffle(incongruent)
        
        # Interleave to avoid long runs
        while congruent or incongruent:
            if not congruent:
                result.append(incongruent.pop(0))
            elif not incongruent:
                result.append(congruent.pop(0))
            else:
                # Check consecutive count
                if last_type and consecutive_count >= max_consecutive:
                    # Force switch
                    if last_type == 'congruent':
                        next_trial = incongruent.pop(0)
                    else:
                        next_trial = congruent.pop(0)
                else:
                    # Random choice
                    if random.random() < 0.5 and congruent:
                        next_trial = congruent.pop(0)
                    else:
                        next_trial = incongruent.pop(0)
                
                # Update consecutive tracking
                if next_trial['type'] == last_type:
                    consecutive_count += 1
                else:
                    consecutive_count = 1
                    last_type = next_trial['type']
                
                result.append(next_trial)
        
        return result
    
    def score_session(
        self,
        session_data: Dict[str, Any],
        responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate performance metrics for Flanker task.
        
        Key Metrics:
        - Overall accuracy and mean RT
        - Congruent trial accuracy and RT
        - Incongruent trial accuracy and RT
        - Flanker/Conflict Effect (Incongruent RT - Congruent RT)
        - Interference error rate
        
        Args:
            session_data: Original session configuration
            responses: List of user responses with RT and direction
        
        Returns:
            Performance metrics and scoring
        """
        # Separate responses by trial type
        congruent_responses = []
        incongruent_responses = []
        
        correct_count = 0
        congruent_correct = 0
        incongruent_correct = 0
        
        congruent_rts = []
        incongruent_rts = []
        all_rts = []
        
        for response in responses:
            trial_num = response['trial_number']
            trial = session_data['trials'][trial_num - 1]
            
            user_direction = response.get('responded_direction') or response.get('direction')
            correct_direction = trial['target_direction']
            rt = response['reaction_time_ms']
            
            is_correct = (user_direction == correct_direction) if user_direction else False
            
            if is_correct:
                correct_count += 1
                all_rts.append(rt)
            
            if trial['trial_type'] == 'congruent':
                congruent_responses.append(response)
                if is_correct:
                    congruent_correct += 1
                    congruent_rts.append(rt)
            else:
                incongruent_responses.append(response)
                if is_correct:
                    incongruent_correct += 1
                    incongruent_rts.append(rt)
        
        # Calculate metrics
        total_trials = len(responses)
        overall_accuracy = (correct_count / total_trials * 100) if total_trials > 0 else 0
        mean_rt = sum(all_rts) / len(all_rts) if all_rts else 0
        
        # Congruent metrics
        congruent_total = len(congruent_responses)
        congruent_accuracy = (congruent_correct / congruent_total * 100) if congruent_total > 0 else 0
        congruent_mean_rt = sum(congruent_rts) / len(congruent_rts) if congruent_rts else 0
        
        # Incongruent metrics
        incongruent_total = len(incongruent_responses)
        incongruent_accuracy = (incongruent_correct / incongruent_total * 100) if incongruent_total > 0 else 0
        incongruent_mean_rt = sum(incongruent_rts) / len(incongruent_rts) if incongruent_rts else 0
        
        # Flanker/Conflict Effect (key measure of selective attention)
        conflict_effect = incongruent_mean_rt - congruent_mean_rt if (congruent_mean_rt > 0 and incongruent_mean_rt > 0) else 0
        
        # Interference error rate (errors on incongruent trials)
        incongruent_errors = incongruent_total - incongruent_correct
        interference_error_rate = (incongruent_errors / incongruent_total * 100) if incongruent_total > 0 else 0
        
        # Calculate performance score (weighted)
        # 40% accuracy, 30% speed, 30% conflict resolution
        normalized_rt = max(0, 100 - (mean_rt / 20)) if mean_rt > 0 else 0
        conflict_control = max(0, 100 - (conflict_effect / 10)) if conflict_effect >= 0 else 100
        performance_score = (overall_accuracy * 0.4) + (normalized_rt * 0.3) + (conflict_control * 0.3)
        
        # Performance level classification
        if performance_score >= 85 and conflict_effect < 100:
            performance_level = "Excellent"
            feedback = "Outstanding selective attention! You effectively filtered flanker interference."
        elif performance_score >= 70 and conflict_effect < 150:
            performance_level = "Good"
            feedback = "Strong conflict resolution with good response speed."
        elif performance_score >= 55 and conflict_effect < 200:
            performance_level = "Fair"
            feedback = "Moderate attention control. Practice helps reduce flanker interference."
        else:
            performance_level = "Needs Practice"
            feedback = "Selective attention challenging. Keep practicing - improvement comes with training!"
        
        return {
            'overall_accuracy': round(overall_accuracy, 2),
            'mean_rt': round(mean_rt, 0),
            'performance_score': round(performance_score, 2),
            'performance_level': performance_level,
            'feedback': feedback,
            
            # Congruent trial metrics
            'congruent_accuracy': round(congruent_accuracy, 2),
            'congruent_mean_rt': round(congruent_mean_rt, 0),
            'congruent_correct': congruent_correct,
            'congruent_errors': congruent_total - congruent_correct,
            
            # Incongruent trial metrics
            'incongruent_accuracy': round(incongruent_accuracy, 2),
            'incongruent_mean_rt': round(incongruent_mean_rt, 0),
            'incongruent_correct': incongruent_correct,
            'incongruent_errors': incongruent_errors,
            
            # Conflict/Interference metrics (KEY measures)
            'conflict_effect_ms': round(conflict_effect, 0),
            'interference_error_rate': round(interference_error_rate, 2),
            
            # Trial counts
            'total_trials': total_trials,
            'total_correct': correct_count,
            'congruent_trials_count': congruent_total,
            'incongruent_trials_count': incongruent_total
        }
    
    def determine_difficulty_adjustment(self, results: Dict[str, Any]) -> int:
        """
        Determine difficulty adjustment based on Flanker performance.
        
        Focus on:
        1. Overall accuracy (primary)
        2. Conflict effect magnitude (key attention measure)
        3. Incongruent trial accuracy (interference resistance)
        4. Response speed
        
        MS-Adapted: Considers that larger conflict effects are normal,
        but should improve with practice.
        """
        overall_accuracy = results['overall_accuracy']
        conflict_effect = results['conflict_effect_ms']
        incongruent_accuracy = results['incongruent_accuracy']
        mean_rt = results['mean_rt']
        
        # Increase difficulty if excellent performance:
        # - High overall accuracy (≥88%) AND
        # - Low conflict effect (<100ms - excellent selective attention) AND
        # - Good incongruent accuracy (≥85%) AND
        # - Fast RT (<700ms)
        if overall_accuracy >= 88 and conflict_effect < 100 and incongruent_accuracy >= 85 and mean_rt < 700:
            return 1
        
        # Strong performance (faster progression):
        # - Very high accuracy (≥92%) AND
        # - Moderate conflict effect (<150ms) AND
        # - Very good incongruent trials (≥88%)
        elif overall_accuracy >= 92 and conflict_effect < 150 and incongruent_accuracy >= 88:
            return 1
        
        # Decrease difficulty if struggling:
        # - Low accuracy (<70%) OR
        # - Very large conflict effect (>300ms - severe interference) OR
        # - Poor incongruent accuracy (<60%) OR
        # - Very slow RT (>1200ms)
        elif overall_accuracy < 70 or conflict_effect > 300 or incongruent_accuracy < 60 or mean_rt > 1200:
            return -1
        
        # Severe difficulty - drop 2 levels:
        # - Very poor accuracy (<60%) OR
        # - Extreme conflict effect (>400ms) OR
        # - Failing incongruent trials (<50%) OR
        # - Extremely slow (>1500ms)
        elif overall_accuracy < 60 or conflict_effect > 400 or incongruent_accuracy < 50 or mean_rt > 1500:
            return -2
        
        return 0

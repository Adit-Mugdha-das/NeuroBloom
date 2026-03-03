"""
Stroop Color-Word Test Service

Clinical Validation: ⭐⭐⭐⭐ Classic Attention/Executive Function Test
Measures: Selective attention, inhibitory control, conflict resolution
MS Relevance: Sensitive to frontal lobe dysfunction, measures cognitive interference

Reference: Parmenter et al., 2007; Stroop, 1935 (original)
"""

from typing import Dict, List, Any, Optional
import random
from datetime import datetime

class StroopTask:
    """
    Stroop Color-Word Test - Name the ink color, ignore the word meaning.
    
    Three conditions:
    1. Color patches (baseline processing speed)
    2. Congruent (word matches color: "RED" in red ink)
    3. Incongruent (word conflicts: "RED" in blue ink) ← KEY MEASURE
    
    Gold standard for measuring cognitive interference and inhibitory control.
    """
    
    # Color sets for different difficulty levels
    BASIC_COLORS = ['red', 'blue', 'green', 'yellow']
    EXTENDED_COLORS = ['red', 'blue', 'green', 'yellow', 'purple']
    FULL_COLORS = ['red', 'blue', 'green', 'yellow', 'purple', 'orange']
    
    # Difficulty levels: 10 levels with varying complexity
    # Presentation time progression: 3000 → 2500 → 2000 → 1900 → 1800 → 1500 → 1400 → 1300 → 1100 → 1000ms
    # All timings research-backed and achievable by healthy adults with practice
    DIFFICULTY_CONFIG = {
        1: {
            "colors": BASIC_COLORS,
            "presentation_time_ms": 3000,
            "trials_per_condition": 8,  # 8 baseline + 8 congruent + 8 incongruent = 24 total
            "response_timeout_ms": 4000,
            "description": "Beginner - 4 colors, plenty of time"
        },
        2: {
            "colors": BASIC_COLORS,
            "presentation_time_ms": 2500,
            "trials_per_condition": 10,
            "response_timeout_ms": 3500,
            "description": "Easy - 4 colors, comfortable pace"
        },
        3: {
            "colors": BASIC_COLORS,
            "presentation_time_ms": 2000,
            "trials_per_condition": 12,
            "response_timeout_ms": 3000,
            "description": "Moderate - 4 colors, standard pace"
        },
        4: {
            "colors": EXTENDED_COLORS,
            "presentation_time_ms": 1900,  # Smooth progression (was 2000ms - removed plateau)
            "trials_per_condition": 12,
            "response_timeout_ms": 2900,
            "description": "Standard - 5 colors, building speed"
        },
        5: {
            "colors": EXTENDED_COLORS,
            "presentation_time_ms": 1800,
            "trials_per_condition": 14,
            "response_timeout_ms": 2500,
            "description": "Intermediate - 5 colors, faster pace"
        },
        6: {
            "colors": EXTENDED_COLORS,
            "presentation_time_ms": 1500,
            "trials_per_condition": 15,
            "response_timeout_ms": 2200,
            "description": "Challenging - 5 colors, quick responses"
        },
        7: {
            "colors": FULL_COLORS,
            "presentation_time_ms": 1400,  # Smooth progression (was 1500ms - removed plateau)
            "trials_per_condition": 15,
            "response_timeout_ms": 2000,
            "description": "Advanced - 6 colors, fast pace"
        },
        8: {
            "colors": FULL_COLORS,
            "presentation_time_ms": 1300,
            "trials_per_condition": 18,
            "response_timeout_ms": 1800,
            "description": "Expert - 6 colors, rapid responses"
        },
        9: {
            "colors": FULL_COLORS,
            "presentation_time_ms": 1100,
            "trials_per_condition": 20,
            "response_timeout_ms": 1600,
            "description": "Master - 6 colors, very fast"
        },
        10: {
            "colors": FULL_COLORS,
            "presentation_time_ms": 1000,
            "trials_per_condition": 22,
            "response_timeout_ms": 1500,
            "description": "Elite - Maximum cognitive interference challenge"
        }
    }
    
    def __init__(self):
        self.session_data = {}
    
    def generate_baseline_trials(self, colors: List[str], num_trials: int) -> List[Dict[str, Any]]:
        """
        Generate baseline color patch trials (no word interference).
        User simply identifies the color of a patch.
        """
        trials = []
        for i in range(num_trials):
            color = random.choice(colors)
            trials.append({
                'trial_number': i + 1,
                'condition': 'baseline',
                'display_color': color,
                'word_text': None,  # No word, just color patch
                'correct_answer': color
            })
        return trials
    
    def generate_congruent_trials(self, colors: List[str], num_trials: int) -> List[Dict[str, Any]]:
        """
        Generate congruent trials (word matches color).
        Example: "RED" displayed in red ink
        """
        trials = []
        for i in range(num_trials):
            color = random.choice(colors)
            trials.append({
                'trial_number': i + 1,
                'condition': 'congruent',
                'display_color': color,
                'word_text': color.upper(),  # Word matches color
                'correct_answer': color
            })
        return trials
    
    def generate_incongruent_trials(self, colors: List[str], num_trials: int) -> List[Dict[str, Any]]:
        """
        Generate incongruent trials (word conflicts with color).
        Example: "RED" displayed in blue ink → Answer: "blue"
        This is the KEY measure of cognitive interference.
        """
        trials = []
        for i in range(num_trials):
            display_color = random.choice(colors)
            # Choose a different word
            available_words = [c for c in colors if c != display_color]
            word_text = random.choice(available_words).upper()
            
            trials.append({
                'trial_number': i + 1,
                'condition': 'incongruent',
                'display_color': display_color,
                'word_text': word_text,
                'correct_answer': display_color  # Answer the INK color, not the word
            })
        return trials
    
    def generate_session(self, difficulty: int = 1) -> Dict[str, Any]:
        """
        Generate a complete Stroop test session with all three conditions.
        Trials are randomized within each block for unpredictability.
        """
        config = self.DIFFICULTY_CONFIG.get(difficulty, self.DIFFICULTY_CONFIG[1])
        colors = config['colors']
        trials_per_condition = config['trials_per_condition']
        
        # Generate all three conditions
        baseline_trials = self.generate_baseline_trials(colors, trials_per_condition)
        congruent_trials = self.generate_congruent_trials(colors, trials_per_condition)
        incongruent_trials = self.generate_incongruent_trials(colors, trials_per_condition)
        
        # Shuffle each block separately
        random.shuffle(baseline_trials)
        random.shuffle(congruent_trials)
        random.shuffle(incongruent_trials)
        
        # Combine all trials (baseline first, then congruent, then incongruent)
        all_trials = baseline_trials + congruent_trials + incongruent_trials
        
        # Re-number trials sequentially
        for idx, trial in enumerate(all_trials):
            trial['trial_number'] = idx + 1
        
        session_data = {
            'difficulty': difficulty,
            'colors': colors,
            'trials': all_trials,
            'total_trials': len(all_trials),
            'presentation_time_ms': config['presentation_time_ms'],
            'response_timeout_ms': config['response_timeout_ms'],
            'trials_per_condition': trials_per_condition,
            'config': config
        }
        
        return session_data
    
    def score_response(self, trial: Dict[str, Any], user_response: str, 
                       reaction_time_ms: int) -> Dict[str, Any]:
        """Score a single trial response."""
        correct = user_response.lower() == trial['correct_answer'].lower()
        
        return {
            'trial_number': trial['trial_number'],
            'condition': trial['condition'],
            'correct': correct,
            'reaction_time_ms': reaction_time_ms,
            'user_response': user_response,
            'correct_answer': trial['correct_answer']
        }
    
    def calculate_condition_metrics(self, responses: List[Dict[str, Any]], 
                                    condition: str) -> Dict[str, float]:
        """Calculate metrics for a specific condition."""
        condition_responses = [r for r in responses if r['condition'] == condition]
        
        if not condition_responses:
            return {
                'accuracy': 0.0,
                'mean_rt': 0.0,
                'median_rt': 0.0,
                'correct_trials': 0,
                'total_trials': 0
            }
        
        correct_responses = [r for r in condition_responses if r['correct']]
        reaction_times = [r['reaction_time_ms'] for r in correct_responses if r['reaction_time_ms'] > 0]
        
        accuracy = (len(correct_responses) / len(condition_responses)) * 100 if condition_responses else 0
        mean_rt = sum(reaction_times) / len(reaction_times) if reaction_times else 0
        
        # Calculate median
        sorted_rts = sorted(reaction_times)
        median_rt = 0
        if sorted_rts:
            mid = len(sorted_rts) // 2
            if len(sorted_rts) % 2 == 0:
                median_rt = (sorted_rts[mid - 1] + sorted_rts[mid]) / 2
            else:
                median_rt = sorted_rts[mid]
        
        return {
            'accuracy': round(accuracy, 2),
            'mean_rt': round(mean_rt, 0),
            'median_rt': round(median_rt, 0),
            'correct_trials': len(correct_responses),
            'total_trials': len(condition_responses)
        }
    
    def score_session(self, session_data: Dict[str, Any], 
                     responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Score complete Stroop session and calculate interference metrics.
        
        Key Metrics:
        1. Baseline accuracy & RT (processing speed without interference)
        2. Congruent accuracy & RT (facilitation effect)
        3. Incongruent accuracy & RT (interference effect)
        4. Stroop Effect: Incongruent RT - Congruent RT
        5. Interference Cost: (Incongruent RT - Baseline RT) / Baseline RT
        """
        # Calculate metrics for each condition
        baseline_metrics = self.calculate_condition_metrics(responses, 'baseline')
        congruent_metrics = self.calculate_condition_metrics(responses, 'congruent')
        incongruent_metrics = self.calculate_condition_metrics(responses, 'incongruent')
        
        # Calculate overall accuracy
        total_correct = sum(1 for r in responses if r['correct'])
        overall_accuracy = (total_correct / len(responses)) * 100 if responses else 0
        
        # Calculate Stroop Effect (classic measure)
        stroop_effect = incongruent_metrics['mean_rt'] - congruent_metrics['mean_rt']
        
        # Calculate Interference Cost (normalized by baseline)
        interference_cost = 0
        if baseline_metrics['mean_rt'] > 0:
            interference_cost = ((incongruent_metrics['mean_rt'] - baseline_metrics['mean_rt']) 
                               / baseline_metrics['mean_rt']) * 100
        
        # Calculate Facilitation Effect (congruent vs baseline)
        facilitation_effect = 0
        if baseline_metrics['mean_rt'] > 0:
            facilitation_effect = baseline_metrics['mean_rt'] - congruent_metrics['mean_rt']
        
        # Calculate consistency (coefficient of variation for incongruent trials)
        incongruent_responses = [r for r in responses if r['condition'] == 'incongruent' and r['correct']]
        incongruent_rts = [r['reaction_time_ms'] for r in incongruent_responses if r['reaction_time_ms'] > 0]
        
        consistency = 100.0
        if len(incongruent_rts) > 1:
            mean_rt = sum(incongruent_rts) / len(incongruent_rts)
            variance = sum((rt - mean_rt) ** 2 for rt in incongruent_rts) / len(incongruent_rts)
            std_dev = variance ** 0.5
            cv = (std_dev / mean_rt) * 100 if mean_rt > 0 else 0
            consistency = max(0, 100 - cv)
        
        # Overall performance score (weighted: accuracy 60%, interference control 40%)
        # Lower interference cost = better inhibitory control
        normalized_interference = max(0, 100 - (interference_cost / 2))  # Normalize to 0-100
        performance_score = (overall_accuracy * 0.6) + (normalized_interference * 0.4)
        
        # Classify performance (with interference cost as secondary criterion)
        # Research-backed: Healthy adults show 20-50% interference cost
        if performance_score >= 85 and interference_cost < 30:
            performance_level = "Excellent"
            feedback = "Outstanding inhibitory control and selective attention!"
        elif performance_score >= 70 and interference_cost < 50:
            performance_level = "Good"
            feedback = "Strong attention control with effective interference management."
        elif performance_score >= 55 and interference_cost < 70:
            performance_level = "Fair"
            feedback = "Moderate interference control. Practice helps improve inhibition."
        else:
            performance_level = "Needs Practice"
            feedback = "Interference affecting performance. Keep practicing - improvement is common!"
        
        return {
            'overall_accuracy': round(overall_accuracy, 2),
            'performance_score': round(performance_score, 2),
            'performance_level': performance_level,
            'feedback': feedback,
            
            # Condition-specific metrics
            'baseline_accuracy': baseline_metrics['accuracy'],
            'baseline_rt': baseline_metrics['mean_rt'],
            'congruent_accuracy': congruent_metrics['accuracy'],
            'congruent_rt': congruent_metrics['mean_rt'],
            'incongruent_accuracy': incongruent_metrics['accuracy'],
            'incongruent_rt': incongruent_metrics['mean_rt'],
            
            # Interference metrics (KEY MEASURES)
            'stroop_effect': round(stroop_effect, 0),  # Incongruent - Congruent RT
            'interference_cost': round(interference_cost, 2),  # % increase from baseline
            'facilitation_effect': round(facilitation_effect, 0),  # Baseline - Congruent RT
            
            # Additional metrics
            'consistency': round(consistency, 2),
            'total_trials': len(responses),
            'correct_trials': total_correct,
            
            # Condition breakdown
            'baseline_trials': baseline_metrics['total_trials'],
            'congruent_trials': congruent_metrics['total_trials'],
            'incongruent_trials': incongruent_metrics['total_trials']
        }
    
    def determine_difficulty_adjustment(self, results: Dict[str, Any]) -> int:
        """
        Determine difficulty adjustment based on performance.
        
        Focus on:
        1. Overall accuracy (primary measure)
        2. Interference cost (cognitive control - research-backed metric)
        3. Incongruent trial accuracy (hardest condition)
        4. Mean RT (cognitive overload detection)

        Research-backed thresholds:
        - Healthy adults: 20-50% interference cost typical
        - Excellent inhibition: <25% interference cost
        - Good inhibition: 25-40% interference cost
        - Struggling: >60% interference cost
        """
        accuracy = results['overall_accuracy']
        interference_cost = results['interference_cost']
        incongruent_accuracy = results['incongruent_accuracy']
        mean_rt = results.get('incongruent_rt', 0)  # Use incongruent RT as primary metric

        # INCREASE +2 (Exceptional performance - rapid progression):
        # - Near-perfect accuracy (≥95%) AND
        # - Excellent interference control (<20% - research elite level) AND
        # - Perfect incongruent trials (≥90%)
        if accuracy >= 95 and interference_cost < 20 and incongruent_accuracy >= 90:
            return 2

        # INCREASE +1 (Strong performance):
        # - High overall accuracy (≥85%) AND
        # - Good interference control (<35% - healthy adult range) AND
        # - Strong incongruent accuracy (≥80%) AND
        # - Reasonable speed (<2500ms - not overthinking)
        if accuracy >= 85 and interference_cost < 35 and incongruent_accuracy >= 80 and mean_rt < 2500:
            return 1

        # INCREASE +1 (Very strong alternative path):
        # - Excellent accuracy (≥92%) AND
        # - Moderate interference (<45%) AND
        # - Very good incongruent (≥85%)
        elif accuracy >= 92 and interference_cost < 45 and incongruent_accuracy >= 85:
            return 1

        # DECREASE -1 (Struggling):
        # - Moderate accuracy issues (<75%) OR
        # - High interference cost (>60% - losing control) OR
        # - Poor incongruent accuracy (<65%) OR
        # - Very slow responses (>3500ms - cognitive overload)
        elif accuracy < 75 or interference_cost > 60 or incongruent_accuracy < 65 or mean_rt > 3500:
            return -1

        # DECREASE -2 (Severe difficulty - needs immediate adjustment):
        # - Very low accuracy (<60%) OR
        # - Extreme interference (>90% - complete loss of inhibition) OR
        # - Failing incongruent trials (<50%) OR
        # - Extremely slow (>5000ms - overwhelmed)
        elif accuracy < 60 or interference_cost > 90 or incongruent_accuracy < 50 or mean_rt > 5000:
            return -2

        # STAY (Performance in acceptable range: 75-85% accuracy, 35-60% interference)
        return 0

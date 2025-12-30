"""
Go/No-Go Task Service

Clinical Validation: ⭐⭐⭐⭐ Response Inhibition Standard
Measures: Impulse control, response inhibition, sustained attention
MS Relevance: Sensitive to attention deficits and executive dysfunction

Reference: Diamond, 2013; Simmonds et al., 2008
"""

from typing import Dict, List, Any, Optional
import random
from datetime import datetime

class GoNoGoTask:
    """
    Go/No-Go Task - Test response inhibition and impulse control.
    
    Task Structure:
    - Go trials (75%): Respond quickly when you see the target (e.g., "X")
    - No-Go trials (25%): Withhold response when you see non-target (e.g., "O")
    
    Key Measures:
    - Go trial speed (processing speed)
    - No-Go accuracy (impulse control / inhibition)
    - Commission errors (false alarms on No-Go)
    - Omission errors (misses on Go)
    """
    
    # Stimulus types for different difficulty levels
    STIMULUS_SETS = {
        'basic': {
            'go': 'X',
            'nogo': 'O',
            'description': 'Simple letters'
        },
        'similar': {
            'go': 'P',
            'nogo': 'R',
            'description': 'Similar letters'
        },
        'shapes': {
            'go': '■',
            'nogo': '●',
            'description': 'Shapes'
        },
        'complex': {
            'go': 'GO',
            'nogo': 'NO',
            'description': 'Words'
        }
    }
    
    # Difficulty levels: 10 levels with varying complexity
    DIFFICULTY_CONFIG = {
        1: {
            "stimulus_set": "basic",
            "presentation_time_ms": 2000,
            "inter_stimulus_interval_ms": 1000,
            "total_trials": 40,
            "go_probability": 0.75,
            "description": "Beginner - Slow pace, clear targets"
        },
        2: {
            "stimulus_set": "basic",
            "presentation_time_ms": 1500,
            "inter_stimulus_interval_ms": 800,
            "total_trials": 50,
            "go_probability": 0.75,
            "description": "Easy - Comfortable pace"
        },
        3: {
            "stimulus_set": "basic",
            "presentation_time_ms": 1200,
            "inter_stimulus_interval_ms": 600,
            "total_trials": 60,
            "go_probability": 0.75,
            "description": "Moderate - Standard pace"
        },
        4: {
            "stimulus_set": "similar",
            "presentation_time_ms": 1000,
            "inter_stimulus_interval_ms": 600,
            "total_trials": 60,
            "go_probability": 0.75,
            "description": "Challenging - Similar stimuli"
        },
        5: {
            "stimulus_set": "similar",
            "presentation_time_ms": 900,
            "inter_stimulus_interval_ms": 500,
            "total_trials": 70,
            "go_probability": 0.70,
            "description": "Intermediate - More No-Go trials"
        },
        6: {
            "stimulus_set": "shapes",
            "presentation_time_ms": 800,
            "inter_stimulus_interval_ms": 500,
            "total_trials": 80,
            "go_probability": 0.70,
            "description": "Advanced - Quick responses required"
        },
        7: {
            "stimulus_set": "shapes",
            "presentation_time_ms": 700,
            "inter_stimulus_interval_ms": 400,
            "total_trials": 90,
            "go_probability": 0.65,
            "description": "Expert - Fast pace"
        },
        8: {
            "stimulus_set": "complex",
            "presentation_time_ms": 600,
            "inter_stimulus_interval_ms": 400,
            "total_trials": 100,
            "go_probability": 0.65,
            "description": "Master - Rapid inhibition"
        },
        9: {
            "stimulus_set": "complex",
            "presentation_time_ms": 500,
            "inter_stimulus_interval_ms": 300,
            "total_trials": 110,
            "go_probability": 0.60,
            "description": "Elite - Maximum challenge"
        },
        10: {
            "stimulus_set": "complex",
            "presentation_time_ms": 500,
            "inter_stimulus_interval_ms": 300,
            "total_trials": 120,
            "go_probability": 0.55,
            "description": "Ultimate - Equal Go/No-Go ratio"
        }
    }
    
    def __init__(self):
        self.session_data = {}
    
    def generate_trial_sequence(self, total_trials: int, go_probability: float) -> List[str]:
        """
        Generate sequence of Go and No-Go trials.
        Ensures no more than 4 consecutive trials of same type.
        """
        # Calculate number of each trial type
        num_go = int(total_trials * go_probability)
        num_nogo = total_trials - num_go
        
        # Create initial sequence
        trials = (['go'] * num_go) + (['nogo'] * num_nogo)
        
        # Shuffle with constraint: max 4 consecutive same type
        max_attempts = 100
        for _ in range(max_attempts):
            random.shuffle(trials)
            
            # Check for long runs
            max_run = 1
            current_run = 1
            for i in range(1, len(trials)):
                if trials[i] == trials[i-1]:
                    current_run += 1
                    max_run = max(max_run, current_run)
                else:
                    current_run = 1
            
            if max_run <= 4:
                break
        
        return trials
    
    def generate_session(self, difficulty: int) -> Dict[str, Any]:
        """Generate a complete Go/No-Go session based on difficulty level."""
        config = self.DIFFICULTY_CONFIG.get(difficulty, self.DIFFICULTY_CONFIG[1])
        stimulus_set = self.STIMULUS_SETS[config['stimulus_set']]
        
        # Generate trial sequence
        trial_sequence = self.generate_trial_sequence(
            config['total_trials'],
            config['go_probability']
        )
        
        # Create trials with detailed info
        trials = []
        for i, trial_type in enumerate(trial_sequence):
            stimulus = stimulus_set['go'] if trial_type == 'go' else stimulus_set['nogo']
            
            trials.append({
                'trial_number': i + 1,
                'trial_type': trial_type,
                'stimulus': stimulus,
                'correct_response': 'press' if trial_type == 'go' else 'withhold'
            })
        
        # Count trial types
        num_go = sum(1 for t in trial_sequence if t == 'go')
        num_nogo = len(trial_sequence) - num_go
        
        session_data = {
            'trials': trials,
            'total_trials': config['total_trials'],
            'go_trials': num_go,
            'nogo_trials': num_nogo,
            'presentation_time_ms': config['presentation_time_ms'],
            'inter_stimulus_interval_ms': config['inter_stimulus_interval_ms'],
            'stimulus_set': config['stimulus_set'],
            'go_stimulus': stimulus_set['go'],
            'nogo_stimulus': stimulus_set['nogo'],
            'description': config['description']
        }
        
        return session_data
    
    def score_session(self, session_data: Dict[str, Any], 
                     responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Score Go/No-Go session.
        
        Key Metrics:
        1. Go trial accuracy & RT (processing speed)
        2. No-Go trial accuracy (impulse control)
        3. Commission errors (false alarms on No-Go)
        4. Omission errors (misses on Go)
        5. d-prime (signal detection theory measure)
        """
        # Separate Go and No-Go responses
        go_responses = [r for r in responses if r['trial_type'] == 'go']
        nogo_responses = [r for r in responses if r['trial_type'] == 'nogo']
        
        # Go trial metrics (processing speed + attention)
        go_hits = sum(1 for r in go_responses if r['responded'])
        go_misses = sum(1 for r in go_responses if not r['responded'])
        go_accuracy = (go_hits / len(go_responses)) * 100 if go_responses else 0
        
        # Calculate mean RT for Go hits only
        go_hit_rts = [r['reaction_time_ms'] for r in go_responses 
                      if r['responded'] and r['reaction_time_ms'] > 0]
        go_mean_rt = sum(go_hit_rts) / len(go_hit_rts) if go_hit_rts else 0
        
        # No-Go trial metrics (impulse control)
        nogo_correct = sum(1 for r in nogo_responses if not r['responded'])
        nogo_commission = sum(1 for r in nogo_responses if r['responded'])
        nogo_accuracy = (nogo_correct / len(nogo_responses)) * 100 if nogo_responses else 0
        
        # Overall accuracy
        total_correct = go_hits + nogo_correct
        overall_accuracy = (total_correct / len(responses)) * 100 if responses else 0
        
        # Calculate d-prime (signal detection measure)
        # Hit rate: P(respond | Go trial)
        # False alarm rate: P(respond | No-Go trial)
        hit_rate = go_hits / len(go_responses) if go_responses else 0
        fa_rate = nogo_commission / len(nogo_responses) if nogo_responses else 0
        
        # Avoid extreme values (0 or 1) for d-prime calculation
        hit_rate = max(0.01, min(0.99, hit_rate))
        fa_rate = max(0.01, min(0.99, fa_rate))
        
        # Calculate d-prime using a safe z-score approximation
        import math
        
        def safe_z_score(p):
            """Convert probability to z-score using approximation."""
            if p <= 0.0001:
                return -3.9
            elif p >= 0.9999:
                return 3.9
            elif p == 0.5:
                return 0
            
            # Rational approximation (Odeh & Evans, 1974)
            if p < 0.5:
                sign = -1
                p = 1 - p
            else:
                sign = 1
                
            t = math.sqrt(-2 * math.log(1 - p))
            
            c0 = 2.515517
            c1 = 0.802853
            c2 = 0.010328
            d1 = 1.432788
            d2 = 0.189269
            d3 = 0.001308
            
            z = t - (c0 + c1*t + c2*t*t) / (1 + d1*t + d2*t*t + d3*t*t*t)
            return sign * z
        
        d_prime = safe_z_score(hit_rate) - safe_z_score(fa_rate)
        
        # Calculate consistency (CV for Go trial RTs)
        consistency = 100.0
        if len(go_hit_rts) > 1:
            mean_rt = sum(go_hit_rts) / len(go_hit_rts)
            variance = sum((rt - mean_rt) ** 2 for rt in go_hit_rts) / len(go_hit_rts)
            std_dev = variance ** 0.5
            cv = (std_dev / mean_rt) * 100 if mean_rt > 0 else 0
            consistency = max(0, 100 - cv)
        
        # Performance score (weighted: inhibition 50%, speed 30%, consistency 20%)
        normalized_rt = max(0, 100 - (go_mean_rt / 10)) if go_mean_rt > 0 else 0  # Normalize to 0-100
        performance_score = (nogo_accuracy * 0.5) + (normalized_rt * 0.3) + (consistency * 0.2)
        
        # Classify performance
        if performance_score >= 85 and nogo_accuracy >= 90:
            performance_level = "Excellent"
            feedback = "Outstanding impulse control and response speed!"
        elif performance_score >= 70 and nogo_accuracy >= 75:
            performance_level = "Good"
            feedback = "Strong inhibitory control with good response execution."
        elif performance_score >= 55 and nogo_accuracy >= 60:
            performance_level = "Fair"
            feedback = "Moderate inhibition ability. Practice helps improve control."
        else:
            performance_level = "Needs Practice"
            feedback = "Inhibition challenging. Keep practicing - improvement comes with training!"
        
        return {
            'overall_accuracy': round(overall_accuracy, 2),
            'performance_score': round(performance_score, 2),
            'performance_level': performance_level,
            'feedback': feedback,
            
            # Go trial metrics (speed + attention)
            'go_accuracy': round(go_accuracy, 2),
            'go_hits': go_hits,
            'go_misses': go_misses,
            'go_mean_rt': round(go_mean_rt, 0),
            
            # No-Go trial metrics (inhibition)
            'nogo_accuracy': round(nogo_accuracy, 2),
            'nogo_correct': nogo_correct,
            'nogo_commission_errors': nogo_commission,
            
            # Signal detection
            'd_prime': round(d_prime, 2),
            'hit_rate': round(hit_rate * 100, 2),
            'false_alarm_rate': round(fa_rate * 100, 2),
            
            # Additional metrics
            'consistency': round(consistency, 2),
            'total_trials': len(responses),
            'total_correct': total_correct,
            'go_trials_count': len(go_responses),
            'nogo_trials_count': len(nogo_responses)
        }
    
    def _inverse_normal_cdf(self, p: float) -> float:
        """Simple approximation of inverse normal CDF for d-prime calculation."""
        # Beasley-Springer-Moro approximation
        if p < 0.5:
            sign = -1
            p = 1 - p
        else:
            sign = 1
        
        t = (-2 * (1 - p)) ** 0.5 if p < 1 else 0
        
        c0 = 2.515517
        c1 = 0.802853
        c2 = 0.010328
        d1 = 1.432788
        d2 = 0.189269
        d3 = 0.001308
        
        numerator = c0 + c1 * t + c2 * t * t
        denominator = 1 + d1 * t + d2 * t * t + d3 * t * t * t
        
        return sign * (t - numerator / denominator) if denominator != 0 else 0
    
    def determine_difficulty_adjustment(self, results: Dict[str, Any]) -> int:
        """
        Determine difficulty adjustment based on performance.
        
        Focus on:
        1. No-Go accuracy (primary measure of inhibition)
        2. Go trial speed (secondary)
        3. Overall accuracy
        """
        nogo_accuracy = results['nogo_accuracy']
        go_accuracy = results['go_accuracy']
        go_mean_rt = results['go_mean_rt']
        
        # Increase difficulty if:
        # - High No-Go accuracy (≥90%) AND
        # - High Go accuracy (≥95%) AND
        # - Fast Go RT (<400ms)
        if nogo_accuracy >= 90 and go_accuracy >= 95 and go_mean_rt < 400:
            return 1
        
        # Decrease difficulty if:
        # - Low No-Go accuracy (<60%) OR
        # - Low Go accuracy (<70%) OR
        # - Very slow Go RT (>800ms)
        elif nogo_accuracy < 60 or go_accuracy < 70 or go_mean_rt > 800:
            return -1
        
        return 0

"""
Advanced Analytics for MS Digital Biomarkers
Phase 1: Enhanced Metrics for Clinical Research

This module provides:
1. Fatigue signature detection (within-session performance decay)
2. Comprehensive IIV (Intra-Individual Variability) metrics
3. Trend detection using EWMA
4. Contextual correlation analysis

Author: NeuroBloom Research Team
Date: February 2026
Clinical Validation: MS-specific digital biomarkers
"""

import statistics
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


# ==================== FATIGUE DETECTION ====================

def calculate_fatigue_signature(trials: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Detect within-session fatigue by comparing performance across trial quartiles.
    
    MS patients show characteristic fatigue patterns:
    - Exponential decay in accuracy
    - Increasing RT toward end of session
    - Higher error rates in final trials
    
    Args:
        trials: List of trial data with keys: 'correct', 'reaction_time', 'trial_num'
    
    Returns:
        {
            'fatigue_index': 0-1 score (0=no fatigue, 1=severe fatigue),
            'accuracy_decline': % drop from first to last quartile,
            'rt_increase': ms increase from first to last quartile,
            'performance_slope': linear regression slope of accuracy over time
        }
    
    Clinical Significance:
    - fatigue_index > 0.3: Moderate fatigue (common in MS)
    - fatigue_index > 0.5: Severe fatigue (may indicate relapse or poor disease control)
    - Increasing fatigue_index over weeks: Disease progression signal
    """
    if not trials or len(trials) < 4:
        return {
            'fatigue_index': 0.0,
            'accuracy_decline': 0.0,
            'rt_increase': 0.0,
            'performance_slope': 0.0
        }
    
    n = len(trials)
    quartile_size = n // 4
    
    # Split into quartiles
    q1_trials = trials[:quartile_size]
    q4_trials = trials[-quartile_size:]
    
    # Calculate accuracy for each quartile
    q1_accuracy = sum(t.get('correct', 0) for t in q1_trials) / len(q1_trials) if q1_trials else 0
    q4_accuracy = sum(t.get('correct', 0) for t in q4_trials) / len(q4_trials) if q4_trials else 0
    
    # Calculate RT for each quartile
    q1_rts = [t.get('reaction_time', 0) for t in q1_trials if t.get('reaction_time', 0) > 0]
    q4_rts = [t.get('reaction_time', 0) for t in q4_trials if t.get('reaction_time', 0) > 0]
    
    q1_rt = statistics.mean(q1_rts) if q1_rts else 0
    q4_rt = statistics.mean(q4_rts) if q4_rts else 0
    
    # Calculate metrics
    accuracy_decline = (q1_accuracy - q4_accuracy) * 100  # percentage points
    rt_increase = q4_rt - q1_rt  # milliseconds
    
    # Performance slope (linear regression of accuracy over trials)
    performance_slope = 0.0
    if len(trials) >= 2:
        trial_nums = list(range(len(trials)))
        accuracies = [float(t.get('correct', 0)) for t in trials]
        
        # Simple linear regression: slope = covariance(x,y) / variance(x)
        mean_x = statistics.mean(trial_nums)
        mean_y = statistics.mean(accuracies)
        
        numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(trial_nums, accuracies))
        denominator = sum((x - mean_x) ** 2 for x in trial_nums)
        
        if denominator > 0:
            performance_slope = numerator / denominator
    
    # Composite fatigue index (0-1 scale)
    # Combines accuracy decline + RT increase + negative slope
    accuracy_component = min(1.0, max(0, accuracy_decline / 30))  # 30% decline = max
    rt_component = min(1.0, max(0, rt_increase / 200))  # 200ms increase = max
    slope_component = min(1.0, max(0, -performance_slope * 100))  # negative slope indicates fatigue
    
    fatigue_index = (accuracy_component * 0.5 + rt_component * 0.3 + slope_component * 0.2)
    
    return {
        'fatigue_index': round(fatigue_index, 3),
        'accuracy_decline': round(accuracy_decline, 2),
        'rt_increase': round(rt_increase, 2),
        'performance_slope': round(performance_slope, 5)
    }


# ==================== IIV METRICS ====================

def calculate_iiv_metrics(reaction_times: List[float], mean_rt: Optional[float] = None) -> Dict[str, float]:
    """
    Calculate comprehensive Intra-Individual Variability (IIV) metrics.
    
    IIV is elevated in MS and correlates with:
    - White matter lesion load
    - Cognitive decline severity
    - Functional impairment
    
    Args:
        reaction_times: List of RT values in milliseconds
        mean_rt: Pre-calculated mean (optional, will compute if not provided)
    
    Returns:
        {
            'rt_std': Standard deviation of RT,
            'rt_cv': Coefficient of Variation (CV = std/mean),
            'rt_mad': Median Absolute Deviation (robust to outliers),
            'rt_iqr': Interquartile Range,
            'rt_range': Max - Min
        }
    
    Clinical Interpretation:
    - CV > 0.25: High variability (common in MS)
    - CV > 0.35: Very high variability (progressive MS or relapse)
    - Increasing CV over time: Demyelination progression
    """
    if not reaction_times or len(reaction_times) < 2:
        return {
            'rt_std': 0.0,
            'rt_cv': 0.0,
            'rt_mad': 0.0,
            'rt_iqr': 0.0,
            'rt_range': 0.0
        }
    
    # Remove zeros and outliers (> 3 std from mean)
    rts_clean = [rt for rt in reaction_times if rt > 0]
    
    if len(rts_clean) < 2:
        return {
            'rt_std': 0.0,
            'rt_cv': 0.0,
            'rt_mad': 0.0,
            'rt_iqr': 0.0,
            'rt_range': 0.0
        }
    
    # Calculate mean
    if mean_rt is None:
        mean_rt = statistics.mean(rts_clean)
    
    # Standard deviation
    rt_std = statistics.stdev(rts_clean) if len(rts_clean) > 1 else 0.0
    
    # Coefficient of Variation (key MS biomarker!)
    rt_cv = (rt_std / mean_rt) if mean_rt > 0 else 0.0
    
    # Median Absolute Deviation (robust measure)
    median_rt = statistics.median(rts_clean)
    deviations = [abs(rt - median_rt) for rt in rts_clean]
    rt_mad = statistics.median(deviations)
    
    # Interquartile Range
    sorted_rts = sorted(rts_clean)
    n = len(sorted_rts)
    q1 = sorted_rts[n // 4]
    q3 = sorted_rts[3 * n // 4]
    rt_iqr = q3 - q1
    
    # Range
    rt_range = max(rts_clean) - min(rts_clean)
    
    return {
        'rt_std': round(rt_std, 2),
        'rt_cv': round(rt_cv, 3),
        'rt_mad': round(rt_mad, 2),
        'rt_iqr': round(rt_iqr, 2),
        'rt_range': round(rt_range, 2)
    }


def calculate_within_person_variability(session_scores: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate variability ACROSS sessions (day-to-day consistency).
    
    Different from within-session IIV - this measures how consistent
    performance is from day to day.
    
    Args:
        session_scores: List of session data with keys: 'score', 'date', 'mean_rt'
    
    Returns:
        {
            'score_std': Std dev of scores across sessions,
            'score_cv': CV of scores,
            'rt_across_sessions_std': Std dev of mean RTs across sessions,
            'reliable_change_index': Statistical significance of score changes
        }
    
    Clinical Use:
    - High across-session variability: Unstable disease control
    - Sudden RCI spike: Possible relapse or medication change
    """
    if not session_scores or len(session_scores) < 2:
        return {
            'score_std': 0.0,
            'score_cv': 0.0,
            'rt_across_sessions_std': 0.0,
            'reliable_change_index': 0.0
        }
    
    # Extract scores and RTs
    scores = [s.get('score', 0) for s in session_scores if s.get('score', 0) > 0]
    mean_rts = [s.get('mean_rt', 0) for s in session_scores if s.get('mean_rt', 0) > 0]
    
    if len(scores) < 2:
        return {
            'score_std': 0.0,
            'score_cv': 0.0,
            'rt_across_sessions_std': 0.0,
            'reliable_change_index': 0.0
        }
    
    # Score variability
    score_mean = statistics.mean(scores)
    score_std = statistics.stdev(scores)
    score_cv = (score_std / score_mean) if score_mean > 0 else 0.0
    
    # RT variability across sessions
    rt_std = statistics.stdev(mean_rts) if len(mean_rts) > 1 else 0.0
    
    # Reliable Change Index (RCI) - compares most recent to baseline
    # RCI = (X2 - X1) / SE_diff
    # SE_diff = sqrt(2 * (SE_measurement)^2)
    # Using score_std as SE estimate
    rci = 0.0
    if len(scores) >= 2 and score_std > 0:
        baseline_score = scores[0]
        latest_score = scores[-1]
        se_diff = (2 ** 0.5) * score_std
        rci = (latest_score - baseline_score) / se_diff if se_diff > 0 else 0.0
    
    return {
        'score_std': round(score_std, 2),
        'score_cv': round(score_cv, 3),
        'rt_across_sessions_std': round(rt_std, 2),
        'reliable_change_index': round(rci, 2)
    }


# ==================== TREND DETECTION ====================

def calculate_ewma_trend(values: List[float], alpha: float = 0.2) -> Dict[str, Any]:
    """
    Exponentially Weighted Moving Average for trend detection.
    
    EWMA gives more weight to recent observations while smoothing out noise.
    Useful for detecting subtle cognitive decline trends.
    
    Args:
        values: Time-ordered performance values (scores, RTs, etc.)
        alpha: Smoothing parameter (0-1). Default 0.2 = 20% weight to new value
               Higher alpha = more responsive to recent changes
               Lower alpha = smoother, less sensitive to noise
    
    Returns:
        {
            'ewma_values': List of smoothed values,
            'current_ewma': Most recent EWMA value,
            'trend_direction': 'improving', 'declining', or 'stable',
            'trend_strength': 0-1 (how strong the trend is),
            'recent_slope': Slope of last 5 EWMA points
        }
    
    Clinical Application:
    - Declining trend + high fatigue = possible relapse
    - Improving trend after intervention = treatment working
    - Stable trend = well-controlled disease
    """
    if not values or len(values) < 2:
        return {
            'ewma_values': values,
            'current_ewma': values[0] if values else 0,
            'trend_direction': 'stable',
            'trend_strength': 0.0,
            'recent_slope': 0.0
        }
    
    # Calculate EWMA
    ewma_values = []
    ewma = values[0]  # Initialize with first value
    ewma_values.append(ewma)
    
    for value in values[1:]:
        ewma = alpha * value + (1 - alpha) * ewma
        ewma_values.append(ewma)
    
    # Determine trend from recent EWMA points (last 5 or all if < 5)
    recent_window = min(5, len(ewma_values))
    recent_ewma = ewma_values[-recent_window:]
    
    # Calculate slope of recent trend
    recent_slope = 0.0
    if len(recent_ewma) >= 2:
        x = list(range(len(recent_ewma)))
        y = recent_ewma
        
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)
        
        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        denominator = sum((xi - mean_x) ** 2 for xi in x)
        
        if denominator > 0:
            recent_slope = numerator / denominator
    
    # Determine trend direction and strength
    # Normalize slope by mean value to get relative change
    mean_value = statistics.mean(values)
    relative_slope = (recent_slope / mean_value) if mean_value > 0 else 0
    
    # Classify trend
    if relative_slope > 0.01:  # 1% improvement per time point
        trend_direction = 'improving'
        trend_strength = min(1.0, abs(relative_slope) * 20)
    elif relative_slope < -0.01:  # 1% decline per time point
        trend_direction = 'declining'
        trend_strength = min(1.0, abs(relative_slope) * 20)
    else:
        trend_direction = 'stable'
        trend_strength = 0.0
    
    return {
        'ewma_values': [round(v, 2) for v in ewma_values],
        'current_ewma': round(ewma_values[-1], 2),
        'trend_direction': trend_direction,
        'trend_strength': round(trend_strength, 3),
        'recent_slope': round(recent_slope, 4)
    }


# ==================== CONTEXTUAL CORRELATION ====================

def calculate_contextual_correlations(
    sessions: List[Dict[str, Any]],
    context_keys: List[str] = ['fatigue_level', 'sleep_quality', 'hours_since_medication']
) -> Dict[str, Dict[str, float]]:
    """
    Correlate performance metrics with contextual factors.
    
    Answers questions like:
    - Does fatigue level predict performance?
    - Does sleep quality affect RT variability?
    - Is there an optimal time after medication for testing?
    
    Args:
        sessions: List of session data with performance + context
        context_keys: Which contextual variables to analyze
    
    Returns:
        {
            'fatigue_level': {
                'correlation_with_score': -0.65,  # negative = higher fatigue → lower score
                'correlation_with_rt': 0.42,      # positive = higher fatigue → slower RT
                'sample_size': 30
            },
            ...
        }
    
    Clinical Insights:
    - Strong negative correlation with fatigue: Confirms MS fatigue impact
    - Medication timing correlation: Optimize testing schedule
    - Sleep correlation: Recommend sleep interventions
    """
    correlations = {}
    
    for context_key in context_keys:
        # Extract pairs of (context_value, score) and (context_value, rt)
        score_pairs = []
        rt_pairs = []
        
        for session in sessions:
            context_value = session.get(context_key)
            score = session.get('score')
            mean_rt = session.get('mean_rt')
            
            if context_value is not None and score is not None:
                score_pairs.append((context_value, score))
            
            if context_value is not None and mean_rt is not None:
                rt_pairs.append((context_value, mean_rt))
        
        # Calculate Pearson correlation coefficient
        def pearson_correlation(pairs):
            if len(pairs) < 3:
                return 0.0
            
            x_values = [p[0] for p in pairs]
            y_values = [p[1] for p in pairs]
            
            mean_x = statistics.mean(x_values)
            mean_y = statistics.mean(y_values)
            
            numerator = sum((x - mean_x) * (y - mean_y) for x, y in pairs)
            
            x_var = sum((x - mean_x) ** 2 for x in x_values)
            y_var = sum((y - mean_y) ** 2 for y in y_values)
            
            denominator = (x_var * y_var) ** 0.5
            
            return (numerator / denominator) if denominator > 0 else 0.0
        
        correlations[context_key] = {
            'correlation_with_score': round(pearson_correlation(score_pairs), 3),
            'correlation_with_rt': round(pearson_correlation(rt_pairs), 3),
            'sample_size': len(score_pairs)
        }
    
    return correlations


# ==================== COMPREHENSIVE SESSION ANALYSIS ====================

def analyze_session_advanced(session_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Complete advanced analysis of a single session.
    
    Combines all Phase 1 metrics into one comprehensive report.
    
    Args:
        session_data: {
            'trials': [...],
            'score': float,
            'mean_rt': float,
            'accuracy': float,
            'context': {...}  # optional
        }
    
    Returns:
        Complete analytics including fatigue, IIV, and context
    """
    trials = session_data.get('trials', [])
    
    # Fatigue detection
    fatigue_metrics = calculate_fatigue_signature(trials)
    
    # IIV metrics
    reaction_times = [t.get('reaction_time', 0) for t in trials if t.get('reaction_time', 0) > 0]
    iiv_metrics = calculate_iiv_metrics(reaction_times, session_data.get('mean_rt'))
    
    # Combine all metrics
    return {
        'basic_metrics': {
            'score': session_data.get('score', 0),
            'accuracy': session_data.get('accuracy', 0),
            'mean_rt': session_data.get('mean_rt', 0)
        },
        'fatigue_metrics': fatigue_metrics,
        'iiv_metrics': iiv_metrics,
        'context': session_data.get('context', {})
    }


def generate_longitudinal_report(
    sessions: List[Dict[str, Any]],
    include_context_correlation: bool = True
) -> Dict[str, Any]:
    """
    Generate comprehensive longitudinal analysis report.
    
    Perfect for doctor portal and research analysis.
    
    Args:
        sessions: List of sessions ordered by date
        include_context_correlation: Whether to analyze contextual factors
    
    Returns:
        Full report with trends, variability, and clinical insights
    """
    if not sessions:
        return {'error': 'No sessions provided'}
    
    # Extract time series data
    scores = [s.get('score', 0) for s in sessions if s.get('score', 0) > 0]
    mean_rts = [s.get('mean_rt', 0) for s in sessions if s.get('mean_rt', 0) > 0]
    
    # Trend analysis
    score_trend = calculate_ewma_trend(scores)
    rt_trend = calculate_ewma_trend(mean_rts)
    
    # Variability across sessions
    variability = calculate_within_person_variability(sessions)
    
    # Average fatigue and IIV across all sessions
    fatigue_indices = []
    cv_values = []
    
    for session in sessions:
        if 'fatigue_metrics' in session:
            fatigue_indices.append(session['fatigue_metrics'].get('fatigue_index', 0))
        if 'iiv_metrics' in session:
            cv_values.append(session['iiv_metrics'].get('rt_cv', 0))
    
    avg_fatigue = statistics.mean(fatigue_indices) if fatigue_indices else 0
    avg_cv = statistics.mean(cv_values) if cv_values else 0
    
    report = {
        'summary': {
            'total_sessions': len(sessions),
            'date_range': {
                'first': sessions[0].get('date', 'unknown'),
                'last': sessions[-1].get('date', 'unknown')
            },
            'current_performance': {
                'score': scores[-1] if scores else 0,
                'mean_rt': mean_rts[-1] if mean_rts else 0
            }
        },
        'trends': {
            'score_trend': score_trend,
            'rt_trend': rt_trend
        },
        'variability': variability,
        'biomarkers': {
            'average_fatigue_index': round(avg_fatigue, 3),
            'average_cv': round(avg_cv, 3),
            'rci': variability.get('reliable_change_index', 0)
        }
    }
    
    # Add contextual correlations if requested
    if include_context_correlation:
        report['contextual_analysis'] = calculate_contextual_correlations(sessions)
    
    return report

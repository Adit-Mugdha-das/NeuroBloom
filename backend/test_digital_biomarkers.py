"""
Test Script: Digital Biomarkers Verification
=============================================
Run this to verify all 5 biomarkers are working correctly.

Usage:
    cd NeuroBloom/backend
    python test_digital_biomarkers.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.advanced_analytics import (
    calculate_fatigue_signature,
    calculate_iiv_metrics,
    calculate_within_person_variability,
    calculate_ewma_trend,
    calculate_contextual_correlations,
    analyze_session_advanced,
    generate_longitudinal_report
)

PASS = "✅ PASS"
FAIL = "❌ FAIL"


# ─────────────────────────────────────────────
# MOCK DATA
# ─────────────────────────────────────────────

def make_trials(start_accuracy=0.95, end_accuracy=0.65, n=40):
    """Simulate a session where patient starts strong and fatigues."""
    trials = []
    for i in range(n):
        progress = i / n  # 0.0 → 1.0
        accuracy = start_accuracy - (start_accuracy - end_accuracy) * progress
        rt = 500 + (progress * 300)  # RT increases from 500ms to 800ms
        trials.append({
            'trial_num': i,
            'correct': 1 if progress < accuracy else 0,
            'reaction_time': rt
        })
    return trials


def make_sessions(trend="improving", n=10):
    """Simulate multiple sessions with a trend over time."""
    sessions = []
    for i in range(n):
        if trend == "improving":
            score = 50 + (i * 3)         # goes from 50 → 77
            mean_rt = 700 - (i * 15)     # gets faster
            fatigue_idx = 0.5 - (i * 0.02)
        elif trend == "declining":
            score = 80 - (i * 4)         # goes from 80 → 44
            mean_rt = 500 + (i * 20)     # gets slower
            fatigue_idx = 0.2 + (i * 0.04)
        else:  # stable
            score = 65
            mean_rt = 600
            fatigue_idx = 0.3

        sessions.append({
            'score': score,
            'mean_rt': mean_rt,
            'date': f"2026-02-{i+1:02d}",
            'fatigue_metrics': {'fatigue_index': fatigue_idx},
            'iiv_metrics': {'rt_cv': 0.3},
            'fatigue_level': 8 - i,        # context: fatigue decreasing (improving condition)
            'sleep_quality': 5 + (i * 0.3),
            'hours_since_medication': 3 + (i * 0.2)
        })
    return sessions


# ─────────────────────────────────────────────
# TEST 1: FATIGUE INDEX
# ─────────────────────────────────────────────

def test_fatigue_index():
    print("\n" + "─" * 50)
    print("TEST 1: Fatigue Index")
    print("─" * 50)

    # Patient who fatigues heavily
    tired_trials = make_trials(start_accuracy=0.95, end_accuracy=0.55)
    result = calculate_fatigue_signature(tired_trials)

    print(f"  Fatigue Index   : {result['fatigue_index']}  (expected > 0.3)")
    print(f"  Accuracy Decline: {result['accuracy_decline']:.1f}%")
    print(f"  RT Increase     : {result['rt_increase']:.0f}ms")
    print(f"  Perf Slope      : {result['performance_slope']:.4f}")

    ok = result['fatigue_index'] > 0.3
    print(f"\n  Result: {PASS if ok else FAIL}")

    # Patient who does NOT fatigue (consistent correct responses throughout)
    fresh_trials = [
        {'trial_num': i, 'correct': 1, 'reaction_time': 500 + (i % 5) * 3}
        for i in range(40)
    ]
    result2 = calculate_fatigue_signature(fresh_trials)
    print(f"\n  No-fatigue Index: {result2['fatigue_index']}  (expected < 0.2)")
    ok2 = result2['fatigue_index'] < 0.2
    print(f"  Result: {PASS if ok2 else FAIL}")

    return ok and ok2


# ─────────────────────────────────────────────
# TEST 2: COEFFICIENT OF VARIATION (CV)
# ─────────────────────────────────────────────

def test_cv():
    print("\n" + "─" * 50)
    print("TEST 2: Coefficient of Variation (CV)")
    print("─" * 50)

    # Erratic RT (MS-like)
    erratic_rts = [500, 900, 450, 1100, 520, 980, 430, 870]
    result = calculate_iiv_metrics(erratic_rts)
    print(f"  Erratic RTs CV  : {result['rt_cv']}  (expected > 0.25)")
    ok1 = result['rt_cv'] > 0.25

    # Consistent RT (healthy-like)
    consistent_rts = [500, 510, 495, 505, 500, 508, 502, 498]
    result2 = calculate_iiv_metrics(consistent_rts)
    print(f"  Consistent RT CV: {result2['rt_cv']}  (expected < 0.05)")
    ok2 = result2['rt_cv'] < 0.05

    print(f"\n  Result: {PASS if (ok1 and ok2) else FAIL}")
    return ok1 and ok2


# ─────────────────────────────────────────────
# TEST 3: RELIABLE CHANGE INDEX (RCI)
# ─────────────────────────────────────────────

def test_rci():
    print("\n" + "─" * 50)
    print("TEST 3: Reliable Change Index (RCI)")
    print("─" * 50)

    # Big improvement over sessions
    improving_sessions = [
        {'score': 40, 'mean_rt': 800},
        {'score': 50, 'mean_rt': 750},
        {'score': 60, 'mean_rt': 700},
        {'score': 70, 'mean_rt': 650},
        {'score': 80, 'mean_rt': 600},
    ]
    result = calculate_within_person_variability(improving_sessions)
    print(f"  RCI (big gain)  : {result['reliable_change_index']}  (expected > 1.0)")
    ok1 = result['reliable_change_index'] > 1.0

    # Stable sessions
    stable_sessions = [
        {'score': 65, 'mean_rt': 600},
        {'score': 66, 'mean_rt': 598},
        {'score': 64, 'mean_rt': 602},
        {'score': 65, 'mean_rt': 600},
    ]
    result2 = calculate_within_person_variability(stable_sessions)
    print(f"  RCI (stable)    : {result2['reliable_change_index']}  (expected near 0)")
    ok2 = abs(result2['reliable_change_index']) < 1.5

    print(f"\n  Result: {PASS if (ok1 and ok2) else FAIL}")
    return ok1 and ok2


# ─────────────────────────────────────────────
# TEST 4: TREND ANALYSIS (EWMA)
# ─────────────────────────────────────────────

def test_ewma():
    print("\n" + "─" * 50)
    print("TEST 4: Trend Analysis (EWMA)")
    print("─" * 50)

    # Clearly improving
    improving = [50, 55, 58, 62, 65, 68, 70, 73, 75, 78]
    r1 = calculate_ewma_trend(improving)
    print(f"  Improving trend : {r1['trend_direction']} / {r1['trend_strength']}  (expected 'improving')")
    ok1 = r1['trend_direction'].lower() == "improving"

    # Clearly declining
    declining = [80, 75, 72, 68, 65, 61, 58, 55, 52, 50]
    r2 = calculate_ewma_trend(declining)
    print(f"  Declining trend : {r2['trend_direction']} / {r2['trend_strength']}  (expected 'declining')")
    ok2 = r2['trend_direction'].lower() == "declining"

    # Stable
    stable = [65, 64, 66, 65, 65, 64, 66, 65, 65, 64]
    r3 = calculate_ewma_trend(stable)
    print(f"  Stable trend    : {r3['trend_direction']}  (expected 'stable')")
    ok3 = r3['trend_direction'].lower() == "stable"

    print(f"\n  Result: {PASS if (ok1 and ok2 and ok3) else FAIL}")
    return ok1 and ok2 and ok3


# ─────────────────────────────────────────────
# TEST 5: CONTEXTUAL CORRELATIONS
# ─────────────────────────────────────────────

def test_correlations():
    print("\n" + "─" * 50)
    print("TEST 5: Contextual Correlations")
    print("─" * 50)

    # High fatigue → low score  (strong negative correlation expected)
    sessions = [
        {'fatigue_level': 9, 'score': 40, 'mean_rt': 900},
        {'fatigue_level': 7, 'score': 55, 'mean_rt': 750},
        {'fatigue_level': 5, 'score': 65, 'mean_rt': 650},
        {'fatigue_level': 3, 'score': 78, 'mean_rt': 550},
        {'fatigue_level': 2, 'score': 85, 'mean_rt': 500},
    ]
    result = calculate_contextual_correlations(sessions, ['fatigue_level'])
    corr = result['fatigue_level']['correlation_with_score']
    print(f"  Fatigue → Score : r = {corr}  (expected < -0.8  strong negative)")
    ok = corr < -0.8

    print(f"\n  Result: {PASS if ok else FAIL}")
    return ok


# ─────────────────────────────────────────────
# TEST 6: FULL SESSION ANALYSIS
# ─────────────────────────────────────────────

def test_full_session():
    print("\n" + "─" * 50)
    print("TEST 6: Full Session Analysis (analyze_session_advanced)")
    print("─" * 50)

    session_data = {
        'trials': make_trials(start_accuracy=0.92, end_accuracy=0.60),
        'score': 72,
        'mean_rt': 620,
        'accuracy': 0.76,
        'context': {'fatigue_level': 6, 'sleep_quality': 5}
    }
    result = analyze_session_advanced(session_data)

    print(f"  Score           : {result['basic_metrics']['score']}")
    print(f"  Fatigue Index   : {result['fatigue_metrics']['fatigue_index']}")
    print(f"  RT CV           : {result['iiv_metrics']['rt_cv']}")

    ok = (
        'fatigue_metrics' in result and
        'iiv_metrics' in result and
        'basic_metrics' in result
    )
    print(f"\n  Result: {PASS if ok else FAIL}")
    return ok


# ─────────────────────────────────────────────
# TEST 7: LONGITUDINAL REPORT
# ─────────────────────────────────────────────

def test_longitudinal():
    print("\n" + "─" * 50)
    print("TEST 7: Longitudinal Report (generate_longitudinal_report)")
    print("─" * 50)

    sessions = make_sessions(trend="improving", n=10)
    report = generate_longitudinal_report(sessions)

    trend_dir = report['trends']['score_trend']['trend_direction']
    avg_fatigue = report['biomarkers']['average_fatigue_index']
    rci = report['biomarkers']['rci']
    total = report['summary']['total_sessions']

    print(f"  Total Sessions  : {total}  (expected 10)")
    print(f"  Score Trend     : {trend_dir}  (expected IMPROVING)")
    print(f"  Avg Fatigue Idx : {avg_fatigue}")
    print(f"  RCI             : {rci}")

    ok = total == 10 and trend_dir.lower() == "improving"
    print(f"\n  Result: {PASS if ok else FAIL}")
    return ok


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  DIGITAL BIOMARKERS - VERIFICATION TESTS")
    print("=" * 50)

    results = {
        "Fatigue Index"           : test_fatigue_index(),
        "Coefficient of Variation": test_cv(),
        "Reliable Change Index"   : test_rci(),
        "Trend Analysis (EWMA)"   : test_ewma(),
        "Contextual Correlations" : test_correlations(),
        "Full Session Analysis"   : test_full_session(),
        "Longitudinal Report"     : test_longitudinal(),
    }

    print("\n" + "=" * 50)
    print("  FINAL RESULTS")
    print("=" * 50)
    passed = 0
    for name, ok in results.items():
        status = PASS if ok else FAIL
        print(f"  {status}  {name}")
        if ok:
            passed += 1

    total = len(results)
    print(f"\n  {passed}/{total} tests passed")
    if passed == total:
        print("\n  🎉 ALL BIOMARKERS WORKING CORRECTLY!")
        print("  Ready for clinical validation study.")
    else:
        print("\n  ⚠️  Some tests failed. Check output above.")
    print("=" * 50 + "\n")

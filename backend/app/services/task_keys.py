from typing import Optional


TASK_KEY_ALIASES = {
    "n-back": "n_back",
    "dual-n-back": "dual_n_back",
    "digit-span": "digit_span",
    "spatial-span": "spatial_span",
    "letter-number-sequencing": "letter_number_sequencing",
    "operation-span": "operation_span",
    "simple-reaction": "simple_reaction",
    "reaction_time": "simple_reaction",
    "choice-reaction-time": "choice_reaction_time",
    "trail-making-a": "trail_making_a",
    "trails_a": "trail_making_a",
    "pattern-comparison": "pattern_comparison",
    "inspection-time": "inspection_time",
    "it": "inspection_time",
    "continuous-performance": "cpt",
    "continuous_performance": "cpt",
    "go-no-go": "go_nogo",
    "gonogo": "go_nogo",
    "flanker-task": "flanker",
    "trail-making-b": "trail_making_b",
    "rule-shift": "rule_shift",
    "rule_shift_task": "rule_shift",
    "plus-minus": "plus_minus",
    "tower-of-london": "tower_of_london",
    "tower_of_hanoi": "tower_of_london",
    "stockings-of-cambridge": "stockings_of_cambridge",
    "stockings_of_cambridge": "stockings_of_cambridge",
    "stockings_of_cambridge_task": "stockings_of_cambridge",
    "category-fluency": "category_fluency",
    "verbal-fluency": "verbal_fluency",
    "twenty-questions": "twenty_questions",
    "target-search": "target_search",
    "visual-search": "visual_search",
    "landmark-task": "landmark_task",
    "cancellation-test": "cancellation_test",
    "cancellation": "cancellation_test",
    "feature-conjunction": "feature_conjunction",
    "multiple-object-tracking": "multiple_object_tracking",
    "mot": "multiple_object_tracking",
    "useful-field-of-view": "useful_field_of_view",
    "ufov": "useful_field_of_view",
    "stroop": "stroop",
    "pasat": "pasat",
    "flanker": "flanker",
    "wcst": "wcst",
    "dccs": "dccs",
    "sart": "sart",
    "sdmt": "sdmt",
    "cpt": "cpt",
    "simple_reaction": "simple_reaction",
    "choice_reaction_time": "choice_reaction_time",
    "trail_making_a": "trail_making_a",
    "pattern_comparison": "pattern_comparison",
    "inspection_time": "inspection_time",
    "go_nogo": "go_nogo",
    "trail_making_b": "trail_making_b",
    "rule_shift": "rule_shift",
    "plus_minus": "plus_minus",
    "tower_of_london": "tower_of_london",
    "target_search": "target_search",
    "visual_search": "visual_search",
    "landmark_task": "landmark_task",
    "cancellation_test": "cancellation_test",
    "feature_conjunction": "feature_conjunction",
    "multiple_object_tracking": "multiple_object_tracking",
    "useful_field_of_view": "useful_field_of_view",
    "category_fluency": "category_fluency",
    "verbal_fluency": "verbal_fluency",
    "twenty_questions": "twenty_questions",
}


def normalize_task_key(task_key: Optional[str]) -> Optional[str]:
    if task_key is None:
        return None

    normalized = str(task_key).strip()
    if not normalized:
        return None

    lowered = normalized.lower().replace(" ", "_").replace("-", "_")
    return TASK_KEY_ALIASES.get(normalized, TASK_KEY_ALIASES.get(lowered, lowered))

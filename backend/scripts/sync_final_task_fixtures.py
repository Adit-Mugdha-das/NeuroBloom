"""Synchronize the final N-C4 numerical fixtures into the task inventory."""

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "docs" / "task_inventory.csv"

BACKEND = "backend/tests/test_task_scoring_fixtures_batch3.py"
BACKEND_B4 = "backend/tests/test_task_scoring_fixtures_batch4.py"
FRONTEND = "frontend-svelte/src/lib/task-scoring.test.js"

FIXTURES = {
    "n_back": (FRONTEND, "6 hits among 8 targets produces score 75"),
    "simple_reaction": (FRONTEND, "component scores 28 21 14 and 8 produce score 71"),
    "cpt": (FRONTEND, "8 hits among 10 targets produces score 80"),
    "stroop": (BACKEND, "100 accuracy and 20 percent interference cost produces score 96"),
    "go_nogo": (BACKEND, "100 inhibition 50 speed and 100 consistency produce score 85"),
    "flanker": (BACKEND, "100 accuracy 450 ms mean RT and 100 ms conflict produce score 90.25"),
    "task_switching": (FRONTEND, "17 correct among 20 responses produces score 85"),
    "trails_b": (BACKEND, "50 seconds and one error produce adjusted time 55 and B-A 20"),
    "wcst": (BACKEND, "one correct trial with zero categories at level 1 produces score 10"),
    "dccs": (BACKEND, "perfect 1500 ms response produces component score 100"),
    "plus_minus": (BACKEND, "perfect 2000 ms responses with zero switch cost produce score 100"),
    "tower_of_london": (BACKEND, "completion 40 efficiency 20 and speed 20 produce score 80"),
    "stockings_cambridge": (BACKEND, "perfect component total 110 is capped at score 100"),
    "verbal_fluency": (BACKEND, "five valid words for one letter produces score 40"),
    "feature_conjunction": (BACKEND, "correct 5-second response among 20 items produces score 1.0"),
    "dual_n_back": (BACKEND_B4, "4 of 6 decisions correct with 50 and 100 hit rates produces trial score 75.4"),
    "choice_reaction_time": (BACKEND_B4, "50 accuracy and 730 ms mean RT produce score 69.5"),
    "sart": (BACKEND_B4, "75 accuracy 50 no-go accuracy and one commission produce score 73"),
    "rule_shift": (BACKEND_B4, "50 accuracy and 200 ms shift cost produce score 50.4"),
    "category_fluency": (BACKEND_B4, "3 unique words at level 5 produce normalized score 10"),
    "twenty_questions": (BACKEND_B4, "9 questions at level 3 produce raw 85 and score 93.5"),
    "visual_search": (BACKEND_B4, "correct rejection in 5 seconds is capped at score 1.0 and a false alarm scores 0"),
    "cancellation_test": (BACKEND_B4, "3 of 4 targets found gives accuracy 75 and score 70"),
    "landmark_task": (BACKEND_B4, "60 accuracy and spatial bias 20 produce score 64"),
    "multiple_object_tracking": (BACKEND_B4, "all targets plus one extra give recall 1 precision 0.75 and score 0.925"),
}

SCORING_CORRECTIONS = {
    "tower_of_london": "score=clip(40*completion_rate+40*planning_efficiency+speed_bonus+10*perfect_rate,0,100)",
    "stockings_cambridge": "score=clip(40*completion_rate+40*planning_efficiency+speed_bonus+10*perfect_rate,0,100)",
    "feature_conjunction": "backend VisualSearchTask score=1 for a correct response and 0 otherwise; correct-response speed bonus is capped at 1",
}

PARADIGM_REFERENCES = {
    "n_back": "Kirchner (1958) [R1]",
    "digit_span": "Wechsler (2008) [R2]",
    "spatial_span": "Kessels et al. (2000) [R3]",
    "letter_number_sequencing": "Wechsler (2008) [R2]",
    "operation_span": "Conway et al. (2005) [R4]",
    "dual_n_back": "Jaeggi et al. (2008) [R5]",
    "simple_reaction": "Donders (1868/1969) [R6]",
    "sdmt": "Smith (1982) [R7]",
    "trails_a": "Reitan (1958) [R8]",
    "pattern_comparison": "Salthouse and Babcock (1991) [R9]",
    "inspection_time": "Vickers et al. (1972) [R10]",
    "choice_reaction_time": "Hick (1952) [R11]",
    "cpt": "Rosvold et al. (1956) [R12]",
    "pasat": "Gronwall (1977) [R13]",
    "stroop": "Stroop (1935) [R14]",
    "go_nogo": "Simmonds et al. (2008) [R30]; Diamond (2013) [R31]",
    "flanker": "Eriksen and Eriksen (1974) [R15]",
    "sart": "Robertson et al. (1997) [R16]",
    "task_switching": "Rogers and Monsell (1995) [R17]",
    "trails_b": "Reitan (1958) [R8]",
    "wcst": "Berg (1948) [R18]",
    "dccs": "Zelazo (2006) [R19]",
    "rule_shift": "Rogers and Monsell (1995) [R17]",
    "plus_minus": "Jersild (1927) [R20]",
    "tower_of_london": "Shallice (1982) [R21]",
    "stockings_cambridge": "Owen et al. (1990) [R22]",
    "verbal_fluency": "Benton (1968) [R23]",
    "category_fluency": "Benton (1968) [R23]",
    "twenty_questions": "Mosher and Hornsby (1966) [R24]",
    "visual_search": "Treisman and Gelade (1980) [R25]",
    "cancellation_test": "Weintraub and Mesulam (1985) [R26]",
    "feature_conjunction": "Treisman and Gelade (1980) [R25]",
    "landmark_task": "Jewell and McCourt (2000) [R27]",
    "multiple_object_tracking": "Pylyshyn and Storm (1988) [R28]",
    "useful_field_of_view": "Ball et al. (1993) [R29]",
}

DIFFICULTY_CLARIFICATIONS = {
    "n_back": "baseline: 20 trials at 1-back; training mode uses 1-back at levels 1-2 and 2-back at levels 3-5 and 3-back at levels 6-10 with 20 trials; Dual N-Back is a separately inventoried training task",
    "digit_span": "levels 1-10 use length/type 3/F 4/F 5/F 4/mixed 5/mixed 5/B 6/B 7/mixed 8/mixed 9/mixed; 8 trials where trials 4 and 7 are sampled one level higher",
    "cpt": "baseline: 60 trials; training mode adds 10 trials per level above level 3 (70-130 trials at levels 4-10); Go/No-Go is a separately inventoried training task",
    "task_switching": "baseline: 40 color/parity trials; training mode adds 10 trials per level above level 4 (up to 100 trials at level 10); Rule Shift is a separately inventoried training task",
    "sart": "levels 1-10 change stream length target rate stimulus duration response window; advance >=84 with <=4 commission errors; regress <64",
    "rule_shift": "levels 1-10 change rules switch interval stimuli timing and trials; advance >=83 with switch accuracy >=72 and <=5 perseverative errors; regress <63",
    "landmark_task": "levels 1-10 change line offset distribution exposure response window and trials; advance >=84 with abs bias <=8 and <=1 omission; regress <64",
    "useful_field_of_view": "levels 1-3 central only and levels 4-6 add a peripheral target and levels 7-10 add 24-47 distractors; presentation time falls from 800 ms at level 1 to 150 ms at level 10",
}


def main() -> None:
    with INVENTORY.open(encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        fieldnames = reader.fieldnames
        rows = list(reader)

    if not fieldnames or len(rows) != 35:
        raise RuntimeError("Expected the 35-row task inventory")

    found = set()
    for row in rows:
        code = row["task_code"]
        if code not in PARADIGM_REFERENCES:
            raise RuntimeError(f"Missing paradigm reference for {code}")
        row["source_and_provenance"] = (
            "Original NeuroBloom implementation inspired by the general paradigm; "
            + PARADIGM_REFERENCES[code]
        )
        if code in DIFFICULTY_CLARIFICATIONS:
            row["difficulty_levels"] = DIFFICULTY_CLARIFICATIONS[code]
        if code not in FIXTURES:
            continue
        found.add(code)
        fixture, expected = FIXTURES[code]
        row["unit_test_fixture"] = fixture
        row["expected_output"] = expected
        row["verification_status"] = "verified"
        if code in SCORING_CORRECTIONS:
            row["scoring_definition"] = SCORING_CORRECTIONS[code]
        if code == "feature_conjunction":
            row["software_module"] = "backend/app/services/visual_search_task.py"

    missing = set(FIXTURES) - found
    if missing:
        raise RuntimeError(f"Inventory tasks not found: {sorted(missing)}")

    with INVENTORY.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()

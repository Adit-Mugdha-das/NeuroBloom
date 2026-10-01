# NeuroBloom 35-Task List

NeuroBloom contains 35 original digital tasks across six cognitive domains. The tasks are inspired by general cognitive paradigms and are not claimed to be equivalent to proprietary standardized instruments.

## Working memory

| No. | Task | Code | Purpose | Implementation |
|---:|---|---|---|---|
| 1 | N-Back | `n_back` | Baseline monitoring and training | `frontend-svelte/src/routes/baseline/tasks/working-memory/+page.svelte` |
| 2 | Digit Span | `digit_span` | Training | `backend/app/services/digit_span_task.py` |
| 3 | Spatial Span | `spatial_span` | Training | `backend/app/services/spatial_span_task.py` |
| 4 | Letter–Number Sequencing | `letter_number_sequencing` | Training | `backend/app/services/letter_number_sequencing_task.py` |
| 5 | Operation Span | `operation_span` | Training | `backend/app/services/operation_span_task.py` |
| 6 | Dual N-Back | `dual_n_back` | Training | `backend/app/services/dual_n_back_task.py` |

## Processing speed

| No. | Task | Code | Purpose | Implementation |
|---:|---|---|---|---|
| 7 | Simple Reaction Time | `simple_reaction` | Baseline monitoring | `frontend-svelte/src/routes/baseline/tasks/processing-speed/+page.svelte` |
| 8 | Symbol–Digit Matching | `sdmt` | Training | `backend/app/services/sdmt_task.py` |
| 9 | Numeric Trail Task | `trails_a` | Training | `backend/app/services/trail_making_a_task.py` |
| 10 | Pattern Comparison | `pattern_comparison` | Training | `backend/app/services/pattern_comparison_task.py` |
| 11 | Inspection Time | `inspection_time` | Training | `backend/app/services/inspection_time_task.py` |
| 12 | Choice Reaction Time | `choice_reaction_time` | Training | `backend/app/services/choice_reaction_time_task.py` |

## Attention

| No. | Task | Code | Purpose | Implementation |
|---:|---|---|---|---|
| 13 | Continuous Performance Task | `cpt` | Baseline monitoring | `frontend-svelte/src/routes/baseline/tasks/attention/+page.svelte` |
| 14 | Serial Addition Task | `pasat` | Training | `backend/app/services/pasat_task.py` |
| 15 | Color–Word Interference | `stroop` | Training | `backend/app/services/stroop_task.py` |
| 16 | Go/No-Go | `go_nogo` | Training | `backend/app/services/go_nogo_task.py` |
| 17 | Flanker | `flanker` | Training | `backend/app/services/flanker_task.py` |
| 18 | Sustained-Attention Response | `sart` | Training | `backend/app/services/sart_task.py` |

## Cognitive flexibility

| No. | Task | Code | Purpose | Implementation |
|---:|---|---|---|---|
| 19 | Task Switching | `task_switching` | Baseline monitoring | `frontend-svelte/src/routes/baseline/tasks/flexibility/+page.svelte` |
| 20 | Alternating Trail Task | `trails_b` | Training | `backend/app/services/trail_making_b_task.py` |
| 21 | Card-Sorting Rule Shift | `wcst` | Training | `backend/app/services/wcst_task.py` |
| 22 | Dimensional Card Sort | `dccs` | Training | `backend/app/services/dccs_task.py` |
| 23 | Rule Shift | `rule_shift` | Training | `backend/app/services/rule_shift_task.py` |
| 24 | Plus–Minus Switching | `plus_minus` | Training | `backend/app/services/plus_minus_task.py` |

## Planning

| No. | Task | Code | Purpose | Implementation |
|---:|---|---|---|---|
| 25 | Tower Planning | `tower_of_london` | Baseline monitoring and training | `backend/app/services/tol_task.py` |
| 26 | Stockings-Style Planning | `stockings_cambridge` | Training | `backend/app/services/soc_task.py` |
| 27 | Verbal Fluency | `verbal_fluency` | Training | `backend/app/services/verbal_fluency_task.py` |
| 28 | Category Fluency | `category_fluency` | Training | `backend/app/services/category_fluency_task.py` |
| 29 | Twenty Questions | `twenty_questions` | Training | `backend/app/services/twenty_questions_task.py` |

## Visual scanning

| No. | Task | Code | Purpose | Implementation |
|---:|---|---|---|---|
| 30 | Visual Search | `visual_search` | Baseline monitoring and training | `backend/app/services/visual_search_task.py` |
| 31 | Cancellation | `cancellation_test` | Training | `backend/app/services/cancellation_test_task.py` |
| 32 | Feature Conjunction | `feature_conjunction` | Training | `backend/app/services/visual_search_task.py` |
| 33 | Landmark Task | `landmark_task` | Training | `backend/app/services/landmark_task.py` |
| 34 | Multiple-Object Tracking | `multiple_object_tracking` | Training | `backend/app/services/multiple_object_tracking_task.py` |
| 35 | Central–Peripheral Attention | `useful_field_of_view` | Training | `backend/app/services/useful_field_of_view_task.py` |

## Detailed inventory

For scoring equations, difficulty rules, Bengali adaptation, provenance, licensing, and test fixtures, see [`task_inventory.csv`](task_inventory.csv).

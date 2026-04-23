export const TRAINING_TASK_ROUTE_BY_KEY = Object.freeze({
	n_back: '/training/dual-n-back',
	dual_n_back: '/training/dual-n-back',
	digit_span: '/training/digit-span',
	spatial_span: '/training/spatial-span',
	letter_number_sequencing: '/training/letter-number-sequencing',
	operation_span: '/training/operation-span',
	simple_reaction: '/training/choice-reaction-time',
	choice_reaction_time: '/training/choice-reaction-time',
	sdmt: '/training/sdmt',
	trail_making_a: '/training/trail-making-a',
	pattern_comparison: '/training/pattern-comparison',
	inspection_time: '/training/inspection-time',
	cpt: '/training/gonogo',
	pasat: '/training/pasat',
	stroop: '/training/stroop',
	go_nogo: '/training/gonogo',
	flanker: '/training/flanker',
	trail_making_b: '/training/trail-making-b',
	wcst: '/training/wcst',
	dccs: '/training/dccs',
	rule_shift: '/training/rule-shift',
	plus_minus: '/training/plus-minus',
	tower_of_london: '/training/tower-of-london',
	stockings_of_cambridge: '/training/stockings-of-cambridge',
	stockings_cambridge: '/training/stockings-of-cambridge',
	verbal_fluency: '/training/verbal-fluency',
	category_fluency: '/training/category-fluency',
	twenty_questions: '/training/twenty-questions',
	target_search: '/training/visual-search',
	visual_search: '/training/visual-search',
	landmark_task: '/training/landmark-task',
	cancellation_test: '/training/cancellation-test',
	feature_conjunction: '/training/feature-conjunction',
	multiple_object_tracking: '/training/multiple-object-tracking',
	useful_field_of_view: '/training/useful-field-of-view',
	sart: '/training/sart'
});

const TASK_KEY_ALIASES = Object.freeze({
	'n-back': 'n_back',
	'dual-n-back': 'dual_n_back',
	'digit-span': 'digit_span',
	'spatial-span': 'spatial_span',
	'letter-number-sequencing': 'letter_number_sequencing',
	'operation-span': 'operation_span',
	'reaction_time': 'simple_reaction',
	'simple-reaction': 'simple_reaction',
	'choice-reaction-time': 'choice_reaction_time',
	'trail-making-a': 'trail_making_a',
	trails_a: 'trail_making_a',
	'pattern-comparison': 'pattern_comparison',
	'inspection-time': 'inspection_time',
	it: 'inspection_time',
	continuous_performance: 'cpt',
	'continuous-performance': 'cpt',
	gonogo: 'go_nogo',
	'go-no-go': 'go_nogo',
	'trail-making-b': 'trail_making_b',
	'rule-shift': 'rule_shift',
	rule_shift_task: 'rule_shift',
	'plus-minus': 'plus_minus',
	'tower-of-london': 'tower_of_london',
	tower_of_hanoi: 'tower_of_london',
	'stockings-of-cambridge': 'stockings_of_cambridge',
	'stockings_cambridge': 'stockings_of_cambridge',
	'category-fluency': 'category_fluency',
	'verbal-fluency': 'verbal_fluency',
	'twenty-questions': 'twenty_questions',
	'target-search': 'target_search',
	'visual-search': 'visual_search',
	'landmark-task': 'landmark_task',
	cancellation: 'cancellation_test',
	'cancellation-test': 'cancellation_test',
	'feature-conjunction': 'feature_conjunction',
	mot: 'multiple_object_tracking',
	'multiple-object-tracking': 'multiple_object_tracking',
	ufov: 'useful_field_of_view',
	'useful-field-of-view': 'useful_field_of_view',
	stroop: 'stroop',
	pasat: 'pasat',
	flanker: 'flanker',
	wcst: 'wcst',
	dccs: 'dccs',
	sart: 'sart',
	sdmt: 'sdmt'
});

export function normalizeTaskKey(taskKey = '') {
	const normalized = String(taskKey || '').trim();
	if (!normalized) return '';
	const lowered = normalized.toLowerCase().replace(/-/g, '_');
	return TASK_KEY_ALIASES[normalized] || TASK_KEY_ALIASES[lowered] || lowered;
}

export function resolveTrainingTaskRoute(taskKey = '') {
	const normalized = normalizeTaskKey(taskKey);
	return TRAINING_TASK_ROUTE_BY_KEY[normalized] || '/training';
}

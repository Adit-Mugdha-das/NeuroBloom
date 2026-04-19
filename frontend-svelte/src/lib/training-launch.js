const TASK_ROUTE_BY_CODE = Object.freeze({
	n_back: '/baseline/tasks/working-memory',
	'n-back': '/baseline/tasks/working-memory',
	dual_n_back: '/training/dual-n-back',
	'dual-n-back': '/training/dual-n-back',
	digit_span: '/training/digit-span',
	'digit-span': '/training/digit-span',
	spatial_span: '/training/spatial-span',
	'spatial-span': '/training/spatial-span',
	letter_number_sequencing: '/training/letter-number-sequencing',
	'letter-number-sequencing': '/training/letter-number-sequencing',
	operation_span: '/training/operation-span',
	'operation-span': '/training/operation-span',
	simple_reaction: '/baseline/tasks/processing-speed',
	choice_reaction_time: '/training/choice-reaction-time',
	'choice-reaction-time': '/training/choice-reaction-time',
	reaction_time: '/baseline/tasks/processing-speed',
	sdmt: '/training/sdmt',
	trails_a: '/training/trail-making-a',
	'trail-making-a': '/training/trail-making-a',
	trail_making_a: '/training/trail-making-a',
	pattern_comparison: '/training/pattern-comparison',
	'pattern-comparison': '/training/pattern-comparison',
	inspection_time: '/training/inspection-time',
	'inspection-time': '/training/inspection-time',
	continuous_performance: '/baseline/tasks/attention',
	cpt: '/baseline/tasks/attention',
	pasat: '/training/pasat',
	sart: '/training/sart',
	stroop: '/training/stroop',
	go_nogo: '/training/gonogo',
	gonogo: '/training/gonogo',
	flanker: '/training/flanker',
	trail_making_b: '/training/trail-making-b',
	'trail-making-b': '/training/trail-making-b',
	wcst: '/training/wcst',
	dccs: '/training/dccs',
	rule_shift: '/training/rule-shift',
	rule_shift_task: '/training/rule-shift',
	'rule-shift': '/training/rule-shift',
	plus_minus: '/training/plus-minus',
	'plus-minus': '/training/plus-minus',
	tower_of_hanoi: '/baseline/tasks/planning',
	tower_of_london: '/baseline/tasks/planning',
	'tower-of-london': '/training/tower-of-london',
	stockings_cambridge: '/training/stockings-of-cambridge',
	'stockings-of-cambridge': '/training/stockings-of-cambridge',
	verbal_fluency: '/training/verbal-fluency',
	'verbal-fluency': '/training/verbal-fluency',
	category_fluency: '/training/category-fluency',
	'category-fluency': '/training/category-fluency',
	twenty_questions: '/training/twenty-questions',
	'twenty-questions': '/training/twenty-questions',
	target_search: '/baseline/tasks/visual-scanning',
	visual_search: '/training/visual-search',
	'visual-search': '/training/visual-search',
	landmark_task: '/training/landmark-task',
	'landmark-task': '/training/landmark-task',
	cancellation: '/training/cancellation-test',
	cancellation_test: '/training/cancellation-test',
	'cancellation-test': '/training/cancellation-test',
	feature_conjunction: '/training/feature-conjunction',
	'feature-conjunction': '/training/feature-conjunction',
	mot: '/training/multiple-object-tracking',
	multiple_object_tracking: '/training/multiple-object-tracking',
	'multiple-object-tracking': '/training/multiple-object-tracking',
	ufov: '/training/useful-field-of-view',
	useful_field_of_view: '/training/useful-field-of-view',
	'useful-field-of-view': '/training/useful-field-of-view'
});

function buildSearchParams(params) {
	const searchParams = new URLSearchParams();

	for (const [key, value] of Object.entries(params)) {
		if (value === undefined || value === null || value === '') continue;
		searchParams.set(key, String(value));
	}

	return searchParams.toString();
}

export function resolveTrainingTaskRoute(taskCode = '') {
	return TASK_ROUTE_BY_CODE[taskCode] || '/dashboard';
}

export function buildTrainingTaskUrl({
	taskCode,
	planId,
	taskId,
	difficulty,
	contextId,
	training = true
}) {
	const baseRoute = resolveTrainingTaskRoute(taskCode);
	const query = buildSearchParams({
		training: training ? 'true' : undefined,
		planId,
		difficulty,
		taskId,
		contextId
	});

	return query ? `${baseRoute}?${query}` : baseRoute;
}

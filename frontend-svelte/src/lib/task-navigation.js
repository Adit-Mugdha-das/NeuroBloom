export const TASK_RETURN_CONTEXT = Object.freeze({
	TRAINING: 'training',
	BASELINE: 'baseline'
});

export function resolveTaskReturn(_url, _context = TASK_RETURN_CONTEXT.TRAINING) {
	return {
		href: '/dashboard',
		labelKey: 'Back to Dashboard'
	};
}

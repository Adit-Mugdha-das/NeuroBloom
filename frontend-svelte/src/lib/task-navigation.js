export const TASK_RETURN_CONTEXT = Object.freeze({
	TRAINING: 'training',
	BASELINE: 'baseline',
	DEV: 'dev'
});

export function resolveTaskReturn(url, context = TASK_RETURN_CONTEXT.TRAINING) {
	const taskId = url?.searchParams?.get('taskId') || '';

	if (context === TASK_RETURN_CONTEXT.BASELINE) {
		return {
			href: '/baseline',
			labelKey: 'Back to Baseline'
		};
	}

	if (context === TASK_RETURN_CONTEXT.DEV || taskId.includes('_dev')) {
		return {
			href: '/dev/games',
			labelKey: 'Back to Game Lab'
		};
	}

	return {
		href: '/training',
		labelKey: 'Back to Training'
	};
}

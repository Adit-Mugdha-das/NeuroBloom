export const TASK_RETURN_CONTEXT = Object.freeze({
	TRAINING: 'training',
	BASELINE: 'baseline'
});

export function resolveTaskReturn(url, context = TASK_RETURN_CONTEXT.TRAINING) {
	const isBaselineContext = context === TASK_RETURN_CONTEXT.BASELINE;
	const launchedFromTraining = isBaselineContext
		? url?.searchParams?.get('training') === 'true'
		: true;

	return {
		href: launchedFromTraining ? '/training' : '/dashboard',
		labelKey: launchedFromTraining ? 'Back to Training' : 'Back to Dashboard'
	};
}

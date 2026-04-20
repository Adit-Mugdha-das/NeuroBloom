import { normalizeTaskKey, resolveTrainingTaskRoute } from '$lib/task-registry';

function buildSearchParams(params) {
	const searchParams = new URLSearchParams();

	for (const [key, value] of Object.entries(params)) {
		if (value === undefined || value === null || value === '') continue;
		searchParams.set(key, String(value));
	}

	return searchParams.toString();
}

export { normalizeTaskKey, resolveTrainingTaskRoute };

export function buildTrainingTaskUrl({
	taskCode,
	planId,
	taskId,
	difficulty,
	contextId,
	training = true
}) {
	const normalizedTaskKey = normalizeTaskKey(taskCode);
	const baseRoute = resolveTrainingTaskRoute(normalizedTaskKey);
	const query = buildSearchParams({
		training: training ? 'true' : undefined,
		planId,
		difficulty,
		taskId,
		task_key: normalizedTaskKey,
		contextId
	});

	return query ? `${baseRoute}?${query}` : baseRoute;
}

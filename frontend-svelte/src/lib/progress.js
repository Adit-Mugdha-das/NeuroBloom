export const domainOrder = [
	'working_memory',
	'attention',
	'processing_speed',
	'flexibility',
	'visual_scanning',
	'planning'
];

export const domainNames = {
	working_memory: 'Working Memory',
	attention: 'Attention',
	flexibility: 'Cognitive Flexibility',
	planning: 'Planning',
	processing_speed: 'Processing Speed',
	visual_scanning: 'Visual Scanning'
};

export function getDomainName(domain) {
	return domainNames[domain] || domain;
}

export function getScoreColor(score) {
	if (score >= 80) return '#15803d';
	if (score >= 60) return '#b45309';
	return '#b91c1c';
}

export function getTrendLabel(value) {
	if (value > 0) return 'Improving';
	if (value < 0) return 'Needs attention';
	return 'Stable';
}

export function getTrendTone(value) {
	if (value > 0) return 'positive';
	if (value < 0) return 'negative';
	return 'neutral';
}

export function calculateOverallScore(metrics) {
	const domainMetrics = Object.values(metrics?.metrics_by_domain || {});
	if (domainMetrics.length === 0) return 0;

	const total = domainMetrics.reduce((sum, domain) => sum + (domain.average_score || 0), 0);
	return Number((total / domainMetrics.length).toFixed(1));
}

export function calculateTrendDelta(trendsData) {
	const points = trendsData?.overall_trend || [];
	if (points.length < 2) return 0;

	const first = points[0]?.avg_score || 0;
	const last = points[points.length - 1]?.avg_score || 0;
	return Number((last - first).toFixed(1));
}

export function formatDuration(totalSeconds) {
	const minutes = Math.floor((totalSeconds || 0) / 60);
	const seconds = (totalSeconds || 0) % 60;
	return `${minutes}m ${seconds}s`;
}

export function formatShortDate(dateValue) {
	return new Date(dateValue).toLocaleDateString();
}
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

export function calculateBaselineDifficulty(score) {
	return Math.max(1, Math.floor((score || 0) / 10));
}

export function formatImprovementPercentage(value) {
	if (Math.abs(value || 0) < 1) return 'Stable';
	return `${value > 0 ? '+' : ''}${Number(value || 0).toFixed(0)}%`;
}

export function getComparisonSummary(value) {
	if (Math.abs(value || 0) < 1) return 'Stable';
	if ((value || 0) > 0) return 'Improved';
	return 'Below baseline';
}

export function getClinicalStatusLabel(value) {
	if ((value || 0) >= 5) return 'Improving';
	if ((value || 0) <= -5) return 'Needs Attention';
	return 'Stable';
}

export function getClinicalStatusTone(value) {
	if ((value || 0) >= 5) return 'improving';
	if ((value || 0) <= -5) return 'attention';
	return 'stable';
}

export function formatPointChange(value) {
	if (Math.abs(value || 0) < 1) return 'No meaningful change since baseline';
	return `${value > 0 ? '+' : ''}${Number(value || 0).toFixed(0)} points since baseline`;
}
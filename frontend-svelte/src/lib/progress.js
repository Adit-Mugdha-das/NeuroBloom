import { localeText } from '$lib/i18n';

export const domainOrder = [
	'working_memory',
	'attention',
	'processing_speed',
	'flexibility',
	'visual_scanning',
	'planning'
];

export const domainNames = {
	working_memory: { en: 'Working Memory', bn: 'ওয়ার্কিং মেমরি' },
	attention: { en: 'Attention', bn: 'মনোযোগ' },
	flexibility: { en: 'Cognitive Flexibility', bn: 'মানসিক নমনীয়তা' },
	planning: { en: 'Planning', bn: 'পরিকল্পনা' },
	processing_speed: { en: 'Processing Speed', bn: 'প্রসেসিং স্পিড' },
	visual_scanning: { en: 'Visual Scanning', bn: 'ভিজ্যুয়াল স্ক্যানিং' }
};

export function getDomainName(domain, targetLocale = 'en') {
	const variants = domainNames[domain];
	return variants ? localeText(variants, targetLocale) : domain;
}

export function getScoreColor(score) {
	if (score >= 80) return '#15803d';
	if (score >= 60) return '#b45309';
	return '#b91c1c';
}

export function getTrendLabel(value, targetLocale = 'en') {
	if (value > 0) return localeText({ en: 'Improving', bn: 'উন্নতি হচ্ছে' }, targetLocale);
	if (value < 0) return localeText({ en: 'Needs attention', bn: 'আরও মনোযোগ দরকার' }, targetLocale);
	return localeText({ en: 'Stable', bn: 'স্থিতিশীল' }, targetLocale);
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

export function formatDuration(totalSeconds, targetLocale = 'en') {
	const minutes = Math.floor((totalSeconds || 0) / 60);
	const seconds = (totalSeconds || 0) % 60;
	if (targetLocale === 'bn') {
		if (minutes <= 0) return `${seconds} সেকেন্ড`;
		if (seconds === 0) return `${minutes} মিনিট`;
		return `${minutes} মিনিট ${seconds} সেকেন্ড`;
	}
	return `${minutes}m ${seconds}s`;
}

export function formatShortDate(dateValue, targetLocale = 'en') {
	return new Date(dateValue).toLocaleDateString(targetLocale === 'bn' ? 'bn-BD' : 'en-US');
}

export function calculateBaselineDifficulty(score) {
	return Math.max(1, Math.floor((score || 0) / 10));
}

export function formatImprovementPercentage(value, targetLocale = 'en') {
	if (Math.abs(value || 0) < 1) return localeText({ en: 'Stable', bn: 'স্থিতিশীল' }, targetLocale);
	return `${value > 0 ? '+' : ''}${Number(value || 0).toFixed(0)}%`;
}

export function getComparisonSummary(value, targetLocale = 'en') {
	if (Math.abs(value || 0) < 1) return localeText({ en: 'Stable', bn: 'স্থিতিশীল' }, targetLocale);
	if ((value || 0) > 0) return localeText({ en: 'Improved', bn: 'উন্নত' }, targetLocale);
	return localeText({ en: 'Below baseline', bn: 'বেসলাইনের নিচে' }, targetLocale);
}

export function getClinicalStatusLabel(value, targetLocale = 'en') {
	if ((value || 0) >= 5) return localeText({ en: 'Improving', bn: 'উন্নতি হচ্ছে' }, targetLocale);
	if ((value || 0) <= -5) return localeText({ en: 'Needs Attention', bn: 'মনোযোগ দরকার' }, targetLocale);
	return localeText({ en: 'Stable', bn: 'স্থিতিশীল' }, targetLocale);
}

export function getClinicalStatusTone(value) {
	if ((value || 0) >= 5) return 'improving';
	if ((value || 0) <= -5) return 'attention';
	return 'stable';
}

export function formatPointChange(value, targetLocale = 'en') {
	if (Math.abs(value || 0) < 1) {
		return localeText(
			{ en: 'No meaningful change since baseline', bn: 'বেসলাইন থেকে তেমন পরিবর্তন নেই' },
			targetLocale
		);
	}
	return targetLocale === 'bn'
		? `${value > 0 ? '+' : ''}${Number(value || 0).toFixed(0)} পয়েন্ট বেসলাইন থেকে`
		: `${value > 0 ? '+' : ''}${Number(value || 0).toFixed(0)} points since baseline`;
}

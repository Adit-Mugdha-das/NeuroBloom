/**
 * Display rules for the longitudinal indicators.
 *
 * Missing values stay missing: null, undefined and non-finite values are
 * "unavailable" and must be shown as insufficient data. A measured 0 is a real
 * value and is displayed as 0.
 */

export function isAvailable(value) {
	return typeof value === 'number' && Number.isFinite(value);
}

/** Descriptive CV range: 'high' (> 0.35), 'moderate' (> 0.25), 'low', or null when unavailable. */
export function cvRange(cv) {
	if (!isAvailable(cv)) return null;
	if (cv > 0.35) return 'high';
	if (cv > 0.25) return 'moderate';
	return 'low';
}

/** Correlation strength: 'strong' (|r| >= 0.6), 'moderate' (|r| >= 0.3), 'weak', or null when unavailable. */
export function correlationStrength(r) {
	if (!isAvailable(r)) return null;
	const absolute = Math.abs(r);
	if (absolute >= 0.6) return 'strong';
	if (absolute >= 0.3) return 'moderate';
	return 'weak';
}

/**
 * Reaction-time trend as a neutral description: 'longer', 'shorter' or 'stable'.
 * The generic trend label calls a rising slope "improving", but for reaction
 * time a rising slope means longer responses, so it is never shown as improvement.
 */
export function responseTimeChange(rtTrend) {
	const explicit = rtTrend?.response_time_change;
	if (explicit === 'longer' || explicit === 'shorter' || explicit === 'stable') return explicit;

	const direction = String(rtTrend?.direction || '').toLowerCase();
	if (direction === 'improving') return 'longer';
	if (direction === 'declining') return 'shorter';
	return 'stable';
}

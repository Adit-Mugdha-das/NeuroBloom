import { describe, expect, it } from 'vitest';
import { correlationStrength, cvRange, isAvailable, responseTimeChange } from './analytics-display.js';

describe('missing indicator values stay unavailable', () => {
	it('treats null, undefined and non-finite values as unavailable', () => {
		expect(isAvailable(null)).toBe(false);
		expect(isAvailable(undefined)).toBe(false);
		expect(isAvailable(Number.NaN)).toBe(false);
	});

	it('treats a measured zero as available', () => {
		expect(isAvailable(0)).toBe(true);
	});

	it('gives no CV range for missing CV, so it is never shown as normal', () => {
		expect(cvRange(null)).toBeNull();
		expect(cvRange(undefined)).toBeNull();
		expect(cvRange(0)).toBe('low');
		expect(cvRange(0.3)).toBe('moderate');
		expect(cvRange(0.4)).toBe('high');
	});

	it('gives no strength for a missing correlation but keeps a real zero', () => {
		expect(correlationStrength(null)).toBeNull();
		expect(correlationStrength(0)).toBe('weak');
		expect(correlationStrength(-0.7)).toBe('strong');
	});
});

describe('reaction-time trend wording', () => {
	it('describes a rising RT slope as longer response times, not improvement', () => {
		expect(responseTimeChange({ direction: 'improving' })).toBe('longer');
		expect(responseTimeChange({ direction: 'declining' })).toBe('shorter');
		expect(responseTimeChange({ direction: 'stable' })).toBe('stable');
	});

	it('prefers the explicit API field when present', () => {
		expect(responseTimeChange({ direction: 'improving', response_time_change: 'longer' })).toBe('longer');
		expect(responseTimeChange(null)).toBe('stable');
	});
});

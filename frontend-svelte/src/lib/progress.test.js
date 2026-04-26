import { describe, it, expect } from 'vitest';
import { getScoreColor, getTrendLabel, getTrendTone, domainOrder } from './progress.js';

describe('getScoreColor', () => {
    it('returns green for scores >= 80', () => {
        expect(getScoreColor(80)).toBe('#15803d');
        expect(getScoreColor(100)).toBe('#15803d');
    });

    it('returns amber for scores 60–79', () => {
        expect(getScoreColor(60)).toBe('#b45309');
        expect(getScoreColor(75)).toBe('#b45309');
    });

    it('returns red for scores below 60', () => {
        expect(getScoreColor(59)).toBe('#b91c1c');
        expect(getScoreColor(0)).toBe('#b91c1c');
    });
});

describe('getTrendTone', () => {
    it('returns positive for improving trend', () => {
        expect(getTrendTone(5)).toBe('positive');
    });
    it('returns negative for declining trend', () => {
        expect(getTrendTone(-3)).toBe('negative');
    });
});

describe('domainOrder', () => {
    it('lists all 6 cognitive domains', () => {
        expect(domainOrder).toHaveLength(6);
    });
    it('working_memory is first (most commonly impaired in MS)', () => {
        expect(domainOrder[0]).toBe('working_memory');
    });
});

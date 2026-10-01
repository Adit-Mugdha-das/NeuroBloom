import { describe, expect, it } from 'vitest';
import {
	scoreContinuousPerformance,
	scoreNBack,
	scoreProcessingSpeed,
	scoreTaskSwitching
} from './task-scoring.js';

describe('N-C4 baseline scoring fixtures', () => {
	it('scores n-back targets', () => {
		expect(scoreNBack(6, 2)).toBe(75);
	});

	it('scores continuous-performance targets', () => {
		expect(scoreContinuousPerformance(8, 10)).toBe(80);
	});

	it('scores task-switching errors', () => {
		expect(scoreTaskSwitching(20, 3)).toBe(85);
	});

	it('sums the processing-speed components', () => {
		// At 250 ms, 430 ms, SD 50 ms, and 80% choice accuracy:
		// simple=28, choice speed=21, consistency=14, accuracy=8.
		expect(scoreProcessingSpeed(250, 430, 50, 0.8)).toBe(71);
	});
});

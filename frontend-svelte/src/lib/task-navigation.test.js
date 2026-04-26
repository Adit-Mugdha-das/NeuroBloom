import { describe, it, expect } from 'vitest';
import { resolveTaskReturn, TASK_RETURN_CONTEXT } from './task-navigation.js';

describe('resolveTaskReturn', () => {
    it('returns training route when context is TRAINING', () => {
        const url = new URL('http://localhost/training/flanker?taskId=flanker_1');
        const result = resolveTaskReturn(url, TASK_RETURN_CONTEXT.TRAINING);
        expect(result.href).toBe('/training');
        expect(result.labelKey).toBe('Back to Training');
    });

    it('returns baseline route when context is BASELINE', () => {
        const url = new URL('http://localhost/baseline/tasks/attention');
        const result = resolveTaskReturn(url, TASK_RETURN_CONTEXT.BASELINE);
        expect(result.href).toBe('/baseline');
        expect(result.labelKey).toBe('Back to Baseline');
    });

    it('returns game lab route when context is DEV', () => {
        const url = new URL('http://localhost/dev/games?taskId=flanker_dev');
        const result = resolveTaskReturn(url, TASK_RETURN_CONTEXT.DEV);
        expect(result.href).toBe('/dev/games');
        expect(result.labelKey).toBe('Back to Game Lab');
    });

    it('returns game lab route when taskId contains _dev suffix', () => {
        const url = new URL('http://localhost/training/flanker?taskId=flanker_dev');
        const result = resolveTaskReturn(url, TASK_RETURN_CONTEXT.TRAINING);
        expect(result.href).toBe('/dev/games');
    });

    it('TASK_RETURN_CONTEXT is frozen (immutable)', () => {
        expect(() => { TASK_RETURN_CONTEXT.NEW = 'new'; }).toThrow();
    });
});

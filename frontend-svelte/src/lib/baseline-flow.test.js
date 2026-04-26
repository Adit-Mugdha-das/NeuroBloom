import { describe, it, expect } from 'vitest';
import { BASELINE_MODULES } from './baseline-flow.js';

describe('BASELINE_MODULES', () => {
    it('contains all 6 required cognitive domains', () => {
        const keys = BASELINE_MODULES.map(m => m.key);
        expect(keys).toContain('working_memory');
        expect(keys).toContain('attention');
        expect(keys).toContain('flexibility');
        expect(keys).toContain('planning');
        expect(keys).toContain('processing_speed');
        expect(keys).toContain('visual_scanning');
    });

    it('every module has a valid route starting with /baseline', () => {
        for (const module of BASELINE_MODULES) {
            expect(module.route).toMatch(/^\/baseline\//);
        }
    });

    it('every module has English and Bengali titles', () => {
        for (const module of BASELINE_MODULES) {
            expect(module.title.en).toBeTruthy();
            expect(module.title.bn).toBeTruthy();
        }
    });

    it('every module has a unique key', () => {
        const keys = BASELINE_MODULES.map(m => m.key);
        const uniqueKeys = new Set(keys);
        expect(uniqueKeys.size).toBe(keys.length);
    });
});

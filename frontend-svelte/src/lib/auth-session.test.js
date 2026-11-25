import { describe, it, expect, vi } from 'vitest';
import { CSRF_HEADER, CSRF_HEADER_VALUE, createAuthFetch, isApiRequest, isSessionEndpoint } from './auth-session.js';

const PAGE = 'http://localhost:8080';
const API = 'http://localhost:8000';

describe('isApiRequest', () => {
	it('recognises absolute URLs on the configured API origin', () => {
		expect(isApiRequest(`${API}/api/training/trends/1`, API, PAGE)).toBe(true);
	});

	it('recognises same-origin /api paths used through the dev proxy', () => {
		expect(isApiRequest('/api/baseline/1', API, PAGE)).toBe(true);
	});

	it('ignores other origins and non-API paths', () => {
		expect(isApiRequest('https://example.org/api/anything', API, PAGE)).toBe(false);
		expect(isApiRequest(`${API}/docs`, API, PAGE)).toBe(false);
		expect(isApiRequest('/favicon.png', API, PAGE)).toBe(false);
	});
});

describe('isSessionEndpoint', () => {
	it('treats the login and logout endpoints as session endpoints', () => {
		expect(isSessionEndpoint(`${API}/api/auth/login`, PAGE)).toBe(true);
		expect(isSessionEndpoint(`${API}/api/admin/login`, PAGE)).toBe(true);
		expect(isSessionEndpoint(`${API}/api/auth/me`, PAGE)).toBe(false);
	});
});

function setup(status = 200) {
	const baseFetch = vi.fn(async () => new Response('{}', { status }));
	const onUnauthorized = vi.fn();
	const authFetch = createAuthFetch(baseFetch, {
		apiBaseUrl: API,
		getPageOrigin: () => PAGE,
		onUnauthorized
	});
	return { baseFetch, onUnauthorized, authFetch };
}

describe('createAuthFetch', () => {
	it('sends the session cookie with API reads, without the write header', async () => {
		const { baseFetch, authFetch } = setup();
		await authFetch(`${API}/api/training/trends/1`);
		const [, init] = baseFetch.mock.calls[0];
		expect(init.credentials).toBe('include');
		expect(init.headers.get(CSRF_HEADER)).toBeNull();
	});

	it('adds the request-verification header to API writes and keeps caller headers', async () => {
		const { baseFetch, authFetch } = setup();
		await authFetch(`${API}/api/training/tasks/stroop/submit/1`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: '{}'
		});
		const [, init] = baseFetch.mock.calls[0];
		expect(init.credentials).toBe('include');
		expect(init.headers.get(CSRF_HEADER)).toBe(CSRF_HEADER_VALUE);
		expect(init.headers.get('Content-Type')).toBe('application/json');
	});

	it('leaves requests to other origins untouched', async () => {
		const { baseFetch, authFetch } = setup();
		const init = { method: 'POST' };
		await authFetch('https://example.org/collect', init);
		expect(baseFetch).toHaveBeenCalledWith('https://example.org/collect', init);
	});

	it('reports an expired session on a 401 from the API', async () => {
		const { onUnauthorized, authFetch } = setup(401);
		await authFetch(`${API}/api/training/trends/1`);
		expect(onUnauthorized).toHaveBeenCalledTimes(1);
	});

	it('does not treat a failed login as an expired session', async () => {
		const { onUnauthorized, authFetch } = setup(401);
		await authFetch(`${API}/api/auth/login`, { method: 'POST' });
		expect(onUnauthorized).not.toHaveBeenCalled();
	});

	it('handles Request objects', async () => {
		const { baseFetch, authFetch } = setup();
		await authFetch(new Request(`${API}/api/auth/patient/1/consent`, { method: 'PATCH' }));
		const [request] = baseFetch.mock.calls[0];
		expect(request.credentials).toBe('include');
		expect(request.headers.get(CSRF_HEADER)).toBe(CSRF_HEADER_VALUE);
	});
});

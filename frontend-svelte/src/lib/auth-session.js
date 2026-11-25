// Browser side of the session model (see backend/app/core/access_control.py).
//
// The access token lives only in an httpOnly cookie that page scripts cannot
// read. API requests therefore send credentials with the request, and writes add
// the X-Requested-With header that the backend requires for cookie sessions.

export const CSRF_HEADER = 'X-Requested-With';
export const CSRF_HEADER_VALUE = 'NeuroBloom';

const SAFE_METHODS = new Set(['GET', 'HEAD', 'OPTIONS']);

// Endpoints whose 401 means "wrong password" rather than "session ended".
const SESSION_ENDPOINTS = ['/api/auth/login', '/api/auth/doctor/login', '/api/admin/login', '/api/auth/logout'];

export function isSafeMethod(method = 'GET') {
	return SAFE_METHODS.has(String(method).toUpperCase());
}

/**
 * True when `url` targets this application's API.
 * @param {string} url absolute or relative request URL
 * @param {string} apiBaseUrl configured API base URL ('' for same origin)
 * @param {string} pageOrigin origin of the current page
 */
export function isApiRequest(url, apiBaseUrl, pageOrigin) {
	let target;
	try {
		target = new URL(url, pageOrigin);
	} catch {
		return false;
	}
	const apiOrigin = apiBaseUrl ? new URL(apiBaseUrl, pageOrigin).origin : pageOrigin;
	// Same-origin /api paths are proxied to the backend by the Vite dev server.
	const knownOrigin = target.origin === apiOrigin || target.origin === pageOrigin;
	return knownOrigin && target.pathname.startsWith('/api/');
}

export function isSessionEndpoint(url, pageOrigin) {
	try {
		const { pathname } = new URL(url, pageOrigin);
		return SESSION_ENDPOINTS.some((path) => pathname === path);
	} catch {
		return false;
	}
}

/**
 * Wrap a fetch implementation so API requests carry the session cookie and the
 * request-verification header, and so an expired session triggers `onUnauthorized`.
 */
export function createAuthFetch(baseFetch, { apiBaseUrl, getPageOrigin, onUnauthorized }) {
	return async function authFetch(input, init = {}) {
		const pageOrigin = getPageOrigin();
		const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url;
		if (!isApiRequest(url, apiBaseUrl, pageOrigin)) {
			return baseFetch(input, init);
		}

		const method = (init.method || (input instanceof Request ? input.method : 'GET')).toUpperCase();
		const headers = new Headers(input instanceof Request ? input.headers : undefined);
		new Headers(init.headers || {}).forEach((value, key) => headers.set(key, value));
		if (!isSafeMethod(method)) {
			headers.set(CSRF_HEADER, CSRF_HEADER_VALUE);
		}

		const request = input instanceof Request
			? new Request(input, { ...init, headers, credentials: 'include' })
			: input;
		const response = input instanceof Request
			? await baseFetch(request)
			: await baseFetch(input, { ...init, headers, credentials: 'include' });

		if (response.status === 401 && !isSessionEndpoint(url, pageOrigin)) {
			onUnauthorized?.();
		}
		return response;
	};
}

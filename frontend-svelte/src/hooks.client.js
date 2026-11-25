import { API_BASE_URL, setUnauthorizedHandler } from '$lib/api';
import { createAuthFetch } from '$lib/auth-session';
import { clearUser, user } from '$lib/stores';
import { get } from 'svelte/store';

const PUBLIC_PATHS = new Set(['/', '/login', '/register']);
let redirecting = false;

// Called when the API reports that the session is missing or expired.
function handleUnauthorized() {
	const hadUser = Boolean(get(user));
	clearUser();
	if (!hadUser || redirecting || PUBLIC_PATHS.has(window.location.pathname)) {
		return;
	}
	redirecting = true;
	window.location.assign('/login?session=expired');
}

// Installed here, before any page runs, so every fetch() to the API sends the
// session cookie and the request-verification header.
window.fetch = createAuthFetch(window.fetch.bind(window), {
	apiBaseUrl: API_BASE_URL,
	getPageOrigin: () => window.location.origin,
	onUnauthorized: handleUnauthorized
});

setUnauthorizedHandler(handleUnauthorized);

import { browser } from '$app/environment';
import { writable } from 'svelte/store';
import { apiUrl } from './api.js';
import { CSRF_HEADER, CSRF_HEADER_VALUE } from './auth-session.js';

// Profile shown in the interface (id, role, name). It is not a credential: the
// session itself is the httpOnly cookie, which the server checks on every request.
const initialUser = browser ? JSON.parse(localStorage.getItem('user') || 'null') : null;

// User store
export const user = writable(initialUser);
export const authReady = writable(false);

// Ask the server to clear the session cookie (page scripts cannot remove it).
function endServerSession() {
	fetch(apiUrl('/api/auth/logout'), {
		method: 'POST',
		credentials: 'include',
		headers: { [CSRF_HEADER]: CSRF_HEADER_VALUE }
	}).catch(() => {});
}

// Subscribe to user changes and update localStorage
if (browser) {
	let previousUser = initialUser;
	user.subscribe(value => {
		if (value) {
			localStorage.setItem('user', JSON.stringify(value));
		} else {
			localStorage.removeItem('user');
			if (previousUser) {
				endServerSession();
			}
		}
		previousUser = value;
	});
}

export const markAuthReady = () => {
	authReady.set(true);
};

// Auth helper functions
export const setUser = (userData) => {
	user.set(userData);
};

export const updateUserPreferences = (preferences = {}) => {
	user.update((currentUser) => {
		if (!currentUser) return currentUser;

		return {
			...currentUser,
			preferences: {
				...(currentUser.preferences || {}),
				...preferences
			}
		};
	});
};

export const clearUser = () => {
	user.set(null);
};

export const isAuthenticated = () => {
	let authenticated = false;
	user.subscribe(value => {
		authenticated = !!value;
	})();
	return authenticated;
};

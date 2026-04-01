import { browser } from '$app/environment';
import { writable } from 'svelte/store';

// Get initial user from localStorage
const initialUser = browser ? JSON.parse(localStorage.getItem('user') || 'null') : null;

// User store
export const user = writable(initialUser);
export const authReady = writable(false);

// Subscribe to user changes and update localStorage
if (browser) {
	user.subscribe(value => {
		if (value) {
			localStorage.setItem('user', JSON.stringify(value));
		} else {
			localStorage.removeItem('user');
		}
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

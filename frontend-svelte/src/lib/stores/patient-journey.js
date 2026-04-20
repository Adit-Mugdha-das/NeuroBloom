import { writable } from 'svelte/store';

import { patientJourney } from '$lib/api';

const initialState = {
	loading: false,
	error: null,
	data: null
};

function createJourneyStore() {
	const { subscribe, set, update } = writable(initialState);

	return {
		subscribe,
		reset() {
			set(initialState);
		},
		async load(userId) {
			update((state) => ({ ...state, loading: true, error: null }));
			try {
				const data = await patientJourney.get(userId);
				set({
					loading: false,
					error: null,
					data
				});
				return data;
			} catch (error) {
				set({
					loading: false,
					error,
					data: null
				});
				throw error;
			}
		}
	};
}

export const patientJourneyStore = createJourneyStore();

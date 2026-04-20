import { redirect } from '@sveltejs/kit';
import {
	createPatientDashboardViewModel,
	getDashboardContext
} from '$lib/dashboard/patient-dashboard.js';

export const ssr = false;

export async function load({ fetch, depends }) {
	depends('app:patient-dashboard');

	const { user, locale } = getDashboardContext();
	if (!user?.id) {
		throw redirect(307, '/login');
	}

	return {
		dashboard: await createPatientDashboardViewModel({
			fetchImpl: fetch,
			user,
			locale
		})
	};
}

import { expect } from '@playwright/test';

export const API = (process.env.E2E_API_URL || 'http://localhost:8000').replace(/\/+$/, '');
export const SESSION_COOKIE = process.env.E2E_SESSION_COOKIE || 'neurobloom_session';
export const CSRF = { 'X-Requested-With': 'NeuroBloom' };

// Synthetic accounts created by seed_initial_data.py and scripts/seed_demo_clinical_data.py.
export const ACCOUNTS = {
	patient: { email: 'sharmin.akter@demo.neurobloom.example', password: 'patient1234', role: 'patient' },
	otherPatient: { email: 'rashedul.islam@demo.neurobloom.example', password: 'patient1234', role: 'patient' },
	admin: { email: 'admin@gmail.com', password: 'admin123', role: 'admin' },
	clinicianPassword: 'doctor1234'
};

const ROLE_BUTTON_INDEX = { patient: 0, doctor: 1, admin: 2 };
const LANDING = { patient: /\/dashboard$/, doctor: /\/doctor\/dashboard$/, admin: /\/admin\/dashboard$/ };

/** Sign in through the login page, as a user would. */
export async function loginThroughUi(page, { email, password, role }) {
	await page.goto('/login');
	await page.locator('.role-btn').nth(ROLE_BUTTON_INDEX[role]).click();
	await page.locator('#email').fill(email);
	await page.locator('#password').fill(password);
	await page.locator('button.submit-btn').click();
	await expect(page).toHaveURL(LANDING[role]);
}

/** Log in through the API (sets the session cookie in the request context). */
export async function apiLogin(request, { email, password, role }) {
	const path = role === 'doctor' ? '/api/auth/doctor/login' : role === 'admin' ? '/api/admin/login' : '/api/auth/login';
	const response = await request.post(`${API}${path}`, { data: { email, password } });
	expect(response.status()).toBe(200);
	return response.json();
}

/** The clinician assigned to a patient, found through the patient's own session. */
export async function assignedClinician(request, patientId) {
	const response = await request.get(`${API}/api/doctor/patient/${patientId}/assigned-doctor`);
	expect(response.status()).toBe(200);
	const body = await response.json();
	expect(body.assigned).toBe(true);
	return body.doctor;
}

export async function sessionCookie(context) {
	return (await context.cookies(API)).find((cookie) => cookie.name === SESSION_COOKIE);
}

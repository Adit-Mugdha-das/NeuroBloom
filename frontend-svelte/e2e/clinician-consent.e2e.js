import { expect, test } from '@playwright/test';
import { ACCOUNTS, API, CSRF, apiLogin, assignedClinician, loginThroughUi } from './helpers.js';

test('a clinician reviews an assigned patient and loses access while consent is withdrawn', async ({ page, browser }) => {
	const patientCtx = await browser.newContext();
	const patient = await apiLogin(patientCtx.request, ACCOUNTS.patient);
	const clinician = await assignedClinician(patientCtx.request, patient.id);
	const setConsent = (value) =>
		patientCtx.request.patch(`${API}/api/auth/patient/${patient.id}/consent?consent=${value}`, { headers: CSRF });

	try {
		await loginThroughUi(page, { email: clinician.email, password: ACCOUNTS.clinicianPassword, role: 'doctor' });

		// The assigned patient appears in the clinician's list, and the record opens.
		await page.goto('/doctor/patients');
		await expect(page.getByText(patient.full_name).first()).toBeVisible();
		const overview = page.waitForResponse((r) => r.url().includes(`/api/doctor/${clinician.id}/patient/${patient.id}/overview`));
		await page.goto(`/doctor/patient/${patient.id}`);
		expect((await overview).status()).toBe(200);

		// The patient withdraws consent: the same page can no longer load the record.
		expect((await setConsent(false)).status()).toBe(200);
		const refused = page.waitForResponse((r) => r.url().includes(`/api/doctor/${clinician.id}/patient/${patient.id}/overview`));
		await page.reload();
		expect((await refused).status()).toBe(403);
		for (const path of [
			`/api/doctor/${clinician.id}/patient/${patient.id}/sessions`,
			`/api/doctor/${clinician.id}/patient/${patient.id}/trends`,
			`/api/training/advanced-analytics/${patient.id}/biomarkers`
		]) {
			expect((await page.request.get(`${API}${path}`)).status(), path).toBe(403);
		}
	} finally {
		// Restore the demo patient's consent for later tests and demonstrations.
		expect((await setConsent(true)).status()).toBe(200);
		await patientCtx.close();
	}

	const restored = await page.request.get(`${API}/api/doctor/${clinician.id}/patient/${patient.id}/overview`);
	expect(restored.status()).toBe(200);
});

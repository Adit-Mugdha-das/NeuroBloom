import { expect, test } from '@playwright/test';
import { ACCOUNTS, API, apiLogin, assignedClinician, loginThroughUi } from './helpers.js';

async function accountId(request, account) {
	return (await apiLogin(request, account)).id;
}

test('a patient cannot read another patient\'s records, even after editing the saved profile', async ({ page, browser }) => {
	const other = await browser.newContext();
	const otherId = await accountId(other.request, ACCOUNTS.otherPatient);
	await other.close();

	await loginThroughUi(page, ACCOUNTS.patient);
	const ownId = (await (await page.request.get(`${API}/api/auth/me`)).json()).id;
	expect(ownId).not.toBe(otherId);

	// Direct requests for the other patient's data are refused by the server.
	for (const path of [
		`/api/training/training-session/history/${otherId}`,
		`/api/training/training-plan/${otherId}`,
		`/api/auth/patient/${otherId}/profile`,
		`/api/training/advanced-analytics/${otherId}/biomarkers`
	]) {
		const status = await page.evaluate(async (url) => (await fetch(url, { credentials: 'include' })).status, `${API}${path}`);
		expect(status, path).toBe(403);
	}

	// Editing the profile saved in the browser does not change who the server sees.
	const refused = [];
	page.on('response', (response) => {
		if (response.url().includes(`/${otherId}`) && response.url().startsWith(API)) refused.push(response.status());
	});
	await page.evaluate((id) => {
		const saved = JSON.parse(localStorage.getItem('user'));
		localStorage.setItem('user', JSON.stringify({ ...saved, id }));
	}, otherId);
	await page.goto('/dashboard');
	await expect.poll(() => page.evaluate(() => JSON.parse(localStorage.getItem('user') || '{}').id)).toBe(ownId);
	// The dashboard did ask for the other patient's data, and every such request was refused.
	expect(refused.length).toBeGreaterThan(0);
	expect(refused.every((status) => status === 403)).toBe(true);
});

test('a patient session cannot use clinician or administrator endpoints', async ({ page }) => {
	await loginThroughUi(page, ACCOUNTS.patient);
	const ownId = (await (await page.request.get(`${API}/api/auth/me`)).json()).id;
	for (const path of [`/api/doctor/${ownId}/patients`, `/api/admin/stats?admin_id=${ownId}`, '/api/admin/patients?admin_id=1']) {
		expect((await page.request.get(`${API}${path}`)).status(), path).toBe(403);
	}
});

test('a clinician cannot open a patient assigned to someone else', async ({ page, browser }) => {
	const patientCtx = await browser.newContext();
	const patientId = await accountId(patientCtx.request, ACCOUNTS.patient);
	const clinician = await assignedClinician(patientCtx.request, patientId);
	await patientCtx.close();

	const otherCtx = await browser.newContext();
	const otherPatientId = await accountId(otherCtx.request, ACCOUNTS.otherPatient);
	const otherClinician = await assignedClinician(otherCtx.request, otherPatientId);
	await otherCtx.close();
	expect(otherClinician.id).not.toBe(clinician.id);

	await loginThroughUi(page, { email: clinician.email, password: ACCOUNTS.clinicianPassword, role: 'doctor' });
	const own = await page.request.get(`${API}/api/doctor/${clinician.id}/patient/${patientId}/overview`);
	expect(own.status()).toBe(200);
	const foreign = await page.request.get(`${API}/api/doctor/${clinician.id}/patient/${otherPatientId}/overview`);
	expect(foreign.status()).toBe(403);
	// Using the other clinician's identifier does not help.
	const borrowed = await page.request.get(`${API}/api/doctor/${otherClinician.id}/patient/${otherPatientId}/overview`);
	expect(borrowed.status()).toBe(403);
});

import { expect, test } from '@playwright/test';
import { ACCOUNTS, API, apiLogin, assignedClinician, loginThroughUi } from './helpers.js';

test('a patient completes a task in the browser and the result is stored and visible to the clinician', async ({ page, browser }) => {
	await loginThroughUi(page, ACCOUNTS.patient);
	const me = await (await page.request.get(`${API}/api/auth/me`)).json();
	const historyBefore = await (await page.request.get(`${API}/api/training/training-session/history/${me.id}?limit=500`)).json();

	await page.goto('/training/pattern-comparison?taskId=processing_speed_0');
	await page.getByRole('button', { name: 'Start Actual Task' }).click();

	const submitted = page.waitForResponse((response) => response.url().includes('/api/training/tasks/pattern-comparison/submit/'));
	const same = page.locator('button.same-btn');
	await expect(same).toBeVisible({ timeout: 15_000 }); // after the 3-second countdown
	for (let trial = 0; trial < 40 && (await same.isVisible()); trial += 1) {
		await same.click();
	}
	const response = await submitted;
	expect(response.status()).toBe(200);
	const result = await response.json();
	expect(result.session_id).toBeTruthy();
	await expect(page.getByRole('button', { name: 'Back to Dashboard' }).first()).toBeVisible();

	// The result is stored for this patient ...
	const historyAfter = await (await page.request.get(`${API}/api/training/training-session/history/${me.id}?limit=500`)).json();
	expect(historyAfter.length).toBe(historyBefore.length + 1);
	expect(historyAfter.map((item) => item.id)).toContain(result.session_id);

	// ... and the assigned clinician, with consent, sees it in the session history.
	const clinician = await assignedClinician(page.request, me.id);
	const clinicianCtx = await browser.newContext();
	await apiLogin(clinicianCtx.request, { email: clinician.email, password: ACCOUNTS.clinicianPassword, role: 'doctor' });
	const sessions = await clinicianCtx.request.get(`${API}/api/doctor/${clinician.id}/patient/${me.id}/sessions?limit=500`);
	expect(sessions.status()).toBe(200);
	expect((await sessions.json()).sessions.map((item) => item.id)).toContain(result.session_id);
	await clinicianCtx.close();
});

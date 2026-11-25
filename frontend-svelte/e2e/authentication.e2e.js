import { expect, test } from '@playwright/test';
import { ACCOUNTS, API, SESSION_COOKIE, loginThroughUi, sessionCookie } from './helpers.js';

test('patient signs in; the session cookie is httpOnly and no token reaches page scripts', async ({ page, context }) => {
	await loginThroughUi(page, ACCOUNTS.patient);

	const cookie = await sessionCookie(context);
	expect(cookie, 'session cookie is set').toBeTruthy();
	expect(cookie.httpOnly).toBe(true);
	expect(cookie.sameSite).toBe('Lax');

	const visible = await page.evaluate(() => ({ cookies: document.cookie, storage: JSON.stringify({ ...localStorage, ...sessionStorage }) }));
	expect(visible.cookies).not.toContain(SESSION_COOKIE);
	expect(visible.storage).not.toMatch(/eyJ[\w-]+\.[\w-]+\./); // no JWT in browser storage

	const me = await page.request.get(`${API}/api/auth/me`);
	expect(me.status()).toBe(200);
	expect((await me.json()).email).toBe(ACCOUNTS.patient.email);
});

test('logging out ends the server session', async ({ page }) => {
	await loginThroughUi(page, ACCOUNTS.patient);
	await page.getByRole('button', { name: 'Logout' }).first().click();
	await expect(page).toHaveURL(/\/login/);
	await expect.poll(async () => (await page.request.get(`${API}/api/auth/me`)).status()).toBe(401);
});

test('an invalid or expired session returns the user to sign-in with a notice', async ({ page, context }) => {
	await loginThroughUi(page, ACCOUNTS.patient);
	await context.addCookies([{ name: SESSION_COOKIE, value: 'tampered.token.value', url: API }]);
	await page.goto('/dashboard');
	await expect(page).toHaveURL(/\/login\?session=expired/);
	await expect(page.getByText('Your session has ended. Please sign in again.')).toBeVisible();
});

test('protected pages send a visitor without a session to sign-in', async ({ page }) => {
	await page.goto('/dashboard');
	await expect(page).toHaveURL(/\/login/);
	const me = await page.request.get(`${API}/api/auth/me`);
	expect(me.status()).toBe(401);
});

test('a wrong password is refused without a session cookie', async ({ page, context }) => {
	await page.goto('/login');
	await page.locator('#email').fill(ACCOUNTS.patient.email);
	await page.locator('#password').fill('not-the-password');
	await page.locator('button.submit-btn').click();
	await expect(page.locator('.error-banner')).toBeVisible();
	await expect(page).toHaveURL(/\/login/);
	expect(await sessionCookie(context)).toBeUndefined();
});

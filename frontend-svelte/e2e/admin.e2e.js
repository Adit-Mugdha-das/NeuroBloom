import { expect, test } from '@playwright/test';
import { ACCOUNTS, API, loginThroughUi } from './helpers.js';

test('an administrator signs in and admin data is bound to that administrator', async ({ page }) => {
	const stats = page.waitForResponse((r) => r.url().includes('/api/admin/stats'));
	await loginThroughUi(page, ACCOUNTS.admin);
	expect((await stats).status()).toBe(200);

	const me = await (await page.request.get(`${API}/api/auth/me`)).json();
	expect(me.role).toBe('admin');
	// Another administrator identifier is refused, even with a valid admin session.
	const borrowed = await page.request.get(`${API}/api/admin/stats?admin_id=${me.id + 1000}`);
	expect(borrowed.status()).toBe(403);
});

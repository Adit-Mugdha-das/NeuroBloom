import { expect, test } from '@playwright/test';
import { ACCOUNTS, API, assignedClinician, loginThroughUi } from './helpers.js';

// Opens every page a role uses and fails if any API call made by the page is
// refused (401/403) or fails on the server (5xx), or if the page shows an alert.
// This guards existing functionality against the authentication changes.

const TRAINING_TASKS = [
	'cancellation-test', 'category-fluency', 'choice-reaction-time', 'dccs', 'digit-span', 'dual-n-back',
	'feature-conjunction', 'flanker', 'gonogo', 'inspection-time', 'landmark-task', 'letter-number-sequencing',
	'multiple-object-tracking', 'operation-span', 'pasat', 'pattern-comparison', 'plus-minus', 'rule-shift',
	'sart', 'sdmt', 'spatial-span', 'stockings-of-cambridge', 'stroop', 'tower-of-london', 'trail-making-a',
	'trail-making-b', 'twenty-questions', 'useful-field-of-view', 'verbal-fluency', 'visual-search', 'wcst'
];

// The 35 inventoried tasks run on 37 pages: 31 training task pages plus the six
// baseline pages, which hold the baseline versions of Simple Reaction Time, N-Back,
// Continuous Performance and Task Switching (docs/task_inventory.csv). In training,
// those four share a page with Choice Reaction Time, Dual N-Back, Go/No-Go and Rule Shift.
const BASELINE_TASKS = ['attention', 'flexibility', 'planning', 'processing-speed', 'visual-scanning', 'working-memory'];

const PATIENT_PAGES = [
	'/dashboard', '/training', '/progress', '/progress/achievements', '/progress/domains', '/progress/history',
	'/progress/insights', '/baseline', '/baseline/results', '/messages', '/notifications', '/prescriptions',
	'/profile', '/settings', '/find-doctor', ...TRAINING_TASKS.map((task) => `/training/${task}`),
	...BASELINE_TASKS.map((task) => `/baseline/tasks/${task}`)
];

const ADMIN_PAGES = [
	'/admin/dashboard', '/admin/analytics', '/admin/audit-logs', '/admin/departments', '/admin/doctors',
	'/admin/interventions', '/admin/messages', '/admin/notifications', '/admin/patients', '/admin/research-data',
	'/admin/system-health'
];

function watchApi(page) {
	const problems = [];
	page.on('response', (response) => {
		const status = response.status();
		if (response.url().startsWith(API) && (status === 401 || status === 403 || status >= 500)) {
			problems.push(`${status} ${response.request().method()} ${response.url().replace(API, '')}`);
		}
	});
	page.on('dialog', async (dialog) => {
		problems.push(`alert: ${dialog.message()}`);
		await dialog.dismiss();
	});
	return problems;
}

async function visitAll(page, paths, problems) {
	for (const path of paths) {
		const before = problems.length;
		await page.goto(path);
		await page.waitForLoadState('networkidle', { timeout: 20_000 }).catch(() => {});
		for (const problem of problems.slice(before)) problems[problems.indexOf(problem)] = `${path}: ${problem}`;
		expect(page.url(), `${path} should not send the user back to sign-in`).not.toContain('/login');
	}
}

test('every patient page loads without refused or failing API calls', async ({ page }) => {
	test.setTimeout(10 * 60_000);
	const problems = watchApi(page);
	await loginThroughUi(page, ACCOUNTS.patient);
	await visitAll(page, PATIENT_PAGES, problems);
	expect(problems).toEqual([]);
});

test('every clinician page loads without refused or failing API calls', async ({ page }) => {
	test.setTimeout(5 * 60_000);
	const patient = await (await page.request.post(`${API}/api/auth/login`, {
		data: { email: ACCOUNTS.patient.email, password: ACCOUNTS.patient.password }
	})).json();
	const clinician = await assignedClinician(page.request, patient.id);
	await page.context().clearCookies();

	const problems = watchApi(page);
	await loginThroughUi(page, { email: clinician.email, password: ACCOUNTS.clinicianPassword, role: 'doctor' });
	await visitAll(page, [
		'/doctor/dashboard', '/doctor/patients', '/doctor/analytics', '/doctor/messages', '/doctor/notifications',
		'/doctor/prescriptions', '/doctor/reports', `/doctor/patient/${patient.id}`,
		`/doctor/patient/${patient.id}/prescriptions`, `/doctor/patient/${patient.id}/reports`
	], problems);
	expect(problems).toEqual([]);
});

test('every administrator page loads without refused or failing API calls', async ({ page }) => {
	test.setTimeout(5 * 60_000);
	const problems = watchApi(page);
	await loginThroughUi(page, ACCOUNTS.admin);
	await visitAll(page, ADMIN_PAGES, problems);
	expect(problems).toEqual([]);
});

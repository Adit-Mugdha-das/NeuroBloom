import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const projectRoot = process.cwd();

const checks = [
	{
		file: 'src/lib/dashboard/patient-dashboard.js',
		patterns: [
			/\btask_name\b/,
			/\bfocus_reason\b(?!_key)/,
			/\blatestBadge\??\.name\b/,
			/\blatestBadge\??\.description\b/,
			/\btranslateText\(/,
			/Patient Workspace/,
			/Advanced Learner/,
			/Weakest area/,
			/Moderate area/
		]
	},
	{
		file: 'src/routes/training/+page.svelte',
		patterns: [
			/\btask\.focus_reason\b/,
			/\btask_name\b/,
			/\btranslateText\(/,
			/Weakest area/,
			/Moderate area/,
			/Advanced Learner/
		]
	},
	{
		file: 'src/lib/components/BadgeNotification.svelte',
		patterns: [/\btranslateText\(/, /\bcurrentBadge\.name\b/, /\bcurrentBadge\.description\b/, /Advanced Learner/]
	},
	{
		file: 'src/routes/progress/achievements/+page.svelte',
		patterns: [/\bbadge\.name\b/, /\bbadge\.description\b/, /Advanced Learner/]
	},
	{
		file: 'src/lib/components/BadgesShowcase.svelte',
		patterns: [/\bbadge\.name\b/, /\bbadge\.description\b/]
	},
	{
		file: 'src/lib/components/DifficultyBadge.svelte',
		patterns: [/\btranslateText\(/, /\bEasy\b/, /\bMedium\b/, /\bHard\b/, /\bExpert\b/]
	}
];

const findings = [];

for (const check of checks) {
	const absolute = path.join(projectRoot, check.file);
	const source = fs.readFileSync(absolute, 'utf8');

	for (const pattern of check.patterns) {
		const match = source.match(pattern);
		if (match) {
			findings.push({
				file: check.file,
				pattern: pattern.toString(),
				match: match[0]
			});
		}
	}
}

if (findings.length > 0) {
	console.error('Patient-native i18n audit failed:');
	for (const finding of findings) {
		console.error(`- ${finding.file}: matched ${finding.pattern} -> ${finding.match}`);
	}
	process.exit(1);
}

console.log('Patient-native i18n audit passed.');

import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { compile, parse } from 'svelte/compiler';

const projectRoot = process.cwd();
const routesRoot = path.join(projectRoot, 'src', 'routes');
const layoutPath = path.join(routesRoot, '+layout.svelte');
const catalogPath = path.join(projectRoot, 'src', 'lib', 'i18n', 'catalog.js');
const reportsDir = path.join(projectRoot, 'reports');
const reportJsonPath = path.join(reportsDir, 'localization-verification-report.json');
const reportMdPath = path.join(reportsDir, 'localization-verification-report.md');

const routeScanRoots = [
	path.join(routesRoot, 'training'),
	path.join(routesRoot, 'baseline', 'tasks')
];

const catalogSource = fs.readFileSync(catalogPath, 'utf8');
const layoutSource = fs.readFileSync(layoutPath, 'utf8');
const longTranslationCallPattern =
	/(?:\bt|translateText)\(\s*(['"`])((?:\\.|(?!\1)[\s\S])+?)\1(?:\s*,[\s\S]*?)?\)/g;
const allowedFragments = [
	'MS',
	'ADHD',
	'WCST',
	'DCCS',
	'PASAT',
	'ANT',
	'OSPAN',
	'SDMT',
	'RT',
	'd-prime',
	'Go/No-Go',
	'GO',
	'NO-GO',
	'SPACEBAR'
];

function extractRouteSet(name) {
	const blockMatch = layoutSource.match(
		new RegExp(`const ${name} = new Set\\(\\[(.*?)\\]\\);`, 's')
	);

	if (!blockMatch) {
		return new Set();
	}

	return new Set(
		[...blockMatch[1].matchAll(/'([^']+)'/g)].map((match) => match[1])
	);
}

function walk(dir, output = []) {
	for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
		const fullPath = path.join(dir, entry.name);
		if (entry.isDirectory()) {
			walk(fullPath, output);
			continue;
		}

		if (entry.isFile() && entry.name === '+page.svelte') {
			output.push(fullPath);
		}
	}

	return output;
}

function routePathFromFile(filePath) {
	const relative = path.relative(routesRoot, path.dirname(filePath));
	if (!relative) {
		return '/';
	}

	return `/${relative.replace(/\\/g, '/')}`;
}

function normalizeText(value) {
	return value.replace(/\s+/g, ' ').trim();
}

function stripAllowedFragments(text) {
	return allowedFragments.reduce(
		(current, fragment) => current.replaceAll(fragment, ''),
		text
	);
}

function looksLikeEnglishUiText(text) {
	const normalized = stripAllowedFragments(normalizeText(text));

	if (!normalized || !/[A-Za-z]/.test(normalized)) {
		return false;
	}

	if (/^[A-Za-z0-9\s()[\]{}+|*.,:;/%'"!?-]+$/.test(normalized) && normalized.length <= 2) {
		return false;
	}

	if (/^(class|style|true|false|null|undefined)$/i.test(normalized)) {
		return false;
	}

	return true;
}

function hasExactCatalogCoverage(text) {
	const escapedSingle = text.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
	const escapedDouble = text.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
	return (
		catalogSource.includes(`'${escapedSingle}'`) ||
		catalogSource.includes(`"${escapedDouble}"`)
	);
}

function collectLongUncoveredTranslations(source) {
	const misses = [];

	for (const match of source.matchAll(longTranslationCallPattern)) {
		const text = normalizeText(match[2] || '');
		if (text.length < 30 || !looksLikeEnglishUiText(text) || hasExactCatalogCoverage(text)) {
			continue;
		}

		misses.push(text);
	}

	return [...new Set(misses)];
}

function collectTemplateEnglishFragments(source) {
	const ast = parse(source);
	const findings = new Set();

	function walkNodes(nodes = []) {
		for (const node of nodes) {
			if (node.type === 'Text') {
				const text = normalizeText(node.data || '');
				if (text.length >= 8 && looksLikeEnglishUiText(text)) {
					findings.add(text);
				}
			}

			if (Array.isArray(node.fragment?.nodes)) {
				walkNodes(node.fragment.nodes);
			}

			if (Array.isArray(node.else?.nodes)) {
				walkNodes(node.else.nodes);
			}

			if (Array.isArray(node.pending?.nodes)) {
				walkNodes(node.pending.nodes);
			}

			if (Array.isArray(node.then?.nodes)) {
				walkNodes(node.then.nodes);
			}

			if (Array.isArray(node.catch?.nodes)) {
				walkNodes(node.catch.nodes);
			}
		}
	}

	walkNodes(ast.fragment?.nodes || []);
	return [...findings];
}

function collectStates(source) {
	const states = new Set();
	const commentStatePattern =
		/let\s+(?:phase|stage|gamePhase|view)\s*=\s*['"`]([^'"`]+)['"`]\s*;\s*\/\/\s*([^\n]+)/g;
	const directComparisonPattern = /(?:phase|stage|gamePhase|view)\s*===\s*['"`]([^'"`]+)['"`]/g;
	const stateConstantPattern = /STATE\.([A-Z_]+)/g;

	for (const match of source.matchAll(commentStatePattern)) {
		states.add(match[1]);
		for (const value of match[2].split(',')) {
			const normalized = normalizeText(value).replace(/^[/-]+/, '').toLowerCase();
			if (normalized) states.add(normalized);
		}
	}

	for (const match of source.matchAll(directComparisonPattern)) {
		states.add(match[1]);
	}

	for (const match of source.matchAll(stateConstantPattern)) {
		states.add(match[1].toLowerCase());
	}

	return [...states].sort();
}

function collectManualChecks(source, states) {
	const checks = new Set(states);

	if (source.includes('showHelp')) checks.add('help-modal');
	if (source.includes('alert(')) checks.add('error-alert');
	if (source.includes('fetch(')) checks.add('backend-response');
	if (source.includes('newBadges')) checks.add('badges');
	if (source.includes('showResults') || source.includes("phase === 'results'") || source.includes("stage === 'results'")) {
		checks.add('results');
	}
	if (source.includes('practice')) checks.add('practice');
	if (source.includes('instructions')) checks.add('instructions');
	if (source.includes('intro')) checks.add('intro');
	if (source.includes('loading')) checks.add('loading');

	return [...checks].sort();
}

function compileRoute(filePath, source) {
	try {
		compile(source, {
			filename: path.relative(projectRoot, filePath).replace(/\\/g, '/'),
			generate: 'client'
		});
		return { ok: true };
	} catch (error) {
		return {
			ok: false,
			message: error?.message || String(error)
		};
	}
}

function analyzeRoute(filePath, nativeRoutes, legacyRoutes) {
	const source = fs.readFileSync(filePath, 'utf8');
	const routePath = routePathFromFile(filePath);
	const relativePath = path.relative(projectRoot, filePath).replace(/\\/g, '/');
	const states = collectStates(source);
	const longUncoveredTranslations = collectLongUncoveredTranslations(source);
	const rawEnglishTemplateFragments = collectTemplateEnglishFragments(source);
	const compileStatus = compileRoute(filePath, source);

	let localizationMode = 'non-game';
	if (nativeRoutes.has(routePath)) {
		localizationMode = 'native';
	} else if (legacyRoutes.has(routePath)) {
		localizationMode = 'legacy';
	}

	return {
		routePath,
		filePath: relativePath,
		lines: source.split(/\r?\n/).length,
		localizationMode,
		hasDataLocalizeSkip: source.includes('data-localize-skip'),
		usesTranslateText: source.includes('translateText') || /function\s+t\(/.test(source),
		usesLocaleText: source.includes('localeText'),
		longUncoveredTranslations,
		rawEnglishTemplateFragments,
		states,
		manualChecks: collectManualChecks(source, states),
		compileStatus
	};
}

function buildMarkdown(summary, routes) {
	const lines = [];

	lines.push('# Localization Verification Report');
	lines.push('');
	lines.push(`Generated: ${new Date().toISOString()}`);
	lines.push('');
	lines.push('## Summary');
	lines.push('');
	lines.push(`- Total game routes scanned: ${summary.totalRoutes}`);
	lines.push(`- Native-localized routes: ${summary.nativeRoutes}`);
	lines.push(`- Legacy fallback routes: ${summary.legacyRoutes}`);
	lines.push(`- Routes with uncovered long translation strings: ${summary.routesWithUncoveredTranslations}`);
	lines.push(`- Routes with compile failures: ${summary.compileFailures}`);
	lines.push('');
	lines.push('## Route Checklist');
	lines.push('');

	for (const route of routes) {
		lines.push(`### ${route.routePath}`);
		lines.push('');
		lines.push(`- File: \`${route.filePath}\``);
		lines.push(`- Mode: \`${route.localizationMode}\``);
		lines.push(`- Root skip marker: \`${route.hasDataLocalizeSkip}\``);
		lines.push(`- Compile status: \`${route.compileStatus.ok ? 'ok' : 'failed'}\``);
		lines.push(`- Manual checks: ${route.manualChecks.length ? route.manualChecks.join(', ') : 'none detected'}`);

		if (route.longUncoveredTranslations.length) {
			lines.push(`- Uncovered long translations: ${route.longUncoveredTranslations.length}`);
			for (const item of route.longUncoveredTranslations.slice(0, 5)) {
				lines.push(`- Missing exact coverage: ${item}`);
			}
		}

		if (!route.compileStatus.ok) {
			lines.push(`- Compile error: ${route.compileStatus.message}`);
		}

		lines.push('');
	}

	return `${lines.join('\n')}\n`;
}

const nativeRoutes = extractRouteSet('NATIVE_LOCALIZED_ROUTES');
const legacyRoutes = extractRouteSet('LEGACY_GAME_ROUTES');
const routeFiles = routeScanRoots.flatMap((root) => walk(root));
const routeReports = routeFiles
	.map((filePath) => analyzeRoute(filePath, nativeRoutes, legacyRoutes))
	.sort((left, right) => left.routePath.localeCompare(right.routePath));

const summary = {
	totalRoutes: routeReports.length,
	nativeRoutes: routeReports.filter((route) => route.localizationMode === 'native').length,
	legacyRoutes: routeReports.filter((route) => route.localizationMode === 'legacy').length,
	routesWithUncoveredTranslations: routeReports.filter(
		(route) => route.longUncoveredTranslations.length > 0
	).length,
	compileFailures: routeReports.filter((route) => !route.compileStatus.ok).length
};

fs.mkdirSync(reportsDir, { recursive: true });
fs.writeFileSync(reportJsonPath, JSON.stringify({ summary, routes: routeReports }, null, 2));
fs.writeFileSync(reportMdPath, buildMarkdown(summary, routeReports));

console.log(`Localization verification report written to ${path.relative(projectRoot, reportJsonPath)}`);
console.log(`Native routes: ${summary.nativeRoutes}`);
console.log(`Legacy routes: ${summary.legacyRoutes}`);
console.log(`Routes with uncovered long translations: ${summary.routesWithUncoveredTranslations}`);
console.log(`Compile failures: ${summary.compileFailures}`);

import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { parse } from 'svelte/compiler';
import { getRouteLocalizationMode } from '../src/lib/i18n/route-localization.js';
import {
	getGoNoGoStimulusPair,
	getTaskDifficultyDescription
} from '../src/lib/i18n/task-ui.js';
import { translateText } from '../src/lib/i18n/translator.js';

const projectRoot = process.cwd();
const routesRoot = path.join(projectRoot, 'src', 'routes');
const scanRoots = [
	path.join(projectRoot, 'src', 'routes', 'training'),
	path.join(projectRoot, 'src', 'routes', 'baseline', 'tasks')
];
const userFacingAttributes = new Set(['placeholder', 'aria-label', 'title', 'alt']);
const allowedFragments = [
	'NeuroBloom',
	'MS',
	'ADHD',
	'WCST',
	'DCCS',
	'PASAT',
	'CPT',
	'UFOV',
	'AX',
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
const longTranslationCallPattern =
	/(?:\bt|translateText)\(\s*(['"`])((?:\\.|(?!\1)[\s\S])+?)\1(?:\s*,[\s\S]*?)?\)/g;

function collectFiles(dir, output = []) {
	for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
		const fullPath = path.join(dir, entry.name);
		if (entry.isDirectory()) {
			collectFiles(fullPath, output);
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

function stripPreservedStimuli(text) {
	return text
		.replace(/"([A-Z])"/g, '""')
		.replace(/\b[A-Z]\b/g, '')
		.replace(/[→←]/g, ' ')
		.replace(/\s+/g, ' ')
		.trim();
}

function looksLikeEnglishUiText(text) {
	const normalized = stripPreservedStimuli(stripAllowedFragments(normalizeText(text)));

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

function createSharedTaskUiFinding(routePath, sourceText, localizedText) {
	return {
		filePath: path.join(projectRoot, 'src', 'lib', 'i18n', 'task-ui.js'),
		routePath,
		localizationMode: 'native',
		kind: 'shared-task-ui',
		line: 1,
		column: 1,
		sourceText,
		localizedText
	};
}

function auditSharedTaskUi() {
	const findings = [];

	for (const taskKey of ['pasat', 'gonogo']) {
		for (let difficulty = 1; difficulty <= 10; difficulty += 1) {
			const localizedText = normalizeText(getTaskDifficultyDescription(taskKey, difficulty, 'bn'));

			if (!localizedText || isResidualEnglish(localizedText)) {
				findings.push(
					createSharedTaskUiFinding(
						`/training/${taskKey}`,
						`${taskKey} difficulty ${difficulty} Bangla description`,
						localizedText || '<missing>'
					)
				);
			}
		}
	}

	for (const stimulusSet of ['basic', 'similar', 'complex']) {
		const pair = getGoNoGoStimulusPair(stimulusSet, 'bn');
		const localizedText = `${pair.go || '<missing>'} / ${pair.nogo || '<missing>'}`;

		if (!pair.go || !pair.nogo || /[A-Za-z]/.test(pair.go) || /[A-Za-z]/.test(pair.nogo)) {
			findings.push(
				createSharedTaskUiFinding(
					'/training/gonogo',
					`gonogo ${stimulusSet} Bangla stimuli`,
					localizedText
				)
			);
		}
	}

	const shapePair = getGoNoGoStimulusPair('shapes', 'bn');
	if (!shapePair.go || !shapePair.nogo) {
		findings.push(
			createSharedTaskUiFinding(
				'/training/gonogo',
				'gonogo shapes Bangla stimuli',
				`${shapePair.go || '<missing>'} / ${shapePair.nogo || '<missing>'}`
			)
		);
	}

	return findings;
}

function createLocator(source) {
	const lineStarts = [0];

	for (let index = 0; index < source.length; index += 1) {
		if (source[index] === '\n') {
			lineStarts.push(index + 1);
		}
	}

	return (position) => {
		let line = 0;
		while (line + 1 < lineStarts.length && lineStarts[line + 1] <= position) {
			line += 1;
		}

		return {
			line: line + 1,
			column: position - lineStarts[line] + 1
		};
	};
}

function getNodeStart(node) {
	return typeof node?.start === 'number'
		? node.start
		: typeof node?.expression?.start === 'number'
			? node.expression.start
			: 0;
}

function getRootNodes(ast) {
	if (Array.isArray(ast?.fragment?.nodes)) {
		return ast.fragment.nodes;
	}

	if (Array.isArray(ast?.html?.children)) {
		return ast.html.children;
	}

	return [];
}

function getChildNodes(block) {
	if (Array.isArray(block?.nodes)) {
		return block.nodes;
	}

	if (Array.isArray(block?.children)) {
		return block.children;
	}

	return [];
}

function localizeForRoute(text, localizationMode) {
	const options = localizationMode === 'observe' ? { aggressive: true } : {};
	return translateText(text, 'bn', options);
}

function isResidualEnglish(text) {
	return looksLikeEnglishUiText(text);
}

function addFinding(findings, filePath, routePath, localizationMode, locator, node, kind, sourceText) {
	const normalizedSource = normalizeText(sourceText);
	const localizedText =
		localizationMode === 'observe'
			? normalizeText(localizeForRoute(normalizedSource, localizationMode))
			: normalizedSource;

	if (!isResidualEnglish(localizedText)) {
		return;
	}

	const location = locator(getNodeStart(node));
	findings.push({
		filePath,
		routePath,
		localizationMode,
		kind,
		line: location.line,
		column: location.column,
		sourceText: normalizedSource,
		localizedText
	});
}

function inspectAttributes(
	findings,
	filePath,
	routePath,
	localizationMode,
	locator,
	attributes = []
) {
	for (const attribute of attributes) {
		if (!userFacingAttributes.has(attribute.name) || !Array.isArray(attribute.value)) {
			continue;
		}

		const textValue = attribute.value
			.filter((part) => part.type === 'Text')
			.map((part) => part.data)
			.join(' ');

		if (looksLikeEnglishUiText(textValue)) {
			addFinding(
				findings,
				filePath,
				routePath,
				localizationMode,
				locator,
				attribute,
				`attribute:${attribute.name}`,
				textValue
			);
		}
	}
}

function walkNodes(findings, filePath, routePath, localizationMode, locator, nodes = []) {
	for (const node of nodes) {
		switch (node.type) {
			case 'Text': {
				const text = normalizeText(node.data || '');
				if (looksLikeEnglishUiText(text)) {
					addFinding(
						findings,
						filePath,
						routePath,
						localizationMode,
						locator,
						node,
						'text',
						text
					);
				}
				break;
			}

			case 'Element':
			case 'RegularElement':
			case 'InlineComponent':
			case 'SvelteElement':
			case 'Slot':
			case 'Component': {
				inspectAttributes(
					findings,
					filePath,
					routePath,
					localizationMode,
					locator,
					node.attributes
				);
				const fragmentNodes = getChildNodes(node.fragment);
				const childNodes = fragmentNodes.length > 0 ? fragmentNodes : getChildNodes(node);
				if (childNodes.length > 0) {
					walkNodes(findings, filePath, routePath, localizationMode, locator, childNodes);
				}
				break;
			}

			case 'IfBlock':
			case 'EachBlock':
			case 'AwaitBlock':
			case 'KeyBlock': {
				const directChildNodes = getChildNodes(node);
				const fragmentNodes = getChildNodes(node.fragment);
				const elseNodes = getChildNodes(node.else);
				const pendingNodes = getChildNodes(node.pending);
				const thenNodes = getChildNodes(node.then);
				const catchNodes = getChildNodes(node.catch);

				if (directChildNodes.length > 0) {
					walkNodes(findings, filePath, routePath, localizationMode, locator, directChildNodes);
				}
				if (fragmentNodes.length > 0) {
					walkNodes(findings, filePath, routePath, localizationMode, locator, fragmentNodes);
				}
				if (elseNodes.length > 0) {
					walkNodes(findings, filePath, routePath, localizationMode, locator, elseNodes);
				}
				if (pendingNodes.length > 0) {
					walkNodes(findings, filePath, routePath, localizationMode, locator, pendingNodes);
				}
				if (thenNodes.length > 0) {
					walkNodes(findings, filePath, routePath, localizationMode, locator, thenNodes);
				}
				if (catchNodes.length > 0) {
					walkNodes(findings, filePath, routePath, localizationMode, locator, catchNodes);
				}
				break;
			}

			default:
				break;
		}
	}
}

function auditFile(filePath) {
	const source = fs.readFileSync(filePath, 'utf8');
	const locator = createLocator(source);
	const ast = parse(source);
	const findings = [];
	const routePath = routePathFromFile(filePath);
	const localizationMode = getRouteLocalizationMode(routePath);

	walkNodes(findings, filePath, routePath, localizationMode, locator, getRootNodes(ast));

	for (const match of source.matchAll(longTranslationCallPattern)) {
		const literal = normalizeText(match[2] || '');
		if (literal.includes('${') || !looksLikeEnglishUiText(literal)) {
			continue;
		}

		const localizedText = normalizeText(localizeForRoute(literal, localizationMode));
		if (!isResidualEnglish(localizedText)) {
			continue;
		}

		const location = locator(match.index || 0);
		findings.push({
			filePath,
			routePath,
			localizationMode,
			kind: 'translation-call',
			line: location.line,
			column: location.column,
			sourceText: literal,
			localizedText
		});
	}

	return {
		routePath,
		localizationMode,
		findings
	};
}

const files = scanRoots.flatMap((root) => collectFiles(root));
const routeAudits = files.map((filePath) => auditFile(filePath));
const findings = [...routeAudits.flatMap((audit) => audit.findings), ...auditSharedTaskUi()];
const observedRoutes = routeAudits.filter((audit) => audit.localizationMode === 'observe').length;
const nativeRoutes = routeAudits.filter((audit) => audit.localizationMode === 'native').length;

if (findings.length === 0) {
	console.log(
		`Bangla UI audit passed. Scanned ${routeAudits.length} game routes with ${nativeRoutes} native and ${observedRoutes} observer-backed routes. No residual English UI text found after applying each route's localization path.`
	);
	process.exit(0);
}

console.log(
	`Bangla UI audit found ${findings.length} residual English issue(s) across ${routeAudits.length} game routes:`
);
for (const finding of findings) {
	const relativePath = path.relative(projectRoot, finding.filePath);
	console.log(
		`${relativePath}:${finding.line}:${finding.column} [${finding.localizationMode}:${finding.kind}] ${finding.sourceText} => ${finding.localizedText}`
	);
}

process.exit(1);

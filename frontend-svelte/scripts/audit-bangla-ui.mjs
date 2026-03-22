import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { parse } from 'svelte/compiler';

const projectRoot = process.cwd();
const catalogSource = fs.readFileSync(
	path.join(projectRoot, 'src', 'lib', 'i18n', 'catalog.js'),
	'utf8'
);
const scanRoots = [
	path.join(projectRoot, 'src', 'routes', 'training'),
	path.join(projectRoot, 'src', 'routes', 'baseline', 'tasks')
];
const userFacingAttributes = new Set(['placeholder', 'aria-label', 'title', 'alt']);
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
	const singleQuoted = `'${text.replace(/\\/g, '\\\\').replace(/'/g, "\\'")}'`;
	const doubleQuoted = `"${text.replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"`;
	return catalogSource.includes(singleQuoted) || catalogSource.includes(doubleQuoted);
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

function addFinding(findings, filePath, locator, node, kind, text) {
	const location = locator(getNodeStart(node));
	findings.push({
		filePath,
		kind,
		line: location.line,
		column: location.column,
		text: normalizeText(text)
	});
}

function inspectAttributes(findings, filePath, locator, attributes = []) {
	for (const attribute of attributes) {
		if (!userFacingAttributes.has(attribute.name) || !Array.isArray(attribute.value)) {
			continue;
		}

		const textValue = attribute.value
			.filter((part) => part.type === 'Text')
			.map((part) => part.data)
			.join(' ');

		if (looksLikeEnglishUiText(textValue)) {
			addFinding(findings, filePath, locator, attribute, `attribute:${attribute.name}`, textValue);
		}
	}
}

function walkNodes(findings, filePath, locator, nodes = []) {
	for (const node of nodes) {
		switch (node.type) {
			case 'Text': {
				const text = normalizeText(node.data || '');
				if (looksLikeEnglishUiText(text)) {
					addFinding(findings, filePath, locator, node, 'text', text);
				}
				break;
			}

			case 'Element':
			case 'InlineComponent':
			case 'SvelteElement':
			case 'Slot':
			case 'Component': {
				inspectAttributes(findings, filePath, locator, node.attributes);
				if (Array.isArray(node.fragment?.nodes)) {
					walkNodes(findings, filePath, locator, node.fragment.nodes);
				}
				break;
			}

			case 'IfBlock':
			case 'EachBlock':
			case 'AwaitBlock':
			case 'KeyBlock': {
				if (Array.isArray(node.fragment?.nodes)) {
					walkNodes(findings, filePath, locator, node.fragment.nodes);
				}
				if (Array.isArray(node.else?.nodes)) {
					walkNodes(findings, filePath, locator, node.else.nodes);
				}
				if (Array.isArray(node.pending?.nodes)) {
					walkNodes(findings, filePath, locator, node.pending.nodes);
				}
				if (Array.isArray(node.then?.nodes)) {
					walkNodes(findings, filePath, locator, node.then.nodes);
				}
				if (Array.isArray(node.catch?.nodes)) {
					walkNodes(findings, filePath, locator, node.catch.nodes);
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

	walkNodes(findings, filePath, locator, ast.fragment?.nodes || []);

	if (!source.includes('data-localize-skip')) {
		findings.push({
			filePath,
			kind: 'route',
			line: 1,
			column: 1,
			text: 'Route still relies on legacy DOM localization.'
		});
	}

	for (const match of source.matchAll(longTranslationCallPattern)) {
		const literal = normalizeText(match[2] || '');

		if (literal.length < 30 || !looksLikeEnglishUiText(literal) || hasExactCatalogCoverage(literal)) {
			continue;
		}

		const location = locator(match.index || 0);
		findings.push({
			filePath,
			kind: 'translation-call',
			line: location.line,
			column: location.column,
			text: literal
		});
	}

	return findings;
}

const files = scanRoots.flatMap((root) => collectFiles(root));
const findings = files.flatMap((filePath) => auditFile(filePath));

if (findings.length === 0) {
	console.log('Bangla UI audit passed. No static English UI text found in training or baseline game pages.');
	process.exit(0);
}

console.log(`Bangla UI audit found ${findings.length} issue(s):`);
for (const finding of findings) {
	const relativePath = path.relative(projectRoot, finding.filePath);
	console.log(`${relativePath}:${finding.line}:${finding.column} [${finding.kind}] ${finding.text}`);
}

process.exit(1);

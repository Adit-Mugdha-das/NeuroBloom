import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const projectRoot = process.cwd();
const scanRoots = [path.join(projectRoot, 'src'), path.join(projectRoot, 'scripts')];
const scannedExtensions = new Set([
	'.css',
	'.html',
	'.js',
	'.json',
	'.mjs',
	'.svelte',
	'.ts'
]);
const ignoredDirectories = new Set([
	'.git',
	'.svelte-kit',
	'build',
	'dist',
	'node_modules'
]);
const allowedLatinTerms = new Set([
	'ADHD',
	'Addition',
	'AI',
	'ANT',
	'API',
	'Auditory',
	'AX',
	'A-B',
	'Backspace',
	'Ball',
	'Benton',
	'BMI',
	'BRB',
	'BRB-N',
	'B-A',
	'BICAMS',
	'CANTAB',
	'CPT',
	'CSV',
	'Ctrl',
	'CV',
	'Corsi',
	'COWAT',
	'DCCS',
	'Diamond',
	'Dual',
	'Enter',
	'Eriksen',
	'EWMA',
	'F1',
	'Field',
	'Gelade',
	'Go',
	'GO',
	'GMC',
	'Gronwall',
	'Hamsher',
	'Hornsby',
	'Inspection',
	'IIV',
	'Jacobson',
	'JSON',
	'LEFT',
	'MACFIMS',
	'Making',
	'Mesulam',
	'Mosher',
	'MOT',
	'MS',
	'N-Back',
	'N-back',
	'NeuroBloom',
	'No',
	'No-Go',
	'NO',
	'NO-GO',
	'Operation',
	'OSPAN',
	'Pattern',
	'Paced',
	'PASAT',
	'PDF',
	'Pearson',
	'PRESS',
	'Pylyshyn',
	'RIGHT',
	'RCI',
	'RT',
	'SAME',
	'SART',
	'SDMT',
	'Serial',
	'Serial-Addition',
	'Shift',
	'Smith',
	'Space',
	'SPACE',
	'Spatial',
	'Spacebar',
	'SPACEBAR',
	'Span',
	'Storm',
	'Tab',
	'Task',
	'Test',
	'Time',
	'Trail',
	'TMT',
	'TMT-A',
	'Treisman',
	'Truax',
	'UFOV',
	'Useful',
	'Vickers',
	'View',
	'WCST',
	'back',
	'd',
	'ms',
	'n',
	'Part',
	'prime',
	's'
]);

function collectFiles(directory, output = []) {
	if (!fs.existsSync(directory)) {
		return output;
	}

	for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
		if (ignoredDirectories.has(entry.name)) {
			continue;
		}

		const fullPath = path.join(directory, entry.name);
		if (entry.isDirectory()) {
			collectFiles(fullPath, output);
			continue;
		}

		if (entry.isFile() && scannedExtensions.has(path.extname(entry.name))) {
			output.push(fullPath);
		}
	}

	return output;
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

function addPatternFindings(findings, filePath, source, locator) {
	const rules = [
		{ kind: 'literal-question-marks', pattern: /\?{4,}/g },
		{ kind: 'replacement-character', pattern: /\uFFFD/g },
		{ kind: 'bangla-mojibake', pattern: /\u00E0[\u00A6\u00A7]/g },
		{ kind: 'punctuation-mojibake', pattern: /\u00E2\u20AC/g },
		{ kind: 'nbsp-mojibake', pattern: /\u00C2\u00A0/g }
	];

	for (const rule of rules) {
		for (const match of source.matchAll(rule.pattern)) {
			const location = locator(match.index || 0);
			findings.push({
				filePath,
				kind: rule.kind,
				line: location.line,
				column: location.column,
				detail: match[0]
			});
		}
	}
}

function stripAllowedText(content) {
	return content
		.replace(/\$\{[\s\S]*?\}/g, ' ')
		.replace(/https?:\/\/\S+/g, ' ')
		.replace(/[A-Z]:\\\S+/g, ' ');
}

function normalizeLatinToken(value) {
	return value.replace(/^[^A-Za-z0-9]+|[^A-Za-z0-9]+$/g, '');
}

function isAllowedLatinWord(word) {
	const tokens = word.split(/[+/]/).map(normalizeLatinToken).filter(Boolean);

	if (tokens.length === 0) {
		return true;
	}

	return tokens.every((token) => {
		if (allowedLatinTerms.has(token)) {
			return true;
		}

		if (/^[A-Z]$/.test(token)) {
			return true;
		}

		if (/^u[0-9A-Fa-f]{4}$/.test(token)) {
			return true;
		}

		return false;
	});
}

function readStringLiteral(source, startIndex) {
	const quote = source[startIndex];
	let content = '';

	for (let index = startIndex + 1; index < source.length; index += 1) {
		const character = source[index];

		if (character === '\\') {
			content += source.slice(index, index + 2);
			index += 1;
			continue;
		}

		if (character === quote) {
			return {
				content,
				endIndex: index + 1
			};
		}

		content += character;
	}

	return {
		content,
		endIndex: source.length
	};
}

function addMixedBanglaFindings(findings, filePath, source, locator) {
	if (filePath.endsWith(path.join('src', 'lib', 'i18n', 'translator.js'))) {
		return;
	}

	const latinWordPattern = /[A-Za-z][A-Za-z0-9+./#-]*/g;
	const mixedSource = extractMixedScanSource(filePath, source);

	for (let index = 0; index < mixedSource.length; index += 1) {
		const character = mixedSource[index];
		if (character !== "'" && character !== '"') {
			continue;
		}

		if (
			character === "'" &&
			/[A-Za-z]/.test(mixedSource[index - 1] || '') &&
			/[A-Za-z]/.test(mixedSource[index + 1] || '')
		) {
			continue;
		}

		const startIndex = index;
		const literal = readStringLiteral(mixedSource, index);
		index = literal.endIndex - 1;

		if (!/[\u0980-\u09FF]/.test(literal.content)) {
			continue;
		}

		const content = stripAllowedText(literal.content);
		const words = [...new Set(content.match(latinWordPattern) || [])].filter(
			(word) => !isAllowedLatinWord(word)
		);

		if (words.length === 0) {
			continue;
		}

		const location = locator(startIndex);
		findings.push({
			filePath,
			kind: 'mixed-bangla-latin',
			line: location.line,
			column: location.column,
			detail: words.join(', ')
		});
	}
}

function extractMixedScanSource(filePath, source) {
	if (path.extname(filePath) !== '.svelte') {
		return source;
	}

	const output = Array.from({ length: source.length }, () => ' ');
	const scriptPattern = /<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/gi;

	for (const match of source.matchAll(scriptPattern)) {
		const scriptStart = (match.index || 0) + match[0].indexOf(match[1]);
		for (let offset = 0; offset < match[1].length; offset += 1) {
			output[scriptStart + offset] = match[1][offset];
		}
	}

	return output.join('');
}

function auditFile(filePath) {
	const source = fs.readFileSync(filePath, 'utf8');
	const locator = createLocator(source);
	const findings = [];

	addPatternFindings(findings, filePath, source, locator);
	addMixedBanglaFindings(findings, filePath, source, locator);

	return findings;
}

const files = scanRoots.flatMap((root) => collectFiles(root));
const findings = files.flatMap((filePath) => auditFile(filePath));

if (findings.length === 0) {
	console.log(`Locale integrity audit passed. Scanned ${files.length} source files.`);
	process.exit(0);
}

console.log(`Locale integrity audit found ${findings.length} issue(s) across ${files.length} source files:`);
for (const finding of findings) {
	const relativePath = path.relative(projectRoot, finding.filePath);
	console.log(`${relativePath}:${finding.line}:${finding.column} [${finding.kind}] ${finding.detail}`);
}

process.exit(1);

import {
	DIGIT_MAP,
	EXACT_TRANSLATIONS,
	PATTERN_TRANSLATIONS,
	PHRASE_TRANSLATIONS,
	WORD_TRANSLATIONS
} from './catalog.js';

export const DEFAULT_LOCALE = 'en';
export const SUPPORTED_LOCALES = [
	{ value: 'en', label: 'English' },
	{ value: 'bn', label: 'বাংলা' }
];

const REVERSE_DIGIT_MAP = Object.fromEntries(
	Object.entries(DIGIT_MAP).map(([digit, localizedDigit]) => [localizedDigit, digit])
);
const PROTECTED_SEGMENT_PATTERNS = [
	/\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/giu,
	/\bhttps?:\/\/[^\s<>"')]+/giu,
	/\bwww\.[^\s<>"')]+/giu
];
const BANGLA_STIMULUS_MAP = {
	A: 'অ',
	B: 'আ',
	C: 'ই',
	D: 'ঈ',
	E: 'উ',
	F: 'ঊ',
	G: 'এ',
	H: 'ঐ',
	I: 'ও',
	J: 'ঔ',
	K: 'ক',
	L: 'খ',
	M: 'গ',
	N: 'ঘ',
	O: 'ঙ',
	P: 'চ',
	Q: 'ছ',
	R: 'জ',
	S: 'ঝ',
	T: 'ট',
	U: 'ঠ',
	V: 'ড',
	W: 'ঢ',
	X: 'ত',
	Y: 'থ',
	Z: 'দ'
};

export function normalizeLocale(value) {
	return value === 'bn' ? 'bn' : 'en';
}

const PHRASE_TRANSLATION_ENTRIES = Object.entries(PHRASE_TRANSLATIONS).sort(
	(a, b) => b[0].length - a[0].length
);
const WORD_TRANSLATION_ENTRIES = Object.entries(WORD_TRANSLATIONS).sort(
	(a, b) => b[0].length - a[0].length
);

function preserveWhitespace(originalText, translatedText) {
	const leadingWhitespace = originalText.match(/^\s*/u)?.[0] ?? '';
	const trailingWhitespace = originalText.match(/\s*$/u)?.[0] ?? '';
	return `${leadingWhitespace}${translatedText}${trailingWhitespace}`;
}

function collapseWhitespace(value) {
	return value.replace(/\s+/gu, ' ').trim();
}

export function toBanglaDigits(value) {
	return String(value).replace(/\d/g, (digit) => DIGIT_MAP[digit] || digit);
}

export function normalizeLocalizedDigits(value) {
	return String(value).replace(/[০-৯]/g, (digit) => REVERSE_DIGIT_MAP[digit] || digit);
}

export function localizeDigitInput(value, targetLocale = DEFAULT_LOCALE) {
	const normalizedValue = normalizeLocalizedDigits(value);
	return targetLocale === 'bn' ? toBanglaDigits(normalizedValue) : normalizedValue;
}

function toAlphabeticToken(index) {
	let current = index;
	let token = '';

	do {
		token = String.fromCharCode(65 + (current % 26)) + token;
		current = Math.floor(current / 26) - 1;
	} while (current >= 0);

	return `⟦${token}⟧`;
}

function protectSegments(input) {
	const segments = [];
	let protectedText = input;

	for (const pattern of PROTECTED_SEGMENT_PATTERNS) {
		protectedText = protectedText.replace(pattern, (match) => {
			const token = toAlphabeticToken(segments.length);
			segments.push({ token, value: match });
			return token;
		});
	}

	return {
		text: protectedText,
		restore(value) {
			return segments.reduce(
				(result, segment) => result.split(segment.token).join(segment.value),
				value
			);
		}
	};
}

function escapeRegExp(value) {
	return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function applyExactTranslation(text) {
	if (EXACT_TRANSLATIONS[text]) {
		return EXACT_TRANSLATIONS[text];
	}

	if (PHRASE_TRANSLATIONS[text]) {
		return PHRASE_TRANSLATIONS[text];
	}

	// Some task-route catalogs still store full-sentence entries in the shared
	// word table. Treat whole-string hits as exact matches before falling back
	// to partial replacement so we don't leak mixed English/Bangla UI.
	if (WORD_TRANSLATIONS[text]) {
		return WORD_TRANSLATIONS[text];
	}

	return null;
}

function applyPatternTranslation(text) {
	for (const rule of PATTERN_TRANSLATIONS) {
		if (!rule.pattern.test(text)) continue;

		return text.replace(rule.pattern, (...args) => rule.replace(...args));
	}

	return null;
}

function applyPhraseTranslation(text) {
	let nextText = text;

	for (const [source, translated] of PHRASE_TRANSLATION_ENTRIES) {
		nextText = nextText.replace(new RegExp(escapeRegExp(source), 'giu'), translated);
	}

	return nextText;
}

function applyWordTranslation(text) {
	let nextText = text;

	for (const [source, translated] of WORD_TRANSLATION_ENTRIES) {
		nextText = nextText.replace(
			new RegExp(`\\b${escapeRegExp(source)}\\b`, 'giu'),
			translated
		);
	}

	return nextText;
}

function countLatinWords(text) {
	return [...text.matchAll(/\b[A-Za-z][A-Za-z'-]*\b/gu)].length;
}

function shouldUsePhraseFallback(text) {
	const latinWordCount = countLatinWords(text);
	return latinWordCount > 0 && latinWordCount <= 8 && text.length <= 80;
}

function shouldUseWordFallback(text) {
	const latinWordCount = countLatinWords(text);
	return latinWordCount > 0 && latinWordCount <= 4 && text.length <= 48;
}

function normalizeTranslationOptions(options = {}) {
	return {
		aggressive: options?.aggressive === true
	};
}

function localizeStimulusToken(value) {
	if (/^[A-Z]$/u.test(value)) {
		return BANGLA_STIMULUS_MAP[value.toUpperCase()] || value;
	}

	if (/^\d+$/u.test(value)) {
		return toBanglaDigits(value);
	}

	return value;
}

function localizeStimulusInlineText(input) {
	const trimmedInput = input.trim();
	if (!trimmedInput) {
		return null;
	}

	if (/^[A-Z]$/u.test(trimmedInput) || /^\d+$/u.test(trimmedInput)) {
		return preserveWhitespace(input, localizeStimulusToken(trimmedInput));
	}

	const tokenPattern = /\b([A-Z]|\d+)\b/gu;
	const tokens = [...trimmedInput.matchAll(tokenPattern)];
	if (tokens.length < 2) {
		return null;
	}

	const structure = trimmedInput.replace(tokenPattern, 'X');
	if (!/^[X\s\-–—→,./|:+()=%]+$/u.test(structure)) {
		return null;
	}

	const localized = input.replace(tokenPattern, (token) => localizeStimulusToken(token));
	return localized === input ? null : localized;
}

function translateBangla(input, options = {}) {
	if (!input) return input;

	const translationOptions = normalizeTranslationOptions(options);
	const protectedInput = protectSegments(input);
	const normalizedText = collapseWhitespace(protectedInput.text);
	if (!normalizedText) {
		return input;
	}

	const localizedStimulusText = localizeStimulusInlineText(protectedInput.text);
	if (localizedStimulusText) {
		return protectedInput.restore(localizedStimulusText);
	}

	const exact = applyExactTranslation(normalizedText);
	if (exact) {
		return preserveWhitespace(input, protectedInput.restore(toBanglaDigits(exact)));
	}

	const pattern = applyPatternTranslation(normalizedText);
	if (pattern) {
		const translatedPattern = applyWordTranslation(applyPhraseTranslation(pattern));
		return preserveWhitespace(input, protectedInput.restore(toBanglaDigits(translatedPattern)));
	}

	const phraseTranslated =
		translationOptions.aggressive || shouldUsePhraseFallback(normalizedText)
			? applyPhraseTranslation(normalizedText)
			: normalizedText;
	const wordTranslated =
		translationOptions.aggressive || shouldUseWordFallback(normalizedText)
			? applyWordTranslation(phraseTranslated)
			: phraseTranslated;

	return preserveWhitespace(input, protectedInput.restore(toBanglaDigits(wordTranslated)));
}

export function translateText(input, targetLocale = DEFAULT_LOCALE, options = {}) {
	if (input === null || input === undefined) return '';

	const normalizedText = String(input);
	if (normalizeLocale(targetLocale) !== 'bn') {
		return normalizedText;
	}

	return translateBangla(normalizedText, options);
}

export function t(input, targetLocale = DEFAULT_LOCALE, options = {}) {
	return translateText(input, targetLocale, options);
}

export function formatNumber(value, targetLocale = DEFAULT_LOCALE, options = {}) {
	if (value === null || value === undefined || value === '') {
		return '';
	}

	const numericValue = typeof value === 'number' ? value : Number(value);

	if (!Number.isFinite(numericValue)) {
		return translateText(value, targetLocale);
	}

	const localeCode = normalizeLocale(targetLocale) === 'bn' ? 'bn-BD' : 'en-US';
	return new Intl.NumberFormat(localeCode, options).format(numericValue);
}

export function formatPercent(value, targetLocale = DEFAULT_LOCALE, options = {}) {
	if (value === null || value === undefined || value === '') {
		return '';
	}

	const minimumFractionDigits =
		options.minimumFractionDigits ?? (Number.isInteger(Number(value)) ? 0 : 1);
	const maximumFractionDigits = options.maximumFractionDigits ?? minimumFractionDigits;

	return `${formatNumber(value, targetLocale, {
		...options,
		minimumFractionDigits,
		maximumFractionDigits
	})}%`;
}

export function localizeStimulusSymbol(value, targetLocale = DEFAULT_LOCALE) {
	if (value === null || value === undefined) {
		return '';
	}

	const normalizedValue = String(value).trim();
	if (!normalizedValue) {
		return normalizedValue;
	}

	if (normalizeLocale(targetLocale) !== 'bn') {
		return normalizedValue;
	}

	if (/^[A-Za-z]$/u.test(normalizedValue)) {
		return BANGLA_STIMULUS_MAP[normalizedValue.toUpperCase()] || normalizedValue;
	}

	if (/^\d+$/u.test(normalizedValue)) {
		return formatNumber(normalizedValue, targetLocale);
	}

	return translateText(normalizedValue, targetLocale);
}

export function localizeStimulusSequence(values, targetLocale = DEFAULT_LOCALE) {
	if (!Array.isArray(values)) {
		return [];
	}

	return values.map((value) => localizeStimulusSymbol(value, targetLocale));
}

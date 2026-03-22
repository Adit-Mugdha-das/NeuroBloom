import { browser } from '$app/environment';
import { get, writable } from 'svelte/store';
import { updateUserPreferences } from '$lib/stores.js';
import {
	DIGIT_MAP,
	EXACT_TRANSLATIONS,
	PATTERN_TRANSLATIONS,
	PHRASE_TRANSLATIONS,
	WORD_TRANSLATIONS
} from './catalog.js';

const DEFAULT_LOCALE = 'en';
const STORAGE_KEY = 'preferred-locale';
const REVERSE_DIGIT_MAP = Object.fromEntries(
	Object.entries(DIGIT_MAP).map(([digit, localizedDigit]) => [localizedDigit, digit])
);
const ORIGINAL_ALERT = browser && typeof window !== 'undefined' ? window.alert.bind(window) : null;
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

export const SUPPORTED_LOCALES = [
	{ value: 'en', label: 'English' },
	{ value: 'bn', label: 'বাংলা' }
];

function normalizeLocale(value) {
	return value === 'bn' ? 'bn' : 'en';
}

function safeParse(value) {
	try {
		return value ? JSON.parse(value) : null;
	} catch (_error) {
		return null;
	}
}

function readBootstrappedLocale() {
	if (!browser) return null;

	const windowLocale = window.__NB_LOCALE__;
	if (windowLocale === 'en' || windowLocale === 'bn') {
		return windowLocale;
	}

	const attributeLocale =
		document.documentElement.dataset.localeBoot || document.documentElement.dataset.locale;

	if (attributeLocale === 'en' || attributeLocale === 'bn') {
		return attributeLocale;
	}

	return null;
}

function readStoredLocale() {
	if (!browser) return DEFAULT_LOCALE;

	const bootstrappedLocale = readBootstrappedLocale();
	if (bootstrappedLocale) {
		return bootstrappedLocale;
	}

	const storedUser = safeParse(localStorage.getItem('user'));
	const userPreference = storedUser?.preferences?.language;
	if (userPreference === 'en' || userPreference === 'bn') {
		return userPreference;
	}

	return normalizeLocale(localStorage.getItem(STORAGE_KEY));
}

const internalLocale = writable(readStoredLocale());

export const locale = {
	subscribe: internalLocale.subscribe
};

export function getLocale() {
	return get(internalLocale);
}

function setDocumentLocale(nextLocale) {
	if (!browser) return;

	document.documentElement.lang = nextLocale === 'bn' ? 'bn-BD' : 'en';
	document.documentElement.dataset.locale = nextLocale;
}

function syncAlertLocalization(nextLocale) {
	if (!browser || !ORIGINAL_ALERT || typeof window === 'undefined') {
		return;
	}

	window.alert = (message) => ORIGINAL_ALERT(translateText(message, nextLocale));
}

function markLocaleReady() {
	if (!browser) return;

	document.documentElement.dataset.localePending = 'false';
}

function persistLocale(nextLocale, syncUser = true) {
	if (!browser) return;

	localStorage.setItem(STORAGE_KEY, nextLocale);

	if (syncUser) {
		updateUserPreferences({ language: nextLocale });
	}
}

export function initializeLocale() {
	const nextLocale = readStoredLocale();
	internalLocale.set(nextLocale);
	setDocumentLocale(nextLocale);
	return nextLocale;
}

export function setLocale(nextLocale, options = {}) {
	const normalizedLocale = normalizeLocale(nextLocale);
	internalLocale.set(normalizedLocale);
	setDocumentLocale(normalizedLocale);
	persistLocale(normalizedLocale, options.syncUser !== false);
	return normalizedLocale;
}

export function localeText(variants, targetLocale = getLocale()) {
	if (typeof variants === 'string') {
		return variants;
	}

	const normalizedLocale = normalizeLocale(targetLocale);
	return variants?.[normalizedLocale] ?? variants?.en ?? variants?.bn ?? '';
}

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

export function localizeDigitInput(value, targetLocale = getLocale()) {
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
	const entries = Object.entries(PHRASE_TRANSLATIONS).sort((a, b) => b[0].length - a[0].length);

	for (const [source, translated] of entries) {
		nextText = nextText.replace(new RegExp(escapeRegExp(source), 'gu'), translated);
	}

	return nextText;
}

function applyWordTranslation(text) {
	let nextText = text;
	const entries = Object.entries(WORD_TRANSLATIONS).sort((a, b) => b[0].length - a[0].length);

	for (const [source, translated] of entries) {
		nextText = nextText.replace(
			new RegExp(`\\b${escapeRegExp(source)}\\b`, 'gu'),
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

function translateBangla(input) {
	if (!input) return input;

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

	const phraseTranslated = shouldUsePhraseFallback(normalizedText)
		? applyPhraseTranslation(normalizedText)
		: normalizedText;
	const wordTranslated = shouldUseWordFallback(normalizedText)
		? applyWordTranslation(phraseTranslated)
		: phraseTranslated;

	return preserveWhitespace(input, protectedInput.restore(toBanglaDigits(wordTranslated)));
}

export function translateText(input, targetLocale = getLocale()) {
	if (input === null || input === undefined) return '';

	const normalizedText = String(input);
	if (targetLocale !== 'bn') {
		return normalizedText;
	}

	return translateBangla(normalizedText);
}

export function t(input, targetLocale = getLocale()) {
	return translateText(input, targetLocale);
}

export function formatNumber(value, targetLocale = getLocale(), options = {}) {
	if (value === null || value === undefined || value === '') {
		return '';
	}

	const numericValue = typeof value === 'number' ? value : Number(value);

	if (!Number.isFinite(numericValue)) {
		return translateText(value, targetLocale);
	}

	const localeCode = targetLocale === 'bn' ? 'bn-BD' : 'en-US';
	return new Intl.NumberFormat(localeCode, options).format(numericValue);
}

export function formatPercent(value, targetLocale = getLocale(), options = {}) {
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

export function localizeStimulusSymbol(value, targetLocale = getLocale()) {
	if (value === null || value === undefined) {
		return '';
	}

	const normalizedValue = String(value).trim();
	if (!normalizedValue) {
		return normalizedValue;
	}

	if (targetLocale !== 'bn') {
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

export function localizeStimulusSequence(values, targetLocale = getLocale()) {
	if (!Array.isArray(values)) {
		return [];
	}

	return values.map((value) => localizeStimulusSymbol(value, targetLocale));
}

function shouldSkipElement(element) {
	if (!element) return true;

	if (element.closest('[data-localize-skip]')) return true;
	if (element.isContentEditable) return true;

	return ['SCRIPT', 'STYLE', 'NOSCRIPT', 'IFRAME', 'TEXTAREA'].includes(element.tagName);
}

function resolveSourceValue(store, key, currentValue) {
	const storedValue = store.get(key);
	if (!storedValue) {
		store.set(key, currentValue);
		return currentValue;
	}

	const englishVersion = translateText(storedValue, 'en');
	const banglaVersion = translateText(storedValue, 'bn');

	if (currentValue === englishVersion || currentValue === banglaVersion) {
		return storedValue;
	}

	store.set(key, currentValue);
	return currentValue;
}

function createTreeWalker(node) {
	return document.createTreeWalker(
		node,
		NodeFilter.SHOW_TEXT,
		{
			acceptNode(textNode) {
				if (!textNode.parentElement || shouldSkipElement(textNode.parentElement)) {
					return NodeFilter.FILTER_REJECT;
				}

				if (!textNode.nodeValue?.trim()) {
					return NodeFilter.FILTER_REJECT;
				}

				return NodeFilter.FILTER_ACCEPT;
			}
		}
	);
}

function translateTextNodes(root, activeLocale, sourceStore) {
	const walker = createTreeWalker(root);
	const nodes = [];

	while (walker.nextNode()) {
		nodes.push(walker.currentNode);
	}

	for (const textNode of nodes) {
		const sourceText = resolveSourceValue(sourceStore, textNode, textNode.nodeValue || '');
		const translatedText = translateText(sourceText, activeLocale);

		if (textNode.nodeValue !== translatedText) {
			textNode.nodeValue = translatedText;
		}
	}
}

function translateTextNode(textNode, activeLocale, sourceStore) {
	if (!textNode?.nodeValue?.trim()) {
		return;
	}

	const parentElement = textNode.parentElement;
	if (!parentElement || shouldSkipElement(parentElement)) {
		return;
	}

	const sourceText = resolveSourceValue(sourceStore, textNode, textNode.nodeValue || '');
	const translatedText = translateText(sourceText, activeLocale);

	if (textNode.nodeValue !== translatedText) {
		textNode.nodeValue = translatedText;
	}
}

function translateAttributes(root, activeLocale, attributeStore) {
	const elements = [];

	if (root instanceof Element) {
		elements.push(root);
	}

	if (root.querySelectorAll) {
		elements.push(...root.querySelectorAll('*'));
	}

	for (const element of elements) {
		if (shouldSkipElement(element)) continue;

		for (const attributeName of ['placeholder', 'title', 'aria-label']) {
			const currentValue = element.getAttribute(attributeName);
			if (!currentValue) continue;

			let sourceMap = attributeStore.get(element);
			if (!sourceMap) {
				sourceMap = new Map();
				attributeStore.set(element, sourceMap);
			}

			const sourceValue = resolveSourceValue(sourceMap, attributeName, currentValue);
			const translatedValue = translateText(sourceValue, activeLocale);

			if (currentValue !== translatedValue) {
				element.setAttribute(attributeName, translatedValue);
			}
		}
	}
}

function translateElementAttributes(element, activeLocale, attributeStore) {
	if (!(element instanceof Element) || shouldSkipElement(element)) {
		return;
	}

	for (const attributeName of ['placeholder', 'title', 'aria-label']) {
		const currentValue = element.getAttribute(attributeName);
		if (!currentValue) continue;

		let sourceMap = attributeStore.get(element);
		if (!sourceMap) {
			sourceMap = new Map();
			attributeStore.set(element, sourceMap);
		}

		const sourceValue = resolveSourceValue(sourceMap, attributeName, currentValue);
		const translatedValue = translateText(sourceValue, activeLocale);

		if (currentValue !== translatedValue) {
			element.setAttribute(attributeName, translatedValue);
		}
	}
}

function translateSubtree(root, activeLocale, textSourceStore, attributeSourceStore) {
	if (!root) {
		return;
	}

	if (root.nodeType === Node.TEXT_NODE) {
		translateTextNode(root, activeLocale, textSourceStore);
		return;
	}

	if (root.nodeType === Node.ELEMENT_NODE || root.nodeType === Node.DOCUMENT_FRAGMENT_NODE) {
		translateTextNodes(root, activeLocale, textSourceStore);
		translateAttributes(root, activeLocale, attributeSourceStore);
	}
}

export function localize(node) {
	if (!browser) {
		return {};
	}

	const textSourceStore = new WeakMap();
	const attributeSourceStore = new WeakMap();
	let isApplying = false;
	let pendingFullRefresh = false;
	let frameHandle = null;
	const pendingNodes = new Set();
	const pendingAttributeTargets = new Set();

	const flushTranslations = () => {
		frameHandle = null;
		if (isApplying) return;
		isApplying = true;

		try {
			const activeLocale = getLocale();
			if (pendingFullRefresh) {
				translateTextNodes(node, activeLocale, textSourceStore);
				translateAttributes(node, activeLocale, attributeSourceStore);
			} else {
				for (const pendingNode of pendingNodes) {
					translateSubtree(pendingNode, activeLocale, textSourceStore, attributeSourceStore);
				}

				for (const targetElement of pendingAttributeTargets) {
					translateElementAttributes(targetElement, activeLocale, attributeSourceStore);
				}
			}

			pendingFullRefresh = false;
			pendingNodes.clear();
			pendingAttributeTargets.clear();
			markLocaleReady();
		} finally {
			isApplying = false;
		}
	};

	const scheduleTranslations = () => {
		if (frameHandle !== null) return;

		if (typeof window !== 'undefined' && typeof window.requestAnimationFrame === 'function') {
			frameHandle = window.requestAnimationFrame(flushTranslations);
			return;
		}

		frameHandle = window.setTimeout(flushTranslations, 0);
	};

	const scheduleFullRefresh = () => {
		pendingFullRefresh = true;
		pendingNodes.clear();
		pendingAttributeTargets.clear();
		scheduleTranslations();
	};

	const scheduleNodeTranslation = (targetNode) => {
		if (pendingFullRefresh || !targetNode) return;
		pendingNodes.add(targetNode);
		scheduleTranslations();
	};

	const scheduleAttributeTranslation = (targetElement) => {
		if (pendingFullRefresh || !(targetElement instanceof Element)) return;
		pendingAttributeTargets.add(targetElement);
		scheduleTranslations();
	};

	const observer = new MutationObserver((mutations) => {
		if (isApplying) return;

		for (const mutation of mutations) {
			if (mutation.type === 'childList') {
				mutation.addedNodes.forEach((addedNode) => {
					if (addedNode.nodeType === Node.TEXT_NODE) {
						const parentElement = addedNode.parentElement;
						if (!parentElement || shouldSkipElement(parentElement)) return;

						textSourceStore.set(addedNode, addedNode.nodeValue || '');
						scheduleNodeTranslation(addedNode);
						return;
					}

					if (addedNode.nodeType === Node.ELEMENT_NODE) {
						scheduleNodeTranslation(addedNode);
					}
				});
			}

			if (mutation.type === 'characterData') {
				textSourceStore.set(mutation.target, mutation.target.nodeValue || '');
				scheduleNodeTranslation(mutation.target);
			}

			if (mutation.type === 'attributes' && mutation.target instanceof Element) {
				let sourceMap = attributeSourceStore.get(mutation.target);
				if (!sourceMap) {
					sourceMap = new Map();
					attributeSourceStore.set(mutation.target, sourceMap);
				}

				const attributeName = mutation.attributeName;
				if (attributeName) {
					sourceMap.set(attributeName, mutation.target.getAttribute(attributeName) || '');
					scheduleAttributeTranslation(mutation.target);
				}
			}
		}
	});

	const unsubscribe = internalLocale.subscribe(() => {
		scheduleFullRefresh();
	});

	scheduleFullRefresh();

	observer.observe(node, {
		subtree: true,
		childList: true,
		characterData: true,
		attributes: true,
		attributeFilter: ['placeholder', 'title', 'aria-label']
	});

	return {
		destroy() {
			unsubscribe();
			observer.disconnect();
			if (frameHandle !== null) {
				if (typeof window !== 'undefined' && typeof window.cancelAnimationFrame === 'function') {
					window.cancelAnimationFrame(frameHandle);
				} else {
					clearTimeout(frameHandle);
				}
			}
		}
	};
}

if (browser) {
	internalLocale.subscribe((value) => {
		setDocumentLocale(value);
		localStorage.setItem(STORAGE_KEY, value);
		syncAlertLocalization(value);
	});
}

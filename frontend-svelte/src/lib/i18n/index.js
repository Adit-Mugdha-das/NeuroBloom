import { browser } from '$app/environment';
import { get, writable } from 'svelte/store';
import { updateUserPreferences } from '$lib/stores.js';
import {
	DEFAULT_LOCALE,
	SUPPORTED_LOCALES,
	formatNumber as formatTranslatedNumber,
	formatPercent as formatTranslatedPercent,
	localizeDigitInput as localizeTranslatedDigitInput,
	localizeStimulusSequence as localizeTranslatedStimulusSequence,
	localizeStimulusSymbol as localizeTranslatedStimulusSymbol,
	normalizeLocale,
	normalizeLocalizedDigits,
	t as translateAlias,
	toBanglaDigits,
	translateText as translateLocalizedText
} from './translator.js';

const STORAGE_KEY = 'preferred-locale';
const ORIGINAL_ALERT = browser && typeof window !== 'undefined' ? window.alert.bind(window) : null;
export { DEFAULT_LOCALE, SUPPORTED_LOCALES, normalizeLocale, normalizeLocalizedDigits, toBanglaDigits };

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
const activeLocalizationRefreshers = new Set();
let queuedLocalizationFrame = null;
let queuedLocalizationKind = null;

export const locale = {
	subscribe: internalLocale.subscribe
};

export function getLocale() {
	return get(internalLocale);
}

export function requestLocalizationRefresh(kind = 'full') {
	if (!browser) return;

	for (const refresh of activeLocalizationRefreshers) {
		refresh(kind);
	}
}

export function queueLocalizationRefresh(kind = 'full') {
	if (!browser || typeof window === 'undefined') return;

	if (kind === 'pulse') {
		requestLocalizationRefresh('pulse');
		return;
	}

	queuedLocalizationKind = queuedLocalizationKind === 'full' || kind === 'full' ? 'full' : kind;
	if (queuedLocalizationFrame !== null) return;

	const flushRefresh = () => {
		const nextKind = queuedLocalizationKind || 'full';
		queuedLocalizationKind = null;
		queuedLocalizationFrame = null;
		requestLocalizationRefresh(nextKind);
	};

	if (typeof window.requestAnimationFrame === 'function') {
		queuedLocalizationFrame = window.requestAnimationFrame(() => {
			queuedLocalizationFrame = window.requestAnimationFrame(flushRefresh);
		});
		return;
	}

	queuedLocalizationFrame = window.setTimeout(flushRefresh, 0);
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

export function localizeDigitInput(value, targetLocale = getLocale()) {
	return localizeTranslatedDigitInput(value, targetLocale);
}

export function translateText(input, targetLocale = getLocale(), options = {}) {
	return translateLocalizedText(input, targetLocale, options);
}

export function t(input, targetLocale = getLocale(), options = {}) {
	return translateAlias(input, targetLocale, options);
}

export function formatNumber(value, targetLocale = getLocale(), options = {}) {
	return formatTranslatedNumber(value, targetLocale, options);
}

export function formatPercent(value, targetLocale = getLocale(), options = {}) {
	return formatTranslatedPercent(value, targetLocale, options);
}

export function localizeStimulusSymbol(value, targetLocale = getLocale()) {
	return localizeTranslatedStimulusSymbol(value, targetLocale);
}

export function localizeStimulusSequence(values, targetLocale = getLocale()) {
	return localizeTranslatedStimulusSequence(values, targetLocale);
}

function shouldSkipElement(element) {
	if (!element) return true;

	if (element.closest('[data-localize-skip]')) return true;
	if (element.isContentEditable) return true;

	return ['SCRIPT', 'STYLE', 'NOSCRIPT', 'IFRAME', 'TEXTAREA'].includes(element.tagName);
}

function resolveSourceValue(store, key, currentValue, translationOptions = {}) {
	const storedValue = store.get(key);
	if (!storedValue) {
		store.set(key, currentValue);
		return currentValue;
	}

	const englishVersion = translateText(storedValue, 'en');
	const banglaVersion = translateText(storedValue, 'bn', translationOptions);

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

function translateTextNodes(root, activeLocale, sourceStore, translationOptions = {}) {
	const walker = createTreeWalker(root);
	const nodes = [];

	while (walker.nextNode()) {
		nodes.push(walker.currentNode);
	}

	for (const textNode of nodes) {
		const sourceText = resolveSourceValue(
			sourceStore,
			textNode,
			textNode.nodeValue || '',
			translationOptions
		);
		const translatedText = translateText(sourceText, activeLocale, translationOptions);

		if (textNode.nodeValue !== translatedText) {
			textNode.nodeValue = translatedText;
		}
	}
}

function translateTextNode(textNode, activeLocale, sourceStore, translationOptions = {}) {
	if (!textNode?.nodeValue?.trim()) {
		return;
	}

	const parentElement = textNode.parentElement;
	if (!parentElement || shouldSkipElement(parentElement)) {
		return;
	}

	const sourceText = resolveSourceValue(
		sourceStore,
		textNode,
		textNode.nodeValue || '',
		translationOptions
	);
	const translatedText = translateText(sourceText, activeLocale, translationOptions);

	if (textNode.nodeValue !== translatedText) {
		textNode.nodeValue = translatedText;
	}
}

function translateAttributes(root, activeLocale, attributeStore, translationOptions = {}) {
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

			const sourceValue = resolveSourceValue(
				sourceMap,
				attributeName,
				currentValue,
				translationOptions
			);
			const translatedValue = translateText(sourceValue, activeLocale, translationOptions);

			if (currentValue !== translatedValue) {
				element.setAttribute(attributeName, translatedValue);
			}
		}
	}
}

function translateElementAttributes(
	element,
	activeLocale,
	attributeStore,
	translationOptions = {}
) {
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

		const sourceValue = resolveSourceValue(
			sourceMap,
			attributeName,
			currentValue,
			translationOptions
		);
		const translatedValue = translateText(sourceValue, activeLocale, translationOptions);

		if (currentValue !== translatedValue) {
			element.setAttribute(attributeName, translatedValue);
		}
	}
}

function translateSubtree(
	root,
	activeLocale,
	textSourceStore,
	attributeSourceStore,
	translationOptions = {}
) {
	if (!root) {
		return;
	}

	if (root.nodeType === Node.TEXT_NODE) {
		translateTextNode(root, activeLocale, textSourceStore, translationOptions);
		return;
	}

	if (root.nodeType === Node.ELEMENT_NODE || root.nodeType === Node.DOCUMENT_FRAGMENT_NODE) {
		translateTextNodes(root, activeLocale, textSourceStore, translationOptions);
		translateAttributes(root, activeLocale, attributeSourceStore, translationOptions);
	}
}

function normalizeLocalizationMode(options) {
	if (typeof options === 'string') {
		return options;
	}

	if (options && typeof options === 'object' && typeof options.mode === 'string') {
		return options.mode;
	}

	return 'observe';
}

export function localize(node, options = 'observe') {
	if (!browser) {
		return {};
	}

	let localizationMode = normalizeLocalizationMode(options);
	const textSourceStore = new WeakMap();
	const attributeSourceStore = new WeakMap();
	let isApplying = false;
	let pendingFullRefresh = false;
	let frameHandle = null;
	let observer = null;
	let observerMode = 'none';
	let pulseStopTimer = null;
	const pendingNodes = new Set();
	const pendingAttributeTargets = new Set();
	const observerOptions = {
		subtree: true,
		childList: true,
		characterData: true,
		attributes: true,
		attributeFilter: ['placeholder', 'title', 'aria-label']
	};

	const flushTranslations = () => {
		frameHandle = null;
		if (isApplying) return;
		isApplying = true;

		try {
			const activeLocale = getLocale();
			const translationOptions = { aggressive: localizationMode === 'observe' };
			if (pendingFullRefresh) {
				translateTextNodes(node, activeLocale, textSourceStore, translationOptions);
				translateAttributes(node, activeLocale, attributeSourceStore, translationOptions);
			} else {
				for (const pendingNode of pendingNodes) {
					translateSubtree(
						pendingNode,
						activeLocale,
						textSourceStore,
						attributeSourceStore,
						translationOptions
					);
				}

				for (const targetElement of pendingAttributeTargets) {
					translateElementAttributes(
						targetElement,
						activeLocale,
						attributeSourceStore,
						translationOptions
					);
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

	const handleMutations = (mutations) => {
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
	};

	const stopObserving = () => {
		if (pulseStopTimer !== null) {
			clearTimeout(pulseStopTimer);
			pulseStopTimer = null;
		}

		if (observer) {
			observer.disconnect();
			observer = null;
		}

		observerMode = 'none';
	};

	const ensureObserver = (nextObserverMode) => {
		if (!observer) {
			observer = new MutationObserver(handleMutations);
			observer.observe(node, observerOptions);
		}

		observerMode = nextObserverMode;
	};

	const schedulePulseStop = () => {
		if (pulseStopTimer !== null) {
			clearTimeout(pulseStopTimer);
		}

		pulseStopTimer = window.setTimeout(() => {
			if (observerMode === 'pulse' && localizationMode === 'refresh') {
				stopObserving();
			}
		}, 180);
	};

	const startObserving = () => {
		if (localizationMode !== 'observe') {
			return;
		}

		ensureObserver('permanent');
	};

	const startPulseObservation = () => {
		if (localizationMode !== 'refresh') {
			return;
		}

		if (observerMode !== 'permanent') {
			ensureObserver('pulse');
		}

		if (observerMode === 'pulse') {
			schedulePulseStop();
		}
	};

	const unsubscribe = internalLocale.subscribe(() => {
		scheduleFullRefresh();
	});
	const handleExternalRefresh = (kind = 'full') => {
		if (kind === 'pulse') {
			startPulseObservation();
			return;
		}

		scheduleFullRefresh();
	};
	activeLocalizationRefreshers.add(handleExternalRefresh);

	scheduleFullRefresh();
	startObserving();

	return {
		update(nextOptions = localizationMode) {
			const nextMode = normalizeLocalizationMode(nextOptions);
			if (nextMode === localizationMode) {
				return;
			}

			localizationMode = nextMode;
			if (localizationMode === 'observe') {
				startObserving();
			} else {
				stopObserving();
			}

			scheduleFullRefresh();
		},
		destroy() {
			activeLocalizationRefreshers.delete(handleExternalRefresh);
			unsubscribe();
			stopObserving();
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

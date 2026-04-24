import { browser } from '$app/environment';
import { get, writable } from 'svelte/store';
import { updateUserPreferences } from '$lib/stores.js';
import { normalizeLocale } from './locale-utils.js';

export const DEFAULT_LOCALE = 'en';
export const SUPPORTED_LOCALES = [
	{ value: 'en', label: 'English' },
	{ value: 'bn', label: 'বাংলা' }
];

export const DIGIT_MAP = {
	'0': '০',
	'1': '১',
	'2': '২',
	'3': '৩',
	'4': '৪',
	'5': '৫',
	'6': '৬',
	'7': '৭',
	'8': '৮',
	'9': '৯'
};

const STORAGE_KEY = 'preferred-locale';
const REVERSE_DIGIT_MAP = Object.fromEntries(
	Object.entries(DIGIT_MAP).map(([digit, localizedDigit]) => [localizedDigit, digit])
);

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
	const text = variants?.[normalizedLocale] ?? variants?.en ?? variants?.bn ?? '';
	return normalizedLocale === 'bn' ? toBanglaDigits(text) : text;
}

export function toBanglaDigits(value) {
	return String(value).replace(/\d/g, (digit) => DIGIT_MAP[digit] || digit);
}

export function normalizeLocalizedDigits(value) {
	return String(value).replace(/[০-৯]/g, (digit) => REVERSE_DIGIT_MAP[digit] || digit);
}

export function localizeDigitInput(value, targetLocale = getLocale()) {
	const normalizedValue = normalizeLocalizedDigits(value);
	return normalizeLocale(targetLocale) === 'bn' ? toBanglaDigits(normalizedValue) : normalizedValue;
}

export function formatNumber(value, targetLocale = getLocale(), options = {}) {
	if (value === null || value === undefined || value === '') {
		return '';
	}

	const numericValue = typeof value === 'number' ? value : Number(value);

	if (!Number.isFinite(numericValue)) {
		return String(value);
	}

	const localeCode = normalizeLocale(targetLocale) === 'bn' ? 'bn-BD' : 'en-US';
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

export function formatSeconds(value, targetLocale = getLocale(), options = {}) {
	const unit = normalizeLocale(targetLocale) === 'bn' ? 'সে.' : 's';
	return `${formatNumber(value, targetLocale, options)}${unit}`;
}

export function formatMilliseconds(value, targetLocale = getLocale(), options = {}) {
	const unit = normalizeLocale(targetLocale) === 'bn' ? 'মি.সে.' : 'ms';
	return `${formatNumber(value, targetLocale, options)}${unit}`;
}

export function formatSecondsPerItem(value, targetLocale = getLocale(), options = {}) {
	const unit = normalizeLocale(targetLocale) === 'bn' ? 'সে./আইটেম' : 's/item';
	return `${formatNumber(value, targetLocale, options)}${unit}`;
}

export function formatMillisecondsPerItem(value, targetLocale = getLocale(), options = {}) {
	const unit = normalizeLocale(targetLocale) === 'bn' ? 'মি.সে./আইটেম' : 'ms/item';
	return `${formatNumber(value, targetLocale, options)} ${unit}`;
}

export function formatDate(value, targetLocale = getLocale(), options = {}) {
	if (!value) return '';

	const date = value instanceof Date ? value : new Date(value);
	if (Number.isNaN(date.getTime())) {
		return String(value);
	}

	const localeCode = normalizeLocale(targetLocale) === 'bn' ? 'bn-BD' : 'en-US';
	return new Intl.DateTimeFormat(localeCode, options).format(date);
}

export function formatDateTime(value, targetLocale = getLocale(), options = {}) {
	return formatDate(value, targetLocale, {
		dateStyle: 'medium',
		timeStyle: 'short',
		...options
	});
}

export function requestLocalizationRefresh() {}

export function queueLocalizationRefresh() {}

if (browser) {
	internalLocale.subscribe((value) => {
		setDocumentLocale(value);
		localStorage.setItem(STORAGE_KEY, value);
	});
}

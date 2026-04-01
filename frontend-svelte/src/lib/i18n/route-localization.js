export const PUBLIC_LANGUAGE_ROUTE_PATHS = ['/', '/login', '/register'];

// These older interactive tasks mutate their own DOM/state frequently, so they
// still need observer-backed localization until they are migrated to native i18n.
export const OBSERVED_DOM_ROUTE_PATHS = [
	'/training',
	'/training/cancellation-test',
	'/training/flanker',
	'/training/inspection-time',
	'/training/multiple-object-tracking',
	'/training/pattern-comparison',
	'/training/stockings-of-cambridge',
	'/training/tower-of-london',
	'/training/trail-making-b',
	'/training/twenty-questions',
	'/training/useful-field-of-view',
	'/training/visual-search',
	'/baseline/tasks/attention',
	'/baseline/tasks/flexibility'
];

export const NATIVE_LOCALIZED_ROUTE_PATHS = [
	'/dashboard',
	'/messages',
	'/notifications',
	'/find-doctor',
	'/baseline/tasks/planning',
	'/baseline/tasks/processing-speed',
	'/baseline/tasks/visual-scanning',
	'/baseline/tasks/working-memory',
	'/training/category-fluency',
	'/training/dccs',
	'/training/digit-span',
	'/training/dual-n-back',
	'/training/gonogo',
	'/training/letter-number-sequencing',
	'/training/operation-span',
	'/training/pasat',
	'/training/plus-minus',
	'/training/sdmt',
	'/training/spatial-span',
	'/training/stroop',
	'/training/trail-making-a',
	'/training/verbal-fluency',
	'/training/wcst'
];

export const PUBLIC_LANGUAGE_ROUTES = new Set(PUBLIC_LANGUAGE_ROUTE_PATHS);
export const OBSERVED_DOM_ROUTES = new Set(OBSERVED_DOM_ROUTE_PATHS);
export const NATIVE_LOCALIZED_ROUTES = new Set(NATIVE_LOCALIZED_ROUTE_PATHS);

// Backwards compatibility for existing tooling imports.
export const LEGACY_GAME_ROUTES = OBSERVED_DOM_ROUTES;

export function getRouteLocalizationMode(pathname = '') {
	if (NATIVE_LOCALIZED_ROUTES.has(pathname)) {
		return 'native';
	}

	if (OBSERVED_DOM_ROUTES.has(pathname)) {
		return 'observe';
	}

	return 'refresh';
}

export function shouldUseLegacyDomLocalization(pathname = '') {
	return getRouteLocalizationMode(pathname) !== 'native';
}

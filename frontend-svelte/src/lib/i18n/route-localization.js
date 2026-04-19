export const PUBLIC_LANGUAGE_ROUTE_PATHS = ['/', '/login', '/register'];

// These older interactive tasks mutate their own DOM/state frequently, so they
// still need observer-backed localization until they are migrated to native i18n.
export const OBSERVED_DOM_ROUTE_PATHS = [];

export const NATIVE_LOCALIZED_ROUTE_PATHS = [
	'/dashboard',
	'/training',
	'/messages',
	'/notifications',
	'/find-doctor',
	'/baseline/tasks/attention',
	'/baseline/tasks/flexibility',
	'/baseline/tasks/planning',
	'/baseline/tasks/processing-speed',
	'/baseline/tasks/visual-scanning',
	'/baseline/tasks/working-memory',
	'/training/cancellation-test',
	'/training/category-fluency',
	'/training/dccs',
	'/training/digit-span',
	'/training/dual-n-back',
	'/training/flanker',
	'/training/gonogo',
	'/training/inspection-time',
	'/training/letter-number-sequencing',
	'/training/multiple-object-tracking',
	'/training/operation-span',
	'/training/pasat',
	'/training/pattern-comparison',
	'/training/plus-minus',
	'/training/sdmt',
	'/training/spatial-span',
	'/training/stockings-of-cambridge',
	'/training/stroop',
	'/training/tower-of-london',
	'/training/trail-making-a',
	'/training/trail-making-b',
	'/training/twenty-questions',
	'/training/useful-field-of-view',
	'/training/verbal-fluency',
	'/training/visual-search',
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

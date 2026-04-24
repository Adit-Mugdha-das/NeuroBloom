export {
	DEFAULT_LOCALE,
	DIGIT_MAP,
	SUPPORTED_LOCALES,
	formatDate,
	formatDateTime,
	formatMilliseconds,
	formatMillisecondsPerItem,
	formatNumber,
	formatPercent,
	formatSeconds,
	formatSecondsPerItem,
	getLocale,
	initializeLocale,
	locale,
	localeText,
	localizeDigitInput,
	normalizeLocalizedDigits,
	queueLocalizationRefresh,
	requestLocalizationRefresh,
	setLocale,
	toBanglaDigits
} from './runtime.js';
export { normalizeLocale } from './locale-utils.js';
export {
	performanceText,
	ruleOptionText,
	taskPhraseText,
	taskValueText,
	ufovInstructionText,
	ufovSubtestText
} from './task-copy.js';

export {
	localizeStimulusSequence,
	localizeStimulusSymbol,
	t,
	translateText,
	uiText
} from './translator.js';

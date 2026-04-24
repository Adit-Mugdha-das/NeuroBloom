import { normalizeLocale } from './locale-utils.js';

const VALUES = {
	side: {
		left: { en: 'Left', bn: 'বাম' },
		right: { en: 'Right', bn: 'ডান' },
		equal: { en: 'Equal', bn: 'সমান' }
	},
	landmark_response: {
		left: { en: 'Left Longer', bn: 'বাম দিক লম্বা' },
		right: { en: 'Right Longer', bn: 'ডান দিক লম্বা' },
		equal: { en: 'Equal', bn: 'সমান' }
	},
	rule: {
		color: { en: 'Color', bn: 'রং' },
		shape: { en: 'Shape', bn: 'আকার' },
		count: { en: 'Count', bn: 'সংখ্যা' }
	},
	rule_value: {
		teal: { en: 'Teal', bn: 'সবুজাভ নীল' },
		orange: { en: 'Orange', bn: 'কমলা' },
		circle: { en: 'Circle', bn: 'বৃত্ত' },
		triangle: { en: 'Triangle', bn: 'ত্রিভুজ' },
		1: { en: 'One item', bn: 'একটি বস্তু' },
		2: { en: 'Two items', bn: 'দুটি বস্তু' },
		'one item': { en: 'One item', bn: 'একটি বস্তু' },
		'two items': { en: 'Two items', bn: 'দুটি বস্তু' }
	},
	vehicle: {
		car: { en: 'CAR', bn: 'কার' },
		truck: { en: 'TRUCK', bn: 'ট্রাক' }
	},
	shape: {
		circle: { en: 'circle', bn: 'বৃত্ত' },
		square: { en: 'square', bn: 'চতুর্ভুজ' },
		triangle: { en: 'triangle', bn: 'ত্রিভুজ' }
	},
	ufov_subtest: {
		central_only: { en: 'Central Only', bn: 'শুধু কেন্দ্র' },
		central_peripheral: { en: 'Central + Peripheral', bn: 'কেন্দ্র ও চারপাশ' },
		with_distractors: { en: 'With Distractors', bn: 'বিভ্রান্তিকর বস্তুসহ' },
		distractors: { en: 'With Distractors', bn: 'বিভ্রান্তিকর বস্তুসহ' }
	},
	performance: {
		perfect: { en: 'Perfect!', bn: 'দারুণ হয়েছে!' },
		partial: { en: 'Good Try', bn: 'ভালো চেষ্টা' },
		incorrect: { en: 'Keep Practicing', bn: 'অনুশীলন চালিয়ে যান' },
		correct: { en: 'Correct', bn: 'সঠিক' },
		wrong: { en: 'Incorrect', bn: 'ভুল' },
		incorrect_response: { en: 'Incorrect', bn: 'ভুল' }
	}
};

const PHRASES = {
	ufov_central_only_instruction: {
		en: 'Identify the vehicle in the center.',
		bn: 'মাঝখানের গাড়িটি কী ছিল তা বেছে নিন।'
	},
	ufov_full_instruction: {
		en: 'Identify the center vehicle and the location of the outside shape.',
		bn: 'মাঝখানের গাড়ি এবং চারপাশের আকারটি কোথায় ছিল তা বেছে নিন।'
	},
	rule_changed: {
		en: 'The rule has changed. Drop the previous mapping before you continue.',
		bn: 'নিয়ম বদলে গেছে। এগোনোর আগে আগের মিলটি ভুলে নতুন নিয়ম ধরুন।'
	},
	no_adaptation_reason: {
		en: 'Difficulty updated from your latest performance.',
		bn: 'সাম্প্রতিক পারফরম্যান্স অনুযায়ী কঠিনতার মাত্রা হালনাগাদ হয়েছে।'
	}
};

function pick(entry, targetLocale, fallback = '') {
	const locale = normalizeLocale(targetLocale);
	return entry?.[locale] ?? entry?.en ?? entry?.bn ?? fallback;
}

function key(value) {
	return String(value ?? '').trim().toLowerCase();
}

export function taskValueText(group, value, targetLocale = 'en', fallback = '') {
	const normalizedKey = key(value).replaceAll('-', '_');
	const entry = VALUES[group]?.[normalizedKey] ?? VALUES[group]?.[key(value)];
	return pick(entry, targetLocale, fallback || String(value ?? ''));
}

export function taskPhraseText(name, targetLocale = 'en', fallback = '') {
	return pick(PHRASES[name], targetLocale, fallback);
}

export function ruleOptionText(rule, value, targetLocale = 'en') {
	if (rule === 'count') {
		return taskValueText('rule_value', value, targetLocale, String(value ?? ''));
	}

	return taskValueText('rule_value', value, targetLocale, String(value ?? ''));
}

export function ufovInstructionText(trialData, targetLocale = 'en') {
	if (!trialData) return '';
	return trialData.subtest === 'central_only'
		? taskPhraseText('ufov_central_only_instruction', targetLocale)
		: taskPhraseText('ufov_full_instruction', targetLocale);
}

export function ufovSubtestText(subtest, targetLocale = 'en', fallback = '') {
	return taskValueText('ufov_subtest', subtest, targetLocale, fallback);
}

export function performanceText(performance, targetLocale = 'en') {
	return taskValueText('performance', performance, targetLocale, taskValueText('performance', 'incorrect', targetLocale));
}

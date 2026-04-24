import { normalizeLocale } from './locale-utils.js';

const TASK_DIFFICULTY_DESCRIPTIONS = {
	pasat: {
		1: {
			en: 'Beginner - 4 second intervals, plenty of time',
			bn: 'শুরুর স্তর - ৪ সেকেন্ড বিরতি, পর্যাপ্ত সময়'
		},
		2: {
			en: 'Easy - Comfortable pace',
			bn: 'সহজ - আরামদায়ক গতি'
		},
		3: {
			en: 'Moderate - Approaching standard PASAT-3',
			bn: 'মধ্যম - মানক PASAT-৩-এর কাছাকাছি'
		},
		4: {
			en: 'Standard - PASAT-3, clinical norm',
			bn: 'মানক - PASAT-৩, ক্লিনিক্যাল মানদণ্ড'
		},
		5: {
			en: 'Intermediate - Faster than standard',
			bn: 'ইন্টারমিডিয়েট - মানকের চেয়ে দ্রুত'
		},
		6: {
			en: 'Challenging - Quick sustained attention',
			bn: 'চ্যালেঞ্জিং - দ্রুত ও স্থায়ী মনোযোগ'
		},
		7: {
			en: 'Advanced - Approaching PASAT-2',
			bn: 'অ্যাডভান্সড - PASAT-২-এর কাছাকাছি'
		},
		8: {
			en: 'Expert - PASAT-2, high demand',
			bn: 'এক্সপার্ট - PASAT-২, উচ্চ চাহিদা'
		},
		9: {
			en: 'Master - Very rapid pace',
			bn: 'মাস্টার - খুব দ্রুত গতি'
		},
		10: {
			en: 'Elite - Extreme sustained attention challenge',
			bn: 'এলিট - দীর্ঘস্থায়ী মনোযোগের চরম চ্যালেঞ্জ'
		}
	},
	gonogo: {
		1: {
			en: 'Beginner - Very slow pace, clear targets',
			bn: 'শুরুর স্তর - খুব ধীর গতি, স্পষ্ট লক্ষ্য'
		},
		2: {
			en: 'Easy - Slow pace, comfortable',
			bn: 'সহজ - ধীর ও স্বস্তিদায়ক গতি'
		},
		3: {
			en: 'Moderate - Standard clinical pace',
			bn: 'মধ্যম - মানক ক্লিনিক্যাল গতি'
		},
		4: {
			en: 'Intermediate - Faster responses',
			bn: 'ইন্টারমিডিয়েট - আরও দ্রুত প্রতিক্রিয়া'
		},
		5: {
			en: 'Challenging - Similar stimuli, quicker pace',
			bn: 'চ্যালেঞ্জিং - কাছাকাছি ধরনের উদ্দীপক, দ্রুততর গতি'
		},
		6: {
			en: 'Advanced - Rapid discrimination required',
			bn: 'অ্যাডভান্সড - দ্রুত পার্থক্য করা প্রয়োজন'
		},
		7: {
			en: 'Expert - Shape discrimination, fast pace',
			bn: 'এক্সপার্ট - আকার আলাদা করার দ্রুত চ্যালেঞ্জ'
		},
		8: {
			en: 'Master - Very fast responses, high inhibition demand',
			bn: 'মাস্টার - খুব দ্রুত প্রতিক্রিয়া, উচ্চ নিয়ন্ত্রণ চাহিদা'
		},
		9: {
			en: 'Elite - Word processing, maximum speed',
			bn: 'এলিট - শব্দভিত্তিক উদ্দীপক, সর্বোচ্চ গতি'
		},
		10: {
			en: 'Ultimate - Peak challenge, near-research standards',
			bn: 'আল্টিমেট - সর্বোচ্চ চ্যালেঞ্জ, গবেষণার মানের কাছাকাছি'
		}
	}
};

const GONOGO_STIMULUS_DISPLAY = {
	basic: {
		en: { go: 'X', nogo: 'O' },
		bn: { go: 'ক', nogo: 'ম' }
	},
	similar: {
		en: { go: 'P', nogo: 'R' },
		bn: { go: 'ত', nogo: 'থ' }
	},
	shapes: {
		en: { go: '■', nogo: '●' },
		bn: { go: '■', nogo: '●' }
	},
	complex: {
		en: { go: 'GO', nogo: 'NO' },
		bn: { go: 'চাপ', nogo: 'থাম' }
	}
};

export function getTaskDifficultyDescription(
	taskKey,
	difficulty,
	targetLocale = 'en',
	fallback = ''
) {
	const normalizedTaskKey = String(taskKey || '').toLowerCase();
	const normalizedDifficulty = Number(difficulty);
	const locale = normalizeLocale(targetLocale);
	const entry = TASK_DIFFICULTY_DESCRIPTIONS[normalizedTaskKey]?.[normalizedDifficulty];

	if (!entry) {
		return fallback;
	}

	return entry[locale] || entry.en || fallback;
}

export function getGoNoGoStimulusPair(
	stimulusSet,
	targetLocale = 'en',
	fallback = {}
) {
	const locale = normalizeLocale(targetLocale);
	const entry = GONOGO_STIMULUS_DISPLAY[String(stimulusSet || '').toLowerCase()];
	const localizedEntry = entry?.[locale] || entry?.en;

	return {
		go: localizedEntry?.go || fallback.go || '',
		nogo: localizedEntry?.nogo || fallback.nogo || ''
	};
}

export function getGoNoGoStimulus(
	stimulusSet,
	trialType,
	targetLocale = 'en',
	fallback = ''
) {
	const pair = getGoNoGoStimulusPair(stimulusSet, targetLocale, {
		go: fallback,
		nogo: fallback
	});

	return trialType === 'nogo' ? pair.nogo : pair.go;
}

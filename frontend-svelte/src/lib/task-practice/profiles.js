export const TASK_PLAY_MODE = Object.freeze({
	PRACTICE: 'practice',
	RECORDED: 'recorded'
});

export const TRAINING_TASK_CODES = [
	'wcst',
	'visual-search',
	'pasat',
	'verbal-fluency',
	'operation-span',
	'useful-field-of-view',
	'multiple-object-tracking',
	'twenty-questions',
	'spatial-span',
	'letter-number-sequencing',
	'trail-making-b',
	'landmark-task',
	'trail-making-a',
	'inspection-time',
	'tower-of-london',
	'gonogo',
	'stroop',
	'stockings-of-cambridge',
	'flanker',
	'choice-reaction-time',
	'dual-n-back',
	'category-fluency',
	'cancellation-test',
	'digit-span',
	'plus-minus',
	'dccs',
	'pattern-comparison',
	'rule-shift',
	'sdmt',
	'sart'
];

export const BASELINE_TASK_CODES = [
	'attention',
	'flexibility',
	'planning',
	'processing-speed',
	'visual-scanning',
	'working-memory'
];

export const PATIENT_TASK_CODES = [...TRAINING_TASK_CODES, ...BASELINE_TASK_CODES];

const DEFAULT_PROFILE = Object.freeze({
	strategy: 'local',
	trialLimit: 4,
	timeLimitSeconds: 20
});

const PROFILES = {
	'dual-n-back': {
		strategy: 'requery',
		trialLimit: 2,
		query: { difficulty: 1, num_trials: 2 }
	},
	'digit-span': {
		strategy: 'requery',
		trialLimit: 3,
		query: { difficulty: 1, num_trials: 3 }
	},
	'spatial-span': {
		strategy: 'requery',
		trialLimit: 3,
		query: { difficulty: 1, num_trials: 3 }
	},
	'operation-span': {
		strategy: 'requery',
		trialLimit: 2,
		query: { difficulty: 1, num_trials: 2 }
	},
	'letter-number-sequencing': {
		strategy: 'requery',
		trialLimit: 3,
		query: { difficulty: 1, num_trials: 3 }
	},
	'choice-reaction-time': {
		strategy: 'requery',
		trialLimit: 4,
		query: { difficulty: 1 }
	},
	'trail-making-a': {
		strategy: 'requery',
		trialLimit: 8,
		query: { difficulty: 1 }
	},
	'pattern-comparison': {
		strategy: 'requery',
		trialLimit: 8,
		query: { difficulty: 1 }
	},
	'sdmt': {
		strategy: 'requery',
		trialLimit: 8,
		query: { difficulty: 1 }
	},
	'sart': {
		strategy: 'requery',
		trialLimit: 12,
		query: { difficulty: 1 }
	},
	'rule-shift': {
		strategy: 'requery',
		trialLimit: 6,
		query: { difficulty: 1 }
	},
	'landmark-task': {
		strategy: 'requery',
		trialLimit: 6,
		query: { difficulty: 1 }
	},
	'pasat': {
		strategy: 'existing',
		trialLimit: 4
	},
	'wcst': {
		strategy: 'existing',
		trialLimit: 12
	},
	'stroop': {
		strategy: 'existing',
		trialLimit: 6
	},
	'gonogo': {
		strategy: 'existing',
		trialLimit: 6
	},
	'flanker': {
		strategy: 'existing',
		trialLimit: 8
	},
	'inspection-time': {
		strategy: 'existing',
		trialLimit: 6
	},
	'trail-making-b': {
		strategy: 'existing',
		trialLimit: 6
	},
	'visual-search': {
		strategy: 'local',
		timeLimitSeconds: 12
	},
	'category-fluency': {
		strategy: 'local',
		timeLimitSeconds: 20
	},
	'verbal-fluency': {
		strategy: 'local',
		timeLimitSeconds: 15
	},
	'cancellation-test': {
		strategy: 'local',
		timeLimitSeconds: 15
	},
	'useful-field-of-view': {
		strategy: 'local',
		trialLimit: 4
	},
	'multiple-object-tracking': {
		strategy: 'local',
		trialLimit: 3
	},
	'twenty-questions': {
		strategy: 'local',
		trialLimit: 1
	},
	'tower-of-london': {
		strategy: 'local',
		trialLimit: 2
	},
	'stockings-of-cambridge': {
		strategy: 'local',
		trialLimit: 2
	},
	'plus-minus': {
		strategy: 'local',
		trialLimit: 2
	},
	'dccs': {
		strategy: 'local',
		trialLimit: 2
	},
	'attention': {
		strategy: 'local',
		trialLimit: 12,
		timeLimitSeconds: 14
	},
	'flexibility': {
		strategy: 'local',
		trialLimit: 8
	},
	'planning': {
		strategy: 'local',
		trialLimit: 3
	},
	'processing-speed': {
		strategy: 'local',
		trialLimit: 6
	},
	'visual-scanning': {
		strategy: 'local',
		trialLimit: 10
	},
	'working-memory': {
		strategy: 'local',
		trialLimit: 6,
		timeLimitSeconds: 18
	}
};

const PRACTICE_COPY = {
	en: {
		trigger: 'Try Practice',
		helper: 'Practice only. Not recorded.',
		bannerTitle: 'Practice Round',
		bannerText: 'This practice run will not affect your recorded performance.',
		exit: 'Exit practice',
		exitAriaLabel: 'Exit practice and return to task setup',
		complete: 'Practice complete. Start when ready.'
	},
	bn: {
		trigger: 'অনুশীলন করুন',
		helper: 'শুধু অনুশীলন। এটি রেকর্ড হবে না।',
		bannerTitle: 'অনুশীলনী রাউন্ড',
		bannerText: 'এই অনুশীলনের ফল রেকর্ড হবে না।',
		exit: 'অনুশীলন থেকে বের হন',
		exitAriaLabel: 'অনুশীলন থেকে বের হয়ে টাস্ক সেটআপে ফিরুন',
		complete: 'অনুশীলন শেষ। প্রস্তুত হলে শুরু করুন।'
	}
};

export function getTaskPracticeProfile(taskCode) {
	return {
		...DEFAULT_PROFILE,
		...(PROFILES[taskCode] || {})
	};
}

export function getPracticeCopy(locale = 'en') {
	return PRACTICE_COPY[locale === 'bn' ? 'bn' : 'en'];
}

function cloneValue(value) {
	if (typeof structuredClone === 'function') {
		return structuredClone(value);
	}

	return JSON.parse(JSON.stringify(value));
}

function applyTrialLimit(target, limit) {
	if (!limit) return;

	const collectionKeys = [
		'trials',
		'trial_cards',
		'items',
		'letters',
		'targets',
		'phases',
		'sequence',
		'test_sequence',
		'circles',
		'distractors',
		'problems',
		'objects',
		'questions',
		'choices'
	];
	for (const key of collectionKeys) {
		if (Array.isArray(target?.[key])) {
			target[key] = target[key].slice(0, limit);
		}
	}

	const counterKeys = [
		'total_trials',
		'num_trials',
		'trial_count',
		'set_size',
		'total_items',
		'total_problems',
		'circle_count'
	];
	for (const key of counterKeys) {
		if (typeof target?.[key] === 'number') {
			target[key] = Math.min(target[key], limit);
		}
	}
}

function applyTimeLimit(target, seconds) {
	if (!seconds) return;

	const secondKeys = ['time_limit', 'time_limit_seconds', 'duration_seconds', 'time_per_letter_seconds'];
	for (const key of secondKeys) {
		if (typeof target?.[key] === 'number') {
			target[key] = Math.min(target[key], seconds);
		}
	}

	if (target?.config && typeof target.config === 'object') {
		applyTimeLimit(target.config, seconds);
	}
}

function applyPracticeProfile(target, profile) {
	if (!target || typeof target !== 'object') return;

	applyTrialLimit(target, profile.trialLimit);
	applyTimeLimit(target, profile.timeLimitSeconds);

	for (const value of Object.values(target)) {
		if (Array.isArray(value)) {
			for (const item of value) {
				applyPracticeProfile(item, profile);
			}
			continue;
		}

		if (value && typeof value === 'object') {
			applyPracticeProfile(value, profile);
		}
	}
}

export function buildPracticePayload(taskCode, payload) {
	if (!payload) return payload;

	const profile = getTaskPracticeProfile(taskCode);
	const clone = cloneValue(payload);

	applyPracticeProfile(clone, profile);

	return clone;
}

function assertPracticeCoverage() {
	const missing = PATIENT_TASK_CODES.filter((taskCode) => !PROFILES[taskCode]);
	if (missing.length > 0) {
		throw new Error(`Missing practice profiles for: ${missing.join(', ')}`);
	}
}

assertPracticeCoverage();

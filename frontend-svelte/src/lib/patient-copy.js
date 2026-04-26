import { localeText } from '$lib/i18n';
import { normalizeTaskKey } from '$lib/task-registry';

const DOMAIN_COPY = Object.freeze({
	working_memory: { en: 'Working Memory', bn: 'ওয়ার্কিং মেমোরি' },
	attention: { en: 'Attention', bn: 'মনোযোগ' },
	flexibility: { en: 'Cognitive Flexibility', bn: 'মানসিক নমনীয়তা' },
	planning: { en: 'Planning', bn: 'পরিকল্পনা' },
	executive_planning: { en: 'Executive Planning', bn: 'নির্বাহী পরিকল্পনা' },
	processing_speed: { en: 'Processing Speed', bn: 'প্রসেসিং স্পিড' },
	visual_scanning: { en: 'Visual Scanning', bn: 'ভিজ্যুয়াল স্ক্যানিং' }
});

const DOMAIN_ALIASES = Object.freeze({
	'working memory': 'working_memory',
	working_memory: 'working_memory',
	attention: 'attention',
	flexibility: 'flexibility',
	'cognitive flexibility': 'flexibility',
	cognitive_flexibility: 'flexibility',
	planning: 'planning',
	'executive planning': 'executive_planning',
	executive_planning: 'executive_planning',
	'processing speed': 'processing_speed',
	processing_speed: 'processing_speed',
	'visual scanning': 'visual_scanning',
	visual_scanning: 'visual_scanning'
});

const TASK_COPY = Object.freeze({
	n_back: {
		en: 'Dual N-Back',
		bn: 'ডুয়াল এন-ব্যাক',
		description: {
			en: 'Track sound and position patterns together.',
			bn: 'শব্দ ও অবস্থানের ধারা একসঙ্গে ধরে রাখুন।'
		}
	},
	digit_span: {
		en: 'Digit Span',
		bn: 'ডিজিট স্প্যান',
		description: {
			en: 'Recall number sequences in order.',
			bn: 'সংখ্যার ধারাগুলো মনে রেখে বলুন।'
		}
	},
	spatial_span: {
		en: 'Spatial Span',
		bn: 'স্পেশাল স্প্যান',
		description: {
			en: 'Remember visual positions in sequence.',
			bn: 'দৃশ্যমান অবস্থানগুলোর ক্রম মনে রাখুন।'
		}
	},
	letter_number_sequencing: {
		en: 'Letter-Number Sequencing',
		bn: 'লেটার-নাম্বার সিকোয়েন্সিং',
		description: {
			en: 'Reorder letters and numbers correctly.',
			bn: 'অক্ষর ও সংখ্যা সঠিক ক্রমে সাজান।'
		}
	},
	operation_span: {
		en: 'Operation Span',
		bn: 'অপারেশন স্প্যান',
		description: {
			en: 'Solve and remember at the same time.',
			bn: 'একই সঙ্গে সমাধান করুন ও মনে রাখুন।'
		}
	},
	simple_reaction: {
		en: 'Choice Reaction Time',
		bn: 'চয়েস রিঅ্যাকশন টাইম',
		description: {
			en: 'Respond quickly to the correct cue.',
			bn: 'সঠিক সংকেতে দ্রুত সাড়া দিন।'
		}
	},
	choice_reaction_time: {
		en: 'Choice Reaction Time',
		bn: 'চয়েস রিঅ্যাকশন টাইম',
		description: {
			en: 'Respond quickly to the correct cue.',
			bn: 'সঠিক সংকেতে দ্রুত সাড়া দিন।'
		}
	},
	sdmt: {
		en: 'Symbol Digit Matching',
		bn: 'সিম্বল-ডিজিট মিলানো',
		description: {
			en: 'Match symbols to digits as fast as you can.',
			bn: 'যত দ্রুত সম্ভব চিহ্নের সঙ্গে সংখ্যা মিলান।'
		}
	},
	trail_making_a: {
		en: 'Trail Making A',
		bn: 'ট্রেইল মেকিং এ',
		description: {
			en: 'Connect items in simple order.',
			bn: 'সহজ ক্রমে আইটেমগুলো যুক্ত করুন।'
		}
	},
	pattern_comparison: {
		en: 'Pattern Comparison',
		bn: 'প্যাটার্ন তুলনা',
		description: {
			en: 'Compare visual patterns quickly.',
			bn: 'দৃশ্যমান প্যাটার্ন দ্রুত তুলনা করুন।'
		}
	},
	inspection_time: {
		en: 'Inspection Time',
		bn: 'ইনস্পেকশন টাইম',
		description: {
			en: 'Spot brief visual differences accurately.',
			bn: 'স্বল্পসময়ের দৃশ্যগত পার্থক্য ঠিকভাবে ধরুন।'
		}
	},
	cpt: {
		en: 'Continuous Performance Task',
		bn: 'কন্টিনিউয়াস পারফরম্যান্স টাস্ক',
		description: {
			en: 'Sustain attention across repeated cues.',
			bn: 'বারবার আসা সংকেতে মনোযোগ ধরে রাখুন।'
		}
	},
	go_nogo: {
		en: 'Go/No-Go',
		bn: 'গো/নো-গো',
		description: {
			en: 'Respond only when the right cue appears.',
			bn: 'সঠিক সংকেত এলে তবেই সাড়া দিন।'
		}
	},
	pasat: {
		en: 'PASAT',
		bn: 'প্যাসাট',
		description: {
			en: 'Add each new number to the previous one.',
			bn: 'নতুন সংখ্যাকে আগের সংখ্যার সঙ্গে যোগ করুন।'
		}
	},
	stroop: {
		en: 'Stroop',
		bn: 'স্ট্রুপ',
		description: {
			en: 'Name colors while ignoring conflicting words.',
			bn: 'বিভ্রান্তিকর শব্দ উপেক্ষা করে রং শনাক্ত করুন।'
		}
	},
	flanker: {
		en: 'Flanker',
		bn: 'ফ্ল্যাঙ্কার',
		description: {
			en: 'Focus on the center cue despite distractions.',
			bn: 'চারপাশের বিভ্রান্তি উপেক্ষা করে মাঝের সংকেতে মন দিন।'
		}
	},
	trail_making_b: {
		en: 'Trail Making B',
		bn: 'ট্রেইল মেকিং বি',
		description: {
			en: 'Switch between sequences flexibly.',
			bn: 'দুই ধরনের ক্রমের মধ্যে নমনীয়ভাবে বদলান।'
		}
	},
	wcst: {
		en: 'WCST',
		bn: 'ডব্লিউসিএসটি',
		description: {
			en: 'Adapt when the sorting rule changes.',
			bn: 'বাছাইয়ের নিয়ম বদলালে নিজেকে মানিয়ে নিন।'
		}
	},
	dccs: {
		en: 'DCCS',
		bn: 'ডিসিসিএস',
		description: {
			en: 'Switch between sorting rules cleanly.',
			bn: 'বিভিন্ন বাছাই নিয়মের মধ্যে সহজে বদলান।'
		}
	},
	rule_shift: {
		en: 'Rule Shift',
		bn: 'রুল শিফট',
		description: {
			en: 'Adjust to a new rule without losing pace.',
			bn: 'গতি না হারিয়ে নতুন নিয়মে বদলান।'
		}
	},
	plus_minus: {
		en: 'Plus-Minus',
		bn: 'প্লাস-মাইনাস',
		description: {
			en: 'Alternate between two mental operations.',
			bn: 'দুটি মানসিক কাজের মধ্যে পালা বদলান।'
		}
	},
	tower_of_london: {
		en: 'Tower of London',
		bn: 'টাওয়ার অব লন্ডন',
		description: {
			en: 'Plan moves before acting.',
			bn: 'চাল দেওয়ার আগে পরিকল্পনা করুন।'
		}
	},
	stockings_of_cambridge: {
		en: 'Stockings of Cambridge',
		bn: 'স্টকিংস অব কেমব্রিজ',
		description: {
			en: 'Find an efficient move sequence.',
			bn: 'সবচেয়ে কার্যকর চালের ক্রম খুঁজে বের করুন।'
		}
	},
	verbal_fluency: {
		en: 'Verbal Fluency',
		bn: 'ভার্বাল ফ্লুয়েন্সি',
		description: {
			en: 'Generate words within a prompt.',
			bn: 'নির্দিষ্ট নির্দেশনা মেনে শব্দ বের করুন।'
		}
	},
	category_fluency: {
		en: 'Category Fluency',
		bn: 'ক্যাটাগরি ফ্লুয়েন্সি',
		description: {
			en: 'List words from one category quickly.',
			bn: 'একটি শ্রেণির শব্দ দ্রুত বলুন।'
		}
	},
	twenty_questions: {
		en: 'Twenty Questions',
		bn: 'টুয়েন্টি কোয়েশ্চনস',
		description: {
			en: 'Narrow down the answer strategically.',
			bn: 'কৌশল করে উত্তর সীমিত করুন।'
		}
	},
	target_search: {
		en: 'Visual Search',
		bn: 'ভিজ্যুয়াল সার্চ',
		description: {
			en: 'Find the target among distractions.',
			bn: 'বিভ্রান্তির মধ্যে লক্ষ্যবস্তু খুঁজে বের করুন।'
		}
	},
	visual_search: {
		en: 'Visual Search',
		bn: 'ভিজ্যুয়াল সার্চ',
		description: {
			en: 'Find the target among distractions.',
			bn: 'বিভ্রান্তির মধ্যে লক্ষ্যবস্তু খুঁজে বের করুন।'
		}
	},
	landmark_task: {
		en: 'Landmark Task',
		bn: 'ল্যান্ডমার্ক টাস্ক',
		description: {
			en: 'Judge visual balance precisely.',
			bn: 'দৃশ্যগত ভারসাম্য নির্ভুলভাবে বিচার করুন।'
		}
	},
	cancellation_test: {
		en: 'Cancellation Test',
		bn: 'ক্যানসেলেশন টেস্ট',
		description: {
			en: 'Scan and cancel the right targets.',
			bn: 'সঠিক লক্ষ্যবস্তু খুঁজে চিহ্নিত করুন।'
		}
	},
	feature_conjunction: {
		en: 'Feature Conjunction',
		bn: 'ফিচার কনজাংশন',
		description: {
			en: 'Combine visual features to find the target.',
			bn: 'দৃশ্যগত বৈশিষ্ট্য মিলিয়ে লক্ষ্যবস্তু খুঁজুন।'
		}
	},
	multiple_object_tracking: {
		en: 'Multiple Object Tracking',
		bn: 'মাল্টিপল অবজেক্ট ট্র্যাকিং',
		description: {
			en: 'Track several moving targets at once.',
			bn: 'একসঙ্গে একাধিক চলমান লক্ষ্য অনুসরণ করুন।'
		}
	},
	useful_field_of_view: {
		en: 'Useful Field of View',
		bn: 'ইউজফুল ফিল্ড অব ভিউ',
		description: {
			en: 'Respond to central and peripheral cues together.',
			bn: 'মাঝের ও পাশের সংকেতে একসঙ্গে সাড়া দিন।'
		}
	},
	sart: {
		en: 'Sustained Attention Response Task',
		bn: 'সাস্টেইন্ড অ্যাটেনশন রেসপন্স টাস্ক',
		description: {
			en: 'Maintain attention over a long sequence.',
			bn: 'দীর্ঘ ধারাবাহিকতায় মনোযোগ ধরে রাখুন।'
		}
	}
});

const FOCUS_REASON_COPY = Object.freeze({
	weakest_area: {
		en: 'Needs the most support right now.',
		bn: 'এই অংশে এখন সবচেয়ে বেশি সহায়তা দরকার।'
	},
	growth_area: {
		en: 'A steady growth area for this phase.',
		bn: 'এই পর্যায়ে ধীরে ধীরে উন্নতির জন্য গুরুত্বপূর্ণ অংশ।'
	},
	maintenance_area: {
		en: 'Keep this area stable while the plan adapts.',
		bn: 'পরিকল্পনা বদলালেও এই অংশ স্থির রাখা দরকার।'
	}
});

const PRIORITY_COPY = Object.freeze({
	primary: { en: 'Primary Focus', bn: 'প্রধান ফোকাস' },
	secondary: { en: 'Secondary Focus', bn: 'দ্বিতীয় ফোকাস' },
	maintenance: { en: 'Maintenance', bn: 'রক্ষণাবেক্ষণ' }
});

const BADGE_COPY = Object.freeze({
	first_session: { en: 'First Steps', bn: 'প্রথম পদক্ষেপ', description: { en: 'Complete your first training session.', bn: 'আপনার প্রথম ট্রেনিং সেশন সম্পন্ন করুন।' } },
	sessions_5: { en: 'Dedicated Learner', bn: 'নিয়মিত শিক্ষার্থী', description: { en: 'Complete 5 training sessions.', bn: '৫টি ট্রেনিং সেশন সম্পন্ন করুন।' } },
	sessions_10: { en: 'Consistent Trainer', bn: 'ধারাবাহিক অনুশীলনকারী', description: { en: 'Complete 10 training sessions.', bn: '১০টি ট্রেনিং সেশন সম্পন্ন করুন।' } },
	sessions_25: { en: 'Brain Athlete', bn: 'মস্তিষ্কের ক্রীড়াবিদ', description: { en: 'Complete 25 training sessions.', bn: '২৫টি ট্রেনিং সেশন সম্পন্ন করুন।' } },
	sessions_50: { en: 'Mental Warrior', bn: 'মানসিক যোদ্ধা', description: { en: 'Complete 50 training sessions.', bn: '৫০টি ট্রেনিং সেশন সম্পন্ন করুন।' } },
	sessions_100: { en: 'Master Trainer', bn: 'মাস্টার ট্রেইনার', description: { en: 'Complete 100 training sessions.', bn: '১০০টি ট্রেনিং সেশন সম্পন্ন করুন।' } },
	streak_3: { en: 'Hot Start', bn: 'দারুণ শুরু', description: { en: 'Maintain a 3-day training streak.', bn: 'টানা ৩ দিনের ট্রেনিং ধারাবাহিকতা ধরে রাখুন।' } },
	streak_7: { en: 'Week Warrior', bn: 'সপ্তাহের যোদ্ধা', description: { en: 'Maintain a 7-day training streak.', bn: 'টানা ৭ দিনের ট্রেনিং ধারাবাহিকতা ধরে রাখুন।' } },
	streak_14: { en: 'Fortnight Champion', bn: 'দুই সপ্তাহের চ্যাম্পিয়ন', description: { en: 'Maintain a 14-day training streak.', bn: 'টানা ১৪ দিনের ট্রেনিং ধারাবাহিকতা ধরে রাখুন।' } },
	streak_30: { en: 'Monthly Master', bn: 'মাসিক মাস্টার', description: { en: 'Maintain a 30-day training streak.', bn: 'টানা ৩০ দিনের ট্রেনিং ধারাবাহিকতা ধরে রাখুন।' } },
	streak_100: { en: 'Unstoppable', bn: 'অপ্রতিরোধ্য', description: { en: 'Maintain a 100-day training streak.', bn: 'টানা ১০০ দিনের ট্রেনিং ধারাবাহিকতা ধরে রাখুন।' } },
	perfect_score: { en: 'Perfectionist', bn: 'নিখুঁত পারফর্মার', description: { en: 'Achieve a perfect score in any task.', bn: 'যেকোনো টাস্কে পূর্ণ নম্বর অর্জন করুন।' } },
	high_accuracy: { en: 'Sharpshooter', bn: 'নির্ভুল শুটার', description: { en: 'Achieve 95% accuracy in a session.', bn: 'একটি সেশনে ৯৫% নির্ভুলতা অর্জন করুন।' } },
	difficulty_5: { en: 'Rising Star', bn: 'উদীয়মান তারকা', description: { en: 'Reach difficulty level 5 in any domain.', bn: 'যেকোনো ডোমেইনে ৫ নম্বর কষ্টস্তরে পৌঁছান।' } },
	difficulty_7: { en: 'Advanced Learner', bn: 'উন্নত শিক্ষার্থী', description: { en: 'Reach difficulty level 7 in any domain.', bn: 'যেকোনো ডোমেইনে ৭ নম্বর কষ্টস্তরে পৌঁছান।' } },
	difficulty_10: { en: 'Elite Mind', bn: 'এলিট মাইন্ড', description: { en: 'Reach the maximum difficulty in any domain.', bn: 'যেকোনো ডোমেইনে সর্বোচ্চ কষ্টস্তরে পৌঁছান।' } },
	all_domains: { en: 'Well Rounded', bn: 'সর্বাঙ্গীণ অগ্রগতি', description: { en: 'Complete at least one task in all six domains.', bn: 'ছয়টি ডোমেইনের প্রত্যেকটিতে অন্তত একটি করে টাস্ক সম্পন্ন করুন।' } },
	domain_expert: { en: 'Domain Expert', bn: 'ডোমেইন বিশেষজ্ঞ', description: { en: 'Complete 20 tasks in a single domain.', bn: 'একটি ডোমেইনে ২০টি টাস্ক সম্পন্ন করুন।' } },
	fast_completion: { en: 'Speed Demon', bn: 'দ্রুতগতির অর্জনকারী', description: { en: 'Complete a session in under 10 minutes.', bn: '১০ মিনিটের মধ্যে একটি সেশন সম্পন্ন করুন।' } },
	big_improvement: { en: 'Growth Mindset', bn: 'উন্নতির মানসিকতা', description: { en: 'Improve your score by 20 points in any domain.', bn: 'যেকোনো ডোমেইনে স্কোর ২০ পয়েন্ট বাড়ান।' } }
});

const BADGE_CATEGORY_COPY = Object.freeze({
	getting_started: { en: 'Getting Started', bn: 'শুরু' },
	milestone: { en: 'Milestones', bn: 'মাইলস্টোন' },
	streak: { en: 'Streaks', bn: 'ধারাবাহিকতা' },
	performance: { en: 'Performance', bn: 'পারফরম্যান্স' },
	mastery: { en: 'Mastery', bn: 'দক্ষতা' },
	speed: { en: 'Speed', bn: 'গতি' },
	improvement: { en: 'Improvement', bn: 'উন্নতি' }
});

const SHELL_COPY = Object.freeze({
	dashboard_title: { en: 'My Dashboard', bn: 'আমার ড্যাশবোর্ড' },
	dashboard_description: {
		en: 'Your next step, today’s practice, and recovery progress in one place.',
		bn: 'আজকের পরবর্তী ধাপ, অনুশীলন, আর অগ্রগতি এক জায়গায় দেখুন।'
	},
	training_title: { en: 'Your Training Plan', bn: 'আপনার ট্রেনিং পরিকল্পনা' },
	training_description: {
		en: "A calm view of today's session, focus areas, and next tasks.",
		bn: 'আজকের সেশন, ফোকাস এলাকা, আর পরবর্তী কাজ শান্তভাবে দেখুন।'
	},
	badge_unlocked: { en: 'New Badge Unlocked!', bn: 'নতুন ব্যাজ আনলক হয়েছে!' },
	no_badge_yet: { en: 'No badge yet', bn: 'এখনো কোনো ব্যাজ নেই' }
});

function pick(locale, variants) {
	return localeText(variants, locale);
}

export function normalizeDomainKey(domain = '') {
	const normalized = String(domain || '').trim().toLowerCase().replace(/-/g, '_');
	return DOMAIN_ALIASES[normalized] || normalized;
}

export function getPatientDomainLabel(domain, locale) {
	const key = normalizeDomainKey(domain);
	return pick(locale, DOMAIN_COPY[key] || { en: 'Training', bn: 'ট্রেনিং' });
}

export function getPatientTaskCopy(taskKey, locale, fallbackDomain = '') {
	const normalized = normalizeTaskKey(taskKey);
	const copy = TASK_COPY[normalized];
	if (copy) {
		return {
			label: pick(locale, copy),
			description: copy.description ? pick(locale, copy.description) : ''
		};
	}

	return {
		label: getPatientDomainLabel(fallbackDomain, locale),
		description: ''
	};
}

export function getPatientTaskLabel(taskKey, locale, fallbackDomain = '') {
	return getPatientTaskCopy(taskKey, locale, fallbackDomain).label;
}

export function getPatientTaskDescription(taskKey, locale, fallbackDomain = '') {
	return getPatientTaskCopy(taskKey, locale, fallbackDomain).description;
}

export function getPatientFocusReason(reasonKey, locale) {
	return pick(locale, FOCUS_REASON_COPY[reasonKey] || {
		en: 'Included in your next recommended session.',
		bn: 'আপনার পরবর্তী প্রস্তাবিত সেশনে এটি রাখা হয়েছে।'
	});
}

export function getPatientPriorityLabel(priority, locale) {
	return pick(locale, PRIORITY_COPY[priority] || PRIORITY_COPY.maintenance);
}

export function getPatientDifficultyLabel(difficulty, locale) {
	if (!difficulty || difficulty <= 3) return pick(locale, { en: 'Gentle', bn: 'সহজ' });
	if (difficulty <= 6) return pick(locale, { en: 'Steady', bn: 'স্থিতিশীল' });
	if (difficulty <= 8) return pick(locale, { en: 'Focused', bn: 'মনোযোগী' });
	return pick(locale, { en: 'Advanced', bn: 'উন্নত' });
}

export function getPatientBadgeCopy(badgeId, locale) {
	const copy = BADGE_COPY[String(badgeId || '').trim()];
	return {
		name: pick(locale, copy || { en: 'Badge', bn: 'ব্যাজ' }),
		description: pick(locale, copy?.description || {
			en: 'Keep practicing to unlock this badge.',
			bn: 'এই ব্যাজ পেতে অনুশীলন চালিয়ে যান।'
		})
	};
}

export function getPatientBadgeCategoryLabel(category, locale) {
	return pick(locale, BADGE_CATEGORY_COPY[category] || { en: 'Badges', bn: 'ব্যাজ' });
}

export function getPatientCopy(key, locale) {
	return pick(locale, SHELL_COPY[key] || { en: '', bn: '' });
}

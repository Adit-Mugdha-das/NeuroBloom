import { API_BASE_URL } from '$lib/api.js';
import {
	getPatientBadgeCopy,
	getPatientCopy,
	getPatientFocusReason,
	getPatientTaskLabel
} from '$lib/patient-copy.js';

const baselineModules = [
	{
		key: 'working_memory',
		title: { en: 'Working Memory', bn: 'ওয়ার্কিং মেমরি' },
		route: '/baseline/tasks/working-memory'
	},
	{
		key: 'attention',
		title: { en: 'Attention', bn: 'মনোযোগ' },
		route: '/baseline/tasks/attention'
	},
	{
		key: 'flexibility',
		title: { en: 'Cognitive Flexibility', bn: 'মানসিক নমনীয়তা' },
		route: '/baseline/tasks/flexibility'
	},
	{
		key: 'planning',
		title: { en: 'Planning', bn: 'পরিকল্পনা' },
		route: '/baseline/tasks/planning'
	},
	{
		key: 'processing_speed',
		title: { en: 'Processing Speed', bn: 'প্রসেসিং স্পিড' },
		route: '/baseline/tasks/processing-speed'
	},
	{
		key: 'visual_scanning',
		title: { en: 'Visual Scanning', bn: 'ভিজ্যুয়াল স্ক্যানিং' },
		route: '/baseline/tasks/visual-scanning'
	}
];

function localeText(locale, variants) {
	return locale === 'bn' ? variants.bn : variants.en;
}

function numberText(locale, value, options = {}) {
	return new Intl.NumberFormat(locale === 'bn' ? 'bn-BD' : 'en-US', options).format(
		Number(value) || 0
	);
}

function formatDate(locale, value, options = {}) {
	if (!value) {
		return localeText(locale, { en: 'Not available', bn: 'পাওয়া যায়নি' });
	}

	return new Date(value).toLocaleDateString(locale === 'bn' ? 'bn-BD' : 'en-US', options);
}

function formatTime(locale, value) {
	if (!value) {
		return localeText(locale, { en: 'Not available', bn: 'পাওয়া যায়নি' });
	}

	return new Date(value).toLocaleTimeString(locale === 'bn' ? 'bn-BD' : 'en-US', {
		hour: 'numeric',
		minute: '2-digit'
	});
}

function getStoredJson(key) {
	if (typeof localStorage === 'undefined') return null;

	try {
		const value = localStorage.getItem(key);
		return value ? JSON.parse(value) : null;
	} catch (_error) {
		return null;
	}
}

export function getDashboardContext() {
	const user = getStoredJson('user');
	const preferredLocale =
		user?.preferences?.language ||
		(typeof localStorage !== 'undefined' ? localStorage.getItem('preferred-locale') : null) ||
		'en';

	return {
		user,
		locale: preferredLocale === 'bn' ? 'bn' : 'en'
	};
}

async function requestJson(fetchImpl, path) {
	const response = await fetchImpl(`${API_BASE_URL}${path}`);
	if (!response.ok) {
		throw new Error(`Request failed: ${path}`);
	}

	return response.json();
}

function getUnreadCount(userId, notifications) {
	if (typeof localStorage === 'undefined') return 0;

	const seenKey = `patient-notifications-seen-${userId}`;
	const lastSeen = localStorage.getItem(seenKey);
	const lastSeenTime = lastSeen ? new Date(lastSeen).getTime() : 0;

	return notifications.filter((notification) => new Date(notification.created_at).getTime() > lastSeenTime)
		.length;
}

function getDisplayName(user, locale) {
	return user?.fullName || user?.full_name || user?.email || localeText(locale, { en: 'Patient', bn: 'রোগী' });
}

function getDomainName(locale, domain) {
	const domainNames = {
		working_memory: { en: 'Working Memory', bn: 'ওয়ার্কিং মেমরি' },
		attention: { en: 'Attention', bn: 'মনোযোগ' },
		flexibility: { en: 'Cognitive Flexibility', bn: 'মানসিক নমনীয়তা' },
		planning: { en: 'Planning', bn: 'পরিকল্পনা' },
		processing_speed: { en: 'Processing Speed', bn: 'প্রসেসিং স্পিড' },
		visual_scanning: { en: 'Visual Scanning', bn: 'ভিজ্যুয়াল স্ক্যানিং' }
	};

	return localeText(locale, domainNames[domain] || { en: 'Training', bn: 'ট্রেনিং' });
}

function getDifficultyLabel(locale, difficulty) {
	if (!difficulty || difficulty <= 3) {
		return localeText(locale, { en: 'Gentle', bn: 'সহজ' });
	}
	if (difficulty <= 6) {
		return localeText(locale, { en: 'Steady', bn: 'স্থিতিশীল' });
	}
	if (difficulty <= 8) {
		return localeText(locale, { en: 'Focused', bn: 'মনোযোগী' });
	}

	return localeText(locale, { en: 'Advanced', bn: 'উন্নত' });
}

function getTaskLabel(locale, task) {
	return getPatientTaskLabel(task?.task_key || task?.task_type || '', locale, task?.domain);
}

function getBadgeCopy(locale, badge) {
	return getPatientBadgeCopy(badge?.badge_id || badge?.id || '', locale);
}

function getFocusReason(locale, task) {
	const fallbackKey =
		task?.priority === 'primary'
			? 'weakest_area'
			: task?.priority === 'secondary'
				? 'growth_area'
				: 'maintenance_area';

	return getPatientFocusReason(task?.focus_reason_key || fallbackKey, locale);
}

function createWarnings(locale, settledEntries) {
	const failedCount = settledEntries.filter((entry) => entry.status === 'rejected').length;
	if (!failedCount) return [];

	return [
		localeText(locale, {
			en: 'A few sections are still loading. Your core patient actions are available.',
			bn: 'কিছু অংশ এখনো লোড হচ্ছে। আপনার মূল রোগী-সম্পর্কিত কাজগুলো ব্যবহার করা যাবে।'
		})
	];
}

function createHeaderActions(locale, unreadCount) {
	return [
		{
			label: localeText(locale, { en: 'Notifications', bn: 'নোটিফিকেশন' }),
			href: '/notifications',
			badge: unreadCount > 0 ? numberText(locale, unreadCount) : ''
		},
		{
			label: localeText(locale, { en: 'Messages', bn: 'বার্তা' }),
			href: '/messages'
		},
		{
			label: localeText(locale, { en: 'Profile', bn: 'প্রোফাইল' }),
			href: '/profile'
		},
		{
			label: localeText(locale, { en: 'Settings', bn: 'সেটিংস' }),
			href: '/settings'
		},
		{
			type: 'logout',
			label: localeText(locale, { en: 'Logout', bn: 'লগআউট' })
		}
	];
}

function createHero(locale, { baselineStatus, nextTasks, streak, metrics }) {
	const baselineIncomplete = !baselineStatus?.all_completed;
	const recommendedTask = nextTasks?.tasks?.find((task) => !task.completed) || nextTasks?.tasks?.[0] || null;

	if (baselineIncomplete) {
		return {
			label: localeText(locale, { en: 'Today', bn: 'আজ' }),
			title: localeText(locale, {
				en: 'Finish the last baseline steps first',
				bn: 'আগে বেসলাইনের বাকি ধাপগুলো শেষ করুন'
			}),
			description: localeText(locale, {
				en: 'Complete the remaining baseline modules once, then your training and progress insights become much more useful.',
				bn: 'বাকি বেসলাইন মডিউলগুলো একবার সম্পন্ন করুন, তারপর ট্রেনিং ও অগ্রগতির ইনসাইট আরও কাজে লাগবে।'
			}),
			status: {
				label: localeText(locale, { en: 'Baseline status', bn: 'বেসলাইন অবস্থা' }),
				value:
					locale === 'bn'
						? `${numberText(locale, baselineStatus?.completed_count || 0)}/${numberText(locale, baselineStatus?.total_tasks || 6)} সম্পন্ন`
						: `${baselineStatus?.completed_count || 0}/${baselineStatus?.total_tasks || 6} complete`
			},
			primaryAction: {
				label: localeText(locale, { en: 'Review baseline', bn: 'বেসলাইন দেখুন' }),
				href: '/baseline/results'
			},
			secondaryAction: {
				label: localeText(locale, { en: 'Open profile', bn: 'প্রোফাইল খুলুন' }),
				href: '/profile'
			},
			facts: [
				{
					label: localeText(locale, { en: 'Current streak', bn: 'বর্তমান ধারাবাহিকতা' }),
					value:
						streak?.current_streak > 0
							? locale === 'bn'
								? `${numberText(locale, streak.current_streak)} দিন`
								: `${streak.current_streak} days`
							: localeText(locale, { en: 'Not started', bn: 'এখনো শুরু হয়নি' })
				},
				{
					label: localeText(locale, { en: 'Last training', bn: 'সর্বশেষ ট্রেনিং' }),
					value: formatDate(locale, metrics?.last_training_date)
				},
				{
					label: localeText(locale, { en: 'Next unlock', bn: 'পরের আনলক' }),
					value: localeText(locale, { en: 'Training plan', bn: 'ট্রেনিং প্ল্যান' })
				}
			]
		};
	}

	return {
		label: localeText(locale, { en: 'Today', bn: 'আজ' }),
		title: recommendedTask
			? locale === 'bn'
				? `${getDomainName(locale, recommendedTask.domain)}-এ ছোট কিন্তু গুরুত্বপূর্ণ একটি ধাপ নিন`
				: `Take one calm next step in ${getDomainName(locale, recommendedTask.domain)}`
			: localeText(locale, {
				en: 'Your training plan is ready for today',
				bn: 'আজকের জন্য আপনার ট্রেনিং প্ল্যান প্রস্তুত'
			}),
		description: recommendedTask
			? locale === 'bn'
				? `${getTaskLabel(locale, recommendedTask)} দিয়ে আজকের সেশন শুরু করলে গতি ধরে রাখা সহজ হবে।`
				: `Start with ${getTaskLabel(locale, recommendedTask)} to keep today simple and consistent.`
			: localeText(locale, {
				en: 'Open your training plan when you are ready to continue.',
				bn: 'চালিয়ে যেতে প্রস্তুত হলে ট্রেনিং প্ল্যান খুলুন।'
			}),
		status: recommendedTask
			? {
				label: localeText(locale, { en: 'Recommended focus', bn: 'প্রস্তাবিত ফোকাস' }),
				value:
					locale === 'bn'
						? `${getDifficultyLabel(locale, recommendedTask.difficulty)} · লেভেল ${numberText(locale, recommendedTask.difficulty)}/10`
						: `${getDifficultyLabel(locale, recommendedTask.difficulty)} · Level ${recommendedTask.difficulty}/10`
			}
			: null,
		primaryAction: {
			label: localeText(locale, { en: 'Open training', bn: 'ট্রেনিং খুলুন' }),
			href: '/training'
		},
		secondaryAction: {
			label: localeText(locale, { en: 'View insights', bn: 'ইনসাইট দেখুন' }),
			href: '/progress/insights'
		},
		facts: [
			{
				label: localeText(locale, { en: 'Current streak', bn: 'বর্তমান ধারাবাহিকতা' }),
				value:
					streak?.current_streak > 0
						? locale === 'bn'
							? `${numberText(locale, streak.current_streak)} দিন`
							: `${streak.current_streak} days`
						: localeText(locale, { en: 'Build it today', bn: 'আজ থেকেই গড়ুন' })
			},
			{
				label: localeText(locale, { en: 'Sessions done', bn: 'সম্পন্ন সেশন' }),
				value: numberText(locale, metrics?.total_sessions || 0)
			},
			{
				label: localeText(locale, { en: 'Last activity', bn: 'সর্বশেষ কার্যকলাপ' }),
				value: formatDate(locale, metrics?.last_training_date)
			}
		]
	};
}

function createQuickActions(locale, { baselineStatus, doctorState, prescriptionSummary }) {
	const hasDoctor = Boolean(doctorState?.assigned && doctorState?.doctor);

	return [
		{
			label: localeText(locale, { en: 'Training', bn: 'ট্রেনিং' }),
			href: '/training',
			eyebrow: localeText(locale, { en: 'Daily plan', bn: 'দৈনিক পরিকল্পনা' }),
			description: localeText(locale, {
				en: 'Open today’s session and focus areas.',
				bn: 'আজকের সেশন ও ফোকাস এলাকা খুলুন।'
			})
		},
		{
			label: localeText(locale, { en: 'Progress', bn: 'অগ্রগতি' }),
			href: '/progress',
			eyebrow: localeText(locale, { en: 'Recovery view', bn: 'রেকভারি ভিউ' }),
			description: localeText(locale, {
				en: 'See your overview, history, and domains.',
				bn: 'ওভারভিউ, হিস্ট্রি ও ডোমেইন দেখুন।'
			})
		},
		{
			label: localeText(locale, { en: 'Insights', bn: 'ইনসাইট' }),
			href: '/progress/insights',
			eyebrow: localeText(locale, { en: 'Insight view', bn: 'ইনসাইট ভিউ' }),
			description: localeText(locale, {
				en: 'Review biomarkers and check-in trends.',
				bn: 'বায়োমার্কার ও চেক-ইন ট্রেন্ড দেখুন।'
			})
		},
		{
			label: hasDoctor
				? localeText(locale, { en: 'Prescriptions', bn: 'প্রেসক্রিপশন' })
				: localeText(locale, { en: 'Find doctor', bn: 'ডাক্তার খুঁজুন' }),
			href: hasDoctor ? '/prescriptions' : '/find-doctor',
			eyebrow: hasDoctor
				? localeText(locale, { en: 'Care access', bn: 'কেয়ার অ্যাক্সেস' })
				: localeText(locale, { en: 'Care support', bn: 'কেয়ার সহায়তা' }),
			description: hasDoctor
				? locale === 'bn'
					? `${numberText(locale, prescriptionSummary?.summary?.active || 0)}টি সক্রিয় প্রেসক্রিপশন দেখুন।`
					: `Review ${prescriptionSummary?.summary?.active || 0} active prescriptions.`
				: localeText(locale, {
					en: 'Connect with a clinician when you need guided support.',
					bn: 'নির্দেশিত সহায়তা দরকার হলে চিকিৎসকের সঙ্গে যুক্ত হোন।'
				})
		}
	];
}

function createTodayPlan(locale, { baselineStatus, nextTasks, weeklySummary, doctorState }) {
	const baselineIncomplete = !baselineStatus?.all_completed;
	const nextTask = nextTasks?.tasks?.find((task) => !task.completed) || nextTasks?.tasks?.[0] || null;
	const hasDoctor = Boolean(doctorState?.assigned && doctorState?.doctor);

	return {
		label: localeText(locale, { en: 'Workspace Snapshot', bn: 'ওয়ার্কস্পেস স্ন্যাপশট' }),
		title: localeText(locale, { en: 'A quick read of what matters today', bn: 'আজ কী গুরুত্বপূর্ণ তার ছোট সারাংশ' }),
		cards: [
			{
				eyebrow: localeText(locale, { en: 'Plan state', bn: 'প্ল্যান অবস্থা' }),
				title: baselineIncomplete
					? localeText(locale, { en: 'Baseline still in progress', bn: 'বেসলাইন এখনো চলছে' })
					: localeText(locale, { en: 'Training plan active', bn: 'ট্রেনিং প্ল্যান সক্রিয়' }),
				meta: baselineIncomplete
					? locale === 'bn'
						? `${numberText(locale, baselineStatus?.completed_count || 0)}/${numberText(locale, baselineStatus?.total_tasks || 6)} মডিউল সম্পন্ন`
						: `${baselineStatus?.completed_count || 0}/${baselineStatus?.total_tasks || 6} modules complete`
					: locale === 'bn'
						? `${numberText(locale, nextTasks?.session_number || 1)} নম্বর সেশন প্রস্তুত`
						: `Session ${nextTasks?.session_number || 1} is ready`
			},
			{
				eyebrow: localeText(locale, { en: 'Next step', bn: 'পরের ধাপ' }),
				title: nextTask ? getTaskLabel(locale, nextTask) : localeText(locale, { en: 'Open your training plan', bn: 'ট্রেনিং প্ল্যান খুলুন' }),
				meta: nextTask
					? locale === 'bn'
						? `${getDomainName(locale, nextTask.domain)} · ${getDifficultyLabel(locale, nextTask.difficulty)}`
						: `${getDomainName(locale, nextTask.domain)} · ${getDifficultyLabel(locale, nextTask.difficulty)}`
					: localeText(locale, { en: 'Ready when you are', bn: 'আপনি প্রস্তুত হলেই শুরু' })
			},
			{
				eyebrow: localeText(locale, { en: 'Weekly rhythm', bn: 'সাপ্তাহিক রিদম' }),
				title: weeklySummary?.has_data
					? locale === 'bn'
						? `${numberText(locale, weeklySummary.total_sessions)}টি সেশন`
						: `${weeklySummary.total_sessions} sessions`
					: localeText(locale, { en: 'Still building', bn: 'এখনো গড়ে উঠছে' }),
				meta: weeklySummary?.has_data
					? locale === 'bn'
						? `${numberText(locale, weeklySummary.active_days)}/7 দিন সক্রিয়`
						: `${weeklySummary.active_days}/7 days active`
					: localeText(locale, { en: 'Train a little more to unlock this', bn: 'এটি দেখতে আরও কিছু ট্রেনিং করুন' })
			},
			{
				eyebrow: localeText(locale, { en: 'Care connection', bn: 'কেয়ার সংযোগ' }),
				title: hasDoctor
					? doctorState.doctor.full_name
					: localeText(locale, { en: 'Independent mode', bn: 'স্বতন্ত্র মোড' }),
				meta: hasDoctor
					? doctorState.doctor.specialization
					: localeText(locale, { en: 'Browse doctors when needed', bn: 'প্রয়োজনে ডাক্তার খুঁজুন' })
			}
		]
	};
}

function createProgressPreview(locale, { weeklySummary, comparisonData, trendsData, recentBadges }) {
	const comparisonEntries = Object.entries(comparisonData?.comparison || {});
	const strongestGain = comparisonEntries
		.map(([domain, value]) => ({
			domain,
			improvement: Number(value?.improvement) || 0
		}))
		.sort((left, right) => right.improvement - left.improvement)[0];
	const latestBadge = recentBadges?.badges?.[0] || null;
	const trendPoints = trendsData?.overall_trend || [];
	const trendDelta =
		trendPoints.length > 1
			? Number(((trendPoints.at(-1)?.avg_score || 0) - (trendPoints[0]?.avg_score || 0)).toFixed(1))
			: null;

	return {
		label: localeText(locale, { en: 'Progress Preview', bn: 'অগ্রগতির প্রিভিউ' }),
		title: localeText(locale, { en: 'Keep progress readable, not overwhelming', bn: 'অগ্রগতি যেন বোঝা সহজ হয়, ভারী না লাগে' }),
		description: localeText(locale, {
			en: 'Open deeper views only when you want more detail.',
			bn: 'আরও বিস্তারিত চাইলে তবেই গভীর ভিউ খুলুন।'
		}),
		cards: [
			{
				eyebrow: localeText(locale, { en: 'Weekly summary', bn: 'সাপ্তাহিক সারাংশ' }),
				title: weeklySummary?.has_data
					? locale === 'bn'
						? `${numberText(locale, weeklySummary.total_sessions)}টি সেশন`
						: `${weeklySummary.total_sessions} sessions`
					: localeText(locale, { en: 'No summary yet', bn: 'এখনো সারাংশ নেই' }),
				description: weeklySummary?.has_data
					? locale === 'bn'
						? `${numberText(locale, weeklySummary.active_days)}টি সক্রিয় দিন · ${numberText(locale, weeklySummary.total_time_minutes)} মিনিট`
						: `${weeklySummary.active_days} active days · ${weeklySummary.total_time_minutes} minutes`
					: localeText(locale, { en: 'A fuller weekly summary appears after more training.', bn: 'আরও ট্রেনিং হলে সম্পূর্ণ সারাংশ দেখা যাবে।' })
			},
			{
				eyebrow: localeText(locale, { en: 'Trend', bn: 'ট্রেন্ড' }),
				title:
					trendDelta === null
						? localeText(locale, { en: 'Still building', bn: 'এখনো তৈরি হচ্ছে' })
						: trendDelta > 0
							? locale === 'bn'
								? `${numberText(locale, trendDelta)} পয়েন্ট উপরে`
								: `${trendDelta} points up`
							: trendDelta < 0
								? locale === 'bn'
									? `${numberText(locale, Math.abs(trendDelta))} পয়েন্ট নিচে`
									: `${Math.abs(trendDelta)} points down`
								: localeText(locale, { en: 'Stable', bn: 'স্থিতিশীল' }),
				description: localeText(locale, {
					en: 'Based on your recent overall score pattern.',
					bn: 'সাম্প্রতিক সামগ্রিক স্কোরের ধারা থেকে তৈরি।'
				})
			},
			{
				eyebrow: localeText(locale, { en: 'Best gain', bn: 'সবচেয়ে ভালো উন্নতি' }),
				title: strongestGain
					? getDomainName(locale, strongestGain.domain)
					: localeText(locale, { en: 'Not available yet', bn: 'এখনো পাওয়া যায়নি' }),
				description: strongestGain
					? locale === 'bn'
						? `${numberText(locale, strongestGain.improvement)} পয়েন্ট বেসলাইনের তুলনায়`
						: `${strongestGain.improvement} points vs baseline`
					: localeText(locale, { en: 'More sessions will make this clearer.', bn: 'আরও সেশন হলে এটি স্পষ্ট হবে।' })
			},
			{
				eyebrow: localeText(locale, { en: 'Latest badge', bn: 'সর্বশেষ ব্যাজ' }),
				title: latestBadge ? getBadgeCopy(locale, latestBadge).name : getPatientCopy('no_badge_yet', locale),
				description: latestBadge ? getBadgeCopy(locale, latestBadge).description : localeText(locale, { en: 'Badges appear as your practice becomes more consistent.', bn: 'নিয়মিত অনুশীলনের সঙ্গে ব্যাজ দেখা যাবে।' })
			}
		],
		links: [
			{ label: localeText(locale, { en: 'Overview', bn: 'ওভারভিউ' }), href: '/progress' },
			{ label: localeText(locale, { en: 'Domains', bn: 'ডোমেইন' }), href: '/progress/domains' },
			{ label: localeText(locale, { en: 'History', bn: 'হিস্ট্রি' }), href: '/progress/history' },
			{ label: localeText(locale, { en: 'Insights', bn: 'ইনসাইট' }), href: '/progress/insights' }
		]
	};
}

function createCarePreview(locale, { notifications, unreadCount, prescriptionSummary, doctorState }) {
	const latestNotification = notifications[0] || null;
	const latestPrescription = prescriptionSummary?.prescriptions?.[0] || null;
	const hasDoctor = Boolean(doctorState?.assigned && doctorState?.doctor);

	return {
		label: localeText(locale, { en: 'Care Preview', bn: 'কেয়ার প্রিভিউ' }),
		title: localeText(locale, { en: 'Patient support without clutter', bn: 'অপ্রয়োজনীয় ভিড় ছাড়া রোগী-সহায়তা' }),
		description: localeText(locale, {
			en: 'This area keeps care context close while the heavier workflows stay on their own pages.',
			bn: 'ভারী কাজগুলো আলাদা পেজে রেখে এখানে কেয়ার-সম্পর্কিত প্রসঙ্গ কাছে রাখা হয়েছে।'
		}),
		items: [
			{
				eyebrow: localeText(locale, { en: 'Care team', bn: 'কেয়ার টিম' }),
				title: hasDoctor ? doctorState.doctor.full_name : localeText(locale, { en: 'No doctor assigned yet', bn: 'এখনো কোনো ডাক্তার নির্ধারিত হয়নি' }),
				description: hasDoctor
					? `${doctorState.doctor.specialization}${doctorState.doctor.institution ? ` · ${doctorState.doctor.institution}` : ''}`
					: localeText(locale, { en: 'Browse doctors when you want guided support.', bn: 'নির্দেশিত সহায়তা চাইলে ডাক্তার খুঁজুন।' }),
				meta: hasDoctor && doctorState.doctor.assigned_at ? [formatDate(locale, doctorState.doctor.assigned_at)] : [],
				action: {
					label: hasDoctor
						? localeText(locale, { en: 'Browse doctors', bn: 'ডাক্তার দেখুন' })
						: localeText(locale, { en: 'Find doctor', bn: 'ডাক্তার খুঁজুন' }),
					href: '/find-doctor'
				}
			},
			{
				eyebrow: localeText(locale, { en: 'Prescription status', bn: 'প্রেসক্রিপশন অবস্থা' }),
				title: latestPrescription?.title || localeText(locale, { en: 'No recent prescription', bn: 'সাম্প্রতিক কোনো প্রেসক্রিপশন নেই' }),
				description: latestPrescription
					? locale === 'bn'
						? `${formatDate(locale, latestPrescription.created_at)} তারিখে ইস্যু করা হয়েছে`
						: `Issued ${formatDate(locale, latestPrescription.created_at)}`
					: localeText(locale, { en: 'Clinician-issued plans will appear here when available.', bn: 'চিকিৎসকের দেওয়া পরিকল্পনা এখানে দেখা যাবে।' }),
				meta: latestPrescription?.doctor_name ? [latestPrescription.doctor_name] : [],
				action: {
					label: localeText(locale, { en: 'Open prescriptions', bn: 'প্রেসক্রিপশন খুলুন' }),
					href: '/prescriptions'
				}
			},
			{
				eyebrow: localeText(locale, { en: 'Notifications', bn: 'নোটিফিকেশন' }),
				title:
					unreadCount > 0
						? locale === 'bn'
							? `${numberText(locale, unreadCount)}টি নতুন আপডেট`
							: `${unreadCount} new updates`
						: localeText(locale, { en: 'Inbox looks calm', bn: 'ইনবক্স এখন শান্ত' }),
				description: latestNotification?.title || localeText(locale, { en: 'Your latest care-related updates appear here first.', bn: 'কেয়ার-সম্পর্কিত সর্বশেষ আপডেট আগে এখানে দেখা যাবে।' }),
				meta: latestNotification?.created_at ? [formatTime(locale, latestNotification.created_at)] : []
			}
		]
	};
}

function createTrainingPreview(locale, { baselineStatus, nextTasks, metrics }) {
	const baselineIncomplete = !baselineStatus?.all_completed;

	if (baselineIncomplete) {
		return {
			label: localeText(locale, { en: 'Baseline Access', bn: 'বেসলাইন অ্যাক্সেস' }),
			title: localeText(locale, { en: 'Finish the remaining modules once', bn: 'বাকি মডিউলগুলো একবার শেষ করুন' }),
			description: localeText(locale, { en: 'The baseline opens personalized training and richer progress views.', bn: 'বেসলাইন সম্পন্ন হলে ব্যক্তিগত ট্রেনিং ও সমৃদ্ধ অগ্রগতি ভিউ খুলে যায়।' }),
			items: baselineModules.map((module) => {
				const complete = Boolean(baselineStatus?.tasks?.[module.key]);
				return {
					eyebrow: complete
						? localeText(locale, { en: 'Completed', bn: 'সম্পন্ন' })
						: localeText(locale, { en: 'Pending', bn: 'বাকি' }),
					title: localeText(locale, module.title),
					description: complete
						? localeText(locale, { en: 'This module is already complete.', bn: 'এই মডিউলটি ইতিমধ্যে সম্পন্ন হয়েছে।' })
						: localeText(locale, { en: 'Open this module to continue your baseline.', bn: 'বেসলাইন চালিয়ে যেতে এই মডিউল খুলুন।' }),
					tone: complete ? 'complete' : 'pending',
					action: {
						label: localeText(locale, { en: 'Open module', bn: 'মডিউল খুলুন' }),
						href: module.route
					}
				};
			}),
			footerAction: {
				label: localeText(locale, { en: 'Review baseline results', bn: 'বেসলাইন ফলাফল দেখুন' }),
				href: '/baseline/results'
			}
		};
	}

	const nextCards = (nextTasks?.tasks || []).slice(0, 4);
	return {
		label: localeText(locale, { en: 'Training Access', bn: 'ট্রেনিং অ্যাক্সেস' }),
		title: localeText(locale, { en: 'The next session is ready', bn: 'পরের সেশন প্রস্তুত' }),
		description: localeText(locale, { en: 'Use this preview to stay oriented, then move into the full training workspace.', bn: 'এই প্রিভিউ দিয়ে দিক ঠিক রাখুন, তারপর পূর্ণ ট্রেনিং ওয়ার্কস্পেসে যান।' }),
		items: nextCards.map((task) => ({
			eyebrow:
				task.priority === 'primary'
					? localeText(locale, { en: 'Primary focus', bn: 'প্রধান ফোকাস' })
					: task.priority === 'secondary'
						? localeText(locale, { en: 'Secondary focus', bn: 'দ্বিতীয় ফোকাস' })
						: localeText(locale, { en: 'Maintenance', bn: 'রক্ষণাবেক্ষণ' }),
			title: getTaskLabel(locale, task),
			description:
				getFocusReason(locale, task),
			meta: [
				getDomainName(locale, task.domain),
				locale === 'bn'
					? `লেভেল ${numberText(locale, task.difficulty)}/10`
					: `Level ${task.difficulty}/10`
			],
			tone: task.completed ? 'complete' : 'primary'
		})),
		footerAction: {
			label:
				metrics?.total_sessions > 0
					? localeText(locale, { en: 'Continue training', bn: 'ট্রেনিং চালিয়ে যান' })
					: localeText(locale, { en: 'Start training', bn: 'ট্রেনিং শুরু করুন' }),
			href: '/training'
		}
	};
}

function createInsightsRail(locale, { notifications, streak, biomarkers, recentContext }) {
	const latestNotification = notifications[0] || null;
	const latestContext = recentContext?.contexts?.[0] || null;
	const hasBiomarkers = (biomarkers?.total_sessions || 0) >= 3;

	return {
		label: localeText(locale, { en: 'Calm Context', bn: 'শান্ত প্রসঙ্গ' }),
		title: localeText(locale, { en: 'Just enough context for today', bn: 'আজকের জন্য যতটুকু জানা দরকার' }),
		cards: [
			{
				eyebrow: localeText(locale, { en: 'Streak', bn: 'ধারাবাহিকতা' }),
				title:
					streak?.current_streak > 0
						? locale === 'bn'
							? `${numberText(locale, streak.current_streak)} দিন`
							: `${streak.current_streak} days`
						: localeText(locale, { en: 'Start one today', bn: 'আজ একটি শুরু করুন' }),
				body: localeText(locale, {
					en: 'Small, repeatable sessions matter more than intensity.',
					bn: 'অতিরিক্ত চাপের চেয়ে ছোট কিন্তু নিয়মিত সেশন বেশি গুরুত্বপূর্ণ।'
				})
			},
			{
				eyebrow: localeText(locale, { en: 'Brain health', bn: 'মস্তিষ্কের স্বাস্থ্য' }),
				title: hasBiomarkers
					? localeText(locale, { en: 'Insights ready', bn: 'ইনসাইট প্রস্তুত' })
					: localeText(locale, { en: 'Unlock after 3 sessions', bn: '৩টি সেশনের পর আনলক হবে' }),
				body: hasBiomarkers
					? locale === 'bn'
						? `ফ্যাটিগ সূচক ${Number(biomarkers?.fatigue_index?.mean || 0).toFixed(2)} · প্রতিক্রিয়ার ধারাবাহিকতা ${Number(biomarkers?.rt_coefficient_of_variation?.mean || 0).toFixed(2)}`
						: `Fatigue index ${Number(biomarkers?.fatigue_index?.mean || 0).toFixed(2)} · response consistency ${Number(biomarkers?.rt_coefficient_of_variation?.mean || 0).toFixed(2)}`
					: localeText(locale, { en: 'Keep training and this area will become more meaningful.', bn: 'ট্রেনিং চালিয়ে যান, এই অংশটি আরও অর্থবহ হবে।' }),
				action: {
					label: localeText(locale, { en: 'Open insights', bn: 'ইনসাইট খুলুন' }),
					href: '/progress/insights'
				}
			},
			{
				eyebrow: localeText(locale, { en: 'Latest check-in', bn: 'সর্বশেষ চেক-ইন' }),
				title: latestContext
					? formatDate(locale, latestContext.created_at)
					: localeText(locale, { en: 'No check-in yet', bn: 'এখনো চেক-ইন নেই' }),
				body: latestContext
					? locale === 'bn'
						? `শক্তি ${numberText(locale, latestContext.fatigue_level || 0)}/10 · প্রস্তুতি ${numberText(locale, latestContext.readiness_level || 0)}/10`
						: `Energy ${latestContext.fatigue_level || 0}/10 · readiness ${latestContext.readiness_level || 0}/10`
					: latestNotification?.title ||
						localeText(locale, { en: 'A short check-in before training helps explain your trends.', bn: 'ট্রেনিংয়ের আগে ছোট চেক-ইন আপনার ট্রেন্ড বুঝতে সাহায্য করে।' })
			}
		]
	};
}

function shortDate(locale, value) {
	return formatDate(locale, value, { day: 'numeric', month: 'short' });
}

function createDashboardHero(locale, { baselineStatus, nextTasks, streak, metrics }) {
	const baselineIncomplete = !baselineStatus?.all_completed;
	const nextTask = nextTasks?.tasks?.find((task) => !task.completed) || nextTasks?.tasks?.[0] || null;

	if (baselineIncomplete) {
		return {
			label: localeText(locale, { en: 'Today', bn: 'আজ' }),
			title: localeText(locale, { en: 'Finish your baseline first', bn: 'আগে বেসলাইন শেষ করুন' }),
			description: localeText(locale, {
				en: 'Complete the remaining modules once to unlock a better training flow.',
				bn: 'বাকি মডিউলগুলো শেষ করলে ট্রেনিং আরও পরিষ্কারভাবে খুলবে।'
			}),
			status: {
				label: localeText(locale, { en: 'Baseline', bn: 'বেসলাইন' }),
				value:
					locale === 'bn'
						? `${numberText(locale, baselineStatus?.completed_count || 0)}/${numberText(locale, baselineStatus?.total_tasks || 6)} শেষ`
						: `${baselineStatus?.completed_count || 0}/${baselineStatus?.total_tasks || 6} done`
			},
			primaryAction: {
				label: localeText(locale, { en: 'View baseline results', bn: 'বেসলাইন ফলাফল দেখুন' }),
				href: '/baseline/results'
			},
			facts: [
				{
					label: localeText(locale, { en: 'Streak', bn: 'ধারাবাহিকতা' }),
					value:
						streak?.current_streak > 0
							? locale === 'bn'
								? `${numberText(locale, streak.current_streak)} দিন`
								: `${streak.current_streak} days`
							: localeText(locale, { en: 'Not started', bn: 'শুরু হয়নি' })
				},
				{
					label: localeText(locale, { en: 'Last activity', bn: 'সর্বশেষ কাজ' }),
					value: metrics?.last_training_date
						? shortDate(locale, metrics.last_training_date)
						: localeText(locale, { en: 'No session yet', bn: 'এখনও সেশন হয়নি' })
				},
				{
					label: localeText(locale, { en: 'Next unlock', bn: 'পরের ধাপ' }),
					value: localeText(locale, { en: 'Training plan', bn: 'ট্রেনিং প্ল্যান' })
				}
			]
		};
	}

	return {
		label: localeText(locale, { en: 'Today', bn: 'আজ' }),
		title: nextTask ? getTaskLabel(locale, nextTask) : localeText(locale, { en: 'Training is ready', bn: 'ট্রেনিং প্রস্তুত' }),
		description: nextTask
			? locale === 'bn'
				? `${getDomainName(locale, nextTask.domain)} দিয়ে আজকের সেশন শুরু করুন।`
				: `Start today with ${getDomainName(locale, nextTask.domain)}.`
			: localeText(locale, {
				en: 'Open your plan when you are ready for the next session.',
				bn: 'পরের সেশনের জন্য প্রস্তুত হলে প্ল্যান খুলুন।'
			}),
		status: nextTask
			? {
				label: localeText(locale, { en: 'Focus', bn: 'ফোকাস' }),
				value:
					locale === 'bn'
						? `${getDifficultyLabel(locale, nextTask.difficulty)} · লেভেল ${numberText(locale, nextTask.difficulty)}/10`
						: `${getDifficultyLabel(locale, nextTask.difficulty)} · Level ${nextTask.difficulty}/10`
			}
			: null,
		primaryAction: {
			label:
				(metrics?.total_sessions || 0) > 0
					? localeText(locale, { en: 'Continue training', bn: 'ট্রেনিং চালিয়ে যান' })
					: localeText(locale, { en: 'Start training', bn: 'ট্রেনিং শুরু করুন' }),
			href: '/training'
		},
		facts: [
			{
				label: localeText(locale, { en: 'Streak', bn: 'ধারাবাহিকতা' }),
				value:
					streak?.current_streak > 0
						? locale === 'bn'
							? `${numberText(locale, streak.current_streak)} দিন`
							: `${streak.current_streak} days`
						: localeText(locale, { en: 'Start today', bn: 'আজ শুরু করুন' })
			},
			{
				label: localeText(locale, { en: 'Sessions', bn: 'সেশন' }),
				value: numberText(locale, metrics?.total_sessions || 0)
			},
			{
				label: localeText(locale, { en: 'Last activity', bn: 'সর্বশেষ কাজ' }),
				value: metrics?.last_training_date
					? shortDate(locale, metrics.last_training_date)
					: localeText(locale, { en: 'No session yet', bn: 'এখনও সেশন হয়নি' })
			}
		]
	};
}

function createTodayStats(locale, { baselineStatus, nextTasks, weeklySummary, doctorState, unreadCount }) {
	const baselineIncomplete = !baselineStatus?.all_completed;
	const hasDoctor = Boolean(doctorState?.assigned && doctorState?.doctor);

	return [
		{
			label: baselineIncomplete
				? localeText(locale, { en: 'Baseline', bn: 'বেসলাইন' })
				: localeText(locale, { en: 'Session', bn: 'সেশন' }),
			value: baselineIncomplete
				? locale === 'bn'
					? `${numberText(locale, baselineStatus?.completed_count || 0)}/${numberText(locale, baselineStatus?.total_tasks || 6)}`
					: `${baselineStatus?.completed_count || 0}/${baselineStatus?.total_tasks || 6}`
				: locale === 'bn'
					? `সেশন ${numberText(locale, nextTasks?.session_number || 1)}`
					: `Session ${nextTasks?.session_number || 1}`
		},
		{
			label: localeText(locale, { en: 'This week', bn: 'এই সপ্তাহ' }),
			value: weeklySummary?.has_data
				? locale === 'bn'
					? `${numberText(locale, weeklySummary.total_sessions || 0)} সেশন`
					: `${weeklySummary?.total_sessions || 0} sessions`
				: localeText(locale, { en: 'Building', bn: 'তৈরি হচ্ছে' })
		},
		{
			label: localeText(locale, { en: 'Care', bn: 'কেয়ার' }),
			value: hasDoctor
				? localeText(locale, { en: 'Connected', bn: 'যুক্ত' })
				: localeText(locale, { en: 'Independent', bn: 'স্বতন্ত্র' })
		},
		{
			label: localeText(locale, { en: 'Updates', bn: 'আপডেট' }),
			value:
				unreadCount > 0
					? locale === 'bn'
						? `${numberText(locale, unreadCount)} নতুন`
						: `${unreadCount} new`
					: localeText(locale, { en: 'Calm', bn: 'শান্ত' })
		}
	];
}

function createProgressPulse(locale, { metrics, weeklySummary, comparisonData, trendsData, recentBadges }) {
	const comparisonEntries = Object.entries(comparisonData?.comparison || {});
	const strongestGain = comparisonEntries
		.map(([domain, value]) => ({
			domain,
			improvement: Number(value?.improvement) || 0
		}))
		.sort((left, right) => right.improvement - left.improvement)[0];
	const trendPoints = trendsData?.overall_trend || [];
	const trendDelta =
		trendPoints.length > 1
			? Number(((trendPoints.at(-1)?.avg_score || 0) - (trendPoints[0]?.avg_score || 0)).toFixed(1))
			: null;
	const latestBadge = recentBadges?.badges?.[0] || null;

	return {
		label: localeText(locale, { en: 'Progress', bn: 'অগ্রগতি' }),
		title: localeText(locale, { en: 'Your recovery pulse', bn: 'আপনার রিকভারি পালস' }),
		tone: 'progress',
		action: {
			label: localeText(locale, { en: 'Open progress', bn: 'অগ্রগতি খুলুন' }),
			href: '/progress'
		},
		metrics: [
			{
				label: localeText(locale, { en: 'Sessions', bn: 'সেশন' }),
				value: numberText(locale, metrics?.total_sessions || 0)
			},
			{
				label: localeText(locale, { en: 'Weekly rhythm', bn: 'সাপ্তাহিক ছন্দ' }),
				value: weeklySummary?.has_data
					? locale === 'bn'
						? `${numberText(locale, weeklySummary.active_days || 0)}/7 দিন`
						: `${weeklySummary?.active_days || 0}/7 days`
					: localeText(locale, { en: 'Building', bn: 'তৈরি হচ্ছে' })
			},
			{
				label: localeText(locale, { en: 'Best signal', bn: 'সেরা সংকেত' }),
				value: latestBadge
					? getBadgeCopy(locale, latestBadge).name
					: strongestGain?.improvement > 0
						? getDomainName(locale, strongestGain.domain)
						: trendDelta !== null
							? trendDelta > 0
								? localeText(locale, { en: 'Improving', bn: 'উন্নতি' })
								: trendDelta < 0
									? localeText(locale, { en: 'Rebuilding', bn: 'পুনর্গঠন' })
									: localeText(locale, { en: 'Stable', bn: 'স্থিতিশীল' })
							: localeText(locale, { en: 'Early stage', bn: 'শুরুর ধাপ' })
			}
		]
	};
}

function createCarePulse(locale, { doctorState, prescriptionSummary, unreadCount, notifications }) {
	const hasDoctor = Boolean(doctorState?.assigned && doctorState?.doctor);
	const activePrescriptions = prescriptionSummary?.summary?.active || 0;
	const latestNotification = notifications?.[0] || null;

	return {
		label: localeText(locale, { en: 'Care', bn: 'কেয়ার' }),
		title: localeText(locale, { en: 'Care stays in sync', bn: 'কেয়ার সমন্বিত থাকুক' }),
		tone: 'care',
		action:
			hasDoctor || activePrescriptions > 0
				? {
					label: localeText(locale, { en: 'Open prescriptions', bn: 'প্রেসক্রিপশন খুলুন' }),
					href: '/prescriptions'
				}
				: {
					label: localeText(locale, { en: 'Find doctor', bn: 'ডাক্তার খুঁজুন' }),
					href: '/find-doctor'
				},
		metrics: [
			{
				label: localeText(locale, { en: 'Doctor', bn: 'ডাক্তার' }),
				value: hasDoctor
					? doctorState.doctor.full_name
					: localeText(locale, { en: 'Not linked', bn: 'যুক্ত নয়' })
			},
			{
				label: localeText(locale, { en: 'Prescriptions', bn: 'প্রেসক্রিপশন' }),
				value:
					activePrescriptions > 0
						? locale === 'bn'
							? `${numberText(locale, activePrescriptions)} সক্রিয়`
							: `${activePrescriptions} active`
						: localeText(locale, { en: 'None yet', bn: 'এখনও নেই' })
			},
			{
				label: localeText(locale, { en: 'Latest update', bn: 'সর্বশেষ আপডেট' }),
				value:
					unreadCount > 0
						? locale === 'bn'
							? `${numberText(locale, unreadCount)} নতুন`
							: `${unreadCount} new`
						: latestNotification?.created_at
							? shortDate(locale, latestNotification.created_at)
							: localeText(locale, { en: 'Quiet', bn: 'নীরব' })
			}
		]
	};
}

function createInsightPulse(locale, { biomarkers, recentContext, trendsData }) {
	const contextEntries = recentContext?.contexts || [];
	const trendPoints = trendsData?.overall_trend || [];
	const hasBiomarkers = (biomarkers?.total_sessions || 0) >= 3;

	if (!hasBiomarkers && contextEntries.length === 0 && trendPoints.length < 2) {
		return null;
	}

	let trendValue = localeText(locale, { en: 'Stable', bn: 'স্থিতিশীল' });
	if (trendPoints.length > 1) {
		const trendDelta = (trendPoints.at(-1)?.avg_score || 0) - (trendPoints[0]?.avg_score || 0);
		trendValue =
			trendDelta > 0
				? localeText(locale, { en: 'Improving', bn: 'উন্নতি' })
				: trendDelta < 0
					? localeText(locale, { en: 'Needs rest', bn: 'বিশ্রাম দরকার' })
					: localeText(locale, { en: 'Stable', bn: 'স্থিতিশীল' });
	}

	return {
		label: localeText(locale, { en: 'Insights', bn: 'ইনসাইট' }),
		title: localeText(locale, { en: 'Deeper signals are ready', bn: 'গভীর সংকেত প্রস্তুত' }),
		tone: 'insight',
		action: {
			label: localeText(locale, { en: 'Open insights', bn: 'ইনসাইট খুলুন' }),
			href: '/progress/insights'
		},
		metrics: [
			{
				label: localeText(locale, { en: 'Biomarkers', bn: 'বায়োমার্কার' }),
				value: hasBiomarkers
					? localeText(locale, { en: 'Ready', bn: 'প্রস্তুত' })
					: localeText(locale, { en: 'Collecting', bn: 'সংগ্রহ হচ্ছে' })
			},
			{
				label: localeText(locale, { en: 'Check-ins', bn: 'চেক-ইন' }),
				value:
					contextEntries.length > 0
						? locale === 'bn'
							? `${numberText(locale, contextEntries.length)}টি`
							: `${contextEntries.length}`
						: localeText(locale, { en: 'None yet', bn: 'এখনও নেই' })
			},
			{
				label: localeText(locale, { en: 'Trend', bn: 'ট্রেন্ড' }),
				value: trendValue
			}
		]
	};
}

function createJourneyDashboardHero(locale, { journey, nextTasks, streak, metrics }) {
	const baselineStatus = journey?.baseline || {};
	const nextTask = nextTasks?.tasks?.find((task) => !task.completed) || nextTasks?.tasks?.[0] || null;
	const baselineProgress =
		locale === 'bn'
			? `${numberText(locale, baselineStatus?.completed_count || 0)}/${numberText(locale, baselineStatus?.total_tasks || 6)} complete`
			: `${baselineStatus?.completed_count || 0}/${baselineStatus?.total_tasks || 6} complete`;

	if (journey?.state === 'new_user' || journey?.state === 'baseline_in_progress') {
		return {
			label: localeText(locale, { en: 'Start here', bn: 'শুরু' }),
			title:
				journey?.state === 'new_user'
					? localeText(locale, { en: 'Start your baseline journey', bn: 'আপনার বেসলাইন যাত্রা শুরু করুন' })
					: localeText(locale, { en: 'Continue your baseline', bn: 'আপনার বেসলাইন চালিয়ে যান' }),
			description: localeText(locale, {
				en: 'Complete the six baseline domains once. That unlocks the regular training and progress flow.',
				bn: 'ছয়টি বেসলাইন ডোমেইন একবার সম্পন্ন করুন। তারপরই নিয়মিত ট্রেনিং ও অগ্রগতির প্রবাহ খুলবে।'
			}),
			status: {
				label: localeText(locale, { en: 'Baseline', bn: 'বেসলাইন' }),
				value: baselineProgress
			},
			primaryAction: {
				label:
					journey?.state === 'new_user'
						? localeText(locale, { en: 'Open baseline', bn: 'বেসলাইন খুলুন' })
						: localeText(locale, { en: 'Continue baseline', bn: 'বেসলাইন চালিয়ে যান' }),
				href: '/baseline'
			},
			secondaryAction: baselineStatus?.next_route
				? {
					label: localeText(locale, { en: 'Open next task', bn: 'পরের টাস্ক খুলুন' }),
					href: baselineStatus.next_route
				}
				: null,
			facts: [
				{
					label: localeText(locale, { en: 'Baseline', bn: 'বেসলাইন' }),
					value: baselineProgress
				},
				{
					label: localeText(locale, { en: 'Next unlock', bn: 'পরের ধাপ' }),
					value: localeText(locale, { en: 'Baseline calculation', bn: 'বেসলাইন ক্যালকুলেশন' })
				},
				{
					label: localeText(locale, { en: 'Training', bn: 'ট্রেনিং' }),
					value: localeText(locale, { en: 'Locked for now', bn: 'এখনো লকড' })
				}
			]
		};
	}

	if (journey?.state === 'baseline_ready_to_calculate') {
		return {
			label: localeText(locale, { en: 'Ready', bn: 'প্রস্তুত' }),
			title: localeText(locale, { en: 'Your baseline is ready to calculate', bn: 'আপনার বেসলাইন ক্যালকুলেট করার জন্য প্রস্তুত' }),
			description: localeText(locale, {
				en: 'All six baseline tasks are complete. Calculate the baseline first, then generate the first training plan.',
				bn: 'ছয়টি বেসলাইন টাস্ক সম্পন্ন হয়েছে। আগে বেসলাইন ক্যালকুলেট করুন, তারপর প্রথম ট্রেনিং প্ল্যান তৈরি করুন।'
			}),
			status: {
				label: localeText(locale, { en: 'Baseline', bn: 'বেসলাইন' }),
				value: baselineProgress
			},
			primaryAction: {
				label: localeText(locale, { en: 'Open baseline workspace', bn: 'বেসলাইন ওয়ার্কস্পেস খুলুন' }),
				href: '/baseline'
			},
			facts: [
				{
					label: localeText(locale, { en: 'Baseline', bn: 'বেসলাইন' }),
					value: baselineProgress
				},
				{
					label: localeText(locale, { en: 'Next unlock', bn: 'পরের ধাপ' }),
					value: localeText(locale, { en: 'Training plan', bn: 'ট্রেনিং প্ল্যান' })
				},
				{
					label: localeText(locale, { en: 'Progress', bn: 'অগ্রগতি' }),
					value: localeText(locale, { en: 'Available after training starts', bn: 'ট্রেনিং শুরু হলে পাওয়া যাবে' })
				}
			]
		};
	}

	if (journey?.state === 'training_plan_missing') {
		return {
			label: localeText(locale, { en: 'Next step', bn: 'পরের ধাপ' }),
			title: localeText(locale, { en: 'Generate your first training plan', bn: 'আপনার প্রথম ট্রেনিং প্ল্যান তৈরি করুন' }),
			description: localeText(locale, {
				en: 'Your baseline has been calculated. Generate the personalized plan to unlock daily training.',
				bn: 'আপনার বেসলাইন ক্যালকুলেট হয়েছে। এখন ব্যক্তিগত ট্রেনিং প্ল্যান তৈরি করলেই দৈনিক ট্রেনিং খুলবে।'
			}),
			status: {
				label: localeText(locale, { en: 'Plan', bn: 'প্ল্যান' }),
				value: localeText(locale, { en: 'Not generated yet', bn: 'এখনো তৈরি হয়নি' })
			},
			primaryAction: {
				label: localeText(locale, { en: 'Open baseline results', bn: 'বেসলাইন রেজাল্ট খুলুন' }),
				href: '/baseline/results'
			},
			facts: [
				{
					label: localeText(locale, { en: 'Baseline', bn: 'বেসলাইন' }),
					value: localeText(locale, { en: 'Calculated', bn: 'ক্যালকুলেটেড' })
				},
				{
					label: localeText(locale, { en: 'Training', bn: 'ট্রেনিং' }),
					value: localeText(locale, { en: 'Opens after plan generation', bn: 'প্ল্যান তৈরি হলে খুলবে' })
				},
				{
					label: localeText(locale, { en: 'Progress', bn: 'অগ্রগতি' }),
					value: localeText(locale, { en: 'Later in the journey', bn: 'যাত্রার পরের ধাপে' })
				}
			]
		};
	}

	if (journey?.state === 'system_not_ready') {
		return {
			label: localeText(locale, { en: 'System', bn: 'সিস্টেম' }),
			title: localeText(locale, { en: 'Training is blocked by setup', bn: 'সেটআপের কারণে ট্রেনিং আটকে আছে' }),
			description:
				journey?.blocking_reason ||
				localeText(locale, {
					en: 'The task catalog is missing, so today’s session cannot be assembled yet.',
					bn: 'টাস্ক ক্যাটালগ অনুপস্থিত, তাই আজকের সেশন এখনো তৈরি করা যাচ্ছে না।'
				}),
			status: {
				label: localeText(locale, { en: 'Training', bn: 'ট্রেনিং' }),
				value: localeText(locale, { en: 'Blocked', bn: 'আটকে আছে' })
			},
			primaryAction: {
				label: localeText(locale, { en: 'Open training', bn: 'ট্রেনিং খুলুন' }),
				href: '/training'
			},
			facts: [
				{
					label: localeText(locale, { en: 'Baseline', bn: 'বেসলাইন' }),
					value: localeText(locale, { en: 'Ready', bn: 'প্রস্তুত' })
				},
				{
					label: localeText(locale, { en: 'Plan', bn: 'প্ল্যান' }),
					value: localeText(locale, { en: 'Available', bn: 'পাওয়া গেছে' })
				},
				{
					label: localeText(locale, { en: 'Catalog', bn: 'ক্যাটালগ' }),
					value: localeText(locale, { en: 'Needs setup', bn: 'সেটআপ দরকার' })
				}
			]
		};
	}

	return {
		label: localeText(locale, { en: 'Today', bn: 'আজ' }),
		title: nextTask ? getTaskLabel(locale, nextTask) : localeText(locale, { en: 'Training is ready', bn: '??????? ????????' }),
		description: nextTask
			? locale === 'bn'
				? `${getDomainName(locale, nextTask.domain)} দিয়ে আজকের সেশন শুরু করুন।`
				: `Start today with ${getDomainName(locale, nextTask.domain)}.`
			: localeText(locale, {
				en: 'Open your training workspace when you are ready for the next session.',
				bn: 'পরের সেশনের জন্য প্রস্তুত হলে ট্রেনিং ওয়ার্কস্পেস খুলুন।'
			}),
		status: nextTask
			? {
				label: localeText(locale, { en: 'Focus', bn: 'ফোকাস' }),
				value: `${getDifficultyLabel(locale, nextTask.difficulty)} · ${localeText(locale, { en: 'Level', bn: 'লেভেল' })} ${numberText(locale, nextTask.difficulty)}/10`
			}
			: null,
		primaryAction: {
			label:
				journey?.state === 'training_in_session'
					? localeText(locale, { en: 'Continue session', bn: 'সেশন চালিয়ে যান' })
					: (metrics?.total_sessions || 0) > 0
						? localeText(locale, { en: 'Continue training', bn: 'ট্রেনিং চালিয়ে যান' })
						: localeText(locale, { en: 'Start training', bn: 'ট্রেনিং শুরু করুন' }),
			href: '/training'
		},
		secondaryAction:
			journey?.state === 'progress_available'
				? {
					label: localeText(locale, { en: 'Open progress', bn: 'অগ্রগতি খুলুন' }),
					href: '/progress'
				}
				: null,
		facts: [
			{
				label: localeText(locale, { en: 'Streak', bn: 'ধারাবাহিকতা' }),
				value:
					streak?.current_streak > 0
						? `${numberText(locale, streak.current_streak)} ${localeText(locale, { en: 'days', bn: 'দিন' })}`
						: localeText(locale, { en: 'Start today', bn: 'আজ শুরু করুন' })
			},
			{
				label: localeText(locale, { en: 'Sessions', bn: 'সেশন' }),
				value: numberText(locale, metrics?.total_sessions || 0)
			},
			{
				label: localeText(locale, { en: 'Last activity', bn: 'সর্বশেষ কাজ' }),
				value: metrics?.last_training_date
					? shortDate(locale, metrics.last_training_date)
					: localeText(locale, { en: 'No session yet', bn: 'এখনো সেশন হয়নি' })
			}
		]
	};
}

function createJourneyTodayStats(locale, { journey, nextTasks, weeklySummary, doctorState, unreadCount }) {
	const baselineStatus = journey?.baseline || {};
	const baselineIncomplete = journey?.state === 'new_user' || journey?.state === 'baseline_in_progress';
	const hasDoctor = Boolean(doctorState?.assigned && doctorState?.doctor);

	return [
		{
			label: baselineIncomplete
				? localeText(locale, { en: 'Baseline', bn: 'বেসলাইন' })
				: journey?.state === 'baseline_ready_to_calculate'
					? localeText(locale, { en: 'Baseline', bn: 'বেসলাইন' })
					: journey?.state === 'training_plan_missing'
						? localeText(locale, { en: 'Plan', bn: 'প্ল্যান' })
						: localeText(locale, { en: 'Session', bn: 'সেশন' }),
			value: baselineIncomplete
				? `${numberText(locale, baselineStatus?.completed_count || 0)}/${numberText(locale, baselineStatus?.total_tasks || 6)}`
				: journey?.state === 'baseline_ready_to_calculate'
					? localeText(locale, { en: 'Ready to calculate', bn: 'ক্যালকুলেটের জন্য প্রস্তুত' })
					: journey?.state === 'training_plan_missing'
						? localeText(locale, { en: 'Needs generation', bn: 'তৈরি করা বাকি' })
						: `${localeText(locale, { en: 'Session', bn: 'সেশন' })} ${numberText(locale, nextTasks?.session_number || 1)}`
		},
		{
			label: localeText(locale, { en: 'This week', bn: 'এই সপ্তাহ' }),
			value: weeklySummary?.has_data
				? `${numberText(locale, weeklySummary.total_sessions || 0)} ${localeText(locale, { en: 'sessions', bn: 'সেশন' })}`
				: baselineIncomplete
					? localeText(locale, { en: 'Begins after baseline', bn: 'বেসলাইন শেষ হলে শুরু হবে' })
					: localeText(locale, { en: 'Building', bn: 'তৈরি হচ্ছে' })
		},
		{
			label: localeText(locale, { en: 'Care', bn: 'কেয়ার' }),
			value: hasDoctor
				? localeText(locale, { en: 'Connected', bn: 'যুক্ত' })
				: localeText(locale, { en: 'Independent', bn: 'স্বতন্ত্র' })
		},
		{
			label: localeText(locale, { en: 'Updates', bn: 'আপডেট' }),
			value:
				unreadCount > 0
					? `${numberText(locale, unreadCount)} ${localeText(locale, { en: 'new', bn: 'নতুন' })}`
					: localeText(locale, { en: 'Calm', bn: 'শান্ত' })
		}
	];
}

function createLockedProgressPulse(locale, journey) {
	return {
		label: localeText(locale, { en: 'Progress', bn: 'অগ্রগতি' }),
		title: localeText(locale, { en: 'Progress unlocks after training starts', bn: 'ট্রেনিং শুরু হলে অগ্রগতি খুলবে' }),
		tone: 'progress',
		action: {
			label: localeText(locale, { en: 'Open next step', bn: 'পরের ধাপ খুলুন' }),
			href: journey?.next_route || '/baseline'
		},
		metrics: [
			{
				label: localeText(locale, { en: 'Current stage', bn: 'বর্তমান ধাপ' }),
				value: journey?.next_label || localeText(locale, { en: 'Start baseline', bn: 'বেসলাইন শুরু করুন' })
			},
			{
				label: localeText(locale, { en: 'Baseline', bn: 'বেসলাইন' }),
				value: `${numberText(locale, journey?.baseline?.completed_count || 0)}/${numberText(locale, journey?.baseline?.total_tasks || 6)}`
			},
			{
				label: localeText(locale, { en: 'Training sessions', bn: 'ট্রেনিং সেশন' }),
				value: numberText(locale, journey?.progress?.training_sessions_count || 0)
			}
		]
	};
}

export async function createPatientDashboardViewModel({ fetchImpl, user, locale }) {
	const userId = user?.id;
	const journey = await requestJson(fetchImpl, `/api/patient-journey/${userId}`);
	const sharedRequestSet = await Promise.allSettled([
		requestJson(fetchImpl, `/api/auth/patient/${userId}/notifications`),
		requestJson(fetchImpl, `/api/auth/patient/${userId}/prescriptions`),
		requestJson(fetchImpl, `/api/doctor/patient/${userId}/assigned-doctor`)
	]);
	const [notificationsResult, prescriptionsResult, doctorResult] = sharedRequestSet;

	let trainingRequestSet = [];
	let metrics = null;
	let streak = null;
	let nextTasks = null;
	let weeklySummary = null;
	let comparisonData = null;
	let trendsData = null;
	let recentBadges = null;
	let biomarkers = null;
	let recentContext = null;

	const shouldLoadTraining =
		journey?.state === 'training_ready' ||
		journey?.state === 'training_in_session' ||
		journey?.state === 'progress_available' ||
		journey?.state === 'system_not_ready';

	if (shouldLoadTraining) {
		trainingRequestSet = await Promise.allSettled([
			requestJson(fetchImpl, `/api/training/training-session/metrics/${userId}?_t=${Date.now()}`),
			requestJson(fetchImpl, `/api/training/training-plan/${userId}/streak`),
			requestJson(fetchImpl, `/api/training/training-plan/${userId}/next-tasks?_t=${Date.now()}`),
			requestJson(fetchImpl, `/api/training/weekly-summary/${userId}`)
		]);

		metrics = trainingRequestSet[0].status === 'fulfilled' ? trainingRequestSet[0].value : null;
		if (metrics?.has_data === false) metrics = null;
		streak = trainingRequestSet[1].status === 'fulfilled' ? trainingRequestSet[1].value : null;
		nextTasks = trainingRequestSet[2].status === 'fulfilled' ? trainingRequestSet[2].value : null;
		weeklySummary = trainingRequestSet[3].status === 'fulfilled' ? trainingRequestSet[3].value : null;
	}

	let progressRequestSet = [];
	const shouldLoadProgress = journey?.progress?.unlocked;
	if (shouldLoadProgress) {
		progressRequestSet = await Promise.allSettled([
			requestJson(fetchImpl, `/api/training/training-session/performance-comparison/${userId}?_t=${Date.now()}`),
			requestJson(fetchImpl, `/api/training/trends/${userId}?days=30`),
			requestJson(fetchImpl, `/api/training/badges/recent/${userId}?limit=3`),
			requestJson(fetchImpl, `/api/training/advanced-analytics/${userId}/biomarkers?days=30`),
			requestJson(fetchImpl, `/api/training/session-context/${userId}/recent?limit=4`)
		]);

		comparisonData = progressRequestSet[0].status === 'fulfilled' ? progressRequestSet[0].value : null;
		if (comparisonData?.has_data === false) comparisonData = null;
		trendsData = progressRequestSet[1].status === 'fulfilled' ? progressRequestSet[1].value : null;
		recentBadges = progressRequestSet[2].status === 'fulfilled' ? progressRequestSet[2].value : null;
		biomarkers = progressRequestSet[3].status === 'fulfilled' ? progressRequestSet[3].value : null;
		recentContext = progressRequestSet[4].status === 'fulfilled' ? progressRequestSet[4].value : null;
	}

	const notifications =
		notificationsResult.status === 'fulfilled' ? notificationsResult.value?.notifications || [] : [];
	const prescriptionSummary =
		prescriptionsResult.status === 'fulfilled' ? prescriptionsResult.value : null;
	const doctorState =
		doctorResult.status === 'fulfilled'
			? doctorResult.value
			: { assigned: false, doctor: null, error: true };
	const unreadCount = getUnreadCount(userId, notifications);
	const requestSet = [...sharedRequestSet, ...trainingRequestSet, ...progressRequestSet];

	return {
		header: {
			brand: 'NeuroBloom',
			title: getPatientCopy('dashboard_title', locale),
			subtitle: '',
			description: getPatientCopy('dashboard_description', locale),
			logoutLabel: localeText(locale, { en: 'Logout', bn: 'লগআউট' })
		},
		headerActions: createHeaderActions(locale, unreadCount),
		hero: createJourneyDashboardHero(locale, { journey, nextTasks, streak, metrics }),
		todayStats: createJourneyTodayStats(locale, {
			journey,
			nextTasks,
			weeklySummary,
			doctorState,
			unreadCount
		}),
		progressPulse: shouldLoadProgress
			? createProgressPulse(locale, {
				metrics,
				weeklySummary,
				comparisonData,
				trendsData,
				recentBadges
			})
			: createLockedProgressPulse(locale, journey),
		carePulse: createCarePulse(locale, {
			doctorState,
			prescriptionSummary,
			unreadCount,
			notifications
		}),
		insightPulse: shouldLoadProgress
			? createInsightPulse(locale, {
				biomarkers,
				recentContext,
				trendsData
			})
			: null,
		warnings: createWarnings(locale, requestSet)
	};
}


import { API_BASE_URL } from '$lib/api.js';

const modules = [
	{
		key: 'working_memory',
		title: { en: 'Working Memory', bn: 'ওয়ার্কিং মেমরি' },
		description: { en: 'Memory and recall exercises.', bn: 'স্মৃতি ও মনে রাখার অনুশীলন।' },
		route: '/baseline/tasks/working-memory'
	},
	{
		key: 'attention',
		title: { en: 'Attention', bn: 'মনোযোগ' },
		description: { en: 'Focus and concentration practice.', bn: 'মনোযোগ ও একাগ্রতার অনুশীলন।' },
		route: '/baseline/tasks/attention'
	},
	{
		key: 'flexibility',
		title: { en: 'Cognitive Flexibility', bn: 'কগনিটিভ ফ্লেক্সিবিলিটি' },
		description: { en: 'Adapting to changing rules.', bn: 'নিয়ম বদলালে মানিয়ে নেওয়ার অনুশীলন।' },
		route: '/baseline/tasks/flexibility'
	},
	{
		key: 'planning',
		title: { en: 'Planning', bn: 'পরিকল্পনা' },
		description: { en: 'Strategy and problem solving.', bn: 'কৌশল ও সমস্যা সমাধানের অনুশীলন।' },
		route: '/baseline/tasks/planning'
	},
	{
		key: 'processing_speed',
		title: { en: 'Processing Speed', bn: 'প্রসেসিং স্পিড' },
		description: { en: 'Speed and response practice.', bn: 'গতি ও দ্রুত সাড়া দেওয়ার অনুশীলন।' },
		route: '/baseline/tasks/processing-speed'
	},
	{
		key: 'visual_scanning',
		title: { en: 'Visual Scanning', bn: 'ভিজুয়াল স্ক্যানিং' },
		description: { en: 'Visual search and detection.', bn: 'চোখে দেখে খুঁজে বের করার অনুশীলন।' },
		route: '/baseline/tasks/visual-scanning'
	}
];

function localeText(locale, variants) {
	return locale === 'bn' ? variants.bn : variants.en;
}

function numberText(locale, value, options = {}) {
	return new Intl.NumberFormat(locale === 'bn' ? 'bn-BD' : 'en-US', options).format(Number(value) || 0);
}

function formatDate(locale, dateValue) {
	if (!dateValue) {
		return localeText(locale, { en: 'Not yet', bn: 'এখনও নয়' });
	}

	return new Date(dateValue).toLocaleDateString(locale === 'bn' ? 'bn-BD' : 'en-US');
}

function dayLabel(locale, value) {
	const count = Number(value) || 0;
	const label = locale === 'bn' ? 'দিন' : `day${count === 1 ? '' : 's'}`;
	return `${numberText(locale, count)} ${label}`;
}

function unreadLabel(locale, count) {
	const displayCount = count > 9 ? `${numberText(locale, 9)}+` : numberText(locale, count);
	return count > 0
		? localeText(locale, { en: `${displayCount} waiting`, bn: `${displayCount}টি অপেক্ষায়` })
		: localeText(locale, { en: 'No unread updates', bn: 'কোনো অপঠিত আপডেট নেই' });
}

function baselineSummaryLabel(locale, baselineStatus) {
	if (!baselineStatus) {
		return localeText(locale, { en: 'Baseline unavailable', bn: 'বেসলাইন পাওয়া যায়নি' });
	}

	return locale === 'bn'
		? `${numberText(locale, baselineStatus.completed_count)}/${numberText(locale, baselineStatus.total_tasks)} সম্পন্ন`
		: `${baselineStatus.completed_count}/${baselineStatus.total_tasks} complete`;
}

function issuedPrescriptionLabel(locale, dateValue) {
	const dateText = formatDate(locale, dateValue);
	return locale === 'bn' ? `${dateText} তারিখে দেওয়া হয়েছে` : `Issued ${dateText}`;
}

function getDisplayName(user, locale) {
	return user?.fullName || user?.full_name || user?.email || localeText(locale, { en: 'Patient', bn: 'পেশেন্ট' });
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

	return notifications.filter((notification) => new Date(notification.created_at).getTime() > lastSeenTime).length;
}

function getPrimaryRecommendation(nextTasks) {
	if (!nextTasks?.tasks?.length) return null;
	return nextTasks.tasks.find((task) => !task.completed) || nextTasks.tasks[0];
}

function getDomainName(locale, domain) {
	const domainNames = {
		working_memory: { en: 'Working Memory', bn: 'ওয়ার্কিং মেমরি' },
		attention: { en: 'Attention', bn: 'মনোযোগ' },
		flexibility: { en: 'Cognitive Flexibility', bn: 'কগনিটিভ ফ্লেক্সিবিলিটি' },
		planning: { en: 'Planning', bn: 'পরিকল্পনা' },
		processing_speed: { en: 'Processing Speed', bn: 'প্রসেসিং স্পিড' },
		visual_scanning: { en: 'Visual Scanning', bn: 'ভিজুয়াল স্ক্যানিং' }
	};

	return localeText(locale, domainNames[domain] || { en: 'Training', bn: 'ট্রেনিং' });
}

function createWarnings(locale, settledEntries) {
	const failedCount = settledEntries.filter((entry) => entry.status === 'rejected').length;
	if (!failedCount) return [];

	return [
		localeText(locale, {
			en: 'Some dashboard sections could not be loaded. You can still continue with the main actions.',
			bn: 'ড্যাশবোর্ডের কিছু অংশ লোড করা যায়নি। তবুও আপনি মূল কাজগুলো চালিয়ে যেতে পারবেন।'
		})
	];
}

function createTodaySlice(locale, primaryRecommendation, unreadCount, streak) {
	const description = primaryRecommendation
		? locale === 'bn'
			? `${getDomainName(locale, primaryRecommendation.domain)} অনুশীলনের জন্য ${primaryRecommendation.task_name || 'প্রস্তাবিত ট্রেনিং'} দিয়ে শুরু করুন। একবারে একটি কাজ করলেই যথেষ্ট।`
			: `Start with ${primaryRecommendation.task_name || 'your recommended training'} for ${getDomainName(locale, primaryRecommendation.domain).toLowerCase()}. One step at a time is enough.`
		: localeText(locale, {
			en: 'Finish your baseline first so we can suggest the best next training step for you.',
			bn: 'আগে আপনার বেসলাইন সম্পন্ন করুন, তাহলে আপনার জন্য উপযুক্ত পরের ট্রেনিং ধাপ সাজানো যাবে।'
		});

	return {
		label: localeText(locale, { en: 'Today', bn: 'আজ' }),
		title: primaryRecommendation
			? localeText(locale, { en: 'Start with one clear next step', bn: 'একটি পরিষ্কার পরের ধাপ দিয়ে শুরু করুন' })
			: localeText(locale, { en: 'Begin with your baseline', bn: 'বেসলাইন দিয়ে শুরু করুন' }),
		description,
		action: primaryRecommendation
			? {
				label: localeText(locale, { en: "Open Today's Training", bn: 'আজকের ট্রেনিং খুলুন' }),
				href: '/training'
			}
			: {
				label: localeText(locale, { en: 'Review Baseline', bn: 'বেসলাইন দেখুন' }),
				href: '/baseline/results'
			},
		facts: [
			{
				label: localeText(locale, { en: 'Unread updates', bn: 'অপঠিত আপডেট' }),
				value: unreadCount > 9 ? `${numberText(locale, 9)}+` : numberText(locale, unreadCount)
			},
			{
				label: localeText(locale, { en: 'Current streak', bn: 'বর্তমান ধারাবাহিকতা' }),
				value: streak
					? dayLabel(locale, streak.current_streak || 0)
					: localeText(locale, { en: 'Unavailable', bn: 'পাওয়া যায়নি' })
			}
		]
	};
}

function createProgressSlice(locale, stats, streak, baselineStatus) {
	return {
		label: localeText(locale, { en: 'Your Progress', bn: 'আপনার অগ্রগতি' }),
		title: localeText(locale, { en: 'Three simple markers to follow', bn: 'তিনটি সহজ অগ্রগতি সূচক' }),
		metrics: [
			{
				label: localeText(locale, { en: 'Last training', bn: 'সর্বশেষ ট্রেনিং' }),
				value: stats ? formatDate(locale, stats.last_training_date) : localeText(locale, { en: 'Unavailable', bn: 'পাওয়া যায়নি' })
			},
			{
				label: localeText(locale, { en: 'Current streak', bn: 'বর্তমান ধারাবাহিকতা' }),
				value: streak ? dayLabel(locale, streak.current_streak || 0) : localeText(locale, { en: 'Unavailable', bn: 'পাওয়া যায়নি' })
			},
			{
				label: localeText(locale, { en: 'Baseline progress', bn: 'বেসলাইন অগ্রগতি' }),
				value: baselineSummaryLabel(locale, baselineStatus)
			}
		]
	};
}

function createCareSummarySlice(locale, unreadCount, latestPrescription) {
	return {
		label: localeText(locale, { en: 'Care', bn: 'কেয়ার' }),
		title: localeText(locale, { en: 'Updates and support', bn: 'আপডেট ও সহায়তা' }),
		disclosureLabel: localeText(locale, { en: 'See care details', bn: 'কেয়ার বিস্তারিত দেখুন' }),
		items: [
			{
				label: localeText(locale, { en: 'Notifications', bn: 'নোটিফিকেশন' }),
				value: unreadLabel(locale, unreadCount),
				note: localeText(locale, { en: 'Open updates when you are ready.', bn: 'সময় হলে আপডেটগুলো খুলুন।' }),
				action: {
					href: '/notifications',
					label: localeText(locale, { en: 'Open', bn: 'খুলুন' })
				}
			},
			{
				label: localeText(locale, { en: 'Messages', bn: 'বার্তা' }),
				value: localeText(locale, { en: 'Care team inbox', bn: 'কেয়ার টিম ইনবক্স' }),
				note: localeText(locale, { en: 'Messages from your clinician or support team.', bn: 'চিকিৎসক বা সহায়তা দলের পাঠানো বার্তা।' }),
				action: {
					href: '/messages',
					label: localeText(locale, { en: 'Open', bn: 'খুলুন' })
				}
			},
			{
				label: localeText(locale, { en: 'Prescription', bn: 'প্রেসক্রিপশন' }),
				value: latestPrescription?.title || localeText(locale, { en: 'No recent prescription', bn: 'সাম্প্রতিক কোনো প্রেসক্রিপশন নেই' }),
				note: latestPrescription
					? issuedPrescriptionLabel(locale, latestPrescription.created_at)
					: localeText(locale, { en: 'Your latest medication plan will appear here.', bn: 'আপনার সর্বশেষ ওষুধের পরিকল্পনা এখানে দেখা যাবে।' })
			}
		],
		latestPrescription
	};
}

function createAreasSlice(locale, baselineStatus) {
	return {
		label: localeText(locale, { en: 'All Areas', bn: 'সব এলাকা' }),
		title: localeText(locale, {
			en: 'Choose an area to review or continue',
			bn: 'যে এলাকা দেখতে বা চালিয়ে যেতে চান, সেটি বেছে নিন'
		}),
		items: modules.map((module) => {
			const complete = Boolean(baselineStatus?.tasks?.[module.key]);
			return {
				title: localeText(locale, module.title),
				description: localeText(locale, module.description),
				href: module.route,
				complete,
				status: complete
					? localeText(locale, { en: 'Complete', bn: 'সম্পন্ন' })
					: localeText(locale, { en: 'Pending', bn: 'বাকি' })
			};
		})
	};
}

function createHeaderActions(locale, unreadCount) {
	return [
		{
			label: localeText(locale, { en: 'Notifications', bn: 'নোটিফিকেশন' }),
			href: '/notifications',
			badge:
				unreadCount > 0
					? unreadCount > 9
						? `${numberText(locale, 9)}+`
						: numberText(locale, unreadCount)
					: ''
		},
		{
			label: localeText(locale, { en: 'Messages', bn: 'বার্তা' }),
			href: '/messages'
		},
		{
			label: localeText(locale, { en: 'Doctor', bn: 'ডাক্তার' }),
			href: '/find-doctor'
		},
		{
			type: 'logout',
			label: localeText(locale, { en: 'Logout', bn: 'লগআউট' })
		}
	];
}

function createRailSlice(locale, unreadCount, notifications, latestPrescription) {
	const latestNotification = notifications[0] || null;
	const unreadBadge =
		unreadCount > 0 ? (unreadCount > 9 ? `${numberText(locale, 9)}+` : numberText(locale, unreadCount)) : '';

	return {
		label: localeText(locale, { en: 'Care & Access', bn: 'কেয়ার ও অ্যাক্সেস' }),
		title: localeText(locale, { en: 'Quick actions and updates', bn: 'দ্রুত কাজ ও আপডেট' }),
		detailsLabel: localeText(locale, { en: 'Open care details', bn: 'কেয়ার বিস্তারিত খুলুন' }),
		items: [
			{
				label: localeText(locale, { en: 'Notifications', bn: 'নোটিফিকেশন' }),
				value: unreadLabel(locale, unreadCount),
				note:
					latestNotification?.title ||
					localeText(locale, { en: 'Your newest update appears here.', bn: 'আপনার নতুন আপডেট এখানে দেখা যাবে।' }),
				action: {
					href: '/notifications',
					label: localeText(locale, { en: 'Open', bn: 'খুলুন' }),
					badge: unreadBadge
				}
			},
			{
				label: localeText(locale, { en: 'Messages', bn: 'বার্তা' }),
				value: localeText(locale, { en: 'Care team inbox', bn: 'কেয়ার টিম ইনবক্স' }),
				note: localeText(locale, { en: 'Ask questions or read replies from your care team.', bn: 'আপনার কেয়ার টিমের কাছে প্রশ্ন পাঠান বা উত্তর পড়ুন।' }),
				action: {
					href: '/messages',
					label: localeText(locale, { en: 'Open inbox', bn: 'ইনবক্স খুলুন' })
				}
			},
			{
				label: localeText(locale, { en: 'Doctor & care', bn: 'ডাক্তার ও কেয়ার' }),
				value: localeText(locale, { en: 'Support options', bn: 'সহায়তার অপশন' }),
				note: localeText(locale, { en: 'Review doctor availability and care support options.', bn: 'ডাক্তার ও কেয়ার সহায়তার অপশন দেখুন।' }),
				action: {
					href: '/find-doctor',
					label: localeText(locale, { en: 'Open', bn: 'খুলুন' })
				}
			},
			{
				label: localeText(locale, { en: 'Prescription', bn: 'প্রেসক্রিপশন' }),
				value:
					latestPrescription?.title ||
					localeText(locale, { en: 'No recent prescription', bn: 'সাম্প্রতিক কোনো প্রেসক্রিপশন নেই' }),
				note: latestPrescription
					? issuedPrescriptionLabel(locale, latestPrescription.created_at)
					: localeText(locale, { en: 'Your latest medication plan appears here.', bn: 'আপনার সর্বশেষ ওষুধের পরিকল্পনা এখানে দেখা যাবে।' }),
				action: {
					href: '/prescriptions',
					label: localeText(locale, { en: 'View', bn: 'দেখুন' })
				}
			}
		]
	};
}

export async function createPatientDashboardViewModel({ fetchImpl, user, locale }) {
	const userId = user?.id;
	const requestSet = await Promise.allSettled([
		requestJson(fetchImpl, `/api/tasks/results/${userId}/baseline-status`),
		requestJson(fetchImpl, `/api/auth/patient/${userId}/notifications`),
		requestJson(fetchImpl, `/api/training/training-session/metrics/${userId}?_t=${Date.now()}`),
		requestJson(fetchImpl, `/api/training/training-plan/${userId}/streak`),
		requestJson(fetchImpl, `/api/training/training-plan/${userId}/next-tasks?_t=${Date.now()}`),
		requestJson(fetchImpl, `/api/auth/patient/${userId}/prescriptions`)
	]);

	const [baselineStatusResult, notificationsResult, statsResult, streakResult, nextTasksResult, prescriptionsResult] = requestSet;
	const baselineStatus = baselineStatusResult.status === 'fulfilled' ? baselineStatusResult.value : null;
	const notifications = notificationsResult.status === 'fulfilled' ? notificationsResult.value?.notifications || [] : [];
	const stats = statsResult.status === 'fulfilled' ? statsResult.value : null;
	const streak = streakResult.status === 'fulfilled' ? streakResult.value : null;
	const nextTasks = nextTasksResult.status === 'fulfilled' ? nextTasksResult.value : null;
	const prescriptionSummary = prescriptionsResult.status === 'fulfilled' ? prescriptionsResult.value : null;
	const latestPrescription = prescriptionSummary?.prescriptions?.[0] || null;
	const unreadCount = getUnreadCount(userId, notifications);
	const primaryRecommendation = getPrimaryRecommendation(nextTasks);

	return {
		header: {
			brand: 'NeuroBloom',
			title: localeText(locale, { en: 'Patient Dashboard', bn: 'পেশেন্ট ড্যাশবোর্ড' }),
			subtitle: getDisplayName(user, locale),
			logoutLabel: localeText(locale, { en: 'Logout', bn: 'লগআউট' })
		},
		headerActions: createHeaderActions(locale, unreadCount),
		today: createTodaySlice(locale, primaryRecommendation, unreadCount, streak),
		progress: createProgressSlice(locale, stats, streak, baselineStatus),
		careSummary: createCareSummarySlice(locale, unreadCount, latestPrescription),
		areas: createAreasSlice(locale, baselineStatus),
		rail: createRailSlice(locale, unreadCount, notifications, latestPrescription),
		warnings: createWarnings(locale, requestSet)
	};
}

export async function loadPatientCareDetails({ fetchImpl, userId, locale }) {
	const detailRequests = await Promise.allSettled([
		requestJson(fetchImpl, `/api/auth/patient/${userId}/notifications`),
		requestJson(fetchImpl, `/api/doctor/patient/${userId}/assigned-doctor`)
	]);

	const [notificationsResult, doctorResult] = detailRequests;
	const notifications = notificationsResult.status === 'fulfilled' ? notificationsResult.value?.notifications || [] : [];
	const doctorState = doctorResult.status === 'fulfilled'
		? doctorResult.value
		: { assigned: false, doctor: null, error: true };

	return {
		notifications: notifications.slice(0, 4),
		doctor: doctorState.doctor || null,
		assignedDoctor: Boolean(doctorState.assigned && doctorState.doctor),
		hasWarning: detailRequests.some((entry) => entry.status === 'rejected'),
		locale,
		apiBaseUrl: API_BASE_URL
	};
}

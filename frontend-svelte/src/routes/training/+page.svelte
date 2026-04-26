<script>
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { patientJourney, training } from '$lib/api';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import PreTaskQuestionnaire from '$lib/components/PreTaskQuestionnaire.svelte';
	import { formatNumber, locale } from '$lib/i18n';
	import {
		getPatientDifficultyLabel,
		getPatientDomainLabel,
		getPatientFocusReason,
		getPatientPriorityLabel,
		getPatientTaskLabel
	} from '$lib/patient-copy.js';
	import { user } from '$lib/stores';
	import { buildTrainingTaskUrl } from '$lib/training-launch';
	import { onMount } from 'svelte';

	let currentUser = null;
	let loading = true;
	let trainingPlan = null;
	let nextTasks = null;
	let metrics = null;
	let error = null;
	let journey = null;
	let trainingState = 'loading';
	let newlyEarnedBadges = [];
	let showPreTaskQuestionnaire = false;
	let pendingTaskRoute = null;
	let pacingWarning = null;
	const SESSION_CONTEXT_PREFIX = 'training-session-context';

	function lt(en, bn) {
		return $locale === 'bn' ? bn : en;
	}

	function n(value, options = {}) {
		return formatNumber(value, $locale, options);
	}

	user.subscribe((value) => {
		currentUser = value;
	});

	onMount(() => {
		if (!currentUser) {
			goto('/login');
			return;
		}

		loadTrainingData();

		if (browser) {
			const handleVisibilityChange = () => {
				if (!document.hidden && currentUser) {
					loadTrainingData();
				}
			};

			document.addEventListener('visibilitychange', handleVisibilityChange);

			return () => {
				document.removeEventListener('visibilitychange', handleVisibilityChange);
			};
		}
	});

	async function loadTrainingData() {
		loading = true;
		error = null;
		pacingWarning = null;
		trainingState = 'loading';
		trainingPlan = null;
		nextTasks = null;
		metrics = null;

		try {
			journey = await patientJourney.get(currentUser.id);

			if (journey.state === 'new_user' || journey.state === 'baseline_in_progress') {
				trainingState = 'baseline_incomplete';
				return;
			}

			if (journey.state === 'baseline_ready_to_calculate') {
				trainingState = 'baseline_ready_to_calculate';
				return;
			}

			if (journey.state === 'training_plan_missing') {
				trainingState = 'plan_missing';
				return;
			}

			if (journey.state === 'system_not_ready') {
				trainingState = 'system_not_ready';
				return;
			}

			trainingPlan = await training.getPlan(currentUser.id);
			if (!trainingPlan?.has_plan) {
				trainingState = 'plan_missing';
				return;
			}
			nextTasks = await training.getNextTasks(currentUser.id);
			if (!nextTasks?.system_ready) {
				trainingState = 'system_not_ready';
				return;
			}

			try {
				metrics = await training.getMetrics(currentUser.id);
				if (metrics?.has_data === false) {
					metrics = null;
				}
			} catch (loadMetricsError) {
				metrics = null;
			}
			trainingState = 'plan_ready';
		} catch (loadError) {
			console.error('Error loading training data:', loadError);
			error = lt(
				'We could not load your training workspace right now.',
				'এই মুহূর্তে আপনার ট্রেনিং ওয়ার্কস্পেস লোড করা যাচ্ছে না।'
			);
			trainingState = 'error';
		} finally {
			loading = false;
		}
	}

	function getDomainName(domain) {
		return getPatientDomainLabel(domain, $locale);
	}

	function getPriorityLabel(priority) {
		return getPatientPriorityLabel(priority, $locale);
	}

	function getPriorityTone(priority) {
		if (priority === 'primary') return 'primary';
		if (priority === 'secondary') return 'secondary';
		return 'maintenance';
	}

	function getDifficultyLabel(difficulty) {
		return getPatientDifficultyLabel(difficulty, $locale);
	}

	function getTaskLabel(task) {
		return getPatientTaskLabel(task?.task_key || task?.task_type || '', $locale, task?.domain);
	}

	function getTaskReason(task) {
		const fallbackKey =
			task?.priority === 'primary'
				? 'weakest_area'
				: task?.priority === 'secondary'
					? 'growth_area'
					: 'maintenance_area';

		return getPatientFocusReason(task?.focus_reason_key || fallbackKey, $locale);
	}

	function formatClockTime(value) {
		if (!value) return lt('later today', 'আজ পরে');
		return new Date(value).toLocaleTimeString($locale === 'bn' ? 'bn-BD' : 'en-US', {
			hour: 'numeric',
			minute: '2-digit'
		});
	}

	function formatDuration(seconds) {
		const totalSeconds = Math.max(0, Number(seconds) || 0);
		const minutes = Math.floor(totalSeconds / 60);
		const remainingSeconds = totalSeconds % 60;
		if ($locale === 'bn') {
			if (minutes <= 0) return `${n(remainingSeconds)} সেকেন্ড`;
			if (remainingSeconds === 0) return `${n(minutes)} মিনিট`;
			return `${n(minutes)} মিনিট ${n(remainingSeconds)} সেকেন্ড`;
		}
		if (minutes <= 0) return `${remainingSeconds} sec`;
		if (remainingSeconds === 0) return `${minutes} min`;
		return `${minutes} min ${remainingSeconds} sec`;
	}

	function getCurrentSessionStorageKey() {
		if (!browser || !currentUser || !trainingPlan) return null;
		const sessionOrdinal = (trainingPlan.total_sessions || 0) + 1;
		return `${SESSION_CONTEXT_PREFIX}:${currentUser.id}:${trainingPlan.id}:${sessionOrdinal}`;
	}

	function getStoredSessionContextValue() {
		const storageKey = getCurrentSessionStorageKey();
		if (!storageKey) return null;
		return localStorage.getItem(storageKey);
	}

	function setStoredSessionContextValue(value) {
		const storageKey = getCurrentSessionStorageKey();
		if (!storageKey) return;
		localStorage.setItem(storageKey, value);
	}

	function getStoredSessionContextId() {
		const storedValue = getStoredSessionContextValue();
		if (!storedValue || storedValue === 'skip') return null;

		const contextId = Number.parseInt(storedValue, 10);
		return Number.isInteger(contextId) && contextId > 0 ? contextId : null;
	}

	function launchTask(route, contextId = null) {
		if (!route) return;

		const activeContextId = contextId ?? getStoredSessionContextId();
		const separator = route.includes('?') ? '&' : '?';
		const finalRoute = activeContextId ? `${route}${separator}contextId=${encodeURIComponent(activeContextId)}` : route;
		goto(finalRoute);
	}

	function startTask(task) {
		if (task.completed) return;

		const sessionPacing = trainingPlan?.session_pacing;
		const sessionAlreadyStarted = !!sessionPacing?.current_session_in_progress || (nextTasks?.completed_tasks || 0) > 0;

		if (!sessionAlreadyStarted && sessionPacing?.remaining_sessions_today === 0) {
			pacingWarning = {
				type: 'limit',
				title: lt('Daily training limit reached', 'আজকের ট্রেনিং সীমা পূর্ণ হয়েছে'),
				message: lt(
					`You have already completed ${trainingPlan?.session_constraints?.max_sessions_per_day || 3} sessions today. Take a longer rest and come back tomorrow.`,
					`আপনি আজ ইতিমধ্যে ${n(trainingPlan?.session_constraints?.max_sessions_per_day || 3)}টি সেশন শেষ করেছেন। একটু বেশি বিশ্রাম নিন এবং আগামীকাল আবার আসুন।`
				),
				guidance: lt(
					'Use this time for recovery, hydration, and low-effort activities before your next training day.',
					'পরের ট্রেনিং দিনের আগে এই সময়টা বিশ্রাম, পানি পান এবং হালকা কাজের জন্য ব্যবহার করুন।'
				)
			};
			return;
		}

		if (!sessionAlreadyStarted && sessionPacing?.cooldown_active) {
			pacingWarning = {
				type: 'cooldown',
				title: lt('Cooldown still active', 'বিরতির সময় এখনো চলছে'),
				message: lt(
					`Please wait ${formatDuration(sessionPacing.cooldown_remaining_seconds)} before starting another session.`,
					`আরেকটি সেশন শুরু করার আগে ${formatDuration(sessionPacing.cooldown_remaining_seconds)} অপেক্ষা করুন।`
				),
				guidance: lt(
					`Your next session window opens around ${formatClockTime(sessionPacing.next_session_available_at)}. Stretch, rest your eyes, and return when the cooldown ends.`,
					`আপনার পরের সেশনের সময় আনুমানিক ${formatClockTime(sessionPacing.next_session_available_at)}-এ শুরু হবে। একটু স্ট্রেচ করুন, চোখকে বিশ্রাম দিন, তারপর আবার ফিরে আসুন।`
				)
			};
			return;
		}

		pacingWarning = null;

		pendingTaskRoute = buildTrainingTaskUrl({
			taskCode: task.task_type,
			planId: trainingPlan.id,
			difficulty: task.difficulty,
			taskId: task.task_id
		});
		const hasHandledQuestionnaire = !!getStoredSessionContextValue();

		if (hasHandledQuestionnaire || sessionAlreadyStarted) {
			launchTask(pendingTaskRoute);
			pendingTaskRoute = null;
			return;
		}

		showPreTaskQuestionnaire = true;
	}

	function handleQuestionnaireComplete(event) {
		const contextId = event.detail?.contextId;
		if (contextId) {
			setStoredSessionContextValue(String(contextId));
		}
		showPreTaskQuestionnaire = false;
		launchTask(pendingTaskRoute, contextId);
		pendingTaskRoute = null;
	}

	function handleQuestionnaireSkip() {
		setStoredSessionContextValue('skip');
		showPreTaskQuestionnaire = false;
		launchTask(pendingTaskRoute);
		pendingTaskRoute = null;
	}

	function backToDashboard() {
		goto('/dashboard');
	}

	function formatDate(dateValue) {
		return dateValue
			? new Date(dateValue).toLocaleDateString($locale === 'bn' ? 'bn-BD' : 'en-US')
			: lt('Not yet', 'এখনও নয়');
	}

	function getSummaryValue(key) {
		if (key === 'total') return metrics?.total_sessions ?? trainingPlan?.total_sessions ?? 0;
		if (key === 'completed') return trainingPlan?.total_sessions ?? Math.max((nextTasks?.session_number || 1) - 1, 0);
		return formatDate(metrics?.last_training_date);
	}

	function getTasksByPriority(priority) {
		return nextTasks?.tasks?.filter((task) => task.priority === priority) || [];
	}

	$: summaryCards = [
		{ key: 'total', label: lt('Total Sessions', 'মোট সেশন') },
		{ key: 'completed', label: lt('Sessions Completed', 'সম্পন্ন সেশন') },
		{ key: 'last', label: lt('Last Training', 'সর্বশেষ ট্রেনিং') }
	];
	$: primaryTasks = getTasksByPriority('primary');
	$: secondaryTasks = getTasksByPriority('secondary');
	$: maintenanceTasks = getTasksByPriority('maintenance');
	$: sessionConstraints = trainingPlan?.session_constraints || null;
	$: sessionPacing = trainingPlan?.session_pacing || null;
	$: pacingBanner = !sessionPacing
		? null
		: sessionPacing.current_session_in_progress
			? {
				kind: 'info',
				title: lt('Session in progress', 'সেশন চলছে'),
				message: lt(
					`You have ${nextTasks?.completed_tasks || 0} of ${nextTasks?.total_tasks || sessionConstraints?.tasks_per_session || 4} tasks done in this session. Finish the remaining tasks whenever you are ready.`,
					`এই সেশনে আপনি ${n(nextTasks?.completed_tasks || 0)}টি কাজ শেষ করেছেন, মোট ${n(nextTasks?.total_tasks || sessionConstraints?.tasks_per_session || 4)}টির মধ্যে। প্রস্তুত হলে বাকি কাজগুলো শেষ করুন।`
				)
			}
			: sessionPacing.remaining_sessions_today === 0
				? {
					kind: 'warning',
					title: lt('Daily limit reached', 'আজকের সীমা পূর্ণ হয়েছে'),
					message: lt(
						`You have completed ${sessionConstraints?.max_sessions_per_day || 3} sessions today. NeuroBloom is holding the next session until tomorrow to protect recovery.`,
						`আপনি আজ ${n(sessionConstraints?.max_sessions_per_day || 3)}টি সেশন সম্পন্ন করেছেন। পুনরুদ্ধারের স্বার্থে NeuroBloom আগামীকাল পর্যন্ত পরের সেশনটি আটকে রাখছে।`
					)
				}
				: sessionPacing.cooldown_active
					? {
						kind: 'warning',
						title: lt('Cooldown in effect', 'বিরতি চলছে'),
						message: lt(
							`Your next session becomes available in ${formatDuration(sessionPacing.cooldown_remaining_seconds)}.`,
							`আপনার পরের সেশন ${formatDuration(sessionPacing.cooldown_remaining_seconds)} পরে পাওয়া যাবে।`
						)
					}
					: null;
</script>

<div class="training-shell">
	{#if showPreTaskQuestionnaire}
		<PreTaskQuestionnaire
			showQuestionnaire={showPreTaskQuestionnaire}
			on:complete={handleQuestionnaireComplete}
			on:skip={handleQuestionnaireSkip}
		/>
	{/if}

	{#if newlyEarnedBadges.length > 0}
		<BadgeNotification badges={newlyEarnedBadges} />
	{/if}

	<div class="training-layout">
		{#if loading}
			<section class="state-card">
				<p>{lt('Loading your training plan...', 'আপনার ট্রেনিং পরিকল্পনা লোড হচ্ছে...')}</p>
			</section>
		{:else if trainingState === 'baseline_incomplete'}
			<section class="state-card error-card">
				<h3>{lt('Baseline still in progress', 'বেসলাইন এখনো চলছে')}</h3>
				<p>{lt('Complete your six baseline tasks first. Training becomes available only after the baseline is complete.', 'আগে আপনার ছয়টি বেসলাইন টাস্ক সম্পন্ন করুন। বেসলাইন সম্পূর্ণ না হওয়া পর্যন্ত ট্রেনিং চালু হবে না।')}</p>
				<button class="primary-btn" on:click={() => goto('/baseline')}>{lt('Open Baseline', 'বেসলাইন খুলুন')}</button>
			</section>
		{:else if trainingState === 'baseline_ready_to_calculate'}
			<section class="state-card error-card">
				<h3>{lt('Baseline ready to calculate', 'বেসলাইন ক্যালকুলেটের জন্য প্রস্তুত')}</h3>
				<p>{lt('You have finished the six baseline tasks. Calculate the baseline first, then generate the training plan.', 'আপনি ছয়টি বেসলাইন টাস্ক শেষ করেছেন। আগে বেসলাইন ক্যালকুলেট করুন, তারপর ট্রেনিং প্ল্যান তৈরি করুন।')}</p>
				<button class="primary-btn" on:click={() => goto('/baseline')}>{lt('Go to Baseline Workspace', 'বেসলাইন ওয়ার্কস্পেসে যান')}</button>
			</section>
		{:else if trainingState === 'plan_missing'}
			<section class="state-card error-card">
				<h3>{lt('Training plan not generated yet', 'ট্রেনিং প্ল্যান এখনো তৈরি হয়নি')}</h3>
				<p>{lt('Your baseline is calculated, but you still need to generate the training plan before daily tasks can start.', 'আপনার বেসলাইন ক্যালকুলেট হয়েছে, কিন্তু দৈনিক টাস্ক শুরুর আগে ট্রেনিং প্ল্যান তৈরি করতে হবে।')}</p>
				<button class="primary-btn" on:click={() => goto('/baseline/results')}>{lt('Open Baseline Results', 'বেসলাইন রেজাল্ট খুলুন')}</button>
			</section>
		{:else if trainingState === 'system_not_ready'}
			<section class="state-card error-card">
				<h3>{lt('Training system not ready', 'ট্রেনিং সিস্টেম প্রস্তুত নয়')}</h3>
				<p>{journey?.blocking_reason || lt('The task catalog is missing, so today’s training session cannot be assembled yet.', 'টাস্ক ক্যাটালগ নেই, তাই আজকের ট্রেনিং সেশন তৈরি করা যাচ্ছে না।')}</p>
				<button class="primary-btn" on:click={loadTrainingData}>{lt('Retry', 'পুনরায় চেষ্টা করুন')}</button>
			</section>
		{:else if error}
			<section class="state-card error-card">
				<h3>{lt('Training workspace unavailable', 'ট্রেনিং ওয়ার্কস্পেস পাওয়া যাচ্ছে না')}</h3>
				<p>{error}</p>
				<button class="primary-btn" on:click={loadTrainingData}>{lt('Retry', 'পুনরায় চেষ্টা করুন')}</button>
			</section>
		{:else if trainingPlan && nextTasks}
			<header class="training-header glass-panel">
				<div class="header-copy">
					<p class="eyebrow">NeuroBloom</p>
					<h1>{lt('Your Training Plan', 'আপনার ট্রেনিং পরিকল্পনা')}</h1>
					<p class="header-subcopy">{lt("A lightweight view of today's session, recommended tasks, and your current focus areas.", 'আজকের সেশন, প্রস্তাবিত কাজ এবং আপনার বর্তমান ফোকাস এলাকা সহজভাবে দেখুন।')}</p>
				</div>
				<div class="header-actions">
					<button class="ghost-btn" on:click={loadTrainingData} disabled={loading}>
						{#if loading}{lt('Refreshing...', 'রিফ্রেশ হচ্ছে...')}{:else}{lt('Refresh', 'রিফ্রেশ')}{/if}
					</button>
					<button class="secondary-btn" on:click={backToDashboard}>{lt('Back to Dashboard', 'ড্যাশবোর্ডে ফিরে যান')}</button>
				</div>

				<div class="summary-strip">
					{#each summaryCards as card}
						<div class="summary-item">
							<p class="summary-label">{card.label}</p>
							<p class="summary-value">{getSummaryValue(card.key)}</p>
						</div>
					{/each}
				</div>
			</header>

			{#if pacingBanner || pacingWarning}
				<section class="section-panel glass-panel pacing-panel {(pacingWarning?.type || pacingBanner?.kind) === 'warning' || (pacingWarning?.type || pacingBanner?.kind) === 'limit' || (pacingWarning?.type || pacingBanner?.kind) === 'cooldown' ? 'warning' : 'info'}">
					<p class="section-kicker">{lt('Session Guidance', 'সেশন নির্দেশনা')}</p>
					<h2>{pacingWarning?.title || pacingBanner?.title}</h2>
					<p class="section-note">{pacingWarning?.message || pacingBanner?.message}</p>
					{#if pacingWarning?.guidance}
						<p class="guidance-copy">{pacingWarning.guidance}</p>
					{:else if sessionConstraints}
						<p class="guidance-copy">{lt(`Recommended pace: up to ${sessionConstraints.max_sessions_per_day} sessions per day, ${sessionConstraints.recommended_sessions_per_week} sessions per week, ${sessionConstraints.recommended_session_length_minutes.min}-${sessionConstraints.recommended_session_length_minutes.max} minutes each, with a ${sessionConstraints.cooldown_between_sessions_minutes}-minute cooldown.`, `প্রস্তাবিত গতি: দিনে সর্বোচ্চ ${n(sessionConstraints.max_sessions_per_day)}টি সেশন, সপ্তাহে ${n(sessionConstraints.recommended_sessions_per_week)}টি সেশন, প্রতিটি ${n(sessionConstraints.recommended_session_length_minutes.min)}-${n(sessionConstraints.recommended_session_length_minutes.max)} মিনিট, এবং সেশনগুলোর মাঝে ${n(sessionConstraints.cooldown_between_sessions_minutes)} মিনিট বিরতি।`)}</p>
					{/if}
				</section>
			{/if}

			<section class="section-panel glass-panel">
				<div class="section-head">
					<div>
						<p class="section-kicker">{lt("Today's Session", 'আজকের সেশন')}</p>
						<h2>{lt(`Session ${nextTasks.session_number}`, `সেশন ${n(nextTasks.session_number)}`)}</h2>
					</div>
					<div class="session-progress">
						<p class="progress-label">{lt(`${nextTasks.completed_tasks} of ${nextTasks.total_tasks} tasks completed`, `${n(nextTasks.completed_tasks)} / ${n(nextTasks.total_tasks)}টি কাজ সম্পন্ন`)}</p>
						<div class="progress-track">
							<div class="progress-fill" style="width: {(nextTasks.completed_tasks / nextTasks.total_tasks) * 100}%"></div>
						</div>
					</div>
				</div>

				{#if nextTasks.session_complete}
					<button class="session-complete-banner" on:click={() => goto(`/session-summary?session=${trainingPlan.total_sessions}`)}>
						<div>
							<p class="complete-kicker">{lt('Session complete', 'সেশন সম্পন্ন')}</p>
							<h3>{lt('All recommended tasks are done.', 'সব প্রস্তাবিত কাজ শেষ হয়েছে।')}</h3>
							<p>{lt('Open your session summary to review progress and next steps.', 'আপনার অগ্রগতি ও পরের ধাপ দেখতে সেশন সারাংশ খুলুন।')}</p>
						</div>
						<span>{lt('View Summary', 'সারাংশ দেখুন')}</span>
					</button>
				{:else}
					<p class="section-note">{lt('Your session is designed to stay focused and compact. Complete the recommended tasks below in any order.', 'আপনার সেশনটি সংক্ষিপ্ত ও মনোযোগী রাখার জন্য সাজানো হয়েছে। নিচের কাজগুলো যেকোনো ক্রমে সম্পন্ন করুন।')}</p>
				{/if}
			</section>

			<section class="section-panel glass-panel">
				<div class="section-head">
					<div>
						<p class="section-kicker">{lt('Recommended Tasks', 'প্রস্তাবিত কাজ')}</p>
						<h2>{lt("Today's actionable tasks", 'আজকের করণীয় কাজ')}</h2>
					</div>
				</div>

				<div class="tasks-grid">
					{#each nextTasks.tasks as task}
						<article class="task-card {task.completed ? 'completed' : ''} {getPriorityTone(task.priority)}">
							<div class="task-topline">
								<p class="task-domain">{getDomainName(task.domain)}</p>
							<h3 class="task-title">{getTaskLabel(task)}</h3>
								<span class="priority-pill {getPriorityTone(task.priority)}">{getPriorityLabel(task.priority)}</span>
							</div>
							<div class="task-meta">
								<span>{getDifficultyLabel(task.difficulty)}</span>
								<span>{lt(`Level ${task.difficulty}/10`, `লেভেল ${n(task.difficulty)}/10`)}</span>
							</div>
							<p class="task-reason">{getTaskReason(task)}</p>
							<button class="primary-btn task-btn" disabled={task.completed} on:click={() => startTask(task)}>
								{task.completed ? lt('Completed', 'সম্পন্ন') : lt('Start Task', 'কাজ শুরু করুন')}
							</button>
						</article>
					{/each}
				</div>
			</section>

			<section class="section-panel glass-panel">
				<div class="section-head">
					<div>
						<p class="section-kicker">{lt('Focus Areas', 'ফোকাস এলাকা')}</p>
						<h2>{lt("How today's plan is balanced", 'আজকের পরিকল্পনা কীভাবে ভারসাম্যপূর্ণ')}</h2>
					</div>
				</div>

				<div class="focus-grid">
					<div class="focus-card primary">
						<h3>{lt('Primary Focus', 'প্রধান ফোকাস')}</h3>
						<p>{lt('Areas needing the most support right now.', 'এই মুহূর্তে যেসব এলাকায় সবচেয়ে বেশি সহায়তা দরকার।')}</p>
						<ul>
							{#each trainingPlan.primary_focus as domain}
								<li>{getDomainName(domain)}</li>
							{/each}
						</ul>
						{#if primaryTasks.length > 0}
							<div class="focus-tags">
								{#each primaryTasks as task}
									<span>{getDomainName(task.domain)}</span>
								{/each}
							</div>
						{/if}
					</div>

					<div class="focus-card secondary">
						<h3>{lt('Secondary Focus', 'দ্বিতীয় ফোকাস')}</h3>
						<p>{lt('Areas with room for steady improvement.', 'যেসব এলাকায় ধীর কিন্তু স্থির উন্নতির সুযোগ আছে।')}</p>
						<ul>
							{#each trainingPlan.secondary_focus as domain}
								<li>{getDomainName(domain)}</li>
							{/each}
						</ul>
						{#if secondaryTasks.length > 0}
							<div class="focus-tags">
								{#each secondaryTasks as task}
									<span>{getDomainName(task.domain)}</span>
								{/each}
							</div>
						{/if}
					</div>

					<div class="focus-card maintenance">
						<h3>{lt('Maintenance', 'রক্ষণাবেক্ষণ')}</h3>
						<p>{lt('Areas to keep stable while the plan adapts.', 'পরিকল্পনা বদলালেও যেসব এলাকা স্থির রাখা দরকার।')}</p>
						<ul>
							{#each trainingPlan.maintenance as domain}
								<li>{getDomainName(domain)}</li>
							{/each}
						</ul>
						{#if maintenanceTasks.length > 0}
							<div class="focus-tags">
								{#each maintenanceTasks as task}
									<span>{getDomainName(task.domain)}</span>
								{/each}
							</div>
						{/if}
					</div>
				</div>
			</section>
		{/if}
	</div>
</div>

<style>
	:global(body) {
		background: linear-gradient(135deg, #eef2ff, #e0f2fe);
	}

	.training-shell {
		min-height: 100vh;
		background:
			radial-gradient(circle at top left, rgba(79, 70, 229, 0.12), transparent 28%),
			radial-gradient(circle at right top, rgba(34, 211, 238, 0.12), transparent 24%),
			linear-gradient(135deg, #eef2ff, #e0f2fe);
		padding: 1.5rem;
		color: #1f2937;
	}

	.training-layout {
		max-width: 1180px;
		margin: 0 auto;
		display: grid;
		gap: 1rem;
	}

	.glass-panel,
	.state-card {
		background: rgba(248, 250, 252, 0.84);
		backdrop-filter: blur(10px);
		border: 1px solid rgba(255, 255, 255, 0.72);
		border-radius: 20px;
		box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
	}

	.state-card {
		padding: 2rem;
		text-align: center;
	}

	.error-card h3 {
		margin: 0 0 0.75rem;
		color: #b91c1c;
	}

	.error-card p {
		margin: 0 0 1.25rem;
		color: #6b7280;
	}

	.training-header {
		padding: 1.4rem;
		display: grid;
		grid-template-columns: 1fr auto;
		grid-template-rows: auto auto;
		gap: 1.1rem;
		align-items: start;
	}

	.header-copy h1 {
		margin: 0.2rem 0 0.4rem;
		font-size: 2rem;
		color: #111827;
	}

	.eyebrow,
	.section-kicker,
	.complete-kicker {
		margin: 0;
		font-size: 0.78rem;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		font-weight: 800;
		color: #4f46e5;
	}

	.header-subcopy {
		margin: 0;
		max-width: 680px;
		line-height: 1.55;
		color: #64748b;
	}

	.header-actions {
		display: flex;
		gap: 0.75rem;
		flex-wrap: wrap;
		justify-content: flex-end;
		grid-column: 2;
		grid-row: 1;
		align-self: start;
		padding-top: 0.1rem;
	}

	.summary-strip {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 0.9rem;
		grid-column: 1 / -1;
	}

	.summary-item {
		padding: 1rem;
		border-radius: 16px;
		background: rgba(255, 255, 255, 0.7);
		border: 1px solid rgba(255, 255, 255, 0.82);
		box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
	}

	.summary-label {
		margin: 0;
		font-size: 0.8rem;
		font-weight: 700;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: #64748b;
	}

	.summary-value {
		margin: 0.45rem 0 0;
		font-size: 1.45rem;
		font-weight: 700;
		color: #111827;
	}

	.section-panel {
		padding: 1.25rem;
		display: grid;
		gap: 1rem;
	}

	.section-head {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 1rem;
	}

	.section-head h2 {
		margin: 0.2rem 0 0;
		font-size: 1.3rem;
		color: #111827;
	}

	.session-progress {
		min-width: min(320px, 100%);
	}

	.progress-label {
		margin: 0 0 0.45rem;
		text-align: right;
		font-size: 0.9rem;
		font-weight: 700;
		color: #4f46e5;
	}

	.progress-track {
		height: 10px;
		border-radius: 999px;
		background: rgba(148, 163, 184, 0.18);
		overflow: hidden;
	}

	.progress-fill {
		height: 100%;
		background: linear-gradient(90deg, #4f46e5, #22c55e);
	}

	.section-note {
		margin: 0;
		color: #64748b;
		line-height: 1.55;
	}

	.pacing-panel.warning {
		background: linear-gradient(135deg, rgba(254, 243, 199, 0.8), rgba(255, 255, 255, 0.92));
		border-color: rgba(245, 158, 11, 0.3);
	}

	.pacing-panel.info {
		background: linear-gradient(135deg, rgba(224, 242, 254, 0.82), rgba(255, 255, 255, 0.92));
		border-color: rgba(14, 165, 233, 0.26);
	}

	.guidance-copy {
		margin: 0;
		color: #475569;
		line-height: 1.6;
		font-size: 0.94rem;
	}

	.session-complete-banner {
		border: none;
		padding: 1.1rem 1.2rem;
		border-radius: 18px;
		background: linear-gradient(135deg, rgba(34, 197, 94, 0.16), rgba(79, 70, 229, 0.14));
		border-left: 5px solid #22c55e;
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 1rem;
		text-align: left;
		cursor: pointer;
		color: #1f2937;
	}

	.session-complete-banner h3,
	.session-complete-banner p {
		margin: 0;
	}

	.session-complete-banner h3 {
		margin-top: 0.2rem;
		margin-bottom: 0.3rem;
	}

	.session-complete-banner span {
		font-weight: 700;
		color: #15803d;
		white-space: nowrap;
	}

	.tasks-grid {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 0.9rem;
	}

	.task-card {
		padding: 1rem;
		border-radius: 18px;
		background: rgba(255, 255, 255, 0.74);
		border: 1px solid rgba(255, 255, 255, 0.8);
		box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
		border-left: 5px solid #94a3b8;
		display: grid;
		gap: 0.85rem;
	}

	.task-card.primary {
		border-left-color: #4f46e5;
	}

	.task-card.secondary {
		border-left-color: #0891b2;
	}

	.task-card.maintenance {
		border-left-color: #14b8a6;
	}

	.task-card.completed {
		opacity: 0.82;
		background: rgba(236, 253, 245, 0.76);
	}

	.task-topline {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 0.75rem;
	}

	.task-domain {
		margin: 0;
		font-size: 1rem;
		font-weight: 700;
		color: #111827;
	}

	.priority-pill {
		padding: 0.35rem 0.7rem;
		border-radius: 999px;
		font-size: 0.75rem;
		font-weight: 700;
	}

	.priority-pill.primary {
		background: rgba(79, 70, 229, 0.12);
		color: #4338ca;
	}

	.priority-pill.secondary {
		background: rgba(8, 145, 178, 0.12);
		color: #0f766e;
	}

	.priority-pill.maintenance {
		background: rgba(20, 184, 166, 0.12);
		color: #0f766e;
	}

	.task-meta {
		display: flex;
		gap: 0.65rem;
		flex-wrap: wrap;
	}

	.task-meta span {
		padding: 0.35rem 0.65rem;
		border-radius: 999px;
		background: rgba(148, 163, 184, 0.12);
		color: #475569;
		font-size: 0.78rem;
		font-weight: 700;
	}

	.task-reason {
		margin: 0;
		line-height: 1.55;
		color: #64748b;
		font-size: 0.92rem;
	}

	.focus-grid {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 0.9rem;
	}

	.focus-card {
		padding: 1rem;
		border-radius: 18px;
		background: rgba(255, 255, 255, 0.72);
		border: 1px solid rgba(255, 255, 255, 0.8);
		box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
	}

	.focus-card.primary {
		box-shadow: inset 0 0 0 1px rgba(79, 70, 229, 0.06), 0 10px 24px rgba(79, 70, 229, 0.04);
	}

	.focus-card.secondary {
		box-shadow: inset 0 0 0 1px rgba(8, 145, 178, 0.06), 0 10px 24px rgba(8, 145, 178, 0.04);
	}

	.focus-card.maintenance {
		box-shadow: inset 0 0 0 1px rgba(20, 184, 166, 0.06), 0 10px 24px rgba(20, 184, 166, 0.04);
	}

	.focus-card h3 {
		margin: 0 0 0.35rem;
		font-size: 1.05rem;
		color: #111827;
	}

	.focus-card p {
		margin: 0 0 0.85rem;
		color: #64748b;
		font-size: 0.9rem;
		line-height: 1.5;
	}

	.focus-card ul {
		list-style: none;
		padding: 0;
		margin: 0;
		display: grid;
		gap: 0.55rem;
	}

	.focus-card li {
		padding: 0.6rem 0.75rem;
		border-radius: 12px;
		background: rgba(248, 250, 252, 0.86);
		color: #1f2937;
		font-weight: 600;
	}

	.focus-tags {
		margin-top: 0.9rem;
		display: flex;
		gap: 0.45rem;
		flex-wrap: wrap;
	}

	.focus-tags span {
		padding: 0.35rem 0.65rem;
		border-radius: 999px;
		background: rgba(79, 70, 229, 0.1);
		color: #4338ca;
		font-size: 0.76rem;
		font-weight: 700;
	}

	.ghost-btn,
	.primary-btn,
	.secondary-btn {
		border: none;
		border-radius: 999px;
		padding: 0.8rem 1.15rem;
		font-weight: 700;
		cursor: pointer;
		transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
	}

	.ghost-btn {
		background: rgba(248, 250, 252, 0.7);
		border: 1px solid rgba(255, 255, 255, 0.8);
		color: #374151;
	}

	.secondary-btn {
		background: rgba(255, 255, 255, 0.7);
		border: 1px solid rgba(99, 102, 241, 0.18);
		color: #4f46e5;
	}

	.primary-btn {
		background: linear-gradient(135deg, #4f46e5, #6366f1);
		color: #ffffff;
		box-shadow: 0 10px 24px rgba(79, 70, 229, 0.18);
	}

	.task-btn {
		width: 100%;
	}

	.primary-btn:disabled {
		background: linear-gradient(135deg, #22c55e, #16a34a);
		cursor: not-allowed;
		box-shadow: none;
	}

	.ghost-btn:hover:not(:disabled),
	.primary-btn:hover:not(:disabled),
	.secondary-btn:hover:not(:disabled) {
		transform: translateY(-1px);
	}

	.ghost-btn:disabled {
		opacity: 0.7;
		cursor: not-allowed;
	}

	@media (max-width: 960px) {
		.training-shell {
			padding: 1rem;
		}

		.header-actions,
		.section-head {
			flex-direction: column;
			align-items: stretch;
		}

		.progress-label {
			text-align: left;
		}

		.summary-strip,
		.tasks-grid,
		.focus-grid {
			grid-template-columns: 1fr;
		}
	}

	@media (max-width: 640px) {
		.training-header,
		.section-panel,
		.state-card {
			padding: 1rem;
		}

		.header-copy h1 {
			font-size: 1.65rem;
		}

		.session-complete-banner {
			flex-direction: column;
			align-items: flex-start;
		}

		.ghost-btn,
		.primary-btn,
		.secondary-btn {
			width: 100%;
		}
	}
</style>

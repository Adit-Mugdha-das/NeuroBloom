<script>
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { training } from '$lib/api';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import PreTaskQuestionnaire from '$lib/components/PreTaskQuestionnaire.svelte';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let currentUser = null;
	let loading = true;
	let trainingPlan = null;
	let nextTasks = null;
	let metrics = null;
	let error = null;
	let newlyEarnedBadges = [];
	let showPreTaskQuestionnaire = false;
	let pendingTaskRoute = null;
	let pacingWarning = null;
	const SESSION_CONTEXT_PREFIX = 'training-session-context';

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

		try {
			trainingPlan = await training.getPlan(currentUser.id);
			nextTasks = await training.getNextTasks(currentUser.id);

			try {
				metrics = await training.getMetrics(currentUser.id);
			} catch (loadMetricsError) {
				metrics = null;
			}
		} catch (loadError) {
			console.error('Error loading training data:', loadError);
			error = 'No training plan found. Please generate one from your baseline results.';
		} finally {
			loading = false;
		}
	}

	function getDomainName(domain) {
		const names = {
			working_memory: 'Working Memory',
			attention: 'Attention',
			flexibility: 'Cognitive Flexibility',
			planning: 'Planning',
			processing_speed: 'Processing Speed',
			visual_scanning: 'Visual Scanning'
		};

		return names[domain] || domain;
	}

	function getTaskRoute(taskType, domain, difficulty, planId, taskId) {
		const routes = {
			n_back: '/baseline/tasks/working-memory',
			dual_n_back: '/training/dual-n-back',
			digit_span: '/training/digit-span',
			spatial_span: '/training/spatial-span',
			letter_number_sequencing: '/training/letter-number-sequencing',
			operation_span: '/training/operation-span',
			simple_reaction: '/baseline/tasks/processing-speed',
			reaction_time: '/baseline/tasks/processing-speed',
			sdmt: '/training/sdmt',
			trails_a: '/training/trail-making-a',
			trail_making_a: '/training/trail-making-a',
			pattern_comparison: '/training/pattern-comparison',
			inspection_time: '/training/inspection-time',
			continuous_performance: '/baseline/tasks/attention',
			cpt: '/baseline/tasks/attention',
			pasat: '/training/pasat',
			stroop: '/training/stroop',
			go_nogo: '/training/gonogo',
			trail_making_b: '/training/trail-making-b',
			wcst: '/training/wcst',
			dccs: '/training/dccs',
			plus_minus: '/training/plus-minus',
			tower_of_hanoi: '/baseline/tasks/planning',
			tower_of_london: '/baseline/tasks/planning',
			stockings_cambridge: '/training/stockings-of-cambridge',
			verbal_fluency: '/training/verbal-fluency',
			category_fluency: '/training/category-fluency',
			twenty_questions: '/training/twenty-questions',
			target_search: '/baseline/tasks/visual-scanning',
			visual_search: '/training/visual-search',
			cancellation: '/training/cancellation-test',
			cancellation_test: '/training/cancellation-test',
			feature_conjunction: '/training/visual-search',
			mot: '/training/multiple-object-tracking',
			multiple_object_tracking: '/training/multiple-object-tracking',
			ufov: '/training/useful-field-of-view',
			useful_field_of_view: '/training/useful-field-of-view'
		};

		const baseRoute = routes[taskType] || '/dashboard';
		return `${baseRoute}?training=true&planId=${planId}&difficulty=${difficulty}&taskId=${encodeURIComponent(taskId)}`;
	}

	function getPriorityLabel(priority) {
		if (priority === 'primary') return 'Primary Focus';
		if (priority === 'secondary') return 'Secondary Focus';
		return 'Maintenance';
	}

	function getPriorityTone(priority) {
		if (priority === 'primary') return 'primary';
		if (priority === 'secondary') return 'secondary';
		return 'maintenance';
	}

	function getDifficultyLabel(difficulty) {
		if (difficulty <= 3) return 'Gentle';
		if (difficulty <= 6) return 'Steady';
		if (difficulty <= 8) return 'Focused';
		return 'Advanced';
	}

	function formatClockTime(value) {
		if (!value) return 'later today';
		return new Date(value).toLocaleTimeString([], {
			hour: 'numeric',
			minute: '2-digit'
		});
	}

	function formatDuration(seconds) {
		const totalSeconds = Math.max(0, Number(seconds) || 0);
		const minutes = Math.floor(totalSeconds / 60);
		const remainingSeconds = totalSeconds % 60;
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
				title: 'Daily training limit reached',
				message: `You have already completed ${trainingPlan?.session_constraints?.max_sessions_per_day || 3} sessions today. Take a longer rest and come back tomorrow.`,
				guidance: 'Use this time for recovery, hydration, and low-effort activities before your next training day.'
			};
			return;
		}

		if (!sessionAlreadyStarted && sessionPacing?.cooldown_active) {
			pacingWarning = {
				type: 'cooldown',
				title: 'Cooldown still active',
				message: `Please wait ${formatDuration(sessionPacing.cooldown_remaining_seconds)} before starting another session.`,
				guidance: `Your next session window opens around ${formatClockTime(sessionPacing.next_session_available_at)}. Stretch, rest your eyes, and return when the cooldown ends.`
			};
			return;
		}

		pacingWarning = null;

		pendingTaskRoute = getTaskRoute(task.task_type, task.domain, task.difficulty, trainingPlan.id, task.task_id);
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
		return dateValue ? new Date(dateValue).toLocaleDateString() : 'Not yet';
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
		{ key: 'total', label: 'Total Sessions' },
		{ key: 'completed', label: 'Sessions Completed' },
		{ key: 'last', label: 'Last Training' }
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
				title: 'Session in progress',
				message: `You have ${nextTasks?.completed_tasks || 0} of ${nextTasks?.total_tasks || sessionConstraints?.tasks_per_session || 4} tasks done in this session. Finish the remaining tasks whenever you are ready.`
			}
			: sessionPacing.remaining_sessions_today === 0
				? {
					kind: 'warning',
					title: 'Daily limit reached',
					message: `You have completed ${sessionConstraints?.max_sessions_per_day || 3} sessions today. NeuroBloom is holding the next session until tomorrow to protect recovery.`
				}
				: sessionPacing.cooldown_active
					? {
						kind: 'warning',
						title: 'Cooldown in effect',
						message: `Your next session becomes available in ${formatDuration(sessionPacing.cooldown_remaining_seconds)}.`
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
				<p>Loading your training plan...</p>
			</section>
		{:else if error}
			<section class="state-card error-card">
				<h3>Training plan unavailable</h3>
				<p>{error}</p>
				<button class="primary-btn" on:click={() => goto('/baseline/results')}>Go to Baseline Results</button>
			</section>
		{:else if trainingPlan && nextTasks}
			<header class="training-header glass-panel">
				<div class="header-copy">
					<p class="eyebrow">NeuroBloom</p>
					<h1>Your Training Plan</h1>
					<p class="header-subcopy">A lightweight view of today’s session, recommended tasks, and your current focus areas.</p>
				</div>
				<div class="header-actions">
					<button class="ghost-btn" on:click={loadTrainingData} disabled={loading}>
						{#if loading}Refreshing...{:else}Refresh{/if}
					</button>
					<button class="secondary-btn" on:click={backToDashboard}>Back to Dashboard</button>
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
					<p class="section-kicker">Session Guidance</p>
					<h2>{pacingWarning?.title || pacingBanner?.title}</h2>
					<p class="section-note">{pacingWarning?.message || pacingBanner?.message}</p>
					{#if pacingWarning?.guidance}
						<p class="guidance-copy">{pacingWarning.guidance}</p>
					{:else if sessionConstraints}
						<p class="guidance-copy">Recommended pace: up to {sessionConstraints.max_sessions_per_day} sessions per day, {sessionConstraints.recommended_sessions_per_week} sessions per week, {sessionConstraints.recommended_session_length_minutes.min}-{sessionConstraints.recommended_session_length_minutes.max} minutes each, with a {sessionConstraints.cooldown_between_sessions_minutes}-minute cooldown.</p>
					{/if}
				</section>
			{/if}

			<section class="section-panel glass-panel">
				<div class="section-head">
					<div>
						<p class="section-kicker">Today's Session</p>
						<h2>Session {nextTasks.session_number}</h2>
					</div>
					<div class="session-progress">
						<p class="progress-label">{nextTasks.completed_tasks} of {nextTasks.total_tasks} tasks completed</p>
						<div class="progress-track">
							<div class="progress-fill" style="width: {(nextTasks.completed_tasks / nextTasks.total_tasks) * 100}%"></div>
						</div>
					</div>
				</div>

				{#if nextTasks.session_complete}
					<button class="session-complete-banner" on:click={() => goto(`/session-summary?session=${trainingPlan.total_sessions}`)}>
						<div>
							<p class="complete-kicker">Session complete</p>
							<h3>All recommended tasks are done.</h3>
							<p>Open your session summary to review progress and next steps.</p>
						</div>
						<span>View Summary</span>
					</button>
				{:else}
					<p class="section-note">Your session is designed to stay focused and compact. Complete the recommended tasks below in any order.</p>
				{/if}
			</section>

			<section class="section-panel glass-panel">
				<div class="section-head">
					<div>
						<p class="section-kicker">Recommended Tasks</p>
						<h2>Today’s actionable tasks</h2>
					</div>
				</div>

				<div class="tasks-grid">
					{#each nextTasks.tasks as task}
						<article class="task-card {task.completed ? 'completed' : ''} {getPriorityTone(task.priority)}">
							<div class="task-topline">
								<p class="task-domain">{getDomainName(task.domain)}</p>
								<span class="priority-pill {getPriorityTone(task.priority)}">{getPriorityLabel(task.priority)}</span>
							</div>
							<div class="task-meta">
								<span>{getDifficultyLabel(task.difficulty)}</span>
								<span>Level {task.difficulty}/10</span>
							</div>
							<p class="task-reason">{task.focus_reason}</p>
							<button class="primary-btn task-btn" disabled={task.completed} on:click={() => startTask(task)}>
								{task.completed ? 'Completed' : 'Start Task'}
							</button>
						</article>
					{/each}
				</div>
			</section>

			<section class="section-panel glass-panel">
				<div class="section-head">
					<div>
						<p class="section-kicker">Focus Areas</p>
						<h2>How today’s plan is balanced</h2>
					</div>
				</div>

				<div class="focus-grid">
					<div class="focus-card primary">
						<h3>Primary Focus</h3>
						<p>Areas needing the most support right now.</p>
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
						<h3>Secondary Focus</h3>
						<p>Areas with room for steady improvement.</p>
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
						<h3>Maintenance</h3>
						<p>Areas to keep stable while the plan adapts.</p>
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
		gap: 1.1rem;
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
	}

	.summary-strip {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 0.9rem;
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

<script>
	import { goto } from '$app/navigation';
	import { tasks, training } from '$lib/api';
	import api from '$lib/api.js';
	import DoctorWidget from '$lib/components/DoctorWidget.svelte';
	import { clearUser, user } from '$lib/stores';
	import { onMount } from 'svelte';

	let currentUser = null;
	let stats = null;
	let baselineStatus = null;
	let streak = null;
	let nextTasks = null;
	let notifications = [];
	let unreadCount = 0;
	let loading = true;
	let pollHandle = null;
	let toastTimer = null;
	let notificationToast = null;
	let latestNotificationFingerprint = null;
	let notificationsHydrated = false;

	const modules = [
		{
			key: 'working_memory',
			title: 'Working Memory',
			description: 'Strengthen short-term memory and recall.',
			route: '/baseline/tasks/working-memory'
		},
		{
			key: 'attention',
			title: 'Attention',
			description: 'Improve focus and sustained concentration.',
			route: '/baseline/tasks/attention'
		},
		{
			key: 'flexibility',
			title: 'Cognitive Flexibility',
			description: 'Practice adapting to changing rules.',
			route: '/baseline/tasks/flexibility'
		},
		{
			key: 'planning',
			title: 'Planning',
			description: 'Build strategy and problem-solving skills.',
			route: '/baseline/tasks/planning'
		},
		{
			key: 'processing_speed',
			title: 'Processing Speed',
			description: 'Work on speed and response efficiency.',
			route: '/baseline/tasks/processing-speed'
		},
		{
			key: 'visual_scanning',
			title: 'Visual Scanning',
			description: 'Train quick visual search and detection.',
			route: '/baseline/tasks/visual-scanning'
		}
	];

	const unsubscribe = user.subscribe((value) => {
		currentUser = value;
	});

	onMount(() => {
		if (!currentUser) {
			goto('/login');
			return unsubscribe;
		}

		initializeDashboard();

		pollHandle = window.setInterval(() => {
			loadNotifications();
		}, 45000);

		return () => {
			if (pollHandle) window.clearInterval(pollHandle);
			if (toastTimer) window.clearTimeout(toastTimer);
			unsubscribe();
		};
	});

	async function initializeDashboard() {
		loading = true;

		try {
			const baselineResp = await tasks.getBaselineStatus(currentUser.id);
			baselineStatus = baselineResp;
			await loadNotifications();

			try {
				stats = await training.getMetrics(currentUser.id);
			} catch (error) {
				stats = {
					total_sessions: 0,
					total_tasks: 0,
					metrics_by_domain: {},
					last_training_date: null
				};
			}

			try {
				streak = await training.getStreak(currentUser.id);
			} catch (error) {
				streak = {
					current_streak: 0,
					longest_streak: 0
				};
			}

			try {
				nextTasks = await training.getNextTasks(currentUser.id);
			} catch (error) {
				nextTasks = null;
			}
		} catch (error) {
			console.error('Error fetching dashboard data:', error);
		} finally {
			loading = false;
		}
	}

	async function loadNotifications() {
		if (!currentUser) return;

		try {
			const response = await api.get(`/api/auth/patient/${currentUser.id}/notifications`);
			syncNotifications(response.data.notifications || []);
		} catch (error) {
			console.error('Error fetching notifications:', error);
		}
	}

	function syncNotifications(nextNotifications) {
		const newestNotification = nextNotifications[0] ?? null;
		const nextFingerprint = newestNotification
			? `${newestNotification.id}:${newestNotification.created_at}`
			: null;

		if (notificationsHydrated && nextFingerprint && nextFingerprint !== latestNotificationFingerprint) {
			showNotificationToast(newestNotification);
		}

		notifications = nextNotifications;
		latestNotificationFingerprint = nextFingerprint;
		notificationsHydrated = true;
		updateUnreadCount();
	}

	function showNotificationToast(notification) {
		if (!notification) return;

		notificationToast = {
			title: notification.title,
			message: notification.message
		};

		if (toastTimer) window.clearTimeout(toastTimer);
		toastTimer = window.setTimeout(() => {
			notificationToast = null;
			toastTimer = null;
		}, 4200);
	}

	function notificationSeenKey() {
		return currentUser ? `patient-notifications-seen-${currentUser.id}` : 'patient-notifications-seen';
	}

	function updateUnreadCount() {
		if (typeof localStorage === 'undefined') {
			unreadCount = 0;
			return;
		}

		const lastSeen = localStorage.getItem(notificationSeenKey());
		const lastSeenTime = lastSeen ? new Date(lastSeen).getTime() : 0;
		unreadCount = notifications.filter((notification) => new Date(notification.created_at).getTime() > lastSeenTime).length;
	}

	function handleLogout() {
		if (pollHandle) window.clearInterval(pollHandle);
		if (toastTimer) window.clearTimeout(toastTimer);
		clearUser();
		goto('/login');
	}

	function formatDate(dateValue) {
		return dateValue ? new Date(dateValue).toLocaleDateString() : 'Not yet';
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

		return names[domain] || 'Training';
	}

	function getDifficultyLabel(difficulty) {
		if (!difficulty) return 'Gentle';
		if (difficulty <= 3) return 'Gentle';
		if (difficulty <= 6) return 'Steady';
		if (difficulty <= 8) return 'Focused';
		return 'Advanced';
	}

	function getPrimaryRecommendation() {
		if (!nextTasks?.tasks?.length) return null;
		return nextTasks.tasks.find((task) => !task.completed) || nextTasks.tasks[0];
	}

	function moduleProgress(moduleKey) {
		return Boolean(baselineStatus?.tasks?.[moduleKey]);
	}

	function getEncouragementMessage() {
		if (primaryRecommendation?.domain) {
			return `Great progress! You're improving your ${getDomainName(primaryRecommendation.domain).toLowerCase()} this week.`;
		}

		if ((streak?.current_streak || 0) > 0) {
			return `Great progress! You've stayed consistent for ${streak.current_streak} day${streak.current_streak === 1 ? '' : 's'}.`;
		}

		return 'Great progress! Each training session helps build a clearer picture of your cognitive health.';
	}

	$: primaryRecommendation = getPrimaryRecommendation();
	$: overviewCards = [
		{ key: 'sessions', label: 'Total Sessions', value: stats?.total_sessions || 0, tone: 'indigo' },
		{ key: 'domains', label: 'Active Domains', value: stats?.metrics_by_domain ? Object.keys(stats.metrics_by_domain).length : 0, tone: 'cyan' },
		{ key: 'last-training', label: 'Last Training', value: formatDate(stats?.last_training_date), tone: 'violet' },
		{ key: 'streak', label: 'Current Streak', value: `${streak?.current_streak || 0} day${(streak?.current_streak || 0) === 1 ? '' : 's'}`, tone: 'teal' }
	];
	$: encouragementMessage = getEncouragementMessage();
</script>

<div class="dashboard-shell">
	{#if notificationToast}
		<div class="toast-shell" role="status" aria-live="polite">
			<div class="notification-toast">
				<p class="toast-label">New notification</p>
				<p class="toast-title">{notificationToast.title}</p>
				<p class="toast-message">{notificationToast.message}</p>
			</div>
		</div>
	{/if}

	<header class="topbar">
		<div class="brand-block">
			<p class="eyebrow">NeuroBloom</p>
			<h1>Your Brain Health Today</h1>
			<p class="subcopy">A calm view of your training progress, next step, and care support.</p>
		</div>
		<div class="topbar-actions">
			{#if currentUser}
				<span class="user-email">{currentUser.email}</span>
				<button class="ghost-btn" on:click={() => goto('/notifications')}>
					Notifications
					{#if unreadCount > 0}
						<span class="notification-badge">{unreadCount > 9 ? '9+' : unreadCount}</span>
					{/if}
				</button>
				<button class="ghost-btn" on:click={() => goto('/messages')}>Messages</button>
				<button class="ghost-btn" on:click={() => goto('/settings')}>Settings</button>
			{/if}
			<button class="logout-btn" on:click={handleLogout}>Logout</button>
		</div>
	</header>

	<main class="dashboard-main">
		{#if loading}
			<section class="loading-panel">
				<p>Loading your dashboard...</p>
			</section>
		{:else}
			<section class="section hero-section">
				<div class="section-head">
					<div>
						<p class="section-kicker">Brain Health Overview</p>
						<h2>Today at a glance</h2>
					</div>
					{#if baselineStatus}
						<div class="baseline-pill">
							Baseline: {baselineStatus.completed_count}/{baselineStatus.total_tasks}
						</div>
					{/if}
				</div>

				<div class="overview-grid">
					{#each overviewCards as card}
						<article class="overview-card {card.tone}">
							<div class="card-topline">
								<div class="card-icon" aria-hidden="true">
									{#if card.key === 'sessions'}
										<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
											<path d="M12 5C8.5 5 5.5 7.2 4.2 10.4C5.5 13.6 8.5 15.8 12 15.8C15.5 15.8 18.5 13.6 19.8 10.4C18.5 7.2 15.5 5 12 5Z" />
											<path d="M9.2 14.8C8.4 16 8 17.3 8 18.7V20" />
											<path d="M14.8 14.8C15.6 16 16 17.3 16 18.7V20" />
											<circle cx="12" cy="10.4" r="2.1" />
										</svg>
									{:else if card.key === 'domains'}
										<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
											<circle cx="6" cy="12" r="2.2" />
											<circle cx="18" cy="6" r="2.2" />
											<circle cx="18" cy="18" r="2.2" />
											<path d="M8 11L15.8 7.2" />
											<path d="M8 13L15.8 16.8" />
										</svg>
									{:else if card.key === 'last-training'}
										<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
											<rect x="3.5" y="5" width="17" height="15" rx="3" />
											<path d="M8 3.8V7" />
											<path d="M16 3.8V7" />
											<path d="M3.5 9.5H20.5" />
										</svg>
									{:else}
										<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
											<path d="M13.8 2.5C10 6 16.5 7.1 14.1 11.1C12.6 13.5 9.5 13.3 8.5 16.1C7.8 18 9.1 20.3 11.7 21.5C9.3 17.1 15.4 16.7 17.2 12.9C18.5 10.1 17.2 5.7 13.8 2.5Z" />
										</svg>
									{/if}
								</div>
								<p class="card-label">{card.label}</p>
							</div>
							<p class="card-value">{card.value}</p>
						</article>
					{/each}
				</div>

				<div class="encouragement-banner">
					<div class="encouragement-icon" aria-hidden="true">
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
							<path d="M12 21C16.4 21 20 17.4 20 13V5L12 3L4 5V13C4 17.4 7.6 21 12 21Z" />
							<path d="M9.2 12.6L11.2 14.6L15.4 10.4" />
						</svg>
					</div>
					<p>{encouragementMessage}</p>
				</div>

				{#if baselineStatus}
					<div class="baseline-track-row">
						<div class="baseline-track-copy">
							<p class="track-title">Baseline assessment progress</p>
							<p class="track-text">Complete all six modules to unlock your personalised plan.</p>
						</div>
						<div class="baseline-track-wrap">
							<div class="baseline-track">
								<div class="baseline-track-fill" style="width: {(baselineStatus.completed_count / baselineStatus.total_tasks) * 100}%"></div>
							</div>
						</div>
					</div>
				{/if}
			</section>

			<section class="section recommendation-section">
				<div class="section-head">
					<div>
						<p class="section-kicker">Today's Recommendation</p>
						<h2>Your next best step</h2>
					</div>
				</div>

				{#if primaryRecommendation}
					<div class="recommendation-card">
						<div class="recommendation-copy">
							<p class="recommendation-domain">{getDomainName(primaryRecommendation.domain)}</p>
							<h3>{primaryRecommendation.task_name || 'Recommended training task'}</h3>
							<p class="recommendation-reason">{primaryRecommendation.focus_reason}</p>
							<div class="recommendation-meta">
								<span class="meta-chip">{getDifficultyLabel(primaryRecommendation.difficulty)} challenge</span>
								<span class="meta-chip">Level {primaryRecommendation.difficulty}/10</span>
							</div>
						</div>
						<div class="recommendation-actions">
							<button class="primary-btn" on:click={() => goto('/training')}>Open Training Plan</button>
							<button class="secondary-btn" on:click={() => goto('/progress')}>View Progress</button>
						</div>
					</div>
				{:else}
					<div class="recommendation-card empty">
						<div class="recommendation-copy">
							<p class="recommendation-domain">Getting started</p>
							<h3>Finish your baseline to unlock recommendations</h3>
							<p class="recommendation-reason">Once baseline assessment is complete, NeuroBloom will suggest the best next training focus for you.</p>
						</div>
						<div class="recommendation-actions">
							<button class="primary-btn" on:click={() => goto('/baseline/results')}>Review Baseline</button>
						</div>
					</div>
				{/if}
			</section>

			<section class="section modules-section">
				<div class="section-head modules-head">
					<div>
						<p class="section-kicker">Training Modules</p>
						<h2>Six key cognitive areas</h2>
					</div>
					<div class="section-actions">
						{#if baselineStatus?.all_completed}
							<a class="inline-link" href="/training">Training Plan</a>
							<a class="inline-link" href="/progress">Progress</a>
						{:else}
							<a class="inline-link" href="/baseline/results">Baseline Status</a>
						{/if}
					</div>
				</div>

				<div class="modules-grid">
					{#each modules as module}
						<a class="module-card" href={module.route}>
							<div class="module-topline">
								<p class="module-title">{module.title}</p>
								{#if moduleProgress(module.key)}
									<span class="status-chip complete">Done</span>
								{:else}
									<span class="status-chip pending">Start</span>
								{/if}
							</div>
							<p class="module-description">{module.description}</p>
						</a>
					{/each}
				</div>
			</section>

			<section class="section care-team-section">
				<details class="care-team-details">
					<summary>
						<div>
							<p class="section-kicker">Healthcare Provider</p>
							<h2>Your Care Team</h2>
						</div>
						<span class="summary-hint">Expand when needed</span>
					</summary>
					<div class="care-team-body">
						{#if currentUser}
							<DoctorWidget userId={currentUser.id} />
						{/if}
					</div>
				</details>
			</section>
		{/if}
	</main>
</div>

<style>
	:global(body) {
		background: linear-gradient(135deg, #eef2ff, #e0f2fe);
	}

	.dashboard-shell {
		min-height: 100vh;
		position: relative;
		background:
			radial-gradient(circle at top left, rgba(79, 70, 229, 0.12), transparent 28%),
			radial-gradient(circle at top right, rgba(6, 182, 212, 0.14), transparent 24%),
			linear-gradient(135deg, #eef2ff, #e0f2fe);
		color: #1f2937;
		overflow: hidden;
	}

	.dashboard-shell::before,
	.dashboard-shell::after {
		content: '';
		position: absolute;
		border-radius: 999px;
		filter: blur(50px);
		pointer-events: none;
	}

	.dashboard-shell::before {
		width: 18rem;
		height: 18rem;
		top: 4rem;
		right: -4rem;
		background: rgba(79, 70, 229, 0.14);
	}

	.dashboard-shell::after {
		width: 14rem;
		height: 14rem;
		left: -3rem;
		bottom: 3rem;
		background: rgba(34, 211, 238, 0.12);
	}

	.toast-shell {
		position: fixed;
		top: 1rem;
		right: 1rem;
		z-index: 1000;
	}

	.notification-toast {
		max-width: 340px;
		background: rgba(248, 250, 252, 0.9);
		backdrop-filter: blur(12px);
		border: 1px solid rgba(255, 255, 255, 0.7);
		border-left: 4px solid #4f46e5;
		border-radius: 14px;
		padding: 0.9rem 1rem;
		box-shadow: 0 18px 45px rgba(15, 23, 42, 0.12);
	}

	.toast-label {
		margin: 0;
		font-size: 0.72rem;
		font-weight: 800;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #4f46e5;
	}

	.toast-title {
		margin: 0.3rem 0 0;
		font-size: 0.95rem;
		font-weight: 700;
		color: #111827;
	}

	.toast-message {
		margin: 0.35rem 0 0;
		font-size: 0.84rem;
		line-height: 1.5;
		color: #4b5563;
	}

	.topbar {
		max-width: 1180px;
		margin: 0 auto;
		padding: 1.35rem 1.5rem 0;
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 1.25rem;
		position: relative;
		z-index: 1;
	}

	.brand-block h1 {
		margin: 0.15rem 0 0.4rem;
		font-size: 2rem;
		font-weight: 700;
		color: #111827;
	}

	.eyebrow,
	.section-kicker {
		margin: 0;
		font-size: 0.78rem;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		font-weight: 800;
		color: #4f46e5;
	}

	.subcopy {
		margin: 0;
		max-width: 560px;
		color: #6b7280;
		line-height: 1.55;
	}

	.topbar-actions {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		flex-wrap: wrap;
		justify-content: flex-end;
	}

	.user-email {
		font-size: 0.85rem;
		color: #6b7280;
	}

	.ghost-btn,
	.logout-btn,
	.primary-btn,
	.secondary-btn {
		border: none;
		border-radius: 999px;
		padding: 0.78rem 1.05rem;
		font-weight: 700;
		cursor: pointer;
		transition: background 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
	}

	.ghost-btn {
		position: relative;
		background: rgba(248, 250, 252, 0.72);
		backdrop-filter: blur(10px);
		color: #374151;
		border: 1px solid rgba(255, 255, 255, 0.6);
		box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
	}

	.logout-btn {
		background: linear-gradient(135deg, #1f2937, #111827);
		color: #ffffff;
		box-shadow: 0 12px 24px rgba(17, 24, 39, 0.15);
	}

	.primary-btn {
		background: linear-gradient(135deg, #4f46e5, #6366f1);
		color: #ffffff;
		box-shadow: 0 12px 28px rgba(79, 70, 229, 0.22);
	}

	.secondary-btn {
		background: rgba(248, 250, 252, 0.72);
		backdrop-filter: blur(10px);
		color: #4f46e5;
		border: 1px solid rgba(99, 102, 241, 0.18);
		box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
	}

	.ghost-btn:hover,
	.logout-btn:hover,
	.primary-btn:hover,
	.secondary-btn:hover {
		transform: translateY(-1px);
	}

	.notification-badge {
		margin-left: 0.5rem;
		min-width: 1.2rem;
		height: 1.2rem;
		padding: 0 0.35rem;
		border-radius: 999px;
		background: #ef4444;
		color: #ffffff;
		font-size: 0.72rem;
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}

	.dashboard-main {
		max-width: 1180px;
		margin: 0 auto;
		padding: 1rem 1.5rem 1.75rem;
		display: grid;
		gap: 1rem;
		position: relative;
		z-index: 1;
	}

	.section,
	.loading-panel {
		background: rgba(248, 250, 252, 0.85);
		backdrop-filter: blur(10px);
		border: 1px solid rgba(255, 255, 255, 0.68);
		border-radius: 22px;
		padding: 1.25rem;
		box-shadow: 0 12px 32px rgba(15, 23, 42, 0.06);
	}

	.loading-panel {
		text-align: center;
		color: #6b7280;
	}

	.section-head {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 1rem;
		margin-bottom: 1rem;
	}

	.section-head h2 {
		margin: 0.15rem 0 0;
		font-size: 1.25rem;
		color: #111827;
	}

	.baseline-pill {
		padding: 0.5rem 0.8rem;
		border-radius: 999px;
		background: rgba(79, 70, 229, 0.12);
		color: #4338ca;
		font-size: 0.82rem;
		font-weight: 700;
	}

	.overview-grid {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 0.9rem;
	}

	.overview-card {
		background: rgba(255, 255, 255, 0.72);
		backdrop-filter: blur(10px);
		border: 1px solid rgba(255, 255, 255, 0.78);
		border-radius: 18px;
		padding: 1rem;
		box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
		position: relative;
		overflow: hidden;
	}

	.overview-card::before {
		content: '';
		position: absolute;
		inset: 0;
		opacity: 0.8;
		background: linear-gradient(135deg, rgba(255, 255, 255, 0.35), transparent 65%);
		pointer-events: none;
	}

	.overview-card.indigo {
		box-shadow: inset 0 0 0 1px rgba(99, 102, 241, 0.06), 0 12px 30px rgba(79, 70, 229, 0.08);
	}

	.overview-card.cyan {
		box-shadow: inset 0 0 0 1px rgba(34, 211, 238, 0.08), 0 12px 30px rgba(34, 211, 238, 0.08);
	}

	.overview-card.violet {
		box-shadow: inset 0 0 0 1px rgba(139, 92, 246, 0.08), 0 12px 30px rgba(139, 92, 246, 0.08);
	}

	.overview-card.teal {
		box-shadow: inset 0 0 0 1px rgba(20, 184, 166, 0.08), 0 12px 30px rgba(20, 184, 166, 0.08);
	}

	.card-topline {
		display: flex;
		align-items: center;
		gap: 0.8rem;
		position: relative;
		z-index: 1;
	}

	.card-icon {
		width: 2.75rem;
		height: 2.75rem;
		border-radius: 14px;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		color: #4f46e5;
		background: linear-gradient(135deg, rgba(79, 70, 229, 0.14), rgba(34, 211, 238, 0.12));
		box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.6);
	}

	.overview-card.cyan .card-icon {
		color: #0891b2;
		background: linear-gradient(135deg, rgba(34, 211, 238, 0.16), rgba(14, 165, 233, 0.1));
	}

	.overview-card.violet .card-icon {
		color: #7c3aed;
		background: linear-gradient(135deg, rgba(139, 92, 246, 0.16), rgba(99, 102, 241, 0.1));
	}

	.overview-card.teal .card-icon {
		color: #0f766e;
		background: linear-gradient(135deg, rgba(20, 184, 166, 0.16), rgba(34, 211, 238, 0.1));
	}

	.card-icon svg {
		width: 1.3rem;
		height: 1.3rem;
	}

	.card-label {
		margin: 0;
		font-size: 0.78rem;
		font-weight: 700;
		color: #6b7280;
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}

	.card-value {
		margin: 0.45rem 0 0;
		font-size: 1.45rem;
		font-weight: 700;
		color: #111827;
		position: relative;
		z-index: 1;
	}

	.encouragement-banner {
		margin-top: 0.9rem;
		display: flex;
		align-items: center;
		gap: 0.85rem;
		padding: 0.9rem 1rem;
		background: linear-gradient(135deg, rgba(79, 70, 229, 0.09), rgba(34, 211, 238, 0.09));
		border: 1px solid rgba(255, 255, 255, 0.68);
		border-radius: 16px;
		box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.55);
	}

	.encouragement-banner p {
		margin: 0;
		font-size: 0.95rem;
		font-weight: 600;
		line-height: 1.55;
		color: #334155;
	}

	.encouragement-icon {
		width: 2.4rem;
		height: 2.4rem;
		border-radius: 12px;
		flex-shrink: 0;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		color: #4f46e5;
		background: rgba(255, 255, 255, 0.65);
		box-shadow: 0 8px 22px rgba(79, 70, 229, 0.1);
	}

	.encouragement-icon svg {
		width: 1.15rem;
		height: 1.15rem;
	}

	.baseline-track-row {
		margin-top: 1rem;
		display: grid;
		grid-template-columns: minmax(220px, 1fr) 1.4fr;
		gap: 1rem;
		align-items: center;
	}

	.track-title {
		margin: 0;
		font-size: 0.92rem;
		font-weight: 700;
		color: #1f2937;
	}

	.track-text {
		margin: 0.25rem 0 0;
		font-size: 0.88rem;
		color: #6b7280;
	}

	.baseline-track {
		height: 10px;
		background: rgba(148, 163, 184, 0.18);
		border-radius: 999px;
		overflow: hidden;
	}

	.baseline-track-fill {
		height: 100%;
		background: linear-gradient(90deg, #4f46e5 0%, #22c55e 100%);
	}

	.recommendation-card {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 1rem;
		padding: 1rem;
		border-radius: 18px;
		background: rgba(255, 255, 255, 0.76);
		backdrop-filter: blur(10px);
		border: 1px solid rgba(255, 255, 255, 0.75);
		border-left: 5px solid #4f46e5;
		box-shadow: 0 10px 30px rgba(79, 70, 229, 0.08);
	}

	.recommendation-card.empty {
		background: rgba(248, 250, 252, 0.8);
	}

	.recommendation-domain {
		margin: 0;
		font-size: 0.8rem;
		font-weight: 800;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #4f46e5;
	}

	.recommendation-copy h3 {
		margin: 0.3rem 0;
		font-size: 1.2rem;
		color: #111827;
	}

	.recommendation-reason {
		margin: 0;
		max-width: 600px;
		line-height: 1.55;
		color: #6b7280;
	}

	.recommendation-meta {
		margin-top: 0.9rem;
		display: flex;
		gap: 0.6rem;
		flex-wrap: wrap;
	}

	.meta-chip,
	.status-chip {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 0.42rem 0.7rem;
		border-radius: 999px;
		font-size: 0.76rem;
		font-weight: 700;
	}

	.meta-chip {
		background: rgba(79, 70, 229, 0.12);
		color: #4338ca;
	}

	.recommendation-actions {
		display: flex;
		gap: 0.75rem;
		flex-wrap: wrap;
		justify-content: flex-end;
	}

	.modules-head {
		align-items: center;
	}

	.section-actions {
		display: flex;
		gap: 0.9rem;
		flex-wrap: wrap;
	}

	.inline-link {
		color: #4f46e5;
		text-decoration: none;
		font-weight: 700;
	}

	.modules-grid {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 0.9rem;
	}

	.module-card {
		text-decoration: none;
		color: inherit;
		background: rgba(248, 250, 252, 0.78);
		backdrop-filter: blur(10px);
		border: 1px solid rgba(255, 255, 255, 0.68);
		border-radius: 18px;
		padding: 1rem;
		transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease, background 0.2s ease;
		box-shadow: 0 10px 26px rgba(15, 23, 42, 0.04);
	}

	.module-card:hover {
		border-color: rgba(99, 102, 241, 0.28);
		background: rgba(255, 255, 255, 0.82);
		box-shadow: 0 12px 28px rgba(79, 70, 229, 0.08);
		transform: translateY(-1px);
	}

	.module-topline {
		display: flex;
		justify-content: space-between;
		gap: 0.75rem;
		align-items: flex-start;
	}

	.module-title {
		margin: 0;
		font-size: 1rem;
		font-weight: 700;
		color: #111827;
	}

	.module-description {
		margin: 0.55rem 0 0;
		font-size: 0.88rem;
		line-height: 1.55;
		color: #6b7280;
	}

	.status-chip.complete {
		background: rgba(34, 197, 94, 0.14);
		color: #15803d;
	}

	.status-chip.pending {
		background: rgba(148, 163, 184, 0.14);
		color: #6b7280;
	}

	.care-team-details {
		background: rgba(248, 250, 252, 0.78);
		backdrop-filter: blur(10px);
		border: 1px solid rgba(255, 255, 255, 0.68);
		border-radius: 18px;
		overflow: hidden;
		box-shadow: 0 10px 26px rgba(15, 23, 42, 0.04);
	}

	.care-team-details summary {
		list-style: none;
		cursor: pointer;
		padding: 1rem 1.1rem;
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 1rem;
	}

	.care-team-details summary::-webkit-details-marker {
		display: none;
	}

	.summary-hint {
		font-size: 0.84rem;
		font-weight: 700;
		color: #6b7280;
	}

	.care-team-body {
		padding: 0 1rem 1rem;
	}

	@media (max-width: 960px) {
		.topbar,
		.dashboard-main {
			padding-left: 1rem;
			padding-right: 1rem;
		}

		.overview-grid,
		.modules-grid {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}

		.recommendation-card,
		.topbar {
			flex-direction: column;
			align-items: stretch;
		}

		.baseline-track-row {
			grid-template-columns: 1fr;
		}

		.recommendation-actions,
		.topbar-actions {
			justify-content: flex-start;
		}
	}

	@media (max-width: 640px) {
		.overview-grid,
		.modules-grid {
			grid-template-columns: 1fr;
		}

		.encouragement-banner {
			align-items: flex-start;
		}

		.section,
		.loading-panel {
			padding: 1rem;
		}

		.brand-block h1 {
			font-size: 1.6rem;
		}

		.recommendation-actions {
			flex-direction: column;
		}

		.primary-btn,
		.secondary-btn,
		.ghost-btn,
		.logout-btn {
			width: 100%;
		}
	}
</style>


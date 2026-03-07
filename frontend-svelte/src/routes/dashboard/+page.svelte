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
	let notifications = [];
	let unreadCount = 0;
	let loading = true;
	let pollHandle = null;
	let toastTimer = null;
	let notificationToast = null;
	let latestNotificationFingerprint = null;
	let notificationsHydrated = false;
	
	const unsubscribe = user.subscribe(value => {
		currentUser = value;
	});
	
	onMount(() => {
		if (!currentUser) {
			goto('/login');
			return unsubscribe;
		}

		async function initializeDashboard() {
			try {
				const baselineResp = await tasks.getBaselineStatus(currentUser.id);
				baselineStatus = baselineResp;
				await loadNotifications();

				try {
					stats = await training.getMetrics(currentUser.id);
				} catch (err) {
					console.log('No training data yet');
					stats = {
						total_sessions: 0,
						average_score: 0,
						best_score: 0
					};
				}
			} catch (error) {
				console.error('Error fetching dashboard data:', error);
			} finally {
				loading = false;
			}
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
</script>

<div class="dashboard">
	{#if notificationToast}
		<div class="toast-shell" role="status" aria-live="polite">
			<div class="notification-toast">
				<div class="toast-accent"></div>
				<div class="toast-content">
					<p class="toast-label">New notification</p>
					<p class="toast-title">{notificationToast.title}</p>
					<p class="toast-message">{notificationToast.message}</p>
				</div>
			</div>
		</div>
	{/if}

	<header class="header">
		<h1>🧠 NeuroBloom</h1>
		<div class="header-right">
			{#if currentUser}
				<span class="user-email">{currentUser.email}</span>
				<button class="btn-notifications" on:click={() => goto('/notifications')}>
					<span>🔔 Notification Center</span>
					{#if unreadCount > 0}
						<span class="notification-badge">{unreadCount > 9 ? '9+' : unreadCount}</span>
					{/if}
				</button>
				<button class="btn-messages" on:click={() => goto('/messages')}>💬 Messages</button>
				<button class="btn-settings" on:click={() => goto('/settings')}>⚙️ Settings</button>
			{/if}
			<button class="btn-logout" on:click={handleLogout}>Logout</button>
		</div>
	</header>
	
	<div class="container">
		<h2 style="margin: 30px 0 20px; color: #333;">Your Dashboard</h2>
		
		{#if loading}
			<p>Loading...</p>
		{:else}
			<!-- Doctor Widget -->
			{#if currentUser}
				<DoctorWidget userId={currentUser.id} />
			{/if}
			
			<div class="stats-grid">
				<div class="stat-card">
					<h3>Total Sessions</h3>
					<div class="value">{stats?.total_sessions || 0}</div>
				</div>
				<div class="stat-card">
					<h3>Active Domains</h3>
					<div class="value">{stats?.metrics_by_domain ? Object.keys(stats.metrics_by_domain).length : 0}</div>
				</div>
				<div class="stat-card">
					<h3>Last Training</h3>
					<div class="value last-training">
						{#if stats?.last_training_date}
							{new Date(stats.last_training_date).toLocaleDateString()}
						{:else}
							Never
						{/if}
					</div>
				</div>
				<div class="stat-card">
					<h3>Total Tasks</h3>
					<div class="value">{stats?.total_tasks || 0}</div>
				</div>
			</div>
			
			<h3 style="margin: 40px 0 20px; color: #333;">Cognitive Training Modules</h3>
			
			{#if baselineStatus}
				<div class="baseline-progress">
					<div class="progress-header">
						<div class="progress-info">
							<div class="progress-bar">
								<div 
									class="progress-fill" 
									style="width: {(baselineStatus.completed_count / baselineStatus.total_tasks) * 100}%"
								></div>
							</div>
							<p class="progress-text">
								{baselineStatus.completed_count} of {baselineStatus.total_tasks} baseline tasks completed
							</p>
						</div>
						{#if baselineStatus.all_completed}
							<div class="action-buttons">
								<a href="/baseline/results" class="btn-baseline">
									View Baseline
								</a>
								<a href="/training" class="btn-training">
									Training Plan
								</a>
								<a href="/progress" class="btn-progress">
									Progress
								</a>
							</div>
						{/if}
					</div>
				</div>
			{/if}
			
			<div class="modules-grid">
				<a href="/baseline/tasks/working-memory" style="text-decoration: none;">
					<div class="module-card {baselineStatus?.tasks?.working_memory ? 'completed' : ''}">
						<div class="icon">🧩</div>
						<h3>Working Memory</h3>
						<p>N-Back Test • Challenge your short-term memory</p>
						{#if baselineStatus?.tasks?.working_memory}
							<div class="completion-badge">✓</div>
						{/if}
					</div>
				</a>
				
				<a href="/baseline/tasks/attention" style="text-decoration: none;">
					<div class="module-card {baselineStatus?.tasks?.attention ? 'completed' : ''}">
						<div class="icon">👁️</div>
						<h3>Attention</h3>
						<p>CPT Test • Sustained attention & vigilance</p>
						{#if baselineStatus?.tasks?.attention}
							<div class="completion-badge">✓</div>
						{/if}
					</div>
				</a>
				
				<a href="/baseline/tasks/flexibility" style="text-decoration: none;">
					<div class="module-card {baselineStatus?.tasks?.flexibility ? 'completed' : ''}">
						<div class="icon">🔄</div>
						<h3>Cognitive Flexibility</h3>
						<p>Task Switching • Adapt to changing rules</p>
						{#if baselineStatus?.tasks?.flexibility}
							<div class="completion-badge">✓</div>
						{/if}
					</div>
				</a>
				
				<a href="/baseline/tasks/planning" style="text-decoration: none;">
					<div class="module-card {baselineStatus?.tasks?.planning ? 'completed' : ''}">
						<div class="icon">🎯</div>
						<h3>Planning</h3>
						<p>Tower of Hanoi • Strategic problem solving</p>
						{#if baselineStatus?.tasks?.planning}
							<div class="completion-badge">✓</div>
						{/if}
					</div>
				</a>
				
				<a href="/baseline/tasks/processing-speed" style="text-decoration: none;">
					<div class="module-card {baselineStatus?.tasks?.processing_speed ? 'completed' : ''}">
						<div class="icon">⚡</div>
						<h3>Processing Speed</h3>
						<p>Reaction Time • Simple & choice responses</p>
						{#if baselineStatus?.tasks?.processing_speed}
							<div class="completion-badge">✓</div>
						{/if}
					</div>
				</a>
				
				<a href="/baseline/tasks/visual-scanning" style="text-decoration: none;">
					<div class="module-card {baselineStatus?.tasks?.visual_scanning ? 'completed' : ''}">
						<div class="icon">🔍</div>
						<h3>Visual Scanning</h3>
						<p>Visual Search • Find targets in grid</p>
						{#if baselineStatus?.tasks?.visual_scanning}
							<div class="completion-badge">✓</div>
						{/if}
					</div>
				</a>
			</div>
		{/if}
	</div>
</div>

<style>
	.dashboard {
		min-height: 100vh;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
	}

	.toast-shell {
		position: fixed;
		top: 1.35rem;
		right: 1.35rem;
		z-index: 1100;
		pointer-events: none;
	}

	.notification-toast {
		display: grid;
		grid-template-columns: 5px 1fr;
		min-width: 320px;
		max-width: 380px;
		background: rgba(255, 255, 255, 0.96);
		border-radius: 18px;
		overflow: hidden;
		box-shadow: 0 18px 45px rgba(31, 41, 55, 0.22);
		border: 1px solid rgba(255, 255, 255, 0.85);
		animation: slide-toast-in 0.26s ease-out;
	}

	.toast-accent {
		background: linear-gradient(180deg, #0f766e 0%, #14b8a6 100%);
	}

	.toast-content {
		padding: 0.9rem 1rem;
	}

	.toast-label {
		margin: 0;
		font-size: 0.72rem;
		font-weight: 800;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #0f766e;
	}

	.toast-title {
		margin: 0.3rem 0 0;
		font-size: 0.95rem;
		font-weight: 800;
		color: #111827;
	}

	.toast-message {
		margin: 0.35rem 0 0;
		font-size: 0.84rem;
		line-height: 1.5;
		color: #4b5563;
		max-height: 2.5rem;
		overflow: hidden;
	}

	@keyframes slide-toast-in {
		from {
			opacity: 0;
			transform: translateY(-12px) scale(0.98);
		}
		to {
			opacity: 1;
			transform: translateY(0) scale(1);
		}
	}
	
	.header {
		background: white;
		padding: 1rem 2rem;
		display: flex;
		justify-content: space-between;
		align-items: center;
		box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
	}
	
	.header h1 {
		margin: 0;
		color: #667eea;
	}
	
	.header-right {
		display: flex;
		align-items: center;
		gap: 1rem;
	}
	
	.user-email {
		color: #666;
		font-size: 0.9rem;
	}
	
	.btn-messages {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		padding: 0.5rem 1.5rem;
		border-radius: 8px;
		cursor: pointer;
		font-weight: 600;
		transition: transform 0.2s;
	}
	
	.btn-messages:hover {
		transform: translateY(-2px);
	}

	.btn-notifications {
		position: relative;
		background: linear-gradient(135deg, #0f766e 0%, #155e75 100%);
		color: white;
		border: none;
		padding: 0.5rem 1.1rem;
		border-radius: 999px;
		cursor: pointer;
		font-weight: 700;
		display: inline-flex;
		align-items: center;
		gap: 0.55rem;
		transition: transform 0.2s, box-shadow 0.2s;
		box-shadow: 0 10px 24px rgba(15, 118, 110, 0.25);
	}

	.btn-notifications:hover {
		transform: translateY(-2px);
		box-shadow: 0 14px 28px rgba(15, 118, 110, 0.3);
	}

	.notification-badge {
		position: absolute;
		top: -0.35rem;
		right: -0.35rem;
		min-width: 1.25rem;
		height: 1.25rem;
		padding: 0 0.35rem;
		border-radius: 999px;
		background: #dc2626;
		color: white;
		font-size: 0.72rem;
		font-weight: 800;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 4px 12px rgba(220, 38, 38, 0.4);
		border: 2px solid white;
	}
	
	.btn-logout {
		background: #dc3545;
		color: white;
		border: none;
		padding: 0.5rem 1.5rem;
		border-radius: 8px;
		cursor: pointer;
		font-weight: 600;
		transition: background 0.3s;
	}
	
	.btn-logout:hover {
		background: #c82333;
	}
	
	.btn-settings {
		background: #667eea;
		color: white;
		border: none;
		padding: 0.5rem 1rem;
		border-radius: 5px;
		cursor: pointer;
		font-weight: 600;
		transition: background 0.3s;
	}
	
	.btn-settings:hover {
		background: #5568d3;
	}
	
	.container {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem;
	}
	
	.stats-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1.5rem;
		margin-bottom: 2rem;
	}
	
	.stat-card {
		background: white;
		padding: 1.5rem;
		border-radius: 12px;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
	}
	
	.stat-card h3 {
		margin: 0 0 0.5rem 0;
		color: #666;
		font-size: 0.9rem;
		font-weight: 600;
	}
	
	.stat-card .value {
		font-size: 2rem;
		font-weight: bold;
		color: #667eea;
	}
	
	.stat-card .value.last-training {
		font-size: 1.2rem;
	}
	
	.baseline-progress {
		background: white;
		padding: 1.5rem;
		border-radius: 12px;
		margin-bottom: 1.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
	}
	
	.progress-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 2rem;
	}
	
	.progress-info {
		flex: 1;
	}
	
	.progress-bar {
		width: 100%;
		height: 12px;
		background: #e0e0e0;
		border-radius: 6px;
		overflow: hidden;
		margin-bottom: 0.5rem;
	}
	
	.progress-fill {
		height: 100%;
		background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
		transition: width 0.5s ease;
	}
	
	.progress-text {
		margin: 0;
		color: #666;
		font-size: 0.9rem;
	}
	
	.btn-baseline {
		background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
		color: white;
		border: none;
		padding: 1rem 2rem;
		border-radius: 12px;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		text-decoration: none;
		display: inline-block;
		transition: all 0.3s;
		white-space: nowrap;
		box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
	}
	
	.btn-baseline:hover {
		transform: translateY(-2px);
		box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
	}
	
	.action-buttons {
		display: flex;
		gap: 1rem;
		flex-wrap: wrap;
	}
	
	.btn-training, .btn-progress {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		padding: 1rem 2rem;
		border-radius: 12px;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		text-decoration: none;
		display: inline-block;
		transition: all 0.3s;
		white-space: nowrap;
		box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
	}
	
	.btn-training:hover, .btn-progress:hover {
		transform: translateY(-2px);
		box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
	}
	
	.modules-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		gap: 1.5rem;
	}
	
	.module-card {
		position: relative;
		background: white;
		padding: 2rem;
		border-radius: 12px;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
		transition: all 0.3s;
		cursor: pointer;
	}
	
	.module-card:hover {
		transform: translateY(-5px);
		box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
	}
	
	.module-card.completed {
		background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
		border: 2px solid #667eea;
	}
	
	.module-card .icon {
		font-size: 3rem;
		margin-bottom: 1rem;
	}
	
	.module-card h3 {
		margin: 0.5rem 0;
		color: #333;
	}
	
	.module-card p {
		margin: 0.5rem 0 0 0;
		color: #666;
		font-size: 0.9rem;
	}
	
	.completion-badge {
		position: absolute;
		top: 1rem;
		right: 1rem;
		width: 40px;
		height: 40px;
		background: #28a745;
		color: white;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.5rem;
		font-weight: bold;
		box-shadow: 0 2px 8px rgba(40, 167, 69, 0.3);
	}

	@media (max-width: 900px) {
		.toast-shell {
			top: auto;
			bottom: 1rem;
			left: 1rem;
			right: 1rem;
		}

		.notification-toast {
			min-width: 0;
			max-width: none;
			width: 100%;
		}

		.header {
			flex-direction: column;
			align-items: stretch;
			gap: 1rem;
		}

		.header-right,
		.progress-header {
			flex-wrap: wrap;
		}

		.btn-notifications,
		.btn-messages,
		.btn-settings,
		.btn-logout {
			justify-content: center;
		}

		.container {
			padding: 1rem;
		}

		.action-buttons {
			flex-direction: column;
		}
	}
</style>


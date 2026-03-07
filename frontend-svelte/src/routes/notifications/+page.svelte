<script>
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	import { clearUser, user } from '$lib/stores';
	import { onMount } from 'svelte';

	let currentUser = null;
	let notifications = [];
	let loading = true;
	let error = '';
	let pollHandle = null;

	const unsubscribe = user.subscribe((value) => {
		currentUser = value;
	});

	onMount(() => {
		if (!currentUser) {
			goto('/login');
			return unsubscribe;
		}

		loadNotifications();
		pollHandle = window.setInterval(() => {
			loadNotifications();
		}, 45000);

		return () => {
			if (pollHandle) window.clearInterval(pollHandle);
			unsubscribe();
		};
	});

	async function loadNotifications() {
		loading = true;
		error = '';
		try {
			const response = await api.get(`/api/auth/patient/${currentUser.id}/notifications`);
			notifications = response.data.notifications || [];
			markViewed();
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Failed to load notifications';
		} finally {
			loading = false;
		}
	}

	function notificationSeenKey() {
		return currentUser ? `patient-notifications-seen-${currentUser.id}` : 'patient-notifications-seen';
	}

	function markViewed() {
		if (typeof localStorage === 'undefined') return;
		localStorage.setItem(notificationSeenKey(), new Date().toISOString());
	}

	function handleLogout() {
		if (pollHandle) window.clearInterval(pollHandle);
		clearUser();
		goto('/login');
	}

	function formatDate(iso) {
		if (!iso) return '-';
		return new Date(iso).toLocaleString('en-GB', {
			day: '2-digit',
			month: 'short',
			year: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function typeLabel(type) {
		if (type === 'announcement') return 'Announcement';
		if (type === 'feature_update') return 'Feature Update';
		if (type === 'research_invitation') return 'Research Invitation';
		return 'Notice';
	}

	function typeClass(type) {
		if (type === 'announcement') return 'type-blue';
		if (type === 'feature_update') return 'type-teal';
		if (type === 'research_invitation') return 'type-amber';
		return 'type-blue';
	}
</script>

<div class="page-shell">
	<header class="topbar">
		<div>
			<p class="eyebrow">Patient Experience</p>
			<h1>Notification Center</h1>
			<p class="subtext">System announcements, feature updates, and research invitations from the NeuroBloom team.</p>
		</div>
		<div class="topbar-actions">
			<button class="ghost-btn" on:click={() => goto('/dashboard')}>Back to Dashboard</button>
			<button class="logout-btn" on:click={handleLogout}>Logout</button>
		</div>
	</header>

	<main class="content">
		<section class="hero-card">
			<div>
				<p class="hero-kicker">Stay Informed</p>
				<h2>Your latest platform notices in one place</h2>
				<p>Unread badges on the dashboard clear as soon as you open this page.</p>
			</div>
			<div class="hero-meta">
				<span class="meta-pill">{notifications.length} total notices</span>
			</div>
		</section>

		{#if loading}
			<div class="state-card">Loading notifications...</div>
		{:else if error}
			<div class="state-card error">{error}</div>
		{:else if notifications.length === 0}
			<div class="state-card empty">
				<h3>No notifications yet</h3>
				<p>New notices from admins will appear here automatically.</p>
			</div>
		{:else}
			<div class="notice-list">
				{#each notifications as notification (notification.id)}
					<article class="notice-card">
						<div class="notice-top">
							<div>
								<p class="notice-title">{notification.title}</p>
								<p class="notice-time">{formatDate(notification.created_at)}</p>
							</div>
							<span class="type-pill {typeClass(notification.notification_type)}">{typeLabel(notification.notification_type)}</span>
						</div>
						<p class="notice-message">{notification.message}</p>
					</article>
				{/each}
			</div>
		{/if}
	</main>
</div>

<style>
	.page-shell {
		min-height: 100vh;
		background:
			radial-gradient(circle at top left, rgba(20, 184, 166, 0.2), transparent 28%),
			linear-gradient(160deg, #f8fafc 0%, #eef2ff 52%, #ecfeff 100%);
		padding: 2rem;
		font-family: 'Inter', system-ui, sans-serif;
	}

	.topbar {
		max-width: 1100px;
		margin: 0 auto 1.5rem;
		background: rgba(255, 255, 255, 0.88);
		backdrop-filter: blur(12px);
		border: 1px solid rgba(255, 255, 255, 0.9);
		box-shadow: 0 20px 50px rgba(15, 23, 42, 0.08);
		border-radius: 24px;
		padding: 1.5rem 1.75rem;
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: flex-start;
	}

	.eyebrow, .hero-kicker {
		margin: 0 0 0.35rem;
		font-size: 0.78rem;
		text-transform: uppercase;
		letter-spacing: 0.14em;
		font-weight: 800;
		color: #0f766e;
	}

	h1, h2 {
		margin: 0;
		color: #0f172a;
	}

	.subtext {
		margin: 0.45rem 0 0;
		color: #475569;
		max-width: 620px;
		line-height: 1.6;
	}

	.topbar-actions {
		display: flex;
		gap: 0.75rem;
		flex-wrap: wrap;
	}

	.ghost-btn, .logout-btn {
		border: none;
		border-radius: 999px;
		padding: 0.8rem 1.15rem;
		font-weight: 700;
		cursor: pointer;
	}

	.ghost-btn {
		background: #e0f2fe;
		color: #0f172a;
	}

	.logout-btn {
		background: #0f172a;
		color: white;
	}

	.content {
		max-width: 1100px;
		margin: 0 auto;
	}

	.hero-card {
		background: linear-gradient(135deg, rgba(255,255,255,0.92), rgba(240,253,250,0.95));
		border: 1px solid rgba(148, 163, 184, 0.18);
		box-shadow: 0 20px 60px rgba(15, 23, 42, 0.08);
		border-radius: 24px;
		padding: 1.5rem 1.75rem;
		margin-bottom: 1.25rem;
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: center;
	}

	.hero-card p {
		margin: 0.45rem 0 0;
		color: #475569;
		line-height: 1.6;
	}

	.meta-pill, .type-pill {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 0.35rem 0.85rem;
		border-radius: 999px;
		font-size: 0.74rem;
		font-weight: 800;
	}

	.meta-pill {
		background: #ccfbf1;
		color: #115e59;
	}

	.notice-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.notice-card, .state-card {
		background: rgba(255, 255, 255, 0.94);
		border-radius: 22px;
		padding: 1.35rem 1.45rem;
		border: 1px solid rgba(226, 232, 240, 0.9);
		box-shadow: 0 16px 40px rgba(15, 23, 42, 0.08);
	}

	.state-card {
		text-align: center;
	}

	.state-card.error {
		color: #b91c1c;
		background: #fef2f2;
		border-color: #fecaca;
	}

	.notice-top {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: flex-start;
	}

	.notice-title {
		margin: 0;
		font-size: 1.02rem;
		font-weight: 800;
		color: #0f172a;
	}

	.notice-time {
		margin: 0.35rem 0 0;
		font-size: 0.8rem;
		color: #64748b;
	}

	.notice-message {
		margin: 0.85rem 0 0;
		font-size: 0.94rem;
		line-height: 1.7;
		color: #334155;
	}

	.type-blue { background: #dbeafe; color: #1d4ed8; }
	.type-teal { background: #ccfbf1; color: #0f766e; }
	.type-amber { background: #fef3c7; color: #92400e; }

	@media (max-width: 820px) {
		.page-shell {
			padding: 1rem;
		}

		.topbar,
		.hero-card,
		.notice-top {
			flex-direction: column;
		}

		.topbar-actions {
			width: 100%;
		}

		.ghost-btn,
		.logout-btn {
			flex: 1;
		}
	}
</style>
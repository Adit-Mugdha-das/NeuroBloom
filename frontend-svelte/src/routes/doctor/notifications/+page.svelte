<script>
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	import DoctorWorkspaceShell from '$lib/components/DoctorWorkspaceShell.svelte';
	import { user } from '$lib/stores.js';
	import { onMount } from 'svelte';

	let doctor = null;
	let notifications = [];
	let loading = true;
	let error = '';
	let pollHandle = null;

	const unsubscribe = user.subscribe((value) => {
		doctor = value;
	});

	onMount(() => {
		if (!doctor || doctor.role !== 'doctor') {
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
			const response = await api.get(`/api/doctor/${doctor.id}/notifications`);
			notifications = response.data.notifications || [];
			markViewed();
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Failed to load notifications';
		} finally {
			loading = false;
		}
	}

	function notificationSeenKey() {
		return doctor ? `doctor-notifications-seen-${doctor.id}` : 'doctor-notifications-seen';
	}

	function markViewed() {
		if (typeof localStorage === 'undefined') return;
		localStorage.setItem(notificationSeenKey(), new Date().toISOString());
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
</script>

<DoctorWorkspaceShell
	title="Notifications"
	subtitle="Administrative updates and research notices collected in one quiet workspace so they do not compete with the clinical dashboard."
>
	<section class="hero-card">
		<div>
			<p class="hero-kicker">Practice Updates</p>
			<h2>{notifications.length} active notices</h2>
			<p>Doctor-facing platform notices, feature updates, and invitations are stored here instead of interrupting patient review.</p>
		</div>
	</section>

	{#if loading}
		<section class="state-card"><p>Loading notifications...</p></section>
	{:else if error}
		<section class="state-card error-state"><p>{error}</p></section>
	{:else if notifications.length === 0}
		<section class="state-card">
			<h2>No notifications yet</h2>
			<p>New doctor notices will appear here automatically.</p>
		</section>
	{:else}
		<section class="notice-list">
			{#each notifications as notification (notification.id)}
				<article class="notice-card">
					<div class="notice-top">
						<div>
							<p class="notice-title">{notification.title}</p>
							<p class="notice-time">{formatDate(notification.created_at)}</p>
						</div>
						<span class="type-pill">{typeLabel(notification.notification_type)}</span>
					</div>
					<p class="notice-message">{notification.message}</p>
				</article>
			{/each}
		</section>
	{/if}
</DoctorWorkspaceShell>

<style>
	.hero-card,
	.notice-card,
	.state-card {
		background: #f8fafc;
		border: 1px solid #e2e8f0;
		border-radius: 24px;
		padding: 1.2rem;
		box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
	}

	.hero-kicker {
		margin: 0;
		font-size: 0.78rem;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: #4f46e5;
	}

	h2,
	.notice-title {
		margin: 0.2rem 0 0;
		color: #111827;
	}

	.hero-card p:last-child,
	.state-card p,
	.notice-time,
	.notice-message {
		color: #6b7280;
		line-height: 1.6;
	}

	.notice-list {
		display: grid;
		gap: 1rem;
	}

	.notice-top {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: flex-start;
	}

	.type-pill {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 0.35rem 0.8rem;
		border-radius: 999px;
		background: #eef2ff;
		color: #4f46e5;
		font-size: 0.78rem;
		font-weight: 800;
	}

	.notice-message {
		margin: 0.8rem 0 0;
	}
</style>
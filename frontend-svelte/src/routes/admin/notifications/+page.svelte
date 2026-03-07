<script>
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let admin = null;
	let loading = true;
	let sending = false;
	let error = '';
	let successMsg = '';

	let notifications = [];
	let summary = null;

	let form = {
		notification_type: 'announcement',
		audience: 'all',
		title: '',
		message: ''
	};

	const TYPE_OPTIONS = [
		{ value: 'announcement', label: 'System Announcement' },
		{ value: 'feature_update', label: 'New Feature Update' },
		{ value: 'research_invitation', label: 'Research Participation Invitation' }
	];

	const AUDIENCE_OPTIONS = [
		{ value: 'all', label: 'All Users' },
		{ value: 'patient', label: 'Patients Only' },
		{ value: 'doctor', label: 'Doctors Only' }
	];

	onMount(async () => {
		const currentUser = $user;
		if (!currentUser || currentUser.role !== 'admin') {
			goto('/login');
			return;
		}

		admin = currentUser;
		await loadNotifications();
	});

	async function loadNotifications() {
		loading = true;
		error = '';
		try {
			const response = await api.get(`/api/admin/notifications?admin_id=${admin.id}`);
			notifications = response.data.notifications;
			summary = response.data.summary;
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Failed to load notifications';
		} finally {
			loading = false;
		}
	}

	async function sendNotification() {
		if (!form.title.trim() || !form.message.trim()) {
			error = 'Title and message are required.';
			return;
		}

		sending = true;
		error = '';
		successMsg = '';
		try {
			const response = await api.post(`/api/admin/notifications?admin_id=${admin.id}`, form);
			successMsg = response.data.message;
			form = { notification_type: 'announcement', audience: 'all', title: '', message: '' };
			await loadNotifications();
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Failed to publish notification';
		} finally {
			sending = false;
		}
	}

	function logout() {
		user.set(null);
		goto('/login');
	}

	function formatDateTime(iso) {
		if (!iso) return '-';
		return new Date(iso).toLocaleString('en-GB', {
			day: '2-digit',
			month: 'short',
			year: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function relativeDate(iso) {
		if (!iso) return '';
		const days = Math.floor((Date.now() - new Date(iso).getTime()) / 86400000);
		if (days === 0) return 'Today';
		if (days === 1) return 'Yesterday';
		if (days < 7) return `${days}d ago`;
		return formatDateTime(iso);
	}

	function typeLabel(type) {
		const entry = TYPE_OPTIONS.find((option) => option.value === type);
		return entry ? entry.label : type;
	}

	function audienceLabel(audience) {
		const entry = AUDIENCE_OPTIONS.find((option) => option.value === audience);
		return entry ? entry.label : audience;
	}

	function typeClass(type) {
		if (type === 'announcement') return 'type-blue';
		if (type === 'feature_update') return 'type-teal';
		return 'type-amber';
	}
</script>

<div class="admin-layout">
	<aside class="sidebar">
		<div class="sidebar-brand">
			<span class="brand-icon">🏥</span>
			<span class="brand-name">NeuroBloom Admin</span>
		</div>
		<nav class="sidebar-nav">
			<a href="/admin/dashboard" class="nav-item"><span class="nav-icon">📊</span> Dashboard</a>
			<a href="/admin/analytics" class="nav-item"><span class="nav-icon">📈</span> System Analytics</a>
			<a href="/admin/doctors" class="nav-item"><span class="nav-icon">👨‍⚕️</span> Doctor Management</a>
			<a href="/admin/patients" class="nav-item"><span class="nav-icon">👤</span> Patient Management</a>
			<a href="/admin/departments" class="nav-item"><span class="nav-icon">🏢</span> Departments</a>
			<a href="/admin/interventions" class="nav-item"><span class="nav-icon">🩺</span> Interventions</a>
			<a href="/admin/messages" class="nav-item"><span class="nav-icon">💬</span> Message Audit</a>
			<a href="/admin/audit-logs" class="nav-item"><span class="nav-icon">📋</span> Audit Logs</a>
			<a href="/admin/system-health" class="nav-item"><span class="nav-icon">🖥️</span> System Health</a>
			<a href="/admin/notifications" class="nav-item active"><span class="nav-icon">🔔</span> Notification Center</a>
		</nav>
		<button class="logout-btn" on:click={logout}><span>🚪</span> Logout</button>
	</aside>

	<main class="main-content">
		<header class="topbar">
			<div>
				<h1 class="page-title">Notification Center</h1>
				<p class="page-sub">Publish system announcements, new feature updates, and research invitations from one professional admin surface.</p>
			</div>
			<div class="admin-info">{admin?.full_name || admin?.email}</div>
		</header>

		<div class="content">
			{#if error}
				<div class="alert error" role="alert">{error}</div>
			{/if}
			{#if successMsg}
				<div class="alert success" role="status">{successMsg}</div>
			{/if}

			{#if loading}
				<div class="loading-state">Loading notification center...</div>
			{:else}
				<div class="stats-strip">
					<div class="stat-card">
						<p class="stat-value">{summary?.total || 0}</p>
						<p class="stat-label">Total Notices</p>
					</div>
					<div class="stat-card">
						<p class="stat-value">{summary?.active || 0}</p>
						<p class="stat-label">Active Notices</p>
					</div>
					<div class="stat-card">
						<p class="stat-value">{summary?.feature_updates || 0}</p>
						<p class="stat-label">Feature Updates</p>
					</div>
					<div class="stat-card">
						<p class="stat-value">{summary?.research || 0}</p>
						<p class="stat-label">Research Invites</p>
					</div>
				</div>

				<div class="center-grid">
					<section class="composer-card">
						<div class="section-head">
							<h2>Publish Notice</h2>
							<p>Example: "New fatigue assessment module available."</p>
						</div>

						<div class="field-grid">
							<label class="field">
								<span>Notice Type</span>
								<select bind:value={form.notification_type}>
									{#each TYPE_OPTIONS as option}
										<option value={option.value}>{option.label}</option>
									{/each}
								</select>
							</label>

							<label class="field">
								<span>Audience</span>
								<select bind:value={form.audience}>
									{#each AUDIENCE_OPTIONS as option}
										<option value={option.value}>{option.label}</option>
									{/each}
								</select>
							</label>
						</div>

						<label class="field">
							<span>Title</span>
							<input type="text" bind:value={form.title} placeholder="New fatigue assessment module available" />
						</label>

						<label class="field">
							<span>Message</span>
							<textarea rows="7" bind:value={form.message} placeholder="Write a clear, professional update for users."></textarea>
						</label>

						<div class="composer-footer">
							<div class="preview-chip {typeClass(form.notification_type)}">{typeLabel(form.notification_type)} · {audienceLabel(form.audience)}</div>
							<button class="publish-btn" type="button" on:click={sendNotification} disabled={sending}>{sending ? 'Publishing...' : 'Publish Notification'}</button>
						</div>
					</section>

					<section class="history-card">
						<div class="section-head">
							<h2>Recent Notices</h2>
							<p>Sent announcements across the platform.</p>
						</div>

						{#if notifications.length === 0}
							<div class="empty-state">
								<p class="empty-title">No notifications published yet</p>
								<p class="empty-sub">Your first announcement will appear here.</p>
							</div>
						{:else}
							<div class="notice-list">
								{#each notifications as notification (notification.id)}
									<div class="notice-card">
										<div class="notice-top">
											<div>
												<p class="notice-title">{notification.title}</p>
												<p class="notice-meta">By {notification.created_by} · {relativeDate(notification.created_at)}</p>
											</div>
											<div class="notice-badges">
												<span class="badge {typeClass(notification.notification_type)}">{typeLabel(notification.notification_type)}</span>
												<span class="badge badge-neutral">{audienceLabel(notification.audience)}</span>
											</div>
										</div>
										<p class="notice-message">{notification.message}</p>
										<div class="notice-footer">
											<span>{notification.is_active ? 'Active' : 'Inactive'}</span>
											<span>{formatDateTime(notification.created_at)}</span>
										</div>
									</div>
								{/each}
							</div>
						{/if}
					</section>
				</div>
			{/if}
		</div>
	</main>
</div>

<style>
	.admin-layout { display: flex; min-height: 100vh; background: #f1f5f9; font-family: 'Inter', system-ui, sans-serif; }
	.sidebar { width: 240px; min-height: 100vh; background: #0f172a; color: #e2e8f0; display: flex; flex-direction: column; position: fixed; top: 0; left: 0; bottom: 0; }
	.sidebar-brand { display: flex; align-items: center; gap: 0.6rem; padding: 1.4rem 1.2rem; border-bottom: 1px solid #1e293b; font-weight: 700; font-size: 0.95rem; }
	.sidebar-nav { flex: 1; padding: 1rem 0.75rem; display: flex; flex-direction: column; gap: 0.25rem; }
	.nav-item { display: flex; align-items: center; gap: 0.6rem; padding: 0.65rem 0.9rem; border-radius: 8px; color: #94a3b8; text-decoration: none; font-size: 0.88rem; font-weight: 500; }
	.nav-item:hover { background: #1e293b; color: #f1f5f9; }
	.nav-item.active { background: #1d4ed8; color: #ffffff; }
	.logout-btn { margin: 0.75rem; padding: 0.65rem 0.9rem; background: transparent; border: 1px solid #334155; border-radius: 8px; color: #94a3b8; cursor: pointer; font-size: 0.88rem; display: flex; align-items: center; gap: 0.5rem; }
	.main-content { flex: 1; margin-left: 240px; }
	.topbar { display: flex; justify-content: space-between; align-items: center; padding: 1.25rem 2rem; background: #ffffff; border-bottom: 1px solid #e2e8f0; }
	.page-title { font-size: 1.35rem; font-weight: 700; color: #0f172a; margin: 0; }
	.page-sub { font-size: 0.8rem; color: #94a3b8; margin: 0.15rem 0 0; max-width: 760px; }
	.admin-info { font-size: 0.88rem; color: #475569; background: #f8fafc; padding: 0.5rem 0.9rem; border-radius: 8px; }
	.content { padding: 1.75rem 2rem; }
	.alert { padding: 0.9rem 1rem; border-radius: 12px; margin-bottom: 1rem; }
	.alert.error { background: #fef2f2; border: 1px solid #fecaca; color: #b91c1c; }
	.alert.success { background: #f0fdf4; border: 1px solid #86efac; color: #166534; }
	.loading-state { padding: 4rem 2rem; text-align: center; color: #64748b; }
	.stats-strip { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 1.25rem; }
	.stat-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 1.1rem 1.2rem; }
	.stat-value { margin: 0; font-size: 1.55rem; font-weight: 700; color: #0f172a; }
	.stat-label { margin: 0.2rem 0 0; font-size: 0.76rem; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.05em; }
	.center-grid { display: grid; grid-template-columns: minmax(320px, 480px) 1fr; gap: 1rem; }
	.composer-card, .history-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 1.15rem 1.2rem; }
	.section-head h2 { margin: 0; font-size: 1rem; color: #0f172a; }
	.section-head p { margin: 0.25rem 0 0; font-size: 0.8rem; color: #94a3b8; }
	.field-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; }
	.field { display: block; margin-top: 1rem; }
	.field span { display: block; margin-bottom: 0.4rem; font-size: 0.78rem; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.05em; }
	.field input, .field select, .field textarea { width: 100%; box-sizing: border-box; border: 1px solid #e2e8f0; border-radius: 10px; padding: 0.75rem 0.85rem; font-size: 0.88rem; background: #ffffff; }
	.field textarea { resize: vertical; }
	.composer-footer { display: flex; justify-content: space-between; gap: 0.8rem; align-items: center; margin-top: 1rem; flex-wrap: wrap; }
	.publish-btn { border: none; background: linear-gradient(135deg, #1d4ed8, #0f766e); color: #ffffff; border-radius: 10px; padding: 0.75rem 1rem; font-weight: 700; cursor: pointer; }
	.publish-btn:disabled { opacity: 0.6; cursor: not-allowed; }
	.notice-list { display: flex; flex-direction: column; gap: 0.8rem; margin-top: 1rem; }
	.notice-card { border: 1px solid #e2e8f0; border-radius: 14px; padding: 1rem; background: #f8fafc; }
	.notice-top { display: flex; justify-content: space-between; gap: 0.75rem; flex-wrap: wrap; }
	.notice-title { margin: 0; font-size: 0.92rem; font-weight: 700; color: #0f172a; }
	.notice-meta { margin: 0.25rem 0 0; font-size: 0.76rem; color: #94a3b8; }
	.notice-badges { display: flex; gap: 0.4rem; flex-wrap: wrap; }
	.badge, .preview-chip { padding: 0.2rem 0.65rem; border-radius: 999px; font-size: 0.72rem; font-weight: 700; }
	.type-blue { background: #dbeafe; color: #1d4ed8; }
	.type-teal { background: #ccfbf1; color: #0f766e; }
	.type-amber { background: #fef3c7; color: #92400e; }
	.badge-neutral { background: #f1f5f9; color: #475569; }
	.notice-message { margin: 0.75rem 0 0; font-size: 0.86rem; line-height: 1.6; color: #475569; }
	.notice-footer { display: flex; justify-content: space-between; gap: 0.75rem; margin-top: 0.8rem; font-size: 0.75rem; color: #94a3b8; }
	.empty-state { padding: 2rem 1rem; text-align: center; }
	.empty-title { margin: 0; font-size: 0.95rem; font-weight: 700; color: #334155; }
	.empty-sub { margin: 0.3rem 0 0; font-size: 0.82rem; color: #94a3b8; }
	@media (max-width: 960px) {
		.sidebar { position: static; width: 100%; min-height: auto; }
		.admin-layout { flex-direction: column; }
		.main-content { margin-left: 0; }
		.topbar { padding: 1rem 1.25rem; align-items: flex-start; }
		.content { padding: 1.25rem; }
		.center-grid, .field-grid { grid-template-columns: 1fr; }
	}
</style>
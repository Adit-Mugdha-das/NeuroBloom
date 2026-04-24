<script>
	import { locale as activeLocale, uiText } from '$lib/i18n';
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
			<div class="brand-mark">
			<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
				<path d="M12 5v14M5 12h14"/>
			</svg>
		</div>
			<span class="brand-name">{uiText("NeuroBloom Admin", $activeLocale)}</span>
		</div>
		<nav class="sidebar-nav">
			<a href="/admin/dashboard" class="nav-item"><svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
				</svg> {uiText("Dashboard", $activeLocale)}</a>
			<a href="/admin/analytics" class="nav-item"><svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
				</svg> {uiText("System Analytics", $activeLocale)}</a>
			<a href="/admin/doctors" class="nav-item"><svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
				</svg> {uiText("Doctor Management", $activeLocale)}</a>
			<a href="/admin/patients" class="nav-item"><svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
				</svg> {uiText("Patient Management", $activeLocale)}</a>
			<a href="/admin/departments" class="nav-item"><svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
				</svg> {uiText("Departments", $activeLocale)}</a>
			<a href="/admin/interventions" class="nav-item"><svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/>
				</svg> {uiText("Interventions", $activeLocale)}</a>
			<a href="/admin/messages" class="nav-item"><svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
				</svg> {uiText("Message Audit", $activeLocale)}</a>
			<a href="/admin/audit-logs" class="nav-item"><svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
				</svg> {uiText("Audit Logs", $activeLocale)}</a>
			<a href="/admin/system-health" class="nav-item"><svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
				</svg> {uiText("System Health", $activeLocale)}</a>
			<a href="/admin/notifications" class="nav-item active"><svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
				</svg> {uiText("Notification Center", $activeLocale)}</a>
			<a href="/admin/research-data" class="nav-item"><svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/>
				</svg> {uiText("Research Data", $activeLocale)}</a>
		</nav>
		<button class="logout-btn" on:click={logout}><svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
			<path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
		</svg> {uiText("Sign Out", $activeLocale)}</button>
	</aside>

	<main class="main-content">
		<header class="topbar">
			<div>
				<h1 class="page-title">{uiText("Notification Center", $activeLocale)}</h1>
				<p class="page-sub">{uiText("Publish system announcements, new feature updates, and research invitations from one professional admin surface.", $activeLocale)}</p>
			</div>
			<div class="admin-info">
				<div class="admin-avatar">
					<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
						<path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2M12 11a4 4 0 100-8 4 4 0 000 8z"/>
					</svg>
				</div>
				<div class="admin-details">
					<span class="admin-name">{admin?.full_name || admin?.email}</span>
					<span class="admin-role">{uiText("Administrator", $activeLocale)}</span>
				</div>
			</div>
		</header>

		<div class="content">
			{#if error}
				<div class="alert error" role="alert">{error}</div>
			{/if}
			{#if successMsg}
				<div class="alert success" role="status">{successMsg}</div>
			{/if}

			{#if loading}
				<div class="loading-state">{uiText("Loading notification center...", $activeLocale)}</div>
			{:else}
				<div class="stats-strip">
					<div class="stat-card">
						<p class="stat-value">{summary?.total || 0}</p>
						<p class="stat-label">{uiText("Total Notices", $activeLocale)}</p>
					</div>
					<div class="stat-card">
						<p class="stat-value">{summary?.active || 0}</p>
						<p class="stat-label">{uiText("Active Notices", $activeLocale)}</p>
					</div>
					<div class="stat-card">
						<p class="stat-value">{summary?.feature_updates || 0}</p>
						<p class="stat-label">{uiText("Feature Updates", $activeLocale)}</p>
					</div>
					<div class="stat-card">
						<p class="stat-value">{summary?.research || 0}</p>
						<p class="stat-label">{uiText("Research Invites", $activeLocale)}</p>
					</div>
				</div>

				<div class="center-grid">
					<section class="composer-card">
						<div class="section-head">
							<h2>{uiText("Publish Notice", $activeLocale)}</h2>
							<p>{uiText("Example: \"New fatigue assessment module available.\"", $activeLocale)}</p>
						</div>

						<div class="field-grid">
							<label class="field">
								<span>{uiText("Notice Type", $activeLocale)}</span>
								<select bind:value={form.notification_type}>
									{#each TYPE_OPTIONS as option}
										<option value={option.value}>{option.label}</option>
									{/each}
								</select>
							</label>

							<label class="field">
								<span>{uiText("Audience", $activeLocale)}</span>
								<select bind:value={form.audience}>
									{#each AUDIENCE_OPTIONS as option}
										<option value={option.value}>{option.label}</option>
									{/each}
								</select>
							</label>
						</div>

						<label class="field">
							<span>{uiText("Title", $activeLocale)}</span>
							<input type="text" bind:value={form.title} placeholder={uiText("New fatigue assessment module available", $activeLocale)} />
						</label>

						<label class="field">
							<span>{uiText("Message", $activeLocale)}</span>
							<textarea rows="7" bind:value={form.message} placeholder={uiText("Write a clear, professional update for users.", $activeLocale)}></textarea>
						</label>

						<div class="composer-footer">
							<div class="preview-chip {typeClass(form.notification_type)}">{typeLabel(form.notification_type)} · {audienceLabel(form.audience)}</div>
							<button class="publish-btn" type="button" on:click={sendNotification} disabled={sending}>{sending ? 'Publishing...' : 'Publish Notification'}</button>
						</div>
					</section>

					<section class="history-card">
						<div class="section-head">
							<h2>{uiText("Recent Notices", $activeLocale)}</h2>
							<p>{uiText("Sent announcements across the platform.", $activeLocale)}</p>
						</div>

						{#if notifications.length === 0}
							<div class="empty-state">
								<p class="empty-title">{uiText("No notifications published yet", $activeLocale)}</p>
								<p class="empty-sub">{uiText("Your first announcement will appear here.", $activeLocale)}</p>
							</div>
						{:else}
							<div class="notice-list">
								{#each notifications as notification (notification.id)}
									<div class="notice-card">
										<div class="notice-top">
											<div>
												<p class="notice-title" data-localize-skip>{notification.title}</p>
												<p class="notice-meta">By {notification.created_by} · {relativeDate(notification.created_at)}</p>
											</div>
											<div class="notice-badges">
												<span class="badge {typeClass(notification.notification_type)}">{typeLabel(notification.notification_type)}</span>
												<span class="badge badge-neutral">{audienceLabel(notification.audience)}</span>
											</div>
										</div>
										<p class="notice-message" data-localize-skip>{notification.message}</p>
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
	.brand-mark { width: 28px; height: 28px; background: #4f46e5; border-radius: 7px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: white; }
	.brand-mark svg { width: 16px; height: 16px; }
	.sidebar-nav { flex: 1; padding: 1rem 0.75rem; display: flex; flex-direction: column; gap: 0.25rem; }
	.nav-item { display: flex; align-items: center; gap: 0.6rem; padding: 0.65rem 0.9rem; border-radius: 8px; color: #94a3b8; text-decoration: none; font-size: 0.88rem; font-weight: 500; }
	.nav-item:hover { background: #1e293b; color: #f1f5f9; }
	.nav-item.active { background: #1d4ed8; color: #ffffff; }
	.nav-icon { width: 17px; height: 17px; flex-shrink: 0; }
	.logout-btn { margin: 0.75rem; padding: 0.65rem 0.9rem; background: transparent; border: 1px solid #334155; border-radius: 8px; color: #94a3b8; cursor: pointer; font-size: 0.88rem; display: flex; align-items: center; gap: 0.5rem; transition: all .2s; }
	.logout-btn:hover { background: #7f1d1d; color: #fca5a5; border-color: #7f1d1d; }
	.main-content { flex: 1; margin-left: 240px; }
	.topbar { display: flex; justify-content: space-between; align-items: center; padding: 1.25rem 2rem; background: #ffffff; border-bottom: 1px solid #e2e8f0; }
	.page-title { font-size: 1.35rem; font-weight: 700; color: #0f172a; margin: 0; }
	.page-sub { font-size: 0.8rem; color: #94a3b8; margin: 0.15rem 0 0; max-width: 760px; }
	.admin-info { display: flex; align-items: center; gap: 0.65rem; }
	.admin-avatar { width: 36px; height: 36px; border-radius: 50%; background: #eff6ff; border: 1.5px solid #bfdbfe; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: #3b82f6; }
	.admin-avatar svg { width: 18px; height: 18px; }
	.admin-details { display: flex; flex-direction: column; gap: 1px; }
	.admin-name { font-size: 0.88rem; font-weight: 600; color: #1e293b; }
	.admin-role { font-size: 0.72rem; color: #94a3b8; }
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
	.publish-btn { border: none; background: #4338ca; color: #ffffff; border-radius: 10px; padding: 0.75rem 1rem; font-weight: 700; cursor: pointer; }
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

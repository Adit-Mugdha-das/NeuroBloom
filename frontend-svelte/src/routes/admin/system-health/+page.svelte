<script>
	import { locale as activeLocale, uiText } from '$lib/i18n';
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let admin = null;
	let loading = true;
	let error = '';
	let health = null;

	async function loadHealth() {
		loading = true;
		error = '';
		try {
			const response = await api.get(`/api/admin/system-health?admin_id=${admin.id}`);
			health = response.data;
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Failed to load system health';
		} finally {
			loading = false;
		}
	}

	onMount(async () => {
		const currentUser = $user;
		if (!currentUser || currentUser.role !== 'admin') {
			goto('/login');
			return;
		}

		admin = currentUser;
		await loadHealth();
	});

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

	function formatUptime(seconds) {
		if (!seconds && seconds !== 0) return '-';
		const days = Math.floor(seconds / 86400);
		const hours = Math.floor((seconds % 86400) / 3600);
		const minutes = Math.floor((seconds % 3600) / 60);
		if (days > 0) return `${days}d ${hours}h ${minutes}m`;
		if (hours > 0) return `${hours}h ${minutes}m`;
		return `${minutes}m`;
	}

	function statusLabel(status) {
		if (status === 'operational') return 'Operational';
		if (status === 'degraded') return 'Degraded';
		return 'Unknown';
	}

	function statusClass(status) {
		if (status === 'operational') return 'status-good';
		if (status === 'degraded') return 'status-warn';
		return 'status-neutral';
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
			<a href="/admin/dashboard" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
				</svg> {uiText("Dashboard", $activeLocale)}
			</a>
			<a href="/admin/analytics" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
				</svg> {uiText("System Analytics", $activeLocale)}
			</a>
			<a href="/admin/doctors" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
				</svg> {uiText("Doctor Management", $activeLocale)}
			</a>
			<a href="/admin/patients" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
				</svg> {uiText("Patient Management", $activeLocale)}
			</a>
			<a href="/admin/departments" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
				</svg> {uiText("Departments", $activeLocale)}
			</a>
			<a href="/admin/interventions" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/>
				</svg> {uiText("Interventions", $activeLocale)}
			</a>
			<a href="/admin/messages" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
				</svg> {uiText("Message Audit", $activeLocale)}
			</a>
			<a href="/admin/audit-logs" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
				</svg> {uiText("Audit Logs", $activeLocale)}
			</a>
			<a href="/admin/system-health" class="nav-item active">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
				</svg> {uiText("System Health", $activeLocale)}
			</a>
			<a href="/admin/notifications" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
				</svg> {uiText("Notification Center", $activeLocale)}
			</a>
			<a href="/admin/research-data" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/>
				</svg> {uiText("Research Data", $activeLocale)}
			</a>
		</nav>
		<button class="logout-btn" on:click={logout}>
			<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
			<path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
		</svg> {uiText("Sign Out", $activeLocale)}
		</button>
	</aside>

	<main class="main-content">
		<header class="topbar">
			<div>
				<h1 class="page-title">{uiText("System Health Monitoring", $activeLocale)}</h1>
				<p class="page-sub">{uiText("Enterprise infrastructure visibility for API availability, database health, live activity, and server uptime", $activeLocale)}</p>
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

			{#if loading}
				<div class="loading-state">{uiText("Loading system health...", $activeLocale)}</div>
			{:else if health}
				<div class="hero-panel">
					<div>
						<p class="hero-kicker">{uiText("Live Infrastructure Overview", $activeLocale)}</p>
						<h2 class="hero-title">{uiText("System status is", $activeLocale)} {health.database?.status === 'operational' && health.api?.status === 'operational' ? 'stable' : 'being monitored closely'}</h2>
						<p class="hero-sub">{uiText("Checked at", $activeLocale)} {formatDateTime(health.api?.checked_at)}{uiText(". Use this panel for operational visibility and enterprise-style platform monitoring.", $activeLocale)}</p>
					</div>
					<button class="refresh-btn" type="button" on:click={loadHealth}>{uiText("Refresh Status", $activeLocale)}</button>
				</div>

				<div class="status-grid">
					<div class="status-card">
						<div class="status-top">
							<p class="status-title">{uiText("API Status", $activeLocale)}</p>
							<span class="status-chip {statusClass(health.api?.status)}">{statusLabel(health.api?.status)}</span>
						</div>
						<p class="status-value">{statusLabel(health.api?.status)}</p>
						<p class="status-meta">{uiText("Version", $activeLocale)} {health.api?.version || 'v1'} {uiText("· last checked", $activeLocale)} {formatDateTime(health.api?.checked_at)}</p>
					</div>

					<div class="status-card">
						<div class="status-top">
							<p class="status-title">{uiText("Database Status", $activeLocale)}</p>
							<span class="status-chip {statusClass(health.database?.status)}">{statusLabel(health.database?.status)}</span>
						</div>
						<p class="status-value">{health.database?.latency_ms ?? '-'} ms</p>
						<p class="status-meta">{uiText("Latency to primary database", $activeLocale)}{health.database?.error ? ` · ${health.database.error}` : ''}</p>
					</div>

					<div class="status-card accent-teal">
						<div class="status-top">
							<p class="status-title">{uiText("Active Sessions", $activeLocale)}</p>
							<span class="status-chip status-good">{uiText("Live", $activeLocale)}</span>
						</div>
						<p class="status-value">{health.sessions?.active_count ?? 0}</p>
						<p class="status-meta">{uiText("Distinct users active in the last", $activeLocale)} {health.sessions?.window_minutes ?? 15} {uiText("minutes", $activeLocale)}</p>
					</div>

					<div class="status-card accent-slate">
						<div class="status-top">
							<p class="status-title">{uiText("Server Uptime", $activeLocale)}</p>
							<span class="status-chip status-good">{uiText("Running", $activeLocale)}</span>
						</div>
						<p class="status-value">{formatUptime(health.server?.uptime_seconds)}</p>
						<p class="status-meta">{uiText("Started", $activeLocale)} {formatDateTime(health.server?.started_at)}</p>
					</div>
				</div>

				<div class="detail-grid">
					<div class="panel-card">
						<h3 class="panel-title">{uiText("Session Activity", $activeLocale)}</h3>
						<div class="metric-row">
							<span>{uiText("Recent context submissions", $activeLocale)}</span>
							<strong>{health.sessions?.recent_contexts ?? 0}</strong>
						</div>
						<div class="metric-row">
							<span>{uiText("Recent training events", $activeLocale)}</span>
							<strong>{health.sessions?.recent_training_events ?? 0}</strong>
						</div>
						<div class="metric-row">
							<span>{uiText("Active session window", $activeLocale)}</span>
							<strong>{health.sessions?.window_minutes ?? 15} {uiText("min", $activeLocale)}</strong>
						</div>
					</div>

					<div class="panel-card">
						<h3 class="panel-title">{uiText("Platform Capacity", $activeLocale)}</h3>
						<div class="metric-row">
							<span>{uiText("Registered patients", $activeLocale)}</span>
							<strong>{health.capacity?.patients ?? 0}</strong>
						</div>
						<div class="metric-row">
							<span>{uiText("Registered doctors", $activeLocale)}</span>
							<strong>{health.capacity?.doctors ?? 0}</strong>
						</div>
						<div class="metric-row">
							<span>{uiText("API mode", $activeLocale)}</span>
							<strong>{health.api?.version || 'v1'}</strong>
						</div>
					</div>

					<div class="panel-card wide-panel">
						<h3 class="panel-title">{uiText("Operational Summary", $activeLocale)}</h3>
						<p class="panel-copy">{uiText("This dashboard is designed for enterprise-grade oversight. Admins can confirm API responsiveness, verify database reachability, assess current activity, and review server runtime without touching clinical records or sensitive workflow controls.", $activeLocale)}</p>
						<div class="summary-strip">
							<div class="summary-pill">
								<span class="pill-label">{uiText("API", $activeLocale)}</span>
								<span class="pill-value {statusClass(health.api?.status)}">{statusLabel(health.api?.status)}</span>
							</div>
							<div class="summary-pill">
								<span class="pill-label">{uiText("Database", $activeLocale)}</span>
								<span class="pill-value {statusClass(health.database?.status)}">{statusLabel(health.database?.status)}</span>
							</div>
							<div class="summary-pill">
								<span class="pill-label">{uiText("Sessions", $activeLocale)}</span>
								<span class="pill-value status-good">{health.sessions?.active_count ?? 0} {uiText("active", $activeLocale)}</span>
							</div>
						</div>
					</div>
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
	.loading-state { padding: 4rem 2rem; text-align: center; color: #64748b; }
	.hero-panel { display: flex; justify-content: space-between; gap: 1rem; align-items: flex-start; padding: 1.35rem 1.4rem; border-radius: 18px; background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 55%, #0f766e 100%); color: #ffffff; margin-bottom: 1.25rem; }
	.hero-kicker { margin: 0; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: rgba(255,255,255,.72); }
	.hero-title { margin: 0.35rem 0 0; font-size: 1.45rem; font-weight: 700; }
	.hero-sub { margin: 0.45rem 0 0; font-size: 0.88rem; color: rgba(255,255,255,.8); max-width: 720px; }
	.refresh-btn { border: 1px solid rgba(255,255,255,.18); background: rgba(255,255,255,.12); color: #ffffff; border-radius: 10px; padding: 0.65rem 0.95rem; cursor: pointer; font-weight: 600; }
	.status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin-bottom: 1.25rem; }
	.status-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 1.15rem 1.2rem; }
	.accent-teal { background: linear-gradient(180deg, #f0fdfa 0%, #ffffff 100%); }
	.accent-slate { background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%); }
	.status-top { display: flex; justify-content: space-between; gap: 0.8rem; align-items: center; }
	.status-title { margin: 0; font-size: 0.78rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.06em; }
	.status-chip, .pill-value { padding: 0.2rem 0.65rem; border-radius: 999px; font-size: 0.72rem; font-weight: 700; }
	.status-good { background: #dcfce7; color: #166534; }
	.status-warn { background: #fef3c7; color: #92400e; }
	.status-neutral { background: #f1f5f9; color: #475569; }
	.status-value { margin: 0.8rem 0 0; font-size: 1.55rem; font-weight: 700; color: #0f172a; }
	.status-meta { margin: 0.25rem 0 0; font-size: 0.8rem; color: #94a3b8; line-height: 1.5; }
	.detail-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }
	.panel-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 1.1rem 1.2rem; }
	.wide-panel { grid-column: 1 / -1; }
	.panel-title { margin: 0 0 0.9rem; font-size: 0.95rem; font-weight: 700; color: #0f172a; }
	.metric-row { display: flex; justify-content: space-between; gap: 1rem; padding: 0.7rem 0; border-bottom: 1px solid #f1f5f9; font-size: 0.86rem; color: #475569; }
	.metric-row:last-child { border-bottom: none; }
	.metric-row strong { color: #0f172a; }
	.panel-copy { margin: 0; font-size: 0.86rem; line-height: 1.65; color: #64748b; }
	.summary-strip { display: flex; gap: 0.75rem; flex-wrap: wrap; margin-top: 1rem; }
	.summary-pill { display: flex; align-items: center; gap: 0.5rem; padding: 0.45rem 0.65rem; border-radius: 999px; background: #f8fafc; border: 1px solid #e2e8f0; }
	.pill-label { font-size: 0.75rem; color: #64748b; font-weight: 700; }
	@media (max-width: 960px) {
		.sidebar { position: static; width: 100%; min-height: auto; }
		.admin-layout { flex-direction: column; }
		.main-content { margin-left: 0; }
		.topbar { padding: 1rem 1.25rem; align-items: flex-start; }
		.content { padding: 1.25rem; }
		.detail-grid { grid-template-columns: 1fr; }
	}
	@media (max-width: 640px) {
		.hero-panel { flex-direction: column; }
		.status-top { align-items: flex-start; }
	}
</style>
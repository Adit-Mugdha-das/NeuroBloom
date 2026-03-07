<script>
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
			<span class="brand-icon">🏥</span>
			<span class="brand-name">NeuroBloom Admin</span>
		</div>
		<nav class="sidebar-nav">
			<a href="/admin/dashboard" class="nav-item">
				<span class="nav-icon">📊</span> Dashboard
			</a>
			<a href="/admin/analytics" class="nav-item">
				<span class="nav-icon">📈</span> System Analytics
			</a>
			<a href="/admin/doctors" class="nav-item">
				<span class="nav-icon">👨‍⚕️</span> Doctor Management
			</a>
			<a href="/admin/patients" class="nav-item">
				<span class="nav-icon">👤</span> Patient Management
			</a>
			<a href="/admin/departments" class="nav-item">
				<span class="nav-icon">🏢</span> Departments
			</a>
			<a href="/admin/interventions" class="nav-item">
				<span class="nav-icon">🩺</span> Interventions
			</a>
			<a href="/admin/messages" class="nav-item">
				<span class="nav-icon">💬</span> Message Audit
			</a>
			<a href="/admin/audit-logs" class="nav-item">
				<span class="nav-icon">📋</span> Audit Logs
			</a>
			<a href="/admin/system-health" class="nav-item active">
				<span class="nav-icon">🖥️</span> System Health
			</a>
			<a href="/admin/notifications" class="nav-item">
				<span class="nav-icon">🔔</span> Notification Center
			</a>
		</nav>
		<button class="logout-btn" on:click={logout}>
			<span>🚪</span> Logout
		</button>
	</aside>

	<main class="main-content">
		<header class="topbar">
			<div>
				<h1 class="page-title">System Health Monitoring</h1>
				<p class="page-sub">Enterprise infrastructure visibility for API availability, database health, live activity, and server uptime</p>
			</div>
			<div class="admin-info">{admin?.full_name || admin?.email}</div>
		</header>

		<div class="content">
			{#if error}
				<div class="alert error" role="alert">{error}</div>
			{/if}

			{#if loading}
				<div class="loading-state">Loading system health...</div>
			{:else if health}
				<div class="hero-panel">
					<div>
						<p class="hero-kicker">Live Infrastructure Overview</p>
						<h2 class="hero-title">System status is {health.database?.status === 'operational' && health.api?.status === 'operational' ? 'stable' : 'being monitored closely'}</h2>
						<p class="hero-sub">Checked at {formatDateTime(health.api?.checked_at)}. Use this panel for operational visibility and enterprise-style platform monitoring.</p>
					</div>
					<button class="refresh-btn" type="button" on:click={loadHealth}>Refresh Status</button>
				</div>

				<div class="status-grid">
					<div class="status-card">
						<div class="status-top">
							<p class="status-title">API Status</p>
							<span class="status-chip {statusClass(health.api?.status)}">{statusLabel(health.api?.status)}</span>
						</div>
						<p class="status-value">{statusLabel(health.api?.status)}</p>
						<p class="status-meta">Version {health.api?.version || 'v1'} · last checked {formatDateTime(health.api?.checked_at)}</p>
					</div>

					<div class="status-card">
						<div class="status-top">
							<p class="status-title">Database Status</p>
							<span class="status-chip {statusClass(health.database?.status)}">{statusLabel(health.database?.status)}</span>
						</div>
						<p class="status-value">{health.database?.latency_ms ?? '-'} ms</p>
						<p class="status-meta">Latency to primary database{health.database?.error ? ` · ${health.database.error}` : ''}</p>
					</div>

					<div class="status-card accent-teal">
						<div class="status-top">
							<p class="status-title">Active Sessions</p>
							<span class="status-chip status-good">Live</span>
						</div>
						<p class="status-value">{health.sessions?.active_count ?? 0}</p>
						<p class="status-meta">Distinct users active in the last {health.sessions?.window_minutes ?? 15} minutes</p>
					</div>

					<div class="status-card accent-slate">
						<div class="status-top">
							<p class="status-title">Server Uptime</p>
							<span class="status-chip status-good">Running</span>
						</div>
						<p class="status-value">{formatUptime(health.server?.uptime_seconds)}</p>
						<p class="status-meta">Started {formatDateTime(health.server?.started_at)}</p>
					</div>
				</div>

				<div class="detail-grid">
					<div class="panel-card">
						<h3 class="panel-title">Session Activity</h3>
						<div class="metric-row">
							<span>Recent context submissions</span>
							<strong>{health.sessions?.recent_contexts ?? 0}</strong>
						</div>
						<div class="metric-row">
							<span>Recent training events</span>
							<strong>{health.sessions?.recent_training_events ?? 0}</strong>
						</div>
						<div class="metric-row">
							<span>Active session window</span>
							<strong>{health.sessions?.window_minutes ?? 15} min</strong>
						</div>
					</div>

					<div class="panel-card">
						<h3 class="panel-title">Platform Capacity</h3>
						<div class="metric-row">
							<span>Registered patients</span>
							<strong>{health.capacity?.patients ?? 0}</strong>
						</div>
						<div class="metric-row">
							<span>Registered doctors</span>
							<strong>{health.capacity?.doctors ?? 0}</strong>
						</div>
						<div class="metric-row">
							<span>API mode</span>
							<strong>{health.api?.version || 'v1'}</strong>
						</div>
					</div>

					<div class="panel-card wide-panel">
						<h3 class="panel-title">Operational Summary</h3>
						<p class="panel-copy">This dashboard is designed for enterprise-grade oversight. Admins can confirm API responsiveness, verify database reachability, assess current activity, and review server runtime without touching clinical records or sensitive workflow controls.</p>
						<div class="summary-strip">
							<div class="summary-pill">
								<span class="pill-label">API</span>
								<span class="pill-value {statusClass(health.api?.status)}">{statusLabel(health.api?.status)}</span>
							</div>
							<div class="summary-pill">
								<span class="pill-label">Database</span>
								<span class="pill-value {statusClass(health.database?.status)}">{statusLabel(health.database?.status)}</span>
							</div>
							<div class="summary-pill">
								<span class="pill-label">Sessions</span>
								<span class="pill-value status-good">{health.sessions?.active_count ?? 0} active</span>
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
	.brand-icon { font-size: 1.2rem; }
	.sidebar-nav { flex: 1; padding: 1rem 0.75rem; display: flex; flex-direction: column; gap: 0.25rem; }
	.nav-item { display: flex; align-items: center; gap: 0.6rem; padding: 0.65rem 0.9rem; border-radius: 8px; color: #94a3b8; text-decoration: none; font-size: 0.88rem; font-weight: 500; }
	.nav-item:hover { background: #1e293b; color: #f1f5f9; }
	.nav-item.active { background: #1d4ed8; color: #ffffff; }
	.nav-icon { font-size: 1rem; }
	.logout-btn { margin: 0.75rem; padding: 0.65rem 0.9rem; background: transparent; border: 1px solid #334155; border-radius: 8px; color: #94a3b8; cursor: pointer; font-size: 0.88rem; display: flex; align-items: center; gap: 0.5rem; }
	.logout-btn:hover { background: #1e293b; color: #f1f5f9; }
	.main-content { flex: 1; margin-left: 240px; }
	.topbar { display: flex; justify-content: space-between; align-items: center; padding: 1.25rem 2rem; background: #ffffff; border-bottom: 1px solid #e2e8f0; }
	.page-title { font-size: 1.35rem; font-weight: 700; color: #0f172a; margin: 0; }
	.page-sub { font-size: 0.8rem; color: #94a3b8; margin: 0.15rem 0 0; max-width: 760px; }
	.admin-info { font-size: 0.88rem; color: #475569; background: #f8fafc; padding: 0.5rem 0.9rem; border-radius: 8px; }
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
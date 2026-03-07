<script>
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let admin = null;
	let loading = true;
	let error = '';

	let allLogs = [];
	let summary = null;

	let periodDays = 30;
	let categoryFilter = 'all';
	let actorFilter = 'all';
	let searchQuery = '';

	/** @type {Array<[number, string]>} */
	const PERIODS = [[7, '7d'], [30, '30d'], [90, '90d'], [0, 'All']];

	onMount(async () => {
		const currentUser = $user;
		if (!currentUser || currentUser.role !== 'admin') {
			goto('/login');
			return;
		}

		admin = currentUser;
		await loadAuditLogs();
	});

	async function loadAuditLogs() {
		loading = true;
		error = '';
		try {
			const response = await api.get(`/api/admin/audit-logs?admin_id=${admin.id}`);
			allLogs = response.data.logs;
			summary = response.data.summary;
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Failed to load audit logs';
		} finally {
			loading = false;
		}
	}

	function logout() {
		user.set(null);
		goto('/login');
	}

	function formatDate(iso) {
		if (!iso) return '-';
		return new Date(iso).toLocaleDateString('en-GB', {
			day: '2-digit',
			month: 'short',
			year: 'numeric'
		});
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
		return formatDate(iso);
	}

	function initials(name) {
		if (!name) return '?';
		const parts = name.trim().split(/\s+/);
		if (parts.length === 1) return parts[0][0].toUpperCase();
		return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
	}

	function categoryLabel(category) {
		if (category === 'admin') return 'Admin';
		if (category === 'clinical') return 'Clinical';
		if (category === 'training') return 'Training';
		if (category === 'communication') return 'Communication';
		return 'System';
	}

	function categoryClass(category) {
		if (category === 'admin') return 'cat-admin';
		if (category === 'clinical') return 'cat-clinical';
		if (category === 'training') return 'cat-training';
		if (category === 'communication') return 'cat-communication';
		return 'cat-system';
	}

	function periodLabel(days) {
		if (days === 0) return 'All time';
		if (days === 7) return 'Last 7 days';
		if (days === 30) return 'Last 30 days';
		return 'Last 90 days';
	}

	$: cutoff = periodDays === 0 ? null : new Date(Date.now() - periodDays * 86400000);
	$: loweredQuery = searchQuery.trim().toLowerCase();
	$: filteredLogs = allLogs.filter((log) => {
		if (categoryFilter !== 'all' && log.category !== categoryFilter) return false;
		if (actorFilter !== 'all' && log.actor_type !== actorFilter) return false;
		if (cutoff && new Date(log.created_at) < cutoff) return false;
		if (!loweredQuery) return true;

		return [log.actor_name || '', log.target_name || '', log.summary || '', log.detail || '', log.badge || '']
			.some((value) => value.toLowerCase().includes(loweredQuery));
	});

	$: categories = [...new Set(allLogs.map((log) => log.category))];
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
			<a href="/admin/audit-logs" class="nav-item active">
				<span class="nav-icon">📋</span> Audit Logs
			</a>
			<a href="/admin/system-health" class="nav-item">
				<span class="nav-icon">🖥️</span> System Health
			</a>
		</nav>
		<button class="logout-btn" on:click={logout}>
			<span>🚪</span> Logout
		</button>
	</aside>

	<main class="main-content">
		<header class="topbar">
			<div>
				<h1 class="page-title">Audit Logs</h1>
				<p class="page-sub">System activity traceability across training, clinical actions, communication, and administrative operations</p>
			</div>
			<div class="admin-info">{admin?.full_name || admin?.email}</div>
		</header>

		<div class="content">
			{#if error}
				<div class="alert error" role="alert">{error}</div>
			{/if}

			{#if loading}
				<div class="loading-state">Loading audit logs...</div>
			{:else}
				<div class="stats-strip">
					<div class="stat-card">
						<p class="stat-value">{filteredLogs.length}</p>
						<p class="stat-label">Events In View</p>
						<p class="stat-sub">{periodLabel(periodDays)}</p>
					</div>
					<div class="stat-card">
						<p class="stat-value">{summary?.admin_actions || 0}</p>
						<p class="stat-label">Admin Actions</p>
						<p class="stat-sub">passwords, approvals, transfers</p>
					</div>
					<div class="stat-card">
						<p class="stat-value">{summary?.clinical_actions || 0}</p>
						<p class="stat-label">Clinical Events</p>
						<p class="stat-sub">interventions recorded</p>
					</div>
					<div class="stat-card">
						<p class="stat-value">{summary?.training_events || 0}</p>
						<p class="stat-label">Training Events</p>
						<p class="stat-sub">patient submissions tracked</p>
					</div>
				</div>

				<div class="filter-panel">
					<div class="filter-top-row">
						<div class="period-tabs">
							{#each PERIODS as [value, label]}
								<button type="button" class="period-btn {periodDays === value ? 'active' : ''}" on:click={() => (periodDays = value)}>{label}</button>
							{/each}
						</div>
						<select class="filter-select" bind:value={categoryFilter}>
							<option value="all">All Categories</option>
							{#each categories as category}
								<option value={category}>{categoryLabel(category)}</option>
							{/each}
						</select>
						<select class="filter-select" bind:value={actorFilter}>
							<option value="all">All Actors</option>
							<option value="admin">Admin</option>
							<option value="doctor">Doctor</option>
							<option value="patient">Patient</option>
						</select>
					</div>

					<div class="filter-bottom-row">
						<input class="search-input" type="text" placeholder="Search actor, target, summary, or details..." bind:value={searchQuery} />
					</div>
				</div>

				<div class="section-head">
					<div>
						<h2 class="section-title">System Activity Timeline</h2>
						<p class="section-sub">This log provides traceability for compliance, investigations, and operational review.</p>
					</div>
					<div class="section-meta">{filteredLogs.length} record{filteredLogs.length !== 1 ? 's' : ''}</div>
				</div>

				{#if filteredLogs.length === 0}
					<div class="empty-state">
						<div class="empty-icon">📋</div>
						<p class="empty-title">No activity logs found</p>
						<p class="empty-sub">Try widening the time range or removing filters.</p>
					</div>
				{:else}
					<div class="timeline-list">
						{#each filteredLogs as log (log.id)}
							<div class="timeline-item">
								<div class="timeline-marker {categoryClass(log.category)}"></div>
								<div class="timeline-card">
									<div class="timeline-top">
										<div class="timeline-actor">
											<div class="actor-avatar">{initials(log.actor_name)}</div>
											<div>
												<p class="actor-name">{log.actor_name}</p>
												<p class="actor-meta">{categoryLabel(log.category)} · {log.badge}</p>
											</div>
										</div>
										<div class="timeline-meta">
											<span class="category-chip {categoryClass(log.category)}">{categoryLabel(log.category)}</span>
											<span class="timeline-date" title={formatDateTime(log.created_at)}>{relativeDate(log.created_at)}</span>
										</div>
									</div>

									<p class="timeline-summary">{log.summary}</p>
									{#if log.detail}
										<p class="timeline-detail">{log.detail}</p>
									{/if}
									<div class="timeline-footer">
										{#if log.target_name}
											<span class="footer-item">Target: {log.target_name}</span>
										{/if}
										<span class="footer-item">Logged: {formatDateTime(log.created_at)}</span>
									</div>
								</div>
							</div>
						{/each}
					</div>
				{/if}
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
	.stats-strip { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 1.25rem; }
	.stat-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 1.1rem 1.2rem; }
	.stat-value { margin: 0; font-size: 1.55rem; font-weight: 700; color: #0f172a; }
	.stat-label { margin: 0.2rem 0 0; font-size: 0.76rem; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.05em; }
	.stat-sub { margin: 0.25rem 0 0; font-size: 0.78rem; color: #94a3b8; }
	.filter-panel { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 1rem 1.1rem; margin-bottom: 1.4rem; }
	.filter-top-row, .filter-bottom-row { display: flex; align-items: center; justify-content: space-between; gap: 0.8rem; flex-wrap: wrap; }
	.filter-bottom-row { margin-top: 0.9rem; }
	.period-tabs { display: flex; gap: 0.35rem; flex-wrap: wrap; }
	.period-btn { padding: 0.45rem 0.9rem; border-radius: 999px; border: 1px solid #e2e8f0; background: #f8fafc; color: #475569; font-size: 0.82rem; font-weight: 600; cursor: pointer; }
	.period-btn.active { background: #1d4ed8; border-color: #1d4ed8; color: #ffffff; }
	.search-input { flex: 1; min-width: 280px; padding: 0.72rem 0.9rem; border: 1px solid #e2e8f0; border-radius: 10px; font-size: 0.88rem; background: #ffffff; }
	.filter-select { padding: 0.7rem 0.85rem; border: 1px solid #e2e8f0; border-radius: 10px; background: #ffffff; font-size: 0.85rem; color: #334155; }
	.section-head { display: flex; justify-content: space-between; align-items: flex-end; gap: 1rem; margin-bottom: 0.9rem; }
	.section-title { margin: 0; font-size: 1rem; font-weight: 700; color: #0f172a; }
	.section-sub { margin: 0.25rem 0 0; font-size: 0.82rem; color: #94a3b8; }
	.section-meta { font-size: 0.82rem; color: #64748b; }
	.empty-state { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 3.5rem 2rem; text-align: center; }
	.empty-icon { font-size: 2rem; margin-bottom: 0.5rem; }
	.empty-title { margin: 0; font-size: 1rem; font-weight: 700; color: #334155; }
	.empty-sub { margin: 0.35rem 0 0; font-size: 0.84rem; color: #94a3b8; }
	.timeline-list { position: relative; display: flex; flex-direction: column; gap: 0.9rem; }
	.timeline-list::before { content: ''; position: absolute; left: 17px; top: 0; bottom: 0; width: 2px; background: #dbe4f0; }
	.timeline-item { position: relative; display: flex; gap: 1rem; }
	.timeline-marker { position: relative; z-index: 1; width: 18px; height: 18px; border-radius: 50%; margin-top: 1.25rem; border: 3px solid #ffffff; box-shadow: 0 0 0 1px #dbe4f0; background: #64748b; flex-shrink: 0; }
	.timeline-card { flex: 1; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 1rem 1.1rem; }
	.timeline-top { display: flex; justify-content: space-between; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 0.65rem; }
	.timeline-actor { display: flex; gap: 0.75rem; align-items: center; }
	.actor-avatar { width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #0f766e, #1d4ed8); color: #ffffff; display: flex; align-items: center; justify-content: center; font-size: 0.82rem; font-weight: 700; }
	.actor-name { margin: 0; font-size: 0.92rem; font-weight: 700; color: #0f172a; }
	.actor-meta { margin: 0.2rem 0 0; font-size: 0.76rem; color: #94a3b8; }
	.timeline-meta { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
	.category-chip { padding: 0.22rem 0.65rem; border-radius: 999px; font-size: 0.72rem; font-weight: 700; }
	.cat-admin { background: #dbeafe; color: #1d4ed8; }
	.cat-clinical { background: #ecfccb; color: #3f6212; }
	.cat-training { background: #ede9fe; color: #6d28d9; }
	.cat-communication { background: #fef3c7; color: #92400e; }
	.cat-system { background: #f1f5f9; color: #475569; }
	.timeline-date { font-size: 0.76rem; color: #94a3b8; }
	.timeline-summary { margin: 0; font-size: 0.9rem; font-weight: 600; color: #1e293b; }
	.timeline-detail { margin: 0.35rem 0 0; font-size: 0.84rem; line-height: 1.6; color: #64748b; }
	.timeline-footer { display: flex; gap: 0.85rem; flex-wrap: wrap; margin-top: 0.85rem; padding-top: 0.75rem; border-top: 1px solid #f1f5f9; }
	.footer-item { font-size: 0.76rem; color: #94a3b8; }
	@media (max-width: 960px) {
		.sidebar { position: static; width: 100%; min-height: auto; }
		.admin-layout { flex-direction: column; }
		.main-content { margin-left: 0; }
		.topbar { padding: 1rem 1.25rem; align-items: flex-start; }
		.content { padding: 1.25rem; }
	}
	@media (max-width: 640px) {
		.search-input { min-width: 100%; }
		.filter-select { width: 100%; }
		.filter-top-row, .filter-bottom-row { align-items: stretch; }
		.timeline-top { flex-direction: column; align-items: flex-start; }
	}
</style>
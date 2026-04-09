<script>
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let admin = null;
	let loading = true;
	let downloading = '';
	let error = '';
	let successMsg = '';
	let datasets = [];
	let summary = null;

	onMount(async () => {
		const currentUser = $user;
		if (!currentUser || currentUser.role !== 'admin') {
			goto('/login');
			return;
		}

		admin = currentUser;
		await loadSummary();
	});

	async function loadSummary() {
		loading = true;
		error = '';
		try {
			const response = await api.get(`/api/admin/research-exports/summary?admin_id=${admin.id}`);
			datasets = response.data.datasets || [];
			summary = response.data.summary;
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Failed to load research export summary';
		} finally {
			loading = false;
		}
	}

	async function downloadExport(datasetKey, format) {
		downloading = `${datasetKey}:${format}`;
		error = '';
		successMsg = '';
		try {
			const response = await api.get('/api/admin/research-exports/download', {
				params: {
					admin_id: admin.id,
					dataset: datasetKey,
					file_format: format
				},
				responseType: 'blob'
			});

			const blobUrl = window.URL.createObjectURL(response.data);
			const link = document.createElement('a');
			const disposition = response.headers['content-disposition'];
			const filenameMatch = disposition?.match(/filename="?([^\"]+)"?/);
			link.href = blobUrl;
			link.download = filenameMatch?.[1] || `${datasetKey}.${format}`;
			document.body.appendChild(link);
			link.click();
			link.remove();
			window.URL.revokeObjectURL(blobUrl);

			successMsg = `${format.toUpperCase()} export downloaded successfully.`;
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Failed to download export';
		} finally {
			downloading = '';
		}
	}

	function logout() {
		user.set(null);
		goto('/login');
	}

	function formatNumber(value) {
		return new Intl.NumberFormat('en-GB').format(value || 0);
	}

	function formatDate(value) {
		if (!value) return 'No data yet';
		return new Date(value).toLocaleDateString('en-GB', {
			day: '2-digit',
			month: 'short',
			year: 'numeric'
		});
	}

	function formatDatasetKey(value) {
		return value.replace(/_/g, ' ');
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
			<span class="brand-name">NeuroBloom Admin</span>
		</div>
		<nav class="sidebar-nav">
			<a href="/admin/dashboard" class="nav-item"><svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
				</svg> Dashboard</a>
			<a href="/admin/analytics" class="nav-item"><svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
				</svg> System Analytics</a>
			<a href="/admin/doctors" class="nav-item"><svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
				</svg> Doctor Management</a>
			<a href="/admin/patients" class="nav-item"><svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
				</svg> Patient Management</a>
			<a href="/admin/departments" class="nav-item"><svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
				</svg> Departments</a>
			<a href="/admin/interventions" class="nav-item"><svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/>
				</svg> Interventions</a>
			<a href="/admin/messages" class="nav-item"><svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
				</svg> Message Audit</a>
			<a href="/admin/audit-logs" class="nav-item"><svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
				</svg> Audit Logs</a>
			<a href="/admin/system-health" class="nav-item"><svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
				</svg> System Health</a>
			<a href="/admin/notifications" class="nav-item"><svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
				</svg> Notification Center</a>
			<a href="/admin/research-data" class="nav-item active"><svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/>
				</svg> Research Data</a>
		</nav>
		<button class="logout-btn" on:click={logout}><svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
			<path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
		</svg> Sign Out</button>
	</aside>

	<main class="main-content">
		<header class="topbar">
			<div>
				<h1 class="page-title">Research Data Exports</h1>
				<p class="page-sub">Export anonymized NeuroBloom datasets for research papers, secondary analysis, and institutional reporting.</p>
			</div>
			<div class="admin-info">
				<div class="admin-avatar">
					<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
						<path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2M12 11a4 4 0 100-8 4 4 0 000 8z"/>
					</svg>
				</div>
				<div class="admin-details">
					<span class="admin-name">{admin?.full_name || admin?.email}</span>
					<span class="admin-role">Administrator</span>
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
				<div class="loading-state">Loading research export catalog...</div>
			{:else}
				<div class="overview-grid">
					<div class="overview-card hero-card">
						<p class="hero-kicker">Research Ready</p>
						<h2>Anonymized datasets for publication workflows</h2>
						<p>All exports remove direct patient identifiers and support CSV, JSON, and concise PDF research reports.</p>
					</div>
					<div class="overview-card stat-card">
						<p class="stat-value">{formatNumber(summary?.total_datasets)}</p>
						<p class="stat-label">Datasets</p>
					</div>
					<div class="overview-card stat-card">
						<p class="stat-value">{formatNumber(summary?.total_records)}</p>
						<p class="stat-label">Rows Available</p>
					</div>
				</div>

				<div class="dataset-grid">
					{#each datasets as dataset}
						<section class="dataset-card">
							<div class="dataset-head">
								<div>
									<p class="dataset-kicker">{formatDatasetKey(dataset.key)}</p>
									<h2>{dataset.label}</h2>
								</div>
								<span class="dataset-count">{formatNumber(dataset.record_count)} rows</span>
							</div>

							<p class="dataset-description">{dataset.description}</p>

							<div class="dataset-metrics">
								<div class="metric-pill">
									<span>Patients</span>
									<strong>{formatNumber(dataset.unique_patients)}</strong>
								</div>
								<div class="metric-pill">
									<span>Start</span>
									<strong>{formatDate(dataset.date_range?.start)}</strong>
								</div>
								<div class="metric-pill">
									<span>Latest</span>
									<strong>{formatDate(dataset.date_range?.end)}</strong>
								</div>
							</div>

							{#if dataset.preview_fields?.length}
								<div class="preview-block">
									<p class="preview-label">Preview fields</p>
									<div class="preview-tags">
										{#each dataset.preview_fields as field}
											<span class="preview-tag">{field}</span>
										{/each}
									</div>
								</div>
							{/if}

							<div class="export-actions">
								<button class="export-btn" on:click={() => downloadExport(dataset.key, 'csv')} disabled={downloading !== ''}>
									{downloading === `${dataset.key}:csv` ? 'Preparing CSV...' : 'Export CSV'}
								</button>
								<button class="export-btn secondary" on:click={() => downloadExport(dataset.key, 'json')} disabled={downloading !== ''}>
									{downloading === `${dataset.key}:json` ? 'Preparing JSON...' : 'Export JSON'}
								</button>
								<button class="export-btn secondary" on:click={() => downloadExport(dataset.key, 'pdf')} disabled={downloading !== ''}>
									{downloading === `${dataset.key}:pdf` ? 'Preparing PDF...' : 'Export PDF Report'}
								</button>
							</div>
						</section>
					{/each}
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
	.overview-grid { display: grid; grid-template-columns: minmax(260px, 2fr) repeat(2, minmax(160px, 1fr)); gap: 1rem; margin-bottom: 1rem; }
	.overview-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 18px; padding: 1.2rem 1.3rem; }
	.hero-card { background: linear-gradient(135deg, #eff6ff 0%, #ecfeff 100%); }
	.hero-kicker { margin: 0 0 0.35rem; font-size: 0.76rem; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: #0f766e; }
	.hero-card h2 { margin: 0; font-size: 1.1rem; color: #0f172a; }
	.hero-card p:last-child { margin: 0.45rem 0 0; color: #475569; line-height: 1.6; }
	.stat-card { display: flex; flex-direction: column; justify-content: center; }
	.stat-value { margin: 0; font-size: 1.7rem; font-weight: 800; color: #0f172a; }
	.stat-label { margin: 0.25rem 0 0; font-size: 0.78rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 700; }
	.dataset-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1rem; }
	.dataset-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 18px; padding: 1.2rem 1.25rem; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04); }
	.dataset-head { display: flex; justify-content: space-between; gap: 1rem; align-items: flex-start; }
	.dataset-kicker { margin: 0 0 0.3rem; font-size: 0.74rem; color: #1d4ed8; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 800; }
	.dataset-head h2 { margin: 0; font-size: 1rem; color: #0f172a; }
	.dataset-count { background: #f8fafc; color: #334155; border-radius: 999px; padding: 0.35rem 0.75rem; font-size: 0.75rem; font-weight: 800; white-space: nowrap; }
	.dataset-description { margin: 0.8rem 0 0; color: #475569; line-height: 1.6; font-size: 0.9rem; }
	.dataset-metrics { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.65rem; margin-top: 1rem; }
	.metric-pill { background: #f8fafc; border-radius: 12px; padding: 0.75rem 0.8rem; }
	.metric-pill span { display: block; font-size: 0.72rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.06em; }
	.metric-pill strong { display: block; margin-top: 0.3rem; font-size: 0.88rem; color: #0f172a; }
	.preview-block { margin-top: 1rem; }
	.preview-label { margin: 0; font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.06em; }
	.preview-tags { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.65rem; }
	.preview-tag { background: #eef2ff; color: #3730a3; padding: 0.3rem 0.65rem; border-radius: 999px; font-size: 0.75rem; font-weight: 700; }
	.export-actions { display: flex; gap: 0.65rem; margin-top: 1.2rem; flex-wrap: wrap; }
	.export-btn { border: none; background: #4338ca; color: #ffffff; border-radius: 10px; padding: 0.72rem 0.95rem; font-weight: 700; cursor: pointer; }
	.export-btn.secondary { background: #e2e8f0; color: #0f172a; }
	.export-btn:disabled { opacity: 0.6; cursor: not-allowed; }
	@media (max-width: 960px) {
		.sidebar { position: static; width: 100%; min-height: auto; }
		.admin-layout { flex-direction: column; }
		.main-content { margin-left: 0; }
		.topbar { padding: 1rem 1.25rem; align-items: flex-start; }
		.content { padding: 1.25rem; }
		.overview-grid, .dataset-metrics { grid-template-columns: 1fr; }
	}
</style>
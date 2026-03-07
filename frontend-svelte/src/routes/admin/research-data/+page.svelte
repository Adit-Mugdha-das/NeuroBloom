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
			<a href="/admin/notifications" class="nav-item"><span class="nav-icon">🔔</span> Notification Center</a>
			<a href="/admin/research-data" class="nav-item active"><span class="nav-icon">🧪</span> Research Data</a>
		</nav>
		<button class="logout-btn" on:click={logout}><span>🚪</span> Logout</button>
	</aside>

	<main class="main-content">
		<header class="topbar">
			<div>
				<h1 class="page-title">Research Data Exports</h1>
				<p class="page-sub">Export anonymized NeuroBloom datasets for research papers, secondary analysis, and institutional reporting.</p>
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
	.export-btn { border: none; background: linear-gradient(135deg, #1d4ed8, #0f766e); color: #ffffff; border-radius: 10px; padding: 0.72rem 0.95rem; font-weight: 700; cursor: pointer; }
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
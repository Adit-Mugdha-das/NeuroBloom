<script>
	import { locale as activeLocale, uiText } from '$lib/i18n';
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let admin = null;
	let loading = true;
	let error = '';

	let allInterventions = [];
	let summary = null;

	let filterType = 'all';
	let filterDoctorId = 'all';
	let periodDays = 30;

	onMount(async () => {
		const currentUser = $user;
		if (!currentUser || currentUser.role !== 'admin') {
			goto('/login');
			return;
		}
		admin = currentUser;
		await load();
	});

	async function load() {
		loading = true;
		error = '';
		try {
			const res = await api.get(`/api/admin/interventions?admin_id=${admin.id}`);
			allInterventions = res.data.interventions;
			summary = res.data.summary;
		} catch (err) {
			error = err.response?.data?.detail || 'Failed to load interventions';
		} finally {
			loading = false;
		}
	}

	const TYPE_LABELS = {
		training_plan_adjustment: 'Plan Adjustment',
		note: 'Clinical Note',
		recommendation: 'Recommendation',
		admin_risk_alert: 'Risk Alert',
		admin_escalation: 'Escalation'
	};

	const TYPE_CLASS = {
		recommendation: 'type-blue',
		note: 'type-slate',
		training_plan_adjustment: 'type-purple',
		admin_risk_alert: 'type-amber',
		admin_escalation: 'type-red'
	};

	const BORDER_CLASS = {
		recommendation: 'border-blue',
		note: 'border-slate',
		training_plan_adjustment: 'border-purple',
		admin_risk_alert: 'border-amber',
		admin_escalation: 'border-red'
	};

	function typeLabel(type) {
		return TYPE_LABELS[type] || type;
	}

	function typeClass(type) {
		return TYPE_CLASS[type] || 'type-slate';
	}

	function borderClass(type) {
		return BORDER_CLASS[type] || 'border-slate';
	}

	function formatDate(iso) {
		if (!iso) return '-';
		return new Date(iso).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
	}

	function relativeDate(iso) {
		if (!iso) return '';
		const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 86400000);
		if (diff === 0) return 'Today';
		if (diff === 1) return 'Yesterday';
		if (diff < 7) return diff + 'd ago';
		return formatDate(iso);
	}

	function initials(name) {
		if (!name) return '?';
		const parts = name.trim().split(' ');
		if (parts.length === 1) return parts[0][0].toUpperCase();
		return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
	}

	function getPeriodLabel(days) {
		if (days === 0) return 'All time';
		if (days === 7) return 'Last 7 days';
		if (days === 30) return 'Last 30 days';
		return 'Last 90 days';
	}

	function buildUniqueDoctors(interventions) {
		const seen = {};
		const result = [];
		for (const i of interventions) {
			if (!seen[i.doctor_id]) {
				seen[i.doctor_id] = true;
				result.push({ id: i.doctor_id, name: i.doctor_name });
			}
		}
		return result.sort(function(a, b) { return a.name < b.name ? -1 : a.name > b.name ? 1 : 0; });
	}

	$: cutoff = periodDays === 0 ? null : new Date(Date.now() - periodDays * 86400000);

	$: filtered = allInterventions.filter(function(i) {
		if (filterType !== 'all' && i.intervention_type !== filterType) return false;
		if (filterDoctorId !== 'all' && String(i.doctor_id) !== filterDoctorId) return false;
		if (cutoff && new Date(i.created_at) < cutoff) return false;
		return true;
	});

	$: uniqueDoctors = buildUniqueDoctors(allInterventions);
	$: uniqueTypes = [...new Set(allInterventions.map(function(i) { return i.intervention_type; }))];
	$: doctorGenerated = filtered.filter(function(i) { return i.intervention_type.indexOf('admin_') !== 0; }).length;
	$: topDoctor = summary && summary.top_doctors && summary.top_doctors[0] ? summary.top_doctors[0] : null;
	$: periodLabel = getPeriodLabel(periodDays);

	/** @type {Array<[number, string]>} */
	const PERIODS = [[7, '7d'], [30, '30d'], [90, '90d'], [0, 'All']];

	function logout() {
		user.set(null);
		goto('/login');
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
			</svg>
			{uiText("Dashboard", $activeLocale)}
			</a>
			<a href="/admin/analytics" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
			</svg>
			{uiText("System Analytics", $activeLocale)}
			</a>
			<a href="/admin/doctors" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
			</svg>
			{uiText("Doctor Management", $activeLocale)}
			</a>
			<a href="/admin/patients" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
			</svg>
			{uiText("Patient Management", $activeLocale)}
			</a>
			<a href="/admin/departments" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
			</svg>
			{uiText("Departments", $activeLocale)}
			</a>
			<a href="/admin/interventions" class="nav-item active">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/>
			</svg>
			{uiText("Interventions", $activeLocale)}
			</a>
			<a href="/admin/messages" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
			</svg>
			{uiText("Message Audit", $activeLocale)}
			</a>
			<a href="/admin/audit-logs" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
			</svg>
			{uiText("Audit Logs", $activeLocale)}
			</a>
			<a href="/admin/system-health" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
			</svg>
			{uiText("System Health", $activeLocale)}
			</a>
			<a href="/admin/notifications" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
			</svg>
			{uiText("Notification Center", $activeLocale)}
			</a>
			<a href="/admin/research-data" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/>
			</svg>
			{uiText("Research Data", $activeLocale)}
			</a>
		</nav>
		<button class="logout-btn" on:click={logout}>
			<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
			</svg>
			{uiText("Sign Out", $activeLocale)}
		</button>
	</aside>

	<main class="main-content">
		<header class="topbar">
			<div>
				<h1 class="page-title">{uiText("Intervention Monitoring", $activeLocale)}</h1>
				<p class="page-sub">{uiText("Clinical quality oversight of all doctor-patient interventions", $activeLocale)}</p>
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
				<div class="alert-error" role="alert">{error}</div>
			{/if}

			{#if loading}
				<div class="loading-state">{uiText("Loading interventions...", $activeLocale)}</div>
			{:else}
				<!-- Summary Strip -->
				<div class="summary-strip">
					<div class="summary-card">
						<p class="sc-value">{filtered.length}</p>
						<p class="sc-label">{uiText("Interventions in View", $activeLocale)}</p>
						<p class="sc-sub">{periodLabel}</p>
					</div>
					<div class="summary-card">
						<p class="sc-value">{doctorGenerated}</p>
						<p class="sc-label">{uiText("Doctor-Generated", $activeLocale)}</p>
						<p class="sc-sub">{uiText("clinical actions", $activeLocale)}</p>
					</div>
					<div class="summary-card">
						<p class="sc-value">{uniqueDoctors.length}</p>
						<p class="sc-label">{uiText("Active Doctors", $activeLocale)}</p>
						<p class="sc-sub">{uiText("with recorded interventions", $activeLocale)}</p>
					</div>
					{#if topDoctor}
						<div class="summary-card summary-highlight">
							<p class="sc-value sc-truncate">{uiText("Dr.", $activeLocale)} {topDoctor.doctor_name}</p>
							<p class="sc-label">{uiText("Most Active Doctor", $activeLocale)}</p>
							<p class="sc-sub">{topDoctor.count} {uiText("intervention", $activeLocale)}{topDoctor.count !== 1 ? 's' : ''} {uiText("total", $activeLocale)}</p>
						</div>
					{/if}
				</div>

				<!-- Filter Bar -->
				<div class="filter-bar">
					<div class="filter-group">
						<span class="filter-label">{uiText("Period", $activeLocale)}</span>
						<div class="period-tabs">
						{#each PERIODS as [val, lbl]}
							<button
								type="button"
								class="period-btn {periodDays === val ? 'active' : ''}"
								on:click={() => (periodDays = val)}
								>{lbl}</button>
							{/each}
						</div>
					</div>
					<div class="filter-group">
						<span class="filter-label">{uiText("Type", $activeLocale)}</span>
						<select class="filter-select" bind:value={filterType}>
							<option value="all">{uiText("All Types", $activeLocale)}</option>
							{#each uniqueTypes as t}
								<option value={t}>{typeLabel(t)}</option>
							{/each}
						</select>
					</div>
					<div class="filter-group">
						<span class="filter-label">{uiText("Doctor", $activeLocale)}</span>
						<select class="filter-select" bind:value={filterDoctorId}>
							<option value="all">{uiText("All Doctors", $activeLocale)}</option>
							{#each uniqueDoctors as d}
								<option value={String(d.id)}>{uiText("Dr.", $activeLocale)} {d.name}</option>
							{/each}
						</select>
					</div>
				</div>

				<!-- Results Count -->
				<p class="results-bar">{filtered.length} {uiText("intervention", $activeLocale)}{filtered.length !== 1 ? 's' : ''}</p>

				<!-- Feed -->
				{#if filtered.length === 0}
					<div class="empty-state">
						<div class="empty-icon-wrap">
						<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
							<path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/>
						</svg>
					</div>
						<p class="empty-title">{uiText("No interventions found", $activeLocale)}</p>
						<p class="empty-sub">{uiText("Try adjusting the period or filters above.", $activeLocale)}</p>
					</div>
				{:else}
					<div class="feed">
						{#each filtered as item (item.id)}
							<div class="icard {borderClass(item.intervention_type)}">
								<div class="icard-avatar">{initials(item.doctor_name)}</div>
								<div class="icard-body">
									<div class="icard-header">
										<div class="icard-who">
											<span class="who-doctor">{uiText("Dr.", $activeLocale)} {item.doctor_name}</span>
											{#if item.doctor_specialization}
												<span class="who-spec">{item.doctor_specialization}</span>
											{/if}
											<span class="who-arrow">&#8594;</span>
											<span class="who-patient">{item.patient_name}</span>
										</div>
										<div class="icard-badges">
											<span class="type-badge {typeClass(item.intervention_type)}">{typeLabel(item.intervention_type)}</span>
											<span class="icard-date" title={formatDate(item.created_at)}>{relativeDate(item.created_at)}</span>
										</div>
									</div>
									<p class="icard-desc">{item.description}</p>
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
	/* Layout */
	.admin-layout { display: flex; min-height: 100vh; background: #f1f5f9; font-family: 'Inter', system-ui, sans-serif; }

	/* Sidebar */
	.sidebar { width: 240px; min-height: 100vh; background: #0f172a; color: #e2e8f0; display: flex; flex-direction: column; position: fixed; top: 0; left: 0; bottom: 0; }
	.sidebar-brand { display: flex; align-items: center; gap: 0.6rem; padding: 1.4rem 1.2rem; border-bottom: 1px solid #1e293b; font-weight: 700; font-size: 0.95rem; }
	.brand-mark { width: 28px; height: 28px; background: #4f46e5; border-radius: 7px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: white; }
	.brand-mark svg { width: 16px; height: 16px; }
	.sidebar-nav { flex: 1; padding: 1rem 0.75rem; display: flex; flex-direction: column; gap: 0.25rem; }
	.nav-item { display: flex; align-items: center; gap: 0.6rem; padding: 0.65rem 0.9rem; border-radius: 8px; color: #94a3b8; text-decoration: none; font-size: 0.88rem; font-weight: 500; }
	.nav-item:hover { background: #1e293b; color: #f1f5f9; }
	.nav-item.active { background: #1d4ed8; color: #ffffff; }
	.nav-icon { width: 17px; height: 17px; flex-shrink: 0; }
	.logout-btn { margin: 0.75rem; padding: 0.65rem 0.9rem; background: transparent; border: 1px solid #334155; border-radius: 8px; color: #94a3b8; cursor: pointer; font-size: 0.88rem; display: flex; align-items: center; gap: 0.5rem; }
	.logout-btn:hover { background: #1e293b; color: #f1f5f9; }

	/* Main area */
	.main-content { flex: 1; margin-left: 240px; }
	.topbar { display: flex; justify-content: space-between; align-items: center; padding: 1.25rem 2rem; background: #ffffff; border-bottom: 1px solid #e2e8f0; }
	.page-title { font-size: 1.35rem; font-weight: 700; color: #0f172a; margin: 0; }
	.page-sub { font-size: 0.8rem; color: #94a3b8; margin: 0.15rem 0 0; }
	.admin-info { display: flex; align-items: center; gap: 0.65rem; }
	.admin-avatar { width: 36px; height: 36px; border-radius: 50%; background: #eff6ff; border: 1.5px solid #bfdbfe; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: #3b82f6; }
	.admin-avatar svg { width: 18px; height: 18px; }
	.admin-details { display: flex; flex-direction: column; gap: 1px; }
	.admin-name { font-size: 0.88rem; font-weight: 600; color: #1e293b; }
	.admin-role { font-size: 0.72rem; color: #94a3b8; }
	.content { padding: 1.75rem 2rem; }

	/* Alerts */
	.alert-error { padding: 0.85rem 1.1rem; border-radius: 10px; margin-bottom: 1.25rem; background: #fef2f2; border: 1px solid #fecaca; color: #b91c1c; font-size: 0.88rem; font-weight: 500; }
	.loading-state { padding: 4rem 2rem; text-align: center; color: #64748b; font-size: 0.9rem; }

	/* Summary strip */
	.summary-strip { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }
	.summary-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.1rem 1.3rem; }
	.summary-highlight { border-color: #c7d2fe; background: #eef2ff; }
	.sc-value { font-size: 1.55rem; font-weight: 700; color: #0f172a; margin: 0 0 0.2rem; line-height: 1; }
	.sc-truncate { font-size: 1rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.sc-label { font-size: 0.78rem; font-weight: 600; color: #475569; margin: 0 0 0.1rem; }
	.sc-sub { font-size: 0.72rem; color: #94a3b8; margin: 0; }

	/* Filter bar */
	.filter-bar { display: flex; align-items: center; gap: 1.5rem; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 0.9rem 1.3rem; margin-bottom: 1rem; flex-wrap: wrap; }
	.filter-group { display: flex; align-items: center; gap: 0.55rem; }
	.filter-label { font-size: 0.72rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.07em; white-space: nowrap; }
	.period-tabs { display: flex; gap: 0.3rem; }
	.period-btn { padding: 0.35rem 0.85rem; border: 1px solid #e2e8f0; border-radius: 999px; background: #f8fafc; cursor: pointer; font-size: 0.8rem; font-weight: 600; color: #64748b; }
	.period-btn.active { background: #4f46e5; border-color: #4f46e5; color: #ffffff; }
	.filter-select { padding: 0.38rem 0.8rem; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 0.83rem; color: #334155; background: #f8fafc; cursor: pointer; outline: none; }

	/* Results */
	.results-bar { font-size: 0.82rem; color: #94a3b8; margin: 0 0 0.75rem; }

	/* Empty state */
	.empty-state { text-align: center; padding: 4rem 2rem; }
	.empty-icon-wrap { width: 56px; height: 56px; border-radius: 50%; background: #f1f5f9; border: 1.5px solid #e2e8f0; display: flex; align-items: center; justify-content: center; margin: 0 auto 0.75rem; color: #94a3b8; }
	.empty-icon-wrap svg { width: 26px; height: 26px; }
	.empty-title { font-size: 1.05rem; font-weight: 600; color: #334155; margin: 0 0 0.35rem; }
	.empty-sub { font-size: 0.85rem; color: #94a3b8; margin: 0; }

	/* Intervention feed */
	.feed { display: flex; flex-direction: column; gap: 0.7rem; }
	.icard { display: flex; align-items: flex-start; gap: 1.1rem; background: #ffffff; border: 1px solid #e2e8f0; border-left-width: 4px; border-radius: 12px; padding: 1.1rem 1.4rem; }
	.icard:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.06); }

	/* Left-border accent  */
	.border-blue   { border-left-color: #3b82f6; }
	.border-purple { border-left-color: #8b5cf6; }
	.border-slate  { border-left-color: #94a3b8; }
	.border-amber  { border-left-color: #f59e0b; }
	.border-red    { border-left-color: #ef4444; }

	/* Avatar */
	.icard-avatar { width: 42px; height: 42px; border-radius: 50%; background: linear-gradient(135deg, #6366f1, #8b5cf6); color: #ffffff; display: flex; align-items: center; justify-content: center; font-size: 0.82rem; font-weight: 700; flex-shrink: 0; margin-top: 0.05rem; }

	/* Card body */
	.icard-body { flex: 1; min-width: 0; }
	.icard-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 0.5rem; }

	/* Who row */
	.icard-who { display: flex; align-items: center; gap: 0.4rem; flex-wrap: wrap; }
	.who-doctor { font-size: 0.93rem; font-weight: 700; color: #0f172a; }
	.who-spec { font-size: 0.77rem; color: #94a3b8; }
	.who-arrow { font-size: 0.85rem; color: #cbd5e1; }
	.who-patient { font-size: 0.85rem; font-weight: 600; color: #334155; background: #f1f5f9; border: 1px solid #e2e8f0; padding: 0.15rem 0.6rem; border-radius: 999px; }

	/* Badges and date */
	.icard-badges { display: flex; align-items: center; gap: 0.55rem; flex-shrink: 0; }
	.icard-date { font-size: 0.76rem; color: #94a3b8; white-space: nowrap; }

	/* Description */
	.icard-desc { font-size: 0.87rem; color: #475569; margin: 0; line-height: 1.6; }

	/* Type badges */
	.type-badge { padding: 0.2rem 0.65rem; border-radius: 999px; font-size: 0.71rem; font-weight: 700; white-space: nowrap; letter-spacing: 0.02em; }
	.type-blue   { background: #dbeafe; color: #1d4ed8; }
	.type-purple { background: #f3e8ff; color: #7e22ce; }
	.type-slate  { background: #f1f5f9; color: #475569; }
	.type-amber  { background: #fef3c7; color: #92400e; }
	.type-red    { background: #fee2e2; color: #b91c1c; }
</style>

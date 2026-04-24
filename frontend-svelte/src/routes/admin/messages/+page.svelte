<script>
	import { locale as activeLocale, uiText } from '$lib/i18n';
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let admin = null;
	let loading = true;
	let error = '';

	let allMessages = [];
	let summary = null;

	let periodDays = 30;
	let directionFilter = 'all';
	let flaggedOnly = false;
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
		await loadAudit();
	});

	async function loadAudit() {
		loading = true;
		error = '';
		try {
			const response = await api.get(`/api/admin/messages/audit?admin_id=${admin.id}`);
			allMessages = response.data.messages;
			summary = response.data.summary;
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Failed to load message audit log';
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

	function severityLabel(severity) {
		if (severity === 'high') return 'High Risk';
		if (severity === 'medium') return 'Review';
		if (severity === 'low') return 'Watch';
		return 'Clear';
	}

	function periodLabel(days) {
		if (days === 0) return 'All time';
		if (days === 7) return 'Last 7 days';
		if (days === 30) return 'Last 30 days';
		return 'Last 90 days';
	}

	function directionLabel(direction) {
		if (direction === 'patient_to_doctor') return 'Patient → Doctor';
		if (direction === 'doctor_to_patient') return 'Doctor → Patient';
		return 'Other';
	}

	function directionClass(direction) {
		if (direction === 'patient_to_doctor') return 'direction-patient';
		if (direction === 'doctor_to_patient') return 'direction-doctor';
		return 'direction-neutral';
	}

	function severityClass(severity) {
		if (severity === 'high') return 'sev-high';
		if (severity === 'medium') return 'sev-medium';
		if (severity === 'low') return 'sev-low';
		return 'sev-none';
	}

	$: cutoff = periodDays === 0 ? null : new Date(Date.now() - periodDays * 86400000);
	$: loweredQuery = searchQuery.trim().toLowerCase();
	$: filteredMessages = allMessages.filter((message) => {
		if (directionFilter !== 'all' && message.direction !== directionFilter) return false;
		if (flaggedOnly && !message.audit.flagged) return false;
		if (cutoff && new Date(message.created_at) < cutoff) return false;
		if (!loweredQuery) return true;

		return [
			message.sender_name,
			message.recipient_name,
			message.subject || '',
			message.message,
			message.preview
		].some((value) => value.toLowerCase().includes(loweredQuery));
	});
	$: flaggedInView = filteredMessages.filter((message) => message.audit.flagged).length;
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
			<a href="/admin/interventions" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/>
			</svg>
			 {uiText("Interventions", $activeLocale)}
			</a>
			<a href="/admin/messages" class="nav-item active">
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
				<h1 class="page-title">{uiText("Message Audit", $activeLocale)}</h1>
				<p class="page-sub">{uiText("Communication logging, moderation signals, and oversight across doctor-patient messaging", $activeLocale)}</p>
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
				<div class="loading-state">{uiText("Loading message audit...", $activeLocale)}</div>
			{:else}
				<div class="stats-strip">
					<div class="stat-card">
						<p class="stat-value">{filteredMessages.length}</p>
						<p class="stat-label">{uiText("Messages In View", $activeLocale)}</p>
						<p class="stat-sub">{periodLabel(periodDays)}</p>
					</div>
					<div class="stat-card danger-soft">
						<p class="stat-value danger-text">{flaggedInView}</p>
						<p class="stat-label">{uiText("Flagged For Review", $activeLocale)}</p>
						<p class="stat-sub">{uiText("potential moderation issues", $activeLocale)}</p>
					</div>
					<div class="stat-card">
						<p class="stat-value">{summary?.patient_to_doctor || 0}</p>
						<p class="stat-label">{uiText("Patient → Doctor", $activeLocale)}</p>
						<p class="stat-sub">{uiText("communications logged", $activeLocale)}</p>
					</div>
					<div class="stat-card">
						<p class="stat-value">{summary?.doctor_to_patient || 0}</p>
						<p class="stat-label">{uiText("Doctor → Patient", $activeLocale)}</p>
						<p class="stat-sub">{uiText("communications logged", $activeLocale)}</p>
					</div>
				</div>

				<div class="filter-panel">
					<div class="filter-top-row">
						<div class="period-tabs">
							{#each PERIODS as [value, label]}
								<button
									type="button"
									class="period-btn {periodDays === value ? 'active' : ''}"
									on:click={() => (periodDays = value)}
								>
									{label}
								</button>
							{/each}
						</div>
						<button
							type="button"
							class="flag-toggle {flaggedOnly ? 'active' : ''}"
							on:click={() => (flaggedOnly = !flaggedOnly)}
						>
							{flaggedOnly ? 'Showing Flagged Only' : 'Show Flagged Only'}
						</button>
					</div>

					<div class="filter-bottom-row">
						<input
							class="search-input"
							type="text"
							placeholder={uiText("Search sender, recipient, subject, or message content...", $activeLocale)}
							bind:value={searchQuery}
						/>
						<select class="filter-select" bind:value={directionFilter}>
							<option value="all">{uiText("All Directions", $activeLocale)}</option>
							<option value="patient_to_doctor">{uiText("Patient → Doctor", $activeLocale)}</option>
							<option value="doctor_to_patient">{uiText("Doctor → Patient", $activeLocale)}</option>
						</select>
					</div>
				</div>

				<div class="section-head">
					<div>
						<h2 class="section-title">{uiText("Communication Log", $activeLocale)}</h2>
						<p class="section-sub">{uiText("Hospitals often require communication logging for compliance and quality review.", $activeLocale)}</p>
					</div>
					<div class="section-meta">{filteredMessages.length} {uiText("record", $activeLocale)}{filteredMessages.length !== 1 ? 's' : ''}</div>
				</div>

				{#if filteredMessages.length === 0}
					<div class="empty-state">
						<div class="empty-icon-wrap">
				<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
					<path d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
				</svg>
			</div>
						<p class="empty-title">{uiText("No messages found", $activeLocale)}</p>
						<p class="empty-sub">{uiText("Try widening the audit window or removing filters.", $activeLocale)}</p>
					</div>
				{:else}
					<div class="audit-list">
						{#each filteredMessages as message (message.id)}
							<div class="audit-card {message.audit.flagged ? 'flagged' : ''}">
								<div class="audit-avatar">{initials(message.sender_name)}</div>
								<div class="audit-body">
									<div class="audit-top">
										<div class="audit-route">
											<span class="route-name">{message.sender_name}</span>
											<span class="route-arrow">→</span>
											<span class="route-name route-recipient">{message.recipient_name}</span>
											<span class="direction-chip {directionClass(message.direction)}">{directionLabel(message.direction)}</span>
										</div>
										<div class="audit-meta">
											<span class="read-chip {message.is_read ? 'read' : 'unread'}">{message.is_read ? 'Read' : 'Unread'}</span>
											<span class="severity-chip {severityClass(message.audit.severity)}">{severityLabel(message.audit.severity)}</span>
											<span class="audit-date" title={formatDateTime(message.created_at)}>{relativeDate(message.created_at)}</span>
										</div>
									</div>

									{#if message.subject}
										<p class="audit-subject" data-localize-skip>{message.subject}</p>
									{/if}
									<p class="audit-message" data-localize-skip>{message.preview}</p>

									{#if message.audit.flagged}
										<div class="audit-reasons">
											{#each message.audit.reasons as reason}
												<span class="reason-chip">{reason}</span>
											{/each}
											{#each message.audit.abuse_terms as term}
												<span class="reason-chip danger">{term}</span>
											{/each}
										</div>
									{/if}

									<div class="audit-footer">
										<span class="footer-item">{uiText("Logged:", $activeLocale)} {formatDateTime(message.created_at)}</span>
										<span class="footer-item">{uiText("Type:", $activeLocale)} {message.sender_type} → {message.recipient_type}</span>
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
	.page-sub { font-size: 0.8rem; color: #94a3b8; margin: 0.15rem 0 0; max-width: 720px; }
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

	.stats-strip { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 1.25rem; }
	.stat-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 1.1rem 1.2rem; }
	.danger-soft { background: linear-gradient(180deg, #fff7f7 0%, #ffffff 100%); border-color: #fecaca; }
	.stat-value { margin: 0; font-size: 1.55rem; font-weight: 700; color: #0f172a; }
	.danger-text { color: #b91c1c; }
	.stat-label { margin: 0.2rem 0 0; font-size: 0.76rem; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.05em; }
	.stat-sub { margin: 0.25rem 0 0; font-size: 0.78rem; color: #94a3b8; }

	.filter-panel { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 1rem 1.1rem; margin-bottom: 1.4rem; }
	.filter-top-row, .filter-bottom-row { display: flex; align-items: center; justify-content: space-between; gap: 0.8rem; flex-wrap: wrap; }
	.filter-bottom-row { margin-top: 0.9rem; }
	.period-tabs { display: flex; gap: 0.35rem; flex-wrap: wrap; }
	.period-btn, .flag-toggle { padding: 0.45rem 0.9rem; border-radius: 999px; border: 1px solid #e2e8f0; background: #f8fafc; color: #475569; font-size: 0.82rem; font-weight: 600; cursor: pointer; }
	.period-btn.active { background: #1d4ed8; border-color: #1d4ed8; color: #ffffff; }
	.flag-toggle.active { background: #fef2f2; border-color: #fecaca; color: #b91c1c; }
	.search-input { flex: 1; min-width: 280px; padding: 0.72rem 0.9rem; border: 1px solid #e2e8f0; border-radius: 10px; font-size: 0.88rem; background: #ffffff; }
	.filter-select { padding: 0.7rem 0.85rem; border: 1px solid #e2e8f0; border-radius: 10px; background: #ffffff; font-size: 0.85rem; color: #334155; }

	.section-head { display: flex; justify-content: space-between; align-items: flex-end; gap: 1rem; margin-bottom: 0.9rem; }
	.section-title { margin: 0; font-size: 1rem; font-weight: 700; color: #0f172a; }
	.section-sub { margin: 0.25rem 0 0; font-size: 0.82rem; color: #94a3b8; }
	.section-meta { font-size: 0.82rem; color: #64748b; }

	.empty-state { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 3.5rem 2rem; text-align: center; }
	.empty-icon-wrap { width: 56px; height: 56px; border-radius: 50%; background: #f1f5f9; border: 1.5px solid #e2e8f0; display: flex; align-items: center; justify-content: center; margin: 0 auto 0.5rem; color: #94a3b8; }
	.empty-icon-wrap svg { width: 26px; height: 26px; }
	.empty-title { margin: 0; font-size: 1rem; font-weight: 700; color: #334155; }
	.empty-sub { margin: 0.35rem 0 0; font-size: 0.84rem; color: #94a3b8; }

	.audit-list { display: flex; flex-direction: column; gap: 0.85rem; }
	.audit-card { display: flex; gap: 1rem; align-items: flex-start; background: #ffffff; border: 1px solid #e2e8f0; border-left: 4px solid #cbd5e1; border-radius: 14px; padding: 1.1rem 1.2rem; }
	.audit-card.flagged { border-left-color: #ef4444; background: linear-gradient(180deg, #fffdfd 0%, #ffffff 100%); }
	.audit-avatar { width: 42px; height: 42px; border-radius: 50%; background: linear-gradient(135deg, #1d4ed8, #0f766e); color: #ffffff; display: flex; align-items: center; justify-content: center; font-size: 0.82rem; font-weight: 700; flex-shrink: 0; }
	.audit-body { flex: 1; min-width: 0; }
	.audit-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 0.55rem; }
	.audit-route { display: flex; align-items: center; gap: 0.45rem; flex-wrap: wrap; }
	.route-name { font-size: 0.92rem; font-weight: 700; color: #0f172a; }
	.route-recipient { color: #334155; }
	.route-arrow { color: #94a3b8; }
	.audit-meta { display: flex; align-items: center; gap: 0.45rem; flex-wrap: wrap; }
	.direction-chip, .read-chip, .severity-chip, .reason-chip { padding: 0.2rem 0.6rem; border-radius: 999px; font-size: 0.72rem; font-weight: 700; white-space: nowrap; }
	.direction-patient { background: #dbeafe; color: #1d4ed8; }
	.direction-doctor { background: #dcfce7; color: #166534; }
	.direction-neutral { background: #f1f5f9; color: #475569; }
	.read { background: #f1f5f9; color: #475569; }
	.unread { background: #fef3c7; color: #92400e; }
	.sev-high { background: #fee2e2; color: #b91c1c; }
	.sev-medium { background: #fef3c7; color: #92400e; }
	.sev-low { background: #e0f2fe; color: #0369a1; }
	.sev-none { background: #ecfdf5; color: #047857; }
	.audit-date { font-size: 0.76rem; color: #94a3b8; }
	.audit-subject { margin: 0; font-size: 0.88rem; font-weight: 700; color: #1e293b; }
	.audit-message { margin: 0.35rem 0 0; font-size: 0.86rem; line-height: 1.65; color: #475569; }
	.audit-reasons { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-top: 0.8rem; }
	.reason-chip { background: #fff7ed; color: #9a3412; }
	.reason-chip.danger { background: #fee2e2; color: #b91c1c; }
	.audit-footer { display: flex; gap: 0.9rem; flex-wrap: wrap; margin-top: 0.8rem; padding-top: 0.75rem; border-top: 1px solid #f1f5f9; }
	.footer-item { font-size: 0.76rem; color: #94a3b8; }

	@media (max-width: 960px) {
		.sidebar { position: static; width: 100%; min-height: auto; }
		.admin-layout { flex-direction: column; }
		.main-content { margin-left: 0; }
		.topbar { padding: 1rem 1.25rem; align-items: flex-start; }
		.content { padding: 1.25rem; }
	}

	@media (max-width: 640px) {
		.audit-card { flex-direction: column; }
		.audit-top { flex-direction: column; align-items: flex-start; }
		.search-input { min-width: 100%; }
		.filter-select { width: 100%; }
		.filter-bottom-row { align-items: stretch; }
	}
</style>

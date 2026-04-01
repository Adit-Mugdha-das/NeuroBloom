<script>
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	import LanguagePreferencePanel from '$lib/components/LanguagePreferencePanel.svelte';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let admin = null;
	let stats = {
		total_patients: 0,
		active_patients_today: 0,
		total_doctors: 0,
		pending_doctors: 0,
		active_doctors: 0,
		completed_sessions: 0,
		total_departments: 0
	};
	let loading = true;
	let error = '';

	onMount(async () => {
		const u = $user;
		if (!u || u.role !== 'admin') {
			goto('/login');
			return;
		}
		admin = u;
		await loadStats();
	});

	async function loadStats() {
		try {
			const res = await api.get(`/api/admin/stats?admin_id=${admin.id}`);
			stats = {
				total_patients: res.data.total_patients,
				active_patients_today: res.data.active_patients_today,
				total_doctors: res.data.total_doctors,
				pending_doctors: res.data.pending_doctors,
				active_doctors: res.data.active_doctors,
				completed_sessions: res.data.completed_sessions,
				total_departments: res.data.total_departments
			};
		} catch (e) {
			error = e.response?.data?.detail || 'Failed to load stats';
		} finally {
			loading = false;
		}
	}

	function logout() {
		user.set(null);
		goto('/login');
	}
</script>

<div class="admin-layout">
	<!-- Sidebar -->
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
			<a href="/admin/dashboard" class="nav-item active">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
					<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
				</svg>
				Dashboard
			</a>
			<a href="/admin/analytics" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
					<path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
				</svg>
				System Analytics
			</a>
			<a href="/admin/doctors" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
					<path d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
				</svg>
				Doctor Management
			</a>
			<a href="/admin/patients" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
					<path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
				</svg>
				Patient Management
			</a>
			<a href="/admin/departments" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
					<path d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
				</svg>
				Departments
			</a>
			<a href="/admin/interventions" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
					<path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/>
				</svg>
				Interventions
			</a>
			<a href="/admin/messages" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
					<path d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
				</svg>
				Message Audit
			</a>
			<a href="/admin/audit-logs" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
					<path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
				</svg>
				Audit Logs
			</a>
			<a href="/admin/system-health" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
					<path d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
				</svg>
				System Health
			</a>
			<a href="/admin/notifications" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
					<path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
				</svg>
				Notification Centre
			</a>
			<a href="/admin/research-data" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
					<path d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/>
				</svg>
				Research Data
			</a>
		</nav>
		<button class="logout-btn" on:click={logout}>
			<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
			</svg>
			Sign Out
		</button>
	</aside>

	<!-- Main content -->
	<main class="main-content">
		<header class="topbar">
			<div class="topbar-left">
				<h1 class="page-title">Overview</h1>
				<span class="page-subtitle">System administration dashboard</span>
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

		{#if error}
			<div class="alert error">{error}</div>
		{/if}

		{#if loading}
			<div class="loading-grid">
				{#each Array(8) as _}
					<div class="stat-card skeleton"></div>
				{/each}
			</div>
		{:else}
			<div class="language-block">
				<LanguagePreferencePanel
					title="Language Preference"
					description="Choose the admin workspace language for navigation, system dashboards, and visible metrics."
				/>
			</div>

			<div class="stats-grid">
				<div class="stat-card">
					<div class="stat-icon-wrap blue">
						<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
							<path d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
						</svg>
					</div>
					<div class="stat-body">
						<p class="stat-label">Total Patients</p>
						<p class="stat-value">{stats.total_patients}</p>
					</div>
				</div>
				<div class="stat-card">
					<div class="stat-icon-wrap green">
						<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
							<path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
						</svg>
					</div>
					<div class="stat-body">
						<p class="stat-label">Active Patient Accounts</p>
						<p class="stat-value">{stats.active_patients}</p>
					</div>
				</div>
				<div class="stat-card">
					<div class="stat-icon-wrap emerald">
						<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
							<path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
						</svg>
					</div>
					<div class="stat-body">
						<p class="stat-label">Active Patients Today</p>
						<p class="stat-value">{stats.active_patients_today}</p>
					</div>
				</div>
				<div class="stat-card">
					<div class="stat-icon-wrap purple">
						<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
							<path d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
						</svg>
					</div>
					<div class="stat-body">
						<p class="stat-label">Total Doctors</p>
						<p class="stat-value">{stats.total_doctors}</p>
					</div>
				</div>
				<div class="stat-card">
					<div class="stat-icon-wrap amber">
						<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
							<path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
						</svg>
					</div>
					<div class="stat-body">
						<p class="stat-label">Pending Approvals</p>
						<p class="stat-value">{stats.pending_doctors}</p>
					</div>
				</div>
				<div class="stat-card">
					<div class="stat-icon-wrap teal">
						<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
							<path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>
						</svg>
					</div>
					<div class="stat-body">
						<p class="stat-label">Active Doctors</p>
						<p class="stat-value">{stats.active_doctors}</p>
					</div>
				</div>
				<div class="stat-card">
					<div class="stat-icon-wrap slate">
						<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
							<path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
						</svg>
					</div>
					<div class="stat-body">
						<p class="stat-label">Sessions Completed</p>
						<p class="stat-value">{stats.completed_sessions}</p>
					</div>
				</div>
				<div class="stat-card">
					<div class="stat-icon-wrap navy">
						<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
							<path d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
						</svg>
					</div>
					<div class="stat-body">
						<p class="stat-label">Departments</p>
						<p class="stat-value">{stats.total_departments}</p>
					</div>
				</div>
			</div>

			<section class="overview-panel">
				<div class="overview-copy">
					<p class="panel-kicker">Admin Workspace</p>
					<h2>System overview</h2>
					<p class="panel-copy">Detailed system metrics, task usage, fatigue trends, and performance charts are available in the dedicated analytics module for a focused administrative view.</p>
				</div>
				<a href="/admin/analytics" class="analytics-link-card">
					<div class="analytics-link-icon">
						<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
							<path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
						</svg>
					</div>
					<div>
						<h3>Open System Analytics</h3>
						<p>View system-wide metrics, high-risk patients, most-used tasks, and core trend charts.</p>
					</div>
				</a>
			</section>

			<section class="quick-actions">
				<h2>Quick Actions</h2>
				<div class="action-cards">
					<a href="/admin/analytics" class="action-card">
						<div class="action-icon blue">
							<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
								<path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
							</svg>
						</div>
						<div>
							<h3>System Analytics</h3>
							<p>Access the analytics module with system-wide charts and performance metrics.</p>
						</div>
					</a>
					<a href="/admin/doctors" class="action-card">
						<div class="action-icon purple">
							<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
								<path d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
							</svg>
						</div>
						<div>
							<h3>Manage Doctors</h3>
							<p>Approve registrations, suspend or activate clinician accounts.</p>
							{#if stats.pending_doctors > 0}
								<span class="badge amber">{stats.pending_doctors} pending</span>
							{/if}
						</div>
					</a>
					<a href="/admin/patients" class="action-card">
						<div class="action-icon teal">
							<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
								<path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
							</svg>
						</div>
						<div>
							<h3>Manage Patients</h3>
							<p>Review and administer all patient accounts in the system.</p>
						</div>
					</a>
					<a href="/admin/departments" class="action-card">
						<div class="action-icon navy">
							<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
								<path d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
							</svg>
						</div>
						<div>
							<h3>Manage Departments</h3>
							<p>Create departments, assign clinicians, and review patient allocation.</p>
						</div>
					</a>
				</div>
			</section>
		{/if}
	</main>
</div>

<style>
	.language-block {
		margin-bottom: 1.5rem;
	}

	.admin-layout {
		display: flex;
		min-height: 100vh;
		background: #f1f5f9;
		font-family: 'Inter', system-ui, sans-serif;
	}

	/* ── Sidebar ── */
	.sidebar {
		width: 248px;
		min-height: 100vh;
		background: #0f172a;
		color: #e2e8f0;
		display: flex;
		flex-direction: column;
		padding: 0;
		position: fixed;
		top: 0;
		left: 0;
		bottom: 0;
		z-index: 10;
	}

	.sidebar-brand {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 1.25rem;
		background: #020617;
		border-bottom: 1px solid #1e293b;
	}

	.brand-mark {
		width: 32px;
		height: 32px;
		background: #1d4ed8;
		border-radius: 7px;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}

	.brand-mark svg {
		width: 16px;
		height: 16px;
		stroke: white;
	}

	.brand-name {
		font-weight: 700;
		font-size: 0.9rem;
		letter-spacing: 0.01em;
		color: #f1f5f9;
	}

	.sidebar-nav {
		flex: 1;
		padding: 1rem 0.75rem;
		display: flex;
		flex-direction: column;
		gap: 0.15rem;
		overflow-y: auto;
	}

	.nav-item {
		display: flex;
		align-items: center;
		gap: 0.7rem;
		padding: 0.58rem 0.85rem;
		border-radius: 6px;
		color: #94a3b8;
		text-decoration: none;
		font-size: 0.875rem;
		font-weight: 500;
		transition: background 0.15s, color 0.15s;
	}

	.nav-item:hover { background: #1e293b; color: #e2e8f0; }

	.nav-item.active { background: #1e3a8a; color: #bfdbfe; }

	.nav-icon {
		width: 17px;
		height: 17px;
		flex-shrink: 0;
	}

	.logout-btn {
		margin: 0.75rem;
		padding: 0.58rem 0.85rem;
		background: transparent;
		border: 1px solid #1e293b;
		border-radius: 6px;
		color: #64748b;
		cursor: pointer;
		font-size: 0.875rem;
		font-weight: 500;
		display: flex;
		align-items: center;
		gap: 0.7rem;
		transition: background 0.15s, color 0.15s, border-color 0.15s;
		width: calc(100% - 1.5rem);
	}

	.logout-btn:hover { background: #450a0a; color: #fca5a5; border-color: #7f1d1d; }

	/* ── Main ── */
	.main-content {
		flex: 1;
		margin-left: 248px;
		padding: 0;
		display: flex;
		flex-direction: column;
	}

	.topbar {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem 2rem;
		background: white;
		border-bottom: 1px solid #e2e8f0;
		position: sticky;
		top: 0;
		z-index: 5;
	}

	.topbar-left { display: flex; flex-direction: column; gap: 0.1rem; }

	.page-title { font-size: 1.2rem; font-weight: 700; color: #0f172a; margin: 0; line-height: 1.2; }

	.page-subtitle { font-size: 0.75rem; color: #94a3b8; font-weight: 400; }

	.admin-info { display: flex; align-items: center; gap: 0.75rem; }

	.admin-avatar {
		width: 36px;
		height: 36px;
		background: #eff6ff;
		border: 1px solid #bfdbfe;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}

	.admin-avatar svg { width: 17px; height: 17px; stroke: #1d4ed8; }

	.admin-details { display: flex; flex-direction: column; gap: 0.1rem; }

	.admin-name { font-size: 0.875rem; font-weight: 600; color: #1e293b; }

	.admin-role {
		font-size: 0.7rem;
		color: #64748b;
		font-weight: 500;
		text-transform: uppercase;
		letter-spacing: 0.06em;
	}

	.alert.error {
		margin: 1.5rem 2rem 0;
		padding: 0.875rem 1.25rem;
		background: #fef2f2;
		border: 1px solid #fecaca;
		border-left: 4px solid #dc2626;
		border-radius: 6px;
		color: #991b1b;
		font-size: 0.875rem;
	}

	/* ── Stats ── */
	.stats-grid,
	.loading-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
		gap: 1.25rem;
		padding: 2rem 2rem 0;
	}

	.stat-card {
		background: white;
		border-radius: 10px;
		padding: 1.25rem;
		display: flex;
		align-items: center;
		gap: 1rem;
		box-shadow: 0 1px 3px rgba(0,0,0,0.06);
		border: 1px solid #e2e8f0;
		transition: box-shadow 0.15s;
	}

	.stat-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }

	.stat-card.skeleton { height: 90px; background: #f1f5f9; border-color: transparent; animation: pulse 1.4s infinite; }

	.stat-icon-wrap {
		width: 44px;
		height: 44px;
		border-radius: 10px;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}

	.stat-icon-wrap svg { width: 22px; height: 22px; }

	.stat-icon-wrap.blue    { background: #eff6ff; color: #1d4ed8; }
	.stat-icon-wrap.green   { background: #f0fdf4; color: #16a34a; }
	.stat-icon-wrap.emerald { background: #ecfdf5; color: #059669; }
	.stat-icon-wrap.purple  { background: #faf5ff; color: #7c3aed; }
	.stat-icon-wrap.amber   { background: #fffbeb; color: #d97706; }
	.stat-icon-wrap.teal    { background: #f0fdfa; color: #0f766e; }
	.stat-icon-wrap.slate   { background: #f8fafc; color: #475569; }
	.stat-icon-wrap.navy    { background: #eff6ff; color: #1e3a8a; }

	.stat-label {
		font-size: 0.72rem;
		color: #64748b;
		margin: 0 0 0.2rem;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		font-weight: 500;
	}

	.stat-value { font-size: 1.875rem; font-weight: 700; color: #0f172a; margin: 0; line-height: 1; }

	/* ── Overview panel ── */
	.panel-kicker {
		margin: 0 0 0.35rem;
		font-size: 0.7rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #1d4ed8;
	}

	.panel-copy {
		margin: 0.35rem 0 0;
		max-width: 48rem;
		font-size: 0.875rem;
		line-height: 1.6;
		color: #64748b;
	}

	.overview-panel {
		margin: 2rem 2rem 0;
		padding: 1.5rem;
		display: grid;
		grid-template-columns: minmax(0, 1.4fr) minmax(280px, 0.9fr);
		gap: 1.5rem;
		background: white;
		border: 1px solid #e2e8f0;
		border-radius: 12px;
		box-shadow: 0 1px 3px rgba(0,0,0,0.06);
	}

	.overview-copy h2 { margin: 0; font-size: 1.1rem; font-weight: 600; color: #0f172a; }

	.analytics-link-card {
		display: flex;
		gap: 1rem;
		align-items: flex-start;
		padding: 1.1rem 1.25rem;
		border-radius: 10px;
		text-decoration: none;
		background: #eff6ff;
		border: 1px solid #bfdbfe;
		color: inherit;
		transition: background 0.15s;
	}

	.analytics-link-card:hover { background: #dbeafe; }

	.analytics-link-icon {
		width: 40px;
		height: 40px;
		background: #1d4ed8;
		border-radius: 8px;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}

	.analytics-link-icon svg { width: 20px; height: 20px; stroke: white; }

	.analytics-link-card h3 { margin: 0; font-size: 0.95rem; font-weight: 600; color: #1e3a8a; }

	.analytics-link-card p { margin: 0.3rem 0 0; font-size: 0.84rem; line-height: 1.5; color: #475569; }

	/* ── Quick actions ── */
	.quick-actions { padding: 2rem; }

	.quick-actions h2 {
		font-size: 0.72rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: #64748b;
		margin: 0 0 1rem;
	}

	.action-cards {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		gap: 1rem;
	}

	.action-card {
		display: flex;
		align-items: flex-start;
		gap: 1rem;
		padding: 1.25rem;
		background: white;
		border-radius: 10px;
		text-decoration: none;
		color: inherit;
		box-shadow: 0 1px 3px rgba(0,0,0,0.06);
		transition: box-shadow 0.15s, transform 0.15s;
		border: 1px solid #e2e8f0;
	}

	.action-card:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }

	.action-icon {
		width: 40px;
		height: 40px;
		border-radius: 10px;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}

	.action-icon svg { width: 20px; height: 20px; }

	.action-icon.blue   { background: #eff6ff; color: #1d4ed8; }
	.action-icon.purple { background: #faf5ff; color: #7c3aed; }
	.action-icon.teal   { background: #f0fdfa; color: #0f766e; }
	.action-icon.navy   { background: #eff6ff; color: #1e3a8a; }

	.action-card h3 { font-size: 0.95rem; font-weight: 600; color: #1e293b; margin: 0 0 0.3rem; }
	.action-card p  { font-size: 0.84rem; color: #64748b; margin: 0 0 0.5rem; line-height: 1.5; }

	.badge {
		display: inline-block;
		padding: 0.2rem 0.6rem;
		border-radius: 99px;
		font-size: 0.72rem;
		font-weight: 600;
	}

	.badge.amber { background: #fffbeb; color: #d97706; border: 1px solid #fde68a; }

	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.4; }
	}

	@media (max-width: 1100px) {
		.overview-panel { grid-template-columns: 1fr; }
	}

	@media (max-width: 720px) {
		.stats-grid,
		.loading-grid,
		.quick-actions { padding-left: 1rem; padding-right: 1rem; }
		.topbar { padding-left: 1rem; padding-right: 1rem; }
	}
</style>

<script>
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let admin = null;
	let stats = { total_patients: 0, active_patients: 0, total_doctors: 0, pending_doctors: 0, active_doctors: 0, total_departments: 0 };
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
			stats = res.data;
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
			<span class="brand-icon">🏥</span>
			<span class="brand-name">NeuroBloom Admin</span>
		</div>
		<nav class="sidebar-nav">
			<a href="/admin/dashboard" class="nav-item active">
				<span class="nav-icon">📊</span> Dashboard
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
		</nav>
		<button class="logout-btn" on:click={logout}>
			<span>🚪</span> Logout
		</button>
	</aside>

	<!-- Main content -->
	<main class="main-content">
		<header class="topbar">
			<h1 class="page-title">Dashboard</h1>
			<div class="admin-info">
				<span class="admin-avatar">🏥</span>
				<span>{admin?.full_name || admin?.email}</span>
			</div>
		</header>

		{#if error}
			<div class="alert error">{error}</div>
		{/if}

		{#if loading}
			<div class="loading-grid">
				{#each Array(6) as _}
					<div class="stat-card skeleton"></div>
				{/each}
			</div>
		{:else}
			<!-- Stats grid -->
			<div class="stats-grid">
				<div class="stat-card blue">
					<div class="stat-icon">👥</div>
					<div class="stat-body">
						<p class="stat-label">Total Patients</p>
						<p class="stat-value">{stats.total_patients}</p>
					</div>
				</div>
				<div class="stat-card green">
					<div class="stat-icon">✅</div>
					<div class="stat-body">
						<p class="stat-label">Active Patients</p>
						<p class="stat-value">{stats.active_patients}</p>
					</div>
				</div>
				<div class="stat-card purple">
					<div class="stat-icon">👨‍⚕️</div>
					<div class="stat-body">
						<p class="stat-label">Total Doctors</p>
						<p class="stat-value">{stats.total_doctors}</p>
					</div>
				</div>
				<div class="stat-card orange">
					<div class="stat-icon">⏳</div>
					<div class="stat-body">
						<p class="stat-label">Pending Approvals</p>
						<p class="stat-value">{stats.pending_doctors}</p>
					</div>
				</div>
				<div class="stat-card teal">
					<div class="stat-icon">🩺</div>
					<div class="stat-body">
						<p class="stat-label">Active Doctors</p>
						<p class="stat-value">{stats.active_doctors}</p>
					</div>
				</div>
				<div class="stat-card navy">
					<div class="stat-icon">🏢</div>
					<div class="stat-body">
						<p class="stat-label">Departments</p>
						<p class="stat-value">{stats.total_departments}</p>
					</div>
				</div>
			</div>

			<!-- Quick actions -->
			<section class="quick-actions">
				<h2>Quick Actions</h2>
				<div class="action-cards">
					<a href="/admin/doctors" class="action-card">
						<span class="action-icon">👨‍⚕️</span>
						<div>
							<h3>Manage Doctors</h3>
							<p>Approve registrations, suspend or activate doctor accounts</p>
							{#if stats.pending_doctors > 0}
								<span class="badge orange">{stats.pending_doctors} pending</span>
							{/if}
						</div>
					</a>
					<a href="/admin/patients" class="action-card">
						<span class="action-icon">👤</span>
						<div>
							<h3>Manage Patients</h3>
							<p>View and control all patient accounts in the system</p>
						</div>
					</a>
					<a href="/admin/departments" class="action-card">
						<span class="action-icon">🏢</span>
						<div>
							<h3>Manage Departments</h3>
							<p>Create departments, assign doctors, and track patient counts</p>
						</div>
					</a>
				</div>
			</section>
		{/if}
	</main>
</div>

<style>
	.admin-layout {
		display: flex;
		min-height: 100vh;
		background: #f0f4f8;
		font-family: 'Inter', sans-serif;
	}

	/* ── Sidebar ── */
	.sidebar {
		width: 240px;
		min-height: 100vh;
		background: #1e293b;
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
		gap: 0.6rem;
		padding: 1.4rem 1.2rem;
		background: #0f172a;
		font-weight: 700;
		font-size: 1rem;
		letter-spacing: 0.02em;
	}

	.brand-icon { font-size: 1.4rem; }

	.sidebar-nav {
		flex: 1;
		padding: 1rem 0.75rem;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.nav-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.65rem 0.9rem;
		border-radius: 8px;
		color: #94a3b8;
		text-decoration: none;
		font-size: 0.9rem;
		font-weight: 500;
		transition: all 0.2s;
	}

	.nav-item:hover,
	.nav-item.active {
		background: #334155;
		color: #f1f5f9;
	}

	.nav-icon { font-size: 1.1rem; }

	.logout-btn {
		margin: 0.75rem;
		padding: 0.65rem 0.9rem;
		background: transparent;
		border: 1px solid #334155;
		border-radius: 8px;
		color: #94a3b8;
		cursor: pointer;
		font-size: 0.9rem;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		transition: all 0.2s;
	}

	.logout-btn:hover { background: #7f1d1d; color: #fca5a5; border-color: #7f1d1d; }

	/* ── Main ── */
	.main-content {
		flex: 1;
		margin-left: 240px;
		padding: 0;
		display: flex;
		flex-direction: column;
	}

	.topbar {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1.25rem 2rem;
		background: white;
		border-bottom: 1px solid #e2e8f0;
		position: sticky;
		top: 0;
		z-index: 5;
	}

	.page-title { font-size: 1.4rem; font-weight: 700; color: #1e293b; margin: 0; }

	.admin-info {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.9rem;
		color: #475569;
	}

	.admin-avatar { font-size: 1.3rem; }

	.alert.error {
		margin: 1.5rem 2rem 0;
		padding: 0.9rem 1.2rem;
		background: #fef2f2;
		border: 1px solid #fecaca;
		border-radius: 8px;
		color: #b91c1c;
	}

	/* ── Stats ── */
	.stats-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
		gap: 1.25rem;
		padding: 2rem 2rem 0;
	}

	.loading-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
		gap: 1.25rem;
		padding: 2rem 2rem 0;
	}

	.stat-card {
		background: white;
		border-radius: 12px;
		padding: 1.4rem 1.2rem;
		display: flex;
		align-items: center;
		gap: 1rem;
		box-shadow: 0 1px 4px rgba(0,0,0,0.07);
		border-top: 3px solid transparent;
	}

	.stat-card.blue  { border-top-color: #3b82f6; }
	.stat-card.green { border-top-color: #22c55e; }
	.stat-card.purple{ border-top-color: #a855f7; }
	.stat-card.orange{ border-top-color: #f97316; }
	.stat-card.teal  { border-top-color: #14b8a6; }
	.stat-card.navy  { border-top-color: #1e3a8a; }
	.stat-card.skeleton { height: 96px; background: #f1f5f9; animation: pulse 1.4s infinite; }

	.stat-icon { font-size: 2rem; }
	.stat-label { font-size: 0.78rem; color: #64748b; margin: 0 0 0.25rem; text-transform: uppercase; letter-spacing: 0.05em; }
	.stat-value { font-size: 2rem; font-weight: 700; color: #1e293b; margin: 0; }

	/* ── Quick actions ── */
	.quick-actions {
		padding: 2rem;
	}

	.quick-actions h2 {
		font-size: 1.1rem;
		font-weight: 600;
		color: #1e293b;
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
		padding: 1.4rem;
		background: white;
		border-radius: 12px;
		text-decoration: none;
		color: inherit;
		box-shadow: 0 1px 4px rgba(0,0,0,0.07);
		transition: transform 0.2s, box-shadow 0.2s;
		border: 1px solid #e2e8f0;
	}

	.action-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.12); }

	.action-icon { font-size: 2rem; flex-shrink: 0; }

	.action-card h3 { font-size: 1rem; font-weight: 600; color: #1e293b; margin: 0 0 0.3rem; }
	.action-card p { font-size: 0.85rem; color: #64748b; margin: 0 0 0.5rem; }

	.badge {
		display: inline-block;
		padding: 0.2rem 0.6rem;
		border-radius: 99px;
		font-size: 0.75rem;
		font-weight: 600;
	}

	.badge.orange { background: #fff7ed; color: #c2410c; }

	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.4; }
	}
</style>

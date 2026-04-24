<script>
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let admin = null;
	let departments = [];
	let loading = true;
	let saving = false;
	let error = '';
	let successMsg = '';
	let form = { name: '', description: '' };

	onMount(async () => {
		const currentUser = $user;
		if (!currentUser || currentUser.role !== 'admin') {
			goto('/login');
			return;
		}

		admin = currentUser;
		await loadDepartments();
	});

	async function loadDepartments() {
		loading = true;
		error = '';
		try {
			const response = await api.get(`/api/admin/departments?admin_id=${admin.id}`);
			departments = response.data.departments;
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Failed to load departments';
		} finally {
			loading = false;
		}
	}

	async function createDepartment() {
		if (!form.name.trim()) {
			error = 'Department name is required.';
			return;
		}

		saving = true;
		try {
			const response = await api.post(`/api/admin/departments?admin_id=${admin.id}`, {
				name: form.name,
				description: form.description
			});
			successMsg = response.data.message;
			form = { name: '', description: '' };
			await loadDepartments();
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Failed to create department';
		} finally {
			saving = false;
		}
	}

	function clearMessages() {
		error = '';
		successMsg = '';
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
			<a href="/admin/dashboard" class="nav-item">
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
			<a href="/admin/departments" class="nav-item active">
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
				Notification Center
			</a>
			<a href="/admin/research-data" class="nav-item">
				<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
					<path d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/>
				</svg>
				Research Data
			</a>
		</nav>
		<button class="logout-btn" on:click={() => { user.set(null); goto('/login'); }}>
			<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
			</svg>
			Sign Out
		</button>
	</aside>

	<main class="main-content">
		<header class="topbar">
			<div>
				<h1 class="page-title">Department Management</h1>
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
				<div class="alert error">
					{error}
					<button class="close-btn" on:click={clearMessages}>x</button>
				</div>
			{/if}
			{#if successMsg}
				<div class="alert success">
					{successMsg}
					<button class="close-btn" on:click={clearMessages}>x</button>
				</div>
			{/if}

			<section class="create-card">
				<h2>Create Department</h2>
				<div class="form-grid">
					<input type="text" placeholder="Department name" bind:value={form.name} />
					<input type="text" placeholder="Description (optional)" bind:value={form.description} />
					<button class="primary-btn" on:click={createDepartment} disabled={saving}>
						{saving ? 'Saving...' : 'Create Department'}
					</button>
				</div>
			</section>

			{#if loading}
				<div class="loading-msg">Loading departments...</div>
			{:else if departments.length === 0}
				<div class="empty-state">
					<p>No departments created yet.</p>
				</div>
			{:else}
				<div class="department-grid">
					{#each departments as department (department.id)}
						<div class="department-card">
							<h3>{department.name}</h3>
							<p class="department-desc">{department.description || 'No description provided.'}</p>
							<div class="metric-row">
								<div>
									<p class="metric-value">{department.doctor_count}</p>
									<p class="metric-label">Doctors</p>
								</div>
								<div>
									<p class="metric-value">{department.patient_count}</p>
									<p class="metric-label">Patients</p>
								</div>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</div>
	</main>
</div>

<style>
	.admin-layout { display: flex; min-height: 100vh; background: #f0f4f8; font-family: 'Inter', sans-serif; }
	.sidebar { width: 240px; min-height: 100vh; background: #1e293b; color: #e2e8f0; display: flex; flex-direction: column; position: fixed; top: 0; left: 0; bottom: 0; }
	.sidebar-brand { display: flex; align-items: center; gap: 0.6rem; padding: 1.4rem 1.2rem; background: #0f172a; font-weight: 700; font-size: 1rem; }
	.brand-mark { width: 28px; height: 28px; background: #1d4ed8; border-radius: 7px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
	.brand-mark svg { width: 16px; height: 16px; stroke: white; }
	.sidebar-nav { flex: 1; padding: 1rem 0.75rem; display: flex; flex-direction: column; gap: 0.25rem; }
	.nav-item { display: flex; align-items: center; gap: 0.75rem; padding: 0.65rem 0.9rem; border-radius: 8px; color: #94a3b8; text-decoration: none; font-size: 0.9rem; font-weight: 500; transition: background .15s, color .15s; }
	.nav-item:hover { background: #1e293b; color: #f1f5f9; }
	.nav-item.active { background: #1d4ed8; color: #ffffff; }
	.nav-icon { width: 17px; height: 17px; flex-shrink: 0; }
	.logout-btn { margin: 0.75rem; padding: 0.65rem 0.9rem; background: transparent; border: 1px solid #334155; border-radius: 8px; color: #94a3b8; cursor: pointer; font-size: 0.9rem; display: flex; align-items: center; gap: 0.5rem; }
	.logout-btn:hover { background: #1e293b; color: #f1f5f9; }
	.main-content { flex: 1; margin-left: 240px; }
	.topbar { display: flex; justify-content: space-between; align-items: center; padding: 1.25rem 2rem; background: white; border-bottom: 1px solid #e2e8f0; }
	.page-title { font-size: 1.4rem; font-weight: 700; color: #1e293b; margin: 0; }
	.admin-info { display: flex; align-items: center; gap: 0.75rem; }
	.admin-avatar { width: 36px; height: 36px; background: #e0e7ff; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
	.admin-avatar svg { width: 18px; height: 18px; stroke: #1d4ed8; }
	.admin-details { display: flex; flex-direction: column; }
	.admin-name { font-size: 0.9rem; font-weight: 600; color: #1e293b; }
	.admin-role { font-size: 0.75rem; color: #64748b; }
	.content { padding: 2rem; }
	.alert { padding: 0.9rem 1.2rem; border-radius: 8px; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center; }
	.alert.error { background: #fef2f2; border: 1px solid #fecaca; color: #b91c1c; }
	.alert.success { background: #f0fdf4; border: 1px solid #bbf7d0; color: #166534; }
	.close-btn { background: none; border: none; cursor: pointer; }
	.create-card { background: white; border-radius: 12px; padding: 1.5rem; box-shadow: 0 1px 4px rgba(0,0,0,.07); margin-bottom: 1.5rem; }
	.create-card h2 { margin: 0 0 1rem; font-size: 1.1rem; }
	.form-grid { display: grid; grid-template-columns: 1.3fr 1.7fr auto; gap: 0.75rem; }
	.form-grid input { padding: 0.7rem 0.9rem; border: 1px solid #dbe2ea; border-radius: 8px; font-size: 0.9rem; }
	.primary-btn { background: #1e293b; color: white; border: none; border-radius: 8px; padding: 0.7rem 1rem; cursor: pointer; font-weight: 600; }
	.primary-btn:disabled { opacity: .6; cursor: not-allowed; }
	.department-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1rem; }
	.department-card { background: white; border-radius: 12px; padding: 1.4rem; box-shadow: 0 1px 4px rgba(0,0,0,.07); border-top: 3px solid #1d4ed8; }
	.department-card h3 { margin: 0 0 0.4rem; font-size: 1.05rem; color: #1e293b; }
	.department-desc { margin: 0 0 1rem; font-size: 0.88rem; color: #64748b; min-height: 2.5rem; }
	.metric-row { display: flex; gap: 1.5rem; }
	.metric-value { margin: 0; font-size: 1.5rem; font-weight: 700; color: #1e293b; }
	.metric-label { margin: 0.2rem 0 0; font-size: 0.75rem; text-transform: uppercase; color: #64748b; }
	.loading-msg, .empty-state { padding: 3rem; text-align: center; color: #64748b; }
</style>
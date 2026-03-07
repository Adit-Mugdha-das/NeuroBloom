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
			<a href="/admin/departments" class="nav-item active">
				<span class="nav-icon">🏢</span> Departments
			</a>
			<a href="/admin/interventions" class="nav-item">
				<span class="nav-icon">🩺</span> Interventions
			</a>
		</nav>
		<button class="logout-btn" on:click={() => { user.set(null); goto('/login'); }}>
			<span>🚪</span> Logout
		</button>
	</aside>

	<main class="main-content">
		<header class="topbar">
			<h1 class="page-title">Department Management</h1>
			<div class="admin-info">
				<span class="admin-avatar">🏥</span>
				<span>{admin?.full_name || admin?.email}</span>
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
	.brand-icon { font-size: 1.4rem; }
	.sidebar-nav { flex: 1; padding: 1rem 0.75rem; display: flex; flex-direction: column; gap: 0.25rem; }
	.nav-item { display: flex; align-items: center; gap: 0.75rem; padding: 0.65rem 0.9rem; border-radius: 8px; color: #94a3b8; text-decoration: none; font-size: 0.9rem; font-weight: 500; }
	.nav-item:hover, .nav-item.active { background: #334155; color: #f1f5f9; }
	.nav-icon { font-size: 1.1rem; }
	.logout-btn { margin: 0.75rem; padding: 0.65rem 0.9rem; background: transparent; border: 1px solid #334155; border-radius: 8px; color: #94a3b8; cursor: pointer; font-size: 0.9rem; display: flex; align-items: center; gap: 0.5rem; }
	.main-content { flex: 1; margin-left: 240px; }
	.topbar { display: flex; justify-content: space-between; align-items: center; padding: 1.25rem 2rem; background: white; border-bottom: 1px solid #e2e8f0; }
	.page-title { font-size: 1.4rem; font-weight: 700; color: #1e293b; margin: 0; }
	.admin-info { display: flex; align-items: center; gap: 0.5rem; font-size: 0.9rem; color: #475569; }
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
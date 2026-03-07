<script>
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let admin = null;
	let patients = [];
	let loading = true;
	let error = '';
	let successMsg = '';
	let searchQuery = '';
	let filter = 'all'; // 'all' | 'active' | 'inactive'

	onMount(async () => {
		const u = $user;
		if (!u || u.role !== 'admin') { goto('/login'); return; }
		admin = u;
		await loadPatients();
	});

	async function loadPatients() {
		loading = true;
		error = '';
		try {
			const res = await api.get(`/api/admin/patients?admin_id=${admin.id}`);
			patients = res.data.patients;
		} catch (e) {
			error = e.response?.data?.detail || 'Failed to load patients';
		} finally {
			loading = false;
		}
	}

	async function deactivatePatient(id) {
		if (!confirm('Deactivate this patient account?')) return;
		try {
			await api.patch(`/api/admin/patients/${id}/deactivate?admin_id=${admin.id}`);
			successMsg = 'Patient account deactivated.';
			await loadPatients();
		} catch (e) {
			error = e.response?.data?.detail || 'Action failed';
		}
	}

	async function activatePatient(id) {
		try {
			await api.patch(`/api/admin/patients/${id}/activate?admin_id=${admin.id}`);
			successMsg = 'Patient account activated.';
			await loadPatients();
		} catch (e) {
			error = e.response?.data?.detail || 'Action failed';
		}
	}

	function clearMessages() { error = ''; successMsg = ''; }

	$: filtered = patients.filter(p => {
		const matchesFilter =
			filter === 'all' ? true :
			filter === 'active' ? p.is_active :
			!p.is_active;
		const q = searchQuery.toLowerCase();
		const matchesSearch = !q ||
			(p.email || '').toLowerCase().includes(q) ||
			(p.full_name || '').toLowerCase().includes(q) ||
			(p.diagnosis || '').toLowerCase().includes(q);
		return matchesFilter && matchesSearch;
	});
</script>

<div class="admin-layout">
	<!-- Sidebar -->
	<aside class="sidebar">
		<div class="sidebar-brand">
			<span class="brand-icon">🏥</span>
			<span class="brand-name">NeuroBloom Admin</span>
		</div>
		<nav class="sidebar-nav">
			<a href="/admin/dashboard" class="nav-item">
				<span class="nav-icon">📊</span> Dashboard
			</a>
			<a href="/admin/doctors" class="nav-item">
				<span class="nav-icon">👨‍⚕️</span> Doctor Management
			</a>
			<a href="/admin/patients" class="nav-item active">
				<span class="nav-icon">👤</span> Patient Management
			</a>
		</nav>
		<button class="logout-btn" on:click={() => { user.set(null); goto('/login'); }}>
			<span>🚪</span> Logout
		</button>
	</aside>

	<main class="main-content">
		<header class="topbar">
			<h1 class="page-title">Patient Management</h1>
			<div class="admin-info">
				<span class="admin-avatar">🏥</span>
				<span>{admin?.full_name || admin?.email}</span>
			</div>
		</header>

		<div class="content">
			{#if error}
				<div class="alert error" role="alert">
					{error}
					<button class="close-btn" on:click={clearMessages}>✕</button>
				</div>
			{/if}
			{#if successMsg}
				<div class="alert success" role="status">
					{successMsg}
					<button class="close-btn" on:click={clearMessages}>✕</button>
				</div>
			{/if}

			<!-- Search & filter bar -->
			<div class="toolbar">
				<input
					class="search-input"
					type="text"
					placeholder="Search by name, email or diagnosis…"
					bind:value={searchQuery}
				/>
				<div class="filter-tabs">
					{#each [['all','All'],['active','Active'],['inactive','Inactive']] as [val, label]}
						<button
							class="tab-btn {filter === val ? 'active' : ''}"
							on:click={() => filter = val}
						>{label}</button>
					{/each}
				</div>
			</div>

			{#if loading}
				<div class="loading-msg">Loading patients…</div>
			{:else if filtered.length === 0}
				<div class="empty-state">
					<span class="empty-icon">👤</span>
					<p>No patients found.</p>
				</div>
			{:else}
				<div class="summary-line">{filtered.length} patient{filtered.length !== 1 ? 's' : ''}</div>
				<div class="table-wrapper">
					<table>
						<thead>
							<tr>
								<th>Patient</th>
								<th>Email</th>
								<th>Date of Birth</th>
								<th>Diagnosis</th>
								<th>Data Sharing</th>
								<th>Status</th>
								<th>Actions</th>
							</tr>
						</thead>
						<tbody>
							{#each filtered as p (p.id)}
								<tr>
									<td class="name-cell">
										<span class="avatar">👤</span>
										{p.full_name || '(no name)'}
									</td>
									<td>{p.email}</td>
									<td>{p.date_of_birth || '—'}</td>
									<td>{p.diagnosis || '—'}</td>
									<td>
										<span class="status {p.consent_to_share ? 'green' : 'gray'}">
											{p.consent_to_share ? 'Yes' : 'No'}
										</span>
									</td>
									<td>
										<span class="status {p.is_active ? 'green' : 'red'}">
											{p.is_active ? 'Active' : 'Inactive'}
										</span>
									</td>
									<td class="actions-cell">
										{#if p.is_active}
											<button class="btn-sm red" on:click={() => deactivatePatient(p.id)}>Deactivate</button>
										{:else}
											<button class="btn-sm green" on:click={() => activatePatient(p.id)}>Activate</button>
										{/if}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</div>
	</main>
</div>

<style>
	.admin-layout { display: flex; min-height: 100vh; background: #f0f4f8; font-family: 'Inter', sans-serif; }

	.sidebar { width: 240px; min-height: 100vh; background: #1e293b; color: #e2e8f0; display: flex; flex-direction: column; position: fixed; top: 0; left: 0; bottom: 0; z-index: 10; }
	.sidebar-brand { display: flex; align-items: center; gap: .6rem; padding: 1.4rem 1.2rem; background: #0f172a; font-weight: 700; font-size: 1rem; }
	.brand-icon { font-size: 1.4rem; }
	.sidebar-nav { flex: 1; padding: 1rem .75rem; display: flex; flex-direction: column; gap: .25rem; }
	.nav-item { display: flex; align-items: center; gap: .75rem; padding: .65rem .9rem; border-radius: 8px; color: #94a3b8; text-decoration: none; font-size: .9rem; font-weight: 500; transition: all .2s; }
	.nav-item:hover, .nav-item.active { background: #334155; color: #f1f5f9; }
	.nav-icon { font-size: 1.1rem; }
	.logout-btn { margin: .75rem; padding: .65rem .9rem; background: transparent; border: 1px solid #334155; border-radius: 8px; color: #94a3b8; cursor: pointer; font-size: .9rem; display: flex; align-items: center; gap: .5rem; transition: all .2s; }
	.logout-btn:hover { background: #7f1d1d; color: #fca5a5; border-color: #7f1d1d; }

	.main-content { flex: 1; margin-left: 240px; display: flex; flex-direction: column; }
	.topbar { display: flex; justify-content: space-between; align-items: center; padding: 1.25rem 2rem; background: white; border-bottom: 1px solid #e2e8f0; position: sticky; top: 0; z-index: 5; }
	.page-title { font-size: 1.4rem; font-weight: 700; color: #1e293b; margin: 0; }
	.admin-info { display: flex; align-items: center; gap: .5rem; font-size: .9rem; color: #475569; }
	.admin-avatar { font-size: 1.3rem; }

	.content { padding: 2rem; }

	.alert { padding: .9rem 1.2rem; border-radius: 8px; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center; font-size: .9rem; }
	.alert.error   { background: #fef2f2; border: 1px solid #fecaca; color: #b91c1c; }
	.alert.success { background: #f0fdf4; border: 1px solid #bbf7d0; color: #166534; }
	.close-btn { background: none; border: none; cursor: pointer; font-size: 1rem; opacity: .6; }
	.close-btn:hover { opacity: 1; }

	/* Toolbar */
	.toolbar { display: flex; gap: 1rem; align-items: center; margin-bottom: 1.25rem; flex-wrap: wrap; }
	.search-input { flex: 1; min-width: 220px; padding: .5rem .9rem; border: 1px solid #e2e8f0; border-radius: 8px; font-size: .9rem; outline: none; }
	.search-input:focus { border-color: #94a3b8; }

	.filter-tabs { display: flex; gap: .5rem; }
	.tab-btn { padding: .45rem 1rem; border: 1px solid #e2e8f0; border-radius: 99px; background: white; cursor: pointer; font-size: .85rem; font-weight: 500; color: #64748b; transition: all .2s; }
	.tab-btn.active { background: #1e293b; color: white; border-color: #1e293b; }

	.summary-line { font-size: .85rem; color: #64748b; margin-bottom: .75rem; }

	/* Table */
	.table-wrapper { background: white; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,.07); overflow: hidden; }
	table { width: 100%; border-collapse: collapse; }
	thead { background: #f8fafc; }
	th { padding: .85rem 1rem; text-align: left; font-size: .78rem; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: .05em; border-bottom: 1px solid #e2e8f0; }
	td { padding: .85rem 1rem; border-bottom: 1px solid #f1f5f9; font-size: .88rem; color: #334155; vertical-align: middle; }
	tr:last-child td { border-bottom: none; }
	tr:hover { background: #fafafa; }
	.name-cell { display: flex; align-items: center; gap: .5rem; font-weight: 500; }
	.avatar { font-size: 1.2rem; }

	.status { padding: .25rem .7rem; border-radius: 99px; font-size: .75rem; font-weight: 600; }
	.status.green { background: #f0fdf4; color: #166534; }
	.status.red   { background: #fef2f2; color: #b91c1c; }
	.status.gray  { background: #f1f5f9; color: #64748b; }

	.actions-cell { display: flex; gap: .5rem; }
	.btn-sm { padding: .35rem .8rem; border: none; border-radius: 6px; cursor: pointer; font-size: .8rem; font-weight: 600; transition: opacity .2s; }
	.btn-sm.green { background: #dcfce7; color: #166534; }
	.btn-sm.green:hover { background: #bbf7d0; }
	.btn-sm.red { background: #fee2e2; color: #b91c1c; }
	.btn-sm.red:hover { background: #fecaca; }

	.loading-msg { padding: 3rem; text-align: center; color: #64748b; }
	.empty-state { padding: 4rem; text-align: center; color: #94a3b8; }
	.empty-icon { font-size: 3rem; display: block; margin-bottom: .75rem; }
</style>

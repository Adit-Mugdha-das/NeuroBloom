<script>
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let admin = null;
	let doctors = [];
	let loading = true;
	let error = '';
	let successMsg = '';
	let filter = 'all'; // 'all' | 'pending' | 'active' | 'suspended'

	onMount(async () => {
		const u = $user;
		if (!u || u.role !== 'admin') { goto('/login'); return; }
		admin = u;
		await loadDoctors();
	});

	async function loadDoctors() {
		loading = true;
		error = '';
		try {
			const res = await api.get(`/api/admin/doctors?admin_id=${admin.id}`);
			doctors = res.data.doctors;
		} catch (e) {
			error = e.response?.data?.detail || 'Failed to load doctors';
		} finally {
			loading = false;
		}
	}

	async function approveDoctor(id, name) {
		if (!confirm(`Approve Dr. ${name}? They will be able to log in.`)) return;
		try {
			await api.patch(`/api/admin/doctors/${id}/approve?admin_id=${admin.id}`);
			successMsg = `Dr. ${name} approved successfully.`;
			await loadDoctors();
		} catch (e) {
			error = e.response?.data?.detail || 'Action failed';
		}
	}

	async function suspendDoctor(id, name) {
		if (!confirm(`Suspend Dr. ${name}? They will lose access.`)) return;
		try {
			await api.patch(`/api/admin/doctors/${id}/suspend?admin_id=${admin.id}`);
			successMsg = `Dr. ${name} suspended.`;
			await loadDoctors();
		} catch (e) {
			error = e.response?.data?.detail || 'Action failed';
		}
	}

	async function activateDoctor(id, name) {
		try {
			await api.patch(`/api/admin/doctors/${id}/activate?admin_id=${admin.id}`);
			successMsg = `Dr. ${name} re-activated.`;
			await loadDoctors();
		} catch (e) {
			error = e.response?.data?.detail || 'Action failed';
		}
	}

	function clearMessages() { error = ''; successMsg = ''; }

	$: filtered = doctors.filter(d => {
		if (filter === 'pending')   return !d.is_verified && d.is_active;
		if (filter === 'active')    return d.is_verified && d.is_active;
		if (filter === 'suspended') return !d.is_active;
		return true;
	});

	function statusLabel(d) {
		if (!d.is_active)   return { text: 'Suspended', cls: 'status red' };
		if (!d.is_verified) return { text: 'Pending',   cls: 'status orange' };
		return                     { text: 'Active',    cls: 'status green' };
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
			<a href="/admin/dashboard" class="nav-item">
				<span class="nav-icon">📊</span> Dashboard
			</a>
			<a href="/admin/doctors" class="nav-item active">
				<span class="nav-icon">👨‍⚕️</span> Doctor Management
			</a>
			<a href="/admin/patients" class="nav-item">
				<span class="nav-icon">👤</span> Patient Management
			</a>
		</nav>
		<button class="logout-btn" on:click={() => { user.set(null); goto('/login'); }}>
			<span>🚪</span> Logout
		</button>
	</aside>

	<main class="main-content">
		<header class="topbar">
			<h1 class="page-title">Doctor Management</h1>
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

			<!-- Filter tabs -->
			<div class="filter-tabs">
				{#each [['all','All'],['pending','Pending Approval'],['active','Active'],['suspended','Suspended']] as [val, label]}
					<button
						class="tab-btn {filter === val ? 'active' : ''}"
						on:click={() => filter = val}
					>{label}</button>
				{/each}
			</div>

			{#if loading}
				<div class="loading-msg">Loading doctors…</div>
			{:else if filtered.length === 0}
				<div class="empty-state">
					<span class="empty-icon">👨‍⚕️</span>
					<p>No doctors found for this filter.</p>
				</div>
			{:else}
				<div class="table-wrapper">
					<table>
						<thead>
							<tr>
								<th>Name</th>
								<th>Email</th>
								<th>Specialization</th>
								<th>Institution</th>
								<th>Registered</th>
								<th>Status</th>
								<th>Actions</th>
							</tr>
						</thead>
						<tbody>
							{#each filtered as d (d.id)}
								{@const st = statusLabel(d)}
								<tr>
									<td class="name-cell">
										<span class="avatar">👨‍⚕️</span>
										{d.full_name}
									</td>
									<td>{d.email}</td>
									<td>{d.specialization || '—'}</td>
									<td>{d.institution || '—'}</td>
									<td>{new Date(d.created_at).toLocaleDateString()}</td>
									<td><span class={st.cls}>{st.text}</span></td>
									<td class="actions-cell">
										{#if !d.is_active}
											<button class="btn-sm green" on:click={() => activateDoctor(d.id, d.full_name)}>Activate</button>
										{:else if !d.is_verified}
											<button class="btn-sm green" on:click={() => approveDoctor(d.id, d.full_name)}>Approve</button>
											<button class="btn-sm red"   on:click={() => suspendDoctor(d.id, d.full_name)}>Reject</button>
										{:else}
											<button class="btn-sm red" on:click={() => suspendDoctor(d.id, d.full_name)}>Suspend</button>
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
	/* ── Layout (same sidebar shell as dashboard) ── */
	.admin-layout { display: flex; min-height: 100vh; background: #f0f4f8; font-family: 'Inter', sans-serif; }

	.sidebar {
		width: 240px; min-height: 100vh; background: #1e293b; color: #e2e8f0;
		display: flex; flex-direction: column; position: fixed; top: 0; left: 0; bottom: 0; z-index: 10;
	}
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

	/* ── Alerts ── */
	.alert { padding: .9rem 1.2rem; border-radius: 8px; margin-bottom: 1rem; display: flex; justify-content: space-between; align-items: center; font-size: .9rem; }
	.alert.error   { background: #fef2f2; border: 1px solid #fecaca; color: #b91c1c; }
	.alert.success { background: #f0fdf4; border: 1px solid #bbf7d0; color: #166534; }
	.close-btn { background: none; border: none; cursor: pointer; font-size: 1rem; opacity: .6; }
	.close-btn:hover { opacity: 1; }

	/* ── Filter tabs ── */
	.filter-tabs { display: flex; gap: .5rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
	.tab-btn { padding: .45rem 1rem; border: 1px solid #e2e8f0; border-radius: 99px; background: white; cursor: pointer; font-size: .85rem; font-weight: 500; color: #64748b; transition: all .2s; }
	.tab-btn.active { background: #1e293b; color: white; border-color: #1e293b; }

	/* ── Table ── */
	.table-wrapper { background: white; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,.07); overflow: hidden; }
	table { width: 100%; border-collapse: collapse; }
	thead { background: #f8fafc; }
	th { padding: .85rem 1rem; text-align: left; font-size: .78rem; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: .05em; border-bottom: 1px solid #e2e8f0; }
	td { padding: .85rem 1rem; border-bottom: 1px solid #f1f5f9; font-size: .88rem; color: #334155; vertical-align: middle; }
	tr:last-child td { border-bottom: none; }
	tr:hover { background: #fafafa; }

	.name-cell { display: flex; align-items: center; gap: .5rem; font-weight: 500; }
	.avatar { font-size: 1.2rem; }

	/* ── Status badges ── */
	.status { padding: .25rem .7rem; border-radius: 99px; font-size: .75rem; font-weight: 600; }
	.status.green  { background: #f0fdf4; color: #166534; }
	.status.orange { background: #fff7ed; color: #c2410c; }
	.status.red    { background: #fef2f2; color: #b91c1c; }

	/* ── Action buttons ── */
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

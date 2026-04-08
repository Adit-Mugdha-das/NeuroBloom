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
	let departments = [];
	let assignModal = { open: false, id: null, name: '', departmentId: '' };
	let assignLoading = false;

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
			const deptRes = await api.get(`/api/admin/departments?admin_id=${admin.id}`);
			departments = deptRes.data.departments;
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

	// ── Reset password modal ──
	let resetModal = { open: false, id: null, name: '' };
	let resetNewPassword = '';
	let resetLoading = false;

	function openResetModal(id, name) {
		resetModal = { open: true, id, name };
		resetNewPassword = '';
	}
	function closeResetModal() { resetModal = { open: false, id: null, name: '' }; }

	async function submitResetPassword() {
		if (!resetNewPassword || resetNewPassword.length < 6) {
			error = 'Password must be at least 6 characters.';
			return;
		}
		resetLoading = true;
		try {
			await api.post(`/api/admin/doctors/${resetModal.id}/reset-password?admin_id=${admin.id}`, { new_password: resetNewPassword });
			successMsg = `Password reset for Dr. ${resetModal.name}.`;
			closeResetModal();
		} catch (e) {
			error = e.response?.data?.detail || 'Reset failed';
		} finally {
			resetLoading = false;
		}
	}

	function openAssignModal(doctor) {
		assignModal = {
			open: true,
			id: doctor.id,
			name: doctor.full_name,
			departmentId: doctor.department_id ? String(doctor.department_id) : ''
		};
	}

	function closeAssignModal() {
		assignModal = { open: false, id: null, name: '', departmentId: '' };
	}

	async function submitDepartmentAssignment() {
		assignLoading = true;
		try {
			const payload = {
				department_id: assignModal.departmentId ? Number(assignModal.departmentId) : null
			};
			const response = await api.patch(`/api/admin/doctors/${assignModal.id}/department?admin_id=${admin.id}`, payload);
			successMsg = response.data.message;
			closeAssignModal();
			await loadDoctors();
		} catch (e) {
			error = e.response?.data?.detail || 'Department assignment failed';
		} finally {
			assignLoading = false;
		}
	}

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
			<a href="/admin/doctors" class="nav-item active">
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
			<h1 class="page-title">Doctor Management</h1>
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
					<div class="empty-icon-wrap">
					<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
						<path d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/>
					</svg>
				</div>
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
								<th>Department</th>
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
									<div class="doc-initial">{(d.full_name || d.email || '?')[0].toUpperCase()}</div>
										{d.full_name}
									</td>
									<td>{d.email}</td>
									<td>{d.specialization || '—'}</td>
									<td>{d.department_name || 'Unassigned'}</td>
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
										<button type="button" class="btn-sm blue" on:click|stopPropagation={() => openAssignModal(d)}>Department</button>
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

<!-- Reset Password Modal -->
{#if resetModal.open}
	<div class="modal-overlay" on:click|self={closeResetModal} role="presentation">
		<div class="modal" role="dialog" aria-modal="true" tabindex="-1">
			<h2 class="modal-title">Reset Password</h2>
			<p class="modal-sub">Set a new password for <strong>Dr. {resetModal.name}</strong></p>
			<input
				class="modal-input"
				type="password"
				placeholder="New password (min 6 chars)"
				bind:value={resetNewPassword}
			/>
			<div class="modal-actions">
				<button class="btn-modal cancel" on:click={closeResetModal} disabled={resetLoading}>Cancel</button>
				<button class="btn-modal confirm" on:click={submitResetPassword} disabled={resetLoading}>
					{resetLoading ? 'Saving…' : 'Reset Password'}
				</button>
			</div>
		</div>
	</div>
{/if}

{#if assignModal.open}
	<div class="modal-overlay" on:click|self={closeAssignModal} role="presentation">
		<div class="modal" role="dialog" aria-modal="true" tabindex="-1">
			<h2 class="modal-title">Assign Department</h2>
			<p class="modal-sub">Select a department for <strong>Dr. {assignModal.name}</strong></p>
			<select class="modal-input" bind:value={assignModal.departmentId}>
				<option value="">No department</option>
				{#each departments as department (department.id)}
					<option value={department.id}>{department.name}</option>
				{/each}
			</select>
			<div class="modal-actions">
				<button class="btn-modal cancel" on:click={closeAssignModal} disabled={assignLoading}>Cancel</button>
				<button class="btn-modal confirm" on:click={submitDepartmentAssignment} disabled={assignLoading}>
					{assignLoading ? 'Saving...' : 'Save Department'}
				</button>
			</div>
		</div>
	</div>
{/if}

<style>
	/* ── Layout (same sidebar shell as dashboard) ── */
	.admin-layout { display: flex; min-height: 100vh; background: #f0f4f8; font-family: 'Inter', sans-serif; }

	.sidebar {
		width: 240px; min-height: 100vh; background: #1e293b; color: #e2e8f0;
		display: flex; flex-direction: column; position: fixed; top: 0; left: 0; bottom: 0; z-index: 10;
	}
	.sidebar-brand { display: flex; align-items: center; gap: .6rem; padding: 1.4rem 1.2rem; background: #0f172a; font-weight: 700; font-size: 1rem; }
	.brand-mark { width: 28px; height: 28px; background: #4f46e5; border-radius: 7px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: white; }
	.brand-mark svg { width: 16px; height: 16px; }
	.sidebar-nav { flex: 1; padding: 1rem .75rem; display: flex; flex-direction: column; gap: .25rem; }
	.nav-item { display: flex; align-items: center; gap: .75rem; padding: .65rem .9rem; border-radius: 8px; color: #94a3b8; text-decoration: none; font-size: .9rem; font-weight: 500; transition: all .2s; }
	.nav-item:hover, .nav-item.active { background: #334155; color: #f1f5f9; }
	.nav-icon { width: 17px; height: 17px; flex-shrink: 0; }
	.logout-btn { margin: .75rem; padding: .65rem .9rem; background: transparent; border: 1px solid #334155; border-radius: 8px; color: #94a3b8; cursor: pointer; font-size: .9rem; display: flex; align-items: center; gap: .5rem; transition: all .2s; }
	.logout-btn:hover { background: #7f1d1d; color: #fca5a5; border-color: #7f1d1d; }

	.main-content { flex: 1; margin-left: 240px; display: flex; flex-direction: column; }
	.topbar { display: flex; justify-content: space-between; align-items: center; padding: 1.25rem 2rem; background: white; border-bottom: 1px solid #e2e8f0; position: sticky; top: 0; z-index: 5; }
	.page-title { font-size: 1.4rem; font-weight: 700; color: #1e293b; margin: 0; }
	.admin-info { display: flex; align-items: center; gap: .65rem; }
	.admin-avatar { width: 36px; height: 36px; border-radius: 50%; background: #eff6ff; border: 1.5px solid #bfdbfe; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: #3b82f6; }
	.admin-avatar svg { width: 18px; height: 18px; }
	.admin-details { display: flex; flex-direction: column; gap: 1px; }
	.admin-name { font-size: .88rem; font-weight: 600; color: #1e293b; }
	.admin-role { font-size: .72rem; color: #94a3b8; }

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

	.name-cell { display: flex; align-items: center; gap: .6rem; font-weight: 500; }
	.doc-initial { width: 34px; height: 34px; border-radius: 50%; background: linear-gradient(135deg, #4f46e5, #7c3aed); color: #fff; display: flex; align-items: center; justify-content: center; font-size: .85rem; font-weight: 700; flex-shrink: 0; }

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
	.btn-sm.blue { background: #dbeafe; color: #1d4ed8; }
	.btn-sm.blue:hover { background: #bfdbfe; }

	/* ── Modal ── */
	.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; z-index: 100; }
	.modal { background: white; border-radius: 14px; padding: 2rem; width: 380px; max-width: 95vw; box-shadow: 0 8px 32px rgba(0,0,0,.18); }
	.modal-title { font-size: 1.2rem; font-weight: 700; color: #1e293b; margin: 0 0 .4rem; }
	.modal-sub { font-size: .9rem; color: #64748b; margin: 0 0 1.2rem; }
	.modal-input { width: 100%; padding: .6rem .9rem; border: 1px solid #e2e8f0; border-radius: 8px; font-size: .9rem; box-sizing: border-box; margin-bottom: 1.2rem; outline: none; }
	.modal-input:focus { border-color: #94a3b8; }
	.modal-actions { display: flex; gap: .75rem; justify-content: flex-end; }
	.btn-modal { padding: .55rem 1.2rem; border: none; border-radius: 8px; font-size: .9rem; font-weight: 600; cursor: pointer; transition: opacity .2s; }
	.btn-modal:disabled { opacity: .6; cursor: not-allowed; }
	.btn-modal.cancel { background: #f1f5f9; color: #475569; }
	.btn-modal.cancel:hover:not(:disabled) { background: #e2e8f0; }
	.btn-modal.confirm { background: #1e293b; color: white; }
	.btn-modal.confirm:hover:not(:disabled) { background: #334155; }

	.loading-msg { padding: 3rem; text-align: center; color: #64748b; }
	.empty-state { padding: 4rem; text-align: center; color: #94a3b8; }
	.empty-icon-wrap { width: 56px; height: 56px; border-radius: 50%; background: #f1f5f9; border: 1.5px solid #e2e8f0; display: flex; align-items: center; justify-content: center; margin: 0 auto .75rem; color: #94a3b8; }
	.empty-icon-wrap svg { width: 26px; height: 26px; }
</style>

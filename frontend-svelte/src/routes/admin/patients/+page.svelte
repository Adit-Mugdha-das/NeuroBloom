<script>
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let admin = null;
	let patients = [];
	let doctors = [];
	let loading = true;
	let error = '';
	let successMsg = '';
	let searchQuery = '';
	let filter = 'all';

	let resetModal = { open: false, id: null, name: '' };
	let resetNewPassword = '';
	let resetLoading = false;

	let transferModal = { open: false, patientId: null, patientName: '' };
	let transferDoctorId = '';
	let transferLoading = false;

	// ── Patient Oversight ──
	let profileModal = false;
	let patientDetail = null;
	let profileLoading = false;
	let profileError = '';
	let profileTab = 'sessions';

	async function viewProfile(patientId) {
		profileModal = true;
		patientDetail = null;
		profileLoading = true;
		profileError = '';
		profileTab = 'sessions';
		try {
			const response = await api.get(`/api/admin/patients/${patientId}/overview?admin_id=${admin.id}`);
			patientDetail = response.data;
		} catch (err) {
			profileError = err.response?.data?.detail || 'Failed to load patient profile';
		} finally {
			profileLoading = false;
		}
	}

	function closeProfileModal() {
		profileModal = false;
		patientDetail = null;
		profileError = '';
	}

	function formatDate(iso) {
		if (!iso) return '—';
		return new Date(iso).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
	}

	function formatDomain(domain) {
		return (domain || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
	}

	function lastActivityLabel(days) {
		if (days === null || days === undefined) return 'No sessions yet';
		if (days === 0) return 'Today';
		if (days === 1) return 'Yesterday';
		return `${days} days ago`;
	}

	onMount(async () => {
		const currentUser = $user;
		if (!currentUser || currentUser.role !== 'admin') {
			goto('/login');
			return;
		}

		admin = currentUser;
		await loadPatients();
	});

	async function loadPatients() {
		loading = true;
		error = '';
		try {
			const response = await api.get(`/api/admin/patients?admin_id=${admin.id}`);
			patients = response.data.patients;
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Failed to load patients';
		} finally {
			loading = false;
		}
	}

	async function loadDoctors() {
		const response = await api.get(`/api/admin/doctors?admin_id=${admin.id}`);
		doctors = response.data.doctors.filter((doctor) => doctor.is_active && doctor.is_verified);
	}

	async function deactivatePatient(id) {
		if (!confirm('Deactivate this patient account?')) {
			return;
		}

		try {
			await api.patch(`/api/admin/patients/${id}/deactivate?admin_id=${admin.id}`);
			successMsg = 'Patient account deactivated.';
			await loadPatients();
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Action failed';
		}
	}

	async function activatePatient(id) {
		try {
			await api.patch(`/api/admin/patients/${id}/activate?admin_id=${admin.id}`);
			successMsg = 'Patient account activated.';
			await loadPatients();
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Action failed';
		}
	}

	function openResetModal(id, name) {
		error = '';
		resetModal = { open: true, id, name };
		resetNewPassword = '';
	}

	function closeResetModal() {
		resetModal = { open: false, id: null, name: '' };
		resetNewPassword = '';
	}

	async function submitResetPassword() {
		if (!resetNewPassword || resetNewPassword.length < 6) {
			error = 'Password must be at least 6 characters.';
			return;
		}

		resetLoading = true;
		try {
			await api.post(`/api/admin/patients/${resetModal.id}/reset-password?admin_id=${admin.id}`, {
				new_password: resetNewPassword
			});
			successMsg = `Password reset for ${resetModal.name}.`;
			closeResetModal();
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Reset failed';
		} finally {
			resetLoading = false;
		}
	}

	async function openTransferModal(patientId, patientName) {
		error = '';
		transferModal = { open: true, patientId, patientName };
		transferDoctorId = '';

		try {
			await loadDoctors();
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Could not load doctors list';
		}
	}

	function closeTransferModal() {
		transferModal = { open: false, patientId: null, patientName: '' };
		transferDoctorId = '';
	}

	async function submitTransfer() {
		if (!transferDoctorId) {
			error = 'Please select a doctor.';
			return;
		}

		transferLoading = true;
		try {
			const response = await api.post(
				`/api/admin/patients/${transferModal.patientId}/transfer?admin_id=${admin.id}`,
				{ new_doctor_id: Number(transferDoctorId) }
			);
			successMsg = response.data.message;
			closeTransferModal();
			await loadPatients();
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Transfer failed';
		} finally {
			transferLoading = false;
		}
	}

	function clearMessages() {
		error = '';
		successMsg = '';
	}

	$: filtered = patients.filter((patient) => {
		const matchesFilter =
			filter === 'all' ? true :
			filter === 'active' ? patient.is_active :
			!patient.is_active;

		const query = searchQuery.toLowerCase();
		const matchesSearch =
			!query ||
			(patient.email || '').toLowerCase().includes(query) ||
			(patient.full_name || '').toLowerCase().includes(query) ||
			(patient.diagnosis || '').toLowerCase().includes(query);

		return matchesFilter && matchesSearch;
	});

	$: totalActive = patients.filter((patient) => patient.is_active).length;
	$: totalInactive = patients.filter((patient) => !patient.is_active).length;
</script>

<div class="admin-layout">
	<aside class="sidebar">
		<div class="sidebar-brand">NeuroBloom Admin</div>
		<nav class="sidebar-nav">
			<a href="/admin/dashboard" class="nav-item">Dashboard</a>
			<a href="/admin/analytics" class="nav-item">System Analytics</a>
			<a href="/admin/doctors" class="nav-item">Doctor Management</a>
			<a href="/admin/patients" class="nav-item active">Patient Management</a>
			<a href="/admin/departments" class="nav-item">Departments</a>
			<a href="/admin/interventions" class="nav-item">Interventions</a>
			<a href="/admin/messages" class="nav-item">Message Audit</a>
			<a href="/admin/audit-logs" class="nav-item">Audit Logs</a>
			<a href="/admin/system-health" class="nav-item">System Health</a>
		</nav>
		<button class="logout-btn" on:click={() => { user.set(null); goto('/login'); }}>Logout</button>
	</aside>

	<main class="main-content">
		<header class="topbar">
			<div>
				<h1 class="page-title">Patient Management</h1>
				<p class="page-sub">View and control all patient accounts</p>
			</div>
			<div class="admin-info">{admin?.full_name || admin?.email}</div>
		</header>

		<div class="content">
			{#if error}
				<div class="alert error" role="alert">
					<span>{error}</span>
					<button class="close-btn" on:click={clearMessages} aria-label="Close error">x</button>
				</div>
			{/if}

			{#if successMsg}
				<div class="alert success" role="status">
					<span>{successMsg}</span>
					<button class="close-btn" on:click={clearMessages} aria-label="Close success">x</button>
				</div>
			{/if}

			<div class="stats-strip">
				<div class="stat-chip">
					<p class="chip-val">{patients.length}</p>
					<p class="chip-lbl">Total</p>
				</div>
				<div class="stat-chip">
					<p class="chip-val">{totalActive}</p>
					<p class="chip-lbl">Active</p>
				</div>
				<div class="stat-chip">
					<p class="chip-val">{totalInactive}</p>
					<p class="chip-lbl">Inactive</p>
				</div>
			</div>

			<div class="toolbar">
				<input class="search-input" type="text" placeholder="Search by name, email or diagnosis..." bind:value={searchQuery} />
				<div class="filter-tabs">
					{#each [['all', 'All'], ['active', 'Active'], ['inactive', 'Inactive']] as [value, label]}
						<button type="button" class="tab-btn {filter === value ? 'active' : ''}" on:click={() => filter = value}>{label}</button>
					{/each}
				</div>
			</div>

			{#if loading}
				<div class="loading-msg">Loading patients...</div>
			{:else if filtered.length === 0}
				<div class="empty-state">
					<p class="empty-title">No patients found</p>
					<p class="empty-sub">Try adjusting your search or filter.</p>
				</div>
			{:else}
				<div class="results-bar">{filtered.length} patient{filtered.length !== 1 ? 's' : ''}</div>
				<div class="table-card">
					<table>
						<thead>
							<tr>
								<th>Patient</th>
								<th>Email</th>
								<th>Diagnosis</th>
								<th>Data Sharing</th>
								<th>Status</th>
								<th>Actions</th>
							</tr>
						</thead>
						<tbody>
							{#each filtered as patient (patient.id)}
								<tr>
									<td>
										<div class="patient-cell">
											<div class="patient-avatar">{(patient.full_name || patient.email)[0].toUpperCase()}</div>
											<div>
												<p class="patient-name">{patient.full_name || '(no name)'}</p>
												{#if patient.date_of_birth}
													<p class="patient-dob">DOB: {patient.date_of_birth}</p>
												{/if}
											</div>
										</div>
									</td>
									<td>{patient.email}</td>
									<td>{patient.diagnosis || '-'}</td>
									<td><span class="badge {patient.consent_to_share ? 'badge-green' : 'badge-gray'}">{patient.consent_to_share ? 'Shared' : 'Private'}</span></td>
									<td><span class="badge {patient.is_active ? 'badge-blue' : 'badge-red'}">{patient.is_active ? 'Active' : 'Inactive'}</span></td>
									<td>
										<div class="actions-cell">
											<button type="button" class="btn-sm teal" on:click={() => viewProfile(patient.id)}>View Profile</button>
											{#if patient.is_active}
												<button type="button" class="btn-sm red" on:click={() => deactivatePatient(patient.id)}>Deactivate</button>
											{:else}
												<button type="button" class="btn-sm green" on:click={() => activatePatient(patient.id)}>Activate</button>
											{/if}
											<button type="button" class="btn-sm blue" on:click={() => openResetModal(patient.id, patient.full_name || patient.email)}>Reset Password</button>
											<button type="button" class="btn-sm purple" on:click={() => openTransferModal(patient.id, patient.full_name || patient.email)}>Transfer Patient</button>
										</div>
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

{#if profileModal}
	<div class="modal-overlay" role="presentation" on:click|self={closeProfileModal}>
		<div class="modal profile-modal" role="dialog" aria-modal="true" aria-label="Patient profile">
			<!-- Modal Header -->
			<div class="profile-modal-header">
				<div class="profile-modal-title-row">
					<h2 class="profile-modal-title">Patient Profile</h2>
					<p class="profile-modal-sub">Read-only oversight view — no medical data is modified</p>
				</div>
				<button class="modal-close" on:click={closeProfileModal} aria-label="Close profile">✕</button>
			</div>

			{#if profileLoading}
				<div class="profile-loading">Loading patient data...</div>
			{:else if profileError}
				<div class="profile-error">{profileError}</div>
			{:else if patientDetail}
				<!-- Identity Strip -->
				<div class="patient-identity">
					<div class="identity-avatar">{(patientDetail.profile.full_name || patientDetail.profile.email)[0].toUpperCase()}</div>
					<div class="identity-info">
						<div class="identity-name-row">
							<span class="identity-name">{patientDetail.profile.full_name}</span>
							<span class="badge {patientDetail.profile.is_active ? 'badge-blue' : 'badge-red'}">{patientDetail.profile.is_active ? 'Active' : 'Inactive'}</span>
							{#if patientDetail.risk}
								<span class="risk-badge risk-{patientDetail.risk.level}">{patientDetail.risk.level === 'stable' ? 'Stable' : patientDetail.risk.level.charAt(0).toUpperCase() + patientDetail.risk.level.slice(1) + ' Risk'}</span>
							{/if}
						</div>
						<p class="identity-email">{patientDetail.profile.email}</p>
						{#if patientDetail.profile.diagnosis}
							<p class="identity-diagnosis">{patientDetail.profile.diagnosis}</p>
						{/if}
					</div>
				</div>

				<!-- Key Metrics Strip -->
				<div class="overview-metrics">
					<div class="ov-metric">
						<p class="ov-label">Doctor</p>
						<p class="ov-value">{patientDetail.doctor ? `Dr. ${patientDetail.doctor.full_name}` : 'Unassigned'}</p>
						{#if patientDetail.doctor?.specialization}
							<p class="ov-sub">{patientDetail.doctor.specialization}</p>
						{/if}
					</div>
					<div class="ov-metric">
						<p class="ov-label">Sessions</p>
						<p class="ov-value">{patientDetail.training_summary.total_sessions}</p>
						<p class="ov-sub">total completed</p>
					</div>
					<div class="ov-metric">
						<p class="ov-label">Risk Level</p>
						<p class="ov-value ov-risk-{patientDetail.risk.level}">{patientDetail.risk.level.charAt(0).toUpperCase() + patientDetail.risk.level.slice(1)}</p>
						<p class="ov-sub">score: {patientDetail.risk.score}</p>
					</div>
					<div class="ov-metric">
						<p class="ov-label">Last Activity</p>
						<p class="ov-value">{lastActivityLabel(patientDetail.training_summary.days_since_last_activity)}</p>
						{#if patientDetail.training_summary.last_activity}
							<p class="ov-sub">{formatDate(patientDetail.training_summary.last_activity)}</p>
						{/if}
					</div>
					{#if patientDetail.profile.date_of_birth}
						<div class="ov-metric">
							<p class="ov-label">Date of Birth</p>
							<p class="ov-value">{patientDetail.profile.date_of_birth}</p>
						</div>
					{/if}
				</div>

				<!-- Doctor & Assignment Info -->
				{#if patientDetail.doctor}
					<div class="info-section">
						<h3 class="section-heading">Assigned Doctor</h3>
						<div class="doctor-info-row">
							<div class="doctor-info-avatar">{patientDetail.doctor.full_name[0].toUpperCase()}</div>
							<div>
								<p class="doctor-info-name">Dr. {patientDetail.doctor.full_name}</p>
								{#if patientDetail.doctor.specialization}<p class="doctor-info-meta">{patientDetail.doctor.specialization}{patientDetail.doctor.institution ? ` · ${patientDetail.doctor.institution}` : ''}</p>{/if}
								{#if patientDetail.assignment?.assigned_at}<p class="doctor-info-meta muted">Assigned {formatDate(patientDetail.assignment.assigned_at)}</p>{/if}
								{#if patientDetail.assignment?.treatment_goal}<p class="doctor-info-meta">Goal: {patientDetail.assignment.treatment_goal}</p>{/if}
							</div>
						</div>
					</div>
				{/if}

				<!-- Domain Summary -->
				{#if patientDetail.training_summary.domain_summary?.length > 0}
					<div class="info-section">
						<h3 class="section-heading">Training Domains</h3>
						<div class="domain-grid">
							{#each patientDetail.training_summary.domain_summary as d}
								<div class="domain-chip">
									<p class="domain-name">{formatDomain(d.domain)}</p>
									<p class="domain-stat">{d.sessions} sessions · avg {d.avg_score}</p>
								</div>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Tabs: Training History / Reports -->
				<div class="info-section">
					<div class="tab-nav">
						<button type="button" class="tab-btn {profileTab === 'sessions' ? 'active' : ''}" on:click={() => profileTab = 'sessions'}>Training History</button>
						<button type="button" class="tab-btn {profileTab === 'reports' ? 'active' : ''}" on:click={() => profileTab = 'reports'}>Progress Reports</button>
					</div>

					{#if profileTab === 'sessions'}
						{#if patientDetail.recent_sessions.length === 0}
							<p class="empty-tab">No training sessions recorded yet.</p>
						{:else}
							<p class="tab-note">Showing the {patientDetail.recent_sessions.length} most recent sessions.</p>
							<div class="session-table-wrap">
								<table class="session-table">
									<thead>
										<tr>
											<th>Domain</th>
											<th>Task</th>
											<th>Score</th>
											<th>Accuracy</th>
											<th>Duration</th>
											<th>Difficulty</th>
											<th>Date</th>
										</tr>
									</thead>
									<tbody>
										{#each patientDetail.recent_sessions as s}
											<tr>
												<td>{formatDomain(s.domain)}</td>
												<td class="task-cell">{formatDomain(s.task)}</td>
												<td><span class="score-chip {s.score >= 70 ? 'score-good' : s.score >= 45 ? 'score-mid' : 'score-low'}">  {s.score}</span></td>
												<td>{s.accuracy}%</td>
												<td>{Math.round(s.duration_s / 60)}m {s.duration_s % 60}s</td>
												<td>Lvl {s.difficulty}</td>
												<td class="date-cell">{formatDate(s.date)}</td>
											</tr>
										{/each}
									</tbody>
								</table>
							</div>
						{/if}
					{:else}
						{#if patientDetail.reports.length === 0}
							<p class="empty-tab">No progress reports have been generated yet.</p>
						{:else}
							<div class="reports-list">
								{#each patientDetail.reports as r}
									<div class="report-card">
										<div class="report-card-header">
											<span class="report-period-badge">{r.period_type === 'weekly' ? 'Weekly' : 'Monthly'}</span>
											<span class="report-range">{formatDate(r.period_start)} – {formatDate(r.period_end)}</span>
											<span class="report-generated">Generated {formatDate(r.generated_at)}</span>
										</div>
										{#if r.doctor_commentary}
											<p class="report-commentary">{r.doctor_commentary}</p>
										{:else}
											<p class="report-commentary muted">No doctor commentary recorded.</p>
										{/if}
									</div>
								{/each}
							</div>
						{/if}
					{/if}
				</div>
			{/if}
		</div>
	</div>
{/if}

{#if resetModal.open}
	<div class="modal-overlay">
		<div class="modal" role="dialog" aria-modal="true" tabindex="-1">
			<div class="modal-header">
				<div>
					<h2 class="modal-title">Reset Password</h2>
					<p class="modal-sub">For {resetModal.name}</p>
				</div>
				<button class="modal-close" on:click={closeResetModal} aria-label="Close reset password modal">x</button>
			</div>
			<div class="modal-body">
				<label class="field-label" for="reset-password-input">New Password</label>
				<input id="reset-password-input" class="field-input" type="password" placeholder="Minimum 6 characters" bind:value={resetNewPassword} />
			</div>
			<div class="modal-footer">
				<button class="btn-outline" on:click={closeResetModal} disabled={resetLoading}>Cancel</button>
				<button class="btn-primary" on:click={submitResetPassword} disabled={resetLoading}>{resetLoading ? 'Saving...' : 'Reset Password'}</button>
			</div>
		</div>
	</div>
{/if}

{#if transferModal.open}
	<div class="modal-overlay">
		<div class="modal" role="dialog" aria-modal="true" tabindex="-1">
			<div class="modal-header">
				<div>
					<h2 class="modal-title">Transfer Patient</h2>
					<p class="modal-sub">Reassign {transferModal.patientName}</p>
				</div>
				<button class="modal-close" on:click={closeTransferModal} aria-label="Close transfer modal">x</button>
			</div>
			<div class="modal-body">
				<label class="field-label" for="transfer-doctor-select">Transfer to Doctor</label>
				{#if doctors.length === 0}
					<p class="muted">No active verified doctors available.</p>
				{:else}
					<select id="transfer-doctor-select" class="field-input" bind:value={transferDoctorId}>
						<option value="">Select a doctor</option>
						{#each doctors as doctor (doctor.id)}
							<option value={doctor.id}>Dr. {doctor.full_name}{doctor.specialization ? ` - ${doctor.specialization}` : ''}{doctor.institution ? ` (${doctor.institution})` : ''}</option>
						{/each}
					</select>
				{/if}
			</div>
			<div class="modal-footer">
				<button class="btn-outline" on:click={closeTransferModal} disabled={transferLoading}>Cancel</button>
				<button class="btn-primary" on:click={submitTransfer} disabled={transferLoading || !transferDoctorId}>{transferLoading ? 'Transferring...' : 'Confirm Transfer'}</button>
			</div>
		</div>
	</div>
{/if}

<style>
	.admin-layout { display: flex; min-height: 100vh; background: #f1f5f9; font-family: 'Inter', system-ui, sans-serif; }
	.sidebar { width: 240px; min-height: 100vh; background: #0f172a; color: #e2e8f0; display: flex; flex-direction: column; position: fixed; top: 0; left: 0; bottom: 0; }
	.sidebar-brand { padding: 1.4rem 1.2rem; border-bottom: 1px solid #1e293b; font-weight: 700; }
	.sidebar-nav { flex: 1; padding: 1rem 0.75rem; display: flex; flex-direction: column; gap: 0.25rem; }
	.nav-item { padding: 0.65rem 0.9rem; border-radius: 8px; color: #94a3b8; text-decoration: none; font-size: 0.9rem; font-weight: 500; }
	.nav-item:hover { background: #1e293b; color: #f1f5f9; }
	.nav-item.active { background: #1d4ed8; color: #ffffff; }
	.logout-btn { margin: 0.75rem; padding: 0.65rem 0.9rem; background: transparent; border: 1px solid #334155; border-radius: 8px; color: #94a3b8; cursor: pointer; }
	.main-content { flex: 1; margin-left: 240px; }
	.topbar { display: flex; justify-content: space-between; align-items: center; padding: 1.25rem 2rem; background: #ffffff; border-bottom: 1px solid #e2e8f0; }
	.page-title { font-size: 1.35rem; font-weight: 700; color: #0f172a; margin: 0; }
	.page-sub { font-size: 0.8rem; color: #94a3b8; margin: 0.15rem 0 0; }
	.admin-info { font-size: 0.88rem; color: #475569; background: #f8fafc; padding: 0.5rem 0.9rem; border-radius: 8px; }
	.content { padding: 1.75rem 2rem; }
	.alert { padding: 0.85rem 1.1rem; border-radius: 10px; margin-bottom: 1.25rem; display: flex; justify-content: space-between; align-items: center; font-size: 0.88rem; font-weight: 500; }
	.alert.error { background: #fef2f2; border: 1px solid #fecaca; color: #b91c1c; }
	.alert.success { background: #f0fdf4; border: 1px solid #86efac; color: #166534; }
	.close-btn { background: none; border: none; cursor: pointer; font-size: 0.95rem; }
	.stats-strip { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }
	.stat-chip { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1rem 1.2rem; }
	.chip-val { font-size: 1.5rem; font-weight: 700; color: #0f172a; margin: 0; }
	.chip-lbl { font-size: 0.72rem; color: #94a3b8; margin: 0.2rem 0 0; text-transform: uppercase; letter-spacing: 0.05em; }
	.toolbar { display: flex; gap: 0.75rem; align-items: center; margin-bottom: 1rem; flex-wrap: wrap; }
	.search-input { flex: 1; min-width: 220px; padding: 0.65rem 0.9rem; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 0.88rem; background: #ffffff; }
	.filter-tabs { display: flex; gap: 0.4rem; }
	.tab-btn { padding: 0.45rem 1rem; border: 1px solid #e2e8f0; border-radius: 999px; background: #ffffff; cursor: pointer; font-size: 0.82rem; font-weight: 500; color: #64748b; }
	.tab-btn.active { background: #4f46e5; border-color: #4f46e5; color: #ffffff; }
	.loading-msg, .empty-state { padding: 3rem 2rem; text-align: center; color: #64748b; }
	.empty-title { font-size: 1.05rem; font-weight: 600; margin: 0 0 0.4rem; color: #334155; }
	.empty-sub { font-size: 0.85rem; margin: 0; }
	.results-bar { font-size: 0.82rem; color: #94a3b8; margin-bottom: 0.6rem; }
	.table-card { background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow-x: auto; }
	table { width: 100%; border-collapse: collapse; }
	thead { background: #f8fafc; }
	th { padding: 0.8rem 1rem; text-align: left; font-size: 0.72rem; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.06em; border-bottom: 1px solid #e2e8f0; }
	td { padding: 0.9rem 1rem; border-bottom: 1px solid #f1f5f9; font-size: 0.86rem; color: #334155; vertical-align: middle; }
	tr:last-child td { border-bottom: none; }
	.patient-cell { display: flex; align-items: center; gap: 0.75rem; }
	.patient-avatar { width: 36px; height: 36px; border-radius: 50%; background: linear-gradient(135deg, #6366f1, #8b5cf6); color: #ffffff; display: flex; align-items: center; justify-content: center; font-weight: 700; flex-shrink: 0; }
	.patient-name { margin: 0; font-weight: 600; color: #0f172a; }
	.patient-dob { margin: 0.2rem 0 0; font-size: 0.75rem; color: #94a3b8; }
	.badge { padding: 0.25rem 0.65rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; white-space: nowrap; }
	.badge-green { background: #dcfce7; color: #15803d; }
	.badge-gray { background: #f1f5f9; color: #64748b; }
	.badge-blue { background: #dbeafe; color: #1d4ed8; }
	.badge-red { background: #fee2e2; color: #b91c1c; }
	.actions-cell { display: flex; gap: 0.5rem; flex-wrap: wrap; }
	.btn-sm { padding: 0.4rem 0.8rem; border: none; border-radius: 6px; cursor: pointer; font-size: 0.8rem; font-weight: 600; }
	.btn-sm.green { background: #dcfce7; color: #166534; }
	.btn-sm.red { background: #fee2e2; color: #b91c1c; }
	.btn-sm.blue { background: #dbeafe; color: #1d4ed8; }
	.btn-sm.purple { background: #f3e8ff; color: #7e22ce; }
	.btn-sm.teal { background: #f0fdfa; color: #0f766e; border: 1px solid #99f6e4; }
	/* ── Profile Modal ── */
	.profile-modal { width: 760px; max-height: 90vh; overflow-y: auto; display: flex; flex-direction: column; }
	.profile-modal-header { display: flex; align-items: flex-start; justify-content: space-between; padding: 1.4rem 1.6rem 1rem; border-bottom: 1px solid #f1f5f9; }
	.profile-modal-title { font-size: 1.15rem; font-weight: 700; color: #0f172a; margin: 0; }
	.profile-modal-sub { font-size: 0.78rem; color: #94a3b8; margin: 0.2rem 0 0; }
	.profile-loading, .profile-error { padding: 3rem 2rem; text-align: center; color: #64748b; font-size: 0.9rem; }
	.profile-error { color: #b91c1c; }
	/* Identity strip */
	.patient-identity { display: flex; align-items: center; gap: 1rem; padding: 1.2rem 1.6rem; border-bottom: 1px solid #f1f5f9; background: #f8fafc; }
	.identity-avatar { width: 52px; height: 52px; border-radius: 50%; background: linear-gradient(135deg, #6366f1, #8b5cf6); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 1.3rem; font-weight: 700; flex-shrink: 0; }
	.identity-name-row { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
	.identity-name { font-size: 1.05rem; font-weight: 700; color: #0f172a; }
	.identity-email { font-size: 0.83rem; color: #64748b; margin: 0.2rem 0 0; }
	.identity-diagnosis { font-size: 0.82rem; color: #475569; margin: 0.15rem 0 0; font-style: italic; }
	/* Risk badges */
	.risk-badge { padding: 0.2rem 0.6rem; border-radius: 999px; font-size: 0.73rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; }
	.risk-high { background: #fee2e2; color: #b91c1c; }
	.risk-moderate { background: #fef3c7; color: #92400e; }
	.risk-stable { background: #dcfce7; color: #15803d; }
	/* Metrics strip */
	.overview-metrics { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 0; border-bottom: 1px solid #f1f5f9; }
	.ov-metric { padding: 1rem 1.4rem; border-right: 1px solid #f1f5f9; }
	.ov-metric:last-child { border-right: none; }
	.ov-label { font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.06em; margin: 0 0 0.3rem; font-weight: 600; }
	.ov-value { font-size: 1rem; font-weight: 700; color: #0f172a; margin: 0; }
	.ov-sub { font-size: 0.73rem; color: #94a3b8; margin: 0.1rem 0 0; }
	.ov-risk-high { color: #b91c1c; }
	.ov-risk-moderate { color: #d97706; }
	.ov-risk-stable { color: #15803d; }
	/* Sections */
	.info-section { padding: 1.2rem 1.6rem; border-bottom: 1px solid #f1f5f9; }
	.info-section:last-child { border-bottom: none; }
	.section-heading { font-size: 0.78rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.07em; margin: 0 0 0.9rem; }
	/* Doctor info */
	.doctor-info-row { display: flex; align-items: flex-start; gap: 0.85rem; }
	.doctor-info-avatar { width: 38px; height: 38px; border-radius: 50%; background: linear-gradient(135deg, #0ea5e9, #6366f1); color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; flex-shrink: 0; }
	.doctor-info-name { font-size: 0.95rem; font-weight: 700; color: #0f172a; margin: 0 0 0.2rem; }
	.doctor-info-meta { font-size: 0.82rem; color: #475569; margin: 0.15rem 0 0; }
	.doctor-info-meta.muted { color: #94a3b8; }
	/* Domain grid */
	.domain-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 0.6rem; }
	.domain-chip { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 0.65rem 0.9rem; }
	.domain-name { font-size: 0.83rem; font-weight: 600; color: #334155; margin: 0; }
	.domain-stat { font-size: 0.75rem; color: #94a3b8; margin: 0.2rem 0 0; }
	/* Tab nav */
	.tab-nav { display: flex; gap: 0.4rem; margin-bottom: 1rem; }
	.tab-note { font-size: 0.78rem; color: #94a3b8; margin: 0 0 0.75rem; }
	.empty-tab { font-size: 0.88rem; color: #94a3b8; padding: 1.5rem 0; margin: 0; }
	/* Session table */
	.session-table-wrap { overflow-x: auto; border-radius: 10px; border: 1px solid #e2e8f0; }
	.session-table { width: 100%; border-collapse: collapse; font-size: 0.83rem; }
	.session-table thead { background: #f8fafc; }
	.session-table th { padding: 0.6rem 0.9rem; text-align: left; font-size: 0.7rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.06em; border-bottom: 1px solid #e2e8f0; white-space: nowrap; }
	.session-table td { padding: 0.65rem 0.9rem; border-bottom: 1px solid #f1f5f9; color: #334155; vertical-align: middle; }
	.session-table tr:last-child td { border-bottom: none; }
	.task-cell { color: #475569; }
	.date-cell { white-space: nowrap; color: #64748b; }
	.score-chip { padding: 0.15rem 0.55rem; border-radius: 999px; font-size: 0.76rem; font-weight: 700; }
	.score-good { background: #dcfce7; color: #15803d; }
	.score-mid { background: #fef3c7; color: #92400e; }
	.score-low { background: #fee2e2; color: #b91c1c; }
	/* Reports */
	.reports-list { display: flex; flex-direction: column; gap: 0.75rem; }
	.report-card { border: 1px solid #e2e8f0; border-radius: 10px; padding: 1rem 1.1rem; background: #f8fafc; }
	.report-card-header { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 0.6rem; }
	.report-period-badge { background: #dbeafe; color: #1d4ed8; font-size: 0.72rem; font-weight: 700; padding: 0.18rem 0.6rem; border-radius: 999px; text-transform: uppercase; letter-spacing: 0.05em; }
	.report-range { font-size: 0.82rem; font-weight: 600; color: #334155; }
	.report-generated { font-size: 0.77rem; color: #94a3b8; margin-left: auto; }
	.report-commentary { font-size: 0.85rem; color: #475569; margin: 0; line-height: 1.5; }
	.report-commentary.muted { color: #94a3b8; font-style: italic; }
	.modal-overlay { position: fixed; inset: 0; background: rgba(15, 23, 42, 0.5); display: flex; align-items: center; justify-content: center; z-index: 100; padding: 1rem; }
	.modal { background: #ffffff; border-radius: 16px; width: 420px; max-width: 100%; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2); overflow: hidden; }
	.modal-header { display: flex; align-items: flex-start; gap: 0.9rem; padding: 1.4rem 1.5rem; border-bottom: 1px solid #f1f5f9; }
	.modal-title { font-size: 1.1rem; font-weight: 700; color: #0f172a; margin: 0; }
	.modal-sub { font-size: 0.82rem; color: #64748b; margin: 0.15rem 0 0; }
	.modal-close { margin-left: auto; background: none; border: none; cursor: pointer; font-size: 1rem; color: #94a3b8; }
	.modal-body { padding: 1.4rem 1.5rem; }
	.field-label { display: block; font-size: 0.8rem; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; }
	.field-input { width: 100%; padding: 0.65rem 0.9rem; border: 1.5px solid #e2e8f0; border-radius: 8px; font-size: 0.9rem; box-sizing: border-box; }
	.muted { margin: 0; color: #94a3b8; }
	.modal-footer { display: flex; gap: 0.75rem; justify-content: flex-end; padding: 1rem 1.5rem; background: #f8fafc; border-top: 1px solid #f1f5f9; }
	.btn-outline { padding: 0.55rem 1.2rem; border: 1.5px solid #e2e8f0; border-radius: 8px; background: #ffffff; color: #475569; font-size: 0.88rem; font-weight: 600; cursor: pointer; }
	.btn-primary { padding: 0.55rem 1.4rem; border: none; border-radius: 8px; background: #4f46e5; color: #ffffff; font-size: 0.88rem; font-weight: 600; cursor: pointer; }
	.btn-outline:disabled, .btn-primary:disabled { opacity: 0.55; cursor: not-allowed; }
</style>
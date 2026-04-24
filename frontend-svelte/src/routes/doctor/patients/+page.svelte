<script>
	import { locale as activeLocale, uiText } from '$lib/i18n';
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	import DoctorWorkspaceShell from '$lib/components/DoctorWorkspaceShell.svelte';
	import { user } from '$lib/stores.js';
	import { onMount } from 'svelte';

	let patients = [];
	let analytics = null;
	let loading = true;
	let error = '';
	let userData;
	let searchTerm = '';
	let riskFilter = 'all';
	let sortBy = 'name';
	let sortDirection = 'asc';

	const unsubscribe = user.subscribe((value) => {
		userData = value;
	});

	onMount(() => {
		if (!userData || userData.role !== 'doctor') {
			goto('/login');
			return;
		}

		loadPatients();

		return unsubscribe;
	});

	async function loadPatients() {
		loading = true;
		error = '';

		try {
			const [patientsResp, analyticsResp] = await Promise.all([
				api.get(`/api/doctor/${userData.id}/patients`),
				api.get(`/api/doctor/${userData.id}/analytics`)
			]);

			patients = patientsResp.data.patients || [];
			analytics = analyticsResp.data;
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Failed to load patients';
		} finally {
			loading = false;
		}
	}

	async function unassignPatient(patientId, patientName) {
		const confirmation = confirm(
			`Are you sure you want to unassign ${patientName}?\n\nThis will remove them from your active patient list.`
		);

		if (!confirmation) return;

		try {
			await api.post(`/api/doctor/${userData.id}/unassign/${patientId}`);
			await loadPatients();
		} catch (requestError) {
			alert(requestError.response?.data?.detail || 'Failed to unassign patient');
		}
	}

	function formatDate(dateStr) {
		if (!dateStr) return 'No recent activity';

		return new Date(dateStr).toLocaleDateString('en-GB', {
			day: '2-digit',
			month: 'short',
			year: 'numeric'
		});
	}

	function sortPatients(field) {
		if (sortBy === field) {
			sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
			return;
		}

		sortBy = field;
		sortDirection = 'asc';
	}

	$: mergedPatients = analytics?.patient_summary
		? analytics.patient_summary.map((summary) => ({
				...summary,
				...(patients.find((patient) => patient.patient_id === summary.patient_id) || {})
			}))
		: [];

	$: filteredPatients = mergedPatients
		.filter((patient) => {
			const query = searchTerm.trim().toLowerCase();
			const matchesSearch = !query || [patient.name, patient.email, patient.diagnosis]
				.filter(Boolean)
				.some((value) => value.toLowerCase().includes(query));
			const matchesRisk = riskFilter === 'all' || patient.risk_level === riskFilter;
			return matchesSearch && matchesRisk;
		})
		.sort((left, right) => {
			let leftValue = left[sortBy];
			let rightValue = right[sortBy];

			if (sortBy === 'name') {
				leftValue = (left.name || '').toLowerCase();
				rightValue = (right.name || '').toLowerCase();
			}

			if (sortBy === 'last_activity') {
				leftValue = left.last_activity ? new Date(left.last_activity).getTime() : 0;
				rightValue = right.last_activity ? new Date(right.last_activity).getTime() : 0;
			}

			if (leftValue < rightValue) return sortDirection === 'asc' ? -1 : 1;
			if (leftValue > rightValue) return sortDirection === 'asc' ? 1 : -1;
			return 0;
		});
</script>

<DoctorWorkspaceShell
	title={uiText("Patients", $activeLocale)}
	subtitle={uiText("A dedicated patient management view for searching, filtering, and opening detailed records without crowding the dashboard.", $activeLocale)}
>
	{#if loading}
		<section class="state-card">
			<p>{uiText("Loading patient list...", $activeLocale)}</p>
		</section>
	{:else if error}
		<section class="state-card error-state">
			<p>{error}</p>
		</section>
	{:else}
		<section class="toolbar">
			<div class="field-group search-field">
				<label for="patientSearch">{uiText("Search", $activeLocale)}</label>
				<input id="patientSearch" bind:value={searchTerm} placeholder={uiText("Search by patient, email, or diagnosis", $activeLocale)} />
			</div>
			<div class="field-group">
				<label for="riskFilter">{uiText("Risk", $activeLocale)}</label>
				<select id="riskFilter" bind:value={riskFilter}>
					<option value="all">{uiText("All risk levels", $activeLocale)}</option>
					<option value="high">{uiText("High", $activeLocale)}</option>
					<option value="medium">{uiText("Medium", $activeLocale)}</option>
					<option value="low">{uiText("Low", $activeLocale)}</option>
				</select>
			</div>
		</section>

		<section class="table-card">
			<div class="table-header">
				<div>
					<p class="table-kicker">{uiText("Patient Directory", $activeLocale)}</p>
					<h2>{filteredPatients.length} {uiText("patients in view", $activeLocale)}</h2>
				</div>
			</div>

			{#if filteredPatients.length === 0}
				<div class="empty-card">
					<h3>{uiText("No patients match the current filters", $activeLocale)}</h3>
					<p>{uiText("Adjust the search or risk filter to broaden the list.", $activeLocale)}</p>
				</div>
			{:else}
				<div class="table-wrap">
					<table>
						<thead>
							<tr>
								<th><button on:click={() => sortPatients('name')}>{uiText("Patient", $activeLocale)}</button></th>
								<th>{uiText("Diagnosis", $activeLocale)}</th>
								<th><button on:click={() => sortPatients('risk_level')}>{uiText("Risk", $activeLocale)}</button></th>
								<th><button on:click={() => sortPatients('adherence_rate')}>{uiText("Adherence", $activeLocale)}</button></th>
								<th><button on:click={() => sortPatients('total_sessions')}>{uiText("Sessions", $activeLocale)}</button></th>
								<th><button on:click={() => sortPatients('avg_score')}>{uiText("Score", $activeLocale)}</button></th>
								<th><button on:click={() => sortPatients('avg_accuracy')}>{uiText("Accuracy", $activeLocale)}</button></th>
								<th><button on:click={() => sortPatients('last_activity')}>{uiText("Last Activity", $activeLocale)}</button></th>
								<th>{uiText("Actions", $activeLocale)}</th>
							</tr>
						</thead>
						<tbody>
							{#each filteredPatients as patient}
								<tr>
									<td>
										<div class="patient-name">{patient.name}</div>
										<div class="patient-email">{patient.email}</div>
									</td>
									<td>{patient.diagnosis || 'Not recorded'}</td>
									<td><span class="risk-pill {patient.risk_level}">{patient.risk_level}</span></td>
									<td>{patient.adherence_rate}%</td>
									<td>{patient.total_sessions}</td>
									<td>{patient.avg_score}</td>
									<td>{patient.avg_accuracy}%</td>
									<td>{formatDate(patient.last_activity)}</td>
									<td>
										<div class="action-row">
											<button class="primary-btn" on:click={() => goto(`/doctor/patient/${patient.patient_id}`)}>{uiText("Open", $activeLocale)}</button>
											<button class="outline-btn" on:click={() => goto(`/doctor/patient/${patient.patient_id}/reports`)}>{uiText("Reports", $activeLocale)}</button>
											<button class="ghost-btn" on:click={() => unassignPatient(patient.patient_id, patient.name)}>{uiText("Unassign", $activeLocale)}</button>
										</div>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</section>
	{/if}
</DoctorWorkspaceShell>

<style>
	.toolbar,
	.table-card,
	.state-card,
	.empty-card {
		background: #f8fafc;
		border: 1px solid #e2e8f0;
		border-radius: 24px;
		box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
	}

	.toolbar {
		padding: 1rem;
		display: grid;
		grid-template-columns: minmax(0, 1.5fr) minmax(220px, 0.5fr);
		gap: 1rem;
	}

	.field-group {
		display: grid;
		gap: 0.45rem;
	}

	label,
	.table-kicker {
		margin: 0;
		font-size: 0.78rem;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: #6b7280;
	}

	input,
	select {
		width: 100%;
		border: 1px solid #d1d5db;
		border-radius: 16px;
		padding: 0.9rem 1rem;
		font: inherit;
		background: #f9fafb;
		color: #111827;
	}

	.table-card,
	.state-card,
	.empty-card {
		padding: 1.2rem;
	}

	.table-header {
		margin-bottom: 1rem;
	}

	h2,
	h3 {
		margin: 0.2rem 0 0;
		color: #111827;
	}

	.empty-card p,
	.state-card p,
	.patient-email {
		margin: 0.35rem 0 0;
		color: #6b7280;
	}

	.table-wrap {
		overflow-x: auto;
	}

	table {
		width: 100%;
		border-collapse: collapse;
	}

	th,
	td {
		padding: 0.95rem 0.8rem;
		border-top: 1px solid #eef2f7;
		text-align: left;
		vertical-align: top;
		color: #374151;
	}

	th button {
		border: none;
		background: none;
		padding: 0;
		font: inherit;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: #6b7280;
		cursor: pointer;
	}

	.patient-name {
		font-weight: 800;
		color: #111827;
	}

	.risk-pill {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		border-radius: 999px;
		padding: 0.28rem 0.72rem;
		font-size: 0.78rem;
		font-weight: 800;
		text-transform: uppercase;
	}

	.risk-pill.high {
		background: #fee2e2;
		color: #b91c1c;
	}

	.risk-pill.medium {
		background: #fef3c7;
		color: #b45309;
	}

	.risk-pill.low {
		background: #dcfce7;
		color: #15803d;
	}

	.action-row {
		display: flex;
		gap: 0.55rem;
		flex-wrap: wrap;
	}

	.primary-btn,
	.outline-btn,
	.ghost-btn {
		border-radius: 999px;
		padding: 0.65rem 0.95rem;
		font-weight: 700;
		cursor: pointer;
	}

	.primary-btn {
		border: 1px solid #4f46e5;
		background: #4f46e5;
		color: #ffffff;
	}

	.outline-btn,
	.ghost-btn {
		border: 1px solid #d1d5db;
		background: #ffffff;
		color: #111827;
	}

	@media (max-width: 900px) {
		.toolbar {
			grid-template-columns: 1fr;
		}
	}
</style>
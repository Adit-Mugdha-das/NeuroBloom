<script>
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	import DoctorWorkspaceShell from '$lib/components/DoctorWorkspaceShell.svelte';
	import { user } from '$lib/stores.js';
	import { onMount } from 'svelte';

	let directory = null;
	let loading = true;
	let error = '';
	let userData;

	const unsubscribe = user.subscribe((value) => {
		userData = value;
	});

	onMount(() => {
		if (!userData || userData.role !== 'doctor') {
			goto('/login');
			return;
		}

		loadDirectory();

		return unsubscribe;
	});

	async function loadDirectory() {
		loading = true;
		error = '';

		try {
			const response = await api.get(`/api/doctor/${userData.id}/prescriptions`);
			directory = response.data;
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Failed to load prescriptions directory';
		} finally {
			loading = false;
		}
	}

	function formatDate(dateValue) {
		if (!dateValue) return 'No prescriptions yet';
		return new Date(dateValue).toLocaleDateString('en-GB', {
			day: '2-digit',
			month: 'short',
			year: 'numeric'
		});
	}

	$: summaryCards = directory
		? [
				{ label: 'Assigned Patients', value: directory.summary.assigned_patients, tone: 'neutral' },
				{ label: 'Patients With Prescriptions', value: directory.summary.patients_with_prescriptions, tone: 'teal' },
				{ label: 'Total Prescriptions', value: directory.summary.total_prescriptions, tone: 'indigo' },
				{ label: 'Active Prescriptions', value: directory.summary.active_prescriptions, tone: 'cyan' }
			]
		: [];
</script>

<DoctorWorkspaceShell
	title="Prescriptions"
	subtitle="Issue, track, and revise structured digital prescriptions with PDF output and patient delivery from one clinical workspace."
>
	{#if loading}
		<section class="state-card"><p>Loading prescription directory...</p></section>
	{:else if error}
		<section class="state-card error-state"><p>{error}</p></section>
	{:else}
		<section class="summary-grid">
			{#each summaryCards as card}
				<article class="summary-card {card.tone}">
					<p>{card.label}</p>
					<strong>{card.value}</strong>
				</article>
			{/each}
		</section>

		<section class="directory-grid">
			{#if !directory?.patients?.length}
				<div class="empty-card">
					<h2>No assigned patients yet</h2>
					<p>Once patients are assigned, their prescription history and issuing workspace will appear here.</p>
				</div>
			{:else}
				{#each directory.patients as patient}
					<article class="patient-card">
						<div class="patient-head">
							<div>
								<p class="card-kicker">Prescription Record</p>
								<h2>{patient.full_name}</h2>
								<p class="card-subtitle">{patient.diagnosis || patient.treatment_goal || 'No diagnosis or treatment goal recorded yet.'}</p>
							</div>
							<button class="primary-btn" on:click={() => goto(`/doctor/patient/${patient.patient_id}/prescriptions`)}>
								Open Workspace
							</button>
						</div>

						<div class="meta-grid">
							<div><span>Total prescriptions</span><strong>{patient.prescription_count}</strong></div>
							<div><span>Active</span><strong>{patient.active_prescription_count}</strong></div>
							<div><span>Latest issued</span><strong>{formatDate(patient.last_prescribed_at)}</strong></div>
							<div><span>Treatment goal</span><strong>{patient.treatment_goal || 'Not recorded'}</strong></div>
						</div>

						{#if patient.latest_prescription}
							<div class="latest-card">
								<div>
									<p class="latest-kicker">Latest Prescription</p>
									<h3>{patient.latest_prescription.title}</h3>
									<p>{patient.latest_prescription.summary || patient.latest_prescription.patient_instructions}</p>
								</div>
								<div class="latest-meta">
									<span>Version {patient.latest_prescription.version_number}</span>
									<span class="status-pill status-{patient.latest_prescription.status}">{patient.latest_prescription.status.replaceAll('_', ' ')}</span>
								</div>
							</div>
						{:else}
							<div class="latest-card empty">
								<p>No prescription has been issued to this patient yet.</p>
							</div>
						{/if}
					</article>
				{/each}
			{/if}
		</section>
	{/if}
</DoctorWorkspaceShell>

<style>
	.summary-grid,
	.directory-grid,
	.meta-grid {
		display: grid;
		gap: 1rem;
	}

	.summary-grid {
		grid-template-columns: repeat(4, minmax(0, 1fr));
	}

	.directory-grid {
		grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
	}

	.state-card,
	.empty-card,
	.summary-card,
	.patient-card,
	.latest-card {
		background: #ffffff;
		border: 1px solid #e5e7eb;
		border-radius: 24px;
		padding: 1.2rem;
		box-shadow: 0 16px 30px rgba(15, 23, 42, 0.05);
	}

	.summary-card {
		background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
	}

	.summary-card.teal {
		background: linear-gradient(180deg, #ffffff 0%, #ecfeff 100%);
	}

	.summary-card.indigo {
		background: linear-gradient(180deg, #ffffff 0%, #eef2ff 100%);
	}

	.summary-card.cyan {
		background: linear-gradient(180deg, #ffffff 0%, #ecfeff 100%);
	}

	.summary-card p,
	.card-kicker,
	.latest-kicker {
		margin: 0;
		font-size: 0.78rem;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: #6b7280;
	}

	.summary-card strong {
		display: block;
		margin-top: 0.45rem;
		font-size: 1.9rem;
		color: #111827;
	}

	h2,
	h3 {
		margin: 0.2rem 0 0;
		color: #111827;
	}

	.state-card p,
	.empty-card p,
	.card-subtitle,
	.latest-card p {
		color: #6b7280;
	}

	.patient-card {
		display: grid;
		gap: 1rem;
	}

	.patient-head {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: flex-start;
	}

	.meta-grid {
		grid-template-columns: repeat(2, minmax(0, 1fr));
	}

	.meta-grid div {
		display: grid;
		gap: 0.25rem;
		padding: 0.9rem;
		border-radius: 18px;
		background: #f8fafc;
	}

	.meta-grid span {
		font-size: 0.84rem;
		color: #6b7280;
	}

	.meta-grid strong {
		color: #111827;
	}

	.latest-card {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: flex-start;
		background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
	}

	.latest-card.empty {
		justify-content: flex-start;
	}

	.latest-meta {
		display: grid;
		gap: 0.5rem;
		justify-items: end;
	}

	.status-pill {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 0.35rem 0.7rem;
		border-radius: 999px;
		font-size: 0.78rem;
		font-weight: 800;
		text-transform: capitalize;
	}

	.status-pill.status-active {
		background: #dcfce7;
		color: #166534;
	}

	.status-pill.status-revised,
	.status-pill.status-inactive {
		background: #e5e7eb;
		color: #4b5563;
	}

	.primary-btn {
		border-radius: 999px;
		padding: 0.8rem 1rem;
		font-weight: 700;
		cursor: pointer;
		border: 1px solid #0f766e;
		background: linear-gradient(135deg, #0f766e, #0ea5a4);
		color: #ffffff;
	}

	@media (max-width: 1024px) {
		.summary-grid {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}

	@media (max-width: 760px) {
		.summary-grid,
		.meta-grid {
			grid-template-columns: 1fr;
		}

		.patient-head,
		.latest-card {
			flex-direction: column;
		}

		.latest-meta {
			justify-items: start;
		}
	}
</style>
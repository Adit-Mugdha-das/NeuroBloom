<script>
	import { goto } from '$app/navigation';
	import DoctorWorkspaceShell from '$lib/components/DoctorWorkspaceShell.svelte';
	import api from '$lib/api.js';
	import { user } from '$lib/stores.js';
	import { onMount } from 'svelte';

	let patients = [];
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

		loadPatients();

		return unsubscribe;
	});

	async function loadPatients() {
		loading = true;
		error = '';

		try {
			const response = await api.get(`/api/doctor/${userData.id}/patients`);
			patients = response.data.patients || [];
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Failed to load report directory';
		} finally {
			loading = false;
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
</script>

<DoctorWorkspaceShell
	title="Reports"
	subtitle="A report entry page that routes clinicians into the existing patient-specific report workspace without cluttering the dashboard."
>
	{#if loading}
		<section class="state-card"><p>Loading reports directory...</p></section>
	{:else if error}
		<section class="state-card error-state"><p>{error}</p></section>
	{:else}
		<section class="report-grid">
			{#if patients.length === 0}
				<div class="empty-card">
					<h2>No assigned patients yet</h2>
					<p>Once patients are assigned, their report workspace will appear here.</p>
				</div>
			{:else}
				{#each patients as patient}
					<article class="report-card">
						<div>
							<p class="card-kicker">Patient Reports</p>
							<h2>{patient.full_name}</h2>
							<p class="card-subtitle">{patient.diagnosis || 'Diagnosis not recorded'}</p>
						</div>
						<div class="report-meta">
							<div><span>Baseline</span><strong>{patient.baseline_completed ? 'Complete' : 'Pending'}</strong></div>
							<div><span>Last Activity</span><strong>{formatDate(patient.last_activity)}</strong></div>
						</div>
						<div class="report-actions">
							<button class="outline-btn" on:click={() => goto(`/doctor/patient/${patient.patient_id}`)}>Open Patient</button>
							<button class="primary-btn" on:click={() => goto(`/doctor/patient/${patient.patient_id}/reports`)}>Open Reports</button>
						</div>
					</article>
				{/each}
			{/if}
		</section>
	{/if}
</DoctorWorkspaceShell>

<style>
	.report-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
		gap: 1rem;
	}

	.report-card,
	.state-card,
	.empty-card {
		background: #ffffff;
		border: 1px solid #e5e7eb;
		border-radius: 24px;
		padding: 1.2rem;
		box-shadow: 0 16px 30px rgba(15, 23, 42, 0.05);
	}

	.card-kicker {
		margin: 0;
		font-size: 0.78rem;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: #6b7280;
	}

	h2 {
		margin: 0.2rem 0 0;
		color: #111827;
	}

	.card-subtitle,
	.state-card p,
	.empty-card p {
		margin: 0.45rem 0 0;
		color: #6b7280;
	}

	.report-meta {
		display: grid;
		gap: 0.75rem;
		margin-top: 1rem;
	}

	.report-meta div {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		padding-top: 0.75rem;
		border-top: 1px solid #eef2f7;
	}

	.report-meta span {
		color: #6b7280;
	}

	.report-meta strong {
		color: #111827;
	}

	.report-actions {
		display: flex;
		gap: 0.65rem;
		margin-top: 1rem;
		flex-wrap: wrap;
	}

	.primary-btn,
	.outline-btn {
		border-radius: 999px;
		padding: 0.7rem 1rem;
		font-weight: 700;
		cursor: pointer;
	}

	.primary-btn {
		border: 1px solid #4f46e5;
		background: #4f46e5;
		color: #ffffff;
	}

	.outline-btn {
		border: 1px solid #d1d5db;
		background: #ffffff;
		color: #111827;
	}
</style>
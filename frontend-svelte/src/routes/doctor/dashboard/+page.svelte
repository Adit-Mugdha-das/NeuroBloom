<script>
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	import { user } from '$lib/stores.js';
	import { onMount } from 'svelte';
	
	let patients = [];
	let loading = true;
	let error = '';
	let userData;
	
	// Subscribe to user store
	const unsubscribe = user.subscribe(value => {
		userData = value;
	});
	
	onMount(() => {
		// Check if user is logged in as doctor
		if (!userData || userData.role !== 'doctor') {
			goto('/login');
			return;
		}
		
		loadPatients();
		
		return unsubscribe;
	});
	
	async function loadPatients() {
		try {
			const response = await api.get(`/api/doctor/${userData.id}/patients`);
			patients = response.data.patients;
		} catch (err) {
			error = 'Failed to load patients';
			console.error('Error loading patients:', err);
		} finally {
			loading = false;
		}
	}
	
	function viewPatient(patientId) {
		goto(`/doctor/patient/${patientId}`);
	}
	
	function formatDate(dateStr) {
		if (!dateStr) return 'Never';
		return new Date(dateStr).toLocaleDateString();
	}
	
	function isRecentlyActive(lastActivity) {
		if (!lastActivity) return false;
		const sevenDaysAgo = new Date(Date.now() - 7*24*60*60*1000);
		return new Date(lastActivity) > sevenDaysAgo;
	}
	
	$: activePatients = patients.filter(p => isRecentlyActive(p.last_activity));
	$: patientsWithBaseline = patients.filter(p => p.baseline_completed);
</script>

<div class="doctor-dashboard">
	<header>
		<h1>👨‍⚕️ Doctor Dashboard</h1>
		<p>Welcome, Dr. {userData?.fullName || userData?.email}</p>
	</header>
	
	{#if loading}
		<div class="loading">Loading patients...</div>
	{:else if error}
		<div class="error">{error}</div>
	{:else}
		<div class="stats-cards">
			<div class="stat-card">
				<div class="stat-number">{patients.length}</div>
				<div class="stat-label">Total Patients</div>
			</div>
			<div class="stat-card">
				<div class="stat-number">{activePatients.length}</div>
				<div class="stat-label">Active (7 days)</div>
			</div>
			<div class="stat-card">
				<div class="stat-number">{patientsWithBaseline.length}</div>
				<div class="stat-label">Baseline Complete</div>
			</div>
		</div>
		
		<div class="patients-section">
			<h2>Your Patients</h2>
			
			{#if patients.length === 0}
				<div class="no-patients">
					<p>📋 No patients assigned yet.</p>
					<p class="subtitle">Patients will appear here once they are assigned to you.</p>
				</div>
			{:else}
				<div class="patients-table">
					<table>
						<thead>
							<tr>
								<th>Patient</th>
								<th>Diagnosis</th>
								<th>Assigned</th>
								<th>Last Activity</th>
								<th>Baseline</th>
								<th>Actions</th>
							</tr>
						</thead>
						<tbody>
							{#each patients as patient}
								<tr>
									<td>
										<div class="patient-name">
											{patient.full_name || patient.email}
										</div>
									</td>
									<td>{patient.diagnosis || 'N/A'}</td>
									<td>{formatDate(patient.assigned_at)}</td>
									<td>
										<span class="activity {isRecentlyActive(patient.last_activity) ? 'active' : 'inactive'}">
											{formatDate(patient.last_activity)}
										</span>
									</td>
									<td>
										<span class="badge {patient.baseline_completed ? 'complete' : 'pending'}">
											{patient.baseline_completed ? '✓ Complete' : 'Pending'}
										</span>
									</td>
									<td>
										<button 
											class="view-btn"
											on:click={() => viewPatient(patient.patient_id)}
										>
											View Details
										</button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.doctor-dashboard {
		max-width: 1400px;
		margin: 0 auto;
		padding: 2rem;
		min-height: 100vh;
		background: #f8f9fa;
	}
	
	header {
		margin-bottom: 2rem;
	}
	
	h1 {
		font-size: 2rem;
		color: #333;
		margin-bottom: 0.5rem;
	}
	
	header p {
		color: #666;
		font-size: 1.1rem;
	}
	
	.stats-cards {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
		margin-bottom: 2rem;
	}
	
	.stat-card {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		padding: 1.5rem;
		border-radius: 12px;
		text-align: center;
		box-shadow: 0 4px 6px rgba(0,0,0,0.1);
	}
	
	.stat-number {
		font-size: 2.5rem;
		font-weight: bold;
		margin-bottom: 0.5rem;
	}
	
	.stat-label {
		font-size: 0.9rem;
		opacity: 0.9;
	}
	
	.patients-section {
		background: white;
		border-radius: 12px;
		padding: 2rem;
		box-shadow: 0 2px 10px rgba(0,0,0,0.1);
	}
	
	h2 {
		margin-bottom: 1.5rem;
		color: #333;
	}
	
	.patients-table {
		overflow-x: auto;
	}
	
	table {
		width: 100%;
		border-collapse: collapse;
	}
	
	th {
		background: #f8f9fa;
		padding: 1rem;
		text-align: left;
		font-weight: 600;
		color: #555;
		border-bottom: 2px solid #e0e0e0;
	}
	
	td {
		padding: 1rem;
		border-bottom: 1px solid #e0e0e0;
	}
	
	tr:hover {
		background: #f8f9fa;
	}
	
	.patient-name {
		font-weight: 500;
		color: #333;
	}
	
	.activity.active {
		color: #28a745;
		font-weight: 500;
	}
	
	.activity.inactive {
		color: #999;
	}
	
	.badge {
		padding: 0.25rem 0.75rem;
		border-radius: 20px;
		font-size: 0.85rem;
		font-weight: 500;
		display: inline-block;
	}
	
	.badge.complete {
		background: #d4edda;
		color: #155724;
	}
	
	.badge.pending {
		background: #fff3cd;
		color: #856404;
	}
	
	.view-btn {
		background: #667eea;
		color: white;
		border: none;
		padding: 0.5rem 1rem;
		border-radius: 6px;
		cursor: pointer;
		font-weight: 500;
		transition: background 0.3s;
	}
	
	.view-btn:hover {
		background: #5568d3;
	}
	
	.no-patients {
		text-align: center;
		padding: 3rem;
		color: #999;
	}
	
	.no-patients .subtitle {
		font-size: 0.9rem;
		margin-top: 0.5rem;
	}
	
	.loading, .error {
		text-align: center;
		padding: 2rem;
		font-size: 1.1rem;
	}
	
	.error {
		color: #c33;
		background: #fee;
		border-radius: 8px;
		margin: 2rem 0;
	}
</style>

<script>
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	import { user } from '$lib/stores.js';
	import { onMount } from 'svelte';
	
	let patients = [];
	let pendingRequests = [];
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
		
		loadData();
		
		return unsubscribe;
	});
	
	async function loadData() {
		try {
			const [patientsResp, requestsResp] = await Promise.all([
				api.get(`/api/doctor/${userData.id}/patients`),
				api.get(`/api/doctor/${userData.id}/pending-requests`)
			]);
			patients = patientsResp.data.patients;
			pendingRequests = requestsResp.data.requests;
		} catch (err) {
			error = 'Failed to load data';
			console.error('Error loading data:', err);
		} finally {
			loading = false;
		}
	}
	
	async function approveRequest(requestId) {
		if (!confirm('Approve this assignment request?')) return;
		
		try {
			await api.post(`/api/doctor/request/${requestId}/approve`, null, {
				params: {
					doctor_id: userData.id,
					treatment_goal: 'Improve cognitive function through targeted training'
				}
			});
			alert('Request approved! Patient has been assigned to you.');
			await loadData();
		} catch (err) {
			alert('Failed to approve request: ' + (err.response?.data?.detail || 'Unknown error'));
		}
	}
	
	async function rejectRequest(requestId) {
		const reason = prompt('Reason for rejection (optional):');
		if (reason === null) return; // User cancelled
		
		try {
			await api.post(`/api/doctor/request/${requestId}/reject`, null, {
				params: {
					doctor_id: userData.id,
					notes: reason || 'Request declined'
				}
			});
			alert('Request rejected.');
			await loadData();
		} catch (err) {
			alert('Failed to reject request: ' + (err.response?.data?.detail || 'Unknown error'));
		}
	}
	
	async function unassignPatient(patientId, patientName) {
		const confirmation = confirm(
			`Are you sure you want to unassign ${patientName}?\n\nThis will remove them from your patient list. They can request reassignment later.`
		);
		
		if (!confirmation) return;
		
		try {
			await api.post(`/api/doctor/${userData.id}/unassign/${patientId}`);
			alert('Patient unassigned successfully.');
			await loadData();
		} catch (err) {
			alert('Failed to unassign patient: ' + (err.response?.data?.detail || 'Unknown error'));
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
		<!-- Pending Requests Section -->
		{#if pendingRequests.length > 0}
			<div class="pending-requests-section">
				<h2>📬 Pending Assignment Requests ({pendingRequests.length})</h2>
				<div class="requests-list">
					{#each pendingRequests as request}
						<div class="request-card">
							<div class="request-info">
								<h3>{request.patient_email}</h3>
								{#if request.patient_name}
									<p class="patient-name">{request.patient_name}</p>
								{/if}
								{#if request.diagnosis}
									<p class="diagnosis">Diagnosis: {request.diagnosis}</p>
								{/if}
								{#if request.reason}
									<p class="reason"><strong>Reason:</strong> {request.reason}</p>
								{/if}
								{#if request.message}
									<p class="message"><strong>Message:</strong> {request.message}</p>
								{/if}
								<p class="date">Requested: {formatDate(request.created_at)}</p>
							</div>
							<div class="request-actions">
								<button class="btn-approve" on:click={() => approveRequest(request.id)}>
									✓ Approve
								</button>
								<button class="btn-reject" on:click={() => rejectRequest(request.id)}>
									✗ Reject
								</button>
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}
		
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
								<th>Name</th>
								<th>Email</th>
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
											{patient.full_name || 'Not provided'}
										</div>
									</td>
									<td>
										<div class="patient-email">
											{patient.email}
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
										<div class="action-buttons">
											<button 
												class="view-btn"
												on:click={() => viewPatient(patient.patient_id)}
											>
												View Details
											</button>
											<button 
												class="unassign-btn"
												on:click={() => unassignPatient(patient.patient_id, patient.full_name || patient.email)}
											>
												Unassign
											</button>
										</div>
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
	
	.patient-email {
		color: #667eea;
		font-size: 0.9rem;
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
	
	/* Pending Requests Section */
	.pending-requests-section {
		margin-bottom: 3rem;
		background: #fffbf0;
		padding: 1.5rem;
		border-radius: 12px;
		border: 2px solid #ffd700;
	}
	
	.pending-requests-section h2 {
		color: #667eea;
		margin-bottom: 1.5rem;
	}
	
	.requests-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.request-card {
		background: white;
		border: 2px solid #e0e0e0;
		border-radius: 10px;
		padding: 1.5rem;
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 1.5rem;
	}
	
	.request-info {
		flex: 1;
	}
	
	.request-info h3 {
		color: #667eea;
		margin: 0 0 0.5rem 0;
		font-size: 1.1rem;
	}
	
	.request-info p {
		margin: 0.3rem 0;
		color: #555;
		font-size: 0.9rem;
	}
	
	.patient-name {
		font-weight: 600;
		color: #333;
	}
	
	.diagnosis {
		color: #764ba2;
		font-weight: 500;
	}
	
	.reason, .message {
		font-style: italic;
		line-height: 1.5;
	}
	
	.date {
		color: #999;
		font-size: 0.85rem;
		margin-top: 0.5rem;
	}
	
	.request-actions {
		display: flex;
		gap: 0.75rem;
		flex-shrink: 0;
	}
	
	.btn-approve,
	.btn-reject {
		padding: 0.75rem 1.5rem;
		border: none;
		border-radius: 8px;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
		font-size: 0.9rem;
	}
	
	.btn-approve {
		background: #28a745;
		color: white;
	}
	
	.btn-approve:hover {
		background: #218838;
		transform: translateY(-2px);
	}
	
	.btn-reject {
		background: #dc3545;
		color: white;
	}
	
	.btn-reject:hover {
		background: #c82333;
		transform: translateY(-2px);
	}
	
	.action-buttons {
		display: flex;
		gap: 0.5rem;
		flex-wrap: wrap;
	}
	
	.view-btn,
	.unassign-btn {
		padding: 0.5rem 1rem;
		border: none;
		border-radius: 6px;
		cursor: pointer;
		font-weight: 500;
		transition: all 0.2s;
		font-size: 0.85rem;
	}
	
	.view-btn {
		background: #667eea;
		color: white;
	}
	
	.view-btn:hover {
		background: #5568d3;
		transform: translateY(-1px);
	}
	
	.unassign-btn {
		background: #dc3545;
		color: white;
	}
	
	.unassign-btn:hover {
		background: #c82333;
		transform: translateY(-1px);
	}
</style>


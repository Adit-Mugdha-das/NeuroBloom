<script>
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	import { user } from '$lib/stores.js';
	import { onMount } from 'svelte';
	
	let currentUser = null;
	let doctors = [];
	let myRequests = [];
	let loading = true;
	let error = '';
	let showRequestModal = false;
	let selectedDoctor = null;
	
	// Request form fields
	let fullName = '';
	let reason = '';
	let message = '';
	let diagnosis = '';
	
	user.subscribe(value => {
		currentUser = value;
	});
	
	onMount(async () => {
		if (!currentUser) {
			goto('/login');
			return;
		}
		
		await loadData();
	});
	
	async function loadData() {
		loading = true;
		try {
			// Load available doctors
			const doctorsResp = await api.get('/api/doctor/available-doctors');
			doctors = doctorsResp.data.doctors;
			
			// Load patient's requests
			const requestsResp = await api.get(`/api/doctor/patient/${currentUser.id}/requests`);
			myRequests = requestsResp.data.requests;
		} catch (err) {
			error = 'Failed to load doctors';
			console.error(err);
		} finally {
			loading = false;
		}
	}
	
	function openRequestModal(doctor) {
		selectedDoctor = doctor;
		showRequestModal = true;
		fullName = currentUser.full_name || '';
		reason = '';
		message = '';
		diagnosis = '';
	}
	
	function closeRequestModal() {
		showRequestModal = false;
		selectedDoctor = null;
	}
	
	async function submitRequest() {
		if (!selectedDoctor) return;
		
		if (!fullName.trim()) {
			alert('Please enter your full name');
			return;
		}
		
		try {
			// Update user's full name if it's not set
			if (!currentUser.full_name) {
				await api.patch(`/api/auth/patient/${currentUser.id}/profile`, null, {
					params: {
						full_name: fullName.trim()
					}
				});
				currentUser.full_name = fullName.trim();
			}
			
			await api.post('/api/doctor/request-assignment', null, {
				params: {
					patient_id: currentUser.id,
					doctor_id: selectedDoctor.id,
					reason: reason || 'Seeking professional oversight',
					message: message || null,
					diagnosis: diagnosis || null
				}
			});
			
			alert('Request sent successfully! The doctor will review your request.');
			closeRequestModal();
			await loadData(); // Reload to show new request
		} catch (err) {
			const errorMsg = err.response?.data?.detail || 'Failed to send request';
			alert(errorMsg);
		}
	}
	
	function getStatusBadgeClass(status) {
		switch (status) {
			case 'pending': return 'status-pending';
			case 'approved': return 'status-approved';
			case 'rejected': return 'status-rejected';
			default: return '';
		}
	}
	
	function formatDate(dateStr) {
		if (!dateStr) return '';
		return new Date(dateStr).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}
</script>

<div class="page-container">
	<h1>🏥 Find a Healthcare Provider</h1>
	<p class="subtitle">Browse verified doctors and request assignment for professional monitoring</p>
	
	{#if loading}
		<div class="loading">Loading doctors...</div>
	{:else if error}
		<div class="error">{error}</div>
	{:else}
		<!-- My Requests Section -->
		{#if myRequests.length > 0}
			<div class="my-requests-section">
				<h2>📋 My Requests</h2>
				<div class="requests-list">
					{#each myRequests as request}
						<div class="request-card">
							<div class="request-header">
								<h3>{request.doctor_name}</h3>
								<span class="status-badge {getStatusBadgeClass(request.status)}">
									{request.status}
								</span>
							</div>
							<div class="request-details">
								<p><strong>Specialization:</strong> {request.doctor_specialization}</p>
								{#if request.reason}
									<p><strong>Reason:</strong> {request.reason}</p>
								{/if}
								<p><strong>Requested:</strong> {formatDate(request.created_at)}</p>
								{#if request.responded_at}
									<p><strong>Responded:</strong> {formatDate(request.responded_at)}</p>
								{/if}
								{#if request.doctor_notes}
									<div class="doctor-notes">
										<strong>Doctor's Response:</strong>
										<p>{request.doctor_notes}</p>
									</div>
								{/if}
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}
		
		<!-- Available Doctors Section -->
		<div class="doctors-section">
			<h2>👨‍⚕️ Available Doctors</h2>
			{#if doctors.length === 0}
				<div class="no-doctors">
					<p>No doctors available at the moment. Please check back later.</p>
				</div>
			{:else}
				<div class="doctors-grid">
					{#each doctors as doctor}
						<div class="doctor-card">
							<div class="doctor-icon">👨‍⚕️</div>
							<h3>{doctor.full_name}</h3>
							<p class="specialization">{doctor.specialization}</p>
							{#if doctor.institution}
								<p class="institution">🏥 {doctor.institution}</p>
							{/if}
							<button class="request-btn" on:click={() => openRequestModal(doctor)}>
								Request Assignment
							</button>
						</div>
					{/each}
				</div>
			{/if}
		</div>
	{/if}
</div>

<!-- Request Modal -->
{#if showRequestModal && selectedDoctor}
	<div class="modal-overlay" on:click={closeRequestModal}>
		<div class="modal-content" on:click|stopPropagation>
			<div class="modal-header">
				<h2>Request Assignment to {selectedDoctor.full_name}</h2>
				<button class="close-btn" on:click={closeRequestModal}>×</button>
			</div>
			
			<div class="modal-body">
				<p class="modal-info">
					Send a request to be assigned to this doctor for professional monitoring of your cognitive training.
				</p>
				
				<div class="form-group">
					<label for="reason">Reason for Request *</label>
					<input 
						type="text" 
						id="reason" 
						bind:value={reason}
						placeholder="e.g., Need professional oversight, diagnosed with MS"
					/>
				</div>
				
				<div class="form-group">
					<label for="diagnosis">Diagnosis (Optional)</label>
					<input 
						type="text" 
						id="diagnosis" 
						bind:value={diagnosis}
						placeholder="e.g., Multiple Sclerosis, RRMS"
					/>
				</div>
				
				<div class="form-group">
					<label for="message">Additional Message (Optional)</label>
					<textarea 
						id="message" 
						bind:value={message}
						placeholder="Any additional information for the doctor..."
						rows="4"
					></textarea>
				</div>
			</div>
			
			<div class="modal-footer">
				<button class="btn-cancel" on:click={closeRequestModal}>Cancel</button>
				<button class="btn-submit" on:click={submitRequest} disabled={!fullName.trim() || !reason.trim()}>
					Send Request
				</button>
			</div>
		</div>
	</div>
{/if}

<style>
	.page-container {
		max-width: 1200px;
		margin: 0 auto;
		padding: 30px 20px;
	}
	
	h1 {
		color: #667eea;
		margin-bottom: 10px;
	}
	
	.subtitle {
		color: #666;
		font-size: 16px;
		margin-bottom: 40px;
	}
	
	.loading {
		text-align: center;
		padding: 50px;
		color: #666;
	}
	
	.error {
		background: #fee;
		color: #c33;
		padding: 15px;
		border-radius: 8px;
		margin-bottom: 20px;
	}
	
	/* My Requests Section */
	.my-requests-section {
		margin-bottom: 50px;
	}
	
	.my-requests-section h2 {
		color: #333;
		margin-bottom: 20px;
	}
	
	.requests-list {
		display: flex;
		flex-direction: column;
		gap: 15px;
	}
	
	.request-card {
		background: white;
		border: 2px solid #e0e0e0;
		border-radius: 12px;
		padding: 20px;
	}
	
	.request-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 15px;
		padding-bottom: 15px;
		border-bottom: 1px solid #f0f0f0;
	}
	
	.request-header h3 {
		margin: 0;
		color: #667eea;
	}
	
	.status-badge {
		padding: 6px 12px;
		border-radius: 20px;
		font-size: 12px;
		font-weight: 600;
		text-transform: uppercase;
	}
	
	.status-pending {
		background: #fff3cd;
		color: #856404;
	}
	
	.status-approved {
		background: #d4edda;
		color: #155724;
	}
	
	.status-rejected {
		background: #f8d7da;
		color: #721c24;
	}
	
	.request-details p {
		margin: 8px 0;
		color: #555;
	}
	
	.doctor-notes {
		margin-top: 15px;
		padding: 12px;
		background: #f9f9f9;
		border-left: 4px solid #667eea;
		border-radius: 4px;
	}
	
	.doctor-notes p {
		margin-top: 5px;
		font-style: italic;
	}
	
	/* Doctors Grid */
	.doctors-section h2 {
		color: #333;
		margin-bottom: 20px;
	}
	
	.doctors-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		gap: 20px;
	}
	
	.doctor-card {
		background: white;
		border: 2px solid #e0e0e0;
		border-radius: 12px;
		padding: 25px;
		text-align: center;
		transition: all 0.3s ease;
	}
	
	.doctor-card:hover {
		border-color: #667eea;
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
		transform: translateY(-2px);
	}
	
	.doctor-icon {
		font-size: 48px;
		margin-bottom: 15px;
	}
	
	.doctor-card h3 {
		margin: 10px 0;
		color: #333;
		font-size: 18px;
	}
	
	.specialization {
		color: #667eea;
		font-weight: 600;
		margin: 10px 0;
	}
	
	.institution {
		color: #888;
		font-size: 14px;
		margin: 8px 0 15px;
	}
	
	.request-btn {
		width: 100%;
		padding: 12px;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		border-radius: 8px;
		font-size: 14px;
		font-weight: 600;
		cursor: pointer;
		transition: transform 0.2s;
		margin-top: 10px;
	}
	
	.request-btn:hover {
		transform: translateY(-2px);
	}
	
	/* Modal */
	.modal-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
	}
	
	.modal-content {
		background: white;
		border-radius: 12px;
		max-width: 500px;
		width: 90%;
		max-height: 90vh;
		overflow-y: auto;
	}
	
	.modal-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 20px;
		border-bottom: 2px solid #f0f0f0;
	}
	
	.modal-header h2 {
		margin: 0;
		color: #667eea;
		font-size: 20px;
	}
	
	.close-btn {
		background: none;
		border: none;
		font-size: 32px;
		color: #999;
		cursor: pointer;
		line-height: 1;
	}
	
	.close-btn:hover {
		color: #333;
	}
	
	.modal-body {
		padding: 20px;
	}
	
	.modal-info {
		color: #666;
		margin-bottom: 20px;
		line-height: 1.6;
	}
	
	.form-group {
		margin-bottom: 20px;
	}
	
	.form-group label {
		display: block;
		margin-bottom: 8px;
		font-weight: 600;
		color: #555;
	}
	
	.form-group input,
	.form-group textarea {
		width: 100%;
		padding: 12px;
		border: 2px solid #e0e0e0;
		border-radius: 8px;
		font-size: 14px;
		font-family: inherit;
	}
	
	.form-group input:focus,
	.form-group textarea:focus {
		outline: none;
		border-color: #667eea;
	}
	
	.form-group small {
		display: block;
		margin-top: 5px;
		color: #888;
		font-size: 12px;
	}
	
	.required {
		color: #dc3545;
		font-weight: bold;
	}
	
	.modal-footer {
		display: flex;
		gap: 10px;
		padding: 20px;
		border-top: 2px solid #f0f0f0;
	}
	
	.btn-cancel,
	.btn-submit {
		flex: 1;
		padding: 12px;
		border: none;
		border-radius: 8px;
		font-size: 14px;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.btn-cancel {
		background: #e0e0e0;
		color: #666;
	}
	
	.btn-cancel:hover {
		background: #d0d0d0;
	}
	
	.btn-submit {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
	}
	
	.btn-submit:hover:not(:disabled) {
		transform: translateY(-2px);
	}
	
	.btn-submit:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	
	.no-doctors {
		text-align: center;
		padding: 50px;
		color: #999;
	}
</style>

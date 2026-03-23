<script>
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	import { locale, localeText, translateText } from '$lib/i18n';
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

	function t(text) {
		return translateText(text ?? '', $locale);
	}

	function lt(en, bn) {
		return localeText({ en, bn }, $locale);
	}
	
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
			error = lt('Failed to load doctors', 'চিকিৎসকদের তথ্য লোড করা যায়নি');
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
			alert(lt('Please enter your full name', 'অনুগ্রহ করে আপনার পূর্ণ নাম লিখুন'));
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
					reason: reason || lt('Seeking professional oversight', 'পেশাদার তত্ত্বাবধান চাই'),
					message: message || null,
					diagnosis: diagnosis || null
				}
			});
			
			alert(lt('Request sent successfully! The doctor will review your request.', 'অনুরোধ সফলভাবে পাঠানো হয়েছে! চিকিৎসক আপনার অনুরোধ পর্যালোচনা করবেন।'));
			closeRequestModal();
			await loadData(); // Reload to show new request
		} catch (err) {
			const errorMsg = err.response?.data?.detail || lt('Failed to send request', 'অনুরোধ পাঠানো যায়নি');
			alert(t(errorMsg));
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
		return new Date(dateStr).toLocaleDateString($locale === 'bn' ? 'bn-BD' : 'en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}

	function statusLabel(status) {
		switch (status) {
			case 'pending':
				return lt('Pending', 'অপেক্ষমাণ');
			case 'approved':
				return lt('Approved', 'অনুমোদিত');
			case 'rejected':
				return lt('Rejected', 'প্রত্যাখ্যাত');
			default:
				return t(status || '');
		}
	}
</script>

<div class="page-container" data-localize-skip>
	<h1>🏥 {lt('Find a Healthcare Provider', 'একজন স্বাস্থ্যসেবা প্রদানকারী খুঁজুন')}</h1>
	<p class="subtitle">{lt('Browse verified doctors and request assignment for professional monitoring', 'যাচাইকৃত চিকিৎসকদের দেখুন এবং পেশাদার পর্যবেক্ষণের জন্য যুক্ত হওয়ার অনুরোধ করুন')}</p>
	
	{#if loading}
		<div class="loading">{lt('Loading doctors...', 'চিকিৎসকদের তথ্য লোড হচ্ছে...')}</div>
	{:else if error}
		<div class="error">{t(error)}</div>
	{:else}
		<!-- My Requests Section -->
		{#if myRequests.length > 0}
			<div class="my-requests-section">
				<h2>📋 {lt('My Requests', 'আমার অনুরোধসমূহ')}</h2>
				<div class="requests-list">
					{#each myRequests as request}
						<div class="request-card">
							<div class="request-header">
								<h3>{request.doctor_name}</h3>
								<span class="status-badge {getStatusBadgeClass(request.status)}">
									{statusLabel(request.status)}
								</span>
							</div>
							<div class="request-details">
								<p><strong>{lt('Specialization:', 'বিশেষায়ন:')}</strong> {request.doctor_specialization}</p>
								{#if request.reason}
									<p><strong>{lt('Reason:', 'কারণ:')}</strong> {request.reason}</p>
								{/if}
								<p><strong>{lt('Requested:', 'অনুরোধের তারিখ:')}</strong> {formatDate(request.created_at)}</p>
								{#if request.responded_at}
									<p><strong>{lt('Responded:', 'জবাবের তারিখ:')}</strong> {formatDate(request.responded_at)}</p>
								{/if}
								{#if request.doctor_notes}
									<div class="doctor-notes">
										<strong>{lt("Doctor's Response:", 'চিকিৎসকের জবাব:')}</strong>
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
			<h2>👨‍⚕️ {lt('Available Doctors', 'উপলভ্য চিকিৎসক')}</h2>
			{#if doctors.length === 0}
				<div class="no-doctors">
					<p>{lt('No doctors available at the moment. Please check back later.', 'এই মুহূর্তে কোনো চিকিৎসক উপলভ্য নেই। পরে আবার দেখুন।')}</p>
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
								{lt('Request Assignment', 'যুক্ত হওয়ার অনুরোধ পাঠান')}
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
	<div class="modal-overlay" on:click|self={closeRequestModal}>
		<div class="modal-content">
			<div class="modal-header">
				<h2>{lt('Request Assignment to', 'নিম্নোক্ত চিকিৎসকের কাছে যুক্ত হওয়ার অনুরোধ')} {selectedDoctor.full_name}</h2>
				<button class="close-btn" on:click={closeRequestModal}>×</button>
			</div>
			
			<div class="modal-body">
				<p class="modal-info">
					{lt('Send a request to be assigned to this doctor for professional monitoring of your cognitive training.', 'আপনার কগনিটিভ ট্রেনিংয়ের পেশাদার পর্যবেক্ষণের জন্য এই চিকিৎসকের কাছে যুক্ত হওয়ার অনুরোধ পাঠান।')}
				</p>
				
				<div class="form-group">
					<label for="reason">{lt('Reason for Request *', 'অনুরোধের কারণ *')}</label>
					<input 
						type="text" 
						id="reason" 
						bind:value={reason}
						placeholder={lt('e.g., Need professional oversight, diagnosed with MS', 'যেমন: পেশাদার তত্ত্বাবধান প্রয়োজন, এমএস নির্ণীত')}
					/>
				</div>
				
				<div class="form-group">
					<label for="diagnosis">{lt('Diagnosis (Optional)', 'রোগ নির্ণয় (ঐচ্ছিক)')}</label>
					<input 
						type="text" 
						id="diagnosis" 
						bind:value={diagnosis}
						placeholder={lt('e.g., Multiple Sclerosis, RRMS', 'যেমন: মাল্টিপল স্ক্লেরোসিস, RRMS')}
					/>
				</div>
				
				<div class="form-group">
					<label for="message">{lt('Additional Message (Optional)', 'অতিরিক্ত বার্তা (ঐচ্ছিক)')}</label>
					<textarea 
						id="message" 
						bind:value={message}
						placeholder={lt('Any additional information for the doctor...', 'চিকিৎসকের জন্য অতিরিক্ত কোনো তথ্য থাকলে লিখুন...')}
						rows="4"
					></textarea>
				</div>
			</div>
			
			<div class="modal-footer">
				<button class="btn-cancel" on:click={closeRequestModal}>{lt('Cancel', 'বাতিল করুন')}</button>
				<button class="btn-submit" on:click={submitRequest} disabled={!fullName.trim() || !reason.trim()}>
					{lt('Send Request', 'অনুরোধ পাঠান')}
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

<script>
	import api from '$lib/api.js';
	import { onMount } from 'svelte';
	
	export let userId;
	
	let loading = true;
	let assigned = false;
	let doctor = null;
	let error = '';
	
	onMount(async () => {
		try {
			const response = await api.get(`/api/doctor/patient/${userId}/assigned-doctor`);
			assigned = response.data.assigned;
			doctor = response.data.doctor;
		} catch (err) {
			console.error('Error loading assigned doctor:', err);
			error = 'Failed to load doctor information';
		} finally {
			loading = false;
		}
	});
	
	function formatDate(dateStr) {
		if (!dateStr) return '';
		return new Date(dateStr).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		});
	}
</script>

<div class="doctor-widget">
	{#if loading}
		<div class="loading-state">
			<div class="spinner"></div>
			<p>Loading doctor information...</p>
		</div>
	{:else if error}
		<div class="error-state">
			<p>⚠️ {error}</p>
		</div>
	{:else if assigned && doctor}
		<div class="doctor-assigned">
			<div class="widget-header">
				<h3>👨‍⚕️ Your Healthcare Provider</h3>
			</div>
			<div class="doctor-info">
				<div class="info-row">
					<span class="label">Doctor:</span>
					<span class="value">{doctor.full_name}</span>
				</div>
				<div class="info-row">
					<span class="label">Specialization:</span>
					<span class="value">{doctor.specialization}</span>
				</div>
				{#if doctor.institution}
					<div class="info-row">
						<span class="label">Institution:</span>
						<span class="value">{doctor.institution}</span>
					</div>
				{/if}
				<div class="info-row">
					<span class="label">Email:</span>
					<span class="value">{doctor.email}</span>
				</div>
				{#if doctor.assigned_at}
					<div class="info-row">
						<span class="label">Under care since:</span>
						<span class="value">{formatDate(doctor.assigned_at)}</span>
					</div>
				{/if}
				{#if doctor.diagnosis}
					<div class="info-row">
						<span class="label">Diagnosis:</span>
						<span class="value diagnosis">{doctor.diagnosis}</span>
					</div>
				{/if}
				{#if doctor.treatment_goal}
					<div class="info-row goals">
						<span class="label">Treatment Goals:</span>
						<span class="value">{doctor.treatment_goal}</span>
					</div>
				{/if}
			</div>
			<div class="widget-footer">
				<p class="info-text">
					✓ Your progress is being monitored by a healthcare professional
				</p>
			</div>
		</div>
	{:else}
		<div class="no-doctor">
			<div class="widget-header">
				<h3>👨‍⚕️ Healthcare Provider</h3>
			</div>
			<div class="no-doctor-content">
				<p class="main-message">No doctor currently assigned</p>
				<p class="sub-message">
					You can continue your training independently, or request to be assigned to a healthcare provider for professional monitoring.
				</p>
				<a href="/find-doctor">
					<button class="request-btn">
						Browse Available Doctors
					</button>
				</a>
			</div>
		</div>
	{/if}
</div>

<style>
	.doctor-widget {
		background: white;
		border-radius: 12px;
		padding: 20px;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
		margin-bottom: 30px;
	}
	
	.loading-state {
		text-align: center;
		padding: 30px;
		color: #666;
	}
	
	.spinner {
		width: 40px;
		height: 40px;
		margin: 0 auto 15px;
		border: 4px solid #f3f3f3;
		border-top: 4px solid #667eea;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}
	
	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}
	
	.error-state {
		padding: 20px;
		background: #fee;
		border-radius: 8px;
		color: #c33;
		text-align: center;
	}
	
	.widget-header {
		margin-bottom: 20px;
		padding-bottom: 15px;
		border-bottom: 2px solid #f0f0f0;
	}
	
	.widget-header h3 {
		margin: 0;
		color: #667eea;
		font-size: 18px;
		font-weight: 600;
	}
	
	.doctor-info {
		display: flex;
		flex-direction: column;
		gap: 12px;
	}
	
	.info-row {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		padding: 8px 0;
		border-bottom: 1px solid #f5f5f5;
	}
	
	.info-row.goals {
		flex-direction: column;
		gap: 8px;
	}
	
	.info-row .label {
		font-weight: 600;
		color: #555;
		min-width: 140px;
	}
	
	.info-row .value {
		color: #333;
		text-align: right;
		flex: 1;
	}
	
	.info-row.goals .value {
		text-align: left;
		padding: 10px;
		background: #f9f9f9;
		border-radius: 6px;
		font-style: italic;
	}
	
	.value.diagnosis {
		font-weight: 500;
		color: #667eea;
	}
	
	.widget-footer {
		margin-top: 20px;
		padding-top: 15px;
		border-top: 2px solid #f0f0f0;
	}
	
	.info-text {
		color: #28a745;
		font-size: 14px;
		margin: 0;
		text-align: center;
		font-weight: 500;
	}
	
	.no-doctor-content {
		text-align: center;
		padding: 20px 0;
	}
	
	.main-message {
		font-size: 16px;
		font-weight: 600;
		color: #666;
		margin-bottom: 10px;
	}
	
	.sub-message {
		color: #888;
		font-size: 14px;
		line-height: 1.6;
		margin-bottom: 20px;
	}
	
	.request-btn {
		padding: 12px 24px;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		border-radius: 8px;
		font-size: 14px;
		font-weight: 600;
		cursor: pointer;
		transition: transform 0.2s;
		margin-bottom: 10px;
	}
	
	.request-btn:hover:not(:disabled) {
		transform: translateY(-2px);
	}
	
	.request-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
</style>

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
		background: rgba(255, 255, 255, 0.62);
		backdrop-filter: blur(10px);
		border-radius: 18px;
		padding: 1rem;
		box-shadow: 0 10px 26px rgba(15, 23, 42, 0.04);
		border: 1px solid rgba(255, 255, 255, 0.7);
		margin: 0;
	}
	
	.loading-state {
		text-align: center;
		padding: 1.5rem;
		color: #6b7280;
	}
	
	.spinner {
		width: 40px;
		height: 40px;
		margin: 0 auto 15px;
		border: 4px solid #eef2f7;
		border-top: 4px solid #4f46e5;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}
	
	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}
	
	.error-state {
		padding: 1rem;
		background: rgba(254, 242, 242, 0.85);
		border-radius: 12px;
		color: #b91c1c;
		text-align: center;
	}
	
	.widget-header {
		margin-bottom: 1rem;
		padding-bottom: 0.85rem;
		border-bottom: 1px solid rgba(148, 163, 184, 0.18);
	}
	
	.widget-header h3 {
		margin: 0;
		color: #111827;
		font-size: 18px;
		font-weight: 700;
	}
	
	.doctor-info {
		display: flex;
		flex-direction: column;
		gap: 0.65rem;
	}
	
	.info-row {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		padding: 0.5rem 0;
		border-bottom: 1px solid rgba(148, 163, 184, 0.12);
	}
	
	.info-row.goals {
		flex-direction: column;
		gap: 8px;
	}
	
	.info-row .label {
		font-weight: 700;
		color: #4b5563;
		min-width: 140px;
	}
	
	.info-row .value {
		color: #111827;
		text-align: right;
		flex: 1;
	}
	
	.info-row.goals .value {
		text-align: left;
		padding: 0.8rem;
		background: rgba(248, 250, 252, 0.82);
		border-radius: 10px;
		font-style: italic;
	}
	
	.value.diagnosis {
		font-weight: 600;
		color: #4f46e5;
	}
	
	.widget-footer {
		margin-top: 1rem;
		padding-top: 0.85rem;
		border-top: 1px solid rgba(148, 163, 184, 0.18);
	}
	
	.info-text {
		color: #15803d;
		font-size: 14px;
		margin: 0;
		text-align: center;
		font-weight: 600;
	}
	
	.no-doctor-content {
		text-align: center;
		padding: 0.75rem 0 0;
	}
	
	.main-message {
		font-size: 16px;
		font-weight: 700;
		color: #374151;
		margin-bottom: 10px;
	}
	
	.sub-message {
		color: #6b7280;
		font-size: 14px;
		line-height: 1.6;
		margin-bottom: 20px;
	}
	
	.request-btn {
		padding: 0.8rem 1.2rem;
		background: linear-gradient(135deg, #4f46e5, #6366f1);
		color: white;
		border: none;
		border-radius: 999px;
		font-size: 14px;
		font-weight: 700;
		cursor: pointer;
		transition: transform 0.2s, box-shadow 0.2s;
		margin-bottom: 10px;
		box-shadow: 0 10px 24px rgba(79, 70, 229, 0.18);
	}
	
	.request-btn:hover:not(:disabled) {
		transform: translateY(-1px);
		box-shadow: 0 14px 28px rgba(79, 70, 229, 0.22);
	}
	
	.request-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	@media (max-width: 640px) {
		.info-row {
			flex-direction: column;
			gap: 0.35rem;
		}

		.info-row .value {
			text-align: left;
		}
	}
</style>

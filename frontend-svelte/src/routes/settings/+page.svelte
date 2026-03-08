<script>
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	import { user } from '$lib/stores.js';
	import { onMount } from 'svelte';

	let userData;
	let profile = null;
	let loading = true;
	let saving = false;
	let message = '';
	let error = '';

	const unsubscribe = user.subscribe(value => {
		userData = value;
	});

	onMount(() => {
		if (!userData || userData.role !== 'patient') {
			goto('/login');
			return;
		}

		loadProfile();

		return () => {
			unsubscribe();
		};
	});

	async function loadProfile() {
		try {
			loading = true;
			const response = await api.get(`/api/auth/patient/${userData.id}/profile`);
			profile = response.data;
		} catch (err) {
			error = 'Failed to load profile';
			console.error(err);
		} finally {
			loading = false;
		}
	}

	async function toggleConsent() {
		try {
			saving = true;
			error = '';
			message = '';

			const response = await api.patch(
				`/api/auth/patient/${userData.id}/consent`,
				null,
				{ params: { consent: !profile.consent_to_share } }
			);

			profile.consent_to_share = response.data.consent_to_share;
			message = 'Consent settings updated successfully';

			setTimeout(() => {
				message = '';
			}, 3000);
		} catch (err) {
			error = err.response?.data?.detail || 'Failed to update consent';
			console.error(err);
		} finally {
			saving = false;
		}
	}
</script>

<div class="settings-container">
	<div class="header">
		<button on:click={() => goto('/dashboard')} class="back-btn">
			← Back to Dashboard
		</button>
		<h1>Settings</h1>
	</div>

	{#if loading}
		<div class="loading">Loading settings...</div>
	{:else if profile}
		<div class="settings-content">
			<!-- Profile Information -->
			<section class="settings-section">
				<h2>Profile Information</h2>
				<div class="info-grid">
					<div class="info-item">
						<label>Email</label>
						<p>{profile.email}</p>
					</div>
					<div class="info-item">
						<label>Full Name</label>
						<p>{profile.full_name || 'Not provided'}</p>
					</div>
					<div class="info-item">
						<label>Date of Birth</label>
						<p>{profile.date_of_birth || 'Not provided'}</p>
					</div>
					<div class="info-item">
						<label>Diagnosis</label>
						<p>{profile.diagnosis || 'Not provided'}</p>
					</div>
				</div>
			</section>

			<!-- Privacy Settings -->
			<section class="settings-section">
				<h2>Privacy & Data Sharing</h2>
				<div class="consent-section">
					<div class="consent-info">
						<h3>Share Data with Healthcare Providers</h3>
						<p>
							Allow your assigned doctor to view your training progress, test results, and
							performance metrics. This helps your healthcare provider monitor your cognitive
							health and adjust treatment plans accordingly.
						</p>
						{#if !profile.consent_to_share}
							<p class="warning">
								⚠️ Without consent, doctors cannot view your data or provide personalized
								support.
							</p>
						{/if}
					</div>

					<div class="consent-toggle">
						<label class="toggle-switch">
							<input
								type="checkbox"
								checked={profile.consent_to_share}
								on:change={toggleConsent}
								disabled={saving}
							/>
							<span class="slider"></span>
						</label>
						<span class="consent-status">
							{profile.consent_to_share ? 'Enabled' : 'Disabled'}
						</span>
					</div>
				</div>
			</section>

			{#if message}
				<div class="success-message">{message}</div>
			{/if}

			{#if error}
				<div class="error-message">{error}</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.settings-container {
		max-width: 900px;
		margin: 0 auto;
		padding: 2rem;
	}

	.header {
		margin-bottom: 2rem;
	}

	.header h1 {
		color: #333;
		margin: 1rem 0;
	}

	.back-btn {
		background: none;
		border: none;
		color: #667eea;
		cursor: pointer;
		font-size: 1rem;
		padding: 0.5rem 0;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.back-btn:hover {
		text-decoration: underline;
	}

	.loading {
		text-align: center;
		padding: 3rem;
		color: #666;
	}

	.settings-content {
		display: flex;
		flex-direction: column;
		gap: 2rem;
	}

	.settings-section {
		background: white;
		border-radius: 8px;
		padding: 2rem;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
	}

	.settings-section h2 {
		margin: 0 0 1.5rem 0;
		color: #333;
		font-size: 1.5rem;
	}

	.info-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: 1.5rem;
	}

	.info-item label {
		display: block;
		font-weight: 600;
		color: #666;
		margin-bottom: 0.5rem;
		font-size: 0.9rem;
	}

	.info-item p {
		color: #333;
		margin: 0;
		font-size: 1rem;
	}

	.consent-section {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 2rem;
	}

	.consent-info {
		flex: 1;
	}

	.consent-info h3 {
		margin: 0 0 1rem 0;
		color: #333;
		font-size: 1.1rem;
	}

	.consent-info p {
		margin: 0.5rem 0;
		color: #666;
		line-height: 1.6;
	}

	.consent-info .warning {
		background: #fff3cd;
		border-left: 4px solid #ffc107;
		padding: 0.75rem;
		margin-top: 1rem;
		border-radius: 4px;
		color: #856404;
	}

	.consent-toggle {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}

	.toggle-switch {
		position: relative;
		display: inline-block;
		width: 60px;
		height: 34px;
	}

	.toggle-switch input {
		opacity: 0;
		width: 0;
		height: 0;
	}

	.slider {
		position: absolute;
		cursor: pointer;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: #ccc;
		transition: 0.4s;
		border-radius: 34px;
	}

	.slider:before {
		position: absolute;
		content: '';
		height: 26px;
		width: 26px;
		left: 4px;
		bottom: 4px;
		background-color: white;
		transition: 0.4s;
		border-radius: 50%;
	}

	input:checked + .slider {
		background-color: #667eea;
	}

	input:checked + .slider:before {
		transform: translateX(26px);
	}

	input:disabled + .slider {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.consent-status {
		font-weight: 600;
		color: #333;
		font-size: 0.9rem;
	}

	.success-message {
		background: #d4edda;
		color: #155724;
		padding: 1rem;
		border-radius: 4px;
		border-left: 4px solid #28a745;
		margin-top: 1rem;
	}

	.error-message {
		background: #f8d7da;
		color: #721c24;
		padding: 1rem;
		border-radius: 4px;
		border-left: 4px solid #dc3545;
		margin-top: 1rem;
	}

	@media (max-width: 768px) {
		.settings-container {
			padding: 1rem;
		}

		.consent-section {
			flex-direction: column;
			align-items: flex-start;
		}

		.info-grid {
			grid-template-columns: 1fr;
		}
	}
</style>

<script>
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	
	let email = '';
	let password = '';
	let confirmPassword = '';
	let registerType = 'patient'; // 'patient' or 'doctor'
	let fullName = '';
	let licenseNumber = '';
	let specialization = '';
	let institution = '';
	let error = '';
	let success = '';
	let loading = false;
	
	async function handleRegister() {
		error = '';
		success = '';
		
		// Validate common fields
		if (!email || !password || !confirmPassword) {
			error = 'Please fill in all fields';
			return;
		}
		
		// Validate doctor-specific fields
		if (registerType === 'doctor') {
			if (!fullName || !licenseNumber || !specialization) {
				error = 'Please fill in all required doctor information';
				return;
			}
		}
		
		if (password !== confirmPassword) {
			error = 'Passwords do not match';
			return;
		}
		
		if (password.length < 6) {
			error = 'Password must be at least 6 characters';
			return;
		}
		
		loading = true;
		
		try {
			if (registerType === 'doctor') {
				// Register as doctor
				await api.post('/api/auth/doctor/register', {
					email,
					password,
					full_name: fullName,
					license_number: licenseNumber,
					specialization,
					institution: institution || null
				});
				
				success = 'Doctor account created! Please wait for admin verification before logging in.';
				
				// Wait a bit to show success message, then redirect
				setTimeout(() => {
					goto('/login');
				}, 3000);
			} else {
				// Register as patient
				await api.post('/api/auth/register', { email, password });
				
				// Redirect to login after successful registration
				goto('/login');
			}
		} catch (err) {
			error = err.response?.data?.detail || 'Registration failed. Please try again.';
		} finally {
			loading = false;
		}
	}
</script>

<div class="auth-container">
	<div class="auth-card">
		<h1>Create Account</h1>
		<p>Start your cognitive training journey</p>
		
		<!-- Registration Type Selector -->
		<div class="register-type-selector">
			<button 
				type="button"
				class="type-btn {registerType === 'patient' ? 'active' : ''}"
				on:click={() => registerType = 'patient'}
				disabled={loading}
			>
				👤 Patient
			</button>
			<button 
				type="button"
				class="type-btn {registerType === 'doctor' ? 'active' : ''}"
				on:click={() => registerType = 'doctor'}
				disabled={loading}
			>
				👨‍⚕️ Doctor
			</button>
		</div>
		
		{#if error}
			<div class="error">{error}</div>
		{/if}
		
		{#if success}
			<div class="success">{success}</div>
		{/if}
		
		<form on:submit|preventDefault={handleRegister}>
			{#if registerType === 'doctor'}
				<div class="form-group">
					<label for="fullName">Full Name *</label>
					<input 
						type="text" 
						id="fullName" 
						bind:value={fullName}
						placeholder="Dr. Jane Smith"
						disabled={loading}
						required
					/>
				</div>
			{/if}
			
			<div class="form-group">
				<label for="email">Email</label>
				<input 
					type="email" 
					id="email" 
					bind:value={email}
					placeholder="your@email.com"
					disabled={loading}
					required
				/>
			</div>
			
			{#if registerType === 'doctor'}
				<div class="form-group">
					<label for="licenseNumber">Medical License Number *</label>
					<input 
						type="text" 
						id="licenseNumber" 
						bind:value={licenseNumber}
						placeholder="License number"
						disabled={loading}
						required
					/>
				</div>
				
				<div class="form-group">
					<label for="specialization">Specialization *</label>
					<input 
						type="text" 
						id="specialization" 
						bind:value={specialization}
						placeholder="e.g., Neurology, Psychiatry"
						disabled={loading}
						required
					/>
				</div>
				
				<div class="form-group">
					<label for="institution">Institution (Optional)</label>
					<input 
						type="text" 
						id="institution" 
						bind:value={institution}
						placeholder="Hospital or clinic name"
						disabled={loading}
					/>
				</div>
			{/if}
			
			<div class="form-group">
				<label for="password">Password</label>
				<input 
					type="password" 
					id="password" 
					bind:value={password}
					placeholder="••••••••"
					disabled={loading}
					required
				/>
			</div>
			
			<div class="form-group">
				<label for="confirmPassword">Confirm Password</label>
				<input 
					type="password" 
					id="confirmPassword" 
					bind:value={confirmPassword}
					placeholder="••••••••"
					disabled={loading}
					required
				/>
			</div>
			
			{#if registerType === 'doctor'}
				<div class="info-notice">
					⚠️ Doctor accounts require admin verification before login access is granted.
				</div>
			{/if}
			
			<button type="submit" class="btn" disabled={loading || !!success}>
				{#if loading}
					Creating account...
				{:else if success}
					Account Created!
				{:else}
					Register as {registerType === 'doctor' ? 'Doctor' : 'Patient'}
				{/if}
			</button>
		</form>
		
		<div class="auth-link">
			Already have an account? <a href="/login">Login here</a>
		</div>
	</div>
</div>

<style>
	.register-type-selector {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 1.5rem;
		background: #f5f5f5;
		border-radius: 8px;
		padding: 4px;
	}
	
	.type-btn {
		flex: 1;
		padding: 0.75rem;
		border: none;
		background: transparent;
		border-radius: 6px;
		cursor: pointer;
		font-weight: 500;
		font-size: 0.95rem;
		transition: all 0.3s ease;
		color: #666;
	}
	
	.type-btn.active {
		background: white;
		color: #667eea;
		box-shadow: 0 2px 8px rgba(0,0,0,0.1);
	}
	
	.type-btn:hover:not(:disabled):not(.active) {
		background: rgba(255,255,255,0.5);
	}
	
	.type-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	
	.success {
		background-color: #d4edda;
		border: 1px solid #c3e6cb;
		color: #155724;
		padding: 12px;
		border-radius: 8px;
		margin-bottom: 20px;
		font-size: 14px;
	}
	
	.info-notice {
		background-color: #fff3cd;
		border: 1px solid #ffeaa7;
		color: #856404;
		padding: 10px;
		border-radius: 6px;
		margin-bottom: 15px;
		font-size: 13px;
		text-align: center;
	}
</style>

<script>
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	import { clearUser, setUser } from '$lib/stores';
	import { onMount } from 'svelte';
	
	let email = '';
	let password = '';
	let loginType = 'patient'; // 'patient', 'doctor', or 'admin'
	let error = '';
	let loading = false;
	
	// Clear any existing session when visiting login page
	onMount(() => {
		clearUser();
	});
	
	async function handleLogin() {
		error = '';
		
		if (!email || !password) {
			error = 'Please fill in all fields';
			return;
		}
		
		loading = true;
		
		try {
const endpoint = loginType === 'doctor'
			? '/api/auth/doctor/login'
			: loginType === 'admin'
			? '/api/admin/login'
				: '/api/auth/login';
			
			console.log('Attempting login to:', endpoint);
			console.log('Login type:', loginType);
			
			const response = await api.post(endpoint, { email, password });
			
			console.log('Login response:', response);
			
			// Store user data with role
			setUser({
				id: response.data.id,
				email: response.data.email,
				role: response.data.role || loginType,
				fullName: response.data.full_name || null
			});
			
			// Redirect based on role
			if (loginType === 'doctor') {
				goto('/doctor/dashboard');
			} else if (loginType === 'admin') {
				goto('/admin/dashboard');
			} else {
				goto('/dashboard');
			}
		} catch (err) {
			console.error('Login error:', err);
			console.error('Error response:', err.response);
			error = err.response?.data?.detail || err.message || 'Login failed. Please try again.';
		} finally {
			loading = false;
		}
	}
</script>

<div class="auth-container">
	<div class="auth-card">
		<h1>Welcome Back</h1>
		<p>Login to continue your cognitive training</p>
		
		<!-- Login Type Selector -->
		<div class="login-type-selector">
			<button 
				type="button"
				class="type-btn {loginType === 'patient' ? 'active' : ''}"
				on:click={() => loginType = 'patient'}
				disabled={loading}
			>
				👤 Patient
			</button>
			<button 
				type="button"
				class="type-btn {loginType === 'doctor' ? 'active' : ''}"
				on:click={() => loginType = 'doctor'}
				disabled={loading}
			>
				👨‍⚕️ Doctor
			</button>
		<button 
			type="button"
			class="type-btn {loginType === 'admin' ? 'active' : ''}"
			on:click={() => loginType = 'admin'}
			disabled={loading}
		>
			🏥 Admin
		</button>
		</div>
		
		{#if error}
			<div class="error">{error}</div>
		{/if}
		
		<form on:submit|preventDefault={handleLogin}>
			<div class="form-group">
				<label for="email">Email</label>
				<input 
					type="email" 
					id="email" 
					bind:value={email}
					placeholder="your@email.com"
					disabled={loading}
				/>
			</div>
			
			<div class="form-group">
				<label for="password">Password</label>
				<input 
					type="password" 
					id="password" 
					bind:value={password}
					placeholder="••••••••"
					disabled={loading}
				/>
			</div>
			
			<button type="submit" class="btn" disabled={loading}>
				{loading ? 'Logging in...' : `Login as ${loginType === 'doctor' ? 'Doctor' : loginType === 'admin' ? 'Admin' : 'Patient'}`}
			</button>
		</form>
		
		<div class="auth-link">
			Don't have an account? <a href="/register">Register here</a>
		</div>
	</div>
</div>

<style>
	.login-type-selector {
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
</style>

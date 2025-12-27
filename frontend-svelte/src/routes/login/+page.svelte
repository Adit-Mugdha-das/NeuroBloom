<script>
	import { auth } from '$lib/api';
	import { setUser, clearUser } from '$lib/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	
	let email = '';
	let password = '';
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
			const response = await auth.login(email, password);
			
			// Store user data
			setUser({
				id: response.id,
				email: response.email
			});
			
			// Redirect to dashboard
			goto('/dashboard');
		} catch (err) {
			error = err.response?.data?.detail || 'Login failed. Please try again.';
		} finally {
			loading = false;
		}
	}
</script>

<div class="auth-container">
	<div class="auth-card">
		<h1>Welcome Back</h1>
		<p>Login to continue your cognitive training</p>
		
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
				{loading ? 'Logging in...' : 'Login'}
			</button>
		</form>
		
		<div class="auth-link">
			Don't have an account? <a href="/register">Register here</a>
		</div>
	</div>
</div>

<script>
	import { goto } from '$app/navigation';
	import { auth } from '$lib/api';
	
	let email = '';
	let password = '';
	let confirmPassword = '';
	let error = '';
	let loading = false;
	
	async function handleRegister() {
		error = '';
		
		if (!email || !password || !confirmPassword) {
			error = 'Please fill in all fields';
			return;
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
			await auth.register(email, password);
			
			// Redirect to login after successful registration
			goto('/login');
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
		
		{#if error}
			<div class="error">{error}</div>
		{/if}
		
		<form on:submit|preventDefault={handleRegister}>
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
			
			<div class="form-group">
				<label for="confirmPassword">Confirm Password</label>
				<input 
					type="password" 
					id="confirmPassword" 
					bind:value={confirmPassword}
					placeholder="••••••••"
					disabled={loading}
				/>
			</div>
			
			<button type="submit" class="btn" disabled={loading}>
				{loading ? 'Creating account...' : 'Register'}
			</button>
		</form>
		
		<div class="auth-link">
			Already have an account? <a href="/login">Login here</a>
		</div>
	</div>
</div>

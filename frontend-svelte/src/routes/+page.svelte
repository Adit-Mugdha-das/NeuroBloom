<script>
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores';
	
	let currentUser = null;
	
	user.subscribe(value => {
		currentUser = value;
	});
	
	function continueToDashboard() {
		goto('/dashboard');
	}
</script>

<div class="auth-container">
	<div class="auth-card">
		<h1>🧠 NeuroBloom</h1>
		<p>Clinical-Grade Cognitive Assessment Platform</p>
		
		{#if currentUser}
			<div style="margin-top: 30px;">
				<p style="color: #667eea; font-weight: 600; margin-bottom: 20px;">
					Welcome back, {currentUser.email}!
				</p>
				<button class="btn" on:click={continueToDashboard}>
					Continue to Dashboard
				</button>
				<a href="/login">
					<button class="btn-secondary" style="width: 100%; margin-top: 10px;">
						Switch Account
					</button>
				</a>
			</div>
		{:else}
			<div style="margin-top: 30px;">
				<a href="/login">
					<button class="btn" style="margin-bottom: 15px;">Login</button>
				</a>
				<a href="/register">
					<button class="btn-secondary" style="width: 100%;">Create Account</button>
				</a>
			</div>
		{/if}
		
		<div style="margin-top: 40px; text-align: center; color: #666; font-size: 14px;">
			<p>Personalized cognitive training with adaptive AI</p>
			<p style="margin-top: 10px;">MS-specific features • Weekly progress tracking</p>
		</div>
	</div>
</div>

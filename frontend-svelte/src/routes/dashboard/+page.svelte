<script>
	import { user, clearUser } from '$lib/stores';
	import { tasks } from '$lib/api';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	
	let currentUser = null;
	let stats = null;
	let loading = true;
	
	user.subscribe(value => {
		currentUser = value;
		if (!value) {
			goto('/login');
		}
	});
	
	onMount(async () => {
		if (!currentUser) {
			goto('/login');
			return;
		}
		
		try {
			stats = await tasks.getUserStats(currentUser.id);
		} catch (error) {
			console.error('Error fetching stats:', error);
		} finally {
			loading = false;
		}
	});
	
	function handleLogout() {
		clearUser();
		goto('/login');
	}
</script>

<div class="dashboard">
	<header class="header">
		<h1>🧠 NeuroBloom</h1>
		<div class="header-right">
			{#if currentUser}
				<span class="user-email">{currentUser.email}</span>
			{/if}
			<button class="btn-logout" on:click={handleLogout}>Logout</button>
		</div>
	</header>
	
	<div class="container">
		<h2 style="margin: 30px 0 20px; color: #333;">Your Dashboard</h2>
		
		{#if loading}
			<p>Loading...</p>
		{:else}
			<div class="stats-grid">
				<div class="stat-card">
					<h3>Total Sessions</h3>
					<div class="value">{stats?.total_sessions || 0}</div>
				</div>
				<div class="stat-card">
					<h3>Average Score</h3>
					<div class="value">{stats?.average_score ? stats.average_score.toFixed(1) : 0}%</div>
				</div>
				<div class="stat-card">
					<h3>Best Score</h3>
					<div class="value">{stats?.best_score || 0}%</div>
				</div>
				<div class="stat-card">
					<h3>Tasks Completed</h3>
					<div class="value">{stats?.total_sessions || 0}</div>
				</div>
			</div>
			
			<h3 style="margin: 40px 0 20px; color: #333;">Cognitive Training Modules</h3>
			
			<div class="modules-grid">
				<a href="/baseline/tasks/working-memory" style="text-decoration: none;">
					<div class="module-card">
						<div class="icon">🧩</div>
						<h3>Working Memory</h3>
						<p>N-Back Test • Challenge your short-term memory</p>
					</div>
				</a>
				
				<a href="/baseline/tasks/attention" style="text-decoration: none;">
					<div class="module-card">
						<div class="icon">👁️</div>
						<h3>Attention</h3>
						<p>CPT Test • Sustained attention & vigilance</p>
					</div>
				</a>
				
				<a href="/baseline/tasks/flexibility" style="text-decoration: none;">
					<div class="module-card">
						<div class="icon">🔄</div>
						<h3>Cognitive Flexibility</h3>
						<p>Task Switching • Adapt to changing rules</p>
					</div>
				</a>
				
				<div class="module-card" style="opacity: 0.6; cursor: not-allowed;">
					<div class="icon">🎯</div>
					<h3>Planning</h3>
					<p>Coming Soon • Tower of Hanoi</p>
				</div>
				
				<div class="module-card" style="opacity: 0.6; cursor: not-allowed;">
					<div class="icon">⚡</div>
					<h3>Processing Speed</h3>
					<p>Coming Soon • Reaction time tests</p>
				</div>
				
				<div class="module-card" style="opacity: 0.6; cursor: not-allowed;">
					<div class="icon">🔍</div>
					<h3>Visual Scanning</h3>
					<p>Coming Soon • Visual search tasks</p>
				</div>
			</div>
		{/if}
	</div>
</div>

<script>
	import { goto } from '$app/navigation';
	import { tasks } from '$lib/api';
	import { clearUser, user } from '$lib/stores';
	import { onMount } from 'svelte';
	
	let currentUser = null;
	let stats = null;
	let baselineStatus = null;
	let loading = true;
	
	user.subscribe(value => {
		currentUser = value;
	});
	
	onMount(async () => {
		if (!currentUser) {
			goto('/login');
			return;
		}
		
		try {
			stats = await tasks.getUserStats(currentUser.id);
			baselineStatus = await tasks.getBaselineStatus(currentUser.id);
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
			
			{#if baselineStatus}
				<div class="baseline-progress">
					<div class="progress-header">
						<div class="progress-info">
							<div class="progress-bar">
								<div 
									class="progress-fill" 
									style="width: {(baselineStatus.completed_count / baselineStatus.total_tasks) * 100}%"
								></div>
							</div>
							<p class="progress-text">
								{baselineStatus.completed_count} of {baselineStatus.total_tasks} baseline tasks completed
							</p>
						</div>
						{#if baselineStatus.all_completed}
							<div class="action-buttons">
								<a href="/baseline/results" class="btn-baseline">
									View Baseline
								</a>
								<a href="/training" class="btn-training">
									Training Plan
								</a>
								<a href="/progress" class="btn-progress">
									Progress
								</a>
							</div>
						{/if}
					</div>
				</div>
			{/if}
			
			<div class="modules-grid">
				<a href="/baseline/tasks/working-memory" style="text-decoration: none;">
					<div class="module-card {baselineStatus?.tasks?.working_memory ? 'completed' : ''}">
						<div class="icon">🧩</div>
						<h3>Working Memory</h3>
						<p>N-Back Test • Challenge your short-term memory</p>
						{#if baselineStatus?.tasks?.working_memory}
							<div class="completion-badge">✓</div>
						{/if}
					</div>
				</a>
				
				<a href="/baseline/tasks/attention" style="text-decoration: none;">
					<div class="module-card {baselineStatus?.tasks?.attention ? 'completed' : ''}">
						<div class="icon">👁️</div>
						<h3>Attention</h3>
						<p>CPT Test • Sustained attention & vigilance</p>
						{#if baselineStatus?.tasks?.attention}
							<div class="completion-badge">✓</div>
						{/if}
					</div>
				</a>
				
				<a href="/baseline/tasks/flexibility" style="text-decoration: none;">
					<div class="module-card {baselineStatus?.tasks?.flexibility ? 'completed' : ''}">
						<div class="icon">🔄</div>
						<h3>Cognitive Flexibility</h3>
						<p>Task Switching • Adapt to changing rules</p>
						{#if baselineStatus?.tasks?.flexibility}
							<div class="completion-badge">✓</div>
						{/if}
					</div>
				</a>
				
				<a href="/baseline/tasks/planning" style="text-decoration: none;">
					<div class="module-card {baselineStatus?.tasks?.planning ? 'completed' : ''}">
						<div class="icon">🎯</div>
						<h3>Planning</h3>
						<p>Tower of Hanoi • Strategic problem solving</p>
						{#if baselineStatus?.tasks?.planning}
							<div class="completion-badge">✓</div>
						{/if}
					</div>
				</a>
				
				<a href="/baseline/tasks/processing-speed" style="text-decoration: none;">
					<div class="module-card {baselineStatus?.tasks?.processing_speed ? 'completed' : ''}">
						<div class="icon">⚡</div>
						<h3>Processing Speed</h3>
						<p>Reaction Time • Simple & choice responses</p>
						{#if baselineStatus?.tasks?.processing_speed}
							<div class="completion-badge">✓</div>
						{/if}
					</div>
				</a>
				
				<a href="/baseline/tasks/visual-scanning" style="text-decoration: none;">
					<div class="module-card {baselineStatus?.tasks?.visual_scanning ? 'completed' : ''}">
						<div class="icon">🔍</div>
						<h3>Visual Scanning</h3>
						<p>Visual Search • Find targets in grid</p>
						{#if baselineStatus?.tasks?.visual_scanning}
							<div class="completion-badge">✓</div>
						{/if}
					</div>
				</a>
			</div>
		{/if}
	</div>
</div>

<style>
	.dashboard {
		min-height: 100vh;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
	}
	
	.header {
		background: white;
		padding: 1rem 2rem;
		display: flex;
		justify-content: space-between;
		align-items: center;
		box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
	}
	
	.header h1 {
		margin: 0;
		color: #667eea;
	}
	
	.header-right {
		display: flex;
		align-items: center;
		gap: 1rem;
	}
	
	.user-email {
		color: #666;
		font-size: 0.9rem;
	}
	
	.btn-logout {
		background: #dc3545;
		color: white;
		border: none;
		padding: 0.5rem 1.5rem;
		border-radius: 8px;
		cursor: pointer;
		font-weight: 600;
		transition: background 0.3s;
	}
	
	.btn-logout:hover {
		background: #c82333;
	}
	
	.container {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem;
	}
	
	.stats-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1.5rem;
		margin-bottom: 2rem;
	}
	
	.stat-card {
		background: white;
		padding: 1.5rem;
		border-radius: 12px;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
	}
	
	.stat-card h3 {
		margin: 0 0 0.5rem 0;
		color: #666;
		font-size: 0.9rem;
		font-weight: 600;
	}
	
	.stat-card .value {
		font-size: 2rem;
		font-weight: bold;
		color: #667eea;
	}
	
	.baseline-progress {
		background: white;
		padding: 1.5rem;
		border-radius: 12px;
		margin-bottom: 1.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
	}
	
	.progress-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 2rem;
	}
	
	.progress-info {
		flex: 1;
	}
	
	.progress-bar {
		width: 100%;
		height: 12px;
		background: #e0e0e0;
		border-radius: 6px;
		overflow: hidden;
		margin-bottom: 0.5rem;
	}
	
	.progress-fill {
		height: 100%;
		background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
		transition: width 0.5s ease;
	}
	
	.progress-text {
		margin: 0;
		color: #666;
		font-size: 0.9rem;
	}
	
	.btn-baseline {
		background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
		color: white;
		border: none;
		padding: 1rem 2rem;
		border-radius: 12px;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		text-decoration: none;
		display: inline-block;
		transition: all 0.3s;
		white-space: nowrap;
		box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
	}
	
	.btn-baseline:hover {
		transform: translateY(-2px);
		box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
	}
	
	.action-buttons {
		display: flex;
		gap: 1rem;
		flex-wrap: wrap;
	}
	
	.btn-training, .btn-progress {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		padding: 1rem 2rem;
		border-radius: 12px;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		text-decoration: none;
		display: inline-block;
		transition: all 0.3s;
		white-space: nowrap;
		box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
	}
	
	.btn-training:hover, .btn-progress:hover {
		transform: translateY(-2px);
		box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
	}
	
	.modules-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
		gap: 1.5rem;
	}
	
	.module-card {
		position: relative;
		background: white;
		padding: 2rem;
		border-radius: 12px;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
		transition: all 0.3s;
		cursor: pointer;
	}
	
	.module-card:hover {
		transform: translateY(-5px);
		box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
	}
	
	.module-card.completed {
		background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
		border: 2px solid #667eea;
	}
	
	.module-card .icon {
		font-size: 3rem;
		margin-bottom: 1rem;
	}
	
	.module-card h3 {
		margin: 0.5rem 0;
		color: #333;
	}
	
	.module-card p {
		margin: 0.5rem 0 0 0;
		color: #666;
		font-size: 0.9rem;
	}
	
	.completion-badge {
		position: absolute;
		top: 1rem;
		right: 1rem;
		width: 40px;
		height: 40px;
		background: #28a745;
		color: white;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.5rem;
		font-weight: bold;
		box-shadow: 0 2px 8px rgba(40, 167, 69, 0.3);
	}
</style>


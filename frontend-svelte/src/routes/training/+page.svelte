<script>
	import { goto } from '$app/navigation';
	import { training } from '$lib/api';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';
	
	let currentUser = null;
	let loading = true;
	let trainingPlan = null;
	let nextTasks = null;
	let metrics = null;
	let error = null;
	
	user.subscribe(value => {
		currentUser = value;
	});
	
	onMount(async () => {
		if (!currentUser) {
			goto('/login');
			return;
		}
		
		await loadTrainingData();
	});
	
	async function loadTrainingData() {
		loading = true;
		error = null;
		
		try {
			// Load training plan
			trainingPlan = await training.getPlan(currentUser.id);
			
			// Load next recommended tasks
			nextTasks = await training.getNextTasks(currentUser.id);
			
			// Load performance metrics
			try {
				metrics = await training.getMetrics(currentUser.id);
			} catch (e) {
				metrics = null;
			}
		} catch (err) {
			console.error('Error loading training data:', err);
			error = 'No training plan found. Please generate one from your baseline results.';
		} finally {
			loading = false;
		}
	}
	
	function getDomainName(domain) {
		const names = {
			working_memory: 'Working Memory',
			attention: 'Attention',
			flexibility: 'Cognitive Flexibility',
			planning: 'Planning',
			processing_speed: 'Processing Speed',
			visual_scanning: 'Visual Scanning'
		};
		return names[domain] || domain;
	}
	
	function getTaskRoute(taskType, domain) {
		// Map task types to routes
		const routes = {
			n_back: '/baseline/tasks/working-memory',
			continuous_performance: '/baseline/tasks/attention',
			task_switching: '/baseline/tasks/flexibility',
			tower_of_hanoi: '/baseline/tasks/planning',
			reaction_time: '/baseline/tasks/processing-speed',
			target_search: '/baseline/tasks/visual-scanning'
		};
		return routes[taskType] || '/dashboard';
	}
	
	function getPriorityColor(priority) {
		if (priority === 'primary') return '#f44336';
		if (priority === 'secondary') return '#ff9800';
		return '#4caf50';
	}
	
	function getPriorityLabel(priority) {
		if (priority === 'primary') return 'High Priority';
		if (priority === 'secondary') return 'Medium Priority';
		return 'Maintenance';
	}
	
	function getDifficultyLabel(difficulty) {
		if (difficulty <= 3) return 'Easy';
		if (difficulty <= 6) return 'Medium';
		if (difficulty <= 8) return 'Hard';
		return 'Expert';
	}
	
	function backToDashboard() {
		goto('/dashboard');
	}
</script>

<div class="container">
	{#if loading}
		<div class="loading-card">
			<p>Loading training plan...</p>
		</div>
	{:else if error}
		<div class="error-card">
			<h3>Error</h3>
			<p>{error}</p>
			<button class="btn-primary" on:click={() => goto('/baseline/results')}>
				Go to Baseline Results
			</button>
		</div>
	{:else if trainingPlan}
		<div class="training-container">
			<!-- Header -->
			<div class="training-header">
				<div class="header-content">
					<div class="header-text">
						<h1>Personalized Training Plan</h1>
						<p class="subtitle">Adaptive cognitive training based on your baseline assessment</p>
					</div>
					<button class="btn-back" on:click={backToDashboard}>← Back to Dashboard</button>
				</div>
			</div>
			
			<!-- Stats Overview -->
			{#if metrics}
				<div class="stats-card">
					<h3>Training Progress</h3>
					<div class="stats-grid">
						<div class="stat">
							<div class="stat-value">{metrics.total_sessions}</div>
							<div class="stat-label">Total Sessions</div>
						</div>
						<div class="stat">
							<div class="stat-value">{trainingPlan.total_sessions}</div>
							<div class="stat-label">Sessions Completed</div>
						</div>
						<div class="stat">
							<div class="stat-value">
								{metrics.last_training_date ? new Date(metrics.last_training_date).toLocaleDateString() : 'Never'}
							</div>
							<div class="stat-label">Last Training</div>
						</div>
					</div>
				</div>
			{/if}
			
			<!-- Next Training Session -->
			<div class="session-card">
				<h3>Next Training Session #{nextTasks.session_number}</h3>
				<p class="session-subtitle">Complete these {nextTasks.total_tasks} tasks to improve your cognitive performance</p>
				
				<div class="tasks-grid">
					{#each nextTasks.tasks as task}
						<div class="task-card" style="border-left: 4px solid {getPriorityColor(task.priority)}">
							<div class="task-header">
								<h4>{getDomainName(task.domain)}</h4>
								<span class="priority-badge" style="background: {getPriorityColor(task.priority)}">
									{getPriorityLabel(task.priority)}
								</span>
							</div>
							
							<p class="task-reason">{task.focus_reason}</p>
							
							<div class="task-details">
								<div class="detail">
									<span class="detail-label">Difficulty:</span>
									<span class="detail-value">{getDifficultyLabel(task.difficulty)} (Level {task.difficulty}/10)</span>
								</div>
							</div>
							
							<button 
								class="btn-start-task"
								on:click={() => goto(getTaskRoute(task.task_type, task.domain))}
							>
								Start Training
							</button>
						</div>
					{/each}
				</div>
			</div>
			
			<!-- Focus Areas -->
			<div class="focus-card">
				<h3>Training Focus</h3>
				<div class="focus-grid">
					<div class="focus-section">
						<h4 class="focus-title primary">Primary Focus</h4>
						<p class="focus-desc">Your weakest areas - needs most attention</p>
						<ul class="focus-list">
							{#each trainingPlan.primary_focus as domain}
								<li>{getDomainName(domain)}</li>
							{/each}
						</ul>
					</div>
					
					<div class="focus-section">
						<h4 class="focus-title secondary">Secondary Focus</h4>
						<p class="focus-desc">Moderate areas - room for improvement</p>
						<ul class="focus-list">
							{#each trainingPlan.secondary_focus as domain}
								<li>{getDomainName(domain)}</li>
							{/each}
						</ul>
					</div>
					
					<div class="focus-section">
						<h4 class="focus-title maintenance">Maintenance</h4>
						<p class="focus-desc">Your strongest areas - maintain performance</p>
						<ul class="focus-list">
							{#each trainingPlan.maintenance as domain}
								<li>{getDomainName(domain)}</li>
							{/each}
						</ul>
					</div>
				</div>
			</div>
			
			<!-- Current Difficulty Levels -->
			<div class="difficulty-card">
				<h3>Current Difficulty Levels</h3>
				<div class="difficulty-grid">
					{#each Object.entries(trainingPlan.current_difficulty) as [domain, difficulty]}
						<div class="difficulty-item">
							<div class="difficulty-name">{getDomainName(domain)}</div>
							<div class="difficulty-bar">
								<div 
									class="difficulty-fill" 
									style="width: {(difficulty / 10) * 100}%"
								></div>
							</div>
							<div class="difficulty-level">Level {difficulty}/10</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.container {
		min-height: 100vh;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		padding: 2rem;
	}
	
	.loading-card, .error-card {
		max-width: 600px;
		margin: 0 auto;
		background: white;
		border-radius: 20px;
		padding: 3rem;
		text-align: center;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
	}
	
	.error-card h3 {
		color: #f44336;
		margin-bottom: 1rem;
	}
	
	.training-container {
		max-width: 1200px;
		margin: 0 auto;
	}
	
	.training-header {
		background: white;
		border-radius: 20px;
		padding: 2rem;
		margin-bottom: 2rem;
		box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
	}
	
	.header-content {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 2rem;
	}
	
	.header-text h1 {
		margin: 0 0 0.5rem 0;
		color: #333;
		font-size: 2rem;
	}
	
	.header-text .subtitle {
		margin: 0;
		color: #666;
		font-size: 1rem;
	}
	
	.btn-back {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		padding: 0.75rem 1.5rem;
		border-radius: 8px;
		cursor: pointer;
		font-weight: 600;
		transition: all 0.3s;
		white-space: nowrap;
	}
	
	.btn-back:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
	}
	
	.stats-card, .session-card, .focus-card, .difficulty-card {
		background: white;
		border-radius: 20px;
		padding: 2rem;
		margin-bottom: 2rem;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
	}
	
	.stats-card h3, .session-card h3, .focus-card h3, .difficulty-card h3 {
		margin: 0 0 1.5rem 0;
		color: #333;
	}
	
	.stats-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 2rem;
	}
	
	.stat {
		text-align: center;
	}
	
	.stat-value {
		font-size: 2.5rem;
		font-weight: bold;
		color: #667eea;
	}
	
	.stat-label {
		color: #666;
		margin-top: 0.5rem;
	}
	
	.session-subtitle {
		color: #666;
		margin-bottom: 2rem;
	}
	
	.tasks-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		gap: 1.5rem;
	}
	
	.task-card {
		background: #f8f9fa;
		border-radius: 12px;
		padding: 1.5rem;
	}
	
	.task-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}
	
	.task-header h4 {
		margin: 0;
		color: #333;
	}
	
	.priority-badge {
		color: white;
		padding: 0.25rem 0.75rem;
		border-radius: 20px;
		font-size: 0.8rem;
		font-weight: 600;
	}
	
	.task-reason {
		color: #666;
		font-size: 0.9rem;
		margin-bottom: 1rem;
	}
	
	.task-details {
		margin-bottom: 1rem;
	}
	
	.detail {
		display: flex;
		justify-content: space-between;
		padding: 0.5rem 0;
	}
	
	.detail-label {
		color: #666;
		font-weight: 600;
	}
	
	.detail-value {
		color: #333;
	}
	
	.btn-start-task {
		width: 100%;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		padding: 0.75rem 1.5rem;
		border-radius: 8px;
		cursor: pointer;
		font-weight: 600;
		transition: all 0.3s;
	}
	
	.btn-start-task:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
	}
	
	.focus-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: 2rem;
	}
	
	.focus-section {
		padding: 1.5rem;
		background: #f8f9fa;
		border-radius: 12px;
	}
	
	.focus-title {
		margin: 0 0 0.5rem 0;
		font-size: 1.1rem;
	}
	
	.focus-title.primary {
		color: #f44336;
	}
	
	.focus-title.secondary {
		color: #ff9800;
	}
	
	.focus-title.maintenance {
		color: #4caf50;
	}
	
	.focus-desc {
		color: #666;
		font-size: 0.85rem;
		margin-bottom: 1rem;
	}
	
	.focus-list {
		list-style: none;
		padding: 0;
	}
	
	.focus-list li {
		padding: 0.5rem 0;
		color: #333;
		font-weight: 600;
	}
	
	.difficulty-grid {
		display: grid;
		gap: 1rem;
	}
	
	.difficulty-item {
		display: grid;
		grid-template-columns: 200px 1fr 100px;
		align-items: center;
		gap: 1rem;
	}
	
	.difficulty-name {
		font-weight: 600;
		color: #333;
	}
	
	.difficulty-bar {
		height: 12px;
		background: #e0e0e0;
		border-radius: 6px;
		overflow: hidden;
	}
	
	.difficulty-fill {
		height: 100%;
		background: linear-gradient(90deg, #4caf50 0%, #ff9800 50%, #f44336 100%);
		transition: width 0.5s ease;
	}
	
	.difficulty-level {
		color: #666;
		font-size: 0.9rem;
	}
	
	.btn-primary {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		padding: 1rem 2.5rem;
		border-radius: 12px;
		font-size: 1.1rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s;
	}
	
	.btn-primary:hover {
		transform: translateY(-2px);
		box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
	}
</style>

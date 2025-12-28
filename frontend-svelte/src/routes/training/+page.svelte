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
	
	function getTaskRoute(taskType, domain, difficulty, planId) {
		// Map task types to routes with training mode parameters
		const routes = {
			n_back: '/baseline/tasks/working-memory',
			continuous_performance: '/baseline/tasks/attention',
			task_switching: '/baseline/tasks/flexibility',
			tower_of_hanoi: '/baseline/tasks/planning',
			reaction_time: '/baseline/tasks/processing-speed',
			target_search: '/baseline/tasks/visual-scanning'
		};
		
		const baseRoute = routes[taskType] || '/dashboard';
		// Add training mode parameters
		return `${baseRoute}?training=true&planId=${planId}&difficulty=${difficulty}`;
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
					<div class="header-actions">
						<button class="btn-refresh" on:click={loadTrainingData} disabled={loading}>
							{#if loading}
								⏳ Loading...
							{:else}
								🔄 Refresh
							{/if}
						</button>
						<button class="btn-back" on:click={backToDashboard}>← Back to Dashboard</button>
					</div>
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
			
			<!-- Current Training Session -->
			<div class="session-card">
				<div class="session-header">
					<h3>Training Session #{nextTasks.session_number}</h3>
					<div class="session-progress">
						<span class="progress-text">{nextTasks.completed_tasks} / {nextTasks.total_tasks} tasks completed</span>
						<div class="progress-bar-mini">
							<div class="progress-fill-mini" style="width: {(nextTasks.completed_tasks / nextTasks.total_tasks) * 100}%"></div>
						</div>
					</div>
				</div>
				
				{#if nextTasks.session_complete}
					<div class="session-complete-banner" on:click={() => goto(`/session-summary?session=${trainingPlan.total_sessions}`)}>
						<div class="banner-content">
							<span class="banner-icon">🎉</span>
							<div class="banner-text">
								<strong>Session Complete!</strong>
								<p>All tasks finished. Click to see your summary!</p>
							</div>
							<span class="banner-arrow">→</span>
						</div>
					</div>
				{:else}
					<p class="session-subtitle">Complete all {nextTasks.total_tasks} tasks to finish this session</p>
				{/if}
				
				<div class="tasks-grid">
					{#each nextTasks.tasks as task}
						<div class="task-card {task.completed ? 'completed' : ''}" style="border-left: 4px solid {getPriorityColor(task.priority)}">
							{#if task.completed}
								<div class="completed-overlay">
									<div class="checkmark">✓</div>
									<span class="completed-label">Completed</span>
								</div>
							{/if}
							
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
								disabled={task.completed}
								on:click={() => goto(getTaskRoute(task.task_type, task.domain, task.difficulty, trainingPlan.id))}
							>
								{task.completed ? '✓ Completed' : 'Start Training'}
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
		flex-wrap: wrap;
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
	
	.header-actions {
		display: flex;
		gap: 1rem;
		align-items: center;
	}
	
	.btn-refresh {
		background: white;
		color: #667eea;
		border: 2px solid #667eea;
		padding: 0.75rem 1.5rem;
		border-radius: 8px;
		cursor: pointer;
		font-weight: 600;
		transition: all 0.3s;
		white-space: nowrap;
	}
	
	.btn-refresh:hover:not(:disabled) {
		background: #667eea;
		color: white;
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
	}
	
	.btn-refresh:disabled {
		opacity: 0.6;
		cursor: not-allowed;
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
	
	.session-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
		flex-wrap: wrap;
		gap: 1rem;
	}
	
	.session-progress {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		gap: 0.5rem;
	}
	
	.progress-text {
		color: #667eea;
		font-weight: 600;
		font-size: 0.95rem;
	}
	
	.progress-bar-mini {
		width: 200px;
		height: 8px;
		background: #e0e0e0;
		border-radius: 10px;
		overflow: hidden;
	}
	
	.progress-fill-mini {
		height: 100%;
		background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
		transition: width 0.3s ease;
	}
	
	.session-complete-banner {
		background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
		color: white;
		padding: 1.5rem;
		border-radius: 15px;
		margin-bottom: 1.5rem;
		cursor: pointer;
		transition: all 0.3s;
		box-shadow: 0 4px 15px rgba(76, 175, 80, 0.4);
		animation: celebrate 0.5s ease;
	}
	
	.session-complete-banner:hover {
		transform: translateY(-3px);
		box-shadow: 0 6px 20px rgba(76, 175, 80, 0.6);
	}
	
	.banner-content {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
	}
	
	.banner-icon {
		font-size: 2.5rem;
		animation: bounce 1s infinite;
	}
	
	.banner-text {
		flex: 1;
		text-align: left;
	}
	
	.banner-text strong {
		display: block;
		font-size: 1.2rem;
		margin-bottom: 0.25rem;
	}
	
	.banner-text p {
		margin: 0;
		font-size: 0.95rem;
		opacity: 0.95;
		font-weight: normal;
	}
	
	.banner-arrow {
		font-size: 1.5rem;
		font-weight: bold;
		animation: slideRight 1s infinite;
	}
	
	@keyframes celebrate {
		0%, 100% { transform: scale(1); }
		50% { transform: scale(1.02); }
	}
	
	@keyframes bounce {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-5px); }
	}
	
	@keyframes slideRight {
		0%, 100% { transform: translateX(0); }
		50% { transform: translateX(5px); }
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
		position: relative;
		transition: all 0.3s ease;
	}
	
	.task-card.completed {
		opacity: 0.7;
		background: #e8f5e9;
	}
	
	.completed-overlay {
		position: absolute;
		top: 0;
		right: 0;
		background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
		color: white;
		padding: 0.5rem 1rem;
		border-radius: 0 12px 0 12px;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-weight: 600;
		font-size: 0.9rem;
	}
	
	.checkmark {
		font-size: 1.2rem;
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
	
	.btn-start-task:disabled {
		background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
		cursor: not-allowed;
		opacity: 0.8;
	}
	
	.btn-start-task:not(:disabled):hover {
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

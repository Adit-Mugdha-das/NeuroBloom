<script>
	import { goto } from '$app/navigation';
	import { training } from '$lib/api';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';
	
	let currentUser = null;
	let loading = true;
	let metrics = null;
	let history = null;
	let error = null;
	
	user.subscribe(value => {
		currentUser = value;
	});
	
	onMount(async () => {
		if (!currentUser) {
			goto('/login');
			return;
		}
		
		await loadProgressData();
	});
	
	async function loadProgressData() {
		loading = true;
		error = null;
		
		try {
			// Load performance metrics
			metrics = await training.getMetrics(currentUser.id);
			
			// Load session history
			history = await training.getHistory(currentUser.id, 20);
		} catch (err) {
			console.error('Error loading progress data:', err);
			error = 'No training data found. Start training to see your progress.';
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
	
	function getTrendIcon(trend) {
		if (trend === 'improving') return '📈';
		if (trend === 'declining') return '📉';
		return '➡️';
	}
	
	function getTrendColor(trend) {
		if (trend === 'improving') return '#4caf50';
		if (trend === 'declining') return '#f44336';
		return '#ff9800';
	}
	
	function getTrendLabel(trend) {
		if (trend === 'improving') return 'Improving';
		if (trend === 'declining') return 'Declining';
		return 'Stable';
	}
	
	function getScoreColor(score) {
		if (score >= 80) return '#4caf50';
		if (score >= 60) return '#ff9800';
		return '#f44336';
	}
	
	function backToDashboard() {
		goto('/dashboard');
	}
</script>

<div class="container">
	{#if loading}
		<div class="loading-card">
			<p>Loading progress data...</p>
		</div>
	{:else if error}
		<div class="error-card">
			<h3>No Training Data</h3>
			<p>{error}</p>
			<button class="btn-primary" on:click={() => goto('/training')}>
				Start Training
			</button>
		</div>
	{:else if metrics}
		<div class="progress-container">
			<!-- Header -->
			<div class="progress-header">
				<div class="header-content">
					<div class="header-text">
						<h1>Training Progress</h1>
						<p class="subtitle">Track your cognitive improvement over time</p>
					</div>
					<button class="btn-back" on:click={backToDashboard}>← Back to Dashboard</button>
				</div>
			</div>
			
			<!-- Overall Stats -->
			<div class="stats-overview">
				<div class="stat-card">
					<div class="stat-icon">🎯</div>
					<div class="stat-value">{metrics.total_sessions}</div>
					<div class="stat-label">Total Sessions</div>
				</div>
				
				<div class="stat-card">
					<div class="stat-icon">📅</div>
					<div class="stat-value">
						{metrics.last_training_date ? new Date(metrics.last_training_date).toLocaleDateString() : 'Never'}
					</div>
					<div class="stat-label">Last Training</div>
				</div>
				
				<div class="stat-card">
					<div class="stat-icon">⚡</div>
					<div class="stat-value">
						{Object.keys(metrics.metrics_by_domain || {}).length}
					</div>
					<div class="stat-label">Active Domains</div>
				</div>
			</div>
			
			<!-- Domain Performance -->
			<div class="performance-card">
				<h3>Performance by Domain</h3>
				<div class="domains-grid">
					{#each Object.entries(metrics.metrics_by_domain || {}) as [domain, domainMetrics]}
						<div class="domain-performance">
							<div class="domain-header">
								<h4>{getDomainName(domain)}</h4>
								<span 
									class="trend-badge" 
									style="background: {getTrendColor(domainMetrics.trend)}"
								>
									{getTrendIcon(domainMetrics.trend)} {getTrendLabel(domainMetrics.trend)}
								</span>
							</div>
							
							<div class="metrics-row">
								<div class="metric">
									<span class="metric-label">Sessions</span>
									<span class="metric-value">{domainMetrics.total_sessions}</span>
								</div>
								<div class="metric">
									<span class="metric-label">Avg Score</span>
									<span class="metric-value" style="color: {getScoreColor(domainMetrics.average_score)}">
										{domainMetrics.average_score.toFixed(1)}
									</span>
								</div>
								<div class="metric">
									<span class="metric-label">Accuracy</span>
									<span class="metric-value">{domainMetrics.average_accuracy.toFixed(1)}%</span>
								</div>
								<div class="metric">
									<span class="metric-label">Difficulty</span>
									<span class="metric-value">{domainMetrics.current_difficulty}/10</span>
								</div>
							</div>
							
							{#if domainMetrics.improvement !== 0}
								<div class="improvement-bar">
									<div class="improvement-text">
										{#if domainMetrics.improvement > 0}
											<span style="color: #4caf50">↑ +{domainMetrics.improvement.toFixed(1)} points improvement</span>
										{:else}
											<span style="color: #f44336">↓ {domainMetrics.improvement.toFixed(1)} points</span>
										{/if}
									</div>
								</div>
							{/if}
							
							<!-- Progress bar -->
							<div class="progress-bar">
								<div 
									class="progress-fill" 
									style="width: {domainMetrics.average_score}%; background: {getScoreColor(domainMetrics.average_score)}"
								></div>
							</div>
						</div>
					{/each}
				</div>
			</div>
			
			<!-- Recent Sessions Timeline -->
			<div class="history-card">
				<h3>Recent Training Sessions</h3>
				{#if history && history.length > 0}
					<div class="timeline">
						{#each history as session}
							<div class="timeline-item">
								<div class="timeline-marker"></div>
								<div class="timeline-content">
									<div class="session-header">
										<h4>{getDomainName(session.domain)}</h4>
										<span class="session-date">{new Date(session.created_at).toLocaleDateString()}</span>
									</div>
									<div class="session-stats">
										<div class="session-stat">
											<span class="stat-label">Score:</span>
											<span class="stat-value" style="color: {getScoreColor(session.score)}">
												{session.score.toFixed(1)}
											</span>
										</div>
										<div class="session-stat">
											<span class="stat-label">Accuracy:</span>
											<span class="stat-value">{session.accuracy.toFixed(1)}%</span>
										</div>
										<div class="session-stat">
											<span class="stat-label">Difficulty:</span>
											<span class="stat-value">Level {session.difficulty}</span>
										</div>
										<div class="session-stat">
											<span class="stat-label">Duration:</span>
											<span class="stat-value">{Math.floor(session.duration / 60)}m {session.duration % 60}s</span>
										</div>
									</div>
								</div>
							</div>
						{/each}
					</div>
				{:else}
					<p class="no-data">No training sessions yet. Start training to build your history.</p>
				{/if}
			</div>
			
			<!-- Current Difficulty Levels -->
			<div class="difficulty-overview">
				<h3>Current Training Difficulty</h3>
				<div class="difficulty-bars">
					{#each Object.entries(metrics.current_difficulty) as [domain, difficulty]}
						<div class="difficulty-row">
							<span class="difficulty-name">{getDomainName(domain)}</span>
							<div class="difficulty-bar-container">
								<div 
									class="difficulty-bar-fill" 
									style="width: {(difficulty / 10) * 100}%"
								></div>
							</div>
							<span class="difficulty-level">Level {difficulty}/10</span>
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
	
	.progress-container {
		max-width: 1200px;
		margin: 0 auto;
	}
	
	.progress-header {
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
	
	.stats-overview {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: 1.5rem;
		margin-bottom: 2rem;
	}
	
	.stat-card {
		background: white;
		border-radius: 20px;
		padding: 2rem;
		text-align: center;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
	}
	
	.stat-icon {
		font-size: 3rem;
		margin-bottom: 1rem;
	}
	
	.stat-value {
		font-size: 2rem;
		font-weight: bold;
		color: #667eea;
		margin-bottom: 0.5rem;
	}
	
	.stat-label {
		color: #666;
		font-size: 0.9rem;
	}
	
	.performance-card, .history-card, .difficulty-overview {
		background: white;
		border-radius: 20px;
		padding: 2rem;
		margin-bottom: 2rem;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
	}
	
	.performance-card h3, .history-card h3, .difficulty-overview h3 {
		margin: 0 0 1.5rem 0;
		color: #333;
	}
	
	.domains-grid {
		display: grid;
		gap: 1.5rem;
	}
	
	.domain-performance {
		background: #f8f9fa;
		border-radius: 12px;
		padding: 1.5rem;
	}
	
	.domain-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}
	
	.domain-header h4 {
		margin: 0;
		color: #333;
	}
	
	.trend-badge {
		color: white;
		padding: 0.25rem 0.75rem;
		border-radius: 20px;
		font-size: 0.8rem;
		font-weight: 600;
	}
	
	.metrics-row {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
		gap: 1rem;
		margin-bottom: 1rem;
	}
	
	.metric {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}
	
	.metric-label {
		color: #666;
		font-size: 0.8rem;
	}
	
	.metric-value {
		font-size: 1.2rem;
		font-weight: 600;
		color: #333;
	}
	
	.improvement-bar {
		margin: 1rem 0;
	}
	
	.improvement-text {
		font-size: 0.9rem;
		font-weight: 600;
	}
	
	.progress-bar {
		height: 8px;
		background: #e0e0e0;
		border-radius: 4px;
		overflow: hidden;
	}
	
	.progress-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.timeline {
		position: relative;
		padding-left: 2rem;
	}
	
	.timeline-item {
		position: relative;
		padding-bottom: 2rem;
	}
	
	.timeline-marker {
		position: absolute;
		left: -2rem;
		top: 0.5rem;
		width: 12px;
		height: 12px;
		background: #667eea;
		border-radius: 50%;
		border: 3px solid white;
		box-shadow: 0 0 0 2px #667eea;
	}
	
	.timeline-item::before {
		content: '';
		position: absolute;
		left: -1.5rem;
		top: 1.5rem;
		bottom: -0.5rem;
		width: 2px;
		background: #e0e0e0;
	}
	
	.timeline-item:last-child::before {
		display: none;
	}
	
	.timeline-content {
		background: #f8f9fa;
		border-radius: 8px;
		padding: 1rem;
	}
	
	.session-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.75rem;
	}
	
	.session-header h4 {
		margin: 0;
		color: #333;
		font-size: 1rem;
	}
	
	.session-date {
		color: #666;
		font-size: 0.85rem;
	}
	
	.session-stats {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
		gap: 0.75rem;
	}
	
	.session-stat {
		display: flex;
		justify-content: space-between;
		font-size: 0.9rem;
	}
	
	.session-stat .stat-label {
		color: #666;
	}
	
	.session-stat .stat-value {
		font-weight: 600;
		color: #333;
	}
	
	.no-data {
		text-align: center;
		color: #666;
		padding: 2rem;
	}
	
	.difficulty-bars {
		display: grid;
		gap: 1rem;
	}
	
	.difficulty-row {
		display: grid;
		grid-template-columns: 200px 1fr 100px;
		align-items: center;
		gap: 1rem;
	}
	
	.difficulty-name {
		font-weight: 600;
		color: #333;
	}
	
	.difficulty-bar-container {
		height: 12px;
		background: #e0e0e0;
		border-radius: 6px;
		overflow: hidden;
	}
	
	.difficulty-bar-fill {
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
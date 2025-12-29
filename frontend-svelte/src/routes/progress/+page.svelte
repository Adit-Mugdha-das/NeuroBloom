<script>
	import { goto } from '$app/navigation';
	import { baseline, training } from '$lib/api';
	import BadgesShowcase from '$lib/components/BadgesShowcase.svelte';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import PerformanceTrends from '$lib/components/PerformanceTrends.svelte';
	import WeeklySummary from '$lib/components/WeeklySummary.svelte';
	import { user } from '$lib/stores';
	import { downloadCSV } from '$lib/utils/chartDownload';
	import { onMount } from 'svelte';
	
	let currentUser = null;
	let loading = true;
	let metrics = null;
	let history = null;
	let comparison = null;
	let streakData = null;
	let badgeData = null;
	let trendsData = null;
	let weeklySummary = null;
	let baselineData = null;
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
			
			// Load baseline vs current comparison
			comparison = await training.getPerformanceComparison(currentUser.id);
			
			// Load baseline data for difficulty journey
			try {
				baselineData = await baseline.get(currentUser.id);
			} catch (err) {
				console.log('No baseline data available');
			}
			
			// Load streak data
			streakData = await training.getStreak(currentUser.id);
			
			// Load badge data
			badgeData = await training.getAvailableBadges(currentUser.id);
			
			// Load trends data (last 30 days)
			trendsData = await training.getTrends(currentUser.id, 30);
			
			// Load weekly summary
			weeklySummary = await training.getWeeklySummary(currentUser.id);
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
	
	function handleDownloadJourney() {
		if (!metrics || !baselineData) return;
		
		const journeyData = Object.entries(metrics.metrics_by_domain || {}).map(([domain, domainMetrics]) => {
			const baselineScore = baselineData.scores?.[domain] || 50;
			const baselineDifficulty = Math.max(1, Math.floor(baselineScore / 10));
			const currentDifficulty = metrics.current_difficulty[domain] || baselineDifficulty;
			
			return {
				domain: getDomainName(domain),
				baseline_difficulty: baselineDifficulty,
				current_difficulty: currentDifficulty,
				difficulty_gain: currentDifficulty - baselineDifficulty,
				total_sessions: domainMetrics.total_sessions,
				avg_score: domainMetrics.average_score.toFixed(1),
				trend: domainMetrics.trend
			};
		});
		
		const filename = `difficulty-journey-${new Date().toISOString().split('T')[0]}`;
		downloadCSV(journeyData, filename);
	}
	
	function handleDownloadHistory() {
		if (!history || history.length === 0) return;
		
		const historyData = history.map(session => ({
			date: new Date(session.created_at).toLocaleDateString(),
			domain: getDomainName(session.domain),
			score: session.score.toFixed(1),
			accuracy: session.accuracy.toFixed(1),
			difficulty_before: session.difficulty_before,
			difficulty_after: session.difficulty_after,
			duration_seconds: session.duration
		}));
		
		const filename = `session-history-${new Date().toISOString().split('T')[0]}`;
		downloadCSV(historyData, filename);
	}
</script>

<div class="container">
	{#if loading}
		<div class="loading-container">
			<LoadingSkeleton variant="card" count={4} />
			<LoadingSkeleton variant="default" count={1} />
		</div>
	{:else if error}
		<EmptyState 
			icon="📊"
			title="Start Your Progress Journey"
			message="Complete your first training session to see detailed analytics, trends, and badges!"
			actionText="Begin Training"
			actionLink="/training"
			tip="Consistent training leads to measurable cognitive improvements"
			variant="large"
		/>
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
				<!-- Streak Card -->
				{#if streakData}
				<div class="stat-card streak-card">
					<div class="stat-icon">🔥</div>
					<div class="stat-value">{streakData.current_streak}</div>
					<div class="stat-label">Day Streak</div>
					{#if streakData.current_streak > 0}
						<div class="streak-details">
							<small>Best: {streakData.longest_streak} days</small>
						</div>
					{/if}
				</div>
				{/if}
				
				<div class="stat-card clickable-stat" on:click={() => goto('/session-summary')}>
					<div class="stat-icon">🎉</div>
					<div class="stat-value">{metrics.total_sessions}</div>
					<div class="stat-label">Total Sessions</div>
					<div class="view-summary">View Last Summary →</div>
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
				<div class="card-header-with-actions">
					<h3>Recent Training Sessions</h3>
					{#if history && history.length > 0}
						<button class="download-btn-small" on:click={handleDownloadHistory} title="Download session history as CSV">
							📋 Download
						</button>
					{/if}
				</div>
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
			
			<!-- Difficulty Journey Visualization -->
			{#if baselineData}
			<div class="difficulty-journey">
				<div class="journey-header">
					<div class="journey-header-left">
						<h3>🎯 Your Difficulty Journey</h3>
						<p class="journey-subtitle">See how far you've progressed from your baseline</p>
					</div>
					<button class="download-btn-small" on:click={handleDownloadJourney} title="Download difficulty journey data as CSV">
						📋 Download
					</button>
				</div>
				
				<div class="journey-grid">
					{#each Object.entries(metrics.metrics_by_domain || {}) as [domain, domainMetrics]}
						{@const baselineScore = baselineData.scores?.[domain] || 50}
						{@const baselineDifficulty = Math.max(1, Math.floor(baselineScore / 10))}
						{@const currentDifficulty = metrics.current_difficulty[domain] || baselineDifficulty}
						{@const difficultyGain = currentDifficulty - baselineDifficulty}
						
						<div class="journey-card">
							<div class="journey-card-header">
								<h4>{getDomainName(domain)}</h4>
								{#if difficultyGain > 0}
									<span class="journey-badge gain">+{difficultyGain} Levels</span>
								{:else if difficultyGain < 0}
									<span class="journey-badge decline">{difficultyGain} Levels</span>
								{:else}
									<span class="journey-badge stable">Stable</span>
								{/if}
							</div>
							
							<div class="journey-track">
								<div class="track-labels">
									<span class="track-start">Start</span>
									<span class="track-end">Now</span>
								</div>
								
								<div class="journey-bar">
									<div 
										class="journey-progress" 
										style="width: {(currentDifficulty / 10) * 100}%"
									>
										<span class="progress-marker start" style="left: {(baselineDifficulty / currentDifficulty) * 100}%">
											<span class="marker-label">L{baselineDifficulty}</span>
										</span>
										<span class="progress-marker current">
											<span class="marker-label">L{currentDifficulty}</span>
										</span>
									</div>
								</div>
								
								<div class="journey-scale">
									{#each Array(10) as _, i}
										<span class="scale-mark" class:active={i + 1 <= currentDifficulty}>{i + 1}</span>
									{/each}
								</div>
							</div>
							
							<div class="journey-stats">
								<div class="stat-mini">
									<span class="stat-mini-label">Sessions:</span>
									<span class="stat-mini-value">{domainMetrics.total_sessions}</span>
								</div>
								<div class="stat-mini">
									<span class="stat-mini-label">Avg Score:</span>
									<span class="stat-mini-value" style="color: {getScoreColor(domainMetrics.average_score)}">
										{domainMetrics.average_score.toFixed(1)}
									</span>
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>
			{/if}
			
			<!-- Weekly Summary -->
			{#if weeklySummary}
				<WeeklySummary summaryData={weeklySummary} />
			{/if}
		
		<!-- Performance Trends -->
		{#if trendsData}
			<PerformanceTrends trendsData={trendsData} />
		{/if}
	
	<!-- Badges Showcase -->
	{#if badgeData}
		<BadgesShowcase 
			badges={badgeData.all_badges}
			totalBadges={badgeData.total_badges}
			earnedCount={badgeData.earned_count}
		/>
	{/if}
		</div>
	{/if}
</div>

<style>
	.loading-container {
		display: flex;
		flex-direction: column;
		gap: 2rem;
		padding: 2rem;
	}
	
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
	
	.clickable-stat {
		cursor: pointer;
		transition: all 0.3s;
		position: relative;
	}
	
	.clickable-stat:hover {
		transform: translateY(-5px);
		box-shadow: 0 12px 40px rgba(102, 126, 234, 0.3);
	}
	
	.view-summary {
		margin-top: 0.75rem;
		color: #667eea;
		font-size: 0.85rem;
		font-weight: 600;
		opacity: 0;
		transition: opacity 0.3s;
	}
	
	.clickable-stat:hover .view-summary {
		opacity: 1;
	}
	
	.streak-card {
		background: linear-gradient(135deg, #ff6b6b 0%, #feca57 100%);
		position: relative;
		overflow: hidden;
	}
	
	.streak-card .stat-icon {
		font-size: 3.5rem;
		animation: flameFlicker 2s ease-in-out infinite;
	}
	
	.streak-card .stat-value {
		color: white;
		font-size: 2.5rem;
		text-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
	}
	
	.streak-card .stat-label {
		color: rgba(255, 255, 255, 0.95);
		font-weight: 600;
		font-size: 1rem;
	}
	
	.streak-details {
		margin-top: 0.75rem;
		padding-top: 0.75rem;
		border-top: 1px solid rgba(255, 255, 255, 0.3);
	}
	
	.streak-details small {
		color: rgba(255, 255, 255, 0.9);
		font-size: 0.85rem;
		font-weight: 500;
	}
	
	@keyframes flameFlicker {
		0%, 100% {
			transform: scale(1) rotate(-2deg);
		}
		25% {
			transform: scale(1.05) rotate(2deg);
		}
		50% {
			transform: scale(1.1) rotate(-1deg);
		}
		75% {
			transform: scale(1.05) rotate(1deg);
		}
	}
	
	.card-header-with-actions {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
		gap: 1rem;
		flex-wrap: wrap;
	}
	
	.card-header-with-actions h3 {
		margin: 0;
	}
	
	.download-btn-small {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		padding: 0.4rem 0.8rem;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		border-radius: 6px;
		font-size: 0.8rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s;
		box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
		white-space: nowrap;
	}
	
	.download-btn-small:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
	}
	
	.download-btn-small:active {
		transform: translateY(0);
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
	
	/* Difficulty Journey Styles */
	.difficulty-journey {
		background: white;
		border-radius: 20px;
		padding: 2rem;
		margin-bottom: 2rem;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
	}
	
	.journey-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
		padding-bottom: 1.5rem;
		border-bottom: 2px solid #f0f0f0;
		gap: 1rem;
		flex-wrap: wrap;
	}
	
	.journey-header-left {
		flex: 1;
		min-width: 250px;
	}
	
	.journey-header h3 {
		margin: 0 0 0.5rem 0;
		color: #333;
		font-size: 1.8rem;
	}
	
	.journey-subtitle {
		margin: 0;
		color: #666;
		font-size: 0.95rem;
	}
	
	.journey-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
		gap: 1.5rem;
	}
	
	.journey-card {
		background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
		border-radius: 15px;
		padding: 1.5rem;
		border: 2px solid #e0e0e0;
		transition: all 0.3s;
	}
	
	.journey-card:hover {
		transform: translateY(-5px);
		border-color: #667eea;
		box-shadow: 0 8px 25px rgba(102, 126, 234, 0.2);
	}
	
	.journey-card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.25rem;
	}
	
	.journey-card-header h4 {
		margin: 0;
		color: #333;
		font-size: 1.1rem;
	}
	
	.journey-badge {
		padding: 0.35rem 0.85rem;
		border-radius: 20px;
		font-size: 0.8rem;
		font-weight: 700;
		color: white;
	}
	
	.journey-badge.gain {
		background: linear-gradient(135deg, #4caf50 0%, #81c784 100%);
		box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);
	}
	
	.journey-badge.decline {
		background: linear-gradient(135deg, #f44336 0%, #e57373 100%);
		box-shadow: 0 2px 8px rgba(244, 67, 54, 0.3);
	}
	
	.journey-badge.stable {
		background: linear-gradient(135deg, #ff9800 0%, #ffb74d 100%);
		box-shadow: 0 2px 8px rgba(255, 152, 0, 0.3);
	}
	
	.journey-track {
		margin-bottom: 1rem;
	}
	
	.track-labels {
		display: flex;
		justify-content: space-between;
		margin-bottom: 0.5rem;
		font-size: 0.8rem;
		color: #666;
		font-weight: 600;
	}
	
	.journey-bar {
		position: relative;
		height: 40px;
		background: #e0e0e0;
		border-radius: 20px;
		overflow: visible;
		margin-bottom: 0.75rem;
	}
	
	.journey-progress {
		position: relative;
		height: 100%;
		background: linear-gradient(90deg, #4caf50 0%, #ff9800 50%, #f44336 100%);
		border-radius: 20px;
		transition: width 0.8s ease;
		box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
	}
	
	.progress-marker {
		position: absolute;
		top: 50%;
		transform: translateY(-50%);
		width: 14px;
		height: 14px;
		background: white;
		border: 3px solid #333;
		border-radius: 50%;
		z-index: 2;
	}
	
	.progress-marker.start {
		border-color: #666;
		background: #fff;
	}
	
	.progress-marker.current {
		right: -7px;
		border-color: #667eea;
		background: #667eea;
		width: 18px;
		height: 18px;
		animation: pulse 2s ease-in-out infinite;
	}
	
	@keyframes pulse {
		0%, 100% { box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.7); }
		50% { box-shadow: 0 0 0 8px rgba(102, 126, 234, 0); }
	}
	
	.marker-label {
		position: absolute;
		top: -28px;
		left: 50%;
		transform: translateX(-50%);
		background: #333;
		color: white;
		padding: 0.2rem 0.5rem;
		border-radius: 6px;
		font-size: 0.7rem;
		font-weight: 700;
		white-space: nowrap;
	}
	
	.progress-marker.current .marker-label {
		background: #667eea;
	}
	
	.journey-scale {
		display: flex;
		justify-content: space-between;
		gap: 0.25rem;
	}
	
	.scale-mark {
		flex: 1;
		text-align: center;
		font-size: 0.7rem;
		color: #999;
		padding: 0.25rem;
		background: #f8f9fa;
		border-radius: 4px;
		font-weight: 600;
	}
	
	.scale-mark.active {
		background: #667eea;
		color: white;
	}
	
	.journey-stats {
		display: flex;
		justify-content: space-around;
		padding-top: 1rem;
		border-top: 1px solid #e0e0e0;
	}
	
	.stat-mini {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.25rem;
	}
	
	.stat-mini-label {
		font-size: 0.75rem;
		color: #666;
	}
	
	.stat-mini-value {
		font-size: 1rem;
		font-weight: 700;
		color: #333;
	}
</style>
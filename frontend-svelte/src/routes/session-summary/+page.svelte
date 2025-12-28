<script>
	import { goto } from '$app/navigation';
	import { training } from '$lib/api';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';
	import WeeklySummary from '$lib/components/WeeklySummary.svelte';
	
	let currentUser = null;
	let loading = true;
	let sessionData = null;
	let weeklySummary = null;
	let error = null;
	
	user.subscribe(value => {
		currentUser = value;
	});
	
	onMount(async () => {
		if (!currentUser) {
			goto('/login');
			return;
		}
		
		await loadSessionSummary();
	});
	
	async function loadSessionSummary() {
		loading = true;
		error = null;
		
		try {
			// Get URL parameters
			const params = new URLSearchParams(window.location.search);
			const sessionNumber = parseInt(params.get('session')) || 1;
			
			// Get recent session history (last 4 tasks = 1 session)
			const history = await training.getHistory(currentUser.id, 4);
			
			// Load weekly summary
			weeklySummary = await training.getWeeklySummary(currentUser.id);
			
			if (!history || history.length === 0) {
				error = 'No session data found';
				return;
			}
			
			// Calculate session statistics
			const avgScore = history.reduce((sum, s) => sum + s.score, 0) / history.length;
			const avgAccuracy = history.reduce((sum, s) => sum + s.accuracy, 0) / history.length;
			const totalErrors = history.reduce((sum, s) => sum + s.errors, 0);
			const tasksCompleted = history.length;
			
			// Group by domain for breakdown
			const taskBreakdown = history.map(session => ({
				domain: getDomainName(session.domain),
				score: session.score,
				accuracy: session.accuracy,
				difficultyBefore: session.difficulty_before,
				difficultyAfter: session.difficulty_after,
				difficultyChange: session.difficulty_after - session.difficulty_before,
				adaptationReason: session.adaptation_reason
			}));
			
			sessionData = {
				sessionNumber,
				avgScore: avgScore.toFixed(1),
				avgAccuracy: avgAccuracy.toFixed(1),
				totalErrors,
				tasksCompleted,
				taskBreakdown,
				timestamp: new Date(history[0].created_at).toLocaleString()
			};
			
		} catch (err) {
			console.error('Error loading session summary:', err);
			error = 'Failed to load session data';
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
	
	function getScoreColor(score) {
		if (score >= 80) return '#4caf50';
		if (score >= 60) return '#ff9800';
		return '#f44336';
	}
	
	function getDifficultyChangeIcon(change) {
		if (change > 0) return '📈';
		if (change < 0) return '📉';
		return '➡️';
	}
	
	function getDifficultyChangeText(change) {
		if (change > 0) return `+${change} (Harder)`;
		if (change < 0) return `${change} (Easier)`;
		return 'No change';
	}
	
	function continueTraining() {
		goto('/training');
	}
	
	function viewProgress() {
		goto('/progress');
	}
</script>

<div class="summary-container">
	{#if loading}
		<div class="loading">
			<p>Loading session summary...</p>
		</div>
	{:else if error}
		<div class="error">
			<p>{error}</p>
			<button on:click={continueTraining}>Back to Training</button>
		</div>
	{:else if sessionData}
		<!-- Header -->
		<div class="header">
			<div class="celebration">🎉</div>
			<h1>Session Complete!</h1>
			<p class="subtitle">Great work! You've completed Session #{sessionData.sessionNumber}</p>
		</div>
		
		<!-- Overall Stats -->
		<div class="stats-grid">
			<div class="stat-card">
				<div class="stat-icon">🎯</div>
				<div class="stat-value" style="color: {getScoreColor(sessionData.avgScore)}">
					{sessionData.avgScore}%
				</div>
				<div class="stat-label">Average Score</div>
			</div>
			
			<div class="stat-card">
				<div class="stat-icon">✓</div>
				<div class="stat-value">{sessionData.avgAccuracy}%</div>
				<div class="stat-label">Accuracy</div>
			</div>
			
			<div class="stat-card">
				<div class="stat-icon">📝</div>
				<div class="stat-value">{sessionData.tasksCompleted}/4</div>
				<div class="stat-label">Tasks Completed</div>
			</div>
			
			<div class="stat-card">
				<div class="stat-icon">⚠️</div>
				<div class="stat-value">{sessionData.totalErrors}</div>
				<div class="stat-label">Total Errors</div>
			</div>
		</div>
		
		<!-- Task Breakdown -->
		<div class="breakdown-card">
			<h3>This Session's Tasks</h3>
			<div class="tasks-list">
				{#each sessionData.taskBreakdown as task}
					<div class="task-row">
						<div class="task-info">
							<div class="task-name">{task.domain}</div>
							<div class="task-score" style="color: {getScoreColor(task.score)}">
								{task.score.toFixed(1)}%
							</div>
						</div>
						
						<div class="task-difficulty">
							<span class="difficulty-label">Difficulty:</span>
							<span class="difficulty-change">
								{getDifficultyChangeIcon(task.difficultyChange)}
								Level {task.difficultyBefore} → {task.difficultyAfter}
								<small>({getDifficultyChangeText(task.difficultyChange)})</small>
							</span>
						</div>
						
						{#if task.adaptationReason}
							<div class="adaptation-reason">
								<small>{task.adaptationReason}</small>
							</div>
						{/if}
					</div>
				{/each}
			</div>
		</div>
		
		<!-- Last 7 Days Overview -->
		{#if weeklySummary}
			<WeeklySummary summaryData={weeklySummary} />
		{/if}
		
		<!-- Next Steps -->
		<div class="next-steps">
			<h3>What's Next?</h3>
			<div class="buttons">
				<button class="btn-primary" on:click={continueTraining}>
					Continue Training
				</button>
				<button class="btn-secondary" on:click={viewProgress}>
					View Full Progress
				</button>
			</div>
			<p class="timestamp">Session completed at {sessionData.timestamp}</p>
		</div>
	{/if}
</div>

<style>
	.summary-container {
		max-width: 900px;
		margin: 0 auto;
		padding: 2rem;
		min-height: 100vh;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
	}
	
	.loading, .error {
		background: white;
		border-radius: 20px;
		padding: 3rem;
		text-align: center;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
	}
	
	.error button {
		margin-top: 1rem;
		padding: 0.75rem 2rem;
		background: #667eea;
		color: white;
		border: none;
		border-radius: 8px;
		cursor: pointer;
		font-weight: 600;
	}
	
	.header {
		background: white;
		border-radius: 20px;
		padding: 3rem;
		text-align: center;
		margin-bottom: 2rem;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
	}
	
	.celebration {
		font-size: 5rem;
		margin-bottom: 1rem;
		animation: bounce 1s ease infinite;
	}
	
	@keyframes bounce {
		0%, 100% {
			transform: translateY(0);
		}
		50% {
			transform: translateY(-20px);
		}
	}
	
	.header h1 {
		margin: 0 0 0.5rem 0;
		color: #333;
		font-size: 2.5rem;
	}
	
	.subtitle {
		margin: 0;
		color: #666;
		font-size: 1.1rem;
	}
	
	.stats-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1.5rem;
		margin-bottom: 2rem;
	}
	
	.stat-card {
		background: white;
		border-radius: 15px;
		padding: 2rem;
		text-align: center;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
		transition: transform 0.3s;
	}
	
	.stat-card:hover {
		transform: translateY(-5px);
	}
	
	.stat-icon {
		font-size: 2.5rem;
		margin-bottom: 1rem;
	}
	
	.stat-value {
		font-size: 2rem;
		font-weight: bold;
		margin-bottom: 0.5rem;
	}
	
	.stat-label {
		color: #666;
		font-size: 0.9rem;
	}
	
	.breakdown-card {
		background: white;
		border-radius: 20px;
		padding: 2rem;
		margin-bottom: 2rem;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
	}
	
	.breakdown-card h3 {
		margin: 0 0 1.5rem 0;
		color: #333;
	}
	
	.tasks-list {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}
	
	.task-row {
		padding: 1.5rem;
		background: #f5f5f5;
		border-radius: 12px;
		border-left: 4px solid #667eea;
	}
	
	.task-info {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.75rem;
	}
	
	.task-name {
		font-weight: 600;
		color: #333;
		font-size: 1.1rem;
	}
	
	.task-score {
		font-size: 1.5rem;
		font-weight: bold;
	}
	
	.task-difficulty {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 0.5rem;
	}
	
	.difficulty-label {
		color: #666;
		font-size: 0.9rem;
	}
	
	.difficulty-change {
		color: #333;
		font-weight: 600;
	}
	
	.difficulty-change small {
		color: #666;
		margin-left: 0.5rem;
	}
	
	.adaptation-reason {
		margin-top: 0.5rem;
	}
	
	.adaptation-reason small {
		color: #666;
		font-style: italic;
	}
	
	.next-steps {
		background: white;
		border-radius: 20px;
		padding: 2rem;
		text-align: center;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
	}
	
	.next-steps h3 {
		margin: 0 0 1.5rem 0;
		color: #333;
	}
	
	.buttons {
		display: flex;
		gap: 1rem;
		justify-content: center;
		margin-bottom: 1.5rem;
	}
	
	.btn-primary, .btn-secondary {
		padding: 1rem 2rem;
		border: none;
		border-radius: 10px;
		font-weight: 600;
		font-size: 1rem;
		cursor: pointer;
		transition: all 0.3s;
	}
	
	.btn-primary {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
	}
	
	.btn-primary:hover {
		transform: translateY(-2px);
		box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
	}
	
	.btn-secondary {
		background: white;
		color: #667eea;
		border: 2px solid #667eea;
	}
	
	.btn-secondary:hover {
		background: #f5f5f5;
	}
	
	.timestamp {
		margin: 0;
		color: #999;
		font-size: 0.9rem;
	}
	
	@media (max-width: 768px) {
		.summary-container {
			padding: 1rem;
		}
		
		.stats-grid {
			grid-template-columns: repeat(2, 1fr);
		}
		
		.buttons {
			flex-direction: column;
		}
		
		.btn-primary, .btn-secondary {
			width: 100%;
		}
	}
</style>

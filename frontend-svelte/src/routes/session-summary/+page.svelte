<script>
	import { locale as activeLocale, uiText } from '$lib/i18n';
	import { goto } from '$app/navigation';
	import { training } from '$lib/api';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';
	
	let currentUser = null;
	let loading = true;
	let sessionData = null;
	let error = null;
	let metricsData = null;
	let sessionDuration = 0;
	
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
			
			// Load metrics for additional data
			metricsData = await training.getMetrics(currentUser.id);
			
			// Calculate session statistics
			const avgScore = history.reduce((sum, s) => sum + s.score, 0) / history.length;
			const avgAccuracy = history.reduce((sum, s) => sum + s.accuracy, 0) / history.length;
			const totalErrors = history.reduce((sum, s) => sum + s.errors, 0);
			const tasksCompleted = history.length;
			
			// Calculate total session duration
			sessionDuration = history.reduce((sum, s) => sum + (s.duration || 0), 0);
			
			// Group by domain for breakdown
			const taskBreakdown = history.map(session => {
				const domainKey = session.domain;
				const domainMetrics = metricsData?.metrics_by_domain?.[domainKey];
				const isPersonalBest = domainMetrics && session.score >= domainMetrics.best_score;
				
				return {
					domain: getDomainName(session.domain),
					domainKey: domainKey,
					score: session.score,
					accuracy: session.accuracy,
					difficultyBefore: session.difficulty_before,
					difficultyAfter: session.difficulty_after,
					difficultyChange: session.difficulty_after - session.difficulty_before,
					adaptationReason: session.adaptation_reason,
					isPersonalBest: isPersonalBest,
					bestScore: domainMetrics?.best_score || 0,
					nextDifficulty: session.difficulty_after
				};
			});
			
			// Calculate sessions until rebalancing (rebalance happens every 4 sessions)
			const totalSessions = metricsData?.total_sessions || 0;
			const sessionsUntilRebalance = 4 - (totalSessions % 4);
			
			sessionData = {
				sessionNumber,
				avgScore: avgScore.toFixed(1),
				avgAccuracy: avgAccuracy.toFixed(1),
				totalErrors,
				tasksCompleted,
				taskBreakdown,
				timestamp: new Date(history[0].created_at).toLocaleString(),
				duration: sessionDuration,
				sessionsUntilRebalance: sessionsUntilRebalance,
				totalSessions: totalSessions
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
		<div class="loading-container">
			<LoadingSkeleton variant="card" count={4} />
		</div>
	{:else if error}
		<EmptyState 
			icon="🎯"
			title={uiText("No Session Data", $activeLocale)}
			message={uiText("Complete a training session to see your celebration summary here!", $activeLocale)}
			actionText={uiText("Start Training", $activeLocale)}
			actionLink="/training"
			tip={uiText("Each session includes 4 cognitive tasks designed to challenge your brain", $activeLocale)}
		/>
	{:else if sessionData}
		<!-- Header -->
		<div class="header">
			<div class="celebration">🎉</div>
			<h1>{uiText("Session Complete!", $activeLocale)}</h1>
			<p class="subtitle">{uiText("Great work! You've completed Session #", $activeLocale)}{sessionData.sessionNumber}</p>
		</div>
		
		<!-- Overall Stats -->
		<div class="stats-grid">
			<div class="stat-card">
				<div class="stat-icon">🎯</div>
				<div class="stat-value" style="color: {getScoreColor(sessionData.avgScore)}">
					{sessionData.avgScore}%
				</div>
				<div class="stat-label">{uiText("Average Score", $activeLocale)}</div>
			</div>
			
			<div class="stat-card">
				<div class="stat-icon">✓</div>
				<div class="stat-value">{sessionData.avgAccuracy}%</div>
				<div class="stat-label">{uiText("Accuracy", $activeLocale)}</div>
			</div>
			
			<div class="stat-card">
				<div class="stat-icon">⏱️</div>
				<div class="stat-value">
					{Math.floor(sessionData.duration / 60)}:{(sessionData.duration % 60).toString().padStart(2, '0')}
				</div>
				<div class="stat-label">{uiText("Session Duration", $activeLocale)}</div>
			</div>
			
			<div class="stat-card rebalance-card">
				<div class="stat-icon">🔄</div>
				<div class="stat-value">{sessionData.sessionsUntilRebalance}</div>
				<div class="stat-label">{uiText("Until Rebalancing", $activeLocale)}</div>
				<div class="stat-subtext">{uiText("Training plan auto-adjusts", $activeLocale)}</div>
			</div>
		</div>
		
		<!-- Task Breakdown -->
		<div class="breakdown-card">
			<h3>{uiText("This Session's Tasks", $activeLocale)}</h3>
			<div class="tasks-list">
				{#each sessionData.taskBreakdown as task}
					<div class="task-row">
						<div class="task-info">
							<div class="task-name">
								{task.domain}
								{#if task.isPersonalBest}
									<span class="personal-best" title={uiText("Personal Best!", $activeLocale)}>🏆</span>
								{/if}
							</div>
							<div class="task-score" style="color: {getScoreColor(task.score)}">
								{task.score.toFixed(1)}%
								{#if task.isPersonalBest}
									<span class="pb-label">{uiText("PB!", $activeLocale)}</span>
								{/if}
							</div>
						</div>
						
						<div class="task-difficulty">
							<span class="difficulty-label">{uiText("Difficulty:", $activeLocale)}</span>
							<span class="difficulty-change">
								{getDifficultyChangeIcon(task.difficultyChange)}
								{uiText("Level", $activeLocale)} {task.difficultyBefore} → {task.difficultyAfter}
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
		
		<!-- Next Session Preview -->
		<div class="next-session-preview">
			<h3>{uiText("🎯 Next Session Preview", $activeLocale)}</h3>
			<p class="preview-subtitle">{uiText("Here's what to expect in your next training session", $activeLocale)}</p>
			<div class="preview-grid">
				{#each sessionData.taskBreakdown as task}
					{@const difficultyChange = task.difficultyChange}
					{@const difficultyCategory = task.nextDifficulty <= 3 ? 'beginner' : task.nextDifficulty <= 6 ? 'intermediate' : task.nextDifficulty <= 8 ? 'advanced' : 'expert'}
					{@const categoryLabel = task.nextDifficulty <= 3 ? 'Beginner' : task.nextDifficulty <= 6 ? 'Intermediate' : task.nextDifficulty <= 8 ? 'Advanced' : 'Expert'}
					
					<div class="preview-card {difficultyCategory}">
						<div class="preview-header">
							<div class="preview-domain">{task.domain}</div>
							{#if difficultyChange > 0}
								<span class="change-indicator up">{uiText("▲ Harder", $activeLocale)}</span>
							{:else if difficultyChange < 0}
								<span class="change-indicator down">{uiText("▼ Easier", $activeLocale)}</span>
							{:else}
								<span class="change-indicator stable">{uiText("◆ Same", $activeLocale)}</span>
							{/if}
						</div>
						
						<div class="difficulty-display">
							<div class="difficulty-number">{task.nextDifficulty}</div>
							<div class="difficulty-max">/10</div>
						</div>
						
						<div class="category-badge">{categoryLabel}</div>
						
						<div class="difficulty-description">
							{#if task.nextDifficulty <= 3}
								{uiText("Warm-up level - building foundations", $activeLocale)}
							{:else if task.nextDifficulty <= 6}
								{uiText("Moderate challenge - good progress", $activeLocale)}
							{:else if task.nextDifficulty <= 8}
								{uiText("Demanding - pushing your limits", $activeLocale)}
							{:else}
								{uiText("Elite level - maximum difficulty", $activeLocale)}
							{/if}
						</div>
					</div>
				{/each}
			</div>
		</div>
		
		<!-- Next Steps -->
		<div class="next-steps">
			<h3>{uiText("What's Next?", $activeLocale)}</h3>
			<div class="buttons">
				<button class="btn-primary" on:click={continueTraining}>
					{uiText("Continue Training", $activeLocale)}
				</button>
				<button class="btn-secondary" on:click={viewProgress}>
					{uiText("View Full Progress", $activeLocale)}
				</button>
			</div>
			<p class="timestamp">{uiText("Session completed at", $activeLocale)} {sessionData.timestamp}</p>
		</div>
	{/if}
</div>

<style>
	.loading-container {
		padding: 2rem;
	}
	
	.summary-container {
		max-width: 900px;
		margin: 0 auto;
		padding: 2rem;
		min-height: 100vh;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
		grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
		gap: 1.5rem;
		margin-bottom: 2rem;
	}
	
	.stat-card {
		background: white;
		border-radius: 15px;
		padding: 1.75rem;
		text-align: center;
		box-shadow: 0 5px 20px rgba(0, 0, 0, 0.2);
		transition: transform 0.3s;
	}
	
	.stat-card:hover {
		transform: translateY(-5px);
	}
	
	.stat-icon {
		font-size: 2.5rem;
		margin-bottom: 0.75rem;
	}
	
	.stat-value {
		font-size: 2.25rem;
		font-weight: 700;
		margin-bottom: 0.5rem;
	}
	
	.stat-label {
		color: #666;
		font-size: 0.9rem;
		font-weight: 500;
	}
	
	.stat-subtext {
		margin-top: 0.5rem;
		color: #999;
		font-size: 0.75rem;
	}
	
	.rebalance-card {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
	}
	
	.rebalance-card .stat-value,
	.rebalance-card .stat-label {
		color: white;
	}
	
	.rebalance-card .stat-subtext {
		color: rgba(255, 255, 255, 0.8);
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
		font-size: 1.5rem;
		font-weight: 700;
	}
	
	.tasks-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.task-row {
		padding: 1.5rem;
		background: #f8f9fa;
		border-radius: 12px;
		border-left: 4px solid #667eea;
		transition: all 0.3s;
	}
	
	.task-row:hover {
		background: #f0f2f5;
		border-left-color: #764ba2;
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
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.personal-best {
		font-size: 1.3rem;
		animation: trophy-bounce 0.6s ease infinite;
	}
	
	@keyframes trophy-bounce {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-4px); }
	}
	
	.pb-label {
		font-size: 0.7rem;
		background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
		color: #333;
		padding: 0.15rem 0.4rem;
		border-radius: 4px;
		font-weight: 700;
		margin-left: 0.5rem;
		box-shadow: 0 2px 5px rgba(255, 215, 0, 0.3);
	}
	
	.task-score {
		font-size: 1.5rem;
		font-weight: 700;
	}
	
	.task-difficulty {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 0.5rem;
		flex-wrap: wrap;
	}
	
	.difficulty-label {
		color: #666;
		font-size: 0.9rem;
		font-weight: 500;
	}
	
	.difficulty-change {
		color: #333;
		font-weight: 600;
		font-size: 0.95rem;
	}
	
	.difficulty-change small {
		color: #666;
		margin-left: 0.5rem;
		font-weight: 400;
	}
	
	.adaptation-reason {
		margin-top: 0.75rem;
		padding-top: 0.75rem;
		border-top: 1px solid #e0e0e0;
	}
	
	.adaptation-reason small {
		color: #666;
		font-style: italic;
		line-height: 1.4;
	}
	
	.next-steps {
		background: white;
		border-radius: 20px;
		padding: 2.5rem 2rem;
		text-align: center;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
		margin-top: 2rem;
	}
	
	.next-steps h3 {
		margin: 0 0 2rem 0;
		color: #333;
		font-size: 1.5rem;
		font-weight: 700;
	}
	
	.buttons {
		display: flex;
		gap: 1rem;
		justify-content: center;
		margin-bottom: 1.5rem;
	}
	
	.btn-primary, .btn-secondary {
		padding: 1rem 2.5rem;
		border: none;
		border-radius: 12px;
		font-weight: 600;
		font-size: 1rem;
		cursor: pointer;
		transition: all 0.3s;
		flex: 1;
		max-width: 250px;
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
		transform: translateY(-2px);
	}
	
	.timestamp {
		margin: 0;
		color: #999;
		font-size: 0.9rem;
	}
	
	.next-session-preview {
		background: white;
		border-radius: 20px;
		padding: 2rem;
		margin-bottom: 2rem;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
	}
	
	.next-session-preview h3 {
		margin: 0 0 0.5rem 0;
		color: #333;
		font-size: 1.5rem;
		font-weight: 700;
	}
	
	.preview-subtitle {
		margin: 0 0 1.5rem 0;
		color: #666;
		font-size: 0.95rem;
	}
	
	.preview-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		gap: 1.25rem;
	}
	
	.preview-card {
		border-radius: 15px;
		padding: 1.5rem;
		border: 3px solid;
		transition: all 0.3s;
		text-align: center;
	}
	
	.preview-card.beginner {
		background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
		border-color: #4caf50;
	}
	
	.preview-card.intermediate {
		background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
		border-color: #ff9800;
	}
	
	.preview-card.advanced {
		background: linear-gradient(135deg, #fce4ec 0%, #f8bbd0 100%);
		border-color: #e91e63;
	}
	
	.preview-card.expert {
		background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
		border-color: #9c27b0;
	}
	
	.preview-card:hover {
		transform: translateY(-5px) scale(1.02);
		box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
	}
	
	.preview-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}
	
	.preview-domain {
		font-weight: 700;
		color: #333;
		font-size: 1rem;
		text-align: left;
	}
	
	.change-indicator {
		font-size: 0.75rem;
		padding: 0.25rem 0.6rem;
		border-radius: 12px;
		font-weight: 700;
	}
	
	.change-indicator.up {
		background: #f44336;
		color: white;
	}
	
	.change-indicator.down {
		background: #4caf50;
		color: white;
	}
	
	.change-indicator.stable {
		background: #9e9e9e;
		color: white;
	}
	
	.difficulty-display {
		display: flex;
		align-items: baseline;
		justify-content: center;
		margin: 1rem 0;
	}
	
	.difficulty-number {
		font-size: 4rem;
		font-weight: 900;
		color: #333;
		line-height: 1;
	}
	
	.difficulty-max {
		font-size: 1.5rem;
		color: #999;
		font-weight: 600;
		margin-left: 0.25rem;
	}
	
	.category-badge {
		display: inline-block;
		padding: 0.4rem 1rem;
		border-radius: 20px;
		font-size: 0.85rem;
		font-weight: 700;
		margin-bottom: 0.75rem;
		background: rgba(0, 0, 0, 0.1);
		color: #333;
	}
	
	.difficulty-description {
		font-size: 0.85rem;
		color: #666;
		line-height: 1.4;
		font-style: italic;
	}
	
	@media (max-width: 768px) {
		.summary-container {
			padding: 1.5rem;
		}
		
		.header {
			padding: 2rem 1.5rem;
		}
		
		.celebration {
			font-size: 3.5rem;
		}
		
		.header h1 {
			font-size: 2rem;
		}
		
		.stats-grid {
			grid-template-columns: repeat(2, 1fr);
			gap: 1rem;
		}
		
		.stat-card {
			padding: 1.25rem;
		}
		
		.stat-icon {
			font-size: 2rem;
		}
		
		.stat-value {
			font-size: 1.75rem;
		}
		
		.breakdown-card {
			padding: 1.5rem;
		}
		
		.task-row {
			padding: 1.25rem;
		}
		
		.task-info {
			flex-direction: column;
			align-items: flex-start;
			gap: 0.5rem;
		}
		
		.task-difficulty {
			flex-direction: column;
			align-items: flex-start;
		}
		
		.buttons {
			flex-direction: column;
		}
		
		.btn-primary, .btn-secondary {
			width: 100%;
			max-width: none;
		}
		
		.next-steps {
			padding: 2rem 1.5rem;
		}
	}
</style>

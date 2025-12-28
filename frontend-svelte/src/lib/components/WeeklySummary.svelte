<script>
	/** @type {any} */
	export let summaryData = null;
	
	const domainNames = {
		working_memory: 'Working Memory',
		attention: 'Attention',
		flexibility: 'Cognitive Flexibility',
		planning: 'Planning',
		processing_speed: 'Processing Speed',
		visual_scanning: 'Visual Scanning'
	};
	
	const domainIcons = {
		working_memory: '🧠',
		attention: '👁️',
		flexibility: '🔄',
		planning: '🎯',
		processing_speed: '⚡',
		visual_scanning: '🔍'
	};
	
	function getDayName(dateStr) {
		const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
		const date = new Date(dateStr);
		return days[date.getDay()];
	}
	
	function getScoreColor(score) {
		if (score >= 80) return '#4caf50';
		if (score >= 60) return '#ff9800';
		return '#f44336';
	}
	
	function getChangeIcon(change) {
		if (change > 0) return '📈';
		if (change < 0) return '📉';
		return '➡️';
	}
</script>

{#if summaryData && summaryData.has_data}
	<div class="weekly-summary">
		<div class="summary-header">
			<h3>📅 This Week's Summary</h3>
			<p class="week-range">
				{new Date(summaryData.week_start).toLocaleDateString()} - {new Date(summaryData.week_end).toLocaleDateString()}
			</p>
		</div>
		
		<div class="summary-grid">
			<!-- Total Sessions Card -->
			<div class="summary-card sessions">
				<div class="card-icon">🎯</div>
				<div class="card-content">
					<div class="card-value">{summaryData.total_sessions}</div>
					<div class="card-label">Sessions Completed</div>
					<div class="card-subtext">{summaryData.active_days}/7 active days</div>
				</div>
			</div>
			
			<!-- Average Score Card -->
			<div class="summary-card score">
				<div class="card-icon">⭐</div>
				<div class="card-content">
					<div class="card-value" style="color: {getScoreColor(summaryData.avg_score)}">
						{summaryData.avg_score}
					</div>
					<div class="card-label">Average Score</div>
					{#if summaryData.score_change_from_last_week !== 0}
						<div class="card-subtext change">
							{getChangeIcon(summaryData.score_change_from_last_week)}
							{Math.abs(summaryData.score_change_from_last_week).toFixed(1)} from last week
						</div>
					{/if}
				</div>
			</div>
			
			<!-- Accuracy Card -->
			<div class="summary-card accuracy">
				<div class="card-icon">🎪</div>
				<div class="card-content">
					<div class="card-value">{summaryData.avg_accuracy}%</div>
					<div class="card-label">Average Accuracy</div>
				</div>
			</div>
			
			<!-- Training Time Card -->
			<div class="summary-card time">
				<div class="card-icon">⏱️</div>
				<div class="card-content">
					<div class="card-value">{summaryData.total_time_minutes} min</div>
					<div class="card-label">Total Training Time</div>
				</div>
			</div>
			
			<!-- Streak Card -->
			<div class="summary-card streak">
				<div class="card-icon">🔥</div>
				<div class="card-content">
					<div class="card-value">{summaryData.current_streak}</div>
					<div class="card-label">Current Streak</div>
					<div class="card-subtext">Keep it going!</div>
				</div>
			</div>
			
			<!-- Most Improved Card -->
			{#if summaryData.most_improved}
				<div class="summary-card improved">
					<div class="card-icon">{domainIcons[summaryData.most_improved.domain]}</div>
					<div class="card-content">
						<div class="card-value">+{summaryData.most_improved.improvement.toFixed(1)}</div>
						<div class="card-label">Most Improved</div>
						<div class="card-subtext">{domainNames[summaryData.most_improved.domain]}</div>
					</div>
				</div>
			{/if}
		</div>
		
		<!-- Daily Activity Chart -->
		<div class="daily-activity">
			<h4>Daily Activity</h4>
			<div class="activity-bars">
				{#each Object.entries(summaryData.daily_counts) as [date, count]}
					<div class="day-bar">
						<div class="bar-container">
							<div 
								class="bar" 
								class:active={count > 0}
								style="height: {Math.min(count * 30, 100)}%"
							>
								{#if count > 0}
									<span class="bar-label">{count}</span>
								{/if}
							</div>
						</div>
						<div class="day-label">{getDayName(date)}</div>
					</div>
				{/each}
			</div>
		</div>
		
		<!-- Domains Trained -->
		<div class="domains-section">
			<h4>Domains Trained This Week</h4>
			<div class="domain-tags">
				{#each summaryData.domains_trained as domain}
					<div class="domain-tag">
						<span class="tag-icon">{domainIcons[domain]}</span>
						<span class="tag-name">{domainNames[domain]}</span>
					</div>
				{/each}
			</div>
		</div>
	</div>
{:else}
	<div class="weekly-summary empty">
		<div class="empty-state">
			<div class="empty-icon">📅</div>
			<p>No activity this week</p>
			<small>Complete some training sessions to see your weekly summary</small>
		</div>
	</div>
{/if}

<style>
	.weekly-summary {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		border-radius: 20px;
		padding: 2rem;
		margin-bottom: 2rem;
		color: white;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
	}
	
	.weekly-summary.empty {
		background: white;
		color: #666;
	}
	
	.summary-header {
		text-align: center;
		margin-bottom: 2rem;
	}
	
	.summary-header h3 {
		margin: 0 0 0.5rem 0;
		font-size: 1.8rem;
		font-weight: 700;
	}
	
	.week-range {
		margin: 0;
		opacity: 0.9;
		font-size: 0.95rem;
	}
	
	.summary-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
		gap: 1rem;
		margin-bottom: 2rem;
	}
	
	.summary-card {
		background: rgba(255, 255, 255, 0.15);
		backdrop-filter: blur(10px);
		border-radius: 15px;
		padding: 1.5rem;
		display: flex;
		align-items: center;
		gap: 1rem;
		transition: all 0.3s;
		border: 1px solid rgba(255, 255, 255, 0.2);
	}
	
	.summary-card:hover {
		transform: translateY(-5px);
		background: rgba(255, 255, 255, 0.2);
		box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
	}
	
	.card-icon {
		font-size: 2.5rem;
		filter: drop-shadow(0 2px 5px rgba(0, 0, 0, 0.2));
	}
	
	.card-content {
		flex: 1;
	}
	
	.card-value {
		font-size: 2rem;
		font-weight: 700;
		line-height: 1;
		margin-bottom: 0.5rem;
	}
	
	.card-label {
		font-size: 0.85rem;
		opacity: 0.9;
		font-weight: 600;
	}
	
	.card-subtext {
		font-size: 0.75rem;
		opacity: 0.8;
		margin-top: 0.3rem;
	}
	
	.card-subtext.change {
		font-weight: 600;
	}
	
	.daily-activity {
		background: rgba(255, 255, 255, 0.1);
		border-radius: 15px;
		padding: 1.5rem;
		margin-bottom: 1.5rem;
	}
	
	.daily-activity h4 {
		margin: 0 0 1.5rem 0;
		font-size: 1.1rem;
		font-weight: 600;
	}
	
	.activity-bars {
		display: flex;
		justify-content: space-around;
		align-items: flex-end;
		height: 120px;
		gap: 0.5rem;
	}
	
	.day-bar {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}
	
	.bar-container {
		width: 100%;
		height: 100px;
		display: flex;
		align-items: flex-end;
		justify-content: center;
	}
	
	.bar {
		width: 100%;
		max-width: 40px;
		background: rgba(255, 255, 255, 0.3);
		border-radius: 8px 8px 0 0;
		position: relative;
		transition: all 0.3s;
		display: flex;
		align-items: flex-start;
		justify-content: center;
		padding-top: 0.3rem;
	}
	
	.bar.active {
		background: rgba(255, 255, 255, 0.9);
	}
	
	.bar-label {
		font-size: 0.75rem;
		font-weight: 700;
		color: #667eea;
	}
	
	.day-label {
		font-size: 0.8rem;
		font-weight: 600;
		opacity: 0.9;
	}
	
	.domains-section {
		background: rgba(255, 255, 255, 0.1);
		border-radius: 15px;
		padding: 1.5rem;
	}
	
	.domains-section h4 {
		margin: 0 0 1rem 0;
		font-size: 1.1rem;
		font-weight: 600;
	}
	
	.domain-tags {
		display: flex;
		flex-wrap: wrap;
		gap: 0.75rem;
	}
	
	.domain-tag {
		background: rgba(255, 255, 255, 0.2);
		padding: 0.5rem 1rem;
		border-radius: 20px;
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.9rem;
		font-weight: 600;
		border: 1px solid rgba(255, 255, 255, 0.3);
	}
	
	.tag-icon {
		font-size: 1.2rem;
	}
	
	.empty-state {
		text-align: center;
		padding: 3rem 2rem;
	}
	
	.empty-icon {
		font-size: 4rem;
		margin-bottom: 1rem;
		opacity: 0.5;
	}
	
	.empty-state p {
		margin: 0 0 0.5rem 0;
		font-size: 1.1rem;
		font-weight: 600;
		color: #666;
	}
	
	.empty-state small {
		font-size: 0.9rem;
		color: #999;
	}
	
	@media (max-width: 768px) {
		.weekly-summary {
			padding: 1.5rem;
		}
		
		.summary-grid {
			grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
			gap: 0.75rem;
		}
		
		.summary-card {
			padding: 1rem;
			flex-direction: column;
			text-align: center;
		}
		
		.card-icon {
			font-size: 2rem;
		}
		
		.card-value {
			font-size: 1.5rem;
		}
		
		.activity-bars {
			height: 100px;
		}
		
		.bar-container {
			height: 80px;
		}
	}
</style>

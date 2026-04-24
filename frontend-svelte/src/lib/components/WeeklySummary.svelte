<script>
	import { formatDate, formatNumber, formatPercent, locale as activeLocale, uiText } from '$lib/i18n';
	import { downloadCSV, downloadJSON } from '$lib/utils/chartDownload';
	import EmptyState from './EmptyState.svelte';
	
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
	
	function n(value, options = {}) {
		return formatNumber(value, $activeLocale, options);
	}

	function oneDecimal(value) {
		return n(value, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
	}

	function percent(value) {
		return formatPercent(value, $activeLocale, { maximumFractionDigits: 1 });
	}

	function getDayName(dateStr) {
		return formatDate(dateStr, $activeLocale, { weekday: 'short' });
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
	
	function handleDownloadSummary() {
		if (!summaryData) return;
		const filename = `weekly-summary-${new Date().toISOString().split('T')[0]}`;
		downloadJSON(summaryData, filename);
	}
	
	function handleDownloadCSV() {
		if (!summaryData) return;
		
		// Create CSV data from summary
		const csvData = [
			{
				period: `${new Date(summaryData.week_start).toLocaleDateString()} - ${new Date(summaryData.week_end).toLocaleDateString()}`,
				total_sessions: summaryData.total_sessions,
				active_days: summaryData.active_days,
				avg_score: summaryData.avg_score,
				avg_accuracy: summaryData.avg_accuracy,
				total_time_minutes: summaryData.total_time_minutes,
				current_streak: summaryData.current_streak
			}
		];
		
		const filename = `weekly-summary-${new Date().toISOString().split('T')[0]}`;
		downloadCSV(csvData, filename);
	}
</script>

{#if summaryData && summaryData.has_data}
	<div class="weekly-summary">
		<div class="summary-header">
			<div class="header-left">
				<h3>{uiText("📅 This Week's Summary", $activeLocale)}</h3>
				<p class="week-range">
					{formatDate(summaryData.week_start, $activeLocale)} - {formatDate(summaryData.week_end, $activeLocale)}
				</p>
			</div>
			<div class="header-actions">
				<button class="download-btn" on:click={handleDownloadCSV} title={uiText("Download summary as CSV", $activeLocale)}>
					{uiText("📋 CSV", $activeLocale)}
				</button>
				<button class="download-btn" on:click={handleDownloadSummary} title={uiText("Download summary as JSON", $activeLocale)}>
					{uiText("📊 JSON", $activeLocale)}
				</button>
			</div>
		</div>
		
		<div class="summary-grid">
			<!-- Total Sessions Card -->
			<div class="summary-card sessions">
				<div class="card-icon">🎯</div>
				<div class="card-content">
					<div class="card-value">{n(summaryData.total_sessions)}</div>
					<div class="card-label">{uiText("Sessions Completed", $activeLocale)}</div>
					<div class="card-subtext">{n(summaryData.active_days)}{uiText("/7 active days", $activeLocale)}</div>
				</div>
			</div>
			
			<!-- Average Score Card -->
			<div class="summary-card score">
				<div class="card-icon">⭐</div>
				<div class="card-content">
					<div class="card-value" style="color: {getScoreColor(summaryData.avg_score)}">
						{n(summaryData.avg_score)}
					</div>
					<div class="card-label">{uiText("Average Score", $activeLocale)}</div>
					{#if summaryData.score_change_from_last_week !== 0}
						<div class="card-subtext change">
							{getChangeIcon(summaryData.score_change_from_last_week)}
							{oneDecimal(Math.abs(summaryData.score_change_from_last_week))} {uiText("from last week", $activeLocale)}
						</div>
					{/if}
				</div>
			</div>
			
			<!-- Accuracy Card -->
			<div class="summary-card accuracy">
				<div class="card-icon">🎪</div>
				<div class="card-content">
					<div class="card-value">{percent(summaryData.avg_accuracy)}</div>
					<div class="card-label">{uiText("Average Accuracy", $activeLocale)}</div>
				</div>
			</div>
			
			<!-- Training Time Card -->
			<div class="summary-card time">
				<div class="card-icon">⏱️</div>
				<div class="card-content">
					<div class="card-value">{n(summaryData.total_time_minutes)} {uiText("min", $activeLocale)}</div>
					<div class="card-label">{uiText("Total Training Time", $activeLocale)}</div>
				</div>
			</div>
			
			<!-- Streak Card -->
			<div class="summary-card streak">
				<div class="card-icon">🔥</div>
				<div class="card-content">
					<div class="card-value">{n(summaryData.current_streak)}</div>
					<div class="card-label">{uiText("Current Streak", $activeLocale)}</div>
					<div class="card-subtext">{uiText("Keep it going!", $activeLocale)}</div>
				</div>
			</div>
			
			<!-- Most Improved Card -->
			{#if summaryData.most_improved}
				<div class="summary-card improved">
					<div class="card-icon">{domainIcons[summaryData.most_improved.domain]}</div>
					<div class="card-content">
						<div class="card-value">+{oneDecimal(summaryData.most_improved.improvement)}</div>
						<div class="card-label">{uiText("Most Improved", $activeLocale)}</div>
						<div class="card-subtext">{uiText(domainNames[summaryData.most_improved.domain], $activeLocale)}</div>
					</div>
				</div>
			{/if}
		</div>
		
		<!-- Daily Activity Chart -->
		<div class="daily-activity">
			<h4>{uiText("Daily Activity", $activeLocale)}</h4>
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
									<span class="bar-label">{n(count)}</span>
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
			<h4>{uiText("Domains Trained This Week", $activeLocale)}</h4>
			<div class="domain-tags">
				{#each summaryData.domains_trained as domain}
					<div class="domain-tag">
						<span class="tag-icon">{domainIcons[domain]}</span>
						<span class="tag-name">{uiText(domainNames[domain], $activeLocale)}</span>
					</div>
				{/each}
			</div>
		</div>
	</div>
{:else}
	<EmptyState 
		icon="📅"
		title={uiText("Build Your Weekly Streak", $activeLocale)}
		message={uiText("Train for 7 days to unlock your weekly summary with insights and progress tracking!", $activeLocale)}
		actionText={uiText("Start Training", $activeLocale)}
		actionLink="/training"
		tip={uiText("Training multiple days per week shows better cognitive improvements", $activeLocale)}
		variant="compact"
	/>
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
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
		flex-wrap: wrap;
		gap: 1rem;
	}
	
	.header-left {
		flex: 1;
		min-width: 200px;
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
	
	.header-actions {
		display: flex;
		gap: 0.5rem;
		align-items: center;
	}
	
	.download-btn {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		padding: 0.5rem 1rem;
		background: rgba(255, 255, 255, 0.25);
		backdrop-filter: blur(10px);
		color: white;
		border: 1px solid rgba(255, 255, 255, 0.3);
		border-radius: 8px;
		font-size: 0.85rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s;
	}
	
	.download-btn:hover {
		background: rgba(255, 255, 255, 0.35);
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
	}
	
	.download-btn:active {
		transform: translateY(0);
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

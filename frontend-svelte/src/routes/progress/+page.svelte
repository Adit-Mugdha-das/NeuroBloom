<script>
	import { goto } from '$app/navigation';
	import { training } from '$lib/api';
	import SimpleTrendChart from '$lib/components/SimpleTrendChart.svelte';
	import {
	  calculateBaselineDifficulty,
	  calculateOverallScore,
	  calculateTrendDelta,
	  formatPointChange,
	  getClinicalStatusLabel,
	  getClinicalStatusTone,
	  getDomainName,
	  getTrendLabel,
	  getTrendTone
	} from '$lib/progress';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let currentUser = null;
	let loading = true;
	let error = null;
	let metrics = null;
	let streakData = null;
	let trendsData = null;
	let weeklySummary = null;
	let comparisonData = null;

	user.subscribe((value) => {
		currentUser = value;
	});

	onMount(async () => {
		if (!currentUser) {
			goto('/login');
			return;
		}

		await loadOverview();
	});

	async function loadOverview() {
		loading = true;
		error = null;

		try {
			metrics = await training.getMetrics(currentUser.id);
			streakData = await training.getStreak(currentUser.id);
			trendsData = await training.getTrends(currentUser.id, 30);
			weeklySummary = await training.getWeeklySummary(currentUser.id);
			comparisonData = await training.getPerformanceComparison(currentUser.id);
		} catch (loadError) {
			console.error('Error loading progress overview:', loadError);
			error = 'Complete more training sessions to unlock your progress overview.';
		} finally {
			loading = false;
		}
	}

	$: overallScore = calculateOverallScore(metrics);
	$: trendDelta = calculateTrendDelta(trendsData);
	$: trendTone = getTrendTone(trendDelta);
	$: comparisonEntries = Object.entries(comparisonData?.comparison || {});
	$: baselineCards = comparisonEntries.map(([domain, values]) => ({
		domain,
		label: getDomainName(domain),
		status: getClinicalStatusLabel(values.improvement),
		tone: getClinicalStatusTone(values.improvement),
		pointChange: formatPointChange(values.improvement)
	}));
	$: difficultyEntries = comparisonEntries
		.map(([domain, values]) => {
			const baselineDifficulty = calculateBaselineDifficulty(values.baseline);
			const currentDifficulty = metrics?.current_difficulty?.[domain] ?? baselineDifficulty;
			const delta = currentDifficulty - baselineDifficulty;

			return {
				domain,
				label: getDomainName(domain),
				baselineDifficulty,
				currentDifficulty,
				delta
			};
		})
		.filter((entry) => entry.delta !== 0)
		.sort((left, right) => Math.abs(right.delta) - Math.abs(left.delta));
</script>

<div class="progress-panel">
	{#if loading}
		<section class="state-panel glass-card">
			<p>Loading progress overview...</p>
		</section>
	{:else if error}
		<section class="state-panel glass-card">
			<h2>Progress overview unavailable</h2>
			<p>{error}</p>
			<a class="action-link" href="/training">Start Training</a>
		</section>
	{:else}
		<div class="overview-stack">
			<section class="summary-grid">
				<article class="glass-card stat-card compact-card">
					<p class="card-label">Weekly Summary</p>
					<h2>{weeklySummary?.total_sessions || 0} sessions</h2>
					<p class="card-copy">{weeklySummary?.active_days || 0} active days and {weeklySummary?.total_time_minutes || 0} minutes this week.</p>
				</article>

				<article class="glass-card stat-card compact-card">
					<p class="card-label">Overall Score</p>
					<h2>{overallScore}</h2>
					<p class="card-copy">A simplified average across your active cognitive domains.</p>
				</article>

				<article class="glass-card stat-card compact-card">
					<p class="card-label">Training Streak</p>
					<h2>{streakData?.current_streak || 0} days</h2>
					<p class="card-copy">Longest streak: {streakData?.longest_streak || 0} days.</p>
				</article>

				<article class="glass-card trend-card compact-card {trendTone}">
					<div class="trend-head">
						<div>
							<p class="card-label">Trend</p>
							<h2>{getTrendLabel(trendDelta)}</h2>
						</div>
						<p class="trend-delta">{trendDelta > 0 ? '+' : ''}{trendDelta}</p>
					</div>
					<SimpleTrendChart points={trendsData?.overall_trend || []} />
				</article>
			</section>

			<section class="detail-grid">
				<article class="glass-card detail-card">
					<div class="detail-head">
						<div>
							<p class="card-label">Improvement Since Baseline</p>
							<h2>Cognitive improvement since baseline</h2>
						</div>
					</div>

					<div class="comparison-list">
						{#each baselineCards as card}
							<div class="comparison-row {card.tone}">
								<div>
									<p class="comparison-domain">{card.label}</p>
									<p class="comparison-change">{card.pointChange}</p>
								</div>
								<p class="comparison-status {card.tone}">{card.status}</p>
							</div>
						{/each}
					</div>
				</article>

				<article class="glass-card detail-card">
					<div class="detail-head">
						<div>
							<p class="card-label">Difficulty Progress</p>
							<h2>Training challenge since baseline</h2>
						</div>
					</div>

					{#if difficultyEntries.length > 0}
						<div class="difficulty-list">
							{#each difficultyEntries.slice(0, 4) as entry}
								<div class="difficulty-row">
									<p class="difficulty-domain">{entry.label}</p>
									<p class="difficulty-copy">Your training difficulty {entry.delta > 0 ? 'increased' : 'decreased'} by {Math.abs(entry.delta)} level{Math.abs(entry.delta) === 1 ? '' : 's'} since baseline.</p>
								</div>
							{/each}
						</div>
					{:else}
						<p class="card-copy">Your training difficulty is stable so far. As you complete more sessions, this section will update automatically.</p>
					{/if}
				</article>
			</section>
		</div>
	{/if}
</div>

<style>
	.progress-panel {
		display: grid;
	}

	.overview-stack {
		display: grid;
		gap: 1rem;
	}

	.summary-grid {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 1rem;
	}

	.detail-grid {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 1rem;
	}

	.glass-card,
	.state-panel {
		background: rgba(248, 250, 252, 0.84);
		backdrop-filter: blur(10px);
		border: 1px solid rgba(255, 255, 255, 0.72);
		border-radius: 22px;
		padding: 1.25rem;
		box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
	}

	.state-panel {
		text-align: center;
	}

	.card-label {
		margin: 0;
		font-size: 0.78rem;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		font-weight: 800;
		color: #4f46e5;
	}

	.stat-card h2,
	.trend-card h2,
	.state-panel h2 {
		margin: 0.25rem 0 0.45rem;
		font-size: 1.7rem;
		color: #111827;
	}

	.card-copy,
	.state-panel p {
		margin: 0;
		line-height: 1.55;
		color: #64748b;
	}

	.compact-card {
		min-height: 100%;
	}

	.detail-card {
		display: grid;
		gap: 1rem;
	}

	.detail-head h2 {
		margin: 0.25rem 0 0;
		font-size: 1.25rem;
		color: #111827;
	}

	.comparison-list,
	.difficulty-list {
		display: grid;
		gap: 0.75rem;
	}

	.comparison-row,
	.difficulty-row {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: flex-start;
		padding: 0.9rem 1rem;
		border-radius: 16px;
		background: rgba(255, 255, 255, 0.68);
		border: 1px solid rgba(255, 255, 255, 0.82);
	}

	.comparison-domain,
	.difficulty-domain {
		margin: 0;
		font-weight: 700;
		color: #111827;
	}

	.comparison-change,
	.difficulty-copy {
		margin: 0.25rem 0 0;
		color: #64748b;
		line-height: 1.5;
		font-size: 0.9rem;
	}

	.comparison-status {
		margin: 0;
		padding: 0.42rem 0.78rem;
		border-radius: 999px;
		font-size: 0.78rem;
		font-weight: 800;
		white-space: nowrap;
	}

	.comparison-row.improving {
		box-shadow: inset 0 0 0 1px rgba(34, 197, 94, 0.1);
	}

	.comparison-row.stable {
		box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.12);
	}

	.comparison-row.attention {
		box-shadow: inset 0 0 0 1px rgba(245, 158, 11, 0.14);
	}

	.comparison-status.improving {
		background: rgba(34, 197, 94, 0.14);
		color: #15803d;
	}

	.comparison-status.stable {
		background: rgba(148, 163, 184, 0.14);
		color: #475569;
	}

	.comparison-status.attention {
		background: rgba(245, 158, 11, 0.16);
		color: #b45309;
	}

	.trend-head {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: flex-start;
		margin-bottom: 0.6rem;
	}

	.trend-delta {
		margin: 0;
		font-size: 1.15rem;
		font-weight: 800;
	}

	.trend-card.positive .trend-delta {
		color: #15803d;
	}

	.trend-card.negative .trend-delta {
		color: #b91c1c;
	}

	.trend-card.neutral .trend-delta {
		color: #475569;
	}

	.action-link {
		display: inline-block;
		margin-top: 1rem;
		padding: 0.8rem 1.1rem;
		border-radius: 999px;
		background: linear-gradient(135deg, #4f46e5, #6366f1);
		color: #fff;
		text-decoration: none;
		font-weight: 700;
	}

	@media (max-width: 860px) {
		.summary-grid,
		.detail-grid {
			grid-template-columns: 1fr;
		}

		.comparison-row,
		.difficulty-row {
			flex-direction: column;
		}
	}
</style>
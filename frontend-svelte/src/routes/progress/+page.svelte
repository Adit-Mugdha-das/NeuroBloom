<script>
	import { goto } from '$app/navigation';
	import { training } from '$lib/api';
	import SimpleTrendChart from '$lib/components/SimpleTrendChart.svelte';
	import { calculateOverallScore, calculateTrendDelta, getTrendLabel, getTrendTone } from '$lib/progress';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let currentUser = null;
	let loading = true;
	let error = null;
	let metrics = null;
	let streakData = null;
	let trendsData = null;
	let weeklySummary = null;

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
		<section class="overview-grid">
			<article class="glass-card stat-card">
				<p class="card-label">Weekly Summary</p>
				<h2>{weeklySummary?.total_sessions || 0} sessions</h2>
				<p class="card-copy">{weeklySummary?.active_days || 0} active days this week and {weeklySummary?.total_time_minutes || 0} training minutes.</p>
			</article>

			<article class="glass-card stat-card">
				<p class="card-label">Overall Score</p>
				<h2>{overallScore}</h2>
				<p class="card-copy">A simplified average across your active cognitive domains.</p>
			</article>

			<article class="glass-card stat-card">
				<p class="card-label">Training Streak</p>
				<h2>{streakData?.current_streak || 0} days</h2>
				<p class="card-copy">Longest streak: {streakData?.longest_streak || 0} days.</p>
			</article>

			<article class="glass-card trend-card {trendTone}">
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
	{/if}
</div>

<style>
	.progress-panel {
		display: grid;
	}

	.overview-grid {
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
		.overview-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
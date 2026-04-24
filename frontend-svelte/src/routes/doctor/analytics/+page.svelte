<script>
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	import DoctorWorkspaceShell from '$lib/components/DoctorWorkspaceShell.svelte';
	import { user } from '$lib/stores.js';
	import { onMount } from 'svelte';

	let analytics = null;
	let domainAnalytics = null;
	let cohortTrends = null;
	let loading = true;
	let error = '';
	let userData;

	const unsubscribe = user.subscribe((value) => {
		userData = value;
	});

	onMount(() => {
		if (!userData || userData.role !== 'doctor') {
			goto('/login');
			return;
		}

		loadAnalytics();

		return unsubscribe;
	});

	async function loadAnalytics() {
		loading = true;
		error = '';

		try {
			const [analyticsResp, domainsResp, trendsResp] = await Promise.all([
				api.get(`/api/doctor/${userData.id}/analytics`),
				api.get(`/api/doctor/${userData.id}/analytics/domains`),
				api.get(`/api/doctor/${userData.id}/analytics/trends?days=30`)
			]);

			analytics = analyticsResp.data;
			domainAnalytics = domainsResp.data;
			cohortTrends = trendsResp.data;
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Failed to load doctor analytics';
		} finally {
			loading = false;
		}
	}

	function formatDomainName(domain) {
		return domain
			.split('_')
			.map((word) => word.charAt(0).toUpperCase() + word.slice(1))
			.join(' ');
	}

	$: lifetimeMetrics = analytics
		? [
				{ label: 'Cohort Avg Score', value: analytics.success_metrics.avg_session_score, timeframe: 'All time' },
				{ label: 'Cohort Avg Accuracy', value: `${analytics.success_metrics.avg_session_accuracy}%`, timeframe: 'All time' },
				{ label: 'Total Sessions', value: analytics.success_metrics.total_sessions_completed, timeframe: 'All time' },
				{ label: 'Baseline Completion', value: `${analytics.overview.baseline_completion_rate}%`, timeframe: 'Current cohort' }
			]
		: [];

	$: recentMetrics = analytics
		? [
				{ label: 'Overall Adherence', value: `${analytics.adherence.overall_adherence_rate}%`, timeframe: 'Last 30 days' },
				{ label: 'Avg Sessions / Week', value: cohortTrends?.summary?.avg_sessions_per_week ?? 0, timeframe: 'Last 30 days' },
				{ label: 'Recent Avg Score', value: cohortTrends?.summary?.overall_avg_score ?? 0, timeframe: 'Last 30 days' },
				{ label: 'Active Patients', value: analytics.overview.active_patients, timeframe: 'Last 7 days' }
			]
		: [];

	$: longitudinalMetrics = analytics
		? [
				{ label: 'Avg Improvement', value: `${analytics.success_metrics.avg_improvement > 0 ? '+' : ''}${analytics.success_metrics.avg_improvement}`, timeframe: 'First 5 vs last 5 sessions' },
				{ label: 'Patients Improving', value: analytics.success_metrics.patients_improving, timeframe: 'Enough sessions only' },
				{ label: 'Patients Declining', value: analytics.success_metrics.patients_declining, timeframe: 'Enough sessions only' },
				{ label: 'Assigned Patients', value: analytics.overview.total_patients, timeframe: 'Current cohort' }
			]
		: [];
</script>

<DoctorWorkspaceShell
	title="Analytics"
	subtitle="Clinician analytics organized by timeframe so current monitoring, lifetime summary, and longitudinal signals are clearly separated."
>
	{#if loading}
		<section class="state-card">
			<p>Loading analytics...</p>
		</section>
	{:else if error}
		<section class="state-card error-state">
			<p>{error}</p>
		</section>
	{:else}
		<section class="orientation-card">
			<div>
				<p class="panel-kicker">How To Read This Page</p>
				<h2>Metrics are grouped by timeframe</h2>
				<p class="empty-copy">Recent monitoring uses the last 30 days unless noted. Lifetime summary uses all completed sessions. Longitudinal trends compare earlier versus more recent performance for patients with enough session history.</p>
			</div>
			<div class="legend-grid">
				<div class="legend-pill recent">Recent monitoring</div>
				<div class="legend-pill lifetime">Lifetime summary</div>
				<div class="legend-pill longitudinal">Longitudinal trends</div>
			</div>
		</section>

		<section class="section-block">
			<div class="section-header-block">
				<p class="panel-kicker">Recent Monitoring</p>
				<h2>Use these metrics for current engagement and short-term activity</h2>
			</div>

			<section class="metrics-grid">
				{#each recentMetrics as metric}
					<article class="metric-card metric-card-recent">
						<p>{metric.label}</p>
						<strong>{metric.value}</strong>
						<span class="timeframe-badge recent">{metric.timeframe}</span>
					</article>
				{/each}
			</section>

			<section class="panel-grid">
				<article class="panel-card">
					<div class="panel-heading">
						<div>
							<p class="panel-kicker">Adherence</p>
							<h2>Cohort Adherence Breakdown</h2>
						</div>
						<div class="heading-stack">
							<span class="timeframe-badge recent">Last 30 days</span>
							<span class="big-value">{analytics.adherence.overall_adherence_rate}%</span>
						</div>
					</div>
					<div class="breakdown-list">
						<div><span>Excellent</span><strong>{analytics.adherence.adherence_breakdown.excellent}</strong></div>
						<div><span>Good</span><strong>{analytics.adherence.adherence_breakdown.good}</strong></div>
						<div><span>Fair</span><strong>{analytics.adherence.adherence_breakdown.fair}</strong></div>
						<div><span>Poor</span><strong>{analytics.adherence.adherence_breakdown.poor}</strong></div>
					</div>
				</article>

				<article class="panel-card">
					<div class="panel-heading">
						<div>
							<p class="panel-kicker">Activity</p>
							<h2>Cohort Activity Summary</h2>
						</div>
						<div class="heading-stack">
							<span class="timeframe-badge recent">Last 30 days</span>
						</div>
					</div>
					<div class="breakdown-list">
						<div><span>Average Sessions / Week</span><strong>{cohortTrends?.summary?.avg_sessions_per_week ?? 0}</strong></div>
						<div><span>Overall Average Score</span><strong>{cohortTrends?.summary?.overall_avg_score ?? 0}</strong></div>
						<div><span>Weeks Tracked</span><strong>{cohortTrends?.summary?.weeks_tracked ?? 0}</strong></div>
						<div><span>Active Patients</span><strong>{analytics.overview.active_patients}</strong></div>
					</div>
				</article>
			</section>
		</section>

		<section class="section-block">
			<div class="section-header-block">
				<p class="panel-kicker">Lifetime Summary</p>
				<h2>These metrics use all completed sessions for the currently assigned cohort</h2>
			</div>

			<section class="metrics-grid">
				{#each lifetimeMetrics as metric}
					<article class="metric-card metric-card-lifetime">
						<p>{metric.label}</p>
						<strong>{metric.value}</strong>
						<span class="timeframe-badge lifetime">{metric.timeframe}</span>
					</article>
				{/each}
			</section>

			<section class="panel-card">
				<div class="panel-heading">
					<div>
						<p class="panel-kicker">Domains</p>
						<h2>Domain Performance Overview</h2>
					</div>
					<div class="heading-stack">
						<span class="timeframe-badge lifetime">All completed sessions</span>
					</div>
				</div>
				<div class="domain-grid">
					{#each Object.entries(domainAnalytics.domains || {}) as [domain, stats]}
						<article class="domain-card">
							<h3>{formatDomainName(domain)}</h3>
							<div class="domain-stats">
								<div><span>Sessions</span><strong>{stats.sessions_count}</strong></div>
								<div><span>Patients</span><strong>{stats.patients_count}</strong></div>
								<div><span>Average Score</span><strong>{stats.avg_score}</strong></div>
								<div><span>Average Accuracy</span><strong>{stats.avg_accuracy}%</strong></div>
								<div><span>Average Reaction Time</span><strong>{stats.avg_reaction_time} ms</strong></div>
								<div><span>Score Range</span><strong>{stats.score_range.min} - {stats.score_range.max}</strong></div>
							</div>
						</article>
					{/each}
				</div>
			</section>
		</section>

		<section class="section-block">
			<div class="section-header-block">
				<p class="panel-kicker">Longitudinal Trends</p>
				<h2>These values compare earlier sessions with more recent sessions</h2>
			</div>

			<section class="metrics-grid">
				{#each longitudinalMetrics as metric}
					<article class="metric-card metric-card-longitudinal">
						<p>{metric.label}</p>
						<strong>{metric.value}</strong>
						<span class="timeframe-badge longitudinal">{metric.timeframe}</span>
					</article>
				{/each}
			</section>

			<section class="panel-card">
				<div class="panel-heading">
					<div>
						<p class="panel-kicker">Method</p>
						<h2>How improvement is calculated</h2>
					</div>
					<div class="heading-stack">
						<span class="timeframe-badge longitudinal">Interpret carefully</span>
					</div>
				</div>
				<p class="empty-copy">Improvement compares the first 5 recorded scores with the last 5 recorded scores for patients who have enough completed sessions. It is a longitudinal signal, not a short-term monitoring metric.</p>
			</section>
		</section>

		<section class="panel-card">
			<div class="panel-heading">
				<div>
					<p class="panel-kicker">Activity</p>
					<h2>Cohort Activity Trends</h2>
				</div>
				<div class="heading-stack">
					<span class="timeframe-badge recent">Last 30 days</span>
				</div>
			</div>
			{#if cohortTrends?.trends?.length}
				<div class="trend-summary">
					<div><span>Average Sessions / Week</span><strong>{cohortTrends.summary.avg_sessions_per_week}</strong></div>
					<div><span>Overall Average Score</span><strong>{cohortTrends.summary.overall_avg_score}</strong></div>
				</div>
				<div class="trend-list">
					{#each cohortTrends.trends as week}
						<div class="trend-row">
							<div class="trend-date">{new Date(week.week_starting).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })}</div>
							<div class="trend-bars">
								<div class="trend-bar sessions" style={`width: ${(week.sessions / cohortTrends.summary.total_sessions) * 400}%`}></div>
							</div>
							<div class="trend-copy">
								<span>{week.sessions} sessions</span>
								<span>{week.active_patients} patients</span>
								<span>Avg {week.avg_score}</span>
							</div>
						</div>
					{/each}
				</div>
			{:else}
				<p class="empty-copy">No recent cohort activity was found for the selected period.</p>
			{/if}
		</section>
	{/if}
</DoctorWorkspaceShell>

<style>
	.metrics-grid,
	.panel-grid,
	.domain-grid,
	.legend-grid {
		display: grid;
		gap: 1rem;
	}

	.metrics-grid {
		grid-template-columns: repeat(4, minmax(0, 1fr));
	}

	.panel-grid {
		grid-template-columns: repeat(2, minmax(0, 1fr));
	}

	.legend-grid {
		grid-template-columns: repeat(3, minmax(0, 1fr));
		align-self: start;
	}

	.metric-card,
	.panel-card,
	.domain-card,
	.state-card,
	.orientation-card {
		background: #f8fafc;
		border: 1px solid #e2e8f0;
		border-radius: 24px;
		padding: 1.2rem;
		box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
	}

	.metric-card p,
	.panel-kicker {
		margin: 0;
		font-size: 0.78rem;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: #6b7280;
	}

	.metric-card strong,
	.big-value {
		display: block;
		margin-top: 0.4rem;
		font-size: 1.9rem;
		font-weight: 800;
		color: #111827;
	}

	.panel-heading {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: flex-start;
		margin-bottom: 1rem;
	}

	h2,
	h3 {
		margin: 0.2rem 0 0;
		color: #111827;
	}

	.section-block {
		display: grid;
		gap: 1rem;
	}

	.section-header-block {
		display: grid;
		gap: 0.2rem;
	}

	.orientation-card {
		display: grid;
		grid-template-columns: 1.25fr 0.75fr;
		gap: 1rem;
	}

	.legend-pill,
	.timeframe-badge {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 0.35rem 0.8rem;
		border-radius: 999px;
		font-size: 0.78rem;
		font-weight: 800;
	}

	.metric-card-recent {
		background: linear-gradient(180deg, #ffffff 0%, #eef2ff 100%);
	}

	.metric-card-lifetime {
		background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
	}

	.metric-card-longitudinal {
		background: linear-gradient(180deg, #ffffff 0%, #ecfeff 100%);
	}

	.legend-pill.recent,
	.timeframe-badge.recent {
		color: #4f46e5;
		border: 1px solid #c7d2fe;
		background: #eef2ff;
	}

	.legend-pill.lifetime,
	.timeframe-badge.lifetime {
		color: #475569;
		border: 1px solid #cbd5e1;
		background: #f8fafc;
	}

	.legend-pill.longitudinal,
	.timeframe-badge.longitudinal {
		color: #0f766e;
		border: 1px solid #99f6e4;
		background: #ecfeff;
	}

	.heading-stack {
		display: grid;
		gap: 0.5rem;
		justify-items: end;
	}

	.breakdown-list,
	.domain-stats,
	.trend-summary {
		display: grid;
		gap: 0.8rem;
	}

	.breakdown-list div,
	.domain-stats div,
	.trend-summary div {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		padding: 0.8rem 0;
		border-top: 1px solid #eef2f7;
	}

	.breakdown-list div:first-child,
	.domain-stats div:first-child,
	.trend-summary div:first-child {
		border-top: none;
		padding-top: 0;
	}

	.breakdown-list span,
	.domain-stats span,
	.trend-summary span,
	.empty-copy,
	.state-card p,
	.trend-copy {
		color: #6b7280;
	}

	.breakdown-list strong,
	.domain-stats strong,
	.trend-summary strong {
		color: #111827;
	}

	.domain-grid {
		grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
	}

	.trend-list {
		display: grid;
		gap: 0.8rem;
		margin-top: 1rem;
	}

	.trend-row {
		display: grid;
		grid-template-columns: 90px minmax(0, 1fr) 220px;
		gap: 0.9rem;
		align-items: center;
	}

	.trend-date {
		font-weight: 700;
		color: #111827;
	}

	.trend-bars {
		height: 12px;
		border-radius: 999px;
		background: #eef2ff;
		overflow: hidden;
	}

	.trend-bar.sessions {
		height: 100%;
		border-radius: 999px;
		background: linear-gradient(90deg, #4f46e5 0%, #818cf8 100%);
	}

	.trend-copy {
		display: flex;
		justify-content: space-between;
		gap: 0.75rem;
		font-size: 0.92rem;
	}

	@media (max-width: 1024px) {
		.metrics-grid,
		.panel-grid,
		.legend-grid {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}

		.orientation-card {
			grid-template-columns: 1fr;
		}

		.trend-row {
			grid-template-columns: 1fr;
		}
	}

	@media (max-width: 760px) {
		.metrics-grid,
		.panel-grid,
		.legend-grid {
			grid-template-columns: 1fr;
		}

		.panel-heading {
			flex-direction: column;
		}

		.heading-stack {
			justify-items: start;
		}
	}
</style>
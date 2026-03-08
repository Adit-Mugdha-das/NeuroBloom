<script>
	import DoctorWorkspaceShell from '$lib/components/DoctorWorkspaceShell.svelte';
	import api from '$lib/api.js';
	import { goto } from '$app/navigation';
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
</script>

<DoctorWorkspaceShell
	title="Analytics"
	subtitle="Detailed cohort, domain, and activity analysis moved off the dashboard to keep clinician workflow focused."
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
		<section class="metrics-grid">
			<article class="metric-card">
				<p>Cohort Avg Score</p>
				<strong>{analytics.success_metrics.avg_session_score}</strong>
			</article>
			<article class="metric-card">
				<p>Cohort Avg Accuracy</p>
				<strong>{analytics.success_metrics.avg_session_accuracy}%</strong>
			</article>
			<article class="metric-card">
				<p>Avg Improvement</p>
				<strong>{analytics.success_metrics.avg_improvement > 0 ? '+' : ''}{analytics.success_metrics.avg_improvement}</strong>
			</article>
			<article class="metric-card">
				<p>Total Sessions</p>
				<strong>{analytics.success_metrics.total_sessions_completed}</strong>
			</article>
		</section>

		<section class="panel-grid">
			<article class="panel-card">
				<div class="panel-heading">
					<div>
						<p class="panel-kicker">Adherence</p>
						<h2>Cohort Adherence Breakdown</h2>
					</div>
					<span class="big-value">{analytics.adherence.overall_adherence_rate}%</span>
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
						<p class="panel-kicker">Performance</p>
						<h2>Improvement Snapshot</h2>
					</div>
				</div>
				<div class="breakdown-list">
					<div><span>Patients Improving</span><strong>{analytics.success_metrics.patients_improving}</strong></div>
					<div><span>Patients Declining</span><strong>{analytics.success_metrics.patients_declining}</strong></div>
					<div><span>Active Patients</span><strong>{analytics.overview.active_patients}</strong></div>
					<div><span>Baseline Completion</span><strong>{analytics.overview.baseline_completion_rate}%</strong></div>
				</div>
			</article>
		</section>

		<section class="panel-card">
			<div class="panel-heading">
				<div>
					<p class="panel-kicker">Domains</p>
					<h2>Domain Performance Overview</h2>
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

		<section class="panel-card">
			<div class="panel-heading">
				<div>
					<p class="panel-kicker">Activity</p>
					<h2>Cohort Activity Trends</h2>
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
	.domain-grid {
		display: grid;
		gap: 1rem;
	}

	.metrics-grid {
		grid-template-columns: repeat(4, minmax(0, 1fr));
	}

	.panel-grid {
		grid-template-columns: repeat(2, minmax(0, 1fr));
	}

	.metric-card,
	.panel-card,
	.domain-card,
	.state-card {
		background: #ffffff;
		border: 1px solid #e5e7eb;
		border-radius: 24px;
		padding: 1.2rem;
		box-shadow: 0 16px 30px rgba(15, 23, 42, 0.05);
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
		.panel-grid {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}

		.trend-row {
			grid-template-columns: 1fr;
		}
	}

	@media (max-width: 760px) {
		.metrics-grid,
		.panel-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
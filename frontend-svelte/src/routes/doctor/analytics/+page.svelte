<script>
	import { formatDate, formatNumber, formatPercent, locale as activeLocale, uiText } from '$lib/i18n';
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
		const label = domain
			.split('_')
			.map((word) => word.charAt(0).toUpperCase() + word.slice(1))
			.join(' ');
		return uiText(label, $activeLocale);
	}

	function n(value, options = {}) {
		return formatNumber(value, $activeLocale, options);
	}

	function oneDecimal(value) {
		return n(value, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
	}

	function pct(value) {
		return formatPercent(value, $activeLocale, { maximumFractionDigits: 1 });
	}

	function compactDate(value) {
		return formatDate(value, $activeLocale, { day: '2-digit', month: 'short' });
	}

	$: lifetimeMetrics = analytics
		? [
				{ label: 'Cohort Avg Score', value: oneDecimal(analytics.success_metrics.avg_session_score), timeframe: 'All time' },
				{ label: 'Cohort Avg Accuracy', value: pct(analytics.success_metrics.avg_session_accuracy), timeframe: 'All time' },
				{ label: 'Total Sessions', value: n(analytics.success_metrics.total_sessions_completed), timeframe: 'All time' },
				{ label: 'Baseline Completion', value: pct(analytics.overview.baseline_completion_rate), timeframe: 'Current cohort' }
			]
		: [];

	$: recentMetrics = analytics
		? [
				{ label: 'Overall Adherence', value: pct(analytics.adherence.overall_adherence_rate), timeframe: 'Last 30 days' },
				{ label: 'Avg Sessions / Week', value: oneDecimal(cohortTrends?.summary?.avg_sessions_per_week ?? 0), timeframe: 'Last 30 days' },
				{ label: 'Recent Avg Score', value: oneDecimal(cohortTrends?.summary?.overall_avg_score ?? 0), timeframe: 'Last 30 days' },
				{ label: 'Active Patients', value: n(analytics.overview.active_patients), timeframe: 'Last 7 days' }
			]
		: [];

	$: longitudinalMetrics = analytics
		? [
				{ label: 'Avg Improvement', value: `${analytics.success_metrics.avg_improvement > 0 ? '+' : ''}${oneDecimal(analytics.success_metrics.avg_improvement)}`, timeframe: 'First 5 vs last 5 sessions' },
				{ label: 'Patients Improving', value: n(analytics.success_metrics.patients_improving), timeframe: 'Enough sessions only' },
				{ label: 'Patients Declining', value: n(analytics.success_metrics.patients_declining), timeframe: 'Enough sessions only' },
				{ label: 'Assigned Patients', value: n(analytics.overview.total_patients), timeframe: 'Current cohort' }
			]
		: [];
</script>

<DoctorWorkspaceShell
	title={uiText("Analytics", $activeLocale)}
	subtitle={uiText("Clinician analytics organized by timeframe so current monitoring, lifetime summary, and longitudinal signals are clearly separated.", $activeLocale)}
>
	{#if loading}
		<section class="state-card">
			<p>{uiText("Loading analytics...", $activeLocale)}</p>
		</section>
	{:else if error}
		<section class="state-card error-state">
			<p>{error}</p>
		</section>
	{:else}
		<section class="orientation-card">
			<div>
				<p class="panel-kicker">{uiText("How To Read This Page", $activeLocale)}</p>
				<h2>{uiText("Metrics are grouped by timeframe", $activeLocale)}</h2>
				<p class="empty-copy">{uiText("Recent monitoring uses the last 30 days unless noted. Lifetime summary uses all completed sessions. Longitudinal trends compare earlier versus more recent performance for patients with enough session history.", $activeLocale)}</p>
			</div>
			<div class="legend-grid">
				<div class="legend-pill recent">{uiText("Recent monitoring", $activeLocale)}</div>
				<div class="legend-pill lifetime">{uiText("Lifetime summary", $activeLocale)}</div>
				<div class="legend-pill longitudinal">{uiText("Longitudinal trends", $activeLocale)}</div>
			</div>
		</section>

		<section class="section-block">
			<div class="section-header-block">
				<p class="panel-kicker">{uiText("Recent Monitoring", $activeLocale)}</p>
				<h2>{uiText("Use these metrics for current engagement and short-term activity", $activeLocale)}</h2>
			</div>

			<section class="metrics-grid">
				{#each recentMetrics as metric}
					<article class="metric-card metric-card-recent">
						<p>{uiText(metric.label, $activeLocale)}</p>
						<strong>{metric.value}</strong>
						<span class="timeframe-badge recent">{uiText(metric.timeframe, $activeLocale)}</span>
					</article>
				{/each}
			</section>

			<section class="panel-grid">
				<article class="panel-card">
					<div class="panel-heading">
						<div>
							<p class="panel-kicker">{uiText("Adherence", $activeLocale)}</p>
							<h2>{uiText("Cohort Adherence Breakdown", $activeLocale)}</h2>
						</div>
						<div class="heading-stack">
							<span class="timeframe-badge recent">{uiText("Last 30 days", $activeLocale)}</span>
							<span class="big-value">{pct(analytics.adherence.overall_adherence_rate)}</span>
						</div>
					</div>
					<div class="breakdown-list">
						<div><span>{uiText("Excellent", $activeLocale)}</span><strong>{n(analytics.adherence.adherence_breakdown.excellent)}</strong></div>
						<div><span>{uiText("Good", $activeLocale)}</span><strong>{n(analytics.adherence.adherence_breakdown.good)}</strong></div>
						<div><span>{uiText("Fair", $activeLocale)}</span><strong>{n(analytics.adherence.adherence_breakdown.fair)}</strong></div>
						<div><span>{uiText("Poor", $activeLocale)}</span><strong>{n(analytics.adherence.adherence_breakdown.poor)}</strong></div>
					</div>
				</article>

				<article class="panel-card">
					<div class="panel-heading">
						<div>
							<p class="panel-kicker">{uiText("Activity", $activeLocale)}</p>
							<h2>{uiText("Cohort Activity Summary", $activeLocale)}</h2>
						</div>
						<div class="heading-stack">
							<span class="timeframe-badge recent">{uiText("Last 30 days", $activeLocale)}</span>
						</div>
					</div>
					<div class="breakdown-list">
						<div><span>{uiText("Average Sessions / Week", $activeLocale)}</span><strong>{oneDecimal(cohortTrends?.summary?.avg_sessions_per_week ?? 0)}</strong></div>
						<div><span>{uiText("Overall Average Score", $activeLocale)}</span><strong>{oneDecimal(cohortTrends?.summary?.overall_avg_score ?? 0)}</strong></div>
						<div><span>{uiText("Weeks Tracked", $activeLocale)}</span><strong>{n(cohortTrends?.summary?.weeks_tracked ?? 0)}</strong></div>
						<div><span>{uiText("Active Patients", $activeLocale)}</span><strong>{n(analytics.overview.active_patients)}</strong></div>
					</div>
				</article>
			</section>
		</section>

		<section class="section-block">
			<div class="section-header-block">
				<p class="panel-kicker">{uiText("Lifetime Summary", $activeLocale)}</p>
				<h2>{uiText("These metrics use all completed sessions for the currently assigned cohort", $activeLocale)}</h2>
			</div>

			<section class="metrics-grid">
				{#each lifetimeMetrics as metric}
					<article class="metric-card metric-card-lifetime">
						<p>{uiText(metric.label, $activeLocale)}</p>
						<strong>{metric.value}</strong>
						<span class="timeframe-badge lifetime">{uiText(metric.timeframe, $activeLocale)}</span>
					</article>
				{/each}
			</section>

			<section class="panel-card">
				<div class="panel-heading">
					<div>
						<p class="panel-kicker">{uiText("Domains", $activeLocale)}</p>
						<h2>{uiText("Domain Performance Overview", $activeLocale)}</h2>
					</div>
					<div class="heading-stack">
						<span class="timeframe-badge lifetime">{uiText("All completed sessions", $activeLocale)}</span>
					</div>
				</div>
				<div class="domain-grid">
					{#each Object.entries(domainAnalytics.domains || {}) as [domain, stats]}
						<article class="domain-card">
							<h3>{formatDomainName(domain)}</h3>
							<div class="domain-stats">
								<div><span>{uiText("Sessions", $activeLocale)}</span><strong>{n(stats.sessions_count)}</strong></div>
								<div><span>{uiText("Patients", $activeLocale)}</span><strong>{n(stats.patients_count)}</strong></div>
								<div><span>{uiText("Average Score", $activeLocale)}</span><strong>{oneDecimal(stats.avg_score)}</strong></div>
								<div><span>{uiText("Average Accuracy", $activeLocale)}</span><strong>{pct(stats.avg_accuracy)}</strong></div>
								<div><span>{uiText("Average Reaction Time", $activeLocale)}</span><strong>{n(stats.avg_reaction_time)} ms</strong></div>
								<div><span>{uiText("Score Range", $activeLocale)}</span><strong>{n(stats.score_range.min)} - {n(stats.score_range.max)}</strong></div>
							</div>
						</article>
					{/each}
				</div>
			</section>
		</section>

		<section class="section-block">
			<div class="section-header-block">
				<p class="panel-kicker">{uiText("Longitudinal Trends", $activeLocale)}</p>
				<h2>{uiText("These values compare earlier sessions with more recent sessions", $activeLocale)}</h2>
			</div>

			<section class="metrics-grid">
				{#each longitudinalMetrics as metric}
					<article class="metric-card metric-card-longitudinal">
						<p>{uiText(metric.label, $activeLocale)}</p>
						<strong>{metric.value}</strong>
						<span class="timeframe-badge longitudinal">{uiText(metric.timeframe, $activeLocale)}</span>
					</article>
				{/each}
			</section>

			<section class="panel-card">
				<div class="panel-heading">
					<div>
						<p class="panel-kicker">{uiText("Method", $activeLocale)}</p>
						<h2>{uiText("How improvement is calculated", $activeLocale)}</h2>
					</div>
					<div class="heading-stack">
						<span class="timeframe-badge longitudinal">{uiText("Interpret carefully", $activeLocale)}</span>
					</div>
				</div>
				<p class="empty-copy">{uiText("Improvement compares the first 5 recorded scores with the last 5 recorded scores for patients who have enough completed sessions. It is a longitudinal signal, not a short-term monitoring metric.", $activeLocale)}</p>
			</section>
		</section>

		<section class="panel-card">
			<div class="panel-heading">
				<div>
					<p class="panel-kicker">{uiText("Activity", $activeLocale)}</p>
					<h2>{uiText("Cohort Activity Trends", $activeLocale)}</h2>
				</div>
				<div class="heading-stack">
					<span class="timeframe-badge recent">{uiText("Last 30 days", $activeLocale)}</span>
				</div>
			</div>
			{#if cohortTrends?.trends?.length}
				<div class="trend-summary">
					<div><span>{uiText("Average Sessions / Week", $activeLocale)}</span><strong>{oneDecimal(cohortTrends.summary.avg_sessions_per_week)}</strong></div>
					<div><span>{uiText("Overall Average Score", $activeLocale)}</span><strong>{oneDecimal(cohortTrends.summary.overall_avg_score)}</strong></div>
				</div>
				<div class="trend-list">
					{#each cohortTrends.trends as week}
						<div class="trend-row">
							<div class="trend-date">{compactDate(week.week_starting)}</div>
							<div class="trend-bars">
								<div class="trend-bar sessions" style={`width: ${(week.sessions / cohortTrends.summary.total_sessions) * 400}%`}></div>
							</div>
							<div class="trend-copy">
								<span>{n(week.sessions)} {uiText("sessions", $activeLocale)}</span>
								<span>{n(week.active_patients)} {uiText("patients", $activeLocale)}</span>
								<span>{uiText("Avg", $activeLocale)} {oneDecimal(week.avg_score)}</span>
							</div>
						</div>
					{/each}
				</div>
			{:else}
				<p class="empty-copy">{uiText("No recent cohort activity was found for the selected period.", $activeLocale)}</p>
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

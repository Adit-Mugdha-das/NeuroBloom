<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import api from '$lib/api.js';
	import DoctorWorkspaceShell from '$lib/components/DoctorWorkspaceShell.svelte';
	import PerformanceTrends from '$lib/components/PerformanceTrends.svelte';
	import { user } from '$lib/stores.js';
	import { Chart, registerables } from 'chart.js';
	import { afterUpdate, onMount } from 'svelte';

	Chart.register(...registerables);

	let patientId;
	let userData;
	let loading = true;
	let error = '';
	let reports = [];
	let selectedReport = null;
	let patientInfo = null;
	let periodType = 'weekly';
	let generating = false;
	let editingCommentary = false;
	let commentaryText = '';
	let trendsData = null;

	let domainChart = null;
	let dailyActivityChart = null;
	let taskPerformanceChart = null;
	let baselineComparisonChart = null;

	const unsubscribeUser = user.subscribe((value) => {
		userData = value;
	});

	const unsubscribePage = page.subscribe((value) => {
		patientId = value.params.id;
	});

	onMount(() => {
		if (!userData || userData.role !== 'doctor') {
			goto('/login');
			return;
		}

		loadReports();

		return () => {
			unsubscribeUser();
			unsubscribePage();
			destroyCharts();
		};
	});

	afterUpdate(() => {
		if (selectedReport && !loading) {
			renderCharts();
		}
	});

	function destroyCharts() {
		if (domainChart) domainChart.destroy();
		if (dailyActivityChart) dailyActivityChart.destroy();
		if (taskPerformanceChart) taskPerformanceChart.destroy();
		if (baselineComparisonChart) baselineComparisonChart.destroy();
	}

	async function loadReports() {
		loading = true;
		error = '';

		try {
			const patientResponse = await api.get(`/api/doctor/${userData.id}/patient/${patientId}/overview`);
			patientInfo = patientResponse.data;

			const reportsResponse = await api.get(`/api/doctor/${userData.id}/patients/${patientId}/reports`);
			reports = reportsResponse.data || [];

			try {
				const trendsResponse = await api.get(`/api/doctor/${userData.id}/patient/${patientId}/trends`, {
					params: { days: 30 }
				});
				trendsData = trendsResponse.data;
			} catch (requestError) {
				console.error('Failed to load trends data:', requestError);
			}

			if (reports.length > 0) {
				selectedReport = reports[0];
				commentaryText = selectedReport.doctor_commentary || '';
			}
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Failed to load progress reports';
			console.error(requestError);
		} finally {
			loading = false;
		}
	}

	async function generateReport() {
		try {
			generating = true;
			error = '';

			const response = await api.post(`/api/doctor/${userData.id}/patients/${patientId}/generate-report?period_type=${periodType}`);
			selectedReport = response.data;
			commentaryText = selectedReport.doctor_commentary || '';

			reports = [selectedReport, ...reports.filter((report) => report.id !== selectedReport.id)];
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Failed to generate report';
			console.error(requestError);
		} finally {
			generating = false;
		}
	}

	async function saveCommentary() {
		if (!selectedReport) return;

		try {
			await api.patch(`/api/doctor/${userData.id}/reports/${selectedReport.id}/commentary`, {
				commentary: commentaryText
			});

			selectedReport.doctor_commentary = commentaryText;
			editingCommentary = false;

			const index = reports.findIndex((report) => report.id === selectedReport.id);
			if (index !== -1) {
				reports[index].doctor_commentary = commentaryText;
			}
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Failed to save commentary';
			console.error(requestError);
		}
	}

	function renderCharts() {
		if (!selectedReport || !selectedReport.report_data) return;

		destroyCharts();
		const data = selectedReport.report_data;

		renderDomainChart(data.domain_stats);

		if (data.baseline && data.baseline.completed) {
			renderBaselineComparisonChart(data.domain_stats, data.baseline);
		}

		renderDailyActivityChart(data.daily_activity);
		renderTaskPerformanceChart(data.task_performance);
	}

	function getChartTextColor() {
		return '#475569';
	}

	function getChartGridColor() {
		return 'rgba(148, 163, 184, 0.22)';
	}

	function commonChartPlugins() {
		return {
			legend: {
				labels: {
					color: getChartTextColor()
				}
			},
			tooltip: {
				backgroundColor: 'rgba(15, 23, 42, 0.92)',
				titleColor: '#ffffff',
				bodyColor: '#ffffff'
			}
		};
	}

	/**
	 * @param {string} canvasId
	 * @returns {CanvasRenderingContext2D | null}
	 */
	function getCanvasContext(canvasId) {
		const canvas = document.getElementById(canvasId);
		if (!canvas || canvas.tagName !== 'CANVAS') return null;

		return /** @type {HTMLCanvasElement} */ (canvas).getContext('2d');
	}

	function renderDomainChart(domainStats) {
		const ctx = getCanvasContext('domainChart');
		if (!ctx) return;
		const domains = Object.keys(domainStats);
		const scores = domains.map((domain) => domainStats[domain].avg_score || 0);
		const accuracies = domains.map((domain) => domainStats[domain].avg_accuracy || 0);

		domainChart = new Chart(ctx, {
			type: 'radar',
			data: {
				labels: domains.map((domain) => formatDomainName(domain)),
				datasets: [
					{
						label: 'Average Score',
						data: scores,
						backgroundColor: 'rgba(79, 70, 229, 0.14)',
						borderColor: 'rgba(79, 70, 229, 1)',
						borderWidth: 2,
						pointBackgroundColor: 'rgba(79, 70, 229, 1)'
					},
					{
						label: 'Average Accuracy',
						data: accuracies,
						backgroundColor: 'rgba(14, 165, 233, 0.14)',
						borderColor: 'rgba(14, 165, 233, 1)',
						borderWidth: 2,
						pointBackgroundColor: 'rgba(14, 165, 233, 1)'
					}
				]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				scales: {
					r: {
						angleLines: { color: getChartGridColor() },
						grid: { color: getChartGridColor() },
						pointLabels: { color: getChartTextColor() },
						ticks: {
							color: getChartTextColor(),
							backdropColor: 'transparent'
						},
						suggestedMin: 0,
						suggestedMax: 100
					}
				},
				plugins: commonChartPlugins()
			}
		});
	}

	function renderBaselineComparisonChart(domainStats, baseline) {
		const ctx = getCanvasContext('baselineComparisonChart');
		if (!ctx) return;
		const domains = Object.keys(domainStats);
		const baselineScores = domains.map((domain) => baseline.domain_scores[domain] || 0);
		const currentScores = domains.map((domain) => domainStats[domain].avg_score || 0);

		baselineComparisonChart = new Chart(ctx, {
			type: 'bar',
			data: {
				labels: domains.map((domain) => formatDomainName(domain)),
				datasets: [
					{
						label: 'Baseline',
						data: baselineScores,
						backgroundColor: 'rgba(148, 163, 184, 0.72)',
						borderColor: 'rgba(100, 116, 139, 1)',
						borderWidth: 1
					},
					{
						label: 'Current',
						data: currentScores,
						backgroundColor: 'rgba(79, 70, 229, 0.72)',
						borderColor: 'rgba(79, 70, 229, 1)',
						borderWidth: 1
					}
				]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				scales: {
					y: {
						beginAtZero: true,
						max: 100,
						ticks: { color: getChartTextColor() },
						grid: { color: getChartGridColor() },
						title: {
							display: true,
							text: 'Score',
							color: getChartTextColor()
						}
					},
					x: {
						ticks: { color: getChartTextColor() },
						grid: { color: getChartGridColor() }
					}
				},
				plugins: {
					...commonChartPlugins(),
					tooltip: {
						...commonChartPlugins().tooltip,
						callbacks: {
							afterBody(context) {
								const domainIndex = context[0].dataIndex;
								const domain = domains[domainIndex];
								const stats = domainStats[domain];
								if (stats.improvement !== null) {
									return [
										'',
										`Change: ${stats.improvement > 0 ? '+' : ''}${stats.improvement.toFixed(1)} (${stats.improvement_percent > 0 ? '+' : ''}${stats.improvement_percent.toFixed(1)}%)`
									];
								}
								return [];
							}
						}
					}
				}
			}
		});
	}

	function renderDailyActivityChart(dailyActivity) {
		const ctx = getCanvasContext('dailyActivityChart');
		if (!ctx) return;
		const days = Object.keys(dailyActivity).sort();
		const sessions = days.map((day) => dailyActivity[day].sessions);
		const avgScores = days.map((day) => dailyActivity[day].avg_score || 0);

		dailyActivityChart = new Chart(ctx, {
			type: 'bar',
			data: {
				labels: days.map((day) => new Date(day).toLocaleDateString('en-GB', { month: 'short', day: 'numeric' })),
				datasets: [
					{
						label: 'Sessions',
						data: sessions,
						backgroundColor: 'rgba(14, 165, 233, 0.72)',
						borderColor: 'rgba(14, 165, 233, 1)',
						borderWidth: 1,
						yAxisID: 'y'
					},
					{
						label: 'Average Score',
						data: avgScores,
						type: 'line',
						borderColor: 'rgba(79, 70, 229, 1)',
						backgroundColor: 'rgba(79, 70, 229, 0.15)',
						borderWidth: 2,
						tension: 0.4,
						yAxisID: 'y1'
					}
				]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				interaction: { mode: 'index', intersect: false },
				scales: {
					y: {
						type: 'linear',
						display: true,
						position: 'left',
						ticks: { color: getChartTextColor(), stepSize: 1 },
						grid: { color: getChartGridColor() },
						title: { display: true, text: 'Sessions', color: getChartTextColor() }
					},
					y1: {
						type: 'linear',
						display: true,
						position: 'right',
						suggestedMin: 0,
						suggestedMax: 100,
						ticks: { color: getChartTextColor() },
						grid: { drawOnChartArea: false },
						title: { display: true, text: 'Score', color: getChartTextColor() }
					},
					x: {
						ticks: { color: getChartTextColor() },
						grid: { color: getChartGridColor() }
					}
				},
				plugins: commonChartPlugins()
			}
		});
	}

	function renderTaskPerformanceChart(taskPerformance) {
		const ctx = getCanvasContext('taskPerformanceChart');
		if (!ctx) return;
		const tasks = Object.keys(taskPerformance).slice(0, 10);
		const scores = tasks.map((task) => taskPerformance[task].avg_score || 0);
		const sessionCounts = tasks.map((task) => taskPerformance[task].sessions);

		taskPerformanceChart = new Chart(ctx, {
			type: 'bar',
			data: {
				labels: tasks.map((task) => formatTaskName(task)),
				datasets: [
					{
						label: 'Average Score',
						data: scores,
						backgroundColor: scores.map((score) => getScoreColor(score, 0.72)),
						borderColor: scores.map((score) => getScoreColor(score, 1)),
						borderWidth: 1
					}
				]
			},
			options: {
				indexAxis: 'y',
				responsive: true,
				maintainAspectRatio: false,
				scales: {
					x: {
						suggestedMax: 100,
						ticks: { color: getChartTextColor() },
						grid: { color: getChartGridColor() }
					},
					y: {
						ticks: { color: getChartTextColor() },
						grid: { color: getChartGridColor() }
					}
				},
				plugins: {
					legend: { display: false },
					tooltip: {
						backgroundColor: 'rgba(15, 23, 42, 0.92)',
						titleColor: '#ffffff',
						bodyColor: '#ffffff',
						callbacks: {
							afterLabel(context) {
								const index = context.dataIndex;
								return `Sessions: ${sessionCounts[index]}`;
							}
						}
					}
				}
			}
		});
	}

	function formatDomainName(domain) {
		return domain.split('_').map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
	}

	function formatTaskName(task) {
		return task.split('_').map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
	}

	function getScoreColor(score, alpha = 1) {
		if (score >= 80) return `rgba(34, 197, 94, ${alpha})`;
		if (score >= 60) return `rgba(245, 158, 11, ${alpha})`;
		return `rgba(239, 68, 68, ${alpha})`;
	}

	function getTrendIcon(trend) {
		if (trend === 'improving') return 'Upward';
		if (trend === 'declining') return 'Downward';
		return 'Stable';
	}

	function getTrendClass(trend) {
		if (trend === 'improving') return 'trend-up';
		if (trend === 'declining') return 'trend-down';
		return 'trend-stable';
	}

	function formatDate(dateString) {
		return new Date(dateString).toLocaleDateString('en-GB', {
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		});
	}

	function exportToPDF() {
		alert('PDF export feature coming soon!');
	}

	function exportToCSV() {
		if (!selectedReport) return;

		const data = selectedReport.report_data;
		let csv = 'Progress Report\n\n';
		csv += `Patient: ${patientInfo?.patient_info?.full_name || patientInfo?.patient_info?.email || 'Patient'}\n`;
		csv += `Period: ${formatDate(selectedReport.period_start)} - ${formatDate(selectedReport.period_end)}\n`;
		csv += `Type: ${selectedReport.period_type}\n\n`;

		csv += '\nSummary\n';
		csv += 'Metric,Value\n';
		csv += `Total Sessions,${data.summary.total_sessions}\n`;
		csv += `Total Duration (minutes),${data.summary.total_duration_minutes}\n`;
		csv += `Average Score,${data.summary.avg_overall_score}\n`;
		csv += `Active Days,${data.summary.active_days}\n\n`;

		csv += '\nDomain Performance\n';
		csv += 'Domain,Sessions,Avg Score,Avg Accuracy,Avg Reaction Time,Trend\n';
		Object.entries(data.domain_stats).forEach(([domain, stats]) => {
			csv += `${formatDomainName(domain)},${stats.sessions_count},${stats.avg_score},${stats.avg_accuracy},${stats.avg_reaction_time},${stats.trend}\n`;
		});

		const blob = new Blob([csv], { type: 'text/csv' });
		const url = window.URL.createObjectURL(blob);
		const link = document.createElement('a');
		link.href = url;
		link.download = `progress-report-${selectedReport.period_type}-${new Date().toISOString().split('T')[0]}.csv`;
		link.click();
		window.URL.revokeObjectURL(url);
	}

	$: patientLabel = patientInfo?.patient_info?.full_name || patientInfo?.patient_info?.email || 'Patient';
	$: summaryCards = selectedReport
		? [
				{ label: 'Total Sessions', value: selectedReport.report_data.summary.total_sessions },
				{ label: 'Training Time', value: `${selectedReport.report_data.summary.total_duration_minutes.toFixed(0)}m` },
				{ label: 'Average Score', value: `${selectedReport.report_data.summary.avg_overall_score.toFixed(1)}%` },
				{ label: 'Active Days', value: selectedReport.report_data.summary.active_days }
			]
		: [];
</script>

<DoctorWorkspaceShell
	title="Progress Reports"
	subtitle="Structured reporting for a single patient, including generated report history, baseline comparison, domain summaries, exports, and clinician commentary."
	eyebrow="Doctor Report Workspace"
	maxWidth="1440px"
>
	<svelte:fragment slot="actions">
		<button class="outline-btn" on:click={() => goto(`/doctor/patient/${patientId}`)}>Back to Patient</button>
		<select bind:value={periodType} class="period-select">
			<option value="weekly">Weekly</option>
			<option value="monthly">Monthly</option>
		</select>
		<button class="primary-btn" on:click={generateReport} disabled={generating}>
			{generating ? 'Generating...' : 'Generate Report'}
		</button>
	</svelte:fragment>

	{#if loading}
		<section class="state-card">
			<p>Loading progress reports...</p>
		</section>
	{:else}
		{#if error}
			<section class="state-card error-state">
				<p>{error}</p>
			</section>
		{/if}

		<section class="hero-card">
			<div>
				<p class="panel-kicker">Patient</p>
				<h2>{patientLabel}</h2>
				<p class="hero-copy">
					{#if selectedReport}
						Current report period: {formatDate(selectedReport.period_start)} to {formatDate(selectedReport.period_end)}
					{:else}
						Generate or select a report to review detailed performance and commentary.
					{/if}
				</p>
			</div>
			<div class="hero-actions">
				<button class="outline-btn" on:click={exportToPDF} disabled={!selectedReport}>Export PDF</button>
				<button class="outline-btn" on:click={exportToCSV} disabled={!selectedReport}>Export CSV</button>
			</div>
		</section>

		<section class="content-grid">
			<aside class="sidebar-card">
				<div class="panel-heading">
					<div>
						<p class="panel-kicker">History</p>
						<h3>Report List</h3>
					</div>
				</div>

				{#if reports.length === 0}
					<div class="empty-card">
						<p>No reports yet. Generate a report to populate this workspace.</p>
					</div>
				{:else}
					<div class="report-list">
						{#each reports as report}
							<button
								class:selected={selectedReport?.id === report.id}
								class="report-item"
								on:click={() => {
									selectedReport = report;
									commentaryText = report.doctor_commentary || '';
								}}
							>
								<div>
									<p class="report-type">{report.period_type}</p>
									<p class="report-dates">{formatDate(report.period_start)} to {formatDate(report.period_end)}</p>
								</div>
								{#if report.doctor_commentary}
									<span class="commentary-flag">Commentary</span>
								{/if}
							</button>
						{/each}
					</div>
				{/if}
			</aside>

			{#if selectedReport}
				<div class="main-column">
					<section class="summary-grid">
						{#each summaryCards as card}
							<article class="summary-card">
								<p>{card.label}</p>
								<strong>{card.value}</strong>
							</article>
						{/each}
					</section>

					<section class="chart-card">
						<div class="panel-heading">
							<div>
								<p class="panel-kicker">Overview</p>
								<h3>Cognitive Domain Performance</h3>
							</div>
						</div>
						<div class="chart-wrapper"><canvas id="domainChart"></canvas></div>
					</section>

					<section class="chart-card">
						<div class="panel-heading">
							<div>
								<p class="panel-kicker">Activity</p>
								<h3>Daily Activity and Scores</h3>
							</div>
						</div>
						<div class="chart-wrapper"><canvas id="dailyActivityChart"></canvas></div>
					</section>

					<section class="chart-card">
						<div class="panel-heading">
							<div>
								<p class="panel-kicker">Tasks</p>
								<h3>Top Task Performance</h3>
							</div>
						</div>
						<div class="chart-wrapper"><canvas id="taskPerformanceChart"></canvas></div>
					</section>

					{#if selectedReport.report_data.baseline && selectedReport.report_data.baseline.completed}
						<section class="panel-card">
							<div class="panel-heading">
								<div>
									<p class="panel-kicker">Baseline</p>
									<h3>Baseline Comparison</h3>
								</div>
							</div>
							<p class="hero-copy">Baseline completed on {formatDate(selectedReport.report_data.baseline.date)}</p>
							<div class="chart-wrapper"><canvas id="baselineComparisonChart"></canvas></div>

							<div class="improvement-grid">
								{#each Object.entries(selectedReport.report_data.domain_stats) as [domain, stats]}
									{#if stats.baseline_score !== null && stats.baseline_score !== undefined}
										<article class="improvement-card">
											<h4>{formatDomainName(domain)}</h4>
											<div class="improvement-metrics">
												<div><span>Baseline</span><strong>{(stats.baseline_score || 0).toFixed(1)}%</strong></div>
												<div><span>Current</span><strong>{(stats.avg_score || 0).toFixed(1)}%</strong></div>
												<div><span>Change</span><strong class:positive={stats.improvement >= 0} class:negative={stats.improvement < 0}>{stats.improvement > 0 ? '+' : ''}{stats.improvement.toFixed(1)} points</strong></div>
											</div>
										</article>
									{/if}
								{/each}
							</div>
						</section>
					{/if}

					<section class="panel-card">
						<div class="panel-heading">
							<div>
								<p class="panel-kicker">Domain Detail</p>
								<h3>Domain Statistics</h3>
							</div>
						</div>
						<div class="domain-grid">
							{#each Object.entries(selectedReport.report_data.domain_stats) as [domain, stats]}
								<article class="domain-card">
									<div class="domain-head">
										<h4>{formatDomainName(domain)}</h4>
										<span class="trend-pill {getTrendClass(stats.trend)}">{getTrendIcon(stats.trend)}</span>
									</div>
									<div class="metric-list compact">
										<div><span>Sessions</span><strong>{stats.sessions_count}</strong></div>
										<div><span>Average Score</span><strong>{stats.avg_score.toFixed(1)}%</strong></div>
										<div><span>Accuracy</span><strong>{stats.avg_accuracy.toFixed(1)}%</strong></div>
										<div><span>Reaction Time</span><strong>{stats.avg_reaction_time.toFixed(0)}ms</strong></div>
										<div><span>Difficulty</span><strong>{stats.avg_difficulty.toFixed(1)}/10</strong></div>
										{#if stats.baseline_score !== null && stats.improvement !== null && stats.improvement_percent !== null}
											<div><span>vs Baseline</span><strong class:positive={stats.improvement >= 0} class:negative={stats.improvement < 0}>{stats.improvement > 0 ? '+' : ''}{stats.improvement.toFixed(1)} ({stats.improvement_percent > 0 ? '+' : ''}{stats.improvement_percent.toFixed(1)}%)</strong></div>
										{/if}
									</div>
								</article>
							{/each}
						</div>
					</section>

					{#if trendsData}
						<section class="panel-card trends-wrapper">
							<PerformanceTrends trendsData={trendsData} />
						</section>
					{/if}

					<section class="panel-card">
						<div class="panel-heading">
							<div>
								<p class="panel-kicker">Commentary</p>
								<h3>Doctor Commentary</h3>
							</div>
							<button class="outline-btn" on:click={() => (editingCommentary = !editingCommentary)}>
								{editingCommentary ? 'Cancel' : 'Edit'}
							</button>
						</div>

						{#if editingCommentary}
							<div class="commentary-editor">
								<textarea bind:value={commentaryText} rows="8" placeholder="Add professional observations and recommendations."></textarea>
								<div class="commentary-actions">
									<button class="primary-btn" on:click={saveCommentary}>Save Commentary</button>
								</div>
							</div>
						{:else}
							<div class="commentary-display">
								{#if selectedReport.doctor_commentary}
									<p>{selectedReport.doctor_commentary}</p>
								{:else}
									<p class="empty-copy">No commentary added yet.</p>
								{/if}
							</div>
						{/if}
					</section>
				</div>
			{:else}
				<section class="panel-card empty-main">
					<h3>No Report Selected</h3>
					<p class="empty-copy">Select a report from the sidebar or generate a new one.</p>
				</section>
			{/if}
		</section>
	{/if}
</DoctorWorkspaceShell>

<style>
	.primary-btn,
	.outline-btn,
	.period-select {
		border-radius: 999px;
		padding: 0.78rem 1rem;
		font-weight: 700;
		font: inherit;
	}

	.primary-btn {
		border: 1px solid #4f46e5;
		background: #4f46e5;
		color: #ffffff;
		cursor: pointer;
	}

	.outline-btn,
	.period-select {
		border: 1px solid #d1d5db;
		background: #ffffff;
		color: #111827;
	}

	.hero-card,
	.sidebar-card,
	.summary-card,
	.chart-card,
	.panel-card,
	.state-card,
	.domain-card,
	.improvement-card,
	.report-item,
	.empty-card {
		background: #f8fafc;
		border: 1px solid #e2e8f0;
		box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
	}

	.hero-card,
	.sidebar-card,
	.chart-card,
	.panel-card,
	.state-card,
	.empty-card {
		border-radius: 26px;
		padding: 1.2rem;
	}

	.error-state {
		border-color: rgba(239, 68, 68, 0.25);
		color: #b91c1c;
	}

	.hero-card,
	.content-grid,
	.summary-grid,
	.domain-grid,
	.improvement-grid {
		display: grid;
		gap: 1rem;
	}

	.hero-card {
		grid-template-columns: 1fr auto;
		align-items: center;
	}

	.hero-actions {
		display: flex;
		gap: 0.75rem;
		flex-wrap: wrap;
		justify-content: flex-end;
	}

	.panel-kicker,
	.summary-card p,
	.report-type,
	.metric-list span,
	.improvement-metrics span {
		margin: 0;
		font-size: 0.78rem;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: #6b7280;
	}

	h2,
	h3,
	h4 {
		margin: 0.2rem 0 0;
		color: #111827;
	}

	.hero-copy,
	.empty-copy,
	.report-dates,
	.commentary-display p {
		color: #6b7280;
		line-height: 1.6;
	}

	.content-grid {
		grid-template-columns: 300px minmax(0, 1fr);
		align-items: start;
	}

	.report-list,
	.main-column {
		display: grid;
		gap: 1rem;
	}

	.report-item {
		display: grid;
		grid-template-columns: 1fr auto;
		gap: 0.75rem;
		text-align: left;
		cursor: pointer;
		border-radius: 20px;
		padding: 1rem;
	}

	.report-item.selected {
		border-color: #4f46e5;
		background: #eef2ff;
	}

	.commentary-flag,
	.trend-pill {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		border-radius: 999px;
		padding: 0.3rem 0.7rem;
		font-size: 0.78rem;
		font-weight: 800;
	}

	.commentary-flag,
	.trend-pill.trend-stable {
		background: #eef2ff;
		color: #4f46e5;
	}

	.trend-pill.trend-up {
		background: #dcfce7;
		color: #15803d;
	}

	.trend-pill.trend-down {
		background: #fee2e2;
		color: #b91c1c;
	}

	.summary-grid {
		grid-template-columns: repeat(4, minmax(0, 1fr));
	}

	.summary-card {
		border-radius: 22px;
		padding: 1rem;
	}

	.summary-card strong {
		display: block;
		margin-top: 0.4rem;
		font-size: 1.7rem;
		color: #111827;
	}

	.chart-wrapper {
		position: relative;
		height: 350px;
	}

	.domain-grid,
	.improvement-grid {
		grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
	}

	.domain-card,
	.improvement-card {
		border-radius: 22px;
		padding: 1rem;
	}

	.domain-head,
	.panel-heading,
	.commentary-actions {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: center;
	}

	.metric-list,
	.improvement-metrics {
		display: grid;
		gap: 0.8rem;
	}

	.metric-list.compact div,
	.improvement-metrics div {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		padding-top: 0.7rem;
		border-top: 1px solid #eef2f7;
	}

	.metric-list.compact div:first-child,
	.improvement-metrics div:first-child {
		padding-top: 0;
		border-top: none;
	}

	.metric-list strong,
	.improvement-metrics strong {
		color: #111827;
	}

	.positive {
		color: #15803d;
	}

	.negative {
		color: #b91c1c;
	}

	.commentary-editor textarea {
		width: 100%;
		border: 1px solid #d1d5db;
		border-radius: 18px;
		padding: 1rem;
		font: inherit;
		background: #f9fafb;
		color: #111827;
		resize: vertical;
		min-height: 180px;
	}

	.empty-main {
		text-align: center;
	}

	:global(.trends-wrapper .card),
	:global(.trends-wrapper .panel),
	:global(.trends-wrapper .chart-card) {
		background: transparent;
		box-shadow: none;
	}

	@media (max-width: 1200px) {
		.content-grid,
		.hero-card {
			grid-template-columns: 1fr;
		}

		.summary-grid {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}

	@media (max-width: 760px) {
		.summary-grid {
			grid-template-columns: 1fr;
		}

		.panel-heading,
		.domain-head,
		.hero-actions {
			flex-direction: column;
			align-items: stretch;
		}

		.report-item {
			grid-template-columns: 1fr;
		}
	}
</style>
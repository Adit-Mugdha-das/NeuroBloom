<script>
	import { locale as activeLocale, uiText } from '$lib/i18n';
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
		if (!selectedReport) return;

		const data = selectedReport.report_data;
		const patient = patientInfo?.patient_info;
		const name = patient?.full_name || patient?.email || 'Patient';
		const period = `${formatDate(selectedReport.period_start)} – ${formatDate(selectedReport.period_end)}`;
		const generated = new Date().toLocaleDateString('en-GB', { year: 'numeric', month: 'long', day: 'numeric' });

		const domainRows = Object.entries(data.domain_stats || {}).map(([domain, stats]) => `
			<tr>
				<td>${formatDomainName(domain)}</td>
				<td>${stats.sessions_count ?? '—'}</td>
				<td>${stats.avg_score != null ? stats.avg_score.toFixed(1) + '%' : '—'}</td>
				<td>${stats.avg_accuracy != null ? stats.avg_accuracy.toFixed(1) + '%' : '—'}</td>
				<td>${stats.avg_reaction_time != null ? stats.avg_reaction_time.toFixed(0) + ' ms' : '—'}</td>
				<td class="trend-${stats.trend}">${stats.trend ?? '—'}</td>
			</tr>`).join('');

		const commentary = selectedReport.doctor_commentary
			? `<section class="section">
					<h2>Clinician Commentary</h2>
					<p class="commentary">${selectedReport.doctor_commentary.replace(/\n/g, '<br>')}</p>
			   </section>`
			: '';

		const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Progress Report – ${name}</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px; color: #1e293b; padding: 32px 40px; }
  header { display: flex; justify-content: space-between; align-items: flex-start; padding-bottom: 16px; border-bottom: 2px solid #0e7490; margin-bottom: 24px; }
  .logo { font-size: 18px; font-weight: 700; color: #0e7490; letter-spacing: -0.02em; }
  .logo span { font-weight: 400; color: #64748b; font-size: 11px; display: block; }
  .meta { text-align: right; color: #64748b; font-size: 11px; line-height: 1.6; }
  h1 { font-size: 20px; font-weight: 700; color: #0f172a; margin-bottom: 4px; }
  h2 { font-size: 13px; font-weight: 700; color: #0e7490; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 10px; }
  .section { margin-bottom: 24px; }
  .summary-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }
  .summary-card { background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 12px 14px; }
  .summary-card .label { font-size: 10px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
  .summary-card .value { font-size: 20px; font-weight: 700; color: #0e7490; }
  table { width: 100%; border-collapse: collapse; font-size: 11.5px; }
  th { background: #f8fafc; text-align: left; padding: 8px 10px; font-size: 10px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 2px solid #e2e8f0; }
  td { padding: 8px 10px; border-bottom: 1px solid #f1f5f9; color: #334155; }
  tr:last-child td { border-bottom: none; }
  .trend-improving { color: #059669; font-weight: 700; }
  .trend-declining { color: #dc2626; font-weight: 700; }
  .trend-stable { color: #d97706; font-weight: 600; }
  .commentary { line-height: 1.7; color: #334155; background: #f8fafc; border-left: 3px solid #0e7490; padding: 12px 16px; border-radius: 0 6px 6px 0; }
  footer { margin-top: 32px; padding-top: 12px; border-top: 1px solid #e2e8f0; font-size: 10px; color: #94a3b8; display: flex; justify-content: space-between; }
  @media print {
    body { padding: 20px 28px; }
    @page { margin: 16mm 18mm; }
  }
</style>
</head>
<body>
<header>
  <div>
    <div class="logo">NeuroBloom <span>Doctor Portal</span></div>
    <h1>${name}</h1>
    <p style="color:#64748b;font-size:11px;margin-top:4px;">Report period: ${period}</p>
  </div>
  <div class="meta">
    <div>Generated: ${generated}</div>
    <div>Period type: ${selectedReport.period_type}</div>
    <div>Report ID: ${selectedReport.id}</div>
  </div>
</header>

<div class="summary-grid">
  <div class="summary-card"><div class="label">Total Sessions</div><div class="value">${data.summary.total_sessions}</div></div>
  <div class="summary-card"><div class="label">Training Time</div><div class="value">${data.summary.total_duration_minutes?.toFixed(0)}m</div></div>
  <div class="summary-card"><div class="label">Average Score</div><div class="value">${data.summary.avg_overall_score?.toFixed(1)}%</div></div>
  <div class="summary-card"><div class="label">Active Days</div><div class="value">${data.summary.active_days}</div></div>
</div>

<section class="section">
  <h2>Cognitive Domain Performance</h2>
  <table>
    <thead>
      <tr>
        <th>Domain</th><th>Sessions</th><th>Avg Score</th><th>Avg Accuracy</th><th>Avg RT</th><th>Trend</th>
      </tr>
    </thead>
    <tbody>${domainRows}</tbody>
  </table>
</section>

${commentary}

<footer>
  <span>NeuroBloom — Cognitive Training &amp; Monitoring Platform</span>
  <span>Confidential — For clinical use only</span>
</footer>

<script>window.onload = function() { window.print(); }<\/script>
</body>
</html>`;

		const win = window.open('', '_blank');
		win.document.write(html);
		win.document.close();
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
	title={uiText("Progress Reports", $activeLocale)}
	subtitle={uiText("Structured reporting for a single patient, including generated report history, baseline comparison, domain summaries, exports, and clinician commentary.", $activeLocale)}
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
			<p>{uiText("Loading progress reports...", $activeLocale)}</p>
		</section>
	{:else}
		{#if error}
			<section class="state-card error-state">
				<p>{error}</p>
			</section>
		{/if}

		<section class="hero-card">
			<div>
				<p class="panel-kicker">{uiText("Patient", $activeLocale)}</p>
				<h2>{patientLabel}</h2>
				<p class="hero-copy">
					{#if selectedReport}
						{uiText("Current report period:", $activeLocale)} {formatDate(selectedReport.period_start)} to {formatDate(selectedReport.period_end)}
					{:else}
						{uiText("Generate or select a report to review detailed performance and commentary.", $activeLocale)}
					{/if}
				</p>
			</div>
			<div class="hero-actions">
				<button class="outline-btn" on:click={exportToPDF} disabled={!selectedReport}>{uiText("Export PDF", $activeLocale)}</button>
				<button class="outline-btn" on:click={exportToCSV} disabled={!selectedReport}>{uiText("Export CSV", $activeLocale)}</button>
			</div>
		</section>

		<section class="content-grid">
			<aside class="sidebar-card">
				<div class="panel-heading">
					<div>
						<p class="panel-kicker">{uiText("History", $activeLocale)}</p>
						<h3>{uiText("Report List", $activeLocale)}</h3>
					</div>
				</div>

				{#if reports.length === 0}
					<div class="empty-card">
						<p>{uiText("No reports yet. Generate a report to populate this workspace.", $activeLocale)}</p>
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
									<span class="commentary-flag">{uiText("Commentary", $activeLocale)}</span>
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
								<p class="panel-kicker">{uiText("Overview", $activeLocale)}</p>
								<h3>{uiText("Cognitive Domain Performance", $activeLocale)}</h3>
							</div>
						</div>
						<div class="chart-wrapper"><canvas id="domainChart"></canvas></div>
					</section>

					<section class="chart-card">
						<div class="panel-heading">
							<div>
								<p class="panel-kicker">{uiText("Activity", $activeLocale)}</p>
								<h3>{uiText("Daily Activity and Scores", $activeLocale)}</h3>
							</div>
						</div>
						<div class="chart-wrapper"><canvas id="dailyActivityChart"></canvas></div>
					</section>

					<section class="chart-card">
						<div class="panel-heading">
							<div>
								<p class="panel-kicker">{uiText("Tasks", $activeLocale)}</p>
								<h3>{uiText("Top Task Performance", $activeLocale)}</h3>
							</div>
						</div>
						<div class="chart-wrapper"><canvas id="taskPerformanceChart"></canvas></div>
					</section>

					{#if selectedReport.report_data.baseline && selectedReport.report_data.baseline.completed}
						<section class="panel-card">
							<div class="panel-heading">
								<div>
									<p class="panel-kicker">{uiText("Baseline", $activeLocale)}</p>
									<h3>{uiText("Baseline Comparison", $activeLocale)}</h3>
								</div>
							</div>
							<p class="hero-copy">{uiText("Baseline completed on", $activeLocale)} {formatDate(selectedReport.report_data.baseline.date)}</p>
							<div class="chart-wrapper"><canvas id="baselineComparisonChart"></canvas></div>

							<div class="improvement-grid">
								{#each Object.entries(selectedReport.report_data.domain_stats) as [domain, stats]}
									{#if stats.baseline_score !== null && stats.baseline_score !== undefined}
										<article class="improvement-card">
											<h4>{formatDomainName(domain)}</h4>
											<div class="improvement-metrics">
												<div><span>{uiText("Baseline", $activeLocale)}</span><strong>{(stats.baseline_score || 0).toFixed(1)}%</strong></div>
												<div><span>{uiText("Current", $activeLocale)}</span><strong>{(stats.avg_score || 0).toFixed(1)}%</strong></div>
												<div><span>{uiText("Change", $activeLocale)}</span><strong class:positive={stats.improvement >= 0} class:negative={stats.improvement < 0}>{stats.improvement > 0 ? '+' : ''}{stats.improvement.toFixed(1)} {uiText("points", $activeLocale)}</strong></div>
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
								<p class="panel-kicker">{uiText("Domain Detail", $activeLocale)}</p>
								<h3>{uiText("Domain Statistics", $activeLocale)}</h3>
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
										<div><span>{uiText("Sessions", $activeLocale)}</span><strong>{stats.sessions_count}</strong></div>
										<div><span>{uiText("Average Score", $activeLocale)}</span><strong>{stats.avg_score.toFixed(1)}%</strong></div>
										<div><span>{uiText("Accuracy", $activeLocale)}</span><strong>{stats.avg_accuracy.toFixed(1)}%</strong></div>
										<div><span>{uiText("Reaction Time", $activeLocale)}</span><strong>{stats.avg_reaction_time.toFixed(0)}ms</strong></div>
										<div><span>{uiText("Difficulty", $activeLocale)}</span><strong>{stats.avg_difficulty.toFixed(1)}/10</strong></div>
										{#if stats.baseline_score !== null && stats.improvement !== null && stats.improvement_percent !== null}
											<div><span>{uiText("vs Baseline", $activeLocale)}</span><strong class:positive={stats.improvement >= 0} class:negative={stats.improvement < 0}>{stats.improvement > 0 ? '+' : ''}{stats.improvement.toFixed(1)} ({stats.improvement_percent > 0 ? '+' : ''}{stats.improvement_percent.toFixed(1)}%)</strong></div>
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
								<p class="panel-kicker">{uiText("Commentary", $activeLocale)}</p>
								<h3>{uiText("Doctor Commentary", $activeLocale)}</h3>
							</div>
							<button class="outline-btn" on:click={() => (editingCommentary = !editingCommentary)}>
								{editingCommentary ? 'Cancel' : 'Edit'}
							</button>
						</div>

						{#if editingCommentary}
							<div class="commentary-editor">
								<textarea bind:value={commentaryText} rows="8" placeholder={uiText("Add professional observations and recommendations.", $activeLocale)}></textarea>
								<div class="commentary-actions">
									<button class="primary-btn" on:click={saveCommentary}>{uiText("Save Commentary", $activeLocale)}</button>
								</div>
							</div>
						{:else}
							<div class="commentary-display">
								{#if selectedReport.doctor_commentary}
									<p>{selectedReport.doctor_commentary}</p>
								{:else}
									<p class="empty-copy">{uiText("No commentary added yet.", $activeLocale)}</p>
								{/if}
							</div>
						{/if}
					</section>
				</div>
			{:else}
				<section class="panel-card empty-main">
					<h3>{uiText("No Report Selected", $activeLocale)}</h3>
					<p class="empty-copy">{uiText("Select a report from the sidebar or generate a new one.", $activeLocale)}</p>
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
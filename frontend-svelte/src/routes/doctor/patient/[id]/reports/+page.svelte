<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import api from '$lib/api.js';
	import { user } from '$lib/stores.js';
	import { Chart, registerables } from 'chart.js';
	import { afterUpdate, onMount } from 'svelte';
	
	Chart.register(...registerables);
	
	let patientId;
	let userData;
	let pageData;
	let loading = true;
	let error = '';
	let reports = [];
	let selectedReport = null;
	let patientInfo = null;
	let periodType = 'weekly'; // 'weekly' or 'monthly'
	let generating = false;
	let editingCommentary = false;
	let commentaryText = '';
	
	// Chart references
	let domainChart = null;
	let trendsChart = null;
	let dailyActivityChart = null;
	let taskPerformanceChart = null;
	
	// Subscribe to stores
	const unsubscribeUser = user.subscribe(value => {
		userData = value;
	});
	
	const unsubscribePage = page.subscribe(value => {
		pageData = value;
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
		if (trendsChart) trendsChart.destroy();
		if (dailyActivityChart) dailyActivityChart.destroy();
		if (taskPerformanceChart) taskPerformanceChart.destroy();
	}
	
	async function loadReports() {
		try {
			loading = true;
			
			// Load patient info
			const patientResponse = await api.get(
				`/api/doctor/${userData.id}/patient/${patientId}/overview`
			);
			patientInfo = patientResponse.data;
			
			// Load reports
			const reportsResponse = await api.get(
				`/api/doctor/${userData.id}/patients/${patientId}/reports`
			);
			reports = reportsResponse.data;
			
			// Select most recent report by default
			if (reports.length > 0) {
				selectedReport = reports[0];
				commentaryText = selectedReport.doctor_commentary || '';
			}
			
		} catch (err) {
			error = 'Failed to load progress reports';
			console.error(err);
		} finally {
			loading = false;
		}
	}
	
	async function generateReport() {
		try {
			generating = true;
			error = '';
			
			const response = await api.post(
				`/api/doctor/${userData.id}/patients/${patientId}/generate-report?period_type=${periodType}`
			);
			
			selectedReport = response.data;
			commentaryText = selectedReport.doctor_commentary || '';
			
			// Reload reports list
			await loadReports();
			
		} catch (err) {
			error = 'Failed to generate report';
			console.error(err);
		} finally {
			generating = false;
		}
	}
	
	async function saveCommentary() {
		if (!selectedReport) return;
		
		try {
			await api.patch(
				`/api/doctor/${userData.id}/reports/${selectedReport.id}/commentary`,
				{ commentary: commentaryText }
			);
			
			selectedReport.doctor_commentary = commentaryText;
			editingCommentary = false;
			
			// Update the report in the list
			const index = reports.findIndex(r => r.id === selectedReport.id);
			if (index !== -1) {
				reports[index].doctor_commentary = commentaryText;
			}
			
		} catch (err) {
			error = 'Failed to save commentary';
			console.error(err);
		}
	}
	
	function renderCharts() {
		if (!selectedReport || !selectedReport.report_data) return;
		
		destroyCharts();
		
		const data = selectedReport.report_data;
		
		// Domain Performance Radar Chart
		renderDomainChart(data.domain_stats);
		
		// Daily Activity Chart
		renderDailyActivityChart(data.daily_activity);
		
		// Task Performance Chart
		renderTaskPerformanceChart(data.task_performance);
	}
	
	function renderDomainChart(domainStats) {
		const canvas = document.getElementById('domainChart');
		if (!canvas) return;
		
		const ctx = /** @type {HTMLCanvasElement} */ (canvas).getContext('2d');
		const domains = Object.keys(domainStats);
		const scores = domains.map(d => domainStats[d].avg_score || 0);
		const accuracies = domains.map(d => domainStats[d].avg_accuracy || 0);
		
		domainChart = new Chart(ctx, {
			type: 'radar',
			data: {
				labels: domains.map(d => formatDomainName(d)),
				datasets: [
					{
						label: 'Average Score',
						data: scores,
						backgroundColor: 'rgba(75, 192, 192, 0.2)',
						borderColor: 'rgba(75, 192, 192, 1)',
						borderWidth: 2,
						pointBackgroundColor: 'rgba(75, 192, 192, 1)',
						pointBorderColor: '#fff',
						pointHoverBackgroundColor: '#fff',
						pointHoverBorderColor: 'rgba(75, 192, 192, 1)'
					},
					{
						label: 'Average Accuracy',
						data: accuracies,
						backgroundColor: 'rgba(255, 99, 132, 0.2)',
						borderColor: 'rgba(255, 99, 132, 1)',
						borderWidth: 2,
						pointBackgroundColor: 'rgba(255, 99, 132, 1)',
						pointBorderColor: '#fff',
						pointHoverBackgroundColor: '#fff',
						pointHoverBorderColor: 'rgba(255, 99, 132, 1)'
					}
				]
			},
			options: {
				responsive: true,
				maintainAspectRatio: true,
				scales: {
					r: {
						angleLines: {
							color: 'rgba(255, 255, 255, 0.1)'
						},
						grid: {
							color: 'rgba(255, 255, 255, 0.1)'
						},
						pointLabels: {
							color: '#fff',
							font: {
								size: 12
							}
						},
						ticks: {
							color: '#fff',
							backdropColor: 'transparent',
						},
						suggestedMin: 0,
						suggestedMax: 100
					}
				},
				plugins: {
					legend: {
						labels: {
							color: '#fff'
						}
					}
				}
			}
		});
	}
	
	function renderDailyActivityChart(dailyActivity) {
		const canvas = document.getElementById('dailyActivityChart');
		if (!canvas) return;
		
		const ctx = /** @type {HTMLCanvasElement} */ (canvas).getContext('2d');
		const days = Object.keys(dailyActivity).sort();
		const sessions = days.map(d => dailyActivity[d].sessions);
		const avgScores = days.map(d => dailyActivity[d].avg_score || 0);
		
		dailyActivityChart = new Chart(ctx, {
			type: 'bar',
			data: {
				labels: days.map(d => new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })),
				datasets: [
					{
						label: 'Sessions',
						data: sessions,
						backgroundColor: 'rgba(54, 162, 235, 0.7)',
						borderColor: 'rgba(54, 162, 235, 1)',
						borderWidth: 1,
						yAxisID: 'y'
					},
					{
						label: 'Average Score',
						data: avgScores,
						type: 'line',
						borderColor: 'rgba(255, 206, 86, 1)',
						backgroundColor: 'rgba(255, 206, 86, 0.2)',
						borderWidth: 2,
						tension: 0.4,
						yAxisID: 'y1'
					}
				]
			},
			options: {
				responsive: true,
				maintainAspectRatio: true,
				interaction: {
					mode: 'index',
					intersect: false
				},
				scales: {
					y: {
						type: 'linear',
						display: true,
						position: 'left',
						ticks: {
							color: '#fff',
							stepSize: 1
						},
						grid: {
							color: 'rgba(255, 255, 255, 0.1)'
						},
						title: {
							display: true,
							text: 'Sessions',
							color: '#fff'
						}
					},
					y1: {
						type: 'linear',
						display: true,
						position: 'right',
						suggestedMin: 0,
						suggestedMax: 100,
						ticks: {
							color: '#fff'
						},
						grid: {
							drawOnChartArea: false
						},
						title: {
							display: true,
							text: 'Score',
							color: '#fff'
						}
					},
					x: {
						ticks: {
							color: '#fff'
						},
						grid: {
							color: 'rgba(255, 255, 255, 0.1)'
						}
					}
				},
				plugins: {
					legend: {
						labels: {
							color: '#fff'
						}
					},
					tooltip: {
						backgroundColor: 'rgba(0, 0, 0, 0.8)',
						titleColor: '#fff',
						bodyColor: '#fff'
					}
				}
			}
		});
	}
	
	function renderTaskPerformanceChart(taskPerformance) {
		const canvas = document.getElementById('taskPerformanceChart');
		if (!canvas) return;
		
		const ctx = /** @type {HTMLCanvasElement} */ (canvas).getContext('2d');
		const tasks = Object.keys(taskPerformance).slice(0, 10); // Top 10 tasks
		const scores = tasks.map(t => taskPerformance[t].avg_score || 0);
		const sessionCounts = tasks.map(t => taskPerformance[t].sessions);
		
		taskPerformanceChart = new Chart(ctx, {
			type: 'bar',
			data: {
				labels: tasks.map(t => formatTaskName(t)),
				datasets: [
					{
						label: 'Average Score',
						data: scores,
						backgroundColor: scores.map(s => getScoreColor(s, 0.7)),
						borderColor: scores.map(s => getScoreColor(s, 1)),
						borderWidth: 1
					}
				]
			},
			options: {
				indexAxis: 'y',
				responsive: true,
				maintainAspectRatio: true,
				scales: {
					x: {
						suggestedMax: 100,
						ticks: {
							color: '#fff'
						},
						grid: {
							color: 'rgba(255, 255, 255, 0.1)'
						}
					},
					y: {
						ticks: {
							color: '#fff'
						},
						grid: {
							color: 'rgba(255, 255, 255, 0.1)'
						}
					}
				},
				plugins: {
					legend: {
						display: false
					},
					tooltip: {
						backgroundColor: 'rgba(0, 0, 0, 0.8)',
						titleColor: '#fff',
						bodyColor: '#fff',
						callbacks: {
							afterLabel: function(context) {
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
		return domain.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
	}
	
	function formatTaskName(task) {
		return task.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
	}
	
	function getScoreColor(score, alpha = 1) {
		if (score >= 80) return `rgba(76, 175, 80, ${alpha})`;
		if (score >= 60) return `rgba(255, 152, 0, ${alpha})`;
		return `rgba(244, 67, 54, ${alpha})`;
	}
	
	function getTrendIcon(trend) {
		if (trend === 'improving') return '📈';
		if (trend === 'declining') return '📉';
		return '➡️';
	}
	
	function getTrendClass(trend) {
		if (trend === 'improving') return 'trend-up';
		if (trend === 'declining') return 'trend-down';
		return 'trend-stable';
	}
	
	function formatDate(dateString) {
		return new Date(dateString).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		});
	}
	
	function exportToPDF() {
		// TODO: Implement PDF export
		alert('PDF export feature coming soon!');
	}
	
	function exportToCSV() {
		if (!selectedReport) return;
		
		const data = selectedReport.report_data;
		let csv = 'Progress Report\n\n';
		csv += `Patient: ${patientInfo?.patient?.name}\n`;
		csv += `Period: ${formatDate(selectedReport.period_start)} - ${formatDate(selectedReport.period_end)}\n`;
		csv += `Type: ${selectedReport.period_type}\n\n`;
		
		// Summary
		csv += '\nSummary\n';
		csv += 'Metric,Value\n';
		csv += `Total Sessions,${data.summary.total_sessions}\n`;
		csv += `Total Duration (minutes),${data.summary.total_duration_minutes}\n`;
		csv += `Average Score,${data.summary.avg_overall_score}\n`;
		csv += `Active Days,${data.summary.active_days}\n\n`;
		
		// Domain stats
		csv += '\nDomain Performance\n';
		csv += 'Domain,Sessions,Avg Score,Avg Accuracy,Avg Reaction Time,Trend\n';
		Object.entries(data.domain_stats).forEach(([domain, stats]) => {
			csv += `${formatDomainName(domain)},${stats.sessions_count},${stats.avg_score},${stats.avg_accuracy},${stats.avg_reaction_time},${stats.trend}\n`;
		});
		
		// Download
		const blob = new Blob([csv], { type: 'text/csv' });
		const url = window.URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `progress-report-${selectedReport.period_type}-${new Date().toISOString().split('T')[0]}.csv`;
		a.click();
		window.URL.revokeObjectURL(url);
	}
</script>

<div class="container">
	{#if loading}
		<div class="loading">
			<div class="spinner"></div>
			<p>Loading progress reports...</p>
		</div>
	{:else}
		<div class="header">
			<div class="header-left">
				<button class="btn-back" on:click={() => goto(`/doctor/patient/${patientId}`)}>
					← Back to Patient
				</button>
				<div>
					<h1>Progress Reports</h1>
					{#if patientInfo}
						<p class="subtitle">{patientInfo.patient?.name} - {patientInfo.patient?.email}</p>
					{/if}
				</div>
			</div>
			<div class="header-actions">
				<select bind:value={periodType} class="period-select">
					<option value="weekly">Weekly</option>
					<option value="monthly">Monthly</option>
				</select>
				<button class="btn-generate" on:click={generateReport} disabled={generating}>
					{generating ? '⏳ Generating...' : '📊 Generate New Report'}
				</button>
			</div>
		</div>

		{#if error}
			<div class="error-message">{error}</div>
		{/if}

		<div class="content">
			<!-- Reports List Sidebar -->
			<div class="sidebar">
				<h3>Report History</h3>
				{#if reports.length === 0}
					<div class="empty-state">
						<p>No reports yet</p>
						<small>Generate a new report to get started</small>
					</div>
				{:else}
					<div class="reports-list">
						{#each reports as report}
							<button
								class="report-item {selectedReport?.id === report.id ? 'active' : ''}"
								on:click={() => {
									selectedReport = report;
									commentaryText = report.doctor_commentary || '';
								}}
							>
								<div class="report-type">{report.period_type}</div>
								<div class="report-date">{formatDate(report.period_start)}</div>
								<small class="report-date-to">to {formatDate(report.period_end)}</small>
								{#if report.doctor_commentary}
									<div class="has-commentary">💬</div>
								{/if}
							</button>
						{/each}
					</div>
				{/if}
			</div>

			<!-- Report Details -->
			{#if selectedReport}
				<div class="main-content">
					<!-- Export Buttons -->
					<div class="export-bar">
						<button class="btn-export" on:click={exportToPDF}>📄 Export PDF</button>
						<button class="btn-export" on:click={exportToCSV}>📊 Export CSV</button>
					</div>

					<!-- Summary Cards -->
					<div class="summary-cards">
						<div class="summary-card">
							<div class="card-icon">🎯</div>
							<div class="card-value">{selectedReport.report_data.summary.total_sessions}</div>
							<div class="card-label">Total Sessions</div>
						</div>
						<div class="summary-card">
							<div class="card-icon">⏱️</div>
							<div class="card-value">{selectedReport.report_data.summary.total_duration_minutes.toFixed(0)}m</div>
							<div class="card-label">Training Time</div>
						</div>
						<div class="summary-card">
							<div class="card-icon">📈</div>
							<div class="card-value">{selectedReport.report_data.summary.avg_overall_score.toFixed(1)}%</div>
							<div class="card-label">Average Score</div>
						</div>
						<div class="summary-card">
							<div class="card-icon">📅</div>
							<div class="card-value">{selectedReport.report_data.summary.active_days}</div>
							<div class="card-label">Active Days</div>
						</div>
					</div>

					<!-- Charts Section -->
					<div class="charts-grid">
						<!-- Domain Performance Radar -->
						<div class="chart-container full-width">
							<h3>Cognitive Domain Performance</h3>
							<div class="chart-wrapper">
								<canvas id="domainChart"></canvas>
							</div>
						</div>

						<!-- Daily Activity -->
						<div class="chart-container full-width">
							<h3>Daily Activity & Scores</h3>
							<div class="chart-wrapper">
								<canvas id="dailyActivityChart"></canvas>
							</div>
						</div>

						<!-- Task Performance -->
						<div class="chart-container full-width">
							<h3>Top Task Performance</h3>
							<div class="chart-wrapper">
								<canvas id="taskPerformanceChart"></canvas>
							</div>
						</div>
					</div>

					<!-- Domain Details -->
					<div class="domain-details">
						<h3>Domain Statistics</h3>
						<div class="domain-grid">
							{#each Object.entries(selectedReport.report_data.domain_stats) as [domain, stats]}
								<div class="domain-card">
									<div class="domain-header">
										<h4>{formatDomainName(domain)}</h4>
										<span class="trend-badge {getTrendClass(stats.trend)}">
											{getTrendIcon(stats.trend)} {stats.trend}
										</span>
									</div>
									<div class="domain-stats">
										<div class="stat">
											<span class="stat-label">Sessions:</span>
											<span class="stat-value">{stats.sessions_count}</span>
										</div>
										<div class="stat">
											<span class="stat-label">Avg Score:</span>
											<span class="stat-value">{stats.avg_score.toFixed(1)}%</span>
										</div>
										<div class="stat">
											<span class="stat-label">Accuracy:</span>
											<span class="stat-value">{stats.avg_accuracy.toFixed(1)}%</span>
										</div>
										<div class="stat">
											<span class="stat-label">Reaction Time:</span>
											<span class="stat-value">{stats.avg_reaction_time.toFixed(0)}ms</span>
										</div>
										<div class="stat">
											<span class="stat-label">Difficulty:</span>
											<span class="stat-value">{stats.avg_difficulty.toFixed(1)}/10</span>
										</div>
									</div>
								</div>
							{/each}
						</div>
					</div>

					<!-- Doctor Commentary -->
					<div class="commentary-section">
						<div class="commentary-header">
							<h3>Doctor's Commentary</h3>
							<button class="btn-edit" on:click={() => editingCommentary = !editingCommentary}>
								{editingCommentary ? '❌ Cancel' : '✏️ Edit'}
							</button>
						</div>
						{#if editingCommentary}
							<div class="commentary-editor">
								<textarea
									bind:value={commentaryText}
									placeholder="Add your professional observations, recommendations, and notes about the patient's progress..."
									rows="8"
								></textarea>
								<button class="btn-save" on:click={saveCommentary}>💾 Save Commentary</button>
							</div>
						{:else}
							<div class="commentary-display">
								{#if selectedReport.doctor_commentary}
									<p>{selectedReport.doctor_commentary}</p>
								{:else}
									<p class="no-commentary">No commentary added yet. Click "Edit" to add your observations.</p>
								{/if}
							</div>
						{/if}
					</div>
				</div>
			{:else}
				<div class="main-content">
					<div class="empty-report">
						<div class="empty-icon">📊</div>
						<h3>No Report Selected</h3>
						<p>Select a report from the sidebar or generate a new one</p>
					</div>
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.container {
		min-height: 100vh;
		background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
		color: white;
		padding: 2rem;
	}

	.loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 50vh;
		gap: 1rem;
	}

	.spinner {
		width: 50px;
		height: 50px;
		border: 4px solid rgba(255, 255, 255, 0.1);
		border-top-color: #4fc3f7;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
		flex-wrap: wrap;
		gap: 1rem;
	}

	.header-left {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.header-actions {
		display: flex;
		gap: 1rem;
		align-items: center;
	}

	.btn-back {
		background: rgba(255, 255, 255, 0.1);
		border: 1px solid rgba(255, 255, 255, 0.2);
		color: white;
		padding: 0.5rem 1rem;
		border-radius: 8px;
		cursor: pointer;
		transition: all 0.3s;
	}

	.btn-back:hover {
		background: rgba(255, 255, 255, 0.2);
		transform: translateX(-2px);
	}

	h1 {
		margin: 0;
		font-size: 2rem;
	}

	.subtitle {
		margin: 0.5rem 0 0 0;
		opacity: 0.7;
		font-size: 0.9rem;
	}

	.period-select {
		background: rgba(255, 255, 255, 0.1);
		border: 1px solid rgba(255, 255, 255, 0.2);
		color: white;
		padding: 0.75rem 1rem;
		border-radius: 8px;
		cursor: pointer;
		font-size: 1rem;
	}

	.btn-generate {
		background: linear-gradient(135deg, #4fc3f7, #2196f3);
		border: none;
		color: white;
		padding: 0.75rem 1.5rem;
		border-radius: 8px;
		cursor: pointer;
		font-weight: 600;
		transition: all 0.3s;
		font-size: 1rem;
	}

	.btn-generate:hover:not(:disabled) {
		transform: translateY(-2px);
		box-shadow: 0 10px 25px rgba(79, 195, 247, 0.3);
	}

	.btn-generate:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.error-message {
		background: rgba(244, 67, 54, 0.2);
		border: 1px solid rgba(244, 67, 54, 0.5);
		color: #ff5252;
		padding: 1rem;
		border-radius: 8px;
		margin-bottom: 1rem;
	}

	.content {
		display: grid;
		grid-template-columns: 280px 1fr;
		gap: 2rem;
	}

	.sidebar {
		background: rgba(255, 255, 255, 0.05);
		border-radius: 12px;
		padding: 1.5rem;
		height: fit-content;
		max-height: calc(100vh - 200px);
		overflow-y: auto;
	}

	.sidebar h3 {
		margin-top: 0;
		margin-bottom: 1rem;
		font-size: 1.2rem;
	}

	.empty-state {
		text-align: center;
		padding: 2rem 1rem;
		opacity: 0.5;
	}

	.reports-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.report-item {
		background: rgba(255, 255, 255, 0.05);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 8px;
		padding: 1rem;
		cursor: pointer;
		transition: all 0.3s;
		text-align: left;
		color: white;
		position: relative;
	}

	.report-item:hover {
		background: rgba(255, 255, 255, 0.1);
		transform: translateX(4px);
	}

	.report-item.active {
		background: linear-gradient(135deg, rgba(79, 195, 247, 0.2), rgba(33, 150, 243, 0.2));
		border-color: #4fc3f7;
	}

	.report-type {
		font-weight: 600;
		text-transform: capitalize;
		margin-bottom: 0.25rem;
	}

	.report-date {
		font-size: 0.9rem;
		opacity: 0.8;
	}

	.report-date-to {
		font-size: 0.8rem;
		opacity: 0.6;
	}

	.has-commentary {
		position: absolute;
		top: 0.5rem;
		right: 0.5rem;
		font-size: 1.2rem;
	}

	.main-content {
		background: rgba(255, 255, 255, 0.05);
		border-radius: 12px;
		padding: 2rem;
	}

	.export-bar {
		display: flex;
		gap: 1rem;
		margin-bottom: 2rem;
		justify-content: flex-end;
	}

	.btn-export {
		background: rgba(255, 255, 255, 0.1);
		border: 1px solid rgba(255, 255, 255, 0.2);
		color: white;
		padding: 0.5rem 1rem;
		border-radius: 8px;
		cursor: pointer;
		transition: all 0.3s;
	}

	.btn-export:hover {
		background: rgba(255, 255, 255, 0.2);
		transform: translateY(-2px);
	}

	.summary-cards {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1.5rem;
		margin-bottom: 2rem;
	}

	.summary-card {
		background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 12px;
		padding: 1.5rem;
		text-align: center;
	}

	.card-icon {
		font-size: 2.5rem;
		margin-bottom: 0.5rem;
	}

	.card-value {
		font-size: 2rem;
		font-weight: 700;
		margin-bottom: 0.25rem;
		background: linear-gradient(135deg, #4fc3f7, #2196f3);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
	}

	.card-label {
		opacity: 0.7;
		font-size: 0.9rem;
	}

	.charts-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
		gap: 2rem;
		margin-bottom: 2rem;
	}

	.chart-container {
		background: rgba(0, 0, 0, 0.2);
		border-radius: 12px;
		padding: 1.5rem;
		border: 1px solid rgba(255, 255, 255, 0.1);
	}

	.chart-container.full-width {
		grid-column: 1 / -1;
	}

	.chart-container h3 {
		margin-top: 0;
		margin-bottom: 1rem;
	}

	.chart-wrapper {
		position: relative;
		height: 350px;
	}

	.domain-details {
		margin-bottom: 2rem;
	}

	.domain-details h3 {
		margin-bottom: 1rem;
	}

	.domain-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		gap: 1.5rem;
	}

	.domain-card {
		background: linear-gradient(135deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.03));
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 12px;
		padding: 1.5rem;
	}

	.domain-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		padding-bottom: 0.75rem;
		border-bottom: 1px solid rgba(255, 255, 255, 0.1);
	}

	.domain-header h4 {
		margin: 0;
		font-size: 1.1rem;
	}

	.trend-badge {
		padding: 0.25rem 0.75rem;
		border-radius: 20px;
		font-size: 0.85rem;
		font-weight: 600;
	}

	.trend-up {
		background: rgba(76, 175, 80, 0.2);
		color: #4caf50;
	}

	.trend-down {
		background: rgba(244, 67, 54, 0.2);
		color: #f44336;
	}

	.trend-stable {
		background: rgba(255, 152, 0, 0.2);
		color: #ff9800;
	}

	.domain-stats {
		display: grid;
		gap: 0.5rem;
	}

	.stat {
		display: flex;
		justify-content: space-between;
	}

	.stat-label {
		opacity: 0.7;
	}

	.stat-value {
		font-weight: 600;
	}

	.commentary-section {
		background: rgba(0, 0, 0, 0.2);
		border-radius: 12px;
		padding: 1.5rem;
		border: 1px solid rgba(255, 255, 255, 0.1);
	}

	.commentary-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	.commentary-header h3 {
		margin: 0;
	}

	.btn-edit {
		background: rgba(255, 255, 255, 0.1);
		border: 1px solid rgba(255, 255, 255, 0.2);
		color: white;
		padding: 0.5rem 1rem;
		border-radius: 8px;
		cursor: pointer;
		transition: all 0.3s;
	}

	.btn-edit:hover {
		background: rgba(255, 255, 255, 0.2);
	}

	.commentary-editor textarea {
		width: 100%;
		background: rgba(0, 0, 0, 0.3);
		border: 1px solid rgba(255, 255, 255, 0.2);
		color: white;
		padding: 1rem;
		border-radius: 8px;
		font-family: inherit;
		font-size: 1rem;
		resize: vertical;
		margin-bottom: 1rem;
	}

	.btn-save {
		background: linear-gradient(135deg, #4caf50, #45a049);
		border: none;
		color: white;
		padding: 0.75rem 1.5rem;
		border-radius: 8px;
		cursor: pointer;
		font-weight: 600;
		transition: all 0.3s;
	}

	.btn-save:hover {
		transform: translateY(-2px);
		box-shadow: 0 10px 25px rgba(76, 175, 80, 0.3);
	}

	.commentary-display {
		line-height: 1.6;
	}

	.no-commentary {
		opacity: 0.5;
		font-style: italic;
	}

	.empty-report {
		text-align: center;
		padding: 4rem 2rem;
	}

	.empty-icon {
		font-size: 4rem;
		margin-bottom: 1rem;
	}

	.empty-report h3 {
		margin-bottom: 0.5rem;
	}

	.empty-report p {
		opacity: 0.7;
	}

	@media (max-width: 1024px) {
		.content {
			grid-template-columns: 1fr;
		}

		.sidebar {
			max-height: 300px;
		}

		.charts-grid {
			grid-template-columns: 1fr;
		}
	}

	@media (max-width: 768px) {
		.header {
			flex-direction: column;
			align-items: flex-start;
		}

		.summary-cards {
			grid-template-columns: repeat(2, 1fr);
		}

		.domain-grid {
			grid-template-columns: 1fr;
		}
	}
</style>

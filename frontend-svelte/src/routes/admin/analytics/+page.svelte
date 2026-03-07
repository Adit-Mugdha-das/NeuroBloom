<script>
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	import { user } from '$lib/stores';
	import { Chart, registerables } from 'chart.js';
	import { onDestroy, onMount, tick } from 'svelte';

	Chart.register(...registerables);

	let admin = null;
	let loading = true;
	let error = '';
	let successMsg = '';
	let riskAlerts = [];
	let riskActionLoading = {};
	let stats = {
		total_patients: 0,
		total_doctors: 0,
		active_patients_today: 0,
		completed_sessions: 0,
		average_improvement_score: 0,
		high_risk_patients: 0,
		high_risk_list: [],
		most_used_tasks: [],
		patient_activity: { labels: [], sessions: [], patients: [] },
		performance_trend: { labels: [], scores: [] },
		fatigue_trend: { labels: [], fatigue_levels: [], scores: [] },
		completion_trend: { labels: [], rates: [], completed_sessions: [] }
	};

	let activityChartCanvas;
	let activityChart;
	let performanceChartCanvas;
	let performanceChart;
	let fatigueChartCanvas;
	let fatigueChart;
	let completionChartCanvas;
	let completionChart;

	onMount(async () => {
		const currentUser = $user;
		if (!currentUser || currentUser.role !== 'admin') {
			goto('/login');
			return;
		}

		admin = currentUser;
		await loadAnalytics();
	});

	async function loadAnalytics() {
		try {
			const [statsResponse, alertsResponse] = await Promise.all([
				api.get(`/api/admin/stats?admin_id=${admin.id}`),
				api.get(`/api/admin/risk-alerts?admin_id=${admin.id}`)
			]);
			stats = statsResponse.data;
			riskAlerts = alertsResponse.data.alerts;
			await tick();
			renderActivityChart();
			renderPerformanceChart();
			renderFatigueChart();
			renderCompletionChart();
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Failed to load analytics';
		} finally {
			loading = false;
		}
	}

	function isRiskActionLoading(patientId, action) {
		return Boolean(riskActionLoading[`${patientId}:${action}`]);
	}

	async function runRiskAction(patientId, action) {
		error = '';
		successMsg = '';
		const key = `${patientId}:${action}`;
		riskActionLoading = { ...riskActionLoading, [key]: true };

		const endpoints = {
			notify: 'notify-doctor',
			escalate: 'escalate',
			review: 'mark-reviewed'
		};

		try {
			const response = await api.post(`/api/admin/risk-alerts/${patientId}/${endpoints[action]}?admin_id=${admin.id}`);
			successMsg = response.data.message;
			const alertsResponse = await api.get(`/api/admin/risk-alerts?admin_id=${admin.id}`);
			riskAlerts = alertsResponse.data.alerts;
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Risk action failed';
		} finally {
			riskActionLoading = { ...riskActionLoading, [key]: false };
		}
	}

	function hasSeriesData(values = []) {
		return Array.isArray(values) && values.some((value) => Number(value) > 0);
	}

	function hasActivityData() {
		return hasSeriesData(stats.patient_activity.sessions) || hasSeriesData(stats.patient_activity.patients);
	}

	function hasPerformanceData() {
		return hasSeriesData(stats.performance_trend.scores);
	}

	function hasFatigueData() {
		return hasSeriesData(stats.fatigue_trend.fatigue_levels);
	}

	function hasCompletionData() {
		return hasSeriesData(stats.completion_trend.rates) || hasSeriesData(stats.completion_trend.completed_sessions);
	}

	function renderActivityChart() {
		if (!activityChartCanvas || !hasActivityData()) {
			return;
		}

		if (activityChart) {
			activityChart.destroy();
		}

		activityChart = new Chart(activityChartCanvas, {
			type: 'bar',
			data: {
				labels: stats.patient_activity.labels,
				datasets: [
					{
						label: 'Completed sessions',
						data: stats.patient_activity.sessions,
						backgroundColor: 'rgba(30, 64, 175, 0.78)',
						borderRadius: 10,
						borderSkipped: false,
						barThickness: 24,
						order: 2
					},
					{
						label: 'Active patients',
						data: stats.patient_activity.patients,
						type: 'line',
						borderColor: '#0f172a',
						backgroundColor: 'rgba(15, 23, 42, 0.14)',
						pointBackgroundColor: '#ffffff',
						pointBorderColor: '#0f172a',
						pointBorderWidth: 2,
						pointRadius: 4,
						tension: 0.36,
						fill: false,
						order: 1
					}
				]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				plugins: {
					legend: {
						position: 'top',
						align: 'start',
						labels: {
							boxWidth: 12,
							usePointStyle: true,
							pointStyle: 'circle',
							color: '#334155',
							font: { size: 12, weight: 600 }
						}
					},
					tooltip: {
						backgroundColor: 'rgba(15, 23, 42, 0.94)',
						padding: 12,
						cornerRadius: 12
					}
				},
				scales: {
					x: {
						grid: { display: false },
						border: { display: false },
						ticks: { color: '#64748b', font: { size: 11, weight: 600 } }
					},
					y: {
						beginAtZero: true,
						grid: { color: 'rgba(148, 163, 184, 0.16)' },
						border: { display: false },
						ticks: { precision: 0, color: '#64748b', font: { size: 11 } }
					}
				}
			}
		});
	}

	function renderPerformanceChart() {
		if (!performanceChartCanvas || !hasPerformanceData()) {
			return;
		}

		if (performanceChart) {
			performanceChart.destroy();
		}

		const context = performanceChartCanvas.getContext('2d');
		const gradient = context.createLinearGradient(0, 0, 0, 300);
		gradient.addColorStop(0, 'rgba(15, 118, 110, 0.24)');
		gradient.addColorStop(1, 'rgba(15, 118, 110, 0.02)');

		performanceChart = new Chart(performanceChartCanvas, {
			type: 'line',
			data: {
				labels: stats.performance_trend.labels,
				datasets: [
					{
						label: 'Average score',
						data: stats.performance_trend.scores,
						borderColor: '#0f766e',
						backgroundColor: gradient,
						fill: true,
						pointRadius: 0,
						pointHoverRadius: 4,
						borderWidth: 3,
						tension: 0.38
					}
				]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				plugins: {
					legend: { display: false },
					tooltip: {
						backgroundColor: 'rgba(15, 23, 42, 0.94)',
						padding: 12,
						cornerRadius: 12,
						displayColors: false
					}
				},
				scales: {
					x: {
						grid: { display: false },
						border: { display: false },
						ticks: { color: '#64748b', maxTicksLimit: 7, font: { size: 11 } }
					},
					y: {
						beginAtZero: true,
						suggestedMax: 100,
						grid: { color: 'rgba(148, 163, 184, 0.14)' },
						border: { display: false },
						ticks: { color: '#64748b', font: { size: 11 } }
					}
				}
			}
		});
	}

	function renderFatigueChart() {
		if (!fatigueChartCanvas || !hasFatigueData()) {
			return;
		}

		if (fatigueChart) {
			fatigueChart.destroy();
		}

		fatigueChart = new Chart(fatigueChartCanvas, {
			type: 'line',
			data: {
				labels: stats.fatigue_trend.labels,
				datasets: [
					{
						label: 'Average fatigue level',
						data: stats.fatigue_trend.fatigue_levels,
						borderColor: '#dc2626',
						backgroundColor: 'rgba(220, 38, 38, 0.12)',
						yAxisID: 'y',
						fill: true,
						pointRadius: 3,
						borderWidth: 2.5,
						tension: 0.35
					},
					{
						label: 'Average score',
						data: stats.fatigue_trend.scores,
						borderColor: '#2563eb',
						backgroundColor: 'rgba(37, 99, 235, 0.08)',
						yAxisID: 'y1',
						fill: false,
						pointRadius: 0,
						borderDash: [7, 5],
						borderWidth: 2,
						tension: 0.28
					}
				]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				plugins: {
					legend: {
						position: 'top',
						align: 'start',
						labels: {
							boxWidth: 12,
							usePointStyle: true,
							color: '#334155',
							font: { size: 12, weight: 600 }
						}
					},
					tooltip: {
						backgroundColor: 'rgba(15, 23, 42, 0.94)',
						padding: 12,
						cornerRadius: 12
					}
				},
				scales: {
					x: {
						grid: { display: false },
						border: { display: false },
						ticks: { color: '#64748b', maxTicksLimit: 7, font: { size: 11 } }
					},
					y: {
						position: 'left',
						min: 0,
						max: 10,
						grid: { color: 'rgba(148, 163, 184, 0.16)' },
						border: { display: false },
						ticks: { color: '#64748b', font: { size: 11 } }
					},
					y1: {
						position: 'right',
						min: 0,
						max: 100,
						grid: { display: false },
						border: { display: false },
						ticks: { color: '#94a3b8', font: { size: 11 } }
					}
				}
			}
		});
	}

	function renderCompletionChart() {
		if (!completionChartCanvas || !hasCompletionData()) {
			return;
		}

		if (completionChart) {
			completionChart.destroy();
		}

		completionChart = new Chart(completionChartCanvas, {
			type: 'bar',
			data: {
				labels: stats.completion_trend.labels,
				datasets: [
					{
						label: 'Completion rate %',
						data: stats.completion_trend.rates,
						backgroundColor: 'rgba(14, 165, 233, 0.72)',
						borderRadius: 10,
						borderSkipped: false,
						barThickness: 22,
						yAxisID: 'y'
					},
					{
						label: 'Completed sessions',
						data: stats.completion_trend.completed_sessions,
						type: 'line',
						borderColor: '#0f172a',
						backgroundColor: 'rgba(15, 23, 42, 0.1)',
						pointRadius: 3,
						pointBackgroundColor: '#ffffff',
						pointBorderColor: '#0f172a',
						pointBorderWidth: 2,
						tension: 0.3,
						yAxisID: 'y1'
					}
				]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				plugins: {
					legend: {
						position: 'top',
						align: 'start',
						labels: {
							boxWidth: 12,
							usePointStyle: true,
							color: '#334155',
							font: { size: 12, weight: 600 }
						}
					},
					tooltip: {
						backgroundColor: 'rgba(15, 23, 42, 0.94)',
						padding: 12,
						cornerRadius: 12
					}
				},
				scales: {
					x: {
						grid: { display: false },
						border: { display: false },
						ticks: { color: '#64748b', maxTicksLimit: 7, font: { size: 11 } }
					},
					y: {
						position: 'left',
						beginAtZero: true,
						max: 100,
						grid: { color: 'rgba(148, 163, 184, 0.16)' },
						border: { display: false },
						ticks: { color: '#64748b', callback: (value) => `${value}%`, font: { size: 11 } }
					},
					y1: {
						position: 'right',
						beginAtZero: true,
						grid: { display: false },
						border: { display: false },
						ticks: { color: '#94a3b8', precision: 0, font: { size: 11 } }
					}
				}
			}
		});
	}

	function logout() {
		user.set(null);
		goto('/login');
	}

	onDestroy(() => {
		if (activityChart) activityChart.destroy();
		if (performanceChart) performanceChart.destroy();
		if (fatigueChart) fatigueChart.destroy();
		if (completionChart) completionChart.destroy();
	});
</script>

<div class="admin-layout">
	<aside class="sidebar">
		<div class="sidebar-brand">
			<span class="brand-icon">🏥</span>
			<span class="brand-name">NeuroBloom Admin</span>
		</div>
		<nav class="sidebar-nav">
			<a href="/admin/dashboard" class="nav-item">
				<span class="nav-icon">📊</span> Dashboard
			</a>
			<a href="/admin/analytics" class="nav-item active">
				<span class="nav-icon">📈</span> System Analytics
			</a>
			<a href="/admin/doctors" class="nav-item">
				<span class="nav-icon">👨‍⚕️</span> Doctor Management
			</a>
			<a href="/admin/patients" class="nav-item">
				<span class="nav-icon">👤</span> Patient Management
			</a>
			<a href="/admin/departments" class="nav-item">
				<span class="nav-icon">🏢</span> Departments
			</a>
			<a href="/admin/interventions" class="nav-item">
				<span class="nav-icon">🩺</span> Interventions
			</a>
			<a href="/admin/messages" class="nav-item">
				<span class="nav-icon">💬</span> Message Audit
			</a>
			<a href="/admin/audit-logs" class="nav-item">
				<span class="nav-icon">📋</span> Audit Logs
			</a>
			<a href="/admin/system-health" class="nav-item">
				<span class="nav-icon">🖥️</span> System Health
			</a>
			<a href="/admin/notifications" class="nav-item">
				<span class="nav-icon">🔔</span> Notification Center
			</a>
		</nav>
		<button class="logout-btn" on:click={logout}>
			<span>🚪</span> Logout
		</button>
	</aside>

	<main class="main-content">
		<header class="topbar">
			<div>
				<h1 class="page-title">System Analytics</h1>
				<p class="page-subtitle">Focused system-wide analytics page with only the core operational and clinical trends.</p>
			</div>
			<div class="admin-info">
				<span class="admin-avatar">🏥</span>
				<span>{admin?.full_name || admin?.email}</span>
			</div>
		</header>

		{#if error}
			<div class="alert error">{error}</div>
		{/if}
		{#if successMsg}
			<div class="alert success">{successMsg}</div>
		{/if}

		{#if loading}
			<div class="loading-grid">
				{#each Array(6) as _}
					<div class="stat-card skeleton"></div>
				{/each}
			</div>
		{:else}
			<div class="stats-grid">
				<div class="stat-card blue">
					<div class="stat-icon">👥</div>
					<div class="stat-body"><p class="stat-label">Total Patients</p><p class="stat-value">{stats.total_patients}</p></div>
				</div>
				<div class="stat-card purple">
					<div class="stat-icon">👨‍⚕️</div>
					<div class="stat-body"><p class="stat-label">Total Doctors</p><p class="stat-value">{stats.total_doctors}</p></div>
				</div>
				<div class="stat-card emerald">
					<div class="stat-icon">📍</div>
					<div class="stat-body"><p class="stat-label">Active Patients Today</p><p class="stat-value">{stats.active_patients_today}</p></div>
				</div>
				<div class="stat-card slate">
					<div class="stat-icon">🧠</div>
					<div class="stat-body"><p class="stat-label">Sessions Completed</p><p class="stat-value">{stats.completed_sessions}</p></div>
				</div>
				<div class="stat-card teal">
					<div class="stat-icon">📈</div>
					<div class="stat-body"><p class="stat-label">Average Improvement</p><p class="stat-value small">{stats.average_improvement_score >= 0 ? '+' : ''}{stats.average_improvement_score}</p></div>
				</div>
				<div class="stat-card red">
					<div class="stat-icon">⚠️</div>
					<div class="stat-body"><p class="stat-label">High-Risk Patients</p><p class="stat-value">{stats.high_risk_patients}</p></div>
				</div>
			</div>

			<section class="risk-monitor-panel">
				<div class="panel-header">
					<div>
						<p class="panel-kicker rose-text">Risk Monitoring</p>
						<h2>High-Risk Patients</h2>
						<p class="panel-copy">System-wide alerts are consolidated here so the admin can quickly notify the assigned doctor, escalate urgent cases, or mark alerts as reviewed without adding workflow clutter elsewhere.</p>
					</div>
					<div class="panel-chip rose-chip">{riskAlerts.length} active alerts</div>
				</div>

				<div class="risk-monitor-list">
					{#if riskAlerts.length === 0}
						<div class="empty-risk-state">No patients are currently flagged as high risk.</div>
					{:else}
						{#each riskAlerts as alert}
							<div class="risk-monitor-row">
								<div class="risk-monitor-main">
									<div class="risk-monitor-top">
										<div>
											<h3>{alert.name}</h3>
											<p class="risk-summary">{alert.alert_summary}</p>
										</div>
										<div class="risk-status-group">
											<span class="status-chip {alert.alert_status}">{alert.alert_status}</span>
											<span class="metric-chip">Risk score {alert.risk_score}</span>
										</div>
									</div>

									<div class="risk-monitor-meta">
										<span>{alert.email}</span>
										<span>Doctor: {alert.assigned_doctor_name || 'Unassigned'}</span>
										{#if alert.recent_avg_fatigue !== null}
											<span>Fatigue {alert.recent_avg_fatigue}</span>
										{/if}
										{#if alert.recent_avg_score !== null}
											<span>Score {alert.recent_avg_score}</span>
										{/if}
									</div>

									<p class="risk-reasons">{alert.reasons.join(' • ')}</p>
								</div>

								<div class="risk-monitor-actions">
									<button
										class="action-btn secondary"
										on:click={() => runRiskAction(alert.id, 'notify')}
										disabled={!alert.assigned_doctor_id || alert.doctor_notified || isRiskActionLoading(alert.id, 'notify')}
									>
										{#if isRiskActionLoading(alert.id, 'notify')}Sending...{:else if alert.doctor_notified}Doctor notified{:else}Notify doctor{/if}
									</button>
									<button
										class="action-btn danger"
										on:click={() => runRiskAction(alert.id, 'escalate')}
										disabled={alert.alert_status === 'escalated' || isRiskActionLoading(alert.id, 'escalate')}
									>
										{#if isRiskActionLoading(alert.id, 'escalate')}Escalating...{:else if alert.alert_status === 'escalated'}Escalated{:else}Escalate case{/if}
									</button>
									<button
										class="action-btn success"
										on:click={() => runRiskAction(alert.id, 'review')}
										disabled={alert.alert_status === 'reviewed' || isRiskActionLoading(alert.id, 'review')}
									>
										{#if isRiskActionLoading(alert.id, 'review')}Saving...{:else if alert.alert_status === 'reviewed'}Reviewed{:else}Mark reviewed{/if}
									</button>
								</div>
							</div>
						{/each}
					{/if}
				</div>
			</section>

			<section class="insights-layout">
				<div class="insight-panel">
					<div class="panel-header compact">
						<div>
							<p class="panel-kicker">Task Usage</p>
							<h2>Most Used Tasks</h2>
						</div>
					</div>
					<div class="task-list">
						{#if stats.most_used_tasks.length === 0}
							<p class="empty-copy">No completed task data is available yet.</p>
						{:else}
							{#each stats.most_used_tasks as task, index}
								<div class="task-row">
									<div class="task-rank">{index + 1}</div>
									<div class="task-meta">
										<p class="task-name">{task.task}</p>
										<p class="task-sub">Completed sessions</p>
									</div>
									<div class="task-count">{task.count}</div>
								</div>
							{/each}
						{/if}
					</div>
				</div>

			</section>

			<section class="chart-grid">
				<div class="chart-panel">
					<div class="panel-header">
						<div>
							<p class="panel-kicker">Activity</p>
							<h2>Patient Activity</h2>
							<p class="panel-copy">Seven-day view of completed sessions and distinct active patients.</p>
						</div>
						<div class="panel-chip">Last 7 days</div>
					</div>
					{#if hasActivityData()}
						<div class="chart-wrap"><canvas bind:this={activityChartCanvas}></canvas></div>
					{:else}
						<div class="empty-state">No activity data is available yet.</div>
					{/if}
				</div>

				<div class="chart-panel">
					<div class="panel-header">
						<div>
							<p class="panel-kicker teal-text">Performance</p>
							<h2>Cognitive Performance Trend</h2>
							<p class="panel-copy">Average completed-session score over the last 14 days.</p>
						</div>
						<div class="panel-chip teal-chip">14 days</div>
					</div>
					{#if hasPerformanceData()}
						<div class="chart-wrap"><canvas bind:this={performanceChartCanvas}></canvas></div>
					{:else}
						<div class="empty-state">No performance trend is available yet.</div>
					{/if}
				</div>

				<div class="chart-panel">
					<div class="panel-header">
						<div>
							<p class="panel-kicker rose-text">Fatigue</p>
							<h2>Fatigue Trends</h2>
							<p class="panel-copy">Fatigue questionnaire signals compared with average performance.</p>
						</div>
						<div class="panel-chip rose-chip">Context data</div>
					</div>
					{#if hasFatigueData()}
						<div class="chart-wrap"><canvas bind:this={fatigueChartCanvas}></canvas></div>
					{:else}
						<div class="empty-state">No fatigue questionnaire data has been recorded yet.</div>
					{/if}
				</div>

				<div class="chart-panel">
					<div class="panel-header">
						<div>
							<p class="panel-kicker sky-text">Completion</p>
							<h2>Task Completion Rate</h2>
							<p class="panel-copy">Completion percentage and completed-session totals across the last 14 days.</p>
						</div>
						<div class="panel-chip sky-chip">14 days</div>
					</div>
					{#if hasCompletionData()}
						<div class="chart-wrap"><canvas bind:this={completionChartCanvas}></canvas></div>
					{:else}
						<div class="empty-state">No completion trend is available yet.</div>
					{/if}
				</div>
			</section>
		{/if}
	</main>
</div>

<style>
	.admin-layout {
		display: flex;
		min-height: 100vh;
		background: #f0f4f8;
		font-family: 'Inter', sans-serif;
	}

	.sidebar {
		width: 240px;
		min-height: 100vh;
		background: #1e293b;
		color: #e2e8f0;
		display: flex;
		flex-direction: column;
		position: fixed;
		top: 0;
		left: 0;
		bottom: 0;
		z-index: 10;
	}

	.sidebar-brand {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		padding: 1.4rem 1.2rem;
		background: #0f172a;
		font-weight: 700;
		font-size: 1rem;
		letter-spacing: 0.02em;
	}

	.brand-icon { font-size: 1.4rem; }

	.sidebar-nav {
		flex: 1;
		padding: 1rem 0.75rem;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.nav-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.65rem 0.9rem;
		border-radius: 8px;
		color: #94a3b8;
		text-decoration: none;
		font-size: 0.9rem;
		font-weight: 500;
		transition: all 0.2s;
	}

	.nav-item:hover,
	.nav-item.active {
		background: #334155;
		color: #f1f5f9;
	}

	.nav-icon { font-size: 1.1rem; }

	.logout-btn {
		margin: 0.75rem;
		padding: 0.65rem 0.9rem;
		background: transparent;
		border: 1px solid #334155;
		border-radius: 8px;
		color: #94a3b8;
		cursor: pointer;
		font-size: 0.9rem;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.logout-btn:hover { background: #7f1d1d; color: #fca5a5; border-color: #7f1d1d; }

	.main-content {
		flex: 1;
		margin-left: 240px;
		display: flex;
		flex-direction: column;
	}

	.topbar {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1.25rem 2rem;
		background: white;
		border-bottom: 1px solid #e2e8f0;
		position: sticky;
		top: 0;
		z-index: 5;
	}

	.page-title {
		font-size: 1.45rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0;
	}

	.page-subtitle {
		margin: 0.3rem 0 0;
		font-size: 0.9rem;
		color: #64748b;
	}

	.admin-info {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.9rem;
		color: #475569;
	}

	.admin-avatar { font-size: 1.3rem; }

	.alert.error {
		margin: 1.5rem 2rem 0;
		padding: 0.9rem 1.2rem;
		background: #fef2f2;
		border: 1px solid #fecaca;
		border-radius: 8px;
		color: #b91c1c;
	}

	.alert.success {
		margin: 1rem 2rem 0;
		padding: 0.9rem 1.2rem;
		background: #ecfdf5;
		border: 1px solid #a7f3d0;
		border-radius: 8px;
		color: #065f46;
	}

	.stats-grid,
	.loading-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
		gap: 1.25rem;
		padding: 2rem 2rem 0;
	}

	.stat-card {
		background: white;
		border-radius: 12px;
		padding: 1.4rem 1.2rem;
		display: flex;
		align-items: center;
		gap: 1rem;
		box-shadow: 0 1px 4px rgba(0, 0, 0, 0.07);
		border-top: 3px solid transparent;
	}

	.stat-card.blue { border-top-color: #3b82f6; }
	.stat-card.purple { border-top-color: #a855f7; }
	.stat-card.emerald { border-top-color: #059669; }
	.stat-card.slate { border-top-color: #475569; }
	.stat-card.teal { border-top-color: #14b8a6; }
	.stat-card.red { border-top-color: #dc2626; }
	.stat-card.skeleton { height: 96px; background: #f1f5f9; animation: pulse 1.4s infinite; }

	.stat-icon { font-size: 2rem; }
	.stat-label { font-size: 0.78rem; color: #64748b; margin: 0 0 0.25rem; text-transform: uppercase; letter-spacing: 0.05em; }
	.stat-value { font-size: 2rem; font-weight: 700; color: #1e293b; margin: 0; }
	.stat-value.small { font-size: 1.65rem; }

	.risk-monitor-panel {
		margin: 2rem 2rem 0;
		background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(255,247,247,0.98));
		border: 1px solid #fecaca;
		border-radius: 18px;
		padding: 1.35rem;
		box-shadow: 0 18px 36px rgba(15, 23, 42, 0.05);
	}

	.risk-monitor-list {
		display: grid;
		gap: 0.85rem;
	}

	.empty-risk-state {
		padding: 1.25rem;
		border-radius: 14px;
		background: #fffafa;
		border: 1px dashed #fecaca;
		color: #7f1d1d;
		font-size: 0.92rem;
	}

	.risk-monitor-row {
		display: grid;
		grid-template-columns: minmax(0, 1fr) auto;
		gap: 1rem;
		padding: 1rem;
		border-radius: 16px;
		background: #fff;
		border: 1px solid #fee2e2;
	}

	.risk-monitor-top {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: flex-start;
	}

	.risk-monitor-top h3 {
		margin: 0;
		font-size: 1rem;
		color: #0f172a;
	}

	.risk-summary {
		margin: 0.3rem 0 0;
		font-size: 0.9rem;
		font-weight: 600;
		color: #991b1b;
	}

	.risk-status-group {
		display: flex;
		gap: 0.45rem;
		flex-wrap: wrap;
		justify-content: flex-end;
	}

	.status-chip,
	.metric-chip {
		display: inline-flex;
		align-items: center;
		padding: 0.3rem 0.6rem;
		border-radius: 999px;
		font-size: 0.74rem;
		font-weight: 700;
	}

	.status-chip.open {
		background: #fef3c7;
		color: #92400e;
	}

	.status-chip.escalated {
		background: #fee2e2;
		color: #991b1b;
	}

	.status-chip.reviewed {
		background: #dcfce7;
		color: #166534;
	}

	.metric-chip {
		background: #e2e8f0;
		color: #334155;
	}

	.risk-monitor-meta {
		margin-top: 0.65rem;
		display: flex;
		flex-wrap: wrap;
		gap: 0.8rem;
		font-size: 0.8rem;
		color: #64748b;
	}

	.risk-monitor-actions {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
		justify-content: center;
		min-width: 150px;
	}

	.action-btn {
		border: 1px solid transparent;
		border-radius: 10px;
		padding: 0.7rem 0.85rem;
		font-size: 0.82rem;
		font-weight: 700;
		cursor: pointer;
		transition: background 0.2s, border-color 0.2s, color 0.2s;
	}

	.action-btn.secondary {
		background: #eff6ff;
		border-color: #bfdbfe;
		color: #1d4ed8;
	}

	.action-btn.danger {
		background: #fef2f2;
		border-color: #fecaca;
		color: #b91c1c;
	}

	.action-btn.success {
		background: #ecfdf5;
		border-color: #a7f3d0;
		color: #047857;
	}

	.action-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.insights-layout {
		padding: 2rem 2rem 0;
		display: grid;
		grid-template-columns: minmax(0, 1fr);
		gap: 1.25rem;
	}

	.insight-panel,
	.chart-panel {
		background: white;
		border: 1px solid #e2e8f0;
		border-radius: 18px;
		padding: 1.35rem;
		box-shadow: 0 18px 36px rgba(15, 23, 42, 0.05);
	}

	.panel-header {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: flex-start;
		margin-bottom: 1rem;
	}

	.panel-header.compact { margin-bottom: 0.8rem; }

	.panel-kicker {
		margin: 0 0 0.35rem;
		font-size: 0.74rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #1d4ed8;
	}

	.panel-header h2 {
		margin: 0;
		font-size: 1.15rem;
		color: #0f172a;
	}

	.panel-copy,
	.empty-copy {
		margin: 0.35rem 0 0;
		font-size: 0.9rem;
		line-height: 1.5;
		color: #64748b;
	}

	.panel-chip {
		padding: 0.45rem 0.75rem;
		border-radius: 999px;
		background: #dbeafe;
		color: #1e3a8a;
		font-size: 0.8rem;
		font-weight: 700;
		white-space: nowrap;
	}

	.teal-text { color: #0f766e; }
	.rose-text { color: #be123c; }
	.sky-text { color: #0369a1; }
	.teal-chip { background: #ccfbf1; color: #115e59; }
	.rose-chip { background: #ffe4e6; color: #9f1239; }
	.sky-chip { background: #e0f2fe; color: #075985; }

	.task-list {
		display: grid;
		gap: 0.75rem;
	}

	.task-row {
		display: grid;
		grid-template-columns: 34px minmax(0, 1fr) auto;
		align-items: center;
		gap: 0.8rem;
		padding: 0.75rem 0.85rem;
		background: #f8fafc;
		border-radius: 12px;
	}

	.task-rank {
		width: 34px;
		height: 34px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		background: #dbeafe;
		color: #1d4ed8;
		font-weight: 700;
	}

	.task-meta { min-width: 0; }
	.task-name { margin: 0; font-size: 0.92rem; font-weight: 700; color: #0f172a; }
	.task-sub { margin: 0.15rem 0 0; font-size: 0.76rem; color: #64748b; }
	.task-count { font-size: 1.1rem; font-weight: 800; color: #0f172a; }

	.risk-reasons { margin: 0.55rem 0 0; font-size: 0.8rem; line-height: 1.5; color: #7f1d1d; }

	.chart-grid {
		padding: 2rem;
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 1.25rem;
	}

	.chart-wrap {
		height: 320px;
		position: relative;
	}

	.empty-state {
		height: 320px;
		display: flex;
		align-items: center;
		justify-content: center;
		text-align: center;
		padding: 1.5rem;
		border-radius: 14px;
		background: #f8fafc;
		color: #64748b;
		font-size: 0.92rem;
	}

	@media (max-width: 1180px) {
		.insights-layout,
		.chart-grid {
			grid-template-columns: 1fr;
		}

		.risk-monitor-row {
			grid-template-columns: 1fr;
		}

		.risk-monitor-actions {
			flex-direction: row;
			flex-wrap: wrap;
		}
	}

	@media (max-width: 720px) {
		.topbar {
			padding-left: 1rem;
			padding-right: 1rem;
			align-items: flex-start;
			flex-direction: column;
			gap: 0.75rem;
		}

		.stats-grid,
		.loading-grid,
		.insights-layout,
		.chart-grid {
			padding-left: 1rem;
			padding-right: 1rem;
		}
	}

	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.4; }
	}
</style>
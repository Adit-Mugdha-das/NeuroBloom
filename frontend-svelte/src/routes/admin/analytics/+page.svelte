<script>
	import { locale as activeLocale, uiText } from '$lib/i18n';
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
			loading = false;
			await tick();
			renderActivityChart();
			renderPerformanceChart();
			renderFatigueChart();
			renderCompletionChart();
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Failed to load analytics';
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
			<div class="brand-mark">
				<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
					<path d="M12 5v14M5 12h14"/>
				</svg>
			</div>
			<span class="brand-name">{uiText("NeuroBloom Admin", $activeLocale)}</span>
		</div>
		<nav class="sidebar-nav">
			<a href="/admin/dashboard" class="nav-item">
			<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
			</svg>
			{uiText("Dashboard", $activeLocale)}
			</a>
			<a href="/admin/analytics" class="nav-item active">
			<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
			</svg>
			{uiText("System Analytics", $activeLocale)}
			</a>
			<a href="/admin/doctors" class="nav-item">
			<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
			</svg>
			{uiText("Doctor Management", $activeLocale)}
			</a>
			<a href="/admin/patients" class="nav-item">
			<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
			</svg>
			{uiText("Patient Management", $activeLocale)}
			</a>
			<a href="/admin/departments" class="nav-item">
			<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
			</svg>
			{uiText("Departments", $activeLocale)}
			</a>
			<a href="/admin/interventions" class="nav-item">
			<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/>
			</svg>
			{uiText("Interventions", $activeLocale)}
			</a>
			<a href="/admin/messages" class="nav-item">
			<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
			</svg>
			{uiText("Message Audit", $activeLocale)}
			</a>
			<a href="/admin/audit-logs" class="nav-item">
			<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
			</svg>
			{uiText("Audit Logs", $activeLocale)}
			</a>
			<a href="/admin/system-health" class="nav-item">
			<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
			</svg>
			{uiText("System Health", $activeLocale)}
			</a>
			<a href="/admin/notifications" class="nav-item">
			<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
			</svg>
			{uiText("Notification Center", $activeLocale)}
			</a>
			<a href="/admin/research-data" class="nav-item">
			<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/>
			</svg>
			{uiText("Research Data", $activeLocale)}
			</a>
		</nav>
		<button class="logout-btn" on:click={logout}>
			<svg class="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
				<path d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
			</svg>
			{uiText("Sign Out", $activeLocale)}
		</button>
	</aside>

	<main class="main-content">
		<header class="topbar">
			<div>
				<h1 class="page-title">{uiText("System Analytics", $activeLocale)}</h1>
				<p class="page-subtitle">{uiText("Focused system-wide analytics page with only the core operational and clinical trends.", $activeLocale)}</p>
			</div>
			<div class="admin-info">
				<div class="admin-avatar">
					<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
						<path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2M12 11a4 4 0 100-8 4 4 0 000 8z"/>
					</svg>
				</div>
				<div class="admin-details">
					<span class="admin-name">{admin?.full_name || admin?.email}</span>
					<span class="admin-role">{uiText("Administrator", $activeLocale)}</span>
				</div>
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
				<div class="stat-card">
				<div class="stat-icon-wrap blue">
					<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
						<path d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
					</svg>
				</div>
					<div class="stat-body"><p class="stat-label">{uiText("Total Patients", $activeLocale)}</p><p class="stat-value">{stats.total_patients}</p></div>
				</div>
				<div class="stat-card">
				<div class="stat-icon-wrap purple">
					<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
						<path d="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0zm6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
					</svg>
				</div>
					<div class="stat-body"><p class="stat-label">{uiText("Total Doctors", $activeLocale)}</p><p class="stat-value">{stats.total_doctors}</p></div>
				</div>
				<div class="stat-card">
				<div class="stat-icon-wrap emerald">
					<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
						<path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
					</svg>
				</div>
					<div class="stat-body"><p class="stat-label">{uiText("Active Patients Today", $activeLocale)}</p><p class="stat-value">{stats.active_patients_today}</p></div>
				</div>
				<div class="stat-card">
				<div class="stat-icon-wrap slate">
					<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
						<path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
					</svg>
				</div>
					<div class="stat-body"><p class="stat-label">{uiText("Sessions Completed", $activeLocale)}</p><p class="stat-value">{stats.completed_sessions}</p></div>
				</div>
				<div class="stat-card">
				<div class="stat-icon-wrap teal">
					<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
						<path d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
					</svg>
				</div>
					<div class="stat-body"><p class="stat-label">{uiText("Average Improvement", $activeLocale)}</p><p class="stat-value small">{stats.average_improvement_score >= 0 ? '+' : ''}{stats.average_improvement_score}</p></div>
				</div>
				<div class="stat-card">
				<div class="stat-icon-wrap red">
					<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
						<path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
					</svg>
				</div>
					<div class="stat-body"><p class="stat-label">{uiText("High-Risk Patients", $activeLocale)}</p><p class="stat-value">{stats.high_risk_patients}</p></div>
				</div>
			</div>

			<section class="risk-monitor-panel">
				<div class="panel-header">
					<div>
						<p class="panel-kicker rose-text">{uiText("Risk Monitoring", $activeLocale)}</p>
						<h2>{uiText("High-Risk Patients", $activeLocale)}</h2>
						<p class="panel-copy">{uiText("System-wide alerts are consolidated here so the admin can quickly notify the assigned doctor, escalate urgent cases, or mark alerts as reviewed without adding workflow clutter elsewhere.", $activeLocale)}</p>
					</div>
					<div class="panel-chip rose-chip">{riskAlerts.length} {uiText("active alerts", $activeLocale)}</div>
				</div>

				<div class="risk-monitor-list">
					{#if riskAlerts.length === 0}
						<div class="empty-risk-state">{uiText("No patients are currently flagged as high risk.", $activeLocale)}</div>
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
											<span class="metric-chip">{uiText("Risk score", $activeLocale)} {alert.risk_score}</span>
										</div>
									</div>

									<div class="risk-monitor-meta">
										<span>{alert.email}</span>
										<span>{uiText("Doctor:", $activeLocale)} {alert.assigned_doctor_name || 'Unassigned'}</span>
										{#if alert.recent_avg_fatigue !== null}
											<span>{uiText("Fatigue", $activeLocale)} {alert.recent_avg_fatigue}</span>
										{/if}
										{#if alert.recent_avg_score !== null}
											<span>{uiText("Score", $activeLocale)} {alert.recent_avg_score}</span>
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
										{#if isRiskActionLoading(alert.id, 'notify')}{uiText("Sending...", $activeLocale)}{:else if alert.doctor_notified}{uiText("Doctor notified", $activeLocale)}{:else}{uiText("Notify doctor", $activeLocale)}{/if}
									</button>
									<button
										class="action-btn danger"
										on:click={() => runRiskAction(alert.id, 'escalate')}
										disabled={alert.alert_status === 'escalated' || isRiskActionLoading(alert.id, 'escalate')}
									>
										{#if isRiskActionLoading(alert.id, 'escalate')}{uiText("Escalating...", $activeLocale)}{:else if alert.alert_status === 'escalated'}{uiText("Escalated", $activeLocale)}{:else}{uiText("Escalate case", $activeLocale)}{/if}
									</button>
									<button
										class="action-btn success"
										on:click={() => runRiskAction(alert.id, 'review')}
										disabled={alert.alert_status === 'reviewed' || isRiskActionLoading(alert.id, 'review')}
									>
										{#if isRiskActionLoading(alert.id, 'review')}{uiText("Saving...", $activeLocale)}{:else if alert.alert_status === 'reviewed'}{uiText("Reviewed", $activeLocale)}{:else}{uiText("Mark reviewed", $activeLocale)}{/if}
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
							<p class="panel-kicker">{uiText("Task Usage", $activeLocale)}</p>
							<h2>{uiText("Most Used Tasks", $activeLocale)}</h2>
						</div>
					</div>
					<div class="task-list">
						{#if stats.most_used_tasks.length === 0}
							<p class="empty-copy">{uiText("No completed task data is available yet.", $activeLocale)}</p>
						{:else}
							{#each stats.most_used_tasks as task, index}
								<div class="task-row">
									<div class="task-rank">{index + 1}</div>
									<div class="task-meta">
										<p class="task-name">{task.task}</p>
										<p class="task-sub">{uiText("Completed sessions", $activeLocale)}</p>
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
							<p class="panel-kicker">{uiText("Activity", $activeLocale)}</p>
							<h2>{uiText("Patient Activity", $activeLocale)}</h2>
							<p class="panel-copy">{uiText("Seven-day view of completed sessions and distinct active patients.", $activeLocale)}</p>
						</div>
						<div class="panel-chip">{uiText("Last 7 days", $activeLocale)}</div>
					</div>
					{#if hasActivityData()}
						<div class="chart-wrap"><canvas bind:this={activityChartCanvas}></canvas></div>
					{:else}
						<div class="empty-state">{uiText("No activity data is available yet.", $activeLocale)}</div>
					{/if}
				</div>

				<div class="chart-panel">
					<div class="panel-header">
						<div>
							<p class="panel-kicker teal-text">{uiText("Performance", $activeLocale)}</p>
							<h2>{uiText("Cognitive Performance Trend", $activeLocale)}</h2>
							<p class="panel-copy">{uiText("Average completed-session score over the last 14 days.", $activeLocale)}</p>
						</div>
						<div class="panel-chip teal-chip">{uiText("14 days", $activeLocale)}</div>
					</div>
					{#if hasPerformanceData()}
						<div class="chart-wrap"><canvas bind:this={performanceChartCanvas}></canvas></div>
					{:else}
						<div class="empty-state">{uiText("No performance trend is available yet.", $activeLocale)}</div>
					{/if}
				</div>

				<div class="chart-panel">
					<div class="panel-header">
						<div>
							<p class="panel-kicker rose-text">{uiText("Fatigue", $activeLocale)}</p>
							<h2>{uiText("Fatigue Trends", $activeLocale)}</h2>
							<p class="panel-copy">{uiText("Fatigue questionnaire signals compared with average performance.", $activeLocale)}</p>
						</div>
						<div class="panel-chip rose-chip">{uiText("Context data", $activeLocale)}</div>
					</div>
					{#if hasFatigueData()}
						<div class="chart-wrap"><canvas bind:this={fatigueChartCanvas}></canvas></div>
					{:else}
						<div class="empty-state">{uiText("No fatigue questionnaire data has been recorded yet.", $activeLocale)}</div>
					{/if}
				</div>

				<div class="chart-panel">
					<div class="panel-header">
						<div>
							<p class="panel-kicker sky-text">{uiText("Completion", $activeLocale)}</p>
							<h2>{uiText("Task Completion Rate", $activeLocale)}</h2>
							<p class="panel-copy">{uiText("Completion percentage and completed-session totals across the last 14 days.", $activeLocale)}</p>
						</div>
						<div class="panel-chip sky-chip">{uiText("14 days", $activeLocale)}</div>
					</div>
					{#if hasCompletionData()}
						<div class="chart-wrap"><canvas bind:this={completionChartCanvas}></canvas></div>
					{:else}
						<div class="empty-state">{uiText("No completion trend is available yet.", $activeLocale)}</div>
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

	.brand-mark {
		width: 28px;
		height: 28px;
		background: #1d4ed8;
		border-radius: 7px;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}

	.brand-mark svg { width: 14px; height: 14px; }

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

	.nav-icon { width: 17px; height: 17px; flex-shrink: 0; }

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
		gap: 0.75rem;
		font-size: 0.9rem;
		color: #475569;
	}

	.admin-avatar {
		width: 36px;
		height: 36px;
		background: #eff6ff;
		border: 1px solid #bfdbfe;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}

	.admin-avatar svg { width: 17px; height: 17px; stroke: #1d4ed8; }

	.admin-details { display: flex; flex-direction: column; gap: 0.1rem; }
	.admin-name { font-size: 0.875rem; font-weight: 600; color: #1e293b; }
	.admin-role { font-size: 0.7rem; color: #64748b; font-weight: 500; text-transform: uppercase; letter-spacing: 0.06em; }

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
		border-radius: 10px;
		padding: 1.25rem;
		display: flex;
		align-items: center;
		gap: 1rem;
		box-shadow: 0 1px 3px rgba(0,0,0,0.06);
		border: 1px solid #e2e8f0;
		transition: box-shadow 0.15s;
	}

	.stat-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
	.stat-card.skeleton { height: 90px; background: #f1f5f9; border-color: transparent; animation: pulse 1.4s infinite; }

	.stat-icon-wrap {
		width: 44px;
		height: 44px;
		border-radius: 10px;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}

	.stat-icon-wrap svg { width: 22px; height: 22px; }

	.stat-icon-wrap.blue    { background: #eff6ff; color: #1d4ed8; }
	.stat-icon-wrap.purple  { background: #faf5ff; color: #7c3aed; }
	.stat-icon-wrap.emerald { background: #ecfdf5; color: #059669; }
	.stat-icon-wrap.slate   { background: #f8fafc; color: #475569; }
	.stat-icon-wrap.teal    { background: #f0fdfa; color: #0f766e; }
	.stat-icon-wrap.red     { background: #fef2f2; color: #dc2626; }

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
<script>
	import { goto } from '$app/navigation';
	import api from '$lib/api.js';
	import { user } from '$lib/stores.js';
	import { onMount } from 'svelte';
	
	let patients = [];
	let pendingRequests = [];
	let analytics = null;
	let domainAnalytics = null;
	let cohortTrends = null;
	let notifications = [];
	let loading = true;
	let error = '';
	let userData;
	let showAnalytics = true;
	let showDomainAnalytics = false;
	let sortBy = 'name';
	let sortDirection = 'asc';
	
	// Subscribe to user store
	const unsubscribe = user.subscribe(value => {
		userData = value;
	});
	
	onMount(() => {
		// Check if user is logged in as doctor
		if (!userData || userData.role !== 'doctor') {
			goto('/login');
			return;
		}
		
		loadData();
		
		return unsubscribe;
	});
	
	async function loadData() {
		try {
			const [patientsResp, requestsResp, analyticsResp, domainResp, trendsResp, notificationsResp] = await Promise.all([
				api.get(`/api/doctor/${userData.id}/patients`),
				api.get(`/api/doctor/${userData.id}/pending-requests`),
				api.get(`/api/doctor/${userData.id}/analytics`),
				api.get(`/api/doctor/${userData.id}/analytics/domains`),
				api.get(`/api/doctor/${userData.id}/analytics/trends?days=30`),
				api.get(`/api/doctor/${userData.id}/notifications`)
			]);
			patients = patientsResp.data.patients;
			pendingRequests = requestsResp.data.requests;
			analytics = analyticsResp.data;
			domainAnalytics = domainResp.data;
			cohortTrends = trendsResp.data;
			notifications = notificationsResp.data.notifications.slice(0, 3);
		} catch (err) {
			error = 'Failed to load data';
			console.error('Error loading data:', err);
		} finally {
			loading = false;
		}
	}
	
	async function approveRequest(requestId) {
		if (!confirm('Approve this assignment request?')) return;
		
		try {
			await api.post(`/api/doctor/request/${requestId}/approve`, null, {
				params: {
					doctor_id: userData.id,
					treatment_goal: 'Improve cognitive function through targeted training'
				}
			});
			alert('Request approved! Patient has been assigned to you.');
			await loadData();
		} catch (err) {
			alert('Failed to approve request: ' + (err.response?.data?.detail || 'Unknown error'));
		}
	}
	
	async function rejectRequest(requestId) {
		const reason = prompt('Reason for rejection (optional):');
		if (reason === null) return; // User cancelled
		
		try {
			await api.post(`/api/doctor/request/${requestId}/reject`, null, {
				params: {
					doctor_id: userData.id,
					notes: reason || 'Request declined'
				}
			});
			alert('Request rejected.');
			await loadData();
		} catch (err) {
			alert('Failed to reject request: ' + (err.response?.data?.detail || 'Unknown error'));
		}
	}
	
	async function unassignPatient(patientId, patientName) {
		const confirmation = confirm(
			`Are you sure you want to unassign ${patientName}?\n\nThis will remove them from your patient list. They can request reassignment later.`
		);
		
		if (!confirmation) return;
		
		try {
			await api.post(`/api/doctor/${userData.id}/unassign/${patientId}`);
			alert('Patient unassigned successfully.');
			await loadData();
		} catch (err) {
			alert('Failed to unassign patient: ' + (err.response?.data?.detail || 'Unknown error'));
		}
	}
	
	function viewPatient(patientId) {
		goto(`/doctor/patient/${patientId}`);
	}
	
	function formatDate(dateStr) {
		if (!dateStr) return 'Never';
		return new Date(dateStr).toLocaleDateString();
	}
	
	function isRecentlyActive(lastActivity) {
		if (!lastActivity) return false;
		const sevenDaysAgo = new Date(Date.now() - 7*24*60*60*1000);
		return new Date(lastActivity) > sevenDaysAgo;
	}
	
	function handleLogout() {
		user.set(null);
		goto('/login');
	}

	function notificationTypeLabel(type) {
		if (type === 'announcement') return 'Announcement';
		if (type === 'feature_update') return 'Feature Update';
		if (type === 'research_invitation') return 'Research Invitation';
		return 'Notice';
	}

	function notificationTypeClass(type) {
		if (type === 'announcement') return 'notice-blue';
		if (type === 'feature_update') return 'notice-teal';
		if (type === 'research_invitation') return 'notice-amber';
		return 'notice-blue';
	}
	
	function sortPatients(field) {
		if (sortBy === field) {
			sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
		} else {
			sortBy = field;
			sortDirection = 'asc';
		}
	}
	
	function getPatientAnalytics(patientId) {
		if (!analytics || !analytics.patient_summary) return null;
		return analytics.patient_summary.find(p => p.patient_id === patientId);
	}
	
	$: activePatients = patients.filter(p => isRecentlyActive(p.last_activity));
	$: patientsWithBaseline = patients.filter(p => p.baseline_completed);
	
	$: sortedPatients = analytics && analytics.patient_summary ? 
		[...analytics.patient_summary].sort((a, b) => {
			let aVal, bVal;
			
			switch(sortBy) {
				case 'name':
					aVal = a.name.toLowerCase();
					bVal = b.name.toLowerCase();
					break;
				case 'adherence':
					aVal = a.adherence_rate;
					bVal = b.adherence_rate;
					break;
				case 'sessions':
					aVal = a.total_sessions;
					bVal = b.total_sessions;
					break;
				case 'score':
					aVal = a.avg_score;
					bVal = b.avg_score;
					break;
				case 'improvement':
					aVal = a.improvement;
					bVal = b.improvement;
					break;
				case 'risk':
					const riskOrder = { high: 0, medium: 1, low: 2 };
					aVal = riskOrder[a.risk_level];
					bVal = riskOrder[b.risk_level];
					break;
				default:
					return 0;
			}
			
			if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
			if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
			return 0;
		}) : patients;

</script>

<div class="doctor-dashboard">
	<header>
		<div class="header-content">
			<div>
				<h1>👨‍⚕️ Doctor Dashboard</h1>
				<p>Welcome, Dr. {userData?.fullName || userData?.email}</p>
			</div>
			<div class="header-actions">
				<button class="btn-messages" on:click={() => goto('/doctor/messages')}>
					💬 Messages
				</button>
				<button class="btn-logout" on:click={handleLogout}>Logout</button>
			</div>
		</div>
	</header>
	
	{#if loading}
		<div class="loading">Loading patients...</div>
	{:else if error}
		<div class="error">{error}</div>
	{:else}
		{#if notifications.length > 0}
			<div class="doctor-notice-section">
				<div class="notice-banner-head">
					<div>
						<h2>🔔 Notification Center</h2>
						<p>Important admin notices, feature updates, and research invitations</p>
					</div>
				</div>
				<div class="doctor-notice-grid">
					{#each notifications as notification (notification.id)}
						<div class="doctor-notice-card">
							<div class="doctor-notice-top">
								<p class="doctor-notice-title">{notification.title}</p>
								<span class="doctor-notice-pill {notificationTypeClass(notification.notification_type)}">{notificationTypeLabel(notification.notification_type)}</span>
							</div>
							<p class="doctor-notice-message">{notification.message}</p>
						</div>
					{/each}
				</div>
			</div>
		{/if}

		<!-- Pending Requests Section -->
		{#if pendingRequests.length > 0}
			<div class="pending-requests-section">
				<h2>📬 Pending Assignment Requests ({pendingRequests.length})</h2>
				<div class="requests-list">
					{#each pendingRequests as request}
						<div class="request-card">
							<div class="request-info">
								<h3>{request.patient_email}</h3>
								{#if request.patient_name}
									<p class="patient-name">{request.patient_name}</p>
								{/if}
								{#if request.diagnosis}
									<p class="diagnosis">Diagnosis: {request.diagnosis}</p>
								{/if}
								{#if request.reason}
									<p class="reason"><strong>Reason:</strong> {request.reason}</p>
								{/if}
								{#if request.message}
									<p class="message"><strong>Message:</strong> {request.message}</p>
								{/if}
								<p class="date">Requested: {formatDate(request.created_at)}</p>
							</div>
							<div class="request-actions">
								<button class="btn-approve" on:click={() => approveRequest(request.id)}>
									✓ Approve
								</button>
								<button class="btn-reject" on:click={() => rejectRequest(request.id)}>
									✗ Reject
								</button>
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}
		
		<div class="stats-cards">
			<div class="stat-card">
				<div class="stat-number">{patients.length}</div>
				<div class="stat-label">Total Patients</div>
			</div>
			<div class="stat-card">
				<div class="stat-number">{activePatients.length}</div>
				<div class="stat-label">Active (7 days)</div>
			</div>
			<div class="stat-card">
				<div class="stat-number">{patientsWithBaseline.length}</div>
				<div class="stat-label">Baseline Complete</div>
			</div>
		</div>
		
		<!-- Analytics Dashboard -->
		{#if analytics}
			<div class="analytics-section">
				<div class="analytics-header">
					<h2>📊 Practice Analytics</h2>
					<button class="toggle-analytics" on:click={() => showAnalytics = !showAnalytics}>
						{showAnalytics ? '▼ Hide' : '▶ Show'} Analytics
					</button>
				</div>
				
				{#if showAnalytics}
					<!-- Adherence Overview -->
					<div class="analytics-grid">
						<div class="analytics-card adherence-card">
							<h3>📅 Overall Adherence</h3>
							<div class="adherence-score">
								<div class="score-circle" class:excellent={analytics.adherence.overall_adherence_rate >= 80} class:good={analytics.adherence.overall_adherence_rate >= 60 && analytics.adherence.overall_adherence_rate < 80} class:fair={analytics.adherence.overall_adherence_rate >= 40 && analytics.adherence.overall_adherence_rate < 60} class:poor={analytics.adherence.overall_adherence_rate < 40}>
									{analytics.adherence.overall_adherence_rate}%
								</div>
							</div>
							<div class="adherence-breakdown">
								<div class="breakdown-item">
									<span class="dot excellent"></span>
									<span>Excellent (≥80%):</span>
									<strong>{analytics.adherence.adherence_breakdown.excellent}</strong>
								</div>
								<div class="breakdown-item">
									<span class="dot good"></span>
									<span>Good (60-79%):</span>
									<strong>{analytics.adherence.adherence_breakdown.good}</strong>
								</div>
								<div class="breakdown-item">
									<span class="dot fair"></span>
									<span>Fair (40-59%):</span>
									<strong>{analytics.adherence.adherence_breakdown.fair}</strong>
								</div>
								<div class="breakdown-item">
									<span class="dot poor"></span>
									<span>Poor (&lt;40%):</span>
									<strong>{analytics.adherence.adherence_breakdown.poor}</strong>
								</div>
							</div>
						</div>
						
						<div class="analytics-card success-card">
							<h3>🎯 Success Metrics</h3>
							<div class="success-metrics">
								<div class="metric-item">
									<div class="metric-value">{analytics.success_metrics.avg_session_score}</div>
									<div class="metric-label">Avg Score</div>
								</div>
								<div class="metric-item">
									<div class="metric-value improvement">{analytics.success_metrics.avg_improvement > 0 ? '+' : ''}{analytics.success_metrics.avg_improvement}</div>
									<div class="metric-label">Avg Improvement</div>
								</div>
								<div class="metric-item">
									<div class="metric-value">{analytics.success_metrics.total_sessions_completed}</div>
									<div class="metric-label">Total Sessions</div>
								</div>
							</div>
							<div class="progress-summary">
								<div class="progress-item improving">
									<span>↗ Improving:</span>
									<strong>{analytics.success_metrics.patients_improving}</strong>
								</div>
								<div class="progress-item declining">
									<span>↘ Declining:</span>
									<strong>{analytics.success_metrics.patients_declining}</strong>
								</div>
							</div>
						</div>
					</div>
					
					<!-- Domain Analytics -->
					{#if domainAnalytics && Object.keys(domainAnalytics.domains).length > 0}
						<div class="domain-section">
							<div class="section-header">
								<h3>🧠 Domain Performance Overview</h3>
								<button class="toggle-btn" on:click={() => showDomainAnalytics = !showDomainAnalytics}>
									{showDomainAnalytics ? '▼ Hide' : '▶ Show'}
								</button>
							</div>
							
							{#if showDomainAnalytics}
								<div class="domain-grid">
									{#each Object.entries(domainAnalytics.domains) as [domain, stats]}
										<div class="domain-card">
											<h4>{domain.replace('_', ' ')}</h4>
											<div class="domain-stats">
												<div class="stat">
													<span class="label">Sessions:</span>
													<span class="value">{stats.sessions_count}</span>
												</div>
												<div class="stat">
													<span class="label">Patients:</span>
													<span class="value">{stats.patients_count}</span>
												</div>
												<div class="stat">
													<span class="label">Avg Score:</span>
													<span class="value score">{stats.avg_score}</span>
												</div>
												<div class="stat">
													<span class="label">Avg Accuracy:</span>
													<span class="value">{stats.avg_accuracy}%</span>
												</div>
												{#if stats.avg_reaction_time > 0}
													<div class="stat">
														<span class="label">Avg RT:</span>
														<span class="value">{stats.avg_reaction_time}ms</span>
													</div>
												{/if}
											</div>
										</div>
									{/each}
								</div>
							{/if}
						</div>
					{/if}
					
					<!-- Cohort Trends -->
					{#if cohortTrends && cohortTrends.trends && cohortTrends.trends.length > 0}
						<div class="trends-section">
							<h3>📈 Cohort Activity Trends (Last {cohortTrends.period_days} Days)</h3>
							<div class="trends-summary">
								<div class="summary-stat">
									<span class="label">Avg Sessions/Week:</span>
									<span class="value">{cohortTrends.summary.avg_sessions_per_week}</span>
								</div>
								<div class="summary-stat">
									<span class="label">Overall Avg Score:</span>
									<span class="value">{cohortTrends.summary.overall_avg_score}</span>
								</div>
							</div>
							<div class="trends-timeline">
								{#each cohortTrends.trends as week}
									<div class="week-bar">
										<div class="week-label">{new Date(week.week_starting).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</div>
										<div class="bar-container">
											<div class="bar sessions" style="width: {(week.sessions / cohortTrends.summary.total_sessions * 100) * 5}%; background: #667eea;" title="{week.sessions} sessions"></div>
										</div>
										<div class="week-stats">
											<span>{week.sessions} sessions</span>
											<span>{week.active_patients} patients</span>
											<span>Avg: {week.avg_score}</span>
										</div>
									</div>
								{/each}
							</div>
						</div>
					{/if}
					
					<!-- High-Risk Patients Alert -->
					{#if analytics.high_risk_patients && analytics.high_risk_patients.length > 0}
						<div class="high-risk-section">
							<h3>⚠️ Patients Requiring Attention ({analytics.high_risk_patients.length})</h3>
							<div class="high-risk-grid">
								{#each analytics.high_risk_patients as patient}
									<div class="high-risk-card risk-{patient.risk_level}">
										<div class="risk-header">
											<div>
												<h4>{patient.name}</h4>
												<p class="patient-email">{patient.email}</p>
											</div>
											<span class="risk-badge {patient.risk_level}">{patient.risk_level.toUpperCase()}</span>
										</div>
										<div class="risk-details">
											<div class="risk-stat">
												<span class="label">Adherence:</span>
												<span class="value">{patient.adherence_rate}%</span>
											</div>
											<div class="risk-stat">
												<span class="label">30-day sessions:</span>
												<span class="value">{patient.sessions_30_days}</span>
											</div>
											<div class="risk-stat">
												<span class="label">Last activity:</span>
												<span class="value">{formatDate(patient.last_activity)}</span>
											</div>
										</div>
										<div class="risk-factors">
											<strong>Concerns:</strong>
											<ul>
												{#each patient.risk_factors as factor}
													<li>{factor}</li>
												{/each}
											</ul>
										</div>
										<button class="btn-view-patient" on:click={() => viewPatient(patient.patient_id)}>
											View Patient
										</button>
									</div>
								{/each}
							</div>
						</div>
					{/if}
				{/if}
			</div>
		{/if}
		
		<div class="patients-section">
			<h2>Your Patients ({patients.length})</h2>
			
			{#if patients.length === 0}
				<div class="no-patients">
					<p>📋 No patients assigned yet.</p>
					<p class="subtitle">Patients will appear here once they are assigned to you.</p>
				</div>
			{:else}
				<div class="patients-table">
					<table>
						<thead>
							<tr>
								<th on:click={() => sortPatients('name')} class="sortable">
									Name {sortBy === 'name' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}
								</th>
								<th>Email</th>
								<th>Diagnosis</th>
								<th on:click={() => sortPatients('risk')} class="sortable">
									Risk {sortBy === 'risk' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}
								</th>
								<th on:click={() => sortPatients('adherence')} class="sortable">
									Adherence {sortBy === 'adherence' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}
								</th>
								<th on:click={() => sortPatients('sessions')} class="sortable">
									Sessions {sortBy === 'sessions' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}
								</th>
								<th on:click={() => sortPatients('score')} class="sortable">
									Avg Score {sortBy === 'score' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}
								</th>
								<th on:click={() => sortPatients('improvement')} class="sortable">
									Trend {sortBy === 'improvement' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}
								</th>
								<th>Actions</th>
							</tr>
						</thead>
						<tbody>
							{#each sortedPatients as patientData}
								{@const patient = patients.find(p => p.patient_id === patientData.patient_id)}
								{#if patient}
									<tr class="risk-{patientData.risk_level}">
										<td>
											<div class="patient-name">
												{patient.full_name || patient.email}
											</div>
										</td>
										<td>
											<div class="patient-email">
												{patient.email}
											</div>
										</td>
										<td>{patient.diagnosis || 'N/A'}</td>
										<td>
											<span class="risk-indicator {patientData.risk_level}">
												{patientData.risk_level.toUpperCase()}
											</span>
										</td>
										<td>
											<span class="adherence-badge {patientData.adherence_status}">
												{patientData.adherence_rate}%
											</span>
										</td>
										<td>
											<div class="session-info">
												<span class="total">{patientData.total_sessions}</span>
												<span class="recent">(7d: {patientData.sessions_last_7_days})</span>
											</div>
										</td>
										<td>
											<strong>{patientData.avg_score}</strong>
										</td>
										<td>
											<span class="trend-indicator {patientData.improvement >= 0 ? 'positive' : 'negative'}">
												{patientData.improvement >= 0 ? '↗' : '↘'} {patientData.improvement > 0 ? '+' : ''}{patientData.improvement}
											</span>
										</td>
										<td>
											<div class="action-buttons">
												<button 
													class="view-btn"
													on:click={() => viewPatient(patient.patient_id)}
												>
													View Details
												</button>
												<button 
													class="unassign-btn"
													on:click={() => unassignPatient(patient.patient_id, patient.full_name || patient.email)}
												>
													Unassign
												</button>
											</div>
										</td>
									</tr>
								{/if}
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.doctor-dashboard {
		max-width: 1400px;
		margin: 0 auto;
		padding: 2rem;
		min-height: 100vh;
		background: #f8f9fa;
	}
	
	header {
		margin-bottom: 2rem;
	}
	
	.header-content {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	
	.header-actions {
		display: flex;
		gap: 1rem;
		align-items: center;
	}
	
	.btn-messages {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		padding: 0.75rem 1.5rem;
		border-radius: 8px;
		cursor: pointer;
		font-weight: 600;
		transition: transform 0.2s;
	}
	
	.btn-messages:hover {
		transform: translateY(-2px);
	}
	
	.btn-logout {
		background: #dc3545;
		color: white;
		border: none;
		padding: 0.75rem 1.5rem;
		border-radius: 8px;
		cursor: pointer;
		font-weight: 600;
		transition: background 0.3s;
	}
	
	.btn-logout:hover {
		background: #c82333;
	}
	
	h1 {
		font-size: 2rem;
		color: #333;
		margin-bottom: 0.5rem;
	}
	
	header p {
		color: #666;
		font-size: 1.1rem;
	}

	.doctor-notice-section {
		margin-bottom: 2rem;
		background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 100%);
		border: 1px solid #bfdbfe;
		border-radius: 16px;
		padding: 1.5rem;
	}

	.notice-banner-head h2 {
		margin: 0;
		color: #1e3a8a;
	}

	.notice-banner-head p {
		margin: 0.3rem 0 0;
		font-size: 0.95rem;
		color: #475569;
	}

	.doctor-notice-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
		gap: 1rem;
		margin-top: 1rem;
	}

	.doctor-notice-card {
		background: white;
		border: 1px solid #dbeafe;
		border-radius: 12px;
		padding: 1rem;
		box-shadow: 0 8px 24px rgba(37, 99, 235, 0.08);
	}

	.doctor-notice-top {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 0.75rem;
	}

	.doctor-notice-title {
		margin: 0;
		font-size: 0.95rem;
		font-weight: 700;
		color: #0f172a;
	}

	.doctor-notice-message {
		margin: 0.6rem 0 0;
		line-height: 1.6;
		color: #475569;
		font-size: 0.9rem;
	}

	.doctor-notice-pill {
		padding: 0.2rem 0.65rem;
		border-radius: 999px;
		font-size: 0.72rem;
		font-weight: 700;
		white-space: nowrap;
	}

	.notice-blue { background: #dbeafe; color: #1d4ed8; }
	.notice-teal { background: #ccfbf1; color: #0f766e; }
	.notice-amber { background: #fef3c7; color: #92400e; }
	
	.stats-cards {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
		margin-bottom: 2rem;
	}
	
	.stat-card {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		padding: 1.5rem;
		border-radius: 12px;
		text-align: center;
		box-shadow: 0 4px 6px rgba(0,0,0,0.1);
	}
	
	.stat-number {
		font-size: 2.5rem;
		font-weight: bold;
		margin-bottom: 0.5rem;
	}
	
	.stat-label {
		font-size: 0.9rem;
		opacity: 0.9;
	}
	
	.patients-section {
		background: white;
		border-radius: 12px;
		padding: 2rem;
		box-shadow: 0 2px 10px rgba(0,0,0,0.1);
	}
	
	h2 {
		margin-bottom: 1.5rem;
		color: #333;
	}
	
	.patients-table {
		overflow-x: auto;
	}
	
	table {
		width: 100%;
		border-collapse: collapse;
	}
	
	th {
		background: #f8f9fa;
		padding: 1rem;
		text-align: left;
		font-weight: 600;
		color: #555;
		border-bottom: 2px solid #e0e0e0;
	}
	
	td {
		padding: 1rem;
		border-bottom: 1px solid #e0e0e0;
	}
	
	tr:hover {
		background: #f8f9fa;
	}
	
	.patient-name {
		font-weight: 500;
		color: #333;
	}
	
	.patient-email {
		color: #667eea;
		font-size: 0.9rem;
	}
	
	.activity.active {
		color: #28a745;
		font-weight: 500;
	}
	
	.activity.inactive {
		color: #999;
	}
	
	.badge {
		padding: 0.25rem 0.75rem;
		border-radius: 20px;
		font-size: 0.85rem;
		font-weight: 500;
		display: inline-block;
	}
	
	.badge.complete {
		background: #d4edda;
		color: #155724;
	}
	
	.badge.pending {
		background: #fff3cd;
		color: #856404;
	}
	
	.view-btn {
		background: #667eea;
		color: white;
		border: none;
		padding: 0.5rem 1rem;
		border-radius: 6px;
		cursor: pointer;
		font-weight: 500;
		transition: background 0.3s;
	}
	
	.view-btn:hover {
		background: #5568d3;
	}
	
	.no-patients {
		text-align: center;
		padding: 3rem;
		color: #999;
	}
	
	.no-patients .subtitle {
		font-size: 0.9rem;
		margin-top: 0.5rem;
	}
	
	.loading, .error {
		text-align: center;
		padding: 2rem;
		font-size: 1.1rem;
	}
	
	.error {
		color: #c33;
		background: #fee;
		border-radius: 8px;
		margin: 2rem 0;
	}
	
	/* Pending Requests Section */
	.pending-requests-section {
		margin-bottom: 3rem;
		background: #fffbf0;
		padding: 1.5rem;
		border-radius: 12px;
		border: 2px solid #ffd700;
	}
	
	.pending-requests-section h2 {
		color: #667eea;
		margin-bottom: 1.5rem;
	}
	
	.requests-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.request-card {
		background: white;
		border: 2px solid #e0e0e0;
		border-radius: 10px;
		padding: 1.5rem;
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 1.5rem;
	}
	
	.request-info {
		flex: 1;
	}
	
	.request-info h3 {
		color: #667eea;
		margin: 0 0 0.5rem 0;
		font-size: 1.1rem;
	}
	
	.request-info p {
		margin: 0.3rem 0;
		color: #555;
		font-size: 0.9rem;
	}
	
	.patient-name {
		font-weight: 600;
		color: #333;
	}
	
	.diagnosis {
		color: #764ba2;
		font-weight: 500;
	}
	
	.reason, .message {
		font-style: italic;
		line-height: 1.5;
	}
	
	.date {
		color: #999;
		font-size: 0.85rem;
		margin-top: 0.5rem;
	}
	
	.request-actions {
		display: flex;
		gap: 0.75rem;
		flex-shrink: 0;
	}
	
	.btn-approve,
	.btn-reject {
		padding: 0.75rem 1.5rem;
		border: none;
		border-radius: 8px;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
		font-size: 0.9rem;
	}
	
	.btn-approve {
		background: #28a745;
		color: white;
	}
	
	.btn-approve:hover {
		background: #218838;
		transform: translateY(-2px);
	}
	
	.btn-reject {
		background: #dc3545;
		color: white;
	}
	
	.btn-reject:hover {
		background: #c82333;
		transform: translateY(-2px);
	}
	
	.action-buttons {
		display: flex;
		gap: 0.5rem;
		flex-wrap: wrap;
	}
	
	.view-btn,
	.unassign-btn {
		padding: 0.5rem 1rem;
		border: none;
		border-radius: 6px;
		cursor: pointer;
		font-weight: 500;
		transition: all 0.2s;
		font-size: 0.85rem;
	}
	
	.view-btn {
		background: #667eea;
		color: white;
	}
	
	.view-btn:hover {
		background: #5568d3;
		transform: translateY(-1px);
	}
	
	.unassign-btn {
		background: #dc3545;
		color: white;
	}
	
	.unassign-btn:hover {
		background: #c82333;
		transform: translateY(-1px);
	}
	
	/* Analytics Section */
	.analytics-section {
		background: white;
		border-radius: 12px;
		padding: 2rem;
		margin-bottom: 2rem;
		box-shadow: 0 2px 10px rgba(0,0,0,0.1);
	}
	
	.analytics-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
	}
	
	.toggle-analytics {
		background: #667eea;
		color: white;
		border: none;
		padding: 0.5rem 1rem;
		border-radius: 6px;
		cursor: pointer;
		font-weight: 500;
		transition: background 0.3s;
	}
	
	.toggle-analytics:hover {
		background: #5568d3;
	}
	
	.analytics-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
		gap: 1.5rem;
		margin-bottom: 2rem;
	}
	
	.analytics-card {
		background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
		border: 2px solid #e0e0e0;
		border-radius: 12px;
		padding: 1.5rem;
	}
	
	.analytics-card h3 {
		margin: 0 0 1.5rem 0;
		color: #333;
		font-size: 1.1rem;
	}
	
	/* Adherence Card */
	.adherence-score {
		display: flex;
		justify-content: center;
		margin-bottom: 1.5rem;
	}
	
	.score-circle {
		width: 120px;
		height: 120px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 2rem;
		font-weight: bold;
		color: white;
		box-shadow: 0 4px 10px rgba(0,0,0,0.15);
	}
	
	.score-circle.excellent {
		background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
	}
	
	.score-circle.good {
		background: linear-gradient(135deg, #17a2b8 0%, #20c997 100%);
	}
	
	.score-circle.fair {
		background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);
	}
	
	.score-circle.poor {
		background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
	}
	
	.adherence-breakdown {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	
	.breakdown-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.9rem;
	}
	
	.dot {
		width: 12px;
		height: 12px;
		border-radius: 50%;
	}
	
	.dot.excellent {
		background: #28a745;
	}
	
	.dot.good {
		background: #17a2b8;
	}
	
	.dot.fair {
		background: #ffc107;
	}
	
	.dot.poor {
		background: #dc3545;
	}
	
	/* Success Metrics Card */
	.success-metrics {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 1rem;
		margin-bottom: 1.5rem;
	}
	
	.metric-item {
		text-align: center;
		padding: 1rem;
		background: white;
		border-radius: 8px;
		border: 1px solid #e0e0e0;
	}
	
	.metric-value {
		font-size: 1.8rem;
		font-weight: bold;
		color: #667eea;
	}
	
	.metric-value.improvement {
		color: #28a745;
	}
	
	.metric-label {
		font-size: 0.85rem;
		color: #666;
		margin-top: 0.5rem;
	}
	
	.progress-summary {
		display: flex;
		justify-content: space-around;
		gap: 1rem;
	}
	
	.progress-item {
		flex: 1;
		padding: 0.75rem;
		border-radius: 8px;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	
	.progress-item.improving {
		background: #d4edda;
		color: #155724;
	}
	
	.progress-item.declining {
		background: #f8d7da;
		color: #721c24;
	}
	
	/* High-Risk Section */
	.high-risk-section {
		background: #fff3cd;
		border: 2px solid #ffc107;
		border-radius: 12px;
		padding: 1.5rem;
		margin-top: 1.5rem;
	}
	
	.high-risk-section h3 {
		color: #856404;
		margin: 0 0 1.5rem 0;
	}
	
	.high-risk-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
		gap: 1rem;
	}
	
	.high-risk-card {
		background: white;
		border-radius: 10px;
		padding: 1.25rem;
		box-shadow: 0 2px 8px rgba(0,0,0,0.1);
	}
	
	.high-risk-card.risk-high {
		border-left: 4px solid #dc3545;
	}
	
	.high-risk-card.risk-medium {
		border-left: 4px solid #ffc107;
	}
	
	.risk-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 1rem;
		gap: 0.5rem;
	}
	
	.risk-header h4 {
		margin: 0;
		color: #333;
		font-size: 1rem;
	}
	
	.risk-header .patient-email {
		margin: 0.25rem 0 0 0;
		font-size: 0.85rem;
		color: #667eea;
	}
	
	.risk-badge {
		padding: 0.25rem 0.75rem;
		border-radius: 12px;
		font-size: 0.75rem;
		font-weight: 600;
		white-space: nowrap;
	}
	
	.risk-badge.high {
		background: #dc3545;
		color: white;
	}
	
	.risk-badge.medium {
		background: #ffc107;
		color: #000;
	}
	
	.risk-details {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		margin-bottom: 1rem;
		padding-bottom: 1rem;
		border-bottom: 1px solid #e0e0e0;
	}
	
	.risk-stat {
		display: flex;
		justify-content: space-between;
		font-size: 0.9rem;
	}
	
	.risk-stat .label {
		color: #666;
	}
	
	.risk-stat .value {
		font-weight: 600;
		color: #333;
	}
	
	.risk-factors {
		margin-bottom: 1rem;
		font-size: 0.9rem;
	}
	
	.risk-factors strong {
		color: #856404;
	}
	
	.risk-factors ul {
		margin: 0.5rem 0 0 0;
		padding-left: 1.5rem;
	}
	
	.risk-factors li {
		color: #721c24;
		margin: 0.25rem 0;
	}
	
	.btn-view-patient {
		width: 100%;
		background: #667eea;
		color: white;
		border: none;
		padding: 0.5rem 1rem;
		border-radius: 6px;
		cursor: pointer;
		font-weight: 500;
		transition: background 0.3s;
	}
	
	.btn-view-patient:hover {
		background: #5568d3;
	}
	
	/* Domain Analytics Section */
	.domain-section {
		background: #f8f9fa;
		border-radius: 12px;
		padding: 1.5rem;
		margin-top: 1.5rem;
	}
	
	.section-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}
	
	.section-header h3 {
		margin: 0;
		color: #333;
	}
	
	.toggle-btn {
		background: #6c757d;
		color: white;
		border: none;
		padding: 0.4rem 0.8rem;
		border-radius: 6px;
		cursor: pointer;
		font-size: 0.85rem;
		transition: background 0.3s;
	}
	
	.toggle-btn:hover {
		background: #5a6268;
	}
	
	.domain-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
		gap: 1rem;
		margin-top: 1rem;
	}
	
	.domain-card {
		background: white;
		border: 2px solid #e0e0e0;
		border-radius: 10px;
		padding: 1rem;
		transition: transform 0.2s, box-shadow 0.2s;
	}
	
	.domain-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0,0,0,0.1);
	}
	
	.domain-card h4 {
		margin: 0 0 0.75rem 0;
		color: #667eea;
		font-size: 1rem;
		text-transform: capitalize;
	}
	
	.domain-stats {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.domain-stats .stat {
		display: flex;
		justify-content: space-between;
		font-size: 0.9rem;
	}
	
	.domain-stats .label {
		color: #666;
	}
	
	.domain-stats .value {
		font-weight: 600;
		color: #333;
	}
	
	.domain-stats .value.score {
		color: #667eea;
		font-weight: bold;
	}
	
	/* Cohort Trends */
	.trends-section {
		background: white;
		border: 2px solid #e0e0e0;
		border-radius: 12px;
		padding: 1.5rem;
		margin-top: 1.5rem;
	}
	
	.trends-section h3 {
		margin: 0 0 1rem 0;
		color: #333;
	}
	
	.trends-summary {
		display: flex;
		gap: 2rem;
		margin-bottom: 1.5rem;
		padding: 1rem;
		background: #f8f9fa;
		border-radius: 8px;
	}
	
	.summary-stat {
		display: flex;
		gap: 0.5rem;
		align-items: center;
	}
	
	.summary-stat .label {
		color: #666;
		font-size: 0.9rem;
	}
	
	.summary-stat .value {
		font-weight: bold;
		color: #667eea;
		font-size: 1.1rem;
	}
	
	.trends-timeline {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.week-bar {
		display: grid;
		grid-template-columns: 80px 1fr 200px;
		gap: 1rem;
		align-items: center;
		padding: 0.5rem;
		border-radius: 6px;
		background: #f8f9fa;
	}
	
	.week-label {
		font-size: 0.85rem;
		color: #666;
		font-weight: 500;
	}
	
	.bar-container {
		background: #e0e0e0;
		border-radius: 4px;
		height: 20px;
		overflow: hidden;
	}
	
	.bar {
		height: 100%;
		transition: width 0.3s;
		border-radius: 4px;
	}
	
	.week-stats {
		display: flex;
		gap: 1rem;
		font-size: 0.85rem;
		color: #666;
	}
	
	/* Enhanced Patient Table */
	th.sortable {
		cursor: pointer;
		user-select: none;
		transition: background 0.2s;
	}
	
	th.sortable:hover {
		background: #e9ecef;
	}
	
	.risk-indicator {
		padding: 0.25rem 0.5rem;
		border-radius: 12px;
		font-size: 0.75rem;
		font-weight: 600;
		text-transform: uppercase;
		display: inline-block;
	}
	
	.risk-indicator.high {
		background: #dc3545;
		color: white;
	}
	
	.risk-indicator.medium {
		background: #ffc107;
		color: #000;
	}
	
	.risk-indicator.low {
		background: #28a745;
		color: white;
	}
	
	.adherence-badge {
		padding: 0.25rem 0.5rem;
		border-radius: 12px;
		font-weight: 600;
		font-size: 0.85rem;
		display: inline-block;
	}
	
	.adherence-badge.excellent {
		background: #d4edda;
		color: #155724;
	}
	
	.adherence-badge.good {
		background: #d1ecf1;
		color: #0c5460;
	}
	
	.adherence-badge.fair {
		background: #fff3cd;
		color: #856404;
	}
	
	.adherence-badge.poor {
		background: #f8d7da;
		color: #721c24;
	}
	
	.session-info {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}
	
	.session-info .total {
		font-weight: bold;
		color: #333;
	}
	
	.session-info .recent {
		font-size: 0.8rem;
		color: #666;
	}
	
	.trend-indicator {
		font-weight: 600;
		font-size: 0.9rem;
	}
	
	.trend-indicator.positive {
		color: #28a745;
	}
	
	.trend-indicator.negative {
		color: #dc3545;
	}
	
	tr.risk-high {
		background: rgba(220, 53, 69, 0.05);
	}
	
	tr.risk-medium {
		background: rgba(255, 193, 7, 0.05);
	}

	@media (max-width: 900px) {
		.doctor-dashboard {
			padding: 1rem;
		}

		.header-content,
		.notice-banner-head,
		.analytics-header,
		.section-header,
		.request-card {
			flex-direction: column;
			align-items: stretch;
		}

		.progress-summary,
		.trends-summary,
		.week-stats,
		.request-actions,
		.header-actions {
			flex-wrap: wrap;
		}

		.week-bar {
			grid-template-columns: 1fr;
		}

		.success-metrics {
			grid-template-columns: 1fr;
		}
	}
</style>

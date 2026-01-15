<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import api from '$lib/api.js';
	import { user } from '$lib/stores.js';
	import { onMount } from 'svelte';
	
	let patientId;
	let patientData = null;
	let sessions = [];
	let interventions = [];
	let progressData = null;
	let loading = true;
	let error = '';
	let userData;
	let pageData;
	
	// Intervention form state
	let showInterventionModal = false;
	let interventionType = 'note';
	let interventionDescription = '';
	let suggestedTasks = '';
	let difficultyAdjustments = {};
	let performanceGoals = '';
	
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
		
		loadPatientData();
		
		return () => {
			unsubscribeUser();
			unsubscribePage();
		};
	});
	
	async function loadPatientData() {
		try {
			// Load overview
			const overviewResponse = await api.get(
				`/api/doctor/${userData.id}/patient/${patientId}/overview`
			);
			patientData = overviewResponse.data;
			
			// Load sessions
			const sessionsResponse = await api.get(
				`/api/doctor/${userData.id}/patient/${patientId}/sessions?limit=20`
			);
			sessions = sessionsResponse.data.sessions;
			
			// Load interventions
			const interventionsResponse = await api.get(
				`/api/doctor/${userData.id}/patient/${patientId}/interventions`
			);
			interventions = interventionsResponse.data.interventions;
			
			// Load progress monitoring data
			const progressResponse = await api.get(
				`/api/doctor/${userData.id}/patient/${patientId}/progress-monitoring`
			);
			progressData = progressResponse.data;
			
		} catch (err) {
			error = 'Failed to load patient data';
			console.error(err);
		} finally {
			loading = false;
		}
	}
	
	async function submitIntervention() {
		try {
			const data = {};
			
			if (interventionType === 'training_adjustment') {
				if (Object.keys(difficultyAdjustments).length > 0) {
					data.difficulty_adjustments = difficultyAdjustments;
				}
				if (performanceGoals.trim()) {
					data.performance_goals = performanceGoals.trim();
				}
			} else if (interventionType === 'task_recommendation') {
				data.suggested_tasks = suggestedTasks.split(',').map(t => t.trim()).filter(t => t);
			}
			
			await api.post(
				`/api/doctor/${userData.id}/patient/${patientId}/intervention`,
				null,
				{
					params: {
						intervention_type: interventionType,
						description: interventionDescription,
						intervention_data: Object.keys(data).length > 0 ? JSON.stringify(data) : null
					}
				}
			);
			
			alert('Intervention added successfully!');
			closeInterventionModal();
			await loadPatientData();
		} catch (err) {
			alert('Failed to add intervention: ' + (err.response?.data?.detail || 'Unknown error'));
		}
	}
	
	function openInterventionModal() {
		showInterventionModal = true;
		interventionType = 'note';
		interventionDescription = '';
		suggestedTasks = '';
		difficultyAdjustments = {};
		performanceGoals = '';
	}
	
	function closeInterventionModal() {
		showInterventionModal = false;
	}
	
	function adjustDifficulty(domain, change) {
		if (!difficultyAdjustments[domain]) {
			difficultyAdjustments[domain] = 1; // default
		}
		difficultyAdjustments[domain] = Math.max(1, Math.min(10, difficultyAdjustments[domain] + change));
		difficultyAdjustments = {...difficultyAdjustments}; // trigger reactivity
	}
	
	function getDomainColor(domain) {
		const colors = {
			working_memory: '#667eea',
			attention: '#f093fb',
			flexibility: '#4facfe',
			planning: '#43e97b',
			processing_speed: '#fa709a',
			visual_scanning: '#feca57'
		};
		return colors[domain] || '#999';
	}
	
	function formatDate(dateStr) {
		if (!dateStr) return 'N/A';
		return new Date(dateStr).toLocaleString();
	}
	
	function formatShortDate(dateStr) {
		if (!dateStr) return 'N/A';
		return new Date(dateStr).toLocaleDateString();
	}
</script>

<div class="patient-detail">
	{#if loading}
		<div class="loading">Loading patient data...</div>
	{:else if error}
		<div class="error">{error}</div>
	{:else if patientData}
		<div class="header">
			<button on:click={() => goto('/doctor/dashboard')} class="back-btn">
				← Back to Dashboard
			</button>
			<div class="header-content">
				<div>
					<h1>{patientData.patient_info.full_name || patientData.patient_info.email}</h1>
					<p class="diagnosis">{patientData.patient_info.diagnosis || 'No diagnosis specified'}</p>
					{#if patientData.patient_info.treatment_goal}
						<p class="treatment-goal">Goal: {patientData.patient_info.treatment_goal}</p>
					{/if}
				</div>
				<div class="header-actions">
					<button class="btn-reports" on:click={() => goto(`/doctor/patient/${patientId}/reports`)}>
						📊 Progress Reports
					</button>
					<button class="btn-intervention" on:click={openInterventionModal}>
						+ Add Intervention
					</button>
				</div>
			</div>
		</div>
		
		<!-- Quick Info Box -->
		<div class="info-box">
			<div class="info-icon">ℹ️</div>
			<div class="info-content">
				<strong>Patient Overview:</strong> This page shows a quick snapshot of the patient's current status and recent activity. 
				For detailed analytics, baseline comparisons, and comprehensive reports, click the 
				<strong style="color: #4fc3f7;">📊 Progress Reports</strong> button above.
			</div>
		</div>
		
		<!-- Interventions Section -->
		{#if interventions.length > 0}
			<div class="section">
				<h2>📋 Recent Interventions & Recommendations</h2>
				<div class="interventions-list">
					{#each interventions as intervention}
						<div class="intervention-card">
							<div class="intervention-header">
								<span class="intervention-type-badge type-{intervention.type}">
									{intervention.type.replace('_', ' ')}
								</span>
								<span class="intervention-date">{formatDate(intervention.created_at)}</span>
							</div>
							<p class="intervention-desc">{intervention.description}</p>
							{#if intervention.data}
								<div class="intervention-data">
									{#if intervention.data.suggested_tasks}
										<div><strong>Suggested Tasks:</strong> {intervention.data.suggested_tasks.join(', ')}</div>
									{/if}
									{#if intervention.data.difficulty_adjustments}
										<div><strong>Difficulty Adjustments:</strong> 
											{JSON.stringify(intervention.data.difficulty_adjustments)}
										</div>
									{/if}
									{#if intervention.data.performance_goals}
										<div><strong>Goals:</strong> {intervention.data.performance_goals}</div>
									{/if}
								</div>
							{/if}
						</div>
					{/each}
				</div>
			</div>
		{/if}
		
		<!-- Overview Stats -->
		<div class="overview-grid">
			<div class="overview-card">
				<h3>Training Summary</h3>
				<div class="stat-row">
					<span>Total Sessions:</span>
					<strong>{patientData.training_summary.total_sessions}</strong>
				</div>
				<div class="stat-row">
					<span>Current Streak:</span>
					<strong>{patientData.training_summary.current_streak} days</strong>
				</div>
				<div class="stat-row">
					<span>Longest Streak:</span>
					<strong>{patientData.training_summary.longest_streak} days</strong>
				</div>
				<div class="stat-row">
					<span>Last Session:</span>
					<strong>{formatShortDate(patientData.training_summary.last_session)}</strong>
				</div>
			</div>
			
			<div class="overview-card">
				<h3>Recent Performance (7 days)</h3>
				<div class="stat-row">
					<span>Sessions:</span>
					<strong>{patientData.recent_performance.sessions_last_7_days}</strong>
				</div>
				<div class="stat-row">
					<span>Avg Score:</span>
					<strong>{patientData.recent_performance.avg_score}/100</strong>
				</div>
				<div class="stat-row">
					<span>Avg Accuracy:</span>
					<strong>{patientData.recent_performance.avg_accuracy}%</strong>
				</div>
			</div>
			
			<div class="overview-card">
				<h3>Focus Areas</h3>
				<div class="focus-section">
					<div>
						<strong>Primary Focus:</strong>
						{#if patientData.focus_areas.primary && patientData.focus_areas.primary.length > 0}
							<div class="focus-tags">
								{#each patientData.focus_areas.primary as area}
									<span class="focus-tag primary">{area.replace('_', ' ')}</span>
								{/each}
							</div>
						{:else}
							<span class="no-data">None set</span>
						{/if}
					</div>
					<div>
						<strong>Secondary:</strong>
						{#if patientData.focus_areas.secondary && patientData.focus_areas.secondary.length > 0}
							<div class="focus-tags">
								{#each patientData.focus_areas.secondary as area}
									<span class="focus-tag secondary">{area.replace('_', ' ')}</span>
								{/each}
							</div>
						{:else}
							<span class="no-data">None set</span>
						{/if}
					</div>
				</div>
			</div>
		</div>
		
		<!-- Progress Monitoring Section -->
		{#if progressData}
			<div class="section progress-monitoring">
				<h2>📊 Progress Monitoring</h2>
				
				<!-- Concerning Areas Alert -->
				{#if progressData.concerning_areas && progressData.concerning_areas.length > 0}
					<div class="alert-box warning">
						<h3>⚠️ Areas Requiring Attention</h3>
						<div class="concerning-list">
							{#each progressData.concerning_areas as concern}
								<div class="concern-item severity-{concern.severity}">
									<div class="concern-header">
										<span class="concern-domain">{concern.domain.replace('_', ' ')}</span>
										<span class="concern-severity">{concern.severity}</span>
									</div>
									<div class="concern-issue">{concern.issue.replace('_', ' ')}</div>
									<div class="concern-details">{concern.details}</div>
								</div>
							{/each}
						</div>
					</div>
				{/if}
				
				<!-- Adherence Tracking -->
				<div class="monitoring-card">
					<h3>📅 Training Adherence</h3>
					<div class="adherence-summary">
						<div class="adherence-status status-{progressData.adherence.status}">
							<div class="status-label">{progressData.adherence.status.replace('_', ' ').toUpperCase()}</div>
							<div class="adherence-rate">{progressData.adherence.adherence_rate}%</div>
						</div>
						<div class="adherence-stats">
							<div class="stat-item">
								<span class="stat-label">Total Sessions:</span>
								<span class="stat-value">{progressData.adherence.total_sessions}</span>
							</div>
							<div class="stat-item">
								<span class="stat-label">Expected:</span>
								<span class="stat-value">{progressData.adherence.expected_sessions}</span>
							</div>
							<div class="stat-item">
								<span class="stat-label">Last 7 days:</span>
								<span class="stat-value">{progressData.adherence.sessions_last_7_days}</span>
							</div>
							<div class="stat-item">
								<span class="stat-label">Last 30 days:</span>
								<span class="stat-value">{progressData.adherence.sessions_last_30_days}</span>
							</div>
							<div class="stat-item">
								<span class="stat-label">Avg Days Between:</span>
								<span class="stat-value">{progressData.adherence.avg_days_between_sessions} days</span>
							</div>
						</div>
					</div>
				</div>
				
				<!-- Trend Analysis -->
				{#if Object.keys(progressData.trends).length > 0}
					<div class="monitoring-card">
						<h3>📉 Recent Trends (Last 7 days vs Previous 7 days)</h3>
						<div class="trends-grid">
							{#each Object.entries(progressData.trends) as [domain, trend]}
								<div class="trend-card direction-{trend.direction}">
									<h4>{domain.replace('_', ' ')}</h4>
									<div class="trend-comparison">
										<div class="trend-value">
											<span class="label">Previous</span>
											<span class="value">{trend.previous_avg}</span>
										</div>
										<div class="trend-arrow">
											{#if trend.direction === 'upward'}
												<span class="arrow up">↗</span>
											{:else if trend.direction === 'downward'}
												<span class="arrow down">↘</span>
											{:else}
												<span class="arrow stable">→</span>
											{/if}
										</div>
										<div class="trend-value">
											<span class="label">Recent</span>
											<span class="value">{trend.recent_avg}</span>
										</div>
									</div>
									<div class="trend-change {trend.change >= 0 ? 'positive' : 'negative'}">
										{trend.change >= 0 ? '+' : ''}{trend.change} points
									</div>
									{#if trend.is_concerning}
										<div class="trend-warning">⚠️ Concerning decline</div>
									{/if}
								</div>
							{/each}
						</div>
					</div>
				{/if}
				
				<!-- Domain-Specific Improvements -->
				{#if Object.keys(progressData.domain_improvements).length > 0}
					<div class="monitoring-card">
						<h3>🎯 Domain-Specific Improvements</h3>
						<div class="improvements-grid">
							{#each Object.entries(progressData.domain_improvements) as [domain, improvement]}
								<div class="improvement-card trending-{improvement.trending}">
									<h4>{domain.replace('_', ' ')}</h4>
									<div class="improvement-summary">
										<div class="avg-comparison">
											<div>
												<span class="label">Early Average:</span>
												<span class="value">{improvement.early_avg}</span>
											</div>
											<div>
												<span class="label">Recent Average:</span>
												<span class="value">{improvement.recent_avg}</span>
											</div>
										</div>
										<div class="overall-change {improvement.overall_improvement >= 0 ? 'positive' : 'negative'}">
											Overall: {improvement.overall_improvement >= 0 ? '+' : ''}{improvement.overall_improvement}
										</div>
									</div>
									<div class="recent-scores">
										<span class="label">Last 5 scores:</span>
										<div class="scores-list">
											{#each improvement.recent_scores as score}
												<span class="score-badge">{score}</span>
											{/each}
										</div>
									</div>
									<div class="session-total">{improvement.total_sessions} total sessions</div>
								</div>
							{/each}
						</div>
					</div>
				{/if}
			</div>
		{/if}
		
		<!-- Recent Sessions -->
		<div class="section">
			<h2>Recent Training Sessions</h2>
			<div class="sessions-table">
				<table>
					<thead>
						<tr>
							<th>Date</th>
							<th>Domain</th>
							<th>Task</th>
							<th>Difficulty</th>
							<th>Score</th>
							<th>Accuracy</th>
							<th>RT (ms)</th>
						</tr>
					</thead>
					<tbody>
						{#each sessions as session}
							<tr>
								<td>{formatDate(session.completed_at)}</td>
								<td>
									<span 
										class="domain-badge" 
										style="background: {getDomainColor(session.domain)}; color: white; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.85rem;"
									>
										{session.domain.replace('_', ' ')}
									</span>
								</td>
								<td>{session.task_code || session.task_type}</td>
								<td>Level {session.difficulty}</td>
								<td><strong>{session.score}</strong></td>
								<td>{session.accuracy}%</td>
								<td>{session.reaction_time || 'N/A'}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	{/if}
</div>

<!-- Intervention Modal -->
{#if showInterventionModal}
	<div class="modal-overlay" on:click={closeInterventionModal}>
		<div class="modal-content" on:click|stopPropagation>
			<div class="modal-header">
				<h2>Add Intervention / Recommendation</h2>
				<button class="close-btn" on:click={closeInterventionModal}>×</button>
			</div>
			
			<div class="modal-body">
				<div class="form-group">
					<label>Intervention Type</label>
					<select bind:value={interventionType}>
						<option value="note">Clinical Note/Observation</option>
						<option value="task_recommendation">Task Recommendation</option>
						<option value="training_adjustment">Training Plan Adjustment</option>
						<option value="goal_setting">Performance Goal</option>
						<option value="check_in">Schedule Check-in</option>
					</select>
				</div>
				
				<div class="form-group">
					<label>Description / Notes</label>
					<textarea 
						bind:value={interventionDescription}
						placeholder="Enter your observations, recommendations, or notes..."
						rows="4"
						required
					></textarea>
				</div>
				
				{#if interventionType === 'task_recommendation'}
					<div class="form-group">
						<label>Suggested Tasks (comma-separated)</label>
						<input 
							type="text" 
							bind:value={suggestedTasks}
							placeholder="e.g., digit_span, trail_making, stroop"
						/>
					</div>
				{/if}
				
				{#if interventionType === 'training_adjustment'}
					<div class="form-group">
						<label>Difficulty Adjustments</label>
						<div class="difficulty-controls">
							{#each Object.keys(patientData.domain_performance) as domain}
								<div class="difficulty-row">
									<span>{domain.replace('_', ' ')}</span>
									<div class="difficulty-buttons">
										<button on:click={() => adjustDifficulty(domain, -1)}>-</button>
										<span>{difficultyAdjustments[domain] || 1}</span>
										<button on:click={() => adjustDifficulty(domain, 1)}>+</button>
									</div>
								</div>
							{/each}
						</div>
					</div>
					
					<div class="form-group">
						<label>Performance Goals</label>
						<textarea 
							bind:value={performanceGoals}
							placeholder="Enter specific performance goals..."
							rows="3"
						></textarea>
					</div>
				{/if}
			</div>
			
			<div class="modal-footer">
				<button class="btn-cancel" on:click={closeInterventionModal}>Cancel</button>
				<button 
					class="btn-submit" 
					on:click={submitIntervention}
					disabled={!interventionDescription.trim()}
				>
					Add Intervention
				</button>
			</div>
		</div>
	</div>
{/if}

<style>
	.patient-detail {
		max-width: 1400px;
		margin: 0 auto;
		padding: 2rem;
		min-height: 100vh;
		background: #f8f9fa;
	}
	
	.header {
		margin-bottom: 2rem;
	}
	
	.header-content {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-top: 1rem;
	}
	
	.header-actions {
		display: flex;
		gap: 1rem;
		align-items: center;
	}
	
	.btn-reports {
		background: linear-gradient(135deg, #4fc3f7 0%, #2196f3 100%);
		color: white;
		border: none;
		padding: 0.75rem 1.5rem;
		border-radius: 8px;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s;
		font-size: 1rem;
	}
	
	.btn-reports:hover {
		transform: translateY(-2px);
		box-shadow: 0 8px 20px rgba(79, 195, 247, 0.3);
	}
	
	.btn-intervention {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		padding: 0.75rem 1.5rem;
		border-radius: 8px;
		font-weight: 600;
		cursor: pointer;
		transition: transform 0.2s;
	}
	
	.btn-intervention:hover {
		transform: translateY(-2px);
	}
	
	.back-btn {
		background: #f0f0f0;
		border: none;
		padding: 0.5rem 1rem;
		border-radius: 6px;
		cursor: pointer;
		margin-bottom: 1rem;
		font-size: 0.95rem;
		transition: background 0.3s;
	}
	
	.back-btn:hover {
		background: #e0e0e0;
	}
	
	h1 {
		font-size: 2rem;
		margin-bottom: 0.5rem;
		color: #333;
	}
	
	.diagnosis {
		color: #666;
		font-size: 1.1rem;
		margin-bottom: 0.25rem;
	}
	
	.treatment-goal {
		color: #667eea;
		font-style: italic;
		font-size: 0.95rem;
	}
	
	.info-box {
		display: flex;
		align-items: center;
		gap: 1rem;
		background: linear-gradient(135deg, rgba(79, 195, 247, 0.1), rgba(33, 150, 243, 0.05));
		border: 1px solid rgba(79, 195, 247, 0.3);
		border-radius: 12px;
		padding: 1rem 1.5rem;
		margin-bottom: 2rem;
	}
	
	.info-icon {
		font-size: 1.5rem;
		flex-shrink: 0;
	}
	
	.info-content {
		color: #333;
		font-size: 0.95rem;
		line-height: 1.5;
	}
	
	.overview-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		gap: 1rem;
		margin-bottom: 2rem;
	}
	
	.overview-card {
		background: white;
		padding: 1.5rem;
		border-radius: 12px;
		box-shadow: 0 2px 10px rgba(0,0,0,0.1);
	}
	
	.overview-card h3 {
		margin-bottom: 1rem;
		color: #333;
		font-size: 1.1rem;
	}
	
	.stat-row {
		display: flex;
		justify-content: space-between;
		padding: 0.5rem 0;
		border-bottom: 1px solid #f0f0f0;
	}
	
	.stat-row:last-child {
		border-bottom: none;
	}
	
	.focus-section {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.focus-tags {
		margin-top: 0.5rem;
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
	}
	
	.focus-tag {
		display: inline-block;
		padding: 0.25rem 0.75rem;
		border-radius: 20px;
		font-size: 0.85rem;
		text-transform: capitalize;
	}
	
	.focus-tag.primary {
		background: #fecaca;
		color: #991b1b;
	}
	
	.focus-tag.secondary {
		background: #fef3c7;
		color: #92400e;
	}
	
	.no-data {
		color: #999;
		font-size: 0.9rem;
	}
	
	.section {
		background: white;
		padding: 2rem;
		border-radius: 12px;
		box-shadow: 0 2px 10px rgba(0,0,0,0.1);
		margin-bottom: 2rem;
	}
	
	.section h2 {
		margin-bottom: 0.5rem;
		color: #333;
	}
	
	.section-subtitle {
		color: #666;
		font-size: 0.9rem;
		margin-bottom: 1.5rem;
	}
	
	.baseline-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
	}
	
	.baseline-card {
		background: #f8f9fa;
		padding: 1rem;
		border-radius: 8px;
		text-align: center;
	}
	
	.baseline-label {
		font-size: 0.85rem;
		color: #666;
		margin-bottom: 0.5rem;
		text-transform: capitalize;
	}
	
	.baseline-value {
		font-size: 1.75rem;
		font-weight: bold;
		color: #667eea;
	}
	
	.domains-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: 1rem;
	}
	
	.domain-card {
		background: #f8f9fa;
		padding: 1rem;
		border-radius: 8px;
	}
	
	.domain-card h4 {
		text-transform: capitalize;
		margin-bottom: 0.75rem;
		color: #333;
	}
	
	.domain-stats div {
		display: flex;
		justify-content: space-between;
		padding: 0.25rem 0;
	}
	
	.sessions-table {
		overflow-x: auto;
	}
	
	table {
		width: 100%;
		border-collapse: collapse;
	}
	
	th {
		background: #f8f9fa;
		padding: 0.75rem;
		text-align: left;
		font-weight: 600;
		border-bottom: 2px solid #e0e0e0;
		font-size: 0.9rem;
	}
	
	td {
		padding: 0.75rem;
		border-bottom: 1px solid #e0e0e0;
		font-size: 0.9rem;
	}
	
	tr:hover {
		background: #f8f9fa;
	}
	
	.loading, .error {
		text-align: center;
		padding: 3rem;
		font-size: 1.1rem;
	}
	
	.error {
		color: #c33;
		background: #fee;
		border-radius: 8px;
	}

	/* Progress Monitoring Styles */
	.progress-monitoring {
		background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
		padding: 2rem;
		border-radius: 12px;
		margin: 2rem 0;
	}

	.progress-monitoring h2 {
		margin-bottom: 1.5rem;
		color: #333;
	}

	.alert-box {
		background: white;
		border-radius: 12px;
		padding: 1.5rem;
		margin-bottom: 1.5rem;
		border-left: 5px solid #f59e0b;
	}

	.alert-box.warning {
		border-left-color: #f59e0b;
		background: #fffbeb;
	}

	.alert-box h3 {
		margin-bottom: 1rem;
		color: #92400e;
	}

	.concerning-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.concern-item {
		background: white;
		padding: 1rem;
		border-radius: 8px;
		border-left: 4px solid #f59e0b;
	}

	.concern-item.severity-high {
		border-left-color: #dc2626;
		background: #fef2f2;
	}

	.concern-item.severity-medium {
		border-left-color: #f59e0b;
		background: #fffbeb;
	}

	.concern-item.severity-low {
		border-left-color: #3b82f6;
		background: #eff6ff;
	}

	.concern-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
	}

	.concern-domain {
		font-weight: 700;
		text-transform: capitalize;
		font-size: 1rem;
	}

	.concern-severity {
		text-transform: uppercase;
		font-size: 0.75rem;
		font-weight: 600;
		padding: 0.25rem 0.5rem;
		border-radius: 4px;
		background: rgba(0, 0, 0, 0.1);
	}

	.concern-issue {
		font-weight: 600;
		color: #666;
		margin-bottom: 0.25rem;
		text-transform: capitalize;
	}

	.concern-details {
		color: #888;
		font-size: 0.9rem;
	}

	.monitoring-card {
		background: white;
		border-radius: 12px;
		padding: 1.5rem;
		margin-bottom: 1.5rem;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	}

	.monitoring-card h3 {
		margin-bottom: 1.25rem;
		color: #333;
		font-size: 1.25rem;
	}

	.adherence-summary {
		display: grid;
		grid-template-columns: auto 1fr;
		gap: 2rem;
		align-items: center;
	}

	.adherence-status {
		text-align: center;
		padding: 1.5rem;
		border-radius: 12px;
		min-width: 150px;
	}

	.adherence-status.status-excellent {
		background: linear-gradient(135deg, #10b981 0%, #059669 100%);
		color: white;
	}

	.adherence-status.status-good {
		background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
		color: white;
	}

	.adherence-status.status-needs_improvement {
		background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
		color: white;
	}

	.adherence-status.status-concerning {
		background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
		color: white;
	}

	.status-label {
		font-weight: 700;
		font-size: 0.9rem;
		margin-bottom: 0.5rem;
	}

	.adherence-rate {
		font-size: 2.5rem;
		font-weight: 800;
	}

	.adherence-stats {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: 1rem;
	}

	.stat-item {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.stat-label {
		font-size: 0.85rem;
		color: #666;
	}

	.stat-value {
		font-size: 1.25rem;
		font-weight: 700;
		color: #333;
	}

	.comparison-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: 1rem;
	}

	.comparison-card {
		background: #f9fafb;
		padding: 1.25rem;
		border-radius: 10px;
		border-left: 4px solid #e5e7eb;
	}

	.comparison-card.status-improving {
		border-left-color: #10b981;
		background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%);
	}

	.comparison-card.status-declining {
		border-left-color: #ef4444;
		background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
	}

	.comparison-card.status-stable {
		border-left-color: #6b7280;
	}

	.comparison-card h4 {
		text-transform: capitalize;
		margin-bottom: 0.75rem;
		color: #333;
		font-size: 1rem;
	}

	.comparison-values {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 0.75rem;
	}

	.comparison-values .baseline,
	.comparison-values .current {
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.comparison-values .label {
		font-size: 0.75rem;
		color: #666;
		margin-bottom: 0.25rem;
	}

	.comparison-values .value {
		font-size: 1.5rem;
		font-weight: 700;
		color: #333;
	}

	.comparison-values .arrow {
		font-size: 1.5rem;
		color: #999;
	}

	.improvement-indicator {
		font-weight: 700;
		font-size: 1.1rem;
		text-align: center;
		padding: 0.5rem;
		border-radius: 6px;
		margin-bottom: 0.5rem;
	}

	.improvement-indicator.positive {
		background: #d1fae5;
		color: #065f46;
	}

	.improvement-indicator.negative {
		background: #fee2e2;
		color: #991b1b;
	}

	.session-count {
		text-align: center;
		font-size: 0.85rem;
		color: #666;
	}

	.trends-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: 1rem;
	}

	.trend-card {
		background: #f9fafb;
		padding: 1.25rem;
		border-radius: 10px;
		border-top: 3px solid #e5e7eb;
	}

	.trend-card.direction-upward {
		border-top-color: #10b981;
		background: linear-gradient(180deg, #ecfdf5 0%, #f9fafb 50%);
	}

	.trend-card.direction-downward {
		border-top-color: #ef4444;
		background: linear-gradient(180deg, #fef2f2 0%, #f9fafb 50%);
	}

	.trend-card.direction-stable {
		border-top-color: #6b7280;
	}

	.trend-card h4 {
		text-transform: capitalize;
		margin-bottom: 0.75rem;
		color: #333;
		font-size: 1rem;
	}

	.trend-comparison {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 0.75rem;
	}

	.trend-value {
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.trend-value .label {
		font-size: 0.75rem;
		color: #666;
		margin-bottom: 0.25rem;
	}

	.trend-value .value {
		font-size: 1.25rem;
		font-weight: 700;
		color: #333;
	}

	.trend-arrow {
		font-size: 2rem;
	}

	.trend-arrow .arrow.up {
		color: #10b981;
	}

	.trend-arrow .arrow.down {
		color: #ef4444;
	}

	.trend-arrow .arrow.stable {
		color: #6b7280;
	}

	.trend-change {
		text-align: center;
		font-weight: 600;
		padding: 0.5rem;
		border-radius: 6px;
		margin-bottom: 0.5rem;
	}

	.trend-change.positive {
		background: #d1fae5;
		color: #065f46;
	}

	.trend-change.negative {
		background: #fee2e2;
		color: #991b1b;
	}

	.trend-warning {
		background: #fef3c7;
		color: #92400e;
		text-align: center;
		padding: 0.5rem;
		border-radius: 6px;
		font-weight: 600;
		font-size: 0.85rem;
	}

	.improvements-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: 1rem;
	}

	.improvement-card {
		background: #f9fafb;
		padding: 1.25rem;
		border-radius: 10px;
		border: 2px solid #e5e7eb;
	}

	.improvement-card.trending-up {
		border-color: #10b981;
		background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%);
	}

	.improvement-card.trending-down {
		border-color: #ef4444;
		background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
	}

	.improvement-card h4 {
		text-transform: capitalize;
		margin-bottom: 0.75rem;
		color: #333;
		font-size: 1rem;
	}

	.improvement-summary {
		margin-bottom: 1rem;
	}

	.avg-comparison {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		margin-bottom: 0.5rem;
	}

	.avg-comparison > div {
		display: flex;
		justify-content: space-between;
	}

	.avg-comparison .label {
		color: #666;
		font-size: 0.9rem;
	}

	.avg-comparison .value {
		font-weight: 700;
		color: #333;
	}

	.overall-change {
		text-align: center;
		font-weight: 700;
		font-size: 1.1rem;
		padding: 0.5rem;
		border-radius: 6px;
	}

	.overall-change.positive {
		background: #d1fae5;
		color: #065f46;
	}

	.overall-change.negative {
		background: #fee2e2;
		color: #991b1b;
	}

	.recent-scores {
		margin: 1rem 0 0.5rem 0;
	}

	.recent-scores .label {
		display: block;
		font-size: 0.85rem;
		color: #666;
		margin-bottom: 0.5rem;
	}

	.scores-list {
		display: flex;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.score-badge {
		background: #667eea;
		color: white;
		padding: 0.25rem 0.75rem;
		border-radius: 20px;
		font-weight: 600;
		font-size: 0.9rem;
	}

	.session-total {
		text-align: center;
		font-size: 0.85rem;
		color: #666;
		margin-top: 0.5rem;
	}


	/* Modal Styles */
	.modal-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
	}

	.modal-content {
		background: white;
		border-radius: 12px;
		max-width: 600px;
		width: 90%;
		max-height: 90vh;
		overflow-y: auto;
	}

	.modal-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1.5rem;
		border-bottom: 2px solid #f0f0f0;
	}

	.modal-header h2 {
		margin: 0;
		color: #667eea;
		font-size: 1.5rem;
	}

	.close-btn {
		background: none;
		border: none;
		font-size: 2rem;
		color: #999;
		cursor: pointer;
		line-height: 1;
		padding: 0;
		width: 32px;
		height: 32px;
	}

	.close-btn:hover {
		color: #333;
	}

	.modal-body {
		padding: 1.5rem;
	}

	.form-group {
		margin-bottom: 1.25rem;
	}

	.form-group label {
		display: block;
		margin-bottom: 0.5rem;
		font-weight: 600;
		color: #555;
	}

	.form-group select,
	.form-group input,
	.form-group textarea {
		width: 100%;
		padding: 0.75rem;
		border: 2px solid #e0e0e0;
		border-radius: 8px;
		font-size: 0.95rem;
		font-family: inherit;
	}

	.form-group select:focus,
	.form-group input:focus,
	.form-group textarea:focus {
		outline: none;
		border-color: #667eea;
	}

	.difficulty-controls {
		margin-top: 0.5rem;
	}

	.difficulty-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.5rem;
		border-bottom: 1px solid #f0f0f0;
	}

	.difficulty-row span:first-child {
		text-transform: capitalize;
		font-weight: 500;
	}

	.difficulty-buttons {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.difficulty-buttons button {
		width: 32px;
		height: 32px;
		border: 2px solid #667eea;
		background: white;
		color: #667eea;
		border-radius: 6px;
		cursor: pointer;
		font-weight: bold;
		transition: all 0.2s;
	}

	.difficulty-buttons button:hover {
		background: #667eea;
		color: white;
	}

	.difficulty-buttons span {
		min-width: 30px;
		text-align: center;
		font-weight: 600;
	}

	.modal-footer {
		display: flex;
		gap: 0.75rem;
		padding: 1.5rem;
		border-top: 2px solid #f0f0f0;
	}

	.btn-cancel,
	.btn-submit {
		flex: 1;
		padding: 0.75rem 1.5rem;
		border: none;
		border-radius: 8px;
		font-size: 0.95rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
	}

	.btn-cancel {
		background: #e0e0e0;
		color: #666;
	}

	.btn-cancel:hover {
		background: #d0d0d0;
	}

	.btn-submit {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
	}

	.btn-submit:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
	}

	.btn-submit:disabled {
		opacity: 0.5;
		cursor: not-allowed;
		transform: none;
	}
</style>

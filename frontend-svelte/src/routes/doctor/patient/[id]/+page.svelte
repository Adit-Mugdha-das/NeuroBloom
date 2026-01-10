<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import api from '$lib/api.js';
	import { user } from '$lib/stores.js';
	import { onMount } from 'svelte';
	
	let patientId;
	let patientData = null;
	let sessions = [];
	let loading = true;
	let error = '';
	let userData;
	let pageData;
	
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
			
		} catch (err) {
			error = 'Failed to load patient data';
			console.error(err);
		} finally {
			loading = false;
		}
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
			<h1>{patientData.patient_info.full_name || patientData.patient_info.email}</h1>
			<p class="diagnosis">{patientData.patient_info.diagnosis || 'No diagnosis specified'}</p>
			{#if patientData.patient_info.treatment_goal}
				<p class="treatment-goal">Goal: {patientData.patient_info.treatment_goal}</p>
			{/if}
		</div>
		
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
		
		<!-- Baseline Information -->
		{#if patientData.baseline.completed}
			<div class="section">
				<h2>Baseline Assessment</h2>
				<p class="section-subtitle">Completed on {formatShortDate(patientData.baseline.date)}</p>
				<div class="baseline-grid">
					<div class="baseline-card">
						<div class="baseline-label">Overall Cognitive Score</div>
						<div class="baseline-value">{patientData.baseline.overall_score?.toFixed(1) || 'N/A'}</div>
					</div>
					{#if patientData.baseline.domain_scores}
						{#each Object.entries(patientData.baseline.domain_scores) as [domain, score]}
							{#if score !== null}
								<div class="baseline-card">
									<div class="baseline-label">{domain.replace('_', ' ')}</div>
									<div class="baseline-value">{score.toFixed(1)}</div>
								</div>
							{/if}
						{/each}
					{/if}
				</div>
			</div>
		{/if}
		
		<!-- Domain Performance -->
		<div class="section">
			<h2>Domain Performance</h2>
			<div class="domains-grid">
				{#each Object.entries(patientData.domain_performance) as [domain, stats]}
					<div class="domain-card" style="border-left: 4px solid {getDomainColor(domain)}">
						<h4>{domain.replace('_', ' ')}</h4>
						<div class="domain-stats">
							<div>
								<span>Baseline:</span>
								<strong>{stats.baseline_score?.toFixed(1) || 'N/A'}</strong>
							</div>
							<div>
								<span>Current Avg:</span>
								<strong>{stats.avg_score.toFixed(1)}</strong>
							</div>
							<div>
								<span>Accuracy:</span>
								<strong>{stats.avg_accuracy.toFixed(1)}%</strong>
							</div>
							<div>
								<span>Sessions:</span>
								<strong>{stats.count}</strong>
							</div>
						</div>
					</div>
				{/each}
			</div>
		</div>
		
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
</style>

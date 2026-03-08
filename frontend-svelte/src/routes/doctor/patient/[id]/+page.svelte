<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import api from '$lib/api.js';
	import BiomarkersPanel from '$lib/components/BiomarkersPanel.svelte';
	import DoctorWorkspaceShell from '$lib/components/DoctorWorkspaceShell.svelte';
	import { user } from '$lib/stores.js';
	import { onMount } from 'svelte';

	let patientId;
	let patientData = null;
	let sessions = [];
	let interventions = [];
	let progressData = null;
	let biomarkerData = null;
	let loading = true;
	let error = '';
	let userData;

	let showInterventionModal = false;
	let interventionType = 'note';
	let interventionDescription = '';
	let suggestedTasks = '';
	let difficultyAdjustments = {};

	let showFocusAreasModal = false;
	let primaryFocusAreas = [];
	let secondaryFocusAreas = [];
	let maintenanceAreas = [];
	let focusAreasNotes = '';

	const allDomains = [
		{ id: 'working_memory', label: 'Working Memory' },
		{ id: 'attention', label: 'Attention' },
		{ id: 'flexibility', label: 'Flexibility' },
		{ id: 'planning', label: 'Planning' },
		{ id: 'processing_speed', label: 'Processing Speed' },
		{ id: 'visual_scanning', label: 'Visual Scanning' }
	];

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

		loadPatientData();

		return () => {
			unsubscribeUser();
			unsubscribePage();
		};
	});

	async function loadPatientData() {
		loading = true;
		error = '';

		try {
			const overviewResponse = await api.get(`/api/doctor/${userData.id}/patient/${patientId}/overview`);
			patientData = overviewResponse.data;

			const sessionsResponse = await api.get(`/api/doctor/${userData.id}/patient/${patientId}/sessions?limit=20`);
			sessions = sessionsResponse.data.sessions || [];

			const interventionsResponse = await api.get(`/api/doctor/${userData.id}/patient/${patientId}/interventions`);
			interventions = interventionsResponse.data.interventions || [];

			const progressResponse = await api.get(`/api/doctor/${userData.id}/patient/${patientId}/progress-monitoring`);
			progressData = progressResponse.data;

			try {
				const biomarkersResponse = await api.get(`/api/training/advanced-analytics/${patientId}/biomarkers`, {
					params: { days: 30 }
				});
				biomarkerData = biomarkersResponse.data;
			} catch (requestError) {
				console.log('Biomarkers not yet available for patient:', requestError);
			}
		} catch (requestError) {
			error = requestError.response?.data?.detail || 'Failed to load patient data';
			console.error(requestError);
		} finally {
			loading = false;
		}
	}

	async function submitIntervention() {
		try {
			const data = {};

			if (interventionType === 'task_recommendation') {
				data.suggested_tasks = suggestedTasks.split(',').map((task) => task.trim()).filter(Boolean);
			}

			await api.post(`/api/doctor/${userData.id}/patient/${patientId}/intervention`, null, {
				params: {
					intervention_type: interventionType,
					description: interventionDescription,
					intervention_data: Object.keys(data).length > 0 ? JSON.stringify(data) : null
				}
			});

			closeInterventionModal();
			await loadPatientData();
		} catch (requestError) {
			alert(requestError.response?.data?.detail || 'Failed to add note');
		}
	}

	function openInterventionModal() {
		showInterventionModal = true;
		interventionType = 'note';
		interventionDescription = '';
		suggestedTasks = '';
	}

	function closeInterventionModal() {
		showInterventionModal = false;
	}

	function openFocusAreasModal() {
		showFocusAreasModal = true;
		if (patientData?.focus_areas) {
			primaryFocusAreas = [...(patientData.focus_areas.primary || [])];
			secondaryFocusAreas = [...(patientData.focus_areas.secondary || [])];
			maintenanceAreas = [...(patientData.focus_areas.maintenance || [])];
		}

		difficultyAdjustments = {};
		allDomains.forEach((domain) => {
			difficultyAdjustments[domain.id] = 5;
		});
		focusAreasNotes = '';
	}

	function closeFocusAreasModal() {
		showFocusAreasModal = false;
	}

	function toggleDomain(domain, category) {
		const lists = {
			primary: primaryFocusAreas,
			secondary: secondaryFocusAreas,
			maintenance: maintenanceAreas
		};

		primaryFocusAreas = primaryFocusAreas.filter((value) => value !== domain);
		secondaryFocusAreas = secondaryFocusAreas.filter((value) => value !== domain);
		maintenanceAreas = maintenanceAreas.filter((value) => value !== domain);

		const list = lists[category];
		if (!list.includes(domain)) {
			lists[category].push(domain);
			primaryFocusAreas = [...primaryFocusAreas];
			secondaryFocusAreas = [...secondaryFocusAreas];
			maintenanceAreas = [...maintenanceAreas];
		}
	}

	async function submitFocusAreas() {
		try {
			await api.patch(`/api/doctor/${userData.id}/patient/${patientId}/focus-areas`, null, {
				params: {
					primary_focus: JSON.stringify(primaryFocusAreas),
					secondary_focus: JSON.stringify(secondaryFocusAreas),
					maintenance: JSON.stringify(maintenanceAreas),
					notes: focusAreasNotes || 'Training plan adjusted by doctor'
				}
			});

			if (Object.keys(difficultyAdjustments).length > 0) {
				await api.patch(`/api/doctor/${userData.id}/patient/${patientId}/training-plan`, null, {
					params: {
						difficulty_adjustments: JSON.stringify(difficultyAdjustments),
						notes: focusAreasNotes || 'Difficulty levels adjusted by doctor'
					}
				});
			}

			closeFocusAreasModal();
			await loadPatientData();
		} catch (requestError) {
			alert(requestError.response?.data?.detail || 'Failed to update training plan');
		}
	}

	function adjustDifficulty(domain, change) {
		if (!difficultyAdjustments[domain]) {
			difficultyAdjustments[domain] = 1;
		}

		difficultyAdjustments[domain] = Math.max(1, Math.min(10, difficultyAdjustments[domain] + change));
		difficultyAdjustments = { ...difficultyAdjustments };
	}

	function getDomainColor(domain) {
		const colors = {
			working_memory: '#4f46e5',
			attention: '#0f766e',
			flexibility: '#0ea5e9',
			planning: '#15803d',
			processing_speed: '#db2777',
			visual_scanning: '#d97706'
		};
		return colors[domain] || '#6b7280';
	}

	function formatDate(dateStr) {
		if (!dateStr) return 'Not available';
		return new Date(dateStr).toLocaleString('en-GB', {
			day: '2-digit',
			month: 'short',
			year: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function formatShortDate(dateStr) {
		if (!dateStr) return 'No recent session';
		return new Date(dateStr).toLocaleDateString('en-GB', {
			day: '2-digit',
			month: 'short',
			year: 'numeric'
		});
	}

	function formatDomainLabel(value) {
		return value.replaceAll('_', ' ');
	}

	function handleModalOverlayKeydown(event, closeModal) {
		if (event.key === 'Enter' || event.key === ' ' || event.key === 'Escape') {
			event.preventDefault();
			closeModal();
		}
	}

	function stopModalPropagation(event) {
		if (event.key === 'Escape') {
			event.stopPropagation();
		}
	}

	$: patientName = patientData?.patient_info?.full_name || patientData?.patient_info?.email || 'Patient';
	$: focusAreas = patientData?.focus_areas || { primary: [], secondary: [], maintenance: [] };
	$: summaryCards = patientData
		? [
				{ label: 'Total Sessions', value: patientData.training_summary.total_sessions },
				{ label: 'Current Streak', value: `${patientData.training_summary.current_streak} days` },
				{ label: 'Average Score', value: `${patientData.recent_performance.avg_score}/100` },
				{ label: 'Average Accuracy', value: `${patientData.recent_performance.avg_accuracy}%` }
			]
		: [];
</script>

<DoctorWorkspaceShell
	title={patientName}
	subtitle="Patient-specific clinical overview with adherence, focus areas, biomarker access, progress monitoring, and recent activity in one calmer workspace."
	eyebrow="Doctor Patient Workspace"
	maxWidth="1360px"
>
	<svelte:fragment slot="actions">
		<button class="outline-btn" on:click={() => goto('/doctor/patients')}>All Patients</button>
		<button class="outline-btn" on:click={() => goto(`/doctor/patient/${patientId}/reports`)}>Progress Reports</button>
		<button class="outline-btn" on:click={() => goto(`/doctor/patient/${patientId}/prescriptions`)}>Prescriptions</button>
		<button class="primary-btn" on:click={openInterventionModal}>Add Clinical Note</button>
		<button class="accent-btn" on:click={openFocusAreasModal}>Adjust Training Plan</button>
	</svelte:fragment>

	{#if loading}
		<section class="state-card">
			<p>Loading patient workspace...</p>
		</section>
	{:else if error}
		<section class="state-card error-state">
			<p>{error}</p>
		</section>
	{:else if patientData}
		<section class="hero-card">
			<div>
				<p class="eyebrow">Clinical Summary</p>
				<h2>{patientData.patient_info.diagnosis || 'Diagnosis not recorded'}</h2>
				<p class="hero-copy">
					{#if patientData.patient_info.treatment_goal}
						Treatment goal: {patientData.patient_info.treatment_goal}
					{:else}
						No explicit treatment goal has been recorded yet.
					{/if}
				</p>
			</div>
			<div class="hero-meta">
				<div>
					<span>Last Session</span>
					<strong>{formatShortDate(patientData.training_summary.last_session)}</strong>
				</div>
				<div>
					<span>Longest Streak</span>
					<strong>{patientData.training_summary.longest_streak} days</strong>
				</div>
			</div>
		</section>

		<section class="summary-grid">
			{#each summaryCards as card}
				<article class="summary-card">
					<p>{card.label}</p>
					<strong>{card.value}</strong>
				</article>
			{/each}
		</section>

		<section class="panel-grid top-grid">
			<article class="panel-card">
				<div class="panel-heading">
					<div>
						<p class="panel-kicker">Focus</p>
						<h3>Training Priorities</h3>
					</div>
					<button class="outline-btn small" on:click={openFocusAreasModal}>Customize</button>
				</div>

				<div class="focus-groups">
					<div>
						<span class="focus-label">Primary</span>
						<div class="focus-tags">
							{#if focusAreas.primary?.length}
								{#each focusAreas.primary as area}
									<span class="focus-tag primary">{formatDomainLabel(area)}</span>
								{/each}
							{:else}
								<span class="empty-inline">No primary focus set</span>
							{/if}
						</div>
					</div>

					<div>
						<span class="focus-label">Secondary</span>
						<div class="focus-tags">
							{#if focusAreas.secondary?.length}
								{#each focusAreas.secondary as area}
									<span class="focus-tag secondary">{formatDomainLabel(area)}</span>
								{/each}
							{:else}
								<span class="empty-inline">No secondary focus set</span>
							{/if}
						</div>
					</div>

					<div>
						<span class="focus-label">Maintenance</span>
						<div class="focus-tags">
							{#if focusAreas.maintenance?.length}
								{#each focusAreas.maintenance as area}
									<span class="focus-tag maintenance">{formatDomainLabel(area)}</span>
								{/each}
							{:else}
								<span class="empty-inline">No maintenance areas set</span>
							{/if}
						</div>
					</div>
				</div>
			</article>

			<article class="panel-card">
				<div class="panel-heading">
					<div>
						<p class="panel-kicker">Recent Performance</p>
						<h3>Last 7 Days</h3>
					</div>
				</div>

				<div class="metric-list">
					<div><span>Sessions</span><strong>{patientData.recent_performance.sessions_last_7_days}</strong></div>
					<div><span>Average Score</span><strong>{patientData.recent_performance.avg_score}</strong></div>
					<div><span>Average Accuracy</span><strong>{patientData.recent_performance.avg_accuracy}%</strong></div>
					<div><span>Total Sessions Overall</span><strong>{patientData.training_summary.total_sessions}</strong></div>
				</div>
			</article>
		</section>

		{#if interventions.length > 0}
			<section class="panel-card">
				<div class="panel-heading">
					<div>
						<p class="panel-kicker">Clinical Notes</p>
						<h3>Recent Interventions</h3>
					</div>
				</div>

				<div class="interventions-list">
					{#each interventions as intervention}
						<article class="intervention-card">
							<div class="intervention-head">
								<span class="type-pill">{formatDomainLabel(intervention.type)}</span>
								<span class="date-copy">{formatDate(intervention.created_at)}</span>
							</div>
							<p class="intervention-copy">{intervention.description}</p>
							{#if intervention.data}
								<div class="intervention-meta">
									{#if intervention.data.suggested_tasks}
										<div><span>Suggested Tasks</span><strong>{intervention.data.suggested_tasks.join(', ')}</strong></div>
									{/if}
									{#if intervention.data.performance_goals}
										<div><span>Goals</span><strong>{intervention.data.performance_goals}</strong></div>
									{/if}
								</div>
							{/if}
						</article>
					{/each}
				</div>
			</section>
		{/if}

		<section class="panel-card">
			<BiomarkersPanel {biomarkerData} doctorView={true} days={30} />
		</section>

		{#if progressData}
			<section class="panel-grid">
				<article class="panel-card">
					<div class="panel-heading">
						<div>
							<p class="panel-kicker">Adherence</p>
							<h3>Training Adherence</h3>
						</div>
						<span class="status-pill status-{progressData.adherence.status}">{progressData.adherence.status.replaceAll('_', ' ')}</span>
					</div>

					<div class="adherence-layout">
						<div class="adherence-score">
							<strong>{progressData.adherence.adherence_rate}%</strong>
							<span>adherence</span>
						</div>
						<div class="metric-list compact">
							<div><span>Total Sessions</span><strong>{progressData.adherence.total_sessions}</strong></div>
							<div><span>Expected</span><strong>{progressData.adherence.expected_sessions}</strong></div>
							<div><span>Last 7 Days</span><strong>{progressData.adherence.sessions_last_7_days}</strong></div>
							<div><span>Last 30 Days</span><strong>{progressData.adherence.sessions_last_30_days}</strong></div>
							<div><span>Avg Days Between</span><strong>{progressData.adherence.avg_days_between_sessions} days</strong></div>
						</div>
					</div>
				</article>

				<article class="panel-card">
					<div class="panel-heading">
						<div>
							<p class="panel-kicker">Alerts</p>
							<h3>Areas Requiring Attention</h3>
						</div>
					</div>

					{#if progressData.concerning_areas?.length}
						<div class="concern-list">
							{#each progressData.concerning_areas as concern}
								<div class="concern-card severity-{concern.severity}">
									<div class="concern-head">
										<strong>{formatDomainLabel(concern.domain)}</strong>
										<span>{concern.severity}</span>
									</div>
									<p>{formatDomainLabel(concern.issue)}</p>
									<small>{concern.details}</small>
								</div>
							{/each}
						</div>
					{:else}
						<p class="empty-copy">No concerning areas are currently flagged.</p>
					{/if}
				</article>
			</section>

			{#if Object.keys(progressData.trends || {}).length > 0}
				<section class="panel-card">
					<div class="panel-heading">
						<div>
							<p class="panel-kicker">Trend Analysis</p>
							<h3>Recent Changes</h3>
						</div>
					</div>

					<div class="trend-grid">
						{#each Object.entries(progressData.trends) as [domain, trend]}
							<article class="trend-card direction-{trend.direction}">
								<h4>{formatDomainLabel(domain)}</h4>
								<div class="trend-comparison">
									<div><span>Previous</span><strong>{trend.previous_avg}</strong></div>
									<div><span>Recent</span><strong>{trend.recent_avg}</strong></div>
								</div>
								<p class:positive={trend.change >= 0} class:negative={trend.change < 0} class="trend-change">
									{trend.change >= 0 ? '+' : ''}{trend.change} points
								</p>
								{#if trend.is_concerning}
									<p class="warning-note">Concerning decline</p>
								{/if}
							</article>
						{/each}
					</div>
				</section>
			{/if}

			{#if Object.keys(progressData.domain_improvements || {}).length > 0}
				<section class="panel-card">
					<div class="panel-heading">
						<div>
							<p class="panel-kicker">Improvement</p>
							<h3>Domain Improvement Snapshot</h3>
						</div>
					</div>

					<div class="improvement-grid">
						{#each Object.entries(progressData.domain_improvements) as [domain, improvement]}
							<article class="improvement-card trending-{improvement.trending}">
								<h4>{formatDomainLabel(domain)}</h4>
								<div class="metric-list compact">
									<div><span>Early Average</span><strong>{improvement.early_avg}</strong></div>
									<div><span>Recent Average</span><strong>{improvement.recent_avg}</strong></div>
									<div><span>Overall Change</span><strong>{improvement.overall_improvement >= 0 ? '+' : ''}{improvement.overall_improvement}</strong></div>
									<div><span>Total Sessions</span><strong>{improvement.total_sessions}</strong></div>
								</div>
								<div class="score-row">
									{#each improvement.recent_scores as score}
										<span class="score-chip">{score}</span>
									{/each}
								</div>
							</article>
						{/each}
					</div>
				</section>
			{/if}
		{/if}

		<section class="panel-card">
			<div class="panel-heading">
				<div>
					<p class="panel-kicker">Activity</p>
					<h3>Recent Training Sessions</h3>
				</div>
			</div>

			{#if sessions.length === 0}
				<p class="empty-copy">No training sessions have been recorded yet.</p>
			{:else}
				<div class="table-wrap">
					<table>
						<thead>
							<tr>
								<th>Date</th>
								<th>Domain</th>
								<th>Task</th>
								<th>Difficulty</th>
								<th>Score</th>
								<th>Accuracy</th>
								<th>RT</th>
							</tr>
						</thead>
						<tbody>
							{#each sessions as session}
								<tr>
									<td>{formatDate(session.completed_at)}</td>
									<td><span class="domain-pill" style={`background:${getDomainColor(session.domain)};`}>{formatDomainLabel(session.domain)}</span></td>
									<td>{session.task_code || session.task_type}</td>
									<td>Level {session.difficulty}</td>
									<td>{session.score}</td>
									<td>{session.accuracy}%</td>
									<td>{session.reaction_time || 'N/A'} ms</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</section>
	{/if}
</DoctorWorkspaceShell>

{#if showInterventionModal}
	<div
		class="modal-overlay"
		role="button"
		tabindex="0"
		aria-label="Close clinical note dialog"
		on:click={closeInterventionModal}
		on:keydown={(event) => handleModalOverlayKeydown(event, closeInterventionModal)}
	>
		<div
			class="modal-content"
			role="dialog"
			aria-modal="true"
			aria-label="Add clinical note"
			tabindex="-1"
			on:click|stopPropagation
			on:keydown|stopPropagation={stopModalPropagation}
		>
			<div class="modal-header">
				<h2>Add Clinical Note</h2>
				<button class="close-btn" on:click={closeInterventionModal}>x</button>
			</div>

			<div class="modal-body">
				<div class="form-group">
					<label for="interventionType">Note Type</label>
					<select id="interventionType" bind:value={interventionType}>
						<option value="note">General Observation</option>
						<option value="task_recommendation">Task Recommendation</option>
						<option value="goal_setting">Performance Goal</option>
						<option value="check_in">Follow-up Scheduled</option>
					</select>
				</div>

				<div class="form-group">
					<label for="interventionDescription">Clinical Notes</label>
					<textarea id="interventionDescription" bind:value={interventionDescription} rows="6" placeholder="Record observations, recommendations, or concerns."></textarea>
				</div>

				{#if interventionType === 'task_recommendation'}
					<div class="form-group">
						<label for="suggestedTasks">Suggested Tasks</label>
						<input id="suggestedTasks" type="text" bind:value={suggestedTasks} placeholder="digit_span, trail_making, stroop" />
					</div>
				{/if}
			</div>

			<div class="modal-footer">
				<button class="outline-btn" on:click={closeInterventionModal}>Cancel</button>
				<button class="primary-btn" disabled={!interventionDescription.trim()} on:click={submitIntervention}>Save Note</button>
			</div>
		</div>
	</div>
{/if}

{#if showFocusAreasModal}
	<div
		class="modal-overlay"
		role="button"
		tabindex="0"
		aria-label="Close training plan dialog"
		on:click={closeFocusAreasModal}
		on:keydown={(event) => handleModalOverlayKeydown(event, closeFocusAreasModal)}
	>
		<div
			class="modal-content large-modal"
			role="dialog"
			aria-modal="true"
			aria-label="Adjust training plan"
			tabindex="-1"
			on:click|stopPropagation
			on:keydown|stopPropagation={stopModalPropagation}
		>
			<div class="modal-header">
				<h2>Adjust Training Plan</h2>
				<button class="close-btn" on:click={closeFocusAreasModal}>x</button>
			</div>

			<div class="modal-body">
				<div class="focus-customization">
					<div class="focus-category">
						<h3 class="category-title">Primary Focus</h3>
						<div class="domain-selection">
							{#each allDomains as domain}
								<button class:selected={primaryFocusAreas.includes(domain.id)} class="domain-btn primary" on:click={() => toggleDomain(domain.id, 'primary')}>{domain.label}</button>
							{/each}
						</div>
					</div>

					<div class="focus-category">
						<h3 class="category-title">Secondary Focus</h3>
						<div class="domain-selection">
							{#each allDomains as domain}
								<button class:selected={secondaryFocusAreas.includes(domain.id)} class="domain-btn secondary" on:click={() => toggleDomain(domain.id, 'secondary')}>{domain.label}</button>
							{/each}
						</div>
					</div>

					<div class="focus-category">
						<h3 class="category-title">Maintenance</h3>
						<div class="domain-selection">
							{#each allDomains as domain}
								<button class:selected={maintenanceAreas.includes(domain.id)} class="domain-btn maintenance" on:click={() => toggleDomain(domain.id, 'maintenance')}>{domain.label}</button>
							{/each}
						</div>
					</div>
				</div>

				<div class="difficulty-grid">
					{#each allDomains as domain}
						<div class="difficulty-card">
							<p>{domain.label}</p>
							<div class="difficulty-controls">
								<button class="step-btn" on:click={() => adjustDifficulty(domain.id, -1)}>-</button>
								<strong>{difficultyAdjustments[domain.id] || 5}</strong>
								<button class="step-btn" on:click={() => adjustDifficulty(domain.id, 1)}>+</button>
							</div>
						</div>
					{/each}
				</div>

				<div class="form-group">
					<label for="focusAreasNotes">Clinical Reasoning</label>
					<textarea id="focusAreasNotes" bind:value={focusAreasNotes} rows="4" placeholder="Explain why these adjustments are being made."></textarea>
				</div>
			</div>

			<div class="modal-footer">
				<button class="outline-btn" on:click={closeFocusAreasModal}>Cancel</button>
				<button class="primary-btn" on:click={submitFocusAreas}>Update Training Plan</button>
			</div>
		</div>
	</div>
{/if}

<style>
	.primary-btn,
	.outline-btn,
	.accent-btn {
		border-radius: 999px;
		padding: 0.78rem 1rem;
		font-weight: 700;
		cursor: pointer;
		transition: 180ms ease;
	}

	.primary-btn {
		border: 1px solid #4f46e5;
		background: #4f46e5;
		color: #ffffff;
	}

	.outline-btn {
		border: 1px solid #d1d5db;
		background: #ffffff;
		color: #111827;
	}

	.accent-btn {
		border: 1px solid #f59e0b;
		background: #f59e0b;
		color: #ffffff;
	}

	.outline-btn.small {
		padding: 0.6rem 0.9rem;
	}

	.hero-card,
	.summary-card,
	.panel-card,
	.state-card,
	.intervention-card,
	.concern-card,
	.trend-card,
	.improvement-card,
	.modal-content,
	.difficulty-card,
	.focus-category {
		background: #ffffff;
		border: 1px solid #e5e7eb;
		box-shadow: 0 16px 30px rgba(15, 23, 42, 0.05);
	}

	.hero-card,
	.panel-card,
	.state-card,
	.modal-content {
		border-radius: 26px;
		padding: 1.25rem;
	}

	.error-state {
		border-color: rgba(239, 68, 68, 0.25);
		color: #b91c1c;
	}

	.hero-card {
		display: grid;
		grid-template-columns: 1.2fr 0.8fr;
		gap: 1rem;
	}

	.eyebrow,
	.panel-kicker,
	.summary-card p,
	.focus-label,
	.metric-list span,
	.hero-meta span,
	.intervention-meta span,
	.trend-comparison span,
	.difficulty-card p,
	.form-group label {
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
	.intervention-copy,
	.concern-card p,
	.concern-card small {
		color: #6b7280;
		line-height: 1.6;
	}

	.hero-meta,
	.summary-grid,
	.panel-grid,
	.focus-groups,
	.interventions-list,
	.concern-list,
	.trend-grid,
	.improvement-grid,
	.difficulty-grid {
		display: grid;
		gap: 1rem;
	}

	.hero-meta {
		align-content: start;
		grid-template-columns: repeat(2, minmax(0, 1fr));
	}

	.hero-meta div,
	.summary-card,
	.difficulty-card {
		border-radius: 20px;
		padding: 1rem;
		background: #f9fafb;
	}

	.hero-meta strong,
	.summary-card strong {
		display: block;
		margin-top: 0.35rem;
		font-size: 1.4rem;
		color: #111827;
	}

	.summary-grid {
		grid-template-columns: repeat(4, minmax(0, 1fr));
	}

	.panel-grid {
		grid-template-columns: repeat(2, minmax(0, 1fr));
	}

	.top-grid {
		align-items: start;
	}

	.panel-heading,
	.intervention-head,
	.concern-head,
	.modal-header,
	.modal-footer,
	.difficulty-controls {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: center;
	}

	.focus-groups,
	.intervention-meta,
	.metric-list,
	.score-row,
	.domain-selection {
		display: flex;
		flex-wrap: wrap;
		gap: 0.6rem;
	}

	.metric-list,
	.intervention-meta {
		flex-direction: column;
	}

	.metric-list div,
	.intervention-meta div,
	.trend-comparison,
	.adherence-layout {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 0.8rem;
	}

	.metric-list.compact div {
		grid-template-columns: 1fr auto;
	}

	.metric-list strong,
	.intervention-meta strong,
	.concern-head strong,
	.trend-comparison strong,
	.improvement-card strong,
	.difficulty-card strong {
		color: #111827;
	}

	.focus-tag,
	.type-pill,
	.status-pill,
	.domain-pill,
	.score-chip {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		border-radius: 999px;
		padding: 0.32rem 0.75rem;
		font-size: 0.8rem;
		font-weight: 800;
		text-transform: capitalize;
	}

	.focus-tag.primary {
		background: #fee2e2;
		color: #b91c1c;
	}

	.focus-tag.secondary {
		background: #fef3c7;
		color: #b45309;
	}

	.focus-tag.maintenance {
		background: #dcfce7;
		color: #15803d;
	}

	.type-pill,
	.domain-pill,
	.score-chip {
		background: #eef2ff;
		color: #4f46e5;
	}

	.status-pill {
		background: #eef2ff;
		color: #4f46e5;
	}

	.status-pill.status-concerning {
		background: #fee2e2;
		color: #b91c1c;
	}

	.status-pill.status-needs_improvement {
		background: #fef3c7;
		color: #b45309;
	}

	.status-pill.status-good,
	.status-pill.status-excellent {
		background: #dcfce7;
		color: #15803d;
	}

	.adherence-layout {
		grid-template-columns: 220px 1fr;
		align-items: center;
	}

	.adherence-score {
		padding: 1rem;
		border-radius: 24px;
		background: linear-gradient(180deg, #eef2ff 0%, #ffffff 100%);
		text-align: center;
	}

	.adherence-score strong {
		display: block;
		font-size: 2.4rem;
		color: #111827;
	}

	.concern-card,
	.trend-card,
	.improvement-card {
		border-radius: 20px;
		padding: 1rem;
	}

	.concern-card.severity-high {
		border-left: 4px solid #ef4444;
	}

	.concern-card.severity-medium {
		border-left: 4px solid #f59e0b;
	}

	.concern-card.severity-low {
		border-left: 4px solid #0ea5e9;
	}

	.trend-card.direction-upward,
	.improvement-card.trending-up {
		background: linear-gradient(180deg, #ecfdf5 0%, #ffffff 100%);
	}

	.trend-card.direction-downward,
	.improvement-card.trending-down {
		background: linear-gradient(180deg, #fef2f2 0%, #ffffff 100%);
	}

	.trend-change {
		margin: 0.8rem 0 0;
		font-weight: 700;
	}

	.trend-change.positive {
		color: #15803d;
	}

	.trend-change.negative {
		color: #b91c1c;
	}

	.warning-note {
		margin: 0.55rem 0 0;
		color: #b45309;
		font-weight: 700;
	}

	.table-wrap {
		overflow-x: auto;
	}

	table {
		width: 100%;
		border-collapse: collapse;
	}

	th,
	td {
		padding: 0.85rem 0.75rem;
		border-top: 1px solid #eef2f7;
		text-align: left;
		color: #374151;
	}

	th {
		font-size: 0.78rem;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: #6b7280;
	}

	.modal-overlay {
		position: fixed;
		inset: 0;
		background: rgba(15, 23, 42, 0.45);
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 1rem;
		z-index: 1000;
	}

	.modal-content {
		width: min(760px, 100%);
		max-height: 90vh;
		overflow: auto;
	}

	.large-modal {
		width: min(980px, 100%);
	}

	.close-btn,
	.step-btn {
		border: 1px solid #d1d5db;
		background: #ffffff;
		color: #111827;
		cursor: pointer;
	}

	.close-btn {
		width: 2rem;
		height: 2rem;
		border-radius: 999px;
	}

	.form-group {
		display: grid;
		gap: 0.45rem;
		margin-bottom: 1rem;
	}

	.form-group input,
	.form-group select,
	.form-group textarea {
		width: 100%;
		border: 1px solid #d1d5db;
		border-radius: 18px;
		padding: 0.9rem 1rem;
		font: inherit;
		background: #f9fafb;
		color: #111827;
	}

	.focus-customization,
	.difficulty-grid {
		margin-bottom: 1rem;
	}

	.focus-category,
	.difficulty-card {
		padding: 1rem;
		border-radius: 20px;
	}

	.category-title {
		margin: 0 0 0.75rem;
	}

	.domain-btn {
		border: 1px solid #d1d5db;
		background: #f9fafb;
		color: #111827;
		border-radius: 999px;
		padding: 0.65rem 0.95rem;
		cursor: pointer;
		font-weight: 700;
	}

	.domain-btn.selected.primary {
		background: #fee2e2;
		border-color: #ef4444;
		color: #b91c1c;
	}

	.domain-btn.selected.secondary {
		background: #fef3c7;
		border-color: #f59e0b;
		color: #b45309;
	}

	.domain-btn.selected.maintenance {
		background: #dcfce7;
		border-color: #22c55e;
		color: #15803d;
	}

	.difficulty-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
	}

	.step-btn {
		width: 2.1rem;
		height: 2.1rem;
		border-radius: 999px;
		font-size: 1.1rem;
		font-weight: 800;
	}

	.empty-inline {
		color: #9ca3af;
		font-size: 0.92rem;
	}

	@media (max-width: 1100px) {
		.hero-card,
		.summary-grid,
		.panel-grid,
		.adherence-layout {
			grid-template-columns: 1fr;
		}

		.summary-grid {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}

	@media (max-width: 760px) {
		.summary-grid,
		.panel-grid,
		.hero-meta,
		.metric-list div,
		.intervention-meta div,
		.trend-comparison,
		.adherence-layout {
			grid-template-columns: 1fr;
		}

		.panel-heading,
		.modal-header,
		.modal-footer {
			flex-direction: column;
			align-items: stretch;
		}
	}
</style>
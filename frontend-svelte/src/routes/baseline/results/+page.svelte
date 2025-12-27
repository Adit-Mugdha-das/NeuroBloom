<script>
	import { goto } from '$app/navigation';
	import { baseline, tasks } from '$lib/api';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';
	
	let currentUser = null;
	let loading = true;
	let baselineData = null;
	let baselineStatus = null;
	let error = null;
	let calculating = false;
	
	user.subscribe(value => {
		currentUser = value;
	});
	
	onMount(async () => {
		if (!currentUser) {
			goto('/login');
			return;
		}
		
		await loadBaseline();
	});
	
	async function loadBaseline() {
		loading = true;
		error = null;
		
		try {
			// Check completion status
			baselineStatus = await tasks.getBaselineStatus(currentUser.id);
			
			// Try to get existing baseline
			try {
				baselineData = await baseline.get(currentUser.id);
			} catch (e) {
				// No baseline yet
				baselineData = null;
			}
		} catch (err) {
			console.error('Error loading baseline:', err);
			error = 'Failed to load baseline data';
		} finally {
			loading = false;
		}
	}
	
	async function calculateBaseline() {
		calculating = true;
		error = null;
		
		try {
			baselineData = await baseline.calculate(currentUser.id);
		} catch (err) {
			console.error('Error calculating baseline:', err);
			error = err.response?.data?.detail || 'Failed to calculate baseline. Make sure you completed all 6 tasks.';
		} finally {
			calculating = false;
		}
	}
	
	function getDomainIcon(domain) {
		// Icons removed for professional appearance
		return '';
	}
	
	function getDomainName(domain) {
		const names = {
			working_memory: 'Working Memory',
			attention: 'Attention',
			flexibility: 'Cognitive Flexibility',
			planning: 'Planning',
			processing_speed: 'Processing Speed',
			visual_scanning: 'Visual Scanning'
		};
		return names[domain] || domain;
	}
	
	function getScoreColor(score) {
		if (score >= 80) return '#4caf50'; // Green
		if (score >= 60) return '#ff9800'; // Orange
		return '#f44336'; // Red
	}
	
	function getScoreLabel(score) {
		if (score >= 80) return 'Excellent';
		if (score >= 70) return 'Good';
		if (score >= 60) return 'Average';
		if (score >= 50) return 'Below Average';
		return 'Needs Improvement';
	}
	
	// Radar chart calculations
	$: radarPoints = baselineData ? calculateRadarPoints() : '';
	
	function calculateRadarPoints() {
		const domains = [
			'working_memory',
			'attention',
			'flexibility',
			'planning',
			'processing_speed',
			'visual_scanning'
		];
		
		const centerX = 250;
		const centerY = 200;
		const maxRadius = 120;
		const angleStep = (2 * Math.PI) / 6;
		
		const points = domains.map((domain, i) => {
			const score = baselineData[`${domain}_score`] || 0;
			const radius = (score / 100) * maxRadius;
			const angle = i * angleStep - Math.PI / 2; // Start from top
			
			const x = centerX + radius * Math.cos(angle);
			const y = centerY + radius * Math.sin(angle);
			
			return `${x},${y}`;
		});
		
		return points.join(' ');
	}
	
	function backToDashboard() {
		goto('/dashboard');
	}
</script>

<div class="container">
	{#if loading}
		<div class="loading-card">
			<p>Loading baseline data...</p>
		</div>
	{:else if error}
		<div class="error-card">
			<h3>Error</h3>
			<p>{error}</p>
			<button class="btn-primary" on:click={loadBaseline}>Retry</button>
		</div>
	{:else if !baselineStatus?.all_completed}
		<div class="incomplete-card">
			<h2>Complete All Tasks First</h2>
			<p>You've completed {baselineStatus?.completed_count || 0} out of 6 baseline tasks.</p>
			
			<div class="task-checklist">
				{#each Object.entries(baselineStatus?.tasks || {}) as [task, completed]}
					<div class="checklist-item {completed ? 'completed' : ''}">
						<span class="check">{completed ? '✓' : '○'}</span>
						<span class="name">{getDomainName(task)}</span>
					</div>
				{/each}
			</div>
			
			<button class="btn-primary" on:click={backToDashboard} style="margin-top: 2rem;">
				Go to Dashboard
			</button>
		</div>
	{:else if !baselineData}
		<div class="ready-card">
			<h2>All Tasks Complete!</h2>
			<p>You've completed all 6 cognitive assessment tasks.</p>
			<p style="color: #666; margin-top: 1rem;">Click below to calculate your baseline cognitive profile.</p>
			
			<button 
				class="btn-calculate" 
				on:click={calculateBaseline}
				disabled={calculating}
			>
				{calculating ? 'Calculating...' : 'Calculate My Baseline'}
			</button>
		</div>
	{:else}
		<!-- Baseline Results -->
		<div class="results-container">
			<!-- Header Section -->
			<div class="results-header">
				<div class="header-content">
					<div class="header-text">
						<h1>Cognitive Baseline Assessment</h1>
						<p class="subtitle">Comprehensive evaluation of cognitive performance across 6 key domains</p>
					</div>
					<button class="btn-back" on:click={backToDashboard}>← Back to Dashboard</button>
				</div>
			</div>
			
			<!-- Overall Score Card -->
			<div class="score-card overall">
				<h2>Overall Cognitive Score</h2>
				<div class="big-score" style="color: {getScoreColor(baselineData.overall_score)}">
					{baselineData.overall_score.toFixed(1)}
				</div>
				<div class="score-label">{getScoreLabel(baselineData.overall_score)}</div>
				<p class="date">Assessed on {new Date(baselineData.assessment_date).toLocaleDateString()}</p>
			</div>
			
			<!-- Radar Chart -->
			<div class="chart-card">
				<h3>Cognitive Profile</h3>
				<svg viewBox="0 0 500 400" class="radar-chart">
					<!-- Background circles -->
					<circle cx="250" cy="200" r="120" fill="none" stroke="#e0e0e0" stroke-width="1"/>
					<circle cx="250" cy="200" r="90" fill="none" stroke="#e0e0e0" stroke-width="1"/>
					<circle cx="250" cy="200" r="60" fill="none" stroke="#e0e0e0" stroke-width="1"/>
					<circle cx="250" cy="200" r="30" fill="none" stroke="#e0e0e0" stroke-width="1"/>
					
					<!-- Axes -->
					<line x1="250" y1="200" x2="250" y2="80" stroke="#ccc" stroke-width="1"/>
					<line x1="250" y1="200" x2="354" y2="140" stroke="#ccc" stroke-width="1"/>
					<line x1="250" y1="200" x2="354" y2="260" stroke="#ccc" stroke-width="1"/>
					<line x1="250" y1="200" x2="250" y2="320" stroke="#ccc" stroke-width="1"/>
					<line x1="250" y1="200" x2="146" y2="260" stroke="#ccc" stroke-width="1"/>
					<line x1="250" y1="200" x2="146" y2="140" stroke="#ccc" stroke-width="1"/>
					
					<!-- Data polygon -->
					<polygon 
						points={radarPoints} 
						fill="rgba(102, 126, 234, 0.3)" 
						stroke="#667eea" 
						stroke-width="2"
					/>
					
					<!-- Labels -->
					<text x="250" y="60" text-anchor="middle" class="chart-label">Working Memory</text>
					<text x="385" y="145" text-anchor="start" class="chart-label">Attention</text>
					<text x="385" y="265" text-anchor="start" class="chart-label">Cognitive Flexibility</text>
					<text x="250" y="350" text-anchor="middle" class="chart-label">Planning</text>
					<text x="115" y="265" text-anchor="end" class="chart-label">Processing Speed</text>
					<text x="115" y="145" text-anchor="end" class="chart-label">Visual Scanning</text>
				</svg>
			</div>
			
			<!-- Domain Scores -->
			<div class="domains-grid">
				<div class="domain-card">
					<div class="domain-header">
						<h4>Working Memory</h4>
					</div>
					<div class="domain-score" style="color: {getScoreColor(baselineData.working_memory_score)}">
						{baselineData.working_memory_score.toFixed(1)}
					</div>
					<div class="progress-bar">
						<div class="progress-fill" style="width: {baselineData.working_memory_score}%; background: {getScoreColor(baselineData.working_memory_score)}"></div>
					</div>
				</div>
				
				<div class="domain-card">
					<div class="domain-header">
						<h4>Attention</h4>
					</div>
					<div class="domain-score" style="color: {getScoreColor(baselineData.attention_score)}">
						{baselineData.attention_score.toFixed(1)}
					</div>
					<div class="progress-bar">
						<div class="progress-fill" style="width: {baselineData.attention_score}%; background: {getScoreColor(baselineData.attention_score)}"></div>
					</div>
				</div>
				
				<div class="domain-card">
					<div class="domain-header">
						<h4>Cognitive Flexibility</h4>
					</div>
					<div class="domain-score" style="color: {getScoreColor(baselineData.flexibility_score)}">
						{baselineData.flexibility_score.toFixed(1)}
					</div>
					<div class="progress-bar">
						<div class="progress-fill" style="width: {baselineData.flexibility_score}%; background: {getScoreColor(baselineData.flexibility_score)}"></div>
					</div>
				</div>
				
				<div class="domain-card">
					<div class="domain-header">
						<h4>Planning</h4>
					</div>
					<div class="domain-score" style="color: {getScoreColor(baselineData.planning_score)}">
						{baselineData.planning_score.toFixed(1)}
					</div>
					<div class="progress-bar">
						<div class="progress-fill" style="width: {baselineData.planning_score}%; background: {getScoreColor(baselineData.planning_score)}"></div>
					</div>
				</div>
				
				<div class="domain-card">
					<div class="domain-header">
						<h4>Processing Speed</h4>
					</div>
					<div class="domain-score" style="color: {getScoreColor(baselineData.processing_speed_score)}">
						{baselineData.processing_speed_score.toFixed(1)}
					</div>
					<div class="progress-bar">
						<div class="progress-fill" style="width: {baselineData.processing_speed_score}%; background: {getScoreColor(baselineData.processing_speed_score)}"></div>
					</div>
				</div>
				
				<div class="domain-card">
					<div class="domain-header">
						<h4>Visual Scanning</h4>
					</div>
					<div class="domain-score" style="color: {getScoreColor(baselineData.visual_scanning_score)}">
						{baselineData.visual_scanning_score.toFixed(1)}
					</div>
					<div class="progress-bar">
						<div class="progress-fill" style="width: {baselineData.visual_scanning_score}%; background: {getScoreColor(baselineData.visual_scanning_score)}"></div>
					</div>
				</div>
			</div>
			
			<!-- Insights -->
			<div class="insights-card">
				<h3>Insights & Recommendations</h3>
				<div class="insights-content">
					{#if baselineData.overall_score >= 80}
						<p><strong>Excellent cognitive performance!</strong> Your scores are above average across all domains.</p>
					{:else if baselineData.overall_score >= 60}
						<p><strong>Good cognitive performance.</strong> You have a solid foundation with room for targeted improvement.</p>
					{:else}
						<p><strong>Baseline established.</strong> Regular training will help improve your cognitive performance.</p>
					{/if}
					
					<div class="recommendation">
						<h4>Focus Areas:</h4>
						<ul>
							{#each Object.entries({
								working_memory: baselineData.working_memory_score,
								attention: baselineData.attention_score,
								flexibility: baselineData.flexibility_score,
								planning: baselineData.planning_score,
								processing_speed: baselineData.processing_speed_score,
								visual_scanning: baselineData.visual_scanning_score
							}).sort((a, b) => a[1] - b[1]).slice(0, 3) as [domain, score]}
								{#if score < 70}
								<li><strong>{getDomainName(domain)}</strong> - Score: {score.toFixed(1)}</li>
								{/if}
							{/each}
						</ul>
					</div>
				</div>
			</div>
			
			<div style="text-align: center; margin-top: 2rem;">
				<button class="btn-primary" on:click={backToDashboard}>
					Continue to Dashboard
				</button>
				<button class="btn-secondary" on:click={calculateBaseline} style="margin-left: 1rem;">
					Recalculate Baseline
				</button>
			</div>
		</div>
	{/if}
</div>

<style>
	.container {
		min-height: 100vh;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		padding: 2rem;
	}
	
	.loading-card, .error-card, .incomplete-card, .ready-card {
		max-width: 600px;
		margin: 0 auto;
		background: white;
		border-radius: 20px;
		padding: 3rem;
		text-align: center;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
	}
	
	.error-card h3 {
		color: #f44336;
		margin-bottom: 1rem;
	}
	
	.task-checklist {
		margin: 2rem 0;
		text-align: left;
	}
	
	.checklist-item {
		display: flex;
		align-items: center;
		padding: 1rem;
		border-bottom: 1px solid #f0f0f0;
		gap: 1rem;
	}
	
	.checklist-item.completed {
		background: #f0f7ff;
	}
	
	.checklist-item .check {
		font-size: 1.5rem;
		color: #ccc;
	}
	
	.checklist-item.completed .check {
		color: #4caf50;
	}
	
	.checklist-item .name {
		font-weight: 600;
		color: #333;
	}
	
	.btn-calculate {
		background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
		color: white;
		border: none;
		padding: 1.5rem 3rem;
		border-radius: 12px;
		font-size: 1.2rem;
		font-weight: bold;
		cursor: pointer;
		transition: all 0.3s;
		margin-top: 2rem;
	}
	
	.btn-calculate:hover:not(:disabled) {
		transform: translateY(-2px);
		box-shadow: 0 8px 20px rgba(76, 175, 80, 0.4);
	}
	
	.btn-calculate:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	
	.results-container {
		max-width: 1200px;
		margin: 0 auto;
	}
	
	.results-header {
		background: white;
		border-radius: 20px;
		padding: 2rem;
		margin-bottom: 2rem;
		box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
	}
	
	.header-content {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 2rem;
	}
	
	.header-text h1 {
		margin: 0 0 0.5rem 0;
		color: #333;
		font-size: 2rem;
	}
	
	.header-text .subtitle {
		margin: 0;
		color: #666;
		font-size: 1rem;
	}
	
	.btn-back {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		padding: 0.75rem 1.5rem;
		border-radius: 8px;
		cursor: pointer;
		font-weight: 600;
		transition: all 0.3s;
		white-space: nowrap;
	}
	
	.btn-back:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
	}
	
	.score-card {
		background: white;
		border-radius: 20px;
		padding: 2rem;
		text-align: center;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
		margin-bottom: 2rem;
	}
	
	.score-card.overall {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
	}
	
	.big-score {
		font-size: 5rem;
		font-weight: bold;
		margin: 1rem 0;
	}
	
	.score-label {
		font-size: 1.5rem;
		opacity: 0.9;
	}
	
	.date {
		margin-top: 1rem;
		opacity: 0.8;
		font-size: 0.9rem;
	}
	
	.chart-card {
		background: white;
		border-radius: 20px;
		padding: 2rem;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
		margin-bottom: 2rem;
	}
	
	.chart-card h3 {
		text-align: center;
		margin-bottom: 2rem;
		color: #333;
	}
	
	.radar-chart {
		max-width: 500px;
		margin: 0 auto;
		display: block;
	}
	
	.chart-label {
		font-size: 12px;
		fill: #666;
		font-weight: 600;
	}
	
	.domains-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		gap: 1.5rem;
		margin-bottom: 2rem;
	}
	
	.domain-card {
		background: white;
		border-radius: 12px;
		padding: 1.5rem;
		box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
	}
	
	.domain-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 1rem;
	}
	
	.domain-header h4 {
		margin: 0;
		color: #333;
		font-size: 1.1rem;
	}
	
	.domain-score {
		font-size: 2.5rem;
		font-weight: bold;
		margin: 0.5rem 0;
	}
	
	.progress-bar {
		width: 100%;
		height: 8px;
		background: #e0e0e0;
		border-radius: 4px;
		overflow: hidden;
	}
	
	.progress-fill {
		height: 100%;
		transition: width 0.5s ease;
	}
	
	.insights-card {
		background: white;
		border-radius: 20px;
		padding: 2rem;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
	}
	
	.insights-card h3 {
		color: #333;
		margin-bottom: 1rem;
	}
	
	.insights-content {
		color: #666;
		line-height: 1.8;
	}
	
	.recommendation {
		margin-top: 1.5rem;
		padding: 1.5rem;
		background: #f8f9fa;
		border-radius: 12px;
	}
	
	.recommendation h4 {
		color: #667eea;
		margin-bottom: 1rem;
	}
	
	.recommendation ul {
		list-style: none;
		padding: 0;
	}
	
	.recommendation li {
		padding: 0.5rem 0;
		color: #666;
	}
	
	.btn-primary {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		padding: 1rem 2.5rem;
		border-radius: 12px;
		font-size: 1.1rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s;
	}
	
	.btn-primary:hover {
		transform: translateY(-2px);
		box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
	}
	
	.btn-secondary {
		background: white;
		color: #667eea;
		border: 2px solid #667eea;
		padding: 1rem 2.5rem;
		border-radius: 12px;
		font-size: 1.1rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s;
	}
	
	.btn-secondary:hover {
		background: #f0f7ff;
	}
</style>

<script>
	import { formatDate, formatNumber, locale as activeLocale, uiText } from '$lib/i18n';
	import { goto } from '$app/navigation';
	import { baseline, patientJourney, training } from '$lib/api';
	import { user } from '$lib/stores';
	import { downloadCSV, downloadSVGAsPNG } from '$lib/utils/chartDownload';
	import { onMount } from 'svelte';
	
	let currentUser = null;
	let loading = true;
	let baselineData = null;
	let baselineStatus = null;
	let trainingPlan = null;
	let comparisonData = null;
	let error = null;
	let calculating = false;
	let generatingPlan = false;
	
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
			const journey = await patientJourney.get(currentUser.id);
			baselineStatus = journey?.baseline || null;

			if (!journey?.baseline?.all_completed) {
				goto('/baseline');
				return;
			}
			
			// Try to get existing baseline
			try {
				const baselineResponse = await baseline.get(currentUser.id);
				baselineData = baselineResponse?.assessment || null;
				
				// Check if training plan exists
				try {
					trainingPlan = await training.getPlan(currentUser.id);
					if (trainingPlan && trainingPlan.has_plan === false) {
						trainingPlan = null;
					}
					
					// If training plan exists, get performance comparison
					try {
						comparisonData = await training.getPerformanceComparison(currentUser.id);
						if (comparisonData && comparisonData.has_data === false) {
							comparisonData = null;
						}
						console.log('Comparison data loaded:', comparisonData);
					} catch (e) {
						console.log('No comparison data yet:', e);
						comparisonData = null;
					}
				} catch (e) {
					trainingPlan = null;
					comparisonData = null;
				}
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
			console.log('Recalculating baseline for user:', currentUser.id);
			baselineData = await baseline.calculate(currentUser.id);
			console.log('Baseline recalculated successfully:', baselineData);
			
			// Reload baseline data to ensure we have the latest
			await loadBaseline();
			
			// Show success message
			alert('Baseline recalculated successfully!');
		} catch (err) {
			console.error('Error calculating baseline:', err);
			error = err.response?.data?.detail || 'Failed to calculate baseline. Make sure you completed all 6 tasks.';
			alert('Error: ' + error);
		} finally {
			calculating = false;
		}
	}
	
	async function generateTrainingPlan() {
		generatingPlan = true;
		error = null;
		
		try {
			trainingPlan = await training.generatePlan(currentUser.id);
			// Redirect to training page
			goto('/dashboard');
		} catch (err) {
			console.error('Error generating training plan:', err);
			error = err.response?.data?.detail || 'Failed to generate training plan.';
		} finally {
			generatingPlan = false;
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
		return uiText(names[domain] || domain, $activeLocale);
	}

	function n(value, options = {}) {
		return formatNumber(value, $activeLocale, options);
	}

	function scoreNumber(value) {
		return n(value, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
	}

	function displayDate(value) {
		return formatDate(value, $activeLocale);
	}
	
	function getScoreColor(score) {
		if (score >= 80) return '#4caf50'; // Green
		if (score >= 60) return '#ff9800'; // Orange
		return '#f44336'; // Red
	}
	
	function getScoreLabel(score) {
		if (score >= 80) return uiText('Excellent', $activeLocale);
		if (score >= 70) return uiText('Good', $activeLocale);
		if (score >= 60) return uiText('Average', $activeLocale);
		if (score >= 50) return uiText('Below Average', $activeLocale);
		return uiText('Needs Improvement', $activeLocale);
	}
	
	function getBaselineScores() {
		if (!baselineData) return null;
		return {
			working_memory: baselineData.working_memory_score || 0,
			attention: baselineData.attention_score || 0,
			flexibility: baselineData.flexibility_score || 0,
			planning: baselineData.planning_score || 0,
			processing_speed: baselineData.processing_speed_score || 0,
			visual_scanning: baselineData.visual_scanning_score || 0
		};
	}
	
	function getCurrentScores() {
		if (!comparisonData?.comparison) return null;
		return {
			working_memory: comparisonData.comparison.working_memory?.current || 0,
			attention: comparisonData.comparison.attention?.current || 0,
			flexibility: comparisonData.comparison.flexibility?.current || 0,
			planning: comparisonData.comparison.planning?.current || 0,
			processing_speed: comparisonData.comparison.processing_speed?.current || 0,
			visual_scanning: comparisonData.comparison.visual_scanning?.current || 0
		};
	}
	
	// Radar chart calculations
	$: radarPoints = baselineData ? calculateRadarPoints(getBaselineScores()) : '';
	$: currentPoints = comparisonData ? calculateRadarPoints(getCurrentScores()) : '';
	
	// Calculate current overall score from comparison data
	$: currentOverallScore = comparisonData ? calculateOverallScore(getCurrentScores()) : null;
	
	function calculateOverallScore(scores) {
		if (!scores) return null;
		const values = Object.values(scores);
		return values.reduce((sum, score) => sum + score, 0) / values.length;
	}
	
	let radarChartSVG;
	
	function handleDownloadChart() {
		if (!radarChartSVG) return;
		const filename = `baseline-results-${new Date().toISOString().split('T')[0]}`;
		downloadSVGAsPNG(radarChartSVG, filename);
	}
	
	function handleDownloadData() {
		if (!baselineData) return;
		
		const scores = {
			working_memory: baselineData.working_memory_score,
			attention: baselineData.attention_score,
			flexibility: baselineData.flexibility_score,
			planning: baselineData.planning_score,
			processing_speed: baselineData.processing_speed_score,
			visual_scanning: baselineData.visual_scanning_score
		};
		
		const csvData = Object.entries(scores).map(([domain, score]) => ({
			domain: getDomainName(domain),
			score: score.toFixed(1),
			level: getScoreLabel(score)
		}));
		
		const filename = `baseline-data-${new Date().toISOString().split('T')[0]}`;
		downloadCSV(csvData, filename);
	}
	
	function calculateRadarPoints(scores) {
		if (!scores) return '';
		
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
			const score = scores[domain] || 0;
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
			<p>{uiText("Loading baseline data...", $activeLocale)}</p>
		</div>
	{:else if error}
		<div class="error-card">
			<h3>{uiText("Error", $activeLocale)}</h3>
			<p>{error}</p>
			<button class="btn-primary" on:click={loadBaseline}>{uiText("Retry", $activeLocale)}</button>
		</div>
	{:else if !baselineStatus?.all_completed}
		<div class="incomplete-card">
			<h2>{uiText("Complete All Tasks First", $activeLocale)}</h2>
			<p>{uiText("You've completed", $activeLocale)} {n(baselineStatus?.completed_count || 0)} {uiText("out of 6 baseline tasks.", $activeLocale)}</p>
			
			<div class="task-checklist">
				{#each Object.entries(baselineStatus?.tasks || {}) as [task, completed]}
					<div class="checklist-item {completed ? 'completed' : ''}">
						<span class="check">{completed ? '✓' : '○'}</span>
						<span class="name">{getDomainName(task)}</span>
					</div>
				{/each}
			</div>
			
			<button class="btn-primary" on:click={backToDashboard} style="margin-top: 2rem;">
				{uiText("Go to Dashboard", $activeLocale)}
			</button>
		</div>
	{:else if !baselineData}
		<div class="ready-card">
			<h2>{uiText("All Tasks Complete!", $activeLocale)}</h2>
			<p>{uiText("You've completed all 6 cognitive assessment tasks.", $activeLocale)}</p>
			<p style="color: #666; margin-top: 1rem;">{uiText("Click below to calculate your baseline cognitive profile.", $activeLocale)}</p>
			
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
						<h1>{uiText("Cognitive Baseline Assessment", $activeLocale)}</h1>
						<p class="subtitle">{uiText("Comprehensive evaluation of cognitive performance across 6 key domains", $activeLocale)}</p>
					</div>
					<button class="btn-back" on:click={backToDashboard}>{uiText("← Back to Dashboard", $activeLocale)}</button>
				</div>
			</div>
			
			<!-- Overall Score Card -->
			{#if comparisonData && currentOverallScore !== null}
				<!-- Show both baseline and current scores side by side -->
				<div class="scores-comparison">
					<div class="score-card half">
						<h3>{uiText("Baseline Score", $activeLocale)}</h3>
						<div class="medium-score" style="color: {getScoreColor(baselineData.overall_score)}">
							{scoreNumber(baselineData.overall_score)}
						</div>
						<div class="score-label-small">{getScoreLabel(baselineData.overall_score)}</div>
						<p class="date-small">{uiText("Initial:", $activeLocale)} {displayDate(baselineData.assessment_date)}</p>
					</div>
					
					<div class="score-card half current">
						<h3>{uiText("Current Score", $activeLocale)}</h3>
						<div class="medium-score" style="color: {getScoreColor(currentOverallScore)}">
							{scoreNumber(currentOverallScore)}
						</div>
						<div class="score-label-small">{getScoreLabel(currentOverallScore)}</div>
						<div class="improvement">
							{#if currentOverallScore > baselineData.overall_score}
								<span class="improvement-positive">↑ {scoreNumber(currentOverallScore - baselineData.overall_score)} {uiText("improvement", $activeLocale)}</span>
							{:else if currentOverallScore < baselineData.overall_score}
								<span class="improvement-negative">↓ {scoreNumber(baselineData.overall_score - currentOverallScore)} {uiText("decrease", $activeLocale)}</span>
							{:else}
								<span class="improvement-neutral">{uiText("No change", $activeLocale)}</span>
							{/if}
						</div>
					</div>
				</div>
			{:else}
				<!-- Show only baseline score -->
				<div class="score-card overall">
					<h2>{uiText("Overall Cognitive Score", $activeLocale)}</h2>
					<div class="big-score" style="color: {getScoreColor(baselineData.overall_score)}">
						{scoreNumber(baselineData.overall_score)}
					</div>
					<div class="score-label">{getScoreLabel(baselineData.overall_score)}</div>
					<p class="date">{uiText("Assessed on", $activeLocale)} {displayDate(baselineData.assessment_date)}</p>
				</div>
			{/if}
			
			<!-- Radar Chart -->
			<div class="chart-card">
				<div class="chart-header">
					<h3>{uiText("Cognitive Profile", $activeLocale)} {comparisonData ? '(Baseline vs Current)' : ''}</h3>
					<div class="chart-actions">
						<button class="download-btn-small" on:click={handleDownloadChart} title={uiText("Download chart as image", $activeLocale)}>
							{uiText("📊 Chart", $activeLocale)}
						</button>
						<button class="download-btn-small" on:click={handleDownloadData} title={uiText("Download data as CSV", $activeLocale)}>
							{uiText("📋 Data", $activeLocale)}
						</button>
					</div>
				</div>
				<svg bind:this={radarChartSVG} viewBox="0 0 500 400" class="radar-chart">
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
					
					<!-- Baseline polygon (blue dashed) -->
					<polygon 
						points={radarPoints} 
						fill="rgba(102, 126, 234, 0.2)" 
						stroke="#667eea" 
						stroke-width="2"
						stroke-dasharray={comparisonData ? "5,5" : "0"}
					/>
					
					<!-- Current performance polygon (green solid) - only show if comparison data exists -->
					{#if comparisonData && currentPoints}
					<polygon 
						points={currentPoints} 
						fill="rgba(76, 175, 80, 0.2)" 
						stroke="#4caf50" 
						stroke-width="3"
					/>
					{/if}
					
					<!-- Labels -->
					<text x="250" y="60" text-anchor="middle" class="chart-label">{uiText("Working Memory", $activeLocale)}</text>
					<text x="385" y="145" text-anchor="start" class="chart-label">{uiText("Attention", $activeLocale)}</text>
					<text x="385" y="265" text-anchor="start" class="chart-label">{uiText("Cognitive Flexibility", $activeLocale)}</text>
					<text x="250" y="350" text-anchor="middle" class="chart-label">{uiText("Planning", $activeLocale)}</text>
					<text x="115" y="265" text-anchor="end" class="chart-label">{uiText("Processing Speed", $activeLocale)}</text>
					<text x="115" y="145" text-anchor="end" class="chart-label">{uiText("Visual Scanning", $activeLocale)}</text>
				</svg>
				
				<!-- Legend (only show if comparison data exists) -->
				{#if comparisonData}
				<div style="display: flex; justify-content: center; gap: 2rem; margin-top: 1rem; font-size: 0.9rem;">
					<div style="display: flex; align-items: center; gap: 0.5rem;">
						<svg width="30" height="3">
							<line x1="0" y1="1.5" x2="30" y2="1.5" stroke="#667eea" stroke-width="2" stroke-dasharray="5,5"/>
						</svg>
						<span>{uiText("Baseline", $activeLocale)}</span>
					</div>
					<div style="display: flex; align-items: center; gap: 0.5rem;">
						<svg width="30" height="3">
							<line x1="0" y1="1.5" x2="30" y2="1.5" stroke="#4caf50" stroke-width="3"/>
						</svg>
						<span>{uiText("Current", $activeLocale)}</span>
					</div>
				</div>
				{/if}
			</div>
			
			<!-- Domain Scores -->
			<div class="domains-grid">
				<div class="domain-card">
					<div class="domain-header">
						<h4>{uiText("Working Memory", $activeLocale)}</h4>
					</div>
					{#if comparisonData}
						<div class="domain-scores-row">
							<div class="baseline-score">
								<div class="score-mini" style="color: {getScoreColor(baselineData.working_memory_score)}">
									{scoreNumber(baselineData.working_memory_score)}
								</div>
								<div class="score-type">{uiText("Baseline", $activeLocale)}</div>
							</div>
							<div class="current-score-mini">
								<div class="score-mini" style="color: {getScoreColor(comparisonData.comparison.working_memory?.current || 0)}">
									{scoreNumber(comparisonData.comparison.working_memory?.current || 0)}
								</div>
								<div class="score-type">{uiText("Current", $activeLocale)}</div>
							</div>
						</div>
					{:else}
						<div class="domain-score" style="color: {getScoreColor(baselineData.working_memory_score)}">
							{scoreNumber(baselineData.working_memory_score)}
						</div>
						<div class="progress-bar">
							<div class="progress-fill" style="width: {baselineData.working_memory_score}%; background: {getScoreColor(baselineData.working_memory_score)}"></div>
						</div>
					{/if}
				</div>
				
				<div class="domain-card">
					<div class="domain-header">
						<h4>{uiText("Attention", $activeLocale)}</h4>
					</div>
					{#if comparisonData}
						<div class="domain-scores-row">
							<div class="baseline-score">
								<div class="score-mini" style="color: {getScoreColor(baselineData.attention_score)}">
									{scoreNumber(baselineData.attention_score)}
								</div>
								<div class="score-type">{uiText("Baseline", $activeLocale)}</div>
							</div>
							<div class="current-score-mini">
								<div class="score-mini" style="color: {getScoreColor(comparisonData.comparison.attention?.current || 0)}">
									{scoreNumber(comparisonData.comparison.attention?.current || 0)}
								</div>
								<div class="score-type">{uiText("Current", $activeLocale)}</div>
							</div>
						</div>
					{:else}
						<div class="domain-score" style="color: {getScoreColor(baselineData.attention_score)}">
							{scoreNumber(baselineData.attention_score)}
						</div>
						<div class="progress-bar">
							<div class="progress-fill" style="width: {baselineData.attention_score}%; background: {getScoreColor(baselineData.attention_score)}"></div>
						</div>
					{/if}
				</div>
				
				<div class="domain-card">
					<div class="domain-header">
						<h4>{uiText("Cognitive Flexibility", $activeLocale)}</h4>
					</div>
					{#if comparisonData}
						<div class="domain-scores-row">
							<div class="baseline-score">
								<div class="score-mini" style="color: {getScoreColor(baselineData.flexibility_score)}">
									{scoreNumber(baselineData.flexibility_score)}
								</div>
								<div class="score-type">{uiText("Baseline", $activeLocale)}</div>
							</div>
							<div class="current-score-mini">
								<div class="score-mini" style="color: {getScoreColor(comparisonData.comparison.flexibility?.current || 0)}">
									{scoreNumber(comparisonData.comparison.flexibility?.current || 0)}
								</div>
								<div class="score-type">{uiText("Current", $activeLocale)}</div>
							</div>
						</div>
					{:else}
						<div class="domain-score" style="color: {getScoreColor(baselineData.flexibility_score)}">
							{scoreNumber(baselineData.flexibility_score)}
						</div>
						<div class="progress-bar">
							<div class="progress-fill" style="width: {baselineData.flexibility_score}%; background: {getScoreColor(baselineData.flexibility_score)}"></div>
						</div>
					{/if}
				</div>
				
				<div class="domain-card">
					<div class="domain-header">
						<h4>{uiText("Planning", $activeLocale)}</h4>
					</div>
					{#if comparisonData}
						<div class="domain-scores-row">
							<div class="baseline-score">
								<div class="score-mini" style="color: {getScoreColor(baselineData.planning_score)}">
									{scoreNumber(baselineData.planning_score)}
								</div>
								<div class="score-type">{uiText("Baseline", $activeLocale)}</div>
							</div>
							<div class="current-score-mini">
								<div class="score-mini" style="color: {getScoreColor(comparisonData.comparison.planning?.current || 0)}">
									{scoreNumber(comparisonData.comparison.planning?.current || 0)}
								</div>
								<div class="score-type">{uiText("Current", $activeLocale)}</div>
							</div>
						</div>
					{:else}
						<div class="domain-score" style="color: {getScoreColor(baselineData.planning_score)}">
							{scoreNumber(baselineData.planning_score)}
						</div>
						<div class="progress-bar">
							<div class="progress-fill" style="width: {baselineData.planning_score}%; background: {getScoreColor(baselineData.planning_score)}"></div>
						</div>
					{/if}
				</div>
				
				<div class="domain-card">
					<div class="domain-header">
						<h4>{uiText("Processing Speed", $activeLocale)}</h4>
					</div>
					{#if comparisonData}
						<div class="domain-scores-row">
							<div class="baseline-score">
								<div class="score-mini" style="color: {getScoreColor(baselineData.processing_speed_score)}">
									{scoreNumber(baselineData.processing_speed_score)}
								</div>
								<div class="score-type">{uiText("Baseline", $activeLocale)}</div>
							</div>
							<div class="current-score-mini">
								<div class="score-mini" style="color: {getScoreColor(comparisonData.comparison.processing_speed?.current || 0)}">
									{scoreNumber(comparisonData.comparison.processing_speed?.current || 0)}
								</div>
								<div class="score-type">{uiText("Current", $activeLocale)}</div>
							</div>
						</div>
					{:else}
						<div class="domain-score" style="color: {getScoreColor(baselineData.processing_speed_score)}">
							{scoreNumber(baselineData.processing_speed_score)}
						</div>
						<div class="progress-bar">
							<div class="progress-fill" style="width: {baselineData.processing_speed_score}%; background: {getScoreColor(baselineData.processing_speed_score)}"></div>
						</div>
					{/if}
				</div>
				
				<div class="domain-card">
					<div class="domain-header">
						<h4>{uiText("Visual Scanning", $activeLocale)}</h4>
					</div>
					{#if comparisonData}
						<div class="domain-scores-row">
							<div class="baseline-score">
								<div class="score-mini" style="color: {getScoreColor(baselineData.visual_scanning_score)}">
									{scoreNumber(baselineData.visual_scanning_score)}
								</div>
								<div class="score-type">{uiText("Baseline", $activeLocale)}</div>
							</div>
							<div class="current-score-mini">
								<div class="score-mini" style="color: {getScoreColor(comparisonData.comparison.visual_scanning?.current || 0)}">
									{scoreNumber(comparisonData.comparison.visual_scanning?.current || 0)}
								</div>
								<div class="score-type">{uiText("Current", $activeLocale)}</div>
							</div>
						</div>
					{:else}
						<div class="domain-score" style="color: {getScoreColor(baselineData.visual_scanning_score)}">
							{scoreNumber(baselineData.visual_scanning_score)}
						</div>
						<div class="progress-bar">
							<div class="progress-fill" style="width: {baselineData.visual_scanning_score}%; background: {getScoreColor(baselineData.visual_scanning_score)}"></div>
						</div>
					{/if}
				</div>
			</div>
			
			<!-- Insights -->
			<div class="insights-card">
				<h3>{uiText("Insights & Recommendations", $activeLocale)}</h3>
				<div class="insights-content">
					{#if comparisonData && currentOverallScore !== null}
						<!-- Show insights based on current performance -->
						{#if currentOverallScore >= 80}
							<p><strong>{uiText("Excellent cognitive performance!", $activeLocale)}</strong> {uiText("Your scores are above average across all domains.", $activeLocale)}</p>
							{#if currentOverallScore > baselineData.overall_score}
								<p style="margin-top: 0.5rem;">{uiText("You've improved by", $activeLocale)} <strong>{scoreNumber(currentOverallScore - baselineData.overall_score)} {uiText("points", $activeLocale)}</strong> {uiText("from your baseline! Keep up the great work.", $activeLocale)}</p>
							{/if}
						{:else if currentOverallScore >= 60}
							<p><strong>{uiText("Good cognitive performance.", $activeLocale)}</strong> {uiText("You have a solid foundation with room for targeted improvement.", $activeLocale)}</p>
							{#if currentOverallScore > baselineData.overall_score}
								<p style="margin-top: 0.5rem;">{uiText("You've improved by", $activeLocale)} <strong>{scoreNumber(currentOverallScore - baselineData.overall_score)} {uiText("points", $activeLocale)}</strong> {uiText("from your baseline! Continue your training to reach excellence.", $activeLocale)}</p>
							{/if}
						{:else}
							<p><strong>{uiText("Keep training!", $activeLocale)}</strong> {uiText("Regular practice will help improve your cognitive performance.", $activeLocale)}</p>
							{#if currentOverallScore > baselineData.overall_score}
								<p style="margin-top: 0.5rem;">{uiText("You've improved by", $activeLocale)} <strong>{scoreNumber(currentOverallScore - baselineData.overall_score)} {uiText("points", $activeLocale)}</strong> {uiText("from your baseline. You're making progress!", $activeLocale)}</p>
							{/if}
						{/if}
						
						<div class="recommendation">
							<h4>{uiText("Current Focus Areas:", $activeLocale)}</h4>
							<ul>
								{#each Object.entries({
									working_memory: comparisonData.comparison.working_memory?.current || 0,
									attention: comparisonData.comparison.attention?.current || 0,
									flexibility: comparisonData.comparison.flexibility?.current || 0,
									planning: comparisonData.comparison.planning?.current || 0,
									processing_speed: comparisonData.comparison.processing_speed?.current || 0,
									visual_scanning: comparisonData.comparison.visual_scanning?.current || 0
								}).sort((a, b) => a[1] - b[1]).slice(0, 3) as [domain, score]}
									{#if score < 70}
									<li><strong>{getDomainName(domain)}</strong> {uiText("- Current:", $activeLocale)} {scoreNumber(score)}</li>
									{/if}
								{/each}
							</ul>
						</div>
					{:else}
						<!-- Show baseline insights -->
						{#if baselineData.overall_score >= 80}
							<p><strong>{uiText("Excellent cognitive performance!", $activeLocale)}</strong> {uiText("Your scores are above average across all domains.", $activeLocale)}</p>
						{:else if baselineData.overall_score >= 60}
							<p><strong>{uiText("Good cognitive performance.", $activeLocale)}</strong> {uiText("You have a solid foundation with room for targeted improvement.", $activeLocale)}</p>
						{:else}
							<p><strong>{uiText("Baseline established.", $activeLocale)}</strong> {uiText("Regular training will help improve your cognitive performance.", $activeLocale)}</p>
						{/if}
						
						<div class="recommendation">
							<h4>{uiText("Focus Areas:", $activeLocale)}</h4>
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
									<li><strong>{getDomainName(domain)}</strong> {uiText("- Score:", $activeLocale)} {scoreNumber(score)}</li>
									{/if}
								{/each}
							</ul>
						</div>
					{/if}
				</div>
			</div>
			
			<div style="text-align: center; margin-top: 2rem;">
				<button class="btn-primary" on:click={backToDashboard}>
					{uiText("Continue to Dashboard", $activeLocale)}
				</button>
				<button 
					class="btn-secondary" 
					on:click={calculateBaseline} 
					disabled={calculating}
					style="margin-left: 1rem;"
				>
					{calculating ? 'Recalculating...' : 'Recalculate Baseline'}
				</button>
				{#if !trainingPlan}
					<button 
						class="btn-training" 
						on:click={generateTrainingPlan}
						disabled={generatingPlan}
						style="margin-left: 1rem;"
					>
						{generatingPlan ? 'Generating...' : 'Generate Training Plan'}
					</button>
				{:else}
					<button 
						class="btn-training" 
						on:click={() => goto('/dashboard')}
						style="margin-left: 1rem;"
					>
						{uiText("View Training Plan", $activeLocale)}
					</button>
				{/if}
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
	
	.scores-comparison {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.5rem;
		margin-bottom: 2rem;
	}
	
	.score-card.half {
		background: white;
		border-radius: 20px;
		padding: 2rem;
		text-align: center;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
		margin-bottom: 0;
	}
	
	.score-card.half h3 {
		margin: 0 0 1rem 0;
		color: #666;
		font-size: 1.2rem;
		font-weight: 600;
	}
	
	.score-card.half.current {
		background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
		color: white;
	}
	
	.score-card.half.current h3 {
		color: white;
		opacity: 0.95;
	}
	
	.medium-score {
		font-size: 3.5rem;
		font-weight: bold;
		margin: 1rem 0;
	}
	
	.score-label-small {
		font-size: 1.2rem;
		opacity: 0.9;
		margin-bottom: 0.5rem;
	}
	
	.date-small {
		margin-top: 0.5rem;
		opacity: 0.7;
		font-size: 0.85rem;
	}
	
	.improvement {
		margin-top: 0.75rem;
		font-size: 0.95rem;
		font-weight: 600;
	}
	
	.improvement-positive {
		color: #fff;
		opacity: 0.95;
	}
	
	.improvement-negative {
		color: #fff;
		opacity: 0.95;
	}
	
	.improvement-neutral {
		color: #fff;
		opacity: 0.8;
	}
	
	@media (max-width: 768px) {
		.scores-comparison {
			grid-template-columns: 1fr;
		}
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
	
	.chart-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
		gap: 1rem;
		flex-wrap: wrap;
	}
	
	.chart-header h3 {
		margin: 0;
		color: #333;
		flex: 1;
		min-width: 150px;
	}
	
	.chart-actions {
		display: flex;
		gap: 0.5rem;
	}
	
	.download-btn-small {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		padding: 0.4rem 0.8rem;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		border-radius: 6px;
		font-size: 0.8rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s;
		box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
		white-space: nowrap;
	}
	
	.download-btn-small:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
	}
	
	.download-btn-small:active {
		transform: translateY(0);
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
	
	.domain-scores-row {
		display: flex;
		justify-content: space-around;
		align-items: center;
		gap: 1rem;
		margin-top: 1rem;
	}
	
	.baseline-score, .current-score-mini {
		text-align: center;
		flex: 1;
	}
	
	.score-mini {
		font-size: 2rem;
		font-weight: bold;
		margin-bottom: 0.25rem;
	}
	
	.score-type {
		font-size: 0.8rem;
		color: #666;
		text-transform: uppercase;
		letter-spacing: 0.5px;
		font-weight: 600;
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
	
	.btn-training {
		background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
		color: white;
		border: none;
		padding: 1rem 2.5rem;
		border-radius: 12px;
		font-size: 1.1rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s;
	}
	
	.btn-training:hover:not(:disabled) {
		transform: translateY(-2px);
		box-shadow: 0 8px 20px rgba(76, 175, 80, 0.4);
	}
	
	.btn-training:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
</style>

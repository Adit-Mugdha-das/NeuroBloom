<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	const API_BASE_URL = 'http://127.0.0.1:8000';

	let currentUser = null;
	let loading = true;
	let sessionData = null;
	let difficulty = 1;
	let currentTrial = 0;
	let responses = [];
	let phase = 'intro'; // intro, instructions, practice, test, results
	let showResults = false;
	let metrics = null;
	let newBadges = [];
	let taskId = null;

	// Practice state
	let practiceTrials = [];
	let currentPractice = 0;
	let practiceFeedback = null;

	// Test state
	let startTime = 0;
	let responded = false;
	let showStimulus = false;
	let trialTimeout = null;
	let stimulusTimeout = null;
	let interStimulusTimeout = null;

	// Help modal
	let showHelp = false;

	// Subscribe to user store
	user.subscribe((value) => {
		currentUser = value;
	});

	onMount(async () => {
		if (!currentUser) {
			goto('/login');
			return;
		}
		await loadSession();
	});

	async function loadSession() {
		try {
			loading = true;
			const response = await fetch(`${API_BASE_URL}/api/training/tasks/flanker/generate/${currentUser.id}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' }
			});

			if (!response.ok) {
				const errorText = await response.text();
				throw new Error(`Failed to load session: ${response.status} - ${errorText}`);
			}

			const data = await response.json();
			sessionData = data.session_data;
			difficulty = data.difficulty;
			loading = false;
		} catch (error) {
			console.error('Error loading session:', error);
			alert('Failed to load training session. Please ensure the backend server is running and you have completed baseline assessment.');
			loading = false;
		}
	}

	function startInstructions() {
		phase = 'instructions';
	}

	function startPractice() {
		// Create practice trials (8 trials: 4 congruent, 4 incongruent)
		practiceTrials = [
			{
				trial_type: 'congruent',
				direction: 'right',
				flanker_count: 2,
				hint: 'Easy! All arrows point right →'
			},
			{
				trial_type: 'congruent',
				direction: 'left',
				flanker_count: 2,
				hint: 'All arrows point left ←'
			},
			{
				trial_type: 'incongruent',
				direction: 'right',
				flanker_count: 2,
				hint: 'Focus on the CENTER arrow only! →'
			},
			{
				trial_type: 'congruent',
				direction: 'right',
				flanker_count: 2,
				hint: 'Congruent again - quick!'
			},
			{
				trial_type: 'incongruent',
				direction: 'left',
				flanker_count: 2,
				hint: 'Ignore distractors - CENTER is ←'
			},
			{
				trial_type: 'congruent',
				direction: 'left',
				flanker_count: 2,
				hint: 'All matching, press quickly'
			},
			{
				trial_type: 'incongruent',
				direction: 'right',
				flanker_count: 2,
				hint: 'Hard! Flankers mislead you'
			},
			{
				trial_type: 'incongruent',
				direction: 'left',
				flanker_count: 2,
				hint: 'Last one - stay focused on CENTER'
			}
		];

		currentPractice = 0;
		practiceFeedback = null;
		phase = 'practice';
		showNextPracticeTrial();
	}

	function showNextPracticeTrial() {
		// Clear any existing timers
		clearTimeout(stimulusTimeout);
		
		if (currentPractice >= practiceTrials.length) {
			// Practice complete
			practiceFeedback = {
				type: 'success',
				message: '✓ Practice complete! You\'re ready for the real test.'
			};
			setTimeout(() => {
				startTest();
			}, 2000);
			return;
		}

		responded = false;
		showStimulus = true;
		startTime = Date.now();

		// Auto-advance after 3 seconds for practice
		stimulusTimeout = setTimeout(() => {
			if (!responded) {
				practiceFeedback = {
					type: 'warning',
					message: '⏱️ Too slow! Try to respond faster.'
				};
				showStimulus = false;
				setTimeout(() => {
					practiceFeedback = null;
					currentPractice++;
					showNextPracticeTrial();
				}, 1500);
			}
		}, 3000);
	}

	function handlePracticeResponse(direction) {
		if (!showStimulus || responded) return;
		
		clearTimeout(stimulusTimeout);
		responded = true;
		
		const trial = practiceTrials[currentPractice];
		const rt = Date.now() - startTime;
		const correct = direction === trial.direction;

		if (correct) {
			practiceFeedback = {
				type: 'success',
				message: `✓ Correct! Response time: ${rt}ms. ${trial.hint}`
			};
		} else {
			practiceFeedback = {
				type: 'error',
				message: `✗ Wrong direction! CENTER arrow pointed ${trial.direction === 'right' ? 'RIGHT →' : 'LEFT ←'}. ${trial.hint}`
			};
		}

		showStimulus = false;

		// Auto-advance after showing feedback
		setTimeout(() => {
			practiceFeedback = null;
			currentPractice++;
			showNextPracticeTrial();
		}, 2000);
	}

	function startTest() {
		phase = 'test';
		currentTrial = 0;
		responses = [];
		showNextTrial();
	}

	function showNextTrial() {
		// Clear all existing timers to prevent race conditions
		clearTimeout(stimulusTimeout);
		clearTimeout(interStimulusTimeout);
		clearTimeout(trialTimeout);
		
		if (currentTrial >= sessionData.trials.length) {
			completeSession();
			return;
		}

		responded = false;
		showStimulus = false;

		// Inter-stimulus interval (fixation cross)
		interStimulusTimeout = setTimeout(() => {
			showStimulus = true;
			startTime = Date.now();

			// Hide stimulus after presentation time
			stimulusTimeout = setTimeout(() => {
				showStimulus = false;

				// If no response yet, wait a bit then record as missed
				if (!responded) {
					trialTimeout = setTimeout(() => {
						recordResponse(null, 0);
					}, 300);
				}
			}, sessionData.presentation_time_ms);
		}, 500); // 500ms fixation
	}

	function recordResponse(direction, reactionTime) {
		if (responded) return;
		
		// Clear all timers immediately
		clearTimeout(stimulusTimeout);
		clearTimeout(interStimulusTimeout);
		clearTimeout(trialTimeout);
		
		responded = true;

		const trial = sessionData.trials[currentTrial];

		responses.push({
			trial_number: trial.trial_number,
			trial_type: trial.trial_type,
			target_direction: trial.target_direction,
			responded_direction: direction,
			reaction_time_ms: reactionTime,
			correct: direction === trial.target_direction
		});

		currentTrial++;
		showStimulus = false;

		// Brief pause before next trial
		interStimulusTimeout = setTimeout(() => {
			showNextTrial();
		}, 300);
	}

	function handleKeyPress(event) {
		if (phase === 'practice' && showStimulus && !responded) {
			if (event.key === 'ArrowLeft' || event.key === 'a' || event.key === 'A') {
				event.preventDefault();
				handlePracticeResponse('left');
			} else if (event.key === 'ArrowRight' || event.key === 'd' || event.key === 'D') {
				event.preventDefault();
				handlePracticeResponse('right');
			}
		} else if (phase === 'test' && showStimulus && !responded) {
			const rt = Date.now() - startTime;
			if (event.key === 'ArrowLeft' || event.key === 'a' || event.key === 'A') {
				event.preventDefault();
				recordResponse('left', rt);
			} else if (event.key === 'ArrowRight' || event.key === 'd' || event.key === 'D') {
				event.preventDefault();
				recordResponse('right', rt);
			}
		}
	}

	async function completeSession() {
		try {
			taskId = $page.url.searchParams.get('taskId');
			const response = await fetch(`${API_BASE_URL}/api/training/tasks/flanker/submit/${currentUser.id}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					difficulty,
					session_data: sessionData,
					responses,
					task_id: taskId
				})
			});

			if (!response.ok) throw new Error('Failed to submit session');

			const data = await response.json();
			metrics = data.metrics;
			newBadges = data.new_badges || [];
			phase = 'results';
			showResults = true;
		} catch (error) {
			console.error('Error submitting session:', error);
			alert('Failed to submit results. Please try again.');
		}
	}

	function returnToDashboard() {
		goto('/dashboard');
	}

	// Progress tracking
	$: progress = sessionData ? ((currentTrial / sessionData.trials.length) * 100) : 0;
	$: trialsRemaining = sessionData ? sessionData.trials.length - currentTrial : 0;

	// Performance badge color
	$: performanceBadgeColor = metrics?.performance_level === 'Excellent' ? 'from-green-500'
		: metrics?.performance_level === 'Good' ? 'from-blue-500'
		: metrics?.performance_level === 'Fair' ? 'from-yellow-500'
		: 'from-gray-500';

	// Generate arrow display for trials
	function generateArrowDisplay(trial) {
		const leftArrow = '←';
		const rightArrow = '→';
		const centerArrow = trial.target_direction === 'right' ? rightArrow : leftArrow;
		const flankerArrow = trial.trial_type === 'congruent' 
			? centerArrow 
			: (centerArrow === rightArrow ? leftArrow : rightArrow);
		
		const flankers = Array(trial.flanker_count).fill(flankerArrow).join(' ');
		return `${flankers} ${centerArrow} ${flankers}`;
	}

	function generatePracticeArrowDisplay(trial) {
		const leftArrow = '←';
		const rightArrow = '→';
		const centerArrow = trial.direction === 'right' ? rightArrow : leftArrow;
		const flankerArrow = trial.trial_type === 'congruent' 
			? centerArrow 
			: (centerArrow === rightArrow ? leftArrow : rightArrow);
		
		const flankers = Array(trial.flanker_count).fill(flankerArrow).join(' ');
		return `${flankers} ${centerArrow} ${flankers}`;
	}
</script>

<svelte:window on:keydown={handleKeyPress} />

<div class="flanker-container">
	{#if loading}
		<div class="loading">
			<div class="spinner"></div>
			<p>Loading task...</p>
		</div>
	{:else if phase === 'intro'}
		<!-- Introduction Screen -->
		<div class="instructions">
			<div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap;">
				<h1>⚡ Flanker Task</h1>
				<DifficultyBadge {difficulty} domain="Attention" />
			</div>
			<div class="classic-badge">Selective Attention & Conflict Resolution Test</div>
			
			<div class="instruction-card">
				<div class="task-header">
					<h2>🎯 Your Mission: Focus on the Center!</h2>
				</div>
				
				<p class="importance">
					This task measures your ability to <strong>selectively attend</strong> to relevant information 
					while <strong>ignoring distractions</strong> - a key cognitive skill tested in the Attention Networks Test (ANT).
				</p>
				
				<!-- Visual Examples -->
				<div class="stimulus-examples">
					<div class="example-card congruent-card">
						<div class="example-label">Congruent Trial (Easy)</div>
						<div class="arrow-display">→ → → → →</div>
						<div class="example-action">✓ All arrows match</div>
						<div class="example-note">CENTER arrow: <strong>RIGHT →</strong></div>
					</div>
					
					<div class="example-card incongruent-card">
						<div class="example-label">Incongruent Trial (Hard)</div>
						<div class="arrow-display conflict">← ← → ← ←</div>
						<div class="example-action">⚠️ Flankers mislead!</div>
						<div class="example-note">CENTER arrow: <strong>RIGHT →</strong> (ignore the rest!)</div>
					</div>
				</div>
				
				<div class="rule-box">
					<strong>⚡ The Challenge:</strong>
					You'll see arrows on the screen. <strong>Always report the direction of the CENTER arrow only!</strong>
					Surrounding "flanker" arrows will sometimes point the opposite direction to test your ability to 
					focus and resist distraction.
				</div>
				
				<!-- Two Column Layout -->
				<div class="info-grid">
					<div class="info-section">
						<h3>📋 What You'll Do</h3>
						<div class="steps-list">
							<div class="step-item">
								<span class="step-num">1</span>
								<div class="step-text">
									<strong>Watch for arrows</strong>
									<span>They appear briefly</span>
								</div>
							</div>
							<div class="step-item">
								<span class="step-num">2</span>
								<div class="step-text">
									<strong>Focus on CENTER</strong>
									<span>Ignore surrounding arrows</span>
								</div>
							</div>
							<div class="step-item">
								<span class="step-num">3</span>
								<div class="step-text">
									<strong>Press arrow key</strong>
									<span>← or → to match center</span>
								</div>
							</div>
						</div>
					</div>
					
					<div class="info-section">
						<h3>💪 What It Measures</h3>
						<div class="measures-list">
							<div class="measure-item">✓ <strong>Selective Attention:</strong> Focusing ability</div>
							<div class="measure-item">✓ <strong>Conflict Resolution:</strong> Ignoring distractors</div>
							<div class="measure-item">✓ <strong>Interference Control:</strong> Resistance to misleading info</div>
							<div class="measure-item">✓ <strong>Processing Speed:</strong> Quick decision-making</div>
						</div>
					</div>
				</div>
				
				<!-- Clinical Context -->
				<div class="clinical-info">
					<h3>📚 Clinical Significance</h3>
					<div class="clinical-grid">
						<div class="clinical-item">
							<strong>🎯 Standard Test:</strong> Attention Networks Test (Eriksen & Eriksen, 1974)
						</div>
						<div class="clinical-item">
							<strong>🧠 Brain Regions:</strong> Tests anterior cingulate cortex & executive control
						</div>
						<div class="clinical-item">
							<strong>🏥 MS Relevance:</strong> Measures selective attention deficits common in MS
						</div>
						<div class="clinical-item">
							<strong>📈 Key Metric:</strong> Conflict Effect = slower RT on incongruent trials
						</div>
					</div>
				</div>
				
				<!-- Controls -->
				<div class="controls-info">
					<h3>🎮 Controls</h3>
					<div class="key-bindings">
						<div class="key-bind">
							<kbd>←</kbd> or <kbd>A</kbd> = Left arrow
						</div>
						<div class="key-bind">
							<kbd>→</kbd> or <kbd>D</kbd> = Right arrow
						</div>
					</div>
				</div>
			</div>
			
			<div class="button-group">
				<button class="start-button" on:click={startInstructions}>
					Begin Task
				</button>
				<button class="btn-secondary" on:click={() => goto('/dashboard')}>
					Back to Dashboard
				</button>
			</div>
		</div>

	{:else if phase === 'instructions'}
		<!-- Quick Instructions -->
		<div class="quick-instructions">
			<h2>Quick Instructions</h2>

			<div class="key-reminder">
				<div class="key-display">
					<kbd class="key-large">←</kbd>
					<span class="key-label">Left Arrow</span>
				</div>
				<div class="key-display">
					<kbd class="key-large">→</kbd>
					<span class="key-label">Right Arrow</span>
				</div>
			</div>

			<div class="task-rule">
				<p class="rule-emphasis">Press the arrow key matching the <strong>CENTER arrow direction</strong> only!</p>
			</div>

			<div class="instructions-flow">
				<div class="flow-step">
					<div class="flow-number">1</div>
					<div class="flow-content">
						<p class="flow-title">Arrows Appear</p>
						<p class="flow-desc">5 arrows flash briefly</p>
					</div>
				</div>

				<div class="flow-arrow">→</div>

				<div class="flow-step">
					<div class="flow-number">2</div>
					<div class="flow-content">
						<p class="flow-title">Focus on Center</p>
						<p class="flow-desc">Ignore outer flankers</p>
					</div>
				</div>

				<div class="flow-arrow">→</div>

				<div class="flow-step">
					<div class="flow-number">3</div>
					<div class="flow-content">
						<p class="flow-title">Press Arrow Key</p>
						<p class="flow-desc">Match center direction</p>
					</div>
				</div>
			</div>

			<div class="example-reminder">
				<div class="example-row">
					<div class="example-stimulus">→ → → → →</div>
					<div class="example-answer">Press <kbd>→</kbd> (Easy - all match)</div>
				</div>
				<div class="example-row conflict">
					<div class="example-stimulus">← ← → ← ←</div>
					<div class="example-answer">Press <kbd>→</kbd> (Hard - center is right!)</div>
				</div>
			</div>

			<div class="tips-box">
				<h3>💡 Success Tips</h3>
				<ul>
					<li><strong>Focus your eyes</strong> on the center of the screen</li>
					<li><strong>Ignore flankers</strong> - they're designed to mislead you</li>
					<li><strong>Respond quickly</strong> - but accuracy matters more than speed</li>
					<li><strong>Stay consistent</strong> - maintain attention throughout</li>
				</ul>
			</div>

			<div class="practice-prompt">
				<p>Let's practice with 8 trials to get comfortable...</p>
				<button class="start-button" on:click={startPractice}>
					Start Practice
				</button>
			</div>
		</div>

	{:else if phase === 'practice'}
		<!-- Practice Trials -->
		<div class="trial-screen">
			<div class="trial-header">
				<h2>Practice Trial {currentPractice + 1} of {practiceTrials.length}</h2>
				<p class="instruction-reminder">Press ← or → to match the CENTER arrow direction</p>
			</div>

			<!-- Stimulus Display -->
			<div class="stimulus-area">
				{#if showStimulus}
					<div class="arrow-stimulus {practiceTrials[currentPractice].trial_type}">
						{generatePracticeArrowDisplay(practiceTrials[currentPractice])}
					</div>
				{:else}
					<div class="fixation">+</div>
				{/if}
			</div>

			<!-- Feedback -->
			{#if practiceFeedback}
				<div class="feedback-box {practiceFeedback.type}">
					<p>{practiceFeedback.message}</p>
				</div>
			{/if}
		</div>

	{:else if phase === 'test'}
		<!-- Test Trials -->
		<div class="trial-screen">
			<!-- Progress Header -->
			<div class="progress-header">
				<div class="progress-top">
					<h2>Trial {currentTrial + 1} of {sessionData.trials.length}</h2>
					<div class="progress-badges">
						<span class="badge-remaining">{trialsRemaining} remaining</span>
					</div>
				</div>
				<div class="progress-bar-container">
					<div class="progress-bar-fill" style="width: {progress}%"></div>
				</div>
			</div>

			<!-- Stimulus Display -->
			<div class="stimulus-area">
				{#if showStimulus && currentTrial < sessionData.trials.length}
					<div class="arrow-stimulus {sessionData.trials[currentTrial].trial_type}">
						{generateArrowDisplay(sessionData.trials[currentTrial])}
					</div>
				{:else}
					<div class="fixation">+</div>
				{/if}
			</div>

			<div class="reminder-text">
				Focus on CENTER arrow only | ← or → keys
			</div>
		</div>

		<!-- Results Screen -->
		<div class="results-container">
			<!-- Badge Notifications -->
			{#if newBadges.length > 0}
				<BadgeNotification badges={newBadges} />
			{/if}

			<div class="results-header">
				<h2>Flanker Task Complete!</h2>
				<div class="performance-badge {performanceBadgeColor}">
					{metrics.performance_level}
				</div>
			</div>

			<!-- Key Metrics Grid -->
			<div class="metrics-grid">
				<!-- Overall Accuracy -->
				<div class="metric-card accuracy-card">
					<div class="metric-label">Overall Accuracy</div>
					<div class="metric-value">{(metrics?.overall_accuracy || 0).toFixed(1)}%</div>
					<div class="metric-detail">{metrics?.total_correct || 0}/{metrics?.total_trials || 0} correct</div>
				</div>

				<!-- Mean RT -->
				<div class="metric-card speed-card">
					<div class="metric-label">Mean Reaction Time</div>
					<div class="metric-value">{(metrics?.mean_rt || 0).toFixed(0)} ms</div>
					<div class="metric-detail">Overall speed</div>
				</div>

				<!-- Conflict Effect -->
				<div class="metric-card conflict-card">
					<div class="metric-label">⚠️ Conflict Effect</div>
					<div class="metric-value">{(metrics?.conflict_effect || 0).toFixed(0)} ms</div>
					<div class="metric-detail">Interference cost</div>
				</div>

				<!-- Selective Attention Score -->
				<div class="metric-card attention-card">
					<div class="metric-label">Selective Attention</div>
					<div class="metric-value">{(metrics?.selective_attention_score || 0).toFixed(1)}</div>
					<div class="metric-detail">Lower = better focus</div>
				</div>
			</div>

			<!-- Trial Type Breakdown -->
			<div class="breakdown-section">
				<h3>Performance by Trial Type</h3>
				<div class="breakdown-grid">
					<!-- Congruent Trials -->
					<div class="breakdown-card congruent-card">
						<p class="breakdown-title">Congruent Trials (Easy)</p>
						<p class="breakdown-subtitle">All arrows point same direction</p>
						<p class="breakdown-stat">Accuracy: <span>{(metrics?.congruent_accuracy || 0).toFixed(1)}%</span></p>
						<p class="breakdown-stat">Mean RT: <span>{(metrics?.congruent_mean_rt || 0).toFixed(0)} ms</span></p>
						<p class="breakdown-stat">Correct: <span>{metrics?.congruent_correct || 0}/{metrics?.congruent_trials || 0}</span></p>
						<p class="breakdown-note">Tests baseline processing speed</p>
					</div>

					<!-- Incongruent Trials -->
					<div class="breakdown-card incongruent-card">
						<p class="breakdown-title">Incongruent Trials (Hard)</p>
						<p class="breakdown-subtitle">Flankers point opposite direction</p>
						<p class="breakdown-stat">Accuracy: <span>{(metrics?.incongruent_accuracy || 0).toFixed(1)}%</span></p>
						<p class="breakdown-stat">Mean RT: <span>{(metrics?.incongruent_mean_rt || 0).toFixed(0)} ms</span></p>
						<p class="breakdown-stat">Correct: <span>{metrics?.incongruent_correct || 0}/{metrics?.incongruent_trials || 0}</span></p>
						<p class="breakdown-note highlight">Tests selective attention & conflict resolution</p>
					</div>
				</div>
			</div>

			<!-- Interference Analysis -->
			<div class="interference-section">
				<h3>🎯 Interference Analysis</h3>
				<div class="interference-grid">
					<div class="interference-card">
						<p class="interference-label">Conflict Effect</p>
						<p class="interference-value">{(metrics?.conflict_effect || 0).toFixed(0)} ms</p>
						<p class="interference-desc">
							How much slower you are on incongruent trials. 
							Lower = better selective attention!
						</p>
					</div>
					<div class="interference-card">
						<p class="interference-label">Interference Error Rate</p>
						<p class="interference-value">{(metrics?.interference_error_rate || 0).toFixed(1)}%</p>
						<p class="interference-desc">
							Percentage of errors caused by distraction. 
							Lower = stronger focus!
						</p>
					</div>
				</div>
			</div>

			<!-- Interpretation -->
			<div class="interpretation-section">
				<h3>What This Means</h3>
				<p class="feedback-text">{metrics?.feedback || 'Great effort on this task!'}</p>
				
				<div class="insights-list">
					{#if (metrics?.conflict_effect || 0) < 100}
						<div class="insight-item excellent">
							<span class="insight-icon">⭐</span>
							<span>Excellent selective attention! You resist distraction very well.</span>
						</div>
					{:else if (metrics?.conflict_effect || 0) < 150}
						<div class="insight-item good">
							<span class="insight-icon">✓</span>
							<span>Good selective attention. Normal interference effect.</span>
						</div>
					{:else}
						<div class="insight-item needs-work">
							<span class="insight-icon">💡</span>
							<span>High interference - practice focusing on relevant information only.</span>
						</div>
					{/if}

					{#if (metrics?.incongruent_accuracy || 0) > 85}
						<div class="insight-item excellent">
							<span class="insight-icon">🎯</span>
							<span>Strong accuracy on hard trials - excellent conflict resolution!</span>
						</div>
					{/if}

					{#if (metrics?.congruent_mean_rt || 0) < 500 && (metrics?.congruent_mean_rt || 0) > 0}
						<div class="insight-item good">
							<span class="insight-icon">⚡</span>
							<span>Fast processing speed on easy trials!</span>
						</div>
					{/if}
				</div>
			</div>

			<!-- Clinical Context -->
			<div class="clinical-context">
				<h3>📊 Clinical Context</h3>
				<p>
					The <strong>Conflict Effect</strong> (incongruent RT - congruent RT) is the key measure 
					of selective attention. Research shows this reflects anterior cingulate cortex function 
					and executive control networks. Reducing your conflict effect through training indicates 
					improved ability to ignore distractions and focus on relevant information.
				</p>
			</div>

			<!-- Navigation -->
			<div class="button-group">
				<button class="primary-button" on:click={returnToDashboard}>
					Return to Dashboard
				</button>
			</div>
		</div>
	{/if}
</div>

<style>
	.flanker-container {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem;
		min-height: 100vh;
	}

	/* Loading State */
	.loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 60vh;
		gap: 1rem;
	}

	.spinner {
		width: 50px;
		height: 50px;
		border: 4px solid rgba(59, 130, 246, 0.2);
		border-top-color: #3b82f6;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	/* Introduction Screen */
	.instructions {
		max-width: 900px;
		margin: 0 auto;
	}

	h1 {
		font-size: 2.5rem;
		font-weight: 700;
		text-align: center;
		margin-bottom: 1rem;
		background: linear-gradient(135deg, #3b82f6, #8b5cf6);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
	}

	.classic-badge {
		text-align: center;
		background: linear-gradient(135deg, #3b82f6, #8b5cf6);
		color: white;
		padding: 0.5rem 1.5rem;
		border-radius: 2rem;
		display: inline-block;
		margin: 0 auto 2rem;
		font-weight: 600;
		display: block;
		width: fit-content;
		margin-left: auto;
		margin-right: auto;
	}

	.instruction-card {
		background: white;
		border-radius: 1rem;
		padding: 2rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
		margin-bottom: 2rem;
	}

	.task-header h2 {
		font-size: 1.75rem;
		margin-bottom: 1rem;
		color: #1f2937;
	}

	.importance {
		font-size: 1.1rem;
		line-height: 1.6;
		color: #374151;
		margin-bottom: 2rem;
		padding: 1rem;
		background: #eff6ff;
		border-left: 4px solid #3b82f6;
		border-radius: 0.5rem;
	}

	/* Stimulus Examples */
	.stimulus-examples {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.5rem;
		margin: 2rem 0;
	}

	.example-card {
		padding: 1.5rem;
		border-radius: 0.75rem;
		text-align: center;
	}

	.congruent-card {
		background: #d1fae5;
		border: 2px solid #10b981;
	}

	.incongruent-card {
		background: #fee2e2;
		border: 2px solid #ef4444;
	}

	.example-label {
		font-weight: 600;
		font-size: 0.9rem;
		text-transform: uppercase;
		margin-bottom: 1rem;
		color: #374151;
	}

	.arrow-display {
		font-size: 3rem;
		margin: 1rem 0;
		font-weight: bold;
		letter-spacing: 0.5rem;
	}

	.arrow-display.conflict {
		color: #ef4444;
	}

	.example-action {
		font-weight: 600;
		margin-top: 1rem;
		color: #1f2937;
	}

	.example-note {
		font-size: 0.9rem;
		color: #6b7280;
		margin-top: 0.5rem;
	}

	.rule-box {
		background: #fef3c7;
		border: 2px solid #f59e0b;
		border-radius: 0.5rem;
		padding: 1rem;
		margin: 2rem 0;
	}

	/* Info Grid */
	.info-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 2rem;
		margin: 2rem 0;
	}

	.info-section h3 {
		font-size: 1.25rem;
		margin-bottom: 1rem;
		color: #1f2937;
	}

	.steps-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.step-item {
		display: flex;
		align-items: flex-start;
		gap: 1rem;
	}

	.step-num {
		background: #3b82f6;
		color: white;
		width: 2rem;
		height: 2rem;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 700;
		flex-shrink: 0;
	}

	.step-text {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.step-text strong {
		color: #1f2937;
	}

	.step-text span {
		font-size: 0.9rem;
		color: #6b7280;
	}

	.measures-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.measure-item {
		padding: 0.5rem;
		background: #f3f4f6;
		border-radius: 0.5rem;
		font-size: 0.95rem;
	}

	/* Clinical Info */
	.clinical-info {
		margin: 2rem 0;
	}

	.clinical-info h3 {
		font-size: 1.25rem;
		margin-bottom: 1rem;
		color: #1f2937;
	}

	.clinical-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}

	.clinical-item {
		padding: 1rem;
		background: #f9fafb;
		border-radius: 0.5rem;
		border-left: 3px solid #3b82f6;
		font-size: 0.9rem;
	}

	/* Controls Info */
	.controls-info {
		margin: 2rem 0;
	}

	.controls-info h3 {
		font-size: 1.25rem;
		margin-bottom: 1rem;
		color: #1f2937;
	}

	.key-bindings {
		display: flex;
		gap: 2rem;
		justify-content: center;
	}

	.key-bind {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 1.1rem;
	}

	kbd {
		background: #374151;
		color: white;
		padding: 0.5rem 1rem;
		border-radius: 0.375rem;
		font-family: monospace;
		font-weight: 600;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
	}

	/* Button Group */
	.button-group {
		display: flex;
		gap: 1rem;
		justify-content: center;
		margin-top: 2rem;
	}

	.start-button, .primary-button {
		background: linear-gradient(135deg, #3b82f6, #8b5cf6);
		color: white;
		border: none;
		padding: 1rem 2.5rem;
		border-radius: 0.75rem;
		font-size: 1.1rem;
		font-weight: 600;
		cursor: pointer;
		transition: transform 0.2s, box-shadow 0.2s;
	}

	.start-button:hover, .primary-button:hover {
		transform: translateY(-2px);
		box-shadow: 0 8px 16px rgba(59, 130, 246, 0.3);
	}

	.btn-secondary {
		background: #e5e7eb;
		color: #374151;
		border: none;
		padding: 1rem 2rem;
		border-radius: 0.75rem;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: background 0.2s;
	}

	.btn-secondary:hover {
		background: #d1d5db;
	}

	/* Quick Instructions */
	.quick-instructions {
		max-width: 800px;
		margin: 0 auto;
		background: white;
		border-radius: 1rem;
		padding: 2rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
	}

	.quick-instructions h2 {
		text-align: center;
		font-size: 2rem;
		margin-bottom: 2rem;
		color: #1f2937;
	}

	.key-reminder {
		display: flex;
		gap: 2rem;
		justify-content: center;
		margin: 2rem 0;
	}

	.key-display {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}

	.key-large {
		font-size: 2rem;
		padding: 1rem 1.5rem;
	}

	.key-label {
		font-weight: 600;
		color: #6b7280;
	}

	.task-rule {
		text-align: center;
		margin: 2rem 0;
	}

	.rule-emphasis {
		font-size: 1.3rem;
		color: #1f2937;
		padding: 1rem;
		background: #fef3c7;
		border-radius: 0.5rem;
		border: 2px solid #f59e0b;
	}

	.instructions-flow {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		margin: 2rem 0;
		padding: 2rem;
		background: #f9fafb;
		border-radius: 0.75rem;
	}

	.flow-step {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		flex: 1;
	}

	.flow-number {
		background: #3b82f6;
		color: white;
		width: 3rem;
		height: 3rem;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.5rem;
		font-weight: 700;
	}

	.flow-content {
		text-align: center;
	}

	.flow-title {
		font-weight: 600;
		color: #1f2937;
		margin-bottom: 0.25rem;
	}

	.flow-desc {
		font-size: 0.9rem;
		color: #6b7280;
	}

	.flow-arrow {
		font-size: 2rem;
		color: #9ca3af;
		font-weight: bold;
	}

	.example-reminder {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		margin: 2rem 0;
		padding: 1.5rem;
		background: #f3f4f6;
		border-radius: 0.75rem;
	}

	.example-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem;
		background: white;
		border-radius: 0.5rem;
	}

	.example-row.conflict {
		background: #fef2f2;
	}

	.example-stimulus {
		font-size: 1.5rem;
		font-weight: bold;
		letter-spacing: 0.3rem;
	}

	.example-answer {
		font-weight: 600;
		color: #374151;
	}

	.tips-box {
		background: #eff6ff;
		border: 2px solid #3b82f6;
		border-radius: 0.75rem;
		padding: 1.5rem;
		margin: 2rem 0;
	}

	.tips-box h3 {
		margin-bottom: 1rem;
		color: #1f2937;
	}

	.tips-box ul {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.tips-box li {
		padding-left: 1.5rem;
		position: relative;
	}

	.tips-box li::before {
		content: '💡';
		position: absolute;
		left: 0;
	}

	.practice-prompt {
		text-align: center;
		margin-top: 2rem;
	}

	.practice-prompt p {
		font-size: 1.1rem;
		margin-bottom: 1rem;
		color: #374151;
	}

	/* Trial Screen */
	.trial-screen {
		max-width: 1000px;
		margin: 0 auto;
	}

	.trial-header {
		text-align: center;
		margin-bottom: 2rem;
	}

	.trial-header h2 {
		font-size: 1.5rem;
		margin-bottom: 0.5rem;
		color: #1f2937;
	}

	.instruction-reminder {
		color: #6b7280;
		font-size: 1rem;
	}

	.progress-header {
		margin-bottom: 2rem;
	}

	.progress-top {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	.progress-badges {
		display: flex;
		gap: 0.5rem;
	}

	.badge-remaining {
		background: #dbeafe;
		color: #1e40af;
		padding: 0.25rem 0.75rem;
		border-radius: 1rem;
		font-size: 0.9rem;
		font-weight: 600;
	}

	.progress-bar-container {
		width: 100%;
		height: 8px;
		background: #e5e7eb;
		border-radius: 1rem;
		overflow: hidden;
	}

	.progress-bar-fill {
		height: 100%;
		background: linear-gradient(90deg, #3b82f6, #8b5cf6);
		transition: width 0.3s ease;
	}

	/* Stimulus Area */
	.stimulus-area {
		min-height: 400px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: white;
		border-radius: 1rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
		margin-bottom: 2rem;
	}

	.arrow-stimulus {
		font-size: 4rem;
		font-weight: bold;
		letter-spacing: 1rem;
		padding: 2rem;
	}

	.arrow-stimulus.congruent {
		color: #10b981;
	}

	.arrow-stimulus.incongruent {
		color: #ef4444;
	}

	.fixation {
		font-size: 4rem;
		color: #9ca3af;
		font-weight: 300;
	}

	.reminder-text {
		text-align: center;
		color: #6b7280;
		font-size: 1rem;
		margin-top: 1rem;
	}

	/* Feedback */
	.feedback-box {
		margin-top: 2rem;
		padding: 1.5rem;
		border-radius: 0.75rem;
		text-align: center;
		font-size: 1.1rem;
		font-weight: 600;
	}

	.feedback-box.success {
		background: #d1fae5;
		color: #065f46;
		border: 2px solid #10b981;
	}

	.feedback-box.error {
		background: #fee2e2;
		color: #991b1b;
		border: 2px solid #ef4444;
	}

	.feedback-box.warning {
		background: #fef3c7;
		color: #92400e;
		border: 2px solid #f59e0b;
	}

	/* Results Screen */
	.results-container {
		max-width: 1000px;
		margin: 0 auto;
	}

	.results-header {
		text-align: center;
		margin-bottom: 2rem;
	}

	.results-header h2 {
		font-size: 2rem;
		margin-bottom: 1rem;
		color: #1f2937;
	}

	.performance-badge {
		display: inline-block;
		background: linear-gradient(135deg, var(--tw-gradient-stops));
		color: white;
		padding: 0.75rem 2rem;
		border-radius: 2rem;
		font-size: 1.25rem;
		font-weight: 700;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
	}

	/* Metrics Grid */
	.metrics-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1.5rem;
		margin-bottom: 2rem;
	}

	.metric-card {
		background: white;
		border-radius: 0.75rem;
		padding: 1.5rem;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
		text-align: center;
	}

	.metric-label {
		font-size: 0.9rem;
		color: #6b7280;
		margin-bottom: 0.5rem;
		text-transform: uppercase;
		font-weight: 600;
	}

	.metric-value {
		font-size: 2.5rem;
		font-weight: 700;
		color: #1f2937;
		margin-bottom: 0.25rem;
	}

	.metric-detail {
		font-size: 0.9rem;
		color: #9ca3af;
	}

	.accuracy-card {
		border-top: 4px solid #10b981;
	}

	.speed-card {
		border-top: 4px solid #3b82f6;
	}

	.conflict-card {
		border-top: 4px solid #ef4444;
	}

	.attention-card {
		border-top: 4px solid #8b5cf6;
	}

	/* Breakdown Section */
	.breakdown-section {
		margin: 2rem 0;
	}

	.breakdown-section h3 {
		font-size: 1.5rem;
		margin-bottom: 1rem;
		color: #1f2937;
	}

	.breakdown-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.5rem;
	}

	.breakdown-card {
		background: white;
		border-radius: 0.75rem;
		padding: 1.5rem;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
	}

	.breakdown-card.congruent-card {
		border-left: 4px solid #10b981;
		background: linear-gradient(to right, #d1fae5 0%, white 10%);
	}

	.breakdown-card.incongruent-card {
		border-left: 4px solid #ef4444;
		background: linear-gradient(to right, #fee2e2 0%, white 10%);
	}

	.breakdown-title {
		font-size: 1.1rem;
		font-weight: 700;
		margin-bottom: 0.25rem;
		color: #1f2937;
	}

	.breakdown-subtitle {
		font-size: 0.9rem;
		color: #6b7280;
		margin-bottom: 1rem;
	}

	.breakdown-stat {
		display: flex;
		justify-content: space-between;
		padding: 0.5rem 0;
		border-bottom: 1px solid #e5e7eb;
		font-size: 0.95rem;
	}

	.breakdown-stat span {
		font-weight: 600;
		color: #1f2937;
	}

	.breakdown-note {
		margin-top: 1rem;
		font-size: 0.9rem;
		color: #6b7280;
		font-style: italic;
	}

	.breakdown-note.highlight {
		color: #dc2626;
		font-weight: 600;
	}

	/* Interference Section */
	.interference-section {
		margin: 2rem 0;
	}

	.interference-section h3 {
		font-size: 1.5rem;
		margin-bottom: 1rem;
		color: #1f2937;
	}

	.interference-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.5rem;
	}

	.interference-card {
		background: linear-gradient(135deg, #fef3c7, #fef9c3);
		border: 2px solid #f59e0b;
		border-radius: 0.75rem;
		padding: 1.5rem;
		text-align: center;
	}

	.interference-label {
		font-size: 0.9rem;
		font-weight: 600;
		color: #78350f;
		text-transform: uppercase;
		margin-bottom: 0.5rem;
	}

	.interference-value {
		font-size: 2rem;
		font-weight: 700;
		color: #92400e;
		margin-bottom: 0.5rem;
	}

	.interference-desc {
		font-size: 0.9rem;
		color: #78350f;
		line-height: 1.4;
	}

	/* Interpretation Section */
	.interpretation-section {
		background: white;
		border-radius: 0.75rem;
		padding: 2rem;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
		margin: 2rem 0;
	}

	.interpretation-section h3 {
		font-size: 1.5rem;
		margin-bottom: 1rem;
		color: #1f2937;
	}

	.feedback-text {
		font-size: 1.1rem;
		line-height: 1.6;
		color: #374151;
		margin-bottom: 1.5rem;
	}

	.insights-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.insight-item {
		display: flex;
		align-items: flex-start;
		gap: 1rem;
		padding: 1rem;
		border-radius: 0.5rem;
	}

	.insight-item.excellent {
		background: #d1fae5;
		border-left: 4px solid #10b981;
	}

	.insight-item.good {
		background: #dbeafe;
		border-left: 4px solid #3b82f6;
	}

	.insight-item.needs-work {
		background: #fef3c7;
		border-left: 4px solid #f59e0b;
	}

	.insight-icon {
		font-size: 1.5rem;
	}

	/* Clinical Context */
	.clinical-context {
		background: #f9fafb;
		border: 2px solid #e5e7eb;
		border-radius: 0.75rem;
		padding: 1.5rem;
		margin: 2rem 0;
	}

	.clinical-context h3 {
		font-size: 1.25rem;
		margin-bottom: 1rem;
		color: #1f2937;
	}

	.clinical-context p {
		line-height: 1.6;
		color: #374151;
	}

	/* Responsive Design */
	@media (max-width: 768px) {
		.flanker-container {
			padding: 1rem;
		}

		h1 {
			font-size: 2rem;
		}

		.stimulus-examples,
		.info-grid,
		.clinical-grid,
		.breakdown-grid,
		.interference-grid {
			grid-template-columns: 1fr;
		}

		.arrow-display {
			font-size: 2rem;
			letter-spacing: 0.3rem;
		}

		.arrow-stimulus {
			font-size: 2.5rem;
			letter-spacing: 0.5rem;
		}

		.instructions-flow {
			flex-direction: column;
		}

		.flow-arrow {
			transform: rotate(90deg);
		}

		.metrics-grid {
			grid-template-columns: 1fr;
		}
	}
</style>

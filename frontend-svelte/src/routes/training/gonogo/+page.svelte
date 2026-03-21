<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import { formatNumber, locale, translateText } from '$lib/i18n';
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
			const response = await fetch(`${API_BASE_URL}/api/training/tasks/gonogo/generate/${currentUser.id}`, {
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
			alert(
				t(
					'Failed to load training session. Please ensure backend server is running and you have completed baseline assessment.'
				)
			);
			loading = false;
		}
	}

	function startInstructions() {
		phase = 'instructions';
	}

	function t(text) {
		return translateText(text, $locale);
	}

	function formatMilliseconds(value) {
		if ($locale === 'bn') {
			return `${formatNumber(value, $locale)} মিলিসেকেন্ড`;
		}

		return `${formatNumber(value, $locale)}ms`;
	}

	function startPractice() {
		// Create practice trials (4 Go, 2 No-Go)
		practiceTrials = [
			{
				trial_type: 'go',
				stimulus: sessionData.go_stimulus,
				hint: t('Press SPACEBAR when you see this!')
			},
			{
				trial_type: 'go',
				stimulus: sessionData.go_stimulus,
				hint: t('Quick! Press SPACEBAR again')
			},
			{
				trial_type: 'nogo',
				stimulus: sessionData.nogo_stimulus,
				hint: t('DON\'T PRESS! Just wait.')
			},
			{
				trial_type: 'go',
				stimulus: sessionData.go_stimulus,
				hint: t('Press SPACEBAR - be ready!')
			},
			{
				trial_type: 'nogo',
				stimulus: sessionData.nogo_stimulus,
				hint: t('Remember: Don\'t press for this one!')
			},
			{
				trial_type: 'go',
				stimulus: sessionData.go_stimulus,
				hint: t('Last practice - press SPACEBAR!')
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
		clearTimeout(interStimulusTimeout);
		
		if (currentPractice >= practiceTrials.length) {
			// Practice complete
			setTimeout(() => {
				startTest();
			}, 1500);
			return;
		}

		responded = false;
		showStimulus = true;
		startTime = Date.now();

		// Auto-advance after presentation time
		stimulusTimeout = setTimeout(() => {
			if (!responded) {
				handlePracticeResponse(false);
			}
		}, 2000); // 2 seconds for practice
	}

	function handlePracticeResponse(didRespond) {
		clearTimeout(stimulusTimeout);
		
		const trial = practiceTrials[currentPractice];
		const correct = (trial.trial_type === 'go' && didRespond) || 
		                (trial.trial_type === 'nogo' && !didRespond);

		if (correct) {
			if (trial.trial_type === 'go') {
				const rt = Date.now() - startTime;
				practiceFeedback = {
					type: 'success',
					message: `✓ ${t('Correct!')} ${t('Response time')}: ${formatMilliseconds(rt)}. ${trial.hint}`
				};
			} else {
				practiceFeedback = {
					type: 'success',
					message: `✓ ${t('Perfect! You successfully withheld your response.')} ${trial.hint}`
				};
			}
		} else {
			if (trial.trial_type === 'go') {
				practiceFeedback = {
					type: 'error',
					message: `✗ ${t('You should have pressed SPACEBAR.')} ${trial.hint}`
				};
			} else {
				practiceFeedback = {
					type: 'error',
					message: `✗ ${t("You pressed when you shouldn't have!")} ${trial.hint}`
				};
			}
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

		// Inter-stimulus interval
		interStimulusTimeout = setTimeout(() => {
			showStimulus = true;
			startTime = Date.now();

			// Hide stimulus after presentation time
			stimulusTimeout = setTimeout(() => {
				showStimulus = false;

				// If no response yet, record as no response after stimulus disappears
				if (!responded) {
					trialTimeout = setTimeout(() => {
						recordResponse(false);
					}, 200);
				}
			}, sessionData.presentation_time_ms);
		}, sessionData.inter_stimulus_interval_ms);
	}

	function recordResponse(didRespond) {
		if (responded) return; // Already responded
		
		// Clear all timers immediately
		clearTimeout(stimulusTimeout);
		clearTimeout(interStimulusTimeout);
		clearTimeout(trialTimeout);
		
		responded = true;

		const reactionTime = didRespond ? Date.now() - startTime : 0;
		const trial = sessionData.trials[currentTrial];

		responses.push({
			trial_number: trial.trial_number,
			trial_type: trial.trial_type,
			responded: didRespond,
			reaction_time_ms: reactionTime
		});

		currentTrial++;
		showStimulus = false;

		// Brief pause before next trial
		interStimulusTimeout = setTimeout(() => {
			showNextTrial();
		}, 300);
	}

	function handleKeyPress(event) {
		if (event.code === 'Space' || event.key === ' ') {
			event.preventDefault();
			
			if (phase === 'practice' && showStimulus && !responded) {
				responded = true;
				handlePracticeResponse(true);
			} else if (phase === 'test' && showStimulus && !responded) {
				recordResponse(true);
			}
		}
	}

	async function completeSession() {
		try {
			taskId = $page.url.searchParams.get('taskId');
			const response = await fetch(`${API_BASE_URL}/api/training/tasks/gonogo/submit/${currentUser.id}`, {
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
			alert(t('Failed to submit results. Please try again.'));
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
</script>

<svelte:window on:keydown={handleKeyPress} />

<div class="gonogo-container">
	{#if loading}
		<div class="loading">
			<div class="spinner"></div>
			<p>Loading task...</p>
		</div>
	{:else if phase === 'intro'}
		<!-- Introduction Screen -->
		<div class="instructions">
			<div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap;">
				<h1>⚡ Go/No-Go Task</h1>
				<DifficultyBadge {difficulty} domain="Attention" />
			</div>
			<div class="classic-badge">Response Inhibition & Impulse Control Test</div>
			
			<div class="instruction-card">
				<div class="task-header">
					<h2>💡 Your Mission: Respond Fast, But Not Always!</h2>
				</div>
				
				<p class="importance">
					This task measures your ability to <strong>control impulses</strong> - a critical executive function. 
					You'll need to respond quickly to targets while <strong>withholding responses</strong> to non-targets.
				</p>
				
				<!-- Visual Examples -->
				<div class="stimulus-examples">
					<div class="example-card go-card">
						<div class="example-label">GO Trial (75%)</div>
						<div class="stimulus-display go-stimulus">{sessionData.go_stimulus}</div>
						<div class="example-action">✓ PRESS SPACEBAR</div>
						<div class="example-note">Respond as quickly as possible!</div>
					</div>
					
					<div class="example-card nogo-card">
						<div class="example-label">NO-GO Trial (25%)</div>
						<div class="stimulus-display nogo-stimulus">{sessionData.nogo_stimulus}</div>
						<div class="example-action">✋ DON'T PRESS</div>
						<div class="example-note">Resist the urge to respond!</div>
					</div>
				</div>
				
				<div class="rule-box">
					<strong>⚡ The Challenge:</strong>
					Most trials require a response, creating a habit. You must <strong>inhibit</strong> this automatic 
					response when you see the NO-GO stimulus. This tests impulse control!
				</div>
				
				<!-- Two Column Layout -->
				<div class="info-grid">
					<div class="info-section">
						<h3>📋 What You'll Do</h3>
						<div class="steps-list">
							<div class="step-item">
								<span class="step-num">1</span>
								<div class="step-text">
									<strong>Watch the screen</strong>
									<span>Stimuli appear briefly</span>
								</div>
							</div>
							<div class="step-item">
								<span class="step-num">2</span>
								<div class="step-text">
									<strong>Identify quickly</strong>
									<span>Is it GO or NO-GO?</span>
								</div>
							</div>
							<div class="step-item">
								<span class="step-num">3</span>
								<div class="step-text">
									<strong>Respond or withhold</strong>
									<span>Press or don't press</span>
								</div>
							</div>
						</div>
					</div>
					
					<div class="info-section">
						<h3>💪 What It Measures</h3>
						<div class="measures-list">
							<div class="measure-item">✓ <strong>Response Speed:</strong> Go trial reaction time</div>
							<div class="measure-item">✓ <strong>Impulse Control:</strong> No-Go accuracy</div>
							<div class="measure-item">✓ <strong>Sustained Attention:</strong> Consistency</div>
							<div class="measure-item">✓ <strong>Executive Function:</strong> Inhibition ability</div>
						</div>
					</div>
				</div>
				
				<!-- Clinical Context -->
				<div class="clinical-info">
					<h3>📚 Clinical Significance</h3>
					<div class="clinical-grid">
						<div class="clinical-item">
							<strong>🎯 Standard Test:</strong> Used in ADHD, frontal lobe, and MS assessment
						</div>
						<div class="clinical-item">
							<strong>🧠 Brain Regions:</strong> Tests prefrontal cortex function
						</div>
						<div class="clinical-item">
							<strong>🏥 MS Relevance:</strong> Sensitive to attention deficits and executive dysfunction
						</div>
						<div class="clinical-item">
							<strong>📈 Training Benefits:</strong> Improves real-world impulse control
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
				<div class="key-icon">SPACEBAR</div>
				<p>Press <strong>SPACEBAR</strong> when you see: <span class="inline-stimulus">{sessionData.go_stimulus}</span></p>
				<p><strong>DON'T PRESS</strong> when you see: <span class="inline-stimulus nogo">{sessionData.nogo_stimulus}</span></p>
			</div>

			<div class="instructions-flow">
				<div class="flow-step">
					<div class="flow-number">1</div>
					<div class="flow-content">
						<p class="flow-title">Stimulus Appears</p>
						<p class="flow-desc">A symbol flashes on screen briefly</p>
					</div>
				</div>

				<div class="flow-arrow">→</div>

				<div class="flow-step">
					<div class="flow-number">2</div>
					<div class="flow-content">
						<p class="flow-title">Identify It</p>
						<p class="flow-desc">Is it GO or NO-GO?</p>
					</div>
				</div>

				<div class="flow-arrow">→</div>

				<div class="flow-step">
					<div class="flow-number">3</div>
					<div class="flow-content">
						<p class="flow-title">Respond or Wait</p>
						<p class="flow-desc">Press SPACEBAR or withhold</p>
					</div>
				</div>
			</div>

			<div class="tips-box">
				<h3>💡 Success Tips</h3>
				<ul>
					<li><strong>Stay focused</strong> - Stimuli appear quickly</li>
					<li><strong>Be ready</strong> - Most trials are GO trials</li>
					<li><strong>Control impulses</strong> - Resist pressing on NO-GO trials</li>
					<li><strong>Speed matters</strong> - Respond quickly to GO trials</li>
				</ul>
			</div>

			<div class="practice-prompt">
				<p>Let's practice with 6 trials to get comfortable...</p>
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
				<p class="instruction-reminder">Press SPACEBAR for GO ({sessionData.go_stimulus}), withhold for NO-GO ({sessionData.nogo_stimulus})</p>
			</div>

			<!-- Stimulus Display -->
			<div class="stimulus-area">
				{#if showStimulus}
					<div class="stimulus-large" class:go={practiceTrials[currentPractice].trial_type === 'go'} class:nogo={practiceTrials[currentPractice].trial_type === 'nogo'}>
						{practiceTrials[currentPractice].stimulus}
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
					<div class="stimulus-xlarge">
						{sessionData.trials[currentTrial].stimulus}
					</div>
				{:else}
					<div class="fixation">+</div>
				{/if}
			</div>

			<div class="reminder-text">
				Press SPACEBAR for {sessionData.go_stimulus} | Don't press for {sessionData.nogo_stimulus}
			</div>
		</div>

	{:else if phase === 'results'}
		<!-- Results Screen -->
		<div class="results-container">
			<div class="results-header">
				<h2>Go/No-Go Task Complete!</h2>
				<div class="performance-badge {performanceBadgeColor}">
					{metrics.performance_level}
				</div>
			</div>

			<!-- Key Metrics Grid -->
			<div class="metrics-grid">
				<!-- Overall Accuracy -->
				<div class="metric-card accuracy-card">
					<div class="metric-label">Overall Accuracy</div>
					<div class="metric-value">{metrics.overall_accuracy.toFixed(1)}%</div>
					<div class="metric-detail">{metrics.total_correct}/{metrics.total_trials} correct</div>
				</div>

				<!-- Go Trial Speed -->
				<div class="metric-card speed-card">
					<div class="metric-label">Go Trial Speed</div>
					<div class="metric-value">{metrics.go_mean_rt.toFixed(0)} ms</div>
					<div class="metric-detail">Processing speed</div>
				</div>

				<!-- No-Go Accuracy -->
				<div class="metric-card inhibition-card">
					<div class="metric-label">Inhibition Control</div>
					<div class="metric-value">{metrics.nogo_accuracy.toFixed(1)}%</div>
					<div class="metric-detail">No-Go accuracy</div>
				</div>

				<!-- d-prime -->
				<div class="metric-card dprime-card">
					<div class="metric-label">d-prime (Sensitivity)</div>
					<div class="metric-value">{metrics.d_prime.toFixed(2)}</div>
					<div class="metric-detail">Signal detection</div>
				</div>
			</div>

			<!-- Trial Type Breakdown -->
			<div class="breakdown-section">
				<h3>Performance by Trial Type</h3>
				<div class="breakdown-grid">
					<!-- Go Trials -->
					<div class="breakdown-card go-card">
						<p class="breakdown-title">GO Trials ({sessionData.go_trials} trials)</p>
						<p class="breakdown-stat">Hits: <span>{metrics.go_hits}</span></p>
						<p class="breakdown-stat">Misses: <span>{metrics.go_misses}</span></p>
						<p class="breakdown-stat">Accuracy: <span>{metrics.go_accuracy.toFixed(1)}%</span></p>
						<p class="breakdown-stat">Mean RT: <span>{metrics.go_mean_rt.toFixed(0)} ms</span></p>
						<p class="breakdown-note">Tests processing speed & attention</p>
					</div>

					<!-- No-Go Trials -->
					<div class="breakdown-card nogo-card">
						<p class="breakdown-title">NO-GO Trials ({sessionData.nogo_trials} trials)</p>
						<p class="breakdown-stat">Correct Withholds: <span>{metrics.nogo_correct}</span></p>
						<p class="breakdown-stat">Commission Errors: <span class="error-count">{metrics.nogo_commission_errors}</span></p>
						<p class="breakdown-stat">Accuracy: <span>{metrics.nogo_accuracy.toFixed(1)}%</span></p>
						<p class="breakdown-stat">Hit Rate: <span>{metrics.hit_rate.toFixed(1)}%</span></p>
						<p class="breakdown-note success">Tests impulse control & inhibition</p>
					</div>
				</div>
			</div>

			<!-- Interpretation -->
			<div class="interpretation-section">
				<h3>What This Means</h3>
				<p class="feedback-text">{metrics.feedback}</p>
				
				<div class="insights-list">
					{#if metrics.nogo_accuracy >= 90}
						<p class="insight success">
							✓ <strong>Excellent inhibitory control:</strong> You successfully withheld responses on NO-GO trials
						</p>
					{:else if metrics.nogo_accuracy >= 75}
						<p class="insight good">
							✓ <strong>Good impulse control:</strong> Managing inhibition effectively
						</p>
					{:else if metrics.nogo_accuracy >= 60}
						<p class="insight moderate">
							⚡ <strong>Moderate inhibition:</strong> Room for improvement in impulse control
						</p>
					{:else}
						<p class="insight high">
							⚡ <strong>Challenging inhibition:</strong> Practice will strengthen impulse control
						</p>
					{/if}

					{#if metrics.go_mean_rt < 400}
						<p class="insight success">
							✓ <strong>Fast processing speed:</strong> Quick reactions to GO trials
						</p>
					{:else if metrics.go_mean_rt < 600}
						<p class="insight good">
							✓ <strong>Good response speed:</strong> Adequate processing time
						</p>
					{:else}
						<p class="insight moderate">
							⚡ <strong>Slower responses:</strong> Practice can improve speed
						</p>
					{/if}

					{#if metrics.d_prime >= 2.0}
						<p class="insight success">
							✓ <strong>High sensitivity:</strong> Excellent discrimination between GO and NO-GO
						</p>
					{:else if metrics.d_prime >= 1.0}
						<p class="insight good">
							✓ <strong>Good discrimination:</strong> Solid signal detection ability
						</p>
					{/if}
				</div>
			</div>

			<!-- Clinical Context -->
			<div class="clinical-context">
				<h3>About the Go/No-Go Task</h3>
				<div class="clinical-content">
					<p>
						<strong>Response Inhibition</strong> is a core executive function that allows you to control 
						impulsive responses. This task measures your ability to withhold prepotent (automatic) responses.
					</p>
					<p>
						<strong>For MS:</strong> Go/No-Go tasks are sensitive to frontal lobe dysfunction and attention 
						deficits. Regular practice can strengthen inhibitory control circuits in the prefrontal cortex.
					</p>
					<p>
						<strong>Real-World Impact:</strong> Better impulse control relates to improved decision-making, 
						safer driving, and better emotional regulation in daily life.
					</p>
					<p>
						<strong>d-prime (d'):</strong> This signal detection metric measures your ability to discriminate 
						between targets and non-targets, independent of response bias. Higher values indicate better discrimination.
					</p>
				</div>
			</div>

			<!-- Difficulty Adaptation -->
			{#if metrics.difficulty_after !== difficulty}
				<div class="difficulty-change">
					<p>
						<strong>Difficulty Adjusted:</strong> Level {difficulty} → Level {metrics.difficulty_after}
					</p>
				</div>
			{/if}

			<!-- New Badges -->
			{#if newBadges.length > 0}
				<div class="badges-section">
					<h3>New Badges Earned!</h3>
					<BadgeNotification badges={newBadges} />
				</div>
			{/if}

			<!-- Actions -->
			<div class="results-actions">
				<button on:click={returnToDashboard} class="return-button">
					Return to Dashboard
				</button>
			</div>
		</div>
	{/if}

	<!-- Help Button -->
	{#if phase !== 'results'}
		<button on:click={() => showHelp = true} class="help-button" aria-label="Help">
			?
		</button>
	{/if}

	<!-- Help Modal -->
	{#if showHelp}
		<div class="modal-overlay" on:click={() => showHelp = false} on:keydown={(e) => e.key === 'Escape' && (showHelp = false)} role="button" aria-label="Close help dialog" tabindex="0">
			<div class="modal-content" on:click|stopPropagation on:keydown={(e) => e.stopPropagation()} role="document" tabindex="0">
				<h2 class="modal-title">Go/No-Go Task Help</h2>

				<div class="help-sections">
					<div class="help-section">
						<h3>What is the Go/No-Go Task?</h3>
						<p>
							A widely-used test of response inhibition and impulse control. It measures your ability to 
							suppress automatic responses when appropriate.
						</p>
					</div>

					<div class="help-section">
						<h3>Why Is It Used in MS?</h3>
						<ul>
							<li>Tests executive function and frontal lobe integrity</li>
							<li>Measures sustained attention and vigilance</li>
							<li>Sensitive to cognitive slowing and inhibition deficits</li>
							<li>Predicts real-world functional outcomes</li>
						</ul>
					</div>

					<div class="help-section">
						<h3>Understanding Your Metrics</h3>
						<div class="metrics-explain">
							<p><strong>Go Trial Speed:</strong> How quickly you respond to target stimuli</p>
							<p><strong>No-Go Accuracy:</strong> Your ability to withhold inappropriate responses</p>
							<p><strong>Commission Errors:</strong> False alarms - pressing when you shouldn't</p>
							<p><strong>d-prime:</strong> Signal detection sensitivity - higher is better</p>
						</div>
					</div>

					<div class="help-section">
						<h3>Tips for Success</h3>
						<ul>
							<li>Keep your finger ready over SPACEBAR</li>
							<li>Focus on the center of the screen</li>
							<li>Don't anticipate - wait to see the stimulus</li>
							<li>Resist the urge to press on NO-GO trials</li>
							<li>Stay alert throughout - consistency matters</li>
						</ul>
					</div>
				</div>

				<button on:click={() => showHelp = false} class="modal-close-btn">
					Close
				</button>
			</div>
		</div>
	{/if}
</div>

<style>
	.gonogo-container {
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(147, 51, 234, 0.05) 100%);
		min-height: 100vh;
		padding: 2rem 1rem;
	}

	.loading {
		background: white;
		padding: 3rem;
		border-radius: 16px;
		text-align: center;
		max-width: 400px;
		margin: 0 auto;
		box-shadow: 0 8px 32px rgba(0,0,0,0.1);
	}

	.spinner {
		width: 50px;
		height: 50px;
		border: 4px solid #f3f3f3;
		border-top: 4px solid #3b82f6;
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin: 0 auto 1rem auto;
	}

	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	.instructions {
		background: white;
		border-radius: 16px;
		padding: 2.5rem 2rem;
		max-width: 1000px;
		margin: 0 auto;
		box-shadow: 0 8px 32px rgba(0,0,0,0.15);
	}

	.instructions h1 {
		text-align: center;
		color: #3b82f6;
		font-size: 2.5rem;
		margin-bottom: 1rem;
	}

	.classic-badge {
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(147, 51, 234, 0.15));
		color: #3b82f6;
		padding: 0.75rem 1.5rem;
		border-radius: 25px;
		text-align: center;
		font-weight: 600;
		margin: 0 auto 2rem auto;
		max-width: fit-content;
		display: block;
	}

	.instruction-card {
		background: #f8f9fa;
		padding: 2rem;
		border-radius: 12px;
		margin-bottom: 2rem;
	}

	.task-header h2 {
		color: #2c3e50;
		margin-bottom: 1rem;
		font-size: 1.8rem;
		text-align: center;
	}

	.importance {
		font-size: 1.1rem;
		line-height: 1.7;
		color: #555;
		margin-bottom: 2rem;
		text-align: center;
	}

	.importance strong {
		color: #3b82f6;
	}

	/* Stimulus Examples */
	.stimulus-examples {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: 1.5rem;
		margin: 2rem 0;
	}

	.example-card {
		background: white;
		padding: 1.5rem;
		border-radius: 12px;
		text-align: center;
		box-shadow: 0 4px 12px rgba(0,0,0,0.08);
	}

	.example-card.go-card {
		border: 3px solid #10b981;
	}

	.example-card.nogo-card {
		border: 3px solid #ef4444;
	}

	.example-label {
		font-size: 0.75rem;
		font-weight: bold;
		color: #666;
		margin-bottom: 1rem;
		text-transform: uppercase;
	}

	.stimulus-display {
		font-size: 4rem;
		font-weight: bold;
		margin: 1rem 0;
		min-height: 100px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.stimulus-display.go-stimulus {
		color: #10b981;
	}

	.stimulus-display.nogo-stimulus {
		color: #ef4444;
	}

	.example-action {
		font-size: 1.1rem;
		font-weight: 700;
		margin: 1rem 0;
	}

	.go-card .example-action {
		color: #10b981;
	}

	.nogo-card .example-action {
		color: #ef4444;
	}

	.example-note {
		font-size: 0.9rem;
		color: #666;
		font-style: italic;
	}

	/* Rule Box */
	.rule-box {
		background: #fef3c7;
		border-left: 4px solid #f59e0b;
		padding: 1.25rem;
		border-radius: 8px;
		margin: 2rem 0;
		color: #92400e;
		line-height: 1.6;
	}

	.rule-box strong {
		font-size: 1.1rem;
		display: block;
		margin-bottom: 0.5rem;
	}

	/* Info Grid */
	.info-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: 1.5rem;
		margin: 2rem 0;
	}

	.info-section {
		background: white;
		padding: 1.5rem;
		border-radius: 12px;
		border: 2px solid #e5e7eb;
	}

	.info-section h3 {
		color: #2c3e50;
		font-size: 1.2rem;
		margin-bottom: 1rem;
	}

	/* Steps List */
	.steps-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.step-item {
		display: flex;
		align-items: center;
		gap: 1rem;
		background: #f8f9fa;
		padding: 1rem;
		border-radius: 8px;
	}

	.step-num {
		width: 40px;
		height: 40px;
		background: linear-gradient(135deg, #3b82f6 0%, #9333ea 100%);
		color: white;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.3rem;
		font-weight: bold;
		flex-shrink: 0;
	}

	.step-text {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.step-text strong {
		font-size: 1rem;
		color: #2c3e50;
	}

	.step-text span {
		font-size: 0.875rem;
		color: #666;
	}

	/* Measures List */
	.measures-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.measure-item {
		background: #eff6ff;
		padding: 0.75rem 1rem;
		border-radius: 8px;
		color: #1e40af;
		font-size: 0.95rem;
		line-height: 1.5;
	}

	/* Clinical Info */
	.clinical-info {
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.08), rgba(147, 51, 234, 0.08));
		padding: 1.5rem;
		border-radius: 12px;
		margin-top: 1.5rem;
	}

	.clinical-info h3 {
		color: #3b82f6;
		margin-bottom: 1rem;
		font-size: 1.1rem;
	}

	.clinical-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		gap: 0.75rem;
	}

	.clinical-item {
		background: white;
		padding: 0.875rem;
		border-radius: 8px;
		font-size: 0.9rem;
		line-height: 1.5;
		color: #555;
	}

	.clinical-item strong {
		color: #3b82f6;
		display: block;
		margin-bottom: 0.25rem;
	}

	/* Buttons */
	.button-group {
		display: flex;
		gap: 1rem;
		justify-content: center;
		margin-top: 2rem;
		flex-wrap: wrap;
	}

	.start-button {
		background: linear-gradient(135deg, #3b82f6 0%, #9333ea 100%);
		color: white;
		border: none;
		padding: 1.25rem 3rem;
		font-size: 1.2rem;
		font-weight: bold;
		border-radius: 12px;
		cursor: pointer;
		transition: all 0.3s;
		box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
	}

	.start-button:hover {
		transform: translateY(-3px);
		box-shadow: 0 6px 25px rgba(59, 130, 246, 0.6);
	}

	.btn-secondary {
		background: #f3f4f6;
		color: #4b5563;
		border: none;
		padding: 1.25rem 2.5rem;
		font-size: 1.1rem;
		font-weight: 600;
		border-radius: 12px;
		cursor: pointer;
		transition: all 0.3s;
	}

	.btn-secondary:hover {
		background: #e5e7eb;
		transform: translateY(-2px);
	}

	/* Quick Instructions */
	.quick-instructions {
		background: white;
		border-radius: 16px;
		padding: 2.5rem 2rem;
		max-width: 800px;
		margin: 0 auto;
		box-shadow: 0 8px 32px rgba(0,0,0,0.15);
	}

	.quick-instructions h2 {
		text-align: center;
		color: #3b82f6;
		font-size: 2rem;
		margin-bottom: 2rem;
	}

	.key-reminder {
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(147, 51, 234, 0.1));
		padding: 1.5rem;
		border-radius: 12px;
		text-align: center;
		margin-bottom: 2rem;
	}

	.key-icon {
		display: inline-block;
		background: #3b82f6;
		color: white;
		padding: 0.75rem 1.5rem;
		border-radius: 8px;
		font-size: 1.2rem;
		font-weight: bold;
		margin-bottom: 1rem;
	}

	.key-reminder p {
		font-size: 1.1rem;
		color: #2c3e50;
		margin: 0.5rem 0;
	}

	.inline-stimulus {
		display: inline-block;
		font-size: 1.5rem;
		font-weight: bold;
		color: #10b981;
		padding: 0.25rem 0.75rem;
		background: rgba(16, 185, 129, 0.1);
		border-radius: 6px;
	}

	.inline-stimulus.nogo {
		color: #ef4444;
		background: rgba(239, 68, 68, 0.1);
	}

	.instructions-flow {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		margin: 2rem 0;
		flex-wrap: wrap;
	}

	.flow-step {
		background: #f8f9fa;
		padding: 1.5rem;
		border-radius: 12px;
		min-width: 180px;
		text-align: center;
	}

	.flow-number {
		width: 50px;
		height: 50px;
		background: linear-gradient(135deg, #3b82f6 0%, #9333ea 100%);
		color: white;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.8rem;
		font-weight: bold;
		margin: 0 auto 1rem auto;
	}

	.flow-title {
		font-size: 1.1rem;
		font-weight: 700;
		color: #2c3e50;
		margin-bottom: 0.5rem;
	}

	.flow-desc {
		font-size: 0.9rem;
		color: #666;
		margin: 0;
	}

	.flow-arrow {
		font-size: 2rem;
		color: #3b82f6;
		font-weight: bold;
	}

	.tips-box {
		background: #ecfdf5;
		border-left: 4px solid #10b981;
		padding: 1.5rem;
		border-radius: 12px;
		margin: 2rem 0;
	}

	.tips-box h3 {
		color: #065f46;
		margin-bottom: 1rem;
	}

	.tips-box ul {
		list-style: none;
		padding: 0;
		margin: 0;
	}

	.tips-box li {
		padding: 0.5rem 0;
		color: #047857;
		font-size: 0.95rem;
	}

	.tips-box li strong {
		color: #064e3b;
	}

	.practice-prompt {
		text-align: center;
		margin-top: 2rem;
	}

	.practice-prompt p {
		font-size: 1.1rem;
		color: #555;
		margin-bottom: 1.5rem;
	}

	/* Trial Screen */
	.trial-screen {
		background: white;
		border-radius: 16px;
		padding: 2rem;
		max-width: 900px;
		margin: 0 auto;
		box-shadow: 0 8px 32px rgba(0,0,0,0.15);
	}

	.trial-header {
		text-align: center;
		margin-bottom: 2rem;
	}

	.trial-header h2 {
		color: #2c3e50;
		font-size: 1.5rem;
		margin-bottom: 0.5rem;
	}

	.instruction-reminder {
		color: #666;
		font-size: 0.95rem;
		margin-top: 0.5rem;
	}

	.progress-header {
		text-align: center;
		margin-bottom: 2rem;
	}

	.progress-top {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		flex-wrap: wrap;
		gap: 1rem;
	}

	.progress-top h2 {
		color: #2c3e50;
		font-size: 1.5rem;
		margin: 0;
	}

	.progress-badges {
		display: flex;
		gap: 0.75rem;
	}

	.badge-remaining {
		background: #dbeafe;
		color: #1e40af;
		padding: 0.5rem 1rem;
		border-radius: 20px;
		font-size: 0.875rem;
		font-weight: 600;
	}

	.progress-bar-container {
		width: 100%;
		height: 10px;
		background: #e5e7eb;
		border-radius: 10px;
		overflow: hidden;
	}

	.progress-bar-fill {
		height: 100%;
		background: linear-gradient(90deg, #3b82f6 0%, #9333ea 100%);
		transition: width 0.3s ease;
	}

	.stimulus-area {
		min-height: 350px;
		display: flex;
		align-items: center;
		justify-content: center;
		margin: 2rem 0;
	}

	.stimulus-large {
		font-size: 8rem;
		font-weight: 900;
		text-shadow: 3px 3px 6px rgba(0,0,0,0.1);
	}

	.stimulus-large.go {
		color: #10b981;
	}

	.stimulus-large.nogo {
		color: #ef4444;
	}

	.stimulus-xlarge {
		font-size: 10rem;
		font-weight: 900;
		text-shadow: 3px 3px 6px rgba(0,0,0,0.1);
		color: #3b82f6;
	}

	.fixation {
		font-size: 5rem;
		color: #d1d5db;
		font-weight: bold;
	}

	.reminder-text {
		text-align: center;
		color: #666;
		font-size: 1rem;
		margin-top: 2rem;
	}

	.feedback-box {
		margin-top: 2rem;
		padding: 1.5rem;
		border-radius: 12px;
		text-align: center;
		font-size: 1.1rem;
		font-weight: 600;
		animation: fadeIn 0.3s ease;
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

	@keyframes fadeIn {
		from {
			opacity: 0;
			transform: translateY(-10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	/* Results Page */
	.results-container {
		background: white;
		border-radius: 16px;
		padding: 2.5rem 2rem;
		max-width: 1100px;
		margin: 0 auto;
		box-shadow: 0 8px 32px rgba(0,0,0,0.15);
	}

	.results-header {
		text-align: center;
		margin-bottom: 2.5rem;
	}

	.results-header h2 {
		font-size: 2.5rem;
		font-weight: bold;
		color: #2c3e50;
		margin-bottom: 1.5rem;
	}

	.performance-badge {
		display: inline-block;
		padding: 1rem 2rem;
		border-radius: 50px;
		font-size: 1.3rem;
		font-weight: bold;
		color: white;
		box-shadow: 0 4px 15px rgba(0,0,0,0.2);
	}

	.performance-badge.from-green-500 {
		background: linear-gradient(135deg, #10b981 0%, #059669 100%);
	}

	.performance-badge.from-blue-500 {
		background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
	}

	.performance-badge.from-yellow-500 {
		background: linear-gradient(135deg, #eab308 0%, #f59e0b 100%);
	}

	.performance-badge.from-gray-500 {
		background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
	}

	/* Metrics Grid */
	.metrics-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		gap: 1.25rem;
		margin-bottom: 2.5rem;
	}

	.metric-card {
		padding: 1.5rem;
		border-radius: 12px;
		border: 2px solid;
		box-shadow: 0 4px 12px rgba(0,0,0,0.08);
	}

	.accuracy-card {
		background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.1));
		border-color: #10b981;
	}

	.speed-card {
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(37, 99, 235, 0.1));
		border-color: #3b82f6;
	}

	.inhibition-card {
		background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(220, 38, 38, 0.1));
		border-color: #ef4444;
	}

	.dprime-card {
		background: linear-gradient(135deg, rgba(147, 51, 234, 0.1), rgba(126, 34, 206, 0.1));
		border-color: #9333ea;
	}

	.metric-label {
		font-size: 0.9rem;
		font-weight: 600;
		color: #555;
		margin-bottom: 0.5rem;
	}

	.metric-value {
		font-size: 2.5rem;
		font-weight: bold;
		color: #2c3e50;
		margin-bottom: 0.25rem;
	}

	.metric-detail {
		font-size: 0.8rem;
		color: #666;
	}

	/* Breakdown Section */
	.breakdown-section {
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.08), rgba(147, 51, 234, 0.08));
		padding: 1.5rem;
		border-radius: 12px;
		margin-bottom: 2rem;
	}

	.breakdown-section h3 {
		font-size: 1.2rem;
		font-weight: 700;
		color: #2c3e50;
		margin-bottom: 1.25rem;
	}

	.breakdown-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: 1rem;
	}

	.breakdown-card {
		background: white;
		padding: 1.25rem;
		border-radius: 10px;
		border: 2px solid;
	}

	.breakdown-card.go-card {
		border-color: #10b981;
	}

	.breakdown-card.nogo-card {
		border-color: #ef4444;
	}

	.breakdown-title {
		font-weight: 700;
		color: #2c3e50;
		margin-bottom: 0.75rem;
		font-size: 1rem;
	}

	.breakdown-stat {
		font-size: 0.9rem;
		color: #555;
		margin-bottom: 0.5rem;
	}

	.breakdown-stat span {
		font-weight: 700;
	}

	.breakdown-stat .error-count {
		color: #ef4444;
	}

	.breakdown-note {
		font-size: 0.85rem;
		color: #666;
		margin-top: 0.75rem;
		font-style: italic;
	}

	.breakdown-note.success {
		color: #059669;
		font-weight: 600;
	}

	/* Interpretation Section */
	.interpretation-section {
		background: white;
		border: 2px solid #3b82f6;
		border-radius: 12px;
		padding: 1.5rem;
		margin-bottom: 2rem;
	}

	.interpretation-section h3 {
		font-size: 1.2rem;
		font-weight: 700;
		color: #2c3e50;
		margin-bottom: 1rem;
	}

	.feedback-text {
		color: #555;
		line-height: 1.6;
		margin-bottom: 1.5rem;
		font-size: 1.05rem;
	}

	.insights-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.insight {
		font-size: 0.95rem;
		line-height: 1.5;
	}

	.insight.success {
		color: #059669;
	}

	.insight.good {
		color: #2563eb;
	}

	.insight.moderate {
		color: #ca8a04;
	}

	.insight.high {
		color: #ea580c;
	}

	/* Clinical Context */
	.clinical-context {
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.08), rgba(147, 51, 234, 0.08));
		padding: 1.5rem;
		border-radius: 12px;
		margin-bottom: 2rem;
	}

	.clinical-context h3 {
		font-size: 1.1rem;
		font-weight: 700;
		color: #2c3e50;
		margin-bottom: 1rem;
	}

	.clinical-content {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.clinical-content p {
		font-size: 0.9rem;
		color: #555;
		line-height: 1.6;
	}

	/* Difficulty Change */
	.difficulty-change {
		background: #dbeafe;
		border-left: 4px solid #3b82f6;
		padding: 1rem;
		border-radius: 8px;
		margin-bottom: 1.5rem;
	}

	.difficulty-change p {
		font-size: 0.9rem;
		color: #1e3a8a;
		margin: 0;
	}

	/* Badges Section */
	.badges-section {
		margin-bottom: 2rem;
	}

	.badges-section h3 {
		font-size: 1.2rem;
		font-weight: 700;
		color: #2c3e50;
		margin-bottom: 1rem;
	}

	/* Results Actions */
	.results-actions {
		display: flex;
		justify-content: center;
		gap: 1rem;
		margin-top: 2rem;
	}

	.return-button {
		background: linear-gradient(135deg, #3b82f6 0%, #9333ea 100%);
		color: white;
		padding: 1.25rem 3rem;
		font-size: 1.1rem;
		font-weight: 700;
		border: none;
		border-radius: 12px;
		cursor: pointer;
		transition: all 0.3s;
		box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
	}

	.return-button:hover {
		transform: translateY(-3px);
		box-shadow: 0 6px 25px rgba(59, 130, 246, 0.6);
	}

	/* Help Button */
	.help-button {
		position: fixed;
		bottom: 2rem;
		right: 2rem;
		width: 56px;
		height: 56px;
		background: #3b82f6;
		color: white;
		border: none;
		border-radius: 50%;
		font-size: 2rem;
		cursor: pointer;
		box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
		transition: all 0.3s;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.help-button:hover {
		background: #2563eb;
		transform: scale(1.1);
	}

	/* Modal */
	.modal-overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 1rem;
		z-index: 1000;
	}

	.modal-content {
		background: white;
		border-radius: 16px;
		padding: 2rem;
		max-width: 650px;
		max-height: 90vh;
		overflow-y: auto;
		box-shadow: 0 10px 40px rgba(0,0,0,0.3);
	}

	.modal-title {
		font-size: 1.8rem;
		font-weight: bold;
		color: #2c3e50;
		margin-bottom: 1.5rem;
	}

	.help-sections {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.help-section h3 {
		font-size: 1.1rem;
		font-weight: 700;
		color: #2c3e50;
		margin-bottom: 0.75rem;
	}

	.help-section p {
		color: #555;
		line-height: 1.6;
	}

	.help-section ul {
		list-style: disc;
		padding-left: 1.5rem;
		color: #555;
	}

	.help-section li {
		margin-bottom: 0.5rem;
		line-height: 1.5;
	}

	.metrics-explain {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.metrics-explain p {
		font-size: 0.95rem;
	}

	.modal-close-btn {
		margin-top: 1.5rem;
		width: 100%;
		padding: 1rem 1.5rem;
		background: #3b82f6;
		color: white;
		border: none;
		border-radius: 12px;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s;
	}

	.modal-close-btn:hover {
		background: #2563eb;
	}

	/* Responsive */
	@media (max-width: 768px) {
		.instructions {
			padding: 1.5rem 1rem;
		}

		.instructions h1 {
			font-size: 2rem;
		}

		.stimulus-examples {
			grid-template-columns: 1fr;
		}

		.info-grid {
			grid-template-columns: 1fr;
		}

		.stimulus-large {
			font-size: 5rem;
		}

		.stimulus-xlarge {
			font-size: 6rem;
		}

		.flow-arrow {
			transform: rotate(90deg);
		}
	}
</style>

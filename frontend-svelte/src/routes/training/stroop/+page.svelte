<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';

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

	// Practice state
	let practiceTrials = [];
	let currentPractice = 0;
	let practiceFeedback = null;

	// Test state
	let startTime = 0;
	let userAnswer = '';
	let showStimulus = true;
	let trialTimeout = null;
	let responseTimeout = null;

	// Color mapping for display
	const COLOR_MAP = {
		red: '#dc2626',
		blue: '#2563eb',
		green: '#16a34a',
		yellow: '#eab308',
		purple: '#9333ea',
		orange: '#ea580c'
	};

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
			const response = await fetch(`${API_BASE_URL}/training/tasks/stroop/generate/${currentUser.id}`, {
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
		if (!sessionData || !sessionData.colors) {
			alert('Session data not loaded. Please refresh the page.');
			return;
		}
		
		// Create practice trials (2 baseline, 2 congruent, 2 incongruent)
		const colors = sessionData.colors.slice(0, 4); // Use 4 colors for practice
		
		practiceTrials = [
			// Baseline trials
			{
				condition: 'baseline',
				display_color: colors[0],
				word_text: null,
				correct_answer: colors[0],
				hint: 'Just click the color of the patch. No word to distract you!'
			},
			{
				condition: 'baseline',
				display_color: colors[1],
				word_text: null,
				correct_answer: colors[1],
				hint: 'Simple color identification - nice and easy.'
			},
			// Congruent trials
			{
				condition: 'congruent',
				display_color: colors[2],
				word_text: colors[2].toUpperCase(),
				correct_answer: colors[2],
				hint: 'The word matches the color - easy!'
			},
			{
				condition: 'congruent',
				display_color: colors[3],
				word_text: colors[3].toUpperCase(),
				correct_answer: colors[3],
				hint: 'Word and color agree - this is the easy condition.'
			},
			// Incongruent trials (THE CHALLENGE)
			{
				condition: 'incongruent',
				display_color: colors[0],
				word_text: colors[1].toUpperCase(),
				correct_answer: colors[0],
				hint: `Ignore the word "${colors[1].toUpperCase()}" - answer the INK COLOR!`
			},
			{
				condition: 'incongruent',
				display_color: colors[2],
				word_text: colors[3].toUpperCase(),
				correct_answer: colors[2],
				hint: `Don't read the word! Focus on the color of the ink.`
			}
		];

		currentPractice = 0;
		practiceFeedback = null;
		phase = 'practice';
	}

	function handlePracticeAnswer(answer) {
		const trial = practiceTrials[currentPractice];
		const correct = answer === trial.correct_answer;

		if (correct) {
			practiceFeedback = {
				type: 'success',
				message: 'Correct! ' + trial.hint
			};
		} else {
			practiceFeedback = {
				type: 'error',
				message: `Not quite. The correct answer was "${trial.correct_answer}". ${trial.hint}`
			};
		}

		// Auto-advance after 2 seconds
		setTimeout(() => {
			if (currentPractice < practiceTrials.length - 1) {
				currentPractice++;
				practiceFeedback = null;
			} else {
				// Practice complete
				setTimeout(() => {
					startTest();
				}, 1000);
			}
		}, 2000);
	}

	function startTest() {
		phase = 'test';
		currentTrial = 0;
		responses = [];
		showNextTrial();
	}

	function showNextTrial() {
		if (currentTrial >= sessionData.trials.length) {
			completeSession();
			return;
		}

		userAnswer = '';
		showStimulus = true;
		startTime = Date.now();

		const trial = sessionData.trials[currentTrial];
		const presentationTime = sessionData.presentation_time_ms;
		const timeoutTime = sessionData.response_timeout_ms;

		// Show stimulus for presentation time, then stay visible but require response
		trialTimeout = setTimeout(() => {
			showStimulus = true; // Keep showing but user must respond
			
			// Auto-advance if no response within timeout
			responseTimeout = setTimeout(() => {
				handleAnswer('', true); // Timeout - no response
			}, timeoutTime);
		}, presentationTime);
	}

	function handleAnswer(answer, isTimeout = false) {
		clearTimeout(trialTimeout);
		clearTimeout(responseTimeout);

		const reactionTime = Date.now() - startTime;
		const trial = sessionData.trials[currentTrial];

		responses.push({
			trial_number: trial.trial_number,
			condition: trial.condition,
			user_response: answer,
			correct_answer: trial.correct_answer,
			correct: answer === trial.correct_answer,
			reaction_time_ms: isTimeout ? 0 : reactionTime
		});

		currentTrial++;
		
		// Brief pause before next trial
		setTimeout(() => {
			showNextTrial();
		}, 300);
	}

	function handleColorClick(color) {
		if (phase === 'practice') {
			handlePracticeAnswer(color);
		} else if (phase === 'test') {
			handleAnswer(color);
		}
	}

	async function completeSession() {
		try {
			const response = await fetch(`${API_BASE_URL}/training/tasks/stroop/submit/${currentUser.id}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					difficulty,
					session_data: sessionData,
					responses
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
		}
	}

	function returnToDashboard() {
		goto('/dashboard');
	}

	// Get current trial data
	$: currentTrialData = phase === 'practice' 
		? practiceTrials[currentPractice] 
		: (sessionData && currentTrial < sessionData.trials.length) 
			? sessionData.trials[currentTrial] 
			: null;

	// Progress tracking
	$: progress = sessionData ? ((currentTrial / sessionData.trials.length) * 100) : 0;
	$: trialsRemaining = sessionData ? sessionData.trials.length - currentTrial : 0;

	// Current condition name
	$: conditionName = currentTrialData?.condition === 'baseline' ? 'Color Patches'
		: currentTrialData?.condition === 'congruent' ? 'Matching Words'
		: 'Conflicting Words';

	// Performance badge color
	$: performanceBadgeColor = metrics?.performance_level === 'Excellent' ? 'from-green-500 to-emerald-600'
		: metrics?.performance_level === 'Good' ? 'from-blue-500 to-indigo-600'
		: metrics?.performance_level === 'Fair' ? 'from-yellow-500 to-orange-500'
		: 'from-gray-500 to-gray-600';
</script>

<div class="stroop-container">
	{#if loading}
		<div class="loading">
			<div class="spinner"></div>
			<p>Loading task...</p>
		</div>
	{:else if phase === 'intro'}
			<!-- Introduction Screen -->
		<div class="instructions">
			<h1>🧠 Stroop Color-Word Test</h1>
			<div class="classic-badge">Classic Attention & Inhibitory Control Assessment</div>
			
			<div class="instruction-card">
				<div class="task-header">
					<h2>💡 Your Task: Name the Color, NOT the Word!</h2>
				</div>
				
				<p class="importance">
					Your brain automatically reads words - it's involuntary! This test measures your ability 
					to <strong>inhibit</strong> this automatic response and focus on the <strong>ink color</strong> instead.
				</p>
				
				<!-- Visual Examples -->
				<div class="stroop-examples">
					<div class="example-card baseline">
						<div class="example-label">Type 1: Baseline</div>
						<div class="color-patch"></div>
						<div class="example-desc">Just a color patch</div>
						<div class="example-note">✓ Easy - No interference</div>
					</div>
					
					<div class="example-card congruent">
						<div class="example-label">Type 2: Congruent</div>
						<div class="stroop-word" style="color: #dc2626;">RED</div>
						<div class="example-desc">Word matches color</div>
						<div class="example-note">✓ Easy - No conflict</div>
					</div>
					
					<div class="example-card incongruent">
						<div class="example-label">Type 3: Incongruent ⚡</div>
						<div class="stroop-word" style="color: #2563eb;">RED</div>
						<div class="example-desc">Word conflicts with color!</div>
						<div class="example-note">🎯 The REAL challenge!</div>
					</div>
				</div>
				
				<div class="rule-box">
					<strong>⚡ The Rule:</strong>
					Always name the INK COLOR, not the word!<br>
					In the example above, the correct answer is <strong>"BLUE"</strong> (ignore the word "RED")
				</div>
				
				<!-- Two Column Layout -->
				<div class="info-grid">
					<div class="info-section">
						<h3>📋 Test Structure</h3>
						<div class="structure-list">
							<div class="structure-item">
								<div class="structure-num">1</div>
								<div class="structure-text">
									<strong>Color Patches</strong>
									<span>Baseline speed</span>
								</div>
							</div>
							<div class="structure-item">
								<div class="structure-num">2</div>
								<div class="structure-text">
									<strong>Matching Words</strong>
									<span>Word = Color</span>
								</div>
							</div>
							<div class="structure-item">
								<div class="structure-num">3</div>
								<div class="structure-text">
									<strong>Conflicting Words</strong>
									<span>The real test!</span>
								</div>
							</div>
						</div>
					</div>
					
					<div class="info-section">
						<h3>💪 Tips for Success</h3>
						<div class="tips-list">
							<div class="tip-item">✓ <strong>Focus on the color</strong> - Not the letters</div>
							<div class="tip-item">✓ <strong>Don't read</strong> - Your brain will try!</div>
							<div class="tip-item">✓ <strong>Stay focused</strong> - Concentration is key</div>
							<div class="tip-item">✓ <strong>Speed matters</strong> - Quick but accurate</div>
							<div class="tip-item">✓ <strong>Practice helps</strong> - Trains your brain!</div>
						</div>
					</div>
				</div>
				
				<!-- Clinical Context -->
				<div class="clinical-info">
					<h3>📚 Clinical Significance</h3>
					<div class="clinical-grid">
						<div class="clinical-item">
							<strong>📜 History:</strong> Stroop, 1935 - Psychology's most famous experiment
						</div>
						<div class="clinical-item">
							<strong>🎯 Measures:</strong> Attention, inhibition, cognitive control
						</div>
						<div class="clinical-item">
							<strong>🏥 MS Relevance:</strong> Sensitive to frontal lobe changes (Parmenter et al., 2007)
						</div>
						<div class="clinical-item">
							<strong>🌍 Clinical Use:</strong> Standard in neuropsych assessments worldwide
						</div>
					</div>
				</div>
			</div>
			
			<div class="button-group">
				<button class="start-button" on:click={startInstructions}>
					Begin Test
				</button>
				<button class="btn-secondary" on:click={() => goto('/dashboard')}>
					Back to Dashboard
				</button>
			</div>
		</div>

		{:else if phase === 'instructions'}
			<!-- Quick Instructions Before Practice -->
		<div class="quick-instructions">
			<h2>Quick Instructions</h2>

			<div class="instructions-steps">
				<div class="instruction-step step-1">
					<span class="step-number">1</span>
					<div class="step-content">
						<p class="step-title">See the Stimulus</p>
						<p class="step-desc">Color patch or colored word appears</p>
					</div>
				</div>

				<div class="instruction-step step-2">
					<span class="step-number">2</span>
					<div class="step-content">
						<p class="step-title">Identify Ink Color</p>
						<p class="step-desc">Ignore what the word says - focus on the COLOR</p>
					</div>
				</div>

				<div class="instruction-step step-3">
					<span class="step-number">3</span>
					<div class="step-content">
						<p class="step-title">Click the Color Button</p>
						<p class="step-desc">Click the button matching the ink color</p>
					</div>
				</div>

				<div class="instruction-step step-4">
					<span class="step-number">4</span>
					<div class="step-content">
						<p class="step-title">Respond Quickly</p>
						<p class="step-desc">Speed matters - but stay accurate!</p>
					</div>
				</div>
			</div>

			<div class="remember-box">
				<p class="remember-title">Remember:</p>
				<p class="remember-text">
					In conflicting trials, your brain will want to read the word. 
					<strong>Resist this impulse!</strong> Focus only on the ink color. This is what makes it challenging!
				</p>
				</div>

			<div class="practice-prompt">
				<p>Let's practice with 6 trials to get familiar...</p>
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
				<p class="condition-label">Condition: <span>{conditionName}</span></p>
			</div>

			<!-- Stimulus Display -->
			<div class="stimulus-area">
				{#if currentTrialData.condition === 'baseline'}
					<!-- Color patch -->
					<div 
						class="color-patch-large"
						style="background-color: {COLOR_MAP[currentTrialData.display_color]};"
					></div>
				{:else}
					<!-- Word in color -->
					<div 
						class="stroop-word-large"
						style="color: {COLOR_MAP[currentTrialData.display_color]};"
					>
						{currentTrialData.word_text}
					</div>
				{/if}
			</div>

			<!-- Color Buttons -->
			<div class="color-buttons">
				{#each sessionData.colors.slice(0, 4) as color}
					<button
						on:click={() => handleColorClick(color)}
						disabled={practiceFeedback !== null}
						class="color-btn"
						style="background-color: {COLOR_MAP[color]};"
					>
						{color.toUpperCase()}
					</button>
				{/each}
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
						<span class="badge-condition">{conditionName}</span>
					</div>
				</div>
				<div class="progress-bar-container">
					<div 
						class="progress-bar-fill"
						style="width: {progress}%"
					></div>
				</div>
			</div>

			<!-- Stimulus Display -->
			{#if showStimulus && currentTrialData}
				<div class="stimulus-area">
					{#if currentTrialData.condition === 'baseline'}
						<!-- Color patch -->
						<div 
							class="color-patch-xlarge"
							style="background-color: {COLOR_MAP[currentTrialData.display_color]};"
						></div>
					{:else}
						<!-- Word in color -->
						<div 
							class="stroop-word-xlarge"
							style="color: {COLOR_MAP[currentTrialData.display_color]};"
						>
							{currentTrialData.word_text}
						</div>
						{#if currentTrialData.condition === 'incongruent'}
							<p class="hint-text">
								(Ignore the word - name the INK color!)
							</p>
						{/if}
					{/if}
				</div>

				<!-- Color Buttons -->
				<div class="color-buttons color-buttons-test">
					{#each sessionData.colors as color}
						<button
							on:click={() => handleColorClick(color)}
							class="color-btn"
							style="background-color: {COLOR_MAP[color]};"
						>
							{color.toUpperCase()}
						</button>
					{/each}
				</div>
			{/if}
		</div>

	{:else if phase === 'results'}
		<!-- Results Screen -->
		<div class="results-container">
			<div class="results-header">
				<h2>Stroop Test Complete!</h2>
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
					<div class="metric-detail">{metrics.correct_trials}/{metrics.total_trials} correct</div>
				</div>

				<!-- Stroop Effect -->
				<div class="metric-card stroop-card">
					<div class="metric-label">Stroop Effect</div>
					<div class="metric-value">{metrics.stroop_effect.toFixed(0)} ms</div>
					<div class="metric-detail">Conflict - Congruent RT</div>
				</div>

				<!-- Interference Cost -->
				<div class="metric-card interference-card">
					<div class="metric-label">Interference Cost</div>
					<div class="metric-value">{metrics.interference_cost.toFixed(1)}%</div>
					<div class="metric-detail">vs Baseline</div>
				</div>

				<!-- Consistency -->
				<div class="metric-card consistency-card">
					<div class="metric-label">Consistency</div>
					<div class="metric-value">{metrics.consistency.toFixed(1)}%</div>
					<div class="metric-detail">Response stability</div>
				</div>
			</div>

				<!-- Condition Breakdown -->
			<div class="conditions-section">
				<h3>Performance by Condition</h3>
				<div class="conditions-grid">
					<!-- Baseline -->
					<div class="condition-card baseline-card">
						<p class="condition-title">Color Patches (Baseline)</p>
						<p class="condition-stat">Accuracy: <span>{metrics.baseline_accuracy.toFixed(1)}%</span></p>
						<p class="condition-stat">Avg RT: <span>{metrics.baseline_rt.toFixed(0)} ms</span></p>
						<p class="condition-note">Pure processing speed</p>
					</div>

					<!-- Congruent -->
					<div class="condition-card congruent-card">
						<p class="condition-title">Matching Words (Congruent)</p>
						<p class="condition-stat">Accuracy: <span>{metrics.congruent_accuracy.toFixed(1)}%</span></p>
						<p class="condition-stat">Avg RT: <span>{metrics.congruent_rt.toFixed(0)} ms</span></p>
						<p class="condition-note success">
							{#if metrics.facilitation_effect > 0}
								✓ {metrics.facilitation_effect.toFixed(0)} ms faster than baseline!
							{:else}
								No facilitation effect
							{/if}
						</p>
					</div>

					<!-- Incongruent -->
					<div class="condition-card incongruent-card">
						<p class="condition-title">Conflicting Words (Incongruent)</p>
						<p class="condition-stat">Accuracy: <span>{metrics.incongruent_accuracy.toFixed(1)}%</span></p>
						<p class="condition-stat">Avg RT: <span>{metrics.incongruent_rt.toFixed(0)} ms</span></p>
						<p class="condition-note warning">
							{#if metrics.stroop_effect > 0}
								⚡ {metrics.stroop_effect.toFixed(0)} ms interference penalty
							{:else}
								Excellent interference control!
							{/if}
						</p>
					</div>
				</div>
			</div>

				<!-- Interpretation -->
			<div class="interpretation-section">
				<h3>What This Means</h3>
				<p class="feedback-text">{metrics.feedback}</p>
				
				<div class="insights-list">
					{#if metrics.interference_cost < 20}
						<p class="insight success">
							✓ <strong>Excellent inhibitory control:</strong> Minimal interference from word reading
						</p>
					{:else if metrics.interference_cost < 40}
						<p class="insight good">
							✓ <strong>Good cognitive control:</strong> Managing interference effectively
						</p>
					{:else if metrics.interference_cost < 60}
						<p class="insight moderate">
							⚡ <strong>Moderate interference:</strong> Word reading affecting performance - normal!
						</p>
					{:else}
						<p class="insight high">
							⚡ <strong>High interference effect:</strong> Word reading strongly competing with color naming
						</p>
					{/if}

					{#if metrics.stroop_effect < 100}
						<p class="insight success">
							✓ <strong>Minimal Stroop effect:</strong> Fast conflict resolution
						</p>
					{:else if metrics.stroop_effect < 200}
						<p class="insight good">
							✓ <strong>Normal Stroop effect:</strong> Expected interference range
						</p>
					{:else}
						<p class="insight moderate">
							⚡ <strong>Significant Stroop effect:</strong> Conflicts taking extra processing time
						</p>
					{/if}
				</div>
			</div>

				<!-- Clinical Context -->
			<div class="clinical-context">
				<h3>About the Stroop Test</h3>
				<div class="clinical-content">
					<p>
						<strong>The Stroop Effect</strong> demonstrates automatic processing (word reading) 
						versus controlled processing (color naming). Everyone experiences this interference!
					</p>
					<p>
						<strong>For MS:</strong> This test is sensitive to frontal lobe dysfunction and executive 
						control deficits. Regular practice can improve inhibitory control and selective attention.
					</p>
					<p>
						<strong>Why It's Hard:</strong> Your brain has practiced reading for years - it happens 
						automatically. Suppressing this automatic response requires focused attention and cognitive control.
					</p>
					<p>
						<strong>Training Benefits:</strong> Repeated Stroop practice strengthens prefrontal circuits 
						involved in inhibitory control, which can improve real-world attention and focus.
					</p>
				</div>
			</div>

			<!-- Difficulty Adaptation Info -->
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

		<!-- Help Button (always visible) -->
	{#if phase !== 'results'}
		<button on:click={() => showHelp = true} class="help-button" aria-label="Help">
			?
		</button>
	{/if}

	<!-- Help Modal -->
	{#if showHelp}
		<div class="modal-overlay" on:click={() => showHelp = false} on:keydown={(e) => e.key === 'Escape' && (showHelp = false)} role="button" aria-label="Close help dialog" tabindex="0">
			<div class="modal-content" on:click|stopPropagation on:keydown={(e) => e.stopPropagation()} role="document" tabindex="0">
				<h2 class="modal-title">Stroop Test Help</h2>

				<div class="help-sections">
					<div class="help-section">
						<h3>What is the Stroop Test?</h3>
						<p>
							A classic psychological test measuring selective attention and cognitive interference. 
							It demonstrates how automatic processes (reading) can interfere with task goals (naming colors).
						</p>
					</div>

					<div class="help-section">
						<h3>Why Is It Used in MS?</h3>
						<ul>
							<li>Sensitive to frontal lobe and executive function changes</li>
							<li>Measures inhibitory control (suppressing automatic responses)</li>
							<li>Assesses selective attention and cognitive flexibility</li>
							<li>Standard in neuropsychological MS assessments</li>
							<li>Training can improve real-world attention control</li>
						</ul>
					</div>

					<div class="help-section">
						<h3>Understanding Your Metrics</h3>
						<div class="metrics-explain">
							<p><strong>Stroop Effect:</strong> Difference between conflicting and matching trials. Lower is better.</p>
							<p><strong>Interference Cost:</strong> How much slower you are on conflict trials vs. baseline. Measures inhibitory control.</p>
							<p><strong>Facilitation Effect:</strong> How much faster matching words are vs. baseline. Shows word reading benefit.</p>
							<p><strong>Consistency:</strong> How stable your response times are across trials.</p>
						</div>
					</div>

					<div class="help-section">
						<h3>Strategies for Success</h3>
						<ul>
							<li>Look at the color of the letters/ink, not their meaning</li>
							<li>Try slightly unfocusing your eyes to blur the word</li>
							<li>Practice saying color names aloud during practice</li>
							<li>Stay focused - concentration improves inhibitory control</li>
							<li>Don't worry about mistakes - interference is universal!</li>
						</ul>
					</div>

					<div class="help-section">
						<h3>Historical Note</h3>
						<p>
							John Ridley Stroop published this effect in 1935. It remains one of the most widely 
							used tests in psychology and neuropsychology, with thousands of research papers published!
						</p>
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
	.stroop-container {
		background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
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
		border-top: 4px solid #667eea;
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
		color: #667eea;
		font-size: 2.5rem;
		margin-bottom: 1rem;
	}

	.classic-badge {
		background: linear-gradient(135deg, rgba(102, 126, 234, 0.15), rgba(118, 75, 162, 0.15));
		color: #667eea;
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
		color: #667eea;
	}

	/* Stroop Examples */
	.stroop-examples {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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

	.example-card.baseline {
		border: 3px solid #9ca3af;
	}

	.example-card.congruent {
		border: 3px solid #16a34a;
	}

	.example-card.incongruent {
		border: 4px solid #f59e0b;
		box-shadow: 0 6px 16px rgba(245, 158, 11, 0.3);
	}

	.example-label {
		font-size: 0.75rem;
		font-weight: bold;
		color: #666;
		margin-bottom: 1rem;
		text-transform: uppercase;
	}

	.incongruent .example-label {
		color: #ea580c;
	}

	.color-patch {
		width: 80px;
		height: 80px;
		background-color: #2563eb;
		border-radius: 12px;
		margin: 1rem auto;
		box-shadow: 0 4px 8px rgba(0,0,0,0.15);
	}

	.stroop-word {
		font-size: 3.5rem;
		font-weight: bold;
		margin: 0.5rem 0;
		line-height: 1.2;
	}

	.example-desc {
		font-size: 0.95rem;
		font-weight: 600;
		color: #2c3e50;
		margin: 0.75rem 0;
	}

	.example-note {
		font-size: 0.85rem;
		font-weight: 600;
		margin-top: 0.5rem;
	}

	.baseline .example-note {
		color: #16a34a;
	}

	.congruent .example-note {
		color: #16a34a;
	}

	.incongruent .example-note {
		color: #ea580c;
	}

	/* Rule Box */
	.rule-box {
		background: #fef2f2;
		border-left: 4px solid #dc2626;
		padding: 1.25rem;
		border-radius: 8px;
		margin: 2rem 0;
		color: #991b1b;
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

	/* Structure List */
	.structure-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.structure-item {
		display: flex;
		align-items: center;
		gap: 1rem;
		background: #f8f9fa;
		padding: 1rem;
		border-radius: 8px;
	}

	.structure-num {
		width: 45px;
		height: 45px;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.5rem;
		font-weight: bold;
		flex-shrink: 0;
	}

	.structure-text {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.structure-text strong {
		font-size: 1rem;
		color: #2c3e50;
	}

	.structure-text span {
		font-size: 0.875rem;
		color: #666;
	}

	/* Tips List */
	.tips-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.tip-item {
		background: #f0fdf4;
		padding: 0.75rem 1rem;
		border-radius: 8px;
		color: #15803d;
		font-size: 0.95rem;
		line-height: 1.5;
	}

	.tip-item strong {
		color: #166534;
	}

	/* Clinical Info */
	.clinical-info {
		background: linear-gradient(135deg, rgba(102, 126, 234, 0.08), rgba(118, 75, 162, 0.08));
		padding: 1.5rem;
		border-radius: 12px;
		margin-top: 1.5rem;
	}

	.clinical-info h3 {
		color: #667eea;
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
		color: #667eea;
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
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		padding: 1.25rem 3rem;
		font-size: 1.2rem;
		font-weight: bold;
		border-radius: 12px;
		cursor: pointer;
		transition: all 0.3s;
		box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
	}

	.start-button:hover {
		transform: translateY(-3px);
		box-shadow: 0 6px 25px rgba(102, 126, 234, 0.6);
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

	/* Quick Instructions Page */
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
		color: #667eea;
		font-size: 2rem;
		margin-bottom: 2rem;
	}

	.instructions-steps {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
		margin-bottom: 2rem;
	}

	.instruction-step {
		display: flex;
		align-items: center;
		gap: 1.5rem;
		background: #f8f9fa;
		padding: 1.5rem;
		border-radius: 12px;
		transition: all 0.3s;
	}

	.instruction-step:hover {
		transform: translateX(8px);
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
	}

	.step-number {
		width: 60px;
		height: 60px;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 2rem;
		font-weight: bold;
		flex-shrink: 0;
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
	}

	.step-content {
		flex: 1;
	}

	.step-title {
		font-size: 1.2rem;
		font-weight: 700;
		color: #2c3e50;
		margin-bottom: 0.5rem;
	}

	.step-desc {
		font-size: 1rem;
		color: #666;
		margin: 0;
	}

	.remember-box {
		background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(239, 68, 68, 0.1));
		border-left: 4px solid #f59e0b;
		padding: 1.5rem;
		border-radius: 12px;
		margin: 2rem 0;
	}

	.remember-title {
		font-size: 1.1rem;
		font-weight: 700;
		color: #ea580c;
		margin-bottom: 0.75rem;
	}

	.remember-text {
		font-size: 1rem;
		color: #78350f;
		line-height: 1.6;
		margin: 0;
	}

	.remember-text strong {
		color: #dc2626;
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

	.trial-header, .progress-header {
		text-align: center;
		margin-bottom: 2rem;
	}

	.trial-header h2, .progress-header h2 {
		color: #2c3e50;
		font-size: 1.5rem;
		margin-bottom: 0.5rem;
	}

	.condition-label {
		color: #666;
		font-size: 1rem;
	}

	.condition-label span {
		font-weight: 700;
		color: #667eea;
	}

	.progress-top {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		flex-wrap: wrap;
		gap: 1rem;
	}

	.progress-badges {
		display: flex;
		gap: 0.75rem;
	}

	.badge-remaining {
		background: #e0e7ff;
		color: #4338ca;
		padding: 0.5rem 1rem;
		border-radius: 20px;
		font-size: 0.875rem;
		font-weight: 600;
	}

	.badge-condition {
		background: #ddd6fe;
		color: #6d28d9;
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
		background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
		transition: width 0.3s ease;
	}

	.stimulus-area {
		min-height: 300px;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		margin: 3rem 0;
	}

	.color-patch-large {
		width: 200px;
		height: 200px;
		border-radius: 20px;
		box-shadow: 0 8px 24px rgba(0,0,0,0.2);
	}

	.color-patch-xlarge {
		width: 250px;
		height: 250px;
		border-radius: 24px;
		box-shadow: 0 10px 30px rgba(0,0,0,0.25);
	}

	.stroop-word-large {
		font-size: 5rem;
		font-weight: 900;
		text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
	}

	.stroop-word-xlarge {
		font-size: 6rem;
		font-weight: 900;
		text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
	}

	.hint-text {
		margin-top: 1rem;
		font-size: 0.9rem;
		color: #666;
		font-style: italic;
	}

	.color-buttons {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
		gap: 1rem;
		max-width: 600px;
		margin: 0 auto;
	}

	.color-buttons-test {
		max-width: 700px;
	}

	.color-btn {
		padding: 1.5rem 1rem;
		font-size: 1.1rem;
		font-weight: 700;
		color: white;
		border: none;
		border-radius: 12px;
		cursor: pointer;
		transition: all 0.2s;
		box-shadow: 0 4px 12px rgba(0,0,0,0.2);
		text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
	}

	.color-btn:hover:not(:disabled) {
		transform: translateY(-4px);
		box-shadow: 0 6px 20px rgba(0,0,0,0.3);
	}

	.color-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
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
		background: linear-gradient(135deg, #3b82f6 0%, #4f46e5 100%);
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

	.stroop-card {
		background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(236, 72, 153, 0.1));
		border-color: #a855f7;
	}

	.interference-card {
		background: linear-gradient(135deg, rgba(251, 146, 60, 0.1), rgba(239, 68, 68, 0.1));
		border-color: #fb923c;
	}

	.consistency-card {
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(79, 70, 229, 0.1));
		border-color: #3b82f6;
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

	/* Conditions Section */
	.conditions-section {
		background: linear-gradient(135deg, rgba(139, 92, 246, 0.08), rgba(236, 72, 153, 0.08));
		padding: 1.5rem;
		border-radius: 12px;
		margin-bottom: 2rem;
	}

	.conditions-section h3 {
		font-size: 1.2rem;
		font-weight: 700;
		color: #2c3e50;
		margin-bottom: 1.25rem;
	}

	.conditions-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: 1rem;
	}

	.condition-card {
		background: white;
		padding: 1.25rem;
		border-radius: 10px;
		border: 2px solid;
	}

	.baseline-card {
		border-color: #9ca3af;
	}

	.congruent-card {
		border-color: #10b981;
	}

	.incongruent-card {
		border-color: #ef4444;
	}

	.condition-title {
		font-weight: 700;
		color: #2c3e50;
		margin-bottom: 0.75rem;
		font-size: 1rem;
	}

	.condition-stat {
		font-size: 0.9rem;
		color: #555;
		margin-bottom: 0.5rem;
	}

	.condition-stat span {
		font-weight: 700;
	}

	.condition-note {
		font-size: 0.85rem;
		color: #666;
		margin-top: 0.75rem;
	}

	.condition-note.success {
		color: #059669;
		font-weight: 600;
	}

	.condition-note.warning {
		color: #ea580c;
		font-weight: 600;
	}

	/* Interpretation Section */
	.interpretation-section {
		background: white;
		border: 2px solid #a855f7;
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
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.08), rgba(139, 92, 246, 0.08));
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
		background: linear-gradient(135deg, #9333ea 0%, #ec4899 100%);
		color: white;
		padding: 1.25rem 3rem;
		font-size: 1.1rem;
		font-weight: 700;
		border: none;
		border-radius: 12px;
		cursor: pointer;
		transition: all 0.3s;
		box-shadow: 0 4px 15px rgba(147, 51, 234, 0.4);
	}

	.return-button:hover {
		transform: translateY(-3px);
		box-shadow: 0 6px 25px rgba(147, 51, 234, 0.6);
	}

	/* Help Button */
	.help-button {
		position: fixed;
		bottom: 2rem;
		right: 2rem;
		width: 56px;
		height: 56px;
		background: #9333ea;
		color: white;
		border: none;
		border-radius: 50%;
		font-size: 2rem;
		cursor: pointer;
		box-shadow: 0 4px 15px rgba(147, 51, 234, 0.4);
		transition: all 0.3s;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.help-button:hover {
		background: #7c3aed;
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
		background: #9333ea;
		color: white;
		border: none;
		border-radius: 12px;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s;
	}

	.modal-close-btn:hover {
		background: #7c3aed;
	}

	/* Responsive */
	@media (max-width: 768px) {
		.instructions {
			padding: 1.5rem 1rem;
		}

		.instructions h1 {
			font-size: 2rem;
		}

		.stroop-examples {
			grid-template-columns: 1fr;
		}

		.info-grid {
			grid-template-columns: 1fr;
		}

		.stroop-word {
			font-size: 2.5rem;
		}
	}
</style>

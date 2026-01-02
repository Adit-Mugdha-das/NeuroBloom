<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { user } from '$lib/stores.js';
	import { onMount } from 'svelte';

	const API_BASE_URL = 'http://127.0.0.1:8000';

	let currentUser = null;
	let sessionData = null;
	let currentTrialIndex = 0;
	let currentTrial = null;
	let responses = [];
	let taskId = null;
	
	// UI states
	let showInstructions = true;
	let showPractice = false;
	let practiceComplete = false;
	let testStarted = false;
	let showStimulus = false;
	let showMask = false;
	let waitingForResponse = false;
	let showResults = false;
	let error = null;
	let loading = false;
	
	// Practice trial data
	let practiceTrial = null;
	let practiceAttempts = 0;
	
	// Timing
	let stimulusStartTime = 0;
	let maskStartTime = 0;
	
	// Results
	let results = null;
	
	// Help modal
	let showHelp = false;

	// Subscribe to user store
	user.subscribe(value => {
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
			error = null;
			
			const response = await fetch(`${API_BASE_URL}/api/training/tasks/inspection-time/generate/${currentUser.id}`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				}
			});
			
			if (!response.ok) {
				throw new Error('Failed to load session');
			}
			
			const data = await response.json();
			sessionData = data.session_data;
			
		} catch (err) {
			error = err.message;
		} finally {
			loading = false;
		}
	}

	function startPractice() {
		showInstructions = false;
		showPractice = true;
		
		// Generate a practice trial (easy settings)
		practiceTrial = {
			left_height: 180,
			right_height: 150,
			longer_side: "left",
			presentation_time_ms: 300,  // Extra long for practice
			line_width: 8
		};
		
		practiceAttempts = 0;
	}

	async function runPracticeTrial() {
		showStimulus = true;
		
		// Show stimulus for practice duration
		await sleep(practiceTrial.presentation_time_ms);
		
		showStimulus = false;
		showMask = true;
		
		// Show mask briefly
		await sleep(500);
		
		showMask = false;
		waitingForResponse = true;
	}

	function handlePracticeResponse(answer) {
		waitingForResponse = false;
		practiceAttempts++;
		
		if (answer === practiceTrial.longer_side) {
			// Correct! Move on
			if (practiceAttempts >= 2) {
				practiceComplete = true;
			} else {
				// One more practice
				setTimeout(() => runPracticeTrial(), 1500);
			}
		} else {
			// Wrong, explain and try again
			alert(`The ${practiceTrial.longer_side} line was longer. Let's try again!`);
			setTimeout(() => runPracticeTrial(), 2000);
		}
	}

	function startTest() {
		showPractice = false;
		practiceComplete = false;
		testStarted = true;
		currentTrialIndex = 0;
		responses = [];
		
		nextTrial();
	}

	async function nextTrial() {
		if (currentTrialIndex >= sessionData.total_trials) {
			await submitResults();
			return;
		}
		
		currentTrial = sessionData.trials[currentTrialIndex];
		
		// Brief pause before trial
		await sleep(800);
		
		// Show fixation cross
		// (can add UI element if desired)
		await sleep(500);
		
		// Show stimulus
		showStimulus = true;
		stimulusStartTime = performance.now();
		
		await sleep(currentTrial.presentation_time_ms);
		
		// Hide stimulus, show mask
		showStimulus = false;
		showMask = true;
		maskStartTime = performance.now();
		
		await sleep(sessionData.config.mask_duration_ms || 500);
		
		// Hide mask, wait for response
		showMask = false;
		waitingForResponse = true;
	}

	function handleResponse(answer) {
		if (!waitingForResponse) return;
		
		const reactionTime = performance.now() - maskStartTime;
		
		responses.push({
			trial_index: currentTrialIndex,
			user_answer: answer,
			reaction_time: reactionTime,
			presentation_time: currentTrial.presentation_time_ms
		});
		
		waitingForResponse = false;
		currentTrialIndex++;
		
		nextTrial();
	}

	async function submitResults() {
		try {
			loading = true;
			testStarted = false;
			taskId = $page.url.searchParams.get('taskId');
			
			const response = await fetch(`${API_BASE_URL}/api/training/tasks/inspection-time/submit/${currentUser.id}`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					difficulty: sessionData.difficulty,
					session_data: sessionData,
					responses: responses,
					task_id: taskId
				})
			});
			
			if (!response.ok) {
				throw new Error('Failed to submit results');
			}
			
			results = await response.json();
			showResults = true;
			
		} catch (err) {
			error = err.message;
		} finally {
			loading = false;
		}
	}

	function sleep(ms) {
		return new Promise(resolve => setTimeout(resolve, ms));
	}

	function returnToDashboard() {
		goto('/dashboard');
	}

	// Reactive calculations
	$: trialsRemaining = sessionData ? sessionData.total_trials - currentTrialIndex : 0;
	$: progressPercent = sessionData ? (currentTrialIndex / sessionData.total_trials * 100) : 0;
</script>

<svelte:head>
	<title>Inspection Time - NeuroBloom</title>
</svelte:head>

<div class="task-container">
	{#if loading}
		<div class="loading-state">
			<div class="spinner"></div>
			<p>Loading task...</p>
		</div>
	{:else if error}
		<div class="error-state">
			<h2>⚠️ Error</h2>
			<p>{error}</p>
			<button on:click={returnToDashboard}>Return to Dashboard</button>
		</div>
	{:else if showInstructions}
		<div class="instructions-panel">
			<div class="task-header">
				<h1>🔍 Inspection Time Task</h1>
				<p class="task-subtitle">Pure Perceptual Speed Assessment</p>
			</div>

			<div class="clinical-context">
				<h3>📋 About This Task</h3>
				<p>The Inspection Time task measures your brain's pure perceptual processing speed - how quickly you can perceive and identify visual information.</p>
				
				<div class="ms-benefits">
					<h4>✨ Benefits for MS</h4>
					<ul>
						<li><strong>No Motor Component:</strong> Tests pure perception, not movement speed</li>
						<li><strong>Processing Speed:</strong> Fundamental to many cognitive abilities</li>
						<li><strong>Visual Pathways:</strong> Directly assesses visual processing efficiency</li>
						<li><strong>Adaptive Training:</strong> Adjusts to your perceptual threshold</li>
					</ul>
				</div>

				<div class="research-note">
					<strong>Research Foundation:</strong> Based on Vickers & Smith (1986) perceptual speed research. Widely used in cognitive aging and clinical neuropsychology.
				</div>
			</div>

			<div class="how-it-works">
				<h3>🎯 How It Works</h3>
				<div class="instruction-steps">
					<div class="step">
						<span class="step-number">1</span>
						<div class="step-content">
							<h4>Brief Flash</h4>
							<p>Two vertical lines will appear very briefly (as short as 50 milliseconds)</p>
						</div>
					</div>
					<div class="step">
						<span class="step-number">2</span>
						<div class="step-content">
							<h4>Immediate Mask</h4>
							<p>A pattern mask appears immediately to prevent afterimage processing</p>
						</div>
					</div>
					<div class="step">
						<span class="step-number">3</span>
						<div class="step-content">
							<h4>Your Decision</h4>
							<p>Indicate which line was longer: LEFT or RIGHT</p>
						</div>
					</div>
				</div>

				<div class="important-note">
					<strong>⏱️ Important:</strong> The flash is VERY brief - this is intentional! We're measuring your basic perceptual speed. Don't worry if it seems fast; everyone finds this challenging.
				</div>
			</div>

			<div class="instruction-tips">
				<h3>💡 Tips for Success</h3>
				<ul>
					<li>Focus on the center of the screen before each trial</li>
					<li>Trust your first impression - don't overthink</li>
					<li>The presentation is too brief for detailed analysis</li>
					<li>It's okay to guess if you're not sure</li>
					<li>Relax - this measures perception, not intelligence</li>
				</ul>
			</div>

			<div class="action-buttons">
				<button class="primary-btn" on:click={startPractice}>
					Start Practice Trials
				</button>
				<button class="help-btn" on:click={() => showHelp = true}>
					📖 More Information
				</button>
			</div>
		</div>
	{:else if showPractice}
		<div class="practice-panel">
			<h2>🎓 Practice Mode</h2>
			<p class="practice-intro">Let's practice with a slower presentation to get familiar with the task.</p>
			
			{#if !practiceComplete}
				<div class="practice-info">
					<p><strong>Practice Trial {practiceAttempts + 1}</strong></p>
					<p>Presentation time: {practiceTrial.presentation_time_ms}ms (slower than actual test)</p>
				</div>

				{#if !showStimulus && !showMask && !waitingForResponse}
					<button class="start-trial-btn" on:click={runPracticeTrial}>
						Ready - Start Practice Trial
					</button>
				{/if}

				{#if showStimulus || showMask}
					<div class="stimulus-area">
						{#if showStimulus}
							<div class="lines-container">
								<div class="line" style="height: {practiceTrial.left_height}px; width: {practiceTrial.line_width}px;"></div>
								<div class="spacer"></div>
								<div class="line" style="height: {practiceTrial.right_height}px; width: {practiceTrial.line_width}px;"></div>
							</div>
						{:else if showMask}
							<div class="mask-pattern">
								<div class="mask-grid">
									{#each Array(20) as _, i}
										<div class="mask-cell" style="animation-delay: {i * 20}ms;"></div>
									{/each}
								</div>
							</div>
						{/if}
					</div>
				{/if}

				{#if waitingForResponse}
					<div class="response-area">
						<p class="response-prompt">Which line was longer?</p>
						<div class="response-buttons">
							<button class="response-btn left-btn" on:click={() => handlePracticeResponse('left')}>
								⬅️ LEFT
							</button>
							<button class="response-btn right-btn" on:click={() => handlePracticeResponse('right')}>
								RIGHT ➡️
							</button>
						</div>
					</div>
				{/if}
			{:else}
				<div class="practice-complete">
					<h3>✅ Practice Complete!</h3>
					<p>Great! You understand the task. The actual test will have shorter presentation times.</p>
					<p><strong>Current difficulty:</strong> {sessionData.config.presentation_time_ms}ms presentation time</p>
					<button class="primary-btn" on:click={startTest}>
						Start Actual Test ({sessionData.total_trials} trials)
					</button>
				</div>
			{/if}
		</div>
	{:else if testStarted}
		<div class="test-panel">
			<div class="test-header">
				<div class="progress-info">
					<div class="trials-remaining">
						<span class="remaining-label">Trials Remaining</span>
						<span class="remaining-value">{trialsRemaining}</span>
					</div>
					<div class="presentation-info">
						<span class="info-label">Presentation Time</span>
						<span class="info-value">{sessionData.config.presentation_time_ms}ms</span>
					</div>
				</div>
				<div class="progress-bar">
					<div class="progress-fill" style="width: {progressPercent}%"></div>
				</div>
			</div>

			<div class="stimulus-area">
				{#if showStimulus}
					<div class="fixation-guide">
						<div class="lines-container">
							<div class="line" style="height: {currentTrial.left_height}px; width: {currentTrial.line_width}px;"></div>
							<div class="spacer"></div>
							<div class="line" style="height: {currentTrial.right_height}px; width: {currentTrial.line_width}px;"></div>
						</div>
					</div>
				{:else if showMask}
					<div class="mask-pattern">
						<div class="mask-grid">
							{#each Array(20) as _, i}
								<div class="mask-cell" style="animation-delay: {i * 20}ms;"></div>
							{/each}
						</div>
					</div>
				{:else if waitingForResponse}
					<div class="response-area">
						<p class="response-prompt">Which line was longer?</p>
						<div class="response-buttons">
							<button class="response-btn left-btn" on:click={() => handleResponse('left')}>
								⬅️ LEFT
							</button>
							<button class="response-btn right-btn" on:click={() => handleResponse('right')}>
								RIGHT ➡️
							</button>
						</div>
					</div>
				{:else}
					<div class="waiting-state">
						<div class="fixation-cross">+</div>
						<p>Get ready...</p>
					</div>
				{/if}
			</div>
		</div>
	{:else if showResults}
		<div class="results-panel">
			<div class="results-header">
				<h2>📊 Inspection Time Results</h2>
				<div class="performance-badge {results.metrics.performance_level.toLowerCase().replace(' ', '-')}">
					{results.metrics.performance_level}
				</div>
			</div>

			<div class="metrics-grid">
				<div class="metric-card primary">
					<div class="metric-icon">🎯</div>
					<div class="metric-value">{results.metrics.accuracy}%</div>
					<div class="metric-label">Accuracy</div>
					<div class="metric-detail">{results.metrics.correct_count}/{results.metrics.total_trials} correct</div>
				</div>

				<div class="metric-card">
					<div class="metric-icon">⚡</div>
					<div class="metric-value">{results.metrics.perceptual_speed_index}</div>
					<div class="metric-label">Perceptual Speed Index</div>
					<div class="metric-detail">At {results.metrics.presentation_time_ms}ms</div>
				</div>

				<div class="metric-card">
					<div class="metric-icon">⏱️</div>
					<div class="metric-value">{results.metrics.average_reaction_time}ms</div>
					<div class="metric-label">Avg Decision Time</div>
					<div class="metric-detail">After mask appearance</div>
				</div>

				<div class="metric-card">
					<div class="metric-icon">📈</div>
					<div class="metric-value">{results.metrics.consistency}%</div>
					<div class="metric-label">Consistency</div>
					<div class="metric-detail">Response variability</div>
				</div>
			</div>

			<div class="interpretation-section">
				<h3>🧠 What This Means</h3>
				<p class="interpretation-text">
					{#if results.metrics.accuracy >= 90}
						Excellent perceptual speed! You're processing visual information very quickly and accurately at {results.metrics.presentation_time_ms}ms presentation time. This indicates strong visual processing pathways.
					{:else if results.metrics.accuracy >= 75}
						Good perceptual processing! You're accurately perceiving information at brief presentation times. Continued practice will help you process even faster.
					{:else if results.metrics.accuracy >= 60}
						Average perceptual speed. Your brain is processing the visual information, but there's room for improvement. Regular practice can enhance your perceptual speed.
					{:else}
						Your perceptual processing is developing. This is a challenging task, and improvement comes with practice. We'll adjust the presentation time to match your current abilities.
					{/if}
				</p>

				<div class="perceptual-context">
					<h4>Understanding Perceptual Speed</h4>
					<ul>
						<li><strong>What it measures:</strong> How quickly your brain can identify and process visual information</li>
						<li><strong>Clinical significance:</strong> Fundamental to many cognitive processes and daily activities</li>
						<li><strong>MS connection:</strong> Processing speed is often affected in MS, making this training valuable</li>
						<li><strong>Improvement:</strong> Regular practice can enhance your brain's processing efficiency</li>
					</ul>
				</div>
			</div>

			{#if results.adaptation_reason}
				<div class="adaptation-info">
					<h4>📊 Next Session</h4>
					<p>{results.adaptation_reason}</p>
					{#if results.difficulty_after > results.difficulty_before}
						<p class="difficulty-change increase">Difficulty increased: {results.difficulty_before} → {results.difficulty_after}</p>
					{:else if results.difficulty_after < results.difficulty_before}
						<p class="difficulty-change decrease">Difficulty decreased: {results.difficulty_before} → {results.difficulty_after}</p>
					{:else}
						<p class="difficulty-change same">Difficulty maintained at level {results.difficulty_after}</p>
					{/if}
				</div>
			{/if}

			{#if results.new_badges && results.new_badges.length > 0}
				<div class="new-badges">
					<h3>🏆 New Badges Earned!</h3>
					<div class="badge-list">
						{#each results.new_badges as badge}
							<div class="badge-item">
								<span class="badge-icon">{badge.icon}</span>
								<div class="badge-info">
									<div class="badge-name">{badge.name}</div>
									<div class="badge-description">{badge.description}</div>
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}

			<div class="action-buttons">
				<button class="primary-btn" on:click={returnToDashboard}>
					Return to Dashboard
				</button>
			</div>
		</div>
	{/if}
</div>

{#if showHelp}
	<div class="modal-overlay" on:click={() => showHelp = false} on:keydown={(e) => e.key === 'Escape' && (showHelp = false)} role="button" tabindex="0">
		<div class="modal-content" on:click|stopPropagation on:keydown role="dialog" tabindex="-1">
			<div class="modal-header">
				<h2>📖 Inspection Time - Detailed Information</h2>
				<button class="close-btn" on:click={() => showHelp = false}>✕</button>
			</div>
			
			<div class="modal-body">
				<section>
					<h3>What is Inspection Time?</h3>
					<p>Inspection Time is a classic cognitive measure that assesses the minimum time needed to perceive and discriminate between simple visual stimuli. It measures pure perceptual processing speed, independent of motor response speed.</p>
				</section>

				<section>
					<h3>Why Brief Presentation?</h3>
					<p>The very short presentation time (50-200ms) ensures we're measuring your brain's raw perceptual speed, not your ability to study the image. The immediate mask prevents you from using afterimages or iconic memory, focusing purely on perception.</p>
				</section>

				<section>
					<h3>Clinical Relevance</h3>
					<ul>
						<li><strong>Cognitive Aging:</strong> Perceptual speed slows with age and in neurological conditions</li>
						<li><strong>Processing Speed:</strong> Fundamental to attention, memory, and executive functions</li>
						<li><strong>MS Research:</strong> Processing speed deficits are common in MS</li>
						<li><strong>Training Effects:</strong> Regular practice can improve perceptual efficiency</li>
					</ul>
				</section>

				<section>
					<h3>Strategies for Success</h3>
					<ol>
						<li><strong>Relax:</strong> Tension doesn't help - stay calm and trust your perception</li>
						<li><strong>Focus:</strong> Keep your eyes on the center fixation point</li>
						<li><strong>First Impression:</strong> Go with your gut - don't overthink</li>
						<li><strong>Practice:</strong> Your brain will adapt to the brief presentations</li>
						<li><strong>Acceptance:</strong> Some trials are genuinely at your perceptual threshold</li>
						<li><strong>Consistency:</strong> Maintain steady focus throughout the session</li>
					</ol>
				</section>

				<section>
					<h3>Understanding Your Results</h3>
					<p><strong>Perceptual Speed Index:</strong> Combines accuracy with presentation time to measure processing efficiency. Higher scores indicate faster, more accurate perception.</p>
					<p><strong>Adaptive Difficulty:</strong> The task adjusts to find your optimal challenge level, ensuring effective training.</p>
				</section>
			</div>

			<div class="modal-footer">
				<button class="primary-btn" on:click={() => showHelp = false}>Got It!</button>
			</div>
		</div>
	</div>
{/if}

<style>
	.task-container {
		max-width: 1000px;
		margin: 0 auto;
		padding: 2rem;
		min-height: 100vh;
	}

	.loading-state, .error-state {
		text-align: center;
		padding: 4rem 2rem;
	}

	.spinner {
		width: 50px;
		height: 50px;
		border: 4px solid rgba(99, 102, 241, 0.1);
		border-top-color: #6366f1;
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin: 0 auto 1rem;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	/* Instructions Panel */
	.instructions-panel {
		background: white;
		border-radius: 16px;
		padding: 2.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
	}

	.task-header {
		text-align: center;
		margin-bottom: 2rem;
	}

	.task-header h1 {
		font-size: 2.5rem;
		color: #1f2937;
		margin-bottom: 0.5rem;
	}

	.task-subtitle {
		font-size: 1.1rem;
		color: #6b7280;
	}

	.clinical-context {
		background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
		border-left: 4px solid #0ea5e9;
		padding: 1.5rem;
		border-radius: 8px;
		margin-bottom: 2rem;
	}

	.clinical-context h3 {
		color: #0c4a6e;
		margin-bottom: 1rem;
	}

	.ms-benefits {
		margin-top: 1rem;
		padding: 1rem;
		background: rgba(255, 255, 255, 0.7);
		border-radius: 8px;
	}

	.ms-benefits h4 {
		color: #0369a1;
		margin-bottom: 0.75rem;
	}

	.ms-benefits ul {
		list-style: none;
		padding: 0;
	}

	.ms-benefits li {
		padding: 0.4rem 0;
		color: #374151;
	}

	.research-note {
		margin-top: 1rem;
		padding: 1rem;
		background: rgba(245, 208, 254, 0.3);
		border-radius: 8px;
		font-size: 0.95rem;
		color: #581c87;
	}

	.how-it-works {
		margin-bottom: 2rem;
	}

	.how-it-works h3 {
		color: #1f2937;
		margin-bottom: 1.5rem;
	}

	.instruction-steps {
		display: grid;
		gap: 1.5rem;
		margin-bottom: 1.5rem;
	}

	.step {
		display: flex;
		gap: 1rem;
		align-items: start;
		padding: 1rem;
		background: #f9fafb;
		border-radius: 8px;
		border: 2px solid #e5e7eb;
	}

	.step-number {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 40px;
		height: 40px;
		background: linear-gradient(135deg, #6366f1, #8b5cf6);
		color: white;
		border-radius: 50%;
		font-weight: bold;
		flex-shrink: 0;
	}

	.step-content h4 {
		color: #374151;
		margin-bottom: 0.25rem;
	}

	.step-content p {
		color: #6b7280;
		font-size: 0.95rem;
	}

	.important-note {
		background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
		border-left: 4px solid #f59e0b;
		padding: 1rem 1.5rem;
		border-radius: 8px;
		color: #78350f;
	}

	.instruction-tips {
		margin-bottom: 2rem;
	}

	.instruction-tips h3 {
		color: #1f2937;
		margin-bottom: 1rem;
	}

	.instruction-tips ul {
		list-style: none;
		padding: 0;
	}

	.instruction-tips li {
		padding: 0.6rem 0;
		padding-left: 1.75rem;
		position: relative;
		color: #374151;
	}

	.instruction-tips li::before {
		content: "→";
		position: absolute;
		left: 0;
		color: #6366f1;
		font-weight: bold;
	}

	.action-buttons {
		display: flex;
		gap: 1rem;
		justify-content: center;
		margin-top: 2rem;
	}

	.primary-btn {
		background: linear-gradient(135deg, #6366f1, #8b5cf6);
		color: white;
		border: none;
		padding: 1rem 2.5rem;
		font-size: 1.1rem;
		border-radius: 12px;
		cursor: pointer;
		font-weight: 600;
		transition: all 0.3s ease;
		box-shadow: 0 4px 6px rgba(99, 102, 241, 0.3);
	}

	.primary-btn:hover {
		transform: translateY(-2px);
		box-shadow: 0 6px 12px rgba(99, 102, 241, 0.4);
	}

	.help-btn {
		background: white;
		color: #6366f1;
		border: 2px solid #6366f1;
		padding: 1rem 2rem;
		font-size: 1.1rem;
		border-radius: 12px;
		cursor: pointer;
		font-weight: 600;
		transition: all 0.3s ease;
	}

	.help-btn:hover {
		background: #f0f9ff;
	}

	/* Practice Panel */
	.practice-panel {
		background: white;
		border-radius: 16px;
		padding: 2.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
		text-align: center;
	}

	.practice-panel h2 {
		color: #1f2937;
		margin-bottom: 1rem;
	}

	.practice-intro {
		color: #6b7280;
		margin-bottom: 2rem;
	}

	.practice-info {
		background: #f0f9ff;
		padding: 1.5rem;
		border-radius: 8px;
		margin-bottom: 2rem;
	}

	.start-trial-btn {
		background: linear-gradient(135deg, #10b981, #059669);
		color: white;
		border: none;
		padding: 1.25rem 3rem;
		font-size: 1.2rem;
		border-radius: 12px;
		cursor: pointer;
		font-weight: 600;
		transition: all 0.3s ease;
		box-shadow: 0 4px 6px rgba(16, 185, 129, 0.3);
	}

	.start-trial-btn:hover {
		transform: translateY(-2px);
		box-shadow: 0 6px 12px rgba(16, 185, 129, 0.4);
	}

	.practice-complete {
		background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
		padding: 2rem;
		border-radius: 12px;
		border: 2px solid #10b981;
	}

	.practice-complete h3 {
		color: #065f46;
		margin-bottom: 1rem;
	}

	.practice-complete p {
		color: #064e3b;
		margin-bottom: 0.75rem;
	}

	/* Test Panel */
	.test-panel {
		background: white;
		border-radius: 16px;
		padding: 2rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
		min-height: 600px;
	}

	.test-header {
		margin-bottom: 2rem;
	}

	.progress-info {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		flex-wrap: wrap;
		gap: 1rem;
	}

	.trials-remaining {
		display: flex;
		align-items: center;
		gap: 1rem;
		background: linear-gradient(135deg, #8b5cf6, #7c3aed);
		padding: 0.75rem 1.5rem;
		border-radius: 12px;
		box-shadow: 0 4px 6px rgba(139, 92, 246, 0.3);
	}

	.remaining-label {
		color: rgba(255, 255, 255, 0.9);
		font-size: 0.9rem;
		font-weight: 500;
	}

	.remaining-value {
		background: rgba(255, 255, 255, 0.25);
		color: white;
		padding: 0.4rem 1rem;
		border-radius: 8px;
		font-weight: bold;
		font-size: 1.3rem;
		min-width: 50px;
		text-align: center;
	}

	.presentation-info {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		background: linear-gradient(135deg, #f97316, #ea580c);
		padding: 0.75rem 1.5rem;
		border-radius: 12px;
		box-shadow: 0 4px 6px rgba(249, 115, 22, 0.3);
	}

	.info-label {
		color: rgba(255, 255, 255, 0.9);
		font-size: 0.9rem;
		font-weight: 500;
	}

	.info-value {
		background: rgba(255, 255, 255, 0.25);
		color: white;
		padding: 0.4rem 1rem;
		border-radius: 8px;
		font-weight: bold;
		font-size: 1.1rem;
	}

	.progress-bar {
		width: 100%;
		height: 8px;
		background: #e5e7eb;
		border-radius: 4px;
		overflow: hidden;
	}

	.progress-fill {
		height: 100%;
		background: linear-gradient(90deg, #6366f1, #8b5cf6);
		transition: width 0.3s ease;
	}

	/* Stimulus Area */
	.stimulus-area {
		display: flex;
		align-items: center;
		justify-content: center;
		min-height: 400px;
		position: relative;
	}

	.lines-container {
		display: flex;
		align-items: flex-end;
		gap: 80px;
		justify-content: center;
	}

	.line {
		background: #1f2937;
		border-radius: 4px;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
	}

	.spacer {
		width: 80px;
	}

	.mask-pattern {
		width: 300px;
		height: 300px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.mask-grid {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		gap: 8px;
		width: 100%;
		height: 100%;
	}

	.mask-cell {
		background: repeating-linear-gradient(
			45deg,
			#1f2937,
			#1f2937 10px,
			#6b7280 10px,
			#6b7280 20px
		);
		border-radius: 4px;
		animation: maskFlicker 0.1s infinite;
	}

	@keyframes maskFlicker {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.7; }
	}

	.waiting-state {
		text-align: center;
	}

	.fixation-cross {
		font-size: 4rem;
		color: #6b7280;
		font-weight: bold;
		margin-bottom: 1rem;
	}

	.waiting-state p {
		color: #9ca3af;
		font-size: 1.1rem;
	}

	/* Response Area */
	.response-area {
		text-align: center;
	}

	.response-prompt {
		font-size: 1.5rem;
		color: #1f2937;
		margin-bottom: 2rem;
		font-weight: 600;
	}

	.response-buttons {
		display: flex;
		gap: 2rem;
		justify-content: center;
	}

	.response-btn {
		padding: 1.5rem 3rem;
		font-size: 1.3rem;
		font-weight: bold;
		border: none;
		border-radius: 12px;
		cursor: pointer;
		transition: all 0.3s ease;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
		min-width: 180px;
	}

	.left-btn {
		background: linear-gradient(135deg, #3b82f6, #2563eb);
		color: white;
	}

	.left-btn:hover {
		transform: translateY(-3px);
		box-shadow: 0 6px 12px rgba(59, 130, 246, 0.4);
	}

	.right-btn {
		background: linear-gradient(135deg, #10b981, #059669);
		color: white;
	}

	.right-btn:hover {
		transform: translateY(-3px);
		box-shadow: 0 6px 12px rgba(16, 185, 129, 0.4);
	}

	/* Results Panel */
	.results-panel {
		background: white;
		border-radius: 16px;
		padding: 2.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
	}

	.results-header {
		text-align: center;
		margin-bottom: 2rem;
	}

	.results-header h2 {
		color: #1f2937;
		margin-bottom: 1rem;
	}

	.performance-badge {
		display: inline-block;
		padding: 0.75rem 2rem;
		border-radius: 12px;
		font-weight: bold;
		font-size: 1.2rem;
		text-transform: uppercase;
		letter-spacing: 1px;
	}

	.performance-badge.excellent {
		background: linear-gradient(135deg, #10b981, #059669);
		color: white;
	}

	.performance-badge.very-good {
		background: linear-gradient(135deg, #3b82f6, #2563eb);
		color: white;
	}

	.performance-badge.good {
		background: linear-gradient(135deg, #8b5cf6, #7c3aed);
		color: white;
	}

	.performance-badge.average {
		background: linear-gradient(135deg, #f59e0b, #d97706);
		color: white;
	}

	.performance-badge.needs-practice {
		background: linear-gradient(135deg, #ef4444, #dc2626);
		color: white;
	}

	.metrics-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1.5rem;
		margin-bottom: 2rem;
	}

	.metric-card {
		background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
		padding: 1.5rem;
		border-radius: 12px;
		text-align: center;
		border: 2px solid #e5e7eb;
		transition: all 0.3s ease;
	}

	.metric-card:hover {
		transform: translateY(-3px);
		box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
	}

	.metric-card.primary {
		background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
		border-color: #0ea5e9;
	}

	.metric-icon {
		font-size: 2rem;
		margin-bottom: 0.5rem;
	}

	.metric-value {
		font-size: 2.5rem;
		font-weight: bold;
		color: #1f2937;
		margin-bottom: 0.5rem;
	}

	.metric-label {
		font-size: 1rem;
		color: #6b7280;
		font-weight: 600;
		margin-bottom: 0.25rem;
	}

	.metric-detail {
		font-size: 0.85rem;
		color: #9ca3af;
	}

	.interpretation-section {
		background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
		padding: 2rem;
		border-radius: 12px;
		margin-bottom: 2rem;
		border-left: 4px solid #0ea5e9;
	}

	.interpretation-section h3 {
		color: #0c4a6e;
		margin-bottom: 1rem;
	}

	.interpretation-text {
		color: #374151;
		line-height: 1.7;
		margin-bottom: 1.5rem;
	}

	.perceptual-context {
		background: rgba(255, 255, 255, 0.7);
		padding: 1.5rem;
		border-radius: 8px;
	}

	.perceptual-context h4 {
		color: #0369a1;
		margin-bottom: 1rem;
	}

	.perceptual-context ul {
		list-style: none;
		padding: 0;
	}

	.perceptual-context li {
		padding: 0.5rem 0;
		color: #374151;
	}

	.adaptation-info {
		background: #f9fafb;
		padding: 1.5rem;
		border-radius: 8px;
		border: 2px solid #e5e7eb;
		margin-bottom: 2rem;
	}

	.adaptation-info h4 {
		color: #1f2937;
		margin-bottom: 0.75rem;
	}

	.difficulty-change {
		font-weight: 600;
		margin-top: 0.75rem;
	}

	.difficulty-change.increase {
		color: #dc2626;
	}

	.difficulty-change.decrease {
		color: #059669;
	}

	.difficulty-change.same {
		color: #6b7280;
	}

	.new-badges {
		background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
		padding: 2rem;
		border-radius: 12px;
		border: 2px solid #f59e0b;
		margin-bottom: 2rem;
	}

	.new-badges h3 {
		color: #78350f;
		margin-bottom: 1.5rem;
	}

	.badge-list {
		display: grid;
		gap: 1rem;
	}

	.badge-item {
		display: flex;
		gap: 1rem;
		align-items: center;
		background: rgba(255, 255, 255, 0.7);
		padding: 1rem;
		border-radius: 8px;
	}

	.badge-icon {
		font-size: 2rem;
	}

	.badge-name {
		font-weight: bold;
		color: #78350f;
		margin-bottom: 0.25rem;
	}

	.badge-description {
		color: #92400e;
		font-size: 0.9rem;
	}

	/* Modal */
	.modal-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.6);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: 1rem;
	}

	.modal-content {
		background: white;
		border-radius: 16px;
		max-width: 700px;
		width: 100%;
		max-height: 90vh;
		overflow-y: auto;
		box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
	}

	.modal-header {
		padding: 2rem;
		border-bottom: 2px solid #e5e7eb;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.modal-header h2 {
		color: #1f2937;
		margin: 0;
	}

	.close-btn {
		background: none;
		border: none;
		font-size: 1.5rem;
		color: #6b7280;
		cursor: pointer;
		padding: 0.5rem;
		transition: color 0.3s ease;
	}

	.close-btn:hover {
		color: #1f2937;
	}

	.modal-body {
		padding: 2rem;
	}

	.modal-body section {
		margin-bottom: 2rem;
	}

	.modal-body h3 {
		color: #1f2937;
		margin-bottom: 1rem;
	}

	.modal-body p {
		color: #374151;
		line-height: 1.7;
		margin-bottom: 1rem;
	}

	.modal-body ul, .modal-body ol {
		color: #374151;
		line-height: 1.7;
		padding-left: 1.5rem;
	}

	.modal-body li {
		margin-bottom: 0.5rem;
	}

	.modal-footer {
		padding: 1.5rem 2rem;
		border-top: 2px solid #e5e7eb;
		text-align: center;
	}

	/* Responsive */
	@media (max-width: 768px) {
		.task-container {
			padding: 1rem;
		}

		.instructions-panel, .practice-panel, .test-panel, .results-panel {
			padding: 1.5rem;
		}

		.response-buttons {
			flex-direction: column;
			gap: 1rem;
		}

		.response-btn {
			width: 100%;
		}

		.lines-container {
			gap: 40px;
		}

		.metrics-grid {
			grid-template-columns: 1fr;
		}

		.progress-info {
			flex-direction: column;
		}
	}
</style>

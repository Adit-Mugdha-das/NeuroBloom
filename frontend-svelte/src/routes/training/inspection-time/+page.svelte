<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
	import { locale } from '$lib/i18n';
	import { user } from '$lib/stores.js';
	import { getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
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
	/** @type {"practice" | "recorded"} */
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';

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
		/** @type {"practice" | "recorded"} */
		const practiceMode = TASK_PLAY_MODE.PRACTICE;
		playMode = practiceMode;
		practiceStatusMessage = '';
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

	function finishPractice() {
		playMode = TASK_PLAY_MODE.RECORDED;
		showStimulus = false;
		showMask = false;
		waitingForResponse = false;
		showPractice = false;
		practiceComplete = false;
		showInstructions = true;
		practiceStatusMessage = getPracticeCopy($locale).complete;
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
				finishPractice();
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
		playMode = TASK_PLAY_MODE.RECORDED;
		practiceStatusMessage = '';
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

<div class="it-container" data-localize-skip>
	<div class="it-inner">
		{#if loading}
			<LoadingSkeleton variant="card" count={3} />

		{:else if error}
			<div class="screen-card error-screen">
				<h2>Error</h2>
				<p>{error}</p>
				<button class="start-button" on:click={returnToDashboard}>Return to Dashboard</button>
			</div>

		{:else if showInstructions}
			<div class="instructions-card">
				<div class="header-content">
					<div class="title-row">
						<h1>Inspection Time</h1>
						<DifficultyBadge difficulty={sessionData?.difficulty || 5} domain="Processing Speed" />
					</div>
					<p class="subtitle">How fast can your brain perceive a brief visual flash?</p>
					<div class="classic-badge">Inspection Time · Vickers & Smith (1986) · Pure Perceptual Speed</div>
				</div>

				{#if practiceStatusMessage}
					<div class="practice-note">{practiceStatusMessage}</div>
				{/if}

				<div class="task-concept">
					<h3>The Challenge</h3>
					<p>Two vertical lines flash on screen for a <strong>fraction of a second</strong> — then a mask covers them. Your job: say which line was <strong>longer</strong> (left or right). No motor tricks — pure perception.</p>
					<div class="demo-lines">
						<div class="demo-line-col">
							<div class="demo-line" style="height: 64px;"></div>
							<span class="demo-line-label">LEFT</span>
						</div>
						<div class="demo-vs">vs</div>
						<div class="demo-line-col">
							<div class="demo-line" style="height: 48px;"></div>
							<span class="demo-line-label">RIGHT</span>
						</div>
					</div>
					<div class="demo-answer-row">
						<span class="demo-ans-same">← LEFT is longer</span>
					</div>
				</div>

				<div class="rules-grid">
					<div class="rule-card">
						<span class="rule-icon">Look</span>
						<div class="rule-text">
							<strong>Step 1: Watch</strong>
							<span>Two lines flash very briefly — as short as 50ms</span>
						</div>
					</div>
					<div class="rule-card">
						<span class="rule-icon">▣</span>
						<div class="rule-text">
							<strong>Step 2: Mask</strong>
							<span>A pattern mask immediately covers the lines</span>
						</div>
					</div>
					<div class="rule-card">
						<span class="rule-icon">↔</span>
						<div class="rule-text">
							<strong>Step 3: Decide</strong>
							<span>Which line was longer — LEFT or RIGHT?</span>
						</div>
					</div>
					<div class="rule-card">
						<span class="rule-icon">↺</span>
						<div class="rule-text">
							<strong>Step 4: Repeat</strong>
							<span>Keep going for all {sessionData?.total_trials || 20} trials</span>
						</div>
					</div>
				</div>

				<div class="info-grid">
					<div class="info-section">
						<h4>Perception Tips</h4>
						<ul class="tips-list">
							<li><strong>Stay relaxed:</strong> Tension reduces perceptual sensitivity</li>
							<li><strong>Central focus:</strong> Keep eyes on the screen centre before each trial</li>
							<li><strong>Trust instincts:</strong> Go with your first impression — don't overthink</li>
							<li><strong>It's OK to guess:</strong> Some trials are genuinely at your threshold</li>
						</ul>
					</div>
					<div class="info-section">
						<h4>Test Format</h4>
						<ul class="structure-list">
							<li><span class="struct-key">Trials</span><span class="struct-val">{sessionData?.total_trials || 20}</span></li>
							<li><span class="struct-key">Flash duration</span><span class="struct-val">{sessionData?.config?.presentation_time_ms || 100}ms</span></li>
							<li><span class="struct-key">Mask duration</span><span class="struct-val">{sessionData?.config?.mask_duration_ms || 500}ms</span></li>
							<li><span class="struct-key">Measures</span><span class="struct-val">perceptual speed</span></li>
						</ul>
					</div>
				</div>

				<div class="clinical-info">
					<h4>Clinical Significance</h4>
					<div class="clinical-grid">
						<div class="clinical-item">
							<strong>Pure Perception</strong>
							<span>Measures basic visual processing speed — no motor component</span>
						</div>
						<div class="clinical-item">
							<strong>MS Sensitive</strong>
							<span>Processing speed is one of the most affected domains in MS</span>
						</div>
						<div class="clinical-item">
							<strong>No Motor Bias</strong>
							<span>Physical limitations don't affect this measure</span>
						</div>
						<div class="clinical-item">
							<strong>Research Backed</strong>
							<span>Vickers & Smith (1986), widely used in neuropsychology</span>
						</div>
					</div>
				</div>

				<div class="perf-guide">
					<h4>Performance Targets</h4>
					<div class="norm-bars">
						<div class="norm-bar norm-excellent">
							<span class="norm-label">Excellent</span>
							<span class="norm-val">≥90% accuracy</span>
						</div>
						<div class="norm-bar norm-good">
							<span class="norm-label">Good</span>
							<span class="norm-val">75–89% accuracy</span>
						</div>
						<div class="norm-bar norm-avg">
							<span class="norm-label">Average</span>
							<span class="norm-val">60–74% accuracy</span>
						</div>
						<div class="norm-bar norm-fair">
							<span class="norm-label">Fair</span>
							<span class="norm-val">50–59% accuracy</span>
						</div>
						<div class="norm-bar norm-needs">
							<span class="norm-label">Developing</span>
							<span class="norm-val">&lt;50% accuracy</span>
						</div>
					</div>
					<p class="norm-note">*Scores depend on presentation time — faster flash = harder task</p>
				</div>

				<div class="button-group">
					<button class="btn-secondary" on:click={startPractice}>Try Practice First</button>
					<TaskPracticeActions
						locale={$locale}
						startLabel="Start Actual Task"
						practiceVisible={false}
						statusMessage={practiceStatusMessage}
						align="center"
						on:start={startTest}
					/>
				</div>
			</div>

		{:else if showPractice}
			<div class="screen-card practice-screen">
				<PracticeModeBanner locale={$locale} />
				<h2>Practice Mode</h2>
				<p class="practice-intro">Practice with a slower flash to get familiar with the task.</p>

				<div class="practice-info-row">
					<span class="p-badge">Trial {practiceAttempts + 1}</span>
					<span class="p-badge p-speed">Flash: {practiceTrial.presentation_time_ms}ms (slower than real test)</span>
				</div>

				{#if !showStimulus && !showMask && !waitingForResponse}
					<div class="practice-ready">
						<p>Focus on the centre of the screen, then click when ready.</p>
						<button class="start-button" on:click={runPracticeTrial}>Ready — Start Trial</button>
					</div>
				{/if}

				{#if showStimulus}
					<div class="stimulus-area">
						<div class="lines-container">
							<div class="line" style="height: {practiceTrial.left_height}px; width: {practiceTrial.line_width}px;"></div>
							<div class="spacer"></div>
							<div class="line" style="height: {practiceTrial.right_height}px; width: {practiceTrial.line_width}px;"></div>
						</div>
					</div>
				{/if}

				{#if showMask}
					<div class="stimulus-area">
						<div class="mask-pattern">
							<div class="mask-grid">
								{#each Array(20) as _, i}
									<div class="mask-cell" style="animation-delay: {i * 20}ms;"></div>
								{/each}
							</div>
						</div>
					</div>
				{/if}

				{#if waitingForResponse}
					<div class="response-area">
						<p class="response-prompt">Which line was longer?</p>
						<div class="response-buttons">
							<button class="response-btn left-btn" on:click={() => handlePracticeResponse('left')}>
								<span class="resp-icon">←</span>
								<span class="resp-text">LEFT</span>
							</button>
							<button class="response-btn right-btn" on:click={() => handlePracticeResponse('right')}>
								<span class="resp-text">RIGHT</span>
								<span class="resp-icon">→</span>
							</button>
						</div>
					</div>
				{/if}
			</div>

		{:else if testStarted}
			<div class="screen-card testing-screen">
				<div class="test-header">
					<div class="test-badges">
						<span class="count-badge">Trial {currentTrialIndex + 1} / {sessionData.total_trials}</span>
						<span class="speed-badge">{sessionData.config.presentation_time_ms}ms flash</span>
					</div>
					<div class="progress-track">
						<div class="progress-fill" style="width: {progressPercent}%"></div>
					</div>
					<button class="help-btn-sm" on:click={() => showHelp = true}>?</button>
				</div>

				<div class="stimulus-area">
					{#if showStimulus}
						<div class="lines-container">
							<div class="line" style="height: {currentTrial.left_height}px; width: {currentTrial.line_width}px;"></div>
							<div class="spacer"></div>
							<div class="line" style="height: {currentTrial.right_height}px; width: {currentTrial.line_width}px;"></div>
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
									<span class="resp-icon">←</span>
									<span class="resp-text">LEFT</span>
								</button>
								<button class="response-btn right-btn" on:click={() => handleResponse('right')}>
									<span class="resp-text">RIGHT</span>
									<span class="resp-icon">→</span>
								</button>
							</div>
						</div>
					{:else}
						<div class="waiting-state">
							<div class="fixation-cross">+</div>
							<p>Get ready…</p>
						</div>
					{/if}
				</div>
			</div>

		{:else if showResults}
			<div class="screen-card complete-screen">
				{#if results}
					<div class="perf-banner">
												<div class="perf-level">{results.metrics.performance_level}</div>
						<div class="perf-subtitle">Perceptual Speed Index: {results.metrics.perceptual_speed_index} · Inspection Time Complete!</div>
					</div>

					<div class="metrics-grid">
						<div class="metric-card highlight">
							<div class="metric-icon">◎</div>
							<div class="metric-value">{results.metrics.accuracy}%</div>
							<div class="metric-label">Accuracy</div>
							<div class="metric-sub">{results.metrics.correct_count}/{results.metrics.total_trials} correct</div>
						</div>
						<div class="metric-card">
							<div class="metric-icon">→</div>
							<div class="metric-value">{results.metrics.perceptual_speed_index}</div>
							<div class="metric-label">Perceptual Speed Index</div>
							<div class="metric-sub">at {results.metrics.presentation_time_ms}ms flash</div>
						</div>
						<div class="metric-card">
							<div class="metric-icon">⏱</div>
							<div class="metric-value">{results.metrics.average_reaction_time}ms</div>
							<div class="metric-label">Avg Decision Time</div>
							<div class="metric-sub">after mask appears</div>
						</div>
						<div class="metric-card">
							<div class="metric-icon">↑</div>
							<div class="metric-value">{results.metrics.consistency}%</div>
							<div class="metric-label">Consistency</div>
							<div class="metric-sub">response variability</div>
						</div>
					</div>

					<div class="breakdown">
						<h3>Detailed Analysis</h3>
						<div class="breakdown-row">
							<span class="bd-label">Total Trials</span>
							<span class="bd-val">{results.metrics.total_trials}</span>
						</div>
						<div class="breakdown-row">
							<span class="bd-label">Correct Answers</span>
							<span class="bd-val bd-success">{results.metrics.correct_count}</span>
						</div>
						<div class="breakdown-row">
							<span class="bd-label">Presentation Time</span>
							<span class="bd-val">{results.metrics.presentation_time_ms}ms</span>
						</div>
						<div class="breakdown-row">
							<span class="bd-label">Perceptual Speed Index</span>
							<span class="bd-val">{results.metrics.perceptual_speed_index}</span>
						</div>
						<div class="breakdown-row">
							<span class="bd-label">Consistency</span>
							<span class="bd-val">{results.metrics.consistency}%</span>
						</div>
						<div class="breakdown-row">
							<span class="bd-label">Performance Level</span>
							<span class="bd-val">{results.metrics.performance_level}</span>
						</div>
					</div>

					<div class="clinical-note">
						<h4>Clinical Context</h4>
						<p>
							{#if results.metrics.accuracy >= 90}
								Excellent perceptual speed! You're accurately processing visual information at <strong>{results.metrics.presentation_time_ms}ms</strong> — significantly below the average conscious perception threshold.
							{:else if results.metrics.accuracy >= 75}
								Good perceptual processing. You're reliably perceiving brief flashes at <strong>{results.metrics.presentation_time_ms}ms</strong>. Regular practice can push your threshold even lower.
							{:else if results.metrics.accuracy >= 60}
								Average perceptual speed at this duration. Your brain is working at its threshold — precision will improve with training.
							{:else}
								You're developing perceptual speed at this threshold. The task adapts to find your optimal level — keep practising and improvement will follow.
							{/if}
						</p>
						<p class="why-matters"><strong>Why this matters for MS:</strong> Processing speed deficits are among the most common cognitive changes in MS. This task measures pure visual perception speed without any motor demands, making it ideal for tracking brain efficiency over time.</p>
					</div>

					{#if results.adaptation_reason}
						<div class="difficulty-info">
							<span>Difficulty: <strong>{results.difficulty_before}</strong> → <strong>{results.difficulty_after}</strong></span>
							<span class="adapt-reason">{results.adaptation_reason}</span>
						</div>
					{/if}

					{#if results.new_badges && results.new_badges.length > 0}
						<BadgeNotification badges={results.new_badges} />
					{/if}

					<div class="button-group">
						<button class="start-button" on:click={returnToDashboard}>Return to Dashboard</button>
						<button class="btn-secondary" on:click={() => goto('/training')}>Back to Training</button>
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>

{#if showHelp}
	<div class="modal-overlay" on:click={() => showHelp = false} role="presentation">
		<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
		<div class="modal-content" on:click|stopPropagation role="dialog" tabindex="-1" on:keydown={(e) => e.key === 'Escape' && (showHelp = false)}>
			<button class="close-btn" on:click={() => showHelp = false}>×</button>
			<h2>Inspection Time — Strategies</h2>
			<div class="strategy">
				<h3>Stay Relaxed</h3>
				<p>Tension and anxiety physically reduce perceptual sensitivity. Take a breath before each trial and stay calm — your perception improves when you're relaxed.</p>
			</div>
			<div class="strategy">
				<h3>Central Focus</h3>
				<p>Keep your gaze fixed on the centre of the screen between trials. The lines appear left and right — central focus lets peripheral vision catch both at once.</p>
			</div>
			<div class="strategy">
				<h3>Trust Your First Impression</h3>
				<p>The flash is too brief for conscious analysis. Your first instinct is your perceptual system's best output — trust it rather than deliberating.</p>
			</div>
			<div class="strategy">
				<h3>Why the Mask?</h3>
				<p>The pattern mask immediately after the flash prevents "afterimage" processing. This ensures we're measuring true real-time perception, not memory of the image.</p>
			</div>
			<div class="strategy">
				<h3>Adaptive Difficulty</h3>
				<p>The task adjusts flash duration to find your perceptual threshold. Getting some wrong is expected and scientifically meaningful — not a failure.</p>
			</div>
			<div class="strategy">
				<h3>Why This Matters</h3>
				<p>Inspection Time requires no complex motor responses — just a simple left/right click. This makes it an exceptionally clean measure of pure cognitive processing speed for MS research.</p>
			</div>
		</div>
	</div>
{/if}

<style>
	/* ── Container ─────────────────────────────────────────── */
	.it-container {
		min-height: 100vh;
		background: #C8DEFA;
		padding: 2rem 1rem;
	}

	.it-inner {
		max-width: 960px;
		margin: 0 auto;
	}

	/* ── Instructions card ─────────────────────────────────── */
	.instructions-card {
		background: white;
		border-radius: 16px;
		padding: 2.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07), 0 1px 3px rgba(0, 0, 0, 0.06);
		display: flex;
		flex-direction: column;
		gap: 1.8rem;
	}

	.header-content { text-align: center; }

	.title-row {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		flex-wrap: wrap;
		margin-bottom: 0.5rem;
	}

	.header-content h1 {
		font-size: 1.8rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0;
	}

	.subtitle {
		color: #64748b;
		font-size: 1rem;
		margin: 0.4rem 0 0.8rem;
	}

	.classic-badge {
		display: inline-block;
		background: rgba(102, 126, 234, 0.12);
		color: #667eea;
		border: 1px solid rgba(102, 126, 234, 0.3);
		border-radius: 20px;
		padding: 0.3rem 1rem;
		font-size: 0.82rem;
		font-weight: 600;
	}

	.practice-note {
		background: #fef9c3;
		border: 1px solid #fde047;
		border-radius: 8px;
		padding: 0.75rem 1rem;
		color: #854d0e;
		font-size: 0.9rem;
		text-align: center;
	}

	/* ── Task concept (violet for neural flash) ────────────── */
	.task-concept {
		background: linear-gradient(135deg, #faf5ff, #ede9fe);
		border: 1px solid #c4b5fd;
		border-radius: 12px;
		padding: 1.5rem;
	}

	.task-concept h3 {
		font-size: 1rem;
		font-weight: 700;
		color: #6d28d9;
		margin: 0 0 0.6rem;
	}

	.task-concept p {
		color: #3b0764;
		margin: 0 0 1.2rem;
		line-height: 1.6;
	}

	.demo-lines {
		display: flex;
		align-items: flex-end;
		justify-content: center;
		gap: 2.5rem;
		background: white;
		border-radius: 10px;
		padding: 1.2rem;
		margin-bottom: 1rem;
		box-shadow: 0 2px 8px rgba(0,0,0,0.06);
	}

	.demo-line-col {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}

	.demo-line {
		width: 10px;
		background: #1e293b;
		border-radius: 2px;
	}

	.demo-line-label {
		font-size: 0.82rem;
		font-weight: 700;
		color: #475569;
	}

	.demo-vs {
		font-size: 1.2rem;
		font-weight: 800;
		color: #7c3aed;
		align-self: center;
	}

	.demo-answer-row {
		display: flex;
		justify-content: center;
	}

	.demo-ans-same {
		background: #ede9fe;
		color: #6d28d9;
		padding: 0.35rem 0.9rem;
		border-radius: 8px;
		font-weight: 700;
		font-size: 0.9rem;
	}

	/* ── Rules grid ────────────────────────────────────────── */
	.rules-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}

	.rule-card {
		display: flex;
		align-items: flex-start;
		gap: 0.8rem;
		padding: 1rem;
		background: #f8fafc;
		border-radius: 10px;
		border-left: 4px solid #7c3aed;
	}

	.rule-icon { font-size: 1.5rem; flex-shrink: 0; }
	.rule-text { display: flex; flex-direction: column; gap: 0.2rem; }
	.rule-text strong { font-size: 0.9rem; color: #1e293b; }
	.rule-text span   { font-size: 0.82rem; color: #64748b; line-height: 1.4; }

	/* ── Info grid ─────────────────────────────────────────── */
	.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }

	.info-section { background: #f8fafc; border-radius: 10px; padding: 1.2rem; }
	.info-section h4 { font-size: 0.9rem; font-weight: 700; color: #1e293b; margin: 0 0 0.8rem; }

	.tips-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 0.5rem; }
	.tips-list li { font-size: 0.85rem; color: #475569; line-height: 1.4; }

	.structure-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 0.5rem; }
	.structure-list li {
		display: flex; justify-content: space-between; align-items: center;
		font-size: 0.85rem; padding: 0.3rem 0; border-bottom: 1px solid #e2e8f0;
	}
	.structure-list li:last-child { border-bottom: none; }
	.struct-key { color: #64748b; }
	.struct-val { font-weight: 600; color: #1e293b; }

	/* ── Clinical info ─────────────────────────────────────── */
	.clinical-info {
		background: linear-gradient(135deg, #f0fdf4, #dcfce7);
		border: 1px solid #bbf7d0;
		border-radius: 12px;
		padding: 1.2rem;
	}
	.clinical-info h4 { font-size: 0.9rem; font-weight: 700; color: #166534; margin: 0 0 0.8rem; }
	.clinical-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
	.clinical-item { display: flex; flex-direction: column; gap: 0.2rem; }
	.clinical-item strong { font-size: 0.82rem; color: #166534; }
	.clinical-item span   { font-size: 0.8rem; color: #15803d; }

	/* ── Performance guide ─────────────────────────────────── */
	.perf-guide { background: #f8fafc; border-radius: 12px; padding: 1.2rem; }
	.perf-guide h4 { font-size: 0.9rem; font-weight: 700; color: #1e293b; margin: 0 0 0.8rem; }
	.norm-bars { display: flex; flex-direction: column; gap: 0.4rem; }
	.norm-bar {
		display: flex; justify-content: space-between; align-items: center;
		padding: 0.5rem 0.9rem; border-radius: 6px; font-size: 0.85rem; font-weight: 600;
	}
	.norm-excellent { background: #dcfce7; color: #166534; }
	.norm-good      { background: #d1fae5; color: #065f46; }
	.norm-avg       { background: #fef9c3; color: #854d0e; }
	.norm-fair      { background: #ffedd5; color: #9a3412; }
	.norm-needs     { background: #fee2e2; color: #991b1b; }
	.norm-label { font-weight: 700; }
	.norm-val   { font-weight: 400; font-size: 0.82rem; }
	.norm-note { font-size: 0.78rem; color: #94a3b8; font-style: italic; margin: 0.5rem 0 0; text-align: center; }

	/* ── Button group ──────────────────────────────────────── */
	.button-group {
		display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap; padding-top: 0.5rem;
		align-items: center;
	}

	.start-button {
		background: #4338ca;
		color: white; border: none; border-radius: 10px;
		padding: 0.85rem 2.5rem; font-size: 1rem; font-weight: 700;
		cursor: pointer; transition: transform 0.15s, box-shadow 0.15s;
		box-shadow: 0 4px 14px rgba(67, 56, 202, 0.35);
	}
	.start-button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5); }

	.btn-secondary {
		background: white; color: #667eea;
		border: 2px solid #667eea; border-radius: 10px;
		padding: 0.85rem 2rem; font-size: 1rem; font-weight: 600;
		cursor: pointer; transition: all 0.15s;
	}
	.btn-secondary:hover { background: rgba(102, 126, 234, 0.08); }

	/* ── Screen card ───────────────────────────────────────── */
	.screen-card {
		background: white;
		border-radius: 16px;
		padding: 2.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
	}

	.error-screen { text-align: center; }
	.error-screen h2 { margin: 0 0 0.75rem; color: #dc2626; }
	.error-screen p  { color: #64748b; margin: 0 0 1.5rem; }

	/* ── Practice screen ───────────────────────────────────── */
	.practice-screen { text-align: center; }
	.practice-screen h2 { font-size: 1.6rem; font-weight: 700; color: #1e293b; margin: 0 0 0.5rem; }
	.practice-intro { color: #64748b; margin: 0 0 1.5rem; }

	.practice-info-row { display: flex; gap: 0.75rem; justify-content: center; flex-wrap: wrap; margin-bottom: 1.5rem; }

	.p-badge {
		background: rgba(102, 126, 234, 0.12); color: #667eea;
		padding: 0.4rem 1rem; border-radius: 20px; font-size: 0.85rem; font-weight: 700;
	}
	.p-speed { background: #ede9fe; color: #6d28d9; }

	.practice-ready { margin: 1.5rem 0; }
	.practice-ready p { color: #64748b; margin-bottom: 1rem; }

	/* ── Testing screen ────────────────────────────────────── */
	.testing-screen { padding: 1.5rem; }

	.test-header {
		display: flex; justify-content: space-between; align-items: center;
		margin-bottom: 1.5rem; flex-wrap: wrap; gap: 0.5rem;
	}
	.test-badges { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; flex: 1; }
	.count-badge {
		background: rgba(102, 126, 234, 0.12); color: #667eea;
		padding: 0.4rem 0.9rem; border-radius: 20px; font-size: 0.85rem; font-weight: 700;
	}
	.speed-badge {
		background: #ede9fe; color: #6d28d9;
		padding: 0.4rem 0.9rem; border-radius: 20px; font-size: 0.82rem; font-weight: 600;
	}
	.progress-track {
		flex: 1; height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden; min-width: 80px;
	}
	.progress-fill { height: 100%; background: linear-gradient(90deg, #7c3aed, #a855f7); border-radius: 3px; transition: width 0.3s; }
	.help-btn-sm {
		width: 36px; height: 36px; border-radius: 50%;
		border: 2px solid #667eea; background: white; color: #667eea;
		font-size: 1.1rem; font-weight: 700; cursor: pointer;
		transition: all 0.2s; display: flex; align-items: center; justify-content: center;
	}
	.help-btn-sm:hover { background: #667eea; color: white; }

	/* ── Stimulus area ─────────────────────────────────────── */
	.stimulus-area {
		display: flex;
		justify-content: center;
		align-items: center;
		min-height: 280px;
		background: #f8fafc;
		border-radius: 14px;
		border: 2px solid #e2e8f0;
	}

	.lines-container {
		display: flex;
		align-items: flex-end;
		gap: 4rem;
	}

	.line {
		background: #1e293b;
		border-radius: 3px;
	}

	.spacer { width: 2rem; }

	/* ── Mask pattern ──────────────────────────────────────── */
	.mask-pattern { padding: 1rem; }
	.mask-grid {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		gap: 3px;
		width: 200px;
	}
	.mask-cell {
		width: 36px;
		height: 36px;
		background: #1e293b;
		border-radius: 2px;
		animation: flicker 0.1s step-end infinite;
	}
	@keyframes flicker {
		0%   { opacity: 1; background: #1e293b; }
		25%  { opacity: 0.8; background: #7c3aed; }
		50%  { opacity: 1; background: #1e293b; }
		75%  { opacity: 0.6; background: #475569; }
		100% { opacity: 1; background: #1e293b; }
	}

	/* ── Response area ─────────────────────────────────────── */
	.response-area { text-align: center; }
	.response-prompt {
		font-size: 1.1rem; font-weight: 600; color: #1e293b; margin: 0 0 1.5rem;
	}
	.response-buttons {
		display: flex; gap: 2rem; justify-content: center; flex-wrap: wrap;
	}
	.response-btn {
		display: flex; align-items: center; gap: 0.5rem;
		padding: 1.1rem 2.5rem; border: none; border-radius: 12px;
		font-size: 1.1rem; font-weight: 700; cursor: pointer;
		transition: transform 0.15s, box-shadow 0.15s; min-width: 140px;
	}
	.left-btn  {
		background: linear-gradient(135deg, #7c3aed, #6d28d9);
		color: white; box-shadow: 0 4px 14px rgba(124, 58, 237, 0.4);
	}
	.left-btn:hover  { transform: translateY(-3px); box-shadow: 0 6px 20px rgba(124, 58, 237, 0.55); }
	.right-btn {
		background: linear-gradient(135deg, #a855f7, #9333ea);
		color: white; box-shadow: 0 4px 14px rgba(168, 85, 247, 0.4);
	}
	.right-btn:hover { transform: translateY(-3px); box-shadow: 0 6px 20px rgba(168, 85, 247, 0.55); }
	.resp-icon { font-size: 1.3rem; }
	.resp-text { font-size: 1rem; letter-spacing: 0.06em; }

	/* ── Waiting state ─────────────────────────────────────── */
	.waiting-state { text-align: center; }
	.fixation-cross {
		font-size: 3rem; font-weight: 300; color: #475569; line-height: 1;
		margin-bottom: 0.75rem;
	}
	.waiting-state p { color: #94a3b8; font-size: 0.9rem; margin: 0; }

	/* ── Complete screen ───────────────────────────────────── */
	.complete-screen { display: flex; flex-direction: column; gap: 1.5rem; }

	.perf-banner {
		text-align: center; padding: 1.5rem;
		background: linear-gradient(135deg, #faf5ff, #ede9fe);
		border: 2px solid #c4b5fd; border-radius: 14px;
	}
	.perf-level    { font-size: 1.8rem; font-weight: 800; color: #6d28d9; }
	.perf-subtitle { font-size: 0.95rem; color: #64748b; margin-top: 0.3rem; }

	.metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; }
	.metric-card {
		background: #f8fafc; border: 1px solid #e2e8f0;
		border-radius: 12px; padding: 1.2rem; text-align: center;
	}
	.metric-card.highlight {
		background: linear-gradient(135deg, #7c3aed, #6d28d9);
		color: white; border-color: transparent;
	}
	.metric-icon  { font-size: 1.8rem; margin-bottom: 0.4rem; }
	.metric-value { font-size: 1.8rem; font-weight: 800; color: #1e293b; margin-bottom: 0.2rem; }
	.metric-card.highlight .metric-value,
	.metric-card.highlight .metric-label,
	.metric-card.highlight .metric-sub { color: white; }
	.metric-label { font-size: 0.82rem; font-weight: 600; color: #64748b; }
	.metric-sub   { font-size: 0.78rem; color: #94a3b8; margin-top: 0.2rem; }

	/* ── Breakdown ─────────────────────────────────────────── */
	.breakdown { background: #f8fafc; border-radius: 12px; padding: 1.2rem; }
	.breakdown h3 { font-size: 0.95rem; font-weight: 700; color: #1e293b; margin: 0 0 0.8rem; }
	.breakdown-row {
		display: flex; justify-content: space-between; align-items: center;
		padding: 0.55rem 0; border-bottom: 1px solid #e2e8f0; font-size: 0.9rem;
	}
	.breakdown-row:last-child { border-bottom: none; }
	.bd-label { color: #64748b; }
	.bd-val   { font-weight: 700; color: #667eea; }
	.bd-success { color: #16a34a; }

	/* ── Clinical note ─────────────────────────────────────── */
	.clinical-note {
		background: linear-gradient(135deg, #f0fdf4, #dcfce7);
		border: 1px solid #bbf7d0; border-radius: 12px; padding: 1.2rem;
	}
	.clinical-note h4 { font-size: 0.9rem; font-weight: 700; color: #166534; margin: 0 0 0.5rem; }
	.clinical-note p { font-size: 0.9rem; color: #15803d; line-height: 1.6; margin: 0 0 0.5rem; }
	.clinical-note p:last-child { margin: 0; }
	.why-matters { font-style: italic; }

	/* ── Difficulty info ───────────────────────────────────── */
	.difficulty-info {
		background: #faf5ff; border: 1px solid #c4b5fd; border-radius: 10px;
		padding: 0.9rem 1.2rem; display: flex; justify-content: space-between;
		align-items: center; flex-wrap: wrap; gap: 0.5rem;
		font-size: 0.88rem; font-weight: 600; color: #6d28d9;
	}
	.adapt-reason { color: #a855f7; font-weight: 400; font-style: italic; }

	/* ── Help modal ────────────────────────────────────────── */
	.modal-overlay {
		position: fixed; inset: 0; background: rgba(0,0,0,0.55);
		display: flex; align-items: center; justify-content: center;
		z-index: 1000; padding: 1rem;
	}
	.modal-content {
		background: white; border-radius: 16px; padding: 2rem;
		max-width: 560px; width: 100%; max-height: 80vh; overflow-y: auto;
		position: relative; box-shadow: 0 20px 60px rgba(0,0,0,0.3);
	}
	.close-btn {
		position: absolute; top: 1rem; right: 1rem;
		width: 36px; height: 36px; border: none; background: #f1f5f9;
		color: #475569; font-size: 1.4rem; border-radius: 50%; cursor: pointer;
		display: flex; align-items: center; justify-content: center; transition: background 0.15s;
	}
	.close-btn:hover { background: #e2e8f0; }
	.modal-content h2 {
		font-size: 1.2rem; font-weight: 700; color: #1e293b;
		margin: 0 0 1.2rem; padding-right: 2.5rem;
	}
	.strategy {
		padding: 0.9rem 1rem; background: #f8fafc;
		border-radius: 8px; border-left: 4px solid #7c3aed; margin-bottom: 0.75rem;
	}
	.strategy h3 { font-size: 0.88rem; font-weight: 700; color: #1e293b; margin: 0 0 0.3rem; }
	.strategy p  { font-size: 0.84rem; color: #64748b; margin: 0; line-height: 1.5; }

	/* ── Responsive ────────────────────────────────────────── */
	@media (max-width: 640px) {
		.instructions-card { padding: 1.5rem; gap: 1.2rem; }
		.rules-grid { grid-template-columns: 1fr; }
		.info-grid { grid-template-columns: 1fr; }
		.clinical-grid { grid-template-columns: 1fr; }
		.metrics-grid { grid-template-columns: repeat(2, 1fr); }
		.header-content h1 { font-size: 1.4rem; }
		.screen-card { padding: 1.25rem; }
		.response-btn { padding: 0.85rem 1.5rem; min-width: 110px; }
		.lines-container { gap: 2rem; }
	}
</style>

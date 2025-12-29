<script>
	import { goto } from '$app/navigation';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import { onMount } from 'svelte';

	// Game states
	const STATE_LOADING = 'loading';
	const STATE_INSTRUCTIONS = 'instructions';
	const STATE_READY = 'ready'; // Get ready...
	const STATE_SHOWING = 'showing'; // Display sequence
	const STATE_INPUT = 'input'; // User input
	const STATE_FEEDBACK = 'feedback'; // Show if correct/incorrect
	const STATE_COMPLETE = 'complete'; // Session complete

	let currentState = STATE_LOADING;
	let sessionData = null;
	let currentTrialIndex = 0;
	let currentTrial = null;

	// Display state
	let displayedDigits = [];
	let currentDigitIndex = 0;

	// User input
	let userInput = '';
	let isCorrect = false;
	let trialStartTime = 0;

	// Results
	let completedTrials = [];
	let sessionResults = null;
	let newBadges = [];

	// UI state
	let showHelp = false;
	let currentDifficulty = 5;

	// Timing - adjusts based on difficulty
	function getDisplayTime(difficulty) {
		// Higher difficulty = faster presentation
		// Level 1-3: 1800ms, 4-6: 1400ms, 7-10: 1000ms
		if (difficulty <= 3) return 1800;
		if (difficulty <= 6) return 1400;
		return 1000;
	}

	function getInterDigitInterval(difficulty) {
		if (difficulty <= 3) return 800;
		if (difficulty <= 6) return 600;
		return 400;
	}

	let DIGIT_DISPLAY_TIME = 1500;
	let INTER_DIGIT_INTERVAL = 700;
	const READY_DISPLAY_TIME = 2000;

	onMount(async () => {
		await loadSession();
	});

	async function loadSession() {
		try {
			const userData = JSON.parse(localStorage.getItem('user') || '{}');
			const userId = userData.id;

			if (!userId) {
				goto('/login');
				return;
			}

			// Get user's current difficulty from their training plan
			const planRes = await fetch(`http://localhost:8000/training/plan/${userId}`);
			const plan = await planRes.json();

			let difficulty = 5; // Default
			if (plan && plan.current_difficulty) {
				const currentDiff =
					typeof plan.current_difficulty === 'string'
						? JSON.parse(plan.current_difficulty)
						: plan.current_difficulty;
				difficulty = currentDiff.working_memory || 5;
			}

			// Update timing based on difficulty
			currentDifficulty = difficulty;
			DIGIT_DISPLAY_TIME = getDisplayTime(difficulty);
			INTER_DIGIT_INTERVAL = getInterDigitInterval(difficulty);

			// Generate session
			const res = await fetch(
				`http://localhost:8000/training/tasks/digit-span/generate/${userId}?difficulty=${difficulty}&num_trials=8`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' }
				}
			);

			if (!res.ok) throw new Error('Failed to load session');

			sessionData = await res.json();
			currentState = STATE_INSTRUCTIONS;
		} catch (error) {
			console.error('Error loading session:', error);
			alert('Failed to load training session');
			goto('/dashboard');
		}
	}

	function startSession() {
		currentState = STATE_READY;
		currentTrialIndex = 0;
		completedTrials = [];
		startTrial();
	}

	function startTrial() {
		currentTrial = sessionData.trials[currentTrialIndex];

		// Show "Get ready" screen
		currentState = STATE_READY;

		setTimeout(() => {
			// Start showing sequence
			currentState = STATE_SHOWING;
			displayedDigits = [];
			currentDigitIndex = 0;
			showNextDigit();
		}, READY_DISPLAY_TIME);
	}

	function showNextDigit() {
		if (currentDigitIndex < currentTrial.sequence.length) {
			// Add digit to display
			displayedDigits = [...displayedDigits, currentTrial.sequence[currentDigitIndex]];

			setTimeout(() => {
				// Clear digit
				displayedDigits = [...displayedDigits.slice(0, -1), ''];

				setTimeout(() => {
					currentDigitIndex++;
					showNextDigit();
				}, INTER_DIGIT_INTERVAL);
			}, DIGIT_DISPLAY_TIME);
		} else {
			// All digits shown, switch to input
			setTimeout(() => {
				currentState = STATE_INPUT;
				userInput = '';
				trialStartTime = Date.now();
			}, INTER_DIGIT_INTERVAL);
		}
	}

	function submitResponse() {
		if (!userInput.trim()) return;

		const reactionTime = Date.now() - trialStartTime;

		// Parse user input (expecting space-separated or just concatenated digits)
		const userDigits = userInput
			.trim()
			.split(/[\s,]+/)
			.map((d) => parseInt(d))
			.filter((d) => !isNaN(d));

		// Check if correct
		const expectedSequence =
			currentTrial.span_type === 'forward'
				? currentTrial.sequence
				: [...currentTrial.sequence].reverse();

		isCorrect =
			userDigits.length === expectedSequence.length &&
			userDigits.every((d, i) => d === expectedSequence[i]);

		// Save trial result
		const trialResult = {
			...currentTrial,
			user_response: userDigits,
			reaction_time: reactionTime,
			correct: isCorrect
		};

		completedTrials.push(trialResult);

		// Show feedback
		currentState = STATE_FEEDBACK;

		// Move to next trial or complete
		setTimeout(() => {
			currentTrialIndex++;

			if (currentTrialIndex < sessionData.trials.length) {
				startTrial();
			} else {
				completeSession();
			}
		}, 1500);
	}

	async function completeSession() {
		currentState = STATE_LOADING;

		try {
			const userData = JSON.parse(localStorage.getItem('user') || '{}');
			const userId = userData.id;

			const res = await fetch(
				`http://localhost:8000/training/tasks/digit-span/submit/${userId}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						difficulty: sessionData.difficulty,
						trials: completedTrials
					})
				}
			);

			if (!res.ok) throw new Error('Failed to submit session');

			sessionResults = await res.json();
			newBadges = sessionResults.new_badges || [];
			currentState = STATE_COMPLETE;
		} catch (error) {
			console.error('Error submitting session:', error);
			alert('Failed to submit results');
			goto('/dashboard');
		}
	}

	function handleKeydown(event) {
		if (currentState === STATE_INPUT && event.key === 'Enter') {
			submitResponse();
		}
	}
</script>

<svelte:window on:keydown={handleKeydown} />

<div class="digit-span-container">
	{#if currentState === STATE_LOADING}
		<LoadingSkeleton variant="card" count={3} />
	{:else if currentState === STATE_INSTRUCTIONS}
		<div class="instructions-card">
			<div class="header">
				<div>
					<h1>🧠 Digit Span Test</h1>
					<p class="subtitle">Working Memory Training</p>
				</div>
				<button class="help-button" on:click={() => showHelp = !showHelp}>
					{showHelp ? '✕' : '❓'}
				</button>
			</div>

			<div class="info-section">
				<h2>How It Works</h2>
				<p>
					You'll see a sequence of digits appear one at a time. Your job is to remember them and
					type them back.
				</p>
			</div>

			<div class="instructions-grid">
				<div class="instruction-item">
					<div class="icon">➡️</div>
					<h3>Forward Span</h3>
					<p>Type the digits in the <strong>same order</strong> you saw them</p>
					<div class="example">
						<div class="example-label">You see:</div>
						<div class="example-sequence">3 → 7 → 2</div>
						<div class="example-label">You type:</div>
						<div class="example-input">3 7 2</div>
					</div>
				</div>

				<div class="instruction-item">
					<div class="icon">↩️</div>
					<h3>Backward Span</h3>
					<p>Type the digits in <strong>reverse order</strong></p>
					<div class="example">
						<div class="example-label">You see:</div>
						<div class="example-sequence">5 → 1 → 9</div>
						<div class="example-label">You type:</div>
						<div class="example-input">9 1 5</div>
					</div>
				</div>
			</div>

			{#if showHelp}
				<div class="help-modal">
					<h3>💡 Helpful Tips</h3>
					<ul>
						<li><strong>Chunking:</strong> Group digits into pairs or triplets (e.g., 3-7-2 becomes "37, 2")</li>
						<li><strong>Rehearsal:</strong> Repeat the numbers quietly to yourself</li>
						<li><strong>Visualization:</strong> Picture the digits on a mental screen</li>
						<li><strong>Relaxation:</strong> Take a breath between trials - stress reduces memory</li>
						<li><strong>Practice:</strong> Your working memory will improve with regular training</li>
					</ul>
					<p class="help-note">This test adapts to your performance - don't worry about mistakes!</p>
				</div>
			{/if}

			<div class="tips">
				<h3>💡 Tips</h3>
				<ul>
					<li>Take your time to remember the sequence</li>
					<li>Use memory strategies that work for you (chunking, visualization, etc.)</li>
					<li>Separate digits with spaces when typing</li>
					<li>Don't worry about mistakes - the task adapts to your level</li>
				</ul>
			</div>

			<div class="session-info">
				<div class="info-item">
					<span class="label">Difficulty Level:</span>
					<span class="value">{sessionData.difficulty}/10</span>
				</div>
				<div class="info-item">
					<span class="label">Trials:</span>
					<span class="value">{sessionData.num_trials}</span>
				</div>
			</div>

			<button class="start-button" on:click={startSession}> Start Training </button>
		</div>
	{:else if currentState === STATE_READY}
		<div class="ready-screen">
			<h1 class="ready-text">Get Ready...</h1>
			<div class="trial-counter">
				Trial {currentTrialIndex + 1} of {sessionData.trials.length}
			</div>
			{#if currentTrial}
				<div class="span-type-indicator {currentTrial.span_type}">
					{currentTrial.span_type === 'forward' ? '➡️ Forward Span' : '↩️ Backward Span'}
				</div>
			{/if}
		</div>
	{:else if currentState === STATE_SHOWING}
		<div class="display-screen">
			<div class="trial-counter">
				Trial {currentTrialIndex + 1} of {sessionData.trials.length}
			</div>

			<div class="digit-display">
				{#each displayedDigits as digit}
					<div class="digit {digit === '' ? 'hidden' : 'visible'}">{digit || '·'}</div>
				{/each}
			</div>

			<div class="progress-dots">
				{#each currentTrial.sequence as _, i}
					<div class="dot {i < currentDigitIndex ? 'shown' : ''}"></div>
				{/each}
			</div>
		</div>
	{:else if currentState === STATE_INPUT}
		<div class="input-screen">
			<div class="trial-counter">
				Trial {currentTrialIndex + 1} of {sessionData.trials.length}
			</div>

			<div class="span-type-reminder {currentTrial.span_type}">
				{currentTrial.span_type === 'forward'
					? '➡️ Type in same order'
					: '↩️ Type in reverse order'}
			</div>

			<div class="input-container">
				<input
					type="text"
					bind:value={userInput}
					placeholder="Type the digits (e.g., 3 7 2)"
					class="digit-input"
				/>
			</div>

			<div class="input-hint">Separate digits with spaces, then press Enter or click Submit</div>

			<button class="submit-button" on:click={submitResponse} disabled={!userInput.trim()}>
				Submit Answer
			</button>
		</div>
	{:else if currentState === STATE_FEEDBACK}
		<div class="feedback-screen {isCorrect ? 'correct' : 'incorrect'}">
			<div class="feedback-icon">{isCorrect ? '✅' : '❌'}</div>
			<div class="feedback-text">{isCorrect ? 'Correct!' : 'Incorrect'}</div>

			{#if !isCorrect}
				<div class="correct-answer">
					<div class="label">Correct answer:</div>
					<div class="answer">
						{currentTrial.span_type === 'forward'
							? currentTrial.sequence.join(' ')
							: [...currentTrial.sequence].reverse().join(' ')}
					</div>
				</div>
			{/if}
		</div>
	{:else if currentState === STATE_COMPLETE}
		<div class="complete-screen">
			<div class="header">
				<h1>🎉 Session Complete!</h1>
				<p class="subtitle">Great work on completing your Digit Span training</p>
			</div>

			{#if newBadges && newBadges.length > 0}
				<div class="badges-section">
				<BadgeNotification badges={newBadges} />
			</div>
		{/if}

			<div class="results-grid">
				<div class="result-card primary">
					<div class="result-label">Overall Score</div>
					<div class="result-value">{sessionResults.metrics.score}</div>
				</div>

				<div class="result-card">
					<div class="result-label">Accuracy</div>
					<div class="result-value">{sessionResults.metrics.accuracy.toFixed(1)}%</div>
				</div>

				<div class="result-card">
					<div class="result-label">Longest Span</div>
					<div class="result-value">{sessionResults.metrics.longest_span} digits</div>
				</div>

				<div class="result-card">
					<div class="result-label">Forward Accuracy</div>
					<div class="result-value">{sessionResults.metrics.forward_accuracy.toFixed(1)}%</div>
				</div>

				<div class="result-card">
					<div class="result-label">Backward Accuracy</div>
					<div class="result-value">{sessionResults.metrics.backward_accuracy.toFixed(1)}%</div>
				</div>
			</div>

			<div class="difficulty-info">
				<h3>Difficulty Adjustment</h3>
				<div class="difficulty-change">
					<span class="before">Level {sessionResults.difficulty_before}</span>
					<span class="arrow">→</span>
					<span class="after">Level {sessionResults.difficulty_after}</span>
				</div>
				<p class="reason">{sessionResults.adaptation_reason}</p>
			</div>

			<div class="actions">
				<button class="secondary-button" on:click={() => goto('/dashboard')}>
					Back to Dashboard
				</button>
				<button class="primary-button" on:click={() => window.location.reload()}>
					Train Again
				</button>
			</div>
		</div>
	{/if}
</div>

<style>
	.digit-span-container {
		max-width: 800px;
		margin: 0 auto;
		padding: 2rem;
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	/* Instructions */
	.instructions-card {
		background: white;
		border-radius: 16px;
		padding: 3rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
	}

	.header {
		display: flex;
		justify-content: space-between;
		align-items: start;
	}

	.header h1 {
		font-size: 2.5rem;
		margin-bottom: 0.5rem;
		color: #2563eb;
	}

	.help-button {
		background: #3b82f6;
		color: white;
		border: none;
		border-radius: 50%;
		width: 48px;
		height: 48px;
		font-size: 1.5rem;
		cursor: pointer;
		transition: all 0.2s;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
	}

	.help-button:hover {
		background: #2563eb;
		transform: scale(1.1);
	}

	.help-modal {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		padding: 2rem;
		border-radius: 12px;
		margin: 2rem 0;
		box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
	}

	.help-modal h3 {
		margin-bottom: 1rem;
		font-size: 1.5rem;
	}

	.help-modal ul {
		list-style: none;
		padding: 0;
		margin-bottom: 1rem;
	}

	.help-modal li {
		padding: 0.75rem 0;
		border-bottom: 1px solid rgba(255, 255, 255, 0.2);
	}

	.help-modal li:last-child {
		border-bottom: none;
	}

	.help-modal strong {
		color: #fbbf24;
	}

	.help-note {
		background: rgba(255, 255, 255, 0.1);
		padding: 1rem;
		border-radius: 8px;
		margin-top: 1rem;
		font-style: italic;
	}

	.subtitle {
		font-size: 1.1rem;
		color: #64748b;
		margin-bottom: 2rem;
	}

	.info-section {
		margin-bottom: 2rem;
		padding: 1.5rem;
		background: #f8fafc;
		border-radius: 12px;
	}

	.info-section h2 {
		margin-bottom: 0.5rem;
		color: #1e293b;
	}

	.instructions-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 2rem;
		margin-bottom: 2rem;
	}

	.instruction-item {
		padding: 1.5rem;
		border: 2px solid #e2e8f0;
		border-radius: 12px;
		text-align: center;
	}

	.icon {
		font-size: 3rem;
		margin-bottom: 1rem;
	}

	.instruction-item h3 {
		margin-bottom: 0.5rem;
		color: #1e293b;
	}

	.example {
		margin-top: 1rem;
		padding: 1rem;
		background: #f8fafc;
		border-radius: 8px;
		font-size: 0.9rem;
	}

	.example-label {
		font-weight: 600;
		color: #64748b;
		margin-bottom: 0.25rem;
	}

	.example-sequence,
	.example-input {
		font-family: monospace;
		font-size: 1.2rem;
		color: #2563eb;
		margin-bottom: 0.5rem;
	}

	.tips {
		background: #fef3c7;
		padding: 1.5rem;
		border-radius: 12px;
		margin-bottom: 2rem;
	}

	.tips h3 {
		margin-bottom: 1rem;
		color: #92400e;
	}

	.tips ul {
		margin-left: 1.5rem;
	}

	.tips li {
		margin-bottom: 0.5rem;
		color: #78350f;
	}

	.session-info {
		display: flex;
		gap: 2rem;
		justify-content: center;
		margin-bottom: 2rem;
	}

	.info-item {
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.info-item .label {
		font-size: 0.9rem;
		color: #64748b;
		margin-bottom: 0.25rem;
	}

	.info-item .value {
		font-size: 1.5rem;
		font-weight: 700;
		color: #2563eb;
	}

	.start-button {
		width: 100%;
		padding: 1rem 2rem;
		background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
		color: white;
		border: none;
		border-radius: 12px;
		font-size: 1.2rem;
		font-weight: 600;
		cursor: pointer;
		transition: transform 0.2s;
	}

	.start-button:hover {
		transform: translateY(-2px);
	}

	/* Ready Screen */
	.ready-screen {
		text-align: center;
		background: white;
		padding: 4rem;
		border-radius: 16px;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
	}

	.ready-text {
		font-size: 3rem;
		color: #2563eb;
		margin-bottom: 1rem;
		animation: pulse 1s ease-in-out;
	}

	.trial-counter {
		font-size: 1.2rem;
		color: #64748b;
		margin-bottom: 1rem;
		text-align: center;
	}

	.span-type-indicator {
		font-size: 1.5rem;
		padding: 1rem 2rem;
		border-radius: 12px;
		display: inline-block;
		margin-top: 1rem;
		font-weight: 600;
	}

	.span-type-indicator.forward {
		background: #dbeafe;
		color: #1e40af;
	}

	.span-type-indicator.backward {
		background: #fce7f3;
		color: #9f1239;
	}

	/* Display Screen */
	.display-screen {
		text-align: center;
		background: white;
		padding: 4rem;
		border-radius: 16px;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
	}

	.digit-display {
		display: flex;
		justify-content: center;
		align-items: center;
		min-height: 200px;
		margin: 2rem 0;
	}

	.digit {
		font-size: 6rem;
		font-weight: 700;
		color: #2563eb;
		transition: opacity 0.3s;
	}

	.digit.visible {
		animation: digitAppear 0.3s ease-out;
	}

	.digit.hidden {
		opacity: 0.2;
	}

	.progress-dots {
		display: flex;
		justify-content: center;
		gap: 0.5rem;
		margin-top: 2rem;
	}

	.dot {
		width: 12px;
		height: 12px;
		border-radius: 50%;
		background: #e2e8f0;
		transition: background 0.3s;
	}

	.dot.shown {
		background: #2563eb;
	}

	/* Input Screen */
	.input-screen {
		text-align: center;
		background: white;
		padding: 4rem;
		border-radius: 16px;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
	}

	.span-type-reminder {
		font-size: 1.3rem;
		padding: 0.75rem 1.5rem;
		border-radius: 12px;
		display: inline-block;
		margin-bottom: 2rem;
		font-weight: 600;
	}

	.span-type-reminder.forward {
		background: #dbeafe;
		color: #1e40af;
	}

	.span-type-reminder.backward {
		background: #fce7f3;
		color: #9f1239;
	}

	.input-container {
		margin-bottom: 1rem;
	}

	.digit-input {
		width: 100%;
		max-width: 400px;
		padding: 1.5rem;
		font-size: 2rem;
		text-align: center;
		border: 3px solid #2563eb;
		border-radius: 12px;
		font-family: monospace;
	}

	.digit-input:focus {
		outline: none;
		border-color: #7c3aed;
		box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.1);
	}

	.input-hint {
		color: #64748b;
		margin-bottom: 2rem;
	}

	.submit-button {
		padding: 1rem 3rem;
		background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
		color: white;
		border: none;
		border-radius: 12px;
		font-size: 1.2rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
	}

	.submit-button:hover:not(:disabled) {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
	}

	.submit-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	/* Feedback Screen */
	.feedback-screen {
		text-align: center;
		background: white;
		padding: 4rem;
		border-radius: 16px;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
	}

	.feedback-icon {
		font-size: 5rem;
		margin-bottom: 1rem;
		animation: scaleIn 0.3s ease-out;
	}

	.feedback-text {
		font-size: 2rem;
		font-weight: 700;
		margin-bottom: 1rem;
	}

	.feedback-screen.correct .feedback-text {
		color: #059669;
	}

	.feedback-screen.incorrect .feedback-text {
		color: #dc2626;
	}

	.correct-answer {
		margin-top: 2rem;
		padding: 1.5rem;
		background: #fef2f2;
		border-radius: 12px;
	}

	.correct-answer .label {
		color: #991b1b;
		margin-bottom: 0.5rem;
	}

	.correct-answer .answer {
		font-size: 1.5rem;
		font-family: monospace;
		color: #dc2626;
		font-weight: 600;
	}

	/* Complete Screen */
	.complete-screen {
		background: white;
		border-radius: 16px;
		padding: 3rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
	}

	.badges-section {
		margin: 2rem 0;
	}

	.results-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: 1rem;
		margin: 2rem 0;
	}

	.result-card {
		padding: 1.5rem;
		background: #f8fafc;
		border-radius: 12px;
		text-align: center;
		border: 2px solid #e2e8f0;
	}

	.result-card.primary {
		background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
		color: white;
		border: none;
	}

	.result-label {
		font-size: 0.9rem;
		color: #64748b;
		margin-bottom: 0.5rem;
	}

	.result-card.primary .result-label {
		color: rgba(255, 255, 255, 0.9);
	}

	.result-value {
		font-size: 2rem;
		font-weight: 700;
		color: #1e293b;
	}

	.result-card.primary .result-value {
		color: white;
	}

	.difficulty-info {
		background: #f8fafc;
		padding: 1.5rem;
		border-radius: 12px;
		margin: 2rem 0;
		text-align: center;
	}

	.difficulty-info h3 {
		margin-bottom: 1rem;
		color: #1e293b;
	}

	.difficulty-change {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 1rem;
		font-size: 1.5rem;
		margin-bottom: 1rem;
	}

	.before,
	.after {
		font-weight: 700;
		color: #2563eb;
	}

	.arrow {
		color: #64748b;
	}

	.reason {
		color: #64748b;
	}

	.actions {
		display: flex;
		gap: 1rem;
		margin-top: 2rem;
	}

	.primary-button,
	.secondary-button {
		flex: 1;
		padding: 1rem 2rem;
		border: none;
		border-radius: 12px;
		font-size: 1.1rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
	}

	.primary-button {
		background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
		color: white;
	}

	.primary-button:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
	}

	.secondary-button {
		background: white;
		border: 2px solid #e2e8f0;
		color: #1e293b;
	}

	.secondary-button:hover {
		background: #f8fafc;
	}

	/* Animations */
	@keyframes pulse {
		0%,
		100% {
			transform: scale(1);
		}
		50% {
			transform: scale(1.05);
		}
	}

	@keyframes digitAppear {
		0% {
			transform: scale(0.5);
			opacity: 0;
		}
		100% {
			transform: scale(1);
			opacity: 1;
		}
	}

	@keyframes scaleIn {
		0% {
			transform: scale(0);
		}
		50% {
			transform: scale(1.1);
		}
		100% {
			transform: scale(1);
		}
	}

	/* Responsive */
	@media (max-width: 768px) {
		.instructions-grid {
			grid-template-columns: 1fr;
		}

		.digit-span-container {
			padding: 1rem;
		}

		.instructions-card,
		.ready-screen,
		.display-screen,
		.input-screen,
		.feedback-screen,
		.complete-screen {
			padding: 2rem;
		}

		.ready-text {
			font-size: 2rem;
		}

		.digit {
			font-size: 4rem;
		}

		.results-grid {
			grid-template-columns: 1fr;
		}

		.actions {
			flex-direction: column;
		}
	}
</style>

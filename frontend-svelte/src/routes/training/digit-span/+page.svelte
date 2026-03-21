<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import { formatNumber, formatPercent, locale, translateText } from '$lib/i18n';
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
	let taskId = null; // Track which specific task in session this is

	// Display state
	let displayedDigits = [];
	let currentDigitIndex = 0;

	// User input — one slot per digit in the sequence
	let digitSlots = [];      // array of single digit strings, length = sequence length
	let activeSlot = 0;       // index of the currently focused slot
	let isCorrect = false;
	let trialStartTime = 0;

	// Results
	let completedTrials = [];
	let sessionResults = null;
	let newBadges = [];

	// UI state
	let showHelp = false;
	let currentDifficulty = 5;

	// Timing variables - will be set based on difficulty
	let DIGIT_DISPLAY_TIME = 1400;
	let INTER_DIGIT_INTERVAL = 600;

	function t(text) {
		return translateText(text, $locale);
	}

	function n(value, options = {}) {
		return formatNumber(value, $locale, options);
	}

	function pct(value, options = {}) {
		return formatPercent(value, $locale, options);
	}

	function formatSequence(values, delimiter = ' → ') {
		return values.map((value) => n(value)).join(delimiter);
	}

	function getSpanTypeLabel(spanType) {
		return spanType === 'forward' ? t('Forward Span') : t('Backward Span');
	}

	function getSpanInputInstruction(spanType) {
		return spanType === 'forward' ? `➡️ ${t('Type in same order')}` : `↩️ ${t('Type in reverse order')}`;
	}

	function displayDigit(value) {
		return value === '' ? '' : n(value);
	}

	onMount(() => {
		// Get taskId from URL params
		taskId = $page.url.searchParams.get('taskId');
	});

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

	const READY_DISPLAY_TIME = 2000;

	onMount(async () => {
		// Get taskId from URL params
		taskId = $page.url.searchParams.get('taskId');
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
			const planRes = await fetch(`http://localhost:8000/api/training/training-plan/${userId}`);
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
			console.log('📊 Digit Span - Loaded difficulty:', difficulty, 'Display time:', DIGIT_DISPLAY_TIME);

			// Generate session
			const res = await fetch(
				`http://localhost:8000/api/training/tasks/digit-span/generate/${userId}?difficulty=${difficulty}&num_trials=8`,
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
			alert(t('Failed to load training session'));
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
				digitSlots = Array(currentTrial.sequence.length).fill('');
				activeSlot = 0;
				trialStartTime = Date.now();
				// Focus first slot after DOM updates
				setTimeout(() => focusSlot(0), 50);
			}, INTER_DIGIT_INTERVAL);
		}
	}

	function focusSlot(index) {
		const el = document.getElementById(`slot-${index}`);
		if (el) el.focus();
	}

	function submitResponse() {
		// All slots must be filled
		if (digitSlots.some((s) => s === '')) return;

		const reactionTime = Date.now() - trialStartTime;

		// Each slot holds exactly one digit string — convert to integers directly
		const userDigits = digitSlots.map((s) => parseInt(s));

		// Expected sequence
		const expectedSequence =
			currentTrial.span_type === 'forward'
				? currentTrial.sequence
				: [...currentTrial.sequence].reverse();

		isCorrect =
			userDigits.length === expectedSequence.length &&
			userDigits.every((d, i) => d === expectedSequence[i]);

		const trialResult = {
			...currentTrial,
			user_response: userDigits,
			reaction_time: reactionTime,
			correct: isCorrect
		};

		completedTrials.push(trialResult);
		currentState = STATE_FEEDBACK;

		setTimeout(() => {
			currentTrialIndex++;
			if (currentTrialIndex < sessionData.trials.length) {
				startTrial();
			} else {
				completeSession();
			}
		}, 1500);
	}

	function handleSlotKeydown(event, index) {
		const key = event.key;

		if (key === 'Backspace') {
			event.preventDefault();
			if (digitSlots[index] !== '') {
				// Clear this slot
				digitSlots[index] = '';
				digitSlots = [...digitSlots];
				activeSlot = index;
			} else if (index > 0) {
				// Move back and clear previous slot
				digitSlots[index - 1] = '';
				digitSlots = [...digitSlots];
				activeSlot = index - 1;
				focusSlot(index - 1);
			}
			return;
		}

		if (key === 'Enter') {
			submitResponse();
			return;
		}

		// Only accept single digit 0-9
		if (/^[0-9]$/.test(key)) {
			event.preventDefault();
			digitSlots[index] = key;
			digitSlots = [...digitSlots];
			if (index < digitSlots.length - 1) {
				// Advance to next slot
				activeSlot = index + 1;
				focusSlot(index + 1);
			} else {
				// Last slot filled — auto-submit
				activeSlot = index;
				submitResponse();
			}
			return;
		}

		// Block everything else
		event.preventDefault();
	}

	async function completeSession() {
		currentState = STATE_LOADING;

		try {
			const userData = JSON.parse(localStorage.getItem('user') || '{}');
			const userId = userData.id;

			const res = await fetch(
				`http://localhost:8000/api/training/tasks/digit-span/submit/${userId}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						difficulty: sessionData.difficulty,
						trials: completedTrials,
						task_id: taskId  // Include task_id to track which specific task in session
					})
				}
			);

			if (!res.ok) throw new Error('Failed to submit session');

			sessionResults = await res.json();
			newBadges = sessionResults.new_badges || [];
			currentState = STATE_COMPLETE;
		} catch (error) {
			console.error('Error submitting session:', error);
			alert(t('Failed to submit results'));
			goto('/dashboard');
		}
	}
</script>


<div class="digit-span-container">
	{#if currentState === STATE_LOADING}
		<LoadingSkeleton variant="card" count={3} />
	{:else if currentState === STATE_INSTRUCTIONS}
		<div class="instructions-card">
			<div class="header">
				<div>
					<h1>🧠 {t('Digit Span Test')}</h1>
					<p class="subtitle">{t('Working Memory Training')}</p>
				</div>
				<button class="help-button" on:click={() => showHelp = !showHelp}>
					{showHelp ? '✕' : '❓'}
				</button>
			</div>

			<div class="info-section">
				<h2>{t('How It Works')}</h2>
				<p>{t("You'll see a sequence of digits appear one at a time. Your job is to remember them and type them back.")}</p>
			</div>

			<div class="instructions-grid">
				<div class="instruction-item">
					<div class="icon">➡️</div>
					<h3>{t('Forward Span')}</h3>
					<p>{t('Type the digits in the same order you saw them')}</p>
					<div class="example">
						<div class="example-label">{t('You see:')}</div>
						<div class="example-sequence">{formatSequence([3, 7, 2])}</div>
						<div class="example-label">{t('You type:')}</div>
						<div class="example-input">{formatSequence([3, 7, 2], ' ')}</div>
					</div>
				</div>

				<div class="instruction-item">
					<div class="icon">↩️</div>
					<h3>{t('Backward Span')}</h3>
					<p>{t('Type the digits in reverse order')}</p>
					<div class="example">
						<div class="example-label">{t('You see:')}</div>
						<div class="example-sequence">{formatSequence([5, 1, 9])}</div>
						<div class="example-label">{t('You type:')}</div>
						<div class="example-input">{formatSequence([9, 1, 5], ' ')}</div>
					</div>
				</div>
			</div>

			{#if showHelp}
				<div class="help-modal">
					<h3>💡 {t('Helpful Tips')}</h3>
					<ul>
						<li>{t('Chunking: Group digits into pairs or triplets')}</li>
						<li>{t('Rehearsal: Repeat the numbers quietly to yourself')}</li>
						<li>{t('Visualization: Picture the digits on a mental screen')}</li>
						<li>{t('Relaxation: Take a breath between trials - stress reduces memory')}</li>
						<li>{t('Practice: Your working memory will improve with regular training')}</li>
					</ul>
					<p class="help-note">{t("This test adapts to your performance - don't worry about mistakes!")}</p>
				</div>
			{/if}

			<div class="tips">
				<h3>💡 {t('Tips')}</h3>
				<ul>
					<li>{t('Take your time to remember the sequence before typing')}</li>
					<li>{t('Use chunking or visualization to hold the digits in mind')}</li>
					<li>{t('One box per digit - Backspace to correct the last entry')}</li>
					<li>{t("Don't worry about mistakes - the task adapts to your level")}</li>
				</ul>
			</div>

			<div class="session-info">
				<div class="info-item">
					<span class="label">{t('Difficulty Level:')}</span>
					<span class="value">{n(sessionData.difficulty)}/{n(10)}</span>
				</div>
				<div class="info-item">
					<span class="label">{t('Trials:')}</span>
					<span class="value">{n(sessionData.num_trials)}</span>
				</div>
			</div>

			<button class="start-button" on:click={startSession}>{t('Start Training')}</button>
		</div>
	{:else if currentState === STATE_READY}
		<div class="ready-screen">
			<h1 class="ready-text">{t('Get Ready...')}</h1>
			<div class="trial-counter">
				{t('Trial')} {n(currentTrialIndex + 1)} {t('of')} {n(sessionData.trials.length)}
			</div>
			{#if currentTrial}
				<div class="span-type-indicator {currentTrial.span_type}">
					{currentTrial.span_type === 'forward'
						? `➡️ ${t('Forward Span')}`
						: `↩️ ${t('Backward Span')}`}
				</div>
			{/if}
		</div>
	{:else if currentState === STATE_SHOWING}
		<div class="display-screen">
			<div class="trial-counter">
				{t('Trial')} {n(currentTrialIndex + 1)} {t('of')} {n(sessionData.trials.length)}
			</div>

			<div class="digit-display">
				{#each displayedDigits as digit}
					<div class="digit {digit === '' ? 'hidden' : 'visible'}">{digit === '' ? '·' : displayDigit(digit)}</div>
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
				{t('Trial')} {n(currentTrialIndex + 1)} {t('of')} {n(sessionData.trials.length)}
			</div>

			<div class="span-type-reminder {currentTrial.span_type}">
				{getSpanInputInstruction(currentTrial.span_type)}
			</div>

			<div class="slot-row">
				{#each digitSlots as slot, i}
					<input
						id="slot-{i}"
						type="text"
						inputmode="numeric"
						maxlength="1"
						value={displayDigit(slot)}
						on:keydown={(e) => handleSlotKeydown(e, i)}
						on:focus={() => (activeSlot = i)}
						readonly
						class="digit-slot {activeSlot === i ? 'active' : ''} {slot !== '' ? 'filled' : ''}"
					/>
				{/each}
			</div>

			<div class="input-hint">
				{t('Type each digit • Backspace to correct • auto-submits on last digit')}
			</div>

			<button
				class="submit-button"
				on:click={submitResponse}
				disabled={digitSlots.some((s) => s === '')}
			>
				{t('Submit Answer')}
			</button>
		</div>
	{:else if currentState === STATE_FEEDBACK}
		<div class="feedback-screen {isCorrect ? 'correct' : 'incorrect'}">
			<div class="feedback-icon">{isCorrect ? '✅' : '❌'}</div>
			<div class="feedback-text">{isCorrect ? t('Correct!') : t('Incorrect')}</div>

			{#if !isCorrect}
				<div class="correct-answer">
					<div class="label">{t('Correct answer:')}</div>
					<div class="answer">
						{currentTrial.span_type === 'forward'
							? formatSequence(currentTrial.sequence, ' ')
							: formatSequence([...currentTrial.sequence].reverse(), ' ')}
					</div>
				</div>
			{/if}
		</div>
	{:else if currentState === STATE_COMPLETE}
		<div class="complete-screen">
			<div class="header">
				<h1>🎉 {t('Session Complete!')}</h1>
				<p class="subtitle">{t('Great work on completing your Digit Span training')}</p>
			</div>

			{#if newBadges && newBadges.length > 0}
				<div class="badges-section">
				<BadgeNotification badges={newBadges} />
			</div>
		{/if}

			<div class="results-grid">
				<div class="result-card primary">
					<div class="result-label">{t('Overall Score')}</div>
					<div class="result-value">{n(sessionResults.metrics.score)}</div>
				</div>

				<div class="result-card">
					<div class="result-label">{t('Accuracy')}</div>
					<div class="result-value">{pct(sessionResults.metrics.accuracy, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}</div>
				</div>

				<div class="result-card">
					<div class="result-label">{t('Longest Span')}</div>
					<div class="result-value">{n(sessionResults.metrics.longest_span)} {t('digits')}</div>
				</div>

				<div class="result-card">
					<div class="result-label">{t('Forward Accuracy')}</div>
					<div class="result-value">{pct(sessionResults.metrics.forward_accuracy, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}</div>
				</div>

				<div class="result-card">
					<div class="result-label">{t('Backward Accuracy')}</div>
					<div class="result-value">{pct(sessionResults.metrics.backward_accuracy, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}</div>
				</div>
			</div>

			<div class="difficulty-info">
				<h3>{t('Difficulty Adjustment')}</h3>
				<div class="difficulty-change">
					<span class="before">{t('Level')} {n(sessionResults.difficulty_before)}</span>
					<span class="arrow">→</span>
					<span class="after">{t('Level')} {n(sessionResults.difficulty_after)}</span>
				</div>
				<p class="reason">{t(sessionResults.adaptation_reason)}</p>
			</div>

			<div class="actions">
				<button class="secondary-button" on:click={() => goto('/dashboard')}>
					{t('Back to Dashboard')}
				</button>
				<button class="primary-button" on:click={() => window.location.reload()}>
					{t('Train Again')}
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

	.slot-row {
		display: flex;
		gap: 0.6rem;
		justify-content: center;
		flex-wrap: wrap;
		margin-bottom: 1.5rem;
	}

	.digit-slot {
		width: 3rem;
		height: 3.5rem;
		font-size: 1.8rem;
		font-family: monospace;
		font-weight: 700;
		text-align: center;
		border: 2.5px solid #cbd5e1;
		border-radius: 10px;
		background: #f8fafc;
		color: #1e293b;
		cursor: default;
		caret-color: transparent;
		transition: border-color 0.15s, box-shadow 0.15s, background 0.15s;
		/* prevent any browser text-editing UI */
		user-select: none;
	}

	.digit-slot.active {
		border-color: #2563eb;
		background: #eff6ff;
		box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.18);
		outline: none;
	}

	.digit-slot.filled {
		border-color: #7c3aed;
		color: #2563eb;
		background: #f5f3ff;
	}

	.digit-slot.active.filled {
		border-color: #2563eb;
		background: #eff6ff;
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

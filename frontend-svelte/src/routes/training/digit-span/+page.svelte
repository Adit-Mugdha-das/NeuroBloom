<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
	import TaskReturnButton from '$lib/components/TaskReturnButton.svelte';
	import { formatNumber, formatPercent, locale, translateText } from '$lib/i18n';
	import { buildPracticePayload, getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
	import { TASK_RETURN_CONTEXT } from '$lib/task-navigation';
	import { onDestroy, onMount } from 'svelte';

	// Game states
	const STATE_LOADING = 'loading';
	const STATE_INSTRUCTIONS = 'instructions';
	const STATE_READY = 'ready';
	const STATE_SHOWING = 'showing';
	const STATE_INPUT = 'input';
	const STATE_FEEDBACK = 'feedback';
	const STATE_COMPLETE = 'complete';
	const READY_DISPLAY_TIME = 2000;
	const FEEDBACK_DISPLAY_TIME = 1500;
	const INPUT_FOCUS_DELAY = 50;

	let currentState = STATE_LOADING;
	let sessionData = null;
	let recordedSessionData = null;
	let currentTrialIndex = 0;
	let currentTrial = null;
	let taskId = null;

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
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';
	let sessionRunId = 0;
	let isDisposed = false;

	// Timing variables - will be set based on difficulty
	let DIGIT_DISPLAY_TIME = 1400;
	let INTER_DIGIT_INTERVAL = 600;
	const scheduledTimeouts = new Set();

	function t(text) {
		return translateText(text, $locale);
	}

	function n(value, options = {}) {
		return formatNumber(value, $locale, options);
	}

	function pct(value, options = {}) {
		return formatPercent(value, $locale, options);
	}

	function cloneData(value) {
		if (typeof structuredClone === 'function') {
			return structuredClone(value);
		}

		return JSON.parse(JSON.stringify(value));
	}

	function formatSequence(values, delimiter = ' → ') {
		return values.map((value) => n(value)).join(delimiter);
	}

	function getSpanTypeLabel(spanType) {
		return spanType === 'forward' ? t('Forward Span') : t('Backward Span');
	}

	function getSpanInputInstruction(spanType) {
		return spanType === 'forward' ? t('Type in same order') : t('Type in reverse order');
	}

	function displayDigit(value) {
		return value === '' ? '' : n(value);
	}

	function clearScheduledTimeouts() {
		for (const timeoutId of scheduledTimeouts) {
			clearTimeout(timeoutId);
		}
		scheduledTimeouts.clear();
	}

	function invalidateRun() {
		sessionRunId += 1;
		clearScheduledTimeouts();
	}

	function scheduleTimeout(callback, delay, runId = sessionRunId) {
		const timeoutId = setTimeout(() => {
			scheduledTimeouts.delete(timeoutId);
			if (isDisposed || runId !== sessionRunId) return;
			callback();
		}, delay);

		scheduledTimeouts.add(timeoutId);
		return timeoutId;
	}

	function resetSessionState() {
		currentTrialIndex = 0;
		currentTrial = null;
		displayedDigits = [];
		currentDigitIndex = 0;
		digitSlots = [];
		activeSlot = 0;
		isCorrect = false;
		trialStartTime = 0;
		completedTrials = [];
		sessionResults = null;
		newBadges = [];
	}

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

	onMount(async () => {
		taskId = $page.url.searchParams.get('taskId');
		await loadSession();
	});

	onDestroy(() => {
		isDisposed = true;
		invalidateRun();
	});

	async function loadSession() {
		try {
			currentState = STATE_LOADING;
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

			const data = await res.json();
			recordedSessionData = cloneData(data);
			sessionData = cloneData(data);
			playMode = TASK_PLAY_MODE.RECORDED;
			practiceStatusMessage = '';
			resetSessionState();
			currentState = STATE_INSTRUCTIONS;
		} catch (error) {
			console.error('Error loading session:', error);
			alert(t('Failed to load training session'));
			goto('/dashboard');
		}
	}

	function startSession(nextMode = TASK_PLAY_MODE.RECORDED) {
		if (!recordedSessionData) return;

		invalidateRun();
		playMode = nextMode;
		practiceStatusMessage = '';
		resetSessionState();
		sessionData =
			nextMode === TASK_PLAY_MODE.PRACTICE
				? buildPracticePayload('digit-span', recordedSessionData)
				: cloneData(recordedSessionData);
		startTrial();
	}

	function leavePractice(completed = false) {
		invalidateRun();
		playMode = TASK_PLAY_MODE.RECORDED;
		sessionData = cloneData(recordedSessionData);
		resetSessionState();
		practiceStatusMessage = completed ? getPracticeCopy($locale).complete : '';
		currentState = STATE_INSTRUCTIONS;
	}

	function startTrial() {
		const runId = sessionRunId;
		currentTrial = sessionData?.trials?.[currentTrialIndex] ?? null;
		displayedDigits = [];
		currentDigitIndex = 0;
		digitSlots = [];
		activeSlot = 0;
		currentState = STATE_READY;

		scheduleTimeout(() => {
			currentState = STATE_SHOWING;
			showNextDigit(runId);
		}, READY_DISPLAY_TIME, runId);
	}

	function showNextDigit(runId = sessionRunId) {
		if (!currentTrial) return;

		if (currentDigitIndex < currentTrial.sequence.length) {
			displayedDigits = [...displayedDigits, currentTrial.sequence[currentDigitIndex]];

			scheduleTimeout(() => {
				displayedDigits = [...displayedDigits.slice(0, -1), ''];
				scheduleTimeout(() => {
					currentDigitIndex += 1;
					showNextDigit(runId);
				}, INTER_DIGIT_INTERVAL, runId);
			}, DIGIT_DISPLAY_TIME, runId);
			return;
		}

		scheduleTimeout(() => {
			currentState = STATE_INPUT;
			digitSlots = Array(currentTrial.sequence.length).fill('');
			activeSlot = 0;
			trialStartTime = Date.now();
			scheduleTimeout(() => focusSlot(0), INPUT_FOCUS_DELAY, runId);
		}, INTER_DIGIT_INTERVAL, runId);
	}

	function focusSlot(index) {
		const element = document.getElementById(`slot-${index}`);
		if (element) element.focus();
	}

	function submitResponse() {
		// All slots must be filled
		if (!currentTrial || digitSlots.some((slot) => slot === '')) return;

		const reactionTime = Date.now() - trialStartTime;

		// Each slot holds exactly one digit string — convert to integers directly
		const userDigits = digitSlots.map((slot) => Number.parseInt(slot, 10));

		// Expected sequence
		const expectedSequence =
			currentTrial.span_type === 'forward'
				? currentTrial.sequence
				: [...currentTrial.sequence].reverse();

		isCorrect =
			userDigits.length === expectedSequence.length &&
			userDigits.every((digit, index) => digit === expectedSequence[index]);

		const trialResult = {
			...currentTrial,
			user_response: userDigits,
			reaction_time: reactionTime,
			correct: isCorrect
		};

		completedTrials = [...completedTrials, trialResult];
		currentState = STATE_FEEDBACK;

		const runId = sessionRunId;
		scheduleTimeout(() => {
			currentTrialIndex += 1;
			if (currentTrialIndex < sessionData.trials.length) {
				startTrial();
				return;
			}

			if (playMode === TASK_PLAY_MODE.PRACTICE) {
				leavePractice(true);
				return;
			}

			completeSession();
		}, FEEDBACK_DISPLAY_TIME, runId);
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


<div class="digit-span-container" data-localize-skip>
<div class="digit-span-inner">
	{#if currentState === STATE_LOADING}
		<LoadingSkeleton variant="card" count={3} />
	{:else if currentState === STATE_INSTRUCTIONS}
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />
		<div class="instructions-card">
			<div class="header">
				<div class="header-content">
					<h1>{t('Digit Span Test')}</h1>
					<p class="subtitle">{t('Working Memory Training')}</p>
					<div class="classic-badge">{t('WAIS-IV Standard · MACFIMS Battery')}</div>
				</div>
				<div class="header-right">
					<DifficultyBadge difficulty={sessionData.difficulty} domain="Working Memory" />
					<button class="help-btn" on:click={() => (showHelp = !showHelp)} aria-label={t('Help')}>?</button>
				</div>
			</div>

			<div class="task-concept">
				<h2>{t('Your Task: Remember & Reproduce Digit Sequences')}</h2>
				<p>{t("You'll see digits appear on screen one at a time. Remember the sequence, then type it back — either in the same order or reversed. The sequence length adapts to your performance.")}</p>
			</div>

			<div class="instructions-grid">
				<div class="instruction-item">
					<div class="icon">→</div>
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
					<div class="icon">←</div>
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

			<div class="info-grid">
				<div class="info-section">
					<h3>{t('Tips for Success')}</h3>
					<div class="tips-list">
						<div class="tip-item">✓ <strong>{t('Chunking:')}</strong> {t('Group digits into pairs (3-7, 2-8)')}</div>
						<div class="tip-item">✓ <strong>{t('Rehearsal:')}</strong> {t('Repeat them quietly to yourself')}</div>
						<div class="tip-item">✓ <strong>{t('Visualization:')}</strong> {t('Picture digits on a mental screen')}</div>
						<div class="tip-item">✓ <strong>{t('Relax:')}</strong> {t('Stress reduces memory — breathe between trials')}</div>
					</div>
				</div>
				<div class="info-section">
					<h3>{t('Session Info')}</h3>
					<div class="structure-list">
						<div class="structure-item">
							<div class="structure-num">{n(sessionData.difficulty)}</div>
							<div class="structure-text">
								<strong>{t('Difficulty Level')}</strong>
								<span>{t('Adapts after each session')}</span>
							</div>
						</div>
						<div class="structure-item">
							<div class="structure-num">{n(sessionData.num_trials)}</div>
							<div class="structure-text">
								<strong>{t('Total Trials')}</strong>
								<span>{t('Forward & Backward mixed')}</span>
							</div>
						</div>
					</div>
				</div>
			</div>

			<div class="clinical-info">
				<h3>{t('Clinical Significance')}</h3>
				<div class="clinical-grid">
					<div class="clinical-item">
						<strong>{t('Standard:')}</strong> {t('WAIS-IV subtest, gold standard in neuropsychology')}
					</div>
					<div class="clinical-item">
						<strong>{t('Measures:')}</strong> {t('Verbal working memory capacity & manipulation')}
					</div>
					<div class="clinical-item">
						<strong>{t('MS Relevance:')}</strong> {t('Included in MACFIMS — sensitive to MS-related deficits (Benedict et al., 2006)')}
					</div>
					<div class="clinical-item">
						<strong>{t('Clinical Use:')}</strong> {t('Standard across neuropsychological assessments worldwide')}
					</div>
				</div>
			</div>

			<TaskPracticeActions
				locale={$locale}
				startLabel={t('Begin Training')}
				statusMessage={practiceStatusMessage}
				align="center"
				on:start={() => startSession()}
				on:practice={() => startSession(TASK_PLAY_MODE.PRACTICE)}
			/>
		</div>
	{:else if currentState === STATE_READY}
		{#if playMode === TASK_PLAY_MODE.PRACTICE}
			<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
		{/if}
		<div class="ready-screen">
			<h1 class="ready-text">{t('Get Ready...')}</h1>
			<div class="trial-counter">
				{t('Trial')} {n(currentTrialIndex + 1)} {t('of')} {n(sessionData.trials.length)}
			</div>
			{#if currentTrial}
				<div class="span-type-indicator {currentTrial.span_type}">
					{currentTrial.span_type === 'forward'
						? t('Forward Span')
						: t('Backward Span')}
				</div>
			{/if}
		</div>
	{:else if currentState === STATE_SHOWING}
		{#if playMode === TASK_PLAY_MODE.PRACTICE}
			<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
		{/if}
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
		{#if playMode === TASK_PLAY_MODE.PRACTICE}
			<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
		{/if}
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
		{#if playMode === TASK_PLAY_MODE.PRACTICE}
			<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
		{/if}
		<div class="feedback-screen {isCorrect ? 'correct' : 'incorrect'}">
			<div class="feedback-icon">{isCorrect ? '✓' : '✗'}</div>
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
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />
		<div class="complete-screen">
			<div class="header">
				<h1>{t('Session Complete!')}</h1>
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
					{t('View Dashboard')}
				</button>
				<button class="primary-button" on:click={loadSession}>
					{t('Train Again')}
				</button>
			</div>
		</div>
	{/if}
</div>
</div>

{#if showHelp}
	<div
		class="modal-overlay"
		role="presentation"
		on:click={() => (showHelp = false)}
		on:keydown={(e) => e.key === 'Escape' && (showHelp = false)}
	>
		<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
		<div
			class="modal-content"
			role="document"
			on:click|stopPropagation
			on:keydown|stopPropagation
		>
			<button class="close-btn" on:click={() => (showHelp = false)}>&times;</button>
			<h2>{t('Memory Strategies')}</h2>

			<div class="strategy">
				<h3>{t('Chunking')}</h3>
				<p>{t('Group digits into pairs or triplets (e.g., 3-7-2 becomes "37" and "2"). This reduces the number of items you need to hold in memory.')}</p>
			</div>
			<div class="strategy">
				<h3>{t('Verbal Rehearsal')}</h3>
				<p>{t('Repeat the sequence quietly to yourself as each digit appears. Subvocalization strengthens the memory trace.')}</p>
			</div>
			<div class="strategy">
				<h3>{t('Visualization')}</h3>
				<p>{t('Picture the digits written on a whiteboard or chalkboard in your mind. Spatial encoding adds a second memory cue.')}</p>
			</div>
			<div class="strategy">
				<h3>{t('Relaxation')}</h3>
				<p>{t("Anxiety narrows working memory capacity. Take a slow breath between trials \u2014 you'll remember more.")}</p>
			</div>
			<p class="help-note">{t("This test adapts automatically to your level \u2014 don't worry about mistakes!")}</p>
		</div>
	</div>
{/if}

<style>
	.digit-span-container {
		background: #C8DEFA;
		min-height: 100vh;
		padding: 2rem 1rem;
	}

	.digit-span-inner {
		max-width: 920px;
		margin: 0 auto;
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
		align-items: flex-start;
		margin-bottom: 1.5rem;
		gap: 1rem;
	}

	.header-content h1 {
		font-size: 2.5rem;
		margin-bottom: 0.25rem;
		color: #667eea;
	}

	.header-right {
		display: flex;
		gap: 0.75rem;
		align-items: center;
		flex-shrink: 0;
	}

	.classic-badge {
		display: inline-block;
		background: linear-gradient(135deg, rgba(102, 126, 234, 0.12), rgba(118, 75, 162, 0.12));
		color: #667eea;
		font-size: 0.8rem;
		font-weight: 600;
		padding: 0.3rem 0.9rem;
		border-radius: 20px;
		border: 1px solid rgba(102, 126, 234, 0.25);
		margin-top: 0.4rem;
		letter-spacing: 0.02em;
	}

	.task-concept {
		background: #f8fafc;
		border-left: 4px solid #667eea;
		padding: 1.25rem 1.5rem;
		border-radius: 0 10px 10px 0;
		margin-bottom: 2rem;
	}

	.task-concept h2 {
		color: #1e293b;
		font-size: 1.15rem;
		margin-bottom: 0.5rem;
	}

	.task-concept p {
		color: #475569;
		line-height: 1.6;
		margin: 0;
	}

	.help-btn {
		background: white;
		color: #667eea;
		border: 2px solid #667eea;
		border-radius: 50%;
		width: 40px;
		height: 40px;
		font-size: 1.1rem;
		font-weight: bold;
		cursor: pointer;
		transition: all 0.2s;
	}

	.help-btn:hover {
		background: #667eea;
		color: white;
		transform: scale(1.1);
	}

	.subtitle {
		font-size: 1rem;
		color: #64748b;
		margin: 0;
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

	/* Info Grid - two-column layout */
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
		font-size: 1.1rem;
		margin-bottom: 1rem;
	}

	.tips-list {
		display: flex;
		flex-direction: column;
		gap: 0.65rem;
	}

	.tip-item {
		background: #f0fdf4;
		padding: 0.65rem 1rem;
		border-radius: 8px;
		color: #15803d;
		font-size: 0.9rem;
		line-height: 1.5;
	}

	.tip-item strong {
		color: #166534;
	}

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
		padding: 0.875rem 1rem;
		border-radius: 8px;
	}

	.structure-num {
		width: 44px;
		height: 44px;
		background: #4338ca;
		color: white;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.1rem;
		font-weight: bold;
		flex-shrink: 0;
	}

	.structure-text {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.structure-text strong {
		font-size: 0.95rem;
		color: #2c3e50;
	}

	.structure-text span {
		font-size: 0.82rem;
		color: #666;
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
		font-size: 0.88rem;
		line-height: 1.5;
		color: #555;
	}

	.clinical-item strong {
		color: #667eea;
		display: block;
		margin-bottom: 0.2rem;
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
		background: #4338ca;
		color: white;
		border: none;
		padding: 1.25rem 3rem;
		font-size: 1.2rem;
		font-weight: bold;
		border-radius: 12px;
		cursor: pointer;
		transition: all 0.3s;
		box-shadow: 0 4px 15px rgba(67, 56, 202, 0.35);
	}

	.start-button:hover {
		transform: translateY(-3px);
		box-shadow: 0 6px 25px rgba(67, 56, 202, 0.5);
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
		transition: all 0.2s;
	}

	.btn-secondary:hover {
		background: #e5e7eb;
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

	.feedback-screen.correct .feedback-icon {
		color: #059669;
	}

	.feedback-screen.incorrect .feedback-icon {
		color: #dc2626;
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

	/* Help Modal Overlay */
	.modal-overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: 1rem;
	}

	.modal-content {
		background: white;
		padding: 2rem;
		border-radius: 16px;
		max-width: 560px;
		width: 100%;
		max-height: 80vh;
		overflow-y: auto;
		position: relative;
	}

	.modal-content h2 {
		color: #1e293b;
		margin-bottom: 1.5rem;
		font-size: 1.4rem;
	}

	.close-btn {
		position: absolute;
		top: 1rem;
		right: 1rem;
		width: 36px;
		height: 36px;
		border: none;
		background: #f1f5f9;
		color: #475569;
		font-size: 1.4rem;
		border-radius: 50%;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: background 0.2s;
	}

	.close-btn:hover {
		background: #e2e8f0;
	}

	.strategy {
		margin-bottom: 1.25rem;
		padding: 1rem;
		background: #f8f9fa;
		border-radius: 8px;
		border-left: 4px solid #667eea;
	}

	.strategy h3 {
		margin: 0 0 0.4rem 0;
		color: #1e293b;
		font-size: 1rem;
	}

	.strategy p {
		margin: 0;
		color: #555;
		line-height: 1.6;
		font-size: 0.9rem;
	}

	.help-note {
		background: linear-gradient(135deg, rgba(102, 126, 234, 0.08), rgba(118, 75, 162, 0.08));
		padding: 1rem;
		border-radius: 8px;
		color: #667eea;
		font-style: italic;
		font-size: 0.9rem;
		text-align: center;
		margin-top: 1rem;
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

		.digit-span-inner {
			max-width: 100%;
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

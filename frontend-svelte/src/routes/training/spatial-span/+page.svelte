<script>
	import { API_BASE_URL } from '$lib/api';
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

	// Task states
	const STATE = {
		LOADING: 'loading',
		INSTRUCTIONS: 'instructions',
		READY: 'ready',
		SHOWING: 'showing',
		INPUT: 'input',
		FEEDBACK: 'feedback',
		COMPLETE: 'complete'
	};

	let state = STATE.LOADING;
	let difficulty = 5;
	let trials = [];
	let recordedTrials = [];
	let currentTrialIndex = 0;
	let currentTrial = null;
	let userResponse = [];
	let gridSize = 3;
	let highlightedBlock = null;
	let startTime = 0;
	let showHelp = false;
	let sessionResults = null;
	let taskId = null;
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';
	let sessionRunId = 0;
	let isDisposed = false;
	let lastResponseCorrect = false;
	const scheduledTimeouts = new Set();

	function t(text) {
		return translateText(text, $locale);
	}

	function n(value, options = {}) {
		return formatNumber(value, $locale, options);
	}

	function pct(value, options = {}) {
		return formatPercent(value, $locale, {
			minimumFractionDigits: 1,
			maximumFractionDigits: 1,
			...options
		});
	}

	function cloneData(value) {
		if (typeof structuredClone === 'function') {
			return structuredClone(value);
		}

		return JSON.parse(JSON.stringify(value));
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
		userResponse = [];
		gridSize = 3;
		highlightedBlock = null;
		startTime = 0;
		sessionResults = null;
		lastResponseCorrect = false;
	}

	function trialLabel(current, total) {
		return $locale === 'bn' ? `ট্রায়াল ${n(current)} / ${n(total)}` : `Trial ${current} of ${total}`;
	}

	function spanModeLabel(mode) {
		if (mode === 'backward') {
			return $locale === 'bn' ? 'উল্টো ক্রম' : 'Backward';
		}

		return $locale === 'bn' ? 'সামনের ক্রম' : 'Forward';
	}

	function difficultyChangeLabel(before, after) {
		return $locale === 'bn'
			? `কঠিনতা: ${n(before)} → ${n(after)}`
			: `Difficulty: ${before} → ${after}`;
	}

	// Timings come from each trial's display_ms / interval_ms set by the backend
	// based on the exact difficulty level — no coarse frontend brackets needed.

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
			state = STATE.LOADING;
			const userData = JSON.parse(localStorage.getItem('user') || '{}');
			const userId = userData.id;

			if (!userId) {
				goto('/login');
				return;
			}

			// Get user's current difficulty from their training plan
			const planRes = await fetch(`${API_BASE_URL}/api/training/training-plan/${userId}`);
			const plan = await planRes.json();

			let userDifficulty = 5; // Default
			if (plan && plan.current_difficulty) {
				const currentDiff =
					typeof plan.current_difficulty === 'string'
						? JSON.parse(plan.current_difficulty)
						: plan.current_difficulty;
				userDifficulty = currentDiff.working_memory || 5;
			}

			difficulty = userDifficulty;
			console.log('📊 Spatial Span - Loaded difficulty:', difficulty);

			// Generate session
			const response = await fetch(
				`${API_BASE_URL}/api/training/tasks/spatial-span/generate/${userId}?difficulty=${difficulty}&num_trials=8`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' }
				}
			);

			if (!response.ok) throw new Error('Failed to load session');

			const data = await response.json();
			recordedTrials = data.trials.map((trial) => ({
				...trial,
				user_response: [],
				reaction_time: 0
			}));
			trials = cloneData(recordedTrials);
			playMode = TASK_PLAY_MODE.RECORDED;
			practiceStatusMessage = '';
			resetSessionState();
			state = STATE.INSTRUCTIONS;
		} catch (error) {
			console.error('Error loading session:', error);
			alert(t('Failed to load task session'));
			goto('/dashboard');
		}
	}

	function startSession(nextMode = TASK_PLAY_MODE.RECORDED) {
		if (!recordedTrials.length) return;

		invalidateRun();
		playMode = nextMode;
		practiceStatusMessage = '';
		resetSessionState();
		const practicePayload = buildPracticePayload('spatial-span', { trials: recordedTrials });
		trials = nextMode === TASK_PLAY_MODE.PRACTICE ? practicePayload.trials : cloneData(recordedTrials);
		startTrial();
	}

	function leavePractice(completed = false) {
		invalidateRun();
		playMode = TASK_PLAY_MODE.RECORDED;
		trials = cloneData(recordedTrials);
		resetSessionState();
		practiceStatusMessage = completed ? getPracticeCopy($locale).complete : '';
		state = STATE.INSTRUCTIONS;
	}

	function startTrial() {
		const runId = sessionRunId;
		currentTrial = trials[currentTrialIndex];
		gridSize = currentTrial.grid_size;
		userResponse = [];
		highlightedBlock = null;
		state = STATE.READY;

		scheduleTimeout(() => {
			state = STATE.SHOWING;
			playSequence(runId);
		}, 800, runId);
	}

	function playSequence(runId = sessionRunId, stepIndex = 0) {
		if (!currentTrial) return;

		const sequence = currentTrial.sequence;
		const highlightTime = currentTrial.display_ms ?? 750;
		const intervalTime = currentTrial.interval_ms ?? 300;

		if (stepIndex >= sequence.length) {
			highlightedBlock = null;
			state = STATE.INPUT;
			startTime = Date.now();
			return;
		}

		highlightedBlock = sequence[stepIndex];
		scheduleTimeout(() => {
			highlightedBlock = null;
			if (stepIndex >= sequence.length - 1) {
				playSequence(runId, stepIndex + 1);
				return;
			}

			scheduleTimeout(() => {
				playSequence(runId, stepIndex + 1);
			}, intervalTime, runId);
		}, highlightTime, runId);
	}

	function handleBlockClick(blockIndex) {
		if (state !== STATE.INPUT) return;
		userResponse = [...userResponse, blockIndex];
	}

	function undoLastClick() {
		if (state !== STATE.INPUT || userResponse.length === 0) return;
		userResponse = userResponse.slice(0, -1);
	}

	function clearClicks() {
		if (state !== STATE.INPUT) return;
		userResponse = [];
	}

	function completeResponse() {
		const reactionTime = Date.now() - startTime;
		trials[currentTrialIndex].user_response = userResponse;
		trials[currentTrialIndex].reaction_time = reactionTime;
		lastResponseCorrect = checkCorrect();
		state = STATE.FEEDBACK;

		const runId = sessionRunId;
		scheduleTimeout(() => {
			if (currentTrialIndex < trials.length - 1) {
				currentTrialIndex += 1;
				startTrial();
				return;
			}

			if (playMode === TASK_PLAY_MODE.PRACTICE) {
				leavePractice(true);
				return;
			}

			submitSession();
		}, 1500, runId);
	}

	function checkCorrect() {
		const expected = currentTrial.span_type === 'backward' 
			? [...currentTrial.sequence].reverse() 
			: currentTrial.sequence;
		
		return JSON.stringify(userResponse) === JSON.stringify(expected);
	}

	async function submitSession() {
		state = STATE.LOADING;
		
		try {
			const userData = JSON.parse(localStorage.getItem('user') || '{}');
			const userId = userData.id;

			const response = await fetch(
				`${API_BASE_URL}/api/training/tasks/spatial-span/submit/${userId}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						difficulty: difficulty,
						trials: trials,
						task_id: taskId
					})
				}
			);

			if (!response.ok) throw new Error('Failed to submit session');

			sessionResults = await response.json();
			state = STATE.COMPLETE;
		} catch (error) {
			console.error('Error submitting session:', error);
			alert(t('Failed to submit results'));
		}
	}

	function isBlockClicked(index) {
		return userResponse.includes(index);
	}

	function getClickNumber(index) {
		// Show all click numbers for this block if it was clicked multiple times
		const clickNumbers = [];
		userResponse.forEach((blockIdx, i) => {
			if (blockIdx === index) {
				clickNumbers.push(i + 1);
			}
		});
		return clickNumbers.length > 0 ? clickNumbers.join(',') : null;
	}

	function toggleHelp() {
		showHelp = !showHelp;
	}
</script>

<div class="spatial-span-container" data-localize-skip>
<div class="spatial-span-inner">
	{#if state === STATE.LOADING}
		<div class="loading-wrapper">
			<LoadingSkeleton variant="card" count={3} />
		</div>
	{:else if state === STATE.INSTRUCTIONS}
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />
		<div class="instructions-card">
			<div class="header">
				<div class="header-content">
					<h1>{t('Spatial Span Test')}</h1>
					<p class="subtitle">{t('Visuospatial Working Memory Training')}</p>
					<div class="classic-badge">{t('Corsi Block Test · WMS-IV Component')}</div>
				</div>
				<div class="header-right">
					<DifficultyBadge {difficulty} domain="Working Memory" />
					<button class="help-btn" on:click={toggleHelp} aria-label={t('Help')}>?</button>
				</div>
			</div>

			<div class="task-concept">
				<h2>{t('Your Task: Remember the Block Sequence')}</h2>
				<p>{t('Blocks on the grid will light up one at a time in a specific order. Watch carefully, then recreate the sequence by clicking the blocks — either in the same order or in reverse.')}</p>
			</div>

			<div class="rules-grid">
				<div class="rule-card">
					<div class="rule-icon">→</div>
					<h3>{t('Forward Span')}</h3>
					<p>{t('Click blocks in the same order they lit up')}</p>
					<div class="rule-example">{t('Sequence: 1→2→3 → You click: 1→2→3')}</div>
				</div>
				<div class="rule-card">
					<div class="rule-icon">←</div>
					<h3>{t('Backward Span')}</h3>
					<p>{t('Click blocks in the reverse order they lit up')}</p>
					<div class="rule-example">{t('Sequence: 1→2→3 → You click: 3→2→1')}</div>
				</div>
			</div>

			<div class="info-grid">
				<div class="info-section">
					<h3>{t('Tips for Success')}</h3>
					<div class="tips-list">
						<div class="tip-item">✓ <strong>{t('Visualize the path:')}</strong> {t('Imagine drawing a line connecting the blocks')}</div>
						<div class="tip-item">✓ <strong>{t('Spatial chunking:')}</strong> {t('Group blocks into L-shapes, diagonals, etc.')}</div>
						<div class="tip-item">✓ <strong>{t('Mental rehearsal:')}</strong> {t('Replay the sequence before clicking')}</div>
						<div class="tip-item">✓ <strong>{t('Landmark method:')}</strong> {t('Use corner blocks as anchors')}</div>
					</div>
				</div>
				<div class="info-section">
					<h3>{t('Session Info')}</h3>
					<div class="structure-list">
						<div class="structure-item">
							<div class="structure-num">{n(difficulty)}</div>
							<div class="structure-text">
								<strong>{t('Difficulty Level')}</strong>
								<span>{t('Adapts after each session')}</span>
							</div>
						</div>
						<div class="structure-item">
							<div class="structure-num">{n(trials.length)}</div>
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
						<strong>{t('Standard:')}</strong> {t('Corsi Block Test — neuropsychological gold standard since 1972')}
					</div>
					<div class="clinical-item">
						<strong>{t('Measures:')}</strong> {t('Visuospatial working memory — distinct from verbal memory')}
					</div>
					<div class="clinical-item">
						<strong>{t('MS Relevance:')}</strong> {t('Correlated with MS lesion load (Rao et al., 1991); WMS-IV component')}
					</div>
					<div class="clinical-item">
						<strong>{t('Clinical Use:')}</strong> {t('Standard in neuropsychological and rehabilitation assessments')}
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
	{:else if state === STATE.READY}
		{#if playMode === TASK_PLAY_MODE.PRACTICE}
			<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
		{/if}
		<div class="ready-screen">
			<h1 class="ready-text">{t('Get Ready...')}</h1>
			<div class="trial-counter">{trialLabel(currentTrialIndex + 1, trials.length)}</div>
			{#if currentTrial}
				<div class="span-type-indicator {currentTrial.span_type}">
					{spanModeLabel(currentTrial.span_type)} {t('Span')}
				</div>
			{/if}
		</div>
	{:else if state === STATE.SHOWING || state === STATE.INPUT}
		{#if playMode === TASK_PLAY_MODE.PRACTICE}
			<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
		{/if}
		<div class="trial-screen">
			<div class="header">
				<div class="trial-info">
					<span class="trial-number">{$locale === 'bn' ? `ট্রায়াল ${n(currentTrialIndex + 1)}/${n(trials.length)}` : `Trial ${currentTrialIndex + 1}/${trials.length}`}</span>
					<span class="span-type">{spanModeLabel(currentTrial.span_type)}</span>
				</div>
				<button class="help-button" on:click={toggleHelp}>?</button>
			</div>

			{#if state === STATE.SHOWING}
				<p class="instruction">{t('Watch the sequence...')}</p>
			{:else}
				<div class="input-header">
					<p class="instruction">
						{t(
							currentTrial.span_type === 'backward'
								? 'Click blocks in REVERSE order'
								: 'Click blocks in the SAME order'
						)}
					</p>
					<div class="control-buttons">
						<button class="control-btn" on:click={undoLastClick} disabled={userResponse.length === 0}>
							↶ {t('Undo')}
						</button>
						<button class="control-btn" on:click={clearClicks} disabled={userResponse.length === 0}>
							✕ {t('Clear')}
						</button>
						<button class="submit-btn" on:click={completeResponse} disabled={userResponse.length === 0}>
							{t('Submit')} ✓
						</button>
					</div>
				</div>
			{/if}

			<div class="grid-container" style="--grid-size: {gridSize}">
				{#each Array(gridSize * gridSize) as _, index}
					<div
						class="block"
						class:highlighted={highlightedBlock === index}
						class:clicked={isBlockClicked(index)}
						class:clickable={state === STATE.INPUT}
						class:showing={state === STATE.SHOWING}
						on:click={() => handleBlockClick(index)}
						role="button"
						tabindex={state === STATE.INPUT ? 0 : -1}
						on:keydown={(e) => e.key === 'Enter' && handleBlockClick(index)}
					>
						{#if getClickNumber(index) !== null}
							<span class="click-number">{getClickNumber(index)}</span>
						{/if}
					</div>
				{/each}
			</div>
		</div>
	{:else if state === STATE.FEEDBACK}
		{#if playMode === TASK_PLAY_MODE.PRACTICE}
			<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
		{/if}
		<div class="feedback-screen {lastResponseCorrect ? 'correct' : 'incorrect'}">
			<div class="feedback-icon">{lastResponseCorrect ? '✓' : '✗'}</div>
			<p class="feedback-text">{lastResponseCorrect ? t('Correct!') : t('Incorrect')}</p>
		</div>
	{:else if state === STATE.COMPLETE}
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />
		<div class="complete-screen">
			<div class="results-header">
				<h1>{t('Session Complete!')}</h1>
				<p class="subtitle">{t('Great work on your Spatial Span training')}</p>
			</div>

			{#if sessionResults.new_badges && sessionResults.new_badges.length > 0}
				<div class="badges-section">
					<BadgeNotification badges={sessionResults.new_badges} />
				</div>
			{/if}

			<div class="metrics-grid">
				<div class="metric-card primary-card">
					<div class="metric-label">{t('Overall Score')}</div>
					<div class="metric-value">{n(sessionResults.metrics.score)}</div>
				</div>
				<div class="metric-card">
					<div class="metric-label">{t('Accuracy')}</div>
					<div class="metric-value">{pct(sessionResults.metrics.accuracy)}</div>
				</div>
				<div class="metric-card">
					<div class="metric-label">{t('Longest Span')}</div>
					<div class="metric-value">{n(sessionResults.metrics.longest_span)}</div>
					<div class="metric-detail">{t('blocks')}</div>
				</div>
				<div class="metric-card">
					<div class="metric-label">{t('Consistency')}</div>
					<div class="metric-value">{pct(sessionResults.metrics.consistency)}</div>
				</div>
			</div>

			<div class="breakdown-section">
				<h3>{t('Performance Breakdown')}</h3>
				<div class="breakdown-row">
					<span>{t('Forward Span:')}</span>
					<span class="breakdown-value">{pct(sessionResults.metrics.forward_accuracy)}</span>
				</div>
				<div class="breakdown-row">
					<span>{t('Backward Span:')}</span>
					<span class="breakdown-value">{pct(sessionResults.metrics.backward_accuracy)}</span>
				</div>
			</div>

			<div class="difficulty-adjust">
				<h3>{t('Difficulty Adjustment')}</h3>
				<div class="difficulty-change">
					<span class="diff-before">{t('Level')} {n(sessionResults.difficulty_before)}</span>
					<span class="diff-arrow">→</span>
					<span class="diff-after">{t('Level')} {n(sessionResults.difficulty_after)}</span>
				</div>
				<p class="adaptation-reason">{t(sessionResults.adaptation_reason)}</p>
			</div>

			<div class="actions">
				<button class="btn-secondary" on:click={() => goto('/dashboard')}>
					{t('View Dashboard')}
				</button>
				<button class="start-button" on:click={loadSession}>
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
		on:click={toggleHelp}
		on:keydown={(e) => e.key === 'Escape' && toggleHelp()}
	>
		<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
		<div
			class="modal-content"
			role="document"
			on:click|stopPropagation
			on:keydown|stopPropagation
		>
			<button class="close-btn" on:click={toggleHelp}>&times;</button>
			<h2>{t('Memory Strategies')}</h2>
			<div class="strategy">
				<h3>{t('Visual Imagery')}</h3>
				<p>{t('Imagine drawing a line connecting the blocks as they light up. Visualize the shape or pattern created by the sequence.')}</p>
			</div>
			<div class="strategy">
				<h3>{t('Spatial Chunking')}</h3>
				<p>{t('Group blocks into meaningful patterns: L-shapes, diagonals, squares, or other geometric forms you recognize.')}</p>
			</div>
			<div class="strategy">
				<h3>{t('Mental Rehearsal')}</h3>
				<p>{t('After the sequence finishes, mentally replay it 1-2 times before clicking. This strengthens the memory trace.')}</p>
			</div>
			<div class="strategy">
				<h3>{t('Landmark Method')}</h3>
				<p>{t('Use corner blocks or central blocks as anchors. Remember other positions relative to these landmarks.')}</p>
			</div>
		</div>
	</div>
{/if}

<style>
	.spatial-span-container {
		background: #C8DEFA;
		min-height: 100vh;
		padding: 2rem 1rem;
	}

	.spatial-span-inner {
		max-width: 900px;
		margin: 0 auto;
	}

	.loading-wrapper {
		padding: 2rem 0;
	}

	/* ── Instructions ── */
	.instructions-card {
		background: #FFFFFF;
		border-radius: 16px;
		padding: 2.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07), 0 1px 3px rgba(0, 0, 0, 0.06);
	}

	.header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 1.5rem;
		gap: 1rem;
		flex-wrap: wrap;
	}

	.header-content h1 {
		font-size: 1.8rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 0.25rem;
	}

	.header-right {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		flex-shrink: 0;
	}

	.subtitle {
		color: #64748b;
		margin: 0 0 0.75rem;
		font-size: 0.95rem;
	}

	.classic-badge {
		display: inline-block;
		background: rgba(102, 126, 234, 0.12);
		color: #667eea;
		font-size: 0.75rem;
		font-weight: 600;
		padding: 0.3rem 0.75rem;
		border-radius: 20px;
	}

	.task-concept {
		background: linear-gradient(135deg, rgba(102, 126, 234, 0.08), rgba(118, 75, 162, 0.08));
		border: 1px solid rgba(102, 126, 234, 0.2);
		border-radius: 12px;
		padding: 1.25rem 1.5rem;
		margin-bottom: 1.5rem;
	}

	.task-concept h2 {
		font-size: 1rem;
		font-weight: 700;
		color: #667eea;
		margin: 0 0 0.5rem;
	}

	.task-concept p {
		color: #374151;
		margin: 0;
		line-height: 1.6;
	}

	.rules-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
		margin-bottom: 1.5rem;
	}

	.rule-card {
		background: #f8fafc;
		padding: 1.25rem;
		border-radius: 12px;
		border-left: 4px solid #667eea;
		text-align: center;
	}

	.rule-icon {
		font-size: 2rem;
		margin-bottom: 0.5rem;
	}

	.rule-card h3 {
		font-size: 0.95rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 0.35rem;
	}

	.rule-card p {
		color: #64748b;
		font-size: 0.85rem;
		margin: 0 0 0.5rem;
	}

	.rule-example {
		font-size: 1rem;
		font-weight: 600;
		color: #667eea;
	}

	/* Info grid */
	.info-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
		margin-bottom: 1.5rem;
	}

	.info-section {
		background: #f8fafc;
		border-radius: 12px;
		padding: 1.25rem;
	}

	.info-section h3 {
		font-size: 0.9rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 0.75rem;
	}

	.tips-list {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.tip-item {
		background: #f0fdf4;
		padding: 0.5rem 0.75rem;
		border-radius: 8px;
		color: #15803d;
		font-size: 0.85rem;
		line-height: 1.4;
	}

	.tip-item strong {
		color: #166534;
	}

	.structure-list {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	.structure-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.structure-num {
		width: 36px;
		height: 36px;
		border-radius: 50%;
		background: #4338ca;
		color: white;
		font-weight: 700;
		font-size: 0.9rem;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}

	.structure-text {
		display: flex;
		flex-direction: column;
	}

	.structure-text strong {
		font-size: 0.85rem;
		color: #1e293b;
	}

	.structure-text span {
		font-size: 0.8rem;
		color: #64748b;
	}

	/* Clinical info */
	.clinical-info {
		background: linear-gradient(135deg, rgba(102, 126, 234, 0.06), rgba(118, 75, 162, 0.06));
		border: 1px solid rgba(102, 126, 234, 0.15);
		border-radius: 12px;
		padding: 1.25rem 1.5rem;
		margin-bottom: 1.5rem;
	}

	.clinical-info h3 {
		font-size: 0.9rem;
		font-weight: 700;
		color: #667eea;
		margin: 0 0 0.75rem;
	}

	.clinical-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0.6rem;
	}

	.clinical-item {
		font-size: 0.82rem;
		color: #4b5563;
		line-height: 1.4;
	}

	.clinical-item strong {
		color: #374151;
	}

	/* Buttons */
	.button-group {
		display: flex;
		gap: 1rem;
		justify-content: center;
		flex-wrap: wrap;
		margin-top: 1.5rem;
	}

	.start-button {
		background: #4338ca;
		color: white;
		border: none;
		padding: 0.9rem 2.5rem;
		font-size: 1rem;
		font-weight: 600;
		border-radius: 10px;
		cursor: pointer;
		box-shadow: 0 4px 14px rgba(67, 56, 202, 0.3);
		transition: all 0.2s;
	}

	.start-button:hover:not(:disabled) {
		transform: translateY(-2px);
		box-shadow: 0 6px 20px rgba(67, 56, 202, 0.4);
	}

	.start-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
		transform: none;
	}

	.btn-secondary {
		background: white;
		color: #667eea;
		border: 2px solid #667eea;
		padding: 0.9rem 2rem;
		font-size: 1rem;
		font-weight: 600;
		border-radius: 10px;
		cursor: pointer;
		transition: all 0.2s;
	}

	.btn-secondary:hover {
		background: rgba(102, 126, 234, 0.06);
		transform: translateY(-2px);
	}

	.help-btn {
		width: 38px;
		height: 38px;
		border-radius: 50%;
		border: 2px solid #667eea;
		background: white;
		color: #667eea;
		font-size: 1.2rem;
		font-weight: bold;
		cursor: pointer;
		transition: all 0.2s;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}

	.help-btn:hover {
		background: #667eea;
		color: white;
	}

	/* ── Ready Screen ── */
	.ready-screen {
		text-align: center;
		background: white;
		padding: 4rem;
		border-radius: 16px;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
	}

	.ready-text {
		font-size: 3rem;
		color: #667eea;
		margin-bottom: 1rem;
		animation: pulse 1s ease-in-out;
	}

	.trial-counter {
		font-size: 1.1rem;
		color: #64748b;
		margin-bottom: 1rem;
	}

	.span-type-indicator {
		font-size: 1.3rem;
		padding: 0.75rem 2rem;
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

	/* ── Trial Screen ── */
	.trial-screen {
		text-align: center;
		background: white;
		padding: 2rem;
		border-radius: 16px;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
	}

	.trial-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
	}

	.trial-info {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.trial-number {
		font-size: 1rem;
		font-weight: 600;
		color: #64748b;
	}

	.span-badge {
		font-size: 0.85rem;
		font-weight: 600;
		padding: 0.3rem 0.9rem;
		border-radius: 20px;
	}

	.span-badge.forward {
		background: #dbeafe;
		color: #1e40af;
	}

	.span-badge.backward {
		background: #fce7f3;
		color: #9f1239;
	}

	.instruction {
		font-size: 1.2rem;
		margin-bottom: 1.25rem;
	}

	.instruction.watching {
		color: #667eea;
		font-weight: 600;
	}

	.instruction.responding {
		color: #1e293b;
		font-weight: 600;
	}

	.input-header {
		margin-bottom: 1.25rem;
	}

	.control-buttons {
		display: flex;
		gap: 0.5rem;
		justify-content: center;
		margin-top: 0.75rem;
	}

	.control-btn {
		padding: 0.5rem 1rem;
		border: 2px solid #667eea;
		background: white;
		color: #667eea;
		border-radius: 8px;
		font-size: 0.9rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
	}

	.control-btn:hover:not(:disabled) {
		background: #667eea;
		color: white;
		transform: translateY(-2px);
	}

	.control-btn:disabled {
		opacity: 0.3;
		cursor: not-allowed;
		border-color: #cbd5e1;
		color: #94a3b8;
	}

	.submit-btn {
		padding: 0.5rem 1.4rem;
		border: none;
		background: #4338ca;
		color: white;
		border-radius: 8px;
		font-size: 0.9rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
		box-shadow: 0 2px 8px rgba(67, 56, 202, 0.3);
	}

	.submit-btn:hover:not(:disabled) {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(67, 56, 202, 0.45);
	}

	.submit-btn:disabled {
		opacity: 0.35;
		cursor: not-allowed;
		background: #cbd5e1;
		box-shadow: none;
	}

	/* Grid */
	.grid-container {
		display: grid;
		grid-template-columns: repeat(var(--grid-size), 1fr);
		gap: 12px;
		max-width: 480px;
		margin: 0 auto;
		padding: 2rem;
	}

	.block {
		aspect-ratio: 1;
		background: linear-gradient(145deg, #f1f5f9, #e2e8f0);
		border-radius: 12px;
		border: 3px solid #cbd5e1;
		transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.5rem;
		font-weight: bold;
		color: white;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
	}

	.block.highlighted {
		background: linear-gradient(145deg, #4338ca, #3730a3);
		border-color: #4338ca;
		box-shadow: 0 0 28px rgba(67, 56, 202, 0.65), 0 4px 8px rgba(0, 0, 0, 0.15);
		transform: scale(1.15);
	}

	.block.clickable {
		cursor: pointer;
	}

	.block.clickable:hover:not(.clicked) {
		background: linear-gradient(145deg, #eff6ff, #dbeafe);
		border-color: #93c5fd;
		transform: scale(1.05);
		box-shadow: 0 4px 10px rgba(102, 126, 234, 0.2);
	}

	.block.clicked {
		background: linear-gradient(145deg, #4338ca, #4f46e5);
		border-color: #4338ca;
		box-shadow: 0 4px 10px rgba(67, 56, 202, 0.4), inset 0 2px 4px rgba(0, 0, 0, 0.15);
		transform: scale(0.95);
	}

	.block.showing {
		cursor: default;
	}

	.click-number {
		font-size: 1.4rem;
		font-weight: bold;
		color: white;
		text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
	}

	/* Response progress indicator */
	.response-progress {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		margin-top: 1rem;
	}

	.progress-label {
		font-size: 0.85rem;
		color: #64748b;
		font-weight: 500;
	}

	.progress-dot {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		background: #e2e8f0;
		transition: background 0.2s;
	}

	.progress-dot.filled {
		background: #667eea;
	}

	.progress-text {
		font-size: 0.85rem;
		color: #64748b;
		font-weight: 600;
	}

	/* ── Feedback ── */
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
	}

	.feedback-screen.correct .feedback-text {
		color: #059669;
	}

	.feedback-screen.incorrect .feedback-text {
		color: #dc2626;
	}

	/* ── Complete Screen ── */
	.complete-screen {
		background: white;
		border-radius: 16px;
		padding: 3rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
	}

	.results-header {
		margin-bottom: 1.5rem;
	}

	.results-header h1 {
		font-size: 2rem;
		color: #1e293b;
		margin-bottom: 0.25rem;
	}

	.badges-section {
		margin: 1.5rem 0;
	}

	.metrics-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: 1rem;
		margin: 2rem 0;
	}

	.metric-card {
		padding: 1.5rem;
		background: #f8fafc;
		border-radius: 12px;
		text-align: center;
		border: 2px solid #e2e8f0;
	}

	.metric-card.primary-card {
		background: #4338ca;
		border: none;
		color: white;
	}

	.metric-label {
		font-size: 0.85rem;
		color: #64748b;
		margin-bottom: 0.5rem;
	}

	.metric-card.primary-card .metric-label {
		color: rgba(255, 255, 255, 0.85);
	}

	.metric-value {
		font-size: 2rem;
		font-weight: 700;
		color: #1e293b;
	}

	.metric-card.primary-card .metric-value {
		color: white;
	}

	.metric-detail {
		font-size: 0.8rem;
		color: #94a3b8;
		margin-top: 0.25rem;
	}

	.breakdown-section {
		background: #f8fafc;
		padding: 1.5rem;
		border-radius: 12px;
		margin: 1.5rem 0;
	}

	.breakdown-section h3 {
		color: #1e293b;
		margin-bottom: 1rem;
		font-size: 1rem;
	}

	.breakdown-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.5rem 0;
		border-bottom: 1px solid #e2e8f0;
		color: #475569;
	}

	.breakdown-row:last-child {
		border-bottom: none;
	}

	.breakdown-value {
		font-weight: 700;
		color: #667eea;
	}

	.difficulty-adjust {
		background: #f8fafc;
		padding: 1.5rem;
		border-radius: 12px;
		margin: 1.5rem 0;
		text-align: center;
	}

	.difficulty-adjust h3 {
		color: #1e293b;
		margin-bottom: 1rem;
		font-size: 1rem;
	}

	.difficulty-change {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 1rem;
		font-size: 1.4rem;
		margin-bottom: 0.75rem;
	}

	.diff-before,
	.diff-after {
		font-weight: 700;
		color: #667eea;
	}

	.diff-arrow {
		color: #94a3b8;
	}

	.adaptation-reason {
		color: #64748b;
		font-size: 0.9rem;
	}

	.actions {
		display: flex;
		gap: 1rem;
		margin-top: 2rem;
		justify-content: center;
		flex-wrap: wrap;
	}

	/* ── Help Modal ── */
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

	/* ── Animations ── */
	@keyframes pulse {
		0%, 100% { transform: scale(1); }
		50% { transform: scale(1.05); }
	}

	@keyframes scaleIn {
		0% { transform: scale(0); }
		50% { transform: scale(1.1); }
		100% { transform: scale(1); }
	}

	/* ── Responsive ── */
	@media (max-width: 768px) {
		.spatial-span-container {
			padding: 1rem;
		}

		.spatial-span-inner {
			max-width: 100%;
		}

		.instructions-card,
		.ready-screen,
		.trial-screen,
		.feedback-screen,
		.complete-screen {
			padding: 1.5rem;
		}

		.rules-grid {
			grid-template-columns: 1fr;
		}

		.info-grid {
			grid-template-columns: 1fr;
		}

		.ready-text {
			font-size: 2rem;
		}

		.metrics-grid {
			grid-template-columns: 1fr 1fr;
		}

		.actions {
			flex-direction: column;
		}

		.button-group {
			flex-direction: column;
			align-items: stretch;
		}
	}
</style>

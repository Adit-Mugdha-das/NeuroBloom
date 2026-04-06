<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
<<<<<<< HEAD
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import { formatNumber, formatPercent, locale, translateText } from '$lib/i18n';
=======
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
	import { formatNumber, formatPercent, locale, localeText, translateText } from '$lib/i18n';
	import { buildPracticePayload, getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
>>>>>>> ed2558175d01470eebd7f72c6220168adb0d88f6
	import { onMount } from 'svelte';

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
	let recordedTrials = [];

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

	function trialLabel(current, total) {
		return $locale === 'bn' ? `ট্রায়াল ${n(current)} / ${n(total)}` : `Trial ${current} of ${total}`;
	}

	function spanModeLabel(mode) {
		if (mode === 'backward') {
			return $locale === 'bn' ? '⬅️ উল্টো ক্রম' : '⬅️ Backward';
		}

		return $locale === 'bn' ? '➡️ সামনের ক্রম' : '➡️ Forward';
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
				`http://localhost:8000/api/training/tasks/spatial-span/generate/${userId}?difficulty=${difficulty}&num_trials=8`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' }
				}
			);

			if (!response.ok) throw new Error('Failed to load session');

			const data = await response.json();
			const mappedTrials = data.trials.map(t => ({
				...t,
				user_response: [],
				reaction_time: 0
			}));
			trials = structuredClone(mappedTrials);
			recordedTrials = structuredClone(mappedTrials);
			
			state = STATE.INSTRUCTIONS;
		} catch (error) {
			console.error('Error loading session:', error);
			alert(t('Failed to load task session'));
			goto('/dashboard');
		}
	}

	function startSession(nextMode = TASK_PLAY_MODE.RECORDED) {
		playMode = nextMode;
		practiceStatusMessage = '';
		console.log('Starting session, trials:', trials.length);
		state = STATE.READY;
		currentTrialIndex = 0;
		trials = nextMode === TASK_PLAY_MODE.PRACTICE
			? buildPracticePayload('spatial-span', { trials: recordedTrials }).trials
			: structuredClone(recordedTrials);
		setTimeout(() => startTrial(), 1000);
	}

	async function startTrial() {
		console.log('Starting trial', currentTrialIndex, 'of', trials.length);
		
		// Set up trial data first
		currentTrial = trials[currentTrialIndex];
		gridSize = currentTrial.grid_size;
		userResponse = [];
		console.log('Current trial:', currentTrial);
		
		// Show ready screen
		state = STATE.READY;
		await new Promise(resolve => setTimeout(resolve, 800));
		
		// Show sequence
		state = STATE.SHOWING;
		await playSequence();
		
		// Allow user input
		state = STATE.INPUT;
		startTime = Date.now();
	}

	async function playSequence() {
		const sequence = currentTrial.sequence;
		const highlightTime = currentTrial.display_ms  ?? 750;
		const intervalTime  = currentTrial.interval_ms ?? 300;

		for (let i = 0; i < sequence.length; i++) {
			highlightedBlock = sequence[i];
			await new Promise(resolve => setTimeout(resolve, highlightTime));
			highlightedBlock = null;
			
			if (i < sequence.length - 1) {
				await new Promise(resolve => setTimeout(resolve, intervalTime));
			}
		}

		highlightedBlock = null;
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

		// Show feedback
		state = STATE.FEEDBACK;
		
		setTimeout(() => {
			if (currentTrialIndex < trials.length - 1) {
				currentTrialIndex++;
				startTrial();
			} else {
				submitSession();
			}
		}, 1500);
	}

	function checkCorrect() {
		const expected = currentTrial.span_type === 'backward' 
			? [...currentTrial.sequence].reverse() 
			: currentTrial.sequence;
		
		return JSON.stringify(userResponse) === JSON.stringify(expected);
	}

	async function submitSession() {
		if (playMode === TASK_PLAY_MODE.PRACTICE) {
			trials = structuredClone(recordedTrials);
			playMode = TASK_PLAY_MODE.RECORDED;
			practiceStatusMessage = getPracticeCopy($locale).complete;
			state = STATE.INSTRUCTIONS;
			return;
		}

		state = STATE.LOADING;
		
		try {
			const userData = JSON.parse(localStorage.getItem('user') || '{}');
			const userId = userData.id;

			const response = await fetch(
				`http://localhost:8000/api/training/tasks/spatial-span/submit/${userId}`,
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
	{#if state === STATE.LOADING}
		<div class="loading-wrapper">
			<LoadingSkeleton variant="card" count={3} />
		</div>
	{:else if state === STATE.INSTRUCTIONS}
		<div class="instructions-card">
			<div class="header">
				<div class="header-content">
					<h1>🧠 {t('Spatial Span Test')}</h1>
					<p class="subtitle">{t('Visuospatial Working Memory Training')}</p>
					<div class="classic-badge">{t('Corsi Block Test · WMS-IV Component')}</div>
				</div>
				<div class="header-right">
					<DifficultyBadge {difficulty} domain="Working Memory" />
					<button class="help-btn" on:click={toggleHelp} aria-label={t('Help')}>?</button>
				</div>
			</div>

			<div class="task-concept">
				<h2>{t('💡 Your Task: Remember the Block Sequence')}</h2>
				<p>{t('Blocks on the grid will light up one at a time in a specific order. Watch carefully, then recreate the sequence by clicking the blocks — either in the same order or in reverse.')}</p>
			</div>

			<div class="instructions-grid">
				<div class="instruction-item">
					<div class="instruction-icon">➡️</div>
					<h3>{t('Forward Span')}</h3>
					<p>{t('Click blocks in the same order they lit up')}</p>
					<div class="instruction-note">{t('Sequence: 1→2→3 → You click: 1→2→3')}</div>
				</div>
				<div class="instruction-item">
					<div class="instruction-icon">⬅️</div>
					<h3>{t('Backward Span')}</h3>
					<p>{t('Click blocks in the reverse order they lit up')}</p>
					<div class="instruction-note">{t('Sequence: 1→2→3 → You click: 3→2→1')}</div>
				</div>
			</div>
<<<<<<< HEAD

			<div class="info-grid">
				<div class="info-section">
					<h3>{t('💪 Tips for Success')}</h3>
					<div class="tips-list">
						<div class="tip-item">✓ <strong>{t('Visualize the path:')}</strong> {t('Imagine drawing a line connecting the blocks')}</div>
						<div class="tip-item">✓ <strong>{t('Spatial chunking:')}</strong> {t('Group blocks into L-shapes, diagonals, etc.')}</div>
						<div class="tip-item">✓ <strong>{t('Mental rehearsal:')}</strong> {t('Replay the sequence before clicking')}</div>
						<div class="tip-item">✓ <strong>{t('Landmark method:')}</strong> {t('Use corner blocks as anchors')}</div>
					</div>
				</div>
				<div class="info-section">
					<h3>{t('📋 Session Info')}</h3>
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
				<h3>{t('📚 Clinical Significance')}</h3>
				<div class="clinical-grid">
					<div class="clinical-item">
						<strong>{t('📜 Standard:')}</strong> {t('Corsi Block Test — neuropsychological gold standard since 1972')}
					</div>
					<div class="clinical-item">
						<strong>{t('🎯 Measures:')}</strong> {t('Visuospatial working memory — distinct from verbal memory')}
					</div>
					<div class="clinical-item">
						<strong>{t('🏥 MS Relevance:')}</strong> {t('Correlated with MS lesion load (Rao et al., 1991); WMS-IV component')}
					</div>
					<div class="clinical-item">
						<strong>{t('🌍 Clinical Use:')}</strong> {t('Standard in neuropsychological and rehabilitation assessments')}
					</div>
				</div>
			</div>

			<div class="button-group">
				<button class="start-button" on:click={startSession} disabled={state !== STATE.INSTRUCTIONS}>
					{t('Begin Training')}
				</button>
				<button class="btn-secondary" on:click={() => goto('/dashboard')}>
					{t('Back to Dashboard')}
				</button>
			</div>
		</div>
	{:else if state === STATE.READY}
		<div class="ready-screen">
			<h1 class="ready-text">{t('Get Ready...')}</h1>
			<div class="trial-counter">{trialLabel(currentTrialIndex + 1, trials.length)}</div>
=======
			
			<TaskPracticeActions
				locale={$locale}
				startLabel={localeText({ en: 'Start Actual Task', bn: 'আসল টাস্ক শুরু করুন' }, $locale)}
				statusMessage={practiceStatusMessage}
				align="center"
				on:start={() => startSession(TASK_PLAY_MODE.RECORDED)}
				on:practice={() => startSession(TASK_PLAY_MODE.PRACTICE)}
			/>
		</div>
	{:else if state === STATE.READY}
		<div class="ready-screen">
			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} />
			{/if}
			<h2>{trialLabel(currentTrialIndex + 1, trials.length)}</h2>
>>>>>>> ed2558175d01470eebd7f72c6220168adb0d88f6
			{#if currentTrial}
				<div class="span-type-indicator {currentTrial.span_type}">
					{spanModeLabel(currentTrial.span_type)} {t('Span')}
				</div>
			{/if}
		</div>
	{:else if state === STATE.SHOWING || state === STATE.INPUT}
		<div class="trial-screen">
			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} />
			{/if}
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
<<<<<<< HEAD
		<div class="feedback-screen {checkCorrect() ? 'correct' : 'incorrect'}">
			<div class="feedback-icon">{checkCorrect() ? '✅' : '❌'}</div>
			<p class="feedback-text">{checkCorrect() ? t('Correct!') : t('Incorrect')}</p>
=======
		<div class="feedback-screen">
			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} />
			{/if}
			<div
				class="feedback-icon"
				style="background: {checkCorrect() ? '#4CAF50' : '#f44336'}"
			>
				{checkCorrect() ? '✓' : '✗'}
			</div>
			<p class="feedback-text">
				{checkCorrect() ? t('Correct!') : t('Incorrect')}
			</p>
>>>>>>> ed2558175d01470eebd7f72c6220168adb0d88f6
		</div>
	{:else if state === STATE.COMPLETE}
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
					<span>{t('➡️ Forward Span:')}</span>
					<span class="breakdown-value">{pct(sessionResults.metrics.forward_accuracy)}</span>
				</div>
				<div class="breakdown-row">
					<span>{t('⬅️ Backward Span:')}</span>
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
					{t('Back to Dashboard')}
				</button>
				<button class="start-button" on:click={() => window.location.reload()}>
					{t('Train Again')}
				</button>
			</div>
		</div>
	{/if}
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
				<h3>🎨 {t('Visual Imagery')}</h3>
				<p>{t('Imagine drawing a line connecting the blocks as they light up. Visualize the shape or pattern created by the sequence.')}</p>
			</div>
			<div class="strategy">
				<h3>🧩 {t('Spatial Chunking')}</h3>
				<p>{t('Group blocks into meaningful patterns: L-shapes, diagonals, squares, or other geometric forms you recognize.')}</p>
			</div>
			<div class="strategy">
				<h3>🔄 {t('Mental Rehearsal')}</h3>
				<p>{t('After the sequence finishes, mentally replay it 1-2 times before clicking. This strengthens the memory trace.')}</p>
			</div>
			<div class="strategy">
				<h3>📍 {t('Landmark Method')}</h3>
				<p>{t('Use corner blocks or central blocks as anchors. Remember other positions relative to these landmarks.')}</p>
			</div>
		</div>
	</div>
{/if}

<style>
	.spatial-span-container {
		max-width: 900px;
		margin: 0 auto;
		padding: 2rem;
		min-height: 100vh;
	}

	.loading-wrapper {
		padding: 2rem 0;
	}

	/* ── Instructions ── */
	.instructions-card {
		background: white;
<<<<<<< HEAD
		border-radius: 16px;
		padding: 3rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
=======
		border-radius: 12px;
		padding: 2rem;
		margin: 2rem 0;
		box-shadow: 0 2px 8px rgba(0,0,0,0.1);
		text-align: left;
	}

	.task-types {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
		margin: 1.5rem 0;
	}

	.type-card {
		background: #f8f9fa;
		padding: 1.5rem;
		border-radius: 8px;
		border-left: 4px solid #4CAF50;
	}

	.type-card h3 {
		margin: 0 0 0.5rem 0;
		color: #2c3e50;
	}

	.tips {
		background: #fff3cd;
		padding: 1.5rem;
		border-radius: 8px;
		margin-top: 1.5rem;
	}

	.tips h3 {
		margin: 0 0 1rem 0;
		color: #856404;
	}

	.tips ul {
		margin: 0;
		padding-left: 1.5rem;
	}

	.tips li {
		margin-bottom: 0.5rem;
		color: #856404;
	}

	.ready-screen {
		text-align: center;
		padding: 4rem 0;
	}

	.span-type {
		font-size: 1.5rem;
		font-weight: bold;
		color: #4CAF50;
		margin: 1rem 0;
	}

	.trial-screen {
		text-align: center;
>>>>>>> ed2558175d01470eebd7f72c6220168adb0d88f6
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

	.subtitle {
		font-size: 1rem;
		color: #64748b;
		margin: 0;
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

	.instructions-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.5rem;
		margin-bottom: 2rem;
	}

	.instruction-item {
		padding: 1.5rem;
		border: 2px solid #e2e8f0;
		border-radius: 12px;
		text-align: center;
	}

	.instruction-icon {
		font-size: 2.5rem;
		margin-bottom: 0.75rem;
	}

	.instruction-item h3 {
		color: #1e293b;
		margin-bottom: 0.5rem;
	}

	.instruction-item p {
		color: #475569;
		font-size: 0.9rem;
		margin-bottom: 0.75rem;
	}

	.instruction-note {
		background: #f8fafc;
		padding: 0.5rem 0.75rem;
		border-radius: 6px;
		font-size: 0.82rem;
		color: #64748b;
		font-family: monospace;
	}

	/* Info grid */
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
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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

	/* Clinical info */
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

	.start-button:hover:not(:disabled) {
		transform: translateY(-3px);
		box-shadow: 0 6px 25px rgba(102, 126, 234, 0.6);
	}

	.start-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
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
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border-radius: 8px;
		font-size: 0.9rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
		box-shadow: 0 2px 8px rgba(102, 126, 234, 0.35);
	}

	.submit-btn:hover:not(:disabled) {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.5);
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
		background: linear-gradient(145deg, #667eea, #764ba2);
		border-color: #4f46e5;
		box-shadow: 0 0 28px rgba(102, 126, 234, 0.75), 0 4px 8px rgba(0, 0, 0, 0.15);
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
		background: linear-gradient(145deg, #667eea, #4f46e5);
		border-color: #4338ca;
		box-shadow: 0 4px 10px rgba(102, 126, 234, 0.4), inset 0 2px 4px rgba(0, 0, 0, 0.15);
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
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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

		.instructions-card,
		.ready-screen,
		.trial-screen,
		.feedback-screen,
		.complete-screen {
			padding: 1.5rem;
		}

		.instructions-grid {
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

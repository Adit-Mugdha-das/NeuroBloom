<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import { formatNumber, formatPercent, locale, translateText } from '$lib/i18n';
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
			trials = data.trials.map(t => ({
				...t,
				user_response: [],
				reaction_time: 0
			}));
			
			state = STATE.INSTRUCTIONS;
		} catch (error) {
			console.error('Error loading session:', error);
			alert(t('Failed to load task session'));
			goto('/dashboard');
		}
	}

	function startSession() {
		console.log('Starting session, trials:', trials.length);
		state = STATE.READY;
		currentTrialIndex = 0;
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
		<div class="loading">
			<div class="spinner"></div>
			<p>{t('Loading Spatial Span Task...')}</p>
		</div>
	{:else if state === STATE.INSTRUCTIONS}
		<div class="instructions">
			<div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap;">
				<h1>{t('Spatial Span Test (Corsi Blocks)')}</h1>
				<DifficultyBadge {difficulty} domain="Working Memory" />
			</div>

			<div class="instruction-card">
				<h2>{t('How It Works')}</h2>
				<p>{t('Blocks will light up in a specific sequence. Your job is to remember the pattern.')}</p>
				
				<div class="task-types">
					<div class="type-card">
						<h3>{t('Forward Span')}</h3>
						<p>{t('Click blocks in the same order they lit up')}</p>
					</div>
					<div class="type-card">
						<h3>{t('Backward Span')}</h3>
						<p>{t('Click blocks in reverse order')}</p>
					</div>
				</div>
				
				<div class="tips">
					<h3>{t('Memory Strategies')}</h3>
					<ul>
						<li><strong>{t('Visualize the path:')}</strong> {t('Imagine drawing a line connecting the blocks')}</li>
						<li><strong>{t('Spatial chunking:')}</strong> {t('Group blocks into patterns (L-shape, diagonal, etc.)')}</li>
						<li><strong>{t('Mental rehearsal:')}</strong> {t('Replay the sequence in your mind before responding')}</li>
					</ul>
				</div>
			</div>
			
			<button class="start-button" on:click={startSession} disabled={state !== STATE.INSTRUCTIONS}>
				{t('Start Training Session')}
			</button>
		</div>
	{:else if state === STATE.READY}
		<div class="ready-screen">
			<h2>{trialLabel(currentTrialIndex + 1, trials.length)}</h2>
			{#if currentTrial}
				<p class="span-type">{spanModeLabel(currentTrial.span_type)} {t('Span')}</p>
			{/if}
			<p>{t('Watch carefully...')}</p>
		</div>
	{:else if state === STATE.SHOWING || state === STATE.INPUT}
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
		<div class="feedback-screen">
			<div
				class="feedback-icon"
				style="background: {checkCorrect() ? '#4CAF50' : '#f44336'}"
			>
				{checkCorrect() ? '✓' : '✗'}
			</div>
			<p class="feedback-text">
				{checkCorrect() ? t('Correct!') : t('Incorrect')}
			</p>
		</div>
	{:else if state === STATE.COMPLETE}
		<div class="complete-screen">
			<h1>{t('Session Complete!')} 🎉</h1>
			
			<div class="results-grid">
				<div class="result-card">
					<div class="result-value">{n(sessionResults.metrics.score)}</div>
					<div class="result-label">{t('Score')}</div>
				</div>
				<div class="result-card">
					<div class="result-value">{pct(sessionResults.metrics.accuracy)}</div>
					<div class="result-label">{t('Accuracy')}</div>
				</div>
				<div class="result-card">
					<div class="result-value">{n(sessionResults.metrics.longest_span)}</div>
					<div class="result-label">{t('Longest Span')}</div>
				</div>
				<div class="result-card">
					<div class="result-value">{pct(sessionResults.metrics.consistency)}</div>
					<div class="result-label">{t('Consistency')}</div>
				</div>
			</div>

			<div class="span-breakdown">
				<h3>{t('Performance Breakdown')}</h3>
				<div class="breakdown-row">
					<span>{t('Forward Span:')}</span>
					<span>{pct(sessionResults.metrics.forward_accuracy)}</span>
				</div>
				<div class="breakdown-row">
					<span>{t('Backward Span:')}</span>
					<span>{pct(sessionResults.metrics.backward_accuracy)}</span>
				</div>
			</div>

			<div class="difficulty-info">
				<p>{difficultyChangeLabel(sessionResults.difficulty_before, sessionResults.difficulty_after)}</p>
				<p class="adaptation-reason">{t(sessionResults.adaptation_reason)}</p>
			</div>

			{#if sessionResults.new_badges && sessionResults.new_badges.length > 0}
				<div class="new-badges">
					<h3>{t('New Badges Earned!')}</h3>
					{#each sessionResults.new_badges as badge}
						<div class="badge">
							<span class="badge-icon">{badge.icon}</span>
							<span class="badge-name">{badge.name}</span>
						</div>
					{/each}
				</div>
			{/if}

			<div class="actions">
				<button on:click={() => goto('/training')}>{t('Back to Training')}</button>
				<button on:click={() => goto('/dashboard')}>{t('View Dashboard')}</button>
			</div>
		</div>
	{/if}
</div>

{#if showHelp}
	<div
		class="help-modal"
		role="presentation"
		on:click={toggleHelp}
		on:keydown={(e) => e.key === 'Escape' && toggleHelp()}
	>
		<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
		<div
			class="help-content"
			role="document"
			on:click|stopPropagation
			on:keydown|stopPropagation
		>
			<button class="close-button" on:click={toggleHelp}>&times;</button>
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

	.loading {
		text-align: center;
		padding: 4rem 0;
	}

	.spinner {
		width: 50px;
		height: 50px;
		border: 4px solid #f3f3f3;
		border-top: 4px solid #4CAF50;
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin: 0 auto 1rem;
	}

	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	.instructions {
		text-align: center;
	}

	.instructions h1 {
		color: #2c3e50;
		margin-bottom: 2rem;
	}

	.instruction-card {
		background: white;
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

	.start-button {
		background: #4CAF50;
		color: white;
		border: none;
		padding: 1rem 3rem;
		font-size: 1.2rem;
		border-radius: 8px;
		cursor: pointer;
		margin-top: 2rem;
		transition: background 0.3s;
	}

	.start-button:hover {
		background: #45a049;
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
	}

	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
	}

	.trial-info {
		display: flex;
		gap: 1rem;
		align-items: center;
	}

	.trial-number {
		background: #e8f5e9;
		padding: 0.5rem 1rem;
		border-radius: 20px;
		font-weight: 500;
	}

	.help-button {
		width: 40px;
		height: 40px;
		border-radius: 50%;
		border: 2px solid #4CAF50;
		background: white;
		color: #4CAF50;
		font-size: 1.5rem;
		font-weight: bold;
		cursor: pointer;
		transition: all 0.3s;
	}

	.help-button:hover {
		background: #4CAF50;
		color: white;
	}

	.input-header {
		margin-bottom: 1.5rem;
	}

	.instruction {
		font-size: 1.3rem;
		margin-bottom: 1rem;
		color: #555;
	}

	.control-buttons {
		display: flex;
		gap: 0.5rem;
		justify-content: center;
		margin-top: 0.5rem;
	}

	.control-btn {
		padding: 0.5rem 1rem;
		border: 2px solid #2196F3;
		background: white;
		color: #2196F3;
		border-radius: 6px;
		font-size: 0.9rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
	}

	.control-btn:hover:not(:disabled) {
		background: #2196F3;
		color: white;
		transform: translateY(-2px);
		box-shadow: 0 2px 8px rgba(33, 150, 243, 0.3);
	}

	.control-btn:disabled {
		opacity: 0.3;
		cursor: not-allowed;
		border-color: #ccc;
		color: #ccc;
	}

	.submit-btn {
		padding: 0.5rem 1.4rem;
		border: 2px solid #4CAF50;
		background: #4CAF50;
		color: white;
		border-radius: 6px;
		font-size: 0.9rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
	}

	.submit-btn:hover:not(:disabled) {
		background: #43a047;
		border-color: #43a047;
		transform: translateY(-2px);
		box-shadow: 0 2px 8px rgba(76, 175, 80, 0.4);
	}

	.submit-btn:disabled {
		opacity: 0.35;
		cursor: not-allowed;
		background: #ccc;
		border-color: #ccc;
	}

	.grid-container {
		display: grid;
		grid-template-columns: repeat(var(--grid-size), 1fr);
		gap: 12px;
		max-width: 500px;
		margin: 0 auto;
		padding: 2rem;
	}

	.block {
		aspect-ratio: 1;
		background: linear-gradient(145deg, #f0f0f0, #e0e0e0);
		border-radius: 12px;
		border: 3px solid #bdbdbd;
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.5rem;
		font-weight: bold;
		color: white;
		box-shadow: 0 2px 4px rgba(0,0,0,0.1);
	}

	.block.highlighted {
		background: linear-gradient(145deg, #4CAF50, #45a049);
		border-color: #2e7d32;
		box-shadow: 0 0 25px rgba(76, 175, 80, 0.8), 0 4px 8px rgba(0,0,0,0.2);
		transform: scale(1.15);
	}

	.block.clickable {
		cursor: pointer;
	}

	.block.clickable:hover:not(.clicked) {
		background: linear-gradient(145deg, #e8f5e9, #c8e6c9);
		border-color: #81c784;
		transform: scale(1.05);
		box-shadow: 0 4px 8px rgba(0,0,0,0.15);
	}

	.block.clicked {
		background: linear-gradient(145deg, #2196F3, #1976D2);
		border-color: #1565C0;
		box-shadow: 0 4px 8px rgba(33, 150, 243, 0.4), inset 0 2px 4px rgba(0,0,0,0.2);
		transform: scale(0.95);
	}

	.block.clicked:hover {
		background: linear-gradient(145deg, #42A5F5, #2196F3);
		transform: scale(0.98);
	}

	.block.showing {
		cursor: default;
	}

	.click-number {
		font-size: 1.8rem;
		font-weight: bold;
		color: white;
	}

	.feedback-screen {
		text-align: center;
		padding: 4rem 0;
	}

	.feedback-icon {
		width: 120px;
		height: 120px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 4rem;
		margin: 0 auto 1rem;
		color: white;
	}


	.feedback-text {
		font-size: 2rem;
		font-weight: bold;
	}

	.complete-screen {
		text-align: center;
	}

	.results-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: 1rem;
		margin: 2rem 0;
	}

	.result-card {
		background: white;
		padding: 1.5rem;
		border-radius: 12px;
		box-shadow: 0 2px 8px rgba(0,0,0,0.1);
	}

	.result-value {
		font-size: 2.5rem;
		font-weight: bold;
		color: #4CAF50;
		margin-bottom: 0.5rem;
	}

	.result-label {
		color: #666;
		font-size: 0.9rem;
	}

	.span-breakdown {
		background: white;
		padding: 1.5rem;
		border-radius: 12px;
		box-shadow: 0 2px 8px rgba(0,0,0,0.1);
		margin: 2rem 0;
	}

	.span-breakdown h3 {
		margin: 0 0 1rem 0;
		color: #2c3e50;
	}

	.breakdown-row {
		display: flex;
		justify-content: space-between;
		padding: 0.5rem 0;
		border-bottom: 1px solid #eee;
	}

	.breakdown-row:last-child {
		border-bottom: none;
	}

	.difficulty-info {
		background: #e3f2fd;
		padding: 1.5rem;
		border-radius: 12px;
		margin: 2rem 0;
	}

	.adaptation-reason {
		color: #666;
		font-size: 0.9rem;
		margin-top: 0.5rem;
	}

	.new-badges {
		background: #fff3e0;
		padding: 1.5rem;
		border-radius: 12px;
		margin: 2rem 0;
	}

	.badge {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 0.5rem;
		background: white;
		border-radius: 8px;
		margin: 0.5rem 0;
	}

	.badge-icon {
		font-size: 2rem;
	}

	.actions {
		display: flex;
		gap: 1rem;
		justify-content: center;
		margin-top: 2rem;
	}

	.actions button {
		padding: 0.8rem 2rem;
		border: none;
		border-radius: 8px;
		font-size: 1rem;
		cursor: pointer;
		transition: all 0.3s;
	}

	.actions button:first-child {
		background: #2196F3;
		color: white;
	}

	.actions button:first-child:hover {
		background: #1976D2;
	}

	.actions button:last-child {
		background: #4CAF50;
		color: white;
	}

	.actions button:last-child:hover {
		background: #45a049;
	}

	.help-modal {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
	}

	.help-content {
		background: white;
		padding: 2rem;
		border-radius: 12px;
		max-width: 600px;
		max-height: 80vh;
		overflow-y: auto;
		position: relative;
	}

	.close-button {
		position: absolute;
		top: 1rem;
		right: 1rem;
		width: 40px;
		height: 40px;
		border: none;
		background: #f44336;
		color: white;
		font-size: 1.5rem;
		border-radius: 50%;
		cursor: pointer;
	}

	.help-content h2 {
		color: #2c3e50;
		margin-bottom: 1.5rem;
	}

	.strategy {
		margin-bottom: 1.5rem;
		padding: 1rem;
		background: #f8f9fa;
		border-radius: 8px;
		border-left: 4px solid #4CAF50;
	}

	.strategy h3 {
		margin: 0 0 0.5rem 0;
		color: #2c3e50;
	}

	.strategy p {
		margin: 0;
		color: #555;
		line-height: 1.6;
	}
</style>

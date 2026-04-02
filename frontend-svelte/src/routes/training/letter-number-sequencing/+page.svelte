<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
	import {
		formatNumber,
		formatPercent,
		locale,
		localeText,
		localizeStimulusSequence,
		localizeStimulusSymbol,
		translateText
	} from '$lib/i18n';
	import { buildPracticePayload, getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
	import { onMount } from 'svelte';

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
	let userNumbers = [];
	let userLetters = [];
	let currentItemIndex = 0;
	let startTime = 0;
	let showHelp = false;
	let sessionResults = null;
	let taskId = null;
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';
	let recordedTrials = [];

	const NUMBERS = ['1', '2', '3', '4', '5', '6', '7', '8', '9'];
	const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'R', 'S', 'T'];

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

	function symbol(value) {
		return localizeStimulusSymbol(value, $locale);
	}

	function sequence(values = []) {
		return localizeStimulusSequence(values, $locale).join(' - ');
	}

	function trialLabel(current, total) {
		return $locale === 'bn'
			? `ট্রায়াল ${n(current)} / ${n(total)}`
			: `Trial ${current} of ${total}`;
	}

	function compactTrialLabel(current, total) {
		return $locale === 'bn'
			? `ট্রায়াল ${n(current)}/${n(total)}`
			: `Trial ${current}/${total}`;
	}

	function levelLabel(value) {
		return $locale === 'bn' ? `লেভেল ${n(value)}` : `Level ${value}`;
	}

	function difficultyChangeLabel(before, after) {
		return $locale === 'bn'
			? `কঠিনতা: ${n(before)} → ${n(after)}`
			: `Difficulty: ${before} → ${after}`;
	}

	function speedTrendLabel(trend) {
		if (trend === 'improving') {
			return $locale === 'bn' ? '📈 উন্নত হচ্ছে' : '📈 Improving';
		}

		if (trend === 'slowing') {
			return $locale === 'bn' ? '📉 ধীর হচ্ছে' : '📉 Slowing';
		}

		return $locale === 'bn' ? '➡️ স্থিতিশীল' : '➡️ Stable';
	}

	function pointsLabel(value) {
		const absolute = Math.abs(Number(value) || 0).toFixed(1);
		const prefix = value >= 0 ? '+' : '-';
		return t(`${prefix}${absolute} pts`);
	}

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

			const planRes = await fetch(`http://localhost:8000/api/training/training-plan/${userId}`);
			const plan = await planRes.json();

			let userDifficulty = 5;
			if (plan && plan.current_difficulty) {
				const currentDiff =
					typeof plan.current_difficulty === 'string'
						? JSON.parse(plan.current_difficulty)
						: plan.current_difficulty;
				userDifficulty = currentDiff.working_memory || 5;
			}

			difficulty = userDifficulty;

			const response = await fetch(
				`http://localhost:8000/api/training/tasks/letter-number-sequencing/generate/${userId}?difficulty=${difficulty}&num_trials=8`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' }
				}
			);

			if (!response.ok) throw new Error('Failed to load session');

			const data = await response.json();
			const mappedTrials = data.trials.map((trial) => ({
				...trial,
				user_numbers: [],
				user_letters: [],
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
		state = STATE.LOADING;
		currentTrialIndex = 0;
		trials = nextMode === TASK_PLAY_MODE.PRACTICE
			? buildPracticePayload('letter-number-sequencing', { trials: recordedTrials }).trials
			: structuredClone(recordedTrials);
		setTimeout(() => startTrial(), 500);
	}

	async function startTrial() {
		currentTrial = trials[currentTrialIndex];
		userNumbers = [];
		userLetters = [];

		state = STATE.READY;
		await new Promise((resolve) => setTimeout(resolve, 1000));

		state = STATE.SHOWING;
		await playSequence();

		state = STATE.INPUT;
		startTime = Date.now();
	}

	async function playSequence() {
		const displayTime = currentTrial.display_ms ?? 1000;
		const intervalTime = currentTrial.interval_ms ?? 400;

		for (let index = 0; index < currentTrial.sequence.length; index += 1) {
			currentItemIndex = index;
			await new Promise((resolve) => setTimeout(resolve, displayTime));

			if (index < currentTrial.sequence.length - 1) {
				currentItemIndex = -1;
				await new Promise((resolve) => setTimeout(resolve, intervalTime));
			}
		}

		currentItemIndex = -1;
	}

	function addNumber(value) {
		if (state !== STATE.INPUT || userNumbers.includes(value)) return;
		userNumbers = [...userNumbers, value];
	}

	function addLetter(value) {
		if (state !== STATE.INPUT || userLetters.includes(value)) return;
		userLetters = [...userLetters, value];
	}

	function removeLastNumber() {
		if (userNumbers.length === 0) return;
		userNumbers = userNumbers.slice(0, -1);
	}

	function removeLastLetter() {
		if (userLetters.length === 0) return;
		userLetters = userLetters.slice(0, -1);
	}

	function clearNumbers() {
		userNumbers = [];
	}

	function clearLetters() {
		userLetters = [];
	}

	function submitResponse() {
		if (state !== STATE.INPUT) return;

		const reactionTime = Date.now() - startTime;
		trials[currentTrialIndex].user_numbers = userNumbers;
		trials[currentTrialIndex].user_letters = userLetters;
		trials[currentTrialIndex].reaction_time = reactionTime;

		state = STATE.FEEDBACK;

		setTimeout(() => {
			if (currentTrialIndex < trials.length - 1) {
				currentTrialIndex += 1;
				startTrial();
			} else {
				submitSession();
			}
		}, 1500);
	}

	function checkCorrect() {
		const numbersCorrect = JSON.stringify(userNumbers) === JSON.stringify(currentTrial.correct_numbers);
		const lettersCorrect = JSON.stringify(userLetters) === JSON.stringify(currentTrial.correct_letters);
		return numbersCorrect && lettersCorrect;
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
				`http://localhost:8000/api/training/tasks/letter-number-sequencing/submit/${userId}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						difficulty,
						trials,
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

	function toggleHelp() {
		showHelp = !showHelp;
	}
</script>

<div class="lns-container" data-localize-skip>
	{#if state === STATE.LOADING}
		<div class="loading">
			<div class="spinner"></div>
			<p>{t('Loading Letter-Number Sequencing Task...')}</p>
		</div>
	{:else if state === STATE.INSTRUCTIONS}
		<div class="instructions">
			<div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap;">
				<h1>🔢🔤 {t('Letter-Number Sequencing')}</h1>
				<DifficultyBadge {difficulty} domain="Working Memory" />
			</div>

			<div class="instruction-card">
				<h2>{t('How It Works')}</h2>
				<p>{t("You'll see a mixed sequence of numbers and letters. Your task is to reorder them:")}</p>
				
				<div class="rules">
					<div class="rule-card">
						<div class="rule-number">1️⃣</div>
						<h3>{t('Numbers First')}</h3>
						<p>
							{t('Put all numbers in')} <strong>{t('ascending order')}</strong><br />
							({symbol('1')}, {symbol('2')}, {symbol('3')}...)
						</p>
					</div>
					<div class="rule-card">
						<div class="rule-number">2️⃣</div>
						<h3>{t('Then Letters')}</h3>
						<p>
							{t('Put all letters in')} <strong>{t('alphabetical order')}</strong><br />
							({symbol('A')}, {symbol('B')}, {symbol('C')}...)
						</p>
					</div>
				</div>

				<div class="example">
					<h3>📝 {t('Example')}</h3>
					<div class="example-flow">
						<div class="example-box">
							<div class="example-label">{t('You See:')}</div>
							<div class="example-sequence">{sequence(['B', '3', 'A', '1'])}</div>
						</div>
						<div class="arrow">→</div>
						<div class="example-box">
							<div class="example-label">{t('You Answer:')}</div>
							<div class="example-answer">
								<span class="answer-numbers">{sequence(['1', '3'])}</span>
								<span class="answer-separator">{t('then')}</span>
								<span class="answer-letters">{sequence(['A', 'B'])}</span>
							</div>
						</div>
					</div>
				</div>
				
				<div class="tips">
					<h3>💡 {t('Memory Strategies')}</h3>
					<ul>
						<li><strong>{t('Categorize first:')}</strong> {t('Mentally separate numbers from letters')}</li>
						<li><strong>{t('Sort mentally:')}</strong> {t('Order each group in your mind before clicking')}</li>
						<li><strong>{t('Use rehearsal:')}</strong> {t('Repeat the correct order silently')}</li>
					</ul>
				</div>
			</div>
			
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
			<p>{t('Watch the sequence carefully...')}</p>
		</div>
	{:else if state === STATE.SHOWING || state === STATE.INPUT}
		<div class="trial-screen">
			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} />
			{/if}
			<div class="header">
				<div class="trial-info">
					<span class="trial-number">{compactTrialLabel(currentTrialIndex + 1, trials.length)}</span>
					<span class="difficulty-badge">{levelLabel(difficulty)}</span>
				</div>
				<button class="help-button" on:click={toggleHelp}>?</button>
			</div>

			{#if state === STATE.SHOWING}
				<p class="instruction">{t('Memorize the sequence...')}</p>
				<div class="sequence-display">
					{#each currentTrial.sequence as item, index}
						<div
							class="sequence-item"
							class:active={currentItemIndex === index}
							class:number={!Number.isNaN(Number(item))}
							class:letter={Number.isNaN(Number(item))}
						>
							{symbol(item)}
						</div>
					{/each}
				</div>
			{:else}
				<div class="input-header">
					<p class="instruction">
						<strong>{t('Reorder:')}</strong>
						{t('Numbers ascending (1, 2, 3...) then Letters alphabetical (A, B, C...)')}
					</p>
				</div>

				<div class="input-section">
					<div class="input-group">
						<h3>{t('Numbers (Low → High)')}</h3>
						<div class="selected-items">
							{#if userNumbers.length === 0}
								<span class="placeholder">{t('Select numbers...')}</span>
							{:else}
								{#each userNumbers as number}
									<span class="selected-item number">{symbol(number)}</span>
								{/each}
							{/if}
						</div>
						<div class="button-grid numbers">
							{#each NUMBERS as number}
								<button
									class="item-button number"
									class:selected={userNumbers.includes(number)}
									disabled={userNumbers.includes(number)}
									on:click={() => addNumber(number)}
								>
									{symbol(number)}
								</button>
							{/each}
						</div>
						<div class="controls">
							<button class="control-btn" on:click={removeLastNumber} disabled={userNumbers.length === 0}>
								↶ {t('Undo')}
							</button>
							<button class="control-btn" on:click={clearNumbers} disabled={userNumbers.length === 0}>
								✕ {t('Clear')}
							</button>
						</div>
					</div>

					<div class="input-group">
						<h3>{t('Letters (A → Z)')}</h3>
						<div class="selected-items">
							{#if userLetters.length === 0}
								<span class="placeholder">{t('Select letters...')}</span>
							{:else}
								{#each userLetters as letter}
									<span class="selected-item letter">{symbol(letter)}</span>
								{/each}
							{/if}
						</div>
						<div class="button-grid letters">
							{#each LETTERS as letter}
								<button
									class="item-button letter"
									class:selected={userLetters.includes(letter)}
									disabled={userLetters.includes(letter)}
									on:click={() => addLetter(letter)}
								>
									{symbol(letter)}
								</button>
							{/each}
						</div>
						<div class="controls">
							<button class="control-btn" on:click={removeLastLetter} disabled={userLetters.length === 0}>
								↶ {t('Undo')}
							</button>
							<button class="control-btn" on:click={clearLetters} disabled={userLetters.length === 0}>
								✕ {t('Clear')}
							</button>
						</div>
					</div>
				</div>

				<div class="submit-section">
					<button class="submit-button" on:click={submitResponse}>
						{t('Submit Answer')}
					</button>
				</div>
			{/if}
		</div>
	{:else if state === STATE.FEEDBACK}
		<div class="feedback-screen">
			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} />
			{/if}
			<div class="feedback-icon {checkCorrect() ? 'correct' : 'incorrect'}">
				{checkCorrect() ? '✓' : '✗'}
			</div>
			<p class="feedback-text">
				{checkCorrect() ? t('Correct!') : t('Incorrect')}
			</p>
			{#if !checkCorrect()}
				<div class="correct-answer">
					<p>{t('Correct answer:')}</p>
					<div class="answer-display">
						<span class="numbers">{sequence(currentTrial.correct_numbers)}</span>
						<span class="separator">{t('then')}</span>
						<span class="letters">{sequence(currentTrial.correct_letters)}</span>
					</div>
				</div>
			{/if}
		</div>
	{:else if state === STATE.COMPLETE}
		<div class="complete-screen">
			<h1>{t('Session Complete!')} 🎉</h1>

			<div class="results-grid">
				<div class="result-card highlight">
					<div class="result-value">{n(sessionResults.metrics.score)}</div>
					<div class="result-label">{t('Session Score')}</div>
				</div>
				<div class="result-card">
					<div class="result-value">{pct(sessionResults.metrics.binary_accuracy)}</div>
					<div class="result-label">{t('Fully Correct')}</div>
				</div>
				<div class="result-card">
					<div class="result-value">{n(sessionResults.metrics.longest_sequence)}</div>
					<div class="result-label">{t('Longest Sequence')}</div>
				</div>
				<div class="result-card">
					<div class="result-value">{pct(sessionResults.metrics.consistency)}</div>
					<div class="result-label">{t('Consistency')}</div>
				</div>
			</div>

			<div class="breakdown">
				<h3>{t('Score Breakdown')}</h3>
				<div class="breakdown-row">
					<span>🧠 {t('Item Recall (what you remembered)')}</span>
					<span>{pct(sessionResults.metrics.avg_set_accuracy)}</span>
				</div>
				<div class="breakdown-row">
					<span>🔢 {t('Ordering (correct sequence)')}</span>
					<span>{pct(sessionResults.metrics.avg_order_accuracy)}</span>
				</div>
				<div class="breakdown-row">
					<span>⚡ {t('Speed Bonus (avg)')}</span>
					<span>{pointsLabel(sessionResults.metrics.avg_speed_bonus)}</span>
				</div>
				<div class="breakdown-row">
					<span>⚠️ {t('Wrong Selections (penalty)')}</span>
					<span>{pointsLabel(-sessionResults.metrics.avg_penalty)}</span>
				</div>
			</div>

			<div class="breakdown">
				<h3>{t('Numbers vs Letters')}</h3>
				<div class="breakdown-row">
					<span>🔢 {t('Numbers — recalled')}</span>
					<span>{pct(sessionResults.metrics.numbers_set_accuracy)}</span>
				</div>
				<div class="breakdown-row">
					<span>🔢 {t('Numbers — ordered correctly')}</span>
					<span>{pct(sessionResults.metrics.numbers_order_accuracy)}</span>
				</div>
				<div class="breakdown-row">
					<span>🔤 {t('Letters — recalled')}</span>
					<span>{pct(sessionResults.metrics.letters_set_accuracy)}</span>
				</div>
				<div class="breakdown-row">
					<span>🔤 {t('Letters — ordered correctly')}</span>
					<span>{pct(sessionResults.metrics.letters_order_accuracy)}</span>
				</div>
				<div class="breakdown-row">
					<span>⏱️ {t('Response speed trend')}</span>
					<span class="trend-{sessionResults.metrics.speed_trend}">
						{speedTrendLabel(sessionResults.metrics.speed_trend)}
					</span>
				</div>
			</div>

			<div class="difficulty-info">
				<p>{difficultyChangeLabel(sessionResults.difficulty_before, sessionResults.difficulty_after)}</p>
				<p class="adaptation-reason">{t(sessionResults.adaptation_reason)}</p>
			</div>

			{#if sessionResults.new_badges && sessionResults.new_badges.length > 0}
				<div class="new-badges">
					<h3>🏆 {t('New Badges Earned!')}</h3>
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
	<div class="help-modal" on:click={toggleHelp} role="dialog" tabindex="-1" on:keydown={(event) => event.key === 'Escape' && toggleHelp()}>
		<div class="help-content" on:click|stopPropagation role="document" tabindex="-1" on:keydown={(event) => event.key === 'Escape' && toggleHelp()}>
			<button class="close-button" on:click={toggleHelp}>&times;</button>
			<h2>{t('Memory Strategies')}</h2>
			
			<div class="strategy">
				<h3>📊 {t('Categorize First')}</h3>
				<p>{t('Quickly identify which items are numbers and which are letters. Group them mentally before ordering.')}</p>
			</div>
			
			<div class="strategy">
				<h3>🔢 {t('Sort Numbers')}</h3>
				<p>{t('Arrange numbers from smallest to largest (1, 2, 3, 4...). This is your first group.')}</p>
			</div>
			
			<div class="strategy">
				<h3>🔤 {t('Sort Letters')}</h3>
				<p>{t('Arrange letters alphabetically (A, B, C, D...). This is your second group.')}</p>
			</div>
			
			<div class="strategy">
				<h3>🔄 {t('Mental Rehearsal')}</h3>
				<p>{t('Silently repeat the correct order 2-3 times before clicking to strengthen memory.')}</p>
			</div>
			
			<div class="strategy">
				<h3>✨ {t('Chunking')}</h3>
				<p>{t('For longer sequences, break them into smaller chunks (e.g., "1-3" and "A-B-D").')}</p>
			</div>
		</div>
	</div>
{/if}

<style>
	.lns-container {
		max-width: 1000px;
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
		border-top: 4px solid #4caf50;
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin: 0 auto 1rem;
	}

	@keyframes spin {
		0% {
			transform: rotate(0deg);
		}
		100% {
			transform: rotate(360deg);
		}
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
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
		text-align: left;
	}

	.rules {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
		margin: 1.5rem 0;
	}

	.rule-card {
		background: #f8f9fa;
		padding: 1.5rem;
		border-radius: 8px;
		border-left: 4px solid #4caf50;
		text-align: center;
	}

	.rule-number {
		font-size: 2rem;
		margin-bottom: 0.5rem;
	}

	.rule-card h3 {
		margin: 0 0 0.5rem 0;
		color: #2c3e50;
	}

	.example {
		background: #e3f2fd;
		padding: 1.5rem;
		border-radius: 8px;
		margin: 1.5rem 0;
	}

	.example h3 {
		margin: 0 0 1rem 0;
		color: #1976d2;
	}

	.example-flow {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		flex-wrap: wrap;
	}

	.example-box {
		background: white;
		padding: 1rem;
		border-radius: 8px;
		min-width: 200px;
	}

	.example-label {
		font-size: 0.85rem;
		color: #666;
		margin-bottom: 0.5rem;
	}

	.example-sequence {
		font-size: 1.5rem;
		font-weight: bold;
		color: #2c3e50;
	}

	.example-answer {
		display: flex;
		gap: 0.5rem;
		align-items: center;
		font-size: 1.2rem;
		font-weight: bold;
		flex-wrap: wrap;
	}

	.answer-numbers {
		color: #2196f3;
	}

	.answer-separator {
		color: #999;
		font-size: 0.9rem;
		font-weight: normal;
	}

	.answer-letters {
		color: #4caf50;
	}

	.arrow {
		font-size: 2rem;
		color: #4caf50;
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
		background: #4caf50;
		color: white;
		border: none;
		padding: 1rem 3rem;
		font-size: 1.2rem;
		border-radius: 8px;
		cursor: pointer;
		margin-top: 2rem;
		transition: background 0.3s;
	}

	.start-button:hover:not(:disabled) {
		background: #45a049;
	}

	.start-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.ready-screen {
		text-align: center;
		padding: 4rem 0;
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

	.difficulty-badge {
		background: #e3f2fd;
		padding: 0.5rem 1rem;
		border-radius: 20px;
		font-weight: 500;
		color: #1976d2;
	}

	.help-button {
		width: 40px;
		height: 40px;
		border-radius: 50%;
		border: 2px solid #4caf50;
		background: white;
		color: #4caf50;
		font-size: 1.5rem;
		font-weight: bold;
		cursor: pointer;
		transition: all 0.3s;
	}

	.help-button:hover {
		background: #4caf50;
		color: white;
	}

	.instruction {
		font-size: 1.2rem;
		margin-bottom: 1.5rem;
		color: #555;
	}

	.sequence-display {
		display: flex;
		gap: 1rem;
		justify-content: center;
		align-items: center;
		flex-wrap: wrap;
		padding: 2rem;
		min-height: 150px;
	}

	.sequence-item {
		width: 80px;
		height: 80px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 2.5rem;
		font-weight: bold;
		border-radius: 12px;
		border: 3px solid #ddd;
		background: #f5f5f5;
		transition: all 0.3s;
		opacity: 0.3;
	}

	.sequence-item.active {
		opacity: 1;
		transform: scale(1.2);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
	}

	.sequence-item.active.number {
		background: linear-gradient(145deg, #2196f3, #1976d2);
		border-color: #1565c0;
		color: white;
	}

	.sequence-item.active.letter {
		background: linear-gradient(145deg, #4caf50, #45a049);
		border-color: #2e7d32;
		color: white;
	}

	.input-section {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 2rem;
		margin: 2rem 0;
	}

	.input-group h3 {
		color: #2c3e50;
		margin-bottom: 1rem;
	}

	.selected-items {
		background: #f8f9fa;
		padding: 1rem;
		border-radius: 8px;
		min-height: 60px;
		display: flex;
		gap: 0.5rem;
		align-items: center;
		flex-wrap: wrap;
		margin-bottom: 1rem;
	}

	.placeholder {
		color: #999;
		font-style: italic;
	}

	.selected-item {
		padding: 0.5rem 1rem;
		border-radius: 6px;
		font-weight: bold;
		font-size: 1.2rem;
	}

	.selected-item.number {
		background: #2196f3;
		color: white;
	}

	.selected-item.letter {
		background: #4caf50;
		color: white;
	}

	.button-grid {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		gap: 0.5rem;
		margin-bottom: 1rem;
	}

	.button-grid.letters {
		grid-template-columns: repeat(6, 1fr);
	}

	.item-button {
		aspect-ratio: 1;
		border: 2px solid #ddd;
		background: white;
		border-radius: 8px;
		font-size: 1.2rem;
		font-weight: bold;
		cursor: pointer;
		transition: all 0.2s;
	}

	.item-button.number {
		color: #2196f3;
		border-color: #2196f3;
	}

	.item-button.letter {
		color: #4caf50;
		border-color: #4caf50;
	}

	.item-button:hover:not(:disabled) {
		transform: translateY(-2px);
		box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
	}

	.item-button.number:hover:not(:disabled) {
		background: #e3f2fd;
	}

	.item-button.letter:hover:not(:disabled) {
		background: #e8f5e9;
	}

	.item-button:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}

	.item-button.selected {
		opacity: 0.4;
	}

	.controls {
		display: flex;
		gap: 0.5rem;
		justify-content: center;
	}

	.control-btn {
		padding: 0.5rem 1rem;
		border: 2px solid #ff9800;
		background: white;
		color: #ff9800;
		border-radius: 6px;
		font-size: 0.9rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
	}

	.control-btn:hover:not(:disabled) {
		background: #ff9800;
		color: white;
		transform: translateY(-2px);
	}

	.control-btn:disabled {
		opacity: 0.3;
		cursor: not-allowed;
		border-color: #ccc;
		color: #ccc;
	}

	.submit-section {
		margin-top: 2rem;
	}

	.submit-button {
		background: linear-gradient(135deg, #4caf50, #45a049);
		color: white;
		border: none;
		padding: 1rem 3rem;
		font-size: 1.2rem;
		font-weight: bold;
		border-radius: 8px;
		cursor: pointer;
		transition: all 0.3s;
		box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
	}

	.submit-button:hover:not(:disabled) {
		transform: translateY(-2px);
		box-shadow: 0 6px 16px rgba(76, 175, 80, 0.4);
	}

	.submit-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
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

	.feedback-icon.correct {
		background: #4caf50;
	}

	.feedback-icon.incorrect {
		background: #f44336;
	}

	.feedback-text {
		font-size: 2rem;
		font-weight: bold;
	}

	.correct-answer {
		margin-top: 2rem;
		background: #f8f9fa;
		padding: 1.5rem;
		border-radius: 12px;
		max-width: 500px;
		margin-left: auto;
		margin-right: auto;
	}

	.answer-display {
		display: flex;
		gap: 0.5rem;
		align-items: center;
		justify-content: center;
		font-size: 1.3rem;
		font-weight: bold;
		margin-top: 1rem;
		flex-wrap: wrap;
	}

	.answer-display .numbers {
		color: #2196f3;
	}

	.answer-display .separator {
		color: #999;
		font-size: 1rem;
		font-weight: normal;
	}

	.answer-display .letters {
		color: #4caf50;
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
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	}

	.result-card.highlight {
		background: linear-gradient(135deg, #4caf50, #45a049);
		color: white;
	}

	.result-card.highlight .result-value,
	.result-card.highlight .result-label {
		color: white;
	}

	.result-value {
		font-size: 2.5rem;
		font-weight: bold;
		color: #4caf50;
		margin-bottom: 0.5rem;
	}

	.result-label {
		color: #666;
		font-size: 0.9rem;
	}

	.breakdown {
		background: white;
		padding: 1.5rem;
		border-radius: 12px;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
		margin: 2rem 0;
	}

	.breakdown h3 {
		margin: 0 0 1rem 0;
		color: #2c3e50;
	}

	.breakdown-row {
		display: flex;
		justify-content: space-between;
		padding: 0.5rem 0;
		border-bottom: 1px solid #eee;
		gap: 1rem;
	}

	.breakdown-row:last-child {
		border-bottom: none;
	}

	.trend-improving {
		color: #4caf50;
		font-weight: 600;
	}

	.trend-slowing {
		color: #f44336;
		font-weight: 600;
	}

	.trend-stable {
		color: #ff9800;
		font-weight: 600;
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
		background: #2196f3;
		color: white;
	}

	.actions button:first-child:hover {
		background: #1976d2;
	}

	.actions button:last-child {
		background: #4caf50;
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
		border-left: 4px solid #4caf50;
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

	@media (max-width: 768px) {
		.rules,
		.input-section {
			grid-template-columns: 1fr;
		}

		.button-grid.letters {
			grid-template-columns: repeat(4, 1fr);
		}

		.button-grid.numbers {
			grid-template-columns: repeat(3, 1fr);
		}

		.actions {
			flex-direction: column;
		}
	}
</style>

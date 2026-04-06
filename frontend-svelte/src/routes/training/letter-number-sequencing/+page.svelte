<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import {
	  formatNumber,
	  formatPercent,
	  locale,
	  localizeStimulusSequence,
	  localizeStimulusSymbol,
	  translateText
	} from '$lib/i18n';
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
			trials = data.trials.map((trial) => ({
				...trial,
				user_numbers: [],
				user_letters: [],
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
		state = STATE.LOADING;
		currentTrialIndex = 0;
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
<div class="lns-inner">
	{#if state === STATE.LOADING}
		<div class="loading-wrapper">
			<LoadingSkeleton variant="card" count={3} />
		</div>
	{:else if state === STATE.INSTRUCTIONS}
		<div class="instructions-card">
			<div class="header">
				<div class="header-content">
					<h1>🔢🔤 {t('Letter-Number Sequencing')}</h1>
					<p class="subtitle">{t('Complex Working Memory Training')}</p>
					<div class="classic-badge">{t('WAIS-IV Subtest · MACFIMS Battery')}</div>
				</div>
				<div class="header-right">
					<DifficultyBadge {difficulty} domain="Working Memory" />
					<button class="help-btn" on:click={toggleHelp} aria-label={t('Help')}>?</button>
				</div>
			</div>

			<div class="task-concept">
				<h2>{t('💡 Your Task: Sort Mixed Sequences')}</h2>
				<p>{t("You'll see a mixed sequence of numbers and letters appear one at a time. Memorize them, then reorder — all numbers ascending first, then all letters alphabetically.")}</p>
			</div>

			<div class="rules-grid">
				<div class="rule-card">
					<div class="rule-icon">🔢</div>
					<h3>{t('Step 1 — Numbers First')}</h3>
					<p>{t('Recall all numbers in ascending order')}</p>
					<div class="rule-example">{symbol('1')}, {symbol('2')}, {symbol('3')}...</div>
				</div>
				<div class="rule-card">
					<div class="rule-icon">🔤</div>
					<h3>{t('Step 2 — Then Letters')}</h3>
					<p>{t('Recall all letters in alphabetical order')}</p>
					<div class="rule-example">{symbol('A')}, {symbol('B')}, {symbol('C')}...</div>
				</div>
			</div>

			<div class="example-panel">
				<h3>📝 {t('Example')}</h3>
				<div class="example-flow">
					<div class="example-box">
						<div class="example-label">{t('You See:')}</div>
						<div class="example-sequence">{sequence(['B', '3', 'A', '1'])}</div>
					</div>
					<div class="example-arrow">→</div>
					<div class="example-box">
						<div class="example-label">{t('You Answer:')}</div>
						<div class="example-answer">
							<span class="answer-numbers">{sequence(['1', '3'])}</span>
							<span class="answer-sep">{t('then')}</span>
							<span class="answer-letters">{sequence(['A', 'B'])}</span>
						</div>
					</div>
				</div>
			</div>

			<div class="info-grid">
				<div class="info-section">
					<h3>{t('💪 Memory Strategies')}</h3>
					<div class="tips-list">
						<div class="tip-item">✓ <strong>{t('Categorize first:')}</strong> {t('Mentally separate numbers from letters as they appear')}</div>
						<div class="tip-item">✓ <strong>{t('Sort mentally:')}</strong> {t('Order each group in your mind before clicking')}</div>
						<div class="tip-item">✓ <strong>{t('Use rehearsal:')}</strong> {t('Silently repeat the correct order 2–3 times')}</div>
						<div class="tip-item">✓ <strong>{t('Chunking:')}</strong> {t('For longer sequences, group into pairs (e.g. "1-3" then "A-B")')}</div>
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
								<span>{t('Mixed numbers & letters')}</span>
							</div>
						</div>
					</div>
				</div>
			</div>

			<div class="clinical-info">
				<h3>{t('📚 Clinical Significance')}</h3>
				<div class="clinical-grid">
					<div class="clinical-item">
						<strong>{t('📜 Standard:')}</strong> {t('WAIS-IV subtest — executive working memory component')}
					</div>
					<div class="clinical-item">
						<strong>{t('🎯 Measures:')}</strong> {t('Complex manipulation of verbal working memory contents')}
					</div>
					<div class="clinical-item">
						<strong>{t('🏥 MS Relevance:')}</strong> {t('Sensitive to MS cognitive dysfunction (Parmenter et al., 2007)')}
					</div>
					<div class="clinical-item">
						<strong>{t('🌍 Clinical Use:')}</strong> {t('Included in MS neuropsychological assessment batteries (MACFIMS)')}
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
			<div class="ready-card">
				<h2>{trialLabel(currentTrialIndex + 1, trials.length)}</h2>
				<p class="ready-text">{t('Watch the sequence carefully...')}</p>
			</div>
		</div>
	{:else if state === STATE.SHOWING || state === STATE.INPUT}
		<div class="trial-screen">
			<div class="trial-header">
				<div class="trial-info">
					<span class="trial-number">{compactTrialLabel(currentTrialIndex + 1, trials.length)}</span>
					<span class="span-badge">{levelLabel(difficulty)}</span>
				</div>
				<button class="help-btn" on:click={toggleHelp} aria-label={t('Help')}>?</button>
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
					<button class="submit-btn" on:click={submitResponse}>
						{t('Submit Answer')}
					</button>
					<button class="skip-btn" on:click={startTrial}>
						{t('Skip Trial')}
					</button>
				</div>
			{/if}
		</div>
	{:else if state === STATE.FEEDBACK}
		<div class="feedback-screen">
			<div class="feedback-icon {checkCorrect() ? 'correct' : 'incorrect'}">
				{checkCorrect() ? '✅' : '❌'}
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

			{#if sessionResults.new_badges && sessionResults.new_badges.length > 0}
				<BadgeNotification badges={sessionResults.new_badges} />
			{/if}

			<div class="metrics-grid">
				<div class="metric-card highlight">
					<div class="metric-value">{n(sessionResults.metrics.score)}</div>
					<div class="metric-label">{t('Session Score')}</div>
				</div>
				<div class="metric-card">
					<div class="metric-value">{pct(sessionResults.metrics.binary_accuracy)}</div>
					<div class="metric-label">{t('Fully Correct')}</div>
				</div>
				<div class="metric-card">
					<div class="metric-value">{n(sessionResults.metrics.longest_sequence)}</div>
					<div class="metric-label">{t('Longest Sequence')}</div>
				</div>
				<div class="metric-card">
					<div class="metric-value">{pct(sessionResults.metrics.consistency)}</div>
					<div class="metric-label">{t('Consistency')}</div>
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

			<div class="button-group">
				<button class="start-button" on:click={() => goto('/training')}>{t('Back to Training')}</button>
				<button class="btn-secondary" on:click={() => goto('/dashboard')}>{t('View Dashboard')}</button>
			</div>
		</div>
	{/if}
</div>
</div>

{#if showHelp}
	<div class="modal-overlay" on:click={toggleHelp} role="dialog" tabindex="-1" on:keydown={(event) => event.key === 'Escape' && toggleHelp()}>
		<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
		<div class="modal-content" on:click|stopPropagation role="document" tabindex="-1" on:keydown={(event) => event.key === 'Escape' && toggleHelp()}>
			<button class="close-btn" on:click={toggleHelp}>&times;</button>
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
	/* ────── Layout ────── */
	.lns-container {
		background: #EAF2FB;
		min-height: 100vh;
		padding: 2rem 1rem;
	}

	.lns-inner {
		max-width: 960px;
		margin: 0 auto;
	}

	/* ────── Loading ────── */
	.loading-wrapper {
		padding: 4rem 0;
	}

	/* ────── Instructions ────── */
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

	.header-right {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		flex-shrink: 0;
	}

	/* ────── Help button ────── */
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
	}

	.help-btn:hover {
		background: #667eea;
		color: white;
	}

	/* ────── Task concept panel ────── */
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

	/* ────── Rules grid ────── */
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

	/* ────── Example panel ────── */
	.example-panel {
		background: #f8fafc;
		border-radius: 12px;
		padding: 1.25rem 1.5rem;
		margin-bottom: 1.5rem;
	}

	.example-panel h3 {
		font-size: 0.95rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 1rem;
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
		padding: 1rem 1.5rem;
		border-radius: 10px;
		border: 1px solid #e2e8f0;
		min-width: 180px;
		text-align: center;
	}

	.example-label {
		font-size: 0.8rem;
		color: #64748b;
		margin-bottom: 0.4rem;
	}

	.example-sequence {
		font-size: 1.4rem;
		font-weight: 700;
		color: #1e293b;
	}

	.example-arrow {
		font-size: 1.5rem;
		color: #667eea;
		font-weight: 600;
	}

	.example-answer {
		display: flex;
		gap: 0.5rem;
		align-items: center;
		justify-content: center;
		font-size: 1.2rem;
		font-weight: 700;
		flex-wrap: wrap;
	}

	.answer-numbers {
		color: #2563eb;
	}

	.answer-sep {
		color: #94a3b8;
		font-size: 0.85rem;
		font-weight: normal;
	}

	.answer-letters {
		color: #7c3aed;
	}

	/* ────── Info grid (tips + structure) ────── */
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
		font-size: 0.85rem;
		color: #15803d;
		background: #f0fdf4;
		padding: 0.5rem 0.75rem;
		border-radius: 8px;
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
		background: linear-gradient(135deg, #667eea, #764ba2);
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

	/* ────── Clinical info panel ────── */
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

	/* ────── Buttons ────── */
	.button-group {
		display: flex;
		gap: 1rem;
		justify-content: center;
		flex-wrap: wrap;
		margin-top: 1.5rem;
	}

	.start-button {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		padding: 0.9rem 2.5rem;
		font-size: 1rem;
		font-weight: 600;
		border-radius: 10px;
		cursor: pointer;
		box-shadow: 0 4px 14px rgba(102, 126, 234, 0.35);
		transition: all 0.2s;
	}

	.start-button:hover:not(:disabled) {
		transform: translateY(-2px);
		box-shadow: 0 6px 20px rgba(102, 126, 234, 0.45);
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

	/* ────── Ready screen ────── */
	.ready-screen {
		text-align: center;
		padding: 4rem 0;
	}

	.ready-card {
		background: #FFFFFF;
		border-radius: 16px;
		padding: 3rem 2rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
		display: inline-block;
		min-width: 320px;
	}

	.ready-card h2 {
		font-size: 1.5rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 0.75rem;
	}

	.ready-text {
		background: linear-gradient(135deg, #667eea, #764ba2);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
		font-size: 1.15rem;
		font-weight: 600;
		margin: 0;
	}

	/* ────── Trial screen ────── */
	.trial-screen {
		background: white;
		border-radius: 16px;
		padding: 2rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
	}

	.trial-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
	}

	.trial-info {
		display: flex;
		gap: 0.75rem;
		align-items: center;
	}

	.trial-number {
		background: rgba(102, 126, 234, 0.1);
		color: #667eea;
		padding: 0.4rem 1rem;
		border-radius: 20px;
		font-weight: 600;
		font-size: 0.9rem;
	}

	.span-badge {
		background: rgba(118, 75, 162, 0.1);
		color: #764ba2;
		padding: 0.4rem 1rem;
		border-radius: 20px;
		font-weight: 600;
		font-size: 0.9rem;
	}

	/* ────── Sequence display ────── */
	.instruction {
		font-size: 1rem;
		margin-bottom: 1rem;
		color: #64748b;
	}

	.sequence-display {
		display: flex;
		gap: 0.75rem;
		justify-content: center;
		align-items: center;
		flex-wrap: wrap;
		padding: 1.5rem;
		min-height: 130px;
	}

	.sequence-item {
		width: 72px;
		height: 72px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 2rem;
		font-weight: 700;
		border-radius: 12px;
		border: 2px solid #e2e8f0;
		background: #f8fafc;
		transition: all 0.25s;
		opacity: 0.3;
	}

	.sequence-item.active {
		opacity: 1;
		transform: scale(1.15);
		box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
	}

	.sequence-item.active.number {
		background: linear-gradient(145deg, #3b82f6, #2563eb);
		border-color: #1d4ed8;
		color: white;
	}

	.sequence-item.active.letter {
		background: linear-gradient(145deg, #8b5cf6, #7c3aed);
		border-color: #6d28d9;
		color: white;
	}

	/* ────── Input section ────── */
	.input-header {
		margin-bottom: 1rem;
	}

	.input-section {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.5rem;
		margin: 1rem 0;
	}

	.input-group {
		background: #f8fafc;
		border-radius: 12px;
		padding: 1.25rem;
	}

	.input-group h3 {
		font-size: 0.9rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 0.75rem;
	}

	.selected-items {
		background: white;
		border: 1px solid #e2e8f0;
		border-radius: 8px;
		padding: 0.75rem;
		min-height: 52px;
		display: flex;
		gap: 0.4rem;
		align-items: center;
		flex-wrap: wrap;
		margin-bottom: 0.75rem;
	}

	.placeholder {
		color: #94a3b8;
		font-style: italic;
		font-size: 0.9rem;
	}

	.selected-item {
		padding: 0.35rem 0.7rem;
		border-radius: 6px;
		font-weight: 700;
		font-size: 1rem;
	}

	.selected-item.number {
		background: #dbeafe;
		color: #1e40af;
	}

	.selected-item.letter {
		background: #f3e8ff;
		color: #7e22ce;
	}

	/* ────── Button grid ────── */
	.button-grid {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		gap: 0.4rem;
		margin-bottom: 0.75rem;
	}

	.button-grid.letters {
		grid-template-columns: repeat(6, 1fr);
	}

	.item-button {
		aspect-ratio: 1;
		border: 2px solid #e2e8f0;
		background: white;
		border-radius: 8px;
		font-size: 1rem;
		font-weight: 700;
		cursor: pointer;
		transition: all 0.15s;
	}

	.item-button.number {
		color: #2563eb;
		border-color: #93c5fd;
	}

	.item-button.letter {
		color: #7c3aed;
		border-color: #c4b5fd;
	}

	.item-button:hover:not(:disabled) {
		transform: translateY(-2px);
		box-shadow: 0 4px 8px rgba(0, 0, 0, 0.12);
	}

	.item-button.number:hover:not(:disabled) {
		background: #dbeafe;
		border-color: #3b82f6;
	}

	.item-button.letter:hover:not(:disabled) {
		background: #f3e8ff;
		border-color: #8b5cf6;
	}

	.item-button:disabled,
	.item-button.selected {
		opacity: 0.3;
		cursor: not-allowed;
		transform: none;
	}

	/* ────── Controls ────── */
	.controls {
		display: flex;
		gap: 0.5rem;
		justify-content: center;
	}

	.control-btn {
		padding: 0.4rem 0.9rem;
		border: 2px solid #667eea;
		background: white;
		color: #667eea;
		border-radius: 6px;
		font-size: 0.85rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.15s;
	}

	.control-btn:hover:not(:disabled) {
		background: #667eea;
		color: white;
	}

	.control-btn:disabled {
		opacity: 0.3;
		cursor: not-allowed;
		border-color: #cbd5e1;
		color: #94a3b8;
	}

	/* ────── Submit ────── */
	.submit-section {
		margin-top: 1.5rem;
		text-align: center;
		display: flex;
		gap: 1rem;
		justify-content: center;
		flex-wrap: wrap;
	}

	.submit-btn {
		background: linear-gradient(135deg, #667eea, #764ba2);
		color: white;
		border: none;
		padding: 0.9rem 3rem;
		font-size: 1rem;
		font-weight: 700;
		border-radius: 10px;
		cursor: pointer;
		box-shadow: 0 4px 14px rgba(102, 126, 234, 0.35);
		transition: all 0.2s;
	}

	.submit-btn:hover:not(:disabled) {
		transform: translateY(-2px);
		box-shadow: 0 6px 20px rgba(102, 126, 234, 0.45);
	}

	.submit-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
		transform: none;
	}

	.skip-btn {
		background: rgba(255, 255, 255, 0.15);
		color: #64748b;
		border: 2px solid #e2e8f0;
		padding: 0.9rem 2rem;
		font-size: 0.9rem;
		font-weight: 600;
		border-radius: 10px;
		cursor: pointer;
		transition: all 0.2s;
	}

	.skip-btn:hover {
		background: #f1f5f9;
		border-color: #94a3b8;
		color: #475569;
	}

	/* ────── Feedback ────── */
	.feedback-screen {
		text-align: center;
		padding: 3rem 0;
	}

	.feedback-icon {
		width: 100px;
		height: 100px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 3rem;
		margin: 0 auto 1rem;
	}

	.feedback-icon.correct {
		background: #dcfce7;
	}

	.feedback-icon.incorrect {
		background: #fee2e2;
	}

	.feedback-text {
		font-size: 1.8rem;
		font-weight: 700;
		color: #1e293b;
	}

	.correct-answer {
		margin-top: 1.5rem;
		background: white;
		border: 1px solid #e2e8f0;
		padding: 1.25rem;
		border-radius: 12px;
		max-width: 480px;
		margin-left: auto;
		margin-right: auto;
	}

	.answer-display {
		display: flex;
		gap: 0.5rem;
		align-items: center;
		justify-content: center;
		font-size: 1.2rem;
		font-weight: 700;
		margin-top: 0.75rem;
		flex-wrap: wrap;
	}

	.answer-display .numbers {
		color: #2563eb;
	}

	.answer-display .separator {
		color: #94a3b8;
		font-size: 0.9rem;
		font-weight: normal;
	}

	.answer-display .letters {
		color: #7c3aed;
	}

	/* ────── Complete screen ────── */
	.complete-screen {
		background: #FFFFFF;
		border-radius: 16px;
		padding: 2.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
		text-align: center;
	}

	.complete-screen h1 {
		font-size: 2rem;
		font-weight: 700;
		color: #1e293b;
		margin-bottom: 1.5rem;
	}

	.metrics-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
		gap: 1rem;
		margin: 1.5rem 0;
	}

	.metric-card {
		background: #f8fafc;
		border: 1px solid #e2e8f0;
		padding: 1.25rem;
		border-radius: 12px;
	}

	.metric-card.highlight {
		background: linear-gradient(135deg, #667eea, #764ba2);
		border-color: transparent;
	}

	.metric-card.highlight .metric-value,
	.metric-card.highlight .metric-label {
		color: white;
	}

	.metric-value {
		font-size: 2rem;
		font-weight: 700;
		color: #667eea;
		margin-bottom: 0.35rem;
	}

	.metric-label {
		color: #64748b;
		font-size: 0.85rem;
	}

	.breakdown {
		background: #f8fafc;
		border: 1px solid #e2e8f0;
		padding: 1.25rem 1.5rem;
		border-radius: 12px;
		margin: 1rem 0;
		text-align: left;
	}

	.breakdown h3 {
		font-size: 0.95rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 0.75rem;
	}

	.breakdown-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.45rem 0;
		border-bottom: 1px solid #e2e8f0;
		gap: 1rem;
		font-size: 0.9rem;
		color: #374151;
	}

	.breakdown-row:last-child {
		border-bottom: none;
	}

	.trend-improving { color: #16a34a; font-weight: 600; }
	.trend-slowing   { color: #dc2626; font-weight: 600; }
	.trend-stable    { color: #d97706; font-weight: 600; }

	.difficulty-info {
		background: linear-gradient(135deg, rgba(102, 126, 234, 0.08), rgba(118, 75, 162, 0.08));
		border: 1px solid rgba(102, 126, 234, 0.15);
		padding: 1.25rem 1.5rem;
		border-radius: 12px;
		margin: 1rem 0;
		font-size: 0.95rem;
		color: #374151;
	}

	.adaptation-reason {
		color: #64748b;
		font-size: 0.85rem;
		margin-top: 0.35rem;
	}

	/* ────── Help modal ────── */
	.modal-overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
	}

	.modal-content {
		background: white;
		padding: 2rem;
		border-radius: 16px;
		max-width: 560px;
		width: 90%;
		max-height: 80vh;
		overflow-y: auto;
		position: relative;
	}

	.modal-content h2 {
		font-size: 1.2rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 1.25rem;
	}

	.close-btn {
		position: absolute;
		top: 1rem;
		right: 1rem;
		width: 36px;
		height: 36px;
		border: none;
		background: #f1f5f9;
		color: #64748b;
		font-size: 1.3rem;
		border-radius: 50%;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s;
	}

	.close-btn:hover {
		background: #e2e8f0;
		color: #1e293b;
	}

	.strategy {
		margin-bottom: 1rem;
		padding: 1rem;
		background: #f8fafc;
		border-radius: 10px;
		border-left: 4px solid #667eea;
	}

	.strategy h3 {
		font-size: 0.9rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 0.35rem;
	}

	.strategy p {
		margin: 0;
		color: #64748b;
		font-size: 0.85rem;
		line-height: 1.5;
	}

	/* ────── Responsive ────── */
	@media (max-width: 768px) {
		.rules-grid,
		.input-section,
		.info-grid,
		.clinical-grid {
			grid-template-columns: 1fr;
		}

		.button-grid.letters {
			grid-template-columns: repeat(4, 1fr);
		}

		.button-grid {
			grid-template-columns: repeat(3, 1fr);
		}

		.button-group {
			flex-direction: column;
			align-items: stretch;
		}
	}
</style>

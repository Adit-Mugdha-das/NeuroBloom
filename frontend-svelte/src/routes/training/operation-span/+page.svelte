<script>
	import { goto } from '$app/navigation';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
import TaskReturnButton from '$lib/components/TaskReturnButton.svelte';
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
import { TASK_RETURN_CONTEXT } from '$lib/task-navigation';
	import { onDestroy, onMount } from 'svelte';

	// Task states
	const STATE = {
		LOADING: 'loading',
		INSTRUCTIONS: 'instructions',
		READY: 'ready',
		MATH_PROBLEM: 'math_problem',
		LETTER_DISPLAY: 'letter_display',
		RECALL: 'recall',
		FEEDBACK: 'feedback',
		COMPLETE: 'complete'
	};

	let state = STATE.LOADING;
	let difficulty = 5;
	let trials = [];
	let currentTrialIndex = 0;
	let currentTrial = null;
	let currentItemIndex = 0;
	let currentItem = null;
	
	// Math problem state
	let mathResponse = null;
	let mathStartTime = 0;
	let mathTimeout = null;
	let timeRemaining = 0;
	let timerInterval = null;
	
	// Letter recall state
	let userLetters = [];
	let mathResponses = [];
	let trialStartTime = 0;
	let lastTrialCorrect = false;
	let lastTrial = null;

	let showHelp = false;
	let sessionResults = null;
	let taskId = null;
	/** @type {"practice" | "recorded"} */
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';
	let recordedTrials = [];
	let sessionRunId = 0;
	let readyTimeout = null;
	let letterRevealTimeout = null;
	let feedbackTimeout = null;

	// Available letters
	const LETTERS = ['B', 'C', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'R', 'S', 'T'];

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

	function letterSequence(values = []) {
		return localizeStimulusSequence(values, $locale).join(' - ');
	}

	function setLabel(current, total) {
		return $locale === 'bn' ? `সেট ${n(current)} / ${n(total)}` : `Set ${current}/${total}`;
	}

	function problemLabel(current, total) {
		return $locale === 'bn' ? `সমস্যা ${n(current)} / ${n(total)}` : `Problem ${current}/${total}`;
	}

	function pairCountLabel(count) {
		return $locale === 'bn' ? `${n(count)}টি গণিত-অক্ষর জোড়া` : `${count} math-letter pairs`;
	}

	function letterProgressLabel(current, total) {
		return $locale === 'bn' ? `অক্ষর ${n(current)} / ${n(total)}` : `Letter ${current} of ${total}`;
	}

	function difficultyChangeLabel(before, after) {
		return $locale === 'bn'
			? `কঠিনতা: ${n(before)} → ${n(after)}`
			: `Difficulty: ${before} → ${after}`;
	}

	onMount(async () => {
		await loadSession();
	});

	onDestroy(() => {
		sessionRunId += 1;
		if (mathTimeout) clearTimeout(mathTimeout);
		if (timerInterval) clearInterval(timerInterval);
		if (readyTimeout) clearTimeout(readyTimeout);
		if (letterRevealTimeout) clearTimeout(letterRevealTimeout);
		if (feedbackTimeout) clearTimeout(feedbackTimeout);
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
			console.log('📊 Operation Span - Loaded difficulty:', difficulty);

			const response = await fetch(
				`http://localhost:8000/api/training/tasks/operation-span/generate/${userId}?difficulty=${difficulty}&num_trials=6`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' }
				}
			);

			if (!response.ok) throw new Error('Failed to load session');

			const data = await response.json();
			const mappedTrials = data.trials.map(t => ({
				...t,
				user_letters: [],
				math_responses: [],
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

	/** @param {"practice" | "recorded"} [nextMode] */
	function startSession(nextMode = TASK_PLAY_MODE.RECORDED) {
		sessionRunId += 1;
		const runId = sessionRunId;
		if (mathTimeout) clearTimeout(mathTimeout);
		if (timerInterval) clearInterval(timerInterval);
		if (readyTimeout) clearTimeout(readyTimeout);
		if (letterRevealTimeout) clearTimeout(letterRevealTimeout);
		if (feedbackTimeout) clearTimeout(feedbackTimeout);

		playMode = nextMode;
		practiceStatusMessage = '';
		state = STATE.LOADING;
		currentTrialIndex = 0;
		trials = nextMode === TASK_PLAY_MODE.PRACTICE
			? buildPracticePayload('operation-span', { trials: recordedTrials }).trials
			: structuredClone(recordedTrials);
		readyTimeout = setTimeout(() => {
			readyTimeout = null;
			if (runId === sessionRunId) startTrial(runId);
		}, 500);
	}

	function leavePractice(completed = false) {
		sessionRunId += 1;
		if (mathTimeout) {
			clearTimeout(mathTimeout);
			mathTimeout = null;
		}
		if (timerInterval) {
			clearInterval(timerInterval);
			timerInterval = null;
		}
		if (readyTimeout) {
			clearTimeout(readyTimeout);
			readyTimeout = null;
		}
		if (letterRevealTimeout) {
			clearTimeout(letterRevealTimeout);
			letterRevealTimeout = null;
		}
		if (feedbackTimeout) {
			clearTimeout(feedbackTimeout);
			feedbackTimeout = null;
		}

		trials = structuredClone(recordedTrials);
		playMode = TASK_PLAY_MODE.RECORDED;
		practiceStatusMessage = completed ? getPracticeCopy($locale).complete : '';
		currentTrialIndex = 0;
		currentTrial = null;
		currentItemIndex = 0;
		currentItem = null;
		mathResponse = null;
		mathStartTime = 0;
		timeRemaining = 0;
		userLetters = [];
		mathResponses = [];
		trialStartTime = 0;
		lastTrialCorrect = false;
		lastTrial = null;
		sessionResults = null;
		state = STATE.INSTRUCTIONS;
	}

	async function startTrial(runId = sessionRunId) {
		currentTrial = trials[currentTrialIndex];
		currentItemIndex = 0;
		userLetters = [];
		mathResponses = [];
		trialStartTime = Date.now();
		
		state = STATE.READY;
		await new Promise(resolve => setTimeout(resolve, 1500));
		if (runId !== sessionRunId) return;
		
		showNextItem();
	}

	function showNextItem() {
		if (currentItemIndex >= currentTrial.items.length) {
			// All items shown, move to recall
			state = STATE.RECALL;
			return;
		}
		
		currentItem = currentTrial.items[currentItemIndex];
		
		// Show math problem
		state = STATE.MATH_PROBLEM;
		mathResponse = null;
		mathStartTime = Date.now();
		
		// Start countdown timer
		timeRemaining = currentTrial.time_limit;
		startTimer();
		
		// Auto-timeout if no response
		mathTimeout = setTimeout(() => {
			if (state === STATE.MATH_PROBLEM) {
				handleMathTimeout();
			}
		}, currentTrial.time_limit);
	}

	function startTimer() {
		if (timerInterval) clearInterval(timerInterval);
		
		timerInterval = setInterval(() => {
			timeRemaining -= 100;
			if (timeRemaining <= 0) {
				clearInterval(timerInterval);
			}
		}, 100);
	}

	function handleMathResponse(response) {
		if (state !== STATE.MATH_PROBLEM) return;
		
		mathResponse = response;
		mathResponses.push(response);
		
		// Clear timeout
		if (mathTimeout) clearTimeout(mathTimeout);
		if (timerInterval) clearInterval(timerInterval);
		mathTimeout = null;
		timerInterval = null;
		
		// Show letter
		const runId = sessionRunId;
		letterRevealTimeout = setTimeout(() => {
			letterRevealTimeout = null;
			if (runId === sessionRunId) showLetter(runId);
		}, 300);
	}

	function handleMathTimeout() {
		// User took too long - count as incorrect
		if (timerInterval) {
			clearInterval(timerInterval);
			timerInterval = null;
		}
		mathTimeout = null;
		mathResponses.push(false);
		showLetter(sessionRunId);
	}

	async function showLetter(runId = sessionRunId) {
		state = STATE.LETTER_DISPLAY;
		
		// Show for 1 second
		await new Promise(resolve => setTimeout(resolve, 1000));
		if (runId !== sessionRunId) return;
		
		// Move to next item
		currentItemIndex++;
		showNextItem();
	}

	function addLetter(letter) {
		if (state !== STATE.RECALL) return;
		if (userLetters.includes(letter)) return;
		userLetters = [...userLetters, letter];
	}

	function removeLastLetter() {
		if (userLetters.length > 0) {
			userLetters = userLetters.slice(0, -1);
		}
	}

	function clearLetters() {
		userLetters = [];
	}

	function submitRecall() {
		if (state !== STATE.RECALL) return;
		
		const reactionTime = Date.now() - trialStartTime;
		trials[currentTrialIndex].user_letters = userLetters;
		trials[currentTrialIndex].math_responses = mathResponses;
		trials[currentTrialIndex].reaction_time = reactionTime;

		lastTrialCorrect = checkCorrect();
		lastTrial = currentTrial;

		state = STATE.FEEDBACK;

		const runId = sessionRunId;
		feedbackTimeout = setTimeout(() => {
			feedbackTimeout = null;
			if (runId !== sessionRunId) return;
			if (currentTrialIndex < trials.length - 1) {
				currentTrialIndex++;
				startTrial(runId);
			} else {
				submitSession();
			}
		}, 2000);
	}

	function checkCorrect() {
		const lettersCorrect = JSON.stringify(userLetters) === JSON.stringify(currentTrial.correct_letters);
		const mathCorrect = mathResponses.every(
			(response, i) => response === currentTrial.items[i].is_correct
		);
		return lettersCorrect && mathCorrect;
	}

	async function submitSession() {
		if (playMode === TASK_PLAY_MODE.PRACTICE) {
			leavePractice(true);
			return;
		}

		state = STATE.LOADING;
		
		try {
			const userData = JSON.parse(localStorage.getItem('user') || '{}');
			const userId = userData.id;

			const response = await fetch(
				`http://localhost:8000/api/training/tasks/operation-span/submit/${userId}`,
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

	function toggleHelp() {
		showHelp = !showHelp;
	}
</script>

<div class="ospan-container" data-localize-skip>
<div class="ospan-inner">
	{#if state === STATE.LOADING}
		<div class="loading-wrapper">
			<LoadingSkeleton variant="card" count={3} />
		</div>
	{:else if state === STATE.INSTRUCTIONS}
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />
		<div class="instructions-card">
			<div class="header">
				<div class="header-content">
					<h1>{t('Operation Span (OSPAN)')}</h1>
					<p class="subtitle">{t('Dual-Task Executive Working Memory Training')}</p>
					<div class="classic-badge">{t('OSPAN · Turner & Engle (1989) · MACFIMS Battery')}</div>
				</div>
				<div class="header-right">
					<DifficultyBadge {difficulty} domain="Working Memory" />
					<button class="help-btn" on:click={toggleHelp} aria-label={t('Help')}>?</button>
				</div>
			</div>

			<div class="task-concept">
				<h2>{t('Your Task: Juggle Math and Memory')}</h2>
				<p>{$locale === 'bn' ? 'এই টাস্কে আপনাকে একই সঙ্গে গণিত যাচাই করতে হবে এবং অক্ষর মনে রাখতে হবে।' : 'Verify math equations AND memorize letters shown after each one. At the end of each set, recall all letters in order.'}</p>
			</div>

			<div class="rules-grid">
				<div class="rule-card">
					<div class="rule-icon">=?</div>
					<h3>{t('Step 1 — Verify Equation')}</h3>
					<p>{t('Is each equation correct or incorrect?')}</p>
					<div class="rule-example">{t('2 + 3 = 5')} ✓ &nbsp; {t('4 + 2 = 7')} ✗</div>
				</div>
				<div class="rule-card">
					<div class="rule-icon">A</div>
					<h3>{t('Step 2 — Remember Letter')}</h3>
					<p>{t('A letter appears after each equation — memorize it')}</p>
					<div class="rule-example">{symbol('F')} → {symbol('K')} → {symbol('M')}...</div>
				</div>
				<div class="rule-card">
					<div class="rule-icon">×n</div>
					<h3>{t('Step 3 — Repeat')}</h3>
					<p>{t('2–8 math-letter pairs per set, depending on difficulty')}</p>
					<div class="rule-example">{t('Pairs adapt to your level')}</div>
				</div>
				<div class="rule-card">
					<div class="rule-icon">[…]</div>
					<h3>{t('Step 4 — Recall Letters')}</h3>
					<p>{t('Recall all letters in order at the end of the set')}</p>
					<div class="rule-example">{letterSequence(['F', 'K', 'M'])}</div>
				</div>
			</div>

			<div class="info-grid">
				<div class="info-section">
					<h3>{t('Memory Strategies')}</h3>
					<div class="tips-list">
						<div class="tip-item">✓ <strong>{t('Balance both tasks:')}</strong> {$locale === 'bn' ? 'দুটি কাজের মধ্যে ভারসাম্য রাখুন।' : "Don't sacrifice math for letters or vice versa"}</div>
						<div class="tip-item">✓ <strong>{t('Active rehearsal:')}</strong> {$locale === 'bn' ? 'প্রতিটি অক্ষর দেখার পর পুরো ধারাটি মনে মনে বলুন।' : 'Silently repeat all letters so far after each one'}</div>
						<div class="tip-item">✓ <strong>{t('Math first:')}</strong> {$locale === 'bn' ? 'দ্রুত গণিত যাচাই করুন, তারপর অক্ষরে মনোযোগ দিন।' : 'Quickly verify math, then shift focus to the letter'}</div>
						<div class="tip-item">✓ <strong>{t('Chunking:')}</strong> {$locale === 'bn' ? 'অক্ষরগুলো ২–৩টির দলে ভাগ করুন।' : 'Group letters into pairs (e.g. FK – MT – B)'}</div>
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
							<div class="structure-num">6</div>
							<div class="structure-text">
								<strong>{t('Total Sets')}</strong>
								<span>{t('Math + letter pairs per set')}</span>
							</div>
						</div>
					</div>
				</div>
			</div>

			<div class="clinical-info">
				<h3>{t('Clinical Significance')}</h3>
				<div class="clinical-grid">
					<div class="clinical-item">
						<strong>{t('Standard:')}</strong> {t('OSPAN — Turner & Engle (1989); the most cited complex span task')}
					</div>
					<div class="clinical-item">
						<strong>{t('Measures:')}</strong> {t('Executive working memory — simultaneous storage and processing')}
					</div>
					<div class="clinical-item">
						<strong>{t('MS Relevance:')}</strong> {t('Highly sensitive to MS cognitive impairment (Rao et al., 1991); included in MACFIMS')}
					</div>
					<div class="clinical-item">
						<strong>{t('Clinical Use:')}</strong> {t('Gold standard for assessing executive working memory in neuropsychology')}
					</div>
				</div>
			</div>

			<div class="button-group">
				<TaskPracticeActions
					locale={$locale}
					startLabel={localeText({ en: 'Begin Training', bn: 'প্রশিক্ষণ শুরু করুন' }, $locale)}
					statusMessage={practiceStatusMessage}
					align="center"
					on:start={() => startSession(TASK_PLAY_MODE.RECORDED)}
					on:practice={() => startSession(TASK_PLAY_MODE.PRACTICE)}
				/>
			</div>
		</div>
	{:else if state === STATE.READY}
		<div class="ready-screen">
			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
			{/if}
			<h2>{setLabel(currentTrialIndex + 1, trials.length)}</h2>
			<p class="set-info">{pairCountLabel(currentTrial.set_size)}</p>
			<p>{t('Get ready...')}</p>
		</div>
	{:else if state === STATE.MATH_PROBLEM}
		<div class="math-screen">
			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
			{/if}
			<div class="header">
				<div class="progress-info">
					<span class="set-badge">{setLabel(currentTrialIndex + 1, trials.length)}</span>
					<span class="item-badge">{problemLabel(currentItemIndex + 1, currentTrial.set_size)}</span>
				</div>
				<button class="help-button" on:click={toggleHelp}>?</button>
			</div>

			<div class="timer-bar">
				<div class="timer-fill" style="width: {(timeRemaining / currentTrial.time_limit) * 100}%"></div>
			</div>

			<div class="math-problem-display">
				<p class="instruction">{t('Is this equation correct?')}</p>
				<div class="equation">{t(currentItem.equation)}</div>
			</div>

			<div class="math-buttons">
				<button 
					class="math-btn correct-btn" 
					on:click={() => handleMathResponse(true)}
					disabled={mathResponse !== null}
				>
					<span class="btn-icon">✓</span>
					<span class="btn-label">{t('Correct')}</span>
				</button>
				<button 
					class="math-btn incorrect-btn" 
					on:click={() => handleMathResponse(false)}
					disabled={mathResponse !== null}
				>
					<span class="btn-icon">✗</span>
					<span class="btn-label">{t('Incorrect')}</span>
				</button>
			</div>
		</div>
	{:else if state === STATE.LETTER_DISPLAY}
		<div class="letter-screen">
			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
			{/if}
			<p class="instruction">{t('Remember this letter')}</p>
			<div class="letter-display">{symbol(currentItem.letter)}</div>
			<div class="letter-count">{letterProgressLabel(currentItemIndex + 1, currentTrial.set_size)}</div>
		</div>
	{:else if state === STATE.RECALL}
		<div class="recall-screen">
			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
			{/if}
			<div class="header">
				<div class="progress-info">
					<span class="set-badge">{setLabel(currentTrialIndex + 1, trials.length)}</span>
				</div>
				<button class="help-button" on:click={toggleHelp}>?</button>
			</div>

			<p class="instruction">{t('Recall the letters in order')}</p>

			<div class="selected-letters">
				{#if userLetters.length === 0}
					<span class="placeholder">{t('Click letters below...')}</span>
				{:else}
					{#each userLetters as letter, index}
						<span class="selected-letter">{n(index + 1)}. {symbol(letter)}</span>
					{/each}
				{/if}
			</div>

			<div class="letter-grid">
				{#each LETTERS as letter}
					<button 
						class="letter-btn" 
						class:selected={userLetters.includes(letter)}
						disabled={userLetters.includes(letter) || userLetters.length >= currentTrial.set_size}
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

			<button 
				class="submit-button" 
				on:click={submitRecall}
				disabled={userLetters.length === 0}
			>
				{t('Submit Recall')}
			</button>
		</div>
	{:else if state === STATE.FEEDBACK}
		<div class="feedback-screen">
			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
			{/if}
			<div class="feedback-icon {lastTrialCorrect ? 'correct' : 'incorrect'}">
				{lastTrialCorrect ? '✓' : '✗'}
			</div>
			<p class="feedback-text">
				{lastTrialCorrect ? t('Perfect!') : t('Not quite')}
			</p>
			{#if !lastTrialCorrect}
				<div class="correct-answer">
					<p>{t('Correct letters:')} <strong>{letterSequence(lastTrial.correct_letters)}</strong></p>
				</div>
			{/if}
		</div>
	{:else if state === STATE.COMPLETE}
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />
		<div class="complete-screen">
			<h1>{t('Session Complete!')}</h1>
			
			<div class="results-grid">
				<div class="result-card">
					<div class="result-value">{n(sessionResults.metrics.score)}</div>
					<div class="result-label">{t('Overall Score')}</div>
				</div>
				<div class="result-card">
					<div class="result-value">{pct(sessionResults.metrics.dual_task_performance)}</div>
					<div class="result-label">{t('Dual-Task Performance')}</div>
				</div>
				<div class="result-card math-card-result">
					<div class="result-value">{pct(sessionResults.metrics.math_accuracy)}</div>
					<div class="result-label">{t('Math Accuracy')}</div>
				</div>
				<div class="result-card letter-card-result">
					<div class="result-value">{pct(sessionResults.metrics.letter_recall_accuracy)}</div>
					<div class="result-label">{t('Letter Recall')}</div>
				</div>
			</div>

			<div class="performance-breakdown">
				<h3>{t('Performance Analysis')}</h3>
				<div class="breakdown-item">
					<span>{t('Perfect Sets (Both Tasks):')}</span>
					<span class="value">{n(sessionResults.metrics.correct_count)} / {n(sessionResults.metrics.total_trials)}</span>
				</div>
				<div class="breakdown-item">
					<span>{t('Consistency:')}</span>
					<span class="value">{pct(sessionResults.metrics.consistency)}</span>
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
				<button on:click={() => goto('/dashboard')}>{t('Back to Dashboard')}</button>
				<button on:click={() => goto('/dashboard')}>{t('View Dashboard')}</button>
			</div>
		</div>
	{/if}
</div>
</div>

{#if showHelp}
	<div class="help-modal" on:click={toggleHelp} role="dialog" tabindex="-1" on:keydown={(e) => e.key === 'Escape' && toggleHelp()}>
		<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
		<div class="help-content" on:click|stopPropagation role="dialog" tabindex="-1" on:keydown={(e) => e.key === 'Escape' && toggleHelp()} aria-modal="true" aria-label="Help">
			<button class="close-button" on:click={toggleHelp}>×</button>
			<h2>{t('Success Strategies')}</h2>
			
			<div class="strategy">
				<h3>{t('Balance Both Tasks')}</h3>
				<p>
					{$locale === 'bn'
						? 'আপনার স্কোর গণিতের নির্ভুলতা ও অক্ষর মনে রাখার ক্ষমতা দুটোর ওপরই নির্ভর করে। তাই একটি বাঁচাতে গিয়ে আরেকটি ছাড়বেন না।'
						: "Your score depends on BOTH math accuracy AND letter recall. Don't sacrifice one for the other - aim for high performance on both tasks."}
				</p>
			</div>
			
			<div class="strategy">
				<h3>{t('Math First, Letters After')}</h3>
				<p>
					{$locale === 'bn'
						? 'আগে সমীকরণটি দ্রুত যাচাই করুন, তারপর সঙ্গে সঙ্গে অক্ষরটি মনে গেঁথে নিন। উত্তর দেওয়ার পর সমীকরণে আর আটকে থাকবেন না।'
						: "Quickly verify the equation, then immediately shift focus to encoding the letter. Don't dwell on the math after answering."}
				</p>
			</div>
			
			<div class="strategy">
				<h3>{t('Active Rehearsal')}</h3>
				<p>
					{$locale === 'bn'
						? 'প্রতিটি অক্ষর দেখার পর এ পর্যন্ত দেখা সব অক্ষর মনে মনে ক্রমানুসারে আবার বলুন। এতে সেগুলো ওয়ার্কিং মেমরিতে সতেজ থাকে।'
						: 'After seeing each letter, silently rehearse ALL letters so far in order. This keeps them fresh in working memory.'}
				</p>
			</div>
			
			<div class="strategy">
				<h3>{t('Accuracy Over Speed')}</h3>
				<p>
					{$locale === 'bn'
						? 'প্রতিটি সমীকরণের জন্য যে সময় দেওয়া আছে তা পুরোটা প্রয়োজনে ব্যবহার করুন। তাড়াহুড়া করলে দুই কাজেই ভুল বাড়ে।'
						: 'Use the full time available for each equation. Rushing leads to errors in both tasks.'}
				</p>
			</div>
			
			<div class="strategy">
				<h3>{t('Chunking Strategy')}</h3>
				<p>
					{$locale === 'bn'
						? `অক্ষরগুলোকে ২-৩টির ছোট দলে মনে রাখুন, যেমন "${letterSequence(['F', 'K'])} - ${letterSequence(['M', 'T'])} - ${symbol('B')}"। এতে মনে রাখার চাপ কমে।`
						: 'Group letters into chunks of 2-3 (e.g., "FK-MT-B" instead of "F-K-M-T-B"). This reduces memory load.'}
				</p>
			</div>
		</div>
	</div>
{/if}

<style>
	.ospan-container {
		background: #C8DEFA;
		min-height: 100vh;
		padding: 2rem 1rem;
	}

	.ospan-inner {
		max-width: 960px;
		margin: 0 auto;
	}

	.loading-wrapper {
		padding: 3rem 0;
	}

	/* Instructions Card */
	.instructions-card {
		background: white;
		border-radius: 16px;
		padding: 2.5rem;
		box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 1rem;
		flex-wrap: wrap;
	}

	.header-content h1 {
		font-size: 1.8rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 0.35rem;
	}

	.header-content .subtitle {
		font-size: 0.95rem;
		color: #64748b;
		margin: 0 0 0.5rem;
	}

	.classic-badge {
		display: inline-block;
		background: #f1f5f9;
		color: #475569;
		font-size: 0.75rem;
		font-weight: 500;
		padding: 0.25rem 0.75rem;
		border-radius: 20px;
	}

	.header-right {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-shrink: 0;
	}

	.help-btn {
		width: 32px;
		height: 32px;
		border-radius: 50%;
		border: 2px solid #7c3aed;
		background: white;
		color: #7c3aed;
		font-weight: 700;
		font-size: 0.9rem;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.task-concept {
		background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
		border: 1px solid #ddd6fe;
		border-radius: 12px;
		padding: 1.25rem 1.5rem;
	}

	.task-concept h2 {
		font-size: 1.05rem;
		color: #5b21b6;
		font-weight: 700;
		margin: 0 0 0.4rem;
	}

	.task-concept p {
		font-size: 0.9rem;
		color: #374151;
		margin: 0;
		line-height: 1.5;
	}

	.rules-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0.75rem;
	}

	.rule-card {
		background: #fafafa;
		border-left: 4px solid #7c3aed;
		border-radius: 8px;
		padding: 1rem;
	}

	.rule-icon {
		font-size: 1.4rem;
		margin-bottom: 0.35rem;
	}

	.rule-card h3 {
		font-size: 0.85rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 0.25rem;
	}

	.rule-card p {
		font-size: 0.82rem;
		color: #64748b;
		margin: 0 0 0.4rem;
		line-height: 1.4;
	}

	.rule-example {
		background: #ede9fe;
		border-radius: 6px;
		padding: 0.3rem 0.6rem;
		font-size: 0.8rem;
		font-weight: 600;
		color: #5b21b6;
		font-family: monospace;
	}

	.info-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0.75rem;
	}

	.info-section {
		background: #f8fafc;
		border-radius: 10px;
		padding: 1rem 1.25rem;
	}

	.info-section h3 {
		font-size: 0.85rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 0.6rem;
	}

	.tips-list {
		display: flex;
		flex-direction: column;
		gap: 0.35rem;
	}

	.tip-item {
		font-size: 0.82rem;
		color: #374151;
		line-height: 1.4;
	}

	.structure-list {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	.structure-item {
		display: flex;
		align-items: flex-start;
		gap: 0.75rem;
	}

	.structure-num {
		background: #7c3aed;
		color: white;
		font-weight: 700;
		font-size: 1rem;
		border-radius: 8px;
		padding: 0.2rem 0.6rem;
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

	.clinical-info {
		background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
		border: 1px solid #bbf7d0;
		border-radius: 12px;
		padding: 1.25rem 1.5rem;
	}

	.clinical-info h3 {
		font-size: 0.9rem;
		font-weight: 700;
		color: #166534;
		margin: 0 0 0.75rem;
	}

	.clinical-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0.5rem;
	}

	.clinical-item {
		font-size: 0.82rem;
		color: #374151;
		line-height: 1.5;
	}

	.button-group {
		display: flex;
		justify-content: center;
		padding-top: 0.5rem;
	}

	.ready-screen {
		background: white;
		border-radius: 16px;
		padding: 4rem 2rem;
		text-align: center;
		box-shadow: 0 8px 32px rgba(0,0,0,0.2);
	}

	.ready-screen h2 {
		color: #667eea;
		margin-bottom: 1rem;
	}

	.set-info {
		color: #666;
		font-size: 1.1rem;
		margin-bottom: 1rem;
	}

	.math-screen, .letter-screen, .recall-screen {
		background: white;
		border-radius: 16px;
		padding: 2rem;
		box-shadow: 0 8px 32px rgba(0,0,0,0.2);
	}

	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
	}

	.progress-info {
		display: flex;
		gap: 0.5rem;
		align-items: center;
		flex-wrap: wrap;
	}

	.set-badge, .item-badge {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		padding: 0.5rem 1rem;
		border-radius: 20px;
		font-weight: 600;
		font-size: 0.9rem;
	}

	.help-button {
		width: 40px;
		height: 40px;
		border-radius: 50%;
		border: 2px solid #667eea;
		background: white;
		color: #667eea;
		font-size: 1.5rem;
		font-weight: bold;
		cursor: pointer;
		transition: all 0.3s;
	}

	.help-button:hover {
		background: #667eea;
		color: white;
	}

	.timer-bar {
		height: 8px;
		background: #e0e0e0;
		border-radius: 10px;
		overflow: hidden;
		margin-bottom: 2rem;
	}

	.timer-fill {
		height: 100%;
		background: linear-gradient(90deg, #4CAF50, #FFC107, #f44336);
		transition: width 0.1s linear;
		border-radius: 10px;
	}

	.math-problem-display {
		text-align: center;
		padding: 3rem 0;
	}

	.instruction {
		font-size: 1.2rem;
		color: #666;
		margin-bottom: 2rem;
	}

	.equation {
		font-size: 3rem;
		font-weight: bold;
		color: #2c3e50;
		padding: 2rem;
		background: #f8f9fa;
		border-radius: 12px;
		display: inline-block;
		min-width: 300px;
	}

	.math-buttons {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.5rem;
		max-width: 600px;
		margin: 0 auto;
	}

	.math-btn {
		padding: 2rem;
		border: none;
		border-radius: 12px;
		font-size: 1.3rem;
		font-weight: bold;
		cursor: pointer;
		transition: all 0.3s;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}

	.correct-btn {
		background: linear-gradient(135deg, #4CAF50, #45a049);
		color: white;
		box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
	}

	.correct-btn:hover:not(:disabled) {
		transform: translateY(-4px);
		box-shadow: 0 6px 20px rgba(76, 175, 80, 0.5);
	}

	.incorrect-btn {
		background: linear-gradient(135deg, #f44336, #d32f2f);
		color: white;
		box-shadow: 0 4px 12px rgba(244, 67, 54, 0.3);
	}

	.incorrect-btn:hover:not(:disabled) {
		transform: translateY(-4px);
		box-shadow: 0 6px 20px rgba(244, 67, 54, 0.5);
	}

	.math-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.btn-icon {
		font-size: 3rem;
	}

	.btn-label {
		font-size: 1.1rem;
	}

	.letter-screen {
		text-align: center;
		padding: 4rem 2rem;
	}

	.letter-display {
		font-size: 8rem;
		font-weight: bold;
		color: #667eea;
		margin: 2rem 0;
		text-shadow: 3px 3px 6px rgba(0,0,0,0.1);
	}

	.letter-count {
		color: #666;
		font-size: 1.1rem;
	}

	.recall-screen .instruction {
		text-align: center;
		margin-bottom: 1.5rem;
	}

	.selected-letters {
		background: #f8f9fa;
		padding: 1.5rem;
		border-radius: 12px;
		min-height: 80px;
		display: flex;
		gap: 1rem;
		align-items: center;
		flex-wrap: wrap;
		margin-bottom: 2rem;
		justify-content: center;
	}

	.placeholder {
		color: #999;
		font-style: italic;
	}

	.selected-letter {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		padding: 0.75rem 1.25rem;
		border-radius: 8px;
		font-weight: bold;
		font-size: 1.3rem;
	}

	.letter-grid {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		gap: 0.75rem;
		margin-bottom: 1.5rem;
	}

	.letter-btn {
		aspect-ratio: 1;
		border: 2px solid #667eea;
		background: white;
		border-radius: 12px;
		font-size: 1.3rem;
		font-weight: bold;
		color: #667eea;
		cursor: pointer;
		transition: all 0.2s;
	}

	.letter-btn:hover:not(:disabled) {
		background: #667eea;
		color: white;
		transform: scale(1.05);
	}

	.letter-btn:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}

	.controls {
		display: flex;
		gap: 0.5rem;
		justify-content: center;
		margin-bottom: 1.5rem;
	}

	.control-btn {
		padding: 0.75rem 1.5rem;
		border: 2px solid #FF9800;
		background: white;
		color: #FF9800;
		border-radius: 8px;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
	}

	.control-btn:hover:not(:disabled) {
		background: #FF9800;
		color: white;
	}

	.control-btn:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}

	.submit-button {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		padding: 1rem 3rem;
		font-size: 1.2rem;
		font-weight: bold;
		border-radius: 12px;
		cursor: pointer;
		transition: all 0.3s;
		display: block;
		margin: 0 auto;
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
	}

	.submit-button:hover:not(:disabled) {
		transform: translateY(-2px);
		box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
	}

	.submit-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.feedback-screen {
		background: white;
		border-radius: 16px;
		padding: 4rem 2rem;
		text-align: center;
		box-shadow: 0 8px 32px rgba(0,0,0,0.2);
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
		background: linear-gradient(135deg, #4CAF50, #45a049);
	}

	.feedback-icon.incorrect {
		background: linear-gradient(135deg, #f44336, #d32f2f);
	}

	.feedback-text {
		font-size: 2rem;
		font-weight: bold;
		color: #2c3e50;
	}

	.correct-answer {
		margin-top: 2rem;
		background: #f8f9fa;
		padding: 1.5rem;
		border-radius: 12px;
	}

	.complete-screen {
		background: white;
		border-radius: 16px;
		padding: 3rem 2rem;
		box-shadow: 0 8px 32px rgba(0,0,0,0.2);
		text-align: center;
	}

	.complete-screen h1 {
		color: #667eea;
		margin-bottom: 2rem;
	}

	.results-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: 1rem;
		margin: 2rem 0;
	}

	.result-card {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		padding: 1.5rem;
		border-radius: 12px;
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
	}

	.math-card-result {
		background: linear-gradient(135deg, #4CAF50, #45a049);
	}

	.letter-card-result {
		background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
	}

	.result-value {
		font-size: 2.5rem;
		font-weight: bold;
		margin-bottom: 0.5rem;
	}

	.result-label {
		font-size: 0.9rem;
		opacity: 0.9;
	}

	.performance-breakdown {
		background: #f8f9fa;
		padding: 1.5rem;
		border-radius: 12px;
		margin: 2rem 0;
	}

	.performance-breakdown h3 {
		margin: 0 0 1rem 0;
		color: #2c3e50;
	}

	.breakdown-item {
		display: flex;
		justify-content: space-between;
		padding: 0.75rem 0;
		border-bottom: 1px solid #e0e0e0;
	}

	.breakdown-item:last-child {
		border-bottom: none;
	}

	.breakdown-item .value {
		font-weight: bold;
		color: #667eea;
	}

	.difficulty-info {
		background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
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
		padding: 0.75rem;
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
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s;
	}

	.actions button:first-child {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
	}

	.actions button:first-child:hover {
		transform: translateY(-2px);
	}

	.actions button:last-child {
		background: linear-gradient(135deg, #4CAF50, #45a049);
		color: white;
	}

	.actions button:last-child:hover {
		transform: translateY(-2px);
	}

	.help-modal {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.7);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
	}

	.help-content {
		background: white;
		padding: 2rem;
		border-radius: 16px;
		max-width: 600px;
		max-height: 80vh;
		overflow-y: auto;
		position: relative;
		box-shadow: 0 8px 32px rgba(0,0,0,0.3);
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
		color: #667eea;
		margin-bottom: 1.5rem;
	}

	.strategy {
		margin-bottom: 1.5rem;
		padding: 1rem;
		background: #f8f9fa;
		border-radius: 8px;
		border-left: 4px solid #667eea;
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


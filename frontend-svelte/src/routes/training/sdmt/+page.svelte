<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
	import { formatNumber, locale, localeText, translateText } from '$lib/i18n';
	import { buildPracticePayload, getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
	import { onDestroy, onMount } from 'svelte';

	// Task states
	const STATE = {
		LOADING: 'loading',
		INSTRUCTIONS: 'instructions',
		READY: 'ready',
		TESTING: 'testing',
		COMPLETE: 'complete'
	};

	let state = STATE.LOADING;
	let difficulty = 5;
	let trial = null;
	
	// Test state
	let currentIndex = 0;
	let userResponses = [];
	let responseTimes = [];
	let startTime = 0;
	let itemStartTime = 0;
	let timeRemaining = 90;
	let timerInterval = null;
	let currentInput = '';
	
	let showHelp = false;
	let sessionResults = null;
	let taskId = null;
	/** @type {"practice" | "recorded"} */
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';
	let recordedTrial = null;
	let readyTimeout = null;

	// Symbol display
	let symbolDigitMapping = {};
	let testSequence = [];
	let currentSymbol = '';

	function t(text) {
		return translateText(text ?? '', $locale);
	}

	function lt(en, bn) {
		return localeText({ en, bn }, $locale);
	}

	function n(value, options = {}) {
		return formatNumber(value, $locale, options);
	}

	function msText(value) {
		return $locale === 'bn' ? `${n(value)} মিলিসেকেন্ড` : `${n(value)} ms`;
	}

	function secondsText(value, digits = 1) {
		return `${n(value, {
			minimumFractionDigits: digits,
			maximumFractionDigits: digits
		})}${lt('s', 'সে')}`;
	}

	function percentText(value, digits = 1) {
		return `${n(value, {
			minimumFractionDigits: digits,
			maximumFractionDigits: digits
		})}%`;
	}

	onMount(async () => {
		await loadSession();
	});

	onDestroy(() => {
		if (timerInterval) clearInterval(timerInterval);
		if (readyTimeout) clearTimeout(readyTimeout);
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
				userDifficulty = currentDiff.processing_speed || 5;
				console.log('📊 SDMT - Loaded difficulty from plan:', userDifficulty, 'Full diff:', currentDiff);
			}

			difficulty = userDifficulty;
			console.log('📊 SDMT - Final difficulty:', difficulty);

			const response = await fetch(
				`http://localhost:8000/api/training/tasks/sdmt/generate/${userId}?difficulty=${difficulty}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' }
				}
			);

			if (!response.ok) throw new Error('Failed to load session');

			const data = await response.json();
			trial = structuredClone(data.trial);
			recordedTrial = structuredClone(data.trial);
			symbolDigitMapping = trial.symbol_digit_mapping;
			testSequence = trial.test_sequence;
			
			state = STATE.INSTRUCTIONS;
		} catch (error) {
			console.error('Error loading session:', error);
			alert(t('Failed to load task session'));
			goto('/dashboard');
		}
	}

	/** @param {"practice" | "recorded"} [nextMode] */
	function startTest(nextMode = TASK_PLAY_MODE.RECORDED) {
		if (timerInterval) {
			clearInterval(timerInterval);
			timerInterval = null;
		}
		if (readyTimeout) {
			clearTimeout(readyTimeout);
			readyTimeout = null;
		}

		playMode = nextMode;
		practiceStatusMessage = '';
		trial = nextMode === TASK_PLAY_MODE.PRACTICE
			? buildPracticePayload('sdmt', { trial: recordedTrial }).trial
			: structuredClone(recordedTrial);
		symbolDigitMapping = trial.symbol_digit_mapping;
		testSequence = trial.test_sequence;
		state = STATE.READY;
		readyTimeout = setTimeout(() => {
			readyTimeout = null;
			state = STATE.TESTING;
			startTime = Date.now();
			timeRemaining = trial.duration_seconds;
			currentIndex = 0;
			userResponses = [];
			responseTimes = [];
			currentSymbol = testSequence[currentIndex];
			itemStartTime = Date.now();
			startTimer();
		}, 2000);
	}

	function leavePractice(completed = false) {
		if (timerInterval) {
			clearInterval(timerInterval);
			timerInterval = null;
		}
		if (readyTimeout) {
			clearTimeout(readyTimeout);
			readyTimeout = null;
		}

		trial = structuredClone(recordedTrial);
		symbolDigitMapping = trial.symbol_digit_mapping;
		testSequence = trial.test_sequence;
		playMode = TASK_PLAY_MODE.RECORDED;
		practiceStatusMessage = completed ? getPracticeCopy($locale).complete : '';
		currentIndex = 0;
		userResponses = [];
		responseTimes = [];
		startTime = 0;
		itemStartTime = 0;
		timeRemaining = trial.duration_seconds;
		currentInput = '';
		currentSymbol = '';
		state = STATE.INSTRUCTIONS;
	}

	function startTimer() {
		if (timerInterval) clearInterval(timerInterval);
		
		timerInterval = setInterval(() => {
			timeRemaining -= 0.1;
			if (timeRemaining <= 0) {
				clearInterval(timerInterval);
				finishTest();
			}
		}, 100);
	}

	function handleKeyPress(event) {
		if (state !== STATE.TESTING) return;
		
		const key = event.key;
		
		// Only accept digit keys
		if (key >= '0' && key <= '9') {
			const digit = parseInt(key);
			
			// Check if this digit exists in the mapping
			const validDigits = Object.values(symbolDigitMapping);
			if (validDigits.includes(digit)) {
				recordResponse(digit);
			}
		} else if (key === 'Backspace') {
			currentInput = '';
		}
	}

	function handleDigitClick(digit) {
		if (state !== STATE.TESTING) return;
		recordResponse(digit);
	}

	function recordResponse(digit) {
		const reactionTime = Date.now() - itemStartTime;
		
		userResponses.push(digit);
		responseTimes.push(reactionTime);
		
		// Move to next symbol
		currentIndex++;
		
		if (currentIndex >= testSequence.length) {
			finishTest();
			return;
		}
		
		currentSymbol = testSequence[currentIndex];
		itemStartTime = Date.now();
		currentInput = '';
	}

	async function finishTest() {
		if (playMode === TASK_PLAY_MODE.PRACTICE) {
			leavePractice(true);
			return;
		}

		if (timerInterval) {
			clearInterval(timerInterval);
			timerInterval = null;
		}
		if (readyTimeout) {
			clearTimeout(readyTimeout);
			readyTimeout = null;
		}
		state = STATE.LOADING;
		taskId = $page.url.searchParams.get('taskId');
		
		try {
			const userData = JSON.parse(localStorage.getItem('user') || '{}');
			const userId = userData.id;

			const response = await fetch(
				`http://localhost:8000/api/training/tasks/sdmt/submit/${userId}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						difficulty: difficulty,
						trial: trial,
						user_responses: userResponses,
						response_times: responseTimes,
						completed_count: currentIndex,
						task_id: taskId
					})
				}
			);

			if (!response.ok) throw new Error('Failed to submit results');

			sessionResults = await response.json();
			state = STATE.COMPLETE;
		} catch (error) {
			console.error('Error submitting results:', error);
			alert(t('Failed to submit results'));
		}
	}

	function toggleHelp() {
		showHelp = !showHelp;
	}

	// Get performance level based on score
	function getPerformanceLevel(score) {
		if (score >= 60) return { level: t('Excellent'), color: '#4CAF50' };
		if (score >= 50) return { level: t('Good'), color: '#8BC34A' };
		if (score >= 40) return { level: t('Average'), color: '#FFC107' };
		if (score >= 30) return { level: t('Fair'), color: '#FF9800' };
		return { level: t('Needs Practice'), color: '#f44336' };
	}
</script>

<svelte:window on:keydown={handleKeyPress} />

<div class="sdmt-container" data-localize-skip>
<div class="sdmt-inner">
	{#if state === STATE.LOADING}
		<div class="loading-wrapper">
			<LoadingSkeleton variant="card" count={3} />
		</div>

	{:else if state === STATE.INSTRUCTIONS}
		<div class="instructions-card">
			<div class="header">
				<div class="header-content">
					<h1>{t('Symbol Digit Modalities Test')}</h1>
					<p class="subtitle">{t('Processing Speed — Gold Standard for MS Assessment')}</p>
					<div class="classic-badge">{t('SDMT · Smith (1973) · MACFIMS Battery')}</div>
				</div>
				<div class="header-right">
					<DifficultyBadge {difficulty} domain="Processing Speed" />
					<button class="help-btn" on:click={toggleHelp} aria-label={t('Help')}>?</button>
				</div>
			</div>

			<div class="task-concept">
				<h2>{t('Your Task: Match Symbols to Numbers')}</h2>
				<p>{$locale === 'bn' ? 'একটি রেফারেন্স কী দেওয়া থাকবে যেখানে প্রতিটি প্রতীকের সাথে একটি সংখ্যা মেলানো আছে। যত দ্রুত সম্ভব সঠিক সংখ্যাটি টাইপ করুন।' : 'A reference key shows which digit matches each symbol. See a symbol, type its matching digit as fast as you can — repeat for 90 seconds.'}</p>
			</div>

			<div class="key-preview-section">
				<h3>{t('Example Symbol–Digit Key')}</h3>
				<div class="key-preview-grid">
					<div class="kp-pair"><span class="kp-sym">★</span><span class="kp-arrow">→</span><span class="kp-num">1</span></div>
					<div class="kp-pair"><span class="kp-sym">●</span><span class="kp-arrow">→</span><span class="kp-num">2</span></div>
					<div class="kp-pair"><span class="kp-sym">■</span><span class="kp-arrow">→</span><span class="kp-num">3</span></div>
					<div class="kp-pair"><span class="kp-sym">▲</span><span class="kp-arrow">→</span><span class="kp-num">4</span></div>
					<div class="kp-pair"><span class="kp-sym">◆</span><span class="kp-arrow">→</span><span class="kp-num">5</span></div>
					<div class="kp-pair"><span class="kp-sym">♦</span><span class="kp-arrow">→</span><span class="kp-num">6</span></div>
				</div>
				<p class="key-note">{t('Your actual key will be shown before the test begins. Study it carefully!')}</p>
			</div>

			<div class="rules-grid">
				<div class="rule-card">
					<div class="rule-icon">Key</div>
					<h3>{t('Step 1 — Study the Key')}</h3>
					<p>{t('Review the symbol–digit pairs shown at the top of the screen')}</p>
					<div class="rule-example">{t('Key stays visible the whole time')}</div>
				</div>
				<div class="rule-card">
					<div class="rule-icon">Look</div>
					<h3>{t('Step 2 — See a Symbol')}</h3>
					<p>{t('A large symbol appears in the centre of the screen')}</p>
					<div class="rule-example">{t('e.g.  ■  appears')}</div>
				</div>
				<div class="rule-card">
					<div class="rule-icon">Type</div>
					<h3>{t('Step 3 — Type the Digit')}</h3>
					<p>{t('Press the matching number key or tap the on-screen button')}</p>
					<div class="rule-example">{t('Keyboard is fastest!')}</div>
				</div>
				<div class="rule-card">
					<div class="rule-icon">×n</div>
					<h3>{t('Step 4 — Repeat')}</h3>
					<p>{t('Answer as many symbols as you can within 90 seconds')}</p>
					<div class="rule-example">{lt(`Target: ${trial?.target_responses ?? 55}+ correct`, `লক্ষ্য: ${n(trial?.target_responses ?? 55)}+`)}</div>
				</div>
			</div>

			<div class="info-grid">
				<div class="info-section">
					<h3>{t('Speed Tips')}</h3>
					<div class="tips-list">
						<div class="tip-item">✓ <strong>{t('Keyboard numbers:')}</strong> {t('Much faster than tapping buttons')}</div>
						<div class="tip-item">✓ <strong>{t('Glance, type, next:')}</strong> {t('Find a steady rhythm — look, press, move on')}</div>
						<div class="tip-item">✓ <strong>{t('Memorise the key:')}</strong> {t("You'll learn pairs naturally as you go")}</div>
						<div class="tip-item">✓ <strong>{t("Don't dwell:")}</strong> {t('If unsure, make a quick guess and keep going')}</div>
					</div>
				</div>
				<div class="info-section">
					<h3>{t('Test Format')}</h3>
					<div class="structure-list">
						<div class="structure-item">
							<div class="structure-num">90</div>
							<div class="structure-text">
								<strong>{t('Seconds')}</strong>
								<span>{t('Timed challenge')}</span>
							</div>
						</div>
						<div class="structure-item">
							<div class="structure-num">{n(trial?.target_responses ?? 55)}</div>
							<div class="structure-text">
								<strong>{t('Target Score')}</strong>
								<span>{t('Correct responses')}</span>
							</div>
						</div>
						<div class="structure-item">
							<div class="structure-num">{n(difficulty)}</div>
							<div class="structure-text">
								<strong>{t('Difficulty')}</strong>
								<span>{t('Adapts after each session')}</span>
							</div>
						</div>
					</div>
				</div>
			</div>

			<div class="clinical-info">
				<h3>{t('Clinical Significance')}</h3>
				<div class="clinical-grid">
					<div class="clinical-item">
						<strong>{t('Gold Standard:')}</strong> {t('Most widely used test in MS clinical trials globally')}
					</div>
					<div class="clinical-item">
						<strong>{t('Measures:')}</strong> {t('Processing speed — how fast your brain retrieves and applies information')}
					</div>
					<div class="clinical-item">
						<strong>{t('MS Relevance:')}</strong> {t('Detects cognitive changes earlier than any other single test; correlates with brain health')}
					</div>
					<div class="clinical-item">
						<strong>{t('Real-World Impact:')}</strong> {t('Predicts employment success, driving safety, and daily functioning for MS patients')}
					</div>
				</div>
			</div>

			<div class="perf-guide">
				<h3>{t('Performance Guide (MS Norms)')}</h3>
				<div class="norm-bars">
					<div class="norm-bar norm-excellent"><span class="norm-label">{lt('60+ Correct', `${n(60)}+ ${t('Correct')}`)}</span><span class="norm-tag">{t('Excellent')}</span></div>
					<div class="norm-bar norm-good"><span class="norm-label">{lt('50–60', `${n(50)}–${n(60)}`)}</span><span class="norm-tag">{t('Good')}</span></div>
					<div class="norm-bar norm-avg"><span class="norm-label">{lt('40–50', `${n(40)}–${n(50)}`)}</span><span class="norm-tag">{t('Average')}</span></div>
					<div class="norm-bar norm-fair"><span class="norm-label">{lt('30–40', `${n(30)}–${n(40)}`)}</span><span class="norm-tag">{t('Fair')}</span></div>
					<div class="norm-bar norm-needs"><span class="norm-label">{lt('< 30', `< ${n(30)}`)}</span><span class="norm-tag">{t('Needs Practice')}</span></div>
				</div>
			</div>

			<div class="button-group">
				<TaskPracticeActions
					locale={$locale}
					startLabel={localeText({ en: 'Begin Test', bn: 'পরীক্ষা শুরু করুন' }, $locale)}
					statusMessage={practiceStatusMessage}
					align="center"
					on:start={() => startTest(TASK_PLAY_MODE.RECORDED)}
					on:practice={() => startTest(TASK_PLAY_MODE.PRACTICE)}
				/>
			</div>
		</div>

	{:else if state === STATE.READY}
		<div class="screen-card ready-screen">
			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
			{/if}
			<h2>{t('Study the Reference Key')}</h2>
			<p class="ready-sub">{t('Memorise these symbol–digit pairs before the test begins')}</p>
			<div class="key-display">
				{#each Object.entries(symbolDigitMapping) as [symbol, digit]}
					<div class="key-pair">
						<div class="key-symbol">{symbol}</div>
						<div class="key-arrow">→</div>
						<div class="key-digit">{n(digit)}</div>
					</div>
				{/each}
			</div>
			<p class="ready-countdown">{t('Starting in 2 seconds...')}</p>
		</div>

	{:else if state === STATE.TESTING}
		<div class="screen-card testing-screen">
			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
			{/if}
			<div class="test-header">
				<div class="progress-info">
					<span class="count-badge">✓ {lt(`${currentIndex}`, `${n(currentIndex)}`)} {t('done')}</span>
					<span class="target-badge">{lt(`${trial.target_responses}`, `${n(trial.target_responses)}`)} {t('target')}</span>
				</div>
				<div class="timer-display" class:urgent={timeRemaining < 10}>
					<span class="timer-icon">⏱</span>
					<span class="timer-value">{secondsText(Math.max(0, timeRemaining), 1)}</span>
				</div>
				<button class="help-btn-sm" on:click={toggleHelp} aria-label={t('Help')}>?</button>
			</div>

			<div class="reference-key">
				<div class="key-label">{t('Reference Key')}</div>
				<div class="key-grid">
					{#each Object.entries(symbolDigitMapping) as [symbol, digit]}
						<div class="key-item">
							<span class="ref-symbol">{symbol}</span>
							<span class="ref-arrow">→</span>
							<span class="ref-digit">{n(digit)}</span>
						</div>
					{/each}
				</div>
			</div>

			<div class="test-area">
				<p class="task-prompt">{t('What number matches this symbol?')}</p>
				<div class="current-symbol">{currentSymbol}</div>
				<div class="digit-buttons">
					{#each Object.values(symbolDigitMapping).sort((a, b) => a - b) as digit}
						<button class="digit-btn" on:click={() => handleDigitClick(digit)}>
							{n(digit)}
						</button>
					{/each}
				</div>
			</div>

			<div class="progress-bar">
				<div class="progress-fill" style="width: {(currentIndex / trial.test_sequence.length) * 100}%"></div>
			</div>
		</div>

	{:else if state === STATE.COMPLETE}
		<div class="screen-card complete-screen">
			<h1>{t('SDMT Complete!')}</h1>

			{#if sessionResults}
				{@const perfLevel = getPerformanceLevel(sessionResults.metrics.score)}

				{#if sessionResults.new_badges && sessionResults.new_badges.length > 0}
					<BadgeNotification badges={sessionResults.new_badges} />
				{/if}

				<div class="perf-banner" style="--perf-color: {perfLevel.color}">
					<div class="perf-label">{perfLevel.level}</div>
					<div class="perf-score">{n(sessionResults.metrics.score)} {t('correct')}</div>
				</div>

				<div class="metrics-grid">
					<div class="metric-card highlight">
						<div class="metric-icon">◎</div>
						<div class="metric-value">{n(sessionResults.metrics.score)}</div>
						<div class="metric-label">{t('Correct Responses')}</div>
						<div class="metric-sub">{lt(`Target: ${trial.target_responses}`, `লক্ষ্য: ${n(trial.target_responses)}`)}</div>
					</div>
					<div class="metric-card">
						<div class="metric-icon">→</div>
						<div class="metric-value">{n(sessionResults.metrics.processing_speed)}</div>
						<div class="metric-label">{t('Processing Speed')}</div>
						<div class="metric-sub">{t('Responses / min')}</div>
					</div>
					<div class="metric-card">
						<div class="metric-icon">✓</div>
						<div class="metric-value">{percentText(sessionResults.metrics.accuracy)}</div>
						<div class="metric-label">{t('Accuracy')}</div>
						<div class="metric-sub">{t('Of attempted items')}</div>
					</div>
					<div class="metric-card">
						<div class="metric-icon">⏱</div>
						<div class="metric-value">{secondsText(sessionResults.metrics.avg_response_time / 1000, 2)}</div>
						<div class="metric-label">{t('Avg Response Time')}</div>
						<div class="metric-sub">{t('Per correct item')}</div>
					</div>
				</div>

				<div class="breakdown">
					<h3>{t('Detailed Breakdown')}</h3>
					<div class="breakdown-row">
						<span>{t('Total Attempted')}</span>
						<strong>{n(sessionResults.metrics.total_attempted)}</strong>
					</div>
					<div class="breakdown-row">
						<span style="color:#16a34a">{t('Correct')}</span>
						<strong style="color:#16a34a">{n(sessionResults.metrics.correct_count)}</strong>
					</div>
					<div class="breakdown-row">
						<span style="color:#dc2626">{t('Incorrect')}</span>
						<strong style="color:#dc2626">{n(sessionResults.metrics.incorrect_count)}</strong>
					</div>
					<div class="breakdown-row">
						<span>{t('Consistency')}</span>
						<strong>{percentText(sessionResults.metrics.consistency)}</strong>
					</div>
				</div>

				<div class="clinical-note">
					<h3>{t('Clinical Context')}</h3>
					<p>
						{#if sessionResults.metrics.score >= 60}
							{t('Excellent performance! Your processing speed is above average for MS patients, suggesting good cognitive efficiency.')}
						{:else if sessionResults.metrics.score >= 50}
							{t('Good performance! Your score is in the average-to-above-average range. Continue training to build on this.')}
						{:else if sessionResults.metrics.score >= 40}
							{t('Average performance. Regular training can improve processing speed over time.')}
						{:else if sessionResults.metrics.score >= 30}
							{t("Fair performance. Consistent practice with SDMT leads to significant gains in processing speed.")}
						{:else}
							{t('Keep going! Processing speed is trainable. Each session builds the neural pathways needed for faster cognition.')}
						{/if}
					</p>
				</div>

				<div class="difficulty-info">
					<p>{t('Difficulty')}: <strong>{n(sessionResults.difficulty_before)}</strong> → <strong>{n(sessionResults.difficulty_after)}</strong></p>
					<p class="adapt-reason">{t(sessionResults.adaptation_reason)}</p>
				</div>

				<div class="button-group">
					<button class="start-button" on:click={() => goto('/training')}>{t('Back to Training')}</button>
					<button class="btn-secondary" on:click={() => goto('/dashboard')}>{t('View Dashboard')}</button>
				</div>
			{/if}
		</div>
	{/if}
</div>
</div>

{#if showHelp}
	<div class="modal-overlay" on:click={toggleHelp} role="dialog" tabindex="-1" on:keydown={(e) => e.key === 'Escape' && toggleHelp()}>
		<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
		<div class="modal-content" on:click|stopPropagation role="document" tabindex="-1" on:keydown={(e) => e.key === 'Escape' && toggleHelp()}>
			<button class="close-btn" on:click={toggleHelp}>&times;</button>
			<h2>{t('SDMT Success Strategies')}</h2>
			<div class="strategy">
				<h3>{t('Visual Scanning')}</h3>
				<p>{lt("Train your eyes to quickly dart between the symbol, the key, and back. With practice, you'll memorise most pairs.", 'চোখকে এমনভাবে অনুশীলন করুন যেন প্রতীক, কী, এবং আবার প্রতীকের দিকে দ্রুত যেতে পারে।')}</p>
			</div>
			<div class="strategy">
				<h3>{t('Chunking Memory')}</h3>
				<p>{lt('Group symbols by shape or type. This creates mental "buckets" that make recall faster.', 'মনে মনে প্রতীকগুলোকে আকার বা ধরন অনুযায়ী ভাগ করুন।')}</p>
			</div>
			<div class="strategy">
				<h3>{t('Keyboard Mastery')}</h3>
				<p>{lt('Use the number row on your keyboard. Position fingers over commonly used digits. Much faster than clicking!', 'কীবোর্ডের সংখ্যার সারি ব্যবহার করুন।')}</p>
			</div>
			<div class="strategy">
				<h3>{t('Rhythm Over Perfection')}</h3>
				<p>{lt("Find a steady rhythm: glance → type → next. Don't stop to verify each answer.", 'একটি স্থির ছন্দ তৈরি করুন: দেখুন → টাইপ করুন → এগোন।')}</p>
			</div>
			<div class="strategy">
				<h3>{t('Why This Matters')}</h3>
				<p>{lt('SDMT measures neural processing efficiency. Regular practice strengthens these neural pathways!', 'SDMT মাপে মস্তিষ্ক কত দ্রুত তথ্য প্রয়োগ করতে পারে।')}</p>
			</div>
		</div>
	</div>
{/if}

<style>
	/* ── Layout ── */
	.sdmt-container {
		background: #C8DEFA;
		min-height: 100vh;
		padding: 2rem 1rem;
	}

	.sdmt-inner {
		max-width: 960px;
		margin: 0 auto;
	}

	/* ── Loading ── */
	.loading-wrapper {
		padding: 3rem 0;
	}

	/* ── Instructions Card ── */
	.instructions-card {
		background: #fff;
		border-radius: 16px;
		padding: 2.5rem;
		box-shadow: 0 4px 6px rgba(0,0,0,0.07), 0 1px 3px rgba(0,0,0,0.06);
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
		margin: 0 0 0.3rem;
	}

	.subtitle {
		font-size: 0.95rem;
		color: #64748b;
		margin: 0 0 0.5rem;
	}

	.classic-badge {
		display: inline-block;
		background: rgba(102,126,234,0.12);
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

	.help-btn {
		width: 38px;
		height: 38px;
		border-radius: 50%;
		border: 2px solid #667eea;
		background: white;
		color: #667eea;
		font-size: 1.1rem;
		font-weight: bold;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all 0.2s;
	}
	.help-btn:hover { background:#667eea; color:white; }

	/* ── Task Concept ── */
	.task-concept {
		background: linear-gradient(135deg, #fef9c3 0%, #fef08a 100%);
		border: 1px solid #fde047;
		border-radius: 12px;
		padding: 1.25rem 1.5rem;
	}

	.task-concept h2 {
		font-size: 1.05rem;
		color: #713f12;
		font-weight: 700;
		margin: 0 0 0.4rem;
	}

	.task-concept p {
		font-size: 0.9rem;
		color: #431407;
		margin: 0;
		line-height: 1.5;
	}

	/* ── Key Preview ── */
	.key-preview-section {
		background: #f8fafc;
		border-radius: 12px;
		padding: 1.25rem 1.5rem;
	}

	.key-preview-section h3 {
		font-size: 0.88rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 0.75rem;
	}

	.key-preview-grid {
		display: flex;
		gap: 0.6rem;
		flex-wrap: wrap;
	}

	.kp-pair {
		display: flex;
		align-items: center;
		gap: 0.3rem;
		background: white;
		border: 1px solid #e2e8f0;
		border-radius: 10px;
		padding: 0.5rem 0.85rem;
	}

	.kp-sym {
		font-size: 1.4rem;
		color: #667eea;
		font-weight: bold;
	}

	.kp-arrow {
		font-size: 0.85rem;
		color: #94a3b8;
	}

	.kp-num {
		font-size: 1.15rem;
		font-weight: 700;
		color: #16a34a;
	}

	.key-note {
		font-size: 0.8rem;
		color: #64748b;
		margin: 0.6rem 0 0;
	}

	/* ── Rules Grid ── */
	.rules-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0.75rem;
	}

	.rule-card {
		background: #fafafa;
		border-left: 4px solid #667eea;
		border-radius: 8px;
		padding: 1rem;
	}

	.rule-icon { font-size: 1.4rem; margin-bottom: 0.3rem; }

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
	}

	/* ── Info Grid ── */
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

	.tips-list { display: flex; flex-direction: column; gap: 0.35rem; }

	.tip-item {
		font-size: 0.82rem;
		color: #374151;
		line-height: 1.4;
	}

	.structure-list { display: flex; flex-direction: column; gap: 0.6rem; }

	.structure-item {
		display: flex;
		align-items: flex-start;
		gap: 0.75rem;
	}

	.structure-num {
		background: #667eea;
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

	/* ── Clinical Info ── */
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

	/* ── Performance Guide ── */
	.perf-guide {
		background: #f8fafc;
		border-radius: 12px;
		padding: 1.25rem 1.5rem;
	}

	.perf-guide h3 {
		font-size: 0.88rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 0.75rem;
	}

	.norm-bars {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}

	.norm-bar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.5rem 1rem;
		border-radius: 8px;
		font-size: 0.85rem;
		font-weight: 600;
	}

	.norm-label { flex: 1; }
	.norm-tag { font-size: 0.78rem; opacity: 0.9; }

	.norm-excellent { background:#dcfce7; color:#166534; }
	.norm-good      { background:#d1fae5; color:#065f46; }
	.norm-avg       { background:#fef9c3; color:#713f12; }
	.norm-fair      { background:#ffedd5; color:#9a3412; }
	.norm-needs     { background:#fee2e2; color:#991b1b; }

	/* ── Button Group ── */
	.button-group {
		display: flex;
		justify-content: center;
		padding-top: 0.5rem;
	}

	/* ── Shared Screen Card ── */
	.screen-card {
		background: white;
		border-radius: 16px;
		padding: 2.5rem 2rem;
		box-shadow: 0 4px 6px rgba(0,0,0,0.07);
	}

	/* ── Ready Screen ── */
	.ready-screen {
		text-align: center;
	}

	.ready-screen h2 {
		font-size: 1.6rem;
		color: #1e293b;
		margin-bottom: 0.5rem;
	}

	.ready-sub {
		color: #64748b;
		font-size: 1rem;
		margin-bottom: 2rem;
	}

	.key-display {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(90px, 1fr));
		gap: 0.75rem;
		max-width: 800px;
		margin: 0 auto 2rem;
	}

	.key-pair {
		background: #f1f5f9;
		border: 2px solid #667eea;
		border-radius: 12px;
		padding: 1.25rem 0.75rem;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 0.25rem;
		font-weight: bold;
	}

	.key-symbol { font-size: 1.8rem; color: #667eea; }
	.key-arrow  { font-size: 0.9rem; color: #94a3b8; }
	.key-digit  { font-size: 1.5rem; color: #16a34a; }

	.ready-countdown {
		color: #f59e0b;
		font-weight: 700;
		font-size: 1.05rem;
		margin-top: 1rem;
	}

	/* ── Testing Screen ── */
	.testing-screen { position: relative; }

	.test-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.75rem;
		margin-bottom: 1.25rem;
		flex-wrap: wrap;
	}

	.progress-info { display: flex; gap: 0.5rem; align-items: center; }

	.count-badge {
		background: #667eea;
		color: white;
		padding: 0.35rem 0.9rem;
		border-radius: 20px;
		font-size: 0.85rem;
		font-weight: 600;
	}

	.target-badge {
		background: #f1f5f9;
		color: #374151;
		padding: 0.35rem 0.9rem;
		border-radius: 20px;
		font-size: 0.85rem;
		font-weight: 600;
	}

	.timer-display {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		background: #f8fafc;
		padding: 0.5rem 1.2rem;
		border-radius: 25px;
		border: 2px solid #16a34a;
	}

	.timer-display.urgent {
		border-color: #dc2626;
		animation: blink-border 0.5s ease-in-out infinite;
	}

	@keyframes blink-border {
		0%,100% { opacity: 1; }
		50%     { opacity: 0.6; }
	}

	.timer-icon { font-size: 1.1rem; }

	.timer-value {
		font-size: 1.4rem;
		font-weight: 700;
		color: #16a34a;
		min-width: 55px;
		text-align: center;
	}

	.timer-display.urgent .timer-value { color: #dc2626; }

	.help-btn-sm {
		width: 34px;
		height: 34px;
		border-radius: 50%;
		border: 2px solid #667eea;
		background: white;
		color: #667eea;
		font-weight: 700;
		font-size: 0.95rem;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.reference-key {
		background: #f8fafc;
		border-radius: 10px;
		padding: 0.75rem 1rem;
		margin-bottom: 1.5rem;
	}

	.key-label {
		font-size: 0.78rem;
		font-weight: 600;
		color: #64748b;
		margin-bottom: 0.5rem;
	}

	.key-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(70px, 1fr));
		gap: 0.4rem;
	}

	.key-item {
		background: white;
		border: 1px solid #e2e8f0;
		border-radius: 8px;
		padding: 0.4rem 0.5rem;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.25rem;
	}

	.ref-symbol { font-size: 1.2rem; color: #667eea; font-weight: bold; }
	.ref-arrow  { font-size: 0.7rem; color: #94a3b8; }
	.ref-digit  { font-size: 1rem; color: #16a34a; font-weight: 700; }

	.test-area { text-align: center; padding: 1.5rem 0; }

	.task-prompt {
		font-size: 0.95rem;
		color: #64748b;
		margin-bottom: 0.5rem;
	}

	.current-symbol {
		font-size: 7rem;
		font-weight: bold;
		color: #667eea;
		margin: 1rem 0 1.5rem;
		text-shadow: 1px 1px 4px rgba(0,0,0,0.08);
		animation: pop-in 0.2s ease-out;
	}

	@keyframes pop-in {
		0%  { transform: scale(0.75); opacity: 0; }
		100%{ transform: scale(1); opacity: 1; }
	}

	.digit-buttons {
		display: flex;
		gap: 0.65rem;
		justify-content: center;
		flex-wrap: wrap;
		max-width: 600px;
		margin: 0 auto;
	}

	.digit-btn {
		width: 66px;
		height: 66px;
		border: 2.5px solid #667eea;
		background: white;
		border-radius: 12px;
		font-size: 1.8rem;
		font-weight: 700;
		color: #667eea;
		cursor: pointer;
		transition: all 0.15s;
	}

	.digit-btn:hover {
		background: #667eea;
		color: white;
		transform: scale(1.07);
	}

	.digit-btn:active { transform: scale(0.96); }

	.progress-bar {
		height: 7px;
		background: #e2e8f0;
		border-radius: 10px;
		overflow: hidden;
		margin-top: 1.5rem;
	}

	.progress-fill {
		height: 100%;
		background: #4338ca;
		transition: width 0.3s ease;
		border-radius: 10px;
	}

	/* ── Complete Screen ── */
	.complete-screen { text-align: center; }

	.complete-screen h1 {
		font-size: 1.8rem;
		font-weight: 700;
		color: #1e293b;
		margin-bottom: 1.25rem;
	}

	.perf-banner {
		border: 3px solid var(--perf-color, #667eea);
		border-radius: 14px;
		padding: 1rem 2.5rem;
		display: inline-block;
		margin-bottom: 1.75rem;
	}

	.perf-label {
		font-size: 1.7rem;
		font-weight: 700;
		color: var(--perf-color, #667eea);
	}

	.perf-score {
		font-size: 1.1rem;
		color: #475569;
		margin-top: 0.2rem;
	}

	.metrics-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
		gap: 0.75rem;
		margin-bottom: 1.5rem;
	}

	.metric-card {
		background: #f8fafc;
		border-radius: 12px;
		padding: 1.25rem;
		border: 1px solid #e2e8f0;
	}

	.metric-card.highlight {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
	}

	.metric-icon { font-size: 1.5rem; margin-bottom: 0.35rem; }

	.metric-value {
		font-size: 2rem;
		font-weight: 700;
		color: #1e293b;
		margin-bottom: 0.25rem;
	}

	.metric-card.highlight .metric-value { color: white; }

	.metric-label {
		font-size: 0.85rem;
		color: #64748b;
		font-weight: 600;
	}

	.metric-card.highlight .metric-label { color: rgba(255,255,255,0.9); }

	.metric-sub {
		font-size: 0.78rem;
		color: #94a3b8;
		margin-top: 0.15rem;
	}

	.metric-card.highlight .metric-sub { color: rgba(255,255,255,0.7); }

	.breakdown {
		background: #f8fafc;
		border-radius: 12px;
		padding: 1.25rem;
		text-align: left;
		margin-bottom: 1rem;
	}

	.breakdown h3 {
		font-size: 0.9rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 0.75rem;
	}

	.breakdown-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.5rem 0;
		border-bottom: 1px solid #e2e8f0;
		font-size: 0.88rem;
	}

	.breakdown-row:last-child { border-bottom: none; }

	.clinical-note {
		background: linear-gradient(135deg, rgba(102,126,234,0.08) 0%, rgba(118,75,162,0.08) 100%);
		border: 1px solid rgba(102,126,234,0.2);
		border-radius: 12px;
		padding: 1.25rem 1.5rem;
		text-align: left;
		margin-bottom: 1rem;
	}

	.clinical-note h3 {
		font-size: 0.9rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 0.5rem;
	}

	.clinical-note p {
		font-size: 0.88rem;
		color: #374151;
		margin: 0;
		line-height: 1.6;
	}

	.difficulty-info {
		background: #eff6ff;
		border-radius: 10px;
		padding: 1rem 1.25rem;
		margin-bottom: 1.25rem;
		font-size: 0.9rem;
		color: #1e40af;
	}

	.difficulty-info p { margin: 0 0 0.25rem; }
	.adapt-reason { color: #64748b !important; font-size: 0.82rem; }

	.start-button {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		padding: 0.8rem 2rem;
		border: none;
		border-radius: 10px;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
	}

	.start-button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(102,126,234,0.4); }

	.btn-secondary {
		background: white;
		color: #667eea;
		padding: 0.8rem 2rem;
		border: 2px solid #667eea;
		border-radius: 10px;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
	}

	.btn-secondary:hover { background: #667eea; color: white; }

	/* ── Help Modal ── */
	.modal-overlay {
		position: fixed;
		inset: 0;
		background: rgba(0,0,0,0.55);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
	}

	.modal-content {
		background: white;
		padding: 2rem;
		border-radius: 16px;
		max-width: 580px;
		width: 90%;
		max-height: 80vh;
		overflow-y: auto;
		position: relative;
	}

	.modal-content h2 {
		font-size: 1.3rem;
		color: #1e293b;
		margin-bottom: 1.25rem;
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
		font-size: 1.3rem;
		border-radius: 50%;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.strategy {
		margin-bottom: 1rem;
		padding: 0.9rem 1rem;
		background: #f8fafc;
		border-radius: 8px;
		border-left: 4px solid #667eea;
	}

	.strategy h3 {
		font-size: 0.9rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 0.35rem;
	}

	.strategy p {
		font-size: 0.85rem;
		color: #374151;
		margin: 0;
		line-height: 1.55;
	}

	/* ── Responsive ── */
	@media (max-width: 600px) {
		.rules-grid,
		.info-grid,
		.clinical-grid { grid-template-columns: 1fr; }
		.key-display { grid-template-columns: repeat(3, 1fr); }
		.metrics-grid { grid-template-columns: 1fr 1fr; }
	}
</style>

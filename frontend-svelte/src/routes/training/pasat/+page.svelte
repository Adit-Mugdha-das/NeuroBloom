<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
	import {
	  formatNumber,
	  formatPercent,
	  locale,
	  localeText,
	  localizeDigitInput,
	  normalizeLocalizedDigits,
	  translateText
	} from '$lib/i18n';
	import { getTaskDifficultyDescription } from '$lib/i18n/task-ui.js';
	import { user } from '$lib/stores.js';
	import { getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
	import { onMount } from 'svelte';

	const API_BASE_URL = 'http://127.0.0.1:8000';

	let currentUser = null;
	let sessionData = null;
	let currentTrialIndex = 0;
	let currentDigit = null;
	let previousDigit = null;
	let responses = [];
	let taskId = null;
	
	// UI states
	let showInstructions = true;
	let showPractice = false;
	let practiceComplete = false;
	let testStarted = false;
	let waitingForAnswer = false;
	let showResults = false;
	let error = null;
	let loading = false;
	
	// User input
	let userAnswer = '';
	let trialStartTime = 0;
	
	// Practice
	let practiceDigits = [3, 5, 2, 7];
	let practiceIndex = 0;
	let practicePrevious = null;
	
	// Results
	let results = null;
	
	// Help modal
	let showHelp = false;
	/** @type {"practice" | "recorded"} */
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';
	
	// Timer for digit presentation
	let digitTimer = null;

	// Subscribe to user store
	user.subscribe(value => {
		currentUser = value;
	});

	function t(text) {
		return translateText(text ?? '', $locale);
	}

	function lt(englishText, banglaText) {
		return localeText({ en: englishText, bn: banglaText }, $locale);
	}

	function n(value, options = {}) {
		return formatNumber(value, $locale, options);
	}

	function pct(value, options = {}) {
		return formatPercent(value, $locale, {
			minimumFractionDigits: 0,
			maximumFractionDigits: 1,
			...options
		});
	}

	function digitsLabel(count) {
		return $locale === 'bn' ? `${n(count)}টি অঙ্ক` : `${count} digits`;
	}

	function secondsLabel(value) {
		return $locale === 'bn' ? `${n(value)} সেকেন্ড` : `${value} seconds`;
	}

	function intervalLabel(value) {
		return $locale === 'bn' ? `${n(value)} সেকেন্ড পরপর` : `${value}s intervals`;
	}

	function actualTestButtonLabel(total) {
		return $locale === 'bn'
			? `আসল পরীক্ষা শুরু করুন (${digitsLabel(total)})`
			: `Start Actual Test (${total} digits)`;
	}

	function millisecondsLabel(value) {
		return $locale === 'bn' ? `${n(value)} মি.সে.` : `${value}ms`;
	}

	function localizedDigit(value) {
		return n(value);
	}

	function numericFieldValue(value) {
		return localizeDigitInput(value, $locale);
	}

	function performanceLevelLabel(value) {
		return t(value);
	}

	function currentPaceDescription() {
		const fallbackDescription = sessionData?.config?.description || 'Standard PASAT-3';
		return getTaskDifficultyDescription('pasat', sessionData?.difficulty, $locale, t(fallbackDescription));
	}

	function paceChangeLabel(type, before, after) {
		if ($locale === 'bn') {
			if (type === 'increase') {
				return `পরের সেশনে গতি বাড়বে: ${n(before)} → ${n(after)}`;
			}

			if (type === 'decrease') {
				return `পরের সেশনে গতি কমবে: ${n(before)} → ${n(after)}`;
			}

			return `পরের সেশন ${n(after)} লেভেলেই থাকবে`;
		}

		if (type === 'increase') {
			return `Pace increased: ${before} → ${after}`;
		}

		if (type === 'decrease') {
			return `Pace slowed: ${before} → ${after}`;
		}

		return `Pace maintained at level ${after}`;
	}

	function interpretationText() {
		if (!results?.metrics) return '';

		if ($locale === 'bn') {
			if (results.metrics.accuracy >= 85) {
				return `অসাধারণ টেকসই মনোযোগ! আপনি ${secondsLabel(results.metrics.interval_seconds)} গতিতেও মনোযোগ ও নির্ভুলতা ধরে রাখতে পেরেছেন। এটি শক্তিশালী ওয়ার্কিং মেমোরি ও মনোযোগের সক্ষমতা দেখায়।`;
			}

			if (results.metrics.accuracy >= 70) {
				return 'এই চ্যালেঞ্জিং টাস্কে আপনার পারফরম্যান্স ভালো। সময়ের চাপের মধ্যেও আপনি মনোযোগ ধরে রাখতে পারছেন। নিয়মিত অনুশীলনে টেকসই মনোযোগ আরও উন্নত হবে।';
			}

			if (results.metrics.accuracy >= 55) {
				return 'পারফরম্যান্স মোটামুটি। PASAT সবচেয়ে কঠিন কগনিটিভ পরীক্ষাগুলোর একটি। আপনার মনোযোগ ও ওয়ার্কিং মেমোরি কাজ করছে, তবে নিয়মিত অনুশীলনে আরও উন্নতি সম্ভব।';
			}

			return 'PASAT বিশেষ করে দ্রুত গতিতে খুবই কঠিন। আপনার মস্তিষ্ক মনোযোগ ধরে রাখা ও মানসিক হিসাব একসঙ্গে করার চেষ্টা করছে। নিয়মিত অনুশীলনে এই ক্ষমতা আরও বাড়বে।';
		}

		if (results.metrics.accuracy >= 85) {
			return `Excellent sustained attention! You maintained focus and accuracy at a ${results.metrics.interval_seconds}s pace. This indicates strong working memory and attention capacity.`;
		}

		if (results.metrics.accuracy >= 70) {
			return "Good performance on this challenging task. You're maintaining attention well under time pressure. Continued practice will further improve your sustained attention.";
		}

		if (results.metrics.accuracy >= 55) {
			return 'Fair performance. PASAT is one of the most demanding cognitive tests. Your attention and working memory are functioning, with room for improvement through regular practice.';
		}

		return 'PASAT is extremely challenging, especially at faster paces. Your brain is working hard to maintain attention and perform mental calculations. Regular practice will help build sustained attention capacity.';
	}

	onMount(async () => {
		if (!currentUser) {
			goto('/login');
			return;
		}
		
		await loadSession();
	});

	async function loadSession() {
		try {
			loading = true;
			error = null;
			
			const response = await fetch(`${API_BASE_URL}/api/training/tasks/pasat/generate/${currentUser.id}?visual_mode=true`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				}
			});
			
			if (!response.ok) {
				throw new Error('Failed to load session');
			}
			
			const data = await response.json();
			sessionData = data.session_data;
			
		} catch (err) {
			error = err.message;
		} finally {
			loading = false;
		}
	}

	function startPractice() {
		playMode = TASK_PLAY_MODE.PRACTICE;
		practiceStatusMessage = '';
		showInstructions = false;
		showPractice = true;
		practiceIndex = 0;
		practicePrevious = null;
		
		runPracticeTrial();
	}

	function finishPractice() {
		playMode = TASK_PLAY_MODE.RECORDED;
		showPractice = false;
		practiceComplete = false;
		waitingForAnswer = false;
		currentDigit = null;
		userAnswer = '';
		showInstructions = true;
		practiceStatusMessage = getPracticeCopy($locale).complete;
	}

	async function runPracticeTrial() {
		if (practiceIndex >= practiceDigits.length) {
			finishPractice();
			return;
		}
		
		const digit = practiceDigits[practiceIndex];
		
		// Show digit
		currentDigit = digit;
		userAnswer = '';
		
		// First digit - no answer needed
		if (practiceIndex === 0) {
			practicePrevious = digit;
			await sleep(2000);
			practiceIndex++;
			runPracticeTrial();
			return;
		}
		
		// Subsequent digits - need answer
		waitingForAnswer = true;
		trialStartTime = performance.now();
	}

	function handlePracticeAnswer() {
		if (!waitingForAnswer || userAnswer === '') return;

		const correctAnswer = practicePrevious + currentDigit;
		const isCorrect = parseInt(userAnswer) === correctAnswer;
		
		waitingForAnswer = false;
		
		if (isCorrect) {
			// Correct! Move to next
			practicePrevious = currentDigit;
			practiceIndex++;
			userAnswer = '';
			
			setTimeout(() => runPracticeTrial(), 800);
		} else {
			// Wrong, show feedback
			alert(`The correct answer was ${correctAnswer} (${practicePrevious} + ${currentDigit}). Try again!`);
			userAnswer = '';
			waitingForAnswer = true;
		}
	}

	function startTest() {
		playMode = TASK_PLAY_MODE.RECORDED;
		practiceStatusMessage = '';
		showPractice = false;
		practiceComplete = false;
		testStarted = true;
		currentTrialIndex = 0;
		responses = [];
		previousDigit = null;
		
		runNextTrial();
	}

	async function runNextTrial() {
		if (currentTrialIndex >= sessionData.total_trials) {
			await submitResults();
			return;
		}
		
		const trial = sessionData.trials[currentTrialIndex];
		currentDigit = trial.digit;
		userAnswer = '';
		
		// First digit - no answer needed
		if (trial.is_first) {
			previousDigit = currentDigit;
			currentTrialIndex++;
			
			// Wait for interval then show next digit
			digitTimer = setTimeout(() => runNextTrial(), sessionData.interval_seconds * 1000);
			return;
		}
		
		// Subsequent digits - need answer
		waitingForAnswer = true;
		trialStartTime = performance.now();
		
		// Auto-advance after interval
		digitTimer = setTimeout(() => {
			handleAutoAdvance();
		}, sessionData.interval_seconds * 1000);
	}

	function handleAnswerSubmit() {
		if (!waitingForAnswer) return;
		
		clearTimeout(digitTimer);
		
		const reactionTime = performance.now() - trialStartTime;
		const answer = userAnswer !== '' ? parseInt(userAnswer) : null;
		
		responses.push({
			trial_index: currentTrialIndex,
			user_answer: answer,
			reaction_time: reactionTime
		});
		
		waitingForAnswer = false;
		previousDigit = currentDigit;
		currentTrialIndex++;
		
		// Small delay before next digit
		setTimeout(() => runNextTrial(), 200);
	}

	function handleAutoAdvance() {
		if (!waitingForAnswer) return;
		
		const reactionTime = performance.now() - trialStartTime;
		
		// No answer given - record as null
		responses.push({
			trial_index: currentTrialIndex,
			user_answer: null,
			reaction_time: reactionTime
		});
		
		waitingForAnswer = false;
		previousDigit = currentDigit;
		currentTrialIndex++;
		
		runNextTrial();
	}

	function handleKeyPress(event) {
		if (event.key === 'Enter') {
			if (showPractice && waitingForAnswer) {
				handlePracticeAnswer();
			} else if (testStarted && waitingForAnswer) {
				handleAnswerSubmit();
			}
		}
	}

	async function submitResults() {
		try {
			loading = true;
			testStarted = false;
			taskId = $page.url.searchParams.get('taskId');
			
			const response = await fetch(`${API_BASE_URL}/api/training/tasks/pasat/submit/${currentUser.id}`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					difficulty: sessionData.difficulty,
					session_data: sessionData,
					responses: responses,
					task_id: taskId
				})
			});
			
			if (!response.ok) {
				throw new Error('Failed to submit results');
			}
			
			results = await response.json();
			showResults = true;
			
		} catch (err) {
			error = err.message;
		} finally {
			loading = false;
		}
	}

	function sleep(ms) {
		return new Promise(resolve => setTimeout(resolve, ms));
	}

	function returnToDashboard() {
		goto('/dashboard');
	}

	// Input validation - only allow numeric characters
	function validateNumericInput(event) {
		const nextValue = normalizeLocalizedDigits(event.currentTarget.value).replace(/[^0-9]/g, '');
		userAnswer = nextValue;
		event.currentTarget.value = numericFieldValue(nextValue);
	}

	// Reactive calculations
	$: trialsRemaining = sessionData ? sessionData.total_trials - currentTrialIndex : 0;
	$: progressPercent = sessionData ? (currentTrialIndex / sessionData.total_trials * 100) : 0;
</script>

<svelte:head>
	<title>{lt('PASAT - NeuroBloom', 'পাসাট - NeuroBloom')}</title>
</svelte:head>

<svelte:window on:keypress={handleKeyPress} />

<div class="pasat-container" data-localize-skip>
	<div class="pasat-inner">
		{#if loading}
			<LoadingSkeleton variant="card" count={3} />

		{:else if error}
			<div class="screen-card error-screen">
				<h2>⚠️ {t('Error')}</h2>
				<p>{t(error)}</p>
				<button class="start-button" on:click={returnToDashboard}>{t('Return to Dashboard')}</button>
			</div>

		{:else if showInstructions}
			<div class="instructions-card">
				<div class="header-content">
					<div class="title-row">
						<h1>🎯 {t('PASAT')}</h1>
						<DifficultyBadge difficulty={sessionData?.difficulty || 5} domain="Attention" />
					</div>
					<p class="subtitle">{t('Paced Auditory Serial Addition Test · MS Gold Standard')}</p>
					<div class="gold-badge">⭐⭐⭐⭐⭐ {t('CLINICAL GOLD STANDARD FOR MS')}</div>
				</div>

				{#if practiceStatusMessage}
					<div class="practice-note">{practiceStatusMessage}</div>
				{/if}

				<div class="task-concept">
					<h3>🔢 {t('The Golden Rule')}</h3>
					<p>{t('Add each NEW digit to the PREVIOUS digit — not to your running total. This is the key rule!')}</p>
					<div class="pasat-example">
						<div class="ex-step ex-first">
							<div class="ex-digit">{localizedDigit(3)}</div>
							<div class="ex-hint">{t('Remember it')}</div>
						</div>
						<div class="ex-arrow">→</div>
						<div class="ex-step">
							<div class="ex-digit">{localizedDigit(5)}</div>
							<div class="ex-hint">{t('Answer')}: <strong>{localizedDigit(8)}</strong></div>
							<div class="ex-sub">{localizedDigit(3)}+{localizedDigit(5)}</div>
						</div>
						<div class="ex-arrow">→</div>
						<div class="ex-step">
							<div class="ex-digit">{localizedDigit(2)}</div>
							<div class="ex-hint">{t('Answer')}: <strong>{localizedDigit(7)}</strong></div>
							<div class="ex-sub">{localizedDigit(5)}+{localizedDigit(2)}</div>
						</div>
						<div class="ex-arrow">→</div>
						<div class="ex-step">
							<div class="ex-digit">{localizedDigit(9)}</div>
							<div class="ex-hint">{t('Answer')}: <strong>{localizedDigit(11)}</strong></div>
							<div class="ex-sub">{localizedDigit(2)}+{localizedDigit(9)}</div>
						</div>
					</div>
					<div class="key-rule-box">
						<strong>⚠️ {t('KEY RULE:')}</strong> {t('Always add to the PREVIOUS digit you saw — not your last answer!')}
					</div>
				</div>

				<div class="rules-grid">
					<div class="rule-card">
						<span class="rule-icon">👁️</span>
						<div class="rule-text">
							<strong>{t('Step 1: See the Digit')}</strong>
							<span>{t('A digit (1–9) appears on screen')}</span>
						</div>
					</div>
					<div class="rule-card">
						<span class="rule-icon">➕</span>
						<div class="rule-text">
							<strong>{t('Step 2: Add to Previous')}</strong>
							<span>{t('Add it to the digit you just saw (not your last answer!)')}</span>
						</div>
					</div>
					<div class="rule-card">
						<span class="rule-icon">⌨️</span>
						<div class="rule-text">
							<strong>{t('Step 3: Type Your Sum')}</strong>
							<span>{t('Enter the answer and press Enter quickly')}</span>
						</div>
					</div>
					<div class="rule-card">
						<span class="rule-icon">⏱️</span>
						<div class="rule-text">
							<strong>{t('Step 4: Keep Pace')}</strong>
							<span>
								{$locale === 'bn'
									? `প্রতি ${secondsLabel(sessionData?.config?.interval_seconds || 3)} পরপর নতুন অঙ্ক আসবে`
									: `New digit every ${sessionData?.config?.interval_seconds || 3} seconds`}
							</span>
						</div>
					</div>
				</div>

				<div class="info-grid">
					<div class="info-section">
						<h4>💡 {t('Tips for Success')}</h4>
						<ul class="tips-list">
							<li><strong>{t('Forget your answer:')}</strong> {t('only remember the digit you just saw')}</li>
							<li><strong>{t("Don't keep a total:")}</strong> {t("that's not the task!")}</li>
							<li><strong>{t('If you miss one:')}</strong> {t('reset with the next digit')}</li>
							<li><strong>{t('Stay calm:')}</strong> {t('even healthy adults find this hard')}</li>
						</ul>
					</div>
					<div class="info-section">
						<h4>📋 {t('Test Format')}</h4>
						<ul class="structure-list">
							<li>
								<span class="struct-key">{t('Digits')}</span>
								<span class="struct-val">{n(sessionData?.total_trials || 60)}</span>
							</li>
							<li>
								<span class="struct-key">{t('Pace')}</span>
								<span class="struct-val">{intervalLabel(sessionData?.config?.interval_seconds || 3)}</span>
							</li>
							<li>
								<span class="struct-key">{t('Version')}</span>
								<span class="struct-val">{currentPaceDescription()}</span>
							</li>
							<li>
								<span class="struct-key">{t('Input')}</span>
								<span class="struct-val">{t('Keyboard / number pad')}</span>
							</li>
						</ul>
					</div>
				</div>

				<div class="clinical-info">
					<h4>🏥 {t('Clinical Significance')}</h4>
					<div class="clinical-grid">
						<div class="clinical-item">
							<strong>{t('MS Gold Standard')}</strong>
							<span>{t('Most widely used MS cognitive test in clinical trials')}</span>
						</div>
						<div class="clinical-item">
							<strong>{t('Sustained Attention')}</strong>
							<span>{t('Tracks attention maintenance over the whole session')}</span>
						</div>
						<div class="clinical-item">
							<strong>{t('Lesion Correlation')}</strong>
							<span>{t('Performance correlates with brain lesion burden')}</span>
						</div>
						<div class="clinical-item">
							<strong>{t('Gronwall, 1977')}</strong>
							<span>{t('Extensively validated in MS populations worldwide')}</span>
						</div>
					</div>
				</div>

				<div class="perf-guide">
					<h4>📊 {t('Performance Reference')}</h4>
					<div class="norm-bars">
						<div class="norm-bar norm-excellent">
							<span class="norm-label">{t('Excellent')}</span>
							<span class="norm-val">≥85% {t('accuracy')}</span>
						</div>
						<div class="norm-bar norm-good">
							<span class="norm-label">{t('Good')}</span>
							<span class="norm-val">70–84%</span>
						</div>
						<div class="norm-bar norm-avg">
							<span class="norm-label">{t('Average')}</span>
							<span class="norm-val">55–69%</span>
						</div>
						<div class="norm-bar norm-fair">
							<span class="norm-label">{t('Fair')}</span>
							<span class="norm-val">40–54%</span>
						</div>
						<div class="norm-bar norm-needs">
							<span class="norm-label">{t('Developing')}</span>
							<span class="norm-val">&lt;40%</span>
						</div>
					</div>
					<p class="norm-note">*{t('Scores depend on pace — faster intervals = harder task')}</p>
				</div>

				<div class="button-group">
					<button class="btn-secondary" on:click={startPractice}>✏️ {t('Try Practice (4 digits)')}</button>
					<TaskPracticeActions
						locale={$locale}
						startLabel={actualTestButtonLabel(sessionData?.total_trials)}
						practiceVisible={false}
						statusMessage={practiceStatusMessage}
						align="center"
						on:start={startTest}
					/>
					<button class="help-link" on:click={() => showHelp = true}>📖 {t('More Information')}</button>
				</div>
			</div>

		{:else if showPractice}
			<div class="screen-card practice-screen">
				<PracticeModeBanner locale={$locale} />
				<h2>✏️ {t('Practice Mode')}</h2>
				<p class="practice-intro">{t("Let's practice with 4 digits. Take your time to understand the pattern.")}</p>

				{#if !practiceComplete}
					<div class="digit-display-area">
						<div class="big-digit-card">
							<div class="big-digit">{localizedDigit(currentDigit)}</div>
						</div>
						<div class="digit-hint">
							{#if practiceIndex === 0}
								<span class="hint-chip hint-first">💡 {t('First digit — just remember it!')}</span>
							{:else if practiceIndex === 1}
								<span class="hint-chip">
									{$locale === 'bn'
										? `${localizedDigit(practicePrevious)} + ${localizedDigit(currentDigit)} = ?`
										: `${practicePrevious} + ${currentDigit} = ?`}
								</span>
							{:else}
								<span class="hint-chip">{t('Add to the previous digit you saw')}</span>
							{/if}
						</div>
					</div>

					{#if waitingForAnswer}
						<div class="answer-area">
							<input
								type="text"
								inputmode="numeric"
								pattern="[0-9]*"
								value={numericFieldValue(userAnswer)}
								on:input={validateNumericInput}
								placeholder={t('Type your answer')}
								class="answer-input"
							/>
							<button class="start-button" on:click={handlePracticeAnswer}>
								{t('Submit Answer')}
							</button>
						</div>
					{/if}
				{:else}
					<div class="complete-msg">
						<div class="complete-icon">✅</div>
						<h3>{t('Practice Complete!')}</h3>
						<p>
							{$locale === 'bn'
								? `দারুণ! এখন আপনি টাস্কটি বুঝে গেছেন। আসল পরীক্ষায় ${digitsLabel(sessionData.total_trials)} থাকবে।`
								: `Great! Now you understand the task. The real test will have ${sessionData.total_trials} digits.`}
						</p>
						<p class="complete-rule"><strong>{t('Remember:')}</strong> {t('Add to the PREVIOUS digit — not to your running total!')}</p>
						<button class="start-button" on:click={startTest}>
							{actualTestButtonLabel(sessionData.total_trials)}
						</button>
					</div>
				{/if}
			</div>

		{:else if testStarted}
			<div class="screen-card testing-screen">
				<div class="test-header">
					<div class="test-badges">
						<span class="count-badge">
							{$locale === 'bn'
								? `${n(trialsRemaining)} অঙ্ক বাকি`
								: `${trialsRemaining} digits left`}
						</span>
						<span class="pace-badge">⏱️ {intervalLabel(sessionData.interval_seconds)}</span>
					</div>
					<div class="progress-track">
						<div class="progress-fill" style="width: {progressPercent}%"></div>
					</div>
					<button class="help-btn-sm" on:click={() => showHelp = true}>?</button>
				</div>

				<div class="digit-display-area">
					<div class="big-digit-card">
						<div class="big-digit">{localizedDigit(currentDigit)}</div>
					</div>
				</div>

				{#if waitingForAnswer}
					<div class="answer-area">
						<p class="answer-prompt">{t('Add to previous — type your sum:')}</p>
						<input
							type="text"
							inputmode="numeric"
							pattern="[0-9]*"
							value={numericFieldValue(userAnswer)}
							on:input={validateNumericInput}
							placeholder={t('Enter sum')}
							class="answer-input large"
						/>
						<button class="start-button" on:click={handleAnswerSubmit}>
							{t('Submit (Enter)')}
						</button>
					</div>
				{:else if currentTrialIndex > 0 && currentTrialIndex < sessionData.total_trials}
					<div class="waiting-state">
						<p>{t('Next digit coming…')}</p>
					</div>
				{/if}
			</div>

		{:else if showResults}
			<div class="screen-card complete-screen">
				{#if results}
					<div class="perf-banner">
						<div class="perf-emoji">🎉</div>
						<div class="perf-level">{t(results.metrics.performance_level)}</div>
						<div class="perf-subtitle">{pct(results.metrics.accuracy, { maximumFractionDigits: 0 })} {t('accuracy')} · PASAT {t('Complete')}!</div>
					</div>

					<div class="metrics-grid">
						<div class="metric-card highlight">
							<div class="metric-icon">🎯</div>
							<div class="metric-value">{pct(results.metrics.accuracy, { maximumFractionDigits: 0 })}</div>
							<div class="metric-label">{t('Accuracy')}</div>
							<div class="metric-sub">
								{$locale === 'bn'
									? `${n(results.metrics.correct_count)}/${n(results.metrics.total_trials)} সঠিক`
									: `${results.metrics.correct_count}/${results.metrics.total_trials} correct`}
							</div>
						</div>
						<div class="metric-card">
							<div class="metric-icon">⚡</div>
							<div class="metric-value">{pct(results.metrics.sustained_attention, { maximumFractionDigits: 0 })}</div>
							<div class="metric-label">{t('Sustained Attention')}</div>
							<div class="metric-sub">{t('Performance in final third')}</div>
						</div>
						<div class="metric-card">
							<div class="metric-icon">⏱️</div>
							<div class="metric-value">{millisecondsLabel(results.metrics.average_reaction_time)}</div>
							<div class="metric-label">{t('Avg Response Time')}</div>
							<div class="metric-sub">{t('per digit')}</div>
						</div>
						<div class="metric-card">
							<div class="metric-icon">📈</div>
							<div class="metric-value">{pct(results.metrics.consistency, { maximumFractionDigits: 0 })}</div>
							<div class="metric-label">{t('Consistency')}</div>
							<div class="metric-sub">{t('Response stability')}</div>
						</div>
					</div>

					<div class="breakdown">
						<h3>{t('Detailed Analysis')}</h3>
						<div class="breakdown-row">
							<span class="bd-label">{t('Total Digits')}</span>
							<span class="bd-val">{n(results.metrics.total_trials)}</span>
						</div>
						<div class="breakdown-row">
							<span class="bd-label">{t('Correct Answers')}</span>
							<span class="bd-val bd-success">{n(results.metrics.correct_count)}</span>
						</div>
						<div class="breakdown-row">
							<span class="bd-label">{t('Pace')}</span>
							<span class="bd-val">{intervalLabel(results.metrics.interval_seconds)}</span>
						</div>
						<div class="breakdown-row">
							<span class="bd-label">{t('Sustained Attention')}</span>
							<span class="bd-val">{pct(results.metrics.sustained_attention, { maximumFractionDigits: 0 })}</span>
						</div>
						{#if results.metrics.fatigue_effect > 0}
							<div class="breakdown-row">
								<span class="bd-label">{t('Fatigue Effect')}</span>
								<span class="bd-val" class:bd-warning={results.metrics.fatigue_effect > 15}>
									{results.metrics.fatigue_effect.toFixed(1)}%
								</span>
							</div>
						{/if}
						<div class="breakdown-row">
							<span class="bd-label">{t('Performance Level')}</span>
							<span class="bd-val">{t(results.metrics.performance_level)}</span>
						</div>
					</div>

					{#if results.metrics.fatigue_effect > 15}
						<div class="fatigue-notice">
							<h4>⚠️ {t('Cognitive Fatigue Detected')}</h4>
							<p>
								{$locale === 'bn'
									? `শুরু থেকে শেষ পর্যন্ত পারফরম্যান্স ${pct(results.metrics.fatigue_effect)} কমেছে। এটি PASAT-এ স্বাভাবিক।`
									: `Your performance decreased ${results.metrics.fatigue_effect.toFixed(1)}% from start to finish — normal for a demanding task like PASAT. Consider taking breaks between sessions.`}
							</p>
						</div>
					{/if}

					<div class="clinical-note">
						<h4>🧠 {t('Clinical Context')}</h4>
						<p>{interpretationText()}</p>
						<p class="why-matters"><strong>{t('Why this matters for MS:')}</strong> {t('PASAT scores correlate with brain lesion burden and predict real-world cognitive functioning. It is included in MACFIMS and BRB-N — the two main MS cognitive batteries.')}</p>
					</div>

					{#if results.adaptation_reason}
						<div class="difficulty-info">
							<span>{t('Pace')}: <strong>{n(results.difficulty_before)}</strong> → <strong>{n(results.difficulty_after)}</strong></span>
							<span class="adapt-reason">{t(results.adaptation_reason)}</span>
						</div>
					{/if}

					{#if results.new_badges && results.new_badges.length > 0}
						<BadgeNotification badges={results.new_badges} />
					{/if}

					<div class="button-group">
						<button class="start-button" on:click={returnToDashboard}>{t('Return to Dashboard')}</button>
						<button class="btn-secondary" on:click={() => goto('/training')}>{t('Back to Training')}</button>
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>

{#if showHelp}
	<div class="modal-overlay" on:click={() => showHelp = false} role="presentation">
		<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
		<div class="modal-content" on:click|stopPropagation role="dialog" tabindex="-1" on:keydown={(e) => e.key === 'Escape' && (showHelp = false)}>
			<button class="close-btn" on:click={() => showHelp = false}>×</button>
			<h2>{t('PASAT — Strategies & Information')}</h2>
			<div class="strategy">
				<h3>🔑 {t('Forget Your Answer')}</h3>
				<p>{t('After you submit, immediately forget your answer. The only thing that matters is the digit you currently see — it becomes the new "previous" for the next addition.')}</p>
			</div>
			<div class="strategy">
				<h3>🚫 {t("Don't Keep a Running Total")}</h3>
				<p>{t('It\'s tempting to track a cumulative sum but that\'s NOT the task. Each answer is only the sum of the last two digits shown.')}</p>
			</div>
			<div class="strategy">
				<h3>😌 {t('Reset After Errors')}</h3>
				<p>{t('If you lose track, skip one answer and restart with the next digit. Missing a few is better than losing track completely.')}</p>
			</div>
			<div class="strategy">
				<h3>👁️ {t('Visualize Two Numbers')}</h3>
				<p>{t('Picture the two digits floating side by side. Some people find it helps to hold the previous digit mentally as an image, not a word.')}</p>
			</div>
			<div class="strategy">
				<h3>📚 {t('PASAT Variants')}</h3>
				<p>
					<strong>PASAT-4:</strong> {t('4-second intervals (easier)')} ·
					<strong>PASAT-3:</strong> {t('3-second intervals (standard)')} ·
					<strong>PASAT-2:</strong> {t('2-second intervals (very hard)')}
				</p>
			</div>
			<div class="strategy">
				<h3>💪 {t('Why This Matters')}</h3>
				<p>{t('PASAT is included in every major MS cognitive battery (MACFIMS, BRB-N). Improving on it demonstrates real gains in sustained attention — one of the most affected domains in MS.')}</p>
			</div>
		</div>
	</div>
{/if}

<style>
	/* ── Container ─────────────────────────────────────────── */
	.pasat-container {
		min-height: 100vh;
		background: #C8DEFA;
		padding: 2rem 1rem;
	}

	.pasat-inner {
		max-width: 960px;
		margin: 0 auto;
	}

	/* ── Instructions card ─────────────────────────────────── */
	.instructions-card {
		background: white;
		border-radius: 16px;
		padding: 2.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07), 0 1px 3px rgba(0, 0, 0, 0.06);
		display: flex;
		flex-direction: column;
		gap: 1.8rem;
	}

	.header-content { text-align: center; }

	.title-row {
		display: flex; align-items: center; justify-content: center;
		gap: 1rem; flex-wrap: wrap; margin-bottom: 0.5rem;
	}

	.header-content h1 { font-size: 1.8rem; font-weight: 700; color: #1e293b; margin: 0; }

	.subtitle { color: #64748b; font-size: 1rem; margin: 0.4rem 0 0.8rem; }

	.gold-badge {
		display: inline-block;
		background: rgba(234, 88, 12, 0.1);
		color: #ea580c;
		border: 1px solid rgba(234, 88, 12, 0.3);
		border-radius: 20px;
		padding: 0.3rem 1rem;
		font-size: 0.82rem;
		font-weight: 700;
		letter-spacing: 0.03em;
	}

	.practice-note {
		background: #fef9c3; border: 1px solid #fde047;
		border-radius: 8px; padding: 0.75rem 1rem;
		color: #854d0e; font-size: 0.9rem; text-align: center;
	}

	/* ── Task concept (orange for Attention domain) ────────── */
	.task-concept {
		background: linear-gradient(135deg, #fff7ed, #ffedd5);
		border: 1px solid #fed7aa;
		border-radius: 12px;
		padding: 1.5rem;
	}

	.task-concept h3 { font-size: 1rem; font-weight: 700; color: #c2410c; margin: 0 0 0.5rem; }
	.task-concept p  { color: #7c2d12; margin: 0 0 1.2rem; line-height: 1.6; }

	/* PASAT example sequence */
	.pasat-example {
		display: flex; align-items: center; justify-content: center;
		gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1.2rem;
		background: white; border-radius: 10px; padding: 1rem;
		box-shadow: 0 2px 8px rgba(0,0,0,0.06);
	}

	.ex-step {
		display: flex; flex-direction: column; align-items: center; gap: 0.2rem;
		background: #f8fafc; border-radius: 8px; padding: 0.6rem 0.8rem;
		min-width: 70px; text-align: center;
	}

	.ex-digit {
		font-size: 1.8rem; font-weight: 800; color: #ea580c;
		line-height: 1;
	}

	.ex-hint { font-size: 0.78rem; font-weight: 600; color: #475569; }
	.ex-hint strong { color: #16a34a; }
	.ex-sub  { font-size: 0.72rem; color: #94a3b8; }

	.ex-first { border: 2px solid #fed7aa; }

	.ex-arrow { font-size: 1.2rem; color: #94a3b8; font-weight: 700; }

	.key-rule-box {
		background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px;
		padding: 0.75rem 1rem; font-size: 0.88rem; color: #991b1b; line-height: 1.5;
	}

	/* ── Rules grid ────────────────────────────────────────── */
	.rules-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }

	.rule-card {
		display: flex; align-items: flex-start; gap: 0.8rem;
		padding: 1rem; background: #f8fafc; border-radius: 10px;
		border-left: 4px solid #ea580c;
	}

	.rule-icon { font-size: 1.5rem; flex-shrink: 0; }
	.rule-text { display: flex; flex-direction: column; gap: 0.2rem; }
	.rule-text strong { font-size: 0.9rem; color: #1e293b; }
	.rule-text span   { font-size: 0.82rem; color: #64748b; line-height: 1.4; }

	/* ── Info grid ─────────────────────────────────────────── */
	.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }

	.info-section { background: #f8fafc; border-radius: 10px; padding: 1.2rem; }
	.info-section h4 { font-size: 0.9rem; font-weight: 700; color: #1e293b; margin: 0 0 0.8rem; }

	.tips-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 0.5rem; }
	.tips-list li { font-size: 0.85rem; color: #475569; line-height: 1.4; }

	.structure-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 0.5rem; }
	.structure-list li {
		display: flex; justify-content: space-between; align-items: center;
		font-size: 0.85rem; padding: 0.3rem 0; border-bottom: 1px solid #e2e8f0;
	}
	.structure-list li:last-child { border-bottom: none; }
	.struct-key { color: #64748b; }
	.struct-val { font-weight: 600; color: #1e293b; }

	/* ── Clinical info ─────────────────────────────────────── */
	.clinical-info {
		background: linear-gradient(135deg, #f0fdf4, #dcfce7);
		border: 1px solid #bbf7d0; border-radius: 12px; padding: 1.2rem;
	}
	.clinical-info h4 { font-size: 0.9rem; font-weight: 700; color: #166534; margin: 0 0 0.8rem; }
	.clinical-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
	.clinical-item { display: flex; flex-direction: column; gap: 0.2rem; }
	.clinical-item strong { font-size: 0.82rem; color: #166534; }
	.clinical-item span   { font-size: 0.8rem; color: #15803d; }

	/* ── Performance guide ─────────────────────────────────── */
	.perf-guide { background: #f8fafc; border-radius: 12px; padding: 1.2rem; }
	.perf-guide h4 { font-size: 0.9rem; font-weight: 700; color: #1e293b; margin: 0 0 0.8rem; }
	.norm-bars { display: flex; flex-direction: column; gap: 0.4rem; }
	.norm-bar {
		display: flex; justify-content: space-between; align-items: center;
		padding: 0.5rem 0.9rem; border-radius: 6px; font-size: 0.85rem; font-weight: 600;
	}
	.norm-excellent { background: #dcfce7; color: #166534; }
	.norm-good      { background: #d1fae5; color: #065f46; }
	.norm-avg       { background: #fef9c3; color: #854d0e; }
	.norm-fair      { background: #ffedd5; color: #9a3412; }
	.norm-needs     { background: #fee2e2; color: #991b1b; }
	.norm-label { font-weight: 700; }
	.norm-val   { font-weight: 400; font-size: 0.82rem; }
	.norm-note  { font-size: 0.78rem; color: #94a3b8; font-style: italic; margin: 0.5rem 0 0; text-align: center; }

	/* ── Button group ──────────────────────────────────────── */
	.button-group {
		display: flex; justify-content: center; gap: 1rem;
		flex-wrap: wrap; padding-top: 0.5rem; align-items: center;
	}

	.start-button {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white; border: none; border-radius: 10px;
		padding: 0.85rem 2.5rem; font-size: 1rem; font-weight: 700;
		cursor: pointer; transition: transform 0.15s, box-shadow 0.15s;
		box-shadow: 0 4px 14px rgba(102, 126, 234, 0.4);
	}
	.start-button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5); }

	.btn-secondary {
		background: white; color: #667eea;
		border: 2px solid #667eea; border-radius: 10px;
		padding: 0.85rem 2rem; font-size: 1rem; font-weight: 600;
		cursor: pointer; transition: all 0.15s;
	}
	.btn-secondary:hover { background: rgba(102, 126, 234, 0.08); }

	.help-link {
		background: none; border: none; color: #667eea;
		font-size: 0.9rem; cursor: pointer; text-decoration: underline;
		padding: 0.5rem; font-weight: 600; transition: color 0.15s;
	}
	.help-link:hover { color: #4f46e5; }

	/* ── Screen card ───────────────────────────────────────── */
	.screen-card {
		background: white; border-radius: 16px; padding: 2.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
	}

	.error-screen { text-align: center; }
	.error-screen h2 { margin: 0 0 0.75rem; color: #dc2626; }
	.error-screen p  { color: #64748b; margin: 0 0 1.5rem; }

	/* ── Practice / Testing screen ─────────────────────────── */
	.practice-screen, .testing-screen { text-align: center; }
	.practice-screen h2 { font-size: 1.6rem; font-weight: 700; color: #1e293b; margin: 0 0 0.4rem; }
	.practice-intro { color: #64748b; margin: 0 0 2rem; }

	/* ── Test header ───────────────────────────────────────── */
	.test-header {
		display: flex; justify-content: space-between; align-items: center;
		margin-bottom: 2rem; flex-wrap: wrap; gap: 0.5rem; text-align: left;
	}
	.test-badges { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; flex: 1; }
	.count-badge {
		background: rgba(102, 126, 234, 0.12); color: #667eea;
		padding: 0.4rem 0.9rem; border-radius: 20px; font-size: 0.85rem; font-weight: 700;
	}
	.pace-badge {
		background: #fff7ed; color: #c2410c;
		padding: 0.4rem 0.9rem; border-radius: 20px; font-size: 0.82rem; font-weight: 600;
	}
	.progress-track {
		flex: 1; height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden; min-width: 80px;
	}
	.progress-fill { height: 100%; background: linear-gradient(90deg, #ea580c, #f97316); border-radius: 3px; transition: width 0.3s; }
	.help-btn-sm {
		width: 36px; height: 36px; border-radius: 50%;
		border: 2px solid #667eea; background: white; color: #667eea;
		font-size: 1.1rem; font-weight: 700; cursor: pointer;
		transition: all 0.2s; display: flex; align-items: center; justify-content: center;
	}
	.help-btn-sm:hover { background: #667eea; color: white; }

	/* ── Big digit display ─────────────────────────────────── */
	.digit-display-area { margin: 1.5rem 0; }

	.big-digit-card {
		display: inline-flex; align-items: center; justify-content: center;
		width: 160px; height: 160px;
		background: linear-gradient(135deg, #fff7ed, #ffedd5);
		border: 3px solid #fed7aa; border-radius: 20px;
		box-shadow: 0 8px 24px rgba(234, 88, 12, 0.2);
		margin: 0 auto;
	}

	.big-digit {
		font-size: 5rem; font-weight: 900; color: #ea580c; line-height: 1;
	}

	.digit-hint { margin-top: 1rem; }

	.hint-chip {
		background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 20px;
		padding: 0.4rem 1rem; font-size: 0.88rem; color: #475569; font-weight: 600;
	}
	.hint-first { background: #fff7ed; border-color: #fed7aa; color: #c2410c; }

	/* ── Answer area ───────────────────────────────────────── */
	.answer-area {
		display: flex; flex-direction: column; align-items: center; gap: 0.75rem; margin-top: 1.5rem;
	}

	.answer-prompt { font-size: 1rem; font-weight: 600; color: #1e293b; margin: 0; }

	.answer-input {
		width: 200px; padding: 0.75rem 1rem; font-size: 1.6rem; font-weight: 700;
		text-align: center; border: 3px solid #fed7aa; border-radius: 12px;
		background: #fff7ed; color: #7c2d12; outline: none;
		transition: border-color 0.2s, box-shadow 0.2s;
	}
	.answer-input:focus { border-color: #ea580c; box-shadow: 0 0 0 3px rgba(234, 88, 12, 0.15); }
	.answer-input.large { width: 240px; font-size: 2rem; padding: 0.9rem 1rem; }

	/* ── Waiting state ─────────────────────────────────────── */
	.waiting-state { margin: 2rem 0; }
	.waiting-state p { color: #94a3b8; font-size: 0.95rem; font-style: italic; margin: 0; }

	/* ── Practice complete ─────────────────────────────────── */
	.complete-msg { text-align: center; padding: 1rem; }
	.complete-icon { font-size: 3rem; margin-bottom: 0.5rem; }
	.complete-msg h3 { font-size: 1.4rem; font-weight: 700; color: #1e293b; margin: 0 0 0.5rem; }
	.complete-msg p { color: #64748b; margin: 0 0 0.75rem; line-height: 1.6; }
	.complete-rule { font-size: 0.9rem; color: #c2410c; font-style: italic; }

	/* ── Complete screen ───────────────────────────────────── */
	.complete-screen { display: flex; flex-direction: column; gap: 1.5rem; }

	.perf-banner {
		text-align: center; padding: 1.5rem;
		background: linear-gradient(135deg, #fff7ed, #ffedd5);
		border: 2px solid #fed7aa; border-radius: 14px;
	}
	.perf-emoji    { font-size: 2.5rem; margin-bottom: 0.25rem; }
	.perf-level    { font-size: 1.8rem; font-weight: 800; color: #ea580c; }
	.perf-subtitle { font-size: 0.95rem; color: #64748b; margin-top: 0.3rem; }

	.metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; }
	.metric-card {
		background: #f8fafc; border: 1px solid #e2e8f0;
		border-radius: 12px; padding: 1.2rem; text-align: center;
	}
	.metric-card.highlight {
		background: linear-gradient(135deg, #ea580c, #c2410c);
		color: white; border-color: transparent;
	}
	.metric-icon  { font-size: 1.8rem; margin-bottom: 0.4rem; }
	.metric-value { font-size: 1.8rem; font-weight: 800; color: #1e293b; margin-bottom: 0.2rem; }
	.metric-card.highlight .metric-value,
	.metric-card.highlight .metric-label,
	.metric-card.highlight .metric-sub { color: white; }
	.metric-label { font-size: 0.82rem; font-weight: 600; color: #64748b; }
	.metric-sub   { font-size: 0.78rem; color: #94a3b8; margin-top: 0.2rem; }

	/* ── Breakdown ─────────────────────────────────────────── */
	.breakdown { background: #f8fafc; border-radius: 12px; padding: 1.2rem; }
	.breakdown h3 { font-size: 0.95rem; font-weight: 700; color: #1e293b; margin: 0 0 0.8rem; }
	.breakdown-row {
		display: flex; justify-content: space-between; align-items: center;
		padding: 0.55rem 0; border-bottom: 1px solid #e2e8f0; font-size: 0.9rem;
	}
	.breakdown-row:last-child { border-bottom: none; }
	.bd-label   { color: #64748b; }
	.bd-val     { font-weight: 700; color: #667eea; }
	.bd-success { color: #16a34a; }
	.bd-warning { color: #dc2626; }

	/* ── Fatigue notice ────────────────────────────────────── */
	.fatigue-notice {
		background: #fef9c3; border: 1px solid #fde047; border-radius: 12px; padding: 1.2rem;
	}
	.fatigue-notice h4 { font-size: 0.9rem; font-weight: 700; color: #854d0e; margin: 0 0 0.5rem; }
	.fatigue-notice p  { font-size: 0.88rem; color: #78350f; margin: 0; line-height: 1.6; }

	/* ── Clinical note ─────────────────────────────────────── */
	.clinical-note {
		background: linear-gradient(135deg, #f0fdf4, #dcfce7);
		border: 1px solid #bbf7d0; border-radius: 12px; padding: 1.2rem;
	}
	.clinical-note h4 { font-size: 0.9rem; font-weight: 700; color: #166534; margin: 0 0 0.5rem; }
	.clinical-note p { font-size: 0.9rem; color: #15803d; line-height: 1.6; margin: 0 0 0.5rem; }
	.clinical-note p:last-child { margin: 0; }
	.why-matters { font-style: italic; }

	/* ── Difficulty info ───────────────────────────────────── */
	.difficulty-info {
		background: #fff7ed; border: 1px solid #fed7aa; border-radius: 10px;
		padding: 0.9rem 1.2rem; display: flex; justify-content: space-between;
		align-items: center; flex-wrap: wrap; gap: 0.5rem;
		font-size: 0.88rem; font-weight: 600; color: #c2410c;
	}
	.adapt-reason { color: #f97316; font-weight: 400; font-style: italic; }

	/* ── Help modal ────────────────────────────────────────── */
	.modal-overlay {
		position: fixed; inset: 0; background: rgba(0,0,0,0.55);
		display: flex; align-items: center; justify-content: center;
		z-index: 1000; padding: 1rem;
	}
	.modal-content {
		background: white; border-radius: 16px; padding: 2rem;
		max-width: 560px; width: 100%; max-height: 80vh; overflow-y: auto;
		position: relative; box-shadow: 0 20px 60px rgba(0,0,0,0.3);
	}
	.close-btn {
		position: absolute; top: 1rem; right: 1rem;
		width: 36px; height: 36px; border: none; background: #f1f5f9;
		color: #475569; font-size: 1.4rem; border-radius: 50%; cursor: pointer;
		display: flex; align-items: center; justify-content: center; transition: background 0.15s;
	}
	.close-btn:hover { background: #e2e8f0; }
	.modal-content h2 {
		font-size: 1.2rem; font-weight: 700; color: #1e293b;
		margin: 0 0 1.2rem; padding-right: 2.5rem;
	}
	.strategy {
		padding: 0.9rem 1rem; background: #f8fafc;
		border-radius: 8px; border-left: 4px solid #ea580c; margin-bottom: 0.75rem;
	}
	.strategy h3 { font-size: 0.88rem; font-weight: 700; color: #1e293b; margin: 0 0 0.3rem; }
	.strategy p  { font-size: 0.84rem; color: #64748b; margin: 0; line-height: 1.5; }

	/* ── Responsive ────────────────────────────────────────── */
	@media (max-width: 640px) {
		.instructions-card { padding: 1.5rem; gap: 1.2rem; }
		.rules-grid { grid-template-columns: 1fr; }
		.info-grid { grid-template-columns: 1fr; }
		.clinical-grid { grid-template-columns: 1fr; }
		.metrics-grid { grid-template-columns: repeat(2, 1fr); }
		.header-content h1 { font-size: 1.4rem; }
		.screen-card { padding: 1.25rem; }
		.pasat-example { gap: 0.25rem; padding: 0.75rem; }
		.ex-digit { font-size: 1.4rem; }
		.big-digit-card { width: 120px; height: 120px; }
		.big-digit { font-size: 3.5rem; }
		.answer-input.large { width: 180px; font-size: 1.6rem; }
	}
</style>

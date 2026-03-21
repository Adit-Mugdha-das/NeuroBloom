<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import {
		formatNumber,
		formatPercent,
		localizeDigitInput,
		locale,
		normalizeLocalizedDigits,
		translateText
	} from '$lib/i18n';
	import { user } from '$lib/stores.js';
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
	
	// Timer for digit presentation
	let digitTimer = null;

	// Subscribe to user store
	user.subscribe(value => {
		currentUser = value;
	});

	function t(text) {
		return translateText(text ?? '', $locale);
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
		showInstructions = false;
		showPractice = true;
		practiceIndex = 0;
		practicePrevious = null;
		
		runPracticeTrial();
	}

	async function runPracticeTrial() {
		if (practiceIndex >= practiceDigits.length) {
			practiceComplete = true;
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
	<title>PASAT - NeuroBloom</title>
</svelte:head>

<svelte:window on:keypress={handleKeyPress} />

<div class="task-container" data-localize-skip>
	{#if loading}
		<div class="loading-state">
			<div class="spinner"></div>
			<p>{t('Loading task...')}</p>
		</div>
	{:else if error}
		<div class="error-state">
			<h2>⚠️ {t('Error')}</h2>
			<p>{t(error)}</p>
			<button on:click={returnToDashboard}>{t('Return to Dashboard')}</button>
		</div>
	{:else if showInstructions}
		<div class="instructions-panel">
			<div class="task-header">
				<div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap;">
					<h1>🎯 {t('PASAT (Paced Auditory Serial Addition Test)')}</h1>
					<DifficultyBadge difficulty={sessionData?.difficulty || 5} domain="Processing Speed" />
				</div>
				<p class="task-subtitle">{t('MS Gold Standard Attention Assessment')}</p>
				<div class="gold-standard-badge">⭐⭐⭐⭐⭐ {t('CLINICAL GOLD STANDARD')}</div>
			</div>

			<div class="clinical-context">
				<h3>📋 {t('About This Task')}</h3>
				<p>{t('PASAT is the most widely used cognitive test in MS research and clinical trials. It measures sustained attention, working memory, and processing speed under time pressure.')}</p>
				
				<div class="ms-benefits">
					<h4>✨ {t('Why PASAT is Critical for MS')}</h4>
					<ul>
						<li><strong>{t('Historical Standard:')}</strong> {t('Used in MS trials for decades')}</li>
						<li><strong>{t('Sustained Attention:')}</strong> {t('Tracks attention over extended periods')}</li>
						<li><strong>{t('Lesion Correlation:')}</strong> {t('Performance correlates with brain lesion burden')}</li>
						<li><strong>{t('Functional Predictor:')}</strong> {t('Relates to real-world cognitive abilities')}</li>
					</ul>
				</div>

				<div class="research-note">
					<strong>{t('Research Foundation:')}</strong> {t('Gronwall, 1977 - Paced Auditory Serial-Addition Task. Extensively validated in MS populations worldwide.')}
				</div>
			</div>

			<div class="how-it-works">
				<h3>🎯 {t('How It Works')}</h3>
				<div class="pasat-example">
					<div class="example-header">{t('Example:')}</div>
					<div class="example-sequence">
						<div class="example-step">
							<div class="digit-display">{localizedDigit(3)}</div>
							<div class="action">({t('Remember this')})</div>
						</div>
						<div class="arrow">→</div>
						<div class="example-step">
							<div class="digit-display">{localizedDigit(5)}</div>
							<div class="action">{t('Answer:')} <strong>{localizedDigit(8)}</strong></div>
							<div class="explanation">({localizedDigit(3)} + {localizedDigit(5)} = {localizedDigit(8)})</div>
						</div>
						<div class="arrow">→</div>
						<div class="example-step">
							<div class="digit-display">{localizedDigit(2)}</div>
							<div class="action">{t('Answer:')} <strong>{localizedDigit(7)}</strong></div>
							<div class="explanation">({localizedDigit(5)} + {localizedDigit(2)} = {localizedDigit(7)})</div>
						</div>
						<div class="arrow">→</div>
						<div class="example-step">
							<div class="digit-display">{localizedDigit(9)}</div>
							<div class="action">{t('Answer:')} <strong>{localizedDigit(11)}</strong></div>
							<div class="explanation">({localizedDigit(2)} + {localizedDigit(9)} = {localizedDigit(11)})</div>
						</div>
					</div>
				</div>

				<div class="key-rule">
					<strong>⚠️ {t('KEY RULE:')}</strong> {t('Add each NEW digit to the PREVIOUS digit. Ignore the running total!')}
				</div>

				<div class="instruction-steps">
					<div class="step">
						<span class="step-number">{n(1)}</span>
						<div class="step-content">
							<h4>{t('See the Digit')}</h4>
							<p>{t('A single digit (1-9) appears on screen')}</p>
						</div>
					</div>
					<div class="step">
						<span class="step-number">{n(2)}</span>
						<div class="step-content">
							<h4>{t('Add to Previous')}</h4>
							<p>{t('Add this digit to the one you just saw (not the answer you gave!)')}</p>
						</div>
					</div>
					<div class="step">
						<span class="step-number">{n(3)}</span>
						<div class="step-content">
							<h4>{t('Type Your Answer')}</h4>
							<p>{t('Enter the sum and press Enter before the next digit appears')}</p>
						</div>
					</div>
					<div class="step">
						<span class="step-number">{n(4)}</span>
						<div class="step-content">
							<h4>{t('Maintain Pace')}</h4>
							<p>
								{$locale === 'bn'
									? `চালিয়ে যান! প্রতি ${secondsLabel(sessionData?.config?.interval_seconds || 3)} পরপর নতুন অঙ্ক দেখাবে।`
									: `Keep going! Digits appear every ${sessionData?.config?.interval_seconds || 3} seconds`}
							</p>
						</div>
					</div>
				</div>
			</div>

			<div class="instruction-tips">
				<h3>💡 {t('Tips for Success')}</h3>
				<ul>
					<li><strong>{t('Focus on the previous digit')}</strong> - {t('not your last answer')}</li>
					<li><strong>{t("Don't try to keep a running total")}</strong> - {t("that's not the task")}</li>
					<li><strong>{t('Speed matters')}</strong> - {t('try to answer before the next digit')}</li>
					<li><strong>{t('If you miss one, keep going')}</strong> - {t("don't get discouraged")}</li>
					<li><strong>{t('Stay calm')}</strong> - {t('this is challenging even for healthy adults')}</li>
					<li><strong>{t("It's okay to skip")}</strong> - {t('better to wait for the next digit than lose track')}</li>
				</ul>
			</div>

			<div class="difficulty-info">
				<h4>📊 {t('Your Current Pace')}</h4>
				<p><strong>{secondsLabel(sessionData?.config?.interval_seconds || 3)}</strong> {t('between digits')}</p>
				<p class="difficulty-description">{t(sessionData?.config?.description || 'Standard PASAT-3')}</p>
			</div>

			<div class="action-buttons">
				<button class="primary-btn" on:click={startPractice}>
					{t('Start Practice (4 digits)')}
				</button>
				<button class="help-btn" on:click={() => showHelp = true}>
					📖 {t('More Information')}
				</button>
			</div>
		</div>
	{:else if showPractice}
		<div class="practice-panel">
			<h2>🎓 {t('Practice Mode')}</h2>
			<p class="practice-intro">{t("Let's practice with 4 digits. Take your time to understand the pattern.")}</p>
			
			{#if !practiceComplete}
				<div class="practice-display">
					<div class="digit-card">
						<div class="current-digit">{localizedDigit(currentDigit)}</div>
						{#if practiceIndex === 0}
							<div class="hint-text">{t('First digit - just remember it!')}</div>
						{:else if practiceIndex === 1}
							<div class="hint-text">
								{$locale === 'bn'
									? `এই অঙ্কটি আগেরটির সঙ্গে যোগ করুন: ${localizedDigit(practicePrevious)} + ${localizedDigit(currentDigit)} = ?`
									: `Add this digit to the previous one: ${practicePrevious} + ${currentDigit} = ?`}
							</div>
						{:else}
							<div class="hint-text">{t('Add to the previous digit (remember it!)')}</div>
						{/if}
					</div>

					{#if waitingForAnswer}
						<div class="answer-input-area">
							<input
								type="text"
								inputmode="numeric"
								pattern="[0-9]*"
								value={numericFieldValue(userAnswer)}
								on:input={validateNumericInput}
								placeholder={t('Type your answer')}
								autofocus
								class="answer-input"
							/>
							<button class="submit-btn" on:click={handlePracticeAnswer}>
								{t('Submit Answer')}
							</button>
						</div>
					{/if}
				</div>
			{:else}
				<div class="practice-complete">
					<h3>✅ {t('Practice Complete!')}</h3>
					<p>
						{$locale === 'bn'
							? `দারুণ! এখন আপনি টাস্কটি বুঝে গেছেন। আসল পরীক্ষায় ${digitsLabel(sessionData.total_trials)} থাকবে।`
							: `Great! Now you understand the task. The real test will have ${sessionData.total_trials} digits.`}
					</p>
					<p><strong>{t('Remember:')}</strong> {t('Add each new digit to the previous digit, not to your running total!')}</p>
					<button class="primary-btn" on:click={startTest}>
						{t(`Start Actual Test (${sessionData.total_trials} digits)`)}
					</button>
				</div>
			{/if}
		</div>
	{:else if testStarted}
		<div class="test-panel">
			<div class="test-header">
				<div class="progress-info">
					<div class="trials-remaining">
						<span class="remaining-label">{t('Digits Remaining')}</span>
						<span class="remaining-value">{n(trialsRemaining)}</span>
					</div>
					<div class="pace-info">
						<span class="info-label">{t('Pace')}</span>
						<span class="info-value">{intervalLabel(sessionData.interval_seconds)}</span>
					</div>
				</div>
				<div class="progress-bar">
					<div class="progress-fill" style="width: {progressPercent}%"></div>
				</div>
			</div>

			<div class="test-display">
				<div class="digit-card large">
					<div class="current-digit-large">{localizedDigit(currentDigit)}</div>
				</div>

				{#if waitingForAnswer}
					<div class="answer-input-area">
						<input
							type="text"
							inputmode="numeric"
							pattern="[0-9]*"
							value={numericFieldValue(userAnswer)}
							on:input={validateNumericInput}
							placeholder={t('Enter sum')}
							autofocus
							class="answer-input large"
						/>
						<button class="submit-btn" on:click={handleAnswerSubmit}>
							{t('Submit (Enter)')}
						</button>
					</div>
				{/if}

				{#if !waitingForAnswer && currentTrialIndex > 0 && currentTrialIndex < sessionData.total_trials}
					<div class="waiting-message">
						<p>{t('Next digit coming...')}</p>
					</div>
				{/if}
			</div>
		</div>
	{:else if showResults}
		<div class="results-panel">
			<div class="results-header">
				<h2>📊 {t('PASAT Results')}</h2>
				<div class="performance-badge {results.metrics.performance_level.toLowerCase().replace(' ', '-')}">
					{performanceLevelLabel(results.metrics.performance_level)}
				</div>
			</div>

			<div class="metrics-grid">
				<div class="metric-card primary">
					<div class="metric-icon">🎯</div>
					<div class="metric-value">{pct(results.metrics.accuracy, { maximumFractionDigits: 0 })}</div>
					<div class="metric-label">{t('Accuracy')}</div>
					<div class="metric-detail">
						{$locale === 'bn'
							? `${n(results.metrics.correct_count)}/${n(results.metrics.total_trials)} সঠিক`
							: `${results.metrics.correct_count}/${results.metrics.total_trials} correct`}
					</div>
				</div>

				<div class="metric-card">
					<div class="metric-icon">⚡</div>
					<div class="metric-value">{pct(results.metrics.sustained_attention, { maximumFractionDigits: 0 })}</div>
					<div class="metric-label">{t('Sustained Attention')}</div>
					<div class="metric-detail">{t('Performance in final third')}</div>
				</div>

				<div class="metric-card">
					<div class="metric-icon">⏱️</div>
					<div class="metric-value">{millisecondsLabel(results.metrics.average_reaction_time)}</div>
					<div class="metric-label">{t('Avg Response Time')}</div>
					<div class="metric-detail">{t('Per digit')}</div>
				</div>

				<div class="metric-card">
					<div class="metric-icon">📈</div>
					<div class="metric-value">{pct(results.metrics.consistency, { maximumFractionDigits: 0 })}</div>
					<div class="metric-label">{t('Consistency')}</div>
					<div class="metric-detail">{t('Response stability')}</div>
				</div>
			</div>

			{#if results.metrics.fatigue_effect > 15}
				<div class="fatigue-notice">
					<h4>⚠️ {t('Fatigue Detected')}</h4>
					<p>
						{$locale === 'bn'
							? `শুরু থেকে শেষ পর্যন্ত আপনার পারফরম্যান্স ${pct(results.metrics.fatigue_effect)} কমেছে। PASAT-এর মতো কঠিন টাস্কে এটি স্বাভাবিক। সেশনগুলোর মাঝে একটু বিরতি নিলে ভালো হবে।`
							: `Your performance decreased ${results.metrics.fatigue_effect.toFixed(1)}% from start to finish. This is normal for PASAT - it's a demanding task! Consider taking breaks between sessions.`}
					</p>
				</div>
			{/if}

			<div class="interpretation-section">
				<h3>🧠 {t('What This Means')}</h3>
				<p class="interpretation-text">{interpretationText()}</p>

				<div class="pasat-context">
					<h4>{t('Understanding PASAT Performance')}</h4>
					<ul>
						<li><strong>{t('Gold Standard Test:')}</strong> {t('Most widely used MS cognitive assessment')}</li>
						<li><strong>{t('Dual Task:')}</strong> {t('Requires both working memory and sustained attention')}</li>
						<li><strong>{t('Time Pressure:')}</strong> {t('Paced presentation adds processing speed demands')}</li>
						<li><strong>{t('MS Research:')}</strong> {t('Performance correlates with brain lesion burden')}</li>
						<li><strong>{t('Training Effect:')}</strong> {t('Regular practice improves sustained attention capacity')}</li>
					</ul>
				</div>
			</div>

			{#if results.adaptation_reason}
				<div class="adaptation-info">
					<h4>📊 {t('Next Session')}</h4>
					<p>{t(results.adaptation_reason)}</p>
					{#if results.difficulty_after > results.difficulty_before}
						<p class="difficulty-change increase">
							{paceChangeLabel('increase', results.difficulty_before, results.difficulty_after)}
						</p>
					{:else if results.difficulty_after < results.difficulty_before}
						<p class="difficulty-change decrease">
							{paceChangeLabel('decrease', results.difficulty_before, results.difficulty_after)}
						</p>
					{:else}
						<p class="difficulty-change same">
							{paceChangeLabel('same', results.difficulty_before, results.difficulty_after)}
						</p>
					{/if}
				</div>
			{/if}

			{#if results.new_badges && results.new_badges.length > 0}
				<div class="new-badges">
					<h3>🏆 {t('New Badges Earned!')}</h3>
					<div class="badge-list">
						{#each results.new_badges as badge}
							<div class="badge-item">
								<span class="badge-icon">{badge.icon}</span>
								<div class="badge-info">
									<div class="badge-name">{t(badge.name)}</div>
									<div class="badge-description">{t(badge.description)}</div>
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}

			<div class="action-buttons">
				<button class="primary-btn" on:click={returnToDashboard}>
					{t('Return to Dashboard')}
				</button>
			</div>
		</div>
	{/if}
</div>

{#if showHelp}
	<div class="modal-overlay" on:click={() => showHelp = false} on:keydown={(e) => e.key === 'Escape' && (showHelp = false)} role="button" tabindex="0">
		<div class="modal-content" on:click|stopPropagation on:keydown role="dialog" tabindex="-1">
			<div class="modal-header">
				<h2>📖 {t('PASAT - Detailed Information')}</h2>
				<button class="close-btn" on:click={() => showHelp = false}>✕</button>
			</div>
			
			<div class="modal-body">
				<section>
					<h3>{t('What is PASAT?')}</h3>
					<p>{t('The Paced Auditory Serial Addition Test is the most widely used cognitive measure in MS clinical trials and research. It assesses sustained attention, working memory, and information processing speed simultaneously.')}</p>
				</section>

				<section>
					<h3>{t('Why is it the MS Gold Standard?')}</h3>
					<ul>
						<li><strong>{t('Historical Use:')}</strong> {t('Decades of MS research and clinical trials')}</li>
						<li><strong>{t('Sensitivity:')}</strong> {t('Detects subtle cognitive changes in MS')}</li>
						<li><strong>{t('Correlation:')}</strong> {t('Scores relate to brain lesion burden and disability')}</li>
						<li><strong>{t('Predictive Value:')}</strong> {t('Performance predicts real-world functioning')}</li>
						<li><strong>{t('Standardized:')}</strong> {t('Well-established norms and procedures')}</li>
					</ul>
				</section>

				<section>
					<h3>{t('Common Challenges')}</h3>
					<ul>
						<li><strong>{t('Confusion:')}</strong> {t('Adding to previous digit vs. running total')}</li>
						<li><strong>{t('Pace:')}</strong> {t('Time pressure can cause anxiety')}</li>
						<li><strong>{t('Fatigue:')}</strong> {t('Performance often decreases over duration')}</li>
						<li><strong>{t('Recovery:')}</strong> {t('Hard to get back on track after mistakes')}</li>
					</ul>
				</section>

				<section>
					<h3>{t('Strategies for Success')}</h3>
					<ol>
						<li><strong>{t('Forget Your Answer:')}</strong> {t('After you answer, only remember the digit you just saw')}</li>
						<li><strong>{t("Don't Keep Totals:")}</strong> {t('Ignore all running sums - just focus on the last two digits')}</li>
						<li><strong>{t('Stay Calm:')}</strong> {t('If you miss one, reset with the next digit')}</li>
						<li><strong>{t('Use Visualization:')}</strong> {t('Picture the two numbers side by side')}</li>
						<li><strong>{t('Practice Pace:')}</strong> {t('Get comfortable with the rhythm')}</li>
						<li><strong>{t('Accept Mistakes:')}</strong> {t("Even healthy adults struggle - it's designed to be hard")}</li>
					</ol>
				</section>

				<section>
					<h3>{t('PASAT Variants')}</h3>
					<p><strong>{t('PASAT-4:')}</strong> {t('4-second intervals (easier, what we start with)')}</p>
					<p><strong>{t('PASAT-3:')}</strong> {t('3-second intervals (standard clinical version)')}</p>
					<p><strong>{t('PASAT-2:')}</strong> {t('2-second intervals (very challenging)')}</p>
					<p><strong>{t('Visual PASAT:')}</strong> {t('Numbers shown visually (less stressful than audio-only)')}</p>
				</section>

				<section>
					<h3>{t('MS Research Applications')}</h3>
					<p>{t('PASAT is included in major MS cognitive batteries (MACFIMS, BRB-N) and has been used in thousands of clinical trials to measure cognitive outcomes and treatment effects.')}</p>
				</section>
			</div>

			<div class="modal-footer">
				<button class="primary-btn" on:click={() => showHelp = false}>{t('Got It!')}</button>
			</div>
		</div>
	</div>
{/if}

<style>
	.task-container {
		max-width: 1100px;
		margin: 0 auto;
		padding: 2rem;
		min-height: 100vh;
	}

	.loading-state, .error-state {
		text-align: center;
		padding: 4rem 2rem;
	}

	.spinner {
		width: 50px;
		height: 50px;
		border: 4px solid rgba(99, 102, 241, 0.1);
		border-top-color: #6366f1;
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin: 0 auto 1rem;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	/* Instructions Panel */
	.instructions-panel {
		background: white;
		border-radius: 16px;
		padding: 2.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
	}

	.task-header {
		text-align: center;
		margin-bottom: 2rem;
	}

	.task-header h1 {
		font-size: 2.5rem;
		color: #1f2937;
		margin-bottom: 0.5rem;
	}

	.task-subtitle {
		font-size: 1.1rem;
		color: #6b7280;
		margin-bottom: 1rem;
	}

	.gold-standard-badge {
		display: inline-block;
		background: linear-gradient(135deg, #f59e0b, #d97706);
		color: white;
		padding: 0.5rem 1.5rem;
		border-radius: 20px;
		font-weight: bold;
		font-size: 0.9rem;
		letter-spacing: 0.5px;
		box-shadow: 0 4px 6px rgba(245, 158, 11, 0.3);
	}

	.clinical-context {
		background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
		border-left: 4px solid #0ea5e9;
		padding: 1.5rem;
		border-radius: 8px;
		margin-bottom: 2rem;
	}

	.clinical-context h3 {
		color: #0c4a6e;
		margin-bottom: 1rem;
	}

	.ms-benefits {
		margin-top: 1rem;
		padding: 1rem;
		background: rgba(255, 255, 255, 0.7);
		border-radius: 8px;
	}

	.ms-benefits h4 {
		color: #0369a1;
		margin-bottom: 0.75rem;
	}

	.ms-benefits ul {
		list-style: none;
		padding: 0;
	}

	.ms-benefits li {
		padding: 0.4rem 0;
		color: #374151;
	}

	.research-note {
		margin-top: 1rem;
		padding: 1rem;
		background: rgba(245, 208, 254, 0.3);
		border-radius: 8px;
		font-size: 0.95rem;
		color: #581c87;
	}

	.how-it-works {
		margin-bottom: 2rem;
	}

	.how-it-works h3 {
		color: #1f2937;
		margin-bottom: 1.5rem;
	}

	.pasat-example {
		background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
		padding: 2rem;
		border-radius: 12px;
		margin-bottom: 1.5rem;
		border: 2px solid #f59e0b;
	}

	.example-header {
		font-weight: bold;
		color: #78350f;
		margin-bottom: 1rem;
		font-size: 1.1rem;
	}

	.example-sequence {
		display: flex;
		align-items: center;
		gap: 1rem;
		flex-wrap: wrap;
		justify-content: center;
	}

	.example-step {
		text-align: center;
	}

	.digit-display {
		background: white;
		width: 60px;
		height: 60px;
		border-radius: 12px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 2rem;
		font-weight: bold;
		color: #1f2937;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
		margin-bottom: 0.5rem;
	}

	.action {
		font-weight: 600;
		color: #059669;
		margin-bottom: 0.25rem;
	}

	.explanation {
		font-size: 0.85rem;
		color: #6b7280;
	}

	.arrow {
		font-size: 1.5rem;
		color: #f59e0b;
		font-weight: bold;
	}

	.key-rule {
		background: linear-gradient(135deg, #fecaca 0%, #fca5a5 100%);
		border-left: 4px solid #dc2626;
		padding: 1rem 1.5rem;
		border-radius: 8px;
		color: #7f1d1d;
		font-size: 1.05rem;
		margin-bottom: 1.5rem;
	}

	.instruction-steps {
		display: grid;
		gap: 1rem;
		margin-bottom: 1.5rem;
	}

	.step {
		display: flex;
		gap: 1rem;
		align-items: start;
		padding: 1rem;
		background: #f9fafb;
		border-radius: 8px;
		border: 2px solid #e5e7eb;
	}

	.step-number {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 40px;
		height: 40px;
		background: linear-gradient(135deg, #6366f1, #8b5cf6);
		color: white;
		border-radius: 50%;
		font-weight: bold;
		flex-shrink: 0;
	}

	.step-content h4 {
		color: #374151;
		margin-bottom: 0.25rem;
	}

	.step-content p {
		color: #6b7280;
		font-size: 0.95rem;
	}

	.instruction-tips {
		margin-bottom: 2rem;
	}

	.instruction-tips h3 {
		color: #1f2937;
		margin-bottom: 1rem;
	}

	.instruction-tips ul {
		list-style: none;
		padding: 0;
	}

	.instruction-tips li {
		padding: 0.6rem 0;
		padding-left: 1.75rem;
		position: relative;
		color: #374151;
	}

	.instruction-tips li::before {
		content: "→";
		position: absolute;
		left: 0;
		color: #6366f1;
		font-weight: bold;
	}

	.difficulty-info {
		background: #f9fafb;
		padding: 1.5rem;
		border-radius: 8px;
		border: 2px solid #e5e7eb;
		margin-bottom: 2rem;
		text-align: center;
	}

	.difficulty-info h4 {
		color: #1f2937;
		margin-bottom: 0.75rem;
	}

	.difficulty-description {
		color: #6b7280;
		font-style: italic;
	}

	.action-buttons {
		display: flex;
		gap: 1rem;
		justify-content: center;
		margin-top: 2rem;
		flex-wrap: wrap;
	}

	.primary-btn {
		background: linear-gradient(135deg, #6366f1, #8b5cf6);
		color: white;
		border: none;
		padding: 1rem 2.5rem;
		font-size: 1.1rem;
		border-radius: 12px;
		cursor: pointer;
		font-weight: 600;
		transition: all 0.3s ease;
		box-shadow: 0 4px 6px rgba(99, 102, 241, 0.3);
	}

	.primary-btn:hover {
		transform: translateY(-2px);
		box-shadow: 0 6px 12px rgba(99, 102, 241, 0.4);
	}

	.help-btn {
		background: white;
		color: #6366f1;
		border: 2px solid #6366f1;
		padding: 1rem 2rem;
		font-size: 1.1rem;
		border-radius: 12px;
		cursor: pointer;
		font-weight: 600;
		transition: all 0.3s ease;
	}

	.help-btn:hover {
		background: #f0f9ff;
	}

	/* Practice Panel */
	.practice-panel {
		background: white;
		border-radius: 16px;
		padding: 2.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
		text-align: center;
	}

	.practice-panel h2 {
		color: #1f2937;
		margin-bottom: 1rem;
	}

	.practice-intro {
		color: #6b7280;
		margin-bottom: 2rem;
	}

	.practice-display {
		max-width: 600px;
		margin: 0 auto;
	}

	.digit-card {
		background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
		padding: 3rem 2rem;
		border-radius: 16px;
		margin-bottom: 2rem;
		border: 3px solid #0ea5e9;
	}

	.current-digit {
		font-size: 5rem;
		font-weight: bold;
		color: #0c4a6e;
		margin-bottom: 1rem;
	}

	.hint-text {
		color: #0369a1;
		font-size: 1.1rem;
		margin: 0.5rem 0;
	}

	.answer-input-area {
		display: flex;
		gap: 1rem;
		justify-content: center;
		align-items: center;
		flex-wrap: wrap;
	}

	.answer-input {
		width: 200px;
		padding: 1rem;
		font-size: 1.5rem;
		border: 3px solid #6366f1;
		border-radius: 12px;
		text-align: center;
		font-weight: bold;
	}

	.answer-input:focus {
		outline: none;
		border-color: #8b5cf6;
		box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2);
	}

	.submit-btn {
		background: linear-gradient(135deg, #10b981, #059669);
		color: white;
		border: none;
		padding: 1rem 2rem;
		font-size: 1.1rem;
		border-radius: 12px;
		cursor: pointer;
		font-weight: 600;
		transition: all 0.3s ease;
	}

	.submit-btn:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 8px rgba(16, 185, 129, 0.3);
	}

	.practice-complete {
		background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
		padding: 2rem;
		border-radius: 12px;
		border: 2px solid #10b981;
	}

	.practice-complete h3 {
		color: #065f46;
		margin-bottom: 1rem;
	}

	.practice-complete p {
		color: #064e3b;
		margin-bottom: 0.75rem;
	}

	/* Test Panel */
	.test-panel {
		background: white;
		border-radius: 16px;
		padding: 2rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
		min-height: 600px;
	}

	.test-header {
		margin-bottom: 2rem;
	}

	.progress-info {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		flex-wrap: wrap;
		gap: 1rem;
	}

	.trials-remaining {
		display: flex;
		align-items: center;
		gap: 1rem;
		background: linear-gradient(135deg, #8b5cf6, #7c3aed);
		padding: 0.75rem 1.5rem;
		border-radius: 12px;
		box-shadow: 0 4px 6px rgba(139, 92, 246, 0.3);
	}

	.remaining-label {
		color: rgba(255, 255, 255, 0.9);
		font-size: 0.9rem;
		font-weight: 500;
	}

	.remaining-value {
		background: rgba(255, 255, 255, 0.25);
		color: white;
		padding: 0.4rem 1rem;
		border-radius: 8px;
		font-weight: bold;
		font-size: 1.3rem;
		min-width: 50px;
		text-align: center;
	}

	.pace-info {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		background: linear-gradient(135deg, #f59e0b, #d97706);
		padding: 0.75rem 1.5rem;
		border-radius: 12px;
		box-shadow: 0 4px 6px rgba(245, 158, 11, 0.3);
	}

	.info-label {
		color: rgba(255, 255, 255, 0.9);
		font-size: 0.9rem;
		font-weight: 500;
	}

	.info-value {
		background: rgba(255, 255, 255, 0.25);
		color: white;
		padding: 0.4rem 1rem;
		border-radius: 8px;
		font-weight: bold;
		font-size: 1.1rem;
	}

	.progress-bar {
		width: 100%;
		height: 8px;
		background: #e5e7eb;
		border-radius: 4px;
		overflow: hidden;
	}

	.progress-fill {
		height: 100%;
		background: linear-gradient(90deg, #6366f1, #8b5cf6);
		transition: width 0.3s ease;
	}

	.test-display {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 400px;
	}

	.digit-card.large {
		background: linear-gradient(135deg, #ddd6fe 0%, #c4b5fd 100%);
		padding: 4rem 3rem;
		border: 4px solid #8b5cf6;
		margin-bottom: 2rem;
	}

	.current-digit-large {
		font-size: 8rem;
		font-weight: bold;
		color: #5b21b6;
	}


	.answer-input.large {
		width: 250px;
		font-size: 2rem;
	}

	.waiting-message {
		color: #9ca3af;
		font-size: 1.2rem;
		font-style: italic;
	}

	/* Results Panel */
	.results-panel {
		background: white;
		border-radius: 16px;
		padding: 2.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
	}

	.results-header {
		text-align: center;
		margin-bottom: 2rem;
	}

	.results-header h2 {
		color: #1f2937;
		margin-bottom: 1rem;
	}

	.performance-badge {
		display: inline-block;
		padding: 0.75rem 2rem;
		border-radius: 12px;
		font-weight: bold;
		font-size: 1.2rem;
		text-transform: uppercase;
		letter-spacing: 1px;
	}

	.performance-badge.excellent {
		background: linear-gradient(135deg, #10b981, #059669);
		color: white;
	}

	.performance-badge.very-good {
		background: linear-gradient(135deg, #3b82f6, #2563eb);
		color: white;
	}

	.performance-badge.good {
		background: linear-gradient(135deg, #8b5cf6, #7c3aed);
		color: white;
	}

	.performance-badge.average {
		background: linear-gradient(135deg, #f59e0b, #d97706);
		color: white;
	}

	.performance-badge.fair {
		background: linear-gradient(135deg, #f97316, #ea580c);
		color: white;
	}

	.performance-badge.needs-practice {
		background: linear-gradient(135deg, #ef4444, #dc2626);
		color: white;
	}

	.metrics-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1.5rem;
		margin-bottom: 2rem;
	}

	.metric-card {
		background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
		padding: 1.5rem;
		border-radius: 12px;
		text-align: center;
		border: 2px solid #e5e7eb;
		transition: all 0.3s ease;
	}

	.metric-card:hover {
		transform: translateY(-3px);
		box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
	}

	.metric-card.primary {
		background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
		border-color: #0ea5e9;
	}

	.metric-icon {
		font-size: 2rem;
		margin-bottom: 0.5rem;
	}

	.metric-value {
		font-size: 2.5rem;
		font-weight: bold;
		color: #1f2937;
		margin-bottom: 0.5rem;
	}

	.metric-label {
		font-size: 1rem;
		color: #6b7280;
		font-weight: 600;
		margin-bottom: 0.25rem;
	}

	.metric-detail {
		font-size: 0.85rem;
		color: #9ca3af;
	}

	.fatigue-notice {
		background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
		border-left: 4px solid #f59e0b;
		padding: 1.5rem;
		border-radius: 8px;
		margin-bottom: 2rem;
	}

	.fatigue-notice h4 {
		color: #78350f;
		margin-bottom: 0.75rem;
	}

	.fatigue-notice p {
		color: #92400e;
	}

	.interpretation-section {
		background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
		padding: 2rem;
		border-radius: 12px;
		margin-bottom: 2rem;
		border-left: 4px solid #0ea5e9;
	}

	.interpretation-section h3 {
		color: #0c4a6e;
		margin-bottom: 1rem;
	}

	.interpretation-text {
		color: #374151;
		line-height: 1.7;
		margin-bottom: 1.5rem;
	}

	.pasat-context {
		background: rgba(255, 255, 255, 0.7);
		padding: 1.5rem;
		border-radius: 8px;
	}

	.pasat-context h4 {
		color: #0369a1;
		margin-bottom: 1rem;
	}

	.pasat-context ul {
		list-style: none;
		padding: 0;
	}

	.pasat-context li {
		padding: 0.5rem 0;
		color: #374151;
	}

	.adaptation-info {
		background: #f9fafb;
		padding: 1.5rem;
		border-radius: 8px;
		border: 2px solid #e5e7eb;
		margin-bottom: 2rem;
	}

	.adaptation-info h4 {
		color: #1f2937;
		margin-bottom: 0.75rem;
	}

	.difficulty-change {
		font-weight: 600;
		margin-top: 0.75rem;
	}

	.difficulty-change.increase {
		color: #dc2626;
	}

	.difficulty-change.decrease {
		color: #059669;
	}

	.difficulty-change.same {
		color: #6b7280;
	}

	.new-badges {
		background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
		padding: 2rem;
		border-radius: 12px;
		border: 2px solid #f59e0b;
		margin-bottom: 2rem;
	}

	.new-badges h3 {
		color: #78350f;
		margin-bottom: 1.5rem;
	}

	.badge-list {
		display: grid;
		gap: 1rem;
	}

	.badge-item {
		display: flex;
		gap: 1rem;
		align-items: center;
		background: rgba(255, 255, 255, 0.7);
		padding: 1rem;
		border-radius: 8px;
	}

	.badge-icon {
		font-size: 2rem;
	}

	.badge-name {
		font-weight: bold;
		color: #78350f;
		margin-bottom: 0.25rem;
	}

	.badge-description {
		color: #92400e;
		font-size: 0.9rem;
	}

	/* Modal */
	.modal-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.6);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: 1rem;
	}

	.modal-content {
		background: white;
		border-radius: 16px;
		max-width: 700px;
		width: 100%;
		max-height: 90vh;
		overflow-y: auto;
		box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
	}

	.modal-header {
		padding: 2rem;
		border-bottom: 2px solid #e5e7eb;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.modal-header h2 {
		color: #1f2937;
		margin: 0;
	}

	.close-btn {
		background: none;
		border: none;
		font-size: 1.5rem;
		color: #6b7280;
		cursor: pointer;
		padding: 0.5rem;
		transition: color 0.3s ease;
	}

	.close-btn:hover {
		color: #1f2937;
	}

	.modal-body {
		padding: 2rem;
	}

	.modal-body section {
		margin-bottom: 2rem;
	}

	.modal-body h3 {
		color: #1f2937;
		margin-bottom: 1rem;
	}

	.modal-body p {
		color: #374151;
		line-height: 1.7;
		margin-bottom: 1rem;
	}

	.modal-body ul, .modal-body ol {
		color: #374151;
		line-height: 1.7;
		padding-left: 1.5rem;
	}

	.modal-body li {
		margin-bottom: 0.5rem;
	}

	.modal-footer {
		padding: 1.5rem 2rem;
		border-top: 2px solid #e5e7eb;
		text-align: center;
	}

	/* Responsive */
	@media (max-width: 768px) {
		.task-container {
			padding: 1rem;
		}

		.instructions-panel, .practice-panel, .test-panel, .results-panel {
			padding: 1.5rem;
		}

		.example-sequence {
			flex-direction: column;
		}

		.arrow {
			transform: rotate(90deg);
		}

		.current-digit {
			font-size: 3.5rem;
		}

		.current-digit-large {
			font-size: 5rem;
		}

		.answer-input {
			width: 100%;
		}

		.metrics-grid {
			grid-template-columns: 1fr;
		}

		.progress-info {
			flex-direction: column;
		}
	}
</style>

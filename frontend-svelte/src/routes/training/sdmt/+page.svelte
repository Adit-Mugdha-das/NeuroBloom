<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
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
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';
	let recordedTrial = null;

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

	function startTest(nextMode = TASK_PLAY_MODE.RECORDED) {
		playMode = nextMode;
		practiceStatusMessage = '';
		trial = nextMode === TASK_PLAY_MODE.PRACTICE
			? buildPracticePayload('sdmt', { trial: recordedTrial }).trial
			: structuredClone(recordedTrial);
		symbolDigitMapping = trial.symbol_digit_mapping;
		testSequence = trial.test_sequence;
		state = STATE.READY;
		setTimeout(() => {
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
			trial = structuredClone(recordedTrial);
			symbolDigitMapping = trial.symbol_digit_mapping;
			testSequence = trial.test_sequence;
			playMode = TASK_PLAY_MODE.RECORDED;
			practiceStatusMessage = getPracticeCopy($locale).complete;
			state = STATE.INSTRUCTIONS;
			return;
		}

		if (timerInterval) clearInterval(timerInterval);
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
	{#if state === STATE.LOADING}
		<div class="loading">
			<div class="spinner"></div>
			<p>{t('Loading Symbol Digit Modalities Test...')}</p>
		</div>
	{:else if state === STATE.INSTRUCTIONS}
		<div class="instructions">
			<div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap;">
				<h1>⚡ {t('Symbol Digit Modalities Test (SDMT)')}</h1>
				<DifficultyBadge {difficulty} domain="Processing Speed" />
			</div>
			<div class="gold-badge">⭐ {t('GOLD STANDARD for MS Assessment')} ⭐</div>
			
			<div class="instruction-card">
				<h2>{t('About This Test')}</h2>
				<p class="importance">
					{t('The SDMT is the most sensitive and widely used test for detecting cognitive changes in Multiple Sclerosis. It measures processing speed - how quickly your brain can match symbols to numbers.')}
				</p>
				
				<div class="clinical-info">
					<h3>{t('📊 Clinical Significance')}</h3>
					<ul>
						<li>{t('Most used in MS clinical trials')} {t('worldwide')}</li>
						<li>{t('Predicts employment success and daily functioning')}</li>
						<li>{t('Correlates with brain health and disease progression')}</li>
						<li>{t('Detects cognitive changes earlier than other tests')}</li>
					</ul>
				</div>

				<div class="how-it-works">
					<h3>{t('🎯 How It Works')}</h3>
					<div class="example-demo">
						<div class="example-key">
							<p><strong>{t('Reference Key (memorize these):')}</strong></p>
							<div class="demo-mappings">
								<div class="demo-pair"><span class="demo-symbol">★</span> → <span class="demo-digit">{n(1)}</span></div>
								<div class="demo-pair"><span class="demo-symbol">●</span> → <span class="demo-digit">{n(2)}</span></div>
								<div class="demo-pair"><span class="demo-symbol">■</span> → <span class="demo-digit">{n(3)}</span></div>
								<div class="demo-pair"><span class="demo-symbol">▲</span> → <span class="demo-digit">{n(4)}</span></div>
							</div>
						</div>
						
						<div class="example-task">
							<p><strong>{t('You see symbol:')}</strong></p>
							<div class="big-symbol">■</div>
							<p><strong>{t('You type:')}</strong></p>
							<div class="big-digit">{n(3)}</div>
						</div>
					</div>
				</div>

				<div class="test-details">
					<h3>{t('⏱️ Test Format')}</h3>
					<div class="details-grid">
						<div class="detail-item">
							<div class="detail-icon">⏰</div>
							<div class="detail-text">
								<strong>{lt('90 Seconds', `${n(90)} সেকেন্ড`)}</strong>
								<span>{t('Timed challenge')}</span>
							</div>
						</div>
						<div class="detail-item">
							<div class="detail-icon">🎯</div>
							<div class="detail-text">
								<strong>{lt(`Target: ${trial.target_responses}`, `লক্ষ্য: ${n(trial.target_responses)}`)}</strong>
								<span>{t('Correct responses')}</span>
							</div>
						</div>
						<div class="detail-item">
							<div class="detail-icon">⚡</div>
							<div class="detail-text">
								<strong>{t('Speed Matters')}</strong>
								<span>{t('Go as fast as you can')}</span>
							</div>
						</div>
						<div class="detail-item">
							<div class="detail-icon">✓</div>
							<div class="detail-text">
								<strong>{t('Accuracy Too')}</strong>
								<span>{t("But don't sacrifice speed")}</span>
							</div>
						</div>
					</div>
				</div>
				
				<div class="tips">
					<h3>{t('💡 Pro Tips')}</h3>
					<ul>
						<li><strong>{t('Memorize the key first:')}</strong> {t('Study the symbol-digit pairs before starting')}</li>
						<li><strong>{t('Use keyboard numbers:')}</strong> {t('Much faster than clicking')}</li>
						<li><strong>{t("Don't overthink:")}</strong> {t('Quick glances at the key are okay')}</li>
						<li><strong>{t('Rhythm is key:')}</strong> {t("Find a steady pace - look, type, next")}</li>
						<li><strong>{t('If unsure, keep going:')}</strong> {t("Don't dwell on mistakes")}</li>
					</ul>
				</div>

				<div class="performance-guide">
					<h3>{t('📈 Performance Guide (MS Norms)')}</h3>
					<div class="norm-scale">
						<div class="norm-item excellent">{lt('60+ = Excellent', `${n(60)}+ = ${t('Excellent')}`)}</div>
						<div class="norm-item good">{lt('50-60 = Good', `${n(50)}-${n(60)} = ${t('Good')}`)}</div>
						<div class="norm-item average">{lt('40-50 = Average', `${n(40)}-${n(50)} = ${t('Average')}`)}</div>
						<div class="norm-item fair">{lt('30-40 = Fair', `${n(30)}-${n(40)} = ${t('Fair')}`)}</div>
						<div class="norm-item practice">{lt('<30 = Practice Needed', `<${n(30)} = ${t('Practice Needed')}`)}</div>
					</div>
				</div>
			</div>
			
			<TaskPracticeActions
				locale={$locale}
				startLabel={localeText({ en: 'Start Actual Task', bn: 'আসল টাস্ক শুরু করুন' }, $locale)}
				statusMessage={practiceStatusMessage}
				align="center"
				on:start={() => startTest(TASK_PLAY_MODE.RECORDED)}
				on:practice={() => startTest(TASK_PLAY_MODE.PRACTICE)}
			/>
		</div>
	{:else if state === STATE.READY}
		<div class="ready-screen">
			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} />
			{/if}
			<h2>{t('Get Ready!')}</h2>
			<p class="ready-message">{t('Study the symbol-digit key below')}</p>
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
		<div class="testing-screen">
			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} />
			{/if}
			<div class="header">
				<div class="progress-info">
					<span class="count-badge">{lt(`Completed: ${currentIndex}`, `সম্পন্ন: ${n(currentIndex)}`)}</span>
					<span class="target-badge">{lt(`Target: ${trial.target_responses}`, `লক্ষ্য: ${n(trial.target_responses)}`)}</span>
				</div>
				<div class="timer-display">
					<span class="timer-icon">⏱️</span>
					<span class="timer-value" class:urgent={timeRemaining < 10}>
						{secondsText(Math.max(0, timeRemaining), 1)}
					</span>
				</div>
			</div>

			<div class="reference-key">
				<div class="key-label">{t('Reference Key:')}</div>
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
				
				<div class="input-area">
					<p class="input-instruction">{t('Type the number or click below:')}</p>
					<div class="digit-buttons">
						{#each Object.values(symbolDigitMapping).sort((a, b) => a - b) as digit}
							<button 
								class="digit-btn" 
								on:click={() => handleDigitClick(digit)}
							>
								{n(digit)}
							</button>
						{/each}
					</div>
				</div>
			</div>

			<div class="progress-bar">
				<div class="progress-fill" style="width: {(currentIndex / trial.test_sequence.length) * 100}%"></div>
			</div>

			<button class="help-button-floating" on:click={toggleHelp}>?</button>
		</div>
	{:else if state === STATE.COMPLETE}
		<div class="complete-screen">
			<h1>{t('SDMT Test Complete! 🎉')}</h1>
			
			{#if sessionResults}
				{@const perfLevel = getPerformanceLevel(sessionResults.metrics.score)}
				
				<div class="performance-badge" style="border-color: {perfLevel.color}; color: {perfLevel.color}">
					<div class="perf-level">{perfLevel.level}</div>
					<div class="perf-score">{lt(`${sessionResults.metrics.score} Correct`, `${n(sessionResults.metrics.score)} ${t('Correct')}`)}</div>
				</div>

				<div class="results-grid">
					<div class="result-card primary">
						<div class="result-icon">🎯</div>
						<div class="result-value">{n(sessionResults.metrics.score)}</div>
						<div class="result-label">{t('Correct Responses')}</div>
						<div class="result-sublabel">{lt(`Target: ${trial.target_responses}`, `লক্ষ্য: ${n(trial.target_responses)}`)}</div>
					</div>
					
					<div class="result-card">
						<div class="result-icon">⚡</div>
						<div class="result-value">{n(sessionResults.metrics.processing_speed)}</div>
						<div class="result-label">{t('Processing Speed')}</div>
						<div class="result-sublabel">{t('Responses/minute')}</div>
					</div>
					
					<div class="result-card">
						<div class="result-icon">✓</div>
						<div class="result-value">{percentText(sessionResults.metrics.accuracy)}</div>
						<div class="result-label">{t('Accuracy')}</div>
						<div class="result-sublabel">{t('Of attempted items')}</div>
					</div>
					
					<div class="result-card">
						<div class="result-icon">⏱️</div>
						<div class="result-value">{secondsText(sessionResults.metrics.avg_response_time / 1000, 2)}</div>
						<div class="result-label">{t('Avg Response Time')}</div>
						<div class="result-sublabel">{t('Per correct item')}</div>
					</div>
				</div>

				<div class="performance-breakdown">
					<h3>{t('📊 Detailed Breakdown')}</h3>
					<div class="breakdown-grid">
						<div class="breakdown-item">
							<span>{t('Total Attempted:')}</span>
							<span class="value">{n(sessionResults.metrics.total_attempted)}</span>
						</div>
						<div class="breakdown-item">
							<span>{t('Correct:')}</span>
							<span class="value correct">{n(sessionResults.metrics.correct_count)}</span>
						</div>
						<div class="breakdown-item">
							<span>{t('Incorrect:')}</span>
							<span class="value incorrect">{n(sessionResults.metrics.incorrect_count)}</span>
						</div>
						<div class="breakdown-item">
							<span>{t('Consistency:')}</span>
							<span class="value">{percentText(sessionResults.metrics.consistency)}</span>
						</div>
					</div>
				</div>

				<div class="clinical-context">
					<h3>{t('🏥 Clinical Context')}</h3>
					<p>
						{#if sessionResults.metrics.score >= 60}
							{t('Excellent performance! Your processing speed is above average for MS patients. This suggests good cognitive function and neural efficiency.')}
						{:else if sessionResults.metrics.score >= 50}
							{t('Good performance! Your score is in the average to above-average range for MS patients. Continue training to maintain and improve this level.')}
						{:else if sessionResults.metrics.score >= 40}
							{t('Average performance. Your score is in the typical range for MS patients. Regular training can help improve processing speed over time.')}
						{:else if sessionResults.metrics.score >= 30}
							{t("Fair performance. There's room for improvement in processing speed. Consistent practice with SDMT can lead to significant gains.")}
						{:else}
							{t('Keep practicing! Processing speed can be trained and improved with regular practice. The SDMT is challenging but very effective for building cognitive efficiency.')}
						{/if}
					</p>
				</div>

				<div class="difficulty-info">
					<p>
						{t('Difficulty:')} <strong>{n(sessionResults.difficulty_before)}</strong> → 
						<strong>{n(sessionResults.difficulty_after)}</strong>
					</p>
					<p class="adaptation-reason">{t(sessionResults.adaptation_reason)}</p>
				</div>

				{#if sessionResults.new_badges && sessionResults.new_badges.length > 0}
					<div class="new-badges">
						<h3>{t('🏆 New Badges Earned!')}</h3>
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
			{/if}
		</div>
	{/if}
</div>

{#if showHelp}
	<div class="help-modal" on:click|self={toggleHelp} role="dialog" tabindex="-1" on:keydown={(e) => e.key === 'Escape' && toggleHelp()}>
		<div class="help-content" role="document" tabindex="-1">
			<button class="close-button" on:click={toggleHelp}>×</button>
			<h2>{t('SDMT Success Strategies')}</h2>
			
			<div class="strategy">
				<h3>{t('👀 Visual Scanning')}</h3>
				<p>{lt("Train your eyes to quickly dart between the symbol, the key, and back. With practice, you'll memorize most pairs.", 'চোখকে এমনভাবে অনুশীলন করুন যেন প্রতীক, কী, এবং আবার প্রতীকের দিকে দ্রুত যেতে পারে। অনুশীলনের সঙ্গে সঙ্গে বেশিরভাগ জোড়া আপনার মনে গেঁথে যাবে।')}</p>
			</div>
			
			<div class="strategy">
				<h3>{t('🧠 Chunking Memory')}</h3>
				<p>{lt('Group symbols by shape or type in your mind. This creates mental "buckets" that make recall faster.', 'মনে মনে প্রতীকগুলোকে আকার বা ধরন অনুযায়ী ভাগ করুন। এতে মানসিক ছোট ছোট দলে সাজানো যায় এবং মনে করা দ্রুত হয়।')}</p>
			</div>
			
			<div class="strategy">
				<h3>{t('⌨️ Keyboard Mastery')}</h3>
				<p>{lt('Use the number row on your keyboard. Position your fingers over commonly used digits. Much faster than clicking!', 'কীবোর্ডের সংখ্যার সারি ব্যবহার করুন। যে অঙ্কগুলো বেশি লাগে, সেগুলোর উপর আঙুল প্রস্তুত রাখুন। এতে ক্লিকের চেয়ে অনেক দ্রুত সাড়া দেওয়া যায়।')}</p>
			</div>
			
			<div class="strategy">
				<h3>{t('🎯 Rhythm Over Perfection')}</h3>
				<p>{lt("Find a steady rhythm: glance → type → next. Don't stop to verify each answer. Speed matters more than perfection.", 'একটি স্থির ছন্দ তৈরি করুন: দেখুন → টাইপ করুন → এগোন। প্রতিটি উত্তর বারবার যাচাই করতে থামবেন না। নিখুঁততার চেয়ে গতি এখানে বেশি গুরুত্বপূর্ণ।')}</p>
			</div>
			
			<div class="strategy">
				<h3>{t('🔄 Progressive Learning')}</h3>
				<p>{lt("First few trials: reference the key often. Later trials: you'll have memorized most pairs. Trust your memory!", 'শুরুর কয়েকটি ট্রায়ালে কী বেশি দেখে নিন। পরে বেশিরভাগ জোড়া মনে থেকে যাবে। নিজের স্মৃতির ওপর ভরসা রাখুন।')}</p>
			</div>

			<div class="strategy">
				<h3>{t('💪 Why This Matters')}</h3>
				<p>{lt('SDMT measures neural processing efficiency - how fast your brain can retrieve and apply information. Regular practice strengthens these neural pathways!', 'SDMT মাপে মস্তিষ্ক কত দ্রুত তথ্য খুঁজে বের করে প্রয়োগ করতে পারে। নিয়মিত অনুশীলন এই স্নায়বিক পথগুলোকে আরও শক্তিশালী করে।')}</p>
			</div>
		</div>
	</div>
{/if}

<style>
	.sdmt-container {
		max-width: 1000px;
		margin: 0 auto;
		padding: 2rem;
		min-height: 100vh;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
	}

	.loading {
		text-align: center;
		padding: 4rem 0;
		color: white;
	}

	.spinner {
		width: 50px;
		height: 50px;
		border: 4px solid rgba(255,255,255,0.3);
		border-top: 4px solid white;
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
		color: white;
		margin-bottom: 1rem;
		font-size: 2.5rem;
		text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
	}

	.gold-badge {
		background: linear-gradient(135deg, #FFD700, #FFA500);
		color: #000;
		padding: 0.75rem 2rem;
		border-radius: 25px;
		font-weight: bold;
		font-size: 1.1rem;
		display: inline-block;
		margin-bottom: 2rem;
		box-shadow: 0 4px 15px rgba(255, 215, 0, 0.4);
		animation: pulse 2s ease-in-out infinite;
	}

	@keyframes pulse {
		0%, 100% { transform: scale(1); }
		50% { transform: scale(1.05); }
	}

	.instruction-card {
		background: white;
		border-radius: 16px;
		padding: 2.5rem;
		margin: 2rem 0;
		box-shadow: 0 8px 32px rgba(0,0,0,0.2);
		text-align: left;
	}

	.importance {
		background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
		padding: 1.5rem;
		border-radius: 12px;
		border-left: 4px solid #667eea;
		margin: 1.5rem 0;
		font-size: 1.05rem;
		line-height: 1.6;
	}

	.clinical-info {
		background: #e3f2fd;
		padding: 1.5rem;
		border-radius: 12px;
		margin: 1.5rem 0;
	}

	.clinical-info h3 {
		color: #1976d2;
		margin: 0 0 1rem 0;
	}

	.clinical-info ul {
		margin: 0;
		padding-left: 1.5rem;
	}

	.clinical-info li {
		margin-bottom: 0.5rem;
		line-height: 1.6;
	}

	.how-it-works {
		margin: 2rem 0;
	}

	.example-demo {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 2rem;
		margin-top: 1rem;
	}

	.example-key, .example-task {
		background: #f8f9fa;
		padding: 1.5rem;
		border-radius: 12px;
		text-align: center;
	}

	.demo-mappings {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 0.75rem;
		margin-top: 1rem;
	}

	.demo-pair {
		background: white;
		padding: 0.75rem;
		border-radius: 8px;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		font-size: 1.2rem;
		font-weight: bold;
	}

	.demo-symbol {
		color: #667eea;
		font-size: 1.5rem;
	}

	.demo-digit {
		color: #4CAF50;
		font-size: 1.3rem;
	}

	.big-symbol {
		font-size: 4rem;
		color: #667eea;
		margin: 1rem 0;
		font-weight: bold;
	}

	.big-digit {
		font-size: 3rem;
		color: #4CAF50;
		font-weight: bold;
		background: #e8f5e9;
		padding: 1rem 2rem;
		border-radius: 12px;
		display: inline-block;
	}

	.test-details {
		margin: 2rem 0;
	}

	.details-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
		margin-top: 1rem;
	}

	.detail-item {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		padding: 1.5rem;
		border-radius: 12px;
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.detail-icon {
		font-size: 2rem;
	}

	.detail-text {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.detail-text strong {
		font-size: 1.1rem;
	}

	.detail-text span {
		font-size: 0.9rem;
		opacity: 0.9;
	}

	.tips {
		background: #fff3cd;
		padding: 1.5rem;
		border-radius: 12px;
		margin: 2rem 0;
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
		line-height: 1.6;
	}

	.performance-guide {
		margin: 2rem 0;
	}

	.norm-scale {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		margin-top: 1rem;
	}

	.norm-item {
		padding: 0.75rem 1rem;
		border-radius: 8px;
		font-weight: 600;
		text-align: center;
	}

	.norm-item.excellent {
		background: linear-gradient(135deg, #4CAF50, #45a049);
		color: white;
	}

	.norm-item.good {
		background: linear-gradient(135deg, #8BC34A, #7CB342);
		color: white;
	}

	.norm-item.average {
		background: linear-gradient(135deg, #FFC107, #FFB300);
		color: #000;
	}

	.norm-item.fair {
		background: linear-gradient(135deg, #FF9800, #FB8C00);
		color: white;
	}

	.norm-item.practice {
		background: linear-gradient(135deg, #f44336, #d32f2f);
		color: white;
	}

	.ready-screen {
		background: white;
		border-radius: 16px;
		padding: 3rem 2rem;
		text-align: center;
		box-shadow: 0 8px 32px rgba(0,0,0,0.2);
	}

	.ready-screen h2 {
		color: #667eea;
		margin-bottom: 1rem;
	}

	.ready-message {
		color: #666;
		font-size: 1.2rem;
		margin-bottom: 2rem;
	}

	.key-display {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
		gap: 1rem;
		margin: 2rem 0;
		max-width: 800px;
		margin-left: auto;
		margin-right: auto;
	}

	.key-pair {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		padding: 1.5rem 1rem;
		border-radius: 12px;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		font-size: 1.3rem;
		font-weight: bold;
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
	}

	.key-symbol {
		font-size: 2rem;
	}

	.key-arrow {
		opacity: 0.7;
	}

	.key-digit {
		font-size: 1.8rem;
	}

	.ready-countdown {
		color: #FF9800;
		font-weight: bold;
		font-size: 1.1rem;
		margin-top: 2rem;
	}

	.testing-screen {
		background: white;
		border-radius: 16px;
		padding: 2rem;
		box-shadow: 0 8px 32px rgba(0,0,0,0.2);
		position: relative;
	}

	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
		flex-wrap: wrap;
		gap: 1rem;
	}

	.progress-info {
		display: flex;
		gap: 0.5rem;
		align-items: center;
	}

	.count-badge, .target-badge {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		padding: 0.5rem 1rem;
		border-radius: 20px;
		font-weight: 600;
		font-size: 0.9rem;
	}

	.timer-display {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		background: #f8f9fa;
		padding: 0.75rem 1.5rem;
		border-radius: 25px;
		box-shadow: 0 2px 8px rgba(0,0,0,0.1);
	}

	.timer-icon {
		font-size: 1.5rem;
	}

	.timer-value {
		font-size: 1.5rem;
		font-weight: bold;
		color: #4CAF50;
		min-width: 60px;
		text-align: center;
	}

	.timer-value.urgent {
		color: #f44336;
		animation: blink 0.5s ease-in-out infinite;
	}

	@keyframes blink {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}

	.reference-key {
		background: #f8f9fa;
		padding: 1rem;
		border-radius: 12px;
		margin-bottom: 2rem;
	}

	.key-label {
		font-weight: 600;
		color: #666;
		margin-bottom: 0.75rem;
		font-size: 0.9rem;
	}

	.key-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
		gap: 0.5rem;
	}

	.key-item {
		background: white;
		padding: 0.5rem;
		border-radius: 8px;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.25rem;
		font-size: 1rem;
		font-weight: 600;
	}

	.ref-symbol {
		color: #667eea;
		font-size: 1.3rem;
	}

	.ref-arrow {
		opacity: 0.5;
		font-size: 0.8rem;
	}

	.ref-digit {
		color: #4CAF50;
		font-size: 1.1rem;
	}

	.test-area {
		text-align: center;
		padding: 2rem 0;
	}

	.task-prompt {
		font-size: 1.2rem;
		color: #666;
		margin-bottom: 1rem;
	}

	.current-symbol {
		font-size: 8rem;
		font-weight: bold;
		color: #667eea;
		margin: 1.5rem 0;
		text-shadow: 3px 3px 6px rgba(0,0,0,0.1);
		animation: symbolPop 0.3s ease-out;
	}

	@keyframes symbolPop {
		0% { transform: scale(0.8); opacity: 0; }
		100% { transform: scale(1); opacity: 1; }
	}

	.input-area {
		margin-top: 2rem;
	}

	.input-instruction {
		color: #666;
		margin-bottom: 1rem;
	}

	.digit-buttons {
		display: flex;
		gap: 0.75rem;
		justify-content: center;
		flex-wrap: wrap;
		max-width: 600px;
		margin: 0 auto;
	}

	.digit-btn {
		width: 70px;
		height: 70px;
		border: 3px solid #667eea;
		background: white;
		border-radius: 12px;
		font-size: 2rem;
		font-weight: bold;
		color: #667eea;
		cursor: pointer;
		transition: all 0.2s;
	}

	.digit-btn:hover {
		background: #667eea;
		color: white;
		transform: scale(1.1);
	}

	.digit-btn:active {
		transform: scale(0.95);
	}

	.progress-bar {
		height: 8px;
		background: #e0e0e0;
		border-radius: 10px;
		overflow: hidden;
		margin-top: 2rem;
	}

	.progress-fill {
		height: 100%;
		background: linear-gradient(90deg, #667eea, #764ba2);
		transition: width 0.3s ease;
		border-radius: 10px;
	}

	.help-button-floating {
		position: absolute;
		top: 1rem;
		right: 1rem;
		width: 45px;
		height: 45px;
		border-radius: 50%;
		border: 2px solid #667eea;
		background: white;
		color: #667eea;
		font-size: 1.5rem;
		font-weight: bold;
		cursor: pointer;
		transition: all 0.3s;
		box-shadow: 0 2px 8px rgba(0,0,0,0.1);
	}

	.help-button-floating:hover {
		background: #667eea;
		color: white;
		transform: scale(1.1);
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

	.performance-badge {
		display: inline-block;
		border: 4px solid;
		border-radius: 16px;
		padding: 1.5rem 3rem;
		margin-bottom: 2rem;
	}

	.perf-level {
		font-size: 2rem;
		font-weight: bold;
		margin-bottom: 0.5rem;
	}

	.perf-score {
		font-size: 1.5rem;
		opacity: 0.9;
	}

	.results-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
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

	.result-card.primary {
		background: linear-gradient(135deg, #4CAF50, #45a049);
		grid-column: span 2;
	}

	.result-icon {
		font-size: 2.5rem;
		margin-bottom: 0.5rem;
	}

	.result-value {
		font-size: 2.5rem;
		font-weight: bold;
		margin-bottom: 0.5rem;
	}

	.result-label {
		font-size: 1rem;
		opacity: 0.95;
		margin-bottom: 0.25rem;
	}

	.result-sublabel {
		font-size: 0.85rem;
		opacity: 0.8;
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

	.breakdown-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
	}

	.breakdown-item {
		display: flex;
		justify-content: space-between;
		padding: 0.75rem;
		background: white;
		border-radius: 8px;
	}

	.breakdown-item .value {
		font-weight: bold;
		color: #667eea;
	}

	.breakdown-item .value.correct {
		color: #4CAF50;
	}

	.breakdown-item .value.incorrect {
		color: #f44336;
	}

	.clinical-context {
		background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
		padding: 1.5rem;
		border-radius: 12px;
		margin: 2rem 0;
		text-align: left;
	}

	.clinical-context h3 {
		color: #667eea;
		margin: 0 0 1rem 0;
	}

	.clinical-context p {
		margin: 0;
		line-height: 1.7;
		color: #555;
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
		flex-wrap: wrap;
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

	.actions button:last-child {
		background: linear-gradient(135deg, #4CAF50, #45a049);
		color: white;
	}

	.actions button:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0,0,0,0.2);
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

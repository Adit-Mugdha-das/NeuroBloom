<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { tasks, training } from '$lib/api';
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
	import {
		formatNumber,
		formatPercent,
		localizeStimulusSymbol,
		locale,
		translateText
	} from '$lib/i18n';
	import { user } from '$lib/stores';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import { getPracticeCopy } from '$lib/task-practice';
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';

	let currentUser = null;
	let stage = 'intro'; // intro, test, results
	let nBackLevel = 1; // Start with 1-back
	let currentTrial = 0;
	let totalTrials = 20;
	
	// Training mode tracking
	let isTrainingMode = false;
	let trainingPlanId = null;
	let trainingDifficulty = 1;
	let taskId = null;
	let sessionComplete = false;
	let completedTasksCount = 0;
	let totalTasksCount = 4;
	
	// Test data
	let letters = [];
	let currentLetter = '';
	let responses = [];
	let reactionTimes = [];
	
	// Results
	let correctHits = 0;
	let misses = 0;
	let falseAlarms = 0;
	let accuracy = 0;
	let meanRT = 0;
	let isPracticeMode = false;
	let practiceStatusMessage = '';
	let showHelp = false;
	let recordedNBackLevel = 1;
	let recordedTotalTrials = 20;
	
	user.subscribe(value => {
		currentUser = value;
		if (!value && browser) {
			goto('/login');
		}
	});

	function t(text) {
		return translateText(text, $locale);
	}

	function n(value, options = {}) {
		return formatNumber(value, $locale, options);
	}

	function pct(value, options = {}) {
		return formatPercent(value, $locale, options);
	}

	function stimulus(value) {
		return localizeStimulusSymbol(value, $locale);
	}

	function nBackLabel(value = nBackLevel) {
		return $locale === 'bn' ? `${n(value)}-ব্যাক` : `${value}-Back`;
	}

	function stepAgoText(value = nBackLevel) {
		if ($locale === 'bn') {
			return `${n(value)} ধাপ আগে`;
		}

		return `${value} step${value > 1 ? 's' : ''} ago`;
	}

	function stepBackText(value = nBackLevel) {
		if ($locale === 'bn') {
			return `${n(value)} ধাপ আগে`;
		}

		return `${value} step${value > 1 ? 's' : ''} back`;
	}

	function previousPositionsText(value = nBackLevel) {
		if ($locale === 'bn') {
			return `${n(value)} অবস্থান আগের`;
		}

		return `${value} position${value > 1 ? 's' : ''} earlier`;
	}

	function completedTasksText() {
		if ($locale === 'bn') {
			return `${n(completedTasksCount)} / ${n(totalTasksCount)} টি টাস্ক সম্পন্ন হয়েছে`;
		}

		return `${completedTasksCount} / ${totalTasksCount} tasks completed`;
	}

	function remainingTasksText() {
		const remainingTasks = totalTasksCount - completedTasksCount;

		if ($locale === 'bn') {
			return `বাকি ${n(remainingTasks)}টি টাস্ক সম্পন্ন করুন`;
		}

		return `Continue to complete remaining ${remainingTasks} task${remainingTasks > 1 ? 's' : ''}`;
	}

	function reactionTimeText(value) {
		if ($locale === 'bn') {
			return `${n(value)} মি.সে.`;
		}

		return `${Math.round(Number(value))}ms`;
	}

	function secondsText(value) {
		if ($locale === 'bn') {
			return `${n(value)} সেকেন্ড`;
		}

		return `${value} seconds`;
	}

	function upgradeMessage(nextLevel) {
		if ($locale === 'bn') {
			return `অসাধারণ পারফরম্যান্স! আপনি ${nBackLabel(nextLevel)} চ্যালেঞ্জের জন্য প্রস্তুত!`;
		}

		return `Outstanding performance! You're ready for ${nextLevel}-Back challenge!`;
	}
	
	onMount(() => {
		// Check if user came from training page
		const urlParams = new URLSearchParams(window.location.search);
		isTrainingMode = urlParams.get('training') === 'true';
		trainingPlanId = parseInt(urlParams.get('planId')) || null;
		trainingDifficulty = parseInt(urlParams.get('difficulty')) || 1;
		taskId = $page.url.searchParams.get('taskId');
		
		if (isTrainingMode && trainingDifficulty > 1) {
			nBackLevel = Math.min(Math.floor(trainingDifficulty / 3) + 1, 3);
		}

		recordedNBackLevel = nBackLevel;
		recordedTotalTrials = totalTrials;
	});
	
	function startTest(practice = false) {
		isPracticeMode = practice;
		practiceStatusMessage = '';
		nBackLevel = practice ? 1 : recordedNBackLevel;
		totalTrials = practice ? 6 : recordedTotalTrials;
		currentTrial = 0;
		responses = [];
		reactionTimes = [];
		correctHits = 0;
		misses = 0;
		falseAlarms = 0;
		accuracy = 0;
		meanRT = 0;
		stage = 'test';
		generateSequence();
		showNextTrial();
	}

	function finishPractice() {
		isPracticeMode = false;
		stage = 'intro';
		currentTrial = 0;
		currentLetter = '';
		responses = [];
		reactionTimes = [];
		nBackLevel = recordedNBackLevel;
		totalTrials = recordedTotalTrials;
		practiceStatusMessage = getPracticeCopy($locale).complete;
	}
	
	function generateSequence() {
		const letterPool = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];
		letters = [];
		
		for (let i = 0; i < totalTrials; i++) {
			if (i >= nBackLevel && Math.random() < 0.3) {
				// 30% chance of match
				letters.push(letters[i - nBackLevel]);
			} else {
				// Random letter
				letters.push(letterPool[Math.floor(Math.random() * letterPool.length)]);
			}
		}
	}
	
	let trialStartTime = 0;
	
	function showNextTrial() {
		if (currentTrial >= totalTrials) {
			calculateResults();
			return;
		}
		
		currentLetter = letters[currentTrial];
		trialStartTime = Date.now();
		
		// Auto-advance after 2 seconds
		setTimeout(() => {
			if (responses.length === currentTrial) {
				// User didn't respond
				responses.push(false);
				reactionTimes.push(2000);
			}
			currentTrial++;
			showNextTrial();
		}, 2000);
	}
	
	function handleResponse(isMatch) {
		if (responses.length > currentTrial) return; // Already responded
		
		const rt = Date.now() - trialStartTime;
		responses.push(isMatch);
		reactionTimes.push(rt);
	}
	
	function calculateResults() {
		correctHits = 0;
		misses = 0;
		falseAlarms = 0;
		
		for (let i = 0; i < totalTrials; i++) {
			const isActualMatch = i >= nBackLevel && letters[i] === letters[i - nBackLevel];
			const userSaidMatch = responses[i];
			
			if (isActualMatch && userSaidMatch) {
				correctHits++;
			} else if (isActualMatch && !userSaidMatch) {
				misses++;
			} else if (!isActualMatch && userSaidMatch) {
				falseAlarms++;
			}
		}
		
		const totalTargets = correctHits + misses;
		accuracy = totalTargets > 0 ? (correctHits / totalTargets) * 100 : 0;
		
		const validRTs = reactionTimes.filter(rt => rt < 2000);
		meanRT = validRTs.length > 0 ? validRTs.reduce((a, b) => a + b, 0) / validRTs.length : 0;
		
		if (isPracticeMode) {
			finishPractice();
			return;
		}

		stage = 'results';
		saveResults();
	}
	
	async function saveResults() {
		try {
			const rtStd = calculateStd(reactionTimes.filter(rt => rt < 2000));
			const rawData = {
				nBackLevel,
				total_trials: totalTrials,
				correct_hits: correctHits,
				misses,
				false_alarms: falseAlarms,
				reaction_times: reactionTimes,
				mean_rt: meanRT,
				rt_std: rtStd
			};
			
			if (isTrainingMode && trainingPlanId) {
				// Submit to training session API
				const consistencyScore = rtStd > 0 ? Math.max(0, 100 - (rtStd / 10)) : 100;
				
				const result = await training.submitSession({
					user_id: currentUser.id,
					training_plan_id: trainingPlanId,
					domain: 'working_memory',
					task_type: 'n_back',
					score: accuracy,
					accuracy: accuracy,
					average_reaction_time: meanRT,
					consistency: consistencyScore,
					errors: misses + falseAlarms,
					session_duration: Math.floor((totalTrials * 2000) / 60),
					raw_data: rawData,
					task_id: taskId
				});
				
				// Update session status
				sessionComplete = result.session_complete;
				completedTasksCount = result.completed_tasks;
				totalTasksCount = result.total_tasks;
			} else {
				// Submit to regular task result API (baseline mode)
				await tasks.submitResult(
					currentUser.id,
					'working_memory',
					accuracy,
					JSON.stringify(rawData)
				);
			}
		} catch (error) {
			console.error('Error saving results:', error);
		}
	}
	
	function calculateStd(arr) {
		if (arr.length === 0) return 0;
		const mean = arr.reduce((a, b) => a + b, 0) / arr.length;
		const variance = arr.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / arr.length;
		return Math.sqrt(variance);
	}
	
	function backToDashboard() {
		if (isTrainingMode) {
			goto('/training');
		} else {
			goto('/dashboard');
		}
	}
</script>

<div class="test-container" data-localize-skip>
<div class="test-inner">
	{#if stage === 'intro'}

		<!-- Header Card -->
		<div class="nb-header-card">
			<div class="nb-header-content">
				<div class="nb-header-text">
					<h1 class="nb-task-title">{t('N-Back Test')}</h1>
					<p class="nb-task-domain">{t('Working Memory · Continuous Updating')}</p>
				</div>
				<DifficultyBadge difficulty={trainingDifficulty} domain="Working Memory" />
			</div>
		</div>

		<!-- Task Concept Card -->
		<div class="nb-card nb-task-concept">
			<div class="nb-concept-badge">
				<span class="nb-badge-label">{t('N-Back Paradigm')}</span>
				<span>{t('Kirchner, 1958 · MS Research Gold Standard')}</span>
			</div>
			<p class="nb-concept-desc">
				{#if $locale === 'bn'}
					{`একটি একটি করে অক্ষর দেখানো হবে। প্রতিটি অক্ষর দেখে বলুন এটি ${stepBackText()} আগের অক্ষরের সাথে মিলে কিনা।`}
				{:else}
					{`Letters appear one at a time. For each letter, decide whether it matches the one from ${nBackLevel} step${nBackLevel > 1 ? 's' : ''} ago. The task continuously updates what you must hold in working memory, making it sensitive to MS-related cognitive changes.`}
				{/if}
			</p>
		</div>

		<!-- Match / No Match Card -->
		<div class="nb-card">
			<h2 class="nb-section-title">{t('How to Respond')}</h2>
			<div class="nb-instructions-grid">
				<div class="nb-instruction-item">
					<div class="nb-icon nb-match-icon">✓</div>
					<h3>{t('Match')}</h3>
					<p>
						{#if $locale === 'bn'}
							{`বর্তমান অক্ষরটি ${stepBackText()} আগের অক্ষরের মতো হলে Match চাপুন`}
						{:else}
							{`Press Match if the current letter is the same as the one from ${stepAgoText()}`}
						{/if}
					</p>
					<div class="nb-example">
						<div class="nb-example-label">{t('You see:')}</div>
						<div class="nb-example-sequence">
							{stimulus('A')} → {stimulus('B')} → <span class="nb-ex-match">{stimulus('A')}</span>
						</div>
						<div class="nb-example-label">{t('At position 3:')}</div>
						<div class="nb-example-result nb-match-result">✓ {t('Match!')}</div>
					</div>
				</div>
				<div class="nb-instruction-item">
					<div class="nb-icon nb-no-match-icon">✗</div>
					<h3>{t('No Match')}</h3>
					<p>
						{#if $locale === 'bn'}
							{`বর্তমান অক্ষরটি ভিন্ন হলে No Match চাপুন`}
						{:else}
							{`Press No Match if the letter is different from ${stepAgoText()}`}
						{/if}
					</p>
					<div class="nb-example">
						<div class="nb-example-label">{t('You see:')}</div>
						<div class="nb-example-sequence">
							{stimulus('A')} → {stimulus('B')} → <span class="nb-ex-no-match">{stimulus('C')}</span>
						</div>
						<div class="nb-example-label">{t('At position 3:')}</div>
						<div class="nb-example-result nb-no-match-result">✗ {t('No Match')}</div>
					</div>
				</div>
			</div>
		</div>

		<!-- Info Grid -->
		<div class="nb-info-grid">
			<!-- Tips -->
			<div class="nb-card">
				<h3 class="nb-card-title">{t('Tips for Success')}</h3>
				<div class="nb-tips-list">
					<div class="nb-tip-item">✓ <strong>{t('Stay focused:')}</strong> {t('Maintain attention continuously across all trials')}</div>
					<div class="nb-tip-item">✓ <strong>{t('Use rhythm:')}</strong> {t('Letters appear at a steady pace — use it to pace yourself')}</div>
					<div class="nb-tip-item">✓ <strong>{t('Trust instinct:')}</strong> {t("Don't overthink — your first impression is usually right")}</div>
					<div class="nb-tip-item">✓ <strong>{t('Relax:')}</strong> {t('Stress reduces memory — breathe steadily between trials')}</div>
				</div>
			</div>
			<!-- Session Details -->
			<div class="nb-card">
				<h3 class="nb-card-title">{t('Session Info')}</h3>
				<div class="nb-details-list">
					<div class="nb-detail-row">
						<span>{t('Difficulty')}</span>
						<strong>{nBackLabel()}</strong>
					</div>
					<div class="nb-detail-row">
						<span>{t('Total Trials')}</span>
						<strong>{n(totalTrials)} {t('letters')}</strong>
					</div>
					<div class="nb-detail-row">
						<span>{t('Time per Letter')}</span>
						<strong>{secondsText(2)}</strong>
					</div>
					<div class="nb-detail-row">
						<span>{t('Response Window')}</span>
						<strong>{t('While letter is shown')}</strong>
					</div>
				</div>
			</div>
		</div>

		<!-- Clinical Basis Card -->
		<div class="nb-clinical-info">
			<div class="nb-clinical-header">
				<div class="nb-clinical-badge">{t('Clinical Basis')}</div>
				<h3>{t('Gold Standard Working Memory Assessment')}</h3>
			</div>
			<p>
				{t('The N-Back task (Kirchner, 1958) is one of the most widely used paradigms in cognitive neuroscience for measuring working memory updating. In MS, N-Back performance sensitively tracks white matter lesion burden and processing speed deficits, making it a key measure in longitudinal cognitive monitoring protocols.')}
			</p>
		</div>

		<TaskPracticeActions
			locale={$locale}
			startLabel={t('Start Test')}
			statusMessage={practiceStatusMessage}
			on:start={() => startTest(false)}
			on:practice={() => startTest(true)}
		/>

		<div style="text-align:center; margin-top: 0.5rem;">
			<button class="nb-btn-back" on:click={backToDashboard}>← {t('Back to Dashboard')}</button>
		</div>
	{:else if stage === 'test'}
		<div class="test-card test-active">
			{#if isPracticeMode}
				<PracticeModeBanner locale={$locale} />
			{/if}
			<div class="progress-bar">
				<div class="progress-fill" style="width: {(currentTrial / totalTrials) * 100}%"></div>
			</div>
			
			<div class="timer">
				{t('Trial')} {n(currentTrial + 1)} {t('of')} {n(totalTrials)}
			</div>
			
			<div class="task-reminder">
				{#if $locale === 'bn'}
					{'এই অক্ষরটি কি '}<strong>{stepBackText()}</strong>{' অক্ষরের সাথে মেলে?'}
				{:else}
					{t('Does this letter match the one from')} <strong>{stepBackText()}</strong>?
				{/if}
			</div>
			
			<div class="word-display">
				{stimulus(currentLetter)}
			</div>
			
			<div class="button-group">
				<button 
					class="btn-primary btn-match" 
					on:click={() => handleResponse(true)}
				>
					<span class="btn-icon">✓</span>
					<span class="btn-text">{t('Match')}</span>
				</button>
				<button 
					class="btn-secondary btn-no-match" 
					on:click={() => handleResponse(false)}
				>
					<span class="btn-icon">✗</span>
					<span class="btn-text">{t('No Match')}</span>
				</button>
			</div>
			
			<div class="help-text">
				{#if $locale === 'bn'}
					{`মনে রাখুন: ${previousPositionsText()} অক্ষরের সাথে তুলনা করুন`}
				{:else}
					{t('Remember:')} {previousPositionsText()}
				{/if}
			</div>
		</div>
	
	{:else if stage === 'results'}
		<div class="test-card">
			<h1>🎉 {t('Test Complete!')}</h1>
			
			{#if isTrainingMode}
				<div class="training-progress-banner">
					<p class="progress-label">{t('Training Progress:')}</p>
					<p class="progress-value">{completedTasksText()}</p>
					{#if sessionComplete}
						<div class="session-complete-msg">
							🎊 {t('Session Complete! All tasks finished!')}
						</div>
					{:else}
						<div class="session-incomplete-msg">
							{remainingTasksText()}
						</div>
					{/if}
				</div>
			{/if}
			
			<div class="score-display">
				{pct(accuracy, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}
			</div>
			
			<div class="performance-label">
				{#if accuracy >= 90}
					<span class="badge excellent">🌟 {t('Excellent!')}</span>
				{:else if accuracy >= 75}
					<span class="badge good">👍 {t('Good Job!')}</span>
				{:else if accuracy >= 60}
					<span class="badge fair">👌 {t('Fair')}</span>
				{:else}
					<span class="badge needs-practice">💪 {t('Keep Practicing!')}</span>
				{/if}
			</div>
			
			<div class="result-details">
				<div class="result-item">
					<span class="result-icon">✓</span>
					<div class="result-info">
						<span class="result-label">{t('Correct Hits')}</span>
						<strong class="result-value">{n(correctHits)}</strong>
					</div>
				</div>
				<div class="result-item">
					<span class="result-icon">⊘</span>
					<div class="result-info">
						<span class="result-label">{t('Misses')}</span>
						<strong class="result-value">{n(misses)}</strong>
					</div>
				</div>
				<div class="result-item">
					<span class="result-icon">⚠</span>
					<div class="result-info">
						<span class="result-label">{t('False Alarms')}</span>
						<strong class="result-value">{n(falseAlarms)}</strong>
					</div>
				</div>
				<div class="result-item">
					<span class="result-icon">⚡</span>
					<div class="result-info">
						<span class="result-label">{t('Avg Reaction Time')}</span>
						<strong class="result-value">{reactionTimeText(meanRT.toFixed(0))}</strong>
					</div>
				</div>
				<div class="result-item">
					<span class="result-icon">🎯</span>
					<div class="result-info">
						<span class="result-label">{t('Difficulty Level')}</span>
						<strong class="result-value">{nBackLabel()}</strong>
					</div>
				</div>
			</div>
			
			{#if accuracy > 80 && nBackLevel < 3}
				<div class="upgrade-notice">
					<p>🚀 {upgradeMessage(nBackLevel + 1)}</p>
				</div>
			{/if}
			
			<div class="button-group">
				<button class="btn-primary btn-large" on:click={backToDashboard}>
					✓ {t('Done - Back to Dashboard')}
				</button>
			</div>
		</div>
	{/if}
</div>
</div>

<style>
	.test-container {
		min-height: 100vh;
		background: #C8DEFA;
		padding: 1.5rem;
	}

	.test-inner {
		max-width: 1100px;
		margin: 0 auto;
	}

	.test-card {
		background: white;
		border-radius: 24px;
		padding: 3rem;
		max-width: 900px;
		width: 100%;
		box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
		text-align: center;
		position: relative;
	}

	.test-active {
		max-width: 700px;
	}

	h1 {
		color: #667eea;
		font-size: 2.5rem;
		margin-bottom: 0.5rem;
		font-weight: 700;
	}

	/* Progress Bar */
	.progress-bar {
		width: 100%;
		height: 8px;
		background: #e0e0e0;
		border-radius: 10px;
		overflow: hidden;
		margin-bottom: 1.5rem;
	}

	.progress-fill {
		height: 100%;
		background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
		transition: width 0.3s ease;
	}

	.timer {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		padding: 0.75rem 1.5rem;
		border-radius: 50px;
		font-size: 1.1rem;
		font-weight: 600;
		display: inline-block;
		margin-bottom: 1.5rem;
		box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
	}

	.task-reminder {
		color: #764ba2;
		font-size: 1.2rem;
		margin-bottom: 1.5rem;
		font-weight: 600;
	}

	.task-reminder strong {
		color: #667eea;
	}

	.word-display {
		font-size: 10rem;
		font-weight: 700;
		color: #667eea;
		margin: 2rem 0;
		min-height: 180px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: linear-gradient(135deg, #f0f7ff 0%, #e8f0fe 100%);
		border-radius: 20px;
		box-shadow: inset 0 4px 20px rgba(102, 126, 234, 0.1);
		animation: letterPulse 0.3s ease;
		letter-spacing: 0.05em;
		border: 3px solid #667eea;
	}

	@keyframes letterPulse {
		0% {
			transform: scale(0.8);
			opacity: 0;
		}
		50% {
			transform: scale(1.05);
		}
		100% {
			transform: scale(1);
			opacity: 1;
		}
	}

	.help-text {
		color: #999;
		font-size: 0.95rem;
		margin-top: 1.5rem;
		font-style: italic;
	}

	/* Results */
	.score-display {
		font-size: 6rem;
		font-weight: 700;
		background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
		margin: 1rem 0;
	}

	.performance-label {
		margin: 1rem 0 2rem;
	}

	.badge {
		display: inline-block;
		padding: 0.75rem 2rem;
		border-radius: 50px;
		font-size: 1.2rem;
		font-weight: 700;
	}

	.badge.excellent {
		background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
		color: white;
	}

	.badge.good {
		background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
		color: white;
	}

	.badge.fair {
		background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
		color: white;
	}

	.badge.needs-practice {
		background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
		color: white;
	}

	.result-details {
		background: #f8f9fa;
		border-radius: 16px;
		padding: 2rem;
		margin: 2rem 0;
	}

	.result-item {
		display: flex;
		align-items: center;
		gap: 1.5rem;
		padding: 1rem;
		border-bottom: 1px solid #e0e0e0;
	}

	.result-item:last-child {
		border-bottom: none;
	}

	.result-icon {
		font-size: 2rem;
		width: 50px;
		text-align: center;
		flex-shrink: 0;
	}

	.result-info {
		flex: 1;
		display: flex;
		justify-content: space-between;
		align-items: center;
		text-align: left;
	}

	.result-label {
		color: #666;
		font-size: 1.1rem;
		font-weight: 500;
	}

	.result-value {
		color: #667eea;
		font-size: 1.5rem;
		font-weight: 700;
	}

	.upgrade-notice {
		background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
		color: white;
		padding: 1.5rem;
		border-radius: 16px;
		margin: 2rem 0;
	}

	.upgrade-notice p {
		margin: 0;
		font-size: 1.2rem;
		font-weight: 600;
	}
	
	/* Training Progress Banner */
	.training-progress-banner {
		background: linear-gradient(135deg, #f0f7ff 0%, #e8f0fe 100%);
		border: 2px solid #667eea;
		border-radius: 16px;
		padding: 1.5rem;
		margin: 1.5rem 0;
	}
	
	.progress-label {
		color: #764ba2;
		font-weight: 600;
		font-size: 0.9rem;
		margin: 0 0 0.5rem 0;
	}
	
	.progress-value {
		color: #667eea;
		font-weight: 700;
		font-size: 1.3rem;
		margin: 0 0 1rem 0;
	}
	
	.session-complete-msg {
		background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
		color: white;
		padding: 1rem;
		border-radius: 12px;
		font-weight: 600;
		animation: celebrate 0.5s ease;
	}
	
	.session-incomplete-msg {
		background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
		color: white;
		padding: 1rem;
		border-radius: 12px;
		font-weight: 600;
	}

	/* Buttons */
	.button-group {
		margin-top: 2rem;
		display: flex;
		gap: 1rem;
		justify-content: center;
		flex-wrap: wrap;
	}


	.btn-primary {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		padding: 1rem 2.5rem;
		border-radius: 50px;
		font-size: 1.1rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s ease;
		box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.btn-primary:hover {
		transform: translateY(-2px);
		box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
	}

	.btn-primary:active {
		transform: translateY(0);
	}

	.btn-large {
		padding: 1.25rem 3rem;
		font-size: 1.2rem;
	}

	.btn-match {
		background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
		box-shadow: 0 4px 15px rgba(76, 175, 80, 0.4);
	}

	.btn-match:hover {
		box-shadow: 0 6px 20px rgba(76, 175, 80, 0.5);
	}

	.btn-secondary {
		background: white;
		color: #f44336;
		border: 2px solid #f44336;
		padding: 1rem 2.5rem;
		border-radius: 50px;
		font-size: 1.1rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s ease;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.btn-secondary:hover {
		background: #f44336;
		color: white;
		transform: translateY(-2px);
		box-shadow: 0 6px 20px rgba(244, 67, 54, 0.3);
	}

	.btn-no-match {
		background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
		color: white;
		border: none;
		box-shadow: 0 4px 15px rgba(244, 67, 54, 0.4);
	}

	.btn-no-match:hover {
		box-shadow: 0 6px 20px rgba(244, 67, 54, 0.5);
	}

	.btn-icon {
		font-size: 1.5rem;
	}

	.btn-text {
		font-size: 1.1rem;
	}

	/* ── Intro Multi-Card Layout (matches visual-search pattern) ── */

	.nb-header-card {
		background: white;
		border-radius: 16px;
		padding: 1.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
		margin-bottom: 1rem;
	}

	.nb-header-content {
		display: flex;
		align-items: center;
		justify-content: space-between;
		flex-wrap: wrap;
		gap: 1rem;
	}

	.nb-task-title {
		font-size: 1.75rem;
		font-weight: 700;
		color: #1a1a2e;
		margin: 0 0 0.25rem 0;
	}

	.nb-task-domain {
		font-size: 0.875rem;
		color: #1e40af;
		font-weight: 500;
		margin: 0;
	}

	.nb-card {
		background: white;
		border-radius: 16px;
		padding: 1.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
		margin-bottom: 1rem;
	}

	.nb-task-concept { margin-bottom: 1rem; }

	.nb-concept-badge {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
		color: white;
		padding: 0.4rem 0.9rem;
		border-radius: 2rem;
		font-size: 0.813rem;
		font-weight: 600;
		margin-bottom: 1rem;
	}

	.nb-badge-label { font-weight: 700; letter-spacing: 0.04em; }

	.nb-concept-desc {
		color: #4b5563;
		font-size: 0.938rem;
		line-height: 1.6;
		margin: 0;
	}

	.nb-section-title {
		font-size: 1.125rem;
		font-weight: 600;
		color: #1a1a2e;
		margin: 0 0 1rem 0;
	}

	.nb-card-title {
		font-size: 1rem;
		font-weight: 700;
		color: #1a1a2e;
		margin: 0 0 1rem 0;
	}

	.nb-instructions-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.5rem;
	}

	.nb-instruction-item {
		border: 1px solid #e5e7eb;
		border-radius: 12px;
		padding: 1.25rem;
		background: #fafafa;
	}

	.nb-icon {
		font-size: 2rem;
		font-weight: 700;
		margin-bottom: 0.75rem;
		display: block;
	}

	.nb-match-icon { color: #16a34a; }
	.nb-no-match-icon { color: #dc2626; }

	.nb-instruction-item h3 {
		font-size: 1.05rem;
		font-weight: 700;
		margin: 0 0 0.4rem 0;
		color: #1a1a2e;
	}

	.nb-instruction-item p {
		color: #4b5563;
		font-size: 0.9rem;
		margin: 0 0 1rem 0;
		line-height: 1.5;
	}

	.nb-example {
		background: white;
		border-radius: 8px;
		padding: 0.875rem;
		border: 1px solid #e5e7eb;
	}

	.nb-example-label {
		color: #9ca3af;
		font-size: 0.78rem;
		margin-bottom: 0.25rem;
	}

	.nb-example-sequence {
		font-weight: 600;
		color: #374151;
		font-size: 1rem;
		margin-bottom: 0.5rem;
	}

	.nb-ex-match { color: #16a34a; font-weight: 700; }
	.nb-ex-no-match { color: #dc2626; font-weight: 700; }

	.nb-example-result {
		font-weight: 700;
		font-size: 0.875rem;
		padding: 0.25rem 0.75rem;
		border-radius: 6px;
		display: inline-block;
	}

	.nb-match-result { background: #dcfce7; color: #16a34a; }
	.nb-no-match-result { background: #fee2e2; color: #dc2626; }

	.nb-info-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
		margin-bottom: 0;
	}

	.nb-info-grid .nb-card { margin-bottom: 1rem; }

	.nb-tips-list {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	.nb-tip-item {
		font-size: 0.9rem;
		color: #374151;
		line-height: 1.5;
	}

	.nb-tip-item strong { color: #1e40af; }

	.nb-details-list {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.nb-detail-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		font-size: 0.9rem;
		padding: 0.5rem 0;
		border-bottom: 1px solid #f3f4f6;
	}

	.nb-detail-row:last-child { border-bottom: none; }
	.nb-detail-row span { color: #6b7280; }
	.nb-detail-row strong { color: #1a1a2e; }

	.nb-clinical-info {
		background: white;
		border-radius: 16px;
		padding: 1.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
		margin-bottom: 1rem;
	}

	.nb-clinical-header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 0.75rem;
	}

	.nb-clinical-badge {
		display: inline-flex;
		background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
		color: white;
		padding: 0.3rem 0.8rem;
		border-radius: 2rem;
		font-size: 0.8rem;
		font-weight: 600;
		white-space: nowrap;
	}

	.nb-clinical-header h3 {
		font-size: 1rem;
		font-weight: 600;
		color: #1a1a2e;
		margin: 0;
	}

	.nb-clinical-info p {
		color: #4b5563;
		font-size: 0.9rem;
		line-height: 1.6;
		margin: 0;
	}

	.nb-btn-back {
		background: transparent;
		color: #6b7280;
		border: none;
		padding: 0.5rem 1rem;
		font-size: 0.9rem;
		cursor: pointer;
		transition: color 0.2s;
	}

	.nb-btn-back:hover { color: #1e40af; }

	@media (max-width: 768px) {
		.test-card {
			padding: 2rem 1.5rem;
		}

		h1 {
			font-size: 2rem;
		}

		.word-display {
			font-size: 6rem;
			margin: 1.5rem 0;
			min-height: 140px;
		}

		.score-display {
			font-size: 4rem;
		}

		.button-group {
			flex-direction: column;
		}

		.btn-primary,
		.btn-secondary {
			width: 100%;
			justify-content: center;
		}

		.nb-instructions-grid,
		.nb-info-grid {
			grid-template-columns: 1fr;
		}
	}
</style>

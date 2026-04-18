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
	let recordedNBackLevel = 1;
	let recordedTotalTrials = 20;
	let trialTimeout = null;
	
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

	function exampleSequence(value = nBackLevel) {
		switch (value) {
			case 1:
				return ['A', 'B', 'B'];
			case 2:
				return ['A', 'B', 'A'];
			default:
				return ['A', 'B', 'C', 'A'];
		}
	}

	function exampleMatchPosition(value = nBackLevel) {
		return exampleSequence(value).length - value;
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

	function finishPractice(completed = false) {
		clearTimeout(trialTimeout);
		isPracticeMode = false;
		stage = 'intro';
		currentTrial = 0;
		currentLetter = '';
		responses = [];
		reactionTimes = [];
		nBackLevel = recordedNBackLevel;
		totalTrials = recordedTotalTrials;
		practiceStatusMessage = completed ? getPracticeCopy($locale).complete : '';
	}

	function leavePractice() {
		finishPractice(false);
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
		clearTimeout(trialTimeout);
		trialTimeout = setTimeout(() => {
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
			finishPractice(true);
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

<div class="wm-container" class:intro-layout={stage === 'intro'} data-localize-skip>
	{#if stage === 'intro'}
		<div class="page-content">
			<div class="task-header">
				<button class="back-btn" on:click={backToDashboard}>
					{isTrainingMode ? t('Back to Training') : t('Back to Dashboard')}
				</button>
				<h1 class="task-title">{t('Working Memory Test')}</h1>
			</div>

			<div class="concept-card">
				<div class="concept-badge">{nBackLabel()} - {t('Baseline Assessment')}</div>
				<h2>{t('Hold the recent letters in mind while new ones appear')}</h2>
				<p>
					{t('This task measures working memory updating and focused attention.')}
					{` `}
					{t('For this round, compare each new letter with the one from')}
					{` `}
					<strong>{stepAgoText()}</strong>.
				</p>
			</div>

			<div class="rules-card">
				<h3>{t('How It Works')}</h3>
				<ol class="rules-list">
					<li>{t('A single letter appears in the center of the screen.')}</li>
					<li>
						{t('Each letter stays visible for')}
						{` `}
						<strong>{secondsText(2)}</strong>.
					</li>
					<li>
						{t('Decide whether it matches the letter from')}
						{` `}
						<strong>{stepAgoText()}</strong>.
					</li>
					<li>{t('Choose Match for a repeat and No Match for a different letter.')}</li>
				</ol>

				<div class="response-keys">
					<div class="response-pill response-pill-match">
						<div class="pill-label">{t('Match')}</div>
						<div class="pill-copy">
							{t('Use this when the current letter is the same as the one from')}
							{` `}
							{stepAgoText()}.
						</div>
					</div>
					<div class="response-pill response-pill-miss">
						<div class="pill-label">{t('No Match')}</div>
						<div class="pill-copy">{t('Use this when the current letter is different from the earlier one.')}</div>
					</div>
				</div>

				<div class="example-panel">
					<div class="card-kicker">{t('Example')}</div>
					<h4>{nBackLabel()} {t('match walkthrough')}</h4>
					<div class="example-sequence">
						{#each exampleSequence() as letter, index}
							<div
								class="example-item"
								class:is-match-anchor={index + 1 === exampleMatchPosition()}
								class:is-current={index === exampleSequence().length - 1}
							>
								<span class="example-position">{t('Position')} {n(index + 1)}</span>
								<span class="example-letter">{stimulus(letter)}</span>
								{#if index + 1 === exampleMatchPosition()}
									<span class="example-tag">{t('Earlier match')}</span>
								{:else if index === exampleSequence().length - 1}
									<span class="example-tag current-tag">{t('Current')}</span>
								{/if}
							</div>
							{#if index < exampleSequence().length - 1}
								<div class="example-arrow">&rarr;</div>
							{/if}
						{/each}
					</div>
					<p class="example-caption">
						{t('The last letter matches the one from')}
						{` `}
						<strong>{stepAgoText()}</strong>
						{`, `}
						{t('so the correct response here is Match.')}
					</p>
				</div>
			</div>

			<div class="info-grid">
				<div class="info-card">
					<div class="info-label">{t('Difficulty')}</div>
					<div class="info-value">{nBackLabel()}</div>
					<p class="info-detail">
						{t('Every choice compares the current letter to the one from')}
						{` `}
						{stepAgoText()}.
					</p>
				</div>
				<div class="info-card">
					<div class="info-label">{t('Total Trials')}</div>
					<div class="info-value">{n(totalTrials)}</div>
					<p class="info-detail">{t('A longer run helps measure consistency across the full task.')}</p>
				</div>
				<div class="info-card">
					<div class="info-label">{t('Time per Letter')}</div>
					<div class="info-value">{secondsText(2)}</div>
					<p class="info-detail">{t('Stay ready, because the sequence advances automatically.')}</p>
				</div>
			</div>

			<div class="tip-card">
				<div class="tip-title">{t('Strategy')}</div>
				<p>{t('Keep a short rolling memory of the latest letters. Refresh that mini-sequence every time a new letter appears, and avoid guessing when you are unsure.')}</p>
			</div>

			<div class="clinical-card">
				<h3>{t('Clinical Basis')}</h3>
				<p>{t('N-back performance reflects working memory updating, attention control, and the ability to keep relevant information active while new stimuli compete for focus. In multiple sclerosis, weaker accuracy or slower responses can reflect disruption in the fronto-parietal networks that support online information maintenance.')}</p>
			</div>

			<TaskPracticeActions
				locale={$locale}
				startLabel={t('Start Actual Test')}
				statusMessage={practiceStatusMessage}
				on:start={() => startTest(false)}
				on:practice={() => startTest(true)}
			/>
		</div>
	{:else if stage === 'test'}
		<div class="test-card test-active">
			{#if isPracticeMode}
				<PracticeModeBanner locale={$locale} showExit on:exit={leavePractice} />
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

<style>
	.wm-container {
		min-height: 100vh;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 2rem;
	}

	.wm-container.intro-layout {
		background: #c8defa;
		display: block;
		padding: 2rem;
	}

	.page-content {
		max-width: 960px;
		margin: 0 auto;
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	.task-header {
		display: flex;
		align-items: center;
		gap: 1.25rem;
		flex-wrap: wrap;
	}

	.back-btn {
		background: white;
		color: #0e7490;
		border: 2px solid #0e7490;
		padding: 0.6rem 1.25rem;
		border-radius: 10px;
		cursor: pointer;
		font-size: 0.95rem;
		font-weight: 600;
		white-space: nowrap;
		transition: background 0.2s ease, color 0.2s ease, transform 0.2s ease;
	}

	.back-btn:hover {
		background: #0e7490;
		color: white;
		transform: translateY(-1px);
	}

	.task-title {
		font-size: 1.9rem;
		font-weight: 700;
		color: #164e63;
		margin: 0;
	}

	.concept-card,
	.rules-card,
	.tip-card,
	.clinical-card {
		background: white;
		border-radius: 18px;
		padding: 2rem;
		box-shadow: 0 4px 14px rgba(15, 23, 42, 0.08);
	}

	.concept-badge {
		display: inline-block;
		background: #cffafe;
		color: #0e7490;
		font-size: 0.82rem;
		font-weight: 700;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		padding: 0.35rem 0.9rem;
		border-radius: 999px;
		margin-bottom: 0.9rem;
	}

	.concept-card h2,
	.rules-card h3,
	.clinical-card h3,
	.example-panel h4 {
		margin: 0;
		color: #164e63;
		font-weight: 700;
	}

	.concept-card h2 {
		font-size: 1.45rem;
		margin-bottom: 0.8rem;
	}

	.rules-card h3,
	.clinical-card h3 {
		font-size: 1.12rem;
		margin-bottom: 1rem;
	}

	.concept-card p,
	.rules-list,
	.pill-copy,
	.example-caption,
	.info-detail,
	.tip-card p,
	.clinical-card p {
		margin: 0;
		color: #334155;
		line-height: 1.68;
	}

	.rules-list {
		padding-left: 1.3rem;
		margin-top: 1.1rem;
	}

	.rules-list li + li {
		margin-top: 0.75rem;
	}

	.response-keys {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
		gap: 1rem;
		margin-top: 1.5rem;
	}

	.response-pill {
		border-radius: 16px;
		padding: 1rem 1.1rem;
		border: 1px solid transparent;
	}

	.response-pill-match {
		background: #ecfdf5;
		border-color: #86efac;
	}

	.response-pill-miss {
		background: #fef2f2;
		border-color: #fca5a5;
	}

	.pill-label {
		font-size: 0.95rem;
		font-weight: 700;
		margin-bottom: 0.35rem;
	}

	.response-pill-match .pill-label {
		color: #166534;
	}

	.response-pill-miss .pill-label {
		color: #b91c1c;
	}

	.example-panel {
		margin-top: 1.5rem;
		padding: 1.35rem;
		border-radius: 16px;
		background: linear-gradient(135deg, #f8fbff 0%, #eef6ff 100%);
		border: 1px solid #bfdbfe;
	}

	.card-kicker {
		font-size: 0.78rem;
		font-weight: 700;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		color: #2563eb;
		margin-bottom: 0.45rem;
	}

	.example-panel h4 {
		font-size: 1.08rem;
		margin-bottom: 1rem;
	}

	.example-sequence {
		display: flex;
		align-items: stretch;
		justify-content: center;
		gap: 0.75rem;
		flex-wrap: wrap;
	}

	.example-item {
		min-width: 112px;
		padding: 0.95rem;
		border-radius: 14px;
		background: white;
		border: 1px solid #dbeafe;
		text-align: center;
		box-shadow: 0 4px 12px rgba(37, 99, 235, 0.08);
	}

	.example-item.is-match-anchor {
		border-color: #0e7490;
		background: #ecfeff;
	}

	.example-item.is-current {
		border-color: #7c3aed;
		background: #f5f3ff;
	}

	.example-position,
	.example-tag {
		display: block;
		font-size: 0.8rem;
		font-weight: 600;
	}

	.example-position {
		color: #64748b;
		margin-bottom: 0.45rem;
	}

	.example-letter {
		display: block;
		font-size: 2.25rem;
		font-weight: 700;
		color: #2563eb;
	}

	.example-tag {
		margin-top: 0.55rem;
		color: #0f766e;
	}

	.current-tag {
		color: #6d28d9;
	}

	.example-arrow {
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.4rem;
		font-weight: 700;
		color: #64748b;
	}

	.example-caption {
		margin-top: 1rem;
	}

	.info-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		gap: 1rem;
	}

	.info-card {
		background: white;
		border-radius: 18px;
		padding: 1.35rem;
		box-shadow: 0 4px 14px rgba(15, 23, 42, 0.08);
		border: 1px solid #dbeafe;
	}

	.info-label {
		display: block;
		font-size: 0.82rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: #64748b;
		margin-bottom: 0.45rem;
	}

	.info-value {
		display: block;
		font-size: 1.4rem;
		font-weight: 700;
		color: #1d4ed8;
		margin-bottom: 0.45rem;
	}

	.info-detail {
		font-size: 0.96rem;
	}

	.tip-title {
		font-size: 1rem;
		font-weight: 700;
		color: #0f766e;
		margin-bottom: 0.55rem;
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

	.test-card h1 {
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

	@media (max-width: 768px) {
		.wm-container,
		.wm-container.intro-layout {
			padding: 1rem;
		}

		.test-card,
		.concept-card,
		.rules-card,
		.tip-card,
		.clinical-card {
			padding: 1.5rem;
		}

		.task-header {
			align-items: flex-start;
		}

		.task-title,
		.test-card h1 {
			font-size: 2rem;
		}

		.rules-list {
			padding-left: 1.1rem;
		}

		.response-keys,
		.info-grid {
			grid-template-columns: 1fr;
		}

		.example-sequence {
			flex-direction: column;
		}

		.example-arrow {
			transform: rotate(90deg);
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
	}
</style>

<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { tasks, training } from '$lib/api';
	import {
		formatNumber,
		formatPercent,
		localizeStimulusSymbol,
		locale,
		translateText
	} from '$lib/i18n';
	import { user } from '$lib/stores';
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
	});
	
	function startTest() {
		stage = 'test';
		generateSequence();
		showNextTrial();
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
	{#if stage === 'intro'}
		<div class="test-card">
			<h1>🧠 {t('Working Memory Test')}</h1>
			<h2 style="color: #764ba2; font-size: 1.5rem; margin-bottom: 2rem; font-weight: 600;">
				{nBackLabel()} {t('Task')}
			</h2>
			
			<div class="instructions">
				<div class="instruction-header">
					<h3>📋 {t('How It Works:')}</h3>
				</div>
				
				<div class="instruction-steps">
					<div class="step">
						<div class="step-number">{n(1)}</div>
						<div class="step-content">
							<p>{t("You'll see letters appear one at a time on screen")}</p>
						</div>
					</div>
					
					<div class="step">
						<div class="step-number">{n(2)}</div>
						<div class="step-content">
							<p>{t('Each letter stays for 2 seconds')}</p>
						</div>
					</div>
					
					<div class="step">
						<div class="step-number">{n(3)}</div>
						<div class="step-content">
							<p>
								{#if $locale === 'bn'}
									{`বর্তমান অক্ষরটি ${stepAgoText()} আগের অক্ষরের মতো হলে `}
									<strong class="match-btn">✓ {t('Match')}</strong>
									{' চাপুন'}
								{:else}
									{`Click `}
									<strong class="match-btn">✓ {t('Match')}</strong>
									{` if the current letter is the same as the letter from ${stepAgoText()}`}
								{/if}
							</p>
						</div>
					</div>
					
					<div class="step">
						<div class="step-number">{n(4)}</div>
						<div class="step-content">
							<p>
								{#if $locale === 'bn'}
									{`ভিন্ন হলে `}
									<strong class="no-match-btn">✗ {t('No Match')}</strong>
									{' চাপুন'}
								{:else}
									{`Click `}
									<strong class="no-match-btn">✗ {t('No Match')}</strong>
									{` if it's different`}
								{/if}
							</p>
						</div>
					</div>
				</div>
				
				<div class="example-box">
					<h4>💡 {t('Example for')} {nBackLabel()}:</h4>
					<div class="sequence-display">
						<div class="sequence-item">
							<span class="letter-demo">{stimulus('A')}</span>
							<span class="position">{t('Position')} {n(1)}</span>
						</div>
						<div class="arrow">→</div>
						<div class="sequence-item">
							<span class="letter-demo">{stimulus('B')}</span>
							<span class="position">{t('Position')} {n(2)}</span>
						</div>
						<div class="arrow">→</div>
						<div class="sequence-item highlight">
							<span class="letter-demo">{stimulus('A')}</span>
							<span class="position">{t('Position')} {n(3)}</span>
							<span class="match-indicator">✓ {t('MATCH!')}</span>
						</div>
					</div>
					<p class="example-explanation">
						{#if $locale === 'bn'}
							{`অবস্থান ${n(3)}-এ আপনি আবার `}
							<strong>{stimulus('A')}</strong>
							{` দেখছেন। ${stepAgoText()} তাকালে আগেও `}
							<strong>{stimulus('A')}</strong>
							{` ছিল, তাই `}
							<strong class="match-btn">{t('Match')}</strong>
							{' চাপুন!'}
						{:else}
							{`At position 3, you see `}
							<strong>{stimulus('A')}</strong>
							{` again. Looking back ${nBackLevel} step${nBackLevel > 1 ? 's' : ''}, you also saw `}
							<strong>{stimulus('A')}</strong>
							{` → Click `}
							<strong class="match-btn">{t('Match')}</strong>
							{`!`}
						{/if}
					</p>
				</div>
				
				<div class="test-info">
					<div class="info-item">
						<span class="info-label">{t('Total Trials:')}</span>
						<span class="info-value">{n(totalTrials)} {t('letters')}</span>
					</div>
					<div class="info-item">
						<span class="info-label">{t('Difficulty:')}</span>
						<span class="info-value">{nBackLabel()}</span>
					</div>
					<div class="info-item">
						<span class="info-label">{t('Time per Letter:')}</span>
						<span class="info-value">{secondsText(2)}</span>
					</div>
				</div>
			</div>
			
			<div class="button-group">
				<button class="btn-primary btn-large" on:click={startTest}>
					🚀 {t('Start Test')}
				</button>
				<button class="btn-secondary" on:click={backToDashboard}>
					← {t('Back to Dashboard')}
				</button>
			</div>
		</div>
	
	{:else if stage === 'test'}
		<div class="test-card test-active">
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
	.test-container {
		min-height: 100vh;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 2rem;
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

	/* Instructions */
	.instructions {
		text-align: left;
		margin: 2rem 0;
	}

	.instruction-header h3 {
		color: #667eea;
		font-size: 1.5rem;
		margin-bottom: 1.5rem;
		font-weight: 700;
	}

	.instruction-steps {
		background: #f8f9fa;
		border-radius: 16px;
		padding: 1.5rem;
		margin-bottom: 2rem;
	}

	.step {
		display: flex;
		align-items: flex-start;
		gap: 1rem;
		margin-bottom: 1.5rem;
	}

	.step:last-child {
		margin-bottom: 0;
	}

	.step-number {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		width: 36px;
		height: 36px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 700;
		flex-shrink: 0;
		font-size: 1.1rem;
		box-shadow: 0 4px 10px rgba(102, 126, 234, 0.3);
	}

	.step-content p {
		margin: 0;
		color: #333;
		font-size: 1.05rem;
		line-height: 1.6;
	}

	.step-content strong {
		color: #667eea;
		font-weight: 700;
	}

	.match-btn {
		color: #4caf50;
		font-weight: 700;
	}

	.no-match-btn {
		color: #f44336;
		font-weight: 700;
	}

	/* Example Box */
	.example-box {
		background: linear-gradient(135deg, #f0f7ff 0%, #e8f0fe 100%);
		border-radius: 16px;
		padding: 2rem;
		margin: 2rem 0;
		border: 2px solid #667eea;
	}

	.example-box h4 {
		color: #667eea;
		font-size: 1.3rem;
		margin-bottom: 1.5rem;
		font-weight: 700;
	}

	.sequence-display {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		margin: 1.5rem 0;
		flex-wrap: wrap;
	}

	.sequence-item {
		background: white;
		border-radius: 12px;
		padding: 1rem;
		min-width: 100px;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
		text-align: center;
	}

	.sequence-item.highlight {
		background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
		color: white;
		animation: highlightPulse 1s ease-in-out;
	}

	@keyframes highlightPulse {
		0%, 100% { transform: scale(1); }
		50% { transform: scale(1.1); }
	}

	.letter-demo {
		display: block;
		font-size: 2.5rem;
		font-weight: 700;
		color: #667eea;
	}

	.sequence-item.highlight .letter-demo {
		color: white;
	}

	.position {
		display: block;
		font-size: 0.85rem;
		color: #999;
		margin-top: 0.5rem;
	}

	.sequence-item.highlight .position {
		color: rgba(255, 255, 255, 0.9);
	}

	.match-indicator {
		display: block;
		font-size: 0.9rem;
		font-weight: 700;
		margin-top: 0.5rem;
		color: white;
	}

	.arrow {
		font-size: 2rem;
		color: #667eea;
		font-weight: 700;
	}

	.example-explanation {
		color: #555;
		font-size: 1rem;
		line-height: 1.6;
		margin-top: 1rem;
		text-align: center;
	}

	.example-explanation strong {
		color: #667eea;
		font-weight: 700;
	}

	/* Test Info */
	.test-info {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
		margin: 2rem 0;
	}

	.info-item {
		background: white;
		border: 2px solid #e0e0e0;
		border-radius: 12px;
		padding: 1rem;
		text-align: center;
	}

	.info-label {
		display: block;
		color: #999;
		font-size: 0.9rem;
		margin-bottom: 0.5rem;
	}

	.info-value {
		display: block;
		color: #667eea;
		font-size: 1.3rem;
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

		.sequence-display {
			flex-direction: column;
		}

		.arrow {
			transform: rotate(90deg);
		}

		.instruction-steps {
			padding: 1rem;
		}

		.step {
			gap: 0.75rem;
		}

		.step-number {
			width: 32px;
			height: 32px;
			font-size: 1rem;
		}

		.step-content p {
			font-size: 0.95rem;
		}
	}
</style>

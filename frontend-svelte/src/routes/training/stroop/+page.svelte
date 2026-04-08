<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
	import { formatNumber, locale, localeText, translateText } from '$lib/i18n';
	import { user } from '$lib/stores';
	import { getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
	import { onMount } from 'svelte';

	const API_BASE_URL = 'http://127.0.0.1:8000';

	let currentUser = null;
	let loading = true;
	let sessionData = null;
	let difficulty = 1;
	let currentTrial = 0;
	let responses = [];
	let phase = 'intro'; // intro, instructions, practice, test, results
	let showResults = false;
	let metrics = null;
	let newBadges = [];
	let taskId = null;
	/** @type {"practice" | "recorded"} */
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';

	// Practice state
	let practiceTrials = [];
	let currentPractice = 0;
	let practiceFeedback = null;

	// Test state
	let startTime = 0;
	let userAnswer = '';
	let showStimulus = true;
	let trialTimeout = null;
	let responseTimeout = null;

	// Color mapping for display
	const COLOR_MAP = {
		red: '#dc2626',
		blue: '#2563eb',
		green: '#16a34a',
		yellow: '#eab308',
		purple: '#9333ea',
		orange: '#ea580c'
	};

	// Help modal
	let showHelp = false;

	// Subscribe to user store
	user.subscribe((value) => {
		currentUser = value;
	});

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
			const response = await fetch(`${API_BASE_URL}/api/training/tasks/stroop/generate/${currentUser.id}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' }
			});

			if (!response.ok) {
				const errorText = await response.text();
				throw new Error(`Failed to load session: ${response.status} - ${errorText}`);
			}

			const data = await response.json();
			sessionData = data.session_data;
			difficulty = data.difficulty;
			loading = false;
		} catch (error) {
			console.error('Error loading session:', error);
			alert(t('Failed to load training session. Please ensure the backend server is running and you have completed baseline assessment.'));
			loading = false;
		}
	}

	function startInstructions() {
		phase = 'instructions';
	}

	function t(text) {
		return translateText(text, $locale);
	}

	function lt(en, bn) {
		return localeText({ en, bn }, $locale);
	}

	function n(value, options = {}) {
		return formatNumber(value, $locale, options);
	}

	function getDisplayColorLabel(color) {
		return translateText(String(color ?? '').toUpperCase(), $locale);
	}

	function displayStimulusWord(wordText) {
		return translateText(String(wordText ?? '').toUpperCase(), $locale);
	}

	function startPractice() {
		if (!sessionData || !sessionData.colors) {
			alert(t('Session data not loaded. Please refresh the page.'));
			return;
		}

		playMode = TASK_PLAY_MODE.PRACTICE;
		practiceStatusMessage = '';
		
		// Create practice trials (2 baseline, 2 congruent, 2 incongruent)
		const colors = sessionData.colors.slice(0, 4); // Use 4 colors for practice
		
		practiceTrials = [
			// Baseline trials
			{
				condition: 'baseline',
				display_color: colors[0],
				word_text: null,
				correct_answer: colors[0],
				hint: t('Just click the color of the patch. No word to distract you!')
			},
			{
				condition: 'baseline',
				display_color: colors[1],
				word_text: null,
				correct_answer: colors[1],
				hint: t('Simple color identification - nice and easy.')
			},
			// Congruent trials
			{
				condition: 'congruent',
				display_color: colors[2],
				word_text: colors[2].toUpperCase(),
				correct_answer: colors[2],
				hint: t('The word matches the color - easy!')
			},
			{
				condition: 'congruent',
				display_color: colors[3],
				word_text: colors[3].toUpperCase(),
				correct_answer: colors[3],
				hint: t('Word and color agree - this is the easy condition.')
			},
			// Incongruent trials (THE CHALLENGE)
			{
				condition: 'incongruent',
				display_color: colors[0],
				word_text: colors[1].toUpperCase(),
				correct_answer: colors[0],
				hint:
					$locale === 'bn'
						? `"${getDisplayColorLabel(colors[1])}" শব্দটি উপেক্ষা করুন, কালির রঙ বলুন!`
						: `Ignore the word "${colors[1].toUpperCase()}" - answer the INK COLOR!`
			},
			{
				condition: 'incongruent',
				display_color: colors[2],
				word_text: colors[3].toUpperCase(),
				correct_answer: colors[2],
				hint: t("Don't read the word! Focus on the color of the ink.")
			}
		];

		currentPractice = 0;
		practiceFeedback = null;
		phase = 'practice';
	}

	function finishPractice() {
		playMode = TASK_PLAY_MODE.RECORDED;
		practiceFeedback = null;
		currentPractice = 0;
		phase = 'instructions';
		practiceStatusMessage = getPracticeCopy($locale).complete;
	}

	function handlePracticeAnswer(answer) {
		const trial = practiceTrials[currentPractice];
		const correct = answer === trial.correct_answer;

		if (correct) {
			practiceFeedback = {
				type: 'success',
				message: `${t('Correct!')} ${trial.hint}`
			};
		} else {
			practiceFeedback = {
				type: 'error',
				message:
					$locale === 'bn'
						? `পুরো ঠিক হয়নি। সঠিক উত্তর ছিল "${getDisplayColorLabel(trial.correct_answer)}"। ${trial.hint}`
						: `Not quite. The correct answer was "${trial.correct_answer}". ${trial.hint}`
			};
		}

		// Auto-advance after 2 seconds
		setTimeout(() => {
			if (currentPractice < practiceTrials.length - 1) {
				currentPractice++;
				practiceFeedback = null;
			} else {
				setTimeout(() => {
					finishPractice();
				}, 1000);
			}
		}, 2000);
	}

	function startTest() {
		playMode = TASK_PLAY_MODE.RECORDED;
		practiceStatusMessage = '';
		phase = 'test';
		currentTrial = 0;
		responses = [];
		showNextTrial();
	}

	function showNextTrial() {
		if (currentTrial >= sessionData.trials.length) {
			completeSession();
			return;
		}

		userAnswer = '';
		showStimulus = true;
		startTime = Date.now();

		const trial = sessionData.trials[currentTrial];
		const presentationTime = sessionData.presentation_time_ms;
		const timeoutTime = sessionData.response_timeout_ms;

		// Show stimulus for presentation time, then stay visible but require response
		trialTimeout = setTimeout(() => {
			showStimulus = true; // Keep showing but user must respond
			
			// Auto-advance if no response within timeout
			responseTimeout = setTimeout(() => {
				handleAnswer('', true); // Timeout - no response
			}, timeoutTime);
		}, presentationTime);
	}

	function handleAnswer(answer, isTimeout = false) {
		clearTimeout(trialTimeout);
		clearTimeout(responseTimeout);

		const reactionTime = Date.now() - startTime;
		const trial = sessionData.trials[currentTrial];

		responses.push({
			trial_number: trial.trial_number,
			condition: trial.condition,
			user_response: answer,
			correct_answer: trial.correct_answer,
			correct: answer === trial.correct_answer,
			reaction_time_ms: isTimeout ? 0 : reactionTime
		});

		currentTrial++;
		
		// Brief pause before next trial
		setTimeout(() => {
			showNextTrial();
		}, 300);
	}

	function handleColorClick(color) {
		if (phase === 'practice') {
			handlePracticeAnswer(color);
		} else if (phase === 'test') {
			handleAnswer(color);
		}
	}

	async function completeSession() {
		try {
			taskId = $page.url.searchParams.get('taskId');
			const response = await fetch(`${API_BASE_URL}/api/training/tasks/stroop/submit/${currentUser.id}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					difficulty,
					session_data: sessionData,
					responses,
					task_id: taskId
				})
			});

			if (!response.ok) throw new Error('Failed to submit session');

			const data = await response.json();
			metrics = data.metrics;
			newBadges = data.new_badges || [];
			phase = 'results';
			showResults = true;
		} catch (error) {
			console.error('Error submitting session:', error);
		}
	}

	function returnToDashboard() {
		goto('/dashboard');
	}

	// Get current trial data
	$: currentTrialData = phase === 'practice' 
		? practiceTrials[currentPractice] 
		: (sessionData && currentTrial < sessionData.trials.length) 
			? sessionData.trials[currentTrial] 
			: null;

	// Progress tracking
	$: progress = sessionData ? ((currentTrial / sessionData.trials.length) * 100) : 0;
	$: trialsRemaining = sessionData ? sessionData.trials.length - currentTrial : 0;

	// Current condition name
	$: conditionName = currentTrialData?.condition === 'baseline'
		? translateText('Color Patches', $locale)
		: currentTrialData?.condition === 'congruent'
			? translateText('Matching Words', $locale)
			: translateText('Conflicting Words', $locale);

	// Performance badge color
	$: performanceBadgeColor = metrics?.performance_level === 'Excellent' ? 'from-green-500 to-emerald-600'
		: metrics?.performance_level === 'Good' ? 'from-blue-500 to-indigo-600'
		: metrics?.performance_level === 'Fair' ? 'from-yellow-500 to-orange-500'
		: 'from-gray-500 to-gray-600';
</script>

<svelte:head>
	<title>{lt('Stroop Test - NeuroBloom', 'স্ট্রুপ পরীক্ষা - NeuroBloom')}</title>
</svelte:head>

<div class="stroop-container" data-localize-skip>
	<div class="stroop-inner">

		{#if loading}
			<LoadingSkeleton variant="card" count={3} />

		{:else if phase === 'intro'}
			<div class="instructions-card">
				<div class="header-content">
					<div class="title-row">
						<h1>{t('Stroop Color-Word Test')}</h1>
						<DifficultyBadge {difficulty} domain="Attention" />
					</div>
					<p class="subtitle">{t('Selective Attention and Inhibitory Control Assessment')}</p>
					<div class="classic-badge">{t('Classic Neuropsychological Assessment — Stroop, 1935')}</div>
				</div>

				<div class="task-concept">
					<h3>{t('The Core Principle')}</h3>
					<p>{t('Your brain reads words automatically and involuntarily. This test measures your ability to suppress that automatic response and name the ink color instead.')}</p>
					<div class="stroop-examples">
						<div class="ex-card ex-baseline">
							<div class="ex-type">{t('Baseline')}</div>
							<div class="color-patch-demo" style="background: {COLOR_MAP['red']};"></div>
							<div class="ex-label">{t('Name the color')}</div>
							<div class="ex-verdict ex-easy">{t('No conflict')}</div>
						</div>
						<div class="ex-card ex-congruent">
							<div class="ex-type">{t('Congruent')}</div>
							<div class="word-demo" style="color: {COLOR_MAP['green']};">{displayStimulusWord('green')}</div>
							<div class="ex-label">{t('Word = Ink color')}</div>
							<div class="ex-verdict ex-easy">{t('Easy — no conflict')}</div>
						</div>
						<div class="ex-card ex-incongruent">
							<div class="ex-type">{t('Incongruent')}</div>
							<div class="word-demo" style="color: {COLOR_MAP['blue']};">{displayStimulusWord('red')}</div>
							<div class="ex-label">{t('Answer: Blue (not Red!)')}</div>
							<div class="ex-verdict ex-hard">{t('The real challenge')}</div>
						</div>
					</div>
					<div class="key-rule-box">
						<strong>{t('Rule:')}</strong> {t('Always name the INK COLOR — never read the word aloud.')}
					</div>
				</div>

				<div class="rules-grid">
					<div class="rule-card">
						<span class="rule-num">1</span>
						<div class="rule-text">
							<strong>{t('See the Stimulus')}</strong>
							<span>{t('A color patch or a colored word appears on screen')}</span>
						</div>
					</div>
					<div class="rule-card">
						<span class="rule-num">2</span>
						<div class="rule-text">
							<strong>{t('Identify Ink Color')}</strong>
							<span>{t('Ignore the word meaning — focus only on the ink color')}</span>
						</div>
					</div>
					<div class="rule-card">
						<span class="rule-num">3</span>
						<div class="rule-text">
							<strong>{t('Click the Button')}</strong>
							<span>{t('Tap the color button that matches the ink color')}</span>
						</div>
					</div>
					<div class="rule-card">
						<span class="rule-num">4</span>
						<div class="rule-text">
							<strong>{t('Respond Quickly')}</strong>
							<span>{t('Accuracy first, then speed — both are measured')}</span>
						</div>
					</div>
				</div>

				<div class="info-grid">
					<div class="info-section">
						<h4>{t('Tips for Success')}</h4>
						<ul class="tips-list">
							<li><strong>{t('Focus on the color:')}</strong> {t('not the letters')}</li>
							<li><strong>{t('Do not read aloud:')}</strong> {t('your brain will try automatically')}</li>
							<li><strong>{t('Stay composed:')}</strong> {t('interference is universal — even experts feel it')}</li>
							<li><strong>{t('Errors are expected:')}</strong> {t('on conflicting trials especially')}</li>
						</ul>
					</div>
					<div class="info-section">
						<h4>{t('Test Structure')}</h4>
						<ul class="structure-list">
							<li>
								<span class="struct-key">{t('Phase 1')}</span>
								<span class="struct-val">{t('Color patches (baseline)')}</span>
							</li>
							<li>
								<span class="struct-key">{t('Phase 2')}</span>
								<span class="struct-val">{t('Matching words (congruent)')}</span>
							</li>
							<li>
								<span class="struct-key">{t('Phase 3')}</span>
								<span class="struct-val">{t('Conflicting words (key measure)')}</span>
							</li>
							<li>
								<span class="struct-key">{t('Response')}</span>
								<span class="struct-val">{t('Color buttons — no typing')}</span>
							</li>
						</ul>
					</div>
				</div>

				<div class="clinical-info">
					<h4>{t('Clinical Significance')}</h4>
					<div class="clinical-grid">
						<div class="clinical-item">
							<strong>{t('History')}</strong>
							<span>{t('Stroop, 1935 — psychology\'s most studied paradigm')}</span>
						</div>
						<div class="clinical-item">
							<strong>{t('Measures')}</strong>
							<span>{t('Selective attention, inhibitory control, cognitive flexibility')}</span>
						</div>
						<div class="clinical-item">
							<strong>{t('MS Relevance')}</strong>
							<span>{t('Sensitive to frontal lobe changes (Parmenter et al., 2007)')}</span>
						</div>
						<div class="clinical-item">
							<strong>{t('Clinical Use')}</strong>
							<span>{t('Standard component of MS neuropsychological batteries')}</span>
						</div>
					</div>
				</div>

				<div class="perf-guide">
					<h4>{t('Performance Reference (Accuracy)')}</h4>
					<div class="norm-bars">
						<div class="norm-bar norm-excellent"><span class="norm-label">{t('Excellent')}</span><span class="norm-val">&ge;92%</span></div>
						<div class="norm-bar norm-good"><span class="norm-label">{t('Good')}</span><span class="norm-val">82–91%</span></div>
						<div class="norm-bar norm-avg"><span class="norm-label">{t('Average')}</span><span class="norm-val">70–81%</span></div>
						<div class="norm-bar norm-fair"><span class="norm-label">{t('Fair')}</span><span class="norm-val">55–69%</span></div>
						<div class="norm-bar norm-needs"><span class="norm-label">{t('Developing')}</span><span class="norm-val">&lt;55%</span></div>
					</div>
					<p class="norm-note">* {t('Incongruent accuracy is always lower than baseline — that is expected.')}</p>
				</div>

				<div class="button-group">
					<button class="start-button" on:click={startInstructions}>{t('Begin Test')}</button>
					<button class="btn-secondary" on:click={() => goto('/dashboard')}>{t('Back to Dashboard')}</button>
					<button class="help-link" on:click={() => showHelp = true}>{t('More Information')}</button>
				</div>
			</div>

		{:else if phase === 'instructions'}
			<div class="screen-card quick-instructions">
				<h2>{t('Quick Instructions')}</h2>
				<p class="instr-subtitle">{t('Name the ink color — ignore the word meaning.')}</p>

				<div class="steps-grid">
					<div class="step-card">
						<span class="step-num">1</span>
						<strong>{t('See the Stimulus')}</strong>
						<span>{t('Color patch or colored word appears')}</span>
					</div>
					<div class="step-card">
						<span class="step-num">2</span>
						<strong>{t('Identify Ink Color')}</strong>
						<span>{t('Ignore what the word says')}</span>
					</div>
					<div class="step-card">
						<span class="step-num">3</span>
						<strong>{t('Click the Button')}</strong>
						<span>{t('Tap the matching color button')}</span>
					</div>
					<div class="step-card">
						<span class="step-num">4</span>
						<strong>{t('Respond Quickly')}</strong>
						<span>{t('Speed and accuracy both measured')}</span>
					</div>
				</div>

				<div class="remember-box">
					<strong>{t('Remember:')}</strong>
					{t('On conflicting trials your brain will try to read the word.')}
					<strong> {t('Resist this — name the ink color only.')}</strong>
				</div>

				{#if practiceStatusMessage}
					<div class="practice-note">{practiceStatusMessage}</div>
				{/if}

				<TaskPracticeActions
					locale={$locale}
					startLabel={t('Start Actual Test')}
					statusMessage={practiceStatusMessage}
					on:start={startTest}
					on:practice={startPractice}
				/>
			</div>

		{:else if phase === 'practice'}
			<div class="screen-card trial-screen">
				<PracticeModeBanner locale={$locale} />
				<div class="trial-header">
					<span class="trial-badge">
						{lt(`Practice ${currentPractice + 1} / ${practiceTrials.length}`,
							`অনুশীলন ${n(currentPractice + 1)} / ${n(practiceTrials.length)}`)}
					</span>
					<span class="condition-badge condition-{currentTrialData?.condition}">{conditionName}</span>
				</div>

				<div class="stimulus-area">
					{#if currentTrialData?.condition === 'baseline'}
						<div class="color-patch-large" style="background: {COLOR_MAP[currentTrialData.display_color]};"></div>
					{:else}
						<div class="stroop-word-large" style="color: {COLOR_MAP[currentTrialData.display_color]};">
							{displayStimulusWord(currentTrialData.word_text)}
						</div>
					{/if}
				</div>

				<div class="color-buttons">
					{#each sessionData.colors.slice(0, 4) as color}
						<button
							class="color-btn"
							style="background: {COLOR_MAP[color]};"
							disabled={practiceFeedback !== null}
							on:click={() => handleColorClick(color)}
						>
							{getDisplayColorLabel(color)}
						</button>
					{/each}
				</div>

				{#if practiceFeedback}
					<div class="feedback-box feedback-{practiceFeedback.type}">
						{practiceFeedback.message}
					</div>
				{/if}
			</div>

		{:else if phase === 'test'}
			<div class="screen-card trial-screen">
				<div class="test-header">
					<div class="test-badges">
						<span class="trial-badge">
							{lt(`Trial ${currentTrial + 1} / ${sessionData.trials.length}`,
								`ট্রায়াল ${n(currentTrial + 1)} / ${n(sessionData.trials.length)}`)}
						</span>
						<span class="condition-badge condition-{currentTrialData?.condition}">{conditionName}</span>
					</div>
					<div class="progress-track">
						<div class="progress-fill" style="width: {progress}%;"></div>
					</div>
					<button class="help-btn-sm" on:click={() => showHelp = true}>?</button>
				</div>

				{#if showStimulus && currentTrialData}
					<div class="stimulus-area">
						{#if currentTrialData.condition === 'baseline'}
							<div class="color-patch-large" style="background: {COLOR_MAP[currentTrialData.display_color]};"></div>
						{:else}
							<div class="stroop-word-large" style="color: {COLOR_MAP[currentTrialData.display_color]};">
								{displayStimulusWord(currentTrialData.word_text)}
							</div>
						{/if}
						{#if currentTrialData.condition === 'incongruent'}
							<p class="conflict-hint">{t('Name the ink color — ignore the word')}</p>
						{/if}
					</div>

					<div class="color-buttons">
						{#each sessionData.colors as color}
							<button
								class="color-btn"
								style="background: {COLOR_MAP[color]};"
								on:click={() => handleColorClick(color)}
							>
								{getDisplayColorLabel(color)}
							</button>
						{/each}
					</div>
				{/if}
			</div>

		{:else if phase === 'results'}
			<div class="screen-card complete-screen">
				{#if metrics}
					<div class="perf-banner">
						<div class="perf-level">{t(metrics.performance_level)}</div>
						<div class="perf-subtitle">{metrics.overall_accuracy.toFixed(1)}% {t('accuracy')} — {t('Stroop Test Complete')}</div>
					</div>

					<div class="metrics-grid">
						<div class="metric-card highlight">
							<div class="metric-value">{metrics.overall_accuracy.toFixed(1)}%</div>
							<div class="metric-label">{t('Overall Accuracy')}</div>
							<div class="metric-sub">{lt(`${metrics.correct_trials}/${metrics.total_trials} correct`, `${n(metrics.correct_trials)}/${n(metrics.total_trials)} সঠিক`)}</div>
						</div>
						<div class="metric-card">
							<div class="metric-value">{n(metrics.stroop_effect.toFixed(0))} {lt('ms', 'মি.সে')}</div>
							<div class="metric-label">{t('Stroop Effect')}</div>
							<div class="metric-sub">{t('Conflict minus congruent RT')}</div>
						</div>
						<div class="metric-card">
							<div class="metric-value">{metrics.interference_cost.toFixed(1)}%</div>
							<div class="metric-label">{t('Interference Cost')}</div>
							<div class="metric-sub">{t('vs. Baseline speed')}</div>
						</div>
						<div class="metric-card">
							<div class="metric-value">{metrics.consistency.toFixed(1)}%</div>
							<div class="metric-label">{t('Consistency')}</div>
							<div class="metric-sub">{t('Response stability')}</div>
						</div>
					</div>

					<div class="breakdown">
						<h3>{t('Performance by Condition')}</h3>
						<div class="condition-row condition-baseline">
							<div class="cond-header">
								<span class="cond-dot" style="background: #64748b;"></span>
								<strong>{t('Baseline (Color Patches)')}</strong>
							</div>
							<div class="cond-stats">
								<span>{t('Accuracy:')} <strong>{metrics.baseline_accuracy.toFixed(1)}%</strong></span>
								<span>{t('Avg RT:')} <strong>{n(metrics.baseline_rt.toFixed(0))} {lt('ms', 'মি.সে')}</strong></span>
								<span class="cond-note">{t('Pure processing speed')}</span>
							</div>
						</div>
						<div class="condition-row condition-congruent">
							<div class="cond-header">
								<span class="cond-dot" style="background: #16a34a;"></span>
								<strong>{t('Congruent (Matching Words)')}</strong>
							</div>
							<div class="cond-stats">
								<span>{t('Accuracy:')} <strong>{metrics.congruent_accuracy.toFixed(1)}%</strong></span>
								<span>{t('Avg RT:')} <strong>{n(metrics.congruent_rt.toFixed(0))} {lt('ms', 'মি.সে')}</strong></span>
								{#if metrics.facilitation_effect > 0}
									<span class="cond-note cond-positive">{lt(`${metrics.facilitation_effect.toFixed(0)}ms faster than baseline`, `${n(metrics.facilitation_effect.toFixed(0))}মি.সে বেসলাইনের চেয়ে দ্রুত`)}</span>
								{:else}
									<span class="cond-note">{t('No facilitation effect')}</span>
								{/if}
							</div>
						</div>
						<div class="condition-row condition-incongruent">
							<div class="cond-header">
								<span class="cond-dot" style="background: #e11d48;"></span>
								<strong>{t('Incongruent (Conflicting Words)')}</strong>
							</div>
							<div class="cond-stats">
								<span>{t('Accuracy:')} <strong>{metrics.incongruent_accuracy.toFixed(1)}%</strong></span>
								<span>{t('Avg RT:')} <strong>{n(metrics.incongruent_rt.toFixed(0))} {lt('ms', 'মি.সে')}</strong></span>
								{#if metrics.stroop_effect > 0}
									<span class="cond-note cond-warning">{lt(`${metrics.stroop_effect.toFixed(0)}ms interference penalty`, `${n(metrics.stroop_effect.toFixed(0))}মি.সে হস্তক্ষেপ বিলম্ব`)}</span>
								{:else}
									<span class="cond-note cond-positive">{t('Excellent interference control')}</span>
								{/if}
							</div>
						</div>
					</div>

					<div class="interpretation-section">
						<h3>{t('What This Means')}</h3>
						<p class="feedback-text">{t(metrics.feedback)}</p>
						<div class="insights">
							{#if metrics.interference_cost < 20}
								<div class="insight insight-good"><strong>{t('Excellent inhibitory control:')}</strong> {t('Minimal interference from word reading')}</div>
							{:else if metrics.interference_cost < 40}
								<div class="insight insight-good"><strong>{t('Good cognitive control:')}</strong> {t('Managing interference effectively')}</div>
							{:else if metrics.interference_cost < 60}
								<div class="insight insight-moderate"><strong>{t('Moderate interference:')}</strong> {t('Word reading affecting performance — this is normal')}</div>
							{:else}
								<div class="insight insight-high"><strong>{t('High interference effect:')}</strong> {t('Word reading is strongly competing with color naming')}</div>
							{/if}
							{#if metrics.stroop_effect < 100}
								<div class="insight insight-good"><strong>{t('Minimal Stroop effect:')}</strong> {t('Fast conflict resolution')}</div>
							{:else if metrics.stroop_effect < 200}
								<div class="insight insight-moderate"><strong>{t('Normal Stroop effect:')}</strong> {t('Expected interference range')}</div>
							{:else}
								<div class="insight insight-high"><strong>{t('Significant Stroop effect:')}</strong> {t('Conflicts require extra processing time')}</div>
							{/if}
						</div>
					</div>

					<div class="clinical-note">
						<h4>{t('About the Stroop Effect')}</h4>
						<p><strong>{t('Automatic vs. Controlled Processing:')}</strong> {t('The Stroop Effect demonstrates how reading (automatic) interferes with color naming (controlled). Everyone experiences this interference.')}</p>
						<p class="why-matters"><strong>{t('For MS:')}</strong> {t('This test is sensitive to frontal lobe dysfunction. Regular Stroop practice strengthens prefrontal inhibitory circuits, which can improve real-world attention and focus.')}</p>
					</div>

					{#if metrics.difficulty_after !== undefined && metrics.difficulty_after !== difficulty}
						<div class="difficulty-info">
							<span>{t('Difficulty:')} <strong>{n(difficulty)}</strong> → <strong>{n(metrics.difficulty_after)}</strong></span>
						</div>
					{/if}

					{#if newBadges.length > 0}
						<BadgeNotification badges={newBadges} />
					{/if}

					<div class="button-group">
						<button class="start-button" on:click={returnToDashboard}>{t('Return to Dashboard')}</button>
						<button class="btn-secondary" on:click={() => goto('/training')}>{t('Back to Training')}</button>
					</div>
				{/if}
			</div>
		{/if}

		{#if phase !== 'results' && phase !== 'intro'}
			<button class="help-fab" on:click={() => showHelp = true} aria-label={t('Help')}>?</button>
		{/if}
	</div>
</div>

{#if showHelp}
	<div class="modal-overlay" on:click={() => showHelp = false} role="presentation">
		<div class="modal-content" role="dialog" tabindex="-1"
			on:click|stopPropagation
			on:keydown={(e) => e.key === 'Escape' && (showHelp = false)}>
			<button class="close-btn" on:click={() => showHelp = false}>×</button>
			<h2>{t('Stroop Test — Strategies and Information')}</h2>
			<div class="strategy">
				<h3>{t('What is the Stroop Test?')}</h3>
				<p>{t('A classic test measuring selective attention and cognitive interference, demonstrating how automatic word reading can interfere with the goal of naming ink colors.')}</p>
			</div>
			<div class="strategy">
				<h3>{t('Why Used for MS?')}</h3>
				<p>{t('Sensitive to frontal lobe and executive function changes common in MS. Measures inhibitory control — the ability to suppress an automatic response. Standard in MS neuropsychological batteries.')}</p>
			</div>
			<div class="strategy">
				<h3>{t('Understanding Your Scores')}</h3>
				<p><strong>{t('Stroop Effect:')}</strong> {t('Gap between conflicting and matching trials. Lower is better.')}</p>
				<p><strong>{t('Interference Cost:')}</strong> {t('How much slower you are on conflict vs. baseline. Measures inhibitory control.')}</p>
				<p><strong>{t('Facilitation Effect:')}</strong> {t('How much faster matching words are vs. baseline.')}</p>
			</div>
			<div class="strategy">
				<h3>{t('Practical Strategies')}</h3>
				<p>{t('Look at the color of the ink rather than the shape of the letters. Try slightly defocusing your gaze to blur the word. Do not try to read — override it consciously.')}</p>
			</div>
			<div class="strategy">
				<h3>{t('Historical Note')}</h3>
				<p>{t('John Ridley Stroop published this paradigm in 1935. It remains one of the most cited experiments in all of psychology, used in thousands of clinical and research studies worldwide.')}</p>
			</div>
		</div>
	</div>
{/if}

<style>
	/* ── Container ─────────────────────────────────────────── */
	.stroop-container {
		min-height: 100vh;
		background: #C8DEFA;
		padding: 2rem 1rem;
	}

	.stroop-inner {
		max-width: 960px;
		margin: 0 auto;
		position: relative;
	}

	/* ── Instructions card ─────────────────────────────────── */
	.instructions-card {
		background: white;
		border-radius: 16px;
		padding: 2.5rem;
		box-shadow: 0 4px 6px rgba(0,0,0,0.07), 0 1px 3px rgba(0,0,0,0.06);
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

	.classic-badge {
		display: inline-block;
		background: rgba(225, 29, 72, 0.1);
		color: #e11d48;
		border: 1px solid rgba(225, 29, 72, 0.3);
		border-radius: 20px;
		padding: 0.3rem 1rem;
		font-size: 0.82rem;
		font-weight: 700;
		letter-spacing: 0.03em;
	}

	/* ── Task concept ──────────────────────────────────────── */
	.task-concept {
		background: linear-gradient(135deg, #fff1f2, #fecdd3);
		border: 1px solid #fda4af;
		border-radius: 12px;
		padding: 1.5rem;
	}

	.task-concept h3 { font-size: 1rem; font-weight: 700; color: #be123c; margin: 0 0 0.5rem; }
	.task-concept > p { color: #9f1239; margin: 0 0 1.2rem; line-height: 1.6; }

	.stroop-examples {
		display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;
		background: white; border-radius: 10px; padding: 1.2rem;
		box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 1.2rem;
	}

	.ex-card {
		display: flex; flex-direction: column; align-items: center; gap: 0.4rem;
		background: #f8fafc; border-radius: 10px; padding: 1rem 1.2rem;
		min-width: 140px; text-align: center;
	}

	.ex-type { font-size: 0.78rem; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.05em; }

	.color-patch-demo {
		width: 80px; height: 48px; border-radius: 8px;
		box-shadow: 0 2px 6px rgba(0,0,0,0.15);
	}

	.word-demo { font-size: 2rem; font-weight: 800; line-height: 1; }

	.ex-label { font-size: 0.8rem; color: #64748b; }

	.ex-verdict {
		font-size: 0.75rem; font-weight: 700; padding: 0.2rem 0.6rem;
		border-radius: 10px;
	}
	.ex-easy { background: #dcfce7; color: #166534; }
	.ex-hard { background: #fee2e2; color: #991b1b; }

	.key-rule-box {
		background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px;
		padding: 0.75rem 1rem; font-size: 0.88rem; color: #991b1b; line-height: 1.5;
	}

	/* ── Rules grid ────────────────────────────────────────── */
	.rules-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }

	.rule-card {
		display: flex; align-items: flex-start; gap: 0.8rem;
		padding: 1rem; background: #f8fafc; border-radius: 10px;
		border-left: 4px solid #e11d48;
	}

	.rule-num {
		width: 28px; height: 28px; border-radius: 50%;
		background: #e11d48; color: white;
		display: flex; align-items: center; justify-content: center;
		font-size: 0.85rem; font-weight: 700; flex-shrink: 0;
	}

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
	.struct-val { font-weight: 600; color: #1e293b; text-align: right; }

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

	/* ── Perf guide ────────────────────────────────────────── */
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

	/* ── Buttons ───────────────────────────────────────────── */
	.button-group {
		display: flex; justify-content: center; gap: 1rem;
		flex-wrap: wrap; padding-top: 0.5rem; align-items: center;
	}

	.start-button {
		background: #4338ca;
		color: white; border: none; border-radius: 10px;
		padding: 0.85rem 2.5rem; font-size: 1rem; font-weight: 700;
		cursor: pointer; transition: transform 0.15s, box-shadow 0.15s;
		box-shadow: 0 4px 14px rgba(67, 56, 202, 0.35);
	}
	.start-button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(67, 56, 202, 0.45); }

	.btn-secondary {
		background: white; color: #667eea;
		border: 2px solid #667eea; border-radius: 10px;
		padding: 0.85rem 2rem; font-size: 1rem; font-weight: 600;
		cursor: pointer; transition: all 0.15s;
	}
	.btn-secondary:hover { background: rgba(102,126,234,0.08); }

	.help-link {
		background: none; border: none; color: #667eea;
		font-size: 0.9rem; cursor: pointer; text-decoration: underline;
		padding: 0.5rem; font-weight: 600; transition: color 0.15s;
	}
	.help-link:hover { color: #4f46e5; }

	/* ── Screen card ───────────────────────────────────────── */
	.screen-card {
		background: white; border-radius: 16px; padding: 2.5rem;
		box-shadow: 0 4px 6px rgba(0,0,0,0.07);
	}

	/* ── Quick instructions ────────────────────────────────── */
	.quick-instructions { text-align: center; }
	.quick-instructions h2 { font-size: 1.6rem; font-weight: 700; color: #1e293b; margin: 0 0 0.4rem; }
	.instr-subtitle { color: #64748b; margin: 0 0 2rem; }

	.steps-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-bottom: 1.5rem; text-align: left; }

	.step-card {
		display: flex; flex-direction: column; gap: 0.3rem;
		background: #f8fafc; border-radius: 10px; padding: 1rem;
		border-left: 4px solid #e11d48;
	}

	.step-num {
		width: 26px; height: 26px; border-radius: 50%;
		background: #e11d48; color: white;
		display: flex; align-items: center; justify-content: center;
		font-size: 0.82rem; font-weight: 700; margin-bottom: 0.2rem;
	}

	.step-card strong { font-size: 0.9rem; color: #1e293b; }
	.step-card span   { font-size: 0.82rem; color: #64748b; }

	.remember-box {
		background: #fff1f2; border: 1px solid #fda4af; border-radius: 10px;
		padding: 0.9rem 1.2rem; font-size: 0.9rem; color: #9f1239; line-height: 1.6;
		margin-bottom: 1.5rem;
	}

	.practice-note {
		background: #fef9c3; border: 1px solid #fde047;
		border-radius: 8px; padding: 0.6rem 1rem;
		color: #854d0e; font-size: 0.88rem; margin-bottom: 1rem;
	}

	/* ── Trial screen ──────────────────────────────────────── */
	.trial-screen { text-align: center; }

	.trial-header {
		display: flex; justify-content: center; align-items: center;
		gap: 0.75rem; flex-wrap: wrap; margin-bottom: 2rem;
	}

	.test-header {
		display: flex; justify-content: space-between; align-items: center;
		margin-bottom: 2rem; gap: 0.75rem; flex-wrap: wrap;
	}

	.test-badges { display: flex; gap: 0.5rem; flex: 1; align-items: center; flex-wrap: wrap; }

	.progress-track {
		flex: 1; height: 6px; background: #e2e8f0; border-radius: 3px;
		overflow: hidden; min-width: 80px;
	}
	.progress-fill { height: 100%; background: linear-gradient(90deg, #e11d48, #f43f5e); border-radius: 3px; transition: width 0.3s; }

	.help-btn-sm {
		width: 36px; height: 36px; border-radius: 50%;
		border: 2px solid #667eea; background: white; color: #667eea;
		font-size: 1.1rem; font-weight: 700; cursor: pointer;
		display: flex; align-items: center; justify-content: center; transition: all 0.2s;
	}
	.help-btn-sm:hover { background: #667eea; color: white; }

	.trial-badge {
		background: rgba(102,126,234,0.12); color: #667eea;
		padding: 0.35rem 0.9rem; border-radius: 20px; font-size: 0.85rem; font-weight: 700;
	}

	.condition-badge {
		padding: 0.35rem 0.9rem; border-radius: 20px; font-size: 0.82rem; font-weight: 600;
	}
	.condition-baseline   { background: #f1f5f9; color: #475569; }
	.condition-congruent  { background: #dcfce7; color: #166534; }
	.condition-incongruent{ background: #fee2e2; color: #991b1b; }

	/* ── Stimulus area ─────────────────────────────────────── */
	.stimulus-area { margin: 1.5rem auto 2rem; display: flex; flex-direction: column; align-items: center; gap: 0.75rem; }

	.color-patch-large {
		width: 160px; height: 100px; border-radius: 14px;
		box-shadow: 0 8px 24px rgba(0,0,0,0.18);
	}

	.stroop-word-large {
		font-size: 5rem; font-weight: 900; line-height: 1;
		letter-spacing: -0.02em;
	}

	.conflict-hint { font-size: 0.88rem; color: #94a3b8; font-style: italic; margin: 0; }

	/* ── Color buttons ─────────────────────────────────────── */
	.color-buttons {
		display: flex; flex-wrap: wrap; justify-content: center; gap: 0.75rem; margin-top: 0.5rem;
	}

	.color-btn {
		padding: 0.65rem 1.6rem; border: none; border-radius: 10px;
		font-size: 0.95rem; font-weight: 700; color: white; cursor: pointer;
		text-shadow: 0 1px 2px rgba(0,0,0,0.35);
		box-shadow: 0 4px 12px rgba(0,0,0,0.2);
		transition: transform 0.1s, box-shadow 0.1s;
		min-width: 90px;
	}
	.color-btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 6px 18px rgba(0,0,0,0.28); }
	.color-btn:active:not(:disabled) { transform: translateY(0); }
	.color-btn:disabled { opacity: 0.5; cursor: default; }

	/* ── Feedback ──────────────────────────────────────────── */
	.feedback-box { margin-top: 1.5rem; padding: 1rem 1.5rem; border-radius: 10px; font-weight: 600; font-size: 0.95rem; line-height: 1.5; }
	.feedback-success { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
	.feedback-error   { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }

	/* ── Complete screen ───────────────────────────────────── */
	.complete-screen { display: flex; flex-direction: column; gap: 1.5rem; }

	.perf-banner {
		text-align: center; padding: 1.5rem;
		background: linear-gradient(135deg, #fff1f2, #fecdd3);
		border: 2px solid #fda4af; border-radius: 14px;
	}
	.perf-level    { font-size: 1.8rem; font-weight: 800; color: #e11d48; }
	.perf-subtitle { font-size: 0.95rem; color: #64748b; margin-top: 0.3rem; }

	.metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; }
	.metric-card {
		background: #f8fafc; border: 1px solid #e2e8f0;
		border-radius: 12px; padding: 1.2rem; text-align: center;
	}
	.metric-card.highlight {
		background: linear-gradient(135deg, #e11d48, #be123c);
		border-color: transparent; color: white;
	}
	.metric-value { font-size: 1.8rem; font-weight: 800; color: #1e293b; margin-bottom: 0.2rem; }
	.metric-card.highlight .metric-value,
	.metric-card.highlight .metric-label,
	.metric-card.highlight .metric-sub { color: white; }
	.metric-label { font-size: 0.82rem; font-weight: 600; color: #64748b; }
	.metric-sub   { font-size: 0.78rem; color: #94a3b8; margin-top: 0.2rem; }

	/* ── Breakdown ─────────────────────────────────────────── */
	.breakdown { background: #f8fafc; border-radius: 12px; padding: 1.2rem; }
	.breakdown h3 { font-size: 0.95rem; font-weight: 700; color: #1e293b; margin: 0 0 1rem; }

	.condition-row {
		padding: 0.9rem; border-radius: 10px; margin-bottom: 0.75rem;
		border: 1px solid #e2e8f0;
	}
	.condition-row:last-child { margin-bottom: 0; }
	.condition-baseline   { background: #f8fafc; }
	.condition-congruent  { background: #f0fdf4; border-color: #bbf7d0; }
	.condition-incongruent{ background: #fff1f2; border-color: #fda4af; }

	.cond-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; }
	.cond-header strong { font-size: 0.88rem; color: #1e293b; }
	.cond-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }

	.cond-stats { display: flex; flex-wrap: wrap; gap: 0.5rem 1.5rem; font-size: 0.85rem; color: #475569; }
	.cond-note { font-style: italic; color: #94a3b8; }
	.cond-positive { color: #16a34a; font-weight: 600; font-style: normal; }
	.cond-warning  { color: #dc2626; font-weight: 600; font-style: normal; }

	/* ── Interpretation ────────────────────────────────────── */
	.interpretation-section { background: #f8fafc; border-radius: 12px; padding: 1.2rem; }
	.interpretation-section h3 { font-size: 0.95rem; font-weight: 700; color: #1e293b; margin: 0 0 0.6rem; }
	.feedback-text { font-size: 0.9rem; color: #475569; margin: 0 0 1rem; line-height: 1.6; }

	.insights { display: flex; flex-direction: column; gap: 0.5rem; }
	.insight { padding: 0.6rem 0.9rem; border-radius: 8px; font-size: 0.85rem; line-height: 1.5; }
	.insight-good     { background: #dcfce7; color: #166534; }
	.insight-moderate { background: #fef9c3; color: #854d0e; }
	.insight-high     { background: #fee2e2; color: #991b1b; }

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
		background: #fff1f2; border: 1px solid #fda4af; border-radius: 10px;
		padding: 0.75rem 1.2rem; font-size: 0.88rem; font-weight: 600; color: #be123c;
	}

	/* ── FAB help button ───────────────────────────────────── */
	.help-fab {
		position: fixed; bottom: 2rem; right: 2rem;
		width: 48px; height: 48px; border-radius: 50%;
		background: white; border: 2px solid #667eea; color: #667eea;
		font-size: 1.3rem; font-weight: 700; cursor: pointer;
		box-shadow: 0 4px 12px rgba(0,0,0,0.15);
		display: flex; align-items: center; justify-content: center;
		transition: all 0.2s;
	}
	.help-fab:hover { background: #667eea; color: white; }

	/* ── Modal ─────────────────────────────────────────────── */
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
		display: flex; align-items: center; justify-content: center;
	}
	.close-btn:hover { background: #e2e8f0; }
	.modal-content h2 {
		font-size: 1.2rem; font-weight: 700; color: #1e293b;
		margin: 0 0 1.2rem; padding-right: 2.5rem;
	}
	.strategy {
		padding: 0.9rem 1rem; background: #f8fafc;
		border-radius: 8px; border-left: 4px solid #e11d48; margin-bottom: 0.75rem;
	}
	.strategy h3 { font-size: 0.88rem; font-weight: 700; color: #1e293b; margin: 0 0 0.3rem; }
	.strategy p  { font-size: 0.84rem; color: #64748b; margin: 0 0 0.3rem; line-height: 1.5; }
	.strategy p:last-child { margin: 0; }

	/* ── Responsive ────────────────────────────────────────── */
	@media (max-width: 640px) {
		.instructions-card { padding: 1.5rem; gap: 1.2rem; }
		.rules-grid         { grid-template-columns: 1fr; }
		.info-grid          { grid-template-columns: 1fr; }
		.clinical-grid      { grid-template-columns: 1fr; }
		.metrics-grid       { grid-template-columns: repeat(2, 1fr); }
		.steps-grid         { grid-template-columns: 1fr; }
		.header-content h1  { font-size: 1.4rem; }
		.screen-card        { padding: 1.25rem; }
		.stroop-word-large  { font-size: 3.5rem; }
		.color-patch-large  { width: 120px; height: 75px; }
		.stroop-examples    { gap: 0.5rem; }
		.ex-card            { min-width: 100px; padding: 0.75rem; }
		.color-btn          { padding: 0.55rem 1.1rem; font-size: 0.88rem; min-width: 75px; }
	}
</style>

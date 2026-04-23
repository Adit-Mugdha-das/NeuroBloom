<script>
	import { API_BASE_URL } from '$lib/api';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
import TaskReturnButton from '$lib/components/TaskReturnButton.svelte';
	import { locale, localeText } from '$lib/i18n';
	import { buildPracticePayload, getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
import { TASK_RETURN_CONTEXT } from '$lib/task-navigation';
	import { onMount } from 'svelte';

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
	let sessionData = null;
	
	// Test state
	let currentTrialIndex = 0;
	let responses = [];
	let trialStartTime = 0;
	let sessionResults = null;
	let countdown = 3;
	let taskId = null;
	
	let showHelp = false;
	/** @type {"practice" | "recorded"} */
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';
	let recordedSessionData = null;
	let countdownHandle = null;

	$: currentTrial = sessionData?.trials?.[currentTrialIndex];
	$: progress = sessionData ? ((currentTrialIndex + 1) / sessionData.total_trials * 100) : 0;
	$: trialsRemaining = sessionData ? sessionData.total_trials - currentTrialIndex : 0;

	onMount(async () => {
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

			// Check for dev tool mode - use URL difficulty parameter if present
			const urlDifficulty = $page.url.searchParams.get('difficulty');
			const isDevMode = $page.url.searchParams.get('taskId')?.includes('_dev');

			let userDifficulty = 5;

			if (isDevMode && urlDifficulty) {
				// Dev tool mode - use URL parameter
				userDifficulty = parseInt(urlDifficulty);
				console.log('🛠️ Pattern Comparison - Dev Mode - Using URL difficulty:', userDifficulty);
			} else {
				// Normal mode - fetch from training plan
				const planRes = await fetch(`${API_BASE_URL}/api/training/training-plan/${userId}`);
				const plan = await planRes.json();

				if (plan && plan.current_difficulty) {
					const currentDiff =
						typeof plan.current_difficulty === 'string'
							? JSON.parse(plan.current_difficulty)
							: plan.current_difficulty;
					userDifficulty = currentDiff.processing_speed || 5;
					console.log('📊 Pattern Comparison - Normal Mode - Using plan difficulty:', userDifficulty);
				}
			}

			difficulty = userDifficulty;

			const response = await fetch(
				`${API_BASE_URL}/api/training/tasks/pattern-comparison/generate/${userId}?difficulty=${difficulty}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' }
				}
			);

			if (!response.ok) throw new Error('Failed to load session');

			const data = await response.json();
			sessionData = structuredClone(data.session);
			recordedSessionData = structuredClone(data.session);
			
			state = STATE.INSTRUCTIONS;
		} catch (error) {
			console.error('Error loading session:', error);
			alert('Failed to load task session');
			goto('/dashboard');
		}
	}

	/** @param {"practice" | "recorded"} nextMode */
	function startTest(nextMode = TASK_PLAY_MODE.RECORDED) {
		if (countdownHandle) {
			clearInterval(countdownHandle);
			countdownHandle = null;
		}

		playMode = nextMode;
		practiceStatusMessage = '';
		sessionData = nextMode === TASK_PLAY_MODE.PRACTICE
			? buildPracticePayload('pattern-comparison', recordedSessionData)
			: structuredClone(recordedSessionData);
		state = STATE.READY;
		currentTrialIndex = 0;
		responses = [];
		countdown = 3;
		
		countdownHandle = setInterval(() => {
			countdown--;
			if (countdown <= 0) {
				clearInterval(countdownHandle);
				countdownHandle = null;
				beginTest();
			}
		}, 1000);
	}

	function leavePractice(completed = false) {
		if (countdownHandle) {
			clearInterval(countdownHandle);
			countdownHandle = null;
		}

		sessionData = structuredClone(recordedSessionData);
		playMode = TASK_PLAY_MODE.RECORDED;
		practiceStatusMessage = completed ? getPracticeCopy($locale).complete : '';
		currentTrialIndex = 0;
		responses = [];
		countdown = 3;
		state = STATE.INSTRUCTIONS;
	}

	function beginTest() {
		state = STATE.TESTING;
		currentTrialIndex = 0;
		responses = [];
		startTrial();
	}

	function startTrial() {
		trialStartTime = Date.now();
	}

	function submitAnswer(answer) {
		const reactionTime = (Date.now() - trialStartTime) / 1000;
		
		responses.push({
			trial_index: currentTrialIndex,
			user_answer: answer,
			reaction_time: reactionTime
		});
		
		// Move to next trial or complete
		if (currentTrialIndex < sessionData.total_trials - 1) {
			currentTrialIndex++;
			startTrial();
		} else {
			completeSession();
		}
	}

	async function completeSession() {
		if (playMode === TASK_PLAY_MODE.PRACTICE) {
			leavePractice(true);
			return;
		}

		state = STATE.LOADING;
		taskId = $page.url.searchParams.get('taskId');
		
		try {
			const userData = JSON.parse(localStorage.getItem('user') || '{}');
			const userId = userData.id;

			const response = await fetch(
				`${API_BASE_URL}/api/training/tasks/pattern-comparison/submit/${userId}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						difficulty: difficulty,
						session_data: sessionData,
						responses: responses,
						task_id: taskId
					})
				}
			);

			if (!response.ok) throw new Error('Failed to submit results');

			sessionResults = await response.json();
			state = STATE.COMPLETE;
		} catch (error) {
			console.error('Error submitting results:', error);
			alert('Failed to submit results');
		}
	}

	function toggleHelp() {
		showHelp = !showHelp;
	}

	function getPerformanceColor(level) {
		switch(level) {
			case 'Excellent': return '#4CAF50';
			case 'Good': return '#8BC34A';
			case 'Average': return '#FFC107';
			default: return '#FF9800';
		}
	}

	function renderPattern(pattern) {
		return pattern.map(row => row.join(' ')).join('\n');
	}
</script>

<div class="pc-container" data-localize-skip>
	<div class="pc-inner">
		{#if state === STATE.LOADING}
			<LoadingSkeleton variant="card" count={3} />

		{:else if state === STATE.INSTRUCTIONS}
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />
			<div class="instructions-card">
				<div class="header-content">
					<div class="title-row">
						<h1>Pattern Comparison</h1>
						<DifficultyBadge difficulty={sessionData?.difficulty || difficulty} domain="Processing Speed" />
					</div>
					<p class="subtitle">Same or different? Decide as fast as you can</p>
					<div class="classic-badge">Pattern Comparison · Woodcock-Johnson Tests · Salthouse (1996)</div>
				</div>

				{#if practiceStatusMessage}
					<div class="practice-note">{practiceStatusMessage}</div>
				{/if}

				<div class="task-concept">
					<h3>The Challenge</h3>
					<p>Two patterns appear side by side. Your job: decide if they are <strong>identical</strong> or <strong>different</strong> — as quickly and accurately as possible.</p>
					<div class="demo-patterns">
						<div class="demo-pattern-box">
							<div class="demo-plabel">Pattern A</div>
							<div class="demo-grid">
								<div class="demo-row"><span>■</span><span>●</span><span>▲</span></div>
								<div class="demo-row"><span>●</span><span>▲</span><span>■</span></div>
								<div class="demo-row"><span>▲</span><span>■</span><span>●</span></div>
							</div>
						</div>
						<div class="demo-vs">VS</div>
						<div class="demo-pattern-box">
							<div class="demo-plabel">Pattern B</div>
							<div class="demo-grid">
								<div class="demo-row"><span>■</span><span>●</span><span>▲</span></div>
								<div class="demo-row"><span>●</span><span>▲</span><span>■</span></div>
								<div class="demo-row"><span>▲</span><span>■</span><span>●</span></div>
							</div>
						</div>
					</div>
					<div class="demo-answer-row">
						<span class="demo-ans-same">✓ SAME</span>
						<span class="demo-ans-label">← correct answer here</span>
					</div>
				</div>

				<div class="rules-grid">
					<div class="rule-card">
						<span class="rule-icon">Look</span>
						<div class="rule-text">
							<strong>Step 1: Look</strong>
							<span>Two patterns appear — scan both quickly</span>
						</div>
					</div>
					<div class="rule-card">
						<span class="rule-icon">⊕</span>
						<div class="rule-text">
							<strong>Step 2: Compare</strong>
							<span>Are they identical or different?</span>
						</div>
					</div>
					<div class="rule-card">
						<span class="rule-icon">▷</span>
						<div class="rule-text">
							<strong>Step 3: Decide</strong>
							<span>Click SAME or DIFFERENT fast</span>
						</div>
					</div>
					<div class="rule-card">
						<span class="rule-icon">×n</span>
						<div class="rule-text">
							<strong>Step 4: Repeat</strong>
							<span>Keep going for all {sessionData?.total_trials || 25} trials</span>
						</div>
					</div>
				</div>

				<div class="info-grid">
					<div class="info-section">
						<h4>Speed Tips</h4>
						<ul class="tips-list">
							<li><strong>First glance:</strong> Trust your initial impression — it's usually right</li>
							<li><strong>Scan systematically:</strong> Row by row if unsure</li>
							<li><strong>Peripheral vision:</strong> With practice, differences pop out</li>
							<li><strong>Don't overthink:</strong> Quick decisions score higher</li>
						</ul>
					</div>
					<div class="info-section">
						<h4>Test Format</h4>
						<ul class="structure-list">
							<li><span class="struct-key">Trials</span><span class="struct-val">{sessionData?.total_trials || 25}</span></li>
							<li><span class="struct-key">Time per trial</span><span class="struct-val">{sessionData?.config?.time_per_trial || 2}s</span></li>
							<li><span class="struct-key">Pattern types</span><span class="struct-val">geometric → abstract</span></li>
							<li><span class="struct-key">Measures</span><span class="struct-val">speed + accuracy</span></li>
						</ul>
					</div>
				</div>

				<div class="clinical-info">
					<h4>Clinical Significance</h4>
					<div class="clinical-grid">
						<div class="clinical-item">
							<strong>Pure Speed</strong>
							<span>Measures processing speed with minimal motor demands</span>
						</div>
						<div class="clinical-item">
							<strong>MS Friendly</strong>
							<span>Low motor requirements — ideal for MS assessment</span>
						</div>
						<div class="clinical-item">
							<strong>Validated</strong>
							<span>Woodcock-Johnson Tests of Cognitive Abilities</span>
						</div>
						<div class="clinical-item">
							<strong>Research Based</strong>
							<span>Sensitive to cognitive processing efficiency (Salthouse, 1996)</span>
						</div>
					</div>
				</div>

				<div class="perf-guide">
					<h4>Performance Targets</h4>
					<div class="norm-bars">
						<div class="norm-bar norm-excellent">
							<span class="norm-label">Excellent</span>
							<span class="norm-val">35+ correct/min</span>
						</div>
						<div class="norm-bar norm-good">
							<span class="norm-label">Good</span>
							<span class="norm-val">25–34 correct/min</span>
						</div>
						<div class="norm-bar norm-avg">
							<span class="norm-label">Average</span>
							<span class="norm-val">15–24 correct/min</span>
						</div>
						<div class="norm-bar norm-fair">
							<span class="norm-label">Fair</span>
							<span class="norm-val">10–14 correct/min</span>
						</div>
						<div class="norm-bar norm-needs">
							<span class="norm-label">Needs Practice</span>
							<span class="norm-val">&lt;10 correct/min</span>
						</div>
					</div>
					<p class="norm-note">*Based on Salthouse (1996) processing speed research</p>
				</div>

				<div class="button-group">
					<TaskPracticeActions
						locale={$locale}
						startLabel={localeText({ en: 'Start Actual Task', bn: 'আসল টাস্ক শুরু করুন' }, $locale)}
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
				<h2>Get Ready!</h2>
				<p class="ready-message">Compare patterns and decide: SAME or DIFFERENT</p>
				<div class="ready-demo">
					<div class="rdy-pattern-box">Pattern A</div>
					<div class="rdy-vs">vs</div>
					<div class="rdy-pattern-box">Pattern B</div>
				</div>
				<div class="rdy-buttons">
					<div class="rdy-btn rdy-same">✓ SAME</div>
					<div class="rdy-btn rdy-diff">✗ DIFFERENT</div>
				</div>
				<div class="countdown">{countdown}</div>
			</div>

		{:else if state === STATE.TESTING}
			<div class="screen-card testing-screen">
				{#if playMode === TASK_PLAY_MODE.PRACTICE}
					<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
				{/if}
				<div class="test-header">
					<div class="test-badges">
						<span class="count-badge">Trial {currentTrialIndex + 1} / {sessionData.total_trials}</span>
						{#if currentTrial}
							<span class="type-badge">
								{#if currentTrial.pattern_type === 'simple_geometric'}Simple
								{:else if currentTrial.pattern_type === 'complex'}Complex
								{:else}Abstract{/if}
							</span>
							<span class="grid-badge">{currentTrial.pattern_size}×{currentTrial.pattern_size}</span>
						{/if}
					</div>
					<div class="progress-track">
						<div class="progress-fill" style="width: {progress}%"></div>
					</div>
					<button class="help-btn-sm" on:click={toggleHelp}>?</button>
				</div>

				{#if currentTrial}
					<div class="patterns-display">
						<div class="pattern-panel">
							<div class="p-label">Pattern A</div>
							<div class="pattern-grid size-{currentTrial.pattern_size}">
								{#each currentTrial.pattern_a as row}
									<div class="pattern-row">
										{#each row as cell}
											<div class="pattern-cell">{cell}</div>
										{/each}
									</div>
								{/each}
							</div>
						</div>

						<div class="vs-divider"><span>VS</span></div>

						<div class="pattern-panel">
							<div class="p-label">Pattern B</div>
							<div class="pattern-grid size-{currentTrial.pattern_size}">
								{#each currentTrial.pattern_b as row}
									<div class="pattern-row">
										{#each row as cell}
											<div class="pattern-cell">{cell}</div>
										{/each}
									</div>
								{/each}
							</div>
						</div>
					</div>

					<div class="decision-area">
						<p class="decision-question">Are these patterns the same or different?</p>
						<div class="decision-buttons">
							<button class="decision-btn same-btn" on:click={() => submitAnswer('SAME')}>
								<span class="dbtn-icon">✓</span>
								<span class="dbtn-text">SAME</span>
							</button>
							<button class="decision-btn diff-btn" on:click={() => submitAnswer('DIFFERENT')}>
								<span class="dbtn-icon">✗</span>
								<span class="dbtn-text">DIFFERENT</span>
							</button>
						</div>
						<p class="time-hint">Time limit: {currentTrial.time_limit}s per trial</p>
					</div>
				{/if}
			</div>

		{:else if state === STATE.COMPLETE}
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />
			<div class="screen-card complete-screen">
				{#if sessionResults}
					{@const perfColor = getPerformanceColor(sessionResults.metrics.performance_level)}
					<div class="perf-banner" style="--perf-color: {perfColor}">
						<div class="perf-level">{sessionResults.metrics.performance_level}</div>
						<div class="perf-subtitle">{sessionResults.metrics.processing_speed} correct/min · Pattern Comparison Complete!</div>
					</div>

					<div class="metrics-grid">
						<div class="metric-card highlight">
							<div class="metric-icon">→</div>
							<div class="metric-value">{sessionResults.metrics.processing_speed}</div>
							<div class="metric-label">Processing Speed</div>
							<div class="metric-sub">correct responses/min</div>
						</div>
						<div class="metric-card">
							<div class="metric-icon">◎</div>
							<div class="metric-value">{sessionResults.metrics.score}</div>
							<div class="metric-label">Score</div>
							<div class="metric-sub">out of 100</div>
						</div>
						<div class="metric-card">
							<div class="metric-icon">✓</div>
							<div class="metric-value">{sessionResults.metrics.accuracy}%</div>
							<div class="metric-label">Accuracy</div>
							<div class="metric-sub">{sessionResults.metrics.correct_count}/{sessionResults.metrics.total_trials} correct</div>
						</div>
						<div class="metric-card">
							<div class="metric-icon">⏱️</div>
							<div class="metric-value">{sessionResults.metrics.average_reaction_time}s</div>
							<div class="metric-label">Avg Response Time</div>
							<div class="metric-sub">per trial</div>
						</div>
					</div>

					<div class="breakdown">
						<h3>Detailed Analysis</h3>
						<div class="breakdown-row">
							<span class="bd-label">Total Trials</span>
							<span class="bd-val">{sessionResults.metrics.total_trials}</span>
						</div>
						<div class="breakdown-row">
							<span class="bd-label">Correct Answers</span>
							<span class="bd-val bd-success">{sessionResults.metrics.correct_count}</span>
						</div>
						<div class="breakdown-row">
							<span class="bd-label">Timeouts</span>
							<span class="bd-val" class:bd-error={sessionResults.metrics.timeout_count > 0} class:bd-success={sessionResults.metrics.timeout_count === 0}>
								{sessionResults.metrics.timeout_count}
							</span>
						</div>
						<div class="breakdown-row">
							<span class="bd-label">Consistency</span>
							<span class="bd-val">{sessionResults.metrics.consistency}%</span>
						</div>
						<div class="breakdown-row">
							<span class="bd-label">Total Time</span>
							<span class="bd-val">{sessionResults.metrics.total_time}s</span>
						</div>
						<div class="breakdown-row">
							<span class="bd-label">Performance Level</span>
							<span class="bd-val" style="color: {perfColor}">{sessionResults.metrics.performance_level}</span>
						</div>
					</div>

					<div class="clinical-note">
						<h4>Clinical Context</h4>
						<p>
							{#if sessionResults.metrics.performance_level === 'Excellent'}
								Outstanding processing speed! Your performance of <strong>{sessionResults.metrics.processing_speed} correct/min</strong> is well above average, indicating excellent cognitive efficiency and visual processing.
							{:else if sessionResults.metrics.performance_level === 'Good'}
								Great performance! Your speed of <strong>{sessionResults.metrics.processing_speed} correct/min</strong> is above average, showing strong pattern recognition and quick decision-making.
							{:else if sessionResults.metrics.performance_level === 'Average'}
								Good work! Your speed of <strong>{sessionResults.metrics.processing_speed} correct/min</strong> is in the normal range. Regular practice can help improve your pattern recognition speed.
							{:else}
								Keep practicing! Processing speed improves significantly with regular training. Pattern comparison builds quick visual processing and decision-making skills.
							{/if}
						</p>
						<p class="why-matters"><strong>Why this matters for MS:</strong> Pattern comparison requires minimal motor skill — just clicking — making it an excellent measure of pure cognitive processing speed unaffected by physical limitations.</p>
					</div>

					<div class="difficulty-info">
						<span>Difficulty: <strong>{sessionResults.difficulty_before}</strong> → <strong>{sessionResults.difficulty_after}</strong></span>
						<span class="adapt-reason">{sessionResults.adaptation_reason}</span>
					</div>

					{#if sessionResults.new_badges && sessionResults.new_badges.length > 0}
						<BadgeNotification badges={sessionResults.new_badges} />
					{/if}

					<div class="button-group">
						<button class="start-button" on:click={() => goto('/dashboard')}>Back to Dashboard</button>
						<button class="btn-secondary" on:click={() => goto('/dashboard')}>View Dashboard</button>
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>

{#if showHelp}
	<div class="modal-overlay" on:click={toggleHelp} role="presentation">
		<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
		<div class="modal-content" on:click|stopPropagation role="dialog" tabindex="-1" on:keydown={(e) => e.key === 'Escape' && toggleHelp()}>
			<button class="close-btn" on:click={toggleHelp}>×</button>
			<h2>Pattern Comparison Strategies</h2>
			<div class="strategy">
				<h3>Quick Visual Scan</h3>
				<p>Your first impression is often correct. Scan both patterns simultaneously rather than examining each in detail.</p>
			</div>
			<div class="strategy">
				<h3>Systematic Approach</h3>
				<p>If unsure, scan row by row (top to bottom) or column by column. This ensures you don't miss differences.</p>
			</div>
			<div class="strategy">
				<h3>Speed vs Accuracy</h3>
				<p>The "correct/min" metric rewards both speed and accuracy. Fast but wrong is worse than slightly slow but accurate.</p>
			</div>
			<div class="strategy">
				<h3>Peripheral Vision</h3>
				<p>With practice, look at the centre and let peripheral vision catch differences automatically.</p>
			</div>
			<div class="strategy">
				<h3>Pattern Recognition</h3>
				<p>Your brain improves at this with repetition. Trust your pattern recognition — don't overthink it.</p>
			</div>
			<div class="strategy">
				<h3>Why This Matters</h3>
				<p>This test measures pure cognitive processing speed without complex motor demands — ideal for assessing MS-related cognitive changes.</p>
			</div>
		</div>
	</div>
{/if}

<style>
	/* ── Container ─────────────────────────────────────────── */
	.pc-container {
		min-height: 100vh;
		background: #C8DEFA;
		padding: 2rem 1rem;
	}

	.pc-inner {
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
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		flex-wrap: wrap;
		margin-bottom: 0.5rem;
	}

	.header-content h1 {
		font-size: 1.8rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0;
	}

	.subtitle {
		color: #64748b;
		font-size: 1rem;
		margin: 0.4rem 0 0.8rem;
	}

	.classic-badge {
		display: inline-block;
		background: rgba(102, 126, 234, 0.12);
		color: #667eea;
		border: 1px solid rgba(102, 126, 234, 0.3);
		border-radius: 20px;
		padding: 0.3rem 1rem;
		font-size: 0.82rem;
		font-weight: 600;
	}

	.practice-note {
		background: #fef9c3;
		border: 1px solid #fde047;
		border-radius: 8px;
		padding: 0.75rem 1rem;
		color: #854d0e;
		font-size: 0.9rem;
		text-align: center;
	}

	/* ── Task concept (teal for visual matching) ───────────── */
	.task-concept {
		background: linear-gradient(135deg, #f0fdfa, #ccfbf1);
		border: 1px solid #99f6e4;
		border-radius: 12px;
		padding: 1.5rem;
	}

	.task-concept h3 {
		font-size: 1rem;
		font-weight: 700;
		color: #0f766e;
		margin: 0 0 0.6rem;
	}

	.task-concept p {
		color: #134e4a;
		margin: 0 0 1.2rem;
		line-height: 1.6;
	}

	.demo-patterns {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1.5rem;
		flex-wrap: wrap;
		margin-bottom: 1rem;
	}

	.demo-pattern-box { text-align: center; }

	.demo-plabel {
		font-weight: 700;
		font-size: 0.82rem;
		color: #0f766e;
		margin-bottom: 0.4rem;
	}

	.demo-grid {
		background: white;
		padding: 0.6rem;
		border-radius: 8px;
		box-shadow: 0 2px 6px rgba(0,0,0,0.08);
		display: inline-block;
	}

	.demo-row {
		display: flex;
		gap: 0.3rem;
		margin-bottom: 0.3rem;
	}

	.demo-row:last-child { margin-bottom: 0; }

	.demo-row span {
		width: 32px;
		height: 32px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.1rem;
		background: #f0fdfa;
		border-radius: 4px;
	}

	.demo-vs {
		font-size: 1.4rem;
		font-weight: 800;
		color: #0f766e;
	}

	.demo-answer-row {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.75rem;
	}

	.demo-ans-same {
		background: #dcfce7;
		color: #166534;
		padding: 0.35rem 0.9rem;
		border-radius: 8px;
		font-weight: 700;
		font-size: 0.9rem;
	}

	.demo-ans-label {
		font-size: 0.82rem;
		color: #64748b;
		font-style: italic;
	}

	/* ── Rules grid ────────────────────────────────────────── */
	.rules-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}

	.rule-card {
		display: flex;
		align-items: flex-start;
		gap: 0.8rem;
		padding: 1rem;
		background: #f8fafc;
		border-radius: 10px;
		border-left: 4px solid #14b8a6;
	}

	.rule-icon { font-size: 1.5rem; flex-shrink: 0; }

	.rule-text { display: flex; flex-direction: column; gap: 0.2rem; }

	.rule-text strong { font-size: 0.9rem; color: #1e293b; }

	.rule-text span { font-size: 0.82rem; color: #64748b; line-height: 1.4; }

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
		border: 1px solid #bbf7d0;
		border-radius: 12px;
		padding: 1.2rem;
	}

	.clinical-info h4 { font-size: 0.9rem; font-weight: 700; color: #166534; margin: 0 0 0.8rem; }

	.clinical-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }

	.clinical-item { display: flex; flex-direction: column; gap: 0.2rem; }
	.clinical-item strong { font-size: 0.82rem; color: #166534; }
	.clinical-item span { font-size: 0.8rem; color: #15803d; }

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

	.norm-note { font-size: 0.78rem; color: #94a3b8; font-style: italic; margin: 0.5rem 0 0; text-align: center; }

	/* ── Button group ──────────────────────────────────────── */
	.button-group {
		display: flex; justify-content: center; gap: 1rem;
		flex-wrap: wrap; padding-top: 0.5rem;
	}

	.start-button {
		background: #4338ca;
		color: white; border: none; border-radius: 10px;
		padding: 0.85rem 2.5rem; font-size: 1rem; font-weight: 700;
		cursor: pointer; transition: transform 0.15s, box-shadow 0.15s;
		box-shadow: 0 4px 14px rgba(67, 56, 202, 0.35);
	}

	.start-button:hover {
		transform: translateY(-2px);
		box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
	}

	.btn-secondary {
		background: white; color: #667eea;
		border: 2px solid #667eea; border-radius: 10px;
		padding: 0.85rem 2rem; font-size: 1rem; font-weight: 600;
		cursor: pointer; transition: all 0.15s;
	}

	.btn-secondary:hover { background: rgba(102, 126, 234, 0.08); }

	/* ── Screen card ───────────────────────────────────────── */
	.screen-card {
		background: white; border-radius: 16px; padding: 2.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
	}

	/* ── Ready screen ──────────────────────────────────────── */
	.ready-screen { text-align: center; }

	.ready-screen h2 { font-size: 1.8rem; font-weight: 700; color: #1e293b; margin: 0 0 0.5rem; }

	.ready-message { color: #64748b; font-size: 1.05rem; margin: 0 0 1.5rem; }

	.ready-demo {
		display: flex; align-items: center; justify-content: center;
		gap: 1.5rem; margin: 1.5rem 0;
	}

	.rdy-pattern-box {
		width: 120px; height: 80px;
		border: 3px solid #14b8a6; border-radius: 10px;
		display: flex; align-items: center; justify-content: center;
		font-weight: 700; color: #0f766e; background: #f0fdfa;
	}

	.rdy-vs { font-size: 1.4rem; font-weight: 800; color: #14b8a6; }

	.rdy-buttons {
		display: flex; align-items: center; justify-content: center; gap: 1rem; margin: 1rem 0;
	}

	.rdy-btn {
		padding: 0.6rem 1.5rem; border-radius: 8px;
		font-weight: 700; font-size: 0.95rem; opacity: 0.75;
	}

	.rdy-same    { background: #dcfce7; color: #166534; }
	.rdy-diff    { background: #fee2e2; color: #991b1b; }

	.countdown {
		font-size: 4.5rem; font-weight: 800; color: #14b8a6; margin-top: 1.5rem;
		animation: pulse 1s ease-in-out infinite;
	}

	@keyframes pulse {
		0%, 100% { transform: scale(1); opacity: 1; }
		50% { transform: scale(1.08); opacity: 0.75; }
	}

	/* ── Testing screen ────────────────────────────────────── */
	.testing-screen { padding: 1.25rem; }

	.test-header {
		display: flex; justify-content: space-between; align-items: center;
		margin-bottom: 1rem; flex-wrap: wrap; gap: 0.5rem;
	}

	.test-badges { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; flex: 1; }

	.count-badge {
		background: rgba(102, 126, 234, 0.12); color: #667eea;
		padding: 0.4rem 0.9rem; border-radius: 20px; font-size: 0.85rem; font-weight: 700;
	}

	.type-badge {
		background: #f0fdfa; color: #0f766e;
		padding: 0.4rem 0.9rem; border-radius: 20px; font-size: 0.82rem; font-weight: 600;
	}

	.grid-badge {
		background: #fef9c3; color: #854d0e;
		padding: 0.4rem 0.8rem; border-radius: 20px; font-size: 0.82rem; font-weight: 600;
	}

	.progress-track {
		flex: 1; height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden; min-width: 80px;
	}

	.progress-fill { height: 100%; background: linear-gradient(90deg, #14b8a6, #0d9488); border-radius: 3px; transition: width 0.3s; }

	.help-btn-sm {
		width: 36px; height: 36px; border-radius: 50%;
		border: 2px solid #667eea; background: white; color: #667eea;
		font-size: 1.1rem; font-weight: 700; cursor: pointer;
		transition: all 0.2s; display: flex; align-items: center; justify-content: center;
	}

	.help-btn-sm:hover { background: #667eea; color: white; }

	/* ── Patterns display ──────────────────────────────────── */
	.patterns-display {
		display: flex; align-items: center; justify-content: center;
		gap: 2rem; margin: 1.5rem 0; flex-wrap: wrap;
	}

	.pattern-panel { text-align: center; }

	.p-label {
		font-weight: 700; font-size: 0.88rem; color: #64748b; margin-bottom: 0.5rem;
		letter-spacing: 0.05em;
	}

	.pattern-grid {
		background: #f8fafc; border: 1px solid #e2e8f0;
		border-radius: 10px; padding: 0.75rem; display: inline-block;
		box-shadow: 0 2px 8px rgba(0,0,0,0.06);
	}

	.pattern-row { display: flex; gap: 0.35rem; margin-bottom: 0.35rem; }
	.pattern-row:last-child { margin-bottom: 0; }

	.pattern-cell {
		display: flex; align-items: center; justify-content: center;
		background: white; border-radius: 5px; font-weight: 600; color: #1e293b;
		box-shadow: 0 1px 3px rgba(0,0,0,0.06);
	}

	.pattern-grid.size-3 .pattern-cell { width: 40px; height: 40px; font-size: 1.2rem; }
	.pattern-grid.size-4 .pattern-cell { width: 36px; height: 36px; font-size: 1.1rem; }
	.pattern-grid.size-5 .pattern-cell { width: 32px; height: 32px; font-size: 1rem; }

	.vs-divider {
		font-size: 1.5rem; font-weight: 800; color: #94a3b8;
		background: #f1f5f9; padding: 0.5rem 0.9rem; border-radius: 8px;
	}

	/* ── Decision area ─────────────────────────────────────── */
	.decision-area { text-align: center; margin-top: 1.5rem; }

	.decision-question {
		font-size: 1.05rem; font-weight: 600; color: #1e293b; margin: 0 0 1.2rem;
	}

	.decision-buttons { display: flex; gap: 1.5rem; justify-content: center; flex-wrap: wrap; }

	.decision-btn {
		display: flex; flex-direction: column; align-items: center; gap: 0.3rem;
		padding: 1rem 2.5rem; border: none; border-radius: 12px;
		cursor: pointer; font-weight: 700; transition: transform 0.15s, box-shadow 0.15s;
		min-width: 140px;
	}

	.same-btn {
		background: linear-gradient(135deg, #16a34a, #15803d);
		color: white; box-shadow: 0 4px 12px rgba(22, 163, 74, 0.35);
	}

	.same-btn:hover { transform: translateY(-3px); box-shadow: 0 6px 18px rgba(22, 163, 74, 0.5); }

	.diff-btn {
		background: linear-gradient(135deg, #dc2626, #b91c1c);
		color: white; box-shadow: 0 4px 12px rgba(220, 38, 38, 0.35);
	}

	.diff-btn:hover { transform: translateY(-3px); box-shadow: 0 6px 18px rgba(220, 38, 38, 0.5); }

	.dbtn-icon { font-size: 1.8rem; }
	.dbtn-text { font-size: 1rem; letter-spacing: 0.05em; }

	.time-hint { font-size: 0.8rem; color: #94a3b8; margin-top: 0.8rem; }

	/* ── Complete screen ───────────────────────────────────── */
	.complete-screen { display: flex; flex-direction: column; gap: 1.5rem; }

	.perf-banner {
		text-align: center; padding: 1.5rem;
		background: linear-gradient(135deg, color-mix(in srgb, var(--perf-color) 10%, white), color-mix(in srgb, var(--perf-color) 20%, white));
		border: 2px solid var(--perf-color); border-radius: 14px;
	}

	.perf-emoji { font-size: 2.5rem; margin-bottom: 0.25rem; }

	.perf-level { font-size: 1.8rem; font-weight: 800; color: var(--perf-color); }

	.perf-subtitle { font-size: 0.95rem; color: #64748b; margin-top: 0.3rem; }

	.metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; }

	.metric-card {
		background: #f8fafc; border: 1px solid #e2e8f0;
		border-radius: 12px; padding: 1.2rem; text-align: center;
	}

	.metric-card.highlight {
		background: linear-gradient(135deg, #14b8a6, #0d9488);
		color: white; border-color: transparent;
	}

	.metric-icon { font-size: 1.8rem; margin-bottom: 0.4rem; }

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

	.bd-label { color: #64748b; }
	.bd-val   { font-weight: 700; color: #667eea; }
	.bd-error   { color: #dc2626; }
	.bd-success { color: #16a34a; }

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
		background: #f0fdfa; border: 1px solid #99f6e4; border-radius: 10px;
		padding: 0.9rem 1.2rem; display: flex; justify-content: space-between;
		align-items: center; flex-wrap: wrap; gap: 0.5rem;
		font-size: 0.88rem; font-weight: 600; color: #0f766e;
	}

	.adapt-reason { color: #14b8a6; font-weight: 400; font-style: italic; }

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
		border-radius: 8px; border-left: 4px solid #14b8a6; margin-bottom: 0.75rem;
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
		.patterns-display { gap: 0.75rem; }
		.decision-btn { padding: 0.85rem 1.5rem; min-width: 110px; }
	}
</style>


<script>
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

	const STATE = {
		LOADING: 'loading',
		INSTRUCTIONS: 'instructions',
		READY: 'ready',
		PLAYING: 'playing',
		COMPLETE: 'complete'
	};

	let state = STATE.LOADING;
	let difficulty = 5;
	let sessionData = null;
	let currentTrialIndex = 0;
	let currentTrial = null;
	let progress = 0;
	let countdown = 3;
	let taskId = null;
	let showHelp = false;
	let stimulusVisible = false;
	let responseWindowOpen = false;
	let sessionStartedAt = 0;
	let stimulusStartAt = 0;
	let selectedKey = '';
	let responses = [];
	let sessionResults = null;
	let newBadges = [];
	let timerHandle;
	let countdownHandle;
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';
	let recordedSessionData = null;

	const keyLabels = {
		'1': '1',
		'2': '2',
		'3': '3',
		'4': '4'
	};

	onMount(async () => {
		taskId = $page.url.searchParams.get('taskId');
		window.addEventListener('keydown', handleKeyDown);
		await loadSession();

		return () => {
			window.removeEventListener('keydown', handleKeyDown);
			if (timerHandle) clearTimeout(timerHandle);
			if (countdownHandle) clearInterval(countdownHandle);
		};
	});

	async function loadSession() {
		try {
			const userData = JSON.parse(localStorage.getItem('user') || '{}');
			const userId = userData.id;
			if (!userId) {
				goto('/login');
				return;
			}

			const urlDifficulty = Number.parseInt($page.url.searchParams.get('difficulty') || '', 10);
			if (Number.isInteger(urlDifficulty) && urlDifficulty >= 1 && urlDifficulty <= 10) {
				difficulty = urlDifficulty;
			} else {
				const planRes = await fetch(`http://localhost:8000/api/training/training-plan/${userId}`);
				const plan = await planRes.json();
				if (plan?.current_difficulty) {
					const currentDiff =
						typeof plan.current_difficulty === 'string'
							? JSON.parse(plan.current_difficulty)
							: plan.current_difficulty;
					difficulty = currentDiff.processing_speed || 5;
				}
			}

			const response = await fetch(
				`http://localhost:8000/api/training/tasks/choice-reaction-time/generate/${userId}?difficulty=${difficulty}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' }
				}
			);

			if (!response.ok) throw new Error('Failed to load Choice Reaction Time');

			const data = await response.json();
			sessionData = data.session;
			recordedSessionData = data.session;
			state = STATE.INSTRUCTIONS;
		} catch (error) {
			console.error('Error loading Choice Reaction Time:', error);
			alert('Failed to load task session');
			goto('/dashboard');
		}
	}

	function startTask(nextMode = TASK_PLAY_MODE.RECORDED) {
		if (timerHandle) clearTimeout(timerHandle);
		if (countdownHandle) clearInterval(countdownHandle);

		playMode = nextMode;
		practiceStatusMessage = '';
		sessionData =
			nextMode === TASK_PLAY_MODE.PRACTICE
				? buildPracticePayload('choice-reaction-time', recordedSessionData)
				: structuredClone(recordedSessionData);
		state = STATE.READY;
		countdown = 3;
		sessionStartedAt = Date.now();
		currentTrialIndex = 0;
		responses = [];

		countdownHandle = setInterval(() => {
			countdown -= 1;
			if (countdown <= 0) {
				clearInterval(countdownHandle);
				countdownHandle = null;
				beginTrial();
			}
		}, 1000);
	}

	function leavePractice(completed = false) {
		if (timerHandle) {
			clearTimeout(timerHandle);
			timerHandle = null;
		}
		if (countdownHandle) {
			clearInterval(countdownHandle);
			countdownHandle = null;
		}

		sessionData = structuredClone(recordedSessionData);
		playMode = TASK_PLAY_MODE.RECORDED;
		practiceStatusMessage = completed ? getPracticeCopy($locale).complete : '';
		currentTrialIndex = 0;
		currentTrial = null;
		progress = 0;
		countdown = 3;
		stimulusVisible = false;
		responseWindowOpen = false;
		selectedKey = '';
		responses = [];
		state = STATE.INSTRUCTIONS;
	}

	function beginTrial() {
		currentTrial = sessionData.trials[currentTrialIndex];
		progress = ((currentTrialIndex + 1) / sessionData.total_trials) * 100;
		selectedKey = '';
		stimulusVisible = true;
		responseWindowOpen = true;
		stimulusStartAt = performance.now();
		state = STATE.PLAYING;

		if (timerHandle) clearTimeout(timerHandle);
		timerHandle = setTimeout(() => {
			if (responseWindowOpen) submitChoice('');
		}, currentTrial.max_response_ms);
	}

	function handleKeyDown(event) {
		if (state !== STATE.PLAYING || !responseWindowOpen) return;
		if (!['1', '2', '3', '4'].includes(event.key)) return;
		event.preventDefault();
		submitChoice(event.key);
	}

	function submitChoice(userKey) {
		if (!responseWindowOpen || !currentTrial) return;

		if (timerHandle) clearTimeout(timerHandle);
		responseWindowOpen = false;
		selectedKey = userKey;

		const reactionTime = userKey ? Math.round(performance.now() - stimulusStartAt) : currentTrial.max_response_ms + 1;
		responses = [
			...responses,
			{
				trial_index: currentTrial.trial_index,
				user_key: userKey,
				reaction_time: reactionTime
			}
		];

		stimulusVisible = false;

		if (currentTrialIndex < sessionData.total_trials - 1) {
			currentTrialIndex += 1;
			timerHandle = setTimeout(beginTrial, currentTrial.iti_ms);
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

		try {
			const userData = JSON.parse(localStorage.getItem('user') || '{}');
			const userId = userData.id;

			const response = await fetch(
				`http://localhost:8000/api/training/tasks/choice-reaction-time/submit/${userId}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						difficulty,
						session_data: sessionData,
						responses,
						task_id: taskId
					})
				}
			);

			if (!response.ok) throw new Error('Failed to submit results');

			sessionResults = await response.json();
			newBadges = sessionResults.new_badges || [];
			state = STATE.COMPLETE;
		} catch (error) {
			console.error('Error submitting results:', error);
			alert('Failed to submit results');
			goto('/dashboard');
		}
	}

	function shapeClass(shape) {
		return `stimulus-shape ${shape}`;
	}

	$: activeStimuli = sessionData?.stimuli || [];
</script>

<div class="crt-page">
	{#if state === STATE.LOADING}
		<LoadingSkeleton variant="card" count={3} />
	{:else if state === STATE.INSTRUCTIONS}
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />
		<section class="panel hero">
			<div class="header">
				<div>
					<p class="eyebrow">Processing Speed Training</p>
					<h1>Choice Reaction Time</h1>
					<p class="subtitle">
						A target appears in the center. Identify it and press the matching key or button as quickly
						as you can. This trains decision speed, not just simple tapping speed.
					</p>
				</div>
				<DifficultyBadge {difficulty} domain="Processing Speed" />
			</div>

			<div class="layout">
				<div class="card mapping">
					<h2>Response Map</h2>
					<div class="mapping-grid">
						{#each activeStimuli as stimulus}
							<div class="mapping-item">
								<div class={shapeClass(stimulus.shape)} style={`background:${stimulus.color}`}></div>
								<div class="mapping-text">
									<strong>{stimulus.label}</strong>
									<span>Press {stimulus.key}</span>
								</div>
							</div>
						{/each}
					</div>
				</div>

				<div class="card details">
					<h2>How It Works</h2>
					<ul>
						<li>You will complete {sessionData.total_trials} rapid identification trials.</li>
						<li>Respond inside the time window or the trial counts as a timeout.</li>
						<li>Accuracy matters first. Fast but wrong decisions lower your score quickly.</li>
					</ul>

					<button class="ghost" on:click={() => (showHelp = !showHelp)}>
						{showHelp ? 'Hide tips' : 'Show tips'}
					</button>

					{#if showHelp}
						<div class="help">
							<p>Keep your fingers resting near the response keys before the cue appears.</p>
							<p>Use the same hand position throughout the block to reduce movement cost.</p>
							<p>If accuracy slips, slow down slightly rather than guessing.</p>
						</div>
					{/if}
				</div>
			</div>

			<div class="actions">
				<TaskPracticeActions
					locale={$locale}
					startLabel={localeText({ en: 'Start Actual Task', bn: 'আসল টাস্ক শুরু করুন' }, $locale)}
					statusMessage={practiceStatusMessage}
					on:start={() => startTask(TASK_PLAY_MODE.RECORDED)}
					on:practice={() => startTask(TASK_PLAY_MODE.PRACTICE)}
				/>			</div>
		</section>
	{:else if state === STATE.READY}
		<section class="panel ready">
			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
			{/if}
			<p class="eyebrow">Get Ready</p>
			<h2>{countdown}</h2>
			<p>Keep your eyes on the center and your fingers near the mapped keys.</p>
		</section>
	{:else if state === STATE.PLAYING}
		<section class="panel play">
			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
			{/if}
			<div class="play-header">
				<div>
					<p class="eyebrow">Trial {currentTrialIndex + 1} of {sessionData.total_trials}</p>
					<h2>Identify And Respond</h2>
				</div>
				<div class="mini-map">
					{#each activeStimuli as stimulus}
						<div class="mini-item">
							<span>{stimulus.key}</span>
							<small>{stimulus.label}</small>
						</div>
					{/each}
				</div>
			</div>

			<div class="progress-track">
				<div class="progress-fill" style={`width:${progress}%`}></div>
			</div>

			<div class="arena">
				<div class="stimulus-stage">
					{#if stimulusVisible && currentTrial}
						<div class={shapeClass(currentTrial.shape)} style={`background:${currentTrial.color}`}></div>
					{:else}
						<div class="fixation">+</div>
					{/if}
				</div>

				<div class="buttons">
					{#each activeStimuli as stimulus}
						<button
							class={`choice-button ${selectedKey === stimulus.key ? 'selected' : ''}`}
							on:click={() => submitChoice(stimulus.key)}
							disabled={!responseWindowOpen}
						>
							<span class="keycap">{stimulus.key}</span>
							<span>{stimulus.label}</span>
						</button>
					{/each}
				</div>
			</div>
		</section>
	{:else if state === STATE.COMPLETE}
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />
		<section class="panel hero">
			<div class="header">
				<div>
					<p class="eyebrow">Session Complete</p>
					<h1>Choice Reaction Time Results</h1>
					<p class="subtitle">Decision speed and accuracy were recorded for your processing-speed profile.</p>
				</div>
			</div>

			{#if newBadges.length > 0}
				<BadgeNotification badges={newBadges} />
			{/if}

			<div class="results">
				<div class="metric primary">
					<span>Overall score</span>
					<strong>{sessionResults.metrics.score}</strong>
				</div>
				<div class="metric">
					<span>Accuracy</span>
					<strong>{sessionResults.metrics.accuracy.toFixed(1)}%</strong>
				</div>
				<div class="metric">
					<span>Average RT</span>
					<strong>{sessionResults.metrics.average_reaction_time.toFixed(0)} ms</strong>
				</div>
				<div class="metric">
					<span>Decision efficiency</span>
					<strong>{sessionResults.metrics.decision_efficiency.toFixed(1)}</strong>
				</div>
				<div class="metric">
					<span>Consistency</span>
					<strong>{sessionResults.metrics.consistency.toFixed(1)}%</strong>
				</div>
				<div class="metric">
					<span>Timeouts</span>
					<strong>{sessionResults.metrics.timeout_count}</strong>
				</div>
			</div>

			<div class="difficulty">
				<span>Level {sessionResults.difficulty_before}</span>
				<span class="arrow">→</span>
				<span>Level {sessionResults.difficulty_after}</span>
			</div>
			<p class="subtitle center">{sessionResults.adaptation_reason}</p>

			<div class="actions">
				<button class="primary" on:click={() => goto('/dashboard')}>Back To Dashboard</button>
				<button class="secondary" on:click={() => goto('/dashboard')}>Back To Dashboard</button>
			</div>
		</section>
	{/if}
</div>

<style>
	:global(body) {
		background:
			radial-gradient(circle at top, rgba(11, 100, 124, 0.12), transparent 34%),
			linear-gradient(180deg, #f8fbfd 0%, #eef4f7 100%);
	}

	.crt-page {
		min-height: 100vh;
		padding: 2rem 1rem 3rem;
		color: #183347;
	}

	.panel {
		max-width: 980px;
		margin: 0 auto;
		background: rgba(255, 255, 255, 0.9);
		border: 1px solid rgba(118, 145, 163, 0.18);
		border-radius: 26px;
		padding: 2rem;
		box-shadow: 0 24px 60px rgba(19, 52, 74, 0.1);
	}

	.header, .layout, .actions, .mapping-grid, .play-header, .mini-map, .buttons, .results {
		display: flex;
		gap: 1rem;
	}

	.header, .play-header {
		justify-content: space-between;
		align-items: flex-start;
	}

	.eyebrow {
		margin: 0 0 0.5rem;
		text-transform: uppercase;
		letter-spacing: 0.16em;
		font-size: 0.78rem;
		font-weight: 700;
		color: #0f6e80;
	}

	h1 {
		font-size: clamp(2rem, 4vw, 3.2rem);
		margin: 0 0 0.75rem;
	}

	h2 {
		margin-top: 0;
	}

	.subtitle {
		max-width: 52rem;
		line-height: 1.6;
		color: #4d6675;
	}

	.subtitle.center {
		text-align: center;
		margin: 1rem auto 0;
	}

	.layout, .results, .mapping-grid, .buttons {
		flex-wrap: wrap;
	}

	.card, .metric {
		flex: 1 1 280px;
		padding: 1.25rem;
		border-radius: 22px;
		background: linear-gradient(180deg, rgba(255,255,255,0.95), rgba(241,247,250,0.92));
		border: 1px solid rgba(118,145,163,0.14);
	}

	.mapping-item, .mini-item {
		display: flex;
		align-items: center;
		gap: 0.8rem;
		padding: 0.75rem;
		border-radius: 18px;
		background: rgba(15, 110, 128, 0.06);
	}

	.mapping-text {
		display: flex;
		flex-direction: column;
	}

	.actions {
		margin-top: 1.5rem;
	}

	button {
		border: none;
		cursor: pointer;
		font-weight: 700;
	}

	.primary, .secondary, .ghost {
		padding: 0.95rem 1.35rem;
		border-radius: 16px;
	}

	.primary {
		background: linear-gradient(135deg, #0f6e80, #104a72);
		color: white;
	}

	.secondary, .ghost {
		background: rgba(84, 103, 118, 0.1);
		color: #294355;
	}

	.help {
		margin-top: 1rem;
		padding: 1rem;
		border-radius: 16px;
		background: rgba(15, 110, 128, 0.08);
	}

	.ready {
		text-align: center;
	}

	.ready h2 {
		font-size: 5rem;
		margin: 0.5rem 0 1rem;
	}

	.mini-map {
		flex-wrap: wrap;
	}

	.mini-item {
		flex-direction: column;
		align-items: flex-start;
		padding: 0.65rem 0.8rem;
	}

	.progress-track {
		height: 10px;
		background: rgba(118,145,163,0.2);
		border-radius: 999px;
		margin: 1.2rem 0 1.8rem;
		overflow: hidden;
	}

	.progress-fill {
		height: 100%;
		background: linear-gradient(90deg, #0f6e80, #48b4a9);
	}

	.arena {
		display: grid;
		grid-template-columns: 1.2fr 1fr;
		gap: 1.25rem;
		align-items: center;
	}

	.stimulus-stage {
		min-height: 300px;
		border-radius: 28px;
		background: linear-gradient(180deg, #f3f8fb, #e4edf2);
		display: flex;
		align-items: center;
		justify-content: center;
		border: 1px solid rgba(118,145,163,0.18);
	}

	.stimulus-shape {
		width: 150px;
		height: 150px;
		filter: drop-shadow(0 16px 26px rgba(24, 51, 71, 0.18));
	}

	.stimulus-shape.circle {
		border-radius: 999px;
	}

	.stimulus-shape.square {
		border-radius: 18px;
	}

	.stimulus-shape.triangle {
		width: 0;
		height: 0;
		border-left: 85px solid transparent;
		border-right: 85px solid transparent;
		border-bottom: 150px solid #2b9a61;
		background: transparent !important;
	}

	.stimulus-shape.star {
		clip-path: polygon(50% 0%, 61% 35%, 98% 35%, 68% 57%, 79% 92%, 50% 70%, 21% 92%, 32% 57%, 2% 35%, 39% 35%);
	}

	.fixation {
		font-size: 4rem;
		color: #7d93a0;
	}

	.choice-button {
		display: flex;
		align-items: center;
		gap: 0.9rem;
		justify-content: flex-start;
		padding: 1rem;
		border-radius: 18px;
		background: rgba(255,255,255,0.94);
		border: 1px solid rgba(118,145,163,0.18);
	}

	.choice-button.selected {
		background: rgba(15,110,128,0.14);
	}

	.choice-button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.keycap {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 2.25rem;
		height: 2.25rem;
		border-radius: 12px;
		background: #183347;
		color: white;
	}

	.metric {
		display: flex;
		flex-direction: column;
		gap: 0.45rem;
	}

	.metric.primary {
		background: linear-gradient(135deg, #0f6e80, #104a72);
		color: white;
	}

	.metric span {
		font-size: 0.82rem;
		text-transform: uppercase;
		letter-spacing: 0.08em;
	}

	.metric strong {
		font-size: 1.6rem;
	}

	.difficulty {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 1rem;
		margin-top: 1.5rem;
		font-weight: 700;
	}

	.arrow {
		font-size: 1.5rem;
		color: #607786;
	}

	@media (max-width: 780px) {
		.panel {
			padding: 1.25rem;
		}

		.header, .play-header, .layout, .arena {
			flex-direction: column;
			display: flex;
		}

		.arena {
			display: flex;
		}

		.stimulus-stage {
			min-height: 220px;
		}

		.stimulus-shape {
			width: 110px;
			height: 110px;
		}

		.stimulus-shape.triangle {
			border-left-width: 62px;
			border-right-width: 62px;
			border-bottom-width: 110px;
		}
	}
</style>



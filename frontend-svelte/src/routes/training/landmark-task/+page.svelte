<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
	import { locale, localeText } from '$lib/i18n';
	import { buildPracticePayload, getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
	import { onMount } from 'svelte';

	const API_BASE_URL = 'http://127.0.0.1:8000';

	const STATE = {
		LOADING: 'loading',
		INSTRUCTIONS: 'instructions',
		PLAYING: 'playing',
		COMPLETE: 'complete'
	};

	let state = STATE.LOADING;
	let difficulty = 5;
	let sessionData = null;
	let currentTrialIndex = 0;
	let currentTrial = null;
	let trialStartedAt = 0;
	let taskId = null;
	let responses = [];
	let sessionResults = null;
	let newBadges = [];
	let showHelp = false;
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';
	let recordedSessionData = null;

	onMount(async () => {
		taskId = $page.url.searchParams.get('taskId');
		window.addEventListener('keydown', handleKeyDown);
		await loadSession();

		return () => {
			window.removeEventListener('keydown', handleKeyDown);
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
				const planRes = await fetch(`${API_BASE_URL}/api/training/training-plan/${userId}`);
				const plan = await planRes.json();
				if (plan?.current_difficulty) {
					const currentDiff =
						typeof plan.current_difficulty === 'string'
							? JSON.parse(plan.current_difficulty)
							: plan.current_difficulty;
					difficulty = currentDiff.visual_scanning || 5;
				}
			}

			const response = await fetch(`${API_BASE_URL}/api/training/tasks/landmark-task/generate/${userId}?difficulty=${difficulty}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' }
			});

			if (!response.ok) throw new Error('Failed to load Landmark Task');

			const data = await response.json();
			sessionData = structuredClone(data.session_data);
			recordedSessionData = structuredClone(data.session_data);
			currentTrial = sessionData.trials[0];
			state = STATE.INSTRUCTIONS;
		} catch (error) {
			console.error('Error loading Landmark Task:', error);
			alert('Failed to load Landmark Task');
			goto('/dashboard');
		}
	}

	function startTask(nextMode = TASK_PLAY_MODE.RECORDED) {
		playMode = nextMode;
		practiceStatusMessage = '';
		sessionData = nextMode === TASK_PLAY_MODE.PRACTICE
			? buildPracticePayload('landmark-task', recordedSessionData)
			: structuredClone(recordedSessionData);
		responses = [];
		currentTrialIndex = 0;
		currentTrial = sessionData.trials[0];
		trialStartedAt = performance.now();
		state = STATE.PLAYING;
	}

	function handleKeyDown(event) {
		if (state !== STATE.PLAYING) return;
		if (event.key === 'ArrowLeft' || event.key.toLowerCase() === 'a') {
			event.preventDefault();
			submitResponse('left');
		}
		if (event.key === 'ArrowDown' || event.key.toLowerCase() === 's') {
			event.preventDefault();
			submitResponse('equal');
		}
		if (event.key === 'ArrowRight' || event.key.toLowerCase() === 'l') {
			event.preventDefault();
			submitResponse('right');
		}
	}

	function submitResponse(responseValue) {
		if (state !== STATE.PLAYING || !currentTrial) return;

		const reactionTime = Math.round(performance.now() - trialStartedAt);
		responses = [
			...responses,
			{
				trial_index: currentTrial.trial_index,
				response: responseValue,
				reaction_time_ms: reactionTime
			}
		];

		const nextTrialIndex = currentTrialIndex + 1;
		if (nextTrialIndex >= sessionData.trials.length) {
			completeSession();
			return;
		}

		currentTrialIndex = nextTrialIndex;
		currentTrial = sessionData.trials[nextTrialIndex];
		trialStartedAt = performance.now();
	}

	async function completeSession() {
		if (playMode === TASK_PLAY_MODE.PRACTICE) {
			sessionData = structuredClone(recordedSessionData);
			playMode = TASK_PLAY_MODE.RECORDED;
			practiceStatusMessage = getPracticeCopy($locale).complete;
			currentTrialIndex = 0;
			currentTrial = sessionData.trials[0];
			state = STATE.INSTRUCTIONS;
			return;
		}

		state = STATE.LOADING;
		try {
			const userData = JSON.parse(localStorage.getItem('user') || '{}');
			const userId = userData.id;

			const response = await fetch(`${API_BASE_URL}/api/training/tasks/landmark-task/submit/${userId}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					difficulty,
					session_data: sessionData,
					responses,
					task_id: taskId
				})
			});

			if (!response.ok) throw new Error('Failed to submit Landmark Task results');

			sessionResults = await response.json();
			newBadges = sessionResults.new_badges || [];
			state = STATE.COMPLETE;
		} catch (error) {
			console.error('Error submitting Landmark Task:', error);
			alert('Failed to submit results');
			goto('/dashboard');
		}
	}

	function lineMarkup(trial) {
		if (!trial) return '';
		const center = 300;
		const halfLength = trial.line_length / 2;
		const startX = center - halfLength;
		const endX = center + halfLength;
		const markerX = center + trial.offset_px;

		return `
			<svg width="100%" height="160" viewBox="0 0 600 160" preserveAspectRatio="xMidYMid meet">
				<line x1="${startX}" y1="80" x2="${endX}" y2="80" stroke="#24323b" stroke-width="10" stroke-linecap="round" />
				<line x1="${markerX}" y1="52" x2="${markerX}" y2="108" stroke="#cb6f27" stroke-width="8" stroke-linecap="round" />
			</svg>
		`;
	}

	$: progress = sessionData ? (currentTrialIndex / sessionData.total_trials) * 100 : 0;
</script>

<div class="landmark-page">
	{#if state === STATE.LOADING}
		<LoadingSkeleton variant="card" count={3} />
	{:else if state === STATE.INSTRUCTIONS}
		<section class="panel hero">
			<div class="header">
				<div>
					<p class="eyebrow">Visual Scanning</p>
					<h1>Landmark Task</h1>
					<p class="subtitle">
						Judge whether the line is evenly bisected or whether the left or right segment is longer.
						This captures midpoint judgment, spatial bias, and visual-attention balance.
					</p>
				</div>
				<DifficultyBadge {difficulty} domain="Visual Scanning" />
			</div>

			<div class="cards">
				<div class="card accent">
					<h2>What to judge</h2>
					<p>If the marker sits in the true middle, choose <strong>Equal</strong>.</p>
					<p>If the marker is too far right, the <strong>left side is longer</strong>.</p>
					<p>If the marker is too far left, the <strong>right side is longer</strong>.</p>
				</div>
				<div class="card">
					<h2>Response style</h2>
					<ul>
						<li>Left longer: `A` or left arrow</li>
						<li>Equal: `S` or down arrow</li>
						<li>Right longer: `L` or right arrow</li>
					</ul>
					<button class="ghost" on:click={() => (showHelp = !showHelp)}>
						{showHelp ? 'Hide tips' : 'Show tips'}
					</button>
					{#if showHelp}
						<div class="help">
							<p>Judge the two line segments, not the marker itself.</p>
							<p>Keep your eyes centered before each response to avoid carry-over bias.</p>
							<p>Use the same decision rhythm across trials to keep timing stable.</p>
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
				/>
				<button class="secondary" on:click={() => goto('/training')}>Back to Training</button>
			</div>
		</section>
	{:else if state === STATE.PLAYING}
		<section class="panel play">
			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} />
			{/if}
			<div class="play-header">
				<div>
					<p class="eyebrow">Trial {currentTrialIndex + 1} of {sessionData.total_trials}</p>
					<h2>Which side is longer?</h2>
				</div>
				<div class="rule-chip">Midpoint Judgment</div>
			</div>

			<div class="progress-track">
				<div class="progress-fill" style={`width:${progress}%`}></div>
			</div>

			<div class="line-stage">
				<div class="line-card">
					{@html lineMarkup(currentTrial)}
				</div>
			</div>

			<div class="response-grid">
				<button class="response-btn left" on:click={() => submitResponse('left')}>
					Left Longer
					<small>`A` / Left Arrow</small>
				</button>
				<button class="response-btn equal" on:click={() => submitResponse('equal')}>
					Equal
					<small>`S` / Down Arrow</small>
				</button>
				<button class="response-btn right" on:click={() => submitResponse('right')}>
					Right Longer
					<small>`L` / Right Arrow</small>
				</button>
			</div>
		</section>
	{:else if state === STATE.COMPLETE}
		<section class="panel hero">
			<div class="header">
				<div>
					<p class="eyebrow">Session Complete</p>
					<h1>Landmark Results</h1>
					<p class="subtitle">Your spatial-bias and midpoint-judgment metrics are now part of the visual-scanning profile.</p>
				</div>
			</div>

			{#if newBadges.length > 0}
				<BadgeNotification badges={newBadges} />
			{/if}

			<div class="results">
				<div class="metric primary-metric">
					<span>Overall score</span>
					<strong>{sessionResults.metrics.score}</strong>
				</div>
				<div class="metric">
					<span>Accuracy</span>
					<strong>{sessionResults.metrics.accuracy.toFixed(1)}%</strong>
				</div>
				<div class="metric">
					<span>Offset accuracy</span>
					<strong>{sessionResults.metrics.offset_accuracy.toFixed(1)}%</strong>
				</div>
				<div class="metric">
					<span>Centered accuracy</span>
					<strong>{sessionResults.metrics.centered_accuracy.toFixed(1)}%</strong>
				</div>
				<div class="metric">
					<span>Avg RT</span>
					<strong>{sessionResults.metrics.average_reaction_time.toFixed(0)} ms</strong>
				</div>
				<div class="metric">
					<span>Spatial bias index</span>
					<strong>{sessionResults.metrics.spatial_bias_index.toFixed(1)}</strong>
				</div>
				<div class="metric">
					<span>Left-bias errors</span>
					<strong>{sessionResults.metrics.left_bias_errors}</strong>
				</div>
				<div class="metric">
					<span>Right-bias errors</span>
					<strong>{sessionResults.metrics.right_bias_errors}</strong>
				</div>
			</div>

			<div class="difficulty">
				<span>Level {sessionResults.difficulty_before}</span>
				<span class="arrow">-&gt;</span>
				<span>Level {sessionResults.difficulty_after}</span>
			</div>
			<p class="subtitle center">{sessionResults.adaptation_reason}</p>

			<div class="actions">
				<button class="primary" on:click={() => goto('/training')}>Return To Training</button>
				<button class="secondary" on:click={() => goto('/dashboard')}>Back To Dashboard</button>
			</div>
		</section>
	{/if}
</div>

<style>
	:global(body) {
		background:
			radial-gradient(circle at top, rgba(23, 90, 104, 0.14), transparent 34%),
			linear-gradient(180deg, #f5f7f6 0%, #ecefea 100%);
	}

	.landmark-page {
		min-height: 100vh;
		padding: 2rem 1rem 3rem;
		color: #2a3130;
	}

	.panel {
		max-width: 980px;
		margin: 0 auto;
		background: rgba(255, 255, 255, 0.93);
		border: 1px solid rgba(102, 120, 118, 0.18);
		border-radius: 28px;
		padding: 2rem;
		box-shadow: 0 24px 60px rgba(41, 49, 48, 0.08);
	}

	.header, .cards, .actions, .results, .play-header, .response-grid {
		display: flex;
		gap: 1rem;
	}

	.header, .play-header {
		justify-content: space-between;
		align-items: flex-start;
	}

	.cards, .actions, .results, .response-grid {
		flex-wrap: wrap;
	}

	.eyebrow {
		margin: 0 0 0.5rem;
		text-transform: uppercase;
		letter-spacing: 0.16em;
		font-size: 0.78rem;
		font-weight: 700;
		color: #1f6670;
	}

	h1 {
		margin: 0 0 0.75rem;
		font-size: clamp(2rem, 4vw, 3.1rem);
	}

	h2 {
		margin: 0 0 0.75rem;
		font-size: clamp(1.4rem, 3vw, 2rem);
	}

	.subtitle {
		max-width: 54rem;
		line-height: 1.6;
		color: #64706d;
	}

	.subtitle.center {
		text-align: center;
		margin: 1rem auto 0;
	}

	.card, .metric {
		flex: 1 1 260px;
		padding: 1.25rem;
		border-radius: 22px;
		background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(241,245,243,0.96));
		border: 1px solid rgba(102,120,118,0.14);
	}

	.card.accent, .primary-metric {
		background: linear-gradient(135deg, #1f6670, #2f8a96);
		color: white;
	}

	ul {
		margin: 0;
		padding-left: 1.15rem;
		line-height: 1.75;
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
		background: linear-gradient(135deg, #1f6670, #2f8a96);
		color: white;
	}

	.secondary, .ghost {
		background: rgba(83, 96, 94, 0.1);
		color: #404746;
	}

	.help {
		margin-top: 1rem;
		padding: 1rem;
		border-radius: 16px;
		background: rgba(31, 102, 112, 0.08);
	}

	.rule-chip {
		padding: 0.65rem 0.9rem;
		border-radius: 999px;
		background: rgba(31, 102, 112, 0.1);
		font-weight: 700;
		color: #1f6670;
	}

	.progress-track {
		height: 10px;
		background: rgba(102,120,118,0.18);
		border-radius: 999px;
		margin: 1.2rem 0 1.6rem;
		overflow: hidden;
	}

	.progress-fill {
		height: 100%;
		background: linear-gradient(90deg, #1f6670, #63aab4);
	}

	.line-stage {
		margin: 1.5rem 0;
	}

	.line-card {
		padding: 2rem 1rem;
		border-radius: 28px;
		background: linear-gradient(180deg, #f9fbfa, #edf3f1);
		border: 1px solid rgba(102,120,118,0.16);
	}

	.response-grid {
		justify-content: center;
	}

	.response-btn {
		flex: 1 1 220px;
		padding: 1.15rem 1rem;
		border-radius: 20px;
		background: white;
		border: 2px solid rgba(102,120,118,0.16);
		box-shadow: 0 12px 28px rgba(41, 49, 48, 0.06);
		color: #29302f;
		font-size: 1rem;
	}

	.response-btn small {
		display: block;
		margin-top: 0.35rem;
		font-size: 0.8rem;
		color: #697370;
	}

	.response-btn.left {
		border-top: 5px solid #2c7b85;
	}

	.response-btn.equal {
		border-top: 5px solid #cb6f27;
	}

	.response-btn.right {
		border-top: 5px solid #5b8f4c;
	}

	.results {
		margin-top: 1.5rem;
	}

	.metric {
		display: flex;
		flex-direction: column;
		gap: 0.45rem;
	}

	.metric span {
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		opacity: 0.78;
	}

	.metric strong {
		font-size: 1.5rem;
	}

	.difficulty {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		margin-top: 1.5rem;
		font-weight: 700;
	}

	.arrow {
		font-size: 1.2rem;
		color: #798280;
	}

	@media (max-width: 780px) {
		.panel {
			padding: 1.25rem;
		}

		.header, .play-header {
			flex-direction: column;
		}
	}
</style>

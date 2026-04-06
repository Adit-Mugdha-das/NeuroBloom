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
		BLOCK_INTRO: 'block_intro',
		PLAYING: 'playing',
		COMPLETE: 'complete'
	};

	let state = STATE.LOADING;
	let difficulty = 5;
	let sessionData = null;
	let currentTrialIndex = 0;
	let currentTrial = null;
	let currentBlock = null;
	let taskId = null;
	let responses = [];
	let sessionResults = null;
	let newBadges = [];
	let stimulusShownAt = 0;
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
					difficulty = currentDiff.flexibility || 5;
				}
			}

			const response = await fetch(`${API_BASE_URL}/api/training/tasks/rule-shift/generate/${userId}?difficulty=${difficulty}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' }
			});

			if (!response.ok) throw new Error('Failed to load Rule Shift session');

			const data = await response.json();
			sessionData = structuredClone(data.session_data);
			recordedSessionData = structuredClone(data.session_data);
			currentTrial = sessionData.trials[0];
			currentBlock = sessionData.blocks[0];
			state = STATE.INSTRUCTIONS;
		} catch (error) {
			console.error('Error loading Rule Shift session:', error);
			alert('Failed to load Rule Shift');
			goto('/dashboard');
		}
	}

	function startTask(nextMode = TASK_PLAY_MODE.RECORDED) {
		playMode = nextMode;
		practiceStatusMessage = '';
		sessionData = nextMode === TASK_PLAY_MODE.PRACTICE
			? buildPracticePayload('rule-shift', recordedSessionData)
			: structuredClone(recordedSessionData);
		responses = [];
		currentTrialIndex = 0;
		currentTrial = sessionData.trials[0];
		currentBlock = sessionData.blocks[0];
		state = STATE.BLOCK_INTRO;
	}

	function beginBlock() {
		currentTrial = sessionData.trials[currentTrialIndex];
		currentBlock = sessionData.blocks[currentTrial.block_index];
		stimulusShownAt = performance.now();
		state = STATE.PLAYING;
	}

	function handleKeyDown(event) {
		if (state !== STATE.PLAYING) return;
		if (event.key === 'ArrowLeft' || event.key.toLowerCase() === 'a') {
			event.preventDefault();
			submitResponse('left');
		}
		if (event.key === 'ArrowRight' || event.key.toLowerCase() === 'l') {
			event.preventDefault();
			submitResponse('right');
		}
	}

	function submitResponse(selectedSide) {
		if (state !== STATE.PLAYING || !currentTrial) return;

		const reactionTime = Math.round(performance.now() - stimulusShownAt);
		responses = [
			...responses,
			{
				trial_index: currentTrial.trial_index,
				selected_side: selectedSide,
				reaction_time_ms: reactionTime
			}
		];

		const nextTrialIndex = currentTrialIndex + 1;
		if (nextTrialIndex >= sessionData.trials.length) {
			completeSession();
			return;
		}

		const nextTrial = sessionData.trials[nextTrialIndex];
		const blockChanged = nextTrial.block_index !== currentTrial.block_index;

		currentTrialIndex = nextTrialIndex;
		currentTrial = nextTrial;
		currentBlock = sessionData.blocks[nextTrial.block_index];

		if (blockChanged) {
			state = STATE.BLOCK_INTRO;
			return;
		}

		stimulusShownAt = performance.now();
	}

	async function completeSession() {
		if (playMode === TASK_PLAY_MODE.PRACTICE) {
			sessionData = structuredClone(recordedSessionData);
			playMode = TASK_PLAY_MODE.RECORDED;
			practiceStatusMessage = getPracticeCopy($locale).complete;
			currentTrialIndex = 0;
			currentTrial = sessionData.trials[0];
			currentBlock = sessionData.blocks[0];
			state = STATE.INSTRUCTIONS;
			return;
		}

		state = STATE.LOADING;
		try {
			const userData = JSON.parse(localStorage.getItem('user') || '{}');
			const userId = userData.id;

			const response = await fetch(`${API_BASE_URL}/api/training/tasks/rule-shift/submit/${userId}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					difficulty,
					session_data: sessionData,
					responses,
					task_id: taskId
				})
			});

			if (!response.ok) throw new Error('Failed to submit Rule Shift results');

			sessionResults = await response.json();
			newBadges = sessionResults.new_badges || [];
			state = STATE.COMPLETE;
		} catch (error) {
			console.error('Error submitting Rule Shift results:', error);
			alert('Failed to submit results');
			goto('/dashboard');
		}
	}

	function optionMeta(rule, side) {
		return sessionData?.labels?.[rule]?.[side] || '';
	}

	function renderStimulus(trial) {
		if (!trial) return '';
		const color = trial.color === 'teal' ? '#1d7f78' : '#dc7b2c';
		const shapeMarkup =
			trial.shape === 'circle'
				? `<circle cx="60" cy="60" r="28" fill="${color}" />`
				: `<polygon points="60,24 94,96 26,96" fill="${color}" />`;
		const copies = trial.count === 2
			? `<g transform="translate(-18,0)">${shapeMarkup}</g><g transform="translate(18,0)">${shapeMarkup}</g>`
			: shapeMarkup;

		return `<svg width="170" height="150" viewBox="0 0 120 120">${copies}</svg>`;
	}

	$: progress = sessionData ? (currentTrialIndex / sessionData.total_trials) * 100 : 0;
</script>

<div class="rule-shift-page">
	{#if state === STATE.LOADING}
		<LoadingSkeleton variant="card" count={3} />
	{:else if state === STATE.INSTRUCTIONS}
		<section class="panel hero">
			<div class="header">
				<div>
					<p class="eyebrow">Flexibility Training</p>
					<h1>Rule Shift</h1>
					<p class="subtitle">
						Follow the active rule for a short run, then adapt when the rule changes. This targets
						set-shifting, inhibition of the previous rule, and flexible executive control.
					</p>
				</div>
				<DifficultyBadge {difficulty} domain="Flexibility" />
			</div>

			<div class="cards">
				<div class="card accent">
					<h2>Task Structure</h2>
					<p>Each block uses one rule only.</p>
					<p>When the block changes, update your response mapping immediately.</p>
					<p class="helper">The earliest trials after each switch matter most.</p>
				</div>
				<div class="card">
					<h2>Response Rules</h2>
					<ul>
						<li>Use the left button for the left-side category label.</li>
						<li>Use the right button for the right-side category label.</li>
						<li>Respond quickly, but do not carry the old rule into the new block.</li>
					</ul>
					<button class="ghost" on:click={() => (showHelp = !showHelp)}>
						{showHelp ? 'Hide tips' : 'Show tips'}
					</button>
					{#if showHelp}
						<div class="help">
							<p>Name the active rule to yourself before the block starts.</p>
							<p>After every switch, reset your mapping before looking at the next stimulus.</p>
							<p>If you feel the old rule pulling you, slow down slightly for the first two trials.</p>
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
	{:else if state === STATE.BLOCK_INTRO}
		<section class="panel block-intro">
			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} />
			{/if}
			<p class="eyebrow">Block {currentBlock.block_index + 1} of {sessionData.blocks.length}</p>
			<h2>{currentBlock.instruction}</h2>
			<div class="rule-grid">
				<div class="rule-card">
					<span>Left</span>
					<strong>{optionMeta(currentBlock.rule, 'left')}</strong>
				</div>
				<div class="rule-card">
					<span>Right</span>
					<strong>{optionMeta(currentBlock.rule, 'right')}</strong>
				</div>
			</div>
			{#if currentBlock.block_index > 0}
				<p class="subtitle center">The rule has changed. Drop the previous mapping before you continue.</p>
			{/if}
			<div class="actions center">
				<button class="primary" on:click={beginBlock}>Begin Block</button>
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
					<h2>Active Rule: {currentBlock.rule}</h2>
				</div>
				<div class="rule-chip">Block {currentBlock.block_index + 1}</div>
			</div>

			<div class="progress-track">
				<div class="progress-fill" style={`width:${progress}%`}></div>
			</div>

			<div class="mapping-board">
				<div class="mapping left">
					<span>Left</span>
					<strong>{optionMeta(currentBlock.rule, 'left')}</strong>
				</div>
				<div class="mapping right">
					<span>Right</span>
					<strong>{optionMeta(currentBlock.rule, 'right')}</strong>
				</div>
			</div>

			<div class="stimulus-stage">
				<div class="stimulus-card">
					{@html renderStimulus(currentTrial)}
					<div class="stimulus-meta">
						<span>{currentTrial.color}</span>
						<span>{currentTrial.shape}</span>
						<span>{currentTrial.count === 1 ? 'one item' : 'two items'}</span>
					</div>
				</div>
			</div>

			<div class="response-panel">
				<button class="response-btn" on:click={() => submitResponse('left')}>
					Left
					<small>{optionMeta(currentBlock.rule, 'left')}</small>
				</button>
				<button class="response-btn" on:click={() => submitResponse('right')}>
					Right
					<small>{optionMeta(currentBlock.rule, 'right')}</small>
				</button>
			</div>

			<p class="hint">Keyboard: `A` or left arrow for left, `L` or right arrow for right.</p>
		</section>
	{:else if state === STATE.COMPLETE}
		<section class="panel hero">
			<div class="header">
				<div>
					<p class="eyebrow">Session Complete</p>
					<h1>Rule Shift Results</h1>
					<p class="subtitle">Your flexibility metrics are now part of the executive profile.</p>
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
					<span>Switch accuracy</span>
					<strong>{sessionResults.metrics.switch_accuracy.toFixed(1)}%</strong>
				</div>
				<div class="metric">
					<span>Stay accuracy</span>
					<strong>{sessionResults.metrics.stay_accuracy.toFixed(1)}%</strong>
				</div>
				<div class="metric">
					<span>Avg RT</span>
					<strong>{sessionResults.metrics.average_reaction_time.toFixed(0)} ms</strong>
				</div>
				<div class="metric">
					<span>Shift cost</span>
					<strong>{sessionResults.metrics.shift_cost_ms.toFixed(0)} ms</strong>
				</div>
				<div class="metric">
					<span>Perseverative errors</span>
					<strong>{sessionResults.metrics.perseverative_errors}</strong>
				</div>
				<div class="metric">
					<span>Flexibility index</span>
					<strong>{sessionResults.metrics.flexibility_index.toFixed(1)}</strong>
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
			radial-gradient(circle at top, rgba(194, 104, 45, 0.14), transparent 34%),
			linear-gradient(180deg, #f7f3ee 0%, #efebe4 100%);
	}

	.rule-shift-page {
		min-height: 100vh;
		padding: 2rem 1rem 3rem;
		color: #2e302d;
	}

	.panel {
		max-width: 980px;
		margin: 0 auto;
		background: rgba(255, 255, 255, 0.92);
		border: 1px solid rgba(122, 114, 103, 0.18);
		border-radius: 28px;
		padding: 2rem;
		box-shadow: 0 24px 60px rgba(44, 42, 38, 0.08);
	}

	.header, .cards, .actions, .results, .play-header, .mapping-board, .response-panel, .rule-grid {
		display: flex;
		gap: 1rem;
	}

	.header, .play-header {
		justify-content: space-between;
		align-items: flex-start;
	}

	.cards, .actions, .results, .rule-grid {
		flex-wrap: wrap;
	}

	.actions.center {
		justify-content: center;
	}

	.eyebrow {
		margin: 0 0 0.5rem;
		text-transform: uppercase;
		letter-spacing: 0.16em;
		font-size: 0.78rem;
		font-weight: 700;
		color: #a05f24;
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
		max-width: 52rem;
		line-height: 1.6;
		color: #656960;
	}

	.subtitle.center {
		text-align: center;
		margin: 1rem auto 0;
	}

	.card, .metric, .rule-card, .mapping {
		flex: 1 1 260px;
		padding: 1.25rem;
		border-radius: 22px;
		background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(246,242,235,0.96));
		border: 1px solid rgba(122,114,103,0.14);
	}

	.card.accent, .primary-metric {
		background: linear-gradient(135deg, #9c5c23, #c67a2d);
		color: white;
	}

	.helper {
		color: rgba(255,255,255,0.88);
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
		background: linear-gradient(135deg, #9c5c23, #c67a2d);
		color: white;
	}

	.secondary, .ghost {
		background: rgba(84, 87, 81, 0.1);
		color: #40433f;
	}

	.help {
		margin-top: 1rem;
		padding: 1rem;
		border-radius: 16px;
		background: rgba(156, 92, 35, 0.08);
	}

	.rule-chip {
		padding: 0.65rem 0.9rem;
		border-radius: 999px;
		background: rgba(156, 92, 35, 0.1);
		font-weight: 700;
		color: #9c5c23;
	}

	.progress-track {
		height: 10px;
		background: rgba(122,114,103,0.18);
		border-radius: 999px;
		margin: 1.2rem 0 1.6rem;
		overflow: hidden;
	}

	.progress-fill {
		height: 100%;
		background: linear-gradient(90deg, #9c5c23, #d49a54);
	}

	.block-intro {
		text-align: center;
	}

	.rule-card span, .mapping span, .metric span {
		display: block;
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: inherit;
		opacity: 0.75;
	}

	.rule-card strong, .mapping strong, .metric strong {
		font-size: 1.45rem;
	}

	.mapping-board {
		margin-bottom: 1.5rem;
	}

	.mapping.left {
		border-left: 5px solid #1d7f78;
	}

	.mapping.right {
		border-left: 5px solid #dc7b2c;
	}

	.stimulus-stage {
		display: flex;
		justify-content: center;
		margin: 1.4rem 0 1.2rem;
	}

	.stimulus-card {
		min-width: 280px;
		padding: 1.5rem;
		border-radius: 28px;
		background: linear-gradient(180deg, #faf7f2, #efe9de);
		border: 1px solid rgba(122,114,103,0.16);
		text-align: center;
	}

	.stimulus-meta {
		display: flex;
		justify-content: center;
		gap: 0.75rem;
		flex-wrap: wrap;
		color: #666a61;
		font-size: 0.92rem;
	}

	.response-panel {
		justify-content: center;
		flex-wrap: wrap;
	}

	.response-btn {
		min-width: 240px;
		padding: 1.15rem 1.25rem;
		border-radius: 20px;
		background: white;
		border: 2px solid rgba(122,114,103,0.16);
		box-shadow: 0 12px 28px rgba(44, 42, 38, 0.06);
		color: #303330;
		font-size: 1.05rem;
	}

	.response-btn small {
		display: block;
		margin-top: 0.35rem;
		font-size: 0.82rem;
		color: #6a6e66;
	}

	.hint {
		margin-top: 1rem;
		text-align: center;
		color: #6a6e66;
	}

	.results {
		margin-top: 1.5rem;
	}

	.metric {
		display: flex;
		flex-direction: column;
		gap: 0.45rem;
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
		color: #777a73;
	}

	@media (max-width: 780px) {
		.panel {
			padding: 1.25rem;
		}

		.header, .play-header, .mapping-board, .response-panel {
			flex-direction: column;
		}

		.stimulus-card {
			min-width: 0;
			width: 100%;
		}

		.response-btn {
			min-width: 0;
			width: 100%;
		}
	}
</style>

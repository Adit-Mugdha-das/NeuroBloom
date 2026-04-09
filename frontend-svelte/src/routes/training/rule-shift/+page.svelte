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
	/** @type {"practice" | "recorded"} */
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';
	let recordedSessionData = null;

	onMount(() => {
		taskId = $page.url.searchParams.get('taskId');
		window.addEventListener('keydown', handleKeyDown);
		loadSession();

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

	/** @param {"practice" | "recorded"} nextMode */
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
		<div class="page-content">
			<div class="task-header">
				<button class="back-btn" on:click={() => goto('/training')}>← Back to Training</button>
				<div class="header-center">
					<h1 class="task-title">Rule Shift Task</h1>
					<DifficultyBadge {difficulty} domain="Flexibility" />
				</div>
			</div>

			{#if practiceStatusMessage}
				<div class="practice-note">{practiceStatusMessage}</div>
			{/if}

			<div class="concept-card">
				<span class="concept-badge">Cognitive Flexibility · Set-Shifting</span>
				<h2>The Core Mechanism</h2>
				<p>
					Each block uses a single classification rule applied to geometric shapes. When the block
					ends, the rule changes — you must drop the previous mapping and immediately apply the new
					one. The earliest trials after each switch reveal your true set-shifting speed.
				</p>
			</div>

			<div class="rules-card">
				<h3>How to Respond</h3>
				<ol class="rules-list">
					<li>A shape (circle or triangle) appears on screen, coloured teal or orange, in a count of one or two.</li>
					<li>Read the <strong>Active Rule</strong> displayed above the stimulus to know which attribute to classify.</li>
					<li>Press <strong>Left</strong> for the left-side category label, <strong>Right</strong> for the right-side label.</li>
					<li>When the block changes, update your response mapping <em>before</em> the first stimulus of the new block.</li>
				</ol>
				<p class="rules-note">
					Accuracy on switch trials is the primary measure. Perseverative errors — applying the old rule after a switch — count against your flexibility index.
				</p>
			</div>

			<div class="info-grid">
				<div class="info-card">
					<div class="info-label">Block Length</div>
					<div class="info-val">4–8</div>
					<p>Trials per rule block</p>
				</div>
				<div class="info-card">
					<div class="info-label">Total Trials</div>
					<div class="info-val">{sessionData?.total_trials ?? '—'}</div>
					<p>Across all rule blocks</p>
				</div>
				<div class="info-card">
					<div class="info-label">Rules Active</div>
					<div class="info-val">3</div>
					<p>Color · Shape · Count</p>
				</div>
				<div class="info-card">
					<div class="info-label">Response</div>
					<div class="info-val">L / R</div>
					<p>Button click or arrow key</p>
				</div>
			</div>

			<div class="tip-card">
				<div class="tip-row">
					<div>
						<p class="tip-title">Performance Tips</p>
						<ul>
							<li><strong>Name the new rule</strong> silently before the first trial of each block.</li>
							<li><strong>Slow down slightly</strong> on the first two trials after a switch — accuracy matters more than speed here.</li>
							<li><strong>Do not rely on momentum</strong> — the same stimulus can require a different response next block.</li>
						</ul>
					</div>
					<button class="show-more-btn" on:click={() => (showHelp = !showHelp)}>
						{showHelp ? 'Less' : 'More tips'}
					</button>
				</div>
				{#if showHelp}
					<ul style="margin-top: 0.75rem;">
						<li>After an error on a switch trial, pause and re-read the rule label before the next response.</li>
						<li>The mappings change every block — commit to re-reading the block intro screen each time.</li>
					</ul>
				{/if}
			</div>

			<div class="clinical-card">
				<h3>Clinical Significance</h3>
				<p>
					Set-shifting deficits are a sensitive marker of executive dysfunction in multiple sclerosis.
					The Rule Shift Task isolates perseverative responding — using a previously correct rule after it
					has changed — and the switch cost (slowing on first post-switch trial). Both metrics are used
					in cognitive rehabilitation research to track frontal lobe integrity over time
					(Chiaravalloti &amp; DeLuca, 2008).
				</p>
			</div>

			<TaskPracticeActions
				locale={$locale}
				startLabel={localeText({ en: 'Start Rule Shift', bn: 'নিয়ম শিফট শুরু করুন' }, $locale)}
				statusMessage={practiceStatusMessage}
				on:start={() => startTask(TASK_PLAY_MODE.RECORDED)}
				on:practice={() => startTask(TASK_PLAY_MODE.PRACTICE)}
			/>
		</div>
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
	/* ── Container ─────────────────────────────────────────── */
	.rule-shift-page {
		min-height: 100vh;
		background: #C8DEFA;
		padding: 2rem 1rem 3rem;
		color: #2e302d;
	}

	/* ── Page content (instruction view) ──────────────────── */
	.page-content {
		max-width: 1100px;
		margin: 0 auto;
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	.task-header {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.back-btn {
		background: white;
		color: #9c5c23;
		border: 2px solid #9c5c23;
		padding: 0.6rem 1.25rem;
		border-radius: 8px;
		cursor: pointer;
		font-size: 0.9rem;
		font-weight: 600;
		white-space: nowrap;
		transition: background 0.2s, color 0.2s;
	}
	.back-btn:hover { background: #9c5c23; color: white; }

	.header-center {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		flex-wrap: wrap;
	}

	.task-title {
		font-size: 1.75rem;
		font-weight: 700;
		color: #7c2d12;
		margin: 0;
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

	.concept-card {
		background: white;
		border-radius: 16px;
		padding: 2rem;
		box-shadow: 0 4px 6px rgba(0,0,0,0.07);
	}

	.concept-badge {
		display: inline-block;
		background: #fff7ed;
		color: #9c5c23;
		font-size: 0.8rem;
		font-weight: 700;
		letter-spacing: 0.5px;
		text-transform: uppercase;
		padding: 0.3rem 0.9rem;
		border-radius: 20px;
		margin-bottom: 0.75rem;
	}

	.concept-card h2 {
		font-size: 1.5rem;
		font-weight: 700;
		color: #7c2d12;
		margin: 0 0 0.75rem;
	}
	.concept-card p { color: #374151; line-height: 1.65; margin: 0; }

	.rules-card {
		background: white;
		border-radius: 16px;
		padding: 2rem;
		box-shadow: 0 4px 6px rgba(0,0,0,0.07);
	}
	.rules-card h3 { font-size: 1.1rem; font-weight: 700; color: #7c2d12; margin: 0 0 1rem; }

	.rules-list {
		margin: 0 0 1rem;
		padding-left: 1.5rem;
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}
	.rules-list li { color: #374151; line-height: 1.55; }
	.rules-list li strong { color: #9c5c23; }

	.rules-note {
		margin: 0;
		background: #fff7ed;
		color: #9c5c23;
		border-radius: 8px;
		padding: 0.75rem 1rem;
		font-size: 0.9rem;
		line-height: 1.5;
	}

	.info-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		gap: 1rem;
	}

	.info-card {
		background: white;
		border-radius: 16px;
		padding: 1.5rem;
		box-shadow: 0 4px 6px rgba(0,0,0,0.07);
	}

	.info-label {
		font-size: 0.75rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.5px;
		color: #9c5c23;
		margin-bottom: 0.25rem;
	}

	.info-val {
		font-size: 1.5rem;
		font-weight: 800;
		color: #7c2d12;
		margin-bottom: 0.5rem;
	}
	.info-card p { font-size: 0.875rem; color: #6b7280; line-height: 1.5; margin: 0; }

	.tip-card {
		background: #fffbeb;
		border: 1px solid #fde68a;
		border-radius: 16px;
		padding: 1.5rem 2rem;
	}
	.tip-card ul {
		margin: 0.75rem 0 0;
		padding-left: 1.5rem;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	.tip-card li { color: #374151; font-size: 0.9rem; line-height: 1.55; }
	.tip-card li strong { color: #9c5c23; }

	.tip-title {
		font-size: 0.8rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.5px;
		color: #9c5c23;
		margin-bottom: 0.5rem;
	}

	.tip-row { display: flex; align-items: center; justify-content: space-between; gap: 1.5rem; }

	.show-more-btn {
		background: white;
		border: 1.5px solid #9c5c23;
		color: #9c5c23;
		padding: 0.5rem 1.1rem;
		border-radius: 8px;
		cursor: pointer;
		font-size: 0.875rem;
		font-weight: 600;
		white-space: nowrap;
		flex-shrink: 0;
		transition: all 0.2s;
	}
	.show-more-btn:hover { background: #9c5c23; color: white; }

	.clinical-card {
		background: #f0fdf4;
		border: 1px solid #bbf7d0;
		border-radius: 16px;
		padding: 1.5rem 2rem;
	}
	.clinical-card h3 { font-size: 1rem; font-weight: 700; color: #14532d; margin: 0 0 0.75rem; }
	.clinical-card p { color: #166534; font-size: 0.95rem; line-height: 1.65; margin: 0; }

	/* ── Shared panel (gameplay + results) ────────────────── */
	.panel {
		max-width: 980px;
		margin: 0 auto;
		background: rgba(255,255,255,0.92);
		border: 1px solid rgba(122,114,103,0.18);
		border-radius: 28px;
		padding: 2rem;
		box-shadow: 0 24px 60px rgba(44,42,38,0.08);
	}

	.header, .actions, .results, .play-header, .mapping-board, .response-panel, .rule-grid {
		display: flex;
		gap: 1rem;
	}

	.header, .play-header {
		justify-content: space-between;
		align-items: flex-start;
	}

	.actions, .results, .rule-grid {
		flex-wrap: wrap;
	}

	.actions.center { justify-content: center; }

	.eyebrow {
		margin: 0 0 0.5rem;
		text-transform: uppercase;
		letter-spacing: 0.16em;
		font-size: 0.78rem;
		font-weight: 700;
		color: #a05f24;
	}

	h1 { margin: 0 0 0.75rem; font-size: clamp(2rem, 4vw, 3.1rem); }
	h2 { margin: 0 0 0.75rem; font-size: clamp(1.4rem, 3vw, 2rem); }

	.subtitle { max-width: 52rem; line-height: 1.6; color: #656960; }
	.subtitle.center { text-align: center; margin: 1rem auto 0; }

	.metric {
		flex: 1 1 240px;
		padding: 1.25rem;
		border-radius: 22px;
		background: white;
		border: 1px solid rgba(122,114,103,0.14);
		display: flex;
		flex-direction: column;
		gap: 0.45rem;
	}

	.metric.primary-metric {
		background: #9c5c23;
		color: white;
	}

	.metric span {
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		opacity: 0.75;
	}

	.metric strong { font-size: 1.45rem; }

	.rule-card, .mapping {
		flex: 1 1 220px;
		padding: 1.25rem;
		border-radius: 22px;
		background: white;
		border: 1px solid rgba(122,114,103,0.14);
	}

	.rule-card span, .mapping span {
		display: block;
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		opacity: 0.65;
	}

	.rule-card strong, .mapping strong { font-size: 1.45rem; }

	button { border: none; cursor: pointer; font-weight: 700; }

	.primary, .secondary {
		padding: 0.95rem 1.35rem;
		border-radius: 16px;
	}

	.primary { background: #9c5c23; color: white; }
	.secondary { background: rgba(84,87,81,0.1); color: #40433f; }

	.rule-chip {
		padding: 0.65rem 0.9rem;
		border-radius: 999px;
		background: #fff7ed;
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
		background: linear-gradient(90deg, #d49a54 0%, #9c5c23 100%);
	}

	.block-intro { text-align: center; }

	.mapping-board { margin-bottom: 1.5rem; }
	.mapping.left { border-left: 5px solid #1d7f78; }
	.mapping.right { border-left: 5px solid #dc7b2c; }

	.stimulus-stage {
		display: flex;
		justify-content: center;
		margin: 1.4rem 0 1.2rem;
	}

	.stimulus-card {
		min-width: 280px;
		padding: 1.5rem;
		border-radius: 28px;
		background: #fffbeb;
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

	.response-panel { justify-content: center; flex-wrap: wrap; }

	.response-btn {
		min-width: 240px;
		padding: 1.15rem 1.25rem;
		border-radius: 20px;
		background: white;
		border: 2px solid rgba(122,114,103,0.16);
		box-shadow: 0 12px 28px rgba(44,42,38,0.06);
		color: #303330;
		font-size: 1.05rem;
	}

	.response-btn small {
		display: block;
		margin-top: 0.35rem;
		font-size: 0.82rem;
		color: #6a6e66;
	}

	.hint { margin-top: 1rem; text-align: center; color: #6a6e66; }

	.results { margin-top: 1.5rem; display: flex; gap: 1rem; flex-wrap: wrap; }

	.difficulty {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		margin-top: 1.5rem;
		font-weight: 700;
	}

	.arrow { font-size: 1.2rem; color: #777a73; }

	@media (max-width: 780px) {
		.panel { padding: 1.25rem; }
		.header, .play-header, .mapping-board, .response-panel { flex-direction: column; }
		.stimulus-card { min-width: 0; width: 100%; }
		.response-btn { min-width: 0; width: 100%; }
	}
</style>

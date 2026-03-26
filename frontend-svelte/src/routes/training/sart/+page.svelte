<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import { onMount } from 'svelte';

	const API_BASE_URL = 'http://127.0.0.1:8000';

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
	let taskId = null;
	let showDigit = false;
	let currentDigit = null;
	let waitingForResponse = false;
	let stimulusShownAt = 0;
	let timerHandle = null;
	let isiHandle = null;
	let responses = [];
	let sessionResults = null;
	let newBadges = [];
	let countdown = 3;
	let showHelp = false;

	onMount(async () => {
		taskId = $page.url.searchParams.get('taskId');
		window.addEventListener('keydown', handleKeyDown);
		await loadSession();

		return () => {
			window.removeEventListener('keydown', handleKeyDown);
			if (timerHandle) clearTimeout(timerHandle);
			if (isiHandle) clearTimeout(isiHandle);
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
					difficulty = currentDiff.attention || 5;
				}
			}

			const response = await fetch(`${API_BASE_URL}/api/training/tasks/sart/generate/${userId}?difficulty=${difficulty}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' }
			});

			if (!response.ok) throw new Error('Failed to load SART session');

			const data = await response.json();
			sessionData = data.session_data;
			state = STATE.INSTRUCTIONS;
		} catch (error) {
			console.error('Error loading SART session:', error);
			alert('Failed to load SART');
			goto('/dashboard');
		}
	}

	function startTask() {
		state = STATE.READY;
		countdown = 3;
		const countdownInterval = setInterval(() => {
			countdown -= 1;
			if (countdown <= 0) {
				clearInterval(countdownInterval);
				beginTrial();
			}
		}, 1000);
	}

	function beginTrial() {
		if (currentTrialIndex >= sessionData.trials.length) {
			completeSession();
			return;
		}

		currentTrial = sessionData.trials[currentTrialIndex];
		currentDigit = currentTrial.digit;
		showDigit = true;
		waitingForResponse = true;
		stimulusShownAt = performance.now();
		state = STATE.PLAYING;

		if (timerHandle) clearTimeout(timerHandle);
		timerHandle = setTimeout(() => {
			finishTrial(false);
		}, sessionData.stimulus_ms);
	}

	function handleKeyDown(event) {
		if (state !== STATE.PLAYING || !waitingForResponse) return;
		if (event.code !== 'Space' && event.key !== ' ') return;
		event.preventDefault();
		finishTrial(true);
	}

	function finishTrial(responded) {
		if (!waitingForResponse || !currentTrial) return;

		waitingForResponse = false;
		if (timerHandle) clearTimeout(timerHandle);

		const reactionTime = responded ? Math.round(performance.now() - stimulusShownAt) : 0;
		responses = [
			...responses,
			{
				trial_index: currentTrial.trial_index,
				responded,
				reaction_time_ms: reactionTime
			}
		];

		showDigit = false;
		currentDigit = null;
		currentTrialIndex += 1;

		isiHandle = setTimeout(() => {
			beginTrial();
		}, sessionData.inter_stimulus_interval_ms);
	}

	async function completeSession() {
		state = STATE.LOADING;
		try {
			const userData = JSON.parse(localStorage.getItem('user') || '{}');
			const userId = userData.id;

			const response = await fetch(`${API_BASE_URL}/api/training/tasks/sart/submit/${userId}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					difficulty,
					session_data: sessionData,
					responses,
					task_id: taskId
				})
			});

			if (!response.ok) throw new Error('Failed to submit SART results');

			sessionResults = await response.json();
			newBadges = sessionResults.new_badges || [];
			state = STATE.COMPLETE;
		} catch (error) {
			console.error('Error submitting SART results:', error);
			alert('Failed to submit results');
			goto('/dashboard');
		}
	}

	$: progress = sessionData ? (currentTrialIndex / sessionData.total_trials) * 100 : 0;
</script>

<div class="sart-page">
	{#if state === STATE.LOADING}
		<LoadingSkeleton variant="card" count={3} />
	{:else if state === STATE.INSTRUCTIONS}
		<section class="panel hero">
			<div class="header">
				<div>
					<p class="eyebrow">Attention Training</p>
					<h1>Sustained Attention To Response Task</h1>
					<p class="subtitle">
						Press <strong>SPACE</strong> for every digit except the rare target digit. This captures vigilance,
						fatigue-sensitive lapses, and inhibitory control under repetitive pressure.
					</p>
				</div>
				<DifficultyBadge {difficulty} domain="Attention" />
			</div>

			<div class="cards">
				<div class="card target">
					<h2>Target Rule</h2>
					<p>Press for every number <strong>except {sessionData.target_digit}</strong>.</p>
					<div class="target-digit">{sessionData.target_digit}</div>
					<p class="helper">When this target appears, keep your hands still.</p>
				</div>

				<div class="card">
					<h2>Why this matters</h2>
					<ul>
						<li>Frequent responding builds a habit that makes lapses measurable.</li>
						<li>Rare no-go targets expose vigilance drift and impulsive responses.</li>
						<li>Fast repetitive pacing makes it sensitive to fatigue-related breakdowns.</li>
					</ul>
					<button class="ghost" on:click={() => (showHelp = !showHelp)}>
						{showHelp ? 'Hide tips' : 'Show tips'}
					</button>
					{#if showHelp}
						<div class="help">
							<p>Keep a steady rhythm instead of reacting emotionally to each digit.</p>
							<p>Reset attention after every target so your next response does not get delayed.</p>
							<p>If you start making impulsive presses, slow your internal pace rather than rushing.</p>
						</div>
					{/if}
				</div>
			</div>

			<div class="actions">
				<button class="primary" on:click={startTask}>Start SART</button>
				<button class="secondary" on:click={() => goto('/training')}>Back to Training</button>
			</div>
		</section>
	{:else if state === STATE.READY}
		<section class="panel ready">
			<p class="eyebrow">Get Ready</p>
			<h2>{countdown}</h2>
			<p>Remember: press for every digit except {sessionData.target_digit}.</p>
		</section>
	{:else if state === STATE.PLAYING}
		<section class="panel play">
			<div class="play-header">
				<div>
					<p class="eyebrow">Trial {currentTrialIndex + 1} of {sessionData.total_trials}</p>
					<h2>Stay steady</h2>
				</div>
				<div class="rule-chip">No press on {sessionData.target_digit}</div>
			</div>

			<div class="progress-track">
				<div class="progress-fill" style={`width:${progress}%`}></div>
			</div>

			<div class="digit-stage">
				{#if showDigit}
					<div class={`digit ${currentTrial?.digit === sessionData.target_digit ? 'target' : 'go'}`}>{currentDigit}</div>
				{:else}
					<div class="fixation">+</div>
				{/if}
			</div>

			<div class="response-panel">
				<button class="primary large" on:click={() => finishTrial(true)} disabled={!waitingForResponse}>
					Press Space
				</button>
				<p class="hint">Ignore only the rare target digit.</p>
			</div>
		</section>
	{:else if state === STATE.COMPLETE}
		<section class="panel hero">
			<div class="header">
				<div>
					<p class="eyebrow">Session Complete</p>
					<h1>SART Results</h1>
					<p class="subtitle">Your vigilance and inhibition scores are now part of the attention profile.</p>
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
					<span>Go accuracy</span>
					<strong>{sessionResults.metrics.go_accuracy.toFixed(1)}%</strong>
				</div>
				<div class="metric">
					<span>No-go accuracy</span>
					<strong>{sessionResults.metrics.nogo_accuracy.toFixed(1)}%</strong>
				</div>
				<div class="metric">
					<span>Avg RT</span>
					<strong>{sessionResults.metrics.average_reaction_time.toFixed(0)} ms</strong>
				</div>
				<div class="metric">
					<span>Commission errors</span>
					<strong>{sessionResults.metrics.commission_errors}</strong>
				</div>
				<div class="metric">
					<span>Omission errors</span>
					<strong>{sessionResults.metrics.omission_errors}</strong>
				</div>
				<div class="metric">
					<span>Vigilance index</span>
					<strong>{sessionResults.metrics.vigilance_index.toFixed(1)}</strong>
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
			radial-gradient(circle at top, rgba(190, 110, 27, 0.12), transparent 32%),
			linear-gradient(180deg, #fbfaf7 0%, #f2f0ea 100%);
	}

	.sart-page {
		min-height: 100vh;
		padding: 2rem 1rem 3rem;
		color: #2e312f;
	}

	.panel {
		max-width: 960px;
		margin: 0 auto;
		background: rgba(255,255,255,0.9);
		border: 1px solid rgba(133, 129, 118, 0.18);
		border-radius: 26px;
		padding: 2rem;
		box-shadow: 0 24px 60px rgba(44, 46, 45, 0.08);
	}

	.header, .cards, .actions, .results, .play-header {
		display: flex;
		gap: 1rem;
	}

	.header, .play-header {
		justify-content: space-between;
		align-items: flex-start;
	}

	.cards, .results, .actions {
		flex-wrap: wrap;
	}

	.eyebrow {
		margin: 0 0 0.5rem;
		text-transform: uppercase;
		letter-spacing: 0.16em;
		font-size: 0.78rem;
		font-weight: 700;
		color: #9a5a16;
	}

	h1 {
		font-size: clamp(2rem, 4vw, 3.1rem);
		margin: 0 0 0.75rem;
	}

	.subtitle {
		max-width: 50rem;
		line-height: 1.6;
		color: #626761;
	}

	.subtitle.center {
		text-align: center;
		margin: 1rem auto 0;
	}

	.card, .metric {
		flex: 1 1 280px;
		padding: 1.25rem;
		border-radius: 22px;
		background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(247,244,238,0.94));
		border: 1px solid rgba(133,129,118,0.14);
	}

	.card.target {
		background: linear-gradient(135deg, #9a5a16, #b8701f);
		color: white;
	}

	.target-digit {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 5rem;
		height: 5rem;
		font-size: 2.4rem;
		font-weight: 800;
		border-radius: 22px;
		background: rgba(255,255,255,0.16);
		margin: 0.5rem 0 0.75rem;
	}

	.helper {
		color: rgba(255,255,255,0.9);
	}

	ul {
		margin: 0;
		padding-left: 1.2rem;
		line-height: 1.7;
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
		background: linear-gradient(135deg, #9a5a16, #b8701f);
		color: white;
	}

	.primary.large {
		padding: 1.1rem 1.8rem;
		font-size: 1rem;
	}

	.secondary, .ghost {
		background: rgba(98,103,97,0.1);
		color: #40443f;
	}

	.help {
		margin-top: 1rem;
		padding: 1rem;
		border-radius: 16px;
		background: rgba(154,90,22,0.08);
	}

	.ready {
		text-align: center;
	}

	.ready h2 {
		font-size: 5rem;
		margin: 0.5rem 0 1rem;
	}

	.rule-chip {
		padding: 0.65rem 0.9rem;
		border-radius: 999px;
		background: rgba(154,90,22,0.1);
		font-weight: 700;
		color: #9a5a16;
	}

	.progress-track {
		height: 10px;
		background: rgba(133,129,118,0.2);
		border-radius: 999px;
		margin: 1.2rem 0 1.6rem;
		overflow: hidden;
	}

	.progress-fill {
		height: 100%;
		background: linear-gradient(90deg, #9a5a16, #d4943f);
	}

	.digit-stage {
		min-height: 280px;
		border-radius: 28px;
		background: linear-gradient(180deg, #faf7f0, #efe9dc);
		display: flex;
		align-items: center;
		justify-content: center;
		border: 1px solid rgba(133,129,118,0.16);
	}

	.digit {
		font-size: clamp(5rem, 14vw, 9rem);
		font-weight: 800;
		line-height: 1;
	}

	.digit.go {
		color: #31483b;
	}

	.digit.target {
		color: #b03b1f;
	}

	.fixation {
		font-size: 4rem;
		color: #94988f;
	}

	.response-panel {
		margin-top: 1.5rem;
		text-align: center;
	}

	.hint {
		margin-top: 0.85rem;
		color: #686e67;
	}

	.results {
		margin-top: 1.5rem;
	}

	.metric {
		display: flex;
		flex-direction: column;
		gap: 0.45rem;
	}

	.metric.primary {
		background: linear-gradient(135deg, #9a5a16, #b8701f);
		color: white;
	}

	.metric span {
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 0.08em;
	}

	.metric strong {
		font-size: 1.55rem;
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
		font-size: 1.5rem;
		color: #767b74;
	}

	@media (max-width: 780px) {
		.panel {
			padding: 1.25rem;
		}

		.header, .play-header, .cards {
			flex-direction: column;
		}

		.digit-stage {
			min-height: 220px;
		}
	}
</style>

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
			sessionData = structuredClone(data.session_data);
			recordedSessionData = structuredClone(data.session_data);
			state = STATE.INSTRUCTIONS;
		} catch (error) {
			console.error('Error loading SART session:', error);
			alert('Failed to load SART');
			goto('/dashboard');
		}
	}

	/** @param {"practice" | "recorded"} nextMode */
	function startTask(nextMode = TASK_PLAY_MODE.RECORDED) {
		playMode = nextMode;
		practiceStatusMessage = '';
		sessionData = nextMode === TASK_PLAY_MODE.PRACTICE
			? buildPracticePayload('sart', recordedSessionData)
			: structuredClone(recordedSessionData);
		currentTrialIndex = 0;
		responses = [];
		currentTrial = null;
		currentDigit = null;
		showDigit = false;
		waitingForResponse = false;
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
		if (playMode === TASK_PLAY_MODE.PRACTICE) {
			sessionData = structuredClone(recordedSessionData);
			playMode = TASK_PLAY_MODE.RECORDED;
			practiceStatusMessage = getPracticeCopy($locale).complete;
			state = STATE.INSTRUCTIONS;
			return;
		}

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
		<div class="page-content">

			<!-- Header -->
			<div class="task-header">
				<button class="back-btn" on:click={() => goto('/training')}>Back to Training</button>
				<div class="header-center">
					<h1 class="task-title">SART</h1>
					<DifficultyBadge {difficulty} domain="Attention" />
				</div>
			</div>

			<div class="concept-card">
				<div class="concept-badge">Attention · Vigilance Training</div>
				<h2>What Is SART?</h2>
				<p>Press <strong>SPACE</strong> for every digit except the rare target digit. This captures vigilance, fatigue-sensitive lapses, and inhibitory control under repetitive pressure.</p>
			</div>

			<div class="rules-card">
				<h3>How to Respond</h3>
				<ol class="rules-list">
					<li>A stream of digits appears rapidly, one at a time.</li>
					<li>Press <strong>SPACE</strong> (or the on-screen button) for every digit you see.</li>
					<li>When you see the target digit <strong>{sessionData.target_digit}</strong>, do <strong>NOT</strong> press — keep your hands still.</li>
					<li>Try to maintain a steady rhythm — speed and accuracy both matter.</li>
				</ol>
				<p class="rules-note">The target digit <strong>{sessionData.target_digit}</strong> appears rarely (~12–16% of trials). Stay alert throughout.</p>
			</div>

			<div class="info-grid">
				<div class="info-card">
					<div class="info-label">Trials</div>
					<div class="info-val">{sessionData.total_trials}</div>
					<p>Total digit stimuli presented in this session.</p>
				</div>
				<div class="info-card">
					<div class="info-label">Target Digit</div>
					<div class="info-val">{sessionData.target_digit}</div>
					<p>The only digit you must withhold your response to.</p>
				</div>
				<div class="info-card">
					<div class="info-label">Scoring</div>
					<div class="info-val">Dual</div>
					<p>Commission errors (pressing on target) and omission errors (missing non-targets) both reduce your score.</p>
				</div>
			</div>

			{#if showHelp}
				<div class="tip-card">
					<div class="tip-title">Advanced Tips</div>
					<ul>
						<li><strong>Steady rhythm:</strong> respond to each digit at the same pace instead of reacting emotionally.</li>
						<li><strong>Reset after targets:</strong> after correctly withholding, fully re-engage for the next digit so you don't miss an immediate non-target.</li>
						<li><strong>Don't rush:</strong> if you start pressing impulsively, slow your internal pace rather than trying to go faster.</li>
						<li><strong>Both errors count:</strong> pressing on the target and missing a non-target both lower your vigilance score equally.</li>
					</ul>
				</div>
			{:else}
				<div class="tip-card minimal">
					<div class="tip-row">
						<div>
							<div class="tip-title">Strategy</div>
							<p>Keep a steady mental rhythm rather than reacting to each digit. Only withhold when you see {sessionData.target_digit} — stay consistent throughout.</p>
						</div>
						<button class="show-more-btn" on:click={() => (showHelp = true)}>More tips</button>
					</div>
				</div>
			{/if}

			<div class="clinical-card">
				<h3>Clinical Basis</h3>
				<p>SART is a widely used sustained-attention paradigm that captures vigilance decrements characteristic of MS-related fatigue. Unlike typical Go/No-Go tasks, SART builds a strong prepotent response habit through high-frequency Go trials, making inhibitory failures under fatigue directly measurable. In multiple sclerosis, attention lapses and inhibitory control deficits affect approximately 50–60% of patients and are strongly correlated with lesion load in frontal white-matter tracts. SART scores distinguish commission errors (inhibitory failure) from omission errors (sustained-attention lapse), providing two clinically meaningful markers within a single brief test.</p>
			</div>

			<TaskPracticeActions
				locale={$locale}
				startLabel={localeText({ en: 'Start Actual Task', bn: 'আসল টাস্ক শুরু করুন' }, $locale)}
				statusMessage={practiceStatusMessage}
				on:start={() => startTask(TASK_PLAY_MODE.RECORDED)}
				on:practice={() => startTask(TASK_PLAY_MODE.PRACTICE)}
			/>
		</div>
	{:else if state === STATE.READY}
		<section class="panel ready">
			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} />
			{/if}
			<p class="eyebrow">Get Ready</p>
			<h2>{countdown}</h2>
			<p>Remember: press for every digit except {sessionData.target_digit}.</p>
		</section>
	{:else if state === STATE.PLAYING}
		<section class="panel play">
			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} />
			{/if}
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
	.sart-page {
		min-height: 100vh;
		background: #C8DEFA;
		padding: 2rem 1rem 3rem;
		color: #2e312f;
	}

	/* Page content wrapper */
	.page-content {
		max-width: 1100px;
		margin: 0 auto;
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	/* Task header */
	.task-header {
		display: flex;
		align-items: center;
		gap: 1rem;
	}
	.back-btn {
		background: white;
		color: #0d9488;
		border: 2px solid #0d9488;
		padding: 0.6rem 1.25rem;
		border-radius: 8px;
		cursor: pointer;
		font-size: 0.9rem;
		font-weight: 600;
		white-space: nowrap;
		transition: background 0.2s, color 0.2s;
	}
	.back-btn:hover { background: #0d9488; color: white; }
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
		color: #134e4a;
		margin: 0;
	}

	/* Concept card */
	.concept-card {
		background: white;
		border-radius: 16px;
		padding: 2rem;
		box-shadow: 0 4px 6px rgba(0,0,0,0.07);
	}
	.concept-badge {
		display: inline-block;
		background: #f0fdfa;
		color: #0d9488;
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
		color: #134e4a;
		margin: 0 0 0.75rem;
	}
	.concept-card p { color: #374151; line-height: 1.65; margin: 0; }

	/* Rules card */
	.rules-card {
		background: white;
		border-radius: 16px;
		padding: 2rem;
		box-shadow: 0 4px 6px rgba(0,0,0,0.07);
	}
	.rules-card h3 { font-size: 1.1rem; font-weight: 700; color: #134e4a; margin: 0 0 1rem; }
	.rules-list {
		margin: 0 0 1rem;
		padding-left: 1.5rem;
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}
	.rules-list li { color: #374151; line-height: 1.55; }
	.rules-list li strong { color: #0d9488; }
	.rules-note {
		margin: 0;
		background: #f0fdfa;
		color: #0d9488;
		border-radius: 8px;
		padding: 0.75rem 1rem;
		font-size: 0.9rem;
		line-height: 1.5;
	}

	/* Info grid */
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
		color: #0d9488;
		margin-bottom: 0.25rem;
	}
	.info-val {
		font-size: 1.5rem;
		font-weight: 800;
		color: #134e4a;
		margin-bottom: 0.5rem;
	}
	.info-card p { font-size: 0.875rem; color: #6b7280; line-height: 1.5; margin: 0; }

	/* Tip card */
	.tip-card {
		background: #f0fdfa;
		border: 1px solid #99f6e4;
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
	.tip-card li strong { color: #0d9488; }
	.tip-card.minimal p { color: #374151; line-height: 1.6; margin: 0; }
	.tip-title {
		font-size: 0.8rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.5px;
		color: #0d9488;
		margin-bottom: 0.5rem;
	}
	.tip-row { display: flex; align-items: center; justify-content: space-between; gap: 1.5rem; }
	.show-more-btn {
		background: white;
		border: 1.5px solid #0d9488;
		color: #0d9488;
		padding: 0.5rem 1.1rem;
		border-radius: 8px;
		cursor: pointer;
		font-size: 0.875rem;
		font-weight: 600;
		white-space: nowrap;
		flex-shrink: 0;
		transition: all 0.2s;
	}
	.show-more-btn:hover { background: #0d9488; color: white; }

	/* Clinical card */
	.clinical-card {
		background: #f0fdf4;
		border: 1px solid #bbf7d0;
		border-radius: 16px;
		padding: 1.5rem 2rem;
	}
	.clinical-card h3 { font-size: 1rem; font-weight: 700; color: #14532d; margin: 0 0 0.75rem; }
	.clinical-card p { color: #166534; font-size: 0.95rem; line-height: 1.65; margin: 0; }

	.panel {
		max-width: 960px;
		margin: 0 auto;
		background: rgba(255,255,255,0.9);
		border: 1px solid rgba(133, 129, 118, 0.18);
		border-radius: 26px;
		padding: 2rem;
		box-shadow: 0 24px 60px rgba(44, 46, 45, 0.08);
	}

	.header, .actions, .results, .play-header {
		display: flex;
		gap: 1rem;
	}

	.header, .play-header {
		justify-content: space-between;
		align-items: flex-start;
	}

	.results, .actions {
		flex-wrap: wrap;
	}

	.eyebrow {
		margin: 0 0 0.5rem;
		text-transform: uppercase;
		letter-spacing: 0.16em;
		font-size: 0.78rem;
		font-weight: 700;
		color: #0d9488;
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

	.metric {
		flex: 1 1 280px;
		padding: 1.25rem;
		border-radius: 22px;
		background: white;
		border: 1px solid #e5e7eb;
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
		background: #0d9488;
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
		background: #f0fdfa;
		font-weight: 700;
		color: #0d9488;
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
		background: linear-gradient(90deg, #5eead4 0%, #0d9488 100%);
	}

	.digit-stage {
		min-height: 280px;
		border-radius: 28px;
		background: #f0fdfa;
		display: flex;
		align-items: center;
		justify-content: center;
		border: 1px solid #99f6e4;
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
		background: #0d9488;
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

		.header, .play-header {
			flex-direction: column;
		}

		.digit-stage {
			min-height: 220px;
		}
	}
</style>

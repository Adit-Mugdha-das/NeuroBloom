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

	/** @param {"practice" | "recorded"} nextMode */
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
		<div class="page-content">
			<div class="task-header">
				<button class="back-btn" on:click={() => goto('/training')}>← Back to Training</button>
				<div class="header-center">
					<h1 class="task-title">Landmark Task</h1>
					<DifficultyBadge {difficulty} domain="Visual Scanning" />
				</div>
			</div>

			{#if practiceStatusMessage}
				<div class="practice-note">{practiceStatusMessage}</div>
			{/if}

			<div class="concept-card">
				<span class="concept-badge">Visual Scanning · Spatial Attention</span>
				<h2>The Core Principle</h2>
				<p>
					Each trial shows a horizontal line with a vertical tick mark already drawn on it. Your task
					is to judge whether the tick divides the line exactly at its midpoint, or whether the left or
					right segment appears longer. No drawing — pure perceptual judgment. This isolates spatial
					attention balance from motor skill entirely.
				</p>
			</div>

			<div class="rules-card">
				<h3>Reading the Line</h3>
				<ol class="rules-list">
					<li>The tick mark on the line is the bisection point — judge the two resulting segments.</li>
					<li>If the <strong>left segment looks longer</strong>, the tick is shifted right → choose <strong>Left Longer</strong>.</li>
					<li>If the <strong>right segment looks longer</strong>, the tick is shifted left → choose <strong>Right Longer</strong>.</li>
					<li>If both segments appear equal, choose <strong>Equal</strong>. Equal trials make up ~20% of the session.</li>
				</ol>
				<p class="rules-note">
					Keyboard: <strong>A</strong> or ← for Left Longer · <strong>S</strong> or ↓ for Equal · <strong>L</strong> or → for Right Longer
				</p>
			</div>

			<div class="info-grid">
				<div class="info-card">
					<div class="info-label">Total Trials</div>
					<div class="info-val">{sessionData?.total_trials ?? '—'}</div>
					<p>Increases with difficulty</p>
				</div>
				<div class="info-card">
					<div class="info-label">Line Length</div>
					<div class="info-val">360–540px</div>
					<p>Longer lines at higher levels</p>
				</div>
				<div class="info-card">
					<div class="info-label">Offset Range</div>
					<div class="info-val">±10–30px</div>
					<p>Smaller at harder levels</p>
				</div>
				<div class="info-card">
					<div class="info-label">Equal Trials</div>
					<div class="info-val">~20%</div>
					<p>Per session</p>
				</div>
			</div>

			<div class="tip-card">
				<div class="tip-row">
					<div>
						<p class="tip-title">Tips for Accuracy</p>
						<ul>
							<li><strong>Judge the segments</strong>, not the tick mark itself — focus on the two white spaces.</li>
							<li><strong>Centre your gaze</strong> before each trial to prevent carry-over bias from the previous response.</li>
							<li><strong>Trust your first impression</strong> — deliberate re-inspection often introduces second-guessing without improving accuracy.</li>
						</ul>
					</div>
					<button class="show-more-btn" on:click={() => (showHelp = !showHelp)}>
						{showHelp ? 'Less' : 'More tips'}
					</button>
				</div>
				{#if showHelp}
					<ul style="margin-top: 0.75rem;">
						<li>Avoid tilting your head — it shifts the apparent midpoint perceptually.</li>
						<li>If you notice you are consistently choosing left or right, slow down — systematic bias is the key clinical signal this task measures.</li>
					</ul>
				{/if}
			</div>

			<div class="clinical-card">
				<h3>Clinical Significance</h3>
				<p>
					Pseudoneglect — the normal tendency to slightly over-extend bisections to the left — is
					detectable with the Landmark Task without any drawing motor requirement. In MS, white-matter
					lesions in right-hemisphere parietal pathways can shift this bias rightward, indicating
					hemispatial attention asymmetry. The lateral bias index computed from your responses serves
					as a screen for such shifts over training time (Harvey et al., 1995; Milner et al., 1992).
				</p>
			</div>

			<TaskPracticeActions
				locale={$locale}
				startLabel={localeText({ en: 'Start Landmark Task', bn: 'ল্যান্ডমার্ক টাস্ক শুরু করুন' }, $locale)}
				statusMessage={practiceStatusMessage}
				on:start={() => startTask(TASK_PLAY_MODE.RECORDED)}
				on:practice={() => startTask(TASK_PLAY_MODE.PRACTICE)}
			/>
		</div>
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
	/* ── Container ─────────────────────────────────────────── */
	.landmark-page {
		min-height: 100vh;
		background: #C8DEFA;
		padding: 2rem 1rem 3rem;
		color: #2a3130;
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
		color: #1f6670;
		border: 2px solid #1f6670;
		padding: 0.6rem 1.25rem;
		border-radius: 8px;
		cursor: pointer;
		font-size: 0.9rem;
		font-weight: 600;
		white-space: nowrap;
		transition: background 0.2s, color 0.2s;
	}
	.back-btn:hover { background: #1f6670; color: white; }

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
		color: #164e55;
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
		background: #ecfeff;
		color: #1f6670;
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
		color: #164e55;
		margin: 0 0 0.75rem;
	}
	.concept-card p { color: #374151; line-height: 1.65; margin: 0; }

	.rules-card {
		background: white;
		border-radius: 16px;
		padding: 2rem;
		box-shadow: 0 4px 6px rgba(0,0,0,0.07);
	}
	.rules-card h3 { font-size: 1.1rem; font-weight: 700; color: #164e55; margin: 0 0 1rem; }

	.rules-list {
		margin: 0 0 1rem;
		padding-left: 1.5rem;
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}
	.rules-list li { color: #374151; line-height: 1.55; }
	.rules-list li strong { color: #1f6670; }

	.rules-note {
		margin: 0;
		background: #ecfeff;
		color: #1f6670;
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
		color: #1f6670;
		margin-bottom: 0.25rem;
	}

	.info-val {
		font-size: 1.5rem;
		font-weight: 800;
		color: #164e55;
		margin-bottom: 0.5rem;
	}
	.info-card p { font-size: 0.875rem; color: #6b7280; line-height: 1.5; margin: 0; }

	.tip-card {
		background: #f0fdfe;
		border: 1px solid #a5f3fc;
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
	.tip-card li strong { color: #1f6670; }

	.tip-title {
		font-size: 0.8rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.5px;
		color: #1f6670;
		margin-bottom: 0.5rem;
	}

	.tip-row { display: flex; align-items: center; justify-content: space-between; gap: 1.5rem; }

	.show-more-btn {
		background: white;
		border: 1.5px solid #1f6670;
		color: #1f6670;
		padding: 0.5rem 1.1rem;
		border-radius: 8px;
		cursor: pointer;
		font-size: 0.875rem;
		font-weight: 600;
		white-space: nowrap;
		flex-shrink: 0;
		transition: all 0.2s;
	}
	.show-more-btn:hover { background: #1f6670; color: white; }

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
		background: rgba(255,255,255,0.93);
		border: 1px solid rgba(102,120,118,0.18);
		border-radius: 28px;
		padding: 2rem;
		box-shadow: 0 24px 60px rgba(41,49,48,0.08);
	}

	.header, .actions, .results, .play-header, .response-grid {
		display: flex;
		gap: 1rem;
	}

	.header, .play-header {
		justify-content: space-between;
		align-items: flex-start;
	}

	.actions, .results, .response-grid {
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

	h1 { margin: 0 0 0.75rem; font-size: clamp(2rem, 4vw, 3.1rem); }
	h2 { margin: 0 0 0.75rem; font-size: clamp(1.4rem, 3vw, 2rem); }

	.subtitle { max-width: 54rem; line-height: 1.6; color: #64706d; }
	.subtitle.center { text-align: center; margin: 1rem auto 0; }

	.metric {
		flex: 1 1 240px;
		padding: 1.25rem;
		border-radius: 22px;
		background: white;
		border: 1px solid rgba(102,120,118,0.14);
		display: flex;
		flex-direction: column;
		gap: 0.45rem;
	}

	.metric.primary-metric {
		background: #1f6670;
		color: white;
	}

	.metric span {
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		opacity: 0.78;
	}

	.metric strong { font-size: 1.5rem; }

	button { border: none; cursor: pointer; font-weight: 700; }

	.primary, .secondary {
		padding: 0.95rem 1.35rem;
		border-radius: 16px;
	}

	.primary { background: #1f6670; color: white; }
	.secondary { background: rgba(83,96,94,0.1); color: #404746; }

	.rule-chip {
		padding: 0.65rem 0.9rem;
		border-radius: 999px;
		background: #ecfeff;
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
		background: linear-gradient(90deg, #67e8f9 0%, #1f6670 100%);
	}

	.line-stage { margin: 1.5rem 0; }

	.line-card {
		padding: 2rem 1rem;
		border-radius: 28px;
		background: #f0fdfe;
		border: 1px solid rgba(102,120,118,0.16);
	}

	.response-grid { justify-content: center; }

	.response-btn {
		flex: 1 1 220px;
		padding: 1.15rem 1rem;
		border-radius: 20px;
		background: white;
		border: 2px solid rgba(102,120,118,0.16);
		box-shadow: 0 12px 28px rgba(41,49,48,0.06);
		color: #29302f;
		font-size: 1rem;
	}

	.response-btn small {
		display: block;
		margin-top: 0.35rem;
		font-size: 0.8rem;
		color: #697370;
	}

	.response-btn.left  { border-top: 5px solid #2c7b85; }
	.response-btn.equal { border-top: 5px solid #cb6f27; }
	.response-btn.right { border-top: 5px solid #5b8f4c; }

	.results { margin-top: 1.5rem; display: flex; gap: 1rem; flex-wrap: wrap; }

	.difficulty {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		margin-top: 1.5rem;
		font-weight: 700;
	}

	.arrow { font-size: 1.2rem; color: #798280; }

	@media (max-width: 780px) {
		.panel { padding: 1.25rem; }
		.header, .play-header { flex-direction: column; }
	}
</style>

<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
	import TaskReturnButton from '$lib/components/TaskReturnButton.svelte';
	import { locale, localeText, formatNumber, formatPercent, taskPhraseText, taskValueText } from '$lib/i18n';
	import { buildPracticePayload, getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
	import { TASK_RETURN_CONTEXT } from '$lib/task-navigation';
	import { onMount } from 'svelte';

	import { API_BASE_URL } from '$lib/api';

	const STATE = {
		LOADING: 'loading',
		INSTRUCTIONS: 'instructions',
		PLAYING: 'playing',
		COMPLETE: 'complete'
	};
	const lt = (en, bn) => localeText({ en, bn }, $locale);

	function n(value, options = {}) {
		return formatNumber(value, $locale, options);
	}

	function fixed(value, digits = 1) {
		return n(value, {
			minimumFractionDigits: digits,
			maximumFractionDigits: digits
		});
	}

	function pct(value) {
		return formatPercent(value, $locale, {
			minimumFractionDigits: 1,
			maximumFractionDigits: 1
		});
	}

	function ms(value) {
		return `${n(value, { maximumFractionDigits: 0 })} ${lt('ms', 'মি.সে.')}`;
	}

	function trialText(current, total) {
		return lt(`Trial ${n(current)} of ${n(total)}`, `${n(total)}টির মধ্যে ${n(current)} নম্বর ট্রায়াল`);
	}

	function landmarkResponse(value) {
		return taskValueText('landmark_response', value, $locale);
	}

	function adaptationReasonText(reason) {
		if ($locale === 'en' && reason) return reason;
		return taskPhraseText('no_adaptation_reason', $locale);
	}

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
			alert(lt('Failed to load Landmark Task', 'ল্যান্ডমার্ক টাস্ক লোড করা যায়নি'));
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

	function leavePractice(completed = false) {
		sessionData = structuredClone(recordedSessionData);
		playMode = TASK_PLAY_MODE.RECORDED;
		practiceStatusMessage = completed ? getPracticeCopy($locale).complete : '';
		responses = [];
		currentTrialIndex = 0;
		currentTrial = sessionData.trials[0];
		trialStartedAt = 0;
		state = STATE.INSTRUCTIONS;
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
			leavePractice(true);
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
			alert(lt('Failed to submit results', 'ফলাফল জমা দেওয়া যায়নি'));
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
		<div class="intro-wrapper">
			<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />
			<div class="hero-banner">
				<div class="hero-inner">
					<div class="hero-text">
						<span class="hero-badge">{lt('Visual Scanning · Spatial Attention', 'দৃশ্য খোঁজা · স্থানিক মনোযোগ')}</span>
						<h1 class="hero-title">{lt('Landmark Task', 'ল্যান্ডমার্ক টাস্ক')}</h1>
						<p class="hero-desc">{lt('Pure perceptual spatial judgment, no drawing required', 'শুধু চোখে দেখে স্থানিক বিচার, আঁকতে হবে না')}</p>
					</div>
					<DifficultyBadge {difficulty} domain={lt('Visual Scanning', 'দৃশ্য খোঁজা')} />
				</div>
			</div>

			{#if practiceStatusMessage}
				<div class="practice-note">{practiceStatusMessage}</div>
			{/if}

			<div class="concept-card">
				<span class="concept-badge">{lt('Visual Scanning · Spatial Attention', 'দৃশ্য খোঁজা · স্থানিক মনোযোগ')}</span>
				<h2>{lt('The Core Principle', 'মূল ধারণা')}</h2>
				<p>
					{lt(
						'Each trial shows a horizontal line with a vertical mark. Judge whether the mark divides the line exactly in the middle, or whether the left or right side looks longer. No drawing is needed.',
						'প্রতিটি ট্রায়ালে একটি অনুভূমিক রেখা ও তার ওপর একটি উল্লম্ব দাগ দেখা যাবে। দাগটি ঠিক মাঝখানে আছে কি না, নাকি বাম বা ডান অংশ বেশি লম্বা দেখাচ্ছে, সেটি বিচার করুন। কিছু আঁকতে হবে না।'
					)}
				</p>
			</div>

			<div class="rules-card">
				<h3>{lt('Reading the Line', 'রেখাটি কীভাবে পড়বেন')}</h3>
				<ol class="rules-list">
					<li>{lt('The mark on the line is the dividing point. Compare the two sides.', 'রেখার ওপরের দাগটাই ভাগ করার জায়গা। দুই পাশ তুলনা করুন।')}</li>
					<li>{lt('If the left segment looks longer, choose', 'বাম পাশ লম্বা দেখালে বেছে নিন')} <strong>{landmarkResponse('left')}</strong>.</li>
					<li>{lt('If the right segment looks longer, choose', 'ডান পাশ লম্বা দেখালে বেছে নিন')} <strong>{landmarkResponse('right')}</strong>.</li>
					<li>{lt('If both sides look equal, choose', 'দুই পাশ সমান দেখালে বেছে নিন')} <strong>{landmarkResponse('equal')}</strong>.</li>
				</ol>
				<p class="rules-note">
					{lt('Keyboard', 'কিবোর্ড')}: <strong>A</strong> {lt('or', 'বা')} ← {lt('for', 'এর জন্য')} {landmarkResponse('left')} ·
					<strong>S</strong> {lt('or', 'বা')} ↓ {lt('for', 'এর জন্য')} {landmarkResponse('equal')} ·
					<strong>L</strong> {lt('or', 'বা')} → {lt('for', 'এর জন্য')} {landmarkResponse('right')}
				</p>
			</div>

			<div class="info-grid">
				<div class="info-card">
					<div class="info-label">{lt('Total Trials', 'মোট ট্রায়াল')}</div>
					<div class="info-val">{sessionData?.total_trials ? n(sessionData.total_trials) : '—'}</div>
					<p>{lt('Increases with difficulty', 'কঠিনতা বাড়লে ট্রায়ালও বাড়ে')}</p>
				</div>
				<div class="info-card">
					<div class="info-label">{lt('Line Length', 'রেখার দৈর্ঘ্য')}</div>
					<div class="info-val">{lt('360–540px', '৩৬০–৫৪০px')}</div>
					<p>{lt('Longer lines at higher levels', 'উচ্চ লেভেলে রেখা দীর্ঘ হয়')}</p>
				</div>
				<div class="info-card">
					<div class="info-label">{lt('Offset Range', 'সরার পরিসর')}</div>
					<div class="info-val">{lt('±10–30px', '±১০–৩০px')}</div>
					<p>{lt('Smaller at harder levels', 'কঠিন লেভেলে পার্থক্য ছোট হয়')}</p>
				</div>
				<div class="info-card">
					<div class="info-label">{lt('Equal Trials', 'সমান ট্রায়াল')}</div>
					<div class="info-val">{lt('~20%', '~২০%')}</div>
					<p>{lt('Per session', 'প্রতি সেশনে')}</p>
				</div>
			</div>

			<div class="tip-card">
				<div class="tip-row">
					<div>
						<p class="tip-title">{lt('Tips for Accuracy', 'সঠিকতার টিপস')}</p>
						<ul>
							<li><strong>{lt('Judge the segments', 'দুই অংশ বিচার করুন')}</strong>, {lt('not the mark itself.', 'শুধু দাগটাকে নয়।')}</li>
							<li><strong>{lt('Centre your gaze', 'চোখ মাঝামাঝি রাখুন')}</strong> {lt('before each trial.', 'প্রতিটি ট্রায়ালের আগে।')}</li>
							<li><strong>{lt('Trust your first impression', 'প্রথম ধারণাকে বিশ্বাস করুন')}</strong> {lt('and avoid over-checking.', 'এবং বারবার মাপার চেষ্টা করবেন না।')}</li>
						</ul>
					</div>
					<button class="show-more-btn" on:click={() => (showHelp = !showHelp)}>
						{showHelp ? lt('Less', 'কম দেখান') : lt('More tips', 'আরও টিপস')}
					</button>
				</div>
				{#if showHelp}
					<ul style="margin-top: 0.75rem;">
						<li>{lt('Avoid tilting your head because it can shift the apparent midpoint.', 'মাথা কাত করবেন না, এতে মাঝখানটা চোখে সরেছে বলে মনে হতে পারে।')}</li>
						<li>{lt('If you keep choosing one side, slow down slightly and re-center your gaze.', 'একই দিক বারবার বেছে নিলে একটু ধীরে চোখ মাঝখানে আনুন।')}</li>
					</ul>
				{/if}
			</div>

			<div class="clinical-card">
				<h3>{lt('Clinical Significance', 'ক্লিনিক্যাল গুরুত্ব')}</h3>
				<p>
					{lt(
						'The Landmark Task helps track spatial attention balance without requiring drawing or hand control.',
						'ল্যান্ডমার্ক টাস্ক আঁকা বা হাতের নিয়ন্ত্রণ ছাড়াই স্থানিক মনোযোগের ভারসাম্য বুঝতে সাহায্য করে।'
					)}
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
				<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
			{/if}
			<div class="play-header">
				<div>
					<p class="eyebrow">{trialText(currentTrialIndex + 1, sessionData.total_trials)}</p>
					<h2>{lt('Which side is longer?', 'কোন দিকটি বেশি লম্বা?')}</h2>
				</div>
				<div class="rule-chip">{lt('Midpoint Judgment', 'মধ্যবিন্দু বিচার')}</div>
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
					{landmarkResponse('left')}
					<small>A / {lt('Left Arrow', 'বাম তীর')}</small>
				</button>
				<button class="response-btn equal" on:click={() => submitResponse('equal')}>
					{landmarkResponse('equal')}
					<small>S / {lt('Down Arrow', 'নিচের তীর')}</small>
				</button>
				<button class="response-btn right" on:click={() => submitResponse('right')}>
					{landmarkResponse('right')}
					<small>L / {lt('Right Arrow', 'ডান তীর')}</small>
				</button>
			</div>
		</section>
	{:else if state === STATE.COMPLETE}
		<section class="panel hero">
			<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />
			<div class="header">
				<div>
					<p class="eyebrow">{lt('Session Complete', 'সেশন শেষ')}</p>
					<h1>{lt('Landmark Results', 'ল্যান্ডমার্ক ফলাফল')}</h1>
					<p class="subtitle">{lt('Your spatial-bias and midpoint-judgment metrics are now part of the visual-scanning profile.', 'আপনার স্থানিক বায়াস ও মধ্যবিন্দু বিচার এখন দৃশ্য-স্ক্যানিং প্রোফাইলে যোগ হয়েছে।')}</p>
				</div>
			</div>

			{#if newBadges.length > 0}
				<BadgeNotification badges={newBadges} />
			{/if}

			<div class="results">
				<div class="metric primary-metric">
					<span>{lt('Overall score', 'সামগ্রিক স্কোর')}</span>
					<strong>{n(sessionResults.metrics.score)}</strong>
				</div>
				<div class="metric">
					<span>{lt('Accuracy', 'সঠিকতা')}</span>
					<strong>{pct(sessionResults.metrics.accuracy)}</strong>
				</div>
				<div class="metric">
					<span>{lt('Offset accuracy', 'সরানো রেখায় সঠিকতা')}</span>
					<strong>{pct(sessionResults.metrics.offset_accuracy)}</strong>
				</div>
				<div class="metric">
					<span>{lt('Centered accuracy', 'মাঝামাঝি রেখায় সঠিকতা')}</span>
					<strong>{pct(sessionResults.metrics.centered_accuracy)}</strong>
				</div>
				<div class="metric">
					<span>{lt('Avg RT', 'গড় RT')}</span>
					<strong>{ms(sessionResults.metrics.average_reaction_time)}</strong>
				</div>
				<div class="metric">
					<span>{lt('Spatial bias index', 'স্থানিক বায়াস সূচক')}</span>
					<strong>{fixed(sessionResults.metrics.spatial_bias_index, 1)}</strong>
				</div>
				<div class="metric">
					<span>{lt('Left-bias errors', 'বাম-বায়াস ভুল')}</span>
					<strong>{n(sessionResults.metrics.left_bias_errors)}</strong>
				</div>
				<div class="metric">
					<span>{lt('Right-bias errors', 'ডান-বায়াস ভুল')}</span>
					<strong>{n(sessionResults.metrics.right_bias_errors)}</strong>
				</div>
			</div>

			<div class="difficulty">
				<span>{lt('Level', 'লেভেল')} {n(sessionResults.difficulty_before)}</span>
				<span class="arrow">-&gt;</span>
				<span>{lt('Level', 'লেভেল')} {n(sessionResults.difficulty_after)}</span>
			</div>
			<p class="subtitle center">{adaptationReasonText(sessionResults.adaptation_reason)}</p>

			<div class="actions">
				<button class="primary" on:click={() => goto('/dashboard')}>{lt('Back To Dashboard', 'ড্যাশবোর্ডে ফিরুন')}</button>
				<button class="secondary" on:click={() => goto('/dashboard')}>{lt('Back To Dashboard', 'ড্যাশবোর্ডে ফিরুন')}</button>
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

	/* ── Intro unified card (GoNoGo-style single container) ── */
	.intro-wrapper {
		max-width: 960px;
		margin: 0 auto;
		background: white;
		border-radius: 16px;
		padding: 2.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07), 0 1px 3px rgba(0, 0, 0, 0.06);
		display: flex;
		flex-direction: column;
		gap: 1.8rem;
	}

	.intro-wrapper > .concept-card,
	.intro-wrapper > .rules-card,
	.intro-wrapper > .tip-card,
	.intro-wrapper > .clinical-card {
		box-shadow: none;
		border-radius: 12px;
		backdrop-filter: none;
		-webkit-backdrop-filter: none;
	}

	.intro-wrapper .info-grid .info-card {
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
		backdrop-filter: none;
		-webkit-backdrop-filter: none;
	}

	/* ── Hero Banner ─────────────────────────────────────────── */
	.hero-banner {
		background: rgba(22, 78, 85, 0.82);
		backdrop-filter: blur(18px);
		-webkit-backdrop-filter: blur(18px);
		border-radius: 20px;
		padding: 2.5rem 2rem;
		border: 1px solid rgba(255, 255, 255, 0.18);
		box-shadow: 0 8px 32px rgba(0, 0, 0, 0.18);
	}

	.hero-inner {
		display: flex;
		align-items: center;
		gap: 1.5rem;
		flex-wrap: wrap;
	}

	.hero-text {
		flex: 1;
		text-align: center;
	}

	.hero-badge {
		display: inline-block;
		background: rgba(255, 255, 255, 0.15);
		color: #a5f3fc;
		padding: 0.3rem 1rem;
		border-radius: 20px;
		font-size: 0.78rem;
		font-weight: 700;
		letter-spacing: 0.5px;
		text-transform: uppercase;
		margin-bottom: 0.5rem;
	}

	.hero-title {
		font-size: clamp(1.8rem, 3vw, 2.5rem);
		font-weight: 800;
		color: white;
		margin: 0 0 0.4rem;
		text-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
	}

	.hero-desc {
		color: rgba(255, 255, 255, 0.75);
		font-size: 0.95rem;
		margin: 0;
	}

	.practice-note {
		background: rgba(254, 249, 195, 0.92);
		backdrop-filter: blur(8px);
		-webkit-backdrop-filter: blur(8px);
		border: 1px solid #fde047;
		border-radius: 8px;
		padding: 0.75rem 1rem;
		color: #854d0e;
		font-size: 0.9rem;
		text-align: center;
	}

	.concept-card {
		background: rgba(255, 255, 255, 0.93);
		backdrop-filter: blur(8px);
		-webkit-backdrop-filter: blur(8px);
		border-radius: 16px;
		padding: 2rem;
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
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
		background: rgba(255, 255, 255, 0.93);
		backdrop-filter: blur(8px);
		-webkit-backdrop-filter: blur(8px);
		border-radius: 16px;
		padding: 2rem;
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
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
		background: rgba(255, 255, 255, 0.93);
		backdrop-filter: blur(8px);
		-webkit-backdrop-filter: blur(8px);
		border-radius: 16px;
		padding: 1.5rem;
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
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
		background: rgba(240, 253, 254, 0.92);
		backdrop-filter: blur(8px);
		-webkit-backdrop-filter: blur(8px);
		border: 1px solid #a5f3fc;
		border-radius: 16px;
		padding: 1.5rem 2rem;
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.07);
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
		background: rgba(240, 253, 244, 0.92);
		backdrop-filter: blur(8px);
		-webkit-backdrop-filter: blur(8px);
		border: 1px solid #bbf7d0;
		border-radius: 16px;
		padding: 1.5rem 2rem;
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.07);
	}
	.clinical-card h3 { font-size: 1rem; font-weight: 700; color: #14532d; margin: 0 0 0.75rem; }
	.clinical-card p { color: #166534; font-size: 0.95rem; line-height: 1.65; margin: 0; }

	/* ── Shared panel (gameplay + results) ────────────────── */
	.panel {
		max-width: 980px;
		margin: 0 auto;
		background: rgba(255, 255, 255, 0.93);
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
		border: 1px solid rgba(102, 120, 118, 0.18);
		border-radius: 28px;
		padding: 2rem;
		box-shadow: 0 24px 60px rgba(41, 49, 48, 0.12);
		position: relative;
		z-index: 1;
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
		.hero-inner { flex-direction: column; text-align: center; }
		.hero-text { text-align: center; }
	}
</style>


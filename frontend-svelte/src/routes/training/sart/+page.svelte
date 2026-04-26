<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
	import TaskReturnButton from '$lib/components/TaskReturnButton.svelte';
	import { locale, localeText, formatNumber, formatPercent, taskPhraseText } from '$lib/i18n';
	import { buildPracticePayload, getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
	import { TASK_RETURN_CONTEXT } from '$lib/task-navigation';
	import { onMount } from 'svelte';

	import { API_BASE_URL } from '$lib/api';

	const STATE = {
		LOADING: 'loading',
		INSTRUCTIONS: 'instructions',
		READY: 'ready',
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

	function adaptationReasonText(reason) {
		if ($locale === 'en' && reason) return reason;
		return taskPhraseText('no_adaptation_reason', $locale);
	}

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
	let countdownHandle = null;

	onMount(() => {
		taskId = $page.url.searchParams.get('taskId');
		window.addEventListener('keydown', handleKeyDown);
		loadSession();

		return () => {
			window.removeEventListener('keydown', handleKeyDown);
			if (timerHandle) clearTimeout(timerHandle);
			if (isiHandle) clearTimeout(isiHandle);
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
			alert(lt('Failed to load SART', 'SART লোড করা যায়নি'));
			goto('/dashboard');
		}
	}

	/** @param {"practice" | "recorded"} nextMode */
	function startTask(nextMode = TASK_PLAY_MODE.RECORDED) {
		if (timerHandle) clearTimeout(timerHandle);
		if (isiHandle) clearTimeout(isiHandle);
		if (countdownHandle) clearInterval(countdownHandle);

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
		if (isiHandle) {
			clearTimeout(isiHandle);
			isiHandle = null;
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
		currentDigit = null;
		showDigit = false;
		waitingForResponse = false;
		responses = [];
		countdown = 3;
		state = STATE.INSTRUCTIONS;
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
			leavePractice(true);
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
			alert(lt('Failed to submit results', 'ফলাফল জমা দেওয়া যায়নি'));
			goto('/dashboard');
		}
	}

	$: progress = sessionData ? (currentTrialIndex / sessionData.total_trials) * 100 : 0;
</script>

<div class="sart-page">
	{#if state === STATE.LOADING}
		<LoadingSkeleton variant="card" count={3} />
	{:else if state === STATE.INSTRUCTIONS}
		<div class="intro-wrapper">
			<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />

			<!-- Header -->
			<div class="task-header">
				<div class="header-center">
					<h1 class="task-title">{lt('SART', 'SART')}</h1>
					<DifficultyBadge {difficulty} domain={lt('Attention', 'মনোযোগ')} />
				</div>
			</div>

			<div class="concept-card">
				<div class="concept-badge">{lt('Attention · Vigilance Training', 'মনোযোগ · সতর্কতা অনুশীলন')}</div>
				<h2>{lt('What Is SART?', 'SART কী?')}</h2>
				<p>{lt('Press', 'প্রতিটি সংখ্যায়')} <strong>SPACE</strong> {lt('for every digit except the rare target digit. This measures vigilance and impulse control under repetition.', 'চাপুন, তবে বিরল লক্ষ্য সংখ্যাটি দেখলে চাপবেন না। এতে বারবার একই কাজে সতর্কতা ও তাড়না নিয়ন্ত্রণ বোঝা যায়।')}</p>
			</div>

			<div class="rules-card">
				<h3>{lt('How to Respond', 'কীভাবে উত্তর দেবেন')}</h3>
				<ol class="rules-list">
					<li>{lt('Digits appear one at a time.', 'সংখ্যাগুলো একটির পর একটি দেখা যাবে।')}</li>
					<li>{lt('Press', 'প্রতিটি সংখ্যায়')} <strong>SPACE</strong> {lt('or the on-screen button for every digit.', 'বা স্ক্রিনের বোতাম চাপুন।')}</li>
					<li>{lt('When you see target digit', 'লক্ষ্য সংখ্যা')} <strong>{n(sessionData.target_digit)}</strong> {lt('do NOT press.', 'দেখলে চাপবেন না।')}</li>
					<li>{lt('Keep a steady rhythm. Speed and accuracy both matter.', 'ছন্দ স্থির রাখুন। গতি ও সঠিকতা দুটোই গুরুত্বপূর্ণ।')}</li>
				</ol>
				<p class="rules-note">{lt('The target digit', 'লক্ষ্য সংখ্যা')} <strong>{n(sessionData.target_digit)}</strong> {lt('appears rarely, so stay alert throughout.', 'খুব কম আসে, তাই পুরো সময় সতর্ক থাকুন।')}</p>
			</div>

			<div class="info-grid">
				<div class="info-card">
					<div class="info-label">{lt('Trials', 'ট্রায়াল')}</div>
					<div class="info-val">{n(sessionData.total_trials)}</div>
					<p>{lt('Total digit stimuli presented in this session.', 'এই সেশনে মোট কতটি সংখ্যা দেখানো হবে।')}</p>
				</div>
				<div class="info-card">
					<div class="info-label">{lt('Target Digit', 'লক্ষ্য সংখ্যা')}</div>
					<div class="info-val">{n(sessionData.target_digit)}</div>
					<p>{lt('The only digit you must withhold your response to.', 'একমাত্র এই সংখ্যাটি দেখলে উত্তর আটকে রাখতে হবে।')}</p>
				</div>
				<div class="info-card">
					<div class="info-label">{lt('Scoring', 'স্কোরিং')}</div>
					<div class="info-val">{lt('Dual', 'দুই দিক')}</div>
					<p>{lt('Pressing on the target and missing non-target digits both reduce your score.', 'লক্ষ্য সংখ্যায় চাপা এবং অন্য সংখ্যায় না চাপা, দুটোই স্কোর কমায়।')}</p>
				</div>
			</div>

			{#if showHelp}
				<div class="tip-card">
					<div class="tip-title">{lt('Advanced Tips', 'আরও টিপস')}</div>
					<ul>
						<li><strong>{lt('Steady rhythm:', 'স্থির ছন্দ:')}</strong> {lt('respond at the same pace instead of reacting impulsively.', 'হঠাৎ তাড়াহুড়ো না করে একই ছন্দে উত্তর দিন।')}</li>
						<li><strong>{lt('Reset after targets:', 'লক্ষ্য সংখ্যার পর নিজেকে গুছিয়ে নিন:')}</strong> {lt('re-engage for the next digit.', 'পরের সংখ্যার জন্য আবার মনোযোগ দিন।')}</li>
						<li><strong>{lt('Do not rush:', 'তাড়াহুড়ো নয়:')}</strong> {lt('slow your internal pace if you start pressing too fast.', 'খুব দ্রুত চাপতে শুরু করলে নিজের ছন্দ একটু ধীর করুন।')}</li>
						<li><strong>{lt('Both errors count:', 'দুই ধরনের ভুলই ধরা হয়:')}</strong> {lt('target presses and missed non-targets both matter.', 'লক্ষ্য সংখ্যায় চাপা ও অন্য সংখ্যা মিস করা দুটোই গুরুত্বপূর্ণ।')}</li>
					</ul>
				</div>
			{:else}
				<div class="tip-card minimal">
					<div class="tip-row">
						<div>
							<div class="tip-title">{lt('Strategy', 'কৌশল')}</div>
							<p>{lt('Keep a steady mental rhythm. Only withhold when you see', 'মনে একটি স্থির ছন্দ রাখুন। শুধু')} {n(sessionData.target_digit)} {lt('and stay consistent throughout.', 'দেখলে চাপবেন না এবং পুরো সময় একইভাবে চালিয়ে যান।')}</p>
						</div>
						<button class="show-more-btn" on:click={() => (showHelp = true)}>{lt('More tips', 'আরও টিপস')}</button>
					</div>
				</div>
			{/if}

			<div class="clinical-card">
				<h3>{lt('Clinical Basis', 'ক্লিনিক্যাল ভিত্তি')}</h3>
				<p>{lt('SART is widely used to measure sustained attention, lapses from fatigue, and inhibitory control during repetitive tasks.', 'দীর্ঘসময় মনোযোগ ধরে রাখা, ক্লান্তিতে মনোযোগের ফাঁক, এবং পুনরাবৃত্ত কাজের মধ্যে তাড়না নিয়ন্ত্রণ বোঝার জন্য SART ব্যবহৃত হয়।')}</p>
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
				<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
			{/if}
			<p class="eyebrow">{lt('Get Ready', 'প্রস্তুত হোন')}</p>
			<h2>{n(countdown)}</h2>
			<p>{lt('Remember: press for every digit except', 'মনে রাখুন: শুধু')} {n(sessionData.target_digit)} {lt('the target digit.', 'ছাড়া প্রতিটি সংখ্যায় চাপুন।')}</p>
		</section>
	{:else if state === STATE.PLAYING}
		<section class="panel play">
			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
			{/if}
			<div class="play-header">
				<div>
					<p class="eyebrow">{trialText(currentTrialIndex + 1, sessionData.total_trials)}</p>
					<h2>{lt('Stay steady', 'স্থির থাকুন')}</h2>
				</div>
				<div class="rule-chip">{lt('No press on', 'চাপবেন না')} {n(sessionData.target_digit)}</div>
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
					{lt('Press Space', 'Space চাপুন')}
				</button>
				<p class="hint">{lt('Ignore only the rare target digit.', 'শুধু বিরল লক্ষ্য সংখ্যাটি এড়িয়ে যান।')}</p>
			</div>
		</section>
	{:else if state === STATE.COMPLETE}
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />
		<section class="panel hero">
			<div class="header">
				<div>
					<p class="eyebrow">{lt('Session Complete', 'সেশন শেষ')}</p>
					<h1>{lt('SART Results', 'SART ফলাফল')}</h1>
					<p class="subtitle">{lt('Your vigilance and inhibition scores are now part of the attention profile.', 'আপনার সতর্কতা ও নিয়ন্ত্রণের স্কোর এখন মনোযোগ প্রোফাইলে যুক্ত হয়েছে।')}</p>
				</div>
			</div>

			{#if newBadges.length > 0}
				<BadgeNotification badges={newBadges} />
			{/if}

			<div class="results">
				<div class="metric primary">
					<span>{lt('Overall score', 'সামগ্রিক স্কোর')}</span>
					<strong>{n(sessionResults.metrics.score)}</strong>
				</div>
				<div class="metric">
					<span>{lt('Accuracy', 'সঠিকতা')}</span>
					<strong>{pct(sessionResults.metrics.accuracy)}</strong>
				</div>
				<div class="metric">
					<span>{lt('Go accuracy', 'চাপার সঠিকতা')}</span>
					<strong>{pct(sessionResults.metrics.go_accuracy)}</strong>
				</div>
				<div class="metric">
					<span>{lt('No-go accuracy', 'না-চাপার সঠিকতা')}</span>
					<strong>{pct(sessionResults.metrics.nogo_accuracy)}</strong>
				</div>
				<div class="metric">
					<span>{lt('Avg RT', 'গড় RT')}</span>
					<strong>{ms(sessionResults.metrics.average_reaction_time)}</strong>
				</div>
				<div class="metric">
					<span>{lt('Commission errors', 'ভুল চাপা')}</span>
					<strong>{n(sessionResults.metrics.commission_errors)}</strong>
				</div>
				<div class="metric">
					<span>{lt('Omission errors', 'মিস করা')}</span>
					<strong>{n(sessionResults.metrics.omission_errors)}</strong>
				</div>
				<div class="metric">
					<span>{lt('Vigilance index', 'সতর্কতা সূচক')}</span>
					<strong>{fixed(sessionResults.metrics.vigilance_index, 1)}</strong>
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

	/* Intro unified card (GoNoGo-style single container) */
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
		padding: 1.5rem;
	}

	.intro-wrapper > .info-grid .info-card {
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
	}

	/* Task header */
	.task-header {
		display: flex;
		align-items: center;
		gap: 1rem;
	}
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


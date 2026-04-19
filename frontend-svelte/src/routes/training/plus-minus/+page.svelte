<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
import TaskReturnButton from '$lib/components/TaskReturnButton.svelte';
	import { formatNumber, locale, localeText, translateText } from '$lib/i18n';
	import { buildPracticePayload, getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
import { TASK_RETURN_CONTEXT } from '$lib/task-navigation';
	import { user } from '$lib/stores';
	import { onMount, onDestroy } from 'svelte';

	let phase = 'intro';
	let loading = false;
	let error = null;
	let sessionData = null;
	let difficulty = 1;
	let baselineFlexibility = null;
	let currentBlock = null;
	let currentBlockIndex = 0;
	let currentTrialIndex = 0;
	let responses = [];
	let startTime = null;
	let elapsedTime = 0;
	let timerInterval = null;
	let cueTimeout = null;
	let trialStartTime = null;
	let showCue = false;
	let cueText = '';
	let userAnswer = '';
	let results = null;
	let newBadges = [];
	let currentUser = null;
	let taskId = null;
	/** @type {string} */
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';
	let recordedSessionData = null;
	let recordedDifficulty = 1;

	function t(text) {
		return translateText(text ?? '', $locale);
	}

	function lt(en, bn) {
		return localeText({ en, bn }, $locale);
	}

	function n(value, options = {}) {
		return formatNumber(value, $locale, options);
	}

	function pct(value) {
		return n((value * 100).toFixed(1), { minimumFractionDigits: 1, maximumFractionDigits: 1 });
	}

	function durationMsLabel(ms) {
		return n(ms.toFixed(0)) + lt('ms', 'মি.সে');
	}

	function signedDurationLabel(ms) {
		const prefix = ms >= 0 ? '+' : '';
		return prefix + durationMsLabel(ms);
	}

	function difficultySummary() {
		if (difficulty <= 3) {
			return lt(
				'Single digit numbers, clear cues (2 seconds)',
				'এক অঙ্কের সংখ্যা, স্পষ্ট সংকেত (২ সেকেন্ড)'
			);
		}
		if (difficulty <= 6) {
			return lt(
				'Two digit numbers, subtle cues (1 second)',
				'দুই অঙ্কের সংখ্যা, সূক্ষ্ম সংকেত (১ সেকেন্ড)'
			);
		}
		return lt(
			'Three digit numbers, minimal cues (fast pace)',
			'তিন অঙ্কের সংখ্যা, খুব সংক্ষিপ্ত সংকেত (দ্রুত গতি)'
		);
	}

	function blockTransitionTitle() {
		if (currentBlockIndex === 1) {
			return lt('Block B: Subtract 3', 'ব্লক B: ৩ বিয়োগ করুন');
		}
		if (currentBlockIndex === 2) {
			return lt('Block C: Alternating', 'ব্লক C: পালাবদল');
		}
		return '';
	}

	function blockTransitionMessage() {
		if (currentBlockIndex === 1) {
			return lt(
				'Now SUBTRACT 3 from each number. Keep working as fast and accurately as you can.',
				'এখন প্রতিটি সংখ্যা থেকে ৩ বিয়োগ করুন। যত দ্রুত এবং নির্ভুলভাবে পারেন কাজ চালিয়ে যান।'
			);
		}
		return lt(
			'In this final block, you will ALTERNATE between adding and subtracting. A brief cue (+3 or -3) will flash before each number. Pay close attention.',
			'এই শেষ ব্লকে কখনো যোগ, কখনো বিয়োগ করতে হবে। প্রতিটি সংখ্যার আগে একটি সংকেত (+৩ বা -৩) ঝলকাবে।'
		);
	}

	function currentBlockLabel(blockNum) {
		return lt(
			`Block ${blockNum} of 3: ${t(currentBlock?.instruction || '')}`,
			`৩টির মধ্যে ব্লক ${n(blockNum)}: ${t(currentBlock?.instruction || '')}`
		);
	}

	function trialProgressLabel(current, total) {
		return lt(`Trial ${current} / ${total}`, `ট্রায়াল ${n(current)} / ${n(total)}`);
	}

	user.subscribe((value) => {
		currentUser = value;
	});

	function cloneData(value) {
		if (typeof structuredClone === 'function') {
			return structuredClone(value);
		}
		return JSON.parse(JSON.stringify(value));
	}

	function restoreRecordedSession() {
		if (recordedSessionData) {
			sessionData = cloneData(recordedSessionData);
		}
		difficulty = recordedDifficulty;
	}

	async function loadSession() {
		try {
			loading = true;
			error = null;
			const baselineResponse = await fetch(
				`http://localhost:8000/api/baseline/${currentUser.id}`
			);
			if (baselineResponse.ok) {
				const baselineData = await baselineResponse.json();
				baselineFlexibility = baselineData.flexibility;
				if (baselineFlexibility !== null) {
					if (baselineFlexibility >= 90) difficulty = 9;
					else if (baselineFlexibility >= 80) difficulty = 8;
					else if (baselineFlexibility >= 70) difficulty = 7;
					else if (baselineFlexibility >= 60) difficulty = 6;
					else if (baselineFlexibility >= 50) difficulty = 5;
					else if (baselineFlexibility >= 40) difficulty = 4;
					else if (baselineFlexibility >= 30) difficulty = 3;
					else if (baselineFlexibility >= 20) difficulty = 2;
					else difficulty = 1;
				}
			}
			const response = await fetch(
				`http://localhost:8000/api/tasks/plus-minus/generate?difficulty=${difficulty}`,
				{ method: 'POST', headers: { 'Content-Type': 'application/json' } }
			);
			if (!response.ok) throw new Error('Failed to load session');
			sessionData = await response.json();
			recordedSessionData = cloneData(sessionData);
			difficulty = sessionData.difficulty;
			recordedDifficulty = difficulty;
		} catch (err) {
			error = err.message;
		} finally {
			loading = false;
		}
	}

	/** @param {string} nextMode */
	function startTask(nextMode = TASK_PLAY_MODE.RECORDED) {
		if (timerInterval) {
			clearInterval(timerInterval);
			timerInterval = null;
		}
		if (cueTimeout) {
			clearTimeout(cueTimeout);
			cueTimeout = null;
		}

		playMode = nextMode;
		practiceStatusMessage = '';
		restoreRecordedSession();
		if (playMode === TASK_PLAY_MODE.PRACTICE) {
			sessionData = buildPracticePayload('plus-minus', recordedSessionData);
		}
		currentBlockIndex = 0;
		currentTrialIndex = 0;
		responses = [];
		results = null;
		showCue = false;
		userAnswer = '';
		currentBlock = sessionData.blocks.block_a;
		phase = 'task';
		startTime = Date.now();
		elapsedTime = 0;
		timerInterval = setInterval(() => {
			elapsedTime = (Date.now() - startTime) / 1000;
		}, 100);
		startTrial();
	}

	function startTrial() {
		trialStartTime = Date.now();
		userAnswer = '';
		const trial = getCurrentTrial();
		if (cueTimeout) {
			clearTimeout(cueTimeout);
			cueTimeout = null;
		}
		if (trial && currentBlock.name === 'alternating') {
			showCue = true;
			cueText = trial.operation === 'add' ? '+3' : '-3';
			cueTimeout = setTimeout(() => {
				cueTimeout = null;
				showCue = false;
			}, sessionData.config.cue_duration_ms);
		}
	}

	async function leavePractice(completed = false) {
		if (timerInterval) {
			clearInterval(timerInterval);
			timerInterval = null;
		}
		if (cueTimeout) {
			clearTimeout(cueTimeout);
			cueTimeout = null;
		}

		playMode = TASK_PLAY_MODE.RECORDED;
		practiceStatusMessage = completed ? getPracticeCopy($locale).complete : '';
		currentBlock = null;
		currentBlockIndex = 0;
		currentTrialIndex = 0;
		responses = [];
		showCue = false;
		cueText = '';
		userAnswer = '';
		results = null;
		startTime = null;
		elapsedTime = 0;
		phase = 'intro';

		if (completed) {
			await loadSession();
		} else {
			restoreRecordedSession();
		}
	}

	function getCurrentTrial() {
		if (!currentBlock || currentTrialIndex >= currentBlock.trials.length) {
			return null;
		}
		return currentBlock.trials[currentTrialIndex];
	}

	function handleSubmit() {
		const trial = getCurrentTrial();
		if (!trial || userAnswer === '') return;
		const responseTime = Date.now() - trialStartTime;
		const answer = parseInt(userAnswer);
		if (isNaN(answer)) {
			userAnswer = '';
			return;
		}
		responses.push({
			trial_number: trial.trial_number,
			user_answer: answer,
			correct_answer: trial.correct_answer,
			reaction_time_ms: responseTime,
			block: currentBlock.name,
			operation: trial.operation,
			is_switch: trial.is_switch || false
		});
		moveToNextTrial();
	}

	function handleKeyPress(event) {
		if (event.key === 'Enter') {
			handleSubmit();
			return;
		}
		const allowedKeys = [
			'0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
			'-', 'Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab'
		];
		if (!allowedKeys.includes(event.key)) {
			event.preventDefault();
		}
	}

	function moveToNextTrial() {
		currentTrialIndex++;
		if (currentTrialIndex >= currentBlock.trials.length) {
			currentBlockIndex++;
			if (currentBlockIndex === 1) {
				currentBlock = sessionData.blocks.block_b;
				currentTrialIndex = 0;
				phase = 'block-transition';
			} else if (currentBlockIndex === 2) {
				currentBlock = sessionData.blocks.block_c;
				currentTrialIndex = 0;
				phase = 'block-transition';
			} else {
				submitSession();
				return;
			}
		} else {
			startTrial();
		}
	}

	function continueToNextBlock() {
		phase = 'task';
		startTrial();
	}

	async function submitSession() {
		if (timerInterval) {
			clearInterval(timerInterval);
			timerInterval = null;
		}
		if (playMode === TASK_PLAY_MODE.PRACTICE) {
			await leavePractice(true);
			return;
		}
		try {
			loading = true;
			error = null;
			const totalTime = Date.now() - startTime;
			taskId = $page.url.searchParams.get('taskId');
			const submitResponse = await fetch(
				`http://localhost:8000/api/training/tasks/plus-minus/submit/${currentUser.id}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						session_data: sessionData,
						user_responses: responses,
						total_time: totalTime,
						task_id: taskId
					})
				}
			);
			if (!submitResponse.ok) throw new Error('Failed to submit result');
			const submitData = await submitResponse.json();
			results = submitData;
			newBadges = submitData.newly_earned_badges || [];
			phase = 'results';
		} catch (err) {
			error = err.message;
		} finally {
			loading = false;
		}
	}

	onMount(async () => {
		if (!currentUser) {
			goto('/login');
			return;
		}
		await loadSession();
	});

	onDestroy(() => {
		if (timerInterval) {
			clearInterval(timerInterval);
			timerInterval = null;
		}
		if (cueTimeout) {
			clearTimeout(cueTimeout);
			cueTimeout = null;
		}
	});
</script>

<div class="pm-page" data-localize-skip>
	<div class="pm-wrapper">

		{#if loading}
			<LoadingSkeleton />
		{:else if error}
			<div class="error-card">
				<p>{t('Error:')} {t(error)}</p>
				<button class="retry-btn" on:click={loadSession}>{t('Retry')}</button>
			</div>

		{:else if phase === 'intro'}
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />

			<!-- Header Card -->
			<div class="header-card">
				<div class="header-content">
					<div class="header-text">
						<h1 class="task-title">{t('Plus-Minus Task')}</h1>
						<p class="task-domain">{lt('Cognitive Flexibility', 'জ্ঞানীয় নমনীয়তা')}</p>
					</div>
					<DifficultyBadge {difficulty} domain="Cognitive Flexibility" />
				</div>
			</div>

			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
			{/if}

			<!-- Task Concept -->
			<div class="card task-concept">
				<div class="concept-badge">
					<span class="badge-icon">+/-</span>
					<span>{lt('Switching Paradigm', 'স্যুইচিং প্যারাডাইম')}</span>
				</div>
				<p class="concept-desc">
					{lt(
						'The Plus-Minus Task measures cognitive switching cost — the time penalty you pay when alternating between mental operations. Jersild (1927) first described switching costs; Miyake et al. (2000) established shifting as a core executive function reliably impaired in multiple sclerosis.',
						'প্লাস-মাইনাস টাস্কটি জ্ঞানীয় স্যুইচিং কস্ট পরিমাপ করে — মানসিক অপারেশন পরিবর্তন করার সময় যে সময়-জরিমানা হয়। মাল্টিপল স্ক্লেরোসিস গবেষণায় এটি একটি মূল এক্সিকিউটিভ ফাংশন পরিমাপক।'
					)}
				</p>
			</div>

			<!-- Block Overview -->
			<div class="card">
				<h2 class="section-title">{lt('Three-Block Structure', 'তিন-ব্লক কাঠামো')}</h2>
				<div class="block-overview">
					<div class="block-item block-item-a">
						<span class="block-badge badge-green">{lt('Block A', 'ব্লক A')}</span>
						<div class="block-op block-op-green">+3</div>
						<div class="block-label">{lt('Add 3', 'যোগ ৩')}</div>
						<div class="block-desc">{lt('Baseline: addition speed', 'বেসলাইন: যোগের গতি')}</div>
					</div>
					<div class="block-arrow">&#8594;</div>
					<div class="block-item block-item-b">
						<span class="block-badge badge-blue">{lt('Block B', 'ব্লক B')}</span>
						<div class="block-op block-op-blue">-3</div>
						<div class="block-label">{lt('Subtract 3', 'বিয়োগ ৩')}</div>
						<div class="block-desc">{lt('Baseline: subtraction speed', 'বেসলাইন: বিয়োগের গতি')}</div>
					</div>
					<div class="block-arrow">&#8594;</div>
					<div class="block-item block-item-c">
						<span class="block-badge badge-lime">{lt('Block C', 'ব্লক C')}</span>
						<div class="block-op block-op-lime">+/-</div>
						<div class="block-label">{lt('Alternating', 'পালাবদল')}</div>
						<div class="block-desc">{lt('Measures switching cost', 'স্যুইচিং কস্ট পরিমাপ')}</div>
					</div>
				</div>
			</div>

			<!-- Rules Grid -->
			<div class="card">
				<h2 class="section-title">{lt('How to Play', 'কীভাবে খেলবেন')}</h2>
				<div class="rules-grid">
					<div class="rule-item">
						<div class="rule-num">1</div>
						<div class="rule-text">
							<strong>{lt('See the number', 'সংখ্যাটি দেখুন')}</strong>
							<span>{lt('A number appears on screen in each trial.', 'প্রতিটি ট্রায়ালে স্ক্রিনে একটি সংখ্যা দেখা যাবে।')}</span>
						</div>
					</div>
					<div class="rule-item">
						<div class="rule-num">2</div>
						<div class="rule-text">
							<strong>{lt('Apply the operation', 'অপারেশন প্রয়োগ করুন')}</strong>
							<span>{lt('Add or subtract 3 as directed by the current block rule.', 'বর্তমান ব্লকের নিয়ম অনুযায়ী ৩ যোগ বা বিয়োগ করুন।')}</span>
						</div>
					</div>
					<div class="rule-item">
						<div class="rule-num">3</div>
						<div class="rule-text">
							<strong>{lt('Type your answer', 'আপনার উত্তর টাইপ করুন')}</strong>
							<span>{lt('Enter the result and press Enter or click Submit.', 'ফলাফল লিখুন এবং Enter চাপুন বা Submit বাটনে ক্লিক করুন।')}</span>
						</div>
					</div>
					<div class="rule-item">
						<div class="rule-num">4</div>
						<div class="rule-text">
							<strong>{lt('Watch the cue in Block C', 'ব্লক C-তে সংকেতে মনোযোগ দিন')}</strong>
							<span>{lt('A brief +3 or -3 cue flashes before each number. React quickly.', 'প্রতিটি সংখ্যার আগে +৩ বা -৩ সংকেত ঝলকাবে। দ্রুত সাড়া দিন।')}</span>
						</div>
					</div>
				</div>
			</div>

			<!-- Info Grid -->
			<div class="info-grid">
				<div class="card">
					<h3 class="card-title">{lt('Session Details', 'সেশনের বিবরণ')}</h3>
					<div class="details-list">
						<div class="detail-row">
							<span>{lt('Total Trials', 'মোট ট্রায়াল')}</span>
							<strong>{sessionData ? n(sessionData.total_trials) : '36'}</strong>
						</div>
						<div class="detail-row">
							<span>{lt('Blocks', 'ব্লক')}</span>
							<strong>{lt('3 (Add / Subtract / Alternating)', '৩টি (যোগ / বিয়োগ / পালাবদল)')}</strong>
						</div>
						<div class="detail-row">
							<span>{lt('Trials per Block', 'প্রতি ব্লকে ট্রায়াল')}</span>
							<strong>12</strong>
						</div>
						<div class="detail-row">
							<span>{lt('Cue Duration (Block C)', 'সংকেত সময় (ব্লক C)')}</span>
							<strong>{sessionData ? durationMsLabel(sessionData.config.cue_duration_ms) : '—'}</strong>
						</div>
						<div class="detail-row">
							<span>{lt('Difficulty', 'কঠিনতা')}</span>
							<strong>{lt(`Level ${difficulty} / 10`, `লেভেল ${n(difficulty)} / ১০`)}</strong>
						</div>
						<div class="detail-row">
							<span>{lt('Number Range', 'সংখ্যার পরিসর')}</span>
							<strong>{difficultySummary()}</strong>
						</div>
					</div>
				</div>
				<div class="card">
					<h3 class="card-title">{lt('What It Measures', 'এটি কী পরিমাপ করে')}</h3>
					<div class="details-list">
						<div class="detail-row">
							<span>{lt('Primary Metric', 'প্রাথমিক মেট্রিক')}</span>
							<strong>{lt('Switching cost (ms)', 'স্যুইচিং কস্ট (মি.সে)')}</strong>
						</div>
						<div class="detail-row">
							<span>{lt('Cognitive Domain', 'জ্ঞানীয় ডোমেইন')}</span>
							<strong>{lt('Cognitive flexibility', 'জ্ঞানীয় নমনীয়তা')}</strong>
						</div>
						<div class="detail-row">
							<span>{lt('Baseline', 'বেসলাইন')}</span>
							<strong>{lt('Blocks A + B pure speed', 'ব্লক A + B খাঁটি গতি')}</strong>
						</div>
						<div class="detail-row">
							<span>{lt('Switch Measure', 'স্যুইচ পরিমাপ')}</span>
							<strong>{lt('Block C minus baseline avg', 'ব্লক C বিয়োগ গড় বেসলাইন')}</strong>
						</div>
						<div class="detail-row">
							<span>{lt('MS Relevance', 'এমএস প্রাসঙ্গিকতা')}</span>
							<strong>{lt('Executive function marker', 'এক্সিকিউটিভ ফাংশন চিহ্নক')}</strong>
						</div>
					</div>
				</div>
			</div>

			<!-- Clinical Info -->
			<div class="clinical-info">
				<div class="clinical-header">
					<div class="clinical-badge">{lt('Clinical Basis', 'ক্লিনিকাল ভিত্তি')}</div>
					<h3>{lt('Validated Switching Paradigm', 'যাচাইকৃত স্যুইচিং প্যারাডাইম')}</h3>
				</div>
				<p>
					{lt(
						'Jersild (1927) first described task-switching costs, and Miyake et al. (2000) confirmed cognitive shifting as a separable executive function. This paradigm isolates pure switching cost with minimal working memory demands, making it ideal for assessing cognitive flexibility impairment in multiple sclerosis.',
						'জার্সিল্ড (১৯২৭) প্রথম টাস্ক-স্যুইচিং কস্টের বর্ণনা দেন, এবং মিয়াকে এবং অন্যান্য (২০০০) জ্ঞানীয় শিফটিংকে একটি আলাদা এক্সিকিউটিভ ফাংশন হিসেবে নিশ্চিত করেন। এই প্যারাডাইমটি মাল্টিপল স্ক্লেরোসিসে জ্ঞানীয় নমনীয়তার দুর্বলতা মূল্যায়নের জন্য আদর্শ।'
					)}
				</p>
			</div>

			<!-- Performance Guide -->
			<div class="card perf-guide">
				<h3 class="card-title">{lt('Switching Cost Norms', 'স্যুইচিং কস্ট নির্দেশিকা')}</h3>
				<p class="perf-subtitle">{lt('Block C RT minus average of Blocks A and B', 'ব্লক C RT বিয়োগ ব্লক A এবং B-এর গড়')}</p>
				<div class="norm-bars">
					<div class="norm-bar">
						<div class="norm-label">{lt('Excellent', 'উৎকৃষ্ট')}</div>
						<div class="norm-track"><div class="norm-fill norm-excellent"></div></div>
						<div class="norm-range">&lt; 100 ms</div>
					</div>
					<div class="norm-bar">
						<div class="norm-label">{lt('Normal', 'স্বাভাবিক')}</div>
						<div class="norm-track"><div class="norm-fill norm-normal"></div></div>
						<div class="norm-range">100–200 ms</div>
					</div>
					<div class="norm-bar">
						<div class="norm-label">{lt('Elevated', 'উচ্চ')}</div>
						<div class="norm-track"><div class="norm-fill norm-elevated"></div></div>
						<div class="norm-range">&gt; 200 ms</div>
					</div>
				</div>
			</div>

			<TaskPracticeActions
				locale={$locale}
				startLabel={t('Start Test')}
				statusMessage={practiceStatusMessage}
				on:start={() => startTask(TASK_PLAY_MODE.RECORDED)}
				on:practice={() => startTask(TASK_PLAY_MODE.PRACTICE)}
			/>

		{:else if phase === 'block-transition'}

			<!-- Block Transition -->
			<div class="transition-card">
				{#if playMode === TASK_PLAY_MODE.PRACTICE}
					<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
				{/if}

				<div class="transition-badge">
					{currentBlockIndex === 1
						? lt('Block B', 'ব্লক B')
						: lt('Block C', 'ব্লক C')}
				</div>
				<h2 class="transition-title">{blockTransitionTitle()}</h2>

				<div class="transition-rule-box">
					{#if currentBlockIndex === 1}
						<div class="op-display op-blue">-3</div>
						<p>{lt('Subtract 3 from each number. Work as fast and accurately as you can.', 'প্রতিটি সংখ্যা থেকে ৩ বিয়োগ করুন। যত দ্রুত এবং নির্ভুলভাবে পারেন কাজ করুন।')}</p>
					{:else}
						<div class="op-display op-lime">+/-</div>
						<p>{lt('A brief cue (+3 or -3) will flash before each number. Respond according to the cue shown.', 'প্রতিটি সংখ্যার আগে একটি সংকেত (+৩ বা -৩) ঝলকাবে। দেখানো সংকেত অনুযায়ী সাড়া দিন।')}</p>
					{/if}
				</div>

				<button class="continue-btn" on:click={continueToNextBlock}>
					{lt('Continue', 'চালিয়ে যান')}
				</button>
			</div>

		{:else if phase === 'task'}

			{#if currentBlock && getCurrentTrial()}
				{@const trial = getCurrentTrial()}
				{@const blockNum = currentBlockIndex + 1}
				{@const totalTrials = currentBlock.total_trials}
				{@const trialNum = currentTrialIndex + 1}

				<div class="task-container">
					{#if playMode === TASK_PLAY_MODE.PRACTICE}
						<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
					{/if}

					<!-- Status Bar -->
					<div class="status-bar">
						<div class="status-pills">
							<span class="pill pill-block">{currentBlockLabel(blockNum)}</span>
							<span class="pill pill-trial">{trialProgressLabel(trialNum, totalTrials)}</span>
						</div>
						<div class="timer-pill">
							{n(elapsedTime.toFixed(1), { minimumFractionDigits: 1, maximumFractionDigits: 1 })}s
						</div>
					</div>

					<!-- Progress Bar -->
					<div class="progress-track">
						<div class="progress-fill" style="width: {(trialNum / totalTrials) * 100}%"></div>
					</div>

					<!-- Cue Flash (Block C alternating only) -->
					{#if showCue}
						<div class="cue-flash-wrap">
							<div class="cue-box {trial.operation === 'add' ? 'cue-add' : 'cue-subtract'}">
								<span class="cue-text">{cueText}</span>
							</div>
						</div>
					{/if}

					<!-- Rule Banner (Blocks A and B only) -->
					{#if currentBlock.name !== 'alternating'}
						<div class="rule-banner">
							{#if trial.operation === 'add'}
								<span class="rule-pill rule-add">{lt('Rule: Add 3 to the number', 'নিয়ম: সংখ্যায় ৩ যোগ করুন')}</span>
							{:else}
								<span class="rule-pill rule-subtract">{lt('Rule: Subtract 3 from the number', 'নিয়ম: সংখ্যা থেকে ৩ বিয়োগ করুন')}</span>
							{/if}
						</div>
					{/if}

					<!-- Number Display -->
					<div class="number-display">
						<div class="number-card">
							<span class="number-value">{trial.number}</span>
						</div>
					</div>

					<!-- Answer Input -->
					<div class="answer-section">
						<label class="answer-label" for="answer-input">
							{lt('Your Answer', 'আপনার উত্তর')}
						</label>
						<input
							id="answer-input"
							type="number"
							bind:value={userAnswer}
							on:keypress={handleKeyPress}
							class="answer-input"
							placeholder="?"
							autofocus
						/>
						<button
							on:click={handleSubmit}
							disabled={userAnswer === ''}
							class="submit-btn"
							class:submit-disabled={userAnswer === ''}
						>
							{t('Submit')}
						</button>
					</div>
				</div>
			{/if}

		{:else if phase === 'results'}
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />

			<!-- Results Header -->
			<div class="results-header">
				<div class="score-pill">
					<span class="score-label">{lt('Score', 'স্কোর')}</span>
					<span class="score-value">{n(results.score)}</span>
				</div>
				<p class="accuracy-line">
					{lt('Overall Accuracy', 'সামগ্রিক নির্ভুলতা')}: {pct(results.accuracy)}%
				</p>
			</div>

			<!-- Per-Block Results -->
			<div class="block-results-grid">
				<div class="block-result block-result-a">
					<div class="block-result-header">{lt('Block A: Add 3', 'ব্লক A: যোগ ৩')}</div>
					<div class="block-result-metric">{pct(results.blocks.block_a.accuracy)}%</div>
					<div class="block-result-sub">{lt('Accuracy', 'নির্ভুলতা')}</div>
					<div class="block-result-metric block-result-rt">{durationMsLabel(results.blocks.block_a.mean_rt)}</div>
					<div class="block-result-sub">{lt('Avg Response Time', 'গড় প্রতিক্রিয়া সময়')}</div>
				</div>
				<div class="block-result block-result-b">
					<div class="block-result-header">{lt('Block B: Subtract 3', 'ব্লক B: বিয়োগ ৩')}</div>
					<div class="block-result-metric">{pct(results.blocks.block_b.accuracy)}%</div>
					<div class="block-result-sub">{lt('Accuracy', 'নির্ভুলতা')}</div>
					<div class="block-result-metric block-result-rt">{durationMsLabel(results.blocks.block_b.mean_rt)}</div>
					<div class="block-result-sub">{lt('Avg Response Time', 'গড় প্রতিক্রিয়া সময়')}</div>
				</div>
				<div class="block-result block-result-c">
					<div class="block-result-header">{lt('Block C: Alternating', 'ব্লক C: পালাবদল')}</div>
					<div class="block-result-metric">{pct(results.blocks.block_c.accuracy)}%</div>
					<div class="block-result-sub">{lt('Accuracy', 'নির্ভুলতা')}</div>
					<div class="block-result-metric block-result-rt">{durationMsLabel(results.blocks.block_c.mean_rt)}</div>
					<div class="block-result-sub">{lt('Avg Response Time', 'গড় প্রতিক্রিয়া সময়')}</div>
				</div>
			</div>

			<!-- Switching Cost Analysis -->
			<div class="card switching-cost-card">
				<h3 class="card-title">{lt('Switching Cost Analysis', 'স্যুইচিং কস্ট বিশ্লেষণ')}</h3>
				<div class="cost-grid">
					<div class="cost-item">
						<div class="cost-label">{lt('Reaction Time Cost', 'প্রতিক্রিয়া সময় কস্ট')}</div>
						<div class="cost-value {results.switching_cost > 200 ? 'cost-elevated' : results.switching_cost > 100 ? 'cost-normal' : 'cost-excellent'}">
							{signedDurationLabel(results.switching_cost)}
						</div>
						<div class="cost-desc">{lt('Time penalty when switching operations', 'অপারেশন পরিবর্তনের সময় জরিমানা')}</div>
					</div>
					<div class="cost-item">
						<div class="cost-label">{lt('Accuracy Cost', 'নির্ভুলতা কস্ট')}</div>
						<div class="cost-value {results.switching_cost_accuracy > 0.1 ? 'cost-elevated' : results.switching_cost_accuracy > 0.05 ? 'cost-normal' : 'cost-excellent'}">
							{results.switching_cost_accuracy >= 0 ? '+' : ''}{pct(results.switching_cost_accuracy)}%
						</div>
						<div class="cost-desc">{lt('Accuracy drop in alternating block', 'পালাবদল ব্লকে নির্ভুলতা হ্রাস')}</div>
					</div>
				</div>
				<div class="cost-interpretation">
					<p>
						{lt(
							'Lower switching cost indicates better cognitive flexibility. A cost near zero means you alternate operations with minimal effort.',
							'কম স্যুইচিং কস্ট মানে ভালো জ্ঞানীয় নমনীয়তা। শূন্যের কাছাকাছি কস্ট মানে আপনি সহজেই অপারেশন পরিবর্তন করতে পারেন।'
						)}
					</p>
				</div>
			</div>

			<!-- Action Buttons -->
			<div class="action-buttons">
				<button class="start-button" on:click={() => goto('/dashboard')}>
					{lt('Return to Dashboard', 'ড্যাশবোর্ডে ফিরুন')}
				</button>
				<button class="btn-secondary" on:click={() => goto('/dashboard')}>
					{lt('Next Task', 'পরবর্তী টাস্ক')}
				</button>
			</div>

		{/if}
	</div>

	{#if phase === 'intro'}
		<button class="help-fab" on:click={() => {}}>?</button>
	{/if}
</div>

{#if newBadges && newBadges.length > 0}
	<BadgeNotification badges={newBadges} />
{/if}

<style>
	/* ── Page Layout ─────────────────────────────────── */
	.pm-page {
		min-height: 100vh;
		background: #C8DEFA;
		padding: 1.5rem;
	}

	.pm-wrapper {
		max-width: 960px;
		margin: 0 auto;
	}

	/* ── Shared Card ──────────────────────────────────── */
	.card {
		background: white;
		border-radius: 16px;
		padding: 1.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
		margin-bottom: 1rem;
	}

	/* ── Error ────────────────────────────────────────── */
	.error-card {
		background: white;
		border: 2px solid #fca5a5;
		border-radius: 16px;
		padding: 1.5rem;
	}

	.error-card p {
		color: #dc2626;
		margin-bottom: 0.75rem;
	}

	.retry-btn {
		padding: 0.5rem 1.25rem;
		background: #dc2626;
		color: white;
		border: none;
		border-radius: 8px;
		font-size: 0.875rem;
		font-weight: 600;
		cursor: pointer;
	}

	/* ── Header Card ─────────────────────────────────── */
	.header-card {
		background: white;
		border-radius: 16px;
		padding: 1.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
		margin-bottom: 1rem;
	}

	.header-content {
		display: flex;
		align-items: center;
		justify-content: space-between;
		flex-wrap: wrap;
		gap: 1rem;
	}

	.task-title {
		font-size: 1.75rem;
		font-weight: 700;
		color: #1a1a2e;
		margin: 0 0 0.25rem 0;
	}

	.task-domain {
		font-size: 0.875rem;
		color: #65a30d;
		font-weight: 500;
		margin: 0;
	}

	/* ── Task Concept ─────────────────────────────────── */
	.concept-badge {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		background: linear-gradient(135deg, #65a30d 0%, #84cc16 100%);
		color: white;
		padding: 0.4rem 0.9rem;
		border-radius: 2rem;
		font-size: 0.813rem;
		font-weight: 600;
		margin-bottom: 1rem;
	}

	.badge-icon {
		font-size: 0.875rem;
		font-weight: 700;
		font-family: monospace;
	}

	.concept-desc {
		color: #4b5563;
		font-size: 0.938rem;
		line-height: 1.6;
		margin: 0;
	}

	/* ── Section Title ────────────────────────────────── */
	.section-title {
		font-size: 1.125rem;
		font-weight: 600;
		color: #1a1a2e;
		margin: 0 0 1.25rem 0;
	}

	/* ── Block Overview ───────────────────────────────── */
	.block-overview {
		display: flex;
		align-items: stretch;
		gap: 0;
	}

	.block-item {
		flex: 1;
		background: #f9fafb;
		border-radius: 12px;
		padding: 1.25rem;
		text-align: center;
	}

	.block-item-a { border-top: 4px solid #16a34a; }
	.block-item-b { border-top: 4px solid #2563eb; }
	.block-item-c { border-top: 4px solid #65a30d; }

	.block-badge {
		display: inline-block;
		padding: 0.2rem 0.7rem;
		border-radius: 1rem;
		font-size: 0.75rem;
		font-weight: 600;
		margin-bottom: 0.75rem;
	}

	.badge-green { background: #dcfce7; color: #166534; }
	.badge-blue  { background: #dbeafe; color: #1e40af; }
	.badge-lime  { background: #ecfccb; color: #365314; }

	.block-op {
		font-size: 2rem;
		font-weight: 700;
		font-family: monospace;
		margin: 0.5rem 0;
	}

	.block-op-green { color: #16a34a; }
	.block-op-blue  { color: #2563eb; }
	.block-op-lime  { color: #65a30d; }

	.block-label {
		font-size: 0.875rem;
		font-weight: 600;
		color: #374151;
		margin-bottom: 0.25rem;
	}

	.block-desc {
		font-size: 0.75rem;
		color: #6b7280;
	}

	.block-arrow {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0 0.75rem;
		font-size: 1.25rem;
		color: #9ca3af;
		font-weight: 700;
	}

	/* ── Rules Grid ───────────────────────────────────── */
	.rules-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}

	.rule-item {
		display: flex;
		align-items: flex-start;
		gap: 0.875rem;
		background: #f9fafb;
		border-radius: 12px;
		padding: 1rem;
	}

	.rule-num {
		min-width: 2rem;
		height: 2rem;
		background: linear-gradient(135deg, #65a30d 0%, #84cc16 100%);
		color: white;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.875rem;
		font-weight: 700;
		flex-shrink: 0;
	}

	.rule-text {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.rule-text strong {
		font-size: 0.875rem;
		color: #1a1a2e;
	}

	.rule-text span {
		font-size: 0.8rem;
		color: #6b7280;
		line-height: 1.4;
	}

	/* ── Info Grid ────────────────────────────────────── */
	.info-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
		margin-bottom: 1rem;
	}

	.card-title {
		font-size: 1rem;
		font-weight: 600;
		color: #1a1a2e;
		margin: 0 0 1rem 0;
	}

	.details-list {
		display: flex;
		flex-direction: column;
		gap: 0.625rem;
	}

	.detail-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		font-size: 0.875rem;
		padding-bottom: 0.625rem;
		border-bottom: 1px solid #f3f4f6;
	}

	.detail-row:last-child {
		border-bottom: none;
		padding-bottom: 0;
	}

	.detail-row span { color: #6b7280; }
	.detail-row strong { color: #1a1a2e; text-align: right; max-width: 60%; }

	/* ── Clinical Info ────────────────────────────────── */
	.clinical-info {
		background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
		border: 1px solid #bbf7d0;
		border-radius: 16px;
		padding: 1.5rem;
		margin-bottom: 1rem;
	}

	.clinical-header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 0.75rem;
	}

	.clinical-badge {
		background: #16a34a;
		color: white;
		padding: 0.2rem 0.7rem;
		border-radius: 1rem;
		font-size: 0.75rem;
		font-weight: 600;
	}

	.clinical-header h3 {
		font-size: 1rem;
		font-weight: 600;
		color: #14532d;
		margin: 0;
	}

	.clinical-info p {
		font-size: 0.875rem;
		color: #166534;
		line-height: 1.6;
		margin: 0;
	}

	/* ── Performance Guide ────────────────────────────── */
	.perf-subtitle {
		font-size: 0.813rem;
		color: #6b7280;
		margin: -0.5rem 0 1rem 0;
	}

	.norm-bars {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.norm-bar {
		display: grid;
		grid-template-columns: 6rem 1fr 6rem;
		align-items: center;
		gap: 0.75rem;
	}

	.norm-label {
		font-size: 0.875rem;
		font-weight: 500;
		color: #374151;
	}

	.norm-track {
		height: 0.5rem;
		background: #f3f4f6;
		border-radius: 0.25rem;
		overflow: hidden;
	}

	.norm-fill { height: 100%; border-radius: 0.25rem; }
	.norm-excellent { width: 30%; background: #16a34a; }
	.norm-normal    { width: 60%; background: #f59e0b; }
	.norm-elevated  { width: 90%; background: #dc2626; }

	.norm-range {
		font-size: 0.75rem;
		color: #6b7280;
		text-align: right;
	}

	/* ── Block Transition ─────────────────────────────── */
	.transition-card {
		background: white;
		border-radius: 16px;
		padding: 2rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
		text-align: center;
		max-width: 600px;
		margin: 0 auto;
	}

	.transition-badge {
		display: inline-block;
		background: linear-gradient(135deg, #65a30d 0%, #84cc16 100%);
		color: white;
		padding: 0.4rem 1.25rem;
		border-radius: 2rem;
		font-size: 0.875rem;
		font-weight: 700;
		margin-bottom: 1rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.transition-title {
		font-size: 1.5rem;
		font-weight: 700;
		color: #1a1a2e;
		margin: 0 0 1.25rem 0;
	}

	.transition-rule-box {
		background: #f7fee7;
		border: 2px solid #a3e635;
		border-radius: 12px;
		padding: 1.25rem;
		margin-bottom: 1.5rem;
	}

	.op-display {
		font-size: 2.5rem;
		font-weight: 700;
		font-family: monospace;
		margin-bottom: 0.5rem;
	}

	.op-blue { color: #2563eb; }
	.op-lime { color: #65a30d; }

	.transition-rule-box p {
		color: #365314;
		font-size: 0.938rem;
		margin: 0;
		line-height: 1.5;
	}

	.continue-btn {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		border-radius: 12px;
		padding: 0.875rem 2.5rem;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
		transition: transform 0.15s;
	}

	.continue-btn:hover { transform: translateY(-2px); }

	/* ── Task Phase ───────────────────────────────────── */
	.task-container {
		background: white;
		border-radius: 16px;
		padding: 1.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
	}

	.status-bar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 0.75rem;
		flex-wrap: wrap;
		gap: 0.5rem;
	}

	.status-pills {
		display: flex;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.pill {
		padding: 0.3rem 0.75rem;
		border-radius: 2rem;
		font-size: 0.8rem;
		font-weight: 500;
	}

	.pill-block { background: #ecfccb; color: #365314; }
	.pill-trial { background: #f3f4f6; color: #374151; }

	.timer-pill {
		background: linear-gradient(135deg, #65a30d 0%, #84cc16 100%);
		color: white;
		padding: 0.375rem 1rem;
		border-radius: 2rem;
		font-size: 0.875rem;
		font-weight: 700;
		min-width: 4rem;
		text-align: center;
	}

	.progress-track {
		height: 6px;
		background: #e5e7eb;
		border-radius: 3px;
		overflow: hidden;
		margin-bottom: 1.5rem;
	}

	.progress-fill {
		height: 100%;
		background: linear-gradient(90deg, #65a30d 0%, #84cc16 100%);
		border-radius: 3px;
		transition: width 0.3s ease;
	}

	/* ── Cue Flash ────────────────────────────────────── */
	.cue-flash-wrap {
		display: flex;
		justify-content: center;
		margin-bottom: 1rem;
	}

	.cue-box {
		padding: 0.75rem 2.5rem;
		border-radius: 12px;
		border: 3px solid;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		animation: cue-pulse 0.4s ease-in-out;
	}

	.cue-add      { border-color: #16a34a; background: #f0fdf4; }
	.cue-subtract { border-color: #2563eb; background: #eff6ff; }

	.cue-text {
		font-size: 2rem;
		font-weight: 700;
		font-family: monospace;
	}

	.cue-add .cue-text      { color: #16a34a; }
	.cue-subtract .cue-text { color: #2563eb; }

	/* ── Rule Banner ──────────────────────────────────── */
	.rule-banner {
		display: flex;
		justify-content: center;
		margin-bottom: 1rem;
	}

	.rule-pill {
		padding: 0.375rem 1.25rem;
		border-radius: 2rem;
		font-size: 0.875rem;
		font-weight: 600;
	}

	.rule-add      { background: #dcfce7; color: #166534; }
	.rule-subtract { background: #dbeafe; color: #1e40af; }

	/* ── Number Display ───────────────────────────────── */
	.number-display {
		display: flex;
		justify-content: center;
		margin: 1.5rem 0;
	}

	.number-card {
		background: white;
		border: 3px solid #a3e635;
		border-radius: 20px;
		padding: 2rem 3.5rem;
		box-shadow: 0 8px 24px rgba(101, 163, 13, 0.15);
		min-width: 200px;
		text-align: center;
	}

	.number-value {
		font-size: 4.5rem;
		font-weight: 700;
		color: #1a1a2e;
		font-family: monospace;
		line-height: 1;
	}

	/* ── Answer Section ───────────────────────────────── */
	.answer-section {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.75rem;
		margin-top: 1rem;
	}

	.answer-label {
		font-size: 0.875rem;
		font-weight: 500;
		color: #6b7280;
	}

	.answer-input {
		font-size: 2rem;
		font-weight: 600;
		text-align: center;
		width: 200px;
		padding: 0.75rem;
		border: 3px solid #a3e635;
		border-radius: 12px;
		font-family: monospace;
		color: #1a1a2e;
		outline: none;
		transition: border-color 0.2s, box-shadow 0.2s;
		-moz-appearance: textfield;
	}

	.answer-input:focus {
		border-color: #65a30d;
		box-shadow: 0 0 0 4px rgba(101, 163, 13, 0.15);
	}

	.answer-input::-webkit-inner-spin-button,
	.answer-input::-webkit-outer-spin-button {
		-webkit-appearance: none;
		margin: 0;
	}

	.submit-btn {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		border-radius: 12px;
		padding: 0.875rem 2.5rem;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
		transition: transform 0.15s, opacity 0.15s;
	}

	.submit-btn:hover:not(:disabled) { transform: translateY(-2px); }

	.submit-disabled {
		background: #d1d5db !important;
		box-shadow: none !important;
		cursor: not-allowed !important;
		transform: none !important;
	}

	/* ── Results ──────────────────────────────────────── */
	.results-header {
		background: linear-gradient(135deg, #65a30d 0%, #84cc16 100%);
		border-radius: 16px;
		padding: 1.75rem;
		text-align: center;
		margin-bottom: 1rem;
		box-shadow: 0 4px 12px rgba(101, 163, 13, 0.3);
	}

	.score-pill {
		display: flex;
		align-items: baseline;
		justify-content: center;
		gap: 0.5rem;
		margin-bottom: 0.5rem;
	}

	.score-label { color: rgba(255, 255, 255, 0.85); font-size: 1rem; font-weight: 500; }
	.score-value { color: white; font-size: 3rem; font-weight: 700; }

	.accuracy-line {
		color: rgba(255, 255, 255, 0.9);
		font-size: 0.938rem;
		margin: 0;
	}

	.block-results-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 1rem;
		margin-bottom: 1rem;
	}

	.block-result {
		background: white;
		border-radius: 16px;
		padding: 1.25rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
		text-align: center;
	}

	.block-result-a { border-top: 4px solid #16a34a; }
	.block-result-b { border-top: 4px solid #2563eb; }
	.block-result-c { border-top: 4px solid #65a30d; }

	.block-result-header {
		font-size: 0.813rem;
		font-weight: 600;
		color: #374151;
		margin-bottom: 0.75rem;
	}

	.block-result-metric {
		font-size: 1.5rem;
		font-weight: 700;
		color: #1a1a2e;
	}

	.block-result-rt {
		font-size: 1.125rem;
		margin-top: 0.5rem;
	}

	.block-result-sub {
		font-size: 0.75rem;
		color: #6b7280;
		margin-bottom: 0.25rem;
	}

	/* ── Switching Cost ───────────────────────────────── */
	.cost-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.5rem;
		margin-bottom: 1rem;
	}

	.cost-item { text-align: center; }

	.cost-label {
		font-size: 0.875rem;
		color: #6b7280;
		margin-bottom: 0.5rem;
	}

	.cost-value {
		font-size: 2rem;
		font-weight: 700;
		margin-bottom: 0.25rem;
	}

	.cost-excellent { color: #16a34a; }
	.cost-normal    { color: #f59e0b; }
	.cost-elevated  { color: #dc2626; }

	.cost-desc {
		font-size: 0.75rem;
		color: #9ca3af;
	}

	.cost-interpretation {
		background: #f0fdf4;
		border-left: 4px solid #16a34a;
		border-radius: 0 8px 8px 0;
		padding: 0.875rem 1rem;
	}

	.cost-interpretation p {
		font-size: 0.875rem;
		color: #166534;
		margin: 0;
		line-height: 1.5;
	}

	/* ── Action Buttons ───────────────────────────────── */
	.action-buttons {
		display: flex;
		gap: 1rem;
		margin-top: 1rem;
	}

	.start-button {
		flex: 1;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		border-radius: 12px;
		padding: 1rem;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
		transition: transform 0.15s;
	}

	.start-button:hover { transform: translateY(-2px); }

	.btn-secondary {
		flex: 1;
		background: white;
		color: #667eea;
		border: 2px solid #667eea;
		border-radius: 12px;
		padding: 1rem;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: transform 0.15s, background 0.15s;
	}

	.btn-secondary:hover { background: #f5f3ff; transform: translateY(-2px); }

	/* ── Help FAB ─────────────────────────────────────── */
	.help-fab {
		position: fixed;
		bottom: 2rem;
		right: 2rem;
		width: 3rem;
		height: 3rem;
		background: linear-gradient(135deg, #65a30d 0%, #84cc16 100%);
		color: white;
		border: none;
		border-radius: 50%;
		font-size: 1.25rem;
		font-weight: 700;
		cursor: pointer;
		box-shadow: 0 4px 12px rgba(101, 163, 13, 0.4);
		display: flex;
		align-items: center;
		justify-content: center;
	}

	/* ── Animations ───────────────────────────────────── */
	@keyframes cue-pulse {
		0%, 100% { transform: scale(1); }
		50%       { transform: scale(1.06); }
	}

	/* ── Responsive ───────────────────────────────────── */
	@media (max-width: 640px) {
		.rules-grid         { grid-template-columns: 1fr; }
		.info-grid          { grid-template-columns: 1fr; }
		.block-results-grid { grid-template-columns: 1fr; }
		.cost-grid          { grid-template-columns: 1fr; }
		.block-overview     { flex-direction: column; }
		.block-arrow        { transform: rotate(90deg); }
		.action-buttons     { flex-direction: column; }
	}
</style>


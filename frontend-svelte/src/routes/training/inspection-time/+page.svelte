<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
import TaskReturnButton from '$lib/components/TaskReturnButton.svelte';
	import { formatNumber, locale, localeText } from '$lib/i18n';
	import { user } from '$lib/stores.js';
	import { getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
import { TASK_RETURN_CONTEXT } from '$lib/task-navigation';
	import { onDestroy, onMount } from 'svelte';

	import { API_BASE_URL } from '$lib/api';

	function n(value, options = {}) {
		return formatNumber(value, $locale, options);
	}

	let currentUser = null;
	let sessionData = null;
	let currentTrialIndex = 0;
	let currentTrial = null;
	let responses = [];
	let taskId = null;
	
	// UI states
	let showInstructions = true;
	let showPractice = false;
	let practiceComplete = false;
	let testStarted = false;
	let showStimulus = false;
	let showMask = false;
	let waitingForResponse = false;
	let showResults = false;
	let error = null;
	let loading = false;
	
	// Practice trial data
	let practiceTrial = null;
	let practiceAttempts = 0;
	
	// Timing
	let stimulusStartTime = 0;
	let maskStartTime = 0;
	
	// Results
	let results = null;
	
	// Help modal
	let showHelp = false;
	/** @type {"practice" | "recorded"} */
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';
	let practiceAdvanceTimeout = null;
	let practiceRunId = 0;
	const lt = (en, bn) => localeText({ en, bn }, $locale);

	// Subscribe to user store
	user.subscribe(value => {
		currentUser = value;
	});

	onMount(async () => {
		if (!currentUser) {
			goto('/login');
			return;
		}
		
		await loadSession();
	});

	async function loadSession() {
		try {
			loading = true;
			error = null;
			
			const response = await fetch(`${API_BASE_URL}/api/training/tasks/inspection-time/generate/${currentUser.id}`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				}
			});
			
			if (!response.ok) {
				throw new Error('Failed to load session');
			}
			
			const data = await response.json();
			sessionData = data.session_data;
			
		} catch (err) {
			error = err.message;
		} finally {
			loading = false;
		}
	}

	function startPractice() {
		practiceRunId += 1;
		clearTimeout(practiceAdvanceTimeout);
		/** @type {"practice" | "recorded"} */
		const practiceMode = TASK_PLAY_MODE.PRACTICE;
		playMode = practiceMode;
		practiceStatusMessage = '';
		showInstructions = false;
		showPractice = true;
		
		// Generate a practice trial (easy settings)
		practiceTrial = {
			left_height: 180,
			right_height: 150,
			longer_side: "left",
			presentation_time_ms: 300,  // Extra long for practice
			line_width: 8
		};
		
		practiceAttempts = 0;
	}

	function finishPractice(completed = true) {
		practiceRunId += 1;
		clearTimeout(practiceAdvanceTimeout);
		playMode = TASK_PLAY_MODE.RECORDED;
		showStimulus = false;
		showMask = false;
		waitingForResponse = false;
		showPractice = false;
		practiceComplete = false;
		showInstructions = true;
		practiceStatusMessage = completed ? getPracticeCopy($locale).complete : '';
	}

	async function runPracticeTrial() {
		const runId = practiceRunId;
		showStimulus = true;
		
		// Show stimulus for practice duration
		await sleep(practiceTrial.presentation_time_ms);
		if (runId !== practiceRunId) return;
		
		showStimulus = false;
		showMask = true;
		
		// Show mask briefly
		await sleep(500);
		if (runId !== practiceRunId) return;
		
		showMask = false;
		waitingForResponse = true;
	}

	function handlePracticeResponse(answer) {
		waitingForResponse = false;
		practiceAttempts++;
		
		if (answer === practiceTrial.longer_side) {
			// Correct! Move on
			if (practiceAttempts >= 2) {
				finishPractice();
			} else {
				// One more practice
				const runId = practiceRunId;
				clearTimeout(practiceAdvanceTimeout);
				practiceAdvanceTimeout = setTimeout(() => {
					practiceAdvanceTimeout = null;
					if (runId === practiceRunId) runPracticeTrial();
				}, 1500);
			}
		} else {
			// Wrong, explain and try again
			alert(`The ${practiceTrial.longer_side} line was longer. Let's try again!`);
			const runId = practiceRunId;
			clearTimeout(practiceAdvanceTimeout);
			practiceAdvanceTimeout = setTimeout(() => {
				practiceAdvanceTimeout = null;
				if (runId === practiceRunId) runPracticeTrial();
			}, 2000);
		}
	}

	function startTest() {
		practiceRunId += 1;
		clearTimeout(practiceAdvanceTimeout);
		playMode = TASK_PLAY_MODE.RECORDED;
		practiceStatusMessage = '';
		showPractice = false;
		practiceComplete = false;
		testStarted = true;
		currentTrialIndex = 0;
		responses = [];
		
		nextTrial();
	}

	async function nextTrial() {
		if (currentTrialIndex >= sessionData.total_trials) {
			await submitResults();
			return;
		}
		
		currentTrial = sessionData.trials[currentTrialIndex];
		
		// Brief pause before trial
		await sleep(800);
		
		// Show fixation cross
		// (can add UI element if desired)
		await sleep(500);
		
		// Show stimulus
		showStimulus = true;
		stimulusStartTime = performance.now();
		
		await sleep(currentTrial.presentation_time_ms);
		
		// Hide stimulus, show mask
		showStimulus = false;
		showMask = true;
		maskStartTime = performance.now();
		
		await sleep(sessionData.config.mask_duration_ms || 500);
		
		// Hide mask, wait for response
		showMask = false;
		waitingForResponse = true;
	}

	onDestroy(() => {
		practiceRunId += 1;
		clearTimeout(practiceAdvanceTimeout);
	});

	function handleResponse(answer) {
		if (!waitingForResponse) return;
		
		const reactionTime = performance.now() - maskStartTime;
		
		responses.push({
			trial_index: currentTrialIndex,
			user_answer: answer,
			reaction_time: reactionTime,
			presentation_time: currentTrial.presentation_time_ms
		});
		
		waitingForResponse = false;
		currentTrialIndex++;
		
		nextTrial();
	}

	async function submitResults() {
		try {
			loading = true;
			testStarted = false;
			taskId = $page.url.searchParams.get('taskId');
			
			const response = await fetch(`${API_BASE_URL}/api/training/tasks/inspection-time/submit/${currentUser.id}`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					difficulty: sessionData.difficulty,
					session_data: sessionData,
					responses: responses,
					task_id: taskId
				})
			});
			
			if (!response.ok) {
				throw new Error('Failed to submit results');
			}
			
			results = await response.json();
			showResults = true;
			
		} catch (err) {
			error = err.message;
		} finally {
			loading = false;
		}
	}

	function sleep(ms) {
		return new Promise(resolve => setTimeout(resolve, ms));
	}

	function returnToDashboard() {
		goto('/dashboard');
	}

	// Reactive calculations
	$: trialsRemaining = sessionData ? sessionData.total_trials - currentTrialIndex : 0;
	$: progressPercent = sessionData ? (currentTrialIndex / sessionData.total_trials * 100) : 0;
</script>

<div class="it-container" data-localize-skip>
	<div class="it-inner">
		{#if loading}
			<LoadingSkeleton variant="card" count={3} />

		{:else if error}
			<div class="screen-card error-screen">
				<h2>{lt('Error', 'ত্রুটি')}</h2>
				<p>{error}</p>
				<button class="start-button" on:click={returnToDashboard}>{lt('Return to Dashboard', 'ড্যাশবোর্ডে ফিরে যান')}</button>
			</div>

		{:else if showInstructions}
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />
			<div class="instructions-card">
				<div class="header-content">
					<div class="title-row">
						<h1>{lt('Inspection Time', 'ইন্সপেকশন টাইম')}</h1>
						<DifficultyBadge difficulty={sessionData?.difficulty || 5} domain="Processing Speed" />
					</div>
					<p class="subtitle">{lt('How fast can your brain perceive a brief visual flash?', 'আপনার মস্তিষ্ক অতি অল্প সময়ের দৃশ্য কত দ্রুত ধরতে পারে?')}</p>
					<div class="classic-badge">{lt('Inspection Time · Vickers & Smith (1986) · Pure Perceptual Speed', 'ইন্সপেকশন টাইম · Vickers & Smith (১৯৮৬) · বিশুদ্ধ উপলব্ধির গতি')}</div>
				</div>

				{#if practiceStatusMessage}
					<div class="practice-note">{practiceStatusMessage}</div>
				{/if}

				<div class="task-concept">
					<h3>{lt('The Challenge', 'চ্যালেঞ্জ')}</h3>
					<p>{lt('Two vertical lines flash on screen for a', 'স্ক্রিনে দুটি উল্লম্ব রেখা')} <strong>{lt('fraction of a second', 'সেকেন্ডের ভগ্নাংশ সময়ের জন্য')}</strong> {lt('then a mask covers them. Your job: say which line was', 'দেখা যাবে, তারপর একটি মাস্ক সেগুলো ঢেকে দেবে। আপনার কাজ: কোন রেখাটি')} <strong>{lt('longer', 'লম্বা')}</strong> {lt('(left or right). No motor tricks — pure perception.', '(বাম নাকি ডান) বলা। মোটর দক্ষতার বিষয় নয় — শুধু উপলব্ধি।')}</p>
					<div class="demo-lines">
						<div class="demo-line-col">
							<div class="demo-line" style="height: 64px;"></div>
							<span class="demo-line-label">{lt('LEFT', 'বাম')}</span>
						</div>
						<div class="demo-vs">{lt('vs', 'বনাম')}</div>
						<div class="demo-line-col">
							<div class="demo-line" style="height: 48px;"></div>
							<span class="demo-line-label">{lt('RIGHT', 'ডান')}</span>
						</div>
					</div>
					<div class="demo-answer-row">
						<span class="demo-ans-same">← LEFT is longer</span>
					</div>
				</div>

				<div class="rules-grid">
					<div class="rule-card">
						<span class="rule-icon">{lt('Look', 'দেখুন')}</span>
						<div class="rule-text">
							<strong>{lt('Step 1: Watch', 'ধাপ ১: দেখুন')}</strong>
							<span>{lt('Two lines flash very briefly — as short as 50ms', 'দুটি রেখা খুব অল্প সময়ের জন্য দেখা যাবে — ৫০ মি.সে. পর্যন্ত কম হতে পারে')}</span>
						</div>
					</div>
					<div class="rule-card">
						<span class="rule-icon">▣</span>
						<div class="rule-text">
							<strong>{lt('Step 2: Mask', 'ধাপ ২: মাস্ক')}</strong>
							<span>{lt('A pattern mask immediately covers the lines', 'একটি প্যাটার্ন মাস্ক সঙ্গে সঙ্গে রেখাগুলো ঢেকে দেবে')}</span>
						</div>
					</div>
					<div class="rule-card">
						<span class="rule-icon">↔</span>
						<div class="rule-text">
							<strong>{lt('Step 3: Decide', 'ধাপ ৩: সিদ্ধান্ত নিন')}</strong>
							<span>{lt('Which line was longer — LEFT or RIGHT?', 'কোন রেখাটি লম্বা ছিল — বাম নাকি ডান?')}</span>
						</div>
					</div>
					<div class="rule-card">
						<span class="rule-icon">↺</span>
						<div class="rule-text">
							<strong>{lt('Step 4: Repeat', 'ধাপ ৪: চালিয়ে যান')}</strong>
							<span>{lt('Keep going for all', 'মোট')} {n(sessionData?.total_trials || 20)} {lt('trials', 'ট্রায়াল শেষ করুন')}</span>
						</div>
					</div>
				</div>

				<div class="info-grid">
					<div class="info-section">
						<h4>{lt('Perception Tips', 'উপলব্ধির পরামর্শ')}</h4>
						<ul class="tips-list">
							<li><strong>{lt('Stay relaxed:', 'শান্ত থাকুন:')}</strong> {lt('Tension reduces perceptual sensitivity', 'টেনশন উপলব্ধির সংবেদনশীলতা কমাতে পারে')}</li>
							<li><strong>{lt('Central focus:', 'মাঝখানে মনোযোগ:')}</strong> {lt('Keep eyes on the screen centre before each trial', 'প্রতিটি ট্রায়ালের আগে স্ক্রিনের মাঝখানে চোখ রাখুন')}</li>
							<li><strong>{lt('Trust instincts:', 'প্রথম ধারণাকে বিশ্বাস করুন:')}</strong> {lt("Go with your first impression — don't overthink", 'প্রথমে যা মনে হয় সেটিই বেছে নিন — অতিরিক্ত ভাববেন না')}</li>
							<li><strong>{lt("It's OK to guess:", 'অনুমান করাও ঠিক আছে:')}</strong> {lt('Some trials are genuinely at your threshold', 'কিছু ট্রায়াল সত্যিই আপনার উপলব্ধির সীমার কাছাকাছি থাকবে')}</li>
						</ul>
					</div>
					<div class="info-section">
						<h4>{lt('Test Format', 'টেস্টের ধরন')}</h4>
						<ul class="structure-list">
							<li><span class="struct-key">{lt('Trials', 'ট্রায়াল')}</span><span class="struct-val">{n(sessionData?.total_trials || 20)}</span></li>
							<li><span class="struct-key">{lt('Flash duration', 'ফ্ল্যাশের সময়')}</span><span class="struct-val">{n(sessionData?.config?.presentation_time_ms || 100)}{lt('ms', 'মি.সে.')}</span></li>
							<li><span class="struct-key">{lt('Mask duration', 'মাস্কের সময়')}</span><span class="struct-val">{n(sessionData?.config?.mask_duration_ms || 500)}{lt('ms', 'মি.সে.')}</span></li>
							<li><span class="struct-key">{lt('Measures', 'যা মাপে')}</span><span class="struct-val">{lt('perceptual speed', 'উপলব্ধির গতি')}</span></li>
						</ul>
					</div>
				</div>

				<div class="clinical-info">
					<h4>{lt('Clinical Significance', 'ক্লিনিক্যাল গুরুত্ব')}</h4>
					<div class="clinical-grid">
						<div class="clinical-item">
							<strong>{lt('Pure Perception', 'বিশুদ্ধ উপলব্ধি')}</strong>
							<span>{lt('Measures basic visual processing speed — no motor component', 'মোটর অংশ ছাড়া মৌলিক ভিজ্যুয়াল প্রসেসিং স্পিড মাপে')}</span>
						</div>
						<div class="clinical-item">
							<strong>{lt('MS Sensitive', 'MS-সংবেদনশীল')}</strong>
							<span>{lt('Processing speed is one of the most affected domains in MS', 'MS-এ প্রসেসিং স্পিড সবচেয়ে বেশি প্রভাবিত ক্ষেত্রগুলোর একটি')}</span>
						</div>
						<div class="clinical-item">
							<strong>{lt('No Motor Bias', 'মোটর পক্ষপাত নেই')}</strong>
							<span>{lt("Physical limitations don't affect this measure", 'শারীরিক সীমাবদ্ধতা এই মাপে প্রভাব ফেলে না')}</span>
						</div>
						<div class="clinical-item">
							<strong>{lt('Research Backed', 'গবেষণাসমর্থিত')}</strong>
							<span>{lt('Vickers & Smith (1986), widely used in neuropsychology', 'Vickers & Smith (১৯৮৬), নিউরোসাইকোলজিতে বহুল ব্যবহৃত')}</span>
						</div>
					</div>
				</div>

				<div class="perf-guide">
					<h4>{lt('Performance Targets', 'পারফরম্যান্স লক্ষ্য')}</h4>
					<div class="norm-bars">
						<div class="norm-bar norm-excellent">
							<span class="norm-label">{lt('Excellent', 'চমৎকার')}</span>
							<span class="norm-val">{lt('≥90% accuracy', '≥৯০% নির্ভুলতা')}</span>
						</div>
						<div class="norm-bar norm-good">
							<span class="norm-label">{lt('Good', 'ভালো')}</span>
							<span class="norm-val">{lt('75–89% accuracy', '৭৫–৮৯% নির্ভুলতা')}</span>
						</div>
						<div class="norm-bar norm-avg">
							<span class="norm-label">{lt('Average', 'গড়')}</span>
							<span class="norm-val">{lt('60–74% accuracy', '৬০–৭৪% নির্ভুলতা')}</span>
						</div>
						<div class="norm-bar norm-fair">
							<span class="norm-label">{lt('Fair', 'মাঝারি')}</span>
							<span class="norm-val">{lt('50–59% accuracy', '৫০–৫৯% নির্ভুলতা')}</span>
						</div>
						<div class="norm-bar norm-needs">
							<span class="norm-label">{lt('Developing', 'উন্নতির পথে')}</span>
							<span class="norm-val">{lt('<50% accuracy', '<৫০% নির্ভুলতা')}</span>
						</div>
					</div>
					<p class="norm-note">{lt('*Scores depend on presentation time — faster flash = harder task', '*স্কোর ফ্ল্যাশ দেখানোর সময়ের ওপর নির্ভর করে — দ্রুত ফ্ল্যাশ মানে কঠিন টাস্ক')}</p>
				</div>

				<div class="button-group">
					<button class="btn-secondary" on:click={startPractice}>{lt('Try Practice First', 'আগে অনুশীলন করুন')}</button>
					<TaskPracticeActions
						locale={$locale}
						startLabel={lt('Start Actual Task', 'আসল টাস্ক শুরু করুন')}
						practiceVisible={false}
						statusMessage={practiceStatusMessage}
						align="center"
						on:start={startTest}
					/>
				</div>
			</div>

		{:else if showPractice}
			<div class="screen-card practice-screen">
				<PracticeModeBanner locale={$locale} showExit on:exit={() => finishPractice(false)} />
				<h2>{lt('Practice Mode', 'অনুশীলন মোড')}</h2>
				<p class="practice-intro">{lt('Practice with a slower flash to get familiar with the task.', 'টাস্কটি বুঝে নিতে ধীর ফ্ল্যাশ দিয়ে অনুশীলন করুন।')}</p>

				<div class="practice-info-row">
					<span class="p-badge">{lt('Trial', 'ট্রায়াল')} {n(practiceAttempts + 1)}</span>
					<span class="p-badge p-speed">{lt('Flash:', 'ফ্ল্যাশ:')} {n(practiceTrial.presentation_time_ms)}{lt('ms', 'মি.সে.')} {lt('(slower than real test)', '(আসল টেস্টের চেয়ে ধীর)')}</span>
				</div>

				{#if !showStimulus && !showMask && !waitingForResponse}
					<div class="practice-ready">
						<p>{lt('Focus on the centre of the screen, then click when ready.', 'স্ক্রিনের মাঝখানে মনোযোগ দিন, প্রস্তুত হলে ক্লিক করুন।')}</p>
						<button class="start-button" on:click={runPracticeTrial}>{lt('Ready — Start Trial', 'প্রস্তুত — ট্রায়াল শুরু করুন')}</button>
					</div>
				{/if}

				{#if showStimulus}
					<div class="stimulus-area">
						<div class="lines-container">
							<div class="line" style="height: {practiceTrial.left_height}px; width: {practiceTrial.line_width}px;"></div>
							<div class="spacer"></div>
							<div class="line" style="height: {practiceTrial.right_height}px; width: {practiceTrial.line_width}px;"></div>
						</div>
					</div>
				{/if}

				{#if showMask}
					<div class="stimulus-area">
						<div class="mask-pattern">
							<div class="mask-grid">
								{#each Array(20) as _, i}
									<div class="mask-cell" style="animation-delay: {i * 20}ms;"></div>
								{/each}
							</div>
						</div>
					</div>
				{/if}

				{#if waitingForResponse}
					<div class="response-area">
						<p class="response-prompt">{lt('Which line was longer?', 'কোন রেখাটি লম্বা ছিল?')}</p>
						<div class="response-buttons">
							<button class="response-btn left-btn" on:click={() => handlePracticeResponse('left')}>
								<span class="resp-icon">←</span>
								<span class="resp-text">{lt('LEFT', 'বাম')}</span>
							</button>
							<button class="response-btn right-btn" on:click={() => handlePracticeResponse('right')}>
								<span class="resp-text">{lt('RIGHT', 'ডান')}</span>
								<span class="resp-icon">→</span>
							</button>
						</div>
					</div>
				{/if}
			</div>

		{:else if testStarted}
			<div class="screen-card testing-screen">
				<div class="test-header">
					<div class="test-badges">
						<span class="count-badge">{lt('Trial', 'ট্রায়াল')} {n(currentTrialIndex + 1)} / {n(sessionData.total_trials)}</span>
						<span class="speed-badge">{n(sessionData.config.presentation_time_ms)}{lt('ms', 'মি.সে.')} {lt('flash', 'ফ্ল্যাশ')}</span>
					</div>
					<div class="progress-track">
						<div class="progress-fill" style="width: {progressPercent}%"></div>
					</div>
					<button class="help-btn-sm" on:click={() => showHelp = true}>?</button>
				</div>

				<div class="stimulus-area">
					{#if showStimulus}
						<div class="lines-container">
							<div class="line" style="height: {currentTrial.left_height}px; width: {currentTrial.line_width}px;"></div>
							<div class="spacer"></div>
							<div class="line" style="height: {currentTrial.right_height}px; width: {currentTrial.line_width}px;"></div>
						</div>
					{:else if showMask}
						<div class="mask-pattern">
							<div class="mask-grid">
								{#each Array(20) as _, i}
									<div class="mask-cell" style="animation-delay: {i * 20}ms;"></div>
								{/each}
							</div>
						</div>
					{:else if waitingForResponse}
						<div class="response-area">
							<p class="response-prompt">{lt('Which line was longer?', 'কোন রেখাটি লম্বা ছিল?')}</p>
							<div class="response-buttons">
								<button class="response-btn left-btn" on:click={() => handleResponse('left')}>
									<span class="resp-icon">←</span>
									<span class="resp-text">{lt('LEFT', 'বাম')}</span>
								</button>
								<button class="response-btn right-btn" on:click={() => handleResponse('right')}>
									<span class="resp-text">{lt('RIGHT', 'ডান')}</span>
									<span class="resp-icon">→</span>
								</button>
							</div>
						</div>
					{:else}
						<div class="waiting-state">
							<div class="fixation-cross">+</div>
							<p>{lt('Get ready…', 'প্রস্তুত হন…')}</p>
						</div>
					{/if}
				</div>
			</div>

		{:else if showResults}
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />
			<div class="screen-card complete-screen">
				{#if results}
					<div class="perf-banner">
												<div class="perf-level">{results.metrics.performance_level}</div>
						<div class="perf-subtitle">{lt('Perceptual Speed Index:', 'উপলব্ধির গতি সূচক:')} {n(results.metrics.perceptual_speed_index)} · {lt('Inspection Time Complete!', 'ইন্সপেকশন টাইম সম্পন্ন!')}</div>
					</div>

					<div class="metrics-grid">
						<div class="metric-card highlight">
							<div class="metric-icon">◎</div>
							<div class="metric-value">{n(results.metrics.accuracy)}%</div>
							<div class="metric-label">{lt('Accuracy', 'নির্ভুলতা')}</div>
							<div class="metric-sub">{n(results.metrics.correct_count)}/{n(results.metrics.total_trials)} {lt('correct', 'সঠিক')}</div>
						</div>
						<div class="metric-card">
							<div class="metric-icon">→</div>
							<div class="metric-value">{n(results.metrics.perceptual_speed_index)}</div>
							<div class="metric-label">{lt('Perceptual Speed Index', 'উপলব্ধির গতি সূচক')}</div>
							<div class="metric-sub">{n(results.metrics.presentation_time_ms)}{lt('ms', 'মি.সে.')} {lt('flash', 'ফ্ল্যাশে')}</div>
						</div>
						<div class="metric-card">
							<div class="metric-icon">⏱</div>
							<div class="metric-value">{n(results.metrics.average_reaction_time)}{lt('ms', 'মি.সে.')}</div>
							<div class="metric-label">{lt('Avg Decision Time', 'গড় সিদ্ধান্ত সময়')}</div>
							<div class="metric-sub">{lt('after mask appears', 'মাস্ক দেখানোর পর')}</div>
						</div>
						<div class="metric-card">
							<div class="metric-icon">↑</div>
							<div class="metric-value">{n(results.metrics.consistency)}%</div>
							<div class="metric-label">{lt('Consistency', 'ধারাবাহিকতা')}</div>
							<div class="metric-sub">{lt('response variability', 'উত্তরের ওঠানামা')}</div>
						</div>
					</div>

					<div class="breakdown">
						<h3>{lt('Detailed Analysis', 'বিস্তারিত বিশ্লেষণ')}</h3>
						<div class="breakdown-row">
							<span class="bd-label">{lt('Total Trials', 'মোট ট্রায়াল')}</span>
							<span class="bd-val">{n(results.metrics.total_trials)}</span>
						</div>
						<div class="breakdown-row">
							<span class="bd-label">{lt('Correct Answers', 'সঠিক উত্তর')}</span>
							<span class="bd-val bd-success">{n(results.metrics.correct_count)}</span>
						</div>
						<div class="breakdown-row">
							<span class="bd-label">{lt('Presentation Time', 'দেখানোর সময়')}</span>
							<span class="bd-val">{n(results.metrics.presentation_time_ms)}{lt('ms', 'মি.সে.')}</span>
						</div>
						<div class="breakdown-row">
							<span class="bd-label">{lt('Perceptual Speed Index', 'উপলব্ধির গতি সূচক')}</span>
							<span class="bd-val">{n(results.metrics.perceptual_speed_index)}</span>
						</div>
						<div class="breakdown-row">
							<span class="bd-label">{lt('Consistency', 'ধারাবাহিকতা')}</span>
							<span class="bd-val">{n(results.metrics.consistency)}%</span>
						</div>
						<div class="breakdown-row">
							<span class="bd-label">{lt('Performance Level', 'পারফরম্যান্স স্তর')}</span>
							<span class="bd-val">{results.metrics.performance_level}</span>
						</div>
					</div>

					<div class="clinical-note">
						<h4>{lt('Clinical Context', 'ক্লিনিক্যাল প্রেক্ষাপট')}</h4>
						<p>
							{#if results.metrics.accuracy >= 90}
								{lt("Excellent perceptual speed! You're accurately processing visual information at", 'চমৎকার উপলব্ধির গতি! আপনি ভিজ্যুয়াল তথ্য সঠিকভাবে প্রসেস করছেন')} <strong>{n(results.metrics.presentation_time_ms)}{lt('ms', 'মি.সে.')}</strong> - {lt('significantly below the average conscious perception threshold.', 'যা সচেতন উপলব্ধির গড় সীমার চেয়েও অনেক কম।')}
							{:else if results.metrics.accuracy >= 75}
								{lt("Good perceptual processing. You're reliably perceiving brief flashes at", 'ভালো উপলব্ধি প্রসেসিং। আপনি নির্ভরযোগ্যভাবে সংক্ষিপ্ত ফ্ল্যাশ ধরতে পারছেন')} <strong>{n(results.metrics.presentation_time_ms)}{lt('ms', 'মি.সে.')}</strong>. {lt('Regular practice can push your threshold even lower.', 'নিয়মিত অনুশীলনে আপনার সীমা আরও কমতে পারে।')}
							{:else if results.metrics.accuracy >= 60}
								{lt('Average perceptual speed at this duration. Your brain is working at its threshold — precision will improve with training.', 'এই সময়মাত্রায় উপলব্ধির গতি গড় পর্যায়ে। আপনার মস্তিষ্ক সীমার কাছাকাছি কাজ করছে — অনুশীলনে নির্ভুলতা বাড়বে।')}
							{:else}
								{lt("You're developing perceptual speed at this threshold. The task adapts to find your optimal level — keep practising and improvement will follow.", 'এই সীমায় আপনার উপলব্ধির গতি উন্নতির পথে। টাস্কটি আপনার উপযুক্ত স্তর খুঁজে নিতে বদলায় — অনুশীলন চালিয়ে গেলে উন্নতি আসবে।')}
							{/if}
						</p>
						<p class="why-matters"><strong>{lt('Why this matters for MS:', 'MS-এর ক্ষেত্রে কেন গুরুত্বপূর্ণ:')}</strong> {lt('Processing speed deficits are among the most common cognitive changes in MS. This task measures pure visual perception speed without any motor demands, making it ideal for tracking brain efficiency over time.', 'MS-এ প্রসেসিং স্পিডের দুর্বলতা সবচেয়ে সাধারণ কগনিটিভ পরিবর্তনগুলোর একটি। এই টাস্ক মোটর চাহিদা ছাড়াই বিশুদ্ধ ভিজ্যুয়াল উপলব্ধির গতি মাপে, তাই সময়ের সঙ্গে মস্তিষ্কের দক্ষতা ট্র্যাক করতে উপযোগী।')}</p>
					</div>

					{#if results.adaptation_reason}
						<div class="difficulty-info">
							<span>{lt('Difficulty:', 'কঠিনতা:')} <strong>{n(results.difficulty_before)}</strong> → <strong>{n(results.difficulty_after)}</strong></span>
							<span class="adapt-reason">{results.adaptation_reason}</span>
						</div>
					{/if}

					{#if results.new_badges && results.new_badges.length > 0}
						<BadgeNotification badges={results.new_badges} />
					{/if}

					<div class="button-group">
						<button class="start-button" on:click={returnToDashboard}>{lt('Return to Dashboard', 'ড্যাশবোর্ডে ফিরে যান')}</button>
						<button class="btn-secondary" on:click={() => goto('/dashboard')}>{lt('Back to Dashboard', 'ড্যাশবোর্ডে ফিরে যান')}</button>
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>

{#if showHelp}
	<div class="modal-overlay" on:click={() => showHelp = false} role="presentation">
		<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
		<div class="modal-content" on:click|stopPropagation role="dialog" tabindex="-1" on:keydown={(e) => e.key === 'Escape' && (showHelp = false)}>
			<button class="close-btn" on:click={() => showHelp = false}>×</button>
			<h2>{lt('Inspection Time — Strategies', 'ইনস্পেকশন টাইম — কৌশল')}</h2>
			<div class="strategy">
				<h3>{lt('Stay Relaxed', 'শান্ত থাকুন')}</h3>
				<p>{lt('Tension and anxiety physically reduce perceptual sensitivity. Take a breath before each trial and stay calm — your perception improves when you are relaxed.', 'টেনশন ও উদ্বেগ চোখে ধরা সংবেদনশীলতা কমাতে পারে। প্রতিটি ট্রায়ালের আগে শ্বাস নিন ও শান্ত থাকুন — শান্ত থাকলে দেখা ভালো হয়।')}</p>
			</div>
			<div class="strategy">
				<h3>{lt('Central Focus', 'মাঝখানে মনোযোগ')}</h3>
				<p>{lt('Keep your gaze fixed on the centre of the screen between trials. The lines appear left and right — central focus lets peripheral vision catch both at once.', 'ট্রায়ালের মাঝে চোখ স্ক্রিনের মাঝখানে রাখুন। রেখা বাম ও ডানে দেখা যাবে — মাঝখানে তাকালে দুই পাশ একসঙ্গে ধরতে সুবিধা হয়।')}</p>
			</div>
			<div class="strategy">
				<h3>{lt('Trust Your First Impression', 'প্রথম ধারণাকে বিশ্বাস করুন')}</h3>
				<p>{lt('The flash is too brief for conscious analysis. Your first instinct is your perceptual system’s best output — trust it rather than deliberating.', 'ঝলকটি বিশ্লেষণ করার মতো দীর্ঘ নয়। প্রথম যে ধারণা আসে সেটিই আপনার দেখার সিস্টেমের সেরা উত্তর — বেশি ভেবে বদলাবেন না।')}</p>
			</div>
			<div class="strategy">
				<h3>{lt('Why the Mask?', 'মাস্ক কেন?')}</h3>
				<p>{lt('The pattern mask immediately after the flash prevents afterimage processing. This measures real-time perception, not memory of the image.', 'ঝলকের পরপরই প্যাটার্ন মাস্ক দেখালে পরে থেকে যাওয়া ছবি ধরে উত্তর দেওয়া যায় না। এতে ছবির স্মৃতি নয়, আসল সময়ে দেখা মাপা হয়।')}</p>
			</div>
			<div class="strategy">
				<h3>{lt('Adaptive Difficulty', 'মানিয়ে নেওয়া কঠিনতা')}</h3>
				<p>{lt('The task adjusts flash duration to find your perceptual threshold. Getting some wrong is expected and meaningful — not a failure.', 'আপনার দেখা ধরার সীমা খুঁজতে টাস্কটি ঝলকের সময় বদলায়। কিছু ভুল হওয়া স্বাভাবিক এবং তথ্যপূর্ণ — এটি ব্যর্থতা নয়।')}</p>
			</div>
			<div class="strategy">
				<h3>{lt('Why This Matters', 'কেন গুরুত্বপূর্ণ')}</h3>
				<p>{lt('Inspection Time requires no complex motor responses — just a simple left/right click. This makes it a clean measure of cognitive processing speed for MS research.', 'ইনস্পেকশন টাইমে জটিল হাতের কাজ লাগে না — শুধু বাম/ডান ক্লিক। তাই MS গবেষণায় এটি প্রক্রিয়াকরণের গতি মাপার পরিষ্কার উপায়।')}</p>
			</div>
		</div>
	</div>
{/if}

<style>
	/* ── Container ─────────────────────────────────────────── */
	.it-container {
		min-height: 100vh;
		background: #C8DEFA;
		padding: 2rem 1rem;
	}

	.it-inner {
		max-width: 960px;
		margin: 0 auto;
	}

	/* ── Instructions card ─────────────────────────────────── */
	.instructions-card {
		background: white;
		border-radius: 16px;
		padding: 2.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07), 0 1px 3px rgba(0, 0, 0, 0.06);
		display: flex;
		flex-direction: column;
		gap: 1.8rem;
	}

	.header-content { text-align: center; }

	.title-row {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		flex-wrap: wrap;
		margin-bottom: 0.5rem;
	}

	.header-content h1 {
		font-size: 1.8rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0;
	}

	.subtitle {
		color: #64748b;
		font-size: 1rem;
		margin: 0.4rem 0 0.8rem;
	}

	.classic-badge {
		display: inline-block;
		background: rgba(102, 126, 234, 0.12);
		color: #667eea;
		border: 1px solid rgba(102, 126, 234, 0.3);
		border-radius: 20px;
		padding: 0.3rem 1rem;
		font-size: 0.82rem;
		font-weight: 600;
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

	/* ── Task concept (violet for neural flash) ────────────── */
	.task-concept {
		background: linear-gradient(135deg, #faf5ff, #ede9fe);
		border: 1px solid #c4b5fd;
		border-radius: 12px;
		padding: 1.5rem;
	}

	.task-concept h3 {
		font-size: 1rem;
		font-weight: 700;
		color: #6d28d9;
		margin: 0 0 0.6rem;
	}

	.task-concept p {
		color: #3b0764;
		margin: 0 0 1.2rem;
		line-height: 1.6;
	}

	.demo-lines {
		display: flex;
		align-items: flex-end;
		justify-content: center;
		gap: 2.5rem;
		background: white;
		border-radius: 10px;
		padding: 1.2rem;
		margin-bottom: 1rem;
		box-shadow: 0 2px 8px rgba(0,0,0,0.06);
	}

	.demo-line-col {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}

	.demo-line {
		width: 10px;
		background: #1e293b;
		border-radius: 2px;
	}

	.demo-line-label {
		font-size: 0.82rem;
		font-weight: 700;
		color: #475569;
	}

	.demo-vs {
		font-size: 1.2rem;
		font-weight: 800;
		color: #7c3aed;
		align-self: center;
	}

	.demo-answer-row {
		display: flex;
		justify-content: center;
	}

	.demo-ans-same {
		background: #ede9fe;
		color: #6d28d9;
		padding: 0.35rem 0.9rem;
		border-radius: 8px;
		font-weight: 700;
		font-size: 0.9rem;
	}

	/* ── Rules grid ────────────────────────────────────────── */
	.rules-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}

	.rule-card {
		display: flex;
		align-items: flex-start;
		gap: 0.8rem;
		padding: 1rem;
		background: #f8fafc;
		border-radius: 10px;
		border-left: 4px solid #7c3aed;
	}

	.rule-icon { font-size: 1.5rem; flex-shrink: 0; }
	.rule-text { display: flex; flex-direction: column; gap: 0.2rem; }
	.rule-text strong { font-size: 0.9rem; color: #1e293b; }
	.rule-text span   { font-size: 0.82rem; color: #64748b; line-height: 1.4; }

	/* ── Info grid ─────────────────────────────────────────── */
	.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }

	.info-section { background: #f8fafc; border-radius: 10px; padding: 1.2rem; }
	.info-section h4 { font-size: 0.9rem; font-weight: 700; color: #1e293b; margin: 0 0 0.8rem; }

	.tips-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 0.5rem; }
	.tips-list li { font-size: 0.85rem; color: #475569; line-height: 1.4; }

	.structure-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 0.5rem; }
	.structure-list li {
		display: flex; justify-content: space-between; align-items: center;
		font-size: 0.85rem; padding: 0.3rem 0; border-bottom: 1px solid #e2e8f0;
	}
	.structure-list li:last-child { border-bottom: none; }
	.struct-key { color: #64748b; }
	.struct-val { font-weight: 600; color: #1e293b; }

	/* ── Clinical info ─────────────────────────────────────── */
	.clinical-info {
		background: linear-gradient(135deg, #f0fdf4, #dcfce7);
		border: 1px solid #bbf7d0;
		border-radius: 12px;
		padding: 1.2rem;
	}
	.clinical-info h4 { font-size: 0.9rem; font-weight: 700; color: #166534; margin: 0 0 0.8rem; }
	.clinical-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
	.clinical-item { display: flex; flex-direction: column; gap: 0.2rem; }
	.clinical-item strong { font-size: 0.82rem; color: #166534; }
	.clinical-item span   { font-size: 0.8rem; color: #15803d; }

	/* ── Performance guide ─────────────────────────────────── */
	.perf-guide { background: #f8fafc; border-radius: 12px; padding: 1.2rem; }
	.perf-guide h4 { font-size: 0.9rem; font-weight: 700; color: #1e293b; margin: 0 0 0.8rem; }
	.norm-bars { display: flex; flex-direction: column; gap: 0.4rem; }
	.norm-bar {
		display: flex; justify-content: space-between; align-items: center;
		padding: 0.5rem 0.9rem; border-radius: 6px; font-size: 0.85rem; font-weight: 600;
	}
	.norm-excellent { background: #dcfce7; color: #166534; }
	.norm-good      { background: #d1fae5; color: #065f46; }
	.norm-avg       { background: #fef9c3; color: #854d0e; }
	.norm-fair      { background: #ffedd5; color: #9a3412; }
	.norm-needs     { background: #fee2e2; color: #991b1b; }
	.norm-label { font-weight: 700; }
	.norm-val   { font-weight: 400; font-size: 0.82rem; }
	.norm-note { font-size: 0.78rem; color: #94a3b8; font-style: italic; margin: 0.5rem 0 0; text-align: center; }

	/* ── Button group ──────────────────────────────────────── */
	.button-group {
		display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap; padding-top: 0.5rem;
		align-items: center;
	}

	.start-button {
		background: #4338ca;
		color: white; border: none; border-radius: 10px;
		padding: 0.85rem 2.5rem; font-size: 1rem; font-weight: 700;
		cursor: pointer; transition: transform 0.15s, box-shadow 0.15s;
		box-shadow: 0 4px 14px rgba(67, 56, 202, 0.35);
	}
	.start-button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5); }

	.btn-secondary {
		background: white; color: #667eea;
		border: 2px solid #667eea; border-radius: 10px;
		padding: 0.85rem 2rem; font-size: 1rem; font-weight: 600;
		cursor: pointer; transition: all 0.15s;
	}
	.btn-secondary:hover { background: rgba(102, 126, 234, 0.08); }

	/* ── Screen card ───────────────────────────────────────── */
	.screen-card {
		background: white;
		border-radius: 16px;
		padding: 2.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
	}

	.error-screen { text-align: center; }
	.error-screen h2 { margin: 0 0 0.75rem; color: #dc2626; }
	.error-screen p  { color: #64748b; margin: 0 0 1.5rem; }

	/* ── Practice screen ───────────────────────────────────── */
	.practice-screen { text-align: center; }
	.practice-screen h2 { font-size: 1.6rem; font-weight: 700; color: #1e293b; margin: 0 0 0.5rem; }
	.practice-intro { color: #64748b; margin: 0 0 1.5rem; }

	.practice-info-row { display: flex; gap: 0.75rem; justify-content: center; flex-wrap: wrap; margin-bottom: 1.5rem; }

	.p-badge {
		background: rgba(102, 126, 234, 0.12); color: #667eea;
		padding: 0.4rem 1rem; border-radius: 20px; font-size: 0.85rem; font-weight: 700;
	}
	.p-speed { background: #ede9fe; color: #6d28d9; }

	.practice-ready { margin: 1.5rem 0; }
	.practice-ready p { color: #64748b; margin-bottom: 1rem; }

	/* ── Testing screen ────────────────────────────────────── */
	.testing-screen { padding: 1.5rem; }

	.test-header {
		display: flex; justify-content: space-between; align-items: center;
		margin-bottom: 1.5rem; flex-wrap: wrap; gap: 0.5rem;
	}
	.test-badges { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; flex: 1; }
	.count-badge {
		background: rgba(102, 126, 234, 0.12); color: #667eea;
		padding: 0.4rem 0.9rem; border-radius: 20px; font-size: 0.85rem; font-weight: 700;
	}
	.speed-badge {
		background: #ede9fe; color: #6d28d9;
		padding: 0.4rem 0.9rem; border-radius: 20px; font-size: 0.82rem; font-weight: 600;
	}
	.progress-track {
		flex: 1; height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden; min-width: 80px;
	}
	.progress-fill { height: 100%; background: linear-gradient(90deg, #7c3aed, #a855f7); border-radius: 3px; transition: width 0.3s; }
	.help-btn-sm {
		width: 36px; height: 36px; border-radius: 50%;
		border: 2px solid #667eea; background: white; color: #667eea;
		font-size: 1.1rem; font-weight: 700; cursor: pointer;
		transition: all 0.2s; display: flex; align-items: center; justify-content: center;
	}
	.help-btn-sm:hover { background: #667eea; color: white; }

	/* ── Stimulus area ─────────────────────────────────────── */
	.stimulus-area {
		display: flex;
		justify-content: center;
		align-items: center;
		min-height: 280px;
		background: #f8fafc;
		border-radius: 14px;
		border: 2px solid #e2e8f0;
	}

	.lines-container {
		display: flex;
		align-items: flex-end;
		gap: 4rem;
	}

	.line {
		background: #1e293b;
		border-radius: 3px;
	}

	.spacer { width: 2rem; }

	/* ── Mask pattern ──────────────────────────────────────── */
	.mask-pattern { padding: 1rem; }
	.mask-grid {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		gap: 3px;
		width: 200px;
	}
	.mask-cell {
		width: 36px;
		height: 36px;
		background: #1e293b;
		border-radius: 2px;
		animation: flicker 0.1s step-end infinite;
	}
	@keyframes flicker {
		0%   { opacity: 1; background: #1e293b; }
		25%  { opacity: 0.8; background: #7c3aed; }
		50%  { opacity: 1; background: #1e293b; }
		75%  { opacity: 0.6; background: #475569; }
		100% { opacity: 1; background: #1e293b; }
	}

	/* ── Response area ─────────────────────────────────────── */
	.response-area { text-align: center; }
	.response-prompt {
		font-size: 1.1rem; font-weight: 600; color: #1e293b; margin: 0 0 1.5rem;
	}
	.response-buttons {
		display: flex; gap: 2rem; justify-content: center; flex-wrap: wrap;
	}
	.response-btn {
		display: flex; align-items: center; gap: 0.5rem;
		padding: 1.1rem 2.5rem; border: none; border-radius: 12px;
		font-size: 1.1rem; font-weight: 700; cursor: pointer;
		transition: transform 0.15s, box-shadow 0.15s; min-width: 140px;
	}
	.left-btn  {
		background: linear-gradient(135deg, #7c3aed, #6d28d9);
		color: white; box-shadow: 0 4px 14px rgba(124, 58, 237, 0.4);
	}
	.left-btn:hover  { transform: translateY(-3px); box-shadow: 0 6px 20px rgba(124, 58, 237, 0.55); }
	.right-btn {
		background: linear-gradient(135deg, #a855f7, #9333ea);
		color: white; box-shadow: 0 4px 14px rgba(168, 85, 247, 0.4);
	}
	.right-btn:hover { transform: translateY(-3px); box-shadow: 0 6px 20px rgba(168, 85, 247, 0.55); }
	.resp-icon { font-size: 1.3rem; }
	.resp-text { font-size: 1rem; letter-spacing: 0.06em; }

	/* ── Waiting state ─────────────────────────────────────── */
	.waiting-state { text-align: center; }
	.fixation-cross {
		font-size: 3rem; font-weight: 300; color: #475569; line-height: 1;
		margin-bottom: 0.75rem;
	}
	.waiting-state p { color: #94a3b8; font-size: 0.9rem; margin: 0; }

	/* ── Complete screen ───────────────────────────────────── */
	.complete-screen { display: flex; flex-direction: column; gap: 1.5rem; }

	.perf-banner {
		text-align: center; padding: 1.5rem;
		background: linear-gradient(135deg, #faf5ff, #ede9fe);
		border: 2px solid #c4b5fd; border-radius: 14px;
	}
	.perf-level    { font-size: 1.8rem; font-weight: 800; color: #6d28d9; }
	.perf-subtitle { font-size: 0.95rem; color: #64748b; margin-top: 0.3rem; }

	.metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; }
	.metric-card {
		background: #f8fafc; border: 1px solid #e2e8f0;
		border-radius: 12px; padding: 1.2rem; text-align: center;
	}
	.metric-card.highlight {
		background: linear-gradient(135deg, #7c3aed, #6d28d9);
		color: white; border-color: transparent;
	}
	.metric-icon  { font-size: 1.8rem; margin-bottom: 0.4rem; }
	.metric-value { font-size: 1.8rem; font-weight: 800; color: #1e293b; margin-bottom: 0.2rem; }
	.metric-card.highlight .metric-value,
	.metric-card.highlight .metric-label,
	.metric-card.highlight .metric-sub { color: white; }
	.metric-label { font-size: 0.82rem; font-weight: 600; color: #64748b; }
	.metric-sub   { font-size: 0.78rem; color: #94a3b8; margin-top: 0.2rem; }

	/* ── Breakdown ─────────────────────────────────────────── */
	.breakdown { background: #f8fafc; border-radius: 12px; padding: 1.2rem; }
	.breakdown h3 { font-size: 0.95rem; font-weight: 700; color: #1e293b; margin: 0 0 0.8rem; }
	.breakdown-row {
		display: flex; justify-content: space-between; align-items: center;
		padding: 0.55rem 0; border-bottom: 1px solid #e2e8f0; font-size: 0.9rem;
	}
	.breakdown-row:last-child { border-bottom: none; }
	.bd-label { color: #64748b; }
	.bd-val   { font-weight: 700; color: #667eea; }
	.bd-success { color: #16a34a; }

	/* ── Clinical note ─────────────────────────────────────── */
	.clinical-note {
		background: linear-gradient(135deg, #f0fdf4, #dcfce7);
		border: 1px solid #bbf7d0; border-radius: 12px; padding: 1.2rem;
	}
	.clinical-note h4 { font-size: 0.9rem; font-weight: 700; color: #166534; margin: 0 0 0.5rem; }
	.clinical-note p { font-size: 0.9rem; color: #15803d; line-height: 1.6; margin: 0 0 0.5rem; }
	.clinical-note p:last-child { margin: 0; }
	.why-matters { font-style: italic; }

	/* ── Difficulty info ───────────────────────────────────── */
	.difficulty-info {
		background: #faf5ff; border: 1px solid #c4b5fd; border-radius: 10px;
		padding: 0.9rem 1.2rem; display: flex; justify-content: space-between;
		align-items: center; flex-wrap: wrap; gap: 0.5rem;
		font-size: 0.88rem; font-weight: 600; color: #6d28d9;
	}
	.adapt-reason { color: #a855f7; font-weight: 400; font-style: italic; }

	/* ── Help modal ────────────────────────────────────────── */
	.modal-overlay {
		position: fixed; inset: 0; background: rgba(0,0,0,0.55);
		display: flex; align-items: center; justify-content: center;
		z-index: 1000; padding: 1rem;
	}
	.modal-content {
		background: white; border-radius: 16px; padding: 2rem;
		max-width: 560px; width: 100%; max-height: 80vh; overflow-y: auto;
		position: relative; box-shadow: 0 20px 60px rgba(0,0,0,0.3);
	}
	.close-btn {
		position: absolute; top: 1rem; right: 1rem;
		width: 36px; height: 36px; border: none; background: #f1f5f9;
		color: #475569; font-size: 1.4rem; border-radius: 50%; cursor: pointer;
		display: flex; align-items: center; justify-content: center; transition: background 0.15s;
	}
	.close-btn:hover { background: #e2e8f0; }
	.modal-content h2 {
		font-size: 1.2rem; font-weight: 700; color: #1e293b;
		margin: 0 0 1.2rem; padding-right: 2.5rem;
	}
	.strategy {
		padding: 0.9rem 1rem; background: #f8fafc;
		border-radius: 8px; border-left: 4px solid #7c3aed; margin-bottom: 0.75rem;
	}
	.strategy h3 { font-size: 0.88rem; font-weight: 700; color: #1e293b; margin: 0 0 0.3rem; }
	.strategy p  { font-size: 0.84rem; color: #64748b; margin: 0; line-height: 1.5; }

	/* ── Responsive ────────────────────────────────────────── */
	@media (max-width: 640px) {
		.instructions-card { padding: 1.5rem; gap: 1.2rem; }
		.rules-grid { grid-template-columns: 1fr; }
		.info-grid { grid-template-columns: 1fr; }
		.clinical-grid { grid-template-columns: 1fr; }
		.metrics-grid { grid-template-columns: repeat(2, 1fr); }
		.header-content h1 { font-size: 1.4rem; }
		.screen-card { padding: 1.25rem; }
		.response-btn { padding: 0.85rem 1.5rem; min-width: 110px; }
		.lines-container { gap: 2rem; }
	}
</style>

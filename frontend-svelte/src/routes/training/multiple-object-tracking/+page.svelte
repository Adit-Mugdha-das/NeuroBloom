<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { generateMOTTrial, submitMOTResponse } from '$lib/api';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
import TaskReturnButton from '$lib/components/TaskReturnButton.svelte';
	import { formatNumber, formatSeconds, locale, localeText } from '$lib/i18n';
	import { getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
import { TASK_RETURN_CONTEXT } from '$lib/task-navigation';
	import { user } from '$lib/stores';
	import { onDestroy, onMount } from 'svelte';

	function n(value, options = {}) {
		return formatNumber(value, $locale, options);
	}

	function sec(value, options = {}) {
		return formatSeconds(value, $locale, options);
	}

	// ── Auth ──────────────────────────────────────────
	let currentUser = null;
	user.subscribe((value) => { currentUser = value; });

	// ── Phase ─────────────────────────────────────────
	let phase = 'loading'; // loading | intro | highlighting | tracking | selection | results

	// ── Trial Data ────────────────────────────────────
	let trialData = null;
	let difficulty = 5;
	let taskId = null;

	// ── Objects ───────────────────────────────────────
	let objects = [];
	let selectedObjects = new Set();
	let animationId = null;
	let startTime = null;
	let timeRemaining = 0;
	let timerInterval = null;
	let highlightTimeout = null;
	let trackingStartTimeout = null;

	// ── Selection Timing ──────────────────────────────
	let selectionStartTime = null;
	let selectionElapsed = 0;
	let selectionTimerInterval = null;

	// ── Results ───────────────────────────────────────
	let results = null;
	let earnedBadges = [];
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';

	// ── Errors ────────────────────────────────────────
	let loadError = false;
	let saveError = false;

	// ── Constants ─────────────────────────────────────
	const HIGHLIGHT_DURATION = 2000;
	const PAUSE_BEFORE_TRACKING = 1000;

	// ── Helpers ───────────────────────────────────────
	function lt(en, bn) { return localeText({ en, bn }, $locale); }

	function performanceLabel(p) {
		const map = {
			perfect:          lt('Perfect', 'নিখুঁত'),
			excellent:        lt('Excellent', 'অসাধারণ'),
			good:             lt('Good', 'ভালো'),
			average:          lt('Average', 'মোটামুটি'),
			needs_improvement: lt('Needs Improvement', 'উন্নতি দরকার')
		};
		return map[p] || (p || '').replace('_', ' ');
	}

	// ── Lifecycle ──────────────────────────────────────
	onMount(() => {
		if (!currentUser) { goto('/login'); return; }
		taskId = $page.url.searchParams.get('taskId');
		loadTrial();
	});

	onDestroy(() => {
		stopAnimation();
		if (timerInterval) clearInterval(timerInterval);
		if (selectionTimerInterval) clearInterval(selectionTimerInterval);
		if (highlightTimeout) clearTimeout(highlightTimeout);
		if (trackingStartTimeout) clearTimeout(trackingStartTimeout);
	});

	// ── Game Logic ─────────────────────────────────────
	async function loadTrial() {
		try {
			loadError = false;
			phase = 'loading';
			const response = await generateMOTTrial(currentUser.id);
			trialData = response.trial_data;
			difficulty = response.difficulty;
			objects = trialData.objects.map(obj => ({
				...obj,
				x: obj.x,
				y: obj.y,
				vx: obj.vx,
				vy: obj.vy,
				is_target: obj.is_target,
				show_highlight: false,
				radius: 20
			}));
			phase = 'intro';
		} catch (_) {
			loadError = true;
			phase = 'intro';
		}
	}

	function startTask(nextMode = TASK_PLAY_MODE.RECORDED) {
		stopAnimation();
		if (timerInterval) {
			clearInterval(timerInterval);
			timerInterval = null;
		}
		if (selectionTimerInterval) {
			clearInterval(selectionTimerInterval);
			selectionTimerInterval = null;
		}
		if (highlightTimeout) {
			clearTimeout(highlightTimeout);
			highlightTimeout = null;
		}
		if (trackingStartTimeout) {
			clearTimeout(trackingStartTimeout);
			trackingStartTimeout = null;
		}

		playMode = nextMode;
		practiceStatusMessage = '';
		selectedObjects = new Set();
		results = null;
		earnedBadges = [];
		selectionStartTime = null;
		selectionElapsed = 0;
		phase = 'highlighting';

		// Show targets highlighted
		objects = objects.map(obj => ({
			...obj,
			show_highlight: obj.is_target
		}));

		highlightTimeout = setTimeout(() => {
			highlightTimeout = null;
			objects = objects.map(obj => ({ ...obj, show_highlight: false }));
			trackingStartTimeout = setTimeout(() => {
				trackingStartTimeout = null;
				startTracking();
			}, PAUSE_BEFORE_TRACKING);
		}, HIGHLIGHT_DURATION);
	}

	function leavePractice(completed = false) {
		stopAnimation();
		if (timerInterval) {
			clearInterval(timerInterval);
			timerInterval = null;
		}
		if (selectionTimerInterval) {
			clearInterval(selectionTimerInterval);
			selectionTimerInterval = null;
		}
		if (highlightTimeout) {
			clearTimeout(highlightTimeout);
			highlightTimeout = null;
		}
		if (trackingStartTimeout) {
			clearTimeout(trackingStartTimeout);
			trackingStartTimeout = null;
		}

		playMode = TASK_PLAY_MODE.RECORDED;
		practiceStatusMessage = completed ? getPracticeCopy($locale).complete : '';
		selectedObjects = new Set();
		results = null;
		earnedBadges = [];
		selectionStartTime = null;
		selectionElapsed = 0;
		timeRemaining = 0;
		if (trialData?.objects) {
			objects = trialData.objects.map((obj) => ({
				...obj,
				x: obj.x,
				y: obj.y,
				show_highlight: false
			}));
		}
		phase = 'intro';
	}

	function startTracking() {
		phase = 'tracking';
		startTime = Date.now();
		timeRemaining = trialData.tracking_duration;

		timerInterval = setInterval(() => {
			const elapsed = (Date.now() - startTime) / 1000;
			timeRemaining = Math.max(0, trialData.tracking_duration - elapsed);
			if (timeRemaining <= 0) { stopTracking(); }
		}, 100);

		animationId = requestAnimationFrame(updateObjects);
	}

	function updateObjects() {
		const arenaSize = trialData.arena_size;
		const radius = 20;

		objects = objects.map(obj => {
			let newX = obj.x + obj.vx;
			let newY = obj.y + obj.vy;
			let newVx = obj.vx;
			let newVy = obj.vy;

			if (newX - radius < 0)          { newX = radius;            newVx =  Math.abs(newVx); }
			else if (newX + radius > arenaSize) { newX = arenaSize - radius; newVx = -Math.abs(newVx); }
			if (newY - radius < 0)          { newY = radius;            newVy =  Math.abs(newVy); }
			else if (newY + radius > arenaSize) { newY = arenaSize - radius; newVy = -Math.abs(newVy); }

			return { ...obj, x: newX, y: newY, vx: newVx, vy: newVy };
		});

		animationId = requestAnimationFrame(updateObjects);
	}

	function stopTracking() {
		stopAnimation();
		if (timerInterval) { clearInterval(timerInterval); timerInterval = null; }
		selectionStartTime = Date.now();
		selectionElapsed = 0;
		selectionTimerInterval = setInterval(() => {
			selectionElapsed = (Date.now() - selectionStartTime) / 1000;
		}, 100);
		phase = 'selection';
	}

	function stopAnimation() {
		if (animationId) { cancelAnimationFrame(animationId); animationId = null; }
	}

	function toggleObjectSelection(objectId) {
		if (selectedObjects.has(objectId)) {
			selectedObjects.delete(objectId);
		} else {
			selectedObjects.add(objectId);
		}
		selectedObjects = selectedObjects; // trigger reactivity
	}

	async function submitSelection() {
		if (selectionTimerInterval) { clearInterval(selectionTimerInterval); selectionTimerInterval = null; }
		const responseTime = (Date.now() - selectionStartTime) / 1000;
		saveError = false;
		try {
			const response = await submitMOTResponse(currentUser.id, {
				trial_data: trialData,
				user_response: {
					selected_objects: Array.from(selectedObjects),
					response_time: responseTime
				},
				task_id: taskId
			});
			results = response;
			earnedBadges = response.new_badges || [];
			phase = 'results';
		} catch (_) {
			saveError = true;
			phase = 'results';
		}
	}

	function nextTrial() {
		if (playMode === TASK_PLAY_MODE.PRACTICE) {
			leavePractice(true);
			return;
		}
		selectedObjects = new Set();
		results = null;
		earnedBadges = [];
		selectionStartTime = null;
		selectionElapsed = 0;
		if (selectionTimerInterval) { clearInterval(selectionTimerInterval); selectionTimerInterval = null; }
		loadTrial();
	}
</script>

<div class="mot-page">
	<div class="mot-wrapper">

		{#if phase === 'loading'}
			<LoadingSkeleton />

		{:else if phase === 'intro'}
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />

			<!-- Header Card -->
			<div class="header-card">
				<div class="header-content">
					<div class="header-text">
						<h1 class="task-title">{lt('Multiple Object Tracking', 'মাল্টিপল অবজেক্ট ট্র্যাকিং')}</h1>
						<p class="task-domain">{lt('Dynamic Visual Attention · Visual Scanning', 'ডায়নামিক ভিজ্যুয়াল মনোযোগ · ভিজ্যুয়াল স্ক্যানিং')}</p>
					</div>
					<DifficultyBadge difficulty={difficulty || 1} domain="Visual Scanning" />
				</div>
			</div>

			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
			{/if}

			{#if loadError}
				<div class="error-card">
					<p>{lt('Failed to load task. Please try again.', 'টাস্ক লোড করতে ব্যর্থ। আবার চেষ্টা করুন।')}</p>
					<button class="start-button" on:click={loadTrial}>{lt('Retry', 'আবার চেষ্টা করুন')}</button>
				</div>
			{:else if trialData}

				<!-- Concept Card -->
				<div class="card task-concept">
					<div class="concept-badge">
						<span class="badge-label">{lt('Multiple Object Tracking', 'MOT')}</span>
						<span>{lt('Pylyshyn & Storm, 1988', 'Pylyshyn & Storm, 1988')}</span>
					</div>
					<p class="concept-desc">
						{lt(
							'In MOT, the visual system must simultaneously assign attentional "FINST" (fingers of instantiation) tokens to multiple moving targets. Unlike static search, this demands sustained distributed attention over time — a capacity strongly diminished by MS white-matter pathology, making it clinically relevant for driving and real-world multitasking safety.',
							'MOT-এ ভিজ্যুয়াল সিস্টেমকে একাধিক চলমান লক্ষ্যে মনোযোগ টোকেন বরাদ্দ করতে হয়। MS শ্বেত পদার্থ ক্ষতির কারণে এই ক্ষমতা উল্লেখযোগ্যভাবে কমে যায়।'
						)}
					</p>
				</div>

				<!-- Rules -->
				<div class="card">
					<h2 class="section-title">{lt('How It Works', 'কীভাবে কাজ করে')}</h2>
					<div class="rules-list">
						<div class="rule-item">
							<div class="rule-num">{n(1)}</div>
							<div class="rule-text">{lt('Several circles will flash — these are your targets to remember', 'কিছু বৃত্ত জ্বলতে থাকবে — এগুলো আপনার মনে রাখার লক্ষ্য')}</div>
						</div>
						<div class="rule-item">
							<div class="rule-num">{n(2)}</div>
							<div class="rule-text">{lt('All circles begin moving randomly — keep your eyes on the targets as they mix with distractors', 'সব বৃত্ত এলোমেলোভাবে চলতে শুরু করবে — লক্ষ্যগুলো চোখে রাখুন')}</div>
						</div>
						<div class="rule-item">
							<div class="rule-num">{n(3)}</div>
							<div class="rule-text">{lt('When movement stops, click all circles you were tracking', 'চলাচল থামলে আপনি যে বৃত্তগুলো ট্র্যাক করছিলেন সেগুলোতে ক্লিক করুন')}</div>
						</div>
						<div class="rule-item">
							<div class="rule-num">{n(4)}</div>
							<div class="rule-text">{lt('Accuracy matters more than speed — take your time during selection', 'গতির চেয়ে নির্ভুলতা বেশি গুরুত্বপূর্ণ — নির্বাচনের সময় সতর্কভাবে দেখুন')}</div>
						</div>
					</div>
				</div>

				<!-- Info Grid -->
				<div class="info-grid">
					<div class="card">
						<h3 class="card-title">{lt('Task Parameters', 'টাস্কের প্যারামিটার')}</h3>
						<div class="details-list">
							<div class="detail-row">
								<span>{lt('Total Objects', 'মোট বস্তু')}</span>
								<strong>{trialData.total_objects}</strong>
							</div>
							<div class="detail-row">
								<span>{lt('Targets to Track', 'ট্র্যাক করার লক্ষ্য')}</span>
								<strong class="highlight-val">{trialData.num_targets}</strong>
							</div>
							<div class="detail-row">
								<span>{lt('Tracking Duration', 'ট্র্যাকিং সময়কাল')}</span>
								<strong>{sec(trialData.tracking_duration)}</strong>
							</div>
							<div class="detail-row">
								<span>{lt('Speed', 'গতি')}</span>
								<strong>{trialData.speed_multiplier?.toFixed(1) || 1}×</strong>
							</div>
						</div>
					</div>
					<div class="card">
						<h3 class="card-title">{lt('What to Expect', 'কী আশা করবেন')}</h3>
						<div class="expect-steps">
							<div class="expect-item">
								<div class="expect-dot dot-yellow"></div>
								<span>{lt('Yellow flash = your targets (2 seconds)', 'হলুদ ঝলক = আপনার লক্ষ্য (২ সেকেন্ড)')}</span>
							</div>
							<div class="expect-item">
								<div class="expect-dot dot-blue"></div>
								<span>{lt('All circles identical while moving', 'চলার সময় সব বৃত্ত একই রকম')}</span>
							</div>
							<div class="expect-item">
								<div class="expect-dot dot-green"></div>
								<span>{lt('Green highlight = selected (click again to deselect)', 'সবুজ = নির্বাচিত (আবার ক্লিক করুন বাতিল করতে)')}</span>
							</div>
						</div>
					</div>
				</div>

				<!-- Clinical Basis -->
				<div class="clinical-info">
					<div class="clinical-header">
						<div class="clinical-badge">{lt('Clinical Basis', 'ক্লিনিকাল ভিত্তি')}</div>
						<h3>{lt('MS Driving Safety & Dynamic Attention', 'MS ড্রাইভিং নিরাপত্তা ও ডায়নামিক মনোযোগ')}</h3>
					</div>
					<p>
						{lt(
							'Multiple Object Tracking (Pylyshyn & Storm, 1988) directly predicts real-world divided attention performance including driving safety. MS-related deficits in sustained and divided visual attention significantly impair MOT capacity, particularly when tracking 3+ objects, making this paradigm a sensitive ecologically-valid measure of functional visual attention in everyday tasks.',
							'মাল্টিপল অবজেক্ট ট্র্যাকিং (Pylyshyn & Storm, 1988) সরাসরি ড্রাইভিং নিরাপত্তাসহ বাস্তব জীবনের বিভক্ত মনোযোগের পূর্বাভাস দেয়। MS-সংক্রান্ত ভিজ্যুয়াল মনোযোগের ঘাটতি MOT ক্ষমতাকে উল্লেখযোগ্যভাবে ক্ষতিগ্রস্ত করে।'
						)}
					</p>
				</div>

				<TaskPracticeActions
					locale={$locale}
					startLabel={lt('Begin Tracking Task', 'ট্র্যাকিং টাস্ক শুরু করুন')}
					statusMessage={practiceStatusMessage}
					on:start={() => startTask(TASK_PLAY_MODE.RECORDED)}
					on:practice={() => startTask(TASK_PLAY_MODE.PRACTICE)}
				/>

			{:else}
				<LoadingSkeleton />
			{/if}

		{:else if phase === 'highlighting' || phase === 'tracking' || phase === 'selection'}

			<!-- Arena Header -->
			<div class="arena-header-card">
				{#if playMode === TASK_PLAY_MODE.PRACTICE}
					<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
				{/if}

				{#if phase === 'highlighting'}
					<div class="phase-status phase-highlight">
						<div class="phase-icon-block dot-yellow-lg"></div>
						<div>
							<div class="phase-label">{lt('Phase 1 — Memorise Targets', 'ধাপ ১ — লক্ষ্য মনে রাখুন')}</div>
							<div class="phase-desc">{lt('The highlighted circles are your targets — remember them', 'হাইলাইট করা বৃত্তগুলো আপনার লক্ষ্য — এগুলো মনে রাখুন')}</div>
						</div>
					</div>

				{:else if phase === 'tracking'}
					<div class="phase-status phase-tracking">
						<div class="timer-block">
							<div class="timer-value {timeRemaining < 3 ? 'timer-critical' : ''}">{n(timeRemaining, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}</div>
							<div class="timer-label">{lt('seconds left', 'সেকেন্ড বাকি')}</div>
						</div>
						<div>
							<div class="phase-label">{lt('Phase 2 — Track the Targets', 'ধাপ ২ — লক্ষ্য ট্র্যাক করুন')}</div>
							<div class="phase-desc">{lt('Keep your eyes on the targets — do not look away!', 'লক্ষ্যের উপর চোখ রাখুন — দূরে তাকাবেন না!')}</div>
						</div>
					</div>

				{:else}
					<div class="phase-status phase-selection">
						<div class="selection-count-block">
							<span class="sel-count {selectedObjects.size === trialData.num_targets ? 'sel-complete' : ''}">{selectedObjects.size}</span>
							<span class="sel-sep">/</span>
							<span class="sel-total">{trialData.num_targets}</span>
						</div>
						<div>
							<div class="phase-label">{lt('Phase 3 — Select Targets', 'ধাপ ৩ — লক্ষ্য নির্বাচন করুন')}</div>
							<div class="phase-desc">{lt('Click all circles you were tracking · Time elapsed:', 'আপনি যে বৃত্তগুলো ট্র্যাক করছিলেন সেগুলো ক্লিক করুন · সময়:')} {sec(selectionElapsed, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}</div>
						</div>
					</div>
				{/if}
			</div>

			<!-- Tracking Arena -->
			<div class="arena-wrapper">
				<div class="arena-box" style="width: {trialData.arena_size}px; height: {trialData.arena_size}px; max-width: 100%;">
					<svg width={trialData.arena_size} height={trialData.arena_size} style="display:block; max-width:100%;">
						{#each objects as obj (obj.id)}
							{#if phase === 'selection'}
								<circle
									cx={obj.x}
									cy={obj.y}
									r={obj.radius}
									class="tracking-object selectable"
									class:selected={selectedObjects.has(obj.id)}
									role="button"
									tabindex="0"
									on:click={() => toggleObjectSelection(obj.id)}
									on:keydown={(e) => e.key === 'Enter' && toggleObjectSelection(obj.id)}
								/>
							{:else}
								<circle
									cx={obj.x}
									cy={obj.y}
									r={obj.radius}
									class="tracking-object"
									class:highlighted={obj.show_highlight}
								/>
							{/if}
						{/each}
					</svg>
				</div>
			</div>

			<!-- Submit Button (selection phase only) -->
			{#if phase === 'selection'}
				<div class="submit-row">
					<button
						class="submit-btn"
						on:click={submitSelection}
						disabled={selectedObjects.size === 0}
					>
						{lt(`Confirm ${selectedObjects.size} Selection${selectedObjects.size !== 1 ? 's' : ''}`, `${selectedObjects.size}টি নির্বাচন নিশ্চিত করুন`)}
					</button>
				</div>
			{/if}

		{:else if phase === 'results'}
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />

			<!-- Results Header -->
			<div class="results-header perf-{results?.performance || 'default'}">
				<div class="score-pill">
					<span class="score-label">{lt('Score', 'স্কোর')}</span>
					<span class="score-value">{results ? (results.score * 100).toFixed(0) : '—'}</span>
					<span class="score-max">%</span>
				</div>
				<p class="results-subtitle">
					{lt('MOT Complete', 'MOT সম্পন্ন')} ·
					{results ? performanceLabel(results.performance) : ''}
				</p>
			</div>

			{#if saveError}
				<div class="warn-card">
					{lt('Error saving results. Your progress may not have been recorded.', 'ফলাফল সংরক্ষণে ত্রুটি। অগ্রগতি রেকর্ড নাও হতে পারে।')}
				</div>
			{/if}

			{#if results}
				<!-- Key Metrics -->
				<div class="metrics-grid">
					<div class="metric-card metric-violet">
						<div class="metric-value">{n(results.score * 100, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}%</div>
						<div class="metric-label">{lt('Overall Score', 'সামগ্রিক স্কোর')}</div>
					</div>
					<div class="metric-card metric-green">
						<div class="metric-value">{results.targets_found}/{results.total_targets}</div>
						<div class="metric-label">{lt('Targets Found', 'লক্ষ্য খুঁজে পাওয়া')}</div>
					</div>
					<div class="metric-card metric-blue">
						<div class="metric-value">{n(results.accuracy * 100, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}%</div>
						<div class="metric-label">{lt('Recall Accuracy', 'রিকল নির্ভুলতা')}</div>
					</div>
					<div class="metric-card metric-amber">
						<div class="metric-value">{results.false_positives}</div>
						<div class="metric-label">{lt('False Alarms', 'মিথ্যা সংকেত')}</div>
					</div>
				</div>

				<!-- Secondary Metrics -->
				<div class="card">
					<h3 class="card-title">{lt('Detailed Analysis', 'বিস্তারিত বিশ্লেষণ')}</h3>
					<div class="analysis-grid">
						<div class="analysis-cell">
							<div class="analysis-label">{lt('Precision', 'নির্ভুলতা')}</div>
							<div class="analysis-value">{n(results.precision * 100, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}%</div>
							<div class="analysis-desc">{lt('Correct out of all selected', 'নির্বাচিতের মধ্যে সঠিক')}</div>
						</div>
						<div class="analysis-cell">
							<div class="analysis-label">{lt('F1 Score', 'F1 স্কোর')}</div>
							<div class="analysis-value">{n(results.f1_score * 100, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}%</div>
							<div class="analysis-desc">{lt('Balanced precision–recall metric', 'সুষম নির্ভুলতা–স্মরণ মেট্রিক')}</div>
						</div>
						<div class="analysis-cell">
							<div class="analysis-label">{lt('Tracking Efficiency', 'ট্র্যাকিং দক্ষতা')}</div>
							<div class="analysis-value">{n(results.tracking_efficiency * 100, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}%</div>
							<div class="analysis-desc">{results.targets_missed} {lt('missed', 'মিস')} · {results.false_positives} {lt('extra', 'অতিরিক্ত')}</div>
						</div>
						<div class="analysis-cell">
							<div class="analysis-label">{lt('Selection Time', 'নির্বাচন সময়')}</div>
							<div class="analysis-value">{sec(results.response_time, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}</div>
							<div class="analysis-desc">{lt('Time taken to identify targets', 'লক্ষ্য চিহ্নিত করতে নেওয়া সময়')}</div>
						</div>
					</div>
				</div>

				{#if results.feedback_message}
					<div class="feedback-card">
						<div class="feedback-dot"></div>
						<p class="feedback-text">{results.feedback_message}</p>
					</div>
				{/if}

				<!-- Difficulty Adaptation -->
				{#if results.new_difficulty !== results.old_difficulty || results.adaptation_reason}
					<div class="adaptation-card">
						<div class="adaptation-label">
							{#if results.new_difficulty > results.old_difficulty}
								{lt('Difficulty Increased', 'কঠিনতা বৃদ্ধি')} — {results.old_difficulty} → {results.new_difficulty}
							{:else if results.new_difficulty < results.old_difficulty}
								{lt('Difficulty Decreased', 'কঠিনতা হ্রাস')} — {results.old_difficulty} → {results.new_difficulty}
							{:else}
								{lt('Difficulty Maintained', 'কঠিনতা বজায়')} — {lt(`Level ${results.new_difficulty}`, `স্তর ${results.new_difficulty}`)}
							{/if}
						</div>
						{#if results.adaptation_reason}
							<p class="adaptation-text">{results.adaptation_reason}</p>
						{/if}
					</div>
				{/if}
			{/if}

			<!-- Action Buttons -->
			<div class="action-buttons">
				<button class="start-button" on:click={nextTrial}>
					{playMode === TASK_PLAY_MODE.PRACTICE ? lt('Finish Practice', 'অনুশীলন শেষ করুন') : lt('Next Trial', 'পরবর্তী ট্রায়াল')}
				</button>
				<button class="btn-secondary" on:click={() => goto('/dashboard')}>
					{lt('Return to Dashboard', 'ড্যাশবোর্ডে ফিরুন')}
				</button>
			</div>

		{/if}
	</div>
</div>

{#if earnedBadges.length > 0}
	<BadgeNotification badges={earnedBadges} />
{/if}

<style>
	/* ── Page Layout ─────────────────────────────────── */
	.mot-page {
		min-height: 100vh;
		background: #C8DEFA;
		padding: 1.5rem;
	}

	.mot-wrapper {
		max-width: 1100px;
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
		color: #7c3aed;
		font-weight: 500;
		margin: 0;
	}

	/* ── Error / Warn ─────────────────────────────────── */
	.error-card {
		background: #fee2e2;
		border: 2px solid #fca5a5;
		border-radius: 16px;
		padding: 2rem;
		text-align: center;
		color: #991b1b;
		margin-bottom: 1rem;
	}

	.warn-card {
		background: #fff7ed;
		border: 2px solid #fed7aa;
		border-radius: 12px;
		padding: 1rem 1.25rem;
		color: #92400e;
		font-size: 0.875rem;
		margin-bottom: 1rem;
	}

	/* ── Task Concept ─────────────────────────────────── */
	.task-concept { margin-bottom: 1rem; }

	.concept-badge {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		background: linear-gradient(135deg, #4c1d95 0%, #7c3aed 100%);
		color: white;
		padding: 0.4rem 0.9rem;
		border-radius: 2rem;
		font-size: 0.813rem;
		font-weight: 600;
		margin-bottom: 1rem;
	}

	.badge-label { font-weight: 700; letter-spacing: 0.04em; }
	.concept-desc { color: #4b5563; font-size: 0.938rem; line-height: 1.6; margin: 0; }

	/* ── Section Title ────────────────────────────────── */
	.section-title {
		font-size: 1.125rem;
		font-weight: 600;
		color: #1a1a2e;
		margin: 0 0 1rem 0;
	}

	/* ── Rules List ───────────────────────────────────── */
	.rules-list { display: flex; flex-direction: column; gap: 0.75rem; }

	.rule-item {
		display: flex;
		align-items: flex-start;
		gap: 0.875rem;
		background: #f5f3ff;
		border-radius: 10px;
		padding: 0.875rem 1rem;
	}

	.rule-num {
		min-width: 2rem;
		height: 2rem;
		background: linear-gradient(135deg, #4c1d95 0%, #7c3aed 100%);
		color: white;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.875rem;
		font-weight: 700;
		flex-shrink: 0;
	}

	.rule-text { font-size: 0.9rem; color: #374151; line-height: 1.5; }

	/* ── Info Grid ────────────────────────────────────── */
	.info-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
		margin-bottom: 1rem;
	}

	.card-title { font-size: 1rem; font-weight: 600; color: #1a1a2e; margin: 0 0 1rem 0; }

	/* ── Details List ─────────────────────────────────── */
	.details-list { display: flex; flex-direction: column; gap: 0.625rem; }

	.detail-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		font-size: 0.875rem;
		padding-bottom: 0.625rem;
		border-bottom: 1px solid #f3f4f6;
	}

	.detail-row:last-child { border-bottom: none; padding-bottom: 0; }
	.detail-row span   { color: #6b7280; }
	.detail-row strong { color: #1a1a2e; }
	.highlight-val     { color: #7c3aed; font-size: 1.125rem; }

	/* ── Expect Steps ─────────────────────────────────── */
	.expect-steps { display: flex; flex-direction: column; gap: 0.75rem; }

	.expect-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		font-size: 0.875rem;
		color: #374151;
	}

	.expect-dot {
		width: 1.25rem;
		height: 1.25rem;
		border-radius: 50%;
		flex-shrink: 0;
	}

	.dot-yellow { background: #fbbf24; border: 3px solid #f59e0b; }
	.dot-blue   { background: #60a5fa; border: 3px solid #3b82f6; }
	.dot-green  { background: #4ade80; border: 3px solid #22c55e; }

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

	.clinical-header h3 { font-size: 1rem; font-weight: 600; color: #14532d; margin: 0; }
	.clinical-info p    { font-size: 0.875rem; color: #166534; line-height: 1.6; margin: 0; }

	/* ── Arena Header Card ────────────────────────────── */
	.arena-header-card {
		background: white;
		border-radius: 16px;
		padding: 1.25rem 1.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
		margin-bottom: 1rem;
	}

	.phase-status {
		display: flex;
		align-items: center;
		gap: 1rem;
		flex-wrap: wrap;
	}

	.phase-label { font-size: 0.938rem; font-weight: 700; color: #1a1a2e; }
	.phase-desc  { font-size: 0.813rem; color: #6b7280; margin-top: 0.125rem; }

	/* Phase highlight icon */
	.dot-yellow-lg {
		width: 2.5rem;
		height: 2.5rem;
		border-radius: 50%;
		background: #fbbf24;
		border: 3px solid #f59e0b;
		box-shadow: 0 0 12px rgba(251, 191, 36, 0.6);
		animation: highlight-pulse 1s ease-in-out infinite;
		flex-shrink: 0;
	}

	/* Timer Block */
	.timer-block { text-align: center; }

	.timer-value {
		font-size: 2rem;
		font-weight: 800;
		color: #7c3aed;
		line-height: 1;
		font-variant-numeric: tabular-nums;
	}

	.timer-critical { color: #dc2626; animation: timer-pulse 0.5s ease-in-out infinite; }
	.timer-label    { font-size: 0.6875rem; color: #6b7280; }

	/* Selection Count Block */
	.selection-count-block {
		display: flex;
		align-items: baseline;
		gap: 0.125rem;
	}

	.sel-count {
		font-size: 1.75rem;
		font-weight: 800;
		color: #7c3aed;
		line-height: 1;
	}

	.sel-count.sel-complete { color: #16a34a; }
	.sel-sep   { font-size: 1rem; color: #9ca3af; margin: 0 0.1rem; }
	.sel-total { font-size: 1.25rem; font-weight: 700; color: #6b7280; }

	/* ── Arena ────────────────────────────────────────── */
	.arena-wrapper {
		display: flex;
		justify-content: center;
		margin-bottom: 1rem;
	}

	.arena-box {
		background: white;
		border-radius: 16px;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
		padding: 4px;
		overflow: hidden;
	}

	.arena-box svg {
		background: #f8f7ff;
		border-radius: 12px;
		border: 2px solid #ede9fe;
	}

	/* ── SVG Objects ─────────────────────────────────── */
	:global(.tracking-object) {
		fill: #818cf8;
		stroke: #4f46e5;
		stroke-width: 2;
	}

	:global(.tracking-object.highlighted) {
		fill: #fbbf24;
		stroke: #d97706;
		stroke-width: 3;
		filter: drop-shadow(0 0 8px rgba(251, 191, 36, 0.7));
		animation: highlight-pulse 0.8s ease-in-out infinite;
	}

	:global(.tracking-object.selectable) {
		cursor: pointer;
		fill: #a5b4fc;
		stroke: #6366f1;
		stroke-width: 2;
		transition: fill 0.15s, stroke 0.15s;
	}

	:global(.tracking-object.selectable:hover) {
		fill: #c4b5fd;
		stroke: #7c3aed;
		stroke-width: 3;
	}

	:global(.tracking-object.selected) {
		fill: #4ade80;
		stroke: #16a34a;
		stroke-width: 3;
		filter: drop-shadow(0 0 6px rgba(74, 222, 128, 0.6));
	}

	/* ── Submit Row ───────────────────────────────────── */
	.submit-row {
		display: flex;
		justify-content: center;
		margin-bottom: 1rem;
	}

	.submit-btn {
		padding: 1rem 3rem;
		background: linear-gradient(135deg, #4c1d95 0%, #7c3aed 100%);
		color: white;
		border: none;
		border-radius: 14px;
		font-size: 1.063rem;
		font-weight: 700;
		cursor: pointer;
		box-shadow: 0 4px 14px rgba(124, 58, 237, 0.4);
		transition: transform 0.15s, box-shadow 0.15s;
	}

	.submit-btn:hover:not(:disabled) {
		transform: translateY(-2px);
		box-shadow: 0 8px 20px rgba(124, 58, 237, 0.5);
	}

	.submit-btn:disabled { opacity: 0.45; cursor: not-allowed; }

	/* ── Results Header ───────────────────────────────── */
	.results-header {
		border-radius: 16px;
		padding: 1.75rem;
		text-align: center;
		margin-bottom: 1rem;
		background: linear-gradient(135deg, #4c1d95 0%, #7c3aed 100%);
		box-shadow: 0 4px 12px rgba(124, 58, 237, 0.35);
	}

	.perf-perfect    { background: linear-gradient(135deg, #92400e 0%, #d97706 100%); box-shadow: 0 4px 12px rgba(217, 119, 6, 0.4); }
	.perf-excellent  { background: linear-gradient(135deg, #14532d 0%, #16a34a 100%); box-shadow: 0 4px 12px rgba(22, 163, 74, 0.4); }
	.perf-good       { background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%); box-shadow: 0 4px 12px rgba(30, 58, 138, 0.35); }

	.score-pill {
		display: flex;
		align-items: baseline;
		justify-content: center;
		gap: 0.375rem;
		margin-bottom: 0.5rem;
	}

	.score-label { color: rgba(255, 255, 255, 0.85); font-size: 1rem; font-weight: 500; }
	.score-value { color: white; font-size: 3rem; font-weight: 700; }
	.score-max   { color: rgba(255, 255, 255, 0.7); font-size: 1.5rem; font-weight: 500; }
	.results-subtitle { color: rgba(255, 255, 255, 0.9); font-size: 0.938rem; margin: 0; }

	/* ── Metrics Grid ─────────────────────────────────── */
	.metrics-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 0.875rem;
		margin-bottom: 1rem;
	}

	.metric-card {
		background: white;
		border-radius: 16px;
		padding: 1.25rem;
		text-align: center;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
		border-top: 4px solid #e5e7eb;
	}

	.metric-violet { border-top-color: #7c3aed; }
	.metric-green  { border-top-color: #16a34a; }
	.metric-blue   { border-top-color: #1e40af; }
	.metric-amber  { border-top-color: #d97706; }

	.metric-value { font-size: 1.5rem; font-weight: 700; color: #1a1a2e; line-height: 1; }
	.metric-label { font-size: 0.75rem; color: #6b7280; margin-top: 0.375rem; }

	/* ── Analysis Grid ────────────────────────────────── */
	.analysis-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 1rem;
	}

	.analysis-cell {
		background: #f8fafc;
		border-radius: 10px;
		padding: 1rem;
		text-align: center;
	}

	.analysis-label { font-size: 0.75rem; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 0.375rem; }
	.analysis-value { font-size: 1.375rem; font-weight: 700; color: #1a1a2e; margin-bottom: 0.25rem; }
	.analysis-desc  { font-size: 0.75rem; color: #9ca3af; line-height: 1.4; }

	/* ── Feedback Card ────────────────────────────────── */
	.feedback-card {
		display: flex;
		align-items: flex-start;
		gap: 1rem;
		background: #f0fdf4;
		border: 1px solid #bbf7d0;
		border-radius: 12px;
		padding: 1.25rem;
		margin-bottom: 1rem;
	}

	.feedback-dot {
		width: 0.5rem;
		height: 0.5rem;
		border-radius: 50%;
		background: #16a34a;
		flex-shrink: 0;
		margin-top: 0.375rem;
	}

	.feedback-text { font-size: 0.938rem; color: #166534; line-height: 1.6; margin: 0; }

	/* ── Adaptation Card ──────────────────────────────── */
	.adaptation-card {
		background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
		border: 1px solid #ddd6fe;
		border-radius: 16px;
		padding: 1.25rem 1.5rem;
		margin-bottom: 1rem;
	}

	.adaptation-label { font-size: 0.875rem; font-weight: 700; color: #4c1d95; margin-bottom: 0.375rem; }
	.adaptation-text  { font-size: 0.875rem; color: #7c3aed; margin: 0; line-height: 1.5; }

	/* ── Action Buttons ───────────────────────────────── */
	.action-buttons { display: flex; gap: 1rem; margin-top: 1rem; }

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

	.action-buttons .btn-secondary { flex: 1; }
	.btn-secondary:hover { background: #f5f3ff; transform: translateY(-2px); }

	/* ── Animations ───────────────────────────────────── */
	@keyframes highlight-pulse {
		0%, 100% { transform: scale(1); opacity: 1; }
		50%       { transform: scale(1.15); opacity: 0.85; }
	}

	@keyframes timer-pulse {
		0%, 100% { transform: scale(1); opacity: 1; }
		50%       { transform: scale(1.08); opacity: 0.8; }
	}

	/* ── Responsive ───────────────────────────────────── */
	@media (max-width: 768px) {
		.info-grid      { grid-template-columns: 1fr; }
		.metrics-grid   { grid-template-columns: 1fr 1fr; }
		.analysis-grid  { grid-template-columns: 1fr 1fr; }
		.action-buttons { flex-direction: column; }
		.phase-status   { gap: 0.75rem; }
	}
</style>

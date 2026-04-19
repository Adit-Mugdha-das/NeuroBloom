<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { API_BASE_URL } from '$lib/api';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
import TaskReturnButton from '$lib/components/TaskReturnButton.svelte';
	import { locale, localeText } from '$lib/i18n';
	import { user } from '$lib/stores';
	import { buildPracticePayload, getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
import { TASK_RETURN_CONTEXT } from '$lib/task-navigation';
	import { onDestroy, onMount } from 'svelte';

	// ── State ─────────────────────────────────────────
	let gamePhase = 'loading'; // loading | intro | playing | results
	let trialData = null;
	let difficulty = 5;
	let searchType = 'conjunction';
	let items = [];
	let targetItem = null;
	let setSize = 0;
	let timeLimit = 30;
	let timeRemaining = 0;
	let startTime = null;
	let timerInterval = null;
	let taskId = null;

	let userAnswer = null; // true = present, false = absent
	let results = null;
	let earnedBadges = [];
	/** @type {"practice" | "recorded"} */
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';
	let recordedTrialData = null;
	let recordedDifficulty = 5;

	let loadError = false;
	let saveError = false;

	// ── Helpers ───────────────────────────────────────
	function lt(en, bn) {
		return localeText({ en, bn }, $locale);
	}

	function cloneData(value) {
		if (typeof structuredClone === 'function') return structuredClone(value);
		return JSON.parse(JSON.stringify(value));
	}

	function applyTrialView(data) {
		trialData = data;
		items = data.items;
		targetItem = data.target;
		searchType = data.search_type || 'conjunction';
		setSize = data.set_size;
		timeLimit = data.time_limit;
		timeRemaining = timeLimit;
	}

	function getColorValue(colorName) {
		const map = {
			red:    '#DC2626',
			blue:   '#2563EB',
			green:  '#16A34A',
			yellow: '#EAB308',
			purple: '#9333EA',
			orange: '#EA580C'
		};
		return map[colorName] || '#6B7280';
	}

	function getShapePath(shape) {
		const paths = {
			circle:   'M 50 50 m -25 0 a 25 25 0 1 0 50 0 a 25 25 0 1 0 -50 0',
			square:   'M 25 25 L 75 25 L 75 75 L 25 75 Z',
			triangle: 'M 50 25 L 75 75 L 25 75 Z',
			diamond:  'M 50 25 L 75 50 L 50 75 L 25 50 Z'
		};
		return paths[shape] || paths.circle;
	}

	function getShapeDisplay(shape) {
		const names = { circle: 'Circle', square: 'Square', triangle: 'Triangle', diamond: 'Diamond' };
		return names[shape] || shape;
	}

	function getColorDisplay(color) {
		return color.charAt(0).toUpperCase() + color.slice(1);
	}

	function performanceLabel(p) {
		const map = {
			excellent:         lt('Excellent', 'অসাধারণ'),
			good:              lt('Good', 'ভালো'),
			average:           lt('Average', 'মোটামুটি'),
			needs_improvement: lt('Needs Improvement', 'উন্নতি দরকার')
		};
		return map[p] || (p || '').replace('_', ' ');
	}

	function responseTypeLabel(rt) {
		const map = {
			hit:               lt('Hit', 'হিট'),
			miss:              lt('Miss', 'মিস'),
			false_alarm:       lt('False Alarm', 'মিথ্যা সংকেত'),
			correct_rejection: lt('Correct Rejection', 'সঠিক প্রত্যাখ্যান')
		};
		return map[rt] || (rt || '').replace('_', ' ');
	}

	function timerClass() {
		if (timeRemaining < 5)  return 'timer-critical';
		if (timeRemaining < 10) return 'timer-warning';
		return '';
	}

	// ── Lifecycle ──────────────────────────────────────
	onMount(() => {
		if (!$user) { goto('/login'); return; }
		taskId = $page.url.searchParams.get('taskId');
		loadTrial();
	});

	onDestroy(() => {
		if (timerInterval) clearInterval(timerInterval);
	});

	// ── Game Logic ─────────────────────────────────────
	async function loadTrial() {
		try {
			loadError = false;
			const response = await fetch(
				`${API_BASE_URL}/api/training/tasks/visual-search/generate/${$user.id}`,
				{ method: 'GET', headers: { 'Content-Type': 'application/json' }, credentials: 'include' }
			);
			if (!response.ok) throw new Error('Failed to load trial');
			const data = await response.json();
			recordedTrialData = cloneData(data.trial_data);
			recordedDifficulty = data.difficulty;
			difficulty = recordedDifficulty;
			applyTrialView(cloneData(recordedTrialData));
			gamePhase = 'intro';
		} catch (_) {
			loadError = true;
			gamePhase = 'intro';
		}
	}

	/** @param {"practice" | "recorded"} nextMode */
	function startGame(nextMode = TASK_PLAY_MODE.RECORDED) {
		if (timerInterval) {
			clearInterval(timerInterval);
			timerInterval = null;
		}

		playMode = nextMode;
		practiceStatusMessage = '';
		difficulty = recordedDifficulty;
		if (playMode === TASK_PLAY_MODE.PRACTICE && recordedTrialData) {
			applyTrialView(buildPracticePayload('visual-search', recordedTrialData));
		} else if (recordedTrialData) {
			applyTrialView(cloneData(recordedTrialData));
		}
		startTime = Date.now();
		userAnswer = null;
		gamePhase = 'playing';
		timerInterval = setInterval(() => {
			const elapsed = (Date.now() - startTime) / 1000;
			timeRemaining = Math.max(0, timeLimit - elapsed);
			if (timeRemaining === 0) handleResponse(false);
		}, 100);
	}

	async function leavePractice(completed = false) {
		if (timerInterval) {
			clearInterval(timerInterval);
			timerInterval = null;
		}

		playMode = TASK_PLAY_MODE.RECORDED;
		practiceStatusMessage = completed ? getPracticeCopy($locale).complete : '';
		results = null;
		userAnswer = null;
		difficulty = recordedDifficulty;

		if (completed) {
			gamePhase = 'loading';
			await loadTrial();
			return;
		}

		if (recordedTrialData) {
			applyTrialView(cloneData(recordedTrialData));
		}
		gamePhase = 'intro';
	}

	function handleResponse(answer) {
		if (userAnswer !== null) return;
		userAnswer = answer;
		if (timerInterval) { clearInterval(timerInterval); timerInterval = null; }
		submitResults();
	}

	async function submitResults() {
		if (playMode === TASK_PLAY_MODE.PRACTICE) {
			await leavePractice(true);
			return;
		}
		saveError = false;
		const reactionTime = (Date.now() - startTime) / 1000;
		try {
			const response = await fetch(
				`${API_BASE_URL}/api/training/tasks/visual-search/submit/${$user.id}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					credentials: 'include',
					body: JSON.stringify({
						trial_data: trialData,
						user_response: { target_found: userAnswer, reaction_time: reactionTime },
						task_id: taskId
					})
				}
			);
			if (!response.ok) throw new Error('Failed to submit results');
			const data = await response.json();
			results = data;
			earnedBadges = data.new_badges || [];
			gamePhase = 'results';
		} catch (_) {
			saveError = true;
			gamePhase = 'results';
		}
	}

	function retryTask() {
		gamePhase = 'loading';
		results = null;
		earnedBadges = [];
		userAnswer = null;
		loadTrial();
	}
</script>

<div class="fcs-page" data-localize-skip>
	<div class="fcs-wrapper">

		{#if gamePhase === 'loading'}
			<LoadingSkeleton />

		{:else if gamePhase === 'intro'}
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />

			<!-- Header Card -->
			<div class="header-card">
				<div class="header-content">
					<div class="header-text">
						<h1 class="task-title">{lt('Conjunction Search', 'কনজাংশন সার্চ')}</h1>
						<p class="task-domain">{lt('Visual Scanning · Serial Attention', 'ভিজ্যুয়াল স্ক্যানিং · সিরিয়াল মনোযোগ')}</p>
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
			{:else if targetItem}

				<!-- Task Concept -->
				<div class="card task-concept">
					<div class="concept-badge">
						<span class="badge-label">{lt('Conjunction Search', 'কনজাংশন সার্চ')}</span>
						<span>{lt('Treisman & Gelade, 1980', 'Treisman & Gelade, 1980')}</span>
					</div>
					<p class="concept-desc">
						{lt(
							'Conjunction Search requires matching BOTH color and shape simultaneously. Unlike feature search (where a unique attribute pops out instantly), you must inspect each item individually — a serial process that places high demand on focused visual attention and is disproportionately affected by MS-related attention deficits.',
							'কনজাংশন সার্চে রঙ এবং আকার উভয়ই মেলাতে হবে। ফিচার সার্চের বিপরীতে, প্রতিটি আইটেম পৃথকভাবে পরীক্ষা করতে হয় — MS-সংক্রান্ত মনোযোগের ঘাটতিতে বিশেষভাবে সংবেদনশীল।'
						)}
					</p>
				</div>

				<!-- Target Display -->
				<div class="card">
					<h2 class="section-title">{lt('Your Target', 'আপনার লক্ষ্য')}</h2>
					<p class="target-subtext">{lt('Find and confirm the presence or absence of this exact item — it must match BOTH attributes:', 'এই নির্দিষ্ট আইটেমটি আছে কি নেই নিশ্চিত করুন — উভয় বৈশিষ্ট্য মেলাতে হবে:')}</p>
					<div class="target-showcase">
						<div class="target-svg-wrap">
							<svg width="100" height="100" viewBox="0 0 100 100">
								<path
									d={getShapePath(targetItem.shape)}
									fill={getColorValue(targetItem.color)}
									stroke="#1F2937"
									stroke-width="3"
								/>
							</svg>
						</div>
						<div class="target-label-group">
							<div class="target-name">{getColorDisplay(targetItem.color)} {getShapeDisplay(targetItem.shape)}</div>
							<div class="target-attrs">
								<span class="attr-chip color-chip" style="background: {getColorValue(targetItem.color)}20; border-color: {getColorValue(targetItem.color)};">
									{getColorDisplay(targetItem.color)}
								</span>
								<span class="attr-chip shape-chip">
									{getShapeDisplay(targetItem.shape)}
								</span>
							</div>
							<div class="match-note">{lt('Must match BOTH color + shape', 'রঙ + আকার উভয়ই মেলাতে হবে')}</div>
						</div>
					</div>
				</div>

				<!-- Rules Card -->
				<div class="card">
					<h2 class="section-title">{lt('Rules', 'নিয়মাবলী')}</h2>
					<div class="rules-list">
						<div class="rule-item">
							<div class="rule-num">1</div>
							<div class="rule-text">{lt('Study the target — remember BOTH its color and shape', 'লক্ষ্যটি মনে রাখুন — রঙ এবং আকার উভয়ই')}</div>
						</div>
						<div class="rule-item">
							<div class="rule-num">2</div>
							<div class="rule-text">{lt('Search the display carefully — distractors share one attribute with the target — scan item by item', 'মনোযোগ দিয়ে স্ক্যান করুন — ডিস্ট্র্যাক্টররা একটি বৈশিষ্ট্য শেয়ার করে')}</div>
						</div>
						<div class="rule-item">
							<div class="rule-num">3</div>
							<div class="rule-text">{lt('Respond as quickly and accurately as possible — both speed and accuracy count', 'দ্রুত ও নির্ভুলভাবে উত্তর দিন — গতি এবং নির্ভুলতা উভয়ই গুরুত্বপূর্ণ')}</div>
						</div>
						<div class="rule-item">
							<div class="rule-num">4</div>
							<div class="rule-text">{lt(`You have ${timeLimit} seconds — if time runs out, it counts as absent`, `আপনার ${timeLimit} সেকেন্ড আছে — সময় শেষ হলে অনুপস্থিত হিসেবে`)}</div>
						</div>
					</div>
				</div>

				<!-- Info Grid -->
				<div class="info-grid">
					<!-- Task Details -->
					<div class="card">
						<h3 class="card-title">{lt('Task Details', 'টাস্কের বিবরণ')}</h3>
						<div class="details-list">
							<div class="detail-row">
								<span>{lt('Search Mode', 'সার্চ মোড')}</span>
								<strong class="type-conjunction">{lt('Conjunction', 'কনজাংশন')}</strong>
							</div>
							<div class="detail-row">
								<span>{lt('Display Items', 'প্রদর্শিত আইটেম')}</span>
								<strong>{setSize}</strong>
							</div>
							<div class="detail-row">
								<span>{lt('Time Limit', 'সময়সীমা')}</span>
								<strong>{timeLimit}s</strong>
							</div>
							<div class="detail-row">
								<span>{lt('Difficulty', 'কঠিনতা')}</span>
								<strong>{lt(`Level ${difficulty} / 10`, `স্তর ${difficulty} / ১০`)}</strong>
							</div>
						</div>
					</div>
					<!-- Strategy Hint -->
					<div class="card">
						<h3 class="card-title">{lt('Search Strategy', 'সার্চ কৌশল')}</h3>
						<div class="strategy-box">
							<div class="strategy-label">{lt('Serial Inspection Required', 'সিরিয়াল পরীক্ষা প্রয়োজন')}</div>
							<p class="strategy-text">{lt('Distractors match ONE attribute of the target. Scan row by row — look for the item matching both color AND shape simultaneously.', 'ডিস্ট্র্যাক্টর একটি বৈশিষ্ট্য মেলায়। সারি সারি স্ক্যান করুন।')}</p>
							<div class="strategy-benchmark">{lt('Benchmark: < 30 ms per item (serial)', 'বেঞ্চমার্ক: আইটেম প্রতি < ৩০ ms')}</div>
						</div>
					</div>
				</div>

				<!-- Clinical Basis -->
				<div class="clinical-info">
					<div class="clinical-header">
						<div class="clinical-badge">{lt('Clinical Basis', 'ক্লিনিকাল ভিত্তি')}</div>
						<h3>{lt('MS-Sensitive Serial Visual Attention', 'MS-সংবেদনশীল সিরিয়াল ভিজ্যুয়াল মনোযোগ')}</h3>
					</div>
					<p>
						{lt(
							'Conjunction search is disproportionately impaired in MS compared to feature search (Treisman & Gelade, 1980). White matter lesion load reduces attentional capacity and slows interhemispheric integration, extending search slopes beyond healthy norms. Tracking conjunction search slope across sessions provides a sensitive index of MS burden on visual cognition.',
							'কনজাংশন সার্চ MS-এ ফিচার সার্চের তুলনায় অসামঞ্জস্যভাবে ক্ষতিগ্রস্ত হয়। শ্বেত পদার্থের ক্ষত মনোযোগ ক্ষমতা হ্রাস করে এবং ইন্টারহেমিস্ফেরিক ইন্টিগ্রেশন ধীর করে।'
						)}
					</p>
				</div>

				<TaskPracticeActions
					locale={$locale}
					startLabel={lt('Begin Conjunction Search', 'কনজাংশন সার্চ শুরু করুন')}
					statusMessage={practiceStatusMessage}
					on:start={() => startGame(TASK_PLAY_MODE.RECORDED)}
					on:practice={() => startGame(TASK_PLAY_MODE.PRACTICE)}
				/>

			{:else}
				<LoadingSkeleton />
			{/if}

		{:else if gamePhase === 'playing'}

			<div class="game-card">
				{#if playMode === TASK_PLAY_MODE.PRACTICE}
					<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
				{/if}

				<!-- Game Status Bar -->
				<div class="game-status-bar">
					<div class="target-reference">
						<span class="ref-label">{lt('Looking for:', 'খুঁজছি:')}</span>
						<div class="ref-item">
							<svg width="40" height="40" viewBox="0 0 100 100">
								<path
									d={getShapePath(targetItem.shape)}
									fill={getColorValue(targetItem.color)}
									stroke="#1F2937"
									stroke-width="3"
								/>
							</svg>
							<span class="ref-name">{getColorDisplay(targetItem.color)} {getShapeDisplay(targetItem.shape)}</span>
						</div>
						<div class="search-type-tag">{lt('Conjunction', 'কনজাংশন')}</div>
					</div>
					<div class="timer-block">
						<div class="timer-value {timerClass()}">{Math.ceil(timeRemaining)}</div>
						<div class="timer-label">{lt('seconds', 'সেকেন্ড')}</div>
					</div>
				</div>

				<!-- Search Arena -->
				<div class="search-arena">
					{#each items as item}
						<div
							class="search-item"
							style="left: {item.position.x * 90 + 5}%; top: {item.position.y * 90 + 5}%;"
						>
							<svg width="45" height="45" viewBox="0 0 100 100">
								<path
									d={getShapePath(item.shape)}
									fill={getColorValue(item.color)}
									stroke="#374151"
									stroke-width="2.5"
								/>
							</svg>
						</div>
					{/each}
				</div>

				<!-- Response Buttons -->
				<div class="response-section">
					<p class="response-prompt">{lt('Is the target present in the display?', 'ডিসপ্লেতে লক্ষ্যটি আছে কি?')}</p>
					<div class="response-buttons">
						<button class="resp-btn resp-present" on:click={() => handleResponse(true)}>
							<span class="resp-icon resp-check">✓</span>
							<span>{lt('Target Present', 'লক্ষ্য আছে')}</span>
						</button>
						<button class="resp-btn resp-absent" on:click={() => handleResponse(false)}>
							<span class="resp-icon resp-cross">✕</span>
							<span>{lt('Target Absent', 'লক্ষ্য নেই')}</span>
						</button>
					</div>
				</div>
			</div>

		{:else if gamePhase === 'results'}
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />

			<!-- Results Header -->
			<div class="results-header {results && results.correct ? 'header-correct' : 'header-incorrect'}">
				<div class="score-pill">
					<span class="score-label">{lt('Score', 'স্কোর')}</span>
					<span class="score-value">{results ? (results.score * 100).toFixed(0) : '—'}</span>
					<span class="score-max">%</span>
				</div>
				<p class="results-subtitle">
					{lt('Conjunction Search Complete', 'কনজাংশন সার্চ সম্পন্ন')} ·
					{results ? (results.correct ? lt('Correct', 'সঠিক') : lt('Incorrect', 'ভুল')) : ''}
				</p>
			</div>

			{#if saveError}
				<div class="warn-card">
					{lt('Error saving results. Your progress may not have been recorded.', 'ফলাফল সংরক্ষণে ত্রুটি।')}
				</div>
			{/if}

			{#if results}
				<!-- Key Metrics -->
				<div class="metrics-grid">
					<div class="metric-card {results.correct ? 'metric-green' : 'metric-red'}">
						<div class="metric-value">{results.correct ? lt('Yes', 'হ্যাঁ') : lt('No', 'না')}</div>
						<div class="metric-label">{lt('Correct', 'সঠিক')}</div>
					</div>
					<div class="metric-card metric-amber">
						<div class="metric-value">{(results.score * 100).toFixed(0)}%</div>
						<div class="metric-label">{lt('Score', 'স্কোর')}</div>
					</div>
					<div class="metric-card metric-orange">
						<div class="metric-value">{results.reaction_time.toFixed(2)}s</div>
						<div class="metric-label">{lt('Reaction Time', 'প্রতিক্রিয়া সময়')}</div>
					</div>
					<div class="metric-card metric-slate">
						<div class="metric-value response-type-text">{responseTypeLabel(results.response_type)}</div>
						<div class="metric-label">{lt('Response Type', 'প্রতিক্রিয়ার ধরন')}</div>
					</div>
				</div>

				<!-- Performance Analysis -->
				<div class="card">
					<h3 class="card-title">{lt('Performance Analysis', 'পারফরম্যান্স বিশ্লেষণ')}</h3>
					<div class="analysis-grid">
						<div class="analysis-cell">
							<div class="analysis-label">{lt('Search Efficiency', 'সার্চ দক্ষতা')}</div>
							<div class="analysis-value">{results.search_efficiency.toFixed(3)}s/item</div>
							<div class="analysis-desc">{lt('Time spent per display item', 'প্রতিটি আইটেমে ব্যয়িত সময়')}</div>
						</div>
						<div class="analysis-cell">
							<div class="analysis-label">{lt('Search Slope', 'সার্চ স্লোপ')}</div>
							<div class="analysis-value">{results.search_slope_ms.toFixed(1)} ms/item</div>
							<div class="analysis-desc">{lt('Conjunction target: < 30 ms = excellent (serial)', 'কনজাংশন: < ৩০ ms = অসাধারণ')}</div>
						</div>
						<div class="analysis-cell">
							<div class="analysis-label">{lt('Rating', 'রেটিং')}</div>
							<div class="analysis-value perf-{results.performance}">{performanceLabel(results.performance)}</div>
							<div class="analysis-desc">{lt('Overall performance classification', 'সামগ্রিক পারফরম্যান্স শ্রেণীবিভাগ')}</div>
						</div>
					</div>
				</div>

				<!-- Trial Summary -->
				<div class="card">
					<h3 class="card-title">{lt('Trial Summary', 'ট্রায়াল সারাংশ')}</h3>
					<div class="details-list">
						<div class="detail-row">
							<span>{lt('Search Mode', 'সার্চ মোড')}</span>
							<strong class="type-conjunction">{lt('Conjunction Search', 'কনজাংশন সার্চ')}</strong>
						</div>
						<div class="detail-row">
							<span>{lt('Set Size', 'সেট সাইজ')}</span>
							<strong>{results.set_size} {lt('items', 'আইটেম')}</strong>
						</div>
						<div class="detail-row">
							<span>{lt('Target Was', 'লক্ষ্য ছিল')}</span>
							<strong>{results.target_present ? lt('Present', 'উপস্থিত') : lt('Absent', 'অনুপস্থিত')}</strong>
						</div>
						<div class="detail-row">
							<span>{lt('Your Response', 'আপনার উত্তর')}</span>
							<strong>{results.user_answer ? lt('Present', 'উপস্থিত') : lt('Absent', 'অনুপস্থিত')}</strong>
						</div>
					</div>
				</div>

				<!-- Difficulty Adjustment -->
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
					<p class="adaptation-text">{results.adaptation_reason}</p>
				</div>
			{/if}

			<!-- Action Buttons -->
			<div class="action-buttons">
				<button class="start-button" on:click={() => goto('/dashboard')}>
					{lt('Return to Dashboard', 'ড্যাশবোর্ডে ফিরুন')}
				</button>
				<button class="btn-secondary" on:click={retryTask}>
					{lt('Try Again', 'আবার চেষ্টা করুন')}
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
	.fcs-page {
		min-height: 100vh;
		background: #C8DEFA;
		padding: 1.5rem;
	}

	.fcs-wrapper {
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
		color: #92400e;
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
		background: linear-gradient(135deg, #92400e 0%, #d97706 100%);
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
		margin: 0 0 0.625rem 0;
	}

	.target-subtext { color: #6b7280; font-size: 0.875rem; margin: 0 0 1rem 0; }

	/* ── Target Showcase ──────────────────────────────── */
	.target-showcase {
		display: flex;
		align-items: center;
		gap: 1.5rem;
		background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
		border: 2px solid #fcd34d;
		border-radius: 12px;
		padding: 1.5rem;
	}

	.target-svg-wrap {
		filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.12));
		flex-shrink: 0;
	}

	.target-name {
		font-size: 1.4rem;
		font-weight: 700;
		color: #78350f;
		margin-bottom: 0.625rem;
	}

	.target-attrs { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.5rem; }

	.attr-chip {
		padding: 0.25rem 0.75rem;
		border-radius: 1rem;
		font-size: 0.813rem;
		font-weight: 600;
		border: 2px solid transparent;
	}

	.shape-chip { background: #fff7ed; border-color: #fcd34d; color: #78350f; }

	.match-note {
		font-size: 0.75rem;
		font-weight: 700;
		color: #92400e;
		background: #fef3c7;
		border: 1px solid #fcd34d;
		border-radius: 0.5rem;
		padding: 0.25rem 0.625rem;
		display: inline-block;
	}

	/* ── Rules List ───────────────────────────────────── */
	.rules-list { display: flex; flex-direction: column; gap: 0.75rem; }

	.rule-item {
		display: flex;
		align-items: flex-start;
		gap: 0.875rem;
		background: #fff7ed;
		border-radius: 10px;
		padding: 0.875rem 1rem;
	}

	.rule-num {
		min-width: 2rem;
		height: 2rem;
		background: linear-gradient(135deg, #92400e 0%, #d97706 100%);
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
	.detail-row strong { color: #1a1a2e; text-align: right; max-width: 65%; }

	.type-conjunction { color: #92400e; font-weight: 700; }

	/* ── Strategy Box ─────────────────────────────────── */
	.strategy-box {
		background: #fef3c7;
		border: 2px solid #fcd34d;
		border-radius: 10px;
		padding: 1rem 1.125rem;
	}

	.strategy-label {
		font-size: 0.875rem;
		font-weight: 700;
		color: #92400e;
		margin-bottom: 0.375rem;
	}

	.strategy-text {
		font-size: 0.875rem;
		line-height: 1.5;
		color: #78350f;
		margin: 0 0 0.625rem 0;
	}

	.strategy-benchmark {
		font-size: 0.75rem;
		font-weight: 600;
		background: #fde68a;
		color: #78350f;
		padding: 0.25rem 0.625rem;
		border-radius: 0.5rem;
		display: inline-block;
	}

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

	/* ── Game Card ────────────────────────────────────── */
	.game-card {
		background: white;
		border-radius: 16px;
		padding: 1.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
	}

	/* ── Game Status Bar ──────────────────────────────── */
	.game-status-bar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		margin-bottom: 1.25rem;
		flex-wrap: wrap;
	}

	.target-reference {
		display: flex;
		align-items: center;
		gap: 1rem;
		flex-wrap: wrap;
	}

	.ref-label { font-size: 0.875rem; font-weight: 700; color: #92400e; }

	.ref-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		background: #fff7ed;
		padding: 0.375rem 0.875rem;
		border-radius: 0.625rem;
		border: 2px solid #fcd34d;
	}

	.ref-name { font-size: 0.938rem; font-weight: 600; color: #78350f; }

	.search-type-tag {
		padding: 0.25rem 0.75rem;
		border-radius: 1rem;
		font-size: 0.813rem;
		font-weight: 700;
		background: #fef3c7;
		color: #92400e;
	}

	/* ── Timer ────────────────────────────────────────── */
	.timer-block { text-align: center; }

	.timer-value {
		font-size: 2.5rem;
		font-weight: 800;
		color: #d97706;
		line-height: 1;
		font-variant-numeric: tabular-nums;
	}

	.timer-warning  { color: #d97706; animation: timer-pulse 1s ease-in-out infinite; }
	.timer-critical { color: #dc2626; animation: timer-pulse 0.5s ease-in-out infinite; }
	.timer-label    { font-size: 0.75rem; color: #6b7280; margin-top: 0.125rem; }

	/* ── Search Arena ─────────────────────────────────── */
	.search-arena {
		position: relative;
		width: 100%;
		height: 65vh;
		min-height: 480px;
		background: white;
		border: 3px solid #fde68a;
		border-radius: 16px;
		overflow: hidden;
		margin-bottom: 1.5rem;
		box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.04);
	}

	.search-item {
		position: absolute;
		transform: translate(-50%, -50%);
	}

	/* ── Response Section ─────────────────────────────── */
	.response-section { text-align: center; }

	.response-prompt {
		font-size: 1.125rem;
		font-weight: 600;
		color: #1a1a2e;
		margin: 0 0 1.25rem 0;
	}

	.response-buttons {
		display: flex;
		justify-content: center;
		gap: 1.5rem;
		flex-wrap: wrap;
	}

	.resp-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.625rem;
		padding: 1.25rem 3rem;
		font-size: 1.125rem;
		font-weight: 700;
		border: none;
		border-radius: 14px;
		cursor: pointer;
		min-width: 210px;
		transition: transform 0.15s, box-shadow 0.15s;
	}

	.resp-btn:hover { transform: translateY(-3px); }

	.resp-present {
		background: linear-gradient(135deg, #16a34a 0%, #22c55e 100%);
		color: white;
		box-shadow: 0 4px 14px rgba(22, 163, 74, 0.35);
	}

	.resp-present:hover { box-shadow: 0 8px 20px rgba(22, 163, 74, 0.45); }

	.resp-absent {
		background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
		color: white;
		box-shadow: 0 4px 14px rgba(220, 38, 38, 0.35);
	}

	.resp-absent:hover { box-shadow: 0 8px 20px rgba(220, 38, 38, 0.45); }

	.resp-icon { font-size: 1.375rem; font-weight: 700; }
	.resp-check { color: #bbf7d0; }
	.resp-cross { color: #fecaca; }

	/* ── Results Header ───────────────────────────────── */
	.results-header {
		border-radius: 16px;
		padding: 1.75rem;
		text-align: center;
		margin-bottom: 1rem;
	}

	.header-correct   { background: linear-gradient(135deg, #15803d 0%, #16a34a 100%); box-shadow: 0 4px 12px rgba(21, 128, 61, 0.35); }
	.header-incorrect { background: linear-gradient(135deg, #92400e 0%, #d97706 100%); box-shadow: 0 4px 12px rgba(146, 64, 14, 0.35); }

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

	.metric-green  { border-top-color: #16a34a; }
	.metric-red    { border-top-color: #dc2626; }
	.metric-amber  { border-top-color: #d97706; }
	.metric-orange { border-top-color: #ea580c; }
	.metric-slate  { border-top-color: #64748b; }

	.metric-value { font-size: 1.5rem; font-weight: 700; color: #1a1a2e; line-height: 1; }
	.metric-label { font-size: 0.75rem; color: #6b7280; margin-top: 0.375rem; }
	.response-type-text { font-size: 1.1rem; }

	/* ── Performance Analysis Grid ────────────────────── */
	.analysis-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
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

	.perf-excellent          { color: #16a34a; }
	.perf-good               { color: #d97706; }
	.perf-average            { color: #ea580c; }
	.perf-needs_improvement  { color: #dc2626; }

	/* ── Adaptation Card ──────────────────────────────── */
	.adaptation-card {
		background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
		border: 1px solid #fcd34d;
		border-radius: 16px;
		padding: 1.25rem 1.5rem;
		margin-bottom: 1rem;
	}

	.adaptation-label { font-size: 0.875rem; font-weight: 700; color: #92400e; margin-bottom: 0.375rem; }
	.adaptation-text  { font-size: 0.875rem; color: #78350f; margin: 0; line-height: 1.5; }

	/* ── Action Buttons ───────────────────────────────── */
	.action-buttons { display: flex; gap: 1rem; margin-top: 1rem; }

	.start-button {
		flex: 1;
		background: #d97706;
		color: white;
		border: none;
		border-radius: 12px;
		padding: 1rem;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		box-shadow: 0 4px 12px rgba(217, 119, 6, 0.35);
		transition: transform 0.15s;
	}

	.start-button:hover { transform: translateY(-2px); }

	.btn-secondary {
		flex: 1;
		background: white;
		color: #d97706;
		border: 2px solid #d97706;
		border-radius: 12px;
		padding: 1rem;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: transform 0.15s, background 0.15s;
	}

	.btn-secondary:hover { background: #fff7ed; transform: translateY(-2px); }

	/* ── Animations ───────────────────────────────────── */
	@keyframes timer-pulse {
		0%, 100% { transform: scale(1); opacity: 1; }
		50%       { transform: scale(1.06); opacity: 0.8; }
	}

	/* ── Responsive ───────────────────────────────────── */
	@media (max-width: 768px) {
		.info-grid       { grid-template-columns: 1fr; }
		.metrics-grid    { grid-template-columns: 1fr 1fr; }
		.analysis-grid   { grid-template-columns: 1fr; }
		.response-buttons { flex-direction: column; align-items: center; }
		.resp-btn        { width: 100%; max-width: 360px; }
		.action-buttons  { flex-direction: column; }
		.game-status-bar { flex-direction: column; align-items: flex-start; }
		.search-arena    { height: 50vh; min-height: 320px; }
	}
</style>


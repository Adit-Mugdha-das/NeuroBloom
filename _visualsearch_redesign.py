#!/usr/bin/env python3
"""Redesign Visual Search UI to LNS design system (deep blue #1e40af)."""

CONTENT = """\
<script>
\timport { goto } from '$app/navigation';
\timport { page } from '$app/stores';
\timport { API_BASE_URL } from '$lib/api';
\timport BadgeNotification from '$lib/components/BadgeNotification.svelte';
\timport DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
\timport LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
\timport PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
\timport TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
\timport { locale, localeText } from '$lib/i18n';
\timport { buildPracticePayload, getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
\timport { user } from '$lib/stores';
\timport { onDestroy, onMount } from 'svelte';

\t// ── State ─────────────────────────────────────────
\tlet gamePhase = 'loading'; // loading | intro | playing | results
\tlet trialData = null;
\tlet difficulty = 5;
\tlet searchType = 'feature';
\tlet items = [];
\tlet targetItem = null;
\tlet setSize = 0;
\tlet timeLimit = 30;
\tlet timeRemaining = 0;
\tlet startTime = null;
\tlet timerInterval = null;
\tlet taskId = null;

\tlet userAnswer = null; // true = present, false = absent
\tlet results = null;
\tlet earnedBadges = [];
\tlet playMode = TASK_PLAY_MODE.RECORDED;
\tlet practiceStatusMessage = '';
\tlet recordedTrialData = null;
\tlet recordedDifficulty = 5;

\tlet loadError = false;
\tlet saveError = false;

\t// ── Helpers ───────────────────────────────────────
\tfunction lt(en, bn) {
\t\treturn localeText({ en, bn }, $locale);
\t}

\tfunction cloneData(value) {
\t\tif (typeof structuredClone === 'function') return structuredClone(value);
\t\treturn JSON.parse(JSON.stringify(value));
\t}

\tfunction applyTrialView(data) {
\t\ttrialData = data;
\t\titems = data.items;
\t\ttargetItem = data.target;
\t\tsearchType = data.search_type;
\t\tsetSize = data.set_size;
\t\ttimeLimit = data.time_limit;
\t\ttimeRemaining = timeLimit;
\t}

\tfunction getColorValue(colorName) {
\t\tconst map = {
\t\t\tred:    '#DC2626',
\t\t\tblue:   '#2563EB',
\t\t\tgreen:  '#16A34A',
\t\t\tyellow: '#EAB308',
\t\t\tpurple: '#9333EA',
\t\t\torange: '#EA580C'
\t\t};
\t\treturn map[colorName] || '#6B7280';
\t}

\tfunction getShapePath(shape) {
\t\tconst paths = {
\t\t\tcircle:   'M 50 50 m -25 0 a 25 25 0 1 0 50 0 a 25 25 0 1 0 -50 0',
\t\t\tsquare:   'M 25 25 L 75 25 L 75 75 L 25 75 Z',
\t\t\ttriangle: 'M 50 25 L 75 75 L 25 75 Z',
\t\t\tdiamond:  'M 50 25 L 75 50 L 50 75 L 25 50 Z'
\t\t};
\t\treturn paths[shape] || paths.circle;
\t}

\tfunction getShapeDisplay(shape) {
\t\tconst names = { circle: 'Circle', square: 'Square', triangle: 'Triangle', diamond: 'Diamond' };
\t\treturn names[shape] || shape;
\t}

\tfunction getColorDisplay(color) {
\t\treturn color.charAt(0).toUpperCase() + color.slice(1);
\t}

\tfunction performanceLabel(p) {
\t\tconst map = {
\t\t\texcellent:        lt('Excellent', 'অসাধারণ'),
\t\t\tgood:             lt('Good', 'ভালো'),
\t\t\taverage:          lt('Average', 'মোটামুটি'),
\t\t\tneeds_improvement: lt('Needs Improvement', 'উন্নতি দরকার')
\t\t};
\t\treturn map[p] || (p || '').replace('_', ' ');
\t}

\tfunction responseTypeLabel(rt) {
\t\tconst map = {
\t\t\thit:          lt('Hit', 'হিট'),
\t\t\tmiss:         lt('Miss', 'মিস'),
\t\t\tfalse_alarm:  lt('False Alarm', 'মিথ্যা সংকেত'),
\t\t\tcorrect_rejection: lt('Correct Rejection', 'সঠিক প্রত্যাখ্যান')
\t\t};
\t\treturn map[rt] || (rt || '').replace('_', ' ');
\t}

\tfunction timerClass() {
\t\tif (timeRemaining < 5)  return 'timer-critical';
\t\tif (timeRemaining < 10) return 'timer-warning';
\t\treturn '';
\t}

\t// ── Lifecycle ──────────────────────────────────────
\tonMount(async () => {
\t\tif (!$user) { goto('/login'); return; }
\t\ttaskId = $page.url.searchParams.get('taskId');
\t\tawait loadTrial();
\t});

\tonDestroy(() => {
\t\tif (timerInterval) clearInterval(timerInterval);
\t});

\t// ── Game Logic ─────────────────────────────────────
\tasync function loadTrial() {
\t\ttry {
\t\t\tloadError = false;
\t\t\tconst response = await fetch(
\t\t\t\t`${API_BASE_URL}/api/training/tasks/visual-search/generate/${$user.id}`,
\t\t\t\t{ method: 'GET', headers: { 'Content-Type': 'application/json' }, credentials: 'include' }
\t\t\t);
\t\t\tif (!response.ok) throw new Error('Failed to load trial');
\t\t\tconst data = await response.json();
\t\t\trecordedTrialData = cloneData(data.trial_data);
\t\t\trecordedDifficulty = data.difficulty;
\t\t\tdifficulty = recordedDifficulty;
\t\t\tapplyTrialView(cloneData(recordedTrialData));
\t\t\tgamePhase = 'intro';
\t\t} catch (_) {
\t\t\tloadError = true;
\t\t\tgamePhase = 'intro';
\t\t}
\t}

\tfunction startGame(nextMode = TASK_PLAY_MODE.RECORDED) {
\t\tplayMode = nextMode;
\t\tpracticeStatusMessage = '';
\t\tdifficulty = recordedDifficulty;
\t\tif (playMode === TASK_PLAY_MODE.PRACTICE && recordedTrialData) {
\t\t\tapplyTrialView(buildPracticePayload('visual-search', recordedTrialData));
\t\t} else if (recordedTrialData) {
\t\t\tapplyTrialView(cloneData(recordedTrialData));
\t\t}
\t\tstartTime = Date.now();
\t\tuserAnswer = null;
\t\tgamePhase = 'playing';
\t\ttimerInterval = setInterval(() => {
\t\t\tconst elapsed = (Date.now() - startTime) / 1000;
\t\t\ttimeRemaining = Math.max(0, timeLimit - elapsed);
\t\t\tif (timeRemaining === 0) handleResponse(false);
\t\t}, 100);
\t}

\tfunction handleResponse(answer) {
\t\tif (userAnswer !== null) return;
\t\tuserAnswer = answer;
\t\tif (timerInterval) { clearInterval(timerInterval); timerInterval = null; }
\t\tsubmitResults();
\t}

\tasync function submitResults() {
\t\tif (playMode === TASK_PLAY_MODE.PRACTICE) {
\t\t\tplayMode = TASK_PLAY_MODE.RECORDED;
\t\t\tpracticeStatusMessage = getPracticeCopy($locale).complete;
\t\t\tresults = null;
\t\t\tuserAnswer = null;
\t\t\tgamePhase = 'loading';
\t\t\tawait loadTrial();
\t\t\treturn;
\t\t}
\t\tsaveError = false;
\t\tconst reactionTime = (Date.now() - startTime) / 1000;
\t\ttry {
\t\t\tconst response = await fetch(
\t\t\t\t`${API_BASE_URL}/api/training/tasks/visual-search/submit/${$user.id}`,
\t\t\t\t{
\t\t\t\t\tmethod: 'POST',
\t\t\t\t\theaders: { 'Content-Type': 'application/json' },
\t\t\t\t\tcredentials: 'include',
\t\t\t\t\tbody: JSON.stringify({
\t\t\t\t\t\ttrial_data: trialData,
\t\t\t\t\t\tuser_response: { target_found: userAnswer, reaction_time: reactionTime },
\t\t\t\t\t\ttask_id: taskId
\t\t\t\t\t})
\t\t\t\t}
\t\t\t);
\t\t\tif (!response.ok) throw new Error('Failed to submit results');
\t\t\tconst data = await response.json();
\t\t\tresults = data;
\t\t\tearnedBadges = data.new_badges || [];
\t\t\tgamePhase = 'results';
\t\t} catch (_) {
\t\t\tsaveError = true;
\t\t\tgamePhase = 'results';
\t\t}
\t}

\tfunction retryTask() {
\t\tgamePhase = 'loading';
\t\tresults = null;
\t\tearnedBadges = [];
\t\tuserAnswer = null;
\t\tloadTrial();
\t}
</script>

<div class="vs-page" data-localize-skip>
\t<div class="vs-wrapper">

\t\t{#if gamePhase === 'loading'}
\t\t\t<LoadingSkeleton />

\t\t{:else if gamePhase === 'intro'}

\t\t\t<!-- Header Card -->
\t\t\t<div class="header-card">
\t\t\t\t<div class="header-content">
\t\t\t\t\t<div class="header-text">
\t\t\t\t\t\t<h1 class="task-title">{lt('Visual Search', 'ভিজ্যুয়াল সার্চ')}</h1>
\t\t\t\t\t\t<p class="task-domain">{lt('Visual Scanning · Selective Attention', 'ভিজ্যুয়াল স্ক্যানিং · নির্বাচনী মনোযোগ')}</p>
\t\t\t\t\t</div>
\t\t\t\t\t<DifficultyBadge difficulty={difficulty || 1} domain="Visual Scanning" />
\t\t\t\t</div>
\t\t\t</div>

\t\t\t{#if playMode === TASK_PLAY_MODE.PRACTICE}
\t\t\t\t<PracticeModeBanner locale={$locale} />
\t\t\t{/if}

\t\t\t{#if loadError}
\t\t\t\t<div class="error-card">
\t\t\t\t\t<p>{lt('Failed to load task. Please try again.', 'টাস্ক লোড করতে ব্যর্থ। আবার চেষ্টা করুন।')}</p>
\t\t\t\t\t<button class="start-button" on:click={loadTrial}>{lt('Retry', 'আবার চেষ্টা করুন')}</button>
\t\t\t\t</div>
\t\t\t{:else if targetItem}

\t\t\t\t<!-- Task Concept -->
\t\t\t\t<div class="card task-concept">
\t\t\t\t\t<div class="concept-badge">
\t\t\t\t\t\t<span class="badge-label">{lt('Visual Search', 'ভিজ্যুয়াল সার্চ')}</span>
\t\t\t\t\t\t<span>{lt('Treisman & Gelade, 1980', 'Treisman & Gelade, 1980')}</span>
\t\t\t\t\t</div>
\t\t\t\t\t{#if searchType === 'feature'}
\t\t\t\t\t\t<p class="concept-desc">
\t\t\t\t\t\t\t{lt(
\t\t\t\t\t\t\t\t'Feature Search: the target differs from distractors by a single attribute — color or shape. This triggers parallel visual processing, so the target "pops out" regardless of how many items are displayed.',
\t\t\t\t\t\t\t\t'ফিচার সার্চ: লক্ষ্যটি একটি মাত্র বৈশিষ্ট্যে (রঙ বা আকার) আলাদা। এটি সমান্তরাল ভিজ্যুয়াল প্রক্রিয়াকরণ চালু করে, তাই লক্ষ্যটি আইটেমের সংখ্যা নির্বিশেষে "পপ আউট" করে।'
\t\t\t\t\t\t\t)}
\t\t\t\t\t\t</p>
\t\t\t\t\t{:else}
\t\t\t\t\t\t<p class="concept-desc">
\t\t\t\t\t\t\t{lt(
\t\t\t\t\t\t\t\t'Conjunction Search: the target requires matching BOTH color and shape simultaneously. This demands serial visual attention — you must examine each item individually, making it sensitive to MS-related attention deficits.',
\t\t\t\t\t\t\t\t'কনজাংশন সার্চ: লক্ষ্যটি রঙ এবং আকার উভয়ই মেলাতে হবে। এটি সিরিয়াল ভিজ্যুয়াল মনোযোগ দাবি করে — MS-সংক্রান্ত মনোযোগের ঘাটতিতে সংবেদনশীল।'
\t\t\t\t\t\t\t)}
\t\t\t\t\t\t</p>
\t\t\t\t\t{/if}
\t\t\t\t</div>

\t\t\t\t<!-- Target Display -->
\t\t\t\t<div class="card">
\t\t\t\t\t<h2 class="section-title">{lt('Your Target', 'আপনার লক্ষ্য')}</h2>
\t\t\t\t\t<p class="target-subtext">{lt('Find and confirm the presence or absence of this exact item:', 'এই নির্দিষ্ট আইটেমটি আছে কি নেই নিশ্চিত করুন:')}</p>
\t\t\t\t\t<div class="target-showcase">
\t\t\t\t\t\t<div class="target-svg-wrap">
\t\t\t\t\t\t\t<svg width="100" height="100" viewBox="0 0 100 100">
\t\t\t\t\t\t\t\t<path
\t\t\t\t\t\t\t\t\td={getShapePath(targetItem.shape)}
\t\t\t\t\t\t\t\t\tfill={getColorValue(targetItem.color)}
\t\t\t\t\t\t\t\t\tstroke="#1F2937"
\t\t\t\t\t\t\t\t\tstroke-width="3"
\t\t\t\t\t\t\t\t/>
\t\t\t\t\t\t\t</svg>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="target-label-group">
\t\t\t\t\t\t\t<div class="target-name">{getColorDisplay(targetItem.color)} {getShapeDisplay(targetItem.shape)}</div>
\t\t\t\t\t\t\t<div class="target-attrs">
\t\t\t\t\t\t\t\t<span class="attr-chip color-chip" style="background: {getColorValue(targetItem.color)}20; border-color: {getColorValue(targetItem.color)};">
\t\t\t\t\t\t\t\t\t{getColorDisplay(targetItem.color)}
\t\t\t\t\t\t\t\t</span>
\t\t\t\t\t\t\t\t<span class="attr-chip shape-chip">
\t\t\t\t\t\t\t\t\t{getShapeDisplay(targetItem.shape)}
\t\t\t\t\t\t\t\t</span>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Rules Card -->
\t\t\t\t<div class="card">
\t\t\t\t\t<h2 class="section-title">{lt('Rules', 'নিয়মাবলী')}</h2>
\t\t\t\t\t<div class="rules-list">
\t\t\t\t\t\t<div class="rule-item">
\t\t\t\t\t\t\t<div class="rule-num">1</div>
\t\t\t\t\t\t\t<div class="rule-text">{lt('Study the target shape above carefully before starting', 'শুরু করার আগে উপরের লক্ষ্যটি মনোযোগ দিয়ে দেখুন')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="rule-item">
\t\t\t\t\t\t\t<div class="rule-num">2</div>
\t\t\t\t\t\t\t<div class="rule-text">{lt('Search the display and decide if the target is present or absent', 'ডিসপ্লে স্ক্যান করুন এবং সিদ্ধান্ত নিন লক্ষ্যটি আছে কি নেই')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="rule-item">
\t\t\t\t\t\t\t<div class="rule-num">3</div>
\t\t\t\t\t\t\t<div class="rule-text">{lt('Respond as quickly and accurately as possible — both speed and accuracy count', 'যত দ্রুত ও নির্ভুলভাবে সম্ভব উত্তর দিন — গতি এবং নির্ভুলতা উভয়ই গুরুত্বপূর্ণ')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="rule-item">
\t\t\t\t\t\t\t<div class="rule-num">4</div>
\t\t\t\t\t\t\t<div class="rule-text">{lt(`You have ${timeLimit} seconds — if time runs out, it counts as absent`, `আপনার ${timeLimit} সেকেন্ড আছে — সময় শেষ হলে অনুপস্থিত হিসেবে গণনা হবে`)}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Info Grid -->
\t\t\t\t<div class="info-grid">
\t\t\t\t\t<!-- Task Details -->
\t\t\t\t\t<div class="card">
\t\t\t\t\t\t<h3 class="card-title">{lt('Task Details', 'টাস্কের বিবরণ')}</h3>
\t\t\t\t\t\t<div class="details-list">
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{lt('Search Type', 'সার্চের ধরন')}</span>
\t\t\t\t\t\t\t\t<strong class="{searchType === 'feature' ? 'type-feature' : 'type-conjunction'}">{searchType === 'feature' ? lt('Feature', 'ফিচার') : lt('Conjunction', 'কনজাংশন')}</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{lt('Display Items', 'প্রদর্শিত আইটেম')}</span>
\t\t\t\t\t\t\t\t<strong>{setSize}</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{lt('Time Limit', 'সময়সীমা')}</span>
\t\t\t\t\t\t\t\t<strong>{timeLimit}s</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{lt('Difficulty', 'কঠিনতা')}</span>
\t\t\t\t\t\t\t\t<strong>{lt(`Level ${difficulty} / 10`, `স্তর ${difficulty} / ১০`)}</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t\t<!-- Strategy Hint -->
\t\t\t\t\t<div class="card">
\t\t\t\t\t\t<h3 class="card-title">{lt('Search Strategy', 'সার্চ কৌশল')}</h3>
\t\t\t\t\t\t{#if searchType === 'feature'}
\t\t\t\t\t\t\t<div class="strategy-box strategy-feature">
\t\t\t\t\t\t\t\t<div class="strategy-label">{lt('Feature Search', 'ফিচার সার্চ')}</div>
\t\t\t\t\t\t\t\t<p class="strategy-text">{lt('Target differs by ONE attribute. It should "pop out" immediately — no need to scan item by item.', 'লক্ষ্য একটি বৈশিষ্ট্যে আলাদা। এটি অবিলম্বে "পপ আউট" করবে।')}</p>
\t\t\t\t\t\t\t\t<div class="strategy-benchmark">{lt('Benchmark: < 10 ms per item (parallel)', 'বেঞ্চমার্ক: আইটেম প্রতি < ১০ ms')}</div>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t{:else}
\t\t\t\t\t\t\t<div class="strategy-box strategy-conjunction">
\t\t\t\t\t\t\t\t<div class="strategy-label">{lt('Conjunction Search', 'কনজাংশন সার্চ')}</div>
\t\t\t\t\t\t\t\t<p class="strategy-text">{lt('Target matches on BOTH attributes. Requires serial inspection — scan carefully, row by row.', 'লক্ষ্য উভয় বৈশিষ্ট্য মেলায়। সারি সারি যত্নসহকারে স্ক্যান করুন।')}</p>
\t\t\t\t\t\t\t\t<div class="strategy-benchmark">{lt('Benchmark: < 30 ms per item (serial)', 'বেঞ্চমার্ক: আইটেম প্রতি < ৩০ ms')}</div>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t{/if}
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Clinical Basis -->
\t\t\t\t<div class="clinical-info">
\t\t\t\t\t<div class="clinical-header">
\t\t\t\t\t\t<div class="clinical-badge">{lt('Clinical Basis', 'ক্লিনিকাল ভিত্তি')}</div>
\t\t\t\t\t\t<h3>{lt('Validated MS Visual Attention Assessment', 'MS-এর জন্য যাচাইকৃত ভিজ্যুয়াল মনোযোগ মূল্যায়ন')}</h3>
\t\t\t\t\t</div>
\t\t\t\t\t<p>
\t\t\t\t\t\t{lt(
\t\t\t\t\t\t\t'The Visual Search paradigm (Treisman & Gelade, 1980) distinguishes automatic pre-attentive processing (feature search) from effortful serial attention (conjunction search). In MS, conjunction search is disproportionately impaired due to white matter lesion load reducing attentional capacity and slowing interhemispheric integration, making it a sensitive index of disease burden on visual cognition.',
\t\t\t\t\t\t\t'ভিজ্যুয়াল সার্চ প্যারাডাইম (Treisman & Gelade, 1980) স্বয়ংক্রিয় প্রি-অ্যাটেন্টিভ প্রক্রিয়াকরণ এবং প্রচেষ্টাপূর্ণ সিরিয়াল মনোযোগ পার্থক্য করে। MS-এ কনজাংশন সার্চ অসামঞ্জস্যভাবে ক্ষতিগ্রস্ত হয়।'
\t\t\t\t\t\t)}
\t\t\t\t\t</p>
\t\t\t\t</div>

\t\t\t\t<TaskPracticeActions
\t\t\t\t\tlocale={$locale}
\t\t\t\t\tstartLabel={lt('Begin Task', 'টাস্ক শুরু করুন')}
\t\t\t\t\tstatusMessage={practiceStatusMessage}
\t\t\t\t\ton:start={() => startGame(TASK_PLAY_MODE.RECORDED)}
\t\t\t\t\ton:practice={() => startGame(TASK_PLAY_MODE.PRACTICE)}
\t\t\t\t/>

\t\t\t{:else}
\t\t\t\t<LoadingSkeleton />
\t\t\t{/if}

\t\t{:else if gamePhase === 'playing'}

\t\t\t<div class="game-card">
\t\t\t\t{#if playMode === TASK_PLAY_MODE.PRACTICE}
\t\t\t\t\t<PracticeModeBanner locale={$locale} />
\t\t\t\t{/if}

\t\t\t\t<!-- Game Status Bar -->
\t\t\t\t<div class="game-status-bar">
\t\t\t\t\t<div class="target-reference">
\t\t\t\t\t\t<span class="ref-label">{lt('Looking for:', 'খুঁজছি:')}</span>
\t\t\t\t\t\t<div class="ref-item">
\t\t\t\t\t\t\t<svg width="40" height="40" viewBox="0 0 100 100">
\t\t\t\t\t\t\t\t<path
\t\t\t\t\t\t\t\t\td={getShapePath(targetItem.shape)}
\t\t\t\t\t\t\t\t\tfill={getColorValue(targetItem.color)}
\t\t\t\t\t\t\t\t\tstroke="#1F2937"
\t\t\t\t\t\t\t\t\tstroke-width="3"
\t\t\t\t\t\t\t\t/>
\t\t\t\t\t\t\t</svg>
\t\t\t\t\t\t\t<span class="ref-name">{getColorDisplay(targetItem.color)} {getShapeDisplay(targetItem.shape)}</span>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="search-type-tag {searchType === 'feature' ? 'tag-feature' : 'tag-conjunction'}">
\t\t\t\t\t\t\t{searchType === 'feature' ? lt('Feature', 'ফিচার') : lt('Conjunction', 'কনজাংশন')}
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t\t<div class="timer-block">
\t\t\t\t\t\t<div class="timer-value {timerClass()}">{Math.ceil(timeRemaining)}</div>
\t\t\t\t\t\t<div class="timer-label">{lt('seconds', 'সেকেন্ড')}</div>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Search Arena -->
\t\t\t\t<div class="search-arena">
\t\t\t\t\t{#each items as item}
\t\t\t\t\t\t<div
\t\t\t\t\t\t\tclass="search-item"
\t\t\t\t\t\t\tstyle="left: {item.position.x * 90 + 5}%; top: {item.position.y * 90 + 5}%;"
\t\t\t\t\t\t>
\t\t\t\t\t\t\t<svg width="45" height="45" viewBox="0 0 100 100">
\t\t\t\t\t\t\t\t<path
\t\t\t\t\t\t\t\t\td={getShapePath(item.shape)}
\t\t\t\t\t\t\t\t\tfill={getColorValue(item.color)}
\t\t\t\t\t\t\t\t\tstroke="#374151"
\t\t\t\t\t\t\t\t\tstroke-width="2.5"
\t\t\t\t\t\t\t\t/>
\t\t\t\t\t\t\t</svg>
\t\t\t\t\t\t</div>
\t\t\t\t\t{/each}
\t\t\t\t</div>

\t\t\t\t<!-- Response Buttons -->
\t\t\t\t<div class="response-section">
\t\t\t\t\t<p class="response-prompt">{lt('Is the target present in the display?', 'ডিসপ্লেতে লক্ষ্যটি আছে কি?')}</p>
\t\t\t\t\t<div class="response-buttons">
\t\t\t\t\t\t<button class="resp-btn resp-present" on:click={() => handleResponse(true)}>
\t\t\t\t\t\t\t<span class="resp-icon resp-check">✓</span>
\t\t\t\t\t\t\t<span>{lt('Target Present', 'লক্ষ্য আছে')}</span>
\t\t\t\t\t\t</button>
\t\t\t\t\t\t<button class="resp-btn resp-absent" on:click={() => handleResponse(false)}>
\t\t\t\t\t\t\t<span class="resp-icon resp-cross">✕</span>
\t\t\t\t\t\t\t<span>{lt('Target Absent', 'লক্ষ্য নেই')}</span>
\t\t\t\t\t\t</button>
\t\t\t\t\t</div>
\t\t\t\t</div>
\t\t\t</div>

\t\t{:else if gamePhase === 'results'}

\t\t\t<!-- Results Header -->
\t\t\t<div class="results-header {results && results.correct ? 'header-correct' : 'header-incorrect'}">
\t\t\t\t<div class="score-pill">
\t\t\t\t\t<span class="score-label">{lt('Score', 'স্কোর')}</span>
\t\t\t\t\t<span class="score-value">{results ? (results.score * 100).toFixed(0) : '—'}</span>
\t\t\t\t\t<span class="score-max">%</span>
\t\t\t\t</div>
\t\t\t\t<p class="results-subtitle">
\t\t\t\t\t{lt('Visual Search Complete', 'ভিজ্যুয়াল সার্চ সম্পন্ন')} ·
\t\t\t\t\t{results ? (results.correct ? lt('Correct', 'সঠিক') : lt('Incorrect', 'ভুল')) : ''}
\t\t\t\t</p>
\t\t\t</div>

\t\t\t{#if saveError}
\t\t\t\t<div class="warn-card">
\t\t\t\t\t{lt('Error saving results. Your progress may not have been recorded.', 'ফলাফল সংরক্ষণে ত্রুটি। অগ্রগতি রেকর্ড নাও হতে পারে।')}
\t\t\t\t</div>
\t\t\t{/if}

\t\t\t{#if results}
\t\t\t\t<!-- Key Metrics -->
\t\t\t\t<div class="metrics-grid">
\t\t\t\t\t<div class="metric-card {results.correct ? 'metric-green' : 'metric-red'}">
\t\t\t\t\t\t<div class="metric-value">{results.correct ? lt('Yes', 'হ্যাঁ') : lt('No', 'না')}</div>
\t\t\t\t\t\t<div class="metric-label">{lt('Correct', 'সঠিক')}</div>
\t\t\t\t\t</div>
\t\t\t\t\t<div class="metric-card metric-blue">
\t\t\t\t\t\t<div class="metric-value">{(results.score * 100).toFixed(0)}%</div>
\t\t\t\t\t\t<div class="metric-label">{lt('Score', 'স্কোর')}</div>
\t\t\t\t\t</div>
\t\t\t\t\t<div class="metric-card metric-amber">
\t\t\t\t\t\t<div class="metric-value">{results.reaction_time.toFixed(2)}s</div>
\t\t\t\t\t\t<div class="metric-label">{lt('Reaction Time', 'প্রতিক্রিয়া সময়')}</div>
\t\t\t\t\t</div>
\t\t\t\t\t<div class="metric-card metric-slate">
\t\t\t\t\t\t<div class="metric-value response-type-text">{responseTypeLabel(results.response_type)}</div>
\t\t\t\t\t\t<div class="metric-label">{lt('Response Type', 'প্রতিক্রিয়ার ধরন')}</div>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Performance Analysis -->
\t\t\t\t<div class="card">
\t\t\t\t\t<h3 class="card-title">{lt('Performance Analysis', 'পারফরম্যান্স বিশ্লেষণ')}</h3>
\t\t\t\t\t<div class="analysis-grid">
\t\t\t\t\t\t<div class="analysis-cell">
\t\t\t\t\t\t\t<div class="analysis-label">{lt('Search Efficiency', 'সার্চ দক্ষতা')}</div>
\t\t\t\t\t\t\t<div class="analysis-value">{results.search_efficiency.toFixed(3)}s/item</div>
\t\t\t\t\t\t\t<div class="analysis-desc">{lt('Time spent per display item', 'প্রতিটি আইটেমে ব্যয়িত সময়')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="analysis-cell">
\t\t\t\t\t\t\t<div class="analysis-label">{lt('Search Slope', 'সার্চ স্লোপ')}</div>
\t\t\t\t\t\t\t<div class="analysis-value">{results.search_slope_ms.toFixed(1)} ms/item</div>
\t\t\t\t\t\t\t<div class="analysis-desc">
\t\t\t\t\t\t\t\t{results.search_type === 'feature'
\t\t\t\t\t\t\t\t\t? lt('Feature target: < 10 ms = excellent (parallel)', 'ফিচার: < ১০ ms = অসাধারণ')
\t\t\t\t\t\t\t\t\t: lt('Conjunction target: < 30 ms = excellent (serial)', 'কনজাংশন: < ৩০ ms = অসাধারণ')}
\t\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="analysis-cell">
\t\t\t\t\t\t\t<div class="analysis-label">{lt('Rating', 'রেটিং')}</div>
\t\t\t\t\t\t\t<div class="analysis-value perf-{results.performance}">{performanceLabel(results.performance)}</div>
\t\t\t\t\t\t\t<div class="analysis-desc">{lt('Overall performance classification', 'সামগ্রিক পারফরম্যান্স শ্রেণীবিভাগ')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Trial Summary -->
\t\t\t\t<div class="card">
\t\t\t\t\t<h3 class="card-title">{lt('Trial Summary', 'ট্রায়াল সারাংশ')}</h3>
\t\t\t\t\t<div class="details-list">
\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t<span>{lt('Search Type', 'সার্চের ধরন')}</span>
\t\t\t\t\t\t\t<strong>{results.search_type === 'feature' ? lt('Feature Search', 'ফিচার সার্চ') : lt('Conjunction Search', 'কনজাংশন সার্চ')}</strong>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t<span>{lt('Set Size', 'সেট সাইজ')}</span>
\t\t\t\t\t\t\t<strong>{results.set_size} {lt('items', 'আইটেম')}</strong>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t<span>{lt('Target Was', 'লক্ষ্য ছিল')}</span>
\t\t\t\t\t\t\t<strong>{results.target_present ? lt('Present', 'উপস্থিত') : lt('Absent', 'অনুপস্থিত')}</strong>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t<span>{lt('Your Response', 'আপনার উত্তর')}</span>
\t\t\t\t\t\t\t<strong>{results.user_answer ? lt('Present', 'উপস্থিত') : lt('Absent', 'অনুপস্থিত')}</strong>
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Difficulty Adjustment -->
\t\t\t\t<div class="adaptation-card">
\t\t\t\t\t<div class="adaptation-label">
\t\t\t\t\t\t{#if results.new_difficulty > results.old_difficulty}
\t\t\t\t\t\t\t{lt('Difficulty Increased', 'কঠিনতা বৃদ্ধি')} — {results.old_difficulty} → {results.new_difficulty}
\t\t\t\t\t\t{:else if results.new_difficulty < results.old_difficulty}
\t\t\t\t\t\t\t{lt('Difficulty Decreased', 'কঠিনতা হ্রাস')} — {results.old_difficulty} → {results.new_difficulty}
\t\t\t\t\t\t{:else}
\t\t\t\t\t\t\t{lt('Difficulty Maintained', 'কঠিনতা বজায়')} — {lt(`Level ${results.new_difficulty}`, `স্তর ${results.new_difficulty}`)}
\t\t\t\t\t\t{/if}
\t\t\t\t\t</div>
\t\t\t\t\t<p class="adaptation-text">{results.adaptation_reason}</p>
\t\t\t\t</div>
\t\t\t{/if}

\t\t\t<!-- Action Buttons -->
\t\t\t<div class="action-buttons">
\t\t\t\t<button class="start-button" on:click={() => goto('/dashboard')}>
\t\t\t\t\t{lt('Return to Dashboard', 'ড্যাশবোর্ডে ফিরুন')}
\t\t\t\t</button>
\t\t\t\t<button class="btn-secondary" on:click={retryTask}>
\t\t\t\t\t{lt('Try Again', 'আবার চেষ্টা করুন')}
\t\t\t\t</button>
\t\t\t</div>

\t\t{/if}
\t</div>
</div>

{#if earnedBadges.length > 0}
\t<BadgeNotification badges={earnedBadges} />
{/if}

<style>
\t/* ── Page Layout ─────────────────────────────────── */
\t.vs-page {
\t\tmin-height: 100vh;
\t\tbackground: #C8DEFA;
\t\tpadding: 1.5rem;
\t}

\t.vs-wrapper {
\t\tmax-width: 1100px;
\t\tmargin: 0 auto;
\t}

\t/* ── Shared Card ──────────────────────────────────── */
\t.card {
\t\tbackground: white;
\t\tborder-radius: 16px;
\t\tpadding: 1.5rem;
\t\tbox-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
\t\tmargin-bottom: 1rem;
\t}

\t/* ── Header Card ─────────────────────────────────── */
\t.header-card {
\t\tbackground: white;
\t\tborder-radius: 16px;
\t\tpadding: 1.5rem;
\t\tbox-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
\t\tmargin-bottom: 1rem;
\t}

\t.header-content {
\t\tdisplay: flex;
\t\talign-items: center;
\t\tjustify-content: space-between;
\t\tflex-wrap: wrap;
\t\tgap: 1rem;
\t}

\t.task-title {
\t\tfont-size: 1.75rem;
\t\tfont-weight: 700;
\t\tcolor: #1a1a2e;
\t\tmargin: 0 0 0.25rem 0;
\t}

\t.task-domain {
\t\tfont-size: 0.875rem;
\t\tcolor: #1e40af;
\t\tfont-weight: 500;
\t\tmargin: 0;
\t}

\t/* ── Error / Warn ─────────────────────────────────── */
\t.error-card {
\t\tbackground: #fee2e2;
\t\tborder: 2px solid #fca5a5;
\t\tborder-radius: 16px;
\t\tpadding: 2rem;
\t\ttext-align: center;
\t\tcolor: #991b1b;
\t\tmargin-bottom: 1rem;
\t}

\t.warn-card {
\t\tbackground: #fff7ed;
\t\tborder: 2px solid #fed7aa;
\t\tborder-radius: 12px;
\t\tpadding: 1rem 1.25rem;
\t\tcolor: #92400e;
\t\tfont-size: 0.875rem;
\t\tmargin-bottom: 1rem;
\t}

\t/* ── Task Concept ─────────────────────────────────── */
\t.task-concept { margin-bottom: 1rem; }

\t.concept-badge {
\t\tdisplay: inline-flex;
\t\talign-items: center;
\t\tgap: 0.5rem;
\t\tbackground: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
\t\tcolor: white;
\t\tpadding: 0.4rem 0.9rem;
\t\tborder-radius: 2rem;
\t\tfont-size: 0.813rem;
\t\tfont-weight: 600;
\t\tmargin-bottom: 1rem;
\t}

\t.badge-label { font-weight: 700; letter-spacing: 0.04em; }
\t.concept-desc { color: #4b5563; font-size: 0.938rem; line-height: 1.6; margin: 0; }

\t/* ── Section Title ────────────────────────────────── */
\t.section-title {
\t\tfont-size: 1.125rem;
\t\tfont-weight: 600;
\t\tcolor: #1a1a2e;
\t\tmargin: 0 0 0.625rem 0;
\t}

\t.target-subtext { color: #6b7280; font-size: 0.875rem; margin: 0 0 1rem 0; }

\t/* ── Target Showcase ──────────────────────────────── */
\t.target-showcase {
\t\tdisplay: flex;
\t\talign-items: center;
\t\tgap: 1.5rem;
\t\tbackground: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
\t\tborder: 2px solid #bfdbfe;
\t\tborder-radius: 12px;
\t\tpadding: 1.5rem;
\t}

\t.target-svg-wrap {
\t\tfilter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.12));
\t\tflex-shrink: 0;
\t}

\t.target-name {
\t\tfont-size: 1.4rem;
\t\tfont-weight: 700;
\t\tcolor: #1e3a8a;
\t\tmargin-bottom: 0.625rem;
\t}

\t.target-attrs { display: flex; gap: 0.5rem; flex-wrap: wrap; }

\t.attr-chip {
\t\tpadding: 0.25rem 0.75rem;
\t\tborder-radius: 1rem;
\t\tfont-size: 0.813rem;
\t\tfont-weight: 600;
\t\tborder: 2px solid transparent;
\t}

\t.shape-chip { background: #f0f9ff; border-color: #7dd3fc; color: #0c4a6e; }

\t/* ── Rules List ───────────────────────────────────── */
\t.rules-list { display: flex; flex-direction: column; gap: 0.75rem; }

\t.rule-item {
\t\tdisplay: flex;
\t\talign-items: flex-start;
\t\tgap: 0.875rem;
\t\tbackground: #eff6ff;
\t\tborder-radius: 10px;
\t\tpadding: 0.875rem 1rem;
\t}

\t.rule-num {
\t\tmin-width: 2rem;
\t\theight: 2rem;
\t\tbackground: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
\t\tcolor: white;
\t\tborder-radius: 50%;
\t\tdisplay: flex;
\t\talign-items: center;
\t\tjustify-content: center;
\t\tfont-size: 0.875rem;
\t\tfont-weight: 700;
\t\tflex-shrink: 0;
\t}

\t.rule-text { font-size: 0.9rem; color: #374151; line-height: 1.5; }

\t/* ── Info Grid ────────────────────────────────────── */
\t.info-grid {
\t\tdisplay: grid;
\t\tgrid-template-columns: 1fr 1fr;
\t\tgap: 1rem;
\t\tmargin-bottom: 1rem;
\t}

\t.card-title { font-size: 1rem; font-weight: 600; color: #1a1a2e; margin: 0 0 1rem 0; }

\t/* ── Details List ─────────────────────────────────── */
\t.details-list { display: flex; flex-direction: column; gap: 0.625rem; }

\t.detail-row {
\t\tdisplay: flex;
\t\tjustify-content: space-between;
\t\talign-items: center;
\t\tfont-size: 0.875rem;
\t\tpadding-bottom: 0.625rem;
\t\tborder-bottom: 1px solid #f3f4f6;
\t}

\t.detail-row:last-child { border-bottom: none; padding-bottom: 0; }
\t.detail-row span   { color: #6b7280; }
\t.detail-row strong { color: #1a1a2e; text-align: right; max-width: 65%; }

\t.type-feature    { color: #1e40af; }
\t.type-conjunction { color: #92400e; }

\t/* ── Strategy Box ─────────────────────────────────── */
\t.strategy-box {
\t\tborder-radius: 10px;
\t\tpadding: 1rem 1.125rem;
\t}

\t.strategy-feature    { background: #eff6ff; border: 2px solid #bfdbfe; }
\t.strategy-conjunction { background: #fef3c7; border: 2px solid #fcd34d; }

\t.strategy-label {
\t\tfont-size: 0.875rem;
\t\tfont-weight: 700;
\t\tmargin-bottom: 0.375rem;
\t}

\t.strategy-feature .strategy-label    { color: #1e40af; }
\t.strategy-conjunction .strategy-label { color: #92400e; }

\t.strategy-text {
\t\tfont-size: 0.875rem;
\t\tline-height: 1.5;
\t\tmargin: 0 0 0.625rem 0;
\t}

\t.strategy-feature .strategy-text    { color: #1e3a8a; }
\t.strategy-conjunction .strategy-text { color: #78350f; }

\t.strategy-benchmark {
\t\tfont-size: 0.75rem;
\t\tfont-weight: 600;
\t\tpadding: 0.25rem 0.625rem;
\t\tborder-radius: 0.5rem;
\t\tdisplay: inline-block;
\t}

\t.strategy-feature .strategy-benchmark    { background: #bfdbfe; color: #1e3a8a; }
\t.strategy-conjunction .strategy-benchmark { background: #fde68a; color: #78350f; }

\t/* ── Clinical Info ────────────────────────────────── */
\t.clinical-info {
\t\tbackground: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
\t\tborder: 1px solid #bbf7d0;
\t\tborder-radius: 16px;
\t\tpadding: 1.5rem;
\t\tmargin-bottom: 1rem;
\t}

\t.clinical-header {
\t\tdisplay: flex;
\t\talign-items: center;
\t\tgap: 0.75rem;
\t\tmargin-bottom: 0.75rem;
\t}

\t.clinical-badge {
\t\tbackground: #16a34a;
\t\tcolor: white;
\t\tpadding: 0.2rem 0.7rem;
\t\tborder-radius: 1rem;
\t\tfont-size: 0.75rem;
\t\tfont-weight: 600;
\t}

\t.clinical-header h3 { font-size: 1rem; font-weight: 600; color: #14532d; margin: 0; }
\t.clinical-info p    { font-size: 0.875rem; color: #166534; line-height: 1.6; margin: 0; }

\t/* ── Game Card ────────────────────────────────────── */
\t.game-card {
\t\tbackground: white;
\t\tborder-radius: 16px;
\t\tpadding: 1.5rem;
\t\tbox-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
\t}

\t/* ── Game Status Bar ──────────────────────────────── */
\t.game-status-bar {
\t\tdisplay: flex;
\t\talign-items: center;
\t\tjustify-content: space-between;
\t\tgap: 1rem;
\t\tmargin-bottom: 1.25rem;
\t\tflex-wrap: wrap;
\t}

\t.target-reference {
\t\tdisplay: flex;
\t\talign-items: center;
\t\tgap: 1rem;
\t\tflex-wrap: wrap;
\t}

\t.ref-label { font-size: 0.875rem; font-weight: 700; color: #1e40af; }

\t.ref-item {
\t\tdisplay: flex;
\t\talign-items: center;
\t\tgap: 0.5rem;
\t\tbackground: #eff6ff;
\t\tpadding: 0.375rem 0.875rem;
\t\tborder-radius: 0.625rem;
\t\tborder: 2px solid #bfdbfe;
\t}

\t.ref-name { font-size: 0.938rem; font-weight: 600; color: #1e3a8a; }

\t.search-type-tag {
\t\tpadding: 0.25rem 0.75rem;
\t\tborder-radius: 1rem;
\t\tfont-size: 0.813rem;
\t\tfont-weight: 700;
\t}

\t.tag-feature    { background: #dbeafe; color: #1e40af; }
\t.tag-conjunction { background: #fef3c7; color: #92400e; }

\t/* ── Timer ────────────────────────────────────────── */
\t.timer-block { text-align: center; }

\t.timer-value {
\t\tfont-size: 2.5rem;
\t\tfont-weight: 800;
\t\tcolor: #1e40af;
\t\tline-height: 1;
\t\tfont-variant-numeric: tabular-nums;
\t}

\t.timer-warning  { color: #d97706; animation: timer-pulse 1s ease-in-out infinite; }
\t.timer-critical { color: #dc2626; animation: timer-pulse 0.5s ease-in-out infinite; }
\t.timer-label    { font-size: 0.75rem; color: #6b7280; margin-top: 0.125rem; }

\t/* ── Search Arena ─────────────────────────────────── */
\t.search-arena {
\t\tposition: relative;
\t\twidth: 100%;
\t\theight: 65vh;
\t\tmin-height: 480px;
\t\tbackground: white;
\t\tborder: 3px solid #e2e8f0;
\t\tborder-radius: 16px;
\t\toverflow: hidden;
\t\tmargin-bottom: 1.5rem;
\t\tbox-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.04);
\t}

\t.search-item {
\t\tposition: absolute;
\t\ttransform: translate(-50%, -50%);
\t}

\t/* ── Response Section ─────────────────────────────── */
\t.response-section { text-align: center; }

\t.response-prompt {
\t\tfont-size: 1.125rem;
\t\tfont-weight: 600;
\t\tcolor: #1a1a2e;
\t\tmargin: 0 0 1.25rem 0;
\t}

\t.response-buttons {
\t\tdisplay: flex;
\t\tjustify-content: center;
\t\tgap: 1.5rem;
\t\tflex-wrap: wrap;
\t}

\t.resp-btn {
\t\tdisplay: flex;
\t\talign-items: center;
\t\tjustify-content: center;
\t\tgap: 0.625rem;
\t\tpadding: 1.25rem 3rem;
\t\tfont-size: 1.125rem;
\t\tfont-weight: 700;
\t\tborder: none;
\t\tborder-radius: 14px;
\t\tcursor: pointer;
\t\tmin-width: 210px;
\t\ttransition: transform 0.15s, box-shadow 0.15s;
\t}

\t.resp-btn:hover { transform: translateY(-3px); }

\t.resp-present {
\t\tbackground: linear-gradient(135deg, #16a34a 0%, #22c55e 100%);
\t\tcolor: white;
\t\tbox-shadow: 0 4px 14px rgba(22, 163, 74, 0.35);
\t}

\t.resp-present:hover { box-shadow: 0 8px 20px rgba(22, 163, 74, 0.45); }

\t.resp-absent {
\t\tbackground: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
\t\tcolor: white;
\t\tbox-shadow: 0 4px 14px rgba(220, 38, 38, 0.35);
\t}

\t.resp-absent:hover { box-shadow: 0 8px 20px rgba(220, 38, 38, 0.45); }

\t.resp-icon { font-size: 1.375rem; font-weight: 700; }
\t.resp-check { color: #bbf7d0; }
\t.resp-cross { color: #fecaca; }

\t/* ── Results Header ───────────────────────────────── */
\t.results-header {
\t\tborder-radius: 16px;
\t\tpadding: 1.75rem;
\t\ttext-align: center;
\t\tmargin-bottom: 1rem;
\t}

\t.header-correct   { background: linear-gradient(135deg, #15803d 0%, #16a34a 100%); box-shadow: 0 4px 12px rgba(21, 128, 61, 0.35); }
\t.header-incorrect { background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%); box-shadow: 0 4px 12px rgba(30, 58, 138, 0.35); }

\t.score-pill {
\t\tdisplay: flex;
\t\talign-items: baseline;
\t\tjustify-content: center;
\t\tgap: 0.375rem;
\t\tmargin-bottom: 0.5rem;
\t}

\t.score-label { color: rgba(255, 255, 255, 0.85); font-size: 1rem; font-weight: 500; }
\t.score-value { color: white; font-size: 3rem; font-weight: 700; }
\t.score-max   { color: rgba(255, 255, 255, 0.7); font-size: 1.5rem; font-weight: 500; }
\t.results-subtitle { color: rgba(255, 255, 255, 0.9); font-size: 0.938rem; margin: 0; }

\t/* ── Metrics Grid ─────────────────────────────────── */
\t.metrics-grid {
\t\tdisplay: grid;
\t\tgrid-template-columns: repeat(4, 1fr);
\t\tgap: 0.875rem;
\t\tmargin-bottom: 1rem;
\t}

\t.metric-card {
\t\tbackground: white;
\t\tborder-radius: 16px;
\t\tpadding: 1.25rem;
\t\ttext-align: center;
\t\tbox-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
\t\tborder-top: 4px solid #e5e7eb;
\t}

\t.metric-green { border-top-color: #16a34a; }
\t.metric-red   { border-top-color: #dc2626; }
\t.metric-blue  { border-top-color: #1e40af; }
\t.metric-amber { border-top-color: #d97706; }
\t.metric-slate { border-top-color: #64748b; }

\t.metric-value { font-size: 1.5rem; font-weight: 700; color: #1a1a2e; line-height: 1; }
\t.metric-label { font-size: 0.75rem; color: #6b7280; margin-top: 0.375rem; }
\t.response-type-text { font-size: 1.1rem; }

\t/* ── Performance Analysis Grid ────────────────────── */
\t.analysis-grid {
\t\tdisplay: grid;
\t\tgrid-template-columns: repeat(3, 1fr);
\t\tgap: 1rem;
\t}

\t.analysis-cell {
\t\tbackground: #f8fafc;
\t\tborder-radius: 10px;
\t\tpadding: 1rem;
\t\ttext-align: center;
\t}

\t.analysis-label { font-size: 0.75rem; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 0.375rem; }
\t.analysis-value { font-size: 1.375rem; font-weight: 700; color: #1a1a2e; margin-bottom: 0.25rem; }
\t.analysis-desc  { font-size: 0.75rem; color: #9ca3af; line-height: 1.4; }

\t.perf-excellent { color: #16a34a; }
\t.perf-good      { color: #1e40af; }
\t.perf-average   { color: #d97706; }
\t.perf-needs_improvement { color: #dc2626; }

\t/* ── Adaptation Card ──────────────────────────────── */
\t.adaptation-card {
\t\tbackground: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
\t\tborder: 1px solid #bfdbfe;
\t\tborder-radius: 16px;
\t\tpadding: 1.25rem 1.5rem;
\t\tmargin-bottom: 1rem;
\t}

\t.adaptation-label { font-size: 0.875rem; font-weight: 700; color: #1e3a8a; margin-bottom: 0.375rem; }
\t.adaptation-text  { font-size: 0.875rem; color: #1e40af; margin: 0; line-height: 1.5; }

\t/* ── Action Buttons ───────────────────────────────── */
\t.action-buttons { display: flex; gap: 1rem; margin-top: 1rem; }

\t.start-button {
\t\tflex: 1;
\t\tbackground: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
\t\tcolor: white;
\t\tborder: none;
\t\tborder-radius: 12px;
\t\tpadding: 1rem;
\t\tfont-size: 1rem;
\t\tfont-weight: 600;
\t\tcursor: pointer;
\t\tbox-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
\t\ttransition: transform 0.15s;
\t}

\t.start-button:hover { transform: translateY(-2px); }

\t.btn-secondary {
\t\tbackground: white;
\t\tcolor: #667eea;
\t\tborder: 2px solid #667eea;
\t\tborder-radius: 12px;
\t\tpadding: 1rem;
\t\tfont-size: 1rem;
\t\tfont-weight: 600;
\t\tcursor: pointer;
\t\ttransition: transform 0.15s, background 0.15s;
\t}

\t.action-buttons .btn-secondary { flex: 1; }
\t.btn-secondary:hover { background: #eff6ff; transform: translateY(-2px); }

\t/* ── Animations ───────────────────────────────────── */
\t@keyframes timer-pulse {
\t\t0%, 100% { transform: scale(1); opacity: 1; }
\t\t50%       { transform: scale(1.06); opacity: 0.8; }
\t}

\t/* ── Responsive ───────────────────────────────────── */
\t@media (max-width: 768px) {
\t\t.info-grid       { grid-template-columns: 1fr; }
\t\t.metrics-grid    { grid-template-columns: 1fr 1fr; }
\t\t.analysis-grid   { grid-template-columns: 1fr; }
\t\t.response-buttons { flex-direction: column; align-items: center; }
\t\t.resp-btn        { width: 100%; max-width: 360px; }
\t\t.action-buttons  { flex-direction: column; }
\t\t.game-status-bar { flex-direction: column; align-items: flex-start; }
\t\t.search-arena    { height: 50vh; min-height: 320px; }
\t}
</style>
"""

with open(
    r'd:\NeuroBloom\frontend-svelte\src\routes\training\visual-search\+page.svelte',
    'w',
    encoding='utf-8'
) as f:
    f.write(CONTENT)

lines = CONTENT.count('\n') + 1
print(f'Done. Lines: {lines}')

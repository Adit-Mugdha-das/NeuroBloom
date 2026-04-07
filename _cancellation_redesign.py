#!/usr/bin/env python3
"""Redesign Cancellation Test UI to LNS design system (sky blue #0369a1)."""

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
\timport { getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
\timport { user } from '$lib/stores';
\timport { onMount } from 'svelte';

\tlet gamePhase = 'loading'; // loading | intro | playing | results
\tlet trialData = null;
\tlet grid = [];
\tlet targetItems = [];
\tlet markedPositions = [];
\tlet startTime = null;
\tlet elapsedTime = 0;
\tlet timerInterval = null;
\tlet taskId = null;

\tlet results = null;
\tlet earnedBadges = [];
\tlet playMode = TASK_PLAY_MODE.RECORDED;
\tlet practiceStatusMessage = '';

\tlet loadError = false;
\tlet saveError = false;

\t// Fixed large cell size for accessibility (visual impairments)
\tconst cellSize = '55px';
\tconst cellFontSize = '1.2rem';

\tfunction lt(en, bn) {
\t\treturn localeText({ en, bn }, $locale);
\t}

\tfunction formatTime(seconds) {
\t\tconst mins = Math.floor(seconds / 60);
\t\tconst secs = seconds % 60;
\t\treturn `${mins}:${secs.toString().padStart(2, '0')}`;
\t}

\tfunction performanceLabel(rating) {
\t\tconst map = {
\t\t\texcellent:    lt('Excellent', 'অসাধারণ'),
\t\t\tgood:         lt('Good', 'ভালো'),
\t\t\taverage:      lt('Average', 'মোটামুটি'),
\t\t\tbelow_average: lt('Below Average', 'নিচের গড়'),
\t\t\tpoor:         lt('Poor', 'দুর্বল')
\t\t};
\t\treturn map[rating] || rating;
\t}

\tonMount(async () => {
\t\tif (!$user) {
\t\t\tgoto('/login');
\t\t\treturn;
\t\t}
\t\tawait loadTrial();
\t});

\tasync function loadTrial() {
\t\ttry {
\t\t\tloadError = false;
\t\t\tconst response = await fetch(
\t\t\t\t`${API_BASE_URL}/api/training/tasks/cancellation-test/generate/${$user.id}`,
\t\t\t\t{
\t\t\t\t\tmethod: 'POST',
\t\t\t\t\theaders: { 'Content-Type': 'application/json' },
\t\t\t\t\tcredentials: 'include'
\t\t\t\t}
\t\t\t);
\t\t\tif (!response.ok) throw new Error('Failed to load trial');
\t\t\tconst data = await response.json();
\t\t\ttrialData = data.trial_data;
\t\t\tgrid = trialData.grid;
\t\t\ttargetItems = trialData.target_items;
\t\t\telapsedTime = 0;
\t\t\tgamePhase = 'intro';
\t\t} catch (_) {
\t\t\tloadError = true;
\t\t\tgamePhase = 'intro';
\t\t}
\t}

\tfunction startGame(nextMode = TASK_PLAY_MODE.RECORDED) {
\t\tplayMode = nextMode;
\t\tpracticeStatusMessage = '';
\t\tmarkedPositions = [];
\t\tstartTime = Date.now();
\t\telapsedTime = 0;
\t\tgamePhase = 'playing';
\t\ttimerInterval = setInterval(() => {
\t\t\telapsedTime = Math.floor((Date.now() - startTime) / 1000);
\t\t}, 100);
\t}

\tfunction toggleCell(row, col, item) {
\t\tconst existingIndex = markedPositions.findIndex(p => p.row === row && p.col === col);
\t\tif (existingIndex >= 0) {
\t\t\tmarkedPositions = markedPositions.filter((_, i) => i !== existingIndex);
\t\t} else {
\t\t\tmarkedPositions = [...markedPositions, { row, col, item }];
\t\t}
\t}

\tfunction isMarked(row, col) {
\t\treturn markedPositions.some(p => p.row === row && p.col === col);
\t}

\tfunction finishGame() {
\t\tif (timerInterval) {
\t\t\tclearInterval(timerInterval);
\t\t\ttimerInterval = null;
\t\t}
\t\tsubmitResults();
\t}

\tasync function submitResults() {
\t\tif (playMode === TASK_PLAY_MODE.PRACTICE) {
\t\t\tplayMode = TASK_PLAY_MODE.RECORDED;
\t\t\tpracticeStatusMessage = getPracticeCopy($locale).complete;
\t\t\tgamePhase = 'intro';
\t\t\treturn;
\t\t}
\t\tsaveError = false;
\t\tconst completionTime = (Date.now() - startTime) / 1000;
\t\ttaskId = $page.url.searchParams.get('taskId');
\t\ttry {
\t\t\tconst response = await fetch(
\t\t\t\t`${API_BASE_URL}/api/training/tasks/cancellation-test/submit/${$user.id}`,
\t\t\t\t{
\t\t\t\t\tmethod: 'POST',
\t\t\t\t\theaders: { 'Content-Type': 'application/json' },
\t\t\t\t\tcredentials: 'include',
\t\t\t\t\tbody: JSON.stringify({
\t\t\t\t\t\tmarked_positions: markedPositions,
\t\t\t\t\t\ttarget_positions: trialData.target_positions,
\t\t\t\t\t\tcompletion_time: completionTime,
\t\t\t\t\t\tsuggested_time: trialData.suggested_time,
\t\t\t\t\t\tdifficulty: trialData.difficulty,
\t\t\t\t\t\ttask_id: taskId
\t\t\t\t\t})
\t\t\t\t}
\t\t\t);
\t\t\tif (!response.ok) throw new Error('Failed to submit results');
\t\t\tresults = await response.json();
\t\t\tearnedBadges = results.new_badges || [];
\t\t\tgamePhase = 'results';
\t\t} catch (_) {
\t\t\tsaveError = true;
\t\t\tgamePhase = 'results';
\t\t}
\t}

\tfunction restartTask() {
\t\tgamePhase = 'loading';
\t\tresults = null;
\t\tearnedBadges = [];
\t\tloadTrial();
\t}
</script>

<div class="ct-page" data-localize-skip>
\t<div class="ct-wrapper">

\t\t{#if gamePhase === 'loading'}
\t\t\t<LoadingSkeleton />

\t\t{:else if gamePhase === 'intro'}

\t\t\t<!-- Header Card -->
\t\t\t<div class="header-card">
\t\t\t\t<div class="header-content">
\t\t\t\t\t<div class="header-text">
\t\t\t\t\t\t<h1 class="task-title">{lt('Cancellation Test', 'ক্যান্সেলেশন টেস্ট')}</h1>
\t\t\t\t\t\t<p class="task-domain">{lt('Visual Scanning · Sustained Attention', 'ভিজ্যুয়াল স্ক্যানিং · টেকসই মনোযোগ')}</p>
\t\t\t\t\t</div>
\t\t\t\t\t<DifficultyBadge difficulty={trialData?.difficulty || 1} domain="Visual Scanning" />
\t\t\t\t</div>
\t\t\t</div>

\t\t\t{#if playMode === TASK_PLAY_MODE.PRACTICE}
\t\t\t\t<PracticeModeBanner locale={$locale} />
\t\t\t{/if}

\t\t\t{#if loadError}
\t\t\t\t<div class="error-card">
\t\t\t\t\t<p>{lt('Failed to load task. Please try again.', 'টাস্ক লোড করতে ব্যর্থ। আবার চেষ্টা করুন।')}</p>
\t\t\t\t\t<button class="start-button" on:click={loadTrial}>
\t\t\t\t\t\t{lt('Retry', 'আবার চেষ্টা করুন')}
\t\t\t\t\t</button>
\t\t\t\t</div>
\t\t\t{:else if trialData}

\t\t\t\t<!-- Task Concept -->
\t\t\t\t<div class="card task-concept">
\t\t\t\t\t<div class="concept-badge">
\t\t\t\t\t\t<span class="badge-label">{lt('Visual Scanning', 'ভিজ্যুয়াল স্ক্যানিং')}</span>
\t\t\t\t\t\t<span>{lt('Sustained Attention', 'টেকসই মনোযোগ')}</span>
\t\t\t\t\t</div>
\t\t\t\t\t<p class="concept-desc">
\t\t\t\t\t\t{trialData.instructions}
\t\t\t\t\t</p>
\t\t\t\t</div>

\t\t\t\t<!-- Target Display -->
\t\t\t\t<div class="card">
\t\t\t\t\t<h2 class="section-title">{lt('Your Target', 'আপনার লক্ষ্য')}</h2>
\t\t\t\t\t<p class="target-subtext">{lt('Find and click every instance of the following in the grid:', 'গ্রিডে নিচের প্রতিটি উদাহরণ খুঁজে ক্লিক করুন:')}</p>
\t\t\t\t\t<div class="target-chips">
\t\t\t\t\t\t{#each targetItems as t}
\t\t\t\t\t\t\t<div class="target-chip">{t}</div>
\t\t\t\t\t\t{/each}
\t\t\t\t\t</div>
\t\t\t\t\t<div class="target-count-row">
\t\t\t\t\t\t<span class="target-count-label">{lt('Total targets in grid:', 'গ্রিডে মোট লক্ষ্য:')}</span>
\t\t\t\t\t\t<span class="target-count-value">{trialData.target_count}</span>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Rules Card -->
\t\t\t\t<div class="card">
\t\t\t\t\t<h2 class="section-title">{lt('Rules', 'নিয়মাবলী')}</h2>
\t\t\t\t\t<div class="rules-list">
\t\t\t\t\t\t<div class="rule-item">
\t\t\t\t\t\t\t<div class="rule-num">1</div>
\t\t\t\t\t\t\t<div class="rule-text">{lt('Click every cell that contains a target item — do not skip any', 'প্রতিটি টার্গেট সেল ক্লিক করুন — কোনোটি বাদ দেবেন না')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="rule-item">
\t\t\t\t\t\t\t<div class="rule-num">2</div>
\t\t\t\t\t\t\t<div class="rule-text">{lt('Click a marked cell again to unmark it if you made a mistake', 'ভুল করলে চিহ্নিত সেলটি আবার ক্লিক করে চিহ্ন তুলে নিন')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="rule-item">
\t\t\t\t\t\t\t<div class="rule-num">3</div>
\t\t\t\t\t\t\t<div class="rule-text">{lt('Scan systematically — left to right, row by row', 'পদ্ধতিগতভাবে স্ক্যান করুন — বাম থেকে ডানে, সারি থেকে সারি')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="rule-item">
\t\t\t\t\t\t\t<div class="rule-num">4</div>
\t\t\t\t\t\t\t<div class="rule-text">{lt('No time limit — prioritize accuracy over speed', 'কোনো সময়সীমা নেই — গতির চেয়ে নির্ভুলতাকে অগ্রাধিকার দিন')}</div>
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
\t\t\t\t\t\t\t\t<span>{lt('Stimulus Type', 'উদ্দীপক ধরন')}</span>
\t\t\t\t\t\t\t\t<strong>{trialData.use_symbols ? lt('Symbols', 'প্রতীক') : lt('Letters', 'অক্ষর')}</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{lt('Targets to Find', 'খুঁজতে হবে')}</span>
\t\t\t\t\t\t\t\t<strong>{trialData.target_count}</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{lt('Difficulty', 'কঠিনতা')}</span>
\t\t\t\t\t\t\t\t<strong>{lt(`Level ${trialData.difficulty} / 10`, `স্তর ${trialData.difficulty} / ১০`)}</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{lt('No Time Limit', 'সময়সীমা নেই')}</span>
\t\t\t\t\t\t\t\t<strong>{lt('Self-paced', 'নিজের গতিতে')}</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t\t<!-- Scoring Info -->
\t\t\t\t\t<div class="card">
\t\t\t\t\t\t<h3 class="card-title">{lt('How You Are Scored', 'স্কোরিং পদ্ধতি')}</h3>
\t\t\t\t\t\t<div class="details-list">
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{lt('Primary Metric', 'প্রাথমিক পরিমাপ')}</span>
\t\t\t\t\t\t\t\t<strong>{lt('Accuracy %', 'নির্ভুলতা %')}</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{lt('Also Tracked', 'অতিরিক্ত পরিমাপ')}</span>
\t\t\t\t\t\t\t\t<strong>{lt('Completion time', 'সম্পন্ন সময়')}</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{lt('Penalised For', 'জরিমানা')}</span>
\t\t\t\t\t\t\t\t<strong>{lt('Misses + false alarms', 'বাদ + ভুল ক্লিক')}</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{lt('Spatial Check', 'স্থানিক পরীক্ষা')}</span>
\t\t\t\t\t\t\t\t<strong>{lt('Left vs Right bias', 'বাম বনাম ডান পক্ষপাতিত্ব')}</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Clinical Basis -->
\t\t\t\t<div class="clinical-info">
\t\t\t\t\t<div class="clinical-header">
\t\t\t\t\t\t<div class="clinical-badge">{lt('Clinical Basis', 'ক্লিনিকাল ভিত্তি')}</div>
\t\t\t\t\t\t<h3>{lt('Validated MS Visual Attention Assessment', 'MS-এর জন্য যাচাইকৃত ভিজ্যুয়াল অ্যাটেনশন মূল্যায়ন')}</h3>
\t\t\t\t\t</div>
\t\t\t\t\t<p>
\t\t\t\t\t\t{lt(
\t\t\t\t\t\t\t'The Cancellation Test (Mesulam, 1985) measures sustained visual attention and unilateral spatial neglect. In MS, asymmetric target detection — more misses on one side — may indicate hemispatial attention deficits correlated with white matter lesion location. Scanning efficiency predicts reading speed and performance of daily functional tasks requiring visual vigilance.',
\t\t\t\t\t\t\t'ক্যান্সেলেশন টেস্ট (Mesulam, 1985) টেকসই ভিজ্যুয়াল মনোযোগ এবং একতরফা স্থানিক অবহেলা পরিমাপ করে। MS-এ একটি পাশে বেশি লক্ষ্য বাদ পড়লে সেটি হেমিস্পেশিয়াল অ্যাটেনশন ঘাটতি নির্দেশ করতে পারে।'
\t\t\t\t\t\t)}
\t\t\t\t\t</p>
\t\t\t\t</div>

\t\t\t\t<TaskPracticeActions
\t\t\t\t\tlocale={$locale}
\t\t\t\t\tstartLabel={lt('Start Task', 'টাস্ক শুরু করুন')}
\t\t\t\t\tstatusMessage={practiceStatusMessage}
\t\t\t\t\ton:start={() => startGame(TASK_PLAY_MODE.RECORDED)}
\t\t\t\t\ton:practice={() => startGame(TASK_PLAY_MODE.PRACTICE)}
\t\t\t\t/>

\t\t\t{:else}
\t\t\t\t<LoadingSkeleton />
\t\t\t{/if}

\t\t{:else if gamePhase === 'playing'}

\t\t\t<div class="game-card" style="--cell-size: {cellSize}; --cell-font-size: {cellFontSize};">
\t\t\t\t{#if playMode === TASK_PLAY_MODE.PRACTICE}
\t\t\t\t\t<PracticeModeBanner locale={$locale} />
\t\t\t\t{/if}

\t\t\t\t<!-- Status Bar -->
\t\t\t\t<div class="game-status-bar">
\t\t\t\t\t<div class="find-label-group">
\t\t\t\t\t\t<span class="find-label">{lt('Find:', 'খুঁজুন:')}</span>
\t\t\t\t\t\t<div class="find-chips">
\t\t\t\t\t\t\t{#each targetItems as t}
\t\t\t\t\t\t\t\t<span class="find-chip">{t}</span>
\t\t\t\t\t\t\t{/each}
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t\t<div class="game-stats">
\t\t\t\t\t\t<div class="stat-pill progress-pill">
\t\t\t\t\t\t\t<span class="stat-value">{markedPositions.length}</span>
\t\t\t\t\t\t\t<span class="stat-sep">/</span>
\t\t\t\t\t\t\t<span class="stat-total">{trialData.target_count}</span>
\t\t\t\t\t\t\t<span class="stat-label">{lt('marked', 'চিহ্নিত')}</span>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="stat-pill timer-pill">
\t\t\t\t\t\t\t<span class="timer-value">{formatTime(elapsedTime)}</span>
\t\t\t\t\t\t\t<span class="stat-label">{lt('elapsed', 'অতিবাহিত')}</span>
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Grid Container -->
\t\t\t\t<div class="grid-container">
\t\t\t\t\t<div class="grid-inner">
\t\t\t\t\t\t{#each grid as row, rowIndex}
\t\t\t\t\t\t\t<div class="grid-row">
\t\t\t\t\t\t\t\t{#each row as item, colIndex}
\t\t\t\t\t\t\t\t\t<button
\t\t\t\t\t\t\t\t\t\ton:click={() => toggleCell(rowIndex, colIndex, item)}
\t\t\t\t\t\t\t\t\t\tclass="grid-cell"
\t\t\t\t\t\t\t\t\t\tclass:marked={isMarked(rowIndex, colIndex)}
\t\t\t\t\t\t\t\t\t>
\t\t\t\t\t\t\t\t\t\t{item}
\t\t\t\t\t\t\t\t\t</button>
\t\t\t\t\t\t\t\t{/each}
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t{/each}
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Finish Button -->
\t\t\t\t<div class="finish-row">
\t\t\t\t\t<button class="finish-btn" on:click={finishGame}>
\t\t\t\t\t\t{lt('Finish Task', 'টাস্ক শেষ করুন')}
\t\t\t\t\t</button>
\t\t\t\t</div>
\t\t\t</div>

\t\t{:else if gamePhase === 'results'}

\t\t\t<!-- Results Header -->
\t\t\t<div class="results-header">
\t\t\t\t<div class="score-pill">
\t\t\t\t\t<span class="score-label">{lt('Score', 'স্কোর')}</span>
\t\t\t\t\t<span class="score-value">{results ? results.score : '—'}</span>
\t\t\t\t\t<span class="score-max">%</span>
\t\t\t\t</div>
\t\t\t\t<p class="results-subtitle">
\t\t\t\t\t{lt('Cancellation Test Complete', 'ক্যান্সেলেশন টেস্ট সম্পন্ন')} ·
\t\t\t\t\t{results ? performanceLabel(results.performance_rating) : ''}
\t\t\t\t</p>
\t\t\t</div>

\t\t\t{#if saveError}
\t\t\t\t<div class="warn-card">
\t\t\t\t\t{lt('Error saving results. Your progress may not have been recorded.', 'ফলাফল সংরক্ষণে ত্রুটি। আপনার অগ্রগতি রেকর্ড নাও হতে পারে।')}
\t\t\t\t</div>
\t\t\t{/if}

\t\t\t{#if results}
\t\t\t\t<!-- Key Metrics -->
\t\t\t\t<div class="metrics-grid">
\t\t\t\t\t<div class="metric-card metric-green">
\t\t\t\t\t\t<div class="metric-value">{results.accuracy.toFixed(1)}%</div>
\t\t\t\t\t\t<div class="metric-label">{lt('Accuracy', 'নির্ভুলতা')}</div>
\t\t\t\t\t</div>
\t\t\t\t\t<div class="metric-card metric-blue">
\t\t\t\t\t\t<div class="metric-value">{results.targets_found}<span class="metric-denom">/{results.total_targets}</span></div>
\t\t\t\t\t\t<div class="metric-label">{lt('Targets Found', 'লক্ষ্য সনাক্ত')}</div>
\t\t\t\t\t</div>
\t\t\t\t\t<div class="metric-card metric-amber">
\t\t\t\t\t\t<div class="metric-value">{results.completion_time.toFixed(1)}s</div>
\t\t\t\t\t\t<div class="metric-label">{lt('Completion Time', 'সম্পন্ন সময়')}</div>
\t\t\t\t\t</div>
\t\t\t\t\t<div class="metric-card metric-red">
\t\t\t\t\t\t<div class="metric-value">{results.targets_missed + results.false_alarms}</div>
\t\t\t\t\t\t<div class="metric-label">{lt('Total Errors', 'মোট ত্রুটি')}</div>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Error Breakdown -->
\t\t\t\t<div class="card">
\t\t\t\t\t<h3 class="card-title">{lt('Error Breakdown', 'ত্রুটির বিশ্লেষণ')}</h3>
\t\t\t\t\t<div class="details-list">
\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t<span>{lt('Targets Missed', 'বাদ পড়া লক্ষ্য')}</span>
\t\t\t\t\t\t\t<strong class="error-miss">{results.targets_missed}</strong>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t<span>{lt('False Alarms', 'ভুল চিহ্নিতকরণ')}</span>
\t\t\t\t\t\t\t<strong class="error-false">{results.false_alarms}</strong>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t<span>{lt('Performance Rating', 'পারফরম্যান্স রেটিং')}</span>
\t\t\t\t\t\t\t<strong>{performanceLabel(results.performance_rating)}</strong>
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Spatial Analysis -->
\t\t\t\t{#if results.spatial_analysis}
\t\t\t\t\t<div class="card">
\t\t\t\t\t\t<h3 class="card-title">{lt('Spatial Pattern Analysis', 'স্থানিক প্যাটার্ন বিশ্লেষণ')}</h3>
\t\t\t\t\t\t<div class="spatial-grid">
\t\t\t\t\t\t\t<div class="spatial-side">
\t\t\t\t\t\t\t\t<div class="spatial-label">{lt('Left Side', 'বাম পাশ')}</div>
\t\t\t\t\t\t\t\t<div class="spatial-value">{results.spatial_analysis.left_accuracy}%</div>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="spatial-divider"></div>
\t\t\t\t\t\t\t<div class="spatial-side">
\t\t\t\t\t\t\t\t<div class="spatial-label">{lt('Right Side', 'ডান পাশ')}</div>
\t\t\t\t\t\t\t\t<div class="spatial-value">{results.spatial_analysis.right_accuracy}%</div>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t</div>

\t\t\t\t\t\t{#if results.spatial_analysis.neglect_detected}
\t\t\t\t\t\t\t<div class="neglect-warn">
\t\t\t\t\t\t\t\t<div class="neglect-title">{lt('Asymmetric Pattern Detected', 'অপ্রতিসম প্যাটার্ন সনাক্ত')}</div>
\t\t\t\t\t\t\t\t<p class="neglect-text">
\t\t\t\t\t\t\t\t\t{lt(
\t\t\t\t\t\t\t\t\t\t`You missed more targets on the ${results.spatial_analysis.neglect_side} side. Try to scan both sides of the grid equally.`,
\t\t\t\t\t\t\t\t\t\t`আপনি ${results.spatial_analysis.neglect_side} পাশে বেশি লক্ষ্য বাদ দিয়েছেন। গ্রিডের উভয় পাশ সমানভাবে স্ক্যান করার চেষ্টা করুন।`
\t\t\t\t\t\t\t\t\t)}
\t\t\t\t\t\t\t\t</p>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t{:else}
\t\t\t\t\t\t\t<div class="neglect-ok">
\t\t\t\t\t\t\t\t<div class="neglect-ok-title">{lt('Balanced Scanning Pattern', 'সুষম স্ক্যানিং প্যাটার্ন')}</div>
\t\t\t\t\t\t\t\t<p class="neglect-ok-text">
\t\t\t\t\t\t\t\t\t{lt('You scanned both sides of the grid evenly.', 'আপনি গ্রিডের উভয় পাশ সমানভাবে স্ক্যান করেছেন।')}
\t\t\t\t\t\t\t\t</p>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t{/if}
\t\t\t\t\t</div>
\t\t\t\t{/if}

\t\t\t\t<!-- Feedback -->
\t\t\t\t<div class="card">
\t\t\t\t\t<h3 class="card-title">{lt('Feedback', 'প্রতিক্রিয়া')}</h3>
\t\t\t\t\t<p class="feedback-text">{results.feedback}</p>
\t\t\t\t</div>

\t\t\t\t<!-- Difficulty Adjustment -->
\t\t\t\t{#if results.adaptation_reason}
\t\t\t\t\t<div class="adaptation-card">
\t\t\t\t\t\t<div class="adaptation-label">{lt('Difficulty Adjustment', 'কঠিনতা সমন্বয়')}</div>
\t\t\t\t\t\t<p class="adaptation-text">{results.adaptation_reason}</p>
\t\t\t\t\t</div>
\t\t\t\t{/if}
\t\t\t{/if}

\t\t\t<!-- Action Buttons -->
\t\t\t<div class="action-buttons">
\t\t\t\t<button class="start-button" on:click={() => goto('/dashboard')}>
\t\t\t\t\t{lt('Return to Dashboard', 'ড্যাশবোর্ডে ফিরুন')}
\t\t\t\t</button>
\t\t\t\t<button class="btn-secondary" on:click={restartTask}>
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
\t.ct-page {
\t\tmin-height: 100vh;
\t\tbackground: #C8DEFA;
\t\tpadding: 1.5rem;
\t}

\t.ct-wrapper {
\t\tmax-width: 1200px;
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
\t\tcolor: #0369a1;
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
\t\tbackground: linear-gradient(135deg, #075985 0%, #0369a1 100%);
\t\tcolor: white;
\t\tpadding: 0.4rem 0.9rem;
\t\tborder-radius: 2rem;
\t\tfont-size: 0.813rem;
\t\tfont-weight: 600;
\t\tmargin-bottom: 1rem;
\t}

\t.badge-label { font-weight: 700; letter-spacing: 0.04em; }
\t.concept-desc { color: #4b5563; font-size: 0.938rem; line-height: 1.6; margin: 0; }

\t/* ── Target Display ───────────────────────────────── */
\t.section-title {
\t\tfont-size: 1.125rem;
\t\tfont-weight: 600;
\t\tcolor: #1a1a2e;
\t\tmargin: 0 0 0.5rem 0;
\t}

\t.target-subtext {
\t\tcolor: #6b7280;
\t\tfont-size: 0.875rem;
\t\tmargin: 0 0 1rem 0;
\t}

\t.target-chips {
\t\tdisplay: flex;
\t\tflex-wrap: wrap;
\t\tgap: 0.625rem;
\t\tmargin-bottom: 1rem;
\t}

\t.target-chip {
\t\tbackground: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
\t\tborder: 2px solid #0369a1;
\t\tborder-radius: 10px;
\t\tpadding: 0.5rem 1.25rem;
\t\tfont-size: 1.5rem;
\t\tfont-weight: 800;
\t\tcolor: #075985;
\t\tmin-width: 3rem;
\t\ttext-align: center;
\t}

\t.target-count-row {
\t\tdisplay: flex;
\t\talign-items: center;
\t\tgap: 0.5rem;
\t\tpadding-top: 0.75rem;
\t\tborder-top: 1px solid #f0f9ff;
\t}

\t.target-count-label { font-size: 0.875rem; color: #6b7280; }
\t.target-count-value { font-size: 0.875rem; font-weight: 700; color: #0369a1; }

\t/* ── Rules List ───────────────────────────────────── */
\t.rules-list { display: flex; flex-direction: column; gap: 0.75rem; }

\t.rule-item {
\t\tdisplay: flex;
\t\talign-items: flex-start;
\t\tgap: 0.875rem;
\t\tbackground: #f0f9ff;
\t\tborder-radius: 10px;
\t\tpadding: 0.875rem 1rem;
\t}

\t.rule-num {
\t\tmin-width: 2rem;
\t\theight: 2rem;
\t\tbackground: linear-gradient(135deg, #075985 0%, #0369a1 100%);
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
\t\tmargin-bottom: 1.5rem;
\t\tflex-wrap: wrap;
\t}

\t.find-label-group {
\t\tdisplay: flex;
\t\talign-items: center;
\t\tgap: 0.75rem;
\t\tflex-wrap: wrap;
\t}

\t.find-label {
\t\tfont-size: 1rem;
\t\tfont-weight: 700;
\t\tcolor: #075985;
\t}

\t.find-chips { display: flex; gap: 0.5rem; flex-wrap: wrap; }

\t.find-chip {
\t\tbackground: linear-gradient(135deg, #075985 0%, #0369a1 100%);
\t\tcolor: white;
\t\tpadding: 0.25rem 0.75rem;
\t\tborder-radius: 0.5rem;
\t\tfont-size: 1.125rem;
\t\tfont-weight: 700;
\t}

\t.game-stats { display: flex; gap: 0.75rem; align-items: center; }

\t.stat-pill {
\t\tdisplay: flex;
\t\talign-items: baseline;
\t\tgap: 0.25rem;
\t\tpadding: 0.5rem 1rem;
\t\tborder-radius: 2rem;
\t\tfont-weight: 700;
\t}

\t.progress-pill { background: #e0f2fe; }
\t.stat-value    { font-size: 1.375rem; color: #075985; }
\t.stat-sep      { font-size: 1rem; color: #94a3b8; }
\t.stat-total    { font-size: 1rem; color: #64748b; }
\t.stat-label    { font-size: 0.75rem; color: #64748b; font-weight: 400; margin-left: 0.25rem; }

\t.timer-pill   { background: #f8fafc; border: 2px solid #e2e8f0; }
\t.timer-value  { font-size: 1.375rem; color: #0369a1; font-variant-numeric: tabular-nums; }

\t/* ── Grid ─────────────────────────────────────────── */
\t.grid-container {
\t\tbackground: #f8fafc;
\t\tborder-radius: 12px;
\t\tpadding: 1rem;
\t\tmargin-bottom: 1.5rem;
\t\tmax-height: 60vh;
\t\toverflow: auto;
\t}

\t.grid-inner { display: inline-block; padding: 4px; }

\t.grid-row {
\t\tdisplay: flex;
\t\tgap: 3px;
\t\tmargin-bottom: 3px;
\t}

\t.grid-row:last-child { margin-bottom: 0; }

\t/* ── Grid Cell ────────────────────────────────────── */
\t.grid-cell {
\t\twidth: var(--cell-size);
\t\theight: var(--cell-size);
\t\tmin-width: var(--cell-size);
\t\tmin-height: var(--cell-size);
\t\tmax-width: var(--cell-size);
\t\tmax-height: var(--cell-size);

\t\tborder: 1px solid #cbd5e1;
\t\tbackground: white;
\t\tborder-radius: 4px;
\t\tcursor: pointer;
\t\tfont-weight: 600;
\t\tfont-size: var(--cell-font-size);
\t\tcolor: #475569;

\t\tdisplay: flex;
\t\talign-items: center;
\t\tjustify-content: center;
\t\tuser-select: none;
\t\tflex-shrink: 0;
\t\tpadding: 0;

\t\ttransition: background 0.1s, border-color 0.1s, transform 0.1s;
\t\tbox-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
\t}

\t.grid-cell:hover:not(.marked) {
\t\tbackground: #f0f9ff;
\t\tborder-color: #0369a1;
\t\tborder-width: 2px;
\t\ttransform: scale(1.08);
\t\tz-index: 10;
\t\tbox-shadow: 0 2px 6px rgba(3, 105, 161, 0.25);
\t}

\t.grid-cell.marked {
\t\tbackground: #e0f2fe;
\t\tborder: 2px solid #0369a1;
\t\tcolor: #075985;
\t\tbox-shadow: 0 2px 8px rgba(3, 105, 161, 0.3);
\t}

\t.grid-cell:active { transform: scale(0.97); }

\t/* ── Finish Row ───────────────────────────────────── */
\t.finish-row { display: flex; justify-content: center; }

\t.finish-btn {
\t\tbackground: linear-gradient(135deg, #059669 0%, #10b981 100%);
\t\tcolor: white;
\t\tborder: none;
\t\tborder-radius: 12px;
\t\tpadding: 1rem 3rem;
\t\tfont-size: 1.125rem;
\t\tfont-weight: 600;
\t\tcursor: pointer;
\t\tbox-shadow: 0 4px 12px rgba(5, 150, 105, 0.35);
\t\ttransition: transform 0.15s, opacity 0.15s;
\t}

\t.finish-btn:hover { transform: translateY(-2px); }

\t/* ── Results Header ───────────────────────────────── */
\t.results-header {
\t\tbackground: linear-gradient(135deg, #075985 0%, #0369a1 100%);
\t\tborder-radius: 16px;
\t\tpadding: 1.75rem;
\t\ttext-align: center;
\t\tmargin-bottom: 1rem;
\t\tbox-shadow: 0 4px 12px rgba(3, 105, 161, 0.35);
\t}

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
\t.metric-blue  { border-top-color: #0369a1; }
\t.metric-amber { border-top-color: #d97706; }
\t.metric-red   { border-top-color: #dc2626; }

\t.metric-value { font-size: 1.625rem; font-weight: 700; color: #1a1a2e; line-height: 1; }
\t.metric-denom { font-size: 1rem; color: #9ca3af; font-weight: 400; }
\t.metric-label { font-size: 0.75rem; color: #6b7280; margin-top: 0.375rem; }

\t/* ── Error Highlights ─────────────────────────────── */
\t.error-miss  { color: #dc2626; }
\t.error-false { color: #d97706; }

\t/* ── Spatial Grid ─────────────────────────────────── */
\t.spatial-grid {
\t\tdisplay: flex;
\t\talign-items: center;
\t\tjustify-content: center;
\t\tgap: 0;
\t\tmargin-bottom: 1rem;
\t\tbackground: #f0f9ff;
\t\tborder-radius: 12px;
\t\tpadding: 1.25rem;
\t}

\t.spatial-side { text-align: center; flex: 1; }
\t.spatial-divider { width: 1px; height: 3rem; background: #bae6fd; margin: 0 1.5rem; flex-shrink: 0; }
\t.spatial-label { font-size: 0.813rem; color: #0369a1; font-weight: 600; margin-bottom: 0.25rem; }
\t.spatial-value { font-size: 1.75rem; font-weight: 700; color: #075985; }

\t/* ── Neglect Cards ────────────────────────────────── */
\t.neglect-warn {
\t\tbackground: #fef3c7;
\t\tborder: 2px solid #fcd34d;
\t\tborder-radius: 10px;
\t\tpadding: 1rem 1.25rem;
\t}

\t.neglect-title { font-weight: 700; color: #92400e; margin-bottom: 0.375rem; font-size: 0.938rem; }
\t.neglect-text  { color: #78350f; font-size: 0.875rem; margin: 0; line-height: 1.5; }

\t.neglect-ok {
\t\tbackground: #f0fdf4;
\t\tborder: 2px solid #86efac;
\t\tborder-radius: 10px;
\t\tpadding: 1rem 1.25rem;
\t}

\t.neglect-ok-title { font-weight: 700; color: #166534; margin-bottom: 0.375rem; font-size: 0.938rem; }
\t.neglect-ok-text  { color: #15803d; font-size: 0.875rem; margin: 0; }

\t/* ── Feedback ─────────────────────────────────────── */
\t.feedback-text { font-size: 0.938rem; color: #374151; line-height: 1.6; margin: 0; }

\t/* ── Adaptation Card ──────────────────────────────── */
\t.adaptation-card {
\t\tbackground: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
\t\tborder: 1px solid #7dd3fc;
\t\tborder-radius: 16px;
\t\tpadding: 1.25rem 1.5rem;
\t\tmargin-bottom: 1rem;
\t}

\t.adaptation-label { font-size: 0.875rem; font-weight: 700; color: #075985; margin-bottom: 0.375rem; }
\t.adaptation-text  { font-size: 0.875rem; color: #0369a1; margin: 0; line-height: 1.5; }

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
\t.btn-secondary:hover { background: #f0f9ff; transform: translateY(-2px); }

\t/* ── Responsive ───────────────────────────────────── */
\t@media (max-width: 768px) {
\t\t.info-grid     { grid-template-columns: 1fr; }
\t\t.metrics-grid  { grid-template-columns: 1fr 1fr; }
\t\t.action-buttons { flex-direction: column; }
\t\t.game-status-bar { flex-direction: column; align-items: flex-start; }
\t}
</style>
"""

with open(
    r'd:\NeuroBloom\frontend-svelte\src\routes\training\cancellation-test\+page.svelte',
    'w',
    encoding='utf-8'
) as f:
    f.write(CONTENT)

lines = CONTENT.count('\n') + 1
print(f'Done. Lines: {lines}')

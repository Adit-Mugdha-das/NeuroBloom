#!/usr/bin/env python3
"""Redesign Multiple Object Tracking UI to LNS design system (violet #7c3aed)."""

CONTENT = """\
<script>
\timport { goto } from '$app/navigation';
\timport { page } from '$app/stores';
\timport { generateMOTTrial, submitMOTResponse } from '$lib/api';
\timport BadgeNotification from '$lib/components/BadgeNotification.svelte';
\timport DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
\timport LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
\timport PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
\timport TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
\timport { locale, localeText } from '$lib/i18n';
\timport { getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
\timport { user } from '$lib/stores';
\timport { onDestroy, onMount } from 'svelte';

\t// ── Auth ──────────────────────────────────────────
\tlet currentUser = null;
\tuser.subscribe((value) => { currentUser = value; });

\t// ── Phase ─────────────────────────────────────────
\tlet phase = 'loading'; // loading | intro | highlighting | tracking | selection | results

\t// ── Trial Data ────────────────────────────────────
\tlet trialData = null;
\tlet difficulty = 5;
\tlet taskId = null;

\t// ── Objects ───────────────────────────────────────
\tlet objects = [];
\tlet selectedObjects = new Set();
\tlet animationId = null;
\tlet startTime = null;
\tlet timeRemaining = 0;
\tlet timerInterval = null;

\t// ── Selection Timing ──────────────────────────────
\tlet selectionStartTime = null;
\tlet selectionElapsed = 0;
\tlet selectionTimerInterval = null;

\t// ── Results ───────────────────────────────────────
\tlet results = null;
\tlet earnedBadges = [];
\tlet playMode = TASK_PLAY_MODE.RECORDED;
\tlet practiceStatusMessage = '';

\t// ── Errors ────────────────────────────────────────
\tlet loadError = false;
\tlet saveError = false;

\t// ── Constants ─────────────────────────────────────
\tconst HIGHLIGHT_DURATION = 2000;
\tconst PAUSE_BEFORE_TRACKING = 1000;

\t// ── Helpers ───────────────────────────────────────
\tfunction lt(en, bn) { return localeText({ en, bn }, $locale); }

\tfunction performanceLabel(p) {
\t\tconst map = {
\t\t\tperfect:          lt('Perfect', 'নিখুঁত'),
\t\t\texcellent:        lt('Excellent', 'অসাধারণ'),
\t\t\tgood:             lt('Good', 'ভালো'),
\t\t\taverage:          lt('Average', 'মোটামুটি'),
\t\t\tneeds_improvement: lt('Needs Improvement', 'উন্নতি দরকার')
\t\t};
\t\treturn map[p] || (p || '').replace('_', ' ');
\t}

\t// ── Lifecycle ──────────────────────────────────────
\tonMount(() => {
\t\tif (!currentUser) { goto('/login'); return; }
\t\ttaskId = $page.url.searchParams.get('taskId');
\t\tloadTrial();
\t});

\tonDestroy(() => {
\t\tstopAnimation();
\t\tif (timerInterval) clearInterval(timerInterval);
\t\tif (selectionTimerInterval) clearInterval(selectionTimerInterval);
\t});

\t// ── Game Logic ─────────────────────────────────────
\tasync function loadTrial() {
\t\ttry {
\t\t\tloadError = false;
\t\t\tphase = 'loading';
\t\t\tconst response = await generateMOTTrial(currentUser.id);
\t\t\ttrialData = response.trial_data;
\t\t\tdifficulty = response.difficulty;
\t\t\tobjects = trialData.objects.map(obj => ({
\t\t\t\t...obj,
\t\t\t\tx: obj.x,
\t\t\t\ty: obj.y,
\t\t\t\tvx: obj.vx,
\t\t\t\tvy: obj.vy,
\t\t\t\tis_target: obj.is_target,
\t\t\t\tshow_highlight: false,
\t\t\t\tradius: 20
\t\t\t}));
\t\t\tphase = 'intro';
\t\t} catch (_) {
\t\t\tloadError = true;
\t\t\tphase = 'intro';
\t\t}
\t}

\tfunction startTask(nextMode = TASK_PLAY_MODE.RECORDED) {
\t\tplayMode = nextMode;
\t\tpracticeStatusMessage = '';
\t\tselectedObjects = new Set();
\t\tresults = null;
\t\tearnedBadges = [];
\t\tselectionStartTime = null;
\t\tselectionElapsed = 0;
\t\tphase = 'highlighting';

\t\t// Show targets highlighted
\t\tobjects = objects.map(obj => ({
\t\t\t...obj,
\t\t\tshow_highlight: obj.is_target
\t\t}));

\t\tsetTimeout(() => {
\t\t\tobjects = objects.map(obj => ({ ...obj, show_highlight: false }));
\t\t\tsetTimeout(() => { startTracking(); }, PAUSE_BEFORE_TRACKING);
\t\t}, HIGHLIGHT_DURATION);
\t}

\tfunction startTracking() {
\t\tphase = 'tracking';
\t\tstartTime = Date.now();
\t\ttimeRemaining = trialData.tracking_duration;

\t\ttimerInterval = setInterval(() => {
\t\t\tconst elapsed = (Date.now() - startTime) / 1000;
\t\t\ttimeRemaining = Math.max(0, trialData.tracking_duration - elapsed);
\t\t\tif (timeRemaining <= 0) { stopTracking(); }
\t\t}, 100);

\t\tanimationId = requestAnimationFrame(updateObjects);
\t}

\tfunction updateObjects() {
\t\tconst arenaSize = trialData.arena_size;
\t\tconst radius = 20;

\t\tobjects = objects.map(obj => {
\t\t\tlet newX = obj.x + obj.vx;
\t\t\tlet newY = obj.y + obj.vy;
\t\t\tlet newVx = obj.vx;
\t\t\tlet newVy = obj.vy;

\t\t\tif (newX - radius < 0)          { newX = radius;            newVx =  Math.abs(newVx); }
\t\t\telse if (newX + radius > arenaSize) { newX = arenaSize - radius; newVx = -Math.abs(newVx); }
\t\t\tif (newY - radius < 0)          { newY = radius;            newVy =  Math.abs(newVy); }
\t\t\telse if (newY + radius > arenaSize) { newY = arenaSize - radius; newVy = -Math.abs(newVy); }

\t\t\treturn { ...obj, x: newX, y: newY, vx: newVx, vy: newVy };
\t\t});

\t\tanimationId = requestAnimationFrame(updateObjects);
\t}

\tfunction stopTracking() {
\t\tstopAnimation();
\t\tif (timerInterval) { clearInterval(timerInterval); timerInterval = null; }
\t\tselectionStartTime = Date.now();
\t\tselectionElapsed = 0;
\t\tselectionTimerInterval = setInterval(() => {
\t\t\tselectionElapsed = (Date.now() - selectionStartTime) / 1000;
\t\t}, 100);
\t\tphase = 'selection';
\t}

\tfunction stopAnimation() {
\t\tif (animationId) { cancelAnimationFrame(animationId); animationId = null; }
\t}

\tfunction toggleObjectSelection(objectId) {
\t\tif (selectedObjects.has(objectId)) {
\t\t\tselectedObjects.delete(objectId);
\t\t} else {
\t\t\tselectedObjects.add(objectId);
\t\t}
\t\tselectedObjects = selectedObjects; // trigger reactivity
\t}

\tasync function submitSelection() {
\t\tif (selectionTimerInterval) { clearInterval(selectionTimerInterval); selectionTimerInterval = null; }
\t\tconst responseTime = (Date.now() - selectionStartTime) / 1000;
\t\tsaveError = false;
\t\ttry {
\t\t\tconst response = await submitMOTResponse(currentUser.id, {
\t\t\t\ttrial_data: trialData,
\t\t\t\tuser_response: {
\t\t\t\t\tselected_objects: Array.from(selectedObjects),
\t\t\t\t\tresponse_time: responseTime
\t\t\t\t},
\t\t\t\ttask_id: taskId
\t\t\t});
\t\t\tresults = response;
\t\t\tearnedBadges = response.new_badges || [];
\t\t\tphase = 'results';
\t\t} catch (_) {
\t\t\tsaveError = true;
\t\t\tphase = 'results';
\t\t}
\t}

\tfunction nextTrial() {
\t\tif (playMode === TASK_PLAY_MODE.PRACTICE) {
\t\t\tplayMode = TASK_PLAY_MODE.RECORDED;
\t\t\tpracticeStatusMessage = getPracticeCopy($locale).complete;
\t\t\tselectedObjects = new Set();
\t\t\tresults = null;
\t\t\tearnedBadges = [];
\t\t\tselectionStartTime = null;
\t\t\tselectionElapsed = 0;
\t\t\tphase = 'intro';
\t\t\treturn;
\t\t}
\t\tselectedObjects = new Set();
\t\tresults = null;
\t\tearnedBadges = [];
\t\tselectionStartTime = null;
\t\tselectionElapsed = 0;
\t\tif (selectionTimerInterval) { clearInterval(selectionTimerInterval); selectionTimerInterval = null; }
\t\tloadTrial();
\t}
</script>

<div class="mot-page">
\t<div class="mot-wrapper">

\t\t{#if phase === 'loading'}
\t\t\t<LoadingSkeleton />

\t\t{:else if phase === 'intro'}

\t\t\t<!-- Header Card -->
\t\t\t<div class="header-card">
\t\t\t\t<div class="header-content">
\t\t\t\t\t<div class="header-text">
\t\t\t\t\t\t<h1 class="task-title">{lt('Multiple Object Tracking', 'মাল্টিপল অবজেক্ট ট্র্যাকিং')}</h1>
\t\t\t\t\t\t<p class="task-domain">{lt('Dynamic Visual Attention · Visual Scanning', 'ডায়নামিক ভিজ্যুয়াল মনোযোগ · ভিজ্যুয়াল স্ক্যানিং')}</p>
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
\t\t\t{:else if trialData}

\t\t\t\t<!-- Concept Card -->
\t\t\t\t<div class="card task-concept">
\t\t\t\t\t<div class="concept-badge">
\t\t\t\t\t\t<span class="badge-label">{lt('Multiple Object Tracking', 'MOT')}</span>
\t\t\t\t\t\t<span>{lt('Pylyshyn & Storm, 1988', 'Pylyshyn & Storm, 1988')}</span>
\t\t\t\t\t</div>
\t\t\t\t\t<p class="concept-desc">
\t\t\t\t\t\t{lt(
\t\t\t\t\t\t\t'In MOT, the visual system must simultaneously assign attentional "FINST" (fingers of instantiation) tokens to multiple moving targets. Unlike static search, this demands sustained distributed attention over time — a capacity strongly diminished by MS white-matter pathology, making it clinically relevant for driving and real-world multitasking safety.',
\t\t\t\t\t\t\t'MOT-এ ভিজ্যুয়াল সিস্টেমকে একাধিক চলমান লক্ষ্যে মনোযোগ টোকেন বরাদ্দ করতে হয়। MS শ্বেত পদার্থ ক্ষতির কারণে এই ক্ষমতা উল্লেখযোগ্যভাবে কমে যায়।'
\t\t\t\t\t\t)}
\t\t\t\t\t</p>
\t\t\t\t</div>

\t\t\t\t<!-- Rules -->
\t\t\t\t<div class="card">
\t\t\t\t\t<h2 class="section-title">{lt('How It Works', 'কীভাবে কাজ করে')}</h2>
\t\t\t\t\t<div class="rules-list">
\t\t\t\t\t\t<div class="rule-item">
\t\t\t\t\t\t\t<div class="rule-num">1</div>
\t\t\t\t\t\t\t<div class="rule-text">{lt('Several circles will flash — these are your targets to remember', 'কিছু বৃত্ত জ্বলতে থাকবে — এগুলো আপনার মনে রাখার লক্ষ্য')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="rule-item">
\t\t\t\t\t\t\t<div class="rule-num">2</div>
\t\t\t\t\t\t\t<div class="rule-text">{lt('All circles begin moving randomly — keep your eyes on the targets as they mix with distractors', 'সব বৃত্ত এলোমেলোভাবে চলতে শুরু করবে — লক্ষ্যগুলো চোখে রাখুন')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="rule-item">
\t\t\t\t\t\t\t<div class="rule-num">3</div>
\t\t\t\t\t\t\t<div class="rule-text">{lt('When movement stops, click all circles you were tracking', 'চলাচল থামলে আপনি যে বৃত্তগুলো ট্র্যাক করছিলেন সেগুলোতে ক্লিক করুন')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="rule-item">
\t\t\t\t\t\t\t<div class="rule-num">4</div>
\t\t\t\t\t\t\t<div class="rule-text">{lt('Accuracy matters more than speed — take your time during selection', 'গতির চেয়ে নির্ভুলতা বেশি গুরুত্বপূর্ণ — নির্বাচনের সময় সতর্কভাবে দেখুন')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Info Grid -->
\t\t\t\t<div class="info-grid">
\t\t\t\t\t<div class="card">
\t\t\t\t\t\t<h3 class="card-title">{lt('Task Parameters', 'টাস্কের প্যারামিটার')}</h3>
\t\t\t\t\t\t<div class="details-list">
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{lt('Total Objects', 'মোট বস্তু')}</span>
\t\t\t\t\t\t\t\t<strong>{trialData.total_objects}</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{lt('Targets to Track', 'ট্র্যাক করার লক্ষ্য')}</span>
\t\t\t\t\t\t\t\t<strong class="highlight-val">{trialData.num_targets}</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{lt('Tracking Duration', 'ট্র্যাকিং সময়কাল')}</span>
\t\t\t\t\t\t\t\t<strong>{trialData.tracking_duration}s</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{lt('Speed', 'গতি')}</span>
\t\t\t\t\t\t\t\t<strong>{trialData.speed_multiplier?.toFixed(1) || 1}×</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t\t<div class="card">
\t\t\t\t\t\t<h3 class="card-title">{lt('What to Expect', 'কী আশা করবেন')}</h3>
\t\t\t\t\t\t<div class="expect-steps">
\t\t\t\t\t\t\t<div class="expect-item">
\t\t\t\t\t\t\t\t<div class="expect-dot dot-yellow"></div>
\t\t\t\t\t\t\t\t<span>{lt('Yellow flash = your targets (2 seconds)', 'হলুদ ঝলক = আপনার লক্ষ্য (২ সেকেন্ড)')}</span>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="expect-item">
\t\t\t\t\t\t\t\t<div class="expect-dot dot-blue"></div>
\t\t\t\t\t\t\t\t<span>{lt('All circles identical while moving', 'চলার সময় সব বৃত্ত একই রকম')}</span>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="expect-item">
\t\t\t\t\t\t\t\t<div class="expect-dot dot-green"></div>
\t\t\t\t\t\t\t\t<span>{lt('Green highlight = selected (click again to deselect)', 'সবুজ = নির্বাচিত (আবার ক্লিক করুন বাতিল করতে)')}</span>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Clinical Basis -->
\t\t\t\t<div class="clinical-info">
\t\t\t\t\t<div class="clinical-header">
\t\t\t\t\t\t<div class="clinical-badge">{lt('Clinical Basis', 'ক্লিনিকাল ভিত্তি')}</div>
\t\t\t\t\t\t<h3>{lt('MS Driving Safety & Dynamic Attention', 'MS ড্রাইভিং নিরাপত্তা ও ডায়নামিক মনোযোগ')}</h3>
\t\t\t\t\t</div>
\t\t\t\t\t<p>
\t\t\t\t\t\t{lt(
\t\t\t\t\t\t\t'Multiple Object Tracking (Pylyshyn & Storm, 1988) directly predicts real-world divided attention performance including driving safety. MS-related deficits in sustained and divided visual attention significantly impair MOT capacity, particularly when tracking 3+ objects, making this paradigm a sensitive ecologically-valid measure of functional visual attention in everyday tasks.',
\t\t\t\t\t\t\t'মাল্টিপল অবজেক্ট ট্র্যাকিং (Pylyshyn & Storm, 1988) সরাসরি ড্রাইভিং নিরাপত্তাসহ বাস্তব জীবনের বিভক্ত মনোযোগের পূর্বাভাস দেয়। MS-সংক্রান্ত ভিজ্যুয়াল মনোযোগের ঘাটতি MOT ক্ষমতাকে উল্লেখযোগ্যভাবে ক্ষতিগ্রস্ত করে।'
\t\t\t\t\t\t)}
\t\t\t\t\t</p>
\t\t\t\t</div>

\t\t\t\t<TaskPracticeActions
\t\t\t\t\tlocale={$locale}
\t\t\t\t\tstartLabel={lt('Begin Tracking Task', 'ট্র্যাকিং টাস্ক শুরু করুন')}
\t\t\t\t\tstatusMessage={practiceStatusMessage}
\t\t\t\t\ton:start={() => startTask(TASK_PLAY_MODE.RECORDED)}
\t\t\t\t\ton:practice={() => startTask(TASK_PLAY_MODE.PRACTICE)}
\t\t\t\t/>

\t\t\t{:else}
\t\t\t\t<LoadingSkeleton />
\t\t\t{/if}

\t\t{:else if phase === 'highlighting' || phase === 'tracking' || phase === 'selection'}

\t\t\t<!-- Arena Header -->
\t\t\t<div class="arena-header-card">
\t\t\t\t{#if playMode === TASK_PLAY_MODE.PRACTICE}
\t\t\t\t\t<PracticeModeBanner locale={$locale} />
\t\t\t\t{/if}

\t\t\t\t{#if phase === 'highlighting'}
\t\t\t\t\t<div class="phase-status phase-highlight">
\t\t\t\t\t\t<div class="phase-icon-block dot-yellow-lg"></div>
\t\t\t\t\t\t<div>
\t\t\t\t\t\t\t<div class="phase-label">{lt('Phase 1 — Memorise Targets', 'ধাপ ১ — লক্ষ্য মনে রাখুন')}</div>
\t\t\t\t\t\t\t<div class="phase-desc">{lt('The highlighted circles are your targets — remember them', 'হাইলাইট করা বৃত্তগুলো আপনার লক্ষ্য — এগুলো মনে রাখুন')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>

\t\t\t\t{:else if phase === 'tracking'}
\t\t\t\t\t<div class="phase-status phase-tracking">
\t\t\t\t\t\t<div class="timer-block">
\t\t\t\t\t\t\t<div class="timer-value {timeRemaining < 3 ? 'timer-critical' : ''}">{timeRemaining.toFixed(1)}</div>
\t\t\t\t\t\t\t<div class="timer-label">{lt('seconds left', 'সেকেন্ড বাকি')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div>
\t\t\t\t\t\t\t<div class="phase-label">{lt('Phase 2 — Track the Targets', 'ধাপ ২ — লক্ষ্য ট্র্যাক করুন')}</div>
\t\t\t\t\t\t\t<div class="phase-desc">{lt('Keep your eyes on the targets — do not look away!', 'লক্ষ্যের উপর চোখ রাখুন — দূরে তাকাবেন না!')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>

\t\t\t\t{:else}
\t\t\t\t\t<div class="phase-status phase-selection">
\t\t\t\t\t\t<div class="selection-count-block">
\t\t\t\t\t\t\t<span class="sel-count {selectedObjects.size === trialData.num_targets ? 'sel-complete' : ''}">{selectedObjects.size}</span>
\t\t\t\t\t\t\t<span class="sel-sep">/</span>
\t\t\t\t\t\t\t<span class="sel-total">{trialData.num_targets}</span>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div>
\t\t\t\t\t\t\t<div class="phase-label">{lt('Phase 3 — Select Targets', 'ধাপ ৩ — লক্ষ্য নির্বাচন করুন')}</div>
\t\t\t\t\t\t\t<div class="phase-desc">{lt('Click all circles you were tracking · Time elapsed:', 'আপনি যে বৃত্তগুলো ট্র্যাক করছিলেন সেগুলো ক্লিক করুন · সময়:')} {selectionElapsed.toFixed(1)}s</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t{/if}
\t\t\t</div>

\t\t\t<!-- Tracking Arena -->
\t\t\t<div class="arena-wrapper">
\t\t\t\t<div class="arena-box" style="width: {trialData.arena_size}px; height: {trialData.arena_size}px; max-width: 100%;">
\t\t\t\t\t<svg width={trialData.arena_size} height={trialData.arena_size} style="display:block; max-width:100%;">
\t\t\t\t\t\t{#each objects as obj (obj.id)}
\t\t\t\t\t\t\t{#if phase === 'selection'}
\t\t\t\t\t\t\t\t<circle
\t\t\t\t\t\t\t\t\tcx={obj.x}
\t\t\t\t\t\t\t\t\tcy={obj.y}
\t\t\t\t\t\t\t\t\tr={obj.radius}
\t\t\t\t\t\t\t\t\tclass="tracking-object selectable"
\t\t\t\t\t\t\t\t\tclass:selected={selectedObjects.has(obj.id)}
\t\t\t\t\t\t\t\t\trole="button"
\t\t\t\t\t\t\t\t\ttabindex="0"
\t\t\t\t\t\t\t\t\ton:click={() => toggleObjectSelection(obj.id)}
\t\t\t\t\t\t\t\t\ton:keydown={(e) => e.key === 'Enter' && toggleObjectSelection(obj.id)}
\t\t\t\t\t\t\t\t/>
\t\t\t\t\t\t\t{:else}
\t\t\t\t\t\t\t\t<circle
\t\t\t\t\t\t\t\t\tcx={obj.x}
\t\t\t\t\t\t\t\t\tcy={obj.y}
\t\t\t\t\t\t\t\t\tr={obj.radius}
\t\t\t\t\t\t\t\t\tclass="tracking-object"
\t\t\t\t\t\t\t\t\tclass:highlighted={obj.show_highlight}
\t\t\t\t\t\t\t\t/>
\t\t\t\t\t\t\t{/if}
\t\t\t\t\t\t{/each}
\t\t\t\t\t</svg>
\t\t\t\t</div>
\t\t\t</div>

\t\t\t<!-- Submit Button (selection phase only) -->
\t\t\t{#if phase === 'selection'}
\t\t\t\t<div class="submit-row">
\t\t\t\t\t<button
\t\t\t\t\t\tclass="submit-btn"
\t\t\t\t\t\ton:click={submitSelection}
\t\t\t\t\t\tdisabled={selectedObjects.size === 0}
\t\t\t\t\t>
\t\t\t\t\t\t{lt(`Confirm ${selectedObjects.size} Selection${selectedObjects.size !== 1 ? 's' : ''}`, `${selectedObjects.size}টি নির্বাচন নিশ্চিত করুন`)}
\t\t\t\t\t</button>
\t\t\t\t</div>
\t\t\t{/if}

\t\t{:else if phase === 'results'}

\t\t\t<!-- Results Header -->
\t\t\t<div class="results-header perf-{results?.performance || 'default'}">
\t\t\t\t<div class="score-pill">
\t\t\t\t\t<span class="score-label">{lt('Score', 'স্কোর')}</span>
\t\t\t\t\t<span class="score-value">{results ? (results.score * 100).toFixed(0) : '—'}</span>
\t\t\t\t\t<span class="score-max">%</span>
\t\t\t\t</div>
\t\t\t\t<p class="results-subtitle">
\t\t\t\t\t{lt('MOT Complete', 'MOT সম্পন্ন')} ·
\t\t\t\t\t{results ? performanceLabel(results.performance) : ''}
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
\t\t\t\t\t<div class="metric-card metric-violet">
\t\t\t\t\t\t<div class="metric-value">{(results.score * 100).toFixed(0)}%</div>
\t\t\t\t\t\t<div class="metric-label">{lt('Overall Score', 'সামগ্রিক স্কোর')}</div>
\t\t\t\t\t</div>
\t\t\t\t\t<div class="metric-card metric-green">
\t\t\t\t\t\t<div class="metric-value">{results.targets_found}/{results.total_targets}</div>
\t\t\t\t\t\t<div class="metric-label">{lt('Targets Found', 'লক্ষ্য খুঁজে পাওয়া')}</div>
\t\t\t\t\t</div>
\t\t\t\t\t<div class="metric-card metric-blue">
\t\t\t\t\t\t<div class="metric-value">{(results.accuracy * 100).toFixed(0)}%</div>
\t\t\t\t\t\t<div class="metric-label">{lt('Recall Accuracy', 'রিকল নির্ভুলতা')}</div>
\t\t\t\t\t</div>
\t\t\t\t\t<div class="metric-card metric-amber">
\t\t\t\t\t\t<div class="metric-value">{results.false_positives}</div>
\t\t\t\t\t\t<div class="metric-label">{lt('False Alarms', 'মিথ্যা সংকেত')}</div>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Secondary Metrics -->
\t\t\t\t<div class="card">
\t\t\t\t\t<h3 class="card-title">{lt('Detailed Analysis', 'বিস্তারিত বিশ্লেষণ')}</h3>
\t\t\t\t\t<div class="analysis-grid">
\t\t\t\t\t\t<div class="analysis-cell">
\t\t\t\t\t\t\t<div class="analysis-label">{lt('Precision', 'নির্ভুলতা')}</div>
\t\t\t\t\t\t\t<div class="analysis-value">{(results.precision * 100).toFixed(0)}%</div>
\t\t\t\t\t\t\t<div class="analysis-desc">{lt('Correct out of all selected', 'নির্বাচিতের মধ্যে সঠিক')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="analysis-cell">
\t\t\t\t\t\t\t<div class="analysis-label">{lt('F1 Score', 'F1 স্কোর')}</div>
\t\t\t\t\t\t\t<div class="analysis-value">{(results.f1_score * 100).toFixed(0)}%</div>
\t\t\t\t\t\t\t<div class="analysis-desc">{lt('Balanced precision–recall metric', 'সুষম নির্ভুলতা–স্মরণ মেট্রিক')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="analysis-cell">
\t\t\t\t\t\t\t<div class="analysis-label">{lt('Tracking Efficiency', 'ট্র্যাকিং দক্ষতা')}</div>
\t\t\t\t\t\t\t<div class="analysis-value">{(results.tracking_efficiency * 100).toFixed(0)}%</div>
\t\t\t\t\t\t\t<div class="analysis-desc">{results.targets_missed} {lt('missed', 'মিস')} · {results.false_positives} {lt('extra', 'অতিরিক্ত')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="analysis-cell">
\t\t\t\t\t\t\t<div class="analysis-label">{lt('Selection Time', 'নির্বাচন সময়')}</div>
\t\t\t\t\t\t\t<div class="analysis-value">{results.response_time.toFixed(1)}s</div>
\t\t\t\t\t\t\t<div class="analysis-desc">{lt('Time taken to identify targets', 'লক্ষ্য চিহ্নিত করতে নেওয়া সময়')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t{#if results.feedback_message}
\t\t\t\t\t<div class="feedback-card">
\t\t\t\t\t\t<div class="feedback-dot"></div>
\t\t\t\t\t\t<p class="feedback-text">{results.feedback_message}</p>
\t\t\t\t\t</div>
\t\t\t\t{/if}

\t\t\t\t<!-- Difficulty Adaptation -->
\t\t\t\t{#if results.new_difficulty !== results.old_difficulty || results.adaptation_reason}
\t\t\t\t\t<div class="adaptation-card">
\t\t\t\t\t\t<div class="adaptation-label">
\t\t\t\t\t\t\t{#if results.new_difficulty > results.old_difficulty}
\t\t\t\t\t\t\t\t{lt('Difficulty Increased', 'কঠিনতা বৃদ্ধি')} — {results.old_difficulty} → {results.new_difficulty}
\t\t\t\t\t\t\t{:else if results.new_difficulty < results.old_difficulty}
\t\t\t\t\t\t\t\t{lt('Difficulty Decreased', 'কঠিনতা হ্রাস')} — {results.old_difficulty} → {results.new_difficulty}
\t\t\t\t\t\t\t{:else}
\t\t\t\t\t\t\t\t{lt('Difficulty Maintained', 'কঠিনতা বজায়')} — {lt(`Level ${results.new_difficulty}`, `স্তর ${results.new_difficulty}`)}
\t\t\t\t\t\t\t{/if}
\t\t\t\t\t\t</div>
\t\t\t\t\t\t{#if results.adaptation_reason}
\t\t\t\t\t\t\t<p class="adaptation-text">{results.adaptation_reason}</p>
\t\t\t\t\t\t{/if}
\t\t\t\t\t</div>
\t\t\t\t{/if}
\t\t\t{/if}

\t\t\t<!-- Action Buttons -->
\t\t\t<div class="action-buttons">
\t\t\t\t<button class="start-button" on:click={nextTrial}>
\t\t\t\t\t{playMode === TASK_PLAY_MODE.PRACTICE ? lt('Finish Practice', 'অনুশীলন শেষ করুন') : lt('Next Trial', 'পরবর্তী ট্রায়াল')}
\t\t\t\t</button>
\t\t\t\t<button class="btn-secondary" on:click={() => goto('/dashboard')}>
\t\t\t\t\t{lt('Return to Dashboard', 'ড্যাশবোর্ডে ফিরুন')}
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
\t.mot-page {
\t\tmin-height: 100vh;
\t\tbackground: #C8DEFA;
\t\tpadding: 1.5rem;
\t}

\t.mot-wrapper {
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
\t\tcolor: #7c3aed;
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
\t\tbackground: linear-gradient(135deg, #4c1d95 0%, #7c3aed 100%);
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
\t\tmargin: 0 0 1rem 0;
\t}

\t/* ── Rules List ───────────────────────────────────── */
\t.rules-list { display: flex; flex-direction: column; gap: 0.75rem; }

\t.rule-item {
\t\tdisplay: flex;
\t\talign-items: flex-start;
\t\tgap: 0.875rem;
\t\tbackground: #f5f3ff;
\t\tborder-radius: 10px;
\t\tpadding: 0.875rem 1rem;
\t}

\t.rule-num {
\t\tmin-width: 2rem;
\t\theight: 2rem;
\t\tbackground: linear-gradient(135deg, #4c1d95 0%, #7c3aed 100%);
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
\t.detail-row strong { color: #1a1a2e; }
\t.highlight-val     { color: #7c3aed; font-size: 1.125rem; }

\t/* ── Expect Steps ─────────────────────────────────── */
\t.expect-steps { display: flex; flex-direction: column; gap: 0.75rem; }

\t.expect-item {
\t\tdisplay: flex;
\t\talign-items: center;
\t\tgap: 0.75rem;
\t\tfont-size: 0.875rem;
\t\tcolor: #374151;
\t}

\t.expect-dot {
\t\twidth: 1.25rem;
\t\theight: 1.25rem;
\t\tborder-radius: 50%;
\t\tflex-shrink: 0;
\t}

\t.dot-yellow { background: #fbbf24; border: 3px solid #f59e0b; }
\t.dot-blue   { background: #60a5fa; border: 3px solid #3b82f6; }
\t.dot-green  { background: #4ade80; border: 3px solid #22c55e; }

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

\t/* ── Arena Header Card ────────────────────────────── */
\t.arena-header-card {
\t\tbackground: white;
\t\tborder-radius: 16px;
\t\tpadding: 1.25rem 1.5rem;
\t\tbox-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
\t\tmargin-bottom: 1rem;
\t}

\t.phase-status {
\t\tdisplay: flex;
\t\talign-items: center;
\t\tgap: 1rem;
\t\tflex-wrap: wrap;
\t}

\t.phase-label { font-size: 0.938rem; font-weight: 700; color: #1a1a2e; }
\t.phase-desc  { font-size: 0.813rem; color: #6b7280; margin-top: 0.125rem; }

\t/* Phase highlight icon */
\t.dot-yellow-lg {
\t\twidth: 2.5rem;
\t\theight: 2.5rem;
\t\tborder-radius: 50%;
\t\tbackground: #fbbf24;
\t\tborder: 3px solid #f59e0b;
\t\tbox-shadow: 0 0 12px rgba(251, 191, 36, 0.6);
\t\tanimation: highlight-pulse 1s ease-in-out infinite;
\t\tflex-shrink: 0;
\t}

\t/* Timer Block */
\t.timer-block { text-align: center; }

\t.timer-value {
\t\tfont-size: 2rem;
\t\tfont-weight: 800;
\t\tcolor: #7c3aed;
\t\tline-height: 1;
\t\tfont-variant-numeric: tabular-nums;
\t}

\t.timer-critical { color: #dc2626; animation: timer-pulse 0.5s ease-in-out infinite; }
\t.timer-label    { font-size: 0.6875rem; color: #6b7280; }

\t/* Selection Count Block */
\t.selection-count-block {
\t\tdisplay: flex;
\t\talign-items: baseline;
\t\tgap: 0.125rem;
\t}

\t.sel-count {
\t\tfont-size: 1.75rem;
\t\tfont-weight: 800;
\t\tcolor: #7c3aed;
\t\tline-height: 1;
\t}

\t.sel-count.sel-complete { color: #16a34a; }
\t.sel-sep   { font-size: 1rem; color: #9ca3af; margin: 0 0.1rem; }
\t.sel-total { font-size: 1.25rem; font-weight: 700; color: #6b7280; }

\t/* ── Arena ────────────────────────────────────────── */
\t.arena-wrapper {
\t\tdisplay: flex;
\t\tjustify-content: center;
\t\tmargin-bottom: 1rem;
\t}

\t.arena-box {
\t\tbackground: white;
\t\tborder-radius: 16px;
\t\tbox-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
\t\tpadding: 4px;
\t\toverflow: hidden;
\t}

\t.arena-box svg {
\t\tbackground: #f8f7ff;
\t\tborder-radius: 12px;
\t\tborder: 2px solid #ede9fe;
\t}

\t/* ── SVG Objects ─────────────────────────────────── */
\t:global(.tracking-object) {
\t\tfill: #818cf8;
\t\tstroke: #4f46e5;
\t\tstroke-width: 2;
\t}

\t:global(.tracking-object.highlighted) {
\t\tfill: #fbbf24;
\t\tstroke: #d97706;
\t\tstroke-width: 3;
\t\tfilter: drop-shadow(0 0 8px rgba(251, 191, 36, 0.7));
\t\tanimation: highlight-pulse 0.8s ease-in-out infinite;
\t}

\t:global(.tracking-object.selectable) {
\t\tcursor: pointer;
\t\tfill: #a5b4fc;
\t\tstroke: #6366f1;
\t\tstroke-width: 2;
\t\ttransition: fill 0.15s, stroke 0.15s;
\t}

\t:global(.tracking-object.selectable:hover) {
\t\tfill: #c4b5fd;
\t\tstroke: #7c3aed;
\t\tstroke-width: 3;
\t}

\t:global(.tracking-object.selected) {
\t\tfill: #4ade80;
\t\tstroke: #16a34a;
\t\tstroke-width: 3;
\t\tfilter: drop-shadow(0 0 6px rgba(74, 222, 128, 0.6));
\t}

\t/* ── Submit Row ───────────────────────────────────── */
\t.submit-row {
\t\tdisplay: flex;
\t\tjustify-content: center;
\t\tmargin-bottom: 1rem;
\t}

\t.submit-btn {
\t\tpadding: 1rem 3rem;
\t\tbackground: linear-gradient(135deg, #4c1d95 0%, #7c3aed 100%);
\t\tcolor: white;
\t\tborder: none;
\t\tborder-radius: 14px;
\t\tfont-size: 1.063rem;
\t\tfont-weight: 700;
\t\tcursor: pointer;
\t\tbox-shadow: 0 4px 14px rgba(124, 58, 237, 0.4);
\t\ttransition: transform 0.15s, box-shadow 0.15s;
\t}

\t.submit-btn:hover:not(:disabled) {
\t\ttransform: translateY(-2px);
\t\tbox-shadow: 0 8px 20px rgba(124, 58, 237, 0.5);
\t}

\t.submit-btn:disabled { opacity: 0.45; cursor: not-allowed; }

\t/* ── Results Header ───────────────────────────────── */
\t.results-header {
\t\tborder-radius: 16px;
\t\tpadding: 1.75rem;
\t\ttext-align: center;
\t\tmargin-bottom: 1rem;
\t\tbackground: linear-gradient(135deg, #4c1d95 0%, #7c3aed 100%);
\t\tbox-shadow: 0 4px 12px rgba(124, 58, 237, 0.35);
\t}

\t.perf-perfect    { background: linear-gradient(135deg, #92400e 0%, #d97706 100%); box-shadow: 0 4px 12px rgba(217, 119, 6, 0.4); }
\t.perf-excellent  { background: linear-gradient(135deg, #14532d 0%, #16a34a 100%); box-shadow: 0 4px 12px rgba(22, 163, 74, 0.4); }
\t.perf-good       { background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%); box-shadow: 0 4px 12px rgba(30, 58, 138, 0.35); }

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

\t.metric-violet { border-top-color: #7c3aed; }
\t.metric-green  { border-top-color: #16a34a; }
\t.metric-blue   { border-top-color: #1e40af; }
\t.metric-amber  { border-top-color: #d97706; }

\t.metric-value { font-size: 1.5rem; font-weight: 700; color: #1a1a2e; line-height: 1; }
\t.metric-label { font-size: 0.75rem; color: #6b7280; margin-top: 0.375rem; }

\t/* ── Analysis Grid ────────────────────────────────── */
\t.analysis-grid {
\t\tdisplay: grid;
\t\tgrid-template-columns: repeat(4, 1fr);
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

\t/* ── Feedback Card ────────────────────────────────── */
\t.feedback-card {
\t\tdisplay: flex;
\t\talign-items: flex-start;
\t\tgap: 1rem;
\t\tbackground: #f0fdf4;
\t\tborder: 1px solid #bbf7d0;
\t\tborder-radius: 12px;
\t\tpadding: 1.25rem;
\t\tmargin-bottom: 1rem;
\t}

\t.feedback-dot {
\t\twidth: 0.5rem;
\t\theight: 0.5rem;
\t\tborder-radius: 50%;
\t\tbackground: #16a34a;
\t\tflex-shrink: 0;
\t\tmargin-top: 0.375rem;
\t}

\t.feedback-text { font-size: 0.938rem; color: #166534; line-height: 1.6; margin: 0; }

\t/* ── Adaptation Card ──────────────────────────────── */
\t.adaptation-card {
\t\tbackground: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
\t\tborder: 1px solid #ddd6fe;
\t\tborder-radius: 16px;
\t\tpadding: 1.25rem 1.5rem;
\t\tmargin-bottom: 1rem;
\t}

\t.adaptation-label { font-size: 0.875rem; font-weight: 700; color: #4c1d95; margin-bottom: 0.375rem; }
\t.adaptation-text  { font-size: 0.875rem; color: #7c3aed; margin: 0; line-height: 1.5; }

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
\t.btn-secondary:hover { background: #f5f3ff; transform: translateY(-2px); }

\t/* ── Animations ───────────────────────────────────── */
\t@keyframes highlight-pulse {
\t\t0%, 100% { transform: scale(1); opacity: 1; }
\t\t50%       { transform: scale(1.15); opacity: 0.85; }
\t}

\t@keyframes timer-pulse {
\t\t0%, 100% { transform: scale(1); opacity: 1; }
\t\t50%       { transform: scale(1.08); opacity: 0.8; }
\t}

\t/* ── Responsive ───────────────────────────────────── */
\t@media (max-width: 768px) {
\t\t.info-grid      { grid-template-columns: 1fr; }
\t\t.metrics-grid   { grid-template-columns: 1fr 1fr; }
\t\t.analysis-grid  { grid-template-columns: 1fr 1fr; }
\t\t.action-buttons { flex-direction: column; }
\t\t.phase-status   { gap: 0.75rem; }
\t}
</style>
"""

with open(
    r'd:\NeuroBloom\frontend-svelte\src\routes\training\multiple-object-tracking\+page.svelte',
    'w',
    encoding='utf-8'
) as f:
    f.write(CONTENT)

lines = CONTENT.count('\n') + 1
print(f'Done. Lines: {lines}')

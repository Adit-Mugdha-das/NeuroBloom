#!/usr/bin/env python3
"""Redesign Category Fluency UI to LNS design system (teal #0891b2)."""

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
\timport { formatNumber, locale, localeText, translateText } from '$lib/i18n';
\timport { buildPracticePayload, getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
\timport { user } from '$lib/stores';
\timport { onMount } from 'svelte';

\tlet gamePhase = 'loading';
\tlet trialData = null;
\tlet timeRemaining = 60;
\tlet timer = null;
\tlet startTime = null;
\tlet taskId = null;
\tlet loadError = false;
\tlet saveError = false;

\tlet currentInput = '';
\tlet submittedWords = [];
\tlet results = null;
\tlet earnedBadges = [];
\t/** @type {string} */
\tlet playMode = TASK_PLAY_MODE.RECORDED;
\tlet practiceStatusMessage = '';
\tlet recordedTrialData = null;

\tfunction t(text) {
\t\treturn translateText(text, $locale);
\t}

\tfunction n(value, options = {}) {
\t\treturn formatNumber(value, $locale, options);
\t}

\tfunction localizedCategoryName(value = trialData?.category_name ?? '') {
\t\treturn t(value);
\t}

\tfunction localizedExamples(values = trialData?.examples ?? []) {
\t\treturn values.map((value) => t(value)).join(', ');
\t}

\tfunction categoryInstructionText() {
\t\tif (!trialData) return '';
\t\tif ($locale === 'bn') {
\t\t\treturn `আপনার কাছে ${n(trialData.time_limit_seconds || 60)} সেকেন্ড সময় আছে। এই বিভাগের যত বেশি সম্ভব শব্দ লিখুন। প্রতিটি শব্দ লিখে এন্টার চাপুন।`;
\t\t}
\t\treturn trialData.instructions;
\t}

\tfunction categoryTipText() {
\t\tif ($locale === 'bn') {
\t\t\treturn 'মূল বিভাগটিকে ছোট ছোট ভাগে ভেবে দেখুন। যেমন পেশা হলে চিকিৎসা, শিক্ষা, প্রযুক্তি, রান্না, অফিসকাজ - এভাবে ভাগ করলে দ্রুত আরও শব্দ মনে আসবে।';
\t\t}
\t\treturn 'Try thinking of subcategories! For example, if the category is "Animals," think of farm animals, pets, wild animals, birds, etc.';
\t}

\tfunction compactSeconds(value) {
\t\treturn $locale === 'bn' ? `${n(value)}স` : `${value}s`;
\t}

\tfunction performanceLabel(rating) {
\t\tconst labels = {
\t\t\texcellent: $locale === 'bn' ? 'অসাধারণ' : 'Excellent',
\t\t\tgood: $locale === 'bn' ? 'ভালো' : 'Good',
\t\t\taverage: $locale === 'bn' ? 'মোটামুটি' : 'Average',
\t\t\tbelow_average: $locale === 'bn' ? 'আরও অনুশীলন দরকার' : 'Below Average'
\t\t};
\t\treturn labels[rating] || rating;
\t}

\tfunction performanceFeedback() {
\t\tif (!results) return '';
\t\tif ($locale !== 'bn') {
\t\t\treturn t(results.feedback);
\t\t}
\t\tconst parts = [];
\t\tconst uniqueCount = Number(results.unique_count) || 0;
\t\tconst duplicateCount = Number(results.duplicate_count) || 0;
\t\tif (results.performance_rating === 'excellent') {
\t\t\tparts.push(`দারুণ! আপনি ${n(uniqueCount)}টি ভিন্ন শব্দ লিখেছেন।`);
\t\t} else if (results.performance_rating === 'good') {
\t\t\tparts.push(`ভালো করেছেন! আপনি ${n(uniqueCount)}টি ভিন্ন শব্দ লিখেছেন।`);
\t\t} else if (results.performance_rating === 'average') {
\t\t\tparts.push(`আপনি ${n(uniqueCount)}টি ভিন্ন শব্দ লিখেছেন।`);
\t\t} else {
\t\t\tparts.push(`আপনি ${n(uniqueCount)}টি ভিন্ন শব্দ লিখেছেন। পরের বার আরও বেশি শব্দ ভাবার চেষ্টা করুন।`);
\t\t}
\t\tif (duplicateCount > 0) {
\t\t\tparts.push(`নোট: ${n(duplicateCount)}টি পুনরাবৃত্ত শব্দ গণনায় ধরা হয়নি।`);
\t\t}
\t\tif (uniqueCount < 10) {
\t\t\tparts.push('পরামর্শ: উপবিভাগ ধরে ভাবলে আরও শব্দ দ্রুত মনে আসতে পারে।');
\t\t}
\t\treturn parts.join(' ');
\t}

\tfunction progressBadgeLabel() {
\t\tif (submittedWords.length >= 15) {
\t\t\treturn $locale === 'bn' ? 'দারুণ!' : 'Outstanding!';
\t\t}
\t\tif (submittedWords.length >= 10) {
\t\t\treturn $locale === 'bn' ? 'ভালো অগ্রগতি' : 'Good Progress';
\t\t}
\t\treturn '';
\t}

\tfunction focusWordInput() {
\t\tdocument.getElementById('word-input')?.focus();
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
\t\t\t\t`${API_BASE_URL}/api/training/tasks/category-fluency/generate/${$user.id}`,
\t\t\t\t{
\t\t\t\t\tmethod: 'POST',
\t\t\t\t\theaders: { 'Content-Type': 'application/json' },
\t\t\t\t\tcredentials: 'include'
\t\t\t\t}
\t\t\t);
\t\t\tif (!response.ok) throw new Error('Failed to load trial');
\t\t\tconst data = await response.json();
\t\t\ttrialData = structuredClone(data.trial_data);
\t\t\trecordedTrialData = structuredClone(data.trial_data);
\t\t\tgamePhase = 'intro';
\t\t} catch (_) {
\t\t\tloadError = true;
\t\t\tgamePhase = 'intro';
\t\t}
\t}

\t/** @param {string} nextMode */
\tfunction startTrial(nextMode = TASK_PLAY_MODE.RECORDED) {
\t\tplayMode = nextMode;
\t\tpracticeStatusMessage = '';
\t\ttrialData =
\t\t\tnextMode === TASK_PLAY_MODE.PRACTICE
\t\t\t\t? buildPracticePayload('category-fluency', recordedTrialData)
\t\t\t\t: structuredClone(recordedTrialData);
\t\ttimeRemaining = trialData?.time_limit_seconds || 60;
\t\tcurrentInput = '';
\t\tsubmittedWords = [];
\t\tgamePhase = 'trial';
\t\tstartTime = Date.now();
\t\ttimer = setInterval(() => {
\t\t\ttimeRemaining--;
\t\t\tif (timeRemaining <= 0) {
\t\t\t\tendTrial();
\t\t\t}
\t\t}, 1000);
\t\tsetTimeout(() => {
\t\t\tfocusWordInput();
\t\t}, 100);
\t}

\tfunction submitWord() {
\t\tif (!currentInput.trim()) return;
\t\tconst word = currentInput.trim();
\t\tsubmittedWords = [...submittedWords, word];
\t\tcurrentInput = '';
\t\tsetTimeout(() => {
\t\t\tfocusWordInput();
\t\t}, 0);
\t}

\tfunction handleKeyPress(event) {
\t\tif (event.key === 'Enter') {
\t\t\tevent.preventDefault();
\t\t\tsubmitWord();
\t\t}
\t}

\tfunction removeWord(index) {
\t\tsubmittedWords = submittedWords.filter((_, i) => i !== index);
\t}

\tasync function endTrial() {
\t\tclearInterval(timer);
\t\tconst timeTaken = (Date.now() - startTime) / 1000;

\t\tif (playMode === TASK_PLAY_MODE.PRACTICE) {
\t\t\ttrialData = structuredClone(recordedTrialData);
\t\t\tplayMode = TASK_PLAY_MODE.RECORDED;
\t\t\tpracticeStatusMessage = getPracticeCopy($locale).complete;
\t\t\tgamePhase = 'intro';
\t\t\treturn;
\t\t}

\t\ttaskId = $page.url.searchParams.get('taskId');

\t\ttry {
\t\t\tsaveError = false;
\t\t\tconst response = await fetch(
\t\t\t\t`${API_BASE_URL}/api/training/tasks/category-fluency/submit/${$user.id}`,
\t\t\t\t{
\t\t\t\t\tmethod: 'POST',
\t\t\t\t\theaders: { 'Content-Type': 'application/json' },
\t\t\t\t\tcredentials: 'include',
\t\t\t\t\tbody: JSON.stringify({
\t\t\t\t\t\tsubmitted_words: submittedWords,
\t\t\t\t\t\ttime_taken_seconds: timeTaken,
\t\t\t\t\t\tdifficulty: trialData.difficulty,
\t\t\t\t\t\tcategory_name: trialData.category_name,
\t\t\t\t\t\ttask_id: taskId
\t\t\t\t\t})
\t\t\t\t}
\t\t\t);
\t\t\tif (!response.ok) throw new Error('Failed to score trial');
\t\t\tconst data = await response.json();
\t\t\tresults = {
\t\t\t\tnormalized_score: data.score,
\t\t\t\tunique_count: data.unique_count,
\t\t\t\ttotal_submitted: data.total_submitted,
\t\t\t\tduplicate_count: data.duplicate_count,
\t\t\t\tperformance_rating: data.performance_rating,
\t\t\t\twords_per_second: data.words_per_second,
\t\t\t\tfeedback: data.feedback,
\t\t\t\tshould_advance: data.new_difficulty > data.old_difficulty,
\t\t\t\tunique_words: submittedWords.filter(
\t\t\t\t\t(w, i, arr) => arr.findIndex((x) => x.toLowerCase() === w.toLowerCase()) === i
\t\t\t\t),
\t\t\t\tinvalid_words: []
\t\t\t};
\t\t\tif (data.new_badges && data.new_badges.length > 0) {
\t\t\t\tearnedBadges = data.new_badges;
\t\t\t}
\t\t\tuser.update((u) => ({
\t\t\t\t...u,
\t\t\t\tplanning_difficulty: data.new_difficulty
\t\t\t}));
\t\t\tgamePhase = 'results';
\t\t} catch (_) {
\t\t\tsaveError = true;
\t\t\tgamePhase = 'results';
\t\t}
\t}
</script>

<div class="cf-page" data-localize-skip>
\t<div class="cf-wrapper">

\t\t{#if gamePhase === 'loading'}
\t\t\t<LoadingSkeleton />

\t\t{:else if gamePhase === 'intro'}

\t\t\t<!-- Header Card -->
\t\t\t<div class="header-card">
\t\t\t\t<div class="header-content">
\t\t\t\t\t<div class="header-text">
\t\t\t\t\t\t<h1 class="task-title">{t('Category Fluency')}</h1>
\t\t\t\t\t\t<p class="task-domain">{t('Semantic Fluency · Planning / Executive Function')}</p>
\t\t\t\t\t</div>
\t\t\t\t\t<DifficultyBadge difficulty={trialData?.difficulty || 1} domain="Executive Planning" />
\t\t\t\t</div>
\t\t\t</div>

\t\t\t{#if playMode === TASK_PLAY_MODE.PRACTICE}
\t\t\t\t<PracticeModeBanner locale={$locale} />
\t\t\t{/if}

\t\t\t{#if loadError}
\t\t\t\t<div class="error-card">
\t\t\t\t\t<p>{t('Failed to load task. Please try again.')}</p>
\t\t\t\t\t<button class="start-button" on:click={loadTrial}>
\t\t\t\t\t\t{t('Retry')}
\t\t\t\t\t</button>
\t\t\t\t</div>
\t\t\t{:else if trialData}

\t\t\t\t<!-- Task Concept -->
\t\t\t\t<div class="card task-concept">
\t\t\t\t\t<div class="concept-badge">
\t\t\t\t\t\t<span class="badge-icon">Semantic</span>
\t\t\t\t\t\t<span>{t('Executive Planning')}</span>
\t\t\t\t\t</div>
\t\t\t\t\t<p class="concept-desc">
\t\t\t\t\t\t{categoryInstructionText()}
\t\t\t\t\t</p>
\t\t\t\t</div>

\t\t\t\t<!-- Clinical Info -->
\t\t\t\t<div class="clinical-info">
\t\t\t\t\t<div class="clinical-header">
\t\t\t\t\t\t<div class="clinical-badge">{t('Clinical Basis')}</div>
\t\t\t\t\t\t<h3>{t('Validated MS Semantic Memory Assessment')}</h3>
\t\t\t\t\t</div>
\t\t\t\t\t<p>
\t\t\t\t\t\t{t(
\t\t\t\t\t\t\t'Category Fluency (Henry & Crawford, 2004) measures semantic memory access and executive retrieval strategy. Semantic fluency deficits in MS reflect reduced processing speed and working memory capacity. Benchmarks such as Animals (< 14/min) and Vegetables (< 10/min) are sensitive MS screening markers included in the MACFIMS and BICAMS batteries.'
\t\t\t\t\t\t)}
\t\t\t\t\t</p>
\t\t\t\t</div>

\t\t\t\t<!-- Rules Card -->
\t\t\t\t<div class="card">
\t\t\t\t\t<h2 class="section-title">{t('Rules')}</h2>
\t\t\t\t\t<div class="rules-list">
\t\t\t\t\t\t<div class="rule-item">
\t\t\t\t\t\t\t<div class="rule-num">1</div>
\t\t\t\t\t\t\t<div class="rule-text">
\t\t\t\t\t\t\t\t{t('Type each word and press')} <strong>{$locale === 'bn' ? 'এন্টার' : 'Enter'}</strong> {t('to submit it')}
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="rule-item">
\t\t\t\t\t\t\t<div class="rule-num">2</div>
\t\t\t\t\t\t\t<div class="rule-text">{t('Submit as many words as you can in the time allowed')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="rule-item">
\t\t\t\t\t\t\t<div class="rule-num">3</div>
\t\t\t\t\t\t\t<div class="rule-text">{t('Duplicate words are automatically filtered — only unique items are counted')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="rule-item">
\t\t\t\t\t\t\t<div class="rule-num">4</div>
\t\t\t\t\t\t\t<div class="rule-text">
\t\t\t\t\t\t\t\t{t('You can remove a word before the timer ends by clicking the')} <strong>×</strong> {t('on its chip')}
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Info Grid -->
\t\t\t\t<div class="info-grid">
\t\t\t\t\t<div class="card">
\t\t\t\t\t\t<!-- Category Highlight -->
\t\t\t\t\t\t<h3 class="card-title">{t('Your Category')}</h3>
\t\t\t\t\t\t<div class="category-highlight">
\t\t\t\t\t\t\t<div class="category-name">{localizedCategoryName()}</div>
\t\t\t\t\t\t\t<div class="category-examples">
\t\t\t\t\t\t\t\t<span class="examples-label">{t('Examples:')}</span>
\t\t\t\t\t\t\t\t{localizedExamples()}
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t\t<div class="card">
\t\t\t\t\t\t<h3 class="card-title">{t('What It Measures')}</h3>
\t\t\t\t\t\t<div class="details-list">
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{t('Primary Metric')}</span>
\t\t\t\t\t\t\t\t<strong>{t('Unique words / 60s')}</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{t('Cognitive Domain')}</span>
\t\t\t\t\t\t\t\t<strong>{t('Semantic memory')}</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{t('Time Limit')}</span>
\t\t\t\t\t\t\t\t<strong>{trialData.time_limit_seconds || 60}s</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{t('Difficulty')}</span>
\t\t\t\t\t\t\t\t<strong>{t(`Level ${trialData.difficulty} / 10`)}</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Strategy Tip -->
\t\t\t\t<div class="tip-card">
\t\t\t\t\t<div class="tip-icon">TIP</div>
\t\t\t\t\t<div class="tip-body">
\t\t\t\t\t\t<div class="tip-title">{t('Subcategory Strategy')}</div>
\t\t\t\t\t\t<p class="tip-text">{categoryTipText()}</p>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Performance Guide -->
\t\t\t\t<div class="card perf-guide">
\t\t\t\t\t<h3 class="card-title">{t('Performance Norms (unique words / 60s)')}</h3>
\t\t\t\t\t<p class="perf-subtitle">{t('Based on MS patient reference data')}</p>
\t\t\t\t\t<div class="norm-bars">
\t\t\t\t\t\t<div class="norm-bar">
\t\t\t\t\t\t\t<div class="norm-label">{t('Excellent')}</div>
\t\t\t\t\t\t\t<div class="norm-track"><div class="norm-fill norm-excellent"></div></div>
\t\t\t\t\t\t\t<div class="norm-range">&gt; 18</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="norm-bar">
\t\t\t\t\t\t\t<div class="norm-label">{t('Normal (MS)')}</div>
\t\t\t\t\t\t\t<div class="norm-track"><div class="norm-fill norm-normal"></div></div>
\t\t\t\t\t\t\t<div class="norm-range">12–18</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="norm-bar">
\t\t\t\t\t\t\t<div class="norm-label">{t('Impaired')}</div>
\t\t\t\t\t\t\t<div class="norm-track"><div class="norm-fill norm-impaired"></div></div>
\t\t\t\t\t\t\t<div class="norm-range">&lt; 12</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<TaskPracticeActions
\t\t\t\t\tlocale={$locale}
\t\t\t\t\tstartLabel={localeText({ en: 'Start Category Task', bn: 'বিভাগ টাস্ক শুরু করুন' }, $locale)}
\t\t\t\t\tstatusMessage={practiceStatusMessage}
\t\t\t\t\ton:start={() => startTrial(TASK_PLAY_MODE.RECORDED)}
\t\t\t\t\ton:practice={() => startTrial(TASK_PLAY_MODE.PRACTICE)}
\t\t\t\t/>

\t\t\t{:else}
\t\t\t\t<LoadingSkeleton />
\t\t\t{/if}

\t\t{:else if gamePhase === 'trial'}

\t\t\t<div class="game-card">
\t\t\t\t{#if playMode === TASK_PLAY_MODE.PRACTICE}
\t\t\t\t\t<PracticeModeBanner locale={$locale} />
\t\t\t\t{/if}

\t\t\t\t<!-- Status Bar -->
\t\t\t\t<div class="game-status-bar">
\t\t\t\t\t<div class="category-display-row">
\t\t\t\t\t\t<div class="category-display">{localizedCategoryName()}</div>
\t\t\t\t\t\t<div class="status-pills">
\t\t\t\t\t\t\t<span class="pill pill-cf">
\t\t\t\t\t\t\t\t{$locale === 'bn'
\t\t\t\t\t\t\t\t\t? `${n(submittedWords.length)}টি শব্দ`
\t\t\t\t\t\t\t\t\t: `${submittedWords.length} word${submittedWords.length !== 1 ? 's' : ''}`}
\t\t\t\t\t\t\t</span>
\t\t\t\t\t\t\t{#if progressBadgeLabel()}
\t\t\t\t\t\t\t\t<span class="pill pill-progress">{progressBadgeLabel()}</span>
\t\t\t\t\t\t\t{/if}
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t\t<div class="timer-display" class:timer-urgent={timeRemaining <= 10}>
\t\t\t\t\t\t{compactSeconds(timeRemaining)}
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Word Entry -->
\t\t\t\t<div class="input-card">
\t\t\t\t\t<label for="word-input" class="input-label">
\t\t\t\t\t\t{t('Type a word and press Enter:')}
\t\t\t\t\t</label>
\t\t\t\t\t<div class="input-row">
\t\t\t\t\t\t<input
\t\t\t\t\t\t\tid="word-input"
\t\t\t\t\t\t\ttype="text"
\t\t\t\t\t\t\tbind:value={currentInput}
\t\t\t\t\t\t\ton:keypress={handleKeyPress}
\t\t\t\t\t\t\tplaceholder={t('Type your word here...')}
\t\t\t\t\t\t\tclass="word-input"
\t\t\t\t\t\t/>
\t\t\t\t\t\t<button class="submit-btn" on:click={submitWord} disabled={!currentInput.trim()}>
\t\t\t\t\t\t\t{t('Add')}
\t\t\t\t\t\t</button>
\t\t\t\t\t</div>
\t\t\t\t\t<p class="input-tip">{t('Tip: Press Enter to add words quickly')}</p>
\t\t\t\t</div>

\t\t\t\t<!-- Submitted Words -->
\t\t\t\t<div class="words-section">
\t\t\t\t\t<h3 class="words-heading">
\t\t\t\t\t\t{t('Your Words')} ({n(submittedWords.length)})
\t\t\t\t\t</h3>
\t\t\t\t\t<div class="words-area" class:words-area-empty={submittedWords.length === 0}>
\t\t\t\t\t\t{#each submittedWords as word, index}
\t\t\t\t\t\t\t<span class="word-chip">
\t\t\t\t\t\t\t\t{word}
\t\t\t\t\t\t\t\t<button
\t\t\t\t\t\t\t\t\tclass="chip-remove"
\t\t\t\t\t\t\t\t\ton:click={() => removeWord(index)}
\t\t\t\t\t\t\t\t\ttitle={t('Remove word')}
\t\t\t\t\t\t\t\t\taria-label={t('Remove word')}
\t\t\t\t\t\t\t\t>×</button>
\t\t\t\t\t\t\t</span>
\t\t\t\t\t\t{/each}
\t\t\t\t\t\t{#if submittedWords.length === 0}
\t\t\t\t\t\t\t<span class="words-empty">{t('No words yet — start typing!')}</span>
\t\t\t\t\t\t{/if}
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- End Early -->
\t\t\t\t<div class="skip-row">
\t\t\t\t\t<button class="btn-secondary" on:click={endTrial}>
\t\t\t\t\t\t{t('Finish Early')}
\t\t\t\t\t</button>
\t\t\t\t</div>
\t\t\t</div>

\t\t{:else if gamePhase === 'results'}

\t\t\t<!-- Results Header -->
\t\t\t<div class="results-header">
\t\t\t\t<div class="score-pill">
\t\t\t\t\t<span class="score-label">{t('Score')}</span>
\t\t\t\t\t<span class="score-value">
\t\t\t\t\t\t{results ? n(results.normalized_score, { maximumFractionDigits: 0 }) : '—'}
\t\t\t\t\t</span>
\t\t\t\t\t<span class="score-max">/100</span>
\t\t\t\t</div>
\t\t\t\t<p class="results-subtitle">{t('Category Fluency Complete')} · {localizedCategoryName()}</p>
\t\t\t</div>

\t\t\t{#if saveError}
\t\t\t\t<div class="warn-card">
\t\t\t\t\t{t('Error saving results. Your progress may not have been recorded.')}
\t\t\t\t</div>
\t\t\t{/if}

\t\t\t{#if results}
\t\t\t\t<!-- Key Metrics -->
\t\t\t\t<div class="metrics-grid">
\t\t\t\t\t<div class="metric-card metric-teal">
\t\t\t\t\t\t<div class="metric-value">{n(results.unique_count)}</div>
\t\t\t\t\t\t<div class="metric-label">{t('Unique Words')}</div>
\t\t\t\t\t</div>
\t\t\t\t\t<div class="metric-card metric-amber">
\t\t\t\t\t\t<div class="metric-value">
\t\t\t\t\t\t\t{n(results.words_per_second, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="metric-label">{t('Words / Second')}</div>
\t\t\t\t\t</div>
\t\t\t\t\t<div
\t\t\t\t\t\tclass="metric-card"
\t\t\t\t\t\tclass:metric-excellent={results.performance_rating === 'excellent'}
\t\t\t\t\t\tclass:metric-good={results.performance_rating === 'good'}
\t\t\t\t\t\tclass:metric-below={results.performance_rating === 'below_average' ||
\t\t\t\t\t\t\tresults.performance_rating === 'average'}
\t\t\t\t\t>
\t\t\t\t\t\t<div class="metric-value">{performanceLabel(results.performance_rating)}</div>
\t\t\t\t\t\t<div class="metric-label">{t('Performance')}</div>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Feedback -->
\t\t\t\t<div class="card">
\t\t\t\t\t<h3 class="card-title">{t('Feedback')}</h3>
\t\t\t\t\t<p class="feedback-text">{performanceFeedback()}</p>

\t\t\t\t\t{#if results.unique_words && results.unique_words.length > 0}
\t\t\t\t\t\t<div class="words-result-section">
\t\t\t\t\t\t\t<h4 class="words-result-heading words-valid-heading">{t('Valid Words')}</h4>
\t\t\t\t\t\t\t<div class="words-result-area">
\t\t\t\t\t\t\t\t{#each results.unique_words as word}
\t\t\t\t\t\t\t\t\t<span class="word-chip word-result">{word}</span>
\t\t\t\t\t\t\t\t{/each}
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t{/if}

\t\t\t\t\t{#if results.invalid_words && results.invalid_words.length > 0}
\t\t\t\t\t\t<div class="words-result-section">
\t\t\t\t\t\t\t<h4 class="words-result-heading words-invalid-heading">{t('Duplicates / Invalid')}</h4>
\t\t\t\t\t\t\t<div class="words-result-area words-invalid-area">
\t\t\t\t\t\t\t\t{#each results.invalid_words as word}
\t\t\t\t\t\t\t\t\t<span class="word-chip word-invalid">{word}</span>
\t\t\t\t\t\t\t\t{/each}
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t{/if}

\t\t\t\t\t{#if results.duplicate_count > 0}
\t\t\t\t\t\t<p class="dupe-note">
\t\t\t\t\t\t\t{$locale === 'bn'
\t\t\t\t\t\t\t\t? `${n(results.duplicate_count)}টি পুনরাবৃত্ত শব্দ বাদ দেওয়া হয়েছে।`
\t\t\t\t\t\t\t\t: `${results.duplicate_count} duplicate${results.duplicate_count !== 1 ? 's' : ''} removed.`}
\t\t\t\t\t\t</p>
\t\t\t\t\t{/if}
\t\t\t\t</div>

\t\t\t\t<!-- Level Up -->
\t\t\t\t{#if results.should_advance}
\t\t\t\t\t<div class="levelup-card">
\t\t\t\t\t\t<div class="levelup-badge">{t('Level Up')}</div>
\t\t\t\t\t\t<p>
\t\t\t\t\t\t\t{$locale === 'bn'
\t\t\t\t\t\t\t\t? `দারুণ পারফরম্যান্স! কঠিনতা লেভেল ${n(trialData.difficulty + 1)}-এ উন্নীত হচ্ছে।`
\t\t\t\t\t\t\t\t: `Great performance! Moving to difficulty level ${trialData.difficulty + 1}.`}
\t\t\t\t\t\t</p>
\t\t\t\t\t</div>
\t\t\t\t{/if}
\t\t\t{/if}

\t\t\t<!-- Action Buttons -->
\t\t\t<div class="action-buttons">
\t\t\t\t<button class="start-button" on:click={() => goto('/dashboard')}>
\t\t\t\t\t{t('Return to Dashboard')}
\t\t\t\t</button>
\t\t\t\t<button class="btn-secondary" on:click={() => goto('/training')}>
\t\t\t\t\t{t('Next Task')}
\t\t\t\t</button>
\t\t\t</div>

\t\t{/if}

\t\t{#if gamePhase === 'intro' && trialData && !loadError}
\t\t\t<button class="help-fab" on:click={() => {}}>?</button>
\t\t{/if}
\t</div>
</div>

{#if earnedBadges.length > 0}
\t<BadgeNotification badges={earnedBadges} />
{/if}

<style>
\t/* ── Page Layout ─────────────────────────────────── */
\t.cf-page {
\t\tmin-height: 100vh;
\t\tbackground: #C8DEFA;
\t\tpadding: 1.5rem;
\t}

\t.cf-wrapper {
\t\tmax-width: 960px;
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
\t\tcolor: #0891b2;
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
\t\tbackground: linear-gradient(135deg, #0e7490 0%, #06b6d4 100%);
\t\tcolor: white;
\t\tpadding: 0.4rem 0.9rem;
\t\tborder-radius: 2rem;
\t\tfont-size: 0.813rem;
\t\tfont-weight: 600;
\t\tmargin-bottom: 1rem;
\t}

\t.badge-icon { font-size: 0.813rem; font-weight: 700; letter-spacing: 0.04em; }

\t.concept-desc { color: #4b5563; font-size: 0.938rem; line-height: 1.6; margin: 0; }

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

\t/* ── Section Title ────────────────────────────────── */
\t.section-title {
\t\tfont-size: 1.125rem;
\t\tfont-weight: 600;
\t\tcolor: #1a1a2e;
\t\tmargin: 0 0 1.25rem 0;
\t}

\t/* ── Rules List ───────────────────────────────────── */
\t.rules-list { display: flex; flex-direction: column; gap: 0.75rem; }

\t.rule-item {
\t\tdisplay: flex;
\t\talign-items: flex-start;
\t\tgap: 0.875rem;
\t\tbackground: #ecfeff;
\t\tborder-radius: 10px;
\t\tpadding: 0.875rem 1rem;
\t}

\t.rule-num {
\t\tmin-width: 2rem;
\t\theight: 2rem;
\t\tbackground: linear-gradient(135deg, #0e7490 0%, #06b6d4 100%);
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

\t/* ── Category Highlight ───────────────────────────── */
\t.category-highlight {
\t\tbackground: linear-gradient(135deg, #cffafe 0%, #a5f3fc 100%);
\t\tborder-radius: 12px;
\t\tpadding: 1.25rem;
\t}

\t.category-name {
\t\tfont-size: 2rem;
\t\tfont-weight: 800;
\t\tcolor: #0e7490;
\t\tmargin-bottom: 0.5rem;
\t\tline-height: 1.1;
\t}

\t.category-examples { font-size: 0.875rem; color: #155e75; }
\t.examples-label { font-weight: 600; margin-right: 0.25rem; }

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

\t/* ── Tip Card ─────────────────────────────────────── */
\t.tip-card {
\t\tbackground: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
\t\tborder: 2px solid #f59e0b;
\t\tborder-radius: 16px;
\t\tpadding: 1.25rem 1.5rem;
\t\tdisplay: flex;
\t\talign-items: flex-start;
\t\tgap: 1rem;
\t\tmargin-bottom: 1rem;
\t}

\t.tip-icon {
\t\tbackground: #d97706;
\t\tcolor: white;
\t\tpadding: 0.25rem 0.6rem;
\t\tborder-radius: 0.5rem;
\t\tfont-size: 0.75rem;
\t\tfont-weight: 700;
\t\twhite-space: nowrap;
\t\tflex-shrink: 0;
\t\tmargin-top: 0.125rem;
\t}

\t.tip-title { font-weight: 700; color: #92400e; font-size: 0.938rem; margin-bottom: 0.25rem; }
\t.tip-text  { font-size: 0.875rem; color: #92400e; margin: 0; line-height: 1.5; }

\t/* ── Performance Guide ────────────────────────────── */
\t.perf-subtitle { font-size: 0.813rem; color: #6b7280; margin: -0.5rem 0 1rem 0; }

\t.norm-bars { display: flex; flex-direction: column; gap: 0.75rem; }

\t.norm-bar {
\t\tdisplay: grid;
\t\tgrid-template-columns: 7rem 1fr 4rem;
\t\talign-items: center;
\t\tgap: 0.75rem;
\t}

\t.norm-label { font-size: 0.875rem; font-weight: 500; color: #374151; }
\t.norm-track { height: 0.5rem; background: #f3f4f6; border-radius: 0.25rem; overflow: hidden; }
\t.norm-fill  { height: 100%; border-radius: 0.25rem; }
\t.norm-excellent { width: 90%; background: #16a34a; }
\t.norm-normal    { width: 65%; background: #f59e0b; }
\t.norm-impaired  { width: 35%; background: #dc2626; }
\t.norm-range { font-size: 0.75rem; color: #6b7280; text-align: right; }

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

\t.category-display-row {
\t\tdisplay: flex;
\t\talign-items: center;
\t\tgap: 1.25rem;
\t}

\t.category-display {
\t\tfont-size: 2.5rem;
\t\tfont-weight: 900;
\t\tcolor: #0891b2;
\t\tline-height: 1;
\t\ttext-shadow: 0 2px 8px rgba(8, 145, 178, 0.2);
\t}

\t.status-pills { display: flex; flex-direction: column; gap: 0.4rem; }

\t.pill {
\t\tpadding: 0.3rem 0.75rem;
\t\tborder-radius: 2rem;
\t\tfont-size: 0.8rem;
\t\tfont-weight: 500;
\t}

\t.pill-cf       { background: #cffafe; color: #155e75; }
\t.pill-progress { background: #f0fdf4; color: #166534; }

\t/* ── Timer ────────────────────────────────────────── */
\t.timer-display {
\t\tbackground: linear-gradient(135deg, #0e7490 0%, #06b6d4 100%);
\t\tcolor: white;
\t\tpadding: 0.5rem 1.5rem;
\t\tborder-radius: 2rem;
\t\tfont-size: 1.5rem;
\t\tfont-weight: 700;
\t\tmin-width: 5rem;
\t\ttext-align: center;
\t\ttransition: background 0.3s;
\t}

\t.timer-urgent {
\t\tbackground: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
\t\tanimation: timer-pulse 0.5s ease-in-out infinite;
\t}

\t/* ── Input Card ───────────────────────────────────── */
\t.input-card {
\t\tbackground: #ecfeff;
\t\tborder: 2px solid #a5f3fc;
\t\tborder-radius: 12px;
\t\tpadding: 1.25rem;
\t\tmargin-bottom: 1.25rem;
\t}

\t.input-label {
\t\tdisplay: block;
\t\tcolor: #0e7490;
\t\tfont-weight: 600;
\t\tfont-size: 0.875rem;
\t\tmargin-bottom: 0.625rem;
\t}

\t.input-row {
\t\tdisplay: flex;
\t\tgap: 0.75rem;
\t\talign-items: center;
\t\tmargin-bottom: 0.5rem;
\t}

\t.word-input {
\t\tflex: 1;
\t\tpadding: 0.875rem 1rem;
\t\tfont-size: 1.125rem;
\t\tborder: 2px solid #a5f3fc;
\t\tborder-radius: 10px;
\t\toutline: none;
\t\tbackground: white;
\t\tcolor: #1a1a2e;
\t\ttransition: border-color 0.15s;
\t}

\t.word-input:focus {
\t\tborder-color: #0891b2;
\t\tbox-shadow: 0 0 0 3px rgba(8, 145, 178, 0.12);
\t}

\t.submit-btn {
\t\tbackground: linear-gradient(135deg, #0e7490 0%, #06b6d4 100%);
\t\tcolor: white;
\t\tborder: none;
\t\tborder-radius: 10px;
\t\tpadding: 0.875rem 1.5rem;
\t\tfont-size: 1rem;
\t\tfont-weight: 600;
\t\tcursor: pointer;
\t\twhite-space: nowrap;
\t\ttransition: opacity 0.15s;
\t}

\t.submit-btn:hover:not(:disabled) { opacity: 0.9; }
\t.submit-btn:disabled { opacity: 0.45; cursor: not-allowed; }

\t.input-tip { font-size: 0.8rem; color: #0891b2; margin: 0; }

\t/* ── Words Section ────────────────────────────────── */
\t.words-section { margin-bottom: 1.25rem; }

\t.words-heading {
\t\tfont-size: 0.938rem;
\t\tfont-weight: 600;
\t\tcolor: #0e7490;
\t\tmargin: 0 0 0.75rem 0;
\t}

\t.words-area {
\t\tdisplay: flex;
\t\tflex-wrap: wrap;
\t\tgap: 0.5rem;
\t\tmin-height: 52px;
\t\tpadding: 0.875rem;
\t\tborder-radius: 10px;
\t\tbackground: #f0fdfe;
\t\tborder: 2px dashed #a5f3fc;
\t}

\t.words-empty { color: #9ca3af; font-style: italic; font-size: 0.875rem; align-self: center; }

\t/* ── Word Chips ───────────────────────────────────── */
\t.word-chip {
\t\tbackground: linear-gradient(135deg, #cffafe 0%, #a5f3fc 100%);
\t\tcolor: #0e7490;
\t\tpadding: 0.35rem 0.4rem 0.35rem 0.875rem;
\t\tborder-radius: 6px;
\t\tfont-size: 0.875rem;
\t\tfont-weight: 600;
\t\tdisplay: inline-flex;
\t\talign-items: center;
\t\tgap: 0.35rem;
\t}

\t.chip-remove {
\t\tbackground: #0e7490;
\t\tcolor: white;
\t\tborder: none;
\t\tborder-radius: 50%;
\t\twidth: 1.25rem;
\t\theight: 1.25rem;
\t\tdisplay: flex;
\t\talign-items: center;
\t\tjustify-content: center;
\t\tfont-size: 0.85rem;
\t\tline-height: 1;
\t\tcursor: pointer;
\t\tpadding: 0;
\t\tflex-shrink: 0;
\t}

\t.chip-remove:hover { background: #155e75; }

\t.word-result  { background: #cffafe; color: #155e75; border: 1px solid #a5f3fc; border-radius: 6px; padding: 0.35rem 0.875rem; font-size: 0.875rem; font-weight: 600; }
\t.word-invalid { background: #fee2e2; color: #991b1b; padding: 0.35rem 0.875rem; border-radius: 6px; font-size: 0.875rem; font-weight: 600; }

\t/* ── Skip Row ─────────────────────────────────────── */
\t.skip-row { display: flex; justify-content: flex-end; margin-top: 0.5rem; }

\t/* ── Results Header ───────────────────────────────── */
\t.results-header {
\t\tbackground: linear-gradient(135deg, #0e7490 0%, #06b6d4 100%);
\t\tborder-radius: 16px;
\t\tpadding: 1.75rem;
\t\ttext-align: center;
\t\tmargin-bottom: 1rem;
\t\tbox-shadow: 0 4px 12px rgba(14, 116, 144, 0.35);
\t}

\t.score-pill {
\t\tdisplay: flex;
\t\talign-items: baseline;
\t\tjustify-content: center;
\t\tgap: 0.5rem;
\t\tmargin-bottom: 0.5rem;
\t}

\t.score-label { color: rgba(255, 255, 255, 0.85); font-size: 1rem; font-weight: 500; }
\t.score-value { color: white; font-size: 3rem; font-weight: 700; }
\t.score-max   { color: rgba(255, 255, 255, 0.7); font-size: 1.5rem; font-weight: 500; }

\t.results-subtitle { color: rgba(255, 255, 255, 0.9); font-size: 0.938rem; margin: 0; }

\t/* ── Metrics Grid ─────────────────────────────────── */
\t.metrics-grid {
\t\tdisplay: grid;
\t\tgrid-template-columns: repeat(3, 1fr);
\t\tgap: 1rem;
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

\t.metric-teal    { border-top-color: #0891b2; }
\t.metric-amber   { border-top-color: #d97706; }
\t.metric-excellent { border-top-color: #16a34a; }
\t.metric-good      { border-top-color: #f59e0b; }
\t.metric-below     { border-top-color: #dc2626; }

\t.metric-value { font-size: 1.75rem; font-weight: 700; color: #1a1a2e; }
\t.metric-label { font-size: 0.75rem; color: #6b7280; margin-top: 0.25rem; }

\t/* ── Feedback ─────────────────────────────────────── */
\t.feedback-text { font-size: 0.938rem; color: #374151; line-height: 1.6; margin: 0 0 1rem 0; }

\t/* ── Words Result ─────────────────────────────────── */
\t.words-result-section { margin-top: 1.25rem; }

\t.words-result-heading {
\t\tfont-size: 0.875rem;
\t\tfont-weight: 600;
\t\tmargin: 0 0 0.625rem 0;
\t}

\t.words-valid-heading   { color: #0e7490; }
\t.words-invalid-heading { color: #991b1b; }

\t.words-result-area {
\t\tdisplay: flex;
\t\tflex-wrap: wrap;
\t\tgap: 0.4rem;
\t}

\t.words-invalid-area .word-invalid { display: inline-block; }

\t.dupe-note { font-size: 0.8rem; color: #9ca3af; margin: 0.75rem 0 0 0; }

\t/* ── Level Up Card ────────────────────────────────── */
\t.levelup-card {
\t\tbackground: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
\t\tborder: 2px solid #86efac;
\t\tborder-radius: 16px;
\t\tpadding: 1.25rem 1.5rem;
\t\tmargin-bottom: 1rem;
\t\tdisplay: flex;
\t\talign-items: center;
\t\tgap: 1rem;
\t}

\t.levelup-badge {
\t\tbackground: #16a34a;
\t\tcolor: white;
\t\tpadding: 0.2rem 0.75rem;
\t\tborder-radius: 1rem;
\t\tfont-size: 0.75rem;
\t\tfont-weight: 600;
\t\twhite-space: nowrap;
\t}

\t.levelup-card p { font-size: 0.875rem; color: #166534; margin: 0; }

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

\t.btn-secondary:not(.skip-row .btn-secondary) { flex: 1; }
\t.btn-secondary:hover { background: #f5f3ff; transform: translateY(-2px); }

\t/* ── Help FAB ─────────────────────────────────────── */
\t.help-fab {
\t\tposition: fixed;
\t\tbottom: 2rem;
\t\tright: 2rem;
\t\twidth: 3rem;
\t\theight: 3rem;
\t\tbackground: linear-gradient(135deg, #0e7490 0%, #06b6d4 100%);
\t\tcolor: white;
\t\tborder: none;
\t\tborder-radius: 50%;
\t\tfont-size: 1.25rem;
\t\tfont-weight: 700;
\t\tcursor: pointer;
\t\tbox-shadow: 0 4px 12px rgba(14, 116, 144, 0.4);
\t\tdisplay: flex;
\t\talign-items: center;
\t\tjustify-content: center;
\t}

\t/* ── Animations ───────────────────────────────────── */
\t@keyframes timer-pulse {
\t\t0%, 100% { transform: scale(1); }
\t\t50%       { transform: scale(1.08); }
\t}

\t/* ── Responsive ───────────────────────────────────── */
\t@media (max-width: 640px) {
\t\t.info-grid      { grid-template-columns: 1fr; }
\t\t.metrics-grid   { grid-template-columns: 1fr; }
\t\t.action-buttons { flex-direction: column; }
\t\t.game-status-bar { flex-direction: column; align-items: flex-start; }
\t\t.category-display { font-size: 2rem; }
\t}
</style>
"""

with open(
    r'd:\NeuroBloom\frontend-svelte\src\routes\training\category-fluency\+page.svelte',
    'w',
    encoding='utf-8'
) as f:
    f.write(CONTENT)

lines = CONTENT.count('\n') + 1
print(f'Done. Lines: {lines}')

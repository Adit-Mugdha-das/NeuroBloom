#!/usr/bin/env python3
"""Redesign Twenty Questions UI to LNS design system (violet #6d28d9)."""

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

\tlet gamePhase = 'loading';
\tlet gameData = null;
\tlet targetObject = null;
\tlet targetAttributes = {};
\tlet taskId = null;

\tlet questionInput = '';
\tlet questionsAsked = 0;
\tlet questionsHistory = [];
\tlet guessInput = '';

\tlet results = null;
\tlet earnedBadges = [];
\t/** @type {string} */
\tlet playMode = TASK_PLAY_MODE.RECORDED;
\tlet practiceStatusMessage = '';

\tlet loadError = false;
\tlet askError = false;
\tlet saveError = false;
\tlet showGiveUpConfirm = false;

\tfunction lt(en, bn) {
\t\treturn localeText({ en, bn }, $locale);
\t}

\tfunction answerClass(answer) {
\t\tconst a = (answer || '').toLowerCase();
\t\tif (a === 'yes') return 'answer-yes';
\t\tif (a === 'no') return 'answer-no';
\t\treturn 'answer-partial';
\t}

\tfunction counterClass() {
\t\tif (questionsAsked >= 18) return 'counter-danger';
\t\tif (questionsAsked >= 14) return 'counter-warn';
\t\treturn 'counter-safe';
\t}

\tfunction performanceLabel(rating) {
\t\tconst map = {
\t\t\texcellent: lt('Excellent', 'অসাধারণ'),
\t\t\tgood: lt('Good', 'ভালো'),
\t\t\taverage: lt('Average', 'মোটামুটি'),
\t\t\tbelow_average: lt('Below Average', 'নিচের গড়'),
\t\t\tincorrect: lt('Incorrect', 'ভুল')
\t\t};
\t\treturn map[rating] || rating;
\t}

\tonMount(async () => {
\t\tif (!$user) {
\t\t\tgoto('/login');
\t\t\treturn;
\t\t}
\t\tawait loadGame();
\t});

\tasync function loadGame() {
\t\ttry {
\t\t\tloadError = false;
\t\t\tconst response = await fetch(
\t\t\t\t`${API_BASE_URL}/api/training/tasks/twenty-questions/generate/${$user.id}`,
\t\t\t\t{
\t\t\t\t\tmethod: 'POST',
\t\t\t\t\theaders: { 'Content-Type': 'application/json' },
\t\t\t\t\tcredentials: 'include'
\t\t\t\t}
\t\t\t);
\t\t\tif (!response.ok) throw new Error('Failed to load game');
\t\t\tconst data = await response.json();
\t\t\tgameData = data.game_data;
\t\t\ttargetObject = gameData.target_object_name;
\t\t\ttargetAttributes = gameData.target_attributes;
\t\t\tgamePhase = 'intro';
\t\t} catch (_) {
\t\t\tloadError = true;
\t\t\tgamePhase = 'intro';
\t\t}
\t}

\t/** @param {string} nextMode */
\tfunction startGame(nextMode = TASK_PLAY_MODE.RECORDED) {
\t\tplayMode = nextMode;
\t\tpracticeStatusMessage = '';
\t\tquestionsAsked = 0;
\t\tquestionsHistory = [];
\t\tquestionInput = '';
\t\tguessInput = '';
\t\tshowGiveUpConfirm = false;
\t\taskError = false;
\t\tgamePhase = 'playing';
\t\tsetTimeout(() => {
\t\t\tdocument.getElementById('question-input')?.focus();
\t\t}, 100);
\t}

\tasync function askQuestion() {
\t\tif (!questionInput.trim()) return;
\t\tconst question = questionInput.trim();
\t\taskError = false;
\t\ttry {
\t\t\tconst response = await fetch(
\t\t\t\t`${API_BASE_URL}/api/training/tasks/twenty-questions/ask/${$user.id}`,
\t\t\t\t{
\t\t\t\t\tmethod: 'POST',
\t\t\t\t\theaders: { 'Content-Type': 'application/json' },
\t\t\t\t\tcredentials: 'include',
\t\t\t\t\tbody: JSON.stringify({
\t\t\t\t\t\tquestion,
\t\t\t\t\t\ttarget_attributes: targetAttributes,
\t\t\t\t\t\ttarget_object_name: targetObject
\t\t\t\t\t})
\t\t\t\t}
\t\t\t);
\t\t\tif (!response.ok) throw new Error('Failed to ask question');
\t\t\tconst data = await response.json();
\t\t\tquestionsHistory = [
\t\t\t\t...questionsHistory,
\t\t\t\t{ question, answer: data.answer, confidence: data.confidence }
\t\t\t];
\t\t\tquestionsAsked++;
\t\t\tquestionInput = '';
\t\t\tsetTimeout(() => {
\t\t\t\tdocument.getElementById('question-input')?.focus();
\t\t\t}, 0);
\t\t\tsetTimeout(() => {
\t\t\t\tconst el = document.getElementById('questions-history');
\t\t\t\tif (el) el.scrollTop = el.scrollHeight;
\t\t\t}, 100);
\t\t} catch (_) {
\t\t\taskError = true;
\t\t}
\t}

\tfunction handleQuestionKeyPress(event) {
\t\tif (event.key === 'Enter') {
\t\t\tevent.preventDefault();
\t\t\taskQuestion();
\t\t}
\t}

\tasync function submitGuess() {
\t\tif (!guessInput.trim()) return;
\t\tconst guess = guessInput.trim();
\t\tawait endGame(guess.toLowerCase() === targetObject.toLowerCase(), guess);
\t}

\tasync function endGame(correctlyIdentified, userGuess) {
\t\tif (playMode === TASK_PLAY_MODE.PRACTICE) {
\t\t\tplayMode = TASK_PLAY_MODE.RECORDED;
\t\t\tpracticeStatusMessage = getPracticeCopy($locale).complete;
\t\t\tresults = null;
\t\t\tearnedBadges = [];
\t\t\tgamePhase = 'loading';
\t\t\tawait loadGame();
\t\t\treturn;
\t\t}
\t\tsaveError = false;
\t\ttry {
\t\t\ttaskId = $page.url.searchParams.get('taskId');
\t\t\tconst response = await fetch(
\t\t\t\t`${API_BASE_URL}/api/training/tasks/twenty-questions/submit/${$user.id}`,
\t\t\t\t{
\t\t\t\t\tmethod: 'POST',
\t\t\t\t\theaders: { 'Content-Type': 'application/json' },
\t\t\t\t\tcredentials: 'include',
\t\t\t\t\tbody: JSON.stringify({
\t\t\t\t\t\tquestions_asked: questionsAsked,
\t\t\t\t\t\tcorrectly_identified: correctlyIdentified,
\t\t\t\t\t\tdifficulty: gameData.difficulty,
\t\t\t\t\t\tquestions_history: questionsHistory,
\t\t\t\t\t\ttarget_object_name: targetObject,
\t\t\t\t\t\tuser_guess: userGuess,
\t\t\t\t\t\ttask_id: taskId
\t\t\t\t\t})
\t\t\t\t}
\t\t\t);
\t\t\tif (!response.ok) throw new Error('Failed to submit game');
\t\t\tconst data = await response.json();
\t\t\tresults = {
\t\t\t\tnormalized_score: data.score,
\t\t\t\tperformance_rating: data.performance_rating,
\t\t\t\tquestions_asked: data.questions_asked,
\t\t\t\tcorrectly_identified: data.correctly_identified,
\t\t\t\tquestion_efficiency: data.question_efficiency,
\t\t\t\tstrategy_score: data.strategy_score,
\t\t\t\tconstraint_seeking_questions: data.constraint_seeking_questions,
\t\t\t\tspecific_guesses: data.specific_guesses,
\t\t\t\tfeedback: data.feedback,
\t\t\t\ttips: data.tips,
\t\t\t\tshould_advance: data.new_difficulty > data.old_difficulty
\t\t\t};
\t\t\tif (data.new_badges?.length > 0) earnedBadges = data.new_badges;
\t\t\tuser.update((u) => ({ ...u, planning_difficulty: data.new_difficulty }));
\t\t\tgamePhase = 'results';
\t\t} catch (_) {
\t\t\tsaveError = true;
\t\t\tgamePhase = 'results';
\t\t}
\t}
</script>

<div class="tq-page" data-localize-skip>
\t<div class="tq-wrapper">

\t\t{#if gamePhase === 'loading'}
\t\t\t<LoadingSkeleton />

\t\t{:else if gamePhase === 'intro'}

\t\t\t<!-- Header Card -->
\t\t\t<div class="header-card">
\t\t\t\t<div class="header-content">
\t\t\t\t\t<div class="header-text">
\t\t\t\t\t\t<h1 class="task-title">{lt('Twenty Questions', 'টুয়েন্টি কোয়েশ্চেন্স')}</h1>
\t\t\t\t\t\t<p class="task-domain">{lt('Strategic Problem-Solving · Planning / Executive Function', 'কৌশলগত সমস্যা সমাধান · পরিকল্পনা / কার্যনির্বাহী কার্যক্ষমতা')}</p>
\t\t\t\t\t</div>
\t\t\t\t\t<DifficultyBadge difficulty={gameData?.difficulty || 1} domain="Executive Planning" />
\t\t\t\t</div>
\t\t\t</div>

\t\t\t{#if playMode === TASK_PLAY_MODE.PRACTICE}
\t\t\t\t<PracticeModeBanner locale={$locale} />
\t\t\t{/if}

\t\t\t{#if loadError}
\t\t\t\t<div class="error-card">
\t\t\t\t\t<p>{lt('Failed to load task. Please try again.', 'টাস্ক লোড করতে ব্যর্থ। আবার চেষ্টা করুন।')}</p>
\t\t\t\t\t<button class="start-button" on:click={loadGame}>
\t\t\t\t\t\t{lt('Retry', 'আবার চেষ্টা করুন')}
\t\t\t\t\t</button>
\t\t\t\t</div>
\t\t\t{:else if gameData}

\t\t\t\t<!-- Task Concept -->
\t\t\t\t<div class="card task-concept">
\t\t\t\t\t<div class="concept-badge">
\t\t\t\t\t\t<span class="badge-icon">{lt('Strategy', 'কৌশল')}</span>
\t\t\t\t\t\t<span>{lt('Executive Planning', 'কার্যনির্বাহী পরিকল্পনা')}</span>
\t\t\t\t\t</div>
\t\t\t\t\t<p class="concept-desc">
\t\t\t\t\t\t{gameData.instructions}
\t\t\t\t\t</p>
\t\t\t\t</div>

\t\t\t\t<!-- Rules Card -->
\t\t\t\t<div class="card">
\t\t\t\t\t<h2 class="section-title">{lt('Rules', 'নিয়মাবলী')}</h2>
\t\t\t\t\t<div class="rules-list">
\t\t\t\t\t\t<div class="rule-item">
\t\t\t\t\t\t\t<div class="rule-num">1</div>
\t\t\t\t\t\t\t<div class="rule-text">{lt('Type a yes/no question and press Enter to submit it', 'একটি হ্যাঁ/না প্রশ্ন টাইপ করুন এবং এন্টার চাপুন')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="rule-item">
\t\t\t\t\t\t\t<div class="rule-num">2</div>
\t\t\t\t\t\t\t<div class="rule-text">{lt('Use broad constraint-seeking questions first — e.g., "Is it living?" not "Is it a dog?"', 'প্রথমে বিস্তৃত সীমানির্ধারণকারী প্রশ্ন করুন — যেমন "এটি কি জীবিত?" না "এটি কি কুকুর?"')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="rule-item">
\t\t\t\t\t\t\t<div class="rule-num">3</div>
\t\t\t\t\t\t\t<div class="rule-text">{lt('When confident, submit your final guess in the guess box below', 'আত্মবিশ্বাসী হলে, নিচের অনুমান বাক্সে আপনার চূড়ান্ত উত্তর দিন')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="rule-item">
\t\t\t\t\t\t\t<div class="rule-num">4</div>
\t\t\t\t\t\t\t<div class="rule-text">{lt('Fewer questions used = higher score. You have 20 questions maximum', 'কম প্রশ্ন = বেশি স্কোর। সর্বাধিক ২০টি প্রশ্ন')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Info Grid -->
\t\t\t\t<div class="info-grid">
\t\t\t\t\t<!-- Category Hint -->
\t\t\t\t\t<div class="card">
\t\t\t\t\t\t<h3 class="card-title">{lt('Category Hint', 'বিভাগ ইঙ্গিত')}</h3>
\t\t\t\t\t\t<div class="hint-box">
\t\t\t\t\t\t\t<div class="hint-label">{lt('I am thinking of a...', 'আমি ভাবছি একটি...')}</div>
\t\t\t\t\t\t\t<div class="hint-value">{gameData.hint}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t\t<!-- What It Measures -->
\t\t\t\t\t<div class="card">
\t\t\t\t\t\t<h3 class="card-title">{lt('What It Measures', 'এটি কী পরিমাপ করে')}</h3>
\t\t\t\t\t\t<div class="details-list">
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{lt('Primary Metric', 'প্রাথমিক পরিমাপ')}</span>
\t\t\t\t\t\t\t\t<strong>{lt('Questions to identify', 'সনাক্তকরণে প্রশ্ন')}</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{lt('Cognitive Domain', 'জ্ঞানীয় ক্ষেত্র')}</span>
\t\t\t\t\t\t\t\t<strong>{lt('Strategic planning', 'কৌশলগত পরিকল্পনা')}</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{lt('Max Questions', 'সর্বাধিক প্রশ্ন')}</span>
\t\t\t\t\t\t\t\t<strong>20</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{lt('Difficulty', 'কঠিনতা')}</span>
\t\t\t\t\t\t\t\t<strong>{lt(`Level ${gameData.difficulty} / 10`, `স্তর ${gameData.difficulty} / ১০`)}</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Strategy Tip -->
\t\t\t\t<div class="tip-card">
\t\t\t\t\t<div class="tip-icon">TIP</div>
\t\t\t\t\t<div class="tip-body">
\t\t\t\t\t\t<div class="tip-title">{lt('Constraint-Seeking Strategy', 'সীমানির্ধারণকারী কৌশল')}</div>
\t\t\t\t\t\t<p class="tip-text">
\t\t\t\t\t\t\t{lt(
\t\t\t\t\t\t\t\t'Start with questions that eliminate half the possibilities: "Is it alive?", "Is it man-made?", "Can you hold it?". Broad questions give far more information than specific guesses.',
\t\t\t\t\t\t\t\t'এমন প্রশ্ন দিয়ে শুরু করুন যা অর্ধেক সম্ভাবনা বাদ দেয়: "এটি কি জীবিত?", "এটি কি মানুষের তৈরি?", "এটি কি ধরা যায়?"'
\t\t\t\t\t\t\t)}
\t\t\t\t\t\t</p>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Clinical Basis -->
\t\t\t\t<div class="clinical-info">
\t\t\t\t\t<div class="clinical-header">
\t\t\t\t\t\t<div class="clinical-badge">{lt('Clinical Basis', 'ক্লিনিকাল ভিত্তি')}</div>
\t\t\t\t\t\t<h3>{lt('Validated MS Strategic Reasoning Assessment', 'MS-এর জন্য যাচাইকৃত কৌশলগত যুক্তি মূল্যায়ন')}</h3>
\t\t\t\t\t</div>
\t\t\t\t\t<p>
\t\t\t\t\t\t{lt(
\t\t\t\t\t\t\t'The Twenty Questions Task (Mosher & Hornsby, 1966) assesses hypothesis-testing strategy and executive planning. In MS, deficits in constraint-seeking behaviour reflect impaired prefrontal-mediated top-down control and reduced cognitive flexibility. Inefficient questioning strategies predict everyday problem-solving difficulties and are sensitive to cognitive load imposed by MS-related fatigue.',
\t\t\t\t\t\t\t'টুয়েন্টি কোয়েশ্চেন্স টাস্ক (Mosher & Hornsby, 1966) হাইপোথিসিস-পরীক্ষা কৌশল এবং কার্যনির্বাহী পরিকল্পনা মূল্যায়ন করে। MS-এ সীমানির্ধারণকারী আচরণে ঘাটতি প্রিফ্রন্টাল-মধ্যস্থ টপ-ডাউন নিয়ন্ত্রণ দুর্বলতা প্রতিফলিত করে।'
\t\t\t\t\t\t)}
\t\t\t\t\t</p>
\t\t\t\t</div>

\t\t\t\t<TaskPracticeActions
\t\t\t\t\tlocale={$locale}
\t\t\t\t\tstartLabel={lt('Start Game', 'গেম শুরু করুন')}
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

\t\t\t\t<!-- Status Bar -->
\t\t\t\t<div class="game-status-bar">
\t\t\t\t\t<div class="game-title-row">
\t\t\t\t\t\t<div class="thinking-label">{lt("I'm thinking of something...", 'আমি কিছু একটা ভাবছি...')}</div>
\t\t\t\t\t\t<div class="category-tag">{gameData?.category}</div>
\t\t\t\t\t</div>
\t\t\t\t\t<div class="question-counter {counterClass()}">
\t\t\t\t\t\t{lt(`${questionsAsked} / 20`, `${questionsAsked} / ২০`)}
\t\t\t\t\t\t<span class="counter-label">{lt('questions', 'প্রশ্ন')}</span>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Question History -->
\t\t\t\t<div class="history-section">
\t\t\t\t\t<h3 class="history-heading">{lt('Question History', 'প্রশ্নের ইতিহাস')}</h3>
\t\t\t\t\t<div class="history-list" id="questions-history">
\t\t\t\t\t\t{#if questionsHistory.length === 0}
\t\t\t\t\t\t\t<p class="history-empty">{lt('No questions asked yet — start asking!', 'এখনো কোনো প্রশ্ন করা হয়নি — শুরু করুন!')}</p>
\t\t\t\t\t\t{:else}
\t\t\t\t\t\t\t{#each questionsHistory as item, index}
\t\t\t\t\t\t\t\t<div class="history-item">
\t\t\t\t\t\t\t\t\t<div class="history-q">
\t\t\t\t\t\t\t\t\t\t<span class="q-num">Q{index + 1}</span>
\t\t\t\t\t\t\t\t\t\t<span class="q-text">{item.question}</span>
\t\t\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t\t\t<div class="history-answer-row">
\t\t\t\t\t\t\t\t\t\t<span class="answer-badge {answerClass(item.answer)}">{item.answer}</span>
\t\t\t\t\t\t\t\t\t\t{#if item.confidence === 'high'}
\t\t\t\t\t\t\t\t\t\t\t<span class="confidence-label">{lt('Confident', 'আত্মবিশ্বাসী')}</span>
\t\t\t\t\t\t\t\t\t\t{/if}
\t\t\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t{/each}
\t\t\t\t\t\t{/if}
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t{#if askError}
\t\t\t\t\t<div class="warn-card">
\t\t\t\t\t\t{lt('Error processing question. Please try again.', 'প্রশ্ন প্রক্রিয়া করতে ত্রুটি। আবার চেষ্টা করুন।')}
\t\t\t\t\t</div>
\t\t\t\t{/if}

\t\t\t\t<!-- Question Input -->
\t\t\t\t{#if questionsAsked < 20}
\t\t\t\t\t<div class="input-card">
\t\t\t\t\t\t<label for="question-input" class="input-label">
\t\t\t\t\t\t\t{lt('Ask a yes/no question:', 'একটি হ্যাঁ/না প্রশ্ন করুন:')}
\t\t\t\t\t\t</label>
\t\t\t\t\t\t<div class="input-row">
\t\t\t\t\t\t\t<input
\t\t\t\t\t\t\t\tid="question-input"
\t\t\t\t\t\t\t\ttype="text"
\t\t\t\t\t\t\t\tbind:value={questionInput}
\t\t\t\t\t\t\t\ton:keypress={handleQuestionKeyPress}
\t\t\t\t\t\t\t\tplaceholder={lt('e.g., Is it an animal?', 'যেমন: এটি কি প্রাণী?')}
\t\t\t\t\t\t\t\tclass="question-input"
\t\t\t\t\t\t\t/>
\t\t\t\t\t\t\t<button
\t\t\t\t\t\t\t\tclass="ask-btn"
\t\t\t\t\t\t\t\ton:click={askQuestion}
\t\t\t\t\t\t\t\tdisabled={!questionInput.trim()}
\t\t\t\t\t\t\t>
\t\t\t\t\t\t\t\t{lt('Ask', 'প্রশ্ন করুন')}
\t\t\t\t\t\t\t</button>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<p class="input-tip">{lt('Tip: Press Enter to submit', 'টিপ: এন্টার চাপলে সাবমিট হবে')}</p>
\t\t\t\t\t</div>
\t\t\t\t{:else}
\t\t\t\t\t<div class="warn-card">
\t\t\t\t\t\t{lt('You have used all 20 questions. Time to make your final guess!', 'আপনি ২০টি প্রশ্ন ব্যবহার করেছেন। এখন আপনার চূড়ান্ত অনুমান করুন!')}
\t\t\t\t\t</div>
\t\t\t\t{/if}

\t\t\t\t<!-- Guess Section -->
\t\t\t\t<div class="guess-card">
\t\t\t\t\t<h3 class="guess-heading">{lt('Ready to guess?', 'অনুমান করতে প্রস্তুত?')}</h3>
\t\t\t\t\t<label for="guess-input" class="input-label">
\t\t\t\t\t\t{lt('What is it?', 'এটি কী?')}
\t\t\t\t\t</label>
\t\t\t\t\t<div class="input-row">
\t\t\t\t\t\t<input
\t\t\t\t\t\t\tid="guess-input"
\t\t\t\t\t\t\ttype="text"
\t\t\t\t\t\t\tbind:value={guessInput}
\t\t\t\t\t\t\tplaceholder={lt('Enter your final guess...', 'আপনার চূড়ান্ত অনুমান লিখুন...')}
\t\t\t\t\t\t\tclass="guess-input"
\t\t\t\t\t\t/>
\t\t\t\t\t\t<button
\t\t\t\t\t\t\tclass="guess-btn"
\t\t\t\t\t\t\ton:click={submitGuess}
\t\t\t\t\t\t\tdisabled={!guessInput.trim()}
\t\t\t\t\t\t>
\t\t\t\t\t\t\t{lt('Submit Guess', 'অনুমান দিন')}
\t\t\t\t\t\t</button>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Give Up -->
\t\t\t\t{#if !showGiveUpConfirm}
\t\t\t\t\t<div class="skip-row">
\t\t\t\t\t\t<button class="btn-secondary" on:click={() => (showGiveUpConfirm = true)}>
\t\t\t\t\t\t\t{lt('Give Up', 'হাল ছেড়ে দিন')}
\t\t\t\t\t\t</button>
\t\t\t\t\t</div>
\t\t\t\t{:else}
\t\t\t\t\t<div class="confirm-card">
\t\t\t\t\t\t<p class="confirm-text">{lt('Are you sure you want to give up?', 'আপনি কি সত্যিই হাল ছেড়ে দিতে চান?')}</p>
\t\t\t\t\t\t<div class="confirm-buttons">
\t\t\t\t\t\t\t<button class="confirm-yes" on:click={() => endGame(false, 'Gave up')}>
\t\t\t\t\t\t\t\t{lt('Yes, give up', 'হ্যাঁ, ছেড়ে দিন')}
\t\t\t\t\t\t\t</button>
\t\t\t\t\t\t\t<button class="confirm-no" on:click={() => (showGiveUpConfirm = false)}>
\t\t\t\t\t\t\t\t{lt('No, keep going', 'না, চালিয়ে যাই')}
\t\t\t\t\t\t\t</button>
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t{/if}
\t\t\t</div>

\t\t{:else if gamePhase === 'results'}

\t\t\t<!-- Results Header -->
\t\t\t<div class="results-header">
\t\t\t\t<div class="score-pill">
\t\t\t\t\t<span class="score-label">{lt('Score', 'স্কোর')}</span>
\t\t\t\t\t<span class="score-value">{results ? results.normalized_score : '—'}</span>
\t\t\t\t\t<span class="score-max">/100</span>
\t\t\t\t</div>
\t\t\t\t<p class="results-subtitle">
\t\t\t\t\t{lt('Twenty Questions Complete', 'টুয়েন্টি কোয়েশ্চেন্স সম্পন্ন')} ·
\t\t\t\t\t{lt('The answer was:', 'উত্তর ছিল:')}
\t\t\t\t\t<strong class="answer-reveal">{targetObject}</strong>
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
\t\t\t\t\t<div class="metric-card metric-violet">
\t\t\t\t\t\t<div class="metric-value">{results.questions_asked}</div>
\t\t\t\t\t\t<div class="metric-label">{lt('Questions Used', 'ব্যবহৃত প্রশ্ন')}</div>
\t\t\t\t\t</div>
\t\t\t\t\t<div class="metric-card {results.correctly_identified ? 'metric-correct' : 'metric-incorrect'}">
\t\t\t\t\t\t<div class="metric-value">{results.correctly_identified ? lt('Yes', 'হ্যাঁ') : lt('No', 'না')}</div>
\t\t\t\t\t\t<div class="metric-label">{lt('Correct Guess', 'সঠিক অনুমান')}</div>
\t\t\t\t\t</div>
\t\t\t\t\t<div class="metric-card metric-amber">
\t\t\t\t\t\t<div class="metric-value">{results.strategy_score ? results.strategy_score.toFixed(0) : '—'}%</div>
\t\t\t\t\t\t<div class="metric-label">{lt('Strategy Score', 'কৌশল স্কোর')}</div>
\t\t\t\t\t</div>
\t\t\t\t\t<div class="metric-card metric-blue">
\t\t\t\t\t\t<div class="metric-value">{results.question_efficiency ? results.question_efficiency.toFixed(0) : '—'}%</div>
\t\t\t\t\t\t<div class="metric-label">{lt('Question Efficiency', 'প্রশ্নের দক্ষতা')}</div>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Performance Details -->
\t\t\t\t<div class="card">
\t\t\t\t\t<h3 class="card-title">{lt('Performance Analysis', 'পারফরম্যান্স বিশ্লেষণ')}</h3>
\t\t\t\t\t<div class="details-list">
\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t<span>{lt('Rating', 'রেটিং')}</span>
\t\t\t\t\t\t\t<strong>{performanceLabel(results.performance_rating)}</strong>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t<span>{lt('Constraint-Seeking Questions', 'সীমানির্ধারণকারী প্রশ্ন')}</span>
\t\t\t\t\t\t\t<strong>{results.constraint_seeking_questions}</strong>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t<span>{lt('Specific Guesses Made', 'নির্দিষ্ট অনুমান')}</span>
\t\t\t\t\t\t\t<strong>{results.specific_guesses}</strong>
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Feedback -->
\t\t\t\t<div class="card">
\t\t\t\t\t<h3 class="card-title">{lt('Feedback', 'প্রতিক্রিয়া')}</h3>
\t\t\t\t\t<p class="feedback-text">{results.feedback}</p>

\t\t\t\t\t{#if results.tips}
\t\t\t\t\t\t<div class="tips-box">
\t\t\t\t\t\t\t<div class="tips-label">{lt('Tips for Next Time', 'পরের বারের জন্য পরামর্শ')}</div>
\t\t\t\t\t\t\t<p class="tips-text">{results.tips}</p>
\t\t\t\t\t\t</div>
\t\t\t\t\t{/if}
\t\t\t\t</div>

\t\t\t\t<!-- Level Up -->
\t\t\t\t{#if results.should_advance}
\t\t\t\t\t<div class="levelup-card">
\t\t\t\t\t\t<div class="levelup-badge">{lt('Level Up', 'লেভেল আপ')}</div>
\t\t\t\t\t\t<p>
\t\t\t\t\t\t\t{lt(
\t\t\t\t\t\t\t\t`Excellent strategy! Moving to difficulty level ${gameData.difficulty + 1}.`,
\t\t\t\t\t\t\t\t`দারুণ কৌশল! কঠিনতা স্তর ${gameData.difficulty + 1}-এ উন্নীত হচ্ছে।`
\t\t\t\t\t\t\t)}
\t\t\t\t\t\t</p>
\t\t\t\t\t</div>
\t\t\t\t{/if}
\t\t\t{/if}

\t\t\t<!-- Action Buttons -->
\t\t\t<div class="action-buttons">
\t\t\t\t<button class="start-button" on:click={() => goto('/dashboard')}>
\t\t\t\t\t{lt('Return to Dashboard', 'ড্যাশবোর্ডে ফিরুন')}
\t\t\t\t</button>
\t\t\t\t<button class="btn-secondary" on:click={() => goto('/training')}>
\t\t\t\t\t{lt('Next Task', 'পরবর্তী টাস্ক')}
\t\t\t\t</button>
\t\t\t</div>

\t\t{/if}

\t\t{#if gamePhase === 'intro' && gameData && !loadError}
\t\t\t<button class="help-fab" on:click={() => {}}>?</button>
\t\t{/if}
\t</div>
</div>

{#if earnedBadges.length > 0}
\t<BadgeNotification badges={earnedBadges} />
{/if}

<style>
\t/* ── Page Layout ─────────────────────────────────── */
\t.tq-page {
\t\tmin-height: 100vh;
\t\tbackground: #C8DEFA;
\t\tpadding: 1.5rem;
\t}

\t.tq-wrapper {
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
\t\tcolor: #6d28d9;
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
\t\tbackground: linear-gradient(135deg, #5b21b6 0%, #7c3aed 100%);
\t\tcolor: white;
\t\tpadding: 0.4rem 0.9rem;
\t\tborder-radius: 2rem;
\t\tfont-size: 0.813rem;
\t\tfont-weight: 600;
\t\tmargin-bottom: 1rem;
\t}

\t.badge-icon { font-size: 0.813rem; font-weight: 700; letter-spacing: 0.04em; }
\t.concept-desc { color: #4b5563; font-size: 0.938rem; line-height: 1.6; margin: 0; }

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
\t\tbackground: #f5f3ff;
\t\tborder-radius: 10px;
\t\tpadding: 0.875rem 1rem;
\t}

\t.rule-num {
\t\tmin-width: 2rem;
\t\theight: 2rem;
\t\tbackground: linear-gradient(135deg, #5b21b6 0%, #7c3aed 100%);
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

\t/* ── Category Hint ─────────────────────────────────── */
\t.hint-box {
\t\tbackground: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%);
\t\tborder-radius: 12px;
\t\tpadding: 1.25rem;
\t}

\t.hint-label { font-size: 0.813rem; color: #5b21b6; font-weight: 500; margin-bottom: 0.5rem; }
\t.hint-value { font-size: 1.5rem; font-weight: 800; color: #4c1d95; }

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

\t.game-title-row { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; }

\t.thinking-label {
\t\tfont-size: 1.25rem;
\t\tfont-weight: 700;
\t\tcolor: #4c1d95;
\t}

\t.category-tag {
\t\tbackground: #ede9fe;
\t\tcolor: #5b21b6;
\t\tpadding: 0.3rem 0.875rem;
\t\tborder-radius: 2rem;
\t\tfont-size: 0.875rem;
\t\tfont-weight: 600;
\t}

\t/* ── Question Counter ─────────────────────────────── */
\t.question-counter {
\t\tpadding: 0.5rem 1.25rem;
\t\tborder-radius: 2rem;
\t\tfont-size: 1.375rem;
\t\tfont-weight: 700;
\t\tdisplay: flex;
\t\talign-items: baseline;
\t\tgap: 0.4rem;
\t}

\t.counter-label { font-size: 0.813rem; font-weight: 400; }
\t.counter-safe    { background: linear-gradient(135deg, #5b21b6 0%, #7c3aed 100%); color: white; }
\t.counter-warn    { background: linear-gradient(135deg, #d97706 0%, #f59e0b 100%); color: white; }
\t.counter-danger  { background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%); color: white; animation: counter-pulse 0.5s ease-in-out infinite; }

\t/* ── Question History ─────────────────────────────── */
\t.history-section { margin-bottom: 1.25rem; }

\t.history-heading {
\t\tfont-size: 0.938rem;
\t\tfont-weight: 600;
\t\tcolor: #5b21b6;
\t\tmargin: 0 0 0.75rem 0;
\t}

\t.history-list {
\t\tdisplay: flex;
\t\tflex-direction: column;
\t\tgap: 0.625rem;
\t\tmax-height: 360px;
\t\toverflow-y: auto;
\t\tpadding-right: 0.25rem;
\t}

\t.history-empty { color: #9ca3af; font-style: italic; font-size: 0.875rem; text-align: center; padding: 1.5rem; }

\t.history-item {
\t\tbackground: #f5f3ff;
\t\tborder-radius: 8px;
\t\tpadding: 0.875rem 1rem;
\t\tborder-left: 4px solid #7c3aed;
\t}

\t.history-q { display: flex; align-items: flex-start; gap: 0.625rem; margin-bottom: 0.5rem; }

\t.q-num {
\t\tbackground: linear-gradient(135deg, #5b21b6 0%, #7c3aed 100%);
\t\tcolor: white;
\t\tpadding: 0.1rem 0.5rem;
\t\tborder-radius: 0.375rem;
\t\tfont-size: 0.75rem;
\t\tfont-weight: 700;
\t\twhite-space: nowrap;
\t\tflex-shrink: 0;
\t\tmargin-top: 0.125rem;
\t}

\t.q-text { font-size: 0.9rem; color: #374151; font-weight: 500; line-height: 1.4; }

\t.history-answer-row { display: flex; align-items: center; gap: 0.5rem; }

\t.answer-badge {
\t\tpadding: 0.2rem 0.75rem;
\t\tborder-radius: 1rem;
\t\tfont-size: 0.813rem;
\t\tfont-weight: 700;
\t\ttext-transform: uppercase;
\t}

\t.answer-yes     { background: #d1fae5; color: #065f46; }
\t.answer-no      { background: #fee2e2; color: #991b1b; }
\t.answer-partial { background: #fef3c7; color: #92400e; }

\t.confidence-label { font-size: 0.75rem; color: #16a34a; font-weight: 500; }

\t/* ── Input Card ───────────────────────────────────── */
\t.input-card {
\t\tbackground: #f5f3ff;
\t\tborder: 2px solid #ddd6fe;
\t\tborder-radius: 12px;
\t\tpadding: 1.25rem;
\t\tmargin-bottom: 1.25rem;
\t}

\t.input-label {
\t\tdisplay: block;
\t\tcolor: #5b21b6;
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

\t.question-input,
\t.guess-input {
\t\tflex: 1;
\t\tpadding: 0.875rem 1rem;
\t\tfont-size: 1rem;
\t\tborder: 2px solid #ddd6fe;
\t\tborder-radius: 10px;
\t\toutline: none;
\t\tbackground: white;
\t\tcolor: #1a1a2e;
\t\ttransition: border-color 0.15s;
\t}

\t.question-input:focus,
\t.guess-input:focus {
\t\tborder-color: #6d28d9;
\t\tbox-shadow: 0 0 0 3px rgba(109, 40, 217, 0.12);
\t}

\t.ask-btn {
\t\tbackground: linear-gradient(135deg, #5b21b6 0%, #7c3aed 100%);
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

\t.ask-btn:hover:not(:disabled) { opacity: 0.9; }
\t.ask-btn:disabled { opacity: 0.45; cursor: not-allowed; }

\t.input-tip { font-size: 0.8rem; color: #6d28d9; margin: 0; }

\t/* ── Guess Card ───────────────────────────────────── */
\t.guess-card {
\t\tbackground: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%);
\t\tborder: 2px solid #c4b5fd;
\t\tborder-radius: 12px;
\t\tpadding: 1.25rem;
\t\tmargin-bottom: 1.25rem;
\t}

\t.guess-heading {
\t\tfont-size: 1rem;
\t\tfont-weight: 700;
\t\tcolor: #4c1d95;
\t\tmargin: 0 0 0.75rem 0;
\t}

\t.guess-btn {
\t\tbackground: linear-gradient(135deg, #059669 0%, #10b981 100%);
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

\t.guess-btn:hover:not(:disabled) { opacity: 0.9; }
\t.guess-btn:disabled { opacity: 0.45; cursor: not-allowed; }

\t/* ── Skip / Give Up ───────────────────────────────── */
\t.skip-row { display: flex; justify-content: flex-end; margin-top: 0.5rem; }

\t/* ── Give Up Confirm ──────────────────────────────── */
\t.confirm-card {
\t\tbackground: #fff1f2;
\t\tborder: 2px solid #fda4af;
\t\tborder-radius: 12px;
\t\tpadding: 1.25rem;
\t\tmargin-top: 0.5rem;
\t\ttext-align: center;
\t}

\t.confirm-text { color: #9f1239; font-weight: 600; margin: 0 0 1rem 0; }

\t.confirm-buttons { display: flex; gap: 0.75rem; justify-content: center; }

\t.confirm-yes {
\t\tbackground: #dc2626;
\t\tcolor: white;
\t\tborder: none;
\t\tborder-radius: 8px;
\t\tpadding: 0.625rem 1.25rem;
\t\tfont-size: 0.875rem;
\t\tfont-weight: 600;
\t\tcursor: pointer;
\t}

\t.confirm-no {
\t\tbackground: white;
\t\tcolor: #374151;
\t\tborder: 2px solid #d1d5db;
\t\tborder-radius: 8px;
\t\tpadding: 0.625rem 1.25rem;
\t\tfont-size: 0.875rem;
\t\tfont-weight: 600;
\t\tcursor: pointer;
\t}

\t/* ── Results Header ───────────────────────────────── */
\t.results-header {
\t\tbackground: linear-gradient(135deg, #5b21b6 0%, #7c3aed 100%);
\t\tborder-radius: 16px;
\t\tpadding: 1.75rem;
\t\ttext-align: center;
\t\tmargin-bottom: 1rem;
\t\tbox-shadow: 0 4px 12px rgba(91, 33, 182, 0.35);
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
\t.answer-reveal    { color: #fde68a; font-size: 1.125rem; }

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

\t.metric-violet    { border-top-color: #6d28d9; }
\t.metric-correct   { border-top-color: #16a34a; }
\t.metric-incorrect { border-top-color: #dc2626; }
\t.metric-amber     { border-top-color: #d97706; }
\t.metric-blue      { border-top-color: #2563eb; }

\t.metric-value { font-size: 1.625rem; font-weight: 700; color: #1a1a2e; }
\t.metric-label { font-size: 0.75rem; color: #6b7280; margin-top: 0.25rem; }

\t/* ── Feedback ─────────────────────────────────────── */
\t.feedback-text { font-size: 0.938rem; color: #374151; line-height: 1.6; margin: 0 0 1rem 0; }

\t.tips-box {
\t\tbackground: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%);
\t\tborder-radius: 10px;
\t\tpadding: 1rem 1.25rem;
\t\tmargin-top: 0.5rem;
\t}

\t.tips-label { font-size: 0.875rem; font-weight: 700; color: #4c1d95; margin-bottom: 0.375rem; }
\t.tips-text  { font-size: 0.875rem; color: #5b21b6; line-height: 1.6; margin: 0; }

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

\t.action-buttons .btn-secondary { flex: 1; }
\t.btn-secondary:hover { background: #f5f3ff; transform: translateY(-2px); }

\t/* ── Help FAB ─────────────────────────────────────── */
\t.help-fab {
\t\tposition: fixed;
\t\tbottom: 2rem;
\t\tright: 2rem;
\t\twidth: 3rem;
\t\theight: 3rem;
\t\tbackground: linear-gradient(135deg, #5b21b6 0%, #7c3aed 100%);
\t\tcolor: white;
\t\tborder: none;
\t\tborder-radius: 50%;
\t\tfont-size: 1.25rem;
\t\tfont-weight: 700;
\t\tcursor: pointer;
\t\tbox-shadow: 0 4px 12px rgba(91, 33, 182, 0.4);
\t\tdisplay: flex;
\t\talign-items: center;
\t\tjustify-content: center;
\t}

\t/* ── Animations ───────────────────────────────────── */
\t@keyframes counter-pulse {
\t\t0%, 100% { transform: scale(1); }
\t\t50%       { transform: scale(1.06); }
\t}

\t/* ── Responsive ───────────────────────────────────── */
\t@media (max-width: 640px) {
\t\t.info-grid      { grid-template-columns: 1fr; }
\t\t.metrics-grid   { grid-template-columns: 1fr 1fr; }
\t\t.action-buttons { flex-direction: column; }
\t\t.game-status-bar { flex-direction: column; align-items: flex-start; }
\t\t.confirm-buttons { flex-direction: column; }
\t}
</style>
"""

with open(
    r'd:\NeuroBloom\frontend-svelte\src\routes\training\twenty-questions\+page.svelte',
    'w',
    encoding='utf-8'
) as f:
    f.write(CONTENT)

lines = CONTENT.count('\n') + 1
print(f'Done. Lines: {lines}')

#!/usr/bin/env python3
"""Redesign Stockings of Cambridge UI to LNS design system (blue #2563eb)."""

CONTENT = """\
<script>
\timport { goto } from '$app/navigation';
\timport { page } from '$app/stores';
\timport { API_BASE_URL } from '$lib/api.js';
\timport BadgeNotification from '$lib/components/BadgeNotification.svelte';
\timport DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
\timport LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
\timport PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
\timport TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
\timport { locale, localeText } from '$lib/i18n';
\timport { buildPracticePayload, getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
\timport { user } from '$lib/stores.js';
\timport { onMount } from 'svelte';

\tlet userId;
\tlet baselineScore = 0;
\tlet difficulty = 1;
\tlet taskId = null;
\tlet loading = false;

\tlet sessionData = null;
\tlet currentProblemIndex = 0;
\tlet currentProblem = null;

\t// Game state
\tlet currentState = [];
\tlet goalState = [];
\tlet selectedBall = null;
\tlet moveHistory = [];
\tlet problemStartTime = null;
\tlet totalMoves = 0;
\tlet stockingFullWarning = -1;
\tlet actualMinMoves = 0;

\t// UI state
\tlet gamePhase = 'intro';
\tlet planningTimeRemaining = 0;
\tlet planningTimer = null;
\tlet userSolutions = [];
\tlet solutions = [];
\tlet showingGoal = true;
\tlet results = null;
\tlet earnedBadges = [];
\tlet showSolution = false;
\tlet solutionPath = [];
\t/** @type {string} */
\tlet playMode = TASK_PLAY_MODE.RECORDED;
\tlet practiceStatusMessage = '';
\tlet recordedSessionData = null;
\tlet recordedDifficulty = 1;

\tconst BALL_COLORS = {
\t\t0: '#ef4444',
\t\t1: '#3b82f6',
\t\t2: '#22c55e'
\t};

\tconst STOCKING_CAPACITIES = [3, 2, 1];

\t// BFS algorithm to find minimum moves and solution path
\tfunction findOptimalSolution(startState, goalState) {
\t\tconst stateKey = (state) => JSON.stringify(state);
\t\tconst isGoal = (state) => stateKey(state) === stateKey(goalState);
\t\tconst queue = [{ state: startState.map(s => [...s]), moves: 0, path: [] }];
\t\tconst visited = new Set([stateKey(startState)]);

\t\twhile (queue.length > 0) {
\t\t\tconst { state, moves, path } = queue.shift();
\t\t\tif (isGoal(state)) return { minMoves: moves, path };

\t\t\tfor (let from = 0; from < 3; from++) {
\t\t\t\tif (state[from].length === 0) continue;
\t\t\t\tfor (let to = 0; to < 3; to++) {
\t\t\t\t\tif (from === to) continue;
\t\t\t\t\tif (state[to].length >= STOCKING_CAPACITIES[to]) continue;
\t\t\t\t\tconst newState = state.map(s => [...s]);
\t\t\t\t\tconst ball = newState[from].pop();
\t\t\t\t\tnewState[to].push(ball);
\t\t\t\t\tconst key = stateKey(newState);
\t\t\t\t\tif (!visited.has(key)) {
\t\t\t\t\t\tvisited.add(key);
\t\t\t\t\t\tqueue.push({ state: newState, moves: moves + 1, path: [...path, { from, to, ball }] });
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}
\t\t}
\t\treturn { minMoves: -1, path: [] };
\t}

\tuser.subscribe(value => {
\t\tif (value) userId = value.id;
\t});

\tfunction lt(en, bn) {
\t\treturn localeText({ en, bn }, $locale);
\t}

\tfunction cloneData(value) {
\t\tif (typeof structuredClone === 'function') return structuredClone(value);
\t\treturn JSON.parse(JSON.stringify(value));
\t}

\tfunction restoreRecordedSession() {
\t\tif (recordedSessionData) sessionData = cloneData(recordedSessionData);
\t\tdifficulty = recordedDifficulty;
\t}

\tfunction getDifficultyInfo() {
\t\tif (!sessionData) return '';
\t\tconst maxMoves = Math.max(...sessionData.problems.map(p => p.minimum_moves));
\t\tif (maxMoves <= 2) return lt('Simple 2-move problems', 'সহজ ২-পদক্ষেপের সমস্যা');
\t\tif (maxMoves <= 3) return lt('3-move planning challenges', '৩-পদক্ষেপের পরিকল্পনা চ্যালেঞ্জ');
\t\tif (maxMoves <= 4) return lt('4-move complex planning', '৪-পদক্ষেপের জটিল পরিকল্পনা');
\t\tif (maxMoves <= 5) return lt('5-move advanced problems', '৫-পদক্ষেপের উন্নত সমস্যা');
\t\treturn lt('6+ move expert challenges', '৬+ পদক্ষেপের বিশেষজ্ঞ চ্যালেঞ্জ');
\t}

\tonMount(async () => {
\t\tif (!userId) {
\t\t\tgoto('/login');
\t\t\treturn;
\t\t}
\t\tawait loadSession();
\t});

\tasync function loadSession() {
\t\ttry {
\t\t\tloading = true;
\t\t\tconst urlDifficulty = $page.url.searchParams.get('difficulty');
\t\t\tconst isDevTool = $page.url.searchParams.get('taskId')?.includes('_dev');

\t\t\tif (isDevTool && urlDifficulty) {
\t\t\t\tdifficulty = parseInt(urlDifficulty);
\t\t\t} else {
\t\t\t\tconst baselineRes = await fetch(`/api/baseline/${userId}`);
\t\t\t\tif (baselineRes.ok) {
\t\t\t\t\tconst baseline = await baselineRes.json();
\t\t\t\t\tbaselineScore = baseline.planning_score || 0;
\t\t\t\t\tif (baselineScore >= 90) difficulty = 9;
\t\t\t\t\telse if (baselineScore >= 80) difficulty = 8;
\t\t\t\t\telse if (baselineScore >= 70) difficulty = 7;
\t\t\t\t\telse if (baselineScore >= 60) difficulty = 6;
\t\t\t\t\telse if (baselineScore >= 50) difficulty = 5;
\t\t\t\t\telse if (baselineScore >= 40) difficulty = 4;
\t\t\t\t\telse if (baselineScore >= 30) difficulty = 3;
\t\t\t\t\telse if (baselineScore >= 20) difficulty = 2;
\t\t\t\t\telse difficulty = 1;
\t\t\t\t}
\t\t\t}

\t\t\tconst response = await fetch('/api/tasks/soc/generate', {
\t\t\t\tmethod: 'POST',
\t\t\t\theaders: { 'Content-Type': 'application/json' },
\t\t\t\tbody: JSON.stringify({ difficulty })
\t\t\t});

\t\t\tif (response.ok) {
\t\t\t\tsessionData = await response.json();
\t\t\t\tdifficulty = sessionData.difficulty;
\t\t\t\trecordedSessionData = cloneData(sessionData);
\t\t\t\trecordedDifficulty = difficulty;
\t\t\t}
\t\t} catch (_) {
\t\t\t// silent
\t\t} finally {
\t\t\tloading = false;
\t\t}
\t}

\t/** @param {string} nextMode */
\tfunction startTask(nextMode = TASK_PLAY_MODE.RECORDED) {
\t\tplayMode = nextMode;
\t\tpracticeStatusMessage = '';
\t\trestoreRecordedSession();
\t\tif (playMode === TASK_PLAY_MODE.PRACTICE) {
\t\t\tsessionData = buildPracticePayload('stockings-of-cambridge', recordedSessionData);
\t\t}
\t\tuserSolutions = [];
\t\tsolutions = [];
\t\tresults = null;
\t\tearnedBadges = [];
\t\tgamePhase = 'planning';
\t\tloadProblem(0);
\t}

\tfunction loadProblem(index) {
\t\tcurrentProblemIndex = index;
\t\tcurrentProblem = sessionData.problems[index];
\t\tcurrentState = currentProblem.start_state.map(s => [...s]);
\t\tgoalState = currentProblem.goal_state.map(s => [...s]);

\t\tconst solution = findOptimalSolution(currentState, goalState);
\t\tactualMinMoves = solution.minMoves;
\t\tsolutionPath = solution.path;
\t\tcurrentProblem.minimum_moves = actualMinMoves;

\t\tselectedBall = null;
\t\tmoveHistory = [];
\t\ttotalMoves = 0;
\t\tshowingGoal = true;
\t\tshowSolution = false;
\t\tstockingFullWarning = -1;

\t\tgamePhase = 'planning';
\t\tplanningTimeRemaining = sessionData.config.planning_time_seconds;
\t\tstartPlanningTimer();
\t}

\tfunction startPlanningTimer() {
\t\tif (planningTimer) clearInterval(planningTimer);
\t\tplanningTimer = setInterval(() => {
\t\t\tplanningTimeRemaining--;
\t\t\tif (planningTimeRemaining <= 0) {
\t\t\t\tclearInterval(planningTimer);
\t\t\t\tstartSolving();
\t\t\t}
\t\t}, 1000);
\t}

\tfunction startSolving() {
\t\tif (planningTimer) clearInterval(planningTimer);
\t\tgamePhase = 'solving';
\t\tshowingGoal = false;
\t\tproblemStartTime = Date.now();
\t}

\tfunction selectBall(stockingIndex, ballIndex) {
\t\tif (gamePhase !== 'solving') return;
\t\tstockingFullWarning = -1;
\t\tconst stocking = currentState[stockingIndex];
\t\tif (ballIndex !== stocking.length - 1) return;
\t\tif (selectedBall && selectedBall.stockingIndex === stockingIndex && selectedBall.ballIndex === ballIndex) {
\t\t\tselectedBall = null;
\t\t} else {
\t\t\tselectedBall = { stockingIndex, ballIndex, color: stocking[ballIndex] };
\t\t}
\t}

\tfunction moveToStocking(targetStockingIndex) {
\t\tif (gamePhase !== 'solving' || !selectedBall) return;
\t\tconst targetStocking = currentState[targetStockingIndex];

\t\tif (selectedBall.stockingIndex === targetStockingIndex) {
\t\t\tselectedBall = null;
\t\t\treturn;
\t\t}

\t\tif (targetStocking.length >= STOCKING_CAPACITIES[targetStockingIndex]) {
\t\t\tstockingFullWarning = targetStockingIndex;
\t\t\tselectedBall = null;
\t\t\tsetTimeout(() => { stockingFullWarning = -1; }, 1800);
\t\t\treturn;
\t\t}

\t\tstockingFullWarning = -1;
\t\tconst sourceStocking = currentState[selectedBall.stockingIndex];
\t\tconst ball = sourceStocking.pop();
\t\ttargetStocking.push(ball);
\t\ttotalMoves++;
\t\tmoveHistory.push({ from: selectedBall.stockingIndex, to: targetStockingIndex, ball });
\t\tselectedBall = null;

\t\tif (checkSolved()) completeProblem();
\t\tcurrentState = currentState.map(s => [...s]);
\t}

\tfunction checkSolved() {
\t\tfor (let i = 0; i < 3; i++) {
\t\t\tif (currentState[i].length !== goalState[i].length) return false;
\t\t\tfor (let j = 0; j < currentState[i].length; j++) {
\t\t\t\tif (currentState[i][j] !== goalState[i][j]) return false;
\t\t\t}
\t\t}
\t\treturn true;
\t}

\tfunction completeProblem() {
\t\tconst timeElapsed = (Date.now() - problemStartTime) / 1000;
\t\tconst problemSolution = {
\t\t\tproblem_number: currentProblem.problem_number,
\t\t\tsolved: true,
\t\t\tmoves_used: totalMoves,
\t\t\ttime_seconds: timeElapsed,
\t\t\tmove_history: moveHistory
\t\t};
\t\tuserSolutions.push(problemSolution);
\t\tsolutions.push(problemSolution);
\t\tif (currentProblemIndex < sessionData.problems.length - 1) {
\t\t\tgamePhase = 'problem_complete';
\t\t} else {
\t\t\tfinishSession();
\t\t}
\t}

\tfunction nextProblem() {
\t\tloadProblem(currentProblemIndex + 1);
\t}

\tasync function finishSession() {
\t\tif (playMode === TASK_PLAY_MODE.PRACTICE) {
\t\t\tplayMode = TASK_PLAY_MODE.RECORDED;
\t\t\tpracticeStatusMessage = getPracticeCopy($locale).complete;
\t\t\tsessionData = null;
\t\t\tcurrentProblemIndex = 0;
\t\t\tcurrentProblem = null;
\t\t\tuserSolutions = [];
\t\t\tsolutions = [];
\t\t\tselectedBall = null;
\t\t\tgamePhase = 'intro';
\t\t\tawait loadSession();
\t\t\treturn;
\t\t}
\t\ttry {
\t\t\tconst scoreResponse = await fetch('/api/tasks/soc/score', {
\t\t\t\tmethod: 'POST',
\t\t\t\theaders: { 'Content-Type': 'application/json' },
\t\t\t\tbody: JSON.stringify({ session_data: sessionData, user_solutions: userSolutions })
\t\t\t});
\t\t\tif (scoreResponse.ok) {
\t\t\t\tresults = await scoreResponse.json();
\t\t\t\tawait saveResults();
\t\t\t\tgamePhase = 'results';
\t\t\t}
\t\t} catch (_) {
\t\t\t// silent
\t\t}
\t}

\tasync function saveResults() {
\t\ttry {
\t\t\ttaskId = $page.url.searchParams.get('taskId');
\t\t\tconst response = await fetch(`${API_BASE_URL}/api/training/tasks/soc/submit/${userId}`, {
\t\t\t\tmethod: 'POST',
\t\t\t\theaders: { 'Content-Type': 'application/json' },
\t\t\t\tcredentials: 'include',
\t\t\t\tbody: JSON.stringify({
\t\t\t\t\tsession_data: { ...sessionData, difficulty },
\t\t\t\t\tuser_solutions: solutions,
\t\t\t\t\ttask_id: taskId
\t\t\t\t})
\t\t\t});
\t\t\tif (!response.ok) throw new Error('Failed to save');
\t\t\tconst data = await response.json();
\t\t\tif (data.new_badges && data.new_badges.length > 0) {
\t\t\t\tearnedBadges = data.new_badges;
\t\t\t}
\t\t\tuser.update(u => ({ ...u, planning_difficulty: data.new_difficulty }));
\t\t} catch (_) {
\t\t\t// silent
\t\t}
\t}

\tfunction toggleGoalView() {
\t\tshowingGoal = !showingGoal;
\t}
</script>

<div class="soc-page" data-localize-skip>
\t<div class="soc-wrapper">

\t\t{#if gamePhase === 'intro'}

\t\t\t<!-- Header Card -->
\t\t\t<div class="header-card">
\t\t\t\t<div class="header-content">
\t\t\t\t\t<div class="header-text">
\t\t\t\t\t\t<h1 class="task-title">{lt('Stockings of Cambridge', 'স্টকিংস অব কেমব্রিজ')}</h1>
\t\t\t\t\t\t<p class="task-domain">{lt('Planning / Executive Function', 'পরিকল্পনা / নির্বাহী কার্যকারিতা')}</p>
\t\t\t\t\t</div>
\t\t\t\t\t<DifficultyBadge difficulty={sessionData?.difficulty || difficulty} domain="Executive Planning" />
\t\t\t\t</div>
\t\t\t</div>

\t\t\t{#if playMode === TASK_PLAY_MODE.PRACTICE}
\t\t\t\t<PracticeModeBanner locale={$locale} />
\t\t\t{/if}

\t\t\t{#if loading}
\t\t\t\t<LoadingSkeleton />
\t\t\t{:else}

\t\t\t\t<!-- Task Concept -->
\t\t\t\t<div class="card task-concept">
\t\t\t\t\t<div class="concept-badge">
\t\t\t\t\t\t<span class="badge-icon">SOC</span>
\t\t\t\t\t\t<span>{lt('Executive Planning', 'নির্বাহী পরিকল্পনা')}</span>
\t\t\t\t\t</div>
\t\t\t\t\t<p class="concept-desc">
\t\t\t\t\t\t{lt(
\t\t\t\t\t\t\t'The Stockings of Cambridge is a CANTAB variant of the Tower of London. Move coloured balls between stockings to match a target arrangement in the minimum number of moves. It measures planning, working memory, and prefrontal executive function — domains frequently impaired in multiple sclerosis.',
\t\t\t\t\t\t\t'স্টকিংস অব কেমব্রিজ হলো টাওয়ার অব লন্ডনের একটি CANTAB রূপ। সর্বনিম্ন পদক্ষেপে রঙিন বল রিঅ্যারেঞ্জ করে লক্ষ্য বিন্যাসের সাথে মেলাতে হয়। এটি পরিকল্পনা, ওয়ার্কিং মেমোরি এবং প্রিফ্রন্টাল নির্বাহী কার্যকারিতা পরিমাপ করে।'
\t\t\t\t\t\t)}
\t\t\t\t\t</p>
\t\t\t\t</div>

\t\t\t\t<!-- Rules Grid -->
\t\t\t\t<div class="card">
\t\t\t\t\t<h2 class="section-title">{lt('How to Play', 'কীভাবে খেলবেন')}</h2>
\t\t\t\t\t<div class="rules-grid">
\t\t\t\t\t\t<div class="rule-item">
\t\t\t\t\t\t\t<div class="rule-num">1</div>
\t\t\t\t\t\t\t<div class="rule-text">
\t\t\t\t\t\t\t\t<strong>{lt('Study start and goal', 'শুরু এবং লক্ষ্য পর্যবেক্ষণ করুন')}</strong>
\t\t\t\t\t\t\t\t<span>{lt('Both stocking configurations are shown during the planning phase. Memorise the goal layout.', 'পরিকল্পনা পর্যায়ে উভয় বিন্যাস দেখানো হয়। লক্ষ্য বিন্যাস মনে রাখুন।')}</span>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="rule-item">
\t\t\t\t\t\t\t<div class="rule-num">2</div>
\t\t\t\t\t\t\t<div class="rule-text">
\t\t\t\t\t\t\t\t<strong>{lt('Plan before moving', 'চলার আগে পরিকল্পনা করুন')}</strong>
\t\t\t\t\t\t\t\t<span>{lt('Work out the full move sequence in your head before touching any ball.', 'কোনো বল স্পর্শ করার আগে সম্পূর্ণ পদক্ষেপের ক্রম মাথায় নির্ধারণ করুন।')}</span>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="rule-item">
\t\t\t\t\t\t\t<div class="rule-num">3</div>
\t\t\t\t\t\t\t<div class="rule-text">
\t\t\t\t\t\t\t\t<strong>{lt('Click ball, then click stocking', 'বল ক্লিক করুন তারপর স্টকিং ক্লিক করুন')}</strong>
\t\t\t\t\t\t\t\t<span>{lt('Select the top ball in any stocking, then click the destination stocking to place it.', 'যেকোনো স্টকিংয়ের সবচেয়ে উপরের বলটি নির্বাচন করুন, তারপর গন্তব্য স্টকিংয়ে ক্লিক করুন।')}</span>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="rule-item">
\t\t\t\t\t\t\t<div class="rule-num">4</div>
\t\t\t\t\t\t\t<div class="rule-text">
\t\t\t\t\t\t\t\t<strong>{lt('Respect capacity limits', 'ধারণক্ষমতার সীমা মানুন')}</strong>
\t\t\t\t\t\t\t\t<span>{lt('Stocking 1 holds 3 balls, Stocking 2 holds 2, Stocking 3 holds only 1. Full stockings refuse new balls.', 'স্টকিং ১ — ৩টি, স্টকিং ২ — ২টি, স্টকিং ৩ — ১টি বল ধারণ করে। পূর্ণ স্টকিং নতুন বল গ্রহণ করে না।')}</span>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Stocking Capacity Visual -->
\t\t\t\t<div class="card">
\t\t\t\t\t<h2 class="section-title">{lt('Stocking Capacities', 'স্টকিংয়ের ধারণক্ষমতা')}</h2>
\t\t\t\t\t<div class="cap-row">
\t\t\t\t\t\t<div class="cap-item">
\t\t\t\t\t\t\t<div class="cap-circle cap-1">3</div>
\t\t\t\t\t\t\t<div class="cap-label">{lt('Stocking 1', 'স্টকিং ১')}</div>
\t\t\t\t\t\t\t<div class="cap-sub">{lt('3 balls max', 'সর্বোচ্চ ৩টি')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="cap-arrow">&#8594;</div>
\t\t\t\t\t\t<div class="cap-item">
\t\t\t\t\t\t\t<div class="cap-circle cap-2">2</div>
\t\t\t\t\t\t\t<div class="cap-label">{lt('Stocking 2', 'স্টকিং ২')}</div>
\t\t\t\t\t\t\t<div class="cap-sub">{lt('2 balls max', 'সর্বোচ্চ ২টি')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="cap-arrow">&#8594;</div>
\t\t\t\t\t\t<div class="cap-item">
\t\t\t\t\t\t\t<div class="cap-circle cap-3">1</div>
\t\t\t\t\t\t\t<div class="cap-label">{lt('Stocking 3', 'স্টকিং ৩')}</div>
\t\t\t\t\t\t\t<div class="cap-sub">{lt('1 ball max', 'সর্বোচ্চ ১টি')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Info Grid -->
\t\t\t\t<div class="info-grid">
\t\t\t\t\t<div class="card">
\t\t\t\t\t\t<h3 class="card-title">{lt('Session Details', 'সেশনের বিবরণ')}</h3>
\t\t\t\t\t\t<div class="details-list">
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{lt('Problems', 'সমস্যা')}</span>
\t\t\t\t\t\t\t\t<strong>{sessionData ? sessionData.total_problems : '—'}</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{lt('Planning Time', 'পরিকল্পনার সময়')}</span>
\t\t\t\t\t\t\t\t<strong>{sessionData ? sessionData.config.planning_time_seconds + 's' : '—'}</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{lt('Difficulty', 'কঠিনতা')}</span>
\t\t\t\t\t\t\t\t<strong>{lt(`Level ${difficulty} / 10`, `লেভেল ${difficulty} / ১০`)}</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{lt('Problem Type', 'সমস্যার ধরন')}</span>
\t\t\t\t\t\t\t\t<strong>{getDifficultyInfo()}</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t{#if baselineScore > 0}
\t\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t\t<span>{lt('Planning Baseline', 'পরিকল্পনা বেসলাইন')}</span>
\t\t\t\t\t\t\t\t\t<strong>{baselineScore}/100</strong>
\t\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t{/if}
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t\t<div class="card">
\t\t\t\t\t\t<h3 class="card-title">{lt('What It Measures', 'এটি কী পরিমাপ করে')}</h3>
\t\t\t\t\t\t<div class="details-list">
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{lt('Primary Metric', 'প্রাথমিক মেট্রিক')}</span>
\t\t\t\t\t\t\t\t<strong>{lt('Planning efficiency', 'পরিকল্পনা দক্ষতা')}</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{lt('Cognitive Domain', 'জ্ঞানীয় ডোমেইন')}</span>
\t\t\t\t\t\t\t\t<strong>{lt('Executive function', 'নির্বাহী কার্যকারিতা')}</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{lt('Scoring Basis', 'স্কোরিং ভিত্তি')}</span>
\t\t\t\t\t\t\t\t<strong>{lt('Moves used vs minimum', 'ব্যবহৃত বনাম সর্বনিম্ন')}</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="detail-row">
\t\t\t\t\t\t\t\t<span>{lt('Test Battery', 'পরীক্ষার ব্যাটারি')}</span>
\t\t\t\t\t\t\t\t<strong>CANTAB</strong>
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<!-- Clinical Info -->
\t\t\t\t<div class="clinical-info">
\t\t\t\t\t<div class="clinical-header">
\t\t\t\t\t\t<div class="clinical-badge">{lt('Clinical Basis', 'ক্লিনিকাল ভিত্তি')}</div>
\t\t\t\t\t\t<h3>{lt('CANTAB Gold Standard Planning Test', 'CANTAB গোল্ড স্ট্যান্ডার্ড পরিকল্পনা পরীক্ষা')}</h3>
\t\t\t\t\t</div>
\t\t\t\t\t<p>
\t\t\t\t\t\t{lt(
\t\t\t\t\t\t\t'Owen et al. (1990) introduced the Stockings of Cambridge as the CANTAB computerised version of the Tower of London. MS patients show significantly more excess moves and longer thinking times, with performance correlating with lesion load in frontal and parietal white matter. The task is included in the BICAMS cognitive battery for MS.',
\t\t\t\t\t\t\t'ওয়েন et al. (১৯৯০) টাওয়ার অব লন্ডনের CANTAB কম্পিউটারাইজড সংস্করণ হিসেবে স্টকিংস অব কেমব্রিজ প্রবর্তন করেন। এমএস রোগীরা উল্লেখযোগ্যভাবে বেশি অতিরিক্ত পদক্ষেপ করেন। পারফরম্যান্স ফ্রন্টাল এবং প্যারিটাল সাদা পদার্থে লেশন লোডের সাথে সম্পর্কিত।'
\t\t\t\t\t\t)}
\t\t\t\t\t</p>
\t\t\t\t</div>

\t\t\t\t<!-- Performance Guide -->
\t\t\t\t<div class="card perf-guide">
\t\t\t\t\t<h3 class="card-title">{lt('Planning Efficiency Norms', 'পরিকল্পনা দক্ষতার নির্দেশিকা')}</h3>
\t\t\t\t\t<p class="perf-subtitle">{lt('Minimum moves / moves used (higher = better)', 'সর্বনিম্ন পদক্ষেপ / ব্যবহৃত পদক্ষেপ (বেশি = ভালো)')}</p>
\t\t\t\t\t<div class="norm-bars">
\t\t\t\t\t\t<div class="norm-bar">
\t\t\t\t\t\t\t<div class="norm-label">{lt('Excellent', 'উৎকৃষ্ট')}</div>
\t\t\t\t\t\t\t<div class="norm-track"><div class="norm-fill norm-excellent"></div></div>
\t\t\t\t\t\t\t<div class="norm-range">&gt; 80%</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="norm-bar">
\t\t\t\t\t\t\t<div class="norm-label">{lt('Normal', 'স্বাভাবিক')}</div>
\t\t\t\t\t\t\t<div class="norm-track"><div class="norm-fill norm-normal"></div></div>
\t\t\t\t\t\t\t<div class="norm-range">60–80%</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="norm-bar">
\t\t\t\t\t\t\t<div class="norm-label">{lt('Impaired', 'দুর্বল')}</div>
\t\t\t\t\t\t\t<div class="norm-track"><div class="norm-fill norm-impaired"></div></div>
\t\t\t\t\t\t\t<div class="norm-range">&lt; 60%</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<TaskPracticeActions
\t\t\t\t\tlocale={$locale}
\t\t\t\t\tstartLabel={lt('Start Planning Challenge', 'পরিকল্পনা চ্যালেঞ্জ শুরু করুন')}
\t\t\t\t\tstatusMessage={practiceStatusMessage}
\t\t\t\t\ton:start={() => startTask(TASK_PLAY_MODE.RECORDED)}
\t\t\t\t\ton:practice={() => startTask(TASK_PLAY_MODE.PRACTICE)}
\t\t\t\t/>

\t\t\t{/if}

\t\t{:else if gamePhase === 'planning'}

\t\t\t<div class="game-card">
\t\t\t\t{#if playMode === TASK_PLAY_MODE.PRACTICE}
\t\t\t\t\t<PracticeModeBanner locale={$locale} />
\t\t\t\t{/if}

\t\t\t\t<!-- Status Bar -->
\t\t\t\t<div class="game-status-bar">
\t\t\t\t\t<div class="status-pills">
\t\t\t\t\t\t<span class="pill pill-soc">{lt(`Problem ${currentProblem.problem_number} / ${sessionData.total_problems}`, `সমস্যা ${currentProblem.problem_number} / ${sessionData.total_problems}`)}</span>
\t\t\t\t\t\t<span class="pill pill-phase">{lt('Planning', 'পরিকল্পনা')}</span>
\t\t\t\t\t</div>
\t\t\t\t\t<div class="planning-timer" class:timer-urgent={planningTimeRemaining <= 5}>
\t\t\t\t\t\t{planningTimeRemaining}s
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t{#if currentProblem.show_minimum}
\t\t\t\t\t<div class="min-moves-banner">
\t\t\t\t\t\t{lt(`Minimum moves required: ${currentProblem.minimum_moves}`, `প্রয়োজনীয় সর্বনিম্ন পদক্ষেপ: ${currentProblem.minimum_moves}`)}
\t\t\t\t\t</div>
\t\t\t\t{/if}

\t\t\t\t<!-- Stockings side by side: START vs GOAL -->
\t\t\t\t<div class="towers-row">
\t\t\t\t\t<div class="tower-panel">
\t\t\t\t\t\t<div class="tower-label tower-label-start">{lt('START', 'শুরু')}</div>
\t\t\t\t\t\t<div class="stockings-row">
\t\t\t\t\t\t\t{#each currentProblem.start_state as stocking, stockingIndex}
\t\t\t\t\t\t\t\t<div class="stocking-col">
\t\t\t\t\t\t\t\t\t<div class="stocking-rim"></div>
\t\t\t\t\t\t\t\t\t<div class="stocking-body stocking-body-static">
\t\t\t\t\t\t\t\t\t\t{#each stocking as ballColor}
\t\t\t\t\t\t\t\t\t\t\t<div class="ball-static"
\t\t\t\t\t\t\t\t\t\t\t\tstyle="background: radial-gradient(circle at 35% 35%, rgba(255,255,255,0.45), {BALL_COLORS[ballColor]});">
\t\t\t\t\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t\t\t\t{/each}
\t\t\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t\t\t<div class="stocking-cap-count">{STOCKING_CAPACITIES[stockingIndex]}</div>
\t\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t{/each}
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>

\t\t\t\t\t<div class="towers-divider">&#8594;</div>

\t\t\t\t\t<div class="tower-panel">
\t\t\t\t\t\t<div class="tower-label tower-label-goal">{lt('GOAL', 'লক্ষ্য')}</div>
\t\t\t\t\t\t<div class="stockings-row">
\t\t\t\t\t\t\t{#each currentProblem.goal_state as stocking, stockingIndex}
\t\t\t\t\t\t\t\t<div class="stocking-col">
\t\t\t\t\t\t\t\t\t<div class="stocking-rim stocking-rim-goal"></div>
\t\t\t\t\t\t\t\t\t<div class="stocking-body stocking-body-static stocking-body-goal">
\t\t\t\t\t\t\t\t\t\t{#each stocking as ballColor}
\t\t\t\t\t\t\t\t\t\t\t<div class="ball-static ball-static-goal"
\t\t\t\t\t\t\t\t\t\t\t\tstyle="background: radial-gradient(circle at 35% 35%, rgba(255,255,255,0.3), {BALL_COLORS[ballColor]});">
\t\t\t\t\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t\t\t\t{/each}
\t\t\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t\t\t<div class="stocking-cap-count stocking-cap-faded">{STOCKING_CAPACITIES[stockingIndex]}</div>
\t\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t{/each}
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t</div>

\t\t\t\t<div class="planning-footer">
\t\t\t\t\t<p class="planning-hint">
\t\t\t\t\t\t{lt('Study both configurations and plan your ball sequence before the timer runs out.', 'টাইমার শেষ হওয়ার আগে উভয় বিন্যাস পর্যবেক্ষণ করুন এবং আপনার বলের ক্রম পরিকল্পনা করুন।')}
\t\t\t\t\t</p>
\t\t\t\t\t<button class="ready-btn" on:click={startSolving}>
\t\t\t\t\t\t{lt('Ready — Start Solving', 'প্রস্তুত — সমাধান শুরু করুন')}
\t\t\t\t\t</button>
\t\t\t\t</div>
\t\t\t</div>

\t\t{:else if gamePhase === 'solving'}

\t\t\t<div class="game-card">
\t\t\t\t{#if playMode === TASK_PLAY_MODE.PRACTICE}
\t\t\t\t\t<PracticeModeBanner locale={$locale} />
\t\t\t\t{/if}

\t\t\t\t<!-- Solving Status Bar -->
\t\t\t\t<div class="game-status-bar">
\t\t\t\t\t<div class="status-pills">
\t\t\t\t\t\t<span class="pill pill-soc">{lt(`Problem ${currentProblem.problem_number} / ${sessionData.total_problems}`, `সমস্যা ${currentProblem.problem_number} / ${sessionData.total_problems}`)}</span>
\t\t\t\t\t\t<span class="pill pill-moves">{lt(`Moves: ${totalMoves}`, `পদক্ষেপ: ${totalMoves}`)}</span>
\t\t\t\t\t\t{#if currentProblem.show_minimum}
\t\t\t\t\t\t\t<span class="pill pill-target">{lt(`Min: ${currentProblem.minimum_moves}`, `সর্বনিম্ন: ${currentProblem.minimum_moves}`)}</span>
\t\t\t\t\t\t{/if}
\t\t\t\t\t</div>
\t\t\t\t\t<button class="toggle-goal-btn" on:click={toggleGoalView}>
\t\t\t\t\t\t{showingGoal ? lt('Hide Goal', 'লক্ষ্য লুকান') : lt('Show Goal', 'লক্ষ্য দেখান')}
\t\t\t\t\t</button>
\t\t\t\t</div>

\t\t\t\t<!-- Selected ball indicator -->
\t\t\t\t{#if selectedBall !== null}
\t\t\t\t\t<div class="selected-indicator">
\t\t\t\t\t\t<div class="selected-swatch"
\t\t\t\t\t\t\tstyle="background: radial-gradient(circle at 35% 35%, rgba(255,255,255,0.45), {BALL_COLORS[selectedBall.color]});">
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<span>{lt('Ball selected — click any stocking to move it', 'বল নির্বাচিত — এটি সরাতে যেকোনো স্টকিংয়ে ক্লিক করুন')}</span>
\t\t\t\t\t</div>
\t\t\t\t{/if}

\t\t\t\t<!-- Stocking full warning -->
\t\t\t\t{#if stockingFullWarning >= 0}
\t\t\t\t\t<div class="stocking-full-warning">
\t\t\t\t\t\t{lt(`Stocking ${stockingFullWarning + 1} is full (max ${STOCKING_CAPACITIES[stockingFullWarning]} balls)`, `স্টকিং ${stockingFullWarning + 1} পূর্ণ (সর্বোচ্চ ${STOCKING_CAPACITIES[stockingFullWarning]} বল)`)}
\t\t\t\t\t</div>
\t\t\t\t{/if}

\t\t\t\t<!-- Solving Layout -->
\t\t\t\t<div class="solving-row" class:solving-single={!showingGoal}>

\t\t\t\t\t<!-- Interactive current state -->
\t\t\t\t\t<div class="tower-panel">
\t\t\t\t\t\t<div class="tower-label tower-label-current">{lt('CURRENT POSITION', 'বর্তমান অবস্থান')}</div>
\t\t\t\t\t\t<div class="stockings-row">
\t\t\t\t\t\t\t{#each currentState as stocking, stockingIndex}
\t\t\t\t\t\t\t\t{@const isFull = stocking.length >= STOCKING_CAPACITIES[stockingIndex]}
\t\t\t\t\t\t\t\t<div class="stocking-col">
\t\t\t\t\t\t\t\t\t<div class="stocking-rim"
\t\t\t\t\t\t\t\t\t\tclass:rim-drop={selectedBall && selectedBall.stockingIndex !== stockingIndex && !isFull}>
\t\t\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t\t\t<div class="stocking-body stocking-body-interactive"
\t\t\t\t\t\t\t\t\t\tclass:drop-active={selectedBall && selectedBall.stockingIndex !== stockingIndex && !isFull}
\t\t\t\t\t\t\t\t\t\tclass:drop-full={selectedBall && selectedBall.stockingIndex !== stockingIndex && isFull}
\t\t\t\t\t\t\t\t\t\tclass:drop-warn={stockingFullWarning === stockingIndex}
\t\t\t\t\t\t\t\t\t\trole="button"
\t\t\t\t\t\t\t\t\t\ttabindex="0"
\t\t\t\t\t\t\t\t\t\taria-label="Move ball to stocking {stockingIndex + 1}"
\t\t\t\t\t\t\t\t\t\ton:click={() => moveToStocking(stockingIndex)}
\t\t\t\t\t\t\t\t\t\ton:keydown={(e) => e.key === 'Enter' && moveToStocking(stockingIndex)}>
\t\t\t\t\t\t\t\t\t\t{#each stocking as ballColor, ballIndex}
\t\t\t\t\t\t\t\t\t\t\t{@const isTopBall = ballIndex === stocking.length - 1}
\t\t\t\t\t\t\t\t\t\t\t{@const isSelected = selectedBall && selectedBall.stockingIndex === stockingIndex && selectedBall.ballIndex === ballIndex}
\t\t\t\t\t\t\t\t\t\t\t<button
\t\t\t\t\t\t\t\t\t\t\t\ton:click|stopPropagation={() => selectBall(stockingIndex, ballIndex)}
\t\t\t\t\t\t\t\t\t\t\t\tdisabled={!isTopBall}
\t\t\t\t\t\t\t\t\t\t\t\tclass="ball-btn"
\t\t\t\t\t\t\t\t\t\t\t\tclass:ball-selected={isSelected}
\t\t\t\t\t\t\t\t\t\t\t\tclass:ball-top={isTopBall && !isSelected}
\t\t\t\t\t\t\t\t\t\t\t\tclass:ball-locked={!isTopBall}
\t\t\t\t\t\t\t\t\t\t\t\taria-label="{isTopBall ? 'Select' : 'Cannot select'} ball in stocking {stockingIndex + 1}"
\t\t\t\t\t\t\t\t\t\t\t\tstyle="background: radial-gradient(circle at 35% 35%, rgba(255,255,255,0.5), {BALL_COLORS[ballColor]});">
\t\t\t\t\t\t\t\t\t\t\t</button>
\t\t\t\t\t\t\t\t\t\t{/each}
\t\t\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t\t\t<div class="stocking-count-badge" class:count-full={isFull}>
\t\t\t\t\t\t\t\t\t\t{stocking.length}/{STOCKING_CAPACITIES[stockingIndex]}
\t\t\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t{/each}
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>

\t\t\t\t\t<!-- Goal reference -->
\t\t\t\t\t{#if showingGoal}
\t\t\t\t\t\t<div class="tower-panel tower-panel-dim">
\t\t\t\t\t\t\t<div class="tower-label tower-label-goal">{lt('TARGET', 'লক্ষ্য')}</div>
\t\t\t\t\t\t\t<div class="stockings-row">
\t\t\t\t\t\t\t\t{#each goalState as stocking, stockingIndex}
\t\t\t\t\t\t\t\t\t<div class="stocking-col">
\t\t\t\t\t\t\t\t\t\t<div class="stocking-rim stocking-rim-goal"></div>
\t\t\t\t\t\t\t\t\t\t<div class="stocking-body stocking-body-static stocking-body-goal">
\t\t\t\t\t\t\t\t\t\t\t{#each stocking as ballColor}
\t\t\t\t\t\t\t\t\t\t\t\t<div class="ball-static ball-static-goal"
\t\t\t\t\t\t\t\t\t\t\t\t\tstyle="background: radial-gradient(circle at 35% 35%, rgba(255,255,255,0.3), {BALL_COLORS[ballColor]});">
\t\t\t\t\t\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t\t\t\t\t{/each}
\t\t\t\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t\t\t\t<div class="stocking-cap-count stocking-cap-faded">{STOCKING_CAPACITIES[stockingIndex]}</div>
\t\t\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t\t{/each}
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t{/if}

\t\t\t\t</div>
\t\t\t</div>

\t\t{:else if gamePhase === 'problem_complete'}

\t\t\t<div class="completion-card">
\t\t\t\t{#if playMode === TASK_PLAY_MODE.PRACTICE}
\t\t\t\t\t<PracticeModeBanner locale={$locale} />
\t\t\t\t{/if}

\t\t\t\t<div class="completion-badge">{lt('Problem Solved', 'সমস্যা সমাধান হয়েছে')}</div>
\t\t\t\t<h2 class="completion-title">{lt('Well done!', 'চমৎকার!')}</h2>

\t\t\t\t<div class="completion-stats">
\t\t\t\t\t<div class="cstat">
\t\t\t\t\t\t<div class="cstat-val">{userSolutions[userSolutions.length - 1].moves_used}</div>
\t\t\t\t\t\t<div class="cstat-lbl">{lt('Moves used', 'ব্যবহৃত পদক্ষেপ')}</div>
\t\t\t\t\t</div>
\t\t\t\t\t{#if currentProblem.show_minimum}
\t\t\t\t\t\t<div class="cstat">
\t\t\t\t\t\t\t<div class="cstat-val">{actualMinMoves}</div>
\t\t\t\t\t\t\t<div class="cstat-lbl">{lt('Minimum', 'সর্বনিম্ন')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t\t<div class="cstat">
\t\t\t\t\t\t\t<div class="cstat-val"
\t\t\t\t\t\t\t\tclass:cstat-perfect={userSolutions[userSolutions.length - 1].moves_used === actualMinMoves}
\t\t\t\t\t\t\t\tclass:cstat-extra={userSolutions[userSolutions.length - 1].moves_used !== actualMinMoves}>
\t\t\t\t\t\t\t\t{userSolutions[userSolutions.length - 1].moves_used === actualMinMoves
\t\t\t\t\t\t\t\t\t? lt('Perfect', 'নিখুঁত')
\t\t\t\t\t\t\t\t\t: '+' + (userSolutions[userSolutions.length - 1].moves_used - actualMinMoves)}
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t<div class="cstat-lbl">{lt('Extra moves', 'অতিরিক্ত পদক্ষেপ')}</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t{/if}
\t\t\t\t</div>

\t\t\t\t<div class="completion-actions">
\t\t\t\t\t{#if !showSolution}
\t\t\t\t\t\t<button class="btn-secondary" on:click={() => showSolution = true}>
\t\t\t\t\t\t\t{lt('Show Optimal Solution', 'সর্বোত্তম সমাধান দেখুন')}
\t\t\t\t\t\t</button>
\t\t\t\t\t{/if}
\t\t\t\t\t<button class="start-button" on:click={nextProblem}>
\t\t\t\t\t\t{lt('Next Problem', 'পরবর্তী সমস্যা')} &#8594;
\t\t\t\t\t</button>
\t\t\t\t</div>

\t\t\t\t{#if showSolution && solutionPath.length > 0}
\t\t\t\t\t<div class="solution-panel">
\t\t\t\t\t\t<h3 class="solution-title">
\t\t\t\t\t\t\t{lt(`Optimal Solution (${actualMinMoves} moves)`, `সর্বোত্তম সমাধান (${actualMinMoves} পদক্ষেপ)`)}
\t\t\t\t\t\t</h3>
\t\t\t\t\t\t<div class="solution-steps">
\t\t\t\t\t\t\t{#each solutionPath as move, index}
\t\t\t\t\t\t\t\t<div class="solution-step">
\t\t\t\t\t\t\t\t\t<span class="step-num">{index + 1}</span>
\t\t\t\t\t\t\t\t\t<div class="step-ball"
\t\t\t\t\t\t\t\t\t\tstyle="background: radial-gradient(circle at 35% 35%, rgba(255,255,255,0.45), {BALL_COLORS[move.ball]});">
\t\t\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t\t\t<span class="step-desc">
\t\t\t\t\t\t\t\t\t\t{move.ball === 0 ? lt('Red', 'লাল') : move.ball === 1 ? lt('Blue', 'নীল') : lt('Green', 'সবুজ')}
\t\t\t\t\t\t\t\t\t\t{lt(`ball: Stocking ${move.from + 1} → Stocking ${move.to + 1}`, `বল: স্টকিং ${move.from + 1} → স্টকিং ${move.to + 1}`)}
\t\t\t\t\t\t\t\t\t</span>
\t\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t\t{/each}
\t\t\t\t\t\t</div>
\t\t\t\t\t</div>
\t\t\t\t{/if}
\t\t\t</div>

\t\t{:else if gamePhase === 'results'}

\t\t\t<!-- Results Header -->
\t\t\t<div class="results-header">
\t\t\t\t<div class="score-pill">
\t\t\t\t\t<span class="score-label">{lt('Score', 'স্কোর')}</span>
\t\t\t\t\t<span class="score-value">{results.score}</span>
\t\t\t\t\t<span class="score-max">/100</span>
\t\t\t\t</div>
\t\t\t\t<p class="results-subtitle">{lt('Planning Challenge Complete', 'পরিকল্পনা চ্যালেঞ্জ সম্পন্ন')}</p>
\t\t\t</div>

\t\t\t<!-- Key Metrics -->
\t\t\t<div class="metrics-grid">
\t\t\t\t<div class="metric-card metric-blue">
\t\t\t\t\t<div class="metric-value">{results.problems_solved}/{results.total_problems}</div>
\t\t\t\t\t<div class="metric-label">{lt('Problems Solved', 'সমস্যা সমাধান')}</div>
\t\t\t\t</div>
\t\t\t\t<div class="metric-card metric-green">
\t\t\t\t\t<div class="metric-value">{results.perfect_solutions}</div>
\t\t\t\t\t<div class="metric-label">{lt('Perfect Solutions', 'নিখুঁত সমাধান')}</div>
\t\t\t\t</div>
\t\t\t\t<div class="metric-card metric-soc">
\t\t\t\t\t<div class="metric-value">{Math.round(results.planning_efficiency * 100)}%</div>
\t\t\t\t\t<div class="metric-label">{lt('Planning Efficiency', 'পরিকল্পনা দক্ষতা')}</div>
\t\t\t\t</div>
\t\t\t</div>

\t\t\t<!-- Problem Breakdown -->
\t\t\t<div class="card">
\t\t\t\t<h3 class="card-title">{lt('Problem Breakdown', 'সমস্যার বিবরণ')}</h3>
\t\t\t\t<div class="problem-list">
\t\t\t\t\t{#each results.problems as problem}
\t\t\t\t\t\t<div class="problem-row"
\t\t\t\t\t\t\tclass:row-perfect={problem.perfect}
\t\t\t\t\t\t\tclass:row-solved={!problem.perfect && problem.solved}
\t\t\t\t\t\t\tclass:row-failed={!problem.solved}>
\t\t\t\t\t\t\t<span class="problem-num">{lt(`Problem ${problem.problem_number}`, `সমস্যা ${problem.problem_number}`)}</span>
\t\t\t\t\t\t\t<div class="problem-detail">
\t\t\t\t\t\t\t\t<span>{problem.moves_used} {lt('moves', 'পদক্ষেপ')}</span>
\t\t\t\t\t\t\t\t<span class="min-label">(min: {problem.minimum_moves})</span>
\t\t\t\t\t\t\t\t{#if problem.perfect}
\t\t\t\t\t\t\t\t\t<span class="tag tag-perfect">{lt('Perfect', 'নিখুঁত')}</span>
\t\t\t\t\t\t\t\t{:else if problem.solved}
\t\t\t\t\t\t\t\t\t<span class="tag tag-solved">+{problem.moves_used - problem.minimum_moves}</span>
\t\t\t\t\t\t\t\t{:else}
\t\t\t\t\t\t\t\t\t<span class="tag tag-failed">{lt('Incomplete', 'অসম্পূর্ণ')}</span>
\t\t\t\t\t\t\t\t{/if}
\t\t\t\t\t\t\t</div>
\t\t\t\t\t\t</div>
\t\t\t\t\t{/each}
\t\t\t\t</div>
\t\t\t</div>

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

\t\t{#if gamePhase === 'intro' && !loading}
\t\t\t<button class="help-fab" on:click={() => {}}>?</button>
\t\t{/if}
\t</div>
</div>

{#if earnedBadges.length > 0}
\t<BadgeNotification badges={earnedBadges} />
{/if}

<style>
\t/* ── Page Layout ─────────────────────────────────── */
\t.soc-page {
\t\tmin-height: 100vh;
\t\tbackground: #C8DEFA;
\t\tpadding: 1.5rem;
\t}

\t.soc-wrapper {
\t\tmax-width: 1000px;
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
\t\tcolor: #2563eb;
\t\tfont-weight: 500;
\t\tmargin: 0;
\t}

\t/* ── Task Concept ─────────────────────────────────── */
\t.task-concept { margin-bottom: 1rem; }

\t.concept-badge {
\t\tdisplay: inline-flex;
\t\talign-items: center;
\t\tgap: 0.5rem;
\t\tbackground: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%);
\t\tcolor: white;
\t\tpadding: 0.4rem 0.9rem;
\t\tborder-radius: 2rem;
\t\tfont-size: 0.813rem;
\t\tfont-weight: 600;
\t\tmargin-bottom: 1rem;
\t}

\t.badge-icon {
\t\tfont-size: 0.813rem;
\t\tfont-weight: 700;
\t\tletter-spacing: 0.05em;
\t}

\t.concept-desc {
\t\tcolor: #4b5563;
\t\tfont-size: 0.938rem;
\t\tline-height: 1.6;
\t\tmargin: 0;
\t}

\t/* ── Section Title ────────────────────────────────── */
\t.section-title {
\t\tfont-size: 1.125rem;
\t\tfont-weight: 600;
\t\tcolor: #1a1a2e;
\t\tmargin: 0 0 1.25rem 0;
\t}

\t/* ── Rules Grid ───────────────────────────────────── */
\t.rules-grid {
\t\tdisplay: grid;
\t\tgrid-template-columns: 1fr 1fr;
\t\tgap: 1rem;
\t}

\t.rule-item {
\t\tdisplay: flex;
\t\talign-items: flex-start;
\t\tgap: 0.875rem;
\t\tbackground: #f9fafb;
\t\tborder-radius: 12px;
\t\tpadding: 1rem;
\t}

\t.rule-num {
\t\tmin-width: 2rem;
\t\theight: 2rem;
\t\tbackground: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%);
\t\tcolor: white;
\t\tborder-radius: 50%;
\t\tdisplay: flex;
\t\talign-items: center;
\t\tjustify-content: center;
\t\tfont-size: 0.875rem;
\t\tfont-weight: 700;
\t\tflex-shrink: 0;
\t}

\t.rule-text { display: flex; flex-direction: column; gap: 0.25rem; }
\t.rule-text strong { font-size: 0.875rem; color: #1a1a2e; }
\t.rule-text span   { font-size: 0.8rem; color: #6b7280; line-height: 1.4; }

\t/* ── Stocking Capacity Row ────────────────────────── */
\t.cap-row {
\t\tdisplay: flex;
\t\talign-items: center;
\t\tjustify-content: center;
\t\tgap: 1.5rem;
\t}

\t.cap-item { text-align: center; }

\t.cap-circle {
\t\twidth: 3.5rem;
\t\theight: 3.5rem;
\t\tborder-radius: 50%;
\t\tdisplay: flex;
\t\talign-items: center;
\t\tjustify-content: center;
\t\tfont-size: 1.5rem;
\t\tfont-weight: 700;
\t\tcolor: white;
\t\tmargin: 0 auto 0.5rem;
\t}

\t.cap-1 { background: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%); }
\t.cap-2 { background: linear-gradient(135deg, #1e40af 0%, #1d4ed8 100%); }
\t.cap-3 { background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%); }

\t.cap-label { font-size: 0.875rem; font-weight: 600; color: #374151; }
\t.cap-sub   { font-size: 0.75rem; color: #9ca3af; }

\t.cap-arrow {
\t\tfont-size: 1.5rem;
\t\tcolor: #d1d5db;
\t\tfont-weight: 700;
\t}

\t/* ── Info Grid ────────────────────────────────────── */
\t.info-grid {
\t\tdisplay: grid;
\t\tgrid-template-columns: 1fr 1fr;
\t\tgap: 1rem;
\t\tmargin-bottom: 1rem;
\t}

\t.card-title {
\t\tfont-size: 1rem;
\t\tfont-weight: 600;
\t\tcolor: #1a1a2e;
\t\tmargin: 0 0 1rem 0;
\t}

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
\t.detail-row strong { color: #1a1a2e; text-align: right; max-width: 60%; }

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

\t/* ── Performance Guide ────────────────────────────── */
\t.perf-subtitle { font-size: 0.813rem; color: #6b7280; margin: -0.5rem 0 1rem 0; }

\t.norm-bars { display: flex; flex-direction: column; gap: 0.75rem; }

\t.norm-bar {
\t\tdisplay: grid;
\t\tgrid-template-columns: 6rem 1fr 5rem;
\t\talign-items: center;
\t\tgap: 0.75rem;
\t}

\t.norm-label { font-size: 0.875rem; font-weight: 500; color: #374151; }
\t.norm-track { height: 0.5rem; background: #f3f4f6; border-radius: 0.25rem; overflow: hidden; }
\t.norm-fill  { height: 100%; border-radius: 0.25rem; }
\t.norm-excellent { width: 85%; background: #16a34a; }
\t.norm-normal    { width: 70%; background: #f59e0b; }
\t.norm-impaired  { width: 45%; background: #dc2626; }
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
\t\tmargin-bottom: 1.25rem;
\t\tflex-wrap: wrap;
\t\tgap: 0.5rem;
\t}

\t.status-pills { display: flex; gap: 0.5rem; flex-wrap: wrap; }

\t.pill {
\t\tpadding: 0.3rem 0.75rem;
\t\tborder-radius: 2rem;
\t\tfont-size: 0.8rem;
\t\tfont-weight: 500;
\t}

\t.pill-soc    { background: #dbeafe; color: #1e3a8a; }
\t.pill-phase  { background: #f3f4f6; color: #374151; }
\t.pill-moves  { background: #eff6ff; color: #1d4ed8; }
\t.pill-target { background: #fef3c7; color: #92400e; }

\t/* ── Planning Timer ───────────────────────────────── */
\t.planning-timer {
\t\tbackground: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%);
\t\tcolor: white;
\t\tpadding: 0.4rem 1.25rem;
\t\tborder-radius: 2rem;
\t\tfont-size: 1.125rem;
\t\tfont-weight: 700;
\t\tmin-width: 4rem;
\t\ttext-align: center;
\t\ttransition: background 0.3s;
\t}

\t.timer-urgent {
\t\tbackground: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
\t\tanimation: timer-pulse 0.5s ease-in-out infinite;
\t}

\t/* ── Min Moves Banner ─────────────────────────────── */
\t.min-moves-banner {
\t\tbackground: #eff6ff;
\t\tborder: 2px solid #bfdbfe;
\t\tborder-radius: 10px;
\t\tpadding: 0.75rem 1rem;
\t\ttext-align: center;
\t\tcolor: #1e3a8a;
\t\tfont-size: 0.938rem;
\t\tfont-weight: 600;
\t\tmargin-bottom: 1.25rem;
\t}

\t/* ── Towers/Stockings Layout ──────────────────────── */
\t.towers-row {
\t\tdisplay: flex;
\t\talign-items: flex-start;
\t\tgap: 1rem;
\t\tmargin-bottom: 1.5rem;
\t\tjustify-content: center;
\t}

\t.solving-row {
\t\tdisplay: flex;
\t\talign-items: flex-start;
\t\tgap: 1.5rem;
\t\tmargin-bottom: 1.5rem;
\t\tjustify-content: center;
\t}

\t.solving-single { justify-content: center; }

\t.towers-divider {
\t\tdisplay: flex;
\t\talign-items: center;
\t\tpadding-top: 3rem;
\t\tfont-size: 1.5rem;
\t\tcolor: #2563eb;
\t\tfont-weight: 700;
\t\tflex-shrink: 0;
\t}

\t.tower-panel {
\t\tflex: 1;
\t\tmin-width: 0;
\t\tmax-width: 380px;
\t}

\t.tower-panel-dim { opacity: 0.8; }

\t.tower-label {
\t\ttext-align: center;
\t\tfont-size: 0.75rem;
\t\tfont-weight: 700;
\t\tletter-spacing: 0.1em;
\t\tmargin-bottom: 1rem;
\t\tpadding: 0.3rem 1rem;
\t\tborder-radius: 2rem;
\t\tdisplay: inline-block;
\t\tmargin-left: 50%;
\t\ttransform: translateX(-50%);
\t}

\t.tower-label-start   { background: #dbeafe; color: #1e3a8a; }
\t.tower-label-goal    { background: #ede9fe; color: #4c1d95; }
\t.tower-label-current { background: #dbeafe; color: #1e3a8a; }

\t/* ── Stockings Row ────────────────────────────────── */
\t.stockings-row {
\t\tdisplay: flex;
\t\tjustify-content: center;
\t\tgap: 1.25rem;
\t}

\t/* ── Stocking Column ──────────────────────────────── */
\t.stocking-col {
\t\tdisplay: flex;
\t\tflex-direction: column;
\t\talign-items: center;
\t\tgap: 0.5rem;
\t}

\t/* ── Stocking Rim ─────────────────────────────────── */
\t.stocking-rim {
\t\twidth: 82px;
\t\theight: 22px;
\t\tbackground: linear-gradient(to bottom, #94a3b8, #64748b);
\t\tborder-radius: 10px 10px 0 0;
\t\tborder: 2px solid #475569;
\t\tborder-bottom: none;
\t\tbox-shadow: 0 -2px 4px rgba(0, 0, 0, 0.1);
\t\ttransition: border-color 0.2s, background 0.2s;
\t\tflex-shrink: 0;
\t}

\t.stocking-rim-goal {
\t\tbackground: linear-gradient(to bottom, #cbd5e1, #94a3b8);
\t\tborder-color: #94a3b8;
\t\topacity: 0.65;
\t}

\t.rim-drop {
\t\tbackground: linear-gradient(to bottom, #93c5fd, #2563eb);
\t\tborder-color: #2563eb;
\t}

\t/* ── Stocking Body ────────────────────────────────── */
\t.stocking-body {
\t\twidth: 76px;
\t\theight: 250px;
\t\tbackground: linear-gradient(160deg, #f8fafc 0%, #e2e8f0 60%, #f8fafc 100%);
\t\tborder-left:   2px solid #94a3b8;
\t\tborder-right:  2px solid #94a3b8;
\t\tborder-bottom: 2px solid #94a3b8;
\t\tborder-top: none;
\t\tborder-radius: 0 0 22px 22px;
\t\tdisplay: flex;
\t\tflex-direction: column-reverse;
\t\talign-items: center;
\t\tpadding: 8px 0;
\t\ttransition: background 0.2s, box-shadow 0.2s;
\t}

\t.stocking-body-static { cursor: default; }

\t.stocking-body-goal {
\t\tbackground: linear-gradient(160deg, #f1f5f9 0%, #e2e8f0 60%, #f1f5f9 100%);
\t\tborder-left:   2px solid #cbd5e1;
\t\tborder-right:  2px solid #cbd5e1;
\t\tborder-bottom: 2px solid #cbd5e1;
\t\topacity: 0.65;
\t}

\t.stocking-body-interactive { cursor: default; }

\t.stocking-body.drop-active {
\t\tbox-shadow: inset 0 0 0 3px #3b82f6;
\t\tbackground: #eff6ff;
\t\tcursor: pointer;
\t}

\t.stocking-body.drop-full {
\t\tbox-shadow: inset 0 0 0 3px #ef4444;
\t\tbackground: #fef2f2;
\t\tcursor: not-allowed;
\t}

\t.stocking-body.drop-warn {
\t\tbox-shadow: inset 0 0 0 3px #ef4444;
\t\tbackground: #fef2f2;
\t\tanimation: shake 0.3s ease;
\t}

\t/* ── Static Ball ──────────────────────────────────── */
\t.ball-static {
\t\twidth: 52px;
\t\theight: 52px;
\t\tborder-radius: 50%;
\t\tborder: 2px solid rgba(0, 0, 0, 0.15);
\t\tbox-shadow: 0 3px 8px rgba(0, 0, 0, 0.18),
\t\t\tinset -3px -3px 8px rgba(0, 0, 0, 0.12),
\t\t\tinset 3px 3px 8px rgba(255, 255, 255, 0.22);
\t\tmargin: 3px 0;
\t\tflex-shrink: 0;
\t}

\t.ball-static-goal { opacity: 0.75; }

\t/* ── Interactive Ball Button ──────────────────────── */
\t.ball-btn {
\t\twidth: 52px;
\t\theight: 52px;
\t\tborder-radius: 50%;
\t\tborder: 2px solid rgba(0, 0, 0, 0.15);
\t\tbox-shadow: 0 3px 8px rgba(0, 0, 0, 0.18),
\t\t\tinset -3px -3px 8px rgba(0, 0, 0, 0.12),
\t\t\tinset 3px 3px 8px rgba(255, 255, 255, 0.22);
\t\tmargin: 3px 0;
\t\tpadding: 0;
\t\tcursor: default;
\t\ttransition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
\t\tflex-shrink: 0;
\t\tposition: relative;
\t\tz-index: 2;
\t}

\t.ball-top { cursor: pointer; }

\t.ball-top:hover {
\t\tbox-shadow: 0 6px 16px rgba(0, 0, 0, 0.25),
\t\t\tinset -4px -4px 10px rgba(0, 0, 0, 0.15),
\t\t\tinset 4px 4px 10px rgba(255, 255, 255, 0.28);
\t}

\t.ball-selected {
\t\tborder: 3px solid #fbbf24 !important;
\t\tbox-shadow: 0 0 0 4px rgba(251, 191, 36, 0.35),
\t\t\t0 8px 20px rgba(0, 0, 0, 0.22),
\t\t\tinset -4px -4px 10px rgba(0, 0, 0, 0.15) !important;
\t\ttransform: translateY(-10px) !important;
\t\tcursor: pointer;
\t}

\t.ball-locked {
\t\topacity: 0.75;
\t\tcursor: not-allowed;
\t\tpointer-events: none;
\t}

\t/* ── Stocking cap labels ──────────────────────────── */
\t.stocking-cap-count {
\t\tfont-size: 0.75rem;
\t\tcolor: #6b7280;
\t\tfont-weight: 600;
\t\ttext-align: center;
\t}

\t.stocking-cap-faded { opacity: 0.5; }

\t.stocking-count-badge {
\t\tbackground: #dbeafe;
\t\tcolor: #1e40af;
\t\tpadding: 0.2rem 0.6rem;
\t\tborder-radius: 1rem;
\t\tfont-size: 0.75rem;
\t\tfont-weight: 600;
\t\tborder: 2px solid #3b82f6;
\t}

\t.count-full {
\t\tbackground: #fee2e2;
\t\tcolor: #991b1b;
\t\tborder-color: #ef4444;
\t}

\t/* ── Selected Ball Indicator ──────────────────────── */
\t.selected-indicator {
\t\tdisplay: flex;
\t\talign-items: center;
\t\tgap: 0.75rem;
\t\tbackground: #fef3c7;
\t\tborder: 2px solid #fbbf24;
\t\tborder-radius: 10px;
\t\tpadding: 0.75rem 1rem;
\t\tmargin-bottom: 1rem;
\t\tcolor: #92400e;
\t\tfont-size: 0.875rem;
\t\tfont-weight: 500;
\t}

\t.selected-swatch {
\t\twidth: 40px;
\t\theight: 40px;
\t\tborder-radius: 50%;
\t\tborder: 3px solid rgba(0, 0, 0, 0.2);
\t\tbox-shadow: 0 3px 8px rgba(0, 0, 0, 0.15), inset -3px -3px 6px rgba(0, 0, 0, 0.12);
\t\tflex-shrink: 0;
\t}

\t/* ── Stocking Full Warning ────────────────────────── */
\t.stocking-full-warning {
\t\tbackground: #fee2e2;
\t\tborder: 2px solid #fca5a5;
\t\tborder-radius: 10px;
\t\tpadding: 0.625rem 1rem;
\t\ttext-align: center;
\t\tcolor: #991b1b;
\t\tfont-size: 0.875rem;
\t\tfont-weight: 500;
\t\tmargin-bottom: 1rem;
\t\tanimation: fadeIn 0.2s ease;
\t}

\t/* ── Toggle Goal Button ───────────────────────────── */
\t.toggle-goal-btn {
\t\tbackground: #dbeafe;
\t\tcolor: #1e40af;
\t\tborder: 2px solid #93c5fd;
\t\tborder-radius: 8px;
\t\tpadding: 0.375rem 0.875rem;
\t\tfont-size: 0.875rem;
\t\tfont-weight: 600;
\t\tcursor: pointer;
\t\ttransition: background 0.15s;
\t}

\t.toggle-goal-btn:hover { background: #bfdbfe; }

\t/* ── Planning Footer ──────────────────────────────── */
\t.planning-footer {
\t\ttext-align: center;
\t\tmargin-top: 1.5rem;
\t}

\t.planning-hint {
\t\tfont-size: 0.875rem;
\t\tcolor: #6b7280;
\t\tmargin-bottom: 1rem;
\t}

\t.ready-btn {
\t\tbackground: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
\t\tcolor: white;
\t\tborder: none;
\t\tborder-radius: 12px;
\t\tpadding: 0.875rem 2.5rem;
\t\tfont-size: 1rem;
\t\tfont-weight: 600;
\t\tcursor: pointer;
\t\tbox-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
\t\ttransition: transform 0.15s;
\t}

\t.ready-btn:hover { transform: translateY(-2px); }

\t/* ── Completion Card ──────────────────────────────── */
\t.completion-card {
\t\tbackground: white;
\t\tborder-radius: 16px;
\t\tpadding: 2rem;
\t\tbox-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
\t\ttext-align: center;
\t\tmax-width: 600px;
\t\tmargin: 0 auto;
\t}

\t.completion-badge {
\t\tdisplay: inline-block;
\t\tbackground: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%);
\t\tcolor: white;
\t\tpadding: 0.4rem 1.25rem;
\t\tborder-radius: 2rem;
\t\tfont-size: 0.875rem;
\t\tfont-weight: 700;
\t\tmargin-bottom: 1rem;
\t\ttext-transform: uppercase;
\t\tletter-spacing: 0.05em;
\t}

\t.completion-title {
\t\tfont-size: 1.5rem;
\t\tfont-weight: 700;
\t\tcolor: #1a1a2e;
\t\tmargin: 0 0 1.5rem 0;
\t}

\t.completion-stats {
\t\tdisplay: flex;
\t\tjustify-content: center;
\t\tgap: 2rem;
\t\tmargin-bottom: 1.5rem;
\t}

\t.cstat { text-align: center; }

\t.cstat-val {
\t\tfont-size: 2rem;
\t\tfont-weight: 700;
\t\tcolor: #1a1a2e;
\t}

\t.cstat-perfect { color: #16a34a !important; }
\t.cstat-extra   { color: #2563eb !important; }
\t.cstat-lbl     { font-size: 0.75rem; color: #9ca3af; margin-top: 0.25rem; }

\t.completion-actions {
\t\tdisplay: flex;
\t\tgap: 1rem;
\t\tjustify-content: center;
\t\tmargin-bottom: 1.5rem;
\t}

\t/* ── Solution Panel ───────────────────────────────── */
\t.solution-panel {
\t\tbackground: #eff6ff;
\t\tborder: 2px solid #bfdbfe;
\t\tborder-radius: 12px;
\t\tpadding: 1.25rem;
\t\ttext-align: left;
\t\tmargin-top: 1rem;
\t}

\t.solution-title {
\t\tfont-size: 1rem;
\t\tfont-weight: 600;
\t\tcolor: #1e3a8a;
\t\tmargin: 0 0 1rem 0;
\t}

\t.solution-steps { display: flex; flex-direction: column; gap: 0.5rem; }

\t.solution-step {
\t\tdisplay: flex;
\t\talign-items: center;
\t\tgap: 0.75rem;
\t\tbackground: white;
\t\tborder-radius: 8px;
\t\tpadding: 0.625rem 0.875rem;
\t}

\t.step-num {
\t\tmin-width: 1.75rem;
\t\theight: 1.75rem;
\t\tbackground: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%);
\t\tcolor: white;
\t\tborder-radius: 50%;
\t\tdisplay: flex;
\t\talign-items: center;
\t\tjustify-content: center;
\t\tfont-size: 0.75rem;
\t\tfont-weight: 700;
\t\tflex-shrink: 0;
\t}

\t.step-ball {
\t\twidth: 28px;
\t\theight: 28px;
\t\tborder-radius: 50%;
\t\tborder: 2px solid rgba(0, 0, 0, 0.15);
\t\tbox-shadow: 0 2px 4px rgba(0, 0, 0, 0.15),
\t\t\tinset -2px -2px 5px rgba(0, 0, 0, 0.1),
\t\t\tinset 2px 2px 5px rgba(255, 255, 255, 0.2);
\t\tflex-shrink: 0;
\t}

\t.step-desc { font-size: 0.875rem; color: #374151; font-weight: 500; }

\t/* ── Results ──────────────────────────────────────── */
\t.results-header {
\t\tbackground: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%);
\t\tborder-radius: 16px;
\t\tpadding: 1.75rem;
\t\ttext-align: center;
\t\tmargin-bottom: 1rem;
\t\tbox-shadow: 0 4px 12px rgba(29, 78, 216, 0.35);
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
\t}

\t.metric-blue  { border-top: 4px solid #3b82f6; }
\t.metric-green { border-top: 4px solid #16a34a; }
\t.metric-soc   { border-top: 4px solid #1d4ed8; }

\t.metric-value { font-size: 1.75rem; font-weight: 700; color: #1a1a2e; }
\t.metric-label { font-size: 0.75rem; color: #6b7280; margin-top: 0.25rem; }

\t/* ── Problem List ─────────────────────────────────── */
\t.problem-list { display: flex; flex-direction: column; gap: 0.5rem; }

\t.problem-row {
\t\tdisplay: flex;
\t\tjustify-content: space-between;
\t\talign-items: center;
\t\tpadding: 0.75rem 1rem;
\t\tborder-radius: 10px;
\t\tborder-left: 4px solid #d1d5db;
\t\tbackground: #f9fafb;
\t\tfont-size: 0.875rem;
\t}

\t.row-perfect { border-left-color: #16a34a; }
\t.row-solved  { border-left-color: #3b82f6; }
\t.row-failed  { border-left-color: #ef4444; }

\t.problem-num    { font-weight: 600; color: #1a1a2e; }
\t.problem-detail { display: flex; align-items: center; gap: 0.5rem; color: #6b7280; }
\t.min-label      { color: #9ca3af; }

\t.tag {
\t\tpadding: 0.15rem 0.5rem;
\t\tborder-radius: 0.75rem;
\t\tfont-size: 0.75rem;
\t\tfont-weight: 600;
\t}

\t.tag-perfect { background: #dcfce7; color: #166534; }
\t.tag-solved  { background: #dbeafe; color: #1e40af; }
\t.tag-failed  { background: #fee2e2; color: #991b1b; }

\t/* ── Action Buttons ───────────────────────────────── */
\t.action-buttons {
\t\tdisplay: flex;
\t\tgap: 1rem;
\t\tmargin-top: 1rem;
\t}

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
\t\tflex: 1;
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

\t.btn-secondary:hover { background: #f5f3ff; transform: translateY(-2px); }

\t/* ── Help FAB ─────────────────────────────────────── */
\t.help-fab {
\t\tposition: fixed;
\t\tbottom: 2rem;
\t\tright: 2rem;
\t\twidth: 3rem;
\t\theight: 3rem;
\t\tbackground: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%);
\t\tcolor: white;
\t\tborder: none;
\t\tborder-radius: 50%;
\t\tfont-size: 1.25rem;
\t\tfont-weight: 700;
\t\tcursor: pointer;
\t\tbox-shadow: 0 4px 12px rgba(29, 78, 216, 0.4);
\t\tdisplay: flex;
\t\talign-items: center;
\t\tjustify-content: center;
\t}

\t/* ── Animations ───────────────────────────────────── */
\t@keyframes timer-pulse {
\t\t0%, 100% { transform: scale(1); }
\t\t50%       { transform: scale(1.05); }
\t}

\t@keyframes shake {
\t\t0%, 100% { transform: translateX(0); }
\t\t25%       { transform: translateX(-4px); }
\t\t75%       { transform: translateX(4px); }
\t}

\t@keyframes fadeIn {
\t\tfrom { opacity: 0; transform: translateY(-4px); }
\t\tto   { opacity: 1; transform: translateY(0); }
\t}

\t/* ── Responsive ───────────────────────────────────── */
\t@media (max-width: 640px) {
\t\t.rules-grid    { grid-template-columns: 1fr; }
\t\t.info-grid     { grid-template-columns: 1fr; }
\t\t.metrics-grid  { grid-template-columns: 1fr; }
\t\t.towers-row    { flex-direction: column; align-items: center; }
\t\t.solving-row   { flex-direction: column; align-items: center; }
\t\t.towers-divider { transform: rotate(90deg); padding: 0; }
\t\t.action-buttons { flex-direction: column; }
\t\t.completion-actions { flex-direction: column; }
\t\t.cap-row       { flex-wrap: wrap; justify-content: center; }
\t}
</style>
"""

with open(
    r'd:\NeuroBloom\frontend-svelte\src\routes\training\stockings-of-cambridge\+page.svelte',
    'w',
    encoding='utf-8'
) as f:
    f.write(CONTENT)

lines = CONTENT.count('\n') + 1
print(f'Done. Lines: {lines}')

<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { API_BASE_URL } from '$lib/api.js';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
import TaskReturnButton from '$lib/components/TaskReturnButton.svelte';
	import { locale, localeText } from '$lib/i18n';
	import { buildPracticePayload, getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
import { TASK_RETURN_CONTEXT } from '$lib/task-navigation';
	import { user } from '$lib/stores.js';
	import { onDestroy, onMount } from 'svelte';

	let userId;
	let baselineScore = 0;
	let difficulty = 1;
	let taskId = null;
	let loading = false;

	let sessionData = null;
	let currentProblemIndex = 0;
	let currentProblem = null;

	// Game state
	let currentState = [];
	let goalState = [];
	let selectedBall = null;
	let moveHistory = [];
	let problemStartTime = null;
	let totalMoves = 0;
	let stockingFullWarning = -1;
	let actualMinMoves = 0;

	// UI state
	let gamePhase = 'intro';
	let planningTimeRemaining = 0;
	let planningTimer = null;
	let warningTimeout = null;
	let userSolutions = [];
	let solutions = [];
	let showingGoal = true;
	let results = null;
	let earnedBadges = [];
	let showSolution = false;
	let solutionPath = [];
	/** @type {string} */
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';
	let recordedSessionData = null;
	let recordedDifficulty = 1;

	const BALL_COLORS = {
		0: '#ef4444',
		1: '#3b82f6',
		2: '#22c55e'
	};

	const STOCKING_CAPACITIES = [3, 2, 1];

	// BFS algorithm to find minimum moves and solution path
	function findOptimalSolution(startState, goalState) {
		const stateKey = (state) => JSON.stringify(state);
		const isGoal = (state) => stateKey(state) === stateKey(goalState);
		const queue = [{ state: startState.map(s => [...s]), moves: 0, path: [] }];
		const visited = new Set([stateKey(startState)]);

		while (queue.length > 0) {
			const { state, moves, path } = queue.shift();
			if (isGoal(state)) return { minMoves: moves, path };

			for (let from = 0; from < 3; from++) {
				if (state[from].length === 0) continue;
				for (let to = 0; to < 3; to++) {
					if (from === to) continue;
					if (state[to].length >= STOCKING_CAPACITIES[to]) continue;
					const newState = state.map(s => [...s]);
					const ball = newState[from].pop();
					newState[to].push(ball);
					const key = stateKey(newState);
					if (!visited.has(key)) {
						visited.add(key);
						queue.push({ state: newState, moves: moves + 1, path: [...path, { from, to, ball }] });
					}
				}
			}
		}
		return { minMoves: -1, path: [] };
	}

	user.subscribe(value => {
		if (value) userId = value.id;
	});

	function lt(en, bn) {
		return localeText({ en, bn }, $locale);
	}

	function cloneData(value) {
		if (typeof structuredClone === 'function') return structuredClone(value);
		return JSON.parse(JSON.stringify(value));
	}

	function restoreRecordedSession() {
		if (recordedSessionData) sessionData = cloneData(recordedSessionData);
		difficulty = recordedDifficulty;
	}

	function getDifficultyInfo() {
		if (!sessionData) return '';
		const maxMoves = Math.max(...sessionData.problems.map(p => p.minimum_moves));
		if (maxMoves <= 2) return lt('Simple 2-move problems', 'সহজ ২-পদক্ষেপের সমস্যা');
		if (maxMoves <= 3) return lt('3-move planning challenges', '৩-পদক্ষেপের পরিকল্পনা চ্যালেঞ্জ');
		if (maxMoves <= 4) return lt('4-move complex planning', '৪-পদক্ষেপের জটিল পরিকল্পনা');
		if (maxMoves <= 5) return lt('5-move advanced problems', '৫-পদক্ষেপের উন্নত সমস্যা');
		return lt('6+ move expert challenges', '৬+ পদক্ষেপের বিশেষজ্ঞ চ্যালেঞ্জ');
	}

	onMount(async () => {
		if (!userId) {
			goto('/login');
			return;
		}
		await loadSession();
	});

	async function loadSession() {
		try {
			loading = true;
			const urlDifficulty = $page.url.searchParams.get('difficulty');
			const isDevTool = $page.url.searchParams.get('taskId')?.includes('_dev');

			if (isDevTool && urlDifficulty) {
				difficulty = parseInt(urlDifficulty);
			} else {
				const baselineRes = await fetch(`/api/baseline/${userId}`);
				if (baselineRes.ok) {
					const baseline = await baselineRes.json();
					baselineScore = baseline.planning_score || 0;
					if (baselineScore >= 90) difficulty = 9;
					else if (baselineScore >= 80) difficulty = 8;
					else if (baselineScore >= 70) difficulty = 7;
					else if (baselineScore >= 60) difficulty = 6;
					else if (baselineScore >= 50) difficulty = 5;
					else if (baselineScore >= 40) difficulty = 4;
					else if (baselineScore >= 30) difficulty = 3;
					else if (baselineScore >= 20) difficulty = 2;
					else difficulty = 1;
				}
			}

			const response = await fetch('/api/tasks/soc/generate', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ difficulty })
			});

			if (response.ok) {
				sessionData = await response.json();
				difficulty = sessionData.difficulty;
				recordedSessionData = cloneData(sessionData);
				recordedDifficulty = difficulty;
			}
		} catch (_) {
			// silent
		} finally {
			loading = false;
		}
	}

	/** @param {string} nextMode */
	function startTask(nextMode = TASK_PLAY_MODE.RECORDED) {
		if (planningTimer) {
			clearInterval(planningTimer);
			planningTimer = null;
		}
		if (warningTimeout) {
			clearTimeout(warningTimeout);
			warningTimeout = null;
		}

		playMode = nextMode;
		practiceStatusMessage = '';
		restoreRecordedSession();
		if (playMode === TASK_PLAY_MODE.PRACTICE) {
			sessionData = buildPracticePayload('stockings-of-cambridge', recordedSessionData);
		}
		userSolutions = [];
		solutions = [];
		results = null;
		earnedBadges = [];
		gamePhase = 'planning';
		loadProblem(0);
	}

	function loadProblem(index) {
		currentProblemIndex = index;
		currentProblem = sessionData.problems[index];
		currentState = currentProblem.start_state.map(s => [...s]);
		goalState = currentProblem.goal_state.map(s => [...s]);

		const solution = findOptimalSolution(currentState, goalState);
		actualMinMoves = solution.minMoves;
		solutionPath = solution.path;
		currentProblem.minimum_moves = actualMinMoves;

		selectedBall = null;
		moveHistory = [];
		totalMoves = 0;
		showingGoal = true;
		showSolution = false;
		stockingFullWarning = -1;
		if (warningTimeout) {
			clearTimeout(warningTimeout);
			warningTimeout = null;
		}

		gamePhase = 'planning';
		planningTimeRemaining = sessionData.config.planning_time_seconds;
		startPlanningTimer();
	}

	function startPlanningTimer() {
		if (planningTimer) clearInterval(planningTimer);
		planningTimer = setInterval(() => {
			planningTimeRemaining--;
			if (planningTimeRemaining <= 0) {
				clearInterval(planningTimer);
				startSolving();
			}
		}, 1000);
	}

	function startSolving() {
		if (planningTimer) clearInterval(planningTimer);
		gamePhase = 'solving';
		showingGoal = false;
		problemStartTime = Date.now();
	}

	function selectBall(stockingIndex, ballIndex) {
		if (gamePhase !== 'solving') return;
		stockingFullWarning = -1;
		const stocking = currentState[stockingIndex];
		if (ballIndex !== stocking.length - 1) return;
		if (selectedBall && selectedBall.stockingIndex === stockingIndex && selectedBall.ballIndex === ballIndex) {
			selectedBall = null;
		} else {
			selectedBall = { stockingIndex, ballIndex, color: stocking[ballIndex] };
		}
	}

	function moveToStocking(targetStockingIndex) {
		if (gamePhase !== 'solving' || !selectedBall) return;
		const targetStocking = currentState[targetStockingIndex];

		if (selectedBall.stockingIndex === targetStockingIndex) {
			selectedBall = null;
			return;
		}

		if (targetStocking.length >= STOCKING_CAPACITIES[targetStockingIndex]) {
			stockingFullWarning = targetStockingIndex;
			selectedBall = null;
			if (warningTimeout) clearTimeout(warningTimeout);
			warningTimeout = setTimeout(() => {
				warningTimeout = null;
				stockingFullWarning = -1;
			}, 1800);
			return;
		}

		stockingFullWarning = -1;
		const sourceStocking = currentState[selectedBall.stockingIndex];
		const ball = sourceStocking.pop();
		targetStocking.push(ball);
		totalMoves++;
		moveHistory.push({ from: selectedBall.stockingIndex, to: targetStockingIndex, ball });
		selectedBall = null;

		if (checkSolved()) completeProblem();
		currentState = currentState.map(s => [...s]);
	}

	function checkSolved() {
		for (let i = 0; i < 3; i++) {
			if (currentState[i].length !== goalState[i].length) return false;
			for (let j = 0; j < currentState[i].length; j++) {
				if (currentState[i][j] !== goalState[i][j]) return false;
			}
		}
		return true;
	}

	function completeProblem() {
		const timeElapsed = (Date.now() - problemStartTime) / 1000;
		const problemSolution = {
			problem_number: currentProblem.problem_number,
			solved: true,
			moves_used: totalMoves,
			time_seconds: timeElapsed,
			move_history: moveHistory
		};
		userSolutions.push(problemSolution);
		solutions.push(problemSolution);
		if (currentProblemIndex < sessionData.problems.length - 1) {
			gamePhase = 'problem_complete';
		} else {
			finishSession();
		}
	}

	function nextProblem() {
		loadProblem(currentProblemIndex + 1);
	}

	async function leavePractice(completed = false) {
		if (planningTimer) {
			clearInterval(planningTimer);
			planningTimer = null;
		}
		if (warningTimeout) {
			clearTimeout(warningTimeout);
			warningTimeout = null;
		}

		playMode = TASK_PLAY_MODE.RECORDED;
		practiceStatusMessage = completed ? getPracticeCopy($locale).complete : '';
		restoreRecordedSession();
		currentProblemIndex = 0;
		currentProblem = null;
		currentState = [];
		goalState = [];
		selectedBall = null;
		moveHistory = [];
		problemStartTime = null;
		totalMoves = 0;
		stockingFullWarning = -1;
		planningTimeRemaining = 0;
		userSolutions = [];
		solutions = [];
		showingGoal = true;
		results = null;
		earnedBadges = [];
		showSolution = false;
		solutionPath = [];
		actualMinMoves = 0;
		gamePhase = 'intro';

		if (completed) {
			await loadSession();
		}
	}

	async function finishSession() {
		if (playMode === TASK_PLAY_MODE.PRACTICE) {
			await leavePractice(true);
			return;
		}
		try {
			const scoreResponse = await fetch('/api/tasks/soc/score', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ session_data: sessionData, user_solutions: userSolutions })
			});
			if (scoreResponse.ok) {
				results = await scoreResponse.json();
				await saveResults();
				gamePhase = 'results';
			}
		} catch (_) {
			// silent
		}
	}

	async function saveResults() {
		try {
			taskId = $page.url.searchParams.get('taskId');
			const response = await fetch(`${API_BASE_URL}/api/training/tasks/soc/submit/${userId}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				credentials: 'include',
				body: JSON.stringify({
					session_data: { ...sessionData, difficulty },
					user_solutions: solutions,
					task_id: taskId
				})
			});
			if (!response.ok) throw new Error('Failed to save');
			const data = await response.json();
			if (data.new_badges && data.new_badges.length > 0) {
				earnedBadges = data.new_badges;
			}
			user.update(u => ({ ...u, planning_difficulty: data.new_difficulty }));
		} catch (_) {
			// silent
		}
	}

	onDestroy(() => {
		if (planningTimer) {
			clearInterval(planningTimer);
			planningTimer = null;
		}
		if (warningTimeout) {
			clearTimeout(warningTimeout);
			warningTimeout = null;
		}
	});

	function toggleGoalView() {
		showingGoal = !showingGoal;
	}
</script>

<div class="soc-page" data-localize-skip>
	<div class="soc-wrapper">

		{#if gamePhase === 'intro'}

			<!-- Header Card -->
			<div class="header-card">
				<div class="header-content">
					<div class="header-text">
						<h1 class="task-title">{lt('Stockings of Cambridge', 'স্টকিংস অব কেমব্রিজ')}</h1>
						<p class="task-domain">{lt('Planning / Executive Function', 'পরিকল্পনা / নির্বাহী কার্যকারিতা')}</p>
					</div>
					<DifficultyBadge difficulty={sessionData?.difficulty || difficulty} domain="Executive Planning" />
				</div>
			</div>

			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
			{/if}

			{#if loading}
				<LoadingSkeleton />
			{:else}

				<!-- Task Concept -->
				<div class="card task-concept">
					<div class="concept-badge">
						<span class="badge-icon">SOC</span>
						<span>{lt('Executive Planning', 'নির্বাহী পরিকল্পনা')}</span>
					</div>
					<p class="concept-desc">
						{lt(
							'The Stockings of Cambridge is a CANTAB variant of the Tower of London. Move coloured balls between stockings to match a target arrangement in the minimum number of moves. It measures planning, working memory, and prefrontal executive function — domains frequently impaired in multiple sclerosis.',
							'স্টকিংস অব কেমব্রিজ হলো টাওয়ার অব লন্ডনের একটি CANTAB রূপ। সর্বনিম্ন পদক্ষেপে রঙিন বল রিঅ্যারেঞ্জ করে লক্ষ্য বিন্যাসের সাথে মেলাতে হয়। এটি পরিকল্পনা, ওয়ার্কিং মেমোরি এবং প্রিফ্রন্টাল নির্বাহী কার্যকারিতা পরিমাপ করে।'
						)}
					</p>
				</div>

				<!-- Rules Grid -->
				<div class="card">
					<h2 class="section-title">{lt('How to Play', 'কীভাবে খেলবেন')}</h2>
					<div class="rules-grid">
						<div class="rule-item">
							<div class="rule-num">1</div>
							<div class="rule-text">
								<strong>{lt('Study start and goal', 'শুরু এবং লক্ষ্য পর্যবেক্ষণ করুন')}</strong>
								<span>{lt('Both stocking configurations are shown during the planning phase. Memorise the goal layout.', 'পরিকল্পনা পর্যায়ে উভয় বিন্যাস দেখানো হয়। লক্ষ্য বিন্যাস মনে রাখুন।')}</span>
							</div>
						</div>
						<div class="rule-item">
							<div class="rule-num">2</div>
							<div class="rule-text">
								<strong>{lt('Plan before moving', 'চলার আগে পরিকল্পনা করুন')}</strong>
								<span>{lt('Work out the full move sequence in your head before touching any ball.', 'কোনো বল স্পর্শ করার আগে সম্পূর্ণ পদক্ষেপের ক্রম মাথায় নির্ধারণ করুন।')}</span>
							</div>
						</div>
						<div class="rule-item">
							<div class="rule-num">3</div>
							<div class="rule-text">
								<strong>{lt('Click ball, then click stocking', 'বল ক্লিক করুন তারপর স্টকিং ক্লিক করুন')}</strong>
								<span>{lt('Select the top ball in any stocking, then click the destination stocking to place it.', 'যেকোনো স্টকিংয়ের সবচেয়ে উপরের বলটি নির্বাচন করুন, তারপর গন্তব্য স্টকিংয়ে ক্লিক করুন।')}</span>
							</div>
						</div>
						<div class="rule-item">
							<div class="rule-num">4</div>
							<div class="rule-text">
								<strong>{lt('Respect capacity limits', 'ধারণক্ষমতার সীমা মানুন')}</strong>
								<span>{lt('Stocking 1 holds 3 balls, Stocking 2 holds 2, Stocking 3 holds only 1. Full stockings refuse new balls.', 'স্টকিং ১ — ৩টি, স্টকিং ২ — ২টি, স্টকিং ৩ — ১টি বল ধারণ করে। পূর্ণ স্টকিং নতুন বল গ্রহণ করে না।')}</span>
							</div>
						</div>
					</div>
				</div>

				<!-- Stocking Capacity Visual -->
				<div class="card">
					<h2 class="section-title">{lt('Stocking Capacities', 'স্টকিংয়ের ধারণক্ষমতা')}</h2>
					<div class="cap-row">
						<div class="cap-item">
							<div class="cap-circle cap-1">3</div>
							<div class="cap-label">{lt('Stocking 1', 'স্টকিং ১')}</div>
							<div class="cap-sub">{lt('3 balls max', 'সর্বোচ্চ ৩টি')}</div>
						</div>
						<div class="cap-arrow">&#8594;</div>
						<div class="cap-item">
							<div class="cap-circle cap-2">2</div>
							<div class="cap-label">{lt('Stocking 2', 'স্টকিং ২')}</div>
							<div class="cap-sub">{lt('2 balls max', 'সর্বোচ্চ ২টি')}</div>
						</div>
						<div class="cap-arrow">&#8594;</div>
						<div class="cap-item">
							<div class="cap-circle cap-3">1</div>
							<div class="cap-label">{lt('Stocking 3', 'স্টকিং ৩')}</div>
							<div class="cap-sub">{lt('1 ball max', 'সর্বোচ্চ ১টি')}</div>
						</div>
					</div>
				</div>

				<!-- Info Grid -->
				<div class="info-grid">
					<div class="card">
						<h3 class="card-title">{lt('Session Details', 'সেশনের বিবরণ')}</h3>
						<div class="details-list">
							<div class="detail-row">
								<span>{lt('Problems', 'সমস্যা')}</span>
								<strong>{sessionData ? sessionData.total_problems : '—'}</strong>
							</div>
							<div class="detail-row">
								<span>{lt('Planning Time', 'পরিকল্পনার সময়')}</span>
								<strong>{sessionData ? sessionData.config.planning_time_seconds + 's' : '—'}</strong>
							</div>
							<div class="detail-row">
								<span>{lt('Difficulty', 'কঠিনতা')}</span>
								<strong>{lt(`Level ${difficulty} / 10`, `লেভেল ${difficulty} / ১০`)}</strong>
							</div>
							<div class="detail-row">
								<span>{lt('Problem Type', 'সমস্যার ধরন')}</span>
								<strong>{getDifficultyInfo()}</strong>
							</div>
							{#if baselineScore > 0}
								<div class="detail-row">
									<span>{lt('Planning Baseline', 'পরিকল্পনা বেসলাইন')}</span>
									<strong>{baselineScore}/100</strong>
								</div>
							{/if}
						</div>
					</div>
					<div class="card">
						<h3 class="card-title">{lt('What It Measures', 'এটি কী পরিমাপ করে')}</h3>
						<div class="details-list">
							<div class="detail-row">
								<span>{lt('Primary Metric', 'প্রাথমিক মেট্রিক')}</span>
								<strong>{lt('Planning efficiency', 'পরিকল্পনা দক্ষতা')}</strong>
							</div>
							<div class="detail-row">
								<span>{lt('Cognitive Domain', 'জ্ঞানীয় ডোমেইন')}</span>
								<strong>{lt('Executive function', 'নির্বাহী কার্যকারিতা')}</strong>
							</div>
							<div class="detail-row">
								<span>{lt('Scoring Basis', 'স্কোরিং ভিত্তি')}</span>
								<strong>{lt('Moves used vs minimum', 'ব্যবহৃত বনাম সর্বনিম্ন')}</strong>
							</div>
							<div class="detail-row">
								<span>{lt('Test Battery', 'পরীক্ষার ব্যাটারি')}</span>
								<strong>CANTAB</strong>
							</div>
						</div>
					</div>
				</div>

				<!-- Clinical Info -->
				<div class="clinical-info">
					<div class="clinical-header">
						<div class="clinical-badge">{lt('Clinical Basis', 'ক্লিনিকাল ভিত্তি')}</div>
						<h3>{lt('CANTAB Gold Standard Planning Test', 'CANTAB গোল্ড স্ট্যান্ডার্ড পরিকল্পনা পরীক্ষা')}</h3>
					</div>
					<p>
						{lt(
							'Owen et al. (1990) introduced the Stockings of Cambridge as the CANTAB computerised version of the Tower of London. MS patients show significantly more excess moves and longer thinking times, with performance correlating with lesion load in frontal and parietal white matter. The task is included in the BICAMS cognitive battery for MS.',
							'ওয়েন et al. (১৯৯০) টাওয়ার অব লন্ডনের CANTAB কম্পিউটারাইজড সংস্করণ হিসেবে স্টকিংস অব কেমব্রিজ প্রবর্তন করেন। এমএস রোগীরা উল্লেখযোগ্যভাবে বেশি অতিরিক্ত পদক্ষেপ করেন। পারফরম্যান্স ফ্রন্টাল এবং প্যারিটাল সাদা পদার্থে লেশন লোডের সাথে সম্পর্কিত।'
						)}
					</p>
				</div>

				<!-- Performance Guide -->
				<div class="card perf-guide">
					<h3 class="card-title">{lt('Planning Efficiency Norms', 'পরিকল্পনা দক্ষতার নির্দেশিকা')}</h3>
					<p class="perf-subtitle">{lt('Minimum moves / moves used (higher = better)', 'সর্বনিম্ন পদক্ষেপ / ব্যবহৃত পদক্ষেপ (বেশি = ভালো)')}</p>
					<div class="norm-bars">
						<div class="norm-bar">
							<div class="norm-label">{lt('Excellent', 'উৎকৃষ্ট')}</div>
							<div class="norm-track"><div class="norm-fill norm-excellent"></div></div>
							<div class="norm-range">&gt; 80%</div>
						</div>
						<div class="norm-bar">
							<div class="norm-label">{lt('Normal', 'স্বাভাবিক')}</div>
							<div class="norm-track"><div class="norm-fill norm-normal"></div></div>
							<div class="norm-range">60–80%</div>
						</div>
						<div class="norm-bar">
							<div class="norm-label">{lt('Impaired', 'দুর্বল')}</div>
							<div class="norm-track"><div class="norm-fill norm-impaired"></div></div>
							<div class="norm-range">&lt; 60%</div>
						</div>
					</div>
				</div>

				<TaskPracticeActions
					locale={$locale}
					startLabel={lt('Start Planning Challenge', 'পরিকল্পনা চ্যালেঞ্জ শুরু করুন')}
					statusMessage={practiceStatusMessage}
					on:start={() => startTask(TASK_PLAY_MODE.RECORDED)}
					on:practice={() => startTask(TASK_PLAY_MODE.PRACTICE)}
				/>

			{/if}

		{:else if gamePhase === 'planning'}

			<div class="game-card">
				{#if playMode === TASK_PLAY_MODE.PRACTICE}
					<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
				{/if}

				<!-- Status Bar -->
				<div class="game-status-bar">
					<div class="status-pills">
						<span class="pill pill-soc">{lt(`Problem ${currentProblem.problem_number} / ${sessionData.total_problems}`, `সমস্যা ${currentProblem.problem_number} / ${sessionData.total_problems}`)}</span>
						<span class="pill pill-phase">{lt('Planning', 'পরিকল্পনা')}</span>
					</div>
					<div class="planning-timer" class:timer-urgent={planningTimeRemaining <= 5}>
						{planningTimeRemaining}s
					</div>
				</div>

				{#if currentProblem.show_minimum}
					<div class="min-moves-banner">
						{lt(`Minimum moves required: ${currentProblem.minimum_moves}`, `প্রয়োজনীয় সর্বনিম্ন পদক্ষেপ: ${currentProblem.minimum_moves}`)}
					</div>
				{/if}

				<!-- Stockings side by side: START vs GOAL -->
				<div class="towers-row">
					<div class="tower-panel">
						<div class="tower-label tower-label-start">{lt('START', 'শুরু')}</div>
						<div class="stockings-row">
							{#each currentProblem.start_state as stocking, stockingIndex}
								<div class="stocking-col">
									<div class="stocking-rim"></div>
									<div class="stocking-body stocking-body-static">
										{#each stocking as ballColor}
											<div class="ball-static"
												style="background: radial-gradient(circle at 35% 35%, rgba(255,255,255,0.45), {BALL_COLORS[ballColor]});">
											</div>
										{/each}
									</div>
									<div class="stocking-cap-count">{STOCKING_CAPACITIES[stockingIndex]}</div>
								</div>
							{/each}
						</div>
					</div>

					<div class="towers-divider">&#8594;</div>

					<div class="tower-panel">
						<div class="tower-label tower-label-goal">{lt('GOAL', 'লক্ষ্য')}</div>
						<div class="stockings-row">
							{#each currentProblem.goal_state as stocking, stockingIndex}
								<div class="stocking-col">
									<div class="stocking-rim stocking-rim-goal"></div>
									<div class="stocking-body stocking-body-static stocking-body-goal">
										{#each stocking as ballColor}
											<div class="ball-static ball-static-goal"
												style="background: radial-gradient(circle at 35% 35%, rgba(255,255,255,0.3), {BALL_COLORS[ballColor]});">
											</div>
										{/each}
									</div>
									<div class="stocking-cap-count stocking-cap-faded">{STOCKING_CAPACITIES[stockingIndex]}</div>
								</div>
							{/each}
						</div>
					</div>
				</div>

				<div class="planning-footer">
					<p class="planning-hint">
						{lt('Study both configurations and plan your ball sequence before the timer runs out.', 'টাইমার শেষ হওয়ার আগে উভয় বিন্যাস পর্যবেক্ষণ করুন এবং আপনার বলের ক্রম পরিকল্পনা করুন।')}
					</p>
					<button class="ready-btn" on:click={startSolving}>
						{lt('Ready — Start Solving', 'প্রস্তুত — সমাধান শুরু করুন')}
					</button>
				</div>
			</div>

		{:else if gamePhase === 'solving'}

			<div class="game-card">
				{#if playMode === TASK_PLAY_MODE.PRACTICE}
					<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
				{/if}

				<!-- Solving Status Bar -->
				<div class="game-status-bar">
					<div class="status-pills">
						<span class="pill pill-soc">{lt(`Problem ${currentProblem.problem_number} / ${sessionData.total_problems}`, `সমস্যা ${currentProblem.problem_number} / ${sessionData.total_problems}`)}</span>
						<span class="pill pill-moves">{lt(`Moves: ${totalMoves}`, `পদক্ষেপ: ${totalMoves}`)}</span>
						{#if currentProblem.show_minimum}
							<span class="pill pill-target">{lt(`Min: ${currentProblem.minimum_moves}`, `সর্বনিম্ন: ${currentProblem.minimum_moves}`)}</span>
						{/if}
					</div>
					<button class="toggle-goal-btn" on:click={toggleGoalView}>
						{showingGoal ? lt('Hide Goal', 'লক্ষ্য লুকান') : lt('Show Goal', 'লক্ষ্য দেখান')}
					</button>
				</div>

				<!-- Selected ball indicator -->
				{#if selectedBall !== null}
					<div class="selected-indicator">
						<div class="selected-swatch"
							style="background: radial-gradient(circle at 35% 35%, rgba(255,255,255,0.45), {BALL_COLORS[selectedBall.color]});">
						</div>
						<span>{lt('Ball selected — click any stocking to move it', 'বল নির্বাচিত — এটি সরাতে যেকোনো স্টকিংয়ে ক্লিক করুন')}</span>
					</div>
				{/if}

				<!-- Stocking full warning -->
				{#if stockingFullWarning >= 0}
					<div class="stocking-full-warning">
						{lt(`Stocking ${stockingFullWarning + 1} is full (max ${STOCKING_CAPACITIES[stockingFullWarning]} balls)`, `স্টকিং ${stockingFullWarning + 1} পূর্ণ (সর্বোচ্চ ${STOCKING_CAPACITIES[stockingFullWarning]} বল)`)}
					</div>
				{/if}

				<!-- Solving Layout -->
				<div class="solving-row" class:solving-single={!showingGoal}>

					<!-- Interactive current state -->
					<div class="tower-panel">
						<div class="tower-label tower-label-current">{lt('CURRENT POSITION', 'বর্তমান অবস্থান')}</div>
						<div class="stockings-row">
							{#each currentState as stocking, stockingIndex}
								{@const isFull = stocking.length >= STOCKING_CAPACITIES[stockingIndex]}
								<div class="stocking-col">
									<div class="stocking-rim"
										class:rim-drop={selectedBall && selectedBall.stockingIndex !== stockingIndex && !isFull}>
									</div>
									<div class="stocking-body stocking-body-interactive"
										class:drop-active={selectedBall && selectedBall.stockingIndex !== stockingIndex && !isFull}
										class:drop-full={selectedBall && selectedBall.stockingIndex !== stockingIndex && isFull}
										class:drop-warn={stockingFullWarning === stockingIndex}
										role="button"
										tabindex="0"
										aria-label="Move ball to stocking {stockingIndex + 1}"
										on:click={() => moveToStocking(stockingIndex)}
										on:keydown={(e) => e.key === 'Enter' && moveToStocking(stockingIndex)}>
										{#each stocking as ballColor, ballIndex}
											{@const isTopBall = ballIndex === stocking.length - 1}
											{@const isSelected = selectedBall && selectedBall.stockingIndex === stockingIndex && selectedBall.ballIndex === ballIndex}
											<button
												on:click|stopPropagation={() => selectBall(stockingIndex, ballIndex)}
												disabled={!isTopBall}
												class="ball-btn"
												class:ball-selected={isSelected}
												class:ball-top={isTopBall && !isSelected}
												class:ball-locked={!isTopBall}
												aria-label="{isTopBall ? 'Select' : 'Cannot select'} ball in stocking {stockingIndex + 1}"
												style="background: radial-gradient(circle at 35% 35%, rgba(255,255,255,0.5), {BALL_COLORS[ballColor]});">
											</button>
										{/each}
									</div>
									<div class="stocking-count-badge" class:count-full={isFull}>
										{stocking.length}/{STOCKING_CAPACITIES[stockingIndex]}
									</div>
								</div>
							{/each}
						</div>
					</div>

					<!-- Goal reference -->
					{#if showingGoal}
						<div class="tower-panel tower-panel-dim">
							<div class="tower-label tower-label-goal">{lt('TARGET', 'লক্ষ্য')}</div>
							<div class="stockings-row">
								{#each goalState as stocking, stockingIndex}
									<div class="stocking-col">
										<div class="stocking-rim stocking-rim-goal"></div>
										<div class="stocking-body stocking-body-static stocking-body-goal">
											{#each stocking as ballColor}
												<div class="ball-static ball-static-goal"
													style="background: radial-gradient(circle at 35% 35%, rgba(255,255,255,0.3), {BALL_COLORS[ballColor]});">
												</div>
											{/each}
										</div>
										<div class="stocking-cap-count stocking-cap-faded">{STOCKING_CAPACITIES[stockingIndex]}</div>
									</div>
								{/each}
							</div>
						</div>
					{/if}

				</div>
			</div>

		{:else if gamePhase === 'problem_complete'}

			<div class="completion-card">
				{#if playMode === TASK_PLAY_MODE.PRACTICE}
					<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
				{/if}

				<div class="completion-badge">{lt('Problem Solved', 'সমস্যা সমাধান হয়েছে')}</div>
				<h2 class="completion-title">{lt('Well done!', 'চমৎকার!')}</h2>

				<div class="completion-stats">
					<div class="cstat">
						<div class="cstat-val">{userSolutions[userSolutions.length - 1].moves_used}</div>
						<div class="cstat-lbl">{lt('Moves used', 'ব্যবহৃত পদক্ষেপ')}</div>
					</div>
					{#if currentProblem.show_minimum}
						<div class="cstat">
							<div class="cstat-val">{actualMinMoves}</div>
							<div class="cstat-lbl">{lt('Minimum', 'সর্বনিম্ন')}</div>
						</div>
						<div class="cstat">
							<div class="cstat-val"
								class:cstat-perfect={userSolutions[userSolutions.length - 1].moves_used === actualMinMoves}
								class:cstat-extra={userSolutions[userSolutions.length - 1].moves_used !== actualMinMoves}>
								{userSolutions[userSolutions.length - 1].moves_used === actualMinMoves
									? lt('Perfect', 'নিখুঁত')
									: '+' + (userSolutions[userSolutions.length - 1].moves_used - actualMinMoves)}
							</div>
							<div class="cstat-lbl">{lt('Extra moves', 'অতিরিক্ত পদক্ষেপ')}</div>
						</div>
					{/if}
				</div>

				<div class="completion-actions">
					{#if !showSolution}
						<button class="btn-secondary" on:click={() => showSolution = true}>
							{lt('Show Optimal Solution', 'সর্বোত্তম সমাধান দেখুন')}
						</button>
					{/if}
					<button class="start-button" on:click={nextProblem}>
						{lt('Next Problem', 'পরবর্তী সমস্যা')} &#8594;
					</button>
				</div>

				{#if showSolution && solutionPath.length > 0}
					<div class="solution-panel">
						<h3 class="solution-title">
							{lt(`Optimal Solution (${actualMinMoves} moves)`, `সর্বোত্তম সমাধান (${actualMinMoves} পদক্ষেপ)`)}
						</h3>
						<div class="solution-steps">
							{#each solutionPath as move, index}
								<div class="solution-step">
									<span class="step-num">{index + 1}</span>
									<div class="step-ball"
										style="background: radial-gradient(circle at 35% 35%, rgba(255,255,255,0.45), {BALL_COLORS[move.ball]});">
									</div>
									<span class="step-desc">
										{move.ball === 0 ? lt('Red', 'লাল') : move.ball === 1 ? lt('Blue', 'নীল') : lt('Green', 'সবুজ')}
										{lt(`ball: Stocking ${move.from + 1} → Stocking ${move.to + 1}`, `বল: স্টকিং ${move.from + 1} → স্টকিং ${move.to + 1}`)}
									</span>
								</div>
							{/each}
						</div>
					</div>
				{/if}
			</div>

		{:else if gamePhase === 'results'}
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />

			<!-- Results Header -->
			<div class="results-header">
				<div class="score-pill">
					<span class="score-label">{lt('Score', 'স্কোর')}</span>
					<span class="score-value">{results.score}</span>
					<span class="score-max">/100</span>
				</div>
				<p class="results-subtitle">{lt('Planning Challenge Complete', 'পরিকল্পনা চ্যালেঞ্জ সম্পন্ন')}</p>
			</div>

			<!-- Key Metrics -->
			<div class="metrics-grid">
				<div class="metric-card metric-blue">
					<div class="metric-value">{results.problems_solved}/{results.total_problems}</div>
					<div class="metric-label">{lt('Problems Solved', 'সমস্যা সমাধান')}</div>
				</div>
				<div class="metric-card metric-green">
					<div class="metric-value">{results.perfect_solutions}</div>
					<div class="metric-label">{lt('Perfect Solutions', 'নিখুঁত সমাধান')}</div>
				</div>
				<div class="metric-card metric-soc">
					<div class="metric-value">{Math.round(results.planning_efficiency * 100)}%</div>
					<div class="metric-label">{lt('Planning Efficiency', 'পরিকল্পনা দক্ষতা')}</div>
				</div>
			</div>

			<!-- Problem Breakdown -->
			<div class="card">
				<h3 class="card-title">{lt('Problem Breakdown', 'সমস্যার বিবরণ')}</h3>
				<div class="problem-list">
					{#each results.problems as problem}
						<div class="problem-row"
							class:row-perfect={problem.perfect}
							class:row-solved={!problem.perfect && problem.solved}
							class:row-failed={!problem.solved}>
							<span class="problem-num">{lt(`Problem ${problem.problem_number}`, `সমস্যা ${problem.problem_number}`)}</span>
							<div class="problem-detail">
								<span>{problem.moves_used} {lt('moves', 'পদক্ষেপ')}</span>
								<span class="min-label">(min: {problem.minimum_moves})</span>
								{#if problem.perfect}
									<span class="tag tag-perfect">{lt('Perfect', 'নিখুঁত')}</span>
								{:else if problem.solved}
									<span class="tag tag-solved">+{problem.moves_used - problem.minimum_moves}</span>
								{:else}
									<span class="tag tag-failed">{lt('Incomplete', 'অসম্পূর্ণ')}</span>
								{/if}
							</div>
						</div>
					{/each}
				</div>
			</div>

			<!-- Action Buttons -->
			<div class="action-buttons">
				<button class="start-button" on:click={() => goto('/dashboard')}>
					{lt('Return to Dashboard', 'ড্যাশবোর্ডে ফিরুন')}
				</button>
				<button class="btn-secondary" on:click={() => goto('/training')}>
					{lt('Next Task', 'পরবর্তী টাস্ক')}
				</button>
			</div>

		{/if}

		{#if gamePhase === 'intro' && !loading}
			<button class="help-fab" on:click={() => {}}>?</button>
		{/if}
	</div>
</div>

{#if earnedBadges.length > 0}
	<BadgeNotification badges={earnedBadges} />
{/if}

<style>
	/* ── Page Layout ─────────────────────────────────── */
	.soc-page {
		min-height: 100vh;
		background: #C8DEFA;
		padding: 1.5rem;
	}

	.soc-wrapper {
		max-width: 1000px;
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
		color: #2563eb;
		font-weight: 500;
		margin: 0;
	}

	/* ── Task Concept ─────────────────────────────────── */
	.task-concept { margin-bottom: 1rem; }

	.concept-badge {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		background: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%);
		color: white;
		padding: 0.4rem 0.9rem;
		border-radius: 2rem;
		font-size: 0.813rem;
		font-weight: 600;
		margin-bottom: 1rem;
	}

	.badge-icon {
		font-size: 0.813rem;
		font-weight: 700;
		letter-spacing: 0.05em;
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
		background: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%);
		color: white;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.875rem;
		font-weight: 700;
		flex-shrink: 0;
	}

	.rule-text { display: flex; flex-direction: column; gap: 0.25rem; }
	.rule-text strong { font-size: 0.875rem; color: #1a1a2e; }
	.rule-text span   { font-size: 0.8rem; color: #6b7280; line-height: 1.4; }

	/* ── Stocking Capacity Row ────────────────────────── */
	.cap-row {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1.5rem;
	}

	.cap-item { text-align: center; }

	.cap-circle {
		width: 3.5rem;
		height: 3.5rem;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.5rem;
		font-weight: 700;
		color: white;
		margin: 0 auto 0.5rem;
	}

	.cap-1 { background: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%); }
	.cap-2 { background: linear-gradient(135deg, #1e40af 0%, #1d4ed8 100%); }
	.cap-3 { background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%); }

	.cap-label { font-size: 0.875rem; font-weight: 600; color: #374151; }
	.cap-sub   { font-size: 0.75rem; color: #9ca3af; }

	.cap-arrow {
		font-size: 1.5rem;
		color: #d1d5db;
		font-weight: 700;
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

	.clinical-header h3 { font-size: 1rem; font-weight: 600; color: #14532d; margin: 0; }
	.clinical-info p    { font-size: 0.875rem; color: #166534; line-height: 1.6; margin: 0; }

	/* ── Performance Guide ────────────────────────────── */
	.perf-subtitle { font-size: 0.813rem; color: #6b7280; margin: -0.5rem 0 1rem 0; }

	.norm-bars { display: flex; flex-direction: column; gap: 0.75rem; }

	.norm-bar {
		display: grid;
		grid-template-columns: 6rem 1fr 5rem;
		align-items: center;
		gap: 0.75rem;
	}

	.norm-label { font-size: 0.875rem; font-weight: 500; color: #374151; }
	.norm-track { height: 0.5rem; background: #f3f4f6; border-radius: 0.25rem; overflow: hidden; }
	.norm-fill  { height: 100%; border-radius: 0.25rem; }
	.norm-excellent { width: 85%; background: #16a34a; }
	.norm-normal    { width: 70%; background: #f59e0b; }
	.norm-impaired  { width: 45%; background: #dc2626; }
	.norm-range { font-size: 0.75rem; color: #6b7280; text-align: right; }

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
		margin-bottom: 1.25rem;
		flex-wrap: wrap;
		gap: 0.5rem;
	}

	.status-pills { display: flex; gap: 0.5rem; flex-wrap: wrap; }

	.pill {
		padding: 0.3rem 0.75rem;
		border-radius: 2rem;
		font-size: 0.8rem;
		font-weight: 500;
	}

	.pill-soc    { background: #dbeafe; color: #1e3a8a; }
	.pill-phase  { background: #f3f4f6; color: #374151; }
	.pill-moves  { background: #eff6ff; color: #1d4ed8; }
	.pill-target { background: #fef3c7; color: #92400e; }

	/* ── Planning Timer ───────────────────────────────── */
	.planning-timer {
		background: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%);
		color: white;
		padding: 0.4rem 1.25rem;
		border-radius: 2rem;
		font-size: 1.125rem;
		font-weight: 700;
		min-width: 4rem;
		text-align: center;
		transition: background 0.3s;
	}

	.timer-urgent {
		background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
		animation: timer-pulse 0.5s ease-in-out infinite;
	}

	/* ── Min Moves Banner ─────────────────────────────── */
	.min-moves-banner {
		background: #eff6ff;
		border: 2px solid #bfdbfe;
		border-radius: 10px;
		padding: 0.75rem 1rem;
		text-align: center;
		color: #1e3a8a;
		font-size: 0.938rem;
		font-weight: 600;
		margin-bottom: 1.25rem;
	}

	/* ── Towers/Stockings Layout ──────────────────────── */
	.towers-row {
		display: flex;
		align-items: flex-start;
		gap: 1rem;
		margin-bottom: 1.5rem;
		justify-content: center;
	}

	.solving-row {
		display: flex;
		align-items: flex-start;
		gap: 1.5rem;
		margin-bottom: 1.5rem;
		justify-content: center;
	}

	.solving-single { justify-content: center; }

	.towers-divider {
		display: flex;
		align-items: center;
		padding-top: 3rem;
		font-size: 1.5rem;
		color: #2563eb;
		font-weight: 700;
		flex-shrink: 0;
	}

	.tower-panel {
		flex: 1;
		min-width: 0;
		max-width: 380px;
	}

	.tower-panel-dim { opacity: 0.8; }

	.tower-label {
		text-align: center;
		font-size: 0.75rem;
		font-weight: 700;
		letter-spacing: 0.1em;
		margin-bottom: 1rem;
		padding: 0.3rem 1rem;
		border-radius: 2rem;
		display: inline-block;
		margin-left: 50%;
		transform: translateX(-50%);
	}

	.tower-label-start   { background: #dbeafe; color: #1e3a8a; }
	.tower-label-goal    { background: #ede9fe; color: #4c1d95; }
	.tower-label-current { background: #dbeafe; color: #1e3a8a; }

	/* ── Stockings Row ────────────────────────────────── */
	.stockings-row {
		display: flex;
		justify-content: center;
		gap: 1.25rem;
	}

	/* ── Stocking Column ──────────────────────────────── */
	.stocking-col {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}

	/* ── Stocking Rim ─────────────────────────────────── */
	.stocking-rim {
		width: 82px;
		height: 22px;
		background: linear-gradient(to bottom, #94a3b8, #64748b);
		border-radius: 10px 10px 0 0;
		border: 2px solid #475569;
		border-bottom: none;
		box-shadow: 0 -2px 4px rgba(0, 0, 0, 0.1);
		transition: border-color 0.2s, background 0.2s;
		flex-shrink: 0;
	}

	.stocking-rim-goal {
		background: linear-gradient(to bottom, #cbd5e1, #94a3b8);
		border-color: #94a3b8;
		opacity: 0.65;
	}

	.rim-drop {
		background: linear-gradient(to bottom, #93c5fd, #2563eb);
		border-color: #2563eb;
	}

	/* ── Stocking Body ────────────────────────────────── */
	.stocking-body {
		width: 76px;
		height: 250px;
		background: linear-gradient(160deg, #f8fafc 0%, #e2e8f0 60%, #f8fafc 100%);
		border-left:   2px solid #94a3b8;
		border-right:  2px solid #94a3b8;
		border-bottom: 2px solid #94a3b8;
		border-top: none;
		border-radius: 0 0 22px 22px;
		display: flex;
		flex-direction: column-reverse;
		align-items: center;
		padding: 8px 0;
		transition: background 0.2s, box-shadow 0.2s;
	}

	.stocking-body-static { cursor: default; }

	.stocking-body-goal {
		background: linear-gradient(160deg, #f1f5f9 0%, #e2e8f0 60%, #f1f5f9 100%);
		border-left:   2px solid #cbd5e1;
		border-right:  2px solid #cbd5e1;
		border-bottom: 2px solid #cbd5e1;
		opacity: 0.65;
	}

	.stocking-body-interactive { cursor: default; }

	.stocking-body.drop-active {
		box-shadow: inset 0 0 0 3px #3b82f6;
		background: #eff6ff;
		cursor: pointer;
	}

	.stocking-body.drop-full {
		box-shadow: inset 0 0 0 3px #ef4444;
		background: #fef2f2;
		cursor: not-allowed;
	}

	.stocking-body.drop-warn {
		box-shadow: inset 0 0 0 3px #ef4444;
		background: #fef2f2;
		animation: shake 0.3s ease;
	}

	/* ── Static Ball ──────────────────────────────────── */
	.ball-static {
		width: 52px;
		height: 52px;
		border-radius: 50%;
		border: 2px solid rgba(0, 0, 0, 0.15);
		box-shadow: 0 3px 8px rgba(0, 0, 0, 0.18),
			inset -3px -3px 8px rgba(0, 0, 0, 0.12),
			inset 3px 3px 8px rgba(255, 255, 255, 0.22);
		margin: 3px 0;
		flex-shrink: 0;
	}

	.ball-static-goal { opacity: 0.75; }

	/* ── Interactive Ball Button ──────────────────────── */
	.ball-btn {
		width: 52px;
		height: 52px;
		border-radius: 50%;
		border: 2px solid rgba(0, 0, 0, 0.15);
		box-shadow: 0 3px 8px rgba(0, 0, 0, 0.18),
			inset -3px -3px 8px rgba(0, 0, 0, 0.12),
			inset 3px 3px 8px rgba(255, 255, 255, 0.22);
		margin: 3px 0;
		padding: 0;
		cursor: default;
		transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
		flex-shrink: 0;
		position: relative;
		z-index: 2;
	}

	.ball-top { cursor: pointer; }

	.ball-top:hover {
		box-shadow: 0 6px 16px rgba(0, 0, 0, 0.25),
			inset -4px -4px 10px rgba(0, 0, 0, 0.15),
			inset 4px 4px 10px rgba(255, 255, 255, 0.28);
	}

	.ball-selected {
		border: 3px solid #fbbf24 !important;
		box-shadow: 0 0 0 4px rgba(251, 191, 36, 0.35),
			0 8px 20px rgba(0, 0, 0, 0.22),
			inset -4px -4px 10px rgba(0, 0, 0, 0.15) !important;
		transform: translateY(-10px) !important;
		cursor: pointer;
	}

	.ball-locked {
		opacity: 0.75;
		cursor: not-allowed;
		pointer-events: none;
	}

	/* ── Stocking cap labels ──────────────────────────── */
	.stocking-cap-count {
		font-size: 0.75rem;
		color: #6b7280;
		font-weight: 600;
		text-align: center;
	}

	.stocking-cap-faded { opacity: 0.5; }

	.stocking-count-badge {
		background: #dbeafe;
		color: #1e40af;
		padding: 0.2rem 0.6rem;
		border-radius: 1rem;
		font-size: 0.75rem;
		font-weight: 600;
		border: 2px solid #3b82f6;
	}

	.count-full {
		background: #fee2e2;
		color: #991b1b;
		border-color: #ef4444;
	}

	/* ── Selected Ball Indicator ──────────────────────── */
	.selected-indicator {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		background: #fef3c7;
		border: 2px solid #fbbf24;
		border-radius: 10px;
		padding: 0.75rem 1rem;
		margin-bottom: 1rem;
		color: #92400e;
		font-size: 0.875rem;
		font-weight: 500;
	}

	.selected-swatch {
		width: 40px;
		height: 40px;
		border-radius: 50%;
		border: 3px solid rgba(0, 0, 0, 0.2);
		box-shadow: 0 3px 8px rgba(0, 0, 0, 0.15), inset -3px -3px 6px rgba(0, 0, 0, 0.12);
		flex-shrink: 0;
	}

	/* ── Stocking Full Warning ────────────────────────── */
	.stocking-full-warning {
		background: #fee2e2;
		border: 2px solid #fca5a5;
		border-radius: 10px;
		padding: 0.625rem 1rem;
		text-align: center;
		color: #991b1b;
		font-size: 0.875rem;
		font-weight: 500;
		margin-bottom: 1rem;
		animation: fadeIn 0.2s ease;
	}

	/* ── Toggle Goal Button ───────────────────────────── */
	.toggle-goal-btn {
		background: #dbeafe;
		color: #1e40af;
		border: 2px solid #93c5fd;
		border-radius: 8px;
		padding: 0.375rem 0.875rem;
		font-size: 0.875rem;
		font-weight: 600;
		cursor: pointer;
		transition: background 0.15s;
	}

	.toggle-goal-btn:hover { background: #bfdbfe; }

	/* ── Planning Footer ──────────────────────────────── */
	.planning-footer {
		text-align: center;
		margin-top: 1.5rem;
	}

	.planning-hint {
		font-size: 0.875rem;
		color: #6b7280;
		margin-bottom: 1rem;
	}

	.ready-btn {
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

	.ready-btn:hover { transform: translateY(-2px); }

	/* ── Completion Card ──────────────────────────────── */
	.completion-card {
		background: white;
		border-radius: 16px;
		padding: 2rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
		text-align: center;
		max-width: 600px;
		margin: 0 auto;
	}

	.completion-badge {
		display: inline-block;
		background: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%);
		color: white;
		padding: 0.4rem 1.25rem;
		border-radius: 2rem;
		font-size: 0.875rem;
		font-weight: 700;
		margin-bottom: 1rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.completion-title {
		font-size: 1.5rem;
		font-weight: 700;
		color: #1a1a2e;
		margin: 0 0 1.5rem 0;
	}

	.completion-stats {
		display: flex;
		justify-content: center;
		gap: 2rem;
		margin-bottom: 1.5rem;
	}

	.cstat { text-align: center; }

	.cstat-val {
		font-size: 2rem;
		font-weight: 700;
		color: #1a1a2e;
	}

	.cstat-perfect { color: #16a34a !important; }
	.cstat-extra   { color: #2563eb !important; }
	.cstat-lbl     { font-size: 0.75rem; color: #9ca3af; margin-top: 0.25rem; }

	.completion-actions {
		display: flex;
		gap: 1rem;
		justify-content: center;
		margin-bottom: 1.5rem;
	}

	/* ── Solution Panel ───────────────────────────────── */
	.solution-panel {
		background: #eff6ff;
		border: 2px solid #bfdbfe;
		border-radius: 12px;
		padding: 1.25rem;
		text-align: left;
		margin-top: 1rem;
	}

	.solution-title {
		font-size: 1rem;
		font-weight: 600;
		color: #1e3a8a;
		margin: 0 0 1rem 0;
	}

	.solution-steps { display: flex; flex-direction: column; gap: 0.5rem; }

	.solution-step {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		background: white;
		border-radius: 8px;
		padding: 0.625rem 0.875rem;
	}

	.step-num {
		min-width: 1.75rem;
		height: 1.75rem;
		background: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%);
		color: white;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.75rem;
		font-weight: 700;
		flex-shrink: 0;
	}

	.step-ball {
		width: 28px;
		height: 28px;
		border-radius: 50%;
		border: 2px solid rgba(0, 0, 0, 0.15);
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15),
			inset -2px -2px 5px rgba(0, 0, 0, 0.1),
			inset 2px 2px 5px rgba(255, 255, 255, 0.2);
		flex-shrink: 0;
	}

	.step-desc { font-size: 0.875rem; color: #374151; font-weight: 500; }

	/* ── Results ──────────────────────────────────────── */
	.results-header {
		background: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%);
		border-radius: 16px;
		padding: 1.75rem;
		text-align: center;
		margin-bottom: 1rem;
		box-shadow: 0 4px 12px rgba(29, 78, 216, 0.35);
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
	.score-max   { color: rgba(255, 255, 255, 0.7); font-size: 1.5rem; font-weight: 500; }

	.results-subtitle { color: rgba(255, 255, 255, 0.9); font-size: 0.938rem; margin: 0; }

	.metrics-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 1rem;
		margin-bottom: 1rem;
	}

	.metric-card {
		background: white;
		border-radius: 16px;
		padding: 1.25rem;
		text-align: center;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
	}

	.metric-blue  { border-top: 4px solid #3b82f6; }
	.metric-green { border-top: 4px solid #16a34a; }
	.metric-soc   { border-top: 4px solid #1d4ed8; }

	.metric-value { font-size: 1.75rem; font-weight: 700; color: #1a1a2e; }
	.metric-label { font-size: 0.75rem; color: #6b7280; margin-top: 0.25rem; }

	/* ── Problem List ─────────────────────────────────── */
	.problem-list { display: flex; flex-direction: column; gap: 0.5rem; }

	.problem-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem 1rem;
		border-radius: 10px;
		border-left: 4px solid #d1d5db;
		background: #f9fafb;
		font-size: 0.875rem;
	}

	.row-perfect { border-left-color: #16a34a; }
	.row-solved  { border-left-color: #3b82f6; }
	.row-failed  { border-left-color: #ef4444; }

	.problem-num    { font-weight: 600; color: #1a1a2e; }
	.problem-detail { display: flex; align-items: center; gap: 0.5rem; color: #6b7280; }
	.min-label      { color: #9ca3af; }

	.tag {
		padding: 0.15rem 0.5rem;
		border-radius: 0.75rem;
		font-size: 0.75rem;
		font-weight: 600;
	}

	.tag-perfect { background: #dcfce7; color: #166534; }
	.tag-solved  { background: #dbeafe; color: #1e40af; }
	.tag-failed  { background: #fee2e2; color: #991b1b; }

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
		background: linear-gradient(135deg, #1d4ed8 0%, #3b82f6 100%);
		color: white;
		border: none;
		border-radius: 50%;
		font-size: 1.25rem;
		font-weight: 700;
		cursor: pointer;
		box-shadow: 0 4px 12px rgba(29, 78, 216, 0.4);
		display: flex;
		align-items: center;
		justify-content: center;
	}

	/* ── Animations ───────────────────────────────────── */
	@keyframes timer-pulse {
		0%, 100% { transform: scale(1); }
		50%       { transform: scale(1.05); }
	}

	@keyframes shake {
		0%, 100% { transform: translateX(0); }
		25%       { transform: translateX(-4px); }
		75%       { transform: translateX(4px); }
	}

	@keyframes fadeIn {
		from { opacity: 0; transform: translateY(-4px); }
		to   { opacity: 1; transform: translateY(0); }
	}

	/* ── Responsive ───────────────────────────────────── */
	@media (max-width: 640px) {
		.rules-grid    { grid-template-columns: 1fr; }
		.info-grid     { grid-template-columns: 1fr; }
		.metrics-grid  { grid-template-columns: 1fr; }
		.towers-row    { flex-direction: column; align-items: center; }
		.solving-row   { flex-direction: column; align-items: center; }
		.towers-divider { transform: rotate(90deg); padding: 0; }
		.action-buttons { flex-direction: column; }
		.completion-actions { flex-direction: column; }
		.cap-row       { flex-wrap: wrap; justify-content: center; }
	}
</style>


<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
	import { locale, localeText } from '$lib/i18n';
	import { buildPracticePayload, getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
	import { user } from '$lib/stores.js';
	import { onMount } from 'svelte';

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
	let selectedDisk = null;
	let moveHistory = [];
	let problemStartTime = null;
	let totalMoves = 0;
	let pegFullWarning = -1;

	// UI state
	let gamePhase = 'intro';
	let planningTimeRemaining = 0;
	let planningTimer = null;
	let userSolutions = [];
	let showingGoal = true;
	let results = null;
	let earnedBadges = [];
	let showSolution = false;
	let solutionPath = [];
	let actualMinMoves = 0;
	/** @type {string} */
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';
	let recordedSessionData = null;
	let recordedDifficulty = 1;

	const DISK_COLORS = {
		0: '#ef4444',
		1: '#3b82f6',
		2: '#22c55e'
	};

	const PEG_CAPACITIES = [3, 2, 1];

	// BFS algorithm to find minimum moves and solution path
	function findOptimalSolution(startState, goalState) {
		const stateKey = (state) => JSON.stringify(state);
		const isGoal = (state) => stateKey(state) === stateKey(goalState);
		const queue = [{ state: startState.map(peg => [...peg]), moves: 0, path: [] }];
		const visited = new Set([stateKey(startState)]);

		while (queue.length > 0) {
			const { state, moves, path } = queue.shift();
			if (isGoal(state)) return { minMoves: moves, path };

			for (let fromPeg = 0; fromPeg < 3; fromPeg++) {
				if (state[fromPeg].length === 0) continue;
				for (let toPeg = 0; toPeg < 3; toPeg++) {
					if (fromPeg === toPeg) continue;
					if (state[toPeg].length >= PEG_CAPACITIES[toPeg]) continue;
					const newState = state.map(peg => [...peg]);
					const disk = newState[fromPeg].pop();
					newState[toPeg].push(disk);
					const key = stateKey(newState);
					if (!visited.has(key)) {
						visited.add(key);
						queue.push({ state: newState, moves: moves + 1, path: [...path, { from: fromPeg, to: toPeg, disk }] });
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
			const response = await fetch('/api/tasks/tol/generate', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ difficulty })
			});
			if (response.ok) {
				sessionData = await response.json();
				recordedSessionData = cloneData(sessionData);
				recordedDifficulty = sessionData.difficulty || difficulty;
			}
		} catch (_) {
			// session load failure handled by loading state
		} finally {
			loading = false;
		}
	}

	/** @param {string} nextMode */
	function startTask(nextMode = TASK_PLAY_MODE.RECORDED) {
		playMode = nextMode;
		practiceStatusMessage = '';
		restoreRecordedSession();
		if (playMode === TASK_PLAY_MODE.PRACTICE) {
			sessionData = buildPracticePayload('tower-of-london', recordedSessionData);
		}
		userSolutions = [];
		results = null;
		earnedBadges = [];
		loadProblem(0);
	}

	function loadProblem(index) {
		currentProblemIndex = index;
		currentProblem = sessionData.problems[index];
		currentState = currentProblem.start_state.map(peg => [...peg]);
		goalState = currentProblem.goal_state.map(peg => [...peg]);

		const solution = findOptimalSolution(currentState, goalState);
		actualMinMoves = solution.minMoves;
		solutionPath = solution.path;
		currentProblem.minimum_moves = actualMinMoves;

		selectedDisk = null;
		moveHistory = [];
		totalMoves = 0;
		showingGoal = true;
		showSolution = false;
		pegFullWarning = -1;

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

	function selectDisk(pegIndex, diskIndex) {
		if (gamePhase !== 'solving') return;
		pegFullWarning = -1;
		const peg = currentState[pegIndex];
		if (diskIndex !== peg.length - 1) return;
		if (selectedDisk) {
			if (selectedDisk.pegIndex === pegIndex && selectedDisk.diskIndex === diskIndex) {
				selectedDisk = null;
			}
		} else {
			selectedDisk = { pegIndex, diskIndex, color: peg[diskIndex] };
		}
	}

	function moveToPeg(targetPegIndex) {
		if (gamePhase !== 'solving' || !selectedDisk) return;
		const sourcePeg = currentState[selectedDisk.pegIndex];
		const targetPeg = currentState[targetPegIndex];
		if (selectedDisk.pegIndex === targetPegIndex) {
			selectedDisk = null;
			return;
		}
		if (targetPeg.length >= PEG_CAPACITIES[targetPegIndex]) {
			pegFullWarning = targetPegIndex;
			selectedDisk = null;
			setTimeout(() => { pegFullWarning = -1; }, 1800);
			return;
		}
		pegFullWarning = -1;
		const disk = sourcePeg.pop();
		targetPeg.push(disk);
		totalMoves++;
		moveHistory.push({ from: selectedDisk.pegIndex, to: targetPegIndex, disk });
		selectedDisk = null;
		if (checkSolved()) completeProblem();
		currentState = currentState;
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
		userSolutions.push({
			problem_number: currentProblem.problem_number,
			solved: true,
			moves_used: totalMoves,
			time_seconds: timeElapsed,
			move_history: moveHistory
		});
		if (currentProblemIndex < sessionData.problems.length - 1) {
			gamePhase = 'problem_complete';
		} else {
			finishSession();
		}
	}

	function nextProblem() {
		loadProblem(currentProblemIndex + 1);
	}

	async function finishSession() {
		if (playMode === TASK_PLAY_MODE.PRACTICE) {
			playMode = TASK_PLAY_MODE.RECORDED;
			practiceStatusMessage = getPracticeCopy($locale).complete;
			sessionData = null;
			currentProblemIndex = 0;
			currentProblem = null;
			userSolutions = [];
			selectedDisk = null;
			gamePhase = 'intro';
			await loadSession();
			return;
		}
		try {
			const scoreResponse = await fetch('/api/tasks/tol/score', {
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
			const response = await fetch(`http://localhost:8000/api/training/tasks/soc/submit/${userId}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					session_data: { difficulty, problems: sessionData?.problems || [] },
					user_solutions: userSolutions,
					task_id: taskId
				})
			});
			if (!response.ok) throw new Error('Failed to save');
			const data = await response.json();
			if (data.newly_earned_badges && data.newly_earned_badges.length > 0) {
				earnedBadges = data.newly_earned_badges;
			}
		} catch (_) {
			// silent
		}
	}

	function toggleGoalView() {
		showingGoal = !showingGoal;
	}
</script>

<div class="tol-page" data-localize-skip>
	<div class="tol-wrapper">

		{#if gamePhase === 'intro'}

			<!-- Header Card -->
			<div class="header-card">
				<div class="header-content">
					<div class="header-text">
						<h1 class="task-title">{lt('Tower of London', 'টাওয়ার অব লন্ডন')}</h1>
						<p class="task-domain">{lt('Planning / Executive Function', 'পরিকল্পনা / নির্বাহী কার্যকারিতা')}</p>
					</div>
					<DifficultyBadge difficulty={sessionData?.difficulty || difficulty} domain="Executive Planning" />
				</div>
			</div>

			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} />
			{/if}

			{#if loading}
				<LoadingSkeleton />
			{:else}

				<!-- Task Concept -->
				<div class="card task-concept">
					<div class="concept-badge">
						<span class="badge-icon">TOL</span>
						<span>{lt('Executive Planning', 'নির্বাহী পরিকল্পনা')}</span>
					</div>
					<p class="concept-desc">
						{lt(
							'The Tower of London requires advance planning, working memory, and inhibitory control to move colored disks in the minimum number of steps. It is widely used to assess prefrontal-dependent planning deficits in multiple sclerosis.',
							'টাওয়ার অব লন্ডন সর্বনিম্ন পদক্ষেপে রঙিন ডিস্ক সরাতে অগ্রিম পরিকল্পনা, ওয়ার্কিং মেমোরি এবং বাধামূলক নিয়ন্ত্রণ প্রয়োজন। এটি মাল্টিপল স্ক্লেরোসিসে প্রিফ্রন্টাল পরিকল্পনার ঘাটতি মূল্যায়নে ব্যাপকভাবে ব্যবহৃত।'
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
								<strong>{lt('Study the planning screen', 'পরিকল্পনার স্ক্রিন পর্যবেক্ষণ করুন')}</strong>
								<span>{lt('The start and goal disk positions are shown side by side during the planning phase.', 'পরিকল্পনা পর্যায়ে শুরু এবং লক্ষ্যের অবস্থান পাশাপাশি দেখানো হয়।')}</span>
							</div>
						</div>
						<div class="rule-item">
							<div class="rule-num">2</div>
							<div class="rule-text">
								<strong>{lt('Plan before moving', 'চলার আগে পরিকল্পনা করুন')}</strong>
								<span>{lt('Work out the minimum number of moves mentally before starting execution.', 'চালু করার আগে মানসিকভাবে সর্বনিম্ন পদক্ষেপের সংখ্যা নির্ধারণ করুন।')}</span>
							</div>
						</div>
						<div class="rule-item">
							<div class="rule-num">3</div>
							<div class="rule-text">
								<strong>{lt('Click disk then click peg', 'ডিস্ক ক্লিক করুন তারপর পেগ ক্লিক করুন')}</strong>
								<span>{lt('Select the top disk on any peg, then click the destination peg to move it.', 'যেকোনো পেগের উপরের ডিস্ক নির্বাচন করুন, তারপর গন্তব্য পেগে ক্লিক করুন।')}</span>
							</div>
						</div>
						<div class="rule-item">
							<div class="rule-num">4</div>
							<div class="rule-text">
								<strong>{lt('Respect capacity limits', 'ধারণক্ষমতার সীমা মানুন')}</strong>
								<span>{lt('Peg 1 holds 3 disks, Peg 2 holds 2, Peg 3 holds only 1. You cannot overfill a peg.', 'পেগ ১ — ৩টি, পেগ ২ — ২টি, পেগ ৩ — ১টি ডিস্ক ধারণ করে। পেগ অতিরিক্ত পূর্ণ করা যাবে না।')}</span>
							</div>
						</div>
					</div>
				</div>

				<!-- Peg Capacity Visual -->
				<div class="card">
					<h2 class="section-title">{lt('Peg Capacities', 'পেগের ধারণক্ষমতা')}</h2>
					<div class="peg-cap-row">
						<div class="peg-cap-item">
							<div class="cap-circle cap-1">3</div>
							<div class="cap-label">{lt('Peg 1', 'পেগ ১')}</div>
							<div class="cap-sub">{lt('3 disks max', 'সর্বোচ্চ ৩টি')}</div>
						</div>
						<div class="cap-arrow">&#8594;</div>
						<div class="peg-cap-item">
							<div class="cap-circle cap-2">2</div>
							<div class="cap-label">{lt('Peg 2', 'পেগ ২')}</div>
							<div class="cap-sub">{lt('2 disks max', 'সর্বোচ্চ ২টি')}</div>
						</div>
						<div class="cap-arrow">&#8594;</div>
						<div class="peg-cap-item">
							<div class="cap-circle cap-3">1</div>
							<div class="cap-label">{lt('Peg 3', 'পেগ ৩')}</div>
							<div class="cap-sub">{lt('1 disk max', 'সর্বোচ্চ ১টি')}</div>
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
								<span>{lt('MS Relevance', 'এমএস প্রাসঙ্গিকতা')}</span>
								<strong>{lt('Prefrontal planning', 'প্রিফ্রন্টাল পরিকল্পনা')}</strong>
							</div>
						</div>
					</div>
				</div>

				<!-- Clinical Info -->
				<div class="clinical-info">
					<div class="clinical-header">
						<div class="clinical-badge">{lt('Clinical Basis', 'ক্লিনিকাল ভিত্তি')}</div>
						<h3>{lt('Gold Standard Planning Paradigm', 'গোল্ড স্ট্যান্ডার্ড পরিকল্পনা প্যারাডাইম')}</h3>
					</div>
					<p>
						{lt(
							'Shallice (1982) developed the Tower of London to study frontal lobe planning. Owen et al. (1990) extended it via the CANTAB battery. MS patients make significantly more excess moves, revealing prefrontal-executive deficits that correlate with daily functioning and real-world multitasking ability.',
							'শ্যালিস (১৯৮২) ফ্রন্টাল লোব পরিকল্পনা অধ্যয়নের জন্য টাওয়ার অব লন্ডন তৈরি করেন। গবেষণায় দেখা গেছে এমএস রোগীরা উল্লেখযোগ্যভাবে বেশি অতিরিক্ত পদক্ষেপ করেন যা দৈনন্দিন কার্যকারিতার সাথে সম্পর্কিত।'
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
					<PracticeModeBanner locale={$locale} />
				{/if}

				<!-- Status Bar -->
				<div class="game-status-bar">
					<div class="status-pills">
						<span class="pill pill-tol">{lt(`Problem ${currentProblem.problem_number} / ${sessionData.total_problems}`, `সমস্যা ${currentProblem.problem_number} / ${sessionData.total_problems}`)}</span>
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

				<!-- Towers side by side -->
				<div class="towers-row">
					<div class="tower-panel">
						<div class="tower-label tower-label-start">{lt('START', 'শুরু')}</div>
						<div class="pegs-row">
							{#each currentProblem.start_state as peg, pegIndex}
								<div class="peg-col">
									<div class="peg-area">
										<div class="peg-rod-elem"></div>
										<div class="peg-base-elem"></div>
										{#each peg as diskColor, diskIndex}
											<div class="disk-abs"
												style="bottom: {12 + diskIndex * 32}px; width: {72 - diskIndex * 10}px; background: {DISK_COLORS[diskColor]};">
											</div>
										{/each}
									</div>
									<div class="peg-cap-count">{PEG_CAPACITIES[pegIndex]}</div>
								</div>
							{/each}
						</div>
					</div>

					<div class="towers-divider">&#8594;</div>

					<div class="tower-panel">
						<div class="tower-label tower-label-goal">{lt('GOAL', 'লক্ষ্য')}</div>
						<div class="pegs-row">
							{#each currentProblem.goal_state as peg, pegIndex}
								<div class="peg-col">
									<div class="peg-area peg-area-goal">
										<div class="peg-rod-elem peg-rod-goal"></div>
										<div class="peg-base-elem peg-base-goal"></div>
										{#each peg as diskColor, diskIndex}
											<div class="disk-abs disk-abs-goal"
												style="bottom: {12 + diskIndex * 32}px; width: {72 - diskIndex * 10}px; background: {DISK_COLORS[diskColor]};">
											</div>
										{/each}
									</div>
									<div class="peg-cap-count peg-cap-faded">{PEG_CAPACITIES[pegIndex]}</div>
								</div>
							{/each}
						</div>
					</div>
				</div>

				<div class="planning-footer">
					<p class="planning-hint">
						{lt('Study both configurations and plan your move sequence before the timer runs out.', 'টাইমার শেষ হওয়ার আগে উভয় কনফিগারেশন পর্যবেক্ষণ করুন এবং আপনার পদক্ষেপের ক্রম পরিকল্পনা করুন।')}
					</p>
					<button class="ready-btn" on:click={startSolving}>
						{lt('Ready — Start Solving', 'প্রস্তুত — সমাধান শুরু করুন')}
					</button>
				</div>
			</div>

		{:else if gamePhase === 'solving'}

			<div class="game-card">
				{#if playMode === TASK_PLAY_MODE.PRACTICE}
					<PracticeModeBanner locale={$locale} />
				{/if}

				<!-- Solving Status Bar -->
				<div class="game-status-bar">
					<div class="status-pills">
						<span class="pill pill-tol">{lt(`Problem ${currentProblem.problem_number} / ${sessionData.total_problems}`, `সমস্যা ${currentProblem.problem_number} / ${sessionData.total_problems}`)}</span>
						<span class="pill pill-moves">{lt(`Moves: ${totalMoves}`, `পদক্ষেপ: ${totalMoves}`)}</span>
						{#if currentProblem.show_minimum}
							<span class="pill pill-target">{lt(`Min: ${currentProblem.minimum_moves}`, `সর্বনিম্ন: ${currentProblem.minimum_moves}`)}</span>
						{/if}
					</div>
					<button class="toggle-goal-btn" on:click={toggleGoalView}>
						{showingGoal ? lt('Hide Goal', 'লক্ষ্য লুকান') : lt('Show Goal', 'লক্ষ্য দেখান')}
					</button>
				</div>

				<!-- Selected disk indicator -->
				{#if selectedDisk !== null}
					<div class="selected-indicator">
						<div class="selected-swatch" style="background: {DISK_COLORS[selectedDisk.color]};"></div>
						<span>{lt('Disk selected — click any peg to move it', 'ডিস্ক নির্বাচিত — এটি সরাতে যেকোনো পেগে ক্লিক করুন')}</span>
					</div>
				{/if}

				<!-- Peg full warning -->
				{#if pegFullWarning >= 0}
					<div class="peg-full-warning">
						{lt(`Peg ${pegFullWarning + 1} is full (max ${PEG_CAPACITIES[pegFullWarning]} disks)`, `পেগ ${pegFullWarning + 1} পূর্ণ (সর্বোচ্চ ${PEG_CAPACITIES[pegFullWarning]} ডিস্ক)`)}
					</div>
				{/if}

				<!-- Solving Layout -->
				<div class="solving-row" class:solving-single={!showingGoal}>

					<!-- Interactive current state -->
					<div class="tower-panel">
						<div class="tower-label tower-label-current">{lt('CURRENT POSITION', 'বর্তমান অবস্থান')}</div>
						<div class="pegs-row pegs-interactive">
							{#each currentState as peg, pegIndex}
								{@const isFull = peg.length >= PEG_CAPACITIES[pegIndex]}
								<div class="peg-col">
									<!-- Clickable drop zone -->
									<div class="peg-area peg-drop"
										class:drop-active={selectedDisk && selectedDisk.pegIndex !== pegIndex && !isFull}
										class:drop-full={selectedDisk && selectedDisk.pegIndex !== pegIndex && isFull}
										class:drop-warn={pegFullWarning === pegIndex}
										role="button"
										tabindex="0"
										aria-label="Move disk to peg {pegIndex + 1}"
										on:click={() => moveToPeg(pegIndex)}
										on:keydown={(e) => e.key === 'Enter' && moveToPeg(pegIndex)}>
										<div class="peg-rod-elem"></div>
										<div class="peg-base-elem"></div>
										{#each peg as diskColor, diskIndex}
											{@const isTopDisk = diskIndex === peg.length - 1}
											{@const isSelected = selectedDisk && selectedDisk.pegIndex === pegIndex && selectedDisk.diskIndex === diskIndex}
											<button
												on:click|stopPropagation={() => selectDisk(pegIndex, diskIndex)}
												disabled={!isTopDisk}
												class="disk-btn"
												class:disk-selected={isSelected}
												class:disk-top={isTopDisk && !isSelected}
												class:disk-locked={!isTopDisk}
												aria-label="{isTopDisk ? 'Select' : 'Cannot select'} disk on peg {pegIndex + 1}"
												style="bottom: {12 + diskIndex * 32}px; width: {72 - diskIndex * 10}px; background: {DISK_COLORS[diskColor]}; {isSelected ? 'transform: translateX(-50%) translateY(-8px);' : 'transform: translateX(-50%);'}">
											</button>
										{/each}
									</div>
									<div class="peg-count-badge" class:count-full={isFull}>
										{peg.length}/{PEG_CAPACITIES[pegIndex]}
									</div>
								</div>
							{/each}
						</div>
					</div>

					<!-- Goal reference -->
					{#if showingGoal}
						<div class="tower-panel tower-panel-dim">
							<div class="tower-label tower-label-goal">{lt('TARGET', 'লক্ষ্য')}</div>
							<div class="pegs-row">
								{#each goalState as peg, pegIndex}
									<div class="peg-col">
										<div class="peg-area peg-area-goal">
											<div class="peg-rod-elem peg-rod-goal"></div>
											<div class="peg-base-elem peg-base-goal"></div>
											{#each peg as diskColor, diskIndex}
												<div class="disk-abs disk-abs-goal"
													style="bottom: {12 + diskIndex * 32}px; width: {72 - diskIndex * 10}px; background: {DISK_COLORS[diskColor]};">
												</div>
											{/each}
										</div>
										<div class="peg-cap-count peg-cap-faded">{PEG_CAPACITIES[pegIndex]}</div>
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
					<PracticeModeBanner locale={$locale} />
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
							<div class="cstat-val" class:cstat-perfect={userSolutions[userSolutions.length - 1].moves_used === actualMinMoves} class:cstat-extra={userSolutions[userSolutions.length - 1].moves_used !== actualMinMoves}>
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
									<div class="step-disk" style="background: {DISK_COLORS[move.disk]};"></div>
									<span class="step-desc">
										{move.disk === 0 ? lt('Red', 'লাল') : move.disk === 1 ? lt('Blue', 'নীল') : lt('Green', 'সবুজ')}
										{lt(`disk: Peg ${move.from + 1} → Peg ${move.to + 1}`, `ডিস্ক: পেগ ${move.from + 1} → পেগ ${move.to + 1}`)}
									</span>
								</div>
							{/each}
						</div>
					</div>
				{/if}
			</div>

		{:else if gamePhase === 'results'}

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
				<div class="metric-card metric-tol">
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
	.tol-page {
		min-height: 100vh;
		background: #C8DEFA;
		padding: 1.5rem;
	}

	.tol-wrapper {
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
		color: #c2410c;
		font-weight: 500;
		margin: 0;
	}

	/* ── Task Concept ─────────────────────────────────── */
	.task-concept { margin-bottom: 1rem; }

	.concept-badge {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		background: linear-gradient(135deg, #c2410c 0%, #ea580c 100%);
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
		background: linear-gradient(135deg, #c2410c 0%, #ea580c 100%);
		color: white;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.875rem;
		font-weight: 700;
		flex-shrink: 0;
	}

	.rule-text {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.rule-text strong { font-size: 0.875rem; color: #1a1a2e; }
	.rule-text span   { font-size: 0.8rem; color: #6b7280; line-height: 1.4; }

	/* ── Peg Capacity Row ─────────────────────────────── */
	.peg-cap-row {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1.5rem;
	}

	.peg-cap-item { text-align: center; }

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

	.cap-1 { background: linear-gradient(135deg, #c2410c 0%, #ea580c 100%); }
	.cap-2 { background: linear-gradient(135deg, #b45309 0%, #d97706 100%); }
	.cap-3 { background: linear-gradient(135deg, #78350f 0%, #92400e 100%); }

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
	.detail-row span    { color: #6b7280; }
	.detail-row strong  { color: #1a1a2e; text-align: right; max-width: 60%; }

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

	.pill-tol    { background: #ffedd5; color: #9a3412; }
	.pill-phase  { background: #f3f4f6; color: #374151; }
	.pill-moves  { background: #dbeafe; color: #1e40af; }
	.pill-target { background: #fef3c7; color: #92400e; }

	/* ── Planning Timer ───────────────────────────────── */
	.planning-timer {
		background: linear-gradient(135deg, #c2410c 0%, #ea580c 100%);
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
		background: #fff7ed;
		border: 2px solid #fed7aa;
		border-radius: 10px;
		padding: 0.75rem 1rem;
		text-align: center;
		color: #9a3412;
		font-size: 0.938rem;
		font-weight: 600;
		margin-bottom: 1.25rem;
	}

	/* ── Towers Layout ────────────────────────────────── */
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
	.solving-single .tower-panel { width: 100%; max-width: 380px; }

	.towers-divider {
		display: flex;
		align-items: center;
		padding-top: 3rem;
		font-size: 1.5rem;
		color: #c2410c;
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

	.tower-label-start   { background: #ffedd5; color: #c2410c; }
	.tower-label-goal    { background: #dbeafe; color: #1e40af; }
	.tower-label-current { background: #ffedd5; color: #c2410c; }

	/* ── Pegs Row ─────────────────────────────────────── */
	.pegs-row {
		display: flex;
		justify-content: center;
		gap: 1.5rem;
	}

	.peg-col {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}

	/* ── Peg Area (absolute-positioned disks inside) ──── */
	.peg-area {
		position: relative;
		width: 88px;
		height: 280px;
	}

	.peg-area-goal { opacity: 0.7; }

	.peg-rod-elem {
		position: absolute;
		bottom: 12px;
		left: 50%;
		transform: translateX(-50%);
		width: 10px;
		height: 240px;
		background: linear-gradient(to right, #cbd5e1, #94a3b8, #cbd5e1);
		border-radius: 5px;
	}

	.peg-rod-goal {
		background: linear-gradient(to right, #e2e8f0, #cbd5e1, #e2e8f0);
	}

	.peg-base-elem {
		position: absolute;
		bottom: 0;
		width: 100%;
		height: 12px;
		background: linear-gradient(to bottom, #94a3b8, #64748b);
		border-radius: 6px;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
	}

	.peg-base-goal {
		background: linear-gradient(to bottom, #cbd5e1, #94a3b8);
		opacity: 0.6;
	}

	/* ── Static disk (planning / goal view) ──────────── */
	.disk-abs {
		position: absolute;
		left: 50%;
		transform: translateX(-50%);
		height: 26px;
		border-radius: 5px;
		border: 2px solid rgba(0, 0, 0, 0.2);
		box-shadow: 0 3px 6px rgba(0, 0, 0, 0.15);
	}

	.disk-abs-goal {
		opacity: 0.7;
		border: 2px solid rgba(0, 0, 0, 0.1);
	}

	/* ── Interactive disk button ──────────────────────── */
	.disk-btn {
		position: absolute;
		left: 50%;
		height: 26px;
		border-radius: 5px;
		border: 3px solid rgba(0, 0, 0, 0.2);
		box-shadow: 0 3px 6px rgba(0, 0, 0, 0.15);
		cursor: default;
		padding: 0;
		transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
	}

	.disk-top {
		cursor: pointer;
	}

	.disk-top:hover {
		box-shadow: 0 6px 16px rgba(0, 0, 0, 0.25);
		border-color: rgba(255, 255, 255, 0.6);
	}

	.disk-selected {
		border: 4px solid #fbbf24 !important;
		box-shadow: 0 0 0 4px rgba(251, 191, 36, 0.35), 0 8px 20px rgba(0, 0, 0, 0.2) !important;
		cursor: pointer;
	}

	.disk-locked {
		opacity: 0.75;
		cursor: not-allowed;
	}

	/* ── Drop Zone (peg-area when a disk is selected) ─── */
	.peg-drop { cursor: default; }

	.drop-active {
		cursor: pointer;
		border: 3px dashed #3b82f6 !important;
		border-radius: 12px;
		background: rgba(59, 130, 246, 0.05);
	}

	.drop-full {
		cursor: not-allowed;
		border: 3px dashed #ef4444 !important;
		background: rgba(239, 68, 68, 0.05);
	}

	.drop-warn {
		border: 3px solid #ef4444 !important;
		background: rgba(239, 68, 68, 0.08);
		animation: shake 0.3s ease-in-out;
	}

	/* ── Peg count badge ──────────────────────────────── */
	.peg-count-badge {
		background: #e0e7ff;
		color: #3730a3;
		padding: 0.2rem 0.6rem;
		border-radius: 1rem;
		font-size: 0.75rem;
		font-weight: 600;
		border: 2px solid #6366f1;
	}

	.count-full {
		background: #fee2e2;
		color: #991b1b;
		border-color: #ef4444;
	}

	.peg-cap-count {
		font-size: 0.75rem;
		color: #6b7280;
		font-weight: 600;
		text-align: center;
	}

	.peg-cap-faded { opacity: 0.5; }

	/* ── Selected indicator ───────────────────────────── */
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
		width: 48px;
		height: 24px;
		border-radius: 4px;
		border: 3px solid #92400e;
		flex-shrink: 0;
	}

	/* ── Peg full warning ─────────────────────────────── */
	.peg-full-warning {
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

	/* ── Toggle goal button ───────────────────────────── */
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
		background: linear-gradient(135deg, #c2410c 0%, #ea580c 100%);
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
	.cstat-extra   { color: #c2410c !important; }

	.cstat-lbl {
		font-size: 0.75rem;
		color: #9ca3af;
		margin-top: 0.25rem;
	}

	.completion-actions {
		display: flex;
		gap: 1rem;
		justify-content: center;
		margin-bottom: 1.5rem;
	}

	/* ── Solution Panel ───────────────────────────────── */
	.solution-panel {
		background: #fff7ed;
		border: 2px solid #fed7aa;
		border-radius: 12px;
		padding: 1.25rem;
		text-align: left;
		margin-top: 1rem;
	}

	.solution-title {
		font-size: 1rem;
		font-weight: 600;
		color: #9a3412;
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
		background: linear-gradient(135deg, #c2410c 0%, #ea580c 100%);
		color: white;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.75rem;
		font-weight: 700;
		flex-shrink: 0;
	}

	.step-disk {
		width: 2.5rem;
		height: 1.25rem;
		border-radius: 3px;
		border: 2px solid rgba(0, 0, 0, 0.15);
		flex-shrink: 0;
	}

	.step-desc { font-size: 0.875rem; color: #374151; font-weight: 500; }

	/* ── Results ──────────────────────────────────────── */
	.results-header {
		background: linear-gradient(135deg, #c2410c 0%, #ea580c 100%);
		border-radius: 16px;
		padding: 1.75rem;
		text-align: center;
		margin-bottom: 1rem;
		box-shadow: 0 4px 12px rgba(194, 65, 12, 0.35);
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
	.metric-tol   { border-top: 4px solid #c2410c; }

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

	.problem-num  { font-weight: 600; color: #1a1a2e; }
	.problem-detail { display: flex; align-items: center; gap: 0.5rem; color: #6b7280; }
	.min-label { color: #9ca3af; }

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
		background: linear-gradient(135deg, #c2410c 0%, #ea580c 100%);
		color: white;
		border: none;
		border-radius: 50%;
		font-size: 1.25rem;
		font-weight: 700;
		cursor: pointer;
		box-shadow: 0 4px 12px rgba(194, 65, 12, 0.4);
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
		.rules-grid     { grid-template-columns: 1fr; }
		.info-grid      { grid-template-columns: 1fr; }
		.metrics-grid   { grid-template-columns: 1fr; }
		.towers-row     { flex-direction: column; align-items: center; }
		.solving-row    { flex-direction: column; align-items: center; }
		.towers-divider { transform: rotate(90deg); padding: 0; }
		.action-buttons { flex-direction: column; }
		.completion-actions { flex-direction: column; }
		.peg-cap-row    { flex-wrap: wrap; justify-content: center; }
	}
</style>

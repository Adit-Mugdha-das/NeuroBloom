<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { API_BASE_URL } from '$lib/api.js';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import { user } from '$lib/stores.js';
	import { onMount } from 'svelte';

	let userId;
	let baselineScore = 0;
	let difficulty = 1;
	let taskId = null;
	
	let sessionData = null;
	let currentProblemIndex = 0;
	let currentProblem = null;
	
	// Game state
	let currentState = []; // Current ball positions [[ball_ids in stocking 0], [stocking 1], [stocking 2]]
	let goalState = [];
	let selectedBall = null; // {stockingIndex, ballIndex, color}
	let moveHistory = [];
	let problemStartTime = null;
	let totalMoves = 0;
	
	// UI state
	let gamePhase = 'intro'; // intro, planning, solving, problem_complete, results
	let planningTimeRemaining = 0;
	let planningTimer = null;
	let userSolutions = [];
	let solutions = []; // Track all problem solutions
	let showingGoal = true;
	let results = null;
	let earnedBadges = [];

	// Colors for balls
	const BALL_COLORS = {
		0: '#ef4444', // red
		1: '#3b82f6', // blue
		2: '#22c55e'  // green
	};

	const STOCKING_CAPACITIES = [3, 2, 1];

	user.subscribe(value => {
		if (value) {
			userId = value.id;
		}
	});

	onMount(async () => {
		if (!userId) {
			goto('/login');
			return;
		}
		await loadSession();
	});

	async function loadSession() {
		try {
			// Fetch baseline to determine difficulty
			const baselineRes = await fetch(`/api/baseline/${userId}`);
			if (baselineRes.ok) {
				const baseline = await baselineRes.json();
				baselineScore = baseline.planning_score || 0;
				
				// Map baseline score to difficulty
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

			const response = await fetch('/api/tasks/soc/generate', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ difficulty })
			});

			if (response.ok) {
				sessionData = await response.json();
				console.log('Session loaded:', sessionData);
			}
		} catch (error) {
			console.error('Error loading session:', error);
		}
	}

	function startTask() {
		gamePhase = 'planning';
		loadProblem(0);
	}

	function loadProblem(index) {
		currentProblemIndex = index;
		currentProblem = sessionData.problems[index];
		
		// Deep copy states
		currentState = currentProblem.start_state.map(stocking => [...stocking]);
		goalState = currentProblem.goal_state.map(stocking => [...stocking]);
		
		selectedBall = null;
		moveHistory = [];
		totalMoves = 0;
		showingGoal = true;
		
		// Start planning phase
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
		
		const stocking = currentState[stockingIndex];
		
		// Can only select top ball
		if (ballIndex !== stocking.length - 1) return;
		
		if (selectedBall) {
			// If same ball clicked, deselect
			if (selectedBall.stockingIndex === stockingIndex && selectedBall.ballIndex === ballIndex) {
				selectedBall = null;
			}
		} else {
			// Select this ball
			const color = stocking[ballIndex];
			selectedBall = { stockingIndex, ballIndex, color };
		}
	}

	function moveToStocking(targetStockingIndex) {
		if (gamePhase !== 'solving' || !selectedBall) return;
		
		const sourceStocking = currentState[selectedBall.stockingIndex];
		const targetStocking = currentState[targetStockingIndex];
		
		// Can't move to same stocking
		if (selectedBall.stockingIndex === targetStockingIndex) {
			selectedBall = null;
			return;
		}
		
		// Check capacity
		if (targetStocking.length >= STOCKING_CAPACITIES[targetStockingIndex]) {
			alert(`Stocking ${targetStockingIndex + 1} is full!`);
			selectedBall = null;
			return;
		}
		
		// Move the ball
		const ball = sourceStocking.pop();
		targetStocking.push(ball);
		
		totalMoves++;
		moveHistory.push({
			from: selectedBall.stockingIndex,
			to: targetStockingIndex,
			ball: ball
		});
		
		selectedBall = null;
		
		// Check if solved
		if (checkSolved()) {
			completeProblem();
		}
		
		// Force reactivity
		currentState = currentState;
	}

	function checkSolved() {
		// Compare current state to goal state
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

	async function finishSession() {
		try {
			const response = await fetch('/api/tasks/soc/score', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					session_data: sessionData,
					user_solutions: userSolutions
				})
			});

			if (response.ok) {
				results = await response.json();
				
				// Save to database
				await saveResults();
				
				gamePhase = 'results';
			}
		} catch (error) {
			console.error('Error scoring session:', error);
		}
	}

	async function saveResults() {
		try {
			taskId = $page.url.searchParams.get('taskId');
			const response = await fetch(`${API_BASE_URL}/api/tasks/soc/submit/${userId}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				credentials: 'include',
				body: JSON.stringify({
					session_data: {
						...sessionData,
						difficulty: difficulty
					},
					user_solutions: solutions,
					task_id: taskId
				})
			});

			if (!response.ok) throw new Error('Failed to save results');
			
			const data = await response.json();
			
			if (data.new_badges && data.new_badges.length > 0) {
				earnedBadges = data.new_badges;
			}

			// Update user store
			user.update(u => ({
				...u,
				planning_difficulty: data.new_difficulty
			}));

		} catch (error) {
			console.error('Error saving results:', error);
		}
	}

	function toggleGoalView() {
		showingGoal = !showingGoal;
	}

	function getDifficultyInfo() {
		if (!sessionData) return '';
		const config = sessionData.config;
		const problems = sessionData.problems;
		const minMoves = Math.min(...problems.map(p => p.minimum_moves));
		const maxMoves = Math.max(...problems.map(p => p.minimum_moves));
		
		let desc = '';
		if (maxMoves <= 2) desc = 'Simple 2-move problems';
		else if (maxMoves <= 3) desc = '3-move planning challenges';
		else if (maxMoves <= 4) desc = '4-move complex planning';
		else if (maxMoves <= 5) desc = '5-move advanced problems';
		else desc = '6+ move expert challenges';
		
		return `${desc}, ${config.planning_time_seconds}s planning time`;
	}
</script>

<div style="min-height: 100vh; background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%); padding: 2rem;">
	<div style="max-width: 1000px; margin: 0 auto;">
		
		{#if gamePhase === 'intro'}
			<div style="background: white; border-radius: 16px; padding: 3rem; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				<div style="text-align: center; margin-bottom: 2rem;">
					<h1 style="font-size: 2.5rem; color: #8b5cf6; margin-bottom: 0.5rem; font-weight: 700;">
						🧦 Stockings of Cambridge
					</h1>
					<p style="font-size: 1.1rem; color: #64748b;">
						Executive Planning & Problem Solving
					</p>
				</div>

				<div style="background: #f8fafc; border-radius: 12px; padding: 2rem; margin-bottom: 2rem; border-left: 4px solid #8b5cf6;">
					<h3 style="color: #1e293b; margin-bottom: 1rem; font-size: 1.3rem;">📋 How It Works</h3>
					<ul style="color: #475569; line-height: 1.8; margin-left: 1.5rem;">
						<li><strong>Planning Phase:</strong> Study the start and goal configurations</li>
						<li><strong>Mental Planning:</strong> Figure out the minimum moves needed</li>
						<li><strong>Execution:</strong> Move colored balls between stockings to match the goal</li>
						<li><strong>Constraints:</strong> Stocking 1 holds 3 balls, Stocking 2 holds 2, Stocking 3 holds 1</li>
						<li><strong>Rule:</strong> Only move the top ball from each stocking</li>
					</ul>
				</div>

				{#if sessionData}
					<div style="background: #f5f3ff; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem; border: 2px solid #8b5cf6;">
						<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
							<h3 style="color: #5b21b6; margin: 0;">Current Session</h3>
							<span style="background: #8b5cf6; color: white; padding: 0.4rem 1rem; border-radius: 20px; font-weight: 600;">
								Level {difficulty}
							</span>
						</div>
						<div style="color: #5b21b6; line-height: 1.8;">
							<div><strong>Problems:</strong> {sessionData.total_problems}</div>
							<div><strong>Difficulty:</strong> {getDifficultyInfo()}</div>
							{#if baselineScore > 0}
								<div style="margin-top: 0.5rem; font-size: 0.9rem; opacity: 0.8;">
									Based on your planning baseline: {baselineScore}/100
								</div>
							{/if}
						</div>
					</div>

					<div style="text-align: center;">
						<button on:click={startTask}
							style="background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%); color: white; border: none; 
							padding: 1rem 3rem; font-size: 1.2rem; border-radius: 12px; cursor: pointer; font-weight: 600;
							box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4); transition: all 0.3s ease;">
							Start Planning Challenge
						</button>
					</div>
				{:else}
					<div style="text-align: center; padding: 2rem; color: #64748b;">
						<div style="font-size: 2rem; margin-bottom: 1rem;">⏳</div>
						<p>Loading session...</p>
					</div>
				{/if}
			</div>

		{:else if gamePhase === 'planning'}
			<div style="background: white; border-radius: 16px; padding: 2rem; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				<div style="text-align: center; margin-bottom: 2rem;">
					<h2 style="color: #8b5cf6; margin-bottom: 0.5rem;">
						Problem {currentProblem.problem_number} of {sessionData.total_problems}
					</h2>
					<div style="font-size: 1.8rem; font-weight: 700; color: #ef4444; margin-bottom: 0.5rem;">
						⏱️ {planningTimeRemaining}s
					</div>
					<p style="color: #64748b;">Study the configurations and plan your moves</p>
				</div>

				{#if currentProblem.show_minimum}
					<div style="background: #fef3c7; border: 2px solid #f59e0b; border-radius: 8px; padding: 1rem; margin-bottom: 2rem; text-align: center;">
						<strong style="color: #92400e;">Minimum Moves Required: {currentProblem.minimum_moves}</strong>
					</div>
				{/if}

				<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-bottom: 2rem;">
					<!-- Start Configuration -->
					<div>
						<h3 style="text-align: center; color: #1e293b; margin-bottom: 1rem;">START</h3>
						<div style="display: flex; justify-content: center; gap: 2.5rem; align-items: flex-end; padding: 2rem 1rem;">
							{#each currentProblem.start_state as stocking, stockingIndex}
								<div style="position: relative; width: 90px; height: 350px; display: flex; flex-direction: column; align-items: center;">
									<!-- Stocking top (opening) -->
									<div style="width: 85px; height: 25px; background: linear-gradient(to bottom, #cbd5e1, #94a3b8); border-radius: 8px 8px 0 0; border: 3px solid #64748b; border-bottom: none; box-shadow: inset 0 -3px 5px rgba(0,0,0,0.1);"></div>
									
									<!-- Stocking body -->
									<div style="width: 80px; flex-grow: 1; background: linear-gradient(to right, #e2e8f0, #cbd5e1, #e2e8f0); border: 3px solid #64748b; border-top: none; border-radius: 0 0 12px 12px; position: relative; display: flex; flex-direction: column-reverse; align-items: center; padding: 0.5rem 0; box-shadow: inset -3px 0 8px rgba(0,0,0,0.1);">
										<!-- Balls stacked from bottom -->
										{#each stocking as ballColor, ballIndex}
											<div style="width: 50px; height: 50px; border-radius: 50%; background: radial-gradient(circle at 30% 30%, {BALL_COLORS[ballColor]}ee, {BALL_COLORS[ballColor]}); margin: 0.3rem 0; border: 3px solid rgba(0,0,0,0.2); box-shadow: 0 4px 8px rgba(0,0,0,0.2), inset -5px -5px 10px rgba(0,0,0,0.2), inset 5px 5px 10px rgba(255,255,255,0.3);"></div>
										{/each}
									</div>
									
									<!-- Capacity label -->
									<div style="position: absolute; bottom: -30px; width: 100%; text-align: center; font-size: 0.8rem; color: #64748b; font-weight: 600;">
										Stocking {stockingIndex + 1} (max: {STOCKING_CAPACITIES[stockingIndex]})
									</div>
								</div>
							{/each}
						</div>
					</div>

					<!-- Goal Configuration -->
					<div>
						<h3 style="text-align: center; color: #1e293b; margin-bottom: 1rem;">GOAL</h3>
						<div style="display: flex; justify-content: center; gap: 2.5rem; align-items: flex-end; padding: 2rem 1rem;">
							{#each currentProblem.goal_state as stocking, stockingIndex}
								<div style="position: relative; width: 90px; height: 350px; display: flex; flex-direction: column; align-items: center;">
									<div style="width: 85px; height: 25px; background: linear-gradient(to bottom, #cbd5e1, #94a3b8); border-radius: 8px 8px 0 0; border: 3px solid #64748b; border-bottom: none; box-shadow: inset 0 -3px 5px rgba(0,0,0,0.1); opacity: 0.7;"></div>
									<div style="width: 80px; flex-grow: 1; background: linear-gradient(to right, #e2e8f0, #cbd5e1, #e2e8f0); border: 3px solid #64748b; border-top: none; border-radius: 0 0 12px 12px; position: relative; display: flex; flex-direction: column-reverse; align-items: center; padding: 0.5rem 0; box-shadow: inset -3px 0 8px rgba(0,0,0,0.1); opacity: 0.7;">
										{#each stocking as ballColor, ballIndex}
											<div style="width: 50px; height: 50px; border-radius: 50%; background: radial-gradient(circle at 30% 30%, {BALL_COLORS[ballColor]}cc, {BALL_COLORS[ballColor]}99); margin: 0.3rem 0; border: 3px solid rgba(0,0,0,0.15); box-shadow: 0 2px 4px rgba(0,0,0,0.1); opacity: 0.8;"></div>
										{/each}
									</div>
									<div style="position: absolute; bottom: -30px; width: 100%; text-align: center; font-size: 0.8rem; color: #64748b; font-weight: 600;">
										Stocking {stockingIndex + 1}
									</div>
								</div>
							{/each}
						</div>
					</div>
				</div>

				<div style="text-align: center;">
					<button on:click={startSolving}
						style="background: #22c55e; color: white; border: none; padding: 1rem 2rem; 
						font-size: 1.1rem; border-radius: 8px; cursor: pointer; font-weight: 600;">
						I'm Ready - Start Solving
					</button>
				</div>
			</div>

		{:else if gamePhase === 'solving'}
			<div style="background: white; border-radius: 16px; padding: 2rem; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
					<h2 style="color: #8b5cf6; margin: 0;">
						Problem {currentProblem.problem_number} of {sessionData.total_problems}
					</h2>
					<div style="display: flex; gap: 1rem; align-items: center;">
						<span style="background: #f5f3ff; color: #5b21b6; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 600; border: 2px solid #8b5cf6;">
							Moves: {totalMoves}
						</span>
						{#if currentProblem.show_minimum}
							<span style="background: #fef3c7; color: #92400e; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 600;">
								Target: {currentProblem.minimum_moves}
							</span>
						{/if}
						<button on:click={toggleGoalView}
							style="background: #8b5cf6; color: white; border: none; padding: 0.5rem 1rem; 
							border-radius: 8px; cursor: pointer; font-size: 0.9rem; transition: all 0.2s;"
							on:mouseenter={(e) => e.currentTarget.style.background = '#7c3aed'}
							on:mouseleave={(e) => e.currentTarget.style.background = '#8b5cf6'}>
							{showingGoal ? 'Hide' : 'Show'} Goal
						</button>
					</div>
				</div>

				{#if selectedBall !== null}
					<div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border: 2px solid #f59e0b; border-radius: 12px; padding: 1.2rem; text-align: center; margin-bottom: 1.5rem; box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);">
						<div style="display: flex; align-items: center; justify-content: center; gap: 0.8rem;">
							<div style="width: 40px; height: 40px; border-radius: 50%; background: radial-gradient(circle at 30% 30%, {BALL_COLORS[selectedBall.color]}ee, {BALL_COLORS[selectedBall.color]}); border: 3px solid #92400e; box-shadow: 0 4px 8px rgba(0,0,0,0.2), inset -3px -3px 6px rgba(0,0,0,0.2), inset 3px 3px 6px rgba(255,255,255,0.3);"></div>
							<strong style="color: #92400e; font-size: 1.1rem;">Click a stocking below to move this ball</strong>
						</div>
					</div>
				{/if}

				<div style="display: grid; grid-template-columns: {showingGoal ? '1fr 1fr' : '1fr'}; gap: 2rem; margin-bottom: 2rem;">
					<!-- Current State (Interactive) -->
					<div>
						<h3 style="text-align: center; color: #1e293b; margin-bottom: 1.5rem; font-weight: 600;">CURRENT POSITION</h3>
						<div style="display: flex; justify-content: center; gap: 3rem; align-items: flex-end; padding: 1rem;">
							{#each currentState as stocking, stockingIndex}
								<div style="position: relative; width: 100px; height: 380px; display: flex; flex-direction: column; align-items: center;">
									<!-- Clickable stocking area -->
									<button on:click={() => moveToStocking(stockingIndex)}
										aria-label="Move ball to stocking {stockingIndex + 1}"
										on:mouseenter={(e) => {
											if (selectedBall && selectedBall.stockingIndex !== stockingIndex) {
												e.currentTarget.style.background = stocking.length >= STOCKING_CAPACITIES[stockingIndex] ? 'rgba(239, 68, 68, 0.1)' : 'rgba(139, 92, 246, 0.15)';
											}
										}}
										on:mouseleave={(e) => e.currentTarget.style.background = 'transparent'}
										style="position: absolute; top: 0; left: 0; width: 100%; height: 350px; 
										background: transparent; 
										border: 3px dashed {selectedBall && selectedBall.stockingIndex !== stockingIndex ? (stocking.length >= STOCKING_CAPACITIES[stockingIndex] ? '#ef4444' : '#8b5cf6') : 'transparent'}; 
										border-radius: 12px; cursor: {selectedBall ? 'pointer' : 'default'}; z-index: 0;
										transition: all 0.3s ease;">
									</button>
									
									<!-- Stocking top (opening) -->
									<div style="width: 90px; height: 25px; background: linear-gradient(to bottom, #cbd5e1, #94a3b8); border-radius: 8px 8px 0 0; border: 3px solid #64748b; border-bottom: none; box-shadow: inset 0 -3px 5px rgba(0,0,0,0.1); z-index: 1;"></div>
									
									<!-- Stocking body -->
									<div style="width: 85px; flex-grow: 1; background: linear-gradient(to right, #e2e8f0, #cbd5e1, #e2e8f0); border: 3px solid #64748b; border-top: none; border-radius: 0 0 12px 12px; position: relative; display: flex; flex-direction: column-reverse; align-items: center; padding: 0.5rem 0; box-shadow: inset -3px 0 8px rgba(0,0,0,0.1); z-index: 1;">
										<!-- Balls stacked from bottom (interactive) -->
										{#each stocking as ballColor, ballIndex}
											{@const isTopBall = ballIndex === stocking.length - 1}
											{@const isSelected = selectedBall && selectedBall.stockingIndex === stockingIndex && selectedBall.ballIndex === ballIndex}
											{@const colorNames = ['red', 'blue', 'green']}
											<button on:click={() => selectBall(stockingIndex, ballIndex)}
												aria-label="{isTopBall ? 'Select' : 'Cannot select'} {colorNames[ballColor]} ball in stocking {stockingIndex + 1}"
												on:mouseenter={(e) => {
													if (isTopBall && !isSelected) {
														e.currentTarget.style.transform = 'scale(1.1) translateY(-5px)';
														e.currentTarget.style.boxShadow = '0 8px 16px rgba(0,0,0,0.3)';
													}
												}}
												on:mouseleave={(e) => {
													if (isTopBall && !isSelected) {
														e.currentTarget.style.transform = 'scale(1)';
														e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.2), inset -5px -5px 10px rgba(0,0,0,0.2), inset 5px 5px 10px rgba(255,255,255,0.3)';
													}
												}}
												disabled={!isTopBall}
												style="width: 52px; height: 52px; border-radius: 50%; 
												background: radial-gradient(circle at 30% 30%, {isSelected ? BALL_COLORS[ballColor] : BALL_COLORS[ballColor] + 'ee'}, {BALL_COLORS[ballColor]}); 
												margin: 0.3rem 0; 
												border: {isSelected ? '4px solid #fbbf24' : '3px solid rgba(0,0,0,0.2)'}; 
												box-shadow: {isSelected ? '0 0 0 5px rgba(251, 191, 36, 0.4), 0 8px 20px rgba(251, 191, 36, 0.3)' : '0 4px 8px rgba(0,0,0,0.2), inset -5px -5px 10px rgba(0,0,0,0.2), inset 5px 5px 10px rgba(255,255,255,0.3)'};
												cursor: {isTopBall ? 'pointer' : 'not-allowed'};
												opacity: {isTopBall ? '1' : '0.6'};
												transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
												filter: {isSelected ? 'brightness(1.15)' : 'none'};
												transform: {isSelected ? 'scale(1.1) translateY(-8px)' : 'scale(1)'};
												z-index: {ballIndex + 2};">
											</button>
										{/each}
									</div>
									
									<!-- Capacity indicator -->
									<div style="position: absolute; bottom: -35px; width: 100%; text-align: center;">
										<div style="display: inline-block; background: {stocking.length >= STOCKING_CAPACITIES[stockingIndex] ? '#fee2e2' : '#f5f3ff'}; 
											color: {stocking.length >= STOCKING_CAPACITIES[stockingIndex] ? '#991b1b' : '#5b21b6'}; 
											padding: 0.3rem 0.8rem; border-radius: 12px; font-size: 0.85rem; font-weight: 600;
											border: 2px solid {stocking.length >= STOCKING_CAPACITIES[stockingIndex] ? '#ef4444' : '#8b5cf6'};">
											{stocking.length}/{STOCKING_CAPACITIES[stockingIndex]}
											{#if stocking.length >= STOCKING_CAPACITIES[stockingIndex]}
												<span style="margin-left: 0.3rem;">🔒</span>
											{/if}
										</div>
									</div>
								</div>
							{/each}
						</div>
					</div>

					<!-- Goal State (Reference) -->
					{#if showingGoal}
						<div>
							<h3 style="text-align: center; color: #1e293b; margin-bottom: 1.5rem; font-weight: 600;">TARGET POSITION</h3>
							<div style="display: flex; justify-content: center; gap: 3rem; align-items: flex-end; padding: 1rem; opacity: 0.85;">
								{#each goalState as stocking, stockingIndex}
									<div style="position: relative; width: 100px; height: 380px; display: flex; flex-direction: column; align-items: center;">
										<div style="width: 90px; height: 25px; background: linear-gradient(to bottom, #cbd5e1, #94a3b8); border-radius: 8px 8px 0 0; border: 3px solid #94a3b8; border-bottom: none; opacity: 0.6;"></div>
										<div style="width: 85px; flex-grow: 1; background: linear-gradient(to right, #e2e8f0, #cbd5e1, #e2e8f0); border: 3px solid #94a3b8; border-top: none; border-radius: 0 0 12px 12px; display: flex; flex-direction: column-reverse; align-items: center; padding: 0.5rem 0; opacity: 0.6;">
											{#each stocking as ballColor, ballIndex}
												<div style="width: 50px; height: 50px; border-radius: 50%; background: radial-gradient(circle at 30% 30%, {BALL_COLORS[ballColor]}cc, {BALL_COLORS[ballColor]}99); margin: 0.3rem 0; border: 3px solid rgba(0,0,0,0.15); box-shadow: 0 2px 4px rgba(0,0,0,0.1); opacity: 0.8;"></div>
											{/each}
										</div>
										<div style="position: absolute; bottom: -35px; width: 100%; text-align: center; font-size: 0.75rem; color: #94a3b8; font-weight: 600;">
											Stocking {stockingIndex + 1}
										</div>
									</div>
								{/each}
							</div>
						</div>
					{/if}
				</div>
			</div>

		{:else if gamePhase === 'problem_complete'}
			<div style="background: white; border-radius: 16px; padding: 3rem; box-shadow: 0 20px 60px rgba(0,0,0,0.3); text-align: center;">
				<div style="font-size: 4rem; margin-bottom: 1rem;">✅</div>
				<h2 style="color: #22c55e; margin-bottom: 1rem;">Problem Solved!</h2>
				
				<div style="background: #f0fdf4; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem;">
					<div style="color: #166534; font-size: 1.1rem; line-height: 1.8;">
						<div><strong>Moves Used:</strong> {userSolutions[userSolutions.length - 1].moves_used}</div>
						{#if currentProblem.show_minimum}
							<div><strong>Minimum Required:</strong> {currentProblem.minimum_moves}</div>
							{#if userSolutions[userSolutions.length - 1].moves_used === currentProblem.minimum_moves}
								<div style="color: #15803d; font-weight: 700; margin-top: 0.5rem;">🎯 Perfect solution!</div>
							{/if}
						{/if}
					</div>
				</div>

				<button on:click={nextProblem}
					style="background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%); color: white; border: none; 
					padding: 1rem 2rem; font-size: 1.1rem; border-radius: 8px; cursor: pointer; font-weight: 600;">
					Next Problem →
				</button>
			</div>

		{:else if gamePhase === 'results'}
			<div style="background: white; border-radius: 16px; padding: 3rem; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				<div style="text-align: center; margin-bottom: 2rem;">
					<h1 style="font-size: 2.5rem; color: #8b5cf6; margin-bottom: 0.5rem;">Session Complete!</h1>
					<div style="font-size: 3rem; font-weight: 700; color: #8b5cf6; margin: 1rem 0;">
						Score: {results.score}/100
					</div>
				</div>

				<div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1.5rem; margin-bottom: 2rem;">
					<div style="background: #f5f3ff; border-radius: 12px; padding: 1.5rem; text-align: center; border: 2px solid #8b5cf6;">
						<div style="font-size: 2rem; font-weight: 700; color: #5b21b6;">
							{results.problems_solved}/{results.total_problems}
						</div>
						<div style="color: #64748b; margin-top: 0.5rem;">Problems Solved</div>
					</div>

					<div style="background: #f0fdf4; border-radius: 12px; padding: 1.5rem; text-align: center; border: 2px solid #22c55e;">
						<div style="font-size: 2rem; font-weight: 700; color: #15803d;">
							{results.perfect_solutions}
						</div>
						<div style="color: #64748b; margin-top: 0.5rem;">Perfect Solutions</div>
					</div>

					<div style="background: #fef3c7; border-radius: 12px; padding: 1.5rem; text-align: center; border: 2px solid #f59e0b;">
						<div style="font-size: 2rem; font-weight: 700; color: #92400e;">
							{Math.round(results.planning_efficiency * 100)}%
						</div>
						<div style="color: #64748b; margin-top: 0.5rem;">Planning Efficiency</div>
					</div>
				</div>

				<div style="background: #f8fafc; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem;">
					<h3 style="color: #1e293b; margin-bottom: 1rem;">Problem Breakdown</h3>
					<div style="display: grid; gap: 0.5rem;">
						{#each results.problems as problem}
							<div style="display: flex; justify-content: space-between; padding: 0.75rem; background: white; border-radius: 8px; border-left: 4px solid {problem.perfect ? '#22c55e' : problem.solved ? '#8b5cf6' : '#ef4444'};">
								<span style="color: #1e293b; font-weight: 600;">Problem {problem.problem_number}</span>
								<span style="color: #64748b;">
									{problem.moves_used} moves (min: {problem.minimum_moves})
									{#if problem.perfect}🎯{/if}
								</span>
							</div>
						{/each}
					</div>
				</div>

				<div style="text-align: center;">
					<button on:click={() => goto('/dashboard')}
						style="background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%); color: white; border: none; 
						padding: 1rem 2rem; font-size: 1.1rem; border-radius: 8px; cursor: pointer; font-weight: 600;">
						Return to Dashboard
					</button>
				</div>
			</div>
		{/if}

	</div>
</div>

{#if earnedBadges.length > 0}
	<BadgeNotification badges={earnedBadges} />
{/if}

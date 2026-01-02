<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
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
	let currentState = []; // Current disk positions [[disk_ids on peg 0], [peg 1], [peg 2]]
	let goalState = [];
	let selectedDisk = null; // {pegIndex, diskIndex, color}
	let moveHistory = [];
	let problemStartTime = null;
	let totalMoves = 0;
	
	// UI state
	let gamePhase = 'intro'; // intro, planning, solving, problem_complete, results
	let planningTimeRemaining = 0;
	let planningTimer = null;
	let userSolutions = [];
	let showingGoal = true;
	let results = null;
	let earnedBadges = [];

	// Colors for disks
	const DISK_COLORS = {
		0: '#ef4444', // red
		1: '#3b82f6', // blue
		2: '#22c55e'  // green
	};

	const PEG_CAPACITIES = [3, 2, 1];

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

			const response = await fetch('/api/tasks/tol/generate', {
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
		currentState = currentProblem.start_state.map(peg => [...peg]);
		goalState = currentProblem.goal_state.map(peg => [...peg]);
		
		selectedDisk = null;
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

	function selectDisk(pegIndex, diskIndex) {
		if (gamePhase !== 'solving') return;
		
		const peg = currentState[pegIndex];
		
		// Can only select top disk
		if (diskIndex !== peg.length - 1) return;
		
		if (selectedDisk) {
			// If same disk clicked, deselect
			if (selectedDisk.pegIndex === pegIndex && selectedDisk.diskIndex === diskIndex) {
				selectedDisk = null;
			}
		} else {
			// Select this disk
			const color = peg[diskIndex];
			selectedDisk = { pegIndex, diskIndex, color };
		}
	}

	function moveToPeg(targetPegIndex) {
		if (gamePhase !== 'solving' || !selectedDisk) return;
		
		const sourcePeg = currentState[selectedDisk.pegIndex];
		const targetPeg = currentState[targetPegIndex];
		
		// Can't move to same peg
		if (selectedDisk.pegIndex === targetPegIndex) {
			selectedDisk = null;
			return;
		}
		
		// Check capacity
		if (targetPeg.length >= PEG_CAPACITIES[targetPegIndex]) {
			alert(`Peg ${targetPegIndex + 1} is full!`);
			selectedDisk = null;
			return;
		}
		
		// Move the disk
		const disk = sourcePeg.pop();
		targetPeg.push(disk);
		
		totalMoves++;
		moveHistory.push({
			from: selectedDisk.pegIndex,
			to: targetPegIndex,
			disk: disk
		});
		
		selectedDisk = null;
		
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
		try {
			const response = await fetch('/api/tasks/tol/score', {
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
			const response = await fetch(`http://localhost:8000/api/training/tasks/soc/submit/${userId}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					session_data: {
						difficulty: difficulty,
						problems: sessionData?.problems || []
					},
					user_solutions: userSolutions,
					task_id: taskId
				})
			});

			if (!response.ok) throw new Error('Failed to save results');
			
			const data = await response.json();
			
			if (data.newly_earned_badges && data.newly_earned_badges.length > 0) {
				earnedBadges = data.newly_earned_badges;
			}
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

<div style="min-height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem;">
	<div style="max-width: 1000px; margin: 0 auto;">
		
		{#if gamePhase === 'intro'}
			<div style="background: white; border-radius: 16px; padding: 3rem; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				<div style="text-align: center; margin-bottom: 2rem;">
					<h1 style="font-size: 2.5rem; color: #667eea; margin-bottom: 0.5rem; font-weight: 700;">
						🎯 Tower of London
					</h1>
					<p style="font-size: 1.1rem; color: #64748b;">
						Executive Planning & Problem Solving
					</p>
				</div>

				<div style="background: #f8fafc; border-radius: 12px; padding: 2rem; margin-bottom: 2rem; border-left: 4px solid #667eea;">
					<h3 style="color: #1e293b; margin-bottom: 1rem; font-size: 1.3rem;">📋 How It Works</h3>
					<ul style="color: #475569; line-height: 1.8; margin-left: 1.5rem;">
						<li><strong>Planning Phase:</strong> Study the start and goal configurations</li>
						<li><strong>Mental Planning:</strong> Figure out the minimum moves needed</li>
						<li><strong>Execution:</strong> Move colored disks to match the goal</li>
						<li><strong>Constraints:</strong> Peg 1 holds 3 disks, Peg 2 holds 2, Peg 3 holds 1</li>
						<li><strong>Rule:</strong> Only move the top disk from each peg</li>
					</ul>
				</div>

				{#if sessionData}
					<div style="background: #eff6ff; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem; border: 2px solid #3b82f6;">
						<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
							<h3 style="color: #1e40af; margin: 0;">Current Session</h3>
							<span style="background: #3b82f6; color: white; padding: 0.4rem 1rem; border-radius: 20px; font-weight: 600;">
								Level {difficulty}
							</span>
						</div>
						<div style="color: #1e40af; line-height: 1.8;">
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
							style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; 
							padding: 1rem 3rem; font-size: 1.2rem; border-radius: 12px; cursor: pointer; font-weight: 600;
							box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4); transition: all 0.3s ease;">
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
					<h2 style="color: #667eea; margin-bottom: 0.5rem;">
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
						<div style="display: flex; justify-content: center; gap: 2rem; height: 300px; align-items: flex-end;">
							{#each currentProblem.start_state as peg, pegIndex}
								<div style="position: relative; width: 80px;">
									<!-- Peg base -->
									<div style="position: absolute; bottom: 0; width: 100%; height: 10px; background: #94a3b8; border-radius: 4px;"></div>
									<!-- Peg rod -->
									<div style="position: absolute; bottom: 10px; left: 50%; transform: translateX(-50%); width: 8px; height: 250px; background: #cbd5e1;"></div>
									<!-- Disks -->
									{#each peg as diskColor, diskIndex}
										<div style="position: absolute; bottom: {10 + diskIndex * 30}px; left: 50%; transform: translateX(-50%); 
											width: {60 - diskIndex * 8}px; height: 25px; background: {DISK_COLORS[diskColor]}; 
											border-radius: 4px; border: 2px solid rgba(0,0,0,0.2); z-index: {diskIndex + 1};"></div>
									{/each}
									<!-- Capacity label -->
									<div style="position: absolute; bottom: -30px; width: 100%; text-align: center; font-size: 0.8rem; color: #64748b;">
										Peg {pegIndex + 1} (max: {PEG_CAPACITIES[pegIndex]})
									</div>
								</div>
							{/each}
						</div>
					</div>

					<!-- Goal Configuration -->
					<div>
						<h3 style="text-align: center; color: #1e293b; margin-bottom: 1rem;">GOAL</h3>
						<div style="display: flex; justify-content: center; gap: 2rem; height: 300px; align-items: flex-end;">
							{#each currentProblem.goal_state as peg, pegIndex}
								<div style="position: relative; width: 80px;">
									<!-- Peg base -->
									<div style="position: absolute; bottom: 0; width: 100%; height: 10px; background: #94a3b8; border-radius: 4px;"></div>
									<!-- Peg rod -->
									<div style="position: absolute; bottom: 10px; left: 50%; transform: translateX(-50%); width: 8px; height: 250px; background: #cbd5e1;"></div>
									<!-- Disks -->
									{#each peg as diskColor, diskIndex}
										<div style="position: absolute; bottom: {10 + diskIndex * 30}px; left: 50%; transform: translateX(-50%); 
											width: {60 - diskIndex * 8}px; height: 25px; background: {DISK_COLORS[diskColor]}; 
											border-radius: 4px; border: 2px solid rgba(0,0,0,0.2); z-index: {diskIndex + 1};"></div>
									{/each}
									<!-- Capacity label -->
									<div style="position: absolute; bottom: -30px; width: 100%; text-align: center; font-size: 0.8rem; color: #64748b;">
										Peg {pegIndex + 1} (max: {PEG_CAPACITIES[pegIndex]})
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
					<h2 style="color: #667eea; margin: 0;">
						Problem {currentProblem.problem_number} of {sessionData.total_problems}
					</h2>
					<div style="display: flex; gap: 1rem; align-items: center;">
						<span style="background: #e0e7ff; color: #4338ca; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 600;">
							Moves: {totalMoves}
						</span>
						{#if currentProblem.show_minimum}
							<span style="background: #fef3c7; color: #92400e; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 600;">
								Target: {currentProblem.minimum_moves}
							</span>
						{/if}
						<button on:click={toggleGoalView}
							style="background: #3b82f6; color: white; border: none; padding: 0.5rem 1rem; 
							border-radius: 8px; cursor: pointer; font-size: 0.9rem; transition: all 0.2s;"
							on:mouseenter={(e) => e.currentTarget.style.background = '#2563eb'}
							on:mouseleave={(e) => e.currentTarget.style.background = '#3b82f6'}>
							{showingGoal ? 'Hide' : 'Show'} Goal
						</button>
					</div>
				</div>

				{#if selectedDisk !== null}
					<div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border: 2px solid #f59e0b; border-radius: 12px; padding: 1.2rem; text-align: center; margin-bottom: 1.5rem; box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);">
						<div style="display: flex; align-items: center; justify-content: center; gap: 0.8rem;">
							<div style="width: 50px; height: 25px; background: {DISK_COLORS[selectedDisk.color]}; border-radius: 4px; border: 3px solid #92400e; box-shadow: 0 2px 8px rgba(0,0,0,0.2);"></div>
							<strong style="color: #92400e; font-size: 1.1rem;">Click a peg below to move this disk</strong>
						</div>
					</div>
				{/if}

				<div style="display: grid; grid-template-columns: {showingGoal ? '1fr 1fr' : '1fr'}; gap: 2rem; margin-bottom: 2rem;">
					<!-- Current State (Interactive) -->
					<div>
						<h3 style="text-align: center; color: #1e293b; margin-bottom: 1.5rem; font-weight: 600;">CURRENT POSITION</h3>
						<div style="display: flex; justify-content: center; gap: 3rem; height: 320px; align-items: flex-end; padding: 0 1rem;">
							{#each currentState as peg, pegIndex}
								<div style="position: relative; width: 100px;">
									<!-- Clickable peg area with hover effect -->
									<button on:click={() => moveToPeg(pegIndex)}
										aria-label="Move disk to peg {pegIndex + 1}"
										on:mouseenter={(e) => {
											if (selectedDisk && selectedDisk.pegIndex !== pegIndex) {
												e.currentTarget.style.background = peg.length >= PEG_CAPACITIES[pegIndex] ? 'rgba(239, 68, 68, 0.1)' : 'rgba(59, 130, 246, 0.15)';
											}
										}}
										on:mouseleave={(e) => e.currentTarget.style.background = 'transparent'}
										style="position: absolute; top: 0; left: 0; width: 100%; height: 280px; 
										background: transparent; 
										border: 3px dashed {selectedDisk && selectedDisk.pegIndex !== pegIndex ? (peg.length >= PEG_CAPACITIES[pegIndex] ? '#ef4444' : '#3b82f6') : 'transparent'}; 
										border-radius: 12px; cursor: {selectedDisk ? 'pointer' : 'default'}; z-index: 0;
										transition: all 0.3s ease;">
									</button>
									
									<!-- Peg base with gradient -->
									<div style="position: absolute; bottom: 0; width: 100%; height: 12px; background: linear-gradient(to bottom, #94a3b8, #64748b); border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);"></div>
									
									<!-- Peg rod with 3D effect -->
									<div style="position: absolute; bottom: 12px; left: 50%; transform: translateX(-50%); width: 10px; height: 250px; background: linear-gradient(to right, #cbd5e1, #94a3b8, #cbd5e1); border-radius: 5px; box-shadow: inset -2px 0 4px rgba(0,0,0,0.1);"></div>
									
									<!-- Disks with improved styling -->
									{#each peg as diskColor, diskIndex}
										{@const isTopDisk = diskIndex === peg.length - 1}
										{@const isSelected = selectedDisk && selectedDisk.pegIndex === pegIndex && selectedDisk.diskIndex === diskIndex}
										{@const colorNames = ['red', 'blue', 'green']}
										<button on:click={() => selectDisk(pegIndex, diskIndex)}
											aria-label="{isTopDisk ? 'Select' : 'Cannot select'} {colorNames[diskColor]} disk on peg {pegIndex + 1}"
											on:mouseenter={(e) => {
												if (isTopDisk && !isSelected) {
													e.currentTarget.style.transform = 'translateX(-50%) translateY(-3px)';
													e.currentTarget.style.boxShadow = '0 6px 16px rgba(0,0,0,0.3)';
												}
											}}
											on:mouseleave={(e) => {
												if (isTopDisk && !isSelected) {
													e.currentTarget.style.transform = 'translateX(-50%)';
													e.currentTarget.style.boxShadow = isSelected ? '0 0 0 5px rgba(251, 191, 36, 0.4), 0 8px 20px rgba(251, 191, 36, 0.3)' : '0 4px 8px rgba(0,0,0,0.2)';
												}
											}}
											disabled={!isTopDisk}
											style="position: absolute; bottom: {12 + diskIndex * 32}px; left: 50%; transform: translateX(-50%) {isSelected ? 'translateY(-8px)' : ''}; 
											width: {70 - diskIndex * 10}px; height: 28px; 
											background: {isSelected ? DISK_COLORS[diskColor] : `linear-gradient(to bottom, ${DISK_COLORS[diskColor]}, ${DISK_COLORS[diskColor]}ee)`}; 
											border-radius: 6px; 
											border: {isSelected ? '4px solid #fbbf24' : '3px solid rgba(0,0,0,0.25)'}; 
											z-index: {diskIndex + 1}; 
											cursor: {isTopDisk ? 'pointer' : 'not-allowed'}; 
											opacity: {isTopDisk ? '1' : '0.7'};
											box-shadow: {isSelected ? '0 0 0 5px rgba(251, 191, 36, 0.4), 0 8px 20px rgba(251, 191, 36, 0.3)' : '0 4px 8px rgba(0,0,0,0.2)'};
											transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
											filter: {isSelected ? 'brightness(1.1)' : 'none'};">
										</button>
									{/each}
									
									<!-- Capacity indicator with dynamic color -->
									<div style="position: absolute; bottom: -35px; width: 100%; text-align: center;">
										<div style="display: inline-block; background: {peg.length >= PEG_CAPACITIES[pegIndex] ? '#fee2e2' : '#e0e7ff'}; 
											color: {peg.length >= PEG_CAPACITIES[pegIndex] ? '#991b1b' : '#3730a3'}; 
											padding: 0.3rem 0.8rem; border-radius: 12px; font-size: 0.85rem; font-weight: 600;
											border: 2px solid {peg.length >= PEG_CAPACITIES[pegIndex] ? '#ef4444' : '#6366f1'};">
											{peg.length}/{PEG_CAPACITIES[pegIndex]}
											{#if peg.length >= PEG_CAPACITIES[pegIndex]}
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
							<div style="display: flex; justify-content: center; gap: 3rem; height: 320px; align-items: flex-end; padding: 0 1rem; opacity: 0.85;">
								{#each goalState as peg, pegIndex}
									<div style="position: relative; width: 100px;">
										<div style="position: absolute; bottom: 0; width: 100%; height: 12px; background: linear-gradient(to bottom, #cbd5e1, #94a3b8); border-radius: 6px; opacity: 0.6;"></div>
										<div style="position: absolute; bottom: 12px; left: 50%; transform: translateX(-50%); width: 10px; height: 250px; background: linear-gradient(to right, #e2e8f0, #cbd5e1, #e2e8f0); border-radius: 5px; opacity: 0.5;"></div>
										{#each peg as diskColor, diskIndex}
											<div style="position: absolute; bottom: {12 + diskIndex * 32}px; left: 50%; transform: translateX(-50%); 
												width: {70 - diskIndex * 10}px; height: 28px; 
												background: linear-gradient(to bottom, {DISK_COLORS[diskColor]}cc, {DISK_COLORS[diskColor]}99); 
												border-radius: 6px; border: 3px solid rgba(0,0,0,0.15); z-index: {diskIndex + 1}; 
												opacity: 0.65; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"></div>
										{/each}
										<div style="position: absolute; bottom: -35px; width: 100%; text-align: center; font-size: 0.75rem; color: #94a3b8; font-weight: 600;">
											Peg {pegIndex + 1}
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
					style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; 
					padding: 1rem 2rem; font-size: 1.1rem; border-radius: 8px; cursor: pointer; font-weight: 600;">
					Next Problem →
				</button>
			</div>

		{:else if gamePhase === 'results'}
			<div style="background: white; border-radius: 16px; padding: 3rem; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				<div style="text-align: center; margin-bottom: 2rem;">
					<h1 style="font-size: 2.5rem; color: #667eea; margin-bottom: 0.5rem;">Session Complete!</h1>
					<div style="font-size: 3rem; font-weight: 700; color: #667eea; margin: 1rem 0;">
						Score: {results.score}/100
					</div>
				</div>

				<div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1.5rem; margin-bottom: 2rem;">
					<div style="background: #f0f9ff; border-radius: 12px; padding: 1.5rem; text-align: center; border: 2px solid #3b82f6;">
						<div style="font-size: 2rem; font-weight: 700; color: #1e40af;">
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
							<div style="display: flex; justify-content: space-between; padding: 0.75rem; background: white; border-radius: 8px; border-left: 4px solid {problem.perfect ? '#22c55e' : problem.solved ? '#3b82f6' : '#ef4444'};">
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
						style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; 
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

<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { tasks, training } from '$lib/api';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';
	
	let currentUser = null;
	let stage = 'intro'; // intro, test, results
	
	// Training mode variables
	let isTrainingMode = false;
	let trainingPlanId = null;
	let trainingDifficulty = 1;
	let taskId = null;
	let sessionComplete = false;
	let completedTasksCount = 0;
	let totalTasksCount = 4;
	
	// Tower of Hanoi state
	let towers = [[3, 2, 1], [], []]; // 3 disks on first tower
	let selectedTower = null;
	let moves = 0;
	let optimalMoves = 7; // 2^3 - 1 = 7 for 3 disks
	let startTime = 0;
	let firstMoveTime = 0;
	let planningTime = 0;
	let completed = false;
	
	user.subscribe(value => {
		currentUser = value;
		if (!value) {
			goto('/login');
		}
	});
	
	onMount(() => {
		const urlParams = new URLSearchParams(window.location.search);
		isTrainingMode = urlParams.get('training') === 'true';
		trainingPlanId = parseInt(urlParams.get('planId')) || null;
		trainingDifficulty = parseInt(urlParams.get('difficulty')) || 1;
		taskId = $page.url.searchParams.get('taskId');
		
		// Adjust difficulty: more disks for higher difficulty
		if (isTrainingMode && trainingDifficulty > 3) {
			// Keep 3 disks but can increase to 4-5 for very high difficulty
			if (trainingDifficulty >= 8) {
				// 5 disks = 31 optimal moves
				optimalMoves = 31;
			} else if (trainingDifficulty >= 6) {
				// 4 disks = 15 optimal moves
				optimalMoves = 15;
			}
		}
	});
	
	function backToDashboard() {
		if (isTrainingMode) {
			goto('/training');
		} else {
			goto('/dashboard');
		}
	}
	
	function startTest() {
		stage = 'test';
		towers = [[3, 2, 1], [], []];
		selectedTower = null;
		moves = 0;
		startTime = Date.now();
		firstMoveTime = 0;
	}
	
	function selectTower(index) {
		if (completed) return;
		
		if (selectedTower === null) {
			// Select source tower (must have disks)
			if (towers[index].length > 0) {
				selectedTower = index;
			}
		} else {
			// Move disk
			if (selectedTower !== index) {
				const disk = towers[selectedTower][towers[selectedTower].length - 1];
				const targetTop = towers[index][towers[index].length - 1];
				
				// Can only place smaller disk on larger disk or empty tower
				if (!targetTop || disk < targetTop) {
					// Valid move
					towers[selectedTower] = towers[selectedTower].slice(0, -1);
					towers[index] = [...towers[index], disk];
					moves++;
					
					// Record first move time (planning time)
					if (moves === 1) {
						firstMoveTime = Date.now();
						planningTime = firstMoveTime - startTime;
					}
					
					// Check if completed
					if (towers[2].length === 3) {
						completed = true;
						calculateResults();
					}
				}
			}
			selectedTower = null;
		}
	}
	
	function calculateResults() {
		const totalTime = Date.now() - startTime;
		
		stage = 'results';
		saveResults(totalTime);
	}
	
	async function saveResults(totalTime) {
		try {
			const excessMoves = moves - optimalMoves;
			const efficiency = Math.max(0, 100 - (excessMoves * 10));
			
			console.log('[Planning] Saving results:', {
				isTrainingMode,
				trainingPlanId,
				userId: currentUser?.id,
				efficiency
			});
			
			if (isTrainingMode && trainingPlanId) {
				// Submit to training session API
				console.log('[Planning] Submitting to training API');
				
				const result = await training.submitSession({
					user_id: currentUser.id,
					training_plan_id: trainingPlanId,
					domain: 'planning',
					task_type: 'tower_of_hanoi',
					score: efficiency,
					accuracy: completed ? 100 : 0,
					average_reaction_time: planningTime,
					consistency: Math.max(0, 100 - excessMoves * 5),
					errors: excessMoves,
					session_duration: Math.round(totalTime / 60000), // minutes
					task_id: taskId
				});
				
				sessionComplete = result.session_complete;
				completedTasksCount = result.completed_tasks;
				totalTasksCount = result.total_tasks;
				
				console.log('[Planning] Training session saved:', result);
			} else {
				// Submit to regular task result API (baseline mode)
				await tasks.submitResult(
					currentUser.id,
					'planning',
					efficiency,
					JSON.stringify({
						moves_taken: moves,
						optimal_moves: optimalMoves,
						excess_moves: excessMoves,
						planning_time_ms: planningTime,
						total_time_seconds: Math.round(totalTime / 1000),
						completed: completed
					})
				);
			}
		} catch (error) {
			console.error('Error saving results:', error);
		}
	}
	
	function resetTest() {
		towers = [[3, 2, 1], [], []];
		selectedTower = null;
		moves = 0;
		completed = false;
		startTime = Date.now();
		firstMoveTime = 0;
	}
	
	function getDiskColor(size) {
		const colors = ['#4caf50', '#2196f3', '#ff9800'];
		return colors[size - 1];
	}
</script>

<div class="test-container">
	{#if stage === 'intro'}
		<div class="test-card">
			<h1>Planning Test</h1>
			<h2 style="color: #666; font-size: 20px; margin-bottom: 30px;">Tower of Hanoi</h2>
			
			<div style="text-align: left; max-width: 600px; margin: 0 auto;">
				<h3 style="color: #667eea; margin-bottom: 15px;">Instructions:</h3>
				<ul style="line-height: 1.8; color: #666;">
					<li>Move all disks from the first tower to the third tower</li>
					<li>You can only move one disk at a time</li>
					<li>A larger disk cannot be placed on a smaller disk</li>
					<li>Try to complete in <strong>minimum moves ({optimalMoves})</strong></li>
					<li>Think before you move - planning is key!</li>
				</ul>
				
				<div style="background: #f0f7ff; padding: 20px; border-radius: 8px; margin-top: 30px;">
					<h4 style="color: #667eea; margin-bottom: 10px;">How to Play:</h4>
					<p style="color: #666; line-height: 1.6;">
						1. Click on a tower to pick up the top disk<br>
						2. Click on another tower to place it<br>
						3. Goal: Get all disks on the rightmost tower
					</p>
				</div>
			</div>
			
			<button class="btn-primary" on:click={startTest} style="margin-top: 40px;">
				Start Test
			</button>
			<button class="btn-secondary" on:click={backToDashboard}>
				Back to Dashboard
			</button>
		</div>
	
	{:else if stage === 'test'}
		<div class="test-card">
			<div style="display: flex; justify-content: space-between; margin-bottom: 30px;">
				<div class="timer">Moves: {moves} / {optimalMoves}</div>
				<button class="btn-secondary" on:click={resetTest} style="padding: 8px 20px; font-size: 14px;">
					Reset
				</button>
			</div>
			
			<!-- Towers Display -->
			<div style="display: flex; justify-content: center; gap: 40px; margin: 60px 0;">
				{#each towers as tower, index}
					<div 
						class="tower"
						class:selected={selectedTower === index}
						on:click={() => selectTower(index)}
						style="cursor: pointer; width: 150px;"
					>
						<!-- Tower pole -->
						<div style="width: 10px; height: 180px; background: #999; margin: 0 auto; position: relative;">
							<!-- Base -->
							<div style="width: 150px; height: 10px; background: #666; position: absolute; bottom: -10px; left: -70px;"></div>
							
							<!-- Disks -->
							<div style="position: absolute; bottom: 0; width: 150px; left: -70px; display: flex; flex-direction: column-reverse; align-items: center; gap: 2px;">
								{#each tower as disk}
									<div 
										style="
											width: {disk * 40}px; 
											height: 25px; 
											background: {getDiskColor(disk)}; 
											border-radius: 5px;
											border: 2px solid #333;
											display: flex;
											align-items: center;
											justify-content: center;
											color: white;
											font-weight: bold;
										"
									>
										{disk}
									</div>
								{/each}
							</div>
						</div>
						
						<div style="text-align: center; margin-top: 20px; color: #666; font-weight: 600;">
							Tower {index + 1}
						</div>
					</div>
				{/each}
			</div>
			
			{#if selectedTower !== null}
				<p style="color: #667eea; font-weight: 600; margin-top: 20px;">
					Selected Tower {selectedTower + 1} - Click another tower to move
				</p>
			{/if}
			
			{#if completed}
				<div style="margin-top: 30px; padding: 20px; background: #4caf50; color: white; border-radius: 8px;">
					<h3>🎉 Puzzle Completed!</h3>
					<p>Calculating results...</p>
				</div>
			{/if}
		</div>
	
	{:else if stage === 'results'}
		<div class="test-card">
			<h1>Test Complete!</h1>
			
			{#if isTrainingMode}
				<div class="training-progress-banner">
					{#if sessionComplete}
						<div class="session-complete-msg">
							🎉 Session Complete! You've finished all 4 tasks for this session.
						</div>
					{:else}
						<div style="margin-bottom: 10px; color: #667eea; font-weight: 600;">
							Training Progress: {completedTasksCount} / {totalTasksCount} tasks completed
						</div>
						<div style="font-size: 14px; color: #666;">
							Continue with the remaining tasks to complete this session
						</div>
					{/if}
				</div>
			{/if}
			
			<div class="score-display">
				{Math.max(0, 100 - ((moves - optimalMoves) * 10)).toFixed(0)}%
			</div>
			
			<div class="result-details">
				<p>
					<span>Moves Taken:</span>
					<strong>{moves}</strong>
				</p>
				<p>
					<span>Optimal Moves:</span>
					<strong>{optimalMoves}</strong>
				</p>
				<p>
					<span>Excess Moves:</span>
					<strong>{moves - optimalMoves}</strong>
				</p>
				<p>
					<span>Planning Time:</span>
					<strong>{(planningTime / 1000).toFixed(1)}s</strong>
				</p>
				<p>
					<span>Completed:</span>
					<strong>{completed ? 'Yes' : 'No'}</strong>
				</p>
			</div>
			
			<div style="margin-top: 30px; padding: 20px; background: #f5f5f5; border-radius: 8px;">
				<h4 style="color: #667eea; margin-bottom: 10px;">Planning Insights:</h4>
				<p style="color: #666; line-height: 1.6;">
					{#if moves === optimalMoves}
						Perfect! You solved it with optimal efficiency. Excellent planning skills!
					{:else if moves <= optimalMoves + 3}
						Great planning! You're close to the optimal solution.
					{:else}
						Keep practicing. Planning ahead can help reduce unnecessary moves.
					{/if}
				</p>
				{#if planningTime > 30000}
					<p style="color: #ff9800; margin-top: 10px;">
						💡 Tip: Long planning time detected. Sometimes thinking through the entire sequence helps!
					</p>
				{/if}
			</div>
			
			<div style="margin-top: 40px;">
				<button class="btn-primary" on:click={backToDashboard}>
					Back to Dashboard
				</button>
			</div>
		</div>
	{/if}
</div>

<style>
	.training-progress-banner {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		padding: 20px;
		border-radius: 12px;
		margin-bottom: 25px;
		text-align: center;
		box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
	}
	
	.session-complete-msg {
		font-size: 18px;
		font-weight: 600;
		animation: celebration 0.5s ease-out;
	}
	
	@keyframes celebration {
		0% { transform: scale(0.9); opacity: 0; }
		50% { transform: scale(1.05); }
		100% { transform: scale(1); opacity: 1; }
	}
	
	.tower {
		transition: all 0.2s;
	}
	
	.tower:hover {
		transform: translateY(-5px);
	}
	
	.tower.selected {
		background: rgba(102, 126, 234, 0.1);
		border-radius: 10px;
		padding: 10px;
		margin: -10px;
	}
</style>

<svelte:head>
	<title>Planning Test - NeuroBloom</title>
</svelte:head>

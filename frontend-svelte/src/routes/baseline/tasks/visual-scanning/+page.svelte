<script>
	import { goto } from '$app/navigation';
	import { tasks, training } from '$lib/api';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';
	
	let currentUser = null;
	let stage = 'intro'; // intro, test, results
	
	// Training mode variables
	let isTrainingMode = false;
	let trainingPlanId = null;
	let trainingDifficulty = 1;
	let sessionComplete = false;
	let completedTasksCount = 0;
	let totalTasksCount = 4;
	
	// Test parameters
	let gridSize = 10; // 10x10 grid
	let totalTargets = 5; // 5 "T"s to find
	let grid = [];
	let foundTargets = [];
	let startTime = 0;
	let endTime = 0;
	let searchTime = 0;
	
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
		
		// Adjust difficulty: larger grid for higher difficulty
		if (isTrainingMode && trainingDifficulty > 3) {
			gridSize = 10 + (trainingDifficulty - 3); // 10-17 grid
			totalTargets = 5 + Math.floor((trainingDifficulty - 3) / 2); // 5-8 targets
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
		generateGrid();
		startTime = Date.now();
	}
	
	function generateGrid() {
		grid = [];
		const distractors = ['L', 'I', 'F', 'E', 'P'];
		const positions = [];
		
		// Initialize with distractors
		for (let i = 0; i < gridSize * gridSize; i++) {
			grid.push({
				letter: distractors[Math.floor(Math.random() * distractors.length)],
				isTarget: false,
				found: false
			});
			positions.push(i);
		}
		
		// Place targets randomly
		for (let i = 0; i < totalTargets; i++) {
			const randomIndex = Math.floor(Math.random() * positions.length);
			const pos = positions.splice(randomIndex, 1)[0];
			grid[pos] = {
				letter: 'T',
				isTarget: true,
				found: false
			};
		}
	}
	
	function handleCellClick(index) {
		if (grid[index].isTarget && !grid[index].found) {
			// Correct target found
			grid[index].found = true;
			foundTargets = [...foundTargets, index];
			
			// Check if all targets found
			if (foundTargets.length === totalTargets) {
				endTime = Date.now();
				searchTime = endTime - startTime;
				calculateResults();
			}
		}
	}
	
	function calculateResults() {
		stage = 'results';
		saveResults();
	}
	
	async function saveResults() {
		try {
			const timePerTarget = searchTime / foundTargets.length;
			const accuracy = (foundTargets.length / totalTargets) * 100;
			const scanEfficiency = (totalTargets / (searchTime / 1000)) * 10; // Targets per 10 seconds
			
			console.log('[Visual Scanning] Saving results:', {
				isTrainingMode,
				trainingPlanId,
				userId: currentUser?.id,
				accuracy
			});
			
			if (isTrainingMode && trainingPlanId) {
				// Submit to training session API
				console.log('[Visual Scanning] Submitting to training API');
				
				const result = await training.submitSession({
					user_id: currentUser.id,
					training_plan_id: trainingPlanId,
					domain: 'visual_scanning',
					task_type: 'target_search',
					score: accuracy,
					accuracy: accuracy,
					average_reaction_time: timePerTarget,
					consistency: Math.max(0, 100 - (timePerTarget / 100)),
					errors: totalTargets - foundTargets.length,
					session_duration: Math.round(searchTime / 60000) // minutes
				});
				
				sessionComplete = result.session_complete;
				completedTasksCount = result.completed_tasks;
				totalTasksCount = result.total_tasks;
				
				console.log('[Visual Scanning] Training session saved:', result);
			} else {
				// Submit to regular task result API (baseline mode)
				await tasks.submitResult(
					currentUser.id,
					'visual_scanning',
					accuracy,
					JSON.stringify({
						targets_total: totalTargets,
						targets_found: foundTargets.length,
						missed_targets: totalTargets - foundTargets.length,
						search_time_ms: searchTime,
						time_per_target: timePerTarget,
						scan_efficiency: scanEfficiency
					})
				);
			}
		} catch (error) {
			console.error('Error saving results:', error);
		}
	}
</script>

<div class="test-container">
	{#if stage === 'intro'}
		<div class="test-card">
			<h1>Visual Scanning Test</h1>
			<h2 style="color: #666; font-size: 20px; margin-bottom: 30px;">Visual Search Task</h2>
			
			<div style="text-align: left; max-width: 600px; margin: 0 auto;">
				<h3 style="color: #667eea; margin-bottom: 15px;">Instructions:</h3>
				<ul style="line-height: 1.8; color: #666;">
					<li>You'll see a grid of letters (L, I, F, E, P, T)</li>
					<li>Find and click ALL the letter <strong style="color: #4caf50; font-size: 24px;">"T"</strong></li>
					<li>There are <strong>{totalTargets} targets</strong> hidden in the grid</li>
					<li>Work as quickly and accurately as possible</li>
					<li>Timer starts when the grid appears</li>
				</ul>
				
				<div style="background: #f0f7ff; padding: 20px; border-radius: 8px; margin-top: 30px;">
					<h4 style="color: #667eea; margin-bottom: 10px;">What to Look For:</h4>
					<div style="display: flex; justify-content: center; gap: 30px; margin-top: 15px;">
						<div>
							<p style="color: #4caf50; font-size: 48px; font-weight: bold; margin: 0;">T</p>
							<p style="color: #666; font-size: 14px;">FIND THIS</p>
						</div>
						<div>
							<p style="color: #999; font-size: 48px; font-weight: bold; margin: 0;">L I F E P</p>
							<p style="color: #666; font-size: 14px;">IGNORE THESE</p>
						</div>
					</div>
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
			<div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
				<div class="timer">
					Targets Found: {foundTargets.length} / {totalTargets}
				</div>
				<div class="timer">
					Time: {((Date.now() - startTime) / 1000).toFixed(1)}s
				</div>
			</div>
			
			<!-- Grid -->
			<div style="
				display: grid; 
				grid-template-columns: repeat({gridSize}, 1fr); 
				gap: 5px; 
				max-width: 600px; 
				margin: 30px auto;
				padding: 20px;
				background: #f5f5f5;
				border-radius: 10px;
			">
				{#each grid as cell, index}
					<div
						on:click={() => handleCellClick(index)}
						style="
							width: 50px;
							height: 50px;
							display: flex;
							align-items: center;
							justify-content: center;
							background: {cell.found ? '#4caf50' : 'white'};
							color: {cell.found ? 'white' : '#333'};
							font-size: 24px;
							font-weight: bold;
							border: 2px solid #ddd;
							border-radius: 4px;
							cursor: pointer;
							transition: all 0.2s;
							font-family: monospace;
						"
						class="grid-cell"
					>
						{cell.letter}
					</div>
				{/each}
			</div>
			
			<p style="color: #666; margin-top: 20px;">
				Click on all the letter "T" in the grid
			</p>
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
				{((foundTargets.length / totalTargets) * 100).toFixed(0)}%
			</div>
			
			<div class="result-details">
				<p>
					<span>Targets Found:</span>
					<strong>{foundTargets.length} / {totalTargets}</strong>
				</p>
				<p>
					<span>Missed Targets:</span>
					<strong>{totalTargets - foundTargets.length}</strong>
				</p>
				<p>
					<span>Total Search Time:</span>
					<strong>{(searchTime / 1000).toFixed(1)}s</strong>
				</p>
				<p>
					<span>Time Per Target:</span>
					<strong>{(searchTime / foundTargets.length / 1000).toFixed(2)}s</strong>
				</p>
				<p>
					<span>Scan Efficiency:</span>
					<strong>{((totalTargets / (searchTime / 1000)) * 10).toFixed(1)} targets/10s</strong>
				</p>
			</div>
			
			<div style="margin-top: 30px; padding: 20px; background: #f5f5f5; border-radius: 8px;">
				<h4 style="color: #667eea; margin-bottom: 10px;">Visual Scanning Insights:</h4>
				<p style="color: #666; line-height: 1.6;">
					{#if foundTargets.length === totalTargets && searchTime < 15000}
						Excellent visual scanning! Fast and accurate detection.
					{:else if foundTargets.length === totalTargets}
						Good accuracy! With practice, you can improve your speed.
					{:else}
						Keep practicing. Systematic scanning strategies can help find all targets.
					{/if}
				</p>
				{#if searchTime / foundTargets.length > 3000}
					<p style="color: #ff9800; margin-top: 10px;">
						💡 Tip: Try scanning row by row or column by column for more efficiency.
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
	
	.grid-cell:hover {
		transform: scale(1.1);
		border-color: #667eea;
	}
</style>

<svelte:head>
	<title>Visual Scanning Test - NeuroBloom</title>
</svelte:head>

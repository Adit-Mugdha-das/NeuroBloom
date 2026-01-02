<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { tasks, training } from '$lib/api';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';
	
	let currentUser = null;
	let stage = 'intro'; // intro, test, results
	let currentTrial = 0;
	let totalTrials = 60; // 1 minute test
	
	// Training mode variables
	let isTrainingMode = false;
	let trainingPlanId = null;
	let trainingDifficulty = 1;
	let taskId = null;
	let sessionComplete = false;
	let completedTasksCount = 0;
	let totalTasksCount = 4;
	
	// Test data
	let letters = [];
	let currentLetter = '';
	let previousLetter = '';
	let responses = [];
	let reactionTimes = [];
	
	// Results
	let targetsShown = 0;
	let targetsHit = 0;
	let misses = 0;
	let falseAlarms = 0;
	let accuracy = 0;
	let meanRT = 0;
	
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
		
		// Adjust difficulty: more trials for higher difficulty
		if (isTrainingMode && trainingDifficulty > 3) {
			totalTrials = 60 + (trainingDifficulty - 3) * 10; // 60-130 trials
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
		generateSequence();
		showNextTrial();
	}
	
	function generateSequence() {
		const letterPool = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'K', 'L', 'M', 'N', 'P', 'R', 'S', 'T', 'X'];
		letters = [];
		
		// Generate sequence with ~20% AX patterns
		for (let i = 0; i < totalTrials; i++) {
			if (i > 0 && letters[i - 1] === 'A' && Math.random() < 0.7) {
				letters.push('X');
			} else if (Math.random() < 0.15) {
				letters.push('A');
			} else {
				const otherLetters = letterPool.filter(l => l !== 'A' && l !== 'X');
				letters.push(otherLetters[Math.floor(Math.random() * otherLetters.length)]);
			}
		}
	}
	
	let trialStartTime = 0;
	let timeout;
	
	function showNextTrial() {
		if (currentTrial >= totalTrials) {
			calculateResults();
			return;
		}
		
		previousLetter = currentTrial > 0 ? letters[currentTrial - 1] : '';
		currentLetter = letters[currentTrial];
		trialStartTime = Date.now();
		
		// Auto-advance after 1 second
		timeout = setTimeout(() => {
			if (responses.length === currentTrial) {
				// User didn't respond
				responses.push(false);
				reactionTimes.push(1000);
			}
			currentTrial++;
			showNextTrial();
		}, 1000);
	}
	
	function handleClick() {
		if (responses.length > currentTrial) return; // Already responded
		
		clearTimeout(timeout);
		const rt = Date.now() - trialStartTime;
		responses.push(true);
		reactionTimes.push(rt);
		
		// Continue immediately
		currentTrial++;
		showNextTrial();
	}
	
	function calculateResults() {
		targetsShown = 0;
		targetsHit = 0;
		misses = 0;
		falseAlarms = 0;
		
		for (let i = 0; i < totalTrials; i++) {
			const isTarget = i > 0 && letters[i - 1] === 'A' && letters[i] === 'X';
			const userClicked = responses[i];
			
			if (isTarget) {
				targetsShown++;
				if (userClicked) {
					targetsHit++;
				} else {
					misses++;
				}
			} else if (userClicked) {
				falseAlarms++;
			}
		}
		
		accuracy = targetsShown > 0 ? (targetsHit / targetsShown) * 100 : 0;
		
		const validRTs = reactionTimes.filter((rt, i) => {
			const isTarget = i > 0 && letters[i - 1] === 'A' && letters[i] === 'X';
			return isTarget && rt < 1000;
		});
		meanRT = validRTs.length > 0 ? validRTs.reduce((a, b) => a + b, 0) / validRTs.length : 0;
		
		stage = 'results';
		saveResults();
	}
	
	async function saveResults() {
		try {
			const rtStd = calculateStd(reactionTimes.filter(rt => rt < 1000));
			
			// Calculate vigilance (performance over time)
			const firstHalf = responses.slice(0, totalTrials / 2).filter(r => r).length;
			const secondHalf = responses.slice(totalTrials / 2).filter(r => r).length;
			const vigilanceDecrement = firstHalf > 0 ? ((firstHalf - secondHalf) / firstHalf) : 0;
			
			console.log('[Attention] Saving results:', {
				isTrainingMode,
				trainingPlanId,
				userId: currentUser?.id,
				accuracy
			});
			
			if (isTrainingMode && trainingPlanId) {
				// Submit to training session API
				console.log('[Attention] Submitting to training API');
				
				const result = await training.submitSession({
					user_id: currentUser.id,
					training_plan_id: trainingPlanId,
					domain: 'attention',
					task_type: 'continuous_performance',
					score: accuracy,
					accuracy: accuracy,
					average_reaction_time: meanRT,
					consistency: rtStd > 0 ? Math.max(0, 100 - rtStd) : 100,
					errors: misses + falseAlarms,
					session_duration: totalTrials / 60, // approximate minutes
					task_id: taskId
				});
				
				sessionComplete = result.session_complete;
				completedTasksCount = result.completed_tasks;
				totalTasksCount = result.total_tasks;
				
				console.log('[Attention] Training session saved:', result);
			} else {
				// Submit to regular task result API (baseline mode)
				await tasks.submitResult(
					currentUser.id,
					'attention',
					accuracy,
					JSON.stringify({
						targets_shown: targetsShown,
						targets_hit: targetsHit,
						misses,
						false_alarms: falseAlarms,
						mean_rt: meanRT,
						rt_std: rtStd,
						vigilance_decrement: vigilanceDecrement,
						total_trials: totalTrials
					})
				);
			}
		} catch (error) {
			console.error('Error saving results:', error);
		}
	}
	
	function calculateStd(arr) {
		if (arr.length === 0) return 0;
		const mean = arr.reduce((a, b) => a + b, 0) / arr.length;
		const variance = arr.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / arr.length;
		return Math.sqrt(variance);
	}
</script>

<div class="test-container">
	{#if stage === 'intro'}
		<div class="test-card">
			<h1>Attention Test</h1>
			<h2 style="color: #666; font-size: 20px; margin-bottom: 30px;">Continuous Performance Test (CPT)</h2>
			
			<div style="text-align: left; max-width: 600px; margin: 0 auto;">
				<h3 style="color: #667eea; margin-bottom: 15px;">Instructions:</h3>
				<ul style="line-height: 1.8; color: #666;">
					<li>Letters will appear rapidly on screen (1 per second)</li>
					<li><strong>Click ONLY</strong> when you see <strong>X after A</strong> (the AX sequence)</li>
					<li>Do NOT click for any other letter or combination</li>
					<li>Stay focused for the entire duration</li>
					<li>Total duration: ~1 minute ({totalTrials} trials)</li>
				</ul>
				
				<div style="background: #f0f7ff; padding: 20px; border-radius: 8px; margin-top: 30px;">
					<h4 style="color: #667eea; margin-bottom: 10px;">Example:</h4>
					<p style="color: #666;">Sequence: B → A → <strong style="color: #4caf50;">X</strong> ← CLICK HERE</p>
					<p style="color: #666;">Sequence: A → B → X ← DON'T CLICK (not AX)</p>
					<p style="color: #666;">Sequence: A → <strong style="color: #f44336;">K</strong> ← DON'T CLICK</p>
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
			<div class="timer">
				Trial {currentTrial + 1} / {totalTrials}
			</div>
			
			<div class="attention-area">
				<div class="letter-box">
					<div class="previous-letter">Previous: {previousLetter || '–'}</div>
					<div class="current-letter">{currentLetter}</div>
				</div>
				
				<button 
					class="click-button" 
					on:click={handleClick}
				>
					CLICK IF X AFTER A
				</button>
			</div>
			
			<p style="color: #999; margin-top: 20px; font-size: 14px;">
				{#if previousLetter === 'A'}
					<strong style="color: #ff9800;">⚠️ Previous was A - Click button if current is X!</strong>
				{:else}
					Click the button ONLY when you see X after A
				{/if}
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
				{accuracy.toFixed(1)}%
			</div>
			
			<div class="result-details">
				<p>
					<span>Targets Shown (AX):</span>
					<strong>{targetsShown}</strong>
				</p>
				<p>
					<span>Targets Hit:</span>
					<strong>{targetsHit}</strong>
				</p>
				<p>
					<span>Misses:</span>
					<strong>{misses}</strong>
				</p>
				<p>
					<span>False Alarms:</span>
					<strong>{falseAlarms}</strong>
				</p>
				<p>
					<span>Average Reaction Time:</span>
					<strong>{meanRT.toFixed(0)}ms</strong>
				</p>
			</div>
			
			<div style="margin-top: 30px; padding: 20px; background: #f5f5f5; border-radius: 8px;">
				<h4 style="color: #667eea; margin-bottom: 10px;">Performance Interpretation:</h4>
				<p style="color: #666; line-height: 1.6;">
					{#if accuracy >= 80}
						Excellent sustained attention! You maintained focus throughout the task.
					{:else if accuracy >= 60}
						Good performance. Continue practicing to improve consistency.
					{:else}
						Keep practicing. Sustained attention improves with regular training.
					{/if}
				</p>
			</div>
			
			<div style="margin-top: 40px;">
				<button class="btn-primary" on:click={backToDashboard}>
					Back to Dashboard
				</button>
			</div>
		</div>
	{/if}
</div>

<svelte:head>
	<title>Attention Test - NeuroBloom</title>
</svelte:head>

<style>
	.test-container {
		min-height: 100vh;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 2rem;
	}
	
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
	
	.test-card {
		background: white;
		border-radius: 20px;
		padding: 3rem;
		max-width: 800px;
		width: 100%;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
		text-align: center;
	}
	
	.timer {
		font-size: 1.1rem;
		color: #667eea;
		font-weight: 600;
		margin-bottom: 2rem;
	}
	
	.attention-area {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 2rem;
		margin: 2rem 0;
	}
	
	.letter-box {
		background: #f8f9fa;
		border-radius: 16px;
		padding: 2rem;
		min-width: 300px;
		border: 3px solid #e0e0e0;
	}
	
	.previous-letter {
		font-size: 1rem;
		color: #999;
		margin-bottom: 1rem;
	}
	
	.current-letter {
		font-size: 6rem;
		font-weight: bold;
		color: #333;
		font-family: monospace;
		margin: 1rem 0;
	}
	
	.click-button {
		background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
		color: white;
		border: none;
		padding: 1.5rem 3rem;
		border-radius: 12px;
		font-size: 1.2rem;
		font-weight: bold;
		cursor: pointer;
		transition: all 0.3s;
		box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
	}
	
	.click-button:hover {
		transform: translateY(-2px);
		box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
	}
	
	.click-button:active {
		transform: translateY(0);
	}
	
	.btn-primary {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		padding: 1rem 2.5rem;
		border-radius: 12px;
		font-size: 1.1rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s;
		margin: 0.5rem;
	}
	
	.btn-primary:hover {
		transform: translateY(-2px);
		box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
	}
	
	.btn-secondary {
		background: #f5f5f5;
		color: #666;
		border: 2px solid #ddd;
		padding: 1rem 2.5rem;
		border-radius: 12px;
		font-size: 1.1rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s;
		margin: 0.5rem;
	}
	
	.btn-secondary:hover {
		background: #ececec;
		border-color: #ccc;
	}
	
	.score-display {
		font-size: 4rem;
		font-weight: bold;
		color: #4caf50;
		margin: 2rem 0;
	}
	
	.result-details {
		text-align: left;
		max-width: 500px;
		margin: 2rem auto;
	}
	
	.result-details p {
		display: flex;
		justify-content: space-between;
		padding: 0.75rem 1rem;
		border-bottom: 1px solid #f0f0f0;
		color: #666;
	}
	
	.result-details strong {
		color: #333;
		font-weight: 600;
	}
</style>

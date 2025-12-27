<script>
	import { goto } from '$app/navigation';
	import { tasks, training } from '$lib/api';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';
	
	let currentUser = null;
	let stage = 'intro'; // intro, simple, choice, results
	
	// Training mode tracking
	let isTrainingMode = false;
	let trainingPlanId = null;
	let trainingDifficulty = 1;
	let sessionComplete = false;
	let completedTasksCount = 0;
	let totalTasksCount = 4;
	
	// Simple RT test
	let simpleTrials = 10;
	let simpleCurrentTrial = 0;
	let simpleRTs = [];
	let simpleWaiting = false;
	let simpleReady = false;
	let simpleStartTime = 0;
	let simpleTimeout;
	
	// Choice RT test
	let choiceTrials = 15;
	let choiceCurrentTrial = 0;
	let choiceRTs = [];
	let choiceAccuracy = [];
	let choiceStimuli = [];
	let choiceCurrentShape = '';
	let choiceStartTime = 0;
	
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
		
		// Adjust test parameters based on difficulty
		if (isTrainingMode && trainingDifficulty > 5) {
			simpleTrials = 15;
			choiceTrials = 20;
		}
	});
	
	function startSimpleTest() {
		stage = 'simple';
		simpleCurrentTrial = 0;
		simpleRTs = [];
		nextSimpleTrial();
	}
	
	function nextSimpleTrial() {
		if (simpleCurrentTrial >= simpleTrials) {
			// Move to choice test
			startChoiceTest();
			return;
		}
		
		simpleWaiting = true;
		simpleReady = false;
		
		// Random delay 1-3 seconds
		const delay = 1000 + Math.random() * 2000;
		simpleTimeout = setTimeout(() => {
			simpleReady = true;
			simpleWaiting = false;
			simpleStartTime = Date.now();
		}, delay);
	}
	
	function handleSimpleClick() {
		if (simpleWaiting) {
			// Too early
			clearTimeout(simpleTimeout);
			simpleRTs.push(9999); // Penalty
			alert('Too early! Wait for the green screen.');
			simpleCurrentTrial++;
			nextSimpleTrial();
		} else if (simpleReady) {
			// Correct response
			const rt = Date.now() - simpleStartTime;
			simpleRTs.push(rt);
			simpleReady = false;
			simpleCurrentTrial++;
			nextSimpleTrial();
		}
	}
	
	function startChoiceTest() {
		stage = 'choice';
		choiceCurrentTrial = 0;
		choiceRTs = [];
		choiceAccuracy = [];
		
		// Generate stimuli (circle or square)
		choiceStimuli = [];
		for (let i = 0; i < choiceTrials; i++) {
			choiceStimuli.push(Math.random() < 0.5 ? 'circle' : 'square');
		}
		
		nextChoiceTrial();
	}
	
	function nextChoiceTrial() {
		if (choiceCurrentTrial >= choiceTrials) {
			calculateResults();
			return;
		}
		
		choiceCurrentShape = choiceStimuli[choiceCurrentTrial];
		choiceStartTime = Date.now();
	}
	
	function handleChoiceResponse(response) {
		const rt = Date.now() - choiceStartTime;
		const correct = response === choiceCurrentShape;
		
		choiceRTs.push(rt);
		choiceAccuracy.push(correct);
		
		choiceCurrentTrial++;
		nextChoiceTrial();
	}
	
	function calculateResults() {
		stage = 'results';
		saveResults();
	}
	
	async function saveResults() {
		try {
			// Simple RT metrics (exclude penalties)
			const validSimpleRTs = simpleRTs.filter(rt => rt < 9000);
			const simpleRTMean = validSimpleRTs.length > 0 
				? validSimpleRTs.reduce((a, b) => a + b, 0) / validSimpleRTs.length 
				: 0;
			const simpleRTStd = calculateStd(validSimpleRTs);
			
			// Choice RT metrics
			const choiceRTMean = choiceRTs.reduce((a, b) => a + b, 0) / choiceRTs.length;
			const choiceRTStd = calculateStd(choiceRTs);
			const choiceAccuracyScore = choiceAccuracy.filter(a => a).length / choiceAccuracy.length;
			
			// Calculate score
			const score = calculateProcessingSpeedScore(
				simpleRTMean, 
				choiceRTMean, 
				simpleRTStd, 
				choiceAccuracyScore
			);
			
			const rawData = {
				simple_rt_mean: simpleRTMean,
				simple_rt_std: simpleRTStd,
				simple_trials: validSimpleRTs.length,
				choice_rt_mean: choiceRTMean,
				choice_rt_std: choiceRTStd,
				choice_accuracy: choiceAccuracyScore,
				choice_trials: choiceTrials
			};
			
			console.log('[Processing Speed] Saving results:', {
				isTrainingMode,
				trainingPlanId,
				userId: currentUser?.id,
				score
			});
			
			if (isTrainingMode && trainingPlanId) {
				// Submit to training session API
				const avgRT = (simpleRTMean + choiceRTMean) / 2;
				const consistencyScore = simpleRTStd > 0 ? Math.max(0, 100 - (simpleRTStd / 10)) : 100;
				
				console.log('[Processing Speed] Submitting to training API');
				
				const result = await training.submitSession({
					user_id: currentUser.id,
					training_plan_id: trainingPlanId,
					domain: 'processing_speed',
					task_type: 'reaction_time',
					score: score,
					accuracy: choiceAccuracyScore * 100,
					average_reaction_time: avgRT,
					consistency: consistencyScore,
					errors: choiceAccuracy.filter(a => !a).length,
					session_duration: 2
				});
				
				sessionComplete = result.session_complete;
				completedTasksCount = result.completed_tasks;
				totalTasksCount = result.total_tasks;
				
				console.log('[Processing Speed] Training session saved:', result);
			} else {
				// Submit to regular task result API (baseline mode)
				await tasks.submitResult(
					currentUser.id,
					'processing_speed',
					score,
					JSON.stringify(rawData)
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
	
	function calculateProcessingSpeedScore(simpleRT, choiceRT, simpleStd, choiceAcc) {
		// Simple RT (40 points) - 200ms=100%, 500ms=0%
		const simpleNormalized = Math.max(0, Math.min(1, (500 - simpleRT) / 300));
		const simpleScore = simpleNormalized * 40;
		
		// Choice RT with accuracy (40 points)
		const choiceNormalized = Math.max(0, Math.min(1, (800 - choiceRT) / 400));
		const choiceScore = choiceNormalized * 30 + (choiceAcc * 10);
		
		// Consistency (20 points)
		const consistencyNormalized = Math.max(0, Math.min(1, (150 - simpleStd) / 150));
		const consistencyScore = consistencyNormalized * 20;
		
		return Math.min(100, simpleScore + choiceScore + consistencyScore);
	}
	
	function backToDashboard() {
		if (isTrainingMode) {
			goto('/training');
		} else {
			goto('/dashboard');
		}
	}
	
	// Get final metrics
	$: validSimpleRTs = simpleRTs.filter(rt => rt < 9000);
	$: simpleRTMean = validSimpleRTs.length > 0 
		? validSimpleRTs.reduce((a, b) => a + b, 0) / validSimpleRTs.length 
		: 0;
	$: choiceRTMean = choiceRTs.length > 0
		? choiceRTs.reduce((a, b) => a + b, 0) / choiceRTs.length 
		: 0;
	$: choiceAccuracyScore = choiceAccuracy.length > 0
		? choiceAccuracy.filter(a => a).length / choiceAccuracy.length
		: 0;
	$: finalScore = calculateProcessingSpeedScore(
		simpleRTMean, 
		choiceRTMean, 
		calculateStd(validSimpleRTs), 
		choiceAccuracyScore
	);
</script>

<div class="test-container">
	{#if stage === 'intro'}
		<div class="test-card">
			<h1>Processing Speed Test</h1>
			<h2 style="color: #666; font-size: 20px; margin-bottom: 30px;">Reaction Time Assessment</h2>
			
			<div style="text-align: left; max-width: 600px; margin: 0 auto;">
				<h3 style="color: #667eea; margin-bottom: 15px;">Two-Part Test:</h3>
				
				<div style="background: #f0f7ff; padding: 20px; border-radius: 8px; margin: 15px 0;">
					<h4 style="color: #667eea; margin-bottom: 10px;">Part 1: Simple Reaction Time</h4>
					<ul style="line-height: 1.8; color: #666;">
						<li>Screen will turn <strong style="color: #4caf50;">GREEN</strong></li>
						<li>Click as fast as possible when it turns green</li>
						<li>Don't click before it turns green!</li>
						<li>{simpleTrials} trials</li>
					</ul>
				</div>
				
				<div style="background: #fff3e0; padding: 20px; border-radius: 8px; margin: 15px 0;">
					<h4 style="color: #ff9800; margin-bottom: 10px;">Part 2: Choice Reaction Time</h4>
					<ul style="line-height: 1.8; color: #666;">
						<li>You'll see either a <strong>Circle ⭕</strong> or <strong>Square ⬜</strong></li>
						<li>Click <strong>LEFT button</strong> for Circle</li>
						<li>Click <strong>RIGHT button</strong> for Square</li>
						<li>Fast AND accurate!</li>
						<li>{choiceTrials} trials</li>
					</ul>
				</div>
			</div>
			
			<button class="btn-primary" on:click={startSimpleTest} style="margin-top: 40px;">
				Start Test
			</button>
			<button class="btn-secondary" on:click={backToDashboard}>
				Back to Dashboard
			</button>
		</div>
	
	{:else if stage === 'simple'}
		<div 
			class="test-card" 
			style="background: {simpleReady ? '#4caf50' : '#fff'}; transition: background 0.1s; cursor: pointer; min-height: 400px; display: flex; flex-direction: column; justify-content: center;"
			on:click={handleSimpleClick}
		>
			<div class="timer" style="color: {simpleReady ? 'white' : '#666'};">
				Trial {simpleCurrentTrial + 1} / {simpleTrials}
			</div>
			
			{#if simpleWaiting}
				<h2 style="color: #666; margin-top: 40px;">Wait...</h2>
			{:else if simpleReady}
				<h1 style="color: white; font-size: 48px; margin-top: 40px;">CLICK NOW!</h1>
			{:else}
				<h2 style="color: #666; margin-top: 40px;">Get ready...</h2>
			{/if}
			
			<p style="color: {simpleReady ? 'white' : '#999'}; margin-top: 30px;">
				{simpleReady ? 'Click anywhere!' : 'Wait for green screen'}
			</p>
		</div>
	
	{:else if stage === 'choice'}
		<div class="test-card">
			<div class="timer">
				Trial {choiceCurrentTrial + 1} / {choiceTrials}
			</div>
			
			<!-- Display shape -->
			<div style="margin: 60px 0;">
				{#if choiceCurrentShape === 'circle'}
					<div style="width: 150px; height: 150px; border-radius: 50%; background: #2196f3; margin: 0 auto;"></div>
				{:else}
					<div style="width: 150px; height: 150px; background: #ff9800; margin: 0 auto;"></div>
				{/if}
			</div>
			
			<!-- Response buttons -->
			<div style="display: flex; gap: 30px; justify-content: center; margin-top: 40px;">
				<button 
					class="btn-primary" 
					on:click={() => handleChoiceResponse('circle')}
					style="font-size: 18px; padding: 20px 40px;"
				>
					⭕ Circle<br><small style="font-size: 12px;">(LEFT)</small>
				</button>
				<button 
					class="btn-primary" 
					on:click={() => handleChoiceResponse('square')}
					style="font-size: 18px; padding: 20px 40px;"
				>
					⬜ Square<br><small style="font-size: 12px;">(RIGHT)</small>
				</button>
			</div>
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
				{finalScore.toFixed(1)}%
			</div>
			
			<div class="result-details">
				<p style="background: #e3f2fd; padding: 15px; border-radius: 6px;">
					<strong style="color: #2196f3;">Part 1: Simple Reaction Time</strong>
				</p>
				<p>
					<span>Average RT:</span>
					<strong>{simpleRTMean.toFixed(0)}ms</strong>
				</p>
				<p>
					<span>Consistency (Std Dev):</span>
					<strong>{calculateStd(validSimpleRTs).toFixed(0)}ms</strong>
				</p>
				<p>
					<span>Valid Trials:</span>
					<strong>{validSimpleRTs.length}/{simpleTrials}</strong>
				</p>
				
				<p style="background: #fff3e0; padding: 15px; border-radius: 6px; margin-top: 20px;">
					<strong style="color: #ff9800;">Part 2: Choice Reaction Time</strong>
				</p>
				<p>
					<span>Average RT:</span>
					<strong>{choiceRTMean.toFixed(0)}ms</strong>
				</p>
				<p>
					<span>Accuracy:</span>
					<strong>{(choiceAccuracyScore * 100).toFixed(1)}%</strong>
				</p>
				<p>
					<span>Correct Responses:</span>
					<strong>{choiceAccuracy.filter(a => a).length}/{choiceTrials}</strong>
				</p>
			</div>
			
			<div style="margin-top: 30px; padding: 20px; background: #f5f5f5; border-radius: 8px;">
				<h4 style="color: #667eea; margin-bottom: 10px;">Processing Speed Insights:</h4>
				<p style="color: #666; line-height: 1.6;">
					{#if simpleRTMean < 300}
						Excellent simple reaction time! Very fast processing speed.
					{:else if simpleRTMean < 400}
						Good processing speed. Above average performance.
					{:else}
						Normal processing speed. Practice can help improve response time.
					{/if}
				</p>
				{#if choiceAccuracyScore < 0.9}
					<p style="color: #ff9800; margin-top: 10px;">
						💡 Tip: In choice RT, accuracy is as important as speed. Try to balance both!
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

<svelte:head>
	<title>Processing Speed Test - NeuroBloom</title>
</svelte:head>
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
</style>
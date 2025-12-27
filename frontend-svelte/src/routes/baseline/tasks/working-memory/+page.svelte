<script>
	import { user } from '$lib/stores';
	import { tasks } from '$lib/api';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	
	let currentUser = null;
	let stage = 'intro'; // intro, test, results
	let nBackLevel = 1; // Start with 1-back
	let currentTrial = 0;
	let totalTrials = 20;
	
	// Test data
	let letters = [];
	let currentLetter = '';
	let responses = [];
	let reactionTimes = [];
	
	// Results
	let correctHits = 0;
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
	
	function startTest() {
		stage = 'test';
		generateSequence();
		showNextTrial();
	}
	
	function generateSequence() {
		const letterPool = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];
		letters = [];
		
		for (let i = 0; i < totalTrials; i++) {
			if (i >= nBackLevel && Math.random() < 0.3) {
				// 30% chance of match
				letters.push(letters[i - nBackLevel]);
			} else {
				// Random letter
				letters.push(letterPool[Math.floor(Math.random() * letterPool.length)]);
			}
		}
	}
	
	let trialStartTime = 0;
	
	function showNextTrial() {
		if (currentTrial >= totalTrials) {
			calculateResults();
			return;
		}
		
		currentLetter = letters[currentTrial];
		trialStartTime = Date.now();
		
		// Auto-advance after 2 seconds
		setTimeout(() => {
			if (responses.length === currentTrial) {
				// User didn't respond
				responses.push(false);
				reactionTimes.push(2000);
			}
			currentTrial++;
			showNextTrial();
		}, 2000);
	}
	
	function handleResponse(isMatch) {
		if (responses.length > currentTrial) return; // Already responded
		
		const rt = Date.now() - trialStartTime;
		responses.push(isMatch);
		reactionTimes.push(rt);
	}
	
	function calculateResults() {
		correctHits = 0;
		misses = 0;
		falseAlarms = 0;
		
		for (let i = 0; i < totalTrials; i++) {
			const isActualMatch = i >= nBackLevel && letters[i] === letters[i - nBackLevel];
			const userSaidMatch = responses[i];
			
			if (isActualMatch && userSaidMatch) {
				correctHits++;
			} else if (isActualMatch && !userSaidMatch) {
				misses++;
			} else if (!isActualMatch && userSaidMatch) {
				falseAlarms++;
			}
		}
		
		const totalTargets = correctHits + misses;
		accuracy = totalTargets > 0 ? (correctHits / totalTargets) * 100 : 0;
		
		const validRTs = reactionTimes.filter(rt => rt < 2000);
		meanRT = validRTs.length > 0 ? validRTs.reduce((a, b) => a + b, 0) / validRTs.length : 0;
		
		stage = 'results';
		saveResults();
	}
	
	async function saveResults() {
		try {
			const rtStd = calculateStd(reactionTimes.filter(rt => rt < 2000));
			
			await tasks.submitResult(
				currentUser.id,
				'working_memory',
				accuracy,
				JSON.stringify({
					nBackLevel,
					total_trials: totalTrials,
					correct_hits: correctHits,
					misses,
					false_alarms: falseAlarms,
					reaction_times: reactionTimes,
					mean_rt: meanRT,
					rt_std: rtStd
				})
			);
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
	
	function backToDashboard() {
		goto('/dashboard');
	}
</script>

<div class="test-container">
	{#if stage === 'intro'}
		<div class="test-card">
			<h1>Working Memory Test</h1>
			<h2 style="color: #666; font-size: 20px; margin-bottom: 30px;">N-Back Task</h2>
			
			<div style="text-align: left; max-width: 600px; margin: 0 auto;">
				<h3 style="color: #667eea; margin-bottom: 15px;">Instructions:</h3>
				<ul style="line-height: 1.8; color: #666;">
					<li>You will see a sequence of letters, one at a time</li>
					<li>Click <strong>"Match"</strong> if the current letter matches the letter from <strong>{nBackLevel} step{nBackLevel > 1 ? 's' : ''} back</strong></li>
					<li>Click <strong>"No Match"</strong> if it doesn't match</li>
					<li>Each letter appears for 2 seconds</li>
					<li>Total trials: {totalTrials}</li>
				</ul>
				
				<div style="background: #f0f7ff; padding: 20px; border-radius: 8px; margin-top: 30px;">
					<h4 style="color: #667eea; margin-bottom: 10px;">Example ({nBackLevel}-Back):</h4>
					<p style="color: #666;">Sequence: A → B → <strong>A</strong></p>
					<p style="color: #666;">When you see the second <strong>A</strong>, it matches the letter from {nBackLevel} step{nBackLevel > 1 ? 's' : ''} back, so you click "Match"</p>
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
			
			<div class="word-display">
				{currentLetter}
			</div>
			
			<div style="margin-top: 40px;">
				<button 
					class="btn-primary" 
					on:click={() => handleResponse(true)}
					style="font-size: 18px; padding: 16px 50px;"
				>
					✓ Match
				</button>
				<button 
					class="btn-secondary" 
					on:click={() => handleResponse(false)}
					style="font-size: 18px; padding: 16px 50px;"
				>
					✗ No Match
				</button>
			</div>
			
			<p style="color: #999; margin-top: 30px; font-size: 14px;">
				Does this letter match the one from {nBackLevel} step{nBackLevel > 1 ? 's' : ''} back?
			</p>
		</div>
	
	{:else if stage === 'results'}
		<div class="test-card">
			<h1>Test Complete!</h1>
			
			<div class="score-display">
				{accuracy.toFixed(1)}%
			</div>
			
			<div class="result-details">
				<p>
					<span>Correct Hits:</span>
					<strong>{correctHits}</strong>
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
				<p>
					<span>N-Back Level:</span>
					<strong>{nBackLevel}-Back</strong>
				</p>
			</div>
			
			<div style="margin-top: 40px;">
				{#if accuracy > 80 && nBackLevel < 3}
					<p style="color: #4caf50; margin-bottom: 20px; font-weight: 600;">
						Excellent! You're ready for {nBackLevel + 1}-Back
					</p>
				{/if}
				
				<button class="btn-primary" on:click={backToDashboard}>
					Back to Dashboard
				</button>
			</div>
		</div>
	{/if}
</div>

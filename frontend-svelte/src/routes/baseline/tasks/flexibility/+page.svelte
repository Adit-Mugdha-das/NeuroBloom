<script>
	import { user } from '$lib/stores';
	import { tasks } from '$lib/api';
	import { goto } from '$app/navigation';
	
	let currentUser = null;
	let stage = 'intro'; // intro, test, results
	let currentTrial = 0;
	let totalTrials = 40;
	
	// Test data
	let trials = [];
	let currentNumber = 0;
	let currentColor = '';
	let currentRule = ''; // 'parity' or 'magnitude'
	let responses = [];
	let reactionTimes = [];
	
	// Results
	let switchTrials = 0;
	let switchErrors = 0;
	let noSwitchErrors = 0;
	let totalErrors = 0;
	let switchCostRT = 0;
	let perseverationErrors = 0;
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
		generateTrials();
		showNextTrial();
	}
	
	function generateTrials() {
		const numbers = [1, 2, 3, 4, 6, 7, 8, 9];
		const colors = ['blue', 'red'];
		const rules = ['parity', 'magnitude'];
		
		trials = [];
		let lastRule = '';
		
		for (let i = 0; i < totalTrials; i++) {
			const number = numbers[Math.floor(Math.random() * numbers.length)];
			const color = colors[Math.floor(Math.random() * colors.length)];
			const rule = color === 'blue' ? 'parity' : 'magnitude';
			const isSwitch = i > 0 && rule !== lastRule;
			
			trials.push({
				number,
				color,
				rule,
				isSwitch
			});
			
			if (isSwitch) switchTrials++;
			lastRule = rule;
		}
	}
	
	let trialStartTime = 0;
	
	function showNextTrial() {
		if (currentTrial >= totalTrials) {
			calculateResults();
			return;
		}
		
		const trial = trials[currentTrial];
		currentNumber = trial.number;
		currentColor = trial.color;
		currentRule = trial.rule;
		trialStartTime = Date.now();
	}
	
	function handleResponse(answer) {
		const rt = Date.now() - trialStartTime;
		const trial = trials[currentTrial];
		
		let correctAnswer;
		if (trial.rule === 'parity') {
			correctAnswer = trial.number % 2 === 0 ? 'even' : 'odd';
		} else {
			correctAnswer = trial.number > 5 ? 'high' : 'low';
		}
		
		const isCorrect = answer === correctAnswer;
		
		responses.push({
			trial: currentTrial,
			answer,
			correctAnswer,
			isCorrect,
			rt,
			isSwitch: trial.isSwitch
		});
		
		reactionTimes.push(rt);
		
		currentTrial++;
		showNextTrial();
	}
	
	function calculateResults() {
		switchErrors = 0;
		noSwitchErrors = 0;
		perseverationErrors = 0;
		
		let switchRTs = [];
		let noSwitchRTs = [];
		
		for (let i = 0; i < responses.length; i++) {
			const response = responses[i];
			
			if (!response.isCorrect) {
				totalErrors++;
				
				if (response.isSwitch) {
					switchErrors++;
					
					// Check for perseveration (used old rule)
					if (i > 0) {
						const prevTrial = trials[i - 1];
						const currentTrial = trials[i];
						
						// If they responded as if using the previous rule
						let prevRuleAnswer;
						if (prevTrial.rule === 'parity') {
							prevRuleAnswer = currentTrial.number % 2 === 0 ? 'even' : 'odd';
						} else {
							prevRuleAnswer = currentTrial.number > 5 ? 'high' : 'low';
						}
						
						if (response.answer === prevRuleAnswer) {
							perseverationErrors++;
						}
					}
				} else {
					noSwitchErrors++;
				}
			}
			
			if (response.isSwitch) {
				switchRTs.push(response.rt);
			} else if (i > 0) {
				noSwitchRTs.push(response.rt);
			}
		}
		
		accuracy = ((responses.length - totalErrors) / responses.length) * 100;
		
		const avgSwitchRT = switchRTs.length > 0 ? switchRTs.reduce((a, b) => a + b, 0) / switchRTs.length : 0;
		const avgNoSwitchRT = noSwitchRTs.length > 0 ? noSwitchRTs.reduce((a, b) => a + b, 0) / noSwitchRTs.length : 0;
		switchCostRT = avgSwitchRT - avgNoSwitchRT;
		
		meanRT = reactionTimes.reduce((a, b) => a + b, 0) / reactionTimes.length;
		
		stage = 'results';
		saveResults();
	}
	
	async function saveResults() {
		try {
			const rtStd = calculateStd(reactionTimes);
			
			await tasks.submitResult(
				currentUser.id,
				'flexibility',
				accuracy,
				JSON.stringify({
					total_trials: totalTrials,
					total_switches: switchTrials,
					switch_errors: switchErrors,
					no_switch_errors: noSwitchErrors,
					perseveration_errors: perseverationErrors,
					switch_cost_rt: switchCostRT,
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
			<h1>Cognitive Flexibility Test</h1>
			<h2 style="color: #666; font-size: 20px; margin-bottom: 30px;">Task Switching</h2>
			
			<div style="text-align: left; max-width: 600px; margin: 0 auto;">
				<h3 style="color: #667eea; margin-bottom: 15px;">Instructions:</h3>
				<ul style="line-height: 1.8; color: #666;">
					<li>You will see numbers with colored backgrounds</li>
					<li><strong style="color: #2196f3;">BLUE background:</strong> Judge if the number is odd or even</li>
					<li><strong style="color: #f44336;">RED background:</strong> Judge if the number is &gt;5 or &lt;5</li>
					<li>The background color changes randomly - stay flexible!</li>
					<li>Total trials: {totalTrials}</li>
				</ul>
				
				<div style="background: #f0f7ff; padding: 20px; border-radius: 8px; margin-top: 30px;">
					<h4 style="color: #667eea; margin-bottom: 10px;">Examples:</h4>
					<div style="background: #2196f3; color: white; padding: 15px; border-radius: 6px; margin: 10px 0;">
						<strong>7</strong> on BLUE → "Odd" (because 7 is odd)
					</div>
					<div style="background: #f44336; color: white; padding: 15px; border-radius: 6px; margin: 10px 0;">
						<strong>7</strong> on RED → "High" (because 7 &gt; 5)
					</div>
					<div style="background: #2196f3; color: white; padding: 15px; border-radius: 6px; margin: 10px 0;">
						<strong>2</strong> on BLUE → "Even" (because 2 is even)
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
			<div class="timer">
				Trial {currentTrial + 1} / {totalTrials}
			</div>
			
			<div 
				class="word-display" 
				style="background: {currentColor}; color: white; border-radius: 20px; padding: 40px; margin: 40px auto; max-width: 200px;"
			>
				{currentNumber}
			</div>
			
			<p style="margin-bottom: 30px; font-size: 18px; color: #666;">
				{#if currentColor === 'blue'}
					Is it <strong>odd</strong> or <strong>even</strong>?
				{:else}
					Is it <strong>&gt;5</strong> or <strong>&lt;5</strong>?
				{/if}
			</p>
			
			<div>
				{#if currentRule === 'parity'}
					<button 
						class="btn-primary" 
						on:click={() => handleResponse('odd')}
						style="font-size: 18px; padding: 16px 50px;"
					>
						Odd
					</button>
					<button 
						class="btn-primary" 
						on:click={() => handleResponse('even')}
						style="font-size: 18px; padding: 16px 50px;"
					>
						Even
					</button>
				{:else}
					<button 
						class="btn-primary" 
						on:click={() => handleResponse('low')}
						style="font-size: 18px; padding: 16px 50px;"
					>
						&lt; 5 (Low)
					</button>
					<button 
						class="btn-primary" 
						on:click={() => handleResponse('high')}
						style="font-size: 18px; padding: 16px 50px;"
					>
						&gt; 5 (High)
					</button>
				{/if}
			</div>
		</div>
	
	{:else if stage === 'results'}
		<div class="test-card">
			<h1>Test Complete!</h1>
			
			<div class="score-display">
				{accuracy.toFixed(1)}%
			</div>
			
			<div class="result-details">
				<p>
					<span>Total Errors:</span>
					<strong>{totalErrors}</strong>
				</p>
				<p>
					<span>Switch Errors:</span>
					<strong>{switchErrors}</strong>
				</p>
				<p>
					<span>No-Switch Errors:</span>
					<strong>{noSwitchErrors}</strong>
				</p>
				<p>
					<span>Perseveration Errors:</span>
					<strong>{perseverationErrors}</strong>
				</p>
				<p>
					<span>Switch Cost (RT increase):</span>
					<strong>{switchCostRT.toFixed(0)}ms</strong>
				</p>
				<p>
					<span>Average RT:</span>
					<strong>{meanRT.toFixed(0)}ms</strong>
				</p>
			</div>
			
			<div style="margin-top: 30px; padding: 20px; background: #f5f5f5; border-radius: 8px;">
				<h4 style="color: #667eea; margin-bottom: 10px;">Cognitive Flexibility Insights:</h4>
				<p style="color: #666; line-height: 1.6;">
					{#if switchCostRT < 150}
						Excellent flexibility! You adapt quickly to changing rules.
					{:else if switchCostRT < 300}
						Good flexibility. With practice, you can reduce your switch cost further.
					{:else}
						Keep practicing. Task switching improves with regular training.
					{/if}
				</p>
				{#if perseverationErrors > 3}
					<p style="color: #ff9800; margin-top: 10px;">
						💡 Tip: You had {perseverationErrors} perseveration errors (using old rule). Try to focus on the current color cue.
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
	<title>Cognitive Flexibility Test - NeuroBloom</title>
</svelte:head>

<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import { onMount } from 'svelte';

	// Task states
	const STATE = {
		LOADING: 'loading',
		INSTRUCTIONS: 'instructions',
		READY: 'ready',
		MATH_PROBLEM: 'math_problem',
		LETTER_DISPLAY: 'letter_display',
		RECALL: 'recall',
		FEEDBACK: 'feedback',
		COMPLETE: 'complete'
	};

	let state = STATE.LOADING;
	let difficulty = 5;
	let trials = [];
	let currentTrialIndex = 0;
	let currentTrial = null;
	let currentItemIndex = 0;
	let currentItem = null;
	
	// Math problem state
	let mathResponse = null;
	let mathStartTime = 0;
	let mathTimeout = null;
	let timeRemaining = 0;
	let timerInterval = null;
	
	// Letter recall state
	let userLetters = [];
	let mathResponses = [];
	let trialStartTime = 0;
	let lastTrialCorrect = false;
	let lastTrial = null;

	let showHelp = false;
	let sessionResults = null;
	let taskId = null;

	// Available letters
	const LETTERS = ['B', 'C', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'R', 'S', 'T'];

	onMount(async () => {
		await loadSession();
	});

	async function loadSession() {
		try {
			const userData = JSON.parse(localStorage.getItem('user') || '{}');
			const userId = userData.id;

			if (!userId) {
				goto('/login');
				return;
			}

			const planRes = await fetch(`http://localhost:8000/api/training/training-plan/${userId}`);
			const plan = await planRes.json();

			let userDifficulty = 5;
			if (plan && plan.current_difficulty) {
				const currentDiff =
					typeof plan.current_difficulty === 'string'
						? JSON.parse(plan.current_difficulty)
						: plan.current_difficulty;
				userDifficulty = currentDiff.working_memory || 5;
			}

			difficulty = userDifficulty;
			console.log('📊 Operation Span - Loaded difficulty:', difficulty);

			const response = await fetch(
				`http://localhost:8000/api/training/tasks/operation-span/generate/${userId}?difficulty=${difficulty}&num_trials=6`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' }
				}
			);

			if (!response.ok) throw new Error('Failed to load session');

			const data = await response.json();
			trials = data.trials.map(t => ({
				...t,
				user_letters: [],
				math_responses: [],
				reaction_time: 0
			}));
			
			state = STATE.INSTRUCTIONS;
		} catch (error) {
			console.error('Error loading session:', error);
			alert('Failed to load task session');
			goto('/dashboard');
		}
	}

	function startSession() {
		state = STATE.LOADING;
		currentTrialIndex = 0;
		setTimeout(() => startTrial(), 500);
	}

	async function startTrial() {
		currentTrial = trials[currentTrialIndex];
		currentItemIndex = 0;
		userLetters = [];
		mathResponses = [];
		trialStartTime = Date.now();
		
		state = STATE.READY;
		await new Promise(resolve => setTimeout(resolve, 1500));
		
		showNextItem();
	}

	function showNextItem() {
		if (currentItemIndex >= currentTrial.items.length) {
			// All items shown, move to recall
			state = STATE.RECALL;
			return;
		}
		
		currentItem = currentTrial.items[currentItemIndex];
		
		// Show math problem
		state = STATE.MATH_PROBLEM;
		mathResponse = null;
		mathStartTime = Date.now();
		
		// Start countdown timer
		timeRemaining = currentTrial.time_limit;
		startTimer();
		
		// Auto-timeout if no response
		mathTimeout = setTimeout(() => {
			if (state === STATE.MATH_PROBLEM) {
				handleMathTimeout();
			}
		}, currentTrial.time_limit);
	}

	function startTimer() {
		if (timerInterval) clearInterval(timerInterval);
		
		timerInterval = setInterval(() => {
			timeRemaining -= 100;
			if (timeRemaining <= 0) {
				clearInterval(timerInterval);
			}
		}, 100);
	}

	function handleMathResponse(response) {
		if (state !== STATE.MATH_PROBLEM) return;
		
		mathResponse = response;
		mathResponses.push(response);
		
		// Clear timeout
		if (mathTimeout) clearTimeout(mathTimeout);
		if (timerInterval) clearInterval(timerInterval);
		
		// Show letter
		setTimeout(() => showLetter(), 300);
	}

	function handleMathTimeout() {
		// User took too long - count as incorrect
		mathResponses.push(false);
		showLetter();
	}

	async function showLetter() {
		state = STATE.LETTER_DISPLAY;
		
		// Show for 1 second
		await new Promise(resolve => setTimeout(resolve, 1000));
		
		// Move to next item
		currentItemIndex++;
		showNextItem();
	}

	function addLetter(letter) {
		if (state !== STATE.RECALL) return;
		if (userLetters.includes(letter)) return;
		userLetters = [...userLetters, letter];
	}

	function removeLastLetter() {
		if (userLetters.length > 0) {
			userLetters = userLetters.slice(0, -1);
		}
	}

	function clearLetters() {
		userLetters = [];
	}

	function submitRecall() {
		if (state !== STATE.RECALL) return;
		
		const reactionTime = Date.now() - trialStartTime;
		trials[currentTrialIndex].user_letters = userLetters;
		trials[currentTrialIndex].math_responses = mathResponses;
		trials[currentTrialIndex].reaction_time = reactionTime;

		lastTrialCorrect = checkCorrect();
		lastTrial = currentTrial;

		state = STATE.FEEDBACK;

		setTimeout(() => {
			if (currentTrialIndex < trials.length - 1) {
				currentTrialIndex++;
				startTrial();
			} else {
				submitSession();
			}
		}, 2000);
	}

	function checkCorrect() {
		return JSON.stringify(userLetters) === JSON.stringify(currentTrial.correct_letters);
	}

	async function submitSession() {
		state = STATE.LOADING;
		
		try {
			const userData = JSON.parse(localStorage.getItem('user') || '{}');
			const userId = userData.id;

			const response = await fetch(
				`http://localhost:8000/api/training/tasks/operation-span/submit/${userId}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						difficulty: difficulty,
						trials: trials,
						task_id: taskId
					})
				}
			);

			if (!response.ok) throw new Error('Failed to submit session');

			sessionResults = await response.json();
			state = STATE.COMPLETE;
		} catch (error) {
			console.error('Error submitting session:', error);
			alert('Failed to submit results');
		}
	}

	function toggleHelp() {
		showHelp = !showHelp;
	}
</script>

<div class="ospan-container">
	{#if state === STATE.LOADING}
		<div class="loading">
			<div class="spinner"></div>
			<p>Loading Operation Span Task...</p>
		</div>
	{:else if state === STATE.INSTRUCTIONS}
		<div class="instructions">
			<div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap;">
				<h1>🧮 Operation Span (OSPAN)</h1>
				<DifficultyBadge {difficulty} domain="Working Memory" />
			</div>

			<div class="instruction-card">
				<h2>Dual-Task Challenge</h2>
				<p>This task measures your ability to juggle two mental tasks simultaneously:</p>
				
				<div class="dual-tasks">
					<div class="task-card math-card">
						<div class="task-icon">🧮</div>
						<h3>Task 1: Verify Math</h3>
						<p>Decide if each equation is correct or incorrect</p>
						<div class="task-example">
							<div class="example-item">2 + 3 = 5 <span class="correct">✓ Correct</span></div>
							<div class="example-item">4 + 2 = 7 <span class="incorrect">✗ Incorrect</span></div>
						</div>
					</div>
					
					<div class="task-card letter-card">
						<div class="task-icon">🔤</div>
						<h3>Task 2: Remember Letters</h3>
						<p>After each equation, memorize a letter</p>
						<div class="task-example">
							<div class="example-item">Remember: <strong>F</strong></div>
							<div class="example-item">Remember: <strong>Q</strong></div>
						</div>
					</div>
				</div>

				<div class="flow-diagram">
					<h3>📋 How It Works</h3>
					<div class="flow-steps">
						<div class="flow-step">
							<div class="step-number">1</div>
							<div class="step-content">
								<strong>Math Problem</strong>
								<p>Is 2+3=5?</p>
								<div class="step-buttons">
									<span class="mini-btn correct">✓ Correct</span>
									<span class="mini-btn incorrect">✗ Incorrect</span>
								</div>
							</div>
						</div>
						<div class="flow-arrow">→</div>
						<div class="flow-step">
							<div class="step-number">2</div>
							<div class="step-content">
								<strong>Remember Letter</strong>
								<p class="big-letter">F</p>
							</div>
						</div>
						<div class="flow-arrow">→</div>
						<div class="flow-step">
							<div class="step-number">3</div>
							<div class="step-content">
								<strong>Repeat 2-8 times</strong>
								<p>More math + letters</p>
							</div>
						</div>
						<div class="flow-arrow">→</div>
						<div class="flow-step">
							<div class="step-number">4</div>
							<div class="step-content">
								<strong>Recall Letters</strong>
								<p>F - Q - M</p>
							</div>
						</div>
					</div>
				</div>
				
				<div class="tips">
					<h3>💡 Pro Tips</h3>
					<ul>
						<li><strong>Balance both tasks:</strong> Don't sacrifice math for letters or vice versa</li>
						<li><strong>Mental rehearsal:</strong> Silently repeat letters after each one</li>
						<li><strong>Take your time:</strong> Use the full time to verify each equation</li>
						<li><strong>Stay focused:</strong> This is mentally demanding - that's the point!</li>
					</ul>
				</div>
			</div>
			
			<button class="start-button" on:click={startSession} disabled={state !== STATE.INSTRUCTIONS}>
				Start Training Session
			</button>
		</div>
	{:else if state === STATE.READY}
		<div class="ready-screen">
			<h2>Set {currentTrialIndex + 1} of {trials.length}</h2>
			<p class="set-info">{currentTrial.set_size} math-letter pairs</p>
			<p>Get ready...</p>
		</div>
	{:else if state === STATE.MATH_PROBLEM}
		<div class="math-screen">
			<div class="header">
				<div class="progress-info">
					<span class="set-badge">Set {currentTrialIndex + 1}/{trials.length}</span>
					<span class="item-badge">Problem {currentItemIndex + 1}/{currentTrial.set_size}</span>
				</div>
				<button class="help-button" on:click={toggleHelp}>?</button>
			</div>

			<div class="timer-bar">
				<div class="timer-fill" style="width: {(timeRemaining / currentTrial.time_limit) * 100}%"></div>
			</div>

			<div class="math-problem-display">
				<p class="instruction">Is this equation correct?</p>
				<div class="equation">{currentItem.equation}</div>
			</div>

			<div class="math-buttons">
				<button 
					class="math-btn correct-btn" 
					on:click={() => handleMathResponse(true)}
					disabled={mathResponse !== null}
				>
					<span class="btn-icon">✓</span>
					<span class="btn-label">Correct</span>
				</button>
				<button 
					class="math-btn incorrect-btn" 
					on:click={() => handleMathResponse(false)}
					disabled={mathResponse !== null}
				>
					<span class="btn-icon">✗</span>
					<span class="btn-label">Incorrect</span>
				</button>
			</div>
		</div>
	{:else if state === STATE.LETTER_DISPLAY}
		<div class="letter-screen">
			<p class="instruction">Remember this letter</p>
			<div class="letter-display">{currentItem.letter}</div>
			<div class="letter-count">Letter {currentItemIndex} of {currentTrial.set_size}</div>
		</div>
	{:else if state === STATE.RECALL}
		<div class="recall-screen">
			<div class="header">
				<div class="progress-info">
					<span class="set-badge">Set {currentTrialIndex + 1}/{trials.length}</span>
				</div>
				<button class="help-button" on:click={toggleHelp}>?</button>
			</div>

			<p class="instruction">Recall the letters in order</p>

			<div class="selected-letters">
				{#if userLetters.length === 0}
					<span class="placeholder">Click letters below...</span>
				{:else}
					{#each userLetters as letter, index}
						<span class="selected-letter">{index + 1}. {letter}</span>
					{/each}
				{/if}
			</div>

			<div class="letter-grid">
				{#each LETTERS as letter}
					<button 
						class="letter-btn" 
						class:selected={userLetters.includes(letter)}
						disabled={userLetters.includes(letter) || userLetters.length >= currentTrial.set_size}
						on:click={() => addLetter(letter)}
					>
						{letter}
					</button>
				{/each}
			</div>

			<div class="controls">
				<button class="control-btn" on:click={removeLastLetter} disabled={userLetters.length === 0}>
					↶ Undo
				</button>
				<button class="control-btn" on:click={clearLetters} disabled={userLetters.length === 0}>
					✕ Clear
				</button>
			</div>

			<button 
				class="submit-button" 
				on:click={submitRecall}
				disabled={userLetters.length === 0}
			>
				Submit Recall
			</button>
		</div>
	{:else if state === STATE.FEEDBACK}
		<div class="feedback-screen">
			<div class="feedback-icon {lastTrialCorrect ? 'correct' : 'incorrect'}">
				{lastTrialCorrect ? '✓' : '✗'}
			</div>
			<p class="feedback-text">
				{lastTrialCorrect ? 'Perfect!' : 'Not quite'}
			</p>
			{#if !lastTrialCorrect}
				<div class="correct-answer">
					<p>Correct letters: <strong>{lastTrial.correct_letters.join(' - ')}</strong></p>
				</div>
			{/if}
		</div>
	{:else if state === STATE.COMPLETE}
		<div class="complete-screen">
			<h1>Session Complete! 🎉</h1>
			
			<div class="results-grid">
				<div class="result-card">
					<div class="result-value">{sessionResults.metrics.score}</div>
					<div class="result-label">Overall Score</div>
				</div>
				<div class="result-card">
					<div class="result-value">{sessionResults.metrics.dual_task_performance.toFixed(1)}%</div>
					<div class="result-label">Dual-Task Performance</div>
				</div>
				<div class="result-card math-card-result">
					<div class="result-value">{sessionResults.metrics.math_accuracy.toFixed(1)}%</div>
					<div class="result-label">Math Accuracy</div>
				</div>
				<div class="result-card letter-card-result">
					<div class="result-value">{sessionResults.metrics.letter_recall_accuracy.toFixed(1)}%</div>
					<div class="result-label">Letter Recall</div>
				</div>
			</div>

			<div class="performance-breakdown">
				<h3>📊 Performance Analysis</h3>
				<div class="breakdown-item">
					<span>Perfect Sets (Both Tasks):</span>
					<span class="value">{sessionResults.metrics.correct_count} / {sessionResults.metrics.total_trials}</span>
				</div>
				<div class="breakdown-item">
					<span>Consistency:</span>
					<span class="value">{sessionResults.metrics.consistency.toFixed(1)}%</span>
				</div>
			</div>

			<div class="difficulty-info">
				<p>
					Difficulty: <strong>{sessionResults.difficulty_before}</strong> → 
					<strong>{sessionResults.difficulty_after}</strong>
				</p>
				<p class="adaptation-reason">{sessionResults.adaptation_reason}</p>
			</div>

			{#if sessionResults.new_badges && sessionResults.new_badges.length > 0}
				<div class="new-badges">
					<h3>🏆 New Badges Earned!</h3>
					{#each sessionResults.new_badges as badge}
						<div class="badge">
							<span class="badge-icon">{badge.icon}</span>
							<span class="badge-name">{badge.name}</span>
						</div>
					{/each}
				</div>
			{/if}

			<div class="actions">
				<button on:click={() => goto('/training')}>Back to Training</button>
				<button on:click={() => goto('/dashboard')}>View Dashboard</button>
			</div>
		</div>
	{/if}
</div>

{#if showHelp}
	<div class="help-modal" on:click={toggleHelp} role="dialog" tabindex="-1" on:keydown={(e) => e.key === 'Escape' && toggleHelp()}>
		<div class="help-content" on:click|stopPropagation role="document" tabindex="-1" on:keydown={(e) => e.key === 'Escape' && toggleHelp()}>
			<button class="close-button" on:click={toggleHelp}>×</button>
			<h2>Success Strategies</h2>
			
			<div class="strategy">
				<h3>⚖️ Balance Both Tasks</h3>
				<p>Your score depends on BOTH math accuracy AND letter recall. Don't sacrifice one for the other - aim for high performance on both tasks.</p>
			</div>
			
			<div class="strategy">
				<h3>🧮 Math First, Letters After</h3>
				<p>Quickly verify the equation, then immediately shift focus to encoding the letter. Don't dwell on the math after answering.</p>
			</div>
			
			<div class="strategy">
				<h3>🔄 Active Rehearsal</h3>
				<p>After seeing each letter, silently rehearse ALL letters so far in order. This keeps them fresh in working memory.</p>
			</div>
			
			<div class="strategy">
				<h3>🎯 Accuracy Over Speed</h3>
				<p>Use the full time available for each equation. Rushing leads to errors in both tasks.</p>
			</div>
			
			<div class="strategy">
				<h3>🧠 Chunking Strategy</h3>
				<p>Group letters into chunks of 2-3 (e.g., "FK-MT-B" instead of "F-K-M-T-B"). This reduces memory load.</p>
			</div>
		</div>
	</div>
{/if}

<style>
	.ospan-container {
		max-width: 900px;
		margin: 0 auto;
		padding: 2rem;
		min-height: 100vh;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
	}

	.loading {
		text-align: center;
		padding: 4rem 0;
		color: white;
	}

	.spinner {
		width: 50px;
		height: 50px;
		border: 4px solid rgba(255,255,255,0.3);
		border-top: 4px solid white;
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin: 0 auto 1rem;
	}

	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	.instructions {
		text-align: center;
	}

	.instructions h1 {
		color: white;
		margin-bottom: 2rem;
		font-size: 2.5rem;
		text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
	}

	.instruction-card {
		background: white;
		border-radius: 16px;
		padding: 2.5rem;
		margin: 2rem 0;
		box-shadow: 0 8px 32px rgba(0,0,0,0.2);
		text-align: left;
	}

	.dual-tasks {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.5rem;
		margin: 2rem 0;
	}

	.task-card {
		padding: 1.5rem;
		border-radius: 12px;
		text-align: center;
		box-shadow: 0 4px 12px rgba(0,0,0,0.1);
	}

	.math-card {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
	}

	.letter-card {
		background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
		color: white;
	}

	.task-icon {
		font-size: 3rem;
		margin-bottom: 0.5rem;
	}

	.task-card h3 {
		margin: 0.5rem 0;
	}

	.task-example {
		margin-top: 1rem;
		padding-top: 1rem;
		border-top: 1px solid rgba(255,255,255,0.3);
	}

	.example-item {
		padding: 0.5rem;
		margin: 0.25rem 0;
	}

	.correct {
		color: #4CAF50;
		font-weight: bold;
	}

	.incorrect {
		color: #f44336;
		font-weight: bold;
	}

	.flow-diagram {
		background: #f8f9fa;
		padding: 2rem;
		border-radius: 12px;
		margin: 2rem 0;
	}

	.flow-diagram h3 {
		margin: 0 0 1.5rem 0;
		color: #2c3e50;
		text-align: center;
	}

	.flow-steps {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.flow-step {
		background: white;
		padding: 1rem;
		border-radius: 8px;
		min-width: 140px;
		box-shadow: 0 2px 8px rgba(0,0,0,0.1);
	}

	.step-number {
		width: 30px;
		height: 30px;
		background: #667eea;
		color: white;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: bold;
		margin: 0 auto 0.5rem;
	}

	.step-content {
		text-align: center;
	}

	.step-content strong {
		display: block;
		color: #2c3e50;
		margin-bottom: 0.5rem;
		font-size: 0.9rem;
	}

	.step-content p {
		margin: 0.25rem 0;
		font-size: 0.85rem;
		color: #666;
	}

	.big-letter {
		font-size: 2rem !important;
		font-weight: bold !important;
		color: #667eea !important;
	}

	.step-buttons {
		display: flex;
		gap: 0.25rem;
		justify-content: center;
		margin-top: 0.5rem;
	}

	.mini-btn {
		padding: 0.25rem 0.5rem;
		border-radius: 4px;
		font-size: 0.75rem;
		font-weight: bold;
	}

	.mini-btn.correct {
		background: #e8f5e9;
		color: #4CAF50;
	}

	.mini-btn.incorrect {
		background: #ffebee;
		color: #f44336;
	}

	.flow-arrow {
		font-size: 1.5rem;
		color: #667eea;
		font-weight: bold;
	}

	.tips {
		background: #fff3cd;
		padding: 1.5rem;
		border-radius: 12px;
		margin-top: 2rem;
	}

	.tips h3 {
		margin: 0 0 1rem 0;
		color: #856404;
	}

	.tips ul {
		margin: 0;
		padding-left: 1.5rem;
	}

	.tips li {
		margin-bottom: 0.5rem;
		color: #856404;
		line-height: 1.6;
	}

	.start-button {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		padding: 1rem 3rem;
		font-size: 1.3rem;
		font-weight: bold;
		border-radius: 12px;
		cursor: pointer;
		margin-top: 2rem;
		transition: all 0.3s;
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
	}

	.start-button:hover:not(:disabled) {
		transform: translateY(-2px);
		box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
	}

	.start-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.ready-screen {
		background: white;
		border-radius: 16px;
		padding: 4rem 2rem;
		text-align: center;
		box-shadow: 0 8px 32px rgba(0,0,0,0.2);
	}

	.ready-screen h2 {
		color: #667eea;
		margin-bottom: 1rem;
	}

	.set-info {
		color: #666;
		font-size: 1.1rem;
		margin-bottom: 1rem;
	}

	.math-screen, .letter-screen, .recall-screen {
		background: white;
		border-radius: 16px;
		padding: 2rem;
		box-shadow: 0 8px 32px rgba(0,0,0,0.2);
	}

	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
	}

	.progress-info {
		display: flex;
		gap: 0.5rem;
		align-items: center;
		flex-wrap: wrap;
	}

	.set-badge, .item-badge {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		padding: 0.5rem 1rem;
		border-radius: 20px;
		font-weight: 600;
		font-size: 0.9rem;
	}

	.help-button {
		width: 40px;
		height: 40px;
		border-radius: 50%;
		border: 2px solid #667eea;
		background: white;
		color: #667eea;
		font-size: 1.5rem;
		font-weight: bold;
		cursor: pointer;
		transition: all 0.3s;
	}

	.help-button:hover {
		background: #667eea;
		color: white;
	}

	.timer-bar {
		height: 8px;
		background: #e0e0e0;
		border-radius: 10px;
		overflow: hidden;
		margin-bottom: 2rem;
	}

	.timer-fill {
		height: 100%;
		background: linear-gradient(90deg, #4CAF50, #FFC107, #f44336);
		transition: width 0.1s linear;
		border-radius: 10px;
	}

	.math-problem-display {
		text-align: center;
		padding: 3rem 0;
	}

	.instruction {
		font-size: 1.2rem;
		color: #666;
		margin-bottom: 2rem;
	}

	.equation {
		font-size: 3rem;
		font-weight: bold;
		color: #2c3e50;
		padding: 2rem;
		background: #f8f9fa;
		border-radius: 12px;
		display: inline-block;
		min-width: 300px;
	}

	.math-buttons {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.5rem;
		max-width: 600px;
		margin: 0 auto;
	}

	.math-btn {
		padding: 2rem;
		border: none;
		border-radius: 12px;
		font-size: 1.3rem;
		font-weight: bold;
		cursor: pointer;
		transition: all 0.3s;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}

	.correct-btn {
		background: linear-gradient(135deg, #4CAF50, #45a049);
		color: white;
		box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
	}

	.correct-btn:hover:not(:disabled) {
		transform: translateY(-4px);
		box-shadow: 0 6px 20px rgba(76, 175, 80, 0.5);
	}

	.incorrect-btn {
		background: linear-gradient(135deg, #f44336, #d32f2f);
		color: white;
		box-shadow: 0 4px 12px rgba(244, 67, 54, 0.3);
	}

	.incorrect-btn:hover:not(:disabled) {
		transform: translateY(-4px);
		box-shadow: 0 6px 20px rgba(244, 67, 54, 0.5);
	}

	.math-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.btn-icon {
		font-size: 3rem;
	}

	.btn-label {
		font-size: 1.1rem;
	}

	.letter-screen {
		text-align: center;
		padding: 4rem 2rem;
	}

	.letter-display {
		font-size: 8rem;
		font-weight: bold;
		color: #667eea;
		margin: 2rem 0;
		text-shadow: 3px 3px 6px rgba(0,0,0,0.1);
	}

	.letter-count {
		color: #666;
		font-size: 1.1rem;
	}

	.recall-screen .instruction {
		text-align: center;
		margin-bottom: 1.5rem;
	}

	.selected-letters {
		background: #f8f9fa;
		padding: 1.5rem;
		border-radius: 12px;
		min-height: 80px;
		display: flex;
		gap: 1rem;
		align-items: center;
		flex-wrap: wrap;
		margin-bottom: 2rem;
		justify-content: center;
	}

	.placeholder {
		color: #999;
		font-style: italic;
	}

	.selected-letter {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		padding: 0.75rem 1.25rem;
		border-radius: 8px;
		font-weight: bold;
		font-size: 1.3rem;
	}

	.letter-grid {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		gap: 0.75rem;
		margin-bottom: 1.5rem;
	}

	.letter-btn {
		aspect-ratio: 1;
		border: 2px solid #667eea;
		background: white;
		border-radius: 12px;
		font-size: 1.3rem;
		font-weight: bold;
		color: #667eea;
		cursor: pointer;
		transition: all 0.2s;
	}

	.letter-btn:hover:not(:disabled) {
		background: #667eea;
		color: white;
		transform: scale(1.05);
	}

	.letter-btn:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}

	.controls {
		display: flex;
		gap: 0.5rem;
		justify-content: center;
		margin-bottom: 1.5rem;
	}

	.control-btn {
		padding: 0.75rem 1.5rem;
		border: 2px solid #FF9800;
		background: white;
		color: #FF9800;
		border-radius: 8px;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
	}

	.control-btn:hover:not(:disabled) {
		background: #FF9800;
		color: white;
	}

	.control-btn:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}

	.submit-button {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		padding: 1rem 3rem;
		font-size: 1.2rem;
		font-weight: bold;
		border-radius: 12px;
		cursor: pointer;
		transition: all 0.3s;
		display: block;
		margin: 0 auto;
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
	}

	.submit-button:hover:not(:disabled) {
		transform: translateY(-2px);
		box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
	}

	.submit-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.feedback-screen {
		background: white;
		border-radius: 16px;
		padding: 4rem 2rem;
		text-align: center;
		box-shadow: 0 8px 32px rgba(0,0,0,0.2);
	}

	.feedback-icon {
		width: 120px;
		height: 120px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 4rem;
		margin: 0 auto 1rem;
		color: white;
	}

	.feedback-icon.correct {
		background: linear-gradient(135deg, #4CAF50, #45a049);
	}

	.feedback-icon.incorrect {
		background: linear-gradient(135deg, #f44336, #d32f2f);
	}

	.feedback-text {
		font-size: 2rem;
		font-weight: bold;
		color: #2c3e50;
	}

	.correct-answer {
		margin-top: 2rem;
		background: #f8f9fa;
		padding: 1.5rem;
		border-radius: 12px;
	}

	.complete-screen {
		background: white;
		border-radius: 16px;
		padding: 3rem 2rem;
		box-shadow: 0 8px 32px rgba(0,0,0,0.2);
		text-align: center;
	}

	.complete-screen h1 {
		color: #667eea;
		margin-bottom: 2rem;
	}

	.results-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: 1rem;
		margin: 2rem 0;
	}

	.result-card {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		padding: 1.5rem;
		border-radius: 12px;
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
	}

	.math-card-result {
		background: linear-gradient(135deg, #4CAF50, #45a049);
	}

	.letter-card-result {
		background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
	}

	.result-value {
		font-size: 2.5rem;
		font-weight: bold;
		margin-bottom: 0.5rem;
	}

	.result-label {
		font-size: 0.9rem;
		opacity: 0.9;
	}

	.performance-breakdown {
		background: #f8f9fa;
		padding: 1.5rem;
		border-radius: 12px;
		margin: 2rem 0;
	}

	.performance-breakdown h3 {
		margin: 0 0 1rem 0;
		color: #2c3e50;
	}

	.breakdown-item {
		display: flex;
		justify-content: space-between;
		padding: 0.75rem 0;
		border-bottom: 1px solid #e0e0e0;
	}

	.breakdown-item:last-child {
		border-bottom: none;
	}

	.breakdown-item .value {
		font-weight: bold;
		color: #667eea;
	}

	.difficulty-info {
		background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
		padding: 1.5rem;
		border-radius: 12px;
		margin: 2rem 0;
	}

	.adaptation-reason {
		color: #666;
		font-size: 0.9rem;
		margin-top: 0.5rem;
	}

	.new-badges {
		background: #fff3e0;
		padding: 1.5rem;
		border-radius: 12px;
		margin: 2rem 0;
	}

	.badge {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 0.75rem;
		background: white;
		border-radius: 8px;
		margin: 0.5rem 0;
	}

	.badge-icon {
		font-size: 2rem;
	}

	.actions {
		display: flex;
		gap: 1rem;
		justify-content: center;
		margin-top: 2rem;
	}

	.actions button {
		padding: 0.8rem 2rem;
		border: none;
		border-radius: 8px;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s;
	}

	.actions button:first-child {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
	}

	.actions button:first-child:hover {
		transform: translateY(-2px);
	}

	.actions button:last-child {
		background: linear-gradient(135deg, #4CAF50, #45a049);
		color: white;
	}

	.actions button:last-child:hover {
		transform: translateY(-2px);
	}

	.help-modal {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.7);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
	}

	.help-content {
		background: white;
		padding: 2rem;
		border-radius: 16px;
		max-width: 600px;
		max-height: 80vh;
		overflow-y: auto;
		position: relative;
		box-shadow: 0 8px 32px rgba(0,0,0,0.3);
	}

	.close-button {
		position: absolute;
		top: 1rem;
		right: 1rem;
		width: 40px;
		height: 40px;
		border: none;
		background: #f44336;
		color: white;
		font-size: 1.5rem;
		border-radius: 50%;
		cursor: pointer;
	}

	.help-content h2 {
		color: #667eea;
		margin-bottom: 1.5rem;
	}

	.strategy {
		margin-bottom: 1.5rem;
		padding: 1rem;
		background: #f8f9fa;
		border-radius: 8px;
		border-left: 4px solid #667eea;
	}

	.strategy h3 {
		margin: 0 0 0.5rem 0;
		color: #2c3e50;
	}

	.strategy p {
		margin: 0;
		color: #555;
		line-height: 1.6;
	}
</style>

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
		SHOWING: 'showing',
		INPUT: 'input',
		FEEDBACK: 'feedback',
		COMPLETE: 'complete'
	};

	let state = STATE.LOADING;
	let difficulty = 5;
	let trials = [];
	let currentTrialIndex = 0;
	let currentTrial = null;
	let userNumbers = [];
	let userLetters = [];
	let showingSequence = false;
	let currentItemIndex = 0;
	let startTime = 0;
	let showHelp = false;
	let sessionResults = null;
	let taskId = null;

	// Available numbers and letters for input
	const NUMBERS = ['1', '2', '3', '4', '5', '6', '7', '8', '9'];
	const LETTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'R', 'S', 'T'];

	// Timings - adaptive based on difficulty
	function getItemDisplayTime(diff) {
		if (diff <= 3) return 1200; // Easy
		if (diff <= 6) return 1000; // Medium
		return 800;                 // Hard
	}

	function getInterItemInterval(diff) {
		if (diff <= 3) return 500;
		if (diff <= 6) return 400;
		return 300;
	}

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

			// Get user's current difficulty from their training plan
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
			console.log('📊 Letter-Number Sequencing - Loaded difficulty:', difficulty);

			// Generate session
			const response = await fetch(
				`http://localhost:8000/api/training/tasks/letter-number-sequencing/generate/${userId}?difficulty=${difficulty}&num_trials=8`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' }
				}
			);

			if (!response.ok) throw new Error('Failed to load session');

			const data = await response.json();
			trials = data.trials.map(t => ({
				...t,
				user_numbers: [],
				user_letters: [],
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
		userNumbers = [];
		userLetters = [];
		
		// Show ready screen
		state = STATE.READY;
		await new Promise(resolve => setTimeout(resolve, 1000));
		
		// Show sequence
		state = STATE.SHOWING;
		showingSequence = true;
		await playSequence();
		
		// Allow user input
		state = STATE.INPUT;
		startTime = Date.now();
	}

	async function playSequence() {
		const sequence = currentTrial.sequence;
		const displayTime = getItemDisplayTime(difficulty);
		const intervalTime = getInterItemInterval(difficulty);

		for (let i = 0; i < sequence.length; i++) {
			currentItemIndex = i;
			await new Promise(resolve => setTimeout(resolve, displayTime));
			
			if (i < sequence.length - 1) {
				currentItemIndex = -1;
				await new Promise(resolve => setTimeout(resolve, intervalTime));
			}
		}
		
		currentItemIndex = -1;
		showingSequence = false;
	}

	function addNumber(num) {
		if (state !== STATE.INPUT) return;
		if (userNumbers.includes(num)) return; // Can't add same number twice
		userNumbers = [...userNumbers, num];
	}

	function addLetter(letter) {
		if (state !== STATE.INPUT) return;
		if (userLetters.includes(letter)) return; // Can't add same letter twice
		userLetters = [...userLetters, letter];
	}

	function removeLastNumber() {
		if (userNumbers.length > 0) {
			userNumbers = userNumbers.slice(0, -1);
		}
	}

	function removeLastLetter() {
		if (userLetters.length > 0) {
			userLetters = userLetters.slice(0, -1);
		}
	}

	function clearNumbers() {
		userNumbers = [];
	}

	function clearLetters() {
		userLetters = [];
	}

	function submitResponse() {
		if (state !== STATE.INPUT) return;
		
		const reactionTime = Date.now() - startTime;
		trials[currentTrialIndex].user_numbers = userNumbers;
		trials[currentTrialIndex].user_letters = userLetters;
		trials[currentTrialIndex].reaction_time = reactionTime;
		
		// Show feedback
		state = STATE.FEEDBACK;
		
		setTimeout(() => {
			if (currentTrialIndex < trials.length - 1) {
				currentTrialIndex++;
				startTrial();
			} else {
				submitSession();
			}
		}, 1500);
	}

	function checkCorrect() {
		const numbersCorrect = JSON.stringify(userNumbers) === JSON.stringify(currentTrial.correct_numbers);
		const lettersCorrect = JSON.stringify(userLetters) === JSON.stringify(currentTrial.correct_letters);
		return numbersCorrect && lettersCorrect;
	}

	async function submitSession() {
		state = STATE.LOADING;
		
		try {
			const userData = JSON.parse(localStorage.getItem('user') || '{}');
			const userId = userData.id;

			taskId = $page.url.searchParams.get('taskId');
			const response = await fetch(
				`http://localhost:8000/api/training/tasks/letter-number-sequencing/submit/${userId}`,
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

<div class="lns-container">
	{#if state === STATE.LOADING}
		<div class="loading">
			<div class="spinner"></div>
			<p>Loading Letter-Number Sequencing Task...</p>
		</div>
	{:else if state === STATE.INSTRUCTIONS}
		<div class="instructions">
			<div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap;">
				<h1>🔢🔤 Letter-Number Sequencing</h1>
				<DifficultyBadge {difficulty} domain="Working Memory" />
			</div>

			<div class="instruction-card">
				<h2>How It Works</h2>
				<p>You'll see a mixed sequence of numbers and letters. Your task is to reorder them:</p>
				
				<div class="rules">
					<div class="rule-card">
						<div class="rule-number">1️⃣</div>
						<h3>Numbers First</h3>
						<p>Put all numbers in <strong>ascending order</strong><br/>(1, 2, 3...)</p>
					</div>
					<div class="rule-card">
						<div class="rule-number">2️⃣</div>
						<h3>Then Letters</h3>
						<p>Put all letters in <strong>alphabetical order</strong><br/>(A, B, C...)</p>
					</div>
				</div>

				<div class="example">
					<h3>📝 Example</h3>
					<div class="example-flow">
						<div class="example-box">
							<div class="example-label">You See:</div>
							<div class="example-sequence">B - 3 - A - 1</div>
						</div>
						<div class="arrow">→</div>
						<div class="example-box">
							<div class="example-label">You Answer:</div>
							<div class="example-answer">
								<span class="answer-numbers">1 - 3</span>
								<span class="answer-separator">then</span>
								<span class="answer-letters">A - B</span>
							</div>
						</div>
					</div>
				</div>
				
				<div class="tips">
					<h3>💡 Memory Strategies</h3>
					<ul>
						<li><strong>Categorize first:</strong> Mentally separate numbers from letters</li>
						<li><strong>Sort mentally:</strong> Order each group in your mind before clicking</li>
						<li><strong>Use rehearsal:</strong> Repeat the correct order silently</li>
					</ul>
				</div>
			</div>
			
			<button class="start-button" on:click={startSession} disabled={state !== STATE.INSTRUCTIONS}>
				Start Training Session
			</button>
		</div>
	{:else if state === STATE.READY}
		<div class="ready-screen">
			<h2>Trial {currentTrialIndex + 1} of {trials.length}</h2>
			<p>Watch the sequence carefully...</p>
		</div>
	{:else if state === STATE.SHOWING || state === STATE.INPUT}
		<div class="trial-screen">
			<div class="header">
				<div class="trial-info">
					<span class="trial-number">Trial {currentTrialIndex + 1}/{trials.length}</span>
					<span class="difficulty-badge">Level {difficulty}</span>
				</div>
				<button class="help-button" on:click={toggleHelp}>?</button>
			</div>

			{#if state === STATE.SHOWING}
				<p class="instruction">Memorize the sequence...</p>
				<div class="sequence-display">
					{#each currentTrial.sequence as item, index}
						<div 
							class="sequence-item" 
							class:active={currentItemIndex === index}
							class:number={!isNaN(item)}
							class:letter={isNaN(item)}
						>
							{item}
						</div>
					{/each}
				</div>
			{:else}
				<div class="input-header">
					<p class="instruction">
						<strong>Reorder:</strong> Numbers ascending (1, 2, 3...) then Letters alphabetical (A, B, C...)
					</p>
				</div>

				<div class="input-section">
					<!-- Numbers Section -->
					<div class="input-group">
						<h3>Numbers (Low → High)</h3>
						<div class="selected-items">
							{#if userNumbers.length === 0}
								<span class="placeholder">Select numbers...</span>
							{:else}
								{#each userNumbers as num}
									<span class="selected-item number">{num}</span>
								{/each}
							{/if}
						</div>
						<div class="button-grid numbers">
							{#each NUMBERS as num}
								<button 
									class="item-button number" 
									class:selected={userNumbers.includes(num)}
									class:available={currentTrial.sequence.includes(num)}
									disabled={!currentTrial.sequence.includes(num) || userNumbers.includes(num)}
									on:click={() => addNumber(num)}
								>
									{num}
								</button>
							{/each}
						</div>
						<div class="controls">
							<button class="control-btn" on:click={removeLastNumber} disabled={userNumbers.length === 0}>
								↶ Undo
							</button>
							<button class="control-btn" on:click={clearNumbers} disabled={userNumbers.length === 0}>
								✕ Clear
							</button>
						</div>
					</div>

					<!-- Letters Section -->
					<div class="input-group">
						<h3>Letters (A → Z)</h3>
						<div class="selected-items">
							{#if userLetters.length === 0}
								<span class="placeholder">Select letters...</span>
							{:else}
								{#each userLetters as letter}
									<span class="selected-item letter">{letter}</span>
								{/each}
							{/if}
						</div>
						<div class="button-grid letters">
							{#each LETTERS as letter}
								<button 
									class="item-button letter" 
									class:selected={userLetters.includes(letter)}
									class:available={currentTrial.sequence.includes(letter)}
									disabled={!currentTrial.sequence.includes(letter) || userLetters.includes(letter)}
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
					</div>
				</div>

				<div class="submit-section">
					<button 
						class="submit-button" 
						on:click={submitResponse}
						disabled={userNumbers.length === 0 && userLetters.length === 0}
					>
						Submit Answer
					</button>
				</div>
			{/if}
		</div>
	{:else if state === STATE.FEEDBACK}
		<div class="feedback-screen">
			<div class="feedback-icon {checkCorrect() ? 'correct' : 'incorrect'}">
				{checkCorrect() ? '✓' : '✗'}
			</div>
			<p class="feedback-text">
				{checkCorrect() ? 'Correct!' : 'Incorrect'}
			</p>
			{#if !checkCorrect()}
				<div class="correct-answer">
					<p>Correct answer:</p>
					<div class="answer-display">
						<span class="numbers">{currentTrial.correct_numbers.join(' - ')}</span>
						<span class="separator">then</span>
						<span class="letters">{currentTrial.correct_letters.join(' - ')}</span>
					</div>
				</div>
			{/if}
		</div>
	{:else if state === STATE.COMPLETE}
		<div class="complete-screen">
			<h1>Session Complete! 🎉</h1>
			
			<div class="results-grid">
				<div class="result-card">
					<div class="result-value">{sessionResults.metrics.score}</div>
					<div class="result-label">Score</div>
				</div>
				<div class="result-card">
					<div class="result-value">{sessionResults.metrics.accuracy.toFixed(1)}%</div>
					<div class="result-label">Accuracy</div>
				</div>
				<div class="result-card">
					<div class="result-value">{sessionResults.metrics.longest_sequence}</div>
					<div class="result-label">Longest Sequence</div>
				</div>
				<div class="result-card">
					<div class="result-value">{sessionResults.metrics.consistency.toFixed(1)}%</div>
					<div class="result-label">Consistency</div>
				</div>
			</div>

			<div class="breakdown">
				<h3>Performance Breakdown</h3>
				<div class="breakdown-row">
					<span>Numbers Accuracy:</span>
					<span>{sessionResults.metrics.numbers_accuracy.toFixed(1)}%</span>
				</div>
				<div class="breakdown-row">
					<span>Letters Accuracy:</span>
					<span>{sessionResults.metrics.letters_accuracy.toFixed(1)}%</span>
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
			<h2>Memory Strategies</h2>
			
			<div class="strategy">
				<h3>📊 Categorize First</h3>
				<p>Quickly identify which items are numbers and which are letters. Group them mentally before ordering.</p>
			</div>
			
			<div class="strategy">
				<h3>🔢 Sort Numbers</h3>
				<p>Arrange numbers from smallest to largest (1, 2, 3, 4...). This is your first group.</p>
			</div>
			
			<div class="strategy">
				<h3>🔤 Sort Letters</h3>
				<p>Arrange letters alphabetically (A, B, C, D...). This is your second group.</p>
			</div>
			
			<div class="strategy">
				<h3>🔄 Mental Rehearsal</h3>
				<p>Silently repeat the correct order 2-3 times before clicking to strengthen memory.</p>
			</div>
			
			<div class="strategy">
				<h3>✨ Chunking</h3>
				<p>For longer sequences, break them into smaller chunks (e.g., "1-3" and "A-B-D").</p>
			</div>
		</div>
	</div>
{/if}

<style>
	.lns-container {
		max-width: 1000px;
		margin: 0 auto;
		padding: 2rem;
		min-height: 100vh;
	}

	.loading {
		text-align: center;
		padding: 4rem 0;
	}

	.spinner {
		width: 50px;
		height: 50px;
		border: 4px solid #f3f3f3;
		border-top: 4px solid #4CAF50;
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
		color: #2c3e50;
		margin-bottom: 2rem;
	}

	.instruction-card {
		background: white;
		border-radius: 12px;
		padding: 2rem;
		margin: 2rem 0;
		box-shadow: 0 2px 8px rgba(0,0,0,0.1);
		text-align: left;
	}

	.rules {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
		margin: 1.5rem 0;
	}

	.rule-card {
		background: #f8f9fa;
		padding: 1.5rem;
		border-radius: 8px;
		border-left: 4px solid #4CAF50;
		text-align: center;
	}

	.rule-number {
		font-size: 2rem;
		margin-bottom: 0.5rem;
	}

	.rule-card h3 {
		margin: 0 0 0.5rem 0;
		color: #2c3e50;
	}

	.example {
		background: #e3f2fd;
		padding: 1.5rem;
		border-radius: 8px;
		margin: 1.5rem 0;
	}

	.example h3 {
		margin: 0 0 1rem 0;
		color: #1976D2;
	}

	.example-flow {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		flex-wrap: wrap;
	}

	.example-box {
		background: white;
		padding: 1rem;
		border-radius: 8px;
		min-width: 200px;
	}

	.example-label {
		font-size: 0.85rem;
		color: #666;
		margin-bottom: 0.5rem;
	}

	.example-sequence {
		font-size: 1.5rem;
		font-weight: bold;
		color: #2c3e50;
	}

	.example-answer {
		display: flex;
		gap: 0.5rem;
		align-items: center;
		font-size: 1.2rem;
		font-weight: bold;
	}

	.answer-numbers {
		color: #2196F3;
	}

	.answer-separator {
		color: #999;
		font-size: 0.9rem;
		font-weight: normal;
	}

	.answer-letters {
		color: #4CAF50;
	}

	.arrow {
		font-size: 2rem;
		color: #4CAF50;
	}

	.tips {
		background: #fff3cd;
		padding: 1.5rem;
		border-radius: 8px;
		margin-top: 1.5rem;
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
	}

	.start-button {
		background: #4CAF50;
		color: white;
		border: none;
		padding: 1rem 3rem;
		font-size: 1.2rem;
		border-radius: 8px;
		cursor: pointer;
		margin-top: 2rem;
		transition: background 0.3s;
	}

	.start-button:hover:not(:disabled) {
		background: #45a049;
	}

	.start-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.ready-screen {
		text-align: center;
		padding: 4rem 0;
	}

	.trial-screen {
		text-align: center;
	}

	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
	}

	.trial-info {
		display: flex;
		gap: 1rem;
		align-items: center;
	}

	.trial-number {
		background: #e8f5e9;
		padding: 0.5rem 1rem;
		border-radius: 20px;
		font-weight: 500;
	}

	.difficulty-badge {
		background: #e3f2fd;
		padding: 0.5rem 1rem;
		border-radius: 20px;
		font-weight: 500;
		color: #1976D2;
	}

	.help-button {
		width: 40px;
		height: 40px;
		border-radius: 50%;
		border: 2px solid #4CAF50;
		background: white;
		color: #4CAF50;
		font-size: 1.5rem;
		font-weight: bold;
		cursor: pointer;
		transition: all 0.3s;
	}

	.help-button:hover {
		background: #4CAF50;
		color: white;
	}

	.instruction {
		font-size: 1.2rem;
		margin-bottom: 1.5rem;
		color: #555;
	}

	.sequence-display {
		display: flex;
		gap: 1rem;
		justify-content: center;
		align-items: center;
		flex-wrap: wrap;
		padding: 2rem;
		min-height: 150px;
	}

	.sequence-item {
		width: 80px;
		height: 80px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 2.5rem;
		font-weight: bold;
		border-radius: 12px;
		border: 3px solid #ddd;
		background: #f5f5f5;
		transition: all 0.3s;
		opacity: 0.3;
	}

	.sequence-item.active {
		opacity: 1;
		transform: scale(1.2);
		box-shadow: 0 4px 12px rgba(0,0,0,0.2);
	}

	.sequence-item.active.number {
		background: linear-gradient(145deg, #2196F3, #1976D2);
		border-color: #1565C0;
		color: white;
	}

	.sequence-item.active.letter {
		background: linear-gradient(145deg, #4CAF50, #45a049);
		border-color: #2e7d32;
		color: white;
	}

	.input-section {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 2rem;
		margin: 2rem 0;
	}

	.input-group h3 {
		color: #2c3e50;
		margin-bottom: 1rem;
	}

	.selected-items {
		background: #f8f9fa;
		padding: 1rem;
		border-radius: 8px;
		min-height: 60px;
		display: flex;
		gap: 0.5rem;
		align-items: center;
		flex-wrap: wrap;
		margin-bottom: 1rem;
	}

	.placeholder {
		color: #999;
		font-style: italic;
	}

	.selected-item {
		padding: 0.5rem 1rem;
		border-radius: 6px;
		font-weight: bold;
		font-size: 1.2rem;
	}

	.selected-item.number {
		background: #2196F3;
		color: white;
	}

	.selected-item.letter {
		background: #4CAF50;
		color: white;
	}

	.button-grid {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		gap: 0.5rem;
		margin-bottom: 1rem;
	}

	.button-grid.letters {
		grid-template-columns: repeat(6, 1fr);
	}

	.item-button {
		aspect-ratio: 1;
		border: 2px solid #ddd;
		background: white;
		border-radius: 8px;
		font-size: 1.2rem;
		font-weight: bold;
		cursor: pointer;
		transition: all 0.2s;
	}

	.item-button.number {
		color: #2196F3;
		border-color: #2196F3;
	}

	.item-button.letter {
		color: #4CAF50;
		border-color: #4CAF50;
	}

	.item-button.available:hover:not(:disabled) {
		transform: translateY(-2px);
		box-shadow: 0 4px 8px rgba(0,0,0,0.15);
	}

	.item-button.number.available:hover:not(:disabled) {
		background: #e3f2fd;
	}

	.item-button.letter.available:hover:not(:disabled) {
		background: #e8f5e9;
	}

	.item-button:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}

	.item-button.selected {
		opacity: 0.4;
	}

	.controls {
		display: flex;
		gap: 0.5rem;
		justify-content: center;
	}

	.control-btn {
		padding: 0.5rem 1rem;
		border: 2px solid #FF9800;
		background: white;
		color: #FF9800;
		border-radius: 6px;
		font-size: 0.9rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
	}

	.control-btn:hover:not(:disabled) {
		background: #FF9800;
		color: white;
		transform: translateY(-2px);
	}

	.control-btn:disabled {
		opacity: 0.3;
		cursor: not-allowed;
		border-color: #ccc;
		color: #ccc;
	}

	.submit-section {
		margin-top: 2rem;
	}

	.submit-button {
		background: linear-gradient(135deg, #4CAF50, #45a049);
		color: white;
		border: none;
		padding: 1rem 3rem;
		font-size: 1.2rem;
		font-weight: bold;
		border-radius: 8px;
		cursor: pointer;
		transition: all 0.3s;
		box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
	}

	.submit-button:hover:not(:disabled) {
		transform: translateY(-2px);
		box-shadow: 0 6px 16px rgba(76, 175, 80, 0.4);
	}

	.submit-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.feedback-screen {
		text-align: center;
		padding: 4rem 0;
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
		background: #4CAF50;
	}

	.feedback-icon.incorrect {
		background: #f44336;
	}

	.feedback-text {
		font-size: 2rem;
		font-weight: bold;
	}

	.correct-answer {
		margin-top: 2rem;
		background: #f8f9fa;
		padding: 1.5rem;
		border-radius: 12px;
		max-width: 500px;
		margin-left: auto;
		margin-right: auto;
	}

	.answer-display {
		display: flex;
		gap: 0.5rem;
		align-items: center;
		justify-content: center;
		font-size: 1.3rem;
		font-weight: bold;
		margin-top: 1rem;
	}

	.answer-display .numbers {
		color: #2196F3;
	}

	.answer-display .separator {
		color: #999;
		font-size: 1rem;
		font-weight: normal;
	}

	.answer-display .letters {
		color: #4CAF50;
	}

	.complete-screen {
		text-align: center;
	}

	.results-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: 1rem;
		margin: 2rem 0;
	}

	.result-card {
		background: white;
		padding: 1.5rem;
		border-radius: 12px;
		box-shadow: 0 2px 8px rgba(0,0,0,0.1);
	}

	.result-value {
		font-size: 2.5rem;
		font-weight: bold;
		color: #4CAF50;
		margin-bottom: 0.5rem;
	}

	.result-label {
		color: #666;
		font-size: 0.9rem;
	}

	.breakdown {
		background: white;
		padding: 1.5rem;
		border-radius: 12px;
		box-shadow: 0 2px 8px rgba(0,0,0,0.1);
		margin: 2rem 0;
	}

	.breakdown h3 {
		margin: 0 0 1rem 0;
		color: #2c3e50;
	}

	.breakdown-row {
		display: flex;
		justify-content: space-between;
		padding: 0.5rem 0;
		border-bottom: 1px solid #eee;
	}

	.breakdown-row:last-child {
		border-bottom: none;
	}

	.difficulty-info {
		background: #e3f2fd;
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
		padding: 0.5rem;
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
		cursor: pointer;
		transition: all 0.3s;
	}

	.actions button:first-child {
		background: #2196F3;
		color: white;
	}

	.actions button:first-child:hover {
		background: #1976D2;
	}

	.actions button:last-child {
		background: #4CAF50;
		color: white;
	}

	.actions button:last-child:hover {
		background: #45a049;
	}

	.help-modal {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
	}

	.help-content {
		background: white;
		padding: 2rem;
		border-radius: 12px;
		max-width: 600px;
		max-height: 80vh;
		overflow-y: auto;
		position: relative;
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
		color: #2c3e50;
		margin-bottom: 1.5rem;
	}

	.strategy {
		margin-bottom: 1.5rem;
		padding: 1rem;
		background: #f8f9fa;
		border-radius: 8px;
		border-left: 4px solid #4CAF50;
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

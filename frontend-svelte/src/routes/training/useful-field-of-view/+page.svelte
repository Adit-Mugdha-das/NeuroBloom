<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import { generateUFOVTrial, submitUFOVResponse } from '$lib/api.js';
	import { onDestroy, onMount } from 'svelte';
	
	// User ID from localStorage
	let userId = null;
	let taskId = null;
	
	// Game state
	let gamePhase = 'intro'; // intro, ready, stimulus, response, results
	let currentTrial = null;
	let trialData = null;
	let difficulty = 1;
	
	// Response tracking
	let centralResponse = null;
	let peripheralResponse = null;
	let responseStartTime = null;
	let responseTime = 0;
	
	// Results
	let results = null;
	let loading = false;
	let error = null;
	
	// Stimulus timing
	let stimulusTimer = null;
	let showStimulus = false;
	let fixationTimer = null;
	
	// Trial counter
	let trialsCompleted = 0;
	const TRIALS_PER_SESSION = 10;
	
	onMount(() => {
		const user = JSON.parse(localStorage.getItem('user') || '{}');
		userId = user.id;
		
		if (!userId) {
			goto('/login');
			return;
		}
	});
	
	onDestroy(() => {
		if (stimulusTimer) clearTimeout(stimulusTimer);
		if (fixationTimer) clearTimeout(fixationTimer);
	});
	
	async function startTask() {
		await loadTrial();
	}
	
	async function loadTrial() {
		loading = true;
		error = null;
		
		// Complete state reset to prevent cross-contamination
		results = null;
		centralResponse = null;
		peripheralResponse = null;
		responseStartTime = null;
		responseTime = 0;
		showStimulus = false;

		try {
			console.log('📊 UFOV - Loading trial for user:', userId);
			const data = await generateUFOVTrial(userId);
			console.log('📊 UFOV - Received data:', data);

			trialData = data.trial;
			difficulty = data.current_difficulty;
			currentTrial = data;
			
			console.log('📊 UFOV - Difficulty:', difficulty, 'Trial data:', trialData);

			// Show fixation, then stimulus
			gamePhase = 'ready';
			loading = false; // Set loading to false so the ready phase shows

			setTimeout(() => {
				showStimulusPhase();
			}, 1500);
			
		} catch (err) {
			console.error('❌ UFOV - Error loading trial:', err);
			error = 'Failed to load trial. Please try again.';
			loading = false;
			gamePhase = 'intro'; // Go back to intro on error
		}
	}
	
	function showStimulusPhase() {
		gamePhase = 'stimulus';
		showStimulus = true;
		responseStartTime = Date.now();
		
		// Hide stimulus after presentation time
		stimulusTimer = setTimeout(() => {
			showStimulus = false;
			gamePhase = 'response';
		}, trialData.presentation_time_ms);
	}
	
	function selectCentralTarget(target) {
		centralResponse = target;
		
		// If central-only subtest, submit immediately
		if (trialData.subtest === 'central_only') {
			submitResponse();
		}
	}
	
	function selectPeripheralPosition(position) {
		peripheralResponse = position;
		
		// If both responses collected, submit
		if (centralResponse && peripheralResponse) {
			submitResponse();
		}
	}
	
	async function submitResponse() {
		responseTime = Date.now() - responseStartTime;
		loading = true;
		taskId = $page.url.searchParams.get('taskId');
		
		try {
			const data = await submitUFOVResponse(userId, {
				central_response: centralResponse,
				peripheral_response: peripheralResponse,
				trial_data: trialData,
				response_time: responseTime,
				task_id: taskId
			});
			
			// Store both results and trial data (with correct answers)
			results = {
				...data,
				// Include user responses and correct answers for comparison
				user_central_response: centralResponse,
				user_peripheral_response: peripheralResponse,
				correct_central_target: trialData.central_target,
				correct_peripheral_position: trialData.peripheral_position,
				correct_peripheral_target: trialData.peripheral_target
			};
			trialsCompleted++;
			gamePhase = 'results';
			
		} catch (err) {
			console.error('Error submitting response:', err);
			error = 'Failed to submit response. Please try again.';
		} finally {
			loading = false;
		}
	}
	
	function nextTrial() {
		if (trialsCompleted >= TRIALS_PER_SESSION) {
			// Session complete - return to training page to show updated progress
			goto('/training');
		} else {
			// loadTrial() now handles all state resets
			loadTrial();
		}
	}
	
	function exitTask() {
		goto('/training');
	}
	
	// Helper function to get peripheral positions for UI
	function getPeripheralPositions() {
		return [
			{ angle: 0, label: "3 o'clock", x: 1, y: 0 },
			{ angle: 45, label: "1:30", x: 0.707, y: -0.707 },
			{ angle: 90, label: "12 o'clock", x: 0, y: -1 },
			{ angle: 135, label: "10:30", x: -0.707, y: -0.707 },
			{ angle: 180, label: "9 o'clock", x: -1, y: 0 },
			{ angle: 225, label: "7:30", x: -0.707, y: 0.707 },
			{ angle: 270, label: "6 o'clock", x: 0, y: 1 },
			{ angle: 315, label: "4:30", x: 0.707, y: 0.707 }
		];
	}
	
	// Performance badge
	function getPerformanceBadge(performance) {
		const badges = {
			perfect: { color: '#10b981', icon: '🎯', text: 'Perfect!' },
			partial: { color: '#f59e0b', icon: '👍', text: 'Good Try' },
			incorrect: { color: '#ef4444', icon: '💪', text: 'Keep Practicing' }
		};
		return badges[performance] || badges.incorrect;
	}
</script>

<div class="ufov-container">
	<div class="ufov-header">
		<button class="back-button" on:click={exitTask}>
			← Back to Dashboard
		</button>
		<div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap;">
			<h1>Useful Field of View (UFOV)</h1>
			<DifficultyBadge difficulty={difficulty} domain="Visual Scanning" />
		</div>
		<div class="clinical-badge">
			<span class="badge-icon">🚗</span>
			<span class="badge-text">Driving Safety Assessment</span>
		</div>
	</div>
	
	{#if error}
		<div class="error-message">
			<p>{error}</p>
			<button on:click={loadTrial}>Try Again</button>
		</div>
	{/if}
	
	{#if gamePhase === 'intro'}
		<div class="intro-section">
			<div class="intro-card">
				<h2>Visual Processing & Divided Attention</h2>
				<p class="intro-description">
					The Useful Field of View (UFOV) test measures your ability to quickly process 
					visual information and divide your attention across your visual field. This is 
					a critical skill for safe driving and everyday activities.
				</p>
				
				<div class="clinical-validation">
					<h3>📋 Clinical Validation</h3>
					<p><strong>Ball et al., 1993</strong> - Predicts driving safety and crash risk</p>
					<p>Widely used in MS research to assess visual processing deficits</p>
				</div>
				
				<div class="instructions-grid">
					<div class="instruction-item">
						<div class="instruction-number">1</div>
						<div class="instruction-content">
							<h4>Focus on the Center</h4>
							<p>A fixation cross (+) will appear. Keep your eyes focused on the center.</p>
						</div>
					</div>
					
					<div class="instruction-item">
						<div class="instruction-number">2</div>
						<div class="instruction-content">
							<h4>Brief Display</h4>
							<p>Images will flash very briefly (150-800ms). Process them quickly!</p>
						</div>
					</div>
					
					<div class="instruction-item">
						<div class="instruction-number">3</div>
						<div class="instruction-content">
							<h4>Identify Targets</h4>
							<p>Report what you saw in the center and/or periphery based on the task.</p>
						</div>
					</div>
				</div>
				
				<div class="task-details">
					<h3>Three Subtests:</h3>
					<div class="subtest-list">
						<div class="subtest-item">
							<span class="subtest-icon">⚡</span>
							<div>
								<strong>Central ID Only</strong>
								<p>Identify vehicle in center (car or truck) - Tests processing speed</p>
							</div>
						</div>
						<div class="subtest-item">
							<span class="subtest-icon">👀</span>
							<div>
								<strong>Central + Peripheral</strong>
								<p>Identify center vehicle AND locate peripheral shape - Tests divided attention</p>
							</div>
						</div>
						<div class="subtest-item">
							<span class="subtest-icon">🎯</span>
							<div>
								<strong>With Distractors</strong>
								<p>Same as above but with visual clutter - Tests selective attention</p>
							</div>
						</div>
					</div>
				</div>
				
				<div class="progress-info">
					<p>Complete <strong>{TRIALS_PER_SESSION} trials</strong> to finish this session</p>
					<p class="difficulty-level">Current Level: <strong>{difficulty}</strong>/10</p>
				</div>
				
				<button class="start-button" on:click={startTask}>
					Begin UFOV Assessment
				</button>
			</div>
		</div>
	{/if}

	{#if gamePhase === 'ready'}
		<div class="ready-phase">
			<div class="ready-card">
				<h2>Get Ready</h2>
				<p class="trial-info">Trial {trialsCompleted + 1} of {TRIALS_PER_SESSION}</p>
				<p class="subtest-name">{trialData?.description}</p>
				<p class="instructions-text">{trialData?.instructions}</p>
				
				<div class="fixation-container">
					<div class="fixation-cross">+</div>
					<p class="fixation-text">Focus on the center cross</p>
				</div>
				
				<p class="timing-info">
					Display time: <strong>{trialData?.presentation_time_ms}ms</strong>
				</p>
			</div>
		</div>
	{/if}
	
	{#if gamePhase === 'stimulus'}
		<div class="stimulus-phase">
			<div class="stimulus-arena">
				{#if showStimulus}
					<!-- Central target -->
					<div class="central-target">
						{#if trialData.central_target === 'car'}
							<div class="vehicle-icon car">🚗</div>
						{:else}
							<div class="vehicle-icon truck">🚚</div>
						{/if}
					</div>
					
					<!-- Peripheral target (if applicable) -->
					{#if trialData.peripheral_target && trialData.peripheral_angle !== null}
						<div 
							class="peripheral-target"
							style="
								left: {50 + (Math.cos(trialData.peripheral_angle * Math.PI / 180) * 40)}%;
								top: {50 - (Math.sin(trialData.peripheral_angle * Math.PI / 180) * 40)}%;
							"
						>
							{#if trialData.peripheral_target === 'circle'}
								<div class="shape-icon circle"></div>
							{:else if trialData.peripheral_target === 'triangle'}
								<div class="shape-icon triangle"></div>
							{:else if trialData.peripheral_target === 'square'}
								<div class="shape-icon square"></div>
							{/if}
						</div>
					{/if}
					
					<!-- Distractors (if applicable) -->
					{#if trialData.distractors && trialData.distractors.length > 0}
						{#each trialData.distractors as distractor}
							<div 
								class="distractor"
								style="
									left: {50 + (Math.cos(distractor.angle * Math.PI / 180) * distractor.radius * 40)}%;
									top: {50 - (Math.sin(distractor.angle * Math.PI / 180) * distractor.radius * 40)}%;
								"
							>
								{#if distractor.shape === 'circle'}
									<div class="shape-icon circle distractor-shape"></div>
								{:else if distractor.shape === 'triangle'}
									<div class="shape-icon triangle distractor-shape"></div>
								{:else if distractor.shape === 'square'}
									<div class="shape-icon square distractor-shape"></div>
								{/if}
							</div>
						{/each}
					{/if}
				{:else}
					<div class="fixation-cross">+</div>
				{/if}
			</div>
		</div>
	{/if}
	
	{#if gamePhase === 'response'}
		<div class="response-phase">
			<div class="response-card">
				<h2>What Did You See?</h2>
				<p class="response-instruction">{trialData?.instructions}</p>
				
				<!-- Central target selection -->
				<div class="response-section">
					<h3>Central Vehicle:</h3>
					<div class="central-options">
						<button 
							class="option-button {centralResponse === 'car' ? 'selected' : ''}"
							on:click={() => selectCentralTarget('car')}
							disabled={loading}
						>
							<span class="option-icon">🚗</span>
							<span class="option-label">Car</span>
						</button>
						<button 
							class="option-button {centralResponse === 'truck' ? 'selected' : ''}"
							on:click={() => selectCentralTarget('truck')}
							disabled={loading}
						>
							<span class="option-icon">🚚</span>
							<span class="option-label">Truck</span>
						</button>
					</div>
				</div>
				
				<!-- Peripheral position selection (if applicable) -->
				{#if trialData?.subtest !== 'central_only'}
					<div class="response-section">
						<h3>Peripheral Shape Location:</h3>
						<p class="peripheral-hint">Where was the {trialData.peripheral_target}?</p>
						
						<div class="peripheral-clock">
							{#each getPeripheralPositions() as position}
								<button 
									class="clock-button"
									class:selected={peripheralResponse === position.label}
									style="
										left: {50 + (position.x * 40)}%;
										top: {50 + (position.y * 40)}%;
									"
									on:click={() => selectPeripheralPosition(position.label)}
									disabled={!centralResponse || loading}
								>
									{position.label}
								</button>
							{/each}
							<div class="clock-center">
								<div class="clock-cross">+</div>
							</div>
						</div>
						
						{#if !centralResponse}
							<p class="selection-note">Select central vehicle first</p>
						{/if}
					</div>
				{/if}
				
				{#if loading}
					<div class="loading-indicator">
						<div class="spinner"></div>
						<p>Evaluating response...</p>
					</div>
				{/if}
			</div>
		</div>
	{/if}
	
	{#if gamePhase === 'results' && results}
		<div class="results-phase">
			<div class="results-card">
				<div class="performance-header" style="background: {getPerformanceBadge(results.performance).color}">
					<span class="performance-icon">{getPerformanceBadge(results.performance).icon}</span>
					<h2>{getPerformanceBadge(results.performance).text}</h2>
				</div>
				
				<div class="results-content">
					<div class="score-display">
						<div class="score-circle" style="background: linear-gradient(135deg, {getPerformanceBadge(results.performance).color}, {getPerformanceBadge(results.performance).color}aa)">
							<div class="score-value">{results.score}</div>
							<div class="score-label">Score</div>
						</div>
					</div>
					
					<div class="metrics-grid">
						<div class="metric-card">
							<div class="metric-label">Accuracy</div>
							<div class="metric-value">{((results.accuracy || 0) * 100).toFixed(0)}%</div>
						</div>
						
						<div class="metric-card">
							<div class="metric-label">Response Time</div>
							<div class="metric-value">{results.response_time}ms</div>
						</div>
						
						<div class="metric-card">
							<div class="metric-label">Processing Speed</div>
							<div class="metric-value">{results.processing_speed_score.toFixed(2)}</div>
						</div>
						
						<div class="metric-card">
							<div class="metric-label">Presentation Time</div>
							<div class="metric-value">{results.presentation_time_ms}ms</div>
						</div>
					</div>
					
					<div class="response-breakdown">
						<h3>Response Details</h3>
						<div class="breakdown-grid">
							<div class="breakdown-item">
								<span class="breakdown-label">Central Target:</span>
								<span class="breakdown-value {results.central_correct ? 'correct' : 'incorrect'}">
									{results.central_correct ? '✓ Correct' : '✗ Incorrect'}
								</span>
							</div>
							{#if results.subtest === 'central_peripheral' || results.subtest === 'central_peripheral_distractors'}
								<div class="breakdown-item">
									<span class="breakdown-label">Peripheral Target:</span>
									<span class="breakdown-value {results.peripheral_correct ? 'correct' : 'incorrect'}">
										{results.peripheral_correct ? '✓ Correct' : '✗ Incorrect'}
									</span>
								</div>
							{/if}
							<div class="breakdown-item">
								<span class="breakdown-label">Subtest:</span>
								<span class="breakdown-value">{results.subtest.replace(/_/g, ' ')}</span>
							</div>
						</div>

						<!-- Answer Comparison Section -->
						{#if results.user_central_response}
							<div class="answer-comparison">
								<h4>📋 Answer Review</h4>

								<!-- Central Target Comparison -->
								<div class="comparison-row">
									<div class="comparison-label">Central Vehicle:</div>
									<div class="comparison-content">
										<div class="answer-item">
											<span class="answer-tag">Your Answer:</span>
											<span class="answer-text {results.central_correct ? 'answer-correct' : 'answer-wrong'}">
												{results.user_central_response === 'car' ? '🚗 Car' : '🚚 Truck'}
											</span>
										</div>
										<div class="answer-item">
											<span class="answer-tag">Correct Answer:</span>
											<span class="answer-text answer-correct">
												{results.correct_central_target === 'car' ? '🚗 Car' : '🚚 Truck'}
											</span>
										</div>
									</div>
								</div>

								<!-- Peripheral Target Comparison (if applicable) -->
								{#if results.subtest === 'central_peripheral' || results.subtest === 'central_peripheral_distractors'}
									<div class="comparison-row">
										<div class="comparison-label">Peripheral Shape:</div>
										<div class="comparison-content">
											<div class="answer-item">
												<span class="answer-tag">Shape Type:</span>
												<span class="answer-text answer-info">
													{results.correct_peripheral_target === 'circle' ? '⭕ Circle' :
													 results.correct_peripheral_target === 'triangle' ? '🔺 Triangle' : '⬜ Square'}
												</span>
											</div>
											<div class="answer-item">
												<span class="answer-tag">Your Location:</span>
												<span class="answer-text {results.peripheral_correct ? 'answer-correct' : 'answer-wrong'}">
													{results.user_peripheral_response || 'Not selected'}
												</span>
											</div>
											<div class="answer-item">
												<span class="answer-tag">Correct Location:</span>
												<span class="answer-text answer-correct">
													{results.correct_peripheral_position}
												</span>
											</div>
										</div>
									</div>

									{#if !results.peripheral_correct && results.correct_peripheral_position}
										<div class="location-hint">
											<span class="hint-icon">💡</span>
											<span class="hint-text">
												The {results.correct_peripheral_target} was at <strong>{results.correct_peripheral_position}</strong>
												{#if results.user_peripheral_response}
													, but you selected <strong>{results.user_peripheral_response}</strong>
												{/if}
											</span>
										</div>
									{/if}
								{/if}
							</div>
						{/if}
					</div>
					
					<div class="feedback-section">
						<p class="feedback-message">{results.feedback_message}</p>
					</div>
					
					{#if results.new_badges && results.new_badges.length > 0}
						<div class="badges-earned">
							<h3>🏆 Badges Earned!</h3>
							<div class="badge-list">
								{#each results.new_badges as badge}
									<div class="badge-item">
										<span class="badge-icon-large">{badge.icon}</span>
										<div>
											<strong>{badge.name}</strong>
											<p>{badge.description}</p>
										</div>
									</div>
								{/each}
							</div>
						</div>
					{/if}
					
					<div class="difficulty-info">
						<p>
							{#if results.new_difficulty > results.old_difficulty}
								📈 <strong>Level Up!</strong> Advancing to level {results.new_difficulty}
							{:else if results.new_difficulty < results.old_difficulty}
								📉 Adjusting to level {results.new_difficulty} for better learning
							{:else}
								✓ Staying at level {results.new_difficulty}
							{/if}
						</p>
						<p class="adaptation-reason">{results.adaptation_reason}</p>
					</div>
					
					<div class="progress-tracker">
						<p>Progress: {trialsCompleted} / {TRIALS_PER_SESSION} trials completed</p>
						<div class="progress-bar">
							<div class="progress-fill" style="width: {(trialsCompleted / TRIALS_PER_SESSION) * 100}%"></div>
						</div>
					</div>
					
					<div class="action-buttons">
						{#if trialsCompleted < TRIALS_PER_SESSION}
							<button class="primary-button" on:click={nextTrial}>
								Next Trial ({TRIALS_PER_SESSION - trialsCompleted} remaining)
							</button>
						{:else}
							<button class="primary-button" on:click={exitTask}>
								Complete Session ✓
							</button>
						{/if}
						<button class="secondary-button" on:click={exitTask}>
							Exit to Dashboard
						</button>
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.ufov-container {
		min-height: 100vh;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		padding: 2rem;
	}
	
	.ufov-header {
		max-width: 1200px;
		margin: 0 auto 2rem;
		text-align: center;
		color: white;
	}
	
	.back-button {
		position: absolute;
		top: 2rem;
		left: 2rem;
		background: rgba(255, 255, 255, 0.2);
		color: white;
		border: none;
		padding: 0.75rem 1.5rem;
		border-radius: 8px;
		cursor: pointer;
		font-size: 1rem;
		transition: background 0.3s;
	}
	
	.back-button:hover {
		background: rgba(255, 255, 255, 0.3);
	}
	
	.ufov-header h1 {
		font-size: 2.5rem;
		margin: 0 0 0.5rem 0;
	}
	
	.clinical-badge {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		background: rgba(255, 255, 255, 0.2);
		padding: 0.5rem 1.5rem;
		border-radius: 20px;
		font-size: 0.95rem;
	}
	
	.badge-icon {
		font-size: 1.2rem;
	}
	
	/* Error message */
	.error-message {
		max-width: 600px;
		margin: 2rem auto;
		background: #fee;
		color: #c33;
		padding: 1.5rem;
		border-radius: 12px;
		text-align: center;
	}
	
	.error-message button {
		margin-top: 1rem;
		background: #c33;
		color: white;
		border: none;
		padding: 0.75rem 2rem;
		border-radius: 8px;
		cursor: pointer;
		font-size: 1rem;
	}
	
	/* Intro section */
	.intro-section {
		max-width: 900px;
		margin: 0 auto;
	}
	
	.intro-card {
		background: white;
		border-radius: 16px;
		padding: 3rem;
		box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
	}
	
	.intro-card h2 {
		color: #667eea;
		font-size: 2rem;
		margin: 0 0 1rem 0;
	}
	
	.intro-description {
		font-size: 1.1rem;
		line-height: 1.6;
		color: #555;
		margin-bottom: 2rem;
	}
	
	.clinical-validation {
		background: #f0f4ff;
		padding: 1.5rem;
		border-radius: 12px;
		margin-bottom: 2rem;
		border-left: 4px solid #667eea;
	}
	
	.clinical-validation h3 {
		color: #667eea;
		margin: 0 0 0.5rem 0;
	}
	
	.clinical-validation p {
		margin: 0.25rem 0;
		color: #555;
	}
	
	.instructions-grid {
		display: grid;
		gap: 1.5rem;
		margin: 2rem 0;
	}
	
	.instruction-item {
		display: flex;
		gap: 1rem;
		align-items: flex-start;
	}
	
	.instruction-number {
		width: 40px;
		height: 40px;
		background: linear-gradient(135deg, #667eea, #764ba2);
		color: white;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.2rem;
		font-weight: bold;
		flex-shrink: 0;
	}
	
	.instruction-content h4 {
		margin: 0 0 0.5rem 0;
		color: #333;
	}
	
	.instruction-content p {
		margin: 0;
		color: #666;
	}
	
	.task-details {
		margin: 2rem 0;
		background: #f8f9fa;
		padding: 1.5rem;
		border-radius: 12px;
	}
	
	.task-details h3 {
		color: #667eea;
		margin: 0 0 1rem 0;
	}
	
	.subtest-list {
		display: grid;
		gap: 1rem;
	}
	
	.subtest-item {
		display: flex;
		gap: 1rem;
		align-items: flex-start;
		background: white;
		padding: 1rem;
		border-radius: 8px;
	}
	
	.subtest-icon {
		font-size: 1.5rem;
		flex-shrink: 0;
	}
	
	.subtest-item strong {
		color: #667eea;
		display: block;
		margin-bottom: 0.25rem;
	}
	
	.subtest-item p {
		margin: 0;
		color: #666;
		font-size: 0.95rem;
	}
	
	.progress-info {
		margin: 2rem 0;
		text-align: center;
		color: #555;
	}
	
	.progress-info p {
		margin: 0.5rem 0;
	}
	
	.difficulty-level {
		color: #667eea;
		font-size: 1.1rem;
	}
	
	.start-button {
		width: 100%;
		background: linear-gradient(135deg, #667eea, #764ba2);
		color: white;
		border: none;
		padding: 1.25rem;
		border-radius: 12px;
		font-size: 1.2rem;
		font-weight: bold;
		cursor: pointer;
		transition: transform 0.2s, box-shadow 0.2s;
	}
	
	.start-button:hover {
		transform: translateY(-2px);
		box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
	}
	
	/* Ready phase */
	.ready-phase {
		max-width: 700px;
		margin: 0 auto;
	}
	
	.ready-card {
		background: white;
		border-radius: 16px;
		padding: 3rem;
		text-align: center;
		box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
	}
	
	.ready-card h2 {
		color: #667eea;
		font-size: 2rem;
		margin: 0 0 1rem 0;
	}
	
	.trial-info {
		color: #764ba2;
		font-size: 1.2rem;
		font-weight: bold;
		margin: 0.5rem 0;
	}
	
	.subtest-name {
		color: #555;
		font-size: 1.1rem;
		margin: 1rem 0;
	}
	
	.instructions-text {
		background: #f0f4ff;
		padding: 1rem;
		border-radius: 8px;
		color: #667eea;
		font-weight: bold;
		margin: 1.5rem 0;
	}
	
	.fixation-container {
		margin: 3rem 0;
	}
	
	.fixation-cross {
		font-size: 4rem;
		color: #333;
		font-weight: bold;
		margin-bottom: 1rem;
	}
	
	.fixation-text {
		color: #666;
		font-style: italic;
	}
	
	.timing-info {
		color: #764ba2;
		font-size: 1.1rem;
	}
	
	/* Stimulus phase */
	.stimulus-phase {
		max-width: 800px;
		margin: 0 auto;
	}
	
	.stimulus-arena {
		background: white;
		border-radius: 16px;
		width: 700px;
		height: 700px;
		margin: 0 auto;
		position: relative;
		box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.central-target {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		z-index: 10;
	}
	
	.vehicle-icon {
		font-size: 4rem;
	}
	
	.peripheral-target {
		position: absolute;
		transform: translate(-50%, -50%);
		z-index: 5;
	}
	
	.distractor {
		position: absolute;
		transform: translate(-50%, -50%);
		z-index: 3;
		opacity: 0.8;
	}
	
	.shape-icon {
		width: 40px;
		height: 40px;
	}
	
	.shape-icon.circle {
		background: #667eea;
		border-radius: 50%;
	}
	
	.shape-icon.triangle {
		width: 0;
		height: 0;
		border-left: 20px solid transparent;
		border-right: 20px solid transparent;
		border-bottom: 35px solid #667eea;
	}
	
	.shape-icon.square {
		background: #667eea;
	}
	
	.shape-icon.distractor-shape {
		opacity: 0.4;
	}
	
	/* Response phase */
	.response-phase {
		max-width: 800px;
		margin: 0 auto;
	}
	
	.response-card {
		background: white;
		border-radius: 16px;
		padding: 3rem;
		box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
	}
	
	.response-card h2 {
		color: #667eea;
		font-size: 2rem;
		margin: 0 0 1rem 0;
		text-align: center;
	}
	
	.response-instruction {
		text-align: center;
		color: #666;
		font-size: 1.1rem;
		margin-bottom: 2rem;
	}
	
	.response-section {
		margin: 2rem 0;
	}
	
	.response-section h3 {
		color: #667eea;
		margin: 0 0 1rem 0;
	}
	
	.central-options {
		display: flex;
		gap: 1.5rem;
		justify-content: center;
	}
	
	.option-button {
		background: white;
		border: 3px solid #ddd;
		border-radius: 12px;
		padding: 2rem 3rem;
		cursor: pointer;
		transition: all 0.3s;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}
	
	.option-button:hover {
		border-color: #667eea;
		transform: translateY(-4px);
		box-shadow: 0 8px 20px rgba(102, 126, 234, 0.2);
	}
	
	.option-button.selected {
		border-color: #667eea;
		background: linear-gradient(135deg, #667eea, #764ba2);
		color: white;
	}
	
	.option-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	
	.option-icon {
		font-size: 3rem;
	}
	
	.option-label {
		font-size: 1.2rem;
		font-weight: bold;
	}
	
	.peripheral-hint {
		text-align: center;
		color: #666;
		margin-bottom: 1.5rem;
	}
	
	.peripheral-clock {
		position: relative;
		width: 400px;
		height: 400px;
		margin: 0 auto;
		background: #f8f9fa;
		border-radius: 50%;
		border: 3px solid #ddd;
	}
	
	.clock-button {
		position: absolute;
		transform: translate(-50%, -50%);
		background: white;
		border: 2px solid #667eea;
		color: #667eea;
		padding: 0.5rem 1rem;
		border-radius: 8px;
		cursor: pointer;
		font-size: 0.9rem;
		font-weight: bold;
		transition: all 0.3s;
		white-space: nowrap;
	}
	
	.clock-button:hover {
		background: #667eea;
		color: white;
		transform: translate(-50%, -50%) scale(1.1);
	}
	
	.clock-button.selected {
		background: linear-gradient(135deg, #667eea, #764ba2);
		color: white;
		border-color: #764ba2;
	}
	
	.clock-button:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}
	
	.clock-center {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 60px;
		height: 60px;
		background: white;
		border-radius: 50%;
		border: 3px solid #667eea;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.clock-cross {
		font-size: 2rem;
		color: #667eea;
		font-weight: bold;
	}
	
	.selection-note {
		text-align: center;
		color: #999;
		font-style: italic;
		margin-top: 1rem;
	}
	
	.loading-indicator {
		text-align: center;
		margin-top: 2rem;
	}
	
	.spinner {
		width: 40px;
		height: 40px;
		border: 4px solid #f3f3f3;
		border-top: 4px solid #667eea;
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin: 0 auto 1rem;
	}
	
	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}
	
	/* Results phase */
	.results-phase {
		max-width: 900px;
		margin: 0 auto;
	}
	
	.results-card {
		background: white;
		border-radius: 16px;
		overflow: hidden;
		box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
	}
	
	.performance-header {
		padding: 2rem;
		text-align: center;
		color: white;
	}
	
	.performance-icon {
		font-size: 3rem;
		display: block;
		margin-bottom: 0.5rem;
	}
	
	.performance-header h2 {
		margin: 0;
		font-size: 2rem;
	}
	
	.results-content {
		padding: 3rem;
	}
	
	.score-display {
		text-align: center;
		margin-bottom: 2rem;
	}
	
	.score-circle {
		width: 150px;
		height: 150px;
		border-radius: 50%;
		display: inline-flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		color: white;
		box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
	}
	
	.score-value {
		font-size: 3rem;
		font-weight: bold;
	}
	
	.score-label {
		font-size: 0.9rem;
		opacity: 0.9;
	}
	
	.metrics-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: 1rem;
		margin-bottom: 2rem;
	}
	
	.metric-card {
		background: #f8f9fa;
		padding: 1.5rem;
		border-radius: 12px;
		text-align: center;
	}
	
	.metric-label {
		color: #666;
		font-size: 0.9rem;
		margin-bottom: 0.5rem;
	}
	
	.metric-value {
		color: #667eea;
		font-size: 1.5rem;
		font-weight: bold;
	}
	
	.response-breakdown {
		margin: 2rem 0;
		background: #f0f4ff;
		padding: 1.5rem;
		border-radius: 12px;
	}
	
	.response-breakdown h3 {
		color: #667eea;
		margin: 0 0 1rem 0;
	}
	
	.breakdown-grid {
		display: grid;
		gap: 0.75rem;
	}
	
	.breakdown-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	
	.breakdown-label {
		color: #555;
	}
	
	.breakdown-value {
		font-weight: bold;
	}
	
	.breakdown-value.correct {
		color: #10b981;
	}
	
	.breakdown-value.incorrect {
		color: #ef4444;
	}
	
	/* Answer Comparison Styles */
	.answer-comparison {
		margin-top: 1.5rem;
		padding-top: 1.5rem;
		border-top: 2px solid #ddd;
	}

	.answer-comparison h4 {
		color: #667eea;
		margin: 0 0 1rem 0;
		font-size: 1.1rem;
	}

	.comparison-row {
		margin: 1.5rem 0;
		background: white;
		padding: 1rem;
		border-radius: 8px;
		border-left: 4px solid #667eea;
	}

	.comparison-label {
		font-weight: bold;
		color: #667eea;
		margin-bottom: 0.75rem;
		font-size: 1.05rem;
	}

	.comparison-content {
		display: grid;
		gap: 0.75rem;
	}

	.answer-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.5rem 0;
	}

	.answer-tag {
		color: #666;
		font-size: 0.9rem;
		font-weight: 500;
	}

	.answer-text {
		font-size: 1rem;
		font-weight: bold;
		padding: 0.25rem 0.75rem;
		border-radius: 6px;
	}

	.answer-correct {
		background: #d1fae5;
		color: #065f46;
	}

	.answer-wrong {
		background: #fee2e2;
		color: #991b1b;
	}

	.answer-info {
		background: #dbeafe;
		color: #1e40af;
	}

	.location-hint {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		background: #fef3c7;
		padding: 1rem;
		border-radius: 8px;
		margin-top: 1rem;
		border-left: 4px solid #f59e0b;
	}

	.hint-icon {
		font-size: 1.5rem;
		flex-shrink: 0;
	}

	.hint-text {
		color: #78350f;
		font-size: 0.95rem;
		line-height: 1.5;
	}

	.hint-text strong {
		color: #92400e;
		font-weight: 700;
	}

	.feedback-section {
		margin: 2rem 0;
		background: #fffbeb;
		border-left: 4px solid #f59e0b;
		padding: 1.5rem;
		border-radius: 8px;
	}
	
	.feedback-message {
		color: #92400e;
		margin: 0;
		line-height: 1.6;
		font-size: 1.05rem;
	}
	
	.badges-earned {
		margin: 2rem 0;
		background: linear-gradient(135deg, #fef3c7, #fde68a);
		padding: 1.5rem;
		border-radius: 12px;
	}
	
	.badges-earned h3 {
		color: #92400e;
		margin: 0 0 1rem 0;
	}
	
	.badge-list {
		display: grid;
		gap: 1rem;
	}
	
	.badge-item {
		display: flex;
		gap: 1rem;
		align-items: center;
		background: white;
		padding: 1rem;
		border-radius: 8px;
	}
	
	.badge-icon-large {
		font-size: 2rem;
	}
	
	.badge-item strong {
		color: #667eea;
		display: block;
		margin-bottom: 0.25rem;
	}
	
	.badge-item p {
		margin: 0;
		color: #666;
		font-size: 0.9rem;
	}
	
	.difficulty-info {
		margin: 2rem 0;
		text-align: center;
		padding: 1.5rem;
		background: #f0f4ff;
		border-radius: 12px;
	}
	
	.difficulty-info p {
		margin: 0.5rem 0;
		color: #555;
	}
	
	.adaptation-reason {
		font-size: 0.95rem;
		color: #666;
		font-style: italic;
	}
	
	.progress-tracker {
		margin: 2rem 0;
	}
	
	.progress-tracker p {
		text-align: center;
		color: #666;
		margin-bottom: 0.5rem;
	}
	
	.progress-bar {
		height: 12px;
		background: #e5e7eb;
		border-radius: 6px;
		overflow: hidden;
	}
	
	.progress-fill {
		height: 100%;
		background: linear-gradient(135deg, #667eea, #764ba2);
		transition: width 0.5s ease;
	}
	
	.action-buttons {
		display: flex;
		gap: 1rem;
		margin-top: 2rem;
	}
	
	.primary-button {
		flex: 1;
		background: linear-gradient(135deg, #667eea, #764ba2);
		color: white;
		border: none;
		padding: 1.25rem;
		border-radius: 12px;
		font-size: 1.1rem;
		font-weight: bold;
		cursor: pointer;
		transition: transform 0.2s, box-shadow 0.2s;
	}
	
	.primary-button:hover {
		transform: translateY(-2px);
		box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
	}
	
	.secondary-button {
		flex: 1;
		background: white;
		color: #667eea;
		border: 2px solid #667eea;
		padding: 1.25rem;
		border-radius: 12px;
		font-size: 1.1rem;
		font-weight: bold;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.secondary-button:hover {
		background: #667eea;
		color: white;
	}
	
	@media (max-width: 768px) {
		.ufov-container {
			padding: 1rem;
		}
		
		.ufov-header h1 {
			font-size: 1.8rem;
		}
		
		.intro-card, .ready-card, .response-card, .results-content {
			padding: 1.5rem;
		}
		
		.stimulus-arena {
			width: 100%;
			max-width: 500px;
			height: 500px;
		}
		
		.peripheral-clock {
			width: 300px;
			height: 300px;
		}
		
		.action-buttons {
			flex-direction: column;
		}
		
		.metrics-grid {
			grid-template-columns: repeat(2, 1fr);
		}
	}
</style>

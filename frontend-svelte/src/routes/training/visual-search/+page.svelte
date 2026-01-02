<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { API_BASE_URL } from '$lib/api';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import { user } from '$lib/stores';
	import { onDestroy, onMount } from 'svelte';

	let gamePhase = 'loading'; // loading, intro, playing, results
	let trialData = null;
	let difficulty = 5;
	let searchType = 'feature';
	let items = [];
	let targetItem = null;
	let setSize = 0;
	let timeLimit = 30;
	let timeRemaining = 0;
	let startTime = null;
	let timerInterval = null;
	let taskId = null; // Track which specific task in session this is
	
	let userAnswer = null; // true = target present, false = target absent
	let results = null;
	let earnedBadges = [];
	let showInstructions = true;

	// Load trial on mount
	onMount(async () => {
		if (!$user) {
			goto('/login');
			return;
		}
		
		// Get taskId from URL params
		taskId = $page.url.searchParams.get('taskId');
		
		await loadTrial();
	});

	// Cleanup on destroy
	onDestroy(() => {
		if (timerInterval) {
			clearInterval(timerInterval);
		}
	});

	async function loadTrial() {
		try {
			const response = await fetch(
				`${API_BASE_URL}/api/training/tasks/visual-search/generate/${$user.id}`,
				{
					method: 'GET',
					headers: { 'Content-Type': 'application/json' },
					credentials: 'include'
				}
			);

			if (!response.ok) throw new Error('Failed to load trial');

			const data = await response.json();
			trialData = data.trial_data;
			difficulty = data.difficulty;
			
			items = trialData.items;
			targetItem = trialData.target;
			searchType = trialData.search_type;
			setSize = trialData.set_size;
			timeLimit = trialData.time_limit;
			timeRemaining = timeLimit;
			
			gamePhase = 'intro';
		} catch (error) {
			console.error('Error loading trial:', error);
			alert('Failed to load task. Please try again.');
		}
	}

	function startGame() {
		startTime = Date.now();
		gamePhase = 'playing';
		userAnswer = null;

		// Start timer
		timerInterval = setInterval(() => {
			const elapsed = (Date.now() - startTime) / 1000;
			timeRemaining = Math.max(0, timeLimit - elapsed);

			if (timeRemaining === 0) {
				// Time's up - auto-submit as "not found"
				handleResponse(false);
			}
		}, 100);
	}

	function handleResponse(answer) {
		if (userAnswer !== null) return; // Already answered
		
		userAnswer = answer;
		
		if (timerInterval) {
			clearInterval(timerInterval);
			timerInterval = null;
		}
		
		submitResults();
	}

	async function submitResults() {
		const reactionTime = (Date.now() - startTime) / 1000;

		try {
			const response = await fetch(
				`${API_BASE_URL}/api/training/tasks/visual-search/submit/${$user.id}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					credentials: 'include',
					body: JSON.stringify({
						trial_data: trialData,
						user_response: {
							target_found: userAnswer,
							reaction_time: reactionTime
						},
						task_id: taskId  // Include task_id to track which specific task in session
					})
				}
			);

			if (!response.ok) throw new Error('Failed to submit results');

			const data = await response.json();
			results = data;
			earnedBadges = data.new_badges || [];
			gamePhase = 'results';
		} catch (error) {
			console.error('Error submitting results:', error);
			alert('Failed to submit results. Please try again.');
		}
	}

	function getColorValue(colorName) {
		const colorMap = {
			red: '#DC2626',
			blue: '#2563EB',
			green: '#16A34A',
			yellow: '#EAB308',
			purple: '#9333EA',
			orange: '#EA580C'
		};
		return colorMap[colorName] || '#6B7280';
	}

	function getShapePath(shape) {
		// SVG paths for different shapes (centered at 50,50 in 100x100 viewBox, standardized size)
		const shapes = {
			circle: 'M 50 50 m -25 0 a 25 25 0 1 0 50 0 a 25 25 0 1 0 -50 0',
			square: 'M 25 25 L 75 25 L 75 75 L 25 75 Z',
			triangle: 'M 50 25 L 75 75 L 25 75 Z',
			diamond: 'M 50 25 L 75 50 L 50 75 L 25 50 Z'
		};
		return shapes[shape] || shapes.circle;
	}

	function getShapeDisplay(shape) {
		const shapeNames = {
			circle: 'Circle',
			square: 'Square',
			triangle: 'Triangle',
			diamond: 'Diamond'
		};
		return shapeNames[shape] || shape;
	}

	function getColorDisplay(color) {
		return color.charAt(0).toUpperCase() + color.slice(1);
	}

	function retryTask() {
		gamePhase = 'loading';
		results = null;
		earnedBadges = [];
		userAnswer = null;
		loadTrial();
	}

	function goToDashboard() {
		goto('/dashboard');
	}
</script>

<div class="container">
	<div class="header">
		<div class="task-badge">
			<span class="domain-label">Visual Scanning</span>
			<span class="difficulty-badge">Level {difficulty}</span>
		</div>
		<h1>Visual Search Task</h1>
		<p class="subtitle">
			{#if searchType === 'feature'}
				<span class="search-type feature">Feature Search</span> — Target differs by one attribute
			{:else}
				<span class="search-type conjunction">Conjunction Search</span> — Target requires multiple attributes
			{/if}
		</p>
	</div>

	{#if gamePhase === 'loading'}
		<div class="loading">
			<p>Loading task...</p>
		</div>
	{/if}

	{#if gamePhase === 'intro'}
		<div class="intro">
			<div class="info-card">
				<div class="intro-header">
					<h2>Task Instructions</h2>
					<div class="clinical-note">
						<span class="icon">🔬</span>
						<span>Based on Treisman & Gelade (1980)</span>
					</div>
				</div>
				
				<div class="target-section">
					<h3>Your Target:</h3>
					<div class="target-display">
						<svg width="100" height="100" viewBox="0 0 100 100" class="target-svg">
							<path
								d={getShapePath(targetItem.shape)}
								fill={getColorValue(targetItem.color)}
								stroke="#1F2937"
								stroke-width="3"
							/>
						</svg>
						<div class="target-info">
							<p class="target-name">{getColorDisplay(targetItem.color)} {getShapeDisplay(targetItem.shape)}</p>
							<p class="target-hint">Find this exact item on the screen</p>
						</div>
					</div>
				</div>

				<div class="instructions-section">
					<h3>How to Complete:</h3>
					<ol class="instruction-steps">
						<li>
							<span class="step-number">1</span>
							<div class="step-content">
								<strong>Search for the target</strong>
								<p>Look through all items displayed on screen</p>
							</div>
						</li>
						<li>
							<span class="step-number">2</span>
							<div class="step-content">
								<strong>Respond quickly and accurately</strong>
								<p>Click "Target Present" if you see it, or "Target Absent" if you don't</p>
							</div>
						</li>
						<li>
							<span class="step-number">3</span>
							<div class="step-content">
								<strong>Work against the clock</strong>
								<p>Complete within {timeLimit} seconds for best results</p>
							</div>
						</li>
					</ol>
				</div>

				<div class="task-details">
					<div class="detail-item">
						<span class="detail-label">Search Type</span>
						<span class="detail-value">{searchType === 'feature' ? 'Feature' : 'Conjunction'}</span>
					</div>
					<div class="detail-item">
						<span class="detail-label">Items</span>
						<span class="detail-value">{setSize}</span>
					</div>
					<div class="detail-item">
						<span class="detail-label">Time Limit</span>
						<span class="detail-value">{timeLimit}s</span>
					</div>
					<div class="detail-item">
						<span class="detail-label">Difficulty</span>
						<span class="detail-value">{difficulty}/10</span>
					</div>
				</div>

				{#if searchType === 'feature'}
					<div class="clinical-hint feature">
						<div class="hint-icon">💡</div>
						<div class="hint-content">
							<strong>Feature Search:</strong>
							<p>The target differs by a single attribute (color OR shape). It should "pop out" from the background using parallel visual processing.</p>
						</div>
					</div>
				{:else}
					<div class="clinical-hint conjunction">
						<div class="hint-icon">🎯</div>
						<div class="hint-content">
							<strong>Conjunction Search:</strong>
							<p>The target requires BOTH color AND shape to match. This demands serial visual search and sustained attention.</p>
						</div>
					</div>
				{/if}

				<button class="btn-start" on:click={startGame}>
					<span class="btn-icon">▶</span>
					Begin Task
				</button>
			</div>
		</div>
	{/if}

	{#if gamePhase === 'playing'}
		<div class="playing">
			<div class="game-controls">
				<div class="control-panel">
					<div class="timer-display">
						<div class="timer-icon">⏱️</div>
						<div class="timer-content">
							<span class="timer-label">Time Remaining</span>
							<span class="timer-value" class:warning={timeRemaining < 10} class:critical={timeRemaining < 5}>
								{Math.ceil(timeRemaining)}s
							</span>
						</div>
					</div>

					<div class="target-reference">
						<span class="reference-label">Looking for:</span>
						<div class="reference-item">
							<svg width="45" height="45" viewBox="0 0 100 100">
								<path
									d={getShapePath(targetItem.shape)}
									fill={getColorValue(targetItem.color)}
									stroke="#1F2937"
									stroke-width="3"
								/>
							</svg>
							<span class="reference-name">{getColorDisplay(targetItem.color)} {getShapeDisplay(targetItem.shape)}</span>
						</div>
					</div>
				</div>
			</div>

			<div class="search-arena">
				<div class="search-display">
					{#each items as item, i}
						<div
							class="search-item"
							style="left: {item.position.x * 90 + 5}%; top: {item.position.y * 90 + 5}%;"
						>
							<svg width="45" height="45" viewBox="0 0 100 100">
								<path
									d={getShapePath(item.shape)}
									fill={getColorValue(item.color)}
									stroke="#374151"
									stroke-width="2.5"
								/>
							</svg>
						</div>
					{/each}
				</div>
			</div>

			<div class="response-section">
				<p class="response-prompt">Is the target present on the screen?</p>
				<div class="response-buttons">
					<button class="btn-response btn-present" on:click={() => handleResponse(true)}>
						<span class="btn-icon">✓</span>
						<span class="btn-text">Target Present</span>
					</button>
					<button class="btn-response btn-absent" on:click={() => handleResponse(false)}>
						<span class="btn-icon">✗</span>
						<span class="btn-text">Target Absent</span>
					</button>
				</div>
			</div>
		</div>
	{/if}

	{#if gamePhase === 'results'}
		<div class="results">
			<h2>Results</h2>

			<div class="result-summary">
				<div class="result-item">
					<span class="label">Correct:</span>
					<span class="value" class:correct={results.correct} class:incorrect={!results.correct}>
						{results.correct ? '✓ YES' : '✗ NO'}
					</span>
				</div>

				<div class="result-item">
					<span class="label">Score:</span>
					<span class="value">{(results.score * 100).toFixed(0)}%</span>
				</div>

				<div class="result-item">
					<span class="label">Reaction Time:</span>
					<span class="value">{results.reaction_time.toFixed(2)}s</span>
				</div>

				<div class="result-item">
					<span class="label">Response Type:</span>
					<span class="value response-type">
						{results.response_type.replace('_', ' ').toUpperCase()}
					</span>
				</div>
			</div>

			<div class="performance-details">
				<h3>Performance Analysis</h3>
				
				<div class="detail-grid">
					<div class="detail-card">
						<h4>Search Efficiency</h4>
						<p class="metric">{results.search_efficiency.toFixed(3)}s per item</p>
						<p class="description">Time spent examining each item</p>
					</div>

					<div class="detail-card">
						<h4>Search Slope</h4>
						<p class="metric">{results.search_slope_ms.toFixed(1)} ms/item</p>
						<p class="description">
							{#if searchType === 'feature'}
								Feature search: &lt;10 ms = excellent (parallel)
							{:else}
								Conjunction search: &lt;30 ms = excellent (serial)
							{/if}
						</p>
					</div>

					<div class="detail-card">
						<h4>Performance Rating</h4>
						<p class="metric performance-{results.performance}">
							{results.performance.replace('_', ' ').toUpperCase()}
						</p>
						<p class="description">Overall performance classification</p>
					</div>
				</div>

				<div class="trial-info">
					<p><strong>Search Type:</strong> {results.search_type === 'feature' ? 'Feature Search' : 'Conjunction Search'}</p>
					<p><strong>Set Size:</strong> {results.set_size} items</p>
					<p><strong>Target Was:</strong> {results.target_present ? 'Present' : 'Absent'}</p>
					<p><strong>You Said:</strong> {results.user_answer ? 'Present' : 'Absent'}</p>
				</div>
			</div>

			<div class="difficulty-feedback">
				<p>
					<strong>Difficulty Adjustment:</strong>
					{#if results.new_difficulty > results.old_difficulty}
						⬆️ Increased from {results.old_difficulty} to {results.new_difficulty}
					{:else if results.new_difficulty < results.old_difficulty}
						⬇️ Decreased from {results.old_difficulty} to {results.new_difficulty}
					{:else}
						➡️ Maintained at {results.new_difficulty}
					{/if}
				</p>
				<p class="adaptation-reason">{results.adaptation_reason}</p>
			</div>

			{#if earnedBadges.length > 0}
				<div class="badges-section">
					<h3>🏆 New Badges Earned!</h3>
					<BadgeNotification badges={earnedBadges} />
				</div>
			{/if}

			<div class="action-buttons">
				<button class="btn-secondary" on:click={retryTask}>Try Again</button>
				<button class="btn-primary" on:click={goToDashboard}>Back to Dashboard</button>
			</div>
		</div>
	{/if}
</div>

<style>
	* {
		box-sizing: border-box;
	}

	.container {
		max-width: 1400px;
		margin: 0 auto;
		padding: 2rem;
		min-height: 100vh;
		background: linear-gradient(135deg, #f5f7fa 0%, #e3e9f0 100%);
	}

	/* Header Styles */
	.header {
		text-align: center;
		margin-bottom: 3rem;
	}

	.task-badge {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 1rem;
		margin-bottom: 1rem;
	}

	.domain-label {
		background: #3B82F6;
		color: white;
		padding: 0.4rem 1rem;
		border-radius: 20px;
		font-size: 0.85rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.difficulty-badge {
		background: #10B981;
		color: white;
		padding: 0.4rem 1rem;
		border-radius: 20px;
		font-size: 0.85rem;
		font-weight: 600;
	}

	.header h1 {
		font-size: 2.75rem;
		color: #1F2937;
		margin-bottom: 0.75rem;
		font-weight: 700;
		letter-spacing: -0.5px;
	}

	.subtitle {
		color: #6B7280;
		font-size: 1.15rem;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
	}

	.search-type {
		font-weight: 600;
		padding: 0.25rem 0.75rem;
		border-radius: 6px;
	}

	.search-type.feature {
		background: #DBEAFE;
		color: #1E40AF;
	}

	.search-type.conjunction {
		background: #FEF3C7;
		color: #92400E;
	}

	.loading {
		text-align: center;
		padding: 4rem;
		font-size: 1.2rem;
		color: #6B7280;
		background: white;
		border-radius: 12px;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
	}

	/* Intro Phase */
	.intro {
		display: flex;
		justify-content: center;
		align-items: center;
		min-height: 60vh;
	}

	.info-card {
		background: white;
		padding: 3rem;
		border-radius: 16px;
		box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
		max-width: 700px;
		width: 100%;
	}

	.intro-header {
		text-align: center;
		margin-bottom: 2rem;
		border-bottom: 2px solid #E5E7EB;
		padding-bottom: 1.5rem;
	}

	.intro-header h2 {
		color: #1F2937;
		font-size: 2rem;
		margin-bottom: 0.75rem;
		font-weight: 700;
	}

	.clinical-note {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		background: #F3F4F6;
		padding: 0.5rem 1rem;
		border-radius: 20px;
		font-size: 0.85rem;
		color: #4B5563;
	}

	.clinical-note .icon {
		font-size: 1rem;
	}

	.target-section {
		margin: 2rem 0;
	}

	.target-section h3 {
		color: #374151;
		font-size: 1.1rem;
		margin-bottom: 1rem;
		text-align: center;
		font-weight: 600;
	}

	.target-display {
		background: linear-gradient(135deg, #F9FAFB 0%, #F3F4F6 100%);
		padding: 2rem;
		border-radius: 12px;
		border: 2px solid #E5E7EB;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1rem;
	}

	.target-svg {
		filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1));
	}

	.target-info {
		text-align: center;
	}

	.target-name {
		font-size: 1.4rem;
		font-weight: 700;
		color: #1F2937;
		margin: 0;
	}

	.target-hint {
		font-size: 0.95rem;
		color: #6B7280;
		margin: 0.25rem 0 0 0;
	}

	.instructions-section {
		margin: 2rem 0;
		text-align: left;
	}

	.instructions-section h3 {
		color: #374151;
		font-size: 1.1rem;
		margin-bottom: 1rem;
		font-weight: 600;
	}

	.instruction-steps {
		list-style: none;
		padding: 0;
		margin: 0;
	}

	.instruction-steps li {
		display: flex;
		gap: 1rem;
		margin-bottom: 1.25rem;
		align-items: flex-start;
	}

	.step-number {
		background: #3B82F6;
		color: white;
		width: 32px;
		height: 32px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 700;
		flex-shrink: 0;
	}

	.step-content {
		flex: 1;
	}

	.step-content strong {
		color: #1F2937;
		display: block;
		margin-bottom: 0.25rem;
		font-size: 1.05rem;
	}

	.step-content p {
		color: #6B7280;
		margin: 0;
		font-size: 0.95rem;
		line-height: 1.5;
	}

	.task-details {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 1rem;
		margin: 2rem 0;
		padding: 1.5rem;
		background: #F9FAFB;
		border-radius: 12px;
		border: 1px solid #E5E7EB;
	}

	.detail-item {
		text-align: center;
	}

	.detail-label {
		display: block;
		font-size: 0.8rem;
		color: #6B7280;
		text-transform: uppercase;
		letter-spacing: 0.5px;
		margin-bottom: 0.5rem;
		font-weight: 600;
	}

	.detail-value {
		display: block;
		font-size: 1.3rem;
		color: #1F2937;
		font-weight: 700;
	}

	.clinical-hint {
		background: linear-gradient(135deg, #DBEAFE 0%, #BFDBFE 100%);
		border-left: 4px solid #3B82F6;
		padding: 1.25rem;
		border-radius: 8px;
		margin: 1.5rem 0;
		display: flex;
		gap: 1rem;
		align-items: flex-start;
	}

	.clinical-hint.conjunction {
		background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
		border-left-color: #F59E0B;
	}

	.hint-icon {
		font-size: 1.5rem;
		flex-shrink: 0;
	}

	.hint-content {
		flex: 1;
	}

	.hint-content strong {
		display: block;
		color: #1F2937;
		margin-bottom: 0.5rem;
		font-size: 1.05rem;
	}

	.hint-content p {
		color: #374151;
		margin: 0;
		line-height: 1.6;
		font-size: 0.95rem;
	}

	.btn-start {
		width: 100%;
		padding: 1.25rem 2rem;
		font-size: 1.2rem;
		font-weight: 700;
		background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
		color: white;
		border: none;
		border-radius: 12px;
		cursor: pointer;
		transition: all 0.3s;
		box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.75rem;
		margin-top: 2rem;
	}

	.btn-start:hover {
		transform: translateY(-2px);
		box-shadow: 0 8px 20px rgba(59, 130, 246, 0.4);
	}

	.btn-icon {
		font-size: 1.2rem;
	}

	/* Playing Phase */
	.playing {
		max-width: 1200px;
		margin: 0 auto;
	}

	.game-controls {
		margin-bottom: 2rem;
	}

	.control-panel {
		background: white;
		padding: 1.5rem;
		border-radius: 12px;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
		display: flex;
		justify-content: space-between;
		align-items: center;
		flex-wrap: wrap;
		gap: 1.5rem;
	}

	.timer-display {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.timer-icon {
		font-size: 2rem;
	}

	.timer-content {
		display: flex;
		flex-direction: column;
	}

	.timer-label {
		font-size: 0.85rem;
		color: #6B7280;
		text-transform: uppercase;
		letter-spacing: 0.5px;
		font-weight: 600;
	}

	.timer-value {
		font-size: 2.5rem;
		font-weight: 800;
		color: #10B981;
		line-height: 1;
	}

	.timer-value.warning {
		color: #F59E0B;
		animation: pulse 1s infinite;
	}

	.timer-value.critical {
		color: #EF4444;
		animation: pulse 0.5s infinite;
	}

	@keyframes pulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.7; transform: scale(1.05); }
	}

	.target-reference {
		display: flex;
		align-items: center;
		gap: 1rem;
		background: #F9FAFB;
		padding: 1rem 1.5rem;
		border-radius: 10px;
		border: 2px solid #E5E7EB;
	}

	.reference-label {
		font-size: 0.9rem;
		color: #6B7280;
		font-weight: 600;
	}

	.reference-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.reference-name {
		font-size: 1rem;
		color: #1F2937;
		font-weight: 600;
	}

	.search-arena {
		margin-bottom: 2rem;
	}

	.search-display {
		position: relative;
		width: 100%;
		height: 650px;
		background: white;
		border: 3px solid #E5E7EB;
		border-radius: 16px;
		box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.05);
		overflow: hidden;
	}

	.search-item {
		position: absolute;
		transform: translate(-50%, -50%);
		cursor: pointer;
		transition: transform 0.15s ease;
	}

	.search-item:hover svg {
		filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.2));
	}

	.response-section {
		text-align: center;
	}

	.response-prompt {
		font-size: 1.3rem;
		color: #1F2937;
		margin-bottom: 1.5rem;
		font-weight: 600;
	}

	.response-buttons {
		display: flex;
		justify-content: center;
		gap: 2rem;
		flex-wrap: wrap;
	}

	.btn-response {
		padding: 1.5rem 3rem;
		font-size: 1.2rem;
		font-weight: 700;
		border: none;
		border-radius: 12px;
		cursor: pointer;
		transition: all 0.3s;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
		display: flex;
		align-items: center;
		gap: 0.75rem;
		min-width: 220px;
		justify-content: center;
	}

	.btn-present {
		background: linear-gradient(135deg, #10B981 0%, #059669 100%);
		color: white;
	}

	.btn-present:hover {
		transform: translateY(-3px);
		box-shadow: 0 8px 20px rgba(16, 185, 129, 0.4);
	}

	.btn-absent {
		background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
		color: white;
	}

	.btn-absent:hover {
		transform: translateY(-3px);
		box-shadow: 0 8px 20px rgba(239, 68, 68, 0.4);
	}

	.btn-response .btn-icon {
		font-size: 1.5rem;
	}

	/* Results Phase */
	.results {
		background: white;
		padding: 3rem;
		border-radius: 16px;
		box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
		max-width: 1000px;
		margin: 0 auto;
	}

	.results h2 {
		text-align: center;
		color: #1F2937;
		font-size: 2.25rem;
		margin-bottom: 2.5rem;
		font-weight: 700;
	}

	.result-summary {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		gap: 1.5rem;
		margin-bottom: 3rem;
	}

	.result-item {
		background: linear-gradient(135deg, #F9FAFB 0%, #F3F4F6 100%);
		padding: 1.75rem;
		border-radius: 12px;
		text-align: center;
		border: 2px solid #E5E7EB;
		transition: transform 0.3s;
	}

	.result-item:hover {
		transform: translateY(-4px);
	}

	.result-item .label {
		display: block;
		font-size: 0.85rem;
		color: #6B7280;
		margin-bottom: 0.75rem;
		text-transform: uppercase;
		letter-spacing: 0.5px;
		font-weight: 600;
	}

	.result-item .value {
		display: block;
		font-size: 1.75rem;
		font-weight: 800;
		color: #1F2937;
	}

	.value.correct {
		color: #10B981;
	}

	.value.incorrect {
		color: #EF4444;
	}

	.response-type {
		font-size: 1.2rem !important;
		text-transform: capitalize;
	}

	.performance-details {
		margin: 3rem 0;
	}

	.performance-details h3 {
		color: #1F2937;
		margin-bottom: 2rem;
		text-align: center;
		font-size: 1.75rem;
		font-weight: 700;
	}

	.detail-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: 1.5rem;
		margin-bottom: 2rem;
	}

	.detail-card {
		background: #F9FAFB;
		padding: 2rem;
		border-radius: 12px;
		text-align: center;
		border: 2px solid #E5E7EB;
		transition: all 0.3s;
	}

	.detail-card:hover {
		border-color: #3B82F6;
		box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
	}

	.detail-card h4 {
		color: #6B7280;
		margin-bottom: 1rem;
		font-size: 0.95rem;
		text-transform: uppercase;
		letter-spacing: 0.5px;
		font-weight: 600;
	}

	.detail-card .metric {
		font-size: 2.25rem;
		font-weight: 800;
		color: #1F2937;
		margin: 0.75rem 0;
	}

	.metric.performance-excellent {
		color: #10B981;
	}

	.metric.performance-good {
		color: #3B82F6;
	}

	.metric.performance-average {
		color: #F59E0B;
	}

	.metric.performance-needs_improvement {
		color: #EF4444;
	}

	.detail-card .description {
		font-size: 0.9rem;
		color: #6B7280;
		margin-top: 0.75rem;
		line-height: 1.5;
	}

	.trial-info {
		background: #F3F4F6;
		padding: 1.75rem;
		border-radius: 12px;
		margin: 2rem 0;
		border: 2px solid #E5E7EB;
	}

	.trial-info p {
		margin: 0.75rem 0;
		color: #374151;
		font-size: 1rem;
	}

	.difficulty-feedback {
		background: linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%);
		border-left: 4px solid #10B981;
		padding: 1.75rem;
		border-radius: 12px;
		margin: 2rem 0;
	}

	.difficulty-feedback p {
		margin: 0.5rem 0;
		color: #1F2937;
		font-size: 1rem;
	}

	.adaptation-reason {
		color: #6B7280;
		font-style: italic;
	}

	.badges-section {
		margin: 2.5rem 0;
		text-align: center;
	}

	.badges-section h3 {
		color: #F59E0B;
		margin-bottom: 1.5rem;
		font-size: 1.5rem;
		font-weight: 700;
	}

	.action-buttons {
		display: flex;
		justify-content: center;
		gap: 1.5rem;
		margin-top: 2.5rem;
		flex-wrap: wrap;
	}

	.btn-primary,
	.btn-secondary {
		padding: 1.25rem 3rem;
		font-size: 1.1rem;
		font-weight: 700;
		border: none;
		border-radius: 12px;
		cursor: pointer;
		transition: all 0.3s;
		min-width: 200px;
	}

	.btn-primary {
		background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);
		color: white;
		box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
	}

	.btn-primary:hover {
		transform: translateY(-2px);
		box-shadow: 0 8px 20px rgba(59, 130, 246, 0.4);
	}

	.btn-secondary {
		background: #F3F4F6;
		color: #374151;
		border: 2px solid #E5E7EB;
	}

	.btn-secondary:hover {
		background: #E5E7EB;
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
	}

	@media (max-width: 768px) {
		.container {
			padding: 1rem;
		}

		.header h1 {
			font-size: 2rem;
		}

		.task-details {
			grid-template-columns: repeat(2, 1fr);
		}

		.control-panel {
			flex-direction: column;
		}

		.search-display {
			height: 450px;
		}

		.response-buttons {
			flex-direction: column;
			gap: 1rem;
		}

		.btn-response {
			width: 100%;
		}

		.detail-grid {
			grid-template-columns: 1fr;
		}

		.action-buttons {
			flex-direction: column;
		}

		.btn-primary,
		.btn-secondary {
			width: 100%;
		}
	}
</style>

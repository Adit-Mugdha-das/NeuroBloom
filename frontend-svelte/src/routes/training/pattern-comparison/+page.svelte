<script>
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	// Task states
	const STATE = {
		LOADING: 'loading',
		INSTRUCTIONS: 'instructions',
		READY: 'ready',
		TESTING: 'testing',
		COMPLETE: 'complete'
	};

	let state = STATE.LOADING;
	let difficulty = 5;
	let sessionData = null;
	
	// Test state
	let currentTrialIndex = 0;
	let responses = [];
	let trialStartTime = 0;
	let sessionResults = null;
	let countdown = 3;
	
	let showHelp = false;

	$: currentTrial = sessionData?.trials?.[currentTrialIndex];
	$: progress = sessionData ? ((currentTrialIndex + 1) / sessionData.total_trials * 100) : 0;
	$: trialsRemaining = sessionData ? sessionData.total_trials - currentTrialIndex : 0;

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

			const planRes = await fetch(`http://localhost:8000/training/plan/${userId}`);
			const plan = await planRes.json();

			let userDifficulty = 5;
			if (plan && plan.current_difficulty) {
				const currentDiff =
					typeof plan.current_difficulty === 'string'
						? JSON.parse(plan.current_difficulty)
						: plan.current_difficulty;
				userDifficulty = currentDiff.processing_speed || 5;
			}

			difficulty = userDifficulty;

			const response = await fetch(
				`http://localhost:8000/api/training/tasks/pattern-comparison/generate/${userId}?difficulty=${difficulty}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' }
				}
			);

			if (!response.ok) throw new Error('Failed to load session');

			const data = await response.json();
			sessionData = data.session;
			
			state = STATE.INSTRUCTIONS;
		} catch (error) {
			console.error('Error loading session:', error);
			alert('Failed to load task session');
			goto('/dashboard');
		}
	}

	function startTest() {
		state = STATE.READY;
		countdown = 3;
		
		const countdownInterval = setInterval(() => {
			countdown--;
			if (countdown <= 0) {
				clearInterval(countdownInterval);
				beginTest();
			}
		}, 1000);
	}

	function beginTest() {
		state = STATE.TESTING;
		currentTrialIndex = 0;
		responses = [];
		startTrial();
	}

	function startTrial() {
		trialStartTime = Date.now();
	}

	function submitAnswer(answer) {
		const reactionTime = (Date.now() - trialStartTime) / 1000;
		
		responses.push({
			trial_index: currentTrialIndex,
			user_answer: answer,
			reaction_time: reactionTime
		});
		
		// Move to next trial or complete
		if (currentTrialIndex < sessionData.total_trials - 1) {
			currentTrialIndex++;
			startTrial();
		} else {
			completeSession();
		}
	}

	async function completeSession() {
		state = STATE.LOADING;
		
		try {
			const userData = JSON.parse(localStorage.getItem('user') || '{}');
			const userId = userData.id;

			const response = await fetch(
				`http://localhost:8000/api/training/tasks/pattern-comparison/submit/${userId}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						difficulty: difficulty,
						session_data: sessionData,
						responses: responses
					})
				}
			);

			if (!response.ok) throw new Error('Failed to submit results');

			sessionResults = await response.json();
			state = STATE.COMPLETE;
		} catch (error) {
			console.error('Error submitting results:', error);
			alert('Failed to submit results');
		}
	}

	function toggleHelp() {
		showHelp = !showHelp;
	}

	function getPerformanceColor(level) {
		switch(level) {
			case 'Excellent': return '#4CAF50';
			case 'Good': return '#8BC34A';
			case 'Average': return '#FFC107';
			default: return '#FF9800';
		}
	}

	function renderPattern(pattern) {
		return pattern.map(row => row.join(' ')).join('\n');
	}
</script>

<div class="pattern-container">
	{#if state === STATE.LOADING}
		<div class="loading">
			<div class="spinner"></div>
			<p>Loading Pattern Comparison...</p>
		</div>
	{:else if state === STATE.INSTRUCTIONS}
		<div class="instructions">
			<h1>🔍 Pattern Comparison (Visual Matching)</h1>
			<div class="woodcock-badge">Woodcock-Johnson Tests</div>
			
			<div class="instruction-card">
				<h2>About This Test</h2>
				<p class="importance">
					Pattern Comparison is from the <strong>Woodcock-Johnson Tests of Cognitive Abilities</strong>, 
					a comprehensive battery used in neuropsychological assessment. It measures <strong>pure processing 
					speed</strong> with minimal motor requirements - making it ideal for MS patients.
				</p>
				
				<div class="clinical-info">
					<h3>📊 Clinical Significance</h3>
					<ul>
						<li>Measures <strong>pure processing speed</strong> (no complex motor skills needed)</li>
						<li><strong>Minimal physical demands</strong> - perfect for MS assessment</li>
						<li>Sensitive to <strong>cognitive processing efficiency</strong></li>
						<li>Validated across <strong>adult populations</strong> (Salthouse, 1996)</li>
					</ul>
				</div>

				<div class="how-it-works">
					<h3>🎯 How It Works</h3>
					<div class="demo-area">
						<div class="demo-patterns">
							<div class="demo-pattern">
								<div class="pattern-label">Pattern A</div>
								<div class="demo-grid">
									<div class="demo-row">
										<span>■</span><span>●</span><span>▲</span>
									</div>
									<div class="demo-row">
										<span>●</span><span>▲</span><span>■</span>
									</div>
									<div class="demo-row">
										<span>▲</span><span>■</span><span>●</span>
									</div>
								</div>
							</div>
							
							<div class="demo-vs">VS</div>
							
							<div class="demo-pattern">
								<div class="pattern-label">Pattern B</div>
								<div class="demo-grid">
									<div class="demo-row">
										<span>■</span><span>●</span><span>▲</span>
									</div>
									<div class="demo-row">
										<span>●</span><span>▲</span><span>■</span>
									</div>
									<div class="demo-row">
										<span>▲</span><span>■</span><span>●</span>
									</div>
								</div>
							</div>
						</div>
						
						<div class="demo-question">
							<p>Are these patterns <strong>SAME</strong> or <strong>DIFFERENT</strong>?</p>
							<div class="demo-buttons">
								<button class="demo-btn same">SAME ✓</button>
								<button class="demo-btn different">DIFFERENT ✗</button>
							</div>
						</div>
					</div>
				</div>

				<div class="test-details">
					<h3>⚡ Test Format</h3>
					<div class="details-grid">
						<div class="detail-item">
							<div class="detail-icon">🔢</div>
							<div class="detail-text">
								<strong>{sessionData?.total_trials || 25} Trials</strong>
								<span>Quick comparisons</span>
							</div>
						</div>
						<div class="detail-item">
							<div class="detail-icon">⏱️</div>
							<div class="detail-text">
								<strong>Time Limited</strong>
								<span>{sessionData?.config?.time_per_trial || 2}s per trial</span>
							</div>
						</div>
						<div class="detail-item">
							<div class="detail-icon">👁️</div>
							<div class="detail-text">
								<strong>Visual Processing</strong>
								<span>Pattern recognition</span>
							</div>
						</div>
						<div class="detail-item">
							<div class="detail-icon">✓</div>
							<div class="detail-text">
								<strong>Speed + Accuracy</strong>
								<span>Both matter!</span>
							</div>
						</div>
					</div>
				</div>
				
				<div class="tips">
					<h3>💡 Pro Tips</h3>
					<ul>
						<li><strong>First glance:</strong> Often your initial impression is correct</li>
						<li><strong>Systematic scan:</strong> Check patterns row by row or column by column</li>
						<li><strong>Trust yourself:</strong> Don't second-guess quick decisions</li>
						<li><strong>Stay focused:</strong> Maintain concentration across all trials</li>
						<li><strong>Speed matters:</strong> But accuracy prevents penalties</li>
					</ul>
				</div>

				<div class="performance-guide">
					<h3>📈 Performance Targets</h3>
					<div class="norm-scale">
						<div class="norm-item excellent">35+ correct/min = Excellent</div>
						<div class="norm-item good">25-34 correct/min = Good</div>
						<div class="norm-item average">15-24 correct/min = Average</div>
						<div class="norm-item needs-practice">&lt;15 correct/min = Practice Needed</div>
					</div>
					<p class="norm-note">*Based on Salthouse (1996) processing speed research</p>
				</div>
			</div>
			
			<button class="start-button" on:click={startTest}>
				Start Pattern Comparison
			</button>
		</div>
	{:else if state === STATE.READY}
		<div class="ready-screen">
			<h2>Get Ready!</h2>
			<p class="ready-message">Compare patterns and decide: SAME or DIFFERENT</p>
			<div class="ready-example">
				<div class="ready-pattern">
					<div class="pattern-box">Pattern A</div>
					<div class="vs-text">vs</div>
					<div class="pattern-box">Pattern B</div>
				</div>
				<div class="ready-arrow">↓</div>
				<div class="ready-buttons">
					<div class="button-preview same">SAME</div>
					<div class="button-preview different">DIFFERENT</div>
				</div>
			</div>
			<div class="countdown">{countdown}</div>
		</div>
	{:else if state === STATE.TESTING}
		<div class="testing-screen">
			<div class="header">
				<div class="progress-bar-container">
					<div class="progress-bar-fill" style="width: {progress}%"></div>
					<div class="progress-text">
						Trial {currentTrialIndex + 1} of {sessionData.total_trials}
					</div>
				</div>
				<button class="help-button-floating" on:click={toggleHelp}>?</button>
			</div>

			{#if currentTrial}
				<div class="trial-container">
					<div class="trials-info">
						<div class="trials-remaining">
							<span class="remaining-label">Trials Remaining:</span>
							<span class="remaining-value">{trialsRemaining}</span>
						</div>
						<div class="pattern-info">
							<span class="info-badge pattern-type">
								{#if currentTrial.pattern_type === 'simple_geometric'}
									📐 Simple Shapes
								{:else if currentTrial.pattern_type === 'complex'}
									🔷 Complex Patterns
								{:else}
									✨ Abstract Design
								{/if}
							</span>
							<span class="info-badge pattern-size">
								{currentTrial.pattern_size}×{currentTrial.pattern_size} Grid
							</span>
						</div>
					</div>

					<div class="patterns-display">
						<div class="pattern-panel">
							<div class="pattern-label">Pattern A</div>
							<div class="pattern-grid size-{currentTrial.pattern_size}">
								{#each currentTrial.pattern_a as row, i}
									<div class="pattern-row">
										{#each row as cell}
											<div class="pattern-cell">{cell}</div>
										{/each}
									</div>
								{/each}
							</div>
						</div>

						<div class="vs-divider">
							<span>VS</span>
						</div>

						<div class="pattern-panel">
							<div class="pattern-label">Pattern B</div>
							<div class="pattern-grid size-{currentTrial.pattern_size}">
								{#each currentTrial.pattern_b as row, i}
									<div class="pattern-row">
										{#each row as cell}
											<div class="pattern-cell">{cell}</div>
										{/each}
									</div>
								{/each}
							</div>
						</div>
					</div>

					<div class="decision-area">
						<h3>Are these patterns the same or different?</h3>
						<div class="decision-buttons">
							<button class="decision-btn same" on:click={() => submitAnswer('SAME')}>
								<span class="btn-icon">✓</span>
								<span class="btn-text">SAME</span>
							</button>
							<button class="decision-btn different" on:click={() => submitAnswer('DIFFERENT')}>
								<span class="btn-icon">✗</span>
								<span class="btn-text">DIFFERENT</span>
							</button>
						</div>
						<div class="time-hint">
							Time limit: {currentTrial.time_limit}s per trial
						</div>
					</div>
				</div>
			{/if}
		</div>
	{:else if state === STATE.COMPLETE}
		<div class="complete-screen">
			<h1>Pattern Comparison Complete! 🎉</h1>
			
			{#if sessionResults}
				{@const perfColor = getPerformanceColor(sessionResults.metrics.performance_level)}
				
				<div class="performance-badge" style="border-color: {perfColor}; color: {perfColor}">
					<div class="perf-level">{sessionResults.metrics.performance_level}</div>
					<div class="perf-speed">{sessionResults.metrics.processing_speed} correct/min</div>
				</div>

				<div class="results-grid">
					<div class="result-card primary">
						<div class="result-icon">⚡</div>
						<div class="result-value">{sessionResults.metrics.processing_speed}</div>
						<div class="result-label">Processing Speed</div>
						<div class="result-sublabel">Correct responses per minute</div>
					</div>
					
					<div class="result-card">
						<div class="result-icon">🎯</div>
						<div class="result-value">{sessionResults.metrics.score}</div>
						<div class="result-label">Score</div>
						<div class="result-sublabel">Out of 100</div>
					</div>
					
					<div class="result-card">
						<div class="result-icon">✓</div>
						<div class="result-value">{sessionResults.metrics.accuracy}%</div>
						<div class="result-label">Accuracy</div>
						<div class="result-sublabel">
							{sessionResults.metrics.correct_count}/{sessionResults.metrics.total_trials} correct
						</div>
					</div>
					
					<div class="result-card">
						<div class="result-icon">⏱️</div>
						<div class="result-value">{sessionResults.metrics.average_reaction_time}s</div>
						<div class="result-label">Avg Reaction Time</div>
						<div class="result-sublabel">Per trial</div>
					</div>
				</div>

				<div class="performance-breakdown">
					<h3>📊 Detailed Analysis</h3>
					<div class="breakdown-grid">
						<div class="breakdown-item">
							<span>Total Trials:</span>
							<span class="value">{sessionResults.metrics.total_trials}</span>
						</div>
						<div class="breakdown-item">
							<span>Correct Answers:</span>
							<span class="value success">{sessionResults.metrics.correct_count}</span>
						</div>
						<div class="breakdown-item">
							<span>Timeouts:</span>
							<span class="value {sessionResults.metrics.timeout_count > 0 ? 'error' : 'success'}">
								{sessionResults.metrics.timeout_count}
							</span>
						</div>
						<div class="breakdown-item">
							<span>Consistency:</span>
							<span class="value">{sessionResults.metrics.consistency}%</span>
						</div>
						<div class="breakdown-item">
							<span>Total Time:</span>
							<span class="value">{sessionResults.metrics.total_time}s</span>
						</div>
						<div class="breakdown-item">
							<span>Performance Level:</span>
							<span class="value" style="color: {perfColor}">
								{sessionResults.metrics.performance_level}
							</span>
						</div>
					</div>
				</div>

				<div class="clinical-context">
					<h3>🏥 Clinical Context</h3>
					<p>
						{#if sessionResults.metrics.performance_level === 'Excellent'}
							Outstanding processing speed! Your performance of <strong>{sessionResults.metrics.processing_speed} 
							correct responses per minute</strong> is well above average. This indicates excellent cognitive 
							efficiency and visual processing ability.
						{:else if sessionResults.metrics.performance_level === 'Good'}
							Great performance! Your processing speed of <strong>{sessionResults.metrics.processing_speed} 
							correct/min</strong> is above average, showing strong pattern recognition and quick decision-making.
						{:else if sessionResults.metrics.performance_level === 'Average'}
							Good work! Your speed of <strong>{sessionResults.metrics.processing_speed} correct/min</strong> 
							is in the normal range. Regular practice can help improve your pattern recognition speed.
						{:else}
							Keep practicing! Processing speed improves significantly with regular training. Pattern 
							comparison tasks are excellent for building quick visual processing and decision-making skills.
						{/if}
					</p>
					<p class="why-matters">
						<strong>Why this matters for MS:</strong> Pattern comparison has minimal motor requirements 
						(just clicking), making it an excellent measure of pure cognitive processing speed without 
						physical limitations affecting your score.
					</p>
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
			{/if}
		</div>
	{/if}
</div>

{#if showHelp}
	<div class="help-modal" on:click={toggleHelp} role="presentation">
		<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
		<div class="help-content" on:click|stopPropagation role="dialog" tabindex="-1" on:keydown={(e) => e.key === 'Escape' && toggleHelp()}>
			<button class="close-button" on:click={toggleHelp}>×</button>
			<h2>Pattern Comparison Strategies</h2>
			
			<div class="strategy">
				<h3>👁️ Quick Visual Scan</h3>
				<p>Your first impression is often correct. Train yourself to quickly scan both patterns simultaneously rather than examining each in detail.</p>
			</div>
			
			<div class="strategy">
				<h3>🔄 Systematic Approach</h3>
				<p>If unsure, use a systematic method: scan row by row (top to bottom) or column by column (left to right). This ensures you don't miss differences.</p>
			</div>
			
			<div class="strategy">
				<h3>⚡ Speed vs Accuracy Balance</h3>
				<p>The metric "correct per minute" rewards both speed AND accuracy. Going fast but making mistakes won't help your score as much as being quick AND accurate.</p>
			</div>
			
			<div class="strategy">
				<h3>🎯 Peripheral Vision</h3>
				<p>With practice, you can detect differences using peripheral vision. Look at the center and let your peripheral vision catch discrepancies.</p>
			</div>
			
			<div class="strategy">
				<h3>🧠 Pattern Recognition</h3>
				<p>Your brain gets better at this with practice. Don't overthink - trust your pattern recognition abilities to improve over time.</p>
			</div>

			<div class="strategy">
				<h3>💪 Why This Matters</h3>
				<p>This task measures pure cognitive processing speed without requiring complex motor skills - perfect for MS assessment. It shows how efficiently your brain processes visual information.</p>
			</div>
		</div>
	</div>
{/if}

<style>
	.pattern-container {
		max-width: 1200px;
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
		margin-bottom: 1rem;
		font-size: 2.5rem;
		text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
	}

	.woodcock-badge {
		background: linear-gradient(135deg, #FF6B6B, #C92A2A);
		color: white;
		padding: 0.75rem 2rem;
		border-radius: 25px;
		font-weight: bold;
		font-size: 1rem;
		display: inline-block;
		margin-bottom: 2rem;
		box-shadow: 0 4px 15px rgba(201, 42, 42, 0.4);
	}

	.instruction-card {
		background: white;
		border-radius: 16px;
		padding: 2.5rem;
		margin: 2rem 0;
		box-shadow: 0 8px 32px rgba(0,0,0,0.2);
		text-align: left;
	}

	.importance {
		background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
		padding: 1.5rem;
		border-radius: 12px;
		border-left: 4px solid #667eea;
		margin: 1.5rem 0;
		font-size: 1.05rem;
		line-height: 1.6;
	}

	.clinical-info {
		background: #e3f2fd;
		padding: 1.5rem;
		border-radius: 12px;
		margin: 1.5rem 0;
	}

	.clinical-info h3 {
		color: #1976d2;
		margin: 0 0 1rem 0;
	}

	.clinical-info ul {
		margin: 0;
		padding-left: 1.5rem;
	}

	.clinical-info li {
		margin-bottom: 0.5rem;
		line-height: 1.6;
	}

	.how-it-works {
		margin: 2rem 0;
	}

	.demo-area {
		background: #f8f9fa;
		padding: 2rem;
		border-radius: 12px;
		margin-top: 1rem;
	}

	.demo-patterns {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 2rem;
		margin-bottom: 2rem;
		flex-wrap: wrap;
	}

	.demo-pattern {
		text-align: center;
	}

	.pattern-label {
		font-weight: bold;
		color: #667eea;
		margin-bottom: 0.5rem;
		font-size: 1.1rem;
	}

	.demo-grid {
		background: white;
		padding: 1rem;
		border-radius: 8px;
		box-shadow: 0 2px 8px rgba(0,0,0,0.1);
	}

	.demo-row {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 0.5rem;
	}

	.demo-row:last-child {
		margin-bottom: 0;
	}

	.demo-row span {
		width: 40px;
		height: 40px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.5rem;
		background: #f8f9fa;
		border-radius: 4px;
	}

	.demo-vs {
		font-size: 2rem;
		font-weight: bold;
		color: #667eea;
	}

	.demo-question {
		text-align: center;
	}

	.demo-question p {
		margin-bottom: 1rem;
		font-size: 1.1rem;
		color: #555;
	}

	.demo-buttons {
		display: flex;
		gap: 1rem;
		justify-content: center;
	}

	.demo-btn {
		padding: 0.75rem 2rem;
		border: none;
		border-radius: 8px;
		font-size: 1rem;
		font-weight: bold;
		cursor: not-allowed;
		opacity: 0.7;
	}

	.demo-btn.same {
		background: linear-gradient(135deg, #4CAF50, #45a049);
		color: white;
	}

	.demo-btn.different {
		background: linear-gradient(135deg, #f44336, #d32f2f);
		color: white;
	}

	.test-details {
		margin: 2rem 0;
	}

	.details-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
		margin-top: 1rem;
	}

	.detail-item {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		padding: 1.5rem;
		border-radius: 12px;
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.detail-icon {
		font-size: 2rem;
	}

	.detail-text {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.detail-text strong {
		font-size: 1.1rem;
	}

	.detail-text span {
		font-size: 0.9rem;
		opacity: 0.9;
	}

	.tips {
		background: #fff3cd;
		padding: 1.5rem;
		border-radius: 12px;
		margin: 2rem 0;
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

	.performance-guide {
		margin: 2rem 0;
	}

	.norm-scale {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		margin-top: 1rem;
	}

	.norm-item {
		padding: 0.75rem 1rem;
		border-radius: 8px;
		font-weight: 600;
		text-align: center;
	}

	.norm-item.excellent {
		background: linear-gradient(135deg, #4CAF50, #45a049);
		color: white;
	}

	.norm-item.good {
		background: linear-gradient(135deg, #8BC34A, #7CB342);
		color: white;
	}

	.norm-item.average {
		background: linear-gradient(135deg, #FFC107, #FFB300);
		color: #000;
	}

	.norm-item.needs-practice {
		background: linear-gradient(135deg, #FF9800, #FB8C00);
		color: white;
	}

	.norm-note {
		margin-top: 0.5rem;
		font-size: 0.85rem;
		color: #666;
		font-style: italic;
		text-align: center;
	}

	.start-button {
		background: linear-gradient(135deg, #4CAF50, #45a049);
		color: white;
		border: none;
		padding: 1.25rem 3.5rem;
		font-size: 1.4rem;
		font-weight: bold;
		border-radius: 12px;
		cursor: pointer;
		margin-top: 2rem;
		transition: all 0.3s;
		box-shadow: 0 4px 15px rgba(76, 175, 80, 0.4);
	}

	.start-button:hover {
		transform: translateY(-3px);
		box-shadow: 0 6px 25px rgba(76, 175, 80, 0.6);
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

	.ready-message {
		color: #666;
		font-size: 1.2rem;
		margin-bottom: 2rem;
	}

	.ready-example {
		margin: 2rem 0;
	}

	.ready-pattern {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 2rem;
		margin-bottom: 2rem;
	}

	.pattern-box {
		width: 150px;
		height: 100px;
		border: 3px solid #667eea;
		border-radius: 8px;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: bold;
		color: #667eea;
		background: #f8f9fa;
	}

	.vs-text {
		font-size: 2rem;
		font-weight: bold;
		color: #667eea;
	}

	.ready-arrow {
		font-size: 3rem;
		color: #667eea;
		margin: 1rem 0;
	}

	.ready-buttons {
		display: flex;
		gap: 1rem;
		justify-content: center;
	}

	.button-preview {
		padding: 1rem 2rem;
		border-radius: 8px;
		font-weight: bold;
		color: white;
	}

	.button-preview.same {
		background: linear-gradient(135deg, #4CAF50, #45a049);
	}

	.button-preview.different {
		background: linear-gradient(135deg, #f44336, #d32f2f);
	}

	.countdown {
		font-size: 5rem;
		font-weight: bold;
		color: #667eea;
		margin-top: 2rem;
		animation: pulse 1s ease-in-out infinite;
	}

	@keyframes pulse {
		0%, 100% { transform: scale(1); opacity: 1; }
		50% { transform: scale(1.1); opacity: 0.7; }
	}

	.testing-screen {
		background: white;
		border-radius: 16px;
		padding: 2rem;
		box-shadow: 0 8px 32px rgba(0,0,0,0.2);
		position: relative;
	}

	.header {
		margin-bottom: 2rem;
		position: relative;
	}

	.progress-bar-container {
		background: #e0e0e0;
		border-radius: 20px;
		height: 40px;
		position: relative;
		overflow: hidden;
		box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
	}

	.progress-bar-fill {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		height: 100%;
		transition: width 0.3s ease;
		border-radius: 20px;
	}

	.progress-text {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-weight: bold;
		color: #2c3e50;
		font-size: 1rem;
		text-shadow: 0 1px 2px rgba(255,255,255,0.8);
	}

	.help-button-floating {
		position: absolute;
		top: 0;
		right: 0;
		width: 45px;
		height: 45px;
		border-radius: 50%;
		border: 2px solid #667eea;
		background: white;
		color: #667eea;
		font-size: 1.5rem;
		font-weight: bold;
		cursor: pointer;
		transition: all 0.3s;
		box-shadow: 0 2px 8px rgba(0,0,0,0.1);
	}

	.help-button-floating:hover {
		background: #667eea;
		color: white;
		transform: scale(1.1);
	}

	.trial-container {
		display: flex;
		flex-direction: column;
		gap: 2rem;
	}

	.trials-info {
		text-align: center;
		margin-bottom: 1rem;
		display: flex;
		flex-direction: column;
		gap: 1rem;
		align-items: center;
	}

	.trials-remaining {
		display: inline-flex;
		align-items: center;
		gap: 0.75rem;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		padding: 0.75rem 2rem;
		border-radius: 25px;
		font-size: 1.1rem;
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
	}

	.remaining-label {
		font-weight: 600;
		opacity: 0.95;
	}

	.remaining-value {
		font-weight: bold;
		font-size: 1.5rem;
		background: rgba(255, 255, 255, 0.2);
		padding: 0.25rem 0.75rem;
		border-radius: 12px;
	}

	.pattern-info {
		display: flex;
		gap: 0.75rem;
		flex-wrap: wrap;
		justify-content: center;
	}

	.info-badge {
		padding: 0.5rem 1.25rem;
		border-radius: 20px;
		font-size: 0.95rem;
		font-weight: 600;
		box-shadow: 0 2px 8px rgba(0,0,0,0.1);
	}

	.info-badge.pattern-type {
		background: linear-gradient(135deg, #4CAF50, #45a049);
		color: white;
	}

	.info-badge.pattern-size {
		background: linear-gradient(135deg, #FF9800, #F57C00);
		color: white;
	}

	.patterns-display {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 2rem;
		flex-wrap: wrap;
		padding: 2rem;
		background: #f8f9fa;
		border-radius: 12px;
	}

	.pattern-panel {
		text-align: center;
	}

	.pattern-grid {
		background: white;
		padding: 1.5rem;
		border-radius: 12px;
		box-shadow: 0 4px 12px rgba(0,0,0,0.1);
		display: inline-block;
	}

	.pattern-row {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 0.5rem;
	}

	.pattern-row:last-child {
		margin-bottom: 0;
	}

	.pattern-cell {
		display: flex;
		align-items: center;
		justify-content: center;
		background: #f8f9fa;
		border-radius: 4px;
		font-weight: bold;
		border: 2px solid #e0e0e0;
	}

	/* Size variations */
	.size-3 .pattern-cell {
		width: 50px;
		height: 50px;
		font-size: 1.8rem;
	}

	.size-4 .pattern-cell {
		width: 45px;
		height: 45px;
		font-size: 1.6rem;
	}

	.size-5 .pattern-cell {
		width: 40px;
		height: 40px;
		font-size: 1.4rem;
	}

	.size-6 .pattern-cell {
		width: 35px;
		height: 35px;
		font-size: 1.2rem;
	}

	.vs-divider {
		font-size: 3rem;
		font-weight: bold;
		color: #667eea;
	}

	.decision-area {
		text-align: center;
		padding: 2rem;
	}

	.decision-area h3 {
		color: #2c3e50;
		margin-bottom: 2rem;
		font-size: 1.5rem;
	}

	.decision-buttons {
		display: flex;
		gap: 2rem;
		justify-content: center;
		margin-bottom: 1rem;
	}

	.decision-btn {
		padding: 1.5rem 3rem;
		border: none;
		border-radius: 12px;
		font-size: 1.3rem;
		font-weight: bold;
		cursor: pointer;
		transition: all 0.3s;
		box-shadow: 0 4px 12px rgba(0,0,0,0.2);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		color: white;
	}

	.decision-btn.same {
		background: linear-gradient(135deg, #4CAF50, #45a049);
	}

	.decision-btn.different {
		background: linear-gradient(135deg, #f44336, #d32f2f);
	}

	.decision-btn:hover {
		transform: translateY(-4px);
		box-shadow: 0 6px 20px rgba(0,0,0,0.3);
	}

	.btn-icon {
		font-size: 2rem;
	}

	.btn-text {
		font-size: 1.2rem;
	}

	.time-hint {
		color: #666;
		font-size: 0.9rem;
		margin-top: 1rem;
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

	.performance-badge {
		display: inline-block;
		border: 4px solid;
		border-radius: 16px;
		padding: 1.5rem 3rem;
		margin-bottom: 2rem;
	}

	.perf-level {
		font-size: 2rem;
		font-weight: bold;
		margin-bottom: 0.5rem;
	}

	.perf-speed {
		font-size: 1.5rem;
		opacity: 0.9;
	}

	.results-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
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

	.result-card.primary {
		background: linear-gradient(135deg, #4CAF50, #45a049);
		grid-column: span 2;
	}

	.result-icon {
		font-size: 2.5rem;
		margin-bottom: 0.5rem;
	}

	.result-value {
		font-size: 2.5rem;
		font-weight: bold;
		margin-bottom: 0.5rem;
	}

	.result-label {
		font-size: 1rem;
		opacity: 0.95;
		margin-bottom: 0.25rem;
	}

	.result-sublabel {
		font-size: 0.85rem;
		opacity: 0.8;
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

	.breakdown-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
	}

	.breakdown-item {
		display: flex;
		justify-content: space-between;
		padding: 0.75rem;
		background: white;
		border-radius: 8px;
	}

	.breakdown-item .value {
		font-weight: bold;
		color: #667eea;
	}

	.breakdown-item .value.success {
		color: #4CAF50;
	}

	.breakdown-item .value.error {
		color: #f44336;
	}

	.clinical-context {
		background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
		padding: 1.5rem;
		border-radius: 12px;
		margin: 2rem 0;
		text-align: left;
	}

	.clinical-context h3 {
		color: #667eea;
		margin: 0 0 1rem 0;
	}

	.clinical-context p {
		margin: 0 0 1rem 0;
		line-height: 1.7;
		color: #555;
	}

	.clinical-context p:last-child {
		margin-bottom: 0;
	}

	.why-matters {
		background: #fff3cd;
		padding: 1rem;
		border-radius: 8px;
		border-left: 4px solid #FFC107;
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
		flex-wrap: wrap;
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

	.actions button:last-child {
		background: linear-gradient(135deg, #4CAF50, #45a049);
		color: white;
	}

	.actions button:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0,0,0,0.2);
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

	@media (max-width: 768px) {
		.patterns-display {
			flex-direction: column;
		}

		.decision-buttons {
			flex-direction: column;
		}

		.results-grid {
			grid-template-columns: 1fr;
		}

		.result-card.primary {
			grid-column: span 1;
		}
	}
</style>

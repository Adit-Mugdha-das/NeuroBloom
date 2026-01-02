<script>
	import { goto } from '$app/navigation';
	import { generateMOTTrial, submitMOTResponse } from '$lib/api';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import { user } from '$lib/stores';
	import { onDestroy, onMount } from 'svelte';

	let currentUser = null;
	user.subscribe((value) => {
		currentUser = value;
	});

	// Game phases
	let phase = 'intro'; // intro, highlighting, tracking, selection, results
	let trialData = null;
	let difficulty = 5;

	// Object tracking
	let objects = [];
	let selectedObjects = new Set();
	let animationId = null;
	let startTime = null;
	let timeRemaining = 0;
	let timerInterval = null;

	// Results
	let results = null;
	let earnedBadges = [];

	// Phase timing
	const HIGHLIGHT_DURATION = 2000; // 2 seconds to show targets
	const PAUSE_BEFORE_TRACKING = 1000; // 1 second pause

	onMount(() => {
		if (!currentUser) {
			goto('/login');
			return;
		}
		loadTrial();
	});

	onDestroy(() => {
		stopAnimation();
		if (timerInterval) clearInterval(timerInterval);
	});

	async function loadTrial() {
		try {
			const response = await generateMOTTrial(currentUser.id);
			trialData = response.trial_data;
			difficulty = response.difficulty;
			
			// Initialize objects from trial data
			objects = trialData.objects.map(obj => ({
				...obj,
				x: obj.x,
				y: obj.y,
				vx: obj.vx,
				vy: obj.vy,
				is_target: obj.is_target,
				show_highlight: false,
				radius: 20
			}));

			phase = 'intro';
		} catch (error) {
			console.error('Error loading trial:', error);
			alert('Error loading task. Please try again.');
		}
	}

	function startTask() {
		phase = 'highlighting';
		
		// Show targets highlighted
		objects = objects.map(obj => ({
			...obj,
			show_highlight: obj.is_target
		}));

		// After highlight duration, start tracking
		setTimeout(() => {
			// Hide highlights
			objects = objects.map(obj => ({
				...obj,
				show_highlight: false
			}));

			// Pause before tracking
			setTimeout(() => {
				startTracking();
			}, PAUSE_BEFORE_TRACKING);
		}, HIGHLIGHT_DURATION);
	}

	function startTracking() {
		phase = 'tracking';
		startTime = Date.now();
		timeRemaining = trialData.tracking_duration;
		
		// Start timer countdown
		timerInterval = setInterval(() => {
			const elapsed = (Date.now() - startTime) / 1000;
			timeRemaining = Math.max(0, trialData.tracking_duration - elapsed);
			
			if (timeRemaining <= 0) {
				stopTracking();
			}
		}, 100);

		// Start animation
		animationId = requestAnimationFrame(updateObjects);
	}

	function updateObjects() {
		const deltaTime = 1 / 60; // Assume 60 FPS
		const arenaSize = trialData.arena_size;
		const radius = 20;

		objects = objects.map(obj => {
			let newX = obj.x + obj.vx;
			let newY = obj.y + obj.vy;
			let newVx = obj.vx;
			let newVy = obj.vy;

			// Bounce off walls
			if (newX - radius < 0) {
				newX = radius;
				newVx = Math.abs(newVx);
			} else if (newX + radius > arenaSize) {
				newX = arenaSize - radius;
				newVx = -Math.abs(newVx);
			}

			if (newY - radius < 0) {
				newY = radius;
				newVy = Math.abs(newVy);
			} else if (newY + radius > arenaSize) {
				newY = arenaSize - radius;
				newVy = -Math.abs(newVy);
			}

			return {
				...obj,
				x: newX,
				y: newY,
				vx: newVx,
				vy: newVy
			};
		});

		animationId = requestAnimationFrame(updateObjects);
	}

	function stopTracking() {
		stopAnimation();
		if (timerInterval) {
			clearInterval(timerInterval);
			timerInterval = null;
		}
		phase = 'selection';
	}

	function stopAnimation() {
		if (animationId) {
			cancelAnimationFrame(animationId);
			animationId = null;
		}
	}

	function toggleObjectSelection(objectId) {
		if (selectedObjects.has(objectId)) {
			selectedObjects.delete(objectId);
		} else {
			selectedObjects.add(objectId);
		}
		selectedObjects = selectedObjects; // Trigger reactivity
	}

	async function submitSelection() {
		const responseTime = (Date.now() - startTime) / 1000;
		
		const userResponse = {
			selected_objects: Array.from(selectedObjects),
			response_time: responseTime
		};

		try {
			const response = await submitMOTResponse(currentUser.id, {
				trial_data: trialData,
				user_response: userResponse
			});

			results = response;
			earnedBadges = response.new_badges || [];
			phase = 'results';
		} catch (error) {
			console.error('Error submitting response:', error);
			alert('Error submitting response. Please try again.');
		}
	}

	function nextTrial() {
		selectedObjects = new Set();
		results = null;
		earnedBadges = [];
		loadTrial();
	}

	function exitTask() {
		goto('/training');
	}

	// Helper to get domain badge color
	function getDomainColor(domain) {
		const colors = {
			visual_scanning: 'from-purple-500 to-pink-500'
		};
		return colors[domain] || 'from-blue-500 to-purple-500';
	}
</script>

<div class="mot-container">
	<BadgeNotification badges={earnedBadges} />

	<!-- Header -->
	<div class="task-header">
		<div class="header-content">
			<div class="task-badges">
				<span class="domain-badge bg-gradient-to-r {getDomainColor('visual_scanning')}">
					👁️ Visual Scanning
				</span>
				<span class="difficulty-badge">Level {difficulty}</span>
			</div>
			<h1 class="task-title">Multiple Object Tracking</h1>
			<p class="task-subtitle">Dynamic Visual Attention • Pylyshyn & Storm (2006)</p>
		</div>
	</div>

	<!-- Intro Phase -->
	{#if phase === 'intro'}
		<div class="phase-container intro-phase">
			<div class="intro-card">
				<div class="clinical-note">
					<span class="clinical-icon">🔬</span>
					<div>
						<div class="clinical-label">Clinical Validation</div>
						<div class="clinical-text">
							Measures sustained visual attention and dynamic tracking ability, 
							relevant for driving safety and real-world multitasking in MS patients.
						</div>
					</div>
				</div>

				<div class="instructions-section">
					<h2 class="section-title">How This Task Works</h2>
					
					<div class="instruction-steps">
						<div class="step-item">
							<div class="step-number">1</div>
							<div class="step-content">
								<div class="step-title">Watch the Targets</div>
								<div class="step-desc">
									Several circles will flash yellow — these are your targets to track
								</div>
							</div>
						</div>

						<div class="step-item">
							<div class="step-number">2</div>
							<div class="step-content">
								<div class="step-title">Track as They Move</div>
								<div class="step-desc">
									All circles will move randomly. Keep your eyes on the targets!
								</div>
							</div>
						</div>

						<div class="step-item">
							<div class="step-number">3</div>
							<div class="step-content">
								<div class="step-title">Select the Targets</div>
								<div class="step-desc">
									When movement stops, click all the circles you were tracking
								</div>
							</div>
						</div>
					</div>
				</div>

				<div class="task-details-grid">
					<div class="detail-card">
						<div class="detail-label">Objects</div>
						<div class="detail-value">{trialData?.total_objects || 0}</div>
					</div>
					<div class="detail-card">
						<div class="detail-label">Targets to Track</div>
						<div class="detail-value">{trialData?.num_targets || 0}</div>
					</div>
					<div class="detail-card">
						<div class="detail-label">Tracking Time</div>
						<div class="detail-value">{trialData?.tracking_duration || 0}s</div>
					</div>
					<div class="detail-card">
						<div class="detail-label">Speed</div>
						<div class="detail-value">{trialData?.speed_multiplier?.toFixed(1) || 1}×</div>
					</div>
				</div>

				<button class="start-button" on:click={startTask}>
					<span class="button-icon">▶</span>
					Begin Tracking
				</button>
			</div>
		</div>
	{/if}

	<!-- Highlighting Phase -->
	{#if phase === 'highlighting'}
		<div class="phase-container tracking-phase">
			<div class="phase-instruction">
				<h2 class="phase-title">👀 Remember These Targets</h2>
				<p class="phase-subtitle">The yellow circles are your targets to track</p>
			</div>

			<div class="tracking-arena" style="width: {trialData.arena_size}px; height: {trialData.arena_size}px;">
				<svg width={trialData.arena_size} height={trialData.arena_size}>
					{#each objects as obj (obj.id)}
						<circle
							cx={obj.x}
							cy={obj.y}
							r={obj.radius}
							class="tracking-object"
							class:highlighted={obj.show_highlight}
						/>
					{/each}
				</svg>
			</div>
		</div>
	{/if}

	<!-- Tracking Phase -->
	{#if phase === 'tracking'}
		<div class="phase-container tracking-phase">
			<div class="tracking-controls">
				<div class="timer-display" class:critical={timeRemaining < 3}>
					<span class="timer-icon">⏱️</span>
					<span class="timer-value">{timeRemaining.toFixed(1)}s</span>
				</div>
				<div class="tracking-hint">
					Keep your eyes on the targets as they move!
				</div>
			</div>

			<div class="tracking-arena" style="width: {trialData.arena_size}px; height: {trialData.arena_size}px;">
				<svg width={trialData.arena_size} height={trialData.arena_size}>
					{#each objects as obj (obj.id)}
						<circle
							cx={obj.x}
							cy={obj.y}
							r={obj.radius}
							class="tracking-object moving"
						/>
					{/each}
				</svg>
			</div>
		</div>
	{/if}

	<!-- Selection Phase -->
	{#if phase === 'selection'}
		<div class="phase-container selection-phase">
			<div class="phase-instruction">
				<h2 class="phase-title">🎯 Select the Targets</h2>
				<p class="phase-subtitle">
					Click on the {trialData.num_targets} circles you were tracking
					<span class="selection-count">({selectedObjects.size}/{trialData.num_targets} selected)</span>
				</p>
			</div>

			<div class="tracking-arena" style="width: {trialData.arena_size}px; height: {trialData.arena_size}px;">
				<svg width={trialData.arena_size} height={trialData.arena_size}>
					{#each objects as obj (obj.id)}
						<circle
							cx={obj.x}
							cy={obj.y}
							r={obj.radius}
							class="tracking-object selectable"
							class:selected={selectedObjects.has(obj.id)}
							role="button"
							tabindex="0"
							on:click={() => toggleObjectSelection(obj.id)}
							on:keydown={(e) => e.key === 'Enter' && toggleObjectSelection(obj.id)}
						/>
					{/each}
				</svg>
			</div>

			<div class="selection-actions">
				<button class="submit-button" on:click={submitSelection} disabled={selectedObjects.size === 0}>
					Submit Selection
				</button>
			</div>
		</div>
	{/if}

	<!-- Results Phase -->
	{#if phase === 'results' && results}
		<div class="phase-container results-phase">
			<div class="results-header">
				<h2 class="results-title">📊 Tracking Results</h2>
				<div class="performance-badge performance-{results.performance}">
					{results.performance === 'perfect' ? '🏆 Perfect!' :
					 results.performance === 'excellent' ? '⭐ Excellent' :
					 results.performance === 'good' ? '👍 Good' :
					 results.performance === 'average' ? '📈 Average' :
					 '💪 Keep Practicing'}
				</div>
			</div>

			<div class="results-grid">
				<div class="result-card primary">
					<div class="result-label">Overall Score</div>
					<div class="result-value">{(results.score * 100).toFixed(0)}%</div>
				</div>

				<div class="result-card">
					<div class="result-label">Accuracy (Recall)</div>
					<div class="result-value">{(results.accuracy * 100).toFixed(0)}%</div>
					<div class="result-detail">{results.targets_found}/{results.total_targets} targets found</div>
				</div>

				<div class="result-card">
					<div class="result-label">Precision</div>
					<div class="result-value">{(results.precision * 100).toFixed(0)}%</div>
					<div class="result-detail">{results.false_positives} false alarm{results.false_positives !== 1 ? 's' : ''}</div>
				</div>

				<div class="result-card">
					<div class="result-label">F1 Score</div>
					<div class="result-value">{(results.f1_score * 100).toFixed(0)}%</div>
					<div class="result-detail">Balanced metric</div>
				</div>

				<div class="result-card">
					<div class="result-label">Tracking Efficiency</div>
					<div class="result-value">{(results.tracking_efficiency * 100).toFixed(0)}%</div>
					<div class="result-detail">
						{results.targets_missed} missed, {results.false_positives} extra
					</div>
				</div>

				<div class="result-card">
					<div class="result-label">Response Time</div>
					<div class="result-value">{results.response_time.toFixed(1)}s</div>
					<div class="result-detail">Selection time</div>
				</div>
			</div>

			{#if results.feedback_message}
				<div class="feedback-card">
					<div class="feedback-icon">💡</div>
					<div class="feedback-text">{results.feedback_message}</div>
				</div>
			{/if}

			{#if results.new_difficulty !== results.old_difficulty}
				<div class="adaptation-notice">
					<span class="adaptation-icon">
						{results.new_difficulty > results.old_difficulty ? '⬆️' : '⬇️'}
					</span>
					<span class="adaptation-text">{results.adaptation_reason}</span>
				</div>
			{/if}

			<div class="results-actions">
				<button class="next-button" on:click={nextTrial}>
					Next Trial
				</button>
				<button class="exit-button" on:click={exitTask}>
					Exit Task
				</button>
			</div>
		</div>
	{/if}
</div>

<style>
	.mot-container {
		min-height: 100vh;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		padding: 2rem;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
	}

	/* Header Styles */
	.task-header {
		background: white;
		border-radius: 16px;
		padding: 2rem;
		margin-bottom: 2rem;
		box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
	}

	.header-content {
		text-align: center;
	}

	.task-badges {
		display: flex;
		gap: 0.75rem;
		justify-content: center;
		margin-bottom: 1rem;
		flex-wrap: wrap;
	}

	.domain-badge {
		padding: 0.5rem 1.25rem;
		border-radius: 50px;
		color: white;
		font-weight: 600;
		font-size: 0.9rem;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
	}

	.difficulty-badge {
		padding: 0.5rem 1.25rem;
		border-radius: 50px;
		background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
		color: white;
		font-weight: 600;
		font-size: 0.9rem;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
	}

	.task-title {
		font-size: 2.5rem;
		font-weight: 700;
		color: #1a202c;
		margin: 0 0 0.5rem 0;
	}

	.task-subtitle {
		font-size: 1.1rem;
		color: #718096;
		margin: 0;
	}

	/* Phase Container */
	.phase-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 2rem;
	}

	/* Intro Phase */
	.intro-card {
		background: white;
		border-radius: 16px;
		padding: 2.5rem;
		max-width: 700px;
		width: 100%;
		box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
	}

	.clinical-note {
		display: flex;
		gap: 1rem;
		background: linear-gradient(135deg, #e0e7ff 0%, #f3e8ff 100%);
		padding: 1.25rem;
		border-radius: 12px;
		margin-bottom: 2rem;
		border-left: 4px solid #667eea;
	}

	.clinical-icon {
		font-size: 1.5rem;
		flex-shrink: 0;
	}

	.clinical-label {
		font-weight: 700;
		color: #5a67d8;
		font-size: 0.85rem;
		text-transform: uppercase;
		letter-spacing: 0.5px;
		margin-bottom: 0.25rem;
	}

	.clinical-text {
		color: #4a5568;
		line-height: 1.6;
		font-size: 0.95rem;
	}

	.instructions-section {
		margin-bottom: 2rem;
	}

	.section-title {
		font-size: 1.5rem;
		font-weight: 700;
		color: #2d3748;
		margin-bottom: 1.5rem;
		text-align: center;
	}

	.instruction-steps {
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	.step-item {
		display: flex;
		gap: 1rem;
		align-items: flex-start;
	}

	.step-number {
		width: 36px;
		height: 36px;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 700;
		flex-shrink: 0;
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
	}

	.step-content {
		flex: 1;
	}

	.step-title {
		font-weight: 600;
		color: #2d3748;
		margin-bottom: 0.25rem;
		font-size: 1.05rem;
	}

	.step-desc {
		color: #718096;
		line-height: 1.5;
		font-size: 0.95rem;
	}

	.task-details-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
		gap: 1rem;
		margin-bottom: 2rem;
	}

	.detail-card {
		background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
		padding: 1rem;
		border-radius: 12px;
		text-align: center;
		border: 2px solid #e2e8f0;
	}

	.detail-label {
		font-size: 0.85rem;
		color: #718096;
		font-weight: 600;
		margin-bottom: 0.5rem;
	}

	.detail-value {
		font-size: 1.75rem;
		font-weight: 700;
		color: #2d3748;
	}

	.start-button {
		width: 100%;
		padding: 1.25rem;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		border-radius: 12px;
		font-size: 1.25rem;
		font-weight: 700;
		cursor: pointer;
		transition: all 0.3s ease;
		box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.75rem;
	}

	.start-button:hover {
		transform: translateY(-2px);
		box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
	}

	.button-icon {
		font-size: 1.5rem;
	}

	/* Tracking Arena */
	.tracking-arena {
		background: white;
		border-radius: 16px;
		box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
		padding: 1rem;
		margin: 0 auto;
	}

	.tracking-arena svg {
		display: block;
		border: 3px solid #e2e8f0;
		border-radius: 12px;
		background: #f7fafc;
	}

	.tracking-object {
		fill: #4299e1;
		stroke: #2b6cb0;
		stroke-width: 2;
		transition: all 0.2s ease;
	}

	.tracking-object.highlighted {
		fill: #fbbf24;
		stroke: #f59e0b;
		stroke-width: 4;
		filter: drop-shadow(0 0 8px rgba(251, 191, 36, 0.6));
		animation: pulse 0.8s ease-in-out infinite;
	}

	@keyframes pulse {
		0%, 100% { transform: scale(1); }
		50% { transform: scale(1.1); }
	}

	.tracking-object.selectable {
		cursor: pointer;
	}

	.tracking-object.selectable:hover {
		fill: #63b3ed;
		stroke-width: 3;
	}

	.tracking-object.selected {
		fill: #48bb78;
		stroke: #2f855a;
		stroke-width: 4;
		filter: drop-shadow(0 0 6px rgba(72, 187, 120, 0.5));
	}

	/* Phase Instructions */
	.phase-instruction {
		background: white;
		border-radius: 16px;
		padding: 1.5rem 2rem;
		text-align: center;
		box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
		max-width: 600px;
		width: 100%;
	}

	.phase-title {
		font-size: 1.75rem;
		font-weight: 700;
		color: #2d3748;
		margin: 0 0 0.5rem 0;
	}

	.phase-subtitle {
		font-size: 1.1rem;
		color: #718096;
		margin: 0;
	}

	.selection-count {
		color: #667eea;
		font-weight: 600;
	}

	/* Tracking Controls */
	.tracking-controls {
		background: white;
		border-radius: 16px;
		padding: 1.5rem 2rem;
		box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
		max-width: 600px;
		width: 100%;
		text-align: center;
	}

	.timer-display {
		display: inline-flex;
		align-items: center;
		gap: 0.75rem;
		background: linear-gradient(135deg, #e6fffa 0%, #b2f5ea 100%);
		padding: 0.75rem 2rem;
		border-radius: 50px;
		margin-bottom: 0.75rem;
		border: 2px solid #81e6d9;
	}

	.timer-display.critical {
		background: linear-gradient(135deg, #fed7d7 0%, #fc8181 100%);
		border-color: #fc8181;
		animation: blink 0.5s ease-in-out infinite;
	}

	@keyframes blink {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.7; }
	}

	.timer-icon {
		font-size: 1.5rem;
	}

	.timer-value {
		font-size: 1.75rem;
		font-weight: 700;
		color: #2d3748;
		min-width: 60px;
	}

	.tracking-hint {
		color: #718096;
		font-size: 1.05rem;
	}

	/* Selection Actions */
	.selection-actions {
		width: 100%;
		max-width: 400px;
	}

	.submit-button {
		width: 100%;
		padding: 1rem 2rem;
		background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
		color: white;
		border: none;
		border-radius: 12px;
		font-size: 1.25rem;
		font-weight: 700;
		cursor: pointer;
		transition: all 0.3s ease;
		box-shadow: 0 6px 20px rgba(72, 187, 120, 0.4);
	}

	.submit-button:hover:not(:disabled) {
		transform: translateY(-2px);
		box-shadow: 0 8px 25px rgba(72, 187, 120, 0.5);
	}

	.submit-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	/* Results Phase */
	.results-header {
		background: white;
		border-radius: 16px;
		padding: 2rem;
		text-align: center;
		box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
		max-width: 600px;
		width: 100%;
	}

	.results-title {
		font-size: 2rem;
		font-weight: 700;
		color: #2d3748;
		margin: 0 0 1rem 0;
	}

	.performance-badge {
		display: inline-block;
		padding: 0.75rem 1.5rem;
		border-radius: 50px;
		font-weight: 700;
		font-size: 1.1rem;
	}

	.performance-perfect {
		background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
		color: white;
		box-shadow: 0 4px 12px rgba(251, 191, 36, 0.4);
	}

	.performance-excellent {
		background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
		color: white;
		box-shadow: 0 4px 12px rgba(72, 187, 120, 0.4);
	}

	.performance-good {
		background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
		color: white;
		box-shadow: 0 4px 12px rgba(66, 153, 225, 0.4);
	}

	.performance-average {
		background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
		color: white;
		box-shadow: 0 4px 12px rgba(237, 137, 54, 0.4);
	}

	.performance-needs_improvement {
		background: linear-gradient(135deg, #a0aec0 0%, #718096 100%);
		color: white;
		box-shadow: 0 4px 12px rgba(160, 174, 192, 0.4);
	}

	.results-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1.5rem;
		max-width: 900px;
		width: 100%;
	}

	.result-card {
		background: white;
		border-radius: 12px;
		padding: 1.5rem;
		text-align: center;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
		border: 2px solid #e2e8f0;
	}

	.result-card.primary {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		grid-column: 1 / -1;
	}

	.result-label {
		font-size: 0.9rem;
		font-weight: 600;
		margin-bottom: 0.5rem;
		opacity: 0.9;
	}

	.result-card.primary .result-label {
		color: white;
	}

	.result-card:not(.primary) .result-label {
		color: #718096;
	}

	.result-value {
		font-size: 2.25rem;
		font-weight: 700;
		margin-bottom: 0.25rem;
	}

	.result-card.primary .result-value {
		color: white;
	}

	.result-card:not(.primary) .result-value {
		color: #2d3748;
	}

	.result-detail {
		font-size: 0.85rem;
		opacity: 0.8;
		color: #a0aec0;
	}

	.feedback-card {
		background: linear-gradient(135deg, #e6fffa 0%, #b2f5ea 100%);
		border: 2px solid #81e6d9;
		border-radius: 12px;
		padding: 1.5rem;
		display: flex;
		gap: 1rem;
		align-items: flex-start;
		max-width: 700px;
		width: 100%;
	}

	.feedback-icon {
		font-size: 1.75rem;
		flex-shrink: 0;
	}

	.feedback-text {
		color: #234e52;
		line-height: 1.6;
		font-size: 1.05rem;
		font-weight: 500;
	}

	.adaptation-notice {
		background: white;
		border-radius: 12px;
		padding: 1rem 1.5rem;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
		display: flex;
		align-items: center;
		gap: 0.75rem;
		max-width: 600px;
		width: 100%;
		border-left: 4px solid #667eea;
	}

	.adaptation-icon {
		font-size: 1.5rem;
	}

	.adaptation-text {
		color: #4a5568;
		font-weight: 500;
	}

	.results-actions {
		display: flex;
		gap: 1rem;
		max-width: 500px;
		width: 100%;
	}

	.next-button,
	.exit-button {
		flex: 1;
		padding: 1rem 2rem;
		border: none;
		border-radius: 12px;
		font-size: 1.1rem;
		font-weight: 700;
		cursor: pointer;
		transition: all 0.3s ease;
	}

	.next-button {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
	}

	.next-button:hover {
		transform: translateY(-2px);
		box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
	}

	.exit-button {
		background: white;
		color: #4a5568;
		border: 2px solid #e2e8f0;
	}

	.exit-button:hover {
		background: #f7fafc;
		border-color: #cbd5e0;
	}

	@media (max-width: 768px) {
		.mot-container {
			padding: 1rem;
		}

		.task-title {
			font-size: 2rem;
		}

		.task-subtitle {
			font-size: 1rem;
		}

		.intro-card {
			padding: 1.5rem;
		}

		.task-details-grid {
			grid-template-columns: repeat(2, 1fr);
		}

		.results-grid {
			grid-template-columns: 1fr;
		}

		.results-actions {
			flex-direction: column;
		}
	}
</style>

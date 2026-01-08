<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { API_BASE_URL } from '$lib/api';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let gamePhase = 'loading'; // loading, intro, playing, results
	let trialData = null;
	let grid = [];
	let targetItems = [];
	let markedPositions = [];
	let startTime = null;
	let timeRemaining = 0;
	let timerInterval = null;
	let taskId = null;
	
	let results = null;
	let earnedBadges = [];

	// Load trial on mount
	onMount(async () => {
		if (!$user) {
			goto('/login');
			return;
		}
		await loadTrial();
	});

	async function loadTrial() {
		try {
			const response = await fetch(`${API_BASE_URL}/api/training/tasks/cancellation-test/generate/${$user.id}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				credentials: 'include'
			});

			if (!response.ok) throw new Error('Failed to load trial');
			
			const data = await response.json();
			trialData = data.trial_data;
			grid = trialData.grid;
			targetItems = trialData.target_items;
			timeRemaining = trialData.time_limit;
			gamePhase = 'intro';
		} catch (error) {
			console.error('Error loading trial:', error);
			alert('Failed to load task. Please try again.');
		}
	}

	function startGame() {
		markedPositions = [];
		startTime = Date.now();
		gamePhase = 'playing';
		
		// Start timer
		timerInterval = setInterval(() => {
			const elapsed = Math.floor((Date.now() - startTime) / 1000);
			timeRemaining = Math.max(0, trialData.time_limit - elapsed);
			
			if (timeRemaining === 0) {
				finishGame();
			}
		}, 100);
	}

	function toggleCell(row, col, item) {
		const positionKey = `${row},${col}`;
		const existingIndex = markedPositions.findIndex(p => p.row === row && p.col === col);
		
		if (existingIndex >= 0) {
			// Unmark
			markedPositions = markedPositions.filter((_, i) => i !== existingIndex);
		} else {
			// Mark
			markedPositions = [...markedPositions, { row, col, item }];
		}
	}

	function isMarked(row, col) {
		return markedPositions.some(p => p.row === row && p.col === col);
	}

	function finishGame() {
		if (timerInterval) {
			clearInterval(timerInterval);
			timerInterval = null;
		}
		submitResults();
	}

	async function submitResults() {
		const completionTime = (Date.now() - startTime) / 1000;
		taskId = $page.url.searchParams.get('taskId');
		
		try {
			const response = await fetch(`${API_BASE_URL}/api/training/tasks/cancellation-test/submit/${$user.id}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				credentials: 'include',
				body: JSON.stringify({
					marked_positions: markedPositions,
					target_positions: trialData.target_positions,
					completion_time: completionTime,
					time_limit: trialData.time_limit,
					difficulty: trialData.difficulty,
					task_id: taskId
				})
			});

			if (!response.ok) throw new Error('Failed to submit results');
			
			results = await response.json();
			earnedBadges = results.new_badges || [];
			gamePhase = 'results';
		} catch (error) {
			console.error('Error submitting results:', error);
			alert('Failed to submit results. Please try again.');
		}
	}

	function getPerformanceColor(rating) {
		const colors = {
			excellent: '#10b981',
			good: '#3b82f6',
			average: '#f59e0b',
			below_average: '#ef4444',
			poor: '#991b1b'
		};
		return colors[rating] || '#64748b';
	}

	function getPerformanceEmoji(rating) {
		const emojis = {
			excellent: '🌟',
			good: '👍',
			average: '✓',
			below_average: '📈',
			poor: '❌'
		};
		return emojis[rating] || '✓';
	}

	function formatTime(seconds) {
		const mins = Math.floor(seconds / 60);
		const secs = seconds % 60;
		return `${mins}:${secs.toString().padStart(2, '0')}`;
	}

	function restartTask() {
		gamePhase = 'loading';
		results = null;
		earnedBadges = [];
		loadTrial();
	}

	function goToDashboard() {
		goto('/training');
	}
</script>

<div style="min-height: 100vh; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); padding: 2rem;">
	<div style="max-width: 1400px; margin: 0 auto;">

		{#if gamePhase === 'loading'}
			<div style="background: white; border-radius: 16px; padding: 3rem; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				<div style="font-size: 3rem; margin-bottom: 1rem;">⏳</div>
				<h2 style="color: #6366f1;">Loading Cancellation Test...</h2>
			</div>

		{:else if gamePhase === 'intro'}
			<div style="background: white; border-radius: 16px; padding: 3rem; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				<div style="text-align: center; margin-bottom: 2rem;">
					<div style="font-size: 4rem; margin-bottom: 1rem;">🔍</div>
					<h1 style="color: #6366f1; font-size: 2.5rem; margin-bottom: 0.5rem;">Cancellation Test</h1>
					<p style="color: #64748b; font-size: 1.1rem;">Visual Scanning & Attention Task</p>
				</div>

				<div style="background: #f8fafc; border-radius: 12px; padding: 2rem; margin-bottom: 2rem;">
					<h3 style="color: #1e293b; margin-bottom: 1rem;">📋 Instructions</h3>
					<div style="color: #475569; line-height: 1.8;">
						{trialData.instructions}
					</div>
					
					<div style="background: white; border-radius: 8px; padding: 1.5rem; margin-top: 1.5rem;">
						<h4 style="color: #6366f1; margin-bottom: 1rem;">Your Task:</h4>
						<ul style="color: #64748b; line-height: 2;">
							<li>Click on all instances of the target {trialData.use_symbols ? 'symbols' : 'letters'}</li>
							<li>Work as quickly and accurately as possible</li>
							<li>Click marked items again to unmark them if you made a mistake</li>
							<li>Try to scan systematically (e.g., left to right, top to bottom)</li>
							<li>Time limit: {formatTime(trialData.time_limit)}</li>
						</ul>
					</div>
				</div>

				<div style="background: #dbeafe; border: 2px solid #3b82f6; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem;">
					<div style="display: flex; align-items: center; gap: 1rem;">
						<div style="font-size: 2rem;">🎯</div>
						<div>
							<div style="color: #1e40af; font-weight: 600; font-size: 1.2rem; margin-bottom: 0.5rem;">
								Find all: {targetItems.join(', ')}
							</div>
							<div style="color: #3b82f6; font-size: 0.9rem;">
								Total targets to find: {trialData.target_count}
							</div>
						</div>
					</div>
				</div>

				<div style="text-align: center;">
					<button on:click={startGame}
						style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); color: white; 
						border: none; padding: 1.5rem 4rem; font-size: 1.3rem; border-radius: 12px; 
						cursor: pointer; font-weight: 700; box-shadow: 0 4px 15px rgba(99,102,241,0.4); 
						transition: all 0.3s;"
						on:mouseenter={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
						on:mouseleave={(e) => e.currentTarget.style.transform = 'translateY(0)'}>
						Start Task
					</button>
				</div>
			</div>

		{:else if gamePhase === 'playing'}
			<div style="background: white; border-radius: 16px; padding: 2rem; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				
				<!-- Header -->
				<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 2px solid #e2e8f0;">
					<div>
						<h2 style="color: #6366f1; margin-bottom: 0.5rem;">
							Find: {targetItems.join(', ')}
						</h2>
						<div style="color: #64748b;">
							Marked: {markedPositions.length} / {trialData.target_count} targets
						</div>
					</div>
					<div style="text-align: right;">
						<div style="font-size: 2.5rem; font-weight: 700; color: {timeRemaining < 10 ? '#ef4444' : '#6366f1'}; 
							font-variant-numeric: tabular-nums;">
							{formatTime(timeRemaining)}
						</div>
						<div style="color: #64748b; font-size: 0.9rem;">Time Remaining</div>
					</div>
				</div>

				<!-- Grid -->
				<div style="background: #f8fafc; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem; overflow-x: auto;">
					<div style="display: inline-block; min-width: 100%;">
						{#each grid as row, rowIndex}
							<div style="display: flex; gap: 2px; margin-bottom: 2px;">
								{#each row as item, colIndex}
									<button
										on:click={() => toggleCell(rowIndex, colIndex, item)}
										style="
											width: 30px; 
											height: 30px; 
											border: 2px solid {isMarked(rowIndex, colIndex) ? '#6366f1' : '#cbd5e1'}; 
											background: {isMarked(rowIndex, colIndex) ? '#dbeafe' : 'white'}; 
											border-radius: 4px; 
											cursor: pointer; 
											font-weight: 600; 
											font-size: 0.9rem;
											color: {isMarked(rowIndex, colIndex) ? '#1e40af' : '#475569'};
											transition: all 0.15s;
											display: flex;
											align-items: center;
											justify-content: center;
											user-select: none;
										"
										on:mouseenter={(e) => {
											if (!isMarked(rowIndex, colIndex)) {
												e.currentTarget.style.background = '#f1f5f9';
												e.currentTarget.style.borderColor = '#94a3b8';
											}
										}}
										on:mouseleave={(e) => {
											if (!isMarked(rowIndex, colIndex)) {
												e.currentTarget.style.background = 'white';
												e.currentTarget.style.borderColor = '#cbd5e1';
											}
										}}
									>
										{item}
									</button>
								{/each}
							</div>
						{/each}
					</div>
				</div>

				<!-- Finish Button -->
				<div style="text-align: center;">
					<button on:click={finishGame}
						style="background: #10b981; color: white; border: none; padding: 1rem 3rem; 
						font-size: 1.1rem; border-radius: 8px; cursor: pointer; font-weight: 600; 
						transition: all 0.3s;"
						on:mouseenter={(e) => e.currentTarget.style.background = '#059669'}
						on:mouseleave={(e) => e.currentTarget.style.background = '#10b981'}>
						Finish Task
					</button>
				</div>
			</div>

		{:else if gamePhase === 'results'}
			<div style="background: white; border-radius: 16px; padding: 3rem; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				
				<!-- Performance Header -->
				<div style="text-align: center; margin-bottom: 3rem;">
					<div style="font-size: 4rem; margin-bottom: 1rem;">
						{getPerformanceEmoji(results.performance_rating)}
					</div>
					<h1 style="color: {getPerformanceColor(results.performance_rating)}; font-size: 2.5rem; margin-bottom: 0.5rem; text-transform: capitalize;">
						{results.performance_rating.replace('_', ' ')} Performance!
					</h1>
					<div style="font-size: 3rem; font-weight: 700; color: #6366f1; margin-top: 1rem;">
						{results.score}%
					</div>
				</div>

				<!-- Stats Grid -->
				<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin-bottom: 3rem;">
					<div style="background: #f0fdf4; border: 2px solid #10b981; border-radius: 12px; padding: 1.5rem; text-align: center;">
						<div style="color: #059669; font-size: 0.9rem; margin-bottom: 0.5rem;">Accuracy</div>
						<div style="font-size: 2rem; font-weight: 700; color: #10b981;">{results.accuracy.toFixed(1)}%</div>
					</div>
					
					<div style="background: #eff6ff; border: 2px solid #3b82f6; border-radius: 12px; padding: 1.5rem; text-align: center;">
						<div style="color: #1e40af; font-size: 0.9rem; margin-bottom: 0.5rem;">Targets Found</div>
						<div style="font-size: 2rem; font-weight: 700; color: #3b82f6;">{results.targets_found}/{results.total_targets}</div>
					</div>
					
					<div style="background: #fef3c7; border: 2px solid #f59e0b; border-radius: 12px; padding: 1.5rem; text-align: center;">
						<div style="color: #92400e; font-size: 0.9rem; margin-bottom: 0.5rem;">Completion Time</div>
						<div style="font-size: 2rem; font-weight: 700; color: #f59e0b;">{results.completion_time.toFixed(1)}s</div>
					</div>
					
					<div style="background: #fee2e2; border: 2px solid #ef4444; border-radius: 12px; padding: 1.5rem; text-align: center;">
						<div style="color: #991b1b; font-size: 0.9rem; margin-bottom: 0.5rem;">Errors</div>
						<div style="font-size: 2rem; font-weight: 700; color: #ef4444;">
							{results.targets_missed} missed, {results.false_alarms} false
						</div>
					</div>
				</div>

				<!-- Spatial Analysis -->
				{#if results.spatial_analysis}
					<div style="background: #f8fafc; border-radius: 12px; padding: 2rem; margin-bottom: 2rem;">
						<h3 style="color: #1e293b; margin-bottom: 1.5rem;">
							📊 Spatial Pattern Analysis
						</h3>
						
						<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-bottom: 1.5rem;">
							<div>
								<div style="color: #64748b; margin-bottom: 0.5rem;">Left Side Accuracy</div>
								<div style="font-size: 1.5rem; font-weight: 700; color: #6366f1;">
									{results.spatial_analysis.left_accuracy}%
								</div>
							</div>
							<div>
								<div style="color: #64748b; margin-bottom: 0.5rem;">Right Side Accuracy</div>
								<div style="font-size: 1.5rem; font-weight: 700; color: #6366f1;">
									{results.spatial_analysis.right_accuracy}%
								</div>
							</div>
						</div>

						{#if results.spatial_analysis.neglect_detected}
							<div style="background: #fef3c7; border: 2px solid #f59e0b; border-radius: 8px; padding: 1rem;">
								<div style="color: #92400e; font-weight: 600;">
									⚠️ Asymmetric Pattern Detected
								</div>
								<div style="color: #78350f; margin-top: 0.5rem;">
									You missed more targets on the {results.spatial_analysis.neglect_side} side. 
									Try to scan both sides of the grid equally.
								</div>
							</div>
						{:else}
							<div style="background: #d1fae5; border: 2px solid #10b981; border-radius: 8px; padding: 1rem;">
								<div style="color: #065f46; font-weight: 600;">
									✓ Balanced Scanning Pattern
								</div>
								<div style="color: #047857; margin-top: 0.5rem;">
									Great job! You scanned both sides of the grid evenly.
								</div>
							</div>
						{/if}
					</div>
				{/if}

				<!-- Feedback -->
				<div style="background: #f8fafc; border-radius: 12px; padding: 2rem; margin-bottom: 2rem;">
					<div style="color: #475569; line-height: 1.8;">
						{results.feedback}
					</div>
				</div>

				<!-- Difficulty Adjustment -->
				<div style="background: linear-gradient(135deg, #dbeafe 0%, #e0e7ff 100%); border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem;">
					<div style="color: #1e40af; font-weight: 600; margin-bottom: 0.5rem;">
						🎯 Difficulty Adjustment
					</div>
					<div style="color: #3b82f6;">
						{results.adaptation_reason}
					</div>
				</div>

				<!-- Badge Notifications -->
				{#if earnedBadges.length > 0}
					<BadgeNotification badges={earnedBadges} />
				{/if}

				<!-- Action Buttons -->
				<div style="display: flex; gap: 1rem; justify-content: center; margin-top: 2rem;">
					<button on:click={restartTask}
						style="background: #6366f1; color: white; border: none; padding: 1rem 2rem; 
						font-size: 1.1rem; border-radius: 8px; cursor: pointer; font-weight: 600; 
						transition: all 0.3s;"
						on:mouseenter={(e) => e.currentTarget.style.background = '#4f46e5'}
						on:mouseleave={(e) => e.currentTarget.style.background = '#6366f1'}>
						Try Again
					</button>
					
					<button on:click={goToDashboard}
						style="background: #10b981; color: white; border: none; padding: 1rem 2rem; 
						font-size: 1.1rem; border-radius: 8px; cursor: pointer; font-weight: 600; 
						transition: all 0.3s;"
						on:mouseenter={(e) => e.currentTarget.style.background = '#059669'}
						on:mouseleave={(e) => e.currentTarget.style.background = '#10b981'}>
						Back to Dashboard
					</button>
				</div>
			</div>
		{/if}
	</div>
</div>

<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { formatNumber, locale, localeText, translateText } from '$lib/i18n';
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
	import { tasks, training } from '$lib/api';
	import { user } from '$lib/stores';
	import { getPracticeCopy } from '$lib/task-practice';
	import { onMount } from 'svelte';
	
	let currentUser = null;
	let stage = 'intro'; // intro, test, results
	
	// Training mode variables
	let isTrainingMode = false;
	let trainingPlanId = null;
	let trainingDifficulty = 1;
	let taskId = null;
	let sessionComplete = false;
	let completedTasksCount = 0;
	let totalTasksCount = 4;
	
	// Tower of Hanoi state
	let diskCount = 3;
	let towers = [];
	let selectedTower = null;
	let moves = 0;
	let optimalMoves = 7;
	let startTime = 0;
	let firstMoveTime = 0;
	let planningTime = 0;
	let completed = false;
	let isPracticeMode = false;
	let practiceStatusMessage = '';
	let recordedDiskCount = 3;

	function t(text) {
		return translateText(text ?? '', $locale);
	}

	function lt(en, bn) {
		return localeText({ en, bn }, $locale);
	}

	function n(value, options = {}) {
		return formatNumber(value, $locale, options);
	}

	function initialTowers() {
		return [Array.from({ length: diskCount }, (_, index) => diskCount - index), [], []];
	}

	function refreshTowerState() {
		towers = initialTowers();
		optimalMoves = 2 ** diskCount - 1;
	}

	function towerLabel(index) {
		return lt(`Tower ${index + 1}`, `টাওয়ার ${n(index + 1)}`);
	}

	function moveSummaryLabel() {
		return lt(`Moves: ${moves} / ${optimalMoves}`, `মুভ: ${n(moves)} / ${n(optimalMoves)}`);
	}

	function selectedTowerMessage() {
		return lt(
			`Selected Tower ${selectedTower + 1} - Click another tower to move`,
			`নির্বাচিত টাওয়ার ${n(selectedTower + 1)} - সরাতে অন্য টাওয়ারে চাপুন`
		);
	}

	function trainingProgressText() {
		return lt(
			`Training Progress: ${completedTasksCount} / ${totalTasksCount} tasks completed`,
			`ট্রেনিং অগ্রগতি: ${n(completedTasksCount)} / ${n(totalTasksCount)}টি টাস্ক সম্পন্ন`
		);
	}

	function insightMessage() {
		if (moves === optimalMoves) {
			return lt(
				'Perfect! You solved it with optimal efficiency. Excellent planning skills!',
				'চমৎকার! আপনি সর্বোত্তম দক্ষতায় ধাঁধাটি সমাধান করেছেন। আপনার পরিকল্পনা দক্ষতা দারুণ।'
			);
		}

		if (moves <= optimalMoves + 3) {
			return lt(
				"Great planning! You're close to the optimal solution.",
				'ভালো পরিকল্পনা! আপনি প্রায় সর্বোত্তম সমাধানের কাছাকাছি পৌঁছেছেন।'
			);
		}

		return lt(
			'Keep practicing. Planning ahead can help reduce unnecessary moves.',
			'অনুশীলন চালিয়ে যান। আগে থেকে পরিকল্পনা করলে অপ্রয়োজনীয় মুভ কমানো যায়।'
		);
	}

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
		taskId = $page.url.searchParams.get('taskId');
		
		if (isTrainingMode && trainingDifficulty >= 8) {
			diskCount = 5;
		} else if (isTrainingMode && trainingDifficulty >= 6) {
			diskCount = 4;
		} else {
			diskCount = 3;
		}

		recordedDiskCount = diskCount;
		refreshTowerState();
	});
	
	function backToDashboard() {
		if (isTrainingMode) {
			goto('/training');
		} else {
			goto('/dashboard');
		}
	}
	
	function startTest(practice = false) {
		isPracticeMode = practice;
		practiceStatusMessage = '';
		diskCount = practice ? 3 : recordedDiskCount;
		stage = 'test';
		refreshTowerState();
		selectedTower = null;
		moves = 0;
		startTime = Date.now();
		firstMoveTime = 0;
		planningTime = 0;
		completed = false;
	}
	
	function selectTower(index) {
		if (completed) return;
		
		if (selectedTower === null) {
			// Select source tower (must have disks)
			if (towers[index].length > 0) {
				selectedTower = index;
			}
		} else {
			// Move disk
			if (selectedTower !== index) {
				const disk = towers[selectedTower][towers[selectedTower].length - 1];
				const targetTop = towers[index][towers[index].length - 1];
				
				// Can only place smaller disk on larger disk or empty tower
				if (!targetTop || disk < targetTop) {
					// Valid move
					towers[selectedTower] = towers[selectedTower].slice(0, -1);
					towers[index] = [...towers[index], disk];
					moves++;
					
					// Record first move time (planning time)
					if (moves === 1) {
						firstMoveTime = Date.now();
						planningTime = firstMoveTime - startTime;
					}
					
					// Check if completed
					if (towers[2].length === diskCount) {
						completed = true;
						calculateResults();
					}
				}
			}
			selectedTower = null;
		}
	}
	
	function calculateResults() {
		const totalTime = Date.now() - startTime;

		if (isPracticeMode) {
			isPracticeMode = false;
			diskCount = recordedDiskCount;
			refreshTowerState();
			selectedTower = null;
			moves = 0;
			completed = false;
			planningTime = 0;
			practiceStatusMessage = getPracticeCopy($locale).complete;
			stage = 'intro';
			return;
		}
		
		stage = 'results';
		saveResults(totalTime);
	}
	
	async function saveResults(totalTime) {
		try {
			const excessMoves = moves - optimalMoves;
			const efficiency = Math.max(0, 100 - (excessMoves * 10));
			
			console.log('[Planning] Saving results:', {
				isTrainingMode,
				trainingPlanId,
				userId: currentUser?.id,
				efficiency
			});
			
			if (isTrainingMode && trainingPlanId) {
				// Submit to training session API
				console.log('[Planning] Submitting to training API');
				
				const result = await training.submitSession({
					user_id: currentUser.id,
					training_plan_id: trainingPlanId,
					domain: 'planning',
					task_type: 'tower_of_hanoi',
					score: efficiency,
					accuracy: completed ? 100 : 0,
					average_reaction_time: planningTime,
					consistency: Math.max(0, 100 - excessMoves * 5),
					errors: excessMoves,
					session_duration: Math.round(totalTime / 60000), // minutes
					task_id: taskId
				});
				
				sessionComplete = result.session_complete;
				completedTasksCount = result.completed_tasks;
				totalTasksCount = result.total_tasks;
				
				console.log('[Planning] Training session saved:', result);
			} else {
				// Submit to regular task result API (baseline mode)
				await tasks.submitResult(
					currentUser.id,
					'planning',
					efficiency,
					JSON.stringify({
						moves_taken: moves,
						optimal_moves: optimalMoves,
						excess_moves: excessMoves,
						planning_time_ms: planningTime,
						total_time_seconds: Math.round(totalTime / 1000),
						completed: completed
					})
				);
			}
		} catch (error) {
			console.error('Error saving results:', error);
		}
	}
	
	function resetTest() {
		refreshTowerState();
		selectedTower = null;
		moves = 0;
		completed = false;
		startTime = Date.now();
		firstMoveTime = 0;
		planningTime = 0;
	}
	
	function getDiskColor(size) {
		const colors = ['#4caf50', '#2196f3', '#ff9800', '#ef4444', '#8b5cf6'];
		return colors[size - 1];
	}
</script>

<div class="test-container" data-localize-skip>
	{#if stage === 'intro'}
		<div class="test-card">
			<h1>{t('Planning Test')}</h1>
			<h2 style="color: #666; font-size: 20px; margin-bottom: 30px;">{t('Tower of Hanoi')}</h2>
			
			<div style="text-align: left; max-width: 600px; margin: 0 auto;">
				<h3 style="color: #667eea; margin-bottom: 15px;">{t('Instructions:')}</h3>
				<ul style="line-height: 1.8; color: #666;">
					<li>{t('Move all disks from the first tower to the third tower')}</li>
					<li>{t('You can only move one disk at a time')}</li>
					<li>{t('A larger disk cannot be placed on a smaller disk')}</li>
					<li>{@html lt(`Try to complete in <strong>minimum moves (${optimalMoves})</strong>`, `যত কম সম্ভব মুভে শেষ করার চেষ্টা করুন <strong>(${n(optimalMoves)})</strong>`)}</li>
					<li>{t('Think before you move - planning is key!')}</li>
				</ul>
				
				<div style="background: #f0f7ff; padding: 20px; border-radius: 8px; margin-top: 30px;">
					<h4 style="color: #667eea; margin-bottom: 10px;">{t('How to Play:')}</h4>
					<p style="color: #666; line-height: 1.6;">
						{lt(
							'1. Click on a tower to pick up the top disk',
							'১. উপরের ডিস্ক তুলতে একটি টাওয়ারে চাপুন'
						)}<br>
						{lt(
							'2. Click on another tower to place it',
							'২. বসাতে অন্য টাওয়ারে চাপুন'
						)}<br>
						{lt(
							'3. Goal: Get all disks on the rightmost tower',
							'৩. লক্ষ্য: সব ডিস্ক ডানদিকের টাওয়ারে নিয়ে যান'
						)}
					</p>
				</div>
			</div>
			
			<TaskPracticeActions
				locale={$locale}
				startLabel={localeText({ en: 'Start Actual Task', bn: 'আসল টাস্ক শুরু করুন' }, $locale)}
				statusMessage={practiceStatusMessage}
				align="center"
				on:start={() => startTest(false)}
				on:practice={() => startTest(true)}
			/>
			<button class="btn-secondary" on:click={backToDashboard}>
				{t('Back to Dashboard')}
			</button>
		</div>
	
	{:else if stage === 'test'}
		<div class="test-card">
			{#if isPracticeMode}
				<PracticeModeBanner locale={$locale} />
			{/if}
			<div style="display: flex; justify-content: space-between; margin-bottom: 30px;">
				<div class="timer">{moveSummaryLabel()}</div>
				<button class="btn-secondary" on:click={resetTest} style="padding: 8px 20px; font-size: 14px;">
					{t('Reset')}
				</button>
			</div>
			
			<!-- Towers Display -->
			<div style="display: flex; justify-content: center; gap: 40px; margin: 60px 0;">
				{#each towers as tower, index}
					<div 
						class="tower"
						class:selected={selectedTower === index}
						on:click={() => selectTower(index)}
						style="cursor: pointer; width: 150px;"
					>
						<!-- Tower pole -->
						<div style="width: 10px; height: 180px; background: #999; margin: 0 auto; position: relative;">
							<!-- Base -->
							<div style="width: 150px; height: 10px; background: #666; position: absolute; bottom: -10px; left: -70px;"></div>
							
							<!-- Disks -->
							<div style="position: absolute; bottom: 0; width: 150px; left: -70px; display: flex; flex-direction: column-reverse; align-items: center; gap: 2px;">
								{#each tower as disk}
									<div 
										style="
											width: {disk * 40}px; 
											height: 25px; 
											background: {getDiskColor(disk)}; 
											border-radius: 5px;
											border: 2px solid #333;
											display: flex;
											align-items: center;
											justify-content: center;
											color: white;
											font-weight: bold;
										"
									>
										{disk}
									</div>
								{/each}
							</div>
						</div>
						
						<div style="text-align: center; margin-top: 20px; color: #666; font-weight: 600;">
							{towerLabel(index)}
						</div>
					</div>
				{/each}
			</div>
			
			{#if selectedTower !== null}
				<p style="color: #667eea; font-weight: 600; margin-top: 20px;">
					{selectedTowerMessage()}
				</p>
			{/if}
			
			{#if completed}
				<div style="margin-top: 30px; padding: 20px; background: #4caf50; color: white; border-radius: 8px;">
					<h3>{t('🎉 Puzzle Completed!')}</h3>
					<p>{t('Calculating results...')}</p>
				</div>
			{/if}
		</div>
	
	{:else if stage === 'results'}
		<div class="test-card">
			<h1>{t('Test Complete!')}</h1>
			
			{#if isTrainingMode}
				<div class="training-progress-banner">
					{#if sessionComplete}
						<div class="session-complete-msg">
							{lt('🎉 Session Complete! You\'ve finished all 4 tasks for this session.', '🎉 সেশন সম্পন্ন! আপনি এই সেশনের সব ৪টি টাস্ক শেষ করেছেন।')}
						</div>
					{:else}
						<div style="margin-bottom: 10px; color: #667eea; font-weight: 600;">
							{trainingProgressText()}
						</div>
						<div style="font-size: 14px; color: #666;">
							{t('Continue with the remaining tasks to complete this session')}
						</div>
					{/if}
				</div>
			{/if}
			
			<div class="score-display">
				{n(Math.max(0, 100 - ((moves - optimalMoves) * 10)).toFixed(0))}%
			</div>
			
			<div class="result-details">
				<p>
					<span>{t('Moves Taken:')}</span>
					<strong>{n(moves)}</strong>
				</p>
				<p>
					<span>{t('Optimal Moves:')}</span>
					<strong>{n(optimalMoves)}</strong>
				</p>
				<p>
					<span>{t('Excess Moves:')}</span>
					<strong>{n(moves - optimalMoves)}</strong>
				</p>
				<p>
					<span>{t('Planning Time:')}</span>
					<strong>{n((planningTime / 1000).toFixed(1), { minimumFractionDigits: 1, maximumFractionDigits: 1 })}{lt('s', 'সে')}</strong>
				</p>
				<p>
					<span>{t('Completed:')}</span>
					<strong>{completed ? t('Yes') : t('No')}</strong>
				</p>
			</div>
			
			<div style="margin-top: 30px; padding: 20px; background: #f5f5f5; border-radius: 8px;">
				<h4 style="color: #667eea; margin-bottom: 10px;">{t('Planning Insights:')}</h4>
				<p style="color: #666; line-height: 1.6;">
					{insightMessage()}
				</p>
				{#if planningTime > 30000}
					<p style="color: #ff9800; margin-top: 10px;">
						{t('💡 Tip: Long planning time detected. Sometimes thinking through the entire sequence helps!')}
					</p>
				{/if}
			</div>
			
			<div style="margin-top: 40px;">
				<button class="btn-primary" on:click={backToDashboard}>
					{t('Back to Dashboard')}
				</button>
			</div>
		</div>
	{/if}
</div>

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
	
	.tower {
		transition: all 0.2s;
	}
	
	.tower:hover {
		transform: translateY(-5px);
	}
	
	.tower.selected {
		background: rgba(102, 126, 234, 0.1);
		border-radius: 10px;
		padding: 10px;
		margin: -10px;
	}
</style>

<svelte:head>
	<title>{lt('Planning Test - NeuroBloom', 'পরিকল্পনা পরীক্ষা - NeuroBloom')}</title>
</svelte:head>

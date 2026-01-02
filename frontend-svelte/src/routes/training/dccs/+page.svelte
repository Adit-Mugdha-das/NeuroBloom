<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let phase = 'intro';
	let loading = false;
	let error = null;
	let sessionData = null;
	let difficulty = 1;
	let baselineFlexibility = null;
	let currentPhase = null;
	let currentPhaseIndex = 0; // 0=phase1, 1=phase2, 2=phase3
	let currentTrialIndex = 0;
	let responses = [];
	let startTime = null;
	let trialStartTime = null;
	let showCue = false;
	let cueText = '';
	let results = null;
	let newBadges = [];
	let currentUser = null;
	let taskId = null;

	const COLORS = {
		red: '#EF4444',
		blue: '#3B82F6'
	};

	// Subscribe to user store
	user.subscribe((value) => {
		currentUser = value;
	});

	async function loadSession() {
		try {
			loading = true;
			error = null;
			
			// Get user's baseline to determine appropriate difficulty
			const baselineResponse = await fetch(
				`http://localhost:8000/api/baseline/${currentUser.id}`
			);
			
			if (baselineResponse.ok) {
				const baselineData = await baselineResponse.json();
				baselineFlexibility = baselineData.flexibility;
				
				// Set difficulty based on baseline (1-10 scale)
				if (baselineFlexibility !== null) {
					if (baselineFlexibility >= 90) difficulty = 9;
					else if (baselineFlexibility >= 80) difficulty = 8;
					else if (baselineFlexibility >= 70) difficulty = 7;
					else if (baselineFlexibility >= 60) difficulty = 6;
					else if (baselineFlexibility >= 50) difficulty = 5;
					else if (baselineFlexibility >= 40) difficulty = 4;
					else if (baselineFlexibility >= 30) difficulty = 3;
					else if (baselineFlexibility >= 20) difficulty = 2;
					else difficulty = 1;
				}
			}
			
			const response = await fetch(
				`http://localhost:8000/api/tasks/dccs/generate?difficulty=${difficulty}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' }
				}
			);
			if (!response.ok) throw new Error('Failed to load session');
			sessionData = await response.json();
			
			// Update difficulty from session data
			difficulty = sessionData.difficulty;
		} catch (err) {
			error = err.message;
		} finally {
			loading = false;
		}
	}

	function startTask() {
		currentPhaseIndex = 0;
		currentTrialIndex = 0;
		responses = [];
		currentPhase = sessionData.phases.phase1;
		phase = 'task';
		startTime = Date.now();
		startTrial();
	}

	function startTrial() {
		trialStartTime = Date.now();
		const trial = getCurrentTrial();
		
		if (trial && trial.cue_shown) {
			// Show cue for mixed phase
			showCue = true;
			cueText = `Sort by ${trial.rule.toUpperCase()}`;
			
			// Hide cue after duration
			setTimeout(() => {
				showCue = false;
			}, sessionData.config.cue_duration_ms);
		}
	}

	function getCurrentTrial() {
		if (!currentPhase || currentTrialIndex >= currentPhase.trials.length) {
			return null;
		}
		return currentPhase.trials[currentTrialIndex];
	}

	function handleTargetSelection(targetId) {
		const responseTime = Date.now() - trialStartTime;
		const trial = getCurrentTrial();
		
		responses.push({
			trial_number: trial.trial_number,
			selected_target: targetId,
			reaction_time_ms: responseTime,
			phase: currentPhase.name,
			rule: trial.rule,
			is_switch_trial: trial.is_switch_trial || false
		});

		moveToNextTrial();
	}

	function moveToNextTrial() {
		currentTrialIndex++;
		
		// Check if current phase is complete
		if (currentTrialIndex >= currentPhase.trials.length) {
			// Move to next phase
			currentPhaseIndex++;
			
			if (currentPhaseIndex === 1) {
				currentPhase = sessionData.phases.phase2;
				currentTrialIndex = 0;
				phase = 'phase-transition';
			} else if (currentPhaseIndex === 2) {
				currentPhase = sessionData.phases.phase3;
				currentTrialIndex = 0;
				phase = 'phase-transition';
			} else {
				// All phases complete
				submitSession();
				return;
			}
		} else {
			// Continue current phase
			startTrial();
		}
	}

	function continueToNextPhase() {
		phase = 'task';
		startTrial();
	}

	async function submitSession() {
		try {
			loading = true;
			error = null;
			const totalTime = Date.now() - startTime;
			taskId = $page.url.searchParams.get('taskId');
			
			console.log('[DCCS] Submitting session:', {
				userId: currentUser?.id,
				taskId,
				responsesCount: responses.length
			});
			
			// Submit to training endpoint
			const submitResponse = await fetch(
				`http://localhost:8000/api/training/tasks/dccs/submit/${currentUser.id}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						session_data: sessionData,
						user_responses: responses,
						task_id: taskId
					})
				}
			);
			
			if (!submitResponse.ok) {
				const errorText = await submitResponse.text();
				console.error('[DCCS] Submit failed:', errorText);
				throw new Error(`Failed to submit result: ${submitResponse.status} ${errorText}`);
			}
			
			const submitData = await submitResponse.json();
			console.log('[DCCS] Submit successful:', submitData);
			results = submitData;
			newBadges = submitData.newly_earned_badges || [];
			phase = 'results';
		} catch (err) {
			console.error('[DCCS] Submit error:', err);
			error = err.message || 'Network error - please check if the backend server is running';
		} finally {
			loading = false;
		}
	}

	function renderCard(card, size = 80) {
		const color = COLORS[card.color] || '#999';
		const shape = card.shape;
		const scale = card.size === 'small' ? 0.7 : 1.0;
		
		if (shape === 'circle') {
			return `<svg width="${size}" height="${size}" viewBox="0 0 100 100">
				<circle cx="50" cy="50" r="${35 * scale}" fill="${color}" />
			</svg>`;
		} else if (shape === 'star') {
			return `<svg width="${size}" height="${size}" viewBox="0 0 100 100">
				<polygon points="50,${15 * (2 - scale)} ${40 * scale + 30},${35 * (2 - scale)} ${20 * scale + 40},${35 * (2 - scale)} ${30 * scale + 35},${55 * (2 - scale)} ${20 * scale + 40},${75 * (2 - scale)} 50,${60 * (2 - scale)} ${60 * scale + 20},${75 * (2 - scale)} ${50 * scale + 25},${55 * (2 - scale)} ${60 * scale + 20},${35 * (2 - scale)}" fill="${color}" />
			</svg>`;
		}
		return '';
	}

	onMount(async () => {
		if (!currentUser) {
			goto('/login');
			return;
		}
		await loadSession();
	});
</script>

<div style="min-height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px;">
	<div style="background: white; padding: 30px; border-radius: 10px; margin: 0 auto; max-width: 1000px;">
		<h1 style="font-size: 28px; font-weight: bold; margin-bottom: 20px; color: #333;">
			Dimensional Change Card Sort (DCCS)
		</h1>

		{#if loading}
			<div style="text-align: center; padding: 40px;">
				<p style="font-size: 18px; color: #666;">Loading...</p>
			</div>
		{:else if error}
			<div style="background: #fee; border: 2px solid #fcc; padding: 20px; border-radius: 8px;">
				<p style="color: #c33; margin-bottom: 10px;">Error: {error}</p>
				<button on:click={loadSession} style="padding: 10px 20px; background: #c33; color: white; border: none; border-radius: 5px; cursor: pointer;">
					Retry
				</button>
			</div>
		{:else if phase === 'intro'}
			<div>
				<h2 style="font-size: 24px; font-weight: 600; margin-bottom: 15px; color: #333;">
					Cognitive Flexibility Assessment
				</h2>
				
				<p style="font-size: 16px; color: #555; margin-bottom: 15px;">
					The Dimensional Change Card Sort (DCCS) measures your ability to:
				</p>
				
				<ul style="margin-left: 30px; margin-bottom: 20px; color: #555;">
					<li style="margin-bottom: 8px;">Switch between different sorting rules</li>
					<li style="margin-bottom: 8px;">Adapt to changing task demands</li>
					<li style="margin-bottom: 8px;">Maintain focus during rule changes</li>
					<li style="margin-bottom: 8px;">Inhibit previous responses</li>
				</ul>

				<div style="background: #f0f9ff; border-left: 4px solid #3b82f6; padding: 15px; margin-bottom: 20px;">
					<h3 style="font-size: 18px; font-weight: 600; margin-bottom: 10px; color: #1e40af;">
						How It Works
					</h3>
					<p style="font-size: 14px; color: #555; margin-bottom: 8px;">
						<strong>Phase 1:</strong> Sort cards by COLOR (e.g., red cards go to one pile, blue to another)
					</p>
					<p style="font-size: 14px; color: #555; margin-bottom: 8px;">
						<strong>Phase 2:</strong> Sort cards by SHAPE (e.g., circles go to one pile, stars to another)
					</p>
					<p style="font-size: 14px; color: #555;">
						<strong>Phase 3:</strong> Mixed sorting - a cue will tell you which rule to use on each trial
					</p>
				</div>

				<div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin-bottom: 20px;">
					<h3 style="font-size: 18px; font-weight: 600; margin-bottom: 10px; color: #92400e;">
						Instructions
					</h3>
					<ul style="margin-left: 20px; color: #555;">
						<li style="margin-bottom: 8px;">Click on the target card that matches the test card</li>
						<li style="margin-bottom: 8px;">In Phase 3, pay attention to the cue shown before each card</li>
						<li style="margin-bottom: 8px;">Work as quickly and accurately as possible</li>
						<li style="margin-bottom: 8px;">Total trials: {sessionData ? sessionData.total_trials : '40'}</li>
					</ul>
				</div>

				<div style="background: #e0f2fe; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
					<p style="font-size: 14px; color: #0c4a6e; margin-bottom: 8px;">
						<strong>Current Difficulty:</strong> Level {difficulty} / 10
					</p>
					<p style="font-size: 13px; color: #0369a1;">
						{#if difficulty <= 4}
							Basic: Color & Shape sorting, {sessionData?.config.cue_duration_ms || 1500}ms cues
						{:else if difficulty <= 7}
							Intermediate: Added size dimension, {sessionData?.config.cue_duration_ms || 800}ms cues
						{:else}
							Advanced: All dimensions, rapid {sessionData?.config.cue_duration_ms || 400}ms cues
						{/if}
					</p>
					{#if baselineFlexibility !== null && baselineFlexibility !== undefined}
						<p style="font-size: 12px; color: #0369a1; margin-top: 8px;">
							Based on your flexibility baseline: {baselineFlexibility.toFixed(0)}/100
						</p>
					{/if}
				</div>

				<button 
					on:click={startTask} 
					style="padding: 15px 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; font-size: 18px; font-weight: 600; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
					Start Test
				</button>
			</div>
		{:else if phase === 'phase-transition'}
			<div style="text-align: center; padding: 40px;">
				<h2 style="font-size: 24px; font-weight: 600; margin-bottom: 20px; color: #333;">
					{#if currentPhaseIndex === 1}
						Phase 2: Sort by Shape
					{:else if currentPhaseIndex === 2}
						Phase 3: Mixed Sorting
					{/if}
				</h2>
				
				<p style="font-size: 16px; color: #555; margin-bottom: 30px;">
					{#if currentPhaseIndex === 1}
						Now switch to sorting by <strong>SHAPE</strong> instead of color.<br/>
						Circles go to one pile, stars to the other.
					{:else if currentPhaseIndex === 2}
						In this phase, a <strong>CUE</strong> will tell you which rule to use.<br/>
						Pay attention to whether it says "COLOR" or "SHAPE".
					{/if}
				</p>

				<button 
					on:click={continueToNextPhase} 
					style="padding: 15px 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; font-size: 18px; font-weight: 600; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
					Continue
				</button>
			</div>
		{:else if phase === 'task'}
			{#if currentPhase && getCurrentTrial()}
				{@const trial = getCurrentTrial()}
				{@const phaseNum = currentPhaseIndex + 1}
				{@const totalTrials = currentPhase.total_trials}
				{@const trialNum = currentTrialIndex + 1}

				<div>
					<!-- Progress -->
					<div style="background: #f3f4f6; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
						<div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
							<span style="font-size: 14px; color: #666;">Phase {phaseNum} of 3</span>
							<span style="font-size: 14px; color: #666;">Trial {trialNum} / {totalTrials}</span>
						</div>
						<div style="background: #e5e7eb; height: 8px; border-radius: 4px; overflow: hidden;">
							<div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); height: 100%; width: {(trialNum / totalTrials) * 100}%; transition: width 0.3s;"></div>
						</div>
					</div>

					<!-- Current Rule Instruction -->
					<div style="text-align: center; margin-bottom: 30px;">
						<h2 style="font-size: 22px; font-weight: 600; color: #333; margin-bottom: 10px;">
							{currentPhase.instruction}
						</h2>
						{#if showCue}
							<div style="background: #fef3c7; border: 3px solid #f59e0b; padding: 15px 30px; border-radius: 8px; display: inline-block; animation: pulse 0.5s;">
								<p style="font-size: 24px; font-weight: bold; color: #92400e; margin: 0;">
									{cueText}
								</p>
							</div>
						{/if}
					</div>

					<!-- Test Card -->
					<div style="text-align: center; margin-bottom: 40px;">
						<p style="font-size: 16px; color: #666; margin-bottom: 15px;">Which target matches this card?</p>
						<div style="display: inline-block; padding: 20px; background: #f9fafb; border: 2px solid #d1d5db; border-radius: 10px;">
							{@html renderCard(trial.card, 100)}
							{#if sessionData.config.use_size_dimension && trial.card.size}
								<p style="font-size: 14px; color: #666; margin-top: 10px;">
									Size: {trial.card.size}
								</p>
							{/if}
						</div>
					</div>

					<!-- Target Cards -->
					<div style="text-align: center;">
						<p style="font-size: 16px; color: #666; margin-bottom: 15px; font-weight: 600;">
							Click a target:
						</p>
						<div style="display: flex; justify-content: center; gap: 40px;">
							{#each sessionData.target_cards as target}
								<button
									on:click={() => handleTargetSelection(target.id)}
								on:mouseenter={(e) => { e.currentTarget.style.borderColor='#667eea'; e.currentTarget.style.transform='scale(1.05)'; }}
								on:mouseleave={(e) => { e.currentTarget.style.borderColor='#d1d5db'; e.currentTarget.style.transform='scale(1)'; }}
								style="padding: 20px; background: white; border: 3px solid #d1d5db; border-radius: 10px; cursor: pointer; transition: all 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
									{@html renderCard(target, 100)}
									{#if sessionData.config.use_size_dimension && target.size}
										<p style="font-size: 14px; color: #666; margin-top: 10px;">
											Size: {target.size}
										</p>
									{/if}
								</button>
							{/each}
						</div>
					</div>
				</div>
			{/if}
		{:else if phase === 'results'}
			<div>
				<h2 style="font-size: 24px; font-weight: 600; margin-bottom: 20px; color: #333;">
					Test Complete!
				</h2>

				<!-- Overall Score -->
				<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; margin-bottom: 30px; text-align: center;">
					<p style="color: white; font-size: 18px; margin-bottom: 10px;">Your Score</p>
					<p style="color: white; font-size: 48px; font-weight: bold; margin: 0;">
						{results.score}
					</p>
					<p style="color: rgba(255,255,255,0.9); font-size: 16px; margin-top: 10px;">
						Accuracy: {(results.accuracy * 100).toFixed(1)}%
					</p>
				</div>

				<!-- Phase Results -->
				<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px;">
					<div style="background: #f0f9ff; padding: 20px; border-radius: 8px; border-left: 4px solid #3b82f6;">
						<h3 style="font-size: 16px; font-weight: 600; color: #1e40af; margin-bottom: 10px;">
							Phase 1: Pre-Switch
						</h3>
						<p style="font-size: 14px; color: #555; margin-bottom: 5px;">
							Accuracy: {(results.phases.phase1.accuracy * 100).toFixed(1)}%
						</p>
						<p style="font-size: 14px; color: #555;">
							Avg RT: {results.phases.phase1.mean_rt.toFixed(0)}ms
						</p>
					</div>

					<div style="background: #f0fdf4; padding: 20px; border-radius: 8px; border-left: 4px solid #10b981;">
						<h3 style="font-size: 16px; font-weight: 600; color: #065f46; margin-bottom: 10px;">
							Phase 2: Post-Switch
						</h3>
						<p style="font-size: 14px; color: #555; margin-bottom: 5px;">
							Accuracy: {(results.phases.phase2.accuracy * 100).toFixed(1)}%
						</p>
						<p style="font-size: 14px; color: #555;">
							Avg RT: {results.phases.phase2.mean_rt.toFixed(0)}ms
						</p>
					</div>

					<div style="background: #fef3c7; padding: 20px; border-radius: 8px; border-left: 4px solid #f59e0b;">
						<h3 style="font-size: 16px; font-weight: 600; color: #92400e; margin-bottom: 10px;">
							Phase 3: Mixed
						</h3>
						<p style="font-size: 14px; color: #555; margin-bottom: 5px;">
							Accuracy: {(results.phases.phase3.accuracy * 100).toFixed(1)}%
						</p>
						<p style="font-size: 14px; color: #555;">
							Avg RT: {results.phases.phase3.mean_rt.toFixed(0)}ms
						</p>
					</div>
				</div>

				<!-- Key Metrics -->
				<div style="background: #f9fafb; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
					<h3 style="font-size: 18px; font-weight: 600; color: #333; margin-bottom: 15px;">
						Key Metrics
					</h3>
					<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
						<div>
							<p style="font-size: 14px; color: #666; margin-bottom: 5px;">Switch Cost</p>
							<p style="font-size: 20px; font-weight: 600; color: #667eea;">
								{results.switch_cost >= 0 ? '+' : ''}{results.switch_cost.toFixed(0)}ms
							</p>
							<p style="font-size: 12px; color: #888;">
								Time penalty for switching rules
							</p>
						</div>
						<div>
							<p style="font-size: 14px; color: #666; margin-bottom: 5px;">Perseverative Errors</p>
							<p style="font-size: 20px; font-weight: 600; color: #f59e0b;">
								{results.perseverative_errors}
							</p>
							<p style="font-size: 12px; color: #888;">
								Times you used the old rule
							</p>
						</div>
					</div>
				</div>

				<!-- Actions -->
				<div style="display: flex; gap: 15px;">
					<button 
						on:click={() => goto('/dashboard')} 
						style="flex: 1; padding: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer;">
						Return to Dashboard
					</button>
					<button 
						on:click={() => goto('/training')} 
						style="flex: 1; padding: 15px; background: white; color: #667eea; border: 2px solid #667eea; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer;">
						Next Task
					</button>
				</div>
			</div>
		{/if}
	</div>
</div>

{#if newBadges && newBadges.length > 0}
	<BadgeNotification badges={newBadges} />
{/if}

<style>
	@keyframes pulse {
		0%, 100% { transform: scale(1); }
		50% { transform: scale(1.05); }
	}
</style>

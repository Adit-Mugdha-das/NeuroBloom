<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import { formatNumber, formatPercent, locale, translateText } from '$lib/i18n';
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

	function t(text) {
		return translateText(text, $locale);
	}

	function n(value, options = {}) {
		return formatNumber(value, $locale, options);
	}

	function pct(value, options = {}) {
		return formatPercent(value, $locale, options);
	}

	function accuracyLabel(value) {
		return pct(Number(value) || 0, { minimumFractionDigits: 1, maximumFractionDigits: 1 });
	}

	function durationMsLabel(value) {
		const roundedValue = Number.isFinite(Number(value)) ? Math.round(Number(value)) : 0;
		return $locale === 'bn' ? `${n(roundedValue)} মি.সে.` : `${roundedValue}ms`;
	}

	function signedDurationLabel(value) {
		const roundedValue = Number.isFinite(Number(value)) ? Math.round(Number(value)) : 0;
		const prefix = roundedValue >= 0 ? '+' : '';
		return $locale === 'bn'
			? `${prefix}${n(roundedValue)} মি.সে.`
			: `${prefix}${roundedValue}ms`;
	}

	function levelLabel(value = difficulty, max = 10) {
		return $locale === 'bn' ? `লেভেল ${n(value)} / ${n(max)}` : `Level ${value} / ${max}`;
	}

	function ruleName(rule) {
		if (rule === 'color') return $locale === 'bn' ? 'রঙ' : 'COLOR';
		if (rule === 'shape') return $locale === 'bn' ? 'আকৃতি' : 'SHAPE';
		if (rule === 'size') return $locale === 'bn' ? 'আকার' : 'SIZE';
		if (rule === 'varies') return $locale === 'bn' ? 'পরিবর্তিত হবে' : 'VARIES';
		return t(rule || '');
	}

	function sizeLabel(size) {
		if (size === 'small') return $locale === 'bn' ? 'ছোট' : 'small';
		if (size === 'large') return $locale === 'bn' ? 'বড়' : 'large';
		return t(size || '');
	}

	function cueInstruction(rule) {
		if ($locale === 'bn') {
			return `${ruleName(rule)} অনুযায়ী সাজান`;
		}
		return `Sort by ${ruleName(rule)}`;
	}

	function phaseRule(index) {
		if (index === 1) return sessionData?.config?.phase1_dimension || 'color';
		if (index === 2) return sessionData?.config?.phase2_dimension || 'shape';
		return 'varies';
	}

	function ruleExample(rule) {
		if ($locale === 'bn') {
			if (rule === 'color') return 'লাল কার্ড এক স্তূপে যাবে, নীল অন্য স্তূপে';
			if (rule === 'shape') return 'বৃত্ত এক স্তূপে যাবে, তারা অন্য স্তূপে';
			if (rule === 'size') return 'বড় কার্ড এক স্তূপে যাবে, ছোট অন্য স্তূপে';
			return '';
		}

		if (rule === 'color') return 'red cards go to one pile, blue to another';
		if (rule === 'shape') return 'circles go to one pile, stars to another';
		if (rule === 'size') return 'large cards go to one pile, small to another';
		return '';
	}

	function phaseOverview(index) {
		const rule = phaseRule(index);
		if ($locale === 'bn') {
			return `${cueInstruction(rule)} (${ruleExample(rule)})`;
		}
		return `${cueInstruction(rule)} (e.g., ${ruleExample(rule)})`;
	}

	function phaseInstructionLabel(phaseData = currentPhase) {
		if (!phaseData) return '';
		if (phaseData.name === 'mixed') {
			return t('Follow the cue on each trial');
		}
		return cueInstruction(phaseData.rule);
	}

	function phaseTitle(value) {
		const phaseNumber = Number(value);
		if (phaseNumber === 1) return $locale === 'bn' ? `ধাপ ${n(1)}: ${cueInstruction(phaseRule(1))}` : `Phase 1: ${cueInstruction(phaseRule(1))}`;
		if (phaseNumber === 2) return $locale === 'bn' ? `ধাপ ${n(2)}: ${cueInstruction(phaseRule(2))}` : `Phase 2: ${cueInstruction(phaseRule(2))}`;
		if (phaseNumber === 3) return t('Phase 3: Mixed Sorting');
		return $locale === 'bn' ? `ধাপ ${n(phaseNumber)}` : `Phase ${phaseNumber}`;
	}

	function phaseProgressLabel(current, total) {
		return $locale === 'bn' ? `ধাপ ${n(current)} / ${n(total)}` : `Phase ${current} of ${total}`;
	}

	function trialProgressLabel(current, total) {
		return $locale === 'bn' ? `ট্রায়াল ${n(current)} / ${n(total)}` : `Trial ${current} / ${total}`;
	}

	function difficultyDescription() {
		const cueDuration = sessionData?.config?.cue_duration_ms || 0;
		if ($locale === 'bn') {
			if (difficulty <= 4) {
				return `প্রাথমিক স্তর: রঙ ও আকৃতি অনুযায়ী সাজানো, ${durationMsLabel(cueDuration)} সংকেত`;
			}
			if (difficulty <= 7) {
				return `মধ্যম স্তর: আকারের মাত্রা যোগ হয়েছে, ${durationMsLabel(cueDuration)} সংকেত`;
			}
			return `উন্নত স্তর: সব মাত্রা সক্রিয়, দ্রুত ${durationMsLabel(cueDuration)} সংকেত`;
		}

		if (difficulty <= 4) {
			return `Basic: Color & Shape sorting, ${cueDuration}ms cues`;
		}
		if (difficulty <= 7) {
			return `Intermediate: Added size dimension, ${cueDuration}ms cues`;
		}
		return `Advanced: All dimensions, rapid ${cueDuration}ms cues`;
	}

	function transitionMessage() {
		if (currentPhaseIndex === 1) {
			if ($locale === 'bn') {
				return `এখন ${ruleName(phaseRule(1))} নয়, ${ruleName(phaseRule(2))} অনুযায়ী সাজান। ${ruleExample(phaseRule(2))}।`;
			}
			return `Now switch to ${cueInstruction(phaseRule(2)).toLowerCase()} instead of ${ruleName(phaseRule(1)).toLowerCase()}. ${ruleExample(phaseRule(2))[0].toUpperCase()}${ruleExample(phaseRule(2)).slice(1)}.`;
		}

		if (currentPhaseIndex === 2) {
			if ($locale === 'bn') {
				return `এবার প্রতিটি ট্রায়ালের আগে দেখানো সংকেত লক্ষ্য করুন। সেখানে ${ruleName(phaseRule(1))} নাকি ${ruleName(phaseRule(2))} অনুযায়ী সাজাতে হবে, তা বলা থাকবে।`;
			}
			return `In this phase, a cue will tell you which rule to use. Pay attention to whether it says "${ruleName(phaseRule(1))}" or "${ruleName(phaseRule(2))}".`;
		}

		return '';
	}

	async function loadSession() {
		try {
			loading = true;
			error = null;
			
			// Check if difficulty is provided via URL (dev tool override)
			const urlDifficulty = $page.url.searchParams.get('difficulty');
			if (urlDifficulty) {
				difficulty = parseInt(urlDifficulty);
				console.log('🔧 DCCS - Using URL difficulty:', difficulty);
			} else {
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
					console.log('📊 DCCS - Using baseline difficulty:', difficulty);
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
			console.log('✅ DCCS - Final difficulty loaded:', difficulty);
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
			cueText = cueInstruction(trial.rule);
			
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

<div data-localize-skip style="min-height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px;">
	<div style="background: white; padding: 30px; border-radius: 10px; margin: 0 auto; max-width: 1000px;">
		<div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 20px;">
			<h1 style="font-size: 28px; font-weight: bold; margin: 0; color: #333;">
				{t('Dimensional Change Card Sort (DCCS)')}
			</h1>
			<DifficultyBadge difficulty={5} domain="Cognitive Flexibility" />
		</div>

		{#if loading}
			<div style="text-align: center; padding: 40px;">
				<p style="font-size: 18px; color: #666;">{t('Loading...')}</p>
			</div>
		{:else if error}
			<div style="background: #fee; border: 2px solid #fcc; padding: 20px; border-radius: 8px;">
				<p style="color: #c33; margin-bottom: 10px;">{t('Error:')} {error}</p>
				<button on:click={loadSession} style="padding: 10px 20px; background: #c33; color: white; border: none; border-radius: 5px; cursor: pointer;">
					{t('Retry')}
				</button>
			</div>
		{:else if phase === 'intro'}
			<div>
				<h2 style="font-size: 24px; font-weight: 600; margin-bottom: 15px; color: #333;">
					{t('Cognitive Flexibility Assessment')}
				</h2>
				
				<p style="font-size: 16px; color: #555; margin-bottom: 15px;">
					{t('The Dimensional Change Card Sort (DCCS) measures your ability to:')}
				</p>
				
				<ul style="margin-left: 30px; margin-bottom: 20px; color: #555;">
					<li style="margin-bottom: 8px;">{t('Switch between different sorting rules')}</li>
					<li style="margin-bottom: 8px;">{t('Adapt to changing task demands')}</li>
					<li style="margin-bottom: 8px;">{t('Maintain focus during rule changes')}</li>
					<li style="margin-bottom: 8px;">{t('Inhibit previous responses')}</li>
				</ul>

				<div style="background: #f0f9ff; border-left: 4px solid #3b82f6; padding: 15px; margin-bottom: 20px;">
					<h3 style="font-size: 18px; font-weight: 600; margin-bottom: 10px; color: #1e40af;">
						{t('How It Works')}
					</h3>
					<p style="font-size: 14px; color: #555; margin-bottom: 8px;">
						<strong>{t('Phase')} {n(1)}:</strong> {phaseOverview(1)}
					</p>
					<p style="font-size: 14px; color: #555; margin-bottom: 8px;">
						<strong>{t('Phase')} {n(2)}:</strong> {phaseOverview(2)}
					</p>
					<p style="font-size: 14px; color: #555;">
						<strong>{t('Phase')} {n(3)}:</strong>
						{$locale === 'bn'
							? `মিশ্র বাছাই - প্রতিটি ট্রায়ালে সংকেত বলে দেবে ${ruleName(phaseRule(1))} নাকি ${ruleName(phaseRule(2))} অনুযায়ী সাজাতে হবে`
							: `Mixed sorting - a cue will tell you whether to sort by ${ruleName(phaseRule(1)).toLowerCase()} or ${ruleName(phaseRule(2)).toLowerCase()}`}
					</p>
				</div>

				<div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin-bottom: 20px;">
					<h3 style="font-size: 18px; font-weight: 600; margin-bottom: 10px; color: #92400e;">
						{t('Instructions')}
					</h3>
					<ul style="margin-left: 20px; color: #555;">
						<li style="margin-bottom: 8px;">{t('Click on the target card that matches the test card')}</li>
						<li style="margin-bottom: 8px;">{t('In Phase 3, pay attention to the cue shown before each card')}</li>
						<li style="margin-bottom: 8px;">{t('Work as quickly and accurately as possible')}</li>
						<li style="margin-bottom: 8px;">{t('Total Trials:')} {n(sessionData ? sessionData.total_trials : 40)}</li>
					</ul>
				</div>

				<div style="background: #e0f2fe; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
					<p style="font-size: 14px; color: #0c4a6e; margin-bottom: 8px;">
						<strong>{t('Current Difficulty:')}</strong> {levelLabel()}
					</p>
					<p style="font-size: 13px; color: #0369a1;">
						{difficultyDescription()}
					</p>
					{#if baselineFlexibility !== null && baselineFlexibility !== undefined}
						<p style="font-size: 12px; color: #0369a1; margin-top: 8px;">
							{$locale === 'bn'
								? `আপনার ফ্লেক্সিবিলিটি বেসলাইন: ${n(baselineFlexibility.toFixed(0))}/${n(100)}`
								: `Based on your flexibility baseline: ${baselineFlexibility.toFixed(0)}/100`}
						</p>
					{/if}
				</div>

				<button 
					on:click={startTask} 
					style="padding: 15px 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; font-size: 18px; font-weight: 600; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
					{t('Start Test')}
				</button>
			</div>
		{:else if phase === 'phase-transition'}
			<div style="text-align: center; padding: 40px;">
				<h2 style="font-size: 24px; font-weight: 600; margin-bottom: 20px; color: #333;">
					{phaseTitle(currentPhaseIndex + 1)}
				</h2>
				
				<p style="font-size: 16px; color: #555; margin-bottom: 30px;">
					{transitionMessage()}
				</p>

				<button 
					on:click={continueToNextPhase} 
					style="padding: 15px 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; font-size: 18px; font-weight: 600; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
					{t('Continue')}
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
							<span style="font-size: 14px; color: #666;">{phaseProgressLabel(phaseNum, 3)}</span>
							<span style="font-size: 14px; color: #666;">{trialProgressLabel(trialNum, totalTrials)}</span>
						</div>
						<div style="background: #e5e7eb; height: 8px; border-radius: 4px; overflow: hidden;">
							<div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); height: 100%; width: {(trialNum / totalTrials) * 100}%; transition: width 0.3s;"></div>
						</div>
					</div>

					<!-- Current Rule Instruction -->
					<div style="text-align: center; margin-bottom: 30px;">
						<h2 style="font-size: 22px; font-weight: 600; color: #333; margin-bottom: 10px;">
							{phaseInstructionLabel(currentPhase)}
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
						<p style="font-size: 16px; color: #666; margin-bottom: 15px;">{t('Which target matches this card?')}</p>
						<div style="display: inline-block; padding: 20px; background: #f9fafb; border: 2px solid #d1d5db; border-radius: 10px;">
							{@html renderCard(trial.card, 100)}
							{#if sessionData.config.use_size_dimension && trial.card.size}
								<p style="font-size: 14px; color: #666; margin-top: 10px;">
									{$locale === 'bn' ? `আকার: ${sizeLabel(trial.card.size)}` : `Size: ${sizeLabel(trial.card.size)}`}
								</p>
							{/if}
						</div>
					</div>

					<!-- Target Cards -->
					<div style="text-align: center;">
						<p style="font-size: 16px; color: #666; margin-bottom: 15px; font-weight: 600;">
							{t('Click a target:')}
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
											{$locale === 'bn' ? `আকার: ${sizeLabel(target.size)}` : `Size: ${sizeLabel(target.size)}`}
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
					{t('Test Complete!')}
				</h2>

				<!-- Overall Score -->
				<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; margin-bottom: 30px; text-align: center;">
					<p style="color: white; font-size: 18px; margin-bottom: 10px;">{t('Your Score')}</p>
					<p style="color: white; font-size: 48px; font-weight: bold; margin: 0;">
						{n(results.score)}
					</p>
					<p style="color: rgba(255,255,255,0.9); font-size: 16px; margin-top: 10px;">
					{t('Accuracy')}: {accuracyLabel(results.accuracy)}
					</p>
				</div>

				<!-- Phase Results -->
			{#if results.phases}
			<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px;">
				{#if results.phases.phase1}
				<div style="background: #f0f9ff; padding: 20px; border-radius: 8px; border-left: 4px solid #3b82f6;">
					<h3 style="font-size: 16px; font-weight: 600; color: #1e40af; margin-bottom: 10px;">
						{t('Phase 1: Pre-Switch')}
					</h3>
					<p style="font-size: 14px; color: #555; margin-bottom: 5px;">
						{t('Accuracy')}: {accuracyLabel(results.phases.phase1.accuracy)}
					</p>
					<p style="font-size: 14px; color: #555;">
						{t('Avg RT:')} {durationMsLabel(results.phases.phase1.mean_rt)}
					</p>
				</div>
				{/if}
{#if results.phases.phase2}
				<div style="background: #f0fdf4; padding: 20px; border-radius: 8px; border-left: 4px solid #10b981;">
					<h3 style="font-size: 16px; font-weight: 600; color: #065f46; margin-bottom: 10px;">
						{t('Phase 2: Post-Switch')}
					</h3>
					<p style="font-size: 14px; color: #555; margin-bottom: 5px;">
						{t('Accuracy')}: {accuracyLabel(results.phases.phase2.accuracy)}
					</p>
					<p style="font-size: 14px; color: #555;">
						{t('Avg RT:')} {durationMsLabel(results.phases.phase2.mean_rt)}
					</p>
				</div>
				{/if}

{#if results.phases.phase3}
				<div style="background: #fef3c7; padding: 20px; border-radius: 8px; border-left: 4px solid #f59e0b;">
					<h3 style="font-size: 16px; font-weight: 600; color: #92400e; margin-bottom: 10px;">
						{t('Phase 3: Mixed')}
					</h3>
					<p style="font-size: 14px; color: #555; margin-bottom: 5px;">
						{t('Accuracy')}: {accuracyLabel(results.phases.phase3.accuracy)}
					</p>
					<p style="font-size: 14px; color: #555;">
						{t('Avg RT:')} {durationMsLabel(results.phases.phase3.mean_rt)}
					</p>
				</div>
				{/if}
			</div>
			{/if}

				<!-- Key Metrics -->
			{#if results.switch_cost !== undefined}
			<div style="background: #f9fafb; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
				<h3 style="font-size: 18px; font-weight: 600; color: #333; margin-bottom: 15px;">
					{t('Key Metrics')}
				</h3>
				<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
					<div>
						<p style="font-size: 14px; color: #666; margin-bottom: 5px;">{t('Switch Cost')}</p>
						<p style="font-size: 20px; font-weight: 600; color: #667eea;">
							{signedDurationLabel(results.switch_cost)}
						</p>
						<p style="font-size: 12px; color: #888;">
							{t('Time penalty for switching rules')}
						</p>
					</div>
					<div>
						<p style="font-size: 14px; color: #666; margin-bottom: 5px;">{t('Perseverative Errors')}</p>
						<p style="font-size: 20px; font-weight: 600; color: #f59e0b;">
							{n(results.perseverative_errors || 0)}
						</p>
						<p style="font-size: 12px; color: #888;">
							{t('Times you used the old rule')}
						</p>
					</div>
				</div>
			</div>
			{/if}
				<!-- Actions -->
				<div style="display: flex; gap: 15px;">
					<button 
						on:click={() => goto('/dashboard')} 
						style="flex: 1; padding: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer;">
						{t('Return to Dashboard')}
					</button>
					<button 
						on:click={() => goto('/training')} 
						style="flex: 1; padding: 15px; background: white; color: #667eea; border: 2px solid #667eea; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer;">
						{t('Next Task')}
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

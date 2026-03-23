<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import { formatNumber, locale, localeText, translateText } from '$lib/i18n';
	import { user } from '$lib/stores';
	import { onMount, onDestroy } from 'svelte';

	let phase = 'intro';
	let loading = false;
	let error = null;
	let sessionData = null;
	let difficulty = 1;
	let baselineFlexibility = null;
	let currentBlock = null;
	let currentBlockIndex = 0; // 0=block_a, 1=block_b, 2=block_c
	let currentTrialIndex = 0;
	let responses = [];
	let startTime = null;
	let elapsedTime = 0; // Add elapsed time tracking
	let timerInterval = null; // Timer interval reference
	let trialStartTime = null;
	let showCue = false;
	let cueText = '';
	let userAnswer = '';
	let results = null;
	let newBadges = [];
	let currentUser = null;
	let taskId = null;

	function t(text) {
		return translateText(text ?? '', $locale);
	}

	function lt(en, bn) {
		return localeText({ en, bn }, $locale);
	}

	function n(value, options = {}) {
		return formatNumber(value, $locale, options);
	}

	function difficultySummary() {
		if (difficulty <= 3) {
			return lt(
				'Single digit numbers, clear cues (2 seconds)',
				'এক অঙ্কের সংখ্যা, স্পষ্ট সংকেত (২ সেকেন্ড)'
			);
		}

		if (difficulty <= 6) {
			return lt(
				'Two digit numbers, subtle cues (1 second)',
				'দুই অঙ্কের সংখ্যা, সূক্ষ্ম সংকেত (১ সেকেন্ড)'
			);
		}

		return lt(
			'Three digit numbers, minimal cues (fast pace)',
			'তিন অঙ্কের সংখ্যা, খুব সংক্ষিপ্ত সংকেত (দ্রুত গতি)'
		);
	}

	function blockTransitionTitle() {
		if (currentBlockIndex === 1) {
			return lt('Block B: Subtract 3', 'ব্লক B: ৩ বিয়োগ করুন');
		}

		if (currentBlockIndex === 2) {
			return lt('Block C: Alternating', 'ব্লক C: পালাবদল');
		}

		return '';
	}

	function blockTransitionMessage() {
		if (currentBlockIndex === 1) {
			return lt(
				'Now SUBTRACT 3 from each number.\nKeep working as fast and accurately as you can.',
				'এখন প্রতিটি সংখ্যা থেকে ৩ বিয়োগ করুন।\nযত দ্রুত এবং নির্ভুলভাবে পারেন কাজ চালিয়ে যান।'
			);
		}

		return lt(
			"In this final block, you'll ALTERNATE between adding and subtracting.\nPay attention to the cue that tells you which operation to perform.",
			'এই শেষ ব্লকে কখনো যোগ, কখনো বিয়োগ করতে হবে।\nকোন কাজটি করতে হবে তা বোঝাতে যে সংকেত দেখাবে, সেটিতে মনোযোগ দিন।'
		);
	}

	function currentBlockLabel(blockNum) {
		return lt(
			`Block ${blockNum} of 3: ${t(currentBlock?.instruction || '')}`,
			`৩টির মধ্যে ব্লক ${n(blockNum)}: ${t(currentBlock?.instruction || '')}`
		);
	}

	function trialProgressLabel(current, total) {
		return lt(`Trial ${current} / ${total}`, `ট্রায়াল ${n(current)} / ${n(total)}`);
	}


	// Subscribe to user store
	user.subscribe((value) => {
		currentUser = value;
	});

	async function loadSession() {
		try {
			loading = true;
			error = null;
			
			// First get user's baseline to determine appropriate difficulty
			const baselineResponse = await fetch(
				`http://localhost:8000/api/baseline/${currentUser.id}`
			);
			
			if (baselineResponse.ok) {
				const baselineData = await baselineResponse.json();
				baselineFlexibility = baselineData.flexibility;
				
				// Set difficulty based on baseline (1-10 scale)
				// Map baseline score (0-100) to difficulty (1-10)
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
			
			// Generate session with appropriate difficulty
			const response = await fetch(
				`http://localhost:8000/api/tasks/plus-minus/generate?difficulty=${difficulty}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' }
				}
			);
			if (!response.ok) throw new Error('Failed to load session');
			sessionData = await response.json();
			
			// Update difficulty from session data (in case it was adjusted)
			difficulty = sessionData.difficulty;
		} catch (err) {
			error = err.message;
		} finally {
			loading = false;
		}
	}

	function startTask() {
		currentBlockIndex = 0;
		currentTrialIndex = 0;
		responses = [];
		currentBlock = sessionData.blocks.block_a;
		phase = 'task';
		startTime = Date.now();
		elapsedTime = 0;

		// Start timer to update elapsed time
		timerInterval = setInterval(() => {
			elapsedTime = (Date.now() - startTime) / 1000;
		}, 100); // Update every 100ms for smooth display

		startTrial();
	}

	function startTrial() {
		trialStartTime = Date.now();
		userAnswer = '';
		const trial = getCurrentTrial();
		
		if (trial && currentBlock.name === 'alternating') {
			// Show cue for alternating block
			showCue = true;
			cueText = trial.operation === 'add' ? '+3' : '-3';
			
			// Hide cue after duration
			setTimeout(() => {
				showCue = false;
			}, sessionData.config.cue_duration_ms);
		}
	}

	function getCurrentTrial() {
		if (!currentBlock || currentTrialIndex >= currentBlock.trials.length) {
			return null;
		}
		return currentBlock.trials[currentTrialIndex];
	}

	function handleSubmit() {
		const trial = getCurrentTrial();
		if (!trial || userAnswer === '') return;
		
		const responseTime = Date.now() - trialStartTime;
		const answer = parseInt(userAnswer);
		
		// Validate that the answer is a valid number
		if (isNaN(answer)) {
			// Invalid input - clear the field and don't record response
			userAnswer = '';
			return;
		}

		responses.push({
			trial_number: trial.trial_number,
			user_answer: answer,
			correct_answer: trial.correct_answer,
			reaction_time_ms: responseTime,
			block: currentBlock.name,
			operation: trial.operation,
			is_switch: trial.is_switch || false
		});

		moveToNextTrial();
	}

	function handleKeyPress(event) {
		if (event.key === 'Enter') {
			handleSubmit();
			return;
		}

		// Allow only numbers, minus sign, and control keys
		const allowedKeys = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '-', 'Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab'];
		if (!allowedKeys.includes(event.key)) {
			event.preventDefault();
		}
	}

	function moveToNextTrial() {
		currentTrialIndex++;
		
		// Check if current block is complete
		if (currentTrialIndex >= currentBlock.trials.length) {
			// Move to next block
			currentBlockIndex++;
			
			if (currentBlockIndex === 1) {
				currentBlock = sessionData.blocks.block_b;
				currentTrialIndex = 0;
				phase = 'block-transition';
			} else if (currentBlockIndex === 2) {
				currentBlock = sessionData.blocks.block_c;
				currentTrialIndex = 0;
				phase = 'block-transition';
			} else {
				// All blocks complete
				submitSession();
				return;
			}
		} else {
			// Continue current block
			startTrial();
		}
	}

	function continueToNextBlock() {
		phase = 'task';
		startTrial();
	}

	async function submitSession() {
		try {
			loading = true;
			error = null;
			const totalTime = Date.now() - startTime;

			// Stop timer interval
			if (timerInterval) {
				clearInterval(timerInterval);
				timerInterval = null;
			}

			taskId = $page.url.searchParams.get('taskId');
			
			// Submit to training endpoint
			const submitResponse = await fetch(
				`http://localhost:8000/api/training/tasks/plus-minus/submit/${currentUser.id}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						session_data: sessionData,
						user_responses: responses,
						total_time: totalTime,  // Send total elapsed time
						task_id: taskId
					})
				}
			);
			
			if (!submitResponse.ok) throw new Error('Failed to submit result');
			
			const submitData = await submitResponse.json();
			results = submitData;
			newBadges = submitData.newly_earned_badges || [];
			phase = 'results';
		} catch (err) {
			error = err.message;
		} finally {
			loading = false;
		}
	}

	onMount(async () => {
		if (!currentUser) {
			goto('/login');
			return;
		}
		await loadSession();
	});

	onDestroy(() => {
		// Clean up timer interval
		if (timerInterval) {
			clearInterval(timerInterval);
			timerInterval = null;
		}
	});
</script>

<div
	style="min-height: 100vh; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px;"
	data-localize-skip
>
	<div style="background: white; padding: 30px; border-radius: 10px; margin: 0 auto; max-width: 800px;">
		<div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 20px;">
			<h1 style="font-size: 28px; font-weight: bold; margin: 0; color: #333;">
				{t('Plus-Minus Task')}
			</h1>
			<DifficultyBadge {difficulty} domain="Cognitive Flexibility" />
		</div>

		{#if loading}
			<div style="text-align: center; padding: 40px;">
				<p style="font-size: 18px; color: #666;">{t('Loading...')}</p>
			</div>
		{:else if error}
			<div style="background: #fee; border: 2px solid #fcc; padding: 20px; border-radius: 8px;">
				<p style="color: #c33; margin-bottom: 10px;">{t('Error:')} {t(error)}</p>
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
					{t('The Plus-Minus Task measures your ability to:')}
				</p>
				
				<ul style="margin-left: 30px; margin-bottom: 20px; color: #555;">
					<li style="margin-bottom: 8px;">{t('Switch between mental operations')}</li>
					<li style="margin-bottom: 8px;">{t('Maintain accuracy under cognitive load')}</li>
					<li style="margin-bottom: 8px;">{t('Adapt to alternating task demands')}</li>
					<li style="margin-bottom: 8px;">{t('Process numerical information quickly')}</li>
				</ul>

				<div style="background: #f0f9ff; border-left: 4px solid #3b82f6; padding: 15px; margin-bottom: 20px;">
					<h3 style="font-size: 18px; font-weight: 600; margin-bottom: 10px; color: #1e40af;">
						{t('How It Works')}
					</h3>
					<p style="font-size: 14px; color: #555; margin-bottom: 8px;">
						<strong>{t('Block A:')}</strong> {t('Add 3 to each number shown (baseline speed)')}
					</p>
					<p style="font-size: 14px; color: #555; margin-bottom: 8px;">
						<strong>{t('Block B:')}</strong> {t('Subtract 3 from each number (baseline speed)')}
					</p>
					<p style="font-size: 14px; color: #555;">
						<strong>{t('Block C:')}</strong> {t('Alternate between +3 and -3 based on the cue (measures switching cost)')}
					</p>
				</div>

				<div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin-bottom: 20px;">
					<h3 style="font-size: 18px; font-weight: 600; margin-bottom: 10px; color: #92400e;">
						{t('Instructions')}
					</h3>
					<ul style="margin-left: 20px; color: #555;">
						<li style="margin-bottom: 8px;">{t('Perform the operation shown and type your answer')}</li>
						<li style="margin-bottom: 8px;">{t('Press Enter or click Submit after each answer')}</li>
						<li style="margin-bottom: 8px;">{t('In Block C, pay close attention to the cue (+3 or -3)')}</li>
						<li style="margin-bottom: 8px;">{t('Work as quickly and accurately as possible')}</li>
						<li style="margin-bottom: 8px;">{lt(`Total trials: ${sessionData ? sessionData.total_trials : '36'}`, `মোট ট্রায়াল: ${n(sessionData ? sessionData.total_trials : 36)}`)}</li>
					</ul>
				</div>

				<div style="background: #e0f2fe; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
					<p style="font-size: 14px; color: #0c4a6e; margin-bottom: 8px;">
						<strong>{t('Current Difficulty:')}</strong> {lt(`Level ${difficulty} / 10`, `লেভেল ${n(difficulty)} / ১০`)}
					</p>
					<p style="font-size: 13px; color: #0369a1;">
						{difficultySummary()}
					</p>
				</div>

				<button 
					on:click={startTask} 
					style="padding: 15px 40px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; border: none; border-radius: 8px; font-size: 18px; font-weight: 600; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
					{t('Start Test')}
				</button>
			</div>
		{:else if phase === 'block-transition'}
			<div style="text-align: center; padding: 40px;">
				<h2 style="font-size: 24px; font-weight: 600; margin-bottom: 20px; color: #333;">
					{blockTransitionTitle()}
				</h2>
				
				<p style="font-size: 16px; color: #555; margin-bottom: 30px;">
					{@html blockTransitionMessage().replace('\n', '<br/>')}
				</p>

				<button 
					on:click={continueToNextBlock} 
					style="padding: 15px 40px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; border: none; border-radius: 8px; font-size: 18px; font-weight: 600; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
					{t('Continue')}
				</button>
			</div>
		{:else if phase === 'task'}
			{#if currentBlock && getCurrentTrial()}
				{@const trial = getCurrentTrial()}
				{@const blockNum = currentBlockIndex + 1}
				{@const totalTrials = currentBlock.total_trials}
				{@const trialNum = currentTrialIndex + 1}

				<div>
					<!-- Progress and Timer -->
					<div style="background: #f3f4f6; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
						<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 10px;">
							<span style="font-size: 14px; color: #666;">{currentBlockLabel(blockNum)}</span>
							<div style="display: flex; align-items: center; gap: 20px;">
								<span style="font-size: 14px; color: #666;">{trialProgressLabel(trialNum, totalTrials)}</span>
								<div style="display: flex; align-items: center; gap: 0.5rem; background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 0.5rem 1rem; border-radius: 1.5rem; box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);">
									<span style="font-size: 1.2rem;">⏱️</span>
									<span style="font-size: 1rem; font-weight: 700; color: white; min-width: 50px; text-align: center;">{n(elapsedTime.toFixed(1), { minimumFractionDigits: 1, maximumFractionDigits: 1 })}{lt('s', 'সে')}</span>
								</div>
							</div>
						</div>
						<div style="background: #e5e7eb; height: 8px; border-radius: 4px; overflow: hidden;">
							<div style="background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%); height: 100%; width: {(trialNum / totalTrials) * 100}%; transition: width 0.3s;"></div>
						</div>
					</div>

					<!-- Cue Display (for Block C) -->
					{#if showCue}
						<div style="text-align: center; margin-bottom: 20px;">
							<div style="background: #fef3c7; border: 3px solid #f59e0b; padding: 20px 40px; border-radius: 8px; display: inline-block; animation: pulse 0.5s;">
								<p style="font-size: 32px; font-weight: bold; color: #92400e; margin: 0;">
									{cueText}
								</p>
							</div>
						</div>
					{/if}

					<!-- Number Display -->
					<div style="text-align: center; margin-bottom: 30px;">
						<div style="background: #f9fafb; border: 3px solid #d1d5db; border-radius: 12px; padding: 40px; display: inline-block; min-width: 200px;">
							<p style="font-size: 64px; font-weight: bold; color: #333; margin: 0; font-family: monospace;">
								{trial.number}
							</p>
						</div>
					</div>

					<!-- Operation Indicator (always shown) -->
					<div style="text-align: center; margin-bottom: 20px;">
						<p style="font-size: 20px; color: #666; font-weight: 600;">
							{#if trial.operation === 'add'}
								<span style="color: #10b981;">{t('Add 3')}</span>
							{:else}
								<span style="color: #f59e0b;">{t('Subtract 3')}</span>
							{/if}
						</p>
					</div>

					<!-- Answer Input -->
					<div style="text-align: center; margin-bottom: 30px;">
						<input
							type="number"
							bind:value={userAnswer}
							on:keypress={handleKeyPress}
							on:focus={(e) => { e.currentTarget.style.borderColor='#f093fb'; }}
							on:blur={(e) => { e.currentTarget.style.borderColor='#d1d5db'; }}
							placeholder={t('Your answer')}
							autofocus
							style="font-size: 32px; padding: 15px 25px; border: 3px solid #d1d5db; border-radius: 8px; text-align: center; width: 250px; font-family: monospace; outline: none; transition: border-color 0.2s;"
						/>
					</div>

					<!-- Submit Button -->
					<div style="text-align: center;">
						<button
							on:click={handleSubmit}
							disabled={userAnswer === ''}
							style="padding: 15px 50px; background: {userAnswer === '' ? '#d1d5db' : 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'}; color: white; border: none; border-radius: 8px; font-size: 18px; font-weight: 600; cursor: {userAnswer === '' ? 'not-allowed' : 'pointer'}; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
							{t('Submit')}
						</button>
					</div>
				</div>
			{/if}
		{:else if phase === 'results'}
			<div>
				<h2 style="font-size: 24px; font-weight: 600; margin-bottom: 20px; color: #333;">
					{t('Test Complete!')}
				</h2>

				<!-- Overall Score -->
				<div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 30px; border-radius: 10px; margin-bottom: 30px; text-align: center;">
					<p style="color: white; font-size: 18px; margin-bottom: 10px;">{t('Your Score')}</p>
					<p style="color: white; font-size: 48px; font-weight: bold; margin: 0;">
						{n(results.score)}
					</p>
					<p style="color: rgba(255,255,255,0.9); font-size: 16px; margin-top: 10px;">
						{t('Overall Accuracy:')} {n((results.accuracy * 100).toFixed(1), { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%
					</p>
				</div>

				<!-- Block Results -->
				<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px;">
					<div style="background: #f0fdf4; padding: 20px; border-radius: 8px; border-left: 4px solid #10b981;">
						<h3 style="font-size: 16px; font-weight: 600; color: #065f46; margin-bottom: 10px;">
							{t('Block A: Add 3')}
						</h3>
						<p style="font-size: 14px; color: #555; margin-bottom: 5px;">
							{t('Accuracy:')} {n((results.blocks.block_a.accuracy * 100).toFixed(1), { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%
						</p>
						<p style="font-size: 14px; color: #555;">
							{t('Avg RT:')} {n(results.blocks.block_a.mean_rt.toFixed(0))}{lt('ms', 'মি.সে')}
						</p>
					</div>

					<div style="background: #f0f9ff; padding: 20px; border-radius: 8px; border-left: 4px solid #3b82f6;">
						<h3 style="font-size: 16px; font-weight: 600; color: #1e40af; margin-bottom: 10px;">
							{t('Block B: Subtract 3')}
						</h3>
						<p style="font-size: 14px; color: #555; margin-bottom: 5px;">
							{t('Accuracy:')} {n((results.blocks.block_b.accuracy * 100).toFixed(1), { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%
						</p>
						<p style="font-size: 14px; color: #555;">
							{t('Avg RT:')} {n(results.blocks.block_b.mean_rt.toFixed(0))}{lt('ms', 'মি.সে')}
						</p>
					</div>

					<div style="background: #fef3c7; padding: 20px; border-radius: 8px; border-left: 4px solid #f59e0b;">
						<h3 style="font-size: 16px; font-weight: 600; color: #92400e; margin-bottom: 10px;">
							{t('Block C: Alternating')}
						</h3>
						<p style="font-size: 14px; color: #555; margin-bottom: 5px;">
							{t('Accuracy:')} {n((results.blocks.block_c.accuracy * 100).toFixed(1), { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%
						</p>
						<p style="font-size: 14px; color: #555;">
							{t('Avg RT:')} {n(results.blocks.block_c.mean_rt.toFixed(0))}{lt('ms', 'মি.সে')}
						</p>
					</div>
				</div>

				<!-- Switching Cost -->
				<div style="background: #f9fafb; padding: 25px; border-radius: 8px; margin-bottom: 30px; border: 2px solid #e5e7eb;">
					<h3 style="font-size: 20px; font-weight: 600; color: #333; margin-bottom: 15px;">
						{t('Switching Cost Analysis')}
					</h3>
					<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
						<div>
							<p style="font-size: 14px; color: #666; margin-bottom: 5px;">{t('Reaction Time Cost')}</p>
							<p style="font-size: 28px; font-weight: 600; color: {results.switching_cost > 0 ? '#f59e0b' : '#10b981'};">
								{results.switching_cost >= 0 ? '+' : ''}{n(results.switching_cost.toFixed(0))}{lt('ms', 'মি.সে')}
							</p>
							<p style="font-size: 12px; color: #888;">
								{t('Time penalty when switching')}
							</p>
						</div>
						<div>
							<p style="font-size: 14px; color: #666; margin-bottom: 5px;">{t('Accuracy Cost')}</p>
							<p style="font-size: 28px; font-weight: 600; color: {results.switching_cost_accuracy > 0 ? '#f59e0b' : '#10b981'};">
								{results.switching_cost_accuracy >= 0 ? '+' : ''}{n((results.switching_cost_accuracy * 100).toFixed(1), { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%
							</p>
							<p style="font-size: 12px; color: #888;">
								{t('Accuracy drop when switching')}
							</p>
						</div>
					</div>
					<div style="background: #e0f2fe; padding: 15px; border-radius: 6px; margin-top: 15px;">
						<p style="font-size: 13px; color: #0c4a6e; margin: 0;">
							<strong>{t('💡 Interpretation:')}</strong> {t('Lower switching cost indicates better cognitive flexibility. The cost measures how much harder it is to alternate between operations compared to doing just one.')}
						</p>
					</div>
				</div>

				<!-- Actions -->
				<div style="display: flex; gap: 15px;">
					<button 
						on:click={() => goto('/dashboard')} 
						style="flex: 1; padding: 15px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer;">
						{t('Return to Dashboard')}
					</button>
					<button 
						on:click={() => goto('/training')} 
						style="flex: 1; padding: 15px; background: white; color: #f5576c; border: 2px solid #f5576c; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer;">
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

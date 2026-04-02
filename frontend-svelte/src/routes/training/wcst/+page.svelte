<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
	import { formatNumber, formatPercent, locale, translateText } from '$lib/i18n';
	import { user } from '$lib/stores';
	import { getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
	import { onMount } from 'svelte';

	let phase = 'intro';
	let loading = false;
	let error = null;
	let sessionData = null;
	let difficulty = 1;
	let baselineFlexibility = null;
	let instructions = null;
	let currentTrialIndex = 0;
	let responses = [];
	let startTime = null;
	let trialStartTime = null;
	let isPractice = false;
	let practiceTrials = [];
	let currentPracticeIndex = 0;
	let showFeedback = false;
	let feedbackMessage = '';
	let feedbackType = '';
	let currentRule = null;
	let correctNeeded = 10;  // Will be set from session config
	let categoryCompletedAt = -1;  // Track when last category was completed
	let results = null;
	let newBadges = [];
	let currentUser = null;
	let taskId = null;
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';

	const COLORS = {
		red: '#EF4444',
		blue: '#3B82F6',
		green: '#10B981',
		yellow: '#F59E0B'
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

	function levelLabel(value = difficulty, max = 10) {
		return $locale === 'bn' ? `লেভেল ${n(value)}/${n(max)}` : `Level ${value}/${max}`;
	}

	function scoreLabel(value, max = 100) {
		return $locale === 'bn' ? `${n(value)}/${n(max)}` : `${value}/${max}`;
	}

	function durationMsLabel(value) {
		const roundedValue = Number.isFinite(Number(value)) ? Math.round(Number(value)) : 0;
		return $locale === 'bn' ? `${n(roundedValue)} মি.সে.` : `${roundedValue}ms`;
	}

	function percentFromWhole(value, options = {}) {
		return pct((Number(value) || 0) / 100, options);
	}

	function ruleName(rule = currentRule) {
		if (rule === 'color') return $locale === 'bn' ? 'রঙ' : 'COLOR';
		if (rule === 'shape') return $locale === 'bn' ? 'আকৃতি' : 'SHAPE';
		if (rule === 'number') return $locale === 'bn' ? 'সংখ্যা' : 'NUMBER';
		return t(rule || '');
	}

	function ruleInstructionLabel(rule = currentRule) {
		if ($locale === 'bn') {
			return `নিয়ম: ${ruleName(rule)} অনুযায়ী সাজান`;
		}
		return `Rule: Sort by ${ruleName(rule)}`;
	}

	function practiceModeLabel() {
		if ($locale === 'bn') {
			return `অনুশীলন মোড - ট্রায়াল ${n(currentPracticeIndex + 1)} / ${n(practiceTrials.length)}`;
		}
		return `Practice Mode - Trial ${currentPracticeIndex + 1} / ${practiceTrials.length}`;
	}

	function trialProgressLabel(current, total) {
		if ($locale === 'bn') {
			return `ট্রায়াল ${n(current)} / ${n(total)}`;
		}
		return `Trial ${current} / ${total}`;
	}

	function cardMetaLabel(card) {
		return `${t(card.color)} ${t(card.shape)}`;
	}

	function symbolCountLabel(count) {
		return `${n(count)} ${count === 1 ? t('symbol') : t('symbols')}`;
	}

	function generatePracticeTrials() {
		const colors = ['red', 'blue', 'green', 'yellow'];
		const shapes = ['circle', 'star', 'triangle', 'cross'];
		const numbers = [1, 2, 3, 4];
		const trials = [];
		for (let i = 0; i < 12; i++) {
			trials.push({
				color: colors[Math.floor(Math.random() * colors.length)],
				shape: shapes[Math.floor(Math.random() * shapes.length)],
				number: numbers[Math.floor(Math.random() * numbers.length)]
			});
		}
		return trials;
	}

	async function loadSession() {
		try {
			loading = true;
			error = null;
			const response = await fetch(
				`http://localhost:8000/api/training/tasks/wcst/generate/${currentUser.id}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' }
				}
			);
			if (!response.ok) throw new Error('Failed to load session');
		const data = await response.json();
		sessionData = data.session_data;
		difficulty = data.difficulty;
		baselineFlexibility = data.baseline_flexibility;
		instructions = data.instructions;
		practiceTrials = generatePracticeTrials();

		// Randomize starting rule (clinical standard)
		const rules = ['color', 'shape', 'number'];
		currentRule = rules[Math.floor(Math.random() * rules.length)];

		// Get correct_needed from difficulty config
		correctNeeded = sessionData.config?.correct_needed || 10;
		console.log(`📋 WCST Config: Difficulty ${difficulty}, Correct needed: ${correctNeeded}, Starting rule: ${currentRule}`);
		} catch (err) {
			error = err.message;
		} finally {
			loading = false;
		}
	}

	function startPractice() {
		playMode = TASK_PLAY_MODE.PRACTICE;
		practiceStatusMessage = '';
		isPractice = true;
		currentPracticeIndex = 0;
		responses = [];
		phase = 'practice';
		trialStartTime = Date.now();
	}

	function startTest() {
		playMode = TASK_PLAY_MODE.RECORDED;
		practiceStatusMessage = '';
		isPractice = false;
		currentTrialIndex = 0;
		responses = [];
		categoryCompletedAt = -1;  // Reset category tracking
		phase = 'test';
		startTime = Date.now();
		trialStartTime = Date.now();
	}

	function finishPractice() {
		playMode = TASK_PLAY_MODE.RECORDED;
		isPractice = false;
		showFeedback = false;
		currentPracticeIndex = 0;
		phase = 'instructions';
		practiceStatusMessage = getPracticeCopy($locale).complete;
	}

	function handleCardSelection(pileIndex) {
		if (showFeedback) return;
		const responseTime = Date.now() - trialStartTime;

		if (isPractice) {
			const trialCard = practiceTrials[currentPracticeIndex];
			const targetCard = sessionData.target_cards[pileIndex];
			const isCorrect = trialCard[currentRule] === targetCard[currentRule];
			feedbackType = isCorrect ? 'correct' : 'wrong';
			feedbackMessage = isCorrect ? t('Correct!') : t('Wrong!');
			showFeedback = true;

			setTimeout(() => {
				showFeedback = false;
				currentPracticeIndex++;
				if (currentPracticeIndex >= practiceTrials.length) {
					finishPractice();
				} else {
					trialStartTime = Date.now();
				}
			}, 1000);
	} else {
		// ACTUAL TEST - MUST SHOW FEEDBACK (clinical requirement!)
		const trialCard = sessionData.trial_cards[currentTrialIndex];
		const targetCard = sessionData.target_cards[pileIndex];

		// Check if correct based on current rule
		const isCorrect = trialCard[currentRule] === targetCard[currentRule];

		// Record response
		responses.push({
			trial_index: currentTrialIndex,
			selected_pile: pileIndex,
			response_time: responseTime,
			is_correct: isCorrect
		});

		// Show feedback - CRITICAL for WCST to function
		feedbackType = isCorrect ? 'correct' : 'wrong';
		feedbackMessage = isCorrect ? t('Correct!') : t('Wrong!');
		showFeedback = true;

		// Check for rule change using sliding window approach
		if (responses.length >= correctNeeded) {
			const windowSize = correctNeeded + 2; // Allow 2 errors in the window
			const recentResponses = responses.slice(-windowSize);
			const correctInWindow = recentResponses.filter(r => r.is_correct).length;
			const trialsSinceLastChange = currentTrialIndex - categoryCompletedAt;

			if (correctInWindow >= correctNeeded && trialsSinceLastChange >= correctNeeded) {
				const rules = ['color', 'shape', 'number'];
				const oldRule = currentRule;

				// Clinical WCST: Randomly select from the OTHER 2 rules (not current)
				const otherRules = rules.filter(rule => rule !== currentRule);
				currentRule = otherRules[Math.floor(Math.random() * otherRules.length)];

				// Mark this trial as when category was completed
				categoryCompletedAt = currentTrialIndex;

				console.log(`🔄 RULE CHANGED! ${oldRule} → ${currentRule}`);
				console.log(`   Strategy: Random selection from [${otherRules.join(', ')}]`);
				console.log(`   Achieved: ${correctInWindow}/${windowSize} correct in sliding window`);
				console.log(`   Required: ${correctNeeded} correct (difficulty level ${difficulty})`);
				console.log(`   Trial: ${currentTrialIndex + 1}, Next change not before trial ${categoryCompletedAt + correctNeeded + 1}`);
			}
		}

		// Log current progress
		if (responses.length >= correctNeeded) {
			const windowSize = correctNeeded + 2;
			const recentResponses = responses.slice(-windowSize);
			const correctInWindow = recentResponses.filter(r => r.is_correct).length;
			const trialsSinceLastChange = currentTrialIndex - categoryCompletedAt;
			console.log(`${isCorrect ? '✅' : '❌'} Trial ${currentTrialIndex + 1}: ${correctInWindow}/${windowSize} correct in window (need ${correctNeeded}), ${trialsSinceLastChange} trials since last change, Rule: ${currentRule}`);
		} else {
			console.log(`${isCorrect ? '✅' : '❌'} Trial ${currentTrialIndex + 1}: Building history (${responses.length}/${correctNeeded} minimum), Rule: ${currentRule}`);
		}

		setTimeout(() => {
			showFeedback = false;
			moveToNextTrial();
		}, 800);
	}
}

	function moveToNextTrial() {
		currentTrialIndex++;
		if (currentTrialIndex >= sessionData.trial_cards.length) {
			submitSession();
		} else {
			trialStartTime = Date.now();
		}
	}

	async function submitSession() {
		try {
			loading = true;
			error = null;
			const totalTime = Date.now() - startTime;
			taskId = $page.url.searchParams.get('taskId');
			const response = await fetch(
				`http://localhost:8000/api/training/tasks/wcst/submit/${currentUser.id}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						session_data: sessionData,
						responses: responses,
						total_time: totalTime,
						task_id: taskId
					})
				}
			);
			if (!response.ok) throw new Error('Failed to submit session');
			const data = await response.json();
			results = data;
			newBadges = data.new_badges || [];
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
</script>

<div class="container" data-localize-skip>
	<div style="background: white; padding: 30px; border-radius: 10px; margin: 20px auto; max-width: 1000px;">
		<div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 20px;">
			<h1 style="font-size: 28px; font-weight: bold; margin: 0; color: #333;">{t('Wisconsin Card Sorting Test')}</h1>
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
				<h2 style="font-size: 24px; font-weight: 600; margin-bottom: 15px; color: #333;">{t('Executive Function Assessment')}</h2>
				
				<p style="font-size: 16px; color: #555; margin-bottom: 15px;">
					{t('The Wisconsin Card Sorting Test (WCST) measures your ability to:')}
				</p>
				
				<ul style="margin-left: 30px; margin-bottom: 20px; color: #555;">
					<li style="margin-bottom: 8px;"><strong>{t('Shift mental sets')}</strong> - {t('Adapt when rules change')}</li>
					<li style="margin-bottom: 8px;"><strong>{t('Learn from feedback')}</strong> - {t('Use "Correct" or "Wrong" cues')}</li>
					<li style="margin-bottom: 8px;"><strong>{t('Maintain strategies')}</strong> - {t('Stick with a rule once discovered')}</li>
					<li style="margin-bottom: 8px;"><strong>{t('Recognize patterns')}</strong> - {t('Identify sorting rules quickly')}</li>
				</ul>

				<div style="background: #e6f3ff; border: 2px solid #99ccff; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
					<h3 style="font-weight: 600; color: #0066cc; margin-bottom: 8px;">{t('How It Works:')}</h3>
					<p style="color: #0066cc;">
						{t("You'll see a card with a color, shape, and number of symbols. Sort it into one of four piles by clicking a target card. The sorting rule (color, shape, or number) will change without warning. Use the feedback to discover the current rule.")}
					</p>
				</div>

				<p style="color: #666; margin-bottom: 20px;">
					<strong>{t('Current Difficulty:')}</strong> {levelLabel()}
				</p>

				<button
					on:click={() => (phase = 'instructions')}
					style="width: 100%; padding: 15px; background: #0066cc; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer;"
				>
					{t('Continue to Instructions')}
				</button>
			</div>
		{:else if phase === 'instructions'}
			<div>
				<h2 style="font-size: 24px; font-weight: 600; margin-bottom: 15px; color: #333;">{t('Instructions')}</h2>

				<div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
					<h3 style="font-weight: 600; color: #333; margin-bottom: 8px;">🎯 {t('Your Task:')}</h3>
					<p style="color: #555;">
						{t(`Sort each card by clicking one of the four target cards at the top. You'll get feedback on whether your sort was "Correct" or "Wrong".`)}
					</p>
				</div>

				<div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
					<h3 style="font-weight: 600; color: #333; margin-bottom: 8px;">🔄 {t('The Rules:')}</h3>
					<p style="color: #555; margin-bottom: 8px;">{t('Cards can be sorted by:')}</p>
					<ul style="margin-left: 30px; color: #555;">
						<li><strong>{t('Color')}</strong> - {t('Match the card color')}</li>
						<li><strong>{t('Shape')}</strong> - {t('Match the shape type')}</li>
						<li><strong>{t('Number')}</strong> - {t('Match the number of symbols')}</li>
					</ul>
				</div>

				<div style="background: #fff3e0; border: 2px solid #ffcc80; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
					<h3 style="font-weight: 600; color: #e65100; margin-bottom: 8px;">⚠️ {t('Important:')}</h3>
					<ul style="margin-left: 30px; color: #e65100;">
						<li>{t('The rule will change without warning during the test')}</li>
						<li>{t('When you get multiple "Wrong" responses, the rule has likely changed')}</li>
						<li>{t("Don't get stuck on a rule that's no longer working")}</li>
					</ul>
				</div>

				<button
					on:click={startPractice}
					style="width: 100%; padding: 15px; background: #2e7d32; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer;"
				>
					{$locale === 'bn'
						? `অনুশীলনী রাউন্ড শুরু করুন (${n(practiceTrials.length)} ট্রায়াল)`
						: `Start Practice Round (${practiceTrials.length} trials)`}
				</button>
				<TaskPracticeActions
					locale={$locale}
					startLabel={$locale === 'bn'
						? `আসল পরীক্ষা শুরু করুন (${n(sessionData.trial_cards.length)} ট্রায়াল)`
						: `Begin Test (${sessionData.trial_cards.length} trials)`}
					practiceVisible={false}
					statusMessage={practiceStatusMessage}
					on:start={startTest}
				/>
			</div>
		{:else if phase === 'practice'}
			<div>
				<PracticeModeBanner locale={$locale} />
				<div style="text-align: center; margin-bottom: 20px;">
					<p style="color: #666;">{practiceModeLabel()}</p>
					<p style="color: #0066cc; font-size: 14px; margin-top: 5px;">{ruleInstructionLabel()}</p>
				</div>

				<p style="text-align: center; color: #666; margin-bottom: 10px;">{t('Click a target card to sort:')}</p>
				<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 30px;">
					{#each sessionData.target_cards as card, index}
						<button
							on:click={() => handleCardSelection(index)}
							disabled={showFeedback}
							style="background: white; border: 2px solid #ccc; border-radius: 8px; padding: 15px; cursor: pointer; min-height: 120px; display: flex; flex-direction: column; align-items: center; justify-content: center; {showFeedback ? 'opacity: 0.5;' : ''}"
						>
							<div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 5px; margin-bottom: 10px;">
								{#each Array(card.number) as _}
									<svg width="28" height="28" viewBox="0 0 40 40">
										{#if card.shape === 'circle'}
											<circle cx="20" cy="20" r="15" fill={COLORS[card.color]} />
										{:else if card.shape === 'star'}
											<path d="M20 5 L23.5 16.5 L35 16.5 L25.5 24 L29 35 L20 27.5 L11 35 L14.5 24 L5 16.5 L16.5 16.5 Z" fill={COLORS[card.color]} />
										{:else if card.shape === 'triangle'}
											<path d="M20 8 L32 32 L8 32 Z" fill={COLORS[card.color]} />
										{:else if card.shape === 'cross'}
											<path d="M15 5 L25 5 L25 15 L35 15 L35 25 L25 25 L25 35 L15 35 L15 25 L5 25 L5 15 L15 15 Z" fill={COLORS[card.color]} />
										{/if}
									</svg>
								{/each}
							</div>
							<div style="font-size: 11px; color: #888; text-align: center;">
								<div>{cardMetaLabel(card)}</div>
								<div>{symbolCountLabel(card.number)}</div>
							</div>
						</button>
					{/each}
				</div>

				{#if currentPracticeIndex < practiceTrials.length}
					<p style="text-align: center; color: #666; margin-bottom: 10px;">{t('Card to sort:')}</p>
					<div style="text-align: center; margin-bottom: 20px;">
						<div style="display: inline-block; background: linear-gradient(135deg, #e3f2fd, #bbdefb); border: 3px solid #42a5f5; border-radius: 10px; padding: 25px;">
							<div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 5px; margin-bottom: 10px;">
								{#each Array(practiceTrials[currentPracticeIndex].number) as _}
									<svg width="40" height="40" viewBox="0 0 40 40">
										{#if practiceTrials[currentPracticeIndex].shape === 'circle'}
											<circle cx="20" cy="20" r="15" fill={COLORS[practiceTrials[currentPracticeIndex].color]} />
										{:else if practiceTrials[currentPracticeIndex].shape === 'star'}
											<path d="M20 5 L23.5 16.5 L35 16.5 L25.5 24 L29 35 L20 27.5 L11 35 L14.5 24 L5 16.5 L16.5 16.5 Z" fill={COLORS[practiceTrials[currentPracticeIndex].color]} />
										{:else if practiceTrials[currentPracticeIndex].shape === 'triangle'}
											<path d="M20 8 L32 32 L8 32 Z" fill={COLORS[practiceTrials[currentPracticeIndex].color]} />
										{:else if practiceTrials[currentPracticeIndex].shape === 'cross'}
											<path d="M15 5 L25 5 L25 15 L35 15 L35 25 L25 25 L25 35 L15 35 L15 25 L5 25 L5 15 L15 15 Z" fill={COLORS[practiceTrials[currentPracticeIndex].color]} />
										{/if}
									</svg>
								{/each}
							</div>
							<div style="font-size: 12px; color: #666; text-align: center;">
								<div>{cardMetaLabel(practiceTrials[currentPracticeIndex])}</div>
							</div>
						</div>
					</div>
				{/if}

				{#if showFeedback}
					<div style="text-align: center; padding: 15px; border-radius: 8px; background: {feedbackType === 'correct' ? '#d4edda' : '#f8d7da'}; color: {feedbackType === 'correct' ? '#155724' : '#721c24'}; font-size: 20px; font-weight: bold;">
						{feedbackMessage}
					</div>
				{/if}
			</div>
		{:else if phase === 'instructions-test'}
			<div>
				<h2 style="font-size: 24px; font-weight: 600; margin-bottom: 15px; color: #2e7d32;">✓ {t('Practice Complete!')}</h2>
				<p style="color: #555; margin-bottom: 15px;">
					{t("Good! You've completed the practice round. Now you're ready for the actual test.")}
				</p>

				<div style="background: #fff3e0; border: 2px solid #ffcc80; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
					<h3 style="font-weight: 600; color: #e65100; margin-bottom: 8px;">{t('In the Real Test:')}</h3>
					<ul style="margin-left: 30px; color: #e65100;">
						<li>{t('The rule will NOT be shown')}</li>
						<li>{t('The rule will CHANGE after you get several correct sorts')}</li>
						<li>{t('You must discover the rule from the feedback')}</li>
					</ul>
				</div>

				<button
					on:click={startTest}
					style="width: 100%; padding: 15px; background: #0066cc; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer;"
				>
					{$locale === 'bn'
						? `পরীক্ষা শুরু করুন (${n(sessionData.trial_cards.length)} ট্রায়াল)`
						: `Begin Test (${sessionData.trial_cards.length} trials)`}
				</button>
			</div>
		{:else if phase === 'test'}
			<div>
				<div style="text-align: center; margin-bottom: 15px;">
					<p style="color: #666;">{trialProgressLabel(currentTrialIndex + 1, sessionData.trial_cards.length)}</p>
					<div style="background: #ddd; height: 8px; border-radius: 4px; margin: 10px auto; max-width: 400px;">
						<div style="background: #0066cc; height: 8px; border-radius: 4px; width: {(currentTrialIndex / sessionData.trial_cards.length) * 100}%;"></div>
					</div>
				</div>

				<p style="text-align: center; color: #666; margin-bottom: 10px;">{t('Click a target card to sort:')}</p>
				<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 30px;">
					{#each sessionData.target_cards as card, index}
						<button
							on:click={() => handleCardSelection(index)}
							style="background: white; border: 2px solid #ccc; border-radius: 8px; padding: 15px; cursor: pointer; min-height: 120px; display: flex; flex-direction: column; align-items: center; justify-content: center;"
						>
							<div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 5px; margin-bottom: 10px;">
								{#each Array(card.number) as _}
									<svg width="28" height="28" viewBox="0 0 40 40">
										{#if card.shape === 'circle'}
											<circle cx="20" cy="20" r="15" fill={COLORS[card.color]} />
										{:else if card.shape === 'star'}
											<path d="M20 5 L23.5 16.5 L35 16.5 L25.5 24 L29 35 L20 27.5 L11 35 L14.5 24 L5 16.5 L16.5 16.5 Z" fill={COLORS[card.color]} />
										{:else if card.shape === 'triangle'}
											<path d="M20 8 L32 32 L8 32 Z" fill={COLORS[card.color]} />
										{:else if card.shape === 'cross'}
											<path d="M15 5 L25 5 L25 15 L35 15 L35 25 L25 25 L25 35 L15 35 L15 25 L5 25 L5 15 L15 15 Z" fill={COLORS[card.color]} />
										{/if}
									</svg>
								{/each}
							</div>
							<div style="font-size: 11px; color: #888; text-align: center;">
								<div>{cardMetaLabel(card)}</div>
							</div>
						</button>
					{/each}
				</div>

				{#if currentTrialIndex < sessionData.trial_cards.length}
					<p style="text-align: center; color: #666; margin-bottom: 10px;">{t('Card to sort:')}</p>
					<div style="text-align: center;">
						<div style="display: inline-block; background: linear-gradient(135deg, #e3f2fd, #bbdefb); border: 3px solid #42a5f5; border-radius: 10px; padding: 25px;">
							<div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 5px; margin-bottom: 10px;">
								{#each Array(sessionData.trial_cards[currentTrialIndex].number) as _}
									<svg width="40" height="40" viewBox="0 0 40 40">
										{#if sessionData.trial_cards[currentTrialIndex].shape === 'circle'}
											<circle cx="20" cy="20" r="15" fill={COLORS[sessionData.trial_cards[currentTrialIndex].color]} />
										{:else if sessionData.trial_cards[currentTrialIndex].shape === 'star'}
											<path d="M20 5 L23.5 16.5 L35 16.5 L25.5 24 L29 35 L20 27.5 L11 35 L14.5 24 L5 16.5 L16.5 16.5 Z" fill={COLORS[sessionData.trial_cards[currentTrialIndex].color]} />
										{:else if sessionData.trial_cards[currentTrialIndex].shape === 'triangle'}
											<path d="M20 8 L32 32 L8 32 Z" fill={COLORS[sessionData.trial_cards[currentTrialIndex].color]} />
										{:else if sessionData.trial_cards[currentTrialIndex].shape === 'cross'}
											<path d="M15 5 L25 5 L25 15 L35 15 L35 25 L25 25 L25 35 L15 35 L15 25 L5 25 L5 15 L15 15 Z" fill={COLORS[sessionData.trial_cards[currentTrialIndex].color]} />
										{/if}
									</svg>
								{/each}
							</div>
							<div style="font-size: 12px; color: #666; text-align: center;">
								<div>{cardMetaLabel(sessionData.trial_cards[currentTrialIndex])}</div>
							</div>
						</div>
					</div>
				{/if}

				<!-- Feedback Display - CRITICAL for WCST! -->
				{#if showFeedback}
					<div style="text-align: center; padding: 15px; border-radius: 8px; margin-top: 20px; background: {feedbackType === 'correct' ? '#d4edda' : '#f8d7da'}; color: {feedbackType === 'correct' ? '#155724' : '#721c24'}; font-size: 20px; font-weight: bold;">
						{feedbackMessage}
					</div>
				{/if}
			</div>
		{:else if phase === 'results'}
			<div>
				<h2 style="font-size: 24px; font-weight: 600; margin-bottom: 20px; color: #2e7d32;">✓ {t('Test Complete!')}</h2>

				<div style="padding: 25px; border-radius: 10px; text-align: center; margin-bottom: 20px; background: {results.performance_category === 'Excellent' ? '#fff9c4' : results.performance_category === 'Good' ? '#c8e6c9' : results.performance_category === 'Fair' ? '#bbdefb' : '#e0e0e0'}; border: 3px solid {results.performance_category === 'Excellent' ? '#fdd835' : results.performance_category === 'Good' ? '#66bb6a' : results.performance_category === 'Fair' ? '#42a5f5' : '#9e9e9e'};">
					<h3 style="font-size: 32px; font-weight: bold; margin-bottom: 10px;">{t(results.performance_category)}</h3>
					<p style="font-size: 20px;">{t('Score')}: {scoreLabel(results.score)}</p>
				</div>

				<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;">
					<div style="background: #e3f2fd; border: 2px solid #42a5f5; padding: 15px; border-radius: 8px;">
						<p style="color: #1976d2; font-weight: 600; margin-bottom: 5px;">{t('Categories')}</p>
						<p style="font-size: 28px; font-weight: bold; color: #1565c0;">{n(results.categories_achieved)}</p>
					</div>
					<div style="background: #f3e5f5; border: 2px solid #ab47bc; padding: 15px; border-radius: 8px;">
						<p style="color: #7b1fa2; font-weight: 600; margin-bottom: 5px;">{t('Accuracy')}</p>
						<p style="font-size: 28px; font-weight: bold; color: #6a1b9a;">{percentFromWhole(results.accuracy, { minimumFractionDigits: 0, maximumFractionDigits: 1 })}</p>
					</div>
					<div style="background: #ffebee; border: 2px solid #ef5350; padding: 15px; border-radius: 8px;">
						<p style="color: #c62828; font-weight: 600; margin-bottom: 5px;">{t('Total Errors')}</p>
						<p style="font-size: 28px; font-weight: bold; color: #b71c1c;">{n(results.total_errors)}</p>
					</div>
					<div style="background: #e8f5e9; border: 2px solid #66bb6a; padding: 15px; border-radius: 8px;">
						<p style="color: #2e7d32; font-weight: 600; margin-bottom: 5px;">{t('Avg Time')}</p>
						<p style="font-size: 28px; font-weight: bold; color: #1b5e20;">{durationMsLabel(results.average_response_time)}</p>
					</div>
				</div>

				<div style="background: #f5f5f5; border: 2px solid #ccc; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
					<p style="font-weight: 600; color: #333; margin-bottom: 10px;">{t('Clinical Interpretation:')}</p>
					<p style="color: #555;">{t(results.feedback)}</p>
				</div>

				{#if newBadges && newBadges.length > 0}
					<div style="margin-bottom: 20px;">
						<BadgeNotification badges={newBadges} />
					</div>
				{/if}

				<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
					<button
						on:click={() => goto('/dashboard')}
						style="padding: 15px; background: #666; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer;"
					>
						{t('Dashboard')}
					</button>
					<button
						on:click={() => goto('/progress')}
						style="padding: 15px; background: #0066cc; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer;"
					>
						{t('View Progress')}
					</button>
				</div>
			</div>
		{/if}
	</div>
</div>

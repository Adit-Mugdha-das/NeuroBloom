<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { formatNumber, locale, localeText, translateText } from '$lib/i18n';
	import { tasks, training } from '$lib/api';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let stage = 'intro';
	let isTrainingMode, trainingPlanId, trainingDifficulty, taskId;
	let sessionComplete = false;
	let completedTasksCount = 0;

	const GREEN_COLOR = '#4caf50';

	// Config: [simpleTrials, choiceTrials, delayMin, delayMax, penalty, choiceShapes]
	const CONFIG = {
		1: [8, 12, 2000, 3500, 'retry', 2],
		2: [10, 12, 1800, 3300, 'retry', 2],
		3: [10, 15, 1500, 3000, 'count', 2],
		4: [12, 15, 1200, 2700, 'count', 2],
		5: [12, 15, 1000, 2500, 'count', 3],
		6: [15, 18, 800, 2200, 'count', 3],
		7: [15, 18, 600, 1900, 'count', 3],
		8: [18, 20, 400, 1600, 'count', 4],
		9: [18, 20, 300, 1500, 'count', 4],
		10: [20, 20, 300, 1500, 'count', 4]
	};

	let simpleTrials, choiceTrials, delayMin, delayMax, earlyClickPenalty, choiceShapeCount;
	let simpleCurrentTrial = 0,
		simpleRTs = [],
		simpleWaiting = false,
		simpleReady = false;
	let simpleStartTime = 0,
		simpleTimeout,
		earlyClickCount = 0;
	let choiceCurrentTrial = 0,
		choiceRTs = [],
		choiceAccuracy = [],
		choiceStimuli = [];
	let choiceCurrentShape = '',
		choiceStartTime = 0;
	let validSimpleRTs = [],
		finalScore = 0;

	function t(text) {
		return translateText(text ?? '', $locale);
	}

	function lt(en, bn) {
		return localeText({ en, bn }, $locale);
	}

	function n(value, options = {}) {
		return formatNumber(value, $locale, options);
	}

	function shapeLabel(shape) {
		const labels = {
			circle: t('Circle'),
			square: t('Square'),
			triangle: t('Triangle'),
			diamond: t('Diamond')
		};

		return labels[shape] || shape;
	}

	function trialLabel(current, total) {
		return lt(`Trial ${current} / ${total}`, `ট্রায়াল ${n(current)} / ${n(total)}`);
	}

	function trainingProgressText() {
		return lt(
			`Training Progress: ${completedTasksCount} / 4 tasks completed`,
			`ট্রেনিং অগ্রগতি: ${n(completedTasksCount)} / ৪টি টাস্ক সম্পন্ন`
		);
	}

	function msText(value) {
		return `${n(value)}${lt('ms', 'মি.সে')}`;
	}

	onMount(() => {
		if (!$user) return goto('/login');

		isTrainingMode = $page.url.searchParams.get('training') === 'true';
		trainingPlanId = parseInt($page.url.searchParams.get('planId')) || null;
		trainingDifficulty = parseInt($page.url.searchParams.get('difficulty')) || 1;
		taskId = $page.url.searchParams.get('taskId');

		const [st, ct, dMin, dMax, penalty, shapeCount] = CONFIG[trainingDifficulty] || CONFIG[1];
		[simpleTrials, choiceTrials, delayMin, delayMax, earlyClickPenalty, choiceShapeCount] = [
			st,
			ct,
			dMin,
			dMax,
			penalty,
			shapeCount
		];
	});

	function startSimpleTest() {
		stage = 'simple';
		simpleCurrentTrial = 0;
		simpleRTs = [];
		earlyClickCount = 0;
		nextSimpleTrial();
	}

	function nextSimpleTrial() {
		if (simpleCurrentTrial >= simpleTrials) {
			startChoiceTest();
			return;
		}

		simpleWaiting = true;
		simpleReady = false;
		const delay = delayMin + Math.random() * (delayMax - delayMin);
		simpleTimeout = setTimeout(() => {
			simpleReady = true;
			simpleWaiting = false;
			simpleStartTime = Date.now();
		}, delay);
	}

	function handleSimpleClick() {
		if (simpleWaiting) {
			clearTimeout(simpleTimeout);
			earlyClickCount++;

			if (earlyClickPenalty === 'retry') {
				alert(t('Too early! Wait for the green screen. Try again.'));
				nextSimpleTrial();
			} else {
				simpleRTs.push(9999);
				alert(
					$locale === 'bn'
						? `খুব তাড়াতাড়ি ক্লিক করেছেন! (আগাম ক্লিক: ${n(earlyClickCount)})`
						: `Too early! (Early clicks: ${earlyClickCount})`
				);
				simpleCurrentTrial++;
				nextSimpleTrial();
			}
		} else if (simpleReady) {
			const rt = Date.now() - simpleStartTime;
			simpleRTs.push(rt);
			simpleReady = false;
			simpleCurrentTrial++;
			nextSimpleTrial();
		}
	}

	function startChoiceTest() {
		stage = 'choice';
		choiceCurrentTrial = 0;
		choiceRTs = [];
		choiceAccuracy = [];
		const shapes = ['circle', 'square'];
		if (choiceShapeCount >= 3) shapes.push('triangle');
		if (choiceShapeCount >= 4) shapes.push('diamond');
		choiceStimuli = [];
		for (let i = 0; i < choiceTrials; i++) {
			choiceStimuli.push(shapes[Math.floor(Math.random() * shapes.length)]);
		}
		nextChoiceTrial();
	}

	function nextChoiceTrial() {
		if (choiceCurrentTrial >= choiceTrials) {
			calculateResults();
			return;
		}
		choiceCurrentShape = choiceStimuli[choiceCurrentTrial];
		choiceStartTime = Date.now();
	}

	function handleChoiceResponse(response) {
		const rt = Date.now() - choiceStartTime;
		const correct = response === choiceCurrentShape;
		choiceRTs.push(rt);
		choiceAccuracy.push(correct);
		choiceCurrentTrial++;
		nextChoiceTrial();
	}

	function calculateResults() {
		validSimpleRTs = simpleRTs.filter((rt) => rt < 9000);
		const simpleRTMean = validSimpleRTs.length
			? validSimpleRTs.reduce((a, b) => a + b) / validSimpleRTs.length
			: 0;
		const simpleRTStd = calculateStd(validSimpleRTs);
		const choiceRTMean = choiceRTs.length
			? choiceRTs.reduce((a, b) => a + b) / choiceRTs.length
			: 0;
		const choiceAccScore = choiceAccuracy.filter((a) => a).length / choiceAccuracy.length;
		finalScore = calculateProcessingSpeedScore(
			simpleRTMean,
			choiceRTMean,
			simpleRTStd,
			choiceAccScore
		);
		stage = 'results';
		saveResults(simpleRTMean, simpleRTStd, choiceRTMean, choiceAccScore);
	}

	async function saveResults(simpleRTMean, simpleRTStd, choiceRTMean, choiceAccScore) {
		try {
			const rawData = {
				simple_rt_mean: simpleRTMean,
				simple_rt_std: simpleRTStd,
				simple_trials: validSimpleRTs.length,
				choice_rt_mean: choiceRTMean,
				choice_rt_std: calculateStd(choiceRTs),
				choice_accuracy: choiceAccScore,
				choice_trials: choiceTrials
			};
			if (isTrainingMode && trainingPlanId) {
				const result = await training.submitSession({
					user_id: $user.id,
					training_plan_id: trainingPlanId,
					domain: 'processing_speed',
					task_type: 'reaction_time',
					score: finalScore,
					accuracy: choiceAccScore * 100,
					average_reaction_time: (simpleRTMean + choiceRTMean) / 2,
					consistency: simpleRTStd > 0 ? Math.max(0, 100 - simpleRTStd / 10) : 100,
					errors: choiceAccuracy.filter((a) => !a).length,
					session_duration: 2,
					task_id: taskId
				});
				sessionComplete = result.session_complete;
				completedTasksCount = result.completed_tasks;
			} else {
				await tasks.submitResult(
					$user.id,
					'processing_speed',
					finalScore,
					JSON.stringify(rawData)
				);
			}
		} catch (error) {
			console.error('Error saving results:', error);
		}
	}

	function calculateStd(arr) {
		if (arr.length === 0) return 0;
		const mean = arr.reduce((a, b) => a + b, 0) / arr.length;
		const variance =
			arr.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / arr.length;
		return Math.sqrt(variance);
	}

	function calculateProcessingSpeedScore(simpleRT, choiceRT, simpleStd, choiceAcc) {
		let simpleScore = 0;
		if (simpleRT <= 190) simpleScore = 36 + ((190 - simpleRT) / 40) * 4;
		else if (simpleRT <= 250) simpleScore = 28 + ((250 - simpleRT) / 60) * 8;
		else if (simpleRT <= 310) simpleScore = 16 + ((310 - simpleRT) / 60) * 12;
		else if (simpleRT <= 400) simpleScore = 4 + ((400 - simpleRT) / 90) * 12;
		else simpleScore = Math.max(0, 4 - ((simpleRT - 400) / 100) * 4);

		let choiceSpeedScore = 0;
		if (choiceRT <= 330) choiceSpeedScore = 27 + ((330 - choiceRT) / 50) * 3;
		else if (choiceRT <= 430) choiceSpeedScore = 21 + ((430 - choiceRT) / 100) * 6;
		else if (choiceRT <= 530) choiceSpeedScore = 12 + ((530 - choiceRT) / 100) * 9;
		else if (choiceRT <= 650) choiceSpeedScore = 3 + ((650 - choiceRT) / 120) * 9;
		else choiceSpeedScore = Math.max(0, 3 - ((choiceRT - 650) / 150) * 3);

		const choiceAccuracyScore = choiceAcc * 10;
		let consistencyScore = 0;
		if (simpleStd <= 30) consistencyScore = 18 + ((30 - simpleStd) / 30) * 2;
		else if (simpleStd <= 50) consistencyScore = 14 + ((50 - simpleStd) / 20) * 4;
		else if (simpleStd <= 80) consistencyScore = 8 + ((80 - simpleStd) / 30) * 6;
		else if (simpleStd <= 120) consistencyScore = 2 + ((120 - simpleStd) / 40) * 6;
		else consistencyScore = Math.max(0, 2 - ((simpleStd - 120) / 60) * 2);
		return Math.min(100, simpleScore + choiceSpeedScore + choiceAccuracyScore + consistencyScore);
	}

	function backToDashboard() {
		goto(isTrainingMode ? '/training' : '/dashboard');
	}
</script>

<div class="test-container" data-localize-skip>
	{#if stage === 'intro'}
		<div class="test-card">
			<h1>{t('Processing Speed Test')}</h1>
			<h2 style="color: #666; font-size: 20px; margin-bottom: 30px;">
				{t('Reaction Time Assessment')}
			</h2>
			<div style="text-align: left; max-width: 600px; margin: 0 auto;">
				<h3 style="color: #667eea; margin-bottom: 15px;">{t('Two-Part Test:')}</h3>
				<div style="background: #f0f7ff; padding: 20px; border-radius: 8px; margin: 15px 0;">
					<h4 style="color: #667eea; margin-bottom: 10px;">
						{t('Part 1: Simple Reaction Time')}
					</h4>
					<ul style="line-height: 1.8; color: #666;">
						<li>
							{@html lt(
								'Screen will turn <strong style="color: #4caf50;">GREEN</strong>',
								'স্ক্রিন <strong style="color: #4caf50;">সবুজ</strong> হবে'
							)}
						</li>
						<li>{t('Click as fast as possible when it turns green')}</li>
						<li>{t("Don't click before it turns green!")}</li>
						<li>{lt(`${n(simpleTrials)} trials`, `${n(simpleTrials)}টি ট্রায়াল`)}</li>
					</ul>
				</div>
				<div style="background: #fff3e0; padding: 20px; border-radius: 8px; margin: 15px 0;">
					<h4 style="color: #ff9800; margin-bottom: 10px;">
						{t('Part 2: Choice Reaction Time')}
					</h4>
					<ul style="line-height: 1.8; color: #666;">
						{#if choiceShapeCount === 2}
							<li>
								{@html lt(
									`You'll see a <strong>${shapeLabel('circle')} ⭕</strong> or <strong>${shapeLabel('square')} ⬜</strong>`,
									`আপনি দেখবেন <strong>${shapeLabel('circle')} ⭕</strong> অথবা <strong>${shapeLabel('square')} ⬜</strong>`
								)}
							</li>
						{:else if choiceShapeCount === 3}
							<li>
								{@html lt(
									`You'll see <strong>${shapeLabel('circle')} ⭕</strong>, <strong>${shapeLabel('square')} ⬜</strong>, or <strong>${shapeLabel('triangle')} 🔺</strong>`,
									`আপনি দেখবেন <strong>${shapeLabel('circle')} ⭕</strong>, <strong>${shapeLabel('square')} ⬜</strong>, অথবা <strong>${shapeLabel('triangle')} 🔺</strong>`
								)}
							</li>
						{:else}
							<li>
								{@html lt(
									`You'll see <strong>${shapeLabel('circle')} ⭕</strong>, <strong>${shapeLabel('square')} ⬜</strong>, <strong>${shapeLabel('triangle')} 🔺</strong>, or <strong>${shapeLabel('diamond')} 🔶</strong>`,
									`আপনি দেখবেন <strong>${shapeLabel('circle')} ⭕</strong>, <strong>${shapeLabel('square')} ⬜</strong>, <strong>${shapeLabel('triangle')} 🔺</strong>, অথবা <strong>${shapeLabel('diamond')} 🔶</strong>`
								)}
							</li>
						{/if}
						<li>{t('Click the matching button as fast as possible')}</li>
						<li>{t('Fast AND accurate!')}</li>
						<li>{lt(`${n(choiceTrials)} trials`, `${n(choiceTrials)}টি ট্রায়াল`)}</li>
					</ul>
				</div>
			</div>
			<button class="btn-primary" on:click={startSimpleTest} style="margin-top: 40px;">
				{t('Start Test')}
			</button>
			<button class="btn-secondary" on:click={backToDashboard}>
				{t('Back to Dashboard')}
			</button>
		</div>
	{:else if stage === 'simple'}
		<div
			class="test-card"
			style="background: {simpleReady ? GREEN_COLOR : '#fff'}; transition: background 0.1s; cursor: pointer; min-height: 400px; display: flex; flex-direction: column; justify-content: center;"
			on:click={handleSimpleClick}
		>
			<div class="timer" style="color: {simpleReady ? 'white' : '#666'};">
				{trialLabel(simpleCurrentTrial + 1, simpleTrials)}
			</div>
			{#if simpleWaiting}
				<h2 style="color: #666; margin-top: 40px;">{t('Wait...')}</h2>
			{:else if simpleReady}
				<h1 style="color: white; font-size: 48px; margin-top: 40px;">{t('CLICK NOW!')}</h1>
			{:else}
				<h2 style="color: #666; margin-top: 40px;">{t('Get ready...')}</h2>
			{/if}
			<p style="color: {simpleReady ? 'white' : '#999'}; margin-top: 30px;">
				{simpleReady ? t('Click anywhere!') : t('Wait for green screen')}
			</p>
		</div>
	{:else if stage === 'choice'}
		<div class="test-card">
			<div class="timer">{trialLabel(choiceCurrentTrial + 1, choiceTrials)}</div>
			<div style="margin: 60px 0;">
				{#if choiceCurrentShape === 'circle'}
					<div
						style="width: 150px; height: 150px; border-radius: 50%; background: #2196f3; margin: 0 auto;"
					></div>
				{:else if choiceCurrentShape === 'square'}
					<div style="width: 150px; height: 150px; background: #ff9800; margin: 0 auto;"></div>
				{:else if choiceCurrentShape === 'triangle'}
					<div
						style="width: 0; height: 0; border-left: 75px solid transparent; border-right: 75px solid transparent; border-bottom: 130px solid #4caf50; margin: 0 auto;"
					></div>
				{:else if choiceCurrentShape === 'diamond'}
					<div
						style="width: 106px; height: 106px; background: #9c27b0; transform: rotate(45deg); margin: 22px auto;"
					></div>
				{/if}
			</div>
			<div
				style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap; max-width: 600px; margin: 40px auto 0;"
			>
				<button
					class="btn-primary"
					on:click={() => handleChoiceResponse('circle')}
					style="font-size: 16px; padding: 15px 30px; min-width: 140px;"
				>
					⭕ {shapeLabel('circle')}
				</button>
				<button
					class="btn-primary"
					on:click={() => handleChoiceResponse('square')}
					style="font-size: 16px; padding: 15px 30px; min-width: 140px;"
				>
					⬜ {shapeLabel('square')}
				</button>
				{#if choiceShapeCount >= 3}
					<button
						class="btn-primary"
						on:click={() => handleChoiceResponse('triangle')}
						style="font-size: 16px; padding: 15px 30px; min-width: 140px;"
					>
						🔺 {shapeLabel('triangle')}
					</button>
				{/if}
				{#if choiceShapeCount >= 4}
					<button
						class="btn-primary"
						on:click={() => handleChoiceResponse('diamond')}
						style="font-size: 16px; padding: 15px 30px; min-width: 140px;"
					>
						🔶 {shapeLabel('diamond')}
					</button>
				{/if}
			</div>
		</div>
	{:else if stage === 'results'}
		<div class="test-card">
			<h1>{t('Test Complete!')}</h1>
			{#if isTrainingMode}
				<div class="training-progress-banner">
					{#if sessionComplete}
						<div class="session-complete-msg">{t('🎉 Session Complete! All 4 tasks finished.')}</div>
					{:else}
						<div style="background: white; padding: 15px; border-radius: 8px; margin: 0;">
							<div
								style="color: #667eea; font-weight: 700; font-size: 16px; margin-bottom: 5px;"
							>
								{trainingProgressText()}
							</div>
							<div style="color: #666; font-size: 14px;">
								{t('Continue with the remaining tasks to complete this session')}
							</div>
						</div>
					{/if}
				</div>
			{/if}
			<div class="score-display">
				{n(finalScore.toFixed(1), { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%
			</div>
			<div class="result-details">
				<p style="background: #e3f2fd; padding: 15px; border-radius: 6px;">
					<strong style="color: #2196f3;">{t('Part 1: Simple Reaction Time')}</strong>
				</p>
				<p>
					<span>{t('Average RT:')}</span>
					<strong>{msText((validSimpleRTs.reduce((a, b) => a + b, 0) / validSimpleRTs.length || 0).toFixed(0))}</strong>
				</p>
				<p>
					<span>{t('Consistency:')}</span>
					<strong>{msText(calculateStd(validSimpleRTs).toFixed(0))}</strong>
				</p>
				<p>
					<span>{t('Valid Trials:')}</span>
					<strong>{n(validSimpleRTs.length)}/{n(simpleTrials)}</strong>
				</p>
				{#if earlyClickCount > 0}
					<p style="color: #ff9800;">
						<span>{t('Early Clicks:')}</span>
						<strong>{n(earlyClickCount)}</strong>
					</p>
				{/if}
				<p style="background: #fff3e0; padding: 15px; border-radius: 6px; margin-top: 20px;">
					<strong style="color: #ff9800;">{t('Part 2: Choice Reaction Time')}</strong>
				</p>
				<p>
					<span>{t('Average RT:')}</span>
					<strong>{msText((choiceRTs.reduce((a, b) => a + b, 0) / choiceRTs.length || 0).toFixed(0))}</strong>
				</p>
				<p>
					<span>{t('Accuracy:')}</span>
					<strong>{n(((choiceAccuracy.filter((a) => a).length / choiceAccuracy.length) * 100).toFixed(1), {
						minimumFractionDigits: 1,
						maximumFractionDigits: 1
					})}%</strong>
				</p>
				<p>
					<span>{t('Correct:')}</span>
					<strong>{n(choiceAccuracy.filter((a) => a).length)}/{n(choiceTrials)}</strong>
				</p>
			</div>
			<div style="margin-top: 40px;">
				<button class="btn-primary" on:click={backToDashboard}>{t('Back to Dashboard')}</button>
			</div>
		</div>
	{/if}
</div>

<svelte:head>
	<title>{lt('Processing Speed Test - NeuroBloom', 'প্রসেসিং স্পিড টেস্ট - NeuroBloom')}</title>
</svelte:head>

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
		0% {
			transform: scale(0.9);
			opacity: 0;
		}
		50% {
			transform: scale(1.05);
		}
		100% {
			transform: scale(1);
			opacity: 1;
		}
	}
</style>

<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
	import { formatNumber, formatPercent, locale, translateText } from '$lib/i18n';
	import { user } from '$lib/stores';
	import { buildPracticePayload, getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
	import { onDestroy, onMount } from 'svelte';

	let phase = 'intro';
	let loading = false;
	let error = null;
	let sessionData = null;
	let difficulty = 1;
	let baselineFlexibility = null;
	let currentPhase = null;
	let currentPhaseIndex = 0;
	let currentTrialIndex = 0;
	let responses = [];
	let startTime = null;
	let trialStartTime = null;
	let showCue = false;
	let cueText = '';
	let cueTimeout = null;
	let results = null;
	let newBadges = [];
	let currentUser = null;
	let taskId = null;
	/** @type {string} */
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';
	let recordedSessionData = null;
	let recordedDifficulty = 1;

	const COLORS = {
		red: '#EF4444',
		blue: '#3B82F6'
	};

	user.subscribe((value) => {
		currentUser = value;
	});

	function cloneData(value) {
		if (typeof structuredClone === 'function') {
			return structuredClone(value);
		}
		return JSON.parse(JSON.stringify(value));
	}

	function restoreRecordedSession() {
		if (recordedSessionData) {
			sessionData = cloneData(recordedSessionData);
		}
		difficulty = recordedDifficulty;
	}

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
		if (size === 'large') return $locale === 'bn' ? 'বড়' : 'large';
		return t(size || '');
	}

	function cueInstruction(rule) {
		if ($locale === 'bn') {
			return `${ruleName(rule)} অনুযায়ী সাজান`;
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
			if (rule === 'size') return 'বড় কার্ড এক স্তূপে যাবে, ছোট অন্য স্তূপে';
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
		return $locale === 'bn' ? `ট্রায়াল ${n(current)} / ${n(total)}` : `Trial ${current} / ${total}`;
	}

	function difficultyDescription() {
		const cueDuration = sessionData?.config?.cue_duration_ms || 0;
		if ($locale === 'bn') {
			if (difficulty <= 4) return `প্রাথমিক স্তর: রঙ ও আকৃতি অনুযায়ী সাজানো, ${durationMsLabel(cueDuration)} সংকেত`;
			if (difficulty <= 7) return `মধ্যম স্তর: আকারের মাত্রা যোগ হয়েছে, ${durationMsLabel(cueDuration)} সংকেত`;
			return `উন্নত স্তর: সব মাত্রা সক্রিয়, দ্রুত ${durationMsLabel(cueDuration)} সংকেত`;
		}
		if (difficulty <= 4) return `Basic: Color & Shape sorting, ${cueDuration}ms cues`;
		if (difficulty <= 7) return `Intermediate: Added size dimension, ${cueDuration}ms cues`;
		return `Advanced: All dimensions, rapid ${cueDuration}ms cues`;
	}

	function transitionMessage() {
		if (currentPhaseIndex === 1) {
			if ($locale === 'bn') {
				return `এখন ${ruleName(phaseRule(1))} নয়, ${ruleName(phaseRule(2))} অনুযায়ী সাজান। ${ruleExample(phaseRule(2))}।`;
			}
			return `Now switch to ${cueInstruction(phaseRule(2)).toLowerCase()} instead of ${ruleName(phaseRule(1)).toLowerCase()}. ${ruleExample(phaseRule(2))[0].toUpperCase()}${ruleExample(phaseRule(2)).slice(1)}.`;
		}
		if (currentPhaseIndex === 2) {
			if ($locale === 'bn') {
				return `এবার প্রতিটি ট্রায়ালের আগে দেখানো সংকেত লক্ষ্য করুন। সেখানে ${ruleName(phaseRule(1))} নাকি ${ruleName(phaseRule(2))} অনুযায়ী সাজাতে হবে, তা বলা থাকবে।`;
			}
			return `In this phase, a cue will tell you which rule to use. Pay attention to whether it says "${ruleName(phaseRule(1))}" or "${ruleName(phaseRule(2))}"`;
		}
		return '';
	}

	async function loadSession() {
		try {
			loading = true;
			error = null;

			const urlDifficulty = $page.url.searchParams.get('difficulty');
			if (urlDifficulty) {
				difficulty = parseInt(urlDifficulty);
			} else {
				const baselineResponse = await fetch(
					`http://localhost:8000/api/baseline/${currentUser.id}`
				);
				if (baselineResponse.ok) {
					const baselineData = await baselineResponse.json();
					baselineFlexibility = baselineData.flexibility;
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
			}

			const response = await fetch(
				`http://localhost:8000/api/tasks/dccs/generate?difficulty=${difficulty}`,
				{ method: 'POST', headers: { 'Content-Type': 'application/json' } }
			);
			if (!response.ok) throw new Error('Failed to load session');
			sessionData = await response.json();
			recordedSessionData = cloneData(sessionData);
			difficulty = sessionData.difficulty;
			recordedDifficulty = difficulty;
		} catch (err) {
			error = err.message;
		} finally {
			loading = false;
		}
	}

	/** @param {string} nextMode */
	function startTask(nextMode = TASK_PLAY_MODE.RECORDED) {
		if (cueTimeout) {
			clearTimeout(cueTimeout);
			cueTimeout = null;
		}

		playMode = nextMode;
		practiceStatusMessage = '';
		restoreRecordedSession();
		if (playMode === TASK_PLAY_MODE.PRACTICE) {
			sessionData = buildPracticePayload('dccs', recordedSessionData);
		}
		currentPhaseIndex = 0;
		currentTrialIndex = 0;
		responses = [];
		results = null;
		showCue = false;
		currentPhase = sessionData.phases.phase1;
		phase = 'task';
		startTime = Date.now();
		startTrial();
	}

	function startTrial() {
		trialStartTime = Date.now();
		const trial = getCurrentTrial();
		if (cueTimeout) {
			clearTimeout(cueTimeout);
			cueTimeout = null;
		}
		if (trial && trial.cue_shown) {
			showCue = true;
			cueText = cueInstruction(trial.rule);
			cueTimeout = setTimeout(() => {
				cueTimeout = null;
				showCue = false;
			}, sessionData.config.cue_duration_ms);
		}
	}

	async function leavePractice(completed = false) {
		if (cueTimeout) {
			clearTimeout(cueTimeout);
			cueTimeout = null;
		}

		playMode = TASK_PLAY_MODE.RECORDED;
		practiceStatusMessage = completed ? getPracticeCopy($locale).complete : '';
		currentPhase = null;
		currentPhaseIndex = 0;
		currentTrialIndex = 0;
		responses = [];
		showCue = false;
		cueText = '';
		results = null;
		startTime = null;
		trialStartTime = null;
		phase = 'intro';

		if (completed) {
			await loadSession();
		} else {
			restoreRecordedSession();
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
		if (currentTrialIndex >= currentPhase.trials.length) {
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
				submitSession();
				return;
			}
		} else {
			startTrial();
		}
	}

	function continueToNextPhase() {
		phase = 'task';
		startTrial();
	}

	async function submitSession() {
		if (playMode === TASK_PLAY_MODE.PRACTICE) {
			await leavePractice(true);
			return;
		}

		try {
			loading = true;
			error = null;
			taskId = $page.url.searchParams.get('taskId');
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
				throw new Error(`Failed to submit result: ${submitResponse.status} ${errorText}`);
			}
			const submitData = await submitResponse.json();
			results = submitData;
			newBadges = submitData.newly_earned_badges || [];
			phase = 'results';
		} catch (err) {
			error = err.message || 'Network error - please check if the backend server is running';
		} finally {
			loading = false;
		}
	}

	onDestroy(() => {
		if (cueTimeout) {
			clearTimeout(cueTimeout);
			cueTimeout = null;
		}
	});

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

<div class="dccs-container">

	<!-- ── LOADING ────────────────────────────────────────────── -->
	{#if loading && phase === 'intro'}
		<div class="loading-wrap">
			<LoadingSkeleton />
		</div>

	<!-- ── ERROR ─────────────────────────────────────────────── -->
	{:else if error}
		<div class="page-wrapper">
			<div class="error-card">
				<p class="error-msg">{t('Error:')} {error}</p>
				<button class="btn-retry" on:click={loadSession}>{t('Retry')}</button>
			</div>
		</div>

	<!-- ── INTRO ──────────────────────────────────────────────── -->
	{:else if phase === 'intro'}
		<div class="page-wrapper">

			<!-- Title row -->
			<div class="task-title-row">
				<div>
					<h1>{t('Dimensional Change Card Sort')}</h1>
					<p class="task-subtitle">{t('DCCS — Cognitive Flexibility & Rule Switching')}</p>
				</div>
				<DifficultyBadge {difficulty} domain="Cognitive Flexibility" />
			</div>

			<!-- Concept card -->
			<div class="card task-concept">
				<div class="concept-badge">{t('Cognitive Flexibility Assessment')}</div>
				<p class="concept-body">
					{$locale === 'bn'
						? 'কার্ড বাছাই করুন, নিয়ম পরিবর্তনের সাথে মানিয়ে নিন। তিনটি ধাপে রঙ ও আকৃতি অনুযায়ী সাজান — মাঝে নিয়ম পরিবর্তন হবে। এটি সেট-শিফটিং এবং ইনহিবিটরি কন্ট্রোল পরিমাপ করে।'
						: 'Sort cards and adapt as the rule changes. Work through three phases using color and shape rules — the rule switches between phases. This measures cognitive set-shifting and inhibitory control.'}
				</p>
			</div>

			<!-- Phases overview -->
			<div class="card">
				<h2 class="section-title">{t('Three-Phase Structure')}</h2>
				<div class="phases-row">
					<div class="phase-block phase1">
						<div class="phase-num">1</div>
						<p class="phase-label">{t('Pre-Switch')}</p>
						<p class="phase-rule">{cueInstruction(phaseRule(1))}</p>
						<p class="phase-eg">{ruleExample(phaseRule(1))}</p>
					</div>
					<div class="phase-arrow">\u2192</div>
					<div class="phase-block phase2">
						<div class="phase-num">2</div>
						<p class="phase-label">{t('Post-Switch')}</p>
						<p class="phase-rule">{cueInstruction(phaseRule(2))}</p>
						<p class="phase-eg">{ruleExample(phaseRule(2))}</p>
					</div>
					<div class="phase-arrow">\u2192</div>
					<div class="phase-block phase3">
						<div class="phase-num">3</div>
						<p class="phase-label">{t('Mixed')}</p>
						<p class="phase-rule">{t('Per-trial cue')}</p>
						<p class="phase-eg">{$locale === 'bn' ? 'কখনো রঙ, কখনো আকৃতি' : 'Color or Shape — cue tells you'}</p>
					</div>
				</div>
			</div>

			<!-- Rules grid -->
			<div class="card">
				<h2 class="section-title">{t('How It Works')}</h2>
				<div class="rules-grid">
					<div class="rule-item">
						<div class="rule-num fuchsia">1</div>
						<div class="rule-body">
							<strong>{t('Cards Have Two Features')}</strong>
							<span>{t('Each card has a color (red or blue) and a shape (circle or star)')}</span>
						</div>
					</div>
					<div class="rule-item">
						<div class="rule-num fuchsia">2</div>
						<div class="rule-body">
							<strong>{t('Click the Matching Target')}</strong>
							<span>{t('Two target cards are shown. Click the one that matches the rule.')}</span>
						</div>
					</div>
					<div class="rule-item">
						<div class="rule-num fuchsia">3</div>
						<div class="rule-body">
							<strong>{t('Rules Switch Between Phases')}</strong>
							<span>{t('Phase 1 uses one rule; Phase 2 switches to a new rule. Ignore your old response pattern.')}</span>
						</div>
					</div>
					<div class="rule-item">
						<div class="rule-num fuchsia">4</div>
						<div class="rule-body">
							<strong>{t('Watch the Cue in Phase 3')}</strong>
							<span>{t('In the mixed phase, a brief cue flashes before each card. It tells you which rule to use.')}</span>
						</div>
					</div>
				</div>
			</div>

			<!-- Info grid -->
			<div class="info-grid">
				<div class="card">
					<h3 class="card-heading">{t('Session Details')}</h3>
					<ul class="detail-list">
						<li>
							<span class="dl-label">{t('Difficulty')}</span>
							<span class="dl-value fuchsia-val">{levelLabel()}</span>
						</li>
						<li>
							<span class="dl-label">{t('Total Trials')}</span>
							<span class="dl-value">{n(sessionData ? sessionData.total_trials : 40)}</span>
						</li>
						<li>
							<span class="dl-label">{t('Cue Duration')}</span>
							<span class="dl-value">{durationMsLabel(sessionData?.config?.cue_duration_ms || 0)}</span>
						</li>
						<li>
							<span class="dl-label">{t('Phases')}</span>
							<span class="dl-value">{t('3 phases')}</span>
						</li>
					</ul>
					<p class="diff-desc">{difficultyDescription()}</p>
					{#if baselineFlexibility !== null && baselineFlexibility !== undefined}
						<p class="baseline-note">
							{$locale === 'bn'
								? `ফ্লেক্সিবিলিটি বেসলাইন: ${n(baselineFlexibility.toFixed(0))}/100`
								: `Flexibility baseline: ${baselineFlexibility.toFixed(0)}/100`}
						</p>
					{/if}
				</div>
				<div class="card">
					<h3 class="card-heading">{t('What It Measures')}</h3>
					<ul class="measure-list">
						<li><span class="dot fuchsia"></span><div><strong>{t('Set-Shifting')}</strong><p>{t('Switching between active sorting rules')}</p></div></li>
						<li><span class="dot fuchsia"></span><div><strong>{t('Cognitive Flexibility')}</strong><p>{t('Adapting to new task demands')}</p></div></li>
						<li><span class="dot fuchsia"></span><div><strong>{t('Inhibitory Control')}</strong><p>{t('Suppressing the previously rewarded response')}</p></div></li>
						<li><span class="dot fuchsia"></span><div><strong>{t('Switch Cost')}</strong><p>{t('Reaction time penalty when the rule changes')}</p></div></li>
					</ul>
				</div>
			</div>

			<!-- Clinical info -->
			<div class="card clinical-info">
				<h3 class="card-heading">{t('Clinical Significance')}</h3>
				<div class="clinical-grid">
					<div class="clinical-item">
						<span class="ci-label">{t('Validated By')}</span>
						<span>Zelazo (2006); {t('developmental and clinical research')}</span>
					</div>
					<div class="clinical-item">
						<span class="ci-label">{t('MS Relevance')}</span>
						<span>{t('Sensitive to MS-related executive and frontal lobe dysfunction')}</span>
					</div>
					<div class="clinical-item">
						<span class="ci-label">{t('Key Metric')}</span>
						<span>{t('Switch Cost = extra reaction time when rule changes; Perseverative errors = stuck on old rule')}</span>
					</div>
					<div class="clinical-item">
						<span class="ci-label">{t('Advantage')}</span>
						<span>{t('Simpler and less frustrating than WCST; clear rule-switching paradigm')}</span>
					</div>
				</div>
			</div>

			<!-- Performance guide -->
			<div class="card perf-guide">
				<h3 class="card-heading">{t('Performance Guide — Switch Cost')}</h3>
				<div class="norm-bars">
					<div class="norm-bar">
						<span class="norm-label">{t('Excellent')}</span>
						<div class="norm-track"><div class="norm-fill fuchsia-fill" style="width:25%"></div></div>
						<span class="norm-val">&lt; 100ms</span>
					</div>
					<div class="norm-bar">
						<span class="norm-label">{t('Good')}</span>
						<div class="norm-track"><div class="norm-fill fuchsia-mid" style="width:50%"></div></div>
						<span class="norm-val">100–200ms</span>
					</div>
					<div class="norm-bar">
						<span class="norm-label">{t('Developing')}</span>
						<div class="norm-track"><div class="norm-fill fuchsia-low" style="width:75%"></div></div>
						<span class="norm-val">&gt; 200ms</span>
					</div>
				</div>
			</div>

			<div class="btn-row">
				<TaskPracticeActions
					locale={$locale}
					startLabel={t('Start DCCS Test')}
					statusMessage={practiceStatusMessage}
					on:start={() => startTask(TASK_PLAY_MODE.RECORDED)}
					on:practice={() => startTask(TASK_PLAY_MODE.PRACTICE)}
				/>
			</div>
		</div>

	<!-- ── PHASE TRANSITION ───────────────────────────────────── -->
	{:else if phase === 'phase-transition'}
		<div class="trial-wrapper">
			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
			{/if}

			<div class="transition-card">
				<div class="transition-badge">
					{phaseTitle(currentPhaseIndex + 1)}
				</div>
				<h2 class="transition-title">{t('Rule Change')}</h2>
				<p class="transition-msg">{transitionMessage()}</p>

				<div class="transition-rule-box">
					<span class="trb-label">{t('New Rule:')}</span>
					<span class="trb-rule">{phaseInstructionLabel(currentPhaseIndex === 1 ? { name: 'normal', rule: phaseRule(2) } : { name: 'mixed' })}</span>
				</div>

				<button class="start-button" on:click={continueToNextPhase}>
					{t('Continue')}
				</button>
			</div>
		</div>

	<!-- ── TASK ───────────────────────────────────────────────── -->
	{:else if phase === 'task'}
		{#if currentPhase && getCurrentTrial()}
			{@const trial = getCurrentTrial()}
			{@const phaseNum = currentPhaseIndex + 1}
			{@const totalTrials = currentPhase.total_trials}
			{@const trialNum = currentTrialIndex + 1}

			<div class="trial-wrapper">
				{#if playMode === TASK_PLAY_MODE.PRACTICE}
					<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
				{/if}

				<!-- Status row -->
				<div class="test-status-row">
					<div class="phase-pill">
						{phaseProgressLabel(phaseNum, 3)}
					</div>
					<div class="trial-pill">
						{trialProgressLabel(trialNum, totalTrials)}
					</div>
				</div>

				<!-- Progress bar -->
				<div class="progress-track">
					<div class="progress-fill" style="width:{(trialNum / totalTrials) * 100}%"></div>
				</div>

				<!-- Rule instruction -->
				<div class="rule-banner">
					<span class="rb-label">{t('Current Rule:')}</span>
					<span class="rb-rule">{phaseInstructionLabel(currentPhase)}</span>
				</div>

				<!-- Cue flash -->
				{#if showCue}
					<div class="cue-flash">
						<p class="cue-text">{cueText}</p>
					</div>
				{/if}

				<!-- Test card -->
				<div class="card-area">
					<p class="area-label">{t('Test Card')}</p>
					<div class="stimulus-card test-card">
						{@html renderCard(trial.card, 100)}
						{#if sessionData.config.use_size_dimension && trial.card.size}
							<p class="size-tag">
								{$locale === 'bn' ? `আকার: ${sizeLabel(trial.card.size)}` : `Size: ${sizeLabel(trial.card.size)}`}
							</p>
						{/if}
					</div>
				</div>

				<!-- Targets -->
				<div class="targets-area">
					<p class="area-label">{t('Click the matching card:')}</p>
					<div class="targets-row">
						{#each sessionData.target_cards as target}
							<button
								class="target-btn"
								on:click={() => handleTargetSelection(target.id)}
							>
								{@html renderCard(target, 100)}
								{#if sessionData.config.use_size_dimension && target.size}
									<p class="size-tag">
										{$locale === 'bn' ? `আকার: ${sizeLabel(target.size)}` : `Size: ${sizeLabel(target.size)}`}
									</p>
								{/if}
							</button>
						{/each}
					</div>
				</div>
			</div>
		{/if}

	<!-- ── RESULTS ─────────────────────────────────────────────── -->
	{:else if phase === 'results'}
		<div class="page-wrapper">

			{#if newBadges && newBadges.length > 0}
				<BadgeNotification badges={newBadges} />
			{/if}

			<!-- Header -->
			<div class="results-header">
				<h1>{t('DCCS Complete')}</h1>
				<div class="score-pill">
					{t('Score')}: {n(results.score)}
				</div>
				<p class="overall-acc">{t('Overall Accuracy')}: {accuracyLabel(results.accuracy)}</p>
			</div>

			<!-- Phase cards -->
			{#if results.phases}
				<div class="phase-results-grid">
					{#if results.phases.phase1}
						<div class="phase-result-card pr1">
							<p class="pr-phase">{t('Phase 1: Pre-Switch')}</p>
							<p class="pr-rule">{cueInstruction(phaseRule(1))}</p>
							<p class="pr-acc">{accuracyLabel(results.phases.phase1.accuracy)}</p>
							<p class="pr-rt">{t('Avg RT')}: {durationMsLabel(results.phases.phase1.mean_rt)}</p>
						</div>
					{/if}
					{#if results.phases.phase2}
						<div class="phase-result-card pr2">
							<p class="pr-phase">{t('Phase 2: Post-Switch')}</p>
							<p class="pr-rule">{cueInstruction(phaseRule(2))}</p>
							<p class="pr-acc">{accuracyLabel(results.phases.phase2.accuracy)}</p>
							<p class="pr-rt">{t('Avg RT')}: {durationMsLabel(results.phases.phase2.mean_rt)}</p>
						</div>
					{/if}
					{#if results.phases.phase3}
						<div class="phase-result-card pr3">
							<p class="pr-phase">{t('Phase 3: Mixed')}</p>
							<p class="pr-rule">{t('Per-trial cue')}</p>
							<p class="pr-acc">{accuracyLabel(results.phases.phase3.accuracy)}</p>
							<p class="pr-rt">{t('Avg RT')}: {durationMsLabel(results.phases.phase3.mean_rt)}</p>
						</div>
					{/if}
				</div>
			{/if}

			<!-- Key metrics -->
			{#if results.switch_cost !== undefined}
				<div class="card">
					<h2 class="section-title">{t('Key Metrics')}</h2>
					<div class="metrics-grid">
						<div class="metric-card fuchsia-top">
							<p class="m-label">{t('Switch Cost')}</p>
							<p class="m-value">{signedDurationLabel(results.switch_cost)}</p>
							<p class="m-sub">{t('Time penalty for switching rules')}</p>
						</div>
						<div class="metric-card fuchsia-top">
							<p class="m-label">{t('Perseverative Errors')}</p>
							<p class="m-value">{n(results.perseverative_errors || 0)}</p>
							<p class="m-sub">{t('Times you used the old rule')}</p>
						</div>
						<div class="metric-card fuchsia-top">
							<p class="m-label">{t('Overall Accuracy')}</p>
							<p class="m-value">{accuracyLabel(results.accuracy)}</p>
							<p class="m-sub">{t('Correct responses across all phases')}</p>
						</div>
						<div class="metric-card fuchsia-top">
							<p class="m-label">{t('Total Score')}</p>
							<p class="m-value">{n(results.score)}</p>
							<p class="m-sub">{t('Performance score')}</p>
						</div>
					</div>
				</div>
			{/if}

			<!-- Clinical context -->
			<div class="card clinical-context-card">
				<h3 class="card-heading">{t('What Your Results Mean')}</h3>
				<p>
					{$locale === 'bn'
						? 'DCCS-এ কম সুইচ কস্ট এবং কম পার্সেভারেটিভ ত্রুটি ভালো কগনিটিভ ফ্লেক্সিবিলিটি নির্দেশ করে। MS রোগীদের ক্ষেত্রে উচ্চ সুইচ কস্ট বা বেশি পার্সেভারেটিভ ত্রুটি ফ্রন্টাল লোব কার্যক্রমে পরিবর্তন নির্দেশ করতে পারে।'
						: 'A lower switch cost and fewer perseverative errors indicate strong cognitive flexibility. In MS patients, higher switch costs or more perseverative errors may reflect changes in frontal lobe function and real-world multitasking ability.'}
				</p>
			</div>

			<div class="btn-row">
				<button class="start-button" on:click={() => goto('/dashboard')}>
					{t('Return to Dashboard')}
				</button>
				<button class="btn-secondary" on:click={() => goto('/training')}>
					{t('Next Task')}
				</button>
			</div>
		</div>
	{/if}
</div>

<style>
	/* ── Base ──────────────────────────────────────────────── */
	.dccs-container {
		min-height: 100vh;
		background: #C8DEFA;
		padding: 2rem 1rem;
	}

	.loading-wrap {
		max-width: 960px;
		margin: 0 auto;
		padding: 4rem 0;
	}

	.page-wrapper {
		max-width: 960px;
		margin: 0 auto;
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	/* ── Error ──────────────────────────────────────────────── */
	.error-card {
		background: #fff;
		border-radius: 16px;
		padding: 2rem;
		border-left: 4px solid #ef4444;
	}
	.error-msg { color: #dc2626; margin-bottom: 1rem; }
	.btn-retry {
		background: #dc2626;
		color: #fff;
		border: none;
		padding: 0.6rem 1.5rem;
		border-radius: 8px;
		cursor: pointer;
		font-weight: 600;
	}

	/* ── Card ──────────────────────────────────────────────── */
	.card {
		background: #fff;
		border-radius: 16px;
		padding: 2rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
	}

	.section-title {
		font-size: 1.25rem;
		font-weight: 700;
		color: #1e293b;
		margin-bottom: 1.25rem;
	}

	.card-heading {
		font-size: 1.1rem;
		font-weight: 700;
		color: #1e293b;
		margin-bottom: 1rem;
	}

	/* ── Task title ────────────────────────────────────────── */
	.task-title-row {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 1rem;
		flex-wrap: wrap;
		padding: 0.5rem 0;
	}

	h1 {
		font-size: 2rem;
		font-weight: 800;
		color: #1e293b;
		margin: 0 0 0.25rem;
	}

	.task-subtitle {
		color: #64748b;
		font-size: 1rem;
		margin: 0;
	}

	/* ── Concept card ──────────────────────────────────────── */
	.task-concept {
		background: linear-gradient(135deg, #fdf4ff 0%, #fae8ff 100%);
		border: 1px solid #f0abfc;
	}

	.concept-badge {
		display: inline-block;
		background: #c026d3;
		color: #fff;
		font-size: 0.8rem;
		font-weight: 700;
		letter-spacing: 0.05em;
		padding: 0.3rem 1rem;
		border-radius: 999px;
		margin-bottom: 1rem;
		text-transform: uppercase;
	}

	.concept-body {
		color: #1e293b;
		font-size: 1.05rem;
		line-height: 1.7;
		margin: 0;
	}

	/* ── Three-phase row ───────────────────────────────────── */
	.phases-row {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.phase-block {
		flex: 1;
		border-radius: 12px;
		padding: 1.25rem 1rem;
		text-align: center;
		border: 2px solid transparent;
	}

	.phase1 { background: #eff6ff; border-color: #bfdbfe; }
	.phase2 { background: #f0fdf4; border-color: #a7f3d0; }
	.phase3 { background: #fdf4ff; border-color: #f0abfc; }

	.phase-num {
		width: 2rem;
		height: 2rem;
		border-radius: 50%;
		background: #c026d3;
		color: #fff;
		font-weight: 700;
		font-size: 1rem;
		display: flex;
		align-items: center;
		justify-content: center;
		margin: 0 auto 0.5rem;
	}

	.phase-label { font-weight: 700; font-size: 0.9rem; color: #1e293b; margin: 0 0 0.25rem; }
	.phase-rule  { font-weight: 600; font-size: 0.85rem; color: #c026d3; margin: 0 0 0.4rem; }
	.phase-eg    { font-size: 0.78rem; color: #64748b; margin: 0; }

	.phase-arrow {
		font-size: 1.5rem;
		color: #c026d3;
		font-weight: 700;
		flex-shrink: 0;
	}

	/* ── Rules grid ────────────────────────────────────────── */
	.rules-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}

	.rule-item {
		display: flex;
		align-items: flex-start;
		gap: 0.75rem;
		padding: 1rem;
		background: #f8fafc;
		border-radius: 12px;
	}

	.rule-num {
		width: 2rem;
		height: 2rem;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 700;
		font-size: 0.95rem;
		flex-shrink: 0;
	}

	.rule-num.fuchsia { background: #c026d3; color: #fff; }

	.rule-body {
		display: flex;
		flex-direction: column;
		gap: 0.35rem;
		font-size: 0.95rem;
		color: #374151;
	}

	.rule-body strong { color: #1e293b; }
	.rule-body span { font-size: 0.85rem; color: #64748b; }

	/* ── Info grid ─────────────────────────────────────────── */
	.info-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.5rem;
	}

	.detail-list {
		list-style: none;
		padding: 0;
		margin: 0 0 0.75rem;
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	.detail-list li {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.6rem 0.75rem;
		background: #f8fafc;
		border-radius: 8px;
		font-size: 0.9rem;
	}

	.dl-label { color: #64748b; font-weight: 500; }
	.dl-value { color: #1e293b; font-weight: 700; }
	.dl-value.fuchsia-val {
		background: #fdf4ff;
		color: #86198f;
		padding: 0.2rem 0.75rem;
		border-radius: 999px;
	}

	.diff-desc {
		font-size: 0.85rem;
		color: #64748b;
		background: #f8fafc;
		border-radius: 8px;
		padding: 0.6rem 0.75rem;
		margin: 0 0 0.5rem;
	}

	.baseline-note {
		font-size: 0.8rem;
		color: #86198f;
		background: #fdf4ff;
		border-radius: 8px;
		padding: 0.5rem 0.75rem;
		margin: 0;
	}

	.measure-list {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.measure-list li {
		display: flex;
		align-items: flex-start;
		gap: 0.6rem;
	}

	.dot {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		flex-shrink: 0;
		margin-top: 0.45rem;
	}

	.dot.fuchsia { background: #c026d3; }

	.measure-list strong { color: #1e293b; font-size: 0.95rem; display: block; }
	.measure-list p { margin: 0.1rem 0 0; font-size: 0.85rem; color: #64748b; }

	/* ── Clinical info ─────────────────────────────────────── */
	.clinical-info {
		background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
		border: 1px solid #a7f3d0;
	}

	.clinical-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0.75rem;
	}

	.clinical-item {
		background: rgba(255, 255, 255, 0.7);
		border-radius: 10px;
		padding: 0.75rem 1rem;
		font-size: 0.9rem;
		color: #374151;
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.ci-label {
		font-weight: 700;
		font-size: 0.75rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: #059669;
	}

	/* ── Performance guide ─────────────────────────────────── */
	.norm-bars {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.norm-bar {
		display: grid;
		grid-template-columns: 110px 1fr 80px;
		align-items: center;
		gap: 0.75rem;
	}

	.norm-label { font-size: 0.9rem; font-weight: 600; color: #374151; }
	.norm-track {
		height: 10px;
		background: #e2e8f0;
		border-radius: 999px;
		overflow: hidden;
	}

	.norm-fill { height: 100%; border-radius: 999px; }
	.norm-fill.fuchsia-fill { background: #c026d3; }
	.norm-fill.fuchsia-mid  { background: #d946ef; }
	.norm-fill.fuchsia-low  { background: #e879f9; }
	.norm-val { font-size: 0.85rem; color: #64748b; text-align: right; }

	/* ── Buttons ───────────────────────────────────────────── */
	.btn-row {
		display: flex;
		gap: 1rem;
		justify-content: center;
		padding: 0.5rem 0 1.5rem;
	}

	.start-button {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: #fff;
		border: none;
		padding: 0.9rem 2.5rem;
		border-radius: 12px;
		font-size: 1rem;
		font-weight: 700;
		cursor: pointer;
		transition: transform 0.15s, box-shadow 0.15s;
	}

	.start-button:hover {
		transform: translateY(-2px);
		box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
	}

	.btn-secondary {
		background: #fff;
		color: #667eea;
		border: 2px solid #667eea;
		padding: 0.9rem 2rem;
		border-radius: 12px;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: background 0.15s;
	}

	.btn-secondary:hover { background: #f5f3ff; }

	/* ── Trial wrapper ─────────────────────────────────────── */
	.trial-wrapper {
		max-width: 820px;
		margin: 0 auto;
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	/* ── Phase transition ──────────────────────────────────── */
	.transition-card {
		background: #fff;
		border-radius: 16px;
		padding: 3rem 2rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
		text-align: center;
	}

	.transition-badge {
		display: inline-block;
		background: #c026d3;
		color: #fff;
		font-size: 0.85rem;
		font-weight: 700;
		padding: 0.35rem 1.25rem;
		border-radius: 999px;
		margin-bottom: 1rem;
	}

	.transition-title {
		font-size: 1.75rem;
		font-weight: 800;
		color: #1e293b;
		margin-bottom: 1rem;
	}

	.transition-msg {
		font-size: 1rem;
		color: #374151;
		line-height: 1.7;
		max-width: 500px;
		margin: 0 auto 1.5rem;
	}

	.transition-rule-box {
		display: inline-flex;
		align-items: center;
		gap: 0.75rem;
		background: #fdf4ff;
		border: 2px solid #f0abfc;
		border-radius: 12px;
		padding: 0.75rem 1.5rem;
		margin-bottom: 2rem;
	}

	.trb-label { font-size: 0.85rem; font-weight: 600; color: #64748b; }
	.trb-rule  { font-size: 1rem; font-weight: 700; color: #c026d3; }

	/* ── Status row ────────────────────────────────────────── */
	.test-status-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.phase-pill {
		background: linear-gradient(135deg, #c026d3, #a21caf);
		color: #fff;
		padding: 0.5rem 1.25rem;
		border-radius: 999px;
		font-weight: 700;
		font-size: 0.9rem;
	}

	.trial-pill {
		background: #f8fafc;
		color: #374151;
		border: 1.5px solid #e2e8f0;
		padding: 0.5rem 1.25rem;
		border-radius: 999px;
		font-weight: 600;
		font-size: 0.9rem;
	}

	/* Progress bar */
	.progress-track {
		height: 6px;
		background: #e2e8f0;
		border-radius: 999px;
		overflow: hidden;
	}

	.progress-fill {
		height: 100%;
		background: linear-gradient(90deg, #c026d3, #a21caf);
		border-radius: 999px;
		transition: width 0.2s;
	}

	/* Rule banner */
	.rule-banner {
		background: #fdf4ff;
		border: 1.5px solid #f0abfc;
		border-radius: 12px;
		padding: 0.75rem 1.5rem;
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.rb-label { font-size: 0.85rem; font-weight: 600; color: #64748b; }
	.rb-rule  { font-size: 1.1rem; font-weight: 800; color: #c026d3; }

	/* Cue flash */
	.cue-flash {
		background: #fdf4ff;
		border: 3px solid #c026d3;
		border-radius: 12px;
		padding: 1rem 2rem;
		text-align: center;
		animation: cue-pulse 0.4s ease;
	}

	.cue-text {
		font-size: 1.5rem;
		font-weight: 800;
		color: #86198f;
		margin: 0;
	}

	@keyframes cue-pulse {
		0%   { transform: scale(0.95); opacity: 0; }
		60%  { transform: scale(1.03); }
		100% { transform: scale(1);    opacity: 1; }
	}

	/* Card areas */
	.card-area {
		text-align: center;
	}

	.area-label {
		font-size: 0.85rem;
		font-weight: 600;
		color: #64748b;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-bottom: 0.75rem;
	}

	.stimulus-card {
		display: inline-flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}

	.test-card {
		background: #fff;
		border: 2px solid #e2e8f0;
		border-radius: 16px;
		padding: 1.5rem;
		box-shadow: 0 4px 6px rgba(0,0,0,0.07);
	}

	.size-tag {
		font-size: 0.8rem;
		color: #64748b;
		margin: 0;
	}

	/* Targets */
	.targets-area {
		text-align: center;
	}

	.targets-row {
		display: flex;
		justify-content: center;
		gap: 2.5rem;
		margin-top: 0.75rem;
	}

	.target-btn {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		padding: 1.5rem;
		background: #fff;
		border: 3px solid #e2e8f0;
		border-radius: 16px;
		cursor: pointer;
		transition: border-color 0.15s, transform 0.15s, box-shadow 0.15s;
		box-shadow: 0 2px 4px rgba(0,0,0,0.08);
	}

	.target-btn:hover {
		border-color: #c026d3;
		transform: translateY(-4px);
		box-shadow: 0 8px 20px rgba(192, 38, 211, 0.2);
	}

	/* ── Results ───────────────────────────────────────────── */
	.results-header {
		text-align: center;
		padding: 0.5rem 0;
	}

	.results-header h1 {
		font-size: 1.75rem;
		font-weight: 800;
		color: #1e293b;
		margin-bottom: 0.75rem;
	}

	.score-pill {
		display: inline-block;
		background: linear-gradient(135deg, #c026d3, #a21caf);
		color: #fff;
		padding: 0.5rem 2rem;
		border-radius: 999px;
		font-size: 1.2rem;
		font-weight: 700;
		margin-bottom: 0.5rem;
	}

	.overall-acc {
		font-size: 1rem;
		color: #64748b;
		margin: 0;
	}

	/* Phase results */
	.phase-results-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 1rem;
	}

	.phase-result-card {
		background: #fff;
		border-radius: 16px;
		padding: 1.5rem;
		box-shadow: 0 4px 6px rgba(0,0,0,0.07);
		text-align: center;
	}

	.pr1 { border-top: 4px solid #3b82f6; }
	.pr2 { border-top: 4px solid #10b981; }
	.pr3 { border-top: 4px solid #c026d3; }

	.pr-phase { font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; margin-bottom: 0.25rem; }
	.pr-rule  { font-size: 0.85rem; font-weight: 600; color: #374151; margin-bottom: 0.5rem; }
	.pr-acc   { font-size: 1.75rem; font-weight: 800; color: #1e293b; margin-bottom: 0.2rem; }
	.pr-rt    { font-size: 0.85rem; color: #94a3b8; margin: 0; }

	/* Key metrics */
	.metrics-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 1rem;
	}

	.metric-card {
		background: #fff;
		border-radius: 16px;
		padding: 1.5rem 1rem;
		box-shadow: 0 4px 6px rgba(0,0,0,0.07);
		text-align: center;
	}

	.metric-card.fuchsia-top { border-top: 4px solid #c026d3; }

	.m-label { font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; margin-bottom: 0.5rem; }
	.m-value { font-size: 1.75rem; font-weight: 800; color: #1e293b; margin-bottom: 0.25rem; }
	.m-sub   { font-size: 0.8rem; color: #94a3b8; }

	/* Clinical context */
	.clinical-context-card { background: #f8fafc; border: 1px solid #e2e8f0; }
	.clinical-context-card p { font-size: 0.95rem; line-height: 1.7; color: #374151; margin: 0; }

	/* ── Responsive ────────────────────────────────────────── */
	@media (max-width: 768px) {
		.dccs-container { padding: 1rem 0.75rem; }
		h1 { font-size: 1.5rem; }
		.rules-grid,
		.info-grid,
		.clinical-grid { grid-template-columns: 1fr; }
		.phases-row { flex-direction: column; }
		.phase-arrow { transform: rotate(90deg); }
		.phase-results-grid { grid-template-columns: 1fr; }
		.metrics-grid { grid-template-columns: 1fr 1fr; }
		.targets-row { gap: 1.5rem; }
		.norm-bar { grid-template-columns: 90px 1fr 70px; }
	}

	@media (max-width: 480px) {
		.metrics-grid { grid-template-columns: 1fr; }
		.targets-row { flex-direction: column; align-items: center; }
	}
</style>

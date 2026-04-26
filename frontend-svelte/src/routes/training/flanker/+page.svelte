<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
	import TaskReturnButton from '$lib/components/TaskReturnButton.svelte';
	import { formatNumber, formatPercent, locale, localeText, translateText } from '$lib/i18n';
	import { user } from '$lib/stores';
	import { buildPracticePayload, getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
	import { TASK_RETURN_CONTEXT } from '$lib/task-navigation';
	import { onDestroy, onMount } from 'svelte';

	import { API_BASE_URL } from '$lib/api';

	let currentUser = null;
	let loading = true;
	let sessionData = null;
	let recordedSessionData = null;
	let difficulty = 1;
	let currentTrial = 0;
	let responses = [];
	let phase = 'intro';
	let metrics = null;
	let newBadges = [];
	let taskId = null;
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';
	let sessionRunId = 0;
	let isDisposed = false;

	let startTime = 0;
	let responded = false;
	let showStimulus = false;
	let trialTimeout = null;
	let stimulusTimeout = null;
	let interStimulusTimeout = null;

	let showHelp = false;

	// Subscribe to user store
	user.subscribe((value) => {
		currentUser = value;
	});

	function lt(en, bn) {
		return localeText({ en, bn }, $locale);
	}

	function t(text) {
		return translateText(text ?? '', $locale);
	}

	function n(value, options = {}) {
		return formatNumber(value, $locale, options);
	}

	function pct(value, options = {}) {
		return formatPercent(value, $locale, {
			minimumFractionDigits: 1,
			maximumFractionDigits: 1,
			...options
		});
	}

	function cloneData(value) {
		if (typeof structuredClone === 'function') {
			return structuredClone(value);
		}

		return JSON.parse(JSON.stringify(value));
	}

	function clearTrialTimers() {
		if (stimulusTimeout) {
			clearTimeout(stimulusTimeout);
			stimulusTimeout = null;
		}
		if (interStimulusTimeout) {
			clearTimeout(interStimulusTimeout);
			interStimulusTimeout = null;
		}
		if (trialTimeout) {
			clearTimeout(trialTimeout);
			trialTimeout = null;
		}
	}

	function invalidateRun() {
		sessionRunId += 1;
		clearTrialTimers();
	}

	function msText(value) {
		const rounded = Math.round(Number(value) || 0);
		return $locale === 'bn' ? `${n(rounded)} মি.সে.` : `${rounded} ms`;
	}

	function performanceLevelLabel(level) {
		const labels = {
			Excellent: lt('Excellent', 'অসাধারণ'),
			Good: lt('Good', 'ভালো'),
			Fair: lt('Fair', 'মোটামুটি'),
			Poor: lt('Needs Practice', 'আরও অনুশীলন দরকার')
		};
		return labels[level] || t(level);
	}

	function directionLabel(direction) {
		return direction === 'right' ? lt('RIGHT', 'ডানে') : lt('LEFT', 'বামে');
	}

	function shortDirection(direction) {
		return direction === 'right' ? lt('right', 'ডান') : lt('left', 'বাম');
	}

	function practiceTrialLabel(current, total) {
		return $locale === 'bn'
			? `অনুশীলনী ট্রায়াল ${n(current)} / ${n(total)}`
			: `Practice Trial ${current} of ${total}`;
	}

	function trialLabel(current, total) {
		return $locale === 'bn' ? `ট্রায়াল ${n(current)} / ${n(total)}` : `Trial ${current} of ${total}`;
	}

	function remainingTrialsLabel(count) {
		return $locale === 'bn' ? `${n(count)}টি বাকি` : `${count} remaining`;
	}

	function localizedHint(trial) {
		return localeText(trial?.hint, $locale);
	}

	function practiceSuccessMessage(rt, trial) {
		return $locale === 'bn'
			? `সঠিক! প্রতিক্রিয়ার সময়: ${msText(rt)}। ${localizedHint(trial)}`
			: `Correct! Response time: ${rt}ms. ${localizedHint(trial)}`;
	}

	function practiceErrorMessage(trial) {
		return $locale === 'bn'
			? `ভুল দিক! মাঝের তীরটি ছিল ${directionLabel(trial.direction)}। ${localizedHint(trial)}`
			: `Wrong direction! CENTER arrow pointed ${directionLabel(trial.direction)}. ${localizedHint(trial)}`;
	}

	function practiceCompleteMessage() {
		return lt("Practice complete! You're ready for the real test.", 'অনুশীলন শেষ! এখন আপনি আসল পরীক্ষার জন্য প্রস্তুত।');
	}

	function slowResponseMessage() {
		return lt('Too slow! Try to respond faster.', 'একটু দেরি হয়ে গেছে! আরও দ্রুত সাড়া দেওয়ার চেষ্টা করুন।');
	}

	function resultsSummaryText() {
		const conflictEffect = Number(metrics?.conflict_effect || 0);
		const accuracy = Number(metrics?.overall_accuracy || 0);

		if ($locale === 'bn') {
			if (accuracy >= 90 && conflictEffect < 100) {
				return 'চমৎকার নির্বাচিত মনোযোগ! বিভ্রান্তিকর সংকেত থাকলেও আপনি খুব ভালোভাবে সঠিক দিক চিনতে পেরেছেন।';
			}
			if (accuracy >= 80 && conflictEffect < 150) {
				return 'ভালো পারফরম্যান্স। আপনার মনোযোগ ও দ্বন্দ্ব সামলানোর ক্ষমতা স্থিতিশীল আছে, তবে আরও অনুশীলনে গতি ও নিয়ন্ত্রণ দুটোই উন্নত হবে।';
			}
			return 'এই টাস্কটি বিভ্রান্তির মাঝেও সঠিক সংকেতে মনোযোগ ধরে রাখার ক্ষমতা মাপে। নিয়মিত অনুশীলনে প্রাসঙ্গিক তথ্য বেছে নেওয়ার দক্ষতা আরও ভালো হবে।';
		}

		if (accuracy >= 90 && conflictEffect < 100) {
			return 'Excellent selective attention! You handled conflicting arrows with strong control and accuracy.';
		}
		if (accuracy >= 80 && conflictEffect < 150) {
			return 'Good performance. Your attention and conflict control are solid, with room to become even faster and more consistent.';
		}
		return 'This task measures how well you focus on relevant information when distractions compete for attention. Practice will help strengthen that control.';
	}

	function buildPracticeTrials() {
		return [
			{
				trial_type: 'congruent',
				direction: 'right',
				flanker_count: 2,
				hint: { en: 'All arrows point right', bn: 'সব তীর ডানে' }
			},
			{
				trial_type: 'congruent',
				direction: 'left',
				flanker_count: 2,
				hint: { en: 'All arrows point left', bn: 'সব তীর বামে' }
			},
			{
				trial_type: 'incongruent',
				direction: 'right',
				flanker_count: 2,
				hint: { en: 'Focus on the CENTER arrow only!', bn: 'শুধু মাঝের তীরটিতে মন দিন!' }
			},
			{
				trial_type: 'congruent',
				direction: 'right',
				flanker_count: 2,
				hint: { en: 'Congruent again - quick!', bn: 'আবার সঙ্গত ট্রায়াল - দ্রুত সাড়া দিন!' }
			},
			{
				trial_type: 'incongruent',
				direction: 'left',
				flanker_count: 2,
				hint: { en: 'Ignore distractors - CENTER is left', bn: 'বিভ্রান্তি উপেক্ষা করুন - মাঝের তীরটি বামে' }
			},
			{
				trial_type: 'congruent',
				direction: 'left',
				flanker_count: 2,
				hint: { en: 'All matching, press quickly', bn: 'সব একই দিকে - দ্রুত চাপুন' }
			},
			{
				trial_type: 'incongruent',
				direction: 'right',
				flanker_count: 2,
				hint: { en: 'Flankers mislead you - stay focused', bn: 'পাশের তীরগুলো বিভ্রান্ত করবে - মনোযোগ রাখুন' }
			},
			{
				trial_type: 'incongruent',
				direction: 'left',
				flanker_count: 2,
				hint: { en: 'Last one - stay focused on CENTER', bn: 'শেষটি - মাঝের তীরেই মন রাখুন' }
			}
		];
	}

	onMount(async () => {
		if (!currentUser) {
			goto('/login');
			return;
		}
		await loadSession();
	});

	onDestroy(() => {
		isDisposed = true;
		invalidateRun();
	});

	async function loadSession() {
		try {
			loading = true;
			const response = await fetch(`${API_BASE_URL}/api/training/tasks/flanker/generate/${currentUser.id}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' }
			});

			if (!response.ok) {
				const errorText = await response.text();
				throw new Error(
					$locale === 'bn'
						? `সেশন লোড করা যায়নি: ${response.status} - ${errorText}`
						: `Failed to load session: ${response.status} - ${errorText}`
				);
			}

			const data = await response.json();
			recordedSessionData = cloneData(data.session_data);
			sessionData = cloneData(data.session_data);
			difficulty = data.difficulty;
			playMode = TASK_PLAY_MODE.RECORDED;
			practiceStatusMessage = '';
			responses = [];
			currentTrial = 0;
			responded = false;
			showStimulus = false;
			phase = 'intro';
			loading = false;
		} catch (error) {
			console.error('Error loading session:', error);
			alert(
				lt(
					'Failed to load training session. Please ensure the backend server is running and you have completed baseline assessment.',
					'ট্রেনিং সেশন লোড করা যায়নি। অনুগ্রহ করে নিশ্চিত করুন ব্যাকএন্ড সার্ভার চালু আছে এবং আপনি বেসলাইন মূল্যায়ন সম্পন্ন করেছেন।'
				)
			);
			loading = false;
		}
	}

	function startInstructions() {
		phase = 'instructions';
	}

	function startPractice() {
		startSession(TASK_PLAY_MODE.PRACTICE);
	}

	function leavePractice(completed = false) {
		invalidateRun();
		playMode = TASK_PLAY_MODE.RECORDED;
		sessionData = cloneData(recordedSessionData);
		responses = [];
		currentTrial = 0;
		responded = false;
		showStimulus = false;
		phase = 'instructions';
		practiceStatusMessage = completed ? getPracticeCopy($locale).complete : '';
	}

	const finishPractice = leavePractice;

	function startTest() {
		startSession(TASK_PLAY_MODE.RECORDED);
	}

	function startSession(nextMode = TASK_PLAY_MODE.RECORDED) {
		if (!recordedSessionData) return;

		invalidateRun();
		playMode = nextMode;
		practiceStatusMessage = '';
		sessionData =
			nextMode === TASK_PLAY_MODE.PRACTICE
				? buildPracticePayload('flanker', recordedSessionData)
				: cloneData(recordedSessionData);
		currentTrial = 0;
		responses = [];
		responded = false;
		showStimulus = false;
		phase = 'test';
		showNextTrial(sessionRunId);
	}

	function showNextTrial(runId = sessionRunId) {
		clearTrialTimers();

		if (currentTrial >= sessionData.trials.length) {
			if (playMode === TASK_PLAY_MODE.PRACTICE) {
				leavePractice(true);
				return;
			}
			completeSession();
			return;
		}

		responded = false;
		showStimulus = false;

		interStimulusTimeout = setTimeout(() => {
			if (isDisposed || runId !== sessionRunId) return;
			showStimulus = true;
			startTime = Date.now();

			stimulusTimeout = setTimeout(() => {
				if (isDisposed || runId !== sessionRunId) return;
				showStimulus = false;
				if (!responded) {
					trialTimeout = setTimeout(() => {
						if (isDisposed || runId !== sessionRunId) return;
						recordResponse(null, 0);
					}, 300);
				}
			}, sessionData.presentation_time_ms);
		}, 500);
	}

	function recordResponse(direction, reactionTime) {
		if (responded) return;
		const runId = sessionRunId;
		clearTrialTimers();
		responded = true;

		const trial = sessionData.trials[currentTrial];
		responses = [...responses, {
			trial_number: trial.trial_number,
			trial_type: trial.trial_type,
			target_direction: trial.target_direction,
			responded_direction: direction,
			reaction_time_ms: reactionTime,
			correct: direction === trial.target_direction
		}];

		currentTrial++;
		showStimulus = false;

		interStimulusTimeout = setTimeout(() => {
			if (isDisposed || runId !== sessionRunId) return;
			showNextTrial(runId);
		}, 300);
	}

	function handleKeyPress(event) {
		if (phase !== 'test' || !showStimulus || responded) return;

		const rt = Date.now() - startTime;
		if (event.key === 'ArrowLeft' || event.key === 'a' || event.key === 'A') {
			event.preventDefault();
			recordResponse('left', rt);
		} else if (event.key === 'ArrowRight' || event.key === 'd' || event.key === 'D') {
			event.preventDefault();
			recordResponse('right', rt);
		}
	}

	async function completeSession() {
		try {
			clearTrialTimers();
			taskId = $page.url.searchParams.get('taskId');
			const response = await fetch(`${API_BASE_URL}/api/training/tasks/flanker/submit/${currentUser.id}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					difficulty,
					session_data: sessionData,
					responses,
					task_id: taskId
				})
			});

			if (!response.ok) throw new Error('Failed to submit session');

			const data = await response.json();
			metrics = data.metrics;
			newBadges = data.new_badges || [];
			phase = 'results';
		} catch (error) {
			console.error('Error submitting session:', error);
			alert(lt('Failed to submit results. Please try again.', 'ফলাফল জমা দেওয়া যায়নি। আবার চেষ্টা করুন।'));
		}
	}

	function returnToDashboard() {
		goto('/dashboard');
	}

	// Progress tracking
	$: progress = sessionData ? ((currentTrial / sessionData.trials.length) * 100) : 0;
	$: trialsRemaining = sessionData ? sessionData.trials.length - currentTrial : 0;

	// Performance badge color
	$: performanceBadgeColor = metrics?.performance_level === 'Excellent' ? 'from-green-500'
		: metrics?.performance_level === 'Good' ? 'from-blue-500'
		: metrics?.performance_level === 'Fair' ? 'from-yellow-500'
		: 'from-gray-500';

	function generateArrowDisplay(trial) {
		const leftArrow = '\u2190';
		const rightArrow = '\u2192';
		const centerArrow = trial.target_direction === 'right' ? rightArrow : leftArrow;
		const flankerArrow = trial.trial_type === 'congruent'
			? centerArrow
			: (centerArrow === rightArrow ? leftArrow : rightArrow);
		const flankers = Array(trial.flanker_count).fill(flankerArrow).join(' ');
		return `${flankers} ${centerArrow} ${flankers}`;
	}

	function generatePracticeArrowDisplay(trial) {
		const leftArrow = '\u2190';
		const rightArrow = '\u2192';
		const centerArrow = trial.direction === 'right' ? rightArrow : leftArrow;
		const flankerArrow = trial.trial_type === 'congruent'
			? centerArrow
			: (centerArrow === rightArrow ? leftArrow : rightArrow);
		const flankers = Array(trial.flanker_count).fill(flankerArrow).join(' ');
		return `${flankers} ${centerArrow} ${flankers}`;
	}
</script>

<svelte:window on:keydown={handleKeyPress} />

<div class="flanker-container">

	<!-- ── LOADING ─────────────────────────────────────────────── -->
	{#if loading}
		<div class="loading-wrap">
			<LoadingSkeleton />
		</div>

	<!-- ── INTRO ──────────────────────────────────────────────── -->
	{:else if phase === 'intro'}
		<div class="intro-wrapper">
			<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />

			<!-- Task title -->
			<div class="task-title-row">
				<div>
					<h1>{lt('Flanker Task', 'ফ্ল্যাঙ্কার টাস্ক')}</h1>
					<p class="task-subtitle">{lt('Selective Attention & Conflict Resolution', 'নির্বাচিত মনোযোগ ও দ্বন্দ্ব সামলানো')}</p>
				</div>
				<DifficultyBadge {difficulty} domain="Attention" />
			</div>

			<!-- Concept card -->
			<div class="card task-concept">
				<div class="concept-badge">{lt('Attention Networks Test (ANT)', 'মনোযোগ নেটওয়ার্ক পরীক্ষা (ANT)')}</div>
				<p class="concept-body">
					{@html lt(
						'You will see a row of arrows. <strong>Identify the direction of the CENTER arrow</strong> and press the matching key. The surrounding (flanker) arrows sometimes point the opposite way to challenge your focus.',
						'একটি সারি তীরচিহ্ন দেখা যাবে। <strong>মাঝের তীরের দিক চিহ্নিত করুন</strong> এবং সংশ্লিষ্ট কী চাপুন। পাশের তীরগুলো কখনও উল্টো দিকে থাকবে, যা আপনার মনোযোগকে চ্যালেঞ্জ করবে।'
					)}
				</p>
			</div>

			<!-- Trial type examples -->
			<div class="card">
				<h2 class="section-title">{lt('Trial Types', 'ট্রায়ালের ধরন')}</h2>
				<div class="rules-grid">
					<div class="rule-item">
						<div class="rule-num sky">{n(1)}</div>
						<div class="rule-body">
							<strong>{lt('Congruent', 'সঙ্গত')}</strong>
							<div class="arrow-demo congruent-demo">&rarr; &rarr; &rarr; &rarr; &rarr;</div>
							<span>{lt('All arrows match — easy!', 'সব তীর একই দিকে — সহজ!')}</span>
						</div>
					</div>
					<div class="rule-item">
						<div class="rule-num sky">{n(2)}</div>
						<div class="rule-body">
							<strong>{lt('Incongruent', 'অসঙ্গত')}</strong>
							<div class="arrow-demo incongruent-demo">&larr; &larr; &rarr; &larr; &larr;</div>
							<span>{lt('Flankers mislead — focus on CENTER!', 'পাশের তীরগুলো বিভ্রান্ত করে — মাঝেরটিতে মন দিন!')}</span>
						</div>
					</div>
					<div class="rule-item">
						<div class="rule-num sky">{n(3)}</div>
						<div class="rule-body">
							<strong>{lt('Press Left Key', 'বাম কী চাপুন')}</strong>
							<div class="key-demo"><kbd>&larr;</kbd> {lt('or', 'অথবা')} <kbd>A</kbd></div>
							<span>{lt('When center arrow points left', 'যখন মাঝের তীর বামে')}</span>
						</div>
					</div>
					<div class="rule-item">
						<div class="rule-num sky">{n(4)}</div>
						<div class="rule-body">
							<strong>{lt('Press Right Key', 'ডান কী চাপুন')}</strong>
							<div class="key-demo"><kbd>&rarr;</kbd> {lt('or', 'অথবা')} <kbd>D</kbd></div>
							<span>{lt('When center arrow points right', 'যখন মাঝের তীর ডানে')}</span>
						</div>
					</div>
				</div>
			</div>

			<!-- Info grid -->
			<div class="info-grid">
				<div class="card">
					<h3 class="card-heading">{lt('What You Do', 'আপনি কী করবেন')}</h3>
					<ol class="step-list">
						<li>
							<span class="step-num sky">{n(1)}</span>
							<div>
								<strong>{lt('Watch for arrow row', 'তীরের সারি দেখুন')}</strong>
								<p>{lt('Arrows appear briefly on screen', 'তীরচিহ্নগুলো অল্প সময়ের জন্য দেখা যায়')}</p>
							</div>
						</li>
						<li>
							<span class="step-num sky">{n(2)}</span>
							<div>
								<strong>{lt('Identify CENTER only', 'শুধু মাঝেরটি চিহ্নিত করুন')}</strong>
								<p>{lt('Ignore all surrounding flanker arrows', 'পাশের সব তীর উপেক্ষা করুন')}</p>
							</div>
						</li>
						<li>
							<span class="step-num sky">{n(3)}</span>
							<div>
								<strong>{lt('Press matching key fast', 'দ্রুত সঠিক কী চাপুন')}</strong>
								<p>{lt('Arrow keys or A / D keys work', 'তীর কী বা A / D কী ব্যবহার করুন')}</p>
							</div>
						</li>
					</ol>
				</div>
				<div class="card">
					<h3 class="card-heading">{lt('What It Measures', 'এটি কী মাপে')}</h3>
					<ul class="measure-list">
						<li><span class="dot sky"></span><div><strong>{lt('Selective Attention', 'নির্বাচিত মনোযোগ')}</strong><p>{lt('Ability to focus on relevant info', 'প্রাসঙ্গিক তথ্যে মন দেওয়ার ক্ষমতা')}</p></div></li>
						<li><span class="dot sky"></span><div><strong>{lt('Conflict Resolution', 'দ্বন্দ্ব সামলানো')}</strong><p>{lt('Suppressing competing distractors', 'প্রতিযোগিতামূলক বিভ্রান্তি দমন')}</p></div></li>
						<li><span class="dot sky"></span><div><strong>{lt('Interference Control', 'হস্তক্ষেপ নিয়ন্ত্রণ')}</strong><p>{lt('Resisting misleading information', 'ভুলপথে নেওয়া তথ্য প্রতিরোধ')}</p></div></li>
						<li><span class="dot sky"></span><div><strong>{lt('Processing Speed', 'প্রক্রিয়াকরণের গতি')}</strong><p>{lt('Quick and accurate decisions', 'দ্রুত ও সঠিক সিদ্ধান্ত')}</p></div></li>
					</ul>
				</div>
			</div>

			<!-- Clinical info -->
			<div class="card clinical-info">
				<h3 class="card-heading">{lt('Clinical Significance', 'ক্লিনিক্যাল গুরুত্ব')}</h3>
				<div class="clinical-grid">
					<div class="clinical-item">
						<span class="ci-label">{lt('Standard Test', 'মানক পরীক্ষা')}</span>
						<span>{lt('Attention Networks Test (Eriksen & Eriksen, 1974)', 'মনোযোগ নেটওয়ার্ক পরীক্ষা (Eriksen & Eriksen, 1974)')}</span>
					</div>
					<div class="clinical-item">
						<span class="ci-label">{lt('Brain Regions', 'মস্তিষ্কের অঞ্চল')}</span>
						<span>{lt('Anterior cingulate cortex & executive control networks', 'অ্যান্টেরিয়র সিংগুলেট কর্টেক্স ও নির্বাহী নিয়ন্ত্রণ নেটওয়ার্ক')}</span>
					</div>
					<div class="clinical-item">
						<span class="ci-label">{lt('MS Relevance', 'MS-এ গুরুত্ব')}</span>
						<span>{lt('Detects selective attention deficits common in MS', 'MS-এ সাধারণ নির্বাচিত মনোযোগ ঘাটতি শনাক্ত করে')}</span>
					</div>
					<div class="clinical-item">
						<span class="ci-label">{lt('Key Metric', 'মূল সূচক')}</span>
						<span>{lt('Conflict Effect = Incongruent RT minus Congruent RT', 'কনফ্লিক্ট ইফেক্ট = অসঙ্গত RT বিয়োগ সঙ্গত RT')}</span>
					</div>
				</div>
			</div>

			<!-- Performance guide -->
			<div class="card perf-guide">
				<h3 class="card-heading">{lt('Performance Guide — Conflict Effect', 'পারফরম্যান্স গাইড — কনফ্লিক্ট ইফেক্ট')}</h3>
				<div class="norm-bars">
					<div class="norm-bar">
						<span class="norm-label">{lt('Excellent', 'অসাধারণ')}</span>
						<div class="norm-track"><div class="norm-fill sky" style="width:30%"></div></div>
						<span class="norm-val">{$locale === 'bn' ? '< ১০০ মি.সে.' : '< 100 ms'}</span>
					</div>
					<div class="norm-bar">
						<span class="norm-label">{lt('Good', 'ভালো')}</span>
						<div class="norm-track"><div class="norm-fill sky-mid" style="width:55%"></div></div>
						<span class="norm-val">{$locale === 'bn' ? '১০০–১৫০ মি.সে.' : '100–150 ms'}</span>
					</div>
					<div class="norm-bar">
						<span class="norm-label">{lt('Developing', 'উন্নয়নশীল')}</span>
						<div class="norm-track"><div class="norm-fill sky-low" style="width:80%"></div></div>
						<span class="norm-val">{$locale === 'bn' ? '> ১৫০ মি.সে.' : '> 150 ms'}</span>
					</div>
				</div>
			</div>

			<div class="btn-row">
				<button class="start-button" on:click={startTest}>
					{lt('Begin Task', 'টাস্ক শুরু করুন')}
				</button>
			</div>
		</div>

	<!-- ── INSTRUCTIONS ───────────────────────────────────────── -->
	{:else if phase === 'instructions'}
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />
		<div class="page-wrapper">
			<div class="card instructions-card">
				<h2 class="instr-title">{lt('Quick Instructions', 'দ্রুত নির্দেশনা')}</h2>

				<div class="key-row">
					<div class="key-col">
						<kbd class="key-xl">&larr;</kbd>
						<span>{lt('Left Arrow', 'বাম তীর')}</span>
					</div>
					<div class="key-sep">{lt('or', 'অথবা')}</div>
					<div class="key-col">
						<kbd class="key-xl">&rarr;</kbd>
						<span>{lt('Right Arrow', 'ডান তীর')}</span>
					</div>
				</div>

				<div class="rule-callout">
					{@html lt(
						'Always press the key matching the <strong>CENTER arrow direction</strong> — ignore the flankers!',
						'সবসময় <strong>মাঝের তীরের দিক</strong> মিলিয়ে কী চাপুন — পাশের তীরগুলো উপেক্ষা করুন!'
					)}
				</div>

				<div class="flow-row">
					<div class="flow-step">
						<div class="flow-num sky">{n(1)}</div>
						<p class="flow-label">{lt('Arrows Appear', 'তীরচিহ্ন দেখা যায়')}</p>
						<p class="flow-sub">{lt('5 arrows flash briefly', '৫টি তীর অল্প সময়ের জন্য')}</p>
					</div>
					<div class="flow-connector"></div>
					<div class="flow-step">
						<div class="flow-num sky">{n(2)}</div>
						<p class="flow-label">{lt('Focus on Center', 'মাঝের তীরে মন দিন')}</p>
						<p class="flow-sub">{lt('Ignore outer flankers', 'বাইরের তীর উপেক্ষা করুন')}</p>
					</div>
					<div class="flow-connector"></div>
					<div class="flow-step">
						<div class="flow-num sky">{n(3)}</div>
						<p class="flow-label">{lt('Press Arrow Key', 'তীরের কী চাপুন')}</p>
						<p class="flow-sub">{lt('Match center direction', 'মাঝের তীরের দিক মিলিয়ে')}</p>
					</div>
				</div>

				<div class="example-block">
					<div class="example-row">
						<div class="ex-stim congruent-stim">&rarr; &rarr; &rarr; &rarr; &rarr;</div>
						<div class="ex-ans">{lt('Press', 'চাপুন')} <kbd>&rarr;</kbd> <span class="ex-note">{lt('(easy – all match)', '(সহজ – সব একই দিকে)')}</span></div>
					</div>
					<div class="example-row incongruent-row">
						<div class="ex-stim incongruent-stim">&larr; &larr; &rarr; &larr; &larr;</div>
						<div class="ex-ans">{lt('Press', 'চাপুন')} <kbd>&rarr;</kbd> <span class="ex-note">{lt('(hard – center is right!)', '(কঠিন – মাঝের তীরটি ডানে!)')}</span></div>
					</div>
				</div>

				<div class="strategy-box">
					<h4>{lt('Success Strategy', 'সফলতার কৌশল')}</h4>
					<ul>
						<li>{lt('Keep your eyes fixed on the center of the screen', 'চোখ সবসময় স্ক্রিনের মাঝখানে রাখুন')}</li>
						<li>{lt('Flanker arrows are designed to mislead — ignore them deliberately', 'পাশের তীরগুলো ইচ্ছাকৃতভাবে বিভ্রান্তকর — সচেতনভাবে উপেক্ষা করুন')}</li>
						<li>{lt('Accuracy matters more than speed — take a moment to be sure', 'গতির চেয়ে সঠিকতা গুরুত্বপূর্ণ — নিশ্চিত হয়ে চাপুন')}</li>
					</ul>
				</div>

				<TaskPracticeActions
					locale={$locale}
					startLabel={lt('Start Actual Task', 'আসল টাস্ক শুরু করুন')}
					statusMessage={practiceStatusMessage}
					align="center"
					on:start={startTest}
					on:practice={startPractice}
				/>
			</div>
		</div>

	<!-- ── PRACTICE ────────────────────────────────────────────── -->
	{:else if phase === 'practice'}
		<div class="trial-wrapper">
			<PracticeModeBanner locale={$locale} showExit on:exit={() => finishPractice(false)} />

			<div class="trial-top">
				<h2 class="trial-counter">{practiceTrialLabel(currentPractice + 1, practiceTrials.length)}</h2>
				<p class="trial-hint">{lt('Press \u2190 or \u2192 to match the CENTER arrow direction', 'মাঝের তীরের দিক মিলিয়ে \u2190 বা \u2192 চাপুন')}</p>
			</div>

			<div class="stimulus-card">
				{#if showStimulus}
					<div class="arrow-stim {practiceTrials[currentPractice].trial_type}">
						{generatePracticeArrowDisplay(practiceTrials[currentPractice])}
					</div>
				{:else}
					<div class="fixation">+</div>
				{/if}
			</div>

			{#if practiceFeedback}
				<div class="feedback-pill {practiceFeedback.type}">{practiceFeedback.message}</div>
			{/if}
		</div>

	<!-- ── TEST ───────────────────────────────────────────────── -->
	{:else if phase === 'test'}
		<div class="trial-wrapper">
			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
			{/if}
			<div class="progress-bar-row">
				<span class="progress-label">{trialLabel(currentTrial + 1, sessionData.trials.length)}</span>
				<span class="remaining-badge">{remainingTrialsLabel(trialsRemaining)}</span>
			</div>
			<div class="progress-track">
				<div class="progress-fill" style="width: {progress}%"></div>
			</div>

			<div class="stimulus-card">
				{#if showStimulus && currentTrial < sessionData.trials.length}
					<div class="arrow-stim {sessionData.trials[currentTrial].trial_type}">
						{generateArrowDisplay(sessionData.trials[currentTrial])}
					</div>
				{:else}
					<div class="fixation">+</div>
				{/if}
			</div>

			<p class="trial-hint">{lt('Focus on CENTER arrow only \u2022 \u2190 or \u2192 keys', 'শুধু মাঝের তীরে মন দিন \u2022 \u2190 বা \u2192 কী')}</p>
		</div>

	<!-- ── RESULTS ─────────────────────────────────────────────── -->
	{:else if phase === 'results'}
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />
		<div class="page-wrapper">

			{#if newBadges.length > 0}
				<BadgeNotification badges={newBadges} />
			{/if}

			<!-- Header -->
			<div class="results-header">
				<h1>{lt('Flanker Task Complete', 'ফ্ল্যাঙ্কার টাস্ক সম্পন্ন')}</h1>
				<div class="perf-pill perf-{(metrics?.performance_level || 'Good').toLowerCase()}">
					{performanceLevelLabel(metrics?.performance_level || 'Good')}
				</div>
			</div>

			<!-- Metrics grid -->
			<div class="metrics-grid">
				<div class="metric-card sky-top">
					<p class="m-label">{lt('Overall Accuracy', 'সামগ্রিক নির্ভুলতা')}</p>
					<p class="m-value">{pct(metrics?.overall_accuracy || 0)}</p>
					<p class="m-sub">
						{$locale === 'bn'
							? `${n(metrics?.total_correct || 0)}/${n(metrics?.total_trials || 0)} সঠিক`
							: `${metrics?.total_correct || 0}/${metrics?.total_trials || 0} correct`}
					</p>
				</div>
				<div class="metric-card sky-top">
					<p class="m-label">{lt('Mean Reaction Time', 'গড় প্রতিক্রিয়ার সময়')}</p>
					<p class="m-value">{msText(metrics?.mean_rt || 0)}</p>
					<p class="m-sub">{lt('Overall speed', 'মোট গতি')}</p>
				</div>
				<div class="metric-card sky-top">
					<p class="m-label">{lt('Conflict Effect', 'কনফ্লিক্ট ইফেক্ট')}</p>
					<p class="m-value">{msText(metrics?.conflict_effect || 0)}</p>
					<p class="m-sub">{lt('Interference cost', 'বিভ্রান্তির খরচ')}</p>
				</div>
				<div class="metric-card sky-top">
					<p class="m-label">{lt('Selective Attention', 'নির্বাচিত মনোযোগ')}</p>
					<p class="m-value">{n((metrics?.selective_attention_score || 0).toFixed(1), { minimumFractionDigits: 1, maximumFractionDigits: 1 })}</p>
					<p class="m-sub">{lt('Lower = better focus', 'যত কম, মনোযোগ তত ভালো')}</p>
				</div>
			</div>

			<!-- Breakdown -->
			<div class="card">
				<h2 class="section-title">{lt('Performance by Trial Type', 'ট্রায়ালভিত্তিক পারফরম্যান্স')}</h2>
				<div class="breakdown-grid">
					<div class="breakdown-card congruent-bd">
						<p class="bd-title">{lt('Congruent Trials', 'সঙ্গত ট্রায়াল')}</p>
						<p class="bd-sub">{lt('All arrows same direction (easy)', 'সব তীর একই দিকে (সহজ)')}</p>
						<div class="bd-stats">
							<div class="bd-stat"><span>{lt('Accuracy', 'নির্ভুলতা')}</span><strong>{pct(metrics?.congruent_accuracy || 0)}</strong></div>
							<div class="bd-stat"><span>{lt('Mean RT', 'গড় RT')}</span><strong>{msText(metrics?.congruent_mean_rt || 0)}</strong></div>
							<div class="bd-stat"><span>{lt('Correct', 'সঠিক')}</span><strong>{n(metrics?.congruent_correct || 0)}/{n(metrics?.congruent_trials || 0)}</strong></div>
						</div>
						<p class="bd-note">{lt('Measures baseline processing speed', 'মৌলিক প্রক্রিয়াকরণের গতি মাপে')}</p>
					</div>
					<div class="breakdown-card incongruent-bd">
						<p class="bd-title">{lt('Incongruent Trials', 'অসঙ্গত ট্রায়াল')}</p>
						<p class="bd-sub">{lt('Flankers point opposite direction (hard)', 'পাশের তীরগুলো উল্টো দিকে (কঠিন)')}</p>
						<div class="bd-stats">
							<div class="bd-stat"><span>{lt('Accuracy', 'নির্ভুলতা')}</span><strong>{pct(metrics?.incongruent_accuracy || 0)}</strong></div>
							<div class="bd-stat"><span>{lt('Mean RT', 'গড় RT')}</span><strong>{msText(metrics?.incongruent_mean_rt || 0)}</strong></div>
							<div class="bd-stat"><span>{lt('Correct', 'সঠিক')}</span><strong>{n(metrics?.incongruent_correct || 0)}/{n(metrics?.incongruent_trials || 0)}</strong></div>
						</div>
						<p class="bd-note highlight">{lt('Key measure of selective attention & conflict resolution', 'নির্বাচিত মনোযোগ ও দ্বন্দ্ব সামলানোর মূল সূচক')}</p>
					</div>
				</div>
			</div>

			<!-- Interference analysis -->
			<div class="card">
				<h2 class="section-title">{lt('Interference Analysis', 'বিভ্রান্তি বিশ্লেষণ')}</h2>
				<div class="interference-grid">
					<div class="interference-card">
						<p class="if-label">{lt('Conflict Effect', 'কনফ্লিক্ট ইফেক্ট')}</p>
						<p class="if-value">{msText(metrics?.conflict_effect || 0)}</p>
						<p class="if-desc">{lt('How much slower on incongruent trials. Lower = better selective attention.', 'অসঙ্গত ট্রায়ালে কতটা ধীর। যত কম, নির্বাচিত মনোযোগ তত ভালো।')}</p>
					</div>
					<div class="interference-card">
						<p class="if-label">{lt('Interference Error Rate', 'বিভ্রান্তিজনিত ভুলের হার')}</p>
						<p class="if-value">{pct(metrics?.interference_error_rate || 0)}</p>
						<p class="if-desc">{lt('Percentage of errors caused by distraction. Lower = stronger focus.', 'বিভ্রান্তির কারণে কত শতাংশ ভুল। যত কম, মনোযোগ তত শক্তিশালী।')}</p>
					</div>
				</div>
			</div>

			<!-- Interpretation -->
			<div class="card">
				<h2 class="section-title">{lt('What This Means', 'এর অর্থ কী')}</h2>
				<p class="interp-text">{resultsSummaryText()}</p>

				<div class="insights">
					{#if (metrics?.conflict_effect || 0) < 100}
						<div class="insight excellent">
							<span class="ins-mark">&#9733;</span>
							<span>{lt('Excellent selective attention — you resist distraction very well.', 'অসাধারণ নির্বাচিত মনোযোগ — বিভ্রান্তি খুব ভালোভাবে প্রতিরোধ করতে পারেন।')}</span>
						</div>
					{:else if (metrics?.conflict_effect || 0) < 150}
						<div class="insight good">
							<span class="ins-mark">&#10003;</span>
							<span>{lt('Good selective attention. Normal interference effect.', 'ভালো নির্বাচিত মনোযোগ। বিভ্রান্তির প্রভাব স্বাভাবিক।')}</span>
						</div>
					{:else}
						<div class="insight developing">
							<span class="ins-mark">&#8594;</span>
							<span>{lt('High interference — practice focusing on relevant information only.', 'বিভ্রান্তির প্রভাব বেশি — শুধু প্রাসঙ্গিক তথ্যে মন দেওয়ার অনুশীলন করুন।')}</span>
						</div>
					{/if}

					{#if (metrics?.incongruent_accuracy || 0) > 85}
						<div class="insight excellent">
							<span class="ins-mark">&#9675;</span>
							<span>{lt('Strong accuracy on hard trials — excellent conflict resolution.', 'কঠিন ট্রায়ালেও নির্ভুলতা খুব ভালো — দ্বন্দ্ব সামলানোর ক্ষমতা শক্তিশালী।')}</span>
						</div>
					{/if}

					{#if (metrics?.congruent_mean_rt || 0) < 500 && (metrics?.congruent_mean_rt || 0) > 0}
						<div class="insight good">
							<span class="ins-mark">&#9650;</span>
							<span>{lt('Fast processing speed on easy trials.', 'সহজ ট্রায়ালে প্রক্রিয়াকরণের গতি দ্রুত।')}</span>
						</div>
					{/if}
				</div>
			</div>

			<!-- Clinical context -->
			<div class="card clinical-context-card">
				<h3 class="card-heading">{lt('Clinical Context', 'ক্লিনিক্যাল প্রেক্ষাপট')}</h3>
				<p>
					{@html lt(
						'The <strong>Conflict Effect</strong> (incongruent RT minus congruent RT) is the key index of selective attention. Research demonstrates this reflects anterior cingulate cortex function and executive control. Reducing your conflict effect through training indicates improved ability to ignore distractions and focus on relevant information.',
						'<strong>কনফ্লিক্ট ইফেক্ট</strong> (অসঙ্গত RT বিয়োগ সঙ্গত RT) হলো নির্বাচিত মনোযোগের মূল সূচক। গবেষণায় দেখা যায়, এটি অ্যান্টেরিয়র সিংগুলেট কর্টেক্স ও নির্বাহী নিয়ন্ত্রণ নেটওয়ার্কের কার্যকারিতা প্রতিফলিত করে।'
					)}
				</p>
			</div>

			<div class="btn-row">
				<button class="start-button" on:click={() => goto('/dashboard')}>
					{lt('Back to Dashboard', 'ড্যাশবোর্ডে ফিরে যান')}
				</button>
				<button class="secondary-button" on:click={returnToDashboard}>
					{lt('View Dashboard', 'ড্যাশবোর্ড দেখুন')}
				</button>
			</div>
		</div>
	{/if}
</div>

<!-- Help FAB -->
{#if phase === 'intro' || phase === 'instructions'}
	<button class="help-fab" on:click={() => (showHelp = true)} aria-label={t('Help')}>?</button>
{/if}

{#if showHelp}
	<div class="modal-overlay" on:click={() => (showHelp = false)} role="button" tabindex="0"
		on:keydown={(e) => e.key === 'Escape' && (showHelp = false)}>
		<div class="modal-content" on:click|stopPropagation role="dialog" aria-modal="true">
			<button class="close-btn" on:click={() => (showHelp = false)} aria-label={t('Close')}>&times;</button>
			<h3>{lt('Quick Help', 'দ্রুত সহায়তা')}</h3>
			<div class="strategy">
				<p><strong>{lt('Goal:', 'লক্ষ্য:')}</strong> {lt('Identify the CENTER arrow direction and press matching key.', 'মাঝের তীরের দিক চিহ্নিত করে সঠিক কী চাপুন।')}</p>
				<p><strong>{lt('Keys:', 'কী:')}</strong> {lt('Left arrow / A = left, Right arrow / D = right.', 'বাম তীর / A = বাম, ডান তীর / D = ডান।')}</p>
				<p><strong>{lt('Tip:', 'টিপস:')}</strong> {lt('Always ignore the flanking arrows — they are designed to distract you.', 'পাশের তীরগুলো সবসময় উপেক্ষা করুন — এগুলো আপনাকে বিভ্রান্ত করতে ডিজাইন করা হয়েছে।')}</p>
			</div>
		</div>
	</div>
{/if}

<style>
	/* ── Base ──────────────────────────────────────────────── */
	.flanker-container {
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

	/* ── Intro unified card (GoNoGo-style single container) ─── */
	.intro-wrapper {
		max-width: 960px;
		margin: 0 auto;
		background: white;
		border-radius: 16px;
		padding: 2.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07), 0 1px 3px rgba(0, 0, 0, 0.06);
		display: flex;
		flex-direction: column;
		gap: 1.8rem;
	}

	/* Flatten individual section cards inside the intro wrapper */
	.intro-wrapper > .card {
		box-shadow: none;
		border-radius: 12px;
		padding: 1.5rem;
	}

	/* info-grid cards stay as subtle embedded cards */
	.intro-wrapper .info-grid .card {
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
		border-radius: 12px;
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

	/* ── Task concept card ─────────────────────────────────── */
	.task-concept {
		background: linear-gradient(135deg, #e0f2fe 0%, #f0f9ff 100%);
		border: 1px solid #bae6fd;
	}

	.concept-badge {
		display: inline-block;
		background: #0ea5e9;
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

	.rule-num.sky { background: #0ea5e9; color: #fff; }

	.rule-body {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
		font-size: 0.95rem;
		color: #374151;
	}

	.rule-body strong { color: #1e293b; }
	.rule-body span { font-size: 0.85rem; color: #64748b; }

	.arrow-demo {
		font-size: 1.5rem;
		font-weight: 700;
		letter-spacing: 0.3rem;
		padding: 0.25rem 0;
	}

	.congruent-demo { color: #059669; }
	.incongruent-demo { color: #dc2626; }

	.key-demo {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.95rem;
	}

	kbd {
		background: #1e293b;
		color: #fff;
		padding: 0.2rem 0.6rem;
		border-radius: 6px;
		font-family: monospace;
		font-weight: 700;
		font-size: 0.9rem;
		box-shadow: 0 2px 0 #0f172a;
	}

	/* ── Info grid ─────────────────────────────────────────── */
	.info-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.5rem;
	}

	.step-list {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.step-list li {
		display: flex;
		align-items: flex-start;
		gap: 0.75rem;
	}

	.step-num {
		width: 2rem;
		height: 2rem;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 700;
		font-size: 0.85rem;
		flex-shrink: 0;
	}

	.step-num.sky { background: #0ea5e9; color: #fff; }

	.step-list strong { color: #1e293b; font-size: 0.95rem; display: block; }
	.step-list p { margin: 0.15rem 0 0; font-size: 0.85rem; color: #64748b; }

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

	.dot.sky { background: #0ea5e9; }

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
	.perf-guide { }

	.norm-bars {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.norm-bar {
		display: grid;
		grid-template-columns: 110px 1fr 90px;
		align-items: center;
		gap: 0.75rem;
	}

	.norm-label {
		font-size: 0.9rem;
		font-weight: 600;
		color: #374151;
	}

	.norm-track {
		height: 10px;
		background: #e2e8f0;
		border-radius: 999px;
		overflow: hidden;
	}

	.norm-fill { height: 100%; border-radius: 999px; }
	.norm-fill.sky { background: #0ea5e9; }
	.norm-fill.sky-mid { background: #38bdf8; }
	.norm-fill.sky-low { background: #7dd3fc; }

	.norm-val {
		font-size: 0.85rem;
		color: #64748b;
		text-align: right;
	}

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

	/* ── Instructions card ─────────────────────────────────── */
	.instructions-card { max-width: 720px; margin: 0 auto; width: 100%; }

	.instr-title {
		font-size: 1.5rem;
		font-weight: 800;
		color: #1e293b;
		text-align: center;
		margin-bottom: 1.5rem;
	}

	.key-row {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1.5rem;
		margin-bottom: 1.5rem;
	}

	.key-col {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.9rem;
		font-weight: 600;
		color: #64748b;
	}

	.key-sep { font-size: 1rem; color: #94a3b8; }

	.key-xl {
		font-size: 2rem;
		padding: 0.75rem 1.25rem;
	}

	.rule-callout {
		background: #e0f2fe;
		border-left: 4px solid #0ea5e9;
		border-radius: 10px;
		padding: 1rem 1.25rem;
		font-size: 1rem;
		color: #0c4a6e;
		margin-bottom: 1.5rem;
		line-height: 1.6;
	}

	.flow-row {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		margin-bottom: 1.5rem;
		padding: 1.25rem;
		background: #f8fafc;
		border-radius: 12px;
	}

	.flow-step {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.4rem;
		flex: 1;
		max-width: 140px;
	}

	.flow-num {
		width: 2.5rem;
		height: 2.5rem;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 700;
		font-size: 1.1rem;
	}

	.flow-num.sky { background: #0ea5e9; color: #fff; }

	.flow-label { font-weight: 600; font-size: 0.9rem; color: #1e293b; text-align: center; margin: 0; }
	.flow-sub { font-size: 0.8rem; color: #64748b; text-align: center; margin: 0; }

	.flow-connector {
		width: 2rem;
		height: 2px;
		background: #cbd5e1;
		flex-shrink: 0;
	}

	.example-block {
		border-radius: 12px;
		overflow: hidden;
		margin-bottom: 1.5rem;
		border: 1px solid #e2e8f0;
	}

	.example-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 1rem 1.25rem;
		background: #f8fafc;
	}

	.incongruent-row { background: #fef2f2; }

	.ex-stim {
		font-size: 1.5rem;
		font-weight: 700;
		letter-spacing: 0.25rem;
	}

	.congruent-stim { color: #059669; }
	.incongruent-stim { color: #dc2626; }

	.ex-ans {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		font-weight: 600;
		color: #374151;
		font-size: 0.95rem;
	}

	.ex-note { font-size: 0.85rem; color: #64748b; font-weight: 400; }

	.strategy-box {
		background: #f8fafc;
		border-radius: 12px;
		padding: 1.25rem;
		margin-bottom: 1.5rem;
	}

	.strategy-box h4 {
		font-size: 0.95rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 0.75rem;
	}

	.strategy-box ul {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.strategy-box li {
		font-size: 0.9rem;
		color: #374151;
		padding-left: 1.25rem;
		position: relative;
	}

	.strategy-box li::before {
		content: '\2192';
		position: absolute;
		left: 0;
		color: #0ea5e9;
		font-weight: 700;
	}

	/* ── Trial/Practice wrapper ────────────────────────────── */
	.trial-wrapper {
		max-width: 800px;
		margin: 0 auto;
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	.trial-top { text-align: center; }

	.trial-counter {
		font-size: 1.25rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 0.25rem;
	}

	.trial-hint {
		font-size: 0.95rem;
		color: #64748b;
		margin: 0;
	}

	/* ── Progress bar ──────────────────────────────────────── */
	.progress-bar-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.progress-label { font-size: 0.95rem; font-weight: 600; color: #374151; }

	.remaining-badge {
		background: #e0f2fe;
		color: #0369a1;
		padding: 0.2rem 0.75rem;
		border-radius: 999px;
		font-size: 0.85rem;
		font-weight: 600;
	}

	.progress-track {
		width: 100%;
		height: 8px;
		background: #e2e8f0;
		border-radius: 999px;
		overflow: hidden;
	}

	.progress-fill {
		height: 100%;
		background: linear-gradient(90deg, #0ea5e9, #764ba2);
		border-radius: 999px;
		transition: width 0.3s ease;
	}

	/* ── Stimulus card ─────────────────────────────────────── */
	.stimulus-card {
		min-height: 340px;
		background: #fff;
		border-radius: 16px;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.arrow-stim {
		font-size: 4rem;
		font-weight: 700;
		letter-spacing: 1rem;
		padding: 2rem;
	}

	.arrow-stim.congruent { color: #059669; }
	.arrow-stim.incongruent { color: #dc2626; }

	.fixation {
		font-size: 4rem;
		color: #94a3b8;
		font-weight: 300;
		line-height: 1;
	}

	/* ── Feedback pill ─────────────────────────────────────── */
	.feedback-pill {
		text-align: center;
		padding: 1rem 1.5rem;
		border-radius: 12px;
		font-size: 1rem;
		font-weight: 600;
	}

	.feedback-pill.success { background: #d1fae5; color: #065f46; border: 1.5px solid #34d399; }
	.feedback-pill.error   { background: #fee2e2; color: #991b1b; border: 1.5px solid #f87171; }
	.feedback-pill.warning { background: #fef3c7; color: #92400e; border: 1.5px solid #fbbf24; }

	/* ── Results ───────────────────────────────────────────── */
	.results-header {
		text-align: center;
		padding: 0.5rem 0;
	}

	.results-header h1 { font-size: 1.75rem; font-weight: 800; color: #1e293b; margin-bottom: 0.75rem; }

	.perf-pill {
		display: inline-block;
		padding: 0.4rem 1.5rem;
		border-radius: 999px;
		font-size: 1rem;
		font-weight: 700;
	}

	.perf-pill.perf-excellent { background: #d1fae5; color: #065f46; }
	.perf-pill.perf-good      { background: #dbeafe; color: #1e40af; }
	.perf-pill.perf-fair      { background: #fef3c7; color: #92400e; }
	.perf-pill.perf-poor      { background: #f3f4f6; color: #374151; }

	/* ── Metrics grid ──────────────────────────────────────── */
	.metrics-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 1rem;
	}

	.metric-card {
		background: #fff;
		border-radius: 16px;
		padding: 1.5rem 1rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
		text-align: center;
	}

	.metric-card.sky-top { border-top: 4px solid #0ea5e9; }

	.m-label {
		font-size: 0.75rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: #64748b;
		margin-bottom: 0.5rem;
	}

	.m-value {
		font-size: 2rem;
		font-weight: 800;
		color: #1e293b;
		margin-bottom: 0.25rem;
	}

	.m-sub { font-size: 0.8rem; color: #94a3b8; }

	/* ── Breakdown ─────────────────────────────────────────── */
	.breakdown-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem; }

	.breakdown-card {
		border-radius: 12px;
		padding: 1.25rem;
	}

	.congruent-bd  { background: linear-gradient(135deg, #d1fae5 0%, #f0fdf4 100%); border: 1px solid #6ee7b7; }
	.incongruent-bd { background: linear-gradient(135deg, #fee2e2 0%, #fff1f2 100%); border: 1px solid #fca5a5; }

	.bd-title { font-size: 1rem; font-weight: 700; color: #1e293b; margin: 0 0 0.2rem; }
	.bd-sub { font-size: 0.85rem; color: #64748b; margin: 0 0 1rem; }

	.bd-stats { display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 0.75rem; }

	.bd-stat {
		display: flex;
		justify-content: space-between;
		font-size: 0.9rem;
		color: #374151;
		padding-bottom: 0.4rem;
		border-bottom: 1px solid rgba(0,0,0,0.07);
	}

	.bd-stat strong { color: #1e293b; font-weight: 700; }

	.bd-note { font-size: 0.85rem; color: #64748b; font-style: italic; margin: 0; }
	.bd-note.highlight { color: #dc2626; font-weight: 600; font-style: normal; }

	/* ── Interference ──────────────────────────────────────── */
	.interference-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem; }

	.interference-card {
		background: linear-gradient(135deg, #fef3c7 0%, #fffbeb 100%);
		border: 1px solid #fcd34d;
		border-radius: 12px;
		padding: 1.25rem;
		text-align: center;
	}

	.if-label { font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #78350f; margin-bottom: 0.5rem; }
	.if-value { font-size: 2rem; font-weight: 800; color: #92400e; margin-bottom: 0.5rem; }
	.if-desc  { font-size: 0.85rem; color: #78350f; line-height: 1.5; margin: 0; }

	/* ── Interpretation ────────────────────────────────────── */
	.interp-text { font-size: 1rem; line-height: 1.7; color: #374151; margin-bottom: 1.25rem; }

	.insights { display: flex; flex-direction: column; gap: 0.75rem; }

	.insight {
		display: flex;
		align-items: flex-start;
		gap: 0.75rem;
		padding: 0.85rem 1rem;
		border-radius: 10px;
		font-size: 0.95rem;
	}

	.insight.excellent  { background: #d1fae5; border-left: 4px solid #10b981; color: #065f46; }
	.insight.good       { background: #dbeafe; border-left: 4px solid #3b82f6; color: #1e40af; }
	.insight.developing { background: #fef3c7; border-left: 4px solid #f59e0b; color: #92400e; }

	.ins-mark { font-size: 1.2rem; flex-shrink: 0; margin-top: 0.05rem; }

	/* ── Clinical context ──────────────────────────────────── */
	.clinical-context-card { background: #f8fafc; border: 1px solid #e2e8f0; }
	.clinical-context-card p { font-size: 0.95rem; line-height: 1.7; color: #374151; margin: 0; }

	/* ── Help FAB & modal ──────────────────────────────────── */
	.help-fab {
		position: fixed;
		bottom: 2rem;
		right: 2rem;
		width: 3rem;
		height: 3rem;
		border-radius: 50%;
		background: #0ea5e9;
		color: #fff;
		border: none;
		font-size: 1.25rem;
		font-weight: 800;
		cursor: pointer;
		box-shadow: 0 4px 12px rgba(14, 165, 233, 0.4);
		z-index: 50;
		transition: transform 0.15s;
	}

	.help-fab:hover { transform: scale(1.1); }

	.modal-overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.45);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 100;
		padding: 1rem;
	}

	.modal-content {
		background: #fff;
		border-radius: 16px;
		padding: 2rem;
		max-width: 480px;
		width: 100%;
		position: relative;
		box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
	}

	.modal-content h3 { font-size: 1.1rem; font-weight: 700; color: #1e293b; margin-bottom: 1rem; }

	.close-btn {
		position: absolute;
		top: 1rem;
		right: 1rem;
		background: none;
		border: none;
		font-size: 1.5rem;
		color: #64748b;
		cursor: pointer;
		line-height: 1;
	}

	.strategy { display: flex; flex-direction: column; gap: 0.6rem; }
	.strategy p { font-size: 0.9rem; color: #374151; margin: 0; line-height: 1.6; }

	/* ── Responsive ────────────────────────────────────────── */
	@media (max-width: 768px) {
		.flanker-container { padding: 1rem 0.75rem; }
		h1 { font-size: 1.5rem; }
		.rules-grid,
		.info-grid,
		.clinical-grid,
		.breakdown-grid,
		.interference-grid { grid-template-columns: 1fr; }
		.metrics-grid { grid-template-columns: 1fr 1fr; }
		.arrow-stim { font-size: 2.5rem; letter-spacing: 0.5rem; }
		.arrow-demo { font-size: 1.2rem; letter-spacing: 0.2rem; }
		.flow-row { flex-direction: column; gap: 0.75rem; }
		.flow-connector { width: 2px; height: 1.5rem; }
		.norm-bar { grid-template-columns: 90px 1fr 70px; }
	}

	@media (max-width: 480px) {
		.metrics-grid { grid-template-columns: 1fr; }
	}

	/* ── Unified intro card ─────────────────────────────────── */
	.task-shell {
		max-width: 920px;
		margin: 0 auto;
		padding-top: 1rem;
	}

	.intro-main-card {
		background: #ffffff;
		border-radius: 16px;
		padding: 2.5rem 2.25rem;
		box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
	}

	.intro-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 1rem;
		margin-bottom: 1.8rem;
	}

	.intro-header h1 {
		font-size: 2rem;
		font-weight: 800;
		color: #0f172a;
		margin: 0 0 0.4rem;
	}

	.concept-strip {
		background: #eaf8ff;
		border: 1px solid #bae6fd;
		border-radius: 14px;
		padding: 1.4rem 1.6rem;
		margin-bottom: 1.5rem;
	}

	.concept-strip p {
		margin: 0;
		font-size: 1rem;
		line-height: 1.7;
		color: #0f172a;
	}

	.challenge-box {
		background: #f5edff;
		border: 1px solid #c4b5fd;
		border-radius: 14px;
		padding: 1.5rem;
		margin-bottom: 1.5rem;
	}

	.challenge-box h2 {
		margin: 0 0 0.7rem;
		font-size: 1.05rem;
		font-weight: 800;
		color: #6d28d9;
	}

	.challenge-box p {
		color: #2e1065;
		line-height: 1.7;
		margin-bottom: 1.2rem;
	}

	.arrow-example-box {
		background: #ffffff;
		border-radius: 12px;
		padding: 1.2rem;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 2rem;
		box-shadow: 0 4px 10px rgba(15, 23, 42, 0.06);
	}

	.arrow-side {
		text-align: center;
	}

	.arrow-side span {
		display: block;
		margin-top: 0.4rem;
		font-size: 0.85rem;
		font-weight: 600;
		color: #475569;
	}

	.vs-text {
		font-weight: 800;
		color: #7c3aed;
	}

	.fixed-rules {
		margin-bottom: 1.5rem;
	}

	.clinical-strip {
		background: #f8fafc;
		border-left: 4px solid #7c3aed;
		border-radius: 12px;
		padding: 1.2rem 1.4rem;
		margin-bottom: 1.5rem;
	}

	.clinical-strip h3 {
		margin: 0 0 0.5rem;
		font-size: 1rem;
		font-weight: 800;
		color: #0f172a;
	}

	.clinical-strip p {
		margin: 0;
		color: #475569;
		line-height: 1.6;
	}

	@media (max-width: 768px) {
		.intro-main-card { padding: 1.5rem; }
		.intro-header { flex-direction: column; }
		.arrow-example-box { flex-direction: column; gap: 1rem; }
	}
</style>


<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
	import { formatNumber, formatPercent, locale, localeText, translateText } from '$lib/i18n';
	import { getGoNoGoStimulus, getGoNoGoStimulusPair } from '$lib/i18n/task-ui.js';
	import { user } from '$lib/stores';
	import { getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
	import { onMount } from 'svelte';

	const API_BASE_URL = 'http://127.0.0.1:8000';

	let currentUser = null;
	let loading = true;
	let sessionData = null;
	let difficulty = 1;
	let currentTrial = 0;
	let responses = [];
	let phase = 'intro'; // intro, instructions, practice, test, results
	let showResults = false;
	let metrics = null;
	let newBadges = [];
	let taskId = null;
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';

	// Practice state
	let practiceTrials = [];
	let currentPractice = 0;
	let practiceFeedback = null;
	let practiceAdvanceTimeout = null;
	let practiceFinishTimeout = null;

	// Test state
	let startTime = 0;
	let responded = false;
	let showStimulus = false;
	let trialTimeout = null;
	let stimulusTimeout = null;
	let interStimulusTimeout = null;

	// Help modal
	let showHelp = false;

	// Subscribe to user store
	user.subscribe((value) => {
		currentUser = value;
	});

	onMount(async () => {
		if (!currentUser) {
			goto('/login');
			return;
		}
		await loadSession();
	});

	async function loadSession() {
		try {
			loading = true;
			const response = await fetch(`${API_BASE_URL}/api/training/tasks/gonogo/generate/${currentUser.id}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' }
			});

			if (!response.ok) {
				const errorText = await response.text();
				throw new Error(`Failed to load session: ${response.status} - ${errorText}`);
			}

			const data = await response.json();
			sessionData = data.session_data;
			difficulty = data.difficulty;
			loading = false;
		} catch (error) {
			console.error('Error loading session:', error);
			alert(
				lt(
					'Failed to load training session. Please ensure the backend server is running and you have completed the baseline assessment.',
					'ট্রেনিং সেশন লোড করা যায়নি। ব্যাকএন্ড সার্ভার চালু আছে কি না এবং বেসলাইন মূল্যায়ন সম্পন্ন হয়েছে কি না নিশ্চিত করুন।'
				)
			);
			loading = false;
		}
	}

	function startInstructions() {
		phase = 'instructions';
	}

	function t(text) {
		return translateText(text, $locale);
	}

	function lt(en, bn) {
		return localeText({ en, bn }, $locale);
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

	function msText(value) {
		return $locale === 'bn' ? `${n(value)} মিলিসেকেন্ড` : `${n(value)} ms`;
	}

	function formatMilliseconds(value) {
		if ($locale === 'bn') {
			return `${n(value)} মিলিসেকেন্ড`;
		}

		return `${n(value)}ms`;
	}

	function performanceLevelLabel(level) {
		switch (level) {
			case 'Excellent':
				return lt('Excellent', 'চমৎকার');
			case 'Good':
				return lt('Good', 'ভালো');
			case 'Fair':
				return lt('Fair', 'মোটামুটি');
			case 'Needs Improvement':
				return lt('Needs Improvement', 'উন্নতির সুযোগ আছে');
			default:
				return t(level || 'Performance');
		}
	}

	function practiceTrialLabel(current, total) {
		return lt(`Practice Trial ${n(current)} of ${n(total)}`, `অনুশীলনী ট্রায়াল ${n(current)} / ${n(total)}`);
	}

	function trialLabel(current, total) {
		return lt(`Trial ${n(current)} of ${n(total)}`, `ট্রায়াল ${n(current)} / ${n(total)}`);
	}

	function remainingTrialsLabel(count) {
		return lt(`${n(count)} remaining`, `${n(count)}টি বাকি`);
	}

	function getDisplayStimulusPair() {
		return getGoNoGoStimulusPair(sessionData?.stimulus_set, $locale, {
			go: sessionData?.go_stimulus || '',
			nogo: sessionData?.nogo_stimulus || ''
		});
	}

	function displayStimulus(trial) {
		if (!trial) return '';

		const fallback =
			trial.trial_type === 'nogo'
				? sessionData?.nogo_stimulus || trial.stimulus || ''
				: sessionData?.go_stimulus || trial.stimulus || '';

		return getGoNoGoStimulus(sessionData?.stimulus_set, trial.trial_type, $locale, fallback);
	}

	function localizedPracticeHint(trial) {
		if (!trial?.hint) return '';
		return lt(trial.hint.en, trial.hint.bn);
	}

	function practiceSuccessMessage(rt, trial) {
		if (trial.trial_type === 'go') {
			return lt(
				`Correct! Response time: ${msText(rt)}. ${localizedPracticeHint(trial)}`,
				`সঠিক! প্রতিক্রিয়ার সময়: ${msText(rt)}। ${localizedPracticeHint(trial)}`
			);
		}

		return lt(
			`Perfect! You successfully withheld your response. ${localizedPracticeHint(trial)}`,
			`দারুণ! আপনি ঠিকভাবে সাড়া থামিয়ে রাখতে পেরেছেন। ${localizedPracticeHint(trial)}`
		);
	}

	function practiceErrorMessage(trial) {
		if (trial.trial_type === 'go') {
			return lt(
				`You should have pressed SPACEBAR. ${localizedPracticeHint(trial)}`,
				`এখানে আপনার স্পেসবার চাপা উচিত ছিল। ${localizedPracticeHint(trial)}`
			);
		}

		return lt(
			`You pressed when you should not have. ${localizedPracticeHint(trial)}`,
			`এখানে আপনার চাপা উচিত ছিল না। ${localizedPracticeHint(trial)}`
		);
	}

	function buildPracticeTrials() {
		return [
			{
				trial_type: 'go',
				hint: {
					en: 'Press SPACEBAR when you see this.',
					bn: 'এটি দেখলে স্পেসবার চাপুন।'
				}
			},
			{
				trial_type: 'go',
				hint: {
					en: 'Quick, press SPACEBAR again.',
					bn: 'দ্রুত আবার স্পেসবার চাপুন।'
				}
			},
			{
				trial_type: 'nogo',
				hint: {
					en: 'Do not press. Just wait.',
					bn: 'চাপবেন না, শুধু অপেক্ষা করুন।'
				}
			},
			{
				trial_type: 'go',
				hint: {
					en: 'Be ready and press SPACEBAR.',
					bn: 'প্রস্তুত থাকুন এবং স্পেসবার চাপুন।'
				}
			},
			{
				trial_type: 'nogo',
				hint: {
					en: 'Remember, do not press for this one.',
					bn: 'মনে রাখুন, এটি দেখলে চাপবেন না।'
				}
			},
			{
				trial_type: 'go',
				hint: {
					en: 'Final practice, press SPACEBAR.',
					bn: 'শেষ অনুশীলন, স্পেসবার চাপুন।'
				}
			}
		];
	}

	function resultsSummaryText() {
		const nogoAccuracy = Number(metrics?.nogo_accuracy || 0);
		const goSpeed = Number(metrics?.go_mean_rt || 0);
		const dPrime = Number(metrics?.d_prime || 0);

		if (nogoAccuracy >= 90 && dPrime >= 2 && goSpeed < 450) {
			return lt(
				'Excellent inhibitory control and selective attention throughout the task.',
				'পুরো টাস্ক জুড়ে আপনার প্রতিক্রিয়া নিয়ন্ত্রণ ও নির্বাচিত মনোযোগ চমৎকার ছিল।'
			);
		}

		if (nogoAccuracy >= 75 && dPrime >= 1) {
			return lt(
				'You maintained solid control with generally reliable attention and inhibition.',
				'আপনি ভালো নিয়ন্ত্রণ ধরে রাখতে পেরেছেন এবং মনোযোগ ও প্রতিক্রিয়া থামিয়ে রাখার দক্ষতা মোটের উপর নির্ভরযোগ্য ছিল।'
			);
		}

		if (nogoAccuracy >= 60) {
			return lt(
				'Your performance was workable, but impulse control and consistency can still improve with practice.',
				'আপনার পারফরম্যান্স গ্রহণযোগ্য ছিল, তবে অনুশীলনের মাধ্যমে আবেগ সংযম ও ধারাবাহিকতা আরও উন্নত হতে পারে।'
			);
		}

		return lt(
			'This session was challenging, which suggests inhibitory control needs more structured practice.',
			'এই সেশনটি আপনার জন্য কঠিন ছিল, যা ইঙ্গিত করে প্রতিক্রিয়া নিয়ন্ত্রণ আরও অনুশীলন চায়।'
		);
	}

	function difficultyChangeText(before, after) {
		return lt(
			`Difficulty adjusted: Level ${n(before)} -> Level ${n(after)}`,
			`কঠিনতা সমন্বয় করা হয়েছে: লেভেল ${n(before)} -> লেভেল ${n(after)}`
		);
	}

	function startPractice() {
		clearTimeout(practiceAdvanceTimeout);
		clearTimeout(practiceFinishTimeout);
		playMode = TASK_PLAY_MODE.PRACTICE;
		practiceStatusMessage = '';
		practiceTrials = buildPracticeTrials();

		currentPractice = 0;
		practiceFeedback = null;
		phase = 'practice';
		showNextPracticeTrial();
	}

	function finishPractice(completed = true) {
		clearTimeout(stimulusTimeout);
		clearTimeout(interStimulusTimeout);
		clearTimeout(trialTimeout);
		clearTimeout(practiceAdvanceTimeout);
		clearTimeout(practiceFinishTimeout);
		playMode = TASK_PLAY_MODE.RECORDED;
		responded = false;
		showStimulus = false;
		practiceFeedback = null;
		currentPractice = 0;
		phase = 'instructions';
		practiceStatusMessage = completed ? getPracticeCopy($locale).complete : '';
	}

	function showNextPracticeTrial() {
		// Clear any existing timers
		clearTimeout(stimulusTimeout);
		clearTimeout(interStimulusTimeout);
		clearTimeout(practiceAdvanceTimeout);
		clearTimeout(practiceFinishTimeout);
		
		if (currentPractice >= practiceTrials.length) {
			practiceFinishTimeout = setTimeout(() => {
				practiceFinishTimeout = null;
				finishPractice();
			}, 1500);
			return;
		}

		responded = false;
		showStimulus = true;
		startTime = Date.now();

		// Auto-advance after presentation time
		stimulusTimeout = setTimeout(() => {
			if (!responded) {
				handlePracticeResponse(false);
			}
		}, 2000); // 2 seconds for practice
	}

	function legacyHandlePracticeResponse(didRespond) {
		clearTimeout(stimulusTimeout);
		
		const trial = practiceTrials[currentPractice];
		const correct = (trial.trial_type === 'go' && didRespond) || 
		                (trial.trial_type === 'nogo' && !didRespond);

		if (correct) {
			if (trial.trial_type === 'go') {
				const rt = Date.now() - startTime;
				practiceFeedback = {
					type: 'success',
					message: `✓ ${t('Correct!')} ${t('Response time')}: ${formatMilliseconds(rt)}. ${trial.hint}`
				};
			} else {
				practiceFeedback = {
					type: 'success',
					message: `✓ ${t('Perfect! You successfully withheld your response.')} ${trial.hint}`
				};
			}
		} else {
			if (trial.trial_type === 'go') {
				practiceFeedback = {
					type: 'error',
					message: `✗ ${t('You should have pressed SPACEBAR.')} ${trial.hint}`
				};
			} else {
				practiceFeedback = {
					type: 'error',
					message: `✗ ${t("You pressed when you shouldn't have!")} ${trial.hint}`
				};
			}
		}

		showStimulus = false;

		// Auto-advance after showing feedback
		setTimeout(() => {
			practiceFeedback = null;
			currentPractice++;
			showNextPracticeTrial();
		}, 2000);
	}

	function handlePracticeResponse(didRespond) {
		clearTimeout(stimulusTimeout);

		const trial = practiceTrials[currentPractice];
		const correct = (trial.trial_type === 'go' && didRespond) ||
			(trial.trial_type === 'nogo' && !didRespond);

		if (correct) {
			if (trial.trial_type === 'go') {
				const rt = Date.now() - startTime;
				practiceFeedback = {
					type: 'success',
					message: `✓ ${practiceSuccessMessage(rt, trial)}`
				};
			} else {
				practiceFeedback = {
					type: 'success',
					message: `✓ ${practiceSuccessMessage(0, trial)}`
				};
			}
		} else {
			practiceFeedback = {
				type: 'error',
				message: `✗ ${practiceErrorMessage(trial)}`
			};
		}

		showStimulus = false;

		practiceAdvanceTimeout = setTimeout(() => {
			practiceAdvanceTimeout = null;
			practiceFeedback = null;
			currentPractice++;
			showNextPracticeTrial();
		}, 2000);
	}

	function startTest() {
		clearTimeout(practiceAdvanceTimeout);
		clearTimeout(practiceFinishTimeout);
		playMode = TASK_PLAY_MODE.RECORDED;
		practiceStatusMessage = '';
		phase = 'test';
		currentTrial = 0;
		responses = [];
		showNextTrial();
	}

	function showNextTrial() {
		// Clear all existing timers to prevent race conditions
		clearTimeout(stimulusTimeout);
		clearTimeout(interStimulusTimeout);
		clearTimeout(trialTimeout);
		
		if (currentTrial >= sessionData.trials.length) {
			completeSession();
			return;
		}

		responded = false;
		showStimulus = false;

		// Inter-stimulus interval
		interStimulusTimeout = setTimeout(() => {
			showStimulus = true;
			startTime = Date.now();

			// Hide stimulus after presentation time
			stimulusTimeout = setTimeout(() => {
				showStimulus = false;

				// If no response yet, record as no response after stimulus disappears
				if (!responded) {
					trialTimeout = setTimeout(() => {
						recordResponse(false);
					}, 200);
				}
			}, sessionData.presentation_time_ms);
		}, sessionData.inter_stimulus_interval_ms);
	}

	function recordResponse(didRespond) {
		if (responded) return; // Already responded
		
		// Clear all timers immediately
		clearTimeout(stimulusTimeout);
		clearTimeout(interStimulusTimeout);
		clearTimeout(trialTimeout);
		
		responded = true;

		const reactionTime = didRespond ? Date.now() - startTime : 0;
		const trial = sessionData.trials[currentTrial];

		responses.push({
			trial_number: trial.trial_number,
			trial_type: trial.trial_type,
			responded: didRespond,
			reaction_time_ms: reactionTime
		});

		currentTrial++;
		showStimulus = false;

		// Brief pause before next trial
		interStimulusTimeout = setTimeout(() => {
			showNextTrial();
		}, 300);
	}

	function handleKeyPress(event) {
		if (event.code === 'Space' || event.key === ' ') {
			event.preventDefault();
			
			if (phase === 'practice' && showStimulus && !responded) {
				responded = true;
				handlePracticeResponse(true);
			} else if (phase === 'test' && showStimulus && !responded) {
				recordResponse(true);
			}
		}
	}

	async function completeSession() {
		try {
			taskId = $page.url.searchParams.get('taskId');
			const response = await fetch(`${API_BASE_URL}/api/training/tasks/gonogo/submit/${currentUser.id}`, {
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
			showResults = true;
		} catch (error) {
			console.error('Error submitting session:', error);
			alert(lt('Failed to submit results. Please try again.', 'ফলাফল জমা দেওয়া যায়নি। আবার চেষ্টা করুন।'));
		}
	}

	function returnToDashboard() {
		goto('/dashboard');
	}

	// Progress tracking
	$: progress = sessionData ? ((currentTrial / sessionData.trials.length) * 100) : 0;
	$: trialsRemaining = sessionData ? sessionData.trials.length - currentTrial : 0;
	$: displayStimuli = getDisplayStimulusPair();
	$: goDisplayStimulus = displayStimuli.go;
	$: nogoDisplayStimulus = displayStimuli.nogo;

	// Performance badge color
	$: performanceBadgeColor = metrics?.performance_level === 'Excellent' ? 'from-green-500'
		: metrics?.performance_level === 'Good' ? 'from-blue-500'
		: metrics?.performance_level === 'Fair' ? 'from-yellow-500'
		: 'from-gray-500';
</script>

<svelte:head>
	<title>{lt('Go/No-Go Task - NeuroBloom', 'গো/নো-গো টাস্ক - NeuroBloom')}</title>
</svelte:head>

<svelte:window on:keydown={handleKeyPress} />

<div class="gonogo-container" data-localize-skip>
	<div class="gonogo-inner">

		{#if loading}
			<LoadingSkeleton variant="card" count={3} />

		{:else if phase === 'intro'}
			<div class="instructions-card">
				<div class="header-content">
					<div class="title-row">
						<h1>{lt('Go/No-Go Task', 'গো/নো-গো টাস্ক')}</h1>
						<DifficultyBadge {difficulty} domain="Attention" />
					</div>
					<p class="subtitle">{lt('Response Inhibition and Impulse Control Assessment', 'প্রতিক্রিয়া নিয়ন্ত্রণ ও আবেগ সংযম মূল্যায়ন')}</p>
					<div class="classic-badge">{lt('Executive Function — Response Inhibition (Diamond, 2013)', 'নির্বাহী দক্ষতা — প্রতিক্রিয়া নিয়ন্ত্রণ (Diamond, 2013)')}</div>
				</div>

				<div class="task-concept">
					<h3>{lt('The Core Principle', 'মূল নীতি')}</h3>
					<p>{lt('Most trials require a response, quickly building a habit. The challenge is suppressing that habit when the No-Go signal appears — this directly tests impulse control and prefrontal inhibition.', 'বেশিরভাগ ট্রায়ালে সাড়া দিতে হয়, দ্রুত একটি অভ্যাস তৈরি হয়। চ্যালেঞ্জ হলো নো-গো সংকেত দেখলে সেই অভ্যাস দমন করা — এটি সরাসরি আবেগ সংযম ও প্রিফ্রন্টাল নিয়ন্ত্রণ যাচাই করে।')}</p>
					<div class="stimulus-examples">
						<div class="ex-card ex-go">
							<div class="ex-type">{lt('GO Trial (75%)', 'গো ট্রায়াল (৭৫%)')}</div>
							<div class="stimulus-demo go-demo">{goDisplayStimulus}</div>
							<div class="ex-action go-action">{lt('PRESS SPACEBAR', 'স্পেসবার চাপুন')}</div>
							<div class="ex-note">{lt('Respond as quickly as possible', 'যত দ্রুত সম্ভব সাড়া দিন')}</div>
						</div>
						<div class="ex-card ex-nogo">
							<div class="ex-type">{lt('NO-GO Trial (25%)', 'নো-গো ট্রায়াল (২৫%)')}</div>
							<div class="stimulus-demo nogo-demo">{nogoDisplayStimulus}</div>
							<div class="ex-action nogo-action">{lt("DON'T PRESS", 'চাপবেন না')}</div>
							<div class="ex-note">{lt('Resist the automatic response', 'স্বয়ংক্রিয় সাড়া থামিয়ে রাখুন')}</div>
						</div>
					</div>
					<div class="key-rule-box">
						<strong>{lt('The Challenge:', 'মূল চ্যালেঞ্জ:')}</strong>
						{lt('75% of trials are GO — your brain builds a pressing habit. On NO-GO trials, you must override that habit. This tests executive inhibitory control.', '৭৫% ট্রায়ালই গো — মস্তিষ্ক দ্রুত একটি চাপার অভ্যাস গড়ে তোলে। নো-গো ট্রায়ালে সেই অভ্যাস ভেঙে বেরিয়ে আসতে হবে। এটিই নির্বাহী নিয়ন্ত্রণ ক্ষমতা যাচাই করে।')}
					</div>
				</div>

				<div class="rules-grid">
					<div class="rule-card">
						<span class="rule-num">1</span>
						<div class="rule-text">
							<strong>{lt('Watch the Screen', 'স্ক্রিনে নজর রাখুন')}</strong>
							<span>{lt('A stimulus appears briefly on screen', 'স্ক্রিনে অল্প সময়ের জন্য একটি উদ্দীপক দেখা যাবে')}</span>
						</div>
					</div>
					<div class="rule-card">
						<span class="rule-num">2</span>
						<div class="rule-text">
							<strong>{lt('Identify Quickly', 'দ্রুত চিহ্নিত করুন')}</strong>
							<span>{lt('Is it a GO or NO-GO stimulus?', 'এটি গো নাকি নো-গো উদ্দীপক?')}</span>
						</div>
					</div>
					<div class="rule-card">
						<span class="rule-num">3</span>
						<div class="rule-text">
							<strong>{lt('Respond or Withhold', 'সাড়া দিন বা থামুন')}</strong>
							<span>{lt('Press SPACEBAR for GO, do nothing for NO-GO', 'গো-তে স্পেসবার চাপুন, নো-গো-তে কিছু করবেন না')}</span>
						</div>
					</div>
					<div class="rule-card">
						<span class="rule-num">4</span>
						<div class="rule-text">
							<strong>{lt('Stay Consistent', 'ধারাবাহিক থাকুন')}</strong>
							<span>{lt('Speed and accuracy both measured throughout', 'পুরো টাস্ক জুড়ে গতি ও নির্ভুলতা উভয়ই মূল্যায়ন করা হয়')}</span>
						</div>
					</div>
				</div>

				<div class="info-grid">
					<div class="info-section">
						<h4>{lt('What It Measures', 'এটি কী মাপে')}</h4>
						<ul class="tips-list">
							<li><strong>{lt('Response Speed:', 'প্রতিক্রিয়ার গতি:')}</strong> {lt('GO trial reaction time', 'গো ট্রায়ালে প্রতিক্রিয়ার সময়')}</li>
							<li><strong>{lt('Impulse Control:', 'আবেগ সংযম:')}</strong> {lt('NO-GO trial accuracy', 'নো-গো ট্রায়ালে নির্ভুলতা')}</li>
							<li><strong>{lt('Sustained Attention:', 'টেকসই মনোযোগ:')}</strong> {lt('Consistency over all trials', 'সকল ট্রায়াল জুড়ে ধারাবাহিকতা')}</li>
							<li><strong>{lt('d-prime:', 'd-prime:')}</strong> {lt('Signal detection sensitivity (higher = better)', 'সংকেত শনাক্তকরণ সংবেদনশীলতা (বেশি = ভালো)')}</li>
						</ul>
					</div>
					<div class="info-section">
						<h4>{lt('Tips for Success', 'সফল হওয়ার টিপস')}</h4>
						<ul class="structure-list">
							<li>
								<span class="struct-key">{lt('Finger Ready', 'আঙ্গুল প্রস্তুত')}</span>
								<span class="struct-val">{lt('Keep thumb on spacebar', 'বুড়ো আঙুল স্পেসবারে রাখুন')}</span>
							</li>
							<li>
								<span class="struct-key">{lt('Eyes Focused', 'দৃষ্টি কেন্দ্রীভূত')}</span>
								<span class="struct-val">{lt('Screen center at all times', 'সর্বদা স্ক্রিনের মাঝে')}</span>
							</li>
							<li>
								<span class="struct-key">{lt('No Guessing', 'অনুমান নয়')}</span>
								<span class="struct-val">{lt('Wait and see the stimulus', 'অপেক্ষা করুন, উদ্দীপক দেখুন')}</span>
							</li>
							<li>
								<span class="struct-key">{lt('Stay Alert', 'সতর্ক থাকুন')}</span>
								<span class="struct-val">{lt('Consistency matters most', 'ধারাবাহিকতাই সবচেয়ে গুরুত্বপূর্ণ')}</span>
							</li>
						</ul>
					</div>
				</div>

				<div class="clinical-info">
					<h4>{lt('Clinical Significance', 'ক্লিনিক্যাল গুরুত্ব')}</h4>
					<div class="clinical-grid">
						<div class="clinical-item">
							<strong>{lt('Standard Use', 'মানক ব্যবহার')}</strong>
							<span>{lt('ADHD, frontal lobe, and MS neuropsychological assessment', 'ADHD, ফ্রন্টাল লোব এবং MS মূল্যায়নে মানক পরীক্ষা')}</span>
						</div>
						<div class="clinical-item">
							<strong>{lt('Brain Region', 'মস্তিষ্কের অংশ')}</strong>
							<span>{lt('Prefrontal cortex — inhibitory control circuits', 'প্রিফ্রন্টাল কর্টেক্স — নিয়ন্ত্রণমূলক সার্কিট')}</span>
						</div>
						<div class="clinical-item">
							<strong>{lt('MS Relevance', 'MS-এ প্রাসঙ্গিকতা')}</strong>
							<span>{lt('Sensitive to attention deficits and executive dysfunction', 'মনোযোগ ঘাটতি ও নির্বাহী কার্যকারিতার সমস্যায় সংবেদনশীল')}</span>
						</div>
						<div class="clinical-item">
							<strong>{lt('Training Benefits', 'অনুশীলনের উপকার')}</strong>
							<span>{lt('Strengthens real-world impulse control and decision-making', 'বাস্তব জীবনের আবেগ সংযম ও সিদ্ধান্ত নেওয়া জোরদার করে')}</span>
						</div>
					</div>
				</div>

				<div class="perf-guide">
					<h4>{lt('Performance Reference (No-Go Accuracy)', 'পারফরম্যান্স রেফারেন্স (নো-গো নির্ভুলতা)')}</h4>
					<div class="norm-bars">
						<div class="norm-bar norm-excellent"><span class="norm-label">{lt('Excellent', 'চমৎকার')}</span><span class="norm-val">&ge;90%</span></div>
						<div class="norm-bar norm-good"><span class="norm-label">{lt('Good', 'ভালো')}</span><span class="norm-val">75–89%</span></div>
						<div class="norm-bar norm-avg"><span class="norm-label">{lt('Average', 'গড়')}</span><span class="norm-val">60–74%</span></div>
						<div class="norm-bar norm-fair"><span class="norm-label">{lt('Fair', 'মোটামুটি')}</span><span class="norm-val">45–59%</span></div>
						<div class="norm-bar norm-needs"><span class="norm-label">{lt('Developing', 'উন্নতির সুযোগ আছে')}</span><span class="norm-val">&lt;45%</span></div>
					</div>
					<p class="norm-note">* {lt('Some commission errors are expected — the task is designed to induce them.', 'কিছু ভুল চাপা স্বাভাবিক — টাস্কটি ইচ্ছাকৃতভাবে এটি ঘটানোর জন্য ডিজাইন করা হয়েছে।')}</p>
				</div>

				<div class="button-group">
					<button class="start-button" on:click={startInstructions}>{lt('Start Task', 'টাস্ক শুরু করুন')}</button>
					<button class="btn-secondary" on:click={() => goto('/dashboard')}>{lt('Back to Dashboard', 'ড্যাশবোর্ডে ফিরে যান')}</button>
					<button class="help-link" on:click={() => showHelp = true}>{lt('More Information', 'আরো তথ্য')}</button>
				</div>
			</div>

		{:else if phase === 'instructions'}
			<div class="screen-card quick-instructions">
				<h2>{lt('Quick Instructions', 'দ্রুত নির্দেশনা')}</h2>
				<p class="instr-subtitle">{lt('Press SPACEBAR for GO — withhold for NO-GO.', 'গো দেখলে স্পেসবার চাপুন — নো-গো দেখলে থামুন।')}</p>

				<div class="key-reminder">
					<div class="key-row">
						<div class="key-box go-key">{lt('SPACEBAR', 'স্পেসবার')}</div>
						<span class="key-for">{lt('when you see', 'যখন দেখবেন')}</span>
						<span class="inline-stim go-stim">{goDisplayStimulus}</span>
					</div>
					<div class="key-row">
						<div class="key-box nogo-key">{lt('DO NOTHING', 'কিছু করবেন না')}</div>
						<span class="key-for">{lt('when you see', 'যখন দেখবেন')}</span>
						<span class="inline-stim nogo-stim">{nogoDisplayStimulus}</span>
					</div>
				</div>

				<div class="steps-grid">
					<div class="step-card">
						<span class="step-num">1</span>
						<strong>{lt('Stimulus Appears', 'উদ্দীপক দেখা যায়')}</strong>
						<span>{lt('A symbol flashes briefly on screen', 'একটি চিহ্ন অল্প সময়ের জন্য দেখা যায়')}</span>
					</div>
					<div class="step-card">
						<span class="step-num">2</span>
						<strong>{lt('Identify It', 'চিনে নিন')}</strong>
						<span>{lt('GO or NO-GO?', 'গো নাকি নো-গো?')}</span>
					</div>
					<div class="step-card">
						<span class="step-num">3</span>
						<strong>{lt('Respond or Wait', 'সাড়া দিন বা অপেক্ষা')}</strong>
						<span>{lt('Press SPACEBAR or stay still', 'স্পেসবার চাপুন বা থামুন')}</span>
					</div>
					<div class="step-card">
						<span class="step-num">4</span>
						<strong>{lt('Stay Consistent', 'ধারাবাহিক থাকুন')}</strong>
						<span>{lt('Maintain focus until the end', 'শেষ পর্যন্ত মনোযোগ ধরে রাখুন')}</span>
					</div>
				</div>

				<div class="remember-box">
					<strong>{lt('Key reminder:', 'গুরুত্বপূর্ণ:')}</strong>
					{lt('Most trials are GO — you will build a pressing habit fast. Stay vigilant for NO-GO signals and resist.', 'বেশিরভাগ ট্রায়ালই গো — তাড়াতাড়ি চাপার অভ্যাস তৈরি হবে। নো-গো সংকেতের জন্য সজাগ থাকুন এবং সংযত থাকুন।')}
				</div>

				{#if practiceStatusMessage}
					<div class="practice-note">{practiceStatusMessage}</div>
				{/if}

				<TaskPracticeActions
					locale={$locale}
					startLabel={lt('Start Actual Task', 'আসল টাস্ক শুরু করুন')}
					statusMessage={practiceStatusMessage}
					on:start={startTest}
					on:practice={startPractice}
				/>
			</div>

		{:else if phase === 'practice'}
			<div class="screen-card trial-screen">
				<PracticeModeBanner locale={$locale} showExit on:exit={() => finishPractice(false)} />
				<div class="trial-header">
					<span class="trial-badge">{practiceTrialLabel(currentPractice + 1, practiceTrials.length)}</span>
					<span class="instr-mini">{lt(`SPACEBAR = ${goDisplayStimulus} | Withhold = ${nogoDisplayStimulus}`, `স্পেসবার = ${goDisplayStimulus} | থামুন = ${nogoDisplayStimulus}`)}</span>
				</div>

				<div class="stimulus-area">
					{#if showStimulus}
						<div class="stimulus-large"
							class:stim-go={practiceTrials[currentPractice]?.trial_type === 'go'}
							class:stim-nogo={practiceTrials[currentPractice]?.trial_type === 'nogo'}>
							{displayStimulus(practiceTrials[currentPractice])}
						</div>
					{:else}
						<div class="fixation">+</div>
					{/if}
				</div>

				{#if practiceFeedback}
					<div class="feedback-box feedback-{practiceFeedback.type}">
						{practiceFeedback.message}
					</div>
				{/if}
			</div>

		{:else if phase === 'test'}
			<div class="screen-card trial-screen">
				<div class="test-header">
					<div class="test-badges">
						<span class="trial-badge">{trialLabel(currentTrial + 1, sessionData.trials.length)}</span>
						<span class="remaining-badge">{remainingTrialsLabel(trialsRemaining)}</span>
					</div>
					<div class="progress-track">
						<div class="progress-fill" style="width: {progress}%;"></div>
					</div>
					<button class="help-btn-sm" on:click={() => showHelp = true} aria-label={lt('Help', 'সহায়তা')}>?</button>
				</div>

				<div class="stimulus-area">
					{#if showStimulus && currentTrial < sessionData.trials.length}
						<div class="stimulus-xlarge">{displayStimulus(sessionData.trials[currentTrial])}</div>
					{:else}
						<div class="fixation">+</div>
					{/if}
				</div>

				<p class="reminder-text">{lt(`Press SPACEBAR for ${goDisplayStimulus} | Don't press for ${nogoDisplayStimulus}`, `${goDisplayStimulus} দেখলে স্পেসবার চাপুন | ${nogoDisplayStimulus} দেখলে চাপবেন না`)}</p>
			</div>

		{:else if phase === 'results'}
			<div class="screen-card complete-screen">
				{#if metrics}
					<div class="perf-banner">
						<div class="perf-level">{performanceLevelLabel(metrics.performance_level)}</div>
						<div class="perf-subtitle">{lt('Go/No-Go Task Complete', 'গো/নো-গো টাস্ক সম্পন্ন')}</div>
					</div>

					<div class="metrics-grid">
						<div class="metric-card highlight">
							<div class="metric-value">{pct(metrics.overall_accuracy || 0)}</div>
							<div class="metric-label">{lt('Overall Accuracy', 'সামগ্রিক নির্ভুলতা')}</div>
							<div class="metric-sub">{lt(`${n(metrics.total_correct || 0)}/${n(metrics.total_trials || 0)} correct`, `${n(metrics.total_correct || 0)}/${n(metrics.total_trials || 0)} সঠিক`)}</div>
						</div>
						<div class="metric-card">
							<div class="metric-value">{msText(metrics.go_mean_rt || 0)}</div>
							<div class="metric-label">{lt('Go Trial Speed', 'গো ট্রায়ালের গতি')}</div>
							<div class="metric-sub">{lt('Processing speed', 'প্রসেসিং গতি')}</div>
						</div>
						<div class="metric-card">
							<div class="metric-value">{pct(metrics.nogo_accuracy || 0)}</div>
							<div class="metric-label">{lt('Inhibition Control', 'প্রতিক্রিয়া নিয়ন্ত্রণ')}</div>
							<div class="metric-sub">{lt('No-Go accuracy', 'নো-গো নির্ভুলতা')}</div>
						</div>
						<div class="metric-card">
							<div class="metric-value">{n((metrics.d_prime || 0).toFixed(2), { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
							<div class="metric-label">{lt("d-prime (Sensitivity)", "ডি-প্রাইম (সংবেদনশীলতা)")}</div>
							<div class="metric-sub">{lt('Signal detection', 'সংকেত শনাক্তকরণ')}</div>
						</div>
					</div>

					<div class="breakdown">
						<h3>{lt('Performance by Trial Type', 'ট্রায়ালভেদে পারফরম্যান্স')}</h3>
						<div class="condition-row condition-go">
							<div class="cond-header">
								<span class="cond-dot" style="background: #059669;"></span>
								<strong>{lt(`GO Trials (${n(sessionData.go_trials || 0)} trials)`, `গো ট্রায়াল (${n(sessionData.go_trials || 0)}টি)`)}</strong>
							</div>
							<div class="cond-stats">
								<span>{lt('Hits:', 'সঠিক সাড়া:')} <strong>{n(metrics.go_hits || 0)}</strong></span>
								<span>{lt('Misses:', 'মিস:')} <strong>{n(metrics.go_misses || 0)}</strong></span>
								<span>{lt('Accuracy:', 'নির্ভুলতা:')} <strong>{pct(metrics.go_accuracy || 0)}</strong></span>
								<span>{lt('Mean RT:', 'গড় RT:')} <strong>{msText(metrics.go_mean_rt || 0)}</strong></span>
								<span class="cond-note">{lt('Tests processing speed and attention', 'প্রসেসিং গতি ও মনোযোগ মাপে')}</span>
							</div>
						</div>
						<div class="condition-row condition-nogo">
							<div class="cond-header">
								<span class="cond-dot" style="background: #dc2626;"></span>
								<strong>{lt(`NO-GO Trials (${n(sessionData.nogo_trials || 0)} trials)`, `নো-গো ট্রায়াল (${n(sessionData.nogo_trials || 0)}টি)`)}</strong>
							</div>
							<div class="cond-stats">
								<span>{lt('Correct Withholds:', 'সফল বিরত:')} <strong>{n(metrics.nogo_correct || 0)}</strong></span>
								<span>{lt('Commission Errors:', 'ভুল চাপা:')} <strong class="err-val">{n(metrics.nogo_commission_errors || 0)}</strong></span>
								<span>{lt('Accuracy:', 'নির্ভুলতা:')} <strong>{pct(metrics.nogo_accuracy || 0)}</strong></span>
								<span class="cond-note">{lt('Tests impulse control and inhibition', 'আবেগ সংযম ও প্রতিক্রিয়া নিয়ন্ত্রণ মাপে')}</span>
							</div>
						</div>
					</div>

					<div class="interpretation-section">
						<h3>{lt('What This Means', 'এর অর্থ কী')}</h3>
						<p class="feedback-text">{resultsSummaryText()}</p>
						<div class="insights">
							{#if metrics.nogo_accuracy >= 90}
								<div class="insight insight-good"><strong>{lt('Excellent inhibitory control:', 'চমৎকার প্রতিক্রিয়া নিয়ন্ত্রণ:')}</strong> {lt('You successfully withheld responses on NO-GO trials.', 'নো-গো ট্রায়ালে আপনি সাড়া থামিয়ে রাখতে পেরেছেন।')}</div>
							{:else if metrics.nogo_accuracy >= 75}
								<div class="insight insight-good"><strong>{lt('Good impulse control:', 'ভালো আবেগ সংযম:')}</strong> {lt('Managing inhibition effectively.', 'বেশ কার্যকরভাবে প্রতিক্রিয়া নিয়ন্ত্রণ করেছেন।')}</div>
							{:else if metrics.nogo_accuracy >= 60}
								<div class="insight insight-moderate"><strong>{lt('Moderate inhibition:', 'মাঝারি নিয়ন্ত্রণ:')}</strong> {lt('Room to improve impulse control with practice.', 'অনুশীলনের মাধ্যমে আবেগ সংযমে আরও উন্নতির সুযোগ আছে।')}</div>
							{:else}
								<div class="insight insight-high"><strong>{lt('Challenging inhibition:', 'চ্যালেঞ্জিং নিয়ন্ত্রণ:')}</strong> {lt('Practice will strengthen impulse control.', 'অনুশীলন এই দক্ষতাকে আরও শক্তিশালী করবে।')}</div>
							{/if}
							{#if metrics.go_mean_rt < 400}
								<div class="insight insight-good"><strong>{lt('Fast processing speed:', 'দ্রুত প্রসেসিং:')}</strong> {lt('Quick reactions to GO trials.', 'গো ট্রায়ালে দ্রুত প্রতিক্রিয়া।')}</div>
							{:else if metrics.go_mean_rt < 600}
								<div class="insight insight-good"><strong>{lt('Good response speed:', 'ভালো প্রতিক্রিয়ার গতি:')}</strong> {lt('Adequate processing time.', 'যথাযথ প্রসেসিং সময়।')}</div>
							{:else}
								<div class="insight insight-moderate"><strong>{lt('Slower responses:', 'তুলনামূলক ধীর:')}</strong> {lt('Practice can improve speed.', 'অনুশীলন গতি বাড়াতে সাহায্য করবে।')}</div>
							{/if}
							{#if metrics.d_prime >= 2.0}
								<div class="insight insight-good"><strong>{lt('High sensitivity:', 'উচ্চ সংবেদনশীলতা:')}</strong> {lt('Excellent discrimination between GO and NO-GO.', 'গো ও নো-গো উদ্দীপক চমৎকারভাবে আলাদা করতে পেরেছেন।')}</div>
							{:else if metrics.d_prime >= 1.0}
								<div class="insight insight-good"><strong>{lt('Good discrimination:', 'ভালো পার্থক্য:')}</strong> {lt('Solid signal detection ability.', 'নির্ভরযোগ্য সংকেত শনাক্তকরণ।')}</div>
							{/if}
						</div>
					</div>

					<div class="clinical-note">
						<h4>{lt('About the Go/No-Go Task', 'গো/নো-গো টাস্ক সম্পর্কে')}</h4>
						<p><strong>{lt('Response Inhibition:', 'প্রতিক্রিয়া নিয়ন্ত্রণ:')}</strong> {lt('A core executive function allowing you to control impulsive responses by suppressing prepotent (automatic) reactions.', 'একটি মূল নির্বাহী দক্ষতা যা স্বয়ংক্রিয় প্রতিক্রিয়া দমন করে আবেগ নিয়ন্ত্রণ করতে সাহায্য করে।')}</p>
						<p class="why-matters"><strong>{lt('For MS:', 'MS-এর ক্ষেত্রে:')}</strong> {lt('Sensitive to frontal lobe dysfunction and attention deficits. Regular practice strengthens inhibitory control circuits in the prefrontal cortex.', 'ফ্রন্টাল লোবের সমস্যা ও মনোযোগ ঘাটতিতে সংবেদনশীল। নিয়মিত অনুশীলন প্রিফ্রন্টাল কর্টেক্সের নিয়ন্ত্রণমূলক সার্কিটকে শক্তিশালী করে।')}</p>
						<p><strong>{lt('d-prime:', 'd-prime:')}</strong> {lt("Measures your ability to distinguish targets from non-targets without bias. Higher values mean better discrimination.", "পক্ষপাত ছাড়াই লক্ষ্যবস্তু ও অ-লক্ষ্যবস্তু আলাদা করার ক্ষমতা মাপে। বেশি মান মানে ভালো পার্থক্য করার সক্ষমতা।")}</p>
					</div>

					{#if metrics.difficulty_after !== undefined && metrics.difficulty_after !== difficulty}
						<div class="difficulty-info">
							<span>{lt('Difficulty:', 'কঠিনতা:')} <strong>{n(difficulty)}</strong> → <strong>{n(metrics.difficulty_after)}</strong></span>
						</div>
					{/if}

					{#if newBadges.length > 0}
						<BadgeNotification badges={newBadges} />
					{/if}

					<div class="button-group">
						<button class="start-button" on:click={returnToDashboard}>{lt('Return to Dashboard', 'ড্যাশবোর্ডে ফিরে যান')}</button>
						<button class="btn-secondary" on:click={() => goto('/training')}>{lt('Back to Training', 'ট্রেনিংয়ে ফিরে যান')}</button>
					</div>
				{/if}
			</div>
		{/if}

		{#if phase !== 'results' && phase !== 'intro'}
			<button class="help-fab" on:click={() => showHelp = true} aria-label={lt('Help', 'সহায়তা')}>?</button>
		{/if}
	</div>
</div>

{#if showHelp}
	<div class="modal-overlay" on:click={() => showHelp = false} role="presentation">
		<div class="modal-content" role="dialog" tabindex="-1"
			on:click|stopPropagation
			on:keydown={(e) => e.key === 'Escape' && (showHelp = false)}>
			<button class="close-btn" on:click={() => showHelp = false}>×</button>
			<h2>{lt('Go/No-Go Task — Help', 'গো/নো-গো টাস্ক — সহায়তা')}</h2>
			<div class="strategy">
				<h3>{lt('What is the Go/No-Go Task?', 'গো/নো-গো টাস্ক কী?')}</h3>
				<p>{lt('A widely-used test of response inhibition and impulse control. Measures your ability to suppress automatic responses when appropriate.', 'প্রতিক্রিয়া নিয়ন্ত্রণ ও আবেগ সংযমের বহুল ব্যবহৃত পরীক্ষা। উপযুক্ত সময়ে স্বয়ংক্রিয় প্রতিক্রিয়া দমনের সক্ষমতা মাপে।')}</p>
			</div>
			<div class="strategy">
				<h3>{lt('Why Used for MS?', 'MS-এ কেন ব্যবহার করা হয়?')}</h3>
				<p>{lt('Tests executive function and frontal lobe integrity. Measures sustained attention and vigilance. Sensitive to cognitive slowing and inhibition deficits common in MS.', 'নির্বাহী কার্যকারিতা ও ফ্রন্টাল লোবের সক্ষমতা যাচাই করে। টেকসই মনোযোগ ও সতর্কতা মাপে। MS-এ সাধারণ জ্ঞানগত ধীরগতি ও নিয়ন্ত্রণ ঘাটতির প্রতি সংবেদনশীল।')}</p>
			</div>
			<div class="strategy">
				<h3>{lt('Understanding Your Metrics', 'আপনার সূচকগুলো বোঝা')}</h3>
				<p><strong>{lt('Go Trial Speed:', 'গো ট্রায়ালের গতি:')}</strong> {lt('How quickly you respond to target stimuli.', 'লক্ষ্যবস্তু দেখলে কত দ্রুত সাড়া দেন।')}</p>
				<p><strong>{lt('No-Go Accuracy:', 'নো-গো নির্ভুলতা:')}</strong> {lt('Your ability to withhold inappropriate responses.', 'অপ্রয়োজনীয় সাড়া থামিয়ে রাখার সক্ষমতা।')}</p>
				<p><strong>{lt('Commission Errors:', 'ভুল চাপা:')}</strong> {lt('False alarms — pressing when you should not have.', 'ভুল সংকেত — যেখানে চাপা উচিত ছিল না, সেখানে চাপা।')}</p>
				<p><strong>{lt("d-prime:", "d-prime:")}</strong> {lt('Signal detection sensitivity. Higher is better.', 'সংকেত শনাক্তকরণ সংবেদনশীলতা। বেশি মান ভালো।')}</p>
			</div>
			<div class="strategy">
				<h3>{lt('Tips for Better Performance', 'ভালো পারফরম্যান্সের টিপস')}</h3>
				<p>{lt('Keep your finger resting on SPACEBAR. Focus on the center of the screen. Do not anticipate — wait to see the actual stimulus. Resist the urge to press on NO-GO trials. Stay alert throughout; consistency matters.', 'স্পেসবারে আঙুল রাখুন। স্ক্রিনের মাঝখানে ফোকাস করুন। আগাম অনুমান করবেন না। নো-গো ট্রায়ালে চাপার তাড়না সামলান। শুরু থেকে শেষ পর্যন্ত সতর্ক থাকুন।')}</p>
			</div>
			<div class="strategy">
				<h3>{lt('Real-World Relevance', 'বাস্তব জীবনের প্রাসঙ্গিকতা')}</h3>
				<p>{lt('Better impulse control relates to improved decision-making, safer driving, and better emotional regulation in daily life. Regular practice strengthens prefrontal inhibitory circuits.', 'ভালো আবেগ সংযম মানে উন্নত সিদ্ধান্ত নেওয়া, নিরাপদ চালানো, এবং দৈনন্দিন জীবনে ভালো আবেগ নিয়ন্ত্রণ। নিয়মিত অনুশীলন প্রিফ্রন্টাল নিয়ন্ত্রণমূলক সার্কিটকে শক্তিশালী করে।')}</p>
			</div>
		</div>
	</div>
{/if}

<style>
	/* ── Container ─────────────────────────────────────────── */
	.gonogo-container {
		min-height: 100vh;
		background: #C8DEFA;
		padding: 2rem 1rem;
	}

	.gonogo-inner {
		max-width: 960px;
		margin: 0 auto;
		position: relative;
	}

	/* ── Instructions card ─────────────────────────────────── */
	.instructions-card {
		background: white;
		border-radius: 16px;
		padding: 2.5rem;
		box-shadow: 0 4px 6px rgba(0,0,0,0.07), 0 1px 3px rgba(0,0,0,0.06);
		display: flex;
		flex-direction: column;
		gap: 1.8rem;
	}

	.header-content { text-align: center; }

	.title-row {
		display: flex; align-items: center; justify-content: center;
		gap: 1rem; flex-wrap: wrap; margin-bottom: 0.5rem;
	}

	.header-content h1 { font-size: 1.8rem; font-weight: 700; color: #1e293b; margin: 0; }

	.subtitle { color: #64748b; font-size: 1rem; margin: 0.4rem 0 0.8rem; }

	.classic-badge {
		display: inline-block;
		background: rgba(5, 150, 105, 0.1);
		color: #059669;
		border: 1px solid rgba(5, 150, 105, 0.3);
		border-radius: 20px;
		padding: 0.3rem 1rem;
		font-size: 0.82rem;
		font-weight: 700;
		letter-spacing: 0.03em;
	}

	/* ── Task concept ──────────────────────────────────────── */
	.task-concept {
		background: linear-gradient(135deg, #ecfdf5, #a7f3d0);
		border: 1px solid #6ee7b7;
		border-radius: 12px;
		padding: 1.5rem;
	}

	.task-concept h3 { font-size: 1rem; font-weight: 700; color: #065f46; margin: 0 0 0.5rem; }
	.task-concept > p { color: #047857; margin: 0 0 1.2rem; line-height: 1.6; }

	.stimulus-examples {
		display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;
		background: white; border-radius: 10px; padding: 1.2rem;
		box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 1.2rem;
	}

	.ex-card {
		display: flex; flex-direction: column; align-items: center; gap: 0.4rem;
		background: #f8fafc; border-radius: 10px; padding: 1rem 1.5rem;
		min-width: 150px; text-align: center; flex: 1;
	}

	.ex-go  { border: 2px solid #10b981; }
	.ex-nogo{ border: 2px solid #ef4444; }

	.ex-type { font-size: 0.78rem; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.05em; }

	.stimulus-demo {
		font-size: 3.5rem; font-weight: 900; line-height: 1;
		min-height: 60px; display: flex; align-items: center; justify-content: center;
	}
	.go-demo   { color: #10b981; }
	.nogo-demo { color: #ef4444; }

	.ex-action { font-size: 0.88rem; font-weight: 700; padding: 0.25rem 0.75rem; border-radius: 6px; }
	.go-action  { background: #d1fae5; color: #065f46; }
	.nogo-action{ background: #fee2e2; color: #991b1b; }

	.ex-note { font-size: 0.78rem; color: #64748b; }

	.key-rule-box {
		background: #fefce8; border: 1px solid #fde047; border-radius: 8px;
		padding: 0.75rem 1rem; font-size: 0.88rem; color: #854d0e; line-height: 1.5;
	}

	/* ── Rules grid ────────────────────────────────────────── */
	.rules-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }

	.rule-card {
		display: flex; align-items: flex-start; gap: 0.8rem;
		padding: 1rem; background: #f8fafc; border-radius: 10px;
		border-left: 4px solid #059669;
	}

	.rule-num {
		width: 28px; height: 28px; border-radius: 50%;
		background: #059669; color: white;
		display: flex; align-items: center; justify-content: center;
		font-size: 0.85rem; font-weight: 700; flex-shrink: 0;
	}

	.rule-text { display: flex; flex-direction: column; gap: 0.2rem; }
	.rule-text strong { font-size: 0.9rem; color: #1e293b; }
	.rule-text span   { font-size: 0.82rem; color: #64748b; line-height: 1.4; }

	/* ── Info grid ─────────────────────────────────────────── */
	.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }

	.info-section { background: #f8fafc; border-radius: 10px; padding: 1.2rem; }
	.info-section h4 { font-size: 0.9rem; font-weight: 700; color: #1e293b; margin: 0 0 0.8rem; }

	.tips-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 0.5rem; }
	.tips-list li { font-size: 0.85rem; color: #475569; line-height: 1.4; }

	.structure-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 0.5rem; }
	.structure-list li {
		display: flex; justify-content: space-between; align-items: center;
		font-size: 0.85rem; padding: 0.3rem 0; border-bottom: 1px solid #e2e8f0;
	}
	.structure-list li:last-child { border-bottom: none; }
	.struct-key { color: #64748b; }
	.struct-val { font-weight: 600; color: #1e293b; text-align: right; max-width: 60%; }

	/* ── Clinical info ─────────────────────────────────────── */
	.clinical-info {
		background: linear-gradient(135deg, #f0fdf4, #dcfce7);
		border: 1px solid #bbf7d0; border-radius: 12px; padding: 1.2rem;
	}
	.clinical-info h4 { font-size: 0.9rem; font-weight: 700; color: #166534; margin: 0 0 0.8rem; }
	.clinical-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
	.clinical-item { display: flex; flex-direction: column; gap: 0.2rem; }
	.clinical-item strong { font-size: 0.82rem; color: #166534; }
	.clinical-item span   { font-size: 0.8rem; color: #15803d; }

	/* ── Perf guide ────────────────────────────────────────── */
	.perf-guide { background: #f8fafc; border-radius: 12px; padding: 1.2rem; }
	.perf-guide h4 { font-size: 0.9rem; font-weight: 700; color: #1e293b; margin: 0 0 0.8rem; }
	.norm-bars { display: flex; flex-direction: column; gap: 0.4rem; }
	.norm-bar {
		display: flex; justify-content: space-between; align-items: center;
		padding: 0.5rem 0.9rem; border-radius: 6px; font-size: 0.85rem; font-weight: 600;
	}
	.norm-excellent { background: #dcfce7; color: #166534; }
	.norm-good      { background: #d1fae5; color: #065f46; }
	.norm-avg       { background: #fef9c3; color: #854d0e; }
	.norm-fair      { background: #ffedd5; color: #9a3412; }
	.norm-needs     { background: #fee2e2; color: #991b1b; }
	.norm-label { font-weight: 700; }
	.norm-val   { font-weight: 400; font-size: 0.82rem; }
	.norm-note  { font-size: 0.78rem; color: #94a3b8; font-style: italic; margin: 0.5rem 0 0; text-align: center; }

	/* ── Buttons ───────────────────────────────────────────── */
	.button-group {
		display: flex; justify-content: center; gap: 1rem;
		flex-wrap: wrap; padding-top: 0.5rem; align-items: center;
	}

	.start-button {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white; border: none; border-radius: 10px;
		padding: 0.85rem 2.5rem; font-size: 1rem; font-weight: 700;
		cursor: pointer; transition: transform 0.15s, box-shadow 0.15s;
		box-shadow: 0 4px 14px rgba(102,126,234,0.4);
	}
	.start-button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(102,126,234,0.5); }

	.btn-secondary {
		background: white; color: #667eea;
		border: 2px solid #667eea; border-radius: 10px;
		padding: 0.85rem 2rem; font-size: 1rem; font-weight: 600;
		cursor: pointer; transition: all 0.15s;
	}
	.btn-secondary:hover { background: rgba(102,126,234,0.08); }

	.help-link {
		background: none; border: none; color: #667eea;
		font-size: 0.9rem; cursor: pointer; text-decoration: underline;
		padding: 0.5rem; font-weight: 600; transition: color 0.15s;
	}
	.help-link:hover { color: #4f46e5; }

	/* ── Screen card ───────────────────────────────────────── */
	.screen-card {
		background: white; border-radius: 16px; padding: 2.5rem;
		box-shadow: 0 4px 6px rgba(0,0,0,0.07);
	}

	/* ── Quick instructions ────────────────────────────────── */
	.quick-instructions { text-align: center; }
	.quick-instructions h2 { font-size: 1.6rem; font-weight: 700; color: #1e293b; margin: 0 0 0.4rem; }
	.instr-subtitle { color: #64748b; margin: 0 0 1.5rem; }

	.key-reminder {
		background: #f0fdf4; border: 1px solid #a7f3d0;
		border-radius: 12px; padding: 1.2rem; margin-bottom: 1.5rem;
		display: flex; flex-direction: column; gap: 0.75rem;
	}

	.key-row { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; justify-content: center; }

	.key-box {
		padding: 0.5rem 1.2rem; border-radius: 8px;
		font-size: 0.95rem; font-weight: 800; letter-spacing: 0.04em;
	}
	.go-key   { background: #059669; color: white; }
	.nogo-key { background: #dc2626; color: white; }

	.key-for { font-size: 0.88rem; color: #64748b; }

	.inline-stim {
		font-size: 1.8rem; font-weight: 900;
		padding: 0.2rem 0.6rem; border-radius: 6px;
	}
	.go-stim  { color: #10b981; background: rgba(16,185,129,0.08); }
	.nogo-stim{ color: #ef4444; background: rgba(239,68,68,0.08); }

	.steps-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-bottom: 1.5rem; text-align: left; }

	.step-card {
		display: flex; flex-direction: column; gap: 0.3rem;
		background: #f8fafc; border-radius: 10px; padding: 1rem;
		border-left: 4px solid #059669;
	}

	.step-num {
		width: 26px; height: 26px; border-radius: 50%;
		background: #059669; color: white;
		display: flex; align-items: center; justify-content: center;
		font-size: 0.82rem; font-weight: 700; margin-bottom: 0.2rem;
	}

	.step-card strong { font-size: 0.9rem; color: #1e293b; }
	.step-card span   { font-size: 0.82rem; color: #64748b; }

	.remember-box {
		background: #fef9c3; border: 1px solid #fde047; border-radius: 10px;
		padding: 0.9rem 1.2rem; font-size: 0.9rem; color: #854d0e; line-height: 1.6;
		margin-bottom: 1.5rem; text-align: left;
	}

	.practice-note {
		background: #fef9c3; border: 1px solid #fde047;
		border-radius: 8px; padding: 0.6rem 1rem;
		color: #854d0e; font-size: 0.88rem; margin-bottom: 1rem;
	}

	/* ── Trial screen ──────────────────────────────────────── */
	.trial-screen { text-align: center; }

	.trial-header {
		display: flex; justify-content: center; align-items: center;
		gap: 0.75rem; flex-wrap: wrap; margin-bottom: 1.5rem;
	}

	.test-header {
		display: flex; justify-content: space-between; align-items: center;
		margin-bottom: 1.5rem; gap: 0.75rem; flex-wrap: wrap;
	}

	.test-badges { display: flex; gap: 0.5rem; flex: 1; align-items: center; flex-wrap: wrap; }

	.progress-track {
		flex: 1; height: 6px; background: #e2e8f0; border-radius: 3px;
		overflow: hidden; min-width: 80px;
	}
	.progress-fill { height: 100%; background: linear-gradient(90deg, #059669, #10b981); border-radius: 3px; transition: width 0.3s; }

	.help-btn-sm {
		width: 36px; height: 36px; border-radius: 50%;
		border: 2px solid #667eea; background: white; color: #667eea;
		font-size: 1.1rem; font-weight: 700; cursor: pointer;
		display: flex; align-items: center; justify-content: center; transition: all 0.2s;
	}
	.help-btn-sm:hover { background: #667eea; color: white; }

	.trial-badge {
		background: rgba(102,126,234,0.12); color: #667eea;
		padding: 0.35rem 0.9rem; border-radius: 20px; font-size: 0.85rem; font-weight: 700;
	}
	.remaining-badge {
		background: rgba(5,150,105,0.12); color: #047857;
		padding: 0.35rem 0.9rem; border-radius: 20px; font-size: 0.82rem; font-weight: 600;
	}

	.instr-mini { font-size: 0.82rem; color: #94a3b8; }

	/* ── Stimulus area ─────────────────────────────────────── */
	.stimulus-area {
		min-height: 300px;
		display: flex; align-items: center; justify-content: center;
		margin: 1.5rem auto 2rem;
	}

	.stimulus-large {
		font-size: 8rem; font-weight: 900;
		line-height: 1; transition: color 0.1s;
	}
	.stim-go   { color: #10b981; }
	.stim-nogo { color: #ef4444; }

	.stimulus-xlarge {
		font-size: 10rem; font-weight: 900; line-height: 1;
		color: #059669;
	}

	.fixation { font-size: 5rem; color: #cbd5e1; font-weight: 300; }

	.reminder-text { font-size: 0.9rem; color: #94a3b8; margin: 0; }

	/* ── Feedback ──────────────────────────────────────────── */
	.feedback-box { margin-top: 1.5rem; padding: 1rem 1.5rem; border-radius: 10px; font-weight: 600; font-size: 0.95rem; line-height: 1.5; }
	.feedback-success { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
	.feedback-error   { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }

	/* ── Complete screen ───────────────────────────────────── */
	.complete-screen { display: flex; flex-direction: column; gap: 1.5rem; }

	.perf-banner {
		text-align: center; padding: 1.5rem;
		background: linear-gradient(135deg, #ecfdf5, #a7f3d0);
		border: 2px solid #6ee7b7; border-radius: 14px;
	}
	.perf-level    { font-size: 1.8rem; font-weight: 800; color: #065f46; }
	.perf-subtitle { font-size: 0.95rem; color: #64748b; margin-top: 0.3rem; }

	.metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; }
	.metric-card {
		background: #f8fafc; border: 1px solid #e2e8f0;
		border-radius: 12px; padding: 1.2rem; text-align: center;
	}
	.metric-card.highlight {
		background: linear-gradient(135deg, #059669, #047857);
		border-color: transparent; color: white;
	}
	.metric-value { font-size: 1.8rem; font-weight: 800; color: #1e293b; margin-bottom: 0.2rem; }
	.metric-card.highlight .metric-value,
	.metric-card.highlight .metric-label,
	.metric-card.highlight .metric-sub { color: white; }
	.metric-label { font-size: 0.82rem; font-weight: 600; color: #64748b; }
	.metric-sub   { font-size: 0.78rem; color: #94a3b8; margin-top: 0.2rem; }

	/* ── Breakdown ─────────────────────────────────────────── */
	.breakdown { background: #f8fafc; border-radius: 12px; padding: 1.2rem; }
	.breakdown h3 { font-size: 0.95rem; font-weight: 700; color: #1e293b; margin: 0 0 1rem; }

	.condition-row {
		padding: 0.9rem; border-radius: 10px; margin-bottom: 0.75rem;
		border: 1px solid #e2e8f0;
	}
	.condition-row:last-child { margin-bottom: 0; }
	.condition-go  { background: #f0fdf4; border-color: #a7f3d0; }
	.condition-nogo{ background: #fff1f2; border-color: #fda4af; }

	.cond-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; }
	.cond-header strong { font-size: 0.88rem; color: #1e293b; }
	.cond-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }

	.cond-stats { display: flex; flex-wrap: wrap; gap: 0.5rem 1.5rem; font-size: 0.85rem; color: #475569; }
	.cond-note { font-style: italic; color: #94a3b8; }
	.err-val   { color: #dc2626; }

	/* ── Interpretation ────────────────────────────────────── */
	.interpretation-section { background: #f8fafc; border-radius: 12px; padding: 1.2rem; }
	.interpretation-section h3 { font-size: 0.95rem; font-weight: 700; color: #1e293b; margin: 0 0 0.6rem; }
	.feedback-text { font-size: 0.9rem; color: #475569; margin: 0 0 1rem; line-height: 1.6; }

	.insights { display: flex; flex-direction: column; gap: 0.5rem; }
	.insight { padding: 0.6rem 0.9rem; border-radius: 8px; font-size: 0.85rem; line-height: 1.5; }
	.insight-good     { background: #dcfce7; color: #166534; }
	.insight-moderate { background: #fef9c3; color: #854d0e; }
	.insight-high     { background: #fee2e2; color: #991b1b; }

	/* ── Clinical note ─────────────────────────────────────── */
	.clinical-note {
		background: linear-gradient(135deg, #f0fdf4, #dcfce7);
		border: 1px solid #bbf7d0; border-radius: 12px; padding: 1.2rem;
	}
	.clinical-note h4 { font-size: 0.9rem; font-weight: 700; color: #166534; margin: 0 0 0.5rem; }
	.clinical-note p { font-size: 0.9rem; color: #15803d; line-height: 1.6; margin: 0 0 0.5rem; }
	.clinical-note p:last-child { margin: 0; }
	.why-matters { font-style: italic; }

	/* ── Difficulty info ───────────────────────────────────── */
	.difficulty-info {
		background: #ecfdf5; border: 1px solid #6ee7b7; border-radius: 10px;
		padding: 0.75rem 1.2rem; font-size: 0.88rem; font-weight: 600; color: #065f46;
	}

	/* ── FAB help button ───────────────────────────────────── */
	.help-fab {
		position: fixed; bottom: 2rem; right: 2rem;
		width: 48px; height: 48px; border-radius: 50%;
		background: white; border: 2px solid #667eea; color: #667eea;
		font-size: 1.3rem; font-weight: 700; cursor: pointer;
		box-shadow: 0 4px 12px rgba(0,0,0,0.15);
		display: flex; align-items: center; justify-content: center;
		transition: all 0.2s;
	}
	.help-fab:hover { background: #667eea; color: white; }

	/* ── Modal ─────────────────────────────────────────────── */
	.modal-overlay {
		position: fixed; inset: 0; background: rgba(0,0,0,0.55);
		display: flex; align-items: center; justify-content: center;
		z-index: 1000; padding: 1rem;
	}
	.modal-content {
		background: white; border-radius: 16px; padding: 2rem;
		max-width: 560px; width: 100%; max-height: 80vh; overflow-y: auto;
		position: relative; box-shadow: 0 20px 60px rgba(0,0,0,0.3);
	}
	.close-btn {
		position: absolute; top: 1rem; right: 1rem;
		width: 36px; height: 36px; border: none; background: #f1f5f9;
		color: #475569; font-size: 1.4rem; border-radius: 50%; cursor: pointer;
		display: flex; align-items: center; justify-content: center;
	}
	.close-btn:hover { background: #e2e8f0; }
	.modal-content h2 {
		font-size: 1.2rem; font-weight: 700; color: #1e293b;
		margin: 0 0 1.2rem; padding-right: 2.5rem;
	}
	.strategy {
		padding: 0.9rem 1rem; background: #f8fafc;
		border-radius: 8px; border-left: 4px solid #059669; margin-bottom: 0.75rem;
	}
	.strategy h3 { font-size: 0.88rem; font-weight: 700; color: #1e293b; margin: 0 0 0.3rem; }
	.strategy p  { font-size: 0.84rem; color: #64748b; margin: 0 0 0.3rem; line-height: 1.5; }
	.strategy p:last-child { margin: 0; }

	/* ── Responsive ────────────────────────────────────────── */
	@media (max-width: 640px) {
		.instructions-card { padding: 1.5rem; gap: 1.2rem; }
		.rules-grid         { grid-template-columns: 1fr; }
		.info-grid          { grid-template-columns: 1fr; }
		.clinical-grid      { grid-template-columns: 1fr; }
		.metrics-grid       { grid-template-columns: repeat(2, 1fr); }
		.steps-grid         { grid-template-columns: 1fr; }
		.header-content h1  { font-size: 1.4rem; }
		.screen-card        { padding: 1.25rem; }
		.stimulus-large     { font-size: 5rem; }
		.stimulus-xlarge    { font-size: 7rem; }
		.stimulus-examples  { gap: 0.5rem; }
		.ex-card            { min-width: 110px; padding: 0.75rem; }
		.key-row            { flex-direction: column; gap: 0.4rem; }
	}
</style>

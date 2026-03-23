<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import { formatNumber, formatPercent, locale, localeText, translateText } from '$lib/i18n';
	import { getGoNoGoStimulus, getGoNoGoStimulusPair } from '$lib/i18n/task-ui.js';
	import { user } from '$lib/stores';
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

	// Practice state
	let practiceTrials = [];
	let currentPractice = 0;
	let practiceFeedback = null;

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
		practiceTrials = buildPracticeTrials();

		currentPractice = 0;
		practiceFeedback = null;
		phase = 'practice';
		showNextPracticeTrial();
	}

	function showNextPracticeTrial() {
		// Clear any existing timers
		clearTimeout(stimulusTimeout);
		clearTimeout(interStimulusTimeout);
		
		if (currentPractice >= practiceTrials.length) {
			// Practice complete
			setTimeout(() => {
				startTest();
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

		setTimeout(() => {
			practiceFeedback = null;
			currentPractice++;
			showNextPracticeTrial();
		}, 2000);
	}

	function startTest() {
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

<svelte:window on:keydown={handleKeyPress} />

<div class="gonogo-container" data-localize-skip>
	{#if loading}
		<div class="loading">
			<div class="spinner"></div>
			<p>{lt('Loading task...', 'টাস্ক লোড হচ্ছে...')}</p>
		</div>
	{:else if phase === 'intro'}
		<!-- Introduction Screen -->
		<div class="instructions">
			<div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap;">
				<h1>{lt('Go/No-Go Task', 'গো/নো-গো টাস্ক')}</h1>
				<DifficultyBadge {difficulty} domain="Attention" />
			</div>
			<div class="classic-badge">{lt('Response Inhibition & Impulse Control Assessment', 'প্রতিক্রিয়া নিয়ন্ত্রণ ও আবেগ সংযম মূল্যায়ন')}</div>
			
			<div class="instruction-card">
				<div class="task-header">
					<h2>{lt('Your Mission: Respond Fast, But Not Always!', 'আপনার লক্ষ্য: দ্রুত সাড়া দিন, তবে সবসময় নয়')}</h2>
				</div>
				
				<p class="importance">
					{@html lt(
						'This task measures your ability to <strong>control impulses</strong>, a critical executive function. You need to respond quickly to targets while <strong>withholding responses</strong> to non-targets.',
						'এই টাস্কটি আপনার <strong>আবেগ সংযম</strong> ও প্রতিক্রিয়া নিয়ন্ত্রণের ক্ষমতা মাপে, যা নির্বাহী কার্যকারিতার একটি গুরুত্বপূর্ণ অংশ। এখানে লক্ষ্যবস্তু দেখলে দ্রুত সাড়া দিতে হবে, আর অ-লক্ষ্যবস্তু দেখলে <strong>প্রতিক্রিয়া থামিয়ে রাখতে</strong> হবে।'
					)}
				</p>
				
				<!-- Visual Examples -->
				<div class="stimulus-examples">
					<div class="example-card go-card">
						<div class="example-label">{lt('GO Trial (75%)', 'গো ট্রায়াল (৭৫%)')}</div>
						<div class="stimulus-display go-stimulus">{goDisplayStimulus}</div>
						<div class="example-action">{lt('PRESS SPACEBAR', 'স্পেসবার চাপুন')}</div>
						<div class="example-note">{lt('Respond as quickly as possible.', 'যত দ্রুত সম্ভব সাড়া দিন।')}</div>
					</div>
					
					<div class="example-card nogo-card">
						<div class="example-label">{lt('NO-GO Trial (25%)', 'নো-গো ট্রায়াল (২৫%)')}</div>
						<div class="stimulus-display nogo-stimulus">{nogoDisplayStimulus}</div>
						<div class="example-action">{lt("DON'T PRESS", 'চাপবেন না')}</div>
						<div class="example-note">{lt('Resist the urge to respond.', 'সাড়া দেওয়ার তাড়না থামিয়ে রাখুন।')}</div>
					</div>
				</div>
				
				<div class="rule-box">
					<strong>{lt('The Challenge:', 'মূল চ্যালেঞ্জ:')}</strong>
					{lt(
						'Most trials require a response, so a response habit quickly builds up. When the NO-GO stimulus appears, you must inhibit that automatic response. This directly tests impulse control.',
						'বেশিরভাগ ট্রায়ালে সাড়া দিতে হয়, তাই খুব দ্রুত একটি অভ্যাস তৈরি হয়। কিন্তু নো-গো উদ্দীপক দেখলে সেই স্বয়ংক্রিয় প্রতিক্রিয়াটিই থামিয়ে রাখতে হবে। এখানেই আপনার আবেগ সংযম ও প্রতিক্রিয়া নিয়ন্ত্রণ যাচাই হয়।'
					)}
				</div>
				
				<!-- Two Column Layout -->
				<div class="info-grid">
					<div class="info-section">
						<h3>{lt("What You'll Do", 'আপনি কী করবেন')}</h3>
						<div class="steps-list">
							<div class="step-item">
								<span class="step-num">1</span>
								<div class="step-text">
									<strong>{lt('Watch the screen', 'স্ক্রিনে নজর রাখুন')}</strong>
									<span>{lt('Stimuli appear briefly.', 'উদ্দীপক খুব অল্প সময়ের জন্য দেখা যাবে।')}</span>
								</div>
							</div>
							<div class="step-item">
								<span class="step-num">2</span>
								<div class="step-text">
									<strong>{lt('Identify quickly', 'দ্রুত চিহ্নিত করুন')}</strong>
									<span>{lt('Decide whether it is GO or NO-GO.', 'এটি গো নাকি নো-গো তা ঠিক করুন।')}</span>
								</div>
							</div>
							<div class="step-item">
								<span class="step-num">3</span>
								<div class="step-text">
									<strong>{lt('Respond or withhold', 'সাড়া দিন বা থামিয়ে রাখুন')}</strong>
									<span>{lt("Press or don't press.", 'চাপুন বা চাপা থেকে বিরত থাকুন।')}</span>
								</div>
							</div>
						</div>
					</div>
					
					<div class="info-section">
						<h3>{lt('What It Measures', 'এটি কী মাপে')}</h3>
						<div class="measures-list">
							<div class="measure-item">{lt('Response Speed:', 'প্রতিক্রিয়ার গতি:')} {lt('Go trial reaction time', 'গো ট্রায়ালে প্রতিক্রিয়ার সময়')}</div>
							<div class="measure-item">{lt('Impulse Control:', 'আবেগ সংযম:')} {lt('No-Go accuracy', 'নো-গো নির্ভুলতা')}</div>
							<div class="measure-item">{lt('Sustained Attention:', 'টেকসই মনোযোগ:')} {lt('Consistency', 'ধারাবাহিকতা')}</div>
							<div class="measure-item">{lt('Executive Function:', 'নির্বাহী কার্যকারিতা:')} {lt('Inhibition ability', 'প্রতিক্রিয়া থামিয়ে রাখার দক্ষতা')}</div>
						</div>
					</div>
				</div>
				
				<!-- Clinical Context -->
				<div class="clinical-info">
					<h3>{lt('Clinical Significance', 'ক্লিনিক্যাল গুরুত্ব')}</h3>
					<div class="clinical-grid">
						<div class="clinical-item">
							<strong>{lt('Standard Test:', 'স্ট্যান্ডার্ড মূল্যায়ন:')}</strong> {lt('Used in ADHD, frontal lobe, and MS assessment', 'ADHD, ফ্রন্টাল লোব এবং MS মূল্যায়নে ব্যবহৃত হয়')}
						</div>
						<div class="clinical-item">
							<strong>{lt('Brain Regions:', 'মস্তিষ্কের অংশ:')}</strong> {lt('Tests prefrontal cortex function', 'প্রিফ্রন্টাল কর্টেক্সের কার্যকারিতা মাপে')}
						</div>
						<div class="clinical-item">
							<strong>{lt('MS Relevance:', 'MS-এ প্রাসঙ্গিকতা:')}</strong> {lt('Sensitive to attention deficits and executive dysfunction', 'মনোযোগ ঘাটতি ও নির্বাহী কার্যকারিতার সমস্যার প্রতি সংবেদনশীল')}
						</div>
						<div class="clinical-item">
							<strong>{lt('Training Benefits:', 'অনুশীলনের উপকার:')}</strong> {lt('Improves real-world impulse control', 'বাস্তব জীবনের আবেগ সংযম উন্নত করতে সহায়তা করে')}
						</div>
					</div>
				</div>
			</div>
			
			<div class="button-group">
				<button class="start-button" on:click={startInstructions}>
					{lt('Start Task', 'টাস্ক শুরু করুন')}
				</button>
				<button class="btn-secondary" on:click={() => goto('/dashboard')}>
					{lt('Back to Dashboard', 'ড্যাশবোর্ডে ফিরে যান')}
				</button>
			</div>
		</div>

	{:else if phase === 'instructions'}
		<!-- Quick Instructions -->
		<div class="quick-instructions">
			<h2>{lt('Quick Instructions', 'দ্রুত নির্দেশনা')}</h2>

			<div class="key-reminder">
				<div class="key-icon">{lt('SPACEBAR', 'স্পেসবার')}</div>
				<p>{@html lt(`Press <strong>SPACEBAR</strong> when you see: <span class="inline-stimulus">${goDisplayStimulus}</span>`, `এটি দেখলে <strong>স্পেসবার</strong> চাপুন: <span class="inline-stimulus">${goDisplayStimulus}</span>`)}</p>
				<p>{@html lt(`<strong>DON'T PRESS</strong> when you see: <span class="inline-stimulus nogo">${nogoDisplayStimulus}</span>`, `এটি দেখলে <strong>চাপবেন না</strong>: <span class="inline-stimulus nogo">${nogoDisplayStimulus}</span>`)}</p>
			</div>

			<div class="instructions-flow">
				<div class="flow-step">
					<div class="flow-number">1</div>
					<div class="flow-content">
						<p class="flow-title">{lt('Stimulus Appears', 'উদ্দীপক দেখা যায়')}</p>
						<p class="flow-desc">{lt('A symbol flashes on screen briefly.', 'একটি চিহ্ন অল্প সময়ের জন্য স্ক্রিনে দেখা যায়।')}</p>
					</div>
				</div>

				<div class="flow-arrow">→</div>

				<div class="flow-step">
					<div class="flow-number">2</div>
					<div class="flow-content">
						<p class="flow-title">{lt('Identify It', 'চিনে নিন')}</p>
						<p class="flow-desc">{lt('Is it GO or NO-GO?', 'এটি গো নাকি নো-গো?')}</p>
					</div>
				</div>

				<div class="flow-arrow">→</div>

				<div class="flow-step">
					<div class="flow-number">3</div>
					<div class="flow-content">
						<p class="flow-title">{lt('Respond or Wait', 'সাড়া দিন বা অপেক্ষা করুন')}</p>
						<p class="flow-desc">{lt('Press SPACEBAR or withhold.', 'স্পেসবার চাপুন অথবা সাড়া থামিয়ে রাখুন।')}</p>
					</div>
				</div>
			</div>

			<div class="tips-box">
				<h3>{lt('Success Tips', 'সফল হওয়ার টিপস')}</h3>
				<ul>
					<li>{@html lt('<strong>Stay focused</strong> - Stimuli appear quickly', '<strong>মনোযোগ ধরে রাখুন</strong> - উদ্দীপক দ্রুত দেখা যায়')}</li>
					<li>{@html lt('<strong>Be ready</strong> - Most trials are GO trials', '<strong>প্রস্তুত থাকুন</strong> - বেশিরভাগ ট্রায়ালই গো ট্রায়াল')}</li>
					<li>{@html lt('<strong>Control impulses</strong> - Resist pressing on NO-GO trials', '<strong>আবেগ সংযম রাখুন</strong> - নো-গো ট্রায়ালে চাপা থেকে বিরত থাকুন')}</li>
					<li>{@html lt('<strong>Speed matters</strong> - Respond quickly to GO trials', '<strong>গতি গুরুত্বপূর্ণ</strong> - গো ট্রায়ালে দ্রুত সাড়া দিন')}</li>
				</ul>
			</div>

			<div class="practice-prompt">
				<p>{lt("Let's practice with 6 trials to get comfortable...", 'স্বচ্ছন্দ হতে আগে ৬টি অনুশীলনী ট্রায়াল করা যাক...')}</p>
				<button class="start-button" on:click={startPractice}>
					{lt('Start Practice', 'অনুশীলন শুরু করুন')}
				</button>
			</div>
		</div>

	{:else if phase === 'practice'}
		<!-- Practice Trials -->
		<div class="trial-screen">
			<div class="trial-header">
				<h2>{practiceTrialLabel(currentPractice + 1, practiceTrials.length)}</h2>
				<p class="instruction-reminder">{lt(`Press SPACEBAR for GO (${goDisplayStimulus}), withhold for NO-GO (${nogoDisplayStimulus})`, `গো (${goDisplayStimulus}) দেখলে স্পেসবার চাপুন, নো-গো (${nogoDisplayStimulus}) দেখলে সাড়া থামিয়ে রাখুন`)}</p>
			</div>

			<!-- Stimulus Display -->
			<div class="stimulus-area">
				{#if showStimulus}
					<div class="stimulus-large" class:go={practiceTrials[currentPractice].trial_type === 'go'} class:nogo={practiceTrials[currentPractice].trial_type === 'nogo'}>
						{displayStimulus(practiceTrials[currentPractice])}
					</div>
				{:else}
					<div class="fixation">+</div>
				{/if}
			</div>

			<!-- Feedback -->
			{#if practiceFeedback}
				<div class="feedback-box {practiceFeedback.type}">
					<p>{practiceFeedback.message}</p>
				</div>
			{/if}
		</div>

	{:else if phase === 'test'}
		<!-- Test Trials -->
		<div class="trial-screen">
			<!-- Progress Header -->
			<div class="progress-header">
				<div class="progress-top">
					<h2>{trialLabel(currentTrial + 1, sessionData.trials.length)}</h2>
					<div class="progress-badges">
						<span class="badge-remaining">{remainingTrialsLabel(trialsRemaining)}</span>
					</div>
				</div>
				<div class="progress-bar-container">
					<div class="progress-bar-fill" style="width: {progress}%"></div>
				</div>
			</div>

			<!-- Stimulus Display -->
			<div class="stimulus-area">
				{#if showStimulus && currentTrial < sessionData.trials.length}
					<div class="stimulus-xlarge">
						{displayStimulus(sessionData.trials[currentTrial])}
					</div>
				{:else}
					<div class="fixation">+</div>
				{/if}
			</div>

			<div class="reminder-text">
				{lt(`Press SPACEBAR for ${goDisplayStimulus} | Don't press for ${nogoDisplayStimulus}`, `${goDisplayStimulus} দেখলে স্পেসবার চাপুন | ${nogoDisplayStimulus} দেখলে চাপবেন না`)}
			</div>
		</div>

	{:else if phase === 'results'}
		<!-- Results Screen -->
		<div class="results-container">
			<div class="results-header">
				<h2>{lt('Go/No-Go Task Complete!', 'গো/নো-গো টাস্ক সম্পন্ন হয়েছে')}</h2>
				<div class="performance-badge {performanceBadgeColor}">
					{performanceLevelLabel(metrics.performance_level)}
				</div>
			</div>

			<!-- Key Metrics Grid -->
			<div class="metrics-grid">
				<!-- Overall Accuracy -->
				<div class="metric-card accuracy-card">
					<div class="metric-label">{lt('Overall Accuracy', 'সামগ্রিক নির্ভুলতা')}</div>
					<div class="metric-value">{pct(metrics.overall_accuracy || 0)}</div>
					<div class="metric-detail">{n(metrics.total_correct || 0)}/{n(metrics.total_trials || 0)} {lt('correct', 'সঠিক')}</div>
				</div>

				<!-- Go Trial Speed -->
				<div class="metric-card speed-card">
					<div class="metric-label">{lt('Go Trial Speed', 'গো ট্রায়ালের গতি')}</div>
					<div class="metric-value">{msText(metrics.go_mean_rt || 0)}</div>
					<div class="metric-detail">{lt('Processing speed', 'প্রসেসিং গতি')}</div>
				</div>

				<!-- No-Go Accuracy -->
				<div class="metric-card inhibition-card">
					<div class="metric-label">{lt('Inhibition Control', 'প্রতিক্রিয়া নিয়ন্ত্রণ')}</div>
					<div class="metric-value">{pct(metrics.nogo_accuracy || 0)}</div>
					<div class="metric-detail">{lt('No-Go accuracy', 'নো-গো নির্ভুলতা')}</div>
				</div>

				<!-- d-prime -->
				<div class="metric-card dprime-card">
					<div class="metric-label">{lt('d-prime (Sensitivity)', 'ডি-প্রাইম (সংবেদনশীলতা)')}</div>
					<div class="metric-value">{n((metrics.d_prime || 0).toFixed(2), { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
					<div class="metric-detail">{lt('Signal detection', 'সংকেত শনাক্তকরণ')}</div>
				</div>
			</div>

			<!-- Trial Type Breakdown -->
			<div class="breakdown-section">
				<h3>{lt('Performance by Trial Type', 'ট্রায়ালভেদে পারফরম্যান্স')}</h3>
				<div class="breakdown-grid">
					<!-- Go Trials -->
					<div class="breakdown-card go-card">
						<p class="breakdown-title">{lt(`GO Trials (${n(sessionData.go_trials)} trials)`, `গো ট্রায়াল (${n(sessionData.go_trials)}টি)` )}</p>
						<p class="breakdown-stat">{lt('Hits:', 'সঠিক সাড়া:')} <span>{n(metrics.go_hits || 0)}</span></p>
						<p class="breakdown-stat">{lt('Misses:', 'মিস:')} <span>{n(metrics.go_misses || 0)}</span></p>
						<p class="breakdown-stat">{lt('Accuracy:', 'নির্ভুলতা:')} <span>{pct(metrics.go_accuracy || 0)}</span></p>
						<p class="breakdown-stat">{lt('Mean RT:', 'গড় প্রতিক্রিয়ার সময়:')} <span>{msText(metrics.go_mean_rt || 0)}</span></p>
						<p class="breakdown-note">{lt('Tests processing speed and attention', 'প্রসেসিং গতি ও মনোযোগ মাপে')}</p>
					</div>

					<!-- No-Go Trials -->
					<div class="breakdown-card nogo-card">
						<p class="breakdown-title">{lt(`NO-GO Trials (${n(sessionData.nogo_trials)} trials)`, `নো-গো ট্রায়াল (${n(sessionData.nogo_trials)}টি)` )}</p>
						<p class="breakdown-stat">{lt('Correct Withholds:', 'সফল বিরত থাকা:')} <span>{n(metrics.nogo_correct || 0)}</span></p>
						<p class="breakdown-stat">{lt('Commission Errors:', 'ভুল চাপা:')} <span class="error-count">{n(metrics.nogo_commission_errors || 0)}</span></p>
						<p class="breakdown-stat">{lt('Accuracy:', 'নির্ভুলতা:')} <span>{pct(metrics.nogo_accuracy || 0)}</span></p>
						<p class="breakdown-stat">{lt('Hit Rate:', 'হিট রেট:')} <span>{pct(metrics.hit_rate || 0)}</span></p>
						<p class="breakdown-note success">{lt('Tests impulse control and inhibition', 'আবেগ সংযম ও প্রতিক্রিয়া নিয়ন্ত্রণ মাপে')}</p>
					</div>
				</div>
			</div>

			<!-- Interpretation -->
			<div class="interpretation-section">
				<h3>{lt('What This Means', 'এর অর্থ কী')}</h3>
				<p class="feedback-text">{resultsSummaryText()}</p>
				
				<div class="insights-list">
					{#if metrics.nogo_accuracy >= 90}
						<p class="insight success">
							{@html lt('<strong>Excellent inhibitory control:</strong> You successfully withheld responses on NO-GO trials.', '<strong>চমৎকার প্রতিক্রিয়া নিয়ন্ত্রণ:</strong> আপনি নো-গো ট্রায়ালে সাড়া থামিয়ে রাখতে পেরেছেন।')}
						</p>
					{:else if metrics.nogo_accuracy >= 75}
						<p class="insight good">
							{@html lt('<strong>Good impulse control:</strong> Managing inhibition effectively.', '<strong>ভালো আবেগ সংযম:</strong> আপনি বেশ কার্যকরভাবে প্রতিক্রিয়া নিয়ন্ত্রণ করেছেন।')}
						</p>
					{:else if metrics.nogo_accuracy >= 60}
						<p class="insight moderate">
							{@html lt('<strong>Moderate inhibition:</strong> There is room to improve impulse control.', '<strong>মাঝারি নিয়ন্ত্রণ:</strong> আবেগ সংযমে আরও উন্নতির সুযোগ আছে।')}
						</p>
					{:else}
						<p class="insight high">
							{@html lt('<strong>Challenging inhibition:</strong> Practice will strengthen impulse control.', '<strong>চ্যালেঞ্জিং নিয়ন্ত্রণ:</strong> অনুশীলন এই দক্ষতাকে আরও শক্তিশালী করবে।')}
						</p>
					{/if}

					{#if metrics.go_mean_rt < 400}
						<p class="insight success">
							{@html lt('<strong>Fast processing speed:</strong> Quick reactions to GO trials.', '<strong>দ্রুত প্রসেসিং গতি:</strong> গো ট্রায়ালে আপনার প্রতিক্রিয়া দ্রুত ছিল।')}
						</p>
					{:else if metrics.go_mean_rt < 600}
						<p class="insight good">
							{@html lt('<strong>Good response speed:</strong> Adequate processing time.', '<strong>ভালো প্রতিক্রিয়ার গতি:</strong> আপনার প্রসেসিং সময় যথাযথ ছিল।')}
						</p>
					{:else}
						<p class="insight moderate">
							{@html lt('<strong>Slower responses:</strong> Practice can improve speed.', '<strong>তুলনামূলক ধীর প্রতিক্রিয়া:</strong> অনুশীলন গতি বাড়াতে সাহায্য করবে।')}
						</p>
					{/if}

					{#if metrics.d_prime >= 2.0}
						<p class="insight success">
							{@html lt('<strong>High sensitivity:</strong> Excellent discrimination between GO and NO-GO.', '<strong>উচ্চ সংবেদনশীলতা:</strong> আপনি গো ও নো-গো উদ্দীপক খুব ভালোভাবে আলাদা করতে পেরেছেন।')}
						</p>
					{:else if metrics.d_prime >= 1.0}
						<p class="insight good">
							{@html lt('<strong>Good discrimination:</strong> Solid signal detection ability.', '<strong>ভালো পার্থক্য নির্ণয়:</strong> আপনার সংকেত শনাক্তকরণ ক্ষমতা নির্ভরযোগ্য ছিল।')}
						</p>
					{/if}
				</div>
			</div>

			<!-- Clinical Context -->
			<div class="clinical-context">
				<h3>{lt('About the Go/No-Go Task', 'গো/নো-গো টাস্ক সম্পর্কে')}</h3>
				<div class="clinical-content">
					<p>
						{@html lt('<strong>Response Inhibition</strong> is a core executive function that allows you to control impulsive responses. This task measures your ability to withhold prepotent (automatic) responses.', '<strong>প্রতিক্রিয়া নিয়ন্ত্রণ</strong> হলো একটি মৌলিক নির্বাহী দক্ষতা, যা আপনাকে হঠাৎ করে সাড়া দেওয়ার প্রবণতা নিয়ন্ত্রণ করতে সাহায্য করে। এই টাস্কটি আপনার স্বয়ংক্রিয় প্রতিক্রিয়া থামিয়ে রাখার ক্ষমতা মাপে।')}
					</p>
					<p>
						{@html lt('<strong>For MS:</strong> Go/No-Go tasks are sensitive to frontal lobe dysfunction and attention deficits. Regular practice can strengthen inhibitory control circuits in the prefrontal cortex.', '<strong>MS-এর ক্ষেত্রে:</strong> গো/নো-গো টাস্ক ফ্রন্টাল লোবের সমস্যা ও মনোযোগ ঘাটতি শনাক্ত করতে সংবেদনশীল। নিয়মিত অনুশীলন প্রিফ্রন্টাল কর্টেক্সের নিয়ন্ত্রণমূলক সার্কিটকে শক্তিশালী করতে সাহায্য করতে পারে।')}
					</p>
					<p>
						{@html lt('<strong>Real-World Impact:</strong> Better impulse control relates to improved decision-making, safer driving, and better emotional regulation in daily life.', '<strong>বাস্তব জীবনের প্রভাব:</strong> ভালো আবেগ সংযম মানে উন্নত সিদ্ধান্ত নেওয়া, নিরাপদ চালনা, এবং দৈনন্দিন জীবনে ভালো আবেগ নিয়ন্ত্রণ।')}
					</p>
					<p>
						{@html lt('<strong>d-prime (d\')</strong> measures how accurately you distinguish between targets and non-targets without being overly biased toward pressing or withholding. Higher values indicate better discrimination.', '<strong>d-prime (d\')</strong> দেখায় আপনি লক্ষ্যবস্তু ও অ-লক্ষ্যবস্তুকে কতটা নির্ভুলভাবে আলাদা করতে পারছেন, অতিরিক্ত চাপা বা না-চাপার পক্ষপাত ছাড়াই। মান যত বেশি, পার্থক্য ধরার ক্ষমতা তত ভালো।')}
					</p>
				</div>
			</div>

			<!-- Difficulty Adaptation -->
			{#if metrics.difficulty_after !== difficulty}
				<div class="difficulty-change">
					<p>
						<strong>{difficultyChangeText(difficulty, metrics.difficulty_after)}</strong>
					</p>
				</div>
			{/if}

			<!-- New Badges -->
			{#if newBadges.length > 0}
				<div class="badges-section">
					<h3>{lt('New Badges Earned!', 'নতুন ব্যাজ অর্জিত হয়েছে')}</h3>
					<BadgeNotification badges={newBadges} />
				</div>
			{/if}

			<!-- Actions -->
			<div class="results-actions">
				<button on:click={returnToDashboard} class="return-button">
					{lt('Return to Dashboard', 'ড্যাশবোর্ডে ফিরে যান')}
				</button>
			</div>
		</div>
	{/if}

	<!-- Help Button -->
	{#if phase !== 'results'}
		<button on:click={() => showHelp = true} class="help-button" aria-label={lt('Help', 'সহায়তা')}>
			?
		</button>
	{/if}

	<!-- Help Modal -->
	{#if showHelp}
		<div class="modal-overlay" on:click|self={() => showHelp = false} on:keydown={(e) => e.key === 'Escape' && (showHelp = false)} role="dialog" aria-modal="true" aria-labelledby="gonogo-help-title" tabindex="0">
			<div class="modal-content" role="document">
				<h2 class="modal-title" id="gonogo-help-title">{lt('Go/No-Go Task Help', 'গো/নো-গো টাস্ক সহায়তা')}</h2>

				<div class="help-sections">
					<div class="help-section">
						<h3>{lt('What is the Go/No-Go Task?', 'গো/নো-গো টাস্ক কী?')}</h3>
						<p>
							{lt('A widely-used test of response inhibition and impulse control. It measures your ability to suppress automatic responses when appropriate.', 'এটি প্রতিক্রিয়া নিয়ন্ত্রণ ও আবেগ সংযমের বহুল ব্যবহৃত একটি পরীক্ষা। উপযুক্ত সময়ে স্বয়ংক্রিয় প্রতিক্রিয়া থামিয়ে রাখার ক্ষমতা এতে মূল্যায়ন করা হয়।')}
						</p>
					</div>

					<div class="help-section">
						<h3>{lt('Why Is It Used in MS?', 'MS-এ এটি কেন ব্যবহার করা হয়?')}</h3>
						<ul>
							<li>{lt('Tests executive function and frontal lobe integrity', 'নির্বাহী কার্যকারিতা ও ফ্রন্টাল লোবের সক্ষমতা যাচাই করে')}</li>
							<li>{lt('Measures sustained attention and vigilance', 'টেকসই মনোযোগ ও সতর্কতা মাপে')}</li>
							<li>{lt('Sensitive to cognitive slowing and inhibition deficits', 'জ্ঞানগত ধীরগতি ও নিয়ন্ত্রণ ঘাটতির প্রতি সংবেদনশীল')}</li>
							<li>{lt('Predicts real-world functional outcomes', 'বাস্তব জীবনের কার্যকারিতার ইঙ্গিত দেয়')}</li>
						</ul>
					</div>

					<div class="help-section">
						<h3>{lt('Understanding Your Metrics', 'আপনার সূচকগুলো বুঝে নিন')}</h3>
						<div class="metrics-explain">
							<p>{@html lt('<strong>Go Trial Speed:</strong> How quickly you respond to target stimuli.', '<strong>গো ট্রায়ালের গতি:</strong> লক্ষ্যবস্তু দেখলে আপনি কত দ্রুত সাড়া দেন।')}</p>
							<p>{@html lt('<strong>No-Go Accuracy:</strong> Your ability to withhold inappropriate responses.', '<strong>নো-গো নির্ভুলতা:</strong> অপ্রয়োজনীয় সাড়া থামিয়ে রাখার সক্ষমতা।')}</p>
							<p>{@html lt('<strong>Commission Errors:</strong> False alarms when you press by mistake.', '<strong>ভুল চাপা:</strong> যেখানে চাপা উচিত ছিল না, সেখানে ভুল করে চাপা।')}</p>
							<p>{@html lt('<strong>d-prime:</strong> Signal detection sensitivity, where higher is better.', '<strong>d-prime:</strong> সংকেত আলাদা করে ধরার সংবেদনশীলতা, যেখানে বেশি মান ভালো।')}</p>
						</div>
					</div>

					<div class="help-section">
						<h3>{lt('Tips for Success', 'ভালো করার টিপস')}</h3>
						<ul>
							<li>{lt('Keep your finger ready over SPACEBAR', 'স্পেসবারের ওপর আঙুল প্রস্তুত রাখুন')}</li>
							<li>{lt('Focus on the center of the screen', 'স্ক্রিনের মাঝখানে মনোযোগ রাখুন')}</li>
							<li>{lt("Don't anticipate, wait to see the stimulus", 'আগাম অনুমান না করে উদ্দীপক দেখার জন্য অপেক্ষা করুন')}</li>
							<li>{lt('Resist the urge to press on NO-GO trials', 'নো-গো ট্রায়ালে চাপার তাড়না সামলান')}</li>
							<li>{lt('Stay alert throughout, consistency matters', 'শুরু থেকে শেষ পর্যন্ত সতর্ক থাকুন, ধারাবাহিকতা গুরুত্বপূর্ণ')}</li>
						</ul>
					</div>
				</div>

				<button on:click={() => showHelp = false} class="modal-close-btn">
					{lt('Close', 'বন্ধ করুন')}
				</button>
			</div>
		</div>
	{/if}
</div>

<style>
	.gonogo-container {
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(147, 51, 234, 0.05) 100%);
		min-height: 100vh;
		padding: 2rem 1rem;
	}

	.loading {
		background: white;
		padding: 3rem;
		border-radius: 16px;
		text-align: center;
		max-width: 400px;
		margin: 0 auto;
		box-shadow: 0 8px 32px rgba(0,0,0,0.1);
	}

	.spinner {
		width: 50px;
		height: 50px;
		border: 4px solid #f3f3f3;
		border-top: 4px solid #3b82f6;
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin: 0 auto 1rem auto;
	}

	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	.instructions {
		background: white;
		border-radius: 16px;
		padding: 2.5rem 2rem;
		max-width: 1000px;
		margin: 0 auto;
		box-shadow: 0 8px 32px rgba(0,0,0,0.15);
	}

	.instructions h1 {
		text-align: center;
		color: #3b82f6;
		font-size: 2.5rem;
		margin-bottom: 1rem;
	}

	.classic-badge {
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(147, 51, 234, 0.15));
		color: #3b82f6;
		padding: 0.75rem 1.5rem;
		border-radius: 25px;
		text-align: center;
		font-weight: 600;
		margin: 0 auto 2rem auto;
		max-width: fit-content;
		display: block;
	}

	.instruction-card {
		background: #f8f9fa;
		padding: 2rem;
		border-radius: 12px;
		margin-bottom: 2rem;
	}

	.task-header h2 {
		color: #2c3e50;
		margin-bottom: 1rem;
		font-size: 1.8rem;
		text-align: center;
	}

	.importance {
		font-size: 1.1rem;
		line-height: 1.7;
		color: #555;
		margin-bottom: 2rem;
		text-align: center;
	}

	.importance :global(strong) {
		color: #3b82f6;
	}

	/* Stimulus Examples */
	.stimulus-examples {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: 1.5rem;
		margin: 2rem 0;
	}

	.example-card {
		background: white;
		padding: 1.5rem;
		border-radius: 12px;
		text-align: center;
		box-shadow: 0 4px 12px rgba(0,0,0,0.08);
	}

	.example-card.go-card {
		border: 3px solid #10b981;
	}

	.example-card.nogo-card {
		border: 3px solid #ef4444;
	}

	.example-label {
		font-size: 0.75rem;
		font-weight: bold;
		color: #666;
		margin-bottom: 1rem;
		text-transform: uppercase;
	}

	.stimulus-display {
		font-size: 4rem;
		font-weight: bold;
		margin: 1rem 0;
		min-height: 100px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.stimulus-display.go-stimulus {
		color: #10b981;
	}

	.stimulus-display.nogo-stimulus {
		color: #ef4444;
	}

	.example-action {
		font-size: 1.1rem;
		font-weight: 700;
		margin: 1rem 0;
	}

	.go-card .example-action {
		color: #10b981;
	}

	.nogo-card .example-action {
		color: #ef4444;
	}

	.example-note {
		font-size: 0.9rem;
		color: #666;
		font-style: italic;
	}

	/* Rule Box */
	.rule-box {
		background: #fef3c7;
		border-left: 4px solid #f59e0b;
		padding: 1.25rem;
		border-radius: 8px;
		margin: 2rem 0;
		color: #92400e;
		line-height: 1.6;
	}

	.rule-box strong {
		font-size: 1.1rem;
		display: block;
		margin-bottom: 0.5rem;
	}

	/* Info Grid */
	.info-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: 1.5rem;
		margin: 2rem 0;
	}

	.info-section {
		background: white;
		padding: 1.5rem;
		border-radius: 12px;
		border: 2px solid #e5e7eb;
	}

	.info-section h3 {
		color: #2c3e50;
		font-size: 1.2rem;
		margin-bottom: 1rem;
	}

	/* Steps List */
	.steps-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.step-item {
		display: flex;
		align-items: center;
		gap: 1rem;
		background: #f8f9fa;
		padding: 1rem;
		border-radius: 8px;
	}

	.step-num {
		width: 40px;
		height: 40px;
		background: linear-gradient(135deg, #3b82f6 0%, #9333ea 100%);
		color: white;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.3rem;
		font-weight: bold;
		flex-shrink: 0;
	}

	.step-text {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.step-text strong {
		font-size: 1rem;
		color: #2c3e50;
	}

	.step-text span {
		font-size: 0.875rem;
		color: #666;
	}

	/* Measures List */
	.measures-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.measure-item {
		background: #eff6ff;
		padding: 0.75rem 1rem;
		border-radius: 8px;
		color: #1e40af;
		font-size: 0.95rem;
		line-height: 1.5;
	}

	/* Clinical Info */
	.clinical-info {
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.08), rgba(147, 51, 234, 0.08));
		padding: 1.5rem;
		border-radius: 12px;
		margin-top: 1.5rem;
	}

	.clinical-info h3 {
		color: #3b82f6;
		margin-bottom: 1rem;
		font-size: 1.1rem;
	}

	.clinical-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		gap: 0.75rem;
	}

	.clinical-item {
		background: white;
		padding: 0.875rem;
		border-radius: 8px;
		font-size: 0.9rem;
		line-height: 1.5;
		color: #555;
	}

	.clinical-item strong {
		color: #3b82f6;
		display: block;
		margin-bottom: 0.25rem;
	}

	/* Buttons */
	.button-group {
		display: flex;
		gap: 1rem;
		justify-content: center;
		margin-top: 2rem;
		flex-wrap: wrap;
	}

	.start-button {
		background: linear-gradient(135deg, #3b82f6 0%, #9333ea 100%);
		color: white;
		border: none;
		padding: 1.25rem 3rem;
		font-size: 1.2rem;
		font-weight: bold;
		border-radius: 12px;
		cursor: pointer;
		transition: all 0.3s;
		box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
	}

	.start-button:hover {
		transform: translateY(-3px);
		box-shadow: 0 6px 25px rgba(59, 130, 246, 0.6);
	}

	.btn-secondary {
		background: #f3f4f6;
		color: #4b5563;
		border: none;
		padding: 1.25rem 2.5rem;
		font-size: 1.1rem;
		font-weight: 600;
		border-radius: 12px;
		cursor: pointer;
		transition: all 0.3s;
	}

	.btn-secondary:hover {
		background: #e5e7eb;
		transform: translateY(-2px);
	}

	/* Quick Instructions */
	.quick-instructions {
		background: white;
		border-radius: 16px;
		padding: 2.5rem 2rem;
		max-width: 800px;
		margin: 0 auto;
		box-shadow: 0 8px 32px rgba(0,0,0,0.15);
	}

	.quick-instructions h2 {
		text-align: center;
		color: #3b82f6;
		font-size: 2rem;
		margin-bottom: 2rem;
	}

	.key-reminder {
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(147, 51, 234, 0.1));
		padding: 1.5rem;
		border-radius: 12px;
		text-align: center;
		margin-bottom: 2rem;
	}

	.key-icon {
		display: inline-block;
		background: #3b82f6;
		color: white;
		padding: 0.75rem 1.5rem;
		border-radius: 8px;
		font-size: 1.2rem;
		font-weight: bold;
		margin-bottom: 1rem;
	}

	.key-reminder p {
		font-size: 1.1rem;
		color: #2c3e50;
		margin: 0.5rem 0;
	}

	.inline-stimulus {
		display: inline-block;
		font-size: 1.5rem;
		font-weight: bold;
		color: #10b981;
		padding: 0.25rem 0.75rem;
		background: rgba(16, 185, 129, 0.1);
		border-radius: 6px;
	}

	.inline-stimulus.nogo {
		color: #ef4444;
		background: rgba(239, 68, 68, 0.1);
	}

	.instructions-flow {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		margin: 2rem 0;
		flex-wrap: wrap;
	}

	.flow-step {
		background: #f8f9fa;
		padding: 1.5rem;
		border-radius: 12px;
		min-width: 180px;
		text-align: center;
	}

	.flow-number {
		width: 50px;
		height: 50px;
		background: linear-gradient(135deg, #3b82f6 0%, #9333ea 100%);
		color: white;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.8rem;
		font-weight: bold;
		margin: 0 auto 1rem auto;
	}

	.flow-title {
		font-size: 1.1rem;
		font-weight: 700;
		color: #2c3e50;
		margin-bottom: 0.5rem;
	}

	.flow-desc {
		font-size: 0.9rem;
		color: #666;
		margin: 0;
	}

	.flow-arrow {
		font-size: 2rem;
		color: #3b82f6;
		font-weight: bold;
	}

	.tips-box {
		background: #ecfdf5;
		border-left: 4px solid #10b981;
		padding: 1.5rem;
		border-radius: 12px;
		margin: 2rem 0;
	}

	.tips-box h3 {
		color: #065f46;
		margin-bottom: 1rem;
	}

	.tips-box ul {
		list-style: none;
		padding: 0;
		margin: 0;
	}

	.tips-box li {
		padding: 0.5rem 0;
		color: #047857;
		font-size: 0.95rem;
	}

	.tips-box li :global(strong) {
		color: #064e3b;
	}

	.practice-prompt {
		text-align: center;
		margin-top: 2rem;
	}

	.practice-prompt p {
		font-size: 1.1rem;
		color: #555;
		margin-bottom: 1.5rem;
	}

	/* Trial Screen */
	.trial-screen {
		background: white;
		border-radius: 16px;
		padding: 2rem;
		max-width: 900px;
		margin: 0 auto;
		box-shadow: 0 8px 32px rgba(0,0,0,0.15);
	}

	.trial-header {
		text-align: center;
		margin-bottom: 2rem;
	}

	.trial-header h2 {
		color: #2c3e50;
		font-size: 1.5rem;
		margin-bottom: 0.5rem;
	}

	.instruction-reminder {
		color: #666;
		font-size: 0.95rem;
		margin-top: 0.5rem;
	}

	.progress-header {
		text-align: center;
		margin-bottom: 2rem;
	}

	.progress-top {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		flex-wrap: wrap;
		gap: 1rem;
	}

	.progress-top h2 {
		color: #2c3e50;
		font-size: 1.5rem;
		margin: 0;
	}

	.progress-badges {
		display: flex;
		gap: 0.75rem;
	}

	.badge-remaining {
		background: #dbeafe;
		color: #1e40af;
		padding: 0.5rem 1rem;
		border-radius: 20px;
		font-size: 0.875rem;
		font-weight: 600;
	}

	.progress-bar-container {
		width: 100%;
		height: 10px;
		background: #e5e7eb;
		border-radius: 10px;
		overflow: hidden;
	}

	.progress-bar-fill {
		height: 100%;
		background: linear-gradient(90deg, #3b82f6 0%, #9333ea 100%);
		transition: width 0.3s ease;
	}

	.stimulus-area {
		min-height: 350px;
		display: flex;
		align-items: center;
		justify-content: center;
		margin: 2rem 0;
	}

	.stimulus-large {
		font-size: 8rem;
		font-weight: 900;
		text-shadow: 3px 3px 6px rgba(0,0,0,0.1);
	}

	.stimulus-large.go {
		color: #10b981;
	}

	.stimulus-large.nogo {
		color: #ef4444;
	}

	.stimulus-xlarge {
		font-size: 10rem;
		font-weight: 900;
		text-shadow: 3px 3px 6px rgba(0,0,0,0.1);
		color: #3b82f6;
	}

	.fixation {
		font-size: 5rem;
		color: #d1d5db;
		font-weight: bold;
	}

	.reminder-text {
		text-align: center;
		color: #666;
		font-size: 1rem;
		margin-top: 2rem;
	}

	.feedback-box {
		margin-top: 2rem;
		padding: 1.5rem;
		border-radius: 12px;
		text-align: center;
		font-size: 1.1rem;
		font-weight: 600;
		animation: fadeIn 0.3s ease;
	}

	.feedback-box.success {
		background: #d1fae5;
		color: #065f46;
		border: 2px solid #10b981;
	}

	.feedback-box.error {
		background: #fee2e2;
		color: #991b1b;
		border: 2px solid #ef4444;
	}

	@keyframes fadeIn {
		from {
			opacity: 0;
			transform: translateY(-10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	/* Results Page */
	.results-container {
		background: white;
		border-radius: 16px;
		padding: 2.5rem 2rem;
		max-width: 1100px;
		margin: 0 auto;
		box-shadow: 0 8px 32px rgba(0,0,0,0.15);
	}

	.results-header {
		text-align: center;
		margin-bottom: 2.5rem;
	}

	.results-header h2 {
		font-size: 2.5rem;
		font-weight: bold;
		color: #2c3e50;
		margin-bottom: 1.5rem;
	}

	.performance-badge {
		display: inline-block;
		padding: 1rem 2rem;
		border-radius: 50px;
		font-size: 1.3rem;
		font-weight: bold;
		color: white;
		box-shadow: 0 4px 15px rgba(0,0,0,0.2);
	}

	.performance-badge.from-green-500 {
		background: linear-gradient(135deg, #10b981 0%, #059669 100%);
	}

	.performance-badge.from-blue-500 {
		background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
	}

	.performance-badge.from-yellow-500 {
		background: linear-gradient(135deg, #eab308 0%, #f59e0b 100%);
	}

	.performance-badge.from-gray-500 {
		background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
	}

	/* Metrics Grid */
	.metrics-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		gap: 1.25rem;
		margin-bottom: 2.5rem;
	}

	.metric-card {
		padding: 1.5rem;
		border-radius: 12px;
		border: 2px solid;
		box-shadow: 0 4px 12px rgba(0,0,0,0.08);
	}

	.accuracy-card {
		background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.1));
		border-color: #10b981;
	}

	.speed-card {
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(37, 99, 235, 0.1));
		border-color: #3b82f6;
	}

	.inhibition-card {
		background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(220, 38, 38, 0.1));
		border-color: #ef4444;
	}

	.dprime-card {
		background: linear-gradient(135deg, rgba(147, 51, 234, 0.1), rgba(126, 34, 206, 0.1));
		border-color: #9333ea;
	}

	.metric-label {
		font-size: 0.9rem;
		font-weight: 600;
		color: #555;
		margin-bottom: 0.5rem;
	}

	.metric-value {
		font-size: 2.5rem;
		font-weight: bold;
		color: #2c3e50;
		margin-bottom: 0.25rem;
	}

	.metric-detail {
		font-size: 0.8rem;
		color: #666;
	}

	/* Breakdown Section */
	.breakdown-section {
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.08), rgba(147, 51, 234, 0.08));
		padding: 1.5rem;
		border-radius: 12px;
		margin-bottom: 2rem;
	}

	.breakdown-section h3 {
		font-size: 1.2rem;
		font-weight: 700;
		color: #2c3e50;
		margin-bottom: 1.25rem;
	}

	.breakdown-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: 1rem;
	}

	.breakdown-card {
		background: white;
		padding: 1.25rem;
		border-radius: 10px;
		border: 2px solid;
	}

	.breakdown-card.go-card {
		border-color: #10b981;
	}

	.breakdown-card.nogo-card {
		border-color: #ef4444;
	}

	.breakdown-title {
		font-weight: 700;
		color: #2c3e50;
		margin-bottom: 0.75rem;
		font-size: 1rem;
	}

	.breakdown-stat {
		font-size: 0.9rem;
		color: #555;
		margin-bottom: 0.5rem;
	}

	.breakdown-stat span {
		font-weight: 700;
	}

	.breakdown-stat .error-count {
		color: #ef4444;
	}

	.breakdown-note {
		font-size: 0.85rem;
		color: #666;
		margin-top: 0.75rem;
		font-style: italic;
	}

	.breakdown-note.success {
		color: #059669;
		font-weight: 600;
	}

	/* Interpretation Section */
	.interpretation-section {
		background: white;
		border: 2px solid #3b82f6;
		border-radius: 12px;
		padding: 1.5rem;
		margin-bottom: 2rem;
	}

	.interpretation-section h3 {
		font-size: 1.2rem;
		font-weight: 700;
		color: #2c3e50;
		margin-bottom: 1rem;
	}

	.feedback-text {
		color: #555;
		line-height: 1.6;
		margin-bottom: 1.5rem;
		font-size: 1.05rem;
	}

	.insights-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.insight {
		font-size: 0.95rem;
		line-height: 1.5;
	}

	.insight.success {
		color: #059669;
	}

	.insight.good {
		color: #2563eb;
	}

	.insight.moderate {
		color: #ca8a04;
	}

	.insight.high {
		color: #ea580c;
	}

	/* Clinical Context */
	.clinical-context {
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.08), rgba(147, 51, 234, 0.08));
		padding: 1.5rem;
		border-radius: 12px;
		margin-bottom: 2rem;
	}

	.clinical-context h3 {
		font-size: 1.1rem;
		font-weight: 700;
		color: #2c3e50;
		margin-bottom: 1rem;
	}

	.clinical-content {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.clinical-content p {
		font-size: 0.9rem;
		color: #555;
		line-height: 1.6;
	}

	/* Difficulty Change */
	.difficulty-change {
		background: #dbeafe;
		border-left: 4px solid #3b82f6;
		padding: 1rem;
		border-radius: 8px;
		margin-bottom: 1.5rem;
	}

	.difficulty-change p {
		font-size: 0.9rem;
		color: #1e3a8a;
		margin: 0;
	}

	/* Badges Section */
	.badges-section {
		margin-bottom: 2rem;
	}

	.badges-section h3 {
		font-size: 1.2rem;
		font-weight: 700;
		color: #2c3e50;
		margin-bottom: 1rem;
	}

	/* Results Actions */
	.results-actions {
		display: flex;
		justify-content: center;
		gap: 1rem;
		margin-top: 2rem;
	}

	.return-button {
		background: linear-gradient(135deg, #3b82f6 0%, #9333ea 100%);
		color: white;
		padding: 1.25rem 3rem;
		font-size: 1.1rem;
		font-weight: 700;
		border: none;
		border-radius: 12px;
		cursor: pointer;
		transition: all 0.3s;
		box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
	}

	.return-button:hover {
		transform: translateY(-3px);
		box-shadow: 0 6px 25px rgba(59, 130, 246, 0.6);
	}

	/* Help Button */
	.help-button {
		position: fixed;
		bottom: 2rem;
		right: 2rem;
		width: 56px;
		height: 56px;
		background: #3b82f6;
		color: white;
		border: none;
		border-radius: 50%;
		font-size: 2rem;
		cursor: pointer;
		box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
		transition: all 0.3s;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.help-button:hover {
		background: #2563eb;
		transform: scale(1.1);
	}

	/* Modal */
	.modal-overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 1rem;
		z-index: 1000;
	}

	.modal-content {
		background: white;
		border-radius: 16px;
		padding: 2rem;
		max-width: 650px;
		max-height: 90vh;
		overflow-y: auto;
		box-shadow: 0 10px 40px rgba(0,0,0,0.3);
	}

	.modal-title {
		font-size: 1.8rem;
		font-weight: bold;
		color: #2c3e50;
		margin-bottom: 1.5rem;
	}

	.help-sections {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.help-section h3 {
		font-size: 1.1rem;
		font-weight: 700;
		color: #2c3e50;
		margin-bottom: 0.75rem;
	}

	.help-section p {
		color: #555;
		line-height: 1.6;
	}

	.help-section ul {
		list-style: disc;
		padding-left: 1.5rem;
		color: #555;
	}

	.help-section li {
		margin-bottom: 0.5rem;
		line-height: 1.5;
	}

	.metrics-explain {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.metrics-explain p {
		font-size: 0.95rem;
	}

	.modal-close-btn {
		margin-top: 1.5rem;
		width: 100%;
		padding: 1rem 1.5rem;
		background: #3b82f6;
		color: white;
		border: none;
		border-radius: 12px;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s;
	}

	.modal-close-btn:hover {
		background: #2563eb;
	}

	/* Responsive */
	@media (max-width: 768px) {
		.instructions {
			padding: 1.5rem 1rem;
		}

		.instructions h1 {
			font-size: 2rem;
		}

		.stimulus-examples {
			grid-template-columns: 1fr;
		}

		.info-grid {
			grid-template-columns: 1fr;
		}

		.stimulus-large {
			font-size: 5rem;
		}

		.stimulus-xlarge {
			font-size: 6rem;
		}

		.flow-arrow {
			transform: rotate(90deg);
		}
	}
</style>

<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import { formatNumber, formatPercent, locale, localeText, translateText } from '$lib/i18n';
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
		return direction === 'right' ? lt('RIGHT →', 'ডানে →') : lt('LEFT ←', 'বামে ←');
	}

	function shortDirection(direction) {
		return direction === 'right' ? lt('right', 'ডান') : lt('left', 'বাম');
	}

	function practiceTrialLabel(current, total) {
		return $locale === 'bn'
			? `অনুশীলনী ট্রায়াল ${n(current)} / ${n(total)}`
			: `Practice Trial ${current} of ${total}`;
	}

	function trialLabel(current, total) {
		return $locale === 'bn' ? `ট্রায়াল ${n(current)} / ${n(total)}` : `Trial ${current} of ${total}`;
	}

	function remainingTrialsLabel(count) {
		return $locale === 'bn' ? `${n(count)}টি বাকি` : `${count} remaining`;
	}

	function localizedHint(trial) {
		return localeText(trial?.hint, $locale);
	}

	function practiceSuccessMessage(rt, trial) {
		return $locale === 'bn'
			? `✓ সঠিক! প্রতিক্রিয়ার সময়: ${msText(rt)}। ${localizedHint(trial)}`
			: `✓ Correct! Response time: ${rt}ms. ${localizedHint(trial)}`;
	}

	function practiceErrorMessage(trial) {
		return $locale === 'bn'
			? `✗ ভুল দিক! মাঝের তীরটি ছিল ${directionLabel(trial.direction)}। ${localizedHint(trial)}`
			: `✗ Wrong direction! CENTER arrow pointed ${directionLabel(trial.direction)}. ${localizedHint(trial)}`;
	}

	function practiceCompleteMessage() {
		return lt("✓ Practice complete! You're ready for the real test.", '✓ অনুশীলন শেষ! এখন আপনি আসল পরীক্ষার জন্য প্রস্তুত।');
	}

	function slowResponseMessage() {
		return lt('⏱️ Too slow! Try to respond faster.', '⏱️ একটু দেরি হয়ে গেছে! আরও দ্রুত সাড়া দেওয়ার চেষ্টা করুন।');
	}

	function resultsSummaryText() {
		const conflictEffect = Number(metrics?.conflict_effect || 0);
		const accuracy = Number(metrics?.overall_accuracy || 0);

		if ($locale === 'bn') {
			if (accuracy >= 90 && conflictEffect < 100) {
				return 'চমৎকার নির্বাচিত মনোযোগ! বিভ্রান্তিকর সংকেত থাকলেও আপনি খুব ভালোভাবে সঠিক দিক চিনতে পেরেছেন।';
			}

			if (accuracy >= 80 && conflictEffect < 150) {
				return 'ভালো পারফরম্যান্স। আপনার মনোযোগ ও দ্বন্দ্ব সামলানোর ক্ষমতা স্থিতিশীল আছে, তবে আরও অনুশীলনে গতি ও নিয়ন্ত্রণ দুটোই উন্নত হবে।';
			}

			return 'এই টাস্কটি বিভ্রান্তির মাঝেও সঠিক সংকেতে মনোযোগ ধরে রাখার ক্ষমতা মাপে। নিয়মিত অনুশীলনে প্রাসঙ্গিক তথ্য বেছে নেওয়ার দক্ষতা আরও ভালো হবে।';
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
				hint: {
					en: 'Easy! All arrows point right →',
					bn: 'সহজ! সব তীর ডানে →'
				}
			},
			{
				trial_type: 'congruent',
				direction: 'left',
				flanker_count: 2,
				hint: {
					en: 'All arrows point left ←',
					bn: 'সব তীর বামে ←'
				}
			},
			{
				trial_type: 'incongruent',
				direction: 'right',
				flanker_count: 2,
				hint: {
					en: 'Focus on the CENTER arrow only! →',
					bn: 'শুধু মাঝের তীরটিতে মন দিন! →'
				}
			},
			{
				trial_type: 'congruent',
				direction: 'right',
				flanker_count: 2,
				hint: {
					en: 'Congruent again - quick!',
					bn: 'আবার সঙ্গত ট্রায়াল - দ্রুত সাড়া দিন!'
				}
			},
			{
				trial_type: 'incongruent',
				direction: 'left',
				flanker_count: 2,
				hint: {
					en: 'Ignore distractors - CENTER is ←',
					bn: 'বিভ্রান্তি উপেক্ষা করুন - মাঝের তীরটি ←'
				}
			},
			{
				trial_type: 'congruent',
				direction: 'left',
				flanker_count: 2,
				hint: {
					en: 'All matching, press quickly',
					bn: 'সব একই দিকে - দ্রুত চাপুন'
				}
			},
			{
				trial_type: 'incongruent',
				direction: 'right',
				flanker_count: 2,
				hint: {
					en: 'Hard! Flankers mislead you',
					bn: 'কঠিন! পাশের তীরগুলো আপনাকে বিভ্রান্ত করবে'
				}
			},
			{
				trial_type: 'incongruent',
				direction: 'left',
				flanker_count: 2,
				hint: {
					en: 'Last one - stay focused on CENTER',
					bn: 'শেষটি - মাঝের তীরেই মন রাখুন'
				}
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
						? `সেশন লোড করা যায়নি: ${response.status} - ${errorText}`
						: `Failed to load session: ${response.status} - ${errorText}`
				);
			}

			const data = await response.json();
			sessionData = data.session_data;
			difficulty = data.difficulty;
			loading = false;
		} catch (error) {
			console.error('Error loading session:', error);
			alert(
				lt(
					'Failed to load training session. Please ensure the backend server is running and you have completed baseline assessment.',
					'ট্রেনিং সেশন লোড করা যায়নি। অনুগ্রহ করে নিশ্চিত করুন ব্যাকএন্ড সার্ভার চালু আছে এবং আপনি বেসলাইন মূল্যায়ন সম্পন্ন করেছেন।'
				)
			);
			loading = false;
		}
	}

	function startInstructions() {
		phase = 'instructions';
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
		
		if (currentPractice >= practiceTrials.length) {
			// Practice complete
			practiceFeedback = {
				type: 'success',
				message: practiceCompleteMessage()
			};
			setTimeout(() => {
				startTest();
			}, 2000);
			return;
		}

		responded = false;
		showStimulus = true;
		startTime = Date.now();

		// Auto-advance after 3 seconds for practice
		stimulusTimeout = setTimeout(() => {
			if (!responded) {
				practiceFeedback = {
					type: 'warning',
					message: slowResponseMessage()
				};
				showStimulus = false;
				setTimeout(() => {
					practiceFeedback = null;
					currentPractice++;
					showNextPracticeTrial();
				}, 1500);
			}
		}, 3000);
	}

	function handlePracticeResponse(direction) {
		if (!showStimulus || responded) return;
		
		clearTimeout(stimulusTimeout);
		responded = true;
		
		const trial = practiceTrials[currentPractice];
		const rt = Date.now() - startTime;
		const correct = direction === trial.direction;

		if (correct) {
			practiceFeedback = {
				type: 'success',
				message: practiceSuccessMessage(rt, trial)
			};
		} else {
			practiceFeedback = {
				type: 'error',
				message: practiceErrorMessage(trial)
			};
		}

		showStimulus = false;

		// Auto-advance after showing feedback
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

		// Inter-stimulus interval (fixation cross)
		interStimulusTimeout = setTimeout(() => {
			showStimulus = true;
			startTime = Date.now();

			// Hide stimulus after presentation time
			stimulusTimeout = setTimeout(() => {
				showStimulus = false;

				// If no response yet, wait a bit then record as missed
				if (!responded) {
					trialTimeout = setTimeout(() => {
						recordResponse(null, 0);
					}, 300);
				}
			}, sessionData.presentation_time_ms);
		}, 500); // 500ms fixation
	}

	function recordResponse(direction, reactionTime) {
		if (responded) return;
		
		// Clear all timers immediately
		clearTimeout(stimulusTimeout);
		clearTimeout(interStimulusTimeout);
		clearTimeout(trialTimeout);
		
		responded = true;

		const trial = sessionData.trials[currentTrial];

		responses.push({
			trial_number: trial.trial_number,
			trial_type: trial.trial_type,
			target_direction: trial.target_direction,
			responded_direction: direction,
			reaction_time_ms: reactionTime,
			correct: direction === trial.target_direction
		});

		currentTrial++;
		showStimulus = false;

		// Brief pause before next trial
		interStimulusTimeout = setTimeout(() => {
			showNextTrial();
		}, 300);
	}

	function handleKeyPress(event) {
		if (phase === 'practice' && showStimulus && !responded) {
			if (event.key === 'ArrowLeft' || event.key === 'a' || event.key === 'A') {
				event.preventDefault();
				handlePracticeResponse('left');
			} else if (event.key === 'ArrowRight' || event.key === 'd' || event.key === 'D') {
				event.preventDefault();
				handlePracticeResponse('right');
			}
		} else if (phase === 'test' && showStimulus && !responded) {
			const rt = Date.now() - startTime;
			if (event.key === 'ArrowLeft' || event.key === 'a' || event.key === 'A') {
				event.preventDefault();
				recordResponse('left', rt);
			} else if (event.key === 'ArrowRight' || event.key === 'd' || event.key === 'D') {
				event.preventDefault();
				recordResponse('right', rt);
			}
		}
	}

	async function completeSession() {
		try {
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

	// Performance badge color
	$: performanceBadgeColor = metrics?.performance_level === 'Excellent' ? 'from-green-500'
		: metrics?.performance_level === 'Good' ? 'from-blue-500'
		: metrics?.performance_level === 'Fair' ? 'from-yellow-500'
		: 'from-gray-500';

	// Generate arrow display for trials
	function generateArrowDisplay(trial) {
		const leftArrow = '←';
		const rightArrow = '→';
		const centerArrow = trial.target_direction === 'right' ? rightArrow : leftArrow;
		const flankerArrow = trial.trial_type === 'congruent' 
			? centerArrow 
			: (centerArrow === rightArrow ? leftArrow : rightArrow);
		
		const flankers = Array(trial.flanker_count).fill(flankerArrow).join(' ');
		return `${flankers} ${centerArrow} ${flankers}`;
	}

	function generatePracticeArrowDisplay(trial) {
		const leftArrow = '←';
		const rightArrow = '→';
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
	{#if loading}
		<div class="loading">
			<div class="spinner"></div>
			<p>{lt('Loading task...', 'টাস্ক লোড হচ্ছে...')}</p>
		</div>
	{:else if phase === 'intro'}
		<!-- Introduction Screen -->
		<div class="instructions">
			<div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap;">
				<h1>⚡ {lt('Flanker Task', 'ফ্ল্যাঙ্কার টাস্ক')}</h1>
				<DifficultyBadge {difficulty} domain="Attention" />
			</div>
			<div class="classic-badge">{lt('Selective Attention & Conflict Resolution Test', 'নির্বাচিত মনোযোগ ও দ্বন্দ্ব সামলানোর পরীক্ষা')}</div>
			
			<div class="instruction-card">
				<div class="task-header">
					<h2>🎯 {lt('Your Mission: Focus on the Center!', 'আপনার কাজ: মাঝের তীরটিতে মন দিন!')}</h2>
				</div>
				
				<p class="importance">
					{@html lt(
						'This task measures your ability to <strong>selectively attend</strong> to relevant information while <strong>ignoring distractions</strong> - a key cognitive skill tested in the Attention Networks Test (ANT).',
						'এই টাস্কটি প্রাসঙ্গিক তথ্যের দিকে <strong>নির্বাচিতভাবে মন দেওয়া</strong> এবং <strong>বিভ্রান্তি উপেক্ষা করা</strong> - এই গুরুত্বপূর্ণ কগনিটিভ দক্ষতা মাপে, যা মনোযোগ নেটওয়ার্ক পরীক্ষা (ANT)-এ ব্যবহৃত হয়।'
					)}
				</p>
				
				<!-- Visual Examples -->
				<div class="stimulus-examples">
					<div class="example-card congruent-card">
						<div class="example-label">{lt('Congruent Trial (Easy)', 'সঙ্গত ট্রায়াল (সহজ)')}</div>
						<div class="arrow-display">→ → → → →</div>
						<div class="example-action">✓ {lt('All arrows match', 'সব তীর একই দিকে')}</div>
						<div class="example-note">
							{lt('CENTER arrow:', 'মাঝের তীর:')} <strong>{directionLabel('right')}</strong>
						</div>
					</div>
					
					<div class="example-card incongruent-card">
						<div class="example-label">{lt('Incongruent Trial (Hard)', 'অসঙ্গত ট্রায়াল (কঠিন)')}</div>
						<div class="arrow-display conflict">← ← → ← ←</div>
						<div class="example-action">⚠️ {lt('Flankers mislead!', 'পাশের তীরগুলো বিভ্রান্ত করবে!')}</div>
						<div class="example-note">
							{lt('CENTER arrow:', 'মাঝের তীর:')} <strong>{directionLabel('right')}</strong>
							{lt(' (ignore the rest!)', ' (বাকিগুলো উপেক্ষা করুন!)')}
						</div>
					</div>
				</div>
				
				<div class="rule-box">
					<strong>⚡ {lt('The Challenge:', 'চ্যালেঞ্জ:')}</strong>
					{#if $locale === 'bn'}
						স্ক্রিনে কয়েকটি তীর দেখা যাবে। <strong>সবসময় শুধু মাঝের তীরের দিকটাই বলুন।</strong>
						চারপাশের তীরগুলো কখনও উল্টো দিকে থাকবে, যাতে আপনার মনোযোগ ধরে রাখা ও বিভ্রান্তি প্রতিরোধের ক্ষমতা মাপা যায়।
					{:else}
						You'll see arrows on the screen. <strong>Always report the direction of the CENTER arrow only!</strong>
						Surrounding "flanker" arrows will sometimes point the opposite direction to test your ability to focus and resist distraction.
					{/if}
				</div>
				
				<!-- Two Column Layout -->
				<div class="info-grid">
					<div class="info-section">
						<h3>📋 {lt("What You'll Do", 'আপনি কী করবেন')}</h3>
						<div class="steps-list">
							<div class="step-item">
								<span class="step-num">{n(1)}</span>
								<div class="step-text">
									<strong>{lt('Watch for arrows', 'তীরচিহ্ন দেখুন')}</strong>
									<span>{lt('They appear briefly', 'এগুলো খুব অল্প সময়ের জন্য দেখা যায়')}</span>
								</div>
							</div>
							<div class="step-item">
								<span class="step-num">{n(2)}</span>
								<div class="step-text">
									<strong>{lt('Focus on CENTER', 'মাঝের তীরটিতে মন দিন')}</strong>
									<span>{lt('Ignore surrounding arrows', 'চারপাশের তীরগুলো উপেক্ষা করুন')}</span>
								</div>
							</div>
							<div class="step-item">
								<span class="step-num">{n(3)}</span>
								<div class="step-text">
									<strong>{lt('Press arrow key', 'তীরের কী চাপুন')}</strong>
									<span>{lt('← or → to match center', 'মাঝের তীরের দিক মিলিয়ে ← বা → চাপুন')}</span>
								</div>
							</div>
						</div>
					</div>
					
					<div class="info-section">
						<h3>💪 {lt('What It Measures', 'এটি কী মাপে')}</h3>
						<div class="measures-list">
							<div class="measure-item">✓ <strong>{lt('Selective Attention:', 'নির্বাচিত মনোযোগ:')}</strong> {lt('Focusing ability', 'মন স্থির রেখে লক্ষ্য বেছে নেওয়ার ক্ষমতা')}</div>
							<div class="measure-item">✓ <strong>{lt('Conflict Resolution:', 'দ্বন্দ্ব সামলানো:')}</strong> {lt('Ignoring distractors', 'বিভ্রান্তিকর সংকেত উপেক্ষা করা')}</div>
							<div class="measure-item">✓ <strong>{lt('Interference Control:', 'হস্তক্ষেপ নিয়ন্ত্রণ:')}</strong> {lt('Resistance to misleading info', 'ভুলপথে নেওয়া তথ্য প্রতিরোধ করার ক্ষমতা')}</div>
							<div class="measure-item">✓ <strong>{lt('Processing Speed:', 'প্রক্রিয়াকরণের গতি:')}</strong> {lt('Quick decision-making', 'দ্রুত ও সঠিক সিদ্ধান্ত নেওয়ার ক্ষমতা')}</div>
						</div>
					</div>
				</div>
				
				<!-- Clinical Context -->
				<div class="clinical-info">
					<h3>📚 {lt('Clinical Significance', 'ক্লিনিক্যাল গুরুত্ব')}</h3>
					<div class="clinical-grid">
						<div class="clinical-item">
							<strong>🎯 {lt('Standard Test:', 'মানক পরীক্ষা:')}</strong> {lt('Attention Networks Test', 'মনোযোগ নেটওয়ার্ক পরীক্ষা')} (Eriksen & Eriksen, {n(1974)})
						</div>
						<div class="clinical-item">
							<strong>🧠 {lt('Brain Regions:', 'মস্তিষ্কের অঞ্চল:')}</strong> {lt('Tests anterior cingulate cortex & executive control', 'অ্যান্টেরিয়র সিংগুলেট কর্টেক্স ও নির্বাহী নিয়ন্ত্রণ নেটওয়ার্কের কার্যকারিতা মাপে')}
						</div>
						<div class="clinical-item">
							<strong>🏥 {lt('MS Relevance:', 'MS-এ গুরুত্ব:')}</strong> {lt('Measures selective attention deficits common in MS', 'MS-এ সাধারণ নির্বাচিত মনোযোগ ঘাটতি মাপে')}
						</div>
						<div class="clinical-item">
							<strong>📈 {lt('Key Metric:', 'মূল সূচক:')}</strong> {lt('Conflict Effect = slower RT on incongruent trials', 'কনফ্লিক্ট ইফেক্ট = অসঙ্গত ট্রায়ালে ধীর প্রতিক্রিয়ার সময়')}
						</div>
					</div>
				</div>
				
				<!-- Controls -->
				<div class="controls-info">
					<h3>🎮 {lt('Controls', 'নিয়ন্ত্রণ')}</h3>
					<div class="key-bindings">
						<div class="key-bind">
							<kbd>←</kbd> {lt('or', 'অথবা')} <kbd>A</kbd> = {lt('Left arrow', 'বাম তীর')}
						</div>
						<div class="key-bind">
							<kbd>→</kbd> {lt('or', 'অথবা')} <kbd>D</kbd> = {lt('Right arrow', 'ডান তীর')}
						</div>
					</div>
				</div>
			</div>
			
			<div class="button-group">
				<button class="start-button" on:click={startInstructions}>
					{lt('Begin Task', 'টাস্ক শুরু করুন')}
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
				<div class="key-display">
					<kbd class="key-large">←</kbd>
					<span class="key-label">{lt('Left Arrow', 'বাম তীর')}</span>
				</div>
				<div class="key-display">
					<kbd class="key-large">→</kbd>
					<span class="key-label">{lt('Right Arrow', 'ডান তীর')}</span>
				</div>
			</div>

			<div class="task-rule">
				<p class="rule-emphasis">
					{@html lt(
						'Press the arrow key matching the <strong>CENTER arrow direction</strong> only!',
						'শুধু <strong>মাঝের তীরের দিক</strong> মিলিয়ে সংশ্লিষ্ট কী চাপুন!'
					)}
				</p>
			</div>

			<div class="instructions-flow">
				<div class="flow-step">
					<div class="flow-number">{n(1)}</div>
					<div class="flow-content">
						<p class="flow-title">{lt('Arrows Appear', 'তীরচিহ্ন দেখা যায়')}</p>
						<p class="flow-desc">{lt('5 arrows flash briefly', '৫টি তীর অল্প সময়ের জন্য দেখা যায়')}</p>
					</div>
				</div>

				<div class="flow-arrow">→</div>

				<div class="flow-step">
					<div class="flow-number">{n(2)}</div>
					<div class="flow-content">
						<p class="flow-title">{lt('Focus on Center', 'মাঝের তীরে মন দিন')}</p>
						<p class="flow-desc">{lt('Ignore outer flankers', 'বাইরের তীরগুলো উপেক্ষা করুন')}</p>
					</div>
				</div>

				<div class="flow-arrow">→</div>

				<div class="flow-step">
					<div class="flow-number">{n(3)}</div>
					<div class="flow-content">
						<p class="flow-title">{lt('Press Arrow Key', 'তীরের কী চাপুন')}</p>
						<p class="flow-desc">{lt('Match center direction', 'মাঝের তীরের দিক মিলিয়ে চাপুন')}</p>
					</div>
				</div>
			</div>

			<div class="example-reminder">
				<div class="example-row">
					<div class="example-stimulus">→ → → → →</div>
					<div class="example-answer">{lt('Press', 'চাপুন')} <kbd>→</kbd> {lt('(Easy - all match)', '(সহজ - সব একই দিকে)')}</div>
				</div>
				<div class="example-row conflict">
					<div class="example-stimulus">← ← → ← ←</div>
					<div class="example-answer">{lt('Press', 'চাপুন')} <kbd>→</kbd> {lt('(Hard - center is right!)', '(কঠিন - মাঝের তীরটি ডানে!)')}</div>
				</div>
			</div>

			<div class="tips-box">
				<h3>💡 {lt('Success Tips', 'ভালো করার উপায়')}</h3>
				<ul>
					<li><strong>{lt('Focus your eyes', 'চোখ মাঝখানে রাখুন')}</strong> {lt('on the center of the screen', 'স্ক্রিনের কেন্দ্রের দিকে')}</li>
					<li><strong>{lt('Ignore flankers', 'পাশের তীরগুলো উপেক্ষা করুন')}</strong> - {lt("they're designed to mislead you", 'এগুলো ইচ্ছাকৃতভাবে আপনাকে বিভ্রান্ত করবে')}</li>
					<li><strong>{lt('Respond quickly', 'দ্রুত সাড়া দিন')}</strong> - {lt('but accuracy matters more than speed', 'তবে গতি নয়, আগে সঠিকতা')}</li>
					<li><strong>{lt('Stay consistent', 'ধারাবাহিক থাকুন')}</strong> - {lt('maintain attention throughout', 'পুরো সময় মনোযোগ ধরে রাখুন')}</li>
				</ul>
			</div>

			<div class="practice-prompt">
				<p>{lt("Let's practice with 8 trials to get comfortable...", 'স্বচ্ছন্দ হতে ৮টি অনুশীলনী ট্রায়াল করি...')}</p>
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
				<p class="instruction-reminder">{lt('Press ← or → to match the CENTER arrow direction', 'মাঝের তীরের দিক মিলিয়ে ← বা → চাপুন')}</p>
			</div>

			<!-- Stimulus Display -->
			<div class="stimulus-area">
				{#if showStimulus}
					<div class="arrow-stimulus {practiceTrials[currentPractice].trial_type}">
						{generatePracticeArrowDisplay(practiceTrials[currentPractice])}
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
					<div class="arrow-stimulus {sessionData.trials[currentTrial].trial_type}">
						{generateArrowDisplay(sessionData.trials[currentTrial])}
					</div>
				{:else}
					<div class="fixation">+</div>
				{/if}
			</div>

			<div class="reminder-text">
				{lt('Focus on CENTER arrow only | ← or → keys', 'শুধু মাঝের তীরে মন দিন | ← বা → কী ব্যবহার করুন')}
			</div>
		</div>

	{:else if phase === 'results'}
		<!-- Results Screen -->
		<div class="results-container">
			<!-- Badge Notifications -->
			{#if newBadges.length > 0}
				<BadgeNotification badges={newBadges} />
			{/if}

			<div class="results-header">
				<h2>{lt('Flanker Task Complete!', 'ফ্ল্যাঙ্কার টাস্ক সম্পন্ন!')}</h2>
				<div class="performance-badge {performanceBadgeColor}">
					{performanceLevelLabel(metrics?.performance_level || 'Good')}
				</div>
			</div>

			<!-- Key Metrics Grid -->
			<div class="metrics-grid">
				<!-- Overall Accuracy -->
				<div class="metric-card accuracy-card">
					<div class="metric-label">{lt('Overall Accuracy', 'সামগ্রিক নির্ভুলতা')}</div>
					<div class="metric-value">{pct(metrics?.overall_accuracy || 0)}</div>
					<div class="metric-detail">
						{$locale === 'bn'
							? `${n(metrics?.total_correct || 0)}/${n(metrics?.total_trials || 0)} সঠিক`
							: `${metrics?.total_correct || 0}/${metrics?.total_trials || 0} correct`}
					</div>
				</div>

				<!-- Mean RT -->
				<div class="metric-card speed-card">
					<div class="metric-label">{lt('Mean Reaction Time', 'গড় প্রতিক্রিয়ার সময়')}</div>
					<div class="metric-value">{msText(metrics?.mean_rt || 0)}</div>
					<div class="metric-detail">{lt('Overall speed', 'মোট গতি')}</div>
				</div>

				<!-- Conflict Effect -->
				<div class="metric-card conflict-card">
					<div class="metric-label">⚠️ {lt('Conflict Effect', 'কনফ্লিক্ট ইফেক্ট')}</div>
					<div class="metric-value">{msText(metrics?.conflict_effect || 0)}</div>
					<div class="metric-detail">{lt('Interference cost', 'বিভ্রান্তির খরচ')}</div>
				</div>

				<!-- Selective Attention Score -->
				<div class="metric-card attention-card">
					<div class="metric-label">{lt('Selective Attention', 'নির্বাচিত মনোযোগ')}</div>
					<div class="metric-value">{n((metrics?.selective_attention_score || 0).toFixed(1), { minimumFractionDigits: 1, maximumFractionDigits: 1 })}</div>
					<div class="metric-detail">{lt('Lower = better focus', 'যত কম, মনোযোগ তত ভালো')}</div>
				</div>
			</div>

			<!-- Trial Type Breakdown -->
			<div class="breakdown-section">
				<h3>{lt('Performance by Trial Type', 'ট্রায়ালভিত্তিক পারফরম্যান্স')}</h3>
				<div class="breakdown-grid">
					<!-- Congruent Trials -->
					<div class="breakdown-card congruent-card">
						<p class="breakdown-title">{lt('Congruent Trials (Easy)', 'সঙ্গত ট্রায়াল (সহজ)')}</p>
						<p class="breakdown-subtitle">{lt('All arrows point same direction', 'সব তীর একই দিকে থাকে')}</p>
						<p class="breakdown-stat">{lt('Accuracy:', 'নির্ভুলতা:')} <span>{pct(metrics?.congruent_accuracy || 0)}</span></p>
						<p class="breakdown-stat">{lt('Mean RT:', 'গড় RT:')} <span>{msText(metrics?.congruent_mean_rt || 0)}</span></p>
						<p class="breakdown-stat">
							{lt('Correct:', 'সঠিক:')}
							<span>{n(metrics?.congruent_correct || 0)}/{n(metrics?.congruent_trials || 0)}</span>
						</p>
						<p class="breakdown-note">{lt('Tests baseline processing speed', 'মৌলিক প্রক্রিয়াকরণের গতি মাপে')}</p>
					</div>

					<!-- Incongruent Trials -->
					<div class="breakdown-card incongruent-card">
						<p class="breakdown-title">{lt('Incongruent Trials (Hard)', 'অসঙ্গত ট্রায়াল (কঠিন)')}</p>
						<p class="breakdown-subtitle">{lt('Flankers point opposite direction', 'পাশের তীরগুলো উল্টো দিকে থাকে')}</p>
						<p class="breakdown-stat">{lt('Accuracy:', 'নির্ভুলতা:')} <span>{pct(metrics?.incongruent_accuracy || 0)}</span></p>
						<p class="breakdown-stat">{lt('Mean RT:', 'গড় RT:')} <span>{msText(metrics?.incongruent_mean_rt || 0)}</span></p>
						<p class="breakdown-stat">
							{lt('Correct:', 'সঠিক:')}
							<span>{n(metrics?.incongruent_correct || 0)}/{n(metrics?.incongruent_trials || 0)}</span>
						</p>
						<p class="breakdown-note highlight">{lt('Tests selective attention & conflict resolution', 'নির্বাচিত মনোযোগ ও দ্বন্দ্ব সামলানোর ক্ষমতা মাপে')}</p>
					</div>
				</div>
			</div>

			<!-- Interference Analysis -->
			<div class="interference-section">
				<h3>🎯 {lt('Interference Analysis', 'বিভ্রান্তি বিশ্লেষণ')}</h3>
				<div class="interference-grid">
					<div class="interference-card">
						<p class="interference-label">{lt('Conflict Effect', 'কনফ্লিক্ট ইফেক্ট')}</p>
						<p class="interference-value">{msText(metrics?.conflict_effect || 0)}</p>
						<p class="interference-desc">
							{lt(
								'How much slower you are on incongruent trials. Lower = better selective attention!',
								'অসঙ্গত ট্রায়ালে আপনি কতটা ধীর হয়েছেন তা বোঝায়। যত কম, নির্বাচিত মনোযোগ তত ভালো!'
							)}
						</p>
					</div>
					<div class="interference-card">
						<p class="interference-label">{lt('Interference Error Rate', 'বিভ্রান্তিজনিত ভুলের হার')}</p>
						<p class="interference-value">{pct(metrics?.interference_error_rate || 0)}</p>
						<p class="interference-desc">
							{lt(
								'Percentage of errors caused by distraction. Lower = stronger focus!',
								'বিভ্রান্তির কারণে কত শতাংশ ভুল হয়েছে তা দেখায়। যত কম, মনোযোগ তত শক্তিশালী!'
							)}
						</p>
					</div>
				</div>
			</div>

			<!-- Interpretation -->
			<div class="interpretation-section">
				<h3>{lt('What This Means', 'এর অর্থ কী')}</h3>
				<p class="feedback-text">{resultsSummaryText()}</p>
				
				<div class="insights-list">
					{#if (metrics?.conflict_effect || 0) < 100}
						<div class="insight-item excellent">
							<span class="insight-icon">⭐</span>
							<span>{lt('Excellent selective attention! You resist distraction very well.', 'অসাধারণ নির্বাচিত মনোযোগ! আপনি বিভ্রান্তি খুব ভালোভাবে প্রতিরোধ করতে পারেন।')}</span>
						</div>
					{:else if (metrics?.conflict_effect || 0) < 150}
						<div class="insight-item good">
							<span class="insight-icon">✓</span>
							<span>{lt('Good selective attention. Normal interference effect.', 'ভালো নির্বাচিত মনোযোগ। বিভ্রান্তির প্রভাব স্বাভাবিক সীমায় আছে।')}</span>
						</div>
					{:else}
						<div class="insight-item needs-work">
							<span class="insight-icon">💡</span>
							<span>{lt('High interference - practice focusing on relevant information only.', 'বিভ্রান্তির প্রভাব বেশি - শুধু প্রাসঙ্গিক তথ্যের দিকে মন দেওয়ার অনুশীলন করুন।')}</span>
						</div>
					{/if}

					{#if (metrics?.incongruent_accuracy || 0) > 85}
						<div class="insight-item excellent">
							<span class="insight-icon">🎯</span>
							<span>{lt('Strong accuracy on hard trials - excellent conflict resolution!', 'কঠিন ট্রায়ালেও নির্ভুলতা খুব ভালো - দ্বন্দ্ব সামলানোর ক্ষমতা শক্তিশালী!')}</span>
						</div>
					{/if}

					{#if (metrics?.congruent_mean_rt || 0) < 500 && (metrics?.congruent_mean_rt || 0) > 0}
						<div class="insight-item good">
							<span class="insight-icon">⚡</span>
							<span>{lt('Fast processing speed on easy trials!', 'সহজ ট্রায়ালে প্রক্রিয়াকরণের গতি দ্রুত!')}</span>
						</div>
					{/if}
				</div>
			</div>

			<!-- Clinical Context -->
			<div class="clinical-context">
				<h3>📊 {lt('Clinical Context', 'ক্লিনিক্যাল প্রেক্ষাপট')}</h3>
				<p>
					{@html lt(
						'The <strong>Conflict Effect</strong> (incongruent RT - congruent RT) is the key measure of selective attention. Research shows this reflects anterior cingulate cortex function and executive control networks. Reducing your conflict effect through training indicates improved ability to ignore distractions and focus on relevant information.',
						'<strong>কনফ্লিক্ট ইফেক্ট</strong> (অসঙ্গত প্রতিক্রিয়ার সময় - সঙ্গত প্রতিক্রিয়ার সময়) হলো নির্বাচিত মনোযোগের একটি গুরুত্বপূর্ণ সূচক। গবেষণায় দেখা যায়, এটি অ্যান্টেরিয়র সিংগুলেট কর্টেক্স এবং নির্বাহী নিয়ন্ত্রণ নেটওয়ার্কের কার্যকারিতাকে প্রতিফলিত করে। অনুশীলনের মাধ্যমে কনফ্লিক্ট ইফেক্ট কমে গেলে বোঝা যায় যে বিভ্রান্তি উপেক্ষা করে প্রাসঙ্গিক তথ্যের দিকে মনোযোগ দেওয়ার ক্ষমতা উন্নত হচ্ছে।'
					)}
				</p>
			</div>

			<!-- Navigation -->
			<div class="button-group">
				<button class="primary-button" on:click={returnToDashboard}>
					{lt('Return to Dashboard', 'ড্যাশবোর্ডে ফিরে যান')}
				</button>
			</div>
		</div>
	{/if}
</div>

<style>
	.flanker-container {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem;
		min-height: 100vh;
	}

	/* Loading State */
	.loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 60vh;
		gap: 1rem;
	}

	.spinner {
		width: 50px;
		height: 50px;
		border: 4px solid rgba(59, 130, 246, 0.2);
		border-top-color: #3b82f6;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	/* Introduction Screen */
	.instructions {
		max-width: 900px;
		margin: 0 auto;
	}

	h1 {
		font-size: 2.5rem;
		font-weight: 700;
		text-align: center;
		margin-bottom: 1rem;
		background: linear-gradient(135deg, #3b82f6, #8b5cf6);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
	}

	.classic-badge {
		text-align: center;
		background: linear-gradient(135deg, #3b82f6, #8b5cf6);
		color: white;
		padding: 0.5rem 1.5rem;
		border-radius: 2rem;
		display: inline-block;
		margin: 0 auto 2rem;
		font-weight: 600;
		display: block;
		width: fit-content;
		margin-left: auto;
		margin-right: auto;
	}

	.instruction-card {
		background: white;
		border-radius: 1rem;
		padding: 2rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
		margin-bottom: 2rem;
	}

	.task-header h2 {
		font-size: 1.75rem;
		margin-bottom: 1rem;
		color: #1f2937;
	}

	.importance {
		font-size: 1.1rem;
		line-height: 1.6;
		color: #374151;
		margin-bottom: 2rem;
		padding: 1rem;
		background: #eff6ff;
		border-left: 4px solid #3b82f6;
		border-radius: 0.5rem;
	}

	/* Stimulus Examples */
	.stimulus-examples {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.5rem;
		margin: 2rem 0;
	}

	.example-card {
		padding: 1.5rem;
		border-radius: 0.75rem;
		text-align: center;
	}

	.congruent-card {
		background: #d1fae5;
		border: 2px solid #10b981;
	}

	.incongruent-card {
		background: #fee2e2;
		border: 2px solid #ef4444;
	}

	.example-label {
		font-weight: 600;
		font-size: 0.9rem;
		text-transform: uppercase;
		margin-bottom: 1rem;
		color: #374151;
	}

	.arrow-display {
		font-size: 3rem;
		margin: 1rem 0;
		font-weight: bold;
		letter-spacing: 0.5rem;
	}

	.arrow-display.conflict {
		color: #ef4444;
	}

	.example-action {
		font-weight: 600;
		margin-top: 1rem;
		color: #1f2937;
	}

	.example-note {
		font-size: 0.9rem;
		color: #6b7280;
		margin-top: 0.5rem;
	}

	.rule-box {
		background: #fef3c7;
		border: 2px solid #f59e0b;
		border-radius: 0.5rem;
		padding: 1rem;
		margin: 2rem 0;
	}

	/* Info Grid */
	.info-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 2rem;
		margin: 2rem 0;
	}

	.info-section h3 {
		font-size: 1.25rem;
		margin-bottom: 1rem;
		color: #1f2937;
	}

	.steps-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.step-item {
		display: flex;
		align-items: flex-start;
		gap: 1rem;
	}

	.step-num {
		background: #3b82f6;
		color: white;
		width: 2rem;
		height: 2rem;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 700;
		flex-shrink: 0;
	}

	.step-text {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.step-text strong {
		color: #1f2937;
	}

	.step-text span {
		font-size: 0.9rem;
		color: #6b7280;
	}

	.measures-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.measure-item {
		padding: 0.5rem;
		background: #f3f4f6;
		border-radius: 0.5rem;
		font-size: 0.95rem;
	}

	/* Clinical Info */
	.clinical-info {
		margin: 2rem 0;
	}

	.clinical-info h3 {
		font-size: 1.25rem;
		margin-bottom: 1rem;
		color: #1f2937;
	}

	.clinical-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}

	.clinical-item {
		padding: 1rem;
		background: #f9fafb;
		border-radius: 0.5rem;
		border-left: 3px solid #3b82f6;
		font-size: 0.9rem;
	}

	/* Controls Info */
	.controls-info {
		margin: 2rem 0;
	}

	.controls-info h3 {
		font-size: 1.25rem;
		margin-bottom: 1rem;
		color: #1f2937;
	}

	.key-bindings {
		display: flex;
		gap: 2rem;
		justify-content: center;
	}

	.key-bind {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 1.1rem;
	}

	kbd {
		background: #374151;
		color: white;
		padding: 0.5rem 1rem;
		border-radius: 0.375rem;
		font-family: monospace;
		font-weight: 600;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
	}

	/* Button Group */
	.button-group {
		display: flex;
		gap: 1rem;
		justify-content: center;
		margin-top: 2rem;
	}

	.start-button, .primary-button {
		background: linear-gradient(135deg, #3b82f6, #8b5cf6);
		color: white;
		border: none;
		padding: 1rem 2.5rem;
		border-radius: 0.75rem;
		font-size: 1.1rem;
		font-weight: 600;
		cursor: pointer;
		transition: transform 0.2s, box-shadow 0.2s;
	}

	.start-button:hover, .primary-button:hover {
		transform: translateY(-2px);
		box-shadow: 0 8px 16px rgba(59, 130, 246, 0.3);
	}

	.btn-secondary {
		background: #e5e7eb;
		color: #374151;
		border: none;
		padding: 1rem 2rem;
		border-radius: 0.75rem;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: background 0.2s;
	}

	.btn-secondary:hover {
		background: #d1d5db;
	}

	/* Quick Instructions */
	.quick-instructions {
		max-width: 800px;
		margin: 0 auto;
		background: white;
		border-radius: 1rem;
		padding: 2rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
	}

	.quick-instructions h2 {
		text-align: center;
		font-size: 2rem;
		margin-bottom: 2rem;
		color: #1f2937;
	}

	.key-reminder {
		display: flex;
		gap: 2rem;
		justify-content: center;
		margin: 2rem 0;
	}

	.key-display {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
	}

	.key-large {
		font-size: 2rem;
		padding: 1rem 1.5rem;
	}

	.key-label {
		font-weight: 600;
		color: #6b7280;
	}

	.task-rule {
		text-align: center;
		margin: 2rem 0;
	}

	.rule-emphasis {
		font-size: 1.3rem;
		color: #1f2937;
		padding: 1rem;
		background: #fef3c7;
		border-radius: 0.5rem;
		border: 2px solid #f59e0b;
	}

	.instructions-flow {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		margin: 2rem 0;
		padding: 2rem;
		background: #f9fafb;
		border-radius: 0.75rem;
	}

	.flow-step {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		flex: 1;
	}

	.flow-number {
		background: #3b82f6;
		color: white;
		width: 3rem;
		height: 3rem;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.5rem;
		font-weight: 700;
	}

	.flow-content {
		text-align: center;
	}

	.flow-title {
		font-weight: 600;
		color: #1f2937;
		margin-bottom: 0.25rem;
	}

	.flow-desc {
		font-size: 0.9rem;
		color: #6b7280;
	}

	.flow-arrow {
		font-size: 2rem;
		color: #9ca3af;
		font-weight: bold;
	}

	.example-reminder {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		margin: 2rem 0;
		padding: 1.5rem;
		background: #f3f4f6;
		border-radius: 0.75rem;
	}

	.example-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem;
		background: white;
		border-radius: 0.5rem;
	}

	.example-row.conflict {
		background: #fef2f2;
	}

	.example-stimulus {
		font-size: 1.5rem;
		font-weight: bold;
		letter-spacing: 0.3rem;
	}

	.example-answer {
		font-weight: 600;
		color: #374151;
	}

	.tips-box {
		background: #eff6ff;
		border: 2px solid #3b82f6;
		border-radius: 0.75rem;
		padding: 1.5rem;
		margin: 2rem 0;
	}

	.tips-box h3 {
		margin-bottom: 1rem;
		color: #1f2937;
	}

	.tips-box ul {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.tips-box li {
		padding-left: 1.5rem;
		position: relative;
	}

	.tips-box li::before {
		content: '💡';
		position: absolute;
		left: 0;
	}

	.practice-prompt {
		text-align: center;
		margin-top: 2rem;
	}

	.practice-prompt p {
		font-size: 1.1rem;
		margin-bottom: 1rem;
		color: #374151;
	}

	/* Trial Screen */
	.trial-screen {
		max-width: 1000px;
		margin: 0 auto;
	}

	.trial-header {
		text-align: center;
		margin-bottom: 2rem;
	}

	.trial-header h2 {
		font-size: 1.5rem;
		margin-bottom: 0.5rem;
		color: #1f2937;
	}

	.instruction-reminder {
		color: #6b7280;
		font-size: 1rem;
	}

	.progress-header {
		margin-bottom: 2rem;
	}

	.progress-top {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	.progress-badges {
		display: flex;
		gap: 0.5rem;
	}

	.badge-remaining {
		background: #dbeafe;
		color: #1e40af;
		padding: 0.25rem 0.75rem;
		border-radius: 1rem;
		font-size: 0.9rem;
		font-weight: 600;
	}

	.progress-bar-container {
		width: 100%;
		height: 8px;
		background: #e5e7eb;
		border-radius: 1rem;
		overflow: hidden;
	}

	.progress-bar-fill {
		height: 100%;
		background: linear-gradient(90deg, #3b82f6, #8b5cf6);
		transition: width 0.3s ease;
	}

	/* Stimulus Area */
	.stimulus-area {
		min-height: 400px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: white;
		border-radius: 1rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
		margin-bottom: 2rem;
	}

	.arrow-stimulus {
		font-size: 4rem;
		font-weight: bold;
		letter-spacing: 1rem;
		padding: 2rem;
	}

	.arrow-stimulus.congruent {
		color: #10b981;
	}

	.arrow-stimulus.incongruent {
		color: #ef4444;
	}

	.fixation {
		font-size: 4rem;
		color: #9ca3af;
		font-weight: 300;
	}

	.reminder-text {
		text-align: center;
		color: #6b7280;
		font-size: 1rem;
		margin-top: 1rem;
	}

	/* Feedback */
	.feedback-box {
		margin-top: 2rem;
		padding: 1.5rem;
		border-radius: 0.75rem;
		text-align: center;
		font-size: 1.1rem;
		font-weight: 600;
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

	.feedback-box.warning {
		background: #fef3c7;
		color: #92400e;
		border: 2px solid #f59e0b;
	}

	/* Results Screen */
	.results-container {
		max-width: 1000px;
		margin: 0 auto;
	}

	.results-header {
		text-align: center;
		margin-bottom: 2rem;
	}

	.results-header h2 {
		font-size: 2rem;
		margin-bottom: 1rem;
		color: #1f2937;
	}

	.performance-badge {
		display: inline-block;
		background: linear-gradient(135deg, var(--tw-gradient-stops));
		color: white;
		padding: 0.75rem 2rem;
		border-radius: 2rem;
		font-size: 1.25rem;
		font-weight: 700;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
	}

	/* Metrics Grid */
	.metrics-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1.5rem;
		margin-bottom: 2rem;
	}

	.metric-card {
		background: white;
		border-radius: 0.75rem;
		padding: 1.5rem;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
		text-align: center;
	}

	.metric-label {
		font-size: 0.9rem;
		color: #6b7280;
		margin-bottom: 0.5rem;
		text-transform: uppercase;
		font-weight: 600;
	}

	.metric-value {
		font-size: 2.5rem;
		font-weight: 700;
		color: #1f2937;
		margin-bottom: 0.25rem;
	}

	.metric-detail {
		font-size: 0.9rem;
		color: #9ca3af;
	}

	.accuracy-card {
		border-top: 4px solid #10b981;
	}

	.speed-card {
		border-top: 4px solid #3b82f6;
	}

	.conflict-card {
		border-top: 4px solid #ef4444;
	}

	.attention-card {
		border-top: 4px solid #8b5cf6;
	}

	/* Breakdown Section */
	.breakdown-section {
		margin: 2rem 0;
	}

	.breakdown-section h3 {
		font-size: 1.5rem;
		margin-bottom: 1rem;
		color: #1f2937;
	}

	.breakdown-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.5rem;
	}

	.breakdown-card {
		background: white;
		border-radius: 0.75rem;
		padding: 1.5rem;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
	}

	.breakdown-card.congruent-card {
		border-left: 4px solid #10b981;
		background: linear-gradient(to right, #d1fae5 0%, white 10%);
	}

	.breakdown-card.incongruent-card {
		border-left: 4px solid #ef4444;
		background: linear-gradient(to right, #fee2e2 0%, white 10%);
	}

	.breakdown-title {
		font-size: 1.1rem;
		font-weight: 700;
		margin-bottom: 0.25rem;
		color: #1f2937;
	}

	.breakdown-subtitle {
		font-size: 0.9rem;
		color: #6b7280;
		margin-bottom: 1rem;
	}

	.breakdown-stat {
		display: flex;
		justify-content: space-between;
		padding: 0.5rem 0;
		border-bottom: 1px solid #e5e7eb;
		font-size: 0.95rem;
	}

	.breakdown-stat span {
		font-weight: 600;
		color: #1f2937;
	}

	.breakdown-note {
		margin-top: 1rem;
		font-size: 0.9rem;
		color: #6b7280;
		font-style: italic;
	}

	.breakdown-note.highlight {
		color: #dc2626;
		font-weight: 600;
	}

	/* Interference Section */
	.interference-section {
		margin: 2rem 0;
	}

	.interference-section h3 {
		font-size: 1.5rem;
		margin-bottom: 1rem;
		color: #1f2937;
	}

	.interference-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.5rem;
	}

	.interference-card {
		background: linear-gradient(135deg, #fef3c7, #fef9c3);
		border: 2px solid #f59e0b;
		border-radius: 0.75rem;
		padding: 1.5rem;
		text-align: center;
	}

	.interference-label {
		font-size: 0.9rem;
		font-weight: 600;
		color: #78350f;
		text-transform: uppercase;
		margin-bottom: 0.5rem;
	}

	.interference-value {
		font-size: 2rem;
		font-weight: 700;
		color: #92400e;
		margin-bottom: 0.5rem;
	}

	.interference-desc {
		font-size: 0.9rem;
		color: #78350f;
		line-height: 1.4;
	}

	/* Interpretation Section */
	.interpretation-section {
		background: white;
		border-radius: 0.75rem;
		padding: 2rem;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
		margin: 2rem 0;
	}

	.interpretation-section h3 {
		font-size: 1.5rem;
		margin-bottom: 1rem;
		color: #1f2937;
	}

	.feedback-text {
		font-size: 1.1rem;
		line-height: 1.6;
		color: #374151;
		margin-bottom: 1.5rem;
	}

	.insights-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.insight-item {
		display: flex;
		align-items: flex-start;
		gap: 1rem;
		padding: 1rem;
		border-radius: 0.5rem;
	}

	.insight-item.excellent {
		background: #d1fae5;
		border-left: 4px solid #10b981;
	}

	.insight-item.good {
		background: #dbeafe;
		border-left: 4px solid #3b82f6;
	}

	.insight-item.needs-work {
		background: #fef3c7;
		border-left: 4px solid #f59e0b;
	}

	.insight-icon {
		font-size: 1.5rem;
	}

	/* Clinical Context */
	.clinical-context {
		background: #f9fafb;
		border: 2px solid #e5e7eb;
		border-radius: 0.75rem;
		padding: 1.5rem;
		margin: 2rem 0;
	}

	.clinical-context h3 {
		font-size: 1.25rem;
		margin-bottom: 1rem;
		color: #1f2937;
	}

	.clinical-context p {
		line-height: 1.6;
		color: #374151;
	}

	/* Responsive Design */
	@media (max-width: 768px) {
		.flanker-container {
			padding: 1rem;
		}

		h1 {
			font-size: 2rem;
		}

		.stimulus-examples,
		.info-grid,
		.clinical-grid,
		.breakdown-grid,
		.interference-grid {
			grid-template-columns: 1fr;
		}

		.arrow-display {
			font-size: 2rem;
			letter-spacing: 0.3rem;
		}

		.arrow-stimulus {
			font-size: 2.5rem;
			letter-spacing: 0.5rem;
		}

		.instructions-flow {
			flex-direction: column;
		}

		.flow-arrow {
			transform: rotate(90deg);
		}

		.metrics-grid {
			grid-template-columns: 1fr;
		}
	}
</style>

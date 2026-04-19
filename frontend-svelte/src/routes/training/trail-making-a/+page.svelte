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
	import { buildPracticePayload, getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
import { TASK_RETURN_CONTEXT } from '$lib/task-navigation';
	import { onDestroy, onMount } from 'svelte';

	// Task states
	const STATE = {
		LOADING: 'loading',
		INSTRUCTIONS: 'instructions',
		READY: 'ready',
		TESTING: 'testing',
		COMPLETE: 'complete'
	};

	let state = STATE.LOADING;
	let difficulty = 5;
	let trial = null;
	let taskId = null;
	
	// Canvas and drawing
	let canvas;
	let ctx;
	let canvasScale = 1;
	
	// Test state
	let currentNumber = 1;
	let startTime = 0;
	let completionTime = 0;
	let elapsedTime = 0; // Add reactive elapsed time variable
	let clicks = [];
	let errors = [];
	let lines = [];
	let timerInterval = null; // Add timer interval reference
	let countdownHandle = null;
	let canvasInitTimeout = null;

	let showHelp = false;
	let sessionResults = null;
	let countdown = 3;
	/** @type {"practice" | "recorded"} */
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';
	let recordedTrial = null;

	function t(text) {
		return translateText(text, $locale);
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

	function secondsLabel(value, options = {}) {
		const formatted = n(value, {
			minimumFractionDigits: 1,
			maximumFractionDigits: 1,
			...options
		});
		return $locale === 'bn' ? `${formatted} সেকেন্ড` : `${formatted}s`;
	}

	function levelBadge(value = difficulty) {
		return $locale === 'bn' ? `লেভেল ${n(value)}` : `Level ${value}`;
	}

	function difficultyChangeLabel(before, after) {
		return $locale === 'bn'
			? `কঠিনতা: ${n(before)} → ${n(after)}`
			: `Difficulty: ${before} → ${after}`;
	}

	onMount(async () => {
		await loadSession();
	});

	onDestroy(() => {
		// Clean up timer interval
		if (timerInterval) {
			clearInterval(timerInterval);
			timerInterval = null;
		}
		if (countdownHandle) {
			clearInterval(countdownHandle);
			countdownHandle = null;
		}
		if (canvasInitTimeout) {
			clearTimeout(canvasInitTimeout);
			canvasInitTimeout = null;
		}
	});

	async function loadSession() {
		try {
			const userData = JSON.parse(localStorage.getItem('user') || '{}');
			const userId = userData.id;

			if (!userId) {
				goto('/login');
				return;
			}

			// Check if difficulty is provided via URL (dev tool override)
			const urlDifficulty = $page.url.searchParams.get('difficulty');
			if (urlDifficulty) {
				difficulty = parseInt(urlDifficulty);
				console.log('🔧 Trail Making A - Using URL difficulty:', difficulty);
			} else {
				// Get user's training plan to determine difficulty
				const planRes = await fetch(`http://localhost:8000/api/training/plan/${userId}`);

				if (planRes.ok) {
					const plan = await planRes.json();

					let userDifficulty = 5;
					if (plan && plan.current_difficulty) {
						const currentDiff =
							typeof plan.current_difficulty === 'string'
								? JSON.parse(plan.current_difficulty)
								: plan.current_difficulty;
						userDifficulty = currentDiff.processing_speed || 5;
					}

					difficulty = userDifficulty;
					console.log('📊 Trail Making A - Using plan difficulty:', difficulty);
				} else {
					// Default to level 5 if plan not found
					difficulty = 5;
					console.log('⚠️ Trail Making A - Plan not found, using default difficulty:', difficulty);
				}
			}

			const response = await fetch(
				`http://localhost:8000/api/training/tasks/trail-making-a/generate/${userId}?difficulty=${difficulty}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' }
				}
			);

			if (!response.ok) throw new Error('Failed to load session');

			const data = await response.json();
			trial = structuredClone(data.trial);
			recordedTrial = structuredClone(data.trial);
			
			state = STATE.INSTRUCTIONS;
		} catch (error) {
			console.error('Error loading session:', error);
			alert(t('Failed to load task session'));
			goto('/dashboard');
		}
	}

	/** @param {"practice" | "recorded"} nextMode */
	function startTest(nextMode = TASK_PLAY_MODE.RECORDED) {
		if (timerInterval) {
			clearInterval(timerInterval);
			timerInterval = null;
		}
		if (countdownHandle) {
			clearInterval(countdownHandle);
			countdownHandle = null;
		}
		if (canvasInitTimeout) {
			clearTimeout(canvasInitTimeout);
			canvasInitTimeout = null;
		}

		playMode = nextMode;
		practiceStatusMessage = '';
		trial = nextMode === TASK_PLAY_MODE.PRACTICE
			? buildPracticePayload('trail-making-a', { trial: recordedTrial }).trial
			: structuredClone(recordedTrial);
		state = STATE.READY;
		countdown = 3;
		
		countdownHandle = setInterval(() => {
			countdown--;
			if (countdown <= 0) {
				clearInterval(countdownHandle);
				countdownHandle = null;
				beginTest();
			}
		}, 1000);
	}

	function leavePractice(completed = false) {
		if (timerInterval) {
			clearInterval(timerInterval);
			timerInterval = null;
		}
		if (countdownHandle) {
			clearInterval(countdownHandle);
			countdownHandle = null;
		}
		if (canvasInitTimeout) {
			clearTimeout(canvasInitTimeout);
			canvasInitTimeout = null;
		}

		trial = structuredClone(recordedTrial);
		playMode = TASK_PLAY_MODE.RECORDED;
		practiceStatusMessage = completed ? getPracticeCopy($locale).complete : '';
		currentNumber = 1;
		startTime = 0;
		completionTime = 0;
		elapsedTime = 0;
		clicks = [];
		errors = [];
		lines = [];
		countdown = 3;
		state = STATE.INSTRUCTIONS;
	}

	function beginTest() {
		state = STATE.TESTING;
		currentNumber = 1;
		startTime = Date.now();
		elapsedTime = 0;
		clicks = [];
		errors = [];
		lines = [];
		
		// Start timer to update elapsed time
		timerInterval = setInterval(() => {
			elapsedTime = (Date.now() - startTime) / 1000;
		}, 100); // Update every 100ms for smooth display

		// Initialize canvas
		canvasInitTimeout = setTimeout(() => {
			canvasInitTimeout = null;
			initCanvas();
			drawCircles();
		}, 100);
	}

	function initCanvas() {
		if (!canvas) return;
		
		ctx = canvas.getContext('2d');
		
		// Set canvas size to match trial dimensions
		canvas.width = trial.canvas_width;
		canvas.height = trial.canvas_height;
		
		// Calculate scale to fit container
		const container = canvas.parentElement;
		const scaleX = container.clientWidth / trial.canvas_width;
		const scaleY = container.clientHeight / trial.canvas_height;
		canvasScale = Math.min(scaleX, scaleY, 1);
		
		canvas.style.width = `${trial.canvas_width * canvasScale}px`;
		canvas.style.height = `${trial.canvas_height * canvasScale}px`;
	}

	function drawCircles() {
		if (!ctx) return;
		
		// Clear canvas
		ctx.clearRect(0, 0, canvas.width, canvas.height);
		
		// Draw lines between connected circles
		ctx.strokeStyle = '#4CAF50';
		ctx.lineWidth = 3;
		for (const line of lines) {
			ctx.beginPath();
			ctx.moveTo(line.fromX, line.fromY);
			ctx.lineTo(line.toX, line.toY);
			ctx.stroke();
		}
		
		// Draw distractors
		ctx.font = 'bold 20px Arial';
		ctx.textAlign = 'center';
		ctx.textBaseline = 'middle';
		
		for (const distractor of trial.distractors) {
			// Circle
			ctx.fillStyle = '#e0e0e0';
			ctx.beginPath();
			ctx.arc(distractor.x, distractor.y, distractor.radius, 0, 2 * Math.PI);
			ctx.fill();
			
			ctx.strokeStyle = '#999';
			ctx.lineWidth = 2;
			ctx.stroke();
			
			// Symbol
			ctx.fillStyle = '#666';
			ctx.fillText(t(distractor.symbol), distractor.x, distractor.y);
		}
		
		// Draw circles
		ctx.font = 'bold 24px Arial';
		
		for (const circle of trial.circles) {
			const isCompleted = circle.number < currentNumber;
			const isLastClicked = circle.number === currentNumber - 1; // Most recently clicked

			// Circle fill - Yellow for last clicked, Green for earlier completed, White for unclicked
			if (isLastClicked) {
				ctx.fillStyle = '#FFC107'; // Yellow for current/last clicked
			} else if (isCompleted) {
				ctx.fillStyle = '#4CAF50'; // Green for previously completed
			} else {
				ctx.fillStyle = 'white'; // White for not yet clicked
			}
			
			ctx.beginPath();
			ctx.arc(circle.x, circle.y, circle.radius, 0, 2 * Math.PI);
			ctx.fill();
			
			// Border - Thicker for last clicked
			if (isLastClicked) {
				ctx.strokeStyle = '#FF9800';
				ctx.lineWidth = 4;
			} else if (isCompleted) {
				ctx.strokeStyle = '#388E3C';
				ctx.lineWidth = 3;
			} else {
				ctx.strokeStyle = '#667eea';
				ctx.lineWidth = 2;
			}
			ctx.stroke();
			
			// Number text - White on completed, dark on unclicked
			ctx.fillStyle = (isCompleted || isLastClicked) ? 'white' : '#2c3e50';
			ctx.fillText(n(circle.number), circle.x, circle.y);
		}
	}

	function handleCanvasClick(event) {
		if (state !== STATE.TESTING) return;
		
		const rect = canvas.getBoundingClientRect();
		const scaleX = canvas.width / rect.width;
		const scaleY = canvas.height / rect.height;
		
		const x = (event.clientX - rect.left) * scaleX;
		const y = (event.clientY - rect.top) * scaleY;
		
		// Check which circle was clicked
		let clickedCircle = null;
		
		for (const circle of trial.circles) {
			const distance = Math.sqrt((x - circle.x) ** 2 + (y - circle.y) ** 2);
			if (distance <= circle.radius) {
				clickedCircle = circle;
				break;
			}
		}
		
		if (clickedCircle) {
			handleCircleClick(clickedCircle, x, y);
		}
	}

	function handleCircleClick(circle, x, y) {
		const timestamp = Date.now() - startTime;
		
		clicks.push({
			number: circle.number,
			x: x,
			y: y,
			timestamp: timestamp
		});
		
		if (circle.number === currentNumber) {
			// Correct click
			if (currentNumber > 1) {
				// Draw line from previous circle
				const prevCircle = trial.circles.find(c => c.number === currentNumber - 1);
				if (prevCircle) {
					lines.push({
						fromX: prevCircle.x,
						fromY: prevCircle.y,
						toX: circle.x,
						toY: circle.y
					});
				}
			}
			
			currentNumber++;
			
			// Check if completed
			if (currentNumber > trial.circles.length) {
				completeTest();
			}
		} else {
			// Incorrect click - record error
			errors.push({
				timestamp: timestamp,
				clicked_number: circle.number,
				expected_number: currentNumber
			});
		}
		
		drawCircles();
	}

	function completeTest() {
		completionTime = Date.now() - startTime;

		// Stop the timer interval
		if (timerInterval) {
			clearInterval(timerInterval);
			timerInterval = null;
		}

		submitResults();
	}

	async function submitResults() {
		if (playMode === TASK_PLAY_MODE.PRACTICE) {
			leavePractice(true);
			return;
		}

		state = STATE.LOADING;
		taskId = $page.url.searchParams.get('taskId');
		
		try {
			const userData = JSON.parse(localStorage.getItem('user') || '{}');
			const userId = userData.id;

			const response = await fetch(
				`http://localhost:8000/api/training/tasks/trail-making-a/submit/${userId}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						difficulty: difficulty,
						trial: trial,
						completion_time: completionTime,
						errors: errors,
						clicks: clicks,
						task_id: taskId
					})
				}
			);

			if (!response.ok) throw new Error('Failed to submit results');

			sessionResults = await response.json();
			state = STATE.COMPLETE;
		} catch (error) {
			console.error('Error submitting results:', error);
			alert(t('Failed to submit results'));
		}
	}

	function toggleHelp() {
		showHelp = !showHelp;
	}

	function getPerformanceColor(level) {
		switch(level) {
			case 'Excellent': return '#4CAF50';
			case 'Good': return '#8BC34A';
			case 'Average': return '#FFC107';
			default: return '#FF9800';
		}
	}
</script>

<div class="tmt-container" data-localize-skip>
	<div class="tmt-inner">
		{#if state === STATE.LOADING}
			<LoadingSkeleton variant="card" count={3} />
		{:else if state === STATE.INSTRUCTIONS}
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />
			<div class="instructions-card">
				<div class="header-content">
					<div class="title-row">
						<h1>Trail Making Test — Part A</h1>
						<DifficultyBadge difficulty={difficulty} domain="Processing Speed" />
					</div>
					<p class="subtitle">Connect numbered circles in order — as fast as you can</p>
					<div class="classic-badge">TMT-A · Halstead-Reitan Battery · MACFIMS Processing Speed</div>
				</div>

				{#if playMode === TASK_PLAY_MODE.PRACTICE && practiceStatusMessage}
					<div class="practice-note">{practiceStatusMessage}</div>
				{/if}

				<div class="task-concept">
					<h3>The Challenge</h3>
					<p>
						{$locale === 'bn'
							? `${n(trial.circles.length)}টি সংখ্যাযুক্ত বৃত্ত এলোমেলোভাবে ছড়িয়ে আছে। যত দ্রুত সম্ভব ১→২→৩→...→${n(trial.circles.length)} ক্রমে ক্লিক করুন।`
							: `${n(trial.circles.length)} numbered circles are scattered randomly. Click them in order 1 → 2 → 3 → ... → ${n(trial.circles.length)} as fast as possible!`}
					</p>
					<div class="demo-sequence">
						<div class="demo-circle first">1</div>
						<div class="demo-arrow">→</div>
						<div class="demo-circle">2</div>
						<div class="demo-arrow">→</div>
						<div class="demo-circle">3</div>
						<div class="demo-arrow">→</div>
						<div class="demo-dots">…{n(trial.circles.length)}</div>
					</div>
				</div>

				<div class="rules-grid">
					<div class="rule-card">
						<span class="rule-icon">⊕</span>
						<div class="rule-text">
							<strong>{$locale === 'bn' ? 'স্ক্যান করুন' : 'Step 1: Scan'}</strong>
							<span>{$locale === 'bn' ? 'বোর্ডে ১ নম্বর বৃত্তটি খুঁজুন' : 'Find circle number 1 on the board'}</span>
						</div>
					</div>
					<div class="rule-card">
						<span class="rule-icon">↑</span>
						<div class="rule-text">
							<strong>{$locale === 'bn' ? 'ক্লিক করুন' : 'Step 2: Click'}</strong>
							<span>{$locale === 'bn' ? 'সঠিক বৃত্তে ক্লিক বা ট্যাপ করুন' : 'Click or tap the correct circle'}</span>
						</div>
					</div>
					<div class="rule-card">
						<span class="rule-icon">→</span>
						<div class="rule-text">
							<strong>{$locale === 'bn' ? 'এগিয়ে যান' : 'Step 3: Continue'}</strong>
							<span>{$locale === 'bn' ? 'পরবর্তী সংখ্যায় যান' : 'Move to the next number in sequence'}</span>
						</div>
					</div>
					<div class="rule-card">
						<span class="rule-icon">▷</span>
						<div class="rule-text">
							<strong>{$locale === 'bn' ? 'গতি বাড়ান' : 'Step 4: Speed'}</strong>
							<span>{$locale === 'bn' ? 'যত দ্রুত সম্ভব সব বৃত্ত শেষ করুন' : 'Complete all circles as fast as you can'}</span>
						</div>
					</div>
				</div>

				<div class="info-grid">
					<div class="info-section">
						<h4>{t('Speed Tips')}</h4>
						<ul class="tips-list">
							<li><strong>{t('Scan ahead:')}</strong> {$locale === 'bn' ? 'বর্তমান বৃত্তে ক্লিক করতে করতে পরের সংখ্যাটি খুঁজুন' : 'Find the next number while clicking the current one'}</li>
							<li><strong>{t('Click center:')}</strong> {$locale === 'bn' ? 'প্রতিটি বৃত্তের মাঝখানে চাপুন' : 'Aim for the center of each circle'}</li>
							<li><strong>{t('Direct lines:')}</strong> {$locale === 'bn' ? 'মাউস বা আঙুল সরলরেখায় চালান' : 'Move in straight lines between circles'}</li>
							<li><strong>{t('Spot clusters:')}</strong> {$locale === 'bn' ? 'কাছাকাছি সংখ্যার গুচ্ছ লক্ষ্য করুন' : 'Recognize groups of nearby numbers'}</li>
						</ul>
					</div>
					<div class="info-section">
						<h4>{t('Test Format')}</h4>
						<ul class="structure-list">
							<li><span class="struct-key">{t('Circles')}</span><span class="struct-val">{n(trial.circles.length)} {t('numbered')}</span></li>
							<li><span class="struct-key">{t('No time limit')}</span><span class="struct-val">{t('finish all circles')}</span></li>
							<li><span class="struct-key">{t('Measures')}</span><span class="struct-val">{t('time + errors')}</span></li>
							<li><span class="struct-key">{t('Difficulty')}</span><span class="struct-val">{levelBadge()}</span></li>
						</ul>
					</div>
				</div>

				<div class="clinical-info">
					<h4>{t('Clinical Significance')}</h4>
					<div class="clinical-grid">
						<div class="clinical-item">
							<strong>{t('Gold Standard')}</strong>
							<span>{$locale === 'bn' ? 'Halstead-Reitan Battery-র ক্লাসিক মূল্যায়ন' : 'Classic Halstead-Reitan Battery test'}</span>
						</div>
						<div class="clinical-item">
							<strong>{t('Measures')}</strong>
							<span>{$locale === 'bn' ? 'সাইকোমোটর গতি ও ভিজ্যুয়াল স্ক্যানিং' : 'Psychomotor speed & visual scanning'}</span>
						</div>
						<div class="clinical-item">
							<strong>{t('MS Relevance')}</strong>
							<span>{$locale === 'bn' ? 'এমএসের অগ্রগতিতে অত্যন্ত সংবেদনশীল' : 'Highly sensitive to MS progression'}</span>
						</div>
						<div class="clinical-item">
							<strong>{t('Real-World Impact')}</strong>
							<span>{$locale === 'bn' ? 'ড্রাইভিং ও নেভিগেশন সক্ষমতার পূর্বাভাস দেয়' : 'Predicts driving & navigation ability'}</span>
						</div>
					</div>
				</div>

				<div class="perf-guide">
					<h4>{t('Performance Norms (MS Patients)')}</h4>
					<div class="norm-bars">
						<div class="norm-bar norm-excellent">
							<span class="norm-label">{t('Excellent')}</span>
							<span class="norm-val">{$locale === 'bn' ? '&lt;২৯ সেকেন্ড' : '<29 seconds'}</span>
						</div>
						<div class="norm-bar norm-good">
							<span class="norm-label">{t('Good')}</span>
							<span class="norm-val">{$locale === 'bn' ? '২৯–৩৯ সেকেন্ড' : '29–39 seconds'}</span>
						</div>
						<div class="norm-bar norm-avg">
							<span class="norm-label">{t('Average')}</span>
							<span class="norm-val">{$locale === 'bn' ? '৪০–৭৮ সেকেন্ড' : '40–78 seconds'}</span>
						</div>
						<div class="norm-bar norm-fair">
							<span class="norm-label">{t('Fair')}</span>
							<span class="norm-val">{$locale === 'bn' ? '৭৯–১০০ সেকেন্ড' : '79–100 seconds'}</span>
						</div>
						<div class="norm-bar norm-needs">
							<span class="norm-label">{t('Needs Practice')}</span>
							<span class="norm-val">{$locale === 'bn' ? '&gt;১০০ সেকেন্ড' : '>100 seconds'}</span>
						</div>
					</div>
					<p class="norm-note">{$locale === 'bn' ? '*সময় ২৫টি বৃত্তের মানদণ্ডে সমন্বিত' : '*Times normalized to 25 circles from MS patient clinical data.'}</p>
				</div>

				<div class="button-group">
					<TaskPracticeActions
						locale={$locale}
						startLabel={localeText({ en: 'Start Actual Task', bn: 'আসল টাস্ক শুরু করুন' }, $locale)}
						statusMessage={practiceStatusMessage}
						align="center"
						on:start={() => startTest(TASK_PLAY_MODE.RECORDED)}
						on:practice={() => startTest(TASK_PLAY_MODE.PRACTICE)}
					/>
				</div>
			</div>

		{:else if state === STATE.READY}
			<div class="screen-card ready-screen">
				{#if playMode === TASK_PLAY_MODE.PRACTICE}
					<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
				{/if}
				<h2>{t('Get Ready!')}</h2>
				<p class="ready-message">{t('Connect the numbered circles in order as fast as you can')}</p>
				<div class="ready-sequence">
					<div class="ready-circle">{n(1)}</div>
					<div class="ready-arrow">→</div>
					<div class="ready-circle">{n(2)}</div>
					<div class="ready-arrow">→</div>
					<div class="ready-circle">{n(3)}</div>
					<div class="ready-arrow">→</div>
					<div class="ready-dots">…</div>
				</div>
				<div class="countdown">{n(countdown)}</div>
			</div>

		{:else if state === STATE.TESTING}
			<div class="screen-card testing-screen">
				{#if playMode === TASK_PLAY_MODE.PRACTICE}
					<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
				{/if}
				<div class="test-header">
					<div class="test-badges">
						<span class="next-badge">
							{$locale === 'bn' ? 'পরবর্তী:' : 'Next:'} <strong>{n(currentNumber)}</strong>
						</span>
						<span class="count-badge">{n(currentNumber - 1)} / {n(trial.circles.length)}</span>
						{#if errors.length > 0}
							<span class="error-badge">{t('Errors:')} {n(errors.length)}</span>
						{/if}
					</div>
					<div class="timer-display">
						<span class="timer-icon">⏱️</span>
						<span class="timer-value">{secondsLabel(elapsedTime)}</span>
					</div>
					<button class="help-btn-sm" on:click={toggleHelp}>?</button>
				</div>

				<div class="canvas-container">
					<canvas
						bind:this={canvas}
						on:click={handleCanvasClick}
					></canvas>
				</div>

				<div class="instruction-bar">
					<p>{t('Click the circles in numerical order: 1 → 2 → 3 → ...')}</p>
					<p class="current-target">
						{t('Looking for:')} <strong>{n(currentNumber)}</strong>
					</p>
				</div>
			</div>

		{:else if state === STATE.COMPLETE}
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />
			<div class="screen-card complete-screen">
				{#if sessionResults}
					{@const perfColor = getPerformanceColor(sessionResults.metrics.performance_level)}
					<div class="perf-banner" style="--perf-color: {perfColor}">
						<div class="perf-level">{t(sessionResults.metrics.performance_level)}</div>
						<div class="perf-subtitle">{secondsLabel(sessionResults.metrics.completion_time)} · {t('Trail Making Test Complete!')}</div>
					</div>

					<div class="metrics-grid">
						<div class="metric-card highlight">
							<div class="metric-icon">▷</div>
							<div class="metric-value">{secondsLabel(sessionResults.metrics.completion_time)}</div>
							<div class="metric-label">{t('Completion Time')}</div>
							<div class="metric-sub">{t('Normalized:')} {secondsLabel(sessionResults.metrics.normalized_time)}</div>
						</div>
						<div class="metric-card">
							<div class="metric-icon">◎</div>
							<div class="metric-value">{n(sessionResults.metrics.score)}</div>
							<div class="metric-label">{t('Score')}</div>
							<div class="metric-sub">{t('Out of 100')}</div>
						</div>
						<div class="metric-card">
							<div class="metric-icon">✓</div>
							<div class="metric-value">{pct(sessionResults.metrics.accuracy, { minimumFractionDigits: 0, maximumFractionDigits: 1 })}</div>
							<div class="metric-label">{t('Accuracy')}</div>
							<div class="metric-sub">{n(sessionResults.metrics.errors)} {t('errors')}</div>
						</div>
						<div class="metric-card">
							<div class="metric-icon">→</div>
							<div class="metric-value">{n(sessionResults.metrics.processing_speed)}</div>
							<div class="metric-label">{t('Processing Speed')}</div>
							<div class="metric-sub">{t('Circles/second')}</div>
						</div>
					</div>

					<div class="breakdown">
						<h3>{t('Detailed Analysis')}</h3>
						<div class="breakdown-row">
							<span class="bd-label">{t('Total Clicks')}</span>
							<span class="bd-val">{n(sessionResults.metrics.total_clicks)}</span>
						</div>
						<div class="breakdown-row">
							<span class="bd-label">{t('Errors Made')}</span>
							<span class="bd-val" class:bd-error={sessionResults.metrics.errors > 0} class:bd-success={sessionResults.metrics.errors === 0}>
								{n(sessionResults.metrics.errors)}
							</span>
						</div>
						<div class="breakdown-row">
							<span class="bd-label">{t('Path Efficiency')}</span>
							<span class="bd-val">{pct(sessionResults.metrics.path_efficiency, { minimumFractionDigits: 0, maximumFractionDigits: 1 })}</span>
						</div>
						<div class="breakdown-row">
							<span class="bd-label">{t('Performance Level')}</span>
							<span class="bd-val" style="color: {perfColor}">{t(sessionResults.metrics.performance_level)}</span>
						</div>
					</div>

					<div class="clinical-note">
						<h4>{t('Clinical Context')}</h4>
						<p>
							{#if sessionResults.metrics.performance_level === 'Excellent'}
								{$locale === 'bn'
									? 'চমৎকার পারফরম্যান্স! আপনার প্রসেসিং স্পিড ও ভিজ্যুয়াল স্ক্যানিং গড়ের চেয়ে অনেক ভালো।'
									: 'Outstanding performance! Your processing speed and visual scanning are well above average for MS patients, indicating excellent psychomotor function.'}
							{:else if sessionResults.metrics.performance_level === 'Good'}
								{$locale === 'bn'
									? 'খুব ভালো পারফরম্যান্স! আপনার প্রসেসিং স্পিড এমএস রোগীদের গড়ের চেয়ে ভালো।'
									: 'Great performance! Your processing speed is above average for MS patients. Keep up the excellent work!'}
							{:else if sessionResults.metrics.performance_level === 'Average'}
								{$locale === 'bn'
									? 'ভালো পারফরম্যান্স! আপনার সময় স্বাভাবিক সীমার মধ্যে রয়েছে।'
									: 'Good performance! Your time is in the normal range for MS patients. Regular practice can help improve speed and efficiency.'}
							{:else}
								{$locale === 'bn'
									? 'অনুশীলন চালিয়ে যান। নিয়মিত ট্রেনিংয়ে প্রসেসিং স্পিড উল্লেখযোগ্যভাবে উন্নত হতে পারে।'
									: 'Keep practicing! Processing speed and visual scanning can improve significantly with regular training.'}
							{/if}
						</p>
					</div>

					<div class="difficulty-info">
						<span>{difficultyChangeLabel(sessionResults.difficulty_before, sessionResults.difficulty_after)}</span>
						<span class="adapt-reason">{t(sessionResults.adaptation_reason)}</span>
					</div>

					{#if sessionResults.new_badges && sessionResults.new_badges.length > 0}
						<BadgeNotification badges={sessionResults.new_badges} />
					{/if}

					<div class="button-group">
						<button class="start-button" on:click={() => goto('/training')}>{t('Back to Training')}</button>
						<button class="btn-secondary" on:click={() => goto('/dashboard')}>{t('View Dashboard')}</button>
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>

{#if showHelp}
	<div class="modal-overlay" on:click={toggleHelp} role="presentation">
		<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
		<div class="modal-content" on:click|stopPropagation role="dialog" tabindex="-1" on:keydown={(e) => e.key === 'Escape' && toggleHelp()}>
			<button class="close-btn" on:click={toggleHelp}>×</button>
			<h2>{t('TMT-A Success Strategies')}</h2>

			<div class="strategy">
				<h3>{t('Visual Scanning')}</h3>
				<p>{$locale === 'bn' ? 'একটি বৃত্তে চাপার সময়ই চোখকে পরের সংখ্যাটি খুঁজতে পাঠান।' : 'While clicking one circle, your eyes should already be locating the next number. Train this split-attention technique.'}</p>
			</div>
			<div class="strategy">
				<h3>{t('Center Clicking')}</h3>
				<p>{$locale === 'bn' ? 'প্রতিটি বৃত্তের মাঝামাঝি অংশে চাপুন। কিনারায় চাপলে মিস হতে পারে।' : 'Click near the center of each circle. Peripheral clicks may miss the target and cost you errors.'}</p>
			</div>
			<div class="strategy">
				<h3>{t('Efficient Path')}</h3>
				<p>{$locale === 'bn' ? 'মাউস বা আঙুল সোজা ও মসৃণভাবে চালান।' : 'Move in smooth, direct lines between circles. Erratic movements waste time and energy.'}</p>
			</div>
			<div class="strategy">
				<h3>{t('Pattern Recognition')}</h3>
				<p>{$locale === 'bn' ? 'কাছাকাছি সংখ্যার ছোট গুচ্ছ চিনে নিন।' : 'Identify clusters of sequential numbers near each other. Planning short routes is more efficient.'}</p>
			</div>
			<div class="strategy">
				<h3>{t('Speed vs Accuracy')}</h3>
				<p>{$locale === 'bn' ? 'ভারসাম্য খুঁজুন — ভুল সময় নষ্ট করে।' : 'Find the balance. Rushing leads to errors, which hurt your score more than going slightly slower but accurately.'}</p>
			</div>
			<div class="strategy">
				<h3>{t('Why This Matters')}</h3>
				<p>{$locale === 'bn' ? 'TMT-A মস্তিষ্কের দৃশ্যমান তথ্য প্রক্রিয়া করার গতি মাপে।' : "TMT-A measures how fast your brain processes visual information and coordinates motor responses — critical for driving and navigation."}</p>
			</div>
		</div>
	</div>
{/if}

<style>
	/* ── Container ─────────────────────────────────────────── */
	.tmt-container {
		min-height: 100vh;
		background: #C8DEFA;
		padding: 2rem 1rem;
	}

	.tmt-inner {
		max-width: 960px;
		margin: 0 auto;
	}

	/* ── Instructions card ─────────────────────────────────── */
	.instructions-card {
		background: white;
		border-radius: 16px;
		padding: 2.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07), 0 1px 3px rgba(0, 0, 0, 0.06);
		display: flex;
		flex-direction: column;
		gap: 1.8rem;
	}

	.header-content {
		text-align: center;
	}

	.title-row {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		flex-wrap: wrap;
		margin-bottom: 0.5rem;
	}

	.header-content h1 {
		font-size: 1.8rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0;
	}

	.subtitle {
		color: #64748b;
		font-size: 1rem;
		margin: 0.4rem 0 0.8rem;
	}

	.classic-badge {
		display: inline-block;
		background: rgba(102, 126, 234, 0.12);
		color: #667eea;
		border: 1px solid rgba(102, 126, 234, 0.3);
		border-radius: 20px;
		padding: 0.3rem 1rem;
		font-size: 0.82rem;
		font-weight: 600;
	}

	.practice-note {
		background: #fef9c3;
		border: 1px solid #fde047;
		border-radius: 8px;
		padding: 0.75rem 1rem;
		color: #854d0e;
		font-size: 0.9rem;
		text-align: center;
	}

	/* ── Task concept (blue/indigo for TMT-A) ─────────────── */
	.task-concept {
		background: linear-gradient(135deg, #eff6ff, #dbeafe);
		border: 1px solid #93c5fd;
		border-radius: 12px;
		padding: 1.5rem;
	}

	.task-concept h3 {
		font-size: 1rem;
		font-weight: 700;
		color: #1e40af;
		margin: 0 0 0.6rem;
	}

	.task-concept p {
		color: #1e3a8a;
		margin: 0 0 1.2rem;
		line-height: 1.6;
	}

	.demo-sequence {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.75rem;
		flex-wrap: wrap;
	}

	.demo-circle {
		width: 48px;
		height: 48px;
		border-radius: 50%;
		border: 3px solid #3b82f6;
		background: white;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.2rem;
		font-weight: 700;
		color: #1e40af;
	}

	.demo-circle.first {
		background: #3b82f6;
		color: white;
		border-color: #2563eb;
	}

	.demo-arrow {
		font-size: 1.4rem;
		color: #3b82f6;
		font-weight: 700;
	}

	.demo-dots {
		font-size: 1.2rem;
		color: #3b82f6;
		font-weight: 700;
	}

	/* ── Rules grid ────────────────────────────────────────── */
	.rules-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}

	.rule-card {
		display: flex;
		align-items: flex-start;
		gap: 0.8rem;
		padding: 1rem;
		background: #f8fafc;
		border-radius: 10px;
		border-left: 4px solid #667eea;
	}

	.rule-icon {
		font-size: 1.5rem;
		flex-shrink: 0;
	}

	.rule-text {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.rule-text strong {
		font-size: 0.9rem;
		color: #1e293b;
	}

	.rule-text span {
		font-size: 0.82rem;
		color: #64748b;
		line-height: 1.4;
	}

	/* ── Info grid ─────────────────────────────────────────── */
	.info-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}

	.info-section {
		background: #f8fafc;
		border-radius: 10px;
		padding: 1.2rem;
	}

	.info-section h4 {
		font-size: 0.9rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 0.8rem;
	}

	.tips-list {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.tips-list li {
		font-size: 0.85rem;
		color: #475569;
		line-height: 1.4;
	}

	.structure-list {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.structure-list li {
		display: flex;
		justify-content: space-between;
		align-items: center;
		font-size: 0.85rem;
		padding: 0.3rem 0;
		border-bottom: 1px solid #e2e8f0;
	}

	.structure-list li:last-child {
		border-bottom: none;
	}

	.struct-key {
		color: #64748b;
	}

	.struct-val {
		font-weight: 600;
		color: #1e293b;
	}

	/* ── Clinical info ─────────────────────────────────────── */
	.clinical-info {
		background: linear-gradient(135deg, #f0fdf4, #dcfce7);
		border: 1px solid #bbf7d0;
		border-radius: 12px;
		padding: 1.2rem;
	}

	.clinical-info h4 {
		font-size: 0.9rem;
		font-weight: 700;
		color: #166534;
		margin: 0 0 0.8rem;
	}

	.clinical-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0.75rem;
	}

	.clinical-item {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
	}

	.clinical-item strong {
		font-size: 0.82rem;
		color: #166534;
	}

	.clinical-item span {
		font-size: 0.8rem;
		color: #15803d;
	}

	/* ── Performance guide ─────────────────────────────────── */
	.perf-guide {
		background: #f8fafc;
		border-radius: 12px;
		padding: 1.2rem;
	}

	.perf-guide h4 {
		font-size: 0.9rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 0.8rem;
	}

	.norm-bars {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}

	.norm-bar {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.5rem 0.9rem;
		border-radius: 6px;
		font-size: 0.85rem;
		font-weight: 600;
	}

	.norm-excellent { background: #dcfce7; color: #166534; }
	.norm-good      { background: #d1fae5; color: #065f46; }
	.norm-avg       { background: #fef9c3; color: #854d0e; }
	.norm-fair      { background: #ffedd5; color: #9a3412; }
	.norm-needs     { background: #fee2e2; color: #991b1b; }

	.norm-label { font-weight: 700; }
	.norm-val   { font-weight: 400; font-size: 0.82rem; }

	.norm-note {
		font-size: 0.78rem;
		color: #94a3b8;
		font-style: italic;
		margin: 0.5rem 0 0;
		text-align: center;
	}

	/* ── Button group ──────────────────────────────────────── */
	.button-group {
		display: flex;
		justify-content: center;
		gap: 1rem;
		flex-wrap: wrap;
		padding-top: 0.5rem;
	}

	.start-button {
		background: #4338ca;
		color: white;
		border: none;
		border-radius: 10px;
		padding: 0.85rem 2.5rem;
		font-size: 1rem;
		font-weight: 700;
		cursor: pointer;
		transition: transform 0.15s, box-shadow 0.15s;
		box-shadow: 0 4px 14px rgba(67, 56, 202, 0.35);
	}

	.start-button:hover {
		transform: translateY(-2px);
		box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
	}

	.btn-secondary {
		background: white;
		color: #667eea;
		border: 2px solid #667eea;
		border-radius: 10px;
		padding: 0.85rem 2rem;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.15s;
	}

	.btn-secondary:hover {
		background: rgba(102, 126, 234, 0.08);
	}

	/* ── Screen card (shared ready/testing/complete) ───────── */
	.screen-card {
		background: white;
		border-radius: 16px;
		padding: 2.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
	}

	/* ── Ready screen ──────────────────────────────────────── */
	.ready-screen {
		text-align: center;
	}

	.ready-screen h2 {
		font-size: 1.8rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 0.5rem;
	}

	.ready-message {
		color: #64748b;
		font-size: 1.05rem;
		margin: 0 0 1.5rem;
	}

	.ready-sequence {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		margin: 1.5rem 0;
	}

	.ready-circle {
		width: 64px;
		height: 64px;
		border-radius: 50%;
		border: 3px solid #667eea;
		background: white;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.6rem;
		font-weight: 700;
		color: #1e293b;
		box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
	}

	.ready-arrow {
		font-size: 2rem;
		color: #667eea;
		font-weight: 700;
	}

	.ready-dots {
		font-size: 2rem;
		color: #667eea;
		font-weight: 700;
	}

	.countdown {
		font-size: 4.5rem;
		font-weight: 800;
		color: #667eea;
		margin-top: 1.5rem;
		animation: pulse 1s ease-in-out infinite;
	}

	@keyframes pulse {
		0%, 100% { transform: scale(1); opacity: 1; }
		50% { transform: scale(1.08); opacity: 0.75; }
	}

	/* ── Testing screen ────────────────────────────────────── */
	.testing-screen {
		padding: 1.25rem;
	}

	.test-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		flex-wrap: wrap;
		gap: 0.5rem;
	}

	.test-badges {
		display: flex;
		gap: 0.5rem;
		align-items: center;
		flex-wrap: wrap;
	}

	.next-badge {
		background: linear-gradient(135deg, #fef9c3, #fde047);
		color: #854d0e;
		padding: 0.4rem 0.9rem;
		border-radius: 20px;
		font-size: 0.9rem;
		font-weight: 600;
		animation: pulse 1.5s ease-in-out infinite;
	}

	.next-badge strong {
		font-size: 1.1rem;
		color: #713f12;
	}

	.count-badge {
		background: rgba(102, 126, 234, 0.12);
		color: #667eea;
		padding: 0.4rem 0.9rem;
		border-radius: 20px;
		font-size: 0.85rem;
		font-weight: 600;
	}

	.error-badge {
		background: #fee2e2;
		color: #991b1b;
		padding: 0.4rem 0.9rem;
		border-radius: 20px;
		font-size: 0.85rem;
		font-weight: 600;
	}

	.timer-display {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		background: #f8fafc;
		border: 1px solid #e2e8f0;
		padding: 0.5rem 1rem;
		border-radius: 20px;
	}

	.timer-icon {
		font-size: 1.1rem;
	}

	.timer-value {
		font-size: 1.2rem;
		font-weight: 700;
		color: #16a34a;
		min-width: 56px;
		text-align: center;
	}

	.help-btn-sm {
		width: 36px;
		height: 36px;
		border-radius: 50%;
		border: 2px solid #667eea;
		background: white;
		color: #667eea;
		font-size: 1.1rem;
		font-weight: 700;
		cursor: pointer;
		transition: all 0.2s;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.help-btn-sm:hover {
		background: #667eea;
		color: white;
	}

	.canvas-container {
		background: #f8fafc;
		border-radius: 12px;
		border: 1px solid #e2e8f0;
		padding: 1rem;
		margin: 0.75rem 0;
		display: flex;
		justify-content: center;
		align-items: center;
		min-height: 500px;
	}

	canvas {
		cursor: pointer;
		border-radius: 8px;
	}

	.instruction-bar {
		background: rgba(102, 126, 234, 0.07);
		border: 1px solid rgba(102, 126, 234, 0.15);
		border-radius: 10px;
		padding: 0.75rem 1rem;
		text-align: center;
	}

	.instruction-bar p {
		margin: 0.2rem 0;
		color: #64748b;
		font-size: 0.9rem;
	}

	.current-target {
		font-size: 1rem;
	}

	.current-target strong {
		color: #d97706;
		font-size: 1.3rem;
	}

	/* ── Complete screen ───────────────────────────────────── */
	.complete-screen {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.perf-banner {
		text-align: center;
		padding: 1.5rem;
		background: linear-gradient(135deg, color-mix(in srgb, var(--perf-color) 10%, white), color-mix(in srgb, var(--perf-color) 20%, white));
		border: 2px solid var(--perf-color);
		border-radius: 14px;
	}

	.perf-level {
		font-size: 1.8rem;
		font-weight: 800;
		color: var(--perf-color);
	}

	.perf-subtitle {
		font-size: 0.95rem;
		color: #64748b;
		margin-top: 0.3rem;
	}

	.metrics-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
		gap: 1rem;
	}

	.metric-card {
		background: #f8fafc;
		border: 1px solid #e2e8f0;
		border-radius: 12px;
		padding: 1.2rem;
		text-align: center;
	}

	.metric-card.highlight {
		background: #4338ca;
		color: white;
		border-color: transparent;
	}

	.metric-icon { font-size: 1.8rem; margin-bottom: 0.4rem; }

	.metric-value {
		font-size: 1.8rem;
		font-weight: 800;
		color: #1e293b;
		margin-bottom: 0.2rem;
	}

	.metric-card.highlight .metric-value,
	.metric-card.highlight .metric-label,
	.metric-card.highlight .metric-sub {
		color: white;
	}

	.metric-label {
		font-size: 0.82rem;
		font-weight: 600;
		color: #64748b;
	}

	.metric-sub {
		font-size: 0.78rem;
		color: #94a3b8;
		margin-top: 0.2rem;
	}

	/* ── Breakdown ─────────────────────────────────────────── */
	.breakdown {
		background: #f8fafc;
		border-radius: 12px;
		padding: 1.2rem;
	}

	.breakdown h3 {
		font-size: 0.95rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 0.8rem;
	}

	.breakdown-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.55rem 0;
		border-bottom: 1px solid #e2e8f0;
		font-size: 0.9rem;
	}

	.breakdown-row:last-child { border-bottom: none; }

	.bd-label { color: #64748b; }

	.bd-val { font-weight: 700; color: #667eea; }
	.bd-error { color: #dc2626; }
	.bd-success { color: #16a34a; }

	/* ── Clinical note ─────────────────────────────────────── */
	.clinical-note {
		background: linear-gradient(135deg, #f0fdf4, #dcfce7);
		border: 1px solid #bbf7d0;
		border-radius: 12px;
		padding: 1.2rem;
	}

	.clinical-note h4 {
		font-size: 0.9rem;
		font-weight: 700;
		color: #166534;
		margin: 0 0 0.5rem;
	}

	.clinical-note p {
		font-size: 0.9rem;
		color: #15803d;
		line-height: 1.6;
		margin: 0;
	}

	/* ── Difficulty info ───────────────────────────────────── */
	.difficulty-info {
		background: #eff6ff;
		border: 1px solid #bfdbfe;
		border-radius: 10px;
		padding: 0.9rem 1.2rem;
		display: flex;
		justify-content: space-between;
		align-items: center;
		flex-wrap: wrap;
		gap: 0.5rem;
		font-size: 0.88rem;
		font-weight: 600;
		color: #1e40af;
	}

	.adapt-reason {
		color: #3b82f6;
		font-weight: 400;
		font-style: italic;
	}

	/* ── Help modal ────────────────────────────────────────── */
	.modal-overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.55);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: 1rem;
	}

	.modal-content {
		background: white;
		border-radius: 16px;
		padding: 2rem;
		max-width: 560px;
		width: 100%;
		max-height: 80vh;
		overflow-y: auto;
		position: relative;
		box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
	}

	.close-btn {
		position: absolute;
		top: 1rem;
		right: 1rem;
		width: 36px;
		height: 36px;
		border: none;
		background: #f1f5f9;
		color: #475569;
		font-size: 1.4rem;
		border-radius: 50%;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: background 0.15s;
	}

	.close-btn:hover { background: #e2e8f0; }

	.modal-content h2 {
		font-size: 1.2rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 1.2rem;
		padding-right: 2.5rem;
	}

	.strategy {
		padding: 0.9rem 1rem;
		background: #f8fafc;
		border-radius: 8px;
		border-left: 4px solid #667eea;
		margin-bottom: 0.75rem;
	}

	.strategy h3 {
		font-size: 0.88rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 0.3rem;
	}

	.strategy p {
		font-size: 0.84rem;
		color: #64748b;
		margin: 0;
		line-height: 1.5;
	}

	/* ── Responsive ────────────────────────────────────────── */
	@media (max-width: 640px) {
		.instructions-card { padding: 1.5rem; gap: 1.2rem; }
		.rules-grid { grid-template-columns: 1fr; }
		.info-grid { grid-template-columns: 1fr; }
		.clinical-grid { grid-template-columns: 1fr; }
		.metrics-grid { grid-template-columns: repeat(2, 1fr); }
		.header-content h1 { font-size: 1.4rem; }
		.screen-card { padding: 1.25rem; }
	}
</style>


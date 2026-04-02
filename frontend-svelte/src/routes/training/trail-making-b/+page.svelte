<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
	import {
		formatNumber,
		formatPercent,
		locale,
		localizeStimulusSymbol,
		translateText
	} from '$lib/i18n';
	import { user } from '$lib/stores';
	import { getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
	import { onMount } from 'svelte';

	const API_BASE_URL = 'http://127.0.0.1:8000';

	let currentUser = null;
	let loading = true;
	let sessionData = null;
	let difficulty = 1;
	let phase = 'intro'; // intro, instructions, practice, test, results
	let metrics = null;
	let newBadges = [];
	let taskId = null;

	// Canvas state
	let canvas;
	let ctx;
	let circles = [];
	let userSequence = [];
	let currentIndex = 0;
	let errors = [];
	let startTime = 0;
	let completionTime = 0;
	let elapsedTime = 0; // Reactive elapsed time variable
	let timerInterval = null; // Timer interval reference
	let hoveredCircle = null;
	let completed = false;

	// Line drawing
	let connections = [];

	// Practice mode
	let practiceCircles = [];
	let practiceSequence = ['1', 'A', '2', 'B', '3'];
	let practiceIndex = 0;
	let practiceFeedback = null;
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';

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

	function marker(value) {
		return localizeStimulusSymbol(value, $locale);
	}

	function secondsLabel(value, options = {}) {
		const formatted = n(value, {
			minimumFractionDigits: 1,
			maximumFractionDigits: 1,
			...options
		});
		return $locale === 'bn' ? `${formatted} সেকেন্ড` : `${formatted}s`;
	}

	function levelLabel(value = difficulty) {
		return $locale === 'bn' ? `লেভেল ${n(value)}` : `Level ${value}`;
	}

	function sequencePreview(values = practiceSequence) {
		return values.map((value) => marker(value)).join(' → ');
	}

	function difficultyChangeLabel(before, after) {
		return $locale === 'bn'
			? `কঠিনতা: ${n(before)} → ${n(after)}`
			: `Difficulty: ${before} → ${after}`;
	}

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
			const response = await fetch(`${API_BASE_URL}/api/training/tasks/trail-making-b/generate/${currentUser.id}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' }
			});

			if (!response.ok) {
				throw new Error('Failed to load session');
			}

			const data = await response.json();
			sessionData = data.session_data;
			difficulty = data.difficulty;
			circles = [...sessionData.circles];
			loading = false;
		} catch (error) {
			console.error('Error loading session:', error);
			alert(t('Failed to load training session. Please ensure backend is running and baseline is completed.'));
			loading = false;
		}
	}

	function startInstructions() {
		phase = 'instructions';
	}

	function startPractice() {
		playMode = TASK_PLAY_MODE.PRACTICE;
		practiceStatusMessage = '';
		phase = 'practice';
		setupPracticeCanvas();
	}

	function finishPractice() {
		playMode = TASK_PLAY_MODE.RECORDED;
		practiceFeedback = null;
		practiceIndex = 0;
		phase = 'instructions';
		practiceStatusMessage = getPracticeCopy($locale).complete;
	}

	function setupPracticeCanvas() {
		// Simple practice: 5 circles in easy positions
		practiceCircles = [
			{ id: 'p0', label: '1', x: 150, y: 100, sequence_index: 0 },
			{ id: 'p1', label: 'A', x: 350, y: 150, sequence_index: 1 },
			{ id: 'p2', label: '2', x: 550, y: 100, sequence_index: 2 },
			{ id: 'p3', label: 'B', x: 350, y: 300, sequence_index: 3 },
			{ id: 'p4', label: '3', x: 150, y: 250, sequence_index: 4 }
		];
		
		practiceIndex = 0;
		practiceFeedback = null;
		
		setTimeout(() => {
			if (canvas) {
				ctx = canvas.getContext('2d');
				drawPracticeCanvas();
			}
		}, 100);
	}

	function drawPracticeCanvas() {
		if (!ctx || !canvas) return;

		ctx.clearRect(0, 0, canvas.width, canvas.height);

		// Draw circles
		practiceCircles.forEach((circle, idx) => {
			const isCompleted = idx < practiceIndex;
			const isLastClicked = idx === practiceIndex - 1; // Most recently clicked

			ctx.beginPath();
			ctx.arc(circle.x, circle.y, 30, 0, Math.PI * 2);
			
			// Yellow for last clicked, green for earlier completed, white for unclicked
			if (isLastClicked) {
				ctx.fillStyle = '#fbbf24'; // Yellow for current/last clicked
				ctx.strokeStyle = '#f59e0b';
			} else if (isCompleted) {
				ctx.fillStyle = '#4ade80'; // Green for earlier completed
				ctx.strokeStyle = '#22c55e';
			} else {
				ctx.fillStyle = 'white'; // White for unclicked
				ctx.strokeStyle = '#3b82f6';
			}
			
			ctx.lineWidth = 3;
			ctx.fill();
			ctx.stroke();

			// Label - White on completed, dark on unclicked
			ctx.fillStyle = (isCompleted || isLastClicked) ? 'white' : '#1e293b';
			ctx.font = 'bold 20px Arial';
			ctx.textAlign = 'center';
			ctx.textBaseline = 'middle';
			ctx.fillText(marker(circle.label), circle.x, circle.y);
		});

		// Draw connections - only between already clicked circles
		ctx.strokeStyle = '#3b82f6';
		ctx.lineWidth = 2;
		for (let i = 0; i < practiceIndex - 1; i++) {
			ctx.beginPath();
			ctx.moveTo(practiceCircles[i].x, practiceCircles[i].y);
			ctx.lineTo(practiceCircles[i + 1].x, practiceCircles[i + 1].y);
			ctx.stroke();
		}
	}

	function handlePracticeClick(event) {
		if (practiceIndex >= practiceCircles.length) return;

		const rect = canvas.getBoundingClientRect();
		const x = event.clientX - rect.left;
		const y = event.clientY - rect.top;

		// Check which circle was clicked
		const clicked = practiceCircles.find(c => {
			const dist = Math.sqrt((c.x - x) ** 2 + (c.y - y) ** 2);
			return dist < 30;
		});

		if (clicked) {
			const expected = practiceCircles[practiceIndex];
			
			if (clicked.id === expected.id) {
				// Correct!
				practiceIndex++;
				practiceFeedback = {
					type: 'success',
					message: $locale === 'bn'
						? `✓ সঠিক! পরেরটি: ${practiceIndex < practiceCircles.length ? marker(practiceSequence[practiceIndex]) : 'সব সম্পন্ন!'}`
						: `✓ Correct! Next: ${practiceIndex < practiceCircles.length ? practiceSequence[practiceIndex] : 'All done!'}`
				};
				
				drawPracticeCanvas();
				
				if (practiceIndex >= practiceCircles.length) {
					setTimeout(() => {
						finishPractice();
					}, 1500);
				}
			} else {
				practiceFeedback = {
					type: 'error',
					message: $locale === 'bn'
						? `✗ ভুল! আপনি "${marker(clicked.label)}" ক্লিক করেছেন, কিন্তু "${marker(expected.label)}" ক্লিক করা উচিত ছিল`
						: `✗ Wrong! You clicked "${clicked.label}" but should click "${expected.label}"`
				};
			}
		}
	}

	function startTest() {
		playMode = TASK_PLAY_MODE.RECORDED;
		practiceStatusMessage = '';
		phase = 'test';
		currentIndex = 0;
		userSequence = [];
		connections = [];
		errors = [];
		completed = false;
		startTime = Date.now();
		elapsedTime = 0;

		// Start timer to update elapsed time
		timerInterval = setInterval(() => {
			elapsedTime = (Date.now() - startTime) / 1000;
		}, 100); // Update every 100ms for smooth display

		setTimeout(() => {
			if (canvas) {
				ctx = canvas.getContext('2d');
				drawCanvas();
			}
		}, 100);
	}

	function drawCanvas() {
		if (!ctx || !canvas) return;

		ctx.clearRect(0, 0, canvas.width, canvas.height);

		// Draw all connections first (lines behind circles)
		ctx.strokeStyle = '#3b82f6';
		ctx.lineWidth = 2;
		connections.forEach(conn => {
			ctx.beginPath();
			ctx.moveTo(conn.fromX, conn.fromY);
			ctx.lineTo(conn.toX, conn.toY);
			ctx.stroke();
		});

		// Draw circles
		circles.forEach(circle => {
			const isCompleted = !circle.is_distractor && circle.sequence_index < currentIndex;
			const isLastClicked = !circle.is_distractor && circle.sequence_index === currentIndex - 1; // Most recently clicked
			const isHovered = hoveredCircle === circle.id;

			ctx.beginPath();
			ctx.arc(circle.x, circle.y, getCircleRadius(), 0, Math.PI * 2);
			
			// Highlight last clicked circle in yellow, earlier ones in green
			if (isLastClicked) {
				ctx.fillStyle = '#fbbf24'; // Yellow for most recent click
				ctx.strokeStyle = '#f59e0b';
			} else if (isCompleted) {
				ctx.fillStyle = '#4ade80'; // Green for earlier completed
				ctx.strokeStyle = '#22c55e';
			} else if (isHovered) {
				ctx.fillStyle = '#e0f2fe'; // Light blue on hover
				ctx.strokeStyle = '#0ea5e9';
			} else if (circle.is_distractor) {
				ctx.fillStyle = '#f1f5f9'; // Gray for distractors
				ctx.strokeStyle = '#cbd5e1';
			} else {
				ctx.fillStyle = 'white'; // White for unclicked targets
				ctx.strokeStyle = '#3b82f6';
			}
			
			ctx.lineWidth = isLastClicked ? 4 : 2;
			ctx.fill();
			ctx.stroke();

			// Label - White on completed/last clicked, dark on others
			ctx.fillStyle = (isCompleted || isLastClicked) ? 'white' : circle.is_distractor ? '#94a3b8' : '#1e293b';
			ctx.font = `bold ${getFontSize()}px Arial`;
			ctx.textAlign = 'center';
			ctx.textBaseline = 'middle';
			ctx.fillText(marker(circle.label), circle.x, circle.y);
		});
	}

	function getCircleRadius() {
		const sizeMap = {
			'large': 35,
			'medium': 30,
			'small': 25,
			'extra-small': 20
		};
		return sizeMap[sessionData?.circle_size] || 30;
	}

	function getFontSize() {
		const sizeMap = {
			'large': 20,
			'medium': 18,
			'small': 16,
			'extra-small': 14
		};
		return sizeMap[sessionData?.circle_size] || 18;
	}

	function handleCanvasClick(event) {
		if (completed) return;

		const rect = canvas.getBoundingClientRect();
		const x = event.clientX - rect.left;
		const y = event.clientY - rect.top;

		// Find clicked circle
		const radius = getCircleRadius();
		const clicked = circles.find(c => {
			const dist = Math.sqrt((c.x - x) ** 2 + (c.y - y) ** 2);
			return dist < radius;
		});

		if (clicked) {
			handleCircleClick(clicked);
		}
	}

	function handleCircleClick(circle) {
		const expectedLabel = sessionData.correct_sequence[currentIndex];
		
		// Check if this is the correct next circle
		if (circle.label === expectedLabel && !circle.is_distractor) {
			// Correct click
			userSequence.push(circle.id);
			
			// Draw connection from previous circle
			if (currentIndex > 0) {
				const prevCircle = circles.find(c => c.sequence_index === currentIndex - 1);
				if (prevCircle) {
					connections.push({
						fromX: prevCircle.x,
						fromY: prevCircle.y,
						toX: circle.x,
						toY: circle.y
					});
				}
			}
			
			currentIndex++;
			
			// Check if completed
			if (currentIndex >= sessionData.correct_sequence.length) {
				completeSession();
			}
			
			drawCanvas();
		} else {
			// Wrong click - log error
			const errorType = circle.is_distractor ? 'distractor_clicked' : 'sequence_error';
			
			// Check if it's a perseverative error (clicking previous item again)
			const isPerseverative = currentIndex > 0 && 
				circle.label === sessionData.correct_sequence[currentIndex - 1];
			
			errors.push({
				sequence_index: currentIndex,
				clicked_label: circle.label,
				expected_label: expectedLabel,
				type: isPerseverative ? 'perseverative_error' : errorType,
				timestamp: Date.now() - startTime
			});
			
			// Visual feedback for error (briefly flash red)
			const originalFill = ctx.fillStyle;
			ctx.beginPath();
			ctx.arc(circle.x, circle.y, getCircleRadius(), 0, Math.PI * 2);
			ctx.fillStyle = '#ef4444';
			ctx.fill();
			ctx.strokeStyle = '#dc2626';
			ctx.stroke();
			
			setTimeout(() => {
				drawCanvas();
			}, 200);
		}
	}

	function handleCanvasMove(event) {
		const rect = canvas.getBoundingClientRect();
		const x = event.clientX - rect.left;
		const y = event.clientY - rect.top;

		const radius = getCircleRadius();
		const hovered = circles.find(c => {
			const dist = Math.sqrt((c.x - x) ** 2 + (c.y - y) ** 2);
			return dist < radius;
		});

		if (hovered?.id !== hoveredCircle) {
			hoveredCircle = hovered?.id || null;
			drawCanvas();
		}
	}

	async function completeSession() {
		completed = true;
		completionTime = (Date.now() - startTime) / 1000; // Convert to seconds
		taskId = $page.url.searchParams.get('taskId');

		try {
			const response = await fetch(`${API_BASE_URL}/api/training/tasks/trail-making-b/submit/${currentUser.id}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					difficulty,
					session_data: sessionData,
					user_sequence: userSequence,
					completion_time_seconds: completionTime,
					errors: errors,
					completed: true,
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
			alert(t('Failed to submit results. Please try again.'));
		}
	}

	function returnToDashboard() {
		goto('/dashboard');
	}

	// Reactive performance badge color
	$: performanceBadgeColor = metrics?.performance_level === 'Excellent' ? 'excellent' :
		metrics?.performance_level === 'Good' ? 'good' :
		metrics?.performance_level === 'Fair' ? 'fair' : 'needs-improvement';
</script>

<svelte:head>
	<title>{t('Trail Making Test - Part B')} | NeuroBloom</title>
</svelte:head>

<svelte:window on:keydown={(e) => e.key === 'Escape' && phase !== 'results' && returnToDashboard()} />

<div class="tmt-b-container">
	{#if loading}
		<div class="loading-state">
			<div class="spinner"></div>
			<p>{t('Loading Trail Making Test - Part B...')}</p>
		</div>

	{:else if phase === 'intro'}
		<!-- Introduction Screen -->
		<div class="intro-container">
			<div class="intro-header">
				<div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap;">
					<h1>{t('Trail Making Test - Part B')}</h1>
					<DifficultyBadge {difficulty} domain="Cognitive Flexibility" />
				</div>
				<div class="classic-badge">{t('Executive Function & Cognitive Flexibility Test')}</div>
			</div>

			<div class="intro-content">
				<div class="info-section">
					<h2>{t('About This Test')}</h2>
					<p>
						{$locale === 'bn'
							? 'Trail Making Test - Part B একটি সুপরিচিত নিউরোসাইকোলজিক্যাল পরীক্ষা, যা কগনিটিভ ফ্লেক্সিবিলিটি, সেট-শিফটিং ও বিভক্ত মনোযোগ মূল্যায়ন করে।'
							: 'The Trail Making Test - Part B is a gold standard neuropsychological test that measures cognitive flexibility, set-shifting, and divided attention.'}
					</p>
					<p>
						{$locale === 'bn'
							? 'এক্সিকিউটিভ ফাংশন মূল্যায়নের জন্য এটি ক্লিনিক্যাল চর্চা ও গবেষণায়, বিশেষ করে এমএস রোগীদের ক্ষেত্রে, বহুল ব্যবহৃত।'
							: 'This test is widely used in clinical practice and research to assess executive function, particularly in Multiple Sclerosis (MS) patients.'}
					</p>
				</div>

				<div class="info-section">
					<h2>{t("What You'll Do")}</h2>
					<ul class="task-steps">
						<li>{$locale === 'bn' ? `ক্রম বদলিয়ে বৃত্ত যুক্ত করুন: ${sequencePreview(['1', 'A', '2', 'B', '3', 'C'])}...` : 'Connect circles in alternating order: 1 → A → 2 → B → 3 → C...'}</li>
						<li>{t('Click each circle in the correct sequence')}</li>
						<li>{t('Work as quickly as possible while staying accurate')}</li>
						<li>{t('Complete before the time limit')}</li>
					</ul>
				</div>

				<div class="info-section highlight-box">
					<h2>🧠 What This Measures</h2>
					<div class="measures-grid">
						<div class="measure-item">
							<span class="measure-icon">🔄</span>
							<span>Set-Shifting</span>
						</div>
						<div class="measure-item">
							<span class="measure-icon">⚡</span>
							<span>Mental Flexibility</span>
						</div>
						<div class="measure-item">
							<span class="measure-icon">👁️</span>
							<span>Divided Attention</span>
						</div>
						<div class="measure-item">
							<span class="measure-icon">🎯</span>
							<span>Task Switching</span>
						</div>
					</div>
				</div>

				<div class="difficulty-info">
					<span class="difficulty-label">{t('Current Level:')}</span>
					<span class="difficulty-value">{levelLabel()}</span>
					<span class="items-info">
						{n(sessionData.total_items)} {t('items')} • 
						{$locale === 'bn'
							? `${n(sessionData.time_limit_seconds / 60)} মিনিটের সীমা`
							: `${sessionData.time_limit_seconds / 60} minute${sessionData.time_limit_seconds > 60 ? 's' : ''} limit`}
					</span>
				</div>
			</div>

			<div class="intro-actions">
				<button class="btn btn-secondary" on:click={returnToDashboard}>← {t('Back to Dashboard')}</button>
				<button class="btn btn-primary" on:click={startInstructions}>{t('Continue to Instructions')} →</button>
			</div>
		</div>

	{:else if phase === 'instructions'}
		<!-- Instructions Screen -->
		<div class="instructions-container">
			<h2>{t('How to Complete the Trail Making Test - Part B')}</h2>

			<div class="instruction-steps">
				<div class="step-card">
					<div class="step-number">1</div>
					<div class="step-content">
						<h3>{t('Alternating Pattern')}</h3>
						<p>{t('Connect numbers and letters in alternating order:')}</p>
						<div class="sequence-example">
							<span class="seq-item">{marker('1')}</span>
							<span class="arrow">→</span>
							<span class="seq-item">{marker('A')}</span>
							<span class="arrow">→</span>
							<span class="seq-item">{marker('2')}</span>
							<span class="arrow">→</span>
							<span class="seq-item">{marker('B')}</span>
							<span class="arrow">→</span>
							<span class="seq-item">{marker('3')}</span>
							<span class="arrow">→</span>
							<span class="seq-item">{marker('C')}</span>
						</div>
						<p class="tip">{t('Always alternate: number → letter → number → letter')}</p>
					</div>
				</div>

				<div class="step-card">
					<div class="step-number">2</div>
					<div class="step-content">
						<h3>{t('Click in Sequence')}</h3>
						<p>{t('Click circles one at a time in the correct order. A line will connect them as you go.')}</p>
						<p class="tip">{t('Your most recent click will be highlighted in yellow to show progress')}</p>
					</div>
				</div>

				<div class="step-card">
					<div class="step-number">3</div>
					<div class="step-content">
						<h3>{t('Speed & Accuracy')}</h3>
						<p>{$locale === 'bn' ? 'যত দ্রুত সম্ভব কাজ করুন, তবে নির্ভুলতাও বজায় রাখুন।' : 'Work as quickly as possible while staying accurate.'}</p>
						<p>{t('If you make a mistake, the circle will briefly flash red - keep going!')}</p>
					</div>
				</div>

				<div class="step-card warning">
					<div class="step-number">!</div>
					<div class="step-content">
						<h3>{t('Watch Out for Distractors')}</h3>
						<p>{t('Some circles may contain numbers or letters NOT in the sequence.')}</p>
						<p class="tip">{t('Only click circles that belong in the alternating pattern')}</p>
					</div>
				</div>
			</div>

			<div class="instructions-actions">
				<button class="btn btn-secondary" on:click={() => phase = 'intro'}>
					← {t('Back')}
				</button>
				<button class="btn btn-primary" on:click={startPractice}>
					{t('Start Practice Round')} →
				</button>
			</div>
		</div>

			<TaskPracticeActions
				locale={$locale}
				startLabel={t('Start Actual Test')}
				practiceVisible={false}
				statusMessage={practiceStatusMessage}
				align="center"
				on:start={startTest}
			/>
	{:else if phase === 'practice'}
		<!-- Practice Round -->
		<div class="practice-container">
			<PracticeModeBanner locale={$locale} />
			<h2>{t('Practice Round')}</h2>
			<p class="practice-subtitle">{t('Connect:')} {sequencePreview()}</p>

			<div class="canvas-wrapper">
				<canvas
					bind:this={canvas}
					width="800"
					height="400"
					on:click={handlePracticeClick}
					class="test-canvas"
				></canvas>
			</div>

			{#if practiceFeedback}
				<div class="feedback-box {practiceFeedback.type}">
					{practiceFeedback.message}
				</div>
			{/if}

			<div class="practice-hint">
				{t('Click the circles in order:')} {sequencePreview()}
			</div>
		</div>

	{:else if phase === 'test'}
		<!-- Main Test -->
		<div class="test-container">
			<div class="test-header">
				<h2>{t('Trail Making Test - Part B')}</h2>
				<div class="header-info">
					<div class="progress-info">
						<span class="progress-text">
							{t('Progress:')} {n(currentIndex)}/{n(sessionData.correct_sequence.length)}
						</span>
					</div>
					<div class="timer-display">
						<span class="timer-icon">⏱️</span>
						<span class="timer-value">{secondsLabel(elapsedTime)}</span>
					</div>
				</div>
			</div>

			<div class="canvas-wrapper">
				<canvas
					bind:this={canvas}
					width="800"
					height="600"
					on:click={handleCanvasClick}
					on:mousemove={handleCanvasMove}
					class="test-canvas"
				></canvas>
			</div>

			<div class="test-instructions">
				{t('Connect in order:')} {sequencePreview(['1', 'A', '2', 'B', '3', 'C'])}... | {t('Click circles to connect')}
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
				<h2>{t('Trail Making Test - Part B Complete!')}</h2>
				<div class="performance-badge {performanceBadgeColor}">
					{t(metrics.performance_level)}
				</div>
			</div>

			<!-- Key Metrics Grid -->
			<div class="metrics-grid">
				<!-- Completion Time -->
				<div class="metric-card time-card">
					<div class="metric-label">{t('Completion Time')}</div>
					<div class="metric-value">{secondsLabel(metrics?.completion_time_seconds || 0)}</div>
					<div class="metric-detail">
						{metrics?.completed ? t('Finished') : t('Incomplete')}
					</div>
				</div>

				<!-- Accuracy -->
				<div class="metric-card accuracy-card">
					<div class="metric-label">{t('Accuracy')}</div>
					<div class="metric-value">{pct(metrics?.accuracy || 0)}</div>
					<div class="metric-detail">
						{n(metrics?.items_completed || 0)}/{n(metrics?.total_items || 0)} {t('correct')}
					</div>
				</div>

				<!-- Total Errors -->
				<div class="metric-card error-card">
					<div class="metric-label">{t('Total Errors')}</div>
					<div class="metric-value">{n(metrics?.total_errors || 0)}</div>
					<div class="metric-detail">
						{n(metrics?.sequence_errors || 0)} {t('sequence')} • 
						{n(metrics?.perseverative_errors || 0)} {t('perseverative')}
					</div>
				</div>

				<!-- B-A Score (if available) -->
				{#if metrics?.b_a_score !== null}
					<div class="metric-card ba-score-card">
						<div class="metric-label">{t('B-A Score')}</div>
						<div class="metric-value">{secondsLabel(metrics?.b_a_score || 0)}</div>
						<div class="metric-detail">{t('Part B - Part A time')}</div>
					</div>
				{/if}
			</div>

			<!-- Clinical Interpretation -->
			<div class="interpretation-section">
				<h3>{t('Performance Analysis')}</h3>
				<p class="interpretation-text">{metrics?.interpretation || ''}</p>
				
				{#if metrics?.clinical_note}
					<div class="clinical-note">
						<strong>{t('Clinical Note:')}</strong> {t(metrics.clinical_note)}
					</div>
				{/if}
			</div>

			<!-- Performance Details -->
			<div class="details-section">
				<h3>{t('Detailed Breakdown')}</h3>
				
				<div class="detail-grid">
					<div class="detail-item">
						<span class="detail-label">{t('Percentile Rank:')}</span>
						<span class="detail-value">{$locale === 'bn' ? `${n(metrics?.percentile || 0)}তম` : `${metrics?.percentile || 0}th`}</span>
					</div>
					<div class="detail-item">
						<span class="detail-label">{t('Adjusted Time:')}</span>
						<span class="detail-value">{secondsLabel(metrics?.adjusted_time_seconds || 0)}</span>
					</div>
					<div class="detail-item">
						<span class="detail-label">{t('Items Completed:')}</span>
						<span class="detail-value">{n(metrics?.items_completed || 0)}/{n(metrics?.total_items || 0)}</span>
					</div>
					<div class="detail-item">
						<span class="detail-label">{t('Difficulty Level:')}</span>
						<span class="detail-value">{levelLabel(metrics?.difficulty || 1)}</span>
					</div>
				</div>
			</div>

			<!-- Error Analysis (if errors occurred) -->
			{#if metrics?.total_errors > 0}
				<div class="errors-section">
					<h3>{t('Error Analysis')}</h3>
					<div class="error-breakdown">
						<div class="error-stat">
							<span class="error-count">{metrics?.sequence_errors || 0}</span>
							<span class="error-type">{t('Sequence Errors')}</span>
							<span class="error-desc">{t('Wrong circle clicked')}</span>
						</div>
						<div class="error-stat">
							<span class="error-count">{metrics?.perseverative_errors || 0}</span>
							<span class="error-type">{t('Perseverative Errors')}</span>
							<span class="error-desc">{t('Clicked previous circle again')}</span>
						</div>
					</div>
					<p class="error-tip">
						{t('Tip: Focus on the alternating pattern (number-letter-number-letter) and take your time to verify before clicking.')}
					</p>
				</div>
			{/if}

			<div class="results-actions">
				<button class="btn btn-secondary" on:click={returnToDashboard}>
					← {t('Back to Dashboard')}
				</button>
			</div>
		</div>
	{/if}
</div>

<style>
	.tmt-b-container {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem;
		min-height: 100vh;
	}

	/* Loading State */
	.loading-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 60vh;
		gap: 1.5rem;
	}

	.spinner {
		width: 50px;
		height: 50px;
		border: 4px solid #e2e8f0;
		border-top-color: #3b82f6;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	/* Intro Screen */
	.intro-container {
		max-width: 900px;
		margin: 0 auto;
	}

	.intro-header {
		text-align: center;
		margin-bottom: 3rem;
	}

	.intro-header h1 {
		font-size: 2.5rem;
		color: #1e293b;
		margin-bottom: 1rem;
	}

	.classic-badge {
		display: inline-block;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		padding: 0.5rem 1.5rem;
		border-radius: 2rem;
		font-size: 0.9rem;
		font-weight: 600;
	}

	.intro-content {
		display: flex;
		flex-direction: column;
		gap: 2rem;
	}

	.info-section {
		background: white;
		padding: 2rem;
		border-radius: 1rem;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	}

	.info-section h2 {
		color: #1e293b;
		margin-bottom: 1rem;
		font-size: 1.3rem;
	}

	.info-section p {
		color: #475569;
		line-height: 1.6;
		margin-bottom: 0.75rem;
	}

	.task-steps {
		list-style: none;
		padding: 0;
	}

	.task-steps li {
		padding: 0.75rem 0;
		padding-left: 2rem;
		position: relative;
		color: #475569;
	}

	.task-steps li::before {
		content: "→";
		position: absolute;
		left: 0;
		color: #3b82f6;
		font-weight: bold;
		font-size: 1.2rem;
	}

	.highlight-box {
		background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
		border: 2px solid #3b82f6;
	}

	.measures-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 1rem;
		margin-top: 1rem;
	}

	.measure-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 1rem;
		background: white;
		border-radius: 0.5rem;
		font-weight: 500;
		color: #1e293b;
	}

	.measure-icon {
		font-size: 1.5rem;
	}

	.difficulty-info {
		text-align: center;
		padding: 1.5rem;
		background: #f8fafc;
		border-radius: 0.75rem;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		flex-wrap: wrap;
	}

	.difficulty-label {
		color: #64748b;
		font-weight: 500;
	}

	.difficulty-value {
		background: #3b82f6;
		color: white;
		padding: 0.5rem 1rem;
		border-radius: 0.5rem;
		font-weight: 600;
	}

	.items-info {
		color: #64748b;
		font-size: 0.9rem;
	}

	.intro-actions {
		display: flex;
		gap: 1rem;
		justify-content: center;
		margin-top: 3rem;
	}

	/* Instructions Screen */
	.instructions-container {
		max-width: 900px;
		margin: 0 auto;
	}

	.instructions-container h2 {
		text-align: center;
		color: #1e293b;
		margin-bottom: 2rem;
		font-size: 2rem;
	}

	.instruction-steps {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
		margin-bottom: 3rem;
	}

	.step-card {
		background: white;
		padding: 2rem;
		border-radius: 1rem;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
		display: flex;
		gap: 1.5rem;
		align-items: flex-start;
	}

	.step-card.warning {
		background: #fef3c7;
		border: 2px solid #f59e0b;
	}

	.step-number {
		background: #3b82f6;
		color: white;
		width: 40px;
		height: 40px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: bold;
		font-size: 1.2rem;
		flex-shrink: 0;
	}

	.step-card.warning .step-number {
		background: #f59e0b;
	}

	.step-content h3 {
		color: #1e293b;
		margin-bottom: 0.75rem;
	}

	.step-content p {
		color: #475569;
		line-height: 1.6;
		margin-bottom: 0.5rem;
	}

	.sequence-example {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin: 1rem 0;
		padding: 1rem;
		background: #f8fafc;
		border-radius: 0.5rem;
		justify-content: center;
	}

	.seq-item {
		width: 50px;
		height: 50px;
		border-radius: 50%;
		background: white;
		border: 3px solid #3b82f6;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: bold;
		font-size: 1.2rem;
		color: #1e293b;
	}

	.arrow {
		color: #3b82f6;
		font-size: 1.5rem;
		font-weight: bold;
	}

	.tip {
		background: #e0f2fe;
		padding: 0.75rem;
		border-radius: 0.5rem;
		color: #0369a1;
		font-weight: 500;
		font-size: 0.9rem;
		margin-top: 0.5rem;
	}

	.instructions-actions {
		display: flex;
		gap: 1rem;
		justify-content: center;
	}

	/* Practice & Test Canvas */
	.practice-container, .test-container {
		max-width: 900px;
		margin: 0 auto;
	}

	.practice-container h2, .test-container h2 {
		text-align: center;
		color: #1e293b;
		margin-bottom: 1rem;
	}

	.practice-subtitle {
		text-align: center;
		color: #64748b;
		font-size: 1.1rem;
		margin-bottom: 2rem;
	}

	.test-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
		flex-wrap: wrap;
		gap: 1rem;
	}

	.progress-info {
		display: flex;
		gap: 2rem;
		align-items: center;
	}

	.progress-text {
		display: inline-block;
		background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
		color: white;
		padding: 0.75rem 1.5rem;
		border-radius: 2rem;
		font-weight: 700;
		font-size: 1.1rem;
		box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
	}

	.timer-display {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		background: linear-gradient(135deg, #10b981 0%, #059669 100%);
		padding: 0.75rem 1.5rem;
		border-radius: 2rem;
		box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
	}

	.timer-icon {
		font-size: 1.5rem;
		line-height: 1;
	}

	.timer-value {
		font-size: 1.25rem;
		font-weight: 700;
		color: white;
		font-variant-numeric: tabular-nums;
		min-width: 60px;
		text-align: center;
		line-height: 1;
	}

	.next-hint {
		color: #1e293b;
	}

	.canvas-wrapper {
		background: white;
		border-radius: 1rem;
		padding: 2rem;
		box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
		margin-bottom: 1.5rem;
		display: flex;
		justify-content: center;
	}

	.test-canvas {
		border: 2px solid #e2e8f0;
		border-radius: 0.5rem;
		cursor: pointer;
	}

	.feedback-box {
		padding: 1rem;
		border-radius: 0.5rem;
		text-align: center;
		font-weight: 500;
		margin-bottom: 1rem;
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

	.practice-hint, .test-instructions {
		text-align: center;
		color: #64748b;
		font-size: 0.95rem;
		padding: 1rem;
		background: #f8fafc;
		border-radius: 0.5rem;
	}

	/* Results Screen */
	.results-container {
		max-width: 1000px;
		margin: 0 auto;
	}

	.results-header {
		text-align: center;
		margin-bottom: 3rem;
	}

	.results-header h2 {
		color: #1e293b;
		font-size: 2.25rem;
		margin-bottom: 1rem;
	}

	.performance-badge {
		display: inline-block;
		padding: 0.75rem 2rem;
		border-radius: 2rem;
		font-weight: 700;
		font-size: 1.25rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.performance-badge.excellent {
		background: linear-gradient(135deg, #10b981, #059669);
		color: white;
	}

	.performance-badge.good {
		background: linear-gradient(135deg, #3b82f6, #2563eb);
		color: white;
	}

	.performance-badge.fair {
		background: linear-gradient(135deg, #f59e0b, #d97706);
		color: white;
	}

	.performance-badge.needs-improvement {
		background: linear-gradient(135deg, #ef4444, #dc2626);
		color: white;
	}

	.metrics-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1.5rem;
		margin-bottom: 3rem;
	}

	.metric-card {
		background: white;
		padding: 1.5rem;
		border-radius: 1rem;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
		text-align: center;
		border-top: 4px solid;
	}

	.time-card {
		border-top-color: #3b82f6;
	}

	.accuracy-card {
		border-top-color: #10b981;
	}

	.error-card {
		border-top-color: #ef4444;
	}

	.ba-score-card {
		border-top-color: #8b5cf6;
	}

	.metric-label {
		color: #64748b;
		font-size: 0.875rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-bottom: 0.5rem;
	}

	.metric-value {
		font-size: 2.5rem;
		font-weight: 700;
		color: #1e293b;
		margin-bottom: 0.25rem;
	}

	.metric-detail {
		color: #64748b;
		font-size: 0.875rem;
	}

	.interpretation-section, .details-section, .errors-section {
		background: white;
		padding: 2rem;
		border-radius: 1rem;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
		margin-bottom: 2rem;
	}

	.interpretation-section h3, .details-section h3, .errors-section h3 {
		color: #1e293b;
		margin-bottom: 1rem;
	}

	.interpretation-text {
		color: #475569;
		line-height: 1.8;
		font-size: 1.05rem;
	}

	.clinical-note {
		margin-top: 1rem;
		padding: 1rem;
		background: #f0f9ff;
		border-left: 4px solid #3b82f6;
		border-radius: 0.5rem;
		color: #1e40af;
	}

	.detail-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
	}

	.detail-item {
		display: flex;
		justify-content: space-between;
		padding: 0.75rem;
		background: #f8fafc;
		border-radius: 0.5rem;
	}

	.detail-label {
		color: #64748b;
		font-weight: 500;
	}

	.detail-value {
		color: #1e293b;
		font-weight: 600;
	}

	.error-breakdown {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1.5rem;
		margin-bottom: 1rem;
	}

	.error-stat {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 1.5rem;
		background: #fef2f2;
		border-radius: 0.75rem;
	}

	.error-count {
		font-size: 2rem;
		font-weight: 700;
		color: #dc2626;
		margin-bottom: 0.5rem;
	}

	.error-type {
		font-weight: 600;
		color: #1e293b;
		margin-bottom: 0.25rem;
	}

	.error-desc {
		font-size: 0.875rem;
		color: #64748b;
	}

	.error-tip {
		background: #e0f2fe;
		padding: 1rem;
		border-radius: 0.5rem;
		color: #0369a1;
		margin-top: 1rem;
	}

	.results-actions {
		display: flex;
		justify-content: center;
		margin-top: 3rem;
	}

	/* Buttons */
	.btn {
		padding: 0.875rem 2rem;
		border-radius: 0.75rem;
		font-weight: 600;
		font-size: 1rem;
		cursor: pointer;
		border: none;
		transition: all 0.2s;
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
	}

	.btn-primary {
		background: linear-gradient(135deg, #3b82f6, #2563eb);
		color: white;
	}

	.btn-primary:hover {
		background: linear-gradient(135deg, #2563eb, #1d4ed8);
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
	}

	.btn-secondary {
		background: white;
		color: #475569;
		border: 2px solid #e2e8f0;
	}

	.btn-secondary:hover {
		background: #f8fafc;
		border-color: #cbd5e1;
	}

	/* Responsive Design */
	@media (max-width: 768px) {
		.tmt-b-container {
			padding: 1rem;
		}

		.intro-header h1 {
			font-size: 2rem;
		}

		.measures-grid {
			grid-template-columns: 1fr;
		}

		.test-canvas {
			max-width: 100%;
			height: auto;
		}

		.metrics-grid {
			grid-template-columns: 1fr;
		}
	}
</style>

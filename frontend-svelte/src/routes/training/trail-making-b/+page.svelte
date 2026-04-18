<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
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
	import { onDestroy, onMount } from 'svelte';

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
	let elapsedTime = 0;
	let timerInterval = null;
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
	let practiceSetupTimeout = null;
	let practiceFinishTimeout = null;
	let canvasInitTimeout = null;
	let errorFlashTimeout = null;

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
		return values.map((value) => marker(value)).join(' \u2192 ');
	}

	function difficultyChangeLabel(before, after) {
		return $locale === 'bn'
			? `কঠিনতা: ${n(before)} \u2192 ${n(after)}`
			: `Difficulty: ${before} \u2192 ${after}`;
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

	onDestroy(() => {
		if (timerInterval) clearInterval(timerInterval);
		if (practiceSetupTimeout) clearTimeout(practiceSetupTimeout);
		if (practiceFinishTimeout) clearTimeout(practiceFinishTimeout);
		if (canvasInitTimeout) clearTimeout(canvasInitTimeout);
		if (errorFlashTimeout) clearTimeout(errorFlashTimeout);
	});

	async function loadSession() {
		try {
			loading = true;
			const response = await fetch(
				`${API_BASE_URL}/api/training/tasks/trail-making-b/generate/${currentUser.id}`,
				{ method: 'POST', headers: { 'Content-Type': 'application/json' } }
			);

			if (!response.ok) throw new Error('Failed to load session');

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
		if (timerInterval) {
			clearInterval(timerInterval);
			timerInterval = null;
		}
		clearTimeout(practiceSetupTimeout);
		clearTimeout(practiceFinishTimeout);
		clearTimeout(canvasInitTimeout);
		clearTimeout(errorFlashTimeout);
		playMode = TASK_PLAY_MODE.PRACTICE;
		practiceStatusMessage = '';
		phase = 'practice';
		setupPracticeCanvas();
	}

	function finishPractice(completed = true) {
		if (timerInterval) {
			clearInterval(timerInterval);
			timerInterval = null;
		}
		clearTimeout(practiceSetupTimeout);
		clearTimeout(practiceFinishTimeout);
		clearTimeout(canvasInitTimeout);
		clearTimeout(errorFlashTimeout);
		playMode = TASK_PLAY_MODE.RECORDED;
		practiceFeedback = null;
		practiceIndex = 0;
		phase = 'instructions';
		practiceStatusMessage = completed ? getPracticeCopy($locale).complete : '';
	}

	function setupPracticeCanvas() {
		practiceCircles = [
			{ id: 'p0', label: '1', x: 150, y: 100, sequence_index: 0 },
			{ id: 'p1', label: 'A', x: 350, y: 150, sequence_index: 1 },
			{ id: 'p2', label: '2', x: 550, y: 100, sequence_index: 2 },
			{ id: 'p3', label: 'B', x: 350, y: 300, sequence_index: 3 },
			{ id: 'p4', label: '3', x: 150, y: 250, sequence_index: 4 }
		];

		practiceIndex = 0;
		practiceFeedback = null;

		practiceSetupTimeout = setTimeout(() => {
			practiceSetupTimeout = null;
			if (canvas) {
				ctx = canvas.getContext('2d');
				drawPracticeCanvas();
			}
		}, 100);
	}

	function drawPracticeCanvas() {
		if (!ctx || !canvas) return;

		ctx.clearRect(0, 0, canvas.width, canvas.height);

		practiceCircles.forEach((circle, idx) => {
			const isCompleted = idx < practiceIndex;
			const isLastClicked = idx === practiceIndex - 1;

			ctx.beginPath();
			ctx.arc(circle.x, circle.y, 30, 0, Math.PI * 2);

			if (isLastClicked) {
				ctx.fillStyle = '#fbbf24';
				ctx.strokeStyle = '#f59e0b';
			} else if (isCompleted) {
				ctx.fillStyle = '#4ade80';
				ctx.strokeStyle = '#22c55e';
			} else {
				ctx.fillStyle = 'white';
				ctx.strokeStyle = '#9333ea';
			}

			ctx.lineWidth = 3;
			ctx.fill();
			ctx.stroke();

			ctx.fillStyle = (isCompleted || isLastClicked) ? 'white' : '#1e293b';
			ctx.font = 'bold 20px Arial';
			ctx.textAlign = 'center';
			ctx.textBaseline = 'middle';
			ctx.fillText(marker(circle.label), circle.x, circle.y);
		});

		ctx.strokeStyle = '#9333ea';
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

		const clicked = practiceCircles.find(c => {
			const dist = Math.sqrt((c.x - x) ** 2 + (c.y - y) ** 2);
			return dist < 30;
		});

		if (clicked) {
			const expected = practiceCircles[practiceIndex];

			if (clicked.id === expected.id) {
				practiceIndex++;
				practiceFeedback = {
					type: 'success',
					message: $locale === 'bn'
						? `সঠিক! পরেরটি: ${practiceIndex < practiceCircles.length ? marker(practiceSequence[practiceIndex]) : 'সব সম্পন্ন!'}`
						: `Correct! Next: ${practiceIndex < practiceCircles.length ? practiceSequence[practiceIndex] : 'All done!'}`
				};

				drawPracticeCanvas();

				if (practiceIndex >= practiceCircles.length) {
					practiceFinishTimeout = setTimeout(() => {
						practiceFinishTimeout = null;
						finishPractice();
					}, 1500);
				}
			} else {
				practiceFeedback = {
					type: 'error',
					message: $locale === 'bn'
						? `ভুল! আপনি "${marker(clicked.label)}" ক্লিক করেছেন, কিন্তু "${marker(expected.label)}" ক্লিক করা উচিত ছিল`
						: `Wrong! You clicked "${clicked.label}" but should click "${expected.label}"`
				};
			}
		}
	}

	function startTest() {
		clearTimeout(practiceSetupTimeout);
		clearTimeout(practiceFinishTimeout);
		clearTimeout(canvasInitTimeout);
		clearTimeout(errorFlashTimeout);
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

		timerInterval = setInterval(() => {
			elapsedTime = (Date.now() - startTime) / 1000;
		}, 100);

		canvasInitTimeout = setTimeout(() => {
			canvasInitTimeout = null;
			if (canvas) {
				ctx = canvas.getContext('2d');
				drawCanvas();
			}
		}, 100);
	}

	function drawCanvas() {
		if (!ctx || !canvas) return;

		ctx.clearRect(0, 0, canvas.width, canvas.height);

		ctx.strokeStyle = '#9333ea';
		ctx.lineWidth = 2;
		connections.forEach(conn => {
			ctx.beginPath();
			ctx.moveTo(conn.fromX, conn.fromY);
			ctx.lineTo(conn.toX, conn.toY);
			ctx.stroke();
		});

		circles.forEach(circle => {
			const isCompleted = !circle.is_distractor && circle.sequence_index < currentIndex;
			const isLastClicked = !circle.is_distractor && circle.sequence_index === currentIndex - 1;
			const isHovered = hoveredCircle === circle.id;

			ctx.beginPath();
			ctx.arc(circle.x, circle.y, getCircleRadius(), 0, Math.PI * 2);

			if (isLastClicked) {
				ctx.fillStyle = '#fbbf24';
				ctx.strokeStyle = '#f59e0b';
			} else if (isCompleted) {
				ctx.fillStyle = '#4ade80';
				ctx.strokeStyle = '#22c55e';
			} else if (isHovered) {
				ctx.fillStyle = '#f3e8ff';
				ctx.strokeStyle = '#9333ea';
			} else if (circle.is_distractor) {
				ctx.fillStyle = '#f1f5f9';
				ctx.strokeStyle = '#cbd5e1';
			} else {
				ctx.fillStyle = 'white';
				ctx.strokeStyle = '#9333ea';
			}

			ctx.lineWidth = isLastClicked ? 4 : 2;
			ctx.fill();
			ctx.stroke();

			ctx.fillStyle = (isCompleted || isLastClicked) ? 'white' : circle.is_distractor ? '#94a3b8' : '#1e293b';
			ctx.font = `bold ${getFontSize()}px Arial`;
			ctx.textAlign = 'center';
			ctx.textBaseline = 'middle';
			ctx.fillText(marker(circle.label), circle.x, circle.y);
		});
	}

	function getCircleRadius() {
		const sizeMap = { 'large': 35, 'medium': 30, 'small': 25, 'extra-small': 20 };
		return sizeMap[sessionData?.circle_size] || 30;
	}

	function getFontSize() {
		const sizeMap = { 'large': 20, 'medium': 18, 'small': 16, 'extra-small': 14 };
		return sizeMap[sessionData?.circle_size] || 18;
	}

	function handleCanvasClick(event) {
		if (completed) return;

		const rect = canvas.getBoundingClientRect();
		const x = event.clientX - rect.left;
		const y = event.clientY - rect.top;

		const radius = getCircleRadius();
		const clicked = circles.find(c => {
			const dist = Math.sqrt((c.x - x) ** 2 + (c.y - y) ** 2);
			return dist < radius;
		});

		if (clicked) handleCircleClick(clicked);
	}

	function handleCircleClick(circle) {
		const expectedLabel = sessionData.correct_sequence[currentIndex];

		if (circle.label === expectedLabel && !circle.is_distractor) {
			userSequence.push(circle.id);

			if (currentIndex > 0) {
				const prevCircle = circles.find(c => c.sequence_index === currentIndex - 1);
				if (prevCircle) {
					connections.push({
						fromX: prevCircle.x, fromY: prevCircle.y,
						toX: circle.x, toY: circle.y
					});
				}
			}

			currentIndex++;

			if (currentIndex >= sessionData.correct_sequence.length) {
				completeSession();
			}

			drawCanvas();
		} else {
			const errorType = circle.is_distractor ? 'distractor_clicked' : 'sequence_error';
			const isPerseverative = currentIndex > 0 &&
				circle.label === sessionData.correct_sequence[currentIndex - 1];

			errors.push({
				sequence_index: currentIndex,
				clicked_label: circle.label,
				expected_label: expectedLabel,
				type: isPerseverative ? 'perseverative_error' : errorType,
				timestamp: Date.now() - startTime
			});

			ctx.beginPath();
			ctx.arc(circle.x, circle.y, getCircleRadius(), 0, Math.PI * 2);
			ctx.fillStyle = '#ef4444';
			ctx.fill();
			ctx.strokeStyle = '#dc2626';
			ctx.stroke();

			errorFlashTimeout = setTimeout(() => {
				errorFlashTimeout = null;
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
		completionTime = (Date.now() - startTime) / 1000;
		taskId = $page.url.searchParams.get('taskId');

		try {
			const response = await fetch(
				`${API_BASE_URL}/api/training/tasks/trail-making-b/submit/${currentUser.id}`,
				{
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
				}
			);

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

	$: performanceBadgeColor = metrics?.performance_level === 'Excellent' ? 'excellent' :
		metrics?.performance_level === 'Good' ? 'good' :
		metrics?.performance_level === 'Fair' ? 'fair' : 'needs-improvement';
</script>

<svelte:head>
	<title>{t('Trail Making Test - Part B')} | NeuroBloom</title>
</svelte:head>

<svelte:window on:keydown={(e) => e.key === 'Escape' && phase !== 'results' && returnToDashboard()} />

<div class="tmtb-container">

	<!-- ── LOADING ─────────────────────────────────────────────── -->
	{#if loading}
		<div class="loading-wrap">
			<LoadingSkeleton />
		</div>

	<!-- ── INTRO ──────────────────────────────────────────────── -->
	{:else if phase === 'intro'}
		<div class="page-wrapper">

			<!-- Title row -->
			<div class="task-title-row">
				<div>
					<h1>{t('Trail Making Test')}</h1>
					<p class="task-subtitle">{t('Part B — Cognitive Flexibility & Set-Shifting')}</p>
				</div>
				<DifficultyBadge {difficulty} domain="Cognitive Flexibility" />
			</div>

			<!-- Concept card -->
			<div class="card task-concept">
				<div class="concept-badge">{t('Executive Function Gold Standard')}</div>
				<p class="concept-body">
					{$locale === 'bn'
						? 'বৃত্তগুলি সংখ্যা ও বর্ণ পর্যায়ক্রমে সংযুক্ত করুন — যেমন 1 → A → 2 → B → 3 → C। এটি কগনিটিভ ফ্লেক্সিবিলিটি, সেট-শিফটিং এবং বিভক্ত মনোযোগ মাপে।'
						: 'Connect circles alternating between numbers and letters — 1 \u2192 A \u2192 2 \u2192 B \u2192 3 \u2192 C. This measures cognitive flexibility, set-shifting, and divided attention.'}
				</p>
			</div>

			<!-- Rules grid -->
			<div class="card">
				<h2 class="section-title">{t('How It Works')}</h2>
				<div class="rules-grid">
					<div class="rule-item">
						<div class="rule-num purple">1</div>
						<div class="rule-body">
							<strong>{t('Alternating Pattern')}</strong>
							<div class="seq-demo">
								<span class="seq-num">1</span>
								<span class="seq-arr">\u2192</span>
								<span class="seq-let">A</span>
								<span class="seq-arr">\u2192</span>
								<span class="seq-num">2</span>
								<span class="seq-arr">\u2192</span>
								<span class="seq-let">B</span>
								<span class="seq-arr">\u2192</span>
								<span class="seq-num">3</span>
							</div>
							<span>{t('Always alternate number \u2192 letter \u2192 number')}</span>
						</div>
					</div>
					<div class="rule-item">
						<div class="rule-num purple">2</div>
						<div class="rule-body">
							<strong>{t('Click in Sequence')}</strong>
							<span>{t('Click each circle in the correct order. A line draws as you connect them.')}</span>
						</div>
					</div>
					<div class="rule-item">
						<div class="rule-num purple">3</div>
						<div class="rule-body">
							<strong>{t('Speed Matters')}</strong>
							<span>{t('Work as quickly as possible. Your completion time is recorded.')}</span>
						</div>
					</div>
					<div class="rule-item">
						<div class="rule-num purple">4</div>
						<div class="rule-body">
							<strong>{t('Watch for Distractors')}</strong>
							<span>{t('Some circles may not belong in the sequence — only click circles that follow the pattern.')}</span>
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
							<span class="dl-value purple-val">{levelLabel()}</span>
						</li>
						<li>
							<span class="dl-label">{t('Total Items')}</span>
							<span class="dl-value">{n(sessionData.total_items)}</span>
						</li>
						<li>
							<span class="dl-label">{t('Time Limit')}</span>
							<span class="dl-value">
								{$locale === 'bn'
									? `${n(sessionData.time_limit_seconds / 60)} মিনিট`
									: `${sessionData.time_limit_seconds / 60} min`}
							</span>
						</li>
						<li>
							<span class="dl-label">{t('Sequence')}</span>
							<span class="dl-value">{t('1 \u2192 A \u2192 2 \u2192 B \u2192 ...')}</span>
						</li>
					</ul>
				</div>
				<div class="card">
					<h3 class="card-heading">{t('What It Measures')}</h3>
					<ul class="measure-list">
						<li><span class="dot purple"></span><div><strong>{t('Set-Shifting')}</strong><p>{t('Switching between number and letter rules')}</p></div></li>
						<li><span class="dot purple"></span><div><strong>{t('Cognitive Flexibility')}</strong><p>{t('Mental agility under time pressure')}</p></div></li>
						<li><span class="dot purple"></span><div><strong>{t('Divided Attention')}</strong><p>{t('Tracking two alternating sequences simultaneously')}</p></div></li>
						<li><span class="dot purple"></span><div><strong>{t('Processing Speed')}</strong><p>{t('Speed of visual scanning and response')}</p></div></li>
					</ul>
				</div>
			</div>

			<!-- Clinical info -->
			<div class="card clinical-info">
				<h3 class="card-heading">{t('Clinical Significance')}</h3>
				<div class="clinical-grid">
					<div class="clinical-item">
						<span class="ci-label">{t('Standard Test')}</span>
						<span>{t('Halstead-Reitan Battery, widely used in neuropsychology')}</span>
					</div>
					<div class="clinical-item">
						<span class="ci-label">{t('MS Relevance')}</span>
						<span>{t('Sensitive to MS executive dysfunction and set-shifting deficits')}</span>
					</div>
					<div class="clinical-item">
						<span class="ci-label">{t('Key Metric')}</span>
						<span>{t('B-A Score = Part B time minus Part A time (pure switching cost)')}</span>
					</div>
					<div class="clinical-item">
						<span class="ci-label">{t('Reference')}</span>
						<span>D'Elia et al., 1996; {t('MS executive function research')}</span>
					</div>
				</div>
			</div>

			<!-- Performance guide -->
			<div class="card perf-guide">
				<h3 class="card-heading">{t('Performance Guide — Completion Time')}</h3>
				<div class="norm-bars">
					<div class="norm-bar">
						<span class="norm-label">{t('Excellent')}</span>
						<div class="norm-track"><div class="norm-fill purple-fill" style="width:25%"></div></div>
						<span class="norm-val">&lt; 60s</span>
					</div>
					<div class="norm-bar">
						<span class="norm-label">{t('Good')}</span>
						<div class="norm-track"><div class="norm-fill purple-mid" style="width:50%"></div></div>
						<span class="norm-val">60–90s</span>
					</div>
					<div class="norm-bar">
						<span class="norm-label">{t('Developing')}</span>
						<div class="norm-track"><div class="norm-fill purple-low" style="width:75%"></div></div>
						<span class="norm-val">&gt; 90s</span>
					</div>
				</div>
			</div>

			<div class="btn-row">
				<button class="start-button" on:click={startInstructions}>
					{t('Continue to Instructions')}
				</button>
				<button class="btn-secondary" on:click={returnToDashboard}>
					{t('Back to Dashboard')}
				</button>
			</div>
		</div>

	<!-- ── INSTRUCTIONS ───────────────────────────────────────── -->
	{:else if phase === 'instructions'}
		<div class="page-wrapper">
			<div class="card instructions-card">
				<h2 class="instr-title">{t('How to Complete Trail Making Test - Part B')}</h2>

				<div class="seq-callout">
					<span class="seq-label">{t('Alternating pattern:')}</span>
					<div class="seq-row">
						<span class="seq-num">1</span>
						<span class="seq-arr-lg">\u2192</span>
						<span class="seq-let">A</span>
						<span class="seq-arr-lg">\u2192</span>
						<span class="seq-num">2</span>
						<span class="seq-arr-lg">\u2192</span>
						<span class="seq-let">B</span>
						<span class="seq-arr-lg">\u2192</span>
						<span class="seq-num">3</span>
						<span class="seq-arr-lg">\u2192</span>
						<span class="seq-let">C</span>
						<span class="seq-more">...</span>
					</div>
				</div>

				<div class="flow-row">
					<div class="flow-step">
						<div class="flow-num purple">1</div>
						<p class="flow-label">{t('Circles Appear')}</p>
						<p class="flow-sub">{t('Numbers and letters scattered on screen')}</p>
					</div>
					<div class="flow-connector"></div>
					<div class="flow-step">
						<div class="flow-num purple">2</div>
						<p class="flow-label">{t('Click in Order')}</p>
						<p class="flow-sub">{t('1 \u2192 A \u2192 2 \u2192 B, alternating')}</p>
					</div>
					<div class="flow-connector"></div>
					<div class="flow-step">
						<div class="flow-num purple">3</div>
						<p class="flow-label">{t('Line Connects')}</p>
						<p class="flow-sub">{t('A trail draws as you progress')}</p>
					</div>
					<div class="flow-connector"></div>
					<div class="flow-step">
						<div class="flow-num purple">4</div>
						<p class="flow-label">{t('Finish Fast')}</p>
						<p class="flow-sub">{t('Complete all items as quickly as possible')}</p>
					</div>
				</div>

				<div class="legend-block">
					<h4 class="legend-title">{t('Circle Colors')}</h4>
					<div class="legend-grid">
						<div class="legend-item">
							<div class="legend-dot" style="background:#fff;border:3px solid #9333ea;"></div>
							<span>{t('Next to click')}</span>
						</div>
						<div class="legend-item">
							<div class="legend-dot" style="background:#fbbf24;border:3px solid #f59e0b;"></div>
							<span>{t('Just clicked')}</span>
						</div>
						<div class="legend-item">
							<div class="legend-dot" style="background:#4ade80;border:3px solid #22c55e;"></div>
							<span>{t('Completed')}</span>
						</div>
						<div class="legend-item">
							<div class="legend-dot" style="background:#ef4444;border:3px solid #dc2626;"></div>
							<span>{t('Error flash')}</span>
						</div>
					</div>
				</div>

				<div class="strategy-box">
					<h4>{t('Success Strategy')}</h4>
					<ul>
						<li>{t('Scan the whole screen before starting — plan your path')}</li>
						<li>{t('Alternate strictly: number \u2192 letter \u2192 number \u2192 letter')}</li>
						<li>{t('If you make an error, the circle flashes red — keep going without stopping')}</li>
						<li>{t('Ignore circles that are not part of the alternating pattern')}</li>
					</ul>
				</div>

				<TaskPracticeActions
					locale={$locale}
					startLabel={t('Start Actual Test')}
					practiceVisible={false}
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
				<h2 class="trial-title">{t('Practice Round')}</h2>
				<p class="trial-sub">{t('Connect:')} {sequencePreview()}</p>
			</div>

			<div class="canvas-card">
				<canvas
					bind:this={canvas}
					width="800"
					height="400"
					on:click={handlePracticeClick}
					class="test-canvas"
				></canvas>
			</div>

			{#if practiceFeedback}
				<div class="feedback-pill {practiceFeedback.type}">{practiceFeedback.message}</div>
			{/if}

			<p class="trial-hint">{t('Click the circles in order:')} {sequencePreview()}</p>
		</div>

	<!-- ── TEST ───────────────────────────────────────────────── -->
	{:else if phase === 'test'}
		<div class="trial-wrapper">
			<div class="test-status-row">
				<div class="progress-pill">
					{t('Progress:')} {n(currentIndex)}/{n(sessionData.correct_sequence.length)}
				</div>
				<div class="timer-pill">
					{secondsLabel(elapsedTime)}
				</div>
			</div>

			<div class="canvas-card">
				<canvas
					bind:this={canvas}
					width="800"
					height="600"
					on:click={handleCanvasClick}
					on:mousemove={handleCanvasMove}
					class="test-canvas"
				></canvas>
			</div>

			<p class="trial-hint">
				{t('Connect in order: 1 \u2192 A \u2192 2 \u2192 B \u2192 3 \u2192 C... | Click circles to connect')}
			</p>
		</div>

	<!-- ── RESULTS ─────────────────────────────────────────────── -->
	{:else if phase === 'results'}
		<div class="page-wrapper">

			{#if newBadges.length > 0}
				<BadgeNotification badges={newBadges} />
			{/if}

			<!-- Header -->
			<div class="results-header">
				<h1>{t('Trail Making Test - Part B Complete')}</h1>
				<div class="perf-pill perf-{performanceBadgeColor}">
					{t(metrics.performance_level)}
				</div>
			</div>

			<!-- Metrics -->
			<div class="metrics-grid">
				<div class="metric-card purple-top">
					<p class="m-label">{t('Completion Time')}</p>
					<p class="m-value">{secondsLabel(metrics?.completion_time_seconds || 0)}</p>
					<p class="m-sub">{metrics?.completed ? t('Finished') : t('Incomplete')}</p>
				</div>
				<div class="metric-card purple-top">
					<p class="m-label">{t('Accuracy')}</p>
					<p class="m-value">{pct(metrics?.accuracy || 0)}</p>
					<p class="m-sub">{n(metrics?.items_completed || 0)}/{n(metrics?.total_items || 0)} {t('correct')}</p>
				</div>
				<div class="metric-card purple-top">
					<p class="m-label">{t('Total Errors')}</p>
					<p class="m-value">{n(metrics?.total_errors || 0)}</p>
					<p class="m-sub">
						{n(metrics?.sequence_errors || 0)} {t('sequence')} &bull;
						{n(metrics?.perseverative_errors || 0)} {t('perseverative')}
					</p>
				</div>
				{#if metrics?.b_a_score !== null}
					<div class="metric-card purple-top">
						<p class="m-label">{t('B-A Score')}</p>
						<p class="m-value">{secondsLabel(metrics?.b_a_score || 0)}</p>
						<p class="m-sub">{t('Part B minus Part A time')}</p>
					</div>
				{/if}
			</div>

			<!-- Interpretation -->
			<div class="card">
				<h2 class="section-title">{t('Performance Analysis')}</h2>
				<p class="interp-text">{metrics?.interpretation || ''}</p>

				{#if metrics?.clinical_note}
					<div class="clinical-note-box">
						<strong>{t('Clinical Note:')}</strong> {t(metrics.clinical_note)}
					</div>
				{/if}
			</div>

			<!-- Details -->
			<div class="card">
				<h2 class="section-title">{t('Detailed Breakdown')}</h2>
				<div class="detail-grid">
					<div class="detail-item">
						<span class="dl-label">{t('Percentile Rank')}</span>
						<span class="dl-value">{$locale === 'bn' ? `${n(metrics?.percentile || 0)}তম` : `${metrics?.percentile || 0}th`}</span>
					</div>
					<div class="detail-item">
						<span class="dl-label">{t('Adjusted Time')}</span>
						<span class="dl-value">{secondsLabel(metrics?.adjusted_time_seconds || 0)}</span>
					</div>
					<div class="detail-item">
						<span class="dl-label">{t('Items Completed')}</span>
						<span class="dl-value">{n(metrics?.items_completed || 0)}/{n(metrics?.total_items || 0)}</span>
					</div>
					<div class="detail-item">
						<span class="dl-label">{t('Difficulty Level')}</span>
						<span class="dl-value">{levelLabel(metrics?.difficulty || 1)}</span>
					</div>
				</div>
			</div>

			<!-- Error analysis -->
			{#if metrics?.total_errors > 0}
				<div class="card">
					<h2 class="section-title">{t('Error Analysis')}</h2>
					<div class="error-grid">
						<div class="error-stat-card">
							<p class="err-count">{metrics?.sequence_errors || 0}</p>
							<p class="err-type">{t('Sequence Errors')}</p>
							<p class="err-desc">{t('Wrong circle clicked')}</p>
						</div>
						<div class="error-stat-card">
							<p class="err-count">{metrics?.perseverative_errors || 0}</p>
							<p class="err-type">{t('Perseverative Errors')}</p>
							<p class="err-desc">{t('Clicked previous circle again')}</p>
						</div>
					</div>
					<div class="error-tip-box">
						{t('Tip: Focus on the alternating pattern (number \u2192 letter \u2192 number) and scan ahead before each click.')}
					</div>
				</div>
			{/if}

			<!-- Clinical context -->
			<div class="card clinical-context-card">
				<h3 class="card-heading">{t('Clinical Context')}</h3>
				<p>
					{$locale === 'bn'
						? 'TMT-B সম্পূর্ণ করার সময় এবং B-A স্কোর (Part B সময় বিয়োগ Part A সময়) কগনিটিভ ফ্লেক্সিবিলিটি এবং সেট-শিফটিং ক্ষমতার মূল সূচক। MS রোগীদের ক্ষেত্রে এই পরীক্ষা এক্সিকিউটিভ ডিসফাংশন এবং মাল্টিটাস্কিং ক্ষমতার পরিবর্তন শনাক্ত করতে সহায়তা করে।'
						: 'Trail Making Test Part B completion time and the B-A score (Part B minus Part A) are key indices of cognitive flexibility and set-shifting. In MS patients, this test detects executive dysfunction and changes in real-world multitasking ability.'}
				</p>
			</div>

			<div class="btn-row">
				<button class="start-button" on:click={returnToDashboard}>
					{t('Return to Dashboard')}
				</button>
			</div>
		</div>
	{/if}
</div>

<!-- Help FAB -->
{#if phase === 'intro' || phase === 'instructions'}
	<button class="help-fab" on:click={() => {}} aria-label="Help">?</button>
{/if}

<style>
	/* ── Base ──────────────────────────────────────────────── */
	.tmtb-container {
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
		background: linear-gradient(135deg, #f3e8ff 0%, #faf5ff 100%);
		border: 1px solid #d8b4fe;
	}

	.concept-badge {
		display: inline-block;
		background: #9333ea;
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

	.rule-num.purple { background: #9333ea; color: #fff; }

	.rule-body {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
		font-size: 0.95rem;
		color: #374151;
	}

	.rule-body strong { color: #1e293b; }
	.rule-body span { font-size: 0.85rem; color: #64748b; }

	/* Sequence demo */
	.seq-demo {
		display: flex;
		align-items: center;
		gap: 0.3rem;
		flex-wrap: wrap;
		margin: 0.25rem 0;
	}

	.seq-num {
		width: 2rem;
		height: 2rem;
		border-radius: 50%;
		background: #f3e8ff;
		border: 2px solid #9333ea;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 700;
		font-size: 0.9rem;
		color: #6b21a8;
	}

	.seq-let {
		width: 2rem;
		height: 2rem;
		border-radius: 50%;
		background: #ede9fe;
		border: 2px solid #7c3aed;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 700;
		font-size: 0.9rem;
		color: #4c1d95;
	}

	.seq-arr { font-size: 0.8rem; color: #9333ea; font-weight: 700; }

	/* ── Info grid ─────────────────────────────────────────── */
	.info-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.5rem;
	}

	.detail-list {
		list-style: none;
		padding: 0;
		margin: 0;
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
	.dl-value.purple-val {
		background: #f3e8ff;
		color: #6b21a8;
		padding: 0.2rem 0.75rem;
		border-radius: 999px;
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

	.dot.purple { background: #9333ea; }

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
	.norm-fill.purple-fill { background: #9333ea; }
	.norm-fill.purple-mid  { background: #a855f7; }
	.norm-fill.purple-low  { background: #c084fc; }

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

	/* ── Instructions card ─────────────────────────────────── */
	.instructions-card { max-width: 780px; margin: 0 auto; width: 100%; }

	.instr-title {
		font-size: 1.5rem;
		font-weight: 800;
		color: #1e293b;
		text-align: center;
		margin-bottom: 1.5rem;
	}

	/* Sequence callout */
	.seq-callout {
		background: #f3e8ff;
		border-left: 4px solid #9333ea;
		border-radius: 12px;
		padding: 1rem 1.5rem;
		margin-bottom: 1.5rem;
	}

	.seq-label {
		display: block;
		font-size: 0.8rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: #6b21a8;
		margin-bottom: 0.75rem;
	}

	.seq-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-wrap: wrap;
	}

	.seq-arr-lg { font-size: 1.1rem; color: #9333ea; font-weight: 700; }
	.seq-more   { font-size: 1.1rem; color: #9333ea; font-weight: 700; }

	/* Flow */
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
		max-width: 120px;
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

	.flow-num.purple { background: #9333ea; color: #fff; }

	.flow-label { font-weight: 600; font-size: 0.9rem; color: #1e293b; text-align: center; margin: 0; }
	.flow-sub   { font-size: 0.78rem; color: #64748b; text-align: center; margin: 0; }

	.flow-connector {
		width: 2rem;
		height: 2px;
		background: #cbd5e1;
		flex-shrink: 0;
	}

	/* Legend */
	.legend-block {
		background: #f8fafc;
		border-radius: 12px;
		padding: 1.25rem;
		margin-bottom: 1.5rem;
	}

	.legend-title {
		font-size: 0.95rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 0.75rem;
	}

	.legend-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 0.75rem;
	}

	.legend-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.85rem;
		color: #374151;
	}

	.legend-dot {
		width: 1.5rem;
		height: 1.5rem;
		border-radius: 50%;
		flex-shrink: 0;
	}

	/* Strategy box */
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
		color: #9333ea;
		font-weight: 700;
	}

	/* ── Trial / test wrapper ──────────────────────────────── */
	.trial-wrapper {
		max-width: 900px;
		margin: 0 auto;
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	.trial-top { text-align: center; }

	.trial-title {
		font-size: 1.25rem;
		font-weight: 700;
		color: #1e293b;
		margin: 0 0 0.25rem;
	}

	.trial-sub  { font-size: 0.95rem; color: #64748b; margin: 0; }
	.trial-hint { font-size: 0.9rem; color: #64748b; text-align: center; padding: 0.75rem 1rem; background: #fff; border-radius: 10px; }

	/* Status row */
	.test-status-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.progress-pill {
		background: linear-gradient(135deg, #9333ea, #7c3aed);
		color: #fff;
		padding: 0.6rem 1.5rem;
		border-radius: 999px;
		font-weight: 700;
		font-size: 1rem;
	}

	.timer-pill {
		background: linear-gradient(135deg, #059669, #047857);
		color: #fff;
		padding: 0.6rem 1.5rem;
		border-radius: 999px;
		font-weight: 700;
		font-size: 1rem;
		font-variant-numeric: tabular-nums;
		min-width: 80px;
		text-align: center;
	}

	/* Canvas card */
	.canvas-card {
		background: #fff;
		border-radius: 16px;
		padding: 1.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
		display: flex;
		justify-content: center;
	}

	.test-canvas {
		border: 1.5px solid #e2e8f0;
		border-radius: 10px;
		cursor: pointer;
		max-width: 100%;
	}

	/* Feedback pill */
	.feedback-pill {
		text-align: center;
		padding: 1rem 1.5rem;
		border-radius: 12px;
		font-size: 1rem;
		font-weight: 600;
	}

	.feedback-pill.success { background: #d1fae5; color: #065f46; border: 1.5px solid #34d399; }
	.feedback-pill.error   { background: #fee2e2; color: #991b1b; border: 1.5px solid #f87171; }

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

	.perf-pill.perf-excellent      { background: #d1fae5; color: #065f46; }
	.perf-pill.perf-good           { background: #dbeafe; color: #1e40af; }
	.perf-pill.perf-fair           { background: #fef3c7; color: #92400e; }
	.perf-pill.perf-needs-improvement { background: #f3f4f6; color: #374151; }

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

	.metric-card.purple-top { border-top: 4px solid #9333ea; }

	.m-label {
		font-size: 0.75rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: #64748b;
		margin-bottom: 0.5rem;
	}

	.m-value { font-size: 2rem; font-weight: 800; color: #1e293b; margin-bottom: 0.25rem; }
	.m-sub   { font-size: 0.8rem; color: #94a3b8; }

	/* Interpretation */
	.interp-text { font-size: 1rem; line-height: 1.7; color: #374151; margin-bottom: 1rem; }

	.clinical-note-box {
		background: #f0f9ff;
		border-left: 4px solid #9333ea;
		border-radius: 10px;
		padding: 1rem 1.25rem;
		color: #1e293b;
		font-size: 0.9rem;
		line-height: 1.6;
	}

	/* Detail grid */
	.detail-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 0.75rem;
	}

	.detail-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem;
		background: #f8fafc;
		border-radius: 8px;
		font-size: 0.9rem;
	}

	/* Error analysis */
	.error-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
		margin-bottom: 1rem;
	}

	.error-stat-card {
		background: #fef2f2;
		border-radius: 12px;
		padding: 1.25rem;
		text-align: center;
	}

	.err-count { font-size: 2rem; font-weight: 800; color: #dc2626; margin-bottom: 0.25rem; }
	.err-type  { font-weight: 700; color: #1e293b; font-size: 0.95rem; margin-bottom: 0.15rem; }
	.err-desc  { font-size: 0.85rem; color: #64748b; }

	.error-tip-box {
		background: #e0f2fe;
		border-radius: 10px;
		padding: 1rem 1.25rem;
		color: #0369a1;
		font-size: 0.9rem;
		line-height: 1.6;
	}

	/* Clinical context */
	.clinical-context-card { background: #f8fafc; border: 1px solid #e2e8f0; }
	.clinical-context-card p { font-size: 0.95rem; line-height: 1.7; color: #374151; margin: 0; }

	/* ── Help FAB ──────────────────────────────────────────── */
	.help-fab {
		position: fixed;
		bottom: 2rem;
		right: 2rem;
		width: 3rem;
		height: 3rem;
		border-radius: 50%;
		background: #9333ea;
		color: #fff;
		border: none;
		font-size: 1.25rem;
		font-weight: 800;
		cursor: pointer;
		box-shadow: 0 4px 12px rgba(147, 51, 234, 0.4);
		z-index: 50;
		transition: transform 0.15s;
	}

	.help-fab:hover { transform: scale(1.1); }

	/* ── Responsive ────────────────────────────────────────── */
	@media (max-width: 768px) {
		.tmtb-container { padding: 1rem 0.75rem; }
		h1 { font-size: 1.5rem; }
		.rules-grid,
		.info-grid,
		.clinical-grid { grid-template-columns: 1fr; }
		.metrics-grid   { grid-template-columns: 1fr 1fr; }
		.detail-grid,
		.error-grid     { grid-template-columns: 1fr; }
		.legend-grid    { grid-template-columns: repeat(2, 1fr); }
		.flow-row       { flex-direction: column; gap: 0.75rem; }
		.flow-connector { width: 2px; height: 1.5rem; }
		.test-canvas    { max-width: 100%; height: auto; }
		.norm-bar       { grid-template-columns: 90px 1fr 70px; }
	}

	@media (max-width: 480px) {
		.metrics-grid { grid-template-columns: 1fr; }
	}
</style>

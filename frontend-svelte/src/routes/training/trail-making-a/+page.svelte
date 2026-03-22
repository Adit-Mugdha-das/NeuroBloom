<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import { formatNumber, formatPercent, locale, translateText } from '$lib/i18n';
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

	let showHelp = false;
	let sessionResults = null;
	let countdown = 3;

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
			trial = data.trial;
			
			state = STATE.INSTRUCTIONS;
		} catch (error) {
			console.error('Error loading session:', error);
			alert(t('Failed to load task session'));
			goto('/dashboard');
		}
	}

	function startTest() {
		state = STATE.READY;
		countdown = 3;
		
		const countdownInterval = setInterval(() => {
			countdown--;
			if (countdown <= 0) {
				clearInterval(countdownInterval);
				beginTest();
			}
		}, 1000);
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
		setTimeout(() => {
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
	{#if state === STATE.LOADING}
		<div class="loading">
			<div class="spinner"></div>
			<p>{t('Loading Trail Making Test...')}</p>
		</div>
	{:else if state === STATE.INSTRUCTIONS}
		<div class="instructions">
			<div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap;">
				<h1>{t('Trail Making Test - Part A')}</h1>
				<DifficultyBadge difficulty={difficulty} domain="Processing Speed" />
			</div>
			<div class="classic-badge">{t('Classic Neuropsychological Test')}</div>
			
			<div class="instruction-card">
				<h2>{t('About This Test')}</h2>
				<p class="importance">
					{$locale === 'bn'
						? 'Trail Making Test (TMT) হলো Halstead-Reitan Battery-র একটি ক্লাসিক নিউরোসাইকোলজিক্যাল মূল্যায়ন। এটি সাইকোমোটর গতি, ভিজ্যুয়াল স্ক্যানিং এবং মোটর নিয়ন্ত্রণ মূল্যায়ন করে, যেগুলো এমএসে প্রভাবিত হতে পারে।'
						: 'The Trail Making Test (TMT) is a classic neuropsychological assessment from the Halstead-Reitan Battery. It measures psychomotor speed, visual scanning, and motor control - all areas that can be affected by MS.'}
				</p>
				
				<div class="clinical-info">
					<h3>{t('Clinical Significance')}</h3>
					<ul>
						<li>{$locale === 'bn' ? 'প্রসেসিং স্পিড মাপার নির্ভরযোগ্য মানদণ্ড' : 'Gold standard for measuring processing speed'}</li>
						<li>{$locale === 'bn' ? 'এমএসের অগ্রগতি ধরতে অত্যন্ত সংবেদনশীল' : 'Highly sensitive to MS progression'}</li>
						<li>{$locale === 'bn' ? 'ভিজ্যুয়াল স্ক্যানিং ও মোটর সমন্বয় মূল্যায়ন করে' : 'Assesses visual scanning and motor coordination'}</li>
						<li>{$locale === 'bn' ? 'নিউরোলজিক্যাল মূল্যায়নে বহুল ব্যবহৃত' : 'Widely used in neurological assessments'}</li>
					</ul>
				</div>

				<div class="how-it-works">
					<h3>{t('How It Works')}</h3>
					<div class="demo-sequence">
						<div class="demo-step">
							<div class="demo-circles">
								<div class="demo-circle active">{n(1)}</div>
								<div class="demo-arrow">→</div>
								<div class="demo-circle">{n(2)}</div>
								<div class="demo-arrow">→</div>
								<div class="demo-circle">{n(3)}</div>
								<div class="demo-arrow">...</div>
								<div class="demo-circle">{n(25)}</div>
							</div>
							<p><strong>{t('Connect the circles in order')}</strong></p>
							<p>{t('Click 1, then 2, then 3, and so on as fast as you can!')}</p>
						</div>
					</div>
				</div>

				<div class="test-details">
					<h3>{t('Test Format')}</h3>
					<div class="details-grid">
						<div class="detail-item">
							<div class="detail-icon">🔢</div>
							<div class="detail-text">
								<strong>{n(trial.circles.length)} {t('Circles')}</strong>
								<span>{t('Connect in sequence')}</span>
							</div>
						</div>
						<div class="detail-item">
							<div class="detail-icon">⚡</div>
							<div class="detail-text">
								<strong>{t('Speed Test')}</strong>
								<span>{t('As fast as possible')}</span>
							</div>
						</div>
						<div class="detail-item">
							<div class="detail-icon">✓</div>
							<div class="detail-text">
								<strong>{t('Accuracy Counts')}</strong>
								<span>{t('Avoid mistakes')}</span>
							</div>
						</div>
						<div class="detail-item">
							<div class="detail-icon">🎯</div>
							<div class="detail-text">
								<strong>{t('One Chance')}</strong>
								<span>{t('Do your best!')}</span>
							</div>
						</div>
					</div>
				</div>
				
				<div class="tips">
					<h3>{t('Pro Tips')}</h3>
					<ul>
						<li><strong>{t('Scan ahead:')}</strong> {$locale === 'bn' ? 'বর্তমান সংখ্যায় চাপার সময় পরের সংখ্যাটি কোথায় আছে তা আগেই খুঁজে নিন।' : 'Look for the next number while clicking current one'}</li>
						<li><strong>{t('Stay focused:')}</strong> {$locale === 'bn' ? 'অন্য প্রতীক দেখে মনোযোগ হারাবেন না।' : "Don't get distracted by other symbols"}</li>
						<li><strong>{t('Click center:')}</strong> {$locale === 'bn' ? 'প্রতিটি বৃত্তের মাঝখানে চাপার চেষ্টা করুন।' : 'Aim for the center of each circle'}</li>
						<li><strong>{t('Smooth movements:')}</strong> {$locale === 'bn' ? 'সুশৃঙ্খল পথ দ্রুততর ফল দেয়।' : 'Efficient path = better time'}</li>
						<li><strong>{t('No rush mistakes:')}</strong> {$locale === 'bn' ? 'অতিরিক্ত তাড়াহুড়ার চেয়ে দ্রুত কিন্তু নির্ভুল হওয়া ভালো।' : 'Going fast but accurate is better than rushing'}</li>
					</ul>
				</div>

				<div class="performance-guide">
					<h3>{t('Performance Norms (MS Patients)')}</h3>
					<div class="norm-scale">
						<div class="norm-item excellent">{$locale === 'bn' ? '&lt;২৯ সেকেন্ড = চমৎকার' : '<29 seconds = Excellent'}</div>
						<div class="norm-item good">{$locale === 'bn' ? '২৯-৩৯ সেকেন্ড = ভালো' : '29-39 seconds = Good'}</div>
						<div class="norm-item average">{$locale === 'bn' ? '৪০-৭৮ সেকেন্ড = গড়' : '40-78 seconds = Average'}</div>
						<div class="norm-item needs-practice">{$locale === 'bn' ? '&gt;৭৮ সেকেন্ড = আরও অনুশীলন দরকার' : '>78 seconds = Practice Needed'}</div>
					</div>
					<p class="norm-note">{$locale === 'bn' ? '*সময় ২৫টি বৃত্তের মানদণ্ডে সমন্বিত' : '*Times normalized to 25 circles'}</p>
				</div>
			</div>
			
			<button class="start-button" on:click={startTest}>{t('Start Trail Making Test')}</button>
		</div>
	{:else if state === STATE.READY}
		<div class="ready-screen">
			<h2>{t('Get Ready!')}</h2>
			<p class="ready-message">{t('Connect the numbered circles in order as fast as you can')}</p>
			<div class="ready-sequence">
				<div class="ready-circle">{n(1)}</div>
				<div class="ready-arrow">→</div>
				<div class="ready-circle">{n(2)}</div>
				<div class="ready-arrow">→</div>
				<div class="ready-circle">{n(3)}</div>
				<div class="ready-arrow">→</div>
				<div class="ready-dots">...</div>
			</div>
			<div class="countdown">{n(countdown)}</div>
		</div>
	{:else if state === STATE.TESTING}
		<div class="testing-screen">
			<div class="header">
				<div class="progress-info">
					<span class="next-badge">{t('Next:')} {n(currentNumber)}</span>
					<span class="progress-badge">{n(currentNumber - 1)} / {n(trial.circles.length)}</span>
					{#if errors.length > 0}
						<span class="errors-badge">{t('Errors:')} {n(errors.length)}</span>
					{/if}
				</div>
				<div class="timer-display">
					<span class="timer-icon">⏱️</span>
					<span class="timer-value">{secondsLabel(elapsedTime)}</span>
				</div>
				<button class="help-button-floating" on:click={toggleHelp}>?</button>
			</div>

			<div class="canvas-container">
				<canvas 
					bind:this={canvas} 
					on:click={handleCanvasClick}
				></canvas>
			</div>

			<div class="instruction-bar">
				<p>{t('Click the circles in numerical order: 1 → 2 → 3 → ...')}</p>
				<p class="current-target">{t('Looking for:')} <strong>{n(currentNumber)}</strong></p>
			</div>
		</div>
	{:else if state === STATE.COMPLETE}
		<div class="complete-screen">
			<h1>{t('Trail Making Test Complete!')} 🎉</h1>
			
			{#if sessionResults}
				{@const perfColor = getPerformanceColor(sessionResults.metrics.performance_level)}
				
				<div class="performance-badge" style="border-color: {perfColor}; color: {perfColor}">
					<div class="perf-level">{t(sessionResults.metrics.performance_level)}</div>
					<div class="perf-time">{secondsLabel(sessionResults.metrics.completion_time)}</div>
				</div>

				<div class="results-grid">
					<div class="result-card primary">
						<div class="result-icon">⏱️</div>
						<div class="result-value">{secondsLabel(sessionResults.metrics.completion_time)}</div>
						<div class="result-label">{t('Completion Time')}</div>
						<div class="result-sublabel">{t('Normalized:')} {secondsLabel(sessionResults.metrics.normalized_time)}</div>
					</div>
					
					<div class="result-card">
						<div class="result-icon">🎯</div>
						<div class="result-value">{n(sessionResults.metrics.score)}</div>
						<div class="result-label">{t('Score')}</div>
						<div class="result-sublabel">{t('Out of 100')}</div>
					</div>
					
					<div class="result-card">
						<div class="result-icon">✓</div>
						<div class="result-value">{pct(sessionResults.metrics.accuracy, { minimumFractionDigits: 0, maximumFractionDigits: 1 })}</div>
						<div class="result-label">{t('Accuracy')}</div>
						<div class="result-sublabel">{n(sessionResults.metrics.errors)} {t('errors')}</div>
					</div>
					
					<div class="result-card">
						<div class="result-icon">⚡</div>
						<div class="result-value">{n(sessionResults.metrics.processing_speed)}</div>
						<div class="result-label">{t('Processing Speed')}</div>
						<div class="result-sublabel">{t('Circles/second')}</div>
					</div>
				</div>

				<div class="performance-breakdown">
					<h3>{t('Detailed Analysis')}</h3>
					<div class="breakdown-grid">
						<div class="breakdown-item">
							<span>{t('Total Clicks:')}</span>
							<span class="value">{n(sessionResults.metrics.total_clicks)}</span>
						</div>
						<div class="breakdown-item">
							<span>{t('Errors Made:')}</span>
							<span class="value {sessionResults.metrics.errors > 0 ? 'error' : 'success'}">
								{n(sessionResults.metrics.errors)}
							</span>
						</div>
						<div class="breakdown-item">
							<span>{t('Path Efficiency:')}</span>
							<span class="value">{pct(sessionResults.metrics.path_efficiency, { minimumFractionDigits: 0, maximumFractionDigits: 1 })}</span>
						</div>
						<div class="breakdown-item">
							<span>{t('Performance Level:')}</span>
							<span class="value" style="color: {perfColor}">
								{t(sessionResults.metrics.performance_level)}
							</span>
						</div>
					</div>
				</div>

				<div class="clinical-context">
					<h3>{t('Clinical Context')}</h3>
					<p>
						{#if sessionResults.metrics.performance_level === 'Excellent'}
							{$locale === 'bn'
								? 'চমৎকার পারফরম্যান্স! আপনার প্রসেসিং স্পিড ও ভিজ্যুয়াল স্ক্যানিং গড়ের চেয়ে অনেক ভালো, যা শক্তিশালী সাইকোমোটর কার্যকারিতা নির্দেশ করে।'
								: 'Outstanding performance! Your processing speed and visual scanning are well above average for MS patients. This indicates excellent psychomotor function.'}
						{:else if sessionResults.metrics.performance_level === 'Good'}
							{$locale === 'bn'
								? 'খুব ভালো পারফরম্যান্স! আপনার প্রসেসিং স্পিড এমএস রোগীদের গড়ের চেয়ে ভালো। এই অগ্রগতি ধরে রাখুন।'
								: 'Great performance! Your processing speed is above average for MS patients. Keep up the excellent work!'}
						{:else if sessionResults.metrics.performance_level === 'Average'}
							{$locale === 'bn'
								? 'ভালো পারফরম্যান্স! আপনার সময় এমএস রোগীদের স্বাভাবিক সীমার মধ্যে রয়েছে। নিয়মিত অনুশীলন গতি ও দক্ষতা বাড়াতে সাহায্য করবে।'
								: 'Good performance! Your time is in the normal range for MS patients. Regular practice can help improve speed and efficiency.'}
						{:else}
							{$locale === 'bn'
								? 'অনুশীলন চালিয়ে যান। নিয়মিত ট্রেনিংয়ের মাধ্যমে প্রসেসিং স্পিড ও ভিজ্যুয়াল স্ক্যানিং অনেক উন্নত হতে পারে।'
								: 'Keep practicing! Processing speed and visual scanning can improve significantly with regular training. The Trail Making Test is excellent for building these skills.'}
						{/if}
					</p>
				</div>

				<div class="difficulty-info">
					<p>
						{difficultyChangeLabel(sessionResults.difficulty_before, sessionResults.difficulty_after)}
					</p>
					<p class="adaptation-reason">{t(sessionResults.adaptation_reason)}</p>
				</div>

				{#if sessionResults.new_badges && sessionResults.new_badges.length > 0}
					<div class="new-badges">
						<h3>{t('New Badges Earned!')}</h3>
						{#each sessionResults.new_badges as badge}
							<div class="badge">
								<span class="badge-icon">{badge.icon}</span>
								<span class="badge-name">{badge.name}</span>
							</div>
						{/each}
					</div>
				{/if}

				<div class="actions">
					<button on:click={() => goto('/training')}>{t('Back to Training')}</button>
					<button on:click={() => goto('/dashboard')}>{t('View Dashboard')}</button>
				</div>
			{/if}
		</div>
	{/if}
</div>

{#if showHelp}
	<div class="help-modal" on:click={toggleHelp} role="presentation">
		<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
		<div class="help-content" on:click|stopPropagation role="dialog" tabindex="-1" on:keydown={(e) => e.key === 'Escape' && toggleHelp()}>
			<button class="close-button" on:click={toggleHelp}>×</button>
			<h2>{t('TMT-A Success Strategies')}</h2>
			
			<div class="strategy">
				<h3>{t('Visual Scanning')}</h3>
				<p>{$locale === 'bn' ? 'একটি বৃত্তে চাপার সময়ই চোখকে পরের সংখ্যাটি খুঁজতে অভ্যস্ত করুন।' : 'Train your eyes to scan ahead. While clicking one circle, your eyes should already be locating the next number.'}</p>
			</div>
			
			<div class="strategy">
				<h3>{t('Center Clicking')}</h3>
				<p>{$locale === 'bn' ? 'দ্রুত ও নির্ভুল ফলের জন্য প্রতিটি বৃত্তের মাঝামাঝি অংশে চাপুন। কিনারায় চাপলে মিস হতে পারে।' : 'Click near the center of each circle for fastest, most accurate results. Peripheral clicks may miss.'}</p>
			</div>
			
			<div class="strategy">
				<h3>{t('Efficient Path')}</h3>
				<p>{$locale === 'bn' ? 'বৃত্তগুলোর মাঝে মাউস বা আঙুল সোজা ও মসৃণভাবে চালান। অগোছালো নড়াচড়া সময় নষ্ট করে।' : 'Your mouse/finger should move in smooth, direct lines between circles. Erratic movements waste time.'}</p>
			</div>
			
			<div class="strategy">
				<h3>{t('Pattern Recognition')}</h3>
				<p>{$locale === 'bn' ? 'ক্রমাগত সংখ্যাগুলোর ছোট ছোট গুচ্ছ লক্ষ্য করুন। এতে পথ পরিকল্পনা করা সহজ হয়।' : 'Try to notice clusters of sequential numbers. This helps you plan your path more efficiently.'}</p>
			</div>
			
			<div class="strategy">
				<h3>{t('Speed vs Accuracy')}</h3>
				<p>{$locale === 'bn' ? 'ভারসাম্য খুঁজুন। অযথা তাড়াহুড়া করলে এমন ভুল হয় যা সামান্য ধীর কিন্তু নির্ভুল হওয়ার চেয়ে বেশি ক্ষতি করে।' : 'Find the balance - rushing leads to errors which hurt your score more than going slightly slower but accurate.'}</p>
			</div>

			<div class="strategy">
				<h3>{t('Why This Matters')}</h3>
				<p>{$locale === 'bn' ? 'TMT-A মস্তিষ্ক কত দ্রুত দৃশ্যমান তথ্য প্রক্রিয়া করতে পারে এবং মোটর প্রতিক্রিয়া সমন্বয় করতে পারে তা মাপে, যা ড্রাইভিং বা পথচলার মতো দৈনন্দিন কাজে গুরুত্বপূর্ণ।' : "TMT-A measures the brain's ability to rapidly process visual information and coordinate motor responses - critical for daily activities like driving and navigation."}</p>
			</div>
		</div>
	</div>
{/if}

<style>
	.tmt-container {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem;
		min-height: 100vh;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
	}

	.loading {
		text-align: center;
		padding: 4rem 0;
		color: white;
	}

	.spinner {
		width: 50px;
		height: 50px;
		border: 4px solid rgba(255,255,255,0.3);
		border-top: 4px solid white;
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin: 0 auto 1rem;
	}

	@keyframes spin {
		0% { transform: rotate(0deg); }
		100% { transform: rotate(360deg); }
	}

	.instructions {
		text-align: center;
	}

	.instructions h1 {
		color: white;
		margin-bottom: 1rem;
		font-size: 2.5rem;
		text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
	}

	.classic-badge {
		background: linear-gradient(135deg, #FF6B6B, #C92A2A);
		color: white;
		padding: 0.75rem 2rem;
		border-radius: 25px;
		font-weight: bold;
		font-size: 1rem;
		display: inline-block;
		margin-bottom: 2rem;
		box-shadow: 0 4px 15px rgba(201, 42, 42, 0.4);
	}

	.instruction-card {
		background: white;
		border-radius: 16px;
		padding: 2.5rem;
		margin: 2rem 0;
		box-shadow: 0 8px 32px rgba(0,0,0,0.2);
		text-align: left;
	}

	.importance {
		background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
		padding: 1.5rem;
		border-radius: 12px;
		border-left: 4px solid #667eea;
		margin: 1.5rem 0;
		font-size: 1.05rem;
		line-height: 1.6;
	}

	.clinical-info {
		background: #e3f2fd;
		padding: 1.5rem;
		border-radius: 12px;
		margin: 1.5rem 0;
	}

	.clinical-info h3 {
		color: #1976d2;
		margin: 0 0 1rem 0;
	}

	.clinical-info ul {
		margin: 0;
		padding-left: 1.5rem;
	}

	.clinical-info li {
		margin-bottom: 0.5rem;
		line-height: 1.6;
	}

	.how-it-works {
		margin: 2rem 0;
	}

	.demo-sequence {
		background: #f8f9fa;
		padding: 2rem;
		border-radius: 12px;
		margin-top: 1rem;
	}

	.demo-step {
		text-align: center;
	}

	.demo-circles {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		margin: 1.5rem 0;
		flex-wrap: wrap;
	}

	.demo-circle {
		width: 60px;
		height: 60px;
		border-radius: 50%;
		border: 3px solid #667eea;
		background: white;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.5rem;
		font-weight: bold;
		color: #2c3e50;
	}

	.demo-circle.active {
		background: #FFC107;
		border-color: #FF9800;
	}

	.demo-arrow {
		font-size: 2rem;
		color: #667eea;
		font-weight: bold;
	}

	.test-details {
		margin: 2rem 0;
	}

	.details-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
		margin-top: 1rem;
	}

	.detail-item {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		padding: 1.5rem;
		border-radius: 12px;
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.detail-icon {
		font-size: 2rem;
	}

	.detail-text {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.detail-text strong {
		font-size: 1.1rem;
	}

	.detail-text span {
		font-size: 0.9rem;
		opacity: 0.9;
	}

	.tips {
		background: #fff3cd;
		padding: 1.5rem;
		border-radius: 12px;
		margin: 2rem 0;
	}

	.tips h3 {
		margin: 0 0 1rem 0;
		color: #856404;
	}

	.tips ul {
		margin: 0;
		padding-left: 1.5rem;
	}

	.tips li {
		margin-bottom: 0.5rem;
		color: #856404;
		line-height: 1.6;
	}

	.performance-guide {
		margin: 2rem 0;
	}

	.norm-scale {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		margin-top: 1rem;
	}

	.norm-item {
		padding: 0.75rem 1rem;
		border-radius: 8px;
		font-weight: 600;
		text-align: center;
	}

	.norm-item.excellent {
		background: linear-gradient(135deg, #4CAF50, #45a049);
		color: white;
	}

	.norm-item.good {
		background: linear-gradient(135deg, #8BC34A, #7CB342);
		color: white;
	}

	.norm-item.average {
		background: linear-gradient(135deg, #FFC107, #FFB300);
		color: #000;
	}

	.norm-item.needs-practice {
		background: linear-gradient(135deg, #FF9800, #FB8C00);
		color: white;
	}

	.norm-note {
		margin-top: 0.5rem;
		font-size: 0.85rem;
		color: #666;
		font-style: italic;
		text-align: center;
	}

	.start-button {
		background: linear-gradient(135deg, #4CAF50, #45a049);
		color: white;
		border: none;
		padding: 1.25rem 3.5rem;
		font-size: 1.4rem;
		font-weight: bold;
		border-radius: 12px;
		cursor: pointer;
		margin-top: 2rem;
		transition: all 0.3s;
		box-shadow: 0 4px 15px rgba(76, 175, 80, 0.4);
	}

	.start-button:hover {
		transform: translateY(-3px);
		box-shadow: 0 6px 25px rgba(76, 175, 80, 0.6);
	}

	.ready-screen {
		background: white;
		border-radius: 16px;
		padding: 4rem 2rem;
		text-align: center;
		box-shadow: 0 8px 32px rgba(0,0,0,0.2);
	}

	.ready-screen h2 {
		color: #667eea;
		margin-bottom: 1rem;
	}

	.ready-message {
		color: #666;
		font-size: 1.2rem;
		margin-bottom: 2rem;
	}

	.ready-sequence {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		margin: 2rem 0;
	}

	.ready-circle {
		width: 70px;
		height: 70px;
		border-radius: 50%;
		border: 4px solid #667eea;
		background: white;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 2rem;
		font-weight: bold;
		color: #2c3e50;
	}

	.ready-arrow {
		font-size: 2.5rem;
		color: #667eea;
		font-weight: bold;
	}

	.ready-dots {
		font-size: 2rem;
		color: #667eea;
		font-weight: bold;
	}

	.countdown {
		font-size: 5rem;
		font-weight: bold;
		color: #667eea;
		margin-top: 2rem;
		animation: pulse 1s ease-in-out infinite;
	}

	@keyframes pulse {
		0%, 100% { transform: scale(1); opacity: 1; }
		50% { transform: scale(1.1); opacity: 0.7; }
	}

	.testing-screen {
		background: white;
		border-radius: 16px;
		padding: 1.5rem;
		box-shadow: 0 8px 32px rgba(0,0,0,0.2);
		position: relative;
	}

	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		flex-wrap: wrap;
		gap: 1rem;
	}

	.progress-info {
		display: flex;
		gap: 0.5rem;
		align-items: center;
		flex-wrap: wrap;
	}

	.next-badge {
		background: linear-gradient(135deg, #FFC107, #FF9800);
		color: #000;
		padding: 0.5rem 1rem;
		border-radius: 20px;
		font-weight: 700;
		font-size: 1rem;
		animation: pulse 1.5s ease-in-out infinite;
	}

	.progress-badge {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		padding: 0.5rem 1rem;
		border-radius: 20px;
		font-weight: 600;
		font-size: 0.9rem;
	}

	.errors-badge {
		background: linear-gradient(135deg, #f44336, #d32f2f);
		color: white;
		padding: 0.5rem 1rem;
		border-radius: 20px;
		font-weight: 600;
		font-size: 0.9rem;
	}

	.timer-display {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		background: #f8f9fa;
		padding: 0.75rem 1.5rem;
		border-radius: 25px;
		box-shadow: 0 2px 8px rgba(0,0,0,0.1);
	}

	.timer-icon {
		font-size: 1.5rem;
	}

	.timer-value {
		font-size: 1.5rem;
		font-weight: bold;
		color: #667eea;
		min-width: 70px;
		text-align: center;
	}

	.canvas-container {
		background: #f8f9fa;
		border-radius: 12px;
		padding: 1rem;
		margin: 1rem 0;
		display: flex;
		justify-content: center;
		align-items: center;
		min-height: 500px;
	}

	canvas {
		cursor: pointer;
		border-radius: 8px;
		box-shadow: 0 4px 12px rgba(0,0,0,0.1);
	}

	.instruction-bar {
		background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
		padding: 1rem;
		border-radius: 12px;
		text-align: center;
	}

	.instruction-bar p {
		margin: 0.25rem 0;
		color: #555;
	}

	.current-target {
		font-size: 1.2rem;
	}

	.current-target strong {
		color: #FF9800;
		font-size: 1.5rem;
	}

	.help-button-floating {
		position: absolute;
		top: 1rem;
		right: 1rem;
		width: 45px;
		height: 45px;
		border-radius: 50%;
		border: 2px solid #667eea;
		background: white;
		color: #667eea;
		font-size: 1.5rem;
		font-weight: bold;
		cursor: pointer;
		transition: all 0.3s;
		box-shadow: 0 2px 8px rgba(0,0,0,0.1);
	}

	.help-button-floating:hover {
		background: #667eea;
		color: white;
		transform: scale(1.1);
	}

	.complete-screen {
		background: white;
		border-radius: 16px;
		padding: 3rem 2rem;
		box-shadow: 0 8px 32px rgba(0,0,0,0.2);
		text-align: center;
	}

	.complete-screen h1 {
		color: #667eea;
		margin-bottom: 2rem;
	}

	.performance-badge {
		display: inline-block;
		border: 4px solid;
		border-radius: 16px;
		padding: 1.5rem 3rem;
		margin-bottom: 2rem;
	}

	.perf-level {
		font-size: 2rem;
		font-weight: bold;
		margin-bottom: 0.5rem;
	}

	.perf-time {
		font-size: 1.5rem;
		opacity: 0.9;
	}

	.results-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
		gap: 1rem;
		margin: 2rem 0;
	}

	.result-card {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		padding: 1.5rem;
		border-radius: 12px;
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
	}

	.result-card.primary {
		background: linear-gradient(135deg, #4CAF50, #45a049);
		grid-column: span 2;
	}

	.result-icon {
		font-size: 2.5rem;
		margin-bottom: 0.5rem;
	}

	.result-value {
		font-size: 2.5rem;
		font-weight: bold;
		margin-bottom: 0.5rem;
	}

	.result-label {
		font-size: 1rem;
		opacity: 0.95;
		margin-bottom: 0.25rem;
	}

	.result-sublabel {
		font-size: 0.85rem;
		opacity: 0.8;
	}

	.performance-breakdown {
		background: #f8f9fa;
		padding: 1.5rem;
		border-radius: 12px;
		margin: 2rem 0;
	}

	.performance-breakdown h3 {
		margin: 0 0 1rem 0;
		color: #2c3e50;
	}

	.breakdown-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
	}

	.breakdown-item {
		display: flex;
		justify-content: space-between;
		padding: 0.75rem;
		background: white;
		border-radius: 8px;
	}

	.breakdown-item .value {
		font-weight: bold;
		color: #667eea;
	}

	.breakdown-item .value.success {
		color: #4CAF50;
	}

	.breakdown-item .value.error {
		color: #f44336;
	}

	.clinical-context {
		background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
		padding: 1.5rem;
		border-radius: 12px;
		margin: 2rem 0;
		text-align: left;
	}

	.clinical-context h3 {
		color: #667eea;
		margin: 0 0 1rem 0;
	}

	.clinical-context p {
		margin: 0;
		line-height: 1.7;
		color: #555;
	}

	.difficulty-info {
		background: #e3f2fd;
		padding: 1.5rem;
		border-radius: 12px;
		margin: 2rem 0;
	}

	.adaptation-reason {
		color: #666;
		font-size: 0.9rem;
		margin-top: 0.5rem;
	}

	.new-badges {
		background: #fff3e0;
		padding: 1.5rem;
		border-radius: 12px;
		margin: 2rem 0;
	}

	.badge {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 0.75rem;
		background: white;
		border-radius: 8px;
		margin: 0.5rem 0;
	}

	.badge-icon {
		font-size: 2rem;
	}

	.actions {
		display: flex;
		gap: 1rem;
		justify-content: center;
		margin-top: 2rem;
		flex-wrap: wrap;
	}

	.actions button {
		padding: 0.8rem 2rem;
		border: none;
		border-radius: 8px;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.3s;
	}

	.actions button:first-child {
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
	}

	.actions button:last-child {
		background: linear-gradient(135deg, #4CAF50, #45a049);
		color: white;
	}

	.actions button:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0,0,0,0.2);
	}

	.help-modal {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.7);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
	}

	.help-content {
		background: white;
		padding: 2rem;
		border-radius: 16px;
		max-width: 600px;
		max-height: 80vh;
		overflow-y: auto;
		position: relative;
		box-shadow: 0 8px 32px rgba(0,0,0,0.3);
	}

	.close-button {
		position: absolute;
		top: 1rem;
		right: 1rem;
		width: 40px;
		height: 40px;
		border: none;
		background: #f44336;
		color: white;
		font-size: 1.5rem;
		border-radius: 50%;
		cursor: pointer;
	}

	.help-content h2 {
		color: #667eea;
		margin-bottom: 1.5rem;
	}

	.strategy {
		margin-bottom: 1.5rem;
		padding: 1rem;
		background: #f8f9fa;
		border-radius: 8px;
		border-left: 4px solid #667eea;
	}

	.strategy h3 {
		margin: 0 0 0.5rem 0;
		color: #2c3e50;
	}

	.strategy p {
		margin: 0;
		color: #555;
		line-height: 1.6;
	}
</style>

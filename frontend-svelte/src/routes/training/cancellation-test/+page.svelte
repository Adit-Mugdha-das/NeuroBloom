<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { API_BASE_URL } from '$lib/api';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
	import { locale, localeText } from '$lib/i18n';
	import { buildPracticePayload, getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let gamePhase = 'loading'; // loading | intro | playing | results
	let trialData = null;
	let grid = [];
	let targetItems = [];
	let markedPositions = [];
	let startTime = null;
	let elapsedTime = 0;
	let timerInterval = null;
	let taskId = null;

	let results = null;
	let earnedBadges = [];
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';
	let recordedTrialData = null;

	let loadError = false;
	let saveError = false;

	// Fixed large cell size for accessibility (visual impairments)
	const cellSize = '55px';
	const cellFontSize = '1.2rem';

	function lt(en, bn) {
		return localeText({ en, bn }, $locale);
	}

	function formatTime(seconds) {
		const mins = Math.floor(seconds / 60);
		const secs = seconds % 60;
		return `${mins}:${secs.toString().padStart(2, '0')}`;
	}

	function performanceLabel(rating) {
		const map = {
			excellent:    lt('Excellent', 'অসাধারণ'),
			good:         lt('Good', 'ভালো'),
			average:      lt('Average', 'মোটামুটি'),
			below_average: lt('Below Average', 'নিচের গড়'),
			poor:         lt('Poor', 'দুর্বল')
		};
		return map[rating] || rating;
	}

	onMount(async () => {
		if (!$user) {
			goto('/login');
			return;
		}
		await loadTrial();
	});

	async function loadTrial() {
		try {
			loadError = false;
			const response = await fetch(
				`${API_BASE_URL}/api/training/tasks/cancellation-test/generate/${$user.id}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					credentials: 'include'
				}
			);
			if (!response.ok) throw new Error('Failed to load trial');
			const data = await response.json();
			trialData = structuredClone(data.trial_data);
			recordedTrialData = structuredClone(data.trial_data);
			grid = trialData.grid;
			targetItems = trialData.target_items;
			elapsedTime = 0;
			gamePhase = 'intro';
		} catch (_) {
			loadError = true;
			gamePhase = 'intro';
		}
	}

	function startGame(nextMode = TASK_PLAY_MODE.RECORDED) {
		if (timerInterval) {
			clearInterval(timerInterval);
			timerInterval = null;
		}

		playMode = nextMode;
		practiceStatusMessage = '';
		trialData =
			nextMode === TASK_PLAY_MODE.PRACTICE
				? buildPracticePayload('cancellation-test', { trial_data: recordedTrialData }).trial_data
				: structuredClone(recordedTrialData);
		grid = trialData.grid;
		targetItems = trialData.target_items;
		markedPositions = [];
		startTime = Date.now();
		elapsedTime = 0;
		gamePhase = 'playing';
		timerInterval = setInterval(() => {
			elapsedTime = Math.floor((Date.now() - startTime) / 1000);
		}, 100);
	}

	function leavePractice(completed = false) {
		if (timerInterval) {
			clearInterval(timerInterval);
			timerInterval = null;
		}

		trialData = structuredClone(recordedTrialData);
		grid = trialData.grid;
		targetItems = trialData.target_items;
		playMode = TASK_PLAY_MODE.RECORDED;
		practiceStatusMessage = completed ? getPracticeCopy($locale).complete : '';
		markedPositions = [];
		startTime = null;
		elapsedTime = 0;
		gamePhase = 'intro';
	}

	function toggleCell(row, col, item) {
		const existingIndex = markedPositions.findIndex(p => p.row === row && p.col === col);
		if (existingIndex >= 0) {
			markedPositions = markedPositions.filter((_, i) => i !== existingIndex);
		} else {
			markedPositions = [...markedPositions, { row, col, item }];
		}
	}

	function isMarked(row, col) {
		return markedPositions.some(p => p.row === row && p.col === col);
	}

	function finishGame() {
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
		saveError = false;
		const completionTime = (Date.now() - startTime) / 1000;
		taskId = $page.url.searchParams.get('taskId');
		try {
			const response = await fetch(
				`${API_BASE_URL}/api/training/tasks/cancellation-test/submit/${$user.id}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					credentials: 'include',
					body: JSON.stringify({
						marked_positions: markedPositions,
						target_positions: trialData.target_positions,
						completion_time: completionTime,
						suggested_time: trialData.suggested_time,
						difficulty: trialData.difficulty,
						task_id: taskId
					})
				}
			);
			if (!response.ok) throw new Error('Failed to submit results');
			results = await response.json();
			earnedBadges = results.new_badges || [];
			gamePhase = 'results';
		} catch (_) {
			saveError = true;
			gamePhase = 'results';
		}
	}

	function restartTask() {
		gamePhase = 'loading';
		results = null;
		earnedBadges = [];
		loadTrial();
	}
</script>

<div class="ct-page" data-localize-skip>
	<div class="ct-wrapper">

		{#if gamePhase === 'loading'}
			<LoadingSkeleton />

		{:else if gamePhase === 'intro'}

			<!-- Header Card -->
			<div class="header-card">
				<div class="header-content">
					<div class="header-text">
						<h1 class="task-title">{lt('Cancellation Test', 'ক্যান্সেলেশন টেস্ট')}</h1>
						<p class="task-domain">{lt('Visual Scanning · Sustained Attention', 'ভিজ্যুয়াল স্ক্যানিং · টেকসই মনোযোগ')}</p>
					</div>
					<DifficultyBadge difficulty={trialData?.difficulty || 1} domain="Visual Scanning" />
				</div>
			</div>

			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} />
			{/if}

			{#if loadError}
				<div class="error-card">
					<p>{lt('Failed to load task. Please try again.', 'টাস্ক লোড করতে ব্যর্থ। আবার চেষ্টা করুন।')}</p>
					<button class="start-button" on:click={loadTrial}>
						{lt('Retry', 'আবার চেষ্টা করুন')}
					</button>
				</div>
			{:else if trialData}

				<!-- Task Concept -->
				<div class="card task-concept">
					<div class="concept-badge">
						<span class="badge-label">{lt('Visual Scanning', 'ভিজ্যুয়াল স্ক্যানিং')}</span>
						<span>{lt('Sustained Attention', 'টেকসই মনোযোগ')}</span>
					</div>
					<p class="concept-desc">
						{trialData.instructions}
					</p>
				</div>

				<!-- Target Display -->
				<div class="card">
					<h2 class="section-title">{lt('Your Target', 'আপনার লক্ষ্য')}</h2>
					<p class="target-subtext">{lt('Find and click every instance of the following in the grid:', 'গ্রিডে নিচের প্রতিটি উদাহরণ খুঁজে ক্লিক করুন:')}</p>
					<div class="target-chips">
						{#each targetItems as t}
							<div class="target-chip">{t}</div>
						{/each}
					</div>
					<div class="target-count-row">
						<span class="target-count-label">{lt('Total targets in grid:', 'গ্রিডে মোট লক্ষ্য:')}</span>
						<span class="target-count-value">{trialData.target_count}</span>
					</div>
				</div>

				<!-- Rules Card -->
				<div class="card">
					<h2 class="section-title">{lt('Rules', 'নিয়মাবলী')}</h2>
					<div class="rules-list">
						<div class="rule-item">
							<div class="rule-num">1</div>
							<div class="rule-text">{lt('Click every cell that contains a target item — do not skip any', 'প্রতিটি টার্গেট সেল ক্লিক করুন — কোনোটি বাদ দেবেন না')}</div>
						</div>
						<div class="rule-item">
							<div class="rule-num">2</div>
							<div class="rule-text">{lt('Click a marked cell again to unmark it if you made a mistake', 'ভুল করলে চিহ্নিত সেলটি আবার ক্লিক করে চিহ্ন তুলে নিন')}</div>
						</div>
						<div class="rule-item">
							<div class="rule-num">3</div>
							<div class="rule-text">{lt('Scan systematically — left to right, row by row', 'পদ্ধতিগতভাবে স্ক্যান করুন — বাম থেকে ডানে, সারি থেকে সারি')}</div>
						</div>
						<div class="rule-item">
							<div class="rule-num">4</div>
							<div class="rule-text">{lt('No time limit — prioritize accuracy over speed', 'কোনো সময়সীমা নেই — গতির চেয়ে নির্ভুলতাকে অগ্রাধিকার দিন')}</div>
						</div>
					</div>
				</div>

				<!-- Info Grid -->
				<div class="info-grid">
					<!-- Task Details -->
					<div class="card">
						<h3 class="card-title">{lt('Task Details', 'টাস্কের বিবরণ')}</h3>
						<div class="details-list">
							<div class="detail-row">
								<span>{lt('Stimulus Type', 'উদ্দীপক ধরন')}</span>
								<strong>{trialData.use_symbols ? lt('Symbols', 'প্রতীক') : lt('Letters', 'অক্ষর')}</strong>
							</div>
							<div class="detail-row">
								<span>{lt('Targets to Find', 'খুঁজতে হবে')}</span>
								<strong>{trialData.target_count}</strong>
							</div>
							<div class="detail-row">
								<span>{lt('Difficulty', 'কঠিনতা')}</span>
								<strong>{lt(`Level ${trialData.difficulty} / 10`, `স্তর ${trialData.difficulty} / ১০`)}</strong>
							</div>
							<div class="detail-row">
								<span>{lt('No Time Limit', 'সময়সীমা নেই')}</span>
								<strong>{lt('Self-paced', 'নিজের গতিতে')}</strong>
							</div>
						</div>
					</div>
					<!-- Scoring Info -->
					<div class="card">
						<h3 class="card-title">{lt('How You Are Scored', 'স্কোরিং পদ্ধতি')}</h3>
						<div class="details-list">
							<div class="detail-row">
								<span>{lt('Primary Metric', 'প্রাথমিক পরিমাপ')}</span>
								<strong>{lt('Accuracy %', 'নির্ভুলতা %')}</strong>
							</div>
							<div class="detail-row">
								<span>{lt('Also Tracked', 'অতিরিক্ত পরিমাপ')}</span>
								<strong>{lt('Completion time', 'সম্পন্ন সময়')}</strong>
							</div>
							<div class="detail-row">
								<span>{lt('Penalised For', 'জরিমানা')}</span>
								<strong>{lt('Misses + false alarms', 'বাদ + ভুল ক্লিক')}</strong>
							</div>
							<div class="detail-row">
								<span>{lt('Spatial Check', 'স্থানিক পরীক্ষা')}</span>
								<strong>{lt('Left vs Right bias', 'বাম বনাম ডান পক্ষপাতিত্ব')}</strong>
							</div>
						</div>
					</div>
				</div>

				<!-- Clinical Basis -->
				<div class="clinical-info">
					<div class="clinical-header">
						<div class="clinical-badge">{lt('Clinical Basis', 'ক্লিনিকাল ভিত্তি')}</div>
						<h3>{lt('Validated MS Visual Attention Assessment', 'MS-এর জন্য যাচাইকৃত ভিজ্যুয়াল অ্যাটেনশন মূল্যায়ন')}</h3>
					</div>
					<p>
						{lt(
							'The Cancellation Test (Mesulam, 1985) measures sustained visual attention and unilateral spatial neglect. In MS, asymmetric target detection — more misses on one side — may indicate hemispatial attention deficits correlated with white matter lesion location. Scanning efficiency predicts reading speed and performance of daily functional tasks requiring visual vigilance.',
							'ক্যান্সেলেশন টেস্ট (Mesulam, 1985) টেকসই ভিজ্যুয়াল মনোযোগ এবং একতরফা স্থানিক অবহেলা পরিমাপ করে। MS-এ একটি পাশে বেশি লক্ষ্য বাদ পড়লে সেটি হেমিস্পেশিয়াল অ্যাটেনশন ঘাটতি নির্দেশ করতে পারে।'
						)}
					</p>
				</div>

				<TaskPracticeActions
					locale={$locale}
					startLabel={lt('Start Task', 'টাস্ক শুরু করুন')}
					statusMessage={practiceStatusMessage}
					on:start={() => startGame(TASK_PLAY_MODE.RECORDED)}
					on:practice={() => startGame(TASK_PLAY_MODE.PRACTICE)}
				/>

			{:else}
				<LoadingSkeleton />
			{/if}

		{:else if gamePhase === 'playing'}

			<div class="game-card" style="--cell-size: {cellSize}; --cell-font-size: {cellFontSize};">
				{#if playMode === TASK_PLAY_MODE.PRACTICE}
					<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
				{/if}

				<!-- Status Bar -->
				<div class="game-status-bar">
					<div class="find-label-group">
						<span class="find-label">{lt('Find:', 'খুঁজুন:')}</span>
						<div class="find-chips">
							{#each targetItems as t}
								<span class="find-chip">{t}</span>
							{/each}
						</div>
					</div>
					<div class="game-stats">
						<div class="stat-pill progress-pill">
							<span class="stat-value">{markedPositions.length}</span>
							<span class="stat-sep">/</span>
							<span class="stat-total">{trialData.target_count}</span>
							<span class="stat-label">{lt('marked', 'চিহ্নিত')}</span>
						</div>
						<div class="stat-pill timer-pill">
							<span class="timer-value">{formatTime(elapsedTime)}</span>
							<span class="stat-label">{lt('elapsed', 'অতিবাহিত')}</span>
						</div>
					</div>
				</div>

				<!-- Grid Container -->
				<div class="grid-container">
					<div class="grid-inner">
						{#each grid as row, rowIndex}
							<div class="grid-row">
								{#each row as item, colIndex}
									<button
										on:click={() => toggleCell(rowIndex, colIndex, item)}
										class="grid-cell"
										class:marked={isMarked(rowIndex, colIndex)}
									>
										{item}
									</button>
								{/each}
							</div>
						{/each}
					</div>
				</div>

				<!-- Finish Button -->
				<div class="finish-row">
					<button class="finish-btn" on:click={finishGame}>
						{lt('Finish Task', 'টাস্ক শেষ করুন')}
					</button>
				</div>
			</div>

		{:else if gamePhase === 'results'}

			<!-- Results Header -->
			<div class="results-header">
				<div class="score-pill">
					<span class="score-label">{lt('Score', 'স্কোর')}</span>
					<span class="score-value">{results ? results.score : '—'}</span>
					<span class="score-max">%</span>
				</div>
				<p class="results-subtitle">
					{lt('Cancellation Test Complete', 'ক্যান্সেলেশন টেস্ট সম্পন্ন')} ·
					{results ? performanceLabel(results.performance_rating) : ''}
				</p>
			</div>

			{#if saveError}
				<div class="warn-card">
					{lt('Error saving results. Your progress may not have been recorded.', 'ফলাফল সংরক্ষণে ত্রুটি। আপনার অগ্রগতি রেকর্ড নাও হতে পারে।')}
				</div>
			{/if}

			{#if results}
				<!-- Key Metrics -->
				<div class="metrics-grid">
					<div class="metric-card metric-green">
						<div class="metric-value">{results.accuracy.toFixed(1)}%</div>
						<div class="metric-label">{lt('Accuracy', 'নির্ভুলতা')}</div>
					</div>
					<div class="metric-card metric-blue">
						<div class="metric-value">{results.targets_found}<span class="metric-denom">/{results.total_targets}</span></div>
						<div class="metric-label">{lt('Targets Found', 'লক্ষ্য সনাক্ত')}</div>
					</div>
					<div class="metric-card metric-amber">
						<div class="metric-value">{results.completion_time.toFixed(1)}s</div>
						<div class="metric-label">{lt('Completion Time', 'সম্পন্ন সময়')}</div>
					</div>
					<div class="metric-card metric-red">
						<div class="metric-value">{results.targets_missed + results.false_alarms}</div>
						<div class="metric-label">{lt('Total Errors', 'মোট ত্রুটি')}</div>
					</div>
				</div>

				<!-- Error Breakdown -->
				<div class="card">
					<h3 class="card-title">{lt('Error Breakdown', 'ত্রুটির বিশ্লেষণ')}</h3>
					<div class="details-list">
						<div class="detail-row">
							<span>{lt('Targets Missed', 'বাদ পড়া লক্ষ্য')}</span>
							<strong class="error-miss">{results.targets_missed}</strong>
						</div>
						<div class="detail-row">
							<span>{lt('False Alarms', 'ভুল চিহ্নিতকরণ')}</span>
							<strong class="error-false">{results.false_alarms}</strong>
						</div>
						<div class="detail-row">
							<span>{lt('Performance Rating', 'পারফরম্যান্স রেটিং')}</span>
							<strong>{performanceLabel(results.performance_rating)}</strong>
						</div>
					</div>
				</div>

				<!-- Spatial Analysis -->
				{#if results.spatial_analysis}
					<div class="card">
						<h3 class="card-title">{lt('Spatial Pattern Analysis', 'স্থানিক প্যাটার্ন বিশ্লেষণ')}</h3>
						<div class="spatial-grid">
							<div class="spatial-side">
								<div class="spatial-label">{lt('Left Side', 'বাম পাশ')}</div>
								<div class="spatial-value">{results.spatial_analysis.left_accuracy}%</div>
							</div>
							<div class="spatial-divider"></div>
							<div class="spatial-side">
								<div class="spatial-label">{lt('Right Side', 'ডান পাশ')}</div>
								<div class="spatial-value">{results.spatial_analysis.right_accuracy}%</div>
							</div>
						</div>

						{#if results.spatial_analysis.neglect_detected}
							<div class="neglect-warn">
								<div class="neglect-title">{lt('Asymmetric Pattern Detected', 'অপ্রতিসম প্যাটার্ন সনাক্ত')}</div>
								<p class="neglect-text">
									{lt(
										`You missed more targets on the ${results.spatial_analysis.neglect_side} side. Try to scan both sides of the grid equally.`,
										`আপনি ${results.spatial_analysis.neglect_side} পাশে বেশি লক্ষ্য বাদ দিয়েছেন। গ্রিডের উভয় পাশ সমানভাবে স্ক্যান করার চেষ্টা করুন।`
									)}
								</p>
							</div>
						{:else}
							<div class="neglect-ok">
								<div class="neglect-ok-title">{lt('Balanced Scanning Pattern', 'সুষম স্ক্যানিং প্যাটার্ন')}</div>
								<p class="neglect-ok-text">
									{lt('You scanned both sides of the grid evenly.', 'আপনি গ্রিডের উভয় পাশ সমানভাবে স্ক্যান করেছেন।')}
								</p>
							</div>
						{/if}
					</div>
				{/if}

				<!-- Feedback -->
				<div class="card">
					<h3 class="card-title">{lt('Feedback', 'প্রতিক্রিয়া')}</h3>
					<p class="feedback-text">{results.feedback}</p>
				</div>

				<!-- Difficulty Adjustment -->
				{#if results.adaptation_reason}
					<div class="adaptation-card">
						<div class="adaptation-label">{lt('Difficulty Adjustment', 'কঠিনতা সমন্বয়')}</div>
						<p class="adaptation-text">{results.adaptation_reason}</p>
					</div>
				{/if}
			{/if}

			<!-- Action Buttons -->
			<div class="action-buttons">
				<button class="start-button" on:click={() => goto('/dashboard')}>
					{lt('Return to Dashboard', 'ড্যাশবোর্ডে ফিরুন')}
				</button>
				<button class="btn-secondary" on:click={restartTask}>
					{lt('Try Again', 'আবার চেষ্টা করুন')}
				</button>
			</div>

		{/if}
	</div>
</div>

{#if earnedBadges.length > 0}
	<BadgeNotification badges={earnedBadges} />
{/if}

<style>
	/* ── Page Layout ─────────────────────────────────── */
	.ct-page {
		min-height: 100vh;
		background: #C8DEFA;
		padding: 1.5rem;
	}

	.ct-wrapper {
		max-width: 1200px;
		margin: 0 auto;
	}

	/* ── Shared Card ──────────────────────────────────── */
	.card {
		background: white;
		border-radius: 16px;
		padding: 1.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
		margin-bottom: 1rem;
	}

	/* ── Header Card ─────────────────────────────────── */
	.header-card {
		background: white;
		border-radius: 16px;
		padding: 1.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
		margin-bottom: 1rem;
	}

	.header-content {
		display: flex;
		align-items: center;
		justify-content: space-between;
		flex-wrap: wrap;
		gap: 1rem;
	}

	.task-title {
		font-size: 1.75rem;
		font-weight: 700;
		color: #1a1a2e;
		margin: 0 0 0.25rem 0;
	}

	.task-domain {
		font-size: 0.875rem;
		color: #0369a1;
		font-weight: 500;
		margin: 0;
	}

	/* ── Error / Warn ─────────────────────────────────── */
	.error-card {
		background: #fee2e2;
		border: 2px solid #fca5a5;
		border-radius: 16px;
		padding: 2rem;
		text-align: center;
		color: #991b1b;
		margin-bottom: 1rem;
	}

	.warn-card {
		background: #fff7ed;
		border: 2px solid #fed7aa;
		border-radius: 12px;
		padding: 1rem 1.25rem;
		color: #92400e;
		font-size: 0.875rem;
		margin-bottom: 1rem;
	}

	/* ── Task Concept ─────────────────────────────────── */
	.task-concept { margin-bottom: 1rem; }

	.concept-badge {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		background: linear-gradient(135deg, #075985 0%, #0369a1 100%);
		color: white;
		padding: 0.4rem 0.9rem;
		border-radius: 2rem;
		font-size: 0.813rem;
		font-weight: 600;
		margin-bottom: 1rem;
	}

	.badge-label { font-weight: 700; letter-spacing: 0.04em; }
	.concept-desc { color: #4b5563; font-size: 0.938rem; line-height: 1.6; margin: 0; }

	/* ── Target Display ───────────────────────────────── */
	.section-title {
		font-size: 1.125rem;
		font-weight: 600;
		color: #1a1a2e;
		margin: 0 0 0.5rem 0;
	}

	.target-subtext {
		color: #6b7280;
		font-size: 0.875rem;
		margin: 0 0 1rem 0;
	}

	.target-chips {
		display: flex;
		flex-wrap: wrap;
		gap: 0.625rem;
		margin-bottom: 1rem;
	}

	.target-chip {
		background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
		border: 2px solid #0369a1;
		border-radius: 10px;
		padding: 0.5rem 1.25rem;
		font-size: 1.5rem;
		font-weight: 800;
		color: #075985;
		min-width: 3rem;
		text-align: center;
	}

	.target-count-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding-top: 0.75rem;
		border-top: 1px solid #f0f9ff;
	}

	.target-count-label { font-size: 0.875rem; color: #6b7280; }
	.target-count-value { font-size: 0.875rem; font-weight: 700; color: #0369a1; }

	/* ── Rules List ───────────────────────────────────── */
	.rules-list { display: flex; flex-direction: column; gap: 0.75rem; }

	.rule-item {
		display: flex;
		align-items: flex-start;
		gap: 0.875rem;
		background: #f0f9ff;
		border-radius: 10px;
		padding: 0.875rem 1rem;
	}

	.rule-num {
		min-width: 2rem;
		height: 2rem;
		background: linear-gradient(135deg, #075985 0%, #0369a1 100%);
		color: white;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.875rem;
		font-weight: 700;
		flex-shrink: 0;
	}

	.rule-text { font-size: 0.9rem; color: #374151; line-height: 1.5; }

	/* ── Info Grid ────────────────────────────────────── */
	.info-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
		margin-bottom: 1rem;
	}

	.card-title { font-size: 1rem; font-weight: 600; color: #1a1a2e; margin: 0 0 1rem 0; }

	/* ── Details List ─────────────────────────────────── */
	.details-list { display: flex; flex-direction: column; gap: 0.625rem; }

	.detail-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		font-size: 0.875rem;
		padding-bottom: 0.625rem;
		border-bottom: 1px solid #f3f4f6;
	}

	.detail-row:last-child { border-bottom: none; padding-bottom: 0; }
	.detail-row span   { color: #6b7280; }
	.detail-row strong { color: #1a1a2e; text-align: right; max-width: 65%; }

	/* ── Clinical Info ────────────────────────────────── */
	.clinical-info {
		background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
		border: 1px solid #bbf7d0;
		border-radius: 16px;
		padding: 1.5rem;
		margin-bottom: 1rem;
	}

	.clinical-header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 0.75rem;
	}

	.clinical-badge {
		background: #16a34a;
		color: white;
		padding: 0.2rem 0.7rem;
		border-radius: 1rem;
		font-size: 0.75rem;
		font-weight: 600;
	}

	.clinical-header h3 { font-size: 1rem; font-weight: 600; color: #14532d; margin: 0; }
	.clinical-info p    { font-size: 0.875rem; color: #166534; line-height: 1.6; margin: 0; }

	/* ── Game Card ────────────────────────────────────── */
	.game-card {
		background: white;
		border-radius: 16px;
		padding: 1.5rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
	}

	/* ── Game Status Bar ──────────────────────────────── */
	.game-status-bar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		margin-bottom: 1.5rem;
		flex-wrap: wrap;
	}

	.find-label-group {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		flex-wrap: wrap;
	}

	.find-label {
		font-size: 1rem;
		font-weight: 700;
		color: #075985;
	}

	.find-chips { display: flex; gap: 0.5rem; flex-wrap: wrap; }

	.find-chip {
		background: linear-gradient(135deg, #075985 0%, #0369a1 100%);
		color: white;
		padding: 0.25rem 0.75rem;
		border-radius: 0.5rem;
		font-size: 1.125rem;
		font-weight: 700;
	}

	.game-stats { display: flex; gap: 0.75rem; align-items: center; }

	.stat-pill {
		display: flex;
		align-items: baseline;
		gap: 0.25rem;
		padding: 0.5rem 1rem;
		border-radius: 2rem;
		font-weight: 700;
	}

	.progress-pill { background: #e0f2fe; }
	.stat-value    { font-size: 1.375rem; color: #075985; }
	.stat-sep      { font-size: 1rem; color: #94a3b8; }
	.stat-total    { font-size: 1rem; color: #64748b; }
	.stat-label    { font-size: 0.75rem; color: #64748b; font-weight: 400; margin-left: 0.25rem; }

	.timer-pill   { background: #f8fafc; border: 2px solid #e2e8f0; }
	.timer-value  { font-size: 1.375rem; color: #0369a1; font-variant-numeric: tabular-nums; }

	/* ── Grid ─────────────────────────────────────────── */
	.grid-container {
		background: #f8fafc;
		border-radius: 12px;
		padding: 1rem;
		margin-bottom: 1.5rem;
		max-height: 60vh;
		overflow: auto;
	}

	.grid-inner { display: inline-block; padding: 4px; }

	.grid-row {
		display: flex;
		gap: 3px;
		margin-bottom: 3px;
	}

	.grid-row:last-child { margin-bottom: 0; }

	/* ── Grid Cell ────────────────────────────────────── */
	.grid-cell {
		width: var(--cell-size);
		height: var(--cell-size);
		min-width: var(--cell-size);
		min-height: var(--cell-size);
		max-width: var(--cell-size);
		max-height: var(--cell-size);

		border: 1px solid #cbd5e1;
		background: white;
		border-radius: 4px;
		cursor: pointer;
		font-weight: 600;
		font-size: var(--cell-font-size);
		color: #475569;

		display: flex;
		align-items: center;
		justify-content: center;
		user-select: none;
		flex-shrink: 0;
		padding: 0;

		transition: background 0.1s, border-color 0.1s, transform 0.1s;
		box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
	}

	.grid-cell:hover:not(.marked) {
		background: #f0f9ff;
		border-color: #0369a1;
		border-width: 2px;
		transform: scale(1.08);
		z-index: 10;
		box-shadow: 0 2px 6px rgba(3, 105, 161, 0.25);
	}

	.grid-cell.marked {
		background: #e0f2fe;
		border: 2px solid #0369a1;
		color: #075985;
		box-shadow: 0 2px 8px rgba(3, 105, 161, 0.3);
	}

	.grid-cell:active { transform: scale(0.97); }

	/* ── Finish Row ───────────────────────────────────── */
	.finish-row { display: flex; justify-content: center; }

	.finish-btn {
		background: linear-gradient(135deg, #059669 0%, #10b981 100%);
		color: white;
		border: none;
		border-radius: 12px;
		padding: 1rem 3rem;
		font-size: 1.125rem;
		font-weight: 600;
		cursor: pointer;
		box-shadow: 0 4px 12px rgba(5, 150, 105, 0.35);
		transition: transform 0.15s, opacity 0.15s;
	}

	.finish-btn:hover { transform: translateY(-2px); }

	/* ── Results Header ───────────────────────────────── */
	.results-header {
		background: linear-gradient(135deg, #075985 0%, #0369a1 100%);
		border-radius: 16px;
		padding: 1.75rem;
		text-align: center;
		margin-bottom: 1rem;
		box-shadow: 0 4px 12px rgba(3, 105, 161, 0.35);
	}

	.score-pill {
		display: flex;
		align-items: baseline;
		justify-content: center;
		gap: 0.375rem;
		margin-bottom: 0.5rem;
	}

	.score-label { color: rgba(255, 255, 255, 0.85); font-size: 1rem; font-weight: 500; }
	.score-value { color: white; font-size: 3rem; font-weight: 700; }
	.score-max   { color: rgba(255, 255, 255, 0.7); font-size: 1.5rem; font-weight: 500; }
	.results-subtitle { color: rgba(255, 255, 255, 0.9); font-size: 0.938rem; margin: 0; }

	/* ── Metrics Grid ─────────────────────────────────── */
	.metrics-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 0.875rem;
		margin-bottom: 1rem;
	}

	.metric-card {
		background: white;
		border-radius: 16px;
		padding: 1.25rem;
		text-align: center;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
		border-top: 4px solid #e5e7eb;
	}

	.metric-green { border-top-color: #16a34a; }
	.metric-blue  { border-top-color: #0369a1; }
	.metric-amber { border-top-color: #d97706; }
	.metric-red   { border-top-color: #dc2626; }

	.metric-value { font-size: 1.625rem; font-weight: 700; color: #1a1a2e; line-height: 1; }
	.metric-denom { font-size: 1rem; color: #9ca3af; font-weight: 400; }
	.metric-label { font-size: 0.75rem; color: #6b7280; margin-top: 0.375rem; }

	/* ── Error Highlights ─────────────────────────────── */
	.error-miss  { color: #dc2626; }
	.error-false { color: #d97706; }

	/* ── Spatial Grid ─────────────────────────────────── */
	.spatial-grid {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0;
		margin-bottom: 1rem;
		background: #f0f9ff;
		border-radius: 12px;
		padding: 1.25rem;
	}

	.spatial-side { text-align: center; flex: 1; }
	.spatial-divider { width: 1px; height: 3rem; background: #bae6fd; margin: 0 1.5rem; flex-shrink: 0; }
	.spatial-label { font-size: 0.813rem; color: #0369a1; font-weight: 600; margin-bottom: 0.25rem; }
	.spatial-value { font-size: 1.75rem; font-weight: 700; color: #075985; }

	/* ── Neglect Cards ────────────────────────────────── */
	.neglect-warn {
		background: #fef3c7;
		border: 2px solid #fcd34d;
		border-radius: 10px;
		padding: 1rem 1.25rem;
	}

	.neglect-title { font-weight: 700; color: #92400e; margin-bottom: 0.375rem; font-size: 0.938rem; }
	.neglect-text  { color: #78350f; font-size: 0.875rem; margin: 0; line-height: 1.5; }

	.neglect-ok {
		background: #f0fdf4;
		border: 2px solid #86efac;
		border-radius: 10px;
		padding: 1rem 1.25rem;
	}

	.neglect-ok-title { font-weight: 700; color: #166534; margin-bottom: 0.375rem; font-size: 0.938rem; }
	.neglect-ok-text  { color: #15803d; font-size: 0.875rem; margin: 0; }

	/* ── Feedback ─────────────────────────────────────── */
	.feedback-text { font-size: 0.938rem; color: #374151; line-height: 1.6; margin: 0; }

	/* ── Adaptation Card ──────────────────────────────── */
	.adaptation-card {
		background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
		border: 1px solid #7dd3fc;
		border-radius: 16px;
		padding: 1.25rem 1.5rem;
		margin-bottom: 1rem;
	}

	.adaptation-label { font-size: 0.875rem; font-weight: 700; color: #075985; margin-bottom: 0.375rem; }
	.adaptation-text  { font-size: 0.875rem; color: #0369a1; margin: 0; line-height: 1.5; }

	/* ── Action Buttons ───────────────────────────────── */
	.action-buttons { display: flex; gap: 1rem; margin-top: 1rem; }

	.start-button {
		flex: 1;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		color: white;
		border: none;
		border-radius: 12px;
		padding: 1rem;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
		transition: transform 0.15s;
	}

	.start-button:hover { transform: translateY(-2px); }

	.btn-secondary {
		background: white;
		color: #667eea;
		border: 2px solid #667eea;
		border-radius: 12px;
		padding: 1rem;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: transform 0.15s, background 0.15s;
	}

	.action-buttons .btn-secondary { flex: 1; }
	.btn-secondary:hover { background: #f0f9ff; transform: translateY(-2px); }

	/* ── Responsive ───────────────────────────────────── */
	@media (max-width: 768px) {
		.info-grid     { grid-template-columns: 1fr; }
		.metrics-grid  { grid-template-columns: 1fr 1fr; }
		.action-buttons { flex-direction: column; }
		.game-status-bar { flex-direction: column; align-items: flex-start; }
	}
</style>

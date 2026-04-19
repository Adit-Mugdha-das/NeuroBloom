<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { API_BASE_URL } from '$lib/api';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
import TaskReturnButton from '$lib/components/TaskReturnButton.svelte';
	import { formatNumber, locale, localeText, translateText } from '$lib/i18n';
	import { user } from '$lib/stores';
	import { buildPracticePayload, getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
import { TASK_RETURN_CONTEXT } from '$lib/task-navigation';
	import { onMount } from 'svelte';

	let gamePhase = 'loading';
	let trialData = null;
	let timeRemaining = 60;
	let timer = null;
	let startTime = null;
	let taskId = null;
	let loadError = false;
	let saveError = false;

	let currentInput = '';
	let submittedWords = [];
	let results = null;
	let earnedBadges = [];
	/** @type {string} */
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';
	let recordedTrialData = null;
	let focusHandle = null;

	function t(text) {
		return translateText(text, $locale);
	}

	function n(value, options = {}) {
		return formatNumber(value, $locale, options);
	}

	function localizedCategoryName(value = trialData?.category_name ?? '') {
		return t(value);
	}

	function localizedExamples(values = trialData?.examples ?? []) {
		return values.map((value) => t(value)).join(', ');
	}

	function categoryInstructionText() {
		if (!trialData) return '';
		if ($locale === 'bn') {
			return `আপনার কাছে ${n(trialData.time_limit_seconds || 60)} সেকেন্ড সময় আছে। এই বিভাগের যত বেশি সম্ভব শব্দ লিখুন। প্রতিটি শব্দ লিখে এন্টার চাপুন।`;
		}
		return trialData.instructions;
	}

	function categoryTipText() {
		if ($locale === 'bn') {
			return 'মূল বিভাগটিকে ছোট ছোট ভাগে ভেবে দেখুন। যেমন পেশা হলে চিকিৎসা, শিক্ষা, প্রযুক্তি, রান্না, অফিসকাজ - এভাবে ভাগ করলে দ্রুত আরও শব্দ মনে আসবে।';
		}
		return 'Try thinking of subcategories! For example, if the category is "Animals," think of farm animals, pets, wild animals, birds, etc.';
	}

	function compactSeconds(value) {
		return $locale === 'bn' ? `${n(value)}স` : `${value}s`;
	}

	function performanceLabel(rating) {
		const labels = {
			excellent: $locale === 'bn' ? 'অসাধারণ' : 'Excellent',
			good: $locale === 'bn' ? 'ভালো' : 'Good',
			average: $locale === 'bn' ? 'মোটামুটি' : 'Average',
			below_average: $locale === 'bn' ? 'আরও অনুশীলন দরকার' : 'Below Average'
		};
		return labels[rating] || rating;
	}

	function performanceFeedback() {
		if (!results) return '';
		if ($locale !== 'bn') {
			return t(results.feedback);
		}
		const parts = [];
		const uniqueCount = Number(results.unique_count) || 0;
		const duplicateCount = Number(results.duplicate_count) || 0;
		if (results.performance_rating === 'excellent') {
			parts.push(`দারুণ! আপনি ${n(uniqueCount)}টি ভিন্ন শব্দ লিখেছেন।`);
		} else if (results.performance_rating === 'good') {
			parts.push(`ভালো করেছেন! আপনি ${n(uniqueCount)}টি ভিন্ন শব্দ লিখেছেন।`);
		} else if (results.performance_rating === 'average') {
			parts.push(`আপনি ${n(uniqueCount)}টি ভিন্ন শব্দ লিখেছেন।`);
		} else {
			parts.push(`আপনি ${n(uniqueCount)}টি ভিন্ন শব্দ লিখেছেন। পরের বার আরও বেশি শব্দ ভাবার চেষ্টা করুন।`);
		}
		if (duplicateCount > 0) {
			parts.push(`নোট: ${n(duplicateCount)}টি পুনরাবৃত্ত শব্দ গণনায় ধরা হয়নি।`);
		}
		if (uniqueCount < 10) {
			parts.push('পরামর্শ: উপবিভাগ ধরে ভাবলে আরও শব্দ দ্রুত মনে আসতে পারে।');
		}
		return parts.join(' ');
	}

	function progressBadgeLabel() {
		if (submittedWords.length >= 15) {
			return $locale === 'bn' ? 'দারুণ!' : 'Outstanding!';
		}
		if (submittedWords.length >= 10) {
			return $locale === 'bn' ? 'ভালো অগ্রগতি' : 'Good Progress';
		}
		return '';
	}

	function focusWordInput() {
		document.getElementById('word-input')?.focus();
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
				`${API_BASE_URL}/api/training/tasks/category-fluency/generate/${$user.id}`,
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
			gamePhase = 'intro';
		} catch (_) {
			loadError = true;
			gamePhase = 'intro';
		}
	}

	/** @param {string} nextMode */
	function startTrial(nextMode = TASK_PLAY_MODE.RECORDED) {
		if (timer) {
			clearInterval(timer);
			timer = null;
		}
		if (focusHandle) {
			clearTimeout(focusHandle);
			focusHandle = null;
		}

		playMode = nextMode;
		practiceStatusMessage = '';
		trialData =
			nextMode === TASK_PLAY_MODE.PRACTICE
				? buildPracticePayload('category-fluency', recordedTrialData)
				: structuredClone(recordedTrialData);
		timeRemaining = trialData?.time_limit_seconds || 60;
		currentInput = '';
		submittedWords = [];
		gamePhase = 'trial';
		startTime = Date.now();
		timer = setInterval(() => {
			timeRemaining--;
			if (timeRemaining <= 0) {
				endTrial();
			}
		}, 1000);
		focusHandle = setTimeout(() => {
			focusHandle = null;
			focusWordInput();
		}, 100);
	}

	function leavePractice(completed = false) {
		if (timer) {
			clearInterval(timer);
			timer = null;
		}
		if (focusHandle) {
			clearTimeout(focusHandle);
			focusHandle = null;
		}

		trialData = structuredClone(recordedTrialData);
		playMode = TASK_PLAY_MODE.RECORDED;
		practiceStatusMessage = completed ? getPracticeCopy($locale).complete : '';
		timeRemaining = trialData?.time_limit_seconds || 60;
		startTime = null;
		currentInput = '';
		submittedWords = [];
		gamePhase = 'intro';
	}

	function submitWord() {
		if (!currentInput.trim()) return;
		const word = currentInput.trim();
		submittedWords = [...submittedWords, word];
		currentInput = '';
		if (focusHandle) {
			clearTimeout(focusHandle);
		}
		focusHandle = setTimeout(() => {
			focusHandle = null;
			focusWordInput();
		}, 0);
	}

	function handleKeyPress(event) {
		if (event.key === 'Enter') {
			event.preventDefault();
			submitWord();
		}
	}

	function removeWord(index) {
		submittedWords = submittedWords.filter((_, i) => i !== index);
	}

	async function endTrial() {
		clearInterval(timer);
		timer = null;
		const timeTaken = (Date.now() - startTime) / 1000;

		if (playMode === TASK_PLAY_MODE.PRACTICE) {
			leavePractice(true);
			return;
		}

		taskId = $page.url.searchParams.get('taskId');

		try {
			saveError = false;
			const response = await fetch(
				`${API_BASE_URL}/api/training/tasks/category-fluency/submit/${$user.id}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					credentials: 'include',
					body: JSON.stringify({
						submitted_words: submittedWords,
						time_taken_seconds: timeTaken,
						difficulty: trialData.difficulty,
						category_name: trialData.category_name,
						task_id: taskId
					})
				}
			);
			if (!response.ok) throw new Error('Failed to score trial');
			const data = await response.json();
			results = {
				normalized_score: data.score,
				unique_count: data.unique_count,
				total_submitted: data.total_submitted,
				duplicate_count: data.duplicate_count,
				performance_rating: data.performance_rating,
				words_per_second: data.words_per_second,
				feedback: data.feedback,
				should_advance: data.new_difficulty > data.old_difficulty,
				unique_words: submittedWords.filter(
					(w, i, arr) => arr.findIndex((x) => x.toLowerCase() === w.toLowerCase()) === i
				),
				invalid_words: []
			};
			if (data.new_badges && data.new_badges.length > 0) {
				earnedBadges = data.new_badges;
			}
			user.update((u) => ({
				...u,
				planning_difficulty: data.new_difficulty
			}));
			gamePhase = 'results';
		} catch (_) {
			saveError = true;
			gamePhase = 'results';
		}
	}
</script>

<div class="cf-page" data-localize-skip>
	<div class="cf-wrapper">

		{#if gamePhase === 'loading'}
			<LoadingSkeleton />

		{:else if gamePhase === 'intro'}
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />

			<!-- Header Card -->
			<div class="header-card">
				<div class="header-content">
					<div class="header-text">
						<h1 class="task-title">{t('Category Fluency')}</h1>
						<p class="task-domain">{t('Semantic Fluency · Planning / Executive Function')}</p>
					</div>
					<DifficultyBadge difficulty={trialData?.difficulty || 1} domain="Executive Planning" />
				</div>
			</div>

			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} />
			{/if}

			{#if loadError}
				<div class="error-card">
					<p>{t('Failed to load task. Please try again.')}</p>
					<button class="start-button" on:click={loadTrial}>
						{t('Retry')}
					</button>
				</div>
			{:else if trialData}

				<!-- Task Concept -->
				<div class="card task-concept">
					<div class="concept-badge">
						<span class="badge-icon">Semantic</span>
						<span>{t('Executive Planning')}</span>
					</div>
					<p class="concept-desc">
						{categoryInstructionText()}
					</p>
				</div>

				<!-- Rules Card -->
				<div class="card">
					<h2 class="section-title">{t('Rules')}</h2>
					<div class="rules-list">
						<div class="rule-item">
							<div class="rule-num">1</div>
							<div class="rule-text">
								{t('Type each word and press')} <strong>{$locale === 'bn' ? 'এন্টার' : 'Enter'}</strong> {t('to submit it')}
							</div>
						</div>
						<div class="rule-item">
							<div class="rule-num">2</div>
							<div class="rule-text">{t('Submit as many words as you can in the time allowed')}</div>
						</div>
						<div class="rule-item">
							<div class="rule-num">3</div>
							<div class="rule-text">{t('Duplicate words are automatically filtered — only unique items are counted')}</div>
						</div>
						<div class="rule-item">
							<div class="rule-num">4</div>
							<div class="rule-text">
								{t('You can remove a word before the timer ends by clicking the')} <strong>×</strong> {t('on its chip')}
							</div>
						</div>
					</div>
				</div>

				<!-- Info Grid -->
				<div class="info-grid">
					<div class="card">
						<!-- Category Highlight -->
						<h3 class="card-title">{t('Your Category')}</h3>
						<div class="category-highlight">
							<div class="category-name">{localizedCategoryName()}</div>
							<div class="category-examples">
								<span class="examples-label">{t('Examples:')}</span>
								{localizedExamples()}
							</div>
						</div>
					</div>
					<div class="card">
						<h3 class="card-title">{t('What It Measures')}</h3>
						<div class="details-list">
							<div class="detail-row">
								<span>{t('Primary Metric')}</span>
								<strong>{t('Unique words / 60s')}</strong>
							</div>
							<div class="detail-row">
								<span>{t('Cognitive Domain')}</span>
								<strong>{t('Semantic memory')}</strong>
							</div>
							<div class="detail-row">
								<span>{t('Time Limit')}</span>
								<strong>{trialData.time_limit_seconds || 60}s</strong>
							</div>
							<div class="detail-row">
								<span>{t('Difficulty')}</span>
								<strong>{t(`Level ${trialData.difficulty} / 10`)}</strong>
							</div>
						</div>
					</div>
				</div>

				<!-- Strategy Tip -->
				<div class="tip-card">
					<div class="tip-icon">TIP</div>
					<div class="tip-body">
						<div class="tip-title">{t('Subcategory Strategy')}</div>
						<p class="tip-text">{categoryTipText()}</p>
					</div>
				</div>

				<!-- Clinical Info -->
				<div class="clinical-info">
					<div class="clinical-header">
						<div class="clinical-badge">{t('Clinical Basis')}</div>
						<h3>{t('Validated MS Semantic Memory Assessment')}</h3>
					</div>
					<p>
						{t(
							'Category Fluency (Henry & Crawford, 2004) measures semantic memory access and executive retrieval strategy. Semantic fluency deficits in MS reflect reduced processing speed and working memory capacity. Benchmarks such as Animals (< 14/min) and Vegetables (< 10/min) are sensitive MS screening markers included in the MACFIMS and BICAMS batteries.'
						)}
					</p>
				</div>

				<!-- Performance Guide -->
				<div class="card perf-guide">
					<h3 class="card-title">{t('Performance Norms (unique words / 60s)')}</h3>
					<p class="perf-subtitle">{t('Based on MS patient reference data')}</p>
					<div class="norm-bars">
						<div class="norm-bar">
							<div class="norm-label">{t('Excellent')}</div>
							<div class="norm-track"><div class="norm-fill norm-excellent"></div></div>
							<div class="norm-range">&gt; 18</div>
						</div>
						<div class="norm-bar">
							<div class="norm-label">{t('Normal (MS)')}</div>
							<div class="norm-track"><div class="norm-fill norm-normal"></div></div>
							<div class="norm-range">12–18</div>
						</div>
						<div class="norm-bar">
							<div class="norm-label">{t('Impaired')}</div>
							<div class="norm-track"><div class="norm-fill norm-impaired"></div></div>
							<div class="norm-range">&lt; 12</div>
						</div>
					</div>
				</div>

				<TaskPracticeActions
					locale={$locale}
					startLabel={localeText({ en: 'Start Category Task', bn: 'বিভাগ টাস্ক শুরু করুন' }, $locale)}
					statusMessage={practiceStatusMessage}
					on:start={() => startTrial(TASK_PLAY_MODE.RECORDED)}
					on:practice={() => startTrial(TASK_PLAY_MODE.PRACTICE)}
				/>

			{:else}
				<LoadingSkeleton />
			{/if}

		{:else if gamePhase === 'trial'}

			<div class="game-card">
				{#if playMode === TASK_PLAY_MODE.PRACTICE}
					<PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
				{/if}

				<!-- Status Bar -->
				<div class="game-status-bar">
					<div class="category-display-row">
						<div class="category-display">{localizedCategoryName()}</div>
						<div class="status-pills">
							<span class="pill pill-cf">
								{$locale === 'bn'
									? `${n(submittedWords.length)}টি শব্দ`
									: `${submittedWords.length} word${submittedWords.length !== 1 ? 's' : ''}`}
							</span>
							{#if progressBadgeLabel()}
								<span class="pill pill-progress">{progressBadgeLabel()}</span>
							{/if}
						</div>
					</div>
					<div class="timer-display" class:timer-urgent={timeRemaining <= 10}>
						{compactSeconds(timeRemaining)}
					</div>
				</div>

				<!-- Word Entry -->
				<div class="input-card">
					<label for="word-input" class="input-label">
						{t('Type a word and press Enter:')}
					</label>
					<div class="input-row">
						<input
							id="word-input"
							type="text"
							bind:value={currentInput}
							on:keypress={handleKeyPress}
							placeholder={t('Type your word here...')}
							class="word-input"
						/>
						<button class="submit-btn" on:click={submitWord} disabled={!currentInput.trim()}>
							{t('Add')}
						</button>
					</div>
					<p class="input-tip">{t('Tip: Press Enter to add words quickly')}</p>
				</div>

				<!-- Submitted Words -->
				<div class="words-section">
					<h3 class="words-heading">
						{t('Your Words')} ({n(submittedWords.length)})
					</h3>
					<div class="words-area" class:words-area-empty={submittedWords.length === 0}>
						{#each submittedWords as word, index}
							<span class="word-chip">
								{word}
								<button
									class="chip-remove"
									on:click={() => removeWord(index)}
									title={t('Remove word')}
									aria-label={t('Remove word')}
								>×</button>
							</span>
						{/each}
						{#if submittedWords.length === 0}
							<span class="words-empty">{t('No words yet — start typing!')}</span>
						{/if}
					</div>
				</div>

				<!-- End Early -->
				<div class="skip-row">
					<button class="btn-secondary" on:click={endTrial}>
						{t('Finish Early')}
					</button>
				</div>
			</div>

		{:else if gamePhase === 'results'}
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />

			<!-- Results Header -->
			<div class="results-header">
				<div class="score-pill">
					<span class="score-label">{t('Score')}</span>
					<span class="score-value">
						{results ? n(results.normalized_score, { maximumFractionDigits: 0 }) : '—'}
					</span>
					<span class="score-max">/100</span>
				</div>
				<p class="results-subtitle">{t('Category Fluency Complete')} · {localizedCategoryName()}</p>
			</div>

			{#if saveError}
				<div class="warn-card">
					{t('Error saving results. Your progress may not have been recorded.')}
				</div>
			{/if}

			{#if results}
				<!-- Key Metrics -->
				<div class="metrics-grid">
					<div class="metric-card metric-teal">
						<div class="metric-value">{n(results.unique_count)}</div>
						<div class="metric-label">{t('Unique Words')}</div>
					</div>
					<div class="metric-card metric-amber">
						<div class="metric-value">
							{n(results.words_per_second, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}
						</div>
						<div class="metric-label">{t('Words / Second')}</div>
					</div>
					<div
						class="metric-card"
						class:metric-excellent={results.performance_rating === 'excellent'}
						class:metric-good={results.performance_rating === 'good'}
						class:metric-below={results.performance_rating === 'below_average' ||
							results.performance_rating === 'average'}
					>
						<div class="metric-value">{performanceLabel(results.performance_rating)}</div>
						<div class="metric-label">{t('Performance')}</div>
					</div>
				</div>

				<!-- Feedback -->
				<div class="card">
					<h3 class="card-title">{t('Feedback')}</h3>
					<p class="feedback-text">{performanceFeedback()}</p>

					{#if results.unique_words && results.unique_words.length > 0}
						<div class="words-result-section">
							<h4 class="words-result-heading words-valid-heading">{t('Valid Words')}</h4>
							<div class="words-result-area">
								{#each results.unique_words as word}
									<span class="word-chip word-result">{word}</span>
								{/each}
							</div>
						</div>
					{/if}

					{#if results.invalid_words && results.invalid_words.length > 0}
						<div class="words-result-section">
							<h4 class="words-result-heading words-invalid-heading">{t('Duplicates / Invalid')}</h4>
							<div class="words-result-area words-invalid-area">
								{#each results.invalid_words as word}
									<span class="word-chip word-invalid">{word}</span>
								{/each}
							</div>
						</div>
					{/if}

					{#if results.duplicate_count > 0}
						<p class="dupe-note">
							{$locale === 'bn'
								? `${n(results.duplicate_count)}টি পুনরাবৃত্ত শব্দ বাদ দেওয়া হয়েছে।`
								: `${results.duplicate_count} duplicate${results.duplicate_count !== 1 ? 's' : ''} removed.`}
						</p>
					{/if}
				</div>

				<!-- Level Up -->
				{#if results.should_advance}
					<div class="levelup-card">
						<div class="levelup-badge">{t('Level Up')}</div>
						<p>
							{$locale === 'bn'
								? `দারুণ পারফরম্যান্স! কঠিনতা লেভেল ${n(trialData.difficulty + 1)}-এ উন্নীত হচ্ছে।`
								: `Great performance! Moving to difficulty level ${trialData.difficulty + 1}.`}
						</p>
					</div>
				{/if}
			{/if}

			<!-- Action Buttons -->
			<div class="action-buttons">
				<button class="start-button" on:click={() => goto('/dashboard')}>
					{t('Return to Dashboard')}
				</button>
				<button class="btn-secondary" on:click={() => goto('/training')}>
					{t('Next Task')}
				</button>
			</div>

		{/if}

		{#if gamePhase === 'intro' && trialData && !loadError}
			<button class="help-fab" on:click={() => {}}>?</button>
		{/if}
	</div>
</div>

{#if earnedBadges.length > 0}
	<BadgeNotification badges={earnedBadges} />
{/if}

<style>
	/* ── Page Layout ─────────────────────────────────── */
	.cf-page {
		min-height: 100vh;
		background: #C8DEFA;
		padding: 1.5rem;
	}

	.cf-wrapper {
		max-width: 960px;
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
		color: #0891b2;
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
		background: linear-gradient(135deg, #0e7490 0%, #06b6d4 100%);
		color: white;
		padding: 0.4rem 0.9rem;
		border-radius: 2rem;
		font-size: 0.813rem;
		font-weight: 600;
		margin-bottom: 1rem;
	}

	.badge-icon { font-size: 0.813rem; font-weight: 700; letter-spacing: 0.04em; }

	.concept-desc { color: #4b5563; font-size: 0.938rem; line-height: 1.6; margin: 0; }

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

	/* ── Section Title ────────────────────────────────── */
	.section-title {
		font-size: 1.125rem;
		font-weight: 600;
		color: #1a1a2e;
		margin: 0 0 1.25rem 0;
	}

	/* ── Rules List ───────────────────────────────────── */
	.rules-list { display: flex; flex-direction: column; gap: 0.75rem; }

	.rule-item {
		display: flex;
		align-items: flex-start;
		gap: 0.875rem;
		background: #ecfeff;
		border-radius: 10px;
		padding: 0.875rem 1rem;
	}

	.rule-num {
		min-width: 2rem;
		height: 2rem;
		background: linear-gradient(135deg, #0e7490 0%, #06b6d4 100%);
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

	/* ── Category Highlight ───────────────────────────── */
	.category-highlight {
		background: linear-gradient(135deg, #cffafe 0%, #a5f3fc 100%);
		border-radius: 12px;
		padding: 1.25rem;
	}

	.category-name {
		font-size: 2rem;
		font-weight: 800;
		color: #0e7490;
		margin-bottom: 0.5rem;
		line-height: 1.1;
	}

	.category-examples { font-size: 0.875rem; color: #155e75; }
	.examples-label { font-weight: 600; margin-right: 0.25rem; }

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

	/* ── Tip Card ─────────────────────────────────────── */
	.tip-card {
		background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
		border: 2px solid #f59e0b;
		border-radius: 16px;
		padding: 1.25rem 1.5rem;
		display: flex;
		align-items: flex-start;
		gap: 1rem;
		margin-bottom: 1rem;
	}

	.tip-icon {
		background: #d97706;
		color: white;
		padding: 0.25rem 0.6rem;
		border-radius: 0.5rem;
		font-size: 0.75rem;
		font-weight: 700;
		white-space: nowrap;
		flex-shrink: 0;
		margin-top: 0.125rem;
	}

	.tip-title { font-weight: 700; color: #92400e; font-size: 0.938rem; margin-bottom: 0.25rem; }
	.tip-text  { font-size: 0.875rem; color: #92400e; margin: 0; line-height: 1.5; }

	/* ── Performance Guide ────────────────────────────── */
	.perf-subtitle { font-size: 0.813rem; color: #6b7280; margin: -0.5rem 0 1rem 0; }

	.norm-bars { display: flex; flex-direction: column; gap: 0.75rem; }

	.norm-bar {
		display: grid;
		grid-template-columns: 7rem 1fr 4rem;
		align-items: center;
		gap: 0.75rem;
	}

	.norm-label { font-size: 0.875rem; font-weight: 500; color: #374151; }
	.norm-track { height: 0.5rem; background: #f3f4f6; border-radius: 0.25rem; overflow: hidden; }
	.norm-fill  { height: 100%; border-radius: 0.25rem; }
	.norm-excellent { width: 90%; background: #16a34a; }
	.norm-normal    { width: 65%; background: #f59e0b; }
	.norm-impaired  { width: 35%; background: #dc2626; }
	.norm-range { font-size: 0.75rem; color: #6b7280; text-align: right; }

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

	.category-display-row {
		display: flex;
		align-items: center;
		gap: 1.25rem;
	}

	.category-display {
		font-size: 2.5rem;
		font-weight: 900;
		color: #0891b2;
		line-height: 1;
		text-shadow: 0 2px 8px rgba(8, 145, 178, 0.2);
	}

	.status-pills { display: flex; flex-direction: column; gap: 0.4rem; }

	.pill {
		padding: 0.3rem 0.75rem;
		border-radius: 2rem;
		font-size: 0.8rem;
		font-weight: 500;
	}

	.pill-cf       { background: #cffafe; color: #155e75; }
	.pill-progress { background: #f0fdf4; color: #166534; }

	/* ── Timer ────────────────────────────────────────── */
	.timer-display {
		background: linear-gradient(135deg, #0e7490 0%, #06b6d4 100%);
		color: white;
		padding: 0.5rem 1.5rem;
		border-radius: 2rem;
		font-size: 1.5rem;
		font-weight: 700;
		min-width: 5rem;
		text-align: center;
		transition: background 0.3s;
	}

	.timer-urgent {
		background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
		animation: timer-pulse 0.5s ease-in-out infinite;
	}

	/* ── Input Card ───────────────────────────────────── */
	.input-card {
		background: #ecfeff;
		border: 2px solid #a5f3fc;
		border-radius: 12px;
		padding: 1.25rem;
		margin-bottom: 1.25rem;
	}

	.input-label {
		display: block;
		color: #0e7490;
		font-weight: 600;
		font-size: 0.875rem;
		margin-bottom: 0.625rem;
	}

	.input-row {
		display: flex;
		gap: 0.75rem;
		align-items: center;
		margin-bottom: 0.5rem;
	}

	.word-input {
		flex: 1;
		padding: 0.875rem 1rem;
		font-size: 1.125rem;
		border: 2px solid #a5f3fc;
		border-radius: 10px;
		outline: none;
		background: white;
		color: #1a1a2e;
		transition: border-color 0.15s;
	}

	.word-input:focus {
		border-color: #0891b2;
		box-shadow: 0 0 0 3px rgba(8, 145, 178, 0.12);
	}

	.submit-btn {
		background: linear-gradient(135deg, #0e7490 0%, #06b6d4 100%);
		color: white;
		border: none;
		border-radius: 10px;
		padding: 0.875rem 1.5rem;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		white-space: nowrap;
		transition: opacity 0.15s;
	}

	.submit-btn:hover:not(:disabled) { opacity: 0.9; }
	.submit-btn:disabled { opacity: 0.45; cursor: not-allowed; }

	.input-tip { font-size: 0.8rem; color: #0891b2; margin: 0; }

	/* ── Words Section ────────────────────────────────── */
	.words-section { margin-bottom: 1.25rem; }

	.words-heading {
		font-size: 0.938rem;
		font-weight: 600;
		color: #0e7490;
		margin: 0 0 0.75rem 0;
	}

	.words-area {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		min-height: 52px;
		padding: 0.875rem;
		border-radius: 10px;
		background: #f0fdfe;
		border: 2px dashed #a5f3fc;
	}

	.words-empty { color: #9ca3af; font-style: italic; font-size: 0.875rem; align-self: center; }

	/* ── Word Chips ───────────────────────────────────── */
	.word-chip {
		background: linear-gradient(135deg, #cffafe 0%, #a5f3fc 100%);
		color: #0e7490;
		padding: 0.35rem 0.4rem 0.35rem 0.875rem;
		border-radius: 6px;
		font-size: 0.875rem;
		font-weight: 600;
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
	}

	.chip-remove {
		background: #0e7490;
		color: white;
		border: none;
		border-radius: 50%;
		width: 1.25rem;
		height: 1.25rem;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.85rem;
		line-height: 1;
		cursor: pointer;
		padding: 0;
		flex-shrink: 0;
	}

	.chip-remove:hover { background: #155e75; }

	.word-result  { background: #cffafe; color: #155e75; border: 1px solid #a5f3fc; border-radius: 6px; padding: 0.35rem 0.875rem; font-size: 0.875rem; font-weight: 600; }
	.word-invalid { background: #fee2e2; color: #991b1b; padding: 0.35rem 0.875rem; border-radius: 6px; font-size: 0.875rem; font-weight: 600; }

	/* ── Skip Row ─────────────────────────────────────── */
	.skip-row { display: flex; justify-content: flex-end; margin-top: 0.5rem; }

	/* ── Results Header ───────────────────────────────── */
	.results-header {
		background: linear-gradient(135deg, #0e7490 0%, #06b6d4 100%);
		border-radius: 16px;
		padding: 1.75rem;
		text-align: center;
		margin-bottom: 1rem;
		box-shadow: 0 4px 12px rgba(14, 116, 144, 0.35);
	}

	.score-pill {
		display: flex;
		align-items: baseline;
		justify-content: center;
		gap: 0.5rem;
		margin-bottom: 0.5rem;
	}

	.score-label { color: rgba(255, 255, 255, 0.85); font-size: 1rem; font-weight: 500; }
	.score-value { color: white; font-size: 3rem; font-weight: 700; }
	.score-max   { color: rgba(255, 255, 255, 0.7); font-size: 1.5rem; font-weight: 500; }

	.results-subtitle { color: rgba(255, 255, 255, 0.9); font-size: 0.938rem; margin: 0; }

	/* ── Metrics Grid ─────────────────────────────────── */
	.metrics-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 1rem;
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

	.metric-teal    { border-top-color: #0891b2; }
	.metric-amber   { border-top-color: #d97706; }
	.metric-excellent { border-top-color: #16a34a; }
	.metric-good      { border-top-color: #f59e0b; }
	.metric-below     { border-top-color: #dc2626; }

	.metric-value { font-size: 1.75rem; font-weight: 700; color: #1a1a2e; }
	.metric-label { font-size: 0.75rem; color: #6b7280; margin-top: 0.25rem; }

	/* ── Feedback ─────────────────────────────────────── */
	.feedback-text { font-size: 0.938rem; color: #374151; line-height: 1.6; margin: 0 0 1rem 0; }

	/* ── Words Result ─────────────────────────────────── */
	.words-result-section { margin-top: 1.25rem; }

	.words-result-heading {
		font-size: 0.875rem;
		font-weight: 600;
		margin: 0 0 0.625rem 0;
	}

	.words-valid-heading   { color: #0e7490; }
	.words-invalid-heading { color: #991b1b; }

	.words-result-area {
		display: flex;
		flex-wrap: wrap;
		gap: 0.4rem;
	}

	.words-invalid-area .word-invalid { display: inline-block; }

	.dupe-note { font-size: 0.8rem; color: #9ca3af; margin: 0.75rem 0 0 0; }

	/* ── Level Up Card ────────────────────────────────── */
	.levelup-card {
		background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
		border: 2px solid #86efac;
		border-radius: 16px;
		padding: 1.25rem 1.5rem;
		margin-bottom: 1rem;
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.levelup-badge {
		background: #16a34a;
		color: white;
		padding: 0.2rem 0.75rem;
		border-radius: 1rem;
		font-size: 0.75rem;
		font-weight: 600;
		white-space: nowrap;
	}

	.levelup-card p { font-size: 0.875rem; color: #166534; margin: 0; }

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

	.btn-secondary:not(.skip-row .btn-secondary) { flex: 1; }
	.btn-secondary:hover { background: #f5f3ff; transform: translateY(-2px); }

	/* ── Help FAB ─────────────────────────────────────── */
	.help-fab {
		position: fixed;
		bottom: 2rem;
		right: 2rem;
		width: 3rem;
		height: 3rem;
		background: linear-gradient(135deg, #0e7490 0%, #06b6d4 100%);
		color: white;
		border: none;
		border-radius: 50%;
		font-size: 1.25rem;
		font-weight: 700;
		cursor: pointer;
		box-shadow: 0 4px 12px rgba(14, 116, 144, 0.4);
		display: flex;
		align-items: center;
		justify-content: center;
	}

	/* ── Animations ───────────────────────────────────── */
	@keyframes timer-pulse {
		0%, 100% { transform: scale(1); }
		50%       { transform: scale(1.08); }
	}

	/* ── Responsive ───────────────────────────────────── */
	@media (max-width: 640px) {
		.info-grid      { grid-template-columns: 1fr; }
		.metrics-grid   { grid-template-columns: 1fr; }
		.action-buttons { flex-direction: column; }
		.game-status-bar { flex-direction: column; align-items: flex-start; }
		.category-display { font-size: 2rem; }
	}
</style>


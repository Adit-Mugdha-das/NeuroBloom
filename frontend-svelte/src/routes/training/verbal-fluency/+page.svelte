<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { API_BASE_URL } from '$lib/api';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
	import { formatNumber, locale, localeText, localizeStimulusSymbol, translateText } from '$lib/i18n';
	import { buildPracticePayload, getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	const ENGLISH_VARIANT_SUFFIXES = ['ing', 'ed', 's', 'es', 'er', 'est', 'ly', 'tion', 'ness', 'ment'];
	const BANGLA_VARIANT_SUFFIXES = ['গুলো', 'গুলি', 'দের', 'ের', 'টা', 'টি', 'রা', 'তে', 'র'];

	let gamePhase = 'loading';
	let sessionData = null;
	let currentLetterIndex = 0;
	let currentLetter = '';
	let timeRemaining = 60;
	let timer = null;
	let taskId = null;
	let loadError = false;
	let saveError = false;

	let currentInput = '';
	let submittedWords = [];
	let validWords = [];
	let invalidWords = [];
	let seenRoots = new Set();

	let allLetterResults = [];
	let results = null;
	let earnedBadges = [];
	/** @type {string} */
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';
	let recordedSessionData = null;

	function taskLocale() {
		return sessionData?.locale === 'bn' ? 'bn' : $locale;
	}

	function t(text, activeLocale = taskLocale()) {
		return translateText(text ?? '', activeLocale);
	}

	function n(value, options = {}, activeLocale = taskLocale()) {
		return formatNumber(value, activeLocale, options);
	}

	function displayLetter(value) {
		return localizeStimulusSymbol(value, taskLocale());
	}

	function secondsLabel(value) {
		return taskLocale() === 'bn' ? `${n(value)} সেকেন্ড` : `${value} seconds`;
	}

	function compactSecondsLabel(value) {
		return taskLocale() === 'bn' ? `${n(value)}স` : `${value}s`;
	}

	function wordsLabel(count) {
		return taskLocale() === 'bn' ? `${n(count)}টি শব্দ` : `${count} words`;
	}

	function validWordsSummary(count) {
		return taskLocale() === 'bn' ? `${n(count)}টি বৈধ শব্দ` : `${count} valid words`;
	}

	function invalidWordsSummary(count) {
		return taskLocale() === 'bn' ? `${n(count)}টি অবৈধ শব্দ` : `${count} invalid word(s)`;
	}

	function performanceLabel(value) {
		const labels = {
			excellent: taskLocale() === 'bn' ? 'অসাধারণ' : 'Excellent',
			good: taskLocale() === 'bn' ? 'ভালো' : 'Good',
			average: taskLocale() === 'bn' ? 'মোটামুটি' : 'Average',
			below_average: taskLocale() === 'bn' ? 'আরও অনুশীলন দরকার' : 'Below Average'
		};
		return labels[value] || value;
	}

	function comparisonStatusLabel(value) {
		if (taskLocale() === 'bn') {
			return value === 'above_average' ? 'গড়ের চেয়ে ভালো' : 'গড়ের নিচে';
		}
		return value === 'above_average' ? 'Above Average' : 'Below Average';
	}

	function averageWordsValue(value) {
		const numericValue = Number(value ?? 0);
		return n(numericValue, Number.isInteger(numericValue)
			? {}
			: { minimumFractionDigits: 1, maximumFractionDigits: 1 });
	}

	function lettersSummary() {
		return (sessionData?.letters ?? []).map((letter) => displayLetter(letter)).join(', ');
	}

	function detailsSummary() {
		if (!sessionData) return '';
		if (taskLocale() === 'bn') {
			return `${n(sessionData.min_words_target)}+ মোট শব্দ (এমএস রোগীর গড়: প্রতি অক্ষরে ১০-১৩টি শব্দ)`;
		}
		return `${sessionData.min_words_target}+ total words (MS average: 10-13 per letter)`;
	}

	function validationMessage(reasonKey, extra = {}) {
		if (taskLocale() === 'bn') {
			const reasons = {
				empty_word: 'ফাঁকা শব্দ গ্রহণযোগ্য নয়',
				too_short: 'খুব ছোট (কমপক্ষে ২টি অক্ষর)',
				wrong_letter: `'${displayLetter(extra.targetLetter || '')}' দিয়ে শুরু হতে হবে`,
				already_used: 'এই শব্দটি আগেই ব্যবহার করা হয়েছে',
				variant_used: 'একই শব্দপরিবার আগেই ব্যবহার হয়েছে'
			};
			return reasons[reasonKey] || reasonKey;
		}
		const reasons = {
			empty_word: 'Empty word',
			too_short: 'Too short (min 2 letters)',
			wrong_letter: `Must start with '${extra.targetLetter || ''}'`,
			already_used: 'Already used',
			variant_used: 'Variant already used'
		};
		return reasons[reasonKey] || reasonKey;
	}

	function normalizeWord(word) {
		return word.trim().replace(/\s+/gu, ' ').toLowerCase();
	}

	function getVariantSuffixes() {
		return taskLocale() === 'bn' ? BANGLA_VARIANT_SUFFIXES : ENGLISH_VARIANT_SUFFIXES;
	}

	function getWordRoot(word) {
		const normalizedWord = normalizeWord(word);
		const suffixes = getVariantSuffixes();
		for (const suffix of [...suffixes].sort((a, b) => b.length - a.length)) {
			if (normalizedWord.endsWith(suffix) && normalizedWord.length > suffix.length + 1) {
				return normalizedWord.slice(0, -suffix.length);
			}
		}
		return normalizedWord;
	}

	function validateWord(word) {
		const wordClean = normalizeWord(word);
		const targetLetter = normalizeWord(currentLetter);

		if (!wordClean) {
			return { valid: false, reason: validationMessage('empty_word') };
		}
		if (wordClean.length < 2) {
			return { valid: false, reason: validationMessage('too_short') };
		}
		if (!wordClean.startsWith(targetLetter)) {
			return {
				valid: false,
				reason: validationMessage('wrong_letter', { targetLetter: currentLetter })
			};
		}
		if (submittedWords.map((entry) => normalizeWord(entry)).includes(wordClean)) {
			return { valid: false, reason: validationMessage('already_used') };
		}
		const root = getWordRoot(wordClean);
		if (seenRoots.has(root)) {
			return { valid: false, reason: validationMessage('variant_used') };
		}
		return { valid: true, root };
	}

	function focusWordInput() {
		document.getElementById('verbal-word-input')?.focus();
	}

	onMount(async () => {
		if (!$user) {
			goto('/login');
			return;
		}
		await loadSession();
	});

	async function loadSession() {
		try {
			loadError = false;
			const difficulty = $user.planning_difficulty || 1;
			const response = await fetch(`${API_BASE_URL}/api/tasks/verbal-fluency/generate`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					difficulty,
					baseline_score: $user.planning_baseline,
					locale: $locale
				})
			});
			if (!response.ok) throw new Error('Failed to load session');
			sessionData = structuredClone(await response.json());
			recordedSessionData = structuredClone(sessionData);
			gamePhase = 'intro';
		} catch (_) {
			loadError = true;
			gamePhase = 'intro';
		}
	}

	/** @param {string} nextMode */
	function startFirstLetter(nextMode = TASK_PLAY_MODE.RECORDED) {
		playMode = nextMode;
		practiceStatusMessage = '';
		sessionData = nextMode === TASK_PLAY_MODE.PRACTICE
			? buildPracticePayload('verbal-fluency', recordedSessionData)
			: structuredClone(recordedSessionData);
		allLetterResults = [];
		currentLetterIndex = 0;
		startLetterRound();
	}

	function startLetterRound() {
		currentLetter = sessionData.letters[currentLetterIndex];
		timeRemaining = sessionData.time_per_letter_seconds;
		currentInput = '';
		submittedWords = [];
		validWords = [];
		invalidWords = [];
		seenRoots = new Set();
		gamePhase = 'letter_round';
		timer = setInterval(() => {
			timeRemaining--;
			if (timeRemaining <= 0) {
				endLetterRound();
			}
		}, 1000);
		setTimeout(() => {
			focusWordInput();
		}, 60);
	}

	function submitWord() {
		if (!currentInput.trim()) return;
		const word = currentInput.trim();
		const validation = validateWord(word);
		submittedWords = [...submittedWords, word];
		if (validation.valid) {
			validWords = [...validWords, word];
			seenRoots = new Set([...seenRoots, validation.root]);
		} else {
			invalidWords = [...invalidWords, { word, reason: validation.reason }];
		}
		currentInput = '';
		setTimeout(() => {
			focusWordInput();
		}, 0);
	}

	function handleKeyPress(event) {
		if (event.key === 'Enter' || event.key === ' ') {
			event.preventDefault();
			submitWord();
		}
	}

	function endLetterRound() {
		clearInterval(timer);
		timer = null;
		allLetterResults = [
			...allLetterResults,
			{
				letter: currentLetter,
				words: [...validWords],
				time_taken_seconds: sessionData.time_per_letter_seconds - timeRemaining
			}
		];
		if (currentLetterIndex < sessionData.letters.length - 1) {
			currentLetterIndex++;
			gamePhase = 'between_letters';
			setTimeout(() => startLetterRound(), 2000);
		} else {
			if (playMode === TASK_PLAY_MODE.PRACTICE) {
				sessionData = structuredClone(recordedSessionData);
				playMode = TASK_PLAY_MODE.RECORDED;
				practiceStatusMessage = getPracticeCopy($locale).complete;
				gamePhase = 'intro';
				return;
			}
			finishSession();
		}
	}

	async function finishSession() {
		try {
			saveError = false;
			const response = await fetch(`${API_BASE_URL}/api/tasks/verbal-fluency/score`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					session_data: sessionData,
					user_responses: allLetterResults
				})
			});
			if (!response.ok) throw new Error('Failed to score session');
			results = await response.json();
			await saveResults();
			gamePhase = 'results';
		} catch (_) {
			saveError = true;
			gamePhase = 'results';
		}
	}

	async function saveResults() {
		try {
			taskId = $page.url.searchParams.get('taskId');
			const response = await fetch(`${API_BASE_URL}/api/tasks/verbal-fluency/submit/${$user.id}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				credentials: 'include',
				body: JSON.stringify({
					session_data: sessionData,
					task_id: taskId,
					user_responses: allLetterResults
				})
			});
			if (!response.ok) throw new Error('Failed to save results');
			const data = await response.json();
			if (data.new_badges && data.new_badges.length > 0) {
				earnedBadges = data.new_badges;
			}
			user.update((existingUser) => ({
				...existingUser,
				planning_difficulty: data.new_difficulty
			}));
		} catch (_) {
			// silent
		}
	}
</script>

<div class="cowat-page" data-localize-skip>
	<div class="cowat-wrapper">

		{#if gamePhase === 'loading'}
			<LoadingSkeleton />

		{:else if gamePhase === 'intro'}

			<!-- Header Card -->
			<div class="header-card">
				<div class="header-content">
					<div class="header-text">
						<h1 class="task-title">{t('Verbal Fluency', $locale)}</h1>
						<p class="task-domain">{t('COWAT · Planning / Executive Function', $locale)}</p>
					</div>
					<DifficultyBadge difficulty={sessionData?.difficulty || 1} domain="Executive Planning" />
				</div>
			</div>

			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} />
			{/if}

			{#if loadError}
				<div class="error-card">
					<p>{t('Failed to load task. Please try again.', $locale)}</p>
					<button class="start-button" on:click={loadSession}>
						{t('Retry', $locale)}
					</button>
				</div>
			{:else if sessionData}

				<!-- Task Concept -->
				<div class="card task-concept">
					<div class="concept-badge">
						<span class="badge-icon">COWAT</span>
						<span>{t('Executive Planning', $locale)}</span>
					</div>
					<p class="concept-desc">
						{sessionData.instructions.description}
					</p>
				</div>

				<!-- Rules Card -->
				<div class="card">
					<h2 class="section-title">{t('Rules', taskLocale())}</h2>
					<div class="rules-list">
						{#each sessionData.instructions.rules as rule, i}
							<div class="rule-item">
								<div class="rule-num">{i + 1}</div>
								<div class="rule-text">{rule}</div>
							</div>
						{/each}
					</div>
				</div>

				<!-- Info Grid -->
				<div class="info-grid">
					<div class="card">
						<h3 class="card-title">{t('Session Details', taskLocale())}</h3>
						<div class="details-list">
							<div class="detail-row">
								<span>{t('Letters', taskLocale())}</span>
								<strong>{lettersSummary()}</strong>
							</div>
							<div class="detail-row">
								<span>{t('Time per letter', taskLocale())}</span>
								<strong>{secondsLabel(sessionData.time_per_letter_seconds)}</strong>
							</div>
							<div class="detail-row">
								<span>{t('Target', taskLocale())}</span>
								<strong>{detailsSummary()}</strong>
							</div>
							<div class="detail-row">
								<span>{t('Difficulty', taskLocale())}</span>
								<strong>{t(`Level ${sessionData.difficulty} / 10`, taskLocale())}</strong>
							</div>
						</div>
					</div>
					<div class="card">
						<h3 class="card-title">{t('What It Measures', taskLocale())}</h3>
						<div class="details-list">
							<div class="detail-row">
								<span>{t('Primary Metric', taskLocale())}</span>
								<strong>{t('Words per letter', taskLocale())}</strong>
							</div>
							<div class="detail-row">
								<span>{t('Cognitive Domain', taskLocale())}</span>
								<strong>{t('Verbal fluency', taskLocale())}</strong>
							</div>
							<div class="detail-row">
								<span>{t('Scoring Basis', taskLocale())}</span>
								<strong>{t('Unique valid words', taskLocale())}</strong>
							</div>
							<div class="detail-row">
								<span>{t('Test Battery', taskLocale())}</span>
								<strong>MACFIMS / BICAMS</strong>
							</div>
						</div>
					</div>
				</div>

				<!-- Clinical Info -->
				<div class="clinical-info">
					<div class="clinical-header">
						<div class="clinical-badge">{t('Clinical Basis', taskLocale())}</div>
						<h3>{t('Validated MS Executive Function Assessment', taskLocale())}</h3>
					</div>
					<p>
						{t(
							'The Controlled Oral Word Association Test (Benton & Hamsher, 1989) is included in the MACFIMS and BICAMS batteries for MS. Verbal fluency deficits affect up to 40% of MS patients and reflect impaired initiation, strategy, and prefrontal executive control. Phonemic fluency (letter-based) taxes executive function more than semantic fluency.',
							$locale
						)}
					</p>
				</div>

				<!-- Performance Guide -->
				<div class="card perf-guide">
					<h3 class="card-title">{t('Performance Norms (per letter, 60s)', taskLocale())}</h3>
					<p class="perf-subtitle">{t('Unique valid words per letter', taskLocale())}</p>
					<div class="norm-bars">
						<div class="norm-bar">
							<div class="norm-label">{t('Excellent', taskLocale())}</div>
							<div class="norm-track"><div class="norm-fill norm-excellent"></div></div>
							<div class="norm-range">&gt; 14</div>
						</div>
						<div class="norm-bar">
							<div class="norm-label">{t('Normal (MS)', taskLocale())}</div>
							<div class="norm-track"><div class="norm-fill norm-normal"></div></div>
							<div class="norm-range">10–14</div>
						</div>
						<div class="norm-bar">
							<div class="norm-label">{t('Impaired', taskLocale())}</div>
							<div class="norm-track"><div class="norm-fill norm-impaired"></div></div>
							<div class="norm-range">&lt; 10</div>
						</div>
					</div>
				</div>

				<TaskPracticeActions
					locale={$locale}
					startLabel={localeText({ en: 'Start Word Association', bn: 'শব্দ সংযোগ শুরু করুন' }, $locale)}
					statusMessage={practiceStatusMessage}
					on:start={() => startFirstLetter(TASK_PLAY_MODE.RECORDED)}
					on:practice={() => startFirstLetter(TASK_PLAY_MODE.PRACTICE)}
				/>

			{:else}
				<LoadingSkeleton />
			{/if}

		{:else if gamePhase === 'letter_round'}

			<div class="game-card">
				{#if playMode === TASK_PLAY_MODE.PRACTICE}
					<PracticeModeBanner locale={$locale} />
				{/if}

				<!-- Status Bar -->
				<div class="game-status-bar">
					<div class="letter-display-row">
						<div class="letter-display">{displayLetter(currentLetter)}</div>
						<div class="status-pills">
							<span class="pill pill-cowat">
								{taskLocale() === 'bn'
									? `অক্ষর ${n(currentLetterIndex + 1)} এর ${n(sessionData.letters.length)}`
									: `Letter ${currentLetterIndex + 1} of ${sessionData.letters.length}`}
							</span>
							<span class="pill pill-words">
								{validWordsSummary(validWords.length)}
							</span>
						</div>
					</div>
					<div class="timer-display" class:timer-urgent={timeRemaining <= 10}>
						{compactSecondsLabel(timeRemaining)}
					</div>
				</div>

				<!-- Word Entry -->
				<div class="input-card">
					<div class="input-row">
						<input
							id="verbal-word-input"
							type="text"
							bind:value={currentInput}
							on:keypress={handleKeyPress}
							placeholder={t('Type a word and press Enter or Space...', taskLocale())}
							class="word-input"
						/>
						<button class="submit-btn" on:click={submitWord}>
							{t('Submit', taskLocale())}
						</button>
					</div>
					<p class="input-tip">
						{t('Tip: Press Enter or Space to submit quickly', taskLocale())}
					</p>
				</div>

				<!-- Valid Words -->
				<div class="words-section">
					<h3 class="words-heading words-valid-heading">
						{t('Valid Words', taskLocale())} ({n(validWords.length)})
					</h3>
					<div class="words-area words-valid-area">
						{#each validWords as word}
							<span class="word-chip word-valid">{word}</span>
						{/each}
						{#if validWords.length === 0}
							<span class="words-empty">{t('No valid words yet...', taskLocale())}</span>
						{/if}
					</div>
				</div>

				<!-- Invalid Words -->
				{#if invalidWords.length > 0}
					<div class="words-section">
						<h3 class="words-heading words-invalid-heading">
							{t('Invalid Words', taskLocale())} ({n(invalidWords.length)})
						</h3>
						<div class="words-area words-invalid-area">
							{#each invalidWords as item}
								<span class="word-chip word-invalid" title={item.reason}>
									{item.word}
									<span class="word-reason">({item.reason})</span>
								</span>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Skip -->
				<div class="skip-row">
					<button class="btn-secondary" on:click={endLetterRound}>
						{taskLocale() === 'bn' ? 'পরের অক্ষরে যান →' : 'Skip to Next Letter →'}
					</button>
				</div>
			</div>

		{:else if gamePhase === 'between_letters'}

			<div class="completion-card">
				<div class="completion-badge">{t('Letter Complete', taskLocale())}</div>
				<h2 class="completion-title">{t('Well done!', taskLocale())}</h2>
				<div class="completion-stat">
					<div class="cstat-val">{validWords.length}</div>
					<div class="cstat-lbl">{t('valid words', taskLocale())}</div>
				</div>
				<p class="next-letter-line">
					{taskLocale() === 'bn' ? 'পরের অক্ষর:' : 'Next letter:'}
					<strong class="next-letter-val">{displayLetter(sessionData.letters[currentLetterIndex])}</strong>
				</p>
				<p class="auto-start-hint">{t('Starting in 2 seconds...', taskLocale())}</p>
			</div>

		{:else if gamePhase === 'results'}

			<!-- Results Header -->
			<div class="results-header">
				<div class="score-pill">
					<span class="score-label">{t('Score', taskLocale())}</span>
					<span class="score-value">{results ? n(results.score) : '—'}</span>
					<span class="score-max">/100</span>
				</div>
				<p class="results-subtitle">{t('Verbal Fluency Complete', taskLocale())}</p>
			</div>

			{#if saveError}
				<div class="warn-card">
					{t('Error saving results. Your progress may not have been recorded.', taskLocale())}
				</div>
			{/if}

			{#if results}
				<!-- Key Metrics -->
				<div class="metrics-grid">
					<div class="metric-card metric-green">
						<div class="metric-value">{n(results.total_valid_words)}</div>
						<div class="metric-label">{t('Total Valid Words', taskLocale())}</div>
					</div>
					<div class="metric-card metric-cowat">
						<div class="metric-value">{averageWordsValue(results.avg_words_per_letter)}</div>
						<div class="metric-label">{t('Avg Per Letter', taskLocale())}</div>
					</div>
					<div class="metric-card"
						class:metric-excellent={results.performance === 'excellent'}
						class:metric-good={results.performance === 'good'}
						class:metric-below={results.performance === 'below_average' || results.performance === 'average'}>
						<div class="metric-value">{performanceLabel(results.performance)}</div>
						<div class="metric-label">{t('Performance', taskLocale())}</div>
					</div>
				</div>

				<!-- MS Comparison -->
				<div class="ms-comparison-card">
					<div class="ms-comparison-header">
						<div class="ms-badge">{t('MS Patient Comparison', taskLocale())}</div>
					</div>
					<p class="ms-desc">{results.ms_comparison.description}</p>
					<div class="ms-stats-row">
						<span>
							{taskLocale() === 'bn' ? 'আপনার গড়:' : 'Your average:'}
							<strong>{averageWordsValue(results.ms_comparison.user_avg)} {taskLocale() === 'bn' ? 'শব্দ/অক্ষর' : 'words/letter'}</strong>
						</span>
						<span class="ms-status-tag"
							class:ms-above={results.ms_comparison.status === 'above_average'}
							class:ms-below={results.ms_comparison.status !== 'above_average'}>
							{comparisonStatusLabel(results.ms_comparison.status)}
						</span>
					</div>
				</div>

				<!-- Letter Breakdown -->
				<div class="card">
					<h3 class="card-title">{t('Letter Breakdown', taskLocale())}</h3>
					<div class="letter-results-list">
						{#each results.letter_results as letterResult}
							<div class="letter-result-row">
								<div class="letter-result-header">
									<span class="letter-result-char">{displayLetter(letterResult.letter)}</span>
									<span class="letter-result-count">{wordsLabel(letterResult.valid_word_count)}</span>
									{#if letterResult.invalid_word_count > 0}
										<span class="tag tag-invalid">{invalidWordsSummary(letterResult.invalid_word_count)}</span>
									{/if}
								</div>
								<div class="letter-words-chips">
									{#each letterResult.valid_words as word}
										<span class="word-chip word-result">{word}</span>
									{/each}
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Action Buttons -->
			<div class="action-buttons">
				<button class="start-button" on:click={() => goto('/dashboard')}>
					{t('Return to Dashboard', taskLocale())}
				</button>
				<button class="btn-secondary" on:click={() => goto('/training')}>
					{t('Next Task', taskLocale())}
				</button>
			</div>

		{/if}

		{#if gamePhase === 'intro' && sessionData && !loadError}
			<button class="help-fab" on:click={() => {}}>?</button>
		{/if}
	</div>
</div>

{#if earnedBadges.length > 0}
	<BadgeNotification badges={earnedBadges} />
{/if}

<style>
	/* ── Page Layout ─────────────────────────────────── */
	.cowat-page {
		min-height: 100vh;
		background: #C8DEFA;
		padding: 1.5rem;
	}

	.cowat-wrapper {
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
		color: #db2777;
		font-weight: 500;
		margin: 0;
	}

	/* ── Error / Warn Cards ───────────────────────────── */
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
		background: linear-gradient(135deg, #be185d 0%, #ec4899 100%);
		color: white;
		padding: 0.4rem 0.9rem;
		border-radius: 2rem;
		font-size: 0.813rem;
		font-weight: 600;
		margin-bottom: 1rem;
	}

	.badge-icon {
		font-size: 0.813rem;
		font-weight: 700;
		letter-spacing: 0.05em;
	}

	.concept-desc {
		color: #4b5563;
		font-size: 0.938rem;
		line-height: 1.6;
		margin: 0;
	}

	/* ── Section Title ────────────────────────────────── */
	.section-title {
		font-size: 1.125rem;
		font-weight: 600;
		color: #1a1a2e;
		margin: 0 0 1.25rem 0;
	}

	/* ── Rules List ───────────────────────────────────── */
	.rules-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.rule-item {
		display: flex;
		align-items: flex-start;
		gap: 0.875rem;
		background: #fdf2f8;
		border-radius: 10px;
		padding: 0.875rem 1rem;
	}

	.rule-num {
		min-width: 2rem;
		height: 2rem;
		background: linear-gradient(135deg, #be185d 0%, #ec4899 100%);
		color: white;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.875rem;
		font-weight: 700;
		flex-shrink: 0;
	}

	.rule-text {
		font-size: 0.9rem;
		color: #374151;
		line-height: 1.5;
	}

	/* ── Info Grid ────────────────────────────────────── */
	.info-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
		margin-bottom: 1rem;
	}

	.card-title {
		font-size: 1rem;
		font-weight: 600;
		color: #1a1a2e;
		margin: 0 0 1rem 0;
	}

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

	.letter-display-row {
		display: flex;
		align-items: center;
		gap: 1.25rem;
	}

	.letter-display {
		font-size: 4rem;
		font-weight: 900;
		color: #db2777;
		line-height: 1;
		letter-spacing: -0.02em;
		text-shadow: 0 2px 8px rgba(219, 39, 119, 0.2);
	}

	.status-pills {
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}

	.pill {
		padding: 0.3rem 0.75rem;
		border-radius: 2rem;
		font-size: 0.8rem;
		font-weight: 500;
	}

	.pill-cowat  { background: #fce7f3; color: #831843; }
	.pill-words  { background: #f0fdf4; color: #166534; }

	/* ── Timer Display ────────────────────────────────── */
	.timer-display {
		background: linear-gradient(135deg, #be185d 0%, #ec4899 100%);
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
		background: #fdf2f8;
		border: 2px solid #fbcfe8;
		border-radius: 12px;
		padding: 1.25rem;
		margin-bottom: 1.25rem;
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
		border: 2px solid #fbcfe8;
		border-radius: 10px;
		outline: none;
		background: white;
		color: #1a1a2e;
		transition: border-color 0.15s;
	}

	.word-input:focus {
		border-color: #db2777;
		box-shadow: 0 0 0 3px rgba(219, 39, 119, 0.12);
	}

	.submit-btn {
		background: linear-gradient(135deg, #be185d 0%, #ec4899 100%);
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

	.submit-btn:hover { opacity: 0.9; }

	.input-tip {
		font-size: 0.8rem;
		color: #9d174d;
		margin: 0;
	}

	/* ── Words Section ────────────────────────────────── */
	.words-section { margin-bottom: 1.25rem; }

	.words-heading {
		font-size: 0.938rem;
		font-weight: 600;
		margin: 0 0 0.75rem 0;
	}

	.words-valid-heading   { color: #166534; }
	.words-invalid-heading { color: #991b1b; }

	.words-area {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		min-height: 52px;
		padding: 0.875rem;
		border-radius: 10px;
		border: 2px dashed;
	}

	.words-valid-area   { background: #f0fdf4; border-color: #86efac; }
	.words-invalid-area { background: #fee2e2; border-color: #fca5a5; }

	.words-empty { color: #9ca3af; font-style: italic; font-size: 0.875rem; align-self: center; }

	/* ── Word Chips ───────────────────────────────────── */
	.word-chip {
		padding: 0.35rem 0.875rem;
		border-radius: 6px;
		font-size: 0.875rem;
		font-weight: 600;
		display: inline-flex;
		align-items: center;
		gap: 0.4rem;
	}

	.word-valid   { background: #22c55e; color: white; }
	.word-invalid { background: #ef4444; color: white; }
	.word-result  { background: #fce7f3; color: #831843; border: 1px solid #fbcfe8; }

	.word-reason {
		font-size: 0.75rem;
		opacity: 0.85;
		font-weight: 400;
	}

	/* ── Skip Row ─────────────────────────────────────── */
	.skip-row {
		display: flex;
		justify-content: flex-end;
		margin-top: 0.5rem;
	}

	/* ── Completion Card ──────────────────────────────── */
	.completion-card {
		background: white;
		border-radius: 16px;
		padding: 2.5rem 2rem;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
		text-align: center;
		max-width: 500px;
		margin: 0 auto;
	}

	.completion-badge {
		display: inline-block;
		background: linear-gradient(135deg, #be185d 0%, #ec4899 100%);
		color: white;
		padding: 0.4rem 1.25rem;
		border-radius: 2rem;
		font-size: 0.875rem;
		font-weight: 700;
		margin-bottom: 0.75rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.completion-title {
		font-size: 1.5rem;
		font-weight: 700;
		color: #1a1a2e;
		margin: 0 0 1.25rem 0;
	}

	.completion-stat { margin-bottom: 1.25rem; }

	.cstat-val {
		font-size: 3rem;
		font-weight: 700;
		color: #db2777;
	}

	.cstat-lbl { font-size: 0.875rem; color: #9ca3af; margin-top: 0.25rem; }

	.next-letter-line {
		color: #374151;
		font-size: 1rem;
		margin: 0 0 0.5rem 0;
	}

	.next-letter-val {
		font-size: 2rem;
		color: #db2777;
		margin-left: 0.5rem;
		vertical-align: middle;
	}

	.auto-start-hint { color: #9ca3af; font-size: 0.875rem; margin: 0; }

	/* ── Results Header ───────────────────────────────── */
	.results-header {
		background: linear-gradient(135deg, #be185d 0%, #ec4899 100%);
		border-radius: 16px;
		padding: 1.75rem;
		text-align: center;
		margin-bottom: 1rem;
		box-shadow: 0 4px 12px rgba(190, 24, 93, 0.35);
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

	.metric-green     { border-top-color: #16a34a; }
	.metric-cowat     { border-top-color: #db2777; }
	.metric-excellent { border-top-color: #16a34a; }
	.metric-good      { border-top-color: #f59e0b; }
	.metric-below     { border-top-color: #dc2626; }

	.metric-value { font-size: 1.75rem; font-weight: 700; color: #1a1a2e; }
	.metric-label { font-size: 0.75rem; color: #6b7280; margin-top: 0.25rem; }

	/* ── MS Comparison Card ───────────────────────────── */
	.ms-comparison-card {
		background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
		border: 2px solid #f59e0b;
		border-radius: 16px;
		padding: 1.25rem 1.5rem;
		margin-bottom: 1rem;
	}

	.ms-comparison-header { margin-bottom: 0.5rem; }

	.ms-badge {
		background: #d97706;
		color: white;
		padding: 0.2rem 0.75rem;
		border-radius: 1rem;
		font-size: 0.75rem;
		font-weight: 600;
		display: inline-block;
	}

	.ms-desc { font-size: 0.875rem; color: #92400e; margin: 0.5rem 0; line-height: 1.5; }

	.ms-stats-row {
		display: flex;
		align-items: center;
		gap: 1rem;
		flex-wrap: wrap;
		color: #92400e;
		font-size: 0.875rem;
	}

	.ms-status-tag {
		padding: 0.2rem 0.75rem;
		border-radius: 1rem;
		font-size: 0.75rem;
		font-weight: 600;
	}

	.ms-above { background: #dcfce7; color: #166534; }
	.ms-below { background: #fee2e2; color: #991b1b; }

	/* ── Letter Breakdown ─────────────────────────────── */
	.letter-results-list { display: flex; flex-direction: column; gap: 0.75rem; }

	.letter-result-row {
		padding: 1rem;
		background: #f9fafb;
		border-radius: 10px;
		border-left: 4px solid #db2777;
	}

	.letter-result-header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 0.625rem;
	}

	.letter-result-char {
		font-size: 1.5rem;
		font-weight: 800;
		color: #db2777;
	}

	.letter-result-count {
		font-size: 1rem;
		font-weight: 600;
		color: #166534;
	}

	.letter-words-chips {
		display: flex;
		flex-wrap: wrap;
		gap: 0.4rem;
	}

	.tag { padding: 0.2rem 0.6rem; border-radius: 0.75rem; font-size: 0.75rem; font-weight: 600; }
	.tag-invalid { background: #fee2e2; color: #991b1b; }

	/* ── Action Buttons ───────────────────────────────── */
	.action-buttons {
		display: flex;
		gap: 1rem;
		margin-top: 1rem;
	}

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
		flex: 1;
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

	.btn-secondary:hover { background: #f5f3ff; transform: translateY(-2px); }

	/* ── Help FAB ─────────────────────────────────────── */
	.help-fab {
		position: fixed;
		bottom: 2rem;
		right: 2rem;
		width: 3rem;
		height: 3rem;
		background: linear-gradient(135deg, #be185d 0%, #ec4899 100%);
		color: white;
		border: none;
		border-radius: 50%;
		font-size: 1.25rem;
		font-weight: 700;
		cursor: pointer;
		box-shadow: 0 4px 12px rgba(190, 24, 93, 0.4);
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
		.info-grid    { grid-template-columns: 1fr; }
		.metrics-grid { grid-template-columns: 1fr; }
		.action-buttons { flex-direction: column; }
		.game-status-bar { flex-direction: column; align-items: flex-start; }
		.letter-display { font-size: 3rem; }
	}
</style>

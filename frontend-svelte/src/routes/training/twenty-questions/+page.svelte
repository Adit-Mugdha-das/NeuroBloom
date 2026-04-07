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
	import { getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let gamePhase = 'loading';
	let gameData = null;
	let targetObject = null;
	let targetAttributes = {};
	let taskId = null;

	let questionInput = '';
	let questionsAsked = 0;
	let questionsHistory = [];
	let guessInput = '';

	let results = null;
	let earnedBadges = [];
	/** @type {string} */
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';

	let loadError = false;
	let askError = false;
	let saveError = false;
	let showGiveUpConfirm = false;

	function lt(en, bn) {
		return localeText({ en, bn }, $locale);
	}

	function answerClass(answer) {
		const a = (answer || '').toLowerCase();
		if (a === 'yes') return 'answer-yes';
		if (a === 'no') return 'answer-no';
		return 'answer-partial';
	}

	function counterClass() {
		if (questionsAsked >= 18) return 'counter-danger';
		if (questionsAsked >= 14) return 'counter-warn';
		return 'counter-safe';
	}

	function performanceLabel(rating) {
		const map = {
			excellent: lt('Excellent', 'অসাধারণ'),
			good: lt('Good', 'ভালো'),
			average: lt('Average', 'মোটামুটি'),
			below_average: lt('Below Average', 'নিচের গড়'),
			incorrect: lt('Incorrect', 'ভুল')
		};
		return map[rating] || rating;
	}

	onMount(async () => {
		if (!$user) {
			goto('/login');
			return;
		}
		await loadGame();
	});

	async function loadGame() {
		try {
			loadError = false;
			const response = await fetch(
				`${API_BASE_URL}/api/training/tasks/twenty-questions/generate/${$user.id}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					credentials: 'include'
				}
			);
			if (!response.ok) throw new Error('Failed to load game');
			const data = await response.json();
			gameData = data.game_data;
			targetObject = gameData.target_object_name;
			targetAttributes = gameData.target_attributes;
			gamePhase = 'intro';
		} catch (_) {
			loadError = true;
			gamePhase = 'intro';
		}
	}

	/** @param {string} nextMode */
	function startGame(nextMode = TASK_PLAY_MODE.RECORDED) {
		playMode = nextMode;
		practiceStatusMessage = '';
		questionsAsked = 0;
		questionsHistory = [];
		questionInput = '';
		guessInput = '';
		showGiveUpConfirm = false;
		askError = false;
		gamePhase = 'playing';
		setTimeout(() => {
			document.getElementById('question-input')?.focus();
		}, 100);
	}

	async function askQuestion() {
		if (!questionInput.trim()) return;
		const question = questionInput.trim();
		askError = false;
		try {
			const response = await fetch(
				`${API_BASE_URL}/api/training/tasks/twenty-questions/ask/${$user.id}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					credentials: 'include',
					body: JSON.stringify({
						question,
						target_attributes: targetAttributes,
						target_object_name: targetObject
					})
				}
			);
			if (!response.ok) throw new Error('Failed to ask question');
			const data = await response.json();
			questionsHistory = [
				...questionsHistory,
				{ question, answer: data.answer, confidence: data.confidence }
			];
			questionsAsked++;
			questionInput = '';
			setTimeout(() => {
				document.getElementById('question-input')?.focus();
			}, 0);
			setTimeout(() => {
				const el = document.getElementById('questions-history');
				if (el) el.scrollTop = el.scrollHeight;
			}, 100);
		} catch (_) {
			askError = true;
		}
	}

	function handleQuestionKeyPress(event) {
		if (event.key === 'Enter') {
			event.preventDefault();
			askQuestion();
		}
	}

	async function submitGuess() {
		if (!guessInput.trim()) return;
		const guess = guessInput.trim();
		await endGame(guess.toLowerCase() === targetObject.toLowerCase(), guess);
	}

	async function endGame(correctlyIdentified, userGuess) {
		if (playMode === TASK_PLAY_MODE.PRACTICE) {
			playMode = TASK_PLAY_MODE.RECORDED;
			practiceStatusMessage = getPracticeCopy($locale).complete;
			results = null;
			earnedBadges = [];
			gamePhase = 'loading';
			await loadGame();
			return;
		}
		saveError = false;
		try {
			taskId = $page.url.searchParams.get('taskId');
			const response = await fetch(
				`${API_BASE_URL}/api/training/tasks/twenty-questions/submit/${$user.id}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					credentials: 'include',
					body: JSON.stringify({
						questions_asked: questionsAsked,
						correctly_identified: correctlyIdentified,
						difficulty: gameData.difficulty,
						questions_history: questionsHistory,
						target_object_name: targetObject,
						user_guess: userGuess,
						task_id: taskId
					})
				}
			);
			if (!response.ok) throw new Error('Failed to submit game');
			const data = await response.json();
			results = {
				normalized_score: data.score,
				performance_rating: data.performance_rating,
				questions_asked: data.questions_asked,
				correctly_identified: data.correctly_identified,
				question_efficiency: data.question_efficiency,
				strategy_score: data.strategy_score,
				constraint_seeking_questions: data.constraint_seeking_questions,
				specific_guesses: data.specific_guesses,
				feedback: data.feedback,
				tips: data.tips,
				should_advance: data.new_difficulty > data.old_difficulty
			};
			if (data.new_badges?.length > 0) earnedBadges = data.new_badges;
			user.update((u) => ({ ...u, planning_difficulty: data.new_difficulty }));
			gamePhase = 'results';
		} catch (_) {
			saveError = true;
			gamePhase = 'results';
		}
	}
</script>

<div class="tq-page" data-localize-skip>
	<div class="tq-wrapper">

		{#if gamePhase === 'loading'}
			<LoadingSkeleton />

		{:else if gamePhase === 'intro'}

			<!-- Header Card -->
			<div class="header-card">
				<div class="header-content">
					<div class="header-text">
						<h1 class="task-title">{lt('Twenty Questions', 'টুয়েন্টি কোয়েশ্চেন্স')}</h1>
						<p class="task-domain">{lt('Strategic Problem-Solving · Planning / Executive Function', 'কৌশলগত সমস্যা সমাধান · পরিকল্পনা / কার্যনির্বাহী কার্যক্ষমতা')}</p>
					</div>
					<DifficultyBadge difficulty={gameData?.difficulty || 1} domain="Executive Planning" />
				</div>
			</div>

			{#if playMode === TASK_PLAY_MODE.PRACTICE}
				<PracticeModeBanner locale={$locale} />
			{/if}

			{#if loadError}
				<div class="error-card">
					<p>{lt('Failed to load task. Please try again.', 'টাস্ক লোড করতে ব্যর্থ। আবার চেষ্টা করুন।')}</p>
					<button class="start-button" on:click={loadGame}>
						{lt('Retry', 'আবার চেষ্টা করুন')}
					</button>
				</div>
			{:else if gameData}

				<!-- Task Concept -->
				<div class="card task-concept">
					<div class="concept-badge">
						<span class="badge-icon">{lt('Strategy', 'কৌশল')}</span>
						<span>{lt('Executive Planning', 'কার্যনির্বাহী পরিকল্পনা')}</span>
					</div>
					<p class="concept-desc">
						{gameData.instructions}
					</p>
				</div>

				<!-- Rules Card -->
				<div class="card">
					<h2 class="section-title">{lt('Rules', 'নিয়মাবলী')}</h2>
					<div class="rules-list">
						<div class="rule-item">
							<div class="rule-num">1</div>
							<div class="rule-text">{lt('Type a yes/no question and press Enter to submit it', 'একটি হ্যাঁ/না প্রশ্ন টাইপ করুন এবং এন্টার চাপুন')}</div>
						</div>
						<div class="rule-item">
							<div class="rule-num">2</div>
							<div class="rule-text">{lt('Use broad constraint-seeking questions first — e.g., "Is it living?" not "Is it a dog?"', 'প্রথমে বিস্তৃত সীমানির্ধারণকারী প্রশ্ন করুন — যেমন "এটি কি জীবিত?" না "এটি কি কুকুর?"')}</div>
						</div>
						<div class="rule-item">
							<div class="rule-num">3</div>
							<div class="rule-text">{lt('When confident, submit your final guess in the guess box below', 'আত্মবিশ্বাসী হলে, নিচের অনুমান বাক্সে আপনার চূড়ান্ত উত্তর দিন')}</div>
						</div>
						<div class="rule-item">
							<div class="rule-num">4</div>
							<div class="rule-text">{lt('Fewer questions used = higher score. You have 20 questions maximum', 'কম প্রশ্ন = বেশি স্কোর। সর্বাধিক ২০টি প্রশ্ন')}</div>
						</div>
					</div>
				</div>

				<!-- Info Grid -->
				<div class="info-grid">
					<!-- Category Hint -->
					<div class="card">
						<h3 class="card-title">{lt('Category Hint', 'বিভাগ ইঙ্গিত')}</h3>
						<div class="hint-box">
							<div class="hint-label">{lt('I am thinking of a...', 'আমি ভাবছি একটি...')}</div>
							<div class="hint-value">{gameData.hint}</div>
						</div>
					</div>
					<!-- What It Measures -->
					<div class="card">
						<h3 class="card-title">{lt('What It Measures', 'এটি কী পরিমাপ করে')}</h3>
						<div class="details-list">
							<div class="detail-row">
								<span>{lt('Primary Metric', 'প্রাথমিক পরিমাপ')}</span>
								<strong>{lt('Questions to identify', 'সনাক্তকরণে প্রশ্ন')}</strong>
							</div>
							<div class="detail-row">
								<span>{lt('Cognitive Domain', 'জ্ঞানীয় ক্ষেত্র')}</span>
								<strong>{lt('Strategic planning', 'কৌশলগত পরিকল্পনা')}</strong>
							</div>
							<div class="detail-row">
								<span>{lt('Max Questions', 'সর্বাধিক প্রশ্ন')}</span>
								<strong>20</strong>
							</div>
							<div class="detail-row">
								<span>{lt('Difficulty', 'কঠিনতা')}</span>
								<strong>{lt(`Level ${gameData.difficulty} / 10`, `স্তর ${gameData.difficulty} / ১০`)}</strong>
							</div>
						</div>
					</div>
				</div>

				<!-- Strategy Tip -->
				<div class="tip-card">
					<div class="tip-icon">TIP</div>
					<div class="tip-body">
						<div class="tip-title">{lt('Constraint-Seeking Strategy', 'সীমানির্ধারণকারী কৌশল')}</div>
						<p class="tip-text">
							{lt(
								'Start with questions that eliminate half the possibilities: "Is it alive?", "Is it man-made?", "Can you hold it?". Broad questions give far more information than specific guesses.',
								'এমন প্রশ্ন দিয়ে শুরু করুন যা অর্ধেক সম্ভাবনা বাদ দেয়: "এটি কি জীবিত?", "এটি কি মানুষের তৈরি?", "এটি কি ধরা যায়?"'
							)}
						</p>
					</div>
				</div>

				<!-- Clinical Basis -->
				<div class="clinical-info">
					<div class="clinical-header">
						<div class="clinical-badge">{lt('Clinical Basis', 'ক্লিনিকাল ভিত্তি')}</div>
						<h3>{lt('Validated MS Strategic Reasoning Assessment', 'MS-এর জন্য যাচাইকৃত কৌশলগত যুক্তি মূল্যায়ন')}</h3>
					</div>
					<p>
						{lt(
							'The Twenty Questions Task (Mosher & Hornsby, 1966) assesses hypothesis-testing strategy and executive planning. In MS, deficits in constraint-seeking behaviour reflect impaired prefrontal-mediated top-down control and reduced cognitive flexibility. Inefficient questioning strategies predict everyday problem-solving difficulties and are sensitive to cognitive load imposed by MS-related fatigue.',
							'টুয়েন্টি কোয়েশ্চেন্স টাস্ক (Mosher & Hornsby, 1966) হাইপোথিসিস-পরীক্ষা কৌশল এবং কার্যনির্বাহী পরিকল্পনা মূল্যায়ন করে। MS-এ সীমানির্ধারণকারী আচরণে ঘাটতি প্রিফ্রন্টাল-মধ্যস্থ টপ-ডাউন নিয়ন্ত্রণ দুর্বলতা প্রতিফলিত করে।'
						)}
					</p>
				</div>

				<TaskPracticeActions
					locale={$locale}
					startLabel={lt('Start Game', 'গেম শুরু করুন')}
					statusMessage={practiceStatusMessage}
					on:start={() => startGame(TASK_PLAY_MODE.RECORDED)}
					on:practice={() => startGame(TASK_PLAY_MODE.PRACTICE)}
				/>

			{:else}
				<LoadingSkeleton />
			{/if}

		{:else if gamePhase === 'playing'}

			<div class="game-card">
				{#if playMode === TASK_PLAY_MODE.PRACTICE}
					<PracticeModeBanner locale={$locale} />
				{/if}

				<!-- Status Bar -->
				<div class="game-status-bar">
					<div class="game-title-row">
						<div class="thinking-label">{lt("I'm thinking of something...", 'আমি কিছু একটা ভাবছি...')}</div>
						<div class="category-tag">{gameData?.category}</div>
					</div>
					<div class="question-counter {counterClass()}">
						{lt(`${questionsAsked} / 20`, `${questionsAsked} / ২০`)}
						<span class="counter-label">{lt('questions', 'প্রশ্ন')}</span>
					</div>
				</div>

				<!-- Question History -->
				<div class="history-section">
					<h3 class="history-heading">{lt('Question History', 'প্রশ্নের ইতিহাস')}</h3>
					<div class="history-list" id="questions-history">
						{#if questionsHistory.length === 0}
							<p class="history-empty">{lt('No questions asked yet — start asking!', 'এখনো কোনো প্রশ্ন করা হয়নি — শুরু করুন!')}</p>
						{:else}
							{#each questionsHistory as item, index}
								<div class="history-item">
									<div class="history-q">
										<span class="q-num">Q{index + 1}</span>
										<span class="q-text">{item.question}</span>
									</div>
									<div class="history-answer-row">
										<span class="answer-badge {answerClass(item.answer)}">{item.answer}</span>
										{#if item.confidence === 'high'}
											<span class="confidence-label">{lt('Confident', 'আত্মবিশ্বাসী')}</span>
										{/if}
									</div>
								</div>
							{/each}
						{/if}
					</div>
				</div>

				{#if askError}
					<div class="warn-card">
						{lt('Error processing question. Please try again.', 'প্রশ্ন প্রক্রিয়া করতে ত্রুটি। আবার চেষ্টা করুন।')}
					</div>
				{/if}

				<!-- Question Input -->
				{#if questionsAsked < 20}
					<div class="input-card">
						<label for="question-input" class="input-label">
							{lt('Ask a yes/no question:', 'একটি হ্যাঁ/না প্রশ্ন করুন:')}
						</label>
						<div class="input-row">
							<input
								id="question-input"
								type="text"
								bind:value={questionInput}
								on:keypress={handleQuestionKeyPress}
								placeholder={lt('e.g., Is it an animal?', 'যেমন: এটি কি প্রাণী?')}
								class="question-input"
							/>
							<button
								class="ask-btn"
								on:click={askQuestion}
								disabled={!questionInput.trim()}
							>
								{lt('Ask', 'প্রশ্ন করুন')}
							</button>
						</div>
						<p class="input-tip">{lt('Tip: Press Enter to submit', 'টিপ: এন্টার চাপলে সাবমিট হবে')}</p>
					</div>
				{:else}
					<div class="warn-card">
						{lt('You have used all 20 questions. Time to make your final guess!', 'আপনি ২০টি প্রশ্ন ব্যবহার করেছেন। এখন আপনার চূড়ান্ত অনুমান করুন!')}
					</div>
				{/if}

				<!-- Guess Section -->
				<div class="guess-card">
					<h3 class="guess-heading">{lt('Ready to guess?', 'অনুমান করতে প্রস্তুত?')}</h3>
					<label for="guess-input" class="input-label">
						{lt('What is it?', 'এটি কী?')}
					</label>
					<div class="input-row">
						<input
							id="guess-input"
							type="text"
							bind:value={guessInput}
							placeholder={lt('Enter your final guess...', 'আপনার চূড়ান্ত অনুমান লিখুন...')}
							class="guess-input"
						/>
						<button
							class="guess-btn"
							on:click={submitGuess}
							disabled={!guessInput.trim()}
						>
							{lt('Submit Guess', 'অনুমান দিন')}
						</button>
					</div>
				</div>

				<!-- Give Up -->
				{#if !showGiveUpConfirm}
					<div class="skip-row">
						<button class="btn-secondary" on:click={() => (showGiveUpConfirm = true)}>
							{lt('Give Up', 'হাল ছেড়ে দিন')}
						</button>
					</div>
				{:else}
					<div class="confirm-card">
						<p class="confirm-text">{lt('Are you sure you want to give up?', 'আপনি কি সত্যিই হাল ছেড়ে দিতে চান?')}</p>
						<div class="confirm-buttons">
							<button class="confirm-yes" on:click={() => endGame(false, 'Gave up')}>
								{lt('Yes, give up', 'হ্যাঁ, ছেড়ে দিন')}
							</button>
							<button class="confirm-no" on:click={() => (showGiveUpConfirm = false)}>
								{lt('No, keep going', 'না, চালিয়ে যাই')}
							</button>
						</div>
					</div>
				{/if}
			</div>

		{:else if gamePhase === 'results'}

			<!-- Results Header -->
			<div class="results-header">
				<div class="score-pill">
					<span class="score-label">{lt('Score', 'স্কোর')}</span>
					<span class="score-value">{results ? results.normalized_score : '—'}</span>
					<span class="score-max">/100</span>
				</div>
				<p class="results-subtitle">
					{lt('Twenty Questions Complete', 'টুয়েন্টি কোয়েশ্চেন্স সম্পন্ন')} ·
					{lt('The answer was:', 'উত্তর ছিল:')}
					<strong class="answer-reveal">{targetObject}</strong>
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
					<div class="metric-card metric-violet">
						<div class="metric-value">{results.questions_asked}</div>
						<div class="metric-label">{lt('Questions Used', 'ব্যবহৃত প্রশ্ন')}</div>
					</div>
					<div class="metric-card {results.correctly_identified ? 'metric-correct' : 'metric-incorrect'}">
						<div class="metric-value">{results.correctly_identified ? lt('Yes', 'হ্যাঁ') : lt('No', 'না')}</div>
						<div class="metric-label">{lt('Correct Guess', 'সঠিক অনুমান')}</div>
					</div>
					<div class="metric-card metric-amber">
						<div class="metric-value">{results.strategy_score ? results.strategy_score.toFixed(0) : '—'}%</div>
						<div class="metric-label">{lt('Strategy Score', 'কৌশল স্কোর')}</div>
					</div>
					<div class="metric-card metric-blue">
						<div class="metric-value">{results.question_efficiency ? results.question_efficiency.toFixed(0) : '—'}%</div>
						<div class="metric-label">{lt('Question Efficiency', 'প্রশ্নের দক্ষতা')}</div>
					</div>
				</div>

				<!-- Performance Details -->
				<div class="card">
					<h3 class="card-title">{lt('Performance Analysis', 'পারফরম্যান্স বিশ্লেষণ')}</h3>
					<div class="details-list">
						<div class="detail-row">
							<span>{lt('Rating', 'রেটিং')}</span>
							<strong>{performanceLabel(results.performance_rating)}</strong>
						</div>
						<div class="detail-row">
							<span>{lt('Constraint-Seeking Questions', 'সীমানির্ধারণকারী প্রশ্ন')}</span>
							<strong>{results.constraint_seeking_questions}</strong>
						</div>
						<div class="detail-row">
							<span>{lt('Specific Guesses Made', 'নির্দিষ্ট অনুমান')}</span>
							<strong>{results.specific_guesses}</strong>
						</div>
					</div>
				</div>

				<!-- Feedback -->
				<div class="card">
					<h3 class="card-title">{lt('Feedback', 'প্রতিক্রিয়া')}</h3>
					<p class="feedback-text">{results.feedback}</p>

					{#if results.tips}
						<div class="tips-box">
							<div class="tips-label">{lt('Tips for Next Time', 'পরের বারের জন্য পরামর্শ')}</div>
							<p class="tips-text">{results.tips}</p>
						</div>
					{/if}
				</div>

				<!-- Level Up -->
				{#if results.should_advance}
					<div class="levelup-card">
						<div class="levelup-badge">{lt('Level Up', 'লেভেল আপ')}</div>
						<p>
							{lt(
								`Excellent strategy! Moving to difficulty level ${gameData.difficulty + 1}.`,
								`দারুণ কৌশল! কঠিনতা স্তর ${gameData.difficulty + 1}-এ উন্নীত হচ্ছে।`
							)}
						</p>
					</div>
				{/if}
			{/if}

			<!-- Action Buttons -->
			<div class="action-buttons">
				<button class="start-button" on:click={() => goto('/dashboard')}>
					{lt('Return to Dashboard', 'ড্যাশবোর্ডে ফিরুন')}
				</button>
				<button class="btn-secondary" on:click={() => goto('/training')}>
					{lt('Next Task', 'পরবর্তী টাস্ক')}
				</button>
			</div>

		{/if}

		{#if gamePhase === 'intro' && gameData && !loadError}
			<button class="help-fab" on:click={() => {}}>?</button>
		{/if}
	</div>
</div>

{#if earnedBadges.length > 0}
	<BadgeNotification badges={earnedBadges} />
{/if}

<style>
	/* ── Page Layout ─────────────────────────────────── */
	.tq-page {
		min-height: 100vh;
		background: #C8DEFA;
		padding: 1.5rem;
	}

	.tq-wrapper {
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
		color: #6d28d9;
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
		background: linear-gradient(135deg, #5b21b6 0%, #7c3aed 100%);
		color: white;
		padding: 0.4rem 0.9rem;
		border-radius: 2rem;
		font-size: 0.813rem;
		font-weight: 600;
		margin-bottom: 1rem;
	}

	.badge-icon { font-size: 0.813rem; font-weight: 700; letter-spacing: 0.04em; }
	.concept-desc { color: #4b5563; font-size: 0.938rem; line-height: 1.6; margin: 0; }

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
		background: #f5f3ff;
		border-radius: 10px;
		padding: 0.875rem 1rem;
	}

	.rule-num {
		min-width: 2rem;
		height: 2rem;
		background: linear-gradient(135deg, #5b21b6 0%, #7c3aed 100%);
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

	/* ── Category Hint ─────────────────────────────────── */
	.hint-box {
		background: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%);
		border-radius: 12px;
		padding: 1.25rem;
	}

	.hint-label { font-size: 0.813rem; color: #5b21b6; font-weight: 500; margin-bottom: 0.5rem; }
	.hint-value { font-size: 1.5rem; font-weight: 800; color: #4c1d95; }

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

	.game-title-row { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; }

	.thinking-label {
		font-size: 1.25rem;
		font-weight: 700;
		color: #4c1d95;
	}

	.category-tag {
		background: #ede9fe;
		color: #5b21b6;
		padding: 0.3rem 0.875rem;
		border-radius: 2rem;
		font-size: 0.875rem;
		font-weight: 600;
	}

	/* ── Question Counter ─────────────────────────────── */
	.question-counter {
		padding: 0.5rem 1.25rem;
		border-radius: 2rem;
		font-size: 1.375rem;
		font-weight: 700;
		display: flex;
		align-items: baseline;
		gap: 0.4rem;
	}

	.counter-label { font-size: 0.813rem; font-weight: 400; }
	.counter-safe    { background: linear-gradient(135deg, #5b21b6 0%, #7c3aed 100%); color: white; }
	.counter-warn    { background: linear-gradient(135deg, #d97706 0%, #f59e0b 100%); color: white; }
	.counter-danger  { background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%); color: white; animation: counter-pulse 0.5s ease-in-out infinite; }

	/* ── Question History ─────────────────────────────── */
	.history-section { margin-bottom: 1.25rem; }

	.history-heading {
		font-size: 0.938rem;
		font-weight: 600;
		color: #5b21b6;
		margin: 0 0 0.75rem 0;
	}

	.history-list {
		display: flex;
		flex-direction: column;
		gap: 0.625rem;
		max-height: 360px;
		overflow-y: auto;
		padding-right: 0.25rem;
	}

	.history-empty { color: #9ca3af; font-style: italic; font-size: 0.875rem; text-align: center; padding: 1.5rem; }

	.history-item {
		background: #f5f3ff;
		border-radius: 8px;
		padding: 0.875rem 1rem;
		border-left: 4px solid #7c3aed;
	}

	.history-q { display: flex; align-items: flex-start; gap: 0.625rem; margin-bottom: 0.5rem; }

	.q-num {
		background: linear-gradient(135deg, #5b21b6 0%, #7c3aed 100%);
		color: white;
		padding: 0.1rem 0.5rem;
		border-radius: 0.375rem;
		font-size: 0.75rem;
		font-weight: 700;
		white-space: nowrap;
		flex-shrink: 0;
		margin-top: 0.125rem;
	}

	.q-text { font-size: 0.9rem; color: #374151; font-weight: 500; line-height: 1.4; }

	.history-answer-row { display: flex; align-items: center; gap: 0.5rem; }

	.answer-badge {
		padding: 0.2rem 0.75rem;
		border-radius: 1rem;
		font-size: 0.813rem;
		font-weight: 700;
		text-transform: uppercase;
	}

	.answer-yes     { background: #d1fae5; color: #065f46; }
	.answer-no      { background: #fee2e2; color: #991b1b; }
	.answer-partial { background: #fef3c7; color: #92400e; }

	.confidence-label { font-size: 0.75rem; color: #16a34a; font-weight: 500; }

	/* ── Input Card ───────────────────────────────────── */
	.input-card {
		background: #f5f3ff;
		border: 2px solid #ddd6fe;
		border-radius: 12px;
		padding: 1.25rem;
		margin-bottom: 1.25rem;
	}

	.input-label {
		display: block;
		color: #5b21b6;
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

	.question-input,
	.guess-input {
		flex: 1;
		padding: 0.875rem 1rem;
		font-size: 1rem;
		border: 2px solid #ddd6fe;
		border-radius: 10px;
		outline: none;
		background: white;
		color: #1a1a2e;
		transition: border-color 0.15s;
	}

	.question-input:focus,
	.guess-input:focus {
		border-color: #6d28d9;
		box-shadow: 0 0 0 3px rgba(109, 40, 217, 0.12);
	}

	.ask-btn {
		background: linear-gradient(135deg, #5b21b6 0%, #7c3aed 100%);
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

	.ask-btn:hover:not(:disabled) { opacity: 0.9; }
	.ask-btn:disabled { opacity: 0.45; cursor: not-allowed; }

	.input-tip { font-size: 0.8rem; color: #6d28d9; margin: 0; }

	/* ── Guess Card ───────────────────────────────────── */
	.guess-card {
		background: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%);
		border: 2px solid #c4b5fd;
		border-radius: 12px;
		padding: 1.25rem;
		margin-bottom: 1.25rem;
	}

	.guess-heading {
		font-size: 1rem;
		font-weight: 700;
		color: #4c1d95;
		margin: 0 0 0.75rem 0;
	}

	.guess-btn {
		background: linear-gradient(135deg, #059669 0%, #10b981 100%);
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

	.guess-btn:hover:not(:disabled) { opacity: 0.9; }
	.guess-btn:disabled { opacity: 0.45; cursor: not-allowed; }

	/* ── Skip / Give Up ───────────────────────────────── */
	.skip-row { display: flex; justify-content: flex-end; margin-top: 0.5rem; }

	/* ── Give Up Confirm ──────────────────────────────── */
	.confirm-card {
		background: #fff1f2;
		border: 2px solid #fda4af;
		border-radius: 12px;
		padding: 1.25rem;
		margin-top: 0.5rem;
		text-align: center;
	}

	.confirm-text { color: #9f1239; font-weight: 600; margin: 0 0 1rem 0; }

	.confirm-buttons { display: flex; gap: 0.75rem; justify-content: center; }

	.confirm-yes {
		background: #dc2626;
		color: white;
		border: none;
		border-radius: 8px;
		padding: 0.625rem 1.25rem;
		font-size: 0.875rem;
		font-weight: 600;
		cursor: pointer;
	}

	.confirm-no {
		background: white;
		color: #374151;
		border: 2px solid #d1d5db;
		border-radius: 8px;
		padding: 0.625rem 1.25rem;
		font-size: 0.875rem;
		font-weight: 600;
		cursor: pointer;
	}

	/* ── Results Header ───────────────────────────────── */
	.results-header {
		background: linear-gradient(135deg, #5b21b6 0%, #7c3aed 100%);
		border-radius: 16px;
		padding: 1.75rem;
		text-align: center;
		margin-bottom: 1rem;
		box-shadow: 0 4px 12px rgba(91, 33, 182, 0.35);
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
	.answer-reveal    { color: #fde68a; font-size: 1.125rem; }

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

	.metric-violet    { border-top-color: #6d28d9; }
	.metric-correct   { border-top-color: #16a34a; }
	.metric-incorrect { border-top-color: #dc2626; }
	.metric-amber     { border-top-color: #d97706; }
	.metric-blue      { border-top-color: #2563eb; }

	.metric-value { font-size: 1.625rem; font-weight: 700; color: #1a1a2e; }
	.metric-label { font-size: 0.75rem; color: #6b7280; margin-top: 0.25rem; }

	/* ── Feedback ─────────────────────────────────────── */
	.feedback-text { font-size: 0.938rem; color: #374151; line-height: 1.6; margin: 0 0 1rem 0; }

	.tips-box {
		background: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%);
		border-radius: 10px;
		padding: 1rem 1.25rem;
		margin-top: 0.5rem;
	}

	.tips-label { font-size: 0.875rem; font-weight: 700; color: #4c1d95; margin-bottom: 0.375rem; }
	.tips-text  { font-size: 0.875rem; color: #5b21b6; line-height: 1.6; margin: 0; }

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

	.action-buttons .btn-secondary { flex: 1; }
	.btn-secondary:hover { background: #f5f3ff; transform: translateY(-2px); }

	/* ── Help FAB ─────────────────────────────────────── */
	.help-fab {
		position: fixed;
		bottom: 2rem;
		right: 2rem;
		width: 3rem;
		height: 3rem;
		background: linear-gradient(135deg, #5b21b6 0%, #7c3aed 100%);
		color: white;
		border: none;
		border-radius: 50%;
		font-size: 1.25rem;
		font-weight: 700;
		cursor: pointer;
		box-shadow: 0 4px 12px rgba(91, 33, 182, 0.4);
		display: flex;
		align-items: center;
		justify-content: center;
	}

	/* ── Animations ───────────────────────────────────── */
	@keyframes counter-pulse {
		0%, 100% { transform: scale(1); }
		50%       { transform: scale(1.06); }
	}

	/* ── Responsive ───────────────────────────────────── */
	@media (max-width: 640px) {
		.info-grid      { grid-template-columns: 1fr; }
		.metrics-grid   { grid-template-columns: 1fr 1fr; }
		.action-buttons { flex-direction: column; }
		.game-status-bar { flex-direction: column; align-items: flex-start; }
		.confirm-buttons { flex-direction: column; }
	}
</style>

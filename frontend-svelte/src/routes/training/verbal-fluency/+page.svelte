<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { API_BASE_URL } from '$lib/api';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import { formatNumber, locale, localizeStimulusSymbol, translateText } from '$lib/i18n';
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

	let currentInput = '';
	let submittedWords = [];
	let validWords = [];
	let invalidWords = [];
	let seenRoots = new Set();

	let allLetterResults = [];
	let results = null;
	let earnedBadges = [];

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
			return value === 'above_average' ? 'গড়ের চেয়ে ভালো' : 'গড়ের নিচে';
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
			return `${n(sessionData.min_words_target)}+ মোট শব্দ (এমএস রোগীর গড়: প্রতি অক্ষরে ১০-১৩টি শব্দ)`;
		}

		return `${sessionData.min_words_target}+ total words (MS average: 10-13 per letter)`;
	}

	function validationMessage(reasonKey, extra = {}) {
		if (taskLocale() === 'bn') {
			const reasons = {
				empty_word: 'ফাঁকা শব্দ গ্রহণযোগ্য নয়',
				too_short: 'খুব ছোট (কমপক্ষে ২টি অক্ষর)',
				wrong_letter: `'${displayLetter(extra.targetLetter || '')}' দিয়ে শুরু হতে হবে`,
				already_used: 'এই শব্দটি আগেই ব্যবহার করা হয়েছে',
				variant_used: 'একই শব্দপরিবার আগেই ব্যবহার হয়েছে'
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

	function setTransform(event, value) {
		event.currentTarget.style.transform = value;
	}

	function setBorderColor(event, value) {
		event.currentTarget.style.borderColor = value;
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

			sessionData = await response.json();
			gamePhase = 'intro';
		} catch (error) {
			console.error('Error loading session:', error);
			alert(t('Failed to load task. Please try again.', $locale));
		}
	}

	function startFirstLetter() {
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
			finishSession();
		}
	}

	async function finishSession() {
		try {
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
		} catch (error) {
			console.error('Error scoring session:', error);
			alert(t('Error saving results. Please try again.', $locale));
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
		} catch (error) {
			console.error('Error saving results:', error);
		}
	}
</script>

<div
	data-localize-skip
	style="min-height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem;"
>
	<div style="max-width: 900px; margin: 0 auto;">
		{#if gamePhase === 'loading'}
			<div style="background: white; border-radius: 16px; padding: 3rem; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				<div style="font-size: 3rem; margin-bottom: 1rem;">⏳</div>
				<h2 style="color: #667eea;">{t('Loading Verbal Fluency Task...', $locale)}</h2>
			</div>
		{:else if gamePhase === 'intro'}
			<div style="background: white; border-radius: 16px; padding: 3rem; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				<div style="text-align: center; margin-bottom: 2rem;">
					<div style="font-size: 4rem; margin-bottom: 1rem;">🗣️</div>
					<div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 0.5rem;">
						<h1 style="color: #667eea; font-size: 2.5rem; margin: 0;">{sessionData.instructions.title}</h1>
						<DifficultyBadge difficulty={sessionData?.difficulty || 1} domain="Executive Planning" />
					</div>
					<p style="color: #64748b; font-size: 1.1rem;">{t('COWAT (Controlled Oral Word Association)', taskLocale())}</p>
				</div>

				<div style="background: #f8fafc; border-radius: 12px; padding: 2rem; margin-bottom: 2rem;">
					<h3 style="color: #1e293b; margin-bottom: 1rem;">📋 {t('Instructions', taskLocale())}</h3>
					<div style="color: #475569; line-height: 1.8; margin-bottom: 1.5rem;">
						{sessionData.instructions.description}
					</div>

					<div style="background: white; border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem;">
						<h4 style="color: #667eea; margin-bottom: 1rem;">{t('Rules:', taskLocale())}</h4>
						<ul style="color: #64748b; line-height: 2;">
							{#each sessionData.instructions.rules as rule}
								<li>{rule}</li>
							{/each}
						</ul>
					</div>
				</div>

				<div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border: 2px solid #f59e0b; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem;">
					<div style="display: flex; align-items: center; gap: 1rem;">
						<div style="font-size: 2rem;">📊</div>
						<div>
							<div style="font-weight: 700; color: #92400e; font-size: 1.1rem;">{sessionData.instructions.details_title || t('Session Details', taskLocale())}</div>
							<div style="color: #92400e; margin-top: 0.5rem;">
								<strong>{t('Letters:', taskLocale())}</strong> {lettersSummary()}
								<span style="margin-left: 1rem;">|</span>
								<strong style="margin-left: 1rem;">{t('Time per letter:', taskLocale())}</strong> {secondsLabel(sessionData.time_per_letter_seconds)}
							</div>
							<div style="color: #92400e; margin-top: 0.3rem;">
								<strong>{t('Target:', taskLocale())}</strong> {detailsSummary()}
							</div>
						</div>
					</div>
				</div>

				<div style="text-align: center;">
					<button
						on:click={startFirstLetter}
						style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none;
						padding: 1.2rem 3rem; font-size: 1.2rem; border-radius: 12px; cursor: pointer; font-weight: 600;
						box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4); transition: all 0.3s;"
						on:mouseenter={(event) => setTransform(event, 'translateY(-2px)')}
						on:mouseleave={(event) => setTransform(event, 'translateY(0)')}
					>
						{t('Start First Letter →', taskLocale())}
					</button>
				</div>
			</div>
		{:else if gamePhase === 'letter_round'}
			<div style="background: white; border-radius: 16px; padding: 3rem; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
					<h2 style="color: #667eea; margin: 0;">
						{taskLocale() === 'bn' ? 'অক্ষর:' : 'Letter:'}
						<span style="font-size: 3rem; font-weight: 800;"> {displayLetter(currentLetter)}</span>
					</h2>
					<div style="display: flex; gap: 1rem; align-items: center;">
						<span style="background: #f8fafc; color: #475569; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 600;">
							{taskLocale() === 'bn'
								? `অক্ষর ${n(currentLetterIndex + 1)} এর ${n(sessionData.letters.length)}`
								: `Letter ${currentLetterIndex + 1} of ${sessionData.letters.length}`}
						</span>
						<div
							style="background: {timeRemaining <= 10 ? '#fee2e2' : '#f0fdf4'};
							color: {timeRemaining <= 10 ? '#991b1b' : '#166534'};
							padding: 0.8rem 1.5rem; border-radius: 8px; font-size: 1.5rem; font-weight: 700;
							border: 2px solid {timeRemaining <= 10 ? '#ef4444' : '#22c55e'};"
						>
							⏱️ {compactSecondsLabel(timeRemaining)}
						</div>
					</div>
				</div>

				<div style="background: #f8fafc; border-radius: 12px; padding: 2rem; margin-bottom: 2rem;">
					<div style="display: flex; gap: 1rem; align-items: center; margin-bottom: 1rem;">
						<input
							id="verbal-word-input"
							type="text"
							bind:value={currentInput}
							on:keypress={handleKeyPress}
							placeholder={t('Type a word and press Enter or Space...', taskLocale())}
							autofocus
							style="flex: 1; padding: 1rem; font-size: 1.2rem; border: 2px solid #cbd5e1; border-radius: 8px; outline: none;"
							on:focus={(event) => setBorderColor(event, '#667eea')}
							on:blur={(event) => setBorderColor(event, '#cbd5e1')}
						/>
						<button
							on:click={submitWord}
							style="background: #667eea; color: white; border: none; padding: 1rem 2rem;
							font-size: 1.1rem; border-radius: 8px; cursor: pointer; font-weight: 600;"
						>
							{t('Submit', taskLocale())}
						</button>
					</div>
					<div style="color: #64748b; font-size: 0.9rem;">
						💡
						{t('Tip: Press Enter or Space to submit quickly', taskLocale())}
					</div>
				</div>

				<div style="margin-bottom: 2rem;">
					<h3 style="color: #22c55e; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">
						✅ {t('Valid Words', taskLocale())} ({n(validWords.length)})
					</h3>
					<div style="display: flex; flex-wrap: wrap; gap: 0.5rem; min-height: 60px; background: #f0fdf4; border-radius: 8px; padding: 1rem; border: 2px dashed #22c55e;">
						{#each validWords as word}
							<span style="background: #22c55e; color: white; padding: 0.5rem 1rem; border-radius: 6px; font-weight: 600;">
								{word}
							</span>
						{/each}
						{#if validWords.length === 0}
							<span style="color: #94a3b8; font-style: italic;">{t('No valid words yet...', taskLocale())}</span>
						{/if}
					</div>
				</div>

				{#if invalidWords.length > 0}
					<div style="margin-bottom: 2rem;">
						<h3 style="color: #ef4444; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">
							❌ {t('Invalid Words', taskLocale())} ({n(invalidWords.length)})
						</h3>
						<div style="display: flex; flex-wrap: wrap; gap: 0.5rem; background: #fee2e2; border-radius: 8px; padding: 1rem; border: 2px dashed #ef4444;">
							{#each invalidWords as item}
								<span
									style="background: #ef4444; color: white; padding: 0.5rem 1rem; border-radius: 6px; font-weight: 500; display: flex; align-items: center; gap: 0.5rem;"
									title={item.reason}
								>
									{item.word}
									<span style="font-size: 0.8rem; opacity: 0.8;">({item.reason})</span>
								</span>
							{/each}
						</div>
					</div>
				{/if}

				<div style="text-align: center; margin-top: 2rem;">
					<button
						on:click={endLetterRound}
						style="background: #f59e0b; color: white; border: none; padding: 1rem 2rem;
						font-size: 1.1rem; border-radius: 8px; cursor: pointer; font-weight: 600;"
					>
						{taskLocale() === 'bn' ? 'পরের অক্ষরে যান →' : 'Skip to Next Letter →'}
					</button>
				</div>
			</div>
		{:else if gamePhase === 'between_letters'}
			<div style="background: white; border-radius: 16px; padding: 3rem; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				<div style="font-size: 4rem; margin-bottom: 1rem;">✅</div>
				<h2 style="color: #22c55e; margin-bottom: 1rem;">{t('Letter Complete!', taskLocale())}</h2>
				<div style="background: #f0fdf4; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem;">
					<div style="color: #166534; font-size: 1.2rem;">
						{taskLocale() === 'bn'
							? `এই অক্ষরে আপনি ${validWordsSummary(validWords.length)} লিখেছেন`
							: `You found ${validWords.length} valid words for letter ${displayLetter(currentLetter)}`}
					</div>
				</div>
				<p style="color: #64748b; font-size: 1.1rem;">
					{taskLocale() === 'bn' ? 'পরের অক্ষর:' : 'Next letter:'}
					<strong style="font-size: 1.5rem; color: #667eea;"> {displayLetter(sessionData.letters[currentLetterIndex])}</strong>
				</p>
				<p style="color: #94a3b8; margin-top: 1rem;">{t('Starting in 2 seconds...', taskLocale())}</p>
			</div>
		{:else if gamePhase === 'results'}
			<div style="background: white; border-radius: 16px; padding: 3rem; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				<div style="text-align: center; margin-bottom: 2rem;">
					<h1 style="font-size: 2.5rem; color: #667eea; margin-bottom: 0.5rem;">{t('Session Complete!', taskLocale())}</h1>
					<div style="font-size: 3.5rem; font-weight: 700; color: #667eea; margin: 1rem 0;">
						{t('Score', taskLocale())}: {n(results.score)}/100
					</div>
				</div>

				<div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1.5rem; margin-bottom: 2rem;">
					<div style="background: #f0fdf4; border-radius: 12px; padding: 1.5rem; text-align: center; border: 2px solid #22c55e;">
						<div style="font-size: 2rem; font-weight: 700; color: #15803d;">
							{n(results.total_valid_words)}
						</div>
						<div style="color: #64748b; margin-top: 0.5rem;">{t('Total Valid Words', taskLocale())}</div>
					</div>

					<div style="background: #f5f3ff; border-radius: 12px; padding: 1.5rem; text-align: center; border: 2px solid #667eea;">
						<div style="font-size: 2rem; font-weight: 700; color: #5b21b6;">
							{averageWordsValue(results.avg_words_per_letter)}
						</div>
						<div style="color: #64748b; margin-top: 0.5rem;">{t('Avg Per Letter', taskLocale())}</div>
					</div>

					<div
						style="background: {results.performance === 'excellent' ? '#f0fdf4' : results.performance === 'good' ? '#fef3c7' : '#fee2e2'};
						border-radius: 12px; padding: 1.5rem; text-align: center;
						border: 2px solid {results.performance === 'excellent' ? '#22c55e' : results.performance === 'good' ? '#f59e0b' : '#ef4444'};"
					>
						<div
							style="font-size: 1.5rem; font-weight: 700;
							color: {results.performance === 'excellent' ? '#15803d' : results.performance === 'good' ? '#92400e' : '#991b1b'};"
						>
							{performanceLabel(results.performance)}
						</div>
						<div style="color: #64748b; margin-top: 0.5rem;">{t('Performance', taskLocale())}</div>
					</div>
				</div>

				<div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border: 2px solid #f59e0b; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem;">
					<div style="display: flex; align-items: center; gap: 1rem;">
						<div style="font-size: 2rem;">📊</div>
						<div>
							<div style="font-weight: 700; color: #92400e; font-size: 1.1rem;">{t('MS Patient Comparison', taskLocale())}</div>
							<div style="color: #92400e; margin-top: 0.5rem;">
								{results.ms_comparison.description}
							</div>
							<div style="color: #92400e; margin-top: 0.3rem;">
								{taskLocale() === 'bn' ? 'আপনার গড়:' : 'Your average:'}
								<strong> {averageWordsValue(results.ms_comparison.user_avg)} {taskLocale() === 'bn' ? 'শব্দ/অক্ষর' : 'words/letter'}</strong>
								{' - '}
								<strong>{comparisonStatusLabel(results.ms_comparison.status)}</strong>
							</div>
						</div>
					</div>
				</div>

				<div style="background: #f8fafc; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem;">
					<h3 style="color: #1e293b; margin-bottom: 1rem;">{t('Letter Breakdown', taskLocale())}</h3>
					<div style="display: grid; gap: 1rem;">
						{#each results.letter_results as letterResult}
							<div style="background: white; border-radius: 8px; padding: 1rem; border-left: 4px solid #667eea;">
								<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
									<span style="font-size: 1.5rem; font-weight: 700; color: #667eea;">
										{taskLocale() === 'bn' ? 'অক্ষর' : 'Letter'} {displayLetter(letterResult.letter)}
									</span>
									<span style="color: #22c55e; font-weight: 700; font-size: 1.2rem;">
										{wordsLabel(letterResult.valid_word_count)}
									</span>
								</div>
								<div style="display: flex; flex-wrap: wrap; gap: 0.3rem;">
									{#each letterResult.valid_words as word}
										<span style="background: #f0fdf4; color: #166534; padding: 0.3rem 0.6rem; border-radius: 4px; font-size: 0.9rem;">
											{word}
										</span>
									{/each}
								</div>
								{#if letterResult.invalid_word_count > 0}
									<div style="margin-top: 0.5rem; color: #ef4444; font-size: 0.9rem;">
										{invalidWordsSummary(letterResult.invalid_word_count)}
									</div>
								{/if}
							</div>
						{/each}
					</div>
				</div>

				<div style="text-align: center;">
					<button
						on:click={() => goto('/dashboard')}
						style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none;
						padding: 1rem 2rem; font-size: 1.1rem; border-radius: 8px; cursor: pointer; font-weight: 600;"
					>
						{t('Return to Dashboard', taskLocale())}
					</button>
				</div>
			</div>
		{/if}
	</div>
</div>

{#if earnedBadges.length > 0}
	<BadgeNotification badges={earnedBadges} />
{/if}

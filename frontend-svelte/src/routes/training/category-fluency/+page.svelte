<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { API_BASE_URL } from '$lib/api';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
	import { formatNumber, locale, localeText, translateText } from '$lib/i18n';
	import { buildPracticePayload, getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let gamePhase = 'loading'; // loading, intro, trial, results
	let trialData = null;
	let timeRemaining = 60;
	let timer = null;
	let startTime = null;
	let taskId = null;
	
	let currentInput = '';
	let submittedWords = [];
	let results = null;
	let earnedBadges = [];
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';
	let recordedTrialData = null;

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
			return `আপনার কাছে ${n(trialData.time_limit_seconds || 60)} সেকেন্ড সময় আছে। এই বিভাগের যত বেশি সম্ভব শব্দ লিখুন। প্রতিটি শব্দ লিখে এন্টার চাপুন।`;
		}

		return trialData.instructions;
	}

	function categoryTipText() {
		if ($locale === 'bn') {
			return 'মূল বিভাগটিকে ছোট ছোট ভাগে ভেবে দেখুন। যেমন পেশা হলে চিকিৎসা, শিক্ষা, প্রযুক্তি, রান্না, অফিসকাজ - এভাবে ভাগ করলে দ্রুত আরও শব্দ মনে আসবে।';
		}

		return 'Try thinking of subcategories! For example, if the category is "Animals," think of farm animals, pets, wild animals, birds, etc.';
	}

	function focusWordInput() {
		document.getElementById('word-input')?.focus();
	}

	function setTransform(event, value) {
		event.currentTarget.style.transform = value;
	}

	function setBorderColor(event, value) {
		event.currentTarget.style.borderColor = value;
	}

	function setBackgroundColor(event, value) {
		event.currentTarget.style.background = value;
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
			parts.push(`নোট: ${n(duplicateCount)}টি পুনরাবৃত্ত শব্দ গণনায় ধরা হয়নি।`);
		}

		if (uniqueCount < 10) {
			parts.push('পরামর্শ: উপবিভাগ ধরে ভাবলে আরও শব্দ দ্রুত মনে আসতে পারে।');
		}

		return parts.join(' ');
	}

	function progressBadgeLabel() {
		if (submittedWords.length >= 15) {
			return $locale === 'bn' ? 'দারুণ! 🌟' : 'Great! 🌟';
		}

		if (submittedWords.length >= 10) {
			return $locale === 'bn' ? 'ভালো অগ্রগতি 👍' : 'Good Progress 👍';
		}

		return '';
	}

	// Load trial on mount
	onMount(async () => {
		if (!$user) {
			goto('/login');
			return;
		}
		await loadTrial();
	});

	async function loadTrial() {
		try {
			const response = await fetch(`${API_BASE_URL}/api/training/tasks/category-fluency/generate/${$user.id}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				credentials: 'include'
			});

			if (!response.ok) throw new Error('Failed to load trial');
			
			const data = await response.json();
			trialData = structuredClone(data.trial_data);
			recordedTrialData = structuredClone(data.trial_data);
			gamePhase = 'intro';
		} catch (error) {
			console.error('Error loading trial:', error);
			alert('Failed to load task. Please try again.');
		}
	}

	function startTrial(nextMode = TASK_PLAY_MODE.RECORDED) {
		playMode = nextMode;
		practiceStatusMessage = '';
		trialData = nextMode === TASK_PLAY_MODE.PRACTICE
			? buildPracticePayload('category-fluency', recordedTrialData)
			: structuredClone(recordedTrialData);
		timeRemaining = trialData?.time_limit_seconds || 60;
		currentInput = '';
		submittedWords = [];
		gamePhase = 'trial';
		startTime = Date.now();
		
		// Start timer
		timer = setInterval(() => {
			timeRemaining--;
			if (timeRemaining <= 0) {
				endTrial();
			}
		}, 1000);

		// Focus input after a short delay
		setTimeout(() => {
			focusWordInput();
		}, 100);
	}

	function submitWord() {
		if (!currentInput.trim()) return;

		const word = currentInput.trim();
		submittedWords = [...submittedWords, word];
		currentInput = '';

		// Keep focus on input
		setTimeout(() => {
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
		const timeTaken = (Date.now() - startTime) / 1000;

		if (playMode === TASK_PLAY_MODE.PRACTICE) {
			trialData = structuredClone(recordedTrialData);
			playMode = TASK_PLAY_MODE.RECORDED;
			practiceStatusMessage = getPracticeCopy($locale).complete;
			gamePhase = 'intro';
			return;
		}

		taskId = $page.url.searchParams.get('taskId');
		
		try {
			const response = await fetch(`${API_BASE_URL}/api/training/tasks/category-fluency/submit/${$user.id}`, {
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
			});

			if (!response.ok) throw new Error('Failed to score trial');
			
			const data = await response.json();
			
			// Extract results from the response
			results = {
				normalized_score: data.score,
				unique_count: data.unique_count,
				total_submitted: data.total_submitted,
				duplicate_count: data.duplicate_count,
				performance_rating: data.performance_rating,
				words_per_second: data.words_per_second,
				feedback: data.feedback,
				should_advance: data.new_difficulty > data.old_difficulty,
				unique_words: submittedWords.filter((w, i, arr) => 
					arr.findIndex(x => x.toLowerCase() === w.toLowerCase()) === i
				),
				invalid_words: []
			};
			
			if (data.new_badges && data.new_badges.length > 0) {
				earnedBadges = data.new_badges;
			}

			// Update user store with new difficulty
			user.update(u => ({
				...u,
				planning_difficulty: data.new_difficulty
			}));

			gamePhase = 'results';
		} catch (error) {
			console.error('Error scoring trial:', error);
			alert('Error saving results. Please try again.');
		}
	}

	function getPerformanceColor(rating) {
		const colors = {
			excellent: '#10b981',
			good: '#3b82f6',
			average: '#f59e0b',
			below_average: '#ef4444'
		};
		return colors[rating] || '#64748b';
	}

	function getPerformanceEmoji(rating) {
		const emojis = {
			excellent: '🌟',
			good: '👍',
			average: '✓',
			below_average: '📈'
		};
		return emojis[rating] || '✓';
	}
</script>

<div
	style="min-height: 100vh; background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%); padding: 2rem;"
	data-localize-skip
>
	<div style="max-width: 900px; margin: 0 auto;">

		{#if gamePhase === 'loading'}
			<div style="background: white; border-radius: 16px; padding: 3rem; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				<div style="font-size: 3rem; margin-bottom: 1rem;">⏳</div>
				<h2 style="color: #8b5cf6;">{t('Loading Category Fluency Task...')}</h2>
			</div>

		{:else if gamePhase === 'intro'}
			<div style="background: white; border-radius: 16px; padding: 3rem; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				<div style="text-align: center; margin-bottom: 2rem;">
					<div style="font-size: 4rem; margin-bottom: 1rem;">🧠</div>
					<div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 0.5rem;">
						<h1 style="color: #8b5cf6; font-size: 2.5rem; margin: 0;">{t('Category Fluency')}</h1>
						<DifficultyBadge difficulty={5} domain="Executive Planning" />
					</div>
					<p style="color: #64748b; font-size: 1.1rem;">{t('Semantic Fluency Test')}</p>
				</div>

				<div style="background: #f8fafc; border-radius: 12px; padding: 2rem; margin-bottom: 2rem;">
					<h3 style="color: #1e293b; margin-bottom: 1rem;">📋 {t('Instructions')}</h3>
					<div style="color: #475569; line-height: 1.8; margin-bottom: 1.5rem;">
						{categoryInstructionText()}
					</div>
					
					<div style="background: white; border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem;">
						<h4 style="color: #8b5cf6; margin-bottom: 1rem;">{t('Rules:')}</h4>
						<ul style="color: #64748b; line-height: 2;">
							<li>{t('Type each word and press')} <strong>{$locale === 'bn' ? 'এন্টার' : 'Enter'}</strong> {t('to submit it')}</li>
							<li>{t('You can submit as many words as you can think of')}</li>
							<li>{t('Duplicate words will be automatically filtered out')}</li>
							<li>{t('You have 60 seconds to complete the task')}</li>
						</ul>
					</div>

					<div style="background: linear-gradient(135deg, #ddd6fe 0%, #c4b5fd 100%); border-radius: 8px; padding: 1.5rem; margin-top: 1rem;">
						<h4 style="color: #5b21b6; margin-bottom: 0.5rem;">{t('Your Category:')}</h4>
						<div style="font-size: 2rem; font-weight: 800; color: #5b21b6; margin-bottom: 0.5rem;">
							{localizedCategoryName()}
						</div>
						<div style="color: #6d28d9; font-size: 0.95rem;">
							{t('Examples:')} {localizedExamples()}
						</div>
					</div>
				</div>

				<div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border: 2px solid #f59e0b; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem;">
					<div style="display: flex; align-items: center; gap: 1rem;">
						<div style="font-size: 2rem;">💡</div>
						<div>
							<div style="font-weight: 700; color: #92400e; font-size: 1.1rem;">{t('Pro Tip')}</div>
							<div style="color: #92400e; margin-top: 0.5rem;">
								{categoryTipText()}
							</div>
						</div>
					</div>
				</div>

				<div style="text-align: center;">
					<TaskPracticeActions
						locale={$locale}
						startLabel={localeText({ en: 'Start Actual Task', bn: 'আসল টাস্ক শুরু করুন' }, $locale)}
						statusMessage={practiceStatusMessage}
						align="center"
						on:start={() => startTrial(TASK_PLAY_MODE.RECORDED)}
						on:practice={() => startTrial(TASK_PLAY_MODE.PRACTICE)}
					/>
					<button on:click={startTrial}
						hidden
						style="background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%); color: white; border: none; 
						padding: 1.2rem 3rem; font-size: 1.2rem; border-radius: 12px; cursor: pointer; font-weight: 600; 
						box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4); transition: all 0.3s;"
						on:mouseenter={(e) => setTransform(e, 'translateY(-2px)')}
						on:mouseleave={(e) => setTransform(e, 'translateY(0)')}>
						{t('Start Task')} →
					</button>
				</div>
			</div>

		{:else if gamePhase === 'trial'}
			<div style="background: white; border-radius: 16px; padding: 3rem; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				{#if playMode === TASK_PLAY_MODE.PRACTICE}
					<PracticeModeBanner locale={$locale} />
				{/if}
				<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
					<h2 style="color: #8b5cf6; margin: 0;">
						{t('Category:')} <span style="font-size: 2rem; font-weight: 800;">{localizedCategoryName()}</span>
					</h2>
					<div style="background: {timeRemaining <= 10 ? '#fee2e2' : '#f0fdf4'}; 
						color: {timeRemaining <= 10 ? '#991b1b' : '#166534'}; 
						padding: 0.75rem 1.5rem; border-radius: 12px; font-size: 1.5rem; font-weight: 700;
						box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
						⏱️ {compactSeconds(timeRemaining)}
					</div>
				</div>

				<div style="background: #f8fafc; border-radius: 12px; padding: 2rem; margin-bottom: 2rem;">
					<label for="word-input" style="display: block; color: #475569; font-weight: 600; margin-bottom: 0.5rem;">
						{t('Type a word and press Enter:')}
					</label>
					<input
						id="word-input"
						type="text"
						bind:value={currentInput}
						on:keypress={handleKeyPress}
						placeholder={t('Type your word here...')}
						style="width: 100%; padding: 1rem; font-size: 1.2rem; border: 2px solid #cbd5e1; 
						border-radius: 8px; outline: none; transition: all 0.3s;"
						on:focus={(e) => setBorderColor(e, '#8b5cf6')}
						on:blur={(e) => setBorderColor(e, '#cbd5e1')}
					/>
					<button on:click={submitWord}
						disabled={!currentInput.trim()}
						style="margin-top: 1rem; background: #8b5cf6; color: white; border: none; 
						padding: 0.75rem 2rem; font-size: 1rem; border-radius: 8px; cursor: pointer; 
						font-weight: 600; opacity: {currentInput.trim() ? '1' : '0.5'}; 
						transition: all 0.3s;">
						{t('Add Word')}
					</button>
				</div>

				<div style="background: #f8fafc; border-radius: 12px; padding: 2rem;">
					<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
						<h3 style="color: #1e293b; margin: 0;">
							{t('Your Words')} ({n(submittedWords.length)})
						</h3>
						{#if progressBadgeLabel()}
							<span style="background: #10b981; color: white; padding: 0.5rem 1rem; 
								border-radius: 20px; font-size: 0.9rem; font-weight: 600;">
								{progressBadgeLabel()}
							</span>
						{/if}
					</div>

					{#if submittedWords.length === 0}
						<p style="color: #94a3b8; text-align: center; padding: 2rem; font-style: italic;">
							{t('No words submitted yet. Start typing!')}
						</p>
					{:else}
						<div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
							{#each submittedWords as word, index}
								<div style="background: linear-gradient(135deg, #ddd6fe 0%, #c4b5fd 100%); 
									color: #5b21b6; padding: 0.5rem 1rem; border-radius: 20px; 
									display: flex; align-items: center; gap: 0.5rem; font-weight: 500;">
									{word}
									<button on:click={() => removeWord(index)}
										style="background: #5b21b6; color: white; border: none; 
										border-radius: 50%; width: 20px; height: 20px; cursor: pointer; 
										display: flex; align-items: center; justify-content: center; 
										font-size: 0.8rem; line-height: 1;"
										title={t('Remove word')}>
										×
									</button>
								</div>
							{/each}
						</div>
					{/if}
				</div>

				<div style="text-align: center; margin-top: 2rem;">
					<button on:click={endTrial}
						style="background: #64748b; color: white; border: none; 
						padding: 0.75rem 2rem; font-size: 1rem; border-radius: 8px; cursor: pointer; 
						font-weight: 600; transition: all 0.3s;"
						on:mouseenter={(e) => setBackgroundColor(e, '#475569')}
						on:mouseleave={(e) => setBackgroundColor(e, '#64748b')}>
						{t('Finish Early')}
					</button>
				</div>
			</div>

		{:else if gamePhase === 'results'}
			<div style="background: white; border-radius: 16px; padding: 3rem; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				<div style="text-align: center; margin-bottom: 2rem;">
					<div style="font-size: 4rem; margin-bottom: 1rem;">
						{getPerformanceEmoji(results.performance_rating)}
					</div>
					<h1 style="color: {getPerformanceColor(results.performance_rating)}; font-size: 2.5rem; margin-bottom: 0.5rem; text-transform: capitalize;">
						{performanceLabel(results.performance_rating)}!
					</h1>
					<p style="color: #64748b; font-size: 1.1rem;">{t('Category:')} {localizedCategoryName()}</p>
				</div>

				<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
					<div style="background: linear-gradient(135deg, #ddd6fe 0%, #c4b5fd 100%); 
						border-radius: 12px; padding: 1.5rem; text-align: center;">
						<div style="font-size: 2.5rem; font-weight: 800; color: #5b21b6; margin-bottom: 0.5rem;">
							{n(results.unique_count)}
						</div>
						<div style="color: #6d28d9; font-weight: 600;">{t('Unique Words')}</div>
					</div>

					<div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); 
						border-radius: 12px; padding: 1.5rem; text-align: center;">
						<div style="font-size: 2.5rem; font-weight: 800; color: #92400e; margin-bottom: 0.5rem;">
							{n(results.normalized_score, { maximumFractionDigits: 2 })}
						</div>
						<div style="color: #92400e; font-weight: 600;">{t('Score')}</div>
					</div>

					{#if results.duplicate_count > 0}
						<div style="background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); 
							border-radius: 12px; padding: 1.5rem; text-align: center;">
							<div style="font-size: 2.5rem; font-weight: 800; color: #991b1b; margin-bottom: 0.5rem;">
								{n(results.duplicate_count)}
							</div>
							<div style="color: #991b1b; font-weight: 600;">{t('Duplicates')}</div>
						</div>
					{/if}

					<div style="background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); 
						border-radius: 12px; padding: 1.5rem; text-align: center;">
						<div style="font-size: 2.5rem; font-weight: 800; color: #065f46; margin-bottom: 0.5rem;">
							{n(results.words_per_second, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}
						</div>
						<div style="color: #065f46; font-weight: 600;">{t('Words/Second')}</div>
					</div>
				</div>

				<div style="background: #f8fafc; border-radius: 12px; padding: 2rem; margin-bottom: 2rem;">
					<h3 style="color: #1e293b; margin-bottom: 1rem;">📊 {t('Feedback')}</h3>
					<p style="color: #475569; line-height: 1.8; margin-bottom: 1rem;">
						{performanceFeedback()}
					</p>

					{#if results.unique_words.length > 0}
						<div style="margin-top: 1.5rem;">
							<h4 style="color: #8b5cf6; margin-bottom: 0.5rem;">{t('Your Valid Words:')}</h4>
							<div style="color: #64748b; line-height: 1.8;">
								{results.unique_words.join(', ')}
							</div>
						</div>
					{/if}

					{#if results.invalid_words.length > 0}
						<div style="margin-top: 1.5rem; background: #fef2f2; border-radius: 8px; padding: 1rem;">
							<h4 style="color: #991b1b; margin-bottom: 0.5rem;">{t('Invalid/Duplicate Words:')}</h4>
							<div style="color: #7f1d1d; line-height: 1.8;">
								{results.invalid_words.join(', ')}
							</div>
						</div>
					{/if}
				</div>

				{#if results.should_advance}
					<div style="background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); 
						border: 2px solid #10b981; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem;">
						<div style="display: flex; align-items: center; gap: 1rem;">
							<div style="font-size: 2rem;">🎉</div>
							<div>
								<div style="font-weight: 700; color: #065f46; font-size: 1.1rem;">{t('Level Up!')}</div>
								<div style="color: #065f46; margin-top: 0.5rem;">
									{$locale === 'bn'
										? `দারুণ পারফরম্যান্স! কঠিনতা লেভেল ${n(trialData.difficulty + 1)}-এ উন্নীত করা হচ্ছে।`
										: `Great performance! Moving to difficulty level ${trialData.difficulty + 1}`}
								</div>
							</div>
						</div>
					</div>
				{/if}

				{#if earnedBadges.length > 0}
					{#each earnedBadges as badge}
						<BadgeNotification badges={[badge]} />
					{/each}
				{/if}

				<div style="display: flex; gap: 1rem; justify-content: center;">
					<button on:click={() => goto('/training')}
						style="background: #64748b; color: white; border: none; 
						padding: 1rem 2rem; font-size: 1.1rem; border-radius: 12px; cursor: pointer; 
						font-weight: 600; transition: all 0.3s;"
						on:mouseenter={(e) => setBackgroundColor(e, '#475569')}
						on:mouseleave={(e) => setBackgroundColor(e, '#64748b')}>
						← {t('Back to Training')}
					</button>

					<button on:click={() => location.reload()}
						style="background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%); color: white; border: none; 
						padding: 1rem 2rem; font-size: 1.1rem; border-radius: 12px; cursor: pointer; 
						font-weight: 600; box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4); transition: all 0.3s;"
						on:mouseenter={(e) => setTransform(e, 'translateY(-2px)')}
						on:mouseleave={(e) => setTransform(e, 'translateY(0)')}>
						{t('Try Again')} 🔄
					</button>
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	* {
		box-sizing: border-box;
	}
</style>

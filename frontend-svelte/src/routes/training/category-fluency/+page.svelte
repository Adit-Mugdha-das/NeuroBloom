<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { API_BASE_URL } from '$lib/api';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
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
			trialData = data.trial_data;
			gamePhase = 'intro';
		} catch (error) {
			console.error('Error loading trial:', error);
			alert('Failed to load task. Please try again.');
		}
	}

	function startTrial() {
		timeRemaining = 60;
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
			document.getElementById('word-input')?.focus();
		}, 100);
	}

	function submitWord() {
		if (!currentInput.trim()) return;

		const word = currentInput.trim();
		submittedWords = [...submittedWords, word];
		currentInput = '';

		// Keep focus on input
		setTimeout(() => {
			document.getElementById('word-input')?.focus();
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

<div style="min-height: 100vh; background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%); padding: 2rem;">
	<div style="max-width: 900px; margin: 0 auto;">

		{#if gamePhase === 'loading'}
			<div style="background: white; border-radius: 16px; padding: 3rem; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				<div style="font-size: 3rem; margin-bottom: 1rem;">⏳</div>
				<h2 style="color: #8b5cf6;">Loading Category Fluency Task...</h2>
			</div>

		{:else if gamePhase === 'intro'}
			<div style="background: white; border-radius: 16px; padding: 3rem; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				<div style="text-align: center; margin-bottom: 2rem;">
					<div style="font-size: 4rem; margin-bottom: 1rem;">🧠</div>
					<h1 style="color: #8b5cf6; font-size: 2.5rem; margin-bottom: 0.5rem;">Category Fluency</h1>
					<p style="color: #64748b; font-size: 1.1rem;">Semantic Fluency Test</p>
				</div>

				<div style="background: #f8fafc; border-radius: 12px; padding: 2rem; margin-bottom: 2rem;">
					<h3 style="color: #1e293b; margin-bottom: 1rem;">📋 Instructions</h3>
					<div style="color: #475569; line-height: 1.8; margin-bottom: 1.5rem;">
						{trialData.instructions}
					</div>
					
					<div style="background: white; border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem;">
						<h4 style="color: #8b5cf6; margin-bottom: 1rem;">Rules:</h4>
						<ul style="color: #64748b; line-height: 2;">
							<li>Type each word and press <strong>Enter</strong> to submit it</li>
							<li>You can submit as many words as you can think of</li>
							<li>Duplicate words will be automatically filtered out</li>
							<li>You have 60 seconds to complete the task</li>
						</ul>
					</div>

					<div style="background: linear-gradient(135deg, #ddd6fe 0%, #c4b5fd 100%); border-radius: 8px; padding: 1.5rem; margin-top: 1rem;">
						<h4 style="color: #5b21b6; margin-bottom: 0.5rem;">Your Category:</h4>
						<div style="font-size: 2rem; font-weight: 800; color: #5b21b6; margin-bottom: 0.5rem;">
							{trialData.category_name}
						</div>
						<div style="color: #6d28d9; font-size: 0.95rem;">
							Examples: {trialData.examples.join(', ')}
						</div>
					</div>
				</div>

				<div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border: 2px solid #f59e0b; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem;">
					<div style="display: flex; align-items: center; gap: 1rem;">
						<div style="font-size: 2rem;">💡</div>
						<div>
							<div style="font-weight: 700; color: #92400e; font-size: 1.1rem;">Pro Tip</div>
							<div style="color: #92400e; margin-top: 0.5rem;">
								Try thinking of subcategories! For example, if the category is "Animals," think of farm animals, pets, wild animals, birds, etc.
							</div>
						</div>
					</div>
				</div>

				<div style="text-align: center;">
					<button on:click={startTrial}
						style="background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%); color: white; border: none; 
						padding: 1.2rem 3rem; font-size: 1.2rem; border-radius: 12px; cursor: pointer; font-weight: 600; 
						box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4); transition: all 0.3s;"
						on:mouseenter={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
						on:mouseleave={(e) => e.currentTarget.style.transform = 'translateY(0)'}>
						Start Task →
					</button>
				</div>
			</div>

		{:else if gamePhase === 'trial'}
			<div style="background: white; border-radius: 16px; padding: 3rem; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
					<h2 style="color: #8b5cf6; margin: 0;">
						Category: <span style="font-size: 2rem; font-weight: 800;">{trialData.category_name}</span>
					</h2>
					<div style="background: {timeRemaining <= 10 ? '#fee2e2' : '#f0fdf4'}; 
						color: {timeRemaining <= 10 ? '#991b1b' : '#166534'}; 
						padding: 0.75rem 1.5rem; border-radius: 12px; font-size: 1.5rem; font-weight: 700;
						box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
						⏱️ {timeRemaining}s
					</div>
				</div>

				<div style="background: #f8fafc; border-radius: 12px; padding: 2rem; margin-bottom: 2rem;">
					<label for="word-input" style="display: block; color: #475569; font-weight: 600; margin-bottom: 0.5rem;">
						Type a word and press Enter:
					</label>
					<input
						id="word-input"
						type="text"
						bind:value={currentInput}
						on:keypress={handleKeyPress}
						placeholder="Type your word here..."
						style="width: 100%; padding: 1rem; font-size: 1.2rem; border: 2px solid #cbd5e1; 
						border-radius: 8px; outline: none; transition: all 0.3s;"
						on:focus={(e) => e.currentTarget.style.borderColor = '#8b5cf6'}
						on:blur={(e) => e.currentTarget.style.borderColor = '#cbd5e1'}
					/>
					<button on:click={submitWord}
						disabled={!currentInput.trim()}
						style="margin-top: 1rem; background: #8b5cf6; color: white; border: none; 
						padding: 0.75rem 2rem; font-size: 1rem; border-radius: 8px; cursor: pointer; 
						font-weight: 600; opacity: {currentInput.trim() ? '1' : '0.5'}; 
						transition: all 0.3s;">
						Add Word
					</button>
				</div>

				<div style="background: #f8fafc; border-radius: 12px; padding: 2rem;">
					<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
						<h3 style="color: #1e293b; margin: 0;">
							Your Words ({submittedWords.length})
						</h3>
						{#if submittedWords.length >= 15}
							<span style="background: #10b981; color: white; padding: 0.5rem 1rem; 
								border-radius: 20px; font-size: 0.9rem; font-weight: 600;">
								Great! 🌟
							</span>
						{:else if submittedWords.length >= 10}
							<span style="background: #3b82f6; color: white; padding: 0.5rem 1rem; 
								border-radius: 20px; font-size: 0.9rem; font-weight: 600;">
								Good Progress 👍
							</span>
						{/if}
					</div>

					{#if submittedWords.length === 0}
						<p style="color: #94a3b8; text-align: center; padding: 2rem; font-style: italic;">
							No words submitted yet. Start typing!
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
										title="Remove word">
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
						on:mouseenter={(e) => e.currentTarget.style.background = '#475569'}
						on:mouseleave={(e) => e.currentTarget.style.background = '#64748b'}>
						Finish Early
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
						{results.performance_rating.replace('_', ' ')}!
					</h1>
					<p style="color: #64748b; font-size: 1.1rem;">Category: {trialData.category_name}</p>
				</div>

				<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
					<div style="background: linear-gradient(135deg, #ddd6fe 0%, #c4b5fd 100%); 
						border-radius: 12px; padding: 1.5rem; text-align: center;">
						<div style="font-size: 2.5rem; font-weight: 800; color: #5b21b6; margin-bottom: 0.5rem;">
							{results.unique_count}
						</div>
						<div style="color: #6d28d9; font-weight: 600;">Unique Words</div>
					</div>

					<div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); 
						border-radius: 12px; padding: 1.5rem; text-align: center;">
						<div style="font-size: 2.5rem; font-weight: 800; color: #92400e; margin-bottom: 0.5rem;">
							{results.normalized_score}
						</div>
						<div style="color: #92400e; font-weight: 600;">Score</div>
					</div>

					{#if results.duplicate_count > 0}
						<div style="background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); 
							border-radius: 12px; padding: 1.5rem; text-align: center;">
							<div style="font-size: 2.5rem; font-weight: 800; color: #991b1b; margin-bottom: 0.5rem;">
								{results.duplicate_count}
							</div>
							<div style="color: #991b1b; font-weight: 600;">Duplicates</div>
						</div>
					{/if}

					<div style="background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); 
						border-radius: 12px; padding: 1.5rem; text-align: center;">
						<div style="font-size: 2.5rem; font-weight: 800; color: #065f46; margin-bottom: 0.5rem;">
							{results.words_per_second.toFixed(1)}
						</div>
						<div style="color: #065f46; font-weight: 600;">Words/Second</div>
					</div>
				</div>

				<div style="background: #f8fafc; border-radius: 12px; padding: 2rem; margin-bottom: 2rem;">
					<h3 style="color: #1e293b; margin-bottom: 1rem;">📊 Feedback</h3>
					<p style="color: #475569; line-height: 1.8; margin-bottom: 1rem;">
						{results.feedback}
					</p>

					{#if results.unique_words.length > 0}
						<div style="margin-top: 1.5rem;">
							<h4 style="color: #8b5cf6; margin-bottom: 0.5rem;">Your Valid Words:</h4>
							<div style="color: #64748b; line-height: 1.8;">
								{results.unique_words.join(', ')}
							</div>
						</div>
					{/if}

					{#if results.invalid_words.length > 0}
						<div style="margin-top: 1.5rem; background: #fef2f2; border-radius: 8px; padding: 1rem;">
							<h4 style="color: #991b1b; margin-bottom: 0.5rem;">Invalid/Duplicate Words:</h4>
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
								<div style="font-weight: 700; color: #065f46; font-size: 1.1rem;">Level Up!</div>
								<div style="color: #065f46; margin-top: 0.5rem;">
									Great performance! Moving to difficulty level {trialData.difficulty + 1}
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
						on:mouseenter={(e) => e.currentTarget.style.background = '#475569'}
						on:mouseleave={(e) => e.currentTarget.style.background = '#64748b'}>
						← Back to Training
					</button>

					<button on:click={() => location.reload()}
						style="background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%); color: white; border: none; 
						padding: 1rem 2rem; font-size: 1.1rem; border-radius: 12px; cursor: pointer; 
						font-weight: 600; box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4); transition: all 0.3s;"
						on:mouseenter={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
						on:mouseleave={(e) => e.currentTarget.style.transform = 'translateY(0)'}>
						Try Again 🔄
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

<script>
	import { goto } from '$app/navigation';
	import { API_BASE_URL } from '$lib/api';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let gamePhase = 'loading'; // loading, intro, letter_round, results
	let sessionData = null;
	let currentLetterIndex = 0;
	let currentLetter = '';
	let timeRemaining = 60;
	let timer = null;
	
	let currentInput = '';
	let submittedWords = [];
	let validWords = [];
	let invalidWords = [];
	let seenRoots = new Set();
	
	let allLetterResults = [];
	let results = null;
	let earnedBadges = [];

	// Load session on mount
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
					difficulty: difficulty,
					baseline_score: $user.planning_baseline
				})
			});

			if (!response.ok) throw new Error('Failed to load session');
			
			sessionData = await response.json();
			gamePhase = 'intro';
		} catch (error) {
			console.error('Error loading session:', error);
			alert('Failed to load task. Please try again.');
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
		
		// Start timer
		timer = setInterval(() => {
			timeRemaining--;
			if (timeRemaining <= 0) {
				endLetterRound();
			}
		}, 1000);
	}

	function getWordRoot(word) {
		word = word.toLowerCase();
		const suffixes = ["ing", "ed", "s", "es", "er", "est", "ly", "tion", "ness", "ment"];
		
		for (let suffix of suffixes.sort((a, b) => b.length - a.length)) {
			if (word.endsWith(suffix) && word.length > suffix.length + 2) {
				return word.slice(0, -suffix.length);
			}
		}
		return word;
	}

	function validateWord(word) {
		const wordClean = word.trim().toLowerCase();
		const targetLower = currentLetter.toLowerCase();

		if (!wordClean) return { valid: false, reason: "Empty word" };
		if (wordClean.length < 2) return { valid: false, reason: "Too short (min 2 letters)" };
		if (!wordClean.startsWith(targetLower)) {
			return { valid: false, reason: `Must start with '${currentLetter}'` };
		}

		// Check for duplicates
		if (submittedWords.map(w => w.toLowerCase()).includes(wordClean)) {
			return { valid: false, reason: "Already used" };
		}

		// Check for variants
		const root = getWordRoot(wordClean);
		if (seenRoots.has(root)) {
			return { valid: false, reason: "Variant already used" };
		}

		return { valid: true, root: root };
	}

	function submitWord() {
		if (!currentInput.trim()) return;

		const word = currentInput.trim();
		const validation = validateWord(word);

		submittedWords = [...submittedWords, word];

		if (validation.valid) {
			validWords = [...validWords, word];
			seenRoots.add(validation.root);
		} else {
			invalidWords = [...invalidWords, { word: word, reason: validation.reason }];
		}

		currentInput = '';
	}

	function handleKeyPress(event) {
		if (event.key === 'Enter' || event.key === ' ') {
			event.preventDefault();
			submitWord();
		}
	}

	function endLetterRound() {
		clearInterval(timer);
		
		// Save results for this letter
		allLetterResults.push({
			letter: currentLetter,
			words: validWords,
			time_taken_seconds: sessionData.time_per_letter_seconds - timeRemaining
		});

		// Check if more letters
		if (currentLetterIndex < sessionData.letters.length - 1) {
			currentLetterIndex++;
			setTimeout(() => startLetterRound(), 2000); // 2 second break
			gamePhase = 'between_letters';
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

			// Save to backend
			await saveResults();

			gamePhase = 'results';
		} catch (error) {
			console.error('Error scoring session:', error);
			alert('Error saving results. Please try again.');
		}
	}

	async function saveResults() {
		try {
			const response = await fetch(`${API_BASE_URL}/api/training/complete`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				credentials: 'include',
				body: JSON.stringify({
					user_id: $user.id,
					domain: 'planning',
					task_type: 'verbal_fluency',
					score: results.score,
					difficulty: sessionData.difficulty,
					performance_data: results
				})
			});

			if (!response.ok) throw new Error('Failed to save results');
			
			const data = await response.json();
			
			if (data.badges_earned && data.badges_earned.length > 0) {
				earnedBadges = data.badges_earned;
			}

			// Update user store
			user.update(u => ({
				...u,
				planning_difficulty: data.new_difficulty,
				total_sessions: data.total_sessions
			}));

		} catch (error) {
			console.error('Error saving results:', error);
		}
	}
</script>

<div style="min-height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem;">
	<div style="max-width: 900px; margin: 0 auto;">

		{#if gamePhase === 'loading'}
			<div style="background: white; border-radius: 16px; padding: 3rem; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				<div style="font-size: 3rem; margin-bottom: 1rem;">⏳</div>
				<h2 style="color: #667eea;">Loading Verbal Fluency Task...</h2>
			</div>

		{:else if gamePhase === 'intro'}
			<div style="background: white; border-radius: 16px; padding: 3rem; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				<div style="text-align: center; margin-bottom: 2rem;">
					<div style="font-size: 4rem; margin-bottom: 1rem;">🗣️</div>
					<h1 style="color: #667eea; font-size: 2.5rem; margin-bottom: 0.5rem;">Verbal Fluency Test</h1>
					<p style="color: #64748b; font-size: 1.1rem;">COWAT (Controlled Oral Word Association)</p>
				</div>

				<div style="background: #f8fafc; border-radius: 12px; padding: 2rem; margin-bottom: 2rem;">
					<h3 style="color: #1e293b; margin-bottom: 1rem;">📋 Instructions</h3>
					<div style="color: #475569; line-height: 1.8; margin-bottom: 1.5rem;">
						{sessionData.instructions.description}
					</div>
					
					<div style="background: white; border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem;">
						<h4 style="color: #667eea; margin-bottom: 1rem;">Rules:</h4>
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
							<div style="font-weight: 700; color: #92400e; font-size: 1.1rem;">Session Details</div>
							<div style="color: #92400e; margin-top: 0.5rem;">
								<strong>Letters:</strong> {sessionData.letters.join(', ')} 
								<span style="margin-left: 1rem;">|</span>
								<strong style="margin-left: 1rem;">Time per letter:</strong> {sessionData.time_per_letter_seconds} seconds
							</div>
							<div style="color: #92400e; margin-top: 0.3rem;">
								<strong>Target:</strong> {sessionData.min_words_target}+ total words (MS average: 10-13 per letter)
							</div>
						</div>
					</div>
				</div>

				<div style="text-align: center;">
					<button on:click={startFirstLetter}
						style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; 
						padding: 1.2rem 3rem; font-size: 1.2rem; border-radius: 12px; cursor: pointer; font-weight: 600; 
						box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4); transition: all 0.3s;"
						on:mouseenter={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
						on:mouseleave={(e) => e.currentTarget.style.transform = 'translateY(0)'}>
						Start First Letter →
					</button>
				</div>
			</div>

		{:else if gamePhase === 'letter_round'}
			<div style="background: white; border-radius: 16px; padding: 3rem; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
					<h2 style="color: #667eea; margin: 0;">
						Letter: <span style="font-size: 3rem; font-weight: 800;">{currentLetter}</span>
					</h2>
					<div style="display: flex; gap: 1rem; align-items: center;">
						<span style="background: #f8fafc; color: #475569; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 600;">
							Letter {currentLetterIndex + 1} of {sessionData.letters.length}
						</span>
						<div style="background: {timeRemaining <= 10 ? '#fee2e2' : '#f0fdf4'}; 
							color: {timeRemaining <= 10 ? '#991b1b' : '#166534'}; 
							padding: 0.8rem 1.5rem; border-radius: 8px; font-size: 1.5rem; font-weight: 700;
							border: 2px solid {timeRemaining <= 10 ? '#ef4444' : '#22c55e'};">
							⏱️ {timeRemaining}s
						</div>
					</div>
				</div>

				<!-- Input area -->
				<div style="background: #f8fafc; border-radius: 12px; padding: 2rem; margin-bottom: 2rem;">
					<div style="display: flex; gap: 1rem; align-items: center; margin-bottom: 1rem;">
						<input
							type="text"
							bind:value={currentInput}
							on:keypress={handleKeyPress}
							placeholder="Type a word and press Enter or Space..."
							autofocus
							style="flex: 1; padding: 1rem; font-size: 1.2rem; border: 2px solid #cbd5e1; border-radius: 8px; outline: none;"
							on:focus={(e) => e.currentTarget.style.borderColor = '#667eea'}
							on:blur={(e) => e.currentTarget.style.borderColor = '#cbd5e1'}
						/>
						<button on:click={submitWord}
							style="background: #667eea; color: white; border: none; padding: 1rem 2rem; 
							font-size: 1.1rem; border-radius: 8px; cursor: pointer; font-weight: 600;">
							Submit
						</button>
					</div>
					<div style="color: #64748b; font-size: 0.9rem;">
						💡 Tip: Press <kbd style="background: white; padding: 0.2rem 0.5rem; border-radius: 4px; border: 1px solid #cbd5e1;">Enter</kbd> or <kbd style="background: white; padding: 0.2rem 0.5rem; border-radius: 4px; border: 1px solid #cbd5e1;">Space</kbd> to submit quickly
					</div>
				</div>

				<!-- Valid words -->
				<div style="margin-bottom: 2rem;">
					<h3 style="color: #22c55e; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">
						✅ Valid Words ({validWords.length})
					</h3>
					<div style="display: flex; flex-wrap: wrap; gap: 0.5rem; min-height: 60px; background: #f0fdf4; border-radius: 8px; padding: 1rem; border: 2px dashed #22c55e;">
						{#each validWords as word}
							<span style="background: #22c55e; color: white; padding: 0.5rem 1rem; border-radius: 6px; font-weight: 600;">
								{word}
							</span>
						{/each}
						{#if validWords.length === 0}
							<span style="color: #94a3b8; font-style: italic;">No valid words yet...</span>
						{/if}
					</div>
				</div>

				<!-- Invalid words -->
				{#if invalidWords.length > 0}
					<div style="margin-bottom: 2rem;">
						<h3 style="color: #ef4444; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">
							❌ Invalid Words ({invalidWords.length})
						</h3>
						<div style="display: flex; flex-wrap: wrap; gap: 0.5rem; background: #fee2e2; border-radius: 8px; padding: 1rem; border: 2px dashed #ef4444;">
							{#each invalidWords as item}
								<span style="background: #ef4444; color: white; padding: 0.5rem 1rem; border-radius: 6px; font-weight: 500; display: flex; align-items: center; gap: 0.5rem;"
									title={item.reason}>
									{item.word}
									<span style="font-size: 0.8rem; opacity: 0.8;">({item.reason})</span>
								</span>
							{/each}
						</div>
					</div>
				{/if}

				<div style="text-align: center; margin-top: 2rem;">
					<button on:click={endLetterRound}
						style="background: #f59e0b; color: white; border: none; padding: 1rem 2rem; 
						font-size: 1.1rem; border-radius: 8px; cursor: pointer; font-weight: 600;">
						Skip to Next Letter →
					</button>
				</div>
			</div>

		{:else if gamePhase === 'between_letters'}
			<div style="background: white; border-radius: 16px; padding: 3rem; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				<div style="font-size: 4rem; margin-bottom: 1rem;">✅</div>
				<h2 style="color: #22c55e; margin-bottom: 1rem;">Letter Complete!</h2>
				<div style="background: #f0fdf4; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem;">
					<div style="color: #166534; font-size: 1.2rem;">
						You found <strong>{validWords.length} valid words</strong> for letter <strong>{currentLetter}</strong>
					</div>
				</div>
				<p style="color: #64748b; font-size: 1.1rem;">
					Next letter: <strong style="font-size: 1.5rem; color: #667eea;">{sessionData.letters[currentLetterIndex]}</strong>
				</p>
				<p style="color: #94a3b8; margin-top: 1rem;">Starting in 2 seconds...</p>
			</div>

		{:else if gamePhase === 'results'}
			<div style="background: white; border-radius: 16px; padding: 3rem; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				<div style="text-align: center; margin-bottom: 2rem;">
					<h1 style="font-size: 2.5rem; color: #667eea; margin-bottom: 0.5rem;">Session Complete!</h1>
					<div style="font-size: 3.5rem; font-weight: 700; color: #667eea; margin: 1rem 0;">
						Score: {results.score}/100
					</div>
				</div>

				<div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1.5rem; margin-bottom: 2rem;">
					<div style="background: #f0fdf4; border-radius: 12px; padding: 1.5rem; text-align: center; border: 2px solid #22c55e;">
						<div style="font-size: 2rem; font-weight: 700; color: #15803d;">
							{results.total_valid_words}
						</div>
						<div style="color: #64748b; margin-top: 0.5rem;">Total Valid Words</div>
					</div>

					<div style="background: #f5f3ff; border-radius: 12px; padding: 1.5rem; text-align: center; border: 2px solid #667eea;">
						<div style="font-size: 2rem; font-weight: 700; color: #5b21b6;">
							{results.avg_words_per_letter}
						</div>
						<div style="color: #64748b; margin-top: 0.5rem;">Avg Per Letter</div>
					</div>

					<div style="background: {results.performance === 'excellent' ? '#f0fdf4' : results.performance === 'good' ? '#fef3c7' : '#fee2e2'}; 
						border-radius: 12px; padding: 1.5rem; text-align: center; 
						border: 2px solid {results.performance === 'excellent' ? '#22c55e' : results.performance === 'good' ? '#f59e0b' : '#ef4444'};">
						<div style="font-size: 1.5rem; font-weight: 700; 
							color: {results.performance === 'excellent' ? '#15803d' : results.performance === 'good' ? '#92400e' : '#991b1b'};">
							{results.performance === 'excellent' ? 'Excellent' : results.performance === 'good' ? 'Good' : results.performance === 'average' ? 'Average' : 'Below Average'}
						</div>
						<div style="color: #64748b; margin-top: 0.5rem;">Performance</div>
					</div>
				</div>

				<!-- MS Comparison -->
				<div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border: 2px solid #f59e0b; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem;">
					<div style="display: flex; align-items: center; gap: 1rem;">
						<div style="font-size: 2rem;">📊</div>
						<div>
							<div style="font-weight: 700; color: #92400e; font-size: 1.1rem;">MS Patient Comparison</div>
							<div style="color: #92400e; margin-top: 0.5rem;">
								{results.ms_comparison.description}
							</div>
							<div style="color: #92400e; margin-top: 0.3rem;">
								Your average: <strong>{results.ms_comparison.user_avg} words/letter</strong> - 
								<strong>{results.ms_comparison.status === 'above_average' ? 'Above Average ✨' : 'Below Average'}</strong>
							</div>
						</div>
					</div>
				</div>

				<!-- Letter breakdown -->
				<div style="background: #f8fafc; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem;">
					<h3 style="color: #1e293b; margin-bottom: 1rem;">Letter Breakdown</h3>
					<div style="display: grid; gap: 1rem;">
						{#each results.letter_results as letterResult}
							<div style="background: white; border-radius: 8px; padding: 1rem; border-left: 4px solid #667eea;">
								<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
									<span style="font-size: 1.5rem; font-weight: 700; color: #667eea;">
										Letter {letterResult.letter}
									</span>
									<span style="color: #22c55e; font-weight: 700; font-size: 1.2rem;">
										{letterResult.valid_word_count} words
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
										{letterResult.invalid_word_count} invalid word(s)
									</div>
								{/if}
							</div>
						{/each}
					</div>
				</div>

				<div style="text-align: center;">
					<button on:click={() => goto('/dashboard')}
						style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; 
						padding: 1rem 2rem; font-size: 1.1rem; border-radius: 8px; cursor: pointer; font-weight: 600;">
						Return to Dashboard
					</button>
				</div>
			</div>
		{/if}

	</div>
</div>

{#if earnedBadges.length > 0}
	<BadgeNotification badges={earnedBadges} />
{/if}

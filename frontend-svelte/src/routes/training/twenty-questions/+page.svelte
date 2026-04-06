<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { API_BASE_URL } from '$lib/api';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
	import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
	import { locale, localeText } from '$lib/i18n';
	import { getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let gamePhase = 'loading'; // loading, intro, playing, results
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
	let playMode = TASK_PLAY_MODE.RECORDED;
	let practiceStatusMessage = '';

	function lt(en, bn) {
		return localeText({ en, bn }, $locale);
	}

	// Load game on mount
	onMount(async () => {
		if (!$user) {
			goto('/login');
			return;
		}
		await loadGame();
	});

	async function loadGame() {
		try {
			const response = await fetch(`${API_BASE_URL}/api/training/tasks/twenty-questions/generate/${$user.id}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				credentials: 'include'
			});

			if (!response.ok) throw new Error('Failed to load game');
			
			const data = await response.json();
			gameData = data.game_data;
			targetObject = gameData.target_object_name;
			targetAttributes = gameData.target_attributes;
			gamePhase = 'intro';
		} catch (error) {
			console.error('Error loading game:', error);
			alert('Failed to load task. Please try again.');
		}
	}

	function startGame(nextMode = TASK_PLAY_MODE.RECORDED) {
		playMode = nextMode;
		practiceStatusMessage = '';
		questionsAsked = 0;
		questionsHistory = [];
		questionInput = '';
		guessInput = '';
		gamePhase = 'playing';
		
		// Focus input after a short delay
		setTimeout(() => {
			document.getElementById('question-input')?.focus();
		}, 100);
	}

	async function askQuestion() {
		if (!questionInput.trim()) return;

		const question = questionInput.trim();
		
		try {
			const response = await fetch(`${API_BASE_URL}/api/training/tasks/twenty-questions/ask/${$user.id}`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				credentials: 'include',
				body: JSON.stringify({
					question: question,
					target_attributes: targetAttributes,
					target_object_name: targetObject
				})
			});

			if (!response.ok) throw new Error('Failed to ask question');
			
			const data = await response.json();
			
			// Add to history
			questionsHistory = [...questionsHistory, {
				question: question,
				answer: data.answer,
				confidence: data.confidence
			}];
			
			questionsAsked++;
			questionInput = '';

			// Focus input again
			setTimeout(() => {
				document.getElementById('question-input')?.focus();
			}, 0);

			// Auto-scroll to latest question
			setTimeout(() => {
				const historyDiv = document.getElementById('questions-history');
				if (historyDiv) {
					historyDiv.scrollTop = historyDiv.scrollHeight;
				}
			}, 100);

		} catch (error) {
			console.error('Error asking question:', error);
			alert('Error processing question. Please try again.');
		}
	}

	function handleQuestionKeyPress(event) {
		if (event.key === 'Enter') {
			event.preventDefault();
			askQuestion();
		}
	}

	async function submitGuess() {
		if (!guessInput.trim()) {
			alert('Please enter your guess!');
			return;
		}

		const guess = guessInput.trim();
		const correctlyIdentified = guess.toLowerCase() === targetObject.toLowerCase();

		await endGame(correctlyIdentified, guess);
	}

	async function giveUp() {
		if (confirm('Are you sure you want to give up?')) {
			await endGame(false, 'Gave up');
		}
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

		try {
			taskId = $page.url.searchParams.get('taskId');
			const response = await fetch(`${API_BASE_URL}/api/training/tasks/twenty-questions/submit/${$user.id}`, {
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
			});

			if (!response.ok) throw new Error('Failed to submit game');
			
			const data = await response.json();
			
			// Extract results from the response
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
			console.error('Error submitting game:', error);
			alert('Error saving results. Please try again.');
		}
	}

	function getPerformanceColor(rating) {
		const colors = {
			excellent: '#10b981',
			good: '#3b82f6',
			average: '#f59e0b',
			below_average: '#ef4444',
			incorrect: '#7f1d1d'
		};
		return colors[rating] || '#64748b';
	}

	function getPerformanceEmoji(rating) {
		const emojis = {
			excellent: '🌟',
			good: '👍',
			average: '✓',
			below_average: '📈',
			incorrect: '❌'
		};
		return emojis[rating] || '✓';
	}

	function getAnswerStyle(answer) {
		if (answer.toLowerCase() === 'yes') {
			return 'background: #d1fae5; color: #065f46;';
		} else if (answer.toLowerCase() === 'no') {
			return 'background: #fee2e2; color: #991b1b;';
		} else {
			return 'background: #fef3c7; color: #92400e;';
		}
	}
</script>

<div style="min-height: 100vh; background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 2rem;">
	<div style="max-width: 1000px; margin: 0 auto;">

		{#if gamePhase === 'loading'}
			<div style="background: white; border-radius: 16px; padding: 3rem; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				<div style="font-size: 3rem; margin-bottom: 1rem;">⏳</div>
				<h2 style="color: #f59e0b;">Loading Twenty Questions...</h2>
			</div>

		{:else if gamePhase === 'intro'}
			<div style="background: white; border-radius: 16px; padding: 3rem; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				<div style="text-align: center; margin-bottom: 2rem;">
					<div style="font-size: 4rem; margin-bottom: 1rem;">🤔</div>
					<div style="display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 0.5rem;">
						<h1 style="color: #f59e0b; font-size: 2.5rem; margin: 0;">Twenty Questions</h1>
						<DifficultyBadge difficulty={5} domain="Executive Planning" />
					</div>
					<p style="color: #64748b; font-size: 1.1rem;">Strategic Problem-Solving Task</p>
				</div>

				<div style="background: #f8fafc; border-radius: 12px; padding: 2rem; margin-bottom: 2rem;">
					<h3 style="color: #1e293b; margin-bottom: 1rem;">📋 How to Play</h3>
					<div style="color: #475569; line-height: 1.8; margin-bottom: 1.5rem;">
						{gameData.instructions}
					</div>
					
					<div style="background: white; border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem;">
						<h4 style="color: #f59e0b; margin-bottom: 1rem;">Game Rules:</h4>
						<ul style="color: #64748b; line-height: 2;">
							<li>Ask yes/no questions to narrow down possibilities</li>
							<li>Use strategic "constraint-seeking" questions (e.g., "Is it living?")</li>
							<li>Avoid specific guesses until you're confident</li>
							<li>You have up to 20 questions to identify the object</li>
							<li>Fewer questions = higher score!</li>
						</ul>
					</div>

					<div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-radius: 8px; padding: 1.5rem; margin-top: 1rem;">
						<h4 style="color: #92400e; margin-bottom: 0.5rem;">Category Hint:</h4>
						<div style="font-size: 1.5rem; font-weight: 700; color: #92400e;">
							{gameData.hint}
						</div>
					</div>
				</div>

				<div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); border: 2px solid #3b82f6; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem;">
					<div style="display: flex; align-items: center; gap: 1rem;">
						<div style="font-size: 2rem;">💡</div>
						<div>
							<div style="font-weight: 700; color: #1e40af; font-size: 1.1rem;">Strategy Tip</div>
							<div style="color: #1e40af; margin-top: 0.5rem;">
								Start with broad questions like "Is it living?" or "Is it an animal?" before asking specific questions like "Is it a dog?"
							</div>
						</div>
					</div>
				</div>

				<div style="text-align: center;">
					<TaskPracticeActions
						locale={$locale}
						align="center"
						startLabel={lt('Start Game', 'গেম শুরু করুন')}
						statusMessage={practiceStatusMessage}
						on:start={() => startGame(TASK_PLAY_MODE.RECORDED)}
						on:practice={() => startGame(TASK_PLAY_MODE.PRACTICE)}
					/>
				</div>
			</div>

		{:else if gamePhase === 'playing'}
			<div style="background: white; border-radius: 16px; padding: 3rem; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
				{#if playMode === TASK_PLAY_MODE.PRACTICE}
					<PracticeModeBanner locale={$locale} />
				{/if}

				<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
					<h2 style="color: #f59e0b; margin: 0;">
						🤔 I'm thinking of something...
					</h2>
					<div style="background: {questionsAsked >= 18 ? '#fee2e2' : '#f0fdf4'}; 
						color: {questionsAsked >= 18 ? '#991b1b' : '#166534'}; 
						padding: 0.75rem 1.5rem; border-radius: 12px; font-size: 1.3rem; font-weight: 700;
						box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
						Questions: {questionsAsked}/20
					</div>
				</div>

				<div style="background: #fef3c7; border: 2px solid #f59e0b; border-radius: 12px; padding: 1rem; margin-bottom: 2rem;">
					<div style="color: #92400e; font-weight: 600; text-align: center;">
						Category: {gameData.category}
					</div>
				</div>

				<div style="background: #f8fafc; border-radius: 12px; padding: 2rem; margin-bottom: 2rem; max-height: 400px; overflow-y: auto;" id="questions-history">
					<h3 style="color: #1e293b; margin-bottom: 1rem;">
						Question History
					</h3>

					{#if questionsHistory.length === 0}
						<p style="color: #94a3b8; text-align: center; padding: 2rem; font-style: italic;">
							No questions asked yet. Start asking!
						</p>
					{:else}
						<div style="display: flex; flex-direction: column; gap: 0.75rem;">
							{#each questionsHistory as item, index}
								<div style="background: white; border-radius: 8px; padding: 1rem; border-left: 4px solid #f59e0b;">
									<div style="color: #475569; font-weight: 600; margin-bottom: 0.5rem;">
										Q{index + 1}: {item.question}
									</div>
									<div style="display: flex; align-items: center; gap: 0.5rem;">
										<span style="padding: 0.25rem 0.75rem; border-radius: 12px; font-weight: 600; font-size: 0.9rem; {getAnswerStyle(item.answer)}">
											{item.answer}
										</span>
										{#if item.confidence === 'high'}
											<span style="color: #10b981; font-size: 0.85rem;">✓ Confident</span>
										{/if}
									</div>
								</div>
							{/each}
						</div>
					{/if}
				</div>

				{#if questionsAsked < 20}
					<div style="background: #f8fafc; border-radius: 12px; padding: 2rem; margin-bottom: 2rem;">
						<label for="question-input" style="display: block; color: #475569; font-weight: 600; margin-bottom: 0.5rem;">
							Ask a yes/no question:
						</label>
						<div style="display: flex; gap: 1rem;">
							<input
								id="question-input"
								type="text"
								bind:value={questionInput}
								on:keypress={handleQuestionKeyPress}
								placeholder="e.g., Is it an animal?"
								style="flex: 1; padding: 1rem; font-size: 1.1rem; border: 2px solid #cbd5e1; 
								border-radius: 8px; outline: none; transition: all 0.3s;"
								on:focus={(e) => { e.currentTarget.style.borderColor = '#f59e0b'; }}
								on:blur={(e) => { e.currentTarget.style.borderColor = '#cbd5e1'; }}
							/>
							<button on:click={askQuestion}
								disabled={!questionInput.trim()}
								style="background: #f59e0b; color: white; border: none; 
								padding: 1rem 2rem; font-size: 1.1rem; border-radius: 8px; cursor: pointer; 
								font-weight: 600; opacity: {questionInput.trim() ? '1' : '0.5'}; 
								white-space: nowrap; transition: all 0.3s;">
								Ask Question
							</button>
						</div>
					</div>
				{/if}

				<div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); border-radius: 12px; padding: 2rem;">
					<h3 style="color: #1e40af; margin-bottom: 1rem;">Ready to guess?</h3>
					<label for="guess-input" style="display: block; color: #1e40af; font-weight: 600; margin-bottom: 0.5rem;">
						What is it?
					</label>
					<div style="display: flex; gap: 1rem;">
						<input
							id="guess-input"
							type="text"
							bind:value={guessInput}
							placeholder="Enter your guess..."
							style="flex: 1; padding: 1rem; font-size: 1.1rem; border: 2px solid #3b82f6; 
							border-radius: 8px; outline: none; transition: all 0.3s;"
						/>
						<button on:click={submitGuess}
							disabled={!guessInput.trim()}
							style="background: #10b981; color: white; border: none; 
							padding: 1rem 2rem; font-size: 1.1rem; border-radius: 8px; cursor: pointer; 
							font-weight: 600; opacity: {guessInput.trim() ? '1' : '0.5'}; 
							white-space: nowrap; transition: all 0.3s;">
							Submit Guess
						</button>
					</div>
				</div>

				<div style="text-align: center; margin-top: 2rem;">
					<button on:click={giveUp}
						style="background: #64748b; color: white; border: none; 
						padding: 0.75rem 2rem; font-size: 1rem; border-radius: 8px; cursor: pointer; 
						font-weight: 600; transition: all 0.3s;"
						on:mouseenter={(e) => { e.currentTarget.style.background = '#475569'; }}
						on:mouseleave={(e) => { e.currentTarget.style.background = '#64748b'; }}>
						Give Up
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
					<p style="color: #64748b; font-size: 1.3rem; font-weight: 600; margin-top: 1rem;">
						The answer was: <span style="color: #f59e0b; font-size: 1.5rem;">{targetObject}</span>
					</p>
				</div>

				<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
					<div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); 
						border-radius: 12px; padding: 1.5rem; text-align: center;">
						<div style="font-size: 2.5rem; font-weight: 800; color: #92400e; margin-bottom: 0.5rem;">
							{results.questions_asked}
						</div>
						<div style="color: #92400e; font-weight: 600;">Questions Used</div>
					</div>

					<div style="background: linear-gradient(135deg, {results.correctly_identified ? '#d1fae5' : '#fee2e2'} 0%, {results.correctly_identified ? '#a7f3d0' : '#fecaca'} 100%); 
						border-radius: 12px; padding: 1.5rem; text-align: center;">
						<div style="font-size: 2.5rem; font-weight: 800; color: {results.correctly_identified ? '#065f46' : '#991b1b'}; margin-bottom: 0.5rem;">
							{results.correctly_identified ? '✓' : '✗'}
						</div>
						<div style="color: {results.correctly_identified ? '#065f46' : '#991b1b'}; font-weight: 600;">
							{results.correctly_identified ? 'Correct!' : 'Incorrect'}
						</div>
					</div>

					<div style="background: linear-gradient(135deg, #ddd6fe 0%, #c4b5fd 100%); 
						border-radius: 12px; padding: 1.5rem; text-align: center;">
						<div style="font-size: 2.5rem; font-weight: 800; color: #5b21b6; margin-bottom: 0.5rem;">
							{results.normalized_score}
						</div>
						<div style="color: #5b21b6; font-weight: 600;">Score</div>
					</div>

					<div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); 
						border-radius: 12px; padding: 1.5rem; text-align: center;">
						<div style="font-size: 2.5rem; font-weight: 800; color: #1e40af; margin-bottom: 0.5rem;">
							{results.strategy_score.toFixed(0)}%
						</div>
						<div style="color: #1e40af; font-weight: 600;">Strategy Score</div>
					</div>
				</div>

				<div style="background: #f8fafc; border-radius: 12px; padding: 2rem; margin-bottom: 2rem;">
					<h3 style="color: #1e293b; margin-bottom: 1rem;">📊 Performance Analysis</h3>
					<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem;">
						<div>
							<span style="color: #64748b;">Question Efficiency:</span>
							<strong style="color: #1e293b;"> {results.question_efficiency.toFixed(0)}%</strong>
						</div>
						<div>
							<span style="color: #64748b;">Constraint-Seeking Questions:</span>
							<strong style="color: #1e293b;"> {results.constraint_seeking_questions}</strong>
						</div>
						<div>
							<span style="color: #64748b;">Specific Guesses:</span>
							<strong style="color: #1e293b;"> {results.specific_guesses}</strong>
						</div>
					</div>

					<div style="background: white; border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem;">
						<h4 style="color: #f59e0b; margin-bottom: 0.5rem;">Feedback:</h4>
						<p style="color: #475569; line-height: 1.8;">
							{results.feedback}
						</p>
					</div>

					<div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); border-radius: 8px; padding: 1.5rem;">
						<h4 style="color: #1e40af; margin-bottom: 0.5rem;">💡 Tips for Next Time:</h4>
						<p style="color: #1e40af; line-height: 1.8;">
							{results.tips}
						</p>
					</div>
				</div>

				{#if results.should_advance}
					<div style="background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); 
						border: 2px solid #10b981; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem;">
						<div style="display: flex; align-items: center; gap: 1rem;">
							<div style="font-size: 2rem;">🎉</div>
							<div>
								<div style="font-weight: 700; color: #065f46; font-size: 1.1rem;">Level Up!</div>
								<div style="color: #065f46; margin-top: 0.5rem;">
									Excellent strategy! Moving to a harder difficulty level
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
						style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; border: none; 
						padding: 1rem 2rem; font-size: 1.1rem; border-radius: 12px; cursor: pointer; 
						font-weight: 600; box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4); transition: all 0.3s;"
						on:mouseenter={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
						on:mouseleave={(e) => e.currentTarget.style.transform = 'translateY(0)'}>
						Play Again 🔄
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

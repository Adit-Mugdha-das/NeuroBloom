<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { API_BASE_URL } from '$lib/api';
	import BadgeNotification from '$lib/components/BadgeNotification.svelte';
	import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
	import { formatNumber, formatPercent, locale, localizeStimulusSymbol, translateText } from '$lib/i18n';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import { onMount } from 'svelte';

	const STATE = {
		LOADING: 'loading',
		INSTRUCTIONS: 'instructions',
		ROUND_INTRO: 'round_intro',
		PLAYING: 'playing',
		TRIAL_FEEDBACK: 'trial_feedback',
		COMPLETE: 'complete'
	};

	let state = STATE.LOADING;
	let difficulty = 5;
	let sessionData = null;
	let trials = [];
	let currentTrialIndex = 0;
	let currentTrial = null;
	let currentStimulusIndex = -1;
	let highlightedPosition = null;
	let currentLetter = '';
	let taskId = null;
	let showHelp = false;
	let speechEnabled = false;
	let visualResponseSelected = false;
	let audioResponseSelected = false;
	let responseEnabled = false;
	let responseLocked = false;
	let stepStartTime = 0;
	let lastActionTime = 0;
	let sessionStartedAt = 0;
	let sessionResults = null;
	let newBadges = [];
	let feedbackSummary = null;
	let isDisposed = false;

	function t(text) {
		return translateText(text, $locale);
	}

	function n(value, options = {}) {
		return formatNumber(value, $locale, options);
	}

	function pct(value, options = {}) {
		return formatPercent(value, $locale, options);
	}

	function stimulus(value) {
		return localizeStimulusSymbol(value, $locale);
	}

	function roundLabel(current, total) {
		return $locale === 'bn' ? `রাউন্ড ${n(current)} / ${n(total)}` : `Round ${current} of ${total}`;
	}

	function nBackLabel(value) {
		return $locale === 'bn' ? `${n(value)}-ব্যাক` : `${value}-Back`;
	}

	function levelLabel(value) {
		return $locale === 'bn' ? `লেভেল ${n(value)}` : `Level ${value}`;
	}

	function wholePercent(value, options = {}) {
		return pct((Number(value) || 0) / 100, options);
	}

	function introSubtitle(level) {
		if ($locale === 'bn') {
			return `একই সঙ্গে চলমান ভিজ্যুয়াল অবস্থান এবং শোনা অক্ষর লক্ষ্য করুন। ${n(level)} ধাপ আগেরটির সঙ্গে মিললে উত্তর দিন।`;
		}
		return `Track a moving visual location and a spoken letter at the same time. Respond when either one matches what appeared ${level} steps back.`;
	}

	function observeInstruction(level) {
		if ($locale === 'bn') {
			return `${n(level)}টি আইটেম দেখা না হওয়া পর্যন্ত শুধু দেখুন এবং ক্রমটি মনে রাখুন।`;
		}
		return `Matches can happen separately or together. During the first ${level} items, just observe the stream and build the sequence in memory.`;
	}

	function roundIntroTitle(level) {
		return $locale === 'bn' ? `${nBackLabel(level)} সিকোয়েন্স শুরু হচ্ছে` : `${level}-Back Sequence Incoming`;
	}

	function roundIntroSupport() {
		return $locale === 'bn'
			? 'মাঝখানে মনোযোগ রাখুন। গ্রিডের আলো আর শোনা সংকেত কয়েক মুহূর্তের মধ্যেই শুরু হবে।'
			: 'Stay centered. The grid flash and the spoken cue will start in a moment.';
	}

	function focusRoundTitle(level) {
		return $locale === 'bn' ? `${nBackLabel(level)} মনোযোগ রাউন্ড` : `${level}-Back Focus Round`;
	}

	function responseSupportLabel() {
		if (responseEnabled) {
			return t('Mark visual and audio matches before the next cue arrives.');
		}
		return $locale === 'bn'
			? `${n(currentNLevel)}টি আইটেম না আসা পর্যন্ত শুধু লক্ষ্য করুন।`
			: `Observe only until ${currentNLevel} items have appeared.`;
	}

	function adaptationReasonLabel(reason) {
		return translateText(reason || '', $locale);
	}

	onMount(() => {
		taskId = $page.url.searchParams.get('taskId');
		speechEnabled = typeof window !== 'undefined' && 'speechSynthesis' in window;

		const handleKeyDown = (event) => {
			if (state !== STATE.PLAYING || !responseEnabled || responseLocked) return;

			const key = event.key.toLowerCase();
			if (key === 'v') {
				event.preventDefault();
				toggleVisualResponse();
			}
			if (key === 'a') {
				event.preventDefault();
				toggleAudioResponse();
			}
		};

		window.addEventListener('keydown', handleKeyDown);
		loadSession();

		return () => {
			isDisposed = true;
			window.removeEventListener('keydown', handleKeyDown);
			if (speechEnabled) {
				window.speechSynthesis.cancel();
			}
		};
	});

	function delay(ms) {
		return new Promise((resolve) => setTimeout(resolve, ms));
	}

	async function loadSession() {
		try {
			const userData = JSON.parse(localStorage.getItem('user') || '{}');
			const userId = userData.id;

			if (!userId) {
				goto('/login');
				return;
			}

			const queryDifficulty = Number.parseInt($page.url.searchParams.get('difficulty') || '', 10);
			const planResponse = await fetch(`${API_BASE_URL}/api/training/training-plan/${userId}`);
			const plan = await planResponse.json();

			let userDifficulty = 5;
			if (Number.isInteger(queryDifficulty) && queryDifficulty >= 1 && queryDifficulty <= 10) {
				userDifficulty = queryDifficulty;
			} else if (plan && plan.current_difficulty) {
				const currentDifficulty =
					typeof plan.current_difficulty === 'string'
						? JSON.parse(plan.current_difficulty)
						: plan.current_difficulty;
				userDifficulty = currentDifficulty.working_memory || 5;
			}

			difficulty = userDifficulty;

			const response = await fetch(
				`${API_BASE_URL}/api/training/tasks/dual-n-back/generate/${userId}?difficulty=${difficulty}&num_trials=4`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' }
				}
			);

			if (!response.ok) {
				throw new Error('Failed to load Dual N-Back session');
			}

			sessionData = await response.json();
			trials = structuredClone(sessionData.trials);
			state = STATE.INSTRUCTIONS;
		} catch (error) {
			console.error('Error loading Dual N-Back session:', error);
			alert(t('Failed to load Dual N-Back'));
			goto('/dashboard');
		}
	}

	function toggleVisualResponse() {
		if (!responseEnabled || responseLocked) return;
		visualResponseSelected = !visualResponseSelected;
		lastActionTime = Date.now();
	}

	function toggleAudioResponse() {
		if (!responseEnabled || responseLocked) return;
		audioResponseSelected = !audioResponseSelected;
		lastActionTime = Date.now();
	}

	function speakLetter(letter) {
		if (!speechEnabled || !letter || isDisposed) return;

		try {
			window.speechSynthesis.cancel();
			const spokenLetter = stimulus(letter);
			const utterance = new SpeechSynthesisUtterance(spokenLetter);
			utterance.lang = $locale === 'bn' ? 'bn-BD' : 'en-US';
			utterance.rate = 0.85;
			utterance.pitch = 1;
			utterance.volume = 1;
			window.speechSynthesis.speak(utterance);
		} catch (error) {
			console.warn('Speech synthesis unavailable for Dual N-Back:', error);
		}
	}

	async function startSession() {
		sessionStartedAt = Date.now();
		currentTrialIndex = 0;
		await startTrial();
	}

	async function startTrial() {
		currentTrial = structuredClone(trials[currentTrialIndex]);
		currentStimulusIndex = -1;
		feedbackSummary = null;
		state = STATE.ROUND_INTRO;

		await delay(1400);
		if (isDisposed) return;

		state = STATE.PLAYING;
		await playTrial(currentTrial);
	}

	async function playTrial(trial) {
		for (let index = 0; index < trial.stimuli.length; index += 1) {
			if (isDisposed) return;

			const stimulus = trial.stimuli[index];
			currentStimulusIndex = index;
			currentLetter = stimulus.letter;
			highlightedPosition = stimulus.position;
			visualResponseSelected = false;
			audioResponseSelected = false;
			responseLocked = false;
			responseEnabled = index >= trial.n_level;
			stepStartTime = Date.now();
			lastActionTime = 0;

			speakLetter(stimulus.letter);

			await delay(trial.stimulus_ms);
			if (isDisposed) return;

			highlightedPosition = null;

			await delay(trial.response_window_ms);
			if (isDisposed) return;

			responseLocked = true;
			stimulus.user_visual_match = responseEnabled ? visualResponseSelected : false;
			stimulus.user_audio_match = responseEnabled ? audioResponseSelected : false;
			stimulus.response_time_ms =
				responseEnabled && lastActionTime > 0 ? lastActionTime - stepStartTime : 0;
		}

		trials[currentTrialIndex] = currentTrial;
		feedbackSummary = summarizeTrial(currentTrial);
		state = STATE.TRIAL_FEEDBACK;

		await delay(1800);
		if (isDisposed) return;

		if (currentTrialIndex < trials.length - 1) {
			currentTrialIndex += 1;
			await startTrial();
		} else {
			await submitSession();
		}
	}

	function summarizeTrial(trial) {
		const eligibleStimuli = trial.stimuli.filter((stimulus) => stimulus.index >= trial.n_level);
		const correctVisual = eligibleStimuli.filter(
			(stimulus) => !!stimulus.user_visual_match === !!stimulus.visual_target
		).length;
		const correctAudio = eligibleStimuli.filter(
			(stimulus) => !!stimulus.user_audio_match === !!stimulus.audio_target
		).length;

		return {
			eligibleStimuli: eligibleStimuli.length,
			correctVisual,
			correctAudio
		};
	}

	async function submitSession() {
		state = STATE.LOADING;

		try {
			const userData = JSON.parse(localStorage.getItem('user') || '{}');
			const userId = userData.id;
			const durationSeconds = Math.max(1, Math.round((Date.now() - sessionStartedAt) / 1000));

			const response = await fetch(
				`${API_BASE_URL}/api/training/tasks/dual-n-back/submit/${userId}`,
				{
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						difficulty,
						trials,
						task_id: taskId,
						duration_seconds: durationSeconds
					})
				}
			);

			if (!response.ok) {
				throw new Error('Failed to submit Dual N-Back session');
			}

			sessionResults = await response.json();
			newBadges = sessionResults.new_badges || [];
			state = STATE.COMPLETE;
		} catch (error) {
			console.error('Error submitting Dual N-Back session:', error);
			alert(t('Failed to submit results'));
			goto('/dashboard');
		}
	}

	function gridCellClasses(position) {
		return [
			'grid-cell',
			highlightedPosition === position ? 'is-highlighted' : '',
			currentTrial?.stimuli?.[currentStimulusIndex]?.position === position && state === STATE.PLAYING
				? 'is-current'
				: ''
		]
			.filter(Boolean)
			.join(' ');
	}

	$: currentNLevel = currentTrial?.n_level ?? sessionData?.instructions?.n_level ?? 2;
	$: progressPercent =
		currentTrial && currentStimulusIndex >= 0
			? ((currentStimulusIndex + 1) / currentTrial.stimuli.length) * 100
			: 0;
</script>

<div class="dual-n-back-page">
	{#if state === STATE.LOADING}
		<LoadingSkeleton variant="card" count={3} />
	{:else if state === STATE.INSTRUCTIONS}
		<section class="hero-card">
			<div class="hero-header">
				<div>
					<p class="eyebrow">{t('Working Memory Training')}</p>
					<h1>{t('Dual N-Back')}</h1>
					<p class="subtitle">{introSubtitle(sessionData.instructions.n_level)}</p>
				</div>
				<DifficultyBadge {difficulty} domain="Working Memory" />
			</div>

			<div class="intro-grid">
				<div class="info-card emphasis">
					<h2>{t('How To Respond')}</h2>
					<div class="control-pills">
						<span>{t('Visual match:')} <strong>V</strong></span>
						<span>{t('Audio match:')} <strong>A</strong></span>
					</div>
					<p>{observeInstruction(sessionData.instructions.n_level)}</p>
				</div>

				<div class="info-card">
					<h2>{t('Session Layout')}</h2>
					<div class="stats-row">
						<div>
							<span class="stat-label">{t('Rounds')}</span>
							<strong>{n(sessionData.num_trials)}</strong>
						</div>
						<div>
							<span class="stat-label">{t('N-Level')}</span>
							<strong>{nBackLabel(sessionData.instructions.n_level)}</strong>
						</div>
						<div>
							<span class="stat-label">{t('Audio')}</span>
							<strong>{speechEnabled ? t('Enabled') : t('Visual fallback only')}</strong>
						</div>
					</div>
				</div>
			</div>

			<div class="tips-card">
				<div class="tips-header">
					<h2>{t('Performance Tips')}</h2>
					<button class="ghost-button" on:click={() => (showHelp = !showHelp)}>
						{showHelp ? t('Hide details') : t('Show details')}
					</button>
				</div>
				<ul>
					<li>{t('Keep your eyes on the grid center and let peripheral motion guide you.')}</li>
					<li>{t('Respond only when you are confident. False alarms make the task harder fast.')}</li>
					<li>{t('Use a steady internal rhythm rather than trying to rush each cue.')}</li>
				</ul>

				{#if showHelp}
					<div class="help-panel">
						<p><strong>{t('Warm-up phase:')}</strong> {t('no responses needed until enough items have appeared.')}</p>
						<p><strong>{t('Dual matches:')}</strong> {t('press both controls if both the position and letter repeat.')}</p>
						<p><strong>{t('Fallback:')}</strong> {t('if speech synthesis is blocked by the browser, the task still runs but the audio load is reduced.')}</p>
					</div>
				{/if}
			</div>

			<div class="action-row">
				<button class="primary-button" on:click={startSession}>{t('Start Dual N-Back')}</button>
				<button class="secondary-button" on:click={() => goto('/training')}>{t('Return to Training')}</button>
			</div>
		</section>
	{:else if state === STATE.ROUND_INTRO}
		<section class="play-card intro-state">
			<p class="eyebrow">{roundLabel(currentTrialIndex + 1, trials.length)}</p>
			<h2>{roundIntroTitle(currentNLevel)}</h2>
			<p>{roundIntroSupport()}</p>
		</section>
	{:else if state === STATE.PLAYING}
		<section class="play-card">
			<div class="play-header">
				<div>
					<p class="eyebrow">{roundLabel(currentTrialIndex + 1, trials.length)}</p>
					<h2>{focusRoundTitle(currentNLevel)}</h2>
				</div>
				<div class="status-cluster">
					<span class="status-chip">{n(currentStimulusIndex + 1)} / {n(currentTrial.stimuli.length)}</span>
					<span class="status-chip muted">{responseEnabled ? t('Response live') : t('Warm-up')}</span>
				</div>
			</div>

			<div class="progress-bar">
				<div class="progress-fill" style={`width: ${progressPercent}%`}></div>
			</div>

			<div class="arena">
				<div class="grid-card">
					<div class="grid-label">{t('Visual Stream')}</div>
					<div class="grid-board">
						{#each Array(9) as _, index}
							<div class={gridCellClasses(index)}></div>
						{/each}
					</div>
				</div>

				<div class="cue-card">
					<div class="cue-label">{t('Audio Stream')}</div>
					<div class="cue-letter">{speechEnabled ? t('Speaker cue active') : stimulus(currentLetter)}</div>
					<p class="cue-support">{responseSupportLabel()}</p>
				</div>
			</div>

			<div class="response-panel">
				<button
					class={`response-button visual ${visualResponseSelected ? 'active' : ''}`}
					on:click={toggleVisualResponse}
					disabled={!responseEnabled || responseLocked}
				>
					<span class="keycap">V</span>
					<span>{t('Visual Match')}</span>
				</button>

				<button
					class={`response-button audio ${audioResponseSelected ? 'active' : ''}`}
					on:click={toggleAudioResponse}
					disabled={!responseEnabled || responseLocked}
				>
					<span class="keycap">A</span>
					<span>{t('Audio Match')}</span>
				</button>
			</div>
		</section>
	{:else if state === STATE.TRIAL_FEEDBACK}
		<section class="play-card feedback-state">
			<p class="eyebrow">
				{$locale === 'bn'
					? `রাউন্ড ${n(currentTrialIndex + 1)} সম্পন্ন`
					: `Round ${currentTrialIndex + 1} complete`}
			</p>
			<h2>{t('Round Review')}</h2>
			<div class="feedback-grid">
				<div class="feedback-metric">
					<span>{t('Eligible cues')}</span>
					<strong>{n(feedbackSummary.eligibleStimuli)}</strong>
				</div>
				<div class="feedback-metric">
					<span>{t('Visual decisions correct')}</span>
					<strong>{n(feedbackSummary.correctVisual)}</strong>
				</div>
				<div class="feedback-metric">
					<span>{t('Audio decisions correct')}</span>
					<strong>{n(feedbackSummary.correctAudio)}</strong>
				</div>
			</div>
			<p class="feedback-note">
				{$locale === 'bn'
					? 'পরের রাউন্ডেও নির্ভুলতা এবং বেছে সাড়া দেওয়ার নিয়ন্ত্রণ সমান গুরুত্বপূর্ণ থাকবে।'
					: 'The next round keeps pressure on both accuracy and selective response control.'}
			</p>
		</section>
	{:else if state === STATE.COMPLETE}
		<section class="hero-card complete-state">
			<div class="hero-header">
				<div>
					<p class="eyebrow">{t('Session Complete')}</p>
					<h1>{$locale === 'bn' ? 'ডুয়াল এন-ব্যাক ফলাফল' : 'Dual N-Back Results'}</h1>
					<p class="subtitle">
						{$locale === 'bn'
							? 'আপনার ওয়ার্কিং মেমরি স্কোর আপডেটের নির্ভুলতা ও ভুল সংকেত নিয়ন্ত্রণ - দুটিকেই দেখায়।'
							: 'Your working-memory score reflects both update accuracy and false-alarm control.'}
					</p>
				</div>
			</div>

			{#if newBadges.length > 0}
				<div class="badge-wrap">
					<BadgeNotification badges={newBadges} />
				</div>
			{/if}

			<div class="results-grid">
				<div class="result-card primary">
					<span>{t('Overall score')}</span>
					<strong>{n(sessionResults.metrics.score)}</strong>
				</div>
				<div class="result-card">
					<span>{t('Accuracy')}</span>
					<strong>{wholePercent(sessionResults.metrics.accuracy, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}</strong>
				</div>
				<div class="result-card">
					<span>{t('Visual accuracy')}</span>
					<strong>{wholePercent(sessionResults.metrics.visual_accuracy, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}</strong>
				</div>
				<div class="result-card">
					<span>{t('Audio accuracy')}</span>
					<strong>{wholePercent(sessionResults.metrics.audio_accuracy, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}</strong>
				</div>
				<div class="result-card">
					<span>{t('Dual-match accuracy')}</span>
					<strong>{wholePercent(sessionResults.metrics.dual_accuracy, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}</strong>
				</div>
				<div class="result-card">
					<span>{t('Highest load')}</span>
					<strong>{nBackLabel(sessionResults.metrics.n_level)}</strong>
				</div>
			</div>

			<div class="difficulty-summary">
				<div class="difficulty-pill">{levelLabel(sessionResults.difficulty_before)}</div>
				<div class="difficulty-arrow">→</div>
				<div class="difficulty-pill accent">{levelLabel(sessionResults.difficulty_after)}</div>
			</div>
			<p class="difficulty-reason">{adaptationReasonLabel(sessionResults.adaptation_reason)}</p>

			<div class="action-row">
				<button class="primary-button" on:click={() => goto('/training')}>{t('Return to Training')}</button>
				<button class="secondary-button" on:click={() => goto('/dashboard')}>{t('Back to Dashboard')}</button>
			</div>
		</section>
	{/if}
</div>

<style>
	:global(body) {
		background:
			radial-gradient(circle at top, rgba(14, 116, 144, 0.16), transparent 35%),
			linear-gradient(180deg, #f5fbff 0%, #eef4f7 100%);
	}

	.dual-n-back-page {
		min-height: 100vh;
		padding: 2rem 1rem 3rem;
		color: #173042;
	}

	.hero-card,
	.play-card {
		max-width: 980px;
		margin: 0 auto;
		background: rgba(255, 255, 255, 0.86);
		backdrop-filter: blur(16px);
		border: 1px solid rgba(118, 145, 163, 0.22);
		border-radius: 28px;
		box-shadow: 0 24px 60px rgba(19, 52, 74, 0.12);
		padding: 2rem;
	}

	.hero-header,
	.play-header,
	.action-row,
	.intro-grid,
	.arena,
	.response-panel,
	.results-grid,
	.feedback-grid,
	.stats-row,
	.status-cluster,
	.control-pills {
		display: flex;
		gap: 1rem;
	}

	.hero-header,
	.play-header {
		justify-content: space-between;
		align-items: flex-start;
	}

	.eyebrow {
		margin: 0 0 0.5rem;
		font-size: 0.78rem;
		font-weight: 700;
		letter-spacing: 0.16em;
		text-transform: uppercase;
		color: #0f6e80;
	}

	h1,
	h2,
	p {
		margin-top: 0;
	}

	h1 {
		font-size: clamp(2rem, 4vw, 3.3rem);
		line-height: 1;
		margin-bottom: 0.7rem;
	}

	h2 {
		font-size: clamp(1.4rem, 2.6vw, 2rem);
		margin-bottom: 0.75rem;
	}

	.subtitle {
		max-width: 56rem;
		font-size: 1.02rem;
		line-height: 1.6;
		color: #486172;
	}

	.intro-grid,
	.results-grid,
	.feedback-grid {
		flex-wrap: wrap;
		margin-top: 1.5rem;
	}

	.info-card,
	.result-card,
	.feedback-metric,
	.grid-card,
	.cue-card,
	.tips-card {
		background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(239, 247, 250, 0.9));
		border: 1px solid rgba(118, 145, 163, 0.16);
		border-radius: 22px;
		padding: 1.25rem;
		box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
	}

	.info-card,
	.feedback-metric,
	.result-card {
		flex: 1 1 220px;
	}

	.info-card.emphasis {
		background: linear-gradient(135deg, #0f6e80, #0f3f63);
		color: #f4fbff;
	}

	.control-pills,
	.stats-row,
	.status-cluster {
		flex-wrap: wrap;
	}

	.control-pills span,
	.status-chip,
	.difficulty-pill {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 0.6rem 0.9rem;
		border-radius: 999px;
		font-size: 0.9rem;
		font-weight: 700;
	}

	.control-pills span,
	.status-chip {
		background: rgba(15, 110, 128, 0.1);
		color: #0f6e80;
	}

	.status-chip.muted {
		background: rgba(84, 103, 118, 0.12);
		color: #546776;
	}

	.stat-label,
	.result-card span,
	.feedback-metric span,
	.grid-label,
	.cue-label {
		display: block;
		font-size: 0.82rem;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: #6a7e8b;
		margin-bottom: 0.45rem;
	}

	.stats-row strong,
	.result-card strong,
	.feedback-metric strong {
		font-size: 1.4rem;
		color: #183347;
	}

	.tips-card {
		margin-top: 1.5rem;
	}

	.tips-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 1rem;
	}

	.tips-card ul {
		margin: 1rem 0 0;
		padding-left: 1.25rem;
		color: #4b6371;
		line-height: 1.7;
	}

	.help-panel {
		margin-top: 1rem;
		padding: 1rem 1.1rem;
		border-radius: 16px;
		background: rgba(15, 110, 128, 0.08);
		color: #365565;
	}

	.action-row {
		margin-top: 1.75rem;
		flex-wrap: wrap;
	}

	.primary-button,
	.secondary-button,
	.ghost-button,
	.response-button {
		border: none;
		border-radius: 18px;
		font-weight: 700;
		cursor: pointer;
		transition: transform 0.16s ease, box-shadow 0.16s ease, background 0.16s ease;
	}

	.primary-button,
	.secondary-button,
	.ghost-button {
		padding: 0.95rem 1.35rem;
		font-size: 0.98rem;
	}

	.primary-button {
		background: linear-gradient(135deg, #0f6e80, #104a72);
		color: white;
		box-shadow: 0 14px 28px rgba(16, 74, 114, 0.25);
	}

	.secondary-button,
	.ghost-button {
		background: rgba(84, 103, 118, 0.1);
		color: #294355;
	}

	.primary-button:hover,
	.secondary-button:hover,
	.ghost-button:hover,
	.response-button:hover:not(:disabled) {
		transform: translateY(-1px);
	}

	.progress-bar {
		margin: 1.25rem 0 1.75rem;
		height: 10px;
		border-radius: 999px;
		background: rgba(120, 144, 156, 0.2);
		overflow: hidden;
	}

	.progress-fill {
		height: 100%;
		background: linear-gradient(90deg, #0f6e80, #4fb4a9);
		border-radius: inherit;
		transition: width 0.2s ease;
	}

	.arena {
		align-items: stretch;
		flex-wrap: wrap;
	}

	.grid-card,
	.cue-card {
		flex: 1 1 320px;
	}

	.grid-board {
		display: grid;
		grid-template-columns: repeat(3, minmax(70px, 1fr));
		gap: 0.9rem;
	}

	.grid-cell {
		aspect-ratio: 1;
		border-radius: 18px;
		background: linear-gradient(180deg, #eef6f9, #dceaf0);
		border: 1px solid rgba(118, 145, 163, 0.2);
		box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
		transition: transform 0.12s ease, background 0.12s ease, box-shadow 0.12s ease;
	}

	.grid-cell.is-current {
		border-color: rgba(15, 110, 128, 0.25);
	}

	.grid-cell.is-highlighted {
		transform: scale(1.04);
		background: linear-gradient(135deg, #0f6e80, #37b1c4);
		box-shadow: 0 18px 36px rgba(15, 110, 128, 0.3);
	}

	.cue-card {
		display: flex;
		flex-direction: column;
		justify-content: center;
		min-height: 100%;
	}

	.cue-letter {
		font-size: clamp(1.2rem, 3vw, 2.2rem);
		font-weight: 800;
		color: #173042;
		margin-bottom: 0.85rem;
	}

	.cue-support {
		color: #55707f;
		line-height: 1.6;
		margin-bottom: 0;
	}

	.response-panel {
		margin-top: 1.5rem;
		flex-wrap: wrap;
	}

	.response-button {
		flex: 1 1 240px;
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 1.1rem 1.2rem;
		background: rgba(255, 255, 255, 0.88);
		border: 1px solid rgba(118, 145, 163, 0.22);
		color: #183347;
		box-shadow: 0 16px 32px rgba(19, 52, 74, 0.08);
	}

	.response-button.visual.active {
		background: linear-gradient(135deg, rgba(15, 110, 128, 0.16), rgba(55, 177, 196, 0.2));
		border-color: rgba(15, 110, 128, 0.35);
	}

	.response-button.audio.active {
		background: linear-gradient(135deg, rgba(16, 74, 114, 0.18), rgba(103, 145, 197, 0.18));
		border-color: rgba(16, 74, 114, 0.35);
	}

	.response-button:disabled {
		opacity: 0.55;
		cursor: not-allowed;
		transform: none;
	}

	.keycap {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 2.3rem;
		height: 2.3rem;
		border-radius: 14px;
		background: #183347;
		color: white;
		font-weight: 800;
	}

	.feedback-state,
	.intro-state,
	.complete-state {
		text-align: center;
	}

	.feedback-note,
	.difficulty-reason {
		margin: 1rem auto 0;
		max-width: 44rem;
		color: #4d6575;
		line-height: 1.6;
	}

	.result-card.primary {
		background: linear-gradient(135deg, #0f6e80, #104a72);
		color: white;
	}

	.result-card.primary span,
	.result-card.primary strong {
		color: white;
	}

	.difficulty-summary {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		margin-top: 1.75rem;
		flex-wrap: wrap;
	}

	.difficulty-pill {
		background: rgba(84, 103, 118, 0.1);
		color: #294355;
	}

	.difficulty-pill.accent {
		background: linear-gradient(135deg, #0f6e80, #104a72);
		color: white;
	}

	.difficulty-arrow {
		font-size: 1.6rem;
		font-weight: 700;
		color: #56707f;
	}

	.badge-wrap {
		margin-top: 1.25rem;
	}

	@media (max-width: 720px) {
		.dual-n-back-page {
			padding-inline: 0.75rem;
		}

		.hero-card,
		.play-card {
			padding: 1.25rem;
			border-radius: 22px;
		}

		.hero-header,
		.play-header,
		.tips-header {
			flex-direction: column;
			align-items: flex-start;
		}

		.grid-board {
			grid-template-columns: repeat(3, minmax(56px, 1fr));
			gap: 0.7rem;
		}
	}
</style>

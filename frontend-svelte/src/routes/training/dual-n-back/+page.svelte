<script>
    import { goto } from '$app/navigation';
    import { page } from '$app/stores';
    import { API_BASE_URL } from '$lib/api';
    import BadgeNotification from '$lib/components/BadgeNotification.svelte';
    import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
    import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
    import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
    import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
    import { formatNumber, formatPercent, locale, localizeStimulusSymbol, translateText } from '$lib/i18n';
    import { buildPracticePayload, getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
    import { onMount } from 'svelte';

    const STATE = {
        LOADING:        'loading',
        INSTRUCTIONS:   'instructions',
        ROUND_INTRO:    'round_intro',
        PLAYING:        'playing',
        TRIAL_FEEDBACK: 'trial_feedback',
        COMPLETE:       'complete'
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
    /** @type {"practice" | "recorded"} */
    let playMode = TASK_PLAY_MODE.RECORDED;
    let practiceStatusMessage = '';
    let recordedTrials = [];
    let recordedSessionData = null;
    let loadError = false;
    let saveError = false;

    function t(text) { return translateText(text, $locale); }
    function n(value, options = {}) { return formatNumber(value, $locale, options); }
    function pct(value, options = {}) { return formatPercent(value, $locale, options); }
    function stimulus(value) { return localizeStimulusSymbol(value, $locale); }
    function wholePercent(value, options = {}) { return pct((Number(value) || 0) / 100, options); }

    function roundLabel(current, total) {
        return $locale === 'bn' ? `রাউন্ড ${n(current)} / ${n(total)}` : `Round ${current} of ${total}`;
    }
    function nBackLabel(value) { return $locale === 'bn' ? `${n(value)}-ব্যাক` : `${value}-Back`; }
    function levelLabel(value) { return $locale === 'bn' ? `লেভেল ${n(value)}` : `Level ${value}`; }

    function introSubtitle(level) {
        if ($locale === 'bn') return `একই সঙ্গে চলমান ভিজ্যুয়াল অবস্থান এবং শোনা অক্ষর লক্ষ্য করুন। ${n(level)} ধাপ আগেরটির সঙ্গে মিললে উত্তর দিন।`;
        return `Track a moving visual location and a spoken letter simultaneously. Respond when either matches what appeared ${level} steps back.`;
    }
    function observeInstruction(level) {
        if ($locale === 'bn') return `${n(level)}টি আইটেম দেখা না হওয়া পর্যন্ত শুধু দেখুন এবং ক্রমটি মনে রাখুন।`;
        return `Matches can happen separately or together. During the first ${level} items, just observe and build the sequence in memory — no responses needed yet.`;
    }
    function roundIntroTitle(level) {
        return $locale === 'bn' ? `${nBackLabel(level)} সিকোয়েন্স শুরু হচ্ছে` : `${level}-Back Sequence Incoming`;
    }
    function roundIntroSupport() {
        return $locale === 'bn'
            ? 'মাঝখানে মনোযোগ রাখুন। গ্রিডের আলো আর শোনা সংকেত কয়েক মুহূর্তের মধ্যেই শুরু হবে।'
            : 'Stay centered. The grid flash and spoken cue will start in a moment.';
    }
    function focusRoundTitle(level) {
        return $locale === 'bn' ? `${nBackLabel(level)} মনোযোগ রাউন্ড` : `${level}-Back Focus Round`;
    }
    function responseSupportLabel() {
        if (responseEnabled) return t('Mark visual and audio matches before the next cue arrives.');
        return $locale === 'bn'
            ? `${n(currentNLevel)}টি আইটেম না আসা পর্যন্ত শুধু লক্ষ্য করুন।`
            : `Observe only — responses activate after ${currentNLevel} items have appeared.`;
    }
    function adaptationReasonLabel(reason) { return translateText(reason || '', $locale); }

    onMount(() => {
        taskId = $page.url.searchParams.get('taskId');
        speechEnabled = typeof window !== 'undefined' && 'speechSynthesis' in window;

        const handleKeyDown = (event) => {
            if (state !== STATE.PLAYING || !responseEnabled || responseLocked) return;
            const key = event.key.toLowerCase();
            if (key === 'v') { event.preventDefault(); toggleVisualResponse(); }
            if (key === 'a') { event.preventDefault(); toggleAudioResponse(); }
        };

        window.addEventListener('keydown', handleKeyDown);
        loadSession();

        return () => {
            isDisposed = true;
            window.removeEventListener('keydown', handleKeyDown);
            if (speechEnabled) window.speechSynthesis.cancel();
        };
    });

    function delay(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

    async function loadSession() {
        loadError = false;
        try {
            const userData = JSON.parse(localStorage.getItem('user') || '{}');
            const userId = userData.id;
            if (!userId) { goto('/login'); return; }

            const queryDifficulty = Number.parseInt($page.url.searchParams.get('difficulty') || '', 10);
            const planResponse = await fetch(`${API_BASE_URL}/api/training/training-plan/${userId}`);
            const plan = await planResponse.json();

            let userDifficulty = 5;
            if (Number.isInteger(queryDifficulty) && queryDifficulty >= 1 && queryDifficulty <= 10) {
                userDifficulty = queryDifficulty;
            } else if (plan && plan.current_difficulty) {
                const currentDifficulty = typeof plan.current_difficulty === 'string'
                    ? JSON.parse(plan.current_difficulty)
                    : plan.current_difficulty;
                userDifficulty = currentDifficulty.working_memory || 5;
            }
            difficulty = userDifficulty;

            const response = await fetch(
                `${API_BASE_URL}/api/training/tasks/dual-n-back/generate/${userId}?difficulty=${difficulty}&num_trials=4`,
                { method: 'POST', headers: { 'Content-Type': 'application/json' } }
            );
            if (!response.ok) throw new Error('Failed to load');

            sessionData = await response.json();
            recordedSessionData = structuredClone(sessionData);
            recordedTrials = structuredClone(sessionData.trials);
            trials = structuredClone(recordedTrials);
            state = STATE.INSTRUCTIONS;
        } catch (err) {
            loadError = true;
            state = STATE.INSTRUCTIONS;
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
            const spoken = stimulus(letter);
            const utterance = new SpeechSynthesisUtterance(spoken);
            utterance.lang = $locale === 'bn' ? 'bn-BD' : 'en-US';
            utterance.rate = 0.85;
            utterance.pitch = 1;
            utterance.volume = 1;
            window.speechSynthesis.speak(utterance);
        } catch (err) {
            // speech unavailable — visual fallback active
        }
    }

    /** @param {"practice" | "recorded"} nextMode */
    async function startSession(nextMode = TASK_PLAY_MODE.RECORDED) {
        playMode = nextMode;
        practiceStatusMessage = '';
        sessionData = nextMode === TASK_PLAY_MODE.PRACTICE
            ? buildPracticePayload('dual-n-back', recordedSessionData)
            : structuredClone(recordedSessionData);
        trials = structuredClone(sessionData.trials);
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
            const stim = trial.stimuli[index];
            currentStimulusIndex = index;
            currentLetter = stim.letter;
            highlightedPosition = stim.position;
            visualResponseSelected = false;
            audioResponseSelected = false;
            responseLocked = false;
            responseEnabled = index >= trial.n_level;
            stepStartTime = Date.now();
            lastActionTime = 0;

            speakLetter(stim.letter);
            await delay(trial.stimulus_ms);
            if (isDisposed) return;
            highlightedPosition = null;
            await delay(trial.response_window_ms);
            if (isDisposed) return;

            responseLocked = true;
            stim.user_visual_match = responseEnabled ? visualResponseSelected : false;
            stim.user_audio_match  = responseEnabled ? audioResponseSelected  : false;
            stim.response_time_ms  = responseEnabled && lastActionTime > 0 ? lastActionTime - stepStartTime : 0;
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
        const eligible = trial.stimuli.filter((s) => s.index >= trial.n_level);
        return {
            eligibleStimuli: eligible.length,
            correctVisual:   eligible.filter((s) => !!s.user_visual_match === !!s.visual_target).length,
            correctAudio:    eligible.filter((s) => !!s.user_audio_match  === !!s.audio_target).length
        };
    }

    async function submitSession() {
        if (playMode === TASK_PLAY_MODE.PRACTICE) {
            playMode = TASK_PLAY_MODE.RECORDED;
            sessionData = structuredClone(recordedSessionData);
            trials = structuredClone(recordedTrials);
            practiceStatusMessage = getPracticeCopy($locale).complete;
            state = STATE.INSTRUCTIONS;
            return;
        }

        saveError = false;
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
                    body: JSON.stringify({ difficulty, trials, task_id: taskId, duration_seconds: durationSeconds })
                }
            );
            if (!response.ok) throw new Error('Failed to submit');

            sessionResults = await response.json();
            newBadges = sessionResults.new_badges || [];
            state = STATE.COMPLETE;
        } catch (err) {
            saveError = true;
            state = STATE.COMPLETE;
        }
    }

    function gridCellClasses(position) {
        return ['grid-cell',
            highlightedPosition === position ? 'is-highlighted' : '',
            currentTrial?.stimuli?.[currentStimulusIndex]?.position === position && state === STATE.PLAYING ? 'is-current' : ''
        ].filter(Boolean).join(' ');
    }

    $: currentNLevel = currentTrial?.n_level ?? sessionData?.instructions?.n_level ?? 2;
    $: progressPercent = currentTrial && currentStimulusIndex >= 0
        ? ((currentStimulusIndex + 1) / currentTrial.stimuli.length) * 100
        : 0;
</script>

<div class="nback-container" data-localize-skip>

    <!-- Loading -->
    {#if state === STATE.LOADING}
        <div class="page-content">
            <LoadingSkeleton />
        </div>

    <!-- Instructions -->
    {:else if state === STATE.INSTRUCTIONS}
        <div class="page-content">

            <!-- Header -->
            <div class="task-header">
                <button class="back-btn" on:click={() => goto('/training')}>Back to Training</button>
                <div class="header-center">
                    <h1 class="task-title">Dual N-Back</h1>
                    <DifficultyBadge {difficulty} domain="Working Memory" />
                </div>
            </div>

            {#if loadError}
                <div class="error-banner">
                    <p>Failed to load session. Please try again.</p>
                    <button on:click={() => { loadError = false; loadSession(); }}>Retry</button>
                </div>
            {:else}
                <div class="concept-card">
                    <div class="concept-badge">Working Memory · Dual-Task Training</div>
                    <h2>What Is Dual N-Back?</h2>
                    <p>{introSubtitle(sessionData.instructions.n_level)}</p>
                </div>

                <div class="rules-card">
                    <h3>How to Respond</h3>
                    <ol class="rules-list">
                        <li>Watch the <strong>3×3 grid</strong> — one cell flashes each step.</li>
                        <li>Listen for a <strong>spoken letter</strong> (or read the on-screen fallback).</li>
                        <li>If the <strong>position</strong> matches what appeared {nBackLabel(sessionData.instructions.n_level)} ago, press <kbd>V</kbd> (Visual Match).</li>
                        <li>If the <strong>letter</strong> matches what appeared {nBackLabel(sessionData.instructions.n_level)} ago, press <kbd>A</kbd> (Audio Match).</li>
                        <li>Both can match simultaneously — press both buttons.</li>
                    </ol>
                    <p class="rules-note">{observeInstruction(sessionData.instructions.n_level)}</p>
                </div>

                <div class="info-grid">
                    <div class="info-card">
                        <div class="info-label">Rounds</div>
                        <div class="info-val">{n(sessionData.num_trials)}</div>
                        <p>Each round is a full stimulus sequence. Round results shown between rounds.</p>
                    </div>
                    <div class="info-card">
                        <div class="info-label">N-Level</div>
                        <div class="info-val">{nBackLabel(sessionData.instructions.n_level)}</div>
                        <p>Match stimuli that appeared this many steps back in the sequence.</p>
                    </div>
                    <div class="info-card">
                        <div class="info-label">Audio</div>
                        <div class="info-val">{speechEnabled ? 'Enabled' : 'Visual fallback'}</div>
                        <p>{speechEnabled ? 'Letters are spoken aloud via speech synthesis.' : 'Speech unavailable — letters shown on screen instead.'}</p>
                    </div>
                </div>

                {#if showHelp}
                    <div class="tip-card">
                        <div class="tip-title">Advanced Tips</div>
                        <ul>
                            <li><strong>Warm-up phase:</strong> no responses needed until enough items have appeared — buttons become active automatically.</li>
                            <li><strong>Dual matches:</strong> press both V and A if both position and letter repeat.</li>
                            <li><strong>Accuracy vs. false alarms:</strong> incorrect presses lower your score just as missed targets do. Only respond when confident.</li>
                            <li><strong>Rhythm:</strong> use a steady internal rhythm rather than rushing each cue.</li>
                        </ul>
                    </div>
                {:else}
                    <div class="tip-card minimal">
                        <div class="tip-row">
                            <div>
                                <div class="tip-title">Strategy</div>
                                <p>Keep your eyes centered on the grid and let peripheral motion guide you. Only press when confident — false alarms count against your score.</p>
                            </div>
                            <button class="show-more-btn" on:click={() => (showHelp = true)}>More tips</button>
                        </div>
                    </div>
                {/if}

                <div class="clinical-card">
                    <h3>Clinical Basis</h3>
                    <p>Dual N-Back is one of the few cognitive training tasks with strong evidence for transfer to real-world working memory capacity. In multiple sclerosis, working memory deficits affect approximately 40–65% of patients and correlate with lesion burden in frontal and parietal white matter. Regular N-Back training has been shown to increase prefrontal cortex activation and improve performance on untrained working memory measures. The dual-task format (simultaneous visual and auditory streams) places maximal load on the central executive component of working memory, targeting the very system most vulnerable to MS-related neurodegeneration.</p>
                </div>

                <TaskPracticeActions
                    locale={$locale}
                    startLabel={t('Start Actual Task')}
                    statusMessage={practiceStatusMessage}
                    on:start={() => startSession(TASK_PLAY_MODE.RECORDED)}
                    on:practice={() => startSession(TASK_PLAY_MODE.PRACTICE)}
                />
            {/if}
        </div>

    <!-- Round intro -->
    {:else if state === STATE.ROUND_INTRO}
        <div class="play-wrap">
            {#if playMode === TASK_PLAY_MODE.PRACTICE}
                <PracticeModeBanner locale={$locale} />
            {/if}
            <div class="play-card centred">
                <div class="round-badge">{roundLabel(currentTrialIndex + 1, trials.length)}</div>
                <h2>{roundIntroTitle(currentNLevel)}</h2>
                <p class="round-support">{roundIntroSupport()}</p>
            </div>
        </div>

    <!-- Playing -->
    {:else if state === STATE.PLAYING}
        <div class="play-wrap">
            {#if playMode === TASK_PLAY_MODE.PRACTICE}
                <PracticeModeBanner locale={$locale} />
            {/if}
            <div class="play-card">

                <div class="play-top">
                    <div>
                        <div class="round-badge">{roundLabel(currentTrialIndex + 1, trials.length)}</div>
                        <h2>{focusRoundTitle(currentNLevel)}</h2>
                    </div>
                    <div class="status-chips">
                        <span class="schip">{n(currentStimulusIndex + 1)} / {n(currentTrial.stimuli.length)}</span>
                        <span class="schip {responseEnabled ? 'chip-live' : 'chip-warm'}">{responseEnabled ? t('Response live') : t('Warm-up')}</span>
                    </div>
                </div>

                <div class="prog-bar">
                    <div class="prog-fill" style="width: {progressPercent}%"></div>
                </div>

                <div class="arena">
                    <div class="stream-card">
                        <div class="stream-label">Visual Stream</div>
                        <div class="grid-board">
                            {#each Array(9) as _, idx}
                                <div class={gridCellClasses(idx)}></div>
                            {/each}
                        </div>
                    </div>

                    <div class="stream-card cue-stream">
                        <div class="stream-label">Audio Stream</div>
                        <div class="cue-letter">{speechEnabled ? t('Speaker cue active') : stimulus(currentLetter)}</div>
                        <p class="cue-support">{responseSupportLabel()}</p>
                    </div>
                </div>

                <div class="response-row">
                    <button
                        class="resp-btn visual-btn {visualResponseSelected ? 'resp-active' : ''}"
                        on:click={toggleVisualResponse}
                        disabled={!responseEnabled || responseLocked}
                    >
                        <kbd class="keycap">V</kbd>
                        <span>{t('Visual Match')}</span>
                    </button>
                    <button
                        class="resp-btn audio-btn {audioResponseSelected ? 'resp-active' : ''}"
                        on:click={toggleAudioResponse}
                        disabled={!responseEnabled || responseLocked}
                    >
                        <kbd class="keycap">A</kbd>
                        <span>{t('Audio Match')}</span>
                    </button>
                </div>

            </div>
        </div>

    <!-- Trial feedback -->
    {:else if state === STATE.TRIAL_FEEDBACK}
        <div class="play-wrap">
            <div class="play-card centred">
                <div class="round-badge">
                    {$locale === 'bn' ? `রাউন্ড ${n(currentTrialIndex + 1)} সম্পন্ন` : `Round ${currentTrialIndex + 1} complete`}
                </div>
                <h2>{t('Round Review')}</h2>
                <div class="fb-grid">
                    <div class="fb-cell">
                        <span class="fb-label">{t('Eligible cues')}</span>
                        <strong>{n(feedbackSummary.eligibleStimuli)}</strong>
                    </div>
                    <div class="fb-cell">
                        <span class="fb-label">{t('Visual correct')}</span>
                        <strong>{n(feedbackSummary.correctVisual)}</strong>
                    </div>
                    <div class="fb-cell">
                        <span class="fb-label">{t('Audio correct')}</span>
                        <strong>{n(feedbackSummary.correctAudio)}</strong>
                    </div>
                </div>
                <p class="fb-note">
                    {$locale === 'bn'
                        ? 'পরের রাউন্ডেও নির্ভুলতা এবং বেছে সাড়া দেওয়ার নিয়ন্ত্রণ সমান গুরুত্বপূর্ণ থাকবে।'
                        : 'The next round keeps pressure on both accuracy and selective response control.'}
                </p>
            </div>
        </div>

    <!-- Complete -->
    {:else if state === STATE.COMPLETE}
        <div class="page-content">

            <div class="task-header">
                <button class="back-btn" on:click={() => goto('/training')}>Back to Training</button>
                <div class="header-center">
                    <h1 class="task-title">Session Complete</h1>
                </div>
            </div>

            {#if saveError}
                <div class="error-banner">
                    <p>Results could not be saved. Your progress may not have been recorded.</p>
                    <button on:click={() => (saveError = false)}>Dismiss</button>
                </div>
            {/if}

            {#if sessionResults}
                <div class="results-card">
                    <div class="results-header">
                        <h2>Dual N-Back Results</h2>
                        <p class="results-sub">
                            {$locale === 'bn'
                                ? 'আপনার ওয়ার্কিং মেমরি স্কোর আপডেটের নির্ভুলতা ও ভুল সংকেত নিয়ন্ত্রণ — দুটিকেই দেখায়।'
                                : 'Your score reflects both update accuracy and false-alarm control across both channels.'}
                        </p>
                    </div>

                    <div class="results-body">
                        <div class="metrics-grid">
                            <div class="mc primary-mc">
                                <div class="mc-val">{n(sessionResults.metrics.score)}</div>
                                <div class="mc-lbl">{t('Overall Score')}</div>
                            </div>
                            <div class="mc">
                                <div class="mc-val">{wholePercent(sessionResults.metrics.accuracy, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}</div>
                                <div class="mc-lbl">{t('Accuracy')}</div>
                            </div>
                            <div class="mc">
                                <div class="mc-val">{wholePercent(sessionResults.metrics.visual_accuracy, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}</div>
                                <div class="mc-lbl">{t('Visual Accuracy')}</div>
                            </div>
                            <div class="mc">
                                <div class="mc-val">{wholePercent(sessionResults.metrics.audio_accuracy, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}</div>
                                <div class="mc-lbl">{t('Audio Accuracy')}</div>
                            </div>
                            <div class="mc">
                                <div class="mc-val">{wholePercent(sessionResults.metrics.dual_accuracy, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}</div>
                                <div class="mc-lbl">{t('Dual-Match Accuracy')}</div>
                            </div>
                            <div class="mc">
                                <div class="mc-val">{nBackLabel(sessionResults.metrics.n_level)}</div>
                                <div class="mc-lbl">{t('Highest Load')}</div>
                            </div>
                        </div>

                        <div class="adapt-card">
                            <div class="adapt-levels">
                                <div class="adapt-pill">{levelLabel(sessionResults.difficulty_before)}</div>
                                <div class="adapt-arrow">&#8594;</div>
                                <div class="adapt-pill accent-pill">{levelLabel(sessionResults.difficulty_after)}</div>
                            </div>
                            <p class="adapt-reason">{adaptationReasonLabel(sessionResults.adaptation_reason)}</p>
                        </div>

                        <div class="action-row">
                            <button class="start-button" on:click={() => goto('/training')}>{t('Return to Training')}</button>
                            <button class="btn-secondary" on:click={() => goto('/dashboard')}>{t('Back to Dashboard')}</button>
                        </div>
                    </div>
                </div>
            {/if}
        </div>
    {/if}

    <!-- BadgeNotification outside all phases -->
    {#if newBadges.length > 0}
        <BadgeNotification badges={newBadges} />
    {/if}

</div>

<style>
    /* Container */
    .nback-container {
        min-height: 100vh;
        background: #C8DEFA;
        padding: 2rem;
        font-family: inherit;
    }

    /* Page content wrapper */
    .page-content {
        max-width: 1100px;
        margin: 0 auto;
        display: flex;
        flex-direction: column;
        gap: 1.25rem;
    }

    /* Task header */
    .task-header {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .back-btn {
        background: white;
        color: #4338ca;
        border: 2px solid #4338ca;
        padding: 0.6rem 1.25rem;
        border-radius: 8px;
        cursor: pointer;
        font-size: 0.9rem;
        font-weight: 600;
        white-space: nowrap;
        transition: background 0.2s, color 0.2s;
    }
    .back-btn:hover { background: #4338ca; color: white; }

    .header-center {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        flex-wrap: wrap;
    }

    .task-title {
        font-size: 1.75rem;
        font-weight: 700;
        color: #1e1b4b;
        margin: 0;
    }

    /* Error banner */
    .error-banner {
        background: #fee2e2;
        border: 1px solid #fca5a5;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
    }
    .error-banner p { margin: 0; color: #991b1b; font-weight: 500; }
    .error-banner button {
        background: #ef4444;
        color: white;
        border: none;
        padding: 0.4rem 1rem;
        border-radius: 6px;
        cursor: pointer;
        font-size: 0.875rem;
        flex-shrink: 0;
    }

    /* Concept card */
    .concept-card {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
    }
    .concept-badge {
        display: inline-block;
        background: #ede9fe;
        color: #4338ca;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        padding: 0.3rem 0.9rem;
        border-radius: 20px;
        margin-bottom: 0.75rem;
    }
    .concept-card h2 {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1e1b4b;
        margin: 0 0 0.75rem;
    }
    .concept-card p {
        color: #374151;
        line-height: 1.65;
        margin: 0;
    }

    /* Rules card */
    .rules-card {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
    }
    .rules-card h3 {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1e1b4b;
        margin: 0 0 1rem;
    }
    .rules-list {
        margin: 0 0 1rem;
        padding-left: 1.5rem;
        display: flex;
        flex-direction: column;
        gap: 0.6rem;
    }
    .rules-list li { color: #374151; line-height: 1.55; }
    .rules-list li strong { color: #4338ca; }
    kbd {
        display: inline-block;
        background: #1e1b4b;
        color: white;
        padding: 0.1rem 0.5rem;
        border-radius: 4px;
        font-size: 0.85rem;
        font-family: monospace;
        font-weight: 700;
    }
    .rules-note {
        margin: 0;
        background: #ede9fe;
        color: #4338ca;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        font-size: 0.9rem;
        line-height: 1.5;
    }

    /* Info grid */
    .info-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 1rem;
    }
    .info-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
    }
    .info-label {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #4338ca;
        margin-bottom: 0.25rem;
    }
    .info-val {
        font-size: 1.5rem;
        font-weight: 800;
        color: #1e1b4b;
        margin-bottom: 0.5rem;
    }
    .info-card p { font-size: 0.875rem; color: #6b7280; line-height: 1.5; margin: 0; }

    /* Tip card */
    .tip-card {
        background: #f5f3ff;
        border: 1px solid #ddd6fe;
        border-radius: 16px;
        padding: 1.5rem 2rem;
    }
    .tip-card ul {
        margin: 0.75rem 0 0;
        padding-left: 1.5rem;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
    .tip-card li { color: #374151; font-size: 0.9rem; line-height: 1.55; }
    .tip-card li strong { color: #4338ca; }
    .tip-card.minimal p { color: #374151; line-height: 1.6; margin: 0; }
    .tip-title {
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #4338ca;
        margin-bottom: 0.5rem;
    }
    .tip-row { display: flex; align-items: center; justify-content: space-between; gap: 1.5rem; }
    .show-more-btn {
        background: white;
        border: 1.5px solid #4338ca;
        color: #4338ca;
        padding: 0.5rem 1.1rem;
        border-radius: 8px;
        cursor: pointer;
        font-size: 0.875rem;
        font-weight: 600;
        white-space: nowrap;
        flex-shrink: 0;
        transition: all 0.2s;
    }
    .show-more-btn:hover { background: #4338ca; color: white; }

    /* Clinical card */
    .clinical-card {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border: 1px solid #bbf7d0;
        border-radius: 16px;
        padding: 1.5rem 2rem;
    }
    .clinical-card h3 { font-size: 1rem; font-weight: 700; color: #14532d; margin: 0 0 0.75rem; }
    .clinical-card p { color: #166534; font-size: 0.95rem; line-height: 1.65; margin: 0; }

    /* Play wrap — game phases use full-screen centred layout */
    .play-wrap {
        max-width: 980px;
        margin: 0 auto;
        padding: 0 1rem;
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .play-card {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
    }
    .play-card.centred { text-align: center; }

    .round-badge {
        display: inline-block;
        background: #ede9fe;
        color: #4338ca;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        padding: 0.3rem 0.9rem;
        border-radius: 20px;
        margin-bottom: 0.75rem;
    }

    .play-card h2 {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1e1b4b;
        margin: 0 0 0.5rem;
    }
    .round-support { color: #6b7280; font-size: 0.95rem; margin: 0; }

    /* Play top row */
    .play-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        flex-wrap: wrap;
        gap: 1rem;
        margin-bottom: 1rem;
    }
    .status-chips { display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center; }
    .schip {
        display: inline-flex;
        align-items: center;
        padding: 0.35rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        background: #ede9fe;
        color: #4338ca;
    }
    .chip-live { background: #d1fae5; color: #065f46; }
    .chip-warm { background: #fef3c7; color: #92400e; }

    /* Progress bar */
    .prog-bar {
        height: 8px;
        background: #e5e7eb;
        border-radius: 4px;
        overflow: hidden;
        margin-bottom: 1.5rem;
    }
    .prog-fill {
        height: 100%;
        background: linear-gradient(90deg, #a5b4fc 0%, #4338ca 100%);
        border-radius: 4px;
        transition: width 0.2s ease;
    }

    /* Arena */
    .arena {
        display: flex;
        gap: 1.25rem;
        flex-wrap: wrap;
        margin-bottom: 1.5rem;
    }
    .stream-card {
        flex: 1 1 280px;
        background: #fafafa;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.25rem;
    }
    .stream-label {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #4338ca;
        margin-bottom: 1rem;
    }

    /* 3x3 grid */
    .grid-board {
        display: grid;
        grid-template-columns: repeat(3, minmax(64px, 1fr));
        gap: 0.75rem;
    }
    .grid-cell {
        aspect-ratio: 1;
        border-radius: 12px;
        background: #ede9fe;
        border: 2px solid #c4b5fd;
        transition: transform 0.12s ease, background 0.12s ease, box-shadow 0.12s ease;
    }
    .grid-cell.is-current { border-color: #7c3aed; }
    .grid-cell.is-highlighted {
        transform: scale(1.06);
        background: linear-gradient(135deg, #4338ca, #7c3aed);
        border-color: #4338ca;
        box-shadow: 0 8px 24px rgba(67,56,202,0.35);
    }

    /* Cue stream card */
    .cue-stream { display: flex; flex-direction: column; justify-content: center; }
    .cue-letter {
        font-size: 1.5rem;
        font-weight: 800;
        color: #1e1b4b;
        margin-bottom: 0.75rem;
    }
    .cue-support { color: #6b7280; line-height: 1.6; font-size: 0.9rem; margin: 0; }

    /* Response buttons */
    .response-row { display: flex; gap: 1rem; flex-wrap: wrap; }
    .resp-btn {
        flex: 1 1 220px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 1.25rem;
        background: white;
        border: 2px solid #c4b5fd;
        border-radius: 12px;
        color: #1e1b4b;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.15s ease;
    }
    .resp-btn:hover:not(:disabled) {
        border-color: #4338ca;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(67,56,202,0.15);
    }
    .resp-btn.resp-active {
        background: linear-gradient(135deg, #ede9fe, #ddd6fe);
        border-color: #4338ca;
        box-shadow: 0 4px 12px rgba(67,56,202,0.2);
    }
    .resp-btn:disabled { opacity: 0.45; cursor: not-allowed; transform: none; }
    .keycap {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 2.2rem;
        height: 2.2rem;
        border-radius: 10px;
        background: #1e1b4b;
        color: white;
        font-weight: 800;
        font-size: 1rem;
        font-family: monospace;
    }

    /* Trial feedback */
    .fb-grid {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
        justify-content: center;
        margin: 1.25rem 0;
    }
    .fb-cell {
        background: #f5f3ff;
        border: 1px solid #ddd6fe;
        border-radius: 12px;
        padding: 1.25rem 1.75rem;
        text-align: center;
        flex: 1 1 140px;
    }
    .fb-label { display: block; font-size: 0.8rem; color: #6b7280; margin-bottom: 0.35rem; text-transform: uppercase; letter-spacing: 0.5px; }
    .fb-cell strong { font-size: 1.75rem; font-weight: 800; color: #4338ca; }
    .fb-note { color: #6b7280; font-size: 0.9rem; line-height: 1.55; margin: 0 auto; max-width: 44rem; }

    /* Results */
    .results-card {
        background: white;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
    }
    .results-header {
        background: linear-gradient(135deg, #4338ca 0%, #312e81 100%);
        padding: 2rem;
        color: white;
        text-align: center;
    }
    .results-header h2 { font-size: 1.75rem; font-weight: 800; margin: 0 0 0.25rem; color: white; }
    .results-sub { margin: 0; font-size: 0.9rem; opacity: 0.85; }
    .results-body { padding: 2rem; display: flex; flex-direction: column; gap: 1.25rem; }

    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 1rem;
    }
    .mc {
        background: #f5f3ff;
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
    }
    .primary-mc {
        background: linear-gradient(135deg, #4338ca 0%, #312e81 100%);
    }
    .mc-val { font-size: 1.6rem; font-weight: 800; color: #4338ca; margin-bottom: 0.25rem; }
    .primary-mc .mc-val { color: white; }
    .mc-lbl { font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }
    .primary-mc .mc-lbl { color: rgba(255,255,255,0.75); }

    /* Adaptation */
    .adapt-card {
        background: #f5f3ff;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        text-align: center;
    }
    .adapt-levels { display: flex; align-items: center; justify-content: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 0.5rem; }
    .adapt-pill {
        background: #e5e7eb;
        color: #374151;
        font-size: 0.9rem;
        font-weight: 700;
        padding: 0.4rem 1rem;
        border-radius: 20px;
    }
    .accent-pill { background: linear-gradient(135deg, #4338ca, #312e81); color: white; }
    .adapt-arrow { font-size: 1.4rem; color: #4338ca; font-weight: 700; }
    .adapt-reason { color: #6b7280; font-size: 0.875rem; font-style: italic; margin: 0; }

    /* Action row */
    .action-row {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
    }
    .start-button {
        flex: 1;
        background: #4338ca;
        color: white;
        border: none;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        font-size: 1rem;
        font-weight: 700;
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .start-button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(67,56,202,0.4); }
    .btn-secondary {
        flex: 1;
        background: white;
        color: #4338ca;
        border: 2px solid #4338ca;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        font-size: 1rem;
        font-weight: 700;
        cursor: pointer;
        transition: all 0.2s;
    }
    .btn-secondary:hover { background: #4338ca; color: white; }

    /* Responsive */
    @media (max-width: 768px) {
        .nback-container { padding: 1rem; }
        .task-title { font-size: 1.35rem; }
        .back-btn { padding: 0.5rem 0.9rem; font-size: 0.8rem; }
        .play-top { flex-direction: column; }
        .grid-board { grid-template-columns: repeat(3, minmax(52px, 1fr)); gap: 0.6rem; }
        .response-row { flex-direction: column; }
        .action-row { flex-direction: column; }
        .metrics-grid { grid-template-columns: repeat(2, 1fr); }
        .results-body { padding: 1.25rem; }
    }
</style>

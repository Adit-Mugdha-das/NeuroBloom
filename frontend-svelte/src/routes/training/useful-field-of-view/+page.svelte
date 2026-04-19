<script>
    import { goto } from '$app/navigation';
    import { page } from '$app/stores';
    import BadgeNotification from '$lib/components/BadgeNotification.svelte';
    import DifficultyBadge from '$lib/components/DifficultyBadge.svelte';
    import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
    import { generateUFOVTrial, submitUFOVResponse } from '$lib/api.js';
    import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
    import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
import TaskReturnButton from '$lib/components/TaskReturnButton.svelte';
    import { locale, localeText } from '$lib/i18n';
    import { getPracticeCopy, TASK_PLAY_MODE } from '$lib/task-practice';
import { TASK_RETURN_CONTEXT } from '$lib/task-navigation';
    import { onDestroy, onMount } from 'svelte';

    let userId = null;
    let taskId = null;

    let gamePhase = 'intro';
    let currentTrial = null;
    let trialData = null;
    let difficulty = 1;

    let centralResponse = null;
    let peripheralResponse = null;
    let responseStartTime = null;
    let responseTime = 0;

    let results = null;
    let earnedBadges = [];
    let loading = false;
    let error = null;
    let playMode = TASK_PLAY_MODE.RECORDED;
    let practiceStatusMessage = '';

    let stimulusTimer = null;
    let showStimulus = false;
    let fixationTimer = null;

    let trialsCompleted = 0;
    const TRIALS_PER_SESSION = 10;

    onMount(() => {
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        userId = user.id;
        if (!userId) {
            goto('/login');
            return;
        }
    });

    onDestroy(() => {
        if (stimulusTimer) clearTimeout(stimulusTimer);
        if (fixationTimer) clearTimeout(fixationTimer);
    });

    async function startTask(nextMode = TASK_PLAY_MODE.RECORDED) {
        if (stimulusTimer) {
            clearTimeout(stimulusTimer);
            stimulusTimer = null;
        }
        if (fixationTimer) {
            clearTimeout(fixationTimer);
            fixationTimer = null;
        }
        playMode = nextMode;
        practiceStatusMessage = '';
        trialsCompleted = 0;
        await loadTrial();
    }

    async function loadTrial() {
        loading = true;
        error = null;
        earnedBadges = [];
        results = null;
        centralResponse = null;
        peripheralResponse = null;
        responseStartTime = null;
        responseTime = 0;
        showStimulus = false;

        try {
            const data = await generateUFOVTrial(userId);
            trialData = data.trial;
            difficulty = data.current_difficulty;
            currentTrial = data;

            gamePhase = 'ready';
            loading = false;

            fixationTimer = setTimeout(() => {
                fixationTimer = null;
                showStimulusPhase();
            }, 1500);
        } catch (err) {
            error = 'Failed to load trial. Please try again.';
            loading = false;
            gamePhase = 'intro';
        }
    }

    function showStimulusPhase() {
        gamePhase = 'stimulus';
        showStimulus = true;
        responseStartTime = Date.now();

        stimulusTimer = setTimeout(() => {
            showStimulus = false;
            gamePhase = 'response';
        }, trialData.presentation_time_ms);
    }

    function leavePractice(completed = false) {
        if (stimulusTimer) {
            clearTimeout(stimulusTimer);
            stimulusTimer = null;
        }
        if (fixationTimer) {
            clearTimeout(fixationTimer);
            fixationTimer = null;
        }

        playMode = TASK_PLAY_MODE.RECORDED;
        practiceStatusMessage = completed ? getPracticeCopy($locale).complete : '';
        results = null;
        earnedBadges = [];
        loading = false;
        error = null;
        centralResponse = null;
        peripheralResponse = null;
        responseStartTime = null;
        responseTime = 0;
        showStimulus = false;
        trialsCompleted = 0;
        gamePhase = 'intro';
    }

    function selectCentralTarget(target) {
        centralResponse = target;
        if (trialData.subtest === 'central_only') {
            submitResponse();
        }
    }

    function selectPeripheralPosition(position) {
        peripheralResponse = position;
        if (centralResponse && peripheralResponse) {
            submitResponse();
        }
    }

    async function submitResponse() {
        responseTime = Date.now() - responseStartTime;
        loading = true;
        taskId = $page.url.searchParams.get('taskId');

        try {
            const data = await submitUFOVResponse(userId, {
                central_response: centralResponse,
                peripheral_response: peripheralResponse,
                trial_data: trialData,
                response_time: responseTime,
                task_id: taskId
            });

            results = {
                ...data,
                user_central_response: centralResponse,
                user_peripheral_response: peripheralResponse,
                correct_central_target: trialData.central_target,
                correct_peripheral_position: trialData.peripheral_position,
                correct_peripheral_target: trialData.peripheral_target
            };
            earnedBadges = data.new_badges || [];
            trialsCompleted++;
            gamePhase = 'results';
        } catch (err) {
            error = 'Failed to submit response. Please try again.';
        } finally {
            loading = false;
        }
    }

    function nextTrial() {
        earnedBadges = [];
        if (playMode === TASK_PLAY_MODE.PRACTICE) {
            leavePractice(true);
            return;
        }
        if (trialsCompleted >= TRIALS_PER_SESSION) {
            goto('/training');
        } else {
            loadTrial();
        }
    }

    function exitTask() {
        goto('/training');
    }

    function getPeripheralPositions() {
        return [
            { angle: 0,   label: "3 o'clock",   x: 1,      y: 0       },
            { angle: 45,  label: "1:30",         x: 0.707,  y: -0.707  },
            { angle: 90,  label: "12 o'clock",   x: 0,      y: -1      },
            { angle: 135, label: "10:30",         x: -0.707, y: -0.707  },
            { angle: 180, label: "9 o'clock",    x: -1,     y: 0       },
            { angle: 225, label: "7:30",          x: -0.707, y: 0.707   },
            { angle: 270, label: "6 o'clock",    x: 0,      y: 1       },
            { angle: 315, label: "4:30",          x: 0.707,  y: 0.707   }
        ];
    }

    function performanceLabel(perf) {
        const map = { perfect: 'Perfect!', partial: 'Good Try', incorrect: 'Keep Practicing' };
        return map[perf] || 'Keep Practicing';
    }

    function perfColor(perf) {
        const map = { perfect: '#10b981', partial: '#f59e0b', incorrect: '#ef4444' };
        return map[perf] || '#ef4444';
    }
</script>

<div class="ufov-container">

    <!-- Header -->
    <div class="task-header">        <div class="header-center">
            <h1 class="task-title">Useful Field of View</h1>
            <DifficultyBadge {difficulty} domain="Visual Scanning" />
        </div>
    </div>

    <!-- Error banner -->
    {#if error}
        <div class="error-banner">
            <p>{error}</p>
            <button on:click={() => { error = null; gamePhase = 'intro'; }}>Dismiss</button>
        </div>
    {/if}

    <!-- Loading skeleton (while fetching trial from intro) -->
    {#if loading && gamePhase === 'intro'}
        <div class="skeleton-wrap">
            <LoadingSkeleton />
        </div>

    <!-- Intro -->
    {:else if gamePhase === 'intro'}
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />
        <div class="page-content">

            <div class="concept-card">
                <div class="concept-badge">Visual Scanning · Divided Attention</div>
                <h2>Useful Field of View (UFOV)</h2>
                <p>Images flash at the center and periphery of your visual field for extremely brief durations — as short as 17ms at the highest level. Your task is to identify the central vehicle and locate peripheral shapes before the display disappears. This tests how quickly and broadly you can process visual information in a single glance.</p>
            </div>

            <div class="rules-card">
                <h3>How It Works</h3>
                <ol class="rules-list">
                    <li><strong>Fix your gaze on the center cross (+)</strong> — keep your eyes perfectly still during the flash.</li>
                    <li><strong>A brief stimulus appears</strong> — a vehicle at center and possibly a shape in the periphery. Duration ranges from 500ms (Level 1) down to 17ms (Level 10).</li>
                    <li><strong>Respond immediately</strong> — report the central vehicle type (car or truck), and for harder subtests, the position of the peripheral shape.</li>
                </ol>
            </div>

            <div class="info-grid">
                <div class="info-card">
                    <div class="info-label">Subtest 1</div>
                    <div class="info-title">Central Only</div>
                    <p>Identify the vehicle in the center of the display. Measures pure visual processing speed with no distractions.</p>
                </div>
                <div class="info-card">
                    <div class="info-label">Subtest 2</div>
                    <div class="info-title">Central + Peripheral</div>
                    <p>Identify the center vehicle and locate the peripheral shape simultaneously. Measures divided visual attention.</p>
                </div>
                <div class="info-card">
                    <div class="info-label">Subtest 3</div>
                    <div class="info-title">With Distractors</div>
                    <p>Same as Subtest 2 but with surrounding visual noise. Measures selective visual attention under clutter.</p>
                </div>
            </div>

            <div class="tip-card">
                <div class="tip-title">Strategy</div>
                <p>Do not try to consciously analyze — respond with your immediate impression. At higher levels the flash is too brief for deliberation. Trust what you sensed, even if uncertain, and answer as quickly as possible.</p>
                <div class="timing-scale">
                    <span class="ts-start">Level 1 · 500ms</span>
                    <div class="ts-bar"></div>
                    <span class="ts-end">Level 10 · 17ms</span>
                </div>
            </div>

            <div class="clinical-card">
                <h3>Clinical Basis</h3>
                <p>Ball et al. (1993) demonstrated that UFOV reduction is the strongest predictor of at-fault driving crashes, outperforming visual acuity, reaction time, and cognitive test scores. In multiple sclerosis, UFOV impairment correlates with white matter lesion volume and predicts difficulty with driving and other complex real-world tasks. It is a key measure of visual processing speed and divided attention in MS rehabilitation programmes.</p>
            </div>

            <TaskPracticeActions
                locale={$locale}
                startLabel={localeText({ en: 'Start Task', bn: 'টাস্ক শুরু করুন' }, $locale)}
                statusMessage={practiceStatusMessage}
                align="center"
                on:start={() => startTask(TASK_PLAY_MODE.RECORDED)}
                on:practice={() => startTask(TASK_PLAY_MODE.PRACTICE)}
            />
        </div>

    <!-- Ready -->
    {:else if gamePhase === 'ready'}
        <div class="page-content narrow">
            {#if playMode === TASK_PLAY_MODE.PRACTICE}
                <PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
            {/if}
            <div class="phase-card">
                <div class="trial-counter">Trial {trialsCompleted + 1} of {TRIALS_PER_SESSION}</div>
                <div class="subtest-tag">{trialData?.description}</div>
                <div class="instructions-box">{trialData?.instructions}</div>
                <div class="fixation-area">
                    <div class="fixation-cross">+</div>
                    <p class="fixation-hint">Keep your eyes on this cross</p>
                </div>
                <div class="timing-tag">Display time: <strong>{trialData?.presentation_time_ms}ms</strong></div>
            </div>
        </div>

    <!-- Stimulus -->
    {:else if gamePhase === 'stimulus'}
        {#if playMode === TASK_PLAY_MODE.PRACTICE}
            <div class="page-content narrow">
                <PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
            </div>
        {/if}
        <div class="stimulus-wrap">
            <div class="stimulus-arena">
                {#if showStimulus}
                    <div class="central-target">
                        <div class="vehicle-tag v-{trialData.central_target}">
                            {trialData.central_target === 'car' ? 'CAR' : 'TRUCK'}
                        </div>
                    </div>

                    {#if trialData.peripheral_target && trialData.peripheral_angle !== null}
                        <div
                            class="peripheral-target"
                            style="left: {50 + Math.cos(trialData.peripheral_angle * Math.PI / 180) * 40}%; top: {50 - Math.sin(trialData.peripheral_angle * Math.PI / 180) * 40}%;"
                        >
                            <div class="geo-shape geo-{trialData.peripheral_target}"></div>
                        </div>
                    {/if}

                    {#each trialData.distractors || [] as d}
                        <div
                            class="distractor-target"
                            style="left: {50 + Math.cos(d.angle * Math.PI / 180) * d.radius * 40}%; top: {50 - Math.sin(d.angle * Math.PI / 180) * d.radius * 40}%;"
                        >
                            <div class="geo-shape geo-{d.shape} dim"></div>
                        </div>
                    {/each}
                {:else}
                    <div class="fix-cross-large">+</div>
                {/if}
            </div>
        </div>

    <!-- Response -->
    {:else if gamePhase === 'response'}
        <div class="page-content">
            {#if playMode === TASK_PLAY_MODE.PRACTICE}
                <PracticeModeBanner locale={$locale} showExit on:exit={() => leavePractice()} />
            {/if}
            <div class="phase-card">
                <h2>What Did You See?</h2>
                <p class="response-sub">{trialData?.instructions}</p>

                <div class="response-group">
                    <h3>Central Vehicle</h3>
                    <div class="vehicle-choices">
                        <button
                            class="vehicle-btn {centralResponse === 'car' ? 'v-active' : ''}"
                            on:click={() => selectCentralTarget('car')}
                            disabled={loading}
                        >
                            <div class="v-chip v-car">CAR</div>
                        </button>
                        <button
                            class="vehicle-btn {centralResponse === 'truck' ? 'v-active' : ''}"
                            on:click={() => selectCentralTarget('truck')}
                            disabled={loading}
                        >
                            <div class="v-chip v-truck">TRUCK</div>
                        </button>
                    </div>
                </div>

                {#if trialData?.subtest !== 'central_only'}
                    <div class="response-group">
                        <h3>Peripheral Shape Location</h3>
                        <p class="response-hint">Where was the <strong>{trialData.peripheral_target}</strong>?</p>
                        <div class="clock-dial">
                            {#each getPeripheralPositions() as pos}
                                <button
                                    class="clock-btn {peripheralResponse === pos.label ? 'clk-active' : ''}"
                                    style="left: {50 + pos.x * 40}%; top: {50 + pos.y * 40}%;"
                                    on:click={() => selectPeripheralPosition(pos.label)}
                                    disabled={!centralResponse || loading}
                                >{pos.label}</button>
                            {/each}
                            <div class="clock-fix">+</div>
                        </div>
                        {#if !centralResponse}
                            <p class="select-note">Select the central vehicle first</p>
                        {/if}
                    </div>
                {/if}

                {#if loading}
                    <div class="submitting">Evaluating response...</div>
                {/if}
            </div>
        </div>

    <!-- Results -->
    {:else if gamePhase === 'results' && results}
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />
        <div class="page-content">
            <div class="results-card">
                <div class="perf-header" style="background: {perfColor(results.performance)}">
                    <h2>{performanceLabel(results.performance)}</h2>
                    <p class="perf-sub">Trial {trialsCompleted} of {TRIALS_PER_SESSION} complete</p>
                </div>

                <div class="results-body">

                    <div class="metrics-grid">
                        <div class="metric-cell">
                            <div class="mc-val">{((results.accuracy || 0) * 100).toFixed(0)}%</div>
                            <div class="mc-lbl">Accuracy</div>
                        </div>
                        <div class="metric-cell">
                            <div class="mc-val">{results.response_time}ms</div>
                            <div class="mc-lbl">Response Time</div>
                        </div>
                        <div class="metric-cell">
                            <div class="mc-val">{results.processing_speed_score.toFixed(2)}</div>
                            <div class="mc-lbl">Processing Speed</div>
                        </div>
                        <div class="metric-cell">
                            <div class="mc-val">{results.presentation_time_ms}ms</div>
                            <div class="mc-lbl">Display Time</div>
                        </div>
                    </div>

                    <div class="breakdown-card">
                        <h3>Trial Breakdown</h3>
                        <div class="breakdown-rows">
                            <div class="br-row">
                                <span class="br-label">Central Vehicle</span>
                                <span class="br-tag {results.central_correct ? 'tag-ok' : 'tag-err'}">
                                    {results.central_correct ? 'Correct' : 'Incorrect'}
                                </span>
                            </div>
                            {#if results.subtest !== 'central_only'}
                                <div class="br-row">
                                    <span class="br-label">Peripheral Location</span>
                                    <span class="br-tag {results.peripheral_correct ? 'tag-ok' : 'tag-err'}">
                                        {results.peripheral_correct ? 'Correct' : 'Incorrect'}
                                    </span>
                                </div>
                            {/if}
                            <div class="br-row">
                                <span class="br-label">Subtest</span>
                                <span class="br-tag tag-info">{results.subtest.replace(/_/g, ' ')}</span>
                            </div>
                        </div>
                    </div>

                    {#if results.user_central_response}
                        <div class="answer-card">
                            <h3>Answer Review</h3>
                            <div class="answer-group">
                                <div class="ag-label">Central Vehicle</div>
                                <div class="ag-row">
                                    <span class="ag-prompt">Your answer</span>
                                    <span class="ag-val {results.central_correct ? 'av-ok' : 'av-err'}">{results.user_central_response.toUpperCase()}</span>
                                </div>
                                {#if !results.central_correct}
                                    <div class="ag-row">
                                        <span class="ag-prompt">Correct answer</span>
                                        <span class="ag-val av-ok">{results.correct_central_target.toUpperCase()}</span>
                                    </div>
                                {/if}
                            </div>
                            {#if (results.subtest === 'central_peripheral' || results.subtest === 'central_peripheral_distractors') && results.correct_peripheral_position}
                                <div class="answer-group">
                                    <div class="ag-label">Peripheral Shape ({results.correct_peripheral_target})</div>
                                    <div class="ag-row">
                                        <span class="ag-prompt">Your location</span>
                                        <span class="ag-val {results.peripheral_correct ? 'av-ok' : 'av-err'}">{results.user_peripheral_response || 'Not selected'}</span>
                                    </div>
                                    {#if !results.peripheral_correct}
                                        <div class="ag-row">
                                            <span class="ag-prompt">Correct location</span>
                                            <span class="ag-val av-ok">{results.correct_peripheral_position}</span>
                                        </div>
                                    {/if}
                                </div>
                            {/if}
                        </div>
                    {/if}

                    <div class="feedback-card">
                        <p>{results.feedback_message}</p>
                    </div>

                    <div class="adapt-card">
                        {#if results.new_difficulty > results.old_difficulty}
                            <p>Level {results.old_difficulty} <span class="arr">&#8594;</span> <strong>Level {results.new_difficulty}</strong> — advancing to a shorter display time</p>
                        {:else if results.new_difficulty < results.old_difficulty}
                            <p>Adjusting to <strong>Level {results.new_difficulty}</strong> for better calibration</p>
                        {:else}
                            <p>Staying at <strong>Level {results.new_difficulty}</strong></p>
                        {/if}
                        <p class="adapt-reason">{results.adaptation_reason}</p>
                    </div>

                    <div class="progress-row">
                        <span class="prog-label">{trialsCompleted} / {TRIALS_PER_SESSION} trials complete</span>
                        <div class="prog-bar">
                            <div class="prog-fill" style="width: {(trialsCompleted / TRIALS_PER_SESSION) * 100}%"></div>
                        </div>
                    </div>

                    <div class="action-row">
                        {#if playMode === TASK_PLAY_MODE.PRACTICE}
                            <button class="start-button" on:click={nextTrial}>Finish Practice</button>
                        {:else if trialsCompleted < TRIALS_PER_SESSION}
                            <button class="start-button" on:click={nextTrial}>
                                Next Trial ({TRIALS_PER_SESSION - trialsCompleted} remaining)
                            </button>
                        {:else}
                            <button class="start-button" on:click={exitTask}>Complete Session</button>
                        {/if}                    </div>

                </div>
            </div>
        </div>
    {/if}

    <!-- BadgeNotification outside all phases -->
    {#if earnedBadges.length > 0}
        <BadgeNotification badges={earnedBadges} />
    {/if}

</div>

<style>
    /* Container */
    .ufov-container {
        min-height: 100vh;
        background: #C8DEFA;
        padding: 2rem;
        font-family: inherit;
    }

    /* Header */
    .task-header {
        max-width: 1100px;
        margin: 0 auto 2rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .back-btn {
        background: white;
        color: #0f766e;
        border: 2px solid #0f766e;
        padding: 0.6rem 1.25rem;
        border-radius: 8px;
        cursor: pointer;
        font-size: 0.9rem;
        font-weight: 600;
        white-space: nowrap;
        transition: background 0.2s, color 0.2s;
    }

    .back-btn:hover {
        background: #0f766e;
        color: white;
    }

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
        color: #134e4a;
        margin: 0;
    }

    /* Error banner */
    .error-banner {
        max-width: 1100px;
        margin: 0 auto 1.5rem;
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

    /* Skeleton */
    .skeleton-wrap {
        max-width: 800px;
        margin: 0 auto;
    }

    /* Page content */
    .page-content {
        max-width: 1100px;
        margin: 0 auto;
        display: flex;
        flex-direction: column;
        gap: 1.25rem;
    }

    .page-content.narrow {
        max-width: 680px;
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
        background: #ccfbf1;
        color: #0f766e;
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
        color: #134e4a;
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
        color: #134e4a;
        margin: 0 0 1rem;
    }

    .rules-list {
        margin: 0;
        padding-left: 1.5rem;
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }

    .rules-list li {
        color: #374151;
        line-height: 1.55;
    }

    .rules-list li strong { color: #0f766e; }

    /* Info grid (3 subtests) */
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
        color: #0f766e;
        margin-bottom: 0.4rem;
    }

    .info-title {
        font-size: 1rem;
        font-weight: 700;
        color: #134e4a;
        margin-bottom: 0.5rem;
    }

    .info-card p {
        font-size: 0.9rem;
        color: #6b7280;
        line-height: 1.5;
        margin: 0;
    }

    /* Tip card */
    .tip-card {
        background: #f0fdfa;
        border: 1px solid #99f6e4;
        border-radius: 16px;
        padding: 1.5rem 2rem;
    }

    .tip-title {
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #0f766e;
        margin-bottom: 0.5rem;
    }

    .tip-card p {
        color: #374151;
        line-height: 1.6;
        margin: 0 0 1rem;
    }

    .timing-scale {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        font-size: 0.875rem;
    }

    .ts-start { color: #0f766e; font-weight: 600; }
    .ts-end   { color: #134e4a; font-weight: 600; }

    .ts-bar {
        flex: 1;
        height: 6px;
        border-radius: 3px;
        background: linear-gradient(90deg, #5eead4 0%, #0f766e 100%);
    }

    /* Clinical card */
    .clinical-card {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border: 1px solid #bbf7d0;
        border-radius: 16px;
        padding: 1.5rem 2rem;
    }

    .clinical-card h3 {
        font-size: 1rem;
        font-weight: 700;
        color: #14532d;
        margin: 0 0 0.75rem;
    }

    .clinical-card p {
        color: #166534;
        font-size: 0.95rem;
        line-height: 1.65;
        margin: 0;
    }

    /* Phase card (ready / response) */
    .phase-card {
        background: white;
        border-radius: 16px;
        padding: 2.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        text-align: center;
    }

    .phase-card h2 {
        font-size: 1.5rem;
        font-weight: 700;
        color: #134e4a;
        margin: 0 0 0.5rem;
        text-align: center;
    }

    .trial-counter {
        font-size: 0.85rem;
        font-weight: 700;
        color: #0f766e;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 1rem;
    }

    .subtest-tag {
        display: inline-block;
        background: #ccfbf1;
        color: #0f766e;
        font-size: 0.85rem;
        font-weight: 600;
        padding: 0.3rem 0.9rem;
        border-radius: 20px;
        margin-bottom: 1rem;
    }

    .instructions-box {
        background: #f0fdfa;
        border: 1px solid #99f6e4;
        border-radius: 10px;
        padding: 0.9rem 1.25rem;
        color: #0f766e;
        font-weight: 600;
        font-size: 0.95rem;
        margin: 1rem auto 1.5rem;
        max-width: 480px;
    }

    .fixation-area {
        margin: 2rem 0;
    }

    .fixation-cross {
        font-size: 5rem;
        font-weight: 900;
        color: #134e4a;
        line-height: 1;
        margin-bottom: 0.5rem;
    }

    .fixation-hint {
        color: #6b7280;
        font-size: 0.9rem;
        font-style: italic;
        margin: 0;
    }

    .timing-tag {
        display: inline-block;
        background: #f0fdfa;
        color: #0f766e;
        border: 1px solid #99f6e4;
        padding: 0.4rem 1.1rem;
        border-radius: 20px;
        font-size: 0.9rem;
    }

    /* Stimulus arena */
    .stimulus-wrap {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 60vh;
        padding: 2rem;
    }

    .stimulus-arena {
        background: white;
        border-radius: 16px;
        width: 700px;
        height: 700px;
        max-width: calc(100vw - 4rem);
        max-height: calc(100vw - 4rem);
        position: relative;
        box-shadow: 0 8px 32px rgba(15,118,110,0.15);
        display: flex;
        align-items: center;
        justify-content: center;
        border: 2px solid #99f6e4;
    }

    .central-target {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        z-index: 10;
    }

    .vehicle-tag {
        font-size: 2rem;
        font-weight: 900;
        letter-spacing: 4px;
        padding: 0.75rem 1.75rem;
        border-radius: 8px;
    }

    .v-car   { background: #0f766e; color: white; }
    .v-truck { background: #134e4a; color: white; }

    .peripheral-target,
    .distractor-target {
        position: absolute;
        transform: translate(-50%, -50%);
    }

    .peripheral-target { z-index: 5; }
    .distractor-target { z-index: 3; }

    .geo-shape {
        width: 36px;
        height: 36px;
    }

    .geo-circle {
        background: #0f766e;
        border-radius: 50%;
    }

    .geo-square {
        background: #0f766e;
    }

    .geo-triangle {
        width: 0;
        height: 0;
        background: none;
        border-left: 18px solid transparent;
        border-right: 18px solid transparent;
        border-bottom: 32px solid #0f766e;
    }

    .geo-shape.dim {
        opacity: 0.35;
    }

    .fix-cross-large {
        font-size: 6rem;
        font-weight: 900;
        color: #134e4a;
        line-height: 1;
    }

    /* Response */
    .response-sub {
        color: #6b7280;
        font-size: 0.95rem;
        margin: 0.25rem 0 1.5rem;
        text-align: center;
    }

    .response-group {
        margin: 1.5rem 0;
        text-align: left;
    }

    .response-group h3 {
        font-size: 1rem;
        font-weight: 700;
        color: #134e4a;
        margin: 0 0 0.75rem;
        text-align: center;
    }

    .vehicle-choices {
        display: flex;
        gap: 1.25rem;
        justify-content: center;
    }

    .vehicle-btn {
        background: white;
        border: 2px solid #d1d5db;
        border-radius: 12px;
        padding: 1.25rem 2.5rem;
        cursor: pointer;
        transition: all 0.2s;
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    .vehicle-btn:hover {
        border-color: #0f766e;
        box-shadow: 0 4px 12px rgba(15,118,110,0.15);
        transform: translateY(-2px);
    }

    .vehicle-btn.v-active {
        border-color: #0f766e;
        background: #f0fdfa;
        box-shadow: 0 4px 12px rgba(15,118,110,0.2);
    }

    .vehicle-btn:disabled {
        opacity: 0.4;
        cursor: not-allowed;
        transform: none;
    }

    .v-chip {
        font-size: 1.25rem;
        font-weight: 900;
        letter-spacing: 3px;
        padding: 0.5rem 1.25rem;
        border-radius: 6px;
    }

    /* Clock dial */
    .response-hint {
        text-align: center;
        color: #6b7280;
        font-size: 0.95rem;
        margin-bottom: 1.25rem;
    }

    .clock-dial {
        position: relative;
        width: 360px;
        height: 360px;
        margin: 0 auto;
        background: #f0fdfa;
        border-radius: 50%;
        border: 2px solid #99f6e4;
    }

    .clock-btn {
        position: absolute;
        transform: translate(-50%, -50%);
        background: white;
        border: 1.5px solid #0f766e;
        color: #0f766e;
        padding: 0.35rem 0.7rem;
        border-radius: 6px;
        cursor: pointer;
        font-size: 0.8rem;
        font-weight: 600;
        transition: all 0.2s;
        white-space: nowrap;
    }

    .clock-btn:hover {
        background: #0f766e;
        color: white;
        transform: translate(-50%, -50%) scale(1.05);
    }

    .clock-btn.clk-active {
        background: #0f766e;
        color: white;
        border-color: #134e4a;
    }

    .clock-btn:disabled {
        opacity: 0.3;
        cursor: not-allowed;
    }

    .clock-fix {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-size: 1.75rem;
        font-weight: 900;
        color: #0f766e;
        width: 52px;
        height: 52px;
        background: white;
        border-radius: 50%;
        border: 2px solid #0f766e;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .select-note {
        text-align: center;
        color: #9ca3af;
        font-size: 0.875rem;
        font-style: italic;
        margin-top: 0.75rem;
    }

    .submitting {
        text-align: center;
        color: #0f766e;
        font-size: 0.9rem;
        font-style: italic;
        margin-top: 1.25rem;
        padding: 0.75rem;
        background: #f0fdfa;
        border-radius: 8px;
    }

    /* Results */
    .results-card {
        background: white;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
    }

    .perf-header {
        padding: 1.75rem 2rem;
        text-align: center;
        color: white;
    }

    .perf-header h2 {
        font-size: 1.75rem;
        font-weight: 800;
        margin: 0 0 0.25rem;
    }

    .perf-sub {
        margin: 0;
        font-size: 0.9rem;
        opacity: 0.85;
    }

    .results-body {
        padding: 2rem;
        display: flex;
        flex-direction: column;
        gap: 1.25rem;
    }

    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
    }

    .metric-cell {
        background: #f0fdfa;
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
    }

    .mc-val {
        font-size: 1.5rem;
        font-weight: 800;
        color: #0f766e;
        margin-bottom: 0.25rem;
    }

    .mc-lbl {
        font-size: 0.8rem;
        color: #6b7280;
        font-weight: 500;
    }

    /* Breakdown */
    .breakdown-card {
        background: #f8fafc;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
    }

    .breakdown-card h3 {
        font-size: 0.95rem;
        font-weight: 700;
        color: #134e4a;
        margin: 0 0 0.75rem;
    }

    .breakdown-rows {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .br-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .br-label { color: #374151; font-size: 0.9rem; }

    .br-tag {
        font-size: 0.8rem;
        font-weight: 600;
        padding: 0.2rem 0.7rem;
        border-radius: 20px;
    }

    .tag-ok   { background: #d1fae5; color: #065f46; }
    .tag-err  { background: #fee2e2; color: #991b1b; }
    .tag-info { background: #dbeafe; color: #1e40af; }

    /* Answer card */
    .answer-card {
        background: #f8fafc;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
    }

    .answer-card h3 {
        font-size: 0.95rem;
        font-weight: 700;
        color: #134e4a;
        margin: 0 0 1rem;
    }

    .answer-group {
        margin-bottom: 1rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid #e5e7eb;
    }

    .answer-group:last-child {
        border-bottom: none;
        margin-bottom: 0;
        padding-bottom: 0;
    }

    .ag-label {
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #0f766e;
        margin-bottom: 0.5rem;
    }

    .ag-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.35rem;
    }

    .ag-prompt { color: #6b7280; font-size: 0.875rem; }

    .ag-val {
        font-size: 0.875rem;
        font-weight: 700;
        padding: 0.2rem 0.7rem;
        border-radius: 6px;
    }

    .av-ok  { background: #d1fae5; color: #065f46; }
    .av-err { background: #fee2e2; color: #991b1b; }

    /* Feedback */
    .feedback-card {
        background: #fefce8;
        border-left: 4px solid #fbbf24;
        border-radius: 8px;
        padding: 1rem 1.25rem;
    }

    .feedback-card p {
        color: #78350f;
        margin: 0;
        line-height: 1.6;
        font-size: 0.95rem;
    }

    /* Adaptation */
    .adapt-card {
        background: #f0fdfa;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
    }

    .adapt-card p {
        margin: 0 0 0.35rem;
        color: #134e4a;
        font-size: 0.95rem;
    }

    .adapt-card p:last-child { margin-bottom: 0; }

    .adapt-reason {
        color: #6b7280;
        font-size: 0.875rem;
        font-style: italic;
    }

    .arr { color: #0f766e; font-weight: 700; }

    /* Progress */
    .progress-row {
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
    }

    .prog-label {
        font-size: 0.875rem;
        color: #6b7280;
        text-align: right;
    }

    .prog-bar {
        height: 10px;
        background: #e5e7eb;
        border-radius: 5px;
        overflow: hidden;
    }

    .prog-fill {
        height: 100%;
        background: linear-gradient(90deg, #5eead4 0%, #0f766e 100%);
        border-radius: 5px;
        transition: width 0.4s ease;
    }

    /* Action buttons */
    .action-row {
        display: flex;
        gap: 1rem;
    }

    .start-button {
        flex: 1;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        font-size: 1rem;
        font-weight: 700;
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .start-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }

    .btn-secondary {
        flex: 1;
        background: white;
        color: #667eea;
        border: 2px solid #667eea;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        font-size: 1rem;
        font-weight: 700;
        cursor: pointer;
        transition: all 0.2s;
    }

    .btn-secondary:hover {
        background: #667eea;
        color: white;
    }

    /* Responsive */
    @media (max-width: 768px) {
        .ufov-container { padding: 1rem; }
        .task-title { font-size: 1.35rem; }
        .back-btn { padding: 0.5rem 0.9rem; font-size: 0.8rem; }
        .metrics-grid { grid-template-columns: repeat(2, 1fr); }
        .stimulus-arena {
            width: calc(100vw - 3rem);
            height: calc(100vw - 3rem);
        }
        .clock-dial { width: 280px; height: 280px; }
        .vehicle-choices { flex-direction: column; align-items: center; }
        .action-row { flex-direction: column; }
        .results-body { padding: 1.25rem; }
        .page-content { gap: 1rem; }
    }
</style>



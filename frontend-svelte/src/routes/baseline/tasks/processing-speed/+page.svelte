<script>
    import { goto } from '$app/navigation';
    import { page } from '$app/stores';
    import { tasks, training } from '$lib/api';
    import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
    import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
    import { formatNumber, locale, localeText, translateText } from '$lib/i18n';
    import { user } from '$lib/stores';
    import { getPracticeCopy } from '$lib/task-practice';
    import { onMount } from 'svelte';

    let stage = 'intro';
    let isTrainingMode, trainingPlanId, trainingDifficulty, taskId;
    let sessionComplete = false;
    let completedTasksCount = 0;

    // Config: [simpleTrials, choiceTrials, delayMin, delayMax, penalty, choiceShapes]
    const CONFIG = {
        1:  [8,  12, 2000, 3500, 'retry', 2],
        2:  [10, 12, 1800, 3300, 'retry', 2],
        3:  [10, 15, 1500, 3000, 'count', 2],
        4:  [12, 15, 1200, 2700, 'count', 2],
        5:  [12, 15, 1000, 2500, 'count', 3],
        6:  [15, 18, 800,  2200, 'count', 3],
        7:  [15, 18, 600,  1900, 'count', 3],
        8:  [18, 20, 400,  1600, 'count', 4],
        9:  [18, 20, 300,  1500, 'count', 4],
        10: [20, 20, 300,  1500, 'count', 4]
    };

    let simpleTrials, choiceTrials, delayMin, delayMax, earlyClickPenalty, choiceShapeCount;
    let simpleCurrentTrial = 0, simpleRTs = [], simpleWaiting = false, simpleReady = false;
    let simpleStartTime = 0, simpleTimeout, earlyClickCount = 0;
    let choiceCurrentTrial = 0, choiceRTs = [], choiceAccuracy = [], choiceStimuli = [];
    let choiceCurrentShape = '', choiceStartTime = 0;
    let validSimpleRTs = [], finalScore = 0;
    let recordedSettings = null;
    let isPracticeMode = false;
    let practiceStatusMessage = '';
    let earlyClickMessage = '';   // replaces alert()
    let earlyMsgTimer = null;

    function t(text) { return translateText(text ?? '', $locale); }
    function lt(en, bn) { return localeText({ en, bn }, $locale); }
    function n(value, options = {}) { return formatNumber(value, $locale, options); }

    function shapeLabel(shape) {
        const labels = { circle: t('Circle'), square: t('Square'), triangle: t('Triangle'), diamond: t('Diamond') };
        return labels[shape] || shape;
    }

    function trialLabel(current, total) {
        return lt(`Trial ${current} / ${total}`, `ট্রায়াল ${n(current)} / ${n(total)}`);
    }

    function trainingProgressText() {
        return lt(
            `Training Progress: ${completedTasksCount} / 4 tasks completed`,
            `ট্রেনিং অগ্রগতি: ${n(completedTasksCount)} / ৪টি টাস্ক সম্পন্ন`
        );
    }

    function msText(value) { return `${n(value)}${lt('ms', 'মি.সে')}`; }

    onMount(() => {
        if (!$user) return goto('/login');
        isTrainingMode     = $page.url.searchParams.get('training') === 'true';
        trainingPlanId     = parseInt($page.url.searchParams.get('planId')) || null;
        trainingDifficulty = parseInt($page.url.searchParams.get('difficulty')) || 1;
        taskId             = $page.url.searchParams.get('taskId');

        const [st, ct, dMin, dMax, penalty, shapeCount] = CONFIG[trainingDifficulty] || CONFIG[1];
        [simpleTrials, choiceTrials, delayMin, delayMax, earlyClickPenalty, choiceShapeCount] =
            [st, ct, dMin, dMax, penalty, shapeCount];
        recordedSettings = { simpleTrials, choiceTrials, delayMin, delayMax, earlyClickPenalty, choiceShapeCount };
    });

    function showEarlyMsg(msg) {
        earlyClickMessage = msg;
        if (earlyMsgTimer) clearTimeout(earlyMsgTimer);
        earlyMsgTimer = setTimeout(() => { earlyClickMessage = ''; }, 1800);
    }

    function startSimpleTest(practice = false) {
        isPracticeMode = practice;
        practiceStatusMessage = '';
        earlyClickMessage = '';
        if (practice) {
            simpleTrials = 4; choiceTrials = 4; delayMin = 1500; delayMax = 2500;
            earlyClickPenalty = 'retry';
            choiceShapeCount = Math.min(recordedSettings?.choiceShapeCount || 2, 2);
        } else if (recordedSettings) {
            ({ simpleTrials, choiceTrials, delayMin, delayMax, earlyClickPenalty, choiceShapeCount } = recordedSettings);
        }
        stage = 'simple';
        simpleCurrentTrial = 0;
        simpleRTs = [];
        earlyClickCount = 0;
        nextSimpleTrial();
    }

    function nextSimpleTrial() {
        if (simpleCurrentTrial >= simpleTrials) { startChoiceTest(); return; }
        simpleWaiting = true;
        simpleReady = false;
        const delay = delayMin + Math.random() * (delayMax - delayMin);
        simpleTimeout = setTimeout(() => {
            simpleReady = true;
            simpleWaiting = false;
            simpleStartTime = Date.now();
        }, delay);
    }

    function handleSimpleClick() {
        if (simpleWaiting) {
            clearTimeout(simpleTimeout);
            earlyClickCount++;
            if (earlyClickPenalty === 'retry') {
                showEarlyMsg(t('Too early! Wait for the green flash.'));
                nextSimpleTrial();
            } else {
                simpleRTs.push(9999);
                showEarlyMsg($locale === 'bn'
                    ? `খুব তাড়াতাড়ি ক্লিক করেছেন! (আগাম ক্লিক: ${n(earlyClickCount)})`
                    : `Too early! (Early clicks: ${earlyClickCount})`);
                simpleCurrentTrial++;
                nextSimpleTrial();
            }
        } else if (simpleReady) {
            const rt = Date.now() - simpleStartTime;
            simpleRTs.push(rt); simpleReady = false;
            simpleCurrentTrial++;
            nextSimpleTrial();
        }
    }

    function startChoiceTest() {
        stage = 'choice';
        choiceCurrentTrial = 0; choiceRTs = []; choiceAccuracy = [];
        const shapes = ['circle', 'square'];
        if (choiceShapeCount >= 3) shapes.push('triangle');
        if (choiceShapeCount >= 4) shapes.push('diamond');
        choiceStimuli = [];
        for (let i = 0; i < choiceTrials; i++) {
            choiceStimuli.push(shapes[Math.floor(Math.random() * shapes.length)]);
        }
        nextChoiceTrial();
    }

    function nextChoiceTrial() {
        if (choiceCurrentTrial >= choiceTrials) { calculateResults(); return; }
        choiceCurrentShape = choiceStimuli[choiceCurrentTrial];
        choiceStartTime = Date.now();
    }

    function handleChoiceResponse(response) {
        const rt = Date.now() - choiceStartTime;
        choiceRTs.push(rt);
        choiceAccuracy.push(response === choiceCurrentShape);
        choiceCurrentTrial++;
        nextChoiceTrial();
    }

    function calculateResults() {
        validSimpleRTs = simpleRTs.filter((rt) => rt < 9000);
        const simpleRTMean = validSimpleRTs.length ? validSimpleRTs.reduce((a, b) => a + b) / validSimpleRTs.length : 0;
        const simpleRTStd = calculateStd(validSimpleRTs);
        const choiceRTMean = choiceRTs.length ? choiceRTs.reduce((a, b) => a + b) / choiceRTs.length : 0;
        const choiceAccScore = choiceAccuracy.filter((a) => a).length / choiceAccuracy.length;
        finalScore = calculateProcessingSpeedScore(simpleRTMean, choiceRTMean, simpleRTStd, choiceAccScore);
        if (isPracticeMode) { finishPractice(true); return; }
        stage = 'results';
        saveResults(simpleRTMean, simpleRTStd, choiceRTMean, choiceAccScore);
    }

    function finishPractice(completed = false) {
        clearTimeout(simpleTimeout);
        clearTimeout(earlyMsgTimer);
        isPracticeMode = false;
        if (recordedSettings) {
            ({ simpleTrials, choiceTrials, delayMin, delayMax, earlyClickPenalty, choiceShapeCount } = recordedSettings);
        }
        stage = 'intro';
        simpleCurrentTrial = 0; choiceCurrentTrial = 0;
        simpleRTs = []; choiceRTs = []; choiceAccuracy = [];
        earlyClickMessage = '';
        practiceStatusMessage = completed ? getPracticeCopy($locale).complete : '';
    }

    function leavePractice() {
        finishPractice(false);
    }

    async function saveResults(simpleRTMean, simpleRTStd, choiceRTMean, choiceAccScore) {
        try {
            const rawData = {
                simple_rt_mean: simpleRTMean, simple_rt_std: simpleRTStd,
                simple_trials: validSimpleRTs.length, choice_rt_mean: choiceRTMean,
                choice_rt_std: calculateStd(choiceRTs), choice_accuracy: choiceAccScore,
                choice_trials: choiceTrials
            };
            if (isTrainingMode && trainingPlanId) {
                const result = await training.submitSession({
                    user_id: $user.id, training_plan_id: trainingPlanId,
                    domain: 'processing_speed', task_type: 'reaction_time',
                    score: finalScore, accuracy: choiceAccScore * 100,
                    average_reaction_time: (simpleRTMean + choiceRTMean) / 2,
                    consistency: simpleRTStd > 0 ? Math.max(0, 100 - simpleRTStd / 10) : 100,
                    errors: choiceAccuracy.filter((a) => !a).length,
                    session_duration: 2, task_id: taskId
                });
                sessionComplete = result.session_complete;
                completedTasksCount = result.completed_tasks;
            } else {
                await tasks.submitResult($user.id, 'processing_speed', finalScore, JSON.stringify(rawData));
            }
        } catch (err) {
            console.error('Error saving results:', err);
        }
    }

    function calculateStd(arr) {
        if (arr.length === 0) return 0;
        const mean = arr.reduce((a, b) => a + b, 0) / arr.length;
        const variance = arr.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / arr.length;
        return Math.sqrt(variance);
    }

    function calculateProcessingSpeedScore(simpleRT, choiceRT, simpleStd, choiceAcc) {
        let simpleScore = 0;
        if (simpleRT <= 190)      simpleScore = 36 + ((190 - simpleRT) / 40) * 4;
        else if (simpleRT <= 250) simpleScore = 28 + ((250 - simpleRT) / 60) * 8;
        else if (simpleRT <= 310) simpleScore = 16 + ((310 - simpleRT) / 60) * 12;
        else if (simpleRT <= 400) simpleScore = 4  + ((400 - simpleRT) / 90) * 12;
        else simpleScore = Math.max(0, 4 - ((simpleRT - 400) / 100) * 4);

        let choiceSpeedScore = 0;
        if (choiceRT <= 330)      choiceSpeedScore = 27 + ((330 - choiceRT) / 50) * 3;
        else if (choiceRT <= 430) choiceSpeedScore = 21 + ((430 - choiceRT) / 100) * 6;
        else if (choiceRT <= 530) choiceSpeedScore = 12 + ((530 - choiceRT) / 100) * 9;
        else if (choiceRT <= 650) choiceSpeedScore = 3  + ((650 - choiceRT) / 120) * 9;
        else choiceSpeedScore = Math.max(0, 3 - ((choiceRT - 650) / 150) * 3);

        const choiceAccuracyScore = choiceAcc * 10;
        let consistencyScore = 0;
        if (simpleStd <= 30)       consistencyScore = 18 + ((30 - simpleStd) / 30) * 2;
        else if (simpleStd <= 50)  consistencyScore = 14 + ((50 - simpleStd) / 20) * 4;
        else if (simpleStd <= 80)  consistencyScore = 8  + ((80 - simpleStd) / 30) * 6;
        else if (simpleStd <= 120) consistencyScore = 2  + ((120 - simpleStd) / 40) * 6;
        else consistencyScore = Math.max(0, 2 - ((simpleStd - 120) / 60) * 2);

        return Math.min(100, simpleScore + choiceSpeedScore + choiceAccuracyScore + consistencyScore);
    }

    function backToDashboard() { goto(isTrainingMode ? '/training' : '/dashboard'); }
</script>

<svelte:head>
    <title>{lt('Processing Speed Test - NeuroBloom', 'প্রসেসিং স্পিড টেস্ট - NeuroBloom')}</title>
</svelte:head>

<div class="ps-container" data-localize-skip>

    <!-- INTRO -->
    {#if stage === 'intro'}
        <div class="page-content">

            <div class="task-header">
                <button class="back-btn" on:click={backToDashboard}>
                    {isTrainingMode ? 'Back to Training' : 'Back to Dashboard'}
                </button>
                <h1 class="task-title">Simple Reaction Time</h1>
            </div>

            <div class="concept-card">
                <div class="concept-badge">Processing Speed · Baseline Assessment</div>
                <h2>What This Test Measures</h2>
                <p>This two-part test measures how quickly and accurately you can process and respond to visual stimuli. Part 1 isolates pure motor reaction speed; Part 2 adds a discrimination element that taxes both speed and decision-making simultaneously.</p>
            </div>

            <div class="parts-grid">
                <div class="part-card part-1">
                    <div class="part-num">Part 1</div>
                    <div class="part-title">Simple Reaction Time</div>
                    <ul class="part-list">
                        <li>The screen flashes <span class="green-tag">GREEN</span></li>
                        <li>Click anywhere as fast as possible</li>
                        <li>Do not click before the green flash</li>
                        <li>{simpleTrials ? n(simpleTrials) : '—'} trials</li>
                    </ul>
                </div>
                <div class="part-card part-2">
                    <div class="part-num">Part 2</div>
                    <div class="part-title">Choice Reaction Time</div>
                    <ul class="part-list">
                        <li>A colored shape appears on screen</li>
                        <li>Click the matching button as fast as possible</li>
                        <li>Speed AND accuracy both matter</li>
                        <li>{choiceTrials ? n(choiceTrials) : '—'} trials · {choiceShapeCount || 2} shapes</li>
                    </ul>
                </div>
            </div>

            <div class="tip-card">
                <div class="tip-title">Strategy</div>
                <p>Stay relaxed with your hand already resting near the button. Tension slows reaction time. For Part 2, avoid guessing — a wrong click counts against your score as much as a slow correct one.</p>
                <div class="rt-scale">
                    <span class="rts-label">Excellent</span>
                    <span class="rts-range">&lt; 200ms</span>
                    <span class="rts-sep">·</span>
                    <span class="rts-label">Good</span>
                    <span class="rts-range">200–300ms</span>
                    <span class="rts-sep">·</span>
                    <span class="rts-label">Average</span>
                    <span class="rts-range">300–400ms</span>
                </div>
            </div>

            <div class="clinical-card">
                <h3>Clinical Basis</h3>
                <p>Reaction time is one of the most reliably slowed measures in multiple sclerosis, reflecting demyelination-related slowing of neural conduction velocity. Simple reaction time assessments have been used in MS research since the 1980s and remain a key component of the Symbol Digit Modalities Test (SDMT) battery. Slowed processing speed affects up to 70% of MS patients and is the strongest predictor of employment status, driving safety, and everyday functional limitations. Choice reaction time adds a discrimination component that engages frontal-parietal networks, making it sensitive to both subcortical and cortical pathology.</p>
            </div>

            <TaskPracticeActions
                locale={$locale}
                startLabel={localeText({ en: 'Start Actual Test', bn: 'আসল পরীক্ষা শুরু করুন' }, $locale)}
                statusMessage={practiceStatusMessage}
                on:start={() => startSimpleTest(false)}
                on:practice={() => startSimpleTest(true)}
            />
        </div>

    <!-- SIMPLE REACTION TIME -->
    {:else if stage === 'simple'}
        <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
        <div class="arena-wrap" class:arena-green={simpleReady} on:click={handleSimpleClick} role="button" tabindex="0" on:keydown={(e) => (e.key === ' ' || e.key === 'Enter') && handleSimpleClick()}>
            {#if isPracticeMode}
                <div class="practice-wrap">
                    <PracticeModeBanner locale={$locale} showExit on:exit={leavePractice} />
                </div>
            {/if}
            <div class="trial-counter" class:counter-green={simpleReady}>
                {trialLabel(simpleCurrentTrial + 1, simpleTrials)}
            </div>

            {#if earlyClickMessage}
                <div class="early-msg">{earlyClickMessage}</div>
            {/if}

            <div class="arena-content">
                {#if simpleWaiting}
                    <div class="arena-state waiting">
                        <div class="wait-dot"></div>
                        <p>{t('Wait...')}</p>
                    </div>
                {:else if simpleReady}
                    <div class="arena-state ready">
                        <div class="click-ring"></div>
                        <p class="click-label">{t('CLICK NOW!')}</p>
                    </div>
                {:else}
                    <div class="arena-state getready">
                        <p>{t('Get ready...')}</p>
                    </div>
                {/if}
            </div>

            <div class="arena-hint" class:hint-green={simpleReady}>
                {simpleReady ? t('Click anywhere!') : t('Wait for the green flash')}
            </div>
        </div>

    <!-- CHOICE REACTION TIME -->
    {:else if stage === 'choice'}
        <div class="page-content">
            {#if isPracticeMode}
                <PracticeModeBanner locale={$locale} showExit on:exit={leavePractice} />
            {/if}
            <div class="choice-panel">
                <div class="choice-header">
                    <div class="part-badge">Part 2 — Choice Reaction Time</div>
                    <div class="trial-tag">{trialLabel(choiceCurrentTrial + 1, choiceTrials)}</div>
                </div>

                <div class="shape-display">
                    {#if choiceCurrentShape === 'circle'}
                        <div class="shape-circle"></div>
                    {:else if choiceCurrentShape === 'square'}
                        <div class="shape-square"></div>
                    {:else if choiceCurrentShape === 'triangle'}
                        <div class="shape-triangle"></div>
                    {:else if choiceCurrentShape === 'diamond'}
                        <div class="shape-diamond"></div>
                    {/if}
                </div>

                <div class="choice-buttons">
                    <button class="choice-btn btn-circle" on:click={() => handleChoiceResponse('circle')}>
                        <div class="btn-shape-mini circle-mini"></div>
                        <span>{shapeLabel('circle')}</span>
                    </button>
                    <button class="choice-btn btn-square" on:click={() => handleChoiceResponse('square')}>
                        <div class="btn-shape-mini square-mini"></div>
                        <span>{shapeLabel('square')}</span>
                    </button>
                    {#if choiceShapeCount >= 3}
                        <button class="choice-btn btn-triangle" on:click={() => handleChoiceResponse('triangle')}>
                            <div class="btn-shape-mini triangle-mini"></div>
                            <span>{shapeLabel('triangle')}</span>
                        </button>
                    {/if}
                    {#if choiceShapeCount >= 4}
                        <button class="choice-btn btn-diamond" on:click={() => handleChoiceResponse('diamond')}>
                            <div class="btn-shape-mini diamond-mini"></div>
                            <span>{shapeLabel('diamond')}</span>
                        </button>
                    {/if}
                </div>
            </div>
        </div>

    <!-- RESULTS -->
    {:else if stage === 'results'}
        <div class="page-content">

            <div class="task-header">
                <button class="back-btn" on:click={backToDashboard}>
                    {isTrainingMode ? 'Back to Training' : 'Back to Dashboard'}
                </button>
                <h1 class="task-title">Results</h1>
            </div>

            {#if isTrainingMode}
                <div class="training-banner {sessionComplete ? 'banner-complete' : ''}">
                    {#if sessionComplete}
                        <strong>Session Complete — all 4 tasks finished.</strong>
                    {:else}
                        <strong>{trainingProgressText()}</strong>
                        <span>Continue with remaining tasks to complete this session.</span>
                    {/if}
                </div>
            {/if}

            <div class="results-card">
                <div class="score-header">
                    <div class="score-big">{n(finalScore.toFixed(1), { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%</div>
                    <div class="score-label">Processing Speed Score</div>
                </div>

                <div class="results-sections">
                    <div class="result-section">
                        <div class="section-tag tag-simple">Part 1 — Simple Reaction Time</div>
                        <div class="result-rows">
                            <div class="result-row">
                                <span>Average RT</span>
                                <strong>{msText((validSimpleRTs.reduce((a, b) => a + b, 0) / (validSimpleRTs.length || 1)).toFixed(0))}</strong>
                            </div>
                            <div class="result-row">
                                <span>Consistency (SD)</span>
                                <strong>{msText(calculateStd(validSimpleRTs).toFixed(0))}</strong>
                            </div>
                            <div class="result-row">
                                <span>Valid Trials</span>
                                <strong>{n(validSimpleRTs.length)} / {n(simpleTrials)}</strong>
                            </div>
                            {#if earlyClickCount > 0}
                                <div class="result-row warn-row">
                                    <span>Early Clicks</span>
                                    <strong>{n(earlyClickCount)}</strong>
                                </div>
                            {/if}
                        </div>
                    </div>

                    <div class="result-section">
                        <div class="section-tag tag-choice">Part 2 — Choice Reaction Time</div>
                        <div class="result-rows">
                            <div class="result-row">
                                <span>Average RT</span>
                                <strong>{msText((choiceRTs.reduce((a, b) => a + b, 0) / (choiceRTs.length || 1)).toFixed(0))}</strong>
                            </div>
                            <div class="result-row">
                                <span>Accuracy</span>
                                <strong>{n(((choiceAccuracy.filter((a) => a).length / choiceAccuracy.length) * 100).toFixed(1), { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%</strong>
                            </div>
                            <div class="result-row">
                                <span>Correct</span>
                                <strong>{n(choiceAccuracy.filter((a) => a).length)} / {n(choiceTrials)}</strong>
                            </div>
                        </div>
                    </div>
                </div>

                <button class="start-button" on:click={backToDashboard}>
                    {isTrainingMode ? t('Back to Training') : t('Back to Dashboard')}
                </button>
            </div>
        </div>
    {/if}
</div>

<style>
    /* Container */
    .ps-container {
        min-height: 100vh;
        background: #C8DEFA;
        padding: 2rem;
        font-family: inherit;
    }

    /* Page content */
    .page-content {
        max-width: 900px;
        margin: 0 auto;
        display: flex;
        flex-direction: column;
        gap: 1.25rem;
    }

    /* Task header */
    .task-header {
        display: flex;
        align-items: center;
        gap: 1.25rem;
        flex-wrap: wrap;
    }

    .back-btn {
        background: white;
        color: #b45309;
        border: 2px solid #b45309;
        padding: 0.6rem 1.25rem;
        border-radius: 8px;
        cursor: pointer;
        font-size: 0.9rem;
        font-weight: 600;
        white-space: nowrap;
        transition: background 0.2s, color 0.2s;
    }
    .back-btn:hover { background: #b45309; color: white; }

    .task-title {
        font-size: 1.75rem;
        font-weight: 700;
        color: #78350f;
        margin: 0;
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
        background: #fef3c7;
        color: #b45309;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        padding: 0.3rem 0.9rem;
        border-radius: 20px;
        margin-bottom: 0.75rem;
    }
    .concept-card h2 { font-size: 1.5rem; font-weight: 700; color: #78350f; margin: 0 0 0.75rem; }
    .concept-card p  { color: #374151; line-height: 1.65; margin: 0; }

    /* Parts grid */
    .parts-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
        gap: 1rem;
    }

    .part-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        border-top: 4px solid transparent;
    }
    .part-1 { border-top-color: #16a34a; }
    .part-2 { border-top-color: #b45309; }

    .part-num {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #b45309;
        margin-bottom: 0.25rem;
    }
    .part-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #78350f;
        margin-bottom: 0.75rem;
    }
    .part-list {
        margin: 0;
        padding-left: 1.25rem;
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
    }
    .part-list li { color: #374151; font-size: 0.9rem; line-height: 1.5; }

    .green-tag {
        display: inline-block;
        background: #dcfce7;
        color: #15803d;
        font-weight: 700;
        padding: 0.1rem 0.5rem;
        border-radius: 4px;
        font-size: 0.85rem;
    }

    /* Tip card */
    .tip-card {
        background: #fffbeb;
        border: 1px solid #fde68a;
        border-radius: 16px;
        padding: 1.5rem 2rem;
    }
    .tip-title {
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #b45309;
        margin-bottom: 0.5rem;
    }
    .tip-card p { color: #374151; line-height: 1.6; margin: 0 0 1rem; }

    .rt-scale {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex-wrap: wrap;
        font-size: 0.85rem;
    }
    .rts-label { font-weight: 700; color: #b45309; }
    .rts-range { color: #374151; }
    .rts-sep   { color: #d1d5db; }

    /* Clinical card */
    .clinical-card {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border: 1px solid #bbf7d0;
        border-radius: 16px;
        padding: 1.5rem 2rem;
    }
    .clinical-card h3 { font-size: 1rem; font-weight: 700; color: #14532d; margin: 0 0 0.75rem; }
    .clinical-card p  { color: #166534; font-size: 0.95rem; line-height: 1.65; margin: 0; }

    /* ============================================================
       SIMPLE REACTION TIME ARENA (full screen flash zone)
    ============================================================ */
    .arena-wrap {
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        background: #1e293b;
        transition: background 0.08s ease;
        user-select: none;
        position: relative;
        padding: 2rem;
    }
    .arena-wrap.arena-green { background: #16a34a; }

    .practice-wrap {
        position: absolute;
        top: 1rem;
        left: 50%;
        transform: translateX(-50%);
        width: 100%;
        max-width: 600px;
        padding: 0 1rem;
    }

    .trial-counter {
        position: absolute;
        top: 1.5rem;
        right: 2rem;
        background: rgba(255,255,255,0.15);
        color: rgba(255,255,255,0.8);
        font-size: 0.85rem;
        font-weight: 600;
        padding: 0.35rem 0.9rem;
        border-radius: 20px;
    }
    .trial-counter.counter-green { background: rgba(255,255,255,0.25); color: white; }

    .early-msg {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -60px);
        background: #fef3c7;
        color: #92400e;
        font-size: 1rem;
        font-weight: 600;
        padding: 0.6rem 1.5rem;
        border-radius: 10px;
        pointer-events: none;
        text-align: center;
        white-space: nowrap;
    }

    .arena-content { text-align: center; }

    .arena-state { display: flex; flex-direction: column; align-items: center; gap: 1.5rem; }

    .arena-state.waiting p  { color: rgba(255,255,255,0.5); font-size: 1.5rem; font-weight: 500; margin: 0; }
    .arena-state.ready  p   { margin: 0; }
    .arena-state.getready p { color: rgba(255,255,255,0.4); font-size: 1.25rem; margin: 0; }

    .wait-dot {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background: rgba(255,255,255,0.2);
        animation: pulse-slow 1.5s ease-in-out infinite;
    }
    @keyframes pulse-slow {
        0%, 100% { transform: scale(1);   opacity: 0.4; }
        50%       { transform: scale(1.4); opacity: 0.7; }
    }

    .click-ring {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        border: 6px solid white;
        animation: ring-pulse 0.5s ease-in-out infinite alternate;
    }
    @keyframes ring-pulse {
        from { transform: scale(0.92); opacity: 0.8; }
        to   { transform: scale(1.06); opacity: 1; }
    }

    .click-label {
        font-size: 3rem;
        font-weight: 900;
        color: white;
        letter-spacing: 4px;
        text-shadow: 0 2px 12px rgba(0,0,0,0.2);
    }

    .arena-hint {
        position: absolute;
        bottom: 2rem;
        color: rgba(255,255,255,0.4);
        font-size: 0.9rem;
    }
    .arena-hint.hint-green { color: rgba(255,255,255,0.75); }

    /* ============================================================
       CHOICE REACTION TIME
    ============================================================ */
    .choice-panel {
        background: white;
        border-radius: 16px;
        padding: 2.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        text-align: center;
    }

    .choice-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 2rem;
        flex-wrap: wrap;
        gap: 0.75rem;
    }

    .part-badge {
        background: #fef3c7;
        color: #b45309;
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 0.3rem 0.9rem;
        border-radius: 20px;
    }

    .trial-tag {
        background: #f1f5f9;
        color: #475569;
        font-size: 0.85rem;
        font-weight: 600;
        padding: 0.3rem 0.9rem;
        border-radius: 20px;
    }

    /* Shape display */
    .shape-display {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 200px;
        margin: 1rem 0 2.5rem;
    }

    .shape-circle  { width: 140px; height: 140px; border-radius: 50%; background: #2563eb; }
    .shape-square  { width: 140px; height: 140px; background: #b45309; }
    .shape-diamond {
        width: 100px; height: 100px;
        background: #7c3aed;
        transform: rotate(45deg);
    }
    .shape-triangle {
        width: 0; height: 0;
        border-left: 70px solid transparent;
        border-right: 70px solid transparent;
        border-bottom: 122px solid #16a34a;
    }

    /* Choice buttons */
    .choice-buttons {
        display: flex;
        gap: 1rem;
        justify-content: center;
        flex-wrap: wrap;
    }

    .choice-btn {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.6rem;
        padding: 1rem 1.75rem;
        background: white;
        border: 2px solid #e5e7eb;
        border-radius: 12px;
        cursor: pointer;
        font-size: 0.95rem;
        font-weight: 600;
        color: #374151;
        min-width: 110px;
        transition: all 0.15s ease;
    }
    .choice-btn:hover { transform: translateY(-3px); box-shadow: 0 6px 16px rgba(0,0,0,0.1); }

    .btn-circle:hover   { border-color: #2563eb; color: #2563eb; }
    .btn-square:hover   { border-color: #b45309; color: #b45309; }
    .btn-triangle:hover { border-color: #16a34a; color: #16a34a; }
    .btn-diamond:hover  { border-color: #7c3aed; color: #7c3aed; }

    /* Mini shapes in buttons */
    .btn-shape-mini { flex-shrink: 0; }
    .circle-mini   { width: 36px; height: 36px; border-radius: 50%; background: #2563eb; }
    .square-mini   { width: 36px; height: 36px; background: #b45309; }
    .triangle-mini {
        width: 0; height: 0;
        border-left: 18px solid transparent;
        border-right: 18px solid transparent;
        border-bottom: 31px solid #16a34a;
    }
    .diamond-mini  {
        width: 26px; height: 26px;
        background: #7c3aed;
        transform: rotate(45deg);
        margin: 5px 5px;
    }

    /* ============================================================
       RESULTS
    ============================================================ */
    .training-banner {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.25rem 1.75rem;
        border-radius: 12px;
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
    }
    .training-banner strong { font-size: 1rem; font-weight: 700; }
    .training-banner span   { font-size: 0.875rem; opacity: 0.85; }
    .banner-complete        { background: linear-gradient(135deg, #16a34a, #0f766e); }

    .results-card {
        background: white;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
    }

    .score-header {
        background: linear-gradient(135deg, #b45309 0%, #78350f 100%);
        padding: 2rem;
        text-align: center;
        color: white;
    }
    .score-big {
        font-size: 4rem;
        font-weight: 900;
        line-height: 1;
        margin-bottom: 0.35rem;
    }
    .score-label { font-size: 0.9rem; opacity: 0.85; font-weight: 500; }

    .results-sections {
        padding: 1.75rem;
        display: flex;
        flex-direction: column;
        gap: 1.25rem;
    }

    .result-section { background: #fafafa; border-radius: 12px; padding: 1.25rem; }

    .section-tag {
        display: inline-block;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 0.25rem 0.8rem;
        border-radius: 20px;
        margin-bottom: 1rem;
    }
    .tag-simple { background: #dcfce7; color: #15803d; }
    .tag-choice { background: #fef3c7; color: #b45309; }

    .result-rows { display: flex; flex-direction: column; gap: 0.5rem; }

    .result-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.4rem 0;
        border-bottom: 1px solid #f1f5f9;
    }
    .result-row:last-child { border-bottom: none; }
    .result-row span  { color: #6b7280; font-size: 0.9rem; }
    .result-row strong { color: #1e293b; font-size: 0.95rem; font-weight: 700; }

    .warn-row span, .warn-row strong { color: #d97706; }

    .start-button {
        display: block;
        width: calc(100% - 3.5rem);
        margin: 0 1.75rem 1.75rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 1rem;
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

    /* Responsive */
    @media (max-width: 768px) {
        .ps-container { padding: 1rem; }
        .task-title  { font-size: 1.4rem; }
        .back-btn    { padding: 0.5rem 0.9rem; font-size: 0.8rem; }
        .choice-panel { padding: 1.5rem; }
        .choice-buttons { gap: 0.75rem; }
        .choice-btn { padding: 0.9rem 1.25rem; min-width: 90px; }
        .score-big  { font-size: 3rem; }
        .results-sections { padding: 1.25rem; }
        .start-button { width: calc(100% - 2.5rem); margin: 0 1.25rem 1.25rem; }
    }
</style>

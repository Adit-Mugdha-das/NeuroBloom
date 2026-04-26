<script>
    import { goto } from '$app/navigation';
    import { page } from '$app/stores';
    import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
    import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
import TaskReturnButton from '$lib/components/TaskReturnButton.svelte';
    import { formatNumber, locale, localeText } from '$lib/i18n';
    import { tasks, training } from '$lib/api';
    import { user } from '$lib/stores';
    import { getPracticeCopy } from '$lib/task-practice';
import { TASK_RETURN_CONTEXT } from '$lib/task-navigation';
    import { onMount } from 'svelte';

    let stage = 'intro'; // intro | test | results
    let currentTrial = 0;
    let totalTrials = 40;

    let isTrainingMode = false;
    let trainingPlanId = null;
    let trainingDifficulty = 1;
    let taskId = null;
    let sessionComplete = false;
    let completedTasksCount = 0;
    let totalTasksCount = 4;

    let trials = [];
    let currentNumber = 0;
    let currentColor = '';
    let currentRule = '';
    let responses = [];
    let reactionTimes = [];

    let switchTrials = 0;
    let switchErrors = 0;
    let noSwitchErrors = 0;
    let totalErrors = 0;
    let switchCostRT = 0;
    let perseverationErrors = 0;
    let accuracy = 0;
    let meanRT = 0;
    let isPracticeMode = false;
    let practiceStatusMessage = '';
    let recordedTotalTrials = 40;

    // Feedback flash
    let lastFeedback = ''; // 'correct' | 'wrong' | ''
    let feedbackTimer = null;
    let acceptingResponse = false;

    function lt(en, bn) {
        return localeText({ en, bn }, $locale);
    }

    function n(value, options = {}) {
        return formatNumber(value, $locale, options);
    }

    onMount(() => {
        if (!$user) return goto('/login');
        const urlParams = new URLSearchParams(window.location.search);
        isTrainingMode     = urlParams.get('training') === 'true';
        trainingPlanId     = parseInt(urlParams.get('planId')) || null;
        trainingDifficulty = parseInt(urlParams.get('difficulty')) || 1;
        taskId             = $page.url.searchParams.get('taskId');
        if (isTrainingMode && trainingDifficulty > 4) {
            totalTrials = 40 + (trainingDifficulty - 4) * 10;
        }
        recordedTotalTrials = totalTrials;
    });

    function backToDashboard() {
        goto('/dashboard');
    }

    function startTest(practice = false) {
        isPracticeMode = practice;
        practiceStatusMessage = '';
        totalTrials = practice ? 12 : recordedTotalTrials;
        currentTrial = 0;
        trials = []; responses = []; reactionTimes = [];
        switchTrials = switchErrors = noSwitchErrors = totalErrors = 0;
        switchCostRT = perseverationErrors = accuracy = meanRT = 0;
        lastFeedback = '';
        acceptingResponse = false;
        stage = 'test';
        generateTrials();
        showNextTrial();
    }

    function generateTrials() {
        const numbers = [1, 2, 3, 4, 6, 7, 8, 9];
        const colors = ['blue', 'red'];
        trials = [];
        let lastRule = '';
        for (let i = 0; i < totalTrials; i++) {
            const number = numbers[Math.floor(Math.random() * numbers.length)];
            const color  = colors[Math.floor(Math.random() * colors.length)];
            const rule   = color === 'blue' ? 'parity' : 'magnitude';
            const isSwitch = i > 0 && rule !== lastRule;
            trials.push({ number, color, rule, isSwitch });
            if (isSwitch) switchTrials++;
            lastRule = rule;
        }
    }

    let trialStartTime = 0;

    function showNextTrial() {
        if (currentTrial >= totalTrials) { calculateResults(); return; }
        const trial = trials[currentTrial];
        if (!trial) {
            calculateResults();
            return;
        }
        currentNumber = trial.number;
        currentColor  = trial.color;
        currentRule   = trial.rule;
        trialStartTime = Date.now();
        acceptingResponse = true;
    }

    function handleResponse(answer) {
        if (!acceptingResponse) return;
        const rt = Date.now() - trialStartTime;
        const trial = trials[currentTrial];
        if (!trial) {
            acceptingResponse = false;
            calculateResults();
            return;
        }
        acceptingResponse = false;
        let correctAnswer;
        if (trial.rule === 'parity') {
            correctAnswer = trial.number % 2 === 0 ? 'even' : 'odd';
        } else {
            correctAnswer = trial.number > 5 ? 'high' : 'low';
        }
        const isCorrect = answer === correctAnswer;
        responses.push({ trial: currentTrial, answer, correctAnswer, isCorrect, rt, isSwitch: trial.isSwitch });
        reactionTimes.push(rt);

        lastFeedback = isCorrect ? 'correct' : 'wrong';
        if (feedbackTimer) clearTimeout(feedbackTimer);
        feedbackTimer = setTimeout(() => {
            lastFeedback = '';
            currentTrial++;
            showNextTrial();
        }, 300);
    }

    function calculateResults() {
        switchErrors = noSwitchErrors = perseverationErrors = 0;
        let switchRTs = [], noSwitchRTs = [];
        for (let i = 0; i < responses.length; i++) {
            const r = responses[i];
            if (!r.isCorrect) {
                totalErrors++;
                if (r.isSwitch) {
                    switchErrors++;
                    if (i > 0) {
                        const prev = trials[i - 1];
                        const cur  = trials[i];
                        const prevRuleAns = prev.rule === 'parity'
                            ? (cur.number % 2 === 0 ? 'even' : 'odd')
                            : (cur.number > 5 ? 'high' : 'low');
                        if (r.answer === prevRuleAns) perseverationErrors++;
                    }
                } else { noSwitchErrors++; }
            }
            if (r.isSwitch) switchRTs.push(r.rt);
            else if (i > 0) noSwitchRTs.push(r.rt);
        }
        accuracy = responses.length > 0 ? ((responses.length - totalErrors) / responses.length) * 100 : 0;
        const avgSwitch   = switchRTs.length   ? switchRTs.reduce((a,b)=>a+b,0)/switchRTs.length     : 0;
        const avgNoSwitch = noSwitchRTs.length ? noSwitchRTs.reduce((a,b)=>a+b,0)/noSwitchRTs.length : 0;
        switchCostRT = avgSwitch - avgNoSwitch;
        meanRT = reactionTimes.length > 0 ? reactionTimes.reduce((a,b)=>a+b,0) / reactionTimes.length : 0;

        if (isPracticeMode) { leavePractice(true); return; }
        stage = 'results';
        saveResults();
    }

    function leavePractice(completed = false) {
        if (feedbackTimer) {
            clearTimeout(feedbackTimer);
            feedbackTimer = null;
        }
        isPracticeMode = false;
        totalTrials = recordedTotalTrials;
        currentTrial = 0;
        responses = [];
        reactionTimes = [];
        switchTrials = 0;
        switchErrors = 0;
        noSwitchErrors = 0;
        totalErrors = 0;
        switchCostRT = 0;
        perseverationErrors = 0;
        accuracy = 0;
        meanRT = 0;
        lastFeedback = '';
        acceptingResponse = false;
        practiceStatusMessage = completed ? getPracticeCopy($locale).complete : '';
        stage = 'intro';
    }

    async function saveResults() {
        try {
            const rtStd = calculateStd(reactionTimes);
            if (isTrainingMode && trainingPlanId) {
                const result = await training.submitSession({
                    user_id: $user.id,
                    training_plan_id: trainingPlanId,
                    domain: 'flexibility',
                    task_type: 'task_switching',
                    score: accuracy, accuracy,
                    average_reaction_time: meanRT,
                    consistency: rtStd > 0 ? Math.max(0, 100 - rtStd / 2) : 100,
                    errors: totalErrors,
                    session_duration: totalTrials / 10,
                    task_id: taskId
                });
                sessionComplete     = result.session_complete;
                completedTasksCount = result.completed_tasks;
                totalTasksCount     = result.total_tasks;
            } else {
                await tasks.submitResult(
                    $user.id, 'flexibility', accuracy,
                    JSON.stringify({
                        total_trials: totalTrials, total_switches: switchTrials,
                        switch_errors: switchErrors, no_switch_errors: noSwitchErrors,
                        perseveration_errors: perseverationErrors,
                        switch_cost_rt: switchCostRT, mean_rt: meanRT, rt_std: rtStd
                    })
                );
            }
        } catch (err) { console.error('Error saving results:', err); }
    }

    function calculateStd(arr) {
        if (arr.length === 0) return 0;
        const mean = arr.reduce((a,b)=>a+b,0) / arr.length;
        return Math.sqrt(arr.reduce((s,v)=>s+Math.pow(v-mean,2),0) / arr.length);
    }

    function flexibilityLabel() {
        if (switchCostRT < 150) return 'Excellent flexibility — you adapt quickly to changing rules.';
        if (switchCostRT < 300) return 'Good flexibility. With practice, you can reduce your switch cost further.';
        return 'Keep practicing. Task switching improves significantly with regular training.';
    }
</script>

<svelte:head>
    <title>{lt('Cognitive Flexibility Test - NeuroBloom', 'মানসিক নমনীয়তা পরীক্ষা - NeuroBloom')}</title>
</svelte:head>

<div class="flex-container" data-localize-skip>

    <!-- INTRO -->
    {#if stage === 'intro'}
        <div class="intro-wrapper">
            <TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.BASELINE} />

            <div class="task-header">                <h1 class="task-title">{lt('Task Switching', 'টাস্ক সুইচিং')}</h1>
            </div>

            <div class="concept-card">
                <div class="concept-badge">Cognitive Flexibility · Baseline Assessment</div>
                <h2>What This Test Measures</h2>
                <p>This test measures <strong>cognitive flexibility</strong> — your ability to shift between mental rules rapidly and without errors. You will judge numbers using two different rules, with the active rule determined by the background colour. The key metric is <em>switch cost</em>: how much slower and less accurate you are on rule-switch trials compared to rule-repeat trials.</p>
            </div>

            <div class="rules-card">
                <h3>The Two Rules</h3>
                <div class="rule-pair">
                    <div class="rule-block rule-blue">
                        <div class="rule-color-tag">Blue background</div>
                        <div class="rule-title">Parity Rule</div>
                        <div class="rule-desc">Is the number <strong>Odd</strong> or <strong>Even</strong>?</div>
                        <div class="rule-example">
                            <span class="num-badge">7</span> → Odd &nbsp;·&nbsp;
                            <span class="num-badge">4</span> → Even
                        </div>
                    </div>
                    <div class="rule-block rule-red">
                        <div class="rule-color-tag">Red background</div>
                        <div class="rule-title">Magnitude Rule</div>
                        <div class="rule-desc">Is the number <strong>Low (&lt;5)</strong> or <strong>High (&gt;5)</strong>?</div>
                        <div class="rule-example">
                            <span class="num-badge">3</span> → Low &nbsp;·&nbsp;
                            <span class="num-badge">8</span> → High
                        </div>
                    </div>
                </div>
                <div class="rules-note">Note: the number 5 does not appear. Numbers used: 1 2 3 4 6 7 8 9</div>
            </div>

            <div class="switch-example">
                <div class="se-title">Switch Example</div>
                <div class="se-sequence">
                    <div class="se-card se-blue"><span class="se-num">7</span><span class="se-ans">Odd</span></div>
                    <div class="se-arrow">→</div>
                    <div class="se-card se-blue"><span class="se-num">2</span><span class="se-ans">Even</span></div>
                    <div class="se-arrow se-switch-arrow">→ SWITCH</div>
                    <div class="se-card se-red"><span class="se-num">7</span><span class="se-ans">High</span></div>
                    <div class="se-arrow">→</div>
                    <div class="se-card se-red"><span class="se-num">3</span><span class="se-ans">Low</span></div>
                </div>
            </div>

            <div class="tip-card">
                <div class="tip-title">Strategy</div>
                <p>Look at the background color first — that tells you which rule to apply. The most common error is "perseveration": accidentally using the previous rule after a switch. When the color changes, pause for a half-second to consciously register the new rule before responding.</p>
            </div>

            <div class="clinical-card">
                <h3>Clinical Basis</h3>
                <p>Cognitive flexibility is among the most commonly impaired executive functions in MS, reflecting damage to prefrontal-basal ganglia circuits involved in rule representation and task-set reconfiguration. Switch cost — the slowdown on rule-change trials — is a particularly sensitive marker: it scales with white matter lesion burden and is predictive of vocational and instrumental daily living difficulties. Perseveration errors (applying the last rule instead of the new one) indicate failed inhibition of dominant response sets, a signature of frontal lobe pathology.</p>
            </div>

            <TaskPracticeActions
                locale={$locale}
                startLabel={localeText({ en: 'Start Actual Task', bn: 'আসল টাস্ক শুরু করুন' }, $locale)}
                statusMessage={practiceStatusMessage}
                align="center"
                on:start={() => startTest(false)}
                on:practice={() => startTest(true)}
            />
        </div>

    <!-- TEST -->
    {:else if stage === 'test'}
        <div class="test-arena" class:arena-blue={currentColor === 'blue'} class:arena-red={currentColor === 'red'}>
            {#if isPracticeMode}
                <div class="practice-wrap">
                    <PracticeModeBanner locale={$locale} showExit on:exit={leavePractice} />
                </div>
            {/if}

            <div class="arena-top">
                <div class="trial-pill">{n(currentTrial + 1)} / {n(totalTrials)}</div>
                {#if trials[currentTrial]?.isSwitch}
                    <div class="switch-pill">{lt('Rule switch', 'নিয়ম বদল')}</div>
                {/if}
            </div>

            <div class="number-display" class:feedback-correct={lastFeedback === 'correct'} class:feedback-wrong={lastFeedback === 'wrong'}>
                {currentNumber}
            </div>

            <div class="rule-hint">
                {#if currentColor === 'blue'}
                    <span class="hint-label blue-hint">Parity</span> — Odd or Even?
                {:else}
                    <span class="hint-label red-hint">Magnitude</span> — Low (&lt;5) or High (&gt;5)?
                {/if}
            </div>

            <div class="response-buttons">
                {#if currentRule === 'parity'}
                    <button class="resp-btn resp-left" on:click={() => handleResponse('odd')} disabled={!acceptingResponse}>{lt('Odd', 'বিজোড়')}</button>
                    <button class="resp-btn resp-right" on:click={() => handleResponse('even')} disabled={!acceptingResponse}>{lt('Even', 'জোড়')}</button>
                {:else}
                    <button class="resp-btn resp-left" on:click={() => handleResponse('low')} disabled={!acceptingResponse}>&lt; 5&ensp;{lt('Low', 'কম')}</button>
                    <button class="resp-btn resp-right" on:click={() => handleResponse('high')} disabled={!acceptingResponse}>&gt; 5&ensp;{lt('High', 'বেশি')}</button>
                {/if}
            </div>
        </div>

    <!-- RESULTS -->
    {:else if stage === 'results'}
        <div class="intro-wrapper">
            <TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.BASELINE} />

            <div class="task-header">                <h1 class="task-title">{lt('Results', 'ফলাফল')}</h1>
            </div>

            {#if isTrainingMode}
                <div class="training-banner {sessionComplete ? 'banner-complete' : ''}">
                    {#if sessionComplete}
                        <strong>Session Complete — all {totalTasksCount} tasks finished.</strong>
                    {:else}
                        <strong>Training Progress: {completedTasksCount} / {totalTasksCount} tasks completed</strong>
                        <span>Continue with remaining tasks to complete this session.</span>
                    {/if}
                </div>
            {/if}

            <div class="results-card">
                <div class="score-header">
                    <div class="score-big">{accuracy.toFixed(1)}%</div>
                    <div class="score-label">{lt('Overall Accuracy', 'সামগ্রিক নির্ভুলতা')}</div>
                </div>

                <div class="metrics-grid">
                    <div class="metric-cell">
                        <div class="metric-value">{meanRT.toFixed(0)}ms</div>
                        <div class="metric-label">{lt('Avg Response Time', 'গড় প্রতিক্রিয়া সময়')}</div>
                    </div>
                    <div class="metric-cell {switchCostRT < 150 ? 'metric-good' : switchCostRT < 300 ? '' : 'metric-warn'}">
                        <div class="metric-value">{switchCostRT > 0 ? '+' : ''}{switchCostRT.toFixed(0)}ms</div>
                        <div class="metric-label">{lt('Switch Cost (RT)', 'সুইচ কস্ট (RT)')}</div>
                    </div>
                    <div class="metric-cell {totalErrors === 0 ? 'metric-good' : 'metric-warn'}">
                        <div class="metric-value">{totalErrors}</div>
                        <div class="metric-label">{lt('Total Errors', 'মোট ভুল')}</div>
                    </div>
                    <div class="metric-cell">
                        <div class="metric-value">{switchErrors}</div>
                        <div class="metric-label">{lt('Switch Errors', 'নিয়ম বদলের ভুল')}</div>
                    </div>
                    <div class="metric-cell">
                        <div class="metric-value">{noSwitchErrors}</div>
                        <div class="metric-label">{lt('Repeat Errors', 'একই নিয়মের ভুল')}</div>
                    </div>
                    <div class="metric-cell {perseverationErrors > 3 ? 'metric-warn' : ''}">
                        <div class="metric-value">{perseverationErrors}</div>
                        <div class="metric-label">{lt('Perseveration Errors', 'পুরোনো নিয়মে আটকে যাওয়ার ভুল')}</div>
                    </div>
                </div>

                <div class="interp-card">
                    <div class="interp-title">{lt('Interpretation', 'ব্যাখ্যা')}</div>
                    <p>{flexibilityLabel()}</p>
                    {#if perseverationErrors > 3}
                        <p class="persev-note">You had {perseverationErrors} perseveration errors — applying the old rule after a switch. Focus on the background color change as your cue to reset.</p>
                    {/if}
                </div>

                <button class="start-button" on:click={backToDashboard}>
                    {lt('Back to Dashboard', 'ড্যাশবোর্ডে ফিরে যান')}
                </button>
            </div>
        </div>
    {/if}
</div>

<style>
    /* Container */
    .flex-container {
        min-height: 100vh;
        background: #C8DEFA;
        padding: 2rem;
        font-family: inherit;
    }

    /* Unified intro/results card */
    .intro-wrapper {
        max-width: 960px;
        margin: 0 auto;
        width: 100%;
        background: white;
        border-radius: 16px;
        padding: 2.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07), 0 1px 3px rgba(0,0,0,0.06);
        display: flex;
        flex-direction: column;
        gap: 1.8rem;
    }
    .intro-wrapper .concept-card,
    .intro-wrapper .rules-card,
    .intro-wrapper .switch-example,
    .intro-wrapper .results-card { box-shadow: none; }

    /* Task header */
    .task-header {
        display: flex;
        align-items: center;
        gap: 1.25rem;
        flex-wrap: wrap;
    }

    .task-title {
        font-size: 1.75rem;
        font-weight: 700;
        color: #1e293b;
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
        background: #e0f2fe;
        color: #0e7490;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        padding: 0.3rem 0.9rem;
        border-radius: 20px;
        margin-bottom: 0.75rem;
    }
    .concept-card h2 { font-size: 1.4rem; font-weight: 700; color: #0e7490; margin: 0 0 0.75rem; }
    .concept-card p  { color: #374151; line-height: 1.65; margin: 0; }

    /* Rules card */
    .rules-card {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
    }
    .rules-card h3 { font-size: 1.1rem; font-weight: 700; color: #0e7490; margin: 0 0 1.25rem; }

    .rule-pair {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 1rem;
        margin-bottom: 1rem;
    }
    .rule-block {
        border-radius: 12px;
        padding: 1.25rem;
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
    }
    .rule-blue { background: #eff6ff; border: 2px solid #93c5fd; }
    .rule-red  { background: #fff1f2; border: 2px solid #fca5a5; }

    .rule-color-tag {
        font-size: 0.75rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .rule-blue .rule-color-tag { color: #1d4ed8; }
    .rule-red  .rule-color-tag { color: #b91c1c; }

    .rule-title { font-size: 1.1rem; font-weight: 800; color: #1e293b; }
    .rule-desc  { color: #374151; font-size: 0.9rem; }
    .rule-example {
        font-size: 0.85rem; color: #374151; margin-top: 0.25rem;
        display: flex; align-items: center; gap: 0.35rem; flex-wrap: wrap;
    }
    .num-badge {
        background: rgba(0,0,0,0.12);
        font-weight: 800;
        padding: 0.1rem 0.5rem;
        border-radius: 4px;
    }
    .rules-note { font-size: 0.82rem; color: #6b7280; }

    /* Switch Example */
    .switch-example {
        background: white;
        border-radius: 16px;
        padding: 1.5rem 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
    }
    .se-title { font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #0e7490; margin-bottom: 1rem; }

    .se-sequence {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        flex-wrap: wrap;
    }
    .se-card {
        display: flex; flex-direction: column; align-items: center;
        padding: 0.75rem 1rem;
        border-radius: 10px;
        min-width: 60px;
    }
    .se-blue { background: #2563eb; color: white; }
    .se-red  { background: #dc2626; color: white; }
    .se-num  { font-size: 1.75rem; font-weight: 900; font-family: monospace; line-height: 1; }
    .se-ans  { font-size: 0.75rem; font-weight: 700; opacity: 0.9; }

    .se-arrow { color: #9ca3af; font-size: 1rem; font-weight: 300; white-space: nowrap; }
    .se-switch-arrow { color: #0e7490; font-weight: 700; font-size: 0.85rem; }

    /* Tip card */
    .tip-card {
        background: #f0f9ff;
        border: 1px solid #bae6fd;
        border-radius: 16px;
        padding: 1.5rem 2rem;
    }
    .tip-title { font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #0e7490; margin-bottom: 0.5rem; }
    .tip-card p { color: #374151; line-height: 1.6; margin: 0; }

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
       TEST ARENA (card panel)
    ============================================================ */
    .test-arena {
        max-width: 680px;
        margin: 0 auto;
        width: 100%;
        min-height: 520px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 2rem 1rem;
        transition: background 0.15s ease;
        position: relative;
        border-radius: 26px;
        box-shadow: 0 24px 60px rgba(19, 52, 74, 0.15);
        overflow: hidden;
    }
    .arena-blue { background: #1d4ed8; }
    .arena-red  { background: #b91c1c; }

    .practice-wrap {
        position: absolute;
        top: 1rem;
        left: 50%;
        transform: translateX(-50%);
        width: 100%;
        max-width: 600px;
        padding: 0 1rem;
    }

    .arena-top {
        position: absolute;
        top: 1.5rem;
        display: flex;
        gap: 0.75rem;
        align-items: center;
    }

    .trial-pill {
        background: rgba(255,255,255,0.15);
        color: rgba(255,255,255,0.8);
        font-size: 0.85rem; font-weight: 600;
        padding: 0.35rem 1rem;
        border-radius: 20px;
    }
    .switch-pill {
        background: rgba(255,255,255,0.25);
        color: white;
        font-size: 0.8rem; font-weight: 700;
        padding: 0.35rem 0.9rem;
        border-radius: 20px;
        animation: pop-in 0.15s ease-out;
    }
    @keyframes pop-in {
        from { transform: scale(0.85); opacity: 0; }
        to   { transform: scale(1);    opacity: 1; }
    }

    /* The big number */
    .number-display {
        font-size: 11rem;
        font-weight: 900;
        font-family: 'Courier New', monospace;
        color: white;
        line-height: 1;
        text-shadow: 0 4px 24px rgba(0,0,0,0.2);
        transition: color 0.1s, text-shadow 0.1s;
        margin-bottom: 1rem;
    }
    .feedback-correct { color: #bbf7d0; text-shadow: 0 0 40px rgba(187,247,208,0.5); }
    .feedback-wrong   { color: #fecaca; text-shadow: 0 0 40px rgba(254,202,202,0.5); }

    .rule-hint {
        font-size: 1.1rem;
        color: rgba(255,255,255,0.75);
        margin-bottom: 3rem;
        font-weight: 500;
    }
    .hint-label {
        display: inline-block;
        font-weight: 800;
        padding: 0.1rem 0.6rem;
        border-radius: 6px;
        font-size: 1rem;
    }
    .blue-hint { background: rgba(255,255,255,0.2); color: white; }
    .red-hint  { background: rgba(255,255,255,0.2); color: white; }

    /* Response buttons */
    .response-buttons {
        display: flex;
        gap: 1.5rem;
        flex-wrap: wrap;
        justify-content: center;
    }

    .resp-btn {
        padding: 1.25rem 3rem;
        border: 3px solid rgba(255,255,255,0.5);
        border-radius: 14px;
        background: rgba(255,255,255,0.15);
        color: white;
        font-size: 1.25rem;
        font-weight: 800;
        cursor: pointer;
        min-width: 160px;
        transition: background 0.15s, transform 0.1s, border-color 0.15s;
    }
    .resp-btn:hover {
        background: rgba(255,255,255,0.3);
        border-color: white;
        transform: translateY(-3px);
    }
    .resp-btn:active { transform: translateY(0); background: rgba(255,255,255,0.4); }

    /* ============================================================
       RESULTS
    ============================================================ */
    .training-banner {
        background: linear-gradient(135deg, #0e7490 0%, #164e63 100%);
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
        background: linear-gradient(135deg, #0e7490 0%, #164e63 100%);
        padding: 2rem;
        text-align: center;
        color: white;
    }
    .score-big   { font-size: 4rem; font-weight: 900; line-height: 1; margin-bottom: 0.35rem; }
    .score-label { font-size: 0.9rem; opacity: 0.85; font-weight: 500; }

    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        border-bottom: 1px solid #f1f5f9;
    }
    .metric-cell {
        padding: 1.25rem; text-align: center;
        border-right: 1px solid #f1f5f9;
        border-bottom: 1px solid #f1f5f9;
    }
    .metric-cell:nth-child(3n) { border-right: none; }

    .metric-value { font-size: 1.6rem; font-weight: 800; color: #1e293b; }
    .metric-label { font-size: 0.78rem; color: #6b7280; font-weight: 500; margin-top: 0.25rem; }
    .metric-good .metric-value { color: #16a34a; }
    .metric-warn .metric-value { color: #d97706; }

    .interp-card {
        padding: 1.5rem 1.75rem;
        border-bottom: 1px solid #f1f5f9;
    }
    .interp-title { font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #0e7490; margin-bottom: 0.5rem; }
    .interp-card p { color: #374151; line-height: 1.6; margin: 0 0 0.5rem; font-size: 0.95rem; }
    .persev-note { color: #b45309; font-size: 0.9rem; }

    .start-button {
        display: block;
        width: calc(100% - 3.5rem);
        margin: 1.75rem;
        background: linear-gradient(135deg, #0e7490 0%, #164e63 100%);
        color: white;
        border: none;
        padding: 1rem;
        border-radius: 12px;
        font-size: 1rem; font-weight: 700;
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .start-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(14, 116, 144, 0.4);
    }

    /* Responsive */
    @media (max-width: 600px) {
        .flex-container { padding: 1rem; }
        .task-title     { font-size: 1.4rem; }
        .number-display { font-size: 7rem; }
        .resp-btn       { padding: 1rem 2rem; min-width: 130px; font-size: 1.1rem; }
        .score-big      { font-size: 3rem; }
        .metrics-grid   { grid-template-columns: repeat(2, 1fr); }
        .metrics-grid .metric-cell:nth-child(3n)  { border-right: 1px solid #f1f5f9; }
        .metrics-grid .metric-cell:nth-child(2n)  { border-right: none; }
        .start-button   { width: calc(100% - 2.5rem); margin: 1.25rem; }
    }
</style>




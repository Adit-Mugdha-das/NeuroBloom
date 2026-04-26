<script>
    import { goto } from '$app/navigation';
    import { page } from '$app/stores';
    import { tasks, training } from '$lib/api';
    import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
    import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
import TaskReturnButton from '$lib/components/TaskReturnButton.svelte';
    import { formatNumber, locale, localeText } from '$lib/i18n';
    import { user } from '$lib/stores';
    import { getPracticeCopy } from '$lib/task-practice';
import { TASK_RETURN_CONTEXT } from '$lib/task-navigation';
    import { onMount } from 'svelte';

    let stage = 'intro'; // intro | test | results

    let currentTrial = 0;
    let totalTrials = 60;

    let isTrainingMode = false;
    let trainingPlanId = null;
    let trainingDifficulty = 1;
    let taskId = null;
    let sessionComplete = false;
    let completedTasksCount = 0;
    let totalTasksCount = 4;

    let letters = [];
    let currentLetter = '';
    let previousLetter = '';
    let responses = [];
    let reactionTimes = [];

    let targetsShown = 0;
    let targetsHit = 0;
    let misses = 0;
    let falseAlarms = 0;
    let accuracy = 0;
    let meanRT = 0;
    let isPracticeMode = false;
    let practiceStatusMessage = '';
    let recordedTotalTrials = 60;

    // Alert-on-target indicator (replaces the ⚠️ inline style)
    let alertActive = false;

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
        if (isTrainingMode && trainingDifficulty > 3) {
            totalTrials = 60 + (trainingDifficulty - 3) * 10;
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
        responses = []; reactionTimes = [];
        targetsShown = targetsHit = misses = falseAlarms = 0;
        accuracy = meanRT = 0;
        alertActive = false;
        stage = 'test';
        generateSequence();
        showNextTrial();
    }

    function finishPractice(completed = false) {
        clearTimeout(timeout);
        isPracticeMode = false;
        stage = 'intro';
        currentTrial = 0;
        currentLetter = ''; previousLetter = '';
        responses = []; reactionTimes = [];
        totalTrials = recordedTotalTrials;
        alertActive = false;
        practiceStatusMessage = completed ? getPracticeCopy($locale).complete : '';
    }

    function leavePractice() {
        finishPractice(false);
    }

    function generateSequence() {
        const letterPool = ['A','B','C','D','E','F','G','H','K','L','M','N','P','R','S','T','X'];
        letters = [];
        for (let i = 0; i < totalTrials; i++) {
            if (i > 0 && letters[i - 1] === 'A' && Math.random() < 0.7) {
                letters.push('X');
            } else if (Math.random() < 0.15) {
                letters.push('A');
            } else {
                const others = letterPool.filter((l) => l !== 'A' && l !== 'X');
                letters.push(others[Math.floor(Math.random() * others.length)]);
            }
        }
    }

    let trialStartTime = 0;
    let timeout;

    function showNextTrial() {
        if (currentTrial >= totalTrials) { calculateResults(); return; }
        previousLetter = currentTrial > 0 ? letters[currentTrial - 1] : '';
        currentLetter  = letters[currentTrial];
        alertActive    = previousLetter === 'A';
        trialStartTime = Date.now();
        timeout = setTimeout(() => {
            if (responses.length === currentTrial) {
                responses.push(false);
                reactionTimes.push(1000);
            }
            currentTrial++;
            showNextTrial();
        }, 1000);
    }

    function handleClick() {
        if (responses.length > currentTrial) return;
        clearTimeout(timeout);
        const rt = Date.now() - trialStartTime;
        responses.push(true);
        reactionTimes.push(rt);
        currentTrial++;
        showNextTrial();
    }

    function calculateResults() {
        targetsShown = targetsHit = misses = falseAlarms = 0;
        for (let i = 0; i < totalTrials; i++) {
            const isTarget = i > 0 && letters[i - 1] === 'A' && letters[i] === 'X';
            const clicked  = responses[i];
            if (isTarget) { targetsShown++; clicked ? targetsHit++ : misses++; }
            else if (clicked) falseAlarms++;
        }
        accuracy = targetsShown > 0 ? (targetsHit / targetsShown) * 100 : 0;
        const validRTs = reactionTimes.filter((rt, i) => {
            const isTarget = i > 0 && letters[i - 1] === 'A' && letters[i] === 'X';
            return isTarget && rt < 1000;
        });
        meanRT = validRTs.length > 0 ? validRTs.reduce((a, b) => a + b, 0) / validRTs.length : 0;
        if (isPracticeMode) { finishPractice(true); return; }
        stage = 'results';
        saveResults();
    }

    async function saveResults() {
        try {
            const rtStd = calculateStd(reactionTimes.filter((rt) => rt < 1000));
            const firstHalf = responses.slice(0, totalTrials / 2).filter((r) => r).length;
            const secondHalf = responses.slice(totalTrials / 2).filter((r) => r).length;
            const vigilanceDecrement = firstHalf > 0 ? (firstHalf - secondHalf) / firstHalf : 0;

            if (isTrainingMode && trainingPlanId) {
                const result = await training.submitSession({
                    user_id: $user.id,
                    training_plan_id: trainingPlanId,
                    domain: 'attention',
                    task_type: 'continuous_performance',
                    score: accuracy,
                    accuracy,
                    average_reaction_time: meanRT,
                    consistency: rtStd > 0 ? Math.max(0, 100 - rtStd) : 100,
                    errors: misses + falseAlarms,
                    session_duration: totalTrials / 60,
                    task_id: taskId
                });
                sessionComplete       = result.session_complete;
                completedTasksCount   = result.completed_tasks;
                totalTasksCount       = result.total_tasks;
            } else {
                await tasks.submitResult(
                    $user.id,
                    'attention',
                    accuracy,
                    JSON.stringify({
                        targets_shown: targetsShown, targets_hit: targetsHit,
                        misses, false_alarms: falseAlarms,
                        mean_rt: meanRT, rt_std: rtStd,
                        vigilance_decrement: vigilanceDecrement,
                        total_trials: totalTrials
                    })
                );
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

    function performanceLabel() {
        if (accuracy >= 80) return lt('Excellent sustained attention.', 'চমৎকার স্থায়ী মনোযোগ।');
        if (accuracy >= 60) return lt('Good performance. Continue practicing to improve consistency.', 'ভালো পারফরম্যান্স। ধারাবাহিকতা বাড়াতে অনুশীলন চালিয়ে যান।');
        return lt('Keep practicing. Sustained attention improves with regular training.', 'অনুশীলন চালিয়ে যান। নিয়মিত চর্চায় স্থায়ী মনোযোগ উন্নত হয়।');
    }
</script>

<svelte:head>
    <title>{lt('Attention Test - NeuroBloom', 'মনোযোগ পরীক্ষা - NeuroBloom')}</title>
</svelte:head>

<div class="cpt-container" data-localize-skip>

    <!-- INTRO -->
    {#if stage === 'intro'}
        <div class="intro-wrapper">
            <TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.BASELINE} />
            <div class="task-header">                <h1 class="task-title">{lt('Continuous Performance Test', 'কন্টিনিউয়াস পারফরম্যান্স টেস্ট')}</h1>
            </div>

            <div class="concept-card">
                <div class="concept-badge">Attention · Baseline Assessment</div>
                <h2>What This Test Measures</h2>
                <p>The CPT measures <strong>sustained attention</strong> — your ability to stay vigilant and respond selectively over an extended period. You will watch a rapid stream of letters and respond only to a specific two-letter sequence. The test distinguishes genuine target detections from impulsive false alarms and tracks whether attention declines over time.</p>
            </div>

            <div class="rules-card">
                <h3>AX Rule</h3>
                <div class="ax-example">
                    <div class="ax-slot ax-other">B</div>
                    <div class="ax-arrow">→</div>
                    <div class="ax-slot ax-a">A</div>
                    <div class="ax-arrow">→</div>
                    <div class="ax-slot ax-x">X</div>
                    <div class="ax-respond">Click here</div>
                </div>
                <ul class="rules-list">
                    <li>Letters appear <strong>one per second</strong> — stay alert</li>
                    <li>Click <strong>only when X follows A</strong> (the A→X sequence)</li>
                    <li>Do NOT click for X alone, A alone, or any other letter</li>
                    <li>False clicks count as errors — accuracy matters as much as speed</li>
                    <li>~{totalTrials} trials · approximately 1 minute</li>
                </ul>
            </div>

            <div class="examples-grid">
                <div class="example-card ex-correct">
                    <div class="ex-tag">Click</div>
                    <div class="ex-seq"><span class="ex-a">A</span> → <span class="ex-x">X</span></div>
                    <div class="ex-note">A immediately before X</div>
                </div>
                <div class="example-card ex-wrong">
                    <div class="ex-tag">Do NOT click</div>
                    <div class="ex-seq"><span class="ex-a">A</span> → <span class="ex-b">B</span> → <span class="ex-x">X</span></div>
                    <div class="ex-note">A was not the one right before X</div>
                </div>
                <div class="example-card ex-wrong">
                    <div class="ex-tag">Do NOT click</div>
                    <div class="ex-seq"><span class="ex-b">B</span> → <span class="ex-x">X</span></div>
                    <div class="ex-note">Preceding letter was not A</div>
                </div>
            </div>

            <div class="tip-card">
                <div class="tip-title">Strategy</div>
                <p>Focus on remembering the previous letter, not the current one. When you see any letter, your job is to decide: "was the last letter A?" If yes, wait for the next letter — if it is X, click. Avoid the temptation to click whenever you see X.</p>
            </div>

            <div class="clinical-card">
                <h3>Clinical Basis</h3>
                <p>Sustained attention deficits affect over 50% of people with MS, even in early stages. The CPT (AX variant) is sensitive to fronto-parietal white matter disruption. Two key metrics — hit rate and false alarm rate — can be combined into a d' (d-prime) sensitivity index, which is used in the Brief International Cognitive Assessment for MS (BICAMS) and other MS-specific batteries. Vigilance decrement (performance drop in the second half) reflects fatigue-driven attention failure, a distinctive feature of MS cognitive impairment.</p>
            </div>

            <TaskPracticeActions
                locale={$locale}
                startLabel={localeText({ en: 'Start Actual Test', bn: 'আসল পরীক্ষা শুরু করুন' }, $locale)}
                statusMessage={practiceStatusMessage}
                on:start={() => startTest(false)}
                on:practice={() => startTest(true)}
            />
        </div>

    <!-- TEST PHASE -->
    {:else if stage === 'test'}
        <div class="test-arena">
            {#if isPracticeMode}
                <div class="practice-wrap">
                    <PracticeModeBanner locale={$locale} showExit on:exit={leavePractice} />
                </div>
            {/if}

            <div class="arena-header">
                <div class="trial-pill">Trial {currentTrial + 1} / {totalTrials}</div>
                {#if alertActive}
                    <div class="alert-pill">Previous was A — ready!</div>
                {/if}
            </div>

            <div class="letter-stage" class:stage-alert={alertActive}>
                <div class="current-letter" class:letter-x={currentLetter === 'X' && alertActive}>
                    {currentLetter}
                </div>
                <div class="prev-label">Previous: <strong>{previousLetter || '—'}</strong></div>
            </div>

            <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
            <div class="respond-zone" on:click={handleClick} role="button" tabindex="0"
                 on:keydown={(e) => (e.key === ' ' || e.key === 'Enter') && handleClick()}>
                <div class="respond-inner">
                    <div class="respond-icon" class:icon-alert={alertActive}>
                        <span>TAP / CLICK</span>
                        <span class="respond-subtext">when you see X after A</span>
                    </div>
                </div>
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
                    <div class="score-label">{lt('Hit Rate (Sustained Attention Score)', 'হিট রেট (স্থায়ী মনোযোগ স্কোর)')}</div>
                </div>

                <div class="metrics-grid">
                    <div class="metric-cell">
                        <div class="metric-value">{targetsShown}</div>
                        <div class="metric-label">{lt('Targets (AX)', 'টার্গেট (AX)')}</div>
                    </div>
                    <div class="metric-cell metric-good">
                        <div class="metric-value">{targetsHit}</div>
                        <div class="metric-label">{lt('Hits', 'সঠিক ধরন')}</div>
                    </div>
                    <div class="metric-cell metric-warn">
                        <div class="metric-value">{misses}</div>
                        <div class="metric-label">{lt('Misses', 'মিস')}</div>
                    </div>
                    <div class="metric-cell metric-warn">
                        <div class="metric-value">{falseAlarms}</div>
                        <div class="metric-label">{lt('False Alarms', 'ভুল সংকেত')}</div>
                    </div>
                    <div class="metric-cell">
                        <div class="metric-value">{meanRT.toFixed(0)}ms</div>
                        <div class="metric-label">{lt('Avg. Reaction Time', 'গড় প্রতিক্রিয়া সময়')}</div>
                    </div>
                    <div class="metric-cell">
                        <div class="metric-value">{totalTrials}</div>
                        <div class="metric-label">{lt('Total Trials', 'মোট ট্রায়াল')}</div>
                    </div>
                </div>

                <div class="interp-card">
                    <div class="interp-title">{lt('Interpretation', 'ব্যাখ্যা')}</div>
                    <p>{performanceLabel()}</p>
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
    .cpt-container {
        min-height: 100vh;
        background: #C8DEFA;
        padding: 2rem;
        font-family: inherit;
    }

    /* Page layout wrapper */
    .page-content {
        max-width: 900px;
        margin: 0 auto;
        display: flex;
        flex-direction: column;
        gap: 1.25rem;
    }

    /* Intro / Results unified card */
    .intro-wrapper {
        max-width: 900px;
        margin: 0 auto;
        background: white;
        border-radius: 16px;
        padding: 2.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07), 0 1px 3px rgba(0, 0, 0, 0.06);
        display: flex;
        flex-direction: column;
        gap: 1.8rem;
    }

    .intro-wrapper > .concept-card,
    .intro-wrapper > .rules-card,
    .intro-wrapper > .tip-card,
    .intro-wrapper > .clinical-card,
    .intro-wrapper > .results-card {
        box-shadow: none;
        border-radius: 12px;
    }

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
        color: #164e63;
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
        background: #cffafe;
        color: #0e7490;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        padding: 0.3rem 0.9rem;
        border-radius: 20px;
        margin-bottom: 0.75rem;
    }
    .concept-card h2 { font-size: 1.4rem; font-weight: 700; color: #164e63; margin: 0 0 0.75rem; }
    .concept-card p  { color: #374151; line-height: 1.65; margin: 0; }

    /* Rules card */
    .rules-card {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
    }
    .rules-card h3 {
        font-size: 1.1rem; font-weight: 700; color: #164e63;
        margin: 0 0 1.25rem;
    }

    /* AX visual example */
    .ax-example {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1.25rem;
        flex-wrap: wrap;
    }
    .ax-slot {
        width: 56px; height: 56px;
        border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.8rem; font-weight: 900; font-family: monospace;
    }
    .ax-other { background: #f1f5f9; color: #64748b; }
    .ax-a     { background: #fef3c7; color: #b45309; }
    .ax-x     { background: #dcfce7; color: #15803d; }
    .ax-arrow { color: #9ca3af; font-size: 1.25rem; font-weight: 300; }
    .ax-respond {
        background: #0e7490;
        color: white;
        font-size: 0.8rem;
        font-weight: 700;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        margin-left: 0.5rem;
    }

    .rules-list {
        margin: 0; padding-left: 1.25rem;
        display: flex; flex-direction: column; gap: 0.45rem;
    }
    .rules-list li { color: #374151; font-size: 0.9rem; line-height: 1.5; }

    /* Examples grid */
    .examples-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
    }
    .example-card {
        background: white;
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        text-align: center;
    }
    .ex-correct { border-top: 4px solid #16a34a; }
    .ex-wrong   { border-top: 4px solid #dc2626; }

    .ex-tag {
        font-size: 0.75rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.5px; margin-bottom: 0.6rem;
    }
    .ex-correct .ex-tag { color: #16a34a; }
    .ex-wrong   .ex-tag { color: #dc2626; }

    .ex-seq {
        font-size: 1.4rem; font-weight: 900; font-family: monospace;
        margin: 0.5rem 0; color: #1e293b;
    }
    .ex-a { color: #b45309; }
    .ex-x { color: #15803d; }
    .ex-b { color: #475569; }

    .ex-note { font-size: 0.8rem; color: #6b7280; }

    /* Tip card */
    .tip-card {
        background: #fffbeb;
        border: 1px solid #fde68a;
        border-radius: 16px;
        padding: 1.5rem 2rem;
    }
    .tip-title {
        font-size: 0.8rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.5px; color: #b45309; margin-bottom: 0.5rem;
    }
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
       TEST ARENA
    ============================================================ */
    .test-arena {
        max-width: 680px;
        margin: 0 auto;
        width: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 2rem;
        background: rgba(255, 255, 255, 0.92);
        border: 1px solid rgba(118, 145, 163, 0.18);
        border-radius: 26px;
        box-shadow: 0 24px 60px rgba(19, 52, 74, 0.1);
        position: relative;
    }

    .practice-wrap {
        position: absolute;
        top: 1rem;
        left: 50%;
        transform: translateX(-50%);
        width: 100%;
        max-width: 600px;
        padding: 0 1rem;
    }

    .arena-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 3rem;
        flex-wrap: wrap;
        justify-content: center;
    }

    .trial-pill {
        background: rgba(14, 116, 144, 0.1);
        color: #0e7490;
        font-size: 0.85rem; font-weight: 600;
        padding: 0.35rem 1rem;
        border-radius: 20px;
    }

    .alert-pill {
        background: #fef3c7;
        color: #92400e;
        font-size: 0.85rem; font-weight: 700;
        padding: 0.35rem 1rem;
        border-radius: 20px;
        animation: pulse-in 0.15s ease-out;
    }
    @keyframes pulse-in {
        from { transform: scale(0.9); opacity: 0; }
        to   { transform: scale(1);   opacity: 1; }
    }

    /* Letter display */
    .letter-stage {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1rem;
        margin-bottom: 3rem;
    }

    .current-letter {
        font-size: 9rem;
        font-weight: 900;
        font-family: 'Courier New', monospace;
        color: #1e293b;
        line-height: 1;
        text-shadow: none;
        transition: color 0.1s ease;
        letter-spacing: -2px;
    }
    .letter-x { color: #16a34a; text-shadow: 0 0 20px rgba(22, 163, 74, 0.3); }

    .stage-alert .current-letter { color: #d97706; text-shadow: none; }
    .stage-alert .letter-x       { color: #16a34a; text-shadow: 0 0 20px rgba(22, 163, 74, 0.4); }

    .prev-label {
        font-size: 0.9rem;
        color: #64748b;
    }
    .prev-label strong { color: #1e293b; }

    /* Response zone */
    .respond-zone {
        width: 100%;
        max-width: 480px;
        cursor: pointer;
    }
    .respond-inner {
        background: rgba(14, 116, 144, 0.06);
        border: 2px solid rgba(14, 116, 144, 0.2);
        border-radius: 20px;
        padding: 2.5rem;
        text-align: center;
        transition: background 0.15s, border-color 0.15s;
    }
    .respond-zone:hover .respond-inner {
        background: rgba(14, 116, 144, 0.1);
        border-color: rgba(14, 116, 144, 0.4);
    }
    .respond-zone:active .respond-inner {
        background: rgba(14, 116, 144, 0.25);
        border-color: #0e7490;
    }

    .respond-icon {
        display: flex; flex-direction: column; align-items: center; gap: 0.35rem;
        color: #64748b;
        font-size: 1.1rem; font-weight: 700;
        letter-spacing: 2px; text-transform: uppercase;
        transition: color 0.15s;
    }
    .respond-icon.icon-alert { color: #d97706; }
    .respond-subtext { font-size: 0.75rem; font-weight: 400; letter-spacing: 0; text-transform: none; opacity: 0.7; }

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
        gap: 0;
        border-bottom: 1px solid #f1f5f9;
    }

    .metric-cell {
        padding: 1.25rem;
        text-align: center;
        border-right: 1px solid #f1f5f9;
        border-bottom: 1px solid #f1f5f9;
    }
    .metric-cell:nth-child(3n) { border-right: none; }

    .metric-value { font-size: 1.75rem; font-weight: 800; color: #1e293b; }
    .metric-label { font-size: 0.78rem; color: #6b7280; font-weight: 500; margin-top: 0.25rem; }

    .metric-good .metric-value { color: #16a34a; }
    .metric-warn .metric-value { color: #d97706; }

    .interp-card {
        padding: 1.5rem 1.75rem;
        border-bottom: 1px solid #f1f5f9;
    }
    .interp-title {
        font-size: 0.8rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.5px; color: #0e7490; margin-bottom: 0.5rem;
    }
    .interp-card p { color: #374151; line-height: 1.6; margin: 0; font-size: 0.95rem; }

    .start-button {
        display: block;
        width: calc(100% - 3.5rem);
        margin: 1.75rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }

    /* Responsive */
    @media (max-width: 600px) {
        .cpt-container { padding: 1rem; }
        .task-title    { font-size: 1.4rem; }
        .current-letter { font-size: 6rem; }
        .score-big     { font-size: 3rem; }
        .metrics-grid  { grid-template-columns: repeat(2, 1fr); }
        .metrics-grid .metric-cell:nth-child(3n)  { border-right: 1px solid #f1f5f9; }
        .metrics-grid .metric-cell:nth-child(2n)  { border-right: none; }
        .start-button  { width: calc(100% - 2.5rem); margin: 1.25rem; }
    }
</style>




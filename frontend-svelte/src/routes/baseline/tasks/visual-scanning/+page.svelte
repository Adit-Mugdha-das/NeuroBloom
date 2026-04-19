<script>
    import { goto } from '$app/navigation';
    import { page } from '$app/stores';
    import { tasks, training } from '$lib/api';
    import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
    import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
import TaskReturnButton from '$lib/components/TaskReturnButton.svelte';
    import { formatNumber, locale, localeText, translateText } from '$lib/i18n';
    import { user } from '$lib/stores';
    import { getPracticeCopy } from '$lib/task-practice';
import { TASK_RETURN_CONTEXT } from '$lib/task-navigation';
    import { onDestroy, onMount } from 'svelte';

    let stage = 'intro'; // intro | test | results

    let isTrainingMode = false;
    let trainingPlanId = null;
    let trainingDifficulty = 1;
    let taskId = null;
    let sessionComplete = false;
    let completedTasksCount = 0;
    let totalTasksCount = 4;

    let gridSize = 10;
    let totalTargets = 5;
    let grid = [];
    let foundTargets = [];
    let startTime = 0;
    let endTime = 0;
    let searchTime = 0;
    let liveElapsedTime = 0;
    let timerInterval = null;
    let isPracticeMode = false;
    let practiceStatusMessage = '';
    let recordedGridSize = 10;
    let recordedTargets = 5;

    // Flash wrong click
    let wrongFlash = false;
    let wrongTimer = null;

    const LETTER_SETS = {
        en: { target: 'T', distractors: ['L','I','F','E','P'], distractorPreview: 'L  I  F  E  P' },
        bn: { target: 'ট', distractors: ['ড','ঠ','ণ','ল','ফ'], distractorPreview: 'ড  ঠ  ণ  ল  ফ' }
    };

    function t(text)        { return translateText(text ?? '', $locale); }
    function lt(en, bn)     { return localeText({ en, bn }, $locale); }
    function n(value, opts) { return formatNumber(value, $locale, opts || {}); }
    function activeLetterSet() { return $locale === 'bn' ? LETTER_SETS.bn : LETTER_SETS.en; }

    function startLiveTimer() {
        if (timerInterval) clearInterval(timerInterval);
        timerInterval = setInterval(() => { liveElapsedTime = Date.now() - startTime; }, 100);
    }
    function stopLiveTimer() {
        if (timerInterval) { clearInterval(timerInterval); timerInterval = null; }
    }

    function trainingProgressText() {
        return lt(
            `Training Progress: ${completedTasksCount} / ${totalTasksCount} tasks completed`,
            `ট্রেনিং অগ্রগতি: ${n(completedTasksCount)} / ${n(totalTasksCount)}টি টাস্ক সম্পন্ন`
        );
    }

    function elapsedSecondsText(valueMs = liveElapsedTime) {
        return `${n((valueMs / 1000).toFixed(1), { minimumFractionDigits: 1, maximumFractionDigits: 1 })}${lt('s','সে')}`;
    }

    onMount(() => {
        if (!$user) return goto('/login');
        const urlParams = new URLSearchParams(window.location.search);
        isTrainingMode     = urlParams.get('training') === 'true';
        trainingPlanId     = parseInt(urlParams.get('planId')) || null;
        trainingDifficulty = parseInt(urlParams.get('difficulty')) || 1;
        taskId             = $page.url.searchParams.get('taskId');

        if (isTrainingMode && trainingDifficulty > 3) {
            gridSize     = 10 + (trainingDifficulty - 3);
            totalTargets = 5 + Math.floor((trainingDifficulty - 3) / 2);
        }
        recordedGridSize = gridSize;
        recordedTargets  = totalTargets;
    });

    function backToDashboard() { goto('/dashboard'); }

    function startTest(practice = false) {
        isPracticeMode       = practice;
        practiceStatusMessage = '';
        gridSize     = practice ? 6 : recordedGridSize;
        totalTargets = practice ? 3 : recordedTargets;
        stage        = 'test';
        foundTargets = [];
        searchTime   = 0;
        endTime      = 0;
        wrongFlash   = false;
        generateGrid();
        startTime      = Date.now();
        liveElapsedTime = 0;
        startLiveTimer();
    }

    function finishPractice(completed = false) {
        stopLiveTimer();
        if (wrongTimer) {
            clearTimeout(wrongTimer);
            wrongTimer = null;
        }
        isPracticeMode        = false;
        stage                 = 'intro';
        foundTargets          = [];
        grid                  = [];
        gridSize              = recordedGridSize;
        totalTargets          = recordedTargets;
        searchTime            = 0;
        liveElapsedTime       = 0;
        wrongFlash            = false;
        practiceStatusMessage = completed ? getPracticeCopy($locale).complete : '';
    }

    function leavePractice() {
        finishPractice(false);
    }

    function generateGrid() {
        grid = [];
        const { distractors, target } = activeLetterSet();
        const positions = [];
        for (let i = 0; i < gridSize * gridSize; i++) {
            grid.push({ letter: distractors[Math.floor(Math.random() * distractors.length)], isTarget: false, found: false });
            positions.push(i);
        }
        for (let i = 0; i < totalTargets; i++) {
            const ri  = Math.floor(Math.random() * positions.length);
            const pos = positions.splice(ri, 1)[0];
            grid[pos] = { letter: target, isTarget: true, found: false };
        }
    }

    function handleCellClick(index) {
        const cell = grid[index];
        if (cell.isTarget && !cell.found) {
            grid[index] = { ...cell, found: true };
            grid = [...grid];
            foundTargets = [...foundTargets, index];
            if (foundTargets.length === totalTargets) {
                endTime    = Date.now();
                searchTime = endTime - startTime;
                stopLiveTimer();
                calculateResults();
            }
        } else if (!cell.isTarget) {
            // Wrong click — flash
            if (wrongTimer) clearTimeout(wrongTimer);
            wrongFlash = true;
            wrongTimer = setTimeout(() => { wrongFlash = false; }, 500);
        }
    }

    function calculateResults() {
        if (isPracticeMode) { finishPractice(true); return; }
        stage = 'results';
        saveResults();
    }

    async function saveResults() {
        try {
            const timePerTarget  = searchTime / foundTargets.length;
            const accuracy       = (foundTargets.length / totalTargets) * 100;
            const scanEfficiency = (totalTargets / (searchTime / 1000)) * 10;

            if (isTrainingMode && trainingPlanId) {
                const result = await training.submitSession({
                    user_id: $user.id, training_plan_id: trainingPlanId,
                    domain: 'visual_scanning', task_type: 'target_search',
                    score: accuracy, accuracy,
                    average_reaction_time: timePerTarget,
                    consistency: Math.max(0, 100 - (timePerTarget / 100)),
                    errors: totalTargets - foundTargets.length,
                    session_duration: Math.round(searchTime / 60000),
                    task_id: taskId
                });
                sessionComplete     = result.session_complete;
                completedTasksCount = result.completed_tasks;
                totalTasksCount     = result.total_tasks;
            } else {
                await tasks.submitResult(
                    $user.id, 'visual_scanning', accuracy,
                    JSON.stringify({
                        targets_total: totalTargets, targets_found: foundTargets.length,
                        missed_targets: totalTargets - foundTargets.length,
                        search_time_ms: searchTime, time_per_target: timePerTarget,
                        scan_efficiency: scanEfficiency
                    })
                );
            }
        } catch (err) { console.error('Error saving results:', err); }
    }

    onDestroy(() => { stopLiveTimer(); });
</script>

<svelte:head>
    <title>{lt('Visual Scanning Test - NeuroBloom','ভিজ্যুয়াল স্ক্যানিং টেস্ট - NeuroBloom')}</title>
</svelte:head>

<div class="vs-container" data-localize-skip>

    <!-- INTRO -->
    {#if stage === 'intro'}
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.BASELINE} />
        <div class="page-content">

            <div class="task-header">                <h1 class="task-title">Visual Search</h1>
            </div>

            <div class="concept-card">
                <div class="concept-badge">Visual Scanning · Baseline Assessment</div>
                <h2>What This Test Measures</h2>
                <p>Visual Search measures your ability to locate target stimuli within a field of visually similar distractors. It reflects the speed and efficiency of your <strong>attentional spotlight</strong> — how quickly your visual system can scan a scene, suppress irrelevant items, and lock onto the target. The primary metric is <em>scan efficiency</em>: targets identified per unit of time.</p>
            </div>

            <div class="rules-card">
                <h3>How It Works</h3>
                <ul class="rules-list">
                    <li>A <strong>{gridSize * gridSize}</strong> grid of letters will appear — all distractors except <strong>{totalTargets} hidden targets</strong></li>
                    <li>Your job: find and click every target letter as fast as possible</li>
                    <li>The timer starts the moment the grid appears</li>
                    <li>The task ends automatically when all targets are found</li>
                </ul>

                <!-- Target preview -->
                <div class="preview-row">
                    <div class="preview-box preview-target">
                        <div class="preview-letter">{activeLetterSet().target}</div>
                        <div class="preview-caption">FIND THIS</div>
                    </div>
                    <div class="preview-divider">vs</div>
                    <div class="preview-box preview-distractor">
                        <div class="preview-letters-small">{activeLetterSet().distractorPreview}</div>
                        <div class="preview-caption">IGNORE THESE</div>
                    </div>
                </div>
            </div>

            <div class="tip-card">
                <div class="tip-title">Strategy</div>
                <p>Resist the urge to scan randomly. A systematic approach — row by row or column by column — is significantly faster than jumping around the grid. Once you identify the shape of the target letter (e.g., "T" has a distinctive horizontal crossbar), your visual cortex can filter distractors more efficiently through <em>feature search</em>.</p>
            </div>

            <div class="clinical-card">
                <h3>Clinical Basis</h3>
                <p>Visual scanning deficits are among the most common cognitive complaints in MS, with roughly 40–50% of patients showing slowed visual search times even in early relapsing-remitting disease. The task is sensitive to posterior cortical and white matter changes affecting the dorsal visual stream (occipitoparietal). Slowed scan speed often co-occurs with processing speed deficits, but is partially dissociable — some patients show normal simple reaction times yet significantly impaired visual search, pointing to difficulties with spatial attention rather than motor speed.</p>
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
        <div class="page-content">

            {#if isPracticeMode}
                <PracticeModeBanner locale={$locale} showExit on:exit={leavePractice} />
            {/if}

            <div class="test-topbar">
                <div class="stat-pill">
                    <span class="pill-label">Found</span>
                    <span class="pill-value">{foundTargets.length} / {totalTargets}</span>
                </div>
                <div class="progress-track">
                    <div class="progress-fill" style="width: {(foundTargets.length / totalTargets) * 100}%"></div>
                </div>
                <div class="stat-pill">
                    <span class="pill-label">Time</span>
                    <span class="pill-value">{elapsedSecondsText()}</span>
                </div>
            </div>

            {#if wrongFlash}
                <div class="wrong-banner">That's a distractor — keep searching for <strong>{activeLetterSet().target}</strong></div>
            {/if}

            <div class="board-card">
                <div
                    class="search-grid"
                    style="grid-template-columns: repeat({gridSize}, 1fr);"
                >
                    {#each grid as cell, index}
                        <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
                        <div
                            class="grid-cell"
                            class:cell-found={cell.found}
                            class:cell-target={cell.isTarget && !cell.found}
                            on:click={() => handleCellClick(index)}
                            role="button"
                            tabindex="0"
                            on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && handleCellClick(index)}
                        >
                            {#if cell.found}
                                <svg viewBox="0 0 20 20" fill="currentColor" class="check-icon">
                                    <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                                </svg>
                            {:else}
                                {cell.letter}
                            {/if}
                        </div>
                    {/each}
                </div>
            </div>

            <div class="board-hint">
                Click every <strong>{activeLetterSet().target}</strong> — ignore {activeLetterSet().distractorPreview}
            </div>
        </div>

    <!-- RESULTS -->
    {:else if stage === 'results'}
		<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.BASELINE} />
        <div class="page-content">

            <div class="task-header">                <h1 class="task-title">Results</h1>
            </div>

            {#if isTrainingMode}
                <div class="training-banner {sessionComplete ? 'banner-complete' : ''}">
                    {#if sessionComplete}
                        <strong>Session Complete — all {totalTasksCount} tasks finished.</strong>
                    {:else}
                        <strong>{trainingProgressText()}</strong>
                        <span>Continue with remaining tasks to complete this session.</span>
                    {/if}
                </div>
            {/if}

            <div class="results-card">
                <div class="score-header">
                    <div class="score-big">{n(((foundTargets.length / totalTargets) * 100).toFixed(0))}%</div>
                    <div class="score-label">Detection Accuracy</div>
                </div>

                <div class="metrics-grid">
                    <div class="metric-cell metric-good">
                        <div class="metric-value">{n(foundTargets.length)} / {n(totalTargets)}</div>
                        <div class="metric-label">Targets Found</div>
                    </div>
                    <div class="metric-cell {totalTargets - foundTargets.length === 0 ? 'metric-good' : 'metric-warn'}">
                        <div class="metric-value">{n(totalTargets - foundTargets.length)}</div>
                        <div class="metric-label">Missed</div>
                    </div>
                    <div class="metric-cell">
                        <div class="metric-value">{elapsedSecondsText(searchTime)}</div>
                        <div class="metric-label">Total Time</div>
                    </div>
                    <div class="metric-cell">
                        <div class="metric-value">{n((searchTime / foundTargets.length / 1000).toFixed(2), { minimumFractionDigits: 2, maximumFractionDigits: 2 })}s</div>
                        <div class="metric-label">Time per Target</div>
                    </div>
                    <div class="metric-cell">
                        <div class="metric-value">{n(((totalTargets / (searchTime / 1000)) * 10).toFixed(1), { minimumFractionDigits: 1, maximumFractionDigits: 1 })}</div>
                        <div class="metric-label">Targets / 10s</div>
                    </div>
                    <div class="metric-cell">
                        <div class="metric-value">{n(gridSize)}×{n(gridSize)}</div>
                        <div class="metric-label">Grid Size</div>
                    </div>
                </div>

                <div class="interp-card">
                    <div class="interp-title">Interpretation</div>
                    {#if foundTargets.length === totalTargets && searchTime < 15000}
                        <p>Excellent visual scanning — fast and complete detection. Your attentional spotlight is highly efficient.</p>
                    {:else if foundTargets.length === totalTargets}
                        <p>Good accuracy — all targets found. Practising systematic row-by-row scanning may help improve speed.</p>
                    {:else}
                        <p>{lt('Some targets were missed. Systematic scanning strategies (row by row) improve both speed and completeness.', 'কিছু লক্ষ্য মিস হয়েছে। সারি-সারি স্ক্যান করলে গতি ও নির্ভুলতা বাড়ে।')}</p>
                    {/if}
                    {#if searchTime / foundTargets.length > 3000}
                        <p class="slow-note">Time per target was above 3s — try committing to a fixed scanning path rather than free-roaming the grid.</p>
                    {/if}
                </div>

                <button class="start-button" on:click={backToDashboard}>
                    {t('Back to Dashboard')}
                </button>
            </div>
        </div>
    {/if}
</div>

<style>
    /* Container */
    .vs-container {
        min-height: 100vh;
        background: #C8DEFA;
        padding: 2rem;
        font-family: inherit;
    }

    .page-content {
        max-width: 900px;
        margin: 0 auto;
        display: flex;
        flex-direction: column;
        gap: 1.25rem;
    }

    /* Header */
    .task-header {
        display: flex;
        align-items: center;
        gap: 1.25rem;
        flex-wrap: wrap;
    }

    .task-title { font-size: 1.75rem; font-weight: 700; color: #0c4a6e; margin: 0; }

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
        color: #0369a1;
        font-size: 0.8rem; font-weight: 700;
        letter-spacing: 0.5px; text-transform: uppercase;
        padding: 0.3rem 0.9rem; border-radius: 20px; margin-bottom: 0.75rem;
    }
    .concept-card h2 { font-size: 1.4rem; font-weight: 700; color: #0c4a6e; margin: 0 0 0.75rem; }
    .concept-card p  { color: #374151; line-height: 1.65; margin: 0; }

    /* Rules card */
    .rules-card {
        background: white; border-radius: 16px;
        padding: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.07);
    }
    .rules-card h3 { font-size: 1.1rem; font-weight: 700; color: #0c4a6e; margin: 0 0 1rem; }

    .rules-list {
        margin: 0 0 1.5rem; padding-left: 1.25rem;
        display: flex; flex-direction: column; gap: 0.45rem;
    }
    .rules-list li { color: #374151; font-size: 0.9rem; line-height: 1.5; }

    .preview-row {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1.25rem;
        flex-wrap: wrap;
    }
    .preview-box {
        display: flex; flex-direction: column; align-items: center;
        padding: 1.25rem 2rem; border-radius: 12px; min-width: 120px;
    }
    .preview-target    { background: #dcfce7; border: 2px solid #86efac; }
    .preview-distractor{ background: #f8fafc; border: 2px solid #e2e8f0; }

    .preview-letter {
        font-size: 3.5rem; font-weight: 900; line-height: 1;
        color: #16a34a; font-family: monospace; margin-bottom: 0.4rem;
    }
    .preview-letters-small {
        font-size: 1.25rem; font-weight: 700; font-family: monospace;
        color: #94a3b8; letter-spacing: 4px; margin-bottom: 0.4rem;
    }
    .preview-caption {
        font-size: 0.72rem; font-weight: 700; letter-spacing: 1px;
        text-transform: uppercase; color: #6b7280;
    }
    .preview-divider { font-size: 1rem; font-weight: 700; color: #94a3b8; }

    /* Tip / Clinical */
    .tip-card {
        background: #f0f9ff; border: 1px solid #bae6fd;
        border-radius: 16px; padding: 1.5rem 2rem;
    }
    .tip-title { font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #0369a1; margin-bottom: 0.5rem; }
    .tip-card p { color: #374151; line-height: 1.6; margin: 0; }

    .clinical-card {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border: 1px solid #bae6fd; border-radius: 16px; padding: 1.5rem 2rem;
    }
    .clinical-card h3 { font-size: 1rem; font-weight: 700; color: #0c4a6e; margin: 0 0 0.75rem; }
    .clinical-card p  { color: #0369a1; font-size: 0.95rem; line-height: 1.65; margin: 0; }

    /* ============================================================
       TEST PHASE
    ============================================================ */
    .test-topbar {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .stat-pill {
        background: white;
        border-radius: 20px;
        padding: 0.45rem 1rem;
        display: flex; gap: 0.4rem; align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        white-space: nowrap;
    }
    .pill-label { font-size: 0.75rem; font-weight: 600; color: #6b7280; }
    .pill-value { font-size: 0.9rem; font-weight: 800; color: #0c4a6e; }

    .progress-track {
        flex: 1;
        height: 8px;
        background: #dbeafe;
        border-radius: 4px;
        overflow: hidden;
    }
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #0369a1, #0ea5e9);
        border-radius: 4px;
        transition: width 0.25s ease;
    }

    .wrong-banner {
        background: #fef3c7; color: #92400e;
        border: 1px solid #fde68a;
        border-radius: 10px; padding: 0.65rem 1.25rem;
        font-size: 0.9rem; font-weight: 500;
        animation: fade-slide 0.2s ease-out;
    }
    @keyframes fade-slide {
        from { opacity: 0; transform: translateY(-6px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* Board */
    .board-card {
        background: white; border-radius: 16px;
        padding: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        overflow: auto;
    }

    .search-grid {
        display: grid;
        gap: 4px;
        justify-content: center;
    }

    .grid-cell {
        width: 44px; height: 44px;
        display: flex; align-items: center; justify-content: center;
        background: #f8fafc;
        border: 2px solid #e2e8f0;
        border-radius: 6px;
        font-size: 1.1rem;
        font-weight: 800;
        font-family: monospace;
        color: #374151;
        cursor: pointer;
        transition: background 0.12s, border-color 0.12s, transform 0.1s;
        user-select: none;
        outline: none;
    }
    .grid-cell:hover:not(.cell-found) {
        background: #e0f2fe;
        border-color: #7dd3fc;
        transform: scale(1.08);
    }
    .grid-cell:focus-visible { outline: 3px solid #0369a1; outline-offset: 2px; }

    .cell-found {
        background: #16a34a !important;
        border-color: #15803d !important;
        color: white;
        animation: pop-found 0.25s ease-out;
        cursor: default;
    }
    @keyframes pop-found {
        0%   { transform: scale(0.8); }
        60%  { transform: scale(1.15); }
        100% { transform: scale(1); }
    }

    .check-icon { width: 20px; height: 20px; }

    .board-hint {
        text-align: center; color: #6b7280; font-size: 0.9rem; margin-top: 0.25rem;
    }

    /* ============================================================
       RESULTS
    ============================================================ */
    .training-banner {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; padding: 1.25rem 1.75rem; border-radius: 12px;
        display: flex; flex-direction: column; gap: 0.35rem;
    }
    .training-banner strong { font-size: 1rem; font-weight: 700; }
    .training-banner span   { font-size: 0.875rem; opacity: 0.85; }
    .banner-complete        { background: linear-gradient(135deg, #16a34a, #0f766e); }

    .results-card {
        background: white; border-radius: 16px;
        overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.07);
    }

    .score-header {
        background: linear-gradient(135deg, #0369a1 0%, #0c4a6e 100%);
        padding: 2rem; text-align: center; color: white;
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
    .metric-value  { font-size: 1.5rem; font-weight: 800; color: #1e293b; }
    .metric-label  { font-size: 0.78rem; color: #6b7280; font-weight: 500; margin-top: 0.25rem; }
    .metric-good .metric-value { color: #16a34a; }
    .metric-warn .metric-value { color: #d97706; }

    .interp-card {
        padding: 1.5rem 1.75rem;
        border-bottom: 1px solid #f1f5f9;
    }
    .interp-title { font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #0369a1; margin-bottom: 0.5rem; }
    .interp-card p { color: #374151; line-height: 1.6; margin: 0 0 0.5rem; font-size: 0.95rem; }
    .slow-note { color: #b45309; font-size: 0.9rem; }

    .start-button {
        display: block;
        width: calc(100% - 3.5rem); margin: 1.75rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; border: none; padding: 1rem; border-radius: 12px;
        font-size: 1rem; font-weight: 700; cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .start-button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(102,126,234,0.4); }

    /* Responsive */
    @media (max-width: 640px) {
        .vs-container   { padding: 1rem; }
        .task-title     { font-size: 1.4rem; }
        .grid-cell      { width: 34px; height: 34px; font-size: 0.9rem; }
        .score-big      { font-size: 3rem; }
        .metrics-grid   { grid-template-columns: repeat(2, 1fr); }
        .metrics-grid .metric-cell:nth-child(3n) { border-right: 1px solid #f1f5f9; }
        .metrics-grid .metric-cell:nth-child(2n) { border-right: none; }
        .start-button   { width: calc(100% - 2.5rem); margin: 1.25rem; }
        .preview-box    { padding: 0.9rem 1.25rem; }
    }
</style>




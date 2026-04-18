<script>
    import { goto } from '$app/navigation';
    import { page } from '$app/stores';
    import { formatNumber, locale, localeText, translateText } from '$lib/i18n';
    import PracticeModeBanner from '$lib/components/PracticeModeBanner.svelte';
    import TaskPracticeActions from '$lib/components/TaskPracticeActions.svelte';
    import { tasks, training } from '$lib/api';
    import { user } from '$lib/stores';
    import { getPracticeCopy } from '$lib/task-practice';
    import { onMount } from 'svelte';

    let stage = 'intro'; // intro | test | results

    let isTrainingMode = false;
    let trainingPlanId = null;
    let trainingDifficulty = 1;
    let taskId = null;
    let sessionComplete = false;
    let completedTasksCount = 0;
    let totalTasksCount = 4;

    let diskCount = 3;
    let towers = [];
    let selectedTower = null;
    let moves = 0;
    let optimalMoves = 7;
    let startTime = 0;
    let firstMoveTime = 0;
    let planningTime = 0;
    let completed = false;
    let isPracticeMode = false;
    let practiceStatusMessage = '';
    let recordedDiskCount = 3;

    // Flash invalid move
    let invalidFlash = false;
    let invalidTimer = null;

    function t(text)        { return translateText(text ?? '', $locale); }
    function lt(en, bn)     { return localeText({ en, bn }, $locale); }
    function n(value, opts) { return formatNumber(value, $locale, opts || {}); }

    function initialTowers() {
        return [Array.from({ length: diskCount }, (_, i) => diskCount - i), [], []];
    }

    function refreshTowerState() {
        towers = initialTowers();
        optimalMoves = 2 ** diskCount - 1;
    }

    function towerLabel(i) { return lt(`Tower ${i + 1}`, `টাওয়ার ${n(i + 1)}`); }

    function moveSummaryLabel() {
        return lt(`Moves: ${moves} / ${optimalMoves} optimal`, `মুভ: ${n(moves)} / ${n(optimalMoves)}`);
    }

    function insightMessage() {
        if (moves === optimalMoves)       return lt('Perfect! You solved it in the minimum number of moves.', 'চমৎকার! সর্বোত্তম সংখ্যক মুভে সমাধান।');
        if (moves <= optimalMoves + 3)    return lt('Great planning — very close to the optimal solution.', 'দুর্দান্ত পরিকল্পনা — সর্বোত্তম সমাধানের কাছাকাছি।');
        return lt('Keep practicing. Planning ahead reduces unnecessary moves.', 'অনুশীলন চালিয়ে যান।');
    }

    function trainingProgressText() {
        return lt(
            `Training Progress: ${completedTasksCount} / ${totalTasksCount} tasks completed`,
            `ট্রেনিং অগ্রগতি: ${n(completedTasksCount)} / ${n(totalTasksCount)}টি টাস্ক সম্পন্ন`
        );
    }

    onMount(() => {
        if (!$user) return goto('/login');
        const urlParams = new URLSearchParams(window.location.search);
        isTrainingMode     = urlParams.get('training') === 'true';
        trainingPlanId     = parseInt(urlParams.get('planId')) || null;
        trainingDifficulty = parseInt(urlParams.get('difficulty')) || 1;
        taskId             = $page.url.searchParams.get('taskId');

        if      (isTrainingMode && trainingDifficulty >= 8) diskCount = 5;
        else if (isTrainingMode && trainingDifficulty >= 6) diskCount = 4;
        else                                                diskCount = 3;

        recordedDiskCount = diskCount;
        refreshTowerState();
    });

    function backToDashboard() { goto(isTrainingMode ? '/training' : '/dashboard'); }

    function startTest(practice = false) {
        isPracticeMode = practice;
        practiceStatusMessage = '';
        diskCount = practice ? 3 : recordedDiskCount;
        stage = 'test';
        refreshTowerState();
        selectedTower = null;
        moves = 0;
        startTime = Date.now();
        firstMoveTime = 0;
        planningTime = 0;
        completed = false;
        invalidFlash = false;
    }

    function selectTower(index) {
        if (completed) return;
        if (selectedTower === null) {
            if (towers[index].length > 0) selectedTower = index;
        } else {
            if (selectedTower !== index) {
                const disk      = towers[selectedTower][towers[selectedTower].length - 1];
                const targetTop = towers[index][towers[index].length - 1];
                if (!targetTop || disk < targetTop) {
                    towers[selectedTower] = towers[selectedTower].slice(0, -1);
                    towers[index]         = [...towers[index], disk];
                    towers = [...towers]; // trigger reactivity
                    moves++;
                    if (moves === 1) {
                        firstMoveTime = Date.now();
                        planningTime  = firstMoveTime - startTime;
                    }
                    if (towers[2].length === diskCount) { completed = true; calculateResults(); }
                } else {
                    // Invalid — flash
                    if (invalidTimer) clearTimeout(invalidTimer);
                    invalidFlash = true;
                    invalidTimer = setTimeout(() => { invalidFlash = false; }, 500);
                }
            }
            selectedTower = null;
        }
    }

    function calculateResults() {
        const totalTime = Date.now() - startTime;
        if (isPracticeMode) {
            leavePractice(true);
            return;
        }
        stage = 'results';
        saveResults(totalTime);
    }

    function leavePractice(completed = false) {
        if (invalidTimer) {
            clearTimeout(invalidTimer);
            invalidTimer = null;
        }
        isPracticeMode = false;
        diskCount = recordedDiskCount;
        refreshTowerState();
        selectedTower = null;
        moves = 0;
        completed = false;
        planningTime = 0;
        invalidFlash = false;
        practiceStatusMessage = completed ? getPracticeCopy($locale).complete : '';
        stage = 'intro';
    }

    async function saveResults(totalTime) {
        try {
            const excessMoves = moves - optimalMoves;
            const efficiency  = Math.max(0, 100 - excessMoves * 10);
            if (isTrainingMode && trainingPlanId) {
                const result = await training.submitSession({
                    user_id: $user.id, training_plan_id: trainingPlanId,
                    domain: 'planning', task_type: 'tower_of_hanoi',
                    score: efficiency, accuracy: completed ? 100 : 0,
                    average_reaction_time: planningTime,
                    consistency: Math.max(0, 100 - excessMoves * 5),
                    errors: excessMoves,
                    session_duration: Math.round(totalTime / 60000),
                    task_id: taskId
                });
                sessionComplete     = result.session_complete;
                completedTasksCount = result.completed_tasks;
                totalTasksCount     = result.total_tasks;
            } else {
                await tasks.submitResult(
                    $user.id, 'planning', efficiency,
                    JSON.stringify({
                        moves_taken: moves, optimal_moves: optimalMoves,
                        excess_moves: excessMoves, planning_time_ms: planningTime,
                        total_time_seconds: Math.round(totalTime / 1000), completed
                    })
                );
            }
        } catch (err) { console.error('Error saving results:', err); }
    }

    function resetTest() {
        refreshTowerState();
        selectedTower = null; moves = 0; completed = false;
        startTime = Date.now(); firstMoveTime = 0; planningTime = 0;
        invalidFlash = false;
    }

    // Disk visual widths: scale from 56px (size 1) to max for current diskCount
    function diskWidth(size) { return 44 + size * 36; }

    const DISK_COLORS = ['#16a34a', '#2563eb', '#d97706', '#dc2626', '#7c3aed'];
    function diskColor(size) { return DISK_COLORS[(size - 1) % DISK_COLORS.length]; }
</script>

<svelte:head>
    <title>{lt('Planning Test - NeuroBloom', 'পরিকল্পনা পরীক্ষা - NeuroBloom')}</title>
</svelte:head>

<div class="plan-container" data-localize-skip>

    <!-- INTRO -->
    {#if stage === 'intro'}
        <div class="page-content">

            <div class="task-header">
                <button class="back-btn" on:click={backToDashboard}>
                    {isTrainingMode ? 'Back to Training' : 'Back to Dashboard'}
                </button>
                <h1 class="task-title">Tower of London</h1>
            </div>

            <div class="concept-card">
                <div class="concept-badge">Planning & Executive Function · Baseline Assessment</div>
                <h2>What This Test Measures</h2>
                <p>The Tower of London measures <strong>planning depth</strong> — your ability to think ahead, anticipate consequences, and execute a multi-step strategy with minimal errors. Unlike simple reaction tasks, this test requires you to mentally simulate several moves before touching anything. The key metric is <em>move efficiency</em>: how close you come to the mathematically optimal solution.</p>
            </div>

            <div class="rules-card">
                <h3>Rules</h3>
                <ul class="rules-list">
                    <li>Three disks are stacked on the <strong>left tower</strong> at the start</li>
                    <li>Goal: move all disks to the <strong>right tower</strong></li>
                    <li>You may only move <strong>one disk at a time</strong> (the top disk)</li>
                    <li>A <strong>larger disk cannot rest on a smaller disk</strong></li>
                    <li>Minimum possible moves for 3 disks: <span class="optimal-badge">{optimalMoves}</span></li>
                </ul>
                <div class="howto-grid">
                    <div class="howto-step">
                        <div class="step-num">1</div>
                        <div class="step-desc">Click a tower to pick up its top disk</div>
                    </div>
                    <div class="howto-step">
                        <div class="step-num">2</div>
                        <div class="step-desc">Click a destination tower to place it</div>
                    </div>
                    <div class="howto-step">
                        <div class="step-num">3</div>
                        <div class="step-desc">Repeat until all disks land on the right tower</div>
                    </div>
                </div>
            </div>

            <div class="tip-card">
                <div class="tip-title">Strategy</div>
                <p>Before making your first move, mentally walk through the entire sequence. The classic minimum-move algorithm always moves the smallest disk first, alternating between the middle and right towers. Resist the urge to move immediately — planning time before the first move is recorded and is clinically meaningful.</p>
            </div>

            <div class="clinical-card">
                <h3>Clinical Basis</h3>
                <p>The Tower of London (Shallice, 1982) is a neuropsychological staple for assessing dorsolateral prefrontal cortex function — the region responsible for goal-directed planning, working memory, and inhibitory control. Planning deficits are documented in up to 65% of MS patients and correlate with lesion load in frontoparietal white matter tracts. Two metrics are particularly informative: <em>initial planning time</em> (time before the first move) reflects forward mental simulation capacity, and <em>excess moves</em> reflect impulsivity and failure to maintain the plan during execution.</p>
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
                <div class="moves-pill" class:pill-perfect={moves === optimalMoves && moves > 0}>
                    {moveSummaryLabel()}
                </div>
                {#if selectedTower !== null}
                    <div class="selected-pill">
                        {lt(`Tower ${selectedTower + 1} selected`, `টাওয়ার ${n(selectedTower + 1)} নির্বাচিত`)}
                    </div>
                {/if}
                <button class="reset-btn" on:click={resetTest}>Reset</button>
            </div>

            {#if invalidFlash}
                <div class="invalid-banner">Invalid move — a larger disk cannot go on a smaller one.</div>
            {/if}

            {#if completed}
                <div class="complete-banner">
                    Puzzle complete — {moves === optimalMoves ? 'perfect score!' : `${moves} moves (optimal: ${optimalMoves})`}
                </div>
            {/if}

            <!-- Tower board -->
            <div class="board-card">
                <div class="towers-row">
                    {#each towers as tower, tIdx}
                        <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
                        <div
                            class="tower-col"
                            class:tower-selected={selectedTower === tIdx}
                            class:tower-hoverable={!completed}
                            on:click={() => selectTower(tIdx)}
                            role="button"
                            tabindex="0"
                            on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && selectTower(tIdx)}
                        >
                            <div class="tower-disks">
                                {#each [...tower].reverse() as disk}
                                    <div
                                        class="disk"
                                        style="width: {diskWidth(disk)}px; background: {diskColor(disk)};"
                                        class:disk-top={disk === tower[tower.length - 1]}
                                    >
                                        {disk}
                                    </div>
                                {/each}
                                <!-- Spacer to push disks to bottom -->
                                <div class="disk-spacer"></div>
                            </div>
                            <div class="peg"></div>
                            <div class="peg-base"></div>
                            <div class="tower-label">{towerLabel(tIdx)}</div>
                        </div>
                    {/each}
                </div>
            </div>

            <div class="board-hint">
                {#if selectedTower !== null}
                    Click a destination tower to place the disk
                {:else}
                    Click any tower with disks to pick up the top disk
                {/if}
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
                        <strong>Session Complete — all {totalTasksCount} tasks finished.</strong>
                    {:else}
                        <strong>{trainingProgressText()}</strong>
                        <span>Continue with remaining tasks to complete this session.</span>
                    {/if}
                </div>
            {/if}

            <div class="results-card">
                <div class="score-header">
                    <div class="score-big">{n(Math.max(0, 100 - ((moves - optimalMoves) * 10)).toFixed(0))}%</div>
                    <div class="score-label">Planning Efficiency Score</div>
                </div>

                <div class="metrics-grid">
                    <div class="metric-cell">
                        <div class="metric-value">{n(moves)}</div>
                        <div class="metric-label">Moves Taken</div>
                    </div>
                    <div class="metric-cell metric-ref">
                        <div class="metric-value">{n(optimalMoves)}</div>
                        <div class="metric-label">Optimal Moves</div>
                    </div>
                    <div class="metric-cell {moves - optimalMoves === 0 ? 'metric-good' : moves - optimalMoves <= 3 ? '' : 'metric-warn'}">
                        <div class="metric-value">+{n(moves - optimalMoves)}</div>
                        <div class="metric-label">Excess Moves</div>
                    </div>
                    <div class="metric-cell">
                        <div class="metric-value">{n((planningTime / 1000).toFixed(1), { minimumFractionDigits: 1, maximumFractionDigits: 1 })}s</div>
                        <div class="metric-label">Planning Time</div>
                    </div>
                    <div class="metric-cell metric-good">
                        <div class="metric-value">{completed ? 'Yes' : 'No'}</div>
                        <div class="metric-label">Completed</div>
                    </div>
                    <div class="metric-cell">
                        <div class="metric-value">{n(diskCount)}</div>
                        <div class="metric-label">Disk Count</div>
                    </div>
                </div>

                <div class="interp-card">
                    <div class="interp-title">Interpretation</div>
                    <p>{insightMessage()}</p>
                    {#if planningTime > 30000}
                        <p class="plan-note">Long initial planning time detected ({(planningTime / 1000).toFixed(0)}s). Thinking through the full sequence before moving is an effective strategy.</p>
                    {/if}
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
    .plan-container {
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
        color: #166534;
        border: 2px solid #166534;
        padding: 0.6rem 1.25rem;
        border-radius: 8px;
        cursor: pointer;
        font-size: 0.9rem;
        font-weight: 600;
        white-space: nowrap;
        transition: background 0.2s, color 0.2s;
    }
    .back-btn:hover { background: #166534; color: white; }

    .task-title {
        font-size: 1.75rem;
        font-weight: 700;
        color: #14532d;
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
        background: #dcfce7;
        color: #166534;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        padding: 0.3rem 0.9rem;
        border-radius: 20px;
        margin-bottom: 0.75rem;
    }
    .concept-card h2 { font-size: 1.4rem; font-weight: 700; color: #14532d; margin: 0 0 0.75rem; }
    .concept-card p  { color: #374151; line-height: 1.65; margin: 0; }

    /* Rules card */
    .rules-card {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
    }
    .rules-card h3 { font-size: 1.1rem; font-weight: 700; color: #14532d; margin: 0 0 1rem; }

    .rules-list {
        margin: 0 0 1.25rem;
        padding-left: 1.25rem;
        display: flex;
        flex-direction: column;
        gap: 0.45rem;
    }
    .rules-list li { color: #374151; font-size: 0.9rem; line-height: 1.5; }

    .optimal-badge {
        display: inline-block;
        background: #dcfce7;
        color: #166534;
        font-weight: 800;
        padding: 0.1rem 0.6rem;
        border-radius: 6px;
    }

    .howto-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
        gap: 0.75rem;
    }
    .howto-step {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        background: #f0fdf4;
        border-radius: 10px;
        padding: 0.85rem;
    }
    .step-num {
        width: 28px; height: 28px;
        background: #166534;
        color: white;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.85rem; font-weight: 800;
        flex-shrink: 0;
    }
    .step-desc { color: #374151; font-size: 0.88rem; line-height: 1.45; }

    /* Tip / Clinical */
    .tip-card {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 16px;
        padding: 1.5rem 2rem;
    }
    .tip-title { font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #166534; margin-bottom: 0.5rem; }
    .tip-card p { color: #374151; line-height: 1.6; margin: 0; }

    .clinical-card {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border: 1px solid #bbf7d0;
        border-radius: 16px;
        padding: 1.5rem 2rem;
    }
    .clinical-card h3 { font-size: 1rem; font-weight: 700; color: #14532d; margin: 0 0 0.75rem; }
    .clinical-card p  { color: #166534; font-size: 0.95rem; line-height: 1.65; margin: 0; }

    /* ============================================================
       TEST PHASE
    ============================================================ */
    .test-topbar {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        flex-wrap: wrap;
    }

    .moves-pill {
        background: white;
        color: #374151;
        font-size: 0.9rem;
        font-weight: 700;
        padding: 0.5rem 1.1rem;
        border-radius: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        transition: background 0.3s, color 0.3s;
    }
    .pill-perfect { background: #16a34a; color: white; }

    .selected-pill {
        background: #166534;
        color: white;
        font-size: 0.82rem;
        font-weight: 700;
        padding: 0.4rem 0.9rem;
        border-radius: 20px;
        animation: pop-in 0.15s ease-out;
    }
    @keyframes pop-in {
        from { transform: scale(0.85); opacity: 0; }
        to   { transform: scale(1);    opacity: 1; }
    }

    .reset-btn {
        margin-left: auto;
        background: white;
        color: #6b7280;
        border: 2px solid #d1d5db;
        padding: 0.45rem 1.1rem;
        border-radius: 8px;
        cursor: pointer;
        font-size: 0.85rem;
        font-weight: 600;
        transition: border-color 0.2s, color 0.2s;
    }
    .reset-btn:hover { border-color: #9ca3af; color: #374151; }

    .invalid-banner {
        background: #fee2e2;
        color: #b91c1c;
        border: 1px solid #fca5a5;
        border-radius: 10px;
        padding: 0.65rem 1.25rem;
        font-size: 0.9rem;
        font-weight: 600;
        animation: shake 0.4s ease;
    }
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25%       { transform: translateX(-6px); }
        75%       { transform: translateX(6px); }
    }

    .complete-banner {
        background: #16a34a;
        color: white;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        font-size: 1rem;
        font-weight: 700;
        text-align: center;
        animation: pop-in 0.3s ease-out;
    }

    /* Board */
    .board-card {
        background: white;
        border-radius: 16px;
        padding: 2rem 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
    }

    .towers-row {
        display: flex;
        justify-content: space-around;
        align-items: flex-end;
        gap: 1rem;
        padding: 0 1rem;
    }

    /* Individual tower column */
    .tower-col {
        display: flex;
        flex-direction: column;
        align-items: center;
        cursor: pointer;
        padding: 0.5rem;
        border-radius: 12px;
        border: 2px solid transparent;
        transition: border-color 0.15s, background 0.15s, transform 0.15s;
        flex: 1;
        max-width: 200px;
        outline: none;
    }
    .tower-col.tower-hoverable:hover {
        background: #f0fdf4;
        border-color: #86efac;
        transform: translateY(-4px);
    }
    .tower-col.tower-selected {
        background: #dcfce7;
        border-color: #16a34a;
    }

    /* Disk stack container */
    .tower-disks {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
        height: 200px;
        position: relative;
        justify-content: flex-end;
        gap: 3px;
        padding-bottom: 0;
        z-index: 2;
    }

    .disk-spacer { flex: 1; }

    .disk {
        height: 28px;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 800;
        font-size: 0.95rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        transition: filter 0.15s;
        min-width: 44px;
    }
    .disk-top { filter: brightness(1.12); }

    .tower-selected .disk-top {
        box-shadow: 0 0 0 3px white, 0 0 0 5px #16a34a;
    }

    /* Peg */
    .peg {
        width: 10px;
        height: 200px;
        background: linear-gradient(to bottom, #94a3b8, #64748b);
        border-radius: 5px;
        margin-top: -200px;
        z-index: 1;
        pointer-events: none;
    }

    .peg-base {
        width: 140px;
        height: 10px;
        background: linear-gradient(to bottom, #64748b, #475569);
        border-radius: 5px;
        margin-top: 2px;
        pointer-events: none;
    }

    .tower-label {
        margin-top: 0.6rem;
        font-size: 0.82rem;
        font-weight: 600;
        color: #6b7280;
    }

    .board-hint {
        text-align: center;
        color: #6b7280;
        font-size: 0.9rem;
        margin-top: 0.25rem;
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
        background: linear-gradient(135deg, #166534 0%, #14532d 100%);
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
    .metric-ref  .metric-value { color: #166534; }

    .interp-card {
        padding: 1.5rem 1.75rem;
        border-bottom: 1px solid #f1f5f9;
    }
    .interp-title { font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #166534; margin-bottom: 0.5rem; }
    .interp-card p { color: #374151; line-height: 1.6; margin: 0 0 0.5rem; font-size: 0.95rem; }
    .plan-note { color: #b45309; font-size: 0.9rem; }

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
    @media (max-width: 640px) {
        .plan-container { padding: 1rem; }
        .task-title     { font-size: 1.4rem; }
        .peg-base       { width: 90px; }
        .score-big      { font-size: 3rem; }
        .metrics-grid   { grid-template-columns: repeat(2, 1fr); }
        .metrics-grid .metric-cell:nth-child(3n)  { border-right: 1px solid #f1f5f9; }
        .metrics-grid .metric-cell:nth-child(2n)  { border-right: none; }
        .start-button   { width: calc(100% - 2.5rem); margin: 1.25rem; }
    }
</style>

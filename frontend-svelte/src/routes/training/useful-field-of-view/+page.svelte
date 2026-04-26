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
    import {
        locale,
        localeText,
        formatNumber,
        formatPercent,
        performanceText,
        taskPhraseText,
        taskValueText,
        ufovInstructionText,
        ufovSubtestText
    } from '$lib/i18n';
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
    const lt = (en, bn) => localeText({ en, bn }, $locale);

    function n(value, options = {}) {
        return formatNumber(value, $locale, options);
    }

    function pct(value) {
        return formatPercent(value, $locale, {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });
    }

    function fixed(value, digits = 2) {
        return n(value, {
            minimumFractionDigits: digits,
            maximumFractionDigits: digits
        });
    }

    function ms(value) {
        return `${n(value)}${lt('ms', 'মি.সে.')}`;
    }

    function trialCountText(current, total) {
        return lt(`Trial ${n(current)} of ${n(total)}`, `${n(total)}টির মধ্যে ${n(current)} নম্বর ট্রায়াল`);
    }

    function clockLabel(label) {
        const map = {
            "3 o'clock": { en: "3 o'clock", bn: '৩টা' },
            '1:30': { en: '1:30', bn: '১:৩০' },
            "12 o'clock": { en: "12 o'clock", bn: '১২টা' },
            '10:30': { en: '10:30', bn: '১০:৩০' },
            "9 o'clock": { en: "9 o'clock", bn: '৯টা' },
            '7:30': { en: '7:30', bn: '৭:৩০' },
            "6 o'clock": { en: "6 o'clock", bn: '৬টা' },
            '4:30': { en: '4:30', bn: '৪:৩০' }
        };
        return localeText(map[label] || { en: label, bn: label }, $locale);
    }

    function feedbackText(performance) {
        if (performance === 'perfect') {
            return lt(
                'Excellent. You identified both the central and peripheral information quickly.',
                'চমৎকার। আপনি মাঝখানের ও চারপাশের তথ্য দ্রুত ধরতে পেরেছেন।'
            );
        }
        if (performance === 'partial') {
            return lt(
                'Good effort. Keep your gaze centered and answer from your first impression.',
                'ভালো চেষ্টা। চোখ মাঝখানে রেখে প্রথম যে ধারণা আসে সেটি দিয়ে উত্তর দিন।'
            );
        }
        return lt(
            'This trial was difficult. Stay relaxed and keep practicing the quick glance strategy.',
            'এই ট্রায়ালটি কঠিন ছিল। শান্ত থাকুন এবং এক ঝলকে দেখার কৌশল অনুশীলন করুন।'
        );
    }

    function adaptationReasonText(reason) {
        if ($locale === 'en' && reason) return reason;
        return taskPhraseText('no_adaptation_reason', $locale);
    }

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
            error = lt('Failed to load trial. Please try again.', 'ট্রায়াল লোড করা যায়নি। আবার চেষ্টা করুন।');
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
            error = lt('Failed to submit response. Please try again.', 'উত্তর জমা দেওয়া যায়নি। আবার চেষ্টা করুন।');
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
            goto('/dashboard');
        } else {
            loadTrial();
        }
    }

    function exitTask() {
        goto('/dashboard');
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
        return performanceText(perf, $locale);
    }

    function perfColor(perf) {
        const map = { perfect: '#10b981', partial: '#f59e0b', incorrect: '#ef4444' };
        return map[perf] || '#ef4444';
    }
</script>

<div class="ufov-container">

    <!-- Header -->
    <div class="task-header">        <div class="header-center">
            <h1 class="task-title">{lt('Useful Field of View', 'ব্যবহারযোগ্য দৃশ্যক্ষেত্র')}</h1>
            <DifficultyBadge {difficulty} domain={lt('Visual Scanning', 'দৃশ্য খোঁজা')} />
        </div>
    </div>

    <!-- Error banner -->
    {#if error}
        <div class="error-banner">
            <p>{error}</p>
            <button on:click={() => { error = null; gamePhase = 'intro'; }}>{lt('Dismiss', 'বন্ধ করুন')}</button>
        </div>
    {/if}

    <!-- Loading skeleton (while fetching trial from intro) -->
    {#if loading && gamePhase === 'intro'}
        <div class="skeleton-wrap">
            <LoadingSkeleton />
        </div>

    <!-- Intro -->
    {:else if gamePhase === 'intro'}
		<div class="intro-wrapper">
			<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />

            <div class="concept-card">
                <div class="concept-badge">{lt('Visual Scanning · Divided Attention', 'দৃশ্য খোঁজা · ভাগ করা মনোযোগ')}</div>
                <h2>{lt('Useful Field of View (UFOV)', 'ব্যবহারযোগ্য দৃশ্যক্ষেত্র (UFOV)')}</h2>
                <p>{lt('Images flash at the center and edge of your visual field for a very short time. Your task is to identify the center vehicle and, in harder rounds, where the outside shape appeared. It checks how much visual information you can catch in one quick glance.', 'স্ক্রিনের মাঝখানে ও চারপাশে খুব অল্প সময়ের জন্য ছবি দেখা যাবে। আপনার কাজ হলো মাঝখানের গাড়িটি চিনে নেওয়া এবং কঠিন রাউন্ডে চারপাশের আকারটি কোথায় ছিল তা বলা। এতে বোঝা যায় এক ঝলকে আপনি কতটা দৃশ্যত তথ্য ধরতে পারছেন।')}</p>
            </div>

            <div class="rules-card">
                <h3>{lt('How It Works', 'কীভাবে করবেন')}</h3>
                <ol class="rules-list">
                    <li><strong>{lt('Keep your eyes on the center cross (+)', 'চোখ মাঝখানের ক্রস (+)-এ রাখুন')}</strong> {lt('during the flash.', 'ছবি ঝলকানোর সময় চোখ সরাবেন না।')}</li>
                    <li><strong>{lt('A very brief stimulus appears', 'খুব অল্প সময়ের জন্য ছবি দেখা যাবে')}</strong> {lt('with a vehicle in the center and sometimes a shape around it.', 'মাঝখানে একটি গাড়ি থাকবে, কখনও চারপাশে একটি আকারও থাকবে।')}</li>
                    <li><strong>{lt('Respond right away', 'দ্রুত উত্তর দিন')}</strong> {lt('by choosing the vehicle and, when asked, the outside location.', 'গাড়ির ধরন এবং প্রয়োজন হলে চারপাশের অবস্থান বেছে নিন।')}</li>
                </ol>
            </div>

            <div class="info-grid">
                <div class="info-card">
                    <div class="info-label">{lt('Subtest 1', 'সাবটেস্ট ১')}</div>
                    <div class="info-title">{lt('Central Only', 'শুধু কেন্দ্র')}</div>
                    <p>{lt('Identify the vehicle in the center. This measures simple visual processing speed.', 'মাঝখানের গাড়িটি চিনুন। এতে সরল দৃশ্য-প্রক্রিয়াকরণের গতি বোঝা যায়।')}</p>
                </div>
                <div class="info-card">
                    <div class="info-label">{lt('Subtest 2', 'সাবটেস্ট ২')}</div>
                    <div class="info-title">{lt('Central + Peripheral', 'কেন্দ্র ও চারপাশ')}</div>
                    <p>{lt('Identify the center vehicle and the outside shape location together. This measures divided visual attention.', 'মাঝখানের গাড়ি ও চারপাশের আকারের অবস্থান একসঙ্গে ধরুন। এতে ভাগ করা দৃশ্য-মনোযোগ বোঝা যায়।')}</p>
                </div>
                <div class="info-card">
                    <div class="info-label">{lt('Subtest 3', 'সাবটেস্ট ৩')}</div>
                    <div class="info-title">{lt('With Distractors', 'বিভ্রান্তিকর বস্তুসহ')}</div>
                    <p>{lt('The same task with extra visual clutter. This measures selective visual attention.', 'একই কাজ, তবে বাড়তি দৃশ্যগত ভিড় থাকবে। এতে নির্বাচিত দৃশ্য-মনোযোগ বোঝা যায়।')}</p>
                </div>
            </div>

            <div class="tip-card">
                <div class="tip-title">{lt('Strategy', 'কৌশল')}</div>
                <p>{lt('Do not over-analyze. Use your first impression and answer as quickly as you can.', 'বেশি বিশ্লেষণ করবেন না। প্রথম যে ধারণা আসে সেটি ধরে যত দ্রুত পারেন উত্তর দিন।')}</p>
                <div class="timing-scale">
                    <span class="ts-start">{lt(`Level ${n(1)} · ${ms(500)}`, `লেভেল ${n(1)} · ${ms(500)}`)}</span>
                    <div class="ts-bar"></div>
                    <span class="ts-end">{lt(`Level ${n(10)} · ${ms(17)}`, `লেভেল ${n(10)} · ${ms(17)}`)}</span>
                </div>
            </div>

            <div class="clinical-card">
                <h3>{lt('Clinical Basis', 'ক্লিনিক্যাল ভিত্তি')}</h3>
                <p>{lt('UFOV is used in rehabilitation research to understand visual processing speed and divided attention, both of which matter for complex daily tasks.', 'দৃশ্য-প্রক্রিয়াকরণের গতি ও ভাগ করা মনোযোগ বোঝার জন্য পুনর্বাসন গবেষণায় UFOV ব্যবহার করা হয়। জটিল দৈনন্দিন কাজে এই দুই দক্ষতাই গুরুত্বপূর্ণ।')}</p>
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
                <div class="trial-counter">{trialCountText(trialsCompleted + 1, TRIALS_PER_SESSION)}</div>
                <div class="subtest-tag">{ufovSubtestText(trialData?.subtest, $locale, trialData?.description)}</div>
                <div class="instructions-box">{ufovInstructionText(trialData, $locale)}</div>
                <div class="fixation-area">
                    <div class="fixation-cross">+</div>
                    <p class="fixation-hint">{lt('Keep your eyes on this cross', 'চোখ এই ক্রসে রাখুন')}</p>
                </div>
                <div class="timing-tag">{lt('Display time', 'দেখানোর সময়')}: <strong>{ms(trialData?.presentation_time_ms)}</strong></div>
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
                            {taskValueText('vehicle', trialData.central_target, $locale)}
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
                <h2>{lt('What Did You See?', 'আপনি কী দেখেছেন?')}</h2>
                <p class="response-sub">{ufovInstructionText(trialData, $locale)}</p>

                <div class="response-group">
                    <h3>{lt('Central Vehicle', 'মাঝখানের গাড়ি')}</h3>
                    <div class="vehicle-choices">
                        <button
                            class="vehicle-btn {centralResponse === 'car' ? 'v-active' : ''}"
                            on:click={() => selectCentralTarget('car')}
                            disabled={loading}
                        >
                            <div class="v-chip v-car">{taskValueText('vehicle', 'car', $locale)}</div>
                        </button>
                        <button
                            class="vehicle-btn {centralResponse === 'truck' ? 'v-active' : ''}"
                            on:click={() => selectCentralTarget('truck')}
                            disabled={loading}
                        >
                            <div class="v-chip v-truck">{taskValueText('vehicle', 'truck', $locale)}</div>
                        </button>
                    </div>
                </div>

                {#if trialData?.subtest !== 'central_only'}
                    <div class="response-group">
                        <h3>{lt('Peripheral Shape Location', 'চারপাশের আকারের অবস্থান')}</h3>
                        <p class="response-hint">{lt('Where was the', 'কোথায় ছিল')} <strong>{taskValueText('shape', trialData.peripheral_target, $locale)}</strong>?</p>
                        <div class="clock-dial">
                            {#each getPeripheralPositions() as pos}
                                <button
                                    class="clock-btn {peripheralResponse === pos.label ? 'clk-active' : ''}"
                                    style="left: {50 + pos.x * 40}%; top: {50 + pos.y * 40}%;"
                                    on:click={() => selectPeripheralPosition(pos.label)}
                                    disabled={!centralResponse || loading}
                                >{clockLabel(pos.label)}</button>
                            {/each}
                            <div class="clock-fix">+</div>
                        </div>
                        {#if !centralResponse}
                            <p class="select-note">{lt('Select the central vehicle first', 'আগে মাঝখানের গাড়ি বেছে নিন')}</p>
                        {/if}
                    </div>
                {/if}

                {#if loading}
                    <div class="submitting">{lt('Evaluating response...', 'উত্তর যাচাই হচ্ছে...')}</div>
                {/if}
            </div>
        </div>

    <!-- Results -->
    {:else if gamePhase === 'results' && results}
		<div class="intro-wrapper">
			<TaskReturnButton locale={$locale} context={TASK_RETURN_CONTEXT.TRAINING} />
            <div class="results-card">
                <div class="perf-header" style="background: {perfColor(results.performance)}">
                    <h2>{performanceLabel(results.performance)}</h2>
                    <p class="perf-sub">{lt(`Trial ${n(trialsCompleted)} of ${n(TRIALS_PER_SESSION)} complete`, `${n(TRIALS_PER_SESSION)}টির মধ্যে ${n(trialsCompleted)}টি ট্রায়াল শেষ`)}</p>
                </div>

                <div class="results-body">

                    <div class="metrics-grid">
                        <div class="metric-cell">
                            <div class="mc-val">{pct((results.accuracy || 0) * 100)}</div>
                            <div class="mc-lbl">{lt('Accuracy', 'সঠিকতা')}</div>
                        </div>
                        <div class="metric-cell">
                            <div class="mc-val">{ms(results.response_time)}</div>
                            <div class="mc-lbl">{lt('Response Time', 'প্রতিক্রিয়ার সময়')}</div>
                        </div>
                        <div class="metric-cell">
                            <div class="mc-val">{fixed(results.processing_speed_score, 2)}</div>
                            <div class="mc-lbl">{lt('Processing Speed', 'প্রক্রিয়াকরণের গতি')}</div>
                        </div>
                        <div class="metric-cell">
                            <div class="mc-val">{ms(results.presentation_time_ms)}</div>
                            <div class="mc-lbl">{lt('Display Time', 'দেখানোর সময়')}</div>
                        </div>
                    </div>

                    <div class="breakdown-card">
                        <h3>{lt('Trial Breakdown', 'ট্রায়ালের বিশ্লেষণ')}</h3>
                        <div class="breakdown-rows">
                            <div class="br-row">
                                <span class="br-label">{lt('Central Vehicle', 'মাঝখানের গাড়ি')}</span>
                                <span class="br-tag {results.central_correct ? 'tag-ok' : 'tag-err'}">
                                    {results.central_correct ? lt('Correct', 'সঠিক') : lt('Incorrect', 'ভুল')}
                                </span>
                            </div>
                            {#if results.subtest !== 'central_only'}
                                <div class="br-row">
                                    <span class="br-label">{lt('Peripheral Location', 'চারপাশের অবস্থান')}</span>
                                    <span class="br-tag {results.peripheral_correct ? 'tag-ok' : 'tag-err'}">
                                        {results.peripheral_correct ? lt('Correct', 'সঠিক') : lt('Incorrect', 'ভুল')}
                                    </span>
                                </div>
                            {/if}
                            <div class="br-row">
                                <span class="br-label">{lt('Subtest', 'সাবটেস্ট')}</span>
                                <span class="br-tag tag-info">{ufovSubtestText(results.subtest, $locale)}</span>
                            </div>
                        </div>
                    </div>

                    {#if results.user_central_response}
                        <div class="answer-card">
                            <h3>{lt('Answer Review', 'উত্তর পর্যালোচনা')}</h3>
                            <div class="answer-group">
                                <div class="ag-label">{lt('Central Vehicle', 'মাঝখানের গাড়ি')}</div>
                                <div class="ag-row">
                                    <span class="ag-prompt">{lt('Your answer', 'আপনার উত্তর')}</span>
                                    <span class="ag-val {results.central_correct ? 'av-ok' : 'av-err'}">{taskValueText('vehicle', results.user_central_response, $locale)}</span>
                                </div>
                                {#if !results.central_correct}
                                    <div class="ag-row">
                                        <span class="ag-prompt">{lt('Correct answer', 'সঠিক উত্তর')}</span>
                                        <span class="ag-val av-ok">{taskValueText('vehicle', results.correct_central_target, $locale)}</span>
                                    </div>
                                {/if}
                            </div>
                            {#if (results.subtest === 'central_peripheral' || results.subtest === 'central_peripheral_distractors') && results.correct_peripheral_position}
                                <div class="answer-group">
                                    <div class="ag-label">{lt('Peripheral Shape', 'চারপাশের আকার')} ({taskValueText('shape', results.correct_peripheral_target, $locale)})</div>
                                    <div class="ag-row">
                                        <span class="ag-prompt">{lt('Your location', 'আপনার বেছে নেওয়া অবস্থান')}</span>
                                        <span class="ag-val {results.peripheral_correct ? 'av-ok' : 'av-err'}">{results.user_peripheral_response ? clockLabel(results.user_peripheral_response) : lt('Not selected', 'নির্বাচন করা হয়নি')}</span>
                                    </div>
                                    {#if !results.peripheral_correct}
                                        <div class="ag-row">
                                            <span class="ag-prompt">{lt('Correct location', 'সঠিক অবস্থান')}</span>
                                            <span class="ag-val av-ok">{clockLabel(results.correct_peripheral_position)}</span>
                                        </div>
                                    {/if}
                                </div>
                            {/if}
                        </div>
                    {/if}

                    <div class="feedback-card">
                        <p>{feedbackText(results.performance)}</p>
                    </div>

                    <div class="adapt-card">
                        {#if results.new_difficulty > results.old_difficulty}
                            <p>{lt('Level', 'লেভেল')} {n(results.old_difficulty)} <span class="arr">&#8594;</span> <strong>{lt('Level', 'লেভেল')} {n(results.new_difficulty)}</strong> {lt('— advancing to a shorter display time', '— আরও কম সময়ের ঝলকে এগোচ্ছে')}</p>
                        {:else if results.new_difficulty < results.old_difficulty}
                            <p>{lt('Adjusting to', 'ভালোভাবে মানিয়ে নিতে')} <strong>{lt('Level', 'লেভেল')} {n(results.new_difficulty)}</strong> {lt('for better calibration', 'এ আনা হচ্ছে')}</p>
                        {:else}
                            <p>{lt('Staying at', 'থাকছে')} <strong>{lt('Level', 'লেভেল')} {n(results.new_difficulty)}</strong></p>
                        {/if}
                        <p class="adapt-reason">{adaptationReasonText(results.adaptation_reason)}</p>
                    </div>

                    <div class="progress-row">
                        <span class="prog-label">{lt(`${n(trialsCompleted)} / ${n(TRIALS_PER_SESSION)} trials complete`, `${n(TRIALS_PER_SESSION)}টির মধ্যে ${n(trialsCompleted)}টি ট্রায়াল শেষ`)}</span>
                        <div class="prog-bar">
                            <div class="prog-fill" style="width: {(trialsCompleted / TRIALS_PER_SESSION) * 100}%"></div>
                        </div>
                    </div>

                    <div class="action-row">
                        {#if playMode === TASK_PLAY_MODE.PRACTICE}
                            <button class="start-button" on:click={nextTrial}>{lt('Finish Practice', 'অনুশীলন শেষ করুন')}</button>
                        {:else if trialsCompleted < TRIALS_PER_SESSION}
                            <button class="start-button" on:click={nextTrial}>
                                {lt(`Next Trial (${n(TRIALS_PER_SESSION - trialsCompleted)} remaining)`, `পরের ট্রায়াল (${n(TRIALS_PER_SESSION - trialsCompleted)} বাকি)`)}
                            </button>
                        {:else}
                            <button class="start-button" on:click={exitTask}>{lt('Complete Session', 'সেশন শেষ করুন')}</button>
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

    /* ── Intro / Results unified card (GoNoGo-style single container) ── */
    .intro-wrapper {
        max-width: 960px;
        margin: 0 auto;
        background: white;
        border-radius: 16px;
        padding: 2.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07), 0 1px 3px rgba(0, 0, 0, 0.06);
        display: flex;
        flex-direction: column;
        gap: 1.8rem;
    }

    /* Flatten inner section cards inside the intro wrapper */
    .intro-wrapper > .concept-card,
    .intro-wrapper > .rules-card,
    .intro-wrapper > .tip-card,
    .intro-wrapper > .clinical-card {
        box-shadow: none;
        border-radius: 12px;
        padding: 1.5rem;
        background: #f8fafc;
    }

    /* Results card inside wrapper: remove double shadow */
    .intro-wrapper > .results-card {
        box-shadow: none;
        border-radius: 12px;
        overflow: hidden;
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



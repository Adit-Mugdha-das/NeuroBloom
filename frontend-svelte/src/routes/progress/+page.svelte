<script>
	import { goto } from '$app/navigation';
	import { patientJourney, training } from '$lib/api';
	import SimpleTrendChart from '$lib/components/SimpleTrendChart.svelte';
	import { formatNumber, locale, localeText } from '$lib/i18n';
	import {
		calculateBaselineDifficulty,
		calculateOverallScore,
		calculateTrendDelta,
		formatPointChange,
		getClinicalStatusLabel,
		getClinicalStatusTone,
		getDomainName,
		getTrendLabel,
		getTrendTone
	} from '$lib/progress';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let currentUser = null;
	let loading = true;
	let error = null;
	let actionHref = '/training';
	let actionLabel = null;
	let metrics = null;
	let streakData = null;
	let trendsData = null;
	let weeklySummary = null;
	let comparisonData = null;
	let journey = null;

	user.subscribe((value) => {
		currentUser = value;
	});

	const lt = (en, bn) => localeText({ en, bn }, $locale);
	const n = (value, options = {}) => formatNumber(value, $locale, options);
	const oneDecimal = (value) => n(value, { minimumFractionDigits: 1, maximumFractionDigits: 1 });

	onMount(async () => {
		if (!currentUser) {
			goto('/login');
			return;
		}

		await loadOverview();
	});

	function setLockedState(message, href, label) {
		error = message;
		actionHref = href;
		actionLabel = label;
	}

	async function loadOverview() {
		loading = true;
		error = null;
		actionHref = '/training';
		actionLabel = lt('Open training', 'ট্রেনিং খুলুন');
		metrics = null;
		streakData = null;
		trendsData = null;
		weeklySummary = null;
		comparisonData = null;

		try {
			journey = await patientJourney.get(currentUser.id);

			if (!journey?.progress?.unlocked) {
				if (journey?.state === 'new_user' || journey?.state === 'baseline_in_progress') {
					setLockedState(
						lt('Finish your baseline first to unlock progress reporting.', 'প্রগ্রেস রিপোর্টিং খুলতে আগে আপনার বেসলাইন সম্পন্ন করুন।'),
						'/baseline',
						lt('Open baseline', 'বেসলাইন খুলুন')
					);
					return;
				}

				if (journey?.state === 'baseline_ready_to_calculate') {
					setLockedState(
						lt('Calculate your baseline first. Progress opens after your training journey begins.', 'আগে আপনার বেসলাইন ক্যালকুলেট করুন। ট্রেনিং যাত্রা শুরু হলে অগ্রগতি খুলবে।'),
						'/baseline',
						lt('Open baseline workspace', 'বেসলাইন ওয়ার্কস্পেস খুলুন')
					);
					return;
				}

				if (journey?.state === 'training_plan_missing') {
					setLockedState(
						lt('Generate your training plan first. Progress becomes useful after training begins.', 'আগে আপনার ট্রেনিং প্ল্যান তৈরি করুন। ট্রেনিং শুরু হলে অগ্রগতি কার্যকর হবে।'),
						'/baseline/results',
						lt('Open baseline results', 'বেসলাইন রেজাল্ট খুলুন')
					);
					return;
				}

				setLockedState(
					lt('Complete more training sessions to unlock your progress overview.', 'আপনার প্রগ্রেস ওভারভিউ দেখতে আরও কিছু ট্রেনিং সেশন সম্পন্ন করুন।'),
					journey?.next_route || '/training',
					journey?.next_label || lt('Open training', 'ট্রেনিং খুলুন')
				);
				return;
			}

			const [metricsResponse, streakResponse, trendsResponse, weeklyResponse, comparisonResponse] =
				await Promise.all([
					training.getMetrics(currentUser.id),
					training.getStreak(currentUser.id),
					training.getTrends(currentUser.id, 30),
					training.getWeeklySummary(currentUser.id),
					training.getPerformanceComparison(currentUser.id)
				]);

			metrics = metricsResponse?.has_data === false ? null : metricsResponse;
			streakData = streakResponse;
			trendsData = trendsResponse;
			weeklySummary = weeklyResponse;
			comparisonData = comparisonResponse?.has_data === false ? null : comparisonResponse;
		} catch (loadError) {
			console.error('Error loading progress overview:', loadError);
			setLockedState(
				lt('We could not load your progress overview right now.', 'এই মুহূর্তে আপনার প্রগ্রেস ওভারভিউ লোড করা যাচ্ছে না।'),
				journey?.next_route || '/training',
				journey?.next_label || lt('Open training', 'ট্রেনিং খুলুন')
			);
		} finally {
			loading = false;
		}
	}

	$: overallScore = calculateOverallScore(metrics);
	$: trendDelta = calculateTrendDelta(trendsData);
	$: trendTone = getTrendTone(trendDelta);
	$: comparisonEntries = Object.entries(comparisonData?.comparison || {});
	$: baselineCards = comparisonEntries.map(([domain, values]) => ({
		domain,
		label: getDomainName(domain, $locale),
		status: getClinicalStatusLabel(values.improvement, $locale),
		tone: getClinicalStatusTone(values.improvement),
		pointChange: formatPointChange(values.improvement, $locale)
	}));
	$: difficultyEntries = comparisonEntries
		.map(([domain, values]) => {
			const baselineDifficulty = calculateBaselineDifficulty(values.baseline);
			const currentDifficulty = metrics?.current_difficulty?.[domain] ?? baselineDifficulty;
			return {
				domain,
				label: getDomainName(domain, $locale),
				delta: currentDifficulty - baselineDifficulty
			};
		})
		.filter((entry) => entry.delta !== 0)
		.sort((left, right) => Math.abs(right.delta) - Math.abs(left.delta));
</script>

<div class="progress-panel">
	{#if loading}
		<section class="state-panel glass-card">
			<p>{lt('Loading progress overview...', 'প্রগ্রেস ওভারভিউ লোড হচ্ছে...')}</p>
		</section>
	{:else if error}
		<section class="state-panel glass-card">
			<h2>{lt('Progress overview unavailable', 'প্রগ্রেস ওভারভিউ পাওয়া যাচ্ছে না')}</h2>
			<p>{error}</p>
			<a class="action-link" href={actionHref}>{actionLabel}</a>
		</section>
	{:else}
		<div class="overview-stack">
			<section class="summary-grid">
				<article class="glass-card stat-card compact-card">
					<p class="card-label">{lt('Weekly summary', 'সাপ্তাহিক সারাংশ')}</p>
					<h2>{n(weeklySummary?.total_sessions || 0)} {lt('sessions', 'সেশন')}</h2>
					<p class="card-copy">{n(weeklySummary?.active_days || 0)} {lt('active days and', 'সক্রিয় দিন এবং')} {n(weeklySummary?.total_time_minutes || 0)} {lt('minutes this week.', 'মিনিট এই সপ্তাহে।')}</p>
				</article>

				<article class="glass-card stat-card compact-card">
					<p class="card-label">{lt('Overall score', 'সামগ্রিক স্কোর')}</p>
					<h2>{oneDecimal(overallScore)}</h2>
					<p class="card-copy">{lt('A simplified average across your active cognitive domains.', 'আপনার সক্রিয় মানসিক ডোমেইনগুলোর একটি সরল গড়।')}</p>
				</article>

				<article class="glass-card stat-card compact-card">
					<p class="card-label">{lt('Training streak', 'ট্রেনিং ধারাবাহিকতা')}</p>
					<h2>{n(streakData?.current_streak || 0)} {lt('days', 'দিন')}</h2>
					<p class="card-copy">{lt('Longest streak:', 'সবচেয়ে বড় ধারাবাহিকতা:')} {n(streakData?.longest_streak || 0)} {lt('days.', 'দিন।')}</p>
				</article>

				<article class="glass-card trend-card compact-card {trendTone}">
					<div class="trend-head">
						<div>
							<p class="card-label">{lt('Trend', 'ট্রেন্ড')}</p>
							<h2>{getTrendLabel(trendDelta, $locale)}</h2>
						</div>
						<p class="trend-delta">{trendDelta > 0 ? '+' : ''}{oneDecimal(trendDelta)}</p>
					</div>
					<SimpleTrendChart points={trendsData?.overall_trend || []} />
				</article>
			</section>

			<section class="detail-grid">
				<article class="glass-card detail-card">
					<div class="detail-head">
						<div>
							<p class="card-label">{lt('Improvement since baseline', 'বেসলাইন থেকে উন্নতি')}</p>
							<h2>{lt('Cognitive improvement since baseline', 'বেসলাইন থেকে মানসিক উন্নতি')}</h2>
						</div>
					</div>

					<div class="comparison-list">
						{#each baselineCards as card}
							<div class="comparison-row {card.tone}">
								<div>
									<p class="comparison-domain">{card.label}</p>
									<p class="comparison-change">{card.pointChange}</p>
								</div>
								<p class="comparison-status {card.tone}">{card.status}</p>
							</div>
						{/each}
					</div>
				</article>

				<article class="glass-card detail-card">
					<div class="detail-head">
						<div>
							<p class="card-label">{lt('Difficulty progress', 'কঠিনতার অগ্রগতি')}</p>
							<h2>{lt('Training challenge since baseline', 'বেসলাইন থেকে ট্রেনিংয়ের পরিবর্তন')}</h2>
						</div>
					</div>

					{#if difficultyEntries.length > 0}
						<div class="difficulty-list">
							{#each difficultyEntries.slice(0, 4) as entry}
								<div class="difficulty-row">
									<p class="difficulty-domain">{entry.label}</p>
									<p class="difficulty-copy">
										{entry.delta > 0
											? lt('Your training difficulty increased by', 'আপনার ট্রেনিংয়ের কঠিনতা বেড়েছে')
											: lt('Your training difficulty decreased by', 'আপনার ট্রেনিংয়ের কঠিনতা কমেছে')}
										{' '}
										{Math.abs(entry.delta)} {lt('level(s) since baseline.', 'লেভেল বেসলাইন থেকে।')}
									</p>
								</div>
							{/each}
						</div>
					{:else}
						<p class="card-copy">{lt('Your training difficulty is stable so far. As you complete more sessions, this section will update automatically.', 'এখন পর্যন্ত আপনার ট্রেনিংয়ের কঠিনতা স্থিতিশীল। আরও সেশন সম্পন্ন করলে এই অংশ নিজে থেকে হালনাগাদ হবে।')}</p>
					{/if}
				</article>
			</section>
		</div>
	{/if}
</div>

<style>
	.progress-panel {
		display: grid;
	}

	.overview-stack {
		display: grid;
		gap: 1rem;
	}

	.summary-grid {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 1rem;
	}

	.detail-grid {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 1rem;
	}

	.glass-card,
	.state-panel {
		background: rgba(248, 250, 252, 0.84);
		backdrop-filter: blur(10px);
		border: 1px solid rgba(255, 255, 255, 0.72);
		border-radius: 22px;
		padding: 1.25rem;
		box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
	}

	.state-panel {
		text-align: center;
	}

	.action-link {
		display: inline-flex;
		margin-top: 1rem;
		padding: 0.8rem 1.1rem;
		border-radius: 999px;
		font-weight: 700;
		text-decoration: none;
		background: linear-gradient(135deg, #4f46e5, #6366f1);
		color: white;
	}

	.card-label {
		margin: 0;
		font-size: 0.78rem;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		font-weight: 800;
		color: #4f46e5;
	}

	.stat-card h2,
	.trend-card h2,
	.state-panel h2 {
		margin: 0.25rem 0 0.45rem;
		font-size: 1.7rem;
		color: #111827;
	}

	.card-copy,
	.state-panel p {
		margin: 0;
		line-height: 1.55;
		color: #64748b;
	}

	.trend-head,
	.detail-head {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 1rem;
		margin-bottom: 1rem;
	}

	.trend-delta {
		margin: 0;
		font-size: 1.3rem;
		font-weight: 800;
		color: #0f172a;
	}

	.comparison-list,
	.difficulty-list {
		display: grid;
		gap: 0.75rem;
	}

	.comparison-row,
	.difficulty-row {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		padding: 0.95rem 1rem;
		border-radius: 16px;
		background: rgba(255, 255, 255, 0.65);
	}

	.comparison-domain,
	.comparison-change,
	.comparison-status,
	.difficulty-domain,
	.difficulty-copy {
		margin: 0;
	}

	.comparison-domain,
	.difficulty-domain {
		font-weight: 700;
		color: #111827;
	}

	.comparison-change,
	.difficulty-copy,
	.comparison-status {
		color: #64748b;
	}

	@media (max-width: 860px) {
		.summary-grid,
		.detail-grid {
			grid-template-columns: 1fr;
		}
	}
</style>

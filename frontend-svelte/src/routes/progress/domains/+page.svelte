<script>
	import { goto } from '$app/navigation';
	import { training } from '$lib/api';
	import { locale, localeText } from '$lib/i18n';
	import { domainOrder, getDomainName, getScoreColor, getTrendLabel, getTrendTone } from '$lib/progress';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let currentUser = null;
	let loading = true;
	let error = null;
	let metrics = null;

	user.subscribe((value) => {
		currentUser = value;
	});

	const lt = (en, bn) => localeText({ en, bn }, $locale);

	onMount(async () => {
		if (!currentUser) {
			goto('/login');
			return;
		}

		await loadDomains();
	});

	async function loadDomains() {
		loading = true;
		error = null;

		try {
			metrics = await training.getMetrics(currentUser.id);
		} catch (loadError) {
			console.error('Error loading domain performance:', loadError);
			error = lt('Complete more training sessions to review domain performance.', 'ডোমেইন পারফরম্যান্স দেখতে আরও কিছু ট্রেনিং সেশন সম্পন্ন করুন।');
		} finally {
			loading = false;
		}
	}

	$: domainCards = domainOrder
		.map((domain) => ({ domain, data: metrics?.metrics_by_domain?.[domain] }))
		.filter((entry) => entry.data);
</script>

<div class="progress-panel">
	{#if loading}
		<section class="state-panel glass-card">
				<p>{lt('Loading domain performance...', 'ডোমেইন পারফরম্যান্স লোড হচ্ছে...')}</p>
			</section>
		{:else if error}
			<section class="state-panel glass-card">
				<h2>{lt('Domain performance unavailable', 'ডোমেইন পারফরম্যান্স পাওয়া যাচ্ছে না')}</h2>
				<p>{error}</p>
			</section>
		{:else}
		<section class="domains-grid">
			{#each domainCards as entry}
				<article class="glass-card domain-card {getTrendTone(entry.data.improvement)}">
					<div class="card-topline">
						<div>
							<p class="card-label">{getDomainName(entry.domain, $locale)}</p>
							<h2>{entry.data.average_score.toFixed(1)}</h2>
						</div>
						<span class="trend-pill {getTrendTone(entry.data.improvement)}">{getTrendLabel(entry.data.improvement, $locale)}</span>
					</div>

					<div class="metric-row">
						<div>
							<p class="metric-label">{lt('Sessions', 'সেশন')}</p>
							<p class="metric-value">{entry.data.total_sessions}</p>
						</div>
						<div>
							<p class="metric-label">{lt('Average score', 'গড় স্কোর')}</p>
							<p class="metric-value" style="color: {getScoreColor(entry.data.average_score)}">{entry.data.average_score.toFixed(1)}</p>
						</div>
						<div>
							<p class="metric-label">{lt('Accuracy', 'নির্ভুলতা')}</p>
							<p class="metric-value">{entry.data.average_accuracy.toFixed(1)}%</p>
						</div>
						<div>
							<p class="metric-label">{lt('Improvement', 'উন্নতি')}</p>
							<p class="metric-value">{entry.data.improvement > 0 ? '+' : ''}{entry.data.improvement.toFixed(1)}</p>
						</div>
					</div>
				</article>
			{/each}
		</section>
	{/if}
</div>

<style>
	.domains-grid {
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

	.card-topline {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		align-items: flex-start;
		margin-bottom: 1rem;
	}

	.card-label,
	.metric-label {
		margin: 0;
		font-size: 0.78rem;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		font-weight: 800;
		color: #64748b;
	}

	.domain-card h2,
	.state-panel h2 {
		margin: 0.25rem 0 0;
		font-size: 1.7rem;
		color: #111827;
	}

	.metric-row {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 0.8rem;
	}

	.metric-value,
	.state-panel p {
		margin: 0.3rem 0 0;
		font-size: 1.05rem;
		font-weight: 700;
		color: #111827;
	}

	.trend-pill {
		padding: 0.4rem 0.75rem;
		border-radius: 999px;
		font-size: 0.76rem;
		font-weight: 700;
	}

	.trend-pill.positive {
		background: rgba(34, 197, 94, 0.14);
		color: #15803d;
	}

	.trend-pill.negative {
		background: rgba(239, 68, 68, 0.12);
		color: #b91c1c;
	}

	.trend-pill.neutral {
		background: rgba(148, 163, 184, 0.14);
		color: #475569;
	}

	@media (max-width: 860px) {
		.domains-grid,
		.metric-row {
			grid-template-columns: 1fr;
		}
	}
</style>

<script>
	import { goto } from '$app/navigation';
	import { patientJourney, training } from '$lib/api';
	import BiomarkersPanel from '$lib/components/BiomarkersPanel.svelte';
	import { locale, localeText } from '$lib/i18n';
	import { user } from '$lib/stores';
	import { onMount } from 'svelte';

	let currentUser = null;
	let loading = true;
	let error = null;
	let actionHref = '/training';
	let actionLabel = null;
	let biomarkerData = null;
	let recentContext = [];
	let longitudinal = null;
	let journey = null;

	user.subscribe((value) => {
		currentUser = value;
	});

	const lt = (en, bn) => localeText({ en, bn }, $locale);

	onMount(async () => {
		if (!currentUser) {
			goto('/login');
			return;
		}

		await loadInsights();
	});

	async function loadInsights() {
		loading = true;
		error = null;
		actionHref = '/training';
		actionLabel = lt('Open training', 'ট্রেনিং খুলুন');

		try {
			journey = await patientJourney.get(currentUser.id);

			if (!journey?.progress?.unlocked) {
				error = lt(
					'Insights open only after your training history starts to build.',
					'আপনার ট্রেনিং ইতিহাস জমতে শুরু করলে তবেই ইনসাইটস খুলবে।'
				);
				actionHref = journey?.next_route || '/training';
				actionLabel = journey?.next_label || lt('Open training', 'ট্রেনিং খুলুন');
				return;
			}

			const [biomarkersResponse, contextResponse, longitudinalResponse] = await Promise.allSettled([
				training.getBiomarkers(currentUser.id, 30),
				training.getRecentContext(currentUser.id, 4),
				training.getLongitudinalAnalytics(currentUser.id, 30)
			]);

			biomarkerData = biomarkersResponse.status === 'fulfilled' ? biomarkersResponse.value : null;
			recentContext = contextResponse.status === 'fulfilled' ? contextResponse.value?.contexts || [] : [];
			longitudinal = longitudinalResponse.status === 'fulfilled' ? longitudinalResponse.value : null;

			if (!biomarkerData && !longitudinal && recentContext.length === 0) {
				error = lt(
					'Complete more training to unlock patient insights.',
					'রোগী-ইনসাইট দেখতে আরও কিছু ট্রেনিং সম্পন্ন করুন।'
				);
				actionHref = '/training';
				actionLabel = lt('Continue training', 'ট্রেনিং চালিয়ে যান');
			}
		} catch (loadError) {
			console.error('Error loading patient insights:', loadError);
			error = lt(
				'We could not load your insights right now.',
				'এই মুহূর্তে আপনার ইনসাইটস লোড করা যাচ্ছে না।'
			);
			actionHref = journey?.next_route || '/training';
			actionLabel = journey?.next_label || lt('Open training', 'ট্রেনিং খুলুন');
		} finally {
			loading = false;
		}
	}

	function formatDate(value) {
		return new Date(value).toLocaleDateString($locale === 'bn' ? 'bn-BD' : 'en-US', {
			day: '2-digit',
			month: 'short',
			year: 'numeric'
		});
	}

	function formatCorrelation(value) {
		if (value === null || value === undefined) {
			return lt('Not enough data', 'যথেষ্ট ডেটা নেই');
		}

		const absolute = Math.abs(value);
		if (absolute >= 0.6) return value > 0 ? lt('Strong positive effect', 'শক্তিশালী ইতিবাচক প্রভাব') : lt('Strong negative effect', 'শক্তিশালী নেতিবাচক প্রভাব');
		if (absolute >= 0.3) return value > 0 ? lt('Moderate positive effect', 'মাঝারি ইতিবাচক প্রভাব') : lt('Moderate negative effect', 'মাঝারি নেতিবাচক প্রভাব');
		return lt('Weak relationship', 'দুর্বল সম্পর্ক');
	}

	$: report = longitudinal?.report || null;
	$: summaryCards = [
		{ label: lt('Sessions analysed', 'বিশ্লেষিত সেশন'), value: report?.summary?.total_sessions ?? 0 },
		{
			label: lt('Score trend', 'স্কোর ট্রেন্ড'),
			value: report?.trends?.score_trend?.trend_direction || lt('Unavailable', 'পাওয়া যায়নি')
		},
		{ label: lt('Recent check-ins', 'সাম্প্রতিক চেক-ইন'), value: recentContext.length }
	];
</script>

<div class="progress-panel">
	{#if loading}
		<section class="state-panel glass-card">
			<p>{lt('Loading patient insights...', 'রোগী-ইনসাইট লোড হচ্ছে...')}</p>
		</section>
	{:else if error}
		<section class="state-panel glass-card">
			<h2>{lt('Insights unavailable', 'ইনসাইট পাওয়া যাচ্ছে না')}</h2>
			<p>{error}</p>
			<a class="action-link" href={actionHref}>{actionLabel}</a>
		</section>
	{:else}
		<section class="summary-shell glass-card">
			<div class="summary-head">
				<div>
					<p class="card-label">{lt('Patient insights', 'রোগী ইনসাইট')}</p>
					<h2>{lt('A calmer view of your deeper analytics', 'আপনার গভীর বিশ্লেষণের একটি শান্ত ভিউ')}</h2>
				</div>
				<p class="summary-copy">{lt('These cards keep advanced information readable without turning the dashboard into a wall of text.', 'এগুলো উন্নত তথ্যকে পড়তে সহজ রাখে, ড্যাশবোর্ডকে দীর্ঘ লেখার দেয়াল বানায় না।')}</p>
			</div>

			<div class="summary-grid">
				{#each summaryCards as card}
					<article class="summary-card">
						<p class="summary-label">{card.label}</p>
						<strong>{card.value}</strong>
					</article>
				{/each}
			</div>
		</section>

		<BiomarkersPanel biomarkerData={biomarkerData} doctorView={false} days={30} />

		<section class="detail-grid">
			<article class="glass-card detail-card">
				<div class="section-head">
					<div>
						<p class="card-label">{lt('Recent check-ins', 'সাম্প্রতিক চেক-ইন')}</p>
						<h3>{lt('How you felt before training', 'ট্রেনিংয়ের আগে আপনি কেমন অনুভব করছিলেন')}</h3>
					</div>
				</div>

				{#if recentContext.length === 0}
					<p class="empty-copy">{lt('Your short training check-ins will appear here once you start using them.', 'ছোট ট্রেনিং চেক-ইন ব্যবহার শুরু করলে সেগুলো এখানে দেখা যাবে।')}</p>
				{:else}
					<div class="context-list">
						{#each recentContext as item}
							<div class="context-row">
								<div>
									<p class="context-date">{formatDate(item.created_at)}</p>
									<p class="context-meta">{lt('Energy', 'শক্তি')} {item.fatigue_level ?? '-'} / 10 · {lt('Readiness', 'প্রস্তুতি')} {item.readiness_level ?? '-'} / 10</p>
								</div>
								<p class="context-note">{lt('Sleep', 'ঘুম')} {item.sleep_quality ?? '-'} / 10</p>
							</div>
						{/each}
					</div>
				{/if}
			</article>

			<article class="glass-card detail-card">
				<div class="section-head">
					<div>
						<p class="card-label">{lt('Context clues', 'প্রসঙ্গের ইঙ্গিত')}</p>
						<h3>{lt('What seems to affect your sessions most', 'কোন বিষয়গুলো সেশনে সবচেয়ে বেশি প্রভাব ফেলছে')}</h3>
					</div>
				</div>

				<div class="correlation-grid">
					<article class="correlation-card">
						<p>{lt('Fatigue', 'ক্লান্তি')}</p>
						<strong>{formatCorrelation(report?.contextual_analysis?.fatigue_level?.correlation_with_score)}</strong>
					</article>
					<article class="correlation-card">
						<p>{lt('Sleep quality', 'ঘুমের মান')}</p>
						<strong>{formatCorrelation(report?.contextual_analysis?.sleep_quality?.correlation_with_score)}</strong>
					</article>
					<article class="correlation-card">
						<p>{lt('Medication timing', 'ওষুধের সময়')}</p>
						<strong>{formatCorrelation(report?.contextual_analysis?.hours_since_medication?.correlation_with_score)}</strong>
					</article>
				</div>
			</article>
		</section>
	{/if}
</div>

<style>
	.glass-card,
	.state-panel {
		background: rgba(248, 250, 252, 0.84);
		backdrop-filter: blur(10px);
		border: 1px solid rgba(255, 255, 255, 0.72);
		border-radius: 22px;
		padding: 1.25rem;
		box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
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

	.summary-shell,
	.detail-grid {
		margin-bottom: 1rem;
	}

	.summary-head,
	.section-head {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		margin-bottom: 1rem;
	}

	.summary-grid,
	.detail-grid,
	.correlation-grid {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 1rem;
	}

	.context-list {
		display: grid;
		gap: 0.75rem;
	}

	.context-row,
	.summary-card,
	.correlation-card {
		padding: 1rem;
		border-radius: 16px;
		background: rgba(255, 255, 255, 0.65);
	}

	.card-label,
	.summary-label {
		margin: 0;
		font-size: 0.78rem;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		font-weight: 800;
		color: #64748b;
	}

	h2,
	h3,
	p {
		margin-top: 0;
	}

	@media (max-width: 860px) {
		.summary-grid,
		.detail-grid,
		.correlation-grid {
			grid-template-columns: 1fr;
		}

		.summary-head,
		.section-head {
			flex-direction: column;
		}
	}
</style>
